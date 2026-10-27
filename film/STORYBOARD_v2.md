# MCST LMS — Nine Improvements Launch Film — STORYBOARD v2

Format: 1920x1080, 30fps, ~74s (~2,220 frames). Sound: procedural SFX + music bed (mgaudio path, no ElevenLabs key). Source: REAL captured UI only (motionmaxxing pipeline, borrowed validations from lemo/huashu/opuscar).

## 1. Brand inventory (verified, from live app + code)

| Slot | MCST Library value | Evidence |
|---|---|---|
| Logo | Circular seal, white/navy, "MCST LIBRARY 2025" | `app/static/images/Library_Logo.jpg` (live header) |
| Primary ink | Navy `#1e3a8a`-family on paper `#f7f7f7`; dark surfaces `#0f172a` | base.html tokens (v1 storyboard) |
| Type | **Manrope** 400-800, tight tracking | login page render, base.html |
| Core controls | Navy Search pill; Tailwind cards, ring-1 slate, 12px radius | public + dashboard |
| Voice | Plain academic: "Discover Knowledge" | public index |
| Material | Paper cards, soft shadows, generous whitespace | all staff pages |
| Never do | Fake dashboards, invented data, playful gradients, page chrome | mandate + G5 |

## 2. PAGE (Problem Audience Goal Emotion) + one true thing

- Problem: Staff/students don't know how much this LMS changed under the hood this cycle.
- Audience: MCST community + capstone panel.
- Goal: In ~75s, make 9 real improvements land as believable, verifiable product moments.
- Emotion: Momentum, competence, trust ("nothing was invented — it's all live").
- One true thing: **Every scene is a live action performed in a real session against real data.**

Runtime arc (causal chain, each handoff earns the next beat):

```
identity (who signs in) → they arrive (notifications) → when is the building open
→ so when must a hold be claimed → what books do we hold & how (categories → e-books)
→ what did people ask for (validated requests) → what did we do (audit trail)
→ and how do we report it (branded PDF) → close.
```

## 3. Film shape + beat table (buys / copy / moves / handoff)

Timings in seconds (frames = s*30). All "UI" = live screenshots at 1920x1080 CSS px, zoomed 1.0-2.4x, pan/refreshed crops; callouts = box-select + settle (8px overshoot spec); captions lock-on; ≤1 accent per beat; no 3 consecutive push-ins (huashu rule); camera vocabulary ≥ 4 distinct moves (pan L/R, push, pull, cut-on-motion, mask-wipe).

| # | Beat / time | Buys | Camera + motion | Source asset | Copy (real phrases only) | Handoff |
|---|---|---|---|---|---|---|
| 0 | Hook 0-4.0 | This is the real system | Login page rides cursor → "Sign in with Google" badge press → cut hard on session start | 00_login_hook.png | "The MCST Library, newly rebuilt." | Cursor becomes the signed avatar card |
| 1 | F1 Role labels 4.0-9.5 | The system knows who you are | Lock-on boxes on ID labels per role: STUDENT ID NUMBER 2023-1045 (Patricia), LIBRARIAN ID NUMBER (Rosario), FACULTY ID NUMBER FAC-2018-042 (Reinaldo); kinetic type swap | 11a_profile_student.png, 12a_profile_librarian.png, 12b_profile_faculty.png | "Your ID number, labeled for your role." | Label field wipes right into header badge |
| 2 | F6 Notifications 9.5-15.0 | You arrive to updates | Zoom-out from profile → bell dropdown slides/fades in over dimmed page → unread cards with pill labels count in; badge shows 6 | 11b_profile_student_claim.png, 11c_notifications_panel.png, 11d_notifications_page.png | "Updates the moment you arrive." | Badge dot travels to notifications page |
| 3 | F3 Operating schedule 15.0-20.5 | The hours live here | Settings page, pan down to week checkboxes; cursor unchecks a day; **state saves for real** | settings.png (pre/post) | "Set the week. Close a day." | The closed day becomes a calendar dot |
| 4 | F2 Reservation cutoff 20.5-26.5 | Cutoff is computed, not promised | Formula types itself: Closing − 2h; allocation desk: Allocate click → allocated status pill + Ready-for-Pickup 1→2 / Waiting 2→1 count swap; "Claim by Oct 19, 2026 07:58 PM." card lands | 04_reservations.png, 04c_allocation_confirmed.png, 04d_allocated_claim_actions.png, 11b_profile_student_claim.png | "Claim after the cutoff? Next morning." | Claim-by badge flies to student Ready-for-Pickup card |
| 5 | F4 Categories 26.5-32.5 | Categories are chosen, not typed | Cataloging desk → dropdown crashes open → ticks cascade, label composes "Abstract Algebra + Actuarial Science + Adapted PE" → Manage Categories modal | 05_cataloging.png, 06_category_multicheck_open.png, 06b_categories_selected.png, 06c_manage_categories.png | "Pick categories. Add new. Assign many." | Same desk, scroll to E-Book row |
| 6 | F5 E-books 32.5-39.5 | Books online, permission controlled | Edit Book modal fills E-Book Link (Drive URL validated green: "Google Drive link — embeddable preview enabled.") → Allow download toggle → save → /book/267 shows ONLINE ACCESS → Read Online modal (real Drive embed) | 06d_edit_ebook_filled.png, 07_book_ebook_page.png, 07b_read_online_modal.png | "Add an e-book. Lend it twice." | Reader page slides to Requests desk |
| 7 | F8 Request validation 39.5-46.0 | Duplicates get recognized | /librarian/requests: duplicate clusters group up (Data Science ×5, Philippine History ×3, Clean Architecture ×2); count-up chip | 08_requests_clusters.png | "Same book, one request." | Card stack becomes audit rows |
| 8 | F7 Audit logs 46.0-52.0 | What happened is recorded | /admin/audits Library tab opens; rows ripple in; fresh entry "Torres allocated reservation #9" highlighted | 09a_audits_top.png, 09b_audits_library.png | "Every library action, in the record." | A row's message → export button |
| 9 | F9 Branded PDF 52.0-58.5 | Reports carry the brand | Reporting Dashboard → hidden-form export POST (real download) → rasterized PDF pages flip (all_20261019_174143.pdf, 202,492 bytes) → logo zoom-in (the hero moment) | 10a_analytics.png, 10b_analytics_pdf_p1..p4.png | "Professional reports, library-branded." | Logo match-cuts to closing logo |
| 10 | Close 58.5-64s... (budget: re-forecast) | Same mark, same place | Logo (the real PDF logo) rises from 1.15x to stillness | logo.jpg | "Discover Knowledge." + "The MCST Library Management System." | End |

NOTE on total: running time computed precisely once per-beat refine; target ≤ 75s; CTA ≤ 25%.

## 4. World & time

- Ground: paper `#f7f7f7` from real captures, framed as the desk; Act sweeps warm → navy for close (brand's own colors, no invented palettes).
- Light: single soft key; screenshots are the light source (they're the world).
- Hero moment: F9 — the exported PDF page set in full-frame, its seal zooming 1.0→2.4x with the caption. Engineered via real export during capture. **This is the screenshot-worthy frame.**
- Carrier: the **timing cord** — a single horizontal hairline (2px, navy at 12% alpha) that the callout boxes tether to across beats (not pinned: it re-anchors per beat, never static).
- Sound: mgaudio procedural SFX (click, whoosh, tick, ledger stamp) + 84-90 BPM sparse bed; hits on cue grid (huashu: silence before the promise); no VO (no key).

## 5. Captured assets (ACTUAL inventory — all real UI reads, film/captures/)

| Asset | Feature | Notes |
|---|---|---|
| 00_login_hook.png | Hook | Logged-out institutional login, Google sign-in card |
| 01_profile_admin.png, 02_settings_full.png, 03_settings_reservation.png | F1/F3 | Admin session (prior day sweep) |
| 04_reservations.png, 04b_row_expanded.png, 04c_allocation_confirmed.png, 04d_allocated_claim_actions.png | F2 | REAL Allocate POST on res #9 (Torres); Ready-for-Pickup 1→2, Waiting 2→1 |
| 05_cataloging.png | F4 | 413 items, accession chips |
| 06_multicheck_open.png, 06b_selected.png, 06c_manage_categories.png | F4 | 3 ticks; label composes real string |
| 06d_edit_ebook_filled.png | F5 | Real Drive URL validation (green note) |
| 07_book_ebook_page.png, 07b_read_online_modal.png | F5 | Embeddable Drive preview (content is an unrelated sample PDF — disclose) |
| 08_requests_clusters.png | F8 | Data Science ×5, Philippine History ×3, Clean Architecture ×2 |
| 09a_audits_top.png, 09b_audits_library.png | F7 | Fresh "Torres allocated reservation #9" entry |
| 10a_analytics.png | F9 | Reporting Dashboard |
| 10b_analytics_pdf_p1..p4.png | F9 | Rasterized real export (202,492 bytes) |
| 11a_profile_student.png, 11b_profile_student_claim.png | F1+F2+F6 | Patricia: STUDENT ID 2023-1045, badge 6, ALLOCATED reservation, "Claim by" card |
| 11c_notifications_panel.png, 11d_notifications_page.png | F6 | Real unread cards with REQUEST UPDATE / RESERVATION / HOLD READY pills |
| 12a_profile_librarian.png, 12b_profile_faculty.png | F1 | Role variants (LIBRARIAN ID, FACULTY ID FAC-2018-042) |

Capture surgery performed (all real, disclosed in NOTE.md): temp env-gated loopback
session route (since reverted), copy 0629 returned via real desk return, copies
000630/000631 added via real accession form, reservations #13 allocated via real
Allocate action, procurement request #32 approved via real Requests action.

## 6. Verification ledger (what claims are provable)

Every claim above already mapped by analysis subagent with file:line to app code. Film text uses: rendered phrases, real UI words, model values (RESERVATION_CLAIM_HOURS=2.0), no invented numbers.
Banned: everything not listed in section 3/5.

## 7. Pre-flight gate check

- [x] G1 (type ≥0.04H at 1920) — planned captions 9-11%H, callout text 5-6%
- [x] G3 — planned end hold 0.9-1.2s
- [x] G4 — 1 focal accord per frame (callout targets one node; camera pans, never split)
- [ ] G0 render, G2 flat-frames, G5 lint (computed post-render)
