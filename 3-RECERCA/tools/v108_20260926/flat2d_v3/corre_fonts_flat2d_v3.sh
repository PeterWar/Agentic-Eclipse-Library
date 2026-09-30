#!/bin/zsh
# corre_fonts_flat2d_v3.sh · Les FONTS de la variant flat2d_v3 (V108): apilats (cada apuntament de la Sony amb la seva C, per la porta per
# estructura), fotogrames de la caixa lunar i fusió CONGELADA, amb els guions de la v2 SENSE CANVIS (b2, a9b, b3d4 de flat2d_v2: l'únic canvi
# respecte de la v2 és el fitxer de C, que s'hi passa per FLAT2D_VIXEN / FLAT2D_SONY). Els controls bit a bit d'aquests guions (sense C = la
# cadena) són els de la v2 (flat2d_v2/apilats_control, limb_frames_control, fusio_control): els guions són els mateixos (el SHA es desa).
# ⛔ No l'editis mentre corre (el zsh llegeix el fitxer a trossos).
# Ús (des de l'arrel del projecte): zsh 3-RECERCA/tools/v108_20260926/flat2d_v3/corre_fonts_flat2d_v3.sh
set -e
cd "$(dirname "$0")/../../../.."
T2=3-RECERCA/tools/v108_20260926/flat2d_v2; R=4-RESULTATS/v108_20260926/flat2d_v3; L=$R/logs; F=$R/flat2d; mkdir -p $L
PY=""; for c in "${V108_PY:-}" "$HOME/.venvs/eines-ia-py312/bin/python" "$(command -v python3 2>/dev/null || true)" /opt/homebrew/bin/python3.12; do
  if [ -n "$c" ] && [ -x "$c" ] && "$c" -c "import numpy, scipy, cv2, rawpy, astropy" 2>/dev/null; then PY="$c"; break; fi; done
[ -n "$PY" ] || { echo "ATURAT: cap Python amb numpy/scipy/opencv/rawpy/astropy"; exit 3; }
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=${OPENBLAS_NUM_THREADS:-6}
cr() { local nom=$1; shift; /usr/bin/time -l -o $L/temps_$nom.txt "$@" > $L/$nom.log 2>&1 || { echo "ATURAT a $nom ($L/$nom.log)"; tail -5 $L/$nom.log; exit 7; }
  printf "%s\t%s s\t%s GB\n" $nom "$(awk '/ real /{print $1; exit}' $L/temps_$nom.txt)" "$(awk '/maximum resident set size/{printf "%.1f", $1/1073741824}' $L/temps_$nom.txt)" | tee -a $L/TEMPS.tsv; }
for f in VIXEN_flat2d_v3.npz SONYTOT_A_flat2d_v3.npz SONYTOT_B_flat2d_v3.npz; do [ -f $F/$f ] || { echo "ATURAT: falta $F/$f (f0_flat2d_v3.py amb --porta)"; exit 2; }; done
shasum -a 256 $T2/b2_flat2d_v2.py $T2/a9b_flat2d_v2.py $T2/b3d4_flat2d_v2.py > $R/GUIONS_SHA_FONTS.txt
# 1 · apilats: la Vixen amb la seva C; la Sony A i la Sony B, cadascuna amb la C de la seva porta
if [ ! -f $R/apilats/vixen_REBUT.json ]; then cr b2_vixen env FLAT2D_VIXEN=$F/VIXEN_flat2d_v3.npz $PY -B $T2/b2_flat2d_v2.py vixen --flat2d si --out $R/apilats; fi
if [ ! -f $R/apilats/sony_A_REBUT.json ]; then cr b2_sony_A env FLAT2D_SONY=$F/SONYTOT_A_flat2d_v3.npz $PY -B $T2/b2_flat2d_v2.py sony_A --flat2d si --out $R/apilats; fi
if [ ! -f $R/apilats/sony_B_REBUT.json ]; then cr b2_sony_B env FLAT2D_SONY=$F/SONYTOT_B_flat2d_v3.npz $PY -B $T2/b2_flat2d_v2.py sony_B --flat2d si --out $R/apilats; fi
# 2 · fotogrames de la caixa lunar (Vixen) amb la mateixa C
if [ ! -f $R/limb_frames_flat2d/COMPLETE.json ]; then cr a9b_flat2d env FLAT2D_VIXEN=$F/VIXEN_flat2d_v3.npz $PY -B $T2/a9b_flat2d_v2.py --flat2d si --out $R/limb_frames_flat2d; fi
# 3 · fusió CONGELADA a la del control (la de la V98–V107)
C98=4-RESULTATS/v98_20260925/cadena_v98
if [ ! -f $R/fusio/COMPLETE.json ]; then
  cr b3d4_flat2d $PY -B $T2/b3d4_flat2d_v2.py --out $R/fusio --vixen $R/apilats/vixen_total.npy --sony-a $R/apilats/sony_A_total.npy --sony-b $R/apilats/cau/sony_B_total_v42.npy --b3-sense-residu-local --congela $C98/b3; fi
echo FONTS_FLAT2D_V3_FETES
