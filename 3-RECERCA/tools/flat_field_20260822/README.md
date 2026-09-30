# Màsters flat posteriors del 22-08-2026

Eines no-clobber per construir i auditar els flats de cel del Vixen/R6 III i
del Sony A7RIIIA/FE 300 mm. Treballen en CFA lineal, abans de debayer, sense
WB ni denoise, i no modifiquen originals ni màsters S6.

## Execució reproduïble

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/USUARI/.venvs/eines-ia-py312/bin/python -u \
  research/tools/flat_field_20260822/build_master_flats.py \
  --train vixen --out output/flats_20260822/vixen_r6iii_posterior_v1

PYTHONDONTWRITEBYTECODE=1 /Users/USUARI/.venvs/eines-ia-py312/bin/python -u \
  research/tools/flat_field_20260822/build_master_flats.py \
  --train sony --out output/flats_20260822/sony_a7r3a_300mm_posterior_v1

PYTHONDONTWRITEBYTECODE=1 /Users/USUARI/.venvs/eines-ia-py312/bin/python -u \
  research/tools/flat_field_20260822/evaluate_transfer.py \
  --vixen output/flats_20260822/vixen_r6iii_posterior_v1 \
  --sony output/flats_20260822/sony_a7r3a_300mm_posterior_v1 \
  --out output/flats_20260822/transfer_assessment_v1
```

Totes les destinacions han de ser inexistents. Cada construcció usa staging i
promoció atòmica. `SHA256SUMS.txt` segella tots els productes.

## Contracte dels productes

L'ordre de plans als NPY és `R,G1,G2,B`. Els FITS són mosaics RGGB 2-D:

- Vixen: 4640×6960, exactament la reixa S6 `raw_image[108:4748,172:7132]`;
- Sony: 5320×7968, exactament `raw_image_visible`.

`MASTER_FULL` és el flat de sessió i queda en quarantena de transferència.
`MASTER_OPTICAL_RADIAL` és la component invariant a rotació.
`MASTER_OPTICAL_EVEN180` elimina el gradient lineal multiplicatiu amb mitjana
geomètrica en log. `MASTER_OPTICAL_SMOOTH2D` conserva camp no radial i pot
contenir gradient de cel. `MASTER_FINE_SENSOR_FACTOR` és el PRNU fi amb shrink
Wiener i defectes grossos exclosos.

Cap d'aquests fitxers no es pot dividir sobre un S6 ja registrat: flat i warp
no commuten. Qualsevol promoció recalibra RAW originals en una branca nova i
propaga per separat variància aleatòria i incertesa compartida del flat.

