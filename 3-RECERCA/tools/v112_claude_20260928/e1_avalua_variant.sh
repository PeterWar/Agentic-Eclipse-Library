#!/bin/zsh
# e1_avalua_variant.sh <variant> · munta el PSB de pas de la variant de cadena (sense la 301), en fa el render natiu complet i mesura:
# perfils de les marques (q1), diferència amb la V112 per zones (v1) i vistes de banda. Tot a 4-RESULTATS/v112_claude_20260928/aval_<variant>/.
set -e; VAR=${1:?}; cd "$(dirname "$0")/../../.."
T=3-RECERCA/tools/v112_claude_20260928; B=4-RESULTATS/v112_claude_20260928; A=$B/aval_$VAR; mkdir -p $A
PY=$HOME/.venvs/eines-ia-py312/bin/python; export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=6
[ -f $A/stage.psb ] || $PY $T/m1_munta_v113.py $A/stage.psb --variant $VAR > $A/munta.log 2>&1 || { tail -3 $A/munta.log; exit 3; }
[ -f $A/render/visible_complet.tif ] || zsh $T/r5_render.sh $A/stage.psb $A/render ""
$PY $T/q1_perfils_marques.py V112=$B/V112_natiu/visible_complet.tif $VAR=$A/render/visible_complet.tif > $A/perfils.txt 2>&1; cat $A/perfils.txt
cp $B/vistes/perfils_marques.png $A/perfils_marques.png; cp $B/PERFILS_MARQUES.json $A/PERFILS_MARQUES.json
$PY $T/v1_diferencia.py $B/V112_natiu/visible_complet.tif $A/render/visible_complet.tif $A/dif > /dev/null
$PY $T/v0c_banda_npy.py $A/render/visible_complet.tif $A/banda.npy
for z in "dalt 4200 0 7600 2400" "dreta 7400 1500 10551 5200" "baix 5500 4000 10551 7506"; do set -- ${=z}
  $PY $T/v0d_retall_banda.py $A/banda_$1.png $2 $3 $4 $5 0.06 $B/vistes/banda_cand.npy $A/banda.npy > /dev/null; done
echo AVALUACIO_${VAR}_FETA
