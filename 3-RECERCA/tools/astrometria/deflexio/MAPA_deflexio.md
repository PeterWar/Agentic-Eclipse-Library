# MAPA — subàrea `deflexio` (deflexió gravitatòria sobre les dades del 12-08-2026)

Promoció del 17-08-2026 dels scripts del rescat
`research/tools/rescat_scratchpad_2026-08-17/deflexio_apod_2027_16-08/` (sessió 604fa71e del 16-08)
i del generador de la màscara d'estrelles que vivia a `~/Desktop/Eclipse 2026/Estrelles/`.
Cap algorisme, llindar ni constant no ha canviat: només les rutes, que ara surten totes de
`../comu.py`, i un script nou (`fusiona_csv.py`) que fa per programa el que el 16-08 es va fer a mà.

## 1. Fitxer promogut → origen

| Promogut (`research/tools/astrometria/deflexio/`) | Origen | Què canvia |
|---|---|---|
| `fusiona_csv.py` | **NOU** (no hi havia generador: `estrelles_*.csv` es van escriure a mà el 16-08 15:58) | construeix `estrelles_sony.csv` i `estrelles_r6.csv` a `comu.out()` |
| `deflexio.py` | `deflexio_apod_2027_16-08/deflexio.py` | `BASE` → `comu.out()`; `load("…/de440s.bsp")` → `comu.efemeride()` |
| `retall_estrella.py` | `deflexio_apod_2027_16-08/retall_estrella.py` | `SORTIDA` → `comu.apod()`; RAW → `comu.DADES_VIXEN_UNF/572A2983.CR3`, `comu.DADES_300MM/DSC06993.ARW` |
| `moviments.py` | `deflexio_apod_2027_16-08/moviments.py` | `load("…/de440s.bsp")` → `comu.efemeride()` |
| `mascara_estrelles.py` | `~/Desktop/Eclipse 2026/Estrelles/mascara_estrelles.py` (16-08 15:58) | `AQUI` (dir de l'script = Estrelles/) → `comu.out()`; `dir` dels RAW → `comu.DADES_300MM` / `comu.DADES_VIXEN_UNF` |

Cap fitxer del rescat s'ha tocat. La cadena 3 (pla 2027: requisits, forecast2027, eclipsi2027,
model/eb_core, step*, …) queda **fora** de la promoció, com diu la síntesi §5: es conserva com a
evidència al rescat.

## 2. Ordre d'execució (des de qualsevol cwd; `$PY` = l'intèrpret que dona `comprova_entorn.py --python`)

```
$PY research/tools/astrometria/deflexio/fusiona_csv.py          # ~0,1 s
$PY research/tools/astrometria/deflexio/deflexio.py             # ~2 s   (stdout: σ(ε))
$PY research/tools/astrometria/deflexio/retall_estrella.py      # ~1 s   (APOD/retalls_estrelles.json)
$PY research/tools/astrometria/deflexio/moviments.py            # ~2 s   (stdout: els 15 moviments)
$PY research/tools/astrometria/deflexio/mascara_estrelles.py sony    # ~3 s
$PY research/tools/astrometria/deflexio/mascara_estrelles.py vixen   # ~7 s
```

`pipeline_estrelles.sh` hi correspon amb les etapes `deflexio` (els quatre primers) i `mascara`
(els dos últims). `mascara` ha d'anar **abans** de `apod`: `render_net.py` i `munta_video.sh`
llegeixen `estrelles_*_marcades.png`.

## 3. Entrades i sortides

| Script | Llegeix | Escriu |
|---|---|---|
| `fusiona_csv.py` | `work("sony")/catalog_sony.txt` (final3.py, 38 fonts) · `work("vixen")/catalog_vixen_fonts.csv` (cat_final.py, 32 candidates) · `work("xmatch")/IDENTIFICACIONS_{sony,r6}.csv` (38 i 21) · `work("xmatch")/final_match_{sony,r6}.csv` (complement: hi ha `V10 = HIP 46464`, que la llista fotomètrica va deixar fora per ser a 79 px de la vora → 22/24) | `out()/estrelles_sony.csv` (38 files) · `out()/estrelles_r6.csv` (24 files: A-00…A-21, B-11, B-24, B-26; les 8 REBUTJADA no hi van) |
| `deflexio.py` | `out()/estrelles_{sony,r6}.csv`, DE440s | stdout |
| `retall_estrella.py` | els dos RAW; posicions de HIP 46345/46335/46232 incrustades (copiades dels CSV) | `apod()/retalls_estrelles.json` |
| `moviments.py` | DE440s | stdout |
| `mascara_estrelles.py <tren>` | RAW del tren; `out()/estrelles_{sony,r6}.csv` | `out()/estrelles_<tren>_marcades.png`, `out()/estrelles_<tren>_zooms.png` |

## 4. Què s'ha provat i amb quin resultat (17-08-2026, 19:33–19:37)

Variables: `ESTRELLES_WORK=~/Desktop/Eclipse 2026/_prova_skill/Estrelles_work`,
`ESTRELLES_OUT=…/_prova_skill/Estrelles`, `APOD_OUT=…/_prova_skill/APOD`; intèrpret
`~/.venvs/eines-ia-py312/bin/python`; executat amb cwd `/tmp` per demostrar que no depèn del cwd.

Entrades del WORK de prova: `catalog_sony.txt`, `catalog_vixen_fonts.csv`, `IDENTIFICACIONS_sony.csv`
i `final_match_*.csv` ja hi eren (les havien deixat les subàrees sony/vixen/xmatch; verificat amb
`cmp` que són **byte-idèntics** als del rescat); `IDENTIFICACIONS_r6.csv` l'he copiat jo del rescat.

| Prova | Resultat | Contra el publicat |
|---|---|---|
| `fusiona_csv.py` | 38 files (38 amb nom) i 24 files (22 amb nom) | 38/38 i 22/24 ✓ |
| `deflexio.py` | R☉ 946,66″, alt 9,07°, α limbe 1,7516″; forecast de Fisher σ(ε) similitud rms/√2 = **1,39** (Sony) / **0,57** (Vixen), combinat **0,53** —sensibilitat teòrica 1,9σ GR i 0,9σ GR–Newton, **no detecció mesurada**—; HIP 46345 r=2,65 R☉ 0,660″ predit = 0,307 px (Vixen) / 0,206 px (Sony); HIP 46335 0,812″ predit, 0,378/0,253 px | números ✓. A la promoció del 17-08 la sortida era **idèntica** (diff) a la del rescat, tret de la columna «estrella»; el 20-08 només s'han corregit docstring i etiquetes perquè diguin explícitament «forecast, no detecció», sense tocar cap càlcul ni número |
| `retall_estrella.py` | HIP 46345 vixen 0,660″ = 0,307 px, sony 0,206 px; HIP 46335 0,812/0,811″ | `retalls_estrelles.json` **byte-idèntic** al viu de `~/Desktop/Eclipse 2026/APOD/` (cmp) |
| `moviments.py` | 15 moviments (2289″ salt … 0,128″) | stdout **idèntic** (diff) al de l'script del rescat |
| `mascara_estrelles.py sony` | offset (−3,0, −3,0) → **17/38** visibles al fotograma sol | 17/38 ✓; PNG: 1,65 % de píxels diferents del viu (les etiquetes noves: 38 noms en lloc de 12) |
| `mascara_estrelles.py vixen` | offset (+3,0, 0,0) → **22/24** | 22/24 ✓; PNG: 0,30 % de píxels diferents (etiquetes) |

## 5. Què he hagut de canviar (línia a línia)

- `deflexio.py`: `BASE = "/Users/USUARI/Desktop/Eclipse 2026/Estrelles"` → `BASE = str(comu.out())`;
  `eph = load("/Users/USUARI/.cache/skyfield/de440s.bsp")` → `eph = comu.efemeride()`. Cap constant
  tocada (escales 3,2020/2,1495, centres del Sol, rms 0,71/0,42, G/M☉/c/R☉).
- `moviments.py`: només l'efemèride, igual que a dalt.
- `retall_estrella.py`: `SORTIDA`, i els dos `path=` dels RAW. Constants R_SOL 946,66, ALPHA 1,7516,
  N=21, offset (−227,6, +706,5) i posicions incrustades: intactes.
- `mascara_estrelles.py`: `AQUI = os.path.dirname(...)` → `AQUI = str(comu.out())` (llegeix el CSV i
  escriu els PNG allà, on abans era «al costat d'aquest fitxer»); `dir=` dels dos trens. Res més.
- `fusiona_csv.py` (nou): el format és el de la capçalera viva `id,x,y,nom,senyal,fwhm,nota`.
  Diferències conscients respecte de la versió a mà, cap de les quals llegeix cap consumidor
  (`deflexio.py` usa id/x/y/nom; `mascara_estrelles.py` usa id/x/y/nom i el `V=` del nom):
  1. **«nom» a totes les identificades** (38/38 i 22/24; a mà n'hi havia 12 i 9, escrites abans del
     creuament complet). Conseqüència visible: més cercles grocs i etiquetes a les marcades.
  2. Sense el nom de Flamsteed («8 Leonis», «7 Leonis», «11 Leonis»): no és a cap entrada.
  3. `senyal`/`fwhm`/`nota` construïts amb el mateix patró però sense la prosa («La més brillant del
     camp», «Verificada píxel a píxel…»). El FWHM en px de la Sony surt de FWHM_as/3,234 (a mà
     s'havia fet a l'inrevés: 3,45 px → 11,2″; ara 11,2″ → 3,46 px).
  4. **Correcció d'un lapsus de la versió a mà**: `A-17` hi duia «V18 = TYC 826-1182-1» i `A-18` cap
     nom; per posició (final_match_r6: V17 = (277,29, 4323,58), V18 = (413,76, 3482,35)) `A-17` és
     **V17 = HIP 46486** i `A-18` és **V18 = TYC 826-1182-1**. La fusió ho posa bé.
  5. La Sony arrodoneix x,y a 0,1 px (com a mà: 5549,87 → 5549,9); l'R6 conserva 0,01 px.

## 6. Pendent / límits

- `retall_estrella.py`, `moviments.py` i `animacio.py` duen R☉ = 946,66″ i α = 1,7516″ copiats a mà
  del que calcula `deflexio.py` (verificat: 946,660″ / 1,75164″); `comu.R_SOL_ARCSEC` és 947,07
  (suns.json). No s'ha unificat per no canviar cap número (síntesi §6.7).
- El σ(ε) de `deflexio.py` és una previsió de Fisher, no una mesura (mapes, nota 1).
- `mascara_estrelles.py` amb `exp` per EXIF (quan no hi ha `defecte`) crida `exiftool` del PATH:
  no s'exercita perquè els dos trens tenen fotograma per defecte.
