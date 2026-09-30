#!/bin/zsh
# corre_mesures_flat2d_v3.sh · Totes les mesures abans/després de la variant flat2d_v3 (només lectura del projecte; escriu a 4-RESULTATS/v108_20260926/flat2d_v3/).
# Ordre: compost amb les màscares de la V107 (c1 de la v2) → proves A − B (Sony) i Vixen − Sony del canvi v3 → m1 (T S K B F P L V Q) → vistes.
# En sèrie (memòria màxima ~10 GB). ⛔ No l'editis mentre corre.
set -e
cd "$(dirname "$0")/../../../.."
T=3-RECERCA/tools/v108_20260926/flat2d_v3; T2=3-RECERCA/tools/v108_20260926/flat2d_v2; R=4-RESULTATS/v108_20260926/flat2d_v3; L=$R/logs
PY=""; for c in "${V108_PY:-}" "$HOME/.venvs/eines-ia-py312/bin/python" "$(command -v python3 2>/dev/null || true)"; do
  if [ -n "$c" ] && [ -x "$c" ] && "$c" -c "import numpy, scipy, cv2, psd_tools, matplotlib" 2>/dev/null; then PY="$c"; break; fi; done
[ -n "$PY" ] || { echo "ATURAT: cap Python"; exit 3; }
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=${OPENBLAS_NUM_THREADS:-6}
cr() { local nom=$1; shift; /usr/bin/time -l -o $L/temps_$nom.txt "$@" > $L/$nom.log 2>&1 || { echo "ATURAT a $nom ($L/$nom.log)"; tail -5 $L/$nom.log; exit 7; }
  printf "%s\t%s s\t%s GB\n" $nom "$(awk '/ real /{print $1; exit}' $L/temps_$nom.txt)" "$(awk '/maximum resident set size/{printf "%.1f", $1/1073741824}' $L/temps_$nom.txt)" | tee -a $L/TEMPS.tsv; }
[ -f $R/compost_flat2d_v3.npy ] || cr c1 $PY -B $T2/c1_compost_v107_mascares.py 4-RESULTATS/v108_20260926/cadena/flat2d_v3/estat_v108 $R/compost_flat2d_v3.npy
[ -f $R/diag/D2_PROVA_AB_v3.json ] || cr d2_v3 $PY -B $T/d2_prova_AB.py --comps v3 --bandes 2-6,6-18,18-54,54-160 --etiqueta _v3
[ -f $R/diag/D3_PROVA_VS_v3.json ] || cr d3_v3 $PY -B $T/d3_prova_VS.py --comps v3 --etiqueta _v3
for q in ${=${1:-T S K B F P L V Q Q2 Q3}}; do cr m1_$q $PY -B $T/m1_mesura_flat2d_v3.py $q; done
cr v1_vistes $PY -B $T/v1_vistes_flat2d_v3.py
cr v2_vistes_sensor $PY -B $T/v2_vistes_sensor_v3.py
echo MESURES_FLAT2D_V3_FETES
