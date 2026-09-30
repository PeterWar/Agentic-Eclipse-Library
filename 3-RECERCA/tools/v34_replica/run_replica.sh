#!/bin/zsh
cd "/Users/USUARI/Downloads/Eclipse 2026/research/tools/v34_replica"; export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=4; PY=~/.venvs/eines-ia-py312/bin/python
for s in a1_pesos_per_fotograma.py b1_camps_per_fotograma.py b2_recomposicio.py; do echo "== $s $(date +%H:%M:%S)"; $PY -W ignore $s > $s.log 2>&1 || { echo "ERROR $s"; tail -5 $s.log; exit 1; }; tail -1 $s.log; done; echo "== REPLICA V34 ACABADA $(date +%H:%M:%S)"
