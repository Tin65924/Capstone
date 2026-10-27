# -*- coding: utf-8 -*-
"""Generate SCRIPT.docx and patch MCST-LMS_Audit_Redesigned.pptx presenter notes."""
import shutil, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from pptx import Presentation
import docx
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

PPTX = r"C:\Users\astro\OneDrive\Desktop\Capstone\Laboratories\MCST-LMS_Audit_Redesigned.pptx"
DOCX_OUT = r"C:\Users\astro\OneDrive\Desktop\Capstone\Laboratories\SCRIPT.docx"
BACKUP = r"C:\Users\astro\OneDrive\Desktop\Capstone\.opencode\temp\MCST-LMS_Audit_Redesigned_backup.pptx"

SCRIPTS = [
 dict(n=1, title="Capstone System IT Audit Engagement", presenter="Justin C. Batlangao",
 script=[
 "Good day, everyone. We are 404NotFound — Justin Batlangao, Glenn Darriguez, and Jenifer Labag. For our capstone, we audited our own system: the MCST Library Management System, which we built for the MCST Library under Head Librarian Calixto Nicolas Camangeg, the system owner.",
 "We tested our own capstone the way an external audit team would — with written criteria, sampled tests, and dated evidence. This is our Final Integrated Professional IT Audit Report, covering Labs 7 to 12. Our evidence closes on October 10, 2026; it covers audited builds BLD-04 and BLD-05; and the report is version 1.0 Final, dated October 20.",
 "Over the next twenty minutes we will show you what we audited, what we tested, what we found, and what we recommend. Let us begin with how the engagement came together.",
 ], qa=None),
 dict(n=2, title="Our Audit Journey — and Who Presents What", presenter="Justin C. Batlangao",
 script=[
 "Our audit was not six separate homework pieces — it is one continuous engagement across six labs, each dated, each building on the last. Lab 7 set scope, objectives, and criteria on September 19 — that is mine. Lab 8 mapped assets, data flows, and accounts on September 26 — Glenn. Lab 9 scored risks and compliance on October 3 — Justin again. Lab 10 evaluated controls, tests, and gaps, also October 3 — Glenn. Lab 11 produced findings and action plans on October 10 — and Jenifer, who also presents today's final integration from Lab 12.",
 "One thread holds it all together: every lab shares the same system, the same build records, and the same ID families — OBJ, RSK, CTL, TEST, GAP, FND. When you hear a number today, it traces to that same family in the final report.",
 "One last point: everyone built and cross-checked in every lab. Today we divided the telling, not the doing.",
 ], qa="Q&A cue: 'who did what' — each member created their own content, cross-reviewed another member's work, and contributed to every lab."),
 dict(n=3, title="The System We Audited", presenter="Justin C. Batlangao",
 script=[
 "What exactly did we audit? The MCST LMS is our own Flask 3.1 web application — catalog, borrowing and returns, fines, requests, buying, stock count, and reports, modules MOD-01 to MOD-08 — running PostgreSQL on Render with timed pg_dump backups, and Google school-email login restricted to @mcst.edu.ph, with role checks on every page. Students and faculty borrow; desk staff circulate; admins manage.",
 "Because we own the code, we could give the audit full transparency — every code path, every screen. But we deliberately treated it like any external client: written criteria, sampled tests, dated evidence.",
 "The build lineage on the right is real git history, frozen before every lab — BLD-01 through BLD-05. And note BLD-06, build c20f98e: it came after our October 10 evidence cutoff. It is excluded from our conclusions and disclosed separately, as you will see later.",
 ], qa="Q&A cue: 'why audit your own system?' — the partner benefit is real findings before live use; integrity is handled by evidence anyone can re-open (screenshots, git, logs)."),
 dict(n=4, title="Audit Objectives and Scope (Lab 7)", presenter="Justin C. Batlangao",
 script=[
 "Our four objectives came from Lab 7 and were approved with the library. OBJ-01: access control — only the right people reach the right pages, with rights granted by the Access Approver, ORG-02. OBJ-02: build truth — the frozen build really supports the library work we claim. OBJ-03: traceability — every borrow, fine, and change leaves a named record. OBJ-04: data safety — backup, settings, and reports protect data and hide secrets.",
 "Each objective anchors to written criteria, CRT-01 to CRT-04. For example, CRT-01 requires role rules in code, a roles table, and school approvals; CRT-03 requires thin pages, POST-only writes, and audit-trail rows.",
 "Our procedures stay inside safe boundaries: records and code inspection, configuration review, walkthroughs, and small demo tests — nothing changed, nothing harmed. We did not do attack testing, live restores, or touch real student data. Demo environment only — and that limit is stated in every conclusion we make.",
 ], qa="Q&A cue: 'why no attack test?' — outside the approved procedures; we promised no over-claim and kept that promise."),
 dict(n=5, title="How We Worked — Evidence First", presenter="Justin C. Batlangao",
 script=[
 "How did we work? The same four-step method through Labs 7 to 12, with every result carrying an ID chain. First, inspect — records, code paths, configuration, forming the EVD-09 and EVD-10 evidence series. Second, walk through — real screens in the demo build, screenshotted only after names are cleaned. Third, test — the TEST-01 to TEST-06 samples. Fourth — the discipline layer — every increment was cross-reviewed by another team member with a written challenge and a recorded resolution: the REV-01 to REV-14 log.",
 "On AI: we used it only for wording fixes, count double-checks, and task clarification. Every suggestion was validated against real records, and it was never an evidence source. All six AI rows are disclosed in the portfolio, AIV-01 to AIV-06, with what we verified and what we revised.",
 ], qa="Q&A cue: 'did AI write your audit?' — no; it shortened sentences and re-checked math; every AI row carries Accept/Revise plus what was verified."),
 dict(n=6, title="Architecture and Trust Boundaries", presenter="Glenn Patrick B. Darriguez",
 script=[
 "Now the system underneath — Figure 2 of our report. Walk the picture with me. A borrower connects over HTTPS to the Flask application. Behind the app, it talks SQL only to PostgreSQL. Google sits outside as an identity provider — it proves who you are; it never touches library data. On the platform side, a scheduler copies the database on a timed pg_dump, and administrators change settings through the highest-trust path.",
 "That is six trust boundaries mapped and named, DEP-01 to DEP-06: public entry, the database line, the Google line, the staff upload path, the backup path, and the admin path.",
 "Three points to hold. There are seven registered account types, and the one-time bootstrap admin used for first setup was closed and verified — that is ACC-07. Secrets — database URLs, OAuth keys — live only in environment configuration: never in the app code, never inside this report. And every line on this map names its evidence source.",
 ], qa="Q&A cue: 'what protects the database?' — env-held credentials plus the admin-only path (DEP-02); provider-side access follows school/provider rules."),
 dict(n=7, title="How Data Moves Through the Library", presenter="Glenn Patrick B. Darriguez",
 script=[
 "Figure 3 shows how data moves through the library, across five flows, FLOW-01 to FLOW-05. FLOW-01 is the heart: borrow, return, and fines — borrowing honors the limits of three books for students and five for faculty, the fine is the rate times days late, and deletion is archive-before-delete, never a hard erase of an active record. FLOW-03 is the CSV import: headers must map, and bad rows are skipped — not half-inserted — with every skip logged. FLOW-04 is login: school email only through Google, and the first-login bootstrap admin closes after setup.",
 "Every flow carries written rules for validation at entry, where data is stored, which channel it moves over, and how long it may be kept. And notice the in-line checks: a can-borrow check before a loan, unique accession numbers before a copy is added, approval before a purchase is bought.",
 "One flow to remember: borrower data sits in PostgreSQL, and its views should be role-limited under CMP-01 and CMP-02. The weak part of that picture is Finding FND-03 — coming up.",
 ], qa="Q&A cue: 'where does borrower data sit?' — PostgreSQL (AST-04); views should be role-limited per CMP-01/02 — the weakness is FND-03."),
 dict(n=8, title="What Could Go Wrong — Risk Profile (Lab 9)", presenter="Justin C. Batlangao",
 script=[
 "What could go wrong? Lab 9 scored eight risk scenarios — likelihood times impact — adjusted for the safeguards we could actually see in the build. Three are High priority. RSK-01: account takeover — a leaked staff password meets no second check; residual sixteen of twenty-five. RSK-04: recovery unproven — backups are logged, but a restore was never demonstrated; residual eight. RSK-07: borrower data exposed through wide staff views and an open export path. Those three drive our three findings.",
 "Two principles in our scoring. First: residuals only drop when a safeguard is proven in the build — the backup log is real, so RSK-04's impact drops from five to four. Second: unmatched safeguards change nothing — RSK-05, a single-provider outage, has no verified safeguard, so nothing drops, and the owner accepts it with a paper control: manual desk steps for outage days.",
 "Our compliance base is the Data Privacy Act of 2012 plus school access rules — CMP-01 to CMP-07.",
 ], qa="Q&A cue: 'why is RSK-01 a 16?' — likelihood 4 x impact 4: passwords leak often and no second check exists; the mitigation is the second factor, aiming for 8."),
 dict(n=9, title="Controls We Evaluated and What the Tests Showed (Lab 10)", presenter="Glenn Patrick B. Darriguez",
 script=[
 "With risks named, we looked for the controls that address them — eight controls, CTL-01 to CTL-08 — and tested six under TEST-01 to TEST-06 on build BLD-04, on October 3. Four came back Effective; two came back Partially Effective.",
 "TEST-01, wrong-role entry: all ten role-gated pages blocked the intruder — ten out of ten, zero exceptions. TEST-02, CSV upload with two bad rows: six good books added, both bad rows skipped and logged. TEST-03, a full borrow-return-fine cycle: the fine matched the rate-times-days formula, and the audit trail logged the events. TEST-04, delete discipline: a delete on an active book was refused; the archived one was allowed.",
 "Then the two partials. TEST-05, the backup log: fourteen runs, fourteen logged — perfect logs, but zero proof any of them restore. TEST-06, settings changes: the change is logged with a name — but there is no approval step before it takes effect.",
 "A word on honesty: these are real populations, not cherry-picked samples — all ten pages, the whole fourteen-row log, the entire CSV. Small system, full coverage. The two partials line up with gaps GAP-02 and GAP-05 — and those gaps are exactly where two of our three findings come from.",
 ], qa="Q&A cue: 'does Partially Effective = failed?' — no: the control partly works (backups run and are logged) but misses the objective — restore proof, approval step."),
 dict(n=10, title="Key Findings — Three High Items", presenter="Ma. Jenifer L. Labag",
 script=[
 "From all that evidence, five finding candidates crossed our desk in Lab 11, and we screened each with four questions: is the evidence sufficient, is it material, is it inside our scope, and what exactly happened? Here are the honest answers.",
 "FC-01 and FC-02 became findings FND-01 and FND-02. FC-03 is an observation, OBS-01 — a small fix backlog; not a finding, because it is fixable small and tracked, not hidden. FC-04 became FND-03. FC-05 is closed and compensated: the risk it described is already offset by logging plus a monthly owner review.",
 "The result: three formal findings, all High. And we want to be explicit — not every candidate became a finding, because inflating the register would dilute the real ones. Materiality disciplined this list, and every one of the five screening decisions carries its evidence IDs.",
 ], qa="Q&A cue: 'why not more findings?' — materiality: small items would dilute; they are tracked (OBS-01 backlog, FC-05 control note), not hidden."),
 dict(n=11, title="Finding 1 — Staff Login Without Second Check", presenter="Ma. Jenifer L. Labag",
 script=[
 "Finding one, FND-01 — and word care matters here, so follow the five steps. Condition: on BLD-05, no staff or admin login asks for a second check — the screens confirm it. TEST-01 was ten-for-ten on blocking the wrong role, but blocking the wrong role is not the same as stopping a stolen password. Criteria: CRT-01 and CMP-03 say access must fit the role and login must stop outsiders — ORG-02 is the approver in that line. Cause: the second step was never built; the code read shows no second step. Effect: one leaked staff password can read and change all borrower, loan, and fine data. We say exposure, not breach — nothing was lost or seen broken.",
 "Why High: residual risk sixteen of twenty-five, full loan and fine data at stake, a single point of failure on the main gate, and every borrower and staff member affected. The limitation, stated on the workpaper: no attack testing was allowed.",
 "The recommendation, REC-01: the Access Approver turns on a second check for staff and admin logins — the target is that a stolen password alone fails, and we re-run TEST-01 plus login attempts to prove it.",
 ], qa="Q&A cue: '10/10 role tests passed — why still a finding?' — role checks stop the wrong people, not a thief with the right password; challenged in REV-13-02."),
 dict(n=12, title="Finding 2 — Restore Never Tested", presenter="Ma. Jenifer L. Labag",
 script=[
 "Finding two, FND-02 — the restore provability point. Condition: fourteen of fourteen backup runs are logged for September and October, completed status — and zero restore demonstrations exist anywhere. Criteria: CMP-05 with CRT-04 requires more than copies; it requires that recovery is actually possible with approval. Cause: a restore needs owner approval and test data, and it was never scheduled — the owner confirmed that, and our search found no record. Effect: if the database dies, desk work may stop for days, and loans and the catalog may be unrecoverable.",
 "Why High: because a backup log proves copies exist — it proves nothing about them coming back. If recovery fails once, the loss is total: every loan, every catalog record. This was the item our cross-review challenged hardest — REV-13-01 — and we kept it High on effect, not on the score alone.",
 "And the safety point: restoring the live database was outside our approved scope — that is SCP-03 — so the remedy itself stays safe. REC-02: the System Admin runs one witnessed restore onto a test copy, files the approved steps, and verification is simply reading the restore log. One admin hour: the cheapest fix in this report, and the largest single step in assurance gained.",
 ], qa="Q&A cue: 'why not restore the real DB?' — out of approved scope; the test-copy exercise gives the proof without touching live data."),
 dict(n=13, title="Finding 3 — Borrower Data Exposure", presenter="Ma. Jenifer L. Labag",
 script=[
 "Finding three, FND-03 — borrower data exposure. Condition: staff roles open full borrower rows — name, school ID, fines — on desk screens; reports show names; and the export path has no extra rule between the staff role and the file. Criteria: CMP-01 and CMP-02 — the Data Privacy Act line and the school borrower-privacy practice — with CRT-01: private data only for roles with a genuine need to know, and names hidden in reports. Cause: the views were built for desk speed, and the export path was never fenced — the code read found no rule. Effect: a curious or rogue staff member could read or copy many student records. Again — exposure; we saw no misuse.",
 "Why High has a two-part answer: many students are affected, and real privacy-law obligations attach. And note this does not conflict with TEST-01 passing — getting in and seeing wide are different questions. Role checks close the door; they do not narrow the room. Limitation: full export was never tested — we had no right to try.",
 "REC-03: the Privacy role narrows views to need-to-know, hides names in reports and exports, and turns on an export log.",
 ], qa="Q&A cue: 'can staff export everything today?' — we did not test export (SCP); the finding rests on wide views seen plus no export rule found; wording softened accordingly."),
 dict(n=14, title="How Conclusions Stand on Evidence — The Chain", presenter="Glenn Patrick B. Darriguez",
 script=[
 "So how do our conclusions stand on evidence? Here is FND-01 traced end to end — and every finding carries the same chain. Step one, TEST-01: ten out of ten wrong-role visits blocked, and no second step visible on any login screen. Step two, that behavior is locked into evidence — EVD-12-01 and EVD-13-01 — clean, sanitized, dated screenshots tied to the build. Step three, the gap is identified as GAP-01 against controls CTL-01 and CTL-02. Step four, FND-01 is written up in full: condition, criteria, cause, effect, severity. Step five, the response is set — REC-01 with owner and result target — tracked as MAP-01.",
 "FND-02's chain runs TEST-05 to EVD-12-04 to GAP-02. FND-03's runs through TEST-01 and the EVD-10 and EVD-13 series to GAP-04.",
 "In total, twenty evidence items are indexed — EVD-09-01 through EVD-13-02 — each with its source, date, privacy treatment, and written limitation. And one more thing: evidence protection. No names, counts only, secrets excluded — nothing sensitive ever left the controlled group folder. Ask us for any ID, and we can show you exactly the condition we saw.",
 ], qa="Q&A cue: 'could screenshots be faked?' — screenshots are only part; the role test uses live behavior, the backup log comes from the system itself, and dates/git tie everything to builds."),
 dict(n=15, title="What We Recommend — and Honestly, What It Is Not Yet", presenter="Ma. Jenifer L. Labag",
 script=[
 "So what do we recommend — and honestly, what it is not yet. Three recommendations, each with a named owner, a priority, a target, and a verifiable result.",
 "REC-01 — High, next release: a second login check for staff and admin accounts, owned by the Access Approver; the result must be that a stolen password alone fails. REC-02 — High, before our final defense: one witnessed restore on a test copy plus filed restore steps, owned by the System Admin; the result is that recovery becomes demonstrable, verified by reading the restore log. REC-03 — High, next release: narrow staff views to need-to-know, hide names in reports and exports, and log every export, owned by the Privacy role.",
 "Now the honest part: all three are our proposals — proposed, not confirmed. No action is claimed as management-approved unless the library owner confirms it. The good news is the price tag: REC-02 is roughly one admin hour; REC-01 and REC-03 are small development tasks for the next release. Each has a verifiable target, so at follow-up we simply re-run the tests. And if the library declines any of these, the residual risk stays — and the report records that acceptance explicitly. Our job is disclosure, then follow-up; theirs is the decision.",
 ], qa="Q&A cue: 'what if the library says no?' — the residual stays; the report records owner acceptance explicitly; our job is disclosure, then follow-up."),
 dict(n=16, title="What This Audit DOES NOT Say (professional honesty)", presenter="Justin C. Batlangao",
 script=[
 "Now the professional-honesty slide: what this audit does not say. Read our limitations plainly. All evidence comes from the demo build and the test site — never live production data. No attack testing, no live restore, no real student records — those are the approved scope limits. Two compliance items stay not determined: CMP-05, because a restore needs approval we could not obtain unilaterally, and CMP-07 on Google's terms. Our samples are small because the system is small, and the populations are honestly listed. So our conclusion is that the system needs improvement — not that it is broken: four of the six tested controls are fully effective.",
 "Finally, change after the cutoff. BLD-06, build c20f98e, landed October 11 to 20 — inventory shared-session fixes, set-based reconcile, a condition modal, and Philippine-time timestamps. None of that was tested: it arrived after the cutoff, so it is disclosed — not absorbed into results. That is the Lab 12 manual rule, applied word for word. One flag for follow-up: once deployed, re-run TEST-03, because timestamps could shift fine displays.",
 ], qa="Q&A cue: 'does the timestamp commit break your conclusion?' — no; conclusions cover BLD-04/05 up to cutoff; BLD-06 gets its own follow-up test after deploy."),
 dict(n=17, title="Overall Conclusion — Needs Improvement", presenter="Justin C. Batlangao",
 script=[
 "Our overall conclusion: the MCST LMS needs improvement, pending remediation — a fair verdict, and here is why.",
 "What works, with evidence we showed today: wrong-role access blocked ten out of ten — control CTL-01; CSV checks that add good rows and skip bad ones, with logs; a full audit trail on desk work with guard rails on deletes; and backups running on schedule — fourteen of fourteen logged.",
 "What must improve — the three High findings, all still Proposed: a second login check under FND-01, one witnessed restore under FND-02, and narrower views with export control under FND-03. Then — before live borrower data ever touches this system — a follow-up review and a BLD-06 re-test.",
 "We debated whether a different verdict fits — that was a real cross-review argument — but three High findings and no confirmed management response mean improvement must come first. A system that holds student data should not go live with an unproven restore and a single-factor gate.",
 ], qa="Q&A cue: 'why not Satisfactory instead?' — we debated it in REV cross-review; three High findings plus no confirmed management response means improvement is required first."),
 dict(n=18, title="Thank You — Questions?", presenter="All",
 script=[
 "Justin: Thank you for your time. Anyone may direct a question to any of us — all three of us reviewed the whole engagement, so no question has to wait for one person. A quick map: Justin owns scope, risks, and the conclusion; Glenn owns the system, controls, and tests; Jenifer owns findings and action plans.",
 "Jenifer: If you ask for evidence, we can bring the report on screen — the twenty-item EVD index, the test workpapers, the review and AI logs, and the build lineage.",
 "Glenn: Prepared answers, in case: the fine formula is rate times days late under settings control TEST-06; the Data Privacy Act basis is CMP-01; the post-cutoff build is BLD-06 — disclosed and excluded; and the action plan is verified by re-running TEST-01 and TEST-03, reading the restore log, and reviewing the export log once they exist.",
 ], qa="Q&A cue: about 3 minutes of Q&A; use the report if asked to show evidence — sections and IDs on request."),
]

# ---------- build SCRIPT.docx ----------
d = docx.Document()
style = d.styles['Normal']
style.font.name = 'Calibri'
style.font.size = Pt(11)

t = d.add_paragraph()
r = t.add_run("Presenter Script — MCST-LMS Final IT Audit Presentation")
r.bold = True; r.font.size = Pt(18); r.font.color.rgb = RGBColor(0x1F, 0x3B, 0x63)
t.alignment = WD_ALIGN_PARAGRAPH.CENTER

meta = d.add_paragraph()
meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
meta.add_run("404NotFound\nMCST Library Management System — Final Integrated Professional IT Audit Report (Labs 7-12)\n"
             "Source deck: MCST-LMS_Audit_Redesigned.pptx  |  Report 1.0 Final, 2026-10-20  |  Evidence cutoff 2026-10-10\n"
             "Presenters: Justin C. Batlangao (engagement, risks, conclusion) | Glenn Patrick B. Darriguez (system, controls, tests) | Ma. Jenifer L. Labag (findings, actions)\n"
             "Target pace: ~140 words/minute; total ~21-22 minutes followed by Q&A.").font.size = Pt(10)
meta.runs[0].font.color.rgb = RGBColor(0x55, 0x55, 0x55)

total_words = 0
for s in SCRIPTS:
    words = sum(len(p.split()) for p in s['script'])
    total_words += words
    mins = words / 140.0
    m, sec = divmod(int(round(mins * 60)), 60)

    h = d.add_heading(level=1)
    h.add_run(f"Slide {s['n']} — {s['title']}")
    pr = d.add_paragraph()
    rr = pr.add_run(f"Presenter: {s['presenter']}   |   Est. {m}:{sec:02d} at ~140 wpm")
    rr.bold = True
    rr.font.size = Pt(10)
    rr.font.color.rgb = RGBColor(0x50, 0x50, 0x50)
    for para in s['script']:
        d.add_paragraph(para)
    if s['qa']:
        q = d.add_paragraph()
        q.add_run(s['qa']).italic = True
        for run in q.runs:
            run.font.size = Pt(10)
            run.font.color.rgb = RGBColor(0x77, 0x50, 0x50)
d.add_page_break()
tail = d.add_paragraph()
tail.add_run(f"Total scripted words: {total_words} (approx. {total_words/140:.1f} minutes at ~140 wpm, excluding Q&A). "
             "The same per-slide script is stored in each slide's presenter notes inside MCST-LMS_Audit_Redesigned.pptx.").italic = True
d.save(DOCX_OUT)
print("DOCX saved:", DOCX_OUT)

# ---------- patch pptx notes (backup first) ----------
shutil.copyfile(PPTX, BACKUP)
print("Backup saved:", BACKUP)

p = Presentation(PPTX)
slides = list(p.slides)
assert len(slides) == len(SCRIPTS), f"slide count {len(slides)} != script count {len(SCRIPTS)}"
for slide, s in zip(slides, SCRIPTS):
    tf = slide.notes_slide.notes_text_frame
    tf.text = f"[{s['presenter']}]\n" + "\n\n".join(s['script']) + (f"\n\n{s['qa']}" if s['qa'] else "")
p.save(PPTX)
print("PPTX notes patched for", len(SCRIPTS), "slides")
print(f"TOTAL WORDS: {total_words}, ~{total_words/140:.1f} min")
