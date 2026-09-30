# 81 — El tutorial d'Astrofalls, pas per pas, i el seu encaix al projecte

**18 d'agost de 2026.** Distil·lat del vídeo de postprocessat d'Astrofalls
(*Total Solar Eclipse Workflow*, lliçó «2023 Eclipse Video», Vimeo 904827483,
1 h 44 min). Transcripció verbatim a
`research/81A_TRANSCRIPCIO_PRIVADA_ASTROFALLS_ECLIPSE_VIDEO.md`. El dataset que hi edita
és **l'eclipsi total més recent a Austràlia** (20-04-2023 a Exmouth, inferit),
**a prop del màxim solar** —corona de llaços i no de plomalls, moviment ràpid,
vermell per tot el limbe i una CME flotant—, o sigui **el mateix règim que ens
espera el 12-08-2026**. Dataset cedit per «Alessandro Da Benedictus» (nom
fonètic).

Aquest és el **segon** cop que Astrofalls entra al projecte: el `research/68`
en va treure el requisit de captura (balanç de blancs manual, no Auto), però
sense el flux d'edició. Aquí hi ha el flux sencer.

**Convenció de marcatge** (la del projecte): **DEMOSTRAT** (dit i mostrat al
vídeo), **INFERIT** (es dedueix), **NO VERIFICAT** (útil, però no comprovat
sobre els nostres fitxers).

> ⚠️ **Naturalesa d'aquest flux, i per què importa.** Astrofalls és un flux
> **estètic** de Photoshop —màscares a mà, Topaz, Clarity, corbes «al gust»—,
> **no** conserva la fotometria i no pretén ser ciència. El nostre producte
> científic (`research/73`/`74` i la skill `postprocessat-corona`) fa
> exactament el contrari: realçat només a l'última porta, sobre una còpia,
> amb la fotometria intacta. Per tant aquest tutorial alimenta el lliurable
> **WOW / estètic** (l'objectiu doble de «impressionant *i* fidedigna» de la
> imatge final), i moltes de les seves receptes —Topaz, Clarity, path blur,
> corbes subjectives— **no poden tocar mai** el compost calibrat. On sí que
> encaixa i on xoca és a §3.

---

## 0. Les tres coses que val la pena endur-se

**1. L'eliminació del gradient de color atmosfèric — resol directament el
problema del `NoEncaixa.tif` de Pere.** Després de l'HDR, la corona surt
**taronja al centre i blava a fora**: és l'atmosfera (el cel de dia tenyeix de
blau, i el gradient del Sol crema de taronja cap endins), no la corona. El
`research/80` descriu exactament aquest símptoma a la capa de Pere: «un gradient
circular concèntric al sol de diferents colors». Astrofalls el treu així
(DEMOSTRAT):

- **Via fàcil: DBE de PixInsight.** Desa l'HDR com a TIFF, obre'l a PixInsight,
  *Background · Dynamic Background Extraction*, posa mostres —als cantons, a
  prop dels plomalls, **evitant els llaços grossos**—, mode **Subtract**, i
  extreu el fons. Queden dues imatges: la corona neta (sense el blau del cel) i
  el **fons** (gradient de color + vinyeta), que desa com a `BG`.
- **Via Photoshop (si no hi ha PixInsight).** Reescala el `BG` a la mida del
  compost (aquí 3864 px a l'eix curt), copia'l a sobre; **duplica l'HDR**, posa
  el duplicat en mode **Color**, el `BG` a sota en mode **Subtract**
  (alt-clic per encaixar-los) → treu el gradient de color. Queda «la corona com
  si fóssim a l'espai».
- **Tornar-hi a posar el blau del cel sense el taronja central**: capa nova,
  pot de pintura amb el **blau de fora**, mode **Screen**, i regula la
  brillantor amb corbes → la corona travessa el color de l'atmosfera però ja
  sense els tons ultracàlids del mig.
- **Senyal que ho has fet bé**: la corona neta surt **lleugerament verda**
  (INFERIT: emissió Fe XIV 530,3 nm) —«the corona is supposed to be green
  slightly»—; és bo, encara que estèticament ell la torna cap a magenta.

**2. Les màscares HDR van molt més borroses del que sembla, i tot anell és
subblur.** «Most people are afraid to blur it enough and then they end up with
the artifacts.» El blur gaussià de cada màscara de lluminositat **creix cap
enfora**: 10 → 40 → 80 → 90 → 355 i fins a 400 px a les capes exteriors. Si
veus un **anell** (ringing) o una vora de brillantor no natural, és que has
blurat poc; i si necessites *massa* blur, torna enrere i **enfosqueix els
Levels de la màscara** per mantenir-la natural. Cada transició, imperceptible.
→ Directament rellevant al **«graó HDR» del Vixen** (la ratlla tangencial a
1,8 R☉ de la memòria HDR4 / `research/80`) i als anells que Pere combat a mà.

**3. Al màxim solar canvia la caixa d'eines.** La corona és de **llaços i
ejeccions**, no de plomalls radials. Conseqüències (DEMOSTRAT al vídeo):

- el **path blur** (desenfoc direccional) és **gairebé inútil** —només serveix
  al mínim solar o activitat mitjana—; l'única capa que sí que es pot path-blur
  és la del **realçat radial pur**, perquè no conté cap detall tangencial;
- el **filtrat tangencial (radial blur en mode *zoom*)** és el que treu els
  llaços, i és aquí on hi ha la feina;
- els **radis dels filtres radials són molt més petits** que al mínim (2017 feia
  ~20 px; aquí n'hi ha prou amb 1–3 px) perquè el contrast intrínsec és molt més
  alt;
- hi ha **vermell (H-alfa) per tot el limbe**, no només a un parell de
  protuberàncies, i sovint una **CME flotant** desenganxada del disc que **viu
  a les exposicions llargues**, no a les curtes.

---

## 1. El flux sencer, fase per fase

Tot és Photoshop (amb un pas opcional a PixInsight per al gradient) i **sobre un
sol bracket**: aquest dataset té ISOs i temps canviants i **no es pot apilar**;
el màxim solar dona prou contrast per compensar-ho (DEMOSTRAT).

1. **Preparació dels RAW (Camera Raw).** Carrega'ls «as shot»; posa **tots** a
   balanç **Daylight** a mà (venien amb Auto WB), **tot el detall/soroll a
   zero**, i desa'ls immediatament com a **TIFF de 16 bits**. Cap altra edició.
   → És el mateix requisit del `research/68`.

2. **Registre (alineació frame a frame).**
   - Els **dos primers** fotogrames (curts): alinea per **protuberàncies**, capa
     de dalt en mode **Difference**, mou fins que la protuberància gran
     desapareix. ⚠️ **La Lluna enganya**: tapa-la mentalment i jutja per la
     protuberància, no pel disc.
   - La resta: **high-pass + Difference**. Grups amb còpia, *High Pass* ~10 px
     (puja a ~19 px per a la corona exterior), aplica el preset de Levels,
     grup en **Difference**, i amb **Ctrl** premut mou fins a minimitzar la
     diferència dels plomalls. Radi de high-pass **més gran** com més exterior.
   - ⚠️ **Al màxim solar la corona es mou entre subfotogrames** (fins i tot dins
     un bracket): jutja per **moviment**, no només per diferència. El fotograma
     més llarg i brillant pot no ser alineable —descarta'l.
   - En acabar: esborra els high-pass (**no** els grups), treu cada imatge
     alineada del seu grup, esborra els grups, i desa com a `registered`
     (local, mai al núvol).

3. **Barreja HDR (màscares de lluminositat ponderades).**
   - **Retalla** primer per treure artefactes de vora que molesten els blurs.
   - De baix cap amunt, per capa: `Ctrl+A`, `Ctrl+C` de la imatge, afegeix
     màscara, enganxa dins la màscara; amb **Levels** puja la zona ben exposada
     cap a la imatge i baixa els negres; amb **Curves** aclareix el detall,
     aixafa els negres i **protegeix els alts** (retalla fort l'extrem alt per no
     cremar les protuberàncies).
   - **Blur gaussià fort a cada màscara** (§0, punt 2). Els anells = subblur.
   - Capes exteriors: la màscara ha de ser **més petita / més a prop de la
     corona**; una que demani 600 px ja és massa. Inclou el fons com a blanc
     per a la corona exterior més neta, però **sense retallar tant els alts** que
     el fons quedi transparent (cal textura, no buit).
   - Desa el fitxer HDR a part. **Duplica la capa de corona interior** abans
     d'aplanar i **guarda la corona exterior en reserva**. Fusiona.

4. **Treure el gradient de color** (§0, punt 1). PixInsight DBE o el truc
   Color/Subtract + re-injecció del blau per Screen. Aplana.

5. **Centrar la Lluna.** Crop cap enfora, fletxes per afinar el disc al centre,
   i **pot de pintura** amb el to de fons a les vores (això ajuda els blurs
   radials després).

6. **Filtrat radial (spin) — detall radial/plomalls.** Sis còpies (A/B/C ×1/2/3).
   *Radial Blur · Spin* petit → *Image · Apply Image*, capa 1, **Subtract**,
   escala/offset **128**, Levels de corona: és un high-pass rotacional. Al màxim
   solar n'hi ha prou amb **2 capes** (no 3) i radis petits. Barreja-les en
   **Overlay**; *Dust & Scratches* 1 px, llindar ~20; **desatura** (només vols
   luminància). Centra els histogrames (no canviïs la brillantor). Cura els
   **grans de pols** amb el pinzell corrector (al filtre radial es converteixen
   en ratlles de motion blur, pitjor lluny del centre) — per això s'omple el
   fons.

7. **Filtrat tangencial (zoom) — els llaços del màxim solar.** ⚠️ **Omple el
   centre de la Lluna primer** (si no, artefactes): *Select Subject* → màscara →
   pinta-hi el to de corona; *Filter · Other · Maximum* (roundness ~6–7 px) per
   fer créixer la màscara net fins a la vora del disc. *Radial Blur · Zoom*
   (~13 px, comença gran per tenir senyal) → *Apply Image*, capa 1, Subtract,
   Levels. Capa tangencial en **Overlay**, puja Levels (histograma centrat),
   **desatura**. Màscara negra + pinzell tou només a la **corona interior** i
   plomalls brillants (allà viu el detall tangencial). **Topaz** (soroll sever /
   màxim, **sense** sharpen) per treure'n el soroll; màscara amb cura, **mai** a
   les protuberàncies.

8. **Incorporar el detall filtrat a l'HDR.** Porta les capes de detall amb
   **màscara de lluminositat** de l'original; posa-les en **Luminosity** (així
   conserves el color vermell i no viren a verd) i les de realçat en **Overlay**.
   Màscares estrictes (sobretot interior; limita la fuita de l'artefacte radial).
   Afegeix filtres radials cada cop més petits (**3 px → 1 px**; l'1 px només se
   sosté amb molt senyal, i el màxim solar en té). **Rota la imatge** de tant en
   tant: mirar-la tanta estona «entumeix» l'ull. Repara els **anells de la
   màscara HDR** amb capa nova i pinzell tou (aclareix l'anell fosc, enfosqueix
   l'interior brillant, blur ~15 px). Fes servir **Clarity** (Camera Raw) per al
   contrast local quan el high-pass renta el detall.

9. **Protuberàncies i cromosfera (vermell per tot el limbe).** Torna als RAW,
   alinea a les protuberàncies i **pinta-les amb el seu color real**. El fons
   negre darrere la protuberància no fa bon HDR → pinta amb compte. La **CME
   flotant** viu a les **exposicions llargues** (obre la 2a, no la més curta) i
   cal pujar-li Clarity, saturació, exposició i un pèl de NR de color per
   encaixar-la (màscara «funky»: inversa, colors girats, blur gran ~7 px, pinta
   fora els anells).

10. **Soroll de la corona exterior.** La capa més exterior és molt sorollosa:
    Topaz **petit** + recupera detall original, i després **NR tradicional de
    Camera Raw**. El **path blur** només a la capa de realçat radial pur (§0,
    punt 3), ~16 %, i *Dust & Scratches* 2–3 px.

11. **Anell de diamant / moment de contacte.** En lloc de «fregir» la Lluna per
    fer-la natural, **composa un fotograma d'anell de diamant**: agafa el RAW de
    l'anell, mode **Screen** a plena opacitat, col·loca'l, i **emmascara'l fora**
    d'on el vols (protegeix la protuberància ja treballada). Neteja les parts
    interiors rentades.

12. **Vora de la Lluna.** Amb un RAW original (rotat per encaixar, aquí 180°),
    màscara de lluminositat (el *Select Subject* de Photoshop falla amb les
    protuberàncies), pot de pintura negre + pinzell dur per omplir només el disc,
    blur gaussià ~1 px per netejar la vora. Fusiona.

13. **Final (Camera Raw).** Compte amb la **saturació**: massa i la corona vira
    al seu **verd** natural (senyal que el gradient s'ha tret de debò). Ell la
    manté cap a magenta/neutra; sovint «no fer res» és millor. «Eclipse editing
    is the hardest thing to edit in astrophotography… trying to get it natural is
    a near impossible task.»

---

## 2. El règim del màxim solar (el nostre cas el 2026)

- **Llaços, no plomalls.** El detall dominant és tangencial; l'eina és el filtre
  **zoom**, no el radial pur. El nostre `research/73`/`74` ja tenen filtres
  radials/tangencials (unsharp radial, ACHF…); això confirma que al 2026 **el
  pes ha d'anar al canal tangencial**.
- **Path blur descartat** com a eina general (només corona de plomalls). Bo
  saber-ho abans de perdre-hi temps.
- **Moviment ràpid**: la corona canvia entre subfotogrames, i això complica
  l'alineació *i* l'apilat. Nosaltres **sí que apilem** (68 fotogrames al Vixen,
  `research/76`), o sigui que aquest moviment és un límit a vigilar a les nostres
  piles llargues, no un problema que Astrofalls hagi de resoldre (ell no apila).
- **Vermell per tot el limbe + CME flotant a les exposicions llargues.** La
  nostra escala HDR de missió arriba a exposicions llargues (àncores i el 10,3 s
  del Vixen): la cromosfera i una eventual CME hi seran, i cal **anar-les a
  buscar a les llargues**.

---

## 3. Encaix amb el pipeline del projecte

**El que adoptem sense reserves (compatible amb la ciència):**

- **L'eliminació del gradient de color atmosfèric** (§0.1). És el que Pere
  necessitava per al `NoEncaixa.tif` (`research/80`). ⚠️ Matís de fotometria:
  el DBE / la resta de fons és **estètic**; si es vol al producte **calibrat**,
  el fons atmosfèric ja el modelem millor amb el nostre calibratge absolut i el
  model de cel (`research/75`/`76`), i el gradient de color s'ha de treure
  **sobre una còpia de realçat**, no sobre el compost lineal. Per al lliurable
  WOW, el truc de Photoshop és perfecte.
- **Blur fort a les màscares HDR i «tot anell és subblur»** (§0.2): val per als
  nostres graons HDR (Vixen 1,8 R☉).
- **Registre per protuberància (interior) + high-pass Difference (exterior)**
  com a tècnica manual de rescat quan el registre automàtic al Sol
  (`research/76`) no arriba a un fotograma concret.
- **Omplir la Lluna abans del filtrat zoom/radial** (§1.7): comprovar que els
  nostres filtres de la skill ho fan; si no, és un artefacte que ens espera.
- **Anell de diamant per Screen** (§1.11): encaixa amb l'objectiu de perles i
  anells i amb l'`efecte-3d-superponer` de la memòria.

**El que NO pot tocar el compost calibrat (només el lliurable estètic final):**

- **Topaz Denoise, Clarity, corbes «al gust», path blur, saturació a ull.** Cap
  no conserva la fotometria; van tots a l'última porta sobre una còpia, mai al
  producte de B/B☉. És exactament la primera regla del `research/73`.
- El seu **realçat per high-pass rotacional/zoom** és una família germana del
  nostre unsharp radial / ACHF, però amb paràmetres triats a ull; el nostre
  pipeline els vol amb la porta fotomètrica al davant.

**On es contradiuen, mana el projecte** (ordre del `CLAUDE.md`): identitat i
evidència física, codi i perfils, QA, i la ciència de `73`/`74`. Astrofalls és
**referència de mètode estètic**, com els papers de Brno ho són de mètode
científic — no autoritat sobre el nostre producte calibrat.

---

## 4. On és la font

- Transcripció verbatim privada (fora d'exports públics):
  `research/81A_TRANSCRIPCIO_PRIVADA_ASTROFALLS_ECLIPSE_VIDEO.md`.
- Vídeo: curs privat d'Astrofalls, Vimeo 904827483 (requereix la sessió de Pere
  a `astrofalls.com`).
- Requisit de captura que ja en va sortir: `research/68` (balanç de blancs
  manual, no Auto).
- Pipeline científic amb què es contrasta: `research/73`, `research/74`, i la
  skill `postprocessat-corona`.
