# R6 Mark III: gate per variar l'obturació base durant totalitat

Data: 2026-08-05

Estat: `LAB GATE REQUIRED`; no activat al perfil de missió.

## Diagnòstic del run 12:22

El run
`20260805T122248_candidate_r6m3_vsd90ss_cfexpress_cardonly_v1_run`
completa 40/40 grups AEB3, 120/120 commits esperats, zero skips i zero
warnings de cronologia. La millora de prioritats posa grups a C2
−5,4/−2,7/0,0 s i C3 −1,4/+1,3/+4,0 s.

Pere ha observat correctament que la base no canvia: és 1/320 durant tot el
run. Cada press genera només la tríada nativa 1/2500, 1/320 i 1/40. El perfil
actiu ho fa expressament perquè el gate físic G40 va qualificar zero setters
després d'armar.

## Objectiu fotogràfic

Amb AEB ±3 EV, sis bases separades aproximadament 1 EV poden formar una
escala intercalada sense repetir cada velocitat:

`1/320, 1/160, 1/80, 1/40, 1/20, 1/10`

La unió teòrica cobreix exactament dotze literals únics observables entre
1/2500 i 0,8 s: les tríades separades 1 EV se solapen a ±3 EV. Els blocs de
contacte han de conservar 1/320 per prioritzar
perles de Baily i anells de diamant; les bases més lentes pertanyen només a
l'interior de la totalitat.

Això és un objectiu de gate, no una afirmació qualificada: cal mesurar
latència, Busy, adopció real, buffer, ordre EXIF i delta CFexpress al cos R6
exacte.

## Per què no s'activa directament

- Només s'ha demostrat físicament un setter d'obturació en preflight i en
  repòs, no entre grups AEB sota càrrega.
- Un write ambigu obliga a aturar només la R6 perquè l'estat físic deixa de
  ser garantible.
- Un Busy explícit `was not set` conserva la base anterior i es pot consumir
  sense replay de trigger, però pot fer perdre el bloc HDR previst.
- Activar setters no qualificats podria empitjorar just la zona C3 que el
  programa 0.7.11 acaba de protegir.

## Ordre de gates

1. **S0, setter-only:** tres cold starts; canvis
   1/320→1/160→1/80→1/40→1/20→1/10→1/320 amb readback individual, zero
   captures i cleanup net.
2. **S1, post-AEB:** un grup AEB3 a 1/320, espera mesurada, canvi a 1/160,
   readback i cleanup. Repetir tres vegades.
3. **G6:** un grup AEB3 per cada base, 18 CR3 esperats i delta CFexpress
   exclusiu +18; validar model, sèrie, ordre EXIF i velocitats reals.
4. **G40/H90 dinàmic:** 40 grups dins l'envelope de 90 s amb els canvis
   agrupats lluny de C2/C3. Exigir 120 commits, delta exclusiu +120, zero
   skips, zero replay i estat final conegut.
5. **Tres històries completes:** cold start, canvi de bateria i permutació de
   ports, sempre amb identitat PTP exacta.
6. Només després, promocionar el programa dinàmic com a físicament qualificat;
   el candidat offline pot materialitzar-se abans si conserva el perfil fix
   1/320 com a fallback reversible Mission First i mostra el deute sense
   convertir-lo en un gate global.

## Diagnòstic físic del primer candidat dinàmic

El run
`20260805T145506_candidate_r6m3_vsd90ss_cfexpress_cardonly_v1_run`
va materialitzar correctament 40 press AEB3, 120 RAW esperats i sis setters,
però només va executar els quatre primers grups (12 RAW esperats). El primer
canvi 1/320→1/160 es va intentar a C2+2,365 s, 2,38 s després del press
anterior, i el cos va respondre literalment `PTP Device Busy / was not set`.

El setter body-specific va classificar correctament aquesta resposta com a
no-adopció neta i va conservar 1/320 conegut. El wrapper de timeline, en
canvi, va confondre el commit de la línia PTP amb un write físic ambigu, va
marcar l'obturació com a desconeguda i va avortar el canal. La reconnexió
read-only posterior va confirmar 1/320 i identitat exacta aproximadament
5,35 s després del press. Per tant, la pèrdua de 36 grups és una regressió de
Mission First demostrada al wrapper, no evidència que el cos hagués adoptat
un shutter indeterminat.

## Implementació offline candidata revisada

La font viva materialitza aquesta escala només quan C2-C3 dura almenys
98,7 s. El cas canònic de 98,8 s conserva els 40 press AEB3 i hi intercala
sis setters agrupats abans dels grups 5, 12, 19, 25, 31 i 37. Cada transició
reserva 5,95 s; els altres 28 intervals de totalitat queden a 2,204 s, per
damunt del gap G40 de 2,20 s. El setter es programa 0,5 s abans del grup
següent i no es pot intentar fins a 5,4 s després del press anterior. El
darrer restaura 1/320 abans del bloc C3. Per sota de 98,7 s, el compilador
conserva sense cap setter el programa G40 fix a 1/320.

Un `Busy / was not set` no tanca la sessió, no activa reconnexió, no marca
l'estat desconegut i no repeteix el write: degrada només aquell setter i les
captures futures continuen amb l'última base confirmada. Un error post-write
realment ambigu conserva el hard stop exclusiu de la R6.

Això és DEMOSTRAT només per QA offline: materialització exacta, auditoria de
deadlines, dependències, fallback Mission First i reconeixement anti-tamper.
No promociona els setters dinàmics a evidència física. El run fallit només
demostra el Busy primerenc i el bug de classificació; encara no substitueix
S0, S1, G6, G40/H90 ni les tres històries completes anteriors.

## Regles Mission First del gate

- Cap trigger ambigu es repeteix.
- Busy net d'un setter no es converteix en trigger ni en replay; es registra
  i es conserva el valor anterior conegut.
- Estat desconegut després d'un write, identitat/propietat divergent o ledger
  no garantible aturen només la R6.
- Les altres càmeres continuen sempre.

## Evidència física nova: run 15:56

El run
`20260805T155615_candidate_r6m3_vsd90ss_cfexpress_cardonly_v1_run`
va executar quatre dels sis setters planificats. Tots quatre van llegir
`Shutter Speed` com a writable, amb valor actual `1/320`, i tots quatre van
rebre literalment `0x2019 PTP Device Busy / was not set`. El primer setter es
va enviar aproximadament 5,46 s després del press anterior, però el hold dura
1 s: el marge real des del release era només d'uns 4,46 s. Per tant, el bound
de 5,4 s ancorat al press queda refutat per aquest context i no es pot
promocionar.

Mission First sí va funcionar: cada Busy net va conservar `1/320`, zero
replay i les captures futures van continuar. Pere va demanar Stop després del
press 28; la manca dels grups finals és una aturada d'operador, no una
supressió automàtica. El ledger suma 84 RAW esperats, però no hi ha manifest
CR3 pre/post reconciliat; ni el ledger, ni els ACK, ni `Available Shots` són
prova física de 84 RAW.

## Gates S0/S1 revisats després del run

La font inclou perfils lab generats de forma determinista per
`controller/tools/compile_r6m3_shutter_readiness_gate.py`. No són perfils
visibles ni autoritzen contacte físic per si sols.

1. `S0-A`, opcional perquè A2 ja aporta un precedent diferent: Single, AEB
   off, zero captures, cicle `1/320 -> 1/160 -> 1/320` amb dos writes.
2. `S0-B`: Continuous high speed, AEB +/-3, zero captures, el mateix cicle de
   dos writes. Si falla, el lock depèn del mode i no del buffer post-captura.
3. `S0-C`, només si S0-B falla: AEB off, canvi i restore de shutter, AEB on;
   quatre writes, zero captures. Discrimina si cal un cicle AEB body-specific.
4. `S1`: un sol press AEB3 i un sol setter `1/320 -> 1/160`, ancorat al
   release real. Com que 4,46 s ja ha fallat, l'escala comença a 6 s i només
   continua a 8 i 12 s fins al primer PASS. Cada intent exigeix manifest
   CFexpress exclusiu +3 i inspecció dels tres CR3; cleanup restaura 1/320
   només després d'una adopció demostrada.

La primera execució `dry-run` d'S1 va detectar abans de tocar la càmera una
superposició de 50 ms: el target release+delay coincidia amb el límit de
`config_ready`, però l'auditoria estricta també reserva la tolerància del
capture. El worker R6 ara tracta aquest cas com un handoff acotat i espera
explícitament fins a `config_ready_until_ns`; la tolerància només pot retardar
el setter, mai avançar-lo dins la finestra Busy. S0-B i S1 6/8/12 completen
`dry-run` amb el worker real. Això demostra compilabilitat i ordre temporal
offline, no adopció física del shutter.

Amb el gate físic G40 actual, cinc grups parcials deixen un màxim qualificat
de 35 grups/105 RAW dins C2-C3. Mantenint aquests 35 grups i el gap G40 de
2,2 s, un PASS S1 a 6, 8 o 12 s permetria com a màxim 4, 3 o 2 transicions,
respectivament. És només capacitat offline: el nombre i les bases finals no es
promocionen fins que S0/S1 acreditin l'adopció i després G6/G40-H90 acreditin
els CR3, timings i estat final.

## Evidència física S0-B: PASS

El run
`20260805T173647_lab_r6m3_s0b_continuous_aeb_on_shutter_readiness_v1_run`
ha completat físicament S0-B amb la R6 III exacta, `Continuous high speed`,
AEB +/-3, RAW a CFexpress i base inicial 1/320. Amb zero captures ha adoptat
`1/320 -> 1/160` i `1/160 -> 1/320`, sempre amb un únic write i readback
exacte. Els temps totals observats han estat 432,222 ms i 427,902 ms,
respectivament; tots dos inclouen 400 ms de settle conservador. El cleanup ha
confirmat de nou 1/320, AEB +/-3 i identitat exacta. No hi ha Busy, recovery,
skips, replay, estat desconegut ni error de cleanup.

El certificat immutable
`controller/evidence/r6m3_shutter_readiness_certificates/20260805T173647_s0b_continuous_aeb_on_pass.json`
té SHA-256
`9e3760ae01c2d3b1287d40a7e9058e65fb89ddeb441de29ca8de8b5c4fb64191`
i estat `S0_MODE_DISCRIMINATOR_PASS`. Certifica només aquest discriminator
setter-only: no demostra adopció després d'un press AEB, materialització CR3,
G6, G40/H90 ni cap història C1-C4, i no autoritza promocionar el perfil públic.

Dos intents previs no són fallades del shutter. El primer es va aturar abans
de qualsevol mutació perquè l'encesa havia cancel·lat AEB. El segon va validar
model i sèrie però va perdre l'arbre `/main` mentre la càmera sortia del menú;
zero writes i zero captures. La interfície física es va recuperar en
desconnectar USB. Per tant, **DEMOSTRAT** és S0-B en pantalla normal;
**FALTA** S1 release-anchored amb +3 CR3 reconciliats; l'**ORDRE DE GATES**
continua S1 6/8/12 s fins al primer PASS, després G6 i G40/H90. Les seccions
següents registren que 6 i 8 s ja han fallat netament.

## Evidència física S1 release+6 s: FAIL de readiness, +3 CR3 PASS

El run
`20260805T174758_lab_r6m3_s1_release_6s_shutter_readiness_v1_run`
ha compromès un únic press AEB3 amb press i release reconeguts. El release
real queda ancorat a `66018207274208` ns monotònics. El write 1/320 -> 1/160
s'ha enviat una sola vegada a release+6,018203 s, després de llegir encara
1/320 writable, però el cos ha respost literalment
`0x2019 PTP Device Busy / was not set`. No hi ha hagut retry ni replay.
El cleanup ha confirmat release i shutter 1/320; `physical_state_unknown=false`.

Els inventaris complets pre/post passen de 921 a 924 fitxers i el delta
immutable
`controller/evidence/r6m3_cfexpress_deltas/20260805T174731_to_20260805T174837_s1_6s_exact_plus3.json`
acredita exactament `+3` CR3, zero removals i zero canvis de metadata visible:
`572A3353.CR3`, `572A3354.CR3` i `572A3355.CR3`. Els tres downloads
manifest-bound han conservat un inventari idèntic abans/després. Les tres
inspeccions ISO-BMFF/ExifTool passen amb model i sèrie exactes, RAW,
Electronic, `Continuous Shooting`, AEB `0,-,+`, `3 shots` i ordre físic
`1/320`, `1/2500`, `1/40` amb valors 0, -3 i +3 EV.

Per tant, **DEMOSTRAT** és un AEB3 card-only materialitzat i reconciliat amb
tres CR3 íntegres, i també que release+6,018 s encara és massa aviat per al
setter en aquest cos/context. **FALTA** el primer delay amb adopció física del
shutter. L'**ORDRE DE GATES** passa a S1 release+8 s; només si també falla,
S1 release+12 s. La frontera màxim-RAW de 6 s queda descartada físicament:
cap opció de 120 RAW C2-C3 es pot promocionar amb aquesta readiness.

## Evidència física S1 release+8 s: FAIL de readiness, +3 CR3 PASS

El run
`20260805T175453_lab_r6m3_s1_release_8s_shutter_readiness_v1_run`
ha compromès un únic press AEB3 amb press i release reconeguts. El release
real queda ancorat a `66433134618875` ns monotònics. El write 1/320 -> 1/160
s'ha enviat una sola vegada a release+8,002403 s, però el cos ha respost
literalment `0x2019 PTP Device Busy / was not set`. No hi ha hagut retry ni
replay. El cleanup ha confirmat release i shutter 1/320;
`physical_state_unknown=false` i `cleanup_ok=true`.

Els inventaris complets pre/post passen de 924 a 927 fitxers i el delta
immutable
`controller/evidence/r6m3_cfexpress_deltas/20260805T175419_to_20260805T175538_s1_8s_exact_plus3.json`
acredita exactament `+3` CR3, zero removals: `572A3356.CR3`,
`572A3357.CR3` i `572A3358.CR3`. Les tres inspeccions passen amb model i
sèrie exactes, RAW, Electronic, `Continuous Shooting`, AEB `0,-,+`,
`3 shots` i ordre físic `1/320`, `1/2500`, `1/40` amb valors 0, -3 i +3 EV.
El delta té SHA-256
`1d8929424f5122d96301bb05cdba045821104a6871172808cd2691c7b1358cbb`.

Per tant, **DEMOSTRAT** és un segon AEB3 card-only exclusiu materialitzat i
reconciliat, i que release+8,002 s encara és massa aviat per al setter en
aquest cos/context. **FALTA** el primer delay amb adopció física del shutter.
L'**ORDRE DE GATES** passa a S1 release+12 s amb autorització física fresca;
G6 no s'obre abans d'un PASS. La frontera de 114 RAW C2-C3 queda descartada
físicament: amb la readiness viva, el màxim candidat passa a 35 grups/105 RAW
dins totalitat i conserva els cinc grups parcials.

## Evidència física S1 release+12 s: FAIL de readiness, +3 CR3 PASS

El run
`20260805T180334_lab_r6m3_s1_release_12s_shutter_readiness_v1_run`
ha compromès un únic press AEB3 amb press i release reconeguts. El release
real queda ancorat a `66954221518125` ns monotònics. Després del readback
encara writable a 1/320, el write 1/320 -> 1/160 s'ha enviat una sola vegada
a release+12,018956 s. El cos ha respost literalment
`0x2019 PTP Device Busy / was not set`; zero retry i zero replay. El cleanup
ha confirmat release i shutter 1/320, `physical_state_unknown=false` i
`cleanup_ok=true`.

Els inventaris complets pre/post passen de 927 a 930 fitxers. El delta
immutable
`controller/evidence/r6m3_cfexpress_deltas/20260805T180320_to_20260805T180408_s1_12s_exact_plus3.json`
acredita exactament `572A3359.CR3`, `572A3360.CR3` i `572A3361.CR3`, zero
removals i zero canvis de metadata disponible. Les tres inspeccions passen
amb model/sèrie exactes, RAW, Electronic, AEB `0,-,+`, `3 shots` i ordre
físic `1/320`, `1/2500`, `1/40`. El delta té SHA-256
`a8eff04e27039f552758f7eef796ae6cee116794db63a07f4902fb974bb95d79`.

Per tant, **DEMOSTRAT** és un tercer AEB3 exclusiu materialitzat i que ni
release+12,019 s desbloqueja el setter dins la mateixa sessió. **FALTA**
discriminar si el bloqueig depèn de la cua d'events/capture-complete, de
l'estat de remote release o de la sessió PTP, no d'afegir una espera cega.
L'**ORDRE DE GATES** deixa d'allargar S1 i passa a un discriminator S2
específic R6, offline primer i físic només amb un únic trigger consumible.
G6 i qualsevol promoció dinàmica continuen tancats.

## S2 offline: drenatge explícit de la cua d'events Canon

Els tres S1 comparteixen una propietat important: dins la sessió persistent,
el worker fa press/release i després consulta/escriu `shutterspeed`, però no
executa cap `wait-event` entre el release i el setter. La documentació oficial
de control remot de gPhoto mostra el release Canon seguit d'una espera
d'events, i el codi font de libgphoto2 per Canon EOS consumeix la cua EOS quan
el client entra a `camera_wait_for_event`; entre els events processats hi ha
`CameraStatus=0`, que es publica com `GP_EVENT_CAPTURE_COMPLETE`.

Fonts primàries:

- https://www.gphoto.org/doc/remote/
- https://github.com/gphoto/libgphoto2/blob/master/camlibs/ptp2/library.c

Això no demostra encara que `CAPTURE_COMPLETE` sigui el lock exacte de la
R6 III; sí que autoritza un discriminator més informatiu que continuar
allargant una espera cega. El perfil generat
`lab_r6m3_s2_event_drain_2500ms_shutter_readiness_v1.json` conserva un únic
press AEB3 a 1/320, comença una única comanda `wait-event 2500ms` després de
la finestra fail-fast de la captura, prohibeix qualsevol payload local i
després intenta una sola vegada 1/320 -> 1/160. No usa
`wait-event-and-download`, no repeteix Busy, no recupera transport i el
cleanup manté el restore a 1/320.

El compilador, el validador, el dry-run del worker i el certificador offline
rebutgen qualsevol descàrrega local, ordre diferent, retry, replay o
promoció. El dry-run
`20260805T181755_lab_r6m3_s2_event_drain_2500ms_shutter_readiness_v1_dry-run`
completa les tres accions amb zero ordres de càmera i 3 imatges esperades;
el perfil té SHA-256
`8570195ca1f4674243b71f802a9b5b4373fe013d1fc69d7843be6f00caa4403f`.

**DEMOSTRAT**: S2 és compilable, schedulable i fail-closed offline, i no toca
el programa operatiu ni l'app. **FALTA**: provar si el drenatge fa writable
l'adopció física de 1/160, reconciliar exactament +3 CR3 i després acotar el
temps mínim. L'**ORDRE DE GATES** és una única execució física S2; només un
PASS obre l'optimització temporal, G6 i G40/H90. El pressupost conservador
actual implica un gap candidat de 6,2 s i, per tant, encara no cap dins el
gap operatiu offline de 5,95 s: no és un canvi de release ni una solució
Mission First demostrada.

### Setter directe després d'S1-12: Busy reproduït sense cap captura nova

A les 18:20 CEST, amb autorització explícita de Pere per provar només el
setter, una sessió interactiva nova de gphoto2 ha resolt una única
`Canon EOS R6 Mark III` a `usb:001,001`, ha llegit model
`Canon EOS R6 Mark III`, sèrie `[SÈRIE]` i shutter writable a 1/320.
Una única ordre
`set-config-index /main/capturesettings/shutterspeed=37` —on el menú viu
confirmava `Choice: 37 1/160`— ha rebut de nou
`0x2019 PTP Device Busy / was not set` i `-110 I/O in progress`. El readback
immediat ha confirmat 1/320; zero captures, zero retry i zero estat
desconegut.

Aquesta observació no és un certificat immutable ni un gate físic complet,
però separa el problema de la cronologia de l'app: fins i tot una comanda
manual nova és refusada en l'estat post-AEB actual del cos. Reforça la
hipòtesi de cua/estat Canon persistent i manté S2 com a pròxim discriminator;
no autoritza repetir cap trigger ni promocionar cap canvi de release.

### Causa arrel demostrada: `Release Full` deixa el half-press actiu

La inspecció del backend oficial libgphoto2 resol el significat exacte dels
literals. `Press Full MF` crida `ptp_canon_eos_remotereleaseon(..., 3, 1)`:
el `3` activa conjuntament half+full. En canvi, `Release Full` crida
`ptp_canon_eos_remotereleaseoff(..., 2)` i només allibera el full-press.
El literal `Release` crida `...off(..., 3)` i allibera tots dos nivells. El
mateix codi documenta com a seqüència típica sense AF
`Press Full MF -> Release`:

- https://github.com/gphoto/libgphoto2/blob/master/camlibs/ptp2/config.c#L7760-L7797

Pere ha confirmat la R6 encesa i ha autoritzat continuar el discriminator
setter-only. En una sessió nova, model `Canon EOS R6 Mark III`, sèrie
`[SÈRIE]` i 1/320 writable, una única ordre
`set-config eosremoterelease=Release` ha completat sense error. Immediatament
després, `set-config-index ...shutterspeed=37` ha adoptat 1/160 amb readback
exacte i Pere ha vist físicament el canvi a la pantalla. El restore amb
índex 40 ha retornat a 1/320 i el readback final l'ha confirmat. Zero captures,
zero retry i sessió tancada netament.

Per tant, **DEMOSTRAT** és que el Busy persistent era un half-press remot
deixat actiu pel contracte erroni `Release Full`, no el buffer, ni una espera
insuficient, ni la manca de `wait-event`. **FALTA** un únic AEB3 amb el
contracte corregit, adopció posterior de shutter i delta +3 CR3 reconciliat.
L'**ORDRE DE GATES** substitueix S2 per: migració body-specific R6 a
`release_value=Release`, QA offline, un AEB3 físic fail-fast i després
G6/G40-H90. El codi S2 no entra a cap release pública mentre sigui innecessari.

## Frontera RAW dins totalitat després d'S1

El G40 físic limita avui el programa a 40 grups totals, però no obliga que
cinc quedin fora de totalitat. Si la prioritat absoluta és maximitzar RAW
C2-C3 i es conserva el mínim dinàmic útil —un canvi fora de 1/320 i un restore
a 1/320 abans del contacte C3—, la frontera matemàtica body-specific és:

| PASS S1 des del release | Estat físic actual | Transicions | Grups/RAW màxims C2-C3 | Grups parcials conservables dins G40 | Slack de cronologia |
|---:|---|---:|---:|---:|---:|
| 6 s | FAIL Busy net | 2 | 40 / 120 | 0 / 5 | 1,0 s |
| 8 s | FAIL Busy net | 2 | 38 / 114 | 2 / 5 | 1,4 s |
| 12 s | FAIL Busy net | 2 | 35 / 105 | 5 / 5 | 0,0 s |

Si es prioritza més diversitat de bases i es conserven els cinc grups
parcials, els màxims continuen sent 4/3/2 transicions per 6/8/12 s i 35
grups/105 RAW dins totalitat. Les tres files es conserven només com a
auditoria de fronteres ja refutades: no són opcions de release. La font
operativa ha de conservar el fallback fix 1/320 fins que un mecanisme S2
diferent superi adopció, G6 i G40/H90.

Aquesta taula no autoritza encara cap materialització. Sacrificar captures
parcials exigeix una decisió explícita de release i reconciliació amb
Exposicions; les bases interiors i els brackets de fins a 0,8 s exigeixen G6.
Qualsevol opció exigeix després G40/H90 dinàmic, delta CFexpress/CR3 i tres
històries C1-C4. El compilador S0/S1 publica la frontera dins
`post_s1_totality_raw_frontier`, marcada `candidate_only=true` i
`operational_compile_ready=false`; l'app continua executant només el fallback
fix 1/320 sense setters.

## Tancament físic del contracte corregit: run 18:57

El run
`20260805T185716_candidate_r6m3_vsd90ss_cfexpress_cardonly_v1_run`
va executar el contracte corregit `Press Full MF -> Release` durant tota la
cronologia dinàmica. Va completar 40/40 grups AEB3, 120/120 commits esperats,
zero skips, replay, recovery, Busy o errors, i les sis transicions
`1/320 -> 1/160 -> 1/80 -> 1/40 -> 1/20 -> 1/10 -> 1/320` amb readback exacte.
Les sis adopcions van durar aproximadament 431–440 ms. Cleanup, restore i
release final van ser nets, amb `physical_state_unknown=false`.

Els hashes d'autoritat són:

- profile snapshot:
  `0472f3d0fd45afdd93d46574bde88a776cb070b1f39add2a301b619822f669f3`;
- run manifest:
  `ead7f3afb501b93d64759e53e492311bd26db02f7ccd2b676d61e30773cd1910`;
- events:
  `cc844eec093138c567a9737374061b1ebae1c955c5fad3a13cd29e0fe2c2d374`;
- result:
  `fc9d31b8f4de5fce0eb26b01b0953911aa8c44d67623f77211ac67907e1956c0`.

**DEMOSTRAT:** la causa arrel era `Release Full`; el contracte `Release`
allibera completament el disparador remot i permet els sis setters dinàmics
body-specific durant una història completa de 40 grups, amb ledger operatiu
íntegre. El bulk de configuració inicial només va exposar `Unknown 1900` i
`1/320`, mentre que la lectura explícita posterior va exposar les 58 opcions;
per tant, un menú bulk incomplet no pot vetar conservadorament un setter que
la consulta explícita i el readback exacte validen.

**FALTA:** el run és `card_only_committed`, no `card_only_verified`; no hi ha
manifest CFexpress exclusiu post-run ni inspecció dels 120 CR3. També falten
H90, les tres històries completes, tracking/òptica VSD90SS i ciència solar.
La nova cadència pública d'un AEB3 documental per minut a les fases parcials
encara no té endurance físic propi.

**ORDRE DE GATES:** manifest/CR3 exclusius del programa dinàmic; G40/H90 amb
el contracte corregit; tres històries C1–C4; després òptica i ciència. Aquests
deutes són informació de programa i no un `WARNING` operatiu ni un gate
global. Un Busy net conserva l'últim shutter conegut i totes les accions
futures segures; un write amb estat desconegut atura només la R6.
