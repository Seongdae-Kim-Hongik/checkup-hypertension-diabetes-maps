#  판정 「고혈압·당뇨병 질환의심」(N103 00401 실인원·00402 고혈압·00403 당뇨병)을 공표 측정 분포와 대조.
#  고혈압 의심 기준: 수축기 ≥140 또는 이완기 ≥90(유질환자=진단·약물치료 문진 자기보고는 별도 판정). 분포 표 N062·N063(수축기), N060·N061(이완기).
#  당뇨병 의심 기준: 공복혈당 ≥126 mg/dL. 분포 표 N068(시도)·N069(연령).
#  측정 분포는 유질환자 포함 → 비(판정/측정 기준 이상)는 1 미만이 정상. 점검 대상 = 비의 연도 계단·시도 간 상관.
#  산출 04_분석/UNDX/results_gate/S0_judgement_national.csv, S0_judgement_province.csv. 키 ~/.kosis_key(내용 출력 금지).
import os, json, csv, math, statistics as st, urllib.request, urllib.parse, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); A = os.path.join(ROOT, "04_분석", "UNDX"); RAW = os.path.join(A, "judgement_gate_261119"); RS = os.path.join(A, "results_gate")
SRC = os.path.join(ROOT, "00_원천", "C_NHIS_검진보험")
def fetch(t):
    p = os.path.join(RAW, t + ".json")
    if os.path.exists(p): return json.load(open(p))
    K = open(os.path.expanduser("~/.kosis_key")).read().strip(); out = []
    for y in range(2011, 2025):
        u = "https://kosis.kr/openapi/Param/statisticsParameterData.do?" + urllib.parse.urlencode(dict(method="getList", apiKey=K, orgId="350", tblId=t, itmId="ALL", objL1="ALL", objL2="ALL", objL3="ALL", format="json", jsonVD="Y", prdSe="Y", startPrdDe=str(y), endPrdDe=str(y)))
        d = json.loads(urllib.request.urlopen(u, timeout=90).read().decode()); out += d if isinstance(d, list) else []
    json.dump(out, open(p, "w"), ensure_ascii=False); return out
num = lambda x: float(str(x).replace(",", "")) if x not in ("", "-", None) else None
SBP140 = ["140-149mmHg", "150-159mmHg", "160-169mmHg", "170-179mmHg", "180mmHg 이상"]; DBP90 = ["90-99mmHg", "100-109mmHg", "110-119mmHg", "120mmHg 이상"]
FBG126 = ["126-139mg/dL", "140-159mg/dL", "160-179mg/dL", "180-199mg/dL", "200mg/dL 이상"]
SX = {"남자": "M", "여자": "F", "합계": "T", "계": "T"}
def tab(t, ok):
    H = collections.defaultdict(float)
    for r in fetch(t):
        v = num(r["DT"])
        if v is None or not ok(r): continue
        H[(int(r["PRD_DE"]), r["C1_NM"], SX.get(r["C2_NM"], r["C2_NM"]), r["C3_NM"])] += v
    return H
def ssum(H, k, bins): return sum(H.get(k + (b,), 0) for b in bins)
N103 = [r for r in csv.DictReader(open(os.path.join(SRC, "DT_35007_N103.csv"), encoding="utf-8-sig"))]
codes = sorted(set((r["C3"], r["C3_NM"]) for r in N103)); print("N103 codes", codes)
J = collections.defaultdict(float)
for r in N103:
    v = num(r["DT"])
    if v is None or r["C3"] not in ("00401", "00402", "00403"): continue
    J[(int(r["PRD_DE"]), r["C1_NM"], SX[r["C2_NM"]], r["C3"])] = v
# 전국: 연령별 표 '계'
s63 = tab("DT_35007_N063", lambda r: r["C1_NM"] == "계"); d61 = tab("DT_35007_N061", lambda r: r["C1_NM"] == "계"); g69 = tab("DT_35007_N069", lambda r: r["C1_NM"] == "계")
nat = []
for y in range(2011, 2025):
    for sx in ("M", "F", "T"):
        k = (y, "계", sx); n_bp = s63.get(k + ("계",), 0); n_g = g69.get(k + ("계",), 0)
        sb = ssum(s63, k, SBP140); db = ssum(d61, k, DBP90); gb = ssum(g69, k, FBG126)
        jh, jd, ju = J.get((y, "계", sx, "00402")), J.get((y, "계", sx, "00403")), J.get((y, "계", sx, "00401"))
        nat.append(dict(year=y, sex=sx, bp_measured=int(n_bp), sbp140=int(sb), dbp90=int(db), pct_sbp140=round(100*sb/n_bp, 2) if n_bp else None,
                        pct_dbp90=round(100*db/n_bp, 2) if n_bp else None, fbg_measured=int(n_g), fbg126=int(gb), pct_fbg126=round(100*gb/n_g, 2) if n_g else None,
                        flag_htn=jh, flag_dm=jd, flag_any=ju, ratio_htn_vs_sbp140=round(jh/sb, 3) if jh and sb else None,
                        ratio_htn_vs_maxbp=round(jh/max(sb, db), 3) if jh and sb else None, ratio_dm_vs_fbg126=round(jd/gb, 3) if jd and gb else None))
# 시도
SH = {"강원특별자치도": "강원", "강원도": "강원", "경기도": "경기", "경상남도": "경남", "경상북도": "경북", "광주광역시": "광주", "대구광역시": "대구", "대전광역시": "대전", "부산광역시": "부산", "서울특별시": "서울",
      "울산광역시": "울산", "인천광역시": "인천", "전라남도": "전남", "전라북도": "전북", "전북특별자치도": "전북", "제주특별자치도": "제주", "제주도": "제주", "충청남도": "충남", "충청북도": "충북", "세종특별자치시": "세종"}
def prov_tab(t):
    H = collections.defaultdict(float)
    for r in fetch(t):
        v = num(r["DT"])
        if v is None or r["C1_NM"] not in SH: continue
        H[(int(r["PRD_DE"]), SH[r["C1_NM"]], SX.get(r["C2_NM"], r["C2_NM"]), r["C3_NM"])] += v
    return H
s62 = prov_tab("DT_35007_N062"); d60 = prov_tab("DT_35007_N060"); g68 = prov_tab("DT_35007_N068")
JP = collections.defaultdict(float)
for r in N103:
    v = num(r["DT"])
    if v is None or len(r["C1"]) != 12 or r["C1_NM"] == "계" or r["C3"] not in ("00402", "00403"): continue
    nm = r["C1_NM"]; sd = SH.get(nm) or (nm if nm in set(SH.values()) else None)
    if sd: JP[(int(r["PRD_DE"]), sd, SX[r["C2_NM"]], r["C3"])] = v
def cor(a, b):
    ma, mb = sum(a)/len(a), sum(b)/len(b); den = math.sqrt(sum((x-ma)**2 for x in a)*sum((y-mb)**2 for y in b)); return sum((x-ma)*(y-mb) for x, y in zip(a, b))/den if den else None
prov = []
for y in range(2011, 2025):
    rh, rd, fh, mh, fd, md = [], [], [], [], [], []
    for sd in sorted(set(SH.values())):
        k = (y, sd, "T")
        nb = s62.get(k + ("계",), 0); ng = g68.get(k + ("계",), 0); jh = JP.get((y, sd, "T", "00402")); jd = JP.get((y, sd, "T", "00403"))
        if not (nb and ng and jh and jd): continue
        sb = ssum(s62, k, SBP140); gb = ssum(g68, k, FBG126)
        rh.append(jh/sb); rd.append(jd/gb); fh.append(100*jh/nb); mh.append(100*sb/nb); fd.append(100*jd/ng); md.append(100*gb/ng)
    if rh: prov.append(dict(year=y, n_prov=len(rh), htn_ratio_median=round(st.median(rh), 3), htn_ratio_cv=round(st.pstdev(rh)/st.mean(rh), 3), r_htnflag_vs_sbp140=round(cor(fh, mh), 3),
                            dm_ratio_median=round(st.median(rd), 3), dm_ratio_cv=round(st.pstdev(rd)/st.mean(rd), 3), r_dmflag_vs_fbg126=round(cor(fd, md), 3)))
os.makedirs(RS, exist_ok=True)
for f, rows in (("S0_judgement_national.csv", nat), ("S0_judgement_province.csv", prov)):
    w = csv.DictWriter(open(os.path.join(RS, f), "w", encoding="utf-8"), fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
print("national", len(nat), "province", len(prov))
