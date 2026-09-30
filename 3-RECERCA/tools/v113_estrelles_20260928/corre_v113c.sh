#!/bin/zsh
# corre_v113c.sh (còpia de v112_claude_20260928/corre_v113.sh: només carpetes i claim) · V113 (Claude, 28-09-2026): la tirada de la V108 (flat2d_v5/corre_v108.sh + cadena_v108.sh, sense canvis de recepta) amb
# les FONTS de la fusió congelada on la Sony A s'ha corregit contra la Sony B al domini de les marques 2, 3, 5 i 8 (f1_correccio_sonyA.py --local),
# i després els operadors de la V112 per a les capes 45/46 (RHEF «mass» del Codex) i 41/42 (genoll de la NRGF G_MAX_T_e30_W_H0, recepta 8).
# Tot s'escriu a 4-RESULTATS/v112_claude_20260928/cadena/<variant>. ⛔ No l'editis mentre corre (el zsh llegeix el fitxer a trossos).
# Ús (des de l'arrel):  zsh 3-RECERCA/tools/v112_claude_20260928/corre_v113.sh <variant> <carpeta de fonts>
#   p. ex.  zsh …/corre_v113.sh v113 4-RESULTATS/v112_claude_20260928/fonts_v113_local/fusio/d4/products/sources
set -e
VAR=${1:?cal el nom de la variant}; FONTS_DIR=${2:?cal la carpeta de fonts}
cd "$(dirname "$0")/../../.."
T=3-RECERCA/tools/v108_20260926/flat2d_v2; T5=3-RECERCA/tools/v108_20260926/flat2d_v5; TC=3-RECERCA/tools/v108_20260926/cadena; T98=3-RECERCA/tools/v98_20260925
TM=3-RECERCA/tools/v113_estrelles_20260928; C=$TM/cadena_v113c.sh; RF=4-RESULTATS/v108_20260926/flat2d_v5
R=4-RESULTATS/v113_estrelles_20260928/cadena/$VAR; L=$R/logs; mkdir -p $L; CTL=4-RESULTATS/v108_20260926/cadena/control
PY=""; for c in "${V108_PY:-}" "$HOME/.venvs/eines-ia-py312/bin/python" "$(command -v python3 2>/dev/null || true)" /opt/homebrew/bin/python3.12; do
  if [ -n "$c" ] && [ -x "$c" ] && "$c" -c "import numpy, scipy, cv2, numexpr, psd_tools" 2>/dev/null; then PY="$c"; break; fi; done
[ -n "$PY" ] || { echo "ATURAT: cap Python"; exit 3; }
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=${OPENBLAS_NUM_THREADS:-6}
export V108_FONTS=$FONTS_DIR V108_LF=$RF/limb_frames_flat2d V108_FILA56=regenera
source 4-RESULTATS/v103_banda_20260926/E/CONFIG.env; export A3C_RAMPES A3C_SILUETA A3D_BANDA
CONG=$CTL/franja/A3D_FRANJA_BANDA.json
cr() { local nom=$1; shift; /usr/bin/time -l -o $L/temps_$nom.txt "$@" > $L/$nom.log 2>&1 || { echo "ATURAT a $nom ($L/$nom.log)"; tail -5 $L/$nom.log; exit 7; }
  printf "%s\t%s s\t%s GB\n" $nom "$(awk '/ real /{print $1; exit}' $L/temps_$nom.txt)" "$(awk '/maximum resident set size/{printf "%.1f", $1/1073741824}' $L/temps_$nom.txt)" | tee -a $L/TEMPS.tsv; }
# 3 · la franja de la variant (congelada, com a la flat2d_v5) ABANS de la cadena
if [ ! -f $R/franja_a3d/A3D_FRANJA_BANDA.json ]; then
  mkdir -p $R/franja_a3d; cp -c 4-RESULTATS/v98_20260925/lineal_v98_franja/A2_GEOMETRIA.json 4-RESULTATS/v98_20260925/lineal_v98_franja/A2_geometria.npz $R/franja_a3d/
  cr a3d env A3B_LF=$V108_LF V97_SORT=$R/franja_a3d V97_FONTS=$V108_FONTS A3D_CONGELA=$CONG $PY -B $T/a3d_congelat_v108.py; fi
# 3b · el domini de la franja congelat al del control i la regla de fragilitat (v5)
if [ ! -f $R/franja/A3D_FRANJA_BANDA.json ]; then cr p1_protuberancia $PY -B $T5/p1_franja_protuberancia_v5.py $R/franja_a3d $CTL/franja $V108_FONTS $R/franja; fi
# 4–6 · la cadena fins als filtres (sense ganxos: els filtres estàndard)
if [ ! -f $R/filtres_v108/ORIGEN.tsv ]; then cr cadena_1a6 env V108_FINS=6 zsh $C $VAR; fi
# 7 · l'estat (r3), la REC de la 56 amb el mapa de S/N del control (congelat, com la flat2d_v5) i c0
FR=$R/franja/A3C_franja_silueta.npz
if [ ! -f $R/estat_v108/CAPES_V98.json ]; then cr r3 $PY -B $T98/r3_estat_v98.py $R/filtres_v108 $R/estat_v108 $R/base/base_v108_final_u16.npy; fi
MUS=$($PY -c "import json,sys; print(json.dumps(json.load(open(sys.argv[1]))['capes']['P05_WOW_bilateral']['mitjanes_escala']))" $R/filtres_std/F3_E2.json)
if [ ! -f $R/fila_REC/REC_56/L56_G_moon.npy ]; then
  mkdir -p $R/fila_REC; cp -c 4-RESULTATS/v108_20260926/cadena/prova_ganxos/fila_REC/SN_MAPA.npz $R/fila_REC/SN_MAPA.npz
  echo "SN_MAPA.npz = còpia del control (prova_ganxos/fila_REC, = V105): congelat, com a la flat2d_v5" > $R/fila_REC/CONGELAT.txt
  cr fila_wow env V108_FILA_LINEAL=$R/lineal V108_FILA_FRANJA=$FR V108_FILA_ESTAT=$R/estat_v108 V108_FILA_OUT=$R/fila_REC V108_FILA_MUS="$MUS" $PY -B $TC/fila/w_wow_v108.py REC_56 --pre snp --sn-esc 0.7 --pre-escales 0,1,2; fi
cr cadena_7 env V108_FINS=7 zsh $C $VAR 7
# 8' · RHEF local «mass» (V112, Codex) per a 45/46, sobre la linealitzada de la variant
if [ ! -f $R/filtres_mass/F3_E6.json ]; then mkdir -p $R/filtres_mass
  cr rhef_mass env V97_SORT=$R/filtres_mass V97_FONTS=$R/lineal V98_FRANJA=$FR $PY -B $TM/run_rhef_mass_v113c.py E6; fi
# 9' · el genoll de la NRGF (41/42) amb la recepta 8 de la V112: màscares i opacitats de V108_Artefactes, RHEF «mass» i MGN de la variant
FS=$R/nrgf_fstd
if [ ! -d $FS ]; then mkdir -p $FS
  for tg in P02c_RHEF_local60_native P02d_RHEF_local30_native; do for s in _u16 _alfa_u16; do ln -s ../filtres_mass/filtres/$tg$s.npy $FS/$tg$s.npy; done; done
  for s in _u16 _alfa_u16; do ln -s ../filtres_std/filtres/P03_MGN$s.npy $FS/P03_MGN$s.npy; done; fi
if [ ! -d $R/nrgf/G_MAX_T_e30_W_H0 ]; then
  cr nrgf_genoll env V97_FONTS=$R/lineal V98_FRANJA=$FR V108_BASE=$R/base/base_v108_final_u16.npy V108_R=$R V97_SORT=$R/nrgf $PY -B 3-RECERCA/tools/v108_20260926/negres_v2/g1_nrgf_genoll.py G_MAX_T_e30_W_H0 --psb 1-PHOTOSHOP/V108_Artefactes.psb --filtres-std $FS; fi
echo CADENA_V113_${VAR}_FETA
