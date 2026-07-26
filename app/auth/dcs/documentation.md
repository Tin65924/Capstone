# Authentication Module Documentation

## Overview

The authentication module implements Google OAuth 2.0 / OpenID Connect for user login. It uses Flask-Login for session management and the `google-auth` / `google-auth-oauthlib` libraries for OAuth token exchange and verification.

Only institutional email addresses (`@mcst.edu.ph`) are allowed. No passwords are stored — authentication is fully delegated to Google.

## Architecture

```
app/auth/
├── __init__.py          # Blueprint registration
├── routes.py            # OAuth flow endpoints
├── models.py            # Database queries (users, roles, borrowers)
├── user.py              # Flask-Login User class
├── decorators.py        # Role-based access decorators
└── documentation.md     # This file
```

Flow diagram:
```
User clicks "Sign in with Google"
        │
        ▼
GET /login/google
  → Generate OAuth URL with state param
  → Store state in session
  → Redirect to Google consent screen
        │
        ▼
Google asks for consent
        │
        ▼
Google redirects to /login/google/callback?state=...&code=...
        │
        ▼
GET /login/google/callback
  → Verify state matches session
  → Exchange authorization code for tokens
  → Verify ID token (signature, aud, iss, email domain)
  → Look up user by oauth_sub
  → If exists → login, redirect to dashboard
  → If new → store info in session, redirect to /login/role-select
        │
        ▼
GET /login/role-select  (new users only)
  → User selects Student or Faculty
  → Enters ID number and department
        │
        ▼
POST /login/role-select
  → If Student → create user_accounts + borrowers (active), auto-login
  → If Faculty → create user_accounts (disabled), show pending page
```

## Security Measures

| Measure | Implementation |
|---|---|
| ID Token verification | `google.oauth2.id_token.verify_oauth2_token()` validates signature, aud, iss |
| Domain restriction | `@mcst.edu.ph` enforced after token verification (app-layer, before any DB write) |
| CSRF protection | OAuth `state` parameter tied to Flask session, popped after use |
| Clock skew tolerance | 30 seconds allowed for token expiry |
| HTTPS required | OAuth redirect URI must use HTTPS in production (HTTP for localhost dev) |
| HTTP-only sessions | Flask session cookies are HTTP-only by default |
| Session expiry | Flask-Login clears session on logout; browser session ends on close |
| Parameterized queries | All DB queries use `%s` placeholders (no SQL injection) |
| No password storage | Zero password fields in the database |

## Configuration

### Environment Variables (`.env`)

```
GOOGLE_OAUTH_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
SECRET_KEY=random-secret-key-for-flask-sessions
DATABASE_URL=postgresql://user:password@localhost:5432/library_db
```

### Google Cloud Console Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project or select existing
3. Navigate to **APIs & Services → Credentials**
4. Create an **OAuth 2.0 Client ID** (Web application)
5. Add authorized redirect URIs:
    - Development: `http://localhost:5000/login/google/callback`
   - Production: `https://yourdomain.com/login/google/callback`
6. Note the Client ID and Client Secret
7. Enable the **Google+ API** or **People API** (for profile info)

## Endpoints

| Method | Path | Description | Auth Required |
|---|---|---|---|
| GET | `/login` | Login page | No |
| GET | `/login/google` | Initiate OAuth flow | No |
| GET | `/login/google/callback` | OAuth callback | No |
| GET | `/login/role-select` | Role selection form | No |
| POST | `/login/role-select` | Submit role selection | No |
| GET | `/logout` | Logout | Yes |

## User Model

```python
class User:
    id          # str — user_accounts.user_id
    email       # str — Google email
    role        # str — 'Student', 'Faculty', 'Librarian', 'Admin'
    full_name   # str — from Google profile
```

Role-based access control is enforced via decorators:

```python
from app.auth.decorators import librarian_required, faculty_required, admin_required

@librarian_required  # Librarian or Admin
@faculty_required    # Faculty, Librarian, or Admin
@admin_required      # Admin only
```

## New User Registration Flow

1. First-time Google sign-in → redirected to `/login/role-select`
2. User selects role and enters ID number + department
3. **Student**: Instant activation. Can immediately borrow up to 3 books.
4. **Faculty**: Account created as `disabled`. A librarian must activate it via User Management before the faculty member can log in.

## Database Tables Used

- `user_accounts` — Primary user records
- `roles` — Role definitions (Student, Faculty, Librarian, Admin)
- `borrowers` — Student/Faculty extension (ID number, department, status)
- `audit_trail` — Login/logout/activity logging

## Dependencies

```
Flask-Login==0.6.3
google-auth==2.38.0
google-auth-oauthlib==1.2.1
```
