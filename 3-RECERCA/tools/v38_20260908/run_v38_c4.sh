#!/bin/zsh
cd "/Users/USUARI/Downloads/Eclipse 2026/research/tools/v38_20260908"; export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=6; PY=~/.venvs/eines-ia-py312/bin/python
while ! grep -q "ACABADA" cadena.log 2>/dev/null; do if grep -q "ERROR" cadena.log 2>/dev/null; then echo "cadena amb ERROR: no construeixo" >> c4.log; exit 1; fi; sleep 20; done
echo "== c4 build $(date +%H:%M:%S)" >> c4.log; $PY -W ignore c4_projecte_complet.py build > c4_build.log 2>&1 || { echo "ERROR build" >> c4.log; tail -8 c4_build.log >> c4.log; exit 1; }; tail -1 c4_build.log >> c4.log
echo "== c4 verify $(date +%H:%M:%S)" >> c4.log; $PY -W ignore c4_projecte_complet.py verify > c4_verify.log 2>&1 || { echo "ERROR verify" >> c4.log; tail -8 c4_verify.log >> c4.log; exit 1; }; tail -1 c4_verify.log >> c4.log
echo "== c4 gate $(date +%H:%M:%S)" >> c4.log; $PY -W ignore c4_projecte_complet.py gate > c4_gate.log 2>&1 || { echo "ERROR gate" >> c4.log; tail -8 c4_gate.log >> c4.log; exit 1; }; tail -1 c4_gate.log >> c4.log
echo "== C4 LLEST PER PUBLICAR $(date +%H:%M:%S)" >> c4.log
