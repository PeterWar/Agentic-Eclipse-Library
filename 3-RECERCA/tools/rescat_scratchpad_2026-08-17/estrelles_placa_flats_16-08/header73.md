> **Com llegir aquest document.** El §0 són les correccions que van sortir
> **després** que el cos del dossier estigués escrit, i tenen prioritat sobre
> ell. La resta és la referència de mètodes: qui és qui, què fa cada filtre,
> les fórmules exactes i què destrueix cadascun. El pla d'obra és a
> `research/74`.

---

## 0. Set correccions que tenen prioritat sobre la resta del document

Van sortir del crític de completesa i s'han verificat al disc, una per una.

### 0.1 El model de halo ja existeix, i el del §4.5 és pitjor

⚠️ **DEMOSTRAT al disc.** `~/Desktop/Eclipse 2026/Earthshine_FINAL/`, del 15
d'agost a les 20:26, conté un producte tancat amb
`earthshine_FINAL_halo_params.json`: **dos nuclis d'ales de PSF per canal**
—índexs 1,5 i 2,5, escales de 6/12 i 320 px— amb amplituds i rms per canal, i
un `LLEGEIX-ME.txt` que declara el mètode: *«dos nuclis d'ales de PSF sobre la
corona real + pla de cel»*, **sense** el mapa LROC dins de l'ajust. Validació
**fora de mostra** contra l'albedo LROC WAC: **r = 0,68** a escala completa i
**0,73** a mitja escala. Les eines són a `research/tools/halo_sony2_full.py`,
`halo_vixen_full.py`, `final_rgb_full.py` i `mesura_sony.py`.

Això obliga a dues correccions:

**(a) El §4.5 i el §8.2 diuen que la separació halo/earthshine «no està feta».
És fals: està feta i validada.** El que queda no és mesurar-la, és
**reajustar-la sobre dades no retallades** (§0.2) i estendre-la al Vixen.

**(b) El model radial `I(r) = E + A·(R_lluna − r + r₀)^−α` que proposava el
§4.5 és físicament pitjor que el que ja hi ha.** Assumeix que la llum difusa
dins del disc depèn només de la distància al limbe, o sigui **simetria
circular**. El halo dins del disc el genera **la corona**, que és fortament
asimètrica: bagues d'un costat, forats polars de l'altre. Un ajust radial
sobre un halo asimètric **absorbeix l'asimetria dins d'`E`**, i llavors `E`
ja no és earthshine. El model correcte és el que ja hi ha: **convolucionar la
corona real mesurada amb els nuclis d'ales i ajustar-ne només les amplituds**,
més un pla de cel.

**(c) I una restricció ja mesurada que no es pot ignorar:** el `LLEGEIX-ME`
diu que les capes Sony de 2 s i 1 s **i el Vixen sencer empitjoraven la
validació fora de mostra**. El producte bo és la pila Sony de **2×8 s**
(DSC06987 + DSC06993). Qualsevol proposta d'ajustar sobre «els dotze
fotogrames profunds dels dos cossos» va contra una mesura que ja s'ha fet.

**(d) La fotometria absoluta de l'earthshine és degenerada**, i el fitxer ho
declara: *«pedestal de halo/cel degenerat amb una constant»*. Qualsevol
criteri d'acceptació que exigeixi que l'earthshine dels dos trens **coincideixi
en nivell** compara dues constants no identificables i no mesura res. El
criteri ha de ser d'**estructura**: correlació espacial amb LROC WAC per tren
per separat, exigint el mateix mapa relatiu, no el mateix zero.

### 0.2 No desbayeris. Superpíxel 2×2

El §4.1 demana recalibrar sense retall i té raó, però la recepta que dona
manté `demosaic_algorithm=AHD`. **Interpolar el mosaic correlaciona píxels
veïns i barreja canals**, i això trenca tres coses del mateix flux: el
recompte de fotolocalitats saturades deixa de quadrar amb el RAW perquè la
saturació s'escampa als veïns; la σ per píxel deixa de ser la del sensor, i
per tant el llindar de 5σ deixa de voler dir res; i la màscara de saturació
per canal es contamina.

**Recepta correcta:** treballar amb els **quatre plans R, G1, G2, B a mitja
resolució** (superpíxel 2×2). A més surt gratis un estimador de soroll: la
diferència G1−G2 és soroll pur, píxel a píxel. El mostreig ja és el coll
d'ampolla a la visualització (§2.8); la fotometria no hi perd res.

### 0.3 Hi ha estrelles als fotogrames, i són el pont al calibratge absolut

El §5.5 conclou que sense la densitat òptica real del filtre solar no hi ha
calibratge absolut. **Hi ha una segona via i és la que Bemporad (2020) fa
servir de veritat**: dues estrelles de magnitud coneguda i la magnitud aparent
del Sol. A 8 s i f/2,8 amb 300 mm, i a 10,3 s amb el VSD90SS, **hi ha d'haver
estrelles al camp durant la totalitat**.

Resol quatre coses d'un cop: calibratge absolut sense mesurar el filtre; l'ala
de la PSF per la via d'`elderflower` que el §4.5 cita i no fa servir;
**resolució astromètrica del camp**, o sigui **orientació nord real** —ara
mateix el producte d'earthshine està en orientació de sensor, no de cel—; i
una comprovació independent de l'escala de placa.

Cost: mitja hora. Apilar les tres àncores i els tres fotogrames de 10,3 s,
córrer un resolutor astromètric, i fer fotometria d'obertura de les estrelles
del catàleg que caiguin al camp.

### 0.4 Hi ha dades externes del mateix dia i ningú no les ha demanades

**INFERIT, però comprovable en una tarda.** El 12 d'agost de 2026, a 18:28–18:30
UTC, SOHO/LASCO C2 i C3 observaven, i el K-Cor de Mauna Loa tenia les 08:30
del matí locals. LASCO C2 cobreix **2–6 R☉**, que és exactament la banda de
solapament dels dos trens; K-Cor cobreix **1,05–3 R☉** i és el que Bemporad
fa servir per a la intercalibració. I Predictive Science publica una
**predicció MHD per a cada eclipsi total**.

És calibratge absolut de franc i és **l'única validació externa real** de si
una estructura existeix. La prova de coherència entre trens del §5.6 és bona
però els dos trens comparteixen atmosfera, lloc, operador i dia; LASCO no.
Això s'ha d'afegir com a porta pròpia (el G7 de `research/74`).

### 0.5 El camp pla encara es pot fer

El §4.3 tracta l'absència de flat com un fet consumat i en deriva que el model
de halo deixa de ser físic. **Els dos trens encara existeixen i no s'han
desmuntat.** Un flat de panell o de cel crepuscular a la mateixa obertura i
focus, tret aquesta setmana, no és perfecte —el focus i la temperatura no són
els del dia— però el vinyetatge d'un refractor i d'un teleobjectiu és estable
si no es toca el diafragma.

Amb un flat aproximat, el terme empíric que barreja vinyetatge, PSF i cel es
redueix molt. **Cal dir-ho ara, mentre el muntatge encara es pot reproduir.**

### 0.6 El guany no es coneix, i sense guany els pesos de l'HDR no són òptims

El §4.4 recull que Druckmüller et al. (2006) declaren com a problema obert
*«how to find such values of pixel weights which would minimize the noise»*.
La resposta és coneguda i és **la inversa de la variància**:

$$\sigma^2_{\text{total}} = \frac{S}{g} + \sigma^2_{\text{lectura}}$$

amb $g$ el guany en electrons per compte. Sense $g$ no hi ha pesos òptims, i
el trapezi que proposa `research/74` és una aproximació raonable però no
òptima.

**El guany es mesura amb les dades que ja hi ha**, sense flats: corba de
transferència de fotons, o sigui mitjana contra variància d'un mateix pegat de
corona als setze esglaons d'exposició del R6. El pendent és $1/g$.

### 0.7 Cap criteri és una porta sense mapa d'incertesa

Tots els criteris d'acceptació d'aquest dossier i del pla són percentatges
—3 %, 5 %, 8 %, 25 %— sobre imatges que no porten pla de variància. **No es
pot dir si un 3 % és significatiu.** S'ha de propagar la variància per píxel
al llarg de la composició i lliurar `hdr_var_*.tif` al costat de `hdr_*.tif`.
Sense això, les fites són indicadors, no portes.

---
