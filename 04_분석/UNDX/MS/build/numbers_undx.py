# -*- coding: utf-8 -*-
import os, json, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); AN = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
PAN = os.path.join(os.path.dirname(AN), "02_패널")
rd = lambda T, f: pd.read_csv(os.path.join(AN, T, "results_std3", f), encoding="utf-8-sig", dtype={"sigungu_cd": str})
REG = {'서울시':'Capital','인천시':'Capital','경기도':'Capital','부산시':'Yeongnam','대구시':'Yeongnam','울산시':'Yeongnam','경상북도':'Yeongnam','경상남도':'Yeongnam','광주시':'Honam','전라북도':'Honam','전라남도':'Honam','대전시':'Chungcheong','세종시':'Chungcheong','충청북도':'Chungcheong','충청남도':'Chungcheong','강원도':'Gangwon','제주도':'Jeju'}
def load():
    N = {}
    X = pd.read_csv(os.path.join(PAN, "UNDX_Estd3.csv"), encoding="utf-8-sig")
    N["n_rows"] = len(X); N["n_districts"] = X.fbd_region.nunique(); N["cases"] = int(X.cases.sum()); N["cases_H"] = int(X.cases_H.sum()); N["cases_D"] = int(X.cases_D.sum()); N["exam"] = int(X.examinees.sum())
    y = X.groupby("year")[["examinees", "cases", "cases_H", "cases_D"]].sum()
    for c in ["cases", "cases_H", "cases_D"]: y["pct" + c[5:]] = 100 * y[c] / y.examinees
    N["yearly"] = y.round(3).reset_index().to_dict("records")
    g = X.groupby("fbd_region")[["cases", "E_std", "cases_H", "E_std_H", "cases_D", "E_std_D"]].sum()
    for s in ["", "_H", "_D"]:
        r = g["cases" + s] / g["E_std" + s]; N["sir" + s] = dict(p10=round(r.quantile(.1), 3), med=round(r.median(), 3), p90=round(r.quantile(.9), 3), min=round(r.min(), 3), max=round(r.max(), 3), p90p10=round(r.quantile(.9) / r.quantile(.1), 3))
    N["rho_HD"] = round((g.cases_H / g.E_std_H).corr(g.cases_D / g.E_std_D, method="spearman"), 3)
    for T, k in [("UNDX", ""), ("UNDXH", "_H"), ("UNDXD", "_D")]:
        S6 = rd(T, "S6_spatial_RR.csv"); S6 = S6[S6["class"] != "unobserved"].copy(); S6["reg"] = S6.fbd_region.str.extract(r"^(\S+?[시도])")[0].map(REG)
        N["hot" + k] = int((S6["class"] == "hotspot").sum()); N["cold" + k] = int((S6["class"] == "coldspot").sum())
        N["hot_reg" + k] = S6[S6["class"] == "hotspot"].reg.value_counts().to_dict(); N["cold_reg" + k] = S6[S6["class"] == "coldspot"].reg.value_counts().to_dict()
        N["rr_range" + k] = [round(S6.RR.min(), 3), round(S6.RR.max(), 3)]
        m = rd(T, "S6_moran_year.csv"); N["moran" + k] = dict(zip(m.year.astype(int), m.moran_I.round(2)))
        F = rd(T, "S3_main_fit.csv").iloc[0]; N["phi" + k] = float(F.phi); N["resid_moran" + k] = float(F.resid_moran_I)
    P = rd("UNDX", "S12_persistence.csv"); N["kendallW"] = round(float(P.iloc[0].kendall_W), 2)
    VP = rd("UNDX", "S42_variance_partition.csv").set_index("component"); N["vp_spatial"] = round(float(VP.loc["spatial_structured", "share_of_sum"]), 2)
    MV = rd("UNDX", "S7_multiverse_summary.csv").set_index("cov"); N["n_specs"] = int(MV.n_specs_total.iloc[0])
    NC = rd("UNDX", "S3_negcontrol.csv"); N["negctl_cred"] = int(NC.cred.sum()); N["negctl_n"] = len(NC)
    R1 = rd("UNDX", "S1_likelihood.csv"); N["waic_forced_nb"] = float(R1[R1.family == "nbinomial"].WAIC.iloc[0]); N["waic_main"] = float(rd("UNDX", "S3_main_fit.csv").WAIC.iloc[0])
    EV = rd("UNDX", "S41_evalues.csv").set_index("cov"); N["evalue_edu"] = [float(EV.loc["tertiary_educated_share", "E_point"]), float(EV.loc["tertiary_educated_share", "E_limit"])]
    NCO = rd("UNDX", "S41_nco_detail.csv"); N["nco_edu"] = NCO[NCO["cov"] == "tertiary_educated_share"][["analysis", "IRR", "lo", "hi"]].to_dict("records")
    PH = rd("UNDX", "S46_undx_posthoc.csv"); N["posthoc"] = PH.to_dict("records")
    OOS = rd("UNDX", "S41_oos2024.csv").iloc[0]; N["oos_cov"] = float(OOS.coverage95)
    return N
HYP = ["tertiary_educated_share", "bp_awareness_rate", "glucose_awareness_rate", "im_specialists_per_100k", "screening_uptake", "obesity_rate", "high_risk_drinking_rate", "current_smoking_rate", "walking_practice_rate", "moderate_pa_rate", "basic_livelihood_rate", "single_person_household_share"]
LAB = {"tertiary_educated_share": "Tertiary education, %", "bp_awareness_rate": "Blood pressure awareness, %", "glucose_awareness_rate": "Blood glucose awareness, %", "im_specialists_per_100k": "Internal medicine specialists per 100,000 (log)",
       "screening_uptake": "Health screening uptake, %", "obesity_rate": "Obesity, self-reported, %", "high_risk_drinking_rate": "High-risk drinking, %", "current_smoking_rate": "Current smoking, %", "walking_practice_rate": "Walking, %",
       "moderate_pa_rate": "Moderate-or-vigorous activity, %", "basic_livelihood_rate": "Public assistance recipients, %", "single_person_household_share": "Single-person households, %"}
DIR = {"tertiary_educated_share": "−", "bp_awareness_rate": "−", "glucose_awareness_rate": "−", "im_specialists_per_100k": "−", "screening_uptake": "−", "obesity_rate": "+", "high_risk_drinking_rate": "+", "current_smoking_rate": "+", "walking_practice_rate": "−", "moderate_pa_rate": "−", "basic_livelihood_rate": "+", "single_person_household_share": "+"}
f3 = lambda r: f"{r.IRR:.3f} ({r.lo:.3f}–{r.hi:.3f})"
def table2():
    M = rd("UNDX", "S3_main_IRR.csv").set_index("cov"); MV = rd("UNDX", "S7_multiverse_summary.csv").set_index("cov"); K4 = rd("UNDX", "S43_part_KH_typeIV.csv").set_index("cov")
    W = rd("UNDX", "S4_window_IRR.csv"); W1 = W[W.window == "W1_2011-17"].set_index("cov"); W2 = W[W.window == "W2_2018-24"].set_index("cov")
    H = rd("UNDXH", "S3_main_IRR.csv").set_index("cov"); D = rd("UNDXD", "S3_main_IRR.csv").set_index("cov")
    rows = []
    for c in HYP:
        rows.append({"Characteristic (per 1 SD)": LAB[c], "Sign": DIR[c], "Main model": f3(M.loc[c]), "Specs, %": str(int(100*MV.loc[c].cred_frac + 0.5)),
                     "Knorr-Held IV": f3(K4.loc[c]), "2011–2017": f3(W1.loc[c]), "2018–2024": f3(W2.loc[c]), "Hypertension": f3(H.loc[c]), "Diabetes": f3(D.loc[c])})
    return pd.DataFrame(rows)
def table1(N):
    X = pd.read_csv(os.path.join(PAN, "UNDX_Estd3.csv"), encoding="utf-8-sig"); P = pd.read_csv(os.path.join(AN, "UNDX", "panel_UNDX_std3.csv"), encoding="utf-8-sig")
    rows = []
    for yr in [2011, 2017, 2018, 2024]:
        y = X[X.year == yr]; p = P[P.year == yr]
        rows.append({"Year": yr, "Examinees, n": f"{int(y.examinees.sum()):,}", "Suspected hypertension or diabetes, n (%)": f"{int(y.cases.sum()):,} ({100*y.cases.sum()/y.examinees.sum():.1f})",
                     "Suspected hypertension, n (%)": f"{int(y.cases_H.sum()):,} ({100*y.cases_H.sum()/y.examinees.sum():.1f})", "Suspected diabetes, n (%)": f"{int(y.cases_D.sum()):,} ({100*y.cases_D.sum()/y.examinees.sum():.1f})",
                     "District proportion, median (IQR), %": f"{(100*y.cases/y.examinees).median():.1f} ({(100*y.cases/y.examinees).quantile(.25):.1f}–{(100*y.cases/y.examinees).quantile(.75):.1f})",
                     "Tertiary education, median (IQR), %": f"{p.tertiary_educated_share_raw.median():.1f} ({p.tertiary_educated_share_raw.quantile(.25):.1f}–{p.tertiary_educated_share_raw.quantile(.75):.1f})"})
    return pd.DataFrame(rows)
if __name__ == "__main__":
    N = load(); os.makedirs(os.path.join(HERE, "tables"), exist_ok=True)
    json.dump(N, open(os.path.join(HERE, "numbers_undx.json"), "w"), ensure_ascii=False, indent=1, default=str)
    t1 = table1(N); t2 = table2(); t1.to_csv(os.path.join(HERE, "tables", "Table1.csv"), index=False); t2.to_csv(os.path.join(HERE, "tables", "Table2.csv"), index=False)
    print(t1.to_string()); print(t2.to_string())
    print({k: N[k] for k in ["cases", "exam", "sir", "sir_H", "sir_D", "rho_HD", "hot", "cold", "hot_reg", "cold_reg", "hot_reg_D", "rr_range", "kendallW", "vp_spatial", "negctl_cred", "evalue_edu", "oos_cov", "phi", "resid_moran"]})
