#!/bin/zsh
cd "/Users/USUARI/Downloads/Eclipse 2026/research/tools/v37_20260908"; export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=4; PY=~/.venvs/eines-ia-py312/bin/python
while ! grep -q "B4c fet" b4c_purs.py.log; do grep -q Traceback b4c_purs.py.log && { echo "b4c error"; exit 1; }; sleep 10; done; echo "== b4c fet $(date +%H:%M:%S)"
( $PY -W ignore c3_portes.py > c3_portes.py.log 2>&1; echo "== c3 acabat $(date +%H:%M:%S)" ) &
rm -f staging/V37.psb; echo "== c4 build $(date +%H:%M:%S)"; $PY -W ignore c4_psb.py build > c4_build.log 2>&1 || { echo ERROR c4 build; tail -5 c4_build.log; exit 1; }; tail -1 c4_build.log
echo "== c4 verify $(date +%H:%M:%S)"; $PY -W ignore c4_psb.py verify > c4_verify.log 2>&1 || { echo ERROR c4 verify; tail -5 c4_verify.log; exit 1; }; tail -1 c4_verify.log
echo "== c4 gate $(date +%H:%M:%S)"; $PY -W ignore c4_psb.py gate > c4_gate.log 2>&1 || { echo ERROR c4 gate; tail -5 c4_gate.log; exit 1; }; tail -1 c4_gate.log
wait; echo "== V37 c3+c4 ACABATS $(date +%H:%M:%S)"
