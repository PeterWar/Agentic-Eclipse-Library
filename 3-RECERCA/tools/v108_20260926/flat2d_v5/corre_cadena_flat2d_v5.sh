#!/bin/zsh
# corre_cadena_flat2d_v5.sh · La variant flat2d_v5 de cadena_v108.sh (V108). CÒPIA de corre_cadena_flat2d_v4.sh on canvien la carpeta de les
# fonts (4-RESULTATS/v108_20260926/flat2d_v5), el nom de la variant (flat2d_v5) i el guió del pas 3b:
#   pas 3b · p1_franja_protuberancia_v5.py = la regla de la v4 (domini de la franja congelat al del control; valor del control on la variant el
#            perdria pel signe de G') MÉS la regla de FRAGILITAT: als píxels del domini amb f = |E_G|/Σ|E| < 0,002 a la franja del control
#            (el nucli vermell de la protuberància, on G' post-matriu ≈ 0), el valor del control. La franja final és a <variant>/franja.
# ─── Text de la v4 ───
# pas 3 · després de l'a3d congelat (que ara escriu a <variant>/franja_a3d), p1_franja_protuberancia.py congela el DOMINI de la franja al del
#           control (com ja ho és la DMIN) i hi posa el valor del control on la variant el perdria només pel signe de G' post-matriu (els 2 píxels
#           de la protuberància, 180°, 17,8 px del limbe): la franja final és a <variant>/franja, i la cadena se la troba feta.
# La franja, la REC i la fusió, congelades com a la v2 i la v3.
# ⛔ No l'editis mentre corre. Text de la v2: el flat 2D sense disc i amb TOT el que la cadena mesura de la dada
# CONGELAT al control, perquè l'únic canvi sigui el flat. Fa servir cadena_v108.sh (sense editar-lo) i els seus propis passos, amb dues
# interposicions documentades que la cadena permet («cada pas se salta si la sortida ja existeix»):
#   pas 3 · la franja: a3d_congelat_v108.py (l'a3d de la variant E amb la T de vora i les escales de la unió del control) escriu la franja
#           de la variant ABANS que la cadena hi arribi; la cadena se la troba feta i no corre l'a3d estàndard.
#   pas 7 · la REC de la 56: la cadena la faria amb un mapa de S/N MESURAT a la dada nova (a3_mapa_sn_v108.py). Aquí es fa amb el mapa
#           del control (4-RESULTATS/v108_20260926/cadena/prova_ganxos/fila_REC/SN_MAPA.npz, el que reprodueix la V105 byte a byte) i amb
#           l'ordre exacte de la cadena (w_wow_v108.py); el mapa mesurat es desa a part per saber quant s'hauria mogut.
# Ús (des de l'arrel): zsh 3-RECERCA/tools/v108_20260926/flat2d_v5/corre_cadena_flat2d_v5.sh
set -e
cd "$(dirname "$0")/../../../.."
T=3-RECERCA/tools/v108_20260926/flat2d_v2; T5=3-RECERCA/tools/v108_20260926/flat2d_v5; TC=3-RECERCA/tools/v108_20260926/cadena; T98=3-RECERCA/tools/v98_20260925
C=$TC/cadena_v108.sh; RF=4-RESULTATS/v108_20260926/flat2d_v5; L=$RF/logs; R=4-RESULTATS/v108_20260926/cadena/flat2d_v5; CTL=4-RESULTATS/v108_20260926/cadena/control
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
# 3b · v5: el domini de la franja congelat al del control; el valor del control on la variant el perdria pel signe de G' (v4) i als píxels fràgils (f < 0,002, v5)
if [ ! -f $R/franja/A3D_FRANJA_BANDA.json ]; then cr p1_protuberancia $PY -B $T5/p1_franja_protuberancia_v5.py $R/franja_a3d $CTL/franja $V108_FONTS $R/franja; cat $L/p1_protuberancia.log; fi
# 4–6 · la cadena fins als filtres
if [ ! -f $R/filtres_v108/ORIGEN.tsv ]; then cr cadena_1a6 env V108_FINS=6 zsh $C flat2d_v5; fi
# 7a · l'estat (l'ordre exacte de la cadena)
if [ ! -f $R/estat_v108/CAPES_V98.json ]; then cr r3 $PY -B $T98/r3_estat_v98.py $R/filtres_v108 $R/estat_v108 $R/base/base_v108_final_u16.npy; cp $L/r3.log $R/r3.log; fi
# 7b · la REC de la 56 amb el mapa de S/N del control (congelat); el mesurat, a part
FR=$R/franja/A3C_franja_silueta.npz
MUS=$($PY -c "import json,sys; print(json.dumps(json.load(open(sys.argv[1]))['capes']['P05_WOW_bilateral']['mitjanes_escala']))" $R/filtres_std/F3_E2.json)
if [ ! -f $RF/fila_sn_mesurat/SN_MAPA.npz ]; then
  cr fila_sn_mesurat env V108_FILA_LINEAL=$R/lineal V108_FILA_FRANJA=$FR V108_FILA_ESTAT=$R/estat_v108 V108_FILA_OUT=$RF/fila_sn_mesurat $PY -B $TC/fila/a3_mapa_sn_v108.py 40; fi
if [ ! -f $R/fila_REC/REC_56/L56_G_moon.npy ]; then
  mkdir -p $R/fila_REC; cp -c 4-RESULTATS/v108_20260926/cadena/prova_ganxos/fila_REC/SN_MAPA.npz $R/fila_REC/SN_MAPA.npz
  echo "SN_MAPA.npz = còpia del control (prova_ganxos/fila_REC, = V105): congelat; el mesurat és a $RF/fila_sn_mesurat" > $R/fila_REC/CONGELAT.txt
  cr fila_wow env V108_FILA_LINEAL=$R/lineal V108_FILA_FRANJA=$FR V108_FILA_ESTAT=$R/estat_v108 V108_FILA_OUT=$R/fila_REC V108_FILA_MUS="$MUS" $PY -B $TC/fila/w_wow_v108.py REC_56 --pre snp --sn-esc 0.7 --pre-escales 0,1,2; fi
# 7c–8 · la resta de la cadena (c0 amb la REC d'aquesta variant, c8)
cr cadena_7a8 zsh $C flat2d_v5 7
echo CADENA_FLAT2D_V5_FETA
