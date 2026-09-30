> **AVÍS HISTÒRIC (27-07-2026):** document superat operativament per
> `controller v0.2.3 candidate`, F3/F3B/F3M i el disseny HDR nadiu. Es
> conserva com a evidència i no és autoritat operativa.

# Pla d'assajos i decisions pendents

## Principi

No s'ha d'implementar el controlador final fins que els assajos hagin tancat:

- assignació de cossos;
- rendiment RAW sense comprimir a la SD definitiva;
- bràqueting;
- canal de trigger;
- release físic i watchdog;
- estratègia de contactes.

## Gates previs a qualsevol implementació

### Gate 1 — card-only i trigger físic

- càmera fora de PC Remote;
- Multi Terminal produeix cinc ARW en `Cont. Bracket`;
- RAW sense comprimir de 14 bits només al Slot 1 UHS-II;
- zero fitxers i zero payload d'imatge al Mac;
- 90 s sense pèrdues ni alentiment;
- release efectiu encara que mori el Mac.

Si falla, es redueix la cadència o es redissenya el trigger; no es
reintrodueix compressió ni descàrrega síncrona.

### Gate 2 — tres bases sense PTP

- `Recall Custom hold` manual amb C1/AF-ON + shutter;
- quinze velocitats úniques a passos d'1 EV;
- automatització BLE en un cos mentre l'altre continua per Multi Terminal;
- dos cossos BLE només com a Gate posterior amb controladors independents;
- 3×5 versus un únic 5×3 repetit;
- targeta i RAW definitius;
- cada cos;
- tots dos simultanis;
- marge d'abort abans de C3;
- pèrdua de BLE sense tecla o shutter retingut.

### Gate 3 — contracte de temps i degradació

- autoritat de temps única;
- UTC i font de sincronització;
- C2/C3 i correcció de perfil lunar com a inputs;
- màquina d'estats absoluta;
- runbook precompromès;
- cap diagnòstic improvisat durant la totalitat.

No és un refinament acadèmic: [NASA documenta](https://umbra.nascom.nasa.gov/eclipse/010621/text/lunar-limb-profile.html) que muntanyes i valls del limbe poden desplaçar els contactes calculats uns quants segons. Amb una totalitat curta, el controlador no pot amagar aquesta convenció dins d'una constant.

L'assignació de cossos queda com a paràmetre reversible i no ha de bloquejar l'arquitectura.

La semàntica del bracket i els 14 bits ja han passat al banc PTP. Ara s'han
de reproduir sense obrir PTP; vegeu el
[Gate 9](../tests/2026-07-26_GATE9_CARD_ONLY_TRIGGER_PROTOCOL.md).

## Fase 0 — inventari

Registrar:

- firmware A7RIIIA;
- firmware A7III;
- tipus exacte de modificació A7III;
- targetes, capacitat i velocitat;
- cables i longitud;
- ordinador i sistema operatiu;
- versió gphoto2/libgphoto2;
- muntures;
- alimentació;
- disparadors Multi Terminal;
- disponibilitat real de Canon i òptica.

Sortida: una fitxa immutable per component.

## Fase 1 — A/B òptic i espectral

### Objectiu

Decidir quin cos va a l'AP.

### Matriu

1. A7RIIIA + AP/QUADTCC.
2. A7III modificada + AP/QUADTCC.
3. A7RIIIA + 300 GM.
4. A7III modificada + 300 GM.

Mateix:

- motiu solar;
- filtre;
- ISO;
- exposició relativa;
- enfocament optimitzat;
- tracking;
- condicions tan pròximes com sigui possible.

Mesurar:

- FWHM/MTF de detall;
- focus per canal;
- desplaçament cromàtic radial;
- halo;
- ghosts;
- vinyetatge;
- clipping per canal;
- flare;
- estabilitat de focus;
- percentatge de frames nítids.

### Criteri de decisió

A7RIIIA/AP queda confirmada si:

- aporta detall real repetible;
- no penalitza cadència crítica;
- conserva color/halos millors;
- el guany sobre A7III/AP sobreviu al processament.

Si no, es torna a la combinació provada A7III/AP.

## Fase 1B — Sol baix

Repetir el test A/B a una altura solar semblant a la totalitat prevista.

Mesurar:

- extinció relativa;
- gradient de cel per canal;
- desplaçament R/G/B;
- FWHM per canal;
- seeing;
- SNR de fons;
- diferència stock/modificada;
- focus tèrmic.

Objectiu:

- saber si els 42,4 MP aporten mostreig útil;
- saber si la modificada empitjora el fons vermell a 300 mm;
- ajustar el ladder sense dependre d'una estimació genèrica.

## Fase 2 — linealitat i RAW

Per cada cos:

- ISO candidat;
- RAW sense comprimir;
- RAW comprimit només com a referència de caracterització, no com a
  candidat de producció;
- mecànic;
- EFCS;
- silenciós;
- simple;
- continu/bracket.

Mesurar:

- bits efectius;
- black/white level;
- senyal/temps;
- clipping per canal;
- banding;
- soroll;
- temperatura;
- efecte de Long Exposure NR, que ha de quedar desactivat.

### Test de referència ja superat

Ja s'ha confirmat que:

- és una pressió virtual;
- no activa exposició BULB real;
- cada ARW sense comprimir conserva 14 bits;
- EXIF i estructura RAW són coherents;
- no hi ha frame addicional en deixar anar;
- el release sempre arriba.

El Gate nou ha de reproduir el mateix resultat per Multi Terminal i, si és
viable, per Bluetooth, amb la càmera fora de PC Remote.

## Fase 3 — bràqueting i búfer

Per cos:

1. 3×5 frames a 3 EV amb tres bases.
2. un únic 5×3 repetit com a baseline.
3. 2×5 només si aporta una degradació útil.
4. pressió física Multi Terminal.
5. `Recall Custom hold` manual i després automatitzat.

Mode principal:

- RAW;
- sense comprimir;
- card-only;
- Slot 1 UHS-II;
- Standard;
- cap JPEG ni duplicació.

`PC+Camera` i JPEG Only al PC es mesuren només com a fallback separat.

Mesurar:

- recompte;
- ordre;
- exposició real;
- latència inicial;
- interval;
- durada de grup;
- temps de buidatge cap a SD;
- ocupació de búfer;
- supervivència a targeta;
- bytes d'imatge al Mac, que han de ser zero;
- errors.

### Volum

- mínim 100 cicles per configuració finalista;
- preferible 500 cicles per arquitectura escollida;
- càmeres soles i simultànies.

### Acceptació

- zero pèrdues;
- zero duplicats;
- zero velocitats incorrectes no detectades;
- cap bloqueig;
- recovery determinista;
- marge de temps abans de C3.

## Fase 4 — contactes

Separar del test HDR.

Provar:

- Lo/Mid/Hi;
- mecànic/EFCS/silenciós;
- RAW sense comprimir;
- diverses durades de ràfega;
- exposicions curtes candidates;
- marge de búfer abans de l'HDR;
- pas de contactes a totalitat;
- pas de totalitat a C3.

Mesurar:

- frames útils;
- clipping;
- rolling shutter;
- vibració;
- búfer;
- temps de canvi de mode;
- risc de quedar bloquejat.

Regla d'acceptació:

- un cos sempre lliure d'exposicions llargues a C2/C3;
- l'HDR no pot retardar la ràfega crítica.

## Fase 5 — fallades provocades

Durant un cicle:

- matar el supervisor;
- desconnectar el Mac del controlador;
- perdre BLE;
- deixar C1/AF-ON o shutter premut i exigir release del watchdog;
- targeta lenta;
- targeta gairebé plena;
- ordinador amb càrrega;
- càmera calenta;
- alimentació externa interrompuda;
- release remot que falla.

Comprovar:

- quins RAW sobreviuen;
- si el trigger físic continua disponible;
- temps de recuperació;
- si l'error queda al log;
- si el sistema degrada sense fer malbé l'altra càmera.

## Fase 6 — assaig temporal complet

Simular:

- parcialitat;
- compte enrere;
- C2;
- totalitat amb durada real;
- C3;
- postcontacte.

Els temps de C2/C3 han d'entrar des d'una única font de circumstàncies locals, amb la convenció de limbe documentada. El test ha d'incloure un error de rellotge i la resposta prevista.

Fer-ho:

- amb tot el maquinari;
- a temperatura alta;
- amb targetes parcialment ocupades;
- sense intervenció humana;
- després, amb una incidència planificada;
- almenys tres vegades en dies diferents.

Comparar:

- pla teòric;
- log;
- EXIF;
- fitxers reals;
- búfer;
- temps de marge.

## Fase 7 — calibracions

Provar abans del viatge:

- protocol de flats;
- repetició de focus;
- rotació del difusor;
- darks exactes;
- temperatura;
- desactivació de neteja de sensor;
- mapa de pols;
- ghosts;
- reflexos.

Decidir què és viable el dia de l'eclipsi sense posar en risc les dades.

## Fase 8 — pipeline amb 2024

Abans d'usar dades noves:

- manifest dels RAW 2024;
- calibratge de mostra;
- registre IPC;
- HDR lineal;
- mapes de pes;
- MGN;
- NRGF;
- FNRGF;
- WOW;
- RHEF;
- comparació visual i d'artefactes.

Objectiu:

- validar que la nostra cadena extreu més informació sense inventar-ne;
- determinar quins calibratges absents de 2024 limiten;
- establir QA.

## Fase 9 — congelació

Quan el sistema superi les proves:

- congelar versions;
- hash de scripts;
- configuracions exportades;
- checklist;
- còpia offline;
- pla manual;
- assignació física de ports;
- etiquetes;
- assaig final sense canvis.

No actualitzar firmware, gphoto2, sistema operatiu o targetes després de congelar, excepte problema greu i nova validació completa.

## Prioritat de les cinc proves més informatives

1. **Gate 9A card-only:** Multi Terminal, RAW sense comprimir i simulació
   dual de 90 s amb la SD definitiva.
2. **Gate 9B manual:** `Recall Custom hold` amb RMT-P1BT, C1/AF-ON i escala
   física de quinze velocitats.
3. **Gate 9B automatitzat:** un cos BLE + un cos Multi Terminal, mort del
   Mac, interferència, pèrdua BLE i release del watchdog.
4. **A/B A7RIIIA versus A7III modificada a l'AP**, incloent focus per canal
   i clipping.
5. **Transició C2 → HDR → C3 a durada real**, amb marge mesurat.

## Decisions i evidència necessària

| Decisió | Evidència |
|---|---|
| A7RIIIA o A7III a l'AP | A/B òptic + cadència + color |
| 300 o 200 mm | resolució, camp, tracking i ghosts |
| Multi Terminal o BLE | Gate 9, jitter, fallades i release |
| un 5×3 o tres bases | cobertura HDR, repeticions i 90 s |
| SD definitiva | flux sostingut, llum d'accés i marge del 25% |
| fallback gphoto | Gate 8 només si card-only no és viable |
| Canon sí/no | valor redundant versus complexitat |
| patró HDR | cobertura, temps i repeticions |
| obturador | vibració, bandes i rolling shutter |

La decisió `un 5×3 o tres bases` té una regla mínima: el bracket simple
només guanya si cada zona radial necessària conserva dues exposicions útils
per canal, solapament radiomètric i registre estable a través dels salts de
3 EV. Si falla, cal l'escala d'1 EV o una estratègia híbrida.

## Condició de consens

No cal que un mètode sigui el més ràpid al laboratori. Ha de ser el més ràpid que:

- manté marge temporal;
- conserva els RAW;
- registra els errors;
- no compromet l'altra cadena;
- ha sobreviscut a fallades provocades.
