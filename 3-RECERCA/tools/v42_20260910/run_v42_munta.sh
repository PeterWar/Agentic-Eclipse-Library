#!/bin/zsh
cd "$(dirname "$0")"; export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=4; PY=~/.venvs/eines-ia-py312/bin/python
for pas in build verify gate publish; do echo "== $pas $(date +%H:%M:%S)"; $PY -W ignore c4_projecte_v42.py $pas > c4_$pas.log 2>&1 || { echo "FALLA $pas"; tail -6 c4_$pas.log; exit 1; }; tail -1 c4_$pas.log | cut -c1-160; done
$PY -W ignore e3_alineament_capes.py "/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V42.psb" > e3.log 2>&1 || { echo "FALLA e3"; tail -6 e3.log; exit 1; }
echo "V42 PUBLICADA I E3 FET"
