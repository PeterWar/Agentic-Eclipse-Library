#!/bin/bash
# Comparacions del mapa MSB (11-10-2026): K-Cor, LASCO C2, prova de banda, pressupost, figura i rebut.
# Ús: executa_comparacions.sh [carpeta amb kl1985.pdf]
#   Sense la carpeta, no es refà la digitalització de Koutchmy & Lamy 1985 (c0) si ja hi ha models_f/F_KL1985_digitalitzat.json.
# Cap intèrpret escrit a pèl: ../executa.sh tria el primer que tingui el que cal. Escriu només a resultats/msb_calibrat_20261011/comparacions/.
set -e
AQUI="$(cd "$(dirname "$0")" && pwd)"
EXE="$AQUI/../executa.sh"
RES="$AQUI/../../../resultats/msb_calibrat_20261011/comparacions"
if [ -n "$1" ] && [ -f "$1/kl1985.pdf" ]; then
  "$EXE" comparacions/c0_models_f.py "$1/kl1985.pdf"
elif [ ! -f "$RES/models_f/F_KL1985_digitalitzat.json" ]; then
  echo "Falta el PDF de Koutchmy & Lamy 1985 (doi:10.1017/S0252921100084359): passa la carpeta on és kl1985.pdf"; exit 1
fi
for g in c1_caselles_nostra.py c2_kcor.py c3_lasco.py c4_banda.py c5_pressupost.py c6_figura.py; do
  "$EXE" "comparacions/$g"
done
"$EXE" comparacions/c7_rebut.py
