#!/bin/zsh
# cadena_v96.sh · b2 (muntatge) → Photoshop sense documents oberts? → b3 (desament natiu) → p6 (compost fusionat) → porta → b4 (proves i làmines)
set -e; cd "$(dirname "$0")/../../.."; PY=~/.venvs/eines-ia-py312/bin/python; T=3-RECERCA/tools/v96_nrgf_20260924; R=4-RESULTATS/v96_nrgf_20260924
$PY $T/b2_munta_v96.py 2>&1 | grep -v Warn | tail -1
N=$(osascript -e 'tell application id "com.adobe.Photoshop" to do javascript "app.documents.length"')
if [ "$N" != "0" ]; then echo "ATURAT: el Photoshop té $N documents oberts (poden ser de Pere); no deso"; exit 5; fi
zsh $T/corre_jsx.sh $T/b3_desa_natiu.jsx
$PY $T/p6_compost_fusionat.py 1-PHOTOSHOP/V96.psb $R/vistes/V96_llenc_sencer.tif | tee $R/P6_COMPOST.txt
bash 3-RECERCA/tools/capes_totals_v14/porta_photoshop.sh "$PWD/1-PHOTOSHOP/V96.psb" 2>&1 | tail -1 | tee $R/PORTA.txt
shasum -a 256 1-PHOTOSHOP/V96.psb | tee $R/SHA_V96.txt
$PY $T/b4_qa_laminas_v96.py 2>&1 | grep -v Warn
echo CADENA_FETA
