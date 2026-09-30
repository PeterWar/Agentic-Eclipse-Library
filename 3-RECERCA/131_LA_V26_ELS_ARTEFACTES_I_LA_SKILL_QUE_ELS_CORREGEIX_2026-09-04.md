# 131 · La V26: els artefactes de Pere estudiats un a un, la skill que els corregeix, i el cel que aplanava la corona

**4 de setembre de 2026.** Ordre de Pere sobre la V25: «Els filtres SÍ que són
magnífics [ACHF 70 % + passa-alt 40 % en Superposar] … un pas de gegant. Les
males notícies: (1) les capes linealitzades NO estan alineades amb les
no-linealitzades, girades significativament; (2) els filtres estan plens
d'artefactes, pintats a `~/Downloads/Artefactes.tif` … l'artefacte esfèric del
reflex de la lent amb el Sol descentrat a les primeres imatges de la Sony.
Estudia'ls, fes una skill per corregir-los que s'executi sempre abans de fer un
filtre nou, i fes una nova versió amb tot arreglat.»

Lliurable: `Projecte photoshop/1-Unint Capes/Capes Totals/CapesTotalsV26_lineal_B.psb`
(rebut al costat), skill `.claude/skills/corregeix-artefactes/` (sincronitzada a
`~/.codex/skills/`), eines `research/tools/v25_lineal/etapa1b_*.py` i
`etapa4_munta_v26.py`, vistes a `IA/output/v26_lineal_20260904/`, mesures a
`research/tools/v25_lineal/cau_v25/rebut_v26.json` i `rebut_etapa1b.json`.
La V24 i la V25 no s'han tocat.

## 1. L'alineació: mesurada, no és el que sembla

La base de la V25/V26 va a la graella de la V23 amb la transformació del
`research/130` (rotació −91,969°, escala 1,0000). Comprovat de tres maneres
independents:

- correlació de fase per finestres de 512 px entre la base i les capes **10**
  (1/125 s) i **09** (1/60 s apilat) de Pere, a 11 posicions entre 1,1 i 2,2 R☉:
  **0,0 px** de desplaçament mitjà, i entre 1 i 2 px contra la seva capa 13 (Sony);
- **escaquer de 128 px** base ↔ capa 10 (1,27 R☉), base ↔ capa 09 (1,45 R☉) i
  base ↔ capa 13 (3,0 R☉): els streamers, les protuberàncies i el limbe continuen
  tessel·la a tessel·la (`V26_PROVA_SUPERPOSICIO_escaquer.png`);
- la fusionada de la V24 està dominada per les capes **01-03** (exposicions llargues
  en QUARANTENA però VISIBLES amb màscares al 37-44 %), que van **7-9 px**
  desplaçades respecte de la 09/10: qui compari la base amb la fusionada de la V24
  veu aquest desplaçament, que és de les capes en quarantena, no de la base.

⛔ No hi ha cap rotació entre la base lineal i les capes registrades de Pere. La
pregunta oberta és **contra quina capa** va mirar Pere: si era la fusionada, el
que veia són les 01-03; si era una altra cosa, cal que la digui.

## 2. Les marques de Pere, una per una (`cau_v25/marques_pere_artefactes.json`)

`marques_pere.py` ingereix el TIF (components de color amb centre, mida, radi,
azimut) i fa el panell TIF ↔ fusionada (`ARTEFACTES_PERE_finestres.png`).

| marca | on | què és (mesurat) | família | cura a la V26 |
|---|---|---|---|---|
| 6 taques grogues | ~8 R☉, sis azimuts | **ghosts del Sol a la lent de la Sony** (Sol descentrat, primer apuntament): a la base són < 4σ del gra i NO es veuen; el passa-alt i l'ACHF els treuen; rodons, 200-400 px | G | pedaç DECLARAT (mediana anular a la base, 0,5 a les tres capes de detall), radi 0,55·mida, ploma 14 px; + el ghost de 3,0 R☉ del `research/116` i 8 més detectats a l'ACHF (>3,5σ, compactes, r > 4 R☉); 15 en total, tots ≤ 218 px |
| línies vermelles i verdes | vora de la cobertura del llenç comú | **vores rectes de l'extensió sintètica** del cel de la V25 (per raig, constant) | V | fora de cobertura hi va DADA: les capes 12+13 de Pere (Sony V17 amb el seu Camera Raw + fons per raig) igualades a la meva base (ρ radial × azimutal k≤2 a 6-8,5 R☉, residu 0,23 → 0,02) amb ploma de 120 px mesurada a la vora EXTERIOR |
| ratllat diagonal | camp exterior, molt visible al passa-alt | **patró fix de la Sony**: dues famílies espectrals al mateix període **27,5 px** a **−45,0° i −36,3°** (mateix angle a les 10 finestres d'azimuts diferents = sensor, no estructura) i una de 362 px a −45° | R | tall direccional en falca (±5°, 8-600 px) a les tres capes de detall amb rampa 2,65→3,5 R☉ (zona Sony): pic/anell 240 → 102 (PAL) i 146 → 84 (ACHF) al primer tall; famílies successives a la ronda 3 |

## 3. El que la skill va destapar i Pere no havia marcat

- **El detall fi (ACHF 2-32 px, passa-alt σ24) és gra pur de 3,5 R☉ enfora.** A
  4-5 R☉ el detector G tornava cinc «blobs» de 160-460 px a 200-500σ: eren zones
  de gra (σ robust esbiaixat pel camp exterior llis). I la «recta» de 3.200 px a
  45° i 4,7 R☉ (10 segments de Hough) era la vora d'un **apuntament de la Sony**
  (les vores de la Sony són a ±45° a la V23; la capa 13 de Pere la té igual):
  on un apuntament s'acaba, el soroll del compost canvia de cop i el gra hi
  dibuixa una línia. `research/82`: a 4 R☉ l'estructura real comença a 30-45 px.
  Cura: el detall fi s'esvaeix **3,5→5 R☉** (declarat, per física).
- **La franja fosca al limbe de la ronda 2** (1,0-1,27 R☉, `limbe` FAIL): la
  ploma del camp exterior es mesurava com a distància a «fora de cobertura», i el
  forat lunar hi comptava: fins a 120 px del limbe la base es barrejava amb les
  capes de Pere, que hi són zero. `binary_fill_holes` abans de la distància. Les
  portes numèriques (H1, fidelitat, OBRE) havien passat: ho van dir `limbe`,
  `monotonia` i les vistes.
- **El cel aplana la corona.** L'etapa 1 fusiona CORONA + CEL (la llum mesurada).
  Per anell (luminància, runs 019/016), CEL/CORONA = 0,3 a 2 R☉, **1,0 a 2,5, 2,0
  a 3, 5,1 a 4, 10,5 a 5, 21 a 6 i 160 a 8 R☉**. Amb el cel dins, la corba B
  (0,22/dècada) deixa la modulació azimutal REAL de la corona (13-27 % fins a
  5 R☉, mesurada per sectors de 10°) a ±0,005 de display: per això la corona
  «s'acaba» a 2,7 R☉ i Pere ha de fer «borrar neblina». I el detall 2-32 px no
  hi pot fer res, perquè els streamers fan centenars de píxels.

## 4. Les dues cures de fons (etapa 1b)

1. **Capa `03 DETALL ACHF 32-256 px`** sobre ln(corona SOLA) —la fusió només-corona
   refeta i desada, `cf_corona_lin.npy`—, calculada a 1/4 de resolució amb NRGF
   complet: mediana per anell restada i **3,5·MAD per anell** com a escala de la
   tanh (en ln r, INTERPOLAT), perquè els streamers de 3-5 R☉ tinguin la mateixa
   vara que els d'1,5 (amb 2 MAD el 6 % dels píxels de 2,5 R☉ saturava). Esvaïda
   **5→6,5 R☉**: de 5,5 R☉ enfora la corona sola és el residu del model de cel
   (modulació 0,6 a 6 R☉ i 2-6 a 7). H1 anivellat. Superposar 50 %.
2. **Capa OCULTA `00b BASE SENSE CEL`**: corona + **0,25·cel** (k declarat), la
   mateixa corba B i la MATEIXA àncora (70.736) que la base: la corona interior
   és idèntica (1,1 R☉ 0,734 vs 0,733; 1,5 R☉ 0,515 vs 0,514) i el camp exterior
   baixa (2,5 R☉ 0,269 vs 0,315; 4 R☉ 0,177 vs 0,275; 6 R☉ 0,137 vs 0,262). És
   l'alternativa a la 00 —mateix exterior de Pere igualat, mateixos pedaços—
   perquè Pere triï mirant les dues (D1); no és el «dehaze» de Camera Raw sinó
   el cel de la descomposició de color de la cadena, restat en lineal.

## 5. Vuit rondes en un dia: què va tombar cadascuna

| ronda | què hi havia de nou | què la va tombar |
|---|---|---|
| 1 | pedaços dels ghosts, notch, extensió de Pere | un «blob» anular al voltant del Sol → pedaç de 3.051 px (aplanava la corona) |
| 2 | detector compacte, sostre de radi | notch a 90° del pic (240 → 254); Hough petava; franja fosca al limbe (ploma amb el forat lunar); detall fi = gra a 4-5 R☉ amb una recta de 3.200 px (vora d'apuntament Sony) |
| 3 | ploma a la vora exterior, esvaïment fi 3,5→5, capa GRAN 32-256, base k | recta de −45° a la capa gran (l'altra vora del mateix apuntament); grana a 32-64 px a 2,5-4 R☉; escala global de la tanh manada pel soroll exterior |
| 4 | GRAN en dues bandes amb esvaïments i S/N, MAD per anell, atenuació de costures | l'atenuador va caçar un STREAMER radial de 900 px (a 57 px del centre); arc fosc saturat a 5,3 R☉ (residu de cel del 2n apuntament amplificat pel MAD petit) |
| 5 | rectes radials excloses, camp exterior per capa amb guany local | (aturada per la 6) |
| 6 | banda grossa 4→5 R☉, terra del MAD a 3,5 R☉ | «famílies» de 341 px als eixos a totes les finestres: fuita del gradient de la base (cap pla restat ni finestra de Hann) → tall injustificat al camp exterior; anellet al ghost de 3 R☉ (el passa-alt gran hi deixa un halo de 150 px que el pedaç de 45 no cobreix) |
| 7 | detector amb pla restat i Hann, període ≤ 200 px | (aturada per la 8) |
| 8 | ghost de 3 R☉ tapat a la CORONA abans del detall gran | — (lliurada; portes al rebut) |

Portes finals: al rebut `CapesTotalsV26_lineal_B_REBUT.md` (H1 de les tres capes,
perfil monòton, limbe, rectes, blobs, saturació de la capa gran, fidelitat 3/3,
OBRE). El blob gran que queda a 3,5 R☉ nord (222×386 px) és un feix de raigs
REAL (`DIAG_blob_gran_N.png`): no es toca.

## 6. Trampes noves (a `trampes.md`, «Vuit trampes de la V26»)

1. Un blob «rodó» pot ser un anell al voltant del Sol (sostre de radi als pedaços).
2. L'orientació del pic espectral no és la de les ratlles (mesura abans i després).
3. Una extensió sintètica deixa vores rectes: fora de cobertura hi va dada.
4. Els ghosts només es veuen al detall; el detector G hi va.
5. La ploma d'un camp exterior es mesura a la vora EXTERIOR (el forat lunar no és vora).
6. Un streamer recte ÉS una recta radial: l'atenuador de costures en va caçar un de
   900 px a 57 px del centre (ronda 4); tota recta porta la distància al Sol.
7. La normalització per anell amplifica els anells de sistemàtics: a 5,3 R☉ el
   residu de cel del segon apuntament sortia com un arc fosc saturat (ronda 4);
   el MAD té terra al valor de 3,5 R☉ i la banda grossa s'esvaeix 4→5 R☉.
8. El cel aplana la corona a la base (§3).

Sis rondes de construcció en un dia: cada ronda la van tombar les VISTES o una
porta que la ronda anterior no tenia, mai una porta que ja hi fos. La norma de
Pere («mira-te-les tu abans») és la porta més barata del projecte.

## 7. Deutes

- Un sol re-mostreig del RAW a la graella V23 (fase 2 de la cadena) i la VAR per
  canal (del 130).
- La prova A/B amb la mateixa vara contra la V24 amb el Camera Raw de Pere.
- La cura de fons dels ghosts (2027): pes zero per fotograma al disc predit del
  ghost, o el Sol centrat als primers fotogrames de la Sony.
- Els ghosts detectats sense marca de Pere (8) són pedaços declarats: cal que
  Pere els validi a la vista `V26_PROPOSTA_finestres_1a1_inspeccio.png`.
