# 96 · El camp de la Sony va caure: dos apuntaments, no un — i què en fem

**23 d'agost de 2026, matinada.** Document canònic. Recull (A) la troballa que
explica d'una sola causa gairebé tots els artefactes que hem perseguit, (B) el
que fa de veritat l'equip de Druckmüller, llegit dels papers, i (C) les
decisions de metodologia que Pere i jo hem consensuat aquesta nit.

Evidència: `output/salt_muntura_20260823/` (les tres figures i el
`registre_v3_sony.json`).

---

## A · LA TROBALLA

### A.1 Com hi vam arribar

Jo havia mesurat, sense saber-ho explicar, que hi ha **dos llenços diferents**:
l'apilat viu a **7968 × 5320** i el projecte de Photoshop a **7648 × 5353**.
Pere ho va llegir i va dir: **«el camp va caure, la muntura va patinar, per
això es va perdre la imatge dels 8 s».** Ho vam comprovar contra el registre i
és exactament això.

### A.2 L'evidència, del `registre_v3.json` de l'apilat Sony v3

Els deu fotogrames apilats es parteixen en **dos grups nets**:

| grup | fotogrames | exposició | desplaçament |
|---|---:|---:|---|
| **nominal** | 6 · `DSC06993` 8 s, `06996` 2 s, `06999` 2 s, `06991` 1 s, `06994` 0,25 s, `06997` 0,25 s | **13,50 s** | 0 a 8 px |
| **desplaçat** | 4 · `DSC06987` 8 s, `06984` 2 s, `06985` 1 s, `06982` 0,25 s | **11,25 s** | **(−233, +713) px** |
| | | **24,75 s** | |

El salt és de **750 px = 40 minuts d'arc** a 3,2020 ″/px. I hi ha **dos
fotogrames exclosos**, que el propi registre documenta:

- **`DSC06990`** (8 s) — «moguda pel salt 2 de muntura (research/72)»
- **`DSC06988`** (1 s) — «traços d'estrelles de ~25 px en y (**inici del salt
  2**); offset astromètric a 4σ no fiable»

O sigui que hi havia **tres** fotogrames de 8 s i el salt se'n va menjar un.
Concorda amb `research/72`, que ja havia mesurat dos salts de l'Skywatcher
(+223 px i −715 px) i n'havia donat la causa per testimoni de Pere: **en
treure el filtre solar va moure la lent de 300 mm** i la pertorbació es va
alliberar amb retard, en dos temps (C2+30 i C2+50).

### A.3 La cadena causal, sencera

```
Pere treu el filtre solar i toca la lent
        ↓
la muntura cedeix en dos temps; el segon salt val 750 px
        ↓
els 10 fotogrames apilables queden a DOS apuntaments diferents
        ↓
al llenç comú, només la INTERSECCIÓ té els 10 fotogrames
        ↓
«zones de cobertura»: 78,34 % amb 24,75 s, 15,52 % amb només 13,50 s
        ↓
un graó d'exposició acumulada a y = 4578, en UNA SOLA FILA
        ↓
el mateix tros de cel es veu a dues posicions del sensor separades 750 px,
o sigui a través de dues parts diferents del VINYETATGE
        ↓
el graó és MULTIPLICATIU (~1,4 %), no additiu
        ↓
a 6 R☉ el cel val 78 vegades la corona: un 1,4 % de cel hi és ~100 % del senyal
        ↓
la costura que hem perseguit tota la nit, i la línia on Pere veia artefactes
```

**Mesures que ho sostenen** (totes DEMOSTRAT):

- petjades al mapa de pes: intersecció x 264–7926, y 40–4578 (**78,34 %**);
  només nominal (13,50 s) **15,52 %**; només desplaçat (11,25 s) 1,00 %.
- el graó és multiplicatiu: creuant y = 4578, la **diferència additiva varia
  ×2,7** al llarg de la vora (−2,05·10⁻¹⁰ a −7,6·10⁻¹¹) mentre que el
  **quocient es manté entre 0,978 i 0,989**.
- amb l'anivellament per vores i per guany: costures de −2,06 / −2,57 / −1,71 %
  a **−0,75 / −0,84 / −1,00 %**. El que queda és el flat.

### A.4 El que això costa, i que no sabíem

**El llenç no aguanta la unió dels dos apuntaments.** La unió és
**8185 × 6017** px i el llenç de l'apilat és **7968 × 5320**: falten **697 px
en y i 217 en x**. Una franja de l'apuntament desplaçat **es va llençar en
silenci**.

I encara n'hi ha un segon: el **llenç de Photoshop (7648 × 5353)** no coincideix
amb el de l'apilat i **perd 16,1 R☉² = el 3,4 % del camp de la Sony**, també en
silenci.

### A.5 I la part bona: el salt ens dona el flat

Un desplaçament de **750 px entre dos apuntaments del mateix cel** és
exactament el que es fa **a propòsit** per autocalibrar un flat: la regió
comuna dona el **quocient del vinyetatge entre dos punts separats 750 px**. És
*flat-field self-calibration* per dither, de manual.

### A.5 bis · EXECUTAT el 23-08 al matí: sí, és vinyetatge, i està mesurat

Els **dos fotogrames de 8 s** són un a cada apuntament —`DSC06993` (nominal) i
`DSC06987` (desplaçat)—, o sigui que el seu quocient **és** el quocient de
vinyetatge entre dues posicions del sensor separades 750 px. Mesurat sobre
4.697.513 píxels entre 1,5 i 9 R☉ (codi i figura a
`output/flat_dither_20260823/`):

| ajust al `ln` del quocient | variància explicada | rms del residu |
|---|---:|---:|
| **constant** | **0,0 %** | 10,05 % |
| **pla** | **96,6 %** | **1,86 %** |
| quàdrica | 97,0 % | 1,74 % |

**El quocient NO és constant: és un gradient.**

⛔ **RECTIFICACIÓ (23-08, tarda).** La primera versió d'aquesta secció deia:
«la direcció del gradient és −74,3° i la del salt −72,0°, coincideixen a 2,4°».
**Aquell 2,4° era fals.** L'ajust es feia en coordenades **normalitzades** —per
amplada i per alçada, que valen 3984 i 2660 i no són la mateixa unitat— i
l'angle que en sortia es comparava amb una direcció del salt en **píxels**.
Convertit bé, el mateix ajust dona **−79,36°** i el salt **−71,96°**: la
coincidència real és de **7,43°**, tres vegades pitjor. I com que la separació
entre les dues hipòtesis (salt contra zenit) és de només **21,79°**, un error de
7° no és cosmètic. La conclusió aguanta; aquella prova, no.

### La prova bona: tres arguments independents

**1. El flat mesurat el prediu.** El màster de flat de la Sony de
`output/flats_20260822/sony_a7r3a_300mm_posterior_v1/` —**53 ARW del 22-08**,
mateix cos, mateix 300 GM, f/2,8, ISO 100, i que **no surt d'aquestes
imatges**— avaluat com `V(p+salt)/V(p)` reprodueix el camp observat amb
**coeficient +1,019** i **explica el 98,0 % de la variància**; el residu passa
de 9,98 % a **1,42 %** rms. Amb el component radial sol dona el mateix (96,7 %),
o sigui que no depèn de la pols ni del camp complet que `research/90` té en
quarantena.

**2. No escala amb el temps, i això desconfon les dues coses.** Sis parells de
fotogrames amb **el mateix salt de 750 px** i Δt diferents:

| parella | Δt | \|g\| (%/1000 px) | eix | dist. al SALT | dist. al ZENIT |
|---|---:|---:|---:|---:|---:|
| 8 s | 33,0 s | 7,968 | 10,61 | 7,43° | 29,22° |
| 1 s | 34,0 s | 8,087 | 10,34 | 7,70° | 29,49° |
| 2 s | 64,0 s | 8,503 | 4,96 | 13,08° | 34,87° |
| 1/4 s | 69,0 s | 8,650 | 4,13 | 13,91° | 35,70° |

**Doblar Δt (33 → 70 s) mou el gradient un +8 %, no ×2.** I l'eix **s'allunya**
del zenit, no s'hi acosta.

**3. Extrapolat a Δt = 0, el flat el clava.** Regressió `g(Δt) = g₀ + Δt·u`
sobre els sis parells:

| | mòdul (%/1000 px) | eix |
|---|---:|---:|
| **g₀** (només apuntament) | **7,564** | **17,16°** |
| **el flat mesurat prediu** | **7,664** | **17,60°** |
| | *1,3 % d'error* | *0,44° d'error* |

### Per què l'extinció no ho pot fer

L'alternativa que va proposar Codex queda **refutada per tres vies
independents**:

- **Mòdul.** Un cop registrat B sobre A per la corona, cada punt coronal mira
  la **mateixa direcció del cel** als dos fotogrames, o sigui que el gradient
  d'extinció pel camp —que és enorme, **8,2× d'una cantonada a l'altra**— **es
  cancel·la exactament**. Només sobreviu la curvatura de X(h) en 33 s: **1,75 %
  de p5 a p95**, el 5,1 % de l'observat. Per fer el gradient observat caldria
  **k = 8,1 mag/massa d'aire**.
- **Signe.** X(h) és convexa i decreixent: anant enrere en el temps el Sol puja
  i la part **baixa** del camp guanya més. L'extinció prediu **PA 220,5°** i
  l'observat va a **PA 10,6°**: **150° de diferència**. La regressió contra el
  model d'extinció dona **b = −14,89** en lloc de +1.
- **Temps.** No escala amb Δt (punt 2).

⚠️ **Però Codex tenia raó en el forat, i era meu.** Apuntament i temps estaven
**perfectament confosos** —el grup desplaçat és l'**anterior**— i amb la mesura
del matí no hi havia manera de separar-los. **Sí que hi ha un terme temporal
uniforme**: l'extinció en prediu **+2,25 % en 33 s** i **+2,86 % en els 42,3 s**
que separen els centres de gravetat dels dos grups. És real i entra a la
costura. ⛔ I no serveix com a detector: la dispersió de nivell **per fotograma**
és de **±6 %**, del mateix ordre.

### L'amplitud estava sobrevenuda

La primera versió deia «34 % quadra amb els −1,5 EV al cantó del 300 GM». El
**gradient** aguanta i millora amb el tall de linealitat —de 16.100 a 12.000 ADU
crus, la variància explicada pel pla puja de 96,36 a **97,27 %** i el residu
baixa a 1,68 %; a 8.000, 98,88 % i 0,85 %—, però **la descomposició de
l'amplitud en termes no està tancada**.

⚠️ **Front obert nou: un pedestal.** El pendent del quocient **creix amb el
nivell a radi fix** (32,5 % a 4000–5500 ADU contra 63,3 % a 9000–11500). La
no-linealitat **no** ho pot fer —tindria el signe contrari, la compressió
hauria de reduir el pendent a dalt— però **sí** un terme **additiu** que no
segueixi el vinyetatge.

⚠️ **I una cosa que NO està tancada:** el signe del graó al **compost** va en
sentit contrari al que dona la parella de 8 s. Cal comprovar si és una qüestió
de convenció del quocient, de si el compost ja porta flat, o de la ponderació
per exposició. **No ho donis per resolt.**

Evidència: `output/gradient_axis_20260823/` i `output/flat_dither_20260823/`.

### A.5 ter · ⚠️ RECTIFICACIÓ: la degeneració és PERPENDICULAR al salt

La versió anterior d'aquesta secció deia que quedava degenerat «el mode de gran
escala **al llarg** de la direcció del salt». **És al revés.**

El que es mesura és `ln F(x) − ln F(x+Δ)` per a tot `x` de la zona comuna. Això
determina `ln F` **al llarg de cada recta paral·lela a Δ**, llevat d'una
constant per recta (els modes periòdics de període |Δ| són negligibles perquè
un vinyetatge és llis). O sigui que **el que queda lliure és una constant per
recta, i això és una funció arbitrària de la coordenada PERPENDICULAR a Δ.**

**I la degeneració es trenca sense sortir de les nostres dades.** `research/72`
§1 documenta **dos** salts i són **perpendiculars entre ells**:

- **SALT 1: +223 px en x** (~12′), cap a C2+30…+42
- **SALT 2: −715 px en y** (~39′), cap a C2+42…+57

Dues direccions ortogonals de dither **determinen el flat sencer** llevat d'una
sola constant global, que la fotometria absoluta de `research/75` ja fixa. El
propi `research/72` ja els anomenava «pseudo-dither» sense treure'n aquesta
conseqüència.

⚠️ **El que falta, amb els candidats concrets.** La cronologia EXIF de la
totalitat, amb el que el v3 va fer amb cada fotograma:

| hora | fitxer | exp | estat |
|---|---|---:|---|
| 20:28:48 | `06979` `06980` `06981` | 1/800, 1/6400, 1/100 | bloc de contacte, no usat |
| 20:28:58 | `06982` `06983` | 1/4, 1/30 | **apuntament desplaçat** |
| 20:29:00 | `06984` | 2 s | apuntament desplaçat |
| 20:29:10 | `06985` | 1 s | apuntament desplaçat |
| 20:29:11 | `06986` | 1/8 | no usat (desplaçat) |
| 20:29:19 | `06987` | **8 s** | apuntament desplaçat |
| 20:29:27 | `06988` | 1 s | **EXCLÒS** — «inici del salt 2» |
| **20:29:28** | **`06989`** | **1/8** | **no usat — candidat: prou curt per no arrossegar-se** |
| 20:29:36 | `06990` | 8 s | **EXCLÒS** — mogut pel salt 2 |
| 20:29:44 | `06991` `06992` | 1 s, 1/8 | **apuntament nominal** |
| 20:29:52 | `06993` | **8 s** | apuntament nominal |
| 20:30:02–10 | `06994`…`06999` | 1/4…2 s | apuntament nominal |

O sigui que **el salt 2 va passar entre les 20:29:19 i les 20:29:44**, i el
`DSC06989` (1/8 s, 20:29:28) hi cau al mig: és prou curt perquè valgui la pena
mirar si té un apuntament propi i net.

I **el salt 1 (+223 px en x) va passar ABANS de les 20:28:58**, o sigui abans
que comencessin les àncores: la seva altra banda són els blocs de contacte de
les 20:28:42–48 (1/800, 1/6400, 1/100). Són curtíssims i saturats a prop del
limbe, però a 1/100 hi ha corona interior de sobres per mesurar-hi un quocient
en una banda de radis limitada.

**Conclusió: `research/90` —«el flat òptic de la Sony no s'ha aplicat»— deixa
de ser un deute sense sortida. El flat es pot mesurar de la pròpia avaria.**
(DEMOSTRAT: que el graó és vinyetatge i que el quocient és un gradient alineat
amb el salt. FALTA: reconstruir el flat i aplicar-lo.)

---

## B · QUÈ FA DE VERITAT L'EQUIP DE DRUCKMÜLLER

Llegit dels 55 PDF de `~/Desktop/Eclipse 2026/Papers Druckmuller/` i de les
notes de `research/data/lectures_druckmuller_2026-08-18/`.

### B.1 L'ordre canònic de Brno

```
calibrar  →  registrar (correlació de fase)  →  compondre (LDIC)  →  realçar (ACHF / FNRGF / NAFE)
```

**No hi ha cap etapa que apili primer els fotogrames de la mateixa exposició i
després en fusioni els resultats.** L'apilat i l'HDR **són la mateixa
operació**: una sola suma ponderada de tots els fotogrames de totes les
exposicions.

### B.2 L'LDIC, amb la fórmula

**LDIC = Linear Digital Image Composer**, Miloslav Druckmüller, 2006. Tesi de
Druckmüllerová 2013 §4.1.4, p. 48, **eq. (4.15)**:

```
g(r,φ) = Σ_i  w( f_i(r,φ) ) · ( k_i(φ)·f_i(r,φ) + q_i(φ) )
```

- coordenades **polars heliocèntriques**; `k` i `q` depenen **només de l'angle
  de posició φ**, no del radi
- `w` és **per píxel i per imatge** i depèn **només del valor del píxel**: 1 a
  la major part del rang, **0 per damunt del ~85 %** (on la resposta ja no és
  lineal) i 0 al tram baix (soroll), amb transicions graduals i contínues
- **cap ponderació per σ², variància ni S/N** en tota la descripció
- `k_i(φ)`, `q_i(φ)`: **60 segments angulars**, regressió lineal per segment
  contra el que ja s'ha compost, suavitzats amb un polinomi trigonomètric
  d'ordre 0/1/2/4. La composició és **seqüencial**, comença per les exposicions
  més llargues
- el factor d'escala **no és el temps nominal**: es mesura de les dades, «more
  exactly on the brightness of the image»
- **lineal, mai logarítmic**: rebutgen l'HDR d'estil paisatge perquè trenca la
  monotonia i inutilitza la fotometria

I la tesi diu explícitament que **una mitjana ponderada que ignori el saturat i
el soroll és un mètode adequat**. El que l'LDIC hi afegeix és: compondre el
color, seguir el moviment de la Lluna —i fer una composició **nítida** de
l'earthshine—, i l'adaptivitat de `k` i `q` per segment angular, que és el que
permet compondre imatges amb **distribucions diferents de llum difusa** (just
després de C2 contra just abans de C3) i fins i tot preses a través de núvols
prims.

### B.3 Els pesos els fan A MÀ

Paper de 2006: **«A subjective method of the weight estimation is currently
used»**, amb dues figures que són **mapes de pes pintats fotograma a
fotograma**. I la Fig. 4.4 de la tesi és la captura d'una interfície
interactiva.

**El mapa de pes de cada fotograma ÉS la màscara de capa de Photoshop.**
Supervisar capa a capa i retocar màscares no és desviar-se del mètode de
Druckmüller: **és el mètode de Druckmüller.**

### B.4 Dos instruments: no cusen, componen

Registren tots els fotogrames de tots els instruments a **un camp comú** per
**semblança** (desplaçament + gir + escala, correlació de fase log-polar) i
fan **una sola composició ponderada**. Precedents literals:

- **1994**: 8 imatges, 100/1875 mm i Maksutov 1050/1100 mm, de **dues
  expedicions, dos llocs i dues totalitats** → una composició
- **1995**: 10 imatges, Exacta 8/500 mm en 24×36 i Zeiss AS 200/3000 mm en
  plaques 18×24 cm. **Relació de focals 6×** → «Composition of the 10 images
  was used for the final picture»
- **2023** (Habbal et al. 2025 §2.1): el compost de camp ample fins a ~10 R☉
  és **199 imatges del 200 mm més les del 1000 mm**. Relació de focals 5×

⚠️ **Rectificació de `research/82` §1.** Deia que el 2002 «interior i exterior
de dos instruments processats a part i **cosits**». El paper **no diu enlloc**
«stitch», «blend», «seam» ni cap radi de traspàs, i atribueix el resultat al
mètode de composició general. **«Cosits» és inferència nostra, no literal.**

⚠️ **I quan és ciència i no una foto, NO barregen.** Boe, Habbal &
Druckmüller 2020 apilen camp estret i camp ample i **eliminen tot el camp ample
per sota de 2 R☉** per la mala resolució comparada. És un **tall radial dur per
resolució**. A Boe et al. 2021 (ApJL 914) els dos instruments ni es fusionen.

### B.5 El camp comú de Brno no és astromètric

Es defineix com **«totes les imatges amb el mateix centre del Sol i el mateix
radi solar en píxels»**. En cap dels 54 PDF no hi ha «gnomonic», «tangent
plane», «WCS» ni «astrometry». **Nosaltres sí que tenim astrometria** (38 i 22
estrelles, `research/75`) i això ens permet un camp comú millor que el seu.

### B.6 El registre

Correlació de fase modificada, cada fotograma contra una referència, amb una
transformació **global de semblança** (desplaçament + gir + escala, 4
paràmetres), reduïda a **desplaçament pur** quan tot ve de la mateixa càmera i
òptica sense reenfocar. **Ni afí, ni elàstica, ni cap camp de deformació.**

I una precaució que hem de copiar: **la Lluna es treu ABANS de mesurar res**
—emmascarada en un anell r₁ < r < r₂, i a sobre s'esborren les freqüències
radials amb un filtre tangencial— perquè si no **el registre s'enganxa a la
vora lunar**, que és l'estructura més contrastada de la imatge.

### B.7 La llibreria de python: què és i què no és

És **`sunkit-image`** (0.5.1 a `~/Downloads/eclipse_venv`). **És de filtres, no
d'HDR.** A la 0.5.1: `enhance.__all__ = ["mgn"]` i
`radial.__all__ = ["fnrgf", "intensity_enhance", "set_attenuation_coefficients",
"nrgf"]`. **Cap funció d'HDR, de fusió d'exposicions ni de composició de
capes**; l'única menció d'exposició diu que «the input data array should be
normalized by the exposure time», o sigui que **dona per fet que l'HDR ja està
fet abans**. Tampoc hi ha l'ACHF ni el NAFE.

⚠️ **«Mètodes de desenfoc millors que els gaussians» no és a cap font.** La
frase no existeix enlloc del projecte, i Gemini diu el contrari: recomana els
gaussians pel seu nom i tot el seu codi de màscares és gaussià. La confusió ve
del §6.1.1 del seu traspàs, que compara l'ACHF amb el **Radial Blur / Spin de
Photoshop** —un desenfoc **rotacional**, no gaussià— citant Druckmüller 2006
(«it is blind to tangential structures»).

**I el nucli de l'ACHF ÉS un gaussià**, tesi §5.2:
`C = exp(−[(r−ρ)² + (r(φ−ϕ))²]/2σ²)`. El que el fa adaptatiu és (a) que la
convolució és **incompleta i normalitzada per w** —exclou la Lluna, la vora del
camp i «parts diferents»— i (b) que en **combina diverses σ**. Totes dues coses
ja les fem al pas alt de `research/95`.

**Conclusió: «gaussianes ben fetes» és la via correcta, i és la de Brno.**

---

## C · LES DECISIONS CONSENSUADES

Ordre nou del projecte, proposat per Pere i acordat amb els matisos de sota.

### C.0 Fase 0 · Calibració, per tren

Només informació **de l'instrument**: dark, bias, linealitat, PRNU, **flat**,
nivell de negre. **Res del cel.**

- ⛔ **el flat és una magnitud de l'espai del sensor i va ABANS de qualsevol
  warp.** El flat i el warp **no commuten**: en l'ordre actual ja no hi ha lloc
  on posar-lo, i per això `research/90` porta setmanes obert
- el nivell de negre real dels CR3 és **511–512 pla**; el de metadata de libraw
  és fals (`research/71`)
- el flat de la Sony es pot **mesurar del propi salt** (§A.5)

### C.1 Fase 1 · Registre i camp comú

Només **geometria**. Res de fotometria.

- **el camp comú és un pla tangent astromètric**, nord amunt, escala declarada
  — no la graella d'un dels dos sensors
- a l'escala fina (la de la Vixen, 2,1495 ″/px), perquè passar la Vixen a
  l'escala de la Sony **llença el 55 % dels seus píxels** i és el tren que
  porta la corona interior

⛔ **RECTIFICACIÓ (23-08, tarda): la mida que hi havia aquí era dolenta per
tres motius alhora.** Deia «26,67 × 17,88 R☉ → 11907 × 7981 px (95,0 Mpx)».

1. **No hi cabia el segon apuntament.** Vaig dimensionar amb el camp d'**un**
   apuntament. Amb els dos, la unió al marc del sensor Sony és **8202 × 6033
   px** (Codex deia 8185 × 6017: coincideixen al 0,2 %).
2. **I sobretot: amb el nord amunt, el camp és VERTICAL, no apaïsat.** El nord
   celeste cau a `pa_north = 90,271°` sobre el sensor de la Sony, o sigui a
   **0,27° de l'eix llarg**. Un llenç nord amunt posa la Sony **dreta**. Tant
   el meu 11907 × 7981 com el 12193 × 8964 que proposava Codex són **apaïsats**:
   tots dos descriuen el llenç al marc del **sensor**, que no és el que aquesta
   fase declara. Si es declara apaïsat i després es gira a nord amunt, no se'n
   perd el 13 % sinó el **34,3 %**.
3. **El radi solar era el mitjà, no el del dia.** Feia servir R☉ = 959,7″ (el
   valor a 1 UA) en lloc del radi aparent mesurat aquell dia, **947,07″**
   (`suns.json`).

**Mida correcta**, pla tangent nord amunt centrat al Sol, mostrejant tot el
perímetre dels tres camps (no només les cantonades):

| | arcsec | R☉ | px a 2,1495 ″/px |
|---|---|---|---|
| bounding box justa | 19327 × 26115 | 20,41 × 27,57 | **8992 × 12149** (109,2 Mpx) |
| amb el Sol al centre | — | 23,47 × 28,94 | **10339 × 12752** (131,8 Mpx) |

O sigui **+39 %** sobre els 95 Mpx que hi havia. La Vixen no hi pinta res per
dimensionar: hi cap sencera. **El llenç s'ha de derivar projectant el perímetre
de tots els fotogrames vàlids, mai amb dimensions escrites a mà.**
- ⛔ **el llenç el dimensiona la UNIÓ de tots els apuntaments**, no el sensor.
  Aquesta nit hem descobert que 697 px de l'apuntament desplaçat es van
  llençar en silenci
- ⛔ **un sol llenç declarat, i cap etapa posterior no el pot retallar.** Ara
  n'hi ha dos i el de Photoshop en perd el 3,4 %
- **DOS productes, no un**: la corona registra al **Sol** i la Lluna
  (earthshine, limbe, protuberàncies) registra a la **Lluna**. La Lluna es mou
  0,585 ″/s respecte del Sol: 9 px entre la primera i la quarta àncora
- la Lluna **s'emmascara abans de mesurar el registre** (§B.6)
- **problema obert**: els fotogrames curts (1/3200 als contactes) **no tenen
  estrelles**. Cal un **model de punteria en el temps** per tren, ajustat amb
  els fotogrames que sí que en tenen i interpolat als que no

### C.2 Fase 2 · Composició fotomètrica

**Es manté com a etapa amb nom propi** —Pere tenia raó i la literatura també—
però **es reanomena**: no és «unir capes en HDR», és **una sola suma ponderada
de tots els fotogrames de totes les exposicions i dels dos trens**, a l'estil
LDIC. Dins seu **no hi ha cap fusió entre trens ni entre exposicions**, i per
tant no hi pot haver cap graó de fusió.

Contra la meva proposta inicial, hi entren **dues coses de l'LDIC** que jo no
tenia:

1. **`k_i(φ)`, `q_i(φ)` per segment angular.** Una exposició no és una altra
   multiplicada per la raó de temps: hi ha un guany i un pedestal que canvien
   amb l'azimut. És el que absorbeix la llum difusa que canvia entre C2 i C3, i
   **el pont fotomètric entre la Vixen i la Sony s'ha d'ajustar PER AZIMUT, no
   amb un escalar.** ⚠️ Sospita forta: **és d'aquí que surten les estries de
   fusió del màster Vixen** (artefacte F, 1,05–1,6 R☉)
2. **`w` depèn del VALOR del píxel**: 0 al tram alt (a partir del ~85 % del
   rang, on es perd la linealitat) i 0 al tram baix, amb transicions graduals

I una cosa on **nosaltres podem anar més enllà que Brno**: ells **no ponderen
per soroll** perquè el paper de 2006 declara el **guany desconegut** com a
problema obert. **Nosaltres el tenim mesurat** (`research/75`, 38 i 22
estrelles), o sigui que podem fer `w` òptim de veritat sense perdre res del
que ells fan.

### ⛔ Dues coses que el contrast del 23-08 hi afegeix, i canvien el disseny

**1. La PSF efectiva varia amb el camp, i `k(φ), q(φ)` NO ho poden arreglar.**
Teorema d'una línia: si `f_i = T ⊛ P_i`, llavors una suma ponderada dona
`P_eff = Σ(w_i·k_i)·P_i / Σ(w_i·k_i)` — **la MTF efectiva és sempre una
combinació convexa** de les dels dos trens. `k` només mou les proporcions (i a
més ja el fixa la fotometria, no és lliure) i `q` és un pedestal que no toca cap
freqüència. **Pes que varia amb el radi ⇒ PSF que varia amb el radi.**

I la diferència és més gran del que dèiem. Als **fotogrames** (`research/75` §2,
tall de ganivet, mateix codi, desbiaixat): Vixen **5,8 ± 0,4″**, Sony
**8,3 ± 0,5″**, raó 1,40. Però a les **piles que de veritat es fusionen**,
mesurat amb estrelles dels catàlegs del 16-08: Sony **12,10″**, Vixen **6,45″**
→ raó **1,88**. I hi ha un límit dur de mostreig: un cop remostrejada al llenç
Vixen, **la capa Sony no pot portar res per sota d'un període de 6,40″**; la
Vixen arriba a 4,30″.

⚠️ Matís: **homogeneïtzar la PSF no arregla la fotometria** (convolucionar el
Vixen fins a la Sony canvia el residu creuat de 0,444 % a 0,432 %, o sigui res).
Són dos problemes separats i s'han de tractar per separat.

**2. La circularitat és real i està mesurada.** Ajustar `k, q` contra la mateixa
discrepància que després es presenta com a resolta **no és calibratge, és
absorció**: passar de 4 a 120 paràmetres millora el residu **dins** del domini
d'ajust (0,444 → 0,297 %) i l'**empitjora fora** (1,33 → **1,76 %** a 6–8 R☉).
Guanya 0,15 punts on mira i en perd 0,43 on no mira.

I `research/72` §3–4 ja ho havia dit el 15 d'agost amb altres paraules: «cada
tren té el seu halo (PSF pròpia): fusionar cossos abans de treure'l barreja
dues sistemàtiques; separar-los conserva l'acord entre cossos com a
validació». **Fusionar és gastar-se l'única prova externa que teníem.**

**Conseqüència per al disseny**: cal **reservar sectors o radis per validar**
que no entrin a l'ajust, i lliurar mapes de dominància, PSF efectiva, variància
i cobertura al costat del compost. I plantejar-se seriosament de fer **dos
compostos independents** i comparar-los, en lloc d'un de fusionat.

**El requisit dur de Pere queda satisfet, i és ortodox.** Es lliura:

- una **capa per fotograma o per grup d'exposició**, ja calibrada amb la seva
  `k(φ)` i `q(φ)`
- la seva **màscara** = el mapa de pes `w`
- i la garantia que la suma normalitzada **reprodueix exactament** el compost

Pere supervisa i retoca les màscares a Photoshop; el compost es renormalitza.
**Una sola estimació, moltes vistes.** El que desapareix no són les capes: és
la decisió arbitrària de quina exposició mana on.

### C.3 Fase 3 · Filtres

Només **presentació**: res que canviï el que la dada vol dir.

- ⛔⛔ **NORMA DEL RECTANGLE** (`research/95`): qualsevol filtre s'aplica a
  **tot el rectangle**, mai a una circumferència, o queden **halos**. L'única
  cosa que el pot aturar és que no hi hagi dada
- **gaussianes ben fetes**: convolució **normalitzada** i **multiescala**, que
  és el que fa l'ACHF (§B.7)
- els filtres van **després** de la composició, mai abans

### C.4 Fase 4 · Rebuts

Cada fase emet un manifest amb comprovacions **provades contra una entrada
dolenta coneguda**. La lliçó d'aquesta nit és que el control de costura deia
«0,000 σ» a totes les versions perquè el 85 % de la seva mostra eren zeros
exactes. **Un control que no pot fallar no és un control.**

### C.5 La regla que decideix on va cada cosa

La frontera entre fases la defineix **quina informació hi entra**, no quina
eina es fa servir:

| fase | informació que hi entra |
|---|---|
| **0** Calibració | només l'instrument. Res del cel |
| **1** Registre | astrometria per fotograma → camp comú. Res de fotometria |
| **2** Composició | una sola suma ponderada al camp comú. Res d'estètica |
| **3** Filtres | res que canviï el que la dada vol dir |

---

## D · QUEDA OBERT PER DEMÀ

1. ~~Executar l'autocalibració del flat~~ **FET el 23-08** (§A.5 bis): és
   vinyetatge, demostrat per tres vies. El que queda obert d'aquí és **el
   pedestal** (el pendent creix amb el nivell a radi fix) i **el signe del graó
   al compost**, que no quadra amb el de la parella.
2. **El model de punteria en el temps** per als fotogrames sense estrelles
   (§C.1).
3. **Com es lliuren les capes a Photoshop** perquè la suma sigui exacta i
   reversible: format, normalització, i com es torna del PSB al lineal.
4. Si el camp comú ha de ser **un** o **dos** (Sol i Lluna) també a Photoshop,
   o només al pipeline.

5. **Repetir la descomposició amb els deu fotogrames**, no només amb la parella
   de 8 s: cadascun té el seu Δt i la seva aportació de cel.
6. **Mesurar la PSF de les piles amb el rigor de `research/75` §2** (tall de
   ganivet, mateix codi) en lloc dels catàlegs d'estrelles: la raó real de
   treball és entre 1,4 i 1,9 i cal saber-la.
7. **Com es reserven sectors de validació** perquè l'ajust entre trens no sigui
   circular.
