> **AVÍS HISTÒRIC (27-07-2026):** document superat operativament per
> `controller v0.2.3 candidate`, F3/F3B/F3M i el disseny HDR nadiu. Es
> conserva com a evidència i no és autoritat operativa.

# Decisió de control de captura 2026

Data de decisió inicial: 25 de juliol de 2026  
Revisió decisiva: 26 de juliol de 2026  
Estat: **card-only escollit com a ruta principal; trigger pendent de Gate 9**

## Decisió

La ruta principal entre C2 i C3 serà:

- càmeres fora de `PC Remote`;
- RAW sense comprimir a una sola SD UHS-II qualificada del Slot 1;
- `Recording Mode = Standard`, sense JPEG ni duplicació al Slot 2;
- bràqueting continu nadiu;
- trigger/release per Multi Terminal o Bluetooth, sense transport d'imatges;
- controlador físic autònom o watchdog que garanteixi el release;
- Mac com a rellotge i supervisor offline, no com a receptor de RAW;
- llaç obert deliberat: durant C2–C3 no es confirma cap fitxer;
- almenys un cos conserva el trigger Multi Terminal qualificat mentre BLE
  sigui experimental;
- inventari i descàrrega només després de C3.

`gphoto2/libgphoto2` es conserva per a laboratori, identificació, preflight
i fallback fora de la finestra crítica. La v0.1.6 actual no és el backend
de producció de C2–C3.

No es migrarà al Sony Camera Remote SDK:

- la versió 2.02.00, publicada el 10 de juny de 2026, no enumera
  `ILCE-7M3` ni `ILCE-7RM3A`;
- Sony Camera Remote Command sí que els enumera, però és una especificació
  PTP de baix nivell restringida a clients corporatius;
- reescriure ara el controlador contra un protocol nou augmentaria el risc
  sense aportar una garantia de temps real.

Fonts:

- [Sony Camera Remote SDK](https://support.d-imaging.sony.co.jp/app/sdk/en/index.html)
- [Sony Camera Remote Command](https://support.d-imaging.sony.co.jp/app/cameraremotecommand/en/index.html)
- [Manual oficial de gphoto2](https://www.gphoto.org/doc/manual/ref-gphoto2-cli.html)

## Evidència experimental que sosté la decisió

### Bràqueting i bits

- A7III i A7RIIIA: una pressió virtual produeix cinc ARW.
- RAW sense comprimir de 14 bits reals als dos cossos.
- A7III: 10 i 15 ARW acumulats sense drenatge intermedi.
- A7III 5 × 3 EV base 1/125 s:
  `1/125, 1/1000, 1/15, 1/8000, 1/2 s`.
- A7III 5 × 3 EV base 1/250 s: el fotograma nominal de 1/16000 queda
  limitat físicament a 1/8000 encara que l'EXIF conservi `−6 EV`.

### Dues càmeres

Els dos processos van disparar a un mateix target UTC amb una separació
inferida de 2,361 ms i van produir 5 + 5 RAW correctes.

### PTP i drenatge

- `d215=3` ha coexistit amb brackets reals de 5, 10 i 15 fitxers.
- `d215` és una finestra d'objectes publicats, no el total compromès ni la
  capacitat restant del búfer.
- `wait-event-and-download 1s` va baixar 4 RAW en 1,225 s i el cinquè en
  una segona finestra d'1,175 s.
- una ordre de restauració de configuració va trigar 25,759 s a retornar.
- `wait-event` sense `and-download` tampoc és un ACK lleuger: en la branca
  Sony de libgphoto2 2.5.34 fa `GetObjectInfo` i `GetObject` del payload
  complet abans de publicar `FILE_ADDED`.

Conclusió: una ordre PTP síncrona no pot governar el calendari de C2–C3, i
“no guardar al Mac” no equival a “no transferir per USB”.

Evidència completa:
[Gate 7](../tests/2026-07-25_GATE7_A7III_BUFFER_DUAL_HDR.md) i
[backend Sony de libgphoto2 2.5.34](https://github.com/gphoto/libgphoto2/blob/v2.5.34/camlibs/ptp2/library.c#L7084-L7191).

## Pressupost de búfer

Sony publica, en condicions pròpies de ràfega:

| Cos | RAW sense comprimir | RAW sense comprimir + JPEG | Mínim propi demostrat |
|---|---:|---:|---:|
| A7III | 40 | 36 | 15 RAW |
| A7RIIIA | 28 | 28 | 5 RAW |

Fonts:

- [Especificacions A7III](https://www.sony.com/electronics/support/e-mount-body-ilce-7-series/ilce-7m3/specifications)
- [Especificacions A7RIIIA](https://www.sony.com/electronics/support/e-mount-body-ilce-7-series/ilce-7rm3a/specifications)

Aquestes xifres són orientatives i descriuen la ràfega nativa cap a
targeta, no la cua PTP. El límit operatiu serà el que superi l'assaig de
90 s amb targeta, temperatura i alimentació definitives.

## Jerarquia actual de rutes

### 1. Card-only + Multi Terminal

Baseline de màxima robustesa: un bracket `5 × 3 EV` preconfigurat, repetit
per un pols físic. No pot canviar la velocitat base, però elimina completament
PTP i continua si mor gphoto o el Mac.

### 2. Card-only + `Recall Custom hold`

Ruta candidata per obtenir tres bases i quinze passos d'1 EV sense
`set-config`. Els dos cossos poden memoritzar exposició i drive mode; el
RMT-P1BT pot accionar les funcions assignades a C1 i AF-ON. El chord
C1/AF-ON mantingut + shutter i l'automatització Bluetooth encara s'han de
validar físicament.

La qualificació serà asimètrica: primer un únic cos per BLE mentre l'altre
executa la ruta Multi Terminal. No es posaran els dos màsters en una mateixa
ruta de ràdio no oficial.

### 3. `PC+Camera` + JPEG Only al PC

Fallback de gphoto. Pot reduir el payload respecte del RAW, però encara crea
JPEG, transfereix imatges i manté una cua PTP. El
[Gate 8](../tests/2026-07-25_GATE8_PC_CAMERA_SD_PROTOCOL.md) es conserva
només per aquesta contingència.

### 4. `PC+Camera` RAW sense drenatge

Només laboratori o microburst delimitat pel límit demostrat. No fer
`wait-event` evita el GetObject immediat, però no evita que la còpia per al
PC quedi pendent en RAM.

Detall complet:
[Card-only amb RAW sense comprimir](16_CARD_ONLY_RAW_SENSE_COMPRIMIR.md).

## Per què cal sortir de PC Remote

Sony només ofereix `PC Only` i `PC+Camera`; no hi ha `Camera Only`.
`Still Img. Save Dest.` tampoc no es pot canviar durant PC Remote:

- [A7III: Still Img. Save Dest.](https://helpguide.sony.net/ilc/1720/v1/en/contents/TP0001661953.html)
- [A7RIIIA: Still Img. Save Dest.](https://helpguide.sony.net/ilc/2050/v1/en/contents/TP1000189509.html)

La taula de libgphoto2 coneix teòricament `card=0x0010`, però els dos cossos
només han anunciat `sdram` i `card+sdram`. A l'A7RIIIA, forçar `card` ja va
ser ignorat. No es farà servir com a bypass ocult.

## Ports, alimentació i SD

Sony confirma que el Multi/Micro USB Terminal pot portar un accessori de
disparador mentre l'USB-C alimenta la càmera. Per mantenir card-only,
l'USB-C ha de venir d'un power bank/adaptador o passar per un bloqueig de
dades verificat; no ha d'obrir una sessió PC Remote.

Només el Slot 1 és UHS-II als dos cossos. La configuració de velocitat és
una sola targeta al Slot 1, sense RAW+JPEG ni escriptura simultània al Slot 2.

- [A7III: ports i slots](https://helpguide.sony.net/ilc/1720/v1/en/contents/TP0001667670.html)
- [A7RIIIA: manual oficial](https://helpguide.sony.net/ilc/2050/v1/en/print.pdf)

## Línies vermelles

- no actualitzar firmware, gphoto2, libgphoto2 o macOS sense requalificar;
- cap sessió PTP entre C2 i C3 en la ruta principal;
- no usar `wait-event`, `capture-image` o qualsevol drenatge dins la
  finestra protegida;
- no confiar en `d215` com a total;
- no considerar una descàrrega JPEG prova del RAW de targeta;
- no fer `set-config` entre C2 i C3;
- no reintroduir RAW comprimit per resoldre un problema de cadència;
- no compartir un únic punt de fallada sense release físic per als dos cossos.
- no usar so d'obturador com a telemetria amb `Silent Shooting`; als assajos,
  vídeo de la llum SD i verificació posterior.
- no esborrar ni reutilitzar cap SD fins a tenir dues còpies verificades.

## Gates següents

1. Gate 9A: Multi Terminal, RAW sense comprimir, un cos i dos cossos.
2. Gate 9A sostingut: 90 s amb les SD definitives i mesura de la llum
   d'accés/búfer.
3. Gate 9B manual: tres bases amb RMT-P1BT, C1 i AF-ON.
4. Gate 9B automatitzat: fallades, espera llarga, interferència i un cos BLE
   simultani amb un cos Multi Terminal.
5. Gate 9C: decidir amb cobertura/SNR/registre si `5 × 3 EV` és suficient o
   calen tres bases d'1 EV.
6. Només si card-only no és viable, executar el Gate 8 de fallback
   `PC+Camera`.
