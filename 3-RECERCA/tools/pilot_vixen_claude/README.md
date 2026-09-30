# Pilot Vixen · fases 0, 1 i 2 amb portes que poden fallar

Executa el traspàs `.coordination/HANDOFF_2026-08-23_PILOT_VIXEN.md` amb les
portes **F0 i F1 reformulades**. El perquè de la reformulació i tots els
números són a `research/99`.

```bash
./run.sh f1                                  # registre  (segons)
./run.sh f0                                  # calibratge (~2 min)
./run.sh f2 --exposicions fisiques --flat si # composició LDIC (~3 min)
./run.sh portes fisiques_flat-si             # E, E2, G, rectangle
./run.sh llenc fisiques_flat-si              # llenç comú nord amunt + vistes
```

Sortides no-clobber a `output/pilot_vixen_claude_20260823/`.

## Fitxers

| | |
|---|---|
| `comu.py` | constants, lectura i calibratge (fosc → PRNU → flat) |
| `portes.py` | les portes, com a funcions pures |
| `pilot.py` | les etapes |
| `test_portes.py` | **34 proves**: cada porta contra una entrada dolenta coneguda |

## Les regles que governen aquest codi

- ⛔ **Una porta que no pot fallar no és una porta.** Cada funció de `portes.py`
  té una prova amb una entrada dolenta que l'ha de fer fallar. Tres versions
  d'aquest codi van ser refusades per aquest motiu: un oracle F1 avaluat sobre
  un model en lloc d'una mesura, un nul de permutació contaminat pel mateix
  salt que buscava, i una E2 que llegia la curvatura del perfil com un graó.
- ⛔ **Cap llindar triat a mà on es pugui calibrar.** El de F0 surt de la
  dispersió interna de cada esglaó; el de la ruptura d'F1, d'una simulació amb
  el soroll net; el de la E2, dels radis que no són transicions més una
  injecció de resposta.
- ⛔ **El flat sempre abans de qualsevol warp** (no commuten).
- ⛔ **Una sola suma ponderada**, mai apilar per exposició i després fusionar.
  `N` i `D` es desen per separat.
- ⛔ **Norma del rectangle**: cap filtre retallat a una circumferència. La porta
  ho comprova mirant si la frontera de la dada depèn de l'azimut.
- ⛔ **Cap intèrpret escrit a pèl**: `run.sh` en detecta un que tingui numpy,
  scipy, rawpy, cv2 i tifffile, i falla amb un missatge útil si no n'hi ha cap.
- Els RAW, els darks, els flats i els productes S6 són **immutables**. Aquest
  codi només llegeix.

## El que aquest pilot NO fa

Sony, earthshine, filtres (fase 3), Photoshop i qualsevol cosa que toqui una
càmera. La fotometria es declara **fins a 3,2 R☉**.
