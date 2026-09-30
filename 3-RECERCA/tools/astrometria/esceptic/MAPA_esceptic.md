# MAPA_esceptic — auditoria escèptica de la placa i la fotometria d'estrelles

Subàrea `esceptic/` de `research/tools/astrometria/`. Promoguda el 17-08-2026 des del rescat
`research/tools/rescat_scratchpad_2026-08-17/estrelles_placa_flats_16-08/skeptic2/` (sessió ea55df18 del
16-08-2026, 15:16–15:23). És l'escèptic dels números publicats a `research/75 §5` (SNR reals, terme de color al Sol,
k contra k, diferència entre trens, unicitat del creuament, dobles, saturació, soroll de la fotometria).

**Cap algorisme, llindar, llavor ni constant s'ha tocat.** Només rutes (tot per `comu.py`) i la capçalera.
`inject.py` (primera versió amb el factor 2 mal posat) i `noise.npy` runtime **no** es promouen com a codi;
`noise.npy` es promou com a **dada rescatada** (`noise_rescat_16-08.npy`) per poder córrer `zprefit.py` i
`chain.py` encara que `inject2.py` no s'hagi executat (avui costa 6 s, no els ~10 min que deia el mapa).

## Fitxer promogut → fitxer d'origen

| Promogut (`esceptic/`) | Origen (`skeptic2/`) | Què fa | Cost mesurat |
|---|---|---|---|
| `inject2.py` | `inject2.py` | soroll real de la fotometria combinada dels 7 ARW + injecció d'estrelles sintètiques (F=400/1200 ADU/s) per banda de R/R☉; **escriu `noise.npy`** | **6,1 s** mesurats (els «~10 min» del mapa eren de la sessió del 16-08 sencera, no d'aquest script) |
| `zprefit.py` | `zprefit.py` | reajust del ZP Sony amb errors reals (mínims quadrats ponderats), SNR real per estrella, quatre subconjunts, error extra per χ²=1 | 0,2 s |
| `chain.py` | `chain.py` | (A) terme de color no aplicat al Sol → factors i quocient R6/Sony 0,83→0,95; (B) curvatura de Bouguer; (C) k Sony contra k R6 | 0,3 s |
| `cross.py` | `cross.py` | D = m_inst,Sony − m_inst,R6 a les estrelles comunes; D~const, +aX, +bBV | 0,2 s |
| `cross2.py` | `cross2.py` | el mateix D per bandes de R/R☉ (dins/fora de 6 R☉) i snr_sony>15 | 0,2 s |
| `unic.py` | `unic.py` | unicitat i taxa d'atzar del creuament: 400 desplaçaments+rotacions aleatoris (NUL) | 0,3 s |
| `amb.py` | `amb.py` | deteccions amb més d'una candidata dins 20 px (dobles) | 0,3 s |
| `sat.py` | `sat.py` | pic verd i pic qualsevol de cada estrella identificada a DSC06993/DSC06987 contra white_level | 0,4 s |
| `noise_rescat_16-08.npy` | `noise.npy` (dada) | els 5 sorolls per banda del 16-08: `[1780.23, 161.58, 86.69, 78.83, 53.11]` ADU/s | — |
| — | `inject.py` | NO promogut (versió amb el factor 2 mal posat; superada per inject2.py) | — |

## Rutes: què hi havia i on va ara

| Abans (scratchpad ea55df18, volàtil) | Ara |
|---|---|
| `sys.path.insert(0,'…/scratchpad/xmatch')` (inject2, unic) | `sys.path.insert(0, parents[1]/'xmatch')` → importa `phot2.phot_stamp`, `phot2.SONY_EXP` del **xmatch promogut** (només inject2; unic no en feia servir res i s'ha tret) |
| `XD` / `X` = `…/scratchpad/xmatch/` | `comu.work('xmatch')` |
| `SD` = `…/scratchpad/sony_stars/` | `comu.work('sony')` |
| `D` = `/Users/USUARI/Desktop/Eclipse 2026/300mm/` | `comu.DADES_300MM` |
| `np.load('…/scratchpad/skeptic2/noise.npy')` (zprefit, chain) | `_noise()`: `comu.work('esceptic')/noise.npy` si existeix (fresc, d'inject2.py); si no, `esceptic/noise_rescat_16-08.npy` amb un `[avis]` a stdout |
| `np.save('…/scratchpad/skeptic2/noise.npy', …)` (inject2) | `comu.work('esceptic')/noise.npy` |

`grep -rn "/private/tmp\|/Users/USUARI" esceptic/*.py` → zero.

## Entrades

- `comu.work('xmatch')/`: `zp2.json`, `final_solution.json` (`sony_radial`, `r6_radial`), `zp_sony.csv`, `zp_r6.csv`,
  `IDENTIFICACIONS_sony.csv`, `final_match_sony.csv`, `final_match_r6.csv`, `cat2_sony.csv`, `cat2_r6.csv`, `cogf_sony.npz`.
  Els fan `xmatch/{cat2,solve,refine3,final_solve,identificacions,phot2,cog2,zp,zp2}.py`.
- `comu.work('sony')/`: `offsets6.pkl` (sony/scan.py), `masterdark_{1,2,8}s.npy` (sony/darks.py),
  `bkg_DSC0698{4,5,7}.npy, bkg_DSC069{91,93,96,99}.npy` (sony/runall.py i sony/mf3.py: fons idèntic,
  Background2D (32,32)/(3,3)/σ3/30 %; l'últim que els escriu és mf3.py).
- `comu.DADES_300MM/`: DSC06984/85/87/91/93/96/99.ARW (inject2), DSC06993/06987.ARW (sat).
- `research/tools/astrometria/xmatch/phot2.py` (import; en importar-lo fa `os.chdir(comu.work('xmatch'))`, innocu
  perquè inject2 només fa servir rutes absolutes de comu).

## Sortides

- `comu.work('esceptic')/noise.npy` (inject2.py). Tota la resta és stdout.

## Ordre d'execució (per a `pipeline_estrelles.sh`, cwd indiferent, `$PY` = intèrpret detectat)

```
$PY esceptic/inject2.py      # 6 s; escriu WORK/esceptic/noise.npy (si faltés, zprefit/chain cauen a noise_rescat_16-08.npy amb avís)
$PY esceptic/zprefit.py
$PY esceptic/chain.py
$PY esceptic/cross.py
$PY esceptic/cross2.py
$PY esceptic/unic.py
$PY esceptic/amb.py
$PY esceptic/sat.py
```

Els sis últims són independents entre ells; zprefit i chain llegeixen noise.npy.

## Llavors

- `inject2.py`: `np.random.default_rng(11)` (original; intacta).
- `unic.py`: **l'original ja portava `np.random.default_rng(7)`** (el mapa deia «no consta»; consta al codi). Es conserva.
  Amb aquesta llavor: esperats <2 px per atzar **0,01/0,02 (Sony, V≤11/12,5) i 0,00/0,00 (R6)** → els «0,02 / 0,00» publicats.

## Provat el 17-08-2026 (entorn `~/.venvs/eines-ia-py312/bin/python`, `PYTHONDONTWRITEBYTECODE=1`)

Variables: `ESTRELLES_WORK=~/Desktop/Eclipse 2026/_prova_skill/Estrelles_work`,
`ESTRELLES_OUT=…/_prova_skill/Estrelles`, `APOD_OUT=…/_prova_skill/APOD`.

Entrades del WORK de prova: **copiades del rescat** (`xmatch/`: zp2.json, final_solution.json, zp_sony.csv, zp_r6.csv,
IDENTIFICACIONS_sony.csv, final_match_{sony,r6}.csv, cat2_{sony,r6}.csv, cogf_sony.npz) i **`offsets6.pkl` copiat del
scratchpad ea55df18** (encara viu; 519 B) a `WORK/sony/`. `masterdark_*.npy` i `bkg_*.npy` a `WORK/sony/` els estava
regenerant en paral·lel la subàrea `sony` (darks.py, runall.py) mentre es feia aquesta prova; no els he copiat jo.

| Script | Resultat obtingut | Publicat (research/75 §5) |
|---|---|---|
| `py_compile` dels 8 | OK | — |
| `chain.py` | Sony c −0,076 → error −4,5 %; R6 c +0,149 → +9,4 %; **quocient 0,83 × (1,0936/0,9553) = 0,950**; k −0,308±0,062 = **5,0 σ**; Bouguer q = −0,0105±0,0924 | 0,83 → 0,95; 5,0σ |
| `zprefit.py` | **S21 (HIP 46335) snr_real 0,1 (flux/soroll = 0,07 abans d'arrodonir), S05 (HIP 46345) 6,6**; totes n=38 ZP +14,167±0,064 k +0,418±0,055 χ²red 1,38 | 0,07 / 6,6; ZP +14,09…+14,22 |
| `cross.py` | 15 comunes; D mediana −0,084, desv 0,627; pendent amb X +0,217±0,285 (predicció −0,308) | — |
| `cross2.py` | R<6 R☉ (n=6) \|D\| med **0,679**, desv 0,964; R≥6 (n=9) \|D\| med **0,249**, desv **0,322**; snr>15 i R>6 desv 0,187 | 0,32 fora / 0,96 dins |
| `unic.py` | Sony: 38/38 a <2 px, NUL <2 px = **0,01 (V≤11) / 0,02 (V≤12,5)**; R6: 22/22, NUL **0,00 / 0,00** | 0,02 / 0,00 |
| `amb.py` | S30 → TYC 1403-1015-2 i 1403-1015-1, V=8,90 tots dos, 0,16 i 0,33 px, mateix HIP | doble no resolta HIP 45824 |
| `sat.py` | DSC06993 pic verd màxim **15.161** (S21) contra white_level **16.383**; DSC06987 14.176 | 15.161 / 16.383 |
| `inject2.py` | soroll 1σ per banda **1780,2 / 161,6 / 86,7 / 78,8 / 53,1 ADU/s**; F_rec/F_inj 0,984…0,953 (2,6–14 R☉, F=400 i 1200) i 2,975/1,283 a 1,6–2,6; **`noise.npy` fresc bit a bit idèntic a `noise_rescat_16-08.npy`** (`np.array_equal` True), amb masterdarks i bkg regenerats per la subàrea sony i offsets6.pkl del scratchpad | 1.780/162/87/79/53; insesgat 3–4 %; 1,3–3,0× |

## Què he canviat, línia a línia

- Tots: capçalera `#!/usr/bin/env python3` + docstring d'origen + les quatre línies del contracte `comu`.
- `inject2.py`: `sys.path.insert` → `parents[1]/'xmatch'`; `SD`, `D`, `XD` → comu; `rawpy.imread(D+name+'.ARW')` →
  `rawpy.imread(str(D/(name+'.ARW')))`; `np.save('…/skeptic2/noise.npy')` → `np.save(OUTD/'noise.npy')` + un `print('desat …')`.
- `zprefit.py`, `chain.py`: `NO=np.load('…/noise.npy')` → `NO=_noise()` (helper de 6 línies definit al mateix fitxer).
- `unic.py`: es treu el `sys.path.insert` al scratchpad (no importava res d'allà).
- `sat.py`: `D`, `final_match_sony.csv`, `offsets6.pkl` per comu.
- **Cap constant numèrica canviada** (RSUN 947,07, sig 3,74/2,3548, BANDS, NP 90, F_inj 400/1200, sostre 15600 dilatació 6,
  CAT 0,10, X☉ 6,077645211221788, BV_SOL 0,653, SH 7968×5320/6960×4640, 400 iteracions, ±1500 px, llavors 11 i 7).

## Pendent / límits

- `zprefit.py`/`chain.py` s'han executat dues vegades: amb `noise_rescat_16-08.npy` (abans d'inject2) i amb el
  `noise.npy` fresc; sortida idèntica (0,1/6,6; 0,950; 5,0σ).
- `offsets6.pkl` de la prova és el del scratchpad ea55df18, no el regenerat per `sony/scan.py` (encara no havia
  arribat quan s'ha fet la prova). Quan `scan.py` l'hagi reescrit, tornar a córrer `inject2.py` i `sat.py` i
  comparar `noise.npy` amb `noise_rescat_16-08.npy` (avui: idèntic).
- Els factors corregits 1,134e-11 / 2,772e-11 no els escriu cap script d'aquesta subàrea: `chain.py` (A) només
  imprimeix els factors Fu/Fc; qui els ha d'escriure és `xmatch/corona2.py` amb el terme −0,653·c (síntesi §4).
- `research/75` diu «SNR 0,07» per a HIP 46335; el format `%9.1f` de zprefit imprimeix `0.1`; el 0,07 és
  flux_tot/soroll = 122/1780 sense arrodonir (mateix número).
