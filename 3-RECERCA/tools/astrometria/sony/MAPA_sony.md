# MAPA_sony — detecció cega d'estrelles del tren Sony A7RIIIA + FE 300 mm f/2,8 GM

Promoció del 17-08-2026 de la cadena mínima canònica de
`research/tools/rescat_scratchpad_2026-08-17/estrelles_placa_flats_16-08/sony_stars/`
(sessió del 16-08-2026, 14:02–14:42) a `research/tools/astrometria/sony/`.
Producte final: `catalog_sony.txt` (38 files, S01–S38), a `comu.work("sony")` i còpia a `comu.out()`.

**Resultat de la prova sencera (17-08, mode `--prova`): `catalog_sony.txt` idèntic byte a byte
al del rescat (MD5 `fbf53236c139b4268932373129c6713d`, 48 línies, 38 fonts).**

## 1. Fitxer promogut → fitxer d'origen

Tots conserven el nom. Origen: `…/estrelles_placa_flats_16-08/sony_stars/<mateix nom>`.

| # | Promogut | Origen (rescat) | Rol | Canvi respecte de l'original |
|---|---|---|---|---|
| 1 | `darks.py` | `sony_stars/darks.py` | master darks per mediana (24 primers per nom de 8, 2, 1 s) | capçalera comu; `DD=str(comu.DARKS_SONY)+"/"` |
| 2 | `runall.py` | `sony_stars/runall.py` | pics >4,5σ per fotograma → `peaks.pkl` (arrel del llinatge d'offsets) | capçalera comu; `D=str(comu.DADES_300MM)+"/"` |
| 3 | `reg3.py` | `sony_stars/reg3.py` | registre inicial (centroide saturat + histograma 2-D) → `offsets.pkl` | capçalera comu; `D=…` |
| 4 | `numden.py` | `sony_stars/numden.py` | pics subpíxel → `peaks2.pkl` | capçalera comu; `D=…` |
| 5 | `refine.py` | `sony_stars/refine.py` | refina offsets → `offsets2.pkl` | capçalera comu |
| 6 | `moon.py` | `sony_stars/moon.py` | centre i radi lunar → `moon.pkl` (CX,CY = 3894,1 / 2765,6) | capçalera comu; `D=…` |
| 7 | `mf3.py` | `sony_stars/mf3.py` | detector definitiu (DC-blind) → `N_*.npy`, `D_*.npy`, `bkg_*.npy` | capçalera comu; `D=…` |
| 8 | `stack2.py` | `sony_stars/stack2.py` | `peaks3.pkl`, `offsets3.pkl`, apilat de 8 | capçalera comu |
| 9 | `reg4.py` | `sony_stars/reg4.py` | registre amb camp estel·lar pur → `offsets4.pkl` | capçalera comu |
| 10 | `boot.py` | `sony_stars/boot.py` | llista mestra `master_xy.npy`/`master_snr.npy`; `offsets5.pkl` (v. boot) | capçalera comu; **guarda del `print` quan `best is None`** (vegeu §5) |
| 11 | `boot2.py` | `sony_stars/boot2.py` | re-registre contra la mestra → `offsets5.pkl` (la que mana) | capçalera comu |
| 12 | `scan.py` | `sony_stars/scan.py` | força bruta ±40 px → `offsets6.pkl` (definitius); DSC06988 4,0σ | capçalera comu |
| 13 | `groups.py` | `sony_stars/groups.py` | apilats per grup → `SA.npy`, `SC.npy` | capçalera comu |
| 14 | `warp.py` | `sony_stars/warp.py` | parelles A↔C >7σ → `u.npy`, `v.npy`, `s.npy` | capçalera comu |
| 15 | `fitwarp.py` | `sony_stars/fitwarp.py` | similitud A→C (rotació 0,138°) → `warpM/T/C.npy` | capçalera comu |
| 16 | `imgs.py` | `sony_stars/imgs.py` | imatges apilades ADU/s → `IMGA.npy`, `IMGC.npy` | capçalera comu; `D=…` |
| 17 | `cat.py` | `sony_stars/cat.py` | catàleg creuat + fotometria → `catalog.npz` | capçalera comu; `D=…` |
| 18 | `clean.py` | `sony_stars/clean.py` | selecció segura → `secure.npz` | capçalera comu |
| 19 | `final2.py` | `sony_stars/final2.py` | retall v1 (41) → `FINAL_idx.npy`, `catalog_sony.txt` v1 | capçalera comu |
| 20 | `final3.py` | `sony_stars/final3.py` | retall v2 (38) → **`catalog_sony.txt`** | capçalera comu; **còpia final a `comu.out()`** |
| 21 | `build.py` (opcional) | `sony_stars/build.py` | apilat de 7 → `F_SNR/F_DEN/F_COV/F_IMG/F_WT.npy` (F_IMG el llegia xmatch/phot.py, superat per phot2) | capçalera comu; `D=…` |
| 22 | `gain.py` (evidència) | `sony_stars/gain.py` | PTC DSC06996/06999 → provenança del GAIN 3,323 e⁻/ADU | capçalera comu; `D=…` |

Capçalera comuna afegida al capdavant de tots (idèntica als 22):

```python
#!/usr/bin/env python3
# Promogut de research/tools/rescat_scratchpad_2026-08-17/estrelles_placa_flats_16-08/sony_stars/<nom>.py
# (sessio del 16-08-2026). Nomes canvien les rutes: dades i intermedis surten de comu.py.
import sys, os; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu
os.chdir(comu.work("sony"))
```

L'`os.chdir(comu.work("sony"))` fa que tots els fitxers relatius (`masterdark_*.npy`, `peaks*.pkl`, `offsets*.pkl`,
`N_/D_/bkg_*.npy`, `SA/SC/IMGA/IMGC.npy`, `catalog.npz`, `secure.npz`, `FINAL_idx.npy`, `catalog_sony.txt`…)
vagin a `$ESTRELLES_WORK/sony/` sigui quin sigui el cwd des d'on es cridi l'script.
`grep -rn "/private/tmp\|/Users/USUARI" sony/` dona zero.

## 2. Ordre d'execució exacte (relatiu a `research/tools/astrometria/`, `$PY` = intèrpret detectat)

```
$PY sony/darks.py
$PY sony/runall.py
$PY sony/reg3.py
$PY sony/numden.py
$PY sony/refine.py
$PY sony/moon.py
$PY sony/mf3.py
$PY sony/stack2.py
$PY sony/reg4.py
$PY sony/boot.py
$PY sony/boot2.py
$PY sony/scan.py
$PY sony/groups.py
$PY sony/warp.py
$PY sony/fitwarp.py
$PY sony/imgs.py
$PY sony/cat.py
$PY sony/clean.py
$PY sony/final2.py
$PY sony/final3.py
$PY sony/build.py      # opcional (F_IMG.npy i companyia; cap script de la cadena final el llegeix)
$PY sony/gain.py       # opcional, evidència del 3,323 e⁻/ADU
```

Cap dependència de cwd. Variables d'entorn que llegeix (via `comu.py`): `DADES_300MM`, `DARKS_SONY`,
`ESTRELLES_WORK`, `ESTRELLES_OUT`. Dependències: rawpy, numpy, scipy, astropy, photutils, `exiftool` al PATH.

## 3. Entrades i sortides

**Entrades (només lectura):**
- `comu.DADES_300MM/DSC06984.ARW` (2 s), `06985` (1 s), `06987` (8 s), `06988` (1 s; només fins a `scan`, exclosa després),
  `06991` (1 s), `06993` (8 s, REF), `06996` (2 s), `06999` (2 s). `gain.py` llegeix `06996` i `06999`.
- `comu.DARKS_SONY/*.ARW`: `darks.py` fa `exiftool -T -FileName -ExposureTime <DD>` **sense `-r`** (ignora la
  subcarpeta `APP Master Darks`), agrupa per la cadena literal `8`, `2`, `1` i agafa **els 24 primers per nom**.
  Llista verificada el 17-08 (44 de 8 s, 49 de 2 s, 45 d'1 s al directori, com al mapa del rescat):
  - **8 s (24 de 44):** DSC09188 … DSC09197 (10) + DSC09855 … DSC09868 (14)
  - **2 s (24 de 49):** DSC09198 … DSC09203 (6) + DSC09905 … DSC09922 (18)
  - **1 s (24 de 45):** DSC08851, DSC08852, DSC08853 (3) + DSC09729 … DSC09749 (21)

**Sortides a `comu.work("sony")`** (106 fitxers, **10 GB** mesurats amb `build.py` inclòs; ≈8,5 GB sense; els
`res_/valid_` de runall i els `num_/den_/validbits_` de numden —3,9 GB— no els llegeix cap pas posterior i es poden esborrar):
`masterdark_{1,2,8}s.npy`, `peaks.pkl`, `offsets.pkl`, `peaks2.pkl`, `offsets2.pkl`, `moon.pkl`,
`N_*.npy`/`D_*.npy`/`bkg_*.npy` (×8), `peaks3.pkl`, `offsets3.pkl`, `SNR/FLX/DEN/COV.npy`, `offsets4.pkl`,
`master_xy.npy`, `master_snr.npy`, `offsets5.pkl`, **`offsets6.pkl`**, `SA.npy`, `SC.npy`, `warpAC/warp_c0/pairs_*.npy`,
`u/v/s.npy`, `warpM/warpT/warpC.npy`, `IMGA.npy`, `IMGC.npy`, `catalog.npz`, `secure.npz`, `FINAL_idx.npy` (41, no 38),
**`catalog_sony.txt`** (38); amb `build.py`: `F_SNR/F_DEN/F_COV/F_IMG/F_WT.npy`.

**Sortida a `comu.out()`:** còpia de `catalog_sony.txt` (afegit a `final3.py`; l'original només l'escrivia al cwd).

Els consumidors d'altres subàrees han de llegir: `comu.work("sony")/catalog_sony.txt` (xmatch/solve),
`comu.work("sony")/offsets6.pkl`, `masterdark_*s.npy`, `bkg_*.npy` (xmatch/phot2, wings; esceptic/sat, inject2),
`IMGA/IMGC.npy` i `F_IMG.npy` (xmatch/phot antic).

## 4. Cost mesurat (17-08-2026, Mac de Pere, mode prova, disc APFS)

| Script | s | Script | s | Script | s |
|---|---:|---|---:|---|---:|
| darks | 28 | mf3 | 57 | imgs | 14 |
| runall | 117 | stack2 | 15 | cat | 10 |
| reg3 | 1 | reg4 | 0 | clean | 0 |
| numden | 116 | boot | 5 | final2 | 0 |
| refine | 0 | boot2 | 0 | final3 | 0 |
| moon | 13 | scan | 1 | build (opc.) | 20 |
| | | groups | 8 | gain (opc.) | 0 |
| | | warp+fitwarp | 2 | | |

Total cadena mínima ≈ **6 min 27 s**; amb build+gain ≈ 6 min 47 s. Coincideix amb la previsió (6–8 min).

## 5. Què s'ha provat i amb quin resultat

Compilació: `py_compile` dels 22 → OK. Execució sencera amb
`ESTRELLES_WORK=…/_prova_skill/Estrelles_work`, `ESTRELLES_OUT=…/_prova_skill/Estrelles`, `APOD_OUT=…/_prova_skill/APOD`,
intèrpret `~/.venvs/eines-ia-py312/bin/python` (rawpy 0.27.0, numpy 2.5.1, scipy 1.18.0, astropy 8.0.1, photutils 3.0.0),
cridada des de `cwd=/` a propòsit. Cap entrada agafada del rescat: tot regenerat des dels RAW i els darks.

- `darks.py`: 44/49/45 darks trobats, 24 de cadascun (llista de §3).
- `runall`/`numden`/`mf3`: 8 fotogrames processats.
- `moon.py`: DSC06993 → (3894,1 , 2765,6) (capçalera del catàleg idèntica).
- `scan.py`: DSC06988 significació **4,0** sobre 6561 proves (la frase de la capçalera); la resta 9,5–22,0.
- `fitwarp.py`: rotació A→C **+0,1379°**, escala 1,000510 (el 0,138° de la síntesi §3).
- `cat.py`: 320 aparellades; `clean.py`: 319 després de dedupe, 79 segures; `final2.py`: 41; `final3.py`: **38**
  («FINAL confirmed stellar point sources: 38 (rejected 3 sitting on corona structure)»).
- **`catalog_sony.txt` nou = rescat, byte a byte** (`diff` buit; MD5 `fbf53236c139b4268932373129c6713d` als dos i a la còpia d'OUT).
  Per tant posicions, fluxos, SNR, FWHM, colors i V_est coincideixen exactament (≤ 0,05 px sobradament: 0,00).
- `gain.py`: pendent 0,30090 → **3,323 e⁻/ADU** (la constant escrita a la cadena; research/75 publica 3,41 ± 0,07 d'un altre PTC).
- `build.py`: apilat de 7 fotogrames, SNR mediana −0,003, sd 1,084 (com l'original).

**Incidència trobada i resolta (`boot.py`).** A la primera passada la cadena es va aturar a `boot.py` amb
`TypeError: 'NoneType' object is not subscriptable` a la línia del `print` per a DSC06988: amb `offsets4` aquest
fotograma no arriba a 3 aparellaments a la primera tolerància (25 px), el bucle fa `break` i `best` queda `None`.
L'original tenia exactament el mateix codi, i les marques temporals del rescat (boot.py 14:28:29–14:28:34, 5 s,
igual que aquí; boot2.py escrit tot seguit a 14:28:53) fan pensar que el 16-08 va petar al mateix punt: `master_xy.npy`
i `master_snr.npy` ja són escrits abans del bucle, i l'`offsets5.pkl` de boot el sobreescriu `boot2.py`, que llegeix
`offsets4.pkl`. La correcció és **només** no petar: si `best is None` s'imprimeix una línia informativa i es passa al
fotograma següent (`continue`; `NEW[n]` ja té l'offset previ). No toca cap número: el catàleg final és idèntic.
Cadena represa des de `boot.py` fins al final sense cap altre incident.

## 6. Constants que continuen escrites a cada script (no s'han tocat, a propòsit)

GAIN 3,323; SG 1,3; HW 7; sostre 15600 + dilatació 8; vora 40/45 px; saturació 16380; Background2D (32,32)/(3,3)/σ3/30 %;
REF DSC06993; RSUN 293; AS 3,234 (escala vella, només per imprimir); ZP 3,6e6; c=(3894, 2766) a fitwarp; llindars
4,5/5/7σ; cKDTree 3,0/1,8/1,5/2; W 90/35/40; clean (3,5 px; joint>6; FWHM 2,8–4,8; b/a>0,55; loc<25; crowd≤1; R>1,2);
final2 (FWHM<4,15; FT/ET>3; 0,15<R/G<2,6; −0,5<B/G<1,9); final3 (nivell<12; p90−p10<28); llistes FR/EXP/USE/A/C.
`comu.SONY` en duu una part (pedestal, sostre, guanys, ref, centre lunar, fotogrames) com a documentació; **cap script
promogut no la llegeix** per no canviar cap valor sense voler.

## 7. Trampes documentades

- `FINAL_idx.npy` té **41** índexs (final2), no 38: no el prenguis com a llista final; la llista final és `catalog_sony.txt`.
- `final2.py` escriu una `catalog_sony.txt` de 41 files que `final3.py` sobreescriu tot seguit: no aturis la cadena entre els dos.
- `offsets5.pkl` s'escriu dues vegades (boot, boot2); mana la de boot2. `offsets6.pkl` són els definitius.
- `mf3.py` processa DSC06988 (N_/D_ existeixen) però `build/groups/imgs/cat` l'exclouen.
- `groups.py` usa c0=(3984,2660) i `fitwarp.py` c=(3894,2766): són dos centres diferents a propòsit (el primer no es fa servir després).
- Aquest `final3.py` ≠ `vixen/final*.py` ≠ `xmatch/final_solve.py`.
