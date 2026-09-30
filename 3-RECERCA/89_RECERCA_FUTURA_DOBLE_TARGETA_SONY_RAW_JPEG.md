# Recerca futura — dues targetes Sony: RAW i JPEG separats

Data d'obertura: 22 d'agost de 2026  
Estat: **PREGUNTA OBERTA; NO IMPLEMENTAT; NO QUALIFICAT**

## Pregunta

Cal comprovar experimentalment si una Sony amb dues targetes pot sostenir una
cadència més alta quan grava els **RAW en una targeta i els JPEG en l'altra**,
en comptes d'escriure tots dos formats a la mateixa targeta.

Aquesta és una línia de recerca futura d'**Eclipse Command**. No canvia la
configuració, els perfils ni la baseline V1.02 actuals, i no autoritza cap
prova física sense una ordre nova de Pere.

## Punt de partida i incertesa

- Als **A7III i A7RIIIA** del projecte només l'**Slot 1 és UHS-II**; l'Slot 2
  és UHS-I (`research/14` i `research/16`). La recomanació històrica és una
  sola UHS-II a l'Slot 1, `Recording Mode = Standard`, sense duplicació.
- No hi ha una mesura específica que compari, amb el mateix cos, targetes i
  coreografia, **RAW+JPEG a l'Slot 1** contra **RAW a l'Slot 1 i JPEG a
  l'Slot 2**.
- Per tant, no s'ha de donar per fet que dues targetes dupliquen el cabal. El
  resultat pot millorar, quedar igual o empitjorar si el pipeline intern és
  compartit, si les escriptures són seriades o si l'Slot 2 UHS-I esdevé el
  coll d'ampolla.
- En el camí Sony actual `PC+Camera`, el JPEG de telemetria també es transfereix
  al Mac. Separar les targetes no elimina necessàriament la cua ni el cost de
  drenatge PTP observats per Eclipse Command.

## Gate experimental futur

Fer una comparació A/B/C **body-specific** i repetir-la per separat a cada
model Sony que es vulgui suportar:

1. A — RAW+JPEG a l'Slot 1, configuració de referència.
2. B — RAW a l'Slot 1 i JPEG a l'Slot 2, si el menú del cos ho permet.
3. C — RAW només a l'Slot 1, control del màxim rendiment de targeta; no és una
   substitució automàtica del JPEG de telemetria d'Eclipse Command.

Condicions que s'han de mantenir idèntiques: cos, firmware, mode d'obturador,
tipus i compressió RAW, mida/qualitat JPEG, coreografia, temperatura, estat de
bateria, capacitat lliure i targetes concretes. Cal fer repeticions en ordre
alternat, després d'un estat inicial conegut, i no extrapolar entre A7III,
A7RIIIA o futurs cossos amb dos slots ràpids.

Mesures mínimes:

- captures demanades, confirmades i presents a les targetes, sense silencis;
- temps per ràfega, cadència sostinguda i temps fins que el búfer queda buit;
- màxim i p95 de drenatge del JPEG al Mac, cua observada i Busy/timeouts;
- manifests pre/post separats per targeta, correspondència 1:1 RAW/JPEG,
  integritat ARW, EXIF i hashes;
- comportament quan una targeta és més lenta, s'omple o falla, sense replay
  ambigu i sense comprometre l'altra càmera.

## Criteri de decisió

Només promoure el mode de dues targetes si B aporta una millora repetible del
pitjor cas i de la cadència sostinguda, sense pèrdues, divergències, més temps
de drenatge PTP ni una recuperació més fràgil. Si només millora la mitjana però
empitjora el màxim o introdueix dependència de l'Slot 2 UHS-I, es manté la
configuració d'una sola UHS-II.

Si algun dia s'incorpora a Eclipse Command, ha de ser una configuració
preflight qualificada per cos i targetes, mai un canvi de slot durant la
missió ni un nou prerequisit global de `Start mission`.

