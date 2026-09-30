#!/bin/zsh
# corre_mesures_flat2d_v5.sh · Les mesures de la variant flat2d_v5 (V108). Només lectura del projecte (i de la Paperera, per als intermedis de la v4);
# escriu a 4-RESULTATS/v108_20260926/flat2d_v5/. En sèrie (memòria màxima ~12 GB). ⛔ No l'editis mentre corre.
#   c1 · el compost amb les màscares de la V107 (el guió de la v2, sense canvis)
#   m7 · la POLS MOGUDA: prova s amb el cel anul·lat (Vixen − Sony del control) i nuls a la mateixa imatge, σ1–4 / 4–40 / 2–60 / 10–60;
#        i la Sony (declaració, sense canvis) per bandes fines
#   m9 · la v5 contra la v4 a cada etapa (fonts, cadena, compost): bit a bit fora dels llocs de l'encàrrec?
#   m8 · el compost a les petjades, la protuberància (franja, base, filtres, compost) i Brno a 1,02–1,5 R☉
#   v1 · les vistes del llenç sencer
set -e
cd "$(dirname "$0")/../../../.."
T=3-RECERCA/tools/v108_20260926/flat2d_v5; T2=3-RECERCA/tools/v108_20260926/flat2d_v2; R=4-RESULTATS/v108_20260926/flat2d_v5; L=$R/logs; mkdir -p $L
PY=""; for c in "${V108_PY:-}" "$HOME/.venvs/eines-ia-py312/bin/python" "$(command -v python3 2>/dev/null || true)"; do
  if [ -n "$c" ] && [ -x "$c" ] && "$c" -c "import numpy, scipy, cv2, psd_tools" 2>/dev/null; then PY="$c"; break; fi; done
[ -n "$PY" ] || { echo "ATURAT: cap Python"; exit 3; }
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=${OPENBLAS_NUM_THREADS:-6}
cr() { local nom=$1; shift; /usr/bin/time -l -o $L/temps_$nom.txt "$@" > $L/$nom.log 2>&1 || { echo "ATURAT a $nom ($L/$nom.log)"; tail -5 $L/$nom.log; exit 7; }
  printf "%s\t%s s\t%s GB\n" $nom "$(awk '/ real /{print $1; exit}' $L/temps_$nom.txt)" "$(awk '/maximum resident set size/{printf "%.1f", $1/1073741824}' $L/temps_$nom.txt)" | tee -a $L/TEMPS.tsv; }
[ -f $R/compost_flat2d_v5.npy ] || cr c1 $PY -B $T2/c1_compost_v107_mascares.py 4-RESULTATS/v108_20260926/cadena/flat2d_v5/estat_v108 $R/compost_flat2d_v5.npy
[ -f $R/M7_POLS_MOGUDA.json ] || cr m7 $PY -B $T/m7_pols_moguda_v5.py
[ -f $L/m9_fonts.log ] || cr m9_fonts $PY -B $T/m9_v5_contra_v4.py fonts
[ -f $L/m9_cadena.log ] || cr m9_cadena $PY -B $T/m9_v5_contra_v4.py cadena
[ -f $L/m9_compost.log ] || cr m9_compost $PY -B $T/m9_v5_contra_v4.py compost
[ -f $R/M8_COMPOST_PROTUBERANCIA.json ] || cr m8 $PY -B $T/m8_compost_i_protuberancia_v5.py ABC
[ -f $R/VISTA_3_apilat_vixen_v5_sobre_v4.png ] || cr v1_vistes $PY -B $T/v1_vistes_flat2d_v5.py
echo MESURES_FLAT2D_V5_FETES
