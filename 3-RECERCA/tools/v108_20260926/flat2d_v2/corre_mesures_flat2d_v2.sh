#!/bin/zsh
# corre_mesures_flat2d_v2.sh · Totes les mesures abans/després de la variant flat2d_v2 (només lectura del projecte; escriu a 4-RESULTATS/v108_20260926/flat2d_v2/).
# Ordre: compostos amb les màscares de la V107 (control i v2) → traços amb nuls a cada imatge → energia, Brno, nivell i color, vora de la Vixen,
# limbe → capes 305/306 → paràmetres congelats → vistes del llenç sencer → resum. En sèrie (memòria màxima ~7 GB).
set -e
cd "$(dirname "$0")/../../../.."
T=3-RECERCA/tools/v108_20260926/flat2d_v2; R=4-RESULTATS/v108_20260926/flat2d_v2; L=$R/logs
PY=""; for c in "${V108_PY:-}" "$HOME/.venvs/eines-ia-py312/bin/python" "$(command -v python3 2>/dev/null || true)"; do
  if [ -n "$c" ] && [ -x "$c" ] && "$c" -c "import numpy, scipy, cv2, psd_tools" 2>/dev/null; then PY="$c"; break; fi; done
[ -n "$PY" ] || { echo "ATURAT: cap Python"; exit 3; }
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=${OPENBLAS_NUM_THREADS:-4}
cr() { local nom=$1; shift; /usr/bin/time -l -o $L/temps_$nom.txt "$@" > $L/$nom.log 2>&1 || { echo "ATURAT a $nom ($L/$nom.log)"; tail -5 $L/$nom.log; exit 7; }
  printf "%s\t%s s\t%s GB\n" $nom "$(awk '/ real /{print $1; exit}' $L/temps_$nom.txt)" "$(awk '/maximum resident set size/{printf "%.1f", $1/1073741824}' $L/temps_$nom.txt)" | tee -a $L/TEMPS.tsv; }
[ -f $R/compost_control.npy ] || cr c1_control $PY -B $T/c1_compost_v107_mascares.py 4-RESULTATS/v108_20260926/cadena/control/estat_v108 $R/compost_control.npy
[ -f $R/compost_flat2d_v2.npy ] || cr c1_flat2d_v2 $PY -B $T/c1_compost_v107_mascares.py 4-RESULTATS/v108_20260926/cadena/flat2d_v2/estat_v108 $R/compost_flat2d_v2.npy
cr m1_T $PY -B $T/m1_mesura_flat2d_v2.py T
for q in E B N V L; do cr m1_$q $PY -B $T/m1_mesura_flat2d_v2.py $q; done
cr m2 $PY -B $T/m2_limbe_305_306.py
cr m3 $PY -B $T/m3_congelats.py
cr v1_vistes $PY -B $T/v1_vistes_flat2d_v2.py
cr r1_resum $PY -B $T/r1_resum.py
echo MESURES_FLAT2D_V2_FETES
