#!/bin/zsh
# cadena_v95.sh · w1 (càlcul) → b2 (muntatge) → Photoshop sense documents oberts? → b3 (desament natiu) → p6 (compost fusionat) → porta → b4b5 (proves i làmines)
set -e; cd "$(dirname "$0")/../../.."; PY=~/.venvs/eines-ia-py312/bin/python; T=3-RECERCA/tools/v95_20260924; R=4-RESULTATS/v95_20260924
$PY -u $T/w1_wow_v95.py 2>&1 | grep --line-buffered -v Warn | tee $R/w1.log
$PY $T/b2_munta_v95.py 2>&1 | grep -v Warn | tail -1
N=$(osascript -e 'tell application id "com.adobe.Photoshop" to do javascript "app.documents.length"')
if [ "$N" != "0" ]; then echo "ATURAT: el Photoshop té $N documents oberts (poden ser de Pere); no deso"; exit 5; fi
zsh $T/corre_jsx.sh $T/b3_desa_natiu.jsx
$PY $T/p6_compost_fusionat.py 1-PHOTOSHOP/V95.psb $R/vistes/V95_llenc_sencer.tif | tee $R/P6_COMPOST.txt
bash 3-RECERCA/tools/capes_totals_v14/porta_photoshop.sh "$PWD/1-PHOTOSHOP/V95.psb" 2>&1 | tail -1 | tee $R/PORTA.txt
shasum -a 256 1-PHOTOSHOP/V95.psb | tee $R/SHA_V95.txt
$PY $T/b4b5_qa_laminas_v95.py 2>&1 | grep -v Warn | grep -E "P2_PASS|ombra|fet"
echo CADENA_FETA
