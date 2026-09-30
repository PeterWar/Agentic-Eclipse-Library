> **AVÍS HISTÒRIC (27-07-2026):** document superat operativament per
> `controller v0.2.3 candidate`, F3/F3B/F3M i el disseny HDR nadiu. Es
> conserva com a evidència i no és autoritat operativa.

# gphoto2, bràqueting nadiu i búfer

## Resposta curta

**gphoto2 continua sent útil per a laboratori i preflight, però deixa de ser
la ruta principal entre C2 i C3.** Els dos cossos no ofereixen card-only
dins PC Remote i el backend Sony transfereix el payload complet fins i tot
per resoldre `wait-event`.

La via principal, revisada el 26-07-2026, és:

> gphoto2 qualifica abans; després se'n tanca la sessió. La càmera captura
> el bràqueting amb la seva màquina d'estats, escriu RAW sense comprimir a
> la SD UHS-II i rep el trigger per un canal físic/BLE independent.

## Què fan realment les ordres

Segons el [manual oficial de gphoto2](https://www.gphoto.org/doc/manual/ref-gphoto2-cli.html):

- `--capture-image`: captura i conserva a la càmera;
- `--capture-image-and-download`: captura i transfereix a l'ordinador;
- `--trigger-capture`: envia el trigger i torna el control;
- `--wait-event`: la CLI no desa el fitxer, però en el backend Sony
  libgphoto2 2.5.34 fa igualment `GetObject` del payload complet abans de
  publicar l'esdeveniment;
- `--wait-event-and-download`: espera i baixa els fitxers nous.

Per això el manual de la CLI no basta per inferir el trànsit Sony. Vegeu
[la branca exacta de `camera_wait_for_event`](https://github.com/gphoto/libgphoto2/blob/v2.5.34/camlibs/ptp2/library.c#L7084-L7191).

La [taula oficial de libgphoto2](https://gphoto.sourceforge.io/proj/libgphoto2/support.php) llista:

- Sony Alpha-A7 III (PC Control);
- Sony Alpha-A7R III (PC Control);

amb capacitats de captura, trigger, live view i configuració.

## Compatibilitat actual i alternatives Sony

La llista de libgphoto2, actualitzada el 30 de maig de 2026, continua declarant els dos models amb captura, trigger, live view i configuració.

La **Sony Camera Remote SDK 2.02.00**, publicada el 10 de juny de 2026,
no admet ni `ILCE-7M3` ni `ILCE-7RM3A`. La interfície de nivell baix
**Camera Remote Command/PTP** sí que enumera exactament els dos cossos,
però Sony restringeix la descàrrega de la documentació i els exemples a
clients corporatius i exigeix el firmware més recent.

Per tant:

- no hi ha una migració oficial suportada de les nostres càmeres al SDK;
- implementar Camera Remote Command seria un projecte PTP nou, no canviar
  una biblioteca per una altra;
- cap de les dues vies ofereix una promesa de latència *hard real-time* o
  control directe del búfer;
- no s'ha d'actualitzar firmware enmig de la qualificació actual sense
  congelar abans el baseline i repetir tots els gates.

Fonts:

- [Sony Camera Remote SDK](https://support.d-imaging.sony.co.jp/app/sdk/en/index.html)
- [Sony Camera Remote Command](https://support.d-imaging.sony.co.jp/app/cameraremotecommand/en/index.html)

## El búfer no és una API separada

Normalment no es «demana al búfer» que treballi. El búfer entra en joc quan:

1. la càmera rep un dispar continu;
2. genera diverses captures internament;
3. les conserva temporalment en RAM;
4. les va escrivint a la targeta o, segons el mode remot, les transfereix;
5. el controlador evita imposar una barrera USB entre cada fotograma.

Per tant, el benefici no prové de `--keep` per si sol. Prové d'evitar el patró:

`canvia paràmetre → obre procés → dispara → espera → descarrega → tanca procés`

i substituir-lo per:

`preconfigura bràqueting → mantén disparador → la càmera fa 5 captures → espera només el necessari → següent base`

## Evidència específica amb A7III i A7RIIIA

Alex Fliker va publicar l'11 de febrer de 2026 un [benchmark de control remot de Sony per a eclipsis](https://fliker09.wordpress.com/2026/02/11/remote-control-of-sony-cameras-for-solar-eclipses/) amb exactament:

- Sony A7III;
- Sony A7RIIIA;
- gphoto2 2.5.28;
- libgphoto2 2.5.31;
- deu repeticions per mesura;
- validació de les exposicions amb EXIF.

Troballes rellevants:

- canviar la velocitat per PTP és relativament lent;
- de vegades el valor queda un o dos passos desplaçat, de manera que cal verificar i repetir;
- l'ordre/acció `bulb` es pot emprar com una pressió mantinguda del disparador mentre la càmera continua en el mode de bràqueting;
- el bràqueting continu nadiu evita reconfigurar cada exposició;
- gphoto2 i una implementació directa de Sony Camera Control PTP van donar velocitats semblants;
- guardar RAW+JPEG o transferir més dades redueix la cadència;
- targeta, format i temps de drenatge són part de la prova.

### Patró de 15 exposicions

Configuració de càmera:

- `Bracket: Cont.`;
- 5 imatges;
- separació de 3 EV.

Tres exposicions base:

- 1/80 s;
- 1/40 s;
- 1/20 s.

Cada pressió produeix cinc frames a:

- base −6 EV;
- base −3 EV;
- base;
- base +3 EV;
- base +6 EV.

Intercalant les tres famílies s'obté aproximadament:

`1/5120, 1/2560, 1/1280, 1/640, 1/320, 1/160, 1/80, 1/40, 1/20, 1/10, 1/5, 0,4, 0,8, 1,6 i 3,2 s`

És a dir, 15 exposicions separades aproximadament 1 EV amb:

- tres canvis PTP de velocitat;
- tres pressions mantingudes;
- ús del motor de bràqueting de la càmera;
- solapament dinàmic continu.

En el seu muntatge, la A7RIIIA va necessitar una espera final més llarga que la A7III, però la diferència total per al patró complet va ser només d'aproximadament 1,24 s.

### Verificació al codi de libgphoto2

El codi font actual de [`_put_Sony_Bulb`](https://raw.githubusercontent.com/gphoto/libgphoto2/master/camlibs/ptp2/config.c) mostra:

- en iniciar: `ShutterHalfRelease` i `RequestOneShooting`;
- en acabar: ordres de release.

El nom `Bulb Mode` és enganyós en aquest context:

- simula mantenir el disparador;
- no canvia necessàriament la càmera a una exposició BULB;
- pot activar el bràqueting continu intern.

És una evidència més forta que la inferència basada només en el benchmark.

## Evidència pròpia del 25 de juliol de 2026

El comportament essencial ja no és una hipòtesi externa:

- A7III i A7RIIIA han produït cinc ARW amb una sola pressió virtual;
- tots els ARW inspeccionats són RAW sense comprimir de 14 bits, amb
  variació real als dos bits baixos;
- l'A7III ha acumulat 10 i després 15 ARW sense cap drenatge intermedi i
  els ha lliurat tots al final;
- dos processos persistents, un per càmera, han disparat al mateix target
  UTC amb una separació inferida de 2,361 ms;
- `d215` ha mostrat 3 mentre el bracket complet contenia 5, 10 o 15
  fitxers: és telemetria instantània, no el comptador final;
- una restauració `set-config` a l'A7RIIIA ha trigat 25,759 s tot i no
  haver-hi cap captura pendent;
- un drenatge A7III amb `wait-event-and-download 1s` ha necessitat dues
  finestres síncrones d'uns 1,2 s per recuperar 4 + 1 RAW.

La lectura conjunta és clara: el bràqueting i el búfer interns són fiables
en el rang provat; el canal PTP no té una latència prou limitada per
governar canvis de configuració o drenatges dins C2–C3.

Vegeu el
[Gate 7](../tests/2026-07-25_GATE7_A7III_BUFFER_DUAL_HDR.md).

## Per què aquesta idea encaixa amb Druckmüller

El patró resol diversos problemes alhora:

- pas màxim d'1 EV al conjunt final;
- exposicions curtes per prominències;
- exposicions llargues per corona exterior;
- poques transaccions lentes de configuració;
- escala prou curta per repetir-la;
- RAW solapats per a LDIC o una fusió equivalent;
- captura interna més determinista que una sèrie de 15 ordres independents.

No cal copiar exactament 15 exposicions. Cal conservar el principi i ajustar:

- límit curt necessari per C2/C3;
- límit llarg compatible amb moviment, seeing, vent i saturació;
- temps total de cada escala;
- nombre de repeticions;
- mode RAW i profunditat efectiva;
- temps real de buidatge del búfer.

## Què queda demostrat i què no

Ja està demostrat en els nostres cossos:

- una retenció `bulb=1`/espera/`bulb=0` produeix cinc ARW;
- RAW sense comprimir conserva 14 bits efectius;
- l'ordre dels cinc fotogrames i els seus bias;
- identitat i aïllament de les dues càmeres;
- acumulació mínima de 15 RAW a l'A7III;
- captura dual amb un target absolut compartit;
- cobertura física A7III de 12 EV amb 5 × 3 EV base 1/125 s.

Encara s'ha de verificar:

- card-only real i persistència a les SD definitives;
- Multi Terminal com a alliberament i trigger independents;
- `Recall Custom hold` amb C1/AF-ON + shutter;
- la seqüència de tres bases i quinze exposicions als dos cossos;
- recuperació després de cable solt, supervisor mort o pèrdua BLE;
- 90 s sense alentiment amb targetes, alimentació i temperatura de camp;
- 100–500 cicles de la configuració finalista.

## Profunditat RAW Sony

Sony documenta que A7III i A7RIII:

- poden conservar 14 bits en RAW sense comprimir en diversos modes continus;
- poden reduir a 12 bits en determinades combinacions, especialment RAW comprimit continu, BULB o Long Exposure NR.

Fonts:

- [Notes Sony sobre profunditat RAW](https://www.sony.com/electronics/support/e-mount-body-ilce-7-series/ilce-7c/articles/00229990)
- [Ajuda A7III sobre RAW](https://helpguide.sony.net/ilc/1720/v1/en/contents/TP0001667676.html)

El codi confirma que `bulb` és una acció de **shutter press**. La inferència forta és que RAW sense comprimir en bràqueting continu conserva 14 bits, tal com documenta Sony. Només una lectura dels nostres ARW ho tanca.

## Capacitat nominal del búfer

Fonts oficials Sony indiquen aproximadament:

- **A7III, Hi+**: fins a 89 RAW comprimits o 40 RAW sense comprimir;
- **A7RIIIA**: fins a 76 RAW comprimits o 28 RAW sense comprimir, segons condicions i especificació.

Fonts:

- [Ajuda Sony A7III: nombre de captures contínues](https://helpguide.sony.net/ilc/1720/v1/en/contents/TP0001653139.html)
- [Especificacions Sony A7RIIIA](https://www.sony.com/electronics/support/e-mount-body-ilce-7-series/ilce-7rm3a/specifications)

Aquestes xifres no són una cadència garantida d'eclipsi. Depenen de targeta, compressió, configuracions, bateria, temperatura, durada de les exposicions i interfície remota. Sí que indiquen que una escala de 15 frames cap nominalment en tots dos búfers.

## PC Remote i destinació

Sony permet, segons cos i configuració:

- `PC Only`;
- `PC + Camera`.

Sony indica explícitament que `Still Img. Save Dest.` **no es pot canviar
durant PC Remote**: s'ha de fixar al menú abans de connectar. Això explica
per què escriure `card+sdram` per PTP durant els primers assajos no podia
convertir una sessió iniciada com `PC Only`.

Amb `PC+Camera`, una targeta absent o no gravable impedeix disparar. Un
preflight de fallback ha de llegir `card+sdram`, comprovar cua zero i
avortar abans d'armar si no es compleix.

També documenta l'opció de capturar RAW+JPEG a la targeta i enviar només el
JPEG a l'ordinador. Pot reduir la càrrega USB i fer del RAW de la SD la
còpia canònica, però és una hipòtesi de rendiment que necessita un A/B
físic: crear també el JPEG i escriure la SD pot reduir el búfer disponible.

Fonts:

- [PC Remote Save Destination, A7III](https://helpguide.sony.net/ilc/1720/v1/en/contents/TP0001661953.html)
- [PC Remote Save Destination, A7RIIIA](https://helpguide.sony.net/ilc/2050/v1/en/contents/TP1000189509.html)
- [RAW+J PC Save Image, A7III](https://helpguide.sony.net/ilc/1720/v1/en/contents/TP0001661944.html)
- [RAW+J PC Save Image, A7RIIIA](https://helpguide.sony.net/ilc/2050/v1/en/contents/TP1000189467.html)

Aquestes Sony ofereixen en PC Remote `PC Only` o `PC+Camera`, no
`Camera Only`. La ruta principal card-only exigeix sortir de PC Remote.
`PC+Camera` + JPEG Only queda com a fallback a qualificar.

El búfer no és emmagatzematge persistent. Una imatge que només espera transferència al PC no és encara una còpia segura.

## gphoto2 versus alternatives

### gphoto2/libgphoto2

Avantatges:

- suport declarat per als dos cossos;
- automatització scriptable;
- configuració i captura en una mateixa sessió;
- codi obert;
- experiència directa del 2024;
- benchmark extern exactament amb els nostres models.

Riscos:

- propietats PTP Sony lentes o inconsistents;
- noms de configuració dependents de versió;
- gestió USB;
- poc control sobre firmware intern;
- una mala arquitectura de script pot anul·lar tots els avantatges.

### Sony Camera Remote SDK

No admet aquests dos models en la versió actual consultada. Queda descartat com a ruta principal mentre Sony no canviï compatibilitat.

### Sony Camera Control PTP propi

Pot donar control precís i una aplicació específica, però:

- augmenta molt l'esforç de desenvolupament i prova;
- no elimina la latència pròpia del cos;
- exigeix mantenir codi de protocol;
- no té sentit si el motor nadiu de bràqueting ja resol la part crítica.

### Disparador físic / Multi Terminal

És una alternativa molt valuosa:

- la càmera rep una ordre nadiua simple;
- pot quedar separada del canal USB;
- permet una ruta de contingència;
- pot controlar un bràqueting continu sense transferència.

No configura velocitats per si sol. La millor arquitectura pot acabar sent híbrida: configuració abans de totalitat i dispar físic durant els segons més delicats.

## Veredicte tècnic revisat el 26 de juliol de 2026

La ruta principal és **mode normal + RAW sense comprimir a SD UHS-II +
trigger independent**. gphoto2/libgphoto2 queda com a banc de laboratori,
preflight i fallback. Sony Camera Remote SDK continua descartat per
incompatibilitat oficial; Camera Remote Command no resol el problema perquè
continua sent PTP.

Hi ha evidència clara per abandonar:

- una invocació de procés per foto;
- la descàrrega síncrona;
- la configuració d'una velocitat per cada frame;
- esperar indefinidament un únic esdeveniment;
- confiar sense llegir el valor aplicat.

La següent decisió és escollir el backend de trigger després de:

1. bràqueting continu amb pressió física;
2. `Recall Custom hold` manual amb RMT-P1BT;
3. automatització BLE en un cos i després dos;
4. 90 s card-only amb les SD definitives;
5. mort del Mac, pèrdua del cable i release per watchdog.

Per a la configuració finalista, l'objectiu és 100–500 cicles, incloent
dues càmeres simultànies i fallades provocades.

El controlador PTP de laboratori ja ha validat la semàntica i els bits. No
s'ha de congelar el release fins a superar el
[Gate 9 card-only](../tests/2026-07-26_GATE9_CARD_ONLY_TRIGGER_PROTOCOL.md),
l'alliberament independent i la política de degradació.
