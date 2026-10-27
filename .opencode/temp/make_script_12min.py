# -*- coding: utf-8 -*-
"""12-minute presenter script: regenerate SCRIPT.docx + patch PPTX notes."""
import shutil, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from pptx import Presentation
import docx
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

PPTX = r"C:\Users\astro\OneDrive\Desktop\Capstone\Laboratories\MCST-LMS_Audit_Redesigned.pptx"
DOCX_OUT = r"C:\Users\astro\OneDrive\Desktop\Capstone\Laboratories\SCRIPT.docx"
BACKUP = r"C:\Users\astro\OneDrive\Desktop\Capstone\.opencode\temp\MCST-LMS_Audit_Redesigned_backup_12min.pptx"

SCRIPTS = [
 dict(n=1, title="Capstone System IT Audit Engagement", presenter="Justin C. Batlangao",
 script=[
 "Good day, everyone. We are 404NotFound — Justin Batlangao, Glenn Darriguez, and Jenifer Labag. We audited our own capstone system, the MCST Library Management System, built for the MCST Library under Head Librarian Calixto Nicolas Camangeg — and we tested it the way an external audit team would: written criteria, sampled tests, dated evidence. This is our final integrated report from Labs 7 to 12; evidence closes October 10, audited builds BLD-04 and BLD-05. Today: what we audited, what we tested, what we found, and what we recommend.",
 ], qa=None),
 dict(n=2, title="Our Audit Journey — and Who Presents What", presenter="Justin C. Batlangao",
 script=[
 "It was one continuous engagement across six labs, each dated. Lab 7 set scope and criteria; Lab 8, assets and flows; Lab 9, risks and compliance; Lab 10, controls and tests; Lab 11, findings and actions; Lab 12 integrated the final report. Every lab shares the same system, build records, and ID families — OBJ, RSK, CTL, TEST, GAP, FND — so every claim traces. And everyone built and cross-checked in every lab — today we divided the telling, not the doing.",
 ], qa="Q&A cue: 'who did what' — each member created their own content, cross-reviewed another member's work, and contributed to every lab."),
 dict(n=3, title="The System We Audited", presenter="Justin C. Batlangao",
 script=[
 "We audited our Flask 3.1 app — catalog, borrowing, fines, requests, buying, stock count, reports: modules MOD-01 to MOD-08 — on PostgreSQL with timed backups, and school-email login with per-page role checks. Because we own the code, we had full transparency, but we audited it like any client: criteria, samples, dated evidence. The build lineage on the right is real git history, frozen every lab — BLD-01 to BLD-05. BLD-06 came after the cutoff — excluded from conclusions, and disclosed later.",
 ], qa="Q&A cue: 'why audit your own system?' — the partner benefit is real findings before live use; integrity is handled by evidence anyone can re-open."),
 dict(n=4, title="Audit Objectives and Scope (Lab 7)", presenter="Justin C. Batlangao",
 script=[
 "Four approved objectives, OBJ-01 to OBJ-04: access control, build truth, traceability, and data safety — each anchored to written criteria CRT-01 to CRT-04. For example, CRT-01 requires role rules in code plus approver ORG-02; CRT-03 requires audited, POST-only desk actions. Our procedures were deliberately safe: record and code inspection, configuration review, walkthroughs, and small demo tests — nothing changed or harmed. No attack testing, no live restore, no real student data — and those limits are stated in every conclusion.",
 ], qa="Q&A cue: 'why no attack test?' — outside the approved procedures; we promised no over-claim and kept that promise."),
 dict(n=5, title="How We Worked — Evidence First", presenter="Justin C. Batlangao",
 script=[
 "One four-step method across Labs 7 to 12. First, inspect records, code, and configuration — the EVD-09 and EVD-10 series. Second, walk through real demo screens with names cleaned. Third, test — full populations where small. Fourth, cross-review: a written challenge and resolution for every increment, REV-01 to 14. On AI: wording fixes, counts, and clarification only — every suggestion validated, never an evidence source; all six uses are disclosed in the portfolio.",
 ], qa="Q&A cue: 'did AI write your audit?' — no; wording and math only; every AI row carries Accept/Revise plus what was verified."),
 dict(n=6, title="Architecture and Trust Boundaries", presenter="Glenn Patrick B. Darriguez",
 script=[
 "Figure 2: a borrower connects over HTTPS to Flask, which talks SQL only to PostgreSQL. Google only proves identity — it never touches library data. A scheduler runs the timed backup, and admins use the highest-trust path. Six trust boundaries, DEP-01 to DEP-06, each with a named evidence source. Seven account types — and the one-time bootstrap admin was closed and verified, ACC-07. Secrets live only in environment config: never in the code, never in this report.",
 ], qa="Q&A cue: 'what protects the database?' — env-held credentials plus the admin-only path (DEP-02)."),
 dict(n=7, title="How Data Moves Through the Library", presenter="Glenn Patrick B. Darriguez",
 script=[
 "Figure 3 shows five data flows, FLOW-01 to 05. Borrowing honors the three-and-five-book limits; fines are rate times days late; deletion is archive-before-delete. The CSV import requires headers and skips bad rows — logged. Login is school email only, with the bootstrap admin closed after setup. Every flow has written validation, storage, channel, and retention rules. Remember one thing: borrower data sits in PostgreSQL, and its views should be role-limited — the weak part is Finding FND-03.",
 ], qa="Q&A cue: 'where does borrower data sit?' — PostgreSQL (AST-04); views should be role-limited per CMP-01/02 — the weakness is FND-03."),
 dict(n=8, title="What Could Go Wrong — Risk Profile (Lab 9)", presenter="Justin C. Batlangao",
 script=[
 "Lab 9 scored eight risks — likelihood times impact, adjusted only for safeguards proven in the build. Three are High. RSK-01: account takeover — a leaked password meets no second check; residual sixteen of twenty-five. RSK-04: recovery unproven — backups logged, restore never demonstrated; residual eight. RSK-07: borrower data exposed through wide views and an open export path. Those three become our findings. One example of adjustment: RSK-04's backup log is real, so its impact drops five to four. Single-provider outage, RSK-05, is accepted with a paper control. Compliance base: the Data Privacy Act plus school rules.",
 ], qa="Q&A cue: 'why is RSK-01 a 16?' — likelihood 4 x impact 4: passwords leak often and no second check exists; mitigating aims for 8."),
 dict(n=9, title="Controls We Evaluated and What the Tests Showed (Lab 10)", presenter="Glenn Patrick B. Darriguez",
 script=[
 "Eight controls, CTL-01 to 08; six tests on BLD-04. Four came back Effective. TEST-01: wrong-role entry blocked on all ten pages — ten for ten, zero exceptions. TEST-02: CSV upload — six good rows added, two bad rows skipped and logged. TEST-03: a full borrow-return-fine cycle — the fine matched the formula. TEST-04: deleting an active book refused; archived allowed. Two came back Partially Effective. TEST-05: fourteen of fourteen backups logged — but zero proof any restores. TEST-06: settings changes logged with a name — no approval step. These were full populations, not cherry-picked samples. The two partials spill into our findings.",
 ], qa="Q&A cue: 'does Partially Effective = failed?' — no: the control partly works but misses the objective — restore proof, approval step."),
 dict(n=10, title="Key Findings — Three High Items", presenter="Ma. Jenifer L. Labag",
 script=[
 "Five finding candidates, screened against evidence, materiality, and scope. FC-01 and FC-02 became findings FND-01 and FND-02. FC-03 became OBS-01 — a small, tracked backlog, not worth a finding. FC-04 became FND-03. FC-05 is closed — its risk is already compensated by logging plus a monthly review. Result: three formal findings, all High. We did not inflate the register — materiality disciplined the list, and every screening decision carries its evidence IDs.",
 ], qa="Q&A cue: 'why not more findings?' — materiality: small items would dilute; they are tracked, not hidden."),
 dict(n=11, title="Finding 1 — Staff Login Without Second Check", presenter="Ma. Jenifer L. Labag",
 script=[
 "Finding one, FND-01. Condition: no staff or admin login asks for a second check on BLD-05. TEST-01 blocked the wrong role ten for ten — but that stops the wrong people, not a thief with the right password. Criteria, CRT-01 and CMP-03: login must stop outsiders. Cause: the second step was never built. Effect: one leaked password could read and change all borrower, loan, and fine data — we say exposure, not breach; nothing was lost. Severity: residual sixteen of twenty-five. REC-01 — ORG-02 turns on a second check; target: a stolen password alone fails.",
 ], qa="Q&A cue: '10/10 role tests passed — why still a finding?' — role checks stop the wrong people, not a thief with the right password; challenged in REV-13-02."),
 dict(n=12, title="Finding 2 — Restore Never Tested", presenter="Ma. Jenifer L. Labag",
 script=[
 "Finding two, FND-02 — recovery provability. Condition: fourteen of fourteen backups logged, zero restore demonstrations. CMP-05 with CRT-04 requires not just copies but provable recovery. Cause: a restore needs owner approval and was never scheduled. Effect: if the database died, desk work could stop for days. Why High: a backup log proves copies exist — nothing about them coming back; one failed recovery means total loss. Our cross-review kept it High on effect, not score alone. REC-02 — one witnessed restore on a test copy plus filed steps: one admin hour, the cheapest fix, the biggest assurance gain.",
 ], qa="Q&A cue: 'why not restore the real DB?' — out of approved scope; the test-copy exercise gives the proof without touching live data."),
 dict(n=13, title="Finding 3 — Borrower Data Exposure", presenter="Ma. Jenifer L. Labag",
 script=[
 "Finding three, FND-03 — borrower data exposure. Staff roles open full borrower rows — name, school ID, fines; reports show names; and the export path has no extra rule. Criteria: the Data Privacy Act line plus CRT-01 — private data only for need-to-know roles. Cause: views built for desk speed; export never fenced. Effect: a curious or rogue staff member could copy many student records — exposure, no misuse seen. And this stands despite TEST-01 passing, because getting in and seeing wide are different questions. REC-03 — narrow views to need-to-know, hide names, log exports.",
 ], qa="Q&A cue: 'can staff export everything today?' — export was not tested (SCP); the finding rests on wide views seen plus no export rule found."),
 dict(n=14, title="How Conclusions Stand on Evidence — The Chain", presenter="Glenn Patrick B. Darriguez",
 script=[
 "Is our conclusion supported? FND-01, traced end to end. TEST-01: ten for ten blocked, no second step visible. Locked into dated, sanitized evidence — EVD-12-01 and 13-01. The gap is GAP-01 against CTL-01 and 02. Then FND-01 written in full, and REC-01 with a named owner, tracked as MAP-01. FND-02 and FND-03 carry the same chain. Twenty evidence items are indexed, each with source, date, privacy treatment, and limitation. And nothing sensitive ever left the controlled folder — no names, counts only, secrets excluded.",
 ], qa="Q&A cue: 'could screenshots be faked?' — screenshots are only part; the role test is live behavior, logs come from the system, dates/git tie to builds."),
 dict(n=15, title="What We Recommend — and Honestly, What It Is Not Yet", presenter="Ma. Jenifer L. Labag",
 script=[
 "Three recommendations — each with an owner, a target, and a verifiable result. REC-01, High, next release: a second login check, owned by the Access Approver; result — a stolen password alone fails. REC-02, High, before our final defense: one witnessed restore plus filed steps, owned by the System Admin; result — recovery demonstrable. REC-03, High, next release: narrow views, hide names, log exports, owned by the Privacy role. The honest part: all three are our proposals, not confirmed. If the library declines any, the residual risk stays — and the report records that acceptance.",
 ], qa="Q&A cue: 'what if the library says no?' — the residual stays; owner acceptance recorded explicitly; disclosure, then follow-up."),
 dict(n=16, title="What This Audit DOES NOT Say (professional honesty)", presenter="Justin C. Batlangao",
 script=[
 "What this audit does not say. All evidence is from the demo build and test site — never live production data. No attack testing, no live restore, no real student records — the approved scope limits. CMP-05 and CMP-07 stay not determined. Samples are small because the system is small, and populations are honestly listed. And BLD-06, the October 11-to-20 build, arrived after the cutoff: untested — disclosed, not absorbed into results. One flag: re-run TEST-03 after deploy, because timestamps could shift fine displays.",
 ], qa="Q&A cue: 'does the timestamp commit break your conclusion?' — no; conclusions cover BLD-04/05 up to cutoff; BLD-06 gets its own follow-up test."),
 dict(n=17, title="Overall Conclusion — Needs Improvement", presenter="Justin C. Batlangao",
 script=[
 "Our verdict: Needs Improvement, pending remediation — a fair call. What works, tested: wrong-role access blocked ten for ten, CSV checks with logs, a full audit trail, and fourteen of fourteen backups on schedule. What must improve — the three High findings, all still Proposed: the second login check, one witnessed restore, and narrowed views with export control. Then a follow-up review and a BLD-06 re-test before any live borrower data. A system holding student data should not go live with an unproven restore and a single-factor gate.",
 ], qa="Q&A cue: 'why not Satisfactory instead?' — debated in REV cross-review; three High findings plus no confirmed management response means improvement comes first."),
 dict(n=18, title="Thank You — Questions?", presenter="All",
 script=[
 "Thank you. Any question can go to any of us — all three reviewed the whole engagement. Justin: scope, risks, conclusion. Glenn: system, controls, tests. Jenifer: findings and actions. Evidence on request: the twenty-item EVD index, test workpapers, and logs. Prepared answers: the fine formula is rate times days late under TEST-06; the privacy basis is CMP-01; BLD-06 is post-cutoff and excluded; and the plan is verified by re-running TEST-01 and TEST-03 plus reading the new logs.",
 ], qa="Q&A cue: keep about 3 minutes of Q&A; use the report if asked to show evidence."),
]

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
             "Target pace: ~140 words/minute; total ~12 minutes followed by Q&A.").font.size = Pt(10)
meta.runs[0].font.color.rgb = RGBColor(0x55, 0x55, 0x55)

total_words = 0
for s in SCRIPTS:
    words = sum(len(p.split()) for p in s['script'])
    total_words += words
    m, sec = divmod(int(round(words / 140.0 * 60)), 60)

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
