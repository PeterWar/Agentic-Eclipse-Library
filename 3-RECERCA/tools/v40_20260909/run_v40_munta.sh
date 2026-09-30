#!/bin/zsh
cd "/Users/USUARI/Downloads/Eclipse 2026/research/tools/v40_20260909"; export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=6; PY=~/.venvs/eines-ia-py312/bin/python; L=cadena_v40_munta.log
while ! grep -q "PILOT V40 FET\|ERROR" ../v39_20260909/cadena_v40.log; do sleep 15; done
echo "== pilot 2 acabat $(date +%H:%M:%S)" >> $L; rm -f staging/V40.psb
for step in build verify gate publish; do echo "== c4 $step $(date +%H:%M:%S)" >> $L; $PY -W ignore c4_projecte_v40.py $step > c4_$step.log 2>&1 || { echo "ERROR $step" >> $L; tail -8 c4_$step.log >> $L; exit 1; }; tail -1 c4_$step.log >> $L; done
for s in c5_rebut_v40.py e1_resultats_157.py d1_autoritat_v40.py d2_tanca_v40.py; do echo "== $s $(date +%H:%M:%S)" >> $L; $PY -W ignore $s > ${s%.py}.log 2>&1 || { echo "ERROR $s" >> $L; tail -8 ${s%.py}.log >> $L; exit 1; }; tail -1 ${s%.py}.log >> $L; done
echo "== V40 LLIURADA $(date +%H:%M:%S)" >> $L
