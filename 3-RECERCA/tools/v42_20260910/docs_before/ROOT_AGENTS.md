# Instruccions per a agents

⛔ **02-09-2026: el projecte ja NO té git.** Per decisió de Pere, `.git` s'ha retirat (història congelada a `.coordination/git_historic_20260902/`, còpies al 4TB). Les instruccions d'aquest fitxer i de CLAUDE.md que parlen de `git status`, `reset`, `checkout`, `stash`, `commit` o «worktree» són inaplicables; tota la resta (SERIAL_WRITES amb `claim.lock`, un sol escriptor, fitxers d'estat, cap acció física sense autorització) continua vigent. La còpia de seguretat és `/Volumes/4TB` (rebut: `output/cleanup/20260902_neteja/REBUT.md`).

Abans de qualsevol mutació, llegeix `CLAUDE.md` sencer. El seu bloc inicial
és el context canònic actual; les seccions datades que segueixen conserven el
disseny i la història de captura i no poden sobreescriure l'estat post-eclipsi.
Si has d’alta una càmera nova, llegeix també `PROTOCOL_ALTA_CAMERA.md` i
`PROTOCOL_UNIVERSAL_ALTA_CAMERA_LLM.md` sencers abans de connectar-la.

## Arrencada obligatòria

1. Treballa des de `/Users/USUARI/Downloads/Eclipse 2026`; és l’única
   arrel canònica de codi.
2. Llegeix `.coordination/CLAUDE_STATUS.md` i
   `.coordination/CODEX_STATUS.md`.
3. No executis Git: el projecte no en té des del02-09-2026. Preserva tots
   els fitxers preexistents i evita sobreescriptures globals.
4. Actualitza només el teu fitxer d’estat. Claude no edita
   `CODEX_STATUS.md`; Codex no edita `CLAUDE_STATUS.md`.
5. Adquireix `SERIAL_WRITES` abans d’editar, construir, registrar l’app o
   tocar PTP. Allibera’l amb un handoff explícit i zero processos propis.

Per a qualsevol tasca post-eclipsi sobre imatges, Photoshop o actius del
Desktop, llegeix també, en aquest ordre:

1. `/Users/USUARI/Desktop/Eclipse 2026/IA/README.md`;
2. `/Users/USUARI/Desktop/Eclipse 2026/IA/ESTAT_ACTUAL.md`;
3. `/Users/USUARI/Desktop/Eclipse 2026/IA/MAPA_RUTES_I_OUTPUTS.md`.

Des del 22 d'agost hi ha dues arrels deliberades: aquest directori de Downloads
continua sent l'única arrel canònica de codi (sense Git); `/Users/USUARI/Desktop/Eclipse
2026` és l'arbre canònic d'actius fotogràfics, Photoshop i memòria d'IA. Les
rutes de Desktop conservades en rebuts anteriors poden ser històriques i no
s'han de reescriure. El mapa viu és a
`/Users/USUARI/Desktop/Eclipse 2026/IA/MAPA_RUTES_I_OUTPUTS.md`.

## Autoritat viva i escriptura única

El projecte és en fase **post-eclipsi**. Des del 22 d'agost Pere alterna Codex
i Claude per incorporar mirades independents amb handoffs auditables; cap IA
és propietària permanent. **El traspàs vigent és
`.coordination/HANDOFF_2026-09-09_V41.md`** (Claude: V41 = capes de la V40 sense cap reducció de soroll (filtres V38 byte a byte) + RHEF υ 0,35 oculta; estrelles: apuntament B de la Sony rotat +8,1′ → V42 candidata; research/159). Abans deia: **El traspàs vigent és
`.coordination/HANDOFF_2026-09-09_V40.md`** (Claude: V40: guany per banda = max(Wiener regional, garrote k=3) amb soroll mesurat a totes les vores i dues particions, sense terme creuat; capes retallades per Pere; research/157). Abans deia: **El traspàs vigent és
`.coordination/HANDOFF_2026-09-09_V39.md`** (Claude: V39: guany per banda dins de MGN/WOW/ACHF = max(llindar tou amb soroll MESURAT en meitats, terme creuat Vixen×Sony); jutge independent Brno; bases de pantalla amb la corba declarada; capes segons Pere; research/156). Abans deia: **El traspàs vigent és
`.coordination/HANDOFF_2026-09-08_V38.md`** (Claude: V38 = projecte complet amb la Lluna a l'INICI de la totalitat; la franja de l'oest mesurada a la font és cromosfera + pocs fotogrames, no un artefacte de 10×; dèficit de la vora lunar per fotograma corregit a l'origen; research/155). Abans deia: **El traspàs vigent és
`.coordination/HANDOFF_2026-09-08_V37.md`** (Claude: V37: condició de contorn al forat lunar també per a les capes ACHF (estaven saturades fins a 1,08–1,16 R☉ des de la V29), farcit B als operadors purs; la franja de la unió temporal queda i Pere decideix; research/154). Abans deia: **El traspàs vigent és
`.coordination/HANDOFF_2026-09-08_V36.md`** (Claude: V36: ERRATA de la LUT Sony corregida, RHEF amb rang continu, vora quadrada dels 8 s mesurada i declarada després de dues cures refusades; research/153). Abans deia: **El traspàs vigent és
`.coordination/HANDOFF_2026-09-08_V35.md`** (Claude: V35 curada a l'origen: vora Vixen conformada i esvaïda, trampa del forat lunar, P03/P04/P05 amb condició de contorn, relleu 1,9→3,5; causa del MGN documentada a research/151 §1). Abans deia: **El traspàs vigent és
`.coordination/HANDOFF_2026-09-07_V34.md`** (Claude: V34 curada a l'origen; la V33 queda refusada; norma nova de Pere: causa arrel, mai cosmètica, mai sacrificar detall). Abans deia: **El traspàs vigent és
`.coordination/HANDOFF_2026-09-07_V33.md`** (Claude: V33 lleugera, filtres amb resolució que segueix el S/N i NRGF/RHEF sense la vora del llenç). L'anterior, `.coordination/HANDOFF_2026-09-07_MARQUES_V32.md`, conserva la revisió de marques. Abans deia: **El traspàs vigent és
`.coordination/HANDOFF_2026-09-07_MARQUES_V32.md`** (Claude: revisió del PSB anotat de la V32; l'interior marcat és corona, mesurat amb control nul; el que queda és dels filtres: vora del llenç a NRGF/RHEF, resolució que segueixi el S/N; pla de V33 al handoff). L'anterior, `.coordination/HANDOFF_2026-09-07_V32.md`, conserva la V32. Abans deia: **El traspàs vigent és
`.coordination/HANDOFF_2026-09-07_V32.md`** (Claude: V32.psb, els 18 filtres regenerats sobre una base curada a l'origen; abans/després mesurat; judici visual de Pere obert). L'anterior, `.coordination/HANDOFF_2026-09-07_CODEX_A_CLAUDE.md`, conserva la revisió 145 i la recerca 143/144. Abans deia: **El traspàs vigent és
`.coordination/HANDOFF_2026-09-07_CODEX_A_CLAUDE.md`** (traspàs explícit de Pere a Claude: revisió de les 19 capes anotades completada, recerca causal143/144 documentada i pendent de continuació; cap correcció nova ni PSB modificat). El producte fotogràfic continua sent V31_FiltresPurs.psb, documentat a research/142. Els handoffs anteriors conserven l'evidència de cada ronda; el del22-08 conserva
la norma d'alternançaCodex/Claude. Represa: bloc inicial deCLAUDE, handoff consolidat i research/145.

En cas de contradicció, mana aquest ordre:

1. `AGENTS.md` per a normes i seguretat;
2. `.coordination/claim.lock/owner.json` per a l'únic escriptor viu;
3. el bloc inicial de `CLAUDE.md`, l'`ACTIVE.json` d'IA i el traspàs vigent
   per a l'estat del projecte;
4. `CODEX_STATUS.md` i `CLAUDE_STATUS.md` com a diaris append-only de cada agent;
5. `README.md`, `research/README.md` i documents datats com a índex i evidència.

`SERIAL_WRITES` és un directori adquirit amb `mkdir
.coordination/claim.lock` —operació atòmica— i conté un únic `owner.json`
amb `claim_id`, propietari, tasca, hora i abast. Si el directori ja existeix,
no escriguis: comprova el propietari i espera o rep un traspàs explícit. En
alliberar, registra primer `RELEASED` al teu fitxer d'estat i després elimina
només el teu `owner.json` i el directori buit. Un fitxer solt anomenat
`claim.lock` no és un lock vàlid.

`.claude/worktrees/gallant-hamilton-e9c6bd` és un worktree històric i no és
font d’autoritat. No hi continuïs feina ni el suprimeixis mentre una sessió
de Claude el pugui estar usant. La font viva és sempre l’arrel.

## Autoritat i maquinari

- Cap agent toca càmeres, PTP, `gphoto2`, captures, LaunchServices o la GUI
  física sense autorització concreta de Pere.
- Una campanya desatesa explícitament autoritzada cobreix els gates del seu
  pla viu, però no amplia l’abast, no autoritza accions manuals o destructives
  i no permet repetir un trigger ambigu.
- Resol sempre el port per identitat USB i confirma model + sèrie per PTP.
  L’ordre dels cables no és identitat.
- En una missió operativa materialitzada, un Busy, `-110`, timeout o resultat
  de trigger ambigu consumeix només aquella acció: registra-la en quarantena,
  no la repeteixis i conserva les accions futures del mateix cos mentre la
  identitat, la propietat i l'estat operatiu continuïn sent segurs.
- Identitat/propietat divergent, una mutació de configuració amb estat físic
  desconegut o la impossibilitat de mantenir el ledger aturen aquell canal.
  Els perfils de qualificació que declaren fail-fast també s'aturen al primer
  error. Cap d'aquests casos atura els altres canals.

## Prioritats invariants

1. **Mission first:** una càmera degradada no atura les altres, UNA CAMERA
   DEGRADADA s'ha d'intentar seguir utilitzant per la missió, costi el que
   costi. Aquest literal ordena esgotar les continuacions segures del canal;
   no autoritza repetir un trigger ambigu ni continuar amb identitat o
   propietat divergent, estat físic desconegut després d’un write o un ledger
   que no es pugui garantir. Aquests límits aturen només el canal afectat.
   Cap control auxiliar nou —ISO, Camera Settings, checklist, Sync UTC o
   equivalent— pot convertir-se directament o indirectament en prerequisit
   de `Start mission`. Només la identitat/propietat física necessària per
   dirigir amb seguretat aquell cos pot retenir el seu canal.
   El checklist és exclusivament un recordatori visual: desmarcat no genera
   `WARNING`, no degrada cap operació i continua editable durant Sync UTC.
   Deute de qualificació, H90, òptica o ciència ha de continuar visible com a
   informació de programa, però no és un `WARNING` operatiu de l'app.
2. **Simplicitat:** l’operador només ha de decidir allò que no pot decidir el
   programa.
3. **Agentic AI abans de la missió:** la captura és local, offline,
   determinista i independent de qualsevol LLM.

Les Sony recomanen ISO 100. La Canon 6D declara ISO 1600 per desplaçar la seva
finestra AEB nativa de 6 EV cap a la corona feble, ja que no pot fer un canvi
ràpid de 9 EV només amb bràqueting. Cap valor ISO —Auto, 0, desconegut o
absent— pot produir `FAILED`, bloquejar un stage o donar sortida no-zero en
una missió operativa. L’ISO és telemetria advisory propietat de l’operador.
El candidat privat local exposa botons ISO 100/200/400 només com a accions
preflight explícites. Un clic autoritza un sol intent per cos PTP suportat,
amb model i sèrie exactes, una mutació, readback i resultat literal `SET` o
`NOT SET`; cada fallada queda aïllada al seu canal. Només un Busy que declara
literalment `was not set` admet reintents acotats. Els controls queden
deshabilitats durant missió, scan, Sync UTC o una altra operació i mai són un
gate de `Start mission`. La release pública 0.8.0 continua immutable i sense
botons ISO.

## Baseline de captura congelat — 10 d’agost de 2026

- App local: `gui/dist/Eclipse Command.app`, candidat privat **V1.02**
  (`1.0.2`). La release pública 0.8.0 continua immutable.
- Executable SHA-256:
  `61227d418ec7a74a6fa11c934970d85218466ffd067754ec68efbc3334ba9f4f`.
- Manifest de 51 fonts SHA-256:
  `d06de97146e521afeb1871c3cfd06c5944faf3c40dbd96898f53c30d734a2f6a`;
  51/51 inputs coincideixen amb la font viva.
- QA font: GUI 513/513, controlador 1.107/1.107, fuzz, perfils, porta de
  totalitats 60–110 s i `git diff --check` verds. QA portable: 11/11 PASS,
  arm64, signatura ad-hoc vàlida i 114 Mach-O autocontinguts.
- La V1.02 mostra noms curts amb obertura de disseny, limita el hover a una
  descripció útil i identitat exacta, i afegeix veu a C2−5 min, −2 min,
  −1 min i C4−1 min. Els cues són one-shot i no es reprodueixen tard.
- Els Sony vius usen base de contacte 1/800, tres àncores d’earthshine i la
  muntanya de corona 1/4 → 1 s → 1/4; cap timing no s’hereta entre cossos.
- La R6 usa una foto per exposició, AEB off, contactes a 1/3200 i bloc fosc
  2 s ×3 + 10,3 s ×3. A la V1.02 el setter pre-C2 comença a C2−15,00 i la
  primera foto a −14,75. S’eliminen només vuit fotos de l’antic prefix;
  des de C2−5,65 fins a C4 el programa és idèntic a la V1.01. A 91 s són
  109 captures de nucli + cinc documentals = 114; totalitat 55, parcial
  posterior 34 i setters 29 no canvien.
- La simulació exhaustiva de la R6 cobreix 1.503 geometries entre 60 i 110 s:
  delta −8 exacte, sufix invariant i cronologies GUI/worker idèntiques.
- El bundle V1.02 s’ha obert físicament: capçalera V1.0.2, R6 III i A7RIIIA
  detectades READY amb els noms nous. No s’ha iniciat cap missió ni captura;
  la prova va acabar amb zero processos propis.
- L’evidència física d’exposicions continua sent la dels runs V1.01/V1.00;
  la V1.02 encara no té un run de dispars propi. Òptica, RAW, H90, HDR i
  tracking continuen com a deute advisory, no com a `WARNING` operatiu.
- Informe d’autoritat local: `gui/QA_REPORT_1.0.2_2026-08-10.md`.

## Regressió mínima

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=gui QT_QPA_PLATFORM=offscreen \
  gui/.venv312/bin/python -u -m unittest discover -s gui/tests

PYTHONDONTWRITEBYTECODE=1 \
  gui/.venv312/bin/python -m unittest discover -s controller/tests

PYTHONDONTWRITEBYTECODE=1 gui/.venv312/bin/python \
  gui/tools/qa_adaptive_timeline_fuzz.py .
```

No canalitzis les suites per `tail`: amaga una possible penjada. Per construir
i validar el bundle, segueix literalment la secció “Build macOS” de
`CLAUDE.md`.
