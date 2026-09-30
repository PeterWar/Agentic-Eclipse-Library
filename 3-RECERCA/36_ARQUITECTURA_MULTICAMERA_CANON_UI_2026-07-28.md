# Arquitectura futura: dues Sony, Canon i interfície

Data: 28-07-2026  
Abast: disseny preparatori; **cap backend Canon ni interfície implementats**  
Prioritat actual: no alterar el candidat A7III + AP130 que ha passat 3/3

> **Actualització 29-07-2026 — implementació v0.5.0.** El backend Canon, el
> supervisor de missió i la interfície de tres canals ja estan implementats.
> Queden superades les referències inferiors a una barrera global `all READY`,
> a `ARM/ARMED` i a una confirmació escrita: la política vigent és
> `degraded_continue`. Un únic `START MISSION` llança una vegada cada càmera
> habilitada; espera `PTP_READY` o un timeout acotat només per serialitzar
> l'obertura PTP, i continua amb el cos següent encara que l'anterior quedi
> degradat. La identitat física incorrecta o un trigger ambigu continuen sent
> hard stops del cos afectat, mai una cancel·lació automàtica dels altres.
> A7III i Canon comparteixen C2/C3; l'A7RIIIA usa `start-at=C2` per al programa
> candidat de cinc RAW. Els tres processos converteixen els mateixos literals
> UTC a monotònic de manera independent; encara no existeix una època
> monotònica única injectada pel supervisor.
>
> **Actualització 29-07-2026 — recuperació A7RIIIA v0.5.1.** Una enumeració
> física real després de canviar bateria va mostrar la sèrie USB
> `[SÈRIE]` com a classe 8 Mass Storage, mentre A7III i Canon continuaven
> en classe 6/PTP. La GUI i el controlador ara ho distingeixen abans d'obrir
> cap shell, eliminen l'etiqueta Canon fantasma del mateix port, indiquen
> esperar el final de l'activitat de targeta, desconnectar USB, posar
> `Network > Ctrl w/ Smartphone > Off` i `Setup > USB Connection > PC Remote`,
> i vigilen la reenumeració. No hi ha cap ordre suportada per convertir Mass
> Storage a PTP des del Mac: el canvi és físic al menú, i la política
> `degraded_continue` manté els altres canals.
>
> **Actualització 29-07-2026 — routing dinàmic i autoreparació v0.5.2.** El
> port `usb:BUS,DEVICE` és ara només una ubicació efímera. Cada escaneig uneix
> `gphoto2`, dispositiu USB i interfície class-6, assigna el perfil per sèrie
> USB exacta —o producte únic en el cas Canon— i normalitza etiquetes de model
> intercanviades. La GUI comprova i aplica només reparacions declarades segures
> a tots els cossos PTP habilitats, d'un en un per preservar la propietat de la
> sessió, i `START` posa primer els canals ja disponibles. El manifest congela
> `role_id -> body_id` però obliga a redescobrir el port. L'òptica, filtre,
> focus i apuntat no es poden inferir per USB i continuen sent assignacions
> físiques; Mass Storage continua requerint el canvi manual a PC Remote. Si
> IORegistry veu el cos exacte en classe 6 però `gphoto2` encara no l'enumera,
> el canal passa a `PTP RECOVERY`: es prova el port resolt per identitat i la
> sèrie/model PTP continuen sent un hard check previ a qualsevol mutació.

## Decisió d'arquitectura

El controlador temporal no s'ha de convertir en una aplicació monolítica que
parli amb totes les càmeres des d'un sol shell. La unitat fiable ha de continuar
sent:

> un procés de captura + una sessió PTP persistent + un cos identificat per
> model i sèrie + un perfil immutable + un directori de run independent.

Per controlar dos o més cossos, un **supervisor offline** prepara una única
època temporal monotònica i arrenca un worker per càmera. La interfície, si
s'afegeix, només governa el supervisor; no executa el bucle de temps crític.

```text
Interfície opcional
        │
        ▼
Supervisor offline ─── compilació, barrera READY, armament, manifest global
        │
        ├── Worker A ── gphoto2 persistent ── A7III + AP130
        ├── Worker B ── gphoto2 persistent ── A7RIIIA + 300 mm
        └── Worker C ── backend Canon ─────── 6D o R6 Mark II
```

El supervisor no envia cada disparador en directe. Calcula una vegada la relació
UTC→monotònic, entrega a cada worker el mateix origen i espera una barrera
`READY`. A partir de l'armament, cada worker espera localment els seus targets.
Això evita que una cua o setter lent d'una càmera retardi l'altra.

## Contracte del supervisor

Abans d'armar:

1. resol cada cos per `model + serial`; mai conserva com a identitat un
   `usb:BUS,DEVICE` volàtil;
2. adquireix un lock independent per cos;
3. obre i verifica totes les sessions PTP;
4. executa el preflight propi de cada backend;
5. compila tots els perfils amb els mateixos C2/C3;
6. compara l'època monotònica dels workers i imposa una barrera de preparació;
7. escriu un manifest global amb hashes, rols, cossos, ports resolts,
   cronologies i política de fallada;
8. només arma si tots els canals obligatoris responen `READY`.

Durant la totalitat, un error d'un worker **no cancel·la l'altre per defecte**.
La política segura és `degraded_continue`: el cos sa continua la seva
cronologia i el cos fallit deixa de disparar si el seu estat físic és ambigu.
Un `abort_all` només ha de ser una decisió explícita per a proves, no el
comportament automàtic de camp.

Després, el supervisor recull els `result.json` independents i crea un resum
global. Mai ha de convertir l'èxit d'una càmera en prova de l'altra.

## Sincronització de les dues Sony

Ja s'ha demostrat una captura dual A7III+A7RIIIA amb un target compartit i una
diferència inferida de 2,361 ms. Això prova viabilitat, però no qualifica encara
la cronologia doble definitiva.

Per al gate de producció cal:

- dos processos, dues sessions persistents i dos locks;
- ports USB directes i, si el Mac comparteix controlador intern, comprovar la
  topologia amb càrrega real;
- cap RAW científic travessant USB durant la seqüència;
- perfils diferents: l'A7III+AP130 no s'ha de deformar per adaptar-se a
  l'A7RIIIA+300 mm;
- tres runs complets simultanis del cas curt;
- mesurar lateness per cos i diferència física entre triggers equivalents;
- injecció d'una fallada en un worker i demostració que l'altre continua;
- manifests SD separats i verificació RAW independent.

La precisió crítica és respecte de C2/C3, no que totes dues càmeres disparin
sempre el mateix patró. Poden compartir anchors i tenir cronologies diferents.

## Backend A7RIIIA

L'A7RIIIA no ha d'heretar literalment els índexs PTP, pressupostos ni
`capturemode` de l'A7III. El seu backend s'ha de descobrir i qualificar amb el
cos físic:

- model i sèrie;
- propietats PTP i valors literals;
- ruta `PC+Camera` i JPEG-only al PC;
- RAW sense comprimir a SD;
- mida del JPEG de telemetria;
- brackets nadius disponibles;
- latència dels setters, desbloqueig de `capturemode` i drenatges;
- restauració i recuperació de sessió.

La seqüència de l'A7RIIIA+300 mm s'ha de dissenyar després de decidir la seva
funció fotogràfica —corona més ampla, redundància de contactes o una escala
d'exposicions diferent—, no copiant el guió AP130.

## Backends Canon 6D i R6 Mark II

La portabilitat de gphoto2 s'ha de fer mitjançant un adapter, no amb condicionals
Sony escampats pel controlador. La part reutilitzable és:

- planificador monotònic;
- perfils JSON i auditoria de solapaments;
- armat explícit, deadlines i política sense *catch-up*;
- locks, logs JSONL, manifests i hashes;
- postflight d'Exif i recompte;
- cleanup i restauració per etapes.

La part que cada Canon ha de descobrir físicament inclou:

- `capturetarget` real i si `card` evita qualsevol payload RAW per USB;
- noms i valors de dial, ISO, shutter, format RAW i bràqueting;
- nombre real de fotos AEB i ordre;
- persistència a cada slot;
- comportament d'EFCS/electrònic amb les exposicions llargues necessàries;
- cadència, buffer, temperatura i targeta final;
- què passa si el cable USB es perd;
- integritat CR2/CR3 i correspondència amb la telemetria.

Que gphoto2 documenti `capturetarget=card` per a una Canon no és qualificació
de camp. La 6D i la R6 Mark II necessiten gates separats; tampoc es pot assumir
que la R6 Mark II es comporti com una R6.

## Interfície: què ha de fer i què no

La interfície ha de ser una capa local, offline i prescindible. El CLI ha de
continuar sent la font de veritat i poder executar tots els assajos sense GUI.

Pantalla mínima:

- llista de cossos amb model, sèrie, rol, port viu i bateria;
- checklist manual en el mateix ordre físic del menú de cada càmera;
- valors C2/C3, durada i cronologia compilada;
- estat `DISCONNECTED / PREFLIGHT / READY / ARMED / RUNNING / DEGRADED /
  COMPLETE / FAILED`;
- discrepàncies amb instrucció manual exacta;
- recompte previst i rebut per canal;
- botó d'armament amb confirmació forta;
- `ABORT BODY` separat d'`ABORT ALL`;
- directori de resultats i resum postflight.

La GUI no ha de:

- mantenir la sessió PTP;
- dormir fins als targets ni enviar triggers;
- modificar un perfil durant un run;
- dependre d'Internet;
- ocultar logs o permetre ignorar gates;
- tancar-se i arrossegar amb ella els workers armats.

Una interfície web local pot ser pràctica, però el servidor i els workers han de
viure en processos separats. Tancar la pestanya no pot aturar la captura.

## Ordre d'implementació

1. **Congelar A7III+AP130:** gate SD amb els 55 ARW, fallades i assaig òptic.
2. **Extraure la interfície de backend:** sense canviar la cronologia ni el
   comportament validat de Sony.
3. **Qualificar A7RIIIA sola** amb el seu perfil i la seva targeta.
4. **Construir el supervisor CLI** i demostrar aïllament i sincronització dual.
5. **Executar tres cronologies dobles del cas curt** i una injecció de fallada.
6. **Afegir Canon 6D** només quan hi hagi el cos físic; repetir el gate per a la
   R6 Mark II si s'incorpora.
7. **Afegir la interfície al final**, consumint exclusivament l'API estable del
   supervisor.

Aquest ordre protegeix la inversió més valuosa: el camí A7III+AP130 ja provat
no queda supeditat a una segona càmera, a un backend encara desconegut ni a una
GUI nova.
