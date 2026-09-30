#!/bin/zsh
# cadena_v99.sh · LA CADENA DE LA V99 (banda), Claude 25-09-2026 vespre. Parteix de la V98 (limb_frames de finestra comuna, fonts d4 sense el
# residu local A→B) i només canvia la franja arran del limbe: a3c = selecció física per fotograma amb la distància al limbe REAL (silueta
# comuna d19) i, opcionalment, la transmissió de vora comuna (TCORR). Cada variant viu a 4-RESULTATS/v99_banda_20260925/<variant>/ amb un
# CONFIG.env (A3C_RAMPES, A3C_TCORR, A3C_SILUETA). Cada pas se salta si la seva sortida ja existeix.
# Passos: 2 silueta real (d17, d18, d21; comuna a totes les variants) · 3 a3c · 4 linealitzada · 5 base · 6 filtres · 7 estat · 8 jutges ·
#         9 PSB de pas · 10 Photoshop (desa com a còpia) + portes + verificació (només la variant lliurada, B).
# ⛔ «des_del_pas» vol dir DES D'AQUEST PAS FINS AL FINAL.
# Ús: zsh cadena_v99.sh <variant> [des_del_pas]
set -e
cd "$(dirname "$0")/../../.."
T=3-RECERCA/tools/v99_banda_20260925; T98=3-RECERCA/tools/v98_20260925; T97=3-RECERCA/tools/v97_refundacio_20260924
R8=4-RESULTATS/v98_20260925; R0=4-RESULTATS/v99_banda_20260925; VAR=${1:?variant}; R=$R0/$VAR
PY=""; for c in "$HOME/.venvs/eines-ia-py312/bin/python" "$(command -v python3)"; do
  if [ -x "$c" ] && "$c" -c "import numpy, scipy, cv2, numexpr, psd_tools, tifffile" 2>/dev/null; then PY="$c"; break; fi; done
[ -n "$PY" ] || { echo "ATURAT: cap Python amb numpy/scipy/opencv/numexpr/psd-tools/tifffile"; exit 3; }
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=4
[ -f $R/CONFIG.env ] || { echo "ATURAT: falta $R/CONFIG.env"; exit 2; }
source $R/CONFIG.env; export A3C_RAMPES A3C_TCORR A3C_SILUETA
DES=${2:-0}; pas() { [ "$DES" -le "$1" ]; }
FR=$R/lineal_v99_franja/A3C_franja_silueta.npz
if pas 2 && [ ! -f $R0/D21_silueta_o2.npz ]; then
  $PY -B $T/d17_vora_per_fotograma.py > $R0/d17.log 2>&1; $PY -B $T/d18_limbe_real_gradient.py > $R0/d18.log 2>&1; $PY -B $T/d21_silueta_o2_exclusio.py > $R0/d21.log 2>&1; fi
if pas 3 && [ ! -f $FR ]; then
  mkdir -p $R/lineal_v99_franja; cp -c $R8/lineal_v98_franja/A2_GEOMETRIA.json $R8/lineal_v98_franja/A2_geometria.npz $R/lineal_v99_franja/
  A3B_LF=$R8/cadena_raw/limb_frames_comuna V97_SORT=$R/lineal_v99_franja V97_FONTS=$R8/cadena_v98/d4/products/sources $PY -B $T/a3c_franja_silueta.py > $R/a3c.log 2>&1; fi
if pas 4 && [ ! -f $R/lineal_v99/LINEAL_REBUT.json ]; then $PY -B $T97/f2_lineal_v97.py $R8/cadena_v98/d4/products/sources $FR $R/lineal_v99 > $R/f2.log 2>&1; fi
if pas 5 && [ ! -f $R/base_v99/base_v99_final_u16.npy ]; then
  mkdir -p $R/base_v99; $PY -B $T97/f2b_base.py $R/lineal_v99/fusion_starless.npy $R/lineal_v99/support.npy $R/base_v99/base_v99_u16.npy --espai assigna > $R/f2b.log 2>&1
  $PY -B $T97/f2c_base_limbe.py $R/base_v99/base_v99_u16.npy $R/base_v99/base_v99_final_u16.npy > $R/f2c.log 2>&1; fi
if pas 6 && [ ! -f $R/filtres_v99/F3_E2.json ]; then
  mkdir -p $R/filtres_v99
  for e in E1 E6 E4 E3 E2; do V97_SORT=$R/filtres_v99 V97_FONTS=$R/lineal_v99 V98_FRANJA=$FR $PY -B $T98/f3_filtres_v98.py $e > $R/filtres_v99/f3_$e.log 2>&1 & done; wait
  for e in E1 E6 E4 E3 E2; do [ -f $R/filtres_v99/F3_$e.json ] || { echo "ATURAT: l'etapa $e dels filtres ha fallat"; exit 6; }; done; fi
if pas 7 && [ ! -f $R/estat_v99/CAPES_V98.json ]; then $PY -B $T98/r3_estat_v98.py $R/filtres_v99/filtres $R/estat_v99 $R/base_v99/base_v99_final_u16.npy > $R/r3.log 2>&1; fi
if pas 8; then
  $PY -B $T98/j14_anells_lupa.py $R/J14_V99.json V99=$R/filtres_v99/filtres > $R/j14.log 2>&1
  $PY -B $T98/j14_anells_lupa.py $R/J14_V99_suportV98.json V99=$R/filtres_v99/filtres --suport $R8/lineal_v98_franja/A3B_franja_neta.npz > $R/j14s.log 2>&1
  mkdir -p $R/compost; $PY -B $T98/j15_compost_limbe.py $R8/estat_v98 $R/estat_v99 $R/compost/v98_v99 > $R/j15.log 2>&1; fi
if pas 9 && [ "$VAR" = B ] && [ ! -f $R/V99_stage.psb ] && [ ! -f 1-PHOTOSHOP/V99.psb ]; then $PY -B $T/b2_munta_v99.py $R/estat_v99 > $R/b2.log 2>&1; fi
if pas 10 && [ "$VAR" = B ]; then
  [ -f 1-PHOTOSHOP/V99.psb ] && { echo "ATURAT: 1-PHOTOSHOP/V99.psb ja existeix (mai no se sobreescriu)"; exit 10; }
  zsh $T/corre_jsx.sh $T/b3_desa_natiu_v99.jsx
  $PY $T97/p6_compost_fusionat.py 1-PHOTOSHOP/V99.psb $R/vistes/V99_llenc_sencer.tif | tee $R/P6_COMPOST.txt
  bash 3-RECERCA/tools/capes_totals_v14/porta_photoshop.sh "$PWD/1-PHOTOSHOP/V99.psb" 2>&1 | tail -1 | tee $R/PORTA.txt
  shasum -a 256 1-PHOTOSHOP/V99.psb | tee $R/SHA_V99.txt
  $PY -B $T/v1_verifica_v99.py $R/estat_v99 $R/V1_VERIFICA_V99.json | tail -1
  $PY $T/r5_natiu_v98_v99.py $R8/vistes/V98_lluna.tif $R/vistes/V99_lluna.tif $R/laminas; fi
echo CADENA_V99_${VAR}_FETA
