# 133 · La V28: el camp de Brno anell a anell, i la corona sola que mentia de 4 R☉ enfora

**5 de setembre de 2026 (matinada).** Objectiu de Pere: «prepara la V28; compara els
resultats amb les fotos finals de Druckmüller; no sé si els filtres agafen bé les imatges
de la Sony, veig que falta camp; itera fins a resultats semblants; després neteja i
traspàs a Codex».

Eines: `research/tools/v25_lineal/etapa6_compara_brno.py`, `etapa6b_brno_parelles.py`
(reutilitzen el registre dels quatre composts de Brno del `research/114`,
`auditoria_estructura/registre2.json`), `etapa1b_v28_detall_ample.py`, `etapa4_munta_v28.py`.
Resultats a `IA/output/v28_20260905/` (`compara_brno_*.json/png`).

## 1. Quant camp de la Sony arriba a la base

Al llenç comú de la cadena (8096×8960, declarat de la Vixen) la Sony cobreix el 96 %
del llenç i arriba a 13,7 R☉ (anells sencers fins a 9-10 R☉); el llenç la retalla pel
costat llarg (toca les vores esquerra, superior i inferior). A la V23, després del gir de
−46,6°, la cobertura és el 75 % del llenç de Pere: les cantonades (> 9-11 R☉) surten de les
seves capes 12 i 13. ⏭️ Un llenç més gran per a la Sony (fase 2 de la cadena) hi afegiria
dada pròpia de 9 a 13 R☉ al costat llarg: queda com a deute (cost: un run nou i refer les
etapes 1-4).

**Però el camp que faltava no era de cobertura: era dels filtres.** A la V27 el detall
s'esvaïa de 3,5 a 5 R☉ (fi) i de 4 a 5 (gran) per un raonament de S/N fet sobre la
corona sola; el contrast azimutal del compost queia de 0,15 (3 R☉) a 0,045 (5) i 0,014 (7),
quan Brno el manté constant fins a 9 R☉ (0,11 al 200 mm, 0,06 al 400 mm).

## 2. El jutge extern: correlació de l'estructura azimutal anell a anell

Mètode del `research/114`: perfil polar en ln, (x − mediana)/MAD per anell, Pearson
anell a anell, a 4,5° i 9° de suavitzat; control = Brno × Brno. Resultat que mana:

| r (R☉) | 200 × 400 (control) | TOTAL lineal × 200 | corona SOLA × 200 | base display × 200 |
|---|---|---|---|---|
| 1,2-3,2 | 0,95-1,00 | 0,84-0,95 | 0,84-0,94 | 0,84-0,96 |
| 3,4-4,8 | 0,82-0,92 | 0,79-0,82 | 0,83 → −0,04 | 0,78-0,82 |
| 5,0-6,4 | 0,70-0,81 | 0,77-0,79 | −0,14 → −0,63 | 0,77-0,78 |
| 6,6-8,6 | 0,05-0,59 (camp del 400 mm acabat) | 0,74-0,76 | −0,69 → −0,82 | 0,74-0,76 |
| 9,0 | 0,18 | 0,64 | −0,77 | 0,49 |

⛔ **La corona sola de la descomposició de color s'ANTICORRELACIONA amb Brno de 5 R☉
enfora** (fins a −0,8): el model de cel s'empassa l'estructura azimutal de la corona i la
deixa en negatiu al residu. ✅ **El TOTAL (corona + cel) segueix el 200 mm de Brno a
0,75-0,80 fins a 8,6 R☉**, tan bé com Brno se segueix a si mateix on el 400 mm encara té
camp. L'estructura de gran escala (≥ 4,5°) del nostre compost és REAL fins a la vora del
llenç. I a 1° d'escala, el compost V27 cau a 0,3-0,4 de 5 R☉ enfora: l'escala fina no
hi és.

## 3. La V28

- **Font híbrida del detall gran** (en ln, mediana per anell restada): corona sola fins a
  3 R☉ (hi és més neta: 0,87-0,93 amb Brno a 2,6-3,2) i TOTAL de 4 R☉ enfora, fosa 3→4.
- **Capa nova `04 ACHF ample 9R`**: passa-alt azimutal de 256-1024 px d'arc (≥ 4,5° a
  r ≤ 7 R☉), normalitzat per anell (3,5·MAD, terra a 6 R☉), esvaït 8,6→9,6 R☉ (la vora de
  cobertura); H1 0,0004. La banda mitjana (64-256) es manté a la capa gran fins a 7 R☉.
- **La base visible és la del cel a un quart** («00 Base (cel/4)»); la base amb cel queda
  oculta. És el que fa que la corona, com a Brno, es vegi fins al final.
- Mesura de tancament: el contrast azimutal per anell del compost V28 contra el dels
  composts de Brno, i la correlació amb ells (etapa 6).

## 4. Portes i mesures de tancament (V28, iteració 2)

Portes: H1 de les quatre capes de detall PASSA (fi 0,0014 · passa-alt 0,0002 · gran 0,0032 ·
ample 0,0117), perfil radial monòton, limbe net, cap recta (ACHF i gran), cap costura,
fidelitat de les capes de Pere 3/3, Photoshop OBRE (26 capes, 3,93 GB), prova azimutal de
la fusionada 0,00° (als renders del Photoshop: −0,5° la fusionada, −1,0° la base cel/4 sola,
al límit de resolució del render a 1/8). Rebut: `V28_REBUT.md`.

Contra Brno (etapa 6, anell a anell, r en R☉):

- Correlació de l'estructura azimutal (4,5°, mitjana dels 4 composts) del compost V28:
  2: 0.93 · 3: 0.88 · 4: 0.57 · 5: 0.40 · 6: 0.45 · 7: 0.47 · 8: -0.00 · 9: 0.31
- Control Brno × Brno (mitjana de parelles; de 3,4 enfora el manen els composts estrets):
  2: 0.99 · 3: 0.96 · 4: 0.42 · 5: 0.35 · 6: 0.41 · 7: 0.32 · 8: -0.05 · 9: 0.18
- Contrast azimutal (MAD de ln, 1°) del compost V28: 2: 0.36 · 3: 0.31 · 4: 0.20 · 5: 0.19 · 6: 0.14 · 7: 0.09 · 8: 0.07 · 9: 0.04
- El mateix del 200 mm de Brno: 2: 0.23 · 3: 0.14 · 4: 0.16 · 5: 0.13 · 6: 0.12 · 7: 0.11 · 8: 0.12 · 9: 0.12
- Del 400 mm de Brno: 2: 0.23 · 3: 0.14 · 4: 0.13 · 5: 0.08 · 6: 0.06 · 7: 0.04 · 8: 0.05 · 9: 0.06

Lectura: fins a 3,4 R☉ el compost V28 té MÉS contrast azimutal que Brno (0,26-0,31 contra
0,10-0,21); de 4 a 6 R☉ és al nivell del 200 mm (0,14-0,20 contra 0,12-0,16); de 7 a 9 R☉
és al nivell del 400 mm (0,05-0,09) i a la meitat del 200 mm (0,11-0,12). La capa
`04 ACHF ample 9R` va al 50 %: al 70-80 % s'arriba al 200 mm de 7 a 9 R☉, al preu
d'amplificar el que quedi de sistemàtics al camp exterior. És un lliscador de Pere.

Iteració 1 → 2: els sis ghosts de Pere esborrats a l'origen (a la capa ampla els pedaços
sortien com a monedes fosques), la capa ampla pel tall del ratllat i sense pedaços, i el
camp exterior de la base tallat fins a 400 px de període (les ratlles de les capes de Pere).

## 5. Deutes

- Llenç més gran per a la Sony (fase 2 amb `LLENC_COMU` ≥ 12000 px al costat llarg): dada
  pròpia de 9 a 13 R☉ i les cantonades de la V23 sense les capes de Pere.
- Un sol re-mostreig; prova A/B amb el Camera Raw de Pere; VAR per canal; el puntet del
  ghost de 3 R☉; el rombe de cobertura (0,004 de display).

