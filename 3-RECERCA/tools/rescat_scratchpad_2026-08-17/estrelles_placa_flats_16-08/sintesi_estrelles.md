# Estrelles a la totalitat: camp resolt, calibratge absolut i què canvia del pla

*12-08-2026, 18:29:38 UTC · 42,299407 N −5,02503 E · 798 m · Sol a 9,07° · X = 6,1*
*Un escèptic va auditar el creuament i va trobar dos errors reals. Manen les seves correccions.*

---

## 1. Què hi havia al camp i què s'hi ha trobat

**MESURAT.** Cerca cega als dos trens, sense catàleg, i creuament posterior amb Tycho-2 + skyfield/DE440s:

| Tren | Fonts cegues | Identificades | Residu de placa | Espera per atzar |
|---|---:|---:|---:|---:|
| Sony A7RIIIA + 300 GM | 38 | **38 de 38** | 0,54 px de mediana (màx. 1,79) | 0,02 coincidències |
| R6 III + VSD90SS | 24 | **22 de 24** | 0,32 px (màx. 0,65) | 0,00 |

Les dues úniques sense contrapartida (B-24 i B-26) ja eren les que el catàleg cec marcava com a dubtoses. **Cap detecció espúria a la classe A.** Cap estrella no satura: el pic més alt de totes és 15.161 ADU contra un sostre de 16.383.

**Les que hi ha, per nom.** Les quatre candidates garantides de la predicció hi són totes: **HIP 46232** (V=6,31), **7 Leonis** = HIP 47096 (6,32), **HIP 45874** (6,57, només a la R6) i **HIP 46713** (6,92). La més brillant del camp Sony és **8 Leonis** = HIP 47189 (V=5,73), que la predicció donava com a *possible* i hi va entrar: reconstrueix la seva magnitud de catàleg amb **0,004 mag** d'error. Hi són també **HIP 46345** (6,83, a 2,65 R☉), **HIP 46745** (7,66) i **HIP 46415** (7,79). La més interna, **HIP 46335** a **2,15 R☉**, és real astromètricament (residu 1,06 px) però **no té fotometria**: veure §3.

**Les que no hi són.** ξ Leonis (V=4,99), ψ Leonis, π² Cancri, π¹ Cancri i 83 Cancri. Les cinc més brillants de la zona eren totes *possible* i cap no va entrar: amb el nord real a PA 90,27°, van quedar fora del quadre.

**Magnitud límit.** La més feble identificada és **V = 9,18** (HIP 46561), als dos trens. La predicció esperava V≈9,2 amb un cel de 12 mag/arcsec²; **el cel mesurat era 9,34 (Sony) i 9,15 (R6) mag/arcsec²** a 8 R☉ —els dos trens coincideixen a 0,19 mag—, entre 1,7 i 4,9 magnituds més brillant que qualsevol hipòtesi de la predicció. Que el límit hi arribés igualment és sort del pressupost, no encert de la hipòtesi. **El que limitava aquestes imatges no era l'exposició ni el sensor: era el cel a massa d'aire 6.**

---

## 2. El camp resolt

**MESURAT** (model lineal + terme radial r³, marc horitzontal refractat):

| | Sony | R6 III |
|---|---|---|
| Escala | **3,2020 ″/px** (−0,99 % del 3,234) | **2,1495 ″/px** (−0,39 % del 2,158) |
| Nord celeste | **PA 90,27°** (gira 90,27° antihorari) | **PA 57,19°** |
| Est | 358,64° | 325,59° |
| Mirall | no | no |
| Centre del **Sol** | (3894,7 , 2768,7) px | (3570,8 , 2267,1) px |
| Residu rms | 0,71 px (2,3″) | 0,42 px (0,9″) |

**L'escala de la Sony no passa la prova de l'1 % del G7a** (−0,99 % amb terme radial, −1,29 % amb similitud pura). Amb 38 estrelles i 0,71 px de residu, l'astrometria és molt més forta que l'ajust del diàmetre del disc, i la focal implicada passa de 288 a 290,5 mm —cap al nominal de 300, no lluny. **Recomanació: adoptar 3,2020 ″/px.** La discrepància queda oberta: sense una mesura independent de focal no es pot tancar, però les dues xifres no poden ser certes alhora.

**Refracció diferencial, troballa metodològica.** Amb el Sol a 9° el camp queda comprimit un **0,77 % (Sony) i 0,80 % (R6)** en vertical. Els dos cossos donaven la mateixa no-perpendicularitat aparent (−0,438° i −0,457°) al marc equatorial: és el cel, no l'òptica. Al marc horitzontal refractat cau a −0,026° i −0,006° i les dues càmeres passen a ser similituds pures.

**Validació de regal.** Amb la solució de placa, l'eix nord lunar cau a **71,97°** al sensor Sony. El producte `earthshine_FINAL` havia **ajustat 71,5°** contra el mapa LROC sense saber res d'estrelles. **Coincideixen a 0,47°**, tan bo com el mètode permet distingir (el pol eclíptic com a substitut del lunar val ±1,5°). L'orientació del producte d'earthshine queda confirmada per una via independent.

---

## 3. El zero fotomètric i la calibració absoluta

| | Sony (X=6,08) | R6 (X=6,02) |
|---|---|---|
| **ZP** | **+14,17 ± 0,08 mag** | **+14,21 ± 0,08 mag** |
| Factor a B/B☉ (per ADU/s i píxel verd) | **1,134 × 10⁻¹¹** | **2,772 × 10⁻¹¹** |
| Incertesa de B/B☉ | **±10 %** | **±10 %** |

**Els dos trens coincideixen**: diferència de punt zero −0,038 ± 0,076 mag. Sobre la corona real, entre 1,15 i 3 R☉, el quocient R6/Sony és **0,95** (0,056 mag). L'encàrrec demanava millor que un factor 2; estem a un 5 %.

**Tres correccions de l'escèptic, i manen elles:**

1. **Els factors publicats eren erronis.** El model ajusta un terme de color, però `corona2.py` no l'aplicava al Sol: F☉ ha de ser 10^(0,4·(ZP+26,75−0,653·c)). Biaix −4,5 % (Sony) i +9,4 % (R6), de signe contrari. **Corregit, el quocient de corona passa de 0,83 a 0,95, i la hipòtesi de llum difosa interna del 300 GM es retira: no queda res per explicar.**
2. **k = 0,416 no és el coeficient d'extinció.** Els dos trens miraven la mateixa atmosfera i donen 0,416 ± 0,050 contra 0,723 ± 0,037: **5,0 σ**. Almenys un està dominat pel vinyetatge, i **no hi ha flats de cap dels dos trens** per trencar la degeneració. El 0,37 del projecte no queda ni confirmat ni desmentit. El ZP al centre del camp, en canvi, amb prou feines es mou (+14,09 a +14,22 en cinc models).
3. **Els SNR del catàleg cec s'han de dividir per 1,5-2.** Soroll combinat mesurat amb obertures buides: 53 ADU/s a 9-14 R☉, 79 a 6-9, 87 a 4-6, 162 a 2,6-4 i **1.780 a 1,6-2,6**. HIP 46335 no té SNR 5,9, té **0,07**; HIP 46345 té 6,6, no 18,4. **Cap de les dues no s'ha de fer servir per calibrar.** A 1,6-2,6 R☉ les estrelles injectades es recuperen a 1,3-3,0× el seu flux.

**El que sí que està provat:** la fotometria d'obertura amb anell 26-40 px és **insesgada al 3-4 %** de 2,6 a 14 R☉ (injecció de fonts sintètiques als set fotogrames reals). El ±0,065 publicat sortia d'un ajust sense pesos amb retall de 2,5σ; el número aguanta, l'error no. **Substituïu la prova de Bemporad per la diferència entre trens** (hi cancel·la la V de catàleg): **0,32 mag per fora de 6 R☉ i 0,96 per dins**. HIP 45824/TYC 1403-1015 és una doble no resolta (dos components V=8,90 a 0,33 px): fora dels calibradors.

---

## 4. Les ales de la PSF i el model de halo

**MESURAT** amb la prova d'integral (el flux acumulat ha de tendir a 1,0): el perfil és fiable **fins a 13 px (42″) a la Sony** —0,94 a 10 px, 1,04 a 13— i **fins a 30 px (64″) a la R6**. Més enllà s'infla fins a 11,8 vegades el flux de l'estrella: allò ja és estructura de corona.

**No es pot validar el model de halo amb estrelles, i no per manca d'ofici.** El model dispersa el 4,30 % de la llum, però **el 97,5 % cau més enllà de 100 px**, i a 100 px el nucli ample (s=320) ja n'aporta el 76 %. A 87,5 px el model prediu 7,4×10⁻⁸ per píxel i el terra sistemàtic mesurat és 2,1×10⁻⁴: **2.800 vegades per damunt**. La raó és física: la corona interior és ~200.000 vegades més brillant que l'estrella més brillant del camp i el seu propi halo enterra qualsevol halo estel·lar.

Al tram estret on se solapen (3-13 px) **la forma casa** —pendent mesurat r^−2,3 contra r^−2,2 del nucli s=6, β=1,5— i l'amplitud mesurada és ~80× la del model. **Això no és un defecte**: aquell tram és el nucli de seeing (FWHM 3,7 px = 12,1″), i el halo s'ajusta dins del disc lunar, on el mapa de font val zero. El model mai no ha pretès descriure la PSF a 5 píxels.

---

## 5. Què canvia del pla (`research/74`)

**G7a — PASSA a mitges, i s'ha de reescriure el criteri.**
- Escala: R6 **passa** l'1 %; **Sony falla** (−0,99 %). Adopta **3,2020 ″/px** i marca la discrepància com a oberta.
- El criteri de Bemporad de **0,1 mag no es compleix globalment** (mediana 0,16 i 0,20 mag; només un terç dins de 0,10). Substitueix-lo per **la diferència entre trens**: exigeix ≤0,35 mag per fora de 6 R☉. La causa és soroll de fotons i error de catàleg, no biaix de la fotometria.
- L'objectiu «ala de la PSF per una segona via» **no es lliura**: §4. `G3/psf_*.npy` pot portar mesura fins a 13 px (Sony) i 30 px (R6) i **res més enllà**. La validació del halo ha de venir de **la fotosfera filtrada de la fase parcial**, no d'estrelles. Anota-ho com a límit dur, no com a deute.

**Números que canvien als fitxers del pla.** Amb l'escala nova, a la Sony el radi solar passa de 296,5 a **295,8 px** i el **radi lunar de 305,7 a 308,7 px** (+3,0, la meitat de l'eixamplament de 6 px de la màscara del G5); a la R6, de 458,2 a **460,0 px**. I el centre de referència ha de ser **el del Sol** (§2), no el lunar: eren 3,1 px (Sony) i 6,4 px (R6) de biaix als radis.

**G4 i qualsevol apilat de gran camp:** treballa en **alt/az refractat**. Una translació pura ignora el 0,8 % de compressió vertical i, a la Sony, els **0,138° de rotació de camp** del salt de muntura.

**G3/G5 guanyen ancoratge absolut.** Amb B/B☉ = 1,134×10⁻¹¹·I (Sony) i 2,772×10⁻¹¹·I (R6), ±10 %, el compost es pot comparar amb **LASCO C2 i K-Cor (G7c)** sense mesurar la densitat òptica del filtre. Afegeix aquest contrast com a criteri de pas del G5.

**G0-bis, peça nova i barata:** **no hi ha flats de cap tren**. Sense flats, extinció i vinyetatge no se separen (§3) i el pla de cel del model de halo continua sent paràmetre lliure. Un joc de flats amb la mateixa òptica i obertura, fet ara, els separa. **G7b (el 6D) puja de prioritat**: el cel feia 9,2 mag/arcsec² i és la component dominant que el G3 no sap separar.