#!/bin/zsh
# cadena_v98.sh · LA CADENA DE LA V98 (Claude, 25-09-2026, nit), a partir dels apilats per tren de la V97 (cadena_raw, bit a bit dels RAW) i de
# la Vixen amb finestra comuna de la V97. Cada pas escriu a 4-RESULTATS/v98_20260925/ i se salta si la seva sortida ja existeix.
# Requisits: claim SERIAL_WRITES viu (claim_id CLAUDE_V98_20260925 o el que diguin les constants), un Python amb numpy, scipy, opencv,
# rawpy, numexpr, psd-tools i tifffile; el Photoshop només per al pas 10.
# Ús: zsh cadena_v98.sh [des_del_pas]
set -e
cd "$(dirname "$0")/../../.."
T=3-RECERCA/tools/v98_20260925; T97=3-RECERCA/tools/v97_refundacio_20260924; R=4-RESULTATS/v98_20260925; R97=4-RESULTATS/v97_refundacio_20260924
PY=""; for c in "$HOME/.venvs/eines-ia-py312/bin/python" "$(command -v python3)"; do
  if [ -x "$c" ] && "$c" -c "import numpy, scipy, cv2, rawpy, numexpr, psd_tools, tifffile" 2>/dev/null; then PY="$c"; break; fi; done
[ -n "$PY" ] || { echo "ATURAT: cap Python amb numpy/scipy/opencv/rawpy/numexpr/psd-tools/tifffile"; exit 3; }
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=4
DES=${1:-0}; pas() { [ "$DES" -le "$1" ]; }
[ -f $R97/cadena_raw/BASELINE_COMPLETE.json ] || { echo "ATURAT: falten els apilats (zsh $T97/cadena_v97.sh 0)"; exit 2; }
[ -f $R97/proves_apilat/vixen_comuna_taula_original/vixen_total.npy ] || { echo "ATURAT: falta la Vixen comuna (zsh $T97/cadena_v97.sh 1)"; exit 2; }
# 1 · Els 67 fotogrames Vixen de la caixa lunar amb la FINESTRA COMUNA (la V85 els tenia per canal). Control: --finestra canal = cadena_raw bit a bit
if pas 1 && [ ! -f $R/cadena_raw/limb_frames_comuna/COMPLETE.json ]; then
  $PY $T/a9b_limb_frames_comuna.py --finestra comuna --out $R/cadena_raw/limb_frames_comuna > $R/cadena_raw/a9b_comuna.log 2>&1; fi
# 2 · Fusió b3 SENSE el residu local A→B de la Sony (el graó diagonal: la V97 el va desplaçar, no curar) i fonts sense estrelles d4
if pas 2 && [ ! -f $R/cadena_v98/d4/products/sources/base_G.npy ]; then
  $PY -B $T/b3d4_v98.py --out $R/cadena_v98 --vixen $R97/proves_apilat/vixen_comuna_taula_original/vixen_total.npy --b3-sense-residu-local > $R/cadena_v98.log 2>&1; fi
# 3 · La corona arran del limbe amb selecció física per fotograma (a3b) · 4 · la linealitzada V98 · 5 · la base (recepta V97; V96 arran del limbe)
if pas 3 && [ ! -f $R/lineal_v98_franja/A3B_franja_neta.npz ]; then
  mkdir -p $R/lineal_v98_franja; cp -c $R97/lineal_v97_franja/A2_GEOMETRIA.json $R97/lineal_v97_franja/A2_geometria.npz $R/lineal_v98_franja/
  A3B_LF=$R/cadena_raw/limb_frames_comuna V97_SORT=$R/lineal_v98_franja V97_FONTS=$R/cadena_v98/d4/products/sources $PY -B $T/a3b_franja_neta.py; fi
if pas 4 && [ ! -f $R/lineal_v98/LINEAL_REBUT.json ]; then $PY -B $T97/f2_lineal_v97.py $R/cadena_v98/d4/products/sources $R/lineal_v98_franja/A3B_franja_neta.npz $R/lineal_v98; fi
if pas 5 && [ ! -f $R/base_v98/base_v98_final_u16.npy ]; then
  mkdir -p $R/base_v98; $PY -B $T97/f2b_base.py $R/lineal_v98/fusion_starless.npy $R/lineal_v98/support.npy $R/base_v98/base_v98_u16.npy --espai assigna
  $PY -B $T97/f2c_base_limbe.py $R/base_v98/base_v98_u16.npy $R/base_v98/base_v98_final_u16.npy; fi
# 6 · Els 16 filtres V98 (5 etapes en paral·lel, ~12 min)
if pas 6 && [ ! -f $R/filtres_v98/F3_E2.json ]; then
  mkdir -p $R/filtres_v98
  for e in E1 E6 E4 E3 E2; do V97_SORT=$R/filtres_v98 V97_FONTS=$R/lineal_v98 V98_FRANJA=$R/lineal_v98_franja/A3B_franja_neta.npz $PY -B $T/f3_filtres_v98.py $e > $R/filtres_v98/f3_$e.log 2>&1 & done; wait
  for e in E1 E6 E4 E3 E2; do [ -f $R/filtres_v98/F3_$e.json ] || { echo "ATURAT: l'etapa $e dels filtres ha fallat"; exit 6; }; done; fi
# 7 · L'estat V98 (filtres, màscares netes dins de la Lluna, base nova; la resta, V97) · 8 · els jutges
if pas 7 && [ ! -f $R/estat_v98/CAPES_V98.json ]; then $PY -B $T/r3_estat_v98.py $R/filtres_v98/filtres $R/estat_v98 $R/base_v98/base_v98_final_u16.npy; fi
if pas 8; then
  $PY -B $T97/j0_jutge.py $R/estat_v98 $R/lineal_v98 $R/J0_V98.json --contra $R97/estat_v97 > $R/J0_V98.log 2>&1
  $PY -B $T97/j9_veredicte.py $R97/J0_V97.json $R/J0_V98.json $R/VEREDICTE_V98_j9.json || true
  $PY -B $T/j14_anells_lupa.py $R/J14_V98.json V98=$R/filtres_v98/filtres
  $PY -B $T/j15_compost_limbe.py $R97/estat_v97 $R/estat_v98 $R/compost/v97_v98
  $PY -B $T/d8_diagonal_perfil.py $R/D8_DIAGONAL.json V97=$R97/lineal_v97/base_G.npy V98=$R/lineal_v98/base_G.npy control=$R97/cadena_raw/d4_baseline/products/sources/base_G.npy
  $PY -B $T/j13_pentagon_factorial.py; fi
# 9 · El PSB de pas (V97 + canvis, la resta byte a byte) · 10 · el Photoshop el desa COM A CÒPIA · portes
if pas 9 && [ ! -f $R/V98_stage.psb ]; then $PY -B $T/b2_munta_v98.py $R/estat_v98; fi
if pas 10; then
  [ -f 1-PHOTOSHOP/V98.psb ] && { echo "ATURAT: 1-PHOTOSHOP/V98.psb ja existeix (mai no se sobreescriu)"; exit 10; }
  zsh $T/corre_jsx.sh $T/b3_desa_natiu_v98.jsx
  $PY $T97/p6_compost_fusionat.py 1-PHOTOSHOP/V98.psb $R/vistes/V98_llenc_sencer.tif | tee $R/P6_COMPOST.txt
  bash 3-RECERCA/tools/capes_totals_v14/porta_photoshop.sh "$PWD/1-PHOTOSHOP/V98.psb" 2>&1 | tail -1 | tee $R/PORTA.txt
  shasum -a 256 1-PHOTOSHOP/V98.psb | tee $R/SHA_V98.txt; fi
echo CADENA_V98_FETA
