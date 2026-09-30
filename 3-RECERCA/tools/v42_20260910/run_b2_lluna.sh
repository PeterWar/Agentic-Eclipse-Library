#!/bin/zsh
cd "$(dirname "$0")"; export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=2; PY=~/.venvs/eines-ia-py312/bin/python
for f in DSC06987.ARW DSC06984.ARW; do $PY -W ignore b2_lluna_v42.py sony $f > b2l_${f%.ARW}.log 2>&1 || { echo "ERROR $f"; tail -4 b2l_${f%.ARW}.log; }; tail -1 b2l_${f%.ARW}.log | cut -c1-200; done
for f in DSC06993.ARW DSC06996.ARW DSC06999.ARW; do $PY -W ignore b2_lluna_v42.py sony $f delta_arcmin=8.10 corr=cau/correccions_B.json > b2l_${f%.ARW}.log 2>&1 || { echo "ERROR $f"; tail -4 b2l_${f%.ARW}.log; }; tail -1 b2l_${f%.ARW}.log | cut -c1-200; done
for f in 572A2982.CR3 572A2983.CR3 572A2984.CR3; do $PY -W ignore b2_lluna_v42.py vixen $f > b2l_${f%.CR3}.log 2>&1 || { echo "ERROR $f"; tail -4 b2l_${f%.CR3}.log; }; tail -1 b2l_${f%.CR3}.log | cut -c1-200; done
echo "B2-LLUNA FET $(date +%H:%M:%S)"
