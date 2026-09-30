# 105 · Com ho fa Brno: el protocol Druckmüller contrastat amb el nostre mecanisme

**Data:** 25 d'agost de 2026, nit. **Agent:** Fable 5.
**Pregunta de Pere**, just després de tancar el mecanisme del `104` («cada
canal compon cada radi amb un joc de fotogrames diferent, i el cel no era el
mateix»): *com ho soluciona això l'equip Druckmüller?*

**Mètode:** cinc recerques independents sobre fonts primàries — el web de
Brno (`zam.fme.vutbr.cz/~druck/eclipse/`, ~220 pàgines tècniques de composts
del 1994 al 2026), el paper fundacional (Druckmüller, Rušin & Minarovjech
2006, CAOSP 36, 131), el paper d'alineació (Druckmüller 2009, ApJ 706, 1605),
la tesi doctoral del grup (Druckmüllerová 2014, Brno UT), i els articles amb
l'equip de Habbal (ApJ 708/734/702, Boe 2020-2022, Alzate 2017). Cada
afirmació porta font; el que és inferència pròpia està marcat **INFERIT**.

**La resposta curta: no ho solucionen al postprocessat — ho maten a la
captura, i el que en queda ho esquiven amb una arquitectura que mai no compon
detall per canal.** Quatre moviments, i un regal final.

---

## §1. Primer moviment: la captura fa que el problema no existeixi

**DOCUMENTAT.** El protocol de captura de Brno és exactament el contrari del
nostre `single HDR` del 12-08:

> «sequences of increasing and decreasing consecutive exposure times, varying
> by a factor two» — Habbal et al. 2011, ApJ 734, 120 (Tatakoto 2010).

Una **escala monòtona de factor 2 que es recorre amunt i avall contínuament
durant tota la totalitat**. Conseqüències mesurades a les seves pàgines:

| Eclipsi | Imatges d'eclipsi | Totalitat | Rang | Cadència |
|---|---:|---:|---|---|
| 2006 Líbia (gran angular) | 231 (5 càmeres) | 239,5 s | 1/1000–8 s | — |
| 2010 Tatakoto (1624 mm) | 89 preses, 61 usades | 269 s | 1/500–2 s | 3,0 s/foto |
| 2017 Whiskey Mtn (200 mm) | 96 | 142 s | 1/30–2 s | 1,5 s/foto |
| 2019 Tres Cruces (347 mm) | 128 | 148 s | 1–1024 ms | 1,2 s/foto |
| 2024 Sims (300 mm f/2,8!) | **487** | 257 s | **1/250–1 s** | **0,53 s/foto** |
| **2026 Trigaza (800 mm)** | **298** | ~100 s | **1/500–1/2 s** | ~0,34 s/foto |

Cada temps d'exposició apareix a **molts instants ben separats** —dividint
total per nivells, de ≈8 a ≈50 aparicions per esglaó (INFERIT: cap pàgina no
publica el recompte per nivell)—. El disseny és **deliberadament redundant
contra la transparència variable**: al 2010, amb núvols rodants, «several
dozens of second long intervals were enough because of the exposure sequence
strategy **which was prepared for this eventuality**» (pàgina del compost de
3,5 R☉). I la recomanació del paper fundacional és literal: «to do many
exposures … **with a shorter time lag** between each other» (CAOSP 2006 §7).

**Què vol dir per al nostre mecanisme del `104`:** amb ~30 aparicions d'un
esglaó repartides pels 250 s, «l'instant mitjà» de cada esglaó — i per tant de
cada **canal**, encara que el verd perdi els fotogrames de la vora abans —
convergeix cap al mateix valor als tres colors. La barreja temporal per canal
que a nosaltres ens deixa les corbes només-G queda diluïda per √N i per
mostreig dens. **El nostre run tenia cada esglaó a 1-2 instants**: el
problema hi surt a amplitud plena, i cap postprocessat de Brno no està pensat
per arreglar-lo perquè al seu material no hi és.

Dos refinaments seus del mateix principi:

- **2019 Mamalluca:** l'escala HDR **repartida entre dues muntures bessones**
  (800 mm + D810): una càmera fa 1/1000–1/4 s i l'altra 1/4–4 s — cadència
  doblada per nivell sense perdre rang. Directament aplicable als nostres dos
  trens del 2027.
- **2012 Austràlia (gran angular):** contra núvols prims, imatges de **tres
  llocs diferents** «distant enough to decrease the influence of thin clouds»
  però amb ≤18 s de diferència a C2 per no barrejar corones diferents.

⏭️ **Això confirma, amb el protocol de l'equip de referència mundial, els
requisits 1 i 2 del §1 quater de `CLAUDE.md`** (escala monòtona amb esglaons
veïns en el temps; cada esglaó a ≥2 instants — ells en fan 8-50). I hi afegeix
el número que ens faltava: el seu terra de cadència real és **0,3-3 s per
fotograma sostinguts tota la totalitat**.

## §2. Segon moviment: la transparència que queda es tria i s'anivella, no es modela

**DOCUMENTAT.** Tres capes de defensa, cap de les quals és una cura 2D per
fotograma com la nostra:

1. **Selecció dura:** els fotogrames «significantly influenced by clouds» es
   llencen. Tatakoto 2010: de 69/64/89 presos (200/500/1624 mm) van usar-ne
   **4/23/61**. Es pot llençar més de la meitat del material perquè la
   redundància del §1 ho permet.
2. **Anivellament per fotograma DINS del compositor:** el LDIC aplica una
   transformació lineal k_i(φ), q_i(φ) **per segment angular** (60 segments,
   polinomi trigonomètric), i la tesi diu que existeix precisament per
   «compose images with different distribution of diffuse light … or even
   images that were taken through thin clouds» (Druckmüllerová 2014 §4.1.4).
   És el cosí del nostre anivellament+coherència — el seu és azimutal, el
   nostre és escalar; cap dels dos no és un camp 2D.
3. **El cel es resta sobre el COMPOST, no per fotograma:** la fotometria dels
   Sherpas mesura el cel «at the center of the Moon» del compost final, el
   resta, i torna a afegir l'earthshine esperat (2,5±1,5·10⁻¹⁰ B☉); l'escala
   absoluta ve de creuar amb el coronògraf K-Cor en una falca d'1,125-1,15 R☉
   (Boe et al. 2021/2022). L'absorció atmosfèrica s'assumeix **constant sobre
   el camp** i la seva variació temporal **no es modela enlloc**.

**INFERIT (negatiu, i és la troballa que ens situa):** cap font — papers,
tesi, 220 pàgines web — no descriu un factor fotomètric ajustat per fotograma
contra una referència per compensar la deriva de transparència dins la
totalitat, ni res com la nostra cura del cel per fotograma del `103`. **La
nostra cura v4 va més enllà del que Brno documenta públicament** — no perquè
siguem més fins, sinó perquè la nostra captura ens hi va obligar: ells
compren amb redundància el que nosaltres hem hagut de reconstruir amb
modelatge.

## §3. Tercer moviment: la Lluna és un objecte a part, ancorat a UN instant

**DOCUMENTAT.** El seu tractament és el patró «piles separades» que nosaltres
ja fem, portat fins al final:

- **L'alineació és NOMÉS sobre estructures coronals** («Neither the edge of
  the Moon nor stars are suitable», CAOSP 2006): correlació de fase sub-píxel
  (<0,01 px al limbe, ApJ 2009) després d'**esborrar amb màscara tot el que es
  mou respecte de la corona** — Lluna, estrelles brillants, pols — i de
  quedar-se només les freqüències tangencials (el gradient radial extrem
  corromp les radials).
- **A la composició, la Lluna té pes −1 per fotograma** (eq. 3-4 del CAOSP
  2006): cap fotograma no aporta corona allà on **la seva** Lluna tapava — el
  mateix que la nostra màscara lunar per fotograma.
- **El disc lunar del compost surt d'UN instant declarat**: «The position of
  the Moon represents the situation X seconds after second contact» (fórmula
  repetida a 2008/2009/2017…), i quan volen earthshine amb detall fan una
  **alineació separada de la Lluna**, perquè «about 5 seconds difference in
  images acquisition would cause noticeable blurring» (Turquia 2006).
- Les estrelles no tenen tercera pila: queden com a **traços**, i les seves
  llargades diferents delaten que «every image part consists of different
  images taken at different time» (Tatakoto 2010) — Brno **conviu** amb la
  barreja d'instants; el que no fa és deixar-la entrar de manera diferent a
  cada canal, pel §4.

El nostre desplaçament de +1,45 px a 1,15 R☉ (el que Pere va veure a
l'animació) és exactament el fenomen que la seva àncora d'instant únic
gestiona: ells **declaren** l'instant de la vora lunar en lloc de deixar que
cada canal en triï un de diferent.

## §4. Quart moviment: el detall MAI no es compon per canal

**DOCUMENTAT, i és la resposta d'arquitectura al nostre problema del verd:**

- El registre es fa sobre **una única imatge de brillantor** (mitjana
  ponderada de R, G i B, «green has higher weight», tesi §4.1.3) — mai per
  canal.
- Els filtres adaptatius (ACHF/NRGF/FNRGF) s'apliquen «to the **brightness /
  lightness component only**» (tesi §3.1.1); es defineixen sobre escala de
  grisos.
- El color del compost es manté «tal com surt de la càmera» i **es tracta com
  a amplitud minúscula**: la corona K és «nearly white» per definició (Thomson
  acromàtic), i per fer visible el color cal restar el cel de Rayleigh i
  multiplicar la saturació **×50 (2008) a ×400 (2020/2023)**. Al compost 2023
  el continu es mostra **gris neutre** i el color el posen només les línies.
- Quan volen estructura fina d'una línia d'emissió (Fe XIV/Fe X), **no la
  treuen dels canals Bayer**: càmeres monocromes bessones amb filtres de
  0,5 nm, parella on/off-band, calibratge fotomètric i resta de continu. La
  via Bayer (Martišek & Druckmüllerová 2011) està validada només com a
  **qualitativa**.
- El LDIC posa **w=0 per sobre de ~85 % del rang** (la no-linealitat pot
  començar allà): la vora de saturació — justament on el nostre verd perd els
  fotogrames — ni tan sols entra al seu compost.

**INFERIT:** cap font no esmenta el problema dels instants efectius diferents
per canal. No l'han resolt: **l'han esquivat estructuralment**. Una sola
lluminància per al detall + color de baixa freqüència = encara que cada canal
porti una barreja temporal una mica diferent, la diferència només pot entrar
al producte com a tint suau, mai com a corbes fines. La nostra fase 3 sobre el
canal G sol és exactament la porta que la seva arquitectura té tancada.

## §5. El regal: Brno ja ha publicat EL NOSTRE eclipsi

**DOCUMENTAT (pàgines actualitzades el 22-24 d'agost de 2026).** L'expedició
Solar Wind Sherpas va observar el 12-08-2026 des de **Pico Trigaza** (Burgos,
N 42° 16,07′ W 3° 15,44′, 1655 m, Sol a **7°**, C2 18:28:24 UT), i Druckmüller
ja té tres composts publicats a
`zam.fme.vutbr.cz/~druck/eclipse/Ecl2026s/Trigaza/`:

| Òptica | Càmera | Imatges | Rang |
|---|---|---:|---|
| Nikon Z 800/6,3 | Z5 II | 298 | 1/500–1/2 s, ISO 100 |
| FSQ-106ED (530 mm) | Z6 II | 225 | 1/250–1 s |
| Z 400/4,5 | — | 208 | 1/250–1 s |

Programari 2026: Astro D3F 2.0, PhaseCorr 8.0, LDIC 6.0, Corona 6.0, ACC 6.1.
I un detall que retrata tota la seva filosofia amb la Lluna: al compost de
800 mm «the black area occulted by the Moon is **not a circle**, but the
intersection of two circles» — les posicions lunars de C2 i C3 —, amb les
protuberàncies de just després de C2 i just abans de C3 **alhora**. Barregen
instants deliberadament, però de manera **declarada i igual als tres canals**.

És material directament comparable amb el nostre (mateix eclipsi, Sol baix,
rang d'obturació curt i 208-298 fotogrames): un patró or extern per contrastar
la forma de la nostra corona — amb la cautela que el seu producte tampoc no és
una mesura (D1 val per a tothom).

## §6. El mapa final: què fem igual, què fem diferent, què n'aprenem

| Peça | Brno (documentat) | Nosaltres |
|---|---|---|
| Composició | UNA mitjana ponderada per píxel (LDIC) | igual (fase 2, per D2/LDIC) |
| Màscara lunar | w=−1 per fotograma | igual |
| Marc de referència | corona (correlació de fase) | efemèride (99 §rectificació) |
| Redundància temporal per esglaó | 8-50 aparicions | **1-2** ← l'arrel del mal |
| Transparència variable | selecció + redundància + k(φ),q(φ) per segment | anivellament + coherència + **cura 2D per fotograma** (més enllà del seu públic) |
| Cel | restat al compost (centre de la Lluna) | restat (99: obligatori abans de fotometria) |
| Detall estructural | **només lluminància**, mai per canal | fase 3 sobre el canal G ← la porta oberta |
| Color | baixa freqüència, saturació ×50-400 | via §D del 100 (discriminador corona/cel) — coherent amb ells |
| Línies d'emissió | monocroma + narrowband on/off | (no en tenim) |
| Ciència | sobre el compost lineal SENSE filtrar | igual (norma del 97) |

**Tres decisions que aquest contrast reforça:**

1. **Per al producte d'avui:** la recomanació A del `104` queda reforçada — i
   la cura de fons (igualar la barreja temporal entre canals aplicant la cura
   del cel també a R i B) és exactament fer a mà el que la seva captura
   redundant fa sola. A més, el §4 suggereix una via complementària de cost
   zero: **compondre el detall de la fase 3 sobre una lluminància** (suma
   ponderada dels tres canals) en lloc del G sol — les estries per canal es
   promitgen i l'estructura real (que és compartida) es conserva.
2. **Per al 2027 (§1 quater):** els requisits 1 i 2 queden confirmats pel
   protocol de l'equip de referència, amb números: escala monòtona amunt-avall
   de factor 2, cadència de 0,3-3 s per fotograma sostinguda, i — si els dos
   trens ho permeten — **l'escala partida entre muntures** a l'estil Mamalluca
   2019 per doblar la cadència per nivell.
3. **Benchmark extern:** els composts de Trigaza són el contrast independent
   natural del nostre fusionat (mateix eclipsi, altre lloc, altra cadena).

⚠️ **Límits d'aquest document:** els interns del LDIC modern no estan
publicats (el que sabem ve del CAOSP 2006 i de la tesi del 2014); els
recomptes per nivell són inferits del total÷nivells; i el silenci d'una font
sobre un problema no demostra que el programari no el tracti — demostra només
que no ho documenten. Les cites són ≤14 paraules i totes duen font.
