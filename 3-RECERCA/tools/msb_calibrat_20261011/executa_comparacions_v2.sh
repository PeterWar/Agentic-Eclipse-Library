#!/bin/bash
# Comparacions de la v2 del mapa MSB (12-10-2026): cel per canal, caselles, K-Cor (i prova Fe XIV), color post hoc, C2, banda,
# figura i rebut. Cap intèrpret escrit a pèl: executa.sh tria el primer que tingui el que cal.
# Escriu només a resultats/msb_calibrat_20261011/v2/comparacions/ (el README_EN_v2.md de per_compartir/ s'escriu a mà).
# Necessita el mapa v2 (w1…w6) i, per a la regla del cel, la cau b3 (Paperera o MSB_CAU), només en lectura.
set -e
AQUI="$(cd "$(dirname "$0")" && pwd)"
for g in cv2_0_cel_canals.py cv2_1_caselles.py cv2_2_kcor.py cv2_2b_color_posthoc.py cv2_3_lasco.py cv2_4_banda.py cv2_5_figura.py cv2_6_rebut.py; do
  "$AQUI/executa.sh" "$g"
done
