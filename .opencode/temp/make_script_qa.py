# -*- coding: utf-8 -*-
"""12-min scripts + 5-question Q&A bank per slide: SCRIPT.docx + PPTX notes."""
import shutil, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from pptx import Presentation
import docx
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

PPTX = r"C:\Users\astro\OneDrive\Desktop\Capstone\Laboratories\MCST-LMS_Audit_Redesigned.pptx"
DOCX_OUT = r"C:\Users\astro\OneDrive\Desktop\Capstone\Laboratories\SCRIPT.docx"
BACKUP = r"C:\Users\astro\OneDrive\Desktop\Capstone\.opencode\temp\MCST-LMS_Audit_Redesigned_backup_qa.pptx"

SCRIPTS = [
 dict(n=1, title="Capstone System IT Audit Engagement", presenter="Justin C. Batlangao",
 script=[
 "Good day, everyone. We are 404NotFound — Justin Batlangao, Glenn Darriguez, and Jenifer Labag. We audited our own capstone system, the MCST Library Management System, built for the MCST Library under Head Librarian Calixto Nicolas Camangeg — and we tested it the way an external audit team would: written criteria, sampled tests, dated evidence. This is our final integrated report from Labs 7 to 12; evidence closes October 10, audited builds BLD-04 and BLD-05. Today: what we audited, what we tested, what we found, and what we recommend.",
 ],
 qa=[
 "Why test our own system? Because the partner benefit is a real audit before the library depends on it — and integrity is protected by re-openable evidence (dated screenshots, git builds, system-generated logs), not just trust in one team.",
 "What exactly is the deliverable? One integrated report: 4 objectives, 8 risks, 8 controls, 6 tests, 3 findings, 3 recommendations, and a 20-item evidence index — all ID-linked (OBJ/RSK/CTL/TEST/FND/REC).",
 "How was it audited? Records and code inspection, a walkthrough of the demo build, six sampled tests, and cross-review — all with dated evidence anyone on the panel can request and re-verify.",
 "Who owns the system? The MCST Library, under Head Librarian Calixto Nicolas Camangeg (ORG-01); our group built and maintains it during the capstone, which gives the audit full code access without full audit freedom.",
 "One-line takeaway before we start? 'We tried our system the way a third party would — and caught three High gaps before it goes live.'",
 ]),

 dict(n=2, title="Our Audit Journey — and Who Presents What", presenter="Justin C. Batlangao",
 script=[
 "It was one continuous engagement across six labs, each dated. Lab 7 set scope and criteria; Lab 8, assets and flows; Lab 9, risks and compliance; Lab 10, controls and tests; Lab 11, findings and actions; Lab 12 integrated the final report. Every lab shares the same system, build records, and ID families — OBJ, RSK, CTL, TEST, GAP, FND — so every claim traces. And everyone built and cross-checked in every lab — today we divided the telling, not the doing.",
 ],
 qa=[
 "Who did what? Every member wrote their lab content, cross-reviewed another lab, and participated in all increments; today's speakers simply match their subjects — Justin: engagement and risks, Glenn: system and tests, Jenifer: findings and actions.",
 "Which lab mattered most? Lab 10, because it turned claims into test results — and Lab 11, because results only become findings after screening.",
 "Did later labs ever change earlier conclusions? No major rework; the prior-feedback log documents the small consistency fixes made at each increment, each with its closing date.",
 "Why all the IDs (OBJ, RSK, CTL, FND)? So any claim traces to its exact register entry in the report — it is how we keep ourselves honest and let you verify.",
 "What happened between Oct 10 and 20? Integration and independent QA only — final review FIN-01..03, no new findings, no new tests.",
 ]),

 dict(n=3, title="The System We Audited", presenter="Justin C. Batlangao",
 script=[
 "We audited our Flask 3.1 app — catalog, borrowing, fines, requests, buying, stock count, reports: modules MOD-01 to MOD-08 — on PostgreSQL with timed backups, and school-email login with per-page role checks. Because we own the code, we had full transparency, but we audited it like any client: criteria, samples, dated evidence. The build lineage on the right is real git history, frozen every lab — BLD-01 to BLD-05. BLD-06 came after the cutoff — excluded from conclusions, and disclosed later.",
 ],
 qa=[
 "What data does the system actually hold? Book catalog and copies, borrower records, loans and fines, and the audit trail — assets AST-02 through AST-07; backups sit in AST-08/10.",
 "How do we prove the code did not change mid-audit? Every lab freezes a git build (BLD-01..05 with commit hashes); all tests ran only against frozen builds.",
 "Is the Render site production? No — a test site; the library is not live yet. That is why 'demo evidence only' is an honest limitation, not an excuse, and it is stated on every conclusion.",
 "What is BLD-06? Build c20f98e, Oct 11-20 — inventory shared-session fixes, set-based reconcile, condition modal, PH-time timestamps; post-cutoff, so untested and disclosed.",
 "Could transparency be 100 percent? For code and screens, yes — that is the advantage of auditing our own build; for owner processes (restore approval), no, which is exactly Finding FND-02.",
 ]),

 dict(n=4, title="Audit Objectives and Scope (Lab 7)", presenter="Justin C. Batlangao",
 script=[
 "Four approved objectives, OBJ-01 to OBJ-04: access control, build truth, traceability, and data safety — each anchored to written criteria CRT-01 to CRT-04. For example, CRT-01 requires role rules in code plus approver ORG-02; CRT-03 requires audited, POST-only desk actions. Our procedures were deliberately safe: record and code inspection, configuration review, walkthroughs, and small demo tests — nothing changed or harmed. No attack testing, no live restore, no real student data — and those limits are stated in every conclusion.",
 ],
 qa=[
 "Where do the criteria come from? CRT-01..04 combine school access rules, Data Privacy Act obligations, and the agreed capstone requirements — approved in writing with the library owner.",
 "Why four objectives and not more? They cover the four angles of 'can we trust this system elsewhere': getting in, doing the work, leaving traces, and protecting data — every lab tallies to one of them.",
 "What exactly is excluded (SCP-03/04)? Attack testing, live restores on the real database, and any use of real student data — all evidence is demo-build and sanitized.",
 "Could the scope change if the panel requests it? Only with the owner's approval (ORG-01) in writing before work starts; otherwise results and limitations stay as filed.",
 "Which objective carries the most risk today? OBJ-04 data safety — unproven recovery (RSK-04) and wide borrower views (RSK-07) are two of our three High findings.",
 ]),

 dict(n=5, title="How We Worked — Evidence First", presenter="Justin C. Batlangao",
 script=[
 "One four-step method across Labs 7 to 12. First, inspect records, code, and configuration — the EVD-09 and EVD-10 series. Second, walk through real demo screens with names cleaned. Third, test — full populations where small. Fourth, cross-review: a written challenge and resolution for every increment, REV-01 to 14. On AI: wording fixes, counts, and clarification only — every suggestion validated, never an evidence source; all six uses are disclosed in the portfolio.",
 ],
 qa=[
 "Did AI write your audit? No — it shortened sentences, re-checked counts, and clarified tasks (AIV-01..06 with Accept/Revise and what was verified); every fact came from real evidence we handled ourselves.",
 "How do cross-reviewers avoid both missing the same thing? Reviewers were assigned different roles than the builder's, and every challenge written into REV-01..14 had to be resolved or the item moved into the gap register.",
 "Why no statistical sampling? Populations were small enough to test fully — all 10 role-gated pages, the entire 14-row backup log, the whole CSV file; sampling buys nothing at this size and hides more than it shows.",
 "What if a reviewer found an error? Fix on the spot if trivial and re-documented, or raise a logged challenge; anything found after the cutoff goes into the limitation log, not silently into results.",
 "What did the walkthrough add beyond the code read? Proof that role checks actually fire per page in the running app, plus visible skip-and-log behavior on the CSV import — behavior never shows in source alone.",
 ]),

 dict(n=6, title="Architecture and Trust Boundaries", presenter="Glenn Patrick B. Darriguez",
 script=[
 "Figure 2: a borrower connects over HTTPS to Flask, which talks SQL only to PostgreSQL. Google only proves identity — it never touches library data. A scheduler runs the timed backup, and admins use the highest-trust path. Six trust boundaries, DEP-01 to DEP-06, each with a named evidence source. Seven account types — and the one-time bootstrap admin was closed and verified, ACC-07. Secrets live only in environment config: never in the code, never in this report.",
 ],
 qa=[
 "What protects the database credentials? They live only in environment configuration held on the platform, referenced through the admin-only path (DEP-02); nothing sensitive is in code, in git, or in this report.",
 "Can Google ever hold our data hostage? No — Google only proves identity (the login line); if OAuth is suspended, data stays inside PostgreSQL and could still be read by the desk paths (dependency logged as INT-01..05).",
 "What stopped the bootstrap admin from being abused? It closed after first setup and was verified closed (ACC-07); follow-up is the quarterly access review under CMP-03 by ORG-02.",
 "Are the pg_dump backups on the same server as the database? They are produced by the provider-side scheduler; reach and retention were outside our scope, but backup status is on the system log (EVD-12-04).",
 "What is not on this map? Offline side-channels (phone calls, USB, paper notices); they carry no tested interfaces in this audit and are named as an assumption, not a boundary.",
 ]),

 dict(n=7, title="How Data Moves Through the Library", presenter="Glenn Patrick B. Darriguez",
 script=[
 "Figure 3 shows five data flows, FLOW-01 to 05. Borrowing honors the three-and-five-book limits; fines are rate times days late; deletion is archive-before-delete. The CSV import requires headers and skips bad rows — logged. Login is school email only, with the bootstrap admin closed after setup. Every flow has written validation, storage, channel, and retention rules. Remember one thing: borrower data sits in PostgreSQL, and its views should be role-limited — the weak part is Finding FND-03.",
 ],
 qa=[
 "What happens to a bad CSV row? It is skipped and logged — never half-inserted; the run log shows added versus skipped counts (demonstrated in TEST-02).",
 "Where are retention rules enforced? The written rules live in the report; enforcement is currently manual — that gap is exactly why the export path in FND-03 ranks High.",
 "How are fines computed? Rate times days late, with the rate held in settings guardrails (who may change it is what TEST-06 tested).",
 "Who may delete a book and what happens? Desk staff with role-gated pages; active records are refused, archived ones may be removed — tested in TEST-04, both sides.",
 "What does a student actually see? Loan limits of three (students) and five (faculty), and a purchase request that waits for approval before it enters the catalog — the flow-internal checks are visible in the demo.",
 ]),

 dict(n=8, title="What Could Go Wrong — Risk Profile (Lab 9)", presenter="Justin C. Batlangao",
 script=[
 "Lab 9 scored eight risks — likelihood times impact, adjusted only for safeguards proven in the build. Three are High. RSK-01: account takeover — a leaked password meets no second check; residual sixteen of twenty-five. RSK-04: recovery unproven — backups logged, restore never demonstrated; residual eight. RSK-07: borrower data exposed through wide views and an open export path. Those three become our findings. One example of adjustment: RSK-04's backup log is real, so its impact drops five to four. Single-provider outage, RSK-05, is accepted with a paper control. Compliance base: the Data Privacy Act plus school rules.",
 ],
 qa=[
 "Why is RSK-01 a 16? Likelihood 4 times impact 4: passwords leak often, and there is no second check to catch one compromised password — the mitigation is the second factor, aiming for 8.",
 "Why accept rather than mitigate the provider outage (RSK-05)? A standby site costs more than a small school library can carry; the owner signed the acceptance with manual desk steps for outage days.",
 "What is the single biggest inherent risk? RSK-04 at inherent 10 — recovery, because the trigger is rare (L=2) but the impact is total (I=5): every loan and every catalog record.",
 "Why is the CSV risk only Moderate (RSK-02)? Bad rows are annoying but contained and self-logged, and no private data is exposed — fixable catalog errors, not privacy or access failures.",
 "Is any risk score guaranteed to drop after remediation? No — the roadmap states target residuals and a re-test step; a score only moves when the validated safeguard, not an intention, is proven.",
 ]),

 dict(n=9, title="Controls We Evaluated and What the Tests Showed (Lab 10)", presenter="Glenn Patrick B. Darriguez",
 script=[
 "Eight controls, CTL-01 to 08; six tests on BLD-04. Four came back Effective. TEST-01: wrong-role entry blocked on all ten pages — ten for ten, zero exceptions. TEST-02: CSV upload — six good rows added, two bad rows skipped and logged. TEST-03: a full borrow-return-fine cycle — the fine matched the formula. TEST-04: deleting an active book refused; archived allowed. Two came back Partially Effective. TEST-05: fourteen of fourteen backups logged — but zero proof any restores. TEST-06: settings changes logged with a name — no approval step. These were full populations, not cherry-picked samples. The two partials spill into our findings.",
 ],
 qa=[
 "Does Partially Effective mean failed? No — the control partly works; it misses a secondary objective: TEST-05 lacks restore proof, TEST-06 lacks a pre-approval step before the change takes effect.",
 "Why not test a restore in Lab 10? Its scope ended at observation — and the missing authorization for a restore is itself the finding; REC-02 schedules the restore as a confirmed owner action.",
 "What actually makes tests trustworthy? They run against frozen builds; evidence is captured screenshots and system-generated logs, not our word (EVD-12-01..05), and two team members observed each run.",
 "How do you know the ten pages are ALL the role-gated pages? The audit trail maps MOD-01..08 route pages; the population list is in the TEST-01 workpaper, section 7.4 (small system, full coverage).",
 "Was the fine math re-derived or just observed? Both: TEST-03 borrowed, returned, and matched the fine against the rate-times-days formula on the returned value — independent recalculation, not just a screenshot.",
 ]),

 dict(n=10, title="Key Findings — Three High Items", presenter="Ma. Jenifer L. Labag",
 script=[
 "Five finding candidates, screened against evidence, materiality, and scope. FC-01 and FC-02 became findings FND-01 and FND-02. FC-03 became OBS-01 — a small, tracked backlog, not worth a finding. FC-04 became FND-03. FC-05 is closed — its risk is already compensated by logging plus a monthly review. Result: three formal findings, all High. We did not inflate the register — materiality disciplined the list, and every screening decision carries its evidence IDs.",
 ],
 qa=[
 "Why is a real gap like CSV job history not a finding (FC-03)? Materiality: it is an inventory-hygiene inconvenience, not a privacy, access, or recovery failure; it is tracked as OBS-01, not buried.",
 "Could any closed candidate (FC-05) resurface later? Yes, if the monthly review stops; the trigger is on the register, and re-opening the finding register is a quick lab-scale job.",
 "How do you prove the screening was honest? All five candidates, with decision reasons and evidence IDs, are in the finding register (section 8.1) — nothing was dropped in silence.",
 "Which candidate had the weakest evidence? FC-05's compensation claim — it leans on the logging note plus the review habit, so we close it rather than raise it to finding.",
 "What exactly makes a finding High? A high residual risk score plus a workpaper gap that independently confirms the control failure; all three meet both tests.",
 ]),

 dict(n=11, title="Finding 1 — Staff Login Without Second Check", presenter="Ma. Jenifer L. Labag",
 script=[
 "Finding one, FND-01. Condition: no staff or admin login asks for a second check on BLD-05. TEST-01 blocked the wrong role ten for ten — but that stops the wrong people, not a thief with the right password. Criteria, CRT-01 and CMP-03: login must stop outsiders. Cause: the second step was never built. Effect: one leaked password could read and change all borrower, loan, and fine data — we say exposure, not breach; nothing was lost. Severity: residual sixteen of twenty-five. REC-01 — ORG-02 turns on a second check; target: a stolen password alone fails.",
 ],
 qa=[
 "Ten-for-ten role tests passed — so why is this still a finding? Role gating stops the wrong people; it does nothing against a stolen but correct password — the cross-review debate is logged in REV-13-02 and the finding kept.",
 "Would the stolen session be visible in the audit trail? No — it enters as a normal-looking staff session; that is precisely why the second check is the recommended countermeasure.",
 "Which compliance line backs this? CMP-03, the school account-and-access rule, alongside CRT-01; both currently grade Partial in the compliance register.",
 "Why not just say 'add 2FA tomorrow'? Practical steps: choosing the second factor (code, prompt, or hardware), then enrolling each staff account — hence 'next release', not overnight.",
 "Is exposure the same as breach? No — exposure means the door is open; breach would be proof someone walked through. Our workpapers state 'no loss seen' for all three findings.",
 ]),

 dict(n=12, title="Finding 2 — Restore Never Tested", presenter="Ma. Jenifer L. Labag",
 script=[
 "Finding two, FND-02 — recovery provability. Condition: fourteen of fourteen backups logged, zero restore demonstrations. CMP-05 with CRT-04 requires not just copies but provable recovery. Cause: a restore needs owner approval and was never scheduled. Effect: if the database died, desk work could stop for days. Why High: a backup log proves copies exist — nothing about them coming back; one failed recovery means total loss. Our cross-review kept it High on effect, not score alone. REC-02 — one witnessed restore on a test copy plus filed steps: one admin hour, the cheapest fix, the biggest assurance gain.",
 ],
 qa=[
 "Why not restore the real database? Out of approved scope (SCP-03) and not ours to authorize; a test copy gives identical proof without touching live data.",
 "What could actually stop a restore from working? Version mismatch, a partial dump, or wrong sequencing — all unknown to us precisely because it has never been run; that unknown IS the finding.",
 "Could Recovery stay 'Not Determined' forever? Only if the owner never exercises it — the roadmap sets 'before our final defense' as the target date for REC-02.",
 "Who signs off that the restore worked? The System Admin (ORG-03) runs it, the owner (ORG-01) witnesses, and the signed steps and log become evidence in the report pack.",
 "Why is this the cheapest fix in the report? Because it converts fourteen logged backups into one demonstrable recovery with roughly a single admin hour — highest assurance per cost, which is why it leads the roadmap.",
 ]),

 dict(n=13, title="Finding 3 — Borrower Data Exposure", presenter="Ma. Jenifer L. Labag",
 script=[
 "Finding three, FND-03 — borrower data exposure. Staff roles open full borrower rows — name, school ID, fines; reports show names; and the export path has no extra rule. Criteria: the Data Privacy Act line plus CRT-01 — private data only for need-to-know roles. Cause: views built for desk speed; export never fenced. Effect: a curious or rogue staff member could copy many student records — exposure, no misuse seen. And this stands despite TEST-01 passing, because getting in and seeing wide are different questions. REC-03 — narrow views to need-to-know, hide names, log exports.",
 ],
 qa=[
 "How is FND-03 different from FND-01? FND-01 is about who gets in; FND-03 is about what an insider sees once inside — passing one says nothing about the other, which is why both stand despite TEST-01.",
 "Does the Data Privacy Act require hiding names from desk staff? No — desk staff need names for borrowing and notices (CMP-02); the requirement is role-based need-to-know plus report/export naming discipline (CMP-01).",
 "Has any student data actually left the system? No — we saw no misuse; the finding is structural exposure, and the workpaper states that explicitly.",
 "Would the fix break desk workflows? No — desk screens keep the fields staff need; the narrowing applies to broad views, reports, and the bulk CSV path.",
 "What does 'log exports' actually add? A record of who exported what and when — writing it into the audit trail turns deliberate misuse into reviewable, attributable events.",
 ]),

 dict(n=14, title="How Conclusions Stand on Evidence — The Chain", presenter="Glenn Patrick B. Darriguez",
 script=[
 "Is our conclusion supported? FND-01, traced end to end. TEST-01: ten for ten blocked, no second step visible. Locked into dated, sanitized evidence — EVD-12-01 and 13-01. The gap is GAP-01 against CTL-01 and 02. Then FND-01 written in full, and REC-01 with a named owner, tracked as MAP-01. FND-02 and FND-03 carry the same chain. Twenty evidence items are indexed, each with source, date, privacy treatment, and limitation. And nothing sensitive ever left the controlled folder — no names, counts only, secrets excluded.",
 ],
 qa=[
 "Where do the twenty evidence items physically live? In the controlled group drive, sanitized or redacted; the index with sources, dates, and limitations is section 13 of the report.",
 "What is MAP-01 beyond REC-01? The management action plan version: owner, target date, expected result, and validation steps — REC says what should happen, MAP says who, when, and how it is verified.",
 "Could one finding span several gaps? Yes — FND-01 came from GAP-01; FND-03 covers GAP-04 plus the unfenced export path observed in the same control area.",
 "How do you prevent 'evidence drift' across lab dates? Every evidence item is dated to its build (EVD-09..13 keyed to BLD history); nothing is analyzed outside its own frozen build.",
 "What makes a chain re-openable for the panel? Fixed IDs plus sanitized samples: give us any ID and we can show you exactly the condition we saw, from the same artifact we used.",
 ]),

 dict(n=15, title="What We Recommend — and Honestly, What It Is Not Yet", presenter="Ma. Jenifer L. Labag",
 script=[
 "Three recommendations — each with an owner, a target, and a verifiable result. REC-01, High, next release: a second login check, owned by the Access Approver; result — a stolen password alone fails. REC-02, High, before our final defense: one witnessed restore plus filed steps, owned by the System Admin; result — recovery demonstrable. REC-03, High, next release: narrow views, hide names, log exports, owned by the Privacy role. The honest part: all three are our proposals, not confirmed. If the library declines any, the residual risk stays — and the report records that acceptance.",
 ],
 qa=[
 "What if the library says no? The residual risk stays as scored, the owner's acceptance is recorded explicitly in the report, and follow-up remains the auditor's job even when the decision is not.",
 "When do we expect confirmation? The roadmap asks for an owner decision before our final defense; REC-02's action date and REC-01/REC-03's 'next release' give the owner three concrete decision points.",
 "Which fix gives the most value per hour? REC-02 — one admin hour converts fourteen logged backups into one demonstrable recovery; CMP-05 moves from Not Determined to evidenced.",
 "Are there guarantees the plan is accepted? None — our deliverable is the proposal plus validation steps, not the management decision; that honesty is part of the audit standard we followed.",
 "Who verifies the fixes actually worked? A follow-up review: re-run TEST-01 and TEST-03, read the restore log, review the export log once it exists — all stated as validation per recommendation.",
 ]),

 dict(n=16, title="What This Audit DOES NOT Say (professional honesty)", presenter="Justin C. Batlangao",
 script=[
 "What this audit does not say. All evidence is from the demo build and test site — never live production data. No attack testing, no live restore, no real student records — the approved scope limits. CMP-05 and CMP-07 stay not determined. Samples are small because the system is small, and populations are honestly listed. And BLD-06, the October 11-to-20 build, arrived after the cutoff: untested — disclosed, not absorbed into results. One flag: re-run TEST-03 after deploy, because timestamps could shift fine displays.",
 ],
 qa=[
 "Does the new timestamp commit break your conclusion? No — conclusions cover BLD-04/05 up to the Oct 10 cutoff; BLD-06 gets its own flagged follow-up: re-run TEST-03 after deploy.",
 "Why 'needs improvement' rather than 'needs immediate action'? Four of six tested controls are fully effective, no live student data runs yet, and remediation is planned before launch — measured language, per the evidence.",
 "Could the panel get a re-scored conclusion today? Not responsibly: refresh needs register re-indexing, owner sign-off, and re-testing — each longer than this session; the honest answer is the follow-up plan.",
 "Why are CMP-05 and CMP-07 not determined? Both need authority we did not have: a restore execution approval, and a position on Google's provider terms — saying so is cleaner than guessing.",
 "What if BLD-06's fixes are launched without verification? That is the flagged risk — which is exactly why the roadmap places the BLD-06 re-test and TEST-03 re-run before any live borrower data.",
 ]),

 dict(n=17, title="Overall Conclusion — Needs Improvement", presenter="Justin C. Batlangao",
 script=[
 "Our verdict: Needs Improvement, pending remediation — a fair call. What works, tested: wrong-role access blocked ten for ten, CSV checks with logs, a full audit trail, and fourteen of fourteen backups on schedule. What must improve — the three High findings, all still Proposed: the second login check, one witnessed restore, and narrowed views with export control. Then a follow-up review and a BLD-06 re-test before any live borrower data. A system holding student data should not go live with an unproven restore and a single-factor gate.",
 ],
 qa=[
 "Why 'improvement' rather than 'satisfactory'? Three High findings and no confirmed management response — the cross-review debate is in the log (REV rows), and improvement-first narrowly carried the day.",
 "Which single fix most lifts the verdict? A witnessed successful restore — it moves CMP-05 from Not Determined to evidenced with one administered action.",
 "How fast can the verdict change? After the owner confirms the plan and the three validation re-tests pass — the roadmap targets before the final defense; a follow-up review is the formal step.",
 "Is there any Critical-level risk we overlooked? No — Critical would need major data loss plus no recovery or detection path; our tests rule that in today's build.",
 "What date should the panel watch? The follow-up review — after REC-01..03 responses and the BLD-06 re-test, we re-issue the conclusion on the same ID structure.",
 ]),

 dict(n=18, title="Thank You — Questions?", presenter="All",
 script=[
 "Thank you. Any question can go to any of us — all three reviewed the whole engagement. Justin: scope, risks, conclusion. Glenn: system, controls, tests. Jenifer: findings and actions. Evidence on request: the twenty-item EVD index, test workpapers, and logs. Prepared answers: the fine formula is rate times days late under TEST-06; the privacy basis is CMP-01; BLD-06 is post-cutoff and excluded; and the plan is verified by re-running TEST-01 and TEST-03 plus reading the new logs.",
 ],
 qa=[
 "Where can the panel read more? The integrated final report (18 sections) and this deck, both in the laboratories folder; section 13's evidence index is the fastest entry point.",
 "Can we pull a specific EVD item right now? Yes — name the ID; we fetch the sanitized sample from the controlled folder with its source, date, and limitation note attached.",
 "What are your next steps as a team? Track REC-01..03 with each named owner (their target dates are before the final defense), and run the follow-up review with the validation re-tests.",
 "Any regret about how the audit went? We would have liked more time to witness a restore — that gap is exactly what REC-02 now schedules with the owner.",
 "If the library contacts us tomorrow, who should they call first? ORG-02 for REC-01 — staff enrollment is the longest lead-time item, and starting it keeps the plan on schedule.",
 ]),
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
             "Spoken script: ~12 minutes at ~140 wpm. Each slide also carries a 5-question Q&A bank (notes/doc only — not spoken).").font.size = Pt(10)
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
    qh = d.add_paragraph()
    qh.add_run("Q&A bank (5 prepared answers):").bold = True
    qh.runs[0].font.size = Pt(10)
    qh.runs[0].font.color.rgb = RGBColor(0x1F, 0x3B, 0x63)
    for i, qa in enumerate(s['qa'], 1):
        q = d.add_paragraph(qa, style='List Number')
        for run in q.runs:
            run.font.size = Pt(10)
d.add_page_break()
tail = d.add_paragraph()
tail.add_run(f"Total scripted words: {total_words} (approx. {total_words/140:.1f} minutes at ~140 wpm, excluding Q&A). "
             "The same per-slide script and Q&A bank are stored in each slide's presenter notes inside MCST-LMS_Audit_Redesigned.pptx.").italic = True
d.save(DOCX_OUT)
print("DOCX saved:", DOCX_OUT)

shutil.copyfile(PPTX, BACKUP)
print("Backup saved:", BACKUP)

p = Presentation(PPTX)
slides = list(p.slides)
assert len(slides) == len(SCRIPTS), f"slide count {len(slides)} != script count {len(SCRIPTS)}"
for slide, s in zip(slides, SCRIPTS):
    tf = slide.notes_slide.notes_text_frame
    tf.clear()
    tf.text = f"[{s['presenter']}]"
    para = tf.add_paragraph(); para.text = "SCRIPT:"
    for seg in s['script']:
        para = tf.add_paragraph(); para.text = seg
    para = tf.add_paragraph(); para.text = "Q&A BANK:"
    for i, qa in enumerate(s['qa'], 1):
        para = tf.add_paragraph(); para.text = f"{i}. {qa}"
p.save(PPTX)
print("PPTX notes patched for", len(SCRIPTS), "slides")
print(f"TOTAL SCRIPT WORDS: {total_words}, ~{total_words/140:.1f} min")
