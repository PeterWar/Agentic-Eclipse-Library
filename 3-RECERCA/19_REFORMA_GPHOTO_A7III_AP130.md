# Reforma gphoto — A7III + AP130GTX + QUADCC

Data: 27 de juliol de 2026  
Estat: **F3 rebutja quinze canvis; substitució HDR nadiua en qualificació**

## Decisió

Es conserva la combinació A7III astromodificada + AP130GTX + QUADCC perquè
és la cadena mesurada i demostrada el 2024. `gphoto2` continua sent candidat
principal com a disparador persistent, sense tancar encara l'alternativa d'un
trigger independent. F3 ha demostrat, però, que el ladder no es pot reproduir
amb quinze canvis d'obturació dinàmics dins la totalitat curta de 2026.

No s'ha copiat el mecanisme del 2024. S'ha conservat el producte fotogràfic
i s'ha substituït l'arquitectura que el va fer fallar.

## Font 2024 recuperada

Còpia operativa més forta:

`/Users/USUARI/Dropbox/Astronomia/Script Eclipse/A7IIIFINAL.sh`

- mida: 5.520 bytes;
- data del fitxer: 8 d'abril de 2024;
- C2: `11:08:49`;
- C3: `11:13:17`;
- SHA-256:
  `3f5333438b9f658ac09921645bb378ac01a97c17b9e2d67c693bee5b56df665d`.

La seqüència RAW completa es troba a:

`/Users/USUARI/Dropbox/Astrofotografia/Eclipse Solar 2024/Eclipse A7III tot`

Conté 792 ARW i permet corregir la primera auditoria feta només amb la carpeta
curta.

## Producte observat

Amb l'offset nominal inferit entre rellotges, els RAW mostren:

- `1/400` × 12, aproximadament C2−30…C2−12;
- `1/8000` × 6, aproximadament C2−8…C2;
- primera volta HDR completa, 20 RAW, aproximadament C2+4…C2+56;
- buit de 30 s;
- segona volta incompleta i un buit de 125 s;
- `1/8000` × 6 al voltant de C3;
- `1/400` × 6 després de C3;
- `1/2500` des de C3+20.

El ladder programat i observat a la primera volta és:

`1/500 → 1/250 → 1/100 → 1/30 → 1/15 → 1/8 → 0,4 → 1 → 2 → 0,8 s`

El guió day-of fixava ISO 200, però Pere ha recordat el 27-07-2026 que va
ser una decisió d'última hora per compensar una capa fina de núvols; el pla
inicial de cel net era ISO 100. El candidat 2026 restaura **ISO 100 fix** i
manté els mateixos temps d'obturació. El canvi posterior ISO 200 → 100 dins
del buit de 125 s continua sent una deriva no planificada del run de 2024,
no evidència d'una transició ISO que s'hagi de reproduir.

## Què fallava el 2024

1. Cada ordre obria un procés i una sessió PTP nous.
2. Els canvis d'exposició no tenien readback.
3. Un error de `set-config` no impedia disparar amb la velocitat anterior.
4. Les funcions bloquejants no tenien deadline ni preempció de C3.
5. No hi havia política `skip_late`; una operació tardana contaminava les
   següents.
6. No hi havia watchdog auditable, identitat estricta, log estructurat ni
   recompte de deute.
7. La seqüència no tenia un handoff temporal auditat entre HDR i C3.

## Reforma implementada

Controlador:

`controller/eclipse_capture.py` — versió `0.2.2-candidate`

Perfil:

`controller/profiles/candidate_a7m3_ap130_2024_choreography.json`

Canvis:

- sessió `gphoto2 --shell` persistent;
- `--c2-at` i `--c3-at` ISO-8601 amb zona;
- una sola conversió UTC → monotònic;
- compilació i ordenació completa abans d'obrir cap sessió PTP;
- accions relatives a C2 o C3 amb offsets negatius o positius;
- deadlines relatius a C2/C3;
- tolerància i política de retard per acció;
- `set_exposure` amb un sol intent, ACK i readback;
- `held_capture` per a preses simples;
- separació entre `hold_s`, watchdog PTP, `worst_case_s` del mètode i
  `camera_busy_s` físic;
- auditoria única compartida per `dry-run` i `run`, amb rebuig de deadlines
  sense slack i de qualsevol solapament entre exposició, rearmament i
  següent ordre;
- dependència explícita foto → canvi d'exposició;
- cascada de salt si el canvi no s'ha completat;
- cap lectura de cua ni descàrrega entre captures del perfil;
- fins a quatre captures de corona `optional_if_fits`, decidides abans
  d'obrir PTP segons els C2/C3 reals;
- hold mesurat des del commit físic real, no des del target;
- watchdog calculat fins a l'últim press legal, de manera que la tolerància
  del scheduler no en retalla la lease;
- watchdog que converteix la intervenció d'emergència en error;
- lock únic per endpoint PTP, independent del directori de resultats i de la
  sèrie escrita al perfil;
- `result.json` atòmic i posterior al `fsync` del log;
- HDR protegit fins a C3−16,2, canvi a `1/8000` entre C3−16 i C3−10,1 i
  onze captures densificades entre C3−10 i C3+5;
- retorn a `1/8000`, després `1/400` i finalment `1/2500`.

El perfil candidat declara 76 accions: **56 fotografies obligatòries i
fins a 61**. Amb 88 s de totalitat compila 59 captures; no deixa 20 s per
«veure què fa la càmera».

| C3−C2 subministrat | Preses opcionals HDR/bridge | Total compilat |
|---:|---:|---:|
| 75,95–79,249 s | 0 | 56 |
| 79,25–82,549 s | 1 | 57 |
| 82,55–86,049 s | 2 | 58 |
| 86,05–89,349 s | 3 | 59 |
| 89,35–92,649 s | 4 | 60 |
| ≥92,65 s | 5 | 61 |

No hi ha una branca improvisada a temps real. Aquest resultat queda tancat
abans del primer accés PTP i es conserva a `events.jsonl` i `result.json`.
En la compilació de 88 s, la finestra no assignada més gran dins C2–C3 és
1,95 s; queda per sota dels 3,25 s auditats que necessita una altra presa
de 0,8 s.

La primera revisió independent de v0.2.0 va trobar dos bloquejadors abans de
cap prova física: deadlines exactament iguals a `target + worst_case`, que
feien saltar les accions amb qualsevol jitter, i parelles llargues separades
només 1 s. La v0.2.1 els elimina. La v0.2.2 afegeix farciment determinista,
postflight segons el calendari real i tanca falsos `complete`. Per a 0,4,
1, 2 i 0,8 s declara,
respectivament, finestres ocupades de 2, 2, 4 i 3 s, coherents amb els RAW
de 2024. El límit simbòlic degradable és **C3−C2 ≥ 75,95 s**; entre aquest
valor i 79,25 s s'omet només la segona presa de 0,8 s. Si no es
compleix, el controlador falla abans d'obrir `gphoto2`.

## Persistència

La ruta candidata és:

- `Still Img. Save Dest. = PC+Camera`;
- `RAW & JPEG`;
- RAW sense comprimir a SD;
- `RAW+J PC Save Img = JPEG Only`;
- JPEG petit com a telemetria pendent;
- cap `wait-event`, descàrrega ni lectura `d215` durant la seqüència;
- drenatge només després de C3+26 i de confirmar que ha vençut la finestra
  `camera_busy_s`;
- manifest de la SD abans/després com a autoritat dels ARW.

Aquesta ruta de persistència encara no està qualificada físicament després del
firmware 4.04.
El postflight automàtic del Mac només valida els JPEG drenats i publica
`scientific_raw_verified=false`; un `complete` del controlador no substitueix
la comprovació posterior dels ARW a la SD.

## Resultat físic post-firmware

F3 s'ha executat amb firmware 4.04: 150/150 canvis correctes, deu repeticions
de cadascuna de les quinze transicions, zero captures i restauració exacta a
`1/125`. La funcionalitat és bona, però el temps invalida el calendari:

- suma dels pressupostos candidats: 34,25 s;
- suma dels màxims observats: 49,043 s;
- suma dels pressupostos d'enginyeria recomanats: 61,3 s;
- salt crític `0,8 → 1/8000`: màxim 6,633 s i pressupost recomanat 7,8 s.

Per tant, el perfil conserva valor com a reconstrucció del producte 2024,
però queda deliberadament amb `timing_qualified=false` i **no s'ha d'armar**.
El detall causal i les mesures són a
[F3 A7III 4.04](20_F3_A7III_4_04_LATENCIA.md).

F3B ha comprovat una reducció a només dos salts extrems,
`1/8000 ↔ 1/30`: 20/20 canvis correctes, zero captures i pressupost recomanat
de 6,8 s en cada sentit. Això és un PASS de viabilitat temporal amb buffers,
no una qualificació de producció. Vegeu
[F3B 1/8000 ↔ 1/30](21_F3B_A7III_1_8000_1_30.md).

La via preferida redueix encara més els setters d'obturació: brackets nadius
agrupats `N × 9EV1 → N × 5EV3`, ISO 100 i base `1/30`, amb una única mutació
de `capturemode`. F3M ha qualificat en repòs les sis arestes directes entre
`Single`, `9EV1` i `5EV3`: 60/60 transicions, una ordre de mutació gphoto2 per
mostra i pressupost provisional de 1,4 s. El disseny i els seus límits són a
[Disseny HDR nadiu](22_DISSENY_HDR_NADIU_A7III_AP130.md) i
[F3M capturemode](23_F3M_A7III_CAPTUREMODE.md).

## Què encara no sabem

- cadència fiable d'una captura simple amb hold de 0,12 s;
- fiabilitat i latència dels canvis de mode mentre hi ha activitat RAW,
  buffer i SD; en repòs ja han completat 60/60;
- cadència real dels brackets nadius candidats i ordre EXIF de cada variant;
- capacitat de 28 i 42 ARW sense comprimir a SD, amb els JPEG de telemetria
  pendents al PC;
- si la cua PTP o el búfer introdueixen una degradació abans del final;
- persistència exacta a SD en les tres repeticions de 90 s;
- comportament amb cable, targeta o procés fallits.

Cap d'aquests valors s'ha de resoldre per opinió: els determina Gate 10.
