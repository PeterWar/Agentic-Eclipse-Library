#!/bin/zsh
# corre_v108.sh · L'ORDRE DE LA V108 amb el flat 2D v4 (CÒPIA del corre_v108.sh de la v3, que queda com era): la mateixa tirada que
# corre_cadena_flat2d_v4.sh (fonts de flat2d_v4, franja congelada amb el domini del control i la regla dels 2 píxels de la protuberància
# —p1_franja_protuberancia.py—, REC de la 56 amb el mapa de S/N del control), per a una VARIANT amb nom propi i amb els ganxos de filtres que es passin per l'entorn
# (V108_F41 … V108_F56, p. ex. la cura de les zones negres, que és decisió de Pere). Opcional: V108_MUNTA=1 fa també el PSB de pas (pas 9–10).
# ⛔ El desament natiu al Photoshop (pas 11, V108_DESA=1) NO es fa des d'aquí: només amb el sí de Pere (vegeu l'INFORME de flat2d_v4, §8).
# ⛔ No l'editis mentre corre (el zsh llegeix el fitxer a trossos).
# Ús (des de l'arrel):  [V108_F41="…" V108_F42="…"] [V108_MUNTA=1] zsh 3-RECERCA/tools/v108_20260926/flat2d_v4/corre_v108.sh <variant>
set -e
VAR=${1:?cal el nom de la variant}
cd "$(dirname "$0")/../../../.."
T=3-RECERCA/tools/v108_20260926/flat2d_v2; T4=3-RECERCA/tools/v108_20260926/flat2d_v4; TC=3-RECERCA/tools/v108_20260926/cadena; T98=3-RECERCA/tools/v98_20260925
C=$TC/cadena_v108.sh; RF=4-RESULTATS/v108_20260926/flat2d_v4; L=$RF/logs/$VAR; mkdir -p $L; R=4-RESULTATS/v108_20260926/cadena/$VAR; CTL=4-RESULTATS/v108_20260926/cadena/control
PY=""; for c in "${V108_PY:-}" "$HOME/.venvs/eines-ia-py312/bin/python" "$(command -v python3 2>/dev/null || true)" /opt/homebrew/bin/python3.12; do
  if [ -n "$c" ] && [ -x "$c" ] && "$c" -c "import numpy, scipy, cv2, numexpr, psd_tools" 2>/dev/null; then PY="$c"; break; fi; done
[ -n "$PY" ] || { echo "ATURAT: cap Python"; exit 3; }
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=${OPENBLAS_NUM_THREADS:-6}
export V108_FONTS=$RF/fusio/d4/products/sources V108_LF=$RF/limb_frames_flat2d V108_FILA56=regenera
source 4-RESULTATS/v103_banda_20260926/E/CONFIG.env; export A3C_RAMPES A3C_SILUETA A3D_BANDA
CONG=$CTL/franja/A3D_FRANJA_BANDA.json
cr() { local nom=$1; shift; /usr/bin/time -l -o $L/temps_$nom.txt "$@" > $L/$nom.log 2>&1 || { echo "ATURAT a $nom ($L/$nom.log)"; tail -5 $L/$nom.log; exit 7; }
  printf "%s\t%s s\t%s GB\n" $nom "$(awk '/ real /{print $1; exit}' $L/temps_$nom.txt)" "$(awk '/maximum resident set size/{printf "%.1f", $1/1073741824}' $L/temps_$nom.txt)" | tee -a $L/TEMPS.tsv; }
# 0 · control de la franja congelada: fotogrames i fonts del control + T/escales del control → la franja del control, clau a clau
if [ ! -f $RF/franja_control/A3D_FRANJA_BANDA.json ]; then
  mkdir -p $RF/franja_control
  cr a3d_ctrl env A3B_LF=4-RESULTATS/v98_20260925/cadena_raw/limb_frames_comuna V97_SORT=$RF/franja_control V97_FONTS=4-RESULTATS/v98_20260925/cadena_v98/d4/products/sources A3D_CONGELA=$CONG $PY -B $T/a3d_congelat_v108.py
  $PY -c "
import numpy as np, sys
a=np.load('$RF/franja_control/A3C_franja_silueta.npz'); b=np.load('$CTL/franja/A3C_franja_silueta.npz'); ks=sorted(b.files)
dif=[k for k in ks if a[k].tobytes()!=b[k].tobytes() or a[k].dtype!=b[k].dtype or a[k].shape!=b[k].shape]; print('franja control congelada (byte a byte, NaN inclosos): claus iguals', len(ks)-len(dif), 'de', len(ks), 'diferents', dif)
sys.exit(1 if dif else 0)" > $L/franja_control_compara.txt || { cat $L/franja_control_compara.txt; exit 8; }; cat $L/franja_control_compara.txt; fi
# 3 · la franja de la variant (congelada) ABANS de la cadena
if [ ! -f $R/franja_a3d/A3D_FRANJA_BANDA.json ]; then
  mkdir -p $R/franja_a3d; cp -c 4-RESULTATS/v98_20260925/lineal_v98_franja/A2_GEOMETRIA.json 4-RESULTATS/v98_20260925/lineal_v98_franja/A2_geometria.npz $R/franja_a3d/
  cr a3d_flat2d env A3B_LF=$V108_LF V97_SORT=$R/franja_a3d V97_FONTS=$V108_FONTS A3D_CONGELA=$CONG $PY -B $T/a3d_congelat_v108.py; fi
# 3b · v4: el domini de la franja congelat al del control i, als píxels que la variant hi perdria pel signe de G', el valor del control
if [ ! -f $R/franja/A3D_FRANJA_BANDA.json ]; then cr p1_protuberancia $PY -B $T4/p1_franja_protuberancia.py $R/franja_a3d $CTL/franja $V108_FONTS $R/franja; cat $L/p1_protuberancia.log; fi
# 4–6 · la cadena fins als filtres
if [ ! -f $R/filtres_v108/ORIGEN.tsv ]; then cr cadena_1a6 env V108_FINS=6 zsh $C $VAR; fi
# 7a · l'estat (l'ordre exacte de la cadena)
if [ ! -f $R/estat_v108/CAPES_V98.json ]; then cr r3 $PY -B $T98/r3_estat_v98.py $R/filtres_v108 $R/estat_v108 $R/base/base_v108_final_u16.npy; cp $L/r3.log $R/r3.log; fi
# 7b · la REC de la 56 amb el mapa de S/N del control (congelat); el mesurat, a part
FR=$R/franja/A3C_franja_silueta.npz
MUS=$($PY -c "import json,sys; print(json.dumps(json.load(open(sys.argv[1]))['capes']['P05_WOW_bilateral']['mitjanes_escala']))" $R/filtres_std/F3_E2.json)
if [ ! -f $L/fila_sn_mesurat/SN_MAPA.npz ]; then
  cr fila_sn_mesurat env V108_FILA_LINEAL=$R/lineal V108_FILA_FRANJA=$FR V108_FILA_ESTAT=$R/estat_v108 V108_FILA_OUT=$L/fila_sn_mesurat $PY -B $TC/fila/a3_mapa_sn_v108.py 40; fi
if [ ! -f $R/fila_REC/REC_56/L56_G_moon.npy ]; then
  mkdir -p $R/fila_REC; cp -c 4-RESULTATS/v108_20260926/cadena/prova_ganxos/fila_REC/SN_MAPA.npz $R/fila_REC/SN_MAPA.npz
  echo "SN_MAPA.npz = còpia del control (prova_ganxos/fila_REC, = V105): congelat; el mesurat és a $L/fila_sn_mesurat" > $R/fila_REC/CONGELAT.txt
  cr fila_wow env V108_FILA_LINEAL=$R/lineal V108_FILA_FRANJA=$FR V108_FILA_ESTAT=$R/estat_v108 V108_FILA_OUT=$R/fila_REC V108_FILA_MUS="$MUS" $PY -B $TC/fila/w_wow_v108.py REC_56 --pre snp --sn-esc 0.7 --pre-escales 0,1,2; fi
# 7c–8 · la resta de la cadena (c0 amb la REC d'aquesta variant, c8)
cr cadena_7a8 zsh $C $VAR 7
if [ "${V108_MUNTA:-}" = 1 ]; then cr cadena_9a10 zsh $C $VAR 9; fi
echo CADENA_V108_${VAR}_FETA
