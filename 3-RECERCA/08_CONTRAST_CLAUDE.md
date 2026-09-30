# Contrast crític amb Claude Fable 5

## Traçabilitat

- Model seleccionat a la interfície: **Fable 5 Extra**.
- Data: 25 de juliol de 2026.
- Conversa nova i separada de projectes anteriors.
- [Prompt complet enviat](CLAUDE_PROMPT.md).
- [Conversa de Claude](https://claude.ai/chat/cf1fdb0a-acce-4875-9519-5cbb464a469c).

La resposta de Claude és una **revisió IA**, no una font primària. Les propostes s'han contrastat amb:

- documents Sony;
- libgphoto2;
- IGN/NASA;
- papers Druckmüller–Habbal;
- RAW de 2024.

## Veredicte del contrast

Claude coincideix amb el nucli:

- A7RIIIA stock a 585 mm és la hipòtesi racional;
- A7III modificada a 300 mm és un segon camp valuós;
- RAW a targeta i descàrrega diferida;
- bràqueting nadiu;
- màster lineal separat dels realçaments;
- no decidir assignació final, RAW ni obturador sense assaig.

Va aportar quatre correccions importants:

1. **El pressupost temporal de 2026 és molt més curt que el de 2024.**
2. **El Sol baix és un problema fotogràfic fins i tot amb meteorologia bona.**
3. **Les dues Sony són complementàries i només parcialment redundants.**
4. **La A7III modificada al 300 mm pot patir més fons vermell/gradient just a la corona exterior.**

Aquest quart punt és el millor argument contra la nostra assignació provisional i s'ha incorporat a l'assaig A/B.

## 1. Durada i altura solar

### Fet

L'eclipsi del 12 d'agost de 2026 travessa Espanya al vespre. La durada i l'altura varien fortament amb el lloc.

L'[Instituto Geográfico Nacional](https://astronomia.ign.es/en/eclipses-de-sol-y-luna/eclipse-total-sol-de-12-de-agosto-2026) dona, per exemple:

- A Coruña: 76 s de totalitat, amb el Sol a 12°;
- Burgos: 104 s de totalitat, amb el Sol a 8°.

Les [circumstàncies NASA](https://eclipse.gsfc.nasa.gov/SEpath/SEpath2001/SE2026Aug12Tpath.html) i els visors oficials permeten calcular cada punt.

### Inferència adoptada

Els 291 s auditats de 2024 no són un pressupost vàlid per a 2026. Cal:

- refer tota la màquina d'estats amb la durada local;
- reservar temps explícit a C2 i C3;
- limitar la longitud de cada escala;
- abortar l'HDR amb marge abans de C3;
- decidir quants cicles complets caben realment.

### Sol baix

Encara que el cel sigui net:

- augmenta la massa d'aire;
- augmenta extinció;
- augmenta dispersió cromàtica atmosfèrica;
- el seeing pot empitjorar;
- el fons i els gradients són més forts;
- la corona exterior competirà amb un cel més brillant.

Claude va donar xifres generals de massa d'aire i dispersió. No les adoptem com a universals:

- a 12°, la massa d'aire és molt diferent de la de 3°;
- extinció i dispersió depenen de lloc, aerosol, altura i longitud d'ona;
- s'han de calcular i mesurar quan es concreti el lloc.

No és consell d'ubicació; és una condició òptica que afecta qualsevol punt espanyol de la franja.

## 2. A7RIIIA/AP versus A7III modificada/AP

### A favor de la hipòtesi actual

- consell directe Druckmüller: càmera normal preferible;
- 42,4 MP aprofitats al tren llarg;
- resposta stock per a color i prominències;
- A7III a 300 encara dona ~471 px de Sol;
- el patró HDR cap als dos búfers.

### Argument adversarial nou

La corona exterior és precisament on:

- el senyal és més feble;
- el cel baix pesa més;
- el gradient pot ser vermell;
- la resposta estesa de la modificada pot captar més fons.

Per tant, no és automàtic que «modificada al camp ampli» sigui innocu. Podria passar que:

- A7III modificada + AP continuï sent millor per la combinació ja provada;
- A7RIIIA + 300 doni una corona exterior més neta.

### Assaig refutador incorporat

Amb la mateixa òptica, a una altura solar semblant:

- gradient per canal;
- SNR de fons;
- halos;
- PSF per canal;
- clipping;
- color;
- regressió sectorial necessària.

La decisió final pot capgirar-se si la modificada penalitza molt el camp exterior.

## 3. «Redundància» versus complementarietat

Claude assenyala correctament que:

- 585 mm a 1,59″/px;
- 300 mm a 4,08″/px;

no són substituts equivalents.

La formulació adoptada és:

- **complementarietat principal**;
- **cross-backup parcial**: el 300 encara pot salvar una imatge de corona si falla l'AP;
- **redundància real** només si una tercera cadena independent cobreix el producte mínim.

Possibles redundàncies:

- Canon 6D en muntura/trípode independent;
- mode cablejat sense PC;
- dos controladors independents;
- configuració manual de retorn.

Si AP i 300 comparteixen muntura, alimentació o controlador, hi ha un punt únic de fallada.

## 4. Bràqueting 3×5

### Fet aritmètic

La suma dels temps oberts de les 15 exposicions és aproximadament 6,4 s:

- grup base 1/80: ~0,91 s;
- grup base 1/40: ~1,83 s;
- grup base 1/20: ~3,66 s.

Amb interframes, canvi de base i drenatge, el cicle real serà més llarg. Només el banc dirà si és:

- 8 s;
- 10 s;
- 15 s;
- més.

### Conseqüència

En una totalitat de l'ordre de 60–110 s, no podem pressupostar cinc minuts. Cal saber:

- quants cicles caben;
- quantes repeticions obté cada exposició;
- quan s'atura abans de C3.

### Variant 2×5

Claude proposa provar dues bases en comptes de tres:

- menys transaccions;
- cicle aproximadament un terç més curt;
- espaiat final alternant 1 i 2 EV;
- 14 bits podrien donar prou solapament.

No s'adopta encara. En una fusió científica, passos d'1 EV donen:

- millor regressió;
- més redundància;
- menor dependència de linealitat.

Cal comparar 3×5, 2×5 i, si és útil, 2×9.

### Contactes fora de l'escala

Coincidència forta:

- 15 exposicions HDR no substitueixen un bloc C2/C3;
- el valor nominal ~1/5000 no és necessàriament suficient per a totes les fases del diamant;
- cal una ràfega curta dedicada;
- cap càmera ha d'estar atrapada en 3,2 s quan arriba C3.

La velocitat exacta —1/8000, 1/4000, 1/2000— depèn d'ISO, obertura, atmosfera, prominències i resultat desitjat.

### Earthshine

Claude suggereix explorar 6–13 s al 300 mm. No s'incorpora com a recomanació:

- consumeix una fracció gran de la totalitat;
- augmenta moviment i risc;
- el fons a baixa altura pot limitar abans;
- podria fer perdre C3.

Es manté com a assaig opcional, només si la durada local i les proves ho justifiquen.

## 5. Mode RAW, ISO i obturador

Claude demana una matriu completa:

- simple/continu;
- pressió virtual;
- mecànic/EFCS/electrònic;
- comprimit/no comprimit.

S'adopta.

### Correccions importants

- 1/5120 és un valor matemàtic; la càmera el quantitza probablement a 1/5000.
- RAW comprimit Sony és lossy i pot penalitzar vores d'alt contrast.
- 14 versus 12 bits s'ha de verificar als ARW.
- EFCS i silent s'han de validar específicament en highlights extrems.
- Long Exposure NR ha d'estar desactivat.

Claude esmenta doble guany prop d'ISO 640. No s'adopta com a configuració:

- el punt exacte i el benefici depenen de cos/mode;
- la prioritat és calibratge simple i highlights;
- l'ISO s'ha de decidir amb photon-transfer/linealitat i proves reals.

## 6. Punts únics de fallada

Incorporats:

- ordinador únic;
- bus/hub USB únic;
- muntura compartida;
- alimentació compartida;
- targeta única;
- enfocament amb canvi tèrmic;
- rellotges;
- operador;
- ruta PTP;
- `release` del disparador virtual.

### Mode de retorn autònom

Idea acceptada:

- bràqueting nadiu;
- disparador cablejat Multi Terminal;
- RAW a targeta;
- sense dependència de PC;
- configuració ja aplicada.

No cal que sigui la ruta principal. Ha d'existir i haver superat assajos.

## 7. Les cinc proves de Claude

1. **Matriu bits/format/obturador.**
2. **Estrès de cadència amb múltiples cicles i targeta definitiva.**
3. **A/B òptic dels dos cossos a l'AP.**
4. **Assaig de Sol baix per gradient, dispersió i seeing.**
5. **Assaig complet fins a ingesta i registre.**

Coincideixen amb el nostre pla i s'han afegit com a prioritats.

## 8. Correccions a la resposta de Claude

La revisió ha estat útil, però conté punts que no s'han de copiar sense verificar:

- va atribuir FNRGF a «Druckmüllerová, Morgan i Druckmüller, ApJS 2011»; la referència correcta és **Hana Druckmüllerová, Huw Morgan i Shadia Habbal, ApJ 737:88**;
- les xifres de massa d'aire/extinció no són vàlides igual de 3° a 12°;
- 1/5000 no és universalment insuficient per a Baily; depèn del sistema;
- 6–13 s per Earthshine és una hipòtesi arriscada;
- EFCS, silent i doble guany necessiten verificació específica;
- la invocació nova de gphoto2 afegeix negociació i latència, però no podem demostrar que causés el buit de 125 s.

Aquestes correccions exemplifiquen la regla:

> Claude és revisor; les fonts primàries i els assajos són l'autoritat.

## Consens final després del contrast

### Conservar

- hipòtesi A7RIIIA/585 + A7III mod/300;
- retorn possible a A7III/AP;
- bràqueting nadiu;
- RAW a targeta;
- descàrrega diferida;
- màster lineal;
- pipeline obert i auditable.

### Canviar

- pressupostar la durada real de 2026;
- incorporar el Sol baix;
- separar contactes de l'HDR;
- dir complementarietat, no redundància completa;
- afegir prova del gradient vermell de la modificada;
- crear mode de retorn sense PC;
- fer photon-transfer/linealitat;
- simular C2–C3 complet.

### No decidir encara

- assignació definitiva;
- 3×5 versus 2×5/2×9;
- ISO;
- RAW comprimit/no comprimit;
- mecànic/EFCS/silent;
- PC Only/PC+Camera;
- Earthshine llarg;
- Canon 6D;
- dependència final de l'acció `bulb`.

## Segona ronda: correccions retornades i consens

Es van retornar a Fable 5:

- la citació FNRGF correcta;
- la verificació del codi libgphoto2;
- la compatibilitat Sony SDK/PTP;
- el caràcter local de durada i atmosfera;
- els punts acceptats i rebutjats.

Claude va reconèixer explícitament que la seva atribució de FNRGF era errònia.

### Objecció sobre la pressió virtual

El codi separa:

- `bulb=1`: half-press + request shooting;
- espera del controlador;
- `bulb=0`: release.

Claude assenyala que el nom `RequestOneShooting` no prova per si sol que el cos produeixi cinc ARW en mode de bràqueting continu.

Adjudicació:

- el benchmark de Fliker amb A7III/A7RIIIA és evidència externa que sí que funciona;
- el codi mostra una retenció separable;
- cap de les dues coses substitueix la prova amb els cossos de Pere;
- si només surt un ARW, l'arquitectura canvia de tres triggers a quinze.

Per això és el primer gate.

### Altres punts finals

- comprovar al menú si 9 frames admeten només fins a 1 EV;
- tractar horaris de contacte i correccions de perfil lunar com a inputs, no constants dins del codi;
- definir una autoritat de temps única;
- escriure el runbook de degradació abans del controlador;
- considerar Multi Terminal l'única implementació realment independent de gphoto2.

### Els tres gates consensuats

#### Gate 1 — semàntica de tret i matriu de bits

Ha de demostrar:

- un trigger sostingut produeix 5 ARW;
- es pot canviar velocitat PTP sense sortir de `Cont. Bracket`;
- RAW sense comprimir conserva 14 bits;
- A7RIIIA enumera i respon correctament;
- el release és fiable.

És arquitectura, no simple paràmetre.

#### Gate 2 — pressupost de cadència

Amb la ruta guanyadora:

- mesurar 3×5;
- mesurar 2×5;
- mesurar 2×9 si el cos ho permet;
- targeta i destinació definitives;
- cada cos per separat i tots dos simultàniament;
- amb les dues permutacions A7RIIIA/A7III a 585/300;
- fallback i fault injection.

Criteri:

- el pitjor cicle, multiplicat per les repeticions mínimes, cap dins la totalitat local amb marge abans de C3.

#### Gate 3 — contracte de temps i degradació

Decidir abans del codi:

- autoritat temporal;
- UTC;
- C2/C3;
- correcció de limbe;
- inici/abort de cada fase;
- què passa si es perd rellotge;
- què passa si falla USB;
- quan es passa a Multi Terminal;
- accions sense diagnòstic improvisat.

### Decisió metodològica final

L'assignació de cossos no bloqueja el controlador. Si els assajos de cadència cobreixen les dues permutacions, l'assignació és una configuració reversible fins a l'assaig general.

## Adjudicació experimental posterior — 25 de juliol de 2026

Aquesta secció no atribueix a Claude una tercera revisió: contrasta el
consens anterior amb les proves físiques posteriors.

### Objecció `RequestOneShooting`

Resolució: **superada**.

- A7III i A7RIIIA han produït cinc ARW amb una sola pressió sostinguda.
- L'ordre i els bias del bracket són correctes.
- Els dos cossos han conservat RAW sense comprimir de 14 bits.

La prudència de Claude era correcta: el codi font no ho podia provar. El
Gate 7 sí.

### Gate 1

Estat: **PASS parcial avançat**.

- semàntica de tret, identitat, ordre i bits: demostrats;
- release normal: demostrat;
- release físicament independent davant un bloqueig libgphoto: pendent.

### Gate 2

Estat: **PASS parcial en PC Only**.

- A7III: 15 RAW sense drenatge intermedi;
- dues càmeres: 5 + 5 RAW al mateix target, separació de 2,361 ms;
- `PC+Camera`, persistència SD, USB-C SuperSpeed A7RIIIA i simulació de
  90 s: pendents.

### Gate 3

Estat: **pendent**.

La dada nova més important és una ordre `set-config` que va tardar
25,759 s. Això reforça exactament l'objecció de Claude:

- cap canvi PTP dins C2–C3;
- targets absoluts;
- política `fatal / skip / degraded_continue`;
- Multi Terminal com a única ruta candidata realment independent.

### Decisió gphoto versus Sony

Sony Camera Remote SDK 2.02.00 no admet els dos cossos. Camera Remote
Command els admet a nivell PTP, però està restringit a clients corporatius.
No hi ha base per reescriure el controlador.

El consens actual queda, doncs:

> gphoto2 persistent per configurar i disparar brackets nadius; SD com a
> persistència; drenatge fora de finestres protegides; Multi Terminal com
> a fallback independent que encara s'ha de qualificar.

## Tercera ronda — card-only real i RAW sense comprimir, 26 de juliol

S'ha reprès la mateixa conversa canònica de Fable 5 Extra amb el nou
resultat de la inspecció de libgphoto2 i dels menús dels dos cossos. Aquesta
ronda **substitueix** la conclusió anterior que mantenia gphoto persistent
per disparar durant C2–C3.

### Fet nou retornat a Claude

- `wait-event` acaba fent `GetObject` del RAW complet al backend Sony;
- els cossos només exposen `sdram` i `card+sdram`, no `card`;
- Sony només documenta `PC Only` i `PC+Camera` en PC Remote;
- RAW sense comprimir i zero trànsit d'imatge exigeixen sortir de PC Remote;
- Multi Terminal ja és el baseline;
- `Recall Custom hold` amb C1/AF-ON és una hipòtesi per obtenir tres bases
  sense PTP.

Claude coincideix que card-only fora de PC Remote és l'única arquitectura
coherent amb els dos requisits innegociables. La seva revisió va afegir cinc
controls útils:

1. declarar que la totalitat funciona en **llaç obert**;
2. provar que el recall es manté durant tot el bracket i què passa si
   s'allibera a mig recorregut;
3. no posar els dos cossos al BLE experimental: almenys un ha de conservar
   el trigger cablejat qualificat;
4. sotmetre BLE a espera llarga, pèrdua de connexió i interferència real a
   2,4 GHz;
5. tractar la SD com a única còpia fins que, després de C3, existeixin dues
   còpies verificades.

### Adjudicació pròpia

S'accepten:

- llaç obert sense telemetria d'imatge;
- asimetria deliberada entre càmeres;
- proves de release de C1/AF-ON a mig bracket;
- prova llarga i interferència;
- regla binària per decidir entre `5 × 3 EV` i tres bases;
- cadena de custòdia post-C3.

Es modifica una proposta de Claude: va suggerir usar àudio de l'obturador
com a senyal residual. Amb `Silent Shooting = On` això no existeix i canviar
a obturador mecànic alteraria precisament el mode qualificat. Als assajos
s'usaran:

- vídeo de la llum d'accés SD amb referència temporal visible;
- log monotònic de press/release;
- recompte, EXIF i hashes després de la tanda.

Cap d'aquests senyals governa la seqüència en producció.

### Criteri de captura consensuat

El `5 × 3 EV` cablejat guanya si cada zona radial necessària conserva
almenys dues exposicions útils per canal, amb SNR suficient, solapament i
registre progressiu estable a través dels salts de 3 EV. Si qualsevol zona
o el registre falla, guanya l'escala d'1 EV de tres bases, sempre que passi
el pressupost de 88 s i la prova BLE.

La decisió no és «més fotogrames sempre és millor». És:

> la ruta més simple que cobreixi tot el rang necessari, repetida prou
> vegades i sense cap dependència de dades amb el Mac.

Claude continua sent revisor. Les fonts Sony/libgphoto2 i el Gate 9 físic
són l'autoritat final.

## Quarta ronda — retirada d'IOBluetooth i Fase A CoreBluetooth, 26 de juliol

S'ha reprès la mateixa conversa canònica després de les proves físiques.
Claude ha rebut els fets i comptatges locals, no una conclusió prefabricada:

- la ruta `IOBluetoothDeviceInquiry` marcada com a LE va crear una sessió
  Classic, va fer inquiry BR/EDR i SDP, i no va emetre el scan CoreBluetooth
  esperat;
- les dues apps IOBluetooth han quedat retirades i no executables;
- el nou artefacte `SonyBLEDiscoveryOnly` només fa scan, callback i
  `stopScan`;
- la Fase A, amb totes les Sony apagades, va obtenir TCC
  `allowed_always`, 29 callbacks i 17 identificadors, amb zero connexions,
  pairing, SMP, L2CAP o GATT atribuïbles al bundle.

### Coincidències útils

Claude confirma com a revisió independent, no com a font:

1. la Fase A satisfà el gate d'autorització i contenció;
2. no hi ha cap motiu de seguretat per evitar una única finestra de 45 s
   amb l'A7III en Pairing, sempre que sigui exactament el mateix artefacte;
3. `active scan` pot emetre `SCAN_REQ`, però sense `CONNECT_IND` no pot
   iniciar connexió, SMP ni bond, ni consumir la finestra per protocol;
4. l'oracle de transport ha de continuar mostrant només una sessió central
   de scan, i qualsevol connexió, pairing, SMP o GATT atribuïble invalida la
   ronda;
5. un resultat positiu només autoritza continuar investigant identitat, no
   connectar ni enviar ordres;
6. un codi `2` val exactament «macOS no ha lliurat cap anunci que superi
   els gates durant aquesta finestra». No prova que la càmera no anunciï,
   que els gates siguin complets, ni que MCU, Android o un sniffer obtinguin
   el mateix resultat.

### Matís no incorporat a l'artefacte congelat

Claude suggereix afegir un testimoni d'aire i comparar trams abans, durant
i després de Pairing. És una millora d'interpretabilitat per a una eventual
repetició negativa, però no justifica reconstruir ara el binari ja
autoritzat ni canviar aquesta primera finestra. Si surt codi `2`, la següent
prova s'haurà de dissenyar amb un sniffer independent o una altra pila BLE.

La pantalla de Pairing visible durant els 45 s és part de l'oracle humà.
El Mac es manté com a instrument d'observació; la via de bond amb macOS
continua tancada.

## Cinquena ronda — Fase B positiva i identitat de l'A7III

La finestra real de discovery amb Pairing visible ha retornat codi `0`:
922 callbacks totals, 695 Sony, un únic candidat, UUID històric, nom
anunciat `ILCE-7M3`, company `0x012D`, payload estable, connectable i adreça
pública visible al log de `bluetoothd`. El servei anunciat és només `1800`;
`FF00` no apareix. El Mac tampoc conserva la càmera al cache de dispositius
aparellats.

Claude considera satisfets identitat i contenció. La seva jerarquia per a
un central extern és:

1. adreça pública verificada entre power-cycles;
2. company id més prefix opac del manufacturer payload;
3. nom anunciat com a confirmació;
4. connectabilitat i correlació amb Pairing com a context.

No accepta com a selector únic l'UUID local de CoreBluetooth, el servei
genèric `1800`, el nom o l'RSSI. Coincideix que `FF00` hauria produït un fals
negatiu si hagués estat l'únic filtre.

Els 47,249 s reals davant 45 s configurats són compatibles amb backpressure
de callbacks i logging a la main queue. No afecta la seguretat d'aquesta
prova, però confirma que el Mac no ha de temporitzar els contactes.

El contrast no altera la prioritat:

1. RMT-P1BT manual per decidir si `Recall Custom hold` sosté el bracket;
2. MCU → Multi Terminal en paral·lel;
3. central extern discovery-only;
4. bond extern només amb gate separat i si la semàntica del comandament
   oficial justifica continuar.

La resposta de Claude continua sent revisió. Els logs, l'artefacte congelat
i els assajos físics són l'autoritat.
