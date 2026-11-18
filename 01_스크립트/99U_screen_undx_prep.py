#!/usr/bin/env python3
#  세 결과를 같은 규칙으로 판정: UNDX(고혈압·당뇨병 질환의심 실인원) · UNDXH(고혈압 의심) · UNDXD(당뇨병 의심). E_std는 99U2 산출(02_패널/UNDX_Estd3.csv).
import os, shutil, unicodedata
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); AN = os.path.join(ROOT, "04_분석"); PAN = os.path.join(ROOT, "02_패널")
NFC = lambda s: unicodedata.normalize("NFC", str(s))
X = pd.read_csv(os.path.join(PAN, "UNDX_Estd3.csv"), encoding="utf-8-sig"); X["fbd_region"] = X.fbd_region.map(NFC)
base = pd.read_csv(os.path.join(AN, "PERIO", "panel_PERIO.csv"), encoding="utf-8-sig"); base["fbd_region"] = base.fbd_region.map(NFC)
for T, suf in [("UNDX", ""), ("UNDXH", "_H"), ("UNDXD", "_D")]:
    D = os.path.join(AN, T); os.makedirs(os.path.join(D, "results"), exist_ok=True)
    P = base.drop(columns=["cases", "E", "SIR", "offset"]).merge(X[["year", "fbd_region", "examinees", "cases" + suf, "E_std" + suf]], on=["year", "fbd_region"], how="inner", validate="one_to_one")
    P = P.rename(columns={"cases" + suf: "cases", "examinees": "offset"})
    nat = P.groupby("year").cases.sum() / P.groupby("year").offset.sum(); P["E"] = P.offset * P.year.map(nat); P["SIR"] = P.cases / P.E
    P.drop(columns=["E_std" + suf]).to_csv(os.path.join(D, f"panel_{T}.csv"), index=False, encoding="utf-8-sig")
    P[["year", "fbd_region"]].assign(E_std=P["E_std" + suf]).to_csv(os.path.join(PAN, f"{T}_Estd.csv"), index=False, encoding="utf-8-sig")
    shutil.copy2(os.path.join(AN, "PERIO", "config_PERIO.json"), os.path.join(D, f"config_{T}.json"))
    shutil.copy2(os.path.join(AN, "METS_std", "results", "nb_METS_std.graph"), os.path.join(D, "results", f"nb_{T}.graph"))
    print(f"[99U-prep] {T}: 행 {len(P)}, 연도 {P.year.min()}-{P.year.max()}, cases {int(P.cases.sum()):,}")
