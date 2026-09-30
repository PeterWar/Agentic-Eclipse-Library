#!/bin/zsh
cd "/Users/USUARI/Downloads/Eclipse 2026/research/tools/v36_20260908"; export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=6; PY=~/.venvs/eines-ia-py312/bin/python
run() { echo "== $1 $(date +%H:%M:%S)"; $PY -W ignore "$@" > "$1.log" 2>&1 || { echo "ERROR a $1"; tail -20 "$1.log"; exit 1; }; tail -1 "$1.log"; }
run a1_pesos_per_fotograma.py; run b1_camps_per_fotograma.py; run b2_recomposicio.py; run b3_fusio.py; run b4a_capes_cadena.py
echo "== PART 1 V36 ACABADA $(date +%H:%M:%S)"
