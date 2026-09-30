#!/bin/zsh
# corre_recepta_flat2d_v5.sh · LA C DE LA v5 (V108). Des de l'arrel, amb el claim viu. Cada pas se salta si la seva sortida ja existeix.
#   f0_flat2d_v5.py VIXEN   · la C de la v4 (control bit a bit) amb la regla de la POLS MOGUDA a les 5 estructures de l'encàrrec
#   f0_flat2d_v5.py SONYTOT · la C de la v4 refeta (control bit a bit): a la Sony la v5 no canvia res (SONYTOT_A_ i SONYTOT_B_flat2d_v5.npz = v4)
# L'encongiment (H1_ENCONGIDA) i la porta són els de la v4, sense tornar-los a mesurar. Després: corre_fonts_flat2d_v5.sh.
# ⛔ No l'editis mentre corre.
set -e
cd "$(dirname "$0")/../../../.."
T=3-RECERCA/tools/v108_20260926/flat2d_v5; R=4-RESULTATS/v108_20260926/flat2d_v5; F=$R/flat2d; L=$R/logs; mkdir -p $L $F
PY=""; for c in "${V108_PY:-}" "$HOME/.venvs/eines-ia-py312/bin/python" "$(command -v python3 2>/dev/null || true)" /opt/homebrew/bin/python3.12; do
  if [ -n "$c" ] && [ -x "$c" ] && "$c" -c "import numpy, scipy, cv2, rawpy, astropy" 2>/dev/null; then PY="$c"; break; fi; done
[ -n "$PY" ] || { echo "ATURAT: cap Python amb numpy/scipy/opencv/rawpy/astropy"; exit 3; }
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=${OPENBLAS_NUM_THREADS:-6}
cr() { local nom=$1; shift; /usr/bin/time -l -o $L/temps_$nom.txt "$@" > $L/$nom.log 2>&1 || { echo "ATURAT a $nom ($L/$nom.log)"; tail -5 $L/$nom.log; exit 7; }
  printf "%s\t%s s\t%s GB\n" $nom "$(awk '/ real /{print $1; exit}' $L/temps_$nom.txt)" "$(awk '/maximum resident set size/{printf "%.1f", $1/1073741824}' $L/temps_$nom.txt)" | tee -a $L/TEMPS.tsv; }
for TR in VIXEN SONYTOT; do [ -f $F/${TR}_flat2d_v5_REBUT.json ] || cr f0_C_$TR $PY -B $T/f0_flat2d_v5.py $TR; done
echo RECEPTA_FLAT2D_V5_FETA
