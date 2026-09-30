⛔ **REFUSADA PER PERE (07-09, nit)**: «no vull corregir estèticament sense atacar l'arrel» ni «sacrificar detall». Els 29 traços de `V33_Artefactes.psb` són costures que el suavitzat de la V33 va fabricar (research/149, vistes `V32_vs_V33_*.png`). Es conserva com a evidència del que NO s'ha de fer; producte vigent: V32.psb. Norma: `norma-causa-arrel-mai-cosmetica`.

# 148 — V33: els filtres amb la resolució que segueix el S/N, i NRGF/RHEF sense la vora del llenç

Lliurada el 2026-09-07T16:53:56.741815+00:00 per ordre de Pere («fes la V33»; el taronja de la RHEF = zona molt pixelada i sense detall). PSB LLEUGER (norma del 07-09): una base lineal + les 10 capes iterades. Les altres capes de la V32 (bases, azimutals 03/03/07, NAFE, precursors, SWAP, C01, estrelles, reflex, les de Pere) no s'han tocat i es queden a `V32.psb`.

- Fitxer: `/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V33.psb` · 10551 × 7506 · RGB16 · 11 capes · 3,622,418,302 bytes · SHA-256 `79424a49c459953ce02b8ae26d9c0400bdb524861eaa0a38c31b617d9f6b33f3`.
- Photoshop real: **OBRE 10551 px x 7506 px · 11 capes**. Font de modes/màscares: `V32.psb` (`dcfc8f53…`), no modificada. Base: la fusió lineal V32, sense cap canvi.

## Què canvia (dos canvis declarats, tots dos als filtres)

1. **Resolució que segueix el S/N** (snmap.sn_v33): σ(x) = max(σ_mapa, σ_local). σ_mapa ve del mapa C0, mesurat: coherència de Fourier entre parelles independents (Sony A×B, Vixen×Sony B) per tessel·les de 512 px, bandes de 8 a 256 px, nul per desplaçament de fase; σ = λ_mín/4 de la banda coherent més fina (transferència 0,29 a λ_mín, 0,73 al doble), 32 px si cap banda és coherent, suavitzat 128 px; a l'interior (r < 2,0) σ = 0,7 fixa com la V29 (les tessel·les no mesuren la corona interior amb la Lluna dins), rampa fins a 2,65. σ_local és f3.suavitza_sn autocalibrat (t 0,18): els graons de gra fi de les entrades de fotogrames. Aplicat a les 5 capes de cadena (en lloc del mapa de resolució congelat de la V29, σ ≤ 8) i, com a pas declarat, al resultat float de les 5 vistes pures (MGN, WOW, WOW bilateral, NRGF, RHEF). σ mediana resultant (capa 05): 1.5 R☉ → 1.1 px, 2.0 R☉ → 2.0 px, 2.65 R☉ → 6.5 px, 3.0 R☉ → 8.0 px, 4.0 R☉ → 13.5 px, 5.0 R☉ → 18.5 px, 6.0 R☉ → 22.5 px, 8.0 R☉ → 30.2 px.
2. **NRGF/RHEF sense la vora del llenç**: de r_edge = 8.48 R☉ enfora (primer anell que toca la vora) la mitjana i la desviació de l'anell SENCER s'estimen dels píxels presents amb la forma azimutal z-normalitzada dels 40 últims anells sencers (funció global, la idea pendent de la tesi de Druckmüllerová §6.1.2); el rang de la RHEF passa a la CDF empírica d'aquests anells, contínua amb el rang empíric. Cap retall, cap radi d'exclusió.

## Mesures, mateixa vara (V32 → V33)

| capa | gra fi a 4 R☉ (rms u) | gra mitjà a 4 R☉ | H1 pitjor | H1b |
|---|---|---|---|---|
| 01 | 0.0107 → 0.0008 | 0.0182 → 0.0056 | 0.0085 | 4.42 |
| 02 | 0.0115 → 0.0011 | 0.0258 → 0.0090 | 0.0108 | 2.53 |
| 04 | 0.0204 → 0.0007 | 0.0169 → 0.0042 | 0.0230 | 15.42 |
| 05 | 0.0107 → 0.0008 | 0.0194 → 0.0063 | 0.0131 | 1.69 |
| 06 | 0.0108 → 0.0009 | 0.0203 → 0.0066 | 0.0069 | 1.34 |
| P01 | 0.0041 → 0.0001 | 0.0023 → 0.0008 | – | – |
| P02 | 0.0125 → 0.0002 | 0.0066 → 0.0016 | – | – |
| P03 | 0.0854 → 0.0010 | 0.0264 → 0.0057 | – | – |
| P04 | 0.0354 → 0.0012 | 0.0308 → 0.0097 | – | – |
| P05 | 0.0355 → 0.0007 | 0.0197 → 0.0052 | – | – |

Anisotropia tangencial a l'anell de la vora del llenç (8,3–8,8 R☉; +1 = cercle): P01 σ16 +0.45 → +0.09, σ32 +0.89 → +0.20; P02 σ16 +0.11 → +0.02, σ32 +0.66 → -0.00.

Geometria azimutal (pic a 0°, nul a 180°): PASS a les cinc capes de cadena. H1b (potència a la freqüència dels calaixos) queda alt a 01 i 04: allà on la capa queda gairebé plana el quocient es dispara sobre valors petits; es declara, no es corregeix.

## Límits

- La resolució exterior és la que els dos trens comparteixen: de 4 R☉ enfora només queden les estructures de 64 px o més; el detall fi que hi hagués per sota queda fora per decisió (Pere: «molt pixelada i amb poc detall»).
- Les vistes pures ja no són pures: porten el suavitzat S/N declarat al nom. Els float abans del suavitzat no es guarden.
- Les azimutals 03/03/07 i les altres capes no s'han iterat (cap marca de Pere).
- El judici visual de Pere queda obert. Vistes: `output/v33_20260907/lliurables/vistes/` (polars V32|V33 per capa i tram, retalls a les marques, gra per radi, mapa C0).

Codi: `research/tools/v33_20260907/` (c0 resolució, c1 cadena, c2 pures, c3 portes, c4 PSB, snmap). Rebuts: `output/v33_20260907/4-rebuts/`.
