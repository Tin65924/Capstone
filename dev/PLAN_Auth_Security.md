# Plan: 2FA, Password Login, Change Password w/ Email Verification, Profile Page

Scope: Professor items 3 (password login for Admin/Staff), 10 (profile page), plus 2FA and change-password-with-email-verification.

## Current State (constraints that shape this plan)

- Auth is Google-OAuth-only. There are no passwords anywhere in the system, no SMTP config, no email-sending code.
- `user_accounts` has: `user_id, email, oauth_sub, full_name, role_id, account_status, created_at` — no password, no phone.
- `oauth_sub` is `UNIQUE NOT NULL` (schema.sql:10) — blocks local-only password accounts; needs a migration.
- `User` model (app/auth/user.py) only carries `id/email/role/full_name`.
- Login page is Google-button-only; profile page is static/hardcoded (welcome "Alice", placeholder stats).
- No CSRF protection, no rate limiting, no Flask-Mail, no SESSION_COOKIE_* hardening — all new work must account for these.

## Decisions (confirmed)

1. Add local username/password login alongside Google (professor item 3).
2. 2FA: TOTP authenticator app as primary + email OTP as backup.
3. Email verification via SMTP credentials (config-driven; test via fake sender).
4. Profile "Contact" = phone number.

## Data Flow

### Flow A — Local password login (first time / subsequent)

1. User opens `/login` (GET) → page shows Google button + "Email & Password" tab.
2. User enters email + password → `POST /login/password` with CSRF token.
3. Route:
   a. `get_credentials_by_email(email)` → no account → generic "Invalid email or password" → **stop**.
   b. `check_password_hash(user.password_hash, password)` → fail → same generic error + rate-limit counter → **stop**.
   c. User has no `password_hash` (Google-only account) → redirect to "set a password" flow → **stop**.
   d. If `totp_enabled` → store `session['_2fa_pending'] = {user_id, auth_method='password'}` → redirect `GET /login/2fa` → **stop here** (no login yet).
   e. Else → `login_user(user)` → `log_activity(user.id, 'login')` → redirect `next` (validated relative) or `/user/profile`.
4. 2FA challenge (`GET /login/2fa`):
   a. User enters 6-digit TOTP code → `POST /login/2fa`.
   b. Route verifies `pyotp.TOTP(totp_secret).verify(code, valid_window=1)` → fail → rate-limit counter → retry → **stop**.
   c. Or user clicks "Email me a code" → `POST /login/2fa/email` → route sends 6-digit OTP to the account's registered email (hashed in session, 10-min expiry, single-use, capped per hour).
   d. User types emailed code → `POST /login/2fa` → verify hash → success.
   e. On success: pop pending → `login_user(user)` → `log_activity` → redirect `next` or `/user/profile`.

Data written: `audit_trail` (login). Data read: `user_accounts`.

### Flow B — Google login with 2FA

1. User clicks "Sign in with Google" → `/login/google` → OAuth redirect → callback (`/login/google/callback`).
2. Google token verified; `get_user_by_oauth_sub(sub)` → existing user found.
3. If `totp_enabled` → same `_2fa_pending` + `/login/2fa` gate as Flow A step 3d/4 (identical enforcement — no weaker path).
4. Else → `login_user` → redirect `next`.

Data written: `audit_trail`. Data read: `user_accounts`.

### Flow C — Enable 2FA (TOTP)

1. User on `/user/profile` clicks **Enable 2FA** → `GET /user/2fa/enable`.
2. Route generates `totp_secret` (base32), builds provisioning URI, renders QR code + secret text.
3. User scans QR in authenticator app, enters the current 6-digit code → `POST /user/2fa/enable`.
4. Route verifies the code against the new secret → fail → error, keep secret → retry → **stop**.
5. Success → UPDATE `user_accounts` set `totp_secret`, `totp_enabled=TRUE` → flash success → redirect profile.

Data written: `user_accounts.totp_secret`, `user_accounts.totp_enabled`.

### Flow D — Change password with email verification

1. User on `/user/profile` enters current password + new password → `POST /user/change-password/request`.
2. Route:
   a. Verify current password (`check_password_hash` on stored hash) → fail → **stop**.
   b. Validate new password policy.
   c. Generate token → INSERT into `verification_tokens` (`token_hash`, `user_id`, `purpose='password_change'`, `expires_at = now + 30min`).
   d. Email a **6-digit code** to the account's registered address (no token in URL).
3. User opens email, types code on `GET /user/change-password/verify` → `POST /user/change-password/verify`.
4. Route:
   a. Look up `verification_tokens` by hash + user + purpose → missing/expired/used → error → **stop**.
   b. Mark `used=TRUE` (single-use).
   c. `set_password(user_id, generate_password_hash(new))`.
   d. Flash success → redirect profile.

Data written: `verification_tokens`, `user_accounts.password_hash`.

### Flow E — Profile page (read + edit)

1. User opens `/user/profile` → route calls `get_user_profile(user_id)` (email, full_name, phone, role, department, id_number, created_at) → renders Basic Information + Security cards with DB values.
2. User edits Name / Phone (or Department) → `POST /user/profile/update` with the field(s).
3. Route:
   a. `current_user.id` only (never a form-supplied `user_id` → no IDOR).
   b. Validate phone format/length.
   c. `update_phone` / `update_full_name` / `update_department` → UPDATE `user_accounts` / `borrowers`.
   d. Flash success → redirect profile.

Data written: `user_accounts` (full_name, phone), `borrowers` (department). Data read: `user_accounts`, `borrowers`, `roles`.

## Phase 0 — Foundation (deps, schema, hardening)

- Add deps: `Flask-Mail`, `Flask-WTF` (CSRFProtect), `Flask-Limiter`, `pyotp`, `qrcode`.
- Schema (`schema.sql`) — additive + idempotent:
  - `user_accounts`: add `password_hash VARCHAR(255)`, `phone VARCHAR(20)`, `totp_secret VARCHAR(255)`, `totp_enabled BOOLEAN NOT NULL DEFAULT FALSE`; make `oauth_sub` nullable.
  - New table `verification_tokens` (`token_hash`, `user_id`, `purpose` = `'password_change' | '2fa_email'`, `expires_at`, `used`).
- Add idempotent `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` in `run_schema` (database.py) so existing DBs upgrade without a reset.
- Security hardening:
  - `CSRFProtect` globally (all new POST endpoints).
  - Session cookie flags: `SESSION_COOKIE_SECURE`, `HTTPONLY`, `SAMESITE=Lax`.
  - Validate `next` is a relative path (block open redirect).

## Phase 1 — Email infrastructure

- `config.py`: `MAIL_SERVER/PORT/USE_TLS/USERNAME/PASSWORD/DEFAULT_SENDER` from env.
- `app/__init__.py`: init `flask_mail.Mail`.
- New `app/mailer.py`: `send_email(to, subject, body)` + HTML templates.
- Never interpolate user input into email headers; always send to the account's registered address.

## Phase 2 — Password login (professor item 3)

- `auth/models.py`: `get_credentials_by_email` (incl. `password_hash`), `set_password`, `get_password_hash`.
- `auth/user.py`: add `has_password`, `totp_enabled`.
- New routes: `GET/POST /login/password` (email + password). On success: do NOT `login_user` yet — store `session['_2fa_pending'] = {user_id, auth_method}`; if 2FA enabled → `/login/2fa`; else log in.
- Google callback: same 2FA gate after existing-user lookup (both paths enforce 2FA identically).
- `login.html`: tabbed UI — Google button + Email/Password form.
- Brute-force protection: Flask-Limiter on `/login/password` + temporary lockout after N failures.
- Generic "Invalid email or password" (no account enumeration).
- Hash with werkzeug scrypt/pbkdf2 (constant-time); enforce min password policy.

## Phase 3 — 2FA (TOTP primary, email backup)

- New routes:
  - `GET /user/2fa/enable` → generate secret (`pyotp`), show QR; `POST` verifies a test code before enabling.
  - `POST /user/2fa/disable` → re-auth (OTP or password) then disable (prevent hijacked-session disabling).
  - `GET/POST /login/2fa` → challenge page; accepts TOTP **or** email OTP; "email me a code" → `POST /login/2fa/email` (6-digit, hashed, 10-min expiry, single-use). Success → `login_user` + redirect `next`.
- Rate limit + per-user lockout on code attempts (only 10^6 combos).
- Cap email-OTP resends per user/hour (prevent email bombing / SMTP cost).
- `totp_secret` encrypted at rest or documented tradeoff; never log secret/codes.
- Optional: track last-used TOTP step to prevent 30s-window replay.

## Phase 4 — Change Password with Email verification

- `POST /user/change-password/request`: require **current password** + new password; create token in `verification_tokens`; email a code the user **types** on a page (no token in URL → no history/referrer leaks).
- `GET/POST /user/change-password/verify`: user enters emailed code → mark token used → set new password.
- Token: single-use, short expiry, marked consumed on first use.
- Rate-limit requests per hour; don't reveal account-existence/email-sent to anonymous callers.

## Phase 5 — Profile Page (professor item 10)

- `auth/models.py`: `get_user_profile` (email, full_name, phone, role, department, id_number, created_at) + `update_phone/full_name/department`.
- Rework `user_profile.html`:
  - **Basic Information** card — Name (editable), Email (read-only), Phone (editable), Department/ID (from `borrowers`).
  - **Security** card — Change Password flow + 2FA enable/disable with QR.
  - Replace static "Alice"/placeholder stats with real DB values.
- Routes: `POST /user/profile/update` — bound to `current_user.id` server-side (never trust form `user_id` → prevents IDOR).
- Phone validation (format/length); no `|safe` on user input (XSS).

## Phase 6 — Tests

- Password login success/failure; account enumeration check.
- 2FA required when enabled: wrong code, TOTP correct, email-OTP fallback.
- Change-password: token valid/expired/used; current-password required.
- Profile updates (phone/name/department); IDOR attempt blocked.
- Full regression: `python -m pytest -q` (129 existing tests must stay green).

## Security Review (threats addressed in this plan)

| Risk | Severity | Mitigation (in plan) |
|---|---|---|
| No CSRF protection | High | Flask-WTF CSRFProtect globally |
| Client-side session cookie | Medium | Strong SECRET_KEY + cookie hardening flags |
| Brute force (password + codes) | High | Flask-Limiter + per-user lockout |
| Open redirect via `next` | Medium | Validate `next` is relative |
| 2FA bypass via weaker login path | High | Identical 2FA gate on Google + password paths |
| TOTP brute force | High | Rate limit + lockout |
| `totp_secret` plaintext in DB | Medium | Encrypt at rest or documented tradeoff |
| Email bombing / SMTP abuse | Medium | Cap resends per user/hour; registered-address-only |
| Verification token in URL | Medium | User types emailed code; no token URLs |
| Token reuse | High | Single-use, consumed, short expiry |
| Session hijack + email = takeover | Medium | Current password required for change-password |
| IDOR on profile update | High | Bind to current_user.id server-side |
| XSS in profile fields | Low | Autoescape; no `|safe` |

## Open items

- SMTP creds: real `MAIL_*` values needed in `.env` for live email tests (tests inject a fake sender).
- Forgot-password (email reset link for users who can't log in) — out of scope unless requested.
