#!/bin/zsh
cd "/Users/USUARI/Downloads/Eclipse 2026/research/tools/v36_20260908"; export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=6; PY=~/.venvs/eines-ia-py312/bin/python
run() { echo "== $1 $(date +%H:%M:%S)"; $PY -W ignore "$@" > "$1.log" 2>&1 || { echo "ERROR a $1"; tail -20 "$1.log"; exit 1; }; tail -1 "$1.log"; }
run a1_pesos_per_fotograma.py; run b1_camps_per_fotograma.py; run b2_recomposicio.py; run b3_fusio.py; run b4a_capes_cadena.py; run b4c_purs.py mgn wow; run b4d_radial_vora.py; rm -f staging/V36.psb
echo "== c4 build $(date +%H:%M:%S)"; $PY -W ignore c4_psb.py build > c4_build.log 2>&1 || { echo ERROR c4 build; tail -5 c4_build.log; exit 1; }; tail -1 c4_build.log
echo "== c4 verify $(date +%H:%M:%S)"; $PY -W ignore c4_psb.py verify > c4_verify.log 2>&1 || { echo ERROR c4 verify; tail -5 c4_verify.log; exit 1; }; tail -1 c4_verify.log
echo "== c4 gate $(date +%H:%M:%S)"; $PY -W ignore c4_psb.py gate > c4_gate.log 2>&1 || { echo ERROR c4 gate; tail -5 c4_gate.log; exit 1; }; tail -1 c4_gate.log; echo "== CADENA V36 ACABADA $(date +%H:%M:%S)"
