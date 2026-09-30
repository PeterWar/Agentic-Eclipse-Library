#!/bin/zsh
cd "/Users/USUARI/Downloads/Eclipse 2026/research/tools/v39_20260909"; export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=3; PY=~/.venvs/eines-ia-py312/bin/python
$PY -W ignore b2_meitats.py pA > b2_pA.log 2>&1 && $PY -W ignore b2_meitats.py pB > b2_pB.log 2>&1 || { echo "ERROR b2 pA/pB" >> cadena_v40.log; exit 1; }
echo "b2 pA/pB fets $(date +%H:%M:%S)" >> cadena_v40.log
(PART=pAB nohup $PY -W ignore a2_soroll_meitats.py > a2_pAB.log 2>&1 &)
(PART=pAB OPENBLAS_NUM_THREADS=2 nohup $PY -W ignore a2c_soroll_canals.py 0 > a2c_0_pAB.log 2>&1 &)
(PART=pAB OPENBLAS_NUM_THREADS=2 nohup $PY -W ignore a2c_soroll_canals.py 2 > a2c_2_pAB.log 2>&1 &)
while pgrep -f "a4_soroll_bilateral.py" > /dev/null && ! grep -q "A4 fet" a4.log; do sleep 15; done
PART=pAB $PY -W ignore a4_soroll_bilateral.py > a4_pAB.log 2>&1; echo "A4 pAB fet $(date +%H:%M:%S)" >> cadena_v40.log
