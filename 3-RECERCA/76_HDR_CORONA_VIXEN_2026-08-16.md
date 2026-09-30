# 76 — Primer HDR de la corona amb el tren Vixen

**16 d'agost de 2026 · evidència mesurada sobre els CR3 de la totalitat**

Primera composició HDR de la corona solar del projecte. Tren Vixen VSD90SS +
Canon R6 Mark III, eclipsi del 12 d'agost de 2026 des de MIRADOR FINAL 2.

Eina: `research/tools/hdr_corona_vixen.py` (etapes `geometria` → `deriva` →
`escala` → `hdr` → `vis`) i `research/tools/masters_vixen_v2.py`.
Sortida: `~/Desktop/Eclipse 2026/Corona_HDR_Vixen/`.

Marcatge: **MESURAT** (sobre els fitxers) · **INFERIT** · **PENDENT**.

---

## 1. Què s'ha compost

**MESURAT.** Dels 124 CR3 de `Vixen Unfiltered`, **68 cauen dins la totalitat**
—de C2 real a C3 real, 103,7 s— i són els que entren. Els altres 56 (22 abans
de C2 i 34 després de C3) porten fotosfera i queden fora: allà la referència no
és corona sinó un creixent, i la seva llum difusa ho inunda tot.

| | |
|---|---|
| Fotogrames | **68** |
| Exposicions úniques | **15**, de 1/3200 a 10,3 s = **15,0 EV** |
| Reixa de sortida | 6958 × 4638, **2,1495 ″/px**, centrada al **Sol** |
| Aportacions per píxel (1,05–6,0 R☉) | mediana **294** |
| Píxels sense dada | 112.699, tots sota el disc lunar de tots els fotogrames |
| Temps de càlcul | 45 s la composició, 2 min els masters |

L'EXIF de la R6 marca **l'inici** de l'exposició, no el final. Es comprova sol:
amb el final, els dos fotogrames consecutius de 2 s se solaparien en el temps.
⚠️ Als dos cossos Sony és a l'inrevés (`CLAUDE.md` §7).

---

## 2. La deriva de la corona no és la deriva de les estrelles

⛔ **Aquesta és la troballa que canvia un número publicat.** `research/75` §5.4
mesura la deriva del Vixen en **0,610 ± 0,010 ″/s** per dos camins independents,
tots dos **estel·lars**: el moviment de les estrelles fotograma a fotograma i la
llargada del seu traç dins de cada exposició de 10,3 s.

**La corona no va a aquella velocitat.** Mesurada aquí per dos camins també
independents:

| Camí | ″/s | direcció al sensor |
|---|---:|---:|
| Limbe lunar + efemèride Lluna−Sol (skyfield/DE440s) | **0,5764** | +47,5° |
| **Correlació de fase de la corona**, 5 parelles de 60–80 s | **0,5781** | +46,5° |
| Estrelles (`research/75`) | 0,610 | 45,0° |

Els dos camins d'aquí coincideixen al **0,3 %**, i el residu de la correlació
contra el model d'efemèrides és de **0,11 px en x i 0,08 px en y**.

**La diferència és física i té el valor exacte que ha de tenir:** el Sol es mou
sobre el fons estel·lar a **0,041 ″/s** (360° en un any). La muntura anava a
taxa solar, o sigui que segueix el Sol i no les estrelles; la diferència
mesurada entre les dues derives és de 0,032 ″/s, dins d'aquell número segons
l'angle.

⚠️ **Conseqüència operativa:** alinear la corona amb la deriva estel·lar
l'hauria escombrada **3,4 px sobre els 103,7 s**, que és més que el FWHM de
5,8 ″ = 2,7 px. La pila que s'apila al Sol ha de fer servir 0,578 ″/s.

**El flare fix del sensor existeix i s'ha vist**, tal com avisava `research/74`
R5. Els esglaons amb el nucli cremat —0,5 s, 1 s, 2 s i 10,3 s— donen el màxim
de correlació a desplaçament **exactament zero en coordenades de sensor**: allà
no queda estructura de corona per guiar i la correlació s'enganxa al patró fix.
Els cinc parells bons són els de 1/15, 1/8 i 1/4, que tenen estructura i el
nucli sencer.

**Ancoratge absolut.** La traça relativa surt del limbe i de l'efemèride, però
el zero el posa la placa estel·lar de `research/75` §5.1 (22 estrelles, residu
0,32 px). Sense això el centre queda **3,64 px desplaçat** i tots els radis en
R☉ n'hereten el biaix.

---

## 3. La gota del drizzle: 2,0 píxels de sortida, ni un menys

**MESURAT, i és una lliçó de mètode.** El `pixfrac` clàssic de Fruchter i Hook
es mesura en píxels **d'entrada**. Aquí un píxel d'un pla de Bayer fa **dos**
píxels de sortida, o sigui que una gota de 0,62 px de sortida és un pixfrac de
0,31: molt més agressiva del que sembla.

Amb gota petita apareix un **escaquer a la diagonal de Nyquist** (període
1,41 px) que domina l'espectre, i el realçat el converteix en una textura
d'espiga sobre tot el fons. La causa és de recompte: G1 i G2 cauen a les
caselles de paritat senar i R i B a les parelles, i les que reben la gota de ple
queden nítides mentre que les altres només en toquen la cua. La cobertura ho
canta: **89 i 94 aportacions alternades**.

| Gota (px de sortida) | escaquer / potència mitjana | soroll del cel |
|---:|---:|---:|
| 0,62 | 818.343 × | 9,24 ADU/s |
| 1,00 | 168.707 × | 6,87 |
| 1,35 | 33.843 × | 6,32 |
| 1,70 | 5.620 × | 6,17 |
| **2,00** | **0 ×** | **6,12** |

**2,00 és l'única amplada que dona partició de la unitat sobre una reixa de
període 2**, i per això l'escaquer surt exactament zero i no aproximadament
zero. Qualsevol altre valor —més gran també— torna a deixar-ne.

**El cost és petit i està mesurat.** Espectre azimutal en un anell a 1,35 R☉,
que no té gradient radial, raó 2,0 contra 0,62:

| Període angular | 32 px | 16 px | 8 px | 4 px | 2,5 px |
|---|---:|---:|---:|---:|---:|
| Potència conservada | 0,97 | 0,79 | 0,43 | 0,31 | 0,17 |

⚠️ **Les caigudes de sota de 8 px són soroll que marxa, no senyal que es perd.**
A 0,62 la potència **puja** en anar de 4 px a 2,5 px, i un senyal real amb un
FWHM de 5,8 ″ = 2,7 px no pot fer això: allà baix només hi ha escaquer i soroll.
La MTF de la caixa de 2 px explica 0,99 i 0,95 a 32 i 16 px; la resta de la
caiguda a 16 px és soroll. El soroll del cel baixa un **34 %**.

**PENDENT:** el nucli del drizzle és conegut i analític, o sigui que la MTF que
costa es pot recuperar per deconvolució. És el camí natural cap a la decisió D3
de `research/74`.

---

## 4. Calibratge relatiu de les quinze exposicions

L'obturació nominal no és la real i un error d'un 5 % entre esglaons deixa
anells al compost. **Dues coses que s'han hagut de corregir per arribar-hi:**

**1. Encadenar raons entre esglaons veïns és un passeig aleatori.** Catorze
graons amb un 2-3 % d'error cadascun donen **0,91 a l'esglaó de 10,3 s**, i
aquell número és soroll acumulat, no obturador. Se substitueix per un **ajust
global**: tots els esglaons contra el mateix perfil de corona, amb el fons difús
de cada fotograma com a paràmetre propi, iterat fins a convergir. Els factors
que en surten queden dins de **±7 %** i no acumulen.

**2. Una sola raó confon l'obturador amb el cel.** Per a cada parella s'ajusta
`p_b = k·p_a + c`: el pendent és la raó d'exposició i l'ordenada a l'origen
absorbeix la diferència de fons difús, que és el que pesa justament allà on
viuen els esglaons llargs. Sense el terme independent, la raó 1/3200→1/2000
sortia 0,80.

⚠️ **Els fotogrames de 1/3200 no tenen centre lunar mesurable** —les perles i
l'anell de diamant fan malbé el limbe—, i són 26 dels 68. La màscara lunar de
tots els fotogrames ha de sortir del **model** de deriva, no de la mesura.

---

## 5. El que ha sortit

### 5.1 Fotometria absoluta, i quadra amb el llibre

Amb el factor de `research/75` §5.2 —B/B☉ = 2,772×10⁻¹¹ per ADU/s, ±10 %—:

| R☉ | ADU/s | B/B☉ |
|---|---:|---:|
| 1,02 | 118.853 | **3,3 × 10⁻⁶** |
| 1,10 | 47.766 | 1,3 × 10⁻⁶ |
| 1,50 | 4.937 | 1,4 × 10⁻⁷ |
| 2,00 | 809 | 2,2 × 10⁻⁸ |
| 3,00 | 175 | 4,9 × 10⁻⁹ |
| 5,00 | 37 | 1,0 × 10⁻⁹ |

**És el perfil K+F de manual sense haver-hi tocat res**: cap ajust, cap
normalització a una referència externa, i el resultat cau on la corona ha de
caure a cada alçada. Aquesta és la millor validació independent que hi ha de la
cadena sencera —masters, linealitat, escala relativa i calibratge absolut.

### 5.2 Continuïtat: criteri 2 del G5 superat

Desviació del perfil radial contra la seva tendència local en log(r)-log(I):
**mitjana 0,08 %, màxima 0,77 % a 1,93 R☉**, contra el **3 %** que demana el
pla. No hi ha anells de composició visibles.

⚠️ El màxim cau a 1,93 R☉ i l'esglaó de 10,3 s satura per sota de 1,96 R☉: el
graó residual, encara que sigui petit, és el de l'esglaó profund.

⛔ **Trampa de mètode, i és fàcil de repetir:** amb una mitjana mòbil en lloc
d'un ajust quadràtic local, aquest mateix criteri donava **11,4 %** a 1,15 R☉.
No era cap graó: era la curvatura del perfil, que és on més gira.

### 5.3 El límit no és el sensor: és el cel

El cel de la totalitat val **283 ADU/s** de constant més un gradient d'**1,2 %
per R☉**, i **no és radialment simètric** —depèn de la distància a la vora de
l'ombra—. La corona iguala el cel cap als **3 R☉**. Coincideix amb els 9,15
mag/arcsec² que `research/75` §5 va mesurar per una altra via.

Per a la visualització es resta constant **més pla inclinat**. Un pla no pot
absorbir una corona radialment simètrica, o sigui que és la resta més segura que
hi ha. **No és el model de halo:** el G3 continua obert.

---

## 5 bis. Els anells concèntrics: d'on surten i com es treuen

**Afegit el 16-08 al vespre.** La primera versió del compost tenia **arcs
concèntrics al Sol** que travessaven els serpentins entre 1,3 i 2,5 R☉. Pere els
va veure de seguida. Es van atacar amb sis hipòtesis independents provades en
paral·lel més mesures pròpies.

### La causa: el cel de la totalitat no és estacionari

**MESURAT.** La taxa de fons del Vixen, mesurada fotograma a fotograma a
5,4–6,4 R☉ i dividida pel temps d'exposició, fa una **V**:

| C2+ | 8 s | 26 s | 46 s | 70 s | 92 s |
|---|---:|---:|---:|---:|---:|
| Fons (ADU/s) | **509** | 414 | 367 | **335** | **491** |

És física i té sentit: prop de C2 i de C3 el punt d'observació és a tocar de la
vora de l'ombra i el cel hi és més clar; al mig de la totalitat, més fosc. La
variació total és de **±20 %**.

**I aquí ve el mecanisme.** Cada radi del compost el domina un esglaó
d'exposició diferent, perquè els esglaons llargs saturen a prop del Sol i només
sobreviuen enfora. Les fronteres estan calculades i mesurades:

| Esglaó | 1/8 s | 1/4 s | 1/2 s | 1 s | 2 s | **10,3 s** |
|---|---:|---:|---:|---:|---:|---:|
| Satura per sota de | 1,03 | 1,09 | 1,18 | **1,30** | **1,44** | **1,96 R☉** |

Cada esglaó es va prendre en un instant diferent, o sigui amb un cel diferent.
**El compost portava un nivell de cel diferent a cada radi, i el salt era a la
frontera.** Els tres fotogrames de 10,3 s cauen tots al fons de la V —el cel
més fosc de tota la totalitat—, i per això l'arc més gros era el seu, a 1,96 R☉.

⚠️ **Les fronteres no són cercles: són isofotes.** Per això surten com a arcs
que **tallen** els serpentins i no com a anells perfectes. La frontera del
10,3 s escombra de 1,60 a 2,20 R☉ segons l'azimut.

### Els quatre amplificadors

Cap no és la causa, però tots multiplicaven el graó:

1. **Els factors d'escala relativa.** El multiplicaven per **1,63**. I no eren
   obturador: un cos amb obturador electrònic i rellotge de quars no falla un
   7 %. Eren **la mateixa variació del cel** colada dins la separació k/c de
   l'ajust — dins d'un mateix esglaó, on l'obturador ha de ser constant, el
   factor variava fins a un **8,1 %** i correlacionava amb el temps (r = −0,60).
   ⛔ Es retiren: `ESCALA_UNITAT=1` passa a ser el valor per defecte.
2. **La rampa de sortida per saturació.** Amb 0,25 el graó a 1,93 R☉ val
   1,567 %; amb 0,80, **0,655 %**; amb tall dur, 3,319 %. Resposta a la dosi
   monòtona. Passa a **0,80**.
3. **La mediana per anell de `perfil_azimutal`.** Sobre desenes de milers de
   píxels salta d'un valor a l'altre entre anells veïns i el quocient se'n
   queda els graons. Passa a **mitjana**. ⚠️ El suavitzat de 17 taps **sí que
   s'ha de conservar**: treure'l empitjora els anells un 36 %.
4. **El realçat multiescala.** Divideix per la desviació local, o sigui que
   allà on la corona és llisa converteix un graó instrumental del 0,5 % en
   contrast ple. És l'amplificador final, i per això els arcs es veien al
   producte realçat i quasi no al lineal.

### El que NO era

- ⛔ **No era el registre.** El model de deriva és bo a **0,06 px entre
  esglaons** i 0,27 px sobre la totalitat sencera. Hipòtesi descartada amb
  mesura.
- ⛔ **No era el model de fons de la visualització ni els salts de cobertura**,
  excepte en una franja de 1,015 a 1,09 R☉, on la màscara lunar de tall dur sí
  que deixava un anell del 20 % perquè la Lluna es desplaça 11 px respecte del
  Sol. Corregit amb una màscara suau de 14 px de transició.
- ⛔ **No eren vores rectes.** A l'estirament dur semblava que n'hi hagués; el
  test objectiu de gradient per files i columnes només troba senyal al limbe
  lunar (1,03 R☉). Era un miratge del contrast.

### El resultat

Desviació del perfil radial contra la seva tendència local:

| Versió | mitjana | màxima |
|---|---:|---:|
| Inicial | 0,086 % | **1,567 %** a 1,93 R☉ |
| Fons anivellat | 0,069 % | 0,846 % |
| **Totes les correccions** | **0,02 %** | **0,24 %** a 1,10 R☉ |

Els arcs han desaparegut de la imatge. El compost antic es conserva com a
`hdr_vixen_*_v1_sense_correccions.npy`.

---

## 5 ter. El color, i per què la corona surt daurada

**No és una gradació: és l'atmosfera.** Amb el Sol a 9° i massa d'aire 6,4, el
blau queda extingit. El color cru mesurat de la corona és **R/G = 0,816 i
B/G = 0,361**, i amb el blanc D65 de la matriu de la càmera surt un taronja de
posta (sRGB lineal 1,97 · 1 · 0,21).

**El balanç de blancs bo es mesura sobre la mateixa corona**, a 1,1–1,3 R☉:
`WB = 1,226 · 1 · 2,768`. No és maquillatge: la corona K és dispersió Thomson
del continu fotosfèric i la F és pols, o sigui que **el seu color intrínsec és
el del Sol**, i fer-la neutra és calibrar contra el Sol.

✅ **Validació que no s'havia buscat:** amb aquell balanç ajustat només a
1,1–1,3 R☉, el color a **1,5–2,5 R☉** surt **R/G = 1,011 i B/G = 0,949**. La
corona és del mateix color a totes les alçades, que és el que ha de ser.

⚠️ **S'ha de mesurar a prop del limbe.** A 2,6–3,4 R☉ el resultat depèn del cel
restat i es dispara.

**Sobre l'estètica del `POWAAAH3.tif`**, que era la referència demanada:
el **84 % de la seva corona està cremat a blanc pur** —tot el que hi ha dins de
**1,84 R☉**— i el daurat viu només a l'anell de 1,86 a ~3,2 R☉, amb una
finestra de senyal de **1,9 EV**. Del seu aspecte se n'ha copiat el **color**
(R/G = 1,55 i B/G = 0,45 en sRGB lineal, mesurats a l'anell no cremat, i el cel
blau aixecat), però **no la corba**: aplicar-la cremaria tot el que hi ha dins
de 1,84 R☉, que és justament el que aquest HDR existeix per evitar.

⛔ **El factor de guany del blau (5,08/4,33) NO s'ha d'aplicar al color.** Els
multiplicadors de balanç i la matriu estan calibrats en ADU, no en electrons.
Provat contra el JPEG que el propi cos va generar de `572A2906`: sense el
factor, el camí el reprodueix a **0,031 EV**; amb el factor, el blau se'n va
**0,35 EV**. El 4,33 només val per al model de soroll dels pesos.

---

## 5 quater. Les línies radials són corona, no defecte

**17 d'agost.** Pere va marcar en vermell unes línies radials primes i
rectíssimes que surten del limbe, i les donava per artefacte. **No ho són.**
Tres agents independents van provar tres hipòtesis i les dues d'artefacte van
caure amb mesura.

**La prova decisiva és de centratge.** Es filtra el pla verd cru menys el
master de fosc, dividit pel perfil azimutal, a escales angulars de menys de 3°,
i es correlaciona el fotograma de referència amb altres presos fins a **80,6 s
més tard**, quan el Sol ja s'ha desplaçat 16–22 px al sensor:

| Centrat a | Correlació | Desfasament |
|---|---:|---:|
| **el SOL** | **0,853 – 0,952** | **+0,00 a +0,06°** |
| la Lluna | 0,617 – 0,725 | |
| un punt fix del sensor | 0,533 – 0,589 | |

Les línies segueixen el Sol. Van d'1,03 a 1,98 R☉, el seu angle de posició
només deriva 0,95–1,64° de punta a punta, i cauen a **77,1° · 86,9° · 93,1° ·
264,3° · 273,2°**.

**Dues confirmacions independents:**

- ⛔ **No són la màscara lunar.** Recomposant amb la màscara 3,5× més ampla i
  amb la màscara treta del tot, el compost surt **bit a bit idèntic** entre
  1,20 i 1,75 R☉ (rms 0,0000 %), que és on viu més del 93 % de la seva
  llargada.
- ⛔ **No les fabrica el realçat.** Un control sintètic —camp pla, el soroll
  real per píxel i el disc lunar farcit exactament com fa el codi— passat pel
  mateix filtre dona una coherència radial de **0,001**. Sobre les dades de
  veritat val 0,70–0,80 al realçat i **0,96 al compost lineal**: les línies ja
  hi són abans de tocar cap filtre. I amb cinc jocs de sigmes diferents cap
  raig no es mou de lloc.

✅ **Són rajos coronals fins, resolts.** No s'han de treure, i qualsevol
suavitzat per damunt de σ = 1,5 px començaria a menjar-se'ls: la cresta més
prima fa 6,9 px d'amplada. L'antialiàsing de 0,9 px del nivell «suau» hi queda
per sota.

---

## 5 quinquies. L'aspecte «robòtic»: realçar per sota del límit òptic

Pere ho va descriure exacte: *«com si a la realitat li haguessis tret el filtre
antialiàsing»*. I té un número que ho explica.

El tren té un **FWHM de 5,8 ″ = 2,70 px**, o sigui una σ de PSF d'**1,15 px**.
**Per sota d'això no hi pot haver res real.** El realçat de la primera versió
treballava a σ = **1,25 i 2,5 px** —per sota i just al límit— i allà només hi
ha soroll i la textura correlacionada del drizzle, que el filtre estirava fins
al mateix contrast que la corona.

Es defineixen tres nivells, i el criteri és físic: **les escales comencen per
damunt de 2× la σ de la PSF**.

| Nivell | σ (px) | k | mescla | antialiàsing | cruixent sub-resolució |
|---|---|---:|---:|---:|---:|
| fort (l'antic) | 2,5 … 80 | 0,70 | 45 % | — | 0,0306 |
| mitjà | 4 … 64 | 0,60 | 35 % | — | 0,0229 |
| **suau** (per defecte) | **6 … 64** | **0,50** | **28 %** | **0,9 px** | **0,0122** |

El cruixent baixa **2,5 vegades** i els serpentins hi són tots: no es perd cap
estructura per damunt del límit òptic perquè no se'n toca cap escala.

---

## 5 sexies. Els zeros de la vora i el gradient

**Els zeros.** `corona_vixen_FINAL.tif` tenia **3.893 píxels a zero exacte** al
vermell i **14.041** al blau, i qualsevol eina de gradient hi divideix per zero.
Dues causes i dues correccions:

1. **La vora morta.** La reixa de sortida està centrada al **Sol**, que al
   fotograma queia 83–102 px a la dreta i 43–63 px avall del centre. Resultat:
   **41 files mortes a dalt i 84 columnes mortes a la dreta**, sense cap
   aportació. Es retalla a `y 45..4633, x 4..6869` → 6866×4589 px, **zero
   píxels sense dada**, i es perden **0,10 R☉** de camp.
2. **La cromaticitat negativa.** Allà on el senyal creua el zero, la
   cromaticitat regularitzada pot sortir negativa i el retall a [0,1] deixava
   zeros escampats. S'hi posa un terra al 22 % del pedestal de cel.

⚠️ **I el gradient de fons: la major part és LA CORONA.** El perfil cau de
118.853 ADU/s a 1,02 R☉ a 37 a 5 R☉ com una llei de potència, i el cel només hi
posa 283 ADU/s amb un gradient d'1,2 % per R☉. Una eina d'extracció de gradient
que vegi aquella caiguda com a «fons» **se't menja la corona**. El que sí que
té sentit treure és el pla de cel, i això ja està fet a l'etapa `tiff`.

---

## 5 septies. El walking noise és PRNU, i no és rebuig d'atípics

Pere va marcar en verd uns traços diagonals curts al fons. Són **walking
noise**, i la seva causa està mesurada:

| Mesura | Valor | Predicció |
|---|---:|---:|
| Angle dels traços | **46,74° ± 1,50°** | deriva a 46,5–47,6° |
| Llargada mediana | **7,22 px** | 7,10 px entre el primer i l'últim 10,3 s |
| Pics de l'autocorrelació | 3,50 i 6,75–7,00 px | salts de 3,51 · 3,60 · 7,10 px |

⛔ **No són píxels calents.** La correlació del patró fix amb el mapa de calents
del master és **+0,008**, la curtosi val **3,14** —gaussià, o sigui de TOTS els
píxels i no d'uns quants— i el patró **escala amb el senyal**: és
**multiplicatiu**. És el **PRNU** del sensor.

Els tres fotogrames de 10,3 s hi posen el **74,8 % del pes i el 88,5 % de la
variància**: recomponent sense ells, el pic de 7,0 px desapareix (0,3 %).

⛔ **I el rebuig d'atípics NO ho arregla**, que és la correcció que semblava
òbvia. Provat amb k = 5, 4 i 3 sobre 2.088 milions de mostres: l'anisotropia del
soroll passa de **+0,0888 a +0,0887** a k=4. El rebuig treu píxels dolents
aïllats (−7 % als vint pitjors) i prou.

**La correcció bona és un mapa de guany píxel a píxel** (`research/tools/prnu_vixen.py`),
mesurat a les pròpies dades i aplicat a `calibra()` dividint per (1 + mapa).

⛔ **Esmena del 17-08 (research/78 §8): aquell mapa v1 portava LES ESTRELLES.**
Sense cap rebuig, cada estrella dels fotogrames llargs hi deixava una filera de
bonys de +0,04 a +0,135 al llarg de la seva traça de deriva, i en dividir-hi
sortien clots foscos en diagonal al costat de cada estrella (−6 %) i el pic
de l'estrella perdia fins a un 10 %. El mapa és ara el v2, amb màscara
d'estrelles i rebuig robust, i el compost s'ha refet amb ell; el v1 queda com
a `prnu_v1_amb_estrelles.npz`.

✅ **Validat amb font independent:** un mapa fet amb la **fotosfera filtrada**
de les parcials correlaciona **r = 0,21** (n = 139.000 px) amb un mapa fet amb
la **corona**. Escenes, instants i exposicions diferents: el patró és del
sensor. El PRNU real que en surt és de **1,3 % al verd i 1,5-1,6 % al vermell i
al blau**.

⚠️ `research/75` §4 estimava «PRNU ≲ 0,2 %». La mesura directa diu **sis o set
vegades més**. Aquell número no venia d'una mesura sobre aquest sensor.

⛔ **Encongiment de Wiener, i no és opcional.** El mapa mesurat és
`veritat + soroll`, i dividir-hi directament deixaria el soroll del mapa com a
patró fix nou, que tornaria a caminar igual. Amb 24 fotogrames la correlació
entre dues meitats disjuntes és **0,81–0,85**, o sigui que el mapa ja és
dominat per PRNU real i l'encongiment surt ×0,89–0,92.

**Resultat:** els traços diagonals desapareixen i queda gra isòtrop;
l'anisotropia del fons a lag 3 baixa de **+0,0426 a +0,0231** i la σ del fons de
4,181 a 3,927 ADU/s. Cost de detall: cap de mesurable —a 1,6 R☉ l'estructura
fina canvia −0,6 % amb correlació 0,9985.

---

## 5 octies. Les línies radials: tancades amb el SEGON TREN

**17 d'agost, i aquesta sí que tanca.** Els dos contrasts independents —Fable 5
i Codex— van coincidir que el test de centratge al Sol **no separa corona d'un
artefacte excitat per la font** (un reflex intern o la diafonia des de la zona
saturada també segueixen el Sol), i tots dos van posar com a **primera** prova
decisiva la mateixa: **buscar-les al tren Sony**.

Fet. Es detecten les crestes radials per separat a cada tren, sobre un
fotograma d'1/8 s de cadascun, i es converteix l'angle d'imatge a **angle de
posició CELESTE** amb els nords mesurats (Vixen 57,19°, Sony 90,27°):

| Vixen | Sony | Δ |
|---:|---:|---:|
| 228,81° | 228,93° | **0,12°** |
| 46,51° | 46,73° | **0,22°** |
| 235,41° | 235,63° | **0,22°** |
| 179,21° | 179,13° | **0,08°** |
| 183,51° | 183,73° | **0,22°** |

Nou coincidències dins de 4° quan l'atzar en dona 2,2, i les cinc bones dins
d'un **quart de grau**. Un refractor apocromàtic de 90 mm i un teleobjectiu de
300 mm, muntures diferents, sensors diferents, escales de placa diferents i
nords separats 33°. **Cap artefacte òptic ni electrònic no pot ser compartit
per dues òptiques independents al mateix angle celeste amb 0,2° de tolerància.**

I hi ha una segona mesura, del diagnòstic en paral·lel: 17 crestes al compost,
totes 17 presents als sis fotogrames individuals, amplada FWHM de 0,62 a 1,94°
—o sigui de 6,9 a 21,3 px, entre 2,6 i 8 vegades la PSF—, senyal/soroll 4,7 en
un sol fotograma, i el compost correlaciona +0,993 amb la mitjana dels sis: el
compost **reprodueix**, no fabrica.

✅ **Són rajos coronals fins i resolts.** El que sí que era meu és que
semblessin *dibuixats*: això ho feia el realçat, i és el que la nova
`etapa_foto` corregeix.

---

## 5 nonies. De filtre de pas alt a fotografia

Pere ho va dir exacte: *«funciona molt bé com a high pass filter, però no és
una foto HDR final del que vaig veure a simple vista»*. **Tenia raó, i hi ha un
número que ho decideix**: la component multiescala divideix per la desviació
local, o sigui que **iguala el contrast a tots els radis** i el cel a 5 R☉
acaba amb el mateix gra que la corona a 2. Una foto no fa això.

La jerarquia nova, que els dos contrasts van demanar per separat:

1. **el compost lineal és l'autoritat** i no es toca;
2. **la foto** (`etapa_foto`) surt d'una corba declarada, contrast local
   **acotat**, color propi i earthshine real;
3. **qualsevol estètica de tercers** és una variant etiquetada.

**La corba.** Tres ancoratges sobre la luminància real, sense normalització
radial: 1,05 R☉ → 0,95 · 2,0 R☉ → 0,65 · 6,8 R☉ → 0,15, interpolats amb una
quadràtica en log-log. ⛔ Provat i descartat: dividir pel perfil radial elevat a
0,7-0,9 **aplana la corona**, i a 0,92 fins i tot la inverteix. La caiguda
radial és el que fa que sembli una foto i s'ha de comprimir **amb la corba**,
no esborrar abans.

**El detall** és additiu i acotat —`L·(1 + 0,35·D)`, escales 4-32 px— en lloc
de substituir l'amplitud per un arctan normalitzat.

**El color** surt d'un mapa declarat de dos ancoratges mesurats al sketch de
Pere: corona (1,28 · 1 · 0,68) i cel (0,91 · 1 · 1,09). ⚠️ És PRESENTACIÓ, i el
motiu de no deixar-hi el color mesurat és físic: amb el Sol a 9° el cel de la
totalitat és **un cel de posta, taronja**, i la corona encara més vermella;
l'ull fosc-adaptat no ho veia així.

**L'earthshine** és real: pila dels tres fotogrames de 10,3 s alineada a la
**Lluna**, amb el halo tret per un polinomi 2D de grau 4 dins del disc, i
col·locada a la posició lunar de l'instant de referència. Contrast del relleu
**1,09 %** sobre un halo de 449 ADU/s. ⚠️ El **nivell** és presentació —és
degenerat amb el model de halo—; el **relleu** és mesurat.

**Encaix amb el sketch**, mesurat:

| R☉ | sketch | foto | raó | color sketch | color foto |
|---|---:|---:|---:|---|---|
| 2,0 | 0,655 | 0,610 | **0,93** | 1,27 / 0,67 | **1,28 / 0,71** |
| 3,0 | 0,496 | 0,331 | 0,67 | 1,30 / 0,71 | 1,12 / 0,98 |
| 5,0 | 0,251 | 0,180 | 0,72 | 1,08 / 0,92 | 0,94 / 1,08 |

⚠️ ~~El sketch no es pot igualar més enllà de 2,5 R☉ [...] la seva corona a
5 R☉ està un 50 % per damunt del seu cel [...] pujar-la seria inventar
senyal.~~ **RECTIFICAT el 17-08 (§5 duodecies)**: la geometria del sketch
estava mal mesurada (R_lluna 1028 px, no 1160: escala 1,13× curta). Amb la
bona, la corona del sketch a 5 R☉ està només un **5–7 %** per damunt del seu
cel, igual que les dades (7 %). La conclusió queia per la banda contrària: la
FOTO d'aleshores anava un 16–22 % MÉS brillant que el sketch a 1,3–3,5 R☉ i un
13–23 % més fosca de 6 R☉ enfora.

---

## 5 decies. Els «radial spokes», les vores dures i la trama fina: una sola causa

Pere ho torna a veure el 17-08 sobre la FOTO ja millorada, i les tres coses que
enumera —feixos estrets perfectament rectes que convergeixen al centre solar,
bandes radials amb vores massa dures, i una trama fina com d'aliasing o
remostreig— **surten totes del mateix**, i no és de les dades.

### La mesura que ho tanca

Contrast rms per banda de freqüència azimutal `m` a l'anell 2,05–2,55 R☉, sobre
el compost lineal normalitzat pel perfil radial i sobre la FOTO d'aleshores:

| banda `m` | amplada | LINEAL | FOTO amb `realca` | factor |
|---|---|---:|---:|---:|
| 5–20 | 18°–72° | 0,11908 | 0,08312 | **0,7×** |
| 20–60 | 6°–18° | 0,03225 | 0,06222 | 1,9× |
| 60–180 | 2°–6° | 0,00615 | 0,06104 | 9,9× |
| 180–400 | 0,9°–2° | 0,00183 | 0,04162 | 22,8× |
| 400–900 | 0,4°–0,9° | 0,00119 | 0,03545 | 29,7× |
| 900–2000 | 0,18°–0,4° | 0,00096 | 0,03070 | **31,9×** |

La jerarquia real entre l'estructura gran i la fina és de **124 : 1**; el
renderitzat la deixava en **2,7 : 1**. Al compost lineal, per damunt de m = 180
—estructures més estretes de 2°— **no hi ha ni un 0,2 % de la potència**: la
trama fina que Pere veu **no és a les dades**, i les vores dures són el mateix
efecte sobre les serpentines que sí que hi són.

### Per què `realca` no ho podia fer bé

Divideix per la desviació local, `arctan(k·(x−μ)/σ)`. Això **iguala el contrast
a totes les escales i a tots els radis**: és la definició d'un filtre de pas
alt, i explica que Pere digués que semblava treure-li el filtre d'antialiàsing
a la realitat. La porta de significació no ho salvava: mirava la variància
**mitjana** d'una regió mentre l'amplificació és **píxel a píxel**, o sigui que
allà on hi ha estructura de veritat la porta s'obria del tot i el soroll que hi
cavalca a sobre s'amplificava igual.

### La substitució

`detall_bandes()`: piràmide de diferències de gaussianes amb **guany declarat
per banda** i **encongiment de Wiener** amb el soroll mesurat de cada banda.
Mai divideix per l'amplitud local, o sigui que la jerarquia es conserva per
construcció. Quatre decisions que no són òbvies:

1. **Les dues bandes més fines van a guany zero.** 1,6–4,2 px és el límit òptic
   (FWHM mesurada 2,70 px) i allà no hi pot haver res que la lent hagi resolt.
2. **El terra de soroll de cada banda es mesura, no s'estima al cel.** L'rms
   d'una banda ampla al cel mesura ESTRUCTURA: a 200–324 px surt 1,7 vegades el
   soroll per píxel, quan una banda que promitja 10⁵ píxels n'hauria de deixar
   passar mil vegades menys. Es mesura sobre una realització sintètica amb la
   correlació del compost —soroll blanc convolucionat amb la gota de drizzle,
   que amb PIXFRAC = 2,0 és una caixa de 2×2 px de sortida—.
3. **El compost porta un sistemàtic d'escala fina ×2,97 per damunt del soroll
   de fotons** —PRNU residual i la reixa del drizzle—, mesurat a la banda més
   fina a 4–5 R☉, on a aquell radi 2 px són 0,06° i no hi pot haver corona
   resolta. Tot el terra de soroll s'escala per aquest factor. És conservador:
   a les bandes amples el senyal/soroll és de centenars i no els toca.
4. **Les bandes es prenen del LOGARITME del contrast.** Amb guanys de 4–5 sobre
   el contrast lineal la modulació topava contra el retall a tota la corona
   interior i hi deixava taques planes.

I una cinquena que era un defecte de veritat: **la corba de to es calibra sobre
la luminància sense realçar i s'aplica a la realçada**. Calibrant-la sobre la
realçada, canviar un guany movia els ancoratges i la corba sencera: el pendent
passava de −0,189 a −1,554 i la corona interior sortia cremada de banda a banda.

### El resultat, amb la mateixa mesura

| banda `m` | amplada | LINEAL | FOTO d'ara | factor |
|---|---|---:|---:|---:|
| 5–20 | 18°–72° | 0,11908 | 0,19149 | 1,6× |
| 20–60 | 6°–18° | 0,03225 | 0,10595 | 3,3× |
| 60–180 | 2°–6° | 0,00615 | 0,04499 | **7,3×** |
| 180–400 | 0,9°–2° | 0,00183 | 0,00735 | 4,0× |
| 400–900 | 0,4°–0,9° | 0,00119 | 0,00113 | **0,9×** |
| 900–2000 | 0,18°–0,4° | 0,00096 | 0,00060 | **0,6×** |

Jerarquia gran:fina **319 : 1** contra 124 : 1 del lineal i 3 : 1 d'abans. El
realçat és ara una gepa centrada a 2–6°, que és on viuen les serpentines i els
radis confirmats al segon tren, i **atenua** el que hi ha per sota de 0,9°.

⚠️ Van caldre **tres** iteracions de dosi, totes demanades per Pere. La primera
deixava 2°–6° a ×3,4 i era massa neta; la segona a ×6,4, encara curta; la viva
és ×7,3, contra ×9,9 de `realca`. **El que no s'ha tocat en cap de les pujades
són les bandes de sota de 0,9°**, que és on vivien la trama fina i les vores
dures: es queden a ×0,6–0,9. La gepa és `GUANYS_BANDA` i és una variable
d'entorn: `GUANYS="0,2,6,10,12,11,9,6,4,2,0"` és el valor viu i es re-renderitza
en quatre minuts.

⚠️ **A la corona interior el que talla el detall no és el realçat, és la corba
de to.** Entre 1,05 i 2,0 R☉ el senyal lineal cau un factor 10 i la corba només
hi gastava 0,30 de pantalla (0,95 → 0,65): el pendent local queda a ~0,15 i
esclafa qualsevol contrast local, hi posis el guany que hi posis. Els ancoratges
baixen a **0,82 al nucli i 0,60 a la corona**, que és el que torna a fer visible
la base de les serpentines. El cel es queda a 0,15.

⚠️ **Els radis reals no s'han tocat i continuen sent-hi**: §5 octies els va
confirmar amb el segon tren a 0,08–0,22° de coincidència. El que s'ha corregit
no és que hi fossin, és que es pintaven **30 vegades** el seu contrast.

### El gradient circular del fons, i per què el va destapar aquest canvi

Pere el veu de seguida a la primera versió corregida, i la causa és mesurable en
una línia: **`norm = L/perfil` val exactament 1,0000 fins al cercle inscrit
(5,20 R☉) i després puja a 1,014 · 1,040 · 1,081 · 1,125** a 7,6 R☉. Més enllà
del cercle inscrit el perfil s'extrapolava amb una llei de potència ajustada a
la corona, i allà baix el que hi ha ja no és corona sinó **halo i cel, que
s'aplanen**: la llei se'n va per sota i deixa un colze a 5,20 R☉.

Aquell colze el veia `realca` també, però com que dividia per la desviació local
li aplanava l'amplitud i no es notava. El realçat nou **conserva l'amplitud**, i
per això el va fer visible: no és un defecte nou, és un defecte vell que el
filtre de pas alt amagava.

Corregit per dos costats:

0. **El fons del detall porta una correcció 2-D**: el residu `L/perfil`
   desenfocat a σ = 250 px —molt per damunt de la banda més ampla que es
   realça, 123 px—. Així `norm` queda pla per construcció a totes les escales
   grans i a tot arreu, dins i fora del cercle inscrit, i el gradient circular
   desapareix del tot en comptes de quedar-ne un romanent. No treu detall:
   250 px són 16° a 2 R☉.
1. **L'extrapolació ja no és una llei de potència**: es continua amb el perfil
   mesurat als **mateixos sectors azimutals a tots els radis** —els que encara
   queden coberts a la cantonada— i s'enganxa per raó al valor de dins. Fixant
   els sectors, el biaix del gradient de cel és el mateix als dos costats de la
   unió i se'n va a la divisió. La desviació a 7,6 R☉ passa de **+12,5 % a
   +2,4 %** i el colze es divideix per cinc. ⚠️ No és el mateix que mesurar
   l'anell sencer allà fora, que és la trampa de §6.1 i torna a fer arcs.
2. **Les dues bandes més amples van a guany zero.** 123–324 px són 8°–21° a
   2 R☉, o sigui la FORMA de la corona, que ja la renderitza la corba de to; no
   aporten detall i sí amplificaven el que quedés del colze.

### Les «costures en falca»

Mesurades: la cobertura varia azimutalment un **3,50 %** a 1,15–1,35 R☉, un
1,44 % a 1,65–2,05 i un **0,06 %** per damunt de 2,5 R☉. És una variació suau
—la de la màscara de saturació, que segueix la brillantor— i no un graó. Amb el
realçat vell això es veia perquè el gra canviava amb la cobertura; amb la porta
de Wiener per píxel, que llegeix el mapa de variància, queda per sota del terra.

---

## 5 undecies. Encallats: el mètode canvia (log-polar, i el detall a pantalla)

Pere, 17-08 al migdia: «repassa aquesta conversa i mira d'aplicar els comentaris
que he anat fent, que em sembla que estem encallats». Tenia raó: tres
iteracions de guanys sobre un mètode amb dos defectes estructurals, i el
mètode s'ha canviat. Aquesta secció **substitueix** el que §5 decies diu
sobre on s'aplica el detall.

### Els dos defectes que cap guany no arreglava

1. **Les bandes en píxels fixos.** La corona té estructura ANGULAR (plomalls de
   0,62–1,94° de FWHM, serpentines de 5–20°). Una banda de 10 px és 1,1° a
   1,2 R☉ —corona real— i 0,3° a 4 R☉ —només soroll—. Cap joc de guanys en
   píxels no pot ser bo als dos radis alhora: si dona detall a dins, embruta a
   fora; si és net a fora, aplana a dins. D'aquí el «massa detall / massa poc»
   que va oscil·lar tres vegades.
2. **El perfil radial extrapolat.** El fons `L/perfil` s'ha d'estendre més
   enllà del cercle inscrit, i qualsevol unió deixa un colze de 8–20 px que
   les bandes amples amplifiquen. La correcció 2-D de σ = 250 px treu la
   rampa, no el colze.

I un tercer que van mesurar **dos contrastos independents** (Fable 5, dos
agents, mateixa conclusió per separat) i que jo no havia mirat: **el pendent
local de la corba de to**. Amb els ancoratges del sketch, d ln t / d ln L val
**0,00–0,07 entre 1,03 i 1,5 R☉** (l'altiplà brillant), 0,34 a 2 R☉, 0,8 a
2,5 i **2,0–2,3 al cel de 4 R☉ enfora**. Com que el detall s'aplicava a L
*abans* de la corba, la corba se'l menjava a la corona interior (×12 nominal →
×0,4 a pantalla: per això els plomalls quedaven tous i l'interior era un bloc
groc pla) i el **doblava al cel** (per això la trama i l'anell es veien tant).
La decisió del §5 decies de posar el detall «a la luminància lineal perquè la
compressió sigui la mateixa per a tot» partia d'una premissa falsa: la
compressió no és la mateixa a cap radi.

### El mètode nou (`detall_logpolar`, `DETALL=logpolar`, viu)

En coordenades log-polars (8192 angles × 2048 log-radis de 400 a 4185 px), una
gaussiana de σ fix és, en la imatge, una gaussiana que **escala amb el radi**
(l'esperit de l'ACHF de Druckmüller):

- `x = ln L`, omplert cap a **dins** del limbe amb el pendent local
  (`inpaint_radial`): el forat de la Lluna no és concèntric i en polars la
  seva vora és ondulada;
- fons `F` = ajust robust de Fourier m ≤ 4 per columna sobre les files
  vàlides, **exacte** mentre totes les files són vàlides (fins a 5,0 R☉) i
  **extrapolat en ρ** més enllà: els harmònics m ≥ 3 amb un polinomi de grau
  2 ajustat a dins, i m = 0, 1, 2 amb un polinomi de grau 3 ajustat també a
  les mitjanes reals de fora (les quatre cantonades simètriques els
  determinen bé). Un polinomi no pot seguir cap graó de composició, i les
  bandes són passa-banda: un error suau del fons no el veuen;
- `R = (x − F)·màscara`; bandes DoG amb σ en graus
  `[0,10 · 0,17 · 0,27 · 0,44 · 0,71 · 1,16 · 1,86 · 3,0 · 4,9 · 7,9 · 12,8 · 20,8]`
  (la mateixa escala que les bandes en px a 2 R☉), **isòtropes en la imatge**
  (σ_ρ = σ_θ·2πK/NA = 0,669·σ_θ; res d'allargar radialment, que fabricaria
  ratlles), normalitzades amb la màscara, angle periòdic amb farciment cíclic;
- porta de Wiener amb el soroll transferit per banda **i per radi**, mesurat
  sobre un camp de soroll sintètic amb la correlació del drizzle remostrejat
  igual; sistemàtic d'escala fina mesurat a la banda més fina a 4–5 R☉;
- guany per banda `GUANYS_DEG = 0 · 2 · 4 · 6 · 6 · 5,5 · 4,5 · 3,5 · 2,5 ·
  1,4 · 0`, apagat per sota d'1,6 px de σ d'imatge (PSF 2,70 px FWHM) i
  esvaït de 5,5 a 7 R☉; compressió suau `0,9·tanh(D/0,9)` en lloc de retall;
- **D s'aplica a la pantalla**: `t = t·exp(D)`, amb la corba calibrada i
  aplicada sobre L sense realçar, i una espatlla suau per damunt de 0,88
  perquè les protuberàncies no retallin. Els guanys són el que es vol VEURE,
  iguals a tots els radis; la corba governa només el gradient.

### Les quatre coses que es van provar i no serveixen (mesurades)

1. **Bandes de ln L sense treure el perfil**: les bandes es mengen la caiguda
   radial (aportacions de 0,3–0,9 en log, deu vegades l'estructura azimutal) i
   el biaix d'una finestra d'un sol costat sobre la rampa del limbe fa un
   anell brillant al voltant de la Lluna.
2. **Omplir cap enfora amb el pendent local**: desplaça la mitjana de columna
   respecte del cel real de les cantonades → anell gegant.
3. **Extensió harmònica cap enfora**: suau i contínua, però el farciment no
   té l'estadística del cel real i les bandes amples ho veuen fins a 4 R☉
   cap a dins (amplitud ×20 a 4,5–5 R☉).
4. **Estadística per columna sobre el conjunt d'angles vàlids a cada radi**
   (mitjana o Fourier): la seva FORMA canvia quan les files de dalt i de baix
   van caient passat el cercle inscrit, i el canvi és un graó en ρ → arcs.

### Dues lliçons que no són del mètode sinó de com es mesura

- ⛔ **«Finit» no vol dir vàlid.** Les files 41–84 de dalt del compost tenen
  cobertura de 3 a 260 aportacions (fila 41: sd 6314 ADU/s). El retall final
  les amagava però ENTRAVEN a tots els càlculs, i en polars són exactament
  les que apareixen just passat 5,0 R☉: estiraven l'ajust del fons de tota la
  columna → arcs. La validesa és la caixa `RETALL`. I el meu script de
  diagnòstic tenia la seva pròpia màscara sense la caixa, o sigui que durant
  una hora vaig «descartar» aquesta causa amb un diagnòstic que la incloïa.
- ⛔ **El test d'anell també tenia el defecte de composició.** Passat 5,0 R☉
  l'anell perd l'arc de dalt (més brillant: horitzó) i la seva mitjana baixa
  sola: la versió SENSE cap detall donava un «vall» de −0,34 % a 5,05 R☉. El
  test bo és sobre un conjunt d'angles FIX (|sin θ| < 0,82, vàlids fins a
  6 R☉), residu respecte d'una quadràtica per finestra de 0,8 R☉.

### Resultat, amb el test net

| versió | residu pic-vall a 4,6–5,4 R☉ |
|---|---:|
| compost sense cap detall (terra de les dades) | 0,09 % |
| FOTO en píxels + correcció 2-D (la que Pere veia) | **2,82 %** |
| log-polar, detall abans de la corba | 0,33 % |
| log-polar, detall a pantalla | 0,05 % |
| + corba del sketch | 0,04 % |
| **+ porta de soroll corregida (viu)** | **0,15 %** |

Contrast per banda azimutal, FOTO viva / lineal, a 2,05–2,55 R☉: 18°–72°
×2,1 · 6°–18° ×3,9 · 2°–6° ×5,2 · 0,9°–2° ×2,0 · 0,4°–0,9° ×0,6 · 0,18°–0,4°
×0,5. Al plomall polar (1,35–1,65 R☉), 2°–6°: **×2,3**, entre el ×0,5 de la
foto en píxels —que allà esborrava tot el detall per culpa de l'altiplà— i el
×4,2 de l'MGN vell. Això és «a mig camí» amb número. La modulació de pantalla
va de ×0,74 a ×1,42 (percentils 1 i 99).

⚠️ La banda de 0,4°–0,9° no té «mig camí» honest: el senyal/soroll per fila
és 0,65 a 2,3 R☉ i 1,0 a 1,3 (contrast extern), i el ×30 que l'MGN hi posava
era soroll amb forma de radis. La porta de Wiener la deixa a ×0,6.

## 5 duodecies. El sketch, mesurat bé: corba, color i earthshine

Auditoria feta per un agent independent sobre `Sketchaprox.tif` (Display P3
→ sRGB abans de mesurar; limbe per 720 raigs + cercle robust; la geometria de
la corona confirmada per correlació creuada del passa-alt amb la FOTO, que
és d'on ve la seva textura fina: r = 0,64). Tres coses que Pere va demanar
explícitament al comentari 5 —to groc → blau fosc, gradient, nivell
d'earthshine— i que jo havia fet a mitges i amb l'escala malament.

### Nivells (Y de pantalla, mediana per anell)

| R☉ | sketch | FOTO d'aleshores | **FOTO viva** |
|---|---:|---:|---:|
| 1,3 | 0,620 | 0,718 | 0,647 |
| 1,5 | 0,594 | 0,695 | 0,602 |
| 2,0 | 0,522 | 0,536 | 0,515 |
| 2,5 | 0,341 | 0,415 | 0,344 |
| 3,0 | 0,275 | 0,325 | 0,274 |
| 4,0 | 0,218 | 0,223 | 0,218 |
| 5,0 | 0,193 | 0,180 | 0,193 |
| 6,8 | 0,183 | 0,153 | 0,183 |
| 8,0 | 0,175 | 0,134 | 0,174 |

**La log-quadràtica de tres ancoratges no pot fer el gradient del sketch**:
té la curvatura negativa i el pendent li creix cap al cel per construcció
(2,3–2,5 de 4 R☉ enfora); el sketch demana ~1 (el seu cel cau −7 % de 6,5 a
8 R☉, la log-quadràtica −15 %). Ara la corba és un **spline monòton en
log-log (PCHIP) pels nivells del sketch** ancorats a la mediana anular del
compost lineal a cada radi (`CORBA=sketch`, `NIVELLS_SKETCH`; els tres
primers +5 % perquè el detall a pantalla i l'espatlla els fan baixar). El
pendent al cel baixa a 0,5–0,6: qualsevol residu del compost —vinyeta, cel no
estacionari, l'anell de 0,09 %— surt a pantalla amb la meitat d'amplitud.
I l'altiplà del sketch a 1,3–1,9 R☉ ja no esborra el detall, perquè D va
després.

### Color (R/G, B/G, mediana per anell)

| R☉ | sketch | FOTO d'aleshores | **FOTO viva** |
|---|---|---|---|
| 1,5 | 1,341 / 0,637 | 1,390 / 0,591 | 1,410 / 0,610 |
| 2,0 | 1,355 / 0,672 | 1,275 / 0,719 | 1,323 / 0,675 |
| 2,5 | 1,277 / 0,784 | 1,206 / 0,884 | 1,230 / 0,801 |
| 3,0 | 1,168 / 0,865 | 1,118 / 0,970 | **1,171 / 0,868** |
| 4,0 | 1,019 / 0,986 | 1,006 / 1,060 | 1,015 / 0,991 |
| 5,0 | 0,959 / 1,067 | 0,948 / 1,081 | 0,940 / 1,053 |
| 6,8 | 0,894 / 1,094 | 0,905 / 1,090 | 0,895 / 1,092 |

Dues correccions: (1) `OBJ_CORONA` (1,28 / 0,68) era la mateixa mesura feta
en **Display P3 sense convertir**; en sRGB és (1,35 / 0,64). (2) Amb dos
ancoratges i un pes lineal en log L el blau arribava a neutre a 3,24 R☉ i el
sketch a 4,14. Els exponents per canal actuaven al revés del que sembla
(el color mesurat és més vermell que l'objectiu a la corona i menys al cel).
Ara hi ha **tres ancoratges** —corona 1,5–2,2, mig 2,7–3,3 (`OBJ_MIG` = 1,17
/ 0,865) i cel 6,2–7,0— amb el camí log-lineal en u entre ells, i el color
mesurat només hi posa la desviació LOCAL respecte del seu propi camí,
comprimida per `EXP_C` = 0,35 (les protuberàncies conserven el rosa; la
vermellor cap a dins de la corona, que el sketch no té, es redueix). El
camí: groc fins a 2,2 R☉ → torrat a 2,5 → beix a 3 → neutre a 4,1–4,3 →
gris blau a 5 → blau pissarra de 6 enfora.

### Earthshine

La mediana ja era la del sketch (1,54× el cel a 6 R☉) però el rang era quatre
vegades el seu (p95/p5 1,63 contra 1,12): el disc del sketch és pla amb un
lleu escalfament cap al limbe. Ara n0 / n1 = 1,50 / 1,68 vegades el cel.
⚠️ El relleu del disc de la FOTO té anells concèntrics de ±12 % (mediana
azimutal 0,215 → 0,275 → 0,215 → 0,27 → 0,32 del centre al limbe): és el
residu de l'ajust polinòmic del halo d'`etapa_earthshine`, i el rang estret
el fa poc visible, però està pendent de refer amb el model de halo (G3).

### El que NO s'ha copiat del sketch

La textura fina (és la FOTO vella usada com a capa; r = 0,64 amb el passa-alt
de 2–8 px); el rim blanc pintat a 1,02–1,08 R☉ (Y 0,87); i el desencaix de la
Lluna (1,5 % petita, 18 px al nord). Pere ho havia dit.

## 5 terdecies. La capa de pas alt, i un error de calibratge que va durar tota la tarda

Pere, 17-08 a la tarda: «ara fes-me únicament un highpass filter de tot, el
faré servir per ressaltar els detalls de la corona». Etapa nova `passalt`
(o `PASSALT=1` dins de `foto`): escriu `corona_vixen_PASSALT.tif`, gris neutre
al 50 % més el mateix camp D que la foto porta a sobre —`0,5 + 0,5·D/0,9`, 16
bits, sRGB, mateix retall que la FOTO, o sigui que s'hi alinea píxel a
píxel—, més `_D.npy` en float32 per reescalar. A Photoshop: Linear Light
afegeix `2·(capa − 0,5) = D/0,9`; Overlay o Soft Light, més suau. La variant
`_FORT` porta les bandes de 0,3°–1,9° a guany 7–10 (`GUANYS_DEG` per entorn).

### ⛔ El calibratge del soroll anava ×7 massa alt des del migdia

En preparar la capa va sortir «mesurat 0,0436 → ×7,26» on al matí deia
«×0,80». La zona de calibratge (4–5,1 R☉) toca la vora de dalt de la caixa
RETALL (5,007 R☉) i el passa-alt de 2 px que s'hi mesurava era una gaussiana
**sense màscara**: barrejava el ln(floor) de fora de la caixa i 1819 píxels
de vora sortien amb salts de 7 unitats. std ×28. Amb MAD (o amb la gaussiana
emmascarada) el número és **0,0016**. Conseqüència: **a tots els renders
log-polars de la tarda la porta de Wiener va 7× massa tancada**, i per això
la sistemàtica d'escala fina sortia ×1,00 (el terra inflat s'ho menjava tot).
Corregit amb `desenfoca_valid` + MAD; la sistemàtica torna a ×1,8 i les
bandes fines s'obren on hi ha senyal. Números vius, FOTO / lineal a
2,05–2,55 R☉: 18°–72° ×2,4 · 6°–18° ×4,6 · 2°–6° **×6,4** · 0,9°–2° ×3,5 ·
0,4°–0,9° ×1,0 · 0,18°–0,4° ×0,7; al plomall polar (1,35–1,65 R☉) 2°–6°
**×2,8**. Test d'anell 0,15 %.

⚠️ La lliçó, que és la mateixa que la del diagnòstic amb màscara pròpia: un
estimador de soroll sobre una zona que TOCA UNA VORA ha de ser emmascarat i
robust, i el seu valor s'ha de LLEGIR a cada render, no només el resultat.

### El compost es va reescriure sota meu

`hdr_vixen_countss.npy`, `var`, `cobertura` i `earthshine_disc.npz` tenen data
16:56 del 17-08 (l'antic queda com `*_prnu_v1_amb_estrelles.npy`): l'altra
sessió (research/78, PRNU v2). Comprovat als tres canals: raó nou/vell
0,9999–1,0002 a tots els radis i el mateix soroll de cel; per a la foto no
canvia res. La FOTO viva i la capa de pas alt són sobre el compost nou.

### Els arcs que Pere va marcar a la capa de pas alt (17-08 vespre)

A la capa nua es veien dos arcs a ~5 R☉ als sectors de dalt. Mesurat al camp
D per sector: dalt-esquerra i dalt-dreta i baix feien **+0,3 % a 4,7 R☉ i
−0,7…−1,1 % a 5,0–5,3**, i el sector lateral res. És la **vora del
fotograma** (dalt 5,007 R☉, baix 5,10): les bandes amples amb la finestra a
mig fer sobre la vora, i la unió exacte/extrapolat del fons a 5,0 R☉, on un
desajust de només 0,05 % ×guany 4–6 ja fa un arc. Dues correccions:

1. **finestra de guany per distància a la vora** de la màscara polar (transformada
   de distància), per banda: cada banda s'apaga suau dins de 2,5 σ (la seva σ
   exterior) de la vora; i l'esvaïment de tot el detall passa a 4,9 → 5,6 R☉;
2. **continuïtat C¹ a la unió** del fons: el polinomi de fora es fixa al valor i
   al pendent de dins a c_ple i només ajusta els termes de grau 2 i 3 (m ≤ 2 amb
   les dades de les cantonades; m ≥ 3 amb el pendent de dins esmorteït), en
   lloc d'un fos de 40 columnes.

Resultat: la variació residual per sector a 4,0–5,7 R☉ és ≤ 0,1–0,15 %, deu
vegades menys que l'arc marcat.

⚠️ **El test d'anell «net» no ho veia**: per esquivar el canvi de composició
mirava un conjunt d'angles fix, i aquell conjunt eren justament els sectors
LATERALS, on l'arc no hi era. El test bo és **per sectors separats**, i sobre
el camp D nu (la capa de pas alt), no sobre la foto: la corba amaga la
meitat.

## 5 quaterdecies. Revisió del compost manual de Pere (`UnintCapes3.tif`)

Pere va fer, capa a capa a Photoshop, un HDR manual amb els **12 esglaons de
l'HDR4** (CR3 sols per als tres més curts, piles DNG de 2–4 fotogrames per als
altres): de baix a dalt 1/3200 → 10,3 s, tots en Normal al 100 %, cadascun
amb màscara (les de 2 s i 10,3 s amagades). Llegit amb les eines de
`research/tools/capes_photoshop/`.

**Pes efectiu de cada capa per radi** (Normal, de dalt a baix): de 2 R☉
enfora el compost és el **1 s al 76–92 %** (pila de 2), el 1/2 s hi posa
5–28 % a 1,6–2,5, les mitjanes (1/60–1/8) només compten a 1,1–1,6, i el
1/3200 i el 1/500 **≤ 5 % enlloc**.

| | Pere | FOTO (pipeline) |
|---|---|---|
| nivell G a 1,1 / 1,5 / 2 / 3 / 5 / 6,8 R☉ | 0,51 / 0,53 / 0,42 / 0,31 / 0,24 / 0,23 | 0,73 / 0,60 / 0,52 / 0,27 / 0,19 / 0,18 |
| color (R/G, B/G) a 1,5 R☉ | 1,20 / 0,73 | 1,41 / 0,61 |
| bandes 2°–6° a 2,05–2,55 R☉ | 0,0036 | 0,039 |
| gra de 2 px a 3,5–4,5 R☉ | **0,65 %** | 0,16 % |
| anells per sector, 4,6–5,4 R☉ | dalt **5,9 %**, resta 0,06–0,3 | 0,1–0,4 |

⛔ **La troballa útil**: la seva corona **puja** de 0,45 a 1,02 R☉ fins a un
màxim de **0,557 a 1,30 R☉** i després baixa (+23 %), mentre que a les dades
lineals cau ×3,3 en aquell tram (7958 → 2385 ADU/s). És el «rim fosc» clàssic
del blending manual: les capes curtes que cobreixen el limbe (1/125–1/30)
estan revelades més fosques que les mitjanes i la màscara barreja una capa
més fosca sobre la zona més brillant.

El que té de bo i que la FOTO no té: naturalitat (cap realçat, contrast baix,
color suau), **protuberàncies roses i nítides** (la FOTO les comprimeix amb
`EXP_C`), i la Lluna negra sense els anells del disc d'earthshine.

**L'híbrid, fet** (`corona_vixen_HIBRID*.tif`): el compost de 68 fotogrames
revelat amb els SEUS nivells (`NIVELLS`, monotonitzats al limbe: 0,615 /
0,590 / 0,570 / 0,549 a 1,02 / 1,15 / 1,30 / 1,50 R☉) i el seu color
(`OBJ_CORONA` 1,22 / 0,768 · `OBJ_MIG` 1,043 / 0,985 · `OBJ_CEL` 0,89 /
1,106, `EXP_C` 0,15 amb les protuberàncies exemptes), Lluna negra
(`LLUNA=negra`), i el detall al 60 %. Comprovat: nivells a ±3 % del seu de
1,1 a 6,8 R☉, color a ±0,03 de 2 R☉ enfora, gra al cel 0,14 % contra 0,65 %.
Es lliura amb la base sola (negra i amb earthshine) i la capa `PASSALT`
perquè l'acabi ell; retall del llenç documentat al `LLEGEIX-ME`.

### Les capes al seu llenç, i un error meu pel camí

Les capes `PASSALT`, la base i l'aplanat es remostregen també al llenç de
6960×4640 de Pere (`*_llencPere.tif`). El seu llenç és la **reixa de sensor
del `572A2969`** (l'apilador HDR4 hi posa el Sol de tots els DNG on era en
aquell fotograma, (3563,89, 2274,66)); el compost del pipeline té el Sol a
(3479, 2319). Desplaçament +84,89 columnes i −44,34 files, comprovat per
correlació a 0,3–0,7 px. ⛔ Una primera recepta deia «X = 40, Y = 85»: sortia
de suposar que el seu llenç era la meva reixa moguda un píxel, i era falsa.

## 5 quindecies. L'earthshine de la Sony ajustat al compost del Vixen (17-08 nit)

Pere porta a `Ajust.tif` (4425×2835, escala nativa del Vixen: R_lluna =
453,3 px) dues capes: la seva corona amb Lluna negra i, a sobre al 60 %,
`POWAAAH3` —la seva A7RIIIA a 2×, 15904×10608— col·locada a ull com a objecte
intel·ligent, perquè l'earthshine que li agrada és el de la Sony. Demana
ajustar-la. El bloc `SoLd` del TIFF diu exactament què hi havia fet: escala
0,7591 i gir −31,86°.

**El centre el tenia clavat a 1,6 px.** L'error era d'escala (+1,9 %, 8,5 px
al limbe) i de gir (1,34°: 11 px al limbe, 31 a 3 R☉).

Els números bons no surten dels discs. **El disc de la Sony acaba on el
compost es crema**: el limbe aparent (màxim del gradient) és a 595 px del seu
marc 2×, contra els 610 que li tocarien per escala de placa —9 px per dins
del limbe real, en píxels del Vixen, per la PSF sobre una corona molt
saturada—. Fer coincidir radis hauria encongit la Sony un 2,5 %. Per tant:

- **escala 0,74482 = (3,2020/2)/2,1495**, les dues escales de placa de
  `research/75` (38 i 22 estrelles, 0,1 % cadascuna);
- **gir −33,20°** en sentit Photoshop (negatiu = antihorari), mesurat
  correlant en angle els plomalls dels dos compostos en tres anells entre
  2,4 i 3,4 R☉: −33,17 / −33,21 / −33,23°, correlació 0,90–0,92. L'astrometria
  dona 57,19° − 90,27° = **−33,08°**, a 0,12° —de l'ordre de la rotació de
  camp de 0,138° que va portar el salt de la muntura Sony (§5.4 de `75`)—;
- **posició**: centre lunar sobre centre lunar. El biaix de la PSF és
  simètric i no mou el centre (rms de l'ajust 2,5 px sobre 1425 punts).

**Comprovació independent, amb les mars.** El relleu de la Sony ajustada
(polinomi de grau 3 restat, passa banda 4–30 px, 78 % interior del disc)
correlat amb `earthshine_disc.npz` del Vixen dona el pic a **escala ×1,004 ±
0,005 i gir −0,05 ± 0,3°** respecte del que s'ha aplicat, correlació 0,74, i
les mateixes taques fosques al mateix lloc. ⚠️ Amb el 92 % del disc la
correlació preferia una escala 3–4 % més petita i era plana en gir: manava
l'anell brillant del limbe, no les mars. La comprovació s'ha de fer amb
l'interior. El desplaçament residual de (−2, +3) px entre els dos relleus és
la diferència entre el disc negre del compost de Pere i la Lluna del
`572A2983` (0,27 px/s de moviment lunar), no un error d'alineació.

La transformació val igual per al llenç de 6960×4640 (`UnintCapes3`)
sumant-hi el retall de la Capa 2, (1325,5, 761,5) per correlació normalitzada
de gradients (la Capa 2 no és un retall pur: mateixa geometria, tonalitat
diferent) —±1 px, els dos discs negres coincideixen a 1,2 px—.

Productes a `Corona_HDR_Vixen/POWAAAH3_ajustada_*` (capa sencera als dos
llenços, màscara del disc, versió amb alfa, JSON amb tot i les
comprovacions), i la recepta de Free Transform al `LLEGEIX-ME`.

I dues trampes del format de Photoshop que han costat mitja hora: els TIFF
petits porten longituds de 4 bytes (els grans, de 8), i els píxels de 16 bits
de les capes van en big-endian dins un TIFF little-endian. Els lectors de
`research/tools/capes_photoshop/` ho autodetecten ara.

## 6. Dues trampes de mètode que costen una tarda

**1. El perfil azimutal fora del cercle inscrit.** Més enllà de 5,2 R☉ l'anell
ja no cap al fotograma i només trepitja les cantonades; amb un cel que té
gradient, la seva mediana fa un graó i surten **arcs enormes** al fons. S'ha de
mesurar només on l'anell hi cap sencer i extrapolar amb llei de potència.

**2. Calibrar el soroll fora d'aquell cercle.** El factor de correlació del
drizzle es mesura comparant la dispersió observada amb la del mapa de variància.
Fet a 6–7 R☉ —zona extrapolada— sortia **κ = 60** en lloc de 0,62, i la porta de
significació apagava **tot** el realçat. Fet a 3,6–4,6 R☉ surt **κ = 0,621**,
que és el valor físic: el drizzle correlaciona els veïns i la dispersió
observada és el 62 % de la del mapa.

---

## 7. Productes

A `~/Desktop/Eclipse 2026/Corona_HDR_Vixen/`:

| Fitxer | Què és |
|---|---|
| `hdr_vixen_countss.npy` | **el producte científic**: float32, 3 canals, ADU/s, centrat al Sol |
| `hdr_vixen_var.npy` | variància per píxel i canal, propagada dels pesos |
| `hdr_vixen_cobertura.npy` | quantes aportacions ha rebut cada píxel |
| `manifest.csv` | els 68 fotogrames amb instant, exposició, centres i escala |
| **`corona_vixen_lineal_16b.tif`** | **TIFF 16 bits, LINEAL i de color neutre**: 65535 = 366.763 ADU/s = 1,02×10⁻⁵ B/B☉ al verd. Conserva els valors |
| **`corona_vixen_FOTO.tif`** | **el lliurable per mirar**: corba de to declarada, detall per bandes amb la jerarquia conservada (§5 decies), color propi de dos ancoratges i earthshine real |
| `comparativa_artefactes.jpg` | abans/ara a 1:1 dels «radial spokes» i la trama fina |
| `corona_vixen_FINAL.tif` | variant amb el color transplantat del POWAAAH3 i la luminància realçada amb `realca`. **És un filtre de pas alt, no una foto** (§5 decies) |
| `corona_vixen_natural.tif` | el color tal com el va veure la càmera, amb la vermellor de la massa d'aire 6,4 |
| `corona_vixen_log/radial/detall/color.png` | visualitzacions, 6958×4638 |
| `corona_vixen_retall_3Rsol/15Rsol.png` | retalls a resolució completa |
| `geometria.json`, `deriva_corona.json`, `escala_global.json`, `vis_params.json` | paràmetres |

⚠️ **Les visualitzacions no tornen a entrar en cap càlcul.** El realçat
multiescala és no lineal i destrueix la fotometria a propòsit, i va **sempre**
després de l'HDR i sobre una còpia.

La luminància surt de **vermell + verd**. ⛔ El blau queda fora: `research/75`
§3 li mesura 4,33 e⁻/ADU contra 5,08 del verd, repetible i sense explicar, i a
sobre va 1,4× més gruixut.

---

## 8. Què queda obert

1. **El model de halo (G3) no s'ha aplicat.** El fons restat és constant més
   pla, que és una decisió de visualització. El halo instrumental i el cel
   continuen barrejats.
2. **El disc lunar és buit.** No s'ha implementat el pes −1 de Druckmüller
   (2006) eq. 3, que faria que el disc del resultat vingués d'un fotograma de
   referència triat. Ara mateix el forat són 112.699 píxels que cap fotograma no
   va veure mai.
3. **La deconvolució (D3).** El nucli del drizzle és analític i el FWHM està
   mesurat: hi ha marge real, i `research/75` §3 diu que les protuberàncies van
   a 257:1 de senyal/soroll, o sigui que el que les limita és la PSF.
4. **El tren Sony no s'ha compost.** El criteri decisiu del G5 —els dos trens
   dins de 0,25 EV entre 1,5 i 3,5 R☉— no es pot avaluar fins que hi sigui.
5. **Els 56 fotogrames de fora de la totalitat** no s'han fet servir. Porten els
   contactes i les perles i volen una pila a part.
6. **El calibratge relatiu de les exposicions queda sense fer.** S'ha retirat
   perquè el que mesurava era el cel, no l'obturador. Per refer-lo bé, el terme
   additiu de `etapa_escala` ha de dependre del RADI i del TEMPS, no ser una
   constant per fotograma, i s'ha de validar amb la dispersió dins d'un mateix
   esglaó, que ha de baixar de l'1,8 % actual a menys del 0,5 %.
7. **G7c**: encara no s'ha comparat amb LASCO C2 ni amb K-Cor.
