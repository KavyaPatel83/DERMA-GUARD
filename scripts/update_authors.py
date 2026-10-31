"""
Remove Rachit Agarwal and Dr. Sindhu Ravindran from:
 1. overleaf_paper/main.tex
 2. scripts/generate_ieee_pdf.py
 3. scripts/generate_bcse335l_final_review_ppt.py
 4. overleaf_paper/Similarity_Report.md
 5. overleaf_paper/TRIPOD_AI_Checklist.md
 6. README.md / overleaf_paper/GITHUB_README.md
Keep ONLY: Patel Kavya Vipulkumar and Aarav Prawin
"""
import os

BASE = r"d:\VIT BOOKS\PROJECT 1\DERMA-GUARD"

AUTHORS_ONLY_TWO = "Patel Kavya Vipulkumar and Aarav Prawin"
AUTHORS_PIPE     = "Patel Kavya Vipulkumar   |   Aarav Prawin"

# ── 1. main.tex ──────────────────────────────────────────────────────────────
tex_path = os.path.join(BASE, "overleaf_paper", "main.tex")
with open(tex_path, 'r', encoding='utf-8') as f:
    tex = f.read()

old_authors = r"""\author{
\IEEEauthorblockN{Rachit Agarwal}
\IEEEauthorblockA{\textit{School of Computer Science and Engineering} \\
\textit{VIT Chennai}, India \\
rachit.agarwal2023@vitstudent.ac.in}
\and
\IEEEauthorblockN{Patel Kavya Vipulkumar}
\IEEEauthorblockA{\textit{School of Computer Science and Engineering} \\
\textit{VIT Chennai}, India \\
patel.kavya2023@vitstudent.ac.in}
\and
\IEEEauthorblockN{Aarav Prawin}
\IEEEauthorblockA{\textit{School of Computer Science and Engineering} \\
\textit{VIT Chennai}, India \\
aarav.prawin2023@vitstudent.ac.in}
\and
\IEEEauthorblockN{Dr. Sindhu Ravindran}
\IEEEauthorblockA{\textit{School of Computer Science and Engineering} \\
\textit{VIT Chennai}, India \\
sindhu.ravindran@vit.ac.in}
}"""

new_authors = r"""\author{
\IEEEauthorblockN{Patel Kavya Vipulkumar}
\IEEEauthorblockA{\textit{School of Computer Science and Engineering} \\
\textit{VIT Chennai}, India \\
patel.kavya2023@vitstudent.ac.in}
\and
\IEEEauthorblockN{Aarav Prawin}
\IEEEauthorblockA{\textit{School of Computer Science and Engineering} \\
\textit{VIT Chennai}, India \\
aarav.prawin2023@vitstudent.ac.in}
}"""

if old_authors in tex:
    tex = tex.replace(old_authors, new_authors)
    print("[OK] main.tex authors updated (exact match)")
else:
    # fallback: patch any remaining rachit/sindhu lines
    lines = tex.splitlines()
    skip = False
    out = []
    i = 0
    while i < len(lines):
        l = lines[i]
        if 'Rachit Agarwal' in l or 'rachit.agarwal' in l.lower():
            # skip this block until next \and or }
            while i < len(lines) and '\\and' not in lines[i] and (i == 0 or 'IEEEauthorblockA' not in lines[i-1] or '}' not in lines[i]):
                i += 1
            if i < len(lines) and '\\and' in lines[i]:
                i += 1  # skip the \and separator
        elif 'Sindhu Ravindran' in l or 'sindhu.ravindran' in l.lower():
            while i < len(lines) and (lines[i].strip() not in ('}', '\\and')):
                i += 1
        else:
            out.append(l)
            i += 1
    tex = '\n'.join(out)
    print("[WARN] main.tex authors updated via fallback line filter")

with open(tex_path, 'w', encoding='utf-8') as f:
    f.write(tex)
print("Saved main.tex")

# ── 2. generate_ieee_pdf.py ───────────────────────────────────────────────────
pdf_path = os.path.join(BASE, "scripts", "generate_ieee_pdf.py")
with open(pdf_path, 'r', encoding='utf-8') as f:
    pdf = f.read()

# Replace the 4-column author grid with a 2-column grid
old_auth_grid = """  <div class="authors-grid">
    <div class="author-col">
      <div class="author-name">Rachit Agarwal</div>
      <div class="author-dept">School of Computer Science and Engineering</div>
      <div class="author-inst">VIT Chennai, India</div>
      <div class="author-email">rachit.agarwal2023@vitstudent.ac.in</div>
    </div>
    <div class="author-col">
      <div class="author-name">Patel Kavya Vipulkumar</div>
      <div class="author-dept">School of Computer Science and Engineering</div>
      <div class="author-inst">VIT Chennai, India</div>
      <div class="author-email">patel.kavya2023@vitstudent.ac.in</div>
    </div>
    <div class="author-col">
      <div class="author-name">Aarav Prawin</div>
      <div class="author-dept">School of Computer Science and Engineering</div>
      <div class="author-inst">VIT Chennai, India</div>
      <div class="author-email">aarav.prawin2023@vitstudent.ac.in</div>
    </div>
    <div class="author-col">
      <div class="author-name">Dr. Sindhu Ravindran</div>
      <div class="author-dept">School of Computer Science and Engineering</div>
      <div class="author-inst">VIT Chennai, India</div>
      <div class="author-email">sindhu.ravindran@vit.ac.in</div>
    </div>
  </div>"""

new_auth_grid = """  <div class="authors-grid">
    <div class="author-col">
      <div class="author-name">Patel Kavya Vipulkumar</div>
      <div class="author-dept">School of Computer Science and Engineering</div>
      <div class="author-inst">VIT Chennai, India</div>
      <div class="author-email">patel.kavya2023@vitstudent.ac.in</div>
    </div>
    <div class="author-col">
      <div class="author-name">Aarav Prawin</div>
      <div class="author-dept">School of Computer Science and Engineering</div>
      <div class="author-inst">VIT Chennai, India</div>
      <div class="author-email">aarav.prawin2023@vitstudent.ac.in</div>
    </div>
  </div>"""

if old_auth_grid in pdf:
    pdf = pdf.replace(old_auth_grid, new_auth_grid)
    print("[OK] generate_ieee_pdf.py author grid updated")
else:
    print("[WARN] generate_ieee_pdf.py author grid not found by exact match, doing string replace")
    pdf = pdf.replace('Rachit Agarwal', 'Patel Kavya Vipulkumar')
    pdf = pdf.replace('rachit.agarwal2023@vitstudent.ac.in', 'patel.kavya2023@vitstudent.ac.in')
    pdf = pdf.replace('Dr. Sindhu Ravindran', 'Aarav Prawin')
    pdf = pdf.replace('sindhu.ravindran@vit.ac.in', 'aarav.prawin2023@vitstudent.ac.in')

with open(pdf_path, 'w', encoding='utf-8') as f:
    f.write(pdf)
print("Saved generate_ieee_pdf.py")

# ── 3. generate_bcse335l_final_review_ppt.py ─────────────────────────────────
ppt_path = os.path.join(BASE, "scripts", "generate_bcse335l_final_review_ppt.py")
with open(ppt_path, 'r', encoding='utf-8') as f:
    ppt = f.read()

replacements = [
    ('• Rachit Agarwal — B.Tech Data Science (rachit.agarwal2023@vitstudent.ac.in)', ''),
    ('add(tfp, "", FONT_B, 11, bold=True, color=WHITE, sb=3)\n', ''),
    ('• Dr. Sindhu Ravindran — Faculty Mentorship (sindhu.ravindran@vit.ac.in)', ''),
    ('add(tff, "", FONT_B, 11, bold=True, color=TEAL_SOFT, sb=2)\n', ''),
    ('Rachit Agarwal   |   Patel Kavya Vipulkumar   |   Aarav Prawin   |   Dr. Sindhu Ravindran', AUTHORS_PIPE),
    ('Rachit Agarwal, Patel Kavya Vipulkumar, Aarav Prawin, Dr. Sindhu Ravindran', AUTHORS_ONLY_TWO),
    ('Rachit Agarwal | Patel Kavya Vipulkumar | Aarav Prawin | Dr. Sindhu Ravindran', AUTHORS_PIPE),
]
for old, new in replacements:
    if old in ppt:
        ppt = ppt.replace(old, new)

# Direct string substitutions for remaining references
ppt = ppt.replace(
    '• Rachit Agarwal \u2014 B.Tech Data Science (rachit.agarwal2023@vitstudent.ac.in)',
    ''
)
ppt = ppt.replace(
    '• Dr. Sindhu Ravindran \u2014 Faculty Mentorship (sindhu.ravindran@vit.ac.in)',
    ''
)
ppt = ppt.replace(
    'Rachit Agarwal   |   Patel Kavya Vipulkumar   |   Aarav Prawin   |   Dr. Sindhu Ravindran',
    AUTHORS_PIPE
)

with open(ppt_path, 'w', encoding='utf-8') as f:
    f.write(ppt)
print("Saved generate_bcse335l_final_review_ppt.py")

# ── 4. Similarity_Report.md ───────────────────────────────────────────────────
sim_path = os.path.join(BASE, "overleaf_paper", "Similarity_Report.md")
sim = open(sim_path, 'r', encoding='utf-8').read()
sim = sim.replace(
    """**Authors:**
- Rachit Agarwal (rachit.agarwal2023@vitstudent.ac.in)
- Patel Kavya Vipulkumar (patel.kavya2023@vitstudent.ac.in)
- Aarav Prawin (aarav.prawin2023@vitstudent.ac.in)
- Dr. Sindhu Ravindran (sindhu.ravindran@vit.ac.in)""",
    """**Authors:**
- Patel Kavya Vipulkumar (patel.kavya2023@vitstudent.ac.in)
- Aarav Prawin (aarav.prawin2023@vitstudent.ac.in)"""
)
sim = sim.replace(
    "by Rachit Agarwal, Patel Kavya Vipulkumar, Aarav Prawin, and Dr. Sindhu Ravindran.",
    "by Patel Kavya Vipulkumar and Aarav Prawin."
)
sim = sim.replace(
    """**Certified by Authors:**  
- **Rachit Agarwal** (`rachit.agarwal2023@vitstudent.ac.in`)  
- **Patel Kavya Vipulkumar** (`patel.kavya2023@vitstudent.ac.in`)  
- **Aarav Prawin** (`aarav.prawin2023@vitstudent.ac.in`)  
- **Dr. Sindhu Ravindran** (`sindhu.ravindran@vit.ac.in`, Faculty Mentor)""",
    """**Certified by Authors:**  
- **Patel Kavya Vipulkumar** (`patel.kavya2023@vitstudent.ac.in`)  
- **Aarav Prawin** (`aarav.prawin2023@vitstudent.ac.in`)"""
)
with open(sim_path, 'w', encoding='utf-8') as f:
    f.write(sim)
print("Saved Similarity_Report.md")

# ── 5. TRIPOD_AI_Checklist.md ─────────────────────────────────────────────────
tri_path = os.path.join(BASE, "overleaf_paper", "TRIPOD_AI_Checklist.md")
tri = open(tri_path, 'r', encoding='utf-8').read()
tri = tri.replace(
    "Rachit Agarwal (rachit.agarwal2023@vitstudent.ac.in), Patel Kavya Vipulkumar (patel.kavya2023@vitstudent.ac.in), Aarav Prawin (aarav.prawin2023@vitstudent.ac.in), Dr. Sindhu Ravindran (sindhu.ravindran@vit.ac.in)",
    "Patel Kavya Vipulkumar (patel.kavya2023@vitstudent.ac.in), Aarav Prawin (aarav.prawin2023@vitstudent.ac.in)"
)
tri = tri.replace(
    "Rachit Agarwal (`23BDS1076`), Patel Kavya Vipulkumar (`23BDS1076`), Aarav Prawin (`23BDS1116`), Dr. Sindhu Ravindran",
    "Patel Kavya Vipulkumar (`23BDS1076`), Aarav Prawin (`23BDS1116`)"
)
with open(tri_path, 'w', encoding='utf-8') as f:
    f.write(tri)
print("Saved TRIPOD_AI_Checklist.md")

# ── 6. README.md ──────────────────────────────────────────────────────────────
for rp in [os.path.join(BASE, "README.md"), os.path.join(BASE, "overleaf_paper", "GITHUB_README.md")]:
    with open(rp, 'r', encoding='utf-8') as f:
        r = f.read()
    r = r.replace(
        "> **Authors:** Rachit Agarwal, Patel Kavya Vipulkumar, Aarav Prawin, Dr. Sindhu Ravindran\n> **Emails:** rachit.agarwal2023@vitstudent.ac.in, patel.kavya2023@vitstudent.ac.in, aarav.prawin2023@vitstudent.ac.in, sindhu.ravindran@vit.ac.in",
        "> **Authors:** Patel Kavya Vipulkumar, Aarav Prawin\n> **Emails:** patel.kavya2023@vitstudent.ac.in, aarav.prawin2023@vitstudent.ac.in"
    )
    r = r.replace(
        "author={Agarwal, Rachit and Patel, Kavya Vipulkumar and Prawin, Aarav and Ravindran, Sindhu}",
        "author={Patel, Kavya Vipulkumar and Prawin, Aarav}"
    )
    r = r.replace("@article{agarwal2026dermaguard,", "@article{patel2026dermaguard,")
    with open(rp, 'w', encoding='utf-8') as f:
        f.write(r)
    print(f"Saved {rp}")

print("\n[DONE] All author references updated.")

