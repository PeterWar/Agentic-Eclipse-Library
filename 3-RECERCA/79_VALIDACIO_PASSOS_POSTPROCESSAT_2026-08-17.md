# Validació dels passos del postprocessat de la corona — abans de fer la skill

*17 d'agost de 2026, vespre. Auditoria de la font viva, no de la memòria.*

## 0. Què he mirat

- `research/71` a `78` sencers i les catorze eines de `research/tools/`
  (`hdr_corona_vixen.py` línia a línia, 2.537 línies).
- Les 27 memòries del projecte i el `CLAUDE.md` (que és **pre-eclipsi**, del 10-08).
- Les dotze sessions de xat de postprocessat, per títol i per cerca de text:
  *Corona postprocessing* i *Astrofalls eclipse processing tutorial* (09-08),
  *Eina de calibratge*, *Adobe connector*, *Masterdarks A7RIIIA*, *Posat al dia
  CODEX* (15-08), *Solar eclipse image alignment algorithms* i *APOD submission*
  (16-08), *Apilat corona solar VIXEN* i *HDR4 corona image stacking* (17-08).
- **Els scratchpads d'aquelles sessions** (`/private/tmp/claude-501/…`), que és
  on viu de veritat una part gran del codi: `ea55df18` (estrelles, placa,
  flats sintètics, 16 GB), `604fa71e` (deflexió i APOD), `8222da38` (diagnòstics
  de l'HDR), `d71d9c5e` (plantilla DNG i JSX de Photoshop), `bd892f38`
  (earthshine i halo).
- Els datasets de `~/Desktop/Eclipse 2026/`, `~/Desktop/HDR4/`, els 56 PDF de
  `Papers Druckmuller/` i els tres PDF d'Astrofalls del Dropbox.
- L'entorn: `~/.venvs/eines-ia-py312`, DNG Converter, exiftool, skyfield.

## 1. Veredicte en una taula

| # | Pas de Pere | Veredicte | En una frase |
|---|---|---|---|
| 0 | Eines Python i DNG Converter | ✅ | Tot hi és (DNG Converter **18.5**, rawpy/libraw, astropy, skyfield+DE440s, opencv, skimage, photutils, tifffile, exiftool 13.55). El drizzle és propi, no cal cap paquet. Dos forats petits al §2. |
| 1 | Deriva de la muntura | ✅ | Mesurada als dos trens per dos camins independents; i s'ha descobert que la corona **no** deriva com les estrelles (0,578 contra 0,610 ″/s). |
| 2 | Plate-solve de les estrelles | ✅ (però el codi és fora del repositori) | Cerca cega + Hipparcos/Tycho-2: 38/38 i 22/24 estrelles, escales, nord, centre solar, punt zero i factor B/B☉ (±10 %, trens al 5 %). |
| 3 | Efemèrides Sol–Lluna al lloc exacte; Astrofalls apila a la Lluna; earthshine | ✅ amb matís | JPL DE440s via skyfield, topocèntric a FINAL 2, validat amb els contactes reals; l'apilat va al **Sol** i el disc lunar s'emmascara. L'earthshine és una pila a part, alineada a la Lluna. |
| 4 | Deriva revisada; refracció i extinció «per homogeneïtzar el fons» | ⚠️ mig | Extinció mesurada de debò (k = 0,402) però **només aplicada a l'HDR4**, no al compost `Corona_HDR_Vixen`. La refracció està mesurada i **no** es corregeix a cap apilat. I el fons no s'homogeneïtza per refracció: el cel de la totalitat fa una V del ±20 % per la vora de l'ombra i s'anivella empíricament. |
| 5 | Desplaçaments relativistes | ⚠️ només forecast | El codi dona σ(ε)=0,53 com a **previsió de Fisher** —1,9σ teòric i 0,9σ Einstein contra Newton sota el model—, no com un ajust d'ε a les dades. **No és cap detecció**; l'APOD és «un retrat». El plate-solve inclou la deflexió de `skyfield.apparent()`. |
| 6 | Filtre de pas alt a partir de Druckmüller | ⚠️ | La recerca es va fer (ACHF, NRGF, FNRGF, MGN, WOW, RHEF, amb correccions), però **el filtre viu no és cap d'aquests**: és `detall_logpolar`, una piràmide de DoG en log-polars, **additiva sobre la pantalla**, sense dividir mai per l'amplitud local. És més a prop d'MGN/WOW que de l'ACHF, que a més no està publicat. |
| 7 | Apilat per exposició amb deriva, Sol–Lluna, fotometria, fons; centroide d'estrelles intacte | ⚠️ | Fet **només al tren Vixen** (68 fotogrames a l'HDR, 26 als nou DNG de l'HDR4). El tren Sony està calibrat, no compost. La frase del centroide no descriu el mètode: l'astrometria es fa sobre fotogrames crus a part, i les estrelles a l'apilat van ser un **problema** (PRNU v1). El fons no canvia per refracció. |
| 8 | Drizzle abans/després de C2, protuberàncies i Nyquist, capa extra, instant de C2 | ⚠️ | Fet el que les dades permeten: gota 2,0 a la reixa del sensor (recupera el submostreig 1,7× de cada pla de Bayer) i capes de protuberàncies a C2 i C3 per excés d'Hα. ⛔ **No hi ha superresolució 2×**: la deriva és una recta i el ditherat és 1-D. Les perles d'abans de C2 **no s'han apilat** (un sol CR3, `572A2956`); el guany de detall que queda és la **deconvolució**. |

## 2. Pas per pas

### Pas 0 — eines ✅

Verificat avui:

- `~/.venvs/eines-ia-py312`: rawpy 0.27 (libraw 0.22, llegeix CR3 de la R6 III i
  ARW de l'A7RIIIA), astropy 8, tifffile, opencv 5, scikit-image 0.26,
  photutils 3, pywavelets, scipy 1.18, **skyfield 1.55 amb `de440s.bsp` a
  `~/.cache/skyfield`**, jplephem, erfa, reproject, matplotlib, pandas.
- `/Applications/Adobe DNG Converter.app` **18.5 (2673)** — el que ha donat el
  blanc 13995 i les matrius de la R6 III; `exiftool` 13.55; Photoshop 27.9 amb
  els JSX provats (`Load Files into Stack`, primera de la llista = capa de dalt).
- **No hi ha** `drizzle` (STScI), `astroalign`, `sep` ni astrometry.net; **no
  fan falta**: el drizzle és propi (`pesos_gota`), la detecció d'estrelles és
  cega i pròpia i el creuament és amb skyfield.

Dos forats: (a) hi ha un `de440s.bsp` de 32 MB **orfe a l'arrel del repositori**
(un `load("de440s.bsp")` relatiu l'ha baixat allà; no s'ha de commitar, i les
eines haurien de carregar sempre `~/.cache/skyfield/de440s.bsp`); (b) `Siril` no
existeix a Homebrew: el contrast independent és el PixInsight de Pere.

### Pas 1 — deriva ✅

- **Vixen/iOptron** (`71`, `75` §5.4): la Lluna a 0,3355 px/s; la muntura a
  **0,610 ± 0,010 ″/s** per les estrelles, direcció −45°, constant, cap salt;
  deriva lliure post-C3 0,689 ″/s = 0,21 de refracció + ~0,48 de muntura (error
  polar ~2°). Les correccions manuals de Pere es veuen als fotogrames.
- **Skywatcher/Sony** (`72`): **dos salts** (+223 px en x cap a C2+35 s, −715 px
  en y cap a C2+50 s; 12′ i 39′) per haver tocat la lent en treure el filtre;
  entre salts, 0,5–1 px; DSC06990 moguda i fora; **0,138° de rotació de camp**
  entre segments (`75`), i les estrelles van retrobar el salt soles.
- El número que mana per apilar corona **no és cap dels dos**: la corona va a
  **0,578 ″/s** (dos camins al 0,3 %, `76` §2) perquè la muntura anava a taxa
  solar; alinear amb el número estel·lar l'hauria escombrada 3,4 px.
- Trampes pagades i documentades (`71` §3): matched filter de disc fosc,
  correlació prop del Sol ancorada al **flare fix al sensor**, plantilla
  estàtica, signe de `ndimage.shift`. ⚠️ `mesura_deriva_v2.py` és el correlador
  de pegats d'aquella trampa; la deriva bona surt del tancament limbe +
  efemèrides i de les parcials.

### Pas 2 — plate-solve ✅ (codi fora del repositori)

- Mètode (`75` §5, `Estrelles/LLEGEIX-ME.md`): pla verd cru, pedestal real,
  fons de corona per mediana en blocs, detecció sobre el residu, falsos positius
  fora (més d'un fotograma, mateixa posició de cel, també a R i B); predicció i
  detecció fetes per agents separats; creuament després. Prova geomètrica:
  totes es mouen amb el cel, no amb el Sol.
- Resultat: model lineal + terme r³ **en marc horitzontal refractat**. Sony
  38/38, 0,54 px, **3,2020 ″/px** (−1 % del 3,234 lunar: discrepància oberta),
  nord PA 90,27°, Sol (3894,7, 2768,7); R6 22/24, 0,32 px, **2,1495 ″/px**, PA
  57,19°, Sol (3570,8, 2267,1). ZP +14,17/+14,21; B/B☉ = 1,134·10⁻¹¹ i
  2,772·10⁻¹¹ per ADU/s (±10 %, trens al 5 %). Cel 9,3 mag/arcsec² a 8 R☉.
- Regal: eix nord lunar astromètric 71,97° contra 71,5° del LROC → 0,47°.
- ⛔ **On és el codi**: al repositori només hi ha `Estrelles/mascara_estrelles.py`
  (dibuixa, no resol). El detector, el creuament, la placa i la fotometria són
  al scratchpad `ea55df18` (`estrelles.py`, `sony_stars/`, `combina.py`,
  `hip_main.dat`, `tyc2.tsv`). **Un reinici del Mac ho pot esborrar.**

### Pas 3 — efemèrides, Astrofalls i earthshine ✅ amb matís

- «Dades de la NASA» = **JPL DE440s** carregat amb skyfield, observador
  `wgs84.latlon(42.299407, −5.02503, 798 m)`; taxa Lluna–Sol topocèntrica
  **0,5905 ″/s a PA 118°** (2,8 px en 10,3 s al Vixen). Validat amb les imatges:
  C2 real −1,0 s i C3 +102,7 s del predit → 103,7 s. Abans, per als contactes,
  ja s'havia contrastat amb Horizons i l'IMCCE (ΔT a 0,09 s).
- Astrofalls: cert, el seu tutorial alinea fotograma a fotograma **al disc
  lunar** i realça amb el *radial/tangential HPF* de Photoshop. En 100 s la Lluna
  es mou 61″ = **28 px (Vixen) i 19 px (Sony)** respecte de la corona: alinear a
  la Lluna escombra la corona. El projecte fa el contrari: **registre al Sol**
  (model lineal de centre solar = limbe lunar mesurat − efemèride, ancorat a la
  placa estel·lar; correlació de fase només com a QA), i el disc lunar de cada
  fotograma s'emmascara. I `73` §2.1 refusa el radial blur de Photoshop: cec a
  les estructures tangencials i canvia la fase.
- Earthshine: **fet** (`72` §4-6, `Earthshine_FINAL/`): pila Sony 2×8 s
  alineada al limbe, model físic de halo (dos nuclis d'ales de PSF sobre l'HDR
  de la corona real + pla de cel), validat **fora de mostra** contra LROC WAC
  (r = 0,68 / 0,73); Sony contra Vixen r = 0,89. Producte = **luminància** (el
  color no és fiable). Pendent: fotometria absoluta (degenerada amb el vel) i
  posar-lo **dins** l'HDR de corona (el disc de `Corona_HDR_Vixen` és buit).
- Matís de vocabulari: la skill ha de dir «efemèride JPL DE440s topocèntrica»,
  no «dades de la NASA»; i el que fa el registre és la **mesura al limbe**, no
  l'efemèride, que en fa la comprovació.

### Pas 4 — deriva revisada, refracció, extinció ⚠️ mig

- Deriva revisada: sí (`75` §5.4, `76` §2, `78` §1: model de centre solar bo a
  ≤ 0,09 px als 17 parells de l'HDR4).
- **Extinció**: la mesura per estrelles (0,416 i 0,723 mag/X, 5σ de
  diferència) està **contaminada pel vinyetatge** i no val (`75`). La bona és la
  diferencial de dins la totalitat: **k = 0,402 ± 0,036 mag/X**, la corona baixa
  un 5,5 % de C2 a C3 (`78` §3). ⛔ Només s'aplica a l'**HDR4**
  (`apila_hdr4_vixen.py`, X de Kasten-Young, normalitzat a C2+8,4 s). Al compost
  `Corona_HDR_Vixen` **no hi ha cap correcció d'extinció** i el 78 la deixa
  PENDENT (i rectifica el 76 §5 bis, que ho havia atribuït tot al cel).
- **Refracció**: mesurada (335″ total; compressió vertical 0,77–0,80 %;
  dispersió R–B **3,08″ a PA 170°**) i feta servir **només a la placa** (marc
  alt/az refractat). Cap apilat la corregeix: `78` §2 estima 0,3–0,9 px de
  refracció diferencial i 0,1–0,5 px de rotació sobre 81 s i ho deixa com a
  translació pura. Alinear R/G/B pels 3,08″ portaria la composició de 5,46 a
  4,97″ (`75`) i tampoc s'ha aplicat.
- **El fons**: el que s'homogeneïtza és el **cel de la totalitat**, que fa una V
  509 → 335 → 491 ADU/s (±20 %) perquè prop de C2 i C3 s'és a tocar de la vora
  de l'ombra; s'anivella per fotograma (mediana a 4,2–5,1 R☉) i sense això
  surten arcs concèntrics a les fronteres de saturació. Això **no** és
  refracció.

### Pas 5 — relativitat ⚠️ forecast, no detecció

- Fet a `77` i a l'APOD: la geometria prediu per a HIP 46345 (2,65 R☉)
  0,66″ = 0,31 px de deflexió, i el soroll dona **σ(ε) = 0,53 com a previsió
  de Fisher**. El 1,9σ i el 0,9σ Einstein–Newton són sensibilitats teòriques,
  no un ajust d'ε ni una detecció. El pla del 2027 (`77`) diu banda honesta
  5–10 % i que el que mana és l'altura del Sol.
- Matís correcte de Pere: skyfield `apparent()` **ja aplica** la deflexió, o
  sigui que la placa dona per suposada la relativitat. El `deflexio.py`
  preservat construeix la matriu de disseny i propaga el rms, però **no resol
  ε sobre residus observats contra un catàleg sense deflexió**. Les referències
  antigues a un ajust separat amb `fit.py` no tenen un rebut preservat que
  demostri una detecció.
- Per a la skill de corona: és un producte **a part** (astrometria), no una
  etapa del postprocessat de la corona. Recomano no ficar-lo dins.

### Pas 6 — el filtre de pas alt ⚠️

- La recerca (`73`) és sòlida i té set correccions que manen: l'ACHF viu no
  està publicat i el de la tesi és el predecessor; el FNRGF de l'ApJ 2011 té
  l'equació de soroll repudiada per l'autora (sumar, no restar) i una prova
  unitària falsa; ordre recomanat **WOW > MGN > RHEF > FNRGF > ACHF**.
- El que hi ha **implementat** (`hdr_corona_vixen.py foto/passalt`) no és cap
  d'aquests: `detall_logpolar` = bandes DoG **en graus** (log-polars, escalen
  amb el radi), fons de Fourier m ≤ 4, encongiment de Wiener amb el soroll
  mesurat per banda i radi, guanys declarats per banda, i **`t·exp(D)` sobre la
  pantalla** (després de la corba de to). El primer intent (dividir per la
  desviació local, tipus MGN d'arctan) es va retirar perquè igualava el
  contrast a tots els radis (jerarquia real 124:1 → 2,7:1) i fabricava trama.
- La capa `PASSALT` (gris 50 % + D) per a Photoshop és el mateix camp D.
- Coses que la skill ha de codificar: la corba es calibra sobre L sense
  realçar; el detall va sobre la pantalla; test d'anell **per sectors** i sobre
  D nu (residu ≤ 0,15 %); estimador de soroll emmascarat + MAD; validesa =
  caixa RETALL, «finit» no vol dir vàlid; mai el radial blur de Photoshop.

### Pas 7 — l'apilat ⚠️

- **Vixen, fet**: `Corona_HDR_Vixen` (68 fotogrames, 15 exposicions, 15,0 EV,
  gota 2,0, pesos `t²/(S/g+RN²)`, sostre 85 %, anivellament del cel, PRNU v2,
  masters per mitjana amb el pedestal a dins) i **HDR4** (nou DNG lineals amb
  els 26 fotogrames de la mateixa exposició, geometria comuna, extinció,
  fons comú, disc de la referència). Validació: perfil K+F de manual
  (3,3·10⁻⁶ B☉ a 1,02 R☉, 1,0·10⁻⁹ a 5), continuïtat 0,02/0,24 %.
- **Sony, no fet**: 194 ARW calibrats (`300mm/calibrated/`) i prou. Té
  dificultats pròpies: tres segments per dos salts, rotació 0,138°, cua de 33
  imatges, i **l'A7RIIIA filtra espacialment el RAW als 8 s** (autocorrelació
  +0,42): l'apilat hi guanya menys de √N. És el que falta per al criteri
  decisiu del G5 (dos trens dins 0,25 EV a 1,5–3,5 R☉).
- «Sense moure el centroide de les estrelles»: no és el que passa. L'apilat es
  registra a la corona; les estrelles hi surten com a traces (0,04 ″/s del Sol
  respecte del fons + res, o sigui < 2 px en tota la totalitat), i **el mapa de
  PRNU v1 les va absorbir** i deixava clots al costat de cada estrella (−10 %
  del pic), refet amb màscara. L'astrometria i la deflexió es van mesurar sobre
  **fotogrames crus, a part**, no sobre l'HDR. La regla bona: *l'HDR no és
  font d'astrometria; l'astrometria no depèn de l'HDR.*
- «Canvi de llum de fons per la refracció»: és per la geometria de l'ombra
  (vegeu pas 4).
- ⚠️ Inconsistència de codi que cap document comenta: `anivella_fons` fa
  servir `escala_rel` i el pes/valor de `hdr` no; i les dues eines posen el
  centre amb una convenció de mig píxel diferent (≤ 0,5 px de «Sol al centre»).

### Pas 8 — drizzle, protuberàncies, C2 ⚠️

- Fet (`78` §9): ràfegues de 1/3200 (**9 en 5,2 s just després de C2**, 17 en
  10,4 s a C3) i trios tardans (1/2000, 1/500, 1/125), gota 2,0, geometria
  comuna, disc cenyit; el soroll del pla R baixa ÷2,8 i la protuberància surt
  amb el pla R mostrejat a la reixa del sensor. I capes per a Photoshop
  (`capa_prot_C2|C3*.tif`) per **excés d'Hα** (E = R − ρG), no per brillantor.
- ⛔ **No hi ha drizzle 2× ni gota < 2,0**: la muntura deriva en línia recta,
  el ditherat és 1-D i qualsevol gota més petita fa escaquer (mesurat: 5.620×
  la potència mitjana amb 1,70). El detall que queda per guanyar és
  **deconvolució** (PSF ben mostrejada, S/N 257:1: la limita la PSF, no els
  fotons). ⚠️ El drizzle **no canvia el FWHM** (5,8″ Vixen); recupera el
  contrast que s'aliasava.
- «Immediatament abans i després de C2»: els apilats de protuberàncies són
  **després** de C2 (0,6–11,6 s) i al voltant de C3. **Els 56 fotogrames de fora
  de la totalitat, amb les perles, no s'han apilat** (`76` §8.5); les perles al
  Prototip 1 i a l'HDR4 són **un sol CR3**, `572A2956` (~C2−0,75 s).
- L'instant: sí, **C2** és el concepte del Prototip 1 (Sony 8 s descentrat per
  la corona externa i l'earthshine; Vixen per la interior, protuberàncies i
  perles), però el prototip és a Photoshop en no lineal i **s'ha de refer sobre
  el pipeline lineal**.

## 3. Els passos que falten (per ordre d'importància)

1. **Rescatar el codi que només viu al scratchpad** (placa, deflexió, halo
   sense LROC, diagnòstics de l'HDR, plantilla DNG, JSX). És a `/private/tmp` i
   les eines de `research/tools/` en depenen amb rutes escrites a pèl (i rutes
   antigues de l'Escriptori). Condició prèvia de qualsevol skill.
2. **Calibratge** com a etapa explícita —Pere no l'ha llistat i és la meitat
   de la feina feta—: masters per **mitjana** (no mediana), pedestal real (512
   Sony, 511,5 R6; el negre de libraw és fals), PRNU v2 amb màscara
   d'estrelles, saturació (pou **16382**, sostre 85 % = 13.490 sobre el fosc,
   Adobe blanc 13995), guanys 5,08/3,41 e⁻/ADU i dos modes de lectura de la R6,
   **cap desbayerat**, cap `clip(0)`, cap balanç, blau de la R6 exclòs dels
   pesos.
3. **Procedència (G0)**: inventari amb SHA-256 de tot (3.650 fitxers; només 322
   coberts), la cua `572A3152–3177` sense explicació, el 6D sense auditar,
   originals mai tocats.
4. **Refer `Corona_HDR_Vixen` amb la normalització d'extinció** (declarat
   PENDENT a `78`) i tancar el calibratge relatiu d'exposicions (terme additiu
   per radi i temps).
5. **HDR del tren Sony**: segments, rotació, alt/az; és el que permet el
   criteri del G5 i el que posa la corona externa i l'earthshine a la foto.
6. **Model de halo (G3) aplicat a la corona**, disc lunar amb el pes −1 de
   Druckmüller (ara és un forat de 112.699 píxels) i l'**earthshine dins
   l'HDR**. La validació del halo ha de venir de la fotosfera filtrada de la
   parcial, no d'estrelles (límit físic).
7. **Deconvolució (D3)** per canal (R6: 4,8/5,8/6,7″; Sony 8,3″ acromàtica),
   amb registre de canals (3,08″).
8. **Validació externa i QA per porta**: LASCO C2/C3 i K-Cor del mateix dia
   (G7c), trens dins 0,25 EV, mapa de variància al costat de cada producte, test
   d'anell per sectors, continuïtat, perfil K+F.
9. **Composició final lineal + revelat declarat**: corba del sketch, detall
   additiu, color per tres ancoratges, earthshine real, capa de
   protuberàncies, perles de C2 → el Prototip 1 refet, i l'`_FINAL.tif` com a
   variant etiquetada.
10. **Els 56 fotogrames de fora de la totalitat** (contactes i perles) com a
    pila pròpia; i el 6D (3.062 CR2) com a registre del cel (G7b).
11. **Flats**: `75` diu que no calen per a la imatge (Sony −0,21 EV via `.lcp`,
    Vixen < 0,15 EV) però sense flats extinció, vinyetatge i pla de cel del
    halo no se separen; decisió a prendre (aplicar el polinomi `.lcp` en lineal
    a la Sony és el mínim).
12. **Documentació**: `research/75`, `77` i sis eines estan **untracked**;
    `CLAUDE.md` no sap res de l'eclipsi; `de440s.bsp` i `sortida.png` orfes a
    l'arrel.

## 4. El que la skill hauria de ser (proposta, per confirmar)

Una skill de projecte, `postprocessat-corona`, amb el pipeline **Vixen** com a
camí provat (deu minuts d'extrem a extrem) i el Sony com a etapa oberta:

```text
0 procedència    inventari SHA-256, no toca originals
1 calibratge     masters (mitjana) · PRNU v2 · pedestal real · sense desbayerar
2 geometria      EXIF · limbe lunar · efemèride DE440s · ancoratge a la placa
3 registre       model de centre solar; correlació de fase només com a QA
4 extinció+cel   k = 0,402 per massa d'aire · anivellament a fons comú
5 hdr            drizzle gota 2,0 · pesos òptims · sostre 85 % · variància
6 apilats/DNG    HDR4: un DNG lineal per exposició (blanc 13995) · protuberàncies
7 vis/foto       corba sketch · detall_logpolar · color · earthshine · passalt
8 qa             perfil K+F · continuïtat · test d'anell per sectors · trens
9 muntatge       Photoshop JSX (ordre de capes provat)
```

Fora de la skill (productes a part): plate-solve i calibratge absolut,
deflexió/APOD, earthshine (que la skill **consumeix** com a entrada).

## 5. Què s'ha fet a la mateixa sessió (17-08, vespre)

- **La skill existeix, com a esborrany v0**: `.claude/skills/postprocessat-corona/`.
  `SKILL.md` (les tres regles, l'entorn, el pipeline en onze etapes amb l'ordre
  de cada una, les portes de QA, l'estat i el pendent), `references/
  pipeline_vixen.md` (cada etapa amb entrades, sortides, paràmetres i variables
  d'entorn), `references/constants.md` (tots els números mesurats amb la font),
  `references/trampes.md` (tot el que ja s'ha pagat una vegada), i dos scripts:
  `comprova_entorn.py` (detecta l'intèrpret bo sense escriure'n cap a pèl,
  comprova binaris, efemèride, dades i productes; només lectura) i
  `pipeline_vixen.sh` (encadena `masters → prnu → geometria → deriva → escala →
  hdr → vis → tiff → foto → passalt → hdr4`, amb `--nomes-mostra`). El
  comprovador dona «Tot a punt» i l'orquestrador ensenya les tretze ordres.
- **El codi dels scratchpads és al repositori**:
  `research/tools/rescat_scratchpad_2026-08-17/` (593 fitxers de text, 6 MB,
  `ORIGEN.md` amb la taula de procedència). No està revisat ni promogut: és la
  còpia de seguretat.
- **La skill s'ha provat d'extrem a extrem sobre les dades reals, sense tocar
  cap producte viu.** Les dues eines accepten ara un directori de sortida per
  variable d'entorn (`CORONA_OUT` a `hdr_corona_vixen.py`, `HDR4_OUT` a
  `apila_hdr4_vixen.py`; canvi d'una línia, compatible cap enrere) i
  `pipeline_vixen.sh --prova DIR` ho embolcalla. Passada del 17-08 a
  `~/Desktop/Eclipse 2026/_prova_skill/` (geometria → deriva → escala → hdr →
  vis → tiff → foto → passalt → hdr4): **14 min 43 s, sortida 0, 2,0 GB**;
  perfil K+F reproduït (3,18·10⁻⁶ B☉ a 1,02 R☉ … 1,03·10⁻⁹ a 5,0),
  continuïtat 0,01 %/0,15 %, deriva de la corona 0,579 ″/s (residu 0,11/0,10
  px), manifest a ≤ 0,01 px del viu (que és del 16-08, anterior al PRNU v2),
  nou DNG de l'HDR4 amb registre ≤ 0,18 px i k = 0,44 ± 0,12 sobre 17
  parelles. L'etapa `earthshine` no era a la llista i `foto` va avisar: ja és
  al pipeline per defecte. La carpeta `_prova_skill/` es pot esborrar.
- **Pere va demanar (17-08, vespre) que l'astrometria i la deflexió entressin
  a la skill, i hi són.** Un workflow de sis lectors va fer el mapa del codi
  rescatat (troballa: la placa, el creuament i el calibratge absolut viuen a
  `xmatch/`, no a l'arrel del rescat; `combina.py`/`fit.py`/`final.py` de
  l'arrel són predicció i PTC) i sis promotors el van portar a
  `research/tools/astrometria/` (`comu.py` amb rutes per variables d'entorn i
  totes les constants; `prediccio/ sony/ vixen/ xmatch/ esceptic/ deflexio/
  apod/`; `pipeline_estrelles.sh --prova DIR`; `test_acceptacio.py`;
  `MAPA.md`), sense canviar cap algorisme, llindar, llavor ni sostre —l'única
  correcció ordenada és el terme de color −0,653·c a `corona2.py`, que
  imprimeix els factors amb i sense—. **Provat d'un sol cop des dels RAW i els
  darks**: 11 min 05 s, sortida 0, **22/22** números d'acceptació (38/24 fonts,
  38/38 i 22/24, 3,2020/2,1495 ″/px, PA 90,27/57,19, ZP 14,167/14,205,
  B/B☉ 1,135/2,771·10⁻¹¹, quocient 0,952, ales 13/30 px, forecast de Fisher
  σ(ε) 0,53, HIP 46345 0,660″ predit), amb `catalog_sony.txt`,
  `catalog_vixen_fonts.csv`, `noise.npy`,
  `retalls_estrelles.json`, `_net.png`, mp4 i gif **byte a byte idèntics** als
  del 16-08. Referència a la skill: `references/astrometria_i_deflexio.md`.
  Catàlegs (Hipparcos 53 MB, Tycho-2) a `~/Desktop/Eclipse 2026/Estrelles/
  catalegs/`; fonts de l'APOD a `APOD/_fonts_apod_scratchpad_16-08/`.
- Dues coses que la promoció ha destapat: el 0,625 ± 0,042 ″/s de `research/75`
  §5.4 (traços) no el reprodueix cap dels dos scripts conservats
  (`fitpsf.py` 0,677 ± 0,051, `fit2.py` 0,545 ± 0,023) tot i entrades
  bit-idèntiques —el catàleg no en depèn—; i el guany que la cadena Sony porta a
  dins és 3,323 e⁻/ADU (`gain.py`) i no el 3,41 publicat: divergència
  documentada, no reconciliada.
- Carpetes de prova, esborrables: `~/Desktop/Eclipse 2026/_prova_skill/`
  (17 GB: corona 2 GB + intermedis d'estrelles de la promoció) i
  `_prova_skill_estrelles/` (15 GB: la passada sencera d'un sol cop).
- Pendent de Pere: confirmar o esmenar la llista del §3.
