#!/bin/zsh
# desa_natiu.sh <stage.psb> <desti.psb> <carpeta_vistes> (rutes relatives a l'arrel) · genera el JSX de la plantilla i el fa córrer al Photoshop.
set -e; cd "$(dirname "$0")"; T=$PWD
J=$T/_b3_$(date +%s).jsx; sed -e "s#__STAGE__#$1#" -e "s#__DST__#$2#" -e "s#__VIS__#$3#" $T/b3_desa_natiu_v104.plantilla.jsx > $J
zsh $T/corre_jsx.sh $J; rm -f $J
