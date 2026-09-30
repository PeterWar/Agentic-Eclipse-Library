#!/bin/zsh
# corre_fonts_flat2d_v2.sh · Les FONTS de la variant flat2d_v2 (V108): apilats, fotogrames de la caixa lunar, fusió congelada i franja congelada,
# amb els controls que demostren que cada pas és neutre sense el flat 2D. Després, la cadena: cadena_v108.sh flat2d_v2 (vegeu INFORME.md).
# Ús (des de l'arrel del projecte): zsh 3-RECERCA/tools/v108_20260926/flat2d_v2/corre_fonts_flat2d_v2.sh [pas_inicial]
set -e
cd "$(dirname "$0")/../../../.."
T=3-RECERCA/tools/v108_20260926/flat2d_v2; R=4-RESULTATS/v108_20260926/flat2d_v2; L=$R/logs; mkdir -p $L
PY=""; for c in "${V108_PY:-}" "$HOME/.venvs/eines-ia-py312/bin/python" "$(command -v python3 2>/dev/null || true)" /opt/homebrew/bin/python3.12; do
  if [ -n "$c" ] && [ -x "$c" ] && "$c" -c "import numpy, scipy, cv2, rawpy, astropy" 2>/dev/null; then PY="$c"; break; fi; done
[ -n "$PY" ] || { echo "ATURAT: cap Python amb numpy/scipy/opencv/rawpy/astropy"; exit 3; }
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=${OPENBLAS_NUM_THREADS:-6}
DES=${1:-1}; pas() { [ "$DES" -le "$1" ]; }
cr() { local nom=$1; shift; /usr/bin/time -l -o $L/temps_$nom.txt "$@" > $L/$nom.log 2>&1 || { echo "ATURAT a $nom ($L/$nom.log)"; tail -5 $L/$nom.log; exit 7; }
  printf "%s\t%s s\t%s GB\n" $nom "$(awk '/ real /{print $1; exit}' $L/temps_$nom.txt)" "$(awk '/maximum resident set size/{printf "%.1f", $1/1073741824}' $L/temps_$nom.txt)" | tee -a $L/TEMPS.tsv; }
F=$R/flat2d; [ -f $F/VIXEN_flat2d_v2.npz ] && [ -f $F/SONYTOT_flat2d_v2.npz ] || { echo "ATURAT: falten els flats 2D (f0_flat2d_v2.py)"; exit 2; }
# 1 · controls dels apilats Sony (la correcció d'ondulació amb el flat original ha de ser neutra: bit a bit amb la cadena)
if pas 1 && [ ! -f $R/apilats_control/sony_B_REBUT.json ]; then
  cr b2_ctrl_sony_A $PY -B $T/b2_flat2d_v2.py sony_A --flat2d no --out $R/apilats_control
  cr b2_ctrl_sony_B $PY -B $T/b2_flat2d_v2.py sony_B --flat2d no --out $R/apilats_control; fi
# 2 · apilats amb el flat 2D
if pas 2 && [ ! -f $R/apilats/sony_B_REBUT.json ]; then
  cr b2_vixen $PY -B $T/b2_flat2d_v2.py vixen --flat2d si --out $R/apilats
  cr b2_sony_A $PY -B $T/b2_flat2d_v2.py sony_A --flat2d si --out $R/apilats
  cr b2_sony_B $PY -B $T/b2_flat2d_v2.py sony_B --flat2d si --out $R/apilats; fi
# 3 · fotogrames de la caixa lunar amb el flat 2D (i el control, que ha de ser bit a bit el de la cadena)
if pas 3 && [ ! -f $R/limb_frames_control/COMPLETE.json ]; then cr a9b_ctrl $PY -B $T/a9b_flat2d_v2.py --flat2d no --out $R/limb_frames_control; fi
if pas 3 && [ ! -f $R/limb_frames_flat2d/COMPLETE.json ]; then cr a9b_flat2d $PY -B $T/a9b_flat2d_v2.py --flat2d si --out $R/limb_frames_flat2d; fi
# 4 · fusió CONGELADA: control (entrades del control → ha de ser bit a bit la fusió i les fonts del control) i flat 2D
C98=4-RESULTATS/v98_20260925/cadena_v98; CR=4-RESULTATS/v97_refundacio_20260924/cadena_raw
VIX0=4-RESULTATS/v97_refundacio_20260924/proves_apilat/vixen_comuna_taula_original/vixen_total.npy
if pas 4 && [ ! -f $R/fusio_control/COMPLETE.json ]; then
  cr b3d4_ctrl $PY -B $T/b3d4_flat2d_v2.py --out $R/fusio_control --vixen $VIX0 --sony-a $CR/b2_sony_A/cau/sony_A_total_v36.npy --sony-b $CR/b2_sony_B/cau/sony_B_total_v42.npy --b3-sense-residu-local --congela $C98/b3; fi
if pas 4 && [ ! -f $R/fusio/COMPLETE.json ]; then
  cr b3d4_flat2d $PY -B $T/b3d4_flat2d_v2.py --out $R/fusio --vixen $R/apilats/vixen_total.npy --sony-a $R/apilats/sony_A_total.npy --sony-b $R/apilats/cau/sony_B_total_v42.npy --b3-sense-residu-local --congela $C98/b3; fi
echo FONTS_FLAT2D_V2_FETES
