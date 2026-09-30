# Lectura (agent 4): la resta de papers (Habbal/Boe/Bailey/PSF/cel/Bemporad) — punts útils

- Bailey 2025: correlació tangencial L⊥ 1,5 Mm (2″) a la cromosfera → ~0,135 R☉; sobre imatge ACHF; no arriben a 2–6 R☉; sense espectre de potència.
- Boe, Habbal, Druckmüller 2020 (RHT): 14 eclipsis ACHF; passa-alt gaussià σ 0,002–0,05 R☉ + blur + binari + Hough rotacional (finestra 0,08–1 R☉); camp ample descartat < 2 R☉; no radial fins a 3, radial cap a 4 R☉; CME a 6 R☉.
- Pasachoff 2009 (2008): 255 imatges 1/4000–8 s; ~2000 calibratges; alineació només sobre corona; tres dominis radials processats per separat; helmet streamers fins a 20 R☉ (200/500 mm, 55 imatges fins a 8 s); cel blau «removed».
- Pasachoff 2014 (2012): 58 fotogrames RED; filtre radialment graduat per alinear; pesos ∝ t_exp; «locally adaptive filters».
- Habbal 2023 white paper: middle corona 1,5–6 R☉; 1″ < 1,5 R☉ i 5″ fins a 10 R☉.
- Boe 2025 (Austràlia 2023, Sol a 54°): 200 mm ×199 imatges compost fins a ~10 R☉; **cel: resten el valor a la cantonada (7,5 R☉) i n'afegeixen part fins a coincidir amb LASCO C2 a 6 R☉ → a 7,5 R☉ el cel era el 80 % del senyal**; continu ≈ constant a alçada fixa tret dels stalks de streamer ≥ 6 R☉; ghosts 0,1–1 % restats per auto-sostracció; CMOS no lineal fins a 30 %.
- Bemporad 2020: DSLR 300 mm f/5,6 sense seguiment; per píxel, mitjana de les exposicions dins l'interval de linealitat; vinyetatge < 25 %; resolució 10,2″; NRGF + «EDGE DOG» → plumes fins a 3 R☉, streamers fins a 5 R☉; cap sostracció de cel; ×2 vs MLSO.
- Hofmeister 2024 BID: I_t ← I_t − (I_t∗PSF − I_o); +23 % soroll; compta llum fora del camp; sense fórmula d'ales.
- Talvala 2007: sòl de glare 20 stops sota una font puntual, però una font extensa deixa 9 stops útils; GSF no invariant; deconvolució amplifica quantització.
- Liu 2022 (Dragonfly, Canon 400/2,8!): ales f_p ≈ 0,3, r^−3,6 (<54″), r^−2,9 (54–126″), r^−1,9 (>126″); pols i aerosols les eixamplen.
- Hanaoka 2021/2024: **cel a 4 R☉ = 8–35×10⁻¹⁰ B☉ (Sol a 40°/13°), ≈ K+F a 4 R☉**; polarització vertical uniforme; cel restat com a constant.
- Snik 2020: polarització del cel vertical, uniforme (rms 3°); punts neutres.
- Emde & Mayer 2007: cel de totalitat = dispersió de 2n ordre a l'estratosfera fora de l'ombra, més vermell, poc sensible als aerosols; sense forma angular a pocs graus.
- Boe 2021 F: F ∝ λ^0,91; cel = valor al centre de la Lluna (earthshine 2,5×10⁻¹⁰ B☉).
- Kalenská ApJS 2024: sèries temporals (PCP/DMD), no una imatge.
- Palmerio 2021: MGN/WPE «no revelen el que no hi ha»; diferències artefactes al limbe.

## Conclusions per a 2–6 R☉
1. Estructura real vista fins a ≥ 6 R☉ (stalks, CME) i 10–20 R☉ amb molta integració; ningú dona S/N(r).
2. Fons: tots resten el cel com a constant (Lluna, cantonada, polarització); ningú modela gradient; F no es resta en llum blanca de banda ampla; halo: només ghosts.
3. Escales reals: raigs de desenes de ″ i estructures 0,1–1 R☉; sota ~10″ no documentat a 2–6 R☉; entre 3 i 7 R☉ Habbal 2026 no té mides.
4. Trampes: mesurar sobre imatges ja filtrades; no linealitat CMOS; ghosts lluny del Sol; cel al 80 % a 7,5 R☉ a 54° (nosaltres 9°: la frontera cel≈corona baixa a ~3 R☉); fons «cecs» suaus poden menjar-se streamers.
