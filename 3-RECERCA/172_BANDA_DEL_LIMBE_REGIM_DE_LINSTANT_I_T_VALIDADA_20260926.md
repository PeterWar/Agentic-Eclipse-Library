# 172 · La banda del limbe: on es perdia el detall i com es recupera amb els fotogrames de l'instant (V103)

26-09-2026, matinada · Claude, amb Codex Astra (dues rondes) · Encàrrec de Pere: «fes V103.psb recuperant TOT el detall dels píxels interiors a prop del limbe lunar. […] Jo crec que en els filtres els estàs escurçant massa […]. Si repasses els PSB de capes interiors, en la versió no linealitzada hi veuràs detall en aquelles zones. […] Potser al stackejar imatges de la mateixa exposició no tens en compte on és la lluna?»

## 1. Les tres hipòtesis de Pere, contrastades
1. **«Al stackejar no tens en compte on és la Lluna.»** No és això. L'apilat per tren (b2) emmascara la Lluna de CADA fotograma amb la seva efemèride (guarda 2 px), i la franja arran del limbe (a3c, V99) fa la selecció física amb la distància al limbe REAL de cada fotograma (silueta d21). Codex ho confirma.
2. **«Als filtres els escurces massa.»** Sí, però no als filtres: **a l'entrada dels filtres**. La franja a3c només admet un fotograma quan veu el píxel a ≥ 4 px del seu limbe (rampa 4→6,5 sobre D_real), fixada per la porta «biaix ≤ 2 % sense cap correcció» (doc. 170). Al costat d'avanç de la Lluna (dalt, esquerra, baix-esquerra) cap fotograma no compleix la condició als primers ~4 px, i hi queda una tira sense dada (3,4–4,2 px a dalt, 5,5–7,4 px a baix-esquerra des del cercle; ~4 px des de la vora real). Els filtres hi afegeixen la seva fosa (1,5 px; 4 px als ACHF azimutals; RHEF local 1→3 px). La V101 hi posava detall tangencial només des de 2,75 px, en una capa a part.
3. **«Als PSB de capes interiors hi ha detall.»** Cert: són fotogrames sols (la 96 de Pere és un 1/15 s) sense cap guarda. Demostra que la dada hi és. El que passa és que un fotograma sol porta el **dèficit de vora** (la PSF perd la llum que hauria vingut del costat de la Lluna): −11 % a 2,25 px, −7 % a 2,75, −4,5 % a 3,25 (mitjans, verd). L'ull no ho veu en un fotograma sol; en un compost on la dreta és neta (tardans lluny de la seva Lluna) i l'esquerra no, es veu com un anell fosc (V98).

## 2. Què hi ha a la banda (diagnosi, `4-RESULTATS/v103_banda_20260926/diag/`)
- **La Lluna de presentació és a t = 18,43 s** (A2_GEOMETRIA; C2 ≈ 15 s). Els 11 fotogrames Vixen amb |Δt| ≤ 4 s (8 × 1/3200, 1/2000, 1/500, 1/125) tenen la Lluna a ≤ 1,1 px de la de presentació.
- **Apilats amb només la guarda del disc (0,75→1,75 px)**, el detall tangencial (rms del DoG 2→16 px al llarg de l'arc, ln G') i la reproductibilitat entre meitats (fotogrames parells i senars) per distància a la silueta real:

  | sector | 2–3 px | 3–4 px | 4–5 px | 7–10 px (a3c) |
  |---|---|---|---|---|
  | dalt 60–130°, rms | 0,029 | 0,027 | 0,027 | 0,027 (0,026) |
  | dalt, ρ meitats | 0,85 | 0,87 | 0,83 | 0,84 |
  | baix-esq 205–250°, rms | 0,055 | 0,042 | 0,037 | 0,037 (0,034) |
  | baix-esq, ρ meitats | 0,86 | 0,89 | 0,89 | 0,87 |

  A 1–2 px el rms puja ×5: és la vora de la Lluna (la silueta d'ordre 2 hi té errors de ±0,5 px; les medianes de D18 per PA se n'aparten fins a 0,6 px a dalt i a 240–250°). **A partir de 2 px a dalt i de 3 px a l'esquerra el detall té la mateixa amplitud i la mateixa reproductibilitat que a 7–10 px.**
- **Qui mana a la banda:** el pes LDIC és proporcional a l'exposició. El 1/125 s (2969, t 22,3 s) porta el 62–69 % del pes; el 1/500 s, el 15–17 %; cada 1/3200 s, un 1–2 %. Fotogrames efectius: 2,0–2,4 (Codex ho va detectar). Les dues meitats són, de fet, el 1/125 contra el 1/500 (+ curts): dos fotogrames independents que coincideixen a ρ 0,85. Sense els mitjans (només els 7 curts), ρ cau a 0,44–0,52: els mitjans són necessaris.
- **Trampa del diagnòstic (Codex):** el comptador NF del `diag_banda.py` sumava sobre el denominador acumulat (dona 11 a tot arreu); el de l'a3d és per fotograma. No afecta cap conclusió.

## 3. La cura a l'origen: `a3d_franja_banda.py` (a3c + règim de banda)
- **Règim net** = l'a3c (4→6,5 sobre D_real, tots els fotogrames): byte a byte on ja hi havia dada neta.
- **Règim de banda, només on el net no arriba** (porta per píxel g = 1 − smoothstep(n_nets_efectius, 1, 4)): els 11 fotogrames de l'instant que veuen el píxel a D_real ≥ lo, amb rampa lo→lo+1 per angle de posició (Codex): **2→3 px a dalt (30–110°), 3→4 px a l'esquerra i baix-esquerra (130–250°)**, transició de 20°. Cap fotograma compta dos cops (s_banda = s(lo, hi)·(1 − s_net)). El nivell arran de la vora ve, doncs, de la foto de 1/125 s de C2+3,9 s amb la Lluna a 1 px de la de presentació: **cap píxel que no vingui d'un fotograma que el veu a ≥ 2 px del seu limbe real.**
- **T de vora per classe i canal, mesurada al mateix conjunt** contra el règim net (≥ 10 fotogrames nets) a la dreta (300–60°), per calaix de 0,5 px de la D_real de cada fotograma (mediana per fotograma i calaix), monòtona, amb el desnivell d'exposició (≥ 6 px) separat del dèficit de vora; pes·T². **Validació creuada:** ajust a 300–360° i prova a 0–60°, i a l'inrevés.

  | D_real | T verd (mitjans) | residu creuat | T blau | residu | T vermell | residu |
  |---|---|---|---|---|---|---|
  | 2,25 px | −11,1 % | ±3,2 % | −17,1 % | ±4,4 % | −9,5 % | ±10 % |
  | 2,75 | −6,8 % | ±1,5 % | −12,1 % | ±2,6 % | −6,4 % | ±5 % |
  | 3,25 | −4,5 % | ±0,3 % | −8,3 % | ±1,0 % | −4,7 % | ±2,4 % |
  | 3,75 | −2,9 % | ±0,1 % | −6,0 % | ±0,6 % | −3,6 % | ±1,1 % |
  | 4,25–6 | −2,2 → −0,8 % | ≤ 0,15 % | −4,4 → −1,9 % | ≤ 1 % | −2,7 → −1,5 % | ≤ 0,5 % |

  Desnivell d'exposició dels mitjans: −0,6 / −1,2 / −1,3 % (G/B/R). Dels curts: −3,8 / −10 / −6 % (els 1/3200 descalibrats del doc. 170 §4; pesen < 15 % a la banda). El vermell a 2–3 px no és transferible entre sectors (±5–10 %): és emissió real de la cromosfera que canvia amb el sector; als filtres hi entra amb pes 0,18 (G' = −0,18 R + 1,69 G − 0,51 B).
- **Sensibilitat a la silueta:** el pendent de T és ~9 %/px a 2,25 px i ~4 %/px a 3,25 (verd): un error de ±0,5 px a la silueta es paga amb ±4,5 % de nivell a 2,25 px, ±2 % a 3,25 i ±1 % a 4. Per això a l'esquerra (on la silueta és menys segura) la rampa és 3→4.
- **Variants:** A (20 fotogrames t < 32 s, rampa 2→3 uniforme, T) — referència; **B** (11 de l'instant, rampa per PA, T validada); **C** (com B, sense T: la banda tal com es veu, amb el dèficit real).

## 4. Resultat
(vegeu `4-RESULTATS/v103_banda_20260926/RESULTAT.md`)
- **Codex, ronda 2:** tria B/D amb T com a candidata experimental i C com a control; demana referència independent (només tardans), validació post-matriu per fotograma i ponderada, recompte únic de fotogrames, rampa de dalt 2,75→3,75 mentre el vermell no validi, i que el j17 tingui control nul. Tot incorporat a la variant D.
- **Validació post-matriu (D):** biaix de G′ ±4,0–4,3 % a 2,25 px, ±1,9–2,1 a 2,75, ≤ 0,6 des de 3,25; de L′ ±5,8–6,3, ±2,9–3,0 i ≤ 1,3. Per fotograma: el 1/125 s (70 % del pes) +4,3/−4,9 % a 2,25, +2,6/−2,1 a 2,75, +1,0/−0,3 a 3,25.
- **La variant lliurada és la D:** dada des de 2,5 px (dalt) i 2,75–3,5 px (esquerra, baix-esquerra) de la silueta real, en lloc de 3,75–4,75; idèntica a la V99 on aquesta ja tenia dada; sense costura (≤ 1,6 % a la transició); una excepció declarada a 240–270° (+2,9 % banda contra net, ≤ 1,2 % al producte).
- **La variant C (sense T)** fa la tira fosca de −2 a −8 % a 2–4,5 px: és l'anell fosc de la V98, i confirma que la T és necessària.
- **Lliçons per a la skill:** (1) el dèficit de vora d'un fotograma és una calibració mesurable (T per classe i canal contra els tardans nets), no un model, si es valida fora de l'ajust i post-matriu; (2) el pes LDIC ∝ exposició fa que arran del limbe manin un o dos fotogrames: cal dir-ho (fotogrames efectius) i les meitats han de ser fotogrames diferents; (3) un «graó» a 2–4 px sobre la recta de 6–12 px és curvatura real de la corona: la costura només es pot jutjar a la zona de transició i on el règim net domina; (4) un comptador que suma sobre el denominador acumulat menteix (Codex); (5) el mostreig polar amb interpolació lineal barreja els zeros de fora del domini: veí més proper.

## 5. V104 i el límit físic (d43)
- **V104** (variant E: rampa 2→3 a dalt): dada des de 1,75–2 px a dalt, amb el biaix de nivell de la T transferida (G′ ±4 % a 2,25 px) declarat. Codex (ronda 4): PARCIAL; la ρ entre meitats no discrimina corona de contaminació de vora (també és 0,82–0,85 a 0,5–2 px); l'argument és el rms igual al de lluny.
- **Silueta fina (d43):** reproduïble només a 180–300° (ρ 0,70–0,85; ±0,3–0,5 px); a dalt l'ordre 2 ja és bo a 0,15 px. Aplicada on és reproduïble, no canvia el detall ni la ρ a 2–4 px. **El límit del detall net amb aquesta dada és ~2 px a dalt i ~3 px a l'esquerra**; més enllà cal dada externa (LOLA) i PSF.
