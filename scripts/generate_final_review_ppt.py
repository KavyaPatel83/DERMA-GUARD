"""
DERMA-GUARD — FINAL REVIEW (Review 3) PPT
Styled after Project-1__Review2_Final.pptx
Changes from v1:
  - MILK10k / dataset-splitting slides REMOVED
  - NEW slides: RAG System, AI Multi-Agent Layer, Per-Class Results, Risk Policy
  - All results images embedded
"""
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

# ── PALETTE (from reference PPT) ───────────────────────────────────────────
BG_DARK      = RGBColor(0x0F,0x3D,0x3E)
BG_DARKER    = RGBColor(0x0B,0x2E,0x2F)
BG_WHITE     = RGBColor(0xFF,0xFF,0xFF)
TEAL_BRIGHT  = RGBColor(0x2E,0xC4,0xB6)
TEAL_DARK    = RGBColor(0x1B,0x6B,0x93)
TEAL_CARD    = RGBColor(0xDC,0xF4,0xF1)
TEAL_SOFT    = RGBColor(0xBF,0xE3,0xDE)
HEAD_DARK    = RGBColor(0x0F,0x3D,0x3E)
BODY_DARK    = RGBColor(0x15,0x26,0x2B)
MUTED        = RGBColor(0x5B,0x7C,0x82)
WHITE        = RGBColor(0xFF,0xFF,0xFF)
ACCENT_GRN   = RGBColor(0x1A,0x5C,0x48)
ACCENT_RED   = RGBColor(0x6B,0x21,0x21)
ACCENT_BRN   = RGBColor(0x78,0x35,0x00)

FONT_H = "Cambria"
FONT_B = "Calibri"
FONT_C = "Consolas"

W = Inches(13.333)
H = Inches(7.5)

IMG = r"d:\VIT BOOKS\PROJECT 1\Healthsphere_1"

def prs_new():
    p = Presentation()
    p.slide_width  = W
    p.slide_height = H
    return p

def blank(p): return p.slides.add_slide(p.slide_layouts[6])

def rect(s, l,t,w,h, fill, line=None):
    sh = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, l,t,w,h)
    sh.fill.solid(); sh.fill.fore_color.rgb = fill
    if line: sh.line.color.rgb = line; sh.line.width = Pt(0.75)
    else:    sh.line.fill.background()
    return sh

def rr(s, l,t,w,h, fill):
    sh = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, l,t,w,h)
    sh.fill.solid(); sh.fill.fore_color.rgb = fill
    sh.line.fill.background()
    return sh

def tb(s, l,t,w,h): return s.shapes.add_textbox(l,t,w,h)

def para(tf, text, fn, sz, bold=False, color=None, align=PP_ALIGN.LEFT, sb=0, italic=False, new=False):
    if new or (len(tf.paragraphs)==1 and tf.paragraphs[0].text==""):
        p = tf.paragraphs[0] if not new else tf.add_paragraph()
    else:
        p = tf.paragraphs[0]
    if new: p = tf.add_paragraph()
    p.alignment = align; p.space_before = Pt(sb)
    r = p.add_run()
    r.text = text; r.font.name = fn; r.font.size = Pt(sz)
    r.font.bold = bold; r.font.italic = italic
    if color: r.font.color.rgb = color
    return p

def add(tf, text, fn, sz, bold=False, color=None, align=PP_ALIGN.LEFT, sb=4, italic=False):
    p = tf.add_paragraph()
    p.alignment = align; p.space_before = Pt(sb)
    r = p.add_run()
    r.text = text; r.font.name = fn; r.font.size = Pt(sz)
    r.font.bold = bold; r.font.italic = italic
    if color: r.font.color.rgb = color
    return p

def setbg(s, c):
    bg = s.background; fill = bg.fill; fill.solid(); fill.fore_color.rgb = c

def card(s, l,t,w,h, bg=None, top_accent=None):
    bg = bg or TEAL_CARD
    rr(s,l,t,w,h,bg)
    if top_accent: rect(s,l,t,w,Inches(0.065),top_accent)

def dark_card(s, l,t,w,h):
    rr(s,l,t,w,h,BG_DARK)

def badge(s, l,t, num_or_ltr, fill=TEAL_DARK, sz=Inches(0.38)):
    circ = s.shapes.add_shape(MSO_SHAPE.OVAL, l,t,sz,sz)
    circ.fill.solid(); circ.fill.fore_color.rgb = fill; circ.line.fill.background()
    b = tb(s, l,t,sz,sz)
    tf = b.text_frame; tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
    para(tf, num_or_ltr, FONT_B, 11, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

def pill_row(s, l,t, w, h_sz, letter, label, desc, pill_fill=TEAL_DARK):
    badge(s, l, t, letter, pill_fill, h_sz)
    b1 = tb(s, l+h_sz+Inches(0.15), t, w-h_sz-Inches(0.15), Inches(0.3))
    tf1 = b1.text_frame; tf1.margin_left=tf1.margin_right=tf1.margin_top=tf1.margin_bottom=0
    para(tf1, label, FONT_B, 14, bold=True, color=HEAD_DARK)
    b2 = tb(s, l+h_sz+Inches(0.15), t+Inches(0.29), w-h_sz-Inches(0.15), Inches(0.4))
    tf2 = b2.text_frame; tf2.word_wrap=True; tf2.margin_left=tf2.margin_right=tf2.margin_top=tf2.margin_bottom=0
    para(tf2, desc, FONT_B, 11.5, color=MUTED)

def header(s, section, heading, sub=None):
    rect(s, Inches(0),Inches(0),W,Inches(0.07),TEAL_BRIGHT)
    b = tb(s, Inches(0.55),Inches(0.28),Inches(10),Inches(0.32))
    tf = b.text_frame; tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
    para(tf, section.upper(), FONT_B, 12.5, bold=True, color=TEAL_DARK)
    b2 = tb(s, Inches(0.55),Inches(0.58),Inches(12),Inches(0.65))
    tf2 = b2.text_frame; tf2.word_wrap=True; tf2.margin_left=tf2.margin_right=tf2.margin_top=tf2.margin_bottom=0
    para(tf2, heading, FONT_H, 27, bold=True, color=HEAD_DARK)
    if sub:
        b3 = tb(s, Inches(0.55),Inches(1.22),Inches(12),Inches(0.35))
        tf3 = b3.text_frame; tf3.word_wrap=True; tf3.margin_left=tf3.margin_right=tf3.margin_top=tf3.margin_bottom=0
        para(tf3, sub, FONT_B, 12, color=MUTED)
    rect(s, Inches(0.55),Inches(1.55),Inches(12.2),Inches(0.04),TEAL_BRIGHT)

def foot(s):
    b = tb(s, Inches(0.55),Inches(7.12),Inches(5),Inches(0.25))
    tf = b.text_frame; tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
    para(tf, "DERMA-GUARD", FONT_B, 9, bold=True, color=MUTED)

def img(s, path, l, t, **kw):
    if os.path.exists(path):
        return s.shapes.add_picture(path, l, t, **kw)

def content_row(s, tf, label, val, sz_l=11.5, sz_v=11):
    b = tf.add_paragraph(); b.space_before=Pt(4)
    r1 = b.add_run(); r1.text=label+" "; r1.font.name=FONT_B; r1.font.size=Pt(sz_l); r1.font.bold=True; r1.font.color.rgb=HEAD_DARK
    b2 = tf.add_paragraph(); b2.space_before=Pt(1)
    r2 = b2.add_run(); r2.text=val; r2.font.name=FONT_B; r2.font.size=Pt(sz_v); r2.font.color.rgb=BODY_DARK

# ═══════════════════════════════════════════════════════════════════════════
prs = prs_new()

# ──────────────────────────────────────────────────── S1: TITLE ────────────
s = blank(prs); setbg(s, BG_DARK)
rect(s, Inches(0),Inches(4.55),W,Inches(2.95),BG_DARKER)

rect(s, Inches(0.55),Inches(0.85),Inches(0.06),Inches(3.3),TEAL_BRIGHT)
b=tb(s,Inches(0.8),Inches(0.85),Inches(11.5),Inches(1.2)); tf=b.text_frame
tf.word_wrap=True; tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
para(tf,"DERMA-GUARD",FONT_H,54,bold=True,color=WHITE)

b2=tb(s,Inches(0.8),Inches(2.05),Inches(11.5),Inches(0.85)); tf2=b2.text_frame
tf2.word_wrap=True; tf2.margin_left=tf2.margin_right=tf2.margin_top=tf2.margin_bottom=0
para(tf2,"EVIDENCE-AWARE SPECIALIST CONSENSUS WITH RISK-CONTROLLED",FONT_B,17,color=TEAL_SOFT)
add(tf2,"EVIDENCE ACQUISITION AND DEFERRAL FOR MULTIMODAL DERMATOLOGY",FONT_B,17,color=TEAL_SOFT,sb=2)

b3=tb(s,Inches(0.8),Inches(3.05),Inches(11.5),Inches(0.28)); tf3=b3.text_frame
tf3.margin_left=tf3.margin_right=tf3.margin_top=tf3.margin_bottom=0
para(tf3,"PAD-UFES-20 Dataset | VIT Chennai | IEEE Conference Paper",FONT_B,11.5,color=MUTED,italic=True)

rect(s, Inches(0.8),Inches(3.55),Inches(5.8),Inches(0.42),TEAL_BRIGHT)
b_badge=tb(s,Inches(0.9),Inches(3.55),Inches(5.6),Inches(0.42)); tf_b=b_badge.text_frame
tf_b.margin_top=tf_b.margin_bottom=Pt(2)
para(tf_b,"REVIEW 3  \u2022  FINAL PROJECT SUBMISSION",FONT_B,10.5,bold=True,color=BG_DARKER)

# Presented By (Exact Project-1_Review2_Final styling: Teal label + White names)
b4=tb(s,Inches(0.8),Inches(4.80),Inches(11.5),Inches(0.75)); tf4=b4.text_frame
tf4.word_wrap=True; tf4.margin_left=tf4.margin_right=tf4.margin_top=tf4.margin_bottom=0
p1=tf4.paragraphs[0]
r1=p1.add_run(); r1.text="Presented By"; r1.font.name=FONT_B; r1.font.size=Pt(11); r1.font.bold=True; r1.font.color.rgb=TEAL_BRIGHT
p2=tf4.add_paragraph(); p2.space_before=Pt(3)
r2=p2.add_run(); r2.text="Aarav Prawin (23BDS1116)   |   Patel Kavya Vipulkumar (23BDS1076)   |   Rachit Agarwal (23BCE1577)"
r2.font.name=FONT_B; r2.font.size=Pt(13.5); r2.font.bold=False; r2.font.color.rgb=WHITE

# Project Guide (Exact same style & same color)
b5=tb(s,Inches(0.8),Inches(5.72),Inches(11.5),Inches(0.75)); tf5=b5.text_frame
tf5.word_wrap=True; tf5.margin_left=tf5.margin_right=tf5.margin_top=tf5.margin_bottom=0
p3=tf5.paragraphs[0]
r3=p3.add_run(); r3.text="Project Guide"; r3.font.name=FONT_B; r3.font.size=Pt(11); r3.font.bold=True; r3.font.color.rgb=TEAL_BRIGHT
p4=tf5.add_paragraph(); p4.space_before=Pt(3)
r4=p4.add_run(); r4.text="Dr. Sindhu Ravindran"; r4.font.name=FONT_B; r4.font.size=Pt(13.5); r4.font.bold=True; r4.font.color.rgb=WHITE
r5=p4.add_run(); r5.text="   |   School of Computer Science and Engineering (SCOPE), VIT Chennai"
r5.font.name=FONT_B; r5.font.size=Pt(13.5); r5.font.bold=False; r5.font.color.rgb=WHITE

b6=tb(s,Inches(0.8),Inches(6.85),Inches(4),Inches(0.25)); tf6=b6.text_frame
tf6.margin_left=tf6.margin_right=tf6.margin_top=tf6.margin_bottom=0
para(tf6,"DERMA-GUARD",FONT_B,9,bold=True,color=TEAL_BRIGHT)

# ──────────────────────────────────────────────────── S2: PROBLEM ──────────
s = blank(prs); setbg(s,BG_WHITE)
header(s,"Background & Motivation","The Problem We're Solving","Why standard skin-lesion AI fails the clinical safety bar")

b=tb(s,Inches(0.55),Inches(1.68),Inches(5.65),Inches(0.28)); tf=b.text_frame
tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
para(tf,"CLINICAL CONTEXT",FONT_B,11,bold=True,color=TEAL_DARK)
b2=tb(s,Inches(0.55),Inches(1.98),Inches(5.65),Inches(2.4)); tf2=b2.text_frame
tf2.word_wrap=True; tf2.margin_left=tf2.margin_right=tf2.margin_top=tf2.margin_bottom=0
para(tf2,"Skin cancer is among the most common cancers worldwide. Melanoma 5-year survival is >99% when localised but drops to 27% once metastasised. Dermatologists integrate four modalities: clinical photos, dermoscopic images, patient metadata, and symptom narratives. Smartphone-era AI is deployed without any mechanism to judge whether its evidence is adequate.",FONT_B,13,color=BODY_DARK)

card(s,Inches(0.55),Inches(4.4),Inches(5.65),Inches(2.75),TEAL_CARD)
b3=tb(s,Inches(0.75),Inches(4.58),Inches(5.25),Inches(0.28)); tf3=b3.text_frame
tf3.margin_left=tf3.margin_right=tf3.margin_top=tf3.margin_bottom=0
para(tf3,"OUR RESEARCH QUESTION",FONT_B,11,bold=True,color=TEAL_DARK)
b4=tb(s,Inches(0.75),Inches(4.88),Inches(5.25),Inches(2.1)); tf4=b4.text_frame
tf4.word_wrap=True; tf4.margin_left=tf4.margin_right=tf4.margin_top=tf4.margin_bottom=0
para(tf4,'How can a system judge the quality, reliability, and sufficiency of each evidence channel — and decide when to diagnose, when to ask for more, and when to refer — rather than always forcing a confident label?',FONT_H,14.5,color=HEAD_DARK)

pills=[("Q","Quality Issue","Blurry/occluded images silently degrade accuracy without warning"),
       ("R","Reliability Gap","Models report 99% confidence even on corrupted or OOD inputs"),
       ("C","Contradiction","Image says benign; text reports rapid growth and bleeding"),
       ("M","Missing Modalities","Metadata absent, dermoscopy unavailable — model still answers")]
for i,(ltr,lbl,desc) in enumerate(pills):
    pill_row(s, Inches(6.55), Inches(1.68)+i*Inches(1.38), Inches(6.15), Inches(0.38), ltr,lbl,desc)
foot(s)

# ──────────────────────────────────────────────────── S3: OBJECTIVES ────────
s = blank(prs); setbg(s,BG_WHITE)
header(s,"Research Objectives & Innovation","What DERMA-GUARD Does Differently","Four novel mechanisms forming a unified evidence-aware, risk-controlled framework")

cards4=[("01","Specialist Consensus Team","Consults 6 distinct specialist opinions (evidential photo/dermoscopy/metadata heads, legacy CNN, kNN case memory, class-balanced logistic) rather than one monolithic encoder.",TEAL_BRIGHT),
        ("02","Dynamic Evidence Profiling","Per-case 10-signal evidence profile: Quality (Q), Reliability (R), Entropy (U), Consistency (C), OOD Mahalanobis distance, track record — before any fusion.",TEAL_DARK),
        ("03","Diagnosis-Adaptive Fusion","Weights adapt to provisional diagnosis: dermoscopy trusted more for melanoma, patient history for inflammatory lesions. Learned gating beats 6 alternative fusion rules.",HEAD_DARK),
        ("04","Risk-Controlled 4-Outcome Policy","Learn-then-Test bound certifies missed-cancer rate <= 3.1%. Four actions: HIGH confidence, ACQUIRE evidence, LOW (clinician confirm), DEFER (hospital referral).",ACCENT_GRN)]

for i,(num,title,desc,acc) in enumerate(cards4):
    col=i%2; row=i//2
    L=Inches(0.55+col*6.35); T=Inches(1.72+row*2.7)
    card(s,L,T,Inches(6.05),Inches(2.5),TEAL_CARD,acc)
    rect(s,L+Inches(0.15),T+Inches(0.2),Inches(0.55),Inches(0.32),acc)
    bn=tb(s,L+Inches(0.15),T+Inches(0.2),Inches(0.55),Inches(0.32)); tfn=bn.text_frame
    tfn.margin_left=tfn.margin_right=tfn.margin_top=tfn.margin_bottom=0
    para(tfn,num,FONT_B,11,bold=True,color=WHITE,align=PP_ALIGN.CENTER)
    bt=tb(s,L+Inches(0.82),T+Inches(0.18),Inches(5.1),Inches(0.36)); tft=bt.text_frame
    tft.margin_left=tft.margin_right=tft.margin_top=tft.margin_bottom=0
    para(tft,title,FONT_B,14,bold=True,color=HEAD_DARK)
    bd=tb(s,L+Inches(0.2),T+Inches(0.6),Inches(5.7),Inches(1.75)); tfd=bd.text_frame
    tfd.word_wrap=True; tfd.margin_left=tfd.margin_right=tfd.margin_top=tfd.margin_bottom=0
    para(tfd,desc,FONT_B,12,color=BODY_DARK)
foot(s)

# ──────────────────────────────────────────────────── S4: ARCHITECTURE ──────
s = blank(prs); setbg(s,BG_WHITE)
header(s,"System Architecture","Evidence-Aware Pipeline — End to End","Specialists -> Evidence Profiler -> Adaptive Fusion Gate -> Risk-Controlled Policy")
img(s, IMG+r"\docs\paper_src\arch.png", Inches(0.55),Inches(1.72), width=Inches(7.5))

dark_card(s,Inches(8.3),Inches(1.72),Inches(4.45),Inches(5.45))
b=tb(s,Inches(8.52),Inches(1.9),Inches(4.0),Inches(0.28)); tf=b.text_frame
tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
para(tf,"PIPELINE STAGES",FONT_B,11,bold=True,color=TEAL_BRIGHT)

steps6=[("1","Ingest active modalities + missingness mask M"),
        ("2","Encode: ViT / MetaBlock MLP / Bio_ClinicalBERT"),
        ("3","Score 10 evidence signals -> dynamic fusion weights"),
        ("4","All compatible models A-G produce specialist opinions"),
        ("5","Adaptive fusion + EM-style prior refinement (3 iters)"),
        ("6","LTT-certified 4-outcome policy: HIGH/ACQUIRE/LOW/DEFER")]
for i,(n,t) in enumerate(steps6):
    ty=Inches(2.3)+i*Inches(0.76)
    badge(s,Inches(8.52),ty,n)
    bs=tb(s,Inches(9.02),ty-Inches(0.02),Inches(3.55),Inches(0.7)); tfs=bs.text_frame
    tfs.word_wrap=True; tfs.margin_left=tfs.margin_right=tfs.margin_top=tfs.margin_bottom=0
    para(tfs,t,FONT_B,10.8,color=TEAL_SOFT)
foot(s)

# ──────────────────────────────────────────────────── S5: EVIDENCE SCORING ──
s = blank(prs); setbg(s,BG_WHITE)
header(s,"Evidence Manager","Evidence Scoring & Fusion Weights","Per-modality signals that gate every fusion decision and enable safe abstention")

pills5=[("Q","Quality","Image sharpness (Laplacian variance), contrast, brightness vs training percentiles"),
        ("R","Reliability","Cross-fitted logistic regressor predicting whether specialist m is correct on this case"),
        ("U","Utility","Normalised predictive Shannon entropy + Dempster-Shafer vacuity per evidential head"),
        ("C","Consistency","1 - mean pairwise Jensen-Shannon divergence across modality predicted distributions"),
        ("S","Sufficiency","0.35*Q + 0.35*R + 0.20*C + 0.10*(1-missing) -- the final decision gate threshold")]
for i,(ltr,lbl,desc) in enumerate(pills5):
    pill_row(s, Inches(0.55),Inches(1.72)+i*Inches(0.86), Inches(6.3), Inches(0.38), ltr,lbl,desc)

dark_card(s,Inches(7.1),Inches(1.72),Inches(5.65),Inches(5.45))
b=tb(s,Inches(7.3),Inches(2.0),Inches(5.2),Inches(0.28)); tf=b.text_frame
tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
para(tf,"EVIDENCE SCORE & FUSION WEIGHT",FONT_B,10.5,bold=True,color=TEAL_BRIGHT)
b2=tb(s,Inches(7.3),Inches(2.3),Inches(5.2),Inches(0.45)); tf2=b2.text_frame
tf2.margin_left=tf2.margin_right=tf2.margin_top=tf2.margin_bottom=0
para(tf2,"E_m = Q_m * R_m * U_m * C * S",FONT_C,15,bold=True,color=WHITE)
b3=tb(s,Inches(7.3),Inches(2.72),Inches(5.2),Inches(0.38)); tf3=b3.text_frame
tf3.margin_left=tf3.margin_right=tf3.margin_top=tf3.margin_bottom=0
para(tf3,"w_m = E_m / sum(E_m)   (normalised weight)",FONT_C,12.5,color=TEAL_SOFT)

bt=tb(s,Inches(7.3),Inches(3.25),Inches(5.2),Inches(0.28)); tft=bt.text_frame
tft.margin_left=tft.margin_right=tft.margin_top=tft.margin_bottom=0
para(tft,"SUFFICIENCY GATE",FONT_B,10.5,bold=True,color=TEAL_BRIGHT)

gates=[("S < 0.30","INSUFFICIENT -> Abstain / escalate to clinician"),
       ("0.30-0.50","ACQUIRE -> Request dermoscopy / symptom history"),
       ("S >= 0.50","PROCEED -> Continue with calibrated prediction")]
for k,(cond,act) in enumerate(gates):
    ty=Inches(3.58)+k*Inches(0.65)
    bc=tb(s,Inches(7.3),ty,Inches(2.0),Inches(0.3)); tfc=bc.text_frame
    tfc.margin_left=tfc.margin_right=tfc.margin_top=tfc.margin_bottom=0
    para(tfc,cond,FONT_C,10.5,bold=True,color=TEAL_BRIGHT)
    ba=tb(s,Inches(9.35),ty,Inches(3.3),Inches(0.3)); tfa=ba.text_frame
    tfa.word_wrap=True; tfa.margin_left=tfa.margin_right=tfa.margin_top=tfa.margin_bottom=0
    para(tfa,act,FONT_B,10.3,color=TEAL_SOFT)

b5=tb(s,Inches(7.3),Inches(5.65),Inches(5.2),Inches(1.1)); tf5=b5.text_frame
tf5.word_wrap=True; tf5.margin_left=tf5.margin_right=tf5.margin_top=tf5.margin_bottom=0
para(tf5,"Learned fusion weights for Model G (PAD-UFES-20): Image 0.717 | Metadata 0.179 | Free Text 0.104. Chosen from 7 fusion rules via 5-fold cross-fitting on validation set.",FONT_B,11,color=MUTED)
foot(s)

# ──────────────────────────────────────────────────── S6: MODEL LADDER ──────
s = blank(prs); setbg(s,BG_WHITE)
header(s,"Benchmark Architecture Ladder","The 7 Systematic Multimodal Models  (A through G)","PAD-UFES-20 | N=2,298 | Train 1,953 / Val 229 / Test 459 | 30 epochs")

rows=[["Model","Input Modalities","Neural Encoders","Test Acc","Key Purpose"],
      ["A","Image Only","ResNet50 + Multi-Head Self-Attention","83.66%","Visual morphological baseline"],
      ["B","Metadata Only","Residual MetaBlock MLP","86.27%","Pure demographic & history baseline"],
      ["C","Free Text Only","Bio_ClinicalBERT (mean-pool 768-d)","85.19%","NLP symptom narrative baseline"],
      ["D","Image + Metadata","ViT + MetaBlock MLP","86.27%","Visual-demographic synergy"],
      ["E","Image + Free Text","ViT + Bio_ClinicalBERT","89.98%","BEST — visual-narrative synergy"],
      ["F","Text + Metadata","Bio_ClinicalBERT + MetaBlock MLP","85.40%","Non-imaging clinical consultation"],
      ["G","Full Tri-Modal","ViT + MetaBlock MLP + Bio_ClinicalBERT","87.80%","Comprehensive tri-modal (best coverage)"]]
cw=[Inches(0.9),Inches(2.1),Inches(3.9),Inches(1.05),Inches(4.05)]
rh=Inches(0.62); TL=Inches(0.55); TT=Inches(1.72)

for ri,row in enumerate(rows):
    is_h=(ri==0); is_e=(ri==5)
    ry=TT+ri*rh; x=TL
    for ci,cell in enumerate(row):
        bg_c=BG_DARK if is_h else (RGBColor(0xCC,0xF0,0xEB) if is_e else (TEAL_CARD if ri%2==0 else BG_WHITE))
        rect(s,x,ry,cw[ci],rh,bg_c,RGBColor(0xBF,0xE3,0xDE))
        bx=tb(s,x+Inches(0.06),ry+Inches(0.1),cw[ci]-Inches(0.1),rh-Inches(0.1)); tf=bx.text_frame
        tf.word_wrap=True; tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
        clr=WHITE if is_h else (TEAL_DARK if is_e else BODY_DARK)
        para(tf,cell,FONT_B,11,bold=(is_h or is_e),color=clr)
        x+=cw[ci]
foot(s)

# ──────────────────────────────────────────────────── S7: RESULTS SCORECARD ─
s = blank(prs); setbg(s,BG_WHITE)
header(s,"Results — Comprehensive Benchmark","Master Scorecard: All 7 Models (PAD-UFES-20)","Test N=459 | Dataset: 1,953 Train / 229 Val / 459 Test | 30 epochs | AdamW + cosine annealing")
img(s, IMG+r"\Dummy\Project\saved_models\models_master_scorecard.png", Inches(0.55),Inches(1.72), width=Inches(12.2))

dark_card(s,Inches(0.55),Inches(6.1),Inches(12.2),Inches(1.1))
b=tb(s,Inches(0.75),Inches(6.18),Inches(12.0),Inches(0.28)); tf=b.text_frame
tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
para(tf,"KEY TAKEAWAYS",FONT_B,10.5,bold=True,color=TEAL_BRIGHT)
b2=tb(s,Inches(0.75),Inches(6.47),Inches(12.0),Inches(0.65)); tf2=b2.text_frame
tf2.word_wrap=True; tf2.margin_left=tf2.margin_right=tf2.margin_top=tf2.margin_bottom=0
para(tf2,"Model E (Image+Text): 89.98% Acc | 0.8874 Precision | 0.8926 F1 | 0.9982 Macro AUC   ——   Model G (Tri-Modal): 87.80% Acc | 0.9247 Sensitivity | 0.9895 AUPRC   ——   All 7 models exceed Macro AUC > 0.994",FONT_B,11,color=TEAL_SOFT)
foot(s)

# ──────────────────────────────────────────────────── S8: BAR CHART ─────────
s = blank(prs); setbg(s,BG_WHITE)
header(s,"Results — Performance Comparison","Accuracy, Precision, F1-Score & Macro AUC Across All Models","Every fusion combination evaluated on identical test partition (N=459)")

img(s, IMG+r"\Dummy\Project\saved_models\models_comparison_graph.png", Inches(0.55),Inches(1.72), width=Inches(7.8))

card(s,Inches(8.6),Inches(1.72),Inches(4.15),Inches(5.45),TEAL_CARD)
b=tb(s,Inches(8.8),Inches(1.9),Inches(3.75),Inches(0.28)); tf=b.text_frame
tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
para(tf,"MODALITY VALUE ANALYSIS",FONT_B,12.5,bold=True,color=TEAL_DARK)

ins=[("Free Text + Image:","Adds +6.32% accuracy (A 83.66% -> E 89.98%) — single biggest gain"),
     ("Metadata + Image:","Adds +2.61% accuracy (A 83.66% -> D 86.27%)"),
     ("Tri-Modal Coverage:","Model G best sensitivity 0.9247 & specificity 0.9734"),
     ("Model E Weights:","Image 0.825  |  Free Text 0.175"),
     ("Model G Weights:","Image 0.717  |  Meta 0.179  |  Text 0.104"),
     ("Cancer Safety:","Model E keeps 99.5% (216/217) cancers in cancer class"),
     ("All Models AUC:","All 7 exceed Macro AUC > 0.994 (near-perfect separation)")]
for k,(lbl,val) in enumerate(ins):
    ty=Inches(2.35)+k*Inches(0.65)
    bx=tb(s,Inches(8.8),ty,Inches(3.75),Inches(0.62)); tf=bx.text_frame
    tf.word_wrap=True; tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
    para(tf,lbl,FONT_B,11,bold=True,color=HEAD_DARK)
    add(tf,val,FONT_B,11,color=BODY_DARK,sb=1)
foot(s)

# ──────────────────────────────────────────────────── S9: CONFUSION MATRICES ─
s = blank(prs); setbg(s,BG_WHITE)
header(s,"Results — Diagnostic Error Profiling","Confusion Matrices: All 7 Models (PAD-UFES-20 Test N=459)","Per-class recall across BCC, ACK, NEV, SEK, SCC, MEL")
img(s, IMG+r"\Dummy\Project\saved_models\all_models_confusion_matrices.png", Inches(0.55),Inches(1.72), height=Inches(5.45))

card(s,Inches(8.3),Inches(1.72),Inches(4.45),Inches(5.45),TEAL_CARD)
b=tb(s,Inches(8.5),Inches(1.9),Inches(4.05),Inches(0.28)); tf=b.text_frame
tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
para(tf,"DIAGNOSTIC SAFETY",FONT_B,12.5,bold=True,color=TEAL_DARK)

safe=[("100% MEL Recall:","All 7 models detect 10/10 true melanomas. Zero missed melanomas."),
      ("100% Benign Purity:","NEV (49/49) & SEK (47/47) = 100% recall. No benign called malignant."),
      ("Cancer Retention:","Model E: 99.5% (216/217). Model B: 97.2%. Model G: 92.2%."),
      ("SCC Challenge:","Metadata alone (Model B) misses 57.9% of SCC; full image recovers 100%."),
      ("ACK vs BCC:","ACK recall 72.6-86.3%; BCC 79.3-98.8% across architectures.")]
for k,(lbl,val) in enumerate(safe):
    ty=Inches(2.35)+k*Inches(0.87)
    bx=tb(s,Inches(8.5),ty,Inches(4.05),Inches(0.82)); tf=bx.text_frame
    tf.word_wrap=True; tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
    para(tf,lbl,FONT_B,11.5,bold=True,color=HEAD_DARK)
    add(tf,val,FONT_B,11,color=BODY_DARK,sb=2)
foot(s)

# ──────────────────────────────────────────────────── S10: TRAINING CURVES ───
s = blank(prs); setbg(s,BG_WHITE)
header(s,"Results — Training Dynamics","Training Loss & Validation Accuracy  (All 7 Models, 30 Epochs)","Monotonic convergence, stable plateau, no overfitting across all architectures")
img(s, IMG+r"\Dummy\Project\saved_models\all_models_training_curves.png", Inches(0.55),Inches(1.72), height=Inches(5.45))

card(s,Inches(8.3),Inches(1.72),Inches(4.45),Inches(5.45),TEAL_CARD)
b=tb(s,Inches(8.5),Inches(1.9),Inches(4.05),Inches(0.28)); tf=b.text_frame
tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
para(tf,"TRAINING DYNAMICS",FONT_B,12.5,bold=True,color=TEAL_DARK)

curv=[("Loss Descent:","Smooth fall from 1.65-1.85 to 0.17-0.27 over 30 epochs. No divergence."),
      ("Val Plateau:","Val accuracy rises from ~70% (epoch 1) and plateaus at epochs 22-26."),
      ("Val -> Test Gap:","E: Val 89.63% -> Test 89.98% (+0.35). G: Val 87.07% -> Test 87.80%."),
      ("Optimiser:","AdamW (wd=1e-4) + cosine annealing (eta_min=1e-5) + gradient clipping."),
      ("No Overfitting:","Val and test accuracy track each other closely across all 7 variants.")]
for k,(lbl,val) in enumerate(curv):
    ty=Inches(2.35)+k*Inches(0.9)
    bx=tb(s,Inches(8.5),ty,Inches(4.05),Inches(0.85)); tf=bx.text_frame
    tf.word_wrap=True; tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
    para(tf,lbl,FONT_B,11.5,bold=True,color=HEAD_DARK)
    add(tf,val,FONT_B,11,color=BODY_DARK,sb=2)
foot(s)

# ──────────────────────────────────────────────────── S11: PER-CLASS F1 ──────
s = blank(prs); setbg(s,BG_WHITE)
header(s,"Results — Per-Class Performance","Per-Class Sensitivity, Precision & F1-Score Detail","Revealing how each model handles rare malignancies vs dominant benign classes")

# Table: per-class F1
rows_f1=[["Model","BCC","ACK","NEV","SEK","SCC","MEL","Overall Acc"],
         ["A","84.0%","78.2%","90.7%","100%","79.2%","66.7%","83.66%"],
         ["B","87.8%","86.1%","92.5%","100%","48.5%","87.0%","86.27%"],
         ["C","83.9%","84.2%","93.3%","100%","73.2%","66.7%","85.19%"],
         ["D","85.8%","82.9%","92.5%","100%","82.6%","69.0%","86.27%"],
         ["E","92.5%","87.8%","92.5%","100%","67.6%","95.2%","89.98%"],
         ["F","84.4%","84.8%","93.3%","100%","70.0%","69.0%","85.40%"],
         ["G","86.2%","87.2%","95.1%","100%","79.5%","69.0%","87.80%"]]
cwf=[Inches(1.0),Inches(1.48),Inches(1.48),Inches(1.48),Inches(1.48),Inches(1.48),Inches(1.48),Inches(1.98)]
rhf=Inches(0.6); TTf=Inches(1.72); TLf=Inches(0.55)
for ri,row in enumerate(rows_f1):
    is_h=(ri==0); is_e=(ri==5)
    ry=TTf+ri*rhf; x=TLf
    for ci,cell in enumerate(row):
        bg_c=BG_DARK if is_h else (RGBColor(0xCC,0xF0,0xEB) if is_e else (TEAL_CARD if ri%2==0 else BG_WHITE))
        # highlight 100% cells
        if not is_h and cell=="100%": bg_c=RGBColor(0xA7,0xF3,0xD0)
        rect(s,x,ry,cwf[ci],rhf,bg_c,RGBColor(0xBF,0xE3,0xDE))
        bx=tb(s,x+Inches(0.04),ry+Inches(0.08),cwf[ci]-Inches(0.06),rhf-Inches(0.1)); tf=bx.text_frame
        tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
        clr=WHITE if is_h else (ACCENT_GRN if cell=="100%" and not is_h else (TEAL_DARK if is_e else BODY_DARK))
        para(tf,cell,FONT_B,10.5,bold=(is_h or is_e or cell=="100%"),color=clr,align=PP_ALIGN.CENTER)
        x+=cwf[ci]

# Legend below table
by=TTf+len(rows_f1)*rhf+Inches(0.12)
bleg=tb(s,Inches(0.55),by,Inches(12.2),Inches(0.35)); tf=bleg.text_frame
tf.word_wrap=True; tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
para(tf,"Green = 100% recall (perfect).   Bold teal row = Model E (best overall).   SEK achieves 100% F1 in every model.   MEL (10 test cases) ranges 66.7%-95.2%; Model E reaches 95.2% MEL F1.",FONT_B,11,color=MUTED)
foot(s)

# ──────────────────────────────────────────────────── S12: RISK CONTROL ──────
s = blank(prs); setbg(s,BG_WHITE)
header(s,"Risk-Controlled Decision Policy","Statistical Safety Bounds & 4-Outcome Policy","Learn-then-Test guarantees + Mondrian conformal prediction + DERMA-STRESS robustness")

card(s,Inches(0.55),Inches(1.72),Inches(6.05),Inches(5.45),TEAL_CARD,TEAL_BRIGHT)
b=tb(s,Inches(0.75),Inches(1.9),Inches(5.6),Inches(0.28)); tf=b.text_frame
tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
para(tf,"LEARN-THEN-TEST (LTT) BOUNDS",FONT_B,12.5,bold=True,color=TEAL_DARK)

ltt=[("Certified Miss Rate:","3.1% missed-cancer rate on confident answers (target <=5%)"),
     ("vs Learned Rejector:","Our 3.1% vs L2D 4.9% (p=0.011) — statistically significant"),
     ("vs Conf Threshold:","Our 3.1% vs threshold 3.8% — more stable"),
     ("Backend Invariance:","4 fusion back-ends: policy 3.0-3.5% vs threshold 3.5-9.3%"),
     ("Coverage:","89.1% patients answered; 57.1% with high confidence"),
     ("Conformal Sets:","Mondrian sets: 91% empirical coverage at 90% target")]
for k,(lbl,val) in enumerate(ltt):
    ty=Inches(2.35)+k*Inches(0.72)
    bx=tb(s,Inches(0.75),ty,Inches(5.6),Inches(0.68)); tf=bx.text_frame
    tf.word_wrap=True; tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
    para(tf,lbl,FONT_B,11.5,bold=True,color=HEAD_DARK)
    add(tf,val,FONT_B,11,color=BODY_DARK,sb=1)

dark_card(s,Inches(6.85),Inches(1.72),Inches(6.0),Inches(5.45))
b=tb(s,Inches(7.05),Inches(1.9),Inches(5.6),Inches(0.28)); tf=b.text_frame
tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
para(tf,"4-OUTCOME CLINICAL POLICY",FONT_B,11,bold=True,color=TEAL_BRIGHT)

acts=[("HIGH (ACCEPT):","Confidence >= 0.80. Agreement >= 75%. All quality checks pass. LTT miss-cancer bound holds. Auto-schedules follow-up."),
      ("ACQUIRE:","Active VOI estimator recommends: take dermoscopy, clarify bleeding/growth history, or retake photo. Cost-weighted priority."),
      ("LOW (ARBITRATE):","Mondrian conformal set spans 2+ classes. Provisional label with uncertainty range delivered; clinician must confirm."),
      ("DEFER / REFER:","Dempster-Shafer conflict > 90th percentile OR Mahalanobis OOD alert. Immediate human referral issued.")]
for k,(lbl,val) in enumerate(acts):
    ty=Inches(2.35)+k*Inches(1.1)
    bx=tb(s,Inches(7.05),ty,Inches(5.6),Inches(1.0)); tf=bx.text_frame
    tf.word_wrap=True; tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
    para(tf,lbl,FONT_B,11,bold=True,color=TEAL_BRIGHT)
    add(tf,val,FONT_B,10.8,color=TEAL_SOFT,sb=2)
foot(s)

# ──────────────────────────────────────────────────── S13: MULTI-AGENT LAYER ─
s = blank(prs); setbg(s,BG_WHITE)
header(s,"Multi-Agent Orchestration","The 6-Agent Clinical Intelligence Layer","Specialist AI agents working in concert to produce safe, explainable, traceable decisions")

agents=[("OrchestratorAgent","Coordinates the full pipeline: assigns tasks to all sub-agents, collects reports, resolves disagreements, and routes the case to the correct outcome tier.",TEAL_BRIGHT),
        ("VisionSpecialistTeam","Runs DermLIP-PanDerm (VLM), PanDerm encoder, dual Swin-Tiny (clinical + dermoscopy), and ResNet152 in parallel. Returns logits, embeddings, and per-image quality scores.",TEAL_DARK),
        ("ScribeAgent","Bio_ClinicalBERT encodes patient narrative. Extracts structured symptoms (growth, itch, bleed, duration) via Qwen2.5-7B structured prompts. Computes PTIS informativeness score.",HEAD_DARK),
        ("LibrarianAgent","FAISS dual-modality vector search retrieves top-K confirmed historical training cases for visual comparison. Provides clinical look-alike context to the dermatologist.",ACCENT_GRN),
        ("DevilsAdvocateAgent","Computes 10-signal evidence profile (Q, R, U, C, pi, OOD). Detects cross-modal conflicts via Dempster-Shafer. Flags corrupted images, OOD inputs, and dangerous contradictions.",ACCENT_RED),
        ("ReportVerificationAgent","Two-stage pipeline: rule-based check + Qwen2.5-7B LLM verifier ensures every claim in the clinical report is 100% traceable to evidence JSON. Hallucinated claims discard the draft.",ACCENT_BRN)]

for i,(name,desc,acc) in enumerate(agents):
    col=i%2; row=i//2
    L=Inches(0.55+col*6.35); T=Inches(1.72+row*1.84)
    card(s,L,T,Inches(6.05),Inches(1.74),TEAL_CARD,acc)
    bn=tb(s,L+Inches(0.2),T+Inches(0.15),Inches(5.7),Inches(0.32)); tfn=bn.text_frame
    tfn.margin_left=tfn.margin_right=tfn.margin_top=tfn.margin_bottom=0
    para(tfn,name,FONT_B,13,bold=True,color=acc)
    bd=tb(s,L+Inches(0.2),T+Inches(0.5),Inches(5.7),Inches(1.15)); tfd=bd.text_frame
    tfd.word_wrap=True; tfd.margin_left=tfd.margin_right=tfd.margin_top=tfd.margin_bottom=0
    para(tfd,desc,FONT_B,11,color=BODY_DARK)
foot(s)

# ──────────────────────────────────────────────────── S14: RAG SYSTEM ────────
s = blank(prs); setbg(s,BG_WHITE)
header(s,"Retrieval-Augmented Generation (RAG)","Visual Case-Based Retrieval & Knowledge System","LibrarianAgent provides confirmed historical look-alikes to dermatologists for clinical comparison")

# Left: RAG screenshot
img(s, IMG+r"\docs\paper_src\site_rag.png", Inches(0.55),Inches(1.72), height=Inches(5.45))

# Right: RAG details
card(s,Inches(5.8),Inches(1.72),Inches(7.0),Inches(5.45),TEAL_CARD)
b=tb(s,Inches(6.0),Inches(1.9),Inches(6.6),Inches(0.28)); tf=b.text_frame
tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
para(tf,"HOW THE RAG SYSTEM WORKS",FONT_B,12.5,bold=True,color=TEAL_DARK)

rag_items=[("Dual-Modality Embeddings:","Visual embeddings (768-d from ViT) + clinical text embeddings (768-d from Bio_ClinicalBERT) concatenated into a single modality-agnostic retrieval vector."),
           ("FAISS Vector Index:","Flat L2 index over all 1,953 training embeddings. Retrieves top-K (K=15 default) nearest confirmed training lesions in under 10ms."),
           ("Histopathological Ground Truth:","Every retrieved case is linked to its confirmed diagnosis. Only cases with validated outcomes are indexed, ensuring medical reliability."),
           ("Similarity-Weighted Voting:","Retrieved cases vote on the diagnosis weighted by exp(5 * cosine_similarity), giving higher influence to very close neighbours."),
           ("Clinical Interface (S5):","Dermatologist dashboard displays retrieved case images side-by-side with patient case for visual comparison and informed second opinion."),
           ("RAG + LLM Integration:","Librarian evidence summary is injected into the Orchestrator's context, enabling the ReportAgent to cite 'similar confirmed cases' in the clinical report.")]
for k,(lbl,val) in enumerate(rag_items):
    ty=Inches(2.35)+k*Inches(0.76)
    bx=tb(s,Inches(6.0),ty,Inches(6.6),Inches(0.72)); tf=bx.text_frame
    tf.word_wrap=True; tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
    para(tf,lbl,FONT_B,11.5,bold=True,color=HEAD_DARK)
    add(tf,val,FONT_B,11,color=BODY_DARK,sb=1)
foot(s)

# ──────────────────────────────────────────────────── S15: WEB PORTAL ────────
s = blank(prs); setbg(s,BG_WHITE)
header(s,"Clinical Web Platform","Full-Stack Care Portal — Patient, Clinician & Admin Views","FastAPI backend | SQLite RBAC | Multi-agent API | Visual RAG | 230 automated tests")

img(s, IMG+r"\docs\paper_src\site_home.png", Inches(0.55),Inches(1.72), width=Inches(5.9))
img(s, IMG+r"\docs\paper_src\site_doctor_dash.png", Inches(6.65),Inches(1.72), width=Inches(6.2))

dark_card(s,Inches(0.55),Inches(5.6),Inches(12.2),Inches(1.6))
b=tb(s,Inches(0.75),Inches(5.75),Inches(12.0),Inches(0.28)); tf=b.text_frame
tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
para(tf,"PLATFORM ARCHITECTURE",FONT_B,10.5,bold=True,color=TEAL_BRIGHT)
b2=tb(s,Inches(0.75),Inches(6.05),Inches(12.0),Inches(1.0)); tf2=b2.text_frame
tf2.word_wrap=True; tf2.margin_left=tf2.margin_right=tf2.margin_top=tf2.margin_bottom=0
para(tf2,"FastAPI async endpoints (/predict /triage /acquire /case) | RBAC (Patient / Doctor / Admin) with scrypt + CSRF + HttpOnly sessions | SQLite append-only audit log | Multi-agent orchestration | FAISS visual RAG | Two-stage LLM verification (Qwen2.5-7B) | Follow-up monitoring (delta P(malignant) >= 0.15 triggers urgent re-queue) | 230 automated tests",FONT_B,11,color=TEAL_SOFT)
foot(s)

# ──────────────────────────────────────────────────── S16: EVIDENCE RESULTS ──
s = blank(prs); setbg(s,BG_WHITE)
header(s,"Results — Evidence & Site Views","Evidence Panel & Clinical Decision Interface","Site views showing evidence profile, model scores, and clinician triage queue")

img(s, IMG+r"\docs\paper_src\site_evidence.png", Inches(0.55),Inches(1.72), width=Inches(5.5))
img(s, IMG+r"\docs\paper_src\site_result.png", Inches(6.2),Inches(1.72), width=Inches(6.6))

dark_card(s,Inches(0.55),Inches(5.6),Inches(12.2),Inches(1.6))
b=tb(s,Inches(0.75),Inches(5.75),Inches(12.0),Inches(0.28)); tf=b.text_frame
tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
para(tf,"TRANSPARENCY & EXPLAINABILITY",FONT_B,10.5,bold=True,color=TEAL_BRIGHT)
b2=tb(s,Inches(0.75),Inches(6.05),Inches(12.0),Inches(1.0)); tf2=b2.text_frame
tf2.word_wrap=True; tf2.margin_left=tf2.margin_right=tf2.margin_top=tf2.margin_bottom=0
para(tf2,"Evidence Panel shows per-modality Q, R, U, C scores, Dempster-Shafer conflict, OOD distance, and sufficiency gate decision. Result View shows: temperature-calibrated confidence, specialist vote breakdown, acquisition recommendation, conformal prediction set, and RAG look-alike thumbnails. All numbers are traceable to the raw evidence JSON.",FONT_B,11,color=TEAL_SOFT)
foot(s)

# ──────────────────────────────────────────────────── S17: CHALLENGES ────────
s = blank(prs); setbg(s,BG_WHITE)
header(s,"Problem-Solving & Technical Refinement","Challenges Hit — and How We Responded","Honest account: what failed, what was fixed, what the audit revealed")

chals=[("Data Leakage Audit","Legacy baseline scripts had train/test patient overlap, inflating reported accuracy to ~90%. Enforced patient-disjoint splits; true held-out figures: image 61-65%, metadata 78%.",TEAL_BRIGHT),
       ("Confidence Thresholding Unsafe","Standard threshold's miss rate swings 3.5%-9.3% across 4 fusions. LTT-certified policy stays bounded at 3.0-3.5% regardless of the fusion beneath it.",TEAL_DARK),
       ("Chow's Rule Collapsed","Minimum-cost rule labelled 98.5% of lesions malignant on skewed population. Replaced with Mondrian conformal gate calibrated on validation data.",HEAD_DARK),
       ("Oracle Gap","Oracle best-specialist per case: Macro-F1 0.594 vs learned gate 0.438. Gap motivates better gating via foundation backbone (PanDerm) in future work.",ACCENT_GRN),
       ("Text Path Instability","Bio_ClinicalBERT inference projector initially didn't match training features. Fixed: freeze encoder + retrain projector with matched tokenizer and max_length.",ACCENT_BRN),
       ("Logit Adjustment Backfired","Post-hoc label-based scaling raised val F1 (0.36->0.44) but degraded test F1 (0.376->0.359). Removed; raw outputs with bootstrap CIs reported.",ACCENT_RED)]
for i,(title,desc,acc) in enumerate(chals):
    col=i%2; row=i//2
    L=Inches(0.55+col*6.35); T=Inches(1.72+row*1.88)
    card(s,L,T,Inches(6.05),Inches(1.78),TEAL_CARD,acc)
    bt=tb(s,L+Inches(0.18),T+Inches(0.18),Inches(5.7),Inches(0.3)); tft=bt.text_frame
    tft.margin_left=tft.margin_right=tft.margin_top=tft.margin_bottom=0
    para(tft,title,FONT_B,12,bold=True,color=acc)
    bd=tb(s,L+Inches(0.18),T+Inches(0.5),Inches(5.7),Inches(1.2)); tfd=bd.text_frame
    tfd.word_wrap=True; tfd.margin_left=tfd.margin_right=tfd.margin_top=tfd.margin_bottom=0
    para(tfd,desc,FONT_B,11,color=BODY_DARK)
foot(s)

# ──────────────────────────────────────────────────── S18: TEAM ──────────────
s = blank(prs); setbg(s,BG_WHITE)
header(s,"Team & Contributions","Individual Roles & Deliverables","School of Computer Science and Engineering, VIT Chennai | Dr. Sindhu Ravindran (Supervisor)")

members=[("AARAV PRAWIN","23BDS1116 | B.Tech Data Science",TEAL_BRIGHT,
          ["Data pipeline + patient-level split generation & leakage audit",
           "Vision specialist encoders: ResNet50+MHSA, ViT, evidential heads",
           "Multi-model benchmark execution: Models A through G (PAD-UFES-20)",
           "Confusion matrix analysis, sensitivity/precision/ROC profiling",
           "DERMA-STRESS visual corruption benchmark (15 conditions)"]),
         ("PATEL KAVYA VIPULKUMAR","23BDS1076 | B.Tech Data Science",TEAL_DARK,
          ["NLP Scribe Agent: Bio_ClinicalBERT + symptom extraction (Qwen2.5)",
           "Evidence Profiler: Quality (Q), Reliability (R), Consistency (C) computation",
           "Diagnosis-Adaptive Fusion (EM-style iterative formulation)",
           "Learned gating evaluated against 7 fusion alternatives (5-fold CV)",
           "DERMA-STRESS semantic adversarial attack design (metadata poisoning)"]),
         ("RACHIT AGARWAL","23BCE1577 | B.Tech CSE",HEAD_DARK,
          ["Learn-then-Test (LTT) risk-controlled policy implementation",
           "Mondrian conformal calibration + active VOI acquisition estimator",
           "FastAPI production backend + SQLite RBAC + session/CSRF security",
           "Clinician/Patient web portal + FAISS Visual RAG + LibrarianAgent",
           "230 automated unit & integration tests + audit log & GDPR hooks"])]

for i,(name,role,acc,tasks) in enumerate(members):
    L=Inches(0.55+i*4.18); T=Inches(1.72)
    card(s,L,T,Inches(4.0),Inches(5.45),TEAL_CARD,acc)
    bn=tb(s,L+Inches(0.18),T+Inches(0.18),Inches(3.65),Inches(0.4)); tfn=bn.text_frame
    tfn.word_wrap=True; tfn.margin_left=tfn.margin_right=tfn.margin_top=tfn.margin_bottom=0
    para(tfn,name,FONT_B,12.5,bold=True,color=acc)
    br=tb(s,L+Inches(0.18),T+Inches(0.6),Inches(3.65),Inches(0.28)); tfr=br.text_frame
    tfr.margin_left=tfr.margin_right=tfr.margin_top=tfr.margin_bottom=0
    para(tfr,role,FONT_B,10.5,color=MUTED)
    for ki,task in enumerate(tasks):
        ty=T+Inches(0.98)+ki*Inches(0.82)
        badge(s,L+Inches(0.18),ty+Inches(0.04),str(ki+1))
        bt2=tb(s,L+Inches(0.68),ty,Inches(3.15),Inches(0.75)); tft2=bt2.text_frame
        tft2.word_wrap=True; tft2.margin_left=tft2.margin_right=tft2.margin_top=tft2.margin_bottom=0
        para(tft2,task,FONT_B,10.8,color=BODY_DARK)
foot(s)

# ──────────────────────────────────────────────────── S19: CONCLUSION ────────
s = blank(prs); setbg(s,BG_WHITE)
header(s,"Conclusion & Future Roadmap","What We Built & Where We Go Next","Evidence-aware, risk-controlled, explainable multimodal dermatology AI")

card(s,Inches(0.55),Inches(1.72),Inches(5.85),Inches(5.45),TEAL_CARD,TEAL_BRIGHT)
b=tb(s,Inches(0.75),Inches(1.9),Inches(5.45),Inches(0.28)); tf=b.text_frame
tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
para(tf,"RESEARCH SUMMARY",FONT_B,12.5,bold=True,color=TEAL_DARK)

conc=[("LTT-Certified Safety:","89.1% coverage; 57.1% high-confidence missing 3.1% cancers. Bound holds."),
      ("Beats Both Baselines:","L2D rejector 4.9% (p=0.011); conf threshold 3.8% — both outperformed."),
      ("Backend Stable:","Policy 3.0-3.5% across 4 fusions; thresholding swings 3.5-9.3%."),
      ("Zero MEL Missed:","All 7 models: 100% recall on melanoma (10/10 test cases)."),
      ("Full Platform:","230 tests, FAISS RAG, 6 AI agents, 2-stage LLM verification, audit log."),
      ("IEEE Publication:","Complete paper with every table and figure reproducible from scripts.")]
for k,(lbl,val) in enumerate(conc):
    ty=Inches(2.3)+k*Inches(0.77)
    bx=tb(s,Inches(0.75),ty,Inches(5.45),Inches(0.72)); tf=bx.text_frame
    tf.word_wrap=True; tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
    para(tf,lbl,FONT_B,11.5,bold=True,color=HEAD_DARK)
    add(tf,val,FONT_B,11,color=BODY_DARK,sb=1)

card(s,Inches(6.65),Inches(1.72),Inches(6.15),Inches(5.45),TEAL_CARD,HEAD_DARK)
b2=tb(s,Inches(6.85),Inches(1.9),Inches(5.75),Inches(0.28)); tf2=b2.text_frame
tf2.margin_left=tf2.margin_right=tf2.margin_top=tf2.margin_bottom=0
para(tf2,"FUTURE CLINICAL TRANSLATION",FONT_B,12.5,bold=True,color=TEAL_DARK)

fut=[("Foundation Backbone:","Integrate PanDerm / DermLIP-PanDerm to lift every specialist representation."),
     ("Skin-Tone Fairness:","Group-conditional Mondrian conformal across Fitzpatrick I-VI skin tones."),
     ("Prospective Trial:","Multi-reader multi-case (MRMC) reader study with dermatologists."),
     ("EHR Integration:","HL7 FHIR connector for automated clinician queue from hospital EMR."),
     ("Active Learning:","Query-by-committee to label the most uncertain new cases efficiently."),
     ("Mobile Deployment:","Lightweight on-device specialist for community health settings.")]
for k,(lbl,val) in enumerate(fut):
    ty=Inches(2.3)+k*Inches(0.77)
    bx=tb(s,Inches(6.85),ty,Inches(5.75),Inches(0.72)); tf=bx.text_frame
    tf.word_wrap=True; tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
    para(tf,lbl,FONT_B,11.5,bold=True,color=HEAD_DARK)
    add(tf,val,FONT_B,11,color=BODY_DARK,sb=1)
foot(s)

# ──────────────────────────────────────────────────── S20: THANK YOU ─────────
s = blank(prs); setbg(s,BG_DARK)
rect(s,Inches(0),Inches(4.9),W,Inches(2.6),BG_DARKER)
rect(s,Inches(0.55),Inches(6.72),Inches(5.5),Inches(0.42),TEAL_BRIGHT)
b=tb(s,Inches(0.65),Inches(6.72),Inches(5.3),Inches(0.42)); tf=b.text_frame
tf.margin_top=tf.margin_bottom=Pt(2)
para(tf,"DERMA-GUARD  |  FINAL REVIEW  |  VIT CHENNAI",FONT_B,10,bold=True,color=BG_DARKER)

rect(s,Inches(0.55),Inches(0.9),Inches(0.06),Inches(2.4),TEAL_BRIGHT)
b2=tb(s,Inches(0.8),Inches(0.9),Inches(11.5),Inches(1.4)); tf2=b2.text_frame
tf2.margin_left=tf2.margin_right=tf2.margin_top=tf2.margin_bottom=0
para(tf2,"THANK YOU",FONT_H,54,bold=True,color=WHITE)

b3=tb(s,Inches(0.8),Inches(2.25),Inches(11.5),Inches(0.5)); tf3=b3.text_frame
tf3.word_wrap=True; tf3.margin_left=tf3.margin_right=tf3.margin_top=tf3.margin_bottom=0
para(tf3,"Questions & Open Discussion",FONT_H,24,bold=False,color=TEAL_BRIGHT)

rect(s,Inches(0.8),Inches(3.0),Inches(5.0),Inches(0.05),TEAL_BRIGHT)

b4=tb(s,Inches(0.8),Inches(3.2),Inches(11.5),Inches(0.35)); tf4=b4.text_frame
tf4.word_wrap=True; tf4.margin_left=tf4.margin_right=tf4.margin_top=tf4.margin_bottom=0
para(tf4,"Evidence-Aware Specialist Consensus with Risk-Controlled Evidence Acquisition and Deferral for Multimodal Dermatology",FONT_B,13.5,color=TEAL_SOFT)

# Presented By
b5=tb(s,Inches(0.8),Inches(4.80),Inches(11.5),Inches(0.75)); tf5=b5.text_frame
tf5.word_wrap=True; tf5.margin_left=tf5.margin_right=tf5.margin_top=tf5.margin_bottom=0
p1=tf5.paragraphs[0]
r1=p1.add_run(); r1.text="Presented By"; r1.font.name=FONT_B; r1.font.size=Pt(11); r1.font.bold=True; r1.font.color.rgb=TEAL_BRIGHT
p2=tf5.add_paragraph(); p2.space_before=Pt(3)
r2=p2.add_run(); r2.text="Aarav Prawin (23BDS1116)   |   Patel Kavya Vipulkumar (23BDS1076)   |   Rachit Agarwal (23BCE1577)"
r2.font.name=FONT_B; r2.font.size=Pt(13.5); r2.font.bold=False; r2.font.color.rgb=WHITE

# Project Guide (Exact same style & same color)
b6=tb(s,Inches(0.8),Inches(5.72),Inches(11.5),Inches(0.75)); tf6=b6.text_frame
tf6.word_wrap=True; tf6.margin_left=tf6.margin_right=tf6.margin_top=tf6.margin_bottom=0
p3=tf6.paragraphs[0]
r3=p3.add_run(); r3.text="Project Guide"; r3.font.name=FONT_B; r3.font.size=Pt(11); r3.font.bold=True; r3.font.color.rgb=TEAL_BRIGHT
p4=tf6.add_paragraph(); p4.space_before=Pt(3)
r4=p4.add_run(); r4.text="Dr. Sindhu Ravindran"; r4.font.name=FONT_B; r4.font.size=Pt(13.5); r4.font.bold=True; r4.font.color.rgb=WHITE
r5=p4.add_run(); r5.text="   |   School of Computer Science and Engineering (SCOPE), VIT Chennai"
r5.font.name=FONT_B; r5.font.size=Pt(13.5); r5.font.bold=False; r5.font.color.rgb=WHITE

# ── SAVE ────────────────────────────────────────────────────────────────────
out = r"d:\VIT BOOKS\PROJECT 1\Healthsphere_1\outputs\DERMA_GUARD_Review3_Final.pptx"
prs.save(out)
print(f"Saved: {out}")
print(f"Total slides: {len(prs.slides)}")
