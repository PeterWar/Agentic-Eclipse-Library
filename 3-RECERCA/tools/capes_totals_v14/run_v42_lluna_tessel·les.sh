#!/bin/zsh
cd "$(dirname "$0")"; export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=2; PY=~/.venvs/eines-ia-py312/bin/python; CORR="/Users/USUARI/Downloads/Eclipse 2026/research/tools/v42_20260910/cau/correccions_B.json"
for f in DSC06987 DSC06993 DSC06984 DSC06996 DSC06999; do echo "== sony $f $(date +%H:%M:%S)"; $PY -W ignore v42_lluna_tren_g0.py sony $f _${f}_g0 "$CORR" > cau_v21/log_g0_$f.txt 2>&1 || { echo "ERROR $f"; tail -5 cau_v21/log_g0_$f.txt; }; done
for f in 572A2982 572A2983 572A2984; do echo "== vixen $f $(date +%H:%M:%S)"; $PY -W ignore v42_lluna_tren_g0.py vixen $f _${f}_g0 > cau_v21/log_g0_$f.txt 2>&1 || { echo "ERROR $f"; tail -5 cau_v21/log_g0_$f.txt; }; done
echo "TESSEL·LES G0 FETES $(date +%H:%M:%S)"
