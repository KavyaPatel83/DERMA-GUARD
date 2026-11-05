"""
Script to remove all course/review/evaluator footers and notes from the research paper.
"""
import os

BASE_DIR = r"d:\VIT BOOKS\PROJECT 1\DERMA-GUARD"

# 1. Update scripts/generate_ieee_pdf.py
gen_script_path = os.path.join(BASE_DIR, "scripts", "generate_ieee_pdf.py")
with open(gen_script_path, "r", encoding="utf-8") as f:
    gen_text = f.read()

# Remove course-note div
old_course_note = """  <div class="course-note">
    Research Paper developed for BCSE335L Healthcare Data Analytics under the instruction and evaluation of <strong>Dr. Maheswari S</strong>, School of Computer Science and Engineering, Vellore Institute of Technology (VIT), Chennai.
  </div>"""
if old_course_note in gen_text:
    gen_text = gen_text.replace(old_course_note, "")
    print("[OK] Removed course-note div from generate_ieee_pdf.py")

# Clean up declarations
gen_text = gen_text.replace(
    "conducted for BCSE335L Healthcare Data Analytics. The manuscript exhibits",
    "conducted by the authors. The manuscript exhibits"
)

# Clean up footer template
old_footer = """        <div style="font-family: 'Times New Roman', serif; font-size: 8.5pt; width: 100%; text-align: center; color: #555;">
          <span>BCSE335L Healthcare Data Analytics — Final Review · @Dr Maheswari S · VIT Chennai</span>
          &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
          <span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span>
        </div>"""

new_footer = """        <div style="font-family: 'Times New Roman', serif; font-size: 9pt; width: 100%; text-align: center; color: #444;">
          <span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span>
        </div>"""

if old_footer in gen_text:
    gen_text = gen_text.replace(old_footer, new_footer)
    print("[OK] Replaced footer template in generate_ieee_pdf.py")
else:
    # flexible replacement
    import re
    gen_text = re.sub(
        r'<span>BCSE335L Healthcare Data Analytics.*?VIT Chennai</span>\s*&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\s*',
        '',
        gen_text
    )
    print("[OK] Replaced footer using regex in generate_ieee_pdf.py")

with open(gen_script_path, "w", encoding="utf-8") as f:
    f.write(gen_text)

# 2. Update overleaf_paper/main.tex
tex_path = os.path.join(BASE_DIR, "overleaf_paper", "main.tex")
with open(tex_path, "r", encoding="utf-8") as f:
    tex_text = f.read()

old_thanks = r"""\thanks{This research paper was developed for the course BCSE335L Healthcare Data Analytics under the instruction and evaluation of Dr. Maheswari S, School of Computer Science and Engineering, Vellore Institute of Technology (VIT), Chennai.}"""
if old_thanks in tex_text:
    tex_text = tex_text.replace(old_thanks, "")
    print("[OK] Removed thanks note from main.tex")

tex_text = tex_text.replace(
    "conducted for BCSE335L Healthcare Data Analytics.",
    "conducted by the authors."
)

with open(tex_path, "w", encoding="utf-8") as f:
    f.write(tex_text)

print("[SUCCESS] All files patched. Ready to recompile.")
