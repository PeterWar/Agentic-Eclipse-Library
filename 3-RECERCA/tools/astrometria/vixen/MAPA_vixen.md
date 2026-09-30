# MAPA — subàrea `vixen` (detecció cega d'estrelles, R6 III + VSD90SS)

Promoció del 17-08-2026 dels scripts canònics del rescat
`research/tools/rescat_scratchpad_2026-08-17/estrelles_placa_flats_16-08/vixen/`
a `research/tools/astrometria/vixen/`, sense canviar-ne cap resultat.
Producte final: **`catalog_vixen_fonts.csv`** (32 files: 21 classe A + 3 classe B
= les 24 fonts publicades a research/75 §5; 8 rebutjades), que
`../xmatch/solve.py` llegeix des de `comu.work("vixen")`.

## 1. Fitxer promogut → fitxer d'origen

| Promogut (`astrometria/vixen/`) | Origen (rescat `…/vixen/`) | Què canvia |
|---|---|---|
| `lib.py` | `lib.py` (versió 14:09, la d'estrelles) | `DIR` ← `comu.DADES_VIXEN_UNF` (abans `'/Users/USUARI/Desktop/Eclipse 2026/Vixen Unfiltered/'`). Res més. |
| `mkdark.py` | `mkdark.py` | `D` ← `comu.DARKS_R6`; `'exiftool'` ← `shutil.which('exiftool')` (surt amb missatge si no hi és); sortides al cwd = `comu.work("vixen")`. |
| `center2.py` | `center2.py` | `DIR` ← `comu.DADES_VIXEN_UNF`; `exiftool` per `shutil.which`; `center_fit.json` al WORK. |
| `proc.py` | `proc.py` | Només bloc `comu` + `os.chdir(comu.work("vixen"))`. |
| `reg.py` | `reg.py` | Ídem. Llavors, prior V, temps EXIF i escala 2,158 intactes. |
| `stack.py` | `stack.py` | Ídem. |
| `stack2.py` | `stack2.py` (versió 14:14, mitges piles A/B; **no** l'antic de l'ESF, perdut) | Ídem. |
| `stack3.py` | `stack3.py` | Ídem. |
| `detect.py` | `detect.py` | Ídem. |
| `final2.py` | `final2.py` | Ídem. |
| `rb.py` | `rb.py` | Ídem (els CR3 i el master surten de `lib.DIR` i del WORK). |
| `cat_final.py` | `cat_final.py` | Ídem. Escriu `catalog_vixen_fonts.csv` al WORK. |
| `fitpsf.py` | `fitpsf.py` | Ídem (només imprimeix; avui dona 0,677 ± 0,051 ″/s, vegeu §4). |
| `fit2.py` | `fit2.py` | Ídem (només imprimeix). |

Cada script comença amb el contracte:

```python
import sys, os; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu
os.chdir(comu.work("vixen"))
```

`lib.py` no fa `chdir` (és mòdul); els seus fitxers de fosc es resolen al cwd,
que tots els consumidors ja han posat al WORK. `import lib` continua funcionant
des de qualsevol cwd perquè Python posa el directori de l'script a `sys.path`.

`diff` contra els originals: les úniques línies que difereixen són les de
rutes de dalt (comprovat el 17-08 amb `diff` fitxer a fitxer). `grep -rn
"/private/tmp\|/Users/USUARI" *.py` al subdirectori dona zero (aquest MAPA cita
l'origen com a text, i prou).

## 2. Ordre d'execució exacte

Cwd indiferent (cada script es col·loca sol a `comu.work("vixen")`). Amb
`$PY` = l'intèrpret que dona `.claude/skills/postprocessat-corona/scripts/comprova_entorn.py --python`
(avui `~/.venvs/eines-ia-py312/bin/python`; cal rawpy, scipy, photutils) i
`exiftool` al PATH:

```
$PY vixen/mkdark.py       # dark_med_10/2/1.npy (mediana de 25/21/15 CR3)
$PY vixen/center2.py      # center_fit.json (16 CR3 curts)
$PY vixen/proc.py         # snr/res/sig/msk/cat_<8 fotogrames>.npy + ndet.json (~4,5 GB)
$PY vixen/reg.py          # shifts_start.json, shifts_end.json (imprimeix 0,610 ″/s)
$PY vixen/stack.py        # stack_flux/sig/snr.npy
$PY vixen/stack2.py       # halfA_snr.npy, halfB_snr.npy
$PY vixen/stack3.py       # g_long_*, g_short_*.npy
$PY vixen/detect.py       # cand.npy (32), moons.npy
$PY vixen/final2.py       # final.json
$PY vixen/rb.py           # rb.npy (3 CR3 de 10,3 s)
$PY vixen/cat_final.py    # catalog_vixen_fonts.csv  ← producte
$PY vixen/fitpsf.py       # (stdout) traça amb angle lliure (imprès 0,677 ± 0,051 ″/s)
$PY vixen/fit2.py         # (stdout) traça amb angle fix −45,05°
```

## 3. Entrades i sortides

Entrades (només lectura), totes via `comu`:
- `comu.DADES_VIXEN_UNF`: 572A2978 (1 s), 2979–2981 (2 s), 2982–2984 (10,3 s), 2996 (1 s) — cerca; 572A2969–2972, 2987–2990, 2999–3002, 3005–3008 — `center2`; 572A2982/83/84 — `rb`.
- `comu.DARKS_R6`: 769 CR3, dels quals `mkdark` fa servir els d'ExposureTime EXIF exactament `10` (25), `2` (21) i `1` (15).
- `exiftool` (PATH).

Sortides, totes a `comu.work("vixen")` (`$ESTRELLES_WORK/vixen/`): els .npy i
.json de la taula de dalt (≈5,5 GB) i `catalog_vixen_fonts.csv`.

Consumidors fora de la subàrea: `xmatch/solve.py` (CSV), `xmatch/phot2.py`
(`res_`/`msk_` + `shifts_start.json`), `xmatch/wings.py` (`shifts_start.json`,
`dark_med_*.npy` + CR3).

## 4. Prova del 17-08-2026 (mode prova, cadena sencera regenerada)

Variables: `ESTRELLES_WORK="…/_prova_skill/Estrelles_work"`,
`ESTRELLES_OUT="…/_prova_skill/Estrelles"`, `APOD_OUT="…/_prova_skill/APOD"`
(sota `~/Desktop/Eclipse 2026/_prova_skill/`). Cap producte del rescat com a
entrada: **tot** s'ha regenerat des dels CR3 i els darks, `mkdark` inclòs.
Registre: `$ESTRELLES_WORK/vixen_prova.log`.

Cost mesurat (Mac de 68 GB, `/usr/bin/time`): **2 min 57 s en total**
(19:31:31 → 19:34:28) i **4,8 GB** de WORK.

| Script | real (s) | Sortida i comprovació |
|---|---:|---|
| mkdark | 69,7 | n=25/21/15 CR3; `dark_med_{10,2,1}.npy` **bit-idèntics** als del scratchpad ea55df18 |
| center2 | 11,9 | `center_fit.json` idèntic al del rescat (T0 73733,44; px [−0,0725, 3578,95]; py [−0,3328, 2274,49]); |v| 0,3406 px/s = 0,735 ″/s; radi mitjà 450,70 px |
| proc | 51,6 | 8 fotogrames a ~6,3 s; `ndet.json` idèntic (31.289 / 24.511 / 24.646 / 24.742 / 14.080 / 14.121 / 14.556 / 32.537); snr/res/sig/msk/cat de tots vuit **bit-idèntics** |
| reg | 0,2 | `shifts_start.json` i `shifts_end.json` idèntics; imprès **0,610 ″/s** (start: vx 0,1999 vy −0,2002; rms 0,169/0,290 px) i 0,620 (end) |
| stack | 9,0 | `stack_flux/sig/snr.npy` bit-idèntics |
| stack2 | 9,0 | `halfA/halfB_snr.npy` bit-idèntics |
| stack3 | 18,9 | `g_long_*`, `g_short_*` bit-idèntics |
| detect | 2,8 | 443 candidates brutes → **32** després de franja lunar, mitges piles i dedup; `cand.npy`, `moons.npy` bit-idèntics |
| final2 | 0,3 | `final.json` idèntic (text) |
| rb | 1,8 | `rb.npy` bit-idèntic |
| cat_final | 0,5 | **`catalog_vixen_fonts.csv` idèntic byte a byte al del rescat** (sha256 834666c5a9b82211…); «classe A (confirmades): 21  classe B (probables): 3  rebutjades: 8» = les 24 publicades; traç de l'id 0 = 6,17″ (→ 0,599 ″/s) |
| fitpsf | 0,4 | imprès: bright n=8, L = 3,23 ± 0,24 px = 6,98 ± 0,52″ → **0,677 ± 0,051 ″/s**; PA −62,5 ± 2,6°; FWHM pila curta 3,10 px = 6,70″ |
| fit2 | 0,4 | imprès: bright n=8, L = 2,60 ± 0,11 px = 5,62 ± 0,24″ → **0,545 ± 0,023 ″/s** |

Comparació feta amb un script de contrast (`compara_vixen.py` al scratchpad de
la sessió) que carrega cada .npy regenerat i el del scratchpad original
ea55df18 (que el 17-08 encara existeix): `np.array_equal` a tots, zero píxels
diferents a les màscares.

⚠️ **No reproduït**: el **0,625 ± 0,042 ″/s** i «traç real 6,4″ = 3,0 px» de
research/75 §5.4, que mapes.md atribueix a `fitpsf.py`/`fit2.py`. Amb entrades
bit-idèntiques a les del 16-08, `fitpsf.py` (angle lliure) dona 0,677 ± 0,051
i `fit2.py` (angle fix −45,05°) 0,545 ± 0,023; `moments.py` del rescat (no
promogut) dona 0,681. La mitjana dels dos ajustos seria 0,611; l'única fila
que dona exactament 3,00 px / 6,47″ / 0,628 és l'id 2 de `fit2.py`. Els
scripts conservats són, per tant, els que van produir el catàleg, però no el
número de la traça publicat: potser una versió intermèdia de `fitpsf.py` o una
selecció diferent de fonts. Queda com a deute de traçabilitat de research/75
§5.4; **el 0,610 ± 0,010 de `reg.py` sí que surt** (0,610 exacte; el ±0,010
no l'imprimeix cap script).

Advisos vistos en córrer (inofensius, iguals que el 16-08): `RuntimeWarning:
All-NaN slice` a `lib.bg_and_sigma` (blocs sencers de màscara, que després
s'omplen pel veí més proper) i les `AstropyDeprecationWarning` de photutils
3.0.0 a `proc.py`.

## 5. Coses a saber (heretades del rescat, no tocades)

- `proc.py` fa servir l'API antiga de photutils (`roundlo/roundhi`,
  `sharplo/sharphi`, `tb['xcentroid']`). Amb photutils **3.0.0** funciona amb
  `AstropyDeprecationWarning`; es retira a la 4.0. Si peta, els equivalents
  són `roundness_range=(-1.5,1.5)`, `sharpness_range=(0.05,2.0)` i
  `x_centroid`/`y_centroid`, amb els mateixos valors (`detect.py` ja els usa).
- `mkdark.py` fa **mediana** per píxel (research/75 §1 diu que la mitjana és
  0,132 ADU més alta i que per als 10,3 s caldria el subconjunt de 41 °C); no
  s'ha canviat perquè el catàleg publicat surt d'aquests masters.
- Escala 2,158 ″/px i radi lunar 451 px a tota la subàrea (pre-placa); la
  placa publicada és 2,1495 i 460,0. `r_sol_*` del CSV és distància al centre
  **lunar** del fotograma 572A2982. `V_aprox_INFERIT` (ZP 9,57e5 ADU/s) no és
  el ZP publicat +14,21.
- `reg.py` duu 8 llavors i el prior de velocitat a pèl; `shifts_start.json`
  assumeix DateTimeOriginal = inici d'exposició.
- El CSV es queda al WORK (no es copia a `ESTRELLES_OUT`): és entrada de
  `xmatch`, no producte d'operador; `estrelles_r6.csv` de l'Escriptori es va
  escriure a mà a partir d'aquest CSV + IDENTIFICACIONS de xmatch.
- Descartats i no promoguts (vegeu mapes.md, àrea Vixen): la via A/B de
  resolució i protuberàncies (importen un `lib.py`/`stack2.py` sobreescrits),
  explora*, scan, geom, test1, shift, center, final, moments, wings*, moonrate.
