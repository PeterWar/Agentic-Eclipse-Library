> **AVÍS HISTÒRIC (27-07-2026):** document superat operativament per
> `controller v0.2.3 candidate`, F3/F3B/F3M i el disseny HDR nadiu. Es
> conserva com a evidència i no és autoritat operativa.

# Tancament de la fase prospectiva — captura

Estat: **arquitectura conceptual gairebé tancada; falten inputs físics i assajos, no més recerca generalista**.

Revisió 26-07-2026: la ruta de C2–C3 queda fixada conceptualment com a
card-only, RAW sense comprimir al Slot 1 UHS-II i trigger independent. Les
referències posteriors a `PC Only/PC+Camera` es mantenen només per al
laboratori o fallback.

Abast d'aquest document:

- només adquisició d'imatges;
- plans A, B i C tractats com a perfils operatius;
- cap decisió de postprocessament;
- cap implementació del controlador;
- cap predicció meteorològica.

## Veredicte

La fase prospectiva es pot donar per tancada quan quedin definits cinc elements:

1. **punt d'observació exacte i perfil d'horitzó** de cada pla;
2. **topologia física** de muntures, alimentació, ports i operadors;
3. **conjunt mínim d'imatges que no es pot sacrificar**;
4. **protocol segur de filtres, focus i contactes**;
5. **matriu d'assajos i criteris d'acceptació** que decidirà les opcions encara reversibles.

Els hotels resolen la base logística, però no els punts 1–5. L'hotel no s'ha de convertir automàticament en lloc d'observació.

## 1. Perfils A, B i C

### Fonts i convencions

Font temporal principal:

- [taula municipal de l'Instituto Geográfico Nacional](https://astronomia.ign.es/resources/informacion-astronomica/eclipses/tablas/eclipse-sol-12-08-2026-tabla.html);
- [pàgina general IGN](https://astronomia.ign.es/eclipses-de-sol-y-luna/eclipse-total-sol-de-12-de-agosto-2026);
- altures i azimuts contrastats amb [JPL Horizons](https://ssd.jpl.nasa.gov/horizons/).

Convencions:

- hora local peninsular, CEST, UTC+2;
- azimut des del nord vertader en sentit horari;
- altura geomètrica/airless per comparar òptiques;
- coordenades representatives del municipi, **no de l'hotel ni del camp final**.

### Circumstàncies representatives

| Pla | Punt representatiu | C1 | C2 | Màxim | C3 | C4 | Totalitat |
|---|---|---:|---:|---:|---:|---:|---:|
| A | Ferrol, 43.484699, −8.233046 | 19:30:40 | 20:27:17 | 20:28:00 | 20:28:45 | 21:21:40 | 88 s |
| B | Medina de Rioseco, 41.8831, −5.0439 | 19:33:59 | 20:29:27 | 20:30:12 | 20:30:58 | 21:22:53 | 91 s |
| C | Deltebre, 40.717303, +0.738444 | 19:36:10 | 20:29:54 | 20:30:40 | 20:31:25 | ~21:21:59 | 91 s |

Al perfil C, el C4 és geomètric però el Sol ja és sota l'horitzó. L'IGN dona la posta a Deltebre aproximadament a les 20:59:14, uns 27 min 49 s després de C3.

Les fonts poden diferir algun segon perquè no totes apliquen el mateix radi solar, refracció, ΔT o perfil del limbe lunar. NASA indica que el relleu lunar pot modificar durades/contactes aproximadament 1–3 s. Els temps anteriors serveixen per dissenyar, no per programar el controlador final.

### Geometria a la totalitat

| Pla | Altura a C2 | Altura al màxim | Altura a C3 | Azimut al màxim | Massa d'aire aproximada |
|---|---:|---:|---:|---:|---:|
| A — Ferrol | 12,024° | 11,896° | 11,761° | 279,194° | 4,72 |
| B — Medina | 9,034° | 8,897° | 8,758° | 281,928° | 6,16 |
| C — Deltebre | 4,456° | 4,316° | 4,180° | 285,831° | 11,23 |

La massa d'aire és només el valor comparatiu modelat per JPL. A 4° la refracció, els aerosols i les capes baixes fan que qualsevol model simple sigui fràgil.

### Incertesa espacial

Els perfils representen municipis, no regions senceres:

- Ferrol i Fene difereixen poc; A Coruña ja té contactes i durada diferents.
- Deltebre i Sant Jaume d'Enveja són semblants; Amposta es desplaça alguns segons; la Ràpita, més.
- Al voltant de Medina, moure's desenes de quilòmetres pot canviar els contactes desenes de segons.

Regla:

> C2, C3 i el perfil de limbe es regeneren amb la coordenada WGS84 exacta del trípode o muntura, no amb el nom de l'hotel ni del municipi.

## 2. Què canvia realment entre els tres plans

### Durada

La diferència representativa és només de tres segons. Això permet:

- un únic controlador;
- una única arquitectura de fases;
- un **nucli mínim dissenyat per als 88 s de Ferrol**;
- repeticions opcionals governades per la durada local.

No calen tres programes diferents. Calen tres fitxers de circumstàncies i exposició.

### Atmosfera

La diferència decisiva és:

- extinció;
- brillantor i gradient del cel;
- dispersió cromàtica;
- seeing de baixa altura;
- fons vermell sobre la A7III modificada;
- exposició llarga màxima útil.

El perfil C no pot heretar automàticament l'escala HDR del perfil A. El patró de bràqueting pot ser el mateix, però les tres velocitats base han de poder formar part del perfil del lloc.

### Posta de Sol

- **Ferrol:** C4 encara és visible, si l'horitzó físic ho permet.
- **Medina:** C4 és molt pròxim a la posta i pot quedar compromès per refracció o relleu.
- **Deltebre:** C4 no és observable; el guió post-C3 ha d'acabar per posta, no esperar C4.

Per a la corona, C2–C3 continua complet en els tres perfils.

## 3. El camp de visió converteix l'horitzó en part de l'òptica

Semialçada aproximada del sensor en orientació horitzontal:

| Tren | Camp vertical total | Del centre a la vora vertical |
|---|---:|---:|
| AP130GTX + QUADTCC, 585 mm | 2,34° | 1,17° |
| Sony 300 mm | 4,56° | 2,28° |

Altura teòrica de la vora inferior a C3, amb el Sol centrat:

| Pla | AP/585 | 300 mm |
|---|---:|---:|
| Ferrol | 10,59° | 9,48° |
| Medina | 7,59° | 6,48° |
| Deltebre | 3,01° | 1,90° |

Conseqüència:

- al Delta, un obstacle de més d'uns **1,9°** pot entrar al camp del 300 mm encara que el disc solar sigui perfectament visible;
- per a l'AP, el llindar equivalent és aproximadament 3°;
- l'horitzó digital no detecta arbres, edificis, grues, públic ni vehicles;
- orientar la càmera en vertical canvia aquests marges i pot empitjorar la intrusió inferior;
- 200 mm augmentaria encara més el camp vertical i la sensibilitat a l'horitzó.

Una opció a assajar al perfil C és col·locar el Sol una mica per sota del centre del sensor, deixant més camp de cel per sobre i més separació entre la vora inferior i l'horitzó. Ha de quedar premarcat; no es decideix durant la totalitat.

## 4. Gate del punt d'observació

Cada pla necessita una fitxa amb:

- coordenada WGS84 exacta;
- altura;
- fotografia panoràmica sense zoom;
- perfil angular de l'horitzó;
- passadís d'azimut aproximat 270°–287°;
- obstacles temporals i permanents;
- terreny ferm per a cada muntura;
- exposició al vent;
- accés i sortida;
- aforament/circulació de públic;
- cobertura de telefonia només com a dada, no com a dependència;
- dos punts alternatius pròxims.

### Acceptació geomètrica

Per al punt final:

1. el disc és visible durant tota la finestra C2–C3;
2. la corona útil i la vora del sensor no intersecten l'horitzó;
3. hi ha marge per l'error de brúixola, nivell i refracció;
4. es repeteix la inspecció físicament el dia anterior a la mateixa franja horària;
5. la posició exacta queda guardada offline a tots els dispositius.

## 5. Conjunt mínim d'imatges

Abans de definir velocitats cal definir què significaria «tornar amb èxit».

### P0 — no sacrificable

1. C2 cobert amb exposicions curtes per almenys una cadena principal.
2. C3 cobert amb exposicions curtes per almenys una cadena principal.
3. Un mínim de **dos cicles HDR complets i vàlids per cada tren principal**, si la cadència mesurada ho permet.
4. Una exposició d'ancoratge comuna repetida en tots els cicles.
5. Corona interior/prominències sense clipping en la càmera stock.
6. Almenys una còpia RAW persistent encara que mori l'ordinador.
7. Cap moment en què totes dues càmeres principals quedin atrapades simultàniament en exposicions llargues prop de C2 o C3.

### P1 — alta prioritat

- més repeticions de les exposicions llargues;
- Earthshine;
- estrelles i corona exterior;
- ràfega de cromosfera/prominències a tots dos contactes;
- seqüència parcial abans i després.

### P2 — només si no augmenta el risc

- Canon 6D;
- 200 mm ambiental;
- timelapse;
- vídeo;
- composicions amb paisatge;
- tercera seqüència manual.

La Canon només entra si funciona sola, grava a targeta i no demana cap acció humana que pugui perjudicar les dues Sony.

## 6. Arquitectura temporal única

La totalitat s'ha de programar en temps relatiu:

```text
finestra protegida C2
→ nucli HDR obligatori
→ cicles addicionals si hi ha pressupost
→ abort de qualsevol exposició llarga
→ finestra protegida C3
```

### Regles

- el nucli obligatori cap dins de 88 s amb marges;
- les finestres C2/C3 es dimensionen després de mesurar latència i dispersió de tret;
- una exposició llarga no comença si `temps restant < pitjor_cas + marge`;
- els dos trens desfasen les exposicions llargues;
- un frame d'ancoratge curt/mitjà reapareix entre cicles;
- qualsevol cicle extra és prescindible;
- si el temps o la càmera esdevenen incoherents, el sistema degrada cap al conjunt P0;
- el final de totalitat no depèn de C4 ni de la posta.

### Perfil del lloc

El controlador final haurà de llegir, com a dades:

- latitud, longitud i altura;
- C2/C3;
- convenció i versió del perfil lunar;
- escala d'exposicions validada;
- límit d'exposició llarga;
- nombre màxim de cicles;
- azimut/altura només per verificació;
- identificador del pla A/B/C.

Cap d'aquests valors ha de quedar escampat pel codi.

## 7. Seguiment, enquadrament i orientació

Durant 88–91 s, respecte d'una muntura fixa el Sol avançaria aproximadament 0,36°:

- uns 800 píxels a A7RIIIA + AP;
- uns 320 píxels a A7III + 300 mm.

El disc continuaria dins del camp, però les exposicions llargues quedarien arrossegades. Cal tancar:

- muntura de cada tren;
- taxa solar o sidèria;
- polar alignment diürn;
- deriva per refracció a baixa altura;
- posició de recentrat final;
- orientació del sensor;
- risc de col·lisió/cable a l'oest;
- comportament si s'atura el seguiment.

### Regla de fallback

Si falla el seguiment durant totalitat:

- no reinicialitzar la muntura;
- no sacrificar la seqüència sencera intentant diagnosticar;
- conservar exposicions curtes;
- continuar disparant mentre el Sol sigui dins del camp;
- deixar el 300 mm com la cadena amb més tolerància d'enquadrament.

### Orientació tardana però precompromesa

L'orientació final pot esperar fins que:

- existeixi un model coronal recent;
- es conegui l'horitzó real;
- s'hagi decidit si es privilegien streamers laterals o camp per sobre del Sol.

Després es marca mecànicament el rotador i no es torna a improvisar.

## 8. Decisions òptiques encara reversibles

### Hipòtesi base

- A7RIIIA stock + AP130GTX/QUADTCC.
- A7III modificada + Sony 300/2,8 GM.
- 70–200/2,8 a 200 mm com a recanvi.
- Canon 6D només com a tercera cadena autònoma.

### Assajos que decideixen

1. A7RIIIA/A7III als dos trens a 12°, 9° i 4°–5°.
2. 300 mm a f/2,8 versus f/3,2–f/4.
3. OSS/IBIS desactivat versus qualsevol mode que l'assaig justifiqui.
4. mecànic versus EFCS; silenciós només si no hi ha bandes ni deformació.
5. RAW sense comprimir per HDR versus comprimit per contactes.
6. ghosts i flare amb el Sol baix.
7. focus per canal i resposta de la càmera modificada.

La ubicació del cos a l'AP continua sent un paràmetre. No bloqueja el controlador.

## 9. Focus i estabilitat

Protocol candidat:

1. focus manual amb filtre solar i detall fotosfèric;
2. comprovació després d'aclimatar AP i 300 mm;
3. comprovació intermèdia durant la parcialitat;
4. comprovació final prou abans de C2;
5. bloqueig mecànic o marca de retorn;
6. AF, auto-ISO, canvi automàtic de WB, Long Exposure NR i neteja automàtica desactivats;
7. no tocar focus durant totalitat.

El balanç de blancs és metadada/revelat. No converteix la resposta RAW de l'A7III modificada en la d'una càmera stock.

Cal mesurar:

- deriva tèrmica;
- FWHM per canal;
- percentatge de frames nítids;
- vibració causada en retirar/recol·locar el filtre;
- temps de retorn després de tocar el tren.

## 10. Filtres i seguretat

Regla oficial de partida:

- filtre solar adequat a la **part frontal** de cada òptica durant totes les fases parcials;
- retirada només durant la totalitat;
- recol·locació abans que reaparegui la fotosfera;
- cap finder sense filtrar o destapat;
- mai mirar per una òptica no filtrada.

Fonts: [American Astronomical Society — filtres per a òptiques](https://eclipse.aas.org/eye-safety/optics-filters) i [guia fotogràfica AAS](https://eclipse.aas.org/node/34).

Per tancar el disseny cal saber:

- filtre exacte de l'AP;
- filtre exacte del 300 mm;
- sistema de retenció;
- si es pot retirar amb una mà sense transmetre vibració;
- com queda assegurat contra vent;
- temps de retirada i recol·locació;
- qui opera cada filtre;
- filtre de recanvi.

Si es vol retirar abans que desaparegui l'última perla per obtenir un diamant exterior sense filtre, això no pot quedar implícit en el guió: és una decisió específica de risc ocular/equip que s'ha de validar separadament. El mode conservador manté el filtre fins que la fotosfera ha desaparegut completament.

## 11. Operadors i càrrega humana

Falta congelar una dada estructural: **una persona o dues**.

### Si hi ha un únic operador

- les dues càmeres han d'arribar a C2 preconfigurades;
- només dues accions manuals crítiques: filtres;
- cap Canon que exigeixi supervisió;
- controls físics dins del mateix abast;
- avisos d'àudio;
- cap lectura de pantalla ni diagnòstic durant totalitat;
- fallback Multi Terminal immediat.

### Si hi ha dos operadors

- una cadena principal per persona;
- vocabulari i compte enrere únics;
- cadascú és responsable del seu filtre;
- només un operador és autoritat temporal;
- cap canvi creuat no assajat.

Un ajudant no entrenat pot augmentar el risc. Ha de participar en els assajos complets.

## 12. Topologia i punts únics de fallada

Cal dibuixar abans d'implementar:

| Element | Cadena AP | Cadena 300 | Canon opcional |
|---|---|---|---|
| cos | per decidir per A/B | complementari | 6D |
| muntura | pendent | pendent | trípode/muntura pròpia |
| alimentació | pròpia | pròpia | bateria |
| targeta | pròpia | pròpia | pròpia |
| USB càmera | alimentació sense dades | alimentació sense dades | cap, idealment |
| trigger principal/retorn | Multi Terminal o BLE / Multi | Multi Terminal o BLE / Multi | intervalòmetre |
| filtre | pendent model | pendent model | pendent |
| operador | pendent | pendent | cap durant totalitat |

Mentre BLE sigui experimental, la taula no permet triar `BLE / BLE`: una de
les dues cadenes Sony ha d'anar obligatòriament per Multi Terminal, amb
watchdog i alimentació propis. L'altra pot assajar BLE. L'assignació
AP/300 es farà després del Gate sense convertir la ràdio en un punt únic de
fallada.

Bloquejants que encara ha d'aportar l'inventari:

- muntura o capçal de cada tren;
- si comparteixen barra, trípode o alimentació;
- ordinador, sistema operatiu i ports reals;
- models de filtre;
- nombre d'operadors;
- disponibilitat i òptica de la Canon.

## 13. Configuració de càmera que s'ha de congelar

Per cada cos:

- firmware;
- mode manual;
- ISO;
- RAW sense comprimir;
- drive/bracket;
- mecànic/EFCS/silenciós;
- obertura;
- Long Exposure NR off;
- High ISO NR irrellevant per RAW però fixat;
- auto-review off;
- power-save off o temporització segura;
- IBIS/OSS;
- Slot 1 i SD UHS-II qualificada;
- Recording Mode Standard, Slot 2 buit;
- PC Remote tancat durant C2–C3;
- USB-C power-only verificat o power bank;
- comportament en reinici;
- rellotge EXIF;
- nom físic i port.

Fer fotografies de totes les pantalles i exportar/registrar les configuracions.

## 14. Captures de calibratge que no poden esperar

El postprocessament pot esperar; **l'adquisició dels calibratges no**.

Per cada combinació final de cos i òptica cal preservar:

- flats del tren de totalitat, sense filtre solar i amb focus, obertura i orientació intactes;
- flats separats de la configuració de parcialitat si el filtre introdueix estructura;
- darks o biblioteca de darks per ISO, temps llarg i temperatura útils;
- bias/offset o preses més curtes que permeti el cos, si després es decideix emprar-les;
- referència de pols abans i després;
- frames de prova de saturació;
- identificació exacta de quins calibratges corresponen a cada sèrie.

### Protocol de camp

- desactivar la neteja automàtica de sensor;
- no rotar càmera ni moure focus fins haver obtingut els flats posteriors;
- no apuntar mai el tren sense filtre al Sol fora de totalitat;
- usar una font uniforme segura després de la seqüència o de la posta;
- tapar completament l'òptica per als darks;
- registrar temperatura de cos o un proxy temporal;
- duplicar els calibratges a la targeta/ordinador quan ja no hi hagi cap fase crítica.

Si obtenir-los immediatament posa en risc equip o parcialitat post-C3, es prioritza la seguretat i es fa una seqüència reproduïble tan aviat com sigui possible. El que no és acceptable és desmuntar el tren sense haver pres una decisió conscient.

## 15. Gates de tancament

### Gate S — lloc

- coordenada exacta;
- horitzó mesurat;
- camp complet lliure;
- punt alternatiu;
- ruta i accés verificats.

### Gate O — òptica

- cos/òptica decidits;
- focus i obertura;
- orientació;
- ghosts;
- vibració;
- seguiment.

### Gate C — captura

- trigger nadiu produeix el recompte esperat;
- bits RAW verificats;
- patró HDR dins del pressupost curt;
- zero pèrdues en assaig repetit;
- targeta i còpia supervivents.

### Gate T — temps/contactes

- C2/C3 exactes;
- perfil lunar documentat;
- rellotge únic;
- finestres de protecció;
- fallback temporal.

### Gate H — humà i seguretat

- filtres assajats;
- funcions assignades;
- àudio;
- tres assajos complets sense improvisació;
- criteri d'abort.

### Gate F — congelació

- versions i hashes;
- configuracions;
- cables etiquetats;
- bateries/targetes;
- còpies offline;
- cap actualització posterior sense repetir validació.

## 16. Assaig general

El guió final s'ha de representar com a mínim:

1. amb 88 s de totalitat;
2. amb tots dos cossos i muntures;
3. amb els filtres reals;
4. amb targetes parcialment ocupades;
5. a una altura solar semblant;
6. amb una fallada deliberada de PC/USB;
7. amb el nombre real d'operadors;
8. tres vegades en dies diferents;
9. una última vegada al punt final, sense canviar res després.

L'èxit no és que «el programa acabi». És:

- fitxers i exposicions correctes;
- C2/C3 coberts;
- cap càmera bloquejada;
- cap acció de seguretat omesa;
- log i EXIF coherents;
- fallback entès sense llegir instruccions llargues.

## 17. Condició final de tancament prospectiu

Es pot declarar la prospectiva tancada quan:

- els tres perfils A/B/C existeixen;
- el nucli funciona conceptualment en 88 s;
- P0/P1/P2 estan acceptats;
- les variables reversibles tenen un assaig i un criteri;
- muntures, filtres i operadors estan identificats;
- ja no queda cap decisió que depengui d'opinió o improvisació.

A partir d'aquí comença una fase diferent:

> **validar → decidir → congelar → assajar**, i només després implementar el controlador definitiu.
