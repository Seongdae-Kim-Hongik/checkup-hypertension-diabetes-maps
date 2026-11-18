#!/usr/bin/env python3
#  ① DT_35007_N104 연령별 성별 일반건강검진 판정결과 질환의심 세부현황(분자: 고혈압당뇨병 질환의심 실인원·고혈압·당뇨병)
#  ② DT_35007_N099 연령별 성별 일반건강검진 판정 현황: 전체(분모: 수검자 계·판정 범주)
#  키: ~/.kosis_key(내용 출력 금지). 산출: 00_원천/C_NHIS_검진보험/<TBL>_national/<연도>.json, <TBL>_national_long.csv
#  사용: python3 99U_fetch_undx_age_sex.py [시작연도] [끝연도]   (기본 2011 2024)
import os, sys, json, time, urllib.request, urllib.parse
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "00_원천", "C_NHIS_검진보험")
Y0, Y1 = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (2011, 2024)
KEY = open(os.path.expanduser("~/.kosis_key")).read().strip()
URL = "https://kosis.kr/openapi/Param/statisticsParameterData.do?"
for TBL in ["DT_35007_N104", "DT_35007_N099"]:
    OUT = os.path.join(SRC, f"{TBL}_national"); os.makedirs(OUT, exist_ok=True); rows = []
    for y in range(Y0, Y1 + 1):
        f = os.path.join(OUT, f"{y}.json")
        if not os.path.exists(f):
            q = dict(method="getList", apiKey=KEY, itmId="ALL", objL1="ALL", objL2="ALL", objL3="ALL", format="json", jsonVD="Y",
                     prdSe="Y", startPrdDe=str(y), endPrdDe=str(y), orgId="350", tblId=TBL)
            d = json.loads(urllib.request.urlopen(URL + urllib.parse.urlencode(q), timeout=300).read().decode("utf-8"))
            if isinstance(d, dict): raise SystemExit(f"[99U-f] {TBL} {y} 오류 응답: {d}")
            json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False); time.sleep(1)
        d = json.load(open(f, encoding="utf-8"))
        for r in d:
            rows.append(dict(year=int(r["PRD_DE"]), age_code=r["C1"], age=r["C1_NM"], sex=r["C2_NM"], grp_code=r.get("C3"), grp=r.get("C3_NM"),
                             item=r["ITM_NM"], value=pd.to_numeric(r["DT"], errors="coerce")))
        print(f"[99U-f] {TBL} {y}: {len(d):,}행")
    L = pd.DataFrame(rows); L.to_csv(os.path.join(SRC, f"{TBL}_national_long.csv"), index=False, encoding="utf-8-sig")
    print(TBL, L.grp.unique().tolist(), L.item.unique().tolist())
