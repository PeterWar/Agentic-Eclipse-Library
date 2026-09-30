# Lectura (agent 3): Druckmüller 2006, tesi curta 2014, Martišek 2012, Druckmüller 2009

## 2006 (CAOSP 36)
- Alineació: la pols del sensor sol donar el màxim global de la correlació; PhaseCorr 3.0 ±1 px, ±0,05°.
- Composició: pesos a mà (subjectius); «have to be calibrated» sense dir com; corona externa amb poc contrast a la suma simple perquè poques imatges hi porten res.
- 8 bits: ull 150–250 nivells; ull = analitzador diferencial amb veïnat adaptatiu → filosofia.
- Radial blur: cec a les tangencials; test de colors blau/taronja (gris = igual).
- Nucli variable: 4 condicions; «amplification limited by the amount of noise»; llindar de diferència màxima de píxel «experimental»; Corona 3.0: 38 paràmetres, 8 barres de freqüència (Fig. 9: guany 1 a λ>0,4 R☉, ~2 a 50 px, ~5 a 10 px, ~10 a 5 px, ~20 a 2 px; R☉ ≈ 400 px); **γ < 1 = corona externa amb més contrast, «this setting is usual»**; Red weight >100 % rebaixa protuberàncies.
- Cap σ, cap mida de nucli. 2002: interior i exterior processats per separat i cosits (dos instruments).

## Tesi curta 2014
- ACHF «multiple two-dimensional direction-invariant kernels with different sizes».
- FNRGF: n_s ≥ 2ω+1 i n_s ≈ 2π r_o/10; A_k baixa el contrast local, C_k el puja (soroll inclòs); A_k més lenta que C_k; mediana d'una passada abans (estrelles/impulsiu); NRGF = n_s=1, ω=1, A0=C0=1, A1=C1=0.
- «FNRGF per a gran escala, ACHF per al detall fi, i composar»; FNRGF llum blanca n_s=150, A=(1;0,99;0,98…), C=(1;0,98;0,96…), radi ~900 px, segons.
- Fig. 3.3: √V_n = 0 / 7,5 / 15 % del soroll a 2,618–2,68 R☉, mescla 7:1.

## Martišek 2012
- AHE amb veïnat quadrat (2r+1)², veïnats adaptatius V(α), A(k), S(α,k,qV,qA), difús μ = 1 − (1−μ_r)/r · C_L; mescla amb l'original (sense valors).
- Adaptivitat al soroll additiu §6.5: c = k a + l b, l→0 quan σ_0 (veïnat) → σ (soroll), l→1 quan σ_0 ≫ σ (funció no publicada). Impulsiu abans que additiu; criteri de rang |r(x) − n/2| > ε.
- Corona (§11.2): veïnat local no adaptatiu r=4; res més.
- Cap filtre freqüencial adaptatiu.

## 2009 (H_ϱ)
- H_ϱ(a) = a − ∫_{−2ϱ}^{2ϱ} a(r, φ+ω) e^{−ω²/2ϱ²} dω: errata (r+cos), sense normalització (∫ = 2,39ϱ), unitats de ϱ no definides (8–16); la tesi llarga usa arc en px constant amb r.
- S'elimina el radial perquè porta la fotometria no fiable (saturació, llum difusa canviant); no perquè el tangencial vegi millor. Cap paper no el proposa com a realçat; Fig. 1 = ratlles radials «Espenak».

## 10 idees implementables (agent)
1. Nucli = gaussiana radial × gaussiana tangencial (arc en px), convolució incompleta normalitzada per w. 2. Banc de σ (16, 32, 64, 128 px per a 2–6 R☉) amb pesos = «barres». 3. w resol Lluna, vora, costura Sony/Vixen. 4. Porta de soroll: V_n (FNRGF) o mescla k a + l b (Martišek) → màscara de capa amb σ_0/σ. 5. FNRGF gran escala + convolució detall fi; FNRGF com a control. 6. Estrelles: màscara (catàleg), no mediana. 7. Test de colors 2006 com a QA. 8. Capa tangencial només estètica (fase, direccional). 9. Capa Linear Light zero-mean sobre gris 50 %; γ<1 = màscara radial de guany. 10. Interior/exterior per separat i cosits (2002).
