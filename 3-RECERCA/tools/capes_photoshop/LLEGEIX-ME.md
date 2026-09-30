# Lectura de TIFF amb capes de Photoshop (17-08-2026)

Photoshop desa les capes d'un TIFF al tag `ImageSourceData` (37724), en un
bloc «Adobe Photoshop Document Data V0002» que als Mac Intel/Apple Silicon
va en **little-endian** (`MIB8` = `8BIM` girat). ⚠️ **Hi ha dos formats
segons la mida del document** (après el 17-08 al vespre amb `Ajust.tif`):

| | document GRAN (`UnintCapes3`, 12 capes 6960×4640) | document PETIT (`Ajust`, 2 capes 4425×2835) |
|---|---|---|
| longitud del bloc `Lr16` | 8 bytes | 4 bytes |
| longitud de cada canal | 8 bytes (estil PSB) | 4 bytes |
| recompte de capes | just després de la longitud | ídem |

Els dos lectors ho **autodetecten** amb la primera capa (rect plausible i
longitud de canal ≤ w·h·2+2). I una segona trampa: **els píxels de 16 bits de
les capes van en big-endian** encara que el TIFF i les capçaleres siguin
little-endian; llegits al revés surten com a soroll de colors amb el disc
lunar encara visible. `extreu_capes.py` tria l'ordre pel gradient entre veïns.
`psd-tools` (instal·lat a `~/.venvs/eines-ia-py312`) no obre TIFF, però el
seu `decompress` serveix per als canals. Els dos scripts accepten el camí del
TIFF com a primer argument.

Els objectes intel·ligents col·locats porten el bloc `SoLd` amb un descriptor
(claus de 4 bytes girades, números LE): `Trnf` són les vuit coordenades de
les cantonades al llenç i `Sz` la mida original. D'aquí surt la transformació
que l'operador ha aplicat a mà (escala, gir i posició), sense haver-la
d'endevinar dels píxels.

- `llegeix_capes.py`: estructura (noms, fusió, opacitat, visibilitat, mides).
- `extreu_capes.py`: RGB + màscara de cada capa, reduïts ×4, a `.npz`.
- `analitza_capes.py`: cobertura de cada màscara per radi i pes efectiu de
  cada capa al compost (Normal, de dalt a baix).
- `compara_amb_foto.py`: nivell, color, bandes, anells per sector i gra
  contra la FOTO del pipeline.

Revisió del `UnintCapes3.tif` de Pere: `research/76` §5 quaterdecies.

Ajust de `POWAAAH3` (earthshine de la Sony) sobre `Ajust.tif`: `research/76`
§5 quindecies i `Corona_HDR_Vixen/POWAAAH3_ajustada_transformacio.json`.

## 18-08-2026 (vespre): els filtres de Pere al llenç de 7648×5353

Pere té a `~/Desktop/Eclipse 2026/Projecte photoshop/2-Filtres/` tres TIFF de
Photoshop amb capes a **tres llenços diferents** (`Aplicant_Filtres.tif` 7648×5353,
`filtres_Tangencials.tif` 6961×4641, `filtres_radials.tif` 6748×4553) més
productes del pipeline (`corona_vixen_PASSALT_FORT.tif`, `_detall.png`, `_radial.png`,
a la reixa de `Corona_HDR_Vixen`), i els vol tots com a capes al llenç E de
7648×5353 per provar-los de filtre de pas alt.

- `capes_tiff.py`: lector de capes **a resolució completa** (classe `TiffCapes`:
  `.capes`, `.canal(k, cid)`, `.rgb(k)`, `.resum()`); autodetecta les longituds de
  4/8 bytes i l'endianitat dels píxels; substitueix `extreu_capes.py` quan cal el
  píxel sencer. Els TIFF de Pere del 18-08 porten la signatura «…Data Block»,
  longituds de 4 bytes i canals **sense comprimir**.
- `inventari_2filtres.py`: estructura, estadístiques i previsualitzacions ×8 de tot
  el que hi ha a la carpeta.
- `mesura_alineacio_filtres.py`: on cau cada imatge dins E (correlació creuada del
  passa-alt, subpíxel per DFT; el signe està comprovat amb un desplaçament conegut i
  explicat al docstring). Resultat: Tangencials → E + (456, 462), radials → E +
  (599, 549), tots dos a 0,00 px; reixa del pipeline → E + (542,6, 418,5) ± 0,1.
- `alinea_filtres_al_llenc.py`: construeix `Filtres_alineats_7648x5353.psb` (base +
  9 capes al seu lloc, amagades, amb el mode de fusió d'origen; psd-tools via
  `../encaix_sony/psb_utils.py`) i els TIFF plans d'`alineades_7648x5353/`.
- `verifica_filtres_al_llenc.py`: reobre els lliurables i torna a mesurar (tot a
  ≤ 0,05 px de mediana; capes del PSB byte a byte iguals a la font).

Trampes trobades: (1) el signe de la correlació —«la font cau a −1,7» vol dir
posar-la 1,7 px més a la dreta; el primer intent va restar en lloc de sumar i va
sortir 3 px fora, i la verificació ho va enxampar—; (2) `a`, `b` i `filtre radial A`
són pas alt **invertit** (correlació −0,97 amb el pas alt de la base): la mesura s'ha
de fer amb el signe girat, i en Overlay/Linear Light suavitzen; (3) les capes `1`,
`2`, `3` del Tangencials són byte a byte iguals; (4) els `*_llencPere.tif` de
`Corona_HDR_Vixen` porten un residu de fins a 0,8 px que varia pel camp respecte
de l'original: no s'han fet servir. Nota: `research/80` §14; LLEGEIX-ME a la carpeta
de Pere: `2-Filtres/LLEGEIX-ME_alineades.md`.
