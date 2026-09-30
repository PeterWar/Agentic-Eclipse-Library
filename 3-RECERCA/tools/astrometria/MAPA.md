# MAPA — `research/tools/astrometria/` (placa d'estrelles, calibratge absolut, deflexió, APOD)

Índex de la promoció del 17-08-2026: els scripts de la sessió ea55df18 (16-08, placa i fotometria) i
604fa71e (16-08, deflexió i APOD), rescatats a `research/tools/rescat_scratchpad_2026-08-17/`, viuen ara
aquí amb el mateix nom, sense cap canvi d'algorisme, llindar, llavor ni constant (l'única correcció que canvia
un número és el terme de color de `xmatch/corona2.py`, ordenada per la síntesi §4). Totes les rutes surten de
`comu.py`; cap intèrpret ni ruta d'usuari escrit a pèl. Cada subdirectori té el seu `MAPA_<sub>.md` amb el
detall línia a línia; aquest fitxer és l'índex i el lloc de les trampes.

## 1. Què hi ha

| Ruta | Què és |
|---|---|
| `comu.py` | rutes de dades (variables d'entorn amb l'Escriptori com a defecte), `work(sub)`, `out()`, `apod()`, `efemeride()`, i les constants documentals (`SONY`, `R6`, `ACCEPTACIO`) |
| `pipeline_estrelles.sh` | orquestrador zsh calcat de `pipeline_vixen.sh`: etapes, `--nomes-mostra`, `--prova DIR`, registres a `$ESTRELLES_WORK/_registres/` |
| `test_acceptacio.py` | llegeix els productes del WORK/OUT i afirma `comu.ACCEPTACIO` amb tolerància (✓/✗/«no trobat»; surt 0/2) |
| `prediccio/` | predicció cega del camp (Sol, planetes, Hipparcos a 4°, candidates V≤8, taula SNR). **No alimenta res**: és el registre de la cerca cega |
| `sony/` | detecció cega d'estrelles a 7 ARW del 300 GM → `catalog_sony.txt` (38 fonts) |
| `vixen/` | detecció cega a 8 CR3 del VSD90SS → `catalog_vixen_fonts.csv` (32 files; 21 A + 3 B = 24 fonts) |
| `xmatch/` | creuament Tycho-2/Hipparcos, placa (lineal i radial), fotometria d'obertura, ZP, Bemporad, B/B☉, ales, orientació, resum |
| `esceptic/` | auditoria escèptica dels números publicats (soroll injectat, SNR reals, terme de color, k contra k, unicitat, dobles, saturació) |
| `deflexio/` | fusió dels CSV d'operador, previsió de Fisher de σ(ε), retalls i moviments, màscares marcades |
| `apod/` | lliurables «Stars Beside an Eclipsed Sun / Where Newton would have put it»: PNG nets, figures, animació, vídeo, HTML |
| `MAPA_*.md` (un per subdirectori) | fitxer per fitxer: origen, canvi, entrades, sortides, cost, prova, pendents |

## 2. Ordre (el de `pipeline_estrelles.sh`, per defecte tot en aquest ordre)

```
catalegs    prediccio/baixa_catalegs.sh                                          0,4 s (si els catàlegs hi són)
prediccio   sol_planetes estrelles combina final                                 < 2 s
sony        darks runall reg3 numden refine moon mf3 stack2 reg4 boot boot2 scan groups warp fitwarp imgs cat clean final2 final3
                                                                                 ~6 min 27 s · ~8,5 GB de WORK
sony_extra  build gain   (fora de la llista per defecte: F_*.npy que ningú llegeix i l'evidència del guany 3,323)   +20 s · +1,5 GB
vixen       mkdark center2 proc reg stack stack2 stack3 detect final2 rb cat_final fitpsf fit2   ~2 min 57 s · 4,8 GB
xmatch      cat cat2 solve refine3 final_solve                                   ~10 s
fotometria  phot2 cog2 zp zp2 bemporad identificacions corona2 wings wings2 orient summary   ~35 s (llegeix RAW)
esceptic    inject2 zprefit chain cross cross2 unic amb sat                      ~8 s
deflexio    fusiona_csv deflexio retall_estrella moviments                       ~5 s
mascara     mascara_estrelles sony · vixen                                       ~10 s
apod        render_net figures animacio munta_video.sh munta                     ~65 s (ffmpeg, fonts del sistema)
acceptacio  test_acceptacio.py                                                   < 1 s
```

Dependències entre etapes que no es veuen a la llista: `xmatch/solve.py` llegeix `work(sony)/catalog_sony.txt` i
`work(vixen)/catalog_vixen_fonts.csv`; `fotometria` (phot2, wings) llegeix `offsets6.pkl`, `masterdark_*.npy`,
`bkg_*.npy` de `work(sony)` i `res_/msk_*.npy`, `shifts_start.json`, `dark_med_*.npy` de `work(vixen)`;
`identificacions.py` va **després** de `bemporad.py`; `esceptic` llegeix `cogf_sony.npz`, `cat2_*.csv`,
`zp_*.csv`, `IDENTIFICACIONS_*.csv`, `final_*` de `work(xmatch)` i `offsets6.pkl`, masterdarks, `bkg_*` de
`work(sony)`; `deflexio/fusiona_csv.py` llegeix els dos catàlegs i `IDENTIFICACIONS_*`/`final_match_*`;
`mascara` ha d'anar abans d'`apod` (`render_net.py` i `munta_video.sh` llegeixen `estrelles_*_marcades.png`).
Cost total de la cadena sencera: **~11 min i ~15 GB** de WORK (dels quals 3,9 GB són `res_/valid_/num_/den_/validbits_`
de `sony/runall.py` i `numden.py`, que cap pas posterior no llegeix).

## 3. Fitxer promogut → origen (consolidat dels sis MAPA_*)

Rescat: `research/tools/rescat_scratchpad_2026-08-17/` (R). Sessions: ea55df18 = `estrelles_placa_flats_16-08/`,
604fa71e = `deflexio_apod_2027_16-08/`. «capçalera» = `#!/usr/bin/env python3` + docstring d'origen +
`sys.path.insert(0, parents[1]); import comu` (+ `os.chdir(comu.work("<sub>"))` a tots menys `vixen/lib.py`).

| Promogut | Origen | Canvi a més de la capçalera |
|---|---|---|
| `comu.py` | **NOU** | — |
| `pipeline_estrelles.sh`, `test_acceptacio.py`, `MAPA.md` | **NOU** | — |
| `prediccio/sol_planetes.py` | R/…placa…/`sol_planetes.py` | efemèride → `comu.efemeride()` |
| `prediccio/estrelles.py` | R/…placa…/`estrelles.py` | efemèride; `hip_main.dat` → `comu.HIP_MAIN`; `hip_4deg.csv` al WORK |
| `prediccio/combina.py` | R/…placa…/`combina.py` | `hip_main.dat` → `comu.HIP_MAIN`; `tyc2.tsv` → `comu.TYC2`; WORK |
| `prediccio/final.py` | R/…placa…/`final.py` | efemèride; `comu.HIP_MAIN`; WORK |
| `prediccio/baixa_catalegs.sh` | **NOU** | comprova/baixa hip_main.dat, tyc2.tsv, tyc2_deep.tsv a `comu.CATALEGS`; `--nomes-mostra` |
| `sony/{darks,runall,reg3,numden,refine,moon,mf3,stack2,reg4,boot,boot2,scan,groups,warp,fitwarp,imgs,cat,clean,final2,final3,build,gain}.py` (22) | R/…placa…/`sony_stars/<mateix nom>` | `D`/`DD` → `comu.DADES_300MM`/`comu.DARKS_SONY`; **`boot.py`**: guarda `if best is None: continue` al print (evita un TypeError amb DSC06988; cap número canvia); **`final3.py`**: còpia de `catalog_sony.txt` a `comu.out()` |
| `vixen/{lib,mkdark,center2,proc,reg,stack,stack2,stack3,detect,final2,rb,cat_final,fitpsf,fit2}.py` (14) | R/…placa…/`vixen/<mateix nom>` (`lib.py` versió 14:09, `stack2.py` versió 14:14) | `DIR`/`D` → `comu.DADES_VIXEN_UNF`/`comu.DARKS_R6`; `exiftool` per `shutil.which` (mkdark, center2) |
| `xmatch/{cat,cat2,solve,refine,refine3,final_solve,phot2,cog2,zp,zp2,bemporad,corona2,wings,wings2,orient,summary}.py` (16) | R/…placa…/`xmatch/<mateix nom>` | efemèride → `comu.efemeride()`; `tyc2_deep.tsv`/`../hip_main.dat` → `comu.TYC2_DEEP`/`comu.HIP_MAIN`; `../sony_stars/`, `../vixen/` → `comu.work(...)`; halo_params → `comu.HALO_PARAMS`; còpies a `comu.out()` de `final_solution.json`, `final_match_*.csv`, `zp2.json`, `corona2.csv`, `wings.json`; **`corona2.py`: terme de color** (`fac` amb −0,653·c, columna nova `fac_nocolor` = l'antic) |
| `xmatch/identificacions.py` | **NOU** | escriu `IDENTIFICACIONS_{sony,r6}.csv` (format dels rescatats, diferència ≤ 5e-15) |
| `esceptic/{inject2,zprefit,chain,cross,cross2,unic,amb,sat}.py` (8) | R/…placa…/`skeptic2/<mateix nom>` | `XD`/`SD`/`D` → comu; `noise.npy` a `comu.work('esceptic')`; zprefit/chain cauen a `noise_rescat_16-08.npy` si no hi ha noise.npy fresc |
| `esceptic/noise_rescat_16-08.npy` | R/…placa…/`skeptic2/noise.npy` (dada, 168 B) | còpia |
| `deflexio/deflexio.py`, `retall_estrella.py`, `moviments.py` | R/`deflexio_apod_2027_16-08/<mateix nom>` | `BASE`/`SORTIDA` → `comu.out()`/`comu.apod()`; efemèride; RAW per comu |
| `deflexio/mascara_estrelles.py` | `~/Desktop/Eclipse 2026/Estrelles/mascara_estrelles.py` (16-08 15:58) | `AQUI` → `comu.out()`; RAW per comu |
| `deflexio/fusiona_csv.py` | **NOU** (els `estrelles_*.csv` es van escriure a mà) | catàlegs + IDENTIFICACIONS (+ final_match) → `out()/estrelles_{sony,r6}.csv` |
| `apod/render_net.py`, `figures.py`, `animacio.py`, `munta.py` | R/`deflexio_apod_2027_16-08/<mateix nom>` | `SORTIDA`/`FRAMES` → `comu.apod()`/`comu.work('apod')`; `munta.py` reescrit només en rutes |
| `apod/munta_video.sh` | **NOU** (els tres passos que el 16-08 es van fer a mà: ffmpeg, poster, imgs.json) | ordres exactes de la transcripció 604fa71e |
| `apod/apod.tpl.html` | R/`apod_assets/apod.tpl.html` (font escrita a mà, 33.789 B) | còpia; **entrada**, no la genera ningú |
| `apod/figA.svg`, `figB.svg`, `poster.jpg` | R/`apod_assets/` | còpies de referència; `figures.py` i `munta_video.sh` els regeneren byte-idèntics |
| — `tyc2.tsv`, `tyc2_deep.tsv` | R/…placa…/`tyc2.tsv`, `xmatch/tyc2_deep.tsv` | **no es copien**: viuen a `comu.CATALEGS` (mateix MD5 / byte-idèntics) |
| — `pressupost.py`, `inject.py`, `solve2.py`, `refine2.py`, `phot.py`, `corona.py` (xmatch), `repeat.py`, `moments.py`, `explora*`, `scan`/`geom`/`test1`/`shift`/`center`/`final` (vixen), la cadena 3 del pla 2027 | rescat | **no promoguts** (superats, erronis o evidència); vegeu cada MAPA_* i la síntesi §5 |

## 4. Entrades externes (només lectura; totes per `comu.py`)

| Entrada | Variable / ruta per defecte | D'on surt |
|---|---|---|
| Hipparcos `hip_main.dat` (53.316.318 B) | `comu.HIP_MAIN` = `$CATALEGS/hip_main.dat` (`~/Desktop/Eclipse 2026/Estrelles/catalegs/`) | CDS I/239: `https://cdsarc.cds.unistra.fr/ftp/I/239/hip_main.dat` |
| Tycho-2 predicció `tyc2.tsv` (4,2°, VT<9, 100 files) | `comu.TYC2` | VizieR I/259: `https://vizier.cds.unistra.fr/viz-bin/asu-tsv?-source=I/259/tyc2&-c=142.10549+%2B14.90721&-c.rd=4.2&-out.add=_RAJ2000,_DEJ2000,_r&-out=TYC1,TYC2,TYC3,BTmag,VTmag,HIP&-out.max=6000&VTmag=%3C9.0` |
| Tycho-2 creuament `tyc2_deep.tsv` (5°, VT<12,5) | `comu.TYC2_DEEP` | VizieR I/259: `…&-c.rd=5.0&-out=TYC1,TYC2,TYC3,BTmag,VTmag,HIP,pmRA,pmDE&-out.max=30000&VTmag=%3C12.5` (URL sencera a `baixa_catalegs.sh`) |
| Efemèride DE440s (32,7 MB) | `comu.EFEMERIDE` = `~/.cache/skyfield/de440s.bsp` | `https://ssd.jpl.nasa.gov/ftp/eph/planets/bsp/de440s.bsp` (mai un `load()` relatiu: baixa al cwd) |
| ARW Sony A7RIIIA + 300 GM | `DADES_300MM` = `~/Desktop/Eclipse 2026/300mm` | DSC06984/85/87/88/91/93/96/99 (estrelles), DSC06982/83/86 (corona) |
| CR3 Vixen dins totalitat | `DADES_VIXEN_UNF` = `~/Desktop/Eclipse 2026/Vixen Unfiltered` | 572A2978–2984, 2996 (estrelles); 2969–72, 2987–90, 2999–3002, 3005–08 (center2); 2970/71/77 (corona); 2983 (APOD) |
| Darks A7RIIIA | `DARKS_SONY` = `~/Desktop/Eclipse 2026/Darks A7RIIIA Eclipse` | 24 primers per nom de 8 s / 2 s / 1 s (llista a MAPA_sony §3); sense `-r` |
| Darks R6 III | `DARKS_R6` = `~/Desktop/Eclipse 2026/Darks Canon R6III Eclipse` | ExposureTime EXIF exacte 10 (25), 2 (21), 1 (15) |
| Paràmetres del halo (earthshine) | `HALO_PARAMS` = `~/Desktop/Eclipse 2026/Earthshine_FINAL/earthshine_FINAL_halo_params.json` | `xmatch/wings.py`, `wings2.py` |
| `exiftool` (PATH) | — | `sony/darks.py`, `vixen/mkdark.py`, `center2.py`, `deflexio/mascara_estrelles.py` (només sense fotograma per defecte) |
| `ffmpeg` (`/opt/homebrew/bin/ffmpeg`) | — | `apod/munta_video.sh` |
| Fonts macOS (Arial Bold, Arial, Menlo) | `/System/Library/Fonts/…` | `apod/animacio.py` (cau a `load_default` si falten) |
| Python: numpy, scipy, pandas, rawpy, astropy, photutils (3.0.0: API antiga a `vixen/proc.py`), skyfield, Pillow | l'intèrpret que dona `comprova_entorn.py --python` (avui `~/.venvs/eines-ia-py312`) | — |

Sortides: `ESTRELLES_WORK` (intermedis per subàrea + `_registres/*.log`), `ESTRELLES_OUT` (catalog_sony.txt,
final_solution.json, final_match_*, IDENTIFICACIONS_*, zp2.json, corona2.csv, wings.json, estrelles_*.csv,
estrelles_*_marcades.png, _zooms.png), `APOD_OUT` (PNG/JPG nets, retalls_estrelles.json, mp4/gif,
APOD_submission.html). `pipeline_estrelles.sh --prova DIR` ho redirigeix tot a `DIR/{Estrelles_work,Estrelles,APOD}`.

## 5. Què s'ha provat en aquesta promoció (17-08-2026) i què no

Tot en mode prova sota `~/Desktop/Eclipse 2026/_prova_skill/` (`Estrelles_work`, `Estrelles`, `APOD`), amb
`~/.venvs/eines-ia-py312/bin/python`, cwd arbitrari (`/`, `/tmp`, `$HOME`), i comparat amb el rescat i amb
els scratchpads originals (ea55df18 i 604fa71e, que el 17-08 encara existien).

**Provat, subàrea a subàrea, cridant els scripts a mà (no encara pel pipeline):**

- `prediccio`: cadena sencera dues vegades; `hip_4deg.csv`, `candidates_v8.csv`, `taula_final.csv` **byte-idèntics**; Sol 9,07°, X 6,055, R☉ 947,07″.
- `sony`: els 22 scripts des dels RAW i darks; `catalog_sony.txt` **byte-idèntic** (MD5 fbf53236…), 38 fonts; DSC06988 4,0σ; rotació 0,138°; guany 3,323.
- `vixen`: els 13 des dels CR3 i darks; tots els .npy `np.array_equal` amb els originals; `catalog_vixen_fonts.csv` **byte-idèntic**; 0,610 ″/s.
- `xmatch` + `fotometria`: cat…final_solve regenerats i idèntics; phot2 i wings de veritat amb els intermedis frescos; 38/38 i 22/24; 3,20199/2,14948; ZP 14,167/14,205; B/B☉ 1,1352e-11/2,7714e-11 (amb color); quocient 0,952.
- `esceptic`: els 8; `noise.npy` fresc **bit-idèntic** a `noise_rescat_16-08.npy`; 5,0σ; 0,950; 15.161/16.383; unic 0,01–0,02/0,00.
- `deflexio` + `mascara`: σ(ε) 1,39/0,57/0,53; `retalls_estrelles.json` **byte-idèntic**; 17/38 i 22/24 visibles.
- `apod`: PNG nets, figA/figB, 714 fotogrames, mp4 i gif **byte-idèntics** al viu; HTML idèntic tret dels dos data-URI de les marcades (més etiquetes).
- `test_acceptacio.py` contra aquest WORK/OUT de prova: **22 ✓ · 0 ✗ · 0 no trobat**; contra un directori buit: 20 «no trobat», rc 0, sense petar.
- `pipeline_estrelles.sh --nomes-mostra`: llista les 77 ordres sense error; `--prova … acceptacio`: executa l'etapa i deixa `_registres/test_acceptacio.log`.

**No provat encara:**

- `pipeline_estrelles.sh` **sencer** d'un sol cop (les etapes s'han executat a mà una per una en el mateix WORK; l'orquestrador només ha corregut `--nomes-mostra` i `acceptacio`).
- La baixada real de `baixa_catalegs.sh` (els tres catàlegs hi són; només `curl -I` al CDS: 200, mateixa mida).
- `esceptic/inject2.py` i `sat.py` amb l'`offsets6.pkl` **regenerat** per `sony/scan.py` (a la prova era el del scratchpad; el catàleg final és idèntic, o sigui que ha de sortir igual, però no s'ha tornat a córrer).
- Els camins sense `ffmpeg`, sense fonts del sistema, i `mascara_estrelles.py` per EXIF (sense fotograma per defecte).
- Cap execució amb els productes **vius** de l'Escriptori com a destí (tot ha anat a `_prova_skill`); en producció `final3.py` copia `catalog_sony.txt` a `Estrelles/` i les marcades i `estrelles_*.csv` **sobreescriuen** les escrites a mà el 16-08 (més etiquetes; A-17/A-18 corregits, MAPA_deflexio §5).
- El 0,625 ± 0,042 ″/s de research/75 §5.4 (fitpsf dona 0,677 ± 0,051, fit2 0,545 ± 0,023) i el «13,9 px» de moviment lunar: no reproduïts per cap script promogut.

## 6. Trampes de noms i de números

- **`final.py` ≠ `final.py`**: `prediccio/final.py` és la taula SNR de la predicció; `sony/final2.py`/`final3.py` són els retalls del catàleg Sony (41 → 38); `vixen/final2.py` escriu `final.json`; la placa és `xmatch/final_solve.py`. Cap és `xmatch/refine.py`, que és **només biblioteca** (el seu `__main__` no s'executa).
- **`corona2.py` de `xmatch/` ≠ `corona2.py` de `deflexio_apod`**: el promogut és el de calibratge (perfil B/B☉, terme de color); el del pressupost 2027 queda al rescat i no s'ha promogut.
- **`combina.py` (prediccio) ≠ `combine.py` (PTC, rescat)**; `stack2.py` de `sony/` (peaks3/offsets3) ≠ `stack2.py` de `vixen/` (mitges piles A/B); `cat.py` de `sony/` (catàleg creuat + fotometria) ≠ `cat.py` de `xmatch/` (Tycho-2 + Hipparcos en pla tangent); `refine.py` de `sony/` (offsets2) ≠ `refine.py` de `xmatch/` (biblioteca).
- **Escala vella / nova**: 3,234 / 2,158 ″/px (radi lunar, pre-placa) surten a `prediccio/`, `sony/` (només per imprimir), `vixen/` (tota la subàrea), `xmatch/solve.py` (llavor de la cerca grollera) i a `deflexio/fusiona_csv.py` (FWHM en px de la Sony); la **placa** és 3,2020 / 2,1495 (radial; `final_solution.json` `*_radial`) i 3,1923 / 2,1478 (lineal; escrites a `wings2.py`). `comu.SONY/R6` en porten les dues (`escala_vella`, `escala`).
- **Guany**: 3,323 e⁻/ADU és el que **usa** tota la cadena Sony (`sony/gain.py`, `cat.py`); research/75 publica 3,41 ± 0,07 d'un altre PTC. Al Vixen `wings.py` duu 3,05 i research/75 mesura 5,08 (verd). Divergències documentades, no reconciliades (`comu.SONY['guany_cadena']`/`['guany_publicat']`).
- **R☉**: 947,07″ (`suns.json`; `xmatch/`, `esceptic/`, `prediccio/`, `comu.R_SOL_ARCSEC`) contra **946,66″** (calculat per `deflexio/deflexio.py` i copiat a mà a `retall_estrella.py`, `moviments.py`, `apod/animacio.py`); α limbe 1,7516″ (deflexio) / 1,7508 / 1,7512 (APOD). No unificat per no canviar cap número.
- **`identificacions.py` va a l'etapa `fotometria`**, després de `bemporad.py`, no a `xmatch` (si es crida abans deixa flux_tot/Vobs/dV buits i ho avisa).
- **`corona2.csv` ha canviat de format**: `fac` és ara el factor **amb** color (1,135e-11 / 2,771e-11) i `fac_nocolor` l'antic (1,188e-11 / 2,534e-11). `test_acceptacio.py` ho sap; qualsevol altre lector antic ha de mirar `fac_nocolor`.
- **`FINAL_idx.npy` (sony) té 41 índexs, no 38**; la llista final és `catalog_sony.txt`. `offsets5.pkl` s'escriu dues vegades (mana boot2); `offsets6.pkl` són els definitius.
- **`catalog_vixen_fonts.csv` té 32 files**: les 24 fonts publicades són classe A + B; les 8 REBUTJADA no van a `estrelles_r6.csv`. `r_sol_*` d'aquest CSV és distància al centre **lunar** de 572A2982.
- **Rellotges i èpoques**: la placa Sony és a 18:29:48,0 UTC i la R6 a 18:29:18,6 (`comu.T_PLACA_*`); la predicció, a 18:29:38. `shifts_start.json` (vixen) assumeix DateTimeOriginal = inici d'exposició.
- **`noise.npy`**: `esceptic/zprefit.py` i `chain.py` llegeixen `work(esceptic)/noise.npy` (fresc, d'`inject2.py`) i, si no hi és, `esceptic/noise_rescat_16-08.npy` amb un `[avis]`.
- **`apod.tpl.html` és entrada**, no producte: font escrita a mà, al costat de `munta.py`; sense ella `munta.py` no pot acabar.
- **`figures.py` duu incrustats** els 15 moviments (de `moviments.py`) i els 62 r/R☉ (de `deflexio.py`): si es reculen els CSV s'han de tornar a copiar a mà.
