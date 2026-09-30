# Auditoria de la discrepància fotomètrica — 31-07-2026

## Veredicte

La diferència d'uns 1,37 EV entre l'escala A7III + AP130 i l'escala Canon
6D + 300/2,8 és aritmèticament real, però **no prova que el perfil A7III
sigui erroni**. Les dues escales provenen de trens òptics i decisions de camp
diferents. El perfil A7III conserva el seu propi ancoratge físic de Mazatlán:
mateix AP130 a f/4,5 i els mateixos temps que el 2024, però a ISO 100 perquè
Pere va confirmar que l'ISO 200 del dia de l'eclipsi compensava una capa fina
de núvols.

Tampoc es pot sostenir, només amb els EXIF conservats, que tots els `1/2500`
o `1/4000` de la Canon siguin específicament diamants o perles. Formen part
d'un escombrat repetit durant uns 290 s i el controlador Canon exacte no s'ha
conservat. Per tant, no són una autoritat de fase prou forta per desplaçar
automàticament l'exposició de les altres càmeres.

No s'ha canviat cap escala d'exposició durant aquesta ronda nocturna. La
promoció dels perfils continua exigint un A/B solar amb les òptiques, filtres,
altura i transparència de camp.

## Càlcul reproduïble

Per comparar senyal nominal s'utilitza:

`E proporcional a temps × ISO / (nombre f)²`

Extrems del perfil A7III:

- ISO 100, f/4,5;
- `1/2000 ... 2 s`.

Escala densa observada a la Canon de Mazatlán:

- ISO 200, f/2,8;
- `1/4000 ... 1 s`.

Als dos extrems, el quocient A7III/Canon és:

`2 × (100/200) × (2,8/4,5)² = 0,3872`

`log2(0,3872) = -1,369 EV`

La diferència és exactament la penalització d'obertura de f/2,8 a f/4,5:
el factor de dos del temps compensa el pas d'ISO 200 a ISO 100. Això explica
l'aritmètica; no determina quin dels dos trens té l'exposició òptima.

## Evidència que evita una correcció precipitada

- Els RAW A7III reals del 2024 són del mateix AP130 a f/4,5 i ISO 200.
  L'escala útil arriba de `1/500` a `2 s`.
- Pere va documentar que ISO 200 va ser una compensació d'última hora pels
  núvols i que el pla de cel net era ISO 100. El perfil actual conserva els
  temps i redueix un pas l'ISO; no hi ha cap canvi d'òptica que obligui a
  normalitzar-lo contra la Canon.
- El RAW A7III `DSC06590` a `1/8000` ja té 1.416 píxels al màxim de 14 bits;
  `DSC06598` a `1/100` en té 45.202, i les exposicions llargues tenen clipping
  extens. L'escala cobreix zones brillants i fosques; aquests recomptes no
  certifiquen la fotometria final, però refuten que tots els graons siguin
  simplement buits per manca d'exposició.
- Els 146 RAW Canon formen aproximadament cinc escombrats i no hi ha un log
  fiable que assigni cada `1/2500` o `1/4000` a una fase concreta del contacte.

## Contactes

La comparació `1/8000` A7III contra `1/2500` o `1/4000` Canon barreja:

- f/4,5 contra f/2,8;
- ISO 100 planificat contra ISO 200 observat;
- una ràfega A7III explícitament situada als contactes;
- valors Canon repetits dins d'una seqüència sense controlador preservat.

La diferència nominal és gran, però no és una prova de fase. El gate correcte
és una sèrie solar curta i filtrada amb cada tren real, inspeccionant RAW,
clipping, SNR, limbe, prominències i l'instant respecte de C2/C3. Fins llavors:

1. no improvisar ISO ni obturació el dia de l'eclipsi;
2. mantenir `timing_qualified=false` i `CANDIDATE_NOT_PRODUCTION`;
3. tractar l'A7RIIIA reancorada al 300/2,8 com un perfil propi, no com una
   validació fotomètrica de l'A7III;
4. exigir promoció explícita després de l'assaig òptic.

## Fonts locals

- `research/data/2024_raw_timeline.csv`
- `research/05_AUDITORIA_2024.md`
- `research/12_FORENSICA_RAW_2024.md`
- `research/22_DISSENY_HDR_NADIU_A7III_AP130.md`
- `research/30_DECISIO_ISO100_CEL_NET_2026-07-27.md`
- `.coordination/CLAUDE_STATUS.md`, apartat «l'exposició de l'A7III no
  quadra amb Mazatlán»

