# Constants mesurades (estat 17-08-2026)

Tot el que és aquí està **mesurat** i té la font al costat. Si un número canvia,
canvia'l aquí i al `3-RECERCA/` corresponent, no només al codi.

## Lloc, instant, geometria

| | Valor | Font |
|---|---|---|
| Lloc | MIRADOR FINAL 2, 42,299407 N, −5,02503 E, 798 m | run `20260812T202219` |
| C2 / C3 predits | 18:28:46 / 18:30:29,2 UTC (20:28:46 local) | app |
| C2 / C3 reals (fotogrames de 1/3200) | −1,0 ± 0,7 s / +102,7 ± 0,7 s del predit → **103,7 s** | `71` |
| Sol a mig totalitat | altura 9,07–9,2°, massa d'aire 6,02 → 6,20 (C2 → C3) | `75`, `78` |
| Refracció total | 5,6–5,8′; compressió vertical del camp 0,77 % (Sony) / 0,80 % (R6) | `75`, `77` |
| Dispersió atmosfèrica R–B | 3,08 ± 0,3″ a PA 170° | `75` |
| Lluna − Sol (topocèntric, DE440s) | **0,5905 ″/s a PA 118°**; 2,8 px en 10,3 s al Vixen | `71`, skyfield |
| Sol sobre el fons estel·lar | 0,041 ″/s | `76` |
| Rellotge A7RIIIA | +0,38 s avançat (mesura del 08-08; invalidada si es toca) | CLAUDE.md §7 |

## Deriva

| | Valor | Font |
|---|---|---|
| Vixen, estrelles | 0,610 ± 0,010 ″/s, direcció −45°, constant, cap salt | `75` §5.4 |
| Vixen, **corona** (el que mana per apilar) | **0,578 ″/s** (dos camins al 0,3 %); 0,5764 al model del manifest | `76` §2 |
| Vixen, deriva lliure post-C3 | 0,689 ″/s = 0,21 refracció + ~0,48 muntura (error polar ~2°) | `71` |
| Sony, salts | +223 px x (~C2+35 s), −715 px y (~C2+50 s); rotació de camp 0,138° | `72`, `75` |
| Sony, entre salts | 0,5–1 px; àncores 1 i 3 amb 0,5–0,75 px de moguda interna | `72` |

## Placa i calibratge absolut (`75` §5, `Estrelles/`)

| | Sony A7RIIIA + 300 GM | R6 III + VSD90SS |
|---|---|---|
| Estrelles | 38 de 38 | 22 de 24 |
| Residu de placa | 0,54 px (rms 0,71) | 0,32 px (rms 0,42) |
| Escala | **3,2020 ″/px** (discrepància −1 % amb 3,234 lunar, oberta) | **2,1495 ″/px** |
| Nord / Est | PA 90,27° / 358,64° | PA 57,19° / 325,59° |
| Centre del Sol (fotograma de referència) | (3894,7, 2768,7) DSC06993 | (3570,8, 2267,1) 572A2983 |
| Punt zero | +14,17 ± 0,08 mag | +14,21 ± 0,08 mag |
| B/B☉ per ADU/s (píxel verd) | 1,134 × 10⁻¹¹ | 2,772 × 10⁻¹¹ |
| Radi solar / lunar | 295,8 / 308,7 px | 446,15 / 453,8 px (limbe real; 460 al model) |
| Cel a 8 R☉ | 9,34 mag/arcsec² | 9,15 mag/arcsec² |
| FWHM total (verd) | 8,3 ± 0,5″ (tova des de 27–38 min abans de C2, filtre posat) | 5,8 ± 0,4″; per canal 4,2–4,6 / 5,5–5,8 / 6,5–6,7″ |
| Trens entre si | quocient R6/Sony **0,95** sobre la corona | |

`F☉ = 10^(0,4·(ZP + 26,75 − 0,653·c))` — amb el terme de color; sense ell el
biaix és −4,5 % i +9,4 %.

## Extinció i cel

| | Valor | Font |
|---|---|---|
| **k (diferencial, dins la totalitat)** | **0,402 ± 0,036 mag/massa d'aire** → corona −5,5 % de C2 a C3, multiplicatiu i uniforme en azimut | `78` §3 |
| k per estrelles | 0,416 (Sony) i 0,723 (R6): **contaminat pel vinyetatge, no val** | `75` |
| Cel de la totalitat | V de 509 → 335 → 491 ADU/s (±20 %); fons 283–332 ADU/s; la corona l'iguala a ~3 R☉ | `76` |
| Fronteres de saturació on surten arcs | 1,03 · 1,09 · 1,18 · 1,30 · 1,44 · 1,96 R☉ | `76` §5 bis |

## Validacions que han de sortir

| | Valor |
|---|---|
| Perfil K+F (Vixen) | 3,3·10⁻⁶ B☉ a 1,02 R☉ · 1,3·10⁻⁶ a 1,10 · 1,4·10⁻⁷ a 1,5 · 2,2·10⁻⁸ a 2,0 · 4,9·10⁻⁹ a 3,0 · 1,0·10⁻⁹ a 5,0 |
| Continuïtat entre esglaons | ≤ 0,3 % (viu 0,02 % mitjana, 0,24 % màxim; el pla demanava 3 %) |
| Registre HDR4 | ≤ 0,09 px als 17 parells; entre apilats ≤ 0,08 |
| Test d'anell per sectors (D nu, 4,6–5,4 R☉) | ≤ 0,15 % |
| Jerarquia azimutal a 2 R☉ (gran/fina) | lineal 124:1; el realçat no la pot deixar per sota de ~300:1 amb guanys declarats |
| Earthshine vs LROC (fora de mostra) | Sony 2×8 s r = 0,68 (escala completa) / 0,73 (mitja) |
| Dos trens (quan hi hagi l'HDR Sony) | ≤ 0,25 EV a 1,5–3,5 R☉; crestes radials al mateix PA a 0,08–0,22° |
