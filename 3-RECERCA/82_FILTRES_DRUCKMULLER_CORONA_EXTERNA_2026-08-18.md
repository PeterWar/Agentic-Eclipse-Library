# 82 — Filtres «Druckmüller» per a la corona externa: lectura dels papers, els filtres de Pere, i les capes dels dos trens

> ⚠️ **RECTIFICAT el 23-08-2026 (`research/96` §B.4).** Aquest document diu
> que el 2002 «interior i exterior de dos instruments processats a part i
> **cosits**». El paper **no diu enlloc** «stitch», «blend», «seam» ni cap radi
> de traspàs: **«cosits» és inferència nostra**. El que l'equip fa de veritat és
> registrar tots els fotogrames de tots els instruments a un camp comú i fer-ne
> **una sola composició ponderada** (LDIC). Precedents literals amb dos
> instruments dins d'una sola composició: 1994, 1995 (focals 6×) i 2023.

18 d'agost de 2026, vespre. Objectiu de Pere: «desenvolupar filtres Druckmüller» — (A) llegir
els 55 papers de `~/Desktop/Eclipse 2026/Papers Druckmuller/`, (B) mirar els filtres que té a
`Projecte photoshop/2-Filtres/` (els seus radial i tangencial d'Astrofalls, i el
`corona_vixen_detall` que troba útil), i (C) amb tots els apilats calibrats dels dos trens, la
millor manera de posar una capa al seu Photoshop per guanyar detall a la corona, sobretot
l'externa. Codi: `research/tools/filtres_druckmuller/`; lliurables:
`~/Desktop/Eclipse 2026/Projecte photoshop/2-Filtres/Druckmuller_2026-08-18/` (11 capes TIFF de
16 bits al llenç 7648×5353, màscara de coherència, NRGF de control, previsualitzacions, QA i un
`LLEGEIX-ME.md` amb la dosi de cadascuna). Lectures senceres dels quatre lots de papers a
`research/data/lectures_druckmuller_2026-08-18/`.

⚠️ La mateixa tarda una altra sessió alineava els filtres de Pere al llenç E (`research/80` §14,
`Filtres_alineats_7648x5353.psb`): és feina paral·lela i compatible; aquí no s'ha tocat.

## 1. El que els papers diuen que compta per implementar (més enllà de `research/73`)

| Font | El que decideix el disseny |
|---|---|
| Druckmüller, Rušin, Minarovjech 2006 | Radial blur (Spin) = comparar amb veïns sobre un arc: **cec a les tangencials**; test de colors blau/taronja (gris = igual). Nucli variable: fase ≈ 0, passa-alt «limitat pel soroll», simètric, zero entre parts diferents (Lluna/corona); Corona 3.0: 38 paràmetres, **8 barres de freqüència** (fig. 9: guany 1 a λ > 0,4 R☉, ~2 a 50 px, ~5 a 10 px, ~20 a 2 px, per a film) i **γ < 1 = «outer corona in higher contrast, this setting is usual»**. Cap σ, cap mida de nucli. 2002: interior i exterior de dos instruments processats a part i cosits. |
| Druckmüllerová 2013 (tesi) §5.2 | L'únic ACHF amb fórmula: **C = exp(−[(r−ρ)² + (r(φ−ϕ))²]/2σ²)**, gaussiana en (Δr, arc) = isòtropa en la imatge, σ fix en px (0,5–64), suport ±2σ; **convolució incompleta normalitzada per w** (Lluna, fora del camp, «parts diferents»); h = K1 f + K2 g. L'ACHF viu (Corona 4.1): «conjunt de filtres amb diversos σ, combinats» + «no-linealitat en l'ús de les imatges filtrades»: **no descrit**. §5.1: el filtre tangencial (Spin) té resposta sinc no monòtona i **fase a tot ⟨0,2π)**; amb finestra gaussiana el sinc marxa però la direccionalitat continua. Fig. 6.15: **σ de segment ∝ mitjana de segment** (contrast relatiu ≈ constant): treballar en ln L o normalitzar; un passa-alt lineal necessita guany creixent amb r. FNRGF: √V_n = 10–15 % del soroll (mediana dels 10 anells exteriors) sumat dins dels c,d; «FNRGF per a les estructures grans i a més alçada, ACHF per al detall fi, i composar» (sense proporció). |
| Druckmüllerová 2014 (curta) | FNRGF llum blanca TSE 2010: n_s = 150, A = (1; 0,99; 0,98…), C = (1; 0,98; 0,96…); A_k més lenta que C_k; mediana d'una passada abans per estrelles/impulsiu. |
| FNRGF ApJ 2011 | n_s = 50 fix, anells d'1 px, ordre 10; A ≈ (1; 0,85; 0,7; 0,55; 0,4; 0,25; 0,1; 0…), S ≈ (1; 0,9; 0,8…; 0); «**NRGF/FNRGF realcen estructures febles a més alçada que l'ACHF**»; FNRGF-N (restar m√DN) → repudiat a la tesi. |
| MGN 2014 | C = (B − B⊗k)/σ_w, arctan(0,7·C), w = 1,25–40 px, γ 3,2, h 0,7; **cap porta de soroll** (ho diuen: NAFE millor «at large heights off the limb»); LASCO C2: k 0,8, h 0,9, γ 1. |
| WOW 2023 | À trous B3 [1,4,6,4,1]/16, blanqueig w/√P local, **desbrollament erf(|w|/(n_s σ_s)) amb n_s = {5,3,1,0…}** (igual per EUV i LASCO C2), σ(k) espacial = √(gI + r²); bilateral edge-aware amb ν_s = variància local (sense paràmetre nou); sortida sense gamma; artefactes coherents (bandes, anells) s'accentuen: emmascarar abans. |
| RHEF 2025 | Rànquing per anell d'1 px, Υ(I; Υ_L, Υ_H) amb 0,35 per a C3; **admet que a baix S/N off-limb el soroll s'exagera** (noise-gating abans); «unsuitable for photometric applications». |
| SWAP 2023 | F = mediana azimutal ±15° en polars, blur σ 4; F' = (F + t0)^c0, t0 ≈ mediana, c0 = 0,75; I' = (I/F')^{1/4}: conserva un gradient suau; el soroll de les zones fosques puja si t0 baixa. |
| NAFE (tesi §5.4; Kalenská) | Equalització d'histograma difús local amb la CDF **convolucionada amb G_σ en l'eix d'intensitat** (= afegir soroll σ sense generar-lo: només actua on el veïnat és soroll); pensat per al disc; γ 2,6, w 0,2, σ 15 (8 bits). |
| Boe/Habbal 2020–2025, Pasachoff 2009/2014, Bemporad 2020 | Estructura real vista a ≥ 6 R☉ (stalks, CME) i 10–20 R☉ amb molta integració; **el cel es resta com a constant a tots** (Lluna, cantonada a 7,5 R☉ —on era el 80 % del senyal a 54°—, polarització); ningú modela gradient ni resta la F en banda ampla; camp ample descartat < 2 R☉ (RHT); Bemporad amb NRGF + DoG veu plumes a 3 i streamers a 5 R☉ amb un 300 mm f/5,6. Hanaoka: cel a 4 R☉ ≈ K+F a 4 R☉ (Sol a 13°). |
| Liu 2022 (Dragonfly, Canon 400/2,8), Talvala 2007, Hofmeister 2024 | Ales de PSF d'una lent semblant a la nostra: f_p 0,3, r^−3,6 (<54″), r^−2,9, r^−1,9 (>126″), eixamplades per pols/aerosols; deconvolució de glare amplifica quantització; BID +23 % de soroll. (No usat aquí.) |

Tres conseqüències directes: (1) **la porta de soroll és el criteri**, no la nitidesa: només WOW i
NAFE en porten una de veritat, i per a 2–6 R☉ cal el mapa σ(k) del compost; (2) per a **alçades
grans la mateixa Brno diu FNRGF/NRGF** (normalitzar per anell) i ACHF per al detall fi, i
composar; (3) el nucli ACHF en (Δr, arc) i el log-polar del pipeline són la mateixa idea (bandes
que segueixen la geometria solar), amb la diferència que aquí les bandes són en graus.

## 2. Els filtres que Pere ja té (B), llegits amb els papers a la mà

- **`filtres_radials.tif`** (llenç 6748×4553): base + `filtre radial A` i `B` en **Overlay**, en
  color (RGB), gris 50 % ± (base − radial blur Spin). És l'unsharp radial d'Espenak: Druckmüller
  2006 §4.1 i tesi §5.1: **cec a les estructures tangencials** (cims de bucles, helmet
  streamers), resposta sinc no monòtona i fase a tot el rang → **estètic, mai base de mesura**. A
  més va en color: hi entra el creuament de color de la Vixen (rim taronja/blau als 2,5–4 R☉) com
  a «detall». `research/80` §14: el radial A va invertit.
- **`filtres_Tangencials.tif`** (6961×4641): tres còpies de la base + `a`, `b` (pas alt tangencial
  = zoom blur restat, en color, mode Normal). Mostra les vores dels anells de saturació de l'HDR i
  el rim de color com a estructura; `research/80` §14: `a` i `b` van invertits.
- **`corona_vixen_detall.png`** (reixa del pipeline): `hdr_corona_vixen.py vis` → `realca()`,
  l'MGN de Morgan i Druckmüller (dividir per la σ local a σ = 6…64 px, arctan, porta Wiener) sobre
  L/perfil radial + log al 72 %. És «útil» perquè iguala el contrast a tots els radis; el preu
  (`research/76`, mesurat): jerarquia real 124:1 → 2,7:1, radis rectilinis i trama fina fabricats.
- **`corona_vixen_PASSALT(_FORT)`**: el log-polar viu (`detall_logpolar`), additiu, bandes en
  graus, porta Wiener, només Vixen, guanys a zero per damunt de 12,8° i cap boost radial: pensat
  per a la FOTO sencera, no per a la corona externa.
- **`Aplicant_Filtres.tif`** (7648×5353): el seu compost actual (Vixen + Sony encaixada + capa A
  del limbe). Sol mesurat per correlació de la corona amb l'HDR: **(4021,35, 2737,90)** (l'altra
  sessió: P + (542,6, 418,5) → (4021,6, 2737,5); 0,25/0,4 px de diferència, sota el que importa
  a 2–6 R☉).

## 3. Els apilats calibrats disponibles (C)

| Producte | Què aporta a la corona externa |
|---|---|
| `Corona_HDR_Vixen/hdr_vixen_countss.npy` (+ var, cobertura) | 68 fotogrames, 15 EV, ADU/s, mapa de variància, RETALL 85..4595 × 40..6830, Sol (3479, 2319). Cobreix ±5,1 R☉ vertical, ±7,6–8 horitzontal. **La font principal**; dins de 3,3 R☉, l'única. |
| Apilat Sony ≥ 1 s (`encaix_sony/apila_sony.py`, 7 ARW, 24 s; flat del 300 mm de `research/80` §9) | Cremat fins a 3,3 R☉ (3,75 als plomalls); de 3,3 enfora recull tanta llum com la Vixen (107 mm × 24 s ≈ 90 mm × 31 s), camp més gran (±8,9 R☉ vertical). Escala 1,49× més grossa: no aporta res per sota de ~5–8 px del llenç (PSF 11″). |
| `HDR4/` (9 DNG per exposició) | El seu HDR manual d'interiors; per a la corona externa no afegeix res que no sigui a l'HDR. |
| `300mm/calibrated/` (194 TIFF lineals) | Els fotogrames Sony individuals; l'apilat de dalt ja els resumeix per a > 1 s. |
| `Earthshine_FINAL/`, `Estrelles/` | No hi entren (la Lluna es posa a 0; les estrelles no s'han emmascarat: són puntuals i les bandes ≥ 0,44° les ignoren). |

## 4. El mètode (`prepara_lluminancia.py` → `filtre_corona_externa.py`)

**Preparació al llenç E (7648×5353).** Vixen: L = (G + 1,2545·R)/2, translació subpíxel
(+542,35, +418,90), σ del mapa ×κ (κ = 0,29 amb el shift bilineal; empíric 0,5 ADU/s per píxel a
4 R☉). Sony: (G + 2,380·R)/2 amb flat, similitud de les 7 estrelles (1,48860, 33,088°) i la
**translació refinada per correlació creuada PLANA de la corona** (banda 8–50 px, anell 3,4–5,2 R☉,
màscara suau; la correlació de fase hi posa un pic fals a l'origen per la màscara compartida):
residu (+0,22, −0,14) px, corr 0,81. ⛔ Per sectors hi ha **problema d'obertura**: els raigs són
radials i cada sector només fixa la component tangencial; el gir residual per la component
tangencial és +0,013° (0,4 px a 4,3 R☉) i l'escala no és observable (es pren de les estrelles).
Aparellament L_v ≈ 0,2778·L_s + pla (rms 4 ADU/s; raó per anell 1,001–1,006 de 3,4 a 7 R☉);
**costura**: (L_s − L_v) suavitzat σ 200 px restat a la Sony i la Vixen esvaïda 150 px cap a la
vora de la seva caixa (sense això la vora sortia com una línia a les capes). Soroll Sony empíric
per anells (transferència calibrada amb soroll blanc passat pel mateix warp) ×1,49 (per unitat
d'àrea del llenç): 0,6 ADU/s; combinació 1/σ²: pes Sony 0,42–0,47, σ combinada 0,73–0,77 la de la
Vixen. La Sony compta de 3,3 R☉ (rampa fins a 3,6) enfora.

**Filtre, en log-polars 8192×3072 (r 400–4869 px), com el `detall_logpolar` viu:** x = ln L (cel
inclòs), fons de Fourier m ≤ 4 per columna (el terme a_0…a_4 del FNRGF), R = x − F; bandes DoG en
graus (0,10 … 34°) isòtropes en la imatge; **soroll per banda i columna** mesurat sobre una
realització sintètica amb l'estadística exacta de cada font (drizzle 2×2 + shift la Vixen, warp
×1,49 la Sony, la mescla ponderada per a la combinada), dividida per L; porta de Wiener
w = max(0, 1 − (t_j·n_j)²/v_j) amb **llindar de significació per banda t_j = 3 … 1** (l'esperit
dels n_s = {5,3,1} del WOW: sense això a S/N ~ 1 la porta quedava mig oberta i el soroll sortia
en grumolls); cada banda ve de la combinada si la seva σ d'imatge és ≥ 8 px i de la Vixen sola si
és fina (fos 5–8 px). Dues sortides:
- **ADD** = Σ g_j(ρ)·w_j·b_j — additiu, jerarquia conservada; guanys per banda (MITJA:
  0/0,5/1,5/3/4,5/5/5/4,5/3,8/2,8/1,6/0,8 de 0,10° a 34°) × rampa exterior (0 → 1 entre 1,8 i
  2,8 R☉, → 0 entre 6,5 i 7,5) × **γ_r = 1 + 0,5·(r − 2)** acotat a 2,5 (el γ < 1 del Corona);
- **WHITE** = Σ g_j·w_j·b_j / √(v_anell + n_j²) — **blanquejat per ANELL** (potència de la banda
  per columna amb dos harmònics azimutals atenuats 0,7/0,4 = els C_k del FNRGF; mitjana no
  robusta: els raigs no són atípics), pis de soroll n_j; guanys plans fins a 4,9°, baixos després
  (les bandes > 8° igualades són taques de cel); rampa fins a 4,6–6 R☉; escala 0,18/√Σg². El primer
  intent normalitzava per la σ LOCAL 2-D (MGN): omplia el camp de grumolls igualats.
- **COH**: la mateixa capa × porta de coherència entre trens c_j = ⟨b_v b_s⟩/√(⟨b_v²⟩⟨b_s²⟩) (finestra
  4σ_j), smoothstep(0,05 → 0,55), només on hi ha les dues i r > 3,6–4,1 R☉ (vora de saturació
  Sony suavitzada 3σ).
Component d'anell restada per columna abans de tornar a la imatge; tanh a ±0,9; capa = 0,5 +
0,5·D/0,9 (la convenció del PASSALT), 16 bits, ICC sRGB, disc lunar (r < 470 px des de (4034,7,
2736,7)) a 0.

## 5. Resultats i QA

- **Coherència entre trens per banda a 3,6–5 R☉** (mediana del c_j): 0,10–0,17°: 0,02 ·
  0,17–0,27°: 0,05 · 0,27–0,44°: 0,13 · **0,44–0,71°: 0,35 · 0,71–1,16°: 0,71 · 1,16–1,86°: 0,88 ·
  1,86–3°: 0,93 · 3–4,9°: 0,95 · 4,9–7,9°: 0,95 · 7,9–12,8°: 0,93 · 12,8–34°: 0,90–0,92**. És la
  mesura de **quines escales són reals a la corona externa amb aquestes dades**: a 4 R☉, de
  0,5–0,7° (15–22 px) enfora; per sota, soroll de cada tren. Correlació global de la capa Vixen
  sola contra la Sony sola a r > 3,4: **0,926**. Cap paper llegit dona un número així (`73` §5.6,
  prova 2).
- **Test de colors** (`QA/QA_colors_vixen_taronja_sony_blau_x3.jpg`): raigs grisos fins a la
  vora; taques del camp llunyà (r > 5) taronges o blaves → d'un sol tren (cel, PRNU, costures de
  fotogrames Sony), no corona.
- **Test d'anell** (mitjana per anell de 0,1 R☉ de D): ADD SUAU 0,08 %, MITJA 0,30 %, FORT 0,82 %;
  WHITE 1,2–1,3 %; TOTCAMP ADD 0,79 %. Per sector 10–30 %: és l'estructura real (bandes fins a 34°).
- **Simulacions** sobre `Aplicant_Filtres.tif` (`previes/simul_*`): EXTERIOR_ADD_MITJA a 60 % treu
  els streamers fins a la vora del camp sense costures ni anells; WHITE a 35 % és massa (grumolls
  a 4,5–5,5 R☉ i vora del disc de 6 R☉ visible): 15–25 % i amb màscara; la COH és més neta.
- Costos: preparació 30 s; filtre 6,5 min (11 capes) al Mac.

## 6. Què queda i trampes

1. La Sony hi entra només com a apilat ≥ 1 s (dins de 3,3 R☉ tot és Vixen): l'HDR del tren Sony
   (`79` §3.2) permetria portar les dues càmeres també a 1,5–3,3 R☉.
2. Cap deconvolució ni model de halo (G3): la capa amplifica el que hi ha, halo inclòs.
3. Al camp llunyà (r > 5 R☉) el que iguala el WHITE és cel/camp; les bandes > 8° s'hi han deixat
   quasi a zero; l'ADD hi és honest però ho ensenya poc. La `MASCARA_coherencia` només és definida
   a 3,6–6,5 R☉.
4. ⛔ Trampes pagades: correlació de fase amb màscara compartida = pic fals a l'origen (cal
   correlació plana amb màscara suau); problema d'obertura per sectors sobre raigs radials;
   normalitzar per σ local (MGN) omple el camp de grumolls igualats — per anell (FNRGF) no;
   `fons_fourier` robust (MAD) sobre b² es menja els raigs; la vora de la caixa Vixen dins la
   combinada surt com una línia si no s'esvaeix la Vixen i no s'aparella la Sony a baixa freqüència;
   la porta w = 1 − n²/v sense llindar deixa passar grumolls a S/N ~ 1.

## 7. Nit: el veredicte de Pere i el `corona_vixen_detall` refet (v2)

Pere prova les onze capes: el `CONTROL_NRGF_gris` «em pot ser útil», però **l'únic que
indubtablement aporta molt valor és `corona_vixen_detall.png`** (el `vis` del 17-08: log 72 % +
`realca` MGN 28 %), i marca els seus artefactes: els dos anells grossos (5,2 i ~7,6 R☉), feixos de
línies rectes paral·leles al voltant del disc (horitzontals a esquerra i dreta, verticals a dalt i
baix, diagonals a la resta), un «polígon» a la dreta i dos punts.

Diagnòstic (retalls a 1:1 i 2×): les línies són **radials** (rectes que apunten al Sol) i van amb una
trama fina de període 4–5 px: la «pinta» que `realca` fabrica dividint per la σ local a σ = 6 px
—reixa del drizzle (2 px), PRNU residual i fils reals del limbe, tots al mateix contrast—; mesurat a
la banda 0,22–0,35° al cel de 4,2–5,2 R☉: **potència ×4,5 el soroll de fotons** (sistemàtic). Els
anells són el colze del `perfil_azimutal` extrapolat (cercle inscrit) i la fi del sector mesurat.
El polígon, trossos d'arc de les fronteres de saturació.

`detall_mgn_v2.py` (mateixa recepta, al llenç E, dos trens de 3,3 R☉ enfora): log de `net` com la
v1; MGN en log-polars amb fons de Fourier per anell (cap anell), bandes en graus 0,22–14° que
s'apaguen entre 2,2 i 3,7 px d'imatge i per damunt de 60–120 px (com els 6–64 px de la v1),
C_j = b_j/√(σ²_local(2σ) + n_j²), arctan(k·C), llindar de significació per banda, component
d'anell zero, esvaïment 4,8→6 R☉ i fora de la caixa Vixen (250 px). Variants: SUAU (k 0,5, F_SIST a
totes les bandes) i FORT (k 0,7, sistemàtic només a la banda més fina, bandes fines ×1,6–1,7), mescles
28 i 40 %, i MIX (FORT 40 dins de 2,3 R☉ → SUAU 28 des de 3,3). Potència per banda (nivells de 8
bits, 1,15–1,6 R☉, bandes < 2 / 2–4 / 4–8 / 8–16 / 16–32 / 32–64 px): v1 1,50 / 1,42 / 2,37 / 2,98 /
3,37 / 7,09; v2 SUAU 28 0,32 / 0,39 / 0,93 / 1,52 / 2,44 / 7,07; **v2 FORT 40 0,61 / 1,26 / 2,86 /
4,15 / 4,91 / 7,95**: la pinta (< 4 px) a un terç, el detall de 4–64 px igual o més. Lliurat a
`2-Filtres/Druckmuller_2026-08-18/detall_v2/` amb comparatives 1:1.

⚠️ El que ensenya això per al pipeline: el `vis` viu (`hdr_corona_vixen.py`) continua produint el
`corona_vixen_detall` amb `realca` sobre `L/perfil`; si es torna a generar, que sigui amb la v2 (o
que `vis` importi `polar_utils`).
