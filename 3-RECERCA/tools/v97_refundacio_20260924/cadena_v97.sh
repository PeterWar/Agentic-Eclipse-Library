#!/bin/zsh
# cadena_v97.sh · LA CADENA SENCERA DE LA V97, dels RAW al PSB, en un sol punt d'entrada (Claude, 24-09-2026).
# Cada pas escriu en una carpeta nova de 4-RESULTATS/v97_refundacio_20260924/ i s'atura si una porta falla (set -e + asserts dins dels scripts).
# Requisits: claim SERIAL_WRITES viu a .coordination/claim.lock; un Python amb numpy, scipy, opencv, rawpy, numexpr, psd-tools i tifffile;
# el Photoshop només per al pas 11 (i sense documents de Pere per desar).
# Ús: zsh cadena_v97.sh [des_del_pas]   (per defecte 0; cada pas se salta si la seva sortida ja existeix)
set -e
cd "$(dirname "$0")/../../.."                                         # arrel del projecte (la carpeta de CLAUDE.md)
T=3-RECERCA/tools/v97_refundacio_20260924; R=4-RESULTATS/v97_refundacio_20260924; P=$R/proves_apilat; C=$R/cadena_v97
PY=""; for c in "$HOME/.venvs/eines-ia-py312/bin/python" "$(command -v python3)"; do
  if [ -x "$c" ] && "$c" -c "import numpy, scipy, cv2, rawpy, numexpr, psd_tools, tifffile" 2>/dev/null; then PY="$c"; break; fi; done
[ -n "$PY" ] || { echo "ATURAT: cap Python amb numpy/scipy/opencv/rawpy/numexpr/psd-tools/tifffile"; exit 3; }
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=4
DES=${1:-0}; pas() { [ "$DES" -le "$1" ]; }
# 0 · Calibració i apilats des dels RAW (còpia literal de la cadena V85; cada etapa compara els SHA amb els congelats) · ~25 min
if pas 0 && [ ! -f $R/cadena_raw/BASELINE_COMPLETE.json ]; then
  $PY -B $T/cadena_raw/a2_calibration.py > $R/cadena_raw/CALIBRATION.log 2>&1
  $PY -B $T/cadena_raw/a10_run_baseline.py > $R/cadena_raw/BASELINE_RUN.log 2>&1; fi
# 1 · Vixen amb la FINESTRA COMUNA als quatre subplans (cura el «polígon» B/G) · ~2,5 min
if pas 1 && [ ! -f $P/vixen_comuna_taula_original/vixen_total.npy ]; then
  $PY -B $T/cadena_raw/b2_v97.py vixen --finestra comuna --vora taula --out $P/vixen_comuna_taula_original > $P/vixen_comuna_taula_original.log 2>&1; fi
# 2 · Fusió (b3) amb el residu A→B de la Sony que s'esvaeix fora del solapament (cura el graó diagonal) i fonts sense estrelles (d4) · ~2 min
if pas 2 && [ ! -f $C/COMPLETE.json ]; then
  $PY -B $T/cadena_raw/b3d4_v97.py --out $C --vixen $P/vixen_comuna_taula_original/vixen_total.npy --b3-local-esvaeix > $C.log 2>&1; fi
# 3 · Franja d'un sol instant (A3A, recepta V88) sobre les fonts noves · ~1 min
if pas 3 && [ ! -f $R/lineal_v97_franja/A3A_franja_un_instant.npz ]; then
  mkdir -p $R/lineal_v97_franja; cp 4-RESULTATS/v86_neta_20260923/A2_GEOMETRIA.json 4-RESULTATS/v86_neta_20260923/A2_geometria.npz $R/lineal_v97_franja/
  V97_SORT=$R/lineal_v97_franja V97_FONTS=$C/d4/products/sources $PY -B $T/a3a_franja_un_instant.py > $R/lineal_v97_franja/a3a.log 2>&1; fi
# 4 · La linealitzada V97 (d4 + franja A3A), la MATEIXA per a la base i per als filtres
if pas 4 && [ ! -f $R/lineal_v97/LINEAL_REBUT.json ]; then
  $PY -B $T/f2_lineal_v97.py $C/d4/products/sources $R/lineal_v97_franja/A3A_franja_un_instant.npz $R/lineal_v97; fi
# 5 · La base (recepta b4e declarada; reprodueix la base V96 a les zones netes)
if pas 5 && [ ! -f $R/base_v97/base_v97_u16.npy ]; then
  mkdir -p $R/base_v97; $PY -B $T/f2b_base.py $R/lineal_v97/fusion_starless.npy $R/lineal_v97/support.npy $R/base_v97/base_v97_u16.npy --espai assigna --compara-v96; fi
# 5b · Arran del limbe (< 150 px, fosa fins a 250 px), la base de la V96: la recomposició nova del limbe feia una franja més clara i blanquinosa
if pas 5 && [ ! -f $R/base_v97/base_v97_final_u16.npy ]; then $PY -B $T/f2c_base_limbe.py $R/base_v97/base_v97_u16.npy $R/base_v97/base_v97_final_u16.npy; fi
# 6 · Els 16 filtres (5 etapes en paral·lel) · ~15 min
if pas 6 && [ ! -f $R/filtres_v97/F3_E2.json ]; then
  mkdir -p $R/filtres_v97; cp -c $R/lineal_v97_franja/A3A_franja_un_instant.npz $R/filtres_v97/
  for e in E1 E6 E4 E3 E2; do V97_SORT=$R/filtres_v97 V97_FONTS=$C/d4/products/sources $PY -B $T/f3_filtres_v97.py $e > $R/filtres_v97/f3_$e.log 2>&1 & done; wait
  for e in E1 E6 E4 E3 E2; do [ -f $R/filtres_v97/F3_$e.json ] || { echo "ATURAT: l'etapa $e dels filtres ha fallat"; exit 6; }; done; fi
# 7 · L'estat V97 (base + filtres nous, la resta de la V96) i 8 · el jutge contra la V96
if pas 7; then
  [ -f $R/v96_ref/CAPES_V96.json ] || $PY -B $T/r2_extreu_v96.py                     # la V96 en ràsters (referència del jutge i de les màscares)
  $PY -B $T/r3_estat_v97.py $R/filtres_v97/filtres $R/base_v97/base_v97_final_u16.npy $R/estat_v97; fi
if pas 8; then
  [ -f $R/J0_V96.json ] || $PY -B $T/j0_jutge.py $R/v96_ref 4-RESULTATS/v85_regeneracio_20260922/d4_baseline/products/sources $R/J0_V96.json > $R/J0_V96.log 2>&1
  $PY -B $T/j0_jutge.py $R/estat_v97 $R/lineal_v97 $R/J0_V97.json --contra $R/v96_ref > $R/J0_V97.log 2>&1
  $PY -B $T/d1_grao_sony.py $R/D1_GRAO_SONY_V97.json baseG_v97=$R/lineal_v97/base_G.npy > /dev/null
  $PY -B $T/j2_poligon.py $R/J2_POLIGON_V97.json fusio_v97=$R/lineal_v97/fusion_starless.npy > /dev/null
  $PY -B $T/j7_vora_limbe.py $R/J7_VORA_V97.json fusio_v97=$R/lineal_v97/fusion_starless.npy > /dev/null
  $PY -B $T/j9_veredicte.py $R/J0_V96.json $R/J0_V97.json $R/VEREDICTE_V97.json || { [ -n "$ACCEPTA_V97" ] || { echo "ATURAT: el veredicte no passa tot. Justifica-ho al RESULTAT i torna a córrer amb ACCEPTA_V97=1"; exit 8; }; }
  $PY -B $T/j10_regressio_neta.py $R/J10_REGRESSIO_NETA.json > /dev/null
  $PY -B $T/r4_laminas.py $R/v96_ref $R/estat_v97 $R/laminas; fi
# 9 · El PSB de pas (V96 + canvis, byte a byte la resta) · 10 · Photoshop el desa COM A CÒPIA · 11 · porta del compost fusionat i porta Photoshop
if pas 9 && [ ! -f $R/V97_stage.psb ]; then $PY -B $T/b2_munta_v97.py $R/estat_v97; fi
if pas 10; then
  [ -f 1-PHOTOSHOP/V97.psb ] && { echo "ATURAT: 1-PHOTOSHOP/V97.psb ja existeix (mai no se sobreescriu)"; exit 10; }
  zsh $T/corre_jsx.sh $T/b3_desa_natiu.jsx
  $PY $T/p6_compost_fusionat.py 1-PHOTOSHOP/V97.psb $R/vistes/V97_llenc_sencer.tif | tee $R/P6_COMPOST.txt
  bash 3-RECERCA/tools/capes_totals_v14/porta_photoshop.sh "$PWD/1-PHOTOSHOP/V97.psb" 2>&1 | tail -1 | tee $R/PORTA.txt
  shasum -a 256 1-PHOTOSHOP/V97.psb | tee $R/SHA_V97.txt; fi
echo CADENA_V97_FETA
