# Poliment de contactes i pipeline C3 de l'A7RIIIA

Data: 2 d'agost de 2026

## Problemes observats i decisio

- Les Sony feien una fotografia invisible abans de C1 per la sonda de ruta
  PTP. Als perfils operatius la sonda fotografica queda desactivada; la
  primera captura cientifica dels tres cossos es C1.
- La Canon 6D no fa tres triggers: cada pressio activa l'AEB natiu `+/-3` i
  produeix exactament tres CR2 (`1/250 -> 1/2000 -> 1/30`). El programa ho
  etiqueta ara com `3 RAW/trigger`. No es commuta AEB durant la missio perque
  els setters post-RAW han produit `PTP Device Busy 0x2019` al cos real.
- Cap cos dispara exactament a C4. El compilador reserva una finestra quieta
  final de fins a 8 s i l'A7RIIIA situa la fotografia documental a C4-30 s.
- L'A7RIIIA aprofita el temps abans del midpoint amb un segon bracket llarg,
  drena per payload sense esperar un selector de mode que no canvia, i reserva
  l'ultim bracket rapid per C3-3,1 s.

## Gate fisic A7RIIIA de 98,8 s

Run canonic:
`controller/runs/codex_20260802_a7r3a_c3_polish/physical_gate_v2/controller/20260802T135037_candidate_a7r3a_300gm_short_checkpointed_1x5_3x9_run`

- 83/83 JPEG confirmats: 2 captures parcials, 72 dins C2-C3 i 9 documentals
  abans de C4.
- 22/22 accions completades; zero skips i zero warnings de cronologia.
- Drain 27: 19,173799 s; drain 36: 26,058970 s; cua pendent final zero.
- Dos brackets llargs: 7,005098 s i 7,005373 s.
- Dues exposicions EXIF de 3,2 s: `capt_DSC03400.JPG` i
  `capt_DSC03409.JPG`; la segona correspon al bracket central.
- Ultim bracket de totalitat a C3-3,1 s: 9/9 JPEG.
- Drain post-C3 de 9 JPEG: 6,224908 s.
- Confirmacions diferides de mode: 8,665 ms i 8,846 ms, sense canvi de mode.
- Cap `Busy`, `-110`, timeout, recovery o replay; `cleanup_ok=true`,
  `restore_ok=true` i `physical_state_unknown=false`.

SHA-256:

- resultat: `bc9e46f854e0f1834ea40ab833b4f8082c67f61525c01e70ac3294da52fa2ada`;
- run manifest: `40b16780e6719465b40a4b57a2450dc77d9b46e15eb7ac080232380d79315e88`;
- downloads manifest: `4a2f024d12f22359547962a603b650ab6cc937b7084f0ab20887492c12337189`;
- profile snapshot: `2d6a14bc3d9a2bb98b4788c45afd253374ccb70ed1a7a4a79b02011418007362`.

## Demostrat, falta i ordre

**DEMOSTRAT:** cronologia JPEG completa de 98,8 s, 72 exposicions dins
totalitat, dos brackets amb 3,2 s, activitat fins C3, drenatges acotats,
absencia de trigger a C4 i estat final conegut.

**FALTA:** delta SD ARW exclusiu, prova solar/optica amb el 300/2,8, filtre i
focus, i resiliencia de cable/bateria. El gate JPEG qualifica temps i control;
no substitueix integritat RAW ni rendiment optic.

**ORDRE:** 1) regressio i paquet portable; 2) delta SD ARW; 3) prova
solar/focus; 4) resiliencia; 5) promocio explicita. Els bounds de buffer son
exclusius de l'A7RIIIA i no es transfereixen a cap altre cos.

## Repeticio multicamera des de la GUI

Sessio:
`controller/runs/codex_20260802_gui_072_final/runs/20260802T140916_multi_camera_mission_run`

- QA d'usuari `ok=true`, tres cossos detectats, tres canals llançats, cap
  modal i cap control critic habilitat mentre la missio era activa.
- A7III: 60/60 JPEG; A7RIIIA: 83/83 JPEG; Canon: 31/31 pressos AEB i 93/93
  commits card-only. Zero misses als tres canals.
- Primera captura planificada dels tres cossos exactament a C1; probes de
  ruta desactivats.
- Ultima captura: A7III C4-8 s, A7RIIIA C4-30 s i Canon C4-38,575 s. Per tant
  no hi ha cap trigger simultani ni rafega exacta a C4.
- L'A7RIIIA repeteix 72/72 dins totalitat, drain 27 en 19,296680 s, drain 36
  en 26,422686 s, dues exposicions EXIF de 3,2 s i bracket final a C3-3,1 s.
- Tots tres canals acaben amb cleanup verd, estat conegut, zero skips i zero
  warnings de cronologia.

La lectura card-only Canon posterior compta 815 CR2. El predecessor verificat
acabava en 629, i els dos runs posteriors tenen ledgers independents de 93
commits cadascun: `629 + 93 + 93 = 815`. Aquesta reconciliacio corrobora que
la targeta va rebre tots dos runs, pero no substitueix un manifest pre/post
exclusiu si es vol atribuir cada CR2 del darrer run al seu action ID.
