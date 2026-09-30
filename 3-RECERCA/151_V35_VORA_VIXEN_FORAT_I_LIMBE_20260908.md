# 151 — V35: les marques de la V34, mesurades a la font i curades a l'origen (08-09-2026)

Ordre de Pere («Mira V34_artefactes i fes V35»): (1) la majoria dels artefactes del MGN han desaparegut a la V34 — documentar què els causava i com s'ha resolt; (2) la V34 afegeix un artefacte nou, el contorn del FOV Vixen dins del camp Sony, a tots els filtres; (3) el P05 WOW bilateral no s'ha corregit mai («error recurrent»); (4) queda algun artefacte subtil a cada filtre. Aquest document és la causa mesurada de cadascun i la cura a l'origen (V35). Rebut: `V35_REBUT.md` al costat del PSB; codi `research/tools/v35_20260908/`; revisió de marques `research/tools/revisio_marques_v34_20260908/`.

## 1. El MGN: què el feia i com s'ha resolt (per a la skill i per al 2027)

**El que Pere veia (V29–V33)**: contorns transversals a 1,0–2,2 R☉ que segueixen isofotes, arcs a 2,0–2,7 i, al MGN, anells al limbe. A cada versió es va intentar una altra cosa (regularització radial V30, suavitzat V31, camps de nivell V32, suavitzat S/N V33) i el MGN els continuava dibuixant.

**La causa (research/149, mesurada a la font)**: no era el NIVELL (els camps B1 de la V32 el deixen pla a ≤ 0,1 % entre exposicions veïnes) sinó el GRA. El compost LDIC pesa cada fotograma ∝ t_exp × finestra; les exposicions salten de 5 en 5 (0,5 → 2 → 10 s) i la finestra de sostre era estreta (rampa lineal del 70 al 85 % de la saturació): on entra un fotograma de 10 s, el gra del compost cau del 40 % en 40–140 px; al canvi de tren (Vixen sola → Sony) el gra pujava un 54 % en 0,3 R☉. El MGN normalitza la imatge pel σ LOCAL a cada escala (1,25–40 px) i el WOW blanqueja per escales: tots dos converteixen cada canvi d'amplitud del gra en un contorn amb la forma de la frontera (una isofota). Per això «no era de nivell» i cap igualació de nivell el treia, i per això un suavitzat (V33) hi afegia costures noves: canviava el gra a un altre lloc.

**La cura (V34, confirmada per Pere el 08-09)**: a l'origen del gra, no a la capa. (a) Entrada GRADUAL de cada fotograma: finestra de sostre smoothstep del 35 al 85 % de la saturació (`finestra_v34`), que eixampla cada entrada ×2 i baixa el graó de 0,82 a 0,93; (b) fusió per VARIÀNCIA: els dos apuntaments Sony i els dos trens amb pesos ∝ 1/σ² mesurats (gra fi de ln G, σ48), amb porta contra l'altre tren; (c) linealitat de la Sony corregida (la no-linealitat feia graons de nivell a les entrades Sony). Gra de la base −30…−44 % de 2,5 a 6 R☉ sense cap suavitzat. Regla per a la skill (`corregeix-artefactes`, fila **N**): tot canvi de pes en el compost és un canvi de gra, i els filtres normalitzats el dibuixen; els pesos han de ser CONTINUS a tota vora (entrada de fotograma, canvi de tren, vora de suport) i mai es corregeix la capa. Per al 2027: escala monòtona amb salts ≤ 2× i cada esglaó a diversos instants (§1 quater de CLAUDE.md).

## 2. Les marques de la V34 (66 components, 10 capes; `output/revisio_marques_v34_20260908/`)

| família | n | on | causa mesurada |
|---|---|---|---|
| contorn del FOV Vixen (nou) | 10 (una per capa) | rectangle girat ~10°, r 5,1–9,8 R☉ | §3 |
| contorn transversal interior | 38 | isofotes a 1,25–2,1 R☉ | entrades dels fotogrames (graó de gra 0,93 a la V34; queden, més subtils) i, al P05, la trampa del forat (§4) |
| transició al limbe | 11 | 1,02–1,3 R☉ (MGN, P05) | operadors isotròpics contra el forat lunar (§5) i trampa del forat (§4) |
| arc intermedi 3–6 (P04) | 3 | rectangles a ±2^s del Sol | à trous dispers contra el forat (§5) |
| contorn intermedi 2,2–3 (P04/P05) | 4 | 2,15–2,7 R☉ | relleu entre trens 2,0→2,65: el gra queia a la meitat en 130 px (§6) |

Detecció per diferència contra V34.psb (>1 DN16; ±1 és la requantització de Photoshop, 42 % dels píxels); a l'anotat les capes són Normal 100 % sense màscara. Base 00: cap marca.

## 3. El contorn del FOV Vixen (`a1_vora_vixen.py`)

Vora del suport Vixen: r de 5,15 a 9,75 R☉ (mediana 7,8). A la V34 el pes Vixen valia 0,36 al camp exterior i queia a 0 en 160 px a la seva vora. Mesurat contra la distància amb signe a la vora (r > 4 R☉, G):

| distància a la vora (px, + dins) | pes Vixen | ln(V/(S·ρ)) σ64 | graó de la base ln F − ln(Sρ) | gra fi base (%) |
|---|---|---|---|---|
| −200…−100 (fora) | 0 | – | 0,00 | 0,103 |
| 0…100 | 0,07 | **−2,86 %** | −0,29 % | 0,094 |
| 100…200 | 0,34 | −2,66 % | **−0,72 %** | 0,078 |
| 200…300 | 0,36 | −2,39 % | −0,84 % | 0,077 |
| 800…900 | 0,36 | −1,39 % | −0,50 % | 0,072 |
| 1200…1300 | 0,36 | −0,69 % | −0,25 % | 0,070 |

La Vixen és més fosca que la Sony·ρ a la seva vora (vinyetatge/flat de la Vixen al seu camp extrem: −0,7 % a 1200 px, −2,9 % a la vora; R fins a −8,9 %), perquè ρ només s'ajustava a 1,5–4 R☉ i s'extrapolava. La fusió imprimia un graó de −0,8 % de nivell i un graó de gra del 30 % en 200 px: un rectangle a tots els filtres (NRGF/RHEF també per la diferència de gra entre dins i fora de cada anell). A 2,65–4 R☉ el desajust era de −0,1 a −0,4 %.

**Cura (b3 V35)**: (a) la Vixen es conforma a la Sony·ρ en baixa freqüència: V′ = V·exp(−δ), δ = ⟨ln(V/(S·ρ))⟩ σ256 a tot el solapament (ajustada als sectors parells, comprovada als senars), amb entrada smoothstep 2,0→2,65 R☉; residu als sectors reservats G 1,10 → 0,39 %, R 2,04 → 0,76 %, B 1,06 → 0,65 %. La referència de baixa freqüència del camp exterior és la Sony (sense vora dins del camp, flat validat pel dither), com a la V32; la Vixen només hi aporta alta freqüència i gra menor. (b) El pes Vixen s'esvaeix en 720 px a la vora del seu suport (0 → 0,36 de 0 a 700 px), més de 4× l'escala del filtre més gran no azimutal: el gra hi canvia com a gradient, no com a vora.

## 4. La trampa del forat lunar, altra vegada

A la V34 la ploma «a la vora del suport Vixen» es calculava amb `distanceTransform` sobre un suport que porta el forat lunar (V > 0): a 1,0–1,36 R☉ la distància a «la vora» és petita i el pes Vixen queia (mediana 0,04 a 1,0–1,1; 0,30 a 1,1–1,2; 0,70 a 1,2–1,3; 0,98 a 1,3–1,4): la Sony (×1,49 més grossa, amb la Lluna en altres instants) entrava al limbe. La lliçó ja era a la skill des de la V26 (`binary_fill_holes` només a la màscara auxiliar) i es va tornar a caure-hi. V35: totes les distàncies sobre suports PLENS (`suport | r < 1,6 R☉`), i el rebut de tota fusió porta el pes per anell d'1,0 a 1,5 (ara 1,00).

## 5. Els anells al limbe del MGN i dels WOW, i els rectangles del WOW (`a2_p05_limbe_roi.py`)

Els operadors purs (P03 MGN, P04 WOW, P05 WOW bilateral) són isotròpics i tracten el forat lunar com a suport absent (convolució normalitzada). Amb un gradient radial de ×2 cada 44 px, la mitjana local d'un píxel a 1,0–1,3 R☉ només veu el costat exterior, més fosc: coeficient positiu coherent a cada escala → anell clar d'amplada ~σ (MGN) o 2·2^s (WOW). Prova d'un sol paràmetre en una ROI de 2,9 R☉ (7 escales), mediana per anell de la sortida dividida per σ, màxim a 1,0–1,3 respecte de 1,3+:

| entrada | WOW bilateral | WOW | MGN |
|---|---|---|---|
| suport tal qual (com V31–V34) | 4,84 σ | 4,94 σ | 4,33 σ |
| forat omplert pel perfil radial mitjà (només entrada) | 1,81 σ | 2,32 σ | 2,94 σ |
| entrada normalitzada radialment (ln B − ⟨ln B⟩) | 1,75 σ | 1,19 σ | 1,49 σ |

Als retalls (`A2_limbe_*_A_B_C.png`) l'halo clar que abraça la Lluna desapareix amb el forat omplert; la normalització radial canvia el caràcter de la capa (blanqueja el detall fi de les zones febles), i es descarta. A més, l'à trous B3 del WOW és DISPERS (25 mostres a ±2^s, ±2·2^s): amb el forat com a màscara, a cada escala copia la silueta del forat a aquests desplaçaments; les envolupants són rectangles amb els costats a CX ± (2·2^s + R_forat): per a 2^s = 256, x 4410/6314 i y 2824/4728; per a 512, x 3898/6826 i y 2312/5240 — els dos rectangles que Pere ha marcat al P04 (4400–6795 × 2729–4721 i 3951–6013 × 2300–5460). Aquest és l'«error recurrent» del P05 (i del P03/P04): no era de la fusió ni del gra.

**Cura (b4c_purs V35)**: condició de contorn DECLARADA dels tres operadors: l'entrada és la base on hi ha suport i, al forat lunar i fora del suport, exp(perfil azimutal mitjà de ln B) de la pròpia imatge (anells d'1 px; dins del forat, continuació lineal en ln amb el pendent dels 20 primers anells sencers). La sortida es desa NOMÉS al suport físic: cap píxel farcit entra al producte (no és inpainting del producte; és el que la convolució veu a la vora, igual que el mirall que ja feia servir a la vora del llenç). El codi dels operadors és el de `v31_purs`, importat tal qual. Les capes ACHF de la cadena (01–06) ja neutralitzaven aquest biaix amb l'anivellament per anell H1.

## 6. El relleu entre trens i la vora de l'apuntament A

Relleu V32/V34: smoothstep 2,0→2,65 R☉ de la Vixen sola (σ 0,134 % a 2,0) a la fusió (0,083 % a 2,3): el gra queia a la meitat en 130 px (marques P04 L09-M06, P05 L10-M02/M17). V35: relleu 1,9→3,5 (la variància només AFEGEIX Vixen): fracció Vixen 0,98 a 2,0, 0,88 a 2,2, 0,73 a 2,4, 0,54 a 2,65, 0,48 a 3,0, 0,39 a 3,5. Preu: més gra a 2,2–2,6 que la V34 (i més resolució nativa de la Vixen); el canvi és un gradient de 350 px.

Vora de l'apuntament A dins de B (`a3_vora_sonyA.py`; r 6–13 R☉, orientació −40/−130°): nivell net (−0,10 % a la vora, 0 a 200 px: el guany 2D A→B funciona) però graó de gra 0,139 → 0,104 % en 160 px. V35: pes A esvaït en 480 px.

## 7. Resultats V35 (portes, mateixa vara)

V35.psb: `Capes Totals/V35.psb`, SHA-256 `50c8e1cfb7144794db67c227324238fb33b9ccaf91502ff33fb6f954692aa6d4`, 4,481,840,046 bytes, OBRE 10551 px x 7506 px · 11 capes (lleugera: base lineal V35 + 10 capes).

Porta aparellada a les vores (`c3b_vora_aparellada.py`: diferència de la mitjana local σ24 a +150 px dins i −150 px fora al llarg de la normal, mediana sobre el contorn, dividida pel rms de la banda 6–12 px de la capa; control nul = el mateix contorn desplaçat 600 px cap endins; la porta per calaixos de distància no val per a NRGF/RHEF perquè els calaixos dins/fora cauen a radis diferents) i biaix d'anell al limbe (mediana per anell / σ d'1,03 a 1,3 R☉ respecte d'1,3+; 1,00–1,03 és el limbe físic i s'exclou):

| capa | graó aparellat vora Vixen (÷ rms; nul) V34 → V35 | vora A V34 → V35 | biaix d'anell al limbe 1,03–1,3 (σ) V34 → V35 |
|---|---|---|---|
| 01 | -1.15 (-0.00) → -0.01 (+0.06) | -0.13 (+0.11) → -0.07 (+0.11) | 0.05 → 0.08 |
| 02 | -1.47 (-0.01) → -0.06 (+0.04) | -0.10 (+0.16) → -0.11 (+0.16) | 0.08 → 0.11 |
| 04 | -0.41 (+0.01) → +0.01 (+0.04) | -0.10 (+0.02) → -0.06 (+0.03) | 0.14 → 0.33 |
| 05 | -2.07 (-0.03) → -0.04 (+0.06) | -0.09 (+0.17) → -0.06 (+0.15) | 0.07 → 0.09 |
| 06 | -2.72 (-0.05) → -0.08 (+0.06) | -0.02 (+0.18) → -0.03 (+0.17) | 0.06 → 0.07 |
| P01 | -16.30 (+5.25) → -0.74 (+3.01) | +3.68 (+1.79) → +2.42 (+1.65) | 0.08 → 0.09 |
| P02 | -5.51 (+2.96) → +0.46 (+1.90) | +0.79 (+0.63) → +0.48 (+0.60) | 0.01 → 0.01 |
| P03 | -0.77 (-0.04) → -0.02 (-0.03) | +0.04 (+0.08) → +0.04 (+0.07) | 2.50 → 1.40 |
| P04 | -6.96 (+0.12) → -0.49 (+0.16) | +2.86 (+0.65) → +2.55 (+0.93) | 2.59 → 0.67 |
| P05 | -5.70 (+0.47) → +0.01 (+0.01) | +1.78 (+1.14) → +1.64 (+0.81) | 3.00 → 0.13 |

Pes Vixen per anell (trampa del forat): 1.0 R☉ 1.00, 1.1 R☉ 1.00, 1.2 R☉ 1.00, 1.3 R☉ 1.00, 1.5 R☉ 1.00. Gra fi de la base V34 → V35 (%): 2.0 R☉ 0.160→0.158, 2.2 R☉ 0.099→0.110, 2.4 R☉ 0.078→0.086, 2.65 R☉ 0.077→0.078, 3.0 R☉ 0.075→0.075, 4.0 R☉ 0.070→0.070, 6.0 R☉ 0.080→0.083, 8.0 R☉ 0.099→0.103. Pendent màxim del gra al relleu 1,8–3,5 (|Δ ln σ| per 0,1 R☉): V34 0.32 → V35 0.25.
Residu: la vora A al P04 queda a +2,55 (nul +0,93) i al P05 +1,64 (nul +0,81): visible només com a canvi suau de textura a les cantonades (r > 6); declarat. El relleu 1,9→3,5 deixa el canvi de gra com a gradient de 350 px (P05 L10-M02/M17: més suau, no absent).

El contorn del FOV Vixen és dins del nul a totes les capes llevat del P04 (−0,49 contra +0,16); el biaix d'anell al limbe cau a ≤ 1,4 σ (P03) i ≤ 0,7 σ (P04/P05); als retalls (`C0_limbe_*`, `C3_retall_*`) l'halo que abraçava la Lluna desapareix i l'estructura es conserva; el gra fi de les capes a 4 R☉ no canvia (±1 %). Les 38 marques interiors (entrades dels fotogrames) i la vora A al P04 queden com a residus declarats.

## 8. Trampes d'aquesta ronda

- El biaix d'anell mesurat com a mediana per anell / σ compta el limbe físic (1,00–1,03) i, al WOW, el gradient del pla gros: mesurar d'1,03 a 1,3 respecte d'1,3+ i mirar el retall.
- La porta de graó per calaixos de distància (dins −250…−50 / fora 50…250) menteix a NRGF/RHEF: els calaixos cauen a radis i azimuts diferents i el camp llis fa de «graó» (P01 −15 → −5,5 sense significat); la porta bona és l'aparellada al llarg de la normal amb control nul.
- Un `distanceTransform` sobre un suport amb el forat lunar: tercera vegada (V26, V34). El rebut de tota fusió porta el pes per anell d'1,0 a 1,5.
- El primer anell sencer del farcit (1,046 R☉) i el pendent dels 20 primers: si el forat és més gran que el disc C2, el farcit continua un perfil que a 1,00–1,04 encara és parcial.

