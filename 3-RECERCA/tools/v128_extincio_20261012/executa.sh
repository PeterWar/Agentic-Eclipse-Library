#!/bin/bash
# V128 (12-10-2026): la V125-FINAL + la correcció de l'extinció diferencial (aproximació sobre la final) com a capa.
#   v1 · la imatge corregida: executa l'e3 de extincio_diferencial_20261012 TAL COM ÉS (sortides desviades) i en desa la matriu
#   v2 · escriu la V128.psb a la carpeta de treball (còpia de bytes de la V125-FINAL + 2 capes; sense psd-tools)
#   v3 · la verifica amb psd-tools, un lector cru propi i sips
#   (mou la V128 a 1-PHOTOSHOP només si el v3 PASSA; no sobreescriu mai)
#   v4 · vistes del llenç sencer a Sortides/v128_extincio_20261012/
#   v5 · portes de la skill, amb veredictes separats
# Ús: executa.sh <carpeta_de_treball>   (fora del projecte; s'hi deixen els fitxers grossos de treball)
# Només llegeix la V125-FINAL.psb. Mai obre el Photoshop. El v2 s'atura si 1-PHOTOSHOP/V128.psb ja existeix.
set -e
AQUI="$(cd "$(dirname "$0")" && pwd)"
FOTO="$(cd "$AQUI/../../../1-PHOTOSHOP" && pwd)"
TREB="${1:?Ús: executa.sh <carpeta_de_treball>}"
mkdir -p "$TREB"
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=4
PY=""
for c in "$HOME/.venvs/eines-ia-py312/bin/python" python3.12 python3; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c "import numpy, scipy, astropy, psd_tools, PIL, matplotlib, cv2, tifffile" 2>/dev/null; then PY="$c"; break; fi
done
[ -n "$PY" ] || { echo "Cap Python amb numpy, scipy, astropy, psd-tools, Pillow, matplotlib, opencv i tifffile: afegeix-los a ~/.venvs/eines-ia-py312"; exit 1; }
[ ! -e "$FOTO/V128.psb" ] || { echo "$FOTO/V128.psb ja existeix: no es refà ni se sobreescriu"; exit 1; }
"$PY" "$AQUI/v1_correccio.py" "$TREB"
"$PY" "$AQUI/v2_escriu_psb.py" "$TREB"
"$PY" "$AQUI/v3_verifica.py" "$TREB/V128.psb" "$TREB"
mv -n "$TREB/V128.psb" "$FOTO/V128.psb"
"$PY" "$AQUI/v4_vistes.py" "$FOTO/V128.psb" "$TREB"
"$PY" "$AQUI/v5_portes.py" "$TREB"
