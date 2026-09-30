#!/bin/zsh
# Espera que b4c acabi i encadena c4 build → verify → gate → publish i c3 comparació.
cd "$(dirname "$0")"
PY=~/.venvs/eines-ia-py312/bin/python; export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=4
while ! grep -q "B4c fet" b4c.log; do sleep 15; done
echo "$(date +%H:%M:%S) b4c acabat, arrenca c4" > final.log
$PY -W ignore c4_psb.py build >> c4_build.log 2>&1 || { echo "BUILD FALLA" >> final.log; exit 1; }
$PY -W ignore c4_psb.py verify >> c4_verify.log 2>&1 || { echo "VERIFY FALLA" >> final.log; exit 1; }
$PY -W ignore c4_psb.py gate >> c4_gate.log 2>&1 || { echo "GATE FALLA" >> final.log; exit 1; }
$PY -W ignore c4_psb.py publish >> c4_publish.log 2>&1 || { echo "PUBLISH FALLA" >> final.log; exit 1; }
$PY -W ignore c3_compara.py >> c3.log 2>&1 || echo "C3 FALLA" >> final.log
echo "$(date +%H:%M:%S) FINAL fet" >> final.log
