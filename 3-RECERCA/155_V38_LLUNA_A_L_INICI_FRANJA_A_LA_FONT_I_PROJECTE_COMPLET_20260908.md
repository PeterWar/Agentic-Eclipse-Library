# 155 — V38: la Lluna a l'inici, la franja de l'oest mesurada a la font (és cromosfera, no un artefacte de 10×), i el projecte complet (08-09-2026, nit)

Ordre de Pere, en tres temps: (1) «el que és maco és tenir tota la protuberància visible, no pots treure aquests artefactes d'alguna manera? potser interpolant?»; (2) «Idealment vull la flamarada de l'esquerra ben visible, les miniflamarades de la dreta visibles, i un forat on hi pugui cabre bé l'earthshine de la Lluna sense alterar la seva forma»; (3) «fem A aplicant les correccions necessàries per treure els artefactes, però anota'm D com a possible millora. Un cop acabada l'A, fes la V38 ja amb totes les capes que havíem eliminat (estrelles, earthshine, part linealitzada, part no linealitzada…) muntat tot en un projecte.»

Codi: `research/tools/v38_20260908/` (a1_franja_font, a2_cura_roi, b2_recomposicio, b3_fusio, b4a, b4b, b4c_purs, b4d, c3_portes, c4_projecte_complet, c5_rebut, d1_autoritat). Rebuts: `output/v38_20260908/4-rebuts/`. Vistes: `output/v38_20260908/lliurables/vistes/` (còpia a `IA/output/v38_20260908/`).

## 1. La geometria, mesurada (rectifica el 154 §4 i el CLAUDE.md: el forat NO és la «unió»)

- **El forat del compost és la INTERSECCIÓ de les posicions de la Lluna** (un píxel té dada si ALGUN fotograma el va veure; la unió de les observacions vàlides = intersecció dels discos). És una llentia de **1,005 R☉ (az −175° i +35°) a 1,046 R☉ (az −75°)**, mesurada al suport de la V36 per sectors de 10°. Amb la guarda de 2 px de la màscara lunar per fotograma, coincideix exactament amb `R_L + 2 + min_i(o_i·û)`.
- **La Lluna fa 455,5 px de radi al llenç (1,034 R☉; `R_lluna_px` del run) i es va moure 28,5 px (≈ 61″) durant els 103 s de fotogrames**: centre a (+14,8, +0,9) px del Sol a t = 15 s (az +3°) i a (−12,4, −7,6) a t = 118 s (az −148°); a mig camí (t 69 s) a (−0,7, −4,0).
- **La flamarada de l'oest (az −175…−120°, > 125 px d'alçada) només la van veure els fotogrames de l'INICI** (la Lluna era a l'est: el seu limbe oest arribava a 1,005) i **les miniflamarades del SE (az +31…+50°, fins a 60 px, les petites 10–20 px) només els del FINAL**. Són exactament oposades sobre l'eix del moviment: **en cap instant les dues bases van estar destapades alhora**. No és cap impossibilitat nostra: és de l'eclipsi. Vistes: `output/v37fc_20260908/lliurables/vistes/LLUNA_tres_instants_*.png` (la Lluna de mida real a tres instants sobre la base).
- Opcions donades a Pere (Lluna sempre rodona, de mida real, a una posició real; el compost no es retalla, el disc va a sobre): **A inici** (flamarada sencera; minis tapades fins a 1,061), **B final** (minis senceres; base de la flamarada tapada fins a 1,065, 25–27 px), **C mig** (13–16 px a l'oest, ~10 al SE), **D dos instants declarats** (A + la corona de la franja del SE dibuixada sobre la vora del disc). **Pere: A, i la D anotada com a millora possible** (CLAUDE.md, bloc de tasca futura).

## 2. La franja de l'oest a la FONT, fotograma a fotograma (A1/A2)

Recomposició de la corona interior (caixa ±1,13 R☉) fotograma a fotograma (67 fotogrames Vixen, G i RGB, resolució completa, pesos, k, camps φ i offsets com al B2) amb la distància de cada píxel a la vora lunar MODELADA de cada fotograma. Reproducció de `vixen_total_v36` al ROI: p99,9 de la diferència relativa 2,2·10⁻⁴ (guardarail 12: primer es reprodueix, després es canvia).

**El que la franja és de veritat** (anells d'1 px, sector W az 150–210°):

| anell (R☉) | fotogrames | pes total | mediana ln | salt respecte de l'anell anterior |
|---|---|---|---|---|
| 1,005 | 2,3 (tots 1/3200 s, t 15–17 s) | 0,0002 | +14,71 | — |
| 1,008 | 5,7 | 0,0011 | +13,64 | −107 % |
| 1,010 | 9,5 | 0,006 | +12,93 | −72 % |
| 1,012 | 12,6 | 0,028 | +12,52 | −41 % |
| 1,015 | 15,0 | 0,068 | +12,41 | −11 % |
| 1,017–1,044 | 15,5–18 | 0,11–0,21 | pendent −2,4 %/px | (tendència natural r⁻⁷) |
| 1,046–1,065 | 20–44 | 0,26–0,76 | | entrada dels fotogrames de mig |
| ≥ 1,07 | 50–53 | 0,8–1,4 | | |

- **Els 3–4 primers anells (1,005–1,012) són la CROMOSFERA i la base de la flamarada**: un 107 %, 72 %, 41 % i 11 % més brillants que la tendència, vistos només per 2–10 fotogrames de 1/3200 s dels primers segons després de C2 (la Lluna encara era a l'est). Dada real i preciosa; al SE passa el mateix amb els últims fotogrames (+95 %, +24 %, +12 %). Els filtres hi reaccionen com a una vora radial molt brusca (la línia fina del NRGF a la vora del forat).
- **El gra de 1,015 a 1,045 és el que els pesos expliquen**: pes 0,11–0,19 contra 0,7–0,8 fora (4–7× menys) → soroll ×2–2,6, **no ×10**. La xifra «gra 7–9 % (10×)» del 154 §1c barrejava els anells cromosfèrics i l'estructura de la flamarada amb el gra: queda RECTIFICADA.
- **No hi ha arcs coherents d'1 px a la franja**: residu del perfil radial respecte de la mediana mòbil de 9 px = 0,0 a 1,015–1,07; coherència azimutal dels anells 456/461/469 px: t = +0,3 / −0,8 / +0,4 (60 sectors d'1°), fracció de sectors amb el mateix signe 0,07–0,08. Els «salts de 5–9 %» que es llegeixen a les primeres diferències són el pendent natural (−2,4 %/px) més soroll: **una primera diferència sobre un perfil amb pendent no és un artefacte** (trampa, §6).
- **Sí que hi ha un dèficit de llum de cada fotograma prop de la SEVA pròpia vora lunar** (ln fotograma/compost net, per classe d'exposició): curts (≤ 1/800) −21 % a 0,5 px, −7 % a 2,5, −3,4 % a 4,5, −1,5 % a 10, −0,6 % a 15; mitjans −4 % a 2,5, −0,6 % a 4,5, 0 a 6; llargs −4 % a 2,5, 0 a 6. És l'ala de dispersió del limbe fosc (la màscara vigent hi posava una guarda de 2 px i declarava «≲ 1,5 %»: als curts és −7 % a 2,5 px). Estable per sectors (W/SE/E/N) dins de ±2 punts. **La posició real del limbe per fotograma coincideix amb la modelada** (creuament de −0,5 ln a +0,6 px de mediana, rang −0,6…+2,5): no és cap error de registre.
- **Nivell per fotograma al limbe (1,00–1,15 R☉, > 6 px de la vora)**: rms 1,15 %, rang −1,8…+2,4 %; els 1/3200 s del final van +2 % i els de l'inici +1 %. Igualar-los NO canvia les mètriques de la franja (només els curts hi són, tots iguals entre ells): no s'aplica (guardarail 12).
- **Prova al ROI (A2)** de la correcció del dèficit (valor × exp(−B_classe(d)), taula mesurada, 0 més enllà de 30 px): residu per classe 0,000 a tota distància; **control nul exacte** (píxels a > 30 px de tota vora: diferència relativa màxima 2·10⁻⁶); les mètriques de gra i arcs de la franja no canvien de manera mesurable (la correcció és de nivell, no de textura). S'ADOPTA com a calibratge de la vora lunar perquè és un biaix mesurat i corregit a l'origen, no com a cura de cap artefacte visible. Guardes més grans (3–8 px) es van provar i REFUSAR: només treuen dada (el forat creix 1,005 → 1,007–1,018) i el que sembla «menys gra» és que desapareixen els anells cromosfèrics.

## 3. Què fa la V38

1. **B2 (Vixen)**: recomposició V36 + `nn *= exp(−B_classe(d))` amb d la distància a la vora lunar modelada del fotograma i B la taula `cau/correccio_vora_lunar.json` (curts/mitjans/llargs; mescla a 0 entre 24 i 30 px). La Sony no es toca (no entra a < 1,9 R☉). Fusió (B3) amb la recepta V35/V36: **lluny de tota vora lunar (r > 1,12) idèntica a la V36 (diferència relativa màxima 3·10⁻⁵)**; a 1,00–1,06 mediana 0,3 %, p99 8,7 %, màxim 9,4 % (els anells de la vora). Suport idèntic.
2. **Filtres amb la recepta V37** (01/02/04/05/06 amb farcit A a l'ACHF; P03/P04/P05 amb farcit B; P01/P02 V36) més **P01b**: NRGF amb μ/σ dels anells parcials del forat extrapolats en ln des dels 40 anells sencers següents (la variant que el 154 va refusar per un «rivet de 5,2 σ»): ara es jutja per azimut (§4): si el rivet clar només és on hi ha cromosfera (W i SE) és senyal, no artefacte. Es lliura com a capa oculta a part perquè Pere triï.
3. **Capes azimutals recuperades**: 03 ACHF azimutal 8-128 (σr 0 i 4) i 07 (σr 8) amb la recepta exacta de la V32 (b4b) sobre la fusió V38.
4. **Projecte COMPLET V38.psb** (42 capes): les 13 capes de Pere (01–12 i 13 Sony >1s), Fons per raig i Estrelles byte a byte; les quatre capes d'earthshine (v2, D87, LROC, V24e) i Reflex **desplaçades (+15, +1) px** = la Lluna a l'INICI (centre mesurat a (+14,8, +0,9) del Sol; error 0,2 px); les dues bases V32 (amb cel, cel/4) conservades ocultes amb el sufix · V32; la base lineal V38; 03 r0/r4/07, 01/02/04/05/06, P01, P01b, P02–P05 (V38); P06–P09 i C01 de la V32 (byte a byte, ocultes, sufix · V32). **Totes les capes de base i de filtre porten màscara nova = fora del disc de la Lluna a l'inici (R 455,5 + 2 px de guarda, rampa de 2 px)**: a l'oest la vora del disc coincideix amb la vora de la dada (la flamarada i la cromosfera queden senceres); al SE/E el disc tapa la franja dels últims fotogrames. Visibles per defecte com a la V32: 12, 11, Earthshine V24e, base V38, 03 r4, 01, 02, Estrelles, Reflex.

## 4. Resultats (C3)

- **Control nul de la fusió**: a r > 1,12 R☉ (més de 35 px de qualsevol vora lunar) la fusió V38 és idèntica a la V36 (diferència relativa màxima 3.6e-05); a 1,00–1,06 la mediana és 0.30 % i el p99 8.4 % (els anells de la vora, on el dèficit corregit era del 4–20 %). Suport idèntic.
- **Rivet a la vora del forat per sector (24), |màx| / |mediana| en σ, abans → V38** (abans = V37; per a les azimutals, V32):

| capa | abans | V38 |
|---|---|---|
| 01 | 2.48 / 1.31 | 2.48 / 1.29 |
| 02 | 2.10 / 1.12 | 2.05 / 1.05 |
| 04 | 3.48 / 1.54 | 3.20 / 1.69 |
| 05 | 2.36 / 1.14 | 2.41 / 1.15 |
| 06 | 2.24 / 1.10 | 2.28 / 1.13 |
| P01 | 1.05 / 0.25 | 1.07 / 0.23 |
| P01x | 1.05 / 0.25 | 1.43 / 0.26 |
| P02 | 0.96 / 0.34 | 0.99 / 0.34 |
| P03 | 0.49 / 0.22 | 0.46 / 0.24 |
| P04 | 0.99 / 0.46 | 0.99 / 0.49 |
| P05 | 1.39 / 0.63 | 1.43 / 0.63 |
| 03r4 | 1.52 / 0.37 | 1.51 / 0.36 |
| 03r0 | 1.38 / 0.40 | 1.35 / 0.39 |
| 07 | 1.16 / 0.36 | 1.14 / 0.34 |

Lectura: la correcció de la vora lunar és un calibratge de nivell de pocs px i no mou els rivets dels filtres (dominats per estructura real: flamarada, cromosfera); el que canvia la V38 al limbe és la LLUNA (on és i què tapa), no la textura. Les azimutals 03/07 regenerades sobre la fusió V38 donen els mateixos números que a la V32 (H1 0,010/0,006/…; geometria azimutal pic a 0°).
- **P01 (estadístiques dels anells parcials, recepta V36/V37) contra P01b (μ/σ extrapolats), rivet per azimut a la vora del forat (72 sectors de 5°)**: P01 dona **−0.67 σ on hi ha cromosfera** (W i SE: la «banda apagada» del 154 és exactament aquí: les estadístiques dels anells parcials, inflades per la cromosfera i la flamarada, apaguen la corona normal del costat) i -0.14 σ a la resta del contorn; P01b dona **+0.79 σ (màx +1.35) on hi ha cromosfera** —el signe correcte: la cromosfera és més brillant que la corona mitjana del seu radi, i això és el «5,2 σ» que el 154 va refusar— però també +0.24 σ de mediana (p95 +0.92) a la resta del contorn: l'extrapolació lineal en r de ln μ subestima el perfil (que és convex, ~r⁻⁷) als anells més interiors. **Es lliuren les dues** (P01 per defecte, P01b oculta); la millora evident és extrapolar en ln r (llei de potència), no en r: anotada, no feta.

Fitxer, verificació i porta de Photoshop: `V38_REBUT.md` al costat del PSB (C4).

## 5. Millora possible anotada: l'opció D

Lluna a l'inici (flamarada sencera) + la corona de la franja del SE (dada dels últims fotogrames, 1,005–1,046) dibuixada per SOBRE de la vora del disc perquè les miniflamarades també es vegin. Compost de dos instants: només declarat al rebut. No s'ha fet.

## 6. Trampes d'aquesta ronda

- **«Unió» per «intersecció»**: tres documents (152 §, 153, 154 i el CLAUDE.md) deien «unió de les posicions de la Lluna». El forat és la intersecció (= unió de les observacions). L'error no canviava cap número, però sí el raonament sobre qui veu què.
- **Una primera diferència sobre un perfil amb pendent no és un artefacte**: −7 % contra −2,4 %/px sembla un salt; el residu contra la mediana mòbil i la coherència azimutal (t < 1) diuen que no. Mesura sempre la coherència en azimut abans de dir «arc».
- **La mètrica de gra no pot contenir estructura**: el sector W conté la flamarada; «gra 37 %» era la flamarada. Mesura el gra a sectors sense estructura (SE/E/N) o contra una referència.
- **`sed` sobre àlies de mòdul no arriba a les rutes literals**: `b4c_purs.py` de la V37 llegia la base amb la ruta literal `v36_20260908/cau/base_G_v36.npy`; el primer llançament de la V38 va córrer els operadors purs sobre la base V36 fins que el log ho va destapar (matat i rellançat). Guardarail: abans de córrer una cadena heretada, `grep -n "v3[0-9]_2026"` a tots els scripts i comprova que cada `readbase` apunta a la versió nova.
- **Dependències natives fora del cau**: `purs/nafe_native.dylib`, `sparse_conv.dylib` i `sources/` s'han de copiar a cada directori de versió (el b4c ho asserta byte a byte contra v31_purs).
- **Retalls fora del ROI**: un retall centrat al limbe oest amb ±150 px sobre una caixa de ±1,13 R☉ cau fora del ROI (el limbe és a 44 px de la vora de la caixa) i surt negre. Comprova sempre que el retall és dins de l'array.
