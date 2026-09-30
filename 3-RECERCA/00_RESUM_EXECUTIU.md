> **AVÍS HISTÒRIC (27-07-2026):** document superat operativament per
> `controller v0.2.3 candidate`, F3/F3B/F3M i el disseny HDR nadiu de
> `research/22_DISSENY_HDR_NADIU_A7III_AP130.md`. Es conserva com a evidència
> i no és autoritat operativa.

# Resum executiu

## Veredicte actual

La millora gran respecte de 2024 no vindrà d'un únic filtre de Photoshop ni de comprar més material. Vindrà de tractar l'eclipsi com un sistema complet:

1. assignació coherent de càmeres i òptiques;
2. temporització i redundància;
3. ús del bràqueting continu nadiu i del búfer;
4. calibratge RAW abans de demosaicar;
5. registre sobre la corona;
6. fusió HDR lineal;
7. realçament separat del màster científic;
8. validació creuada entre càmeres, exposicions i algoritmes.

## Conclusions de confiança alta

### 0. El 2026 no té el pressupost temporal ni atmosfèric del 2024

La totalitat espanyola serà al vespre, curta i amb el Sol baix. Sense entrar encara en ubicacions:

- la durada exacta dependrà del punt i serà molt inferior als 291 s auditats de 2024;
- el Sol baix augmentarà extinció, dispersió cromàtica, seeing i gradients de cel;
- cada exposició i cada cicle s'hauran de rederivar quan es fixin les circumstàncies locals;
- l'assaig òptic més rellevant no és al migdia, sinó amb el Sol a una altura semblant.

L'IGN dona dos exemples útils: A Coruña, 76 s de totalitat amb el Sol a 12°, i Burgos, 104 s amb el Sol a 8°. Això no decideix la ubicació; sí que prova que no podem reciclar el guió temporal de 2024.

Amb els plans ja reservats i punts municipals representatius:

| Pla | Totalitat | Altura al màxim | Azimut al màxim |
|---|---:|---:|---:|
| A — Ferrol | 88 s | 11,9° | 279,2° |
| B — Medina de Rioseco | 91 s | 8,9° | 281,9° |
| C — Deltebre | 91 s | 4,3° | 285,8° |

Això permet un únic nucli de captura dissenyat per a 88 s. La diferència crítica és l'atmosfera i l'horitzó, sobretot al Delta. Les circumstàncies finals s'han de regenerar amb la coordenada exacta del camp.

### 1. El pipeline Druckmüller té dues sortides diferents

- **Màster lineal calibrat:** preserva tant com és possible la relació entre senyal i radiància; és la base per a mesures, comparacions i una fusió HDR controlada.
- **Derivats realçats:** ACHF/Corona, FNRGF, NAFE, MGN o altres mètodes fan visible la morfologia, però alteren localment els valors i no conserven fotometria absoluta.

Barrejar aquestes dues etapes impediria saber si un detall és físic, un producte de la fusió o un artefacte del realçament.

### 2. El resultat de Druckmüller no depèn d'un «algoritme secret» únic

És una cadena:

- exposicions abundants i solapades;
- darks, flats, bias/offset i caracterització de la resposta;
- registre subpíxel per correlació de fase;
- fusió ponderada només en la zona útil i lineal de cada exposició;
- compensació de transparència i llum difusa;
- realçament adaptatiu multiescala;
- revisió humana i contrast amb dades independents.

Part del programari és privat —especialment Corona/ACHF, LDIC i ACC—, però els principis són publicats i hi ha alternatives obertes prou bones per construir un pipeline propi i auditable.

### 3. La A7RIIIA té més sentit al telescopi

Amb els valors nominals:

| Tren | Escala aproximada | Diàmetre solar aproximat | Camp vertical en radis solars |
|---|---:|---:|---:|
| A7RIIIA + 585 mm | 1,59″/px | 1.190 px | 4,47 R☉ |
| A7III + 585 mm | 2,09″/px | 905 px | 4,47 R☉ |
| A7RIIIA + 300 mm | 3,10″/px | 619 px | 8,72 R☉ |
| A7III + 300 mm | 4,08″/px | 471 px | 8,72 R☉ |

Per tant:

- els 42,4 MP aporten més on la focal de 585 mm pot convertir-los en detall;
- la càmera no modificada és preferible en el tren destinat a corona interior i prominències;
- els 24 MP a 300 mm encara deixen una imatge solar prou gran i un camp ampli excel·lent per a corona exterior.

El balanç de blancs pot fer que la A7III modificada sembli normal de dia, però **no restaura la resposta espectral original del RAW**. Tampoc elimina la saturació més primerenca de prominències ni l'eventual desenfoc cromàtic causat per longituds d'ona addicionals. Això coincideix amb l'advertiment de l'equip Druckmüller.

### 4. Entre 200 i 300 mm, 300 mm és la focal principal més útil

Dos-cents mil·límetres dona molt camp però desaprofita resolució en una càmera de format complet si la prioritat és la corona. Tres-cents mil·límetres manté un camp vertical d'uns 8,7 radis solars i és coherent amb la recomanació directa rebuda de Hana Druckmüllerová.

El 70–200 a 200 mm continua sent útil com a:

- pla de contingència;
- composició ambiental;
- tercer sistema;
- opció si seguiment, vent o muntatge fan inviable el 300 mm.

No és la primera opció per al segon màster coronal.

### 5. C2–C3 serà card-only; gphoto queda fora del camí de dades

La inspecció de libgphoto2 2.5.34 ha resolt una ambigüitat important:
`wait-event` no és un ACK lleuger en aquestes Sony. El backend llegeix
`d215`, executa `GetObject` del fitxer complet, el posa a memòria de
libgphoto2 i només després publica `FILE_ADDED`. Pot no aparèixer cap ARW
al directori del Mac, però el payload ja ha travessat l'USB.

A7III i A7RIIIA només han anunciat `sdram` i `card+sdram`; no ofereixen
`card`. Sony també documenta només `PC Only` i `PC+Camera`. Per tant,
deixar de drenar en PC Remote no és card-only: només acumula una cua PTP de
profunditat desconeguda.

La ruta principal passa a ser:

- càmera fora de PC Remote entre C2 i C3;
- RAW sense comprimir només a una SD UHS-II qualificada del Slot 1;
- bràqueting continu nadiu;
- trigger independent per Multi Terminal o Bluetooth;
- cap `wait-event`, `capture-image`, drenatge ni `set-config`;
- Mac com a rellotge/supervisor, no com a receptor de fotografies;
- funcionament deliberadament en llaç obert: es confirmen ordres i releases,
  no fitxers;
- almenys un cos amb Multi Terminal qualificat mentre l'altre assaja
  `Recall Custom hold` per Bluetooth;
- verificació i còpia només després de C3.

Un assaig publicat el febrer de 2026 amb exactament A7III i A7RIIIA va
obtenir una escala de 15 exposicions a passos d'1 EV amb només tres canvis
de velocitat, combinant tres bràquetings continus de cinc imatges separades
3 EV. En lloc de fer aquests canvis per PTP, investigarem
`Recall Custom hold`: C1 i AF-ON poden seleccionar dues receptes mentre el
perfil normal aporta la tercera, tot sense transferir imatges.

**Actualització 25-07-2026.** La semàntica essencial ja s'ha reproduït amb
els cossos de Pere:

- A7III i A7RIIIA produeixen cinc RAW amb una sola pulsació sostinguda;
- les dues conserven 14 bits reals en silent, RAW sense comprimir;
- l'A7III ha acumulat 15 RAW en tres brackets, sense drenatge intermedi,
  i els ha lliurat tots al final;
- els dos cossos han disparat simultàniament a 2,36 ms de diferència;
- el bracket A7III 5 × 3 EV base 1/125 cobreix físicament
  `1/8000…1/2 s`;
- base 1/250 queda retallada a 1/8000 malgrat conservar `−6 EV` a l'EXIF.
- `d215` pot indicar 3 mentre hi ha 5, 10 o 15 captures compromeses;
- una ordre PTP de configuració ha trigat 25,759 s: no hi haurà
  `set-config` ni drenatge dins les finestres protegides.

Sony Camera Remote SDK 2.02.00 no admet ni A7III ni A7RIIIA. Camera Remote
Command sí que les enumera, però és PTP de baix nivell restringit a clients
corporatius. No hi ha una alternativa oficial disponible que justifiqui
reescriure el sistema.

El codi de libgphoto2 confirma que el control Sony etiquetat `bulb` envia
una pressió/retenció/alliberament del disparador; no obliga a seleccionar
una exposició BULB. Això ja ha validat la semàntica del bracket al
laboratori. La producció ha de reproduir-la per una via que no obri PTP.

Vegeu el [Gate 7](../tests/2026-07-25_GATE7_A7III_BUFFER_DUAL_HDR.md), la
[decisió de control](14_DECISIO_CONTROL_CAPTURA_2026.md), la
[decisió card-only](16_CARD_ONLY_RAW_SENSE_COMPRIMIR.md) i el
[Gate 9](../tests/2026-07-26_GATE9_CARD_ONLY_TRIGGER_PROTOCOL.md).

### 6. El 2024 va fallar el contracte entre ordre, estat i temps

L'auditoria dels RAW crítics ha trobat:

- **A7III + AP:** 56 RAW en 291 s; mediana de 2 s, però dos buits greus de 30 i 125 s.
- **Canon 6D + 300 mm:** 146 RAW en 290 s; mediana de 2 s i cap buit superior a 4 s.
- **A7S + Questar:** 58 RAW en 325 s; mediana de 6 s. Durant totalitat, 35 de 45 captures —77,8%— no tenen la velocitat del seu slot programat.

El buit de 125 s de l'AP és la pèrdua temporal més costosa. No es pot
atribuir amb certesa a una sola causa: PTP/USB, `wait-event`, càmera ocupada i
búfer/targeta continuen sent mecanismes compatibles. Sí que queda demostrat
que l'arquitectura no podia limitar ni diagnosticar cap d'ells.

L'A7S aporta una prova encara més directa: el guió ordenava una escala
alternada, però els RAW formen blocs llargs; C2 demana `1/100` i obté
`1/640`, i C3 demana `1/8000` i obté `1/20`. A més, `1/2` no existia al menú
del cos —el literal admès era `5/10`— i el guió disparava sense comprovar el
retorn ni rellegir l'estat.

Els scripts etiquetats com a finals presenten:

- dates i contactes de prova;
- errors de sintaxi;
- ordres sense port explícit;
- inicialitzacions que disparen fotos reals;
- processos `gphoto2` nous per a cada operació;
- absència de comprovació de retorn i de configuració;
- noms de fitxer irrellevants quan no es descarrega;
- cap registre estructurat;
- seqüències que no coincideixen exactament amb els RAW.

La causa sistèmica és prou clara: configuracions sense identitat de cos,
processos i sessions PTP nous per operació, errors ignorats, cap readback, cap
deadline i descàrrega bloquejant a l'A7S. La lliçó no és només registrar
millor: és impedir que una ordre no confirmada o tardana pugui governar la
captura següent. Vegeu la
[forense dels RAW](12_FORENSICA_RAW_2024.md) i
l'[autòpsia causal](13_AUTOPSIA_CAUSAL_2024.md).

## Arquitectura conceptual 2026

### Capa A — captura

- dues cadenes principals complementàries i tan independents com sigui possible;
- plans separats per parcialitat, C2, totalitat, C3 i postcontacte;
- cap sessió PC Remote ni transferència d'imatges durant la finestra crítica;
- RAW sense comprimir a una SD UHS-II del Slot 1;
- trigger amb release físicament independent;
- cap telemetria d'imatge durant C2–C3 ni reintents de *catch-up*;
- bràqueting curt i repetit, no una única escala lenta;
- seqüència específica de prominències/diamant/Baily, separada de l'HDR de corona;
- rellotges sincronitzats i registre temporal monotònic;
- comprovació del nombre de fitxers esperat.

### Capa B — calibratge

- RAW intactes;
- sensor net i estabilitzat;
- flats sense moure sensor, focus ni obertura;
- darks i bias/offset quan siguin útils;
- perfil de linealitat i saturació per càmera, ISO i mode RAW;
- possible perfil espectral comparatiu entre càmera modificada i normal.

### Capa C — registre i fusió

- calibratge sobre el mosaic Bayer abans de demosaicar, si el revelador ho permet;
- registre sobre estructures coronals, emmascarant Lluna i saturació;
- registre progressiu entre exposicions veïnes;
- fusió ponderada per SNR, linealitat i saturació;
- finestres temporals petites per evitar convertir el màster en una mitjana de massa minuts.

### Capa D — productes

1. màster HDR lineal i documentat;
2. versió visual principal;
3. versions de control amb MGN, NRGF/FNRGF, WOW i RHEF;
4. màscara d'artefactes i registre de decisions;
5. composicions artístiques separades, si es vol incorporar paisatge o contactes.

## Decisions que encara no estan tancades

- assignació definitiva A7RIIIA/AP versus mantenir la combinació provada A7III/AP;
- Multi Terminal simple o `Recall Custom hold` per Bluetooth;
- controlador autònom per cos o un únic controlador dual;
- si BLE supera el Gate en un cos sense comprometre el segon cos cablejat;
- model i cadència sostenible de les SD UHS-II definitives;
- patró exacte de bràqueting i nombre de repeticions;
- ús o no de la Canon 6D;
- quantitat i tipus de calibracions de camp;
- filtre addicional per limitar la resposta de la A7III modificada;
- impacte del fons vermell i la dispersió a baixa altura sobre la A7III modificada;
- pipeline final de revelat/calibratge Bayer;
- criteris objectius de focus, halos, clipping i cadència.

Aquestes decisions s'han de prendre amb assajos, no durant l'eclipsi.

## Quatre gates abans de congelar el release

1. **Semàntica i bits:** una pressió produeix els 5 ARW; ordre EV i 14 bits
   reals. **PASS de laboratori** als dos cossos.
2. **Card-only sostingut:** Slot 1 UHS-II, RAW sense comprimir, zero payload
   al Mac i 90 s sense alentiment. **Pendent — Gate 9A**.
3. **Escala de tres bases:** 15 velocitats úniques amb C1/AF-ON, un cos i
   després un assaig asimètric amb l'altre cos cablejat. **Pendent — Gate
   9B**.
4. **Temps i degradació:** autoritat temporal única, C2/C3 i perfil de limbe
   com a inputs, `late_policy=skip`, watchdog i release físic independent.
   **Pendent**.

Gate 8 (`PC+Camera`) queda reclassificat com a fallback, no com a pas
necessari de la ruta principal.

L'assignació A7RIIIA/AP no ha de quedar codificada: ha de ser un paràmetre reversible fins que l'A/B òptic i el test de fons vermell la confirmin.
