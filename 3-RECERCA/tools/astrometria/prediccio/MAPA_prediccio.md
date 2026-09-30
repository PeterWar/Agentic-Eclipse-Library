# MAPA — subàrea `prediccio` (predicció cega del camp d'estrelles)

Promoció del 17-08-2026 dels scripts de predicció de la sessió ea55df18 del
16-08-2026. Cap algorisme, llindar ni constant no s'ha tocat: els tres CSV
que surten són **byte a byte idèntics** als del rescat.

Què és i què no és: aquesta cadena és el **registre de la cerca cega**
(quines estrelles Hipparcos/Tycho-2 hi ha a 4° del Sol, quines cauen dins de
cada sensor i quin SNR es preveia). **No alimenta el creuament ni la placa**:
cap script de `xmatch/` llegeix `hip_4deg.csv`, `candidates_v8.csv`,
`taula_final.csv` ni `tyc2.tsv` (el creuament fa servir `tyc2_deep.tsv` i
`hip_main.dat` directament). Cap número de placa (3,2020/2,1495) ni de
calibratge (ZP, B/B☉) surt d'aquí; surten de `xmatch/`.

## Fitxer promogut → origen al rescat

Rescat: `research/tools/rescat_scratchpad_2026-08-17/estrelles_placa_flats_16-08/`

| Promogut (`research/tools/astrometria/prediccio/`) | Origen | Canvi |
|---|---|---|
| `sol_planetes.py` | `sol_planetes.py` | `load('/Users/…/de440s.bsp')` → `comu.efemeride()`; capçalera i `import comu` |
| `estrelles.py` | `estrelles.py` | efemèride → `comu.efemeride()`; `open('hip_main.dat')` → `open(comu.HIP_MAIN)`; `os.chdir(comu.work("prediccio"))` perquè `hip_4deg.csv` vagi al WORK; imprimeix la ruta del fitxer |
| `combina.py` | `combina.py` | `open('hip_main.dat')` → `open(comu.HIP_MAIN)`; `open('tyc2.tsv')` → `open(comu.TYC2)`; `os.chdir(comu.work("prediccio"))` (llegeix `hip_4deg.csv`, escriu `candidates_v8.csv`) |
| `final.py` | `final.py` | efemèride → `comu.efemeride()`; `open('hip_main.dat')` → `open(comu.HIP_MAIN)`; `os.chdir(comu.work("prediccio"))` (llegeix `candidates_v8.csv`, escriu `taula_final.csv`) |
| `baixa_catalegs.sh` | **NOU** (URL de les capçaleres de `tyc2.tsv` i `xmatch/tyc2_deep.tsv`, i la del CDS que apunta el mapa) | comprova `hip_main.dat`, `tyc2.tsv`, `tyc2_deep.tsv` a `comu.CATALEGS` i baixa amb `curl` el que falti; si hi són, no fa res |
| — | `tyc2.tsv` (dada) | no es copia: ja és a `comu.TYC2` (`~/Desktop/Eclipse 2026/Estrelles/catalegs/tyc2.tsv`, mateix MD5 `fdf9462f…` que el rescat) |
| — | `pressupost.py` | **no promogut** (pressupost de paper previ, mateix model que `final.py` amb la llista escrita a mà; queda al rescat com a evidència) |

Trampa de noms: aquest `final.py` (taula SNR de predicció) **no** és
`sony_stars/final.py`, ni `vixen/final.py`, ni `xmatch/final_solve.py`; i
`combina.py` (fusió de catàlegs) no és `combine.py` (PTC).

## Ordre d'execució exacte

Relatiu a `research/tools/astrometria/`, amb `$PY` l'intèrpret que dona
`.claude/skills/postprocessat-corona/scripts/comprova_entorn.py --python`.
Cap script depèn del cwd (fan `os.chdir(comu.work("prediccio"))`).

```
prediccio/baixa_catalegs.sh
$PY prediccio/sol_planetes.py
$PY prediccio/estrelles.py
$PY prediccio/combina.py
$PY prediccio/final.py
```

## Entrades i sortides

| | Ruta (per `comu.py`) | Nota |
|---|---|---|
| Efemèride | `comu.EFEMERIDE` = `~/.cache/skyfield/de440s.bsp` | 32,7 MB, existeix |
| Hipparcos | `comu.HIP_MAIN` = `$CATALEGS/hip_main.dat` | CDS I/239, 53.316.318 B (existeix a `~/Desktop/Eclipse 2026/Estrelles/catalegs/`) |
| Tycho-2 (predicció) | `comu.TYC2` = `$CATALEGS/tyc2.tsv` | VizieR I/259, 4,2°, VT<9, 100 files |
| Tycho-2 (creuament) | `comu.TYC2_DEEP` = `$CATALEGS/tyc2_deep.tsv` | només el comprova `baixa_catalegs.sh`; el fa servir `xmatch/` |
| Sortida 1 | `comu.work("prediccio")/hip_4deg.csv` | 112 estrelles Hipparcos dins 4,0°, totes les magnituds |
| Sortida 2 | `comu.work("prediccio")/candidates_v8.csv` | 42 estrelles V≤8 amb SEGUR/POSSIBLE/FORA per tren (escales ANTIGUES 3,234/2,158) |
| Sortida 3 | `comu.work("prediccio")/taula_final.csv` | 42 files amb PA_deg, snr_sony/r6 a cel 11/12/14 i exposicions usades |
| stdout | `sol_planetes.py` | Sol a 9,07° geomètric / 9,16° refractat, X 6,055, R☉ 947,07″, planetes |

## Cost mesurat

Sencera: **< 2 s de rellotge** (sol_planetes ≈0,1 s, estrelles ≈0,5 s,
combina ≈0,4 s, final ≈0,4 s) amb `~/.venvs/eines-ia-py312` (skyfield 1.55,
pandas 3.0.5, numpy 2.5.1). `baixa_catalegs.sh` amb els catàlegs presents:
0,4 s. Si cal baixar `hip_main.dat`: 53 MB del CDS.

## Què s'ha provat i resultat

Executat des de `cwd=$HOME` (no des del directori de l'script) amb
`ESTRELLES_WORK="~/Desktop/Eclipse 2026/_prova_skill/Estrelles_work"`,
`ESTRELLES_OUT=…/_prova_skill/Estrelles`, `APOD_OUT=…/_prova_skill/APOD` i
`CATALEGS` per defecte (`~/Desktop/Eclipse 2026/Estrelles/catalegs`, només lectura):

- `py_compile` dels quatre `.py`: bé; `zsh -n baixa_catalegs.sh`: bé.
- `grep -rn "/private/tmp\|/Users/USUARI" prediccio/`: **zero**.
- `baixa_catalegs.sh`: detecta `comu.CATALEGS` via `comprova_entorn.py`, troba
  els tres catàlegs i l'efemèride i no baixa res. Amb `CATALEGS` apuntant a un
  directori buit i `--nomes-mostra`, imprimeix les tres URL i no toca res
  (la baixada real no s'ha exercit: els fitxers hi són).
- `sol_planetes.py`: RA 142,10549 / Dec +14,90721 (J2000), alt geomètrica
  9,0721°, refractada 9,1588°, X 6,055, R☉ 947,07″ — coincideix amb la síntesi
  (9,07°, X≈6,1, 947,07″).
- `estrelles.py` → `hip_4deg.csv`: 112 estrelles, **`cmp` idèntic** al del
  rescat (i al de `Estrelles/catalegs/hip_4deg.csv`).
- `combina.py` → `candidates_v8.csv`: 42 estrelles, **`cmp` idèntic**; les
  quatre «segures» HIP 46232, 47096, 45874, 46713 hi són SEGUR a la Sony.
- `final.py` → `taula_final.csv`: 42 files, **`cmp` idèntic**.
- Cap fitxer de skyfield no ha caigut al cwd (l'efemèride surt de la cau).

## Què s'ha canviat, línia a línia

Cap constant numèrica. Als quatre scripts s'hi afegeix la capçalera del
contracte (`sys.path.insert(0, parents[1]); import comu`) i:

- `sol_planetes.py` l.6: `eph = load('/Users/USUARI/.cache/skyfield/de440s.bsp')` → `eph = comu.efemeride()`.
- `estrelles.py` l.6 igual; l.12 `open('hip_main.dat')` → `open(comu.HIP_MAIN)`; afegit `os.chdir(comu.work("prediccio"))` i un `print` final de la ruta.
- `combina.py` l.6 `open('hip_main.dat')` → `open(comu.HIP_MAIN)`; l.16 `open('tyc2.tsv')` → `open(comu.TYC2)`; afegit `os.chdir(comu.work("prediccio"))` i un `print` final.
- `final.py` l.5 `load('/Users/…/de440s.bsp')` → `comu.efemeride()`; l.9 `open('hip_main.dat')` → `open(comu.HIP_MAIN)`; afegit `os.chdir(comu.work("prediccio"))`; l'últim `print` diu la ruta sencera.

Els literals de lloc (42,299407 / −5,02503 / 798 m), instant (18:29:38 UTC),
centre de cerca (142,10549 / +14,90721), radis (6°, 4°), R☉ 947,07″, escales
antigues 3,234/2,158, sensors 7952×5304 i 6960×4640, i el model de pressupost
(F0 8,97e5, ETA_PX 0,27, ETA_STAR 0,135, A_EXT 0,37·6,2, taula K+F) es
conserven escrits al codi tal com eren; `comu.py` porta els mateixos valors
(LLOC, T_PREDICCIO_UTC, CENTRE_CERCA_J2000, RADI_CERCA_DEG, R_SOL_ARCSEC,
escala_vella) com a referència, però no s'ha canviat el codi perquè els
llegís d'allà: era el canvi mínim i el resultat és idèntic.

## Pendent

- La baixada real de `baixa_catalegs.sh` no s'ha exercit (els tres fitxers hi
  són); s'ha verificat només amb `curl -I` que la URL del CDS de `hip_main.dat`
  respon 200 amb 53.316.318 B (la mateixa mida que el fitxer local) i que
  `hip_main.dat.gz` dona 404. Una consulta nova a VizieR donaria un TSV amb la
  capçalera de data diferent (mateixes files).
- Escales antigues (3,234/2,158) i criteri purament radial de SEGUR/POSSIBLE:
  és el que era; amb el nord real a PA 90,27° les «possible» brillants van
  quedar fora. No es corregeix perquè és registre de predicció, no producte.
