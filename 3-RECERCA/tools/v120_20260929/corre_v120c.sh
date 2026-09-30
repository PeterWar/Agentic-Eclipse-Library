#!/bin/zsh
# corre_v120c.sh · V120, TERCERA PASSADA (Claude, 29/30-09-2026): el suport de la Sony és l'ORIGINAL deformat (f5), no la reconstrucció dels pesos
# (que hi afegia 16.219 píxels a la vora del marc de la B). Es refà només el que en depèn: f5 → b3d4 → cadena → o1. Les llistes d'estrelles (f7), el
# catàleg, la 202 i la 203 (f8), Brno (f9) i la porta de la regla 9 (f6, f6e) no llegeixen el suport i queden els de la segona tirada.
# El que es refà de la segona tirada és a 4-RESULTATS/v120_20260929/descartat/segona_tirada_suport_reconstruit/. Ús (des de l'arrel): zsh 3-RECERCA/tools/v120_20260929/corre_v120c.sh
set -e
cd "$(dirname "$0")/../../.."
PY=""; for c in "${V108_PY:-}" "$HOME/.venvs/eines-ia-py312/bin/python" "$(command -v python3 2>/dev/null || true)" /opt/homebrew/bin/python3.12; do
  if [ -n "$c" ] && [ -x "$c" ] && "$c" -c "import numpy, scipy, cv2, numexpr, psd_tools" 2>/dev/null; then PY="$c"; break; fi; done
[ -n "$PY" ] || { echo "ATURAT: cap Python"; exit 3; }
TV=3-RECERCA/tools/v120_20260929; O=4-RESULTATS/v120_20260929; SV=$O/sony_v; LL=$O/llistes; mkdir -p $O/logs_c
pas() { local nom=$1; shift; local t=$(date +%s); "$@" > $O/logs_c/$nom.log 2>&1 || { echo "ATURAT a $nom ($O/logs_c/$nom.log)"; tail -5 $O/logs_c/$nom.log; exit 7; }; echo "$nom	$(( $(date +%s) - t )) s"; }
$PY -c "import json; d=json.load(open('$O/f1/CAMP_V120.json')); assert d['vora']['L_px'] == 200, d.get('vora')"
for d in $SV $O/fonts $O/cadena $O/ot; do [ ! -e $d ] || { echo "ATURAT: $d ja existeix"; exit 4; }; done
[ -f $LL/EXTRA_ESTRELLES_V120.json ] || { echo "ATURAT: falten les llistes"; exit 4; }
pas f5 $PY -B $TV/f5_warp_sony.py $O/f1 $SV
mkdir -p $O/fonts/logs
pas b3d4 $PY -B $TV/b3d4_v120.py --out $O/fonts/fusio --vixen 4-RESULTATS/v108_20260926/flat2d_v5/apilats/vixen_total.npy --sony-a $SV/sony_A_total_v113vora.npy --sony-b $SV/sony_B_total_v42.npy \
  --sony-a-pesos $SV/sony_A_weights.npy --sony-b-pesos-v42 $SV/sony_B_weights_v42.npy --sony-b-pesos $SV/sony_B_weights.npy --sony-pes-g $SV/sony_weight_G.npy --sony-suport $SV/sony_support.npy \
  --b3-sense-residu-local --congela $SV/congela_b3 --recentra --nucli-fi --extra $LL/EXTRA_ESTRELLES_V120.json --estrelles $LL/estrelles_v42.json --d3 $LL/D3_empirical_pilot.json
pas cadena zsh $TV/corre_v120.sh v120 $O/fonts/fusio/d4/products/sources
grep -q CADENA_V120_v120_FETA $O/logs_c/cadena.log || { echo "ATURAT: la cadena no ha acabat"; exit 8; }
pas o1 $PY -B $TV/o1_ordit_trama_v120.py $O/ot
echo CORRE_V120C_FET
