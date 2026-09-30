#!/bin/zsh
# lliura_v104.sh · passos 9–10 per a la V104 (variant E de la cadena V103): muntatge des de la V101, desament natiu com a còpia, portes, verificació i làmines V103 | V104.
set -e; cd "$(dirname "$0")/../../.."
T=3-RECERCA/tools/v103_banda_20260926; T97=3-RECERCA/tools/v97_refundacio_20260924; R=4-RESULTATS/v103_banda_20260926/E
PY="$HOME/.venvs/eines-ia-py312/bin/python"; export PYTHONDONTWRITEBYTECODE=1
[ -f 1-PHOTOSHOP/V104.psb ] && { echo "ATURAT: 1-PHOTOSHOP/V104.psb ja existeix"; exit 10; }
[ -f $R/V104_stage.psb ] || $PY -B $T/b2_munta_v104.py $R/estat_v103 > $R/b2.log 2>&1
zsh $T/desa_natiu_v104.sh $R/V104_stage.psb 1-PHOTOSHOP/V104.psb $R/vistes
$PY $T97/p6_compost_fusionat.py 1-PHOTOSHOP/V104.psb $R/vistes/V104_llenc_sencer.tif | tee $R/P6_COMPOST.txt
bash 3-RECERCA/tools/capes_totals_v14/porta_photoshop.sh "$PWD/1-PHOTOSHOP/V104.psb" 2>&1 | tail -1 | tee $R/PORTA.txt
shasum -a 256 1-PHOTOSHOP/V104.psb | tee $R/SHA_V104.txt
$PY -B $T/v1_verifica_v104.py $R/estat_v103 $R/V1_VERIFICA_V104.json | tail -1
$PY $T/r5_natiu_v103_v104.py 4-RESULTATS/v103_banda_20260926/D/vistes/V103_lluna.tif $R/vistes/V104_lluna.tif $R/laminas
echo LLIURA_V104_FET
