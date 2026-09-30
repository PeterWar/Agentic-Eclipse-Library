# Contrast independent — arquitectura de control de camp per a l'eclipsi de 2026

Data de consulta: 26 de juliol de 2026

## Rol

Actua com a revisor independent de sistemes de captura fotogràfica de missió
única. No assumeixis que més precisió electrònica implica un sistema millor.
Prioritza la probabilitat real d'obtenir una seqüència completa en un camp,
amb muntatge o desmuntatge ràpid per meteorologia.

Separa sempre:

- fets proporcionats;
- inferències;
- dades que cal mesurar;
- afirmacions de fabricant que caldria verificar.

No inventis compatibilitats, exactituds de rellotge ni prestacions de búfer.

## Objectiu

Escollir una arquitectura principal i una còpia de seguretat per governar dues
Sony durant l'eclipsi total del 12 d'agost de 2026, amb uns tretze dies
operatius de marge.

Sistemes:

- Sony A7RIIIA no modificada + AP130GTX/QUADCC, aproximadament 585 mm;
- Sony A7III astromodificada + Sony FE 300 mm f/2,8 GM;
- totalitat representativa de només 88–91 segons;
- possibilitat real de canviar d'emplaçament i muntar de pressa.

Requisits no negociables:

- RAW sense comprimir;
- una SD UHS-II qualificada al Slot 1 de cada cos;
- imatges només a la SD durant la finestra crítica;
- funcionament sense Internet;
- cap muntatge de plaques, fils soldats o connectors improvisats al camp;
- màxim pràctic: una unitat comercial acabada i un cable curt per càmera;
- el fotògraf no ha d'estar gestionant ordinadors durant C2–C3.

## Evidència pròpia disponible

1. El 2024, l'A7III controlada per scripts gphoto va deixar buits de 30 s i
   125 s. Els scripts obrien processos nous, no verificaven bé retorns ni
   estat, i barrejaven control i transferència.
2. El 2026 s'ha reproduït físicament que una pulsació sostinguda pot completar
   un bracket nadiu de cinc RAW `5 × 3 EV` en tots dos cossos.
3. A l'A7III, base `1/125 s`, el bracket cobreix aproximadament
   `1/8000, 1/1000, 1/125, 1/15 i 1/2 s`.
4. Els RAW continuen sent de 14 bits en silent shooting i sense compressió.
5. En PC Remote, aquestes Sony només ofereixen `PC Only` o `PC+Camera`, no
   `Camera Only`.
6. En el backend Sony de libgphoto2, `wait-event` pot recuperar el payload
   complet per USB abans de publicar l'esdeveniment. No descarregar a disc no
   equival a no transferir.
7. Una ordre PTP de configuració ja ha trigat 25,759 s al laboratori.
8. El BLE experimental des del Mac no ha pogut completar autenticació i queda
   retirat.
9. El Sony Camera Remote SDK actual no admet A7III ni A7RIIIA.
10. L'exactitud fotogràfica no és només el rellotge: hi ha retard del
    disparador, latència/jitter del cos i incertesa física del contacte.
11. NASA indica que NMEA pot tenir dècimes de segon de retard i que, per a
    cronometria científica de contactes, cal 1PPS. Amb perfil lunar Kaguya/LRO,
    la predicció del contacte queda aproximadament al nivell de 0,2 s.
12. El projecte pot protegir el resultat amb captura densa abans i després de
    C2/C3, en lloc de confiar en una sola fotografia exacta.

## Opcions a contrastar

### A. LRTimelapse PRO Timer 3.5

Fets proporcionats pel fabricant:

- producte comercial acabat;
- bateria interna i rellotge RTC;
- inici programable per data/hora;
- dos ports de càmera de 2,5 mm que disparen en paral·lel;
- intervals configurables des d'aproximadament 0,3 s;
- dos cables `2,5 mm TRS → Sony Multiport RM-SPR1/S8`;
- no canvia ISO ni velocitat de la càmera;
- l'exactitud UTC absoluta i la deriva de l'RTC no estan publicades;
- no és impermeable.

### B. Hähnel Captur Timer per Sony + dos receptors

Fets proporcionats pel fabricant:

- temporitzador comercial per ràdio 2,4 GHz;
- compatible amb A7III/A7RIII;
- un receptor i un cable curt per càmera;
- receptors addicionals per disparar diverses càmeres;
- delay, burst/hold, dos intervals i repeticions;
- alimentació amb piles AA;
- no incorpora GNSS ni hora UTC absoluta;
- elimina el cable entre muntures, però introdueix ràdio, pairing, més piles i
  un punt de fallada compartit.

### C. Dos JJC TM-F2 cablejats

- un intervalòmetre comercial i un cable per rig;
- delay, interval i nombre de captures;
- alimentació 2 × AAA;
- sense ràdio ni ordinador;
- els dos temporitzadors no comparteixen rellotge ni botó de start.

### D. Mac + gphoto2 + dos USB

- permet taules arbitràries i canvis de configuració;
- pot temporitzar les ordres amb precisió de mil·lisegons al Mac;
- obliga PC Remote, USB/PTP i potencial transferència/cua d'imatges;
- ja existeixen bloqueigs de desenes de segons;
- afegeix Mac, cables, hub/alimentació i un punt comú de fallada.

### E. Controlador propi Pico/GNSS

- podria oferir UTC/1PPS i sortides aïllades;
- amb el termini actual implicaria construir, cablejar, encapsular, alimentar i
  qualificar hardware nou;
- la proposta de plaques i mòduls visibles al camp ha estat rebutjada per
  fragilitat operativa;
- només seria reconsiderable com una única caixa segellada i acabada, no com a
  prototip de camp.

### F. Interval intern de les Sony

- zero cables i RAW directament a SD;
- interval mínim aproximat d'1 s;
- la compatibilitat real amb el bracket continu `5 × 3 EV` no està demostrada
  i s'ha de provar, no assumir.

## Preguntes

1. Ordena les opcions per a ruta principal i fallback. Dona una sola
   recomanació final, no una llista evasiva.
2. Canvia la decisió si les dues muntures estan juntes o separades 1–3 metres?
3. És fotogràficament millor sincronitzar exactament els dos cossos o
   desfasar-los deliberadament per augmentar el mostreig temporal?
4. Com obtindries alineació suficient amb C2/C3 sense fabricar un receptor
   GNSS? Distingir metrologia científica de captura fotogràfica robusta.
5. Defineix un gate de 48 hores, amb proves que puguin falsar la teva opció
   preferida: pols/hold, bracket complet, cadència, RAW esperats, fallada de
   cable/ràdio, rellotge i tres seqüències completes de 90–120 s.
6. Quina és la compra mínima immediata? Què no compraries?
7. Identifica el risc ocult més probable de la teva pròpia recomanació.

## Format de resposta

- Veredicte executiu.
- Rànquing amb justificació.
- Arquitectura de camp en cinc línies.
- Estratègia temporal C2/C3.
- Gate de 48 hores amb criteris PASS/FAIL.
- Compra mínima i pla B.
- Risc que podria fer-te canviar d'opinió.
- Confiança de 0 a 100.

Màxim aproximat: 1.500 paraules.
