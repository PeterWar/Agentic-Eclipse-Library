#!/bin/bash
# V128 amb la regla del limbe (12-10-2026): la capa A refeta perquè la correcció arribi fins on hi ha dada al limbe
# (regla predeclarada a resultats/v128_extincio_20261012/PREDECLARACIO_LIMBE.md) i la capa B amb data al nom.
#   v1  · (només si falta) la capa A anterior, OUT_rgb16.npy, i E_u16.npy: l'e3 tal com és
#   v1b · la capa A nova amb la regla del limbe, i les proves P1–P10 de la predeclaració
#   v2b · escriu la V128.psb a la carpeta de treball (mateix escriptor de bytes del v2; sense psd-tools)
#   v3b · la verifica: psd-tools, lector cru propi, sips i ael.photoshop.verify() (pren ael del clon 3-AEL/repo)
#   (mou la V128 a 1-PHOTOSHOP només si el v3b PASSA i allà no n'hi ha cap; no sobreescriu mai)
#   v4b · vistes noves (b01–b05) a Sortides/v128_extincio_20261012/; b05 és el gràfic del perfil del limbe, en lloc de retalls
#   v5b · portes de la skill, amb veredictes separats
# Ús: executa_b.sh <carpeta_de_treball>   (fora del projecte; s'hi deixen els fitxers grossos de treball)
# Només llegeix la V125-FINAL.psb. Mai obre el Photoshop.
# Si 1-PHOTOSHOP/V128.psb ja existeix, s'atura abans de moure-hi res: retirar-la és un pas a part, amb
#   paperera.py --lot <lot> --motiu "…" 4-Photoshop/1-PHOTOSHOP/V128.psb   (4-Photoshop/2-ARXIU/neteja_20261003/)
set -e
AQUI="$(cd "$(dirname "$0")" && pwd)"
FOTO="$(cd "$AQUI/../../../1-PHOTOSHOP" && pwd)"
TREB="${1:?Ús: executa_b.sh <carpeta_de_treball>}"
mkdir -p "$TREB"
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=4
PY=""
for c in "$HOME/.venvs/eines-ia-py312/bin/python" python3.12 python3; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c "import numpy, scipy, astropy, psd_tools, PIL, matplotlib, cv2, tifffile" 2>/dev/null; then PY="$c"; break; fi
done
[ -n "$PY" ] || { echo "Cap Python amb numpy, scipy, astropy, psd-tools, Pillow, matplotlib, opencv i tifffile: afegeix-los a ~/.venvs/eines-ia-py312"; exit 1; }
if [ ! -f "$TREB/OUT_rgb16.npy" ] || [ ! -f "$TREB/E_u16.npy" ]; then
  "$PY" "$AQUI/v1_correccio.py" "$TREB"
fi
"$PY" "$AQUI/v1b_correccio_limbe.py" "$TREB"
"$PY" "$AQUI/v2b_escriu_psb.py" "$TREB"
"$PY" "$AQUI/v3b_verifica.py" "$TREB/V128.psb" "$TREB"
[ ! -e "$FOTO/V128.psb" ] || { echo "$FOTO/V128.psb ja existeix: no se sobreescriu. La nova és a $TREB/V128.psb (verificada)."; exit 1; }
mv -n "$TREB/V128.psb" "$FOTO/V128.psb"
"$PY" "$AQUI/v4b_vistes.py" "$FOTO/V128.psb" "$TREB"
"$PY" "$AQUI/v5b_portes.py" "$TREB"
