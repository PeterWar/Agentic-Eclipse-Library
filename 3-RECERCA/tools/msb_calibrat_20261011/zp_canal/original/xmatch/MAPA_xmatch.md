# MAPA — subàrea `xmatch` (creuament, placa, fotometria absoluta)

Promoció del 17-08-2026 dels scripts de
`research/tools/rescat_scratchpad_2026-08-17/estrelles_placa_flats_16-08/xmatch/`
(sessió ea55df18 del 16-08-2026) a `research/tools/astrometria/xmatch/`.
Cap algorisme, llindar, constant ni ordre de fotogrames s'ha tocat; l'única
excepció és la correcció ordenada a `corona2.py` (terme de color del Sol), que
s'imprimeix amb i sense el terme. Tot el que abans anava al cwd o a `../` passa
per `comu.py`.

## 1. Fitxer promogut → fitxer d'origen

| Promogut | Origen (rescat xmatch/) | Paper | Canvis (a més de la capçalera comuna) |
|---|---|---|---|
| `cat.py` | `cat.py` | catàleg Tycho-2 profund + V d'Hipparcos, pla tangent equatorial, dos instants; escriu `cat_{sony,r6}.csv`, `suns.json` | `load('/Users/…/de440s.bsp')` → `comu.efemeride()`; `'tyc2_deep.tsv'` → `comu.TYC2_DEEP`; `'../hip_main.dat'` (×2) → `comu.HIP_MAIN` |
| `cat2.py` | `cat2.py` | tres projeccions (equatorial, horitzontal refractada, horitzontal sense refracció); `cat2_{sony,r6}.csv`, `suns2.json` | efemèride → `comu.efemeride()` |
| `solve.py` | `solve.py` | `load_dets` (biblioteca) + cerca grollera → `coarse.json` | `'../sony_stars/catalog_sony.txt'` → `comu.work('sony')/'catalog_sony.txt'`; `'../vixen/catalog_vixen_fonts.csv'` → `comu.work('vixen')/'catalog_vixen_fonts.csv'` |
| `refine.py` | `refine.py` | **només biblioteca**: `predict`, `fit_affine`, `fit_similarity` que importen `refine3.py`/`final_solve.py`. El seu `__main__` (solution.json, par_*.npy, match_*.csv) és el pas superat i **no s'executa** a la cadena | cap |
| `refine3.py` | `refine3.py` | cerca grollera per marc + refinament afí/similitud (impressions de diagnòstic, `frames.pkl`) | cap |
| `final_solve.py` | `final_solve.py` | solució de placa definitiva (lineal i radial) → `final_solution.json`, `final_match_{sony,r6}.csv` | efemèride → `comu.efemeride()`; **afegit** còpia dels tres productes a `comu.out()` |
| `phot2.py` | `phot2.py` | fotometria d'obertura fotograma a fotograma → `phot_{sony,r6}.npz` | `SONY_DIR` → `str(comu.DADES_300MM)+'/'`; `../sony_stars/{offsets6.pkl, masterdark_*s.npy, bkg_*.npy}` → `comu.work('sony')/…`; `../vixen/{shifts_start.json, res_*.npy, msk_*.npy}` → `comu.work('vixen')/…` |
| `cog2.py` | `cog2.py` | corba de creixement i correcció d'obertura → `cogf_{sony,r6}.npz` | cap |
| `zp.py` | `zp.py` | ZP∞, k, c amb retall 2,5σ → `zp.json`, `zp_{sony,r6}.csv` | efemèride → `comu.efemeride()` |
| `zp2.py` | `zp2.py` | ZP reparametritzat a X☉, vuit models → `zp2.json`, `zp2_{sony,r6}.csv` | **afegit** còpia de `zp2.json` a `comu.out()` |
| `bemporad.py` | `bemporad.py` | prova de Bemporad → `pairs_*.csv`, `bemp_*.csv` | cap |
| `identificacions.py` | **NOU** (no era al rescat) | escriu `IDENTIFICACIONS_{sony,r6}.csv` amb el format dels rescatats; còpia a `comu.out()` | vegeu §4 |
| `corona2.py` | `corona2.py` | perfil de corona i factor B/B☉ → `corona2.csv` | `SONY`/`VIX` → `comu.DADES_300MM`/`comu.DADES_VIXEN_UNF`; **terme de color** (§5); columna nova `fac_nocolor`; còpia a `comu.out()` |
| `wings.py` | `wings.py` | ales de la PSF apilades → `wings_{sony,r6}.npz`, `wings.json` | `SONY`/`VIX` com a dalt; `../sony_stars/…` i `../vixen/…` → `comu.work(...)`; halo_params absolut → `comu.HALO_PARAMS`; còpia de `wings.json` a `comu.out()` |
| `wings2.py` | `wings2.py` | prova d'integral i model de halo | halo_params absolut → `comu.HALO_PARAMS` |
| `orient.py` | `orient.py` | eix nord lunar al sensor, 71,97° contra 71,5° | efemèride → `comu.efemeride()` |
| `summary.py` | `summary.py` | prova del radi, candidates recuperades, taula de placa → `radi_{sony,r6}.csv` | cap |
| — | `tyc2_deep.tsv` | dada (VizieR I/259, 5°, VT<12,5) | **no es copia**: viu a `comu.TYC2_DEEP` (`Estrelles/catalegs/tyc2_deep.tsv`, byte-idèntic al del rescat) |

Capçalera comuna afegida a tots (les úniques línies noves fora de la taula):

```python
#!/usr/bin/env python3
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu
os.chdir(comu.work("xmatch"))
```

**No promoguts** (superats o erronis, es queden al rescat): `solve2.py`, `refine2.py`,
`phot.py`, `corona.py`, `repeat.py`, `solution.json` (mirall=True). `refine.py`
es promou només com a biblioteca.

## 2. Ordre d'execució exacte

`$PY` és l'intèrpret detectat per
`.claude/skills/postprocessat-corona/scripts/comprova_entorn.py --python`
(avui `~/.venvs/eines-ia-py312/bin/python`). Es poden llançar des de qualsevol
cwd; tots fan `os.chdir(comu.work("xmatch"))`. Rutes relatives a
`research/tools/astrometria/`.

Etapa **xmatch** (barata, ~10 s en total):

```
$PY xmatch/cat.py            # ~1 s   → cat_*.csv, suns.json
$PY xmatch/cat2.py           # ~0,4 s → cat2_*.csv, suns2.json
$PY xmatch/solve.py          # ~0,6 s → coarse.json
$PY xmatch/refine3.py        # ~4,7 s → frames.pkl (diagnòstic dels tres marcs)
$PY xmatch/final_solve.py    # ~3,2 s → final_solution.json, final_match_*.csv (+ còpia a OUT)
```

Etapa **fotometria** (~35 s en total; phot2/corona2/wings llegeixen RAW):

```
$PY xmatch/phot2.py          # ~4 s   → phot_*.npz   (7 ARW + res_/msk_ del Vixen)
$PY xmatch/cog2.py           # ~0,2 s → cogf_*.npz
$PY xmatch/zp.py             # ~0,3 s → zp.json, zp_*.csv
$PY xmatch/zp2.py            # ~0,2 s → zp2.json (+ còpia a OUT), zp2_*.csv
$PY xmatch/bemporad.py       # ~0,2 s → pairs_*.csv, bemp_*.csv
$PY xmatch/identificacions.py# ~0,2 s → IDENTIFICACIONS_*.csv (+ còpia a OUT)
$PY xmatch/corona2.py        # ~17 s  → corona2.csv (+ còpia a OUT)   (6 RAW de corona)
$PY xmatch/wings.py          # ~7 s   → wings_*.npz, wings.json (+ còpia a OUT)
$PY xmatch/wings2.py         # ~0,5 s (només impressions)
$PY xmatch/orient.py         # ~0,1 s (només impressions)
$PY xmatch/summary.py        # ~0,2 s → radi_*.csv
```

`identificacions.py` va **després de `bemporad.py`** perquè `flux_tot`, `Vobs` i
`dV` surten de `bemp_*.csv`. Si es crida abans (per exemple a l'etapa xmatch),
escriu la taula amb aquestes tres columnes buides i ho diu; llavors cal
tornar-hi després de bemporad.

## 3. Entrades i sortides

Entrades (per `comu.py`):

- `comu.TYC2_DEEP` (tyc2_deep.tsv), `comu.HIP_MAIN` (hip_main.dat), `comu.efemeride()` (de440s.bsp);
- `comu.work('sony')/catalog_sony.txt` (final3.py de la subàrea sony) i, per a phot2/wings, `offsets6.pkl`, `masterdark_{1,2,8}s.npy`, `bkg_DSC069{84,85,87,91,93,96,99}.npy`;
- `comu.work('vixen')/catalog_vixen_fonts.csv` (cat_final.py de la subàrea vixen) i, per a phot2/wings, `shifts_start.json`, `res_572A29{78..84,96}.npy`, `msk_*.npy`, `dark_med_{1,2,10}.npy`;
- RAW (només lectura): `comu.DADES_300MM` (ARW de fotometria i DSC06982/83/86 de corona), `comu.DADES_VIXEN_UNF` (572A2970/71/77 de corona);
- `comu.HALO_PARAMS`.

Sortides: tot a `comu.work('xmatch')`; els productes finals també a `comu.out()`:
`final_solution.json`, `final_match_sony.csv`, `final_match_r6.csv`,
`IDENTIFICACIONS_sony.csv`, `IDENTIFICACIONS_r6.csv`, `zp2.json`, `corona2.csv`,
`wings.json`.

## 4. `identificacions.py` (nou)

Format deduït dels rescatats i reproduït exactament (columnes, ordre de files,
valors: diferència màxima 5e-15 a `R_Rsol`, la resta idèntica):

`det, HIP, TYC, HD, Sp, V, BV, R_Rsol, resid, flux_tot, snr, Vobs, dV`

- `det…BV, resid, snr` de `final_match_<tag>.csv` (ja ordenat per V);
- `R_Rsol = hypot(x − sun_x, y − sun_y) · escala / 947,07` amb `final_solution.json[tag]`
  (la solució **lineal**, no la `_radial`: és l'única combinació que reprodueix
  el rescat a 1e-15; el `_radial` s'hi desvia 0,04);
- `flux_tot, Vobs, dV` de `bemp_<tag>.csv`; només les files amb fotometria (R6: 21 de 22, com al rescat).

## 5. La correcció de `corona2.py` (l'única que canvia un número)

Abans: `fac = π·R☉px²/10^(0,4·(ZP☉+26,75))` → 1,188e-11 (Sony), 2,534e-11 (R6).
Ara:

```python
BV_SOL = 0.653
c_col = zp2[tag]['c']
fac_nocolor = np.pi*Rsun_px**2/10**(0.4*(zp2[tag]['ZPsun']+26.75))
fac         = np.pi*Rsun_px**2/10**(0.4*(zp2[tag]['ZPsun']+26.75-BV_SOL*c_col))
```

Motiu: el ZP s'ha ajustat amb `V − m_inst = ZP − k(X−X☉) − c(B−V)`, o sigui que el
flux instrumental del Sol és `10^(0,4(ZP + 26,75 − 0,653·c))` (és el que
skeptic2/chain.py feia a mà). Sortida: **1,1352e-11 (Sony, ×0,9553) i 2,7714e-11
(R6, ×1,0936)**, sense color 1,1883e-11 / 2,5342e-11; quocient R6/Sony a
1,15–3 R☉ **0,952** (0,831 sense color). `corona2.csv` porta ara `fac` (amb color)
i `fac_nocolor` (l'antic `fac`, idèntic al del rescat); la taula B/B☉ impresa
usa el `fac` amb color.

## 6. Què s'ha provat i amb quin resultat

Entorn: `~/.venvs/eines-ia-py312/bin/python`; `py_compile` de tots els .py verd;
`grep -rn "/private/tmp\|/Users/USUARI"` al directori: zero.

**Prova A — WORK oficial de la skill** (`ESTRELLES_WORK=…/_prova_skill/Estrelles_work`,
`ESTRELLES_OUT=…/_prova_skill/Estrelles`):

- entrades: `catalog_sony.txt` i `catalog_vixen_fonts.csv` copiats del rescat a
  `WORK/sony` i `WORK/vixen` (byte-idèntics als originals);
- `cat → cat2 → solve → refine3 → final_solve`: `cat2_*.csv`, `suns2.json`,
  `coarse.json`, `final_solution.json` i `final_match_*.csv` **idèntics** al rescat
  (diferència numèrica 0,0). Números: 38/38 (Sony) i 22/24 (R6) identificades;
  escala 3,20199 / 2,14948 ″/px (radial) i 3,1923 / 2,1478 (lineal); PA nord
  90,2706° / 57,195°, est 358,65° / 325,59°; rms 0,713 / 0,424 px; mediana
  del residu 0,545 / 0,323 px; centre del Sol (3894,0, 2768,7) / (3571,0, 2267,0);
- fotometria: primer amb `phot_*.npz` i `wings_*.npz` copiats del rescat
  (`cog2 → zp → zp2 → bemporad → identificacions → corona2 → wings2 → orient → summary`),
  i després, quan les subàrees sony i vixen ja havien deixat al WORK els seus
  intermedis regenerats (`offsets6.pkl`, masterdarks, `bkg_*`, `res_/msk_*`,
  `shifts_start.json`), **`phot2.py` i `wings.py` de veritat**: `phot_*.npz`,
  `wings_*.npz`, `zp2.json` i `zp2_*.csv` **idèntics** al rescat.

**Prova B — WORK d'intermedis originals** (`ESTRELLES_WORK=…/_prova_skill/Estrelles_work_xmatch_fotometria`,
amb `sony/` i `vixen/` enllaçats als npy/pkl del scratchpad ea55df18 que
encara existeix): la cadena de fotometria sencera, `phot2 → … → summary`, en 35 s.
Tots els productes idèntics als del rescat: `phot_*.npz`, `cogf_*.npz`
(plateau 0,96275 / 0,99196), `zp_*.csv`, `zp2.json` (ZP☉ 14,167 ± 0,065 /
14,205 ± 0,040; k 0,4158 ± 0,0496 / 0,7234 ± 0,0370; c −0,076 / +0,149),
`bemp_*.csv` (mediana Bemporad 0,162 / 0,199), `IDENTIFICACIONS_*.csv`,
`corona2.csv` (columnes antigues idèntiques), `wings.json`, `radi_*.csv`;
`orient` 71,97° contra 71,5° (0,47°); `summary` focal 290,5 mm.

Els registres són a `_prova_skill/xmatch_fotometria.log`,
`xmatch_prova_oficial.log` i `xmatch_prova_oficial_phot2.log`.

## 7. Trampes i pendents

- `refine.py` no és de la cadena: només biblioteca. No confondre `final_solve.py`
  amb `final.py` de l'arrel, sony_stars/ o vixen/. `corona2.py` d'aquí és el de
  calibratge, no el de deflexio_apod (pressupost 2027).
- `solve.py` porta l'escala de referència vella `SCALE = {'sony': 3.234, 'r6': 2.158}`
  només com a llavor de la cerca grollera; el resultat no en depèn (deixada tal qual).
- `wings2.py` porta escrites les escales no radials 3,1923/2,1478 (deixades tal qual: no
  intervenen en cap número).
- `summary.py` duu la taula `PRED` de la predicció (radis previstos en px) incrustada.
- El sostre 15600/15800, el pedestal 512,0/511,5, `RSUN_AS = 947,07`, `RMAX 20`,
  anell 26–40, obertures 6/7 i les llistes de fotogrames són als scripts, com al
  rescat; `comu.py` en porta la còpia documental.
- Avisos `RuntimeWarning: invalid value encountered in divide` a `cog2.py`/`zp.py`
  (estrella sense cap fotograma vàlid): ja hi eren al rescat, no afecten res.
- No hi ha `test_acceptacio.py` en aquesta subàrea; els números de referència són
  a `comu.ACCEPTACIO`.
