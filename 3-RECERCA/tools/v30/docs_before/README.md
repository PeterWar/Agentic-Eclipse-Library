# Eclipse Command

Aplicació local i offline per coordinar quatre càmeres durant l’eclipsi total
del 12 d’agost de 2026. La GUI prepara una cronologia C1–C4 i executa un
worker PTP independent per cos; cap IA participa en la captura.

## Principis

1. **Mission first:** un problema en una càmera no atura les altres, UNA
   CAMERA DEGRADADA s'ha d'intentar seguir utilitzant per la missió, costi el
   que costi. Això obliga a esgotar les continuacions segures, però mai a
   repetir un trigger ambigu ni a continuar amb identitat/propietat divergent,
   estat físic desconegut després d’un write o un ledger no garantible;
   aquests límits aturen només el canal afectat.
2. **Simplicitat:** l’operador veu què passarà i rep només instruccions útils.
3. **Agentic AI abans de la missió:** els agents poden mesurar i optimitzar
   perfils, però el run és determinista, local i auditable.

Un resultat de captura ambigu consumeix només aquella acció: no es repeteix,
però el mateix cos conserva les accions futures si continua identificat,
controlat i operatiu. Una incidència d'un cos no atura els altres.

ISO 100 és el baseline recomanat per a les Sony. La Canon 6D usa ISO 1600 com
a baseline de disseny per desplaçar la seva finestra AEB nativa de 6 EV cap a
la corona feble: no pot fer un canvi ràpid de 9 EV només amb bràqueting. En
tots els cossos l’ISO és propietat de l’operador i sempre advisory; cap valor
—inclòs Auto, 0 o desconegut— pot donar `FAILED` ni cancel·lar una missió.
El candidat privat V1.02 (`1.0.2`) mostra `ISO 100`, `ISO 200` i `ISO 400` al
footer. Només un clic explícit de l’operador autoritza el write preflight a
cada cos PTP suportat i identificat exactament; cada intent exigeix readback i
acaba literalment `SET` o `NOT SET`. Els botons queden deshabilitats mentre hi
ha missió, scan, Sync UTC o una altra operació de càmera. No són prerequisit
de `Start mission`, no s’usen durant el run i cap resultat ISO degrada altres
canals. La release pública 0.8.0 continua immutable i sense aquests botons.

Durant les fases parcials, els quatre canals afegeixen una captura documental
per minut entre C1 i C2−30 s i entre C3+30 s i la finestra quieta de C4. Els
cores de contactes i totalitat continuen sent específics de cada cos. En Canon
amb AEB natiu, una captura significa un únic press AEB3 i tres RAW esperats.

## Versió actual

[Eclipse Command.app](gui/dist/Eclipse%20Command.app) és el candidat privat
local **V1.02**. La release pública vigent continua sent la 0.8.0.

El projecte és ara en fase **post-eclipsi**. La V1.02 és una baseline de
captura congelada, no una cua de desenvolupament activa. El run operatiu
canònic del 12 d'agost és `20260812T202219_multi_camera_mission_run`; el
veredicte, la reconciliació de ledgers i l'annex foto a foto són a
[l'informe auditat del run real](output/pdf/Informe_auditat_run_Eclipse_Command_20260812T202219.pdf).
La represa viva i els pendents demostrats són al
[traspàs viu d'alternança Codex ↔ Claude](.coordination/HANDOFF_2026-08-22_ALTERNANCA_CODEX_CLAUDE.md).

La **V1.00** hi va portar les **escales d'exposició noves dels tres cossos**:
els dos Sony passen els contactes a base **1/800** i el mig de la totalitat es
converteix en una **muntanya** 1/4 → 1 s → 1/4 amb nou esglaons i 2,00 EV de
salt màxim, i la R6 passa les finestres de contacte a **1/3200**, les allarga
fins a **C2−20** i **C3+20** i canvia el fotograma de 15 s per un **bloc fosc
de 2 s ×3 i 10,3 s ×3 al mig de la totalitat**. El TEST RUN passa a durar
**1 min 31 s**, que és el terra de planificació.

La **V1.01** no toca cap geometria, cap exposició ni cap cadència: corregeix
els **set defectes d'operador** que Pere va reportar —quatre dels quals eren
la mateixa fallada, el dial de mode de la R6 a **B**, que ara es reconeix i es
diu pel seu nom en lloc de reintentar-se quatre minuts— i hi afegeix dues
features: la versió al costat del nom a la capçalera i el trasllat de la
descripció del programa a la cel·la de càmera.

La **V1.02** treu aquella descripció gegant del hover: la fila i el selector
mostren només `A7III · f/2.8`, `6D · f/5.5`, `A7RIIIA · f/2.8` i
`R6 III · f/5.5`, mentre el tooltip conserva un resum curt i la identitat
PTP/USB exacta. Afegeix avisos de veu a C2−5 min, −2 min i −1 min, i a
C4−1 min. A la R6, el setter d'aproximació comença a **C2−15,00** i el primer
fotograma a **C2−14,75**: desapareixen exactament vuit `1/3200` del prefix i
tot el programa des de C2−5,65 fins a C4 queda idèntic a la V1.01.

✅ **Abans del dia 12, l'escala ja havia volat en proves.** Set TEST RUN pel binari del bundle el 9
d'agost a la nit, tots amb totalitat de 91,0 s: el de flota amb els tres
cossos alhora (`20260809T233027`) fa **198 fotos, zero degradades i zero
exposicions divergents**, i el darrer (`20260809T234629`, A7RIIIA i R6) en fa
**163 de 163** amb retard màxim 1,473 ms i cap `mission_warning`. Volable no
vol dir qualificat: òptica, RAW i seguiment continuen sent gates oberts.
Informes: [QA V1.02](gui/QA_REPORT_1.0.2_2026-08-10.md),
[QA V1.01](gui/QA_REPORT_1.0.1_2026-08-10.md),
[QA V1.00](gui/QA_REPORT_1.0.0_2026-08-10.md),
[QA 0.9.4](gui/QA_REPORT_0.9.4_2026-08-09.md) i
[QA 0.9.3](gui/QA_REPORT_0.9.3_2026-08-09.md).

⚠️ **Lliçó de qualificació conservada:** amb la CFexpress de la R6 plena, la
finestra de contacte de C3 perdia un fotograma de cada tres; formatar-la de
fresc ho recuperava del tot. És evidència pre-eclipsi, no una instrucció de
represa post-eclipsi.

- executable SHA-256:
  `61227d418ec7a74a6fa11c934970d85218466ffd067754ec68efbc3334ba9f4f`;
- manifest de 51 fonts SHA-256:
  `d06de97146e521afeb1871c3cfd06c5944faf3c40dbd96898f53c30d734a2f6a`, i els
  51 inputs incrustats tenen el mateix SHA que la font viva;
- **Sony A7RIIIA:** base de contacte 1/800, sempre tres àncores d'earthshine
  1/8 · 1 · 8 s i de zero a tres tríades de corona a base 1/4 segons la
  durada. L'A7III usa la seva pròpia cua i ordre de ràfega; cap timing no
  s'hereta entre cossos.
- **R6 III:** una foto per exposició, Drive `Single`, AEB `off`, contactes a
  1/3200, escales A/B completes i bloc fosc 2 s ×3 + 10,3 s ×3. El cue de
  filtre continua a C2−20 i dona cinc segons abans del setter C2−15.
- A 91 s, la R6 V1.02 espera **109 captures de nucli + cinc documentals =
  114**, contra 117+5 a la V1.01. Totalitat 55, parcials posteriors 34,
  setters 29 i tota la geometria no eliminada són invariants.
- El trigger R6 continua sent `Press Full MF` → `Release`; un trigger ambigu
  es consumeix i no es repeteix. Un setter només admet un reintent davant un
  rebuig net que provi que el valor no s'ha adoptat.
- `Check cameras now` convergeix ajustos abans d’armar i no captura. ISO,
  checklist i deute de qualificació són advisory i mai un gate de
  `Start mission`.
- En Canon `card_only`, zero descàrregues locals és N/A: un ledger complet i
  net pot donar `COMPLETE`, però CR2/CR3 continua pendent del manifest
  exclusiu.

El bundle és arm64, ad-hoc i no notaritzat. Inclou Python i Qt, però necessita
`gphoto2` al Mac. Si macOS el bloqueja la primera vegada, obre’l explícitament
des de Finder o Configuració del Sistema.

## Instal·lació pública

El repositori públic és
[PeterWar/Eclipse-Command](https://github.com/PeterWar/Eclipse-Command).
En un Mac Apple silicon amb Homebrew:

```bash
brew install gphoto2 python@3.12
git clone https://github.com/PeterWar/Eclipse-Command.git
cd Eclipse-Command
python3.12 -m venv gui/.venv312
gui/.venv312/bin/python -m pip install -r gui/requirements.txt
```

Abans d’adaptar una càmera, un agent ha de llegir sencers `AGENTS.md`,
`CLAUDE.md` i `PROTOCOL_UNIVERSAL_ALTA_CAMERA_LLM.md`. Canon, Sony i Nikon no
comparteixen automàticament timings, opcions PTP, brackets ni límits de buffer.
Nikon és una ruta d’adaptació prevista, no compatibilitat demostrada.

El backend públic és exclusivament `gphoto2`/libgphoto2. EDSDK, els seus
headers, frameworks, binaris, llicències i el backend privat R6 no formen part
del repositori ni del bundle públic.

## Beta i seguretat

Eclipse Command és programari beta i s'ha d'assajar de principi a fi amb cada
cos, firmware, cable, targeta i tren òptic exactes abans de l'eclipsi. No
substitueix un filtre solar certificat, la verificació de focus ni la decisió
de l'operador. La llicència MIT el proporciona tal com és, sense garantia.
L'evidència Canon i Sony del projecte és body-specific; Nikon continua sense
prova física i requereix backend, perfil, manifest RAW i qualificació propis.

## Resultat físic històric de referència

El TEST RUN complet de 98,8 s es va executar amb el bundle 0.7.2. L’A7III
encara usava l’AP130 i la Canon estava a ISO 100; és evidència del scheduler i
d’aquells contractes, no una qualificació física del 300GM o d’ISO 1600:

| Càmera | Captures confirmades | Comportament rellevant |
|---|---:|---|
| Sony A7III | 60/60 JPEG | primera a C1; última a C4−8 s |
| Sony A7RIIIA | 83/83 JPEG; 72 en totalitat | dues exposicions de 3,2 s; bracket final a C3−3,1 s |
| Canon 6D | 31 triggers; 93/93 commits esperats card-only | AEB ±3: tres RAW esperats per press; sense manifest CR2 exclusiu |

No hi va haver misses, skips, warnings de cronologia ni ràfega exactament a
C4. El run és a
`controller/runs/codex_20260802_gui_072_final/runs/20260802T140916_multi_camera_mission_run`.

Això acredita el TEST RUN, no tota la ciència final. Encara falten:

- A7III: gate SD/ARW i resiliència física propis del cos;
- A7RIIIA: delta SD ARW exclusiu i prova solar/òptica amb el 300 mm f/2,8;
- Canon 6D: manifest CR2 pre/post exclusiu, Stage B i prova solar/òptica;
- Canon R6 Mark III: els gates AEB3 G1/G5/G40 són PASS de transport acotat i
  el G40 té delta CFexpress exclusiu +120. El core materialitza 40 press,
  120 CR3 esperats i 105 durant totalitat. Un TEST RUN posterior va adoptar
  sis setters dinàmics amb readback exacte i 40/40 grups, però continua
  `card_only_committed`. Falten el gate d’endurance de la nova cadència, H90,
  tracking/VSD90SS+MF i assaig
  solar/òptic/científic; el perfil continua candidat, no producció.

Aquests deutes es mostren com a informació del programa, no com a `WARNING`.
No han de tornar a deixar la Canon 6D ni el programa acotat R6 en
`PROGRAM BLOCKED`, ni cancel·lar les altres càmeres. El checklist tampoc
genera `WARNING`: és només un recordatori editable.

## Ús d’operador

1. Connecta les càmeres. L’ordre físic dels cables USB és indiferent: el
   programa resol cada cos per identitat, no per número de port.
2. Obre l’app i introdueix C1, C2, C3 i C4 en UTC. El mode `TEST RUN` crea una
   cronologia curta, però no dispara per si sol.
3. Revisa les càmeres detectades i els warnings. Una càmera desconeguda queda
   visible com `NO PROGRAM` i no rep writes ni triggers.
4. Completa el checklist físic, especialment filtre solar, focus, bateria i
   espai a targeta. El balanç de blancs no l'has de tocar: si el cos porta
   automàtic, `Check cameras now` l'hi posa a `Daylight`. La suspensió del
   Mac tampoc: mentre hi ha un run en marxa l'app el reté despert, també amb
   bateria.
5. Ajusta manualment la ISO que vulguis a cada cos i prem `Check cameras now`.
   La release pública no escriu ISO ni converteix el seu valor en un gate.
6. Activa l’àudio si vols recordatoris de veu en anglès. Els avisos automàtics
   i el cronograma esperen `Start mission`; `Test audio` continua sent una
   prova manual explícita.
7. Si l’UTC no és `BOUNDED`, prem `Sync UTC`: comprova Internet/NTP sense
   escriure, demana autenticació nativa només si `time.apple.com` respon i
   accepta l’èxit únicament amb un bound del kernel de 400 ms o millor. Sense
   connexió no toca el rellotge ni bloqueja la missió després de l’avís.
8. Prem `Start mission`. El botó indica el nombre real de càmeres llançables i
   engega el cronograma i els avisos.
9. `Stop safely` atura cronograma i veu, conserva `STOPPED` sense tornar a
   mostrar `CONTACTS ALREADY IN PROGRESS/ELAPSED`, i demana cleanup
   independent a cada worker. Editar contactes o `TEST RUN` obre un pla nou.

La salut UTC del header és informativa per a TEST RUN. Una missió científica
absoluta pot exigir un gate UTC específic al perfil. La GUI mai assumeix que
un ACK o JPEG descarregat demostra un RAW íntegre a la targeta.

## Arquitectura

```text
gui/                         aplicació Qt, packaging i QA
controller/                  motor PTP, perfils, eines i proves
controller/profiles/         perfils de missió i de laboratori
controller/runs/             evidència física immutable
research/                    decisions, mesures i història tècnica
tests/, runs/, outputs/      datasets i evidència; no són temporals
```

Perfils operatius actuals:

- `candidate_a7m3_300gm_short_checkpointed_1x5_3x9.json`;
- `candidate_a7r3a_300gm_short_checkpointed_1x5_3x9.json`;
- `candidate_canon6d_fixed_aeb3_continuous_cardonly_v2.json`;
- `candidate_r6m3_vsd90ss_cfexpress_cardonly_v1.json`.

La Canon 6D utilitza `controller/eclipse_capture_canon_v2.py`; la R6 Mark III,
`controller/eclipse_capture_r6m3.py`; les Sony, `controller/eclipse_capture.py`.
No es transfereixen timings ni límits de buffer entre cossos.

## Desenvolupament

La font canònica és aquesta arrel, no cap worktree sota `.claude/`. Abans de
modificar res, llegeix [CLAUDE.md](CLAUDE.md) sencer i els dos fitxers de
`.coordination/`. No netegis el worktree amb ordres Git destructives.

Regressió principal:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=gui QT_QPA_PLATFORM=offscreen \
  gui/.venv312/bin/python -u -m unittest discover -s gui/tests

PYTHONDONTWRITEBYTECODE=1 \
  gui/.venv312/bin/python -m unittest discover -s controller/tests

PYTHONDONTWRITEBYTECODE=1 gui/.venv312/bin/python \
  gui/tools/qa_adaptive_timeline_fuzz.py .
```

Build i QA macOS:

```bash
gui/build_macos_portable_app.sh

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=gui QT_QPA_PLATFORM=offscreen \
  gui/.venv312/bin/python gui/tools/qa_macos_portable.py \
  "gui/dist/Eclipse Command.app"
```

Cal tenir `SERIAL_WRITES`, zero processos GUI/controller/gphoto2 propis i els
inputs congelats. Les llistes de perfils de `runtime_manifest.py`,
`EclipseCommand.spec` i `source_manifest.py` han de coincidir; una prova
específica ho verifica.

## Documentació

- [CLAUDE.md](CLAUDE.md): estat canònic, invariants i handoff per agents.
- [AGENTS.md](AGENTS.md): arrencada mínima per qualsevol agent.
- [Protocol universal](PROTOCOL_UNIVERSAL_ALTA_CAMERA_LLM.md): alta eficient
  d’una càmera nova.
- [Protocol complet](PROTOCOL_ALTA_CAMERA.md): mesures, fallades i gates.
- [Índex de QA](gui/QA_REPORTS.md): baseline actual i informes històrics.
- [Índex de recerca](research/README.md): evidència viva i documents d’arxiu.

Llicència MIT. © 2026 Pere Guerra Serra.
