# Eines del PDF «Els filtres de la corona» (17-09-2026)

Generen les imatges de `4-RESULTATS/pdf_filtres_brno_20260917/font/img/` i els rebuts de `…/rebuts/`. Només llegeixen `1-PHOTOSHOP/V77.psb` i `V80.tif`.

Intèrpret: el que torni `.claude/skills/apilatge-imatges-eclipsi/scripts/comprova_entorn.py --python` (cal numpy, scipy, opencv, Pillow, matplotlib, psd-tools; per al PDF, WeasyPrint).

Ordre, des d'aquesta carpeta:

| Pas | Què fa |
|---|---|
| `1_extreu_capes.py` | Llegeix les capes de filtre, la base i la fusionada de la V77; desa reduccions ÷5 (llenç sencer) i ÷2 (zona central) a la carpeta de treball |
| `2_imatges_capes.py` | Portada, tires de cada capa i parella abans/després |
| `3_espenak_real.py` | La recepta d'Espenak (gir de 10°, resta, producte) sobre la nostra base |
| `4_sintetic_tangencial.py` | Simulació: màscara en arc contra màscara rodona adaptativa |
| `5_sintetic_lineal.py` | Simulació: compondre en lineal contra compondre fotos revelades |
| `6_grafics.py` | Els dos gràfics de la figura 6 (vectorials) |

Els intermedis (uns 0,9 GB de `.npy`) van a una carpeta temporal fora del projecte; es pot triar amb la variable `PDF_FILTRES_TREBALL` i es pot esborrar en acabar. `comu.py` troba l'arrel del projecte pujant fins a la carpeta que conté `CLAUDE.md`: cap ruta absoluta.
