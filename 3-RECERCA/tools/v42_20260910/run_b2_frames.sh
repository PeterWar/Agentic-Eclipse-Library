#!/bin/zsh
cd "$(dirname "$0")"; export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=4; PY=~/.venvs/eines-ia-py312/bin/python
for f in DSC06993.ARW DSC06996.ARW DSC06999.ARW; do
  s=${f%.ARW}; $PY -W ignore b2_recomposicio_v42.py sony_B delta_arcmin=8.10 nomes=$f sufix=_$s > b2_$s.log 2>&1 && $PY -W ignore e2_estrelles_ab.py cau/sony_B_total_v42_$s.npy $s > e2_$s.log 2>&1
done
echo "FRAMES FET"
