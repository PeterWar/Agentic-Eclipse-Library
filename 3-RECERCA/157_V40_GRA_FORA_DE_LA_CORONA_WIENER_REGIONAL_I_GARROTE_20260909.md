# 157 — V40: el gra fora de la corona, ara sí: guany per banda = màxim de Wiener regional i garrote, soroll mesurat a TOTES les vores, cap terme creuat (09-09-2026, tarda)

Ordre de Pere sobre la V39 (`V39_Artefactes.psb`): «no hem millorat el soroll en res, crec que estem encallats; a més hem introduït artefactes al borde del FOV del Vixen en alguns filtres que no hi eren abans. Com ho desencallem?… se m'acut fer passar tots els filtres per una IA de reducció de soroll, però no em sembla òptim.» I: «quan toqui fer la V40 només posa les capes que han quedat a V39_Artefactes i les primeres capes no-linealitzades (de la 06 a la 12)». Contrast previ amb Codex (GPT xhigh, tema `v40-desencallar-soroll`), per ordre seva: §6.

Mètode, estimador de soroll i història: `research/156` (V39). Codi: `research/tools/v39_20260909/` (operadors, estimador, portes) i `research/tools/v40_20260909/` (muntador, rebut, traspàs). Rebuts: `output/v39_20260909/4-rebuts/` (pilot) i `output/v40_20260909/4-rebuts/`.

## 1. Les marques de Pere (G1)

`V39_Artefactes.psb`: 15 capes (les que conserva), totes en Normal 100 % per inspecció, marques pintades a sobre. Detecció per saturació (`g1_marques_v39.py`): al **P04 i al P05, el rectangle SENCER del camp de la Vixen** resseguit en blau (component amb el centroide al centre del Sol); a 03 r0, P01, P01b, P02, P03, P04 i P05, dues o tres marques blaves al **limbe oest** (1,03–1,07 R☉, azimuts 134–164° i −155…−173°: la franja i el limbe, residu conegut, no nou).

## 2. Per què la V39 no es veia millor (mesurat)

- **Un llindar tou k = 2 deixa passar el 58 % de l'amplitud del soroll pur.** Sintètic: residu 0,58 (llindar tou k = 2), 0,33 (k = 4), 0,18 (garrote k = 2), 0,036 (garrote k = 3), 0,05 (Wiener regional amb N/E = 0,95). Real: el P03 a 5,5 R☉ passa de rms 0,246 a 0,150 (= 0,61), amb el residu a les bandes ≤ 1 / 1–2 / 2–4 / 4–8 px de 0,069 / 0,052 / 0,040 / 0,023. L'ull no veu una baixada del 40 % de l'amplitud del gra: veu si el gra hi és o no. El k = 2 s'havia triat per aprovar la porta d'injecció (que un blob feble i aïllat sobrevisqui ≥ 0,75): per coeficient, «conservar el feble aïllat» i «treure el gra» són el mateix problema.
- **El terme creuat dibuixava el rectangle de la Vixen.** g_creuat només existia al suport comú dels dos trens i queia a zero fora: dins del camp les bandes grans es confirmaven (g 0,6–1,0), fora només hi havia la Sony (0,56–0,76). Capa 01: rms 0,017 fora del camp → 0,037 dins (×2,2; V38 ×1,5). Resolució segons cobertura, no segons S/N: la norma que no s'havia de trencar.
- **L'estimador de soroll per meitats era invàlid també a la vora EXTERIOR del camp de la Vixen** (i a les vores de la Sony): ln(E/O) ×13 a 0–2 px, ×3,4 fins a 10 px, 1,1 a 10–20; el soroll mesurat hi sortia ×8–22 fins a 16 px, ×5–8 fins a 32 i ×2 fins a 128 px a les bandes grans. A la V39 només s'havia exclòs el forat lunar.

## 3. La cura (acordada amb Codex)

- **Guany per banda g = max(g_W, g_G)**: g_W = clip(1 − N/E, 0, 1) (Wiener REGIONAL: N el soroll mesurat de la banda, E l'energia regional del coeficient amb σ_E = max(3 ℓ, 8 px); on la banda és 95 % soroll val 0,05, on és senyal val 1); g_G = max(0, 1 − (kσ)²/w²) amb k = 3 (garrote: protegeix el compacte fort: 5 σ 0,64, 7 σ 0,82, 10 σ 0,91). Prova sintètica (`filtres_v39.guany`, mode `wg`): residu de soroll pur 0,058 (contra 0,592 del llindar tou k = 2), blob de 5 σ 0,61 i de 8 σ 0,89, i en una regió amb senyal (E/N = 10) guany mitjà 0,86 amb la correlació amb l'estructura intacta (0,953 contra 0,949). τ = 0 reprodueix la V38.
- **Cap terme creuat com a guany** (només validació amb Brno). Sense ploma amb el pes de la Vixen: amagaria la línia però mantindria la resposta lligada al camp de l'instrument.
- **Estimador de soroll amb totes les vores excloses, per escala**: `comu39.dist_vora_suport` (distància a qualsevol vora del suport comú de les dues meitats); D = ln(E/O) només on d ≥ 16 px; l'energia de cada banda només on d ≥ max(16, ℓ). Dues particions independents de fotogrames (parell/senar i parelles alternades pA/pB, `b2_meitats`); N = mitjana de les dues, dispersió anotada (`Soroll.dispersio`).
- **Portes noves** (Codex): gra (rms de la candidata / rms de la V38 per banda a finestres on la banda és soroll: objectiu ≤ 0,08 per banda fina, ≤ 0,12 agregat), vores (salt dins/fora del camp de la Vixen no pitjor que la V38; perfil per bins de distància signada), Brno (transferència agregada 0,90–1,10 on Brno jutja; ≥ 0,90 dins de 3 R☉), i la injecció A3b passa a ser corba de preu declarada, no porta universal. `c3d_vores_i_etapes.py`, `c3c_jutge_brno.py`, `c3_portes.py`.
- **Pilot abans del PSB** (Codex): regenerar P03/P04/P05 i les ACHF amb la regla nova, passar les portes i mirar-ho a 1:1 a la vora de la Vixen; si queda cap rectangle, no fer la V40.

**Pilot 2 (17:37): el creuat com a MODEL DE SOROLL, i quin soroll fa de referència.** `creuat_v39.Creuat.soroll_total`: al solapament, N_V = max(E_V − C, N_V,meitats) i N_S = max(E_S − C, N_S,meitats) amb C = ⟨b_V·b_S⟩ (finestra σ_c = max(6ℓ, 24 px), suport comú eroditat 3ℓ); fora del solapament, el soroll de meitats de cada tren multiplicat pel quocient medià (N_total/N_meitats) del seu anell al solapament (continu en r). Mesurat (canal G): N_total/N_meitats de la Vixen és 1,0 a ≤ 2 px, 1,2 a 4, 1,9 a 8, 5,0 a 16 i 6,9 a 32 px (els patrons fixos i tot el que la Sony no confirma són la MAJOR part de l'energia de la Vixen a les bandes grans); el de la Sony és 1,00–1,03 a totes (les meitats V29 ja hi eren bones). Tres referències provades per al guany, amb el perfil per franges de distància a la vora de la Vixen (bandes 16 i 32 px, guany fora / franja 100–600 / dins 900–1300):
- **fusió** (w_V²N_V + w_S²N_S, el soroll real de la fusió): 0,07 / 0,04 / 0,28 i 0,14 / 0,19 / 0,63. És el guany òptim en S/N i, per això mateix, dibuixa el camp: on hi ha dos telescopis la fusió té menys soroll i el filtre ho ensenya. **Refusat**: la norma és que cap filtre dibuixi el contorn d'un tren.
- **pitjor tren present** (max(N_V, N_S)): 0,07 / 0,00 / 0,07 i 0,12 / 0,05 / 0,40: un CLOT a la franja d'entrada de la Vixen (100–600 px), on pesa un 3–30 % però hi és molt sorollosa (pocs fotogrames a la vora) i el màxim l'agafa. **Refusat.**
- **la Sony allà on la Sony hi és** (i la Vixen només a l'interior on la Sony no arriba): 0,07 / 0,01–0,03 / 0,13–0,16 i **0,13 / 0,13 / 0,39–0,53**: la banda de 32 px és plana des de 600 px fora fins a 300 px dins de la vora; dins puja suaument amb el pes de la Vixen (ploma de 720 px de la fusió), on la Vixen aporta energia. **Adoptat** (`soroll_ref: sony`). El coeficient fusionat conserva l'avantatge de S/N del segon tren; només el guany deixa de créixer al contorn.

**Veredicte del pilot 1 (17:00):** gra PASSA (×0,12–0,26 a 5,5 R☉; P04 ×0,45), Brno PASSA (≥ 0,92 dins de 3 R☉; 0,91–1,00 a 3–5 on jutja; correlacions amunt: P03 0,52→0,63 a dins, P05 0,22→0,31 a 3–5), **vores FALLA** (salt dins/fora a la vora de la Vixen ×4–6 a les ACHF, ×1,6 al P03/P05; V38 ×0,9–1,4). Mecanisme (perfil per franges, canal G): fora del camp el soroll de la Sony (meitats de la V29) supera l'energia de la banda un 15–20 % (N/E 1,1–1,2 → g 0,02–0,05, tot buit); dins, a les bandes de 8–32 px el soroll de la Vixen és 2–3× menor que el de la Sony, N/E cau a 0,2–0,7 i el guany puja a 0,3–0,75, però l'energia TOTAL de la banda és la mateixa a banda i banda de la vora: el que l'estimador pren per senyal dins és el que les meitats no veuen com a soroll (patrons fixos de la Vixen). A més, la finestra de 3 ℓ fa el guany a pedaços (grumolls, retalls `C3d_vora_vixen_*`). No es munta. **Pilot 2:** soroll = potència total − potència creuada entre sensors (estimador del 31-08), calibrat per anell fora del solapament; finestra 6 ℓ i suavitzat del quocient; el creuat com a MODEL DE SOROLL, mai com a guany.

**Veredicte del pilot 2 (20:41; llenç sencer, canal G a R/G/B per a l'ACHF):** gra: residu a 5,5 R☉ ×0,02 (01, 04), ×0,06 (P03), ×0,09 (06), ×0,17 (P05), ×0,32 (P04); a 3,7 R☉ ×0,08–0,40 (V39: ×0,53–0,67). Brno: transferència agregada a 1,2–3 R☉ 0,97 / 0,89 / 0,99 / 1,00 / 0,94 / 0,90 / 0,93 (01/04/05/06/P03/P04/P05); a 3–5, on Brno jutja, 0,89 (01) / 0,97 (05) / 0,99 (06) / 0,95 (P04); correlació amb Brno amunt a totes les capes, sobretot a 3–5 R☉ (P03 +0,07→+0,30, P04 +0,34→+0,45, P05 +0,22→+0,29, 04 +0,10→+0,18, 01 +0,24→+0,29); nuls |r| ≤ 0,10. Vores: cap contorn a escala igual als PNG del llenç sencer a mida ½ (`output/v40_20260909/lliurables/llenc/`); perfil de la capa 01 per franges de distància a la vora de la Vixen: fora 0,016, vora prima 0,025 als primers 30 px, SOLC de 0,002–0,006 entre 30 i 600 px dins (la Sony perd pes a la ploma i la Vixen encara no hi posa energia: el coeficient fusionat baixa i la referència no), i 0,027 de 600 px endins (V38: 0,040 fora → 0,046 dins). El que queda dins és, per Brno, estructura confirmada (correlació amunt), no soroll. Es munta com a **V40 candidata** amb aquests límits declarats; millora pendent (V41): referència de soroll que segueixi el pes de la Sony a la franja de la ploma (elimina el solc) i fusió multiescala per soroll total mesurat (redueix l'energia no compartida de la Vixen a la seva vora). ⚠️ Els retalls de `C3d_vora_vixen_*` estan estirats per percentils de cada tessel·la (escales diferents): només serveixen per veure formes, no per comparar amplituds; per comparar, els PNG del llenç sencer.

## 4. Resultats del pilot (candidata V40 contra V38 i V39)

**Soroll per anell** (rms de capa − 0,5; 1,1–1,5 / 1,5–2 / 2–2,65 / 2,65–3,5 / 3,5–5 / 5–7 R☉), V38 → V40:

| capa | V38 | V40 |
|---|---|---|
| 01 | 0.145 / 0.107 / 0.122 / 0.077 / 0.041 / 0.030 | 0.141 / 0.102 / 0.110 / 0.055 / 0.019 / 0.003 |
| 04 | 0.103 / 0.069 / 0.084 / 0.067 / 0.045 / 0.036 | 0.097 / 0.060 / 0.059 / 0.025 / 0.008 / 0.002 |
| 05 | 0.186 / 0.151 / 0.161 / 0.099 / 0.047 / 0.032 | 0.184 / 0.148 / 0.154 / 0.081 / 0.029 / 0.005 |
| 06 | 0.205 / 0.179 / 0.178 / 0.110 / 0.051 / 0.033 | 0.203 / 0.176 / 0.173 / 0.093 / 0.034 / 0.006 |
| P01 | 0.194 / 0.192 / 0.189 / 0.192 / 0.194 / 0.194 | 0.194 / 0.192 / 0.189 / 0.192 / 0.194 / 0.194 |
| P01b | 0.237 / 0.235 / 0.232 / 0.235 / 0.237 / 0.237 | 0.237 / 0.235 / 0.232 / 0.235 / 0.237 / 0.237 |
| P02 | 0.289 / 0.289 / 0.289 / 0.289 / 0.289 / 0.289 | 0.289 / 0.289 / 0.289 / 0.289 / 0.289 / 0.289 |
| P03 | 0.163 / 0.192 / 0.215 / 0.235 / 0.245 / 0.246 | 0.150 / 0.164 / 0.118 / 0.048 / 0.024 / 0.012 |
| P04 | 0.105 / 0.111 / 0.127 / 0.146 / 0.172 / 0.190 | 0.098 / 0.094 / 0.081 / 0.083 / 0.110 / 0.099 |
| P05 | 0.081 / 0.098 / 0.115 / 0.127 / 0.137 / 0.153 | 0.076 / 0.090 / 0.091 / 0.091 / 0.091 / 0.115 |

**Porta de GRA** (residu candidata/V38 per banda ≤1 / 1–2 / 2–4 / 4–8 / 8–16 / 16–32 / 32–64 px a finestres on la banda és soroll; objectiu ≤ 0,08 fi, ≤ 0,12 agregat; entre parèntesis el total de la V39):

| capa | finestra | residu per banda | total V40/V38 (V39/V38) |
|---|---|---|---|
| 01 | 5.5R | 0.02 / 0.01 / 0.01 / 0.01 / 0.02 / 0.04 / 0.06 | 0.02 (0.58) |
| 01 | 3.7R | 0.06 / 0.06 / 0.06 / 0.07 / 0.13 / 0.31 / 0.53 | 0.16 (0.59) |
| 04 | 5.5R | 0.03 / 0.02 / 0.02 / 0.02 / 0.02 / 0.02 / 0.03 | 0.02 (0.55) |
| 04 | 3.7R | 0.10 / 0.09 / 0.07 / 0.06 / 0.07 / 0.08 / 0.11 | 0.08 (0.53) |
| 06 | 5.5R | 0.01 / 0.01 / 0.01 / 0.01 / 0.03 / 0.12 / 0.35 | 0.09 (0.59) |
| 06 | 3.7R | 0.06 / 0.06 / 0.07 / 0.08 / 0.17 / 0.45 / 0.80 | 0.40 (0.67) |
| P03 | 5.5R | 0.09 / 0.06 / 0.03 / 0.02 / 0.03 / 0.10 / 0.18 | 0.06 (0.61) |
| P03 | 3.7R | 0.14 / 0.10 / 0.05 / 0.05 / 0.15 / 0.42 / 0.70 | 0.11 (0.62) |
| P04 | 5.5R | 0.12 / 0.06 / 0.02 / 0.03 / 0.09 / 0.24 / 0.47 | 0.32 (0.64) |
| P04 | 3.7R | 0.15 / 0.08 / 0.04 / 0.08 / 0.21 / 0.43 / 0.66 | 0.25 (0.62) |
| P05 | 5.5R | 0.12 / 0.09 / 0.08 / 0.10 / 0.15 / 0.26 / 0.38 | 0.17 (0.59) |
| P05 | 3.7R | 0.17 / 0.15 / 0.16 / 0.24 / 0.37 / 0.53 / 0.73 | 0.21 (0.60) |

**Porta de VORES** (rms per bins de distància signada a la vora exterior del camp de la Vixen, r > 2,8 R☉; salt = rms a 300–900 px dins / rms a 30–300 px fora; no pot ser pitjor que la V38):

| capa | salt V38 | salt V39 | salt V40 |
|---|---|---|---|
| 01 | ×1.17 | ×1.70 | ×7.76 |
| 04 | ×0.99 | ×1.24 | ×6.80 |
| 06 | ×1.36 | ×2.14 | ×5.72 |
| P03 | ×1.00 | ×1.07 | ×3.47 |
| P04 | ×0.94 | ×1.01 | ×1.10 |
| P05 | ×0.90 | ×0.95 | ×1.40 |

**Jutge Brno** (1°; rangs 1,2–3 / 3–5 / 5–9 R☉; control Brno×Brno +0.99 / +0.38 / +0.04; transferència agregada, «n/d» = Brno no hi correlaciona ≥ 0,10; [un Brno fora]; (sectors p16/med/p84)):

| capa | corr V38 | corr V40 | nul | transferència | rms V40/V38 |
|---|---|---|---|---|---|
| 01 | +0.70 / +0.24 / -0.01 | +0.70 / +0.29 / +0.05 | +0.05 / -0.03 / +0.01 | 0.97 [0.96,0.97] (0.93/0.96/0.98) / 0.89 [0.85,0.91] (0.66/0.76/0.86) / n/d [n/d,n/d] (n/d/n/d/n/d) | 0.97 / 0.66 / 0.09 |
| 04 | +0.58 / +0.10 / +0.01 | +0.61 / +0.18 / +0.09 | +0.04 / -0.01 / -0.02 | 0.89 [0.89,0.89] (0.83/0.89/0.91) / n/d [0.54,0.54] (0.26/0.36/0.57) / n/d [n/d,n/d] (n/d/n/d/n/d) | 0.90 / 0.22 / 0.03 |
| 05 | +0.73 / +0.29 / +0.00 | +0.73 / +0.32 / +0.04 | +0.07 / -0.03 / +0.01 | 0.99 [0.99,0.99] (0.97/0.99/1.00) / 0.97 [0.94,0.98] (0.82/0.90/0.95) / n/d [n/d,n/d] (n/d/n/d/n/d) | 0.99 / 0.85 / 0.16 |
| 06 | +0.73 / +0.32 / +0.01 | +0.73 / +0.34 / +0.02 | +0.07 / -0.02 / -0.01 | 1.00 [1.00,1.00] (0.98/0.99/1.01) / 0.99 [0.97,1.00] (0.88/0.91/0.97) / n/d [n/d,n/d] (n/d/n/d/n/d) | 1.00 / 0.90 / 0.20 |
| P03 | +0.52 / +0.07 / +0.00 | +0.64 / +0.30 / +0.10 | +0.05 / -0.00 / -0.01 | 0.94 [0.94,0.94] (0.89/0.92/1.00) / n/d [n/d,n/d] (0.76/0.94/1.09) / n/d [n/d,n/d] (-0.02/-0.01/0.01) | 0.91 / 0.19 / 0.05 |
| P04 | +0.54 / +0.34 / +0.09 | +0.54 / +0.45 / +0.05 | +0.07 / +0.10 / +0.04 | 0.90 [0.90,0.90] (0.89/0.91/0.94) / 0.95 [0.89,0.98] (0.76/0.87/0.92) / n/d [n/d,n/d] (0.67/0.67/0.67) | 0.91 / 0.70 / 0.52 |
| P05 | +0.52 / +0.21 / +0.11 | +0.55 / +0.29 / +0.26 | +0.04 / -0.05 / -0.10 | 0.93 [0.92,0.93] (0.89/0.92/0.95) / n/d [0.91,0.91] (0.84/0.88/1.00) / n/d [n/d,n/d] (n/d/n/d/n/d) | 0.94 / 0.65 / 0.31 |

A 4,5°: 01 0.97 / n/d / n/d; 04 0.91 / n/d / n/d; 05 0.99 / n/d / n/d; 06 1.00 / n/d / n/d; P03 0.96 / n/d / n/d; P04 0.87 / 1.17 / n/d; P05 0.96 / n/d / n/d.

**H1/H1b (ACHF, b4a):** 01 H1 0.079 · H1b 5.13; 04 H1 0.064 · H1b 2.67; 05 H1 0.057 · H1b 3.31; 06 H1 0.045 · H1b 2.51 (V38: 0,078/2,53 · 0,063/2,66 · 0,056/1,86 · 0,044/1,57).

**Dispersió del soroll entre les dues particions** (mediana |N1−N2|/(N1+N2) i quocient pAB / parell-senar): G: dog2 0.08 (1.16), dog8 0.10 (1.21), bpachf16 0.11 (1.18), atrous3 0.16 (1.35); R: dog2 0.07 (1.15), dog8 0.10 (1.22), bpachf16 0.13 (1.27); B: dog2 0.08 (1.16), dog8 0.10 (1.22), bpachf16 0.11 (1.20); bilat: bilat0 0.10 (1.22), bilat3 0.12 (1.28).

**Corba de preu (A3b, injecció cega, cota inferior):** quocient V40/V38 d'un blob DoG ± de σ 2 / 8 / 24 px a 1 / 3 / 10 %:

- **1.6R**: MGN 0.79 0.95 0.98 0.78 0.95 0.98 0.83 0.94 0.98 · WOW 0.79 0.94 0.97 0.79 0.94 0.97 0.83 0.94 0.97 · ACHF01 0.74 0.94 0.98 0.74 0.94 0.98 0.80 0.94 0.98 · ACHF04 0.73 0.93 0.96 0.73 0.93 0.96 0.79 0.93 0.96 · ACHF06 0.79 0.93 0.98 0.79 0.93 0.98 0.84 0.94 0.98  (ordre: 1 % σ2/8/24, 3 % σ2/8/24, 10 % σ2/8/24)
- **3.7R**: MGN 0.24 0.59 0.84 0.69 0.77 0.86 0.92 0.85 0.87 · WOW 0.21 0.65 0.84 0.58 0.82 0.88 0.89 0.88 0.91 · ACHF01 0.20 0.50 0.72 0.68 0.76 0.83 0.94 0.91 0.93 · ACHF04 0.20 0.43 0.53 0.67 0.71 0.69 0.94 0.89 0.85 · ACHF06 0.20 0.51 0.79 0.69 0.73 0.88 0.94 0.93 0.94  (ordre: 1 % σ2/8/24, 3 % σ2/8/24, 10 % σ2/8/24)
- **5.5R**: MGN 0.20 0.54 0.80 0.69 0.75 0.85 0.92 0.85 0.87 · WOW 0.18 0.61 0.85 0.56 0.79 0.89 0.87 0.88 0.92 · ACHF01 0.16 0.45 0.68 0.66 0.74 0.82 0.94 0.90 0.92 · ACHF04 0.16 0.39 0.47 0.65 0.69 0.67 0.93 0.88 0.85 · ACHF06 0.17 0.47 0.76 0.68 0.70 0.87 0.94 0.92 0.94  (ordre: 1 % σ2/8/24, 3 % σ2/8/24, 10 % σ2/8/24)

Vistes: `output/v39_20260909/lliurables/vistes/C3_retall_*`, `C3d_vora_vixen_*` (1:1 a la vora de la Vixen: V38 | V39 | candidata), `output/v40_20260909/lliurables/vistes/C4_compost_V40_llenc_sencer.png`.

## 5. Sobre la IA de reducció de soroll (pregunta de Pere)

No, per a les capes de dada: BlurXTerminator ja va fallar el criteri (research/156 §8: potència de les bandes fines ×2–5 i acord amb les dades independents a la baixa a totes les bandes); un model entrenat amb altres imatges no coneix el soroll d'aquesta per banda ni el que confirma l'altre telescopi (els streamers febles de 3–5 R☉, per sota d'1 σ per coeficient, els tracta igual que el gra); no és reproduïble ni declarable. Codex: cap ús defensable com a capa científica; només com a capa estètica declarada o com a detector de zones, mai font de píxels. La regla de §3 és «un reductor de soroll amb el model de soroll VERITABLE d'aquesta imatge».

## 6. Contrast amb Codex (GPT xhigh, tema `v40-desencallar-soroll`)

Coincideix en les tres causes i en l'arquitectura, amb correccions adoptades: (1) la guarda de les vores per escala i per tren, d ≥ max(16, ℓ), comprovada fins que N faci plataforma; on no hi ha interior suficient la banda és «no estimable» i s'extrapola des de la zona vàlida (és el que fa la finestra normalitzada); (2) la regla max(Wiener regional, garrote k = 3), residu 0,05–0,08 per banda, pas objectiu del compacte 3 σ 0–0,10 · 4 σ 0,35–0,55 · 5 σ 0,55–0,75 · 7 σ ≥ 0,75; el ferm 2,5→4 deixaria 0,11–0,13 (massa) i la mixtura bayesiana per regió es deixa per a més endavant (fàcil de sobreajustar); normalitzar per max(σ_local, σ_soroll) no resol el cas pur; (3) el creuat fora del guany i sense ploma; (4) la IA no; (5) el pilot sense PSB, amb les tres portes i la mirada a 1:1; el soroll de diverses bandes residuals se suma: la porta ha de ser també sobre la capa final (u16, després de tanh/LUT), no només per banda.

## 7. Trampes d'aquesta ronda

- **Una reducció del 40 % de l'amplitud del gra no es veu**: la percepció és de presència; qualsevol regla per coeficient que conservi el feble aïllat deixa el gra. El residu s'ha de mesurar com a amplitud residual sobre soroll pur (sintètic) i sobre la capa final.
- **Un guany que existeix només on hi ha un segon tren dibuixa el contorn del segon tren**, per bo que sigui el que protegeix.
- **L'estimador de meitats és invàlid a TOTES les vores del suport comú, no només al forat**; la guarda és per escala.
- **Les marques de Pere poden ser un contorn sencer**: un component gran amb el centroide al centre del Sol és un rectangle resseguit, no una taca.
