# 80 — Encaix de la capa Sony 300 mm al compost de Photoshop, i les estrelles mogudes

18 d'agost de 2026, matinada. Sessió de postprocessat sobre el document de Pere
`~/Downloads/NoEncaixa.tif` («només em queda per encaixar una capa que no
encaixa i per molt que jugo amb els filtres de desenfoc gaussià sempre em queda
un gradient circular concèntric al sol de diferents colors»). Lliurables i el
detall d'ús a `~/Downloads/Encaixada_2026-08-18/LLEGEIX-ME.md`; codi a
`tools/encaix_sony/`.

## 1. Què hi havia al document

Photoshop 27.9, Display P3, 6748×4553 (la reixa de 6960×4640 retallada
`[87:4640, 143:6891]`, com diu el `LLEGEIX-ME` de `Corona_HDR_Vixen`; Sol a
(3420,9, 2187,7)). Dues capes al tag 37724 (little-endian, longituds PSB, **dades
de canal big-endian**): la Vixen a baix (`03_1s_572A2978_apilat2.dng`, aplanat
del seu HDR4 amb el realçat) i la Sony a dalt (`Capa 1`, 15660×14452 de bbox,
la A7RIIIA a 2× posada al 74,48 % i −33,2°, amb màscara). Reconstrucció exacta
de l'aplanat: `vixen·(1−m) + sony·m`, diferència 3·10⁻⁵.

## 2. El diagnòstic: no era la màscara

Perfils per canal (mediana per anell de 0,05 R☉):

- la Sony és **cremada** fins a 3,25 R☉ en R (2,9 G, 2,4 B) de mediana i fins a
  **3,75 R☉** als plomalls brillants; entre 2,5 i 3,9 R☉ hi ha el rim de saturació
  per canals (R/G = 1,6 a 3,3 R☉ contra 1,1 a la Vixen): taronja i verd;
- fora del cremat és **2–3× més clara** que la Vixen al mateix radi (0,57/0,43/0,34
  contra 0,18/0,19/0,22 a 4 R☉) i **càlida on la Vixen és blava**;
- la màscara de Pere val 0,02–0,07 dins de 2,5 R☉ (un vel blanc del 2–9 % sobre la
  corona interior), 0,5 a 3,7 R☉ i 0,95 a 5.

Amb això, qualsevol màscara suau produeix un anell de colors on barreja: el
problema és la capa, no la ploma.

## 3. El mètode

1. **LUT per canal per aparellament de quantils** Sony → Vixen a la zona vàlida
   (cap canal > 0,70, r > 3,3 R☉, 50 px d'erosió). Posa la Sony al to i al color de
   la Vixen.
2. **Residu de baixa freqüència** `E = LUT(sony) − vixen`, gaussiana σ = 80 px per
   convolució normalitzada sobre la zona vàlida, restat. Tot el que és més gros que
   ~200 px (7′) és la Vixen; la Sony aporta el que és més fi. Primer es va provar un
   estimador polar (anells de 0,05 R☉ × sectors de 5° suavitzats 30°): deixava
   ±0,01–0,02 de taques a 200–500 px i tota la vora de dalt (l'enfosquiment de vora
   de la Vixen); el cartesià ho resol.
3. **Dins la zona cremada la capa és la Vixen** (`w` = smoothstep de la distància a
   la vora de la zona vàlida, 0 → 1 en 120 px). Fit − Vixen ≤ 0,07 % per anell de
   0,05 R☉ entre 3 i 4,2 R☉; per sector (±25° a l'esquerra) ≤ 0,1 %.
4. **Estrelles**: totes les traces són iguals (σ major 3,3–3,9 px, σ menor 1,6–1,7,
   angle 47 ± 3° al llenç → traça ≈ 12 px = 25″ ≈ 8 px natius Sony). Ajust
   gaussià el·líptic + fons per font; s'accepta si direcció ±12° de la global (les 8
   més brillants, ponderades per S/N), 2,2 ≤ σa ≤ 5,5, 1,2 < σb < 2,4, S/N ≥ 8 i
   residu de l'ajust acceptable (el llindar creix amb la brillantor: la gaussiana és
   un model aproximat de traça). Es resta l'el·líptica per canal i s'hi posa una
   rodona (σ = σb) del mateix flux al mateix centroide. 31 al domini estès (15 dins
   el llenç); les mateixes 4 brillants amb S/N 16–55. El raig recte de dalt a
   l'esquerra és a les dues càmeres al mateix PA: no és de la Sony i no s'ha tocat.
5. **Detall exterior**: bandes DoG en unitats angulars (12–35, 35–100, 100–280,
   280–600 px = 26″–21′) sobre la luminància del compost encaixat, al **domini
   estès** (la Sony arriba 550/250/600/300 px més enllà del llenç, o sigui que el
   DoG no veu les vores) i sense el perfil radial; coring a 1,5 σ (MAD al cel);
   rampa radial 3,2 → 4,4 R☉; estrelles fora; **component d'anell = 0** (mitjana per
   anell de 0,05 R☉ sobre tots els píxels on s'aplica). SUAU ×1,5/3/2,5/0; FORT
   ×3/6/5/2. Test d'anell (3,2–5,5 R☉, anells complets): ≤ 0,03 % (llindar 0,15 %).

## 4. Tres coses que van costar

- **La component d'anell del detall no és zero per construcció.** El coring és
  simètric però la corona té cues positives: la mitjana per anell del detall sortia
  +1,6 a +1,9 %. I si la mitjana es treu amb pesos que no són exactament els píxels
  on s'aplica (vora del llenç, zona cremada), torna a sortir +0,3–0,7 %. S'ha de
  restar la mitjana per anell **sobre tots els píxels on s'aplica**, després del
  coring i dels guanys.
- **L'enfosquiment de vora de la capa Vixen.** Les últimes 300 files de dalt cauen
  de 0,16 a 0,074 (la meitat), la dreta de 0,10 a 0,05 en 250 columnes; la Sony hi
  té el cel pla. No és cel: és del processat. Un DoG de 280–600 px hi veu una banda
  de −0,04 (un 25 %) i el converteix en un marc. Solució: el detall es calcula al
  domini estès i sense perfil radial, i la capa té dues variants (segueix la Vixen /
  vores netes, amb el residu estimat a > 300 px de la vora i extrapolat).
- **El binari `binary_opening` de scipy** posa a False la vora de l'array (erosió
  amb `border_value=0`): en el domini estès això feia la capa negra a les vores.
  Erosió amb `border_value=1` i dilatació a part.

## 5. Què aporta de veritat la Sony aquí, i què no

- Al llenç actual, poc detall nou: a 25–70 px la Vixen (que ja porta el realçat de
  Pere) té ~6× més amplitud que la Sony passada per la LUT, correlació 0,5–0,7.
  El realçat exterior s'ha fet sobre el compost encaixat, no sobre la Sony sola.
- El seu **camp** amb aquesta col·locació (−33,2°) només arriba a 550/250/600/300
  px més enllà del llenç com a rectangle ple; els cantons girats queden fora.
- Sí que aporta: un cel pla a les vores (contra l'enfosquiment de la Vixen) i les
  estrelles.

## 6. Pendent

- Refer-ho quan la Sony estigui composta de debò (l'HDR del tren Sony, `79` §3
  punt 2): llavors la LUT hauria de sortir gairebé lineal i el residu, petit.
- Si Pere vol l'earthshine de la Sony al disc, és a `Earthshine_FINAL/`: la capa
  encaixada hi porta la Vixen.

## 7. Segona ronda: el halo que quedava, i l'apilat de la Sony ≥ 1 s

**El halo concèntric de 2,7–4 R☉ que Pere veia al SUAU és de la capa Vixen** (el SUAU
hi coincideix a ≤ 0,1 % per anell) i **no és de luminància**: el perfil azimutal és a
≤ 1,5 % d'una Hermite log-log entre 2,4 i 5,6 R☉, i forçar-hi un pendent monòton
(regressió isotònica) canvia < 0,5 %. És el creuament de color: corona càlida
((R−B)/L = +0,36 a 2,5 R☉) → gris a 3,3 → cel blau (−0,30 a 4,5, −0,40 a 5,5), sobre la
meseta on la corona iguala el cel. Tractament: croma × CM i luminància × G, rampa
smoothstep 2,6 → 4,5 R☉ i constant enllà (monòton: cap anell nou). A: 0,35/0,95
(recomanada), B: 0,20/0,90, C: 0,50/1,00.

**Apilat de la Sony ≥ 1 s** (pendent núm. 2 de `79` §3, en la seva versió mínima): els 7
fotogrames de `comu.SONY['fotogrames']` (06984 2 s, 06985 1 s, 06987 8 s, 06991 1 s,
06993 8 s, 06996 2 s, 06999 2 s; 06990 mogut, 06988 exclòs pel scan), 24 s. Per fotograma:
raw − masterdark, saturació ≥ 15600 dilatada 8 px, cada pla de Bayer a resolució plena per
convolució normalitzada (σ 0,7 verd, 1,0 R/B), /exposició, **cel anivellat** a l'anell
4,5–6 R☉ (referència 06993; el 06984 hi va un 22 % més clar, la V del cel: sense això
surt un arc on els 8 s deixen d'estar cremats), desplaçament `offsets6` i, al grup A, la
similitud A→C (`warpM/T/C`, rotació 0,138°). Pes = exposició. Estrelles a l'apilat natiu:
σ 1,45 × 1,15 px (FWHM 11″, el·lipticitat 1,3). **Col·locació al llenç per 7 estrelles
comunes** (la capa Vixen de Pere sí que en té; l'ajust de similitud dona escala 1,48860,
gir 33,088°, Sol a (3427,0, 2185,2) al llenç, rms 0,52 px; l'astrometria deia 1,48965 i
33,08°, i el Sol a (3420,9, 2187,7): 6 px de diferència que queden oberts). Correlació de
la corona (banda 6–28 px, 1,9–3,3 R☉) amb la Vixen: 0,71.

Resultat: capa neta (sense el gra en cuc del Photoshop), estrelles rodones (13″ al llenç),
mateixa correlació dels plomalls amb la Vixen a 4–5 R☉ (0,55–0,6 a 15–70 px); **més
enllà de 5 R☉ cap dels dos trens no té estructura a 15–70 px** (correlació ~0). L'apilat
recull tanta llum com la Vixen (107 mm × 24 s ≈ 90 mm × 31 s): sumar-los guanyaria √2.
Pendent: la combinació d'alta freqüència dels dos trens, i la placa sobre l'apilat.

## 8. Tercera ronda: colze del raig, frontera de fotogrames, i extensió sense halos

- **Colze del raig a la costura**: no és registració (desregistre local apilat–Vixen 0,0–0,3 px
  per sectors a 3,1–4,2 R☉ i 4,2–5,5); és que el raig als 8 s de la Sony porta un sotabanc
  fosc paral·lel (filtratge espacial del RAW llarg) i el seu perfil no és el de la Vixen.
  Corredor ±60 px (ploma 40) a θ = 129,6° entre 2,8 i 6 R☉ amb la Vixen (σ 1,5).
- **Diagonal a baix a la dreta**: la franja on només hi ha els 4 fotogrames de després del
  salt (13 s de 24). El cel de cada fotograma és una superfície llisa diferent (06984 −
  06993: +55…+450 ADU/s segons la zona): un desplaçament constant deixa un salt d'1 %; un
  pla sol, pitjor a les vores; **pla + residu suavitzat σ 300 px** (a 1/8) sobre la zona
  comuna, amb a = 1 fixat (deixar-lo lliure es confon amb el nivell del cel: sortia 1,27 al
  2 s), ho deixa continu. I només píxels del tot dins del vàlid (`Ww > 0,97 e`): la
  interpolació bilineal barrejava zeros a les vores i feia una ratlla fosca de 5–10 px.
- **Els halos del REALÇAT SUAU** eren la banda 100–280 px del DoG isotròpic: al sector
  dret +1,9 % a 5,4–5,8 R☉ i tall a 6,0. Substituït per un **detall només azimutal**
  (polars, bandes en graus 0,6–2 / 2–6 / 6–16, mitjana per radi conservada exactament) i
  una **extensió radial** `cel + (base − cel)·k(r)`, k 1 → 1,4 (3,4 → 6 R☉), cel = mediana
  a 7–7,8 R☉. Cap dels dos pot fer un arc. La banda tangencial gruixuda (6–16°) va a mig
  guany perquè respon a estructura de cel a gran escala (taca fosca al forat entre lòbuls).
- Els fitxers: `APILAT/` (base v2, TANGENCIAL SUAU/MITJA/FORT + PASSALT, EXTENSIO,
  EXTENSIO_TANGENCIAL_MITJA); els del DoG a `APILAT/_anteriors_DoG/`.

## 9. Quarta ronda: les ombres dels cantons, i el flat del 300 mm que ningú feia servir

Pere tria el REALÇAT SUAU (DoG, segona ronda) i marca quatre ombres: tres cantons i la
punta del raig a la vora de dalt. Quatre causes, totes nostres, i una troballa que val
per a tot el projecte.

- **El FE 300 mm f/2,8 GM a f/2,8 vinyeta −1,5 EV al cantó del sensor, i hi ha flat.**
  A `~/Desktop/Sony Calibration/Calibració A7III 04-2025/Flats NETS 300mm {3200,6400}/`
  hi ha 49 + 59 flats de cel de crepuscle de la lent a f/2,8 (A7III, 6048×4024, 300 ADU
  de senyal). Black restat, mitjana, plans de Bayer, **simetrització 180°** (el gradient
  del cel de crepuscle és senar i se'n va; el vinyetatge òptic és parell), σ 25 px, i
  reescalat a la reixa de l'A7RIIIA pel pitch (5,94 → 4,51 µm, centres alineats).
  Resultat: **0,70 a 10 mm, 0,54 a 15 mm, 0,38 a 20 mm, 0,34 al cantó**; radialment
  simètric a ±0,3 % i els dos jocs coincideixen a l'1 %. Sobre el llenç: 0,60–0,65 als
  cantons contra 0,77–0,83 a dalt/baix i 0,69–0,70 als costats. Perfil radial a
  `tools/encaix_sony/flat_sony300_f28_perfil_radial.csv`; codi `flat_sony300.py`.
  ⚠️ El polinomi del `.lcp` que cita `research/75` §4 dona **0,86 al cantó**: es queda
  quatre vegades curt. No el facis servir per a fotometria; el flat mesurat, sí.
  **Comprovació independent** (`test_flat_vs_vixen.py`): l'apilat Sony aplanat contra
  l'apilat lineal de 10,3 s de la Vixen (HDR4, `01_10.3s_…apilat3.dng`) dona un quocient
  de **0,993–1,006 de 4 a 8,8 R☉** (0,97–1,03 als cantons); sense flat cau de 1,03 a
  0,77. Dues conseqüències: el flat és bo, i **la Vixen (VSD90SS + R6 III) no té
  vinyetatge apreciable al llenç** (< 3 % relatiu entre 4–5 R☉ i els cantons). Això
  reobre el §5.3 de `75` en la direcció bona: el pendent «d'extinció» de 0,723 mag/X de
  la Sony és vinyetatge; el de la Vixen (0,416) és el que s'assembla a l'extinció real.
- **La capa Vixen de Pere és una corba de to global a ±1 %, excepte dues rampes.**
  LUT per canal Vixen lineal → capa (`diag_capa_vixen_pere.py`, ajustada a r > 3,6 fora
  de les bandes): quocient 0,993–1,004 de 4 a 8,8 R☉ i 0,998–1,006 a baix i a
  l'esquerra; a dalt, **×0,61 a la fila 0 → 0,99 a ~650 px**; a la dreta **×0,54 a
  l'última columna → 1,00 a ~700 px**. A la matinada s'havia estimat 300 px i només a
  dalt (`VORESNETES`, VORA = 300): entre 300 i 700 px la Sony copiava mig enfosquiment.
- **Les quatre ombres**: baix-esquerra = vinyetatge Sony sense corregir als últims 300 px
  (−8…−12 %); dalt-dreta = vinyetatge + copiar la rampa de Pere; punta del raig = a la
  v1 el sotabanc fosc dels 8 s arribant a la vora, a la v2/v3 el corredor hi posava la
  Vixen enfosquida de la banda de dalt (taca ben definida a (1790, 200)); baix-dreta =
  la frontera de fotogrames de la v1 (×0,62 de la Vixen), ja arreglada al §8.
- **v4** (`pipeline_stack_v4.py`): apilat aplanat; referència = capa de Pere on és de
  fiar i `LUT(Vixen lineal)` dins de les dues bandes (y < 500 / x > W−550, rampes de
  200 px); **D estimat fins a les vores** (VORA = 0); corredor i tros sense apilat (108×70
  px de baix a la dreta) amb la mateixa referència. Capa/referència = 1,000 ± 0,001 als
  quatre cantons, quatre costats i punta del raig. Detall SUAU/FORT com a la v1.
- **El que queda és cel**: els cantons extrems (r ≈ 9 R☉) són un ~20 % més foscos que
  els punts mitjans de les vores (5–7,7 R☉) a la Vixen lineal, a la Sony aplanada i a la
  capa de Pere. Variant cosmètica `_CELPLA` (`cel_pla.py`): luminància del camp llunyà
  (r > 5,6, σ 250) al nivell de 5,6–6,2 R☉ amb rampa 4,8 → 6,2, un sol factor per als
  tres canals (per canal el cel llunyà agafava el color de 6 R☉: R ×1,47 contra B ×1,31).
- Fitxers: `APILAT/` (v4: base, REALCADA SUAU/FORT + PASSALT, `_CELPLA`, TANGENCIAL i
  EXTENSIO regenerats, comparacions abans/després); la v2 sense flat a
  `APILAT/_anteriors_v2_sense_flat/`; el DoG v1 continua a `_anteriors_DoG/`.
- ⚠️ Cap fotometria de la Sony d'aquest projecte no ha portat flat fins avui: l'apilat de
  `apila_sony.py`, la capa de Pere, i les mesures d'extinció de `75`. Qui torni a mesurar-hi
  res, que divideixi pel flat abans.

## 10. La ratlla tangencial a 1,7–1,9 R☉: el graó de la fusió HDR, i el «10,3 s» que és 10,08

Pere tria l'`ESTESA_…_EXTENSIO_TANGENCIAL_MITJA` i hi marca una ratlla recta tangencial a
baix a l'esquerra del disc (θ ≈ 217–271°, r 1,83–1,94). A r < 3 la capa és la Vixen de
Pere tal qual, o sigui que la ratlla és de la seva fusió HDR (`diag_artefacte_tangencial.py`):

- **el contorn de saturació de l'apilat de 10,3 s (13.995 ADU) passa a 37 px de la línia**,
  paral·lel, i la capa de Pere hi té una cresta de +0,5…+0,9 % just a dins i un sot de
  −0,6…−0,8 % just a fora (~40 px): un graó de fusió, visible on el contorn és recte (la
  vora d'un plomall) i camuflat a la resta del contorn.
- **l'apilat de 10,3 s de l'HDR4 és un ~2 % més fosc que el de 2 s**: 10,3 s / (2 s × 5,15)
  = 0,977 a 1,5–1,8 R☉ … 0,987 a 2,8–3,3 (sectors 0,975–0,993); 2 s / (1 s × 2) =
  1,001–1,008. La causa més simple: **l'exposició real del terç de pas és 2^(10/3) =
  10,08 s**, i 10,08/10,3 = 0,979 clava el quocient. «10,3» és l'etiqueta de libgphoto2 (i
  el nom dels fitxers de l'HDR4); l'EXIF `ExposureTime` dels CR3 diu **10** i el
  `ShutterSpeedValue` APEX −3,375 (10,37 s: Canon encodeix el Tv en vuitens). Els CR3 crus
  no tenen cap no-linealitat abans del blanc real (16.383): pugen monòtons; el DNG de
  l'apilat es talla a 13.995 (blanc d'Adobe).
  ⚠️ Conseqüència per a la fotometria: on s'hagi dividit per 10,3 s (`75`, `76`, l'HDR4
  mateix), el resultat és un 2,2 % baix. I si algú refà l'HDR de la Vixen a Photoshop, el
  DNG de 10,3 s s'ha de declarar com a 10,08 s (o multiplicar-lo per 1,02).
- **Correcció v4b sobre la capa** (`corregeix_grao_local_v.py` + `corregeix_grao_local2.py`,
  `K_grao_total.npy`): dues passades multiplicatives per canal, només al sector θ −160…−78°
  (rampes de 12°) i a ±120 px del contorn: (1) perfil mediana en funció del valor del 10,3 s
  (fora, bins de 25 ADU) i de la distància cap endins (dins, 3 px), base lineal i rampes;
  (2) al marc girat de la línia, perfil coherent a y fix (mitjana sobre 700 px de x del
  passa-alt relatiu σ 25), rampes en x de 100 px. El perfil coherent passa de
  +0,52/−0,67 % a −0,24/−0,25 (llis). Un intent global a tot el contorn
  (`corregeix_grao_hdr.py`) es va descartar: la mediana per bins barreja estructura real
  (sectors de −2,3 a +1,0 %). Aplicat a tots els TIFF d'`APILAT/` (no PASSALT).

## 11. UnintCapes4.psb: els retocs com a capes imatge + màscara

Pere demana un successor del seu `UnintCapes3.psb` (6960×4640, 16 bits, Display P3: les tres
capes de l'HDR4 —1 s com a objecte intel·ligent, 2 s + màscara, 10,3 s + màscara al 68 %— que
són el seu HDR manual) amb els retocs de la sessió com a capes imatge + màscara. Fet amb
psd-tools 1.18 (`tools/encaix_sony/psb_utils.py`, `construeix_unintcapes4.py`): llenç estès
7648×5353 (l'ESTESA que ha triat; la seva reixa a +457/+463), les tres capes seves (la 1 s
rasteritzada; 2 s i 10,3 s reutilitzades byte a byte amb màscara i opacitat), la Vixen de
referència (capa de Pere / LUT(lineal) a les bandes), la Sony aplanada i encaixada amb
**màscara = el pes de barreja w** (corredor del raig inclòs), i tres capes Linear Light amb
màscara: graó HDR (sector), detall tangencial MITJA, extensió radial; el cel pla com a capa
oculta. Fusionada = el TIFF ESTESA v4b, i les capes rellegides el reprodueixen a sis retalls.
Tres coses de psd-tools que cal saber: als documents de 16 bits Photoshop posa les capes al
bloc `Lr16` i deixa buida la secció clàssica (psd-tools escriu a la clàssica: `finalize_lr16`
ho mou); `TaggedBlocks.set_data` construeix la classe registrada amb els arguments posicionals
(passar-hi una instància deixa `layer_count` = la instància i peta en escriure); i **les
màscares de capa van a la profunditat del document** —Photoshop les desa a 16 bits als
documents de 16 bits (el canal de màscara d'UnintCapes3 descomprimeix a W×H×2 bytes i psd-tools
mateix les llegeix així)—, mentre que `Layer.create_mask` de psd-tools les escriu sempre a
8 bits i ho documenta com si fos la norma: la màscara surt amb mitja fila cada fila
(`add_mask16` a `psb_utils.py` ho arregla). Comprovat amb psd-tools (composició de sis retalls
contra el TIFF, al nivell de l'arrodoniment) i amb l'ImageIO del Mac; pendent que Pere l'obri
amb Photoshop.

## 12. Els dos projectes de Pere al mateix llenç: CapesInteriors i CapesExteriors

Pere neteja i deixa dos PSB a `~/Desktop/Eclipse 2026/Projecte Photoshop/1-Unint Capes/`:
`CapesInteriors.psb` (6961×4641: les dotze exposicions de l'HDR4 de 1/3200 a 1 s amb màscares +
«Capa 1» = el TIFF ESTESA a (−457,−463)) i `CapesExteriors.psb` (7648×5353: el nostre UnintCapes4
obert i editat a Photoshop —o sigui que Photoshop l'ha obert bé—, amb la Vixen+Sony fosos en una
capa «EDITAT PERE: Earthshine i textures»). Vol copiar i enganxar capes entre tots dos.

Mesures (correlació de fase del passa-alt, anells de retalls; només pics > 0,1):
- **Interiors és coherent**: cada exposició amb la veïna a 0,00 px (pics 0,8–0,97), i totes amb
  Capa 1 (0,0 / +0,2 px). Les 11..03 són a (1,1) i la 1/3200 a (0,0): la va alinear ell.
- **Entre projectes**: la 03_1s d'Interiors i la d'Exteriors coincideixen a **I + (456, 462) = E**
  (pic 0,96); Capa 1 (TIFF a I(−457,−463)) i EDITAT PERE (TIFF a E(−1,−1): Pere l'havia mogut 1 px)
  ho confirmen (0,00 px, pic 1,00). O sigui que la meva col·locació del TIFF respecte de la reixa
  crua a UnintCapes4 anava 1 px avall/dreta de les seves capes, i ell ho va corregir movent el TIFF.
- **A Exteriors**: la 03 està alineada amb EDITAT (0,01/0,14 px); la **01_10.3s** era a (−2,+1) →
  moguda (+2,−1) → (0,00/0,03); les quatre Linear Light nostres (reixa del TIFF a (0,0)) → (−1,−1).
  La **02_2s no és una translació**: els desplaçaments giren amb l'azimut (fins a 6 px; ~−0,5 %
  d'escala + (−1,9, −0,1)): un revelat de Camera Raw diferent (correcció d'objectiu / retall) del DNG
  de 2 s a l'UnintCapes3 antic. Queda sota EDITAT; si mai la necessita, revelar el DNG com la 1 s.
- **Fet** (`redimensiona_interiors.py`): Interiors → 7648×5353 amb totes les capes a +(456,462) (Capa 1
  a (−1,−1) = EDITAT), fusionada nova, `header.channels` 4 → 3 (⚠️ l'original duia RGB + alfa
  fusionada; amb 3 canals de dades i 4 a la capçalera Photoshop no ho obriria) i sense Mt16/SLICES;
  Exteriors amb la 01 i les Linear Light mogudes (107 bytes de diferència amb l'original). Còpies
  `*_abans_*.psb` al costat. Enganxar entre projectes: «Enganxa al lloc» (Maj+Cmd+V).
- ⚠️ El scratchpad de la sessió es va buidar a mig fer (macOS o la neteja): els intermedis de la
  v4 no hi són; els scripts són tots a `tools/encaix_sony/` i es regeneren amb `v4_intermedis.py`.

## 13. El limbe lunar: franja de color i ondulació, i les dues capes correctores

Pere marca «cercles concèntrics» al limbe (de color i de «pixelat»). Mesurat en polars sobre la
vora real del disc (detectada per azimut, subpíxel; centre (4034,7, 2736,7), radi mitjà 452,5 px,
el perfil lunar es desvia 1,4 px rms del cercle):
- **franja de color**: el canal blau té la vora més tova (Bayer/PSF): just dins de la vora
  (d −7…−1 px) el disc surt blau ((R−B)/L −0,13…−0,38) i a d 0…+2 hi ha un anell groc-verd; el
  color de la corona (+0,41…+0,48) es recupera a d ≥ +3. És a EDITAT i a la composició d'Interiors.
- **ondulació**: a EDITAT (el revelat/enfocament antic) el passa-alt mostra anells alterns d'1–2 px
  fins a ~+8 px del limbe i un 30 % més de variància azimutal a la banda 1,01–1,06 R que la
  composició nova d'Interiors, que és neta.
`CorreccioLimbe.psb` (mateix llenç; `tools/encaix_sony/correccio_limbe.py`), per duplicar cap a
CapesExteriors: **A «desfranja de color», mode COLOR** —dins del limbe el color del disc del mateix
azimut (mesurat a −14…−8 px), fora el de la corona o protuberància (+9…+15), transició ±1,5 px,
màscara −7…+5 amb ploma 3— només toca to i saturació, val sobre qualsevol base i respecta les
protuberàncies; **B «textura», LINEAR LIGHT** = passa-alt σ 2 px d'Interiors − el d'EDITAT a
−3…+14 px: canvia l'estructura fina sense moure nivells (cap graó a les vores de la màscara), i
només val sobre EDITAT. Es va provar i descartar un suavitzat tangencial (σ 0,4°: esborrava les
protuberàncies) i una substitució de píxels per la composició d'Interiors (graons de nivell: EDITAT
té el disc el doble de clar).

## 14. Els filtres de pas alt de Pere, tots al mateix llenç

Pere prova filtres de pas alt a Photoshop i té la carpeta `Projecte photoshop/2-Filtres/` amb
tres documents de capes a **tres llenços diferents** —`Aplicant_Filtres.tif` (7648×5353 = E, la seva
imatge amb la capa A del limbe), `filtres_Tangencials.tif` (6961×4641: base amb el disc farcit
d'un beix pla ×3 + dos pas alt tangencials `a`, `b`) i `filtres_radials.tif` (6748×4553: base +
`filtre radial A`, `B` en Overlay)— més el `PASSALT_FORT`, el `detall` i el `radial` del pipeline
a la reixa de `Corona_HDR_Vixen`. Demana tenir-ho tot alineat per apilar-ho com a capes.

Mesurat (correlació creuada del passa-alt σ6, 8–10 retalls, subpíxel per DFT;
`tools/capes_photoshop/mesura_alineacio_filtres.py`), amb la fusionada d'`Aplicant_Filtres`
com a E:
- `filtres_Tangencials.tif` és el llenç de CapesInteriors d'abans de redimensionar: **E = font +
  (456, 462)**, 0,00 px, NCC 0,98–1,00; `filtres_radials.tif` és el llenç antic de 6748×4553:
  **E = font + (599, 549)**, 0,00 px. Els dos coincideixen amb §12 (E = I + (456, 462); llenç antic
  a ESTESA (600, 550), E = ESTESA − 1). El pas alt tangencial i el radial A **van invertits**
  (blur − base + 50 %: correlació −0,97 amb el pas alt de la base; el radial B i el nostre
  PASSALT, +0,98): en Overlay/Linear Light suavitzen. Les capes `1`, `2` i `3` són byte a byte
  la mateixa.
- la reixa del pipeline (6958×4638, Sol a (3479, 2319)) cau a **E = P + (542,6, 418,5) ± 0,1 px**,
  per tres camins que coincideixen a 0,1 px (`detall`, `radial` i `PASSALT` contra la fusionada,
  i via el DNG `03_1s` de l'HDR4: P → DNG (85,50, −44,02) contra els (84,89, −44,34) documentats a
  `alineacio_llenc_Pere.json`, o sigui +0,6/+0,3 px, els mateixos que la comprovació d'allà; i
  DNG cru → E (457,0, 462,7): les capes ACR de Pere estan 0,34 px per damunt de les dades del
  DNG). Els `*_llencPere.tif` de `Corona_HDR_Vixen`, comparats amb el seu propi original, porten
  un residu de fins a 0,8 px que varia pel camp; no s'han fet servir.

Lliurat a la mateixa carpeta (`tools/capes_photoshop/alinea_filtres_al_llenc.py`):
`Filtres_alineats_7648x5353.psb` (base + 9 capes al seu lloc, amagades, mode d'origen; les del
pipeline remostrejades cúbic pel subpíxel) i `alineades_7648x5353/` amb un TIFF pla per capa
per «Enganxa al lloc»; tot Display P3, 16 bits; `LLEGEIX-ME_alineades.md` al costat. Verificat
reobrint-ho: capes byte a byte iguals a la font, alineació ≤ 0,05 px de mediana. Una trampa
que va costar una passada: **el signe de la correlació** («la font cau a −1,7» = posar-la 1,7 px
més a la dreta); el primer intent ho va restar i va sortir 3 px fora, i la verificació ho va
enxampar. Lector de capes a resolució completa: `tools/capes_photoshop/capes_tiff.py`.
