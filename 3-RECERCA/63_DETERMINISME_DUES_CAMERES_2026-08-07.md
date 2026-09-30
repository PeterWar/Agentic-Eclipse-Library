# 63 — Determinisme a les dues càmeres: què el trencava i què s'ha corregit

7 d'agost de 2026, vespre. Encàrrec de Pere: runs deterministes a la R6 III i
a l'A7RIIIA que capturin perles de Baily i anells de diamant a C2 i C3, un
bracketing de corona amb moltes EV, i earthshine.

## 1. El punt de partida: el run multicàmera `20260807T210529`

Primer run amb les dues càmeres alhora i el programa nou de la R6. Estat
global `warning`.

| | Previst | Fet |
|---|---:|---:|
| A7RIIIA | 60 | **60 confirmats**, 27/27 accions, 0 saltades, 0 reconnexions |
| R6 III | 120 | **67 físics a la targeta**, 92 accions saltades, 20 reconnexions |

La R6 va perdre 39 fotogrames dins totalitat i 32 dels 54 canvis d'exposició.
Només va assolir 7 de les 15 velocitats previstes, i **70 fotogrames es van
disparar amb una base que no era la prevista, 44 d'ells a 0,5 s**. A la
totalitat això és corona cremada.

El delta CFexpress ho tanca sense ambigüitat: la targeta es va formatar just
abans del run i després contenia exactament **67 CR3** (`572A9196`–`572A9262`).
Els 87 «commits» del ledger eren optimistes; el que hi ha són 67.

L'error és sempre el mateix i torna **en 3 ms**, no és cap timeout:
`set-config eosremoterelease=Press Full MF` -> `-110: 'I/O in progress'`.

## 2. Què NO ho causava

| Sospitós | Per què cau |
|---|---|
| El codi | Mateix SHA del worker als runs bons i als dolents (`ec1fed67…`), repositori i bundle idèntics |
| La geometria | Tres runs de laboratori amb la geometria exacta (0,40/0,25) van fer 175/175 accions i 115 fotogrames, zero saltades |
| La cadència | A les 20:34 també va petar la geometria **lenta** (0,50/0,62) |
| El menú col·lapsat | Preflight sempre amb 58 opcions |
| La bateria | Va fallar a 81, 80 i 79 %, i va anar bé a 78, 77 i 76 % |
| La targeta | Va fallar amb targeta acabada de formatar i també amb targeta plena |
| La segona càmera | Els runs trencats de les 18:48 i 19:02 tenien **un sol cos al bus** |

## 3. Què sí que ho causa

Un **estat intermitent del transport USB de la R6**, per blocs de temps. La
signatura és la latència de pulsació:

| Run | Mediana | p90 | Màxim | > 80 ms |
|---|---:|---:|---:|---:|
| App 18:14 (bo) | 20,4 ms | 25,4 | 129,8 | 1 de 120 |
| Lab 20:37/20:41 (bons) | 19,4 ms | 23,7 | 46,0 | 0 de 115 |
| App 21:05 (dolent) | **114 ms** | **196** | **346** | **58 de 67** |

Als runs dolents la sisena pulsació seguida ja triga 130 ms i la setena rep el
`-110` a l'instant. Als bons, 101 intervals seguits de 0,40 s sense passar de
46 ms.

A les 22:08, durant una validació, **la R6 va desaparèixer del bus USB
sencera**: `USB_PHYSICAL_BLOCKED`, zero coincidències, només la Sony a
l'inventari PTP. Encaixa amb un enllaç USB marginal: bufades de `-110`,
períodes nets, i finalment la caiguda.

**Comprovació física pendent de Pere: cable i connector de la R6.**

## 4. Correcció 1 — un `-110` no pot costar una sessió sencera

`controller/eclipse_capture_r6m3.py`.

El classificador `is_camera_transport_loss` tracta el `-110` com a pèrdua de
transport i autoritza tancar i reobrir PTP. Amb l'alliberament d'emergència
que l'acompanya, la sessió queda `tainted` i el camí car és l'únic possible.
Cost mesurat: **0,9 s de reconnexió més dues o tres accions rebutjades per
tard**. Al run de les 21:05, 20 incidències es van menjar 53 fotogrames.

Ara, abans de refer la sessió, s'intenta `resync_live_transport`:

1. només si el procés del shell continua viu i l'excepció no és d'identitat
   ni de transport perdut de debò;
2. `recover_prompt` drena els límits de resposta pendents i envia un probe
   `get-config /main/status/cameramodel`;
3. una rellegida real de l'obturació demostra que la sessió PTP continua
   servint el cos, i s'adopta com a lectura dinàmica igual que ho faria una
   reconnexió;
4. pressupost dur de **300 ms**; si no hi arriba, es torna al camí car sense
   cap canvi de semàntica.

L'acció ambigua continua consumida i en quarantena. No hi ha replay, ni
identitat nova, ni ledger tocat. Només s'estalvia el que no calia pagar.

Validació: 1.075/1.075 proves del controlador. Al cos, el camí sa no es
degrada — 151 s de run amb la correcció posada van donar 65 fotogrames i 40
setters amb **zero incidències** i mediana de pulsació de 18,8 ms. El camí
d'error es va exercir una vegada, en una desaparició real del cos: va fallar
al probe en 0,31 s i va delegar correctament. **Falta exercir-lo sobre un
`-110` recuperable de debò**, que és el cas per al qual s'ha escrit.

## 5. Correcció 2 — la Sony perdia els dos anells de diamant

`gui/eclipse_command/adaptive_profiles.py`.

El tram `a7r3a_fixed9_buffer_pipeline_72_v2` col·locava els brackets de
contacte a **C2+0,0 / +2,9 / +5,8** i a **C3−6,0 / −3,1**. El comentari del
codi ho justificava dient que a C3−6 s «hi ha el segon anell de diamant».

Això és un error de física. A C2 el Sol ja és tapat: les perles i el primer
anell passen **abans** de C2. A C3 el limbe encara està tapat: el segon anell
surt **a C3 i just després**. El programa antic tancava l'obturador 0,23 s
abans del segon anell i el perdia sencer, i el bloc de C2 arribava sempre
tard al primer.

La conseqüència operativa és pitjor que la fotogràfica: **els dos anells
depenien només de la R6**, que és el canal que es degrada. Al run del 7
d'agost no en va quedar cap.

Ara els blocs travessen els contactes:

| | Abans | Ara |
|---|---|---|
| Bloc C2 | +0,0 / +2,9 / +5,8 | **−2,9 / 0,0 / +2,9** |
| Bloc C3 | −6,0 / −3,1 | **−2,0 / +0,9** |

Efectes col·laterals tractats explícitament:

- el drenatge posterior a C3 estava ancorat a C3+1,0 i hauria arrencat 2,8 s
  abans que s'alliberés l'obturador. Ara penja del final de l'últim bracket i
  conserva el traspàs d'1,229 s del pla qualificat;
- els tres passos de sortida (confirmació de selector, Single, base 1/400) es
  calculaven amb offsets fixos a C3 i l'auditoria estricta hi detectava un
  solapament de 3,07 s. Ara pengen del final del drenatge;
- la finestra d'earthshine es continua calculant contra una **reserva de
  6,0 s**, no contra la posició nova del bracket. Avançar-lo allibera 4 s
  reals, però gastar-los en una àncora més movia el llindar on una totalitat
  de 90 s deixa de fer brackets HDR i passa a fer earthshine. Aquest canvi
  només vol posar els contactes al costat correcte; el repartiment del mig es
  decideix a part.

## 6. Evidència física de la correcció 2

Run `20260807T222902`, A7RIIIA al cos:

- **60/60 fotogrames confirmats i descarregats**, 27/27 accions, zero
  saltades, zero reconnexions, drenatge, restore i cleanup nets, pla complet;
- moments reals: **C2−2,89 / +0,01 / +2,90** i **C3−2,00 / +0,91**;
- EXIF llegible als 60, **13 exposicions úniques de 1/4000 a 8 s** (15 EV) i
  les dues àncores d'earthshine de **8 s reals a ISO 100**.

## 6 bis. Determinisme demostrat amb les dues càmeres alhora

La R6 va tornar al bus a les 22:40 amb bateria al 54 %. Primer run sol del
perfil de missió amb la correcció posada, `20260807T224123`: **181/181
accions, 120/120 commits, delta CFexpress exclusiu +120**
(`572A9563`–`572A9682`), 62/62 setters, zero retards, una sola sessió.

Després, **dos runs multicàmera concurrents** amb els dos cossos disparant a
la vegada i els mateixos contactes, `20260807T224852` i `20260807T225500`:

| | Estat | Accions | Saltades | Recuperacions | Setters | Commits | Latència mediana/màx |
|---|---|---:|---:|---:|---:|---:|---:|
| R6 run 1 | complete | 181/181 | 0 | 0 | 61/61 | 120 | 20,5 / 50,3 ms |
| R6 run 2 | complete | 181/181 | 0 | 0 | 61/61 | 120 | 20,3 / 47,5 ms |
| Sony run 1 | 60/60 | 27/27 | 0 | 0 | — | 60 | 13 exposicions úniques |
| Sony run 2 | 60/60 | 27/27 | 0 | 0 | — | 60 | 13 exposicions úniques |

Delta CFexpress exclusiu **+120 als dos**: `572A9683`–`572A9802` i
`572A9803`–`572A9922`. Cap fotograma perdut, cap sessió refeta, cap
exposició no prevista. **Dos runs idèntics mètrica per mètrica és el que
volia dir determinisme.**

La segona càmera al bus no degrada la primera: la latència de pulsació de la
R6 amb la Sony disparant en paral·lel (20,5 i 20,3 ms de mediana) és la
mateixa que sola (18,75 ms), i molt lluny dels 114 ms del run trencat.

## 6 ter. Per què no s'ha estret la geometria de la R6

Mesura fresca del run `20260807T224123` sobre 61 setters: **mediana 27,96 ms,
p95 62,40, màxim 84,00**. La ranura és de 250 ms, o sigui **3× de marge sobre
el pitjor cas observat**. Baixar-la a 200 ms compraria uns set fotogrames de
120 i deixaria el marge a 2,4×, en una acció d'un sol intent i sense reintent
on un retard costa el fotograma i l'escaló d'exposició. Per un eclipsi
irrepetible és mal negoci i no s'ha fet.

Els 0,40 s entre fotogrames tampoc es toquen: són el terra de pulsació
sostinguda del cos —a 300 ms rebutja amb 21 `DEVICE_BUSY` sobre 12
fotogrames—, no un cost nostre.

El compilador, a més, refusa qualsevol geometria divergent abans d'escriure
el perfil (`R6 III AEB3 operational contract is absent or divergent`), que és
exactament el que ha de fer.

## 6 quater. Què passa si la totalitat no dura el que esperem

Pregunta de Pere: si passem de 1m41s a 1m00s, continuem tenint earthshine,
anells de diamant, perles i bracketing? Mesurat compilant els dos perfils a
totes les durades:

| Totalitat | R6 III | A7RIIIA |
|---|---|---|
| 40 s | 67 img, contactes ✓, 14,9 EV, 15 s | 28 img, contactes ✓, **0 EV**, sense earthshine |
| 60 s | 92 img, contactes ✓, 14,9 EV, 15 s | 38 img, contactes ✓, **6,1 EV**, sense earthshine |
| 80 s | 115 img, contactes ✓, 14,9 EV, 15 s | 54 img, contactes ✓, **6,1 EV**, sense earthshine |
| 90-104 s | 105-123 img, contactes ✓, 14,9 EV, 15 s | 51-65 img, contactes ✓, **15 EV**, 2-3 àncores de 8 s |
| 120 s | 141 img, contactes ✓, 14,9 EV, 15 s | 98 img, contactes ✓, **10 EV**, sense earthshine |

**La R6 és robusta a la durada**: de 40 a 200 s manté sempre els dos
contactes travessats, 14,9 EV i els fotogrames de 15 s. El programa es
dimensiona a partir de la durada i no canvia de caràcter.

**L'A7RIIIA no.** El seu tram bo tenia una finestra de 90 a 100 s i fora
d'ella queia a trams antics. El sostre de 100 **no descrivia cap límit
físic**: amb 98,8 s previstos, dos segons d'error a l'estimació feien caure
el cos a `dense_74`, que dona més fotogrames però **10 EV i cap àncora
d'earthshine** en comptes de 15 EV i dues. Sostre pujat a **104 s**, que és
fins on el tram conserva les invariants que el projecte té escrites (per
sobre de 105 s deixa de superar la graella de 20 s en densitat temporal, i
això sí que és una pèrdua real).

El terra dels 90 s, en canvi, **sí que és físic** i ho he comprovat contra
l'auditoria de cronologia, no contra el compilador: per sota de 88 s el
bracket de 3,2 s del punt mitjà se solapa amb la finestra de re-trigger, i
per sota de 76 s el pla no hi cap. Vaig intentar baixar-lo a 30 i el fuzz em
va enxampar; el terra es queda a 90.

Verificat al cos a 101 s, run `20260807T233944`: R6 **186/186 accions, delta
CFexpress exclusiu +119**; Sony 27/27, 60/60 confirmats, 13 exposicions
úniques fins a 8 s i contactes a **C2−2,90/+0,01/+2,91** i **C3−2,00/+0,91**.

**Resposta curta a la pregunta**: a 60 s continues tenint-ho tot, però
**només per la R6**. La Sony, per sota de 90 s, es queda sense earthshine i
amb 6,1 EV. Si el pronòstic de totalitat baixés d'aquest llindar, el tram
curt de l'A7RIIIA és feina pendent.

## 6 quinquies. Per què la Sony fa 60 fotogrames i la R6 en fa 120

No és el programa, és el cos. Pressupost dels 98,8 s de totalitat de
l'A7RIIIA, comptat del pla compilat:

| | s | % |
|---|---:|---:|
| **Drenant** (baixant JPEG al Mac) | **31,8** | **32,2 %** |
| Disparant | 30,3 | 30,7 % |
| Escrivint exposició | 13,7 | 13,9 % |
| Escrivint mode | 2,9 | 3,0 % |
| Marges i osques | 20,0 | 20,3 % |

Un terç de la totalitat se'n va en descàrrega. I **no es pot treure**: el cos
només ofereix dos objectius de captura, `sdram` i `card+sdram` —comprovat
llegint `/main/settings/capturetarget` al cos—, o sigui que **no hi ha mode
només-targeta**. Cada fotograma ha de passar per la SDRAM cap a l'amfitrió i
buidar la cua costa 0,51 s per imatge. La R6, en canvi, escriu a CFexpress i
no envia mai res al Mac: per això en fa el doble.

L'únic marge que queda és als pressupostos de drenatge: el segon en declara
12,0 s per una mesura de 5,1-7,7 s. Retallar-lo a 9 s compraria un bracket
més (nou imatges). No s'ha tocat: són budgets qualificats físicament i
aquest projecte ja s'ha cremat una vegada amb un drenatge no verificat que
va arrossegar tota la seqüència posterior a C3.

## 7. Cobertura dels tres objectius

| Objectiu | R6 III | A7RIIIA |
|---|---|---|
| Perles i anell a C2 | 25 fotogrames de C2−5,00 a +4,62, tots 1/2000 cada 0,40 s | 3 brackets de nou, C2−2,9 a +5,77 |
| Perles i anell a C3 | 30 fotogrames de C3−7,92 a +3,71 | 2 brackets de nou, C3−2,0 a +3,78 |
| Corona amb moltes EV | 58 fotogrames al nucli, **14 velocitats de 1/2000 a 15 s** (~15 EV) | 9 per bracket, 1/4000 a 1/15, més 1/8..8 s a les àncores |
| Earthshine | 2 s i **15 s** | dues ràfegues de cinc amb **8 s** |

## 8. Què queda

1. **Físic, i no s'ha diagnosticat**: la R6 va caure del bus una vegada i va
   tornar sola. Els cinc runs posteriors són perfectes, o sigui que ara mateix
   no es pot reproduir. **Revisar cable i connector abans del dia 12** i, si
   hi torna a haver una bufada de `-110`, mirar el cable primer.
2. La correcció 1 té les quatre proves offline que fixen el comportament
   (`R6M3LiveTransportResyncTests`) i s'ha exercit una vegada al cos, en una
   desaparició real: va delegar al camí car en 0,31 s, correctament. **Falta
   exercir-la sobre un `-110` recuperable de debò**, que no s'ha pogut
   provocar perquè el cos ja no els fa.
3. El canal Sony surt `WARNING` només per `manual_checklist_incomplete`, que
   el contracte del projecte declara informació i mai avís operatiu. El
   controlador ja degrada el seu propi estat a `warning` per aquest avís, i
   `operational_outcome` no hi arriba mai a la branca de `COMPLETE`. La GUI
   ja té `has_operational_mission_warnings`, que el classifica correctament
   com a no operatiu, però la branca multicanal no la fa servir. **No s'ha
   tocat**: canvia com es jutja qualsevol missió i és una decisió de Pere.
   Efecte pràctic mentre no es toqui: un run perfecte de la Sony es veu igual
   que un de trencat, i això és precisament el que va costar una hora de
   forense aquesta nit.
4. Els trams `..._74_plus_c1_c4` i `..._hdr_plus_c1_c4` (totalitats de 60 a
   120 s) continuen acabant a C3−7 i no travessen el contacte. Per al 12
   d'agost no aplica —la totalitat és de 98,8 s—, però és el mateix defecte.
