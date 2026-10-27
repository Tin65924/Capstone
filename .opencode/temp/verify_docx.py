import sys, io, docx
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
d = docx.Document(r"C:\Users\astro\OneDrive\Desktop\Capstone\Laboratories\SCRIPT.docx")
heads = [p.text for p in d.paragraphs if p.style.name == "Heading 1"]
print(len(heads), "headings")
print("\n".join(heads))
for p in d.paragraphs:
    if "Total scripted" in p.text:
        print(p.text)
