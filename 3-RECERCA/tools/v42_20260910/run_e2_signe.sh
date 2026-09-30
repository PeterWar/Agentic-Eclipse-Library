#!/bin/zsh
cd "$(dirname "$0")"; export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=2; PY=~/.venvs/eines-ia-py312/bin/python
$PY -W ignore e2_estrelles_ab.py "/Users/USUARI/Downloads/Eclipse 2026/research/tools/v36_20260908/cau/sony_B_total_v36.npy" v36 > e2_v36.log 2>&1
$PY -W ignore e2_estrelles_ab.py cau/sony_B_total_v42_dpos.npy dpos > e2_dpos.log 2>&1
$PY -W ignore e2_estrelles_ab.py cau/sony_B_total_v42_dneg.npy dneg > e2_dneg.log 2>&1
echo "E2 FET"
