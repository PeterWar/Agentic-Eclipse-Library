#!/bin/zsh
# corre_recepta_flat2d_v4.sh · LA C DE LA v4, pas a pas (la tirada que es va fer el 27-09 al matí). Des de l'arrel, amb el claim viu.
#   1 · f0 (components + controls: la v2 i la v3 bit a bit)       2 · g1 (la porta de la v3 refeta + la plantilla de taca)
#   3 · h1 --zero + f0 --etiqueta a0: la C «a0» (textura i fons de la petjada aplicats, taca no)
#   4 · apilats «a0» (b2 de la v2, sense canvis; la Vixen passa de 16 GB: sol)      5 · g2 sobre «a0»: la taca que QUEDA a la dada (r0)
#   6 · h1 --dada a0: la â encongida (bayesià jeràrquic, grup de rebutjades)     7 · f0 --encongida: les C finals (VIXEN_, SONYTOT_A_, SONYTOT_B_flat2d_v4.npz)
# Després: corre_fonts_flat2d_v4.sh → corre_cadena_flat2d_v4.sh → corre_mesures_flat2d_v4.sh. Cada pas se salta si la seva sortida ja existeix.
# ⛔ No l'editis mentre corre.
set -e
cd "$(dirname "$0")/../../../.."
T=3-RECERCA/tools/v108_20260926/flat2d_v4; T2=3-RECERCA/tools/v108_20260926/flat2d_v2; R=4-RESULTATS/v108_20260926/flat2d_v4; F=$R/flat2d; L=$R/logs; mkdir -p $L
PY=""; for c in "${V108_PY:-}" "$HOME/.venvs/eines-ia-py312/bin/python" "$(command -v python3 2>/dev/null || true)" /opt/homebrew/bin/python3.12; do
  if [ -n "$c" ] && [ -x "$c" ] && "$c" -c "import numpy, scipy, cv2, rawpy, astropy" 2>/dev/null; then PY="$c"; break; fi; done
[ -n "$PY" ] || { echo "ATURAT: cap Python amb numpy/scipy/opencv/rawpy/astropy"; exit 3; }
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=${OPENBLAS_NUM_THREADS:-6}
cr() { local nom=$1; shift; /usr/bin/time -l -o $L/temps_$nom.txt "$@" > $L/$nom.log 2>&1 || { echo "ATURAT a $nom ($L/$nom.log)"; tail -5 $L/$nom.log; exit 7; }
  printf "%s\t%s s\t%s GB\n" $nom "$(awk '/ real /{print $1; exit}' $L/temps_$nom.txt)" "$(awk '/maximum resident set size/{printf "%.1f", $1/1073741824}' $L/temps_$nom.txt)" | tee -a $L/TEMPS.tsv; }
for TR in VIXEN SONYTOT; do [ -f $F/${TR}_components_v4.npz ] || cr f0_components_$TR $PY -B $T/f0_flat2d_v4.py $TR; done
for TR in VIXEN SONYTOT; do [ -f $F/G1_PORTA_V4_$TR.json ] || cr g1_$TR $PY -B $T/g1_porta_v4.py $TR; done
for TR in VIXEN SONYTOT; do
  [ -f $F/H1_ENCONGIDA_ZERO_$TR.json ] || cr h1_zero_$TR $PY -B $T/h1_encongiment.py $TR --dada control --zero
  [ -f $F/${TR}_flat2d_v4_a0_REBUT.json ] || cr f0_a0_$TR $PY -B $T/f0_flat2d_v4.py $TR --encongida $F/H1_ENCONGIDA_ZERO_$TR.json --etiqueta a0; done
O=$R/prova_a0/apilats
[ -f $O/vixen_REBUT.json ] || cr a0_b2_vixen env FLAT2D_VIXEN=$F/VIXEN_flat2d_v4_a0.npz $PY -B $T2/b2_flat2d_v2.py vixen --flat2d si --out $O
[ -f $O/sony_A_REBUT.json ] || cr a0_b2_sony_A env FLAT2D_SONY=$F/SONYTOT_A_flat2d_v4_a0.npz $PY -B $T2/b2_flat2d_v2.py sony_A --flat2d si --out $O
[ -f $O/sony_B_REBUT.json ] || cr a0_b2_sony_B env FLAT2D_SONY=$F/SONYTOT_B_flat2d_v4_a0.npz $PY -B $T2/b2_flat2d_v2.py sony_B --flat2d si --out $O
if [ ! -f $R/G2_RESIDU_PORTA_a0.json ]; then for TR in VIXEN SONYTOT; do cr g2_a0_$TR $PY -B $T/g2_residu_porta_v4.py $TR control,v3,a0 a0; done; fi
for TR in VIXEN SONYTOT; do
  [ -f $F/H1_ENCONGIDA_$TR.json ] || cr h1_a0_$TR $PY -B $T/h1_encongiment.py $TR --dada a0
  [ -f $F/${TR}_flat2d_v4_REBUT.json ] || cr f0_C_$TR $PY -B $T/f0_flat2d_v4.py $TR --encongida $F/H1_ENCONGIDA_$TR.json; done
echo RECEPTA_FLAT2D_V4_FETA
