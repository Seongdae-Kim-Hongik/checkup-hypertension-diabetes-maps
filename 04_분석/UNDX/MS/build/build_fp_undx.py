# -*- coding: utf-8 -*-
# build_fp_undx.py — Family Practice 원고 빌더(2026-11-19, python-docx).
#  입력: draft/01_manuscript_fp.md, build/refs_undx.json, build/tables/Table1.csv·Table2.csv, results_gate/S0_judgement_national.csv.
#  Family Practice 규정: 원저 ≤3,000단어·표+그림 ≤5·참고 ≤40(AMA, 인용 순서), 초록 Background/Objective/Methods/Results/Conclusion, Key messages 3–6(각 <83자),
#   Discussion 안 Limitations·Conclusion 소제목, 제목·소제목·표 제목·그림 범례 약어 금지, 표는 참고문헌 뒤 각 쪽, 그림 범례 뒤 Alt text, Data availability 절, 선언(윤리·연구비·이해충돌)은 참고문헌 앞.
import os, re, json, csv
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
HERE = os.path.dirname(os.path.abspath(__file__)); MS = os.path.dirname(HERE); OUT = os.path.join(MS, "out_fp"); os.makedirs(OUT, exist_ok=True)
SRC = open(os.path.join(MS, "draft", "01_manuscript_fp.md"), encoding="utf-8").read(); SRC = re.sub(r"<!--.*?-->", "", SRC, flags=re.S)
REFS = json.load(open(os.path.join(HERE, "refs_undx.json"), encoding="utf-8"))
ZENODO_DOI = open(os.path.join(OUT, "zenodo_doi.txt")).read().strip() if os.path.exists(os.path.join(OUT, "zenodo_doi.txt")) else "10.5281/zenodo.XXXXXXX"
REPO = "https://github.com/Seongdae-Kim-Hongik/checkup-hypertension-diabetes-maps"
AUTHOR = "Seongdae Kim, PhD"
AFFIL = "Department of Biohealth Convergence Open Sharing System, Hongik University, Seoul, Republic of Korea"
ADDRESS = "Department of Biohealth Convergence Open Sharing System, Hongik University, 94 Wausan-ro, Mapo-gu, Seoul 04066, Republic of Korea"
PHONE = "+82-10-3059-3217"; EMAIL = "kimsd@hongik.ac.kr"; ORCID = "0000-0002-1525-0091"
KEYWORDS = "Hypertension; Diabetes Mellitus; Mass Screening; Undiagnosed Diseases; Spatial Analysis; Educational Status"
AI_STATEMENT = "The author used Claude (Anthropic) and ChatGPT (OpenAI) only for translation and English-language editing of the manuscript. The author reviewed and edited all output and takes full responsibility for the content of this publication."

def sec(title):
    m = re.search(r"(?m)^# " + re.escape(title) + r"\s*$", SRC); assert m, title
    n = re.search(r"(?m)^# ", SRC[m.end():]); return SRC[m.end(): m.end() + n.start()] if n else SRC[m.end():]
TITLE = sec("TITLE").strip()
# ── 인용 번호(첫 등장 순서, 괄호 번호) ──
ORDER = []
def _num(m):
    ks = [k.strip().lstrip("@") for k in m.group(1).split(";")]
    for k in ks:
        assert k in REFS, k
        if k not in ORDER: ORDER.append(k)
    ns = sorted(ORDER.index(k) + 1 for k in ks); out = []; i = 0
    while i < len(ns):
        j = i
        while j + 1 < len(ns) and ns[j + 1] == ns[j] + 1: j += 1
        out.append(f"{ns[i]}–{ns[j]}" if j - i >= 2 else (f"{ns[i]},{ns[j]}" if j == i + 1 else f"{ns[i]}")); i = j + 1
    return "\x02" + ",".join(out) + "\x03"
CITE = re.compile(r"\[(@[^\]]+)\]")
def cite(t):
    t = CITE.sub(_num, t); t = re.sub(r"\s+(\x02[^\x03]*\x03)", r"\1", t)
    return re.sub(r"(\x02[^\x03]*\x03)([.,;:])", r"\2\1", t)
# ── AMA 참고문헌 ──
KEEP = {"Korea", "Korean", "Koreans", "Norway", "US", "U.S.", "England", "China", "India", "Indians", "Bangladesh", "Russia", "Chicago's", "Chicago", "South", "Side", "NHS", "COVID-19", "KNHANES", "IDF", "Tromsø", "HELIUS",
        "ADDITION-Cambridge", "Bayesian", "Gaussian", "Laplace", "STROBE", "Study", "Global", "Burden", "Disease", "United", "States", "National", "Health", "Nutrition", "Examination", "Survey", "Surveys",
        "Insurance", "Service", "Program", "Screening", "COMPASS", "Alabama", "Birmingham", "Aging", "Community", "Atlas", "Preventive", "Services", "Task", "Force", "Recommendation", "Statement", "ChinaHEART", "SES", "Asian"}
def sentcase(t):
    w = t.split(" "); caps = sum(1 for x in w if x[:1].isupper()); 
    if caps < 0.6 * len(w): return t
    out = []; prev_colon = True
    for x in w:
        core = re.sub(r"[^A-Za-z]", "", x)
        if prev_colon or x.isupper() or core in KEEP or (len(core) > 1 and core[1:].lower() != core[1:]): out.append(x)
        else: out.append(x[:1].lower() + x[1:])
        prev_colon = x.endswith(":") or x.endswith("?")
    return " ".join(out)
TFIX = {"lee2021risk": "Risk factors of undiagnosed diabetes mellitus among Korean adults: a national cross-sectional study using the KNHANES data",
        "park2019determinants": "The determinants of and barriers to awareness and treatment of hypertension in the Korean population",
        "hodges2010adding": "Adding spatially-correlated errors can mess up the fixed effect you love",
        "lee2017socioeconomic": "Socioeconomic disparities in the prevalence, diagnosis, and control of hypertension in the context of a universal health insurance system",
        "oh2026validation": "Validation of self-reported disease history in Korea: a National Health Insurance cohort study",
        "ogurtsova2022idf": "IDF Diabetes Atlas: global estimates of undiagnosed diabetes in adults for 2021",
        "ruiz2021undiagnosed": "Undiagnosed diabetes based on HbA1c by socioeconomic status and healthcare consumption in the Tromsø Study 1994-2016"}
def ama(r, key=None):
    if r["type"] == "web":
        return f"{r['authors']}. {r['title']}. Published {r['year']}. Accessed {r['accessed']}. {r['url']}"
    au = r["authors"]; a = ", ".join(au) if len(au) <= 6 else ", ".join(au[:3]) + ", et al"
    t = TFIX.get(key) or sentcase(r["title"].rstrip("."))
    vol = r.get("vol", ""); iss = r.get("issue", ""); pg = r.get("pages", "")
    loc = f"{r['year']}" + (f";{vol}" if vol else "") + (f"({iss})" if iss else "") + (f":{pg}" if pg else "")
    doi = f" doi:{r['doi']}" if r.get("doi") else ""
    return f"{a}. {t}. {r['journal']}. {loc}.{doi}"

TFIX["dwyerlindgren2016diagnosed"] = "Diagnosed and undiagnosed diabetes prevalence by county in the U.S., 1999-2012"
REFS["web:kosis2026screening"] = dict(REFS["web:kosis2026screening"], title="National health screening statistics: general health screening results by district and sex (DT_35007_N098, DT_35007_N103), by sex and age group (DT_35007_N099, DT_35007_N104), and distributions of systolic and diastolic blood pressure and fasting glucose by province and age group (DT_35007_N060 to N063, N068, N069), 2011-2024. Korean Statistical Information Service", accessed="November 19, 2026")

D = Document(); st = D.styles["Normal"]; st.font.name = "Times New Roman"; st.font.size = Pt(12)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
st.paragraph_format.line_spacing = 2.0; st.paragraph_format.space_after = Pt(0); st.paragraph_format.space_before = Pt(0)
s0 = D.sections[0]; s0.page_width = Inches(8.27); s0.page_height = Inches(11.69)
for a in ("left_margin", "right_margin", "top_margin", "bottom_margin"): setattr(s0, a, Inches(1))
D.core_properties.author = "Seongdae Kim"; D.core_properties.title = TITLE; D.core_properties.comments = ""; D.core_properties.last_modified_by = "Seongdae Kim"
def fld(r, code):
    for t, v in (("begin", None), (None, code), ("end", None)):
        if t: e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), t)
        else: e = OxmlElement("w:instrText"); e.set(qn("xml:space"), "preserve"); e.text = v
        r._r.append(e)
p = s0.header.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.RIGHT; fld(p.add_run(), "PAGE")
# 줄번호(연속)
ln = OxmlElement("w:lnNumType"); ln.set(qn("w:countBy"), "1"); ln.set(qn("w:restart"), "continuous"); s0._sectPr.append(ln)
def para(text, bold_lead=None, align=None, italic=False, size=None):
    p = D.add_paragraph()
    if align is not None: p.alignment = align
    if bold_lead: rr = p.add_run(bold_lead); rr.bold = True
    for part in re.split(r"(\*[^*]+\*|\x02[^\x03]*\x03)", text):
        if not part: continue
        if part.startswith("\x02"):
            rr = p.add_run(part[1:-1]); rr.font.superscript = True
            if size: rr.font.size = Pt(size)
            continue
        it = part.startswith("*") and part.endswith("*")
        rr = p.add_run(part[1:-1] if it else part); rr.italic = italic or it
        if size: rr.font.size = Pt(size)
    return p
def head(t, lvl=1):
    p = D.add_paragraph(); r = p.add_run(t); r.bold = (lvl == 1); r.italic = (lvl == 2)
    p.paragraph_format.keep_with_next = True; return p
def body_paras(txt): return [x.strip() for x in re.split(r"\n\s*\n", txt.strip()) if x.strip() and not x.strip().startswith("## ")]
def subsections(txt):
    parts = re.split(r"(?m)^## (.+)$", txt); out = [(None, parts[0])]
    for i in range(1, len(parts), 2): out.append((parts[i].strip(), parts[i + 1]))
    return out
def words(t): return len(re.sub(CITE, "", t).split())
ABS = sec("ABSTRACT"); ABS_W = sum(words(b) for _, b in subsections(ABS)[1:])
BODY_TXT = "".join(sec(s) for s in ("INTRODUCTION", "METHODS", "RESULTS", "DISCUSSION")); BODY_W = words(re.sub(r"(?m)^## .*$", "", BODY_TXT))
KM = [x[2:].strip() for x in sec("KEY MESSAGES").strip().splitlines() if x.startswith("- ")]
assert 3 <= len(KM) <= 6 and all(len(k) < 83 for k in KM), [(k, len(k)) for k in KM]
LAY = " ".join(body_paras(sec("LAY SUMMARY"))); LAY_W = len(LAY.split()); assert LAY_W <= 200, LAY_W
assert BODY_W <= 3000, BODY_W
# ── 제목면 ──
para(TITLE, align=WD_ALIGN_PARAGRAPH.CENTER).runs[0].bold = True
para(sec("RUNNING HEAD").strip(), bold_lead="Running head: ")
para("Epidemiology (Original research)", bold_lead="Article category: ")
para("Seongdae Kim¹", align=WD_ALIGN_PARAGRAPH.CENTER)
para("¹" + AFFIL)
para(f"Dr. S. Kim, {ADDRESS}. Email: {EMAIL}. Telephone: {PHONE}. ORCID: {ORCID}", bold_lead="Correspondence: ")
para(f"Abstract, {ABS_W} words; main text, {BODY_W} words; references, {len(REFS)}; tables, 2; figures, 2.", bold_lead="Word counts: ")
D.add_page_break()
head("Key messages")
for k in KM:
    p = D.add_paragraph(style="List Bullet"); p.add_run(k)
head("Abstract")
for h, b in subsections(ABS)[1:]: para(cite(" ".join(body_paras(b))), bold_lead=f"{h}: ")
para(KEYWORDS, bold_lead="Keywords: ")
D.add_page_break(); head("Lay summary"); para(LAY)
D.add_page_break()
for S, H in (("INTRODUCTION", "Introduction"), ("METHODS", "Methods"), ("RESULTS", "Results"), ("DISCUSSION", "Discussion")):
    head(H)
    for sub, txt in subsections(sec(S)):
        if sub: head(sub, 2)
        for b in body_paras(txt): para(cite(b))
# ── 선언(참고문헌 앞) ──
head("Declarations")
para("The Institutional Review Board of Hongik University approved this study on November 4, 2025 (approval no. 7002340-202511-HR-012; continuing review 7002340-202611-HR-040) and waived informed consent because only published aggregate statistics were used.", bold_lead="Ethical approval: ")
para("This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors.", bold_lead="Funding: ")
para("The author declares no conflict of interest.", bold_lead="Conflict of interest: ")
para("The author used Claude (Anthropic) and ChatGPT (OpenAI) only for translation and English-language editing of the manuscript. The author reviewed and edited all output and takes full responsibility for the content of this publication.", bold_lead="Use of artificial intelligence: ")
head("Data availability")
para(f"The data are publicly available district statistics from the Korean Statistical Information Service (https://kosis.kr) and the Korea Community Health Survey. The analysis code is available at {REPO} and archived at https://doi.org/{ZENODO_DOI}.")
# ── 참고문헌 ──
D.add_page_break(); head("References")
assert len(ORDER) == len(REFS) <= 40, (len(ORDER), len(REFS))
for i, k in enumerate(ORDER, 1):
    p = para(f"{i}. " + ama(REFS[k], k)); p.paragraph_format.left_indent = Inches(0.3); p.paragraph_format.first_line_indent = Inches(-0.3)
# ── 표 ──
TABLES = [
 ("Table 1. Examinees and those not under treatment with suspected hypertension or diabetes, National General Health Screening, 228 districts of South Korea, 2011, 2017, 2018, and 2024", "Table1.csv",
  ["a Each examinee with suspected hypertension or diabetes is counted once; an examinee with both conditions is counted in each condition column.",
   "b Proportion of examinees with suspected hypertension or diabetes in each district. Percentages in the count columns use all examinees with a screening judgment as denominator; counts are sums over 228 districts and differ from the national measurement totals in Supplementary Table S1.", "c Share of residents with tertiary education from the population census, interpolated between census years and carried forward after 2020."]),
 ("Table 2. Rate ratios per 1 standard deviation of 12 district characteristics for suspected hypertension or diabetes in 200,907,394 examinations, National General Health Screening, 228 districts of South Korea, 2011–2024", "Table2.csv",
  ["a Expected direction, set before covariate models were fitted: − fewer suspected cases, + more suspected cases.",
   "b Bayesian negative binomial model with BYM2 spatial effect, random walk and independent year effects, the 12 characteristics, and 5 forced controls (urban population share, physicians, sex ratio, fiscal autonomy, and share aged 80 years or older); values are rate ratio (95% credible interval), judged on unrounded limits.",
   "c Percentage of models in which the 95% credible interval excluded 1, among the 200 models with random subsets of 6 characteristics that included the characteristic (86–113 models each).", "d Knorr-Held type IV space–time interaction model allowing district-specific trends.",
   "e Same model fitted to suspected hypertension or suspected diabetes alone."])]
HDRFIX = {"District proportion, median (IQR), %": "District proportion, median (interquartile range), %", "Tertiary education, median (IQR), %": "Tertiary education, median (interquartile range), %",
          "Specs, %": "Subsets credible, %", "Characteristic (per 1 SD)": "Characteristic (per 1 standard deviation)"}
SUPA = {"Table1.csv": {"Suspected hypertension or diabetes, n (%)": "a", "District proportion, median (interquartile range), %": "b", "Tertiary education, median (interquartile range), %": "c"},
        "Table2.csv": {"Sign": "a", "Main model": "b", "Subsets credible, %": "c", "Knorr-Held IV": "d", "Hypertension": "e", "Diabetes": "e"}}
def cellfmt(c, text, bold=False, sup=None):
    c.text = ""; p = c.paragraphs[0]; p.paragraph_format.line_spacing = 1.0; r = p.add_run(text); r.font.size = Pt(9); r.bold = bold
    if sup: s = p.add_run(sup); s.font.size = Pt(9); s.font.superscript = True; s.bold = bold
def three_line(T):
    tblPr = T._tbl.tblPr; b = OxmlElement("w:tblBorders")
    for edge, val in (("top", "single"), ("bottom", "single"), ("left", "nil"), ("right", "nil"), ("insideH", "nil"), ("insideV", "nil")):
        e = OxmlElement(f"w:{edge}"); e.set(qn("w:val"), val)
        if val == "single": e.set(qn("w:sz"), "8"); e.set(qn("w:color"), "000000")
        b.append(e)
    tblPr.append(b)
    for c in T.rows[0].cells:
        tcPr = c._tc.get_or_add_tcPr(); bb = OxmlElement("w:tcBorders"); e = OxmlElement("w:bottom"); e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "6"); e.set(qn("w:color"), "000000"); bb.append(e); tcPr.append(bb)
from docx.enum.section import WD_SECTION
def new_sec(landscape):
    sc = D.add_section(WD_SECTION.NEW_PAGE); sc.orientation = WD_ORIENT.LANDSCAPE if landscape else WD_ORIENT.PORTRAIT
    sc.page_width, sc.page_height = (Inches(11.69), Inches(8.27)) if landscape else (Inches(8.27), Inches(11.69)); return sc
for title, f, notes in TABLES:
    if f == "Table2.csv": new_sec(True)
    else: D.add_page_break()
    para(title).runs[0].bold = True
    rows = list(csv.reader(open(os.path.join(HERE, "tables", f), encoding="utf-8"))); rows[0] = [HDRFIX.get(v, v) for v in rows[0]]; rows = [[c.replace(" (log)", " (logarithm)") for c in r] for r in rows]
    T = D.add_table(rows=len(rows), cols=len(rows[0])); T.autofit = False
    WID = {"Table1.csv": [0.45, 0.85, 1.0, 1.0, 0.85, 1.0, 1.1], "Table2.csv": [1.05, 0.38, 0.66, 0.55, 0.66, 0.66, 0.66, 0.66, 0.0]}[f]
    if f == "Table2.csv": WID = [1.45, 0.45, 1.19, 0.65, 1.19, 1.19, 1.19, 1.19, 1.19]
    for j, w in enumerate(WID):
        for c in T.columns[j].cells: c.width = Inches(w)
    for gc, w in zip(T._tbl.tblGrid.findall(qn("w:gridCol")), WID): gc.set(qn("w:w"), str(int(w * 1440)))
    _lay = OxmlElement("w:tblLayout"); _lay.set(qn("w:type"), "fixed"); T._tbl.tblPr.append(_lay)
    for i, row in enumerate(rows):
        for j, v in enumerate(row): cellfmt(T.cell(i, j), v, bold=(i == 0), sup=SUPA[f].get(v) if i == 0 else None)
    three_line(T)
    for n in notes:
        p = D.add_paragraph(); p.paragraph_format.line_spacing = 1.0; s = p.add_run(n[0]); s.font.superscript = True; s.font.size = Pt(9); r = p.add_run(n[1:]); r.font.size = Pt(9)
# ── 그림 범례 + Alt text ──
FIGS = [("Figure 1. Residual spatial rate ratios and spatial autocorrelation of suspected hypertension or diabetes among examinees not under treatment, National General Health Screening, 228 districts of South Korea, 2011–2024.",
         "Residual spatial rate ratios from the main model on a common color scale for suspected hypertension or diabetes (A), suspected hypertension (B), and suspected diabetes (C), with hot and cold spots outlined, and yearly Moran's I of observed log standardized ratios (D).",
         "Three maps of South Korean districts and a line graph. For the combined outcome and hypertension, ratios are higher in the northwest, center, and northeast and lower in the southeast and southwest. For diabetes, high ratios are scattered, with a cluster in the southwest. The line graph shows Moran's I rising after 2017 for the combined outcome and hypertension and flat for diabetes."),
        ("Figure 2. Rate ratios per 1 standard deviation for 12 district characteristics and for tertiary education across analyses, National General Health Screening, 228 districts of South Korea, 2011–2024.",
         "Main-model rate ratios with 95% credible intervals for 12 district characteristics (A) and the tertiary education rate ratio across alternative models, periods, components, and outcomes (B). Filled markers indicate intervals excluding 1.",
         "Two dot-and-whisker plots. Panel A shows that tertiary education has the lowest rate ratio, well below 1, and other characteristics lie close to 1. Panel B shows the tertiary education rate ratio between 0.93 and 0.97, below 1, in all 12 analyses shown.")]
new_sec(False); head("Figure legends")
for t, cap, alt in FIGS:
    para(t).runs[0].bold = True; para(cap); para(alt, bold_lead="Alt text: ")
fp = os.path.join(OUT, "Manuscript_FP.docx"); D.save(fp)
json.dump(dict(abstract=ABS_W, body=BODY_W, lay=LAY_W, key_messages=[len(k) for k in KM], refs=len(ORDER), order=ORDER), open(os.path.join(OUT, "wordcount_fp.json"), "w"), indent=1)
print(f"[build] {fp}: abstract {ABS_W}, body {BODY_W}, lay {LAY_W}, KM {[len(k) for k in KM]}, refs {len(ORDER)}")
# ── 보충 표 S1(판정 구성 대조) ──
G = list(csv.DictReader(open(os.path.join(os.path.dirname(MS), "results_gate", "S0_judgement_national.csv"), encoding="utf-8")))
G = [g for g in G if g["sex"] == "T"]
S = Document(); ss = S.styles["Normal"]; ss.font.name = "Times New Roman"; ss.font.size = Pt(11); ss.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
S.core_properties.author = "Seongdae Kim"; S.core_properties.title = "Supplementary data"; S.core_properties.comments = ""
p = S.add_paragraph(); r = p.add_run("Supplementary data"); r.bold = True
p = S.add_paragraph(); r = p.add_run(TITLE); r.italic = True
p = S.add_paragraph(); r = p.add_run("Supplementary Table S1. Suspected hypertension and suspected diabetes among examinees not under treatment compared with measured blood pressure and fasting glucose among all examinees, National General Health Screening, South Korea, 2011–2024"); r.bold = True
from decimal import Decimal, ROUND_HALF_UP
pc = lambda a, b, nd="0.1": str(Decimal(str(100 * float(a) / float(b))).quantize(Decimal(nd), rounding=ROUND_HALF_UP))
rt = lambda a, b: str(Decimal(str(float(a) / float(b))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
PV = {int(r["year"]): r for r in csv.DictReader(open(os.path.join(os.path.dirname(MS), "results_gate", "S0_judgement_province.csv"), encoding="utf-8"))}
hdr = ["Year", "Blood pressure measured, n", "Systolic ≥140 mm Hg, %", "Diastolic ≥90 mm Hg, %", "Suspected hypertension, n", "Ratio to systolic ≥140 mm Hg", "Provincial median ratio", "Fasting glucose measured, n", "Fasting glucose ≥126 mg/dL, %", "Suspected diabetes, n", "Ratio to glucose ≥126 mg/dL"]
sec_ = S.sections[0]; sec_.orientation = WD_ORIENT.LANDSCAPE; sec_.page_width, sec_.page_height = Inches(11.69), Inches(8.27)
for a_ in ("left_margin", "right_margin"): setattr(sec_, a_, Inches(0.8))
T = S.add_table(rows=1 + len(G), cols=len(hdr)); T.autofit = False
WS = [0.45, 1.0, 0.75, 0.75, 1.0, 0.85, 0.85, 1.0, 0.85, 0.95, 0.85]
for j_, w in enumerate(WS):
    for c in T.columns[j_].cells: c.width = Inches(w)
for gc, w in zip(T._tbl.tblGrid.findall(qn("w:gridCol")), WS): gc.set(qn("w:w"), str(int(w * 1440)))
_l = OxmlElement("w:tblLayout"); _l.set(qn("w:type"), "fixed"); T._tbl.tblPr.append(_l)
for j_, h in enumerate(hdr): cellfmt(T.cell(0, j_), h, bold=True)
fmt = lambda x: f"{int(float(x)):,}"
for i_, g in enumerate(G, 1):
    y = int(g["year"])
    vals = [g["year"], fmt(g["bp_measured"]), pc(g["sbp140"], g["bp_measured"]), pc(g["dbp90"], g["bp_measured"]), fmt(g["flag_htn"]), rt(g["flag_htn"], g["sbp140"]),
            f"{float(PV[y]['htn_ratio_median']):.2f}", fmt(g["fbg_measured"]), pc(g["fbg126"], g["fbg_measured"]), fmt(g["flag_dm"]), rt(g["flag_dm"], g["fbg126"])]
    for j_, v in enumerate(vals): cellfmt(T.cell(i_, j_), v)
three_line(T)
p = S.add_paragraph("Sources: Korean Statistical Information Service tables DT_35007_N061, N063, and N069 (national totals of all examinees with each measurement) and N103 (suspected cases, national total); provincial median ratio from N062 and N103 for 17 provinces. Measured distributions include examinees already under treatment, who are classified separately, and the joint distribution of systolic and diastolic pressure is not published, so the ratios are descriptive checks rather than sensitivity estimates. Measurement totals cover all examinees nationally and differ from the examinees with a screening judgment summed over 228 districts in Table 1. Pearson correlations between provincial suspected and measured rates were 0.53–0.73 for hypertension and 0.80–0.96 for diabetes. The step in the hypertension ratio between 2017 and 2018 coincided with the 2018 revision of the screening program.")
for r in p.runs: r.font.size = Pt(9)
sp = os.path.join(OUT, "Supplementary_Data_FP.docx"); S.save(sp); print("[supp]", sp)
