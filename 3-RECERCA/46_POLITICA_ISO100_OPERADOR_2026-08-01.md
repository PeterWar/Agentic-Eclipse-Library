# Política operativa ISO 100, propietat de l'operador i MISSION FIRST

Data de decisió: **2026-08-01**  
Override final de Pere: **cap valor ISO pot provocar `FAILED`**.

## Decisió

Els tres perfils operatius habilitats comparteixen aquest contracte:

1. **ISO 100 manual** és el baseline recomanat de disseny;
2. **Auto ISO està prohibit com a instrucció d'operació**, no com un hard-fail
   del programa;
3. Eclipse Command no envia cap setter ISO al preflight, configuració,
   timeline, reconnexió ni cleanup, i tampoc restaura ISO;
4. l'operador pot seleccionar qualsevol ISO a voluntat, també entre C2 i C3;
5. qualsevol valor observat —`100`, un altre número, `Auto`, `Auto ISO`, `0`,
   desconegut o metadada absent— és telemetria advisory;
6. la ISO no pot bloquejar `PTP_READY`, preflight, sonda, timeline, reconnexió
   o postflight, ni causar `FAILED` o un exit no-zero;
7. quan existeix, el valor real queda auditat al report i als EXIF.

La prohibició d'Auto ISO continua sent una indicació clara per a l'operador
per preservar una exposició fotomètrica determinista. MISSION FIRST obliga,
però, que oblidar-la o rebre una lectura ambigua no sacrifiqui els triggers.
`FAILED` queda reservat al criteri global del projecte: missió acabada amb
evidència concloent de zero imatges, no a una preferència ISO.

El programa no sondeja ISO abans de cada trigger: afegiria trànsit PTP al camí
calent i convertiria una decisió manual en una dependència de captura. Les
lectures que ja es fan per auditoria tampoc es converteixen en gates.

## Baseline de perfil versus estat real

El validador continua exigint que un perfil amb `mission.enabled=true`
declari ISO 100 i que l'opció 100 formi part del contracte de capacitats.
Això fixa la intenció de disseny i les instruccions de camp; **no exigeix que
la càmera estigui realment a 100 durant una execució**.

Per tant:

- una definició de perfil operatiu amb baseline ISO 200 és invàlida;
- una càmera que durant la missió mostra ISO 200, Auto, 0 o Unknown continua;
- una metadada ISO absent no fa fallar el postflight;
- cap discrepància ISO genera una correcció, restauració o replay.

## Abast

La política advisory s'activa exclusivament quan `mission.enabled=true`. Els
perfils de laboratori i qualificació conserven els seus ISO exactes (100, 200
o 400), els verificadors corresponents i els resultats físics històrics. No es
reescriu cap evidència anterior com si s'hagués capturat a ISO 100.

## A7RIIIA + 300 mm

El baseline del perfil operatiu passa de ISO 400 a ISO 100. Les obturacions no
s'han multiplicat automàticament per quatre: fer-ho alteraria la cobertura HDR,
els deadlines i la qualificació temporal. Això redueix nominalment l'exposició
de baseline en **2 EV** respecte del candidat anterior i manté obert el gate
solar/òptic. L'operador pot compensar meteorologia amb ISO manual, però aquesta
llibertat no converteix la fotometria pendent en una qualificació.

## Guardrails de codi

- el validador exigeix el baseline ISO 100 als perfils operatius;
- rebutja qualsevol write ISO a `preflight.auto_configure`, `configure` i
  `sequence.actions[].set_config`, inclosos els àlies del path;
- `camera_startup_ready_paths()` exclou ISO de `PTP_READY` operatiu;
- preflight i reconnect conserven el valor real com a observació no bloquejant;
- `constant_configured_setting()` no inventa una ISO constant de missió;
- el postflight operatiu no exigeix metadada ISO i registra la disponible;
- `mission_iso_policy_record()` declara `startup_iso_blocking=false`,
  `runtime_program_writes=false` i `iso_can_fail_mission=false`;
- els laboratoris fora de `mission.enabled=true` mantenen els seus gates
  exactes.
