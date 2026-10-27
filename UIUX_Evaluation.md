# MCST LMS — UI/UX Evaluation

**Date:** 2026-10-16
**Repo:** `C:\Users\astro\OneDrive\Desktop\Capstone`
**Scope:** `app/templates/**/*.html`, `app/static/js/autosuggest.js`, `ajax_ui.js`, `charts.js`
**Lenses:**
- `PracticalSwan/agent-skills: frontend-design` v2.0 (Design Mode Router, WCAG 2.2 AA baseline, responsive, state completeness, verification protocol) + `references/accessibility-checklist.md` + `scripts/contrast-checker.py`
- `uxuiprinciples/agent-skills`: `uxui-evaluator`, `interface-auditor` (8 smells), `flow-checker` (onboarding/forms/dashboard/empty-states), `vibe-coding-advisor`, `ai-interface-reviewer` (N/A — no AI UI in Capstone)
- No `UXUI_API_KEY` — findings use internal taxonomy, not live API enrichment. Static-source audit only (no screen-reader run).

Skills installed locally: `.opencode/skills/frontend-design`, `uxui-evaluator`, `interface-auditor`, `vibe-coding-advisor`, `ai-interface-reviewer`, `flow-checker`.

## Executive Summary

Capstone is a Flask 3.1 + server-rendered Jinja2 + Tailwind LMS. Correct `frontend-design` mode is **product/workspace + commerce/service** (catalog discovery → borrow/reserve + staff operations). Task fit is good: responsive drawers, desktop-table/mobile-card splits, empty states (`No books found`, `All clear`, `No active loans`) are present.

Overall: **fair (~50/100)** — completable but blocked from `good/excellent` by systematic hard-gate failures:

1. Three parallel design systems (`base.html` Tailwind config vs per-module standalone `<html>` with inline `:root` + `.card/.btn` in `dashboard.html`, `cataloging.html`, `circulation.html`; `bookinfo.html` duplicates head/header/footer instead of extending `base.html`).
2. Placeholder-only inputs, custom listboxes that hide the native `<select>` with `aria-hidden`, icon-only buttons with `title`-only names, decorative Material Symbols exposed to AT.
3. 6 overlays (borrow/category/confirm/loan-filter/mobile drawers/notif panel) with missing `role=dialog`, no focus trap/return, inconsistent Escape.
4. Systematic contrast failure: `#94a3b8` on white 2.56:1 / on `#f8fafc` 2.45:1 (chart labels, helpers, icons).
5. Silent async failures (`autosuggest.js`, `notif_panel.html` `catch(()=>{})`), 6s auto-dismiss flashes with no `aria-live`, `alert()` in bulk import, `href="#"` dead CTAs.
6. Misleading commerce actions: card `Borrow` links to `book_info` (second navigation, not a borrow), grid/list Reserve behavior diverges.

No data loss / auth bypass found in UI layer. All issues below are fixable without schema changes.

## 1. Public Discovery (index/catalog/bookinfo)

> Commerce/service task inside a marketing hero. Catalog/bookinfo use service patterns but break trust rules.

| Severity | Location | Smell/Principle | Evidence | Remediation |
|---|---|---|---|---|
| critical | `public/index.html:17-19`, `public/catalog.html:255-257`, `public/catalog.html:96-100` | contrast-blindness / WCAG 3.3.2 + 1.3.1 | Search + year From/To placeholder-only, no `<label>`, `placeholder-slate-400` low contrast | Add `<label class="sr-only">` + `id`; keep placeholder as hint only; `aria-label="Year from"` for year fields |
| critical | `public/catalog.html:218-232,234-248` + `js/autosuggest.js:103-115` | mystery-navigation / APG Listbox failure | Native `<select class="sr-only" tabindex="-1" aria-hidden="true">` hidden from AT; custom `button + ul[role=listbox]` has no `aria-activedescendant`, no Home/End/type-ahead | Delete custom widget, style native `<select>`; or implement full APG Select-Only Combobox |
| critical | `public/catalog.html:247-279`, `public/bookinfo.html:247-279`, `components/confirm_modal.html:1-16` | dead-end-states + silent-errors | categoryModal, borrowModal, mobile drawers: no `role=dialog`, no `aria-modal`, no trap, no return-focus | Shared modal partial: `role=dialog aria-modal aria-labelledby`, trap Tab, Escape closes, return focus |
| warning | `public/catalog.html:354-362,424-439`; `bookinfo.html:210-226` | inconsistent-actions | List/grid `Borrow` both `<a href="book_info">` (navigation, not borrow); grid disables Reserve when available, list hides it | Cards: `View Details` only; Borrow/Reserve only on `bookinfo.html`; keep grid/list identical |
| warning | `public/bookinfo.html:1-80,281-297` vs `base.html:39,46` | Maintainability | `bookinfo.html` duplicates head/config/header/footer; footer `© 2024` vs dynamic year, missing `notif_panel` | Convert to `{% extends "base.html" %}`; delete duplicated head/footer |
| warning | `public/catalog.html:13-108` vs `119-210` | Maintainability / overloaded-screen | Desktop + mobile filter forms copy-pasted ~90 lines; desktop auto-submits `onchange`, mobile requires Apply | One `_filters.html` partial; explicit Apply/Clear both; remove auto-submit |
| warning | `js/autosuggest.js:222-242,264-280,429-432` | silent-errors | Suggest listbox no label, no `aria-expanded/activedescendant`, no `role=status`; fetch fail closes silently; scroll hides list; Tab hijacked | APG Combobox wiring + `aria-live` count + busy/error states; don't trap Tab |
| warning | `public/catalog.html:23,27,31,41,46,61,67` | click-cemetery (inverted) | Sort/Category/Type radios auto-submit on arrow — focus loss, no announcement | Remove `onchange submit`; single Apply + `role=status` count |
| warning | `components/flash_messages.html:3-13,17-28` | silent-errors / WCAG 4.1.3 | No `role=status/alert`, 6s fade, tiny `×` dismiss <24px | `aria-live polite` / `role=alert` for errors; don't auto-dismiss errors; ≥24px dismiss |
| warning | `public/catalog.html:305,309`; `bookinfo.html:218,232` | Hover-only info | View-toggle + disabled Reserve reason via `title=` only | Visible hint + `aria-describedby`; `aria-pressed/current` for toggle |
| warning | `public/catalog.html:367-371,450-454`; `index.html:121-125` | dead-end-states | `No books found` / `No new arrivals` with no CTA | Add `Clear filters` + `Browse catalog` + link to request flow; `role=status` counts |
| warning | `base.html:41-44` + `catalog.html:4` | Structure | `<main>` nested in `<main>`; `h3` filter headings before `h2` results; `bookinfo` no `h1`; no skip link | Unnest mains; single `h1`; `fieldset/legend`; skip-to-content link |
| suggestion | `public/index.html:28-46` | inconsistent-actions | Filter chips plain buttons, state = color + JS-injected icon, no `radiogroup` | `role=radiogroup` + `aria-checked` or native radios as pills; `aria-hidden` icon |
| suggestion | `public/catalog.html:458-482` | Targets + motion | Pagination ~28px height, page-wide transitions, no reduced-motion guard | `prefers-reduced-motion` guard; ≥24px targets + spacing |

**Band: fair (~50/100). Top 5:** label inputs → native select → honest card actions → `bookinfo` onto `base.html` → dedupe filters + trap modals.

## 2. Staff Workspace (dashboard/cataloging/circulation)

| Severity | Location | Smell/Principle | Evidence | Remediation |
|---|---|---|---|---|
| Critical | `cataloging.html:611-615,717-722,804-808,909-914`; `circulation.html:722-729` | silent-errors / focus | `openModal()` toggles class only; icon closes no `aria-label`; loan-filter modal has `role=dialog` but never moves/traps focus | Shared dialog primitive: focus-in, trap, Escape, focus-return; label all closes |
| Critical | `cataloging.html:638-639,831,884`; `circulation.html:413,470,475,515,535` | form-graveyard / WCAG 3.3.1 | `<label>` without `for`, inputs without `id`; Borrower lookup placeholder-only; `pattern="\d{6}"` tooltip-only, no inline error | `for/id` + `aria-describedby` error `<p>`; blur validation with specific text; render `?modal=` flashes inline |
| Critical | `cataloging.html:391-418,460-473`; `dashboard.html:214,235,366,140-143` | contrast-blindness / targets | Icon-only row actions `title`-only; chart dots `r=5` (~10px <24px); `.trend-dot:focus{outline:none}` removes focus | `aria-label="Edit {title}"`; ≥24px hit areas; restore `:focus-visible` ring; shared `.icon-btn` 32–44px |
| High | `cataloging.html:915-942,1068-1115` | dead-end-states / forms postflight | Bulk import: generic spinner, no counts/%, `location.reload()` on done, `alert()` on fail; copy says title+author required but route needs accession too | Determinate progress + row counts + `aria-live` + error table + Cancel + error CSV; fix copy; no `alert()` |
| High | `dashboard.html:248-284` | overloaded-screen / Cognitive Load | 7 equal-weight KPIs; two cards → same `cataloging_page` with `per Title` vs `per Accession` indistinguishable | 4–5 primary stats; `Titles (works)` / `Copies (accessions)`; `as of HH:MM` + units; labelled links |
| High | Staff tables: `cataloging:346-359`; `circulation:586-599,642-653` | Visual hierarchy / WCAG 1.3.1 | Zero `<caption>` / `scope="col"` in dashboard/cataloging/circulation/inventory/backup; nested copies table no name | `<caption class="sr-only">` + `scope="col"`; nested `aria-label="Copies of {title}"`; header color `#475569` |
| High | `circulation.html:479-494`; `cataloging.html:268-288` | mystery-navigation | Two divergent custom listboxes hide native with `aria-hidden`; state = color + appended check | Native `<select>` styled, or one APG listbox partial; delete duplicate JS `744-830` vs `1132-1178` |
| High | `circulation.html:532-544` | Destructive without confirm | Mark Lost (closes loan) / Mark Damaged via adjacent `formaction` buttons, no confirm, note `#9ca3af` ~2.6:1 | Confirm modal with loan impact + required reason; darken helper to `#64748b`; `aria-describedby` |
| Medium | `dashboard:32-43`, `cataloging:32-50`, `circulation:32-50` | inconsistent-actions / reuse | Each page standalone `<html>` with own `:root` + `.card/.btn`; tokens drift | One `staff_base.html` owning tokens/sidebar/flash/confirm modal |
| Medium | `dashboard:335,391`; `circulation:519,546` | Contrast | `text-[10px]/[11px] text-gray-400` helpers <4.5:1 | Bump to `#64748b` min, 12px where possible |
| Medium | `cataloging:345,502-581` | click-cemetery (mild) | Desktop `colspan=8` but 9 cols when Reason shows; history `min-w-[720px]` forces 2-D scroll; expanders no `aria-expanded` | Fix colspan; `aria-expanded/controls`; cards instead of raw x-scroll on mobile |
| Medium | Motion | WCAG 2.3.3 | `fadeIn/slideUp`, `scroll-behavior:smooth`, tooltip div no live region | `prefers-reduced-motion` guard; button semantics or data-table fallback for charts |
| Medium | `sidebar.html`, `librarian_sidebar_nav.html`, `admin_sidebar_nav.html` | mystery-navigation | 3 nav systems, `Overview` vs `System Overview`; active = color only, no `aria-current`; history pages drop hamburger | One role-filtered nav partial, `aria-current="page"`, shared drawer script |
| Medium | `user_history_detail:170-172`; `backup:9` | silent-errors | `confirm()` for fines; backup `<meta refresh=5>` loses focus/scroll | `confirm_modal` + undo window; polling + `aria-live` progress |

**Band: fair (~47/100). Top 5:** shared dialog + icon names → label + inline errors → import progress → `staff_base.html` → table semantics + stat reduction.

## 3. Auth and Member Flows

| Severity | Location | Smell/Principle | Evidence | Remediation |
|---|---|---|---|---|
| Critical | `auth/login.html:74` | dead-end-states | `href="#"` Contact IT Support — only recovery on Google-only login is dead | Real `mailto:`/help page or remove |
| Critical | `auth/role_select.html:64,77` | silent-errors | Program + Department both `name="department"`; one starts disabled | `program` vs `department`; server re-render with inline error |
| Critical | `auth/role_select.html:56-58` | Error Prevention | ID defaults to Student `\d{4}-\d{5}` before role picked; misleading Faculty error | No pattern until role chosen; `aria-describedby` + `aria-live` error |
| Critical | `auth/pending_approval.html:11-13,28-31` | dead-end-states / abandon-resume | Hardcoded Faculty copy; sole CTA `Back to Login` loops; no SLA/logout/contact/status-check | Dynamic role, SLA, logout/switch, contact, re-check |
| Critical | `users/users.html:634-641,962` | inconsistent-actions / destructive | Role `<select onchange=submit>` applies privilege instantly, no confirm (elsewhere uses `confirmFromData`) | Route through `confirm_modal` with consequences + audit note |
| Warning | `reservations:389-393,482-486` | Destructive | `expire` labelled `Cancel` submits immediately, no undo | Confirm + consistent `Expire/Cancel hold` + toast |
| Warning | `requests:203-210 vs 269-283` | inconsistent-actions | Bulk Approve/Reject POST directly; `reject-modal` dead code → rejections without reason | Wire bulk-Reject through modal; confirm bulk-Approve count |
| Warning | `user_profile:246-259,179-182,262,300,328,359` | dead-end-states | `Return at desk` vs `View Details` split unexplained; `Action required` + `At limit` static; 4 empties with bare `<p>` | One `View Details` pattern; actionable overdue/fines links; empty-state CTAs (`Browse Catalog`, `Request a Book`) |
| Warning | `user_history:148,171,192,222`; `user_notifications:70` | empty-states | Same bare empties; fines no pay path; notif empty no trigger explanation | Contextual CTAs + `How fines work / where to pay` |
| Warning | `users.html:496`; `requests:229,239`; `users:729,736` | Recovery | `Clear` drops only `q`; disabled pagination `<a href="#">` focusable dead targets | `Clear search` + `Reset filters`; disabled as `<span aria-disabled>` |
| Warning | `requests/user_request_book:113-173` | Forms preflight | No catalog-duplicate check, no `aria-describedby`, no preview/confirm, no ETA/reason | `Already in catalog?` check + confirm (`review in ~X days`) + queue/reviewer note |
| Suggestion | `settings:185-190`; `user_sidebar_nav:12`; `errors/error:6-19` | Prevention/navigation/recovery | hidden `0` after checkbox may shadow `1`; `Overview` ligature invalid icon; error no correlation ID/retry | Hidden before checkbox + dirty indicator; valid icon + `aria-current`; support code + `Try again` for 500/503 |

Flow preflight gaps: no ONE activation event; no role_select abandon-resume; empty programs/departments walls completion; no pending SLA/polling/switch-account; no duplicate-submit/input-preservation contract; member borrow/return state machine not exposed (waiting→allocated→claimed→expired→borrowed→returned).

Flow postflight: `ship_ready:false` — no step indicator on role_select; native pattern-only errors; badge updates without `aria-live`; reservation/role-change bypass confirm; terminal states without next steps.

## 4. Accessibility Hard Gates

| # | Gate (WCAG 2.2 AA) | Verdict | Key evidence |
|---|---|---|---|
| G1 | Names/labels/icons hidden | FAIL blocking | Placeholder-only: `catalog:96-100,255-257,507`, `circulation:413,470,475,515,535`. No `aria-hidden` on any decorative ligature (`catalog:8-9`, `navbar:22`, `dashboard:250-281`, etc.). Title-only toggles `catalog:305,309`; unnamed `bookinfo:61,252`. Positive: `circulation:567` search `aria-label`; `notif_panel:27,46` labelled; `flash:12` dismiss labelled |
| G2 | Keyboard/focus/listbox | FAIL blocking | Custom listboxes have arrows/Enter/Escape but no `aria-activedescendant`/Home/End, `tabindex=0` options, Tab leaves open (`catalog:776-780`). Autosuggest no `combobox/expanded/controls/activedescendant` (`autosuggest:103-115`); scroll drops context. No global `:focus-visible`; `dashboard:140-143` removes outline. Zero focus-return/initial-focus on 6 overlays |
| G3 | Contrast / color-alone | FAIL blocking (one pair) | PASS: `#1e3a8a`/white 10.36, `#64748b`/white 4.76, `#64748b`/`#f8fafc` 4.55, `#4f46e5`/white 6.29, badges 4.57–8.01. FAIL: `#94a3b8`/white **2.56**, `#94a3b8`/`#f8fafc` **2.45** (`dashboard:335,353,358,365,160-168`, `notif:103`, `charts.js:273-290`). Dark-mode `#94a3b8`/`#0f172a` 6.96 PASS. Dots pair color+text — acceptable |
| G4 | Target size ≥24px | FAIL (chart dots) | `dashboard:366` `r=5` (~10px), `charts.js:293` `r=4.5` (~9px) <24px. Info btn exactly 24px zero margin. Borrow/Reserve/pagination/flash-`×` below 44px recommendation |
| G5 | Reduced motion | FAIL | Zero `prefers-reduced-motion` hits; `scroll-behavior:smooth`, `slideUp/fadeIn`, card lift, toast fade unconditional |
| G6 | Tables | FAIL | No `<caption>`/`scope` anywhere; `overflow-x-auto` divs no `tabindex/role/label`; no sticky headers |
| G7 | Dialogs/drawers | FAIL blocking | Labelled only `circulation:685` + `dashboard:408` (still no focus lifecycle). Unlabelled `catalog:495`, `bookinfo:247`, `confirm_modal:1`, all drawers. Escape missing `bookinfo:300-306`, `confirm_modal:42-45`. No traps |
| G8 | Live regions | FAIL blocking | Flash no `role/status/alert`, 6s delete (`flash:26`); notif fetch/badge no live region; autosuggest no count announcement. Positive pattern: `ajax_ui.js:22-24` `role=status aria-live=polite` to reuse |

Measured with `contrast-checker.py --json` (Windows needs `--json` — pretty printer emits box-drawing that `cp1252` can't encode).

## Cross-Cutting Top 10 (ship order)

1. Dialog system: one `confirm_modal`/dialog partial with `role=dialog aria-modal labelledby`, focus-in/trap/Escape/return; apply to borrow/category/loan-filter/confirm/drawers/notif (`bookinfo:247`, `catalog:495`, `circulation:685`, `confirm_modal:1`).
2. Labels + inline errors: `for/id` + `aria-describedby` on all search/year/borrow/return/accession/ID fields; blur validation for `\d{6}` + role-dependent ID; `role=alert` errors (`cataloging:638-680`, `circulation:408-540`, `role_select:56-77`).
3. Kill `#94a3b8`-on-light: replace with `#64748b`+ for `dashboard:335,353,365`, `notif:103`, `charts.js:273-290`; 12px min for helpers.
4. Icon names + hide decoration: `aria-hidden=true` on all Material ligatures; `aria-label` on icon-only edit/delete/menu/close/view-toggles; `<label>` for placeholder-only inputs.
5. Live regions: flash `role=status/alert` + keep errors until dismissed; autosuggest `combobox` + count announcements; notif badge/list `aria-live` (reuse `ajax_ui.js:22-24`).
6. Honest actions: cards link to details only; Borrow/Reserve on `bookinfo`; identical grid/list; confirm for role-change/reservation Cancel/Allocate/bulk Reject; fix `Expire` vs `Cancel`.
7. Layout consolidation: `bookinfo` extends `base.html`; one `staff_base.html` for tokens/sidebar/flash/modals; one `_filters.html` partial; remove auto-submit radios.
8. Tables: `<caption class="sr-only">` + `scope=col` everywhere; fix `colspan` with Reason col; keyboard-scrollable regions (`tabindex=0 role=region aria-label`); mobile cards over raw x-scroll.
9. Targets + motion: ≥24px hits (chart dots via transparent stroke), `:focus-visible` ring globally (remove `outline:none`), `prefers-reduced-motion` kill-switch, 44px for Borrow/Reserve/Search.
10. Dead-ends + flows: real support link (no `href="#"`), disabled pagination as `<span>`, empty-state CTAs + request-book link, pending_approval SLA/switch/re-check, role_select empty-vocabulary path, import progress + error CSV.

## Appendix

Files audited: `base.html`, `public/index.html`, `public/catalog.html`, `public/bookinfo.html`, `dashboard/dashboard.html`, `admin_overview.html`, `admin_audits.html`, `cataloging/cataloging.html`, `circulation/circulation.html`, `user_history_list/detail.html`, `inventory/inventory.html`, `procurement/procurement.html`, `analytics/analytics.html`, `backup/backup.html`, `auth/login.html`, `role_select.html`, `pending_approval.html`, `users/user_profile.html`, `user_history.html`, `user_notifications.html`, `users.html`, `requests/requests.html`, `user_request_book.html`, `reservations/reservations.html`, `settings/settings.html`, `errors/error.html`, `components/navbar.html`, `sidebar.html`, `librarian/admin/user_sidebar_nav.html`, `notif_panel.html`, `flash_messages.html`, `confirm_modal.html`, `footer.html`, `static/js/autosuggest.js`, `ajax_ui.js`, `charts.js`.
