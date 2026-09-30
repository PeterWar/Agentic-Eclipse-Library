# 78 — HDR4: apilats per exposició del Vixen, i l'extinció dins de la totalitat

**17 d'agost de 2026 · evidència mesurada sobre els CR3 de la totalitat**

Pere va triar a `~/Desktop/HDR3` dotze CR3 del tren Vixen (VSD90SS + R6 III),
un per esglaó, per fer-ne un HDR: 1/3200 (C2−0,75 s), 1/500, 1/125, 1/30,
1/8, 1/2, 1/60, 1/15, 1/4, 1 s, 2 s i 10,3 s, tots entre C2−1 i C2+34 s. Un
sol fotograma va bé per a les protuberàncies —canvien en segons— però per a la
corona en volia l'apilat de tots els fotogrames de la mateixa exposició. El
resultat és `~/Desktop/HDR4`: els tres primers CR3 tal qual a l'arrel, i els
nou següents substituïts per un DNG lineal (a `apilats/`) que apila **tots** els fotogrames de
dins de la totalitat amb aquella exposició (26 fotogrames en nou apilats de
2, 3 o 4), tots en una mateixa geometria: el Sol al lloc on era a 572A2969.

Eina: `research/tools/apila_hdr4_vixen.py` (`mesura` → `apila` → `munta`).
QA a `~/Desktop/HDR4/qa/`. Marcatge: **MESURAT** · **INFERIT** · **PENDENT**.

---

## 1. Què s'ha apilat i com

| DNG | exp | membres | Δt entre extrems |
|---|---:|---|---:|
| `572A2970_apilat4` | 1/30 | 2970 · 2988 · 3000 · 3006 | 80,6 s |
| `572A2971_apilat4` | 1/8 | 2971 · 2989 · 3001 · 3007 | 80,6 s |
| `572A2972_apilat4` | 1/2 | 2972 · 2990 · 3002 · 3008 | 80,6 s |
| `572A2975_apilat2` | 1/60 | 2975 · 2993 | 61,7 s |
| `572A2976_apilat2` | 1/15 | 2976 · 2994 | 61,7 s |
| `572A2977_apilat2` | 1/4 | 2977 · 2995 | 61,7 s |
| `572A2978_apilat2` | 1 s | 2978 · 2996 | 61,7 s |
| `572A2979_apilat3` | 2 s | 2979 · 2980 · 2981 | 5,8 s |
| `572A2982_apilat3` | 10,3 s | 2982 · 2983 · 2984 | 26,5 s |

Cada apilat aplica el que `research/71`, `75` i `76` van deixar mesurat:
calibratge en espai cru amb el master de fosc de la seva exposició i el
pedestal real, mapa de PRNU, cap retall, cap balanç, cap desbayerat abans
d'apilar; **registre a la corona** amb el model de centre solar del manifest
de `Corona_HDR_Vixen`, i **una sola geometria de sortida per a tots els
apilats**: el Sol al lloc on era a 572A2969 (C2+8,4 s), l'últim CR3 que HDR4
conserva sencer, perquè els nou DNG i aquell CR3 quedin alineats en corona
sense que el merge hagi d'alinear res (la primera versió deixava cada apilat
en la geometria del seu propi CR3, com a l'HDR3, i si el merge alinea per la
Lluna la corona queda fins a 9 px desalineada entre extrems; `--geometria
propia` la reprodueix); **disc lunar del fotograma de referència**, desplaçat
amb la seva corona, amb els altres emmascarats amb transició suau de 14 px;
drizzle de **gota 2,0 px de sortida** amb pesos iguals; anivellament del cel;
saturació exclosa mostra a mostra. Sortida: DNG 1.4 LinearRaw de tres
mostres i 16 bits, 6960×4640 —el retall de Canon, no el de libraw, que es
queda un píxel curt—, amb **els valors que Adobe fa servir per a la R6 III**,
llegits del DNG que en fa el DNG Converter 18.5 (Pere el va actualitzar
aquell mateix dia; el 17.5 no coneixia el cos): `BlackLevel 512`,
**`WhiteLevel 13995`**, `BaselineExposure 0,26`, `BaselineNoise 0,8`,
`BaselineSharpness 1,25`, `LinearResponseLimit 1`, matrius de color i
`AsShotNeutral` del cos (les matrius coincideixen amb les del perfil `Adobe
Standard` del Camera Raw d'aquest Mac). ⚠️ **13995 = 512 + 0,85 × 15.871 a
7 comptes**: el blanc d'Adobe per a aquest cos és exactament el sostre de
linealitat del 85 % de `research/74`. Camera Raw tracta com a cremat tot el
que passa de 13995 als CR3, i els apilats exclouen el mateix llindar i
declaren el mateix blanc, perquè un CR3 i un DNG de la mateixa exposició
es vegin igual. Els nou DNG passen pel DNG Converter (DNG → DNG, compressió
sense pèrdua: de 194 a 33–64 MB, píxels idèntics comprovats), o sigui que
són DNG que Adobe mateix ha rellegit i reescrit. Els noms porten un prefix
d'ordre per exposició decreixent (`01_10.3s_…` a `12_1-3200s_…`) perquè
«Load Files into Stack» de Photoshop —comprovat al 27.9 amb tres fitxers de
prova, i al codi de `CreateImageStack.jsx`— posa **la primera imatge de la
llista a la capa de dalt**.

---

## 2. El registre: el model és bo a 0,05 px, però la mesura t'enganya dues vegades

**MESURAT.** Per a cada parella (membre, referència) es mesura el
desplaçament de la corona per correlació de fase de la imatge auxiliar
—corona dividida pel seu perfil radial, com fa `etapa_deriva`— i es compara
amb el model. Els 17 parells donen **residu ≤ 0,09 px**, la majoria ≤ 0,05,
també les del 10,3 s. El model és el que s'aplica; la mesura és la comprovació.

Però arribar-hi ha costat dues correccions de mètode, totes dues amb número:

1. ⛔ **Sense suavitzar, la correlació de fase surt 0,25 px del model.** Pesa
   igual totes les freqüències, i el gra a escala de píxel i el patró fix del
   sensor la tiben. Amb σ = 3 px (mitja resolució) el residu de les mateixes
   parelles cau a 0,05. La corona és llisa: el que s'alinea són les bagues.
2. ⛔ **El radi interior de la imatge auxiliar ha de deixar fora les
   protuberàncies.** Amb 490 px (disc lunar + 30), l'apilat de 1/8 s sortia
   **+0,2 px desplaçat en x a les tres parelles** i el de 1/4 s +0,35, i el de
   1/30 no. Semblava un salt de la muntura al fotograma de referència; no ho
   era: entre 490 i 600 px hi ha les protuberàncies —saturades a partir de
   1/8 s— i el que la Lluna en va descobrint entre un fotograma i el següent,
   estructura que es mou amb la **Lluna** i no amb la corona. Amb 600 px les
   mateixes parelles cauen a ±0,04, i les parelles creuades entre exposicions
   veïnes (1/30→1/8 al mateix instant, 0,9 s de diferència) donen 0,00–0,04:
   la muntura no salta a l'escala del segon.
   Per a les exposicions llargues el forat de saturació fa el mateix paper:
   amb el radi interior fix la mesura sortia d'1 a 4 px del model; amb
   `r_int = 1,25 × radi de saturació` (1 s → 725, 2 s → 800, 10,3 s → 1100 px)
   i finestra i suavitzat més grans, tornen a ≤ 0,1.

**El que no es pot mesurar aquí, i s'estima.** Als costats, a 2–4 R☉, la
corona de les exposicions curtes ja és soroll i la de les llargues queda
dominada pel patró fix del sensor —pols i vinyetatge: no hi ha flats— i la
correlació s'hi enganxa a desplaçament zero en coordenades de sensor. Per
tant ni la rotació de camp ni el canvi de refracció diferencial no es poden
mesurar amb la corona, i s'estimen amb l'efemèride:

| Efecte, sobre els 81 s de l'apilat més llarg | 1,5 R☉ | 3 R☉ | 5 R☉ |
|---|---:|---:|---:|
| Refracció diferencial: el Sol baixa de 9,23° a 8,99°, dR/dh passa de −30,4 a −31,9 ″/° (compressió del camp 0,84 → 0,88 %) | 0,27 px | 0,54 px | 0,90 px |
| Rotació de camp per un error polar de 2° (cota superior, 0,53 ″/s) | 0,14 px | 0,28 px | 0,46 px |

Tots dos per sota del FWHM (2,70 px) i només en la direcció de l'altura o de
la rotació; **els apilats són translació pura**, com el compost de
`research/76`. **PENDENT:** si algun dia es vol el 0,5 px de 3 R☉ del 0,5 s i
l'1 s, cal un drizzle afí i saber la direcció de l'altura al sensor.

---

## 3. L'extinció dins de la totalitat: k = 0,40 mag per massa d'aire

⛔ **Aquesta és la troballa nova, i canvia una conclusió de `research/76`.**

**MESURAT.** Comparant cada membre amb la seva referència, ja registrats, per
un ajust conjunt `membre = a·referència + b` sobre els perfils anulars del
pla verd (anells de 0,05 R☉ d'1,05 a 4,8 R☉, fora del disc i sense
saturació), els fotogrames tardans surten **un 4–6 % més fluixos**, i el
factor és **multiplicatiu i uniforme en azimut** —a 1,3–1,6 R☉ els quatre
sectors donen −5,0 / −6,5 / −5,2 / −8,8 % al 1/30 s—. No pot ser cel: a
1,05–1,15 R☉ el cel és el 0,3 % de la corona i la diferència hi és de −5,5 %.

És l'atmosfera. El Sol es pon: entre C2 i C3 passa de 9,23° a 8,92° d'altura
i la massa d'aire (Kasten-Young) de **6,02 a 6,20**. Amb `a` i la diferència
de massa d'aire de cada parella surt el coeficient d'extinció:

| exp | parella | Δt | ΔX | a | k (mag/X) |
|---|---|---:|---:|---:|---:|
| 1/30 | 2970→2988 · 3000 · 3006 | 62–81 s | 0,115–0,151 | 0,960 · 0,946 · 0,943 | 0,385 · 0,438 · 0,424 |
| 1/8 | 2971→2989 · 3001 · 3007 | 62–81 s | 0,115–0,151 | 0,959 · 0,955 · 0,934 | 0,395 · 0,363 · 0,490 |
| 1/2 | 2972→2990 · 3002 · 3008 | 62–81 s | 0,115–0,151 | 0,958 · 0,953 · 0,952 | 0,409 · 0,379 · 0,358 |
| 1/60 · 1/15 · 1/4 · 1 s | (2 membres) | 62 s | 0,115 | 0,955 · 0,959 · 0,958 · 0,964 | 0,432 · 0,393 · 0,403 · 0,348 |
| 10,3 s | 2982→2984 | 26,5 s | 0,049 | 0,981 | 0,419 |

**k = 0,402 ± 0,036 mag per massa d'aire** (14 parelles amb Δt > 20 s, set
exposicions). Les tres parelles curtes (2 s a 3–6 s, 10,3 s a 13 s) tenen ΔX
massa petit per dir res i queden fora de la mitjana.

Tres coses que se'n desprenen:

- ✅ **El 0,37 del projecte queda confirmat per una via independent i neta.**
  `research/75` §5 no podia separar l'extinció del vinyetatge (0,416 i 0,723
  als dos trens); aquí la mesura és **diferencial sobre els mateixos píxels**
  —mateixa posició al camp, mateixa exposició, 60–80 s de diferència— i el
  vinyetatge no hi entra.
- ⛔ **`research/76` §5 bis es va equivocar de causa en un punt.** Els factors
  d'escala relativa entre esglaons «correlacionaven amb el temps (r = −0,60)»
  i es van atribuir sencers a la variació del cel colada dins l'ajust, amb
  l'argument que «un cos amb obturador electrònic no falla un 7 %». L'obturador
  no falla, però **la corona sí que baixa un 5,5 % de C2 a C3, multiplicativament**,
  i això és exactament una correlació amb el temps. El compost del 16-08 barreja
  esglaons presos a instants diferents sense aquesta correcció; el seu efecte
  sobre la continuïtat és de l'ordre del 2–4 % entre esglaons veïns, i és
  **PENDENT** refer-lo amb la normalització d'extinció (§4).
- **Cada membre es normalitza a la massa d'aire d'un instant comú**, el de
  `572A2969` (C2+8,44 s), l'últim CR3 que HDR4 conserva sencer: factors
  ×1,0006 a ×1,0597. Així els dotze fitxers de l'HDR queden a la mateixa
  escala fotomètrica.

---

## 4. El cel: un fons comú per a tots els apilats

`research/76` §5 bis: el cel de la totalitat fa una V (509 → 335 → 491 ADU/s)
i cada esglaó es pren en un instant diferent. Aquí es veu tal qual: al 1/30 s
la diferència de cel amb la referència val −111, −55 i −19 ADU/s a C2+71, 84 i
90 s (el terme `b` de l'ajust), o sigui que a C2+90 el cel ja torna a pujar
cap a C3.

**Anivellar cada apilat al seu propi valor mitjà no basta.** Els apilats de
quatre tenen l'època mitjana cap a C2+64 s (cel fosc) i els de 2 s i 10,3 s a
C2+23 i C2+47: entre el 2 s i el 10,3 s hi hauria **50 ADU/s de diferència
de cel, un 6 % de la corona a 1,96 R☉**, que és on l'HDR passa de l'un a
l'altre —el mecanisme exacte dels arcs concèntrics—. Per això tots els
apilats s'anivellen a **un mateix fons per pla**, el de `572A2972`
(0,5 s, C2+11,6 s): és la primera exposició prou llarga perquè el fons es
mesuri amb precisió i té el cel de tocar de C2, el més clar, o sigui que
anivellar-hi vol dir afegir pedestal i mai treure'n. El 10,3 s rep entre
+1.148 i +1.336 comptes; el 1/30 s, un compte.

**Continuïtat resultant, MESURADA sobre els DNG** (raó de comptes/s entre
apilats consecutius als anells sense saturació a cap dels dos): 1,0000 ·
0,9958 · 1,0170 · 1,0000 · 1,0025 · 0,9986 · 0,9996 · 0,9964. Tot dins l'1 %
llevat de 1/15 → 1/8 (1,7 %), i el parell 2 s → 10,3 s a 0,4 %.

---

## 5. Comprovacions sobre els productes

**MESURAT.**

- **Registre del resultat**: la correlació de cada DNG amb cada membre dona
  el desplaçament del model a ≤ 0,07 px, i **entre apilats** —tots en la
  geometria comuna— la corona coincideix a ≤ 0,08 px (el pitjor és 2 s →
  10,3 s, −0,08 en x); contra el CR3 572A2969 els de 1/60 a 2 s donen
  ≤ 0,04 px (els dos més profunds no s'hi poden comparar: a 1/125 s no queda
  corona més enllà de 2 R☉).
- **Soroll**: a 4,5–5 R☉ el gra del verd baixa a **0,33×** el d'un fotograma
  sol als apilats de quatre i a 0,39× als de tres (√N més la mescla G1+G2 i
  la gota).
- **El disc lunar** és el de la referència píxel a píxel; entre el disc de la
  referència i el dels altres membres (fins a 20 px de desplaçament relatiu)
  no queda cap sagnat.
- **A prop del limbe** (r < 600 px del centre lunar) l'apilat i la referència
  difereixen un 3–4 % perquè les protuberàncies i el que la Lluna descobreix
  canvien en 80 s: és el motiu pel qual Pere conserva els tres CR3 sencers.

---

## 6. Dues coses del cos que no constaven

- ⛔ **El pou de la R6 III clava a 16382, no a 16383.** Al fotograma de
  10,3 s hi ha 1,26 milions de píxels a 16382 i 43.000 a 16383, i per sota
  de 16382 la densitat és d'uns 60 píxels per compte, plana. `n_sat` a
  `hdr_corona_vixen.py` compta `≥ 16383` i subestima la saturació 30 vegades;
  no ha fet mal perquè els pesos ja tallen al 85 % del pou, però la constant
  és falsa. **I Adobe hi posa el blanc a 13995** (§1): els apilats exclouen a
  partir d'allà, que és el que Camera Raw fa amb els CR3.
- **G1 = G2** al fons (16,83 i 16,83): cap desequilibri de verds.

---

## 7. Què queda obert

1. **Refer `Corona_HDR_Vixen` amb la normalització d'extinció** (§3): factor
   multiplicatiu per fotograma segons la massa d'aire, abans de l'anivellament
   del cel i abans de retirar cap factor d'escala per «no ser obturador». (El
   mapa de PRNU v2 de §8 sí que ja s'hi ha aplicat.)
2. **Drizzle afí** per als 0,5 px de refracció diferencial a 3 R☉ dels apilats
   de 80 s (§2), si mai cal.
3. **Flats.** Sense flats el patró fix del sensor mana a la correlació dels
   costats i no es pot comprovar la rotació de camp amb la corona.

---

## 8. Les estrelles: el mapa de PRNU portava les seves traces

Pere va veure, al costat de cada estrella —puntual—, **un artefacte diagonal
al fons: uns quants píxels una mica més foscos en línia**, i va demanar
arreglar-ho sense tocar la PSF de l'estrella, que és el que farà servir per a
la relativitat (`research/77`).

**MESURAT: era el mapa de PRNU (`prnu.npz` v1, research/76 §5 septies), no
els fotogrames.** El mapa era una mitjana ponderada pel senyal, sobre 24
fotogrames, de `(píxel − mitjana local 9×9)/mitjana local`, sense cap rebuig.
Les estrelles dels fotogrames llargs hi entraven senceres: al llarg de la
traça que cada estrella deixa pel sensor en derivar la muntura (0,27 px/s), el
mapa tenia una filera de bonys **de +0,04 a +0,135** —de 3 a 10 σ del mapa,
que val 0,013— i, per fer-ho pitjor, la mitjana local que inclou l'estrella
deixava els veïns per **sota** de zero. Dividir cada fotograma per `1 + mapa`
feia tres coses: clots foscos del 4 al 13 % **en diagonal, en la direcció de
la deriva**, al costat de cada estrella (això és el que Pere veia); l'estrella
mateixa perdia **fins a un 10 % del pic** allà on trepitjava un bony seu; i el
resultat era diferent a cada fotograma perquè l'estrella no era al mateix
lloc del sensor. Per a astrometria, tot això és verí.

| | mapa v1 | mapa v2 |
|---|---:|---:|
| màxim del mapa en 5×5 a l'estrella més brillant (pla R / G) | +0,135 / +0,118 | +0,029 / +0,023 |
| ídem, deu estrelles més (rang, pla R) | +0,044 a +0,135 | +0,015 a +0,043 |
| el mateix en llocs aleatoris del mapa (mediana / p90 / p99, pla R) | | +0,023 / +0,031 / +0,040 |
| mínim del fons en un retall de 61 px al voltant de l'estrella | **−6,3 %** | −0,8 % (soroll) |
| σ del mapa (pla G) | 0,0126 | 0,0109 |
| píxels amb `|m| > 0,04` (pla G) | 31.107 | 16.959 |

**La correcció** (`research/tools/prnu_vixen.py` v2): a cada fotograma i
pla, **es detecten i s'emmascaren les estrelles i qualsevol transitori
compacte** —píxels més de 6 σ per damunt de la mediana 7×7, dilatats 3 px de
pla— i la mitjana local es calcula sense ells (convolució normalitzada); la
mitjana ponderada es fa dues vegades i a la segona es rebutja tota mostra que
s'aparti més de 3,5 σ del mapa de la primera. On una estrella hi era, el mapa
el fan els altres fotogrames: el mapa continua essent **del sensor** (PRNU
real 1,1–1,4 %, correlació entre meitats 0,78–0,83, com abans) i ja no porta
res del cel. Es rebutja el 0,2 % de les mostres.

⚠️ **Una trampa de mètode que ha costat mitja hora**: la primera versió del
rebuig, sense la màscara d'estrelles i amb cinc passades iteratives amb
dilatació, **convergia al mode equivocat** allà on la primera passada ja era
esbiaixada: rebutjava els fotogrames profunds (que discrepaven del bony) i es
quedava amb el soroll dels curts, i en algun píxel deixava un bony de +0,12.
La màscara ha de ser **independent del mapa**.

**El resultat sobre les estrelles dels apilats (10,3 s):** perfil radial de
la més brillant 1619 · 1054 · 373 · 98 · 23 · 7 · 4 comptes per damunt del
fons, cap píxel per sota del −3 % del fons en un 29×29 (abans, clots del
−6 %); la PSF és la que va veure el sensor, només amb el fosc restat i el
guany píxel a píxel corregit. Els nou DNG s'han regenerat, i el compost
`Corona_HDR_Vixen` (research/76) s'ha refet amb el mapa v2 —tenia el mateix
defecte—; el v1 queda com a `prnu_v1_amb_estrelles.npz` i els productes vells
a `Corona_HDR_Vixen/_productes_prnu_v1_amb_estrelles/`.

⛔ **Lliçó general**: qualsevol mapa mesurat «a les pròpies dades» —PRNU,
flat sintètic, halo— s'ha de construir amb les fonts puntuals emmascarades i
un estimador robust; si no, el mapa aprèn el cel i el torna, invertit, a
cada fotograma.

---

## 9. Els apilats de protuberàncies, i per què no hi ha drizzle 2×

Pere: «no podem guanyar detall de les protuberàncies fent més drizzle?». La
resposta té dues meitats, i les dues estan mesurades.

**El que sí que es guanya, i s'ha fet.** Les protuberàncies són vermelles
(Hα) i el pla R és el pitjor mostrejat del sensor: un píxel cada 4,3″ per a un
FWHM de 4,2–4,6″ (`research/75`), un sol mostreig per FWHM. Amb fotogrames
desplaçats una fracció de píxel entre ells, el drizzle sobre la reixa del
sensor recupera aquell mostreig; i tenim seqüències ideals, en què la
protuberància no ha canviat ni la Lluna n'ha descobert res: les ràfegues de
1/3200 (**9 fotogrames en 5,2 s a C2**, 572A2958–2966, i **17 en 10,4 s a
C3**, 3009–3025; consecutius cada 0,65 s, 0,17 px de deriva entre l'un i
l'altre) i els trios tardans de 1/2000, 1/500 i 1/125 (19 s de finestra). Els
cinc són a `HDR4/protuberancies/`, en la geometria comuna i amb la màscara
lunar cenyida al limbe real (453,8 + 2 px, transició 4; per als 1/3200, que no
tenen limbe mesurable, el centre del model corregit amb l'offset limbe−model
mesurat, (+2,55, −2,59) px). A la ràfega de C2 el soroll del pla R baixa de
2,73 a 0,97 comptes (÷2,8) i la protuberància del limbe est surt amb el pla R
mostrejat a la reixa del sensor en lloc de per blocs de 2×2.

**El que no es pot fer, i per què.** Una reixa de sortida 2× o una gota més
petita que el pas del pla no dona més resolució amb aquestes dades: **la
muntura deriva en línia recta**, o sigui que el ditherat és unidimensional
—les fases subpíxel en x i en y van lligades, sobre una diagonal— i una gota
més petita que 2,0 px de sortida deixa píxels que la reben de ple i píxels que
només en toquen la cua, alternats: l'escaquer que `research/76` §3 va mesurar
amb 68 fotogrames (5.620× la potència mitjana amb gota 1,70). Amb 9 o 17 no
millora, perquè no és qüestió de nombre sinó de que les fases no omplen el
pla. La gota de 2,0 —partició de la unitat— és el màxim que aquest ditherat
permet, i és el que fan tots els apilats. El camí per a més resolució és la
**deconvolució** (`research/76` §8, D3): la PSF ja està ben mostrejada i el
senyal/soroll és 3× més alt.

**Les capes per a Photoshop** (`etapa capes`, `HDR4/protuberancies/capa_prot_C2|C3*.tif`).
Pere treballa per capes i volia la protuberància com una capa més, de la
mateixa mida i alineada, i «les altres protuberàncies interessants a prop de
C2» (una punxa feble a dalt de la Lluna). Es fa un HDR d'època —tots els
fotogrames presos en uns segons al voltant del contacte, 15 a C2 (0,6–11,6 s,
1/3200 a 1/2) i 29 a C3 (81–104 s), comptes per segon amb pesos t²/(S/g+RN²),
drizzle 2,0, geometria comuna, disc lunar cenyit— i se'n treuen les
protuberàncies **pel color, no per la brillantor**: una protuberància feble
és 10× més fluixa que la corona que té al darrere i només se'n distingeix per
l'excés d'Hα, E = R − ρ·G en comptes de càmera, amb ρ = R/G de la corona
mesurat a la mateixa imatge (0,809 a C2 i 0,814 a C3: el 0,816 de
`research/76` §5 ter). ⛔ El soroll de E no és de fotons: és el residu suau
del model de color (±700–860 comptes/s en taques de centenars de píxels) i no
baixa en suavitzar; restant-li el seu fons suau (σ = 40 px, sense el disc ni
les protuberàncies fortes) queda a 271–332 comptes/s, i les protuberàncies,
que són compactes o primes, sobreviuen. Màscara: E passa-alt suavitzat 2 px a
> 2 σ amb confirmació a 4 px (> 1,5 σ), disc a zero, ploma d'1,5 px. ⛔
Provat i retirat: llindar per histèresi (llavors 3,5 σ, creixement fins a
1,5 σ) —la cromosfera és llavor a tot el limbe i el soroll que la toca
creixia en confeti—. Sortides per època: la capa (asinh, s = 0,01 de la
màxima), la lineal, l'excés d'Hα **sense màscara** (on la punxa de dalt de C2
es veu amb la seva cua de 40 px a 1–2 σ per píxel, que cap llindar per píxel
no pot conservar) i la màscara. Color: balanç del cos i matriu càmera→sRGB
(mètode dcraw amb la ColorMatrix2 d'Adobe).

