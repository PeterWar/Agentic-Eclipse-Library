#!/bin/zsh
# corre_v120b.sh · V120, SEGONA TIRADA (Claude, 29-09-2026): el camp de deformació esvaït a la vora del marc de cada tren (f10 + camp_v120 amb
# «vora», L = 200 px). Tot el que depèn del camp es refà, en ordre, amb les MATEIXES ordres que la primera tirada:
#   f5 (Sony deformada) → f6 i f6e (porta de la regla 9) → f7 (llistes d'estrelles) → b3d4 (fusió + D4) → corre_v120.sh (cadena) → f8 (catàleg,
#   202, 203) → f9 (Brno) → o1 (ordit i trama, amb el cercle dels peus omplert).
# La primera tirada ja és a 4-RESULTATS/v120_20260929/descartat/primera_tirada_sense_vora/ (i l'intent amb l'erosió de 2 px a la vora, a segona_tirada_erosio_2px/). Ús (des de l'arrel): zsh 3-RECERCA/tools/v120_20260929/corre_v120b.sh
set -e
cd "$(dirname "$0")/../../.."
PY=""; for c in "${V108_PY:-}" "$HOME/.venvs/eines-ia-py312/bin/python" "$(command -v python3 2>/dev/null || true)" /opt/homebrew/bin/python3.12; do
  if [ -n "$c" ] && [ -x "$c" ] && "$c" -c "import numpy, scipy, cv2, numexpr, psd_tools" 2>/dev/null; then PY="$c"; break; fi; done
[ -n "$PY" ] || { echo "ATURAT: cap Python"; exit 3; }
TV=3-RECERCA/tools/v120_20260929; O=4-RESULTATS/v120_20260929; SV=$O/sony_v; LL=$O/llistes; mkdir -p $O/logs_b
pas() { local nom=$1; shift; local t=$(date +%s); "$@" > $O/logs_b/$nom.log 2>&1 || { echo "ATURAT a $nom ($O/logs_b/$nom.log)"; tail -5 $O/logs_b/$nom.log; exit 7; }; echo "$nom	$(( $(date +%s) - t )) s"; }
$PY -c "import json; d=json.load(open('$O/f1/CAMP_V120.json')); assert d['vora']['L_px'] == 200, d.get('vora')"
[ ! -e $SV ] || { echo "ATURAT: $SV ja existeix"; exit 4; }
pas f5 $PY -B $TV/f5_warp_sony.py $O/f1 $SV
pas f6 $PY -B $TV/f6_porta_regla9.py $SV $O/porta_regla9
pas f6e $PY -B $TV/f6e_estrelles_detall.py $SV $O/porta_regla9
pas f7 $PY -B $TV/f7_llistes_estrelles.py $O/f1 $LL
mkdir -p $O/fonts/logs
pas b3d4 $PY -B $TV/b3d4_v120.py --out $O/fonts/fusio --vixen 4-RESULTATS/v108_20260926/flat2d_v5/apilats/vixen_total.npy --sony-a $SV/sony_A_total_v113vora.npy --sony-b $SV/sony_B_total_v42.npy \
  --sony-a-pesos $SV/sony_A_weights.npy --sony-b-pesos-v42 $SV/sony_B_weights_v42.npy --sony-b-pesos $SV/sony_B_weights.npy --sony-pes-g $SV/sony_weight_G.npy --sony-suport $SV/sony_support.npy \
  --b3-sense-residu-local --congela $SV/congela_b3 --recentra --nucli-fi --extra $LL/EXTRA_ESTRELLES_V120.json --estrelles $LL/estrelles_v42.json --d3 $LL/D3_empirical_pilot.json
pas cadena zsh $TV/corre_v120.sh v120 $O/fonts/fusio/d4/products/sources
grep -q CADENA_V120_v120_FETA $O/logs_b/cadena.log || { echo "ATURAT: la cadena no ha acabat"; exit 8; }
pas f8 $PY -B $TV/f8_estrelles_v120.py $O/f1 $O/estrelles
pas f9 $PY -B $TV/f9_brno_v120.py $O/f1 $O/brno
pas o1 $PY -B $TV/o1_ordit_trama_v120.py $O/ot
echo CORRE_V120B_FET
