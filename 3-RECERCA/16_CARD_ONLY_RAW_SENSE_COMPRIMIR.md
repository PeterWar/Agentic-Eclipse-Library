> **AVÍS HISTÒRIC (27-07-2026):** document superat operativament per
> `controller v0.2.3 candidate`, F3/F3B/F3M i el disseny HDR nadiu. Es
> conserva com a evidència i no és autoritat operativa.

# Captura crítica card-only amb RAW sense comprimir

Data: 26 de juliol de 2026  
Estat: **nova ruta principal; pendent de Gate 9 físic**

## Decisió

Entre C2 i C3, la ruta principal ha de ser:

1. càmera fora de `PC Remote`;
2. `File Format = RAW`;
3. `RAW File Type = Uncompressed`;
4. una sola SD UHS-II qualificada al `Slot 1`;
5. `Recording Mode = Standard`;
6. cap transferència, consulta o drenatge PTP;
7. disparador independent per Multi Terminal o Bluetooth;
8. verificació dels ARW només després de C3.

El Mac pot calcular els temps, armar el sistema i registrar les ordres, però
no ha d'estar en el camí de dades dels RAW. La versió de producció preferida
és encara més independent: un petit controlador amb el programa pre-carregat
executa els polsos localment i el Mac queda com a supervisor.

Aquesta decisió conserva el requisit de Pere —RAW sense comprimir— i elimina
alhora el trànsit USB que podia bloquejar el canal de control.

### Contracte operatiu: llaç obert deliberat

Card-only implica acceptar una propietat important: durant C2–C3 no sabrem
des del controlador si cada ARW ha quedat escrit. No intentarem recuperar
aquesta confirmació obrint PTP, perquè la verificació mateixa reintroduiria
el camí de dades que volem eliminar.

El sistema treballarà deliberadament en llaç obert:

- el controlador confirma **ordres i releases**, no fitxers;
- el watchdog confirma que cap contacte o botó queda premut;
- la llum d'accés SD es pot filmar en els assajos, però no governa la
  seqüència;
- no hi ha reintents ni *catch-up* basats en una captura presumptament
  perduda;
- la salut real es determina després de C3, amb recompte, EXIF i hashes.

La conseqüència pràctica és que la robustesa s'ha d'obtenir abans de
l'eclipsi —assaig llarg, marge de cadència i rutes independents—, no amb
diagnòstic improvisat durant els noranta segons.

## Troballa decisiva: `wait-event` no és telemetria lleugera en Sony

La CLI de gphoto2 diferencia entre `--wait-event` i
`--wait-event-and-download`, però el backend Sony de libgphoto2 2.5.34 ha de
recuperar l'objecte de RAM abans de poder publicar l'esdeveniment:

1. llegeix `PTP_DPC_SONY_ObjectInMemory` (`d215`);
2. fa `GetObjectInfo`;
3. fa `GetObject` del fitxer complet;
4. desa els bytes al filesystem intern de libgphoto2;
5. només llavors retorna `GP_EVENT_FILE_ADDED`.

Per tant, `--wait-event` pot no escriure l'ARW en un directori visible del
Mac, però **sí que transfereix el RAW complet per USB fins a memòria host**.
No és un ACK barat i queda prohibit dins la finestra protegida.

Font exacta:

- [libgphoto2 2.5.34, `camera_wait_for_event`, línies 7084–7191](https://github.com/gphoto/libgphoto2/blob/v2.5.34/camlibs/ptp2/library.c#L7084-L7191)

## Per què `PC+Camera` sense drenar tampoc és card-only

Sony només documenta dues destinacions durant PC Remote:

- `PC Only`;
- `PC+Camera`.

No hi ha una opció oficial `Camera Only`. Els nostres dos cossos, interrogats
amb gphoto, només han anunciat `sdram` i `card+sdram`. La taula genèrica de
libgphoto2 coneix també el valor teòric `card = 0x0010`, però això no crea una
capacitat que el firmware no exposa. A l'A7RIIIA, forçar `card` o `0x0010` ja
va ser ignorat pel cos.

Fonts:

- [Sony A7III: Still Img. Save Dest.](https://helpguide.sony.net/ilc/1720/v1/en/contents/TP0001661953.html)
- [Sony A7RIIIA: Still Img. Save Dest.](https://helpguide.sony.net/ilc/2050/v1/en/contents/TP1000189509.html)
- [libgphoto2 2.5.34: taula `sony_capturetarget`](https://github.com/gphoto/libgphoto2/blob/v2.5.34/camlibs/ptp2/config.c#L10755-L10760)

En `PC+Camera`, no cridar `wait-event` evita la transferència immediata,
però deixa els objectes pendents a la cua PTP/RAM. Això només ajorna el
problema. `d215` no en dona el deute total: a l'A7III va continuar indicant
3 amb 5, 10 i 15 RAW compromesos.

El mínim demostrat és 15 RAW a l'A7III i 5 a l'A7RIIIA. No autoritza una
seqüència de totalitat. A una cadència hipotètica de cinc RAW cada quatre
segons durant 90 segons serien 115 fitxers, aproximadament:

| Cos | Mida mitjana observada | Total aproximat | Flux RAW mitjà |
|---|---:|---:|---:|
| A7III | 49 MB | 5,6 GB | 62 MB/s |
| A7RIIIA | 85 MB | 9,8 GB | 109 MB/s |

La cua PTP no està qualificada per això. El búfer publicat per Sony tampoc
és una garantia de cua PC Remote: descriu la ràfega nativa cap a targeta.

## Ruta de trigger A — Multi Terminal

És el baseline de màxima robustesa:

- càmera en mode normal;
- pressió sostinguda del disparador pel Multi/Micro USB Terminal;
- bràqueting continu nadiu;
- RAW només a SD;
- USB-C lliure per a alimentació;
- cap sessió gphoto oberta.

Sony confirma que un accessori de disparador al Multi Terminal es pot usar
mentre l'USB-C alimenta la càmera. Si l'USB-C porta només alimentació i no
una sessió PC Remote, no hi ha cua PTP.

Fonts:

- [A7III: ports, Slot 1 UHS-II i ús simultani del Multi Terminal](https://helpguide.sony.net/ilc/1720/v1/en/contents/TP0001667670.html)
- [A7RIIIA: manual oficial, pàgina 27](https://helpguide.sony.net/ilc/2050/v1/en/print.pdf)

Limitació: un disparador elèctric simple pot iniciar i aturar el bracket,
però no canvia la velocitat base. La ruta mínima segura és repetir un únic
`5 × 3 EV` preconfigurat. La combinació ja demostrada a l'A7III,
base `1/125 s`, produeix físicament:

`1/8000, 1/1000, 1/125, 1/15, 1/2 s`

amb 12 EV de cobertura i sense clipping del fotograma curt.

## Ruta de trigger B — tres bases sense PTP

Hi ha una via prometedora per conservar l'escala de 15 exposicions sense
transferir fitxers ni canviar paràmetres per USB.

Els dos cossos ofereixen `Reg Cust Shoot Set`:

- es poden registrar exposició i drive mode;
- `Recall Custom hold 1…3` aplica els ajustos mentre es manté premuda una
  tecla personalitzada;
- el tret es fa mentre es continua mantenint la tecla.

El comandament Sony RMT-P1BT pot accionar el disparador i les funcions
assignades a `C1` i `AF-ON`. Això permet plantejar, com a primeres receptes
de laboratori:

| Tren candidat | Tres bases | Escala resultant aproximada |
|---|---|---|
| A7RIIIA + AP130GTX/QUADCC | 1/20, 1/40 i 1/80 s | 1/5000…3,2 s |
| A7III + 300 mm f/2,8 | 1/30, 1/60 i 1/125 s | 1/8000…2 s |

Per al segon cas, la unió teòrica ordenada és:

`1/8000, 1/4000, 1/2000, 1/1000, 1/500, 1/250, 1/125, 1/60,`
`1/30, 1/15, 1/8, 1/4, 1/2, 1, 2 s`

Són 15 passos d'1 EV sense cap `set-config`, cap PC Remote i cap RAW cap al
Mac. Les bases no queden congelades: s'han de calibrar per tren òptic amb el
Sol a una altura semblant, i després verificar que ni el límit curt ni el
llarg queden retallats.

Fonts oficials:

- [A7III: Reg Cust Shoot Set](https://helpguide.sony.net/ilc/1720/v1/en/contents/TP0001666494.html)
- [A7RIII: Reg Cust Shoot Set](https://helpguide.sony.net/ilc/1710/v1/en/contents/TP0001666494.html)
- [RMT-P1BT: C1 i AF-ON activen la funció assignada](https://helpguide.sony.net/ilc/1820/v1/en/contents/TP0002240390.html)
- [A7RIIIA: Bluetooth Rmt Ctrl](https://helpguide.sony.net/ilc/2050/v1/en/contents/TP1000196363.html)

La part oficial arriba fins aquí. Automatitzar aquests botons des d'un
ordinador o microcontrolador usa un protocol Bluetooth no documentat per
Sony. El projecte obert
[α-Remote](https://github.com/staacks/alpharemote) confirma funcionament
amb A7III i A7RIII i exposa press/release de disparador, C1 i AF-ON, però
és evidència experimental, no una garantia de producció.

### Guardrail de llicència

`α-Remote` és GPL-3.0. Es pot estudiar com a prova d'interoperabilitat, però
no se'n copiarà codi al controlador. Si el Gate BLE passa, s'implementarà
una capa mínima pròpia a partir del comportament observat i de les fonts que
sigui lícit reutilitzar, mantenint clara la procedència.

### Asimetria obligatòria mentre BLE sigui experimental

Un únic RMT-P1BT s'emparella amb un cos. Governar les dues càmeres requeriria
dos comandaments físics o un host BLE no oficial capaç de mantenir dues
connexions. Això afegeix risc de firmware, ràdio i estat compartit.

Per tant, la qualificació i la primera versió de producció seran
deliberadament asimètriques:

- **un cos** conserva sempre el `5 × 3 EV` qualificat per Multi Terminal;
- **l'altre cos** pot provar les tres bases per C1/AF-ON;
- mai no es migren tots dos cossos al BLE experimental en la mateixa ronda;
- un error BLE no pot afectar el rellotge ni el release del cos cablejat.

Només una prova llarga de dos controladors físicament independents podria
autoritzar BLE als dos cossos. No és necessari per obtenir un sistema fort.

### Hipòtesi per als contactes: fotograma curt amb una pulsació breu

Cal provar, sense adoptar encara, una possible simplificació. Si l'ordre del
bracket es configura `− → 0 → +`, el primer fotograma del `5 × 3 EV` és el
més curt. Una pulsació molt breu podria donar només aquest fotograma de
`−6 EV`, mentre una pulsació sostinguda completaria els cinc.

Seria una manera elegant de compartir el mateix trigger per:

- ràfega curta de diamant/Baily a C2 i C3;
- bracket complet de corona durant la totalitat.

Però només és una hipòtesi de banc. S'ha de mesurar si la pulsació breu
produeix exactament un ARW, si alguna vegada en produeix zero o més d'un, i
si el cos queda en un estat residual. Si no és absolutament determinista,
els contactes tindran una recepta física separada.

## Pressupost de dades: ara el coll d'ampolla és la SD

Treure l'USB del camí no fa infinita la ràfega. Amb RAW sense comprimir,
l'A7RIIIA és el cos exigent:

- un cicle de 15 RAW és prop d'1,28 GB;
- la suma dels 15 temps d'exposició de l'escala proposada és prop de 6,4 s;
- a l'A7III, l'escala candidata suma prop de 4,2 s;
- totes dues xifres exclouen readout, interframes i escriptura;
- repetir massa aviat pot omplir el búfer encara que no hi hagi ordinador.

Per això no es congelarà encara una cadència. El Gate 9 ha de mesurar amb
les SD definitives:

1. durada real de cada bracket;
2. temps fins que s'apaga la llum d'accés;
3. deriva de la cadència quan el búfer deixa de ser buit;
4. màxim flux sostingut sense `busy`;
5. marge tèrmic i d'alimentació.

Als dos cossos, només el Slot 1 és UHS-II; el Slot 2 és UHS-I. Per prioritzar
cadència:

- una sola targeta UHS-II al Slot 1;
- `Prioritize Rec. Media = Slot 1`;
- `Recording Mode = Standard`;
- sense RAW+JPEG;
- sense duplicació simultània al Slot 2.

Fonts:

- [A7III: useu Slot 1 per a UHS-II](https://helpguide.sony.net/ilc/1720/v1/en/contents/TP0001653092.html)
- [A7RIIIA: manual oficial, targetes compatibles](https://helpguide.sony.net/ilc/2050/v1/en/print.pdf)

## Jerarquia de rutes

1. **Producció preferida:** card-only real + controlador físic/BLE autònom.
2. **Fallback robust:** card-only real + un únic `5 × 3 EV` repetit per
   Multi Terminal.
3. **Fallback gphoto:** `PC+Camera`, RAW+JPEG a SD i només JPEG al PC, si
   supera 90 s complets; continua tenint cua PTP i cost JPEG.
4. **Només laboratori/microburst:** `PC+Camera` RAW sense drenatge.
5. **Prohibit entre C2 i C3:** `wait-event`, `capture-image`,
   `wait-event-and-download`, `set-config` o reconnectar PTP.

## `5 × 3 EV` o escala de tres bases

La cadència no es decidirà pel nombre d'exposicions més impressionant, sinó
pel producte mínim que volem garantir. La ruta simple `5 × 3 EV` guanya si,
en una prova de Sol baix representativa:

- cada zona radial necessària té almenys dues exposicions no saturades per
  canal amb SNR per sobre del llindar fixat;
- hi ha solapament radiomètric suficient entre exposicions veïnes;
- el registre progressiu convergeix malgrat els salts de 3 EV;
- es poden repetir prou brackets dins 88 s amb marge per a C2 i C3.

Si falla qualsevol d'aquests punts, la cobertura d'1 EV de les tres bases
guanya, sempre que passi el pressupost temporal i d'escriptura. També es
provarà una estratègia híbrida: algun cicle complet de 15 RAW més repeticions
del nucli `5 × 3 EV`. No es congelarà cap recepta abans de mesurar els dos
cossos amb les SD definitives.

## Custòdia després de C3

En card-only, cada SD és durant uns minuts l'única còpia de la totalitat.
Després de C3:

1. esperar que s'apagui completament la llum d'accés;
2. no esborrar, formatar ni revisar massivament a càmera;
3. apagar el cos abans d'extreure la targeta;
4. bloquejar i etiquetar la SD amb cos, slot i hora;
5. fer dues còpies verificades per hash abans de reutilitzar-la;
6. conservar la targeta original sense modificacions fins a validar les
   dues còpies.

## Què falta demostrar

La decisió de dades ja és clara; la de trigger encara no:

- si Multi Terminal reprodueix exactament els cinc ARW a cada cos;
- si `Recall Custom hold` funciona amb C1/AF-ON remots durant bracket;
- si el recall continua actiu fins al cinquè fotograma i què passa si es
  deixa anar a mig bracket;
- latència i ordre real dels tres brackets;
- si un controlador Bluetooth pot mantenir dos cossos sense interferència;
- comportament després d'hores en espera i amb trànsit intens a 2,4 GHz;
- si una pulsació breu amb ordre `− → 0 → +` és un contacte determinista;
- si la seqüència continua quan el Mac mor o se'n retira el cable;
- cadència sostenible de 90 s amb les targetes reals.

Tot això queda convertit en criteris binaris al
[Gate 9](../tests/2026-07-26_GATE9_CARD_ONLY_TRIGGER_PROTOCOL.md).
