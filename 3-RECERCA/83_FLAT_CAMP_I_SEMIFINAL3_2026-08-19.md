# 83 — El flat artificial del camp i FiltresSEMIFINAL3.psb (nit del 19-08-2026)

Encàrrec de Pere abans d'anar a dormir: un projecte nou `FiltresSEMIFINAL3.psb` amb la mateixa
base que la SEMIFINAL2 i les capes que hi tenia actives (amb màscares), prototips nous de filtre
en la línia dels dos que li han anat bé (`corona_detall_v2_40` i el radial B «d'Espenak»), en TIF
i com a capes amb màscara, i **un flat artificial** que deixi tot el camp homogeni sense crear cap
artefacte radial on s'acaba la corona externa. Codi a `research/tools/filtres_druckmuller/`
(`flat_camp.py`, `capes_semifinal3.py`, `construeix_semifinal3.py`); lliurables a
`2-Filtres/FiltresSEMIFINAL3.psb` i `2-Filtres/SEMIFINAL3_capes/` (amb el seu `LLEGEIX-ME.md`).

## 1. Què tenia el camp de la base (Aplicant_Filtres.tif = llenç E)

Diagnòstic sobre la base sola i sobre la composició de la SEMIFINAL2 (residu després de treure la
mediana azimutal, i vista polar angle–radi amb la derivada radial):

| Artefacte | On | Mida |
|---|---|---|
| arc de màscara circular | r = 3829–3841 px (8,6 R☉), a les quatre cantonades | graó de +0,037 a −0,009 segons l'angle (fins a 4,5 nivells de 255); el signe canvia amb l'angle: és la vora d'una màscara sobre una capa que difereix de la base d'una quantitat variable |
| segon arc | r ≈ 4565–4605 px (10,3 R☉), només al racó superior esquerre | més fluix |
| caixa de la capa Vixen | rectangle (600,550)–(7348,5103) i les franges fosques ~700 px de dalt i de la dreta | suau, 2–5 nivells |
| triangles del marc Sony | racons superior esquerre i inferior dret (marc girat 33°) | el cel «cosmètic» de fora és més fosc, transició ~100 px |
| costura vertical | x = 4020 = x_Sol, files 0–450 (graó +0,0044 → +0,0015) i 5050–5353 (−0,002 → −0,0043) | embolcall polar de Photoshop (12 i 6 en punt) |
| gradient real del cel | tot el camp | −4,95 unitats de L per 1000 px cap avall (i −0,15 en x); a la LUT de la base ≈ 6 nivells de dalt a baix |
| cantons foscos | els quatre | 5–15 nivells |

I de les capes actives: el **radial B** té al seu camp llunyà desplaçaments suaus de ±0,01 i un
racó inferior esquerre a 0,43–0,47 (el «pedaç» rectangular que es veia a la composició: és la
cantonada del bbox de la capa); el **NRGF de control** té ±0,5 d'estructura no radial de gran
escala al camp llunyà (al 9 % són dos nivells de gradient); el **v2_40** només porta, més enllà
de 6 R☉, el cel de la imatge log amb un pla i les cantonades del marc.

## 2. El mètode del flat: contra una referència física, no contra si mateixa

Un DBE fet només sobre la base no pot distingir un raig de 600 px d'una franja fosca de 700 px.
El que sí que ho distingeix és la **lluminància calibrada dels dos trens al mateix llenç**
(`lum_llenc.npz` de `research/82`: HDR Vixen + apilat Sony ≥ 1 s aplanat i aparellat), que no ha
passat per cap màscara de Photoshop. Mesurat a ×4: la base és una funció **molt estreta** de
ln L_c (σ 0,004 / 0,008 / 0,012 en R / G / B a 2–10 R☉, o sigui 1–3 nivells). D'aquí:

1. `L_model` = L_c − pla del cel (ajustat a r > 6 R☉ iterant amb el perfil azimutal), amb la
   validesa **erosionada 40 px** (la vora del marc Sony porta una tira brillant a L_c) i el racó
   sense Sony omplert per extrapolació suau del residu (σ 120 px); suavitzat 2 px.
2. `T_c` = LUT monòtona base_c ↔ ln L_model per canal (mediana per bin, ajustada a 2–10 R☉).
3. **El guany de Pere.** La base porta l'estructura no radial de la referència multiplicada per
   un guany g(r) que ella no té (extensió radial, detall tangencial, corbes): pendent robust de
   base_nr sobre T_nr per anell = 1,1 (1,75 R☉), 1,6 (3,25), **2,0 (4,25–4,75)**, 1,7 (5,75), 1,3
   (7,25), 1,0 (≥ 8,75). Δ = base − T − (g−1)·(T − T_m0). Sense això la primera versió del flat
   **esborrava els raigs exteriors** (els prenia per artefacte).
4. Δ0(r) = mediana azimutal de Δ (la part radial: hi viu l'arc de 8,6 R☉ i les diferències de
   LUT); Δ_nr = Δ − Δ0 → passabaix σ 24 px + **zones de vora** exactes (|G2 − G10| > 0,002 en
   components de ≥ 60 px, més les bandes geomètriques: costura ±60 px a x = 4020, arcs
   3800–3870 i 4540–4630 px), amb una porta que les apaga on el model T és sorollós.
5. Corr = w1·LP(Δ_nr) + w1e·E·(Δ_nr − LP) + w2·Δ0, amb **w1 5→6,5 R☉** (part suau), **w1e
   3,5→5** (vores dures) i **w2 6→7,5** (radial), tot smoothstep. Capa Linear Light: 0,5 − Corr/2.

## 3. La trampa que Pere temia, trobada i esquivada

Amb w1 a 3,5→5 R☉ el flat treia també l'**halo de color** de la capa Vixen de Pere (blau/verd,
fins a 5,8 R☉, +0,016 en B a 5,25 R☉ al quadrant superior dret) i el perfil corregit feia un
**colze** a 5,5 R☉ (la referència toca el terra del cel de la LUT abans que la base): a la vista
del quadrant era una vora suau «on s'acaba la corona». Solució: la part suau del flat no entra
fins a 5 R☉ i és plena a 6,5, on la base i la referència ja són planes totes dues; les vores dures
sí que s'arreglen des de 3,5. Perfil per sectors de la base corregida (B, quadrant superior
dret): 0,216 (5,0) → 0,207 (5,5) → 0,199 (6,0) → 0,197 (6,5) → 0,197 (7): cap colze nou; a la
vista polar del residu no queda cap línia vertical de 3 R☉ enllà.

## 4. Capes «camp net» i prototips

- Radials B: menys w(r)·LP₆₀(capa − 0,5) amb w de 4,5 a 6 R☉ (l'original queda ocult al PSB).
- v2_40: de 5,5 a 6,5 R☉ passa al seu perfil azimutal.
- NRGF: menys w(r)·LP₁₂₀(capa − perfil azimutal), w de 4,5 a 6 R☉.
- Prototips sobre la luminància de la base **ja corregida**, capa grisa 0,5 + 1,2·HP, Overlay
  60 %, màscara radial 0 al disc / 1 d'1,1 a 5,5 / 0 a 7 R☉: `ESPENAK_multiescala` (Spin 2°, 6°,
  18°; 0,4/0,35/0,25), `ACHF_lite_isotrop` (gaussià σ 12 i 36 px, el nucli isòtrop de la tesi
  §5.2), `ESPENAK_ampli` (polar: 6° d'arc × ~30 px radials). El desenfoc polar es normalitza per
  la cobertura del marc; sense això la vora del llenç deixava una vinyeta.

## 5. Regles que en surten

- Per corregir un compost de Photoshop, la referència és la lluminància calibrada del mateix
  llenç, i la base s'hi ajusta com a LUT + guany per anell; el que sobra és artefacte.
- Cap rampa radial no pot començar on la base i la referència encara difereixen de manera
  llisa (halo, guany): la part suau entra on totes dues ja són planes; les vores dures poden
  entrar abans.
- La vora d'un marc registrat deixa una tira a la lluminància combinada: erosionar la validesa.
- Els prototips i les capes de detall han de tenir el camp llunyà neutre (0,5 o el propi perfil
  azimutal); si no, en Overlay/Linear Light tornen a embrutar el camp que el flat ha netejat.

## 6. El HALO (19-08, migdia i tarda) → `FiltresSEMIFINAL4.psb`

Pere torna amb la SEMIFINAL3 retocada (radial B original al 40 % damunt del «camp net», la màscara
del NRGF substituïda pel NRGF net amb corba, la màscara de la FLAT pintada a zero sobre les
protuberàncies: **«la part de les protuberàncies no es toca per cap filtre, és sagrada»**) i amb
l'ordre: **eliminar el HALO** (un anell ample i gris-blanc de ~3,5 a ~5,5 R☉ que s'acaba amb una
vora suau sobre el cel blau; cap DBE de PixInsight li funciona).

### 6.1 Diagnòstic: un genoll de la corba de to, no llum mal restada

Corba de to de la base (ja corregida de camp) per canal contra la lluminància física L (mediana
per bin de 4 ADU/s, r > 3 R☉; L = 302–311 és el cel, 440 ≈ 3,5 R☉, 370 ≈ 5, 356 ≈ 5,6, 330 ≈ 8):

| canal | terra | tram dret | per damunt |
|---|---|---|---|
| R | 0,0885 fins a L=310 | pendent 0,009–0,012 per 10 L des de 318 | 0,009/10 |
| G | 0,1449 fins a **L=330 (8 R☉)** | 0,005–0,009/10 a 330–380 | 0,005/10 |
| B | 0,1970 fins a **L=356 (5,6 R☉)**, amb un petit enfonsament a 0,1955 a L≈350 | **0,0076/10 a 356–382 (r 5,6→4,3)** | 0,002/10 |

O sigui: en blau (i en verd) un tram dret que pinta un anell clar a 4,3–5,6 R☉ i un terra dur
just després: el «halo» és la banda de Mach del genoll, més el canvi de color (gris → blau) que
s'hi atura. El test per sectors ho confirma: el genoll del blau cau a L ≈ 340–372 (constant a
±5 %) mentre r_knee va de 5,1 a 6,2 R☉ segons el sector: és la corba, no una màscara radial
(una màscara tallaria tots els sectors i tots els canals al mateix r). Contrast adversarial
(workflow): d'acord amb el diagnòstic; avisa que l'Hermite amb pendent zero al terra no s'ha
d'aplicar al vermell (no té terra), que l'additiu pot empènyer el fons entre raigs per sota del
terra, i proposa els tests de l'apartat 6.4.

### 6.2 Què és físicament la llum del halo

Amb el factor absolut de `research/75` (2,77·10⁻¹¹ B☉ per ADU/s, ±10 %), l'excés de L sobre el
cel val 4,0·10⁻⁹ B☉ a 3,5 R☉, **1,9·10⁻⁹ a 5**, 1,4·10⁻⁹ a 6 i 8·10⁻¹⁰ a 8 R☉: dins d'un factor
~1,5 del K+F esperat (K de Baumbach + F). **És la corona exterior real (K+F, i potser una mica
d'aurèola), no un artefacte.** La corba de Pere la pinta com un halo gris damunt d'un cel blau
perquè el vermell té pendent fort a L baixa i el blau té el terra. «Eliminar el halo» vol dir,
doncs, restar la component azimutalment uniforme de la corona exterior, que és exactament el que
fan el fons mensual de LASCO i els filtres radials de Brno; s'ha de dir així.

Els dos fons de PixInsight de Pere (agent XISF): l'ABE (grau 4, sobre FiltresSEMIFINAL2 /2) i el
GraXpert **no són plans: són funcions radials centrades al Sol més l'asimetria nord** (un pla
n'explica el 3–40 % de la variància). De 5 R☉ enfora l'ABE coincideix amb la imatge a ±0,005:
restar-lo esborra el 100 % de la llum de 5 a 9 R☉ i el 58–98 % a 3–5 (residu negatiu de 5,25 a
8 R☉); el GraXpert és un passabaix de la imatge mateixa i s'enduria el 80–98 % a 3–6 R☉ amb un
residu que creix amb el radi. Per això «cap DBE funcionava».

### 6.3 La correcció: `halo_uniforme.py` (Linear Light damunt de la FLAT)

1. p_q(r) = envolupant inferior per anell de L (percentil 25; de 6,5 a 8,5 R☉ passa a la mediana
   perquè el camp llunyà quedi al nivell del cel dels cantons); cel = mediana de L a r > 9,5.
2. A(r) = w(r)·(p_q − cel), w = smootherstep(3,2 → 5,5 R☉) («fora») o (3,2 → 7) («suau»).
3. L' = L − A(r), amb retall suau per sota del cel (asímptota −6 ADU/s).
4. Corba objectiu S_c(L): igual a la corba mediana D_c per a L ≥ 440; entre 310 i 440, Hermite
   monòton amb el pendent **de la corda** al terra (no zero: els raigs no han de morir al terra; al
   vermell S ≈ D) i el valor i pendent de D a 440; continuació lineal per sota de 310.
5. Δ_c = S_c(L') − D_c(L) per píxel (additiu: conserva l'estructura), més un terme radial ρ_c(r)
   perquè la mediana per anell caigui exactament sobre S_c(L'_mediana) (la base no segueix la corba
   mediana anell a anell, ±0,003; sense això quedava un anell fosc de 0,5 nivells a 5,6 R☉), i
   **saturació suau del Δ negatiu a −(V − terra)**: cap píxel baixa del cel, i els que Pere ja
   tenia per sota (el sud fosc) no es toquen.
6. Capa ANELL a dalt de tot (`construeix_semifinal4.py`): ρ₂(r) = mediana per anell de
   (base+FLAT+HALO) − mediana per anell de la composició amb els filtres de Pere (Overlay): els
   filtres enfosquien el camp exterior 1–1,5 nivells de mitjana (0,002–0,006), cosa que el halo
   amagava. Radial i llisa; s'ha de recalcular si es canvien opacitats o màscares.

### 6.4 Resultat i QA

- Perfil azimutal de la composició final (R/G/B): 5 R☉ 0,101/0,151/0,200 → 5,5 0,098/0,150/0,199
  → 6 0,098/0,150/0,199 → 7 0,094/0,148/0,198 → 9 0,089/0,145/0,197: monòton, sense genoll;
  vista polar sense cap línia vertical; el sud (+60°…+120°) conserva la pujada de 5 a 6 R☉ que ja
  tenia la base de Pere (el seu sud fosc, més fosc que el cel), no se n'afegeix cap.
- Estructura azimutal (σ per anell de la luminància): 4 R☉ 0,0194 → 0,0186; 5 R☉ 0,0181 → 0,0133;
  6 R☉ 0,0080 → 0,0066: els raigs es conserven amb un 25–30 % menys de contrast a 5 R☉ (el tram
  dret del blau era un guany que Pere hi havia posat; és el preu, i els filtres Overlay el
  recuperen en part).
- Zona de les protuberàncies: Δ ≡ 0 dins de 2,6 R☉ i la màscara de les capes HALO és la que Pere
  va pintar a la FLAT; la composició hi és idèntica.
- Lliurables: `2-Filtres/FiltresSEMIFINAL4.psb` (la SEMIFINAL3 de Pere tal com l'ha deixada + HALO
  fora (visible) + HALO suau (oculta) + ANELL a dalt), TIF a `SEMIFINAL3_capes/`
  (`HALO_fora_LinearLight.tif`, `HALO_suau_LinearLight.tif`, `ANELL_compensa_filtres_LinearLight.tif`,
  `Base_corregida_camp_i_halo.tif` plana per a PixInsight) i comparatives
  `SEMIFINAL3_vs_4_composicio.jpg`.

## 7. Segona volta: «encara veig el halo» → apilat Sony v2, capa de detall exterior i avaluació externa (19-08, tarda)

Pere encara veu el halo a la SEMIFINAL4 i demana (a) repassar les fotos del 300 mm i fer un apilat nou amb
tots els fotogrames de més de 1/8 s, sense el retall del 85 %, per tenir el màxim SNR a la vora del camp;
(b) posar-lo al projecte per veure si el detall de la corona exterior trenca l'efecte halo; (c) desar-ho en
un projecte nou i que Codex avaluï; (d) consultar un LLM de visió per OpenRouter.

### 7.1 Apilat Sony v2 (`research/tools/encaix_sony/apila_sony_v2.py`, `~/Desktop/Eclipse 2026/300mm_apilat_v2/`)

13 fotogrames (1/8 ×3, 1/4 ×3, 1 s ×2, 2 s ×3, 8 s ×2; 06988 i 06990 fora pels salts), reixa de la 06993,
pes = exposició (25,1 s contra 24), saturació al nivell físic (16100) en lloc de 15600/85 %. Els sis nous
(sense astrometria) es registren per correlació plana de la corona (1,25–3,6 R☉, banda 6–40 px del ln)
contra la 06993 processada, amb el warp A→C al grup A: residus 0,1–0,3 px, coherents amb els offsets del
grup (06992 → (1,02, 4,86) contra la mitjana C (0,98, 4,76); 06982/06986 → (−233,1, 713,2) contra
(−233,2, 713,0)); la 06989 (grup B, entre salts) a (−6,1, 693,8). Masterdarks nous de 1/4 i 1/8 s (24
fotogrames cadascun). **Guany de SNR a la vora: ~1,5 %** (σ passa d'1,34 a 1,32 ADU/s a 4–5 R☉ i d'1,12 a
1,10 a 8–9): els curts no porten fotons; el que guanya és la corona interior (saturació aixecada). La
lluminància combinada es regenera (`treball2/lum_llenc.npz`, pes Sony 0,43–0,47, sense canvis apreciables).

### 7.2 Capa «DETALL EXTERIOR» (`detall_exterior_v2.py`, mode COH)

El que sí que pot trencar el halo és ensenyar l'estructura real a 3,5–6 R☉ en lloc d'un resplendor llis.
Log-polar, fons de Fourier m ≤ 4, bandes DoG en graus; per banda, **coherència entre trens per
correlació creuada normalitzada local** (finestra 2·σ₁) entre la banda Vixen i la banda Sony: pes
clip(c,0,1)^1,5 sobre la mitjana de les dues (on només hi ha Sony: porta de Wiener amb el soroll real
mesurat com var(b_v − b_s)/2 a la zona comuna, ×0,5). Amplitud en règim quasi lineal (tanh(D/2,5·p99)).
Finestra 2,8→4,2 R☉ d'entrada (Codex: l'entrada a 3,2–3,6 feia una vora de textura), 5,5→7,5 de sortida,
costura de la caixa Vixen apagada ±150 px. **Control nul**: amb la Sony girada 180° en angle la
coherència cau de ⟨c⟩ 0,53–0,99 a 0,05–0,10 i l'estructura coherent un factor 8–26 per banda: el que la
capa ensenya és comú als dos trens alineats, no geometria del filtre. Capa Linear Light al **25 %**.
Abans (v2: bandes des de 0,5°, coherència per signe, 40 %) els tres avaluadors la trobaven «pintada».

### 7.3 Avaluació externa (Codex pel pont; Gemini 3.1 Pro i Grok 4.6 per OpenRouter, visió)

Sobre A (SEMIFINAL3 de Pere), B (SEMIFINAL4: halo fora) i C (SEMIFINAL5 v2: B + detall al 40 %):
- **A**: halo clar (3/3, 2/3, «clar») a 3,5–5,5 R☉, tots tres.
- **B**: halo eliminat (Gemini 0–1, Grok 1 «subtil», Codex «el halo principal desapareix, sense vora dura
  a 5,5»; Codex hi veu un pedestal exterior molt subtil a 7,5–9,5 R☉; Gemini troba que els plomalls es
  tallen massa de pressa).
- **C (v2)**: cap halo, però la capa de detall es veu artificial (raigs massa regulars, «starburst»
  confinat per la finestra; Codex: σ(C−B) 0,0155 a 3,55 R☉, demana ≤ 0,008, entrada a 4,2, fora la banda
  0,5–0,8°, opacitat 20–25 %; Gemini: treure-la; Grok: baixar-la). → v3 d'aquí dalt.
- Decisió: HALO per defecte amb R2 = 6,0 R☉ (punt mig entre «fora» 5,5 i «suau» 7,5; la «suau» queda
  oculta), detall v3 al 25 %, i segona ronda d'avaluació sobre la SEMIFINAL5 definitiva.

### 7.4 Segona ronda sobre la SEMIFINAL5 definitiva (HALO 3,2→6,0; detall v3 al 25 %)

- **Gemini 3.1 Pro**: A halo 3/3; B2 0,5 («la rampa ha funcionat, cap vora dura»); **C2 0: «en afegir
  detall direccional es trenca per complet qualsevol percepció de frontera circular»**; cap artefacte nou;
  estructura exterior «molt natural»; veredicte C2, pujar la capa al 30–35 %.
- **Grok 4.6**: A 2; B2 1 (residu molt subtil 4–6 R☉); C2 0–1; sense anells, fossat ni vores; estructura
  «natural, raigs coherents»; veredicte C2, pujar al 30–40 % i repetir el control nul.
- **Codex**: «es sosté, visualment»: cap anell, fossat ni vora; cap vora de textura ni starburst;
  σ(C2−B2) 0,0022 (3,45 R☉) → màx 0,0038 (4,05), dins del ≤ 0,008; el pedestal de 7,5–9,5 R☉ (B2−A
  +0,002…+0,004 als sectors laterals) és l'ANELL que compensa l'enfosquiment dels filtres, no una vora;
  demana controls nuls a més angles i piles Sony partides abans de tancar; no tocaria res més a C2.
- Controls nuls afegits a **90° i 137°**: ⟨c⟩ 0,03–0,11 contra 0,53–0,99 real; estructura coherent un factor
  4–16 per sota. σ(C2−B2) al compost de 16 bits: 0,0011 (3,4 R☉), 0,0032 màxim (4,0), 0 a 7 R☉; mitjana
  per anell ≤ 0,0001 (la capa no toca el perfil radial).
- Pendent (no fet): piles Sony 6+7 independents amb correlació amb el Vixen a totes dues.

### 7.5 El color del cel → `FiltresSEMIFINAL6.psb` (19-08, vespre)

Pere: «la mescla de colors no sembla natural… un blau menys marí i més blau-grisós, com la capa externa de la
corona». El cel del compost era 0,093/0,146/0,197 (to 210°, saturació 0,53) i la corona exterior a 3,5–4,5 R☉
0,171/0,186/0,215 (saturació 0,2): la transició corona → cel era de croma, no només de luminància, i l'ull hi
llegia una vora. `cel_blau_gris.py`: dues capes Linear Light només sobre el cel (màscara per luminància baixa i
radi 3,5→5,5 R☉) que el porten al mateix to amb menys saturació: V1 0,110/0,150/0,190 (0,42) oculta i **V2
0,125/0,155/0,185 (0,32) visible**. Pere: «m'agrada molt… el canvi de to ha ajudat molt a fusionar la imatge».

## 8. Els filtres «profunds» → `FiltresSEMIFINAL7.psb` (19-08, nit)

### 8.1 El defecte que Pere assenyala

«Els nostres filtres treballen sempre sobre l'stack de Vixen, però els que afecten la corona externa han de
fer-se pensant en l'stack de les exposicions de la Sony de llarga durada i les de Vixen de llarga durada», i
«que ja tinguin les correccions de gradient/vinyetatge de les lents a la part exterior. Ara que tenim un
gradient suau no me'l vull carregar amb nous filtres». És cert per al Radials B (fet per Pere al Photoshop sobre
la seva capa Vixen: la seva amplitud rms cau de 0,040 a 1,5 R☉ a 0,003 de 4,5 R☉ enllà) i pels prototips de la
SF3 (calculats sobre la base). El `corona_detall_v2_40` i el `CONTROL_NRGF` ja es feien sobre L_c (els dos
trens), però portaven el cel de la imatge log i la vinyeta del Vixen, i per això a la SF3 se'ls va haver de
tallar el camp («camp net»). El DETALL EXTERIOR (7.2) ja és profund per construcció.

### 8.2 Referència profunda i correcció de flat (`filtres_profunds_v7.py`)

- L_d = L_c v2 (Vixen HDR + apilat Sony v2 ≥ 1/8 s de 3,3 R☉ enfora, pesos 1/σ²; la Sony hi pesa 43–47 % de
  4 a 8 R☉) **+ corr_lf**: la correcció de baixa freqüència (σ 200 px) que `prepara_lluminancia.py` §4 bis
  havia RESTAT a la Sony perquè coincidís amb el Vixen a la costura. La combinada quedava amb el camp del
  Vixen, que **no té flat** (`hdr_corona_vixen.py`: «pols i vinyetatge: no hi ha flats»; `research/80` §9:
  ≤ 3 % als cantons), i la Sony sí que en té un de mesurat (bo a 0,993–1,006 de 4 a 8,8 R☉). Es recupera
  repetint el warp i l'aparellament amb la geometria desada i es comprova contra la L_s desada: error mitjà
  0,0000, màxim 0,004 ADU/s. Mediana +0,44 ADU/s; +2,3 a 7–7,5 R☉; **+6,8 (2 %) a 8,5–9 R☉**, p1/p99
  −4,3/+10,0. No és radial (el camp del Sony és una similitud girada 33°): `v7/corr_lf_x8.jpg`.
- Fons de Fourier per anell (m ≤ 4; m ≤ 2 al NRGF) sobre ln L_d abans de filtrar: pla del cel i vinyeta
  descentrada són m = 0, 1 (i 2). Validesa erosionada 30 px i sense el disc (470 px).

### 8.3 Els tres filtres

Tots en log-polars (8192 × 3072), sobre R = ln L_d − F:

| Filtre | Bandes | Normalització | Porta | Esvaïment radial per banda |
|---|---|---|---|---|
| RADIALS (Espenak multiescala) | només angulars 0,4–2°, 2–6°, 6–18° (σ_r 2 col.), pesos 1/0,6/0,25 | blanquejat per anell (rms robust, pis = soroll/2) | Wiener T 1,8/1,3/1,1 | ≤ 2°: 7,5→9; 6°: 5→7,5; 18°: 4→6,5 R☉ |
| MGN | isòtropes 0,5/0,8/1,3/2,1/3,4/5,5/9°, G 1/1,2/1,3/1,2/0,6/0,3 | local √(v + n² + rms_anell²): local on hi ha estructura, d'anell on és feble | T 2,2…1,05 | 2,1°: 7,5→9; 3,4°: 6→8,5; 5,5°: 5→7,5; 9°: 4,5→7 |
| NRGF | R₂ suavitzat 0,25° | σ robusta de l'anell, pis √n | — | 4,5→7 |

El soroll per banda i radi és **real**: var(b_Vixen − b_Sony)/2 a la zona comuna (inclou sistemàtics), amb el
sintètic × F_SIST com a mínim. Fora de la caixa Vixen (un sol tren) només passen les bandes ≤ 2° a la meitat
(3,4° a un quart; NRGF a la meitat). Mitjana zero per anell a la capa i després dels esvaïments (correcció
c(r) dins del taper), esvaïment a 150 px de les vores de dades i de la costura de la caixa, tanh; capa grisa
0,5 + A·D amb A = 0,125 / 0,125 / 0,20. Màscara radial 2,6→3,6 R☉ (a dins hi ha Vixen sol i els filtres de
Pere). Fracció significativa a 3,5–8 R☉: RADIALS 0,40 (fina) / 1,00 / 1,00; MGN 0,15 / 0,41 / 0,70 / 0,96 /
0,99 / 1,00 per banda.

Tres iteracions abans de tancar: (1) amb les bandes amples fins a 7,5→9 R☉ i l'MGN local pur, el camp llunyà
sortia mollat (taques «de núvol» a 6–9 R☉, de l'escala on viuen les incerteses de flat/cel, i un anell de
textura que s'acabava de cop); (2) esvaïments per banda i mig pes fora de la caixa; (3) esvaïments més
graduals (2,5–3 R☉ d'amplada) i el pis d'anell a l'MGN. Perfil radial de la composició (SF6 + les tres capes
a 40/30/8 %): mediana −0,0009 a 3,5–4 R☉ i zero de 5 enllà; rms 0,008 (4 %) a 3,5–4, 0,0045 a 5, 0,002 a 6,
0,001 a 7, 0,0001 a 8: cap graó. Correlació amb el DETALL EXTERIOR v3 a 3,8–6 R☉: 0,70 / 0,80 / 0,53.

### 8.4 `FiltresSEMIFINAL7.psb` (`construeix_semifinal7.py`)

= SF6 + RADIALS 40 % + MGN 30 % + NRGF 8 % (Overlay, MASCARA_profund) damunt del DETALL EXTERIOR, ANELL
recalculat, cap capa de Pere tocada. TIF a `SEMIFINAL3_capes/` i LLEGEIX-ME §SF7. Les opacitats són el punt
de partida: a 50/40/12 la corona exterior ja es veia pintada a l'escombrada.

## 9. SEMIFINAL8: la corona profunda sencera, el camp net fins al límit, i tots els filtres reconstruïts (19/20-08, nit)

### 9.1 El que Pere va veure a la SF7 i el que hi havia de debò

«CONTROL_NRGF, NRGF profund, corona_detall_v2_40, MGN profund encara plens d'artefactes a les cantonades del camp»; «RADIALS
profund té una banda horitzontal» a la vora superior de la caixa Vixen. Quatre anàlisis en paral·lel (agents A1–A4,
`sf3/v8/`) van posar-hi números:
- **La banda horitzontal** era el taper de la costura de la v7 (`smooth01((dbox−60)/150)`: zero a |d| < 60, ple a 210)
  centrat a la caixa NOMINAL de les capes de Pere (600/7348/550/5103) quan la caixa REAL de `valid_v` és **583..7372 ×
  504..5013** (46 px dalt, 90 baix): una franja de ~120 px de filtre apagat, desplaçada, sobre estructura viva (les
  costures són a 4,9 i 5,3 R☉, on els plomalls polars encara són forts).
- **Les cantonades del compost**: la causa principal era `corona_detall_v2_40 · camp net` (de Pere): el seu camp > 6,5 R☉
  era el perfil azimutal de la capa (0,14–0,33, fosc) → Overlay enfosquia el camp −3,5 % on la màscara val 0,10 i 0 als
  triangles del marc Sony → **triangles TL/BR +3,3/+3,5 punts més clars** (mesurat +2,2 % TL i +4,5 % BR al compost).
  `CONTROL_NRGF` tenia el neutre a 0,61 (offset +0,11: +1 % a tot el camp i cunya als triangles), gra sense porta i arcs.
  MGN/NRGF profunds: taques «de núvol» de 100–160 px a TR/BR (bandes 3,4–5,5° a mig pes a 6–7 R☉ + normalització local
  que iguala el camp feble), franja de dalt granulosa (NRGF sense porta, g_n encara 0,5 a 6 R☉), banda sense textura a les
  quatre costures. RADIALS: gra fi fora de la caixa (banda 0,4–2° a mig pes) i arc de gra a la dreta. El DETALL v3: PASS.
- **La costura, a les dades** (A3): L_d és contínua a la vora per construcció, però hi ha un **sot de −0,10…−0,21 %**
  (0,4–0,7 ADU/s) centrat a ~100 px dins i ~250 px d'ample: la costura σ 200 (convolució normalitzada) **té biaix de vora**
  i no segueix la caiguda del Vixen als últims ~200 px del seu marc (1–2 ADU/s: vinyeta/cobertura); a les bandes DoG de
  ln L_d la costura sortia com a línia de 0,55–1,47 × la rms de la banda 25–60 px. I `corr_lf` **no és una vinyeta**
  (radial al centre Vixen R² 0,17, al Sony 0,26; poly4 0,94): és un camp quadràtic d'eix vertical (84°) alineat amb el
  gradient del cel dels dos trens (−88°): diferència de cel entre èpoques, additiva. El marc Sony: la dada és fiable des
  de ~60 px (l'apilat hi té 0–11,5 s de pes de 25).

### 9.2 Encàrrec 1: l'apilat profund sencer

- **Sony v3** (`apila_sony_v3.py`, A1): els 10 fotogrames > 1/8 s (1/4 ×3, 1 s ×2, 2 s ×3, 8 s ×2 = 24,75 s), pes =
  exposició, registre per ESTRELLES (S01–S09) dels que no tenien astrometria (la correlació de corona de la v2 era
  insensible: una prova sintètica desplaçada 20 px torna −2,5), i **meitats A/B** (12,25/12,5 s) per al soroll real:
  σ_total = σ(A−B)·√(wA·wB)/(wA+wB), validada al 96–99 % contra el passa-alt del total. Exclosos 06990 (8 s, salt 2) i
  **06988** (1 s: traços d'estrelles de ~25 px, inici del salt 2; l'offset «astromètric» de la v2 no era fiable). Pendent
  menor: la 06991 (1 s, 4 %) va 11 px trailada (cua del salt); 06999 +0,8 px en x.
- **Vixen** (A2): l'HDR viu ja és la pila de llargues: de 4 a 8 R☉ el 70–72 % del pes són els 10,3 s, 88 % els ≥ 2 s, 93 %
  els ≥ 1 s; σ per píxel 6–8 % MENOR que els 10,3 s sols (0,46 vs 0,50 ADU/s a 5–6 R☉) i igual (±1,5 %) que 10,3+2+1; BF
  HDR − 10,3 s ≤ ±1 ADU/s (0,1–0,2 % de L, un pla de 0,1 ADU/s per R☉: el cel d'altres èpoques). **No s'ha fet cap pila a
  part.** Apunt: l'HDR va −0,5 px en x i y respecte de la convenció HDR4 (Sol a (3478,5, 2318,5)); el seu mapa de variància
  sobreestima σ ×2,7 (és un pes, no una variància calibrada); una rampa de saturació més estreta recuperaria un 8 % de σ a
  2–3 R☉.

### 9.3 Encàrrec 2: el camp (`prepara_lluminancia_v3.py`)

corr = **poly4 ajustat al nucli (dV > 200) + residu σ 200 calculat sense la franja dV < 150** (sense biaix de vora); la
caiguda del Vixen a la vora (excés Sony − Vixen, detrendat amb una recta a 300–500 px) es mesura per vora i s'afegeix a
L_v (+0,5 ADU/s a 0–50 px a dalt, ≈ 0 a les altres un cop corregit el biaix); el pes del Vixen s'esvaeix en 400 px; la
correcció es desa al npz (`corr_lf`). Comprovació: **L_d − L_s_crua = 0,00 ADU/s** a 0–25, 25–75, 75–125, 125–200 i
200–300 px de les quatre vores (v7: −0,2…−0,6); el desajust entre trens a la vora, de −1,2…−2,0 a ±0,2.

### 9.4 Encàrrec 3: tots els filtres (`filtres_profunds_v8.py`, `neteja_capes_velles_v8.py`, `construeix_semifinal8.py`)

- **Porta de soroll REAL i LOCAL**: n² = (1−f)²·n²_Vixen(sintètic × F) + f²·n²_Sony(meitats, local) amb f = frac_s, i pis
  var(b_v − b_s)/2 per columna a la zona comuna; cap extrapolació «last value»; **cap pes en forma de caixa ni taper de
  costura**; erosió 70 px + esvaïment 200 px a tota vora de dades; 50 estrelles brillants emmascarades (DoG 1,5–4, 7 σ per
  anell, compacitat) i omplertes amb l'entorn abans de filtrar; mitjana zero per anell dins del taper; 0,5 exacte fora.
- **Esvaïments per banda, tots acabats a 8 R☉** (fines 6,5→8; 2–3,4° 6→7,5; 3,4–5,5 5→7; 5,5–9 4,5→6,5; 18° 4→6; MGN
  mig R☉ abans amb pis d'anell ×2 a 7 R☉; NRGF 4,5→6,5): més enllà de 8 R☉ la corona (3 % del cel) no té estructura
  detectable en cap banda i el que passava la porta a les zones només-Sony tenia l'escala dels residus de flat (pols,
  100–200 px, comuns a les dues meitats).
- Les quatre capes de Pere es mantenen visibles i netes: Radials B ×2 (0,5 exacte > 4,5–5,5 R☉), corona_detall_v2_40 (0,5
  exacte > 5,5–6,5 i fora de dades), CONTROL_NRGF (recentrat 0,5 + (s − m0)·w, w → 0 a 6 R☉, 0,5 fora de dades).
- **Test d'acceptació** (`sf3/v8/qa_capes.py`, A4: cantonades rms < 0,002, mitjana per anell < 0,0005, cap línia > 1,5σ
  a les costures, marc Sony): RADIALS, NRGF, DETALL, CONTROL_NRGF v8 PASS; MGN v8 cantonades TR/BR 0,0025/0,0023
  (contingut legítim a 7–7,5 R☉; 0 de 8 enllà) i el detector de línia a la vora baix marca un perfil suau de 400 px
  (sector sud), no cap discontinuïtat (×8 visualment net). L'ANELL recalculat és **0 de 7 R☉ enllà**. SF8 − SF7 per anell:
  |mediana| ≤ 0,002. `FiltresSEMIFINAL8.psb`: 16 capes, 1,50 GB; LLEGEIX-ME §SF8.

### 9.5 Verificació (tres agents en paral·lel: QA numèric, revisió visual adversària, Gemini 3.1 Pro + Grok 4.6)

- Compost: salt al marc Sony TL −2,17 % / BR −4,51 % (SF7) → **0,00 %** (SF8); caixa Vixen: banda de dalt +0,88 % → +0,27
  (desapareguda), baix −1,51 % / graó −0,69 % → +0,33 / −0,04; cantonades (rms 30–120 px) 0,26/0,25/0,35/0,59 % →
  0,15/0,14/0,16/0,18 %; cap costura > 1,2 σ; els residus als llocs dels artefactes són byte a byte els de Base+FLAT+HALO.
  L_d − L_s_crua: −0,35…−0,73 ADU/s → ≤ 0,09.
- Visió externa: Gemini i Grok trien SF8 i donen els artefactes de la SF7 (2–3/3) per resolts (0) a la SF8; la
  discrepància de Gemini («pintada», halo a 3,5–4) no la comparteix Grok i la desmenteix la mesura (menys alta freqüència
  a 4–7 R☉ que la SF7, perfil radial igual a < 0,001). Cost 0,09 USD.
- Un pas en fals detectat pel perfil radial i corregit abans de tancar: el taper de validesa de les capes velles netes
  (60 px de la validesa de lum_llenc, que no inclou el disc lunar) neutralitzava el corona_detall_v2_40 al limbe (−1,4 %
  a 1,05 R☉) → el taper només actua a r > 3 R☉; i el CONTROL_NRGF recentrat es deixa idèntic dins d'1,15 R☉. **Limbe i
  protuberàncies: byte a byte els de la SF7.** Canvis de nivell que queden: −0,7…−1,0 % a 1,2–3,25 R☉ (offset espuri del
  CONTROL_NRGF tret) i +0,8 % a 4,75–5,25 (ANELL). El que queda és de la base de Pere (ratlles a 33°, bandes paral·leles
  al marc Sony, costura polar 1,5 %, graó +0,4 % a y=5103 vora nominal, línies d'1–2 px a l'última fila/columna).

### 9.6 SEMIFINAL9: cap tall radial; la porta és la coherència entre grups de muntura (20-08)

Pere: «cada píxel del fotograma importa, no et limitis a un filtre radial». La SF8 apagava radialment (tot a 8 R☉) per no
deixar entrar als cantons els residus de flat; la SF9 substitueix el criteri geogràfic per un de físic: **les meitats de
la Sony per GRUP de muntura** (A = 06982/84/85/87, 11,25 s; C = 06991/93/94/96/97/99, 13,5 s; `apila_sony_v3.py` amb
`MEITATS_PER_GRUP=1`, `sony3g/`) van desplaçades (−233, +713) px, o sigui que el que és fix al sensor es mou i el que és
del cel no; la correlació local per banda entre les dues (finestra 2·σ, pes c^1,5) és la porta, a tot el camp on hi ha
Sony. Control nul (C girada 180°): ⟨c⟩ real 0,32–0,94 vs nul 0,02–0,14 (fora de la caixa 0,22–0,93 vs 0,01–0,13). Res
radial: ni esvaïments per banda, ni sortida del DETALL, ni del NRGF (fons m ≤ 2 ajustat mentre l'anell tingui ≥ 10 % de
cobertura, fins a 9,7 R☉: l'extrapolació de `fons_fourier` feia un cercle a c_ple); erosió 60 + taper 120 px. Resultat:
estructura fins a les vores (rms de capa a 8,5–9,5 R☉: 0,004/0,009/0,049), modulació del compost 1,1–1,8 % al camp
llunyà, dominada pel NRGF (sectors de cel: coherent entre grups, real al cel, però cel d'ombra més que corona); costures
sense línia; marc Sony sense excés. Límits: l'anivellament per fotograma (pla + σ 300) fa compartir la baixa freqüència
de la 06993 als dos grups → la coherència no discrimina a > 300 px. `FiltresSEMIFINAL9.psb` (16 capes, 1,63 GB).
Pere hi va marcar dos cercles: eren fronteres d'algorisme — c_ple (5,86 R☉, on `fons_fourier` passava d'ajustar a extrapolar:
ara `frac_min_fit=0.10` a tots els residus), el final de la zona comuna (~9 R☉, el pis per columna queia a zero: ara en 80
columnes) i l'entrada de la Sony a 3,3 R☉ (Wiener → coherència d'un píxel a l'altre: ara rampa 3,3→4,0 i la màscara del
DETALL des de 3,3). Al compost en polars no queda cap línia vertical de 2 a 10 R☉. `FiltresSEMIFINAL9.psb` refet (1,63 GB).

## 10. SEMIFINAL10: la revisió de màscares de CapesInteriorsV4, aplicada als filtres (20-08, matinada)

Encàrrec de Pere: fer amb les capes exteriors el mateix que `research/84` va fer amb l'HDR interior —
repassar cada capa d'imatge amb la seva màscara, buscar els artefactes que la màscara mal aplicada
imprimeix al compost, i arreglar-ho sense crear halos. Mètode: per a cada capa de la SF9 es mesura
l'**empremta no radial de la màscara** = compost − (el mateix compost amb la màscara promitjada per
anell). Tot el que hi surt és estructura que la màscara inventa o esborra, no la capa.

Troballes, per ordre de gravetat (tot verificat sobre `FiltresSEMIFINAL9.psb`):

| # | Capa | Defecte | Empremta al compost |
|---|---|---|---|
| 1 | DETALL EXTERIOR v9 | **màscara tota 0** (error d'unitats a `win_det`: `rR` és en R☉ i s'hi restava `3,3·R_SOL` px) | la capa no feia RES a SF8/SF9 |
| 2 | CONTROL_NRGF_gris | màscara = la capa mateixa (R² 0,99; sectors de 45°); i dins d'1,15 R☉ el biaix +0,126 no estava recentrat | 0,7–1,0 % rms, 2–3 % p99 (1–4,5 R☉); +1 % de llum espúria a 1,0–1,4 R☉ |
| 3 | corona_detall_v2_40 | màscara ≈ còpia de la capa (R² 0,87): autoemmascarament; i deixava entrar la transició del seu disc lunar (−0,4→+0,19 a r_ll 453–466) | 0,3–0,6 % rms; vora fosca al limbe; enfosquia l'earthshine dins la Lluna |
| 4 | Radials B ×2 | màscara de lluminositat amb discos superposats de vora dura (grad 0,44) i streamers (68 % no radial) | 0,5 % rms, 2 % p99 (1–2 R☉) |
| 5 | CEL blau-gris ×2 | màscara per lluminositat: retallava els streamers reals de 3,6 a 5,5 R☉ | 0,26 % rms (4–4,5 R☉) |

La correcció és la de CapesInteriorsV4: **màscares només radials** (mitjana per anell de la de Pere, o
sigui el mateix efecte mitjà exactament), amb el tall interior centrat a la **Lluna** on la capa té la
resposta de vora del disc (r_ll 470/466 px), el CONTROL_NRGF **recentrat per anell a tot arreu** (fora
d'1,4 R☉ byte-idèntic al v8) amb màscara constant 0,5, i la màscara del DETALL v9 la que tocava
(3,3→4,3 R☉ × validesa). **Guarda de la protuberància**: el·lipse suau (3578, 2653; 90×110 px, rampa
50) on màscara i contingut es queden EXACTES de la SF9 — els 2.792 píxels rosats donen 0,000 % de canvi.

Verificació del merged: test d'anells igual o millor que la SF9 a tots els radis; perfil radial −1 % a
1,0–1,4 R☉ (el biaix del punt 2, fora) i ±0,3 % la resta; cap línia nova a les costures (≤ 4·10⁻⁴);
cantons ±0,2 %; cap cercle ni anell en polars; l'estructura a escala de streamer es redistribueix
±1–2 % rms — el contrast que les màscares autocorrelades aplanaven (mateixa física que el 0,34–0,82 de
CapesInteriorsV3). Lliurat: `FiltresSEMIFINAL10.psb` (16 capes, 1,51 GB), TIF de les cinc màscares
noves + CONTROL recentrat + ANELL SF10, previsualitzacions `SEMIFINAL9_vs_10_*` i el mapa
`SEMIFINAL9_empremtes_mascares.jpg`. Codi: `construeix_semifinal10.py`.

Regla que en surt (la mateixa de `research/84`, ara demostrada també aquí): **una màscara correlada amb
el contingut de la capa —o amb la base— imprimeix i aplana alhora**; l'única màscara que no interfereix
és la radial (o una de constant), i el tall interior s'ha de centrar a la Lluna, no al Sol, quan el que
es talla és la resposta de vora del disc lunar de la capa.
