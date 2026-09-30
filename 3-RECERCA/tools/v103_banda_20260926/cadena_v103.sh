#!/bin/zsh
# cadena_v103.sh · LA CADENA DE LA V103 (banda del limbe), Claude 26-09-2026 matinada. Parteix de la V99/V101 (limb_frames comuna, fonts d4 de la V98,
# silueta d21) i només canvia la franja arran del limbe: a3d = a3c + règim de banda (fotogrames de l'instant a D_real ≥ lo, T mesurada) on el
# règim net no arriba. Cada variant viu a 4-RESULTATS/v103_banda_20260926/<variant>/ amb un CONFIG.env (A3C_RAMPES, A3C_SILUETA, A3D_BANDA).
# Passos: 3 a3d · 4 linealitzada · 5 base · 6 filtres · 7 estat · 8 jutges (j14, j15 contra la V99, j17 banda) · 9 PSB de pas (des de la V101) ·
#         10 Photoshop (desa com a còpia) + portes + làmines V101/V103 (només la variant lliurada, LLIURA=<variant>).
# ⛔ «des_del_pas» vol dir DES D'AQUEST PAS FINS AL FINAL. Cada pas se salta si la seva sortida ja existeix.
# Ús: zsh cadena_v103.sh <variant> [des_del_pas]        (LLIURA=A zsh cadena_v103.sh A 9 per muntar i desar)
set -e
cd "$(dirname "$0")/../../.."
T=3-RECERCA/tools/v103_banda_20260926; T99=3-RECERCA/tools/v99_banda_20260925; T98=3-RECERCA/tools/v98_20260925; T97=3-RECERCA/tools/v97_refundacio_20260924
R8=4-RESULTATS/v98_20260925; R9=4-RESULTATS/v99_banda_20260925; R0=4-RESULTATS/v103_banda_20260926; VAR=${1:?variant}; R=$R0/$VAR
PY=""; for c in "$HOME/.venvs/eines-ia-py312/bin/python" "$(command -v python3)"; do
  if [ -x "$c" ] && "$c" -c "import numpy, scipy, cv2, numexpr, psd_tools, tifffile" 2>/dev/null; then PY="$c"; break; fi; done
[ -n "$PY" ] || { echo "ATURAT: cap Python amb numpy/scipy/opencv/numexpr/psd-tools/tifffile"; exit 3; }
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=4
[ -f $R/CONFIG.env ] || { echo "ATURAT: falta $R/CONFIG.env"; exit 2; }
source $R/CONFIG.env; export A3C_RAMPES A3C_SILUETA A3D_BANDA
DES=${2:-0}; pas() { [ "$DES" -le "$1" ]; }
FR=$R/lineal_v103_franja/A3C_franja_silueta.npz
if pas 3 && [ ! -f $FR ]; then
  mkdir -p $R/lineal_v103_franja; cp -c $R8/lineal_v98_franja/A2_GEOMETRIA.json $R8/lineal_v98_franja/A2_geometria.npz $R/lineal_v103_franja/
  A3B_LF=$R8/cadena_raw/limb_frames_comuna V97_SORT=$R/lineal_v103_franja V97_FONTS=$R8/cadena_v98/d4/products/sources $PY -B $T/a3d_franja_banda.py > $R/a3d.log 2>&1; fi
if pas 4 && [ ! -f $R/lineal_v103/LINEAL_REBUT.json ]; then $PY -B $T97/f2_lineal_v97.py $R8/cadena_v98/d4/products/sources $FR $R/lineal_v103 > $R/f2.log 2>&1; fi
if pas 5 && [ ! -f $R/base_v103/base_v103_final_u16.npy ]; then
  mkdir -p $R/base_v103; $PY -B $T97/f2b_base.py $R/lineal_v103/fusion_starless.npy $R/lineal_v103/support.npy $R/base_v103/base_v103_u16.npy --espai assigna > $R/f2b.log 2>&1
  $PY -B $T97/f2c_base_limbe.py $R/base_v103/base_v103_u16.npy $R/base_v103/base_v103_final_u16.npy > $R/f2c.log 2>&1; fi
if pas 6 && [ ! -f $R/filtres_v103/F3_E2.json ]; then
  mkdir -p $R/filtres_v103
  for e in E1 E6 E4 E3 E2; do V97_SORT=$R/filtres_v103 V97_FONTS=$R/lineal_v103 V98_FRANJA=$FR $PY -B $T98/f3_filtres_v98.py $e > $R/filtres_v103/f3_$e.log 2>&1 & done; wait
  for e in E1 E6 E4 E3 E2; do [ -f $R/filtres_v103/F3_$e.json ] || { echo "ATURAT: l'etapa $e dels filtres ha fallat"; exit 6; }; done; fi
if pas 7 && [ ! -f $R/estat_v103/CAPES_V98.json ]; then $PY -B $T98/r3_estat_v98.py $R/filtres_v103/filtres $R/estat_v103 $R/base_v103/base_v103_final_u16.npy > $R/r3.log 2>&1; fi
if pas 8; then
  $PY -B $T98/j14_anells_lupa.py $R/J14_V103.json V103=$R/filtres_v103/filtres > $R/j14.log 2>&1
  $PY -B $T98/j14_anells_lupa.py $R/J14_V103_suportV99.json V103=$R/filtres_v103/filtres V99=$R9/B/filtres_v99/filtres --suport $R9/B/lineal_v99_franja/A3C_franja_silueta.npz > $R/j14s.log 2>&1
  mkdir -p $R/compost; $PY -B $T98/j15_compost_limbe.py $R9/B/estat_v99 $R/estat_v103 $R/compost/v99_v103 > $R/j15.log 2>&1
  $PY -B $T/j17_banda.py $FR $R9/B/lineal_v99_franja/A3C_franja_silueta.npz $R/J17_BANDA.json > $R/j17.log 2>&1; fi
if pas 9 && [ "$VAR" = "${LLIURA:-}" ] && [ ! -f $R/V103_stage.psb ] && [ ! -f 1-PHOTOSHOP/V103.psb ]; then $PY -B $T/b2_munta_v103.py $R/estat_v103 > $R/b2.log 2>&1; fi
if pas 10 && [ "$VAR" = "${LLIURA:-}" ]; then
  [ -f 1-PHOTOSHOP/V103.psb ] && { echo "ATURAT: 1-PHOTOSHOP/V103.psb ja existeix (mai no se sobreescriu)"; exit 10; }
  zsh $T/desa_natiu.sh $R/V103_stage.psb 1-PHOTOSHOP/V103.psb $R/vistes
  $PY $T97/p6_compost_fusionat.py 1-PHOTOSHOP/V103.psb $R/vistes/V103_llenc_sencer.tif | tee $R/P6_COMPOST.txt
  bash 3-RECERCA/tools/capes_totals_v14/porta_photoshop.sh "$PWD/1-PHOTOSHOP/V103.psb" 2>&1 | tail -1 | tee $R/PORTA.txt
  shasum -a 256 1-PHOTOSHOP/V103.psb | tee $R/SHA_V103.txt
  $PY -B $T/v1_verifica_v103.py $R/estat_v103 $R/V1_VERIFICA_V103.json | tail -1
  $PY $T/r5_natiu_v101_v103.py 4-RESULTATS/v100_detall_20260925/final_V101/vistes/V100_lluna.tif $R/vistes/V103_lluna.tif $R/laminas; fi
echo CADENA_V103_${VAR}_FETA
