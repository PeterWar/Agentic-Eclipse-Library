#!/bin/zsh
cd "/Users/USUARI/Downloads/Eclipse 2026/research/tools/v35_20260908"; export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=4; PY=~/.venvs/eines-ia-py312/bin/python
for step in verify gate publish; do echo "== c4 $step $(date +%H:%M:%S)"; $PY -W ignore c4_psb.py $step > c4_$step.log 2>&1 || { echo "ERROR c4 $step"; tail -8 c4_$step.log; exit 1; }; tail -1 c4_$step.log; done; echo "== C4 ACABAT $(date +%H:%M:%S)"
