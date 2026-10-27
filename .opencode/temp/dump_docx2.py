import docx

d = docx.Document(r"C:\Users\astro\OneDrive\Desktop\Capstone\Laboratories\PEIS002_Lab12_Group404NotFound_MCST-LMS_Final_IT_Audit_Report.docx")

# Print paragraph texts in sections 2 and 4.1-4.3
grab = False
targets = ("2. Executive Summary", "3. Engagement Profile", "4. Audit Objectives")
for para in d.paragraphs:
    t = para.text.strip()
    if not t:
        continue
    if para.style.name.startswith('Heading'):
        grab = any(t.startswith(x) for x in targets)
    if grab and not para.style.name.startswith('Heading'):
        print("P:", t)

print("\n=== FINDING WORKPAPERS T34-36 ===")
for i in (34, 35, 36):
    for r in d.tables[i].rows:
        print(" | ".join(c.text.strip() for c in r.cells)[:400])
    print("----")
