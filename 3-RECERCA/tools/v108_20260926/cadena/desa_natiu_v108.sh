#!/bin/zsh
# desa_natiu_v108.sh <stage.psb> <desti.psb> <carpeta_vistes> (rutes relatives a l'arrel del projecte) · genera el JSX de la plantilla i el fa córrer
# al Photoshop obert (desa COM A CÒPIA; no toca cap altre document). ⛔ Només quan Pere hi estigui d'acord: obre un PSB de 7 GB al seu Photoshop.
set -e; cd "$(dirname "$0")"; T=$PWD
[ $# -eq 3 ] || { echo "ús: desa_natiu_v108.sh <stage.psb> <desti.psb> <carpeta_vistes>"; exit 2; }
J=$T/_b3_$(date +%s).jsx; sed -e "s#__STAGE__#$1#" -e "s#__DST__#$2#" -e "s#__VIS__#$3#" $T/b3_desa_natiu_v108.plantilla.jsx > $J
zsh $T/corre_jsx.sh $J; rm -f $J
