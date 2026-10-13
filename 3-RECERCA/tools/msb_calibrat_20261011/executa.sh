#!/bin/bash
# Mapa MSB (11-10-2026). Ús: executa.sh <guió.py> [arguments]   (p. ex. executa.sh p0_zones_i_proves.py; executa.sh mapa_msb.py)
# Cap intèrpret escrit a pèl: el primer que tingui el que cal. Res no escriu fora de resultats/msb_calibrat_20261011/.
set -e
cd "$(dirname "$0")"
export PYTHONDONTWRITEBYTECODE=1
PY=""
for c in "$HOME/.venvs/eines-ia-py312/bin/python" python3.12 python3; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c "import numpy, scipy, astropy, sunpy, rawpy, cv2, matplotlib" 2>/dev/null; then PY="$c"; break; fi
done
[ -n "$PY" ] || { echo "Cap Python amb numpy, scipy, astropy, sunpy, rawpy, cv2 i matplotlib: afegeix-los a ~/.venvs/eines-ia-py312"; exit 1; }
exec "$PY" "$@"
