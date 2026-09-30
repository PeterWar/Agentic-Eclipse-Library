#!/bin/zsh
# d1_apilats_components.sh (V108, flat2d_v3, DIAGNOSI) · Apilats Sony A i B amb cada component de C (d0_components_C.py), amb el b2 de la v2
# (l'únic canvi respecte del control és C; ondulació i pesos, els de la cadena). En sèrie (12–14 GB cadascun).
# Ús (des de l'arrel): zsh 3-RECERCA/tools/v108_20260926/flat2d_v3/d1_apilats_components.sh [components] [grups]
set -e
cd "$(dirname "$0")/../../../.."
R=4-RESULTATS/v108_20260926/flat2d_v3/diag; L=4-RESULTATS/v108_20260926/flat2d_v3/logs; mkdir -p $L
B2=3-RECERCA/tools/v108_20260926/flat2d_v2/b2_flat2d_v2.py
PY=""; for c in "${V108_PY:-}" "$HOME/.venvs/eines-ia-py312/bin/python" "$(command -v python3 2>/dev/null || true)"; do
  if [ -n "$c" ] && [ -x "$c" ] && "$c" -c "import numpy, scipy, cv2, rawpy, astropy" 2>/dev/null; then PY="$c"; break; fi; done
[ -n "$PY" ] || { echo "ATURAT: cap Python"; exit 3; }
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=${OPENBLAS_NUM_THREADS:-6}
COMPS=(${=${1:-Lf Lg Kf Kg}}); GRUPS=(${=${2:-sony_A sony_B}})
for c in $COMPS; do for g in $GRUPS; do
  O=$R/apilats_$c; [ -f $O/${g}_REBUT.json ] && continue
  env FLAT2D_SONY=$R/components/SONYTOT_$c.npz /usr/bin/time -l -o $L/temps_d1_${c}_$g.txt $PY -B $B2 $g --flat2d si --out $O > $L/d1_${c}_$g.log 2>&1 || { echo "ATURAT $c $g"; tail -3 $L/d1_${c}_$g.log; exit 7; }
  printf "d1_%s_%s\t%s s\t%s GB\n" $c $g "$(awk '/ real /{print $1; exit}' $L/temps_d1_${c}_$g.txt)" "$(awk '/maximum resident set size/{printf "%.1f", $1/1073741824}' $L/temps_d1_${c}_$g.txt)" | tee -a $L/TEMPS.tsv
done; done
echo D1_FET
