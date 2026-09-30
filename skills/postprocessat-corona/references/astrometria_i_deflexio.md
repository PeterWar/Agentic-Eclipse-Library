# Astrometria i deflexió: placa d'estrelles, calibratge absolut, Einstein

Estat: 17-08-2026. Font d'autoritat del mètode: `3-RECERCA/75` §5 (placa i
calibratge), `3-RECERCA/77` §1-2 (deflexió), `4-RESULTATS/derivats/Astrometria/Estrelles/
LLEGEIX-ME.md`. El codi viu és `3-RECERCA/tools/astrometria/` (promogut el 17-08
del rescat `3-RECERCA/tools/rescat_scratchpad_2026-08-17/`; l'índex fitxer a
fitxer és `3-RECERCA/tools/astrometria/MAPA.md`) i l'orquestrador
`3-RECERCA/tools/astrometria/pipeline_estrelles.sh`.

## 0. Per què és dins la skill

Les estrelles de la totalitat són el pont entre les imatges i el món físic:
d'elles surten **l'escala de placa real, el nord celeste, el centre del Sol al
sensor, el punt zero fotomètric i el factor a B/B☉** que fa comparable el
compost amb LASCO i K-Cor sense mesurar la densitat del filtre. I la deflexió
gravitatòria és el mateix ajust amb un paràmetre més. Pere ho va demanar dins
la skill el 17-08.

Regla d'or: **l'astrometria es fa sobre fotogrames crus i piles pròpies, mai
sobre l'HDR de la corona; l'HDR consumeix la placa (centre del Sol, escala,
PA), no la fa.**

## 1. La cadena, en ordre

| # | Etapa | Directori | Què fa | Producte |
|---|---|---|---|---|
| P | Predicció | `prediccio/` | skyfield + DE440s des de FINAL 2 a les 18:29:38 UTC; Hipparcos (`hip_main.dat`, CDS I/239) prefiltrat a 6°, aparent, dins 4° del Sol; Tycho-2 (`tyc2.tsv`) per completar a V ≤ 8; SEGUR/POSSIBLE/FORA per tren; SNR previst | `hip_4deg.csv` (112), `candidates_v8.csv` (42), `taula_final.csv` |
| S | Detecció cega Sony | `sony/` | 8 ARW (grup A 06984/85/87 = 11 s, grup C 06991/93/96/99 = 13 s; 06988 i 06990 fora), masters de fosc propis, pla verd interpolat, `Background2D` (32,32), detecció sobre residu/σ, aparellament entre fotogrames, warp per segments (el salt de la muntura), fotometria d'obertura r ≤ 5 / anell 7–10, PSF, neteja (FWHM 2,8–4,8, b/a > 0,55, colors) | `catalog_sony.txt` (38 fonts S01–S38, sistema de DSC06993) |
| V | Detecció cega Vixen | `vixen/` | 8 CR3 (2978 1 s; 2979–81 2 s; 2982–84 10,3 s; 2996 1 s), masters, `center2` amb 16 curts, DAOStarFinder sobre residu, registre a deriva constant (prior V = (0,199, −0,214) px/s), piles, classes A/B, obertura 5 / anell 9–14 | `catalog_vixen_fonts.csv` (32 files: 21 A + 3 B = 24; 8 rebutjades) |
| X | Creuament + placa | `xmatch/` | catàleg projectat (Tycho-2 profund + Hipparcos, 5°), aparellament gruixut → fi, **model lineal + terme radial r³ en marc alt/az refractat** (20 °C, 930 mbar), èpoques 18:29:48,0 (Sony) i 18:29:18,6 (R6) | `final_solution.json`, `final_match_*.csv` (38 / 22), `IDENTIFICACIONS_*.csv` |
| F | Fotometria absoluta | `xmatch/` | fotometria d'obertura (anell 26–40 px), corba de creixement, ZP amb terme de color i extinció aparent, factor a B/B☉ amb **F☉ = 10^(0,4·(ZP + 26,75 − 0,653·c))**, Bemporad, ales de la PSF, orientació | `zp2.json`, `corona2.csv`, `wings.json`, `radi_*.csv` |
| E | Escèptic | `esceptic/` | injecció de fonts sintètiques als 7 ARW (soroll per banda, biaix 3–4 %), refit del ZP, cadena del terme de color (0,83 → 0,95), unicitat per atzar (0,02 / 0,00), doble no resolta, saturació | stdout + `noise.npy` |
| D | Deflexió | `deflexio/` | fusió catàleg + identificacions → `estrelles_*.csv`; ajust conjunt placa + ε (similitud, σ★ = rms/√2): σ(ε) 1,39 / 0,57 / **0,53** → 1,9σ i 0,9σ Einstein–Newton; retall d'estrelles heroi; moviments; màscara marcada | `estrelles_sony.csv`, `estrelles_r6.csv`, `retalls_estrelles.json`, PNG marcades |
| A | APOD | `apod/` | imatges netes/anotades, animació *where Newton would have put it* (714 fotogrames → mp4/gif), pàgina HTML | `6-PUBLICACIO/APOD/` |

Fora de la skill (evidència, no cadena): el pla del 2027 (`3-RECERCA/77`, Fisher,
requisits, previsions) i les mesures de resolució/ESF/MTF, flats i foscos de
`3-RECERCA/75` §1–4, que viuen al rescat.

## 2. Els números que ha de reproduir (i qui els imprimeix)

| Número | Valor | Script |
|---|---|---|
| Fonts cegues | 38 (Sony) · 24 (R6: 21 A + 3 B) | `sony/final3.py`, `vixen/cat_final.py` |
| Identificades | 38/38 · 22/24; per atzar 0,02 / 0,00 | `xmatch/final_solve.py`, `esceptic/unic.py` |
| Escala | **3,2020 ″/px** (−0,99 % del 3,234 lunar: oberta) · **2,1495** | `xmatch/final_solve.py` |
| Nord / est | PA 90,27° / 358,64° · 57,19° / 325,59° | `final_solve.py`, `orient.py` |
| Centre del Sol | (3894,7, 2768,7) DSC06993 · (3570,8, 2267,1) 572A2983 (lineal; el radial dona 3894,0 / 3571,0) | `final_solve.py` |
| Residu | mediana 0,54 / 0,32 px (rms 0,71 / 0,42) | `final_solve.py` |
| ZP | +14,167 ± 0,065 · +14,205 ± 0,040 (publicat ±0,08) | `xmatch/zp2.py` |
| k aparent, c | 0,416 / 0,723 (5σ: vinyetatge, **no és extinció**); c −0,076 / +0,149 | `zp2.py`, `esceptic/chain.py` |
| B/B☉ per ADU/s | **1,134·10⁻¹¹ · 2,772·10⁻¹¹** (±10 %; sense color 1,188 / 2,534) | `xmatch/corona2.py` |
| Quocient corona R6/Sony | 0,95 (0,83 sense el terme de color) | `corona2.py` + `chain.py` |
| Diferència entre trens | 0,32 mag fora de 6 R☉ (criteri ≤ 0,35), 0,96 dins | `bemporad.py`, `cross2.py` |
| Fotometria d'obertura | insesgada al 3–4 % de 2,6 a 14 R☉; 1,3–3,0× a 1,6–2,6 | `esceptic/inject2.py` |
| Soroll per banda (ADU/s) | 1.780 · 162 · 87 · 79 · 53 (1,6–2,6 → 9–14 R☉) | `inject2.py` |
| Ales de PSF fiables | 13 px (Sony) · 30 px (R6); a 87,5 px el halo estel·lar és 2.800× per sota | `wings2.py` |
| Nord lunar | 71,97° al sensor Sony contra 71,5° del LROC → 0,47° | `orient.py` |
| Deriva Vixen | 0,610 ± 0,010 ″/s (fotograma a fotograma) · 0,625 ± 0,042 (traços) | `vixen/reg.py`, `fitpsf.py` |
| σ(ε) | 1,39 / 0,57 / 0,53 → **1,9σ**, 0,9σ Einstein–Newton | `deflexio/deflexio.py` |
| Estrella heroi | HIP 46345 (2,646 R☉): 0,662″ = 0,308 px (Newton 0,331″) | `retall_estrella.py` |
| Cel | 9,34 / 9,15 mag/arcsec² a 8 R☉; V límit 9,18 (HIP 46561, als dos) | (cap script el reimprimeix: `3-RECERCA/75`) |

`3-RECERCA/tools/astrometria/test_acceptacio.py` afirma la taula amb les
toleràncies de `comu.ACCEPTACIO`.

✅ **Passada de prova del 17-08-2026**, executada originalment amb
`pipeline_estrelles.sh --prova _prova_skill_estrelles`
(les onze etapes d'un sol cop,
des dels RAW i els darks, sense cap intermedi del rescat): **11 min 05 s,
sortida 0, 22 ✓ · 0 ✗ · 0 no trobat**, ~15 GB d'intermedis. `catalog_sony.txt`
i `catalog_vixen_fonts.csv` byte a byte idèntics als del 16-08; `noise.npy` de
l'escèptic idèntic amb els `offsets6.pkl` regenerats; `retalls_estrelles.json`,
`_net.png`, mp4 i gif idèntics als vius. Registres a
`Derivats/Astrometria/Estrelles/Rebuts/acceptacio_22de22/registres/*.log`; el
work preservat és `Derivats/Astrometria/Estrelles/Work_2026-08-17/`. Cap
producte viu d'`Estrelles/` ni d'`APOD/` va ser tocat durant aquella passada.
La cadena viva usa per defecte `Derivats/Astrometria/Estrelles/_work/` per als
intermedis mutables i l'arrel `Derivats/Astrometria/Estrelles/` per als
productes. `Work_2026-08-17/` i `Resultats_acceptacio_2026-08-17/` són una
prova i una acceptació preservades: no són destinacions d'escriptura per defecte.

## 3. Constants que manen (a `comu.py`)

Lloc 42,299407 / −5,02503 / 798 m; predicció 18:29:38 UTC; èpoques de placa
18:29:48,0 (Sony) i 18:29:18,6 (R6); refracció 20 °C / 930 mbar; centre de
cerca J2000 142,10549 / +14,90721; R☉ 947,07″; m☉ −26,75; (B−V)☉ 0,653;
deflexió al limbe 1,7516″. Pedestals 512 / 511,5; vàlid < 15600 (Sony, dilatat
8) / 15800 (R6). **Guanys de la cadena** 3,323 (Sony) i 3,05 (R6) — no són els
publicats (3,41 / 5,08): la cadena els porta a dins i el `MAPA.md` ho anota
perquè no es «corregeixin» a mitges. Escales **velles** 3,234 / 2,158 a la
detecció; **noves** 3,2020 / 2,1495 a la màscara i la deflexió.

## 4. Trampes pròpies d'aquesta cadena

- **La predicció no alimenta el creuament**: és el registre de la cerca cega
  (predir i detectar els van fer agents separats; el creuament després). No
  «ajudis» el detector amb el catàleg.
- **Cap número de placa surt de l'arrel del rescat** (`combina.py`, `fit.py`,
  `final.py` de l'arrel són predicció i PTC): tot és a `xmatch/`.
- **Noms que xoquen**: `final.py` (arrel) ≠ `sony/final*.py` ≠ `vixen/final*.py`
  ≠ `xmatch/final_solve.py`; `corona2.py` de `xmatch/` (calibratge) ≠
  `corona2.py` del pla 2027; `combina.py` ≠ `combine.py`.
- **`corona2.py` no aplicava el terme de color** (−0,653·c): sense ell els
  factors surten 1,188 / 2,534·10⁻¹¹ i el quocient entre trens 0,83. El
  promogut el porta i imprimeix les dues versions.
- **k = 0,416 / 0,723 no és l'extinció**: és pendent contra massa d'aire dins
  el camp i està dominat pel vinyetatge; el coeficient bo és el diferencial de
  dins la totalitat (0,402, `3-RECERCA/78`).
- **Les ales de la PSF no es mesuren amb estrelles** més enllà de 13 / 30 px
  (límit físic); el halo es valida amb la fotosfera filtrada.
- **`FINAL_idx.npy` té 41 índexs, no 38** (versió superada): la llista final és
  `catalog_sony.txt`. `offsets5.pkl` és sobreescrit per `boot2`.
- **σ(ε) és una previsió de Fisher sobre la placa, no una detecció**; l'APOD és
  «un retrat, no un test». HIP 46335 té SNR 0,07, no 5,9: no calibra res.
- **Sostres i llavors mouen les 38/24**: 15600 + dilatació 8 (Sony), 15800
  (R6), llavors 3 i 11 (injecció) i la d'`unic.py` (fixada a la promoció).
- **`proc.py` usa l'API antiga de photutils** (`roundlo`, `xcentroid`); amb
  photutils 3.0.0 encara va, a la 4.0 no.
- **`hip_main.dat`** (53 MB) no és al repositori: a `Estrelles/catalegs/`
  (`prediccio/baixa_catalegs.sh` el torna a baixar de CDS si falta). El `.gz`
  del scratchpad era una pàgina d'error.
- **Cap `load('de440s.bsp')` relatiu**: `comu.efemeride()`.
