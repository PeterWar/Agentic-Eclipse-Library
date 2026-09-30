# A7RIIIA + 300 mm: fixed 5×3 i exposició central

> **SUPERSEDIT:** el gate fixed 9x1 de 63 fotos és a
> `48_A7RIIIA_FIXED9_BUFFER_PIPELINE_2026-08-02.md`. Aquest document conserva
> l’evidència històrica del fallback de 35 fotos.

Data: 2 d’agost de 2026

## Decisió

Per totalitats de 90–100 s, la Sony A7RIIIA manté un únic mode nadiu
`5 pictures × 3 EV` entre C2 i C3. Fa set brackets, 35 imatges i 15
obturacions diferents. No canvia `capturemode` ni drena dins totalitat.

El bracket central usa base 1/20 i produeix, en l’ordre físic observat:

`1/20 → 1/160 → 2/5 → 1/1250 → 3,2 s`

Com que la presa de 3,2 s comença 3,2 s després del press i el seu centre és
1,6 s més tard, el controlador prem 4,8 s abans del midpoint C2–C3.

## Per què s’abandona el canvi de mode dins totalitat

El primer TEST RUN simultani va acumular 36 JPEG pendents. Amb aquesta cua:

- `shutterspeed` encara va acceptar canvis;
- `capturemode` va passar a readonly;
- les captures que el pla considerava Single van continuar generant brackets.

No hi va haver trigger ambigu ni replay, però el resultat 90 JPEG per 80
previstos va refutar la coreografia de canvi de mode. El disseny fixed 5×3
converteix el comportament demostrat en contracte: mode únic, canvis només de
base i deute màxim 35.

## Cobertura

Bases i exposicions dels set brackets:

- 1/80: `1/5000, 1/640, 1/80, 1/10, 4/5`;
- 1/40: `1/2500, 1/320, 1/40, 1/5, 1,6 s`;
- 1/20 central: `1/1250, 1/160, 1/20, 2/5, 3,2 s`.

La seqüència simètrica és
`1/80, 1/80, 1/40, 1/20, 1/40, 1/80, 1/80`.

## Evidència física

### Gate exclusiu

- run: `20260802T032019_candidate_a7r3a_300gm_short_checkpointed_1x5_3x9_run`;
- 42/42 JPEG totals, 35/35 dins totalitat;
- resultat SHA-256
  `7baff3562d5f082462d1159b244ec8b45a90361d4062bf840310587696b7a38c`;
- manifest SHA-256
  `ca021a16072cdd7543015b582701c49673e6cec56ee067d08235197a8bd78549`;
- zero Busy, timeout, desconnexió, replay o estat desconegut;
- drenatge post-C3 de 35 JPEG: 23,878543 s.

### TEST RUN final de la GUI

- run multicàmera: `20260802T033631_multi_camera_mission_run`;
- A7RIIIA 42/42 JPEG, zero misses;
- `capt_DSC02781.JPG`: EXIF 3,2 s;
- centre planificat: C2+49,400000958 s;
- midpoint: C2+49,4 s;
- resultat SHA-256
  `ab3277042a2efa2e873749613be695c7041ae0901caf77777dc5bcff10770a62`.

## Demostrat, falta i ordre de gates

**DEMOSTRAT:** ordre de bracket, canvi d’obturació sota deute JPEG 35,
42/42 dues vegades, drenatge post-C3, cleanup/restore i execució simultània
des de la GUI.

**FALTA:** delta SD ARW exclusiu d’aquesta coreografia; retard físic exacte
press→obturador; escala solar/òptica amb el Sony 300/2,8, filtre i focus reals;
comportament tèrmic, cable-pull i canvi de bateria.

**ORDRE:** 1) delta SD ARW sense canviar el programa; 2) assaig solar
d’exposició/focus; 3) cable-pull i bateria; 4) tres runs finals amb els mateixos
hashes; 5) promoció explícita. Cap gate pendent impedeix mission-first, però
cap d’ells es pot declarar superat per inferència.
