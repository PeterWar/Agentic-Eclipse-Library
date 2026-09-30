# Seguiment, deriva i calibratge del tren Vixen + R6 III, mesurats de les imatges de l'eclipsi

Data: 15 d'agost de 2026, matinada. Mesures fetes per Claude sobre els 124 CR3
de totalitat (`~/Desktop/Eclipse Vixen Unfiltered`) i la biblioteca de darks
del 14 d'agost. **Coneixement canònic del tren Vixen VSD90SS + Canon R6 Mark
III**, declarat per Pere. Eines reproduïbles: `research/tools/
pilot_calibratge_vixen.py`, `lot_calibratge_vixen.py` i `mesura_deriva_v2.py`.

## 1. Seguiment i deriva: taxa SOLAR verificada, i la deriva residual és la REFRACCIÓ

⚠️ **Aquesta secció substitueix una versió anterior del mateix dia que
declarava deriva ≤ 2″ i escala 2,1935″/px: totes dues sortien d'un ajust de
limbe degenerat** (§3, trampa 0). Amb l'ajust bo (42/42 fotogrames vàlids,
arcs de 360°, rms 1,1-1,5 px, residu de traça 0,26 px):

- **La Lluna es mou a 0,3355 px/s sobre el sensor** (traça lineal robusta;
  model conjunt amb biaix de glare per grups d'exposició: betes ≤ 0,4 px, no
  canvien el pendent; semiarcs brillant/fosc coincideixen a 5 %).
- **Escala de placa: 2,158″/px** (radi lunar al límit d'exposició curta,
  453,8 px, contra 979,1″; equival a focal 494 mm ✓ VSD90SS 495). ⚠️ El radi
  ajustat **decreix amb l'exposició** (453,8 → 446,7 px a 10,3 s): el glow de
  l'anell saturat menja la vora. Cap mesura de radi amb fotogrames profunds.
- **Els contactes reals són a les imatges** (brillantor dels 79 fotogrames
  d'1/3200): C2 real a **−1,0 ± 0,7 s** i C3 real a **+102,7 ± 0,7 s** del
  predit → **totalitat real 103,7 s**, clavada a la predicció del FINAL 2
  (103,8). Això valida efemèrides i lloc, i acota (rellotge R6 + error de
  predicció) ≤ 1 s.
- **La deriva real està mesurada directament de les parcials filtrades**
  (ajust RANSAC del cercle solar a 26 parcials, discriminant el cercle solar
  del lunar —radis quasi iguals!— per la brillantor interior). El tram d'or:
  **20 fotogrames seguits sense correccions (C2+850 a C2+1417 s) donen una
  deriva lliure de 0,689″/s**. La refracció prevista allà (alt 5,8°, baixant
  10,7″/s) és 0,209″/s → **la muntura deriva ~0,48″/s ≈ error polar d'uns
  2°** (alineació diürna, com Pere sospitava). Les **correccions manuals de
  Pere són visibles** (salt de +183 px a C3+90 s).
- **Durant la totalitat** (ningú no toca res): el tancament
  |v_Lluna − v_Sol| = 0,2737 px/s amb la direcció de deriva mesurada dona
  **v_Sol ≈ 0,28 px/s = 0,61″/s → ~63″ ≈ 29 px de deriva en els 103,7 s**,
  compartits per Sol i Lluna: **el relatiu no es toca i les piles alineades a
  la Lluna no en pateixen**. Refracció a totalitat (alt 9,1°): 0,106″/s; la
  resta és muntura. Coherència global: v_Lluna mesurada contra
  (efemèrides + deriva del tram) tanca a **+4,7 %** — el que queda reflecteix
  que la deriva evoluciona entre èpoques.
- ⚠️ Una versió intermèdia d'aquest document atribuïa tota la deriva residual
  a la refracció («muntura essencialment perfecta»): fals. La correlació de
  «banderols» que donava Sol quiet estava ancorada al flare de l'òptica (§3,
  trampa 4), i la deriva real és ~5 vegades la refracció.
- Pendent de clavar: l'àncora d'azimut de perles a C2/C3 per fixar la rotació
  del sensor i la descomposició exacta vertical (refracció) / declinació
  (polar).
- Moviment topocèntric Lluna−Sol al FINAL 2: **0,5905″/s, PA 118°**; 2,8 px
  de moguda interna a cada fotograma de 10,3 s (capa SNR; la nitidesa la
  posen els 2 s).

## 2. Calibratge dels CR3: el negre de la metadata és fals i el pedestal real és 511-512

- ⚠️ **libraw declara un negre per canal [0, 31, 94, 63] per a la R6 III i és
  fals: el pedestal real són 511-512 ADU, pla als quatre canals** (mesurat als
  867 darks; sonda: un master passat pel revelat deixa ~478 ADU residuals).
  Qualsevol eina basada en libraw —PixInsight inclòs— pot arrossegar un
  pedestal fantasma de ~480 ADU, que **trenca l'HDR lineal**. El pipeline
  n'és immune per construcció: el pedestal viatja dins el master
  (`llum − (master − negre_metadata)`).
- **Masters propis per MEDIANA** de fins a 25 darks per exposició, 16
  exposicions (1/3200 → 10,3 s), pedestal vigilat: tots a 511,0-512,2.
  Validació fotomètrica del lot: **residu 0,0 ADU a les curtes** i taxa de cel
  coherent 375-500 ADU/s d'1/125 a 10,3 s (decreix cap al mig de la totalitat,
  com toca físicament).
- **Els masters APP de Pere: 15 de 16 validats** (coincidència ±1,4 ADU al
  99,9 % dels píxels amb el master de mediana independent; píxels calents
  conservats, ratio 1,022). ⛔ **El de 0,5 s és defectuós** —std 18,6 i 21.457
  falsos calents— per barreja tèrmica entre tandes: la cua de píxels tèrmics
  canvia per sessió i a 0,5 s el cos hi és singularment sensible (parelles
  del mateix run: std 4-5 les fredes, ~52 les calentes; medianes totes 512,0,
  o sigui cap fuita de llum). La mitjana amb rebuig la barreja; la mediana la
  neteja.
- **Sensor a 41-43 °C durant la totalitat** (EXIF); darks conservats ≤ 44 °C.
  Els residus tèrmics que quedin els remata el mapa de defectes (G1B), no més
  darks.
- Balanç de blancs de càmera (Daylight escrit per l'app al preflight):
  **R ×1,94 · B ×1,66**. El «verd» en debayerar sense WB és comportament
  lineal correcte, no cap defecte.
- Vel de cel a 9° d'altura (massa d'aire 6,4): **3.400-4.300 ADU al fotograma
  de 10,3 s** — el fons dominant; el model de cel/halo de G1B/G3 és el front
  real per a la corona exterior i l'earthshine.
- Lot calibrat: `Eclipse Vixen Unfiltered/Calibrated_Claude/` (124 TIFF
  lineals 16 bits + `_masters/` + `manifest.csv` amb SHA-256 + `previews_sRGB/`
  + parelles de comparació a `Comparacio_Calibratge/`).

## 3. Les trampes de mesura, perquè ningú no hi torni a caure

0. **El disc «fosc» que no ho és**: amb vinyetatge i vel, les cantonades del
   sensor són més fosques que el disc lunar (13.400 contra 15.400 ADU16), i
   un matched filter de «disc més fosc» clava el centre a un racó. El bo és
   **centre-vora** (anell brillant − interior). I un ajust degenerat pot
   retornar un radi igual al centre de la finestra de cerca (445 px per a
   rs∈[370,520]) i una «traça» que no és res: sempre validar amb rms, arc
   cobert i dibuix sobre la imatge.
1. **El dipol del centre**: restar un perfil radial centrat a la Lluna deixa
   un residu dipolar que es mou amb ella; el correlador segueix la Lluna
   creient que segueix el Sol. Mesura contaminada: 0,73″/s de «deriva» falsa.
2. **L'àncora del forat**: emmascarar la Lluna amb la unió de les dues
   posicions fa el forat idèntic als dos costats — i amb el senyal afeblit,
   la vora del forat ancora la correlació a zero exacte.
3. **La solució per a estructura**: pegats petits en anell que eviten
   geomètricament Lluna i saturació, passa-alts isòtrop, mediana entre pegats
   (la dispersió entre pegats és la mètrica d'error real; la `err` de
   `phase_cross_correlation` desborda en float32 i val 1,0 sempre).
4. ⚠️ **Però els «banderols» a prop del Sol estan contaminats pel patró de
   flare/difracció de l'òptica, que és FIX AL SENSOR**: la correlació de
   pegats hi surt ancorada a zero encara que el Sol es mogui (és com es va
   mesurar una falsa deriva nul·la). El moviment solar fi s'ha de treure del
   tancament Lluna−efemèrides o d'àncores de contacte, no de correlació prop
   del Sol.
5. **Restar una plantilla estàtica a un patró que es mou poc** converteix el
   senyal en còpies escalades del mateix patró derivat i la correlació pica a
   zero per construcció. No serveix per mesurar el moviment del patró.
6. **El signe de `scipy.ndimage.shift`**: desplaça el contingut *cap a*
   +shift; per portar un fotograma amb offset (dx,dy) al de referència cal
   aplicar (−dy,−dx). El primer apilat d'earthshine duia el signe girat i
   doblava el desajust (~17 px de vora doble; ho va detectar Pere a ull).
   **Norma: tot apilat porta verificació independent** — re-ajustar el limbe
   sobre cada fotograma ja alineat i exigir dispersió < 0,5 px entre membres.

## 4. Hores i rellotge

EXIF de la R6 amb subsegon (`SubSecTimeOriginal`) via exiftool. Per al
moviment **relatiu** entre fotogrames el rellotge es cancel·la; el tancament
absolut (convenció inici/final d'exposició i offset del cos) queda pendent de
les perles de C2 (gate G0). Sensibilitat: 0,269 px/s → un error d'1 s són
0,27 px a l'alineació absoluta.
