#!/bin/bash
# Extinció diferencial: costat a costat per a Pere (12-10-2026). Refà tot: e1 (massa d'aire al marc de la final),
# e2 (pis 1, compost lineal), e3 (pis 2, aproximació sobre la V125-FINAL), e4 (rebut amb els SHA-256), e5 (mesures del
# LLEGEIX-ME_v2) i e6 (rebut v2). Atenció: el ple refà el rebut v1 amb el codi actual; e6 ho detecta i ho diu.
# Només llegeix la cau b3 de la V42 i la V125-FINAL.psb (psd-tools; mai el Photoshop). Escriu a
# 4-Photoshop/Sortides/extincio_diferencial_20261012/ i 4-Photoshop/3-RECERCA/resultats/extincio_diferencial_20261012/.
# Ús: executa.sh            (tot)
#     executa.sh e3_pis2_final_aproximacio.py   (un guió)
set -e
AQUI="$(cd "$(dirname "$0")" && pwd)"
export PYTHONDONTWRITEBYTECODE=1
# cap intèrpret escrit a pèl: el primer que tingui el que cal
PY=""
for c in "$HOME/.venvs/eines-ia-py312/bin/python" python3.12 python3; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c "import numpy, scipy, astropy, psd_tools, PIL, matplotlib, rawpy" 2>/dev/null; then PY="$c"; break; fi
done
[ -n "$PY" ] || { echo "Cap Python amb numpy, scipy, astropy, psd-tools, Pillow, matplotlib i rawpy: afegeix-los a ~/.venvs/eines-ia-py312"; exit 1; }
if [ $# -gt 0 ]; then
  "$PY" "$AQUI/$1"
else
  for g in e1_massa_aire_final.py e2_pis1_compost_lineal.py e3_pis2_final_aproximacio.py e4_rebut.py e5_mesures_llegeixme_v2.py e6_rebut_v2.py; do
    echo "== $g"; "$PY" "$AQUI/$g"
  done
fi
