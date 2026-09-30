# 154 — V37: el limbe. Les capes ACHF saturades contra el forat, el rivet del farcit, i la franja de la unió temporal (08-09-2026, vespre)

Ordre de Pere: «Mira V36_Artefactes.psb; els d'a prop del limbe lunar els veig claríssims, els altres són una mica més subtils.» Revisió: `research/tools/revisio_marques_v36_20260908/`, `output/revisio_marques_v36_20260908/` (23 components). Les del limbe (1,03–1,07 R☉) són a P01–P05 i totes a l'OEST (az 130…178 i −178…−143); les altres, contorns d'entrada dels fotogrames a 01–06 (1,24–2,09) i el quadrat dels 8 s al P05 (declarats al 153).

## 1. Tres coses al limbe, mesurades

**(a) Les capes ACHF de cadena (01/02/04/05/06) estaven saturades al voltant de la Lluna, des de la V29.** La vista polar del limbe (`A10_polar_limbe_totes_les_capes_V36.png`) ensenya una banda sense estructura que segueix la vora ondulada del forat i acaba de cop. Mesurat per anells de 0,01 R☉: la mediana de d/escala_tanh val +27 a 1,00 i és > 1 fins a 1,08 (01), 1,10 (02), 1,05 (04), 1,16 (06); la fracció de píxels amb |tanh| > 0,95 és del 99 % al limbe i del 50 % encara a 1,08 (01/02) i 1,12 (06); la std de la capa hi cau a 0,05 contra 0,17–0,26 més enfora. Mecanisme: la convolució normalitzada amb el forat com a suport absent fa una mitjana d'UN SOL COSTAT contra un gradient de ×2 cada 44 px (el mateix mecanisme del 151 §5 per als operadors purs); la tanh satura; `centre_rings` (H1) re-centra la banda saturada i la deixa plana. En Superposar (01 al 36 %, 02 al 20 %) el detall comença a 20–70 px del limbe. Pere no ho ha marcat a 01/02 però és un defecte de mètode clar.

**(b) El rivet clar del MGN/WOW a la vora del forat depèn de la fondària de la franja.** Per sector azimutal (24), mitjana de la capa a 0–8 px de la vora menys a 20–40 px: +1,5…+2,1 σ on la vora del forat és 10–15 px més a prop del Sol que el primer anell sencer (W, NW, E, SW), i ≈ 0 o negatiu on coincideixen (NE, S). Causa: el farcit de la V35 sobreescrivia els anells parcials (1,005–1,046) amb l'extrapolació des del primer anell SENCER (1,046) amb el seu pendent (−0,023 ln/px), però el pendent real al limbe és −0,167 ln/px (7×): a les corones parcials el farcit quedava fosc, la mitjana local baixava i el rivet sortia clar.

**(c) La franja de la unió temporal.** El forat del compost és la unió de les posicions de la Lluna (0,585″/s × 100 s ≈ 27 px): radi de 1,005 a 1,046 R☉ segons l'azimut (mínim a l'oest). A la franja 1,005–1,046 de l'oest només hi contribueixen els fotogrames d'abans que la Lluna tapés el píxel (13–16 contra 22–36 a l'est als mateixos radis), amb pes total 3–4× menor (0,13 contra 0,4) i **gra de la base del 7–9 % (10× el de fora, 0,4–0,9 %)**. És dada real i pobra. El NRGF/RHEF hi tenen estadístiques d'anell parcial (banda apagada, −0,4…−1 σ); el MGN/WOW hi ensenyen gra. La norma de Pere del 27-08 («conserva la unió temporal de les observacions vàlides, sense imposar al compost un forat circular més gran») la conserva.

## 2. Proves i cures

Prova en ROI per sector (`a11_roi_rivet.py`, `A11_roi_rivet.json`), rivet màxim / mediana per sector (σ):

| variant | MGN | WOW | WOW bilateral |
|---|---|---|---|
| A · farcit V35 (extrapolació des del primer anell sencer) | 2,06 / 1,34 | 1,99 / 1,10 | 1,40 / 0,67 |
| **B · mitjanes dels anells parcials conservades, pendent local que decau (L 60 px, pujada ≤ 5 ln)** | **0,70 / 0,36** | **0,56 / 0,16** | (desbordament float32 sense la fita; adoptat amb fita) |
| C · B + variància/potència només sobre el suport real | 1,07 / 0,90 (signe invertit) | 9,68 / 1,82 | – |
| NRGF a · estadístiques parcials (V36) | 1,05 / 0,24 | | |
| NRGF b · μ i σ extrapolats dels anells sencers | 5,22 / 0,22 (espurneig ×3,6) | | |

**V37**: farcit B a P03/P04/P05 (operadors de v31_purs amb una màscara, com la V35) i la mateixa condició de contorn a l'entrada de l'ACHF de cadena (ln TOTAL per canal; convolució sense màscara; sortida al suport). NRGF/RHEF com la V36 (b refusat). Fusió i base: V36.

## 3. Resultats V37

V37.psb: `Capes Totals/V37.psb` (lleugera; base V36 idèntica), SHA-256 `9706226c1878c836038cbb1afecefb5b7a9d990ab010aecf3159749a3d6385ec`, 4,484,412,802 bytes, OBRE 10551 px x 7506 px · 11 capes. Portes al limbe, V36 → V37 (`C3_portes.json`):

| capa ACHF | r on la saturació de la tanh cau al 50 % (V36 → V37) | std de la capa a 1,03 R☉ | H1 pitjor (R☉) | H1b |
|---|---|---|---|---|
| 01 | 1.057 → 1.019 | 0.088 → 0.295 | 0.0075 (1.13) → 0.0823 (1.01) | 1.58 → 2.56 |
| 02 | 1.081 → 1.029 | 0.057 → 0.323 | 0.0105 (1.20) → 0.0210 (1.07) | 1.74 → 1.94 |
| 04 | 1.028 → 1.015 | 0.184 → 0.303 | 0.0252 (1.01) → 0.0600 (1.01) | 1.10 → 2.68 |
| 05 | 1.097 → 1.021 | 0.058 → 0.306 | 0.0138 (1.17) → 0.0641 (1.01) | 1.41 → 1.86 |
| 06 | 1.125 → 1.023 | 0.049 → 0.309 | 0.0084 (2.47) → 0.0511 (1.01) | 0.84 → 1.59 |

| capa pura | rivet a la vora del forat, màx / mediana per sector (σ) | biaix d'anell 1,03–1,3 (σ) | farcit |
|---|---|---|---|
| P03 | 2.11 / 1.31 → 0.64 / 0.20 | 1.42 → 1.07 | B |
| P04 | 2.10 / 1.13 → 0.98 / 0.46 | 0.67 → 0.34 | B |
| P05 | 1.39 / 0.62 → 1.39 / 0.62 | 0.13 → 0.13 | A (B empitjora el bilateral, A12) |
| P01 | 1.05 / 0.23 → 1.05 / 0.23 | 0.10 → 0.10 | – (V36) |
| P02 | 0.96 / 0.33 → 0.96 / 0.33 | 0.17 → 0.17 | – (V36) |

Gra fi a 4 R☉ per capa: sense canvis (01 0.0077, 02 0.0082, 04 0.0146, 05 0.0076, 06 0.0077, P01 0.0026, P02 0.0086, P03 0.0761, P04 0.0331, P05 0.0318).

H1 al primer anell (1,00–1,02 R☉) queda a 0,05–0,08 a quatre capes: és el limbe físic (cromosfera, protuberàncies), que la capa ara deixa passar en lloc de saturar-lo; de 1,04 R☉ enfora H1 ≤ 0,02. H1b (avís, no atura) puja a 2,6–2,7 a 01 i 04 (V36: 1,6–0,9): l'estructura recuperada al limbe té potència a la freqüència dels calaixos del `centre_rings`; declarat. Els anivellaments previs a la tanh provats (anells d'1 px: H1 0,02 i H1b 4,2; suavitzats σ3: H1 0,12 i H1b 3,0) queden refusats.


## 4. La franja: decisió de Pere

La franja és l'única causa restant de les marques «claríssimes» del limbe oest a P01/P02 (i part del gra a P03–P05). Dues sortides, cap de cosmètica: (1) conservar-la (norma del 27-08) i acceptar que els filtres la mostrin com el que és, 18 px de dada amb 10× més gra; (2) un forat circular al radi màxim de la unió (1,046 R☉ a tots els azimuts), que perd aquests 18 px a l'oest i deixa el limbe net i circular. La (2) és exactament el que la norma prohibeix; per això no s'ha fet i es pregunta.

### 4 bis. Les dues versions (08-09, nit)

Pere: «pots fer-me les dues versions? les vull veure i després decidir». Feta la segona: `V37_forat_circular.psb` (SHA-256 `59ac0b98c9a37257c406892258b3d8294573a1a9a6b23071ac4cf68a0d3cf85f`, 4,485,886,326 bytes, OBRE 10551 px x 7506 px · 11 capes) = la mateixa base V36 amb r < 461 px (1,046 R☉) tret del suport (36.119 px) i els 10 filtres regenerats amb la recepta exacta de la V37. Comparació V37 | V37fc (rivet per capa, vista polar del limbe, retalls 1:1 a l'oest i al sud-oest): `output/v37fc_20260908/lliurables/vistes/` i el rebut `V37_forat_circular_REBUT.md`. No és una cura de res: la causa de la franja continua essent la de §4; el forat circular només l'exclou del producte al preu dels 18 px de corona interior de l'oest (dada real amb 10× més gra). Decisió de Pere.

## 5. Trampes d'aquesta ronda

- Un anivellament per anell (H1) amaga una saturació: la banda plana passava totes les portes des de la V29. Porta nova: fracció de |tanh| > 0,95 per anell i std de la capa per anell al limbe.
- Un farcit «pel perfil mitjà» extrapolat des del primer anell SENCER ignora justament els anells que toquen el forat: el pendent del limbe és 7× més gran i el farcit queda fosc.
- Una continuació exponencial sense fita desborda el float32 dins del forat (×e^74): tota continuació porta fita.
- El mateix rivet mesurat globalment (biaix d'anell) i per sector diu coses diferents: al limbe la mètrica ha de ser per azimut, perquè la causa (la fondària de la franja) ho és.
