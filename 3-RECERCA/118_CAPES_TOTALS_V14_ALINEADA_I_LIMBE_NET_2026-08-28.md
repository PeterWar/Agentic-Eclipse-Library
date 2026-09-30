# 118 — CapesTotalsV14 refeta: la V13_Pere alineada amb la corona, i el limbe net

Encàrrec de Pere (27-08-2026, nit): «fes CapesTotalsV14.psd (overwrite de l'actual, que no
serveix per res). Agafa CapesTotalsV13_Pere.psd i estudia'l en profunditat […] limita't a:
(1) alinear totes les imatges ja existents amb la corona, en base a com saps ara que es mou
durant l'eclipsi, movent només una mica cada imatge; (2) retocar només una mica les màscares
perquè el limbe lunar de les capes 10, 11 i 12 aparegui ben net, a cada capa, i no
introdueixi artefactes, cosa que ara està passant amb la V13_Pere».

⏭️ La V14 «calibrada» del 27-08 (`research/117`) queda **substituïda com a producte** —
apartada a `Documentacio i QA/V14_calibrada_20260827_superseded/`— però el seu document i
les seves mesures continuen sent vàlides i s'hi cita. La diferència de fons: aquella V14
canviava la dada (compost calibrat, to del run, cel pla, sense plomalls); aquesta **conserva
els píxels de Pere byte a byte** i només mou rectangles i multiplica màscares.

Eines: `research/tools/capes_totals_v14/` — `posicions_cadena.py`, `extreu_v13pere.py`,
`mesura_desalineacio.py`, `fes_v14_pere.py`, `comprova_v14_pere.py`, `vistes_v14_pere.py`.
Rebut del lliurable: `CapesTotalsV14_REBUT.md` al costat del PSD.

---

## 0. Resum en sis línies

1. La desalineació entre capes **s'ha mesurat sobre la corona mateixa** (correlació de fase
   dels plomalls per parelles, amb redundància creuada): **cap de les dues hipòtesis prèvies
   no era certa** (§1).
2. Les capes cauen en **tres grups separats per desplaçaments quasi exactament ENTERS**:
   l'empremta de retocs manuals de Pere amb les fletxes del teclat sobre DNG que ja
   compartien geometria (§1).
3. Els moviments aplicats són **enters d'1 a 3 px** (cap re-mostreig) i el residu de corona
   re-mesurat **al fitxer escrit** és **0,23 px** al pitjor parell (abans 2,9) (§3).
4. **El vel del limbe no el posaven les màscares que Pere assenyalava**: el 95 % era la capa
   01 (10,3 s, màscara 0,08-0,11 dins del disc × bloom a 0,50-0,87); les de 10/11 hi
   aportaven 0,0003 (§2).
5. La cura és **només multiplicativa i confinada al disc + 3,5 px**: disc de C2 declarat
   (el limbe de la capa 12) a zero a totes les màscares menys la 12; les 11/10 també pel seu
   propi disc. Vel: **0,038-0,090 → 0,0004-0,0017**. Silueta p95: **6,0 → 3,5 px** (§2-§3).
6. ⛔ Trampa nova de PSD: **als documents de 16 bits, `topil()` de psd-tools retorna la
   màscara a 8 bits**; re-codificar des d'allà deixa el canal a la MEITAT de bytes i el
   fitxer corromput. Els canals s'han de llegir i escriure amb la profunditat del document,
   i **cada canal editat s'ha de tornar a descodificar abans de desar** (§4).

---

## 1. La mesura de la desalineació, i la troballa

### El mètode

`mesura_desalineacio.py`: per a cada parella de capes, correlació de fase de l'estructura
de corona (passa-alt σ=20 px) en l'anell on totes dues tenen dada (vores interiors de
saturació de `research/117` §2 + marges), amb el limbe i els saturats exclosos, taper de
24 px, **signe autocalibrat amb un desplaçament sintètic**, i cada banda partida en dues
mitges bandes radials per estimar la dispersió. Setze parelles adjacents i creuades, més
reforços:

- **capa 01** (dada des de 1,96 R☉): contra una **referència apilada** de 05+04+03+02 ja
  portades al marc comú — banda 2,02-2,55 R☉, resposta 0,238, estable a σ=20 i 35. La banda
  2,3-2,9 degrada a resposta negativa: **la trampa del patró fix de `research/78` §2 en
  acció** (pols i vinyetatge fixos al sensor s'enganxen a desplaçament zero);
- **capa 12** (banda fina 1,04-1,15, resposta 0,13, poc fiable): **triangulació pel limbe**
  — P = limbe_mesurat − (lluna−sol)(efemèride) − sol(referència) − biaix, on el sol del
  fotograma **es cancel·la algebraicament** (no depèn del registre de 572A2956) i el biaix
  de l'ajust de limbe es calibra amb les capes 10/11, de P coneguda. Les protuberàncies no
  serveixen per desempatar: evolucionen entre exposicions (dispersió ±3 px entre finestres).

### El resultat

| grup | capes | P mesurada (px, marc de la capa 10) | ≈ retoc enter |
|---|---|---|---|
| referència | 10, 11 | (0, 0) | (0, 0) |
| a | 09, 07, 05, 03 | (−1,87, −0,1) | (−2, 0) |
| b | 08, 06, 04 | (−1,04, −0,9) | (−1, −1) |
| — | 02 | (−2,85, +1,0) — 2 parelles independents | (−3, +1) |
| — | 01 | (−1,03, −0,0) | (−1, 0) |
| — | 12 | (−2,86, +0,4) | — |

Les parelles creuades ho reblen: 09→07, 08→06 i 06→04 valen (0,00-0,03) — **els grups són
interns exactes**. I les dues hipòtesis de partida queden refutades alhora:

- ⛔ **H_comuna** (`research/78`: els nou apilats comparteixen la geometria de 572A2969, o
  sigui que només 12 i 11 s'haurien de moure): els grups a/b/02/01 no són a (0,0);
- ⛔ **H_pròpia** (`research/117` §1: cada capa seu a la posició crua del seu fotograma):
  prediu salts alternats de ±1,0-1,2 px entre veïnes **amb el signe contrari** al mesurat, i
  les creuades no serien zero.

⏭️ **La lectura que ho explica tot**: els DNG de l'HDR4 sí que compartien la geometria de
572A2969 (research/78 diu la veritat), i **Pere els va acabar d'ajustar a mà, capa a capa,
amb les fletxes del teclat** — per això els retocs són enters, per grups (les capes que va
moure juntes), i de 0 a 3 px. La «desalineació» de la V13 era el residu d'aquell ajust
visual, no un defecte de construcció. `research/117` §1 va llegir «cada capa al seu
fotograma» perquè el seu contrast (limbe per capa, ≤2,3 px) no distingia les dues coses.

### Els moviments

M = −P arrodonit a l'enter — **cap re-mostreig, cap interpolació**: 12:(+3,0) · 11:(0,0) ·
10:(0,0) · 09:(+2,0) · 08:(+1,+1) · 07:(+2,0) · 06:(+1,+1) · 05:(+2,0) · 04:(+1,+1) ·
03:(+2,0) · 02:(+3,−1) · 01:(+1,0). Residu esperat ≤0,15 px (la 12, ±0,5). La màscara
viatja amb la seva capa, o sigui que **l'alineació no toca cap màscara** — com Pere
sospitava («no crec ni que faci falta tocar les màscares»).

---

## 2. El limbe: qui l'embrutava de veritat

Pes efectiu de cada capa (pila Normal, de dalt a baix) dins del disc lunar de la V13_Pere,
per anells de r−R:

| anell (px) | qui hi pinta | nivell que aporta |
|---|---|---|
| [−120, −80] | **01: pes 0,075 × G 0,50** · 12: pes 0,92 × G 0,0004 | **0,038** · 0,0003 |
| [−60, −40] | **01: 0,091 × 0,55** · resta ≤0,0004 | **0,050** |
| [−30, −20] | **01: 0,101 × 0,65** · 05: 0,0017 · 09: 0,0004 · 10: 0,0001 | **0,066** |
| [−12, −6] | **01: 0,107 × 0,87** · 05: 0,005 · 09: 0,002 · 10: 0,0003 | **0,094** |

⛔ **El vel era la capa 01** — la màscara de 10,3 s dins del disc (la malaltia de
`research/87` §1, que Pere ja havia abaixat de 0,33 a ~0,10 a mà) — amb cues de 09 i 05.
Les màscares de les capes 10 i 11, les que l'encàrrec assenyalava, hi aportaven **0,0003**:
els seus píxels dins del disc són negres. (La de la 10 sí que era un defecte *en potència*:
ploma de 0,05-0,27 travessant el limbe; es veia en mirar la capa sola.)

### La cura (multiplicativa, confinada, mesurada)

1. **Disc de C2 DECLARAT** = el limbe mesurat del contingut de la capa 12, mogut amb ella:
   centre (4039,11 · 2740,04), R 453,52 px. És el mateix instant que perles i protuberàncies
   — la decisió «només C2» de Pere aplicada al muntatge. **Totes les màscares menys la de la
   12** es multipliquen per una rampa 0→1 a [R+0,5, R+3,5] px;
2. les capes **11 i 10** també pel **seu propi disc** (limbe mesurat de cadascuna): netes
   també mirades soles («a cada capa»);
3. els apilats (09…01) també pel disc del seu fotograma de referència (sol(2969) +
   (lluna−sol) d'efemèride, R 453,5+2 de guarda) — la seva Lluna hi és escombrada i la seva
   dada legítima comença a 1,4 R☉ o més enllà;
4. la màscara de la **12 és intacta**: el seu contingut ÉS el limbe, i el disc fosc de Pere
   (0,024) es conserva.

⚠️ **Declarat i NO tocat** (fora de l'encàrrec): la màscara de la 01 també posa un rentat
groc de bloom **fora** del limbe (a 1,07 R☉, vora la protuberància, pesa 0,125 amb píxels
saturats blancs). És el glow que envolta la protuberància; treure'l canvia l'aspecte que
Pere ha ajustat i no s'ha demanat. Si es vol fora, és una multiplicació més de la mateixa
família.

---

## 3. Les portes, totes sobre el fitxer escrit

| porta | què | resultat |
|---|---|---|
| **A** fidelitat | canals de píxels **byte a byte** (SHA-256 per canal); rectangles = original+M; màscara 12 intacta; les altres només avall i només dins del disc+rampa | **PASSA** |
| **B** alineació | corona re-mesurada al fitxer escrit, 13 parelles | pitjor residu **0,23 px** (llindar 0,35; abans fins a 2,9) · **PASSA** |
| **C** limbe | vel per anell dins del disc + monotonia del perfil radial al limbe | **0,0004-0,0017** (abans 0,038-0,090) · **PASSA** |
| **D** silueta | vora per **màxim de gradient** contra la V13_Pere amb la mateixa vara | p95 **3,5 px** (V13_Pere 6,0) · màx 6,5 = 6,5 · **PASSA** |
| **E** obrible | psd-tools + ImageIO (`sips`) | **PASSA** |

⛔ La primera versió de la porta D (radi per llindar de brillantor) va marcar 9 px i **era
la mètrica, no el fitxer**: un llindar mesura la **isofota**, que a l'azimut de la
protuberància cau al limbe i a la resta uns px més enfora — la mateixa lliçó de
`research/111`/`114` (el nivell viu a una brillantor, no a un radi). La vora física es
mesura pel màxim de gradient, i la desviació residual compartida de 6,5 px a ~194° **és la
protuberància**, present idèntica a la V13_Pere.

---

## 4. La construcció quirúrgica, i la trampa nova de PSD

El fitxer es fa **obrint la V13_Pere i editant-la**, no reconstruint-la:

- **round-trip de psd-tools verificat abans**: obrir i desar sense tocar res dona mida
  idèntica i canals byte a byte;
- **moviments = rectangles**: el registre de capa i el de màscara es desplacen M; cap canal
  de píxels no es toca;
- **fusionada**: recomposta amb el compositor propi —validat contra la que Photoshop havia
  desat a la V13_Pere: RGBA, **matte blanc**, alfa exacta— i escrita en **RAW** (mai ZIP a
  Image Data: la matriu de `research/117` §7).

⛔ **La trampa que la porta A va enxampar al primer intent**: als documents de 16 bits
**psd-tools desa les màscares a 16 bits però `topil()` les retorna a 8**. Re-codificar des
del `topil()` va deixar el canal amb **la meitat exacta dels bytes** (40,9 MB per 81,9):
`sips` no ho veia (només llegeix la fusionada) i psd-tools tampoc fins que DESCODIFICAVA la
màscara. La regla de `research/117` §7 («el lector que et diu que un fitxer està bé no pot
ser el mateix que l'ha escrit») s'estén: **no n'hi ha prou amb rellegir l'estructura i la
fusionada — cada canal editat s'ha de tornar a descodificar**. Ara `fes_v14_pere.py` ho fa
en el mateix moment d'escriure'l, i la cura és llegir el canal cru amb
`decompress(cd.data, …, depth_del_document)` en lloc de `topil()`.

---

## 5. Cues obertes

- el **rentat groc de la 01 fora del limbe** (§2), si Pere el vol fora;
- els retocs manuals de Pere ara són **coneguts i enters**: si mai es refà el muntatge des
  dels DNG, la taula de §1 és la seva intenció mesurada;
- la silueta comparteix amb la V13_Pere el màxim de 6,5 px a la protuberància — no és cap
  defecte, però que ningú no el «corregeixi» sense mirar què hi ha.
