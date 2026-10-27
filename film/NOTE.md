# Film Note — MCST LMS launch film (film/final.mp4)

64.4 s, 1920×1080, 30 fps, with sound. Built from **real UI captures only** — every screenshot shown on screen is the running MCST Library LMS, captured in a browser at 1280×720 and displayed at 1.5×. No fabricated UI.

## What is real
- All 29 captures in `film/captures/` are genuine screenshots of the deployed app (login, dashboards, profile, settings, circulation, book management, e-book reader, audit log, analytics, reports) taken of the app running on `localhost:5000`.
- The MCST Library 2023 seal is the real `app/static/images/Library_Logo.jpg`.
- The "Reservation allocated." flow (scene 4) is a real interaction: the Allocate press on capture 04b, the flash confirmation and the counters changing (Ready 1→2 / Waiting 2→1) across the following shots.

## Capture disclosures (performed on a test account, not production data)
- A temporary capture route injected a session for screenshotting the staff pages; it was **removed and reverted** after capture.
- Overlays added in the film (caption cards, the notification dots in scene 2b drawn to mirror the live panel's unread state, category tags in scene 5) are marked by Motion — the underlying capture pixels are otherwise untouched.
- During capture these real writes happened: **copies 000630 and 000631 were added** to a book; **copy 0629 was returned**; a borrowing **request (#32) was approved** (the "Reservation allocated." flash in scene 4). Dates visible on capture ("Claim by Oct 12, 2025") reflect the capture date.
- The Google Drive e-book in scene 6 opens **sample content that does not match the e-book's metadata** (Drive-side placeholder); the connection, page-turn interaction and borrow limit are real.
- Storyboard `STORYBOARD_v2.md` maps 1:1 onto the final cut positions.

## Audio
- **No voice-over.** No ElevenLabs API key was available, so no narration or music could be sourced; the film is caption-driven.
- All sound effects are **procedurally synthesized** with ffmpeg (whooshes, UI click, stamp, chime, push riser, seal boom, ambient pad) — synced to the 22 cuts and key beats via `audio/sfx.json`; mix normalized to -18 LUFS / -1 dBTP (`audio/mix.wav`). cut-sync: 20 of 22 cuts land within ±80 ms of a sound onset.
- Fonts: Manrope (overlaid headings/captions); in-app type remains the app's own web font.

## Gates (verified on final.mp4)
- G0 duration 64.40 s — PASS · G2 no empty frame — PASS · G3 end-hold 0.73 s, final shot 10% — PASS
- G5 style lint — PASS (all C/D/P/T/V rules)
- look.py contact sheet: `film/look-final/sheet.jpg`
