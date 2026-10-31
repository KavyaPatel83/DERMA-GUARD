"""
Generate overleaf_code.txt containing the complete LaTeX code, BibTeX references,
and step-by-step Overleaf compilation guide.
"""
import os

BASE_DIR = r"d:\VIT BOOKS\PROJECT 1\DERMA-GUARD"
MAIN_TEX_PATH = os.path.join(BASE_DIR, "overleaf_paper", "main.tex")
REFS_BIB_PATH = os.path.join(BASE_DIR, "overleaf_paper", "references.bib")
OUT_TXT_PATH = os.path.join(BASE_DIR, "overleaf_paper", "overleaf_code.txt")
OUT_ROOT_TXT = os.path.join(BASE_DIR, "overleaf_code.txt")

with open(MAIN_TEX_PATH, "r", encoding="utf-8") as f:
    main_tex = f.read()

with open(REFS_BIB_PATH, "r", encoding="utf-8") as f:
    refs_bib = f.read()

separator = "=" * 80

content = f"""{separator}
OVERLEAF RESEARCH PAPER SOURCE CODE & BIBLIOGRAPHY
BCSE335L Healthcare Data Analytics — Final Review
Project: DERMA-GUARD: Evidence-Aware Specialist Consensus with Risk-Controlled Evidence Acquisition and Deferral for Multimodal Dermatology
Dataset: PAD-UFES-20 (Smartphone Skin Lesion Cohort)
Authors: Rachit Agarwal, Patel Kavya Vipulkumar, Aarav Prawin, Dr. Sindhu Ravindran
Evaluator: Dr. Maheswari S (@Dr Maheswari S)
Department: School of Computer Science and Engineering, VIT Chennai
{separator}

INSTRUCTIONS FOR OVERLEAF COMPILATION:
1. Log into your Overleaf account (https://www.overleaf.com).
2. Click "New Project" -> "Blank Project". Name it: "BCSE335L_DERMA_GUARD".
3. Overleaf will create a default 'main.tex'. Select all and delete it.
4. Copy the entire contents under [FILE 1: main.tex] below and paste it into Overleaf's 'main.tex'.
5. In the left sidebar of Overleaf, click "New File", name it 'references.bib'.
6. Copy the entire contents under [FILE 2: references.bib] below and paste it into 'references.bib'.
7. Click the Upload button in Overleaf (or drag-and-drop) to upload the figure images located in
   your local folder: "d:\\VIT BOOKS\\PROJECT 1\\DERMA-GUARD\\overleaf_paper\\"
   (Key figures required: arch.png, r_bars.png, r_card.png, r_conf.png, r_curves.png, site_home.png, site_evidence.png, site_doctor_dash.png, site_rag.png)
8. Click "Recompile". The PDF will compile directly into standard IEEE 2-column format (6 to 8 pages).
9. Download the PDF and rename as per guidelines: BCSE335L_TeamNo_DERMA_GUARD.pdf.

{separator}
[FILE 1: main.tex] — IEEE TRANSACTIONS / CONFERENCE 2-COLUMN LATEX CODE
{separator}

{main_tex}

{separator}
[FILE 2: references.bib] — 26 IEEE BIBTEX CITATIONS
{separator}

{refs_bib}

{separator}
END OF OVERLEAF SOURCE CODE
{separator}
"""

with open(OUT_TXT_PATH, "w", encoding="utf-8") as f:
    f.write(content)

with open(OUT_ROOT_TXT, "w", encoding="utf-8") as f:
    f.write(content)

print(f"[SUCCESS] Exported Overleaf code to {OUT_TXT_PATH} and {OUT_ROOT_TXT}")
