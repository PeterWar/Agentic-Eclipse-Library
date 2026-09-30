# Última campanya curta i repòs segur — 28-07-2026

## Resultat

Campanya física aturada al primer intent, sense cap fotografia nova. El
controlador va rebutjar el run abans d'obrir la càmera perquè el lead real era
de `116,594 s`, inferior al gate dur de `120,000 s`. En compliment del
contracte, no es va fer un segon run.

## Evidència prèvia

- Preflight:
  `controller/runs/20260728T065615_candidate_a7m3_ap130_short_checkpointed_1x5_3x9_preflight/result.json`
- Identitat: `ILCE-7M3`, sèrie
  `[SÈRIE]`.
- Bateria `55%`; cua `d215=0`; `Single Shot`; ISO `100`; `1/8000`;
  DRO `Off`; sensor crop `Off`; `capturetarget=card+sdram`.
- `manual_actions=[]`, `cleanup_ok=true`, lock alliberat.
- Controlador SHA-256:
  `c9afc078b2d62b07a6b3d9ce9bbf00f79e24b3071be6d05557b94e66f38b120e`.
- Perfil SHA-256:
  `d6ee636db3697df581675ecb2661be2690bbbd0909e0b1c06297a31f1e8d887e`.

## Intent aturat

Resultat:
`controller/runs/20260728T065644_candidate_a7m3_ap130_short_checkpointed_1x5_3x9_run/result.json`.
L'error es produeix durant la compilació temporal, abans de detecció USB,
sessió gphoto2, sonda de ruta o trigger. Per tant: `0` captures, `0` descàrregues
i cap canvi d'ajust de càmera.

## Comparació i auditoria

No hi ha dos runs nous comparables. La reauditoria compatible s'ha executat
sobre els tres runs físics qualificats anteriors i ha tornat `ok=true`:
`36/36` accions, `55/55` JPEG i `97,300 s` per run, hashes actuals i payloads
verificats. Les mètriques qualificades continuen sent:

- lateness màxima d'inici d'acció: `0,022 ms`;
- lateness màxima de trigger: `0,879 ms`;
- checkpoint C2 pitjor: `5,501 s` sobre pressupost `7,8 s`;
- checkpoint 5 JPEG pitjor: `2,343 s` sobre pressupost `4,3 s`;
- checkpoint 27 JPEG pitjor: `14,341 s` sobre pressupost `17,8 s`;
- marge estructural del perfil: `0,310 s`;
- marge real abans del primer C3: `1,061–1,072 s`.

Suite offline: `394/394` tests passats.

## Conclusió i optimització segura

No s'ha trobat cap regressió del controlador ni del perfil. No se n'ha
modificat cap dels dos. Per a una futura campanya interactiva, cal calcular C2
després de l'aprovació o reservar almenys `180 s` de lead per absorbir la
latència humana de l'armat. Això no altera la cronologia exacta C2–C3 de
`97,300 s`.

No s'ha enviat cap ordre PTP de power-off. Després de tancar processos i
sessions locals, l'interruptor físic queda en `ON` i la càmera pot aplicar
`Pwr Save Start Time = 30 Min`.
