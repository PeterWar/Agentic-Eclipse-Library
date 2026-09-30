#!/bin/zsh
# Reprodueix la variant recomanada de la filera de punts (V105, Claude, 26-09-2026). Només escriu a /private/tmp/claude_v105/fila/.
# 1) mapa de resolució que segueix el S/N (mesurat a la linealitzada E), 2) capa 56 (WOW bilateral) i 3) capa 51 (ACHF micro) amb l'entrada
# promitjada a la franja de banda, 4) compost emulat i mesures, 5) làmines.
set -e
cd /private/tmp/claude_v105/fila
PY=""; for c in "$HOME/.venvs/eines-ia-py312/bin/python" "$(command -v python3)"; do
  if [ -x "$c" ] && "$c" -c "import numpy, scipy, cv2, numexpr, PIL" 2>/dev/null; then PY="$c"; break; fi; done
[ -n "$PY" ] || { echo "ATURAT: cap Python amb numpy/scipy/opencv/numexpr/PIL"; exit 3; }
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=4
NOM=${1:-REC}; ESC=${2:-0.7}
[ -f SN_MAPA.npz ] || $PY a3_mapa_sn.py 40
$PY w_wow.py ${NOM}_56 --pre snp --sn-esc $ESC --pre-escales 0,1,2
$PY a_achf.py ${NOM}_51 --pre snp --sn-esc $ESC
mkdir -p $NOM; cp ${NOM}_56/L56_G_moon.npy ${NOM}_51/L51_G_moon.npy $NOM/
$PY m_mesura.py $NOM; $PY m_punts.py $NOM; $PY m_voltant.py $NOM | tail -1
$PY l_laminas.py ${NOM}_lam $NOM; $PY l_zoom.py ${NOM}_dalt 5335,3308,5385,3336 $NOM
echo FILA_${NOM}_FETA
