#!/bin/zsh
cd "/Users/USUARI/Downloads/Eclipse 2026/research/tools/v38_20260908"; export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=6; PY=~/.venvs/eines-ia-py312/bin/python
run() { echo "== $1 $(date +%H:%M:%S)" >> cadena.log; $PY -W ignore "$@" > "$1.log" 2>&1 || { echo "ERROR a $1" >> cadena.log; tail -20 "$1.log" >> cadena.log; exit 1; }; tail -1 "$1.log" >> cadena.log; }
run b4c_purs.py mgn wow; run b4d_radial_vora.py; run b4b_capes_azimutals.py; run c3_portes.py
echo "== CADENA V38 (fins a C3) ACABADA $(date +%H:%M:%S)" >> cadena.log
