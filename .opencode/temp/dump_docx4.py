import sys, io, docx
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

d = docx.Document(r"C:\Users\astro\OneDrive\Desktop\Capstone\Laboratories\PEIS002_Lab12_Group404NotFound_MCST-LMS_Final_IT_Audit_Report.docx")

seen = set()
for i, t in enumerate(d.tables):
    if i in seen: continue
    txt = "\n".join(" | ".join(c.text.strip() for c in r.cells) for r in t.rows)
    hit = None
    for row in t.rows:
        first = " | ".join(c.text.strip() for c in row.cells)
        if first.startswith("RSK-") or first.startswith("CMP-") or first.startswith("CRT-") or first.startswith("REC-0") or first.startswith("EVD-"):
            hit = first
            break
    if hit:
        seen.add(i)
        print(f"=== TABLE {i} ===")
        print(txt[:2400])
        print()
