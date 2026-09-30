# Gate de cronologia completa v0.3.5 — A7III + AP130

Data: 28-07-2026  
Cos: Sony ILCE-7M3, firmware 4.04  
Tren: A7III astromodificada + AP130GTX + QUADCC  
Estat: **gate temporal complet 3/3 superat; candidat, no producció**

## Resultat executiu

El perfil
`candidate_a7m3_ap130_short_checkpointed_1x5_3x9` ha completat tres runs
consecutius de **97,300 s**, la durada corregida pel limbe del cas curt de
Ferrol:

- `36/36` accions per run i cap `skipped`;
- `55/55` imatges de telemetria per run, `165/165` en total;
- 11 contactes C2, un bracket `5×3 EV`, tres brackets `9×1 EV` i 12
  contactes C3;
- ordre d'obturació, ordre de bias, ISO i consistència EV correctes;
- tres checkpoints JPEG amb cua final zero i `capturemode` escrivible;
- restauració a `Single Shot`, `1/8000` i ISO 100;
- `cleanup_ok=true`, `restore_ok=true`, release final confirmat i
  `physical_state_unknown=false`;
- bateria estable al 57% amb `USB Power Supply = On`;
- funcionament completament offline.

Hashes comuns als tres runs:

- controlador:
  `c9afc078b2d62b07a6b3d9ce9bbf00f79e24b3071be6d05557b94e66f38b120e`;
- perfil:
  `d6ee636db3697df581675ecb2661be2690bbbd0909e0b1c06297a31f1e8d887e`.

El compilador calcula una durada mínima de **96,99 s**. Per tant, 97,3 s
deixa 0,31 s de marge estructural després d'incloure els pressupostos,
toleràncies i jitter declarats.

## Runs comptats

| Run | C2 | C3 | C2 11 JPEG | HDR 5 JPEG | HDR 27 JPEG | Marge real abans del primer C3 |
|---|---|---|---:|---:|---:|---:|
| `20260728T033705…run` | 01:39:30.000Z | 01:41:07.300Z | 5,419 s | 2,228 s | 13,632 s | 1,063 s |
| `20260728T034202…run` | 01:44:30.000Z | 01:46:07.300Z | 5,367 s | 2,197 s | 13,667 s | 1,061 s |
| `20260728T034702…run` | 01:49:30.000Z | 01:51:07.300Z | 5,501 s | 2,343 s | 14,341 s | 1,072 s |

Pressupostos del perfil:

- checkpoint C2: 7,8 s; pitjor observat 5,501 s; marge 2,299 s;
- checkpoint de cinc JPEG: 4,3 s; pitjor observat 2,343 s; marge 1,957 s;
- checkpoint de vint-i-set JPEG: 17,8 s; pitjor observat 14,341 s;
  marge 3,459 s.

La lateness màxima d'inici d'acció va ser 0,022 ms. La lateness màxima de
l'ordre física `capture=1/0` va ser 0,879 ms.

Resultats:

- [run curt 1](../controller/runs/20260728T033705_candidate_a7m3_ap130_short_checkpointed_1x5_3x9_run/result.json)
- [run curt 2](../controller/runs/20260728T034202_candidate_a7m3_ap130_short_checkpointed_1x5_3x9_run/result.json)
- [run curt 3](../controller/runs/20260728T034702_candidate_a7m3_ap130_short_checkpointed_1x5_3x9_run/result.json)

## Reauditoria offline

`controller/tools/verify_full_timeline_gate.py` torna a comprovar els tres
`result.json`, els manifests, els hashes actuals de controlador i perfil, les
108 accions, els 165 fitxers i tots els seus SHA-256 sense contactar la
càmera. La reauditoria del 28-07-2026 ha retornat `ok=true`, sense errors.
El report conserva explícitament `scientific_raw_verified=false`.

La mateixa versió també ha completat per `dry-run` les tres envolupants
operatives: **97,3 s, 98,8 s i 99,7 s**, sempre amb 36 accions, 55 imatges
esperades i cap branca opcional. La prova física al cas més curt és, per
tant, la més exigent de les tres quant a espai temporal.

Un preflight final només de lectura a les 04:15 locals també ha passat:
identitat correcta, `Single Shot`, ISO 100, `1/8000`, DRO Off, sensor crop
Off, `card+sdram`, cua zero, bateria 57%, cap acció manual pendent i cleanup
net. No va executar cap sonda ni cap disparador.

La sonda d'espai SD només de lectura ha demostrat també un límit del backend:
en `PC Remote`, `storage-info` no retorna res i `summary` mostra
`Storage Devices Summary` buit. No es pot convertir l'espai lliure en gate
PTP per a aquesta A7III; cal comprovar ≥10 GiB manualment en `Mass Storage`.

## Què s'ha corregit

El primer perfil híbrid intentava canviar `capturemode` amb JPEG pendents.
La Sony retornava la propietat com a `Readonly` i la cronologia col·lapsava.
El perfil nou buida cada grup abans de canviar de Drive Mode.

Un primer intent del perfil checkpointed restaurava `1/8000` abans de
drenar 27 JPEG. Aquell setter va consumir 4,68 s sota càrrega i va deixar
el drenatge sense marge. Ara el controlador:

1. acaba els tres brackets `9×1`;
2. drena immediatament els 27 JPEG;
3. restaura `1/8000` amb la cua a zero;
4. restaura `Single Shot`;
5. inicia els contactes C3.

També reserva marge perquè `wait-event-and-download` escrigui els fitxers i
retorni el prompt. La purga final sense payload usa un guard separat de
0,25 s. Això evita convertir l'epíleg de gphoto2 en un fals timeout o en
una sessió contaminada.

El pressupost antic de 5,28 s del checkpoint C2 va fallar en dos runs
complets: una vegada quedava `d215=1` després de rebre els onze JPEG i una
altra `d215=0` però `capturemode` encara era `Readonly`. El perfil definitiu
usa 7,8 s. Els resultats antics 3/3 + 10/10 continuen sent evidència
històrica del subgate, però no qualifiquen el hash actual.

## Què no acredita

Els 55 fitxers reconciliats al Mac són JPEG petits de telemetria. Els
manifests declaren honestament:

`scientific_raw_verified=false`

Encara s'ha de canviar la càmera a Mass Storage després d'una campanya,
crear manifests pre/post de la SD i demostrar:

- exactament 56 ARW nous entre manifests: un de la sonda diagnòstica i
  55 científics, identificats i separats pels seus números de fitxer;
- `6048×4024`, RAW sense comprimir i integritat TIFF/ARW;
- ordre i Exif coherents amb els JPEG;
- absència de bandes o degradació inacceptable amb Silent Shooting;
- espai i rendiment de la SD de camp.

Tampoc queden qualificats encara:

- desconnexió USB o apagada enmig de totalitat;
- supervisor de dues càmeres;
- A7RIIIA + 300 mm;
- Canon 6D o R6 Mark II;
- interfície d'usuari;
- assaig amb l'òptica, filtre, focus i cel real.

Per això `timing_qualified=false` i `CANDIDATE_NOT_PRODUCTION` es mantenen.
