> **AVÍS HISTÒRIC (27-07-2026):** document superat operativament per
> `controller v0.2.3 candidate`, F3/F3B/F3M i el disseny HDR nadiu. Es
> conserva com a evidència i no és autoritat operativa.

# Contrast final — control de captura de camp 2026

Data: 2026-07-26  
Estat: **decisió d'arquitectura provisional; compra i producció condicionades
al Gate físic de 48 hores**

## Veredicte

La decisió ja no és «Pico o gphoto». La ruta que maximitza la probabilitat
real de tornar amb imatges és:

> **RAW sense comprimir només a la SD + un temporitzador comercial cablejat,
> autònom i independent per cada rig.**

Per als dos rigs separats, el candidat principal a qualificar és **2 ×
LRTimelapse PRO Timer 3.5, un per càmera i amb un únic cable Sony curt per
rig**. Això conserva els avantatges que han vist Claude i els tres models
(RTC, inici programable, card-only, cap ordinador, cap ràdio) però elimina el
seu error arquitectònic comú: un sol LRT de dos ports és un punt únic de
fallada i obliga a estendre un cable entre muntures.

Si els dos equips formen físicament una única unitat rígida, un sol LRT amb
dos ports paral·lels és una simplificació acceptable. Si estan en trípodes o
muntures diferents, no és la configuració per defecte.

**Fallback de producció:** dos JJC TM-F2, un per rig, si el LRT no arriba a
temps o falla el Gate.  
**gphoto2:** banc de laboratori i últim fallback qualificat, no ruta principal
de C2–C3.  
**Pico/GNSS i BLE no oficial:** retirats de producció.  
**Hähnel:** només es reobre si cal separar físicament els rigs i no es poden
tenir dos temporitzadors cablejats independents.

Confiança actual en l'arquitectura: **84/100**. Confiança en un model concret
de temporitzador abans del Gate: **55/100**.

## Què han dit els quatre revisors

| Revisor | Principal | Fallback | Sincronia | Confiança declarada |
|---|---|---|---|---:|
| Claude Fable 5 Extra | 1 LRT, dos ports | 2 JJC | desfasar; amb rigs separats, JJC principal | 78 |
| Gemini 3.1 Pro | 1 LRT, dos ports | 2 JJC | desfasar | 95 |
| Grok 4.5 | 1 LRT, dos ports | 2 JJC | desfasar | 78 |
| NVIDIA Nemotron 3 Ultra | 1 LRT, dos ports | 2 JJC | simultani | 85 |

Consens 4/4:

- card-only i RAW sense comprimir;
- temporitzador comercial cablejat com a candidat principal;
- LRT per davant de JJC, interval intern, Hähnel, gphoto i Pico;
- cap Mac, USB/PTP o Internet dins la finestra crítica;
- el continuous bracket, el rellotge i la cadència s'han de mesurar;
- la captura densa és més important que una fotografia única «exacta».

Aquest consens és útil, però està parcialment ancorat per les opcions del
prompt. Cap model va proposar espontàniament la variant que resol millor el
camp: **dos LRT independents, un per rig**.

## Correccions de l'auditoria

### 1. El trigger físic encara no està demostrat

El prompt enviat deia que una pulsació sostinguda havia completat físicament
el bracket als dos cossos. La documentació viva diu una altra cosa:

- s'han obtingut cinc ARW amb una **pressió virtual gphoto/PTP**;
- el temps dual de 2,361 ms és separació entre ordres enviades, no inici òptic
  d'exposició;
- [Gate 9](../../tests/2026-07-26_GATE9_CARD_ONLY_TRIGGER_PROTOCOL.md) continua
  marcat `9A PENDENT DE DISPARADOR FÍSIC`.

Per tant, cap LRT, JJC o Hähnel està encara qualificat per producció. El prompt
es conserva sense reescriure per mantenir l'auditoria de què van rebre els
models.

### 2. Els buits de 2024 són reals; la causa única no

La [forense RAW 2024](../12_FORENSICA_RAW_2024.md) prova els buits de 30 s i
125 s i la numeració contínua de la càmera. L'[autòpsia
causal](../13_AUTOPSIA_CAUSAL_2024.md) prova una arquitectura fràgil —processos
nous, cap timeout, cap readback, cap watchdog i antecedents de 50,57 s obrint
PTP—, però no permet afirmar que una sola funció de gphoto causés el buit de
125 s.

Conclusió correcta: **no condemnem gphoto per una causalitat no provada; el
retirem del camí crític perquè el seu risc estructural sí que està provat.**

### 3. El «fallback calent» d'un LRT dual és fals

Si un únic LRT governa les dues càmeres i falla a C2, reconnectar dos JJC en
menys de 60 s no salva una totalitat de 88–91 s. És un fallback previ a
l'eclipsi, no calent. Dos controladors principals independents contenen la
fallada: si un mor, l'altre rig continua sense cap intervenció.

### 4. Especificacions que no existeixen

El fabricant del LRT sí documenta:

- mode temporitzat per data/hora;
- `Release Time` configurable en mil·lisegons;
- segon port que dispara en paral·lel;
- resolució normal de 0,1 s;
- RTC i bateria interna.

No publica:

- exactitud UTC, ppm o deriva del RTC;
- skew entre ports;
- garantia de continuous bracket Sony;
- compatibilitat literal amb `A7RIIIA` —llista A7RIII;
- una cadència sostenible amb cinc RAW sense comprimir.

El JJC sí llista explícitament A7III i `a7R3A`, dos AAA, delay, exposició,
interval i fins a 399 captures o il·limitades. No publica sincronització entre
dues unitats ni continuous bracket Sony certificat.

### 5. Propostes externes que es rebutgen

- No es faran 1.800 RAW en sis minuts ni s'assumirà un bracket per segon:
  l'A7RIIIA genera aproximadament 425 MB per bracket de cinc RAW observats.
- No s'assumiran extensions d'àudio de 3 m al camí de shutter.
- No s'usarà so d'obturador com a telemetria: treballem amb `Silent Shooting`.
- No es dirà que el LRT treballa en UTC: té data/hora local; l'offset real es
  mesura.
- No es congela cap velocitat base de l'A7RIIIA fins que passi el Gate 9C de
  cobertura.

## Arquitectura de camp proposada

### Rigs separats — configuració preferida

```text
Rig 1: A7RIIIA + AP130GTX/QUADCC
       └─ LRT #1 ─ cable Sony curt ─ càmera ─ SD UHS-II Slot 1

Rig 2: A7III astromodificada + 300 mm GM
       └─ LRT #2 ─ cable Sony curt ─ càmera ─ SD UHS-II Slot 1
```

Propietats:

- cada rig es mou com una sola unitat;
- zero cable entre trípodes;
- zero ràdio, pairing, hub, Mac o Internet;
- una fallada conserva almenys una seqüència;
- cada temporitzador pot tenir programa, cadència i fase propis;
- exactament una caixa acabada i un cable curt per càmera.

### Rigs realment units

Un LRT central amb dos ports és acceptable si:

- els cables no travessen una zona de pas;
- la fallada/desconnexió d'un port no afecta l'altre;
- el risc comú s'accepta perquè el conjunt ja és una única unitat mecànica;
- passa tres simulacions dobles completes.

### Fallback JJC

Dos TM-F2 són més simples i independents, però tenen resolució d'un segon i
dos rellotges relatius. Poden ser principals si:

- completen el continuous bracket de cinc RAW;
- el delay llarg i la deriva cobreixen la finestra amb marge;
- el sistema queda armat abans de C2 sense manipulació crítica;
- tres tandes dobles de 120 s donen zero errors.

### Hähnel

Només aporta valor si no es pot cablejar cada rig localment. El sistema
timer + dos receptors elimina el cable entre muntures, però afegeix ràdio,
pairing, sis piles AA aproximadament i un transmissor comú. No millora la
sincronització absoluta i programa en passos d'un segon.

## Temps de l'eclipsi: precisió suficient, no falsa precisió

L'objectiu fotogràfic no és que les dues càmeres obrin l'obturador al mateix
mil·lisegon. És no tenir cap buit rellevant al voltant de C2 i C3.

Procediment:

1. Calcula C2/C3 finals per a la coordenada exacta.
2. Sincronitza els dos temporitzadors amb la mateixa referència abans de la
   sessió i mesura l'error real.
3. Arma una finestra que comenci amb desenes de segons de marge abans de C2 i
   acabi després de C3; el marge final surt del Gate, no d'una xifra inventada.
4. Si hi ha dos temporitzadors, desfasa el segon aproximadament mig cicle
   **mesurat**. Això augmenta el mostreig temporal i desacobla els moments de
   búfer/escriptura.
5. No depenguis d'un únic fotograma al contacte. Ordena el bracket perquè la
   presa curta útil aparegui on el Gate 9A-C demostri que és determinista.

Per a recerca metrològica de contactes, GNSS 1PPS i calibració de shutter lag
serien un projecte separat. No són necessaris per obtenir una seqüència
fotogràfica robusta i no han d'entrar al controlador de camp d'aquest any.

## Gate de 48 hores que decideix de debò

### G0 — cable, boot i desplegament

- un LRT/JJC fixat a cada rig;
- una sola connexió curta;
- power-cycle i sleep/wake sense falsos dispars;
- control de cada rig desplegable en menys de dos minuts;
- cap cable entre rigs.

**FAIL:** qualsevol fals trigger, connector insegur o necessitat
d'ordinador/pairing.

### G1 — semàntica física del hold

Per cada cos:

- provar una graella de `Release Time`;
- 20 brackets inicials per valor;
- fixar el primer valor que dona exactament cinc ARW;
- executar **100/100** cicles amb exactament cinc RAW.

**FAIL:** un sol 0/5, 1–4/5, 6+/5, shutter enganxat o estat residual.

### G2 — integritat d'imatge

- RAW sense comprimir;
- 14 bits reals;
- només SD UHS-II Slot 1;
- zero JPEG, zero fitxer al Mac;
- escala d'exposició exacta;
- hashes únics i numeració contínua.

**FAIL:** qualsevol canvi de format, destí o bracket.

### G3 — cadència i búfer

Per cada cos i després tots dos:

- 3 × 120 s amb la SD, bateria i perfil finals;
- mesurar durada real del bracket i activitat de la llum SD amb vídeo;
- apuntar les càmeres a un cronòmetre visual offline per mesurar els gaps;
- producció = cadència més ràpida que conserva **25% de marge** sobre el pitjor
  cicle observat.

**PASS:** recompte exacte `N × 5`, zero gap fora del pressupost i zero deriva
sistemàtica. No es fixa ara `0,3 s`, `1 s` o `2 s`.

### G4 — rellotge i fase

- posar els dos RTC a T0;
- programar arrencades a +2 h i +24 h;
- fotografiar un cronòmetre visual per mesurar offset real;
- repetir després d'apagar/encendre.

**PASS fotogràfic:** l'error queda molt dins la banda de guarda i la fase entre
rigs és repetible. No s'exigeix 1PPS.

### G5 — contenció de fallades

- desconnectar/apagar un temporitzador;
- afluixar un cable;
- simular bateria baixa;
- deixar dormir i despertar càmera/temporitzador;
- confirmar que el segon rig no s'atura.

**FAIL:** un incident en un rig afecta l'altre o deixa shutter premut.

### G6 — mudança real

Empaquetar, moure, remuntar sense Internet i repetir una tanda doble de 120 s.

**PASS global:** zero errors en G0–G6. Després es congelen firmware,
configuració, cables, SD, piles i checklist.

## Compra mínima

Si es poden rebre i provar immediatament:

1. **2 × LRTimelapse PRO Timer 3.5**;
2. **2 × cable 2,5 mm TRS → Sony Multiport RM-SPR1/S8** correcte;
3. **2 × JJC TM-F2** només si el cost és petit respecte del risc, com a ruta
   alternativa completa ja qualificada;
4. elements de fixació i protecció de pluja simples, sense connectors
   improvisats.

Senyal d'estoc consultat el 2026-07-26: el fabricant va anunciar el 21 de
juny que el 3.5 tornava a estar disponible i
[Black Forest Motion el mostra en estoc](https://blackforestmotion.com/en/produkt/lrtimelapse-pro-timer-3-bundle/).
Un altre distribuïdor el mostra a 159 CHF i especifica que
[el cable de càmera no va inclòs](https://www.fotichaestli.ch/en/lrtimelapse-pro-timer-3.5-camera-interval-timer/).
Cal confirmar lliurament real a Espanya abans de pagar; «en estoc» no
substitueix una data de lliurament.

Si només es pot obtenir un LRT a temps, no es converteix automàticament en
màster dual:

- rigs units: provar-lo amb dos ports;
- rigs separats: LRT en un rig i JJC en l'altre, o dos JJC, prioritzant
  independència.

No comprar ara:

- Pico, GNSS, optoacobladors, plaques o caixes a fabricar;
- hubs, cables USB llargs o un altre Mac;
- Hähnel abans de demostrar que dos controls cablejats locals no són viables;
- extensions de shutter no qualificades.

## Quan tornaria gphoto a ser candidat

Només si tots els temporitzadors físics fallen la semàntica de bracket i el
[Gate 8](../../tests/2026-07-25_GATE8_PC_CAMERA_SD_PROTOCOL.md) supera:

- 3 tandes dobles completes de 120 s;
- zero `set-config`, `wait-event` o drenatge dins C2–C3;
- cap transferència RAW inesperada;
- exactament cinc RAW per trigger i cap cua residual;
- fallada d'un procés/cos sense afectar l'altre;
- release físic independent.

Fins aleshores, conservar el controlador gphoto és prudent; tornar-lo a posar
al centre de C2–C3, no.

## Fonts primàries de producte

- [Manual LRTimelapse PRO Timer](https://lrtimelapse.com/lrtpt/manual/)
- [Cables LRT per càmera](https://lrtimelapse.com/lrtpt/camera-release-cables/)
- [Hähnel Captur Timer Kit for Sony](https://www.hahnel.ie/irish-shop/captur_timer_kit_for_sony/)
- [JJC TM-F2 oficial](https://www.jjc.cc/index/goods/detail.html?id=469)

## Artefactes de la ronda

- [Prompt comú](PROMPT.md)
- [Metadades, errors i cost](RUN_METADATA.md)
- [Claude Fable 5 Extra](responses/claude_fable_5_extra.md)
- [Gemini 3.1 Pro Preview](responses/gemini_3_1_pro_preview.md)
- [Grok 4.5](responses/grok_4_5.md)
- [NVIDIA Nemotron 3 Ultra](responses/nvidia_nemotron_3_ultra.md)
