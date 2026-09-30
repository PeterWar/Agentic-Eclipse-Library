#!/bin/zsh
cd "/Users/USUARI/Downloads/Eclipse 2026/research/tools/v36_20260908"; export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=6; PY=~/.venvs/eines-ia-py312/bin/python
while ! grep -q "PART 1 V36 ACABADA" chain1.log; do grep -q ERROR chain1.log && { echo "part 1 amb error"; exit 1; }; sleep 10; done
run() { echo "== $1 $(date +%H:%M:%S)"; $PY -W ignore "$@" > "$1.log" 2>&1 || { echo "ERROR a $1"; tail -20 "$1.log"; exit 1; }; tail -1 "$1.log"; }
run b4c_purs.py mgn wow; run b4d_radial_vora.py; rm -f staging/V36.psb
echo "== c4 build $(date +%H:%M:%S)"; $PY -W ignore c4_psb.py build > c4_build.log 2>&1 || { echo ERROR c4 build; tail -5 c4_build.log; exit 1; }; tail -1 c4_build.log
echo "== c4 verify $(date +%H:%M:%S)"; $PY -W ignore c4_psb.py verify > c4_verify.log 2>&1 || { echo ERROR c4 verify; tail -5 c4_verify.log; exit 1; }; tail -1 c4_verify.log
echo "== PART 2 V36 ACABADA $(date +%H:%M:%S)"
