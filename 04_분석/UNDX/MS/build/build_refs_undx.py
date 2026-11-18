#  키 = 원고 원천(draft md + content_mets.py)의 [@key]. manifest(ALL_refs.csv) PMID → PubMed esummary, 없으면 DOI → Crossref. 웹 문헌은 WEB 사전.
import os, re, json, time, urllib.request, urllib.parse, glob
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); MS = os.path.dirname(HERE)
man = pd.read_csv(os.path.join(MS, "refs", "manifest", "ALL_refs.csv"), dtype=str).fillna("")
man["pmid"] = man.pmid.str.replace(r"\.0$", "", regex=True); M = man.set_index("key")
src = open(os.path.join(MS, "draft", "01_manuscript_fp.md"), encoding="utf-8").read()
src = re.sub(r"<!--.*?-->", "", src, flags=re.S); src = re.sub(r"(?m)^\s*#.*$", "", src)
keys = sorted({k.strip().lstrip("@") for g in re.findall(r"\[(@[^\]]+)\]", src) for k in g.split(";")})
keys = [k for k in keys if re.fullmatch(r"(web:)?[a-z][a-z0-9]*", k)]
WEB = {
 "web:kosis2026screening": dict(type="web", authors="National Health Insurance Service", title="National health screening statistics: general health screening results by district and sex (DT_35007_N098, DT_35007_N103) and by sex and age group (DT_35007_N099, DT_35007_N104), 2011-2024. Korean Statistical Information Service", url="https://kosis.kr", year=2026, accessed="November 10, 2026"),
 "web:mois2026population": dict(type="web", authors="Ministry of the Interior and Safety", title="Resident registration population by district, sex, and 5-year age group, 2011-2024", url="https://jumin.mois.go.kr", year=2026, accessed="October 20, 2026"),
 "web:rcore2026": dict(type="web", authors="R Core Team", title="R: a language and environment for statistical computing. Version 4.6.0. Vienna: R Foundation for Statistical Computing", url="https://www.R-project.org/", year=2026, accessed="October 20, 2026"),
}
out = {}
miss = [k for k in keys if not k.startswith("web:") and k not in M.index]; assert not miss, miss
pm = [k for k in keys if not k.startswith("web:") and M.loc[k, "pmid"]]
for i in range(0, len(pm), 150):
    ids = ",".join(M.loc[k, "pmid"] for k in pm[i:i + 150])
    d = json.load(urllib.request.urlopen("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id=" + ids, timeout=60))["result"]
    for k in pm[i:i + 150]:
        r = d[M.loc[k, "pmid"]]
        au = [a["name"] for a in r["authors"] if a.get("authtype", "Author") == "Author"] or [a["name"] for a in r["authors"]]
        doi = next((a["value"] for a in r["articleids"] if a["idtype"] == "doi"), "") or M.loc[k, "doi"]
        pages = r.get("pages", "") or (r.get("elocationid", "").replace("pii: ", "").split(" doi")[0] if r.get("elocationid", "").startswith("pii:") else "")
        out[k] = dict(type="journal", authors=au, title=r["title"].rstrip("."), journal=r["source"], year=int(r["pubdate"][:4]), vol=r.get("volume", ""), issue=r.get("issue", ""), pages=pages, doi=doi, pmid=M.loc[k, "pmid"], verified="PubMed esummary " + time.strftime("%Y-%m-%d"))
    time.sleep(0.4)
JABBR = {"Political Science Research and Methods": "Polit Sci Res Methods", "Geographical Analysis": "Geogr Anal", "Econometrica": "Econometrica", "Statistical Science": "Stat Sci"}
for k in keys:
    if k.startswith("web:"): out[k] = WEB[k]; continue
    if k in out: continue
    doi = M.loc[k, "doi"]; assert doi, k
    m = json.load(urllib.request.urlopen(urllib.request.Request("https://api.crossref.org/works/" + urllib.parse.quote(doi), headers={"User-Agent": "research (kimsd@hongik.ac.kr)"}), timeout=60))["message"]
    au = [f"{a.get('family','')} {''.join(x[0] for x in re.split(r'[ -]', a.get('given','')) if x)}".strip() for a in m.get("author", [])]
    ct = (m.get("container-title") or [""])[0]; jt = JABBR.get(ct, (m.get("short-container-title") or [ct])[0])
    yr = (m.get("published-print") or m.get("published-online") or m.get("issued"))["date-parts"][0][0]
    out[k] = dict(type="journal", authors=au, title=re.sub(r"<[^>]+>", "", (m.get("title") or [""])[0]), journal=jt, year=int(yr), vol=m.get("volume", ""), issue=m.get("issue", ""), pages=m.get("page", "") or m.get("article-number", ""), doi=doi, verified="Crossref " + time.strftime("%Y-%m-%d"))
    time.sleep(0.3)
# 서식 통일: 학술지 MEDLINE 약어(마침표 없음), 쪽 범위 전체 표기, 대문자 제목 문장형
JN = {"Polit. Sci. Res. Methods": "Polit Sci Res Methods", "Geogr. Anal.": "Geogr Anal", "Stat. Sci.": "Stat Sci", "J R Stat Soc Series B Stat Methodol": "J R Stat Soc Series B Stat Methodol",
      "Journal of the Royal Statistical Society Series B: Statistical Methodology": "J R Stat Soc Series B Stat Methodol"}
def fullp(p):
    m = re.match(r"^(\d+)-(\d+)$", str(p))
    if not m: return p
    a, b = m.groups(); return p if len(b) >= len(a) else f"{a}-{a[:len(a)-len(b)]+b}"
FIXP = {"lee2021risk": "1195", "ruiz2021undiagnosed": "e002423", "namgung2019role": "3486", "jun2018gender": "311", "park2023maintained": "1811", "mann1945nonparametric": "245-259"}   # 전자 논문 번호(Crossref article-number 확인 필요 항목은 아래에서 assert)   # 전자 논문 번호(PubMed esummary pages 없음·마침표 붙음)
AHEAD = set()
for k, v in out.items():
    if v.get("type") != "journal": continue
    if k in FIXP: v["pages"] = FIXP[k]
    if k in AHEAD: v["pages"] = ""; v["vol"] = ""; v["ahead"] = True
    v["journal"] = JN.get(v["journal"], v["journal"]).replace(".", "")
    v["pages"] = fullp(v.get("pages", "")) if k not in AHEAD else ""
    if v["title"].isupper(): v["title"] = v["title"].capitalize()
    v["authors"] = [a.title() if a.isupper() else a for a in v["authors"]]
# 문장형 제목(제목형 대소문자 문헌만 직접 지정, 고유명사 유지)
SENT = {
 "blanc2019occupational": "The occupational burden of nonmalignant respiratory diseases. An official American Thoracic Society and European Respiratory Society statement",
 "choi2020regional": "Regional variation of suicide mortality in South Korea",
 "dwyerlindgren2017trends": "Trends and patterns of differences in chronic respiratory disease mortality among US counties, 1980-2014",
 "hwang2017recent": "Recent trends in the prevalence of chronic obstructive pulmonary disease in Korea",
 "kim2022trends": "Trends in regional disparity in cardiovascular mortality in Korea, 1983-2019",
 "lee2016risk": "The risk factors and characteristics of COPD among nonsmokers in Korea: an analysis of KNHANES IV and V",
 "raju2019rural": "Rural residence and poverty are independent risk factors for chronic obstructive pulmonary disease in the United States",
 "luo2026copd": "COPD burden across 48 Asian locations, 2009-2023: demographic drivers and socioeconomic inequality",
 "kim2017income": "Income differences in smoking prevalences in 245 districts of South Korea: patterns by area deprivation and urbanity, 2008-2014",
 "cheolseong2017data": "Data resource profile: the National Health Information Database of the National Health Insurance Service in South Korea",
 "steegen2016increasing": "Increasing transparency through a multiverse analysis",
 "vanderweele2017sensitivity": "Sensitivity analysis in observational research: introducing the E-value",
 "bell2015explaining": "Explaining fixed effects: random effects modeling of time-series cross-sectional and panel data",
 "rue2009approximate": "Approximate Bayesian inference for latent Gaussian models by using integrated nested Laplace approximations",
 "morgenstern1995ecologic": "Ecologic studies in epidemiology: concepts, principles, and methods",
 "inskip1983methods": "Methods for age-adjustment of rates",
 "knorrheld2000bayesian": "Bayesian modelling of inseparable space-time variation in disease risk",
 "dupont2022spatial": "Spatial+: a novel approach to spatial confounding",
 "lipsitch2010negative": "Negative controls: a tool for detecting confounding and bias in observational studies",
 "vonelm2007strengthening": "The Strengthening the Reporting of Observational Studies in Epidemiology (STROBE) statement: guidelines for reporting observational studies",
 "lederer2019control": "Control of confounding and reporting of results in causal inference studies. Guidance for authors from editors of respiratory, sleep, and critical care journals",
}
for k, t in SENT.items():
    if k in out: out[k]["title"] = t
SENT.update({
 "mottillo2010metabolic": "The metabolic syndrome and cardiovascular risk: a systematic review and meta-analysis",
 "namgung2019role": "The role of built environment on health of older adults in Korea: obesity and gender differences",
 "kang2022current": "Current status of the national health screening programs in South Korea",
 "jo2020leisure": "Leisure time physical activity to reduce metabolic syndrome risk: a 10-year community-based prospective study in Korea",
 "alberti2009harmonizing": "Harmonizing the metabolic syndrome: a joint interim statement of the International Diabetes Federation Task Force on Epidemiology and Prevention; National Heart, Lung, and Blood Institute; American Heart Association; World Heart Federation; International Atherosclerosis Society; and International Association for the Study of Obesity",
 "kang2015korea": "Korea Community Health Survey data profiles",
 "getis1992analysis": "The analysis of spatial association by use of distance statistics",
 "park2023maintained": "Does maintained medical aid coverage affect healthy lifestyle factors, metabolic syndrome-related health status, and individuals' use of healthcare services?",
 "palmaleal2025active": "Is active commuting associated with metabolic syndrome in adults, adolescents, and children? A systematic review and meta-analysis",
 "huh2018metabolic": "Metabolic syndrome epidemic among Korean adults: Korean Survey of Cardiometabolic Syndrome (2018)",
})
for k, t in SENT.items():
    if k in out: out[k]["title"] = t
for k, v in out.items():   # 콜론 뒤 첫 글자 소문자(고유명사·약어 제외)
    if v.get("type") == "journal":
        v["title"] = re.sub(r":\s+([A-Z][a-z]*)\b", lambda m: ": " + (m.group(1) if m.group(1) in ("Korea", "Korean", "South", "Bayesian", "Spatial", "E", "GLOBOCAN", "COPD", "Korean", "A") else m.group(1).lower()), v["title"])
AUTHOR_FIX = {"Cheol Seong S": "Seong SC", "Heon Park J": "Park JH", "Hyon Bang J": "Bang JH", "Ae Shin S": "Shin SA", "Won Yoon J": "Yoon JW"}   # lim2011increasing Yoon JW(문헌 에이전트 11/8)
for _k, _v in out.items():
    if isinstance(_v.get("authors"), list): _v["authors"] = [AUTHOR_FIX.get(a, a) for a in _v["authors"]]
assert not any("Cheol Seong" in a for v in out.values() if isinstance(v.get("authors"), list) for a in v["authors"])
json.dump(out, open(os.path.join(HERE, "refs_undx.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
import re as _re
for _k, _v in out.items():
    if isinstance(_v.get("authors"), list): assert not [a for a in _v["authors"] if a not in ("Tchetgen Tchetgen E", "Di Angelantonio E", "Van Dyck D", "De Bourdeaudhuij I") and _re.fullmatch(r"[A-Z][a-z]+ [A-Z][a-z]+ [A-Z]", a)], (_k, _v["authors"])
print(len(keys), "keys;", sum(v["type"] == "journal" for v in out.values()), "journal,", sum(v["type"] == "web" for v in out.values()), "web")
