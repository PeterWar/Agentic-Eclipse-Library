#!/bin/zsh
# corre_mesures_flat2d_v4.sh · Totes les mesures abans/després de la variant flat2d_v4 (control = la V107; la v3 al costat). Només lectura del projecte;
# escriu a 4-RESULTATS/v108_20260926/flat2d_v4/. CÒPIA de corre_mesures_flat2d_v3.sh amb els guions de la v4 i quatre mesures més:
#   g2 (quant en queda de cada estructura després de corregir, amb el cel anul·lat), m2 (taques noves i pics del control amb el cel anul·lat, i
#   l'energia σ4–40 del compost dins de les petjades contra el voltant), m4 (energia del compost per bandes i anells: el que la v3 no declarava).
# En sèrie (memòria màxima ~12 GB). ⛔ No l'editis mentre corre.
set -e
cd "$(dirname "$0")/../../../.."
T=3-RECERCA/tools/v108_20260926/flat2d_v4; T2=3-RECERCA/tools/v108_20260926/flat2d_v2; R=4-RESULTATS/v108_20260926/flat2d_v4; L=$R/logs
PY=""; for c in "${V108_PY:-}" "$HOME/.venvs/eines-ia-py312/bin/python" "$(command -v python3 2>/dev/null || true)"; do
  if [ -n "$c" ] && [ -x "$c" ] && "$c" -c "import numpy, scipy, cv2, psd_tools, matplotlib" 2>/dev/null; then PY="$c"; break; fi; done
[ -n "$PY" ] || { echo "ATURAT: cap Python"; exit 3; }
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=${OPENBLAS_NUM_THREADS:-6}
cr() { local nom=$1; shift; /usr/bin/time -l -o $L/temps_$nom.txt "$@" > $L/$nom.log 2>&1 || { echo "ATURAT a $nom ($L/$nom.log)"; tail -5 $L/$nom.log; exit 7; }
  printf "%s\t%s s\t%s GB\n" $nom "$(awk '/ real /{print $1; exit}' $L/temps_$nom.txt)" "$(awk '/maximum resident set size/{printf "%.1f", $1/1073741824}' $L/temps_$nom.txt)" | tee -a $L/TEMPS.tsv; }
[ -f $R/compost_flat2d_v4.npy ] || cr c1 $PY -B $T2/c1_compost_v107_mascares.py 4-RESULTATS/v108_20260926/cadena/flat2d_v4/estat_v108 $R/compost_flat2d_v4.npy
[ -f $R/G2_RESIDU_PORTA.json ] || { cr g2_VIXEN $PY -B $T/g2_residu_porta_v4.py VIXEN control,v3,a0,v4; cr g2_SONYTOT $PY -B $T/g2_residu_porta_v4.py SONYTOT control,v3,a0,v4; }
[ -f $R/diag/D2_PROVA_AB_v4.json ] || cr d2_v4 $PY -B $T/d2_prova_AB_v4.py --comps v4 --bandes 2-6,6-18,18-54,54-160 --etiqueta _v4
[ -f $R/diag/D3_PROVA_VS_v4.json ] || cr d3_v4 $PY -B $T/d3_prova_VS_v4.py --comps v4 --etiqueta _v4
for q in ${=${1:-T S K B F P L V Q Q2 Q3}}; do cr m1_$q $PY -B $T/m1_mesura_flat2d_v4.py $q; done
cr m2 $PY -B $T/m2_taques_forats_v4.py A B
cr m5 $PY -B $T/m5_pics_control_v4.py
cr m6 $PY -B $T/m6_cura_petjades_v4.py
cr m4_compost $PY -B $T/m4_energia_compost_v4.py compost
cr v1_vistes $PY -B $T/v1_vistes_flat2d_v4.py
cr r1_resum $PY -B $T/r1_resum_flat2d_v4.py
echo MESURES_FLAT2D_V4_FETES
