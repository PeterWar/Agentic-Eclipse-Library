# F3M — latència de `capturemode` a l'A7III

> Actualització 27-07-2026: les proves F3M aquí descrites es van fer a
> ISO 200 i continuen sent evidència de latència de `capturemode`. El
> candidat de cel net posterior usa ISO 100 segons
> `30_DECISIO_ISO100_CEL_NET_2026-07-27.md`.

Data: 27 de juliol de 2026  
Estat: **PASS sense càrrega RAW; sis arestes qualificades amb 10 mostres cadascuna**

## Veredicte

Les transicions directes entre els tres modes necessaris per al candidat HDR
nadiu han completat **60/60 canvis**:

- `Single Shot ↔ Bracketing C 3.0 Steps 5 Pictures`;
- `Single Shot ↔ Bracketing C 1.0 Steps 9 Pictures`;
- `Bracketing C 3.0 Steps 5 Pictures ↔ Bracketing C 1.0 Steps 9 Pictures`.

Cada mostra ha enviat **una única ordre de mutació `set-config-index` de
gphoto2**, sense retry, i ha esperat fins que el readback ha confirmat el valor
nou. Això no implica necessàriament una única transacció física USB/PTP dins de
libgphoto2. Totes les mostres han estat adoptades dins la finestra de 3 s. El
pressupost provisional resultant en repòs és **1,4 s per transició**.

Aquest PASS només qualifica el canvi de `capturemode` amb la càmera en repòs:
no s'ha disparat ni escrit cap RAW. Encara cal validar el mateix camí mentre la
càmera buida brackets RAW sense comprimir a la SD.

## Condicions i invariants

- Sony A7III (`ILCE-7M3`), firmware 4.04 confirmat físicament per l'operador;
  el readback PTP exposa `4.0`;
- gphoto2 2.5.32 i libgphoto2 2.5.34;
- 10 rondes per sentit i per parella, 60 transicions totals;
- una única ordre gphoto2 `set-config-index` per mostra;
- polls de readback cada 100 ms, amb finestra màxima de 3 s;
- cap segona ordre de mutació davant d'un readback encara antic;
- `capture_triggered=false` i `capture_press_commits=0` als tres runs;
- firewall primari reconciliat exactament amb els esdeveniments
  `gphoto_command_sent`, sense cap ordre prohibida; escaneig del transcript
  net com a comprovació secundària;
- `offline=true`, `network_used=false`;
- cap error de neteja;
- estat original restaurat i verificat exactament com a `Single Shot` als tres
  runs.

Els 60 canvis van necessitar entre 7 i 8 polls. No hi va haver cap
`late_ack_recovered`, cap finestra exhaurida i cap mostra fallida.

Una auditoria posterior de l'eina ha reconciliat exactament les ordres
permeses amb els commits registrats: `233/233`, `217/217` i `218/218` als
tres runs. També ha blindat les execucions futures amb quarantena de
restauració, detecció de deriva tardana i un límit dur de dues ordres de
restauració. Aquest enduriment no altera les mesures dels runs antics; evita
que un run futur pugui confondre una coincidència transitòria amb un estat
final estable.

## Resultats exactes

La latència principal és el temps des del commit del write fins al primer
readback que ja mostra el mode sol·licitat. Amb només 10 mostres per aresta no
s'estima un p95: la cua observada es representa amb el màxim.

| Transició | n | Mínim | Mediana | MAD | Màxim | Marge | Pressupost |
|---|---:|---:|---:|---:|---:|---:|---:|
| `3EV5 → 1EV9` | 10 | 789,886 ms | 815,660 ms | 13,014 ms | 835,890 ms | 500 ms | **1,4 s** |
| `1EV9 → 3EV5` | 10 | 735,405 ms | 817,405 ms | 14,896 ms | 844,078 ms | 500 ms | **1,4 s** |
| `Single → 3EV5` | 10 | 696,518 ms | 816,060 ms | 17,249 ms | 839,370 ms | 500 ms | **1,4 s** |
| `3EV5 → Single` | 10 | 782,400 ms | 818,584 ms | 12,571 ms | 838,438 ms | 500 ms | **1,4 s** |
| `Single → 1EV9` | 10 | 710,407 ms | 813,435 ms | 25,530 ms | 878,636 ms | 500 ms | **1,4 s** |
| `1EV9 → Single` | 10 | 782,573 ms | 819,774 ms | 9,020 ms | 836,846 ms | 500 ms | **1,4 s** |

El marge segueix la regla:

`max(500 ms, 3 × MAD, rang/2, 0,15 × màxim)`

En les sis arestes domina el mínim conservador de 500 ms. El pressupost
s'arrodoneix cap amunt a dècimes de segon després de sumar el marge al màxim
observat. Globalment, el primer readback positiu va arribar entre **696,518 i
878,636 ms** després del commit, amb mediana agregada de **816,730 ms**.

La crida de write va retornar ACK molt abans que la càmera adoptés el mode:
entre **3,400 i 35,269 ms** després del commit en el conjunt de les 60 mostres.
Per tant, l'ACK continua sense ser una confirmació d'adopció; el readback és
obligatori.

## Runs

### `3EV5 ↔ 1EV9`

[Resultat JSON](../controller/runs/20260727T024315_candidate_a7m3_ap130_2024_choreography_f3m-capturemode/result.json)

- inici: `2026-07-27T00:43:15.949Z`;
- final: `2026-07-27T00:43:34.053Z`;
- 20/20 transicions, una ordre de mutació gphoto2 per mostra;
- setup: `Single Shot → 3EV5`, verificat;
- restauració: `3EV5 → Single Shot`, verificada;
- 22 writes totals: 1 de setup, 20 de mostra i 1 de restauració.

### `Single ↔ 3EV5`

[Resultat JSON](../controller/runs/20260727T024354_candidate_a7m3_ap130_2024_choreography_f3m-capturemode/result.json)

- inici: `2026-07-27T00:43:54.396Z`;
- final: `2026-07-27T00:44:10.897Z`;
- 20/20 transicions, una ordre de mutació gphoto2 per mostra;
- setup ja coincident amb `Single Shot`;
- restauració forçada a `Single Shot`, verificada;
- 21 writes totals: 20 de mostra i 1 de restauració.

### `Single ↔ 1EV9`

[Resultat JSON](../controller/runs/20260727T024429_candidate_a7m3_ap130_2024_choreography_f3m-capturemode/result.json)

- inici: `2026-07-27T00:44:29.223Z`;
- final: `2026-07-27T00:44:45.863Z`;
- 20/20 transicions, una ordre de mutació gphoto2 per mostra;
- setup ja coincident amb `Single Shot`;
- restauració forçada a `Single Shot`, verificada;
- 21 writes totals: 20 de mostra i 1 de restauració.

## Reinterpretació del FAIL curt anterior

El run curt de les 00:36 va enviar una ordre de mutació, va esperar
aproximadament 0,4 s i
encara va llegir el valor antic. Això demostrava correctament que l'ACK no
implicava adopció immediata, però **no demostrava que el write hagués estat
ignorat**: el programa va deixar d'observar abans del rang d'adopció que ara
s'ha mesurat.

La mostra més ràpida dels tres runs nous només va confirmar el valor nou
696,518 ms després del commit. Per tant, veure el mode antic als 0,4 s és
compatible amb les 60 adopcions correctes d'una sola ordre. No es pot reconstruir
retroactivament l'instant d'adopció d'aquell write concret, però ja no hi ha
base per etiquetar-lo com a «ignorat».

La política correcta és:

1. enviar una única ordre de mutació gphoto2;
2. no interpretar l'ACK com a estat efectiu;
3. sondejar el readback fins a confirmació;
4. reservar provisionalment 1,4 s per transició en repòs;
5. abortar de manera segura si s'exhaureix el deadline, sense retry ocult.

## Abast del PASS i següent Gate

F3M elimina el bloquejador de latència en repòs i permet mantenir la
recomanació fotogràfica híbrida agrupada `N × 9EV1 → N × 5EV3`. No autoritza
encara un perfil de producció:

- falta mesurar brackets reals a base `1/30`, ISO 200 i RAW sense comprimir;
- falta confirmar per EXIF l'ordre i els temps físics de `9EV1` i `3EV5`;
- falta repetir els switches en la posició exacta de la coreografia mentre hi
  ha activitat de buffer/SD;
- falta demostrar 28 i 42 RAW íntegres sense col·lapse de la cua.

## Integritat dels artefactes

Hashes SHA-256:

| Artefacte | SHA-256 |
|---|---|
| `024315/events.jsonl` | `856d6c149c90fa8f1d9b5a3f3d128be52a0c2aee7f6bd537f49e621d854c4767` |
| `024315/gphoto_transcript.log` | `af0ca1856408bee18d62ec653c9cfd1f4a901cf059d4ee5717a5a15fb1024036` |
| `024315/result.json` | `aa633b407c3fde2bcfbeebfb6b540f94fec7c174a1ff69fb0dcac36765eaa633` |
| `024354/events.jsonl` | `db355f6b49ace545c3b48ea6f54d962d791e8c8f61ffcaec707bb7da1cff8f3c` |
| `024354/gphoto_transcript.log` | `f5d547ca541306f7b3640cbf481d54361b83d5259d2f122a6c1568d212386e1b` |
| `024354/result.json` | `eafbece5d0256f676c349442fac7135c072f4ec4338666c3d21a4aff06c40a3c` |
| `024429/events.jsonl` | `bf641b8279c74555ad8b0904550742a44fd23f218216a9a0be9e39bbbbbb2d15` |
| `024429/gphoto_transcript.log` | `28e939835328ba802df59f8bc893d516aee0568cc9b1e71e039243ec1ccef415` |
| `024429/result.json` | `7f73e6c23aed02fcbad0c311b7bc167081205a2910481064aa6449fe92cec888` |
| `qualify_capturemode_transitions.py` | `a8f2004ab3ed2b5e11dc25b0f274d0870a97f2a44376348610b8c74d783de120` |
| perfil candidat | `8354307cb399ac40593408169f955b5c66961ec29ca7e29fc0830a040dfc6a42` |
