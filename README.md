# Hypertension and diabetes newly detected at national health checkups across South Korean districts, 2011-2024

Analysis code for the manuscript

> Kim S. *Newly detected hypertension and diabetes at national health checkups follow different maps across South Korean districts.* Manuscript submitted.

Archived version: Zenodo, https://doi.org/10.5281/zenodo.24355983.

## Contents

This repository contains code only. The processed district-year data (master table, analytic panel, expected counts, result tables, adjacency graph and boundary file) are not included; they are available from the author on reasonable request. All source statistics are public (see Data sources).

| Path | What it is |
|---|---|
| `01_스크립트/` | Analysis scripts (below) |
| `04_분석/UNDX/sets_UNDX_*.json`, `04_분석/UNDXH/`, `04_분석/UNDXD/`, `run_std3_chain.sh`, `run_sens3.sh` | Covariate set, expected directions, forced controls, comparison outcomes and model settings fixed before covariate models were fitted (principal model `std3`; sensitivity versions `s577`, `s2`, `s8`; component outcomes UNDXH, hypertension, and UNDXD, diabetes), and the run order |
| `04_분석/UNDX/MS/build/` | Scripts that read the result tables and write every number, table, figure and reference in the manuscript |

Folder and some column names are in Korean because the source tables are Korean; each script has a header comment describing its inputs and outputs.

## Data sources

All inputs are public, aggregated statistics. No individual-level data are included.

- Measured systolic and diastolic blood pressure and fasting glucose distributions by province and age group (KOSIS DT_35007_N060-N063, N068, N069), used by `99G_undx_judgement_gate.py`.
- Examinees with suspected hypertension or diabetes, and examinees, by district and sex (KOSIS DT_35007_N103, DT_35007_N098) and nationally by sex and 15 age groups (DT_35007_N104, DT_35007_N099): National Health Insurance Service, national health screening statistics, 2011-2024. `99U_fetch_undx_age_sex.py` fetches the national tables (requires a personal KOSIS API key in `~/.kosis_key`; the key is not included).
- Population by sex and 5-year age group: Ministry of the Interior and Safety, resident registration statistics. The 2023 age block of Changwon duplicated the 2022 block and was corrected (`population_override` in the sets files).
- District covariates: Korean Statistical Information Service (KOSIS), the Community Health Survey, national health screening statistics (uptake, share already under treatment), national assistance statistics and the population census. Comparison outcomes (people treated for gastric cancer and for infectious diseases) come from National Health Insurance Service statistics.

## Pipeline

Run from the repository root (set `ST_ROOT`, `ST_DATA_ROOT` and `ST_FBDZIP_CORRECTED` to the local copies of the public source files). `rslot.sh` limits the number of concurrent R processes.

| Step | Script | Output |
|---|---|---|
| 0 | `99U_fetch_undx_age_sex.py` | National sex-by-age suspicion and examinee tables |
| 0b | `99G_undx_judgement_gate.py` | Comparison of the suspected hypertension and diabetes classification with published distributions of measured blood pressure and fasting glucose, by year and province (Supplementary Table S1) |
| 1 | `99U2_build_Estd3_undx.py` | Sex- and age-standardized expected counts (examinee-based), age-only and population-based variants, share aged 80+ |
| 2 | `99U_screen_undx_prep.py`, `98_fit_forced.R`, `99U_screen_undx.py` (uses `98_screen_std.py`) | Descriptive spatial screening of the three outcomes |
| 3 | `99c_extra_canonical_pool_undx.py` | Internal medicine specialists, public assistance recipients (2021-2023 values below 20% of the district's 2020 and 2024 mean set missing and linearly interpolated), tertiary education, share already under treatment, joined by district code |
| 4 | `80_build_disease_panel_v.py UNDX` (`ST_VER=std3`) | Analytic panel |
| 5 | `81_fit_inla.R UNDX` (see `04_분석/UNDX/run_std3_chain.sh`) | Principal model, set comparison, 200-subset multiverse, window models |
| 6 | `85_window_maps.R`, `86_yearly_maps_ehsa.py`, `87_window_grid.py` | Maps and persistence |
| 7 | `88g_sens_prep.py UNDX std3 INFECT,GCA`, `88g_sens_suite.R` (`GROUP=1..6`), `88h_ppc_varpart.R`, `88k_struct_kh.R`, `88k_struct_kh_undx.R kh` with `kh_constraints_undx.R` (Knorr-Held models with one unobserved district), `89g_sens_combine.py` | Sensitivity analyses, comparison outcomes, Knorr-Held models |
| 8 | `88U_undx_reverse_posthoc.R` | Post hoc models for associations opposite to expectation |
| 9 | `04_분석/UNDX/MS/build/numbers_undx.py`, `figs_fp_undx.py`, `build_refs_undx.py`, `build_fp_undx.py` | Numbers, tables, figures, references and manuscript |

The boundary file is found at `data/boundary/final.shp` by default; set `ST_SHP` to use another path.

## Software

R 4.6.0 with R-INLA, spdep and sf; Python 3.9 with pandas, geopandas, numpy, scipy, matplotlib and python-docx.
