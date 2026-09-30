#!/bin/zsh
# verificació de la correcció amb DSC06993 sol → B sencera amb δ + correccions → fusió V42 → base sense estrelles
cd "$(dirname "$0")"; export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=5; PY=~/.venvs/eines-ia-py312/bin/python
$PY -W ignore b2_recomposicio_v42.py sony_B delta_arcmin=8.10 nomes=DSC06993.ARW corr=cau/correccions_B.json sufix=_DSC06993corr > b2_DSC06993corr.log 2>&1 && $PY -W ignore e2_estrelles_ab.py cau/sony_B_total_v42_DSC06993corr.npy DSC06993corr > e2_DSC06993corr.log 2>&1
ok=$($PY -c "import json;e=json.load(open('/Users/USUARI/Downloads/Eclipse 2026/output/v42_20260910/4-rebuts/E2_AB_DSC06993corr.json'));import math;m=e['mitjana_AB'];print(1 if math.hypot(*m)<2.5 else 0)")
if [ "$ok" != "1" ]; then echo "SIGNE DE LA CORRECCIÓ DOLENT: revisa E2_AB_DSC06993corr.json"; exit 1; fi
$PY -W ignore b2_recomposicio_v42.py sony_B delta_arcmin=8.10 corr=cau/correccions_B.json > b2_final.log 2>&1 && $PY -W ignore e2_estrelles_ab.py cau/sony_B_total_v42.npy final > e2_final.log 2>&1 || { echo "ERROR b2 final"; exit 1; }
$PY -W ignore b3_fusio_v42.py > b3.log 2>&1 || { echo "ERROR b3"; tail -5 b3.log; exit 1; }
$PY -W ignore b3b_sense_estrelles_v42.py > b3b.log 2>&1 || { echo "ERROR b3b"; tail -5 b3b.log; exit 1; }
echo "B2-B3b FET"
