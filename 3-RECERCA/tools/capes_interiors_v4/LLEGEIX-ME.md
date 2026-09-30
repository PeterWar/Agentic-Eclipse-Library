# CapesInteriorsV4: màscares netes per a l'HDR interior de Photoshop (19/20-08-2026)

**El disseny final és el de `v5_*`** (decisió de Pere: «prefereixo la V3, manen les capes
inferiors»): les màscares de V3 promitjades per anell + cascada de protecció + Lluna negra,
ordre i aspecte de V3. La cadena `dissenya_v4`/`rasteritza_v4`/`construeix_v4` és el primer
disseny (radial de nou encuny amb altiplà i Color Dodge), refusat però conservat com a
referència del sostre no comprimit.

Codi de la sessió que va diagnosticar les màscares de `CapesInteriorsV3.psb` (Pere) i va
construir `CapesInteriorsV4.psb` (nota `research/84`; LLEGEIX-ME de lliurament a
`~/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors/Documentacio i QA/V4/LLEGEIX-ME_CapesInteriorsV4.md`).
Tot sobre `~/.venvs/eines-ia-py312` (psd-tools 1.18, numpy, scipy, matplotlib), des d'un
directori de treball on es creen `v3/` i `v4/` (rutes relatives). `psb_utils.py` és la còpia de
`../encaix_sony/psb_utils.py`.

| Script | Què fa |
|---|---|
| `inventari_v3.py FITXER.psb…` | estructura de capes (ordre de baix a dalt, bbox, màscara, mode, visibilitat) |
| `extreu_v3.py` | bolca cada capa de V3 (RGB uint16) i la seva màscara (16 bits) a `v3/*.npy` + previsualitzacions |
| `verifica_compost.py` | reprodueix el compost de Photoshop (espai codificat, màscares com a alfa, de baix a dalt) i el compara amb el fusionat del PSB: 1·10⁻⁵ |
| `registre_v3.py`, `alineacio_12.py`, `alineacio_exteriors.py`, `compara_capa45.py` | alineació entre capes (corona), la 1/3200 via la protuberància, V3 contra CapesExteriors (EDITAT PERE, 03_1s): **V3 és a (+1,+1) px** |
| `limbe2_v3.py` | limbe lunar per gradient i ajust de cercle; vora de la màscara de disc de Capa 4 |
| `perfils_v3.py`, `polar_maps_v3.py` | mostreig polar (r 0,9–4 R☉ cada 0,005, θ cada 0,5°) de capes i màscares; pesos efectius; compost V3 i compost amb màscares promitjades per anell; quocient |
| `tonecurves_v3.py` | corba de to de cada capa contra l'HDR lineal calibrat (`Corona_HDR_Vixen`): totes iguals, γ local ≈ 1 fins a e≈0,2 i compressió després |
| `validesa_v3.py`, `perfils_exteriors_v3.py` | percentils azimutals (50/95/99) del canal màxim per radi, soroll per capa; perfils de 4 a 11,5 R☉ |
| `dissenya_v4.py` | **el disseny**: validesa per capa (P95_MAX 0,66, P50_MAX 0,46, rampa 0,12 R☉), sostre vàlid, perfil objectiu (V3 limitat al sostre, monòton, genoll arrodonit per sota, unió suau en ln), pesos per parelles adjacents (camp llunyà: 05 + Capa 4), màscares m_k(r) → `v4/disseny.npz` |
| `rasteritza_v4.py` | màscares a resolució completa (coordenades de V4 = V3 − (1,1); disc lunar a 0; marc), compost, capa de guany radial (Color Dodge, p99,5 ≤ 0,97), previsualitzacions |
| `construeix_v4.py` | el PSB des de zero amb `psb_utils` (capes ZIP, màscares 16 bits ZIP-pred, Lr16, fusionada) |
| `verifica_v4.py` | rellegeix el PSB: estructura, profunditat de les màscares, compost rellegit vs el meu (3·10⁻⁵), fusionada |
| `qa_v4.py`, `compara_estructura.py` | test d'anells, pendent, correlació i contrast de l'estructura azimutal amb les capes soles, figures |

Ordre: `extreu_v3` → (`registre_v3`, `alineacio_*`, `limbe2_v3`) → `perfils_v3` → `polar_maps_v3` →
`validesa_v3` → `perfils_exteriors_v3` → `dissenya_v4` → `rasteritza_v4` → `construeix_v4` →
`verifica_v4` → `qa_v4`, `compara_estructura`.

## Disseny final (v5)

| Script | Què fa |
|---|---|
| `v5_radialitza.py` | perfils radials (mitjana azimutal) de les màscares de V3 → màscares radials × disc lunar × cascada de protecció (1/125 cremada → 1/500; 1/500 cremada → 1/3200); compost i previsualització |
| `construeix_v5.py` | reescriu `CapesInteriorsV4.psb` amb l'ordre de V3 (la 1/3200 a baix sense màscara, 04/03 ocultes), màscares a 16 bits; l'anterior queda com a `.anterior-disseny-claude` |
| `verifica_v5.py` | rellegeix el PSB i recompon dues finestres contra el compost (3·10⁻⁵) |
| `qa_v5.py` | perfil contra V3 (±7 %), test d'anells (0,18 % rms), correlació/contrast amb les capes soles, zooms |

## CapesInteriorsV5 (matinada del 20-08): sobre el V4 editat de Pere

| Script | Què fa |
|---|---|
| `extreu_v4_editat.py`, `identifica_capes.py` | bolquen màscares/píxels del V4 editat i identifiquen cada capa contra les conegudes (12 capes: dues 12, Capa 1/2 = velles C4/C5, dues 09, 08…03) |
| `analitza_v4_editat.py` | **limbe lunar per capa** (centres ~3 px de ball, radis 449,5–451,8 px) i diff de màscares (on ha repassat Pere) |
| `perfils_v4_editat.py` | perfils de les màscares editades i del compost amb/sense 04-03 |
| `mascares_0403_v5.py` | les màscares noves: max(vella de Pere, neta radial monòtona aplanada de 3 R☉ enfora, zero fins a 1,15/1,25) |
| `compon_v5.py`, `escriu_v5.py` | compost final i el PSB V5 (round-trip del V4 editat, només canvien les dues màscares + merged) |
| `verifica_v5psb.py`, `qa_v5_final.py` | capes byte-idèntiques, màscares substituïdes, merged = compost; diff per bandes radials, test d'anells, zooms |
