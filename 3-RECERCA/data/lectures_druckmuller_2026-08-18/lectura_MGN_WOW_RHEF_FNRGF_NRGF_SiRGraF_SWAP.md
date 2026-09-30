# Lectura (agent 1): MGN, WOW, RHEF, FNRGF, NRGF, SiRGraF, SWAP, Druckmüller 2014, NAFE (Kalenská)

(Resum de treball; el text sencer de l'agent és a la conversa. Punts que decideixen el disseny.)

## MGN (Morgan & Druckmüller 2014)
- C = (B − B⊗k_w)/σ_w; σ_w = sqrt([(B−B⊗k_w)²]⊗k_w); C' = arctan(kC); C'_g = ((B−a0)/(a1−a0))^(1/γ); I = h·C'_g + (1−h)/n Σ g_i C'_i.
- w = {1,25; 2,5; 5; 10; 20; 40} px; k = 0,7; γ = 3,2 (2,5–4); h = 0,7; g_i ≈ (0,60; 0,91; 0,98; 0,99; 1; 1) (raó σ_w/σ sobre soroll blanc). LASCO C2: k=0,8, h=0,9, γ=1, fons de llarga durada restat abans.
- **Cap porta de soroll**: el paper mateix ho diu (NAFE millor «at large heights off the limb»); Auchère: MGN «enhances the high-frequency noise», franges fosques d'unsharp.
- Convolució separable; vores no descrites.

## WOW (Auchère et al. 2023)
- À trous, B3 spline h=[1,4,6,4,1]/16, forats 2^s, vores mirall, S = log2 N escales.
- Blanqueig: w̄_s = w_s / sqrt(P̄_s), P̄_s = w_s² * h_s (mateix nucli de l'escala). Sortida c̄_0 = c̄_S + Σ w̄_s (com es blanqueja c_S: no hi és; a la figura surt pla).
- Desbrollament: |w_s| > n_s σ_s, σ_s = σ·σ_s^1 (σ_s^1 mesurat numèricament sobre soroll N(0,1)); atenuació suau α = erf(|w_s|/(n_s σ_s)); σ(k) espacial = sqrt(g·I + r²) (LASCO C2: g=0,07 DN/ph, r=0,3 DN). **n_s = {5,3,1,0,…}** igual per a HRI, AIA i LASCO C2.
- Edge-aware: bilateral amb b = exp(−½((c_s(k)−c_s(k+2^s l))/ν_s)²), ν_s² = h_s*c_s² − (h_s*c_s)²: cap paràmetre lliure afegit; ~4–5× més lent.
- Sortida sense gamma; visualització percentils 0,1–99,9. Es pot barrejar amb l'original γ-estirat (eq. 19, w=0,7, γ=2,4 per MGN) o arcsinh(x/β).
- Artefactes coherents (bandes, anells de difracció) s'accentuen: emmascarar/calibrar abans.
- Cost: 0,5 s (1k²), 14 s (4k²); bilateral 2,3 / 53 s. Codi: github.com/frederic-auchere/wavelets.

## RHEF (Gilly & Cranmer 2025)
- I_out[A_i] = rank(I_in[A_i])/N_A_i, anells ~1 px; mediana de l'anell → 0,5.
- Υ(I; Υ_L, Υ_H) = ½·(2I)^Υ_L si I ≤ 0,5; ½·(2 − (2(1−I))^Υ_H) si I > 0,5. Υ = 0,35 (LASCO C3); Υ_L ∈ [0,5,1], Υ_H ∈ [0,3,0,5]. K-Cor sense Υ.
- Soroll: §5.2 admet que off-limb a baix S/N «noise can become exaggerated»; recomana noise-gating (DeForest 2017) abans; restar fons constant abans. Centre: r < 0,6 R☉ com un sol anell.
- Cost N³: 1k² 1,1 s, 4k² ~60 s. «Unsuitable for photometric applications».
- Híbrid: RHEF sobre sortida MSGN.

## FNRGF (Druckmüllerová, Morgan & Habbal 2011)
- n = 50 segments fix a tots els radis; anells d'1 px; ordre 10.
- Atenuacions «prop de l'òptim»: A = (1; 0,85; 0,7; 0,55; 0,4; 0,25; 0,1; 0…), S = (1; 0,9; 0,8; 0,7; 0,6; 0,5; 0,4; 0…). Una dècima més i s'espatlla.
- Soroll: variància d'una regió sense estructura (50×50 px a gran alçada); FNRGF-N resta m√DN (m=0,5) — **la tesi 2013 ho repudia: sumar V_n dins dels c,d**.
- Mescla Z = K1 X + K2 Y; exemple K1=1, K2=15 000 amb X ∈ [0, 514 040].
- «NRGF i FNRGF realcen les estructures febles a més alçada que l'ACHF»; per baix S/N el FNRGF és més viable que l'ACHF; l'ACHF guanya en detall fi. Combinació 0,4 FNRGF + 0,6 altes freqüències ACHF (Fig. 9d: ~0 fins a 0,01 c/px, pujada des de 0,05, ~300× a 1 c/px, R☉ = 275 px).

## NRGF (Morgan, Habbal & Woo 2006)
- I' = (I − ⟨I⟩_φ(r))/σ_φ(r). Res del soroll a radis grans. Fons a restar (C2): mitjana llarga de la component no polaritzada. Validació: perfil latitudinal de tB filtrada vs pB. C2 retallat a 2,3–6 R☉.

## SiRGraF (Patel 2022): necessita sèrie temporal (fons mínim). No serveix per a una imatge sola.

## SWAP (Seaton 2023)
- F: en polars, mediana azimutal ±15° (no toca la radial), tancament 0/360, gaussiana σ 4 px. F' = (F + t0)^c0, t0 ≈ mediana del filtre (1,5), c0 = 0,75. I' = [(I0/F')^(1/4)] retallat a [0,5, 2].
- Amplifica el soroll de les parts fosques si t0 baix; sense escales ni desbrollament.

## Druckmüller, Habbal & Morgan 2014 (ApJ 785)
- ≥10 exposicions, alineació 2009, **ACHF** (paràmetres NO declarats), resolució 2–3″, 20–50 s efectius; «altes freqüències ×300; estructures 10³ més febles que el contrast global». Validació: ubiqüitat a 4 eclipsis, pel·lícula i digital, contrapartides LASCO C2/Hinode. Escales: bucles 30–40″, anells 20–30″, hèlixs 0,5–1 R☉, bombolles diversos R☉.

## NAFE (Kalenská 2024)
- f_B = (1−w) φ_γ(f_A) + w E_{N,σ}(f_A); E: equalització d'histograma difús local (pesos gaussians b_kl), l'histograma acumulat convolucionat amb G_σ (= afegir soroll σ sense generar-lo; només actua on el veïnat és soroll), Δ^ε per no barrejar brillantors molt diferents. Producció AIA: γ=2,6, w=0,2, σ=15 (8 bits); Auchère: N=129, σ=12, w=0,2.

## Conclusions per a la corona externa
1. Només WOW i NAFE porten porta de soroll de debò; MGN i RHEF no (i ho admeten); NRGF no en parla; SWAP només t0.
2. El desbrollament WOW vol el mapa σ(k) — nosaltres el tenim (mapa de variància del compost).
3. n_s = {5,3,1} és universal al paper (EUV i C2), no calibrat per a llum blanca a S/N baix.
4. Per a alçades grans, la pròpia Brno diu FNRGF/NRGF > ACHF.
