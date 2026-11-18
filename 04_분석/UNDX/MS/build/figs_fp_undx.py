# -*- coding: utf-8 -*-
# figs_fp_undx.py — 그림 2장 Family Practice판(2026-11-19): 그림 안 약어를 풀어 씀, 나머지는 figs_undx.py와 같음.
#  그림은 원고에 넣지 않고 별도 파일, 원본 형식(EPS/SVG) + PDF, 지도 600 dpi TIFF, 8.5×11 세로 안, 캡션은 그림 밖(원고 끝).
#  규칙: 컬러, 패널 문자 대문자·모두 같은 크기(fig.text 상수 PANEL_LABEL_PT=60), 방위표 3배, 그림 안 설명문 없음, 결합은 시군구 코드로만.
#  Fig 1 (A) 합 결과 잔차 공간 RR + 핫·콜드 (B) 고혈압 의심 (C) 당뇨 의심 (D) 연도별 Moran's I 세 결과 · Fig 2 (A) 주모형 가설 12개 RR (B) 고등교육 비율 RR 분석별
import os, unicodedata, numpy as np, pandas as pd, geopandas as gpd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch, Rectangle, Polygon
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__)); AN = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SHP = os.environ.get("ST_SHP", os.path.join(HERE, "..", "..", "..", "..", "data", "boundary", "final.shp"))
FIG = os.path.join(HERE, "figs_fp"); os.makedirs(FIG, exist_ok=True); OUTF = os.path.join(os.path.dirname(HERE), "out_fp", "Figures"); os.makedirs(OUTF, exist_ok=True)
MM = 1 / 25.4; W = 178 * MM; DPI = 600; LW = 0.3
plt.rcParams.update({"font.family": "Arial", "font.size": 8, "legend.fontsize": 7.5, "legend.title_fontsize": 8, "axes.linewidth": 0.5, "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none"})
PANEL_LABEL_PT = 60
def letter(fig, ch, x, y): fig.text(x, y, ch.upper(), fontsize=PANEL_LABEL_PT, fontweight="bold", va="top", ha="left")
rd = lambda T, f: pd.read_csv(os.path.join(AN, T, "results_std3", f), encoding="utf-8-sig", dtype={"sigungu_cd": str})
G = gpd.read_file(SHP); G["cd"] = G.sigungu_cd.astype(str); G["sido"] = G.cd.str[:2]; SIDO = G.dissolve("sido")
XL = (G.total_bounds[0], G.total_bounds[2]); YL = (G.total_bounds[1], G.total_bounds[3])
def mapax(ax):
    SIDO.boundary.plot(ax=ax, color="#404040", linewidth=0.8); ax.set_xlim(*XL); ax.set_ylim(*YL); ax.set_axis_off(); ax.set_aspect("equal")
    x0, x1 = XL; y0, y1 = YL; W_ = x1 - x0; H_ = y1 - y0; bx, by = x0 + 0.60 * W_, y0 + 0.03 * H_; hh = 0.012 * H_
    ax.add_patch(Rectangle((bx, by), 50000, hh, facecolor="black", edgecolor="black", linewidth=0.8)); ax.add_patch(Rectangle((bx + 50000, by), 50000, hh, facecolor="white", edgecolor="black", linewidth=0.8))
    for xx, lab in ((0, "0"), (50000, "50"), (100000, "100")): ax.text(bx + xx, by + hh + 0.008 * H_, lab, ha="center", va="bottom", fontsize=6.5)
    ax.text(bx + 108000, by + 0.5 * hh, "km", ha="left", va="center", fontsize=6.5)
    nx, ny = x0 + 0.92 * W_, y0 + 0.66 * H_
    ax.add_patch(Polygon([[nx - 0.036 * W_, ny], [nx + 0.036 * W_, ny], [nx, ny + 0.21 * H_]], closed=True, facecolor="black", edgecolor="none"))
    ax.text(nx, ny + 0.225 * H_, "N", ha="center", va="bottom", fontsize=22)
def save(fig, k):
    base = os.path.join(OUTF, f"Figure{k}")
    fig.savefig(base + ".pdf", facecolor="white"); fig.savefig(base + ".eps", facecolor="white"); fig.savefig(base + ".svg", facecolor="white")
    p = os.path.join(FIG, f"Fig{k}.png"); fig.savefig(p, dpi=DPI, facecolor="white"); plt.close(fig)
    im = Image.open(p).convert("RGB"); im.save(base + ".tif", dpi=(DPI, DPI), compression="tiff_lzw"); return im.size
BR = [0, 0.85, 0.9, 0.95, 1, 1.05, 1.1, 1.15, 99]; LB = ["<0.85", "0.85–0.89", "0.90–0.94", "0.95–0.99", "1.00–1.04", "1.05–1.09", "1.10–1.14", "≥1.15"]
PAL = ["#2166AC", "#4393C3", "#92C5DE", "#D1E5F0", "#FDDBC7", "#F4A582", "#D6604D", "#B2182B"]
fig = plt.figure(figsize=(W, 240 * MM))
axs = [fig.add_axes([0.03, 0.56, 0.45, 0.40]), fig.add_axes([0.53, 0.56, 0.45, 0.40]), fig.add_axes([0.03, 0.12, 0.45, 0.40])]
for ax, T, ch, xy in zip(axs, ["UNDX", "UNDXH", "UNDXD"], "ABC", [(0.0, 0.995), (0.50, 0.995), (0.0, 0.555)]):
    S6 = rd(T, "S6_spatial_RR.csv"); assert len(S6) == 229
    d = S6.set_index("sigungu_cd"); gg = G.copy(); gg["v"] = gg.cd.map(d.RR); gg["c"] = gg.cd.map(d["class"]); assert int((gg.c == "unobserved").sum()) == 1 and gg.v.notna().all()
    ob = gg[gg.c != "unobserved"]; ob.plot(ax=ax, column="v", cmap=ListedColormap(PAL), norm=BoundaryNorm(BR, len(PAL)), edgecolor="#a0a0a0", linewidth=LW)
    gg[gg.c == "unobserved"].plot(ax=ax, color="#bdbdbd", edgecolor="#a0a0a0", linewidth=LW)
    gg[gg.c == "coldspot"].boundary.plot(ax=ax, color="#2171B5", linewidth=0.6, linestyle=(0, (2.0, 1.2))); gg[gg.c == "hotspot"].boundary.plot(ax=ax, color="black", linewidth=0.6)
    mapax(ax); letter(fig, ch, *xy)
ax = fig.add_axes([0.60, 0.17, 0.37, 0.30]); letter(fig, "D", 0.50, 0.555)
for T, lab, ls, mk in [("UNDX", "Hypertension or diabetes", "-", "o"), ("UNDXH", "Hypertension", "--", "s"), ("UNDXD", "Diabetes", ":", "^")]:
    m = rd(T, "S6_moran_year.csv"); ax.plot(m.year, m.moran_I, ls, marker=mk, ms=3, lw=1.1, label=lab, color={"UNDX": "#B2182B", "UNDXH": "#E08214", "UNDXD": "#2166AC"}[T])
ax.axvline(2017.5, color="#808080", lw=0.6, ls=(0, (1, 2)))
ax.set_xlabel("Year"); ax.set_ylabel("Moran's I, observed log standardized ratio"); ax.set_ylim(0, 0.7); ax.set_xticks(range(2011, 2025, 2)); ax.legend(frameon=False, loc="lower right", fontsize=7)
for s in ("top", "right"): ax.spines[s].set_visible(False)
h = [Patch(facecolor=c, edgecolor="#777777", linewidth=LW, label=l) for c, l in zip(PAL, LB)] + [Patch(facecolor="none", edgecolor="black", linewidth=0.8, label="Hot spot"), Patch(facecolor="none", edgecolor="#2171B5", linewidth=0.8, linestyle="--", label="Cold spot"), Patch(facecolor="#bdbdbd", edgecolor="#777777", linewidth=LW, label="Not observed")]
fig.legend(handles=h, title="Residual spatial rate ratio (A–C)", loc="lower center", bbox_to_anchor=(0.5, 0.0), ncol=6, frameon=False, columnspacing=0.8, handlelength=1.2)
print("Fig1", save(fig, 1))
# Fig 2
LABEL = {"tertiary_educated_share": "Tertiary education", "bp_awareness_rate": "Blood pressure awareness", "glucose_awareness_rate": "Blood glucose awareness", "im_specialists_per_100k": "Internal medicine specialists",
         "screening_uptake": "Screening uptake", "obesity_rate": "Obesity", "high_risk_drinking_rate": "High-risk drinking", "current_smoking_rate": "Current smoking", "walking_practice_rate": "Walking",
         "moderate_pa_rate": "Moderate-or-vigorous activity", "basic_livelihood_rate": "Public assistance recipients", "single_person_household_share": "Single-person households"}
S3 = rd("UNDX", "S3_main_IRR.csv"); S3 = S3[S3.role == "hypothesis"].set_index("cov").loc[list(LABEL)]
def row(T, f, an=None, cov="tertiary_educated_share", col="analysis"):
    d = rd(T, f); d = d[d["cov"] == cov]
    if an is not None: d = d[d[col] == an]
    assert len(d) == 1, (T, f, an); r = d.iloc[0]; return float(r.IRR), float(r.lo), float(r.hi)
E = [("Main model", row("UNDX", "S3_main_IRR.csv")),
     ("Knorr-Held type II", row("UNDX", "S43_part_KH_typeII.csv")), ("Knorr-Held type III", row("UNDX", "S43_part_KH_typeIII.csv")), ("Knorr-Held type IV", row("UNDX", "S43_part_KH_typeIV.csv")),
     ("Province-by-year effects", row("UNDX", "S41_part_C4_sido_year_iid.csv")), ("Between-district", row("UNDX", "S41_part_bw_twoway.csv", cov="tertiary_educated_share__between")),
     ("Within-district", row("UNDX", "S41_part_bw_twoway.csv", cov="tertiary_educated_share__within")),
     ("2011–2017", row("UNDX", "S4_window_IRR.csv", "W1_2011-17", col="window")), ("2018–2024", row("UNDX", "S4_window_IRR.csv", "W2_2018-24", col="window")),
     ("Population denominator", row("UNDX", "S10_offset_sensitivity_IRR.csv")),
     ("Hypertension only", row("UNDXH", "S3_main_IRR.csv")), ("Diabetes only", row("UNDXD", "S3_main_IRR.csv"))]
fig = plt.figure(figsize=(W, 110 * MM))
for k, (ax, ttl) in enumerate([(fig.add_axes([0.30, 0.12, 0.22, 0.74]), "12 hypothesized district factors"), (fig.add_axes([0.745, 0.12, 0.225, 0.74]), "Tertiary education, by analysis")]):
    if k == 0: names = [LABEL[c] for c in S3.index]; v = S3[["IRR", "lo", "hi"]].values; cr = S3.cred.values
    else: names = [e[0] for e in E]; v = np.array([e[1] for e in E]); cr = (v[:, 1] > 1) | (v[:, 2] < 1)
    y = np.arange(len(names))[::-1]
    ax.errorbar(v[:, 0], y, xerr=[v[:, 0] - v[:, 1], v[:, 2] - v[:, 0]], fmt="none", ecolor="#555555", elinewidth=0.8, capsize=1.5)
    ax.scatter(v[:, 0], y, s=14, c=np.where(cr, "#B2182B", "white"), edgecolors="#B2182B", linewidths=0.8, zorder=3)
    ax.axvline(1, color="#808080", lw=0.6); ax.set_yticks(y); ax.set_yticklabels(names, fontsize=7); ax.set_xlabel("Rate ratio per 1 standard deviation\n(95% credible interval)")
    ax.set_title(ttl, fontsize=8, loc="left"); [ax.spines[s].set_visible(False) for s in ("top", "right")]
    if k == 0: ax.set_xlim(0.92, 1.04)
    else: ax.set_xlim(0.88, 1.02)
letter(fig, "A", 0.0, 0.995); letter(fig, "B", 0.53, 0.995)
print("Fig2", save(fig, 2))
