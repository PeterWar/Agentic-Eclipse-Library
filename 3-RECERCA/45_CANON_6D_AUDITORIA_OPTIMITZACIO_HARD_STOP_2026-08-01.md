# Canon EOS 6D — auditoria, optimització i hard stop físic

Data: 2026-08-01  
Cos: Canon EOS 6D, número de cos `[SÈRIE]`  
Sèrie PTP autoritzada: `[SÈRIE]`

## Veredicte executiu

La Canon 6D **no està qualificada per a la missió adaptativa C1-C4**. Tres
gates físics mínims —un RAW card-only i un únic canvi d'obturació sense
reintents— han reproduït `PTP Device Busy 0x2019`: aproximadament 6 s i 20 s
després del release amb `Image review=Hold`, i **7,012 s després del release amb
`Image review=None`**. El cos també havia rebutjat amb `0x2019` l'intent únic de
canviar `Image review` de `Hold` a `None` fins i tot en repòs.

Pere va posar `Image review=Off` manualment i dos preflights ho han demostrat
com `reviewtime=None`. Un primer run posterior va comprometre i verificar un
RAW però el scheduler va rebutjar el setter abans d'enviar-lo perquè el target
estàtic no reservava tot el pitjor cas de la captura. El perfil v3 va corregir
aquell calendari i sí que va enviar el setter exactament una vegada: també va
rebre `0x2019`. Per tant, `Hold` podia agreujar el bloqueig, però **no n'era la
causa única**, i ni 6,2 s ni 7,0 s són una finestra segura qualificada.

El hard stop pactat es va aplicar immediatament a cada campanya. Després del
power-cycle manual autoritzat, **AEB Single sí que s'ha qualificat físicament**:
`p=3`, ordre CR2 `1/250 -> 1/2000 -> 1/30`, vuit captures íntegres i fase
posterior normalitzada a zero amb un novè CR2. El pas següent, canviar Drive de
Single a Continuous amb AEB actiu, ha tornat a rebre `0x2019` abans de cap
captura. Continuous, escala de buffer i coreografia C2-C3 continuen sense
qualificació. El perfil viu està bloquejat tant al materialitzador com al
controlador abans d'armar-se. Un intent posterior d'apagar AEB, 49,6 minuts
després de l'últim RAW, també ha rebut `0x2019`; el cold-start abans del primer
RAW passa a ser la via obligatòria.

## Actualització física desatesa — 2026-08-01 14:20Z

1. Pere ha convertit la campanya Canon en una autorització continuada: no hi
   haurà checkpoints humans entre gates verds. Això no elimina el hard stop ni
   autoritza replay d'un write o trigger ambigu.
2. El primer stage `preflight_only` ha autodetectat una única Canon EOS 6D a
   `usb:001,001` i ha verificat model/sèrie exactes, bateria 50 %, Manual, MF,
   RAW, ISO 100, Memory card, `reviewtime=None`, mirror 0, 1/250, Drive Single
   i AEB +/-3. El perfil tenia zero accions, captures, configure o restore.
3. L'únic write, `set-config-index /main/capturesettings/aeb=0`, ha rebut
   `PTP Device Busy 0x2019` i `-110` al primer intent, en 9,532 ms. Zero retry,
   recovery, trigger o stage posterior; `capture_may_have_started=false`,
   cleanup/lock verds i cap procés viu
   (`controller/runs/codex_20260801_canon6d_optimization/20260801T162039_canon6d_lab_drive_stage_01_aeb_off_v1_preflight/result.json`).
4. Havien passat 2.974,183 s des de l'ACK de release de l'últim RAW i aquell
   CR2 ja estava descarregat, hashejat i estable. Això refuta encara amb més
   força una cua RAW pendent com a causa d'aquest Busy: en l'estat AEB
   actiu/Drive Single, el firmware PTP rebutja tant canviar Drive com apagar
   AEB. El mecanisme exacte continua sent una inferència d'interlock, no una
   especificació Canon demostrada.
5. La via següent ja no pot començar des de l'estat calent actual. Cal un
   cold-start que presenti AEB off abans de cap write; llavors el software ha
   de fixar, en aquest ordre i abans del primer RAW, obturació base, Drive
   Continuous i AEB +/-3. El power-cycle/estat AEB off és una dependència
   física real, no una nova petició d'autorització de software.

### Preflights externs posteriors — 2026-08-01 14:33–14:36Z

Quatre preflights llançats per una GUI externa van tornar a obrir la sessió
PTP després del hard stop. No van enviar cap setter ni trigger: tots quatre
registren zero commits i captures, `capture_may_have_started=false`, identitat
exacta, `cleanup_ok=true`, `restore_ok=true` i estat físic conegut. Les quatre
lectures coincideixen: `1/250`, AEB `+/- 3`, Drive `Single`, mirror lock 0,
`reviewtime=None`, M, MF, RAW, ISO 100 i `Memory card`.

Van acabar com a `WARNING`, no com a preflight verd, perquè el perfil històric
bloquejat exigia AEB off i `1/4000`. Aquesta evidència només demostra que les
lectures PTP continuaven funcionant i que l'estat no havia derivat; **no neteja
ni qualifica el latch d'escriptura** que havia rebutjat l'AEB, i no substitueix
el power-cycle cold-start. Artefactes:
`/Users/USUARI/Library/Application Support/Eclipse Command/state/runs/20260801T163334_candidate_canon6d_contacts_cardonly_preflight/mission_result.json`
fins a
`.../20260801T163657_candidate_canon6d_contacts_cardonly_preflight/mission_result.json`.

## Actualització física desatesa — 2026-08-01 13:14–13:39Z

1. Després del power-cycle de Pere, el preflight AEB Single va verificar la
   Canon/sèrie exactes, bateria 50 %, M, MF, RAW, ISO 100, Memory card,
   `reviewtime=None`, mirror lock 0 i Drive Single; va convergir una sola vegada
   `1/4000 -> 1/250` i `AEB off -> +/- 3`, abans de cap RAW
   (`controller/runs/codex_20260801_canon6d_optimization/20260801T151403_canon6d_lab_aeb_single_v1_preflight/result.json`).
   El snapshot posterior va trobar `IMG_2301.CR2`, creat abans del preflight;
   es va verificar només en lectura com a 1/4000, ISO 100 i CR2 íntegre i es va
   etiquetar `UNATTRIBUTED_PREEXISTING_CR2`, sense atribuir-li cap ledger
   (`.../20260801T151458_canon6d_lab_aeb_single_v1_canon-card-inspect-existing/result.json`).
2. El run AEB Single va completar 8/8 parelles press/release, zero setters
   post-RAW, Busy, retries, recovery, warnings o replay. El gate card-only va
   afegir exclusivament `IMG_2302.CR2`–`IMG_2309.CR2`: vuit hashes únics,
   153.292.134 bytes, cos i ISO exactes, payloads RAW íntegres, delta/ledger 8
   i inventari final estable
   (`.../20260801T151545_canon6d_lab_aeb_single_v1_run/result.json` i
   `.../20260801T151725_canon6d_lab_aeb_single_v1_canon-card-gate/result.json`).
3. L'ordre físic repetit és `1/250 -> 1/2000 -> 1/30`, amb `p=3`, dues voltes
   completes i `tail=2`. La 6D grava `ExposureBiasValue=0` als tres CR2; el
   gate usa les obturacions reals, no inventa els biaixos
   (`.../20260801T151725_canon6d_lab_aeb_single_v1_canon-card-gate/capture_sequence.json`).
4. Amb la fase a índex 2, la 6D exposava per PTP només `Current=1/30` i una
   única choice `1/30`. Un primer perfil incompatible va fallar només en
   lectura, abans de mutació o captura. El v2, lligat per SHA al gate anterior,
   va fer exactament una pressió sense setters. `IMG_2310.CR2` és 1/30,
   íntegre, delta/ledger 1, i el gate demostra `tail 2 -> 0` i
   `phase_zero_verified=true`
   (`.../20260801T153100_canon6d_lab_aeb_phase_complete_p3_t2_v2_run/result.json`
   i `.../20260801T153202_canon6d_lab_aeb_phase_complete_p3_t2_v2_canon-card-gate/capture_sequence.json`).
5. El perfil Continuous d'un bracket conservava l'ordre CR2 complet però
   exigia al menú PTP només la base. El preflight viu va veure fase zero,
   `Current=1/250`, 52 choices, AEB +/-3 i Single. Shutter i AEB coincidien i
   no van generar writes. L'únic write, `Drive Single -> Continuous`, va ser
   rebutjat al primer intent amb `PTP Device Busy 0x2019` i `-110`
   (`.../20260801T153759_canon6d_lab_aeb_continuous_p3_g1_v1_preflight/events.jsonl:65-80`).
6. Aquest últim hard stop és anterior a qualsevol trigger: zero CR2 nou, zero
   retry/recovery/replay, canvi de Drive rebutjat, estat conegut en Single,
   cleanup i lock verds i cap procés de càmera viu. No qualifica Continuous ni
   cap buffer. La transició següent només es prepara offline: AEB actiu -> off,
   Drive Continuous i AEB +/-3, tot abans del primer RAW, amb readbacks i zero
   retries; encara és una hipòtesi no executada.

## Actualització física desatesa — 2026-08-01 12:57–13:00Z

1. Amb la nova autorització de Pere i `SERIAL_WRITES` exclusiu, el preflight v3
   va verificar identitats exactes, `reviewtime=None`, mirror lock 0, Single,
   AEB off, M, MF, RAW, ISO 100, Memory card i 1/4000, amb zero warnings,
   captures o accions manuals
   (`controller/runs/codex_20260801_canon6d_optimization/20260801T145759_canon6d_lab_quiet_v1_preflight/result.json`).
2. El manifest immediatament anterior era estable i contenia exactament cinc
   CR2, d'`IMG_2295.CR2` a `IMG_2299.CR2`, sense mutació ni trigger
   (`.../20260801T145817_canon6d_lab_quiet_v1_canon-card-snapshot/inventory.json`).
3. El run v3 va obtenir ACK d'un únic press i release i va comprometre una
   imatge. El release es va enviar a `1978561441000` ns i l'únic setter
   `1/4000 -> 1/2500` a `1985573822000` ns: **7,012381 s després**. El write va
   tornar `PTP Device Busy 0x2019` al primer intent. Hi va haver zero Busy
   retries, recovery, reconnexió o replay; l'aturada fail-fast és explícita
   (`.../20260801T145831_canon6d_lab_quiet_v1_run/events.jsonl:121-145`).
4. El cleanup va esperar el guard, va rellegir 1/4000, va confirmar release,
   estat físic resolt i cap restore write necessari
   (`.../20260801T145831_canon6d_lab_quiet_v1_run/events.jsonl:146-164`).
5. El gate posterior només de reconciliació va trobar exactament
   `IMG_2300.CR2`: delta 1/ledger 1, 19.174.667 bytes, SHA-256
   `1da746dc2b5a03d790aa801441d24b14c1bc6debb4fee3a18427c9bc8cc94980`,
   EXIF 12:58:37.74, 1/4000, ISO 100, cos exacte, CR2 2.0 i payload RAW
   íntegre. La tercera lectura de la targeta va ser estable i
   `scientific_raw_verified=true`
   (`.../20260801T150000_canon6d_lab_quiet_v1_canon-card-gate/result.json` i
   `downloads_manifest.json`).
6. El run font continua KO: la reconciliació qualifica només aquella captura,
   no el setter ni el perfil v3. El hard stop va impedir executar AEB Single,
   AEB Continuous, buffer, cadència o coreografia C2-C3.

## Actualització física desatesa — 2026-08-01 12:25–12:37Z

1. El preflight estricte va verificar `reviewtime=None`, identitats exactes,
   mirror lock 0, Single, AEB off, M, MF, RAW, ISO 100, Memory card, 1/4000,
   bateria 100 %, cap warning i cap acció manual
   (`controller/runs/codex_20260801_canon6d_optimization/20260801T142932_canon6d_lab_quiet_v1_preflight/result.json`).
2. L'inventari va trobar un `IMG_2298.CR2` anterior al preflight. Una via
   només lectura el va descarregar pel nom exacte, va repetir l'inventari i el
   va etiquetar `UNATTRIBUTED_PREEXISTING_CR2`, sense inventar cap ledger ni
   qualificar cap captura. És íntegre: 19.148.713 bytes, SHA-256
   `34b9737b9ee7aa2df6687c9bed8e23c88f110297358ccab810a09f5ea52f00f6`,
   EXIF 12:25:47, 1/4000, ISO 100, cos exacte i CR2 2.0
   (`.../20260801T143337_canon6d_lab_quiet_v1_canon-card-inspect-existing/result.json`
   i `downloads_manifest.json`).
3. El run següent va fer un únic `Press Full MF` i `Release Full`, tots dos
   amb ACK, i ledger d'una imatge. El release real va quedar aproximadament
   0,453 s després del target inicial. El readiness de configuració era
   `release+6,2 s`, però el setter tenia target fix a 6,32 s; el scheduler el
   va rebutjar abans de cap ordre d'obturació perquè faltaven 0,333 s. Zero
   setter PTP, `0x2019`, Busy retry, recovery, reconnexió o replay
   (`.../20260801T143439_canon6d_lab_quiet_v1_run/events.jsonl:120-145`).
4. `IMG_2299.CR2` queda correlacionat exactament amb aquell ledger: delta 1,
   19.163.801 bytes, SHA-256
   `abbc39af84f261f4566e5708ad8095193b652148d3afb9efa1c653a4d5dbe56f`,
   EXIF 12:34:45.41, 1/4000, ISO 100, cos exacte, payload RAW íntegre i targeta
   estable. El gate és explícitament `capture_reconciliation_only`; no
   converteix el run font KO en qualificació
   (`.../20260801T143652_canon6d_lab_quiet_v1_canon-card-gate/result.json`).
5. En aquell punt, el generador offline ja programava qualsevol setter post-RAW
   després del `worst_case_s` complet de la captura més el quiet gap. El perfil nou posa el
   setter a 7,12 s = 0,92 + 6,2, valida i fa dry-run verd. Posteriorment s'ha
   executat una sola vegada i ha quedat vermell, tal com documenta
   l'actualització 12:57–13:00Z:
   `controller/runs/codex_20260801_canon6d_optimization/profiles/canon6d_lab_quiet_gap6_2_review_required_v3.json`,
   SHA-256
   `aa3477ddc04e4b4f7d7f358b01d55bd74436418f5817842ef16f6213ddaccdf5`.

## Actualització física desatesa — 2026-08-01 10:59–11:03Z

La represa autoritzada va tancar dos punts que faltaven i va trobar un segon
hard stop:

1. El CR2 orfe anterior es va reconciliar sense trigger. La targeta va passar
   exactament d'1 a 2 fitxers i va afegir només `IMG_2296.CR2`: 19.144.464
   bytes, SHA-256
   `f051ac76a12c557b462fab3555a846297ea2e06ad8fee2b2e2f2007ed4e51067`,
   Canon EOS 6D, cos `[SÈRIE]`, CR2 2.0, RAW 5568×3708 amb payload
   íntegre, ISO 100, 1/4000 i biaix 0 EV. Delta 1 i ledger 1 coincideixen
   (`controller/runs/codex_20260801_canon6d_optimization/20260801T125913_canon6d_lab_quiet_v1_canon-card-gate/result.json`).
2. El preflight viu va ser estricte i verd: identitat exacta, bateria 100%,
   M, MF, RAW, ISO 100, Memory card, 1/4000, Single, AEB off, mirror lock 0
   i zero accions manuals
   (`.../20260801T125957_canon6d_lab_setter_idle_v1_preflight/result.json`).
3. El setter-idle va completar `1/4000 -> 1/2500 -> 1/4000`, amb dos writes
   al primer intent, ACK/readback i aproximadament 46 ms de roundtrip per
   write. Zero captures, Busy, recovery o reconnexió; l'inventari SD posterior
   va continuar exactament amb `IMG_2295.CR2` i `IMG_2296.CR2`
   (`.../20260801T130031_canon6d_lab_setter_idle_v1_run/result.json`).
4. El nou gate RAW va tenir press i release inequívocs i ledger 1. El setter
   `1/4000 -> 1/2500` va ser enviat una sola vegada aproximadament 20 s després
   de l'ACK del release i va tornar a rebre `0x2019`. Zero retries, recovery o
   replay. El cleanup va esperar el guard de 50 s, va llegir 1/4000 i va deixar
   l'estat físic conegut
   (`.../20260801T130209_canon6d_lab_quiet_v1_run/events.jsonl:114-158`).

## Actualització física desatesa — 2026-08-01 11:22–11:24Z

La nova autorització va permetre tancar el RAW pendent i provar una sola
autocorrecció abans de qualsevol trigger:

1. L'inventari card-only va passar exactament de 2 a 3 fitxers i va afegir
   només `IMG_2297.CR2`: 19.146.068 bytes, SHA-256
   `23b01a3f99a3a596cfbde315a6c74bf616fb1e5876d0c0c2df477264091b9934`,
   CR2 2.0, Canon EOS 6D, cos `[SÈRIE]`, RAW 5568×3708 íntegre, ISO 100,
   1/4000 i biaix 0 EV. Delta 1, ledger 1, nom consecutiu, hash, EXIF i payload
   són verds
   (`controller/runs/codex_20260801_canon6d_optimization/20260801T132242_canon6d_lab_quiet_v1_canon-card-gate/result.json` i
   `downloads_manifest.json`).
2. El preflight següent va verificar la identitat exacta i tot l'estat excepte
   `reviewtime=Hold`. Va enviar una única ordre
   `set-config-index /main/settings/reviewtime=0`, amb `max_attempts=1` i
   `busy_retries=0`, per intentar `Hold -> None`; el cos la va rebutjar amb
   `PTP Device Busy 0x2019`
   (`.../20260801T132430_canon6d_lab_quiet_v1_preflight/result.json`).
3. El gate va acabar amb zero trigger, zero captura nova, zero retry, zero
   recovery, release no necessari i cleanup verd. `SERIAL_WRITES` es va
   alliberar immediatament.

Això demostrava en aquell moment una dependència manual concreta: **Pere havia
de posar Revisió d'imatge/Image review a Off al cos**. Pere ho va fer després;
els apartats anteriors documenten la lectura `None` i el gate causal posterior.

## Image review = Hold: hipòtesi causal i bloqueig manual demostrat

El bolcat complet immediatament anterior als dos gates va llegir:

- `/main/settings/reviewtime = Hold`;
- `/main/settings/autopoweroff = 0`.

La propietat `reviewtime` és writable i ofereix `None`, `2 seconds`,
`4 seconds`, `8 seconds` i `Hold`
(`controller/runs/codex_20260801_canon6d_optimization/20260801T010919_candidate_canon6d_contacts_cardonly_capabilities/capabilities.txt:215-224`).
El manual oficial Canon EOS 6D, pàgina 55, diu que `Hold` manté la imatge
mostrada fins que expira l'autoapagada. Amb autoapagada desactivada, aquest
estat és compatible amb un bloqueig post-RAW molt més llarg que l'escriptura
del fitxer: <https://gdlp01.c-wss.com/gds/7/0300009627/03/EOS_6D_Instruction_Manual_EN.pdf>.

Això era una **inferència causal forta, no una qualificació física**. Ara el
canvi manual, la lectura `None` i el gate v3 sí que estan demostrats. El setter
únic enviat 7,012 s després del release també ha retornat `0x2019`. Per tant,
`None` **no resol per si sol** el Busy post-RAW. No s'ha de repetir el mateix
gate ni augmentar el constant per intuïció; el camí preferit passa a ser blocs
de configuració fixa, preparats abans del primer RAW i sense setters post-RAW.

La conclusió fotomètrica de Mazatlán és diferent: **la Canon no va quedar
globalment ni massa sobreexposada ni massa subexposada** perquè l'escala era
àmplia. Sí que hi ha sobreexposició deliberada o excessiva en els extrems
llargs i en alguns diamants, i el `1/400` a ISO 100 del candidat actual és
sospitós de ser massa llarg per al diamant. `1/4000` continua sent una àncora
necessària de highlights.

## Abast i frontera de seguretat

- `SERIAL_WRITES` es va adquirir només després de l'alliberament explícit del
  task A7RIIIA.
- No es va obrir ni executar la GUI.
- No es va fer cap prova solar, òptica, manual, destructiva, de cable-pull o
  de bateria.
- El primer error de càmera va tancar la campanya física; tota la feina
  posterior és offline.
- Els resultats Sony només s'han transferit com a **mètode**. Cap cadència,
  fondària de buffer, temps de drenatge o ordre de bracket Sony s'ha atribuït
  a la Canon.

## Perfil viu, materialització i missatges heretats

El perfil `candidate_canon6d_contacts_cardonly.json` continua sent operatiu en
inventari (`mission.enabled=true`) però no és executable: declara
`CANDIDATE_NOT_PRODUCTION`, `timing_qualified=false` i un
`mission_capture_blocked_reason`. La materialització adaptativa Canon llegeix
aquest blocker i llança `ProfileError` abans de compilar cap cronologia; si
s'invoca directament el controlador en mode `run`, el segon gate torna a fallar
abans de `--arm` o PTP (`gui/eclipse_command/adaptive_profiles.py:2652-2670` i
`controller/eclipse_capture.py:14609-14621`).

El mode `preflight` sí que pot obrir PTP per llegir l'estat i acaba en warning
si el cos divergeix; això explica els quatre preflights externs, però no permet
una captura ni qualifica el perfil. El port declarat `usb:002,001` és
deliberadament històric i volàtil: la identitat real és el model i la sèrie PTP,
i els runs recents resolen `usb:001,001`.

La política ISO nova només afecta els tres perfils de missió: ISO 100 manual és
el baseline recomanat, Auto ISO és prohibit com a instrucció i hi ha zero
setters/restore ISO. Qualsevol valor observat és propietat de l'operador, també
entre C2 i C3, i no pot bloquejar ni fer fallar la missió
(`research/46_POLITICA_ISO100_OPERADOR_2026-08-01.md`). Els perfils lab i els
manifests històrics mantenen ISO exacta i no es reetiqueten.

Queden tres incoherències textuals explícites que **no són evidència física**:

1. el blocker del perfil diu `2.974,171 s`; el càlcul entre l'ACK del release
   `3927279166625 ns` i l'enviament AEB `6901462083083 ns` és
   `2.974,182916458 s`, és a dir, `2.974,183 s` arrodonit;
2. el checklist `1/4000`, AEB off i Single descriu el baseline de missió
   històric, no l'últim estat físic conegut (`1/250`, AEB `+/- 3`, Single);
3. les constants històriques `CANON_SHUTTER_QUIET_GAP_S=6.0` i schedule 6,2 s
   continuen al compilador antic, però 6,0/6,2/7,012 s ja estan refutats i el
   blocker impedeix que aquella branca es materialitzi. No es poden presentar
   com a mitigació qualificada.

El primer text no es corregeix dins del perfil en aquesta represa perquè el
bundle immutable cold-start v2 pinna exactament el seu SHA post-ISO; l'errata
queda auditada aquí i haurà de corregir-se només amb una nova versió immutable
de tots els dependents, no alterant v2 en lloc.

## DEMOSTRAT físicament

### 1. Identitat USB/PTP i canvi de port

- El bolcat viu només lectura va resoldre `usb:001,001`, tot i que el perfil
  conserva l'endpoint històric volàtil `usb:002,001`. Va verificar model PTP,
  sèrie PTP i firmware exactes, 85 paths, zero writes i zero triggers
  (`controller/runs/codex_20260801_canon6d_optimization/20260801T010919_candidate_canon6d_contacts_cardonly_capabilities/result.json:1-19,52-81`).
- IORegistry només va trobar un producte `Canon Digital Camera`; després
  d'obrir aquell port, el controlador va verificar la identitat PTP exacta.
  La Canon no exposa una sèrie USB documentada en aquesta ruta
  (`.../result.json:59-76`).
- L'etiqueta de `gphoto2 --auto-detect` no és identitat: en aquest Mac dos
  endpoints apareixien com a `Canon EOS 6D`, i un d'ells era una Sony. El
  missatge manual del perfil s'ha corregit perquè exigeixi model i sèrie PTP,
  no l'etiqueta ni el número de bus.
- Hi ha evidència física anterior del mateix cos a `usb:002,001` i posterior a
  `usb:001,001`. Això qualifica el rebind després de reordenar ports, no un
  cable-pull en calent.

### 2. Estat viu, mirror lock i temporitzador

El preflight immediat de 2026-08-01 va ser estricte, no advisory, sense
warnings ni accions manuals. Va llegir:

- `Drive Mode = Single`, és a dir, sense temporitzador de 2 s;
- `mirrorlock = 0`;
- `AEB = off`, M, MF, RAW, ISO 100, `Memory card`, `1/4000`;
- bateria 100 %, 2.469 exposicions disponibles, autoapagada 0;
- model, sèrie PTP, firmware i número de cos exactes.

Evidència:
`controller/runs/codex_20260801_canon6d_optimization/20260801T011708_canon6d_lab_quiet_v1_run/events.jsonl:108-111`.

La nota heretada «mirror lock i Timer 2 sec posats alhora» era incorrecta. Un
artefacte del 30-07 sí que mostra `Timer 2 sec` divergent, però en el mateix
artefacte `mirrorlock=0`
(`/Users/USUARI/Library/Application Support/Eclipse Command/state/runs/20260730T220459_candidate_canon6d_contacts_cardonly_preflight/channels/canon6d/controller/20260730T220500_candidate_canon6d_contacts_cardonly_preflight/result.json:288-341,407-467`).

El preflight els detecta. El problema històric és que mission-first podia
convertir aquestes divergències en avisos i continuar. El bloqueig nou del
perfil evita que la Canon de missió arribi a aquesta ruta. Això no substitueix
la necessitat que, en una futura promoció, timer, drive i mirror lock siguin
gates no bypassables.

### 3. Targeta abans del run

L'inventari remot card-only verd va recórrer cinc directoris i va trobar una
única entrada inicial, `IMG_2295.CR2`, sense write, trigger, delete ni format
(`controller/runs/codex_20260801_canon6d_optimization/20260801T011609_candidate_canon6d_contacts_cardonly_canon-card-snapshot/inventory.json:1-28,61-71`).

La llista remota de gPhoto no aporta mida ni hash. Per això el manifest previ
només pot fixar la clau `(folder, name)`; la integritat exigeix descarregar el
delta exacte després del run.

### 4. Gates mínims `0x2019`

El perfil físic va declarar `max_attempts=1` i `busy_retries=0`. El run va fer:

1. un press RAW reconegut;
2. un release reconegut;
3. un únic `get-config` d'obturació;
4. un únic `set-config-index` `1/4000 -> 1/2500`;
5. zero reintents i zero reconnexions.

Els instants verificables són:

- press enviat: `77715596988833` ns;
- release enviat: `77715717025541` ns;
- ACK del release: `77715726883708` ns;
- setter enviat: `77721818135583` ns;
- resposta Busy: 19,429 ms després.

El `get-config` immediatament anterior deia `Readonly: 0`; el write va ser
rebutjat igualment. Una lectura disponible no prova disponibilitat
d'escriptura. Evidència completa:
`controller/runs/codex_20260801_canon6d_optimization/20260801T011708_canon6d_lab_quiet_v1_run/events.jsonl:113-138`.

Queda demostrat un punt vermell a 6,091 s post-ACK-release. **No queda
demostrat el temps mínim segur.**

El gate v3 posterior afegeix un punt vermell més fort: amb
`reviewtime=None`, el setter únic també falla a 7,012381 s del release. El
readback immediatament anterior encara publicava `Readonly: 0`; això confirma
de nou que llegir la propietat no prova que el write sigui admissible
(`controller/runs/codex_20260801_canon6d_optimization/20260801T145831_canon6d_lab_quiet_v1_run/events.jsonl:135-145`).

### 5. Cleanup de l'últim artefacte

L'artefacte final registra release confirmat, zero intents de reconnexió,
obturació observada a `1/4000`, `restore_ok=true`, `cleanup_ok=true` i estat
físic resolt. No es van modificar AEB ni Drive. Aquesta és evidència del final
de la sessió, no una lectura viva posterior
(`controller/runs/codex_20260801_canon6d_optimization/20260801T145831_canon6d_lab_quiet_v1_run/events.jsonl:146-164`).

### 6. Evidència física anterior que continua sent vàlida

La coreografia fixa antiga de 23 contactes sí que té evidència física:

- 23/23 press+release i 23 commits al ledger;
- delta posterior de 23 CR2 consecutius, 11 a C2 i 12 a C3;
- dues mostres completes amb SHA-256, CR2 v2.0, 5472×3648, Canon 6D,
  ISO 100 i `1/4000`.

Fonts:
`runs/2026-07-29_real_mission_first/REAL_RUN_REPORT_2026-07-29.md:80-121` i
`runs/2026-07-29_real_three_camera_simultaneous/REAL_THREE_CAMERA_SIMULTANEOUS_REPORT_2026-07-29.md:65-84`.

Aquesta evidència qualifica **23 captures fixes a `1/4000`**, inclosa
simultaneïtat de software amb els altres cossos. No qualifica la
materialització adaptativa, AEB, Continuous, fondària de buffer, canvis
d'obturació ni integritat de tots els CR2.

## CR2 dels gates actuals: límit exacte

Els quatre RAW atribuïbles als gates actuals ja estan reconciliats.
`IMG_2296.CR2`, `IMG_2297.CR2`, `IMG_2299.CR2` i `IMG_2300.CR2` tenen delta i
ledger unitaris, hash SHA-256, CR2 2.0, payload íntegre, cos exacte, ISO 100,
1/4000 i biaix 0 EV. `IMG_2298.CR2` també és íntegre, però queda deliberadament
fora d'aquesta sèrie perquè és preexistent i no atribuït a cap ledger.

Això qualifica la persistència i integritat d'aquests **quatre RAW individuals**.
No qualifica AEB, una ràfega, la fondària de buffer, la cadència ni la
persistència d'un grup multiimatge.

## Mazatlán 2024: vam sobreexposar o subexposar massa?

S'ha auditat directament la carpeta Dropbox
`Eclipse Solar 2024/Eclipse 300mm`: 1.038 CR2, tots de la Canon EOS 6D amb
número de cos `[SÈRIE]`. El bloc crític RAW conté 162 fotogrames
`_MG_9424`–`_MG_9585`; l'inventari forense anterior preservat al repositori
només cobria 146 CR2 (`_MG_9428`–`_MG_9573`) i confirma la gamma d'obturacions,
continuïtat i cadència
(`research/12_FORENSICA_RAW_2024.md:48-66` i
`research/data/2024_exposure_runs.csv:2-41`).

### Resultat visual i quantitatiu

- El mosaic RAW decodificat té nivell negre 2.047 i blanc 15.070. A C2,
  `1/1250`, ISO 200, deixa entre 0,0403 % i 1,0728 % dels samples globals al
  sostre; a la ROI central el rang puja de 0,56 % a 15,03 %. És útil per al
  diamant, però massa llarg per preservar totes les perles fines.
- A C2, `1/4000`, ISO 200, baixa a 0,00012–0,00450 % global i 0–0,06 % a la
  ROI central. Conserva molt millor perles, anell i highlights: no estava
  «massa fosc» per a aquesta capa ràpida.
- A la corona, el clipping global medià creix de 0,000245 % a `1/1000` a
  0,00124 % (`1/500`), 0,0187 % (`1/200`), 0,174 % (`1/80`), 0,531 %
  (`1/30`), 1,667 % (`1/4`), 2,429 % (`0,4 s`) i 5,998 % (`1 s`). Les
  exposicions llargues cremen la corona interior, però a `1 s` l'anell exterior
  encara queda aproximadament 1.953–2.859 DN sobre el fons: era una capa HDR
  útil, no una exposició única correcta.
- A C3, `1/4000` queda prop de 0,0015–0,002 % global; `1/2500` puja a
  0,0079–0,0675 %, i `1/1600` arriba a 0,3–1,136 % global i fins a 15,9 % a
  la ROI central. Per tant, `1/1600` és massa llarg per a la perla més fina,
  però encara útil per al diamant.

L'obertura i la focal EXIF dels CR2 són zero: `f/2,8` prové del nom de la
carpeta/tren documentat, no d'una lectura EXIF. Els percentatges anteriors són
clipping del mosaic RAW, no del JPEG incrustat; continuen sent diagnòstic de
l'escala 2024, no una qualificació solar 2026.

### Implicació per al candidat 2026

A igual obertura:

- `1/400`, ISO 100 rep +0,64 EV respecte de `1/1250`, ISO 200;
- `1/400`, ISO 100 rep +1 EV respecte de `1/1600`, ISO 200.

Com que aquells diamants ja mostraven clipping, el `1/400` actual és un risc
real de sobreexposició i necessita A/B solar. En canvi, tota l'escala 2026 a
ISO 100 és un stop més fosca que la mateixa obturació a ISO 200 de Mazatlán;
això redueix l'excés dels graons llargs, però també fa `1/4000` encara més
conservador. La decisió operativa prudent és conservar una via ràpida
independent per a perles (`1/4000` com a mínim candidat), donar més repeticions
a la banda coronal `1/500`–`1/30`, i usar només unes poques preses de `0,4`–`1 s`
per a corona exterior. No s'ha de substituir la via ràpida per una sola
exposició més lenta.

Conclusió pràctica: conservar `1/4000` com a àncora; no promoure `1/400` com a
diamant definitiu; mantenir HDR ampli i decidir l'ancoratge amb tren, filtre,
altura solar i transparència reals.

## AEB i buffer: què sabem i què no

### DEMOSTRAT físicament

El bolcat viu ofereix:

- Drive `Single` i `Continuous`;
- AEB `off` fins a `+/- 3`;
- `bracketmode = Unknown value 0000` com a única opció.

Fonts:
`controller/runs/codex_20260801_canon6d_optimization/20260801T010919_candidate_canon6d_contacts_cardonly_capabilities/capabilities.json:424-470`.

A més de demostrar que els setters existeixen, la campanya actual prova en
Single:

- AEB `+/- 3` amb `p=3`;
- ordre CR2 `1/250 -> 1/2000 -> 1/30`;
- dues voltes completes, una cua de dues posicions i la seva normalització
  posterior exacta a fase zero;
- 9/9 CR2 nous íntegres i correlacionats amb el ledger;
- cap setter post-RAW, Busy, retry, recovery o replay dins d'aquests dos runs.

La coreografia fixa anterior aporta una altra dada separada: dues execucions
23/23 —una d'elles simultània amb els altres cossos— van sostenir una cadència
Single aproximada d'1,25 s, holds d'uns 130–146 ms i lateness de dispatch per
sota de 0,5 ms. Això qualifica el scheduler Single en aquella càrrega, però no
la durada real d'un grup Continuous ni el drenatge de la targeta
(`runs/2026-07-29_real_mission_first/REAL_RUN_REPORT_2026-07-29.md:80-121` i
`runs/2026-07-29_real_three_camera_simultaneous/REAL_THREE_CAMERA_SIMULTANEOUS_REPORT_2026-07-29.md:65-84`).

Els vuit CR2 AEB del gate actual pesen 153.292.134 bytes: 19,16 MB per imatge i
57,48 MB per grup de tres de mitjana. Això equival a una entrada nominal de
19,16 MB/s a `P=3,0 s`, 28,74 MB/s a `P=2,0 s`, 38,32 MB/s a `P=1,5 s` i
45,99 MB/s a `P=1,25 s`. Són càrregues calculades, no rendiment SD mesurat.

No revela encara el hold mínim de Continuous, el període mínim entre grups,
quan acaba un grup sota pressió sostinguda ni quants grups complets caben al
buffer. L'intent de passar a Drive Continuous amb AEB actiu ha fallat amb
`0x2019` abans de cap captura.

El manual oficial declara nominalment 4,5 fps i aproximadament 14 RAW amb
targeta estàndard o 17 amb UHS-I, i permet AEB de 2/3/5/7 preses. Són
especificacions del fabricant, no qualificació d'aquest cos, aquesta targeta o
aquests CR2: <https://gdlp01.c-wss.com/gds/7/0300009627/04/EOS_6D_Instruction_Manual_EN.pdf>.
Amb `p=3`, aquells dos límits serien només 4 o 5 grups complets més dues imatges;
sis grups (18 CR2) superarien tots dos nominals. Això justifica provar
`1 -> 2 -> 4 -> 5` i tractar 6 com a frontera explícita, però no prediu el
resultat d'aquesta targeta.

El perfil de laboratori conservador encara reserva `W=1,8 s`, readiness de
configuració/drenatge `1,8 s`, retrigger `0,1 s` i jitter `0,02 s`; per tant
exigeix `P >= 2,12 s`. Els marges offline són +0,88 s a `P=3,0`, -0,12 s a
`P=2,0`, -0,62 s a `P=1,5` i -0,87 s a `P=1,25`. No es poden compilar les
dècimes agressives com a qualificades fins que Continuous redueixi físicament
aquests bounds.

### Hipòtesi d'optimització parcialment qualificada

El cos ja ha confirmat físicament `p=3` i l'ordre `1/250 -> 1/2000 -> 1/30` per
al candidat actual. Això permet reduir setters i, si Continuous supera el seu
gate pendent, explotar el buffer en grups complets. Les altres bases següents
continuen sent càlcul fotomètric, no seqüències físiques qualificades:

- contactes, base `1/1250` i ±1⅔ EV: aproximadament
  `1/4000, 1/1250, 1/400`;
- totalitat, base `1/125` i ±3 EV: aproximadament
  `1/1000, 1/125, 1/15`;
- totalitat, base `1/30` i ±3 EV: aproximadament
  `1/250, 1/30, 1/4`;
- totalitat, base `1/8` i ±3 EV: aproximadament
  `1/60, 1/8, 1 s`.

La prioritat de buffer indicada per Pere es conserva: grup dens abans de C2,
màxima densitat durant totalitat i grup dens immediatament després de C3. Els
canvis de base han d'anar fora de cada bloc dens i només amb una finestra
`Q[g]` qualificada per al nombre de grups `g` acumulats.

L'aprenentatge transferit de l'A7RIIIA és metodològic:

1. blocs de configuració fixa en la zona crítica;
2. comptar fitxers reals, no ACK de press;
3. trobar el màxim repetidament verd;
4. reservar com a mínim un grup complet per sota d'aquell màxim;
5. aturar al primer dèficit, Busy o trigger ambigu;
6. verificar cada grup amb ledger, delta SD, hash, integritat i EXIF.

Els números Sony —0,75 s, 4×9, drenatges o cua `d215`— **no són números Canon**.
La 6D card-only no exposa telemetria de cua equivalent.

### Pic de buffer després de C3: definició verificable

Sense telemetria de cua no es pot observar ni certificar `BUFFER_FULL` en viu.
El màxim científicament honest és:

- `PEAK_ENVELOPE_SCHEDULED` mentre corre la seqüència;
- `PEAK_ENVELOPE_CONFIRMED` només si el postflight troba exactament tots els
  CR2 consecutius, íntegres, amb ordre AEB, hashes i correlació ledger;
- mai interpretar el primer trigger rebutjat com una mesura vàlida de «ple».

El planificador offline
`controller/tools/plan_canon6d_c3_buffer_peak.py` exigeix valors físics del
mateix cos, targeta, format i història: mida del bracket `p`, període `P`,
offsets de cada exposició `u[j]`, final de grup `u_end`, posició del highlight i
màxim repetidament verd `G_ok`. Per un pic desitjat `delta` després de C3:

```text
S_last = C3 + delta - u_end
S_k    = S_last - (G - 1 - k) * P
H_last = C3 + delta - (u_end - u[h])
```

Amb reserva, `G = G_ok - 1`; amb la petició literal de Pere de tocar el límit,
`G = G_ok`, però l'eina ho etiqueta explícitament
`qualification_boundary_no_margin`. En cap cas ho presenta com a producció
qualificada abans de tres repeticions completes i el gate CR2 posterior.

El planificador produeix àlgebra i JSON; el compilador offline separat usa ara
un flux no circular. Stage A pot crear el perfil lab de tota la història amb
un recompte `G_TRIAL_NOT_G_OK_TAIL`, sense afirmar capacitat. Només després
d'un run i card-gate verds un certificador revalida semànticament els quatre
artefactes i pot emetre evidència `G_ok_tail`; Stage B exigeix aquesta
evidència per compilar la cua final amb reserva. Cap d'aquestes eines pot
inventar els inputs físics que falten. A més, els temps EXIF permeten estimar
intervals relatius dins del grup, però no hi ha un calibratge demostrat entre
el rellotge EXIF Canon i el target monotònic del press. Per prometre dècimes
respecte de C3 cal mesurar l'offset absolut `u0` o declarar-ne la incertesa.
Finalment, el límit útil és `G_ok_tail`, qualificat amb la mateixa història
prèvia C2-C3; un `G_ok` obtingut amb el buffer buit no és transferible al pic
final.

L'extractor offline aplicat als vuit trets Single dóna offsets nominals
press-dispatch->EXIF de 0,85 a 0,92 s, mitjana 0,86875 s. Com que no hi ha bound
mesurat entre el rellotge Canon i el host, l'artefacte queda explícitament
`TIMING_NOMINAL_CLOCK_ALIGNMENT_UNBOUNDED`, `physical_qualification_granted=false`.
Tampoc calcula `P` ni `u_end`: cada acció Single només té una imatge. És
evidència útil de disseny, no precisió física promesa
(`.../20260801T151725_canon6d_lab_aeb_single_v1_canon-card-gate/timing_evidence.json`).

Una sola cadència uniforme tampoc pot maximitzar simultàniament cobertura i
pic. Per cobrir `C3-8,75...C3+5` cal `(G-1)P >= 13,75 s`; amb cinc grups això
força `P >= 3,438 s`, massa relaxat per tensar el buffer per dècimes. La
coreografia executable ha de tenir dues capes amb la mateixa configuració
fixa: grups espaiats que cobreixen els highlights dels contactes i un bloc
terminal dens que acaba després de C3. `G_ok_tail` s'ha de qualificar amb tota
la primera capa ja executada; no es pot trasplantar el límit d'un buffer buit.

### Arquitectura preferida per robustesa, encara provisional

La via més prometedora és eliminar la classe de fallada coneguda: configurar
Image review, AEB, Drive i una obturació base **abans del primer RAW**, i des
d'aquell moment fins fora de la finestra científica enviar només parelles
`Press Full MF`/`Release Full`. Les captures s'han d'agrupar en cicles AEB
complets; cap canvi d'obturació, AEB, ISO o Drive entre C2 i C3, i restauració
manual o diferida fins després de C4 si no hi ha un `Q_restore` físicament verd.

Un candidat de laboratori `1/250 ±3 EV`, ISO 100, cobriria nominalment prop de
`1/2000, 1/250, 1/30`: és robust davant el defecte dels setters i conserva
highlights més corona mitjana, però només cobreix uns 6 EV. No substitueix els
aproximadament 12 EV de l'escala ampla de Mazatlán ni està qualificat
fotomètricament. S'ha de comparar amb una opció més coronal i amb l'HDR ampli
en A/B solar abans d'escollir-lo.

`Continuous` és una optimització posterior, no el baseline: Single ja ha
demostrat el cicle i la fase. Falta resoldre, abans de cap RAW, la transició de
Drive sense canviar-la mentre AEB és actiu; després cal provar que una sola
pressió Continuous produeix exactament un grup complet, sense parcials ni
extres.

## Optimitzacions offline implementades

- `busy_retries` explícit i limitat per als setters de qualificació; els
  perfils Canon lab usen zero.
- Contracte lab: només `--qualification-run`, sense mission-first, recovery,
  autofix ni replay, i stop al primer error.
- Fail-fast real abans de qualsevol mutació o captura posterior, tant si el
  setter fallit és ambigu com si és un rebuig net.
- El gate causal `quiet` conserva un restore diagnòstic amb zero retries i
  espera de readiness; el floor de 30 s és conservador i lab-only. Els perfils
  AEB fixos no recorden ni restauren cap configuració post-RAW.
- El generador ja no accepta un quiet gap implícit de 6,2 s; exigeix un valor
  experimental explícit.
- El generador pot preparar una única autocorrecció `Image review=None` abans
  del trigger, sense remember, retries ni restore; el gate físic ha demostrat
  que el cos actual la rebutja i, per tant, no és una substitució del canvi
  manual.
- Els perfils AEB Single, AEB Continuous i buffer fix convergeixen AEB, Drive
  i obturació al preflight persistent amb `remember=False`; `configure=[]`, el
  cleanup no els restaura i, després del primer RAW, la timeline només conté
  grups `held_capture`. La branca `buffer+quiet+setter` queda separada com a
  diagnòstic, no com a camí preferit C2-C3.
- El camí de `Press Full MF` i `Release Full` força zero Busy retries dins de
  la sessió gPhoto, encara que la comanda física comenci per `set-config`.
  Això tanca un possible replay heretat del retry genèric dels setters.
- Una fallada de captura en un perfil lab puja directament: no entra a recovery
  de transport ni consumeix el retry precommit del camí de missió. El contracte
  `no_post_capture_config_writes` i l'auditor card-only rebutgen qualsevol
  setter, restore o retry posterior al primer press en els perfils AEB fixos.
- Planificador C3 fail-closed que calcula grups complets, cobertura de la
  finestra `C3-8,75...C3+5`, pic posterior, recompte CR2 i reserva; prohibeix
  l'etiqueta `BUFFER_FULL` i exigeix verificació posterior exacta.
- Perfil AEB Single materialitzat i **executat físicament** a
  `controller/runs/codex_20260801_canon6d_optimization/profiles/canon6d_lab_aeb_single_base1_250_v1.json`:
  base provisional 1/250, ±3 EV i vuit presses espaiades. El gate ha descobert
  l'ordre físic, i un perfil v2 posterior n'ha completat la fase. SHA-256
  `dbf8c52fca70b7c2cfc9bafbaa4e650a7bd7b2bfdfa7cd742f919939869a036c`.
- El validador separa ara el menú PTP Canon de l'ordre CR2: per una acció
  `native_bracket`, `expected_shutter_menu_values` ha de ser exactament la base
  del preflight, mentre `expected_shutters` conserva les tres exposicions que
  el gate card-only ha de trobar. La protecció és específica del backend Canon;
  Sony conserva la cardinalitat anterior.
- Bundle immutable de transició Drive preparat a
  `controller/runs/codex_20260801_canon6d_optimization/profiles/canon6d_drive_transition_preflight_bundle_v1/`:
  tres perfils `preflight_only` per AEB off, Drive Continuous i AEB +/-3.
  Cada stage té un únic setter amb `max_attempts=1`, `busy_retries=0`, zero
  captures/timeline/restore, i `run`/`drain` fallen abans d'obrir PTP. El
  manifest té SHA-256
  `1c4c1659bc4be5d02e813729b6818bf90aff2ab2656b429f939c48b4085773cc`;
  el guard de 7,0 s és lab-only i no Q-qualificat.
- Després de la política ISO operativa, els bundles cold-start **v1**–**v4**
  es conserven immutables, però queden quarantinats. Els manifests són,
  respectivament,
  `66d6b1de586a4cc06a87c9e317cfde97366800284ca82a69915307a7400237de`,
  `cc9b9144abfb55f5834fc642066ec930f304325924eb9da96177a04090009c59` i
  `0ddeadd844b26192800f6b9f4ed7b660865ade97cebafe1a47c00c608359e6f2` i
  `f4619e4b9fe789514529b4d34cfb39e13fdca2573cd62a411864c62044836c3f`.
  v1/v2 pinen dependències antigues; v3 encara tenia un TOCTOU entre el valor
  preflight cachejat i el valor viu anterior al write, i mission-first podia
  degradar el gate a warning. V4 ho va corregir, però els SHA només eren al
  manifest extern i una invocació directa d'un stage podia saltar-se el gate
  de dependències. **No s'han d'executar.**
- El substitut immutable **v6** incorpora quatre stages —AEB off, obturació
  `1/250`, Continuous i AEB `+/- 3`— i pinna el controlador
  `b5df9d9bdbd6a973df0630f93207afac6bfefb1021b1a9535c019ea29f72a4c3`
  i el perfil Canon
  `13b8fea1f0abd980e145a7f395152834f1927f8de4be7339ff2500996679f37c`.
  Cada stage porta un `runtime_dependency_binding` que el controlador valida
  abans de qualsevol mode o PTP. Revalida també el valor viu dins del setter
  abans del no-op, índex o write; una
  precondició divergent és `ConfigWritePreconditionError` dur, també sota
  mission-first. Cada stage manté ISO 100 exacta, zero captures/timeline/
  restore/replay, `max_attempts=1`, `busy_retries=0` i com a màxim un write.
  Manifest:
  `c74f86f3e97597e4a72a927c3faf7d15666f46a5633a9b94437dedaab8a026ec`.
  És preparació offline; no qualifica físicament el cold-start ni el guard
  interstage de 7,0 s.
- El perfil lab preconfigurat **v6** per un únic grup Continuous pinna les
  mateixes dues dependències i exigeix exactament `1/250`, AEB `+/- 3`, Drive
  Continuous i ISO 100. Té `auto_configure=[]`, `configure=[]`, només una
  `held_capture`, zero setters/restore/recovery/replay i SHA-256
  `fd30acf73caad2c67625037808087d8b82fd3018ad57d4133eaf31632b798992`.
  v2–v5 queden quarantinats; v6 tampoc és qualificació física.
- Eina offline d'extracció temporal que lliga perfil, events, manifest,
  identitats, hashes i mapa acció->fitxers. Manté `null` qualsevol bound no
  demostrat i no confon dispatch PTP, EXIF ni drenatge del buffer.
- Planificador/compilador C3 Stage A/B: Stage A només emet
  `G_TRIAL_NOT_G_OK_TAIL`; el certificador torna a llegir i validar pla,
  perfil, run i card-gate, rebutja runs vermells encara que es rehashegin i
  lliga ISO, mirror, review, modes, storage ID i identitat física de targeta.
  Stage B només programa cobertura espaiada més cua densa amb grups AEB
  complets, zero setters post-RAW i evidència `G_ok_tail` de la mateixa
  història. Encara no existeix cap Stage B físic perquè falten Continuous,
  `P`, offsets, identitat SD i `G_ok_tail` verds.
- El controlador produeix `timeline_clock_bridge.json` abans de gphoto2,
  lock o PTP per als perfils full-history. Card-gate i planner reobren els
  mateixos bytes i comproven les dues mostres `ntp_gettime`, l'àncora
  UTC/monotònica, els events i els fingerprints. Els runs antics sense aquest
  sidecar no es poden promoure retrospectivament. El Mac és `TIME_OK`, però la
  cota observada continua per sobre dels 50 ms requerits per l'Stage A actual.
- Eina card-only amb firewall de comandes, manifest pre/post, delta exacte,
  descàrrega nominal, SHA-256, estabilitat de targeta i correlació amb ledger.
- Subordre card-only `inspect-existing`: només accepta carpeta canònica i nom
  CR2 exacte ja presents en un manifest estable; verifica identitat, hash,
  EXIF i payload, repeteix inventari i etiqueta el fitxer com a preexistent no
  atribuït, sense ledger ni qualificació física.
- Reconciliació fail-closed del cas `scheduler_readiness_rejection`: exigeix
  un únic press/release i CR2, zero setter PTP, forma d'error exacta, cleanup
  verd i cap recovery; només tanca el fitxer, no el timing ni el run.
- Correcció del calendari quiet/buffer diagnòstic: el setter estàtic reserva
  `worst_case_s + quiet_gap_s`, no només `hold_s + quiet_gap_s`. El perfil v3
  a 7,12 s s'ha executat físicament una vegada i ha quedat vermell per
  `0x2019`; la correcció del scheduler és vàlida, però el timing no queda
  qualificat.
- Inspector CR2 amb capçalera/versionat, offsets RAW, bounds de payload i
  metadades de cos/temps.
- `mission_capture_blocked_reason` al perfil viu; el materialitzador i el
  controlador fallen abans de PTP/armament. La GUI 0.6.6 mostra ara
  `PROGRAM BLOCKED`, no compta la 6D al botó START i conserva l'exclusió amb
  motiu i identitat a `launch_spec.json` i `mission_result.json`; la resta de
  canals continua mission-first.
- Missatge manual d'identitat corregit: `--auto-detect` i el port no són
  identitat.
- Protocol d'alta corregit: timer històric sense mirror lock simultani i
  6,0/6,2 s refutats amb `Hold`; 7,012 s també refutats amb `None`.

La regressió completa després del hardening de la ladder és **793/793** verda.
El conjunt dirigit card-gate/planner/compiler/certificador C3 és **89/89** verd i
la unitat
runtime/cold-start/preconfigured és **79/79** verda, amb 9/9 proves específiques
del binding executable. El verificador immutable v6 és verd. Aquestes proves
de software no qualifiquen Continuous, buffer, canvis d'obturació, precisió
UTC ni cap perfil físic; el perfil quiet v3 continua físicament vermell.

## FALTA

1. Un **power-cycle físic posterior a l'últim Busy d'AEB**. El cicle que Pere
   ja va fer és anterior als RAW AEB i al rebuig d'apagar AEB 2.974,183 s més
   tard; no neteja aquest estat posterior. També cal absència estable de la GUI
   externa i de qualsevol client PTP abans d'obrir la sessió Canon.
2. Executar físicament el bundle cold-start **v6** de quatre stages: AEB off,
   obturació `1/250`, Drive Continuous i AEB `+/- 3`, amb readback, com a màxim
   un write per stage, zero retries i cap captura/restore. Els perfils offline
   no qualifiquen el gate ni els 7,0 s.
3. Un grup AEB Continuous, repeticions i prova que la durada de la pressió no
   crea grups parcials o extra. Single `p=3`, ordre i fase zero ja estan
   demostrats; no s'han de tornar a descobrir.
4. Optimització del hold en dècimes i del període amb dos grups: 3,0 -> 2,0 ->
   1,5 -> 1,25 s, sempre aturant al primer dèficit o extra.
5. Escala de buffer per grups complets i valor `G_ok`; producció com a màxim
   `G_ok - 1 grup`.
6. Delta SD exclusiu, hash, integritat i EXIF de tots els CR2 de cada gate.
7. Calibratge de l'offset absolut press monotònic→EXIF i execució de Stage A;
   no confondre el pla/perfil candidat `G_TRIAL` amb capacitat qualificada.
8. Certificar `G_ok_tail` amb exactament la mateixa història fosca C2-C3 i
   identitat SD, compilar Stage B de dues capes —cobertura espaiada i bloc
   terminal dens— i després fer el run simultani.
9. Mesura de `Q[g]` només si es manté una branca opcional amb setters post-RAW;
   no assumir un `Q` universal ni extrapolar-lo de 7,012 s.
10. A/B solar/òptic del diamant, perles i escala coronal.
11. Cable-pull, canvi de bateria, rellotge intern i prova Linux si s'utilitzarà
    aquell host.
12. L'app 0.6.6 actual ja incorpora el controlador v6, QtTextToSpeech i el
    bloqueig `PROGRAM BLOCKED`, i ha passat QA portable. Això no arma ni
    qualifica la Canon: després de completar i promoure els gates físics encara
    caldrà reconstruir-la de nou amb el perfil de producció final.

## ORDRE DE GATES per reprendre

1. **Dependència manual única:** apagar i encendre físicament la 6D després de
   l'últim `0x2019`. No és una nova autorització de software; és l'única acció
   corporal que l'agent no pot substituir.
2. **Exclusió de clients:** GUI externa absent de manera estable durant un
   cicle periòdic complet; zero Eclipse Command, gphoto2, controlador, hosts,
   workers o reconciliació. Cap replay dels writes rebutjats.
3. **Stage 1 cold-start v6:** lectura estricta de model/sèrie, firmware,
   mirror 0, review None, M, MF, RAW, ISO 100, targeta, bateria i espai; després
   convergir només AEB a off sota la doble precondició cachejada+viva.
4. **Stages 2–4 v6:** convergir successivament `1/250`, Drive Continuous i
   AEB `+/- 3`, un únic setter possible per stage, readback, zero retries,
   recovery, captures o restore; guard lab de 7,0 s i hard stop al primer error.
5. **AEB Continuous preconfigurat v6:** un únic grup amb `p=3` conegut i fase
   zero demostrada, sense cap write; després repeticions idèntiques.
6. **Hold i període:** reduir hold en dècimes; després dos grups a 3,0, 2,0,
   1,5 i 1,25 s. Conservar un marge de 0,1 s sobre el mínim repetidament verd.
7. **Buffer tail-only:** 1, 2, 4 i 5 grups a configuració fixa, sense setters;
   sis només com a frontera explícita. Exigir grups complets i delta exacte;
   determinar `G_ok` i reservar un grup.
8. **Mesurar offsets i planificar C3:** obtenir `P`, `u[j]` i `u_end`, calibrar
   l'offset absolut press monotònic→EXIF i executar el perfil Stage A amb tota
   la història prèvia. Només el certificador verd pot convertir el candidat en
   `G_ok_tail`; Stage B compila llavors cobertura espaiada + bloc terminal dens.
   Reserva d'un grup per producció o zero reserva només com a gate de frontera.
9. **Branca adaptativa opcional, buffer + setter:** només amb una decisió
   explícita diferent i un disseny de gate nou; el perfil quiet v3 no s'ha de
   repetir. Si es conserva, mesurar `Q[g]` per cada `g`, sempre amb zero retries
   i sense continuar després d'un Busy. La branca fixa preferida no té setters
   dins C2-C3 i difereix tota restauració.
10. **Coreografia Canon fosca:** blocs densos abans de C2, durant totalitat i
    després de C3; cap setter dins del bloc dens; manifests, CR2 i correlació
    complets. El pic es diu `PEAK_ENVELOPE`, mai `BUFFER_FULL`.
11. **Simultaneïtat:** repetir amb els altres canals sense copiar-ne els
    números ni permetre competència PTP.
12. **Solar/òptic i promoció:** A/B del diamant amb àncora `1/4000`, escala
    coronal, focus, filtre i tren reals; només llavors treure el blocker,
    marcar timing qualificat, reconstruir el bundle i fer QA complet.

## Estat de tancament d'aquesta campanya

- Campanya física: `Image review=None`, AEB Single `p=3`, ordre
  `1/250 -> 1/2000 -> 1/30` i fase zero demostrats. El pas a Continuous s'ha
  aturat perquè l'únic write Drive amb AEB actiu ha rebut `0x2019`.
- Continuous/buffer/coreografia: no executats i no qualificats.
- Cos segons l'últim preflight físic: `reviewtime=None`, `1/250`, AEB +/-3,
  Drive Single, fase zero, mirror 0, M/MF/RAW/ISO 100/Memory card i bateria
  50 %. El write Drive va ser rebutjat netament; zero trigger, cleanup verd i
  cap procés viu.
- Targeta: setze CR2 fins a `IMG_2310`; els nou CR2 de la descoberta i
  normalització AEB són íntegres i correlacionats amb els ledgers. Cap CR2
  pendent conegut després del preflight Continuous, que no va disparar.
- Perfil de missió: bloquejat fail-closed.
- Perfil i GUI font: exigeixen Image review None; el bundle 0.6.6 està
  reconstruït i fa visible el blocker com `PROGRAM BLOCKED`. No presenta la
  6D com a READY ni li crea worker mentre el blocker sigui viu.
- Perfil quiet corregit v3: calendari validat offline, executat una sola vegada
  i físicament vermell per `0x2019`.
- Cold-start v6: quatre stages `preflight_only` amb binding executable,
  materialitzats i verificats offline; no executats físicament. Manifest
  SHA-256
  `c74f86f3e97597e4a72a927c3faf7d15666f46a5633a9b94437dedaab8a026ec`.
- C3: flux Stage A/certificació/Stage B implementat i fail-closed; no hi ha
  perfil Stage B real perquè falten Continuous, identitat SD, `G_ok_tail` i
  una observació UTC estructurada del mateix run. Els manifests antics no es
  poden completar retrospectivament.
- SERIAL_WRITES: adquirit per aquesta unitat offline i pel rebuild GUI; zero
  processos Canon/PTP/gphoto2 al checkpoint posterior. El power-cycle físic
  posterior a l'últim Busy continua pendent i no es pot inferir d'un run que
  no va crear cap canal Canon.
- Regressió offline final: controlador 793/793, focal ladder/card-gate/C3
  111/111, C3 89/89 i binding/bundles 79/79 + 9/9; bundle v6 verify verd.
  La ladder exigeix ara baseline canònic v6, CR2 reoberts i reinspeccionats,
  identitat física SD i reconstrucció transitiva del predecessor. Cap d'això és
  qualificació física.

## Addenda append-only — trust root Continuous v7 fail-fast

Aquesta addenda no reescriu l'evidència v6 anterior ni converteix cap prova
offline en qualificació física. Després d'incorporar al controlador el
contracte d'obertura PTP fail-fast, el checkpoint executable viu és
`b9c4b28233350b225edaa4bbb09f3d6fb5d52fc7fc7c10ca5bf592e575f4421d`.

El nou baseline operatiu únic de la ladder és el G1 preconfigurat v7:

- path canònic:
  `controller/runs/codex_20260801_canon6d_optimization/profiles/canon6d_preconfigured_v7/canon6d_lab_aeb_continuous_p3_g1_cadence3_0_hold1_0_preconfigured_v7.json`;
- SHA-256:
  `887da805d3c66eeb0ff75f459b12f672080a5f26886774095ed7204c660dc7dd`;
- coreografia física conservada: un grup Continuous, `p=3`, hold `1,0 s`,
  ordre `1/250 -> 1/2000 -> 1/30`, zero setters, recovery o replay;
- diferència de seguretat: `lab_execution_contract.ptp_open_max_attempts=1`.

El builder emet aquest límit en cada rung i el verifier, el certifier i el
card gate el tornen a exigir. El primer `-110`, timeout o error transitori
d'obertura és terminal per al run; no hi ha segon intent d'obrir PTP.

El G1 v6 amb SHA
`fd30acf73caad2c67625037808087d8b82fd3018ad57d4133eaf31632b798992`
continua immutable i auditable. El card gate el pot reobrir exclusivament per
verificar evidència històrica, amb el rol explícit
`historical_v6_audit_only`; el certifier no l'accepta com a baseline i cap
bundle nou pot heretar-lo com a trust root.

Per tant, l'ordre operatiu actualitzat és: cold-start v7 verd, tres parelles
G1 v7 run/card-gate verdes sobre la mateixa `media_identity`, certificació
baseline v7 i només després construcció dels rungs hold/cadència/buffer. La
precisió UTC de Stage A continua sent un gate separat: aquesta migració no la
qualifica ni l'eludeix.
