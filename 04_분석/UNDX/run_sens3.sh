#!/bin/bash
S="${ST_ROOT:?set ST_ROOT}"; cd "$S"; RS="$S/01_스크립트/rslot.sh"; T=UNDX; GR="$S/04_분석/$T/graph_593.graph"
for V in s577 s2 s8; do ST_VER=$V python3 01_스크립트/80_build_disease_panel_v.py $T && (cd 01_스크립트 && ST_VER=$V ST_THREADS=1 ST_MV_N=2 ST_GRAPH=$([ $V = s577 ] || echo "$GR") $RS Rscript 81_fit_inla.R $T); done
echo "SENS3 rc=$?"
