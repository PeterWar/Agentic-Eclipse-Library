#!/bin/zsh
# r5_render.sh <psb relatiu a l'arrel> <carpeta de sortida relativa> "<ids a amagar, separats per comes>"
set -e; cd "$(dirname "$0")"; T=$PWD
J=$T/_r5_$(date +%s).jsx; sed -e "s#__SRC__#$1#" -e "s#__DIR__#$2#" -e "s#__HIDE__#$3#" $T/r5_render.jsx.plantilla > $J
zsh $T/../v108_20260926/cadena/corre_jsx.sh $J; rm -f $J
