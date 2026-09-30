# 153 — V36: les marques de la V35 (la vora quadrada dels 8 s de la Sony, els anells discrets de NRGF/RHEF i el limbe) — 08-09-2026

Ordre de Pere: «Encara he trobat algun petit artefacte a la V35, principalment a prop del limbe lunar, en la corona interior, mira V35_Artefactes.» Revisió: `research/tools/revisio_marques_v35_20260908/`, `output/revisio_marques_v35_20260908/` (26 components, totes liles; 0 a la base i a 01/02/04/05).

## 1. Les marques

| capa | marques | on | causa mesurada |
|---|---|---|---|
| P05 WOW bilateral | quadrat gruixut (4 costats de 400–500 px) a ±1500–1600 px del Sol (3,3–3,8 R☉); dues línies verticals fines a CX+694 i CX−1152 (r 1,6–3,2) | | vora dels 8 s (§2); línies: còpies de l'à trous del farcit (§4) |
| 06 ACHF estructura 4-64 | franja vertical 475×2665 px a x ≈ 6885 (CX+1520) | est | costat est de la vora dels 8 s (§2) |
| P03 MGN, P04 WOW, P05 | arcs fins a 1,03–1,08 R☉ a az −178…−144, −17…4, 129…174 | limbe, sobretot oest | franja de la unió temporal i graó del farcit (§4) |
| P01 NRGF | tres arcs a 1,036–1,065 (az −159…−147, −178…−166, 161…172) | limbe oest | discontinuïtat al primer anell sencer (1,046 R☉) (§3) |
| P02 RHEF | arc a 1,04–1,06 i TRES línies horitzontals paral·leles (y 3792, 3811, 3824; x 4757–4898) a az 178° | eix −x | bandes de fase del rang discret (§3) |

## 2. La vora dels 8 s de la Sony és un quadrat arrodonit

Els dos fotogrames de 8 s (DSC06987 A, DSC06993 B) entren on el seu valor baixa del 85 % de saturació. Mesurat amb els pesos per fotograma (a1, graella 1/4), la zona sense pes dels 8 s **no és un cercle: és un quadrat arrodonit alineat amb el llenç** (`A6_pes_8s_sony_contorn_mig_pes_vs_quadrats_atrous.png`), amb els costats a ~1540–1620 px del Sol (E 6900, O 3750, N 2150, S 5300). El sensor de la Sony és a ~45° del llenç: un quadrat alineat amb el llenç és un rombe al sensor, i això és el que fa el **vinyetatge** d'un 300 mm a f/2,8 sobre una escena dominada pel cel: la saturació arriba més enfora pels eixos del sensor que per les diagonals. La rampa de pes anava de 0 a ple en ~450 px (finestra 0,35→0,85), però la variància del compost canvia sobretot mentre el pes dels 8 s és petit (g < 0,2), o sigui a la part alta de la rampa (f 0,71–0,83 de saturació): el gra del compost cau ~35 % en ~110 px, seguint el quadrat. El 06 (σ 4–64) i el P05 ho dibuixen com una banda gruixuda.

**Dues cures provades a l'origen, totes dues REFUSADES** (mateixa vara: gra fi de la base contra la distància amb signe al contorn de mig pes dels 8 s, calaixos de 50 px, r > 2,2 R☉, sense ghost; `C3_portes.json` de cada ronda):

| variant | gra fi (%) a −800 (8 s plens) / al contorn / +800 (dins) | què fa |
|---|---|---|
| V35 (finestra V34, 0,35→0,85) | 0,072 / 0,069→0,079 / 0,079 | graó del 14 % en ~200 px |
| finestra pròpia dels 8 s, (1 − ss(0,10→0,85))² | 0,081 / 0,083 / 0,079 | graó fora, però +14 % de gra a TOT el camp on els 8 s són al 10–50 % de saturació (fins a 800 px enfora) |
| esvaïment espacial, pes × ss(d, 0, 900 px)³ des del contorn de mig pes | 0,073 → 0,093 (−400…−250) / 0,089 / 0,080 | bony de gra fins a +30 % en una banda de 1200 px (també treia els 8 s de l'anell interior on tenien 0–50 % de pes) |

El compromís és intrínsec: amagar un graó de gra del 14 % exigeix un gradient del 14 % en algun lloc, i com més ample, més àrea amb gra intermedi; les dues variants gastaven senyal/soroll en molta més àrea que la del defecte. Norma de Pere: no sacrificar detall. **La V36 conserva els pesos de la V35 i declara la vora dels 8 s com a residu d'origen de captura** (salt ×4 d'exposició entre els 2 s i els 8 s; el protocol del 2027 amb salts ≤ 2× el resol). La forma quadrada és del vinyetatge i no es toca.

## 2 bis. ⛔ ERRATA de la V34 i la V35: la LUT de linealitat de la Sony no s'havia aplicat mai

En muntar la finestra dels 8 s (que va per nom de fotograma dins de `plans`), la prova de comprovació va dir que els pesos de la V36 eren idèntics als de la V34. La causa: `plans_v34` només aplicava la correcció si `s.run.tren == 'sony'`, i el run de la Sony es diu **`SONYTOT`**. La condició era falsa a tots els fotogrames: **la V34 i la V35 no porten la correcció de linealitat de la Sony que els seus rebuts declaren** (les altres cures —finestra gradual, camps B1, fusió per variància, δ, esvaïments— sí que hi són: no depenien de l'etiqueta). La V36 la porta de debò (comprovat: el pla calibrat d'un fotograma de 8 s canvia; comparació amb i sense a `A9`). Lliçó per als guardarails (152 §5): **cap canvi declarat sense una prova que ha entrat** (un hash de sortida que canvia o un delta mesurat entre amb/sense); una condició sobre una etiqueta que no s'ha imprès mai no és una prova.

## 3. NRGF i RHEF: anells d'1 px, forat excèntric, fase constant als eixos

El forat lunar del compost és la unió de les posicions de la Lluna: radi de 1,005 a 1,046 R☉ segons l'azimut (mínim a az −174°, màxim a −73°), centre a 3,5 px del Sol (`A5_forat_geometria.json`). Els anells 1,005–1,046 són PARCIALS (només tenen píxels a l'oest). La V35 tractava els anells incomplets només a la vora del llenç; a dins, mitjana i desviació de l'anell parcial → salt a 1,046 (marques P01 a l'oest). **Prova (b4d)**: aplicar als anells interiors el mateix estimador de l'anell sencer per la forma azimutal dels anells sencers veïns (1,046–1,135). ⛔ REFUSADA: la forma azimutal al limbe canvia amb r (prominències compactes) i la mediana per anell a 1,003–1,02 passava de −0,4 a +0,8 σ. Les estadístiques dels anells parcials queden com a la V35. Els pics d'anells d'1 px que queden a l'oest (rings 455/460/462 = 1,033/1,044/1,049 R☉, +0,3/+0,1/+0,2 σ; les marques P01) són iguals a les dues versions i queden com a residu (discretització dels anells contra la graella al costat de l'eix −x, o estructura real del limbe: no discriminat).

Les tres línies horitzontals de la RHEF a az 178°: amb anells d'1 px, prop de l'eix −x el radi val r ≈ |dx| + dy²/(2|dx|): la fase r mod 1 és quasi constant al llarg d'un segment de fila, o sigui que tots els píxels d'una fila cauen a la mateixa posició subpíxel del seu anell, i com que dins d'un anell d'1 px el gradient radial (×2 cada 44 px) ja ordena els píxels, el RANG és coherent per files: bandes horitzontals (i verticals prop de ±y). És la discretització, no la dada. **Cura**: rang en radi continu, F(B) = (1−α)·F_i(B) + α·F_{i+1}(B) amb les CDF empíriques dels dos anells veïns i α la posició subpíxel.

## 4. El limbe als operadors isotròpics: el que s'ha provat i el que queda

Farcit V35 (perfil azimutal mitjà, exponencial fins al centre: ×29.000 el limbe al centre) contra dues alternatives, en ROI (`a8_roi_farcit.py`, `A8_roi_farcit.json`): (B) farcit separable P(r)+A(θ) amb pendent que decau (L 100 px) i variància/potència només sobre el suport real; (C) el mateix farcit amb una màscara.

| | MGN biaix 1,03–1,3 / graó vora forat (σ) | WOW | WOW bilateral |
|---|---|---|---|
| V35 | 1,40 / +1,14 | 0,36 / +0,75 | 0,19 / +0,29 |
| B | 1,38 / +1,37 | 1,83 / +1,86 | 2,16 / +2,11 |
| C | 1,35 / +1,36 | 0,78 / +0,99 | – |

⛔ Les dues alternatives empitjoren el WOW: la curvatura del farcit exponencial entra a la variància local i, per casualitat útil, compensa el biaix d'un sol costat; treure-la (pendent que decau, o variància només real) el destapa. Es conserva el farcit V35. El que queda al limbe oest (1,04–1,06) és en part la **franja de la unió temporal**: els píxels a 1,005–1,046 de l'oest només els veuen els fotogrames d'abans que la Lluna els tapés (menys fotogrames, més gra), i la norma diu conservar la unió temporal. Residu declarat. Les còpies de l'à trous del farcit (línies fines a CX+694 = 2·128+449 i CX−1152 = 1024+128) queden com a residu del mètode à trous amb un objecte compacte brillant al centre.

## 5. Resultats V36

V36.psb: `Capes Totals/V36.psb`, SHA-256 `fb3f3cefd9492eb8740315b1e567c447787f6af8b3504a6d2a36e5d11385d1bf`, 4,482,062,742 bytes, OBRE 10551 px x 7506 px · 11 capes (lleugera). Canvis efectius respecte de la V35: la LUT de linealitat de la Sony (fins a +1,9 % als píxels més brillants dels fotogrames Sony; a la base i als filtres el seu efecte és petit), el rang en radi continu de la RHEF, i cap altre: la vora dels 8 s, els anells parcials del NRGF i el farcit dels operadors isotròpics queden com a la V35 després de provar-ne cures i refusar-les amb la mateixa vara.

| capa | graó de GRA aparellat al contorn dels 8 s, ln(dins/fora) V35 → V36 (nul) | biaix d'anell al limbe 1,03–1,3 (σ) |
|---|---|---|
| 01 | +0.161 → +0.161 (+0.014) | 0.08 → 0.08 |
| 02 | +0.141 → +0.140 (+0.011) | 0.11 → 0.11 |
| 04 | +0.231 → +0.231 (+0.012) | 0.33 → 0.33 |
| 05 | +0.154 → +0.154 (-0.014) | 0.09 → 0.09 |
| 06 | +0.150 → +0.150 (-0.053) | 0.07 → 0.07 |
| P01 | -0.141 → -0.143 (-0.452) | 0.09 → 0.09 |
| P02 | -0.169 → -0.172 (-0.728) | 0.01 → 0.01 |
| P03 | -0.038 → -0.037 (-0.175) | 1.40 → 1.40 |
| P04 | -0.019 → -0.019 (-0.061) | 0.67 → 0.67 |
| P05 | -0.093 → -0.093 (-0.173) | 0.13 → 0.13 |

Base, gra fi al contorn dels 8 s (fora −250…−50 / dins +50…+250 px): V35 0.070/0.070 % → V36 0.070/0.070 % (la LUT no mou el gra; el graó del 14 % és el residu declarat).
NRGF, salt màxim entre anells de 0,005 R☉ a 1,00–1,10: V35 0.133 σ → V36 0.133 σ (NRGF sense canvis per disseny). RHEF: bandes de fase a l'eix −x fora als retalls (`C0_limbe_oest_P02_RHEF_V35_V36.png`); la mètrica de potència per files no les distingeix (la fase deriva amb x) i es declara.
Proves refusades, amb els números: finestra quadràtica dels 8 s (gra de la base a −800…0 px del contorn 0,072 → 0,081–0,084 %), esvaïment espacial 900 px (0,072 → fins a 0,093 % a −400…−250 px i 0,089 al contorn), compleció dels anells parcials del NRGF (1,003–1,02: −0,4 → +0,8 σ), farcit separable i dues màscares als operadors (ROI: WOW 0,36 → 1,83 σ, WOW bil. 0,19 → 2,16 σ).

## 6. Trampes d'aquesta ronda

- Una etiqueta que no s'ha imprès mai (`run.tren == 'sony'`) va deixar dues versions declarant una correcció que no hi era: **cap canvi declarat sense prova que ha entrat**.
- Un esvaïment espacial anclat al contorn de MIG pes treu pes també dins del contorn (on el fotograma en tenia 0–50 %): si s'esvaeix, cal anclar-ho al contorn de pes ZERO.
- Amagar un graó de gra del 14 % costa un gradient del 14 % en algun lloc; el compromís és intrínsec i es decideix pel cost de S/N, no per la mètrica de la vora.
- La forma azimutal dels anells sencers no serveix per completar anells parcials AL LIMBE (la corona hi canvia amb r): l'estimador de l'anell sencer val a la vora del llenç, no al forat.
- La mediana per fila d'un camp llis no detecta bandes de fase que deriven amb x: quan la mètrica i el retall no coincideixen, mana el retall i es diu.

