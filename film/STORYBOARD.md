# MCST LMS Launch Film — STORYBOARD.md (motionmaxxing, storyboard-only)

Format: 1920x1080, 30fps, 20s = 600f, silent (no ElevenLabs key assumed).
Source: real templates only. No render yet, no gate numbers claimed.

## 1. Brand inventory (from repo, not invented)

| Slot | MCST Library value | Source |
|---|---|---|
| Logo shape | Square navy badge, white serif "L", rounded 22px | `Project_Tracker_Site/index.html:7`, `app/static/images/Library_Logo.jpg` |
| Core control | Search bar: `Search by title, author, or ISBN...` + navy Search button | `app/templates/public/index.html:17-24` |
| Material | Paper cards on `#f7f7f7`, white surfaces, ring-1 slate borders, 12px radius | `base.html:19-21`, `dashboard.html:32-43` |
| Key verb | Discover / Search → Borrow | `index.html:6-10` "Discover Knowledge" |
| Success moment | Search resolves to a holdable book + due date in My Loans | `catalog.html` grid, `bookinfo.html`, `dashboard.html` |
| Voice | Plain academic: "Access thousands of books across our academic network." | `index.html:9-10` |
| Colour logic | Ink `#0f172a`, primary navy `#1e3a8a`, bg `#f7f7f7` / dark `#0f172a`. Accent = navy button, never link-blue. | `base.html:14-32` |
| Type | Manrope 400-800, tight tracking headlines; Material Symbols for icons | `base.html:10-12` |
| Never do | Playful startup gradients, stacked stats, "future of libraries" slogans | — |

## 2. PAGE + one true thing

- Problem: Students think the library is a room you walk to.
- Audience: MCST students/faculty + capstone panel.
- Goal: Believe catalog search ends with a book in hand, in seconds.
- Emotion: Quiet competence, relief.
- One true thing: The search bar on the public home *is* the library front door (real `q` param → `cataloging.public_catalog`).

Assumption: film follows one real task — search "Introduction to Algorithms" → open book → Borrow → lands in dashboard loans. Uses `books_seed.csv` titles so nothing is invented.

## 3. Three ideas (different KINDS), pick one

1. **UI documentary of one task (picked):** One continuous search-to-borrow, shot as magnified UI fragments through a camera. Search text becomes results grid becomes cover becomes loan row becomes mark.
2. **Held shot:** Single 20s locked macro of New Arrivals shelf breathing with light drift, one cursor enters once to borrow. Rejected: too still for a system with 6 stubbed modules; risks dead frames.
3. **Typographic essay:** Manrope words "title. author. ISBN." set at speech rhythm, UI only as punctuation. Rejected: says the claim, doesn't perform it; fails "show it, then say it."

Cover-the-logo test: with logo covered, only (1) still reads as *this* catalog (navy Search pill, Title/Author/ISBN chips, Manrope cards). Competitor-swap fails for (2)/(3). Pick (1).

## 4. World and time

- Ground: not flat swatches. Act 1-3: captured paper `#f7f7f7` as lit desk surface with grain + soft top light; Act 4: deep navy `#1e3a8a → #172554` reading room gloom. Depth via real drop shadows from Tailwind cards, camera parallax 40-80px.
- Light: one soft key top-left throughout; hero book cover gets rim + 8% grain.
- Hero moment: beat 4 — physical book cover lifts from grid at 2.2x oversize, decelerates (softLand), Borrow press squashes 2f, loan row answers 1f later. Worth a screenshot.
- Sound (planned, not built): room tone + 2 hits (keystroke return, borrow thunk). Silent for now.
- Carrier: the query string ink. It travels every seam, never pinned.
- Film shape: claim → cut → proof → cta. Proof = 9s (45%, largest share). At most 1 beat is "the point" (beat 4).

## 5. Beat table (buys / moves / handoff / frames)

| # | Role / frames | Buys | Copy (real) | What moves (entry / exit) | Handoff to next |
|---|---|---|---|---|---|
| 1 | Hook 0-90f (0-3s) | the viewer: search is instant | `Search by title, author, or ISBN...` + typed `Introduction to Algorithms` | Cursor enters 3x oversize, parks 6f, types words 4-6f apart irregular; entry softLand 12f; no exit — cut mid-keystroke | Last typed "s" freezes mid-caret blink → becomes first result title |
| 2 | Turn 90-240f (3-8s) | filters are real, not decoration | Chips: All / Title / Author / ISBN; sort: relevance | Grid crashes in from 1.4x, decelerates; chips actuate 8f each; leave accelerates right 10f, cut on motion | Selected card cover scales 1.0→2.2x through the cut, same pose |
| 3 | Proof-a 240-390f (8-13s) | this book exists and is holdable | `bookinfo.html` fragment: title, author, availability badge, Borrow button | Camera dives 1.3x to fragment ≥0.6W, text ≥0.06H; Borrow squashes 2f on press, answers 1f later; cut before release | Borrow button navy fill floods 12f → becomes dashboard loan row ground |
| 4 | Proof-b HERO 390-510f (13-17s) | borrowing lands somewhere | Dashboard `My Loans` row: cover thumb + due date (from seed data) | Row slides in from edge (accelExit inverse), counter steps per-frame to due date; designed breath 18f with light drift only | Loan row ink condenses → library "L" badge, crash from 3.5x |
| 5 | CTA 510-600f (17-20s) | name the door you just used | `Discover Knowledge.` Manrope 800, 9%H, centered y 0.50 | Mark lands decelerating from 3.5x (snapSettle 14f); type unmasks, no fade; resolved hold 30f = 1.0s | Ends on designed stillness, in motion system |

Total: 5 shots, cuts every ~3-5s, no fades between scenes, nothing grows from zero, one spring max (beat 5).

## 6. Gate pre-check (before building)

- G1 proof readable: beats 2-4 framed ≥0.55W, UI text ≥0.05H via camera 1.3-2.2x. To verify on `look/sheet.jpg`.
- G3 end card short: hold 1.0s ≤1.4s; final shot 3s = 15% ≤25%. Pass by construction.
- G4 one hero: 1 lit object/frame (caret, selected card, Borrow button, loan row, mark). No split panels.
- G5 no page chrome by construction: no corner brand, no counters/timecodes/progress bars, no kicker-over-headline, no headline-left/device-right, no letter-typed headline (typing only inside real input), no vibe-cards.

## 7. Picture sources to capture (no invented UI)

1. `app/templates/public/index.html` search hero (light + dark)
2. `app/templates/public/catalog.html` grid + filter sidebar at 1400px
3. `app/templates/public/bookinfo.html` detail fragment
4. `app/templates/dashboard/dashboard.html` loans table
5. `app/static/images/Library_Logo.jpg` official mark only

## 8. Next steps to render (blocked on toolchain)

```powershell
winget install Gyan.FFmpeg Google.Chrome
git clone https://github.com/Tejashmakwana/motionmaxxing $env:USERPROFILE\.claude\skills\motionmaxxing
bash ~/.claude/skills/motionmaxxing/install.sh
# then: hardest beat first (beat 4), stills, render --scale 0.5, look.py + lint.mjs, NOTE.md
```

No `NOTE.md` gate numbers yet — nothing rendered or looked at. Two honest passes minimum once toolchain lands.
