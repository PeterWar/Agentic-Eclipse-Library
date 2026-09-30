# El limbe lunar de l'earthshine: les tres vores, el forat de la base i l'ala de la PSF

> **Qualificació vigent 15-09-2026.** Aquest document conserva el relat i les receptes V50–V53. La investigació posterior no ha separat tota la fotometria ampla de la llum dispersada: S8 pot retirar senyal lunar i té un error de mig sector. La taca ampla V68 continua pendent. Les frases de «cura» i «disc pla» de sota no són validació física general ni autorització per reaplicar S8. Els detectors absoluts finals van fallar també en versions de referència: conservar els resultats i els llindars, no exigir-los com a PASS ja demostrat. Estat i fonts a `../../postprocessat-corona/references/estat_i_reproductibilitat.md`.

Lliçó de les V50–V53 (12/13-09-2026). Pere: «per fi puc ajustar la brillantor de la Lluna sense preocupar-me pels halos al limbe… no m'hi vull tornar a trobar».
Codi: `3-RECERCA/tools/earthshine_v50_temporal_20260912/` (m1_vores, s1_capes, s4_origen, s5_candidat_origen, s8_vel, s9_psb_v52).
Informe: `4-RESULTATS/earthshine_v50_temporal_20260912/RESULTAT.md`. Traspassos `.coordination/HANDOFF_2026-09-12_EARTHSHINE_V5{1,2}.md`.

## Símptoma

Franja blanca als últims píxels de la Lluna, vall fosca esglaonada just fora, protuberàncies que «volen» (separades del disc per una línia fosca), i un gradient de brillantor ampli dins del disc que Camera Raw amplifica.

## Diagnòstic històric V50–V53: comparar vores al mateix marc, distingint detectors

Al marc de la ROI lunar (1400², centre lunar (699,57; 699,65)), 1440 azimuts i ajust de cercle robust `r(θ) = R + dx cosθ + dy sinθ` (`m1_vores.py`). **Rectificació V85 R03:** F4 usa el màxim de derivada radial amb σ0,75 px; `m1_vores.py` ajusta directament aquest contorn. El detector del 50 % s’aplica a les altres vores. La diferència de radis inclou aquesta diferència de definició i no prova un error físic uniforme de 2 px:

| vora | R (px) | centre (dx, dy) | què és |
|---|---:|---|---|
| silueta aparent de la font lunar (F4) | 453,5 | (−1,0; −0,6) | màxim de derivada òptica aparent; no contorn físic independent |
| forat de la base | 457,2 | (−0,5; −0,1) | disc MODELAT 455,5 + 2 px de guarda (+2 de rampa) |
| alfa de la capa lunar (heretada V44) | 456,3 | (−1,7; −0,2) | pes FOTOGRÀFIC ajustat, no cobertura |
| Llunes de les capes solars de Pere (12/11/10) | 453,2–453,5 | ≈ (−3; +0,3) | instants 7–8 s, 2 px a l'esquerra de F4 |

Entre F4 i el forat: la capa lunar ensenya els seus últims píxels (llum solar de la PSF) i, on l'alfa s'acaba abans que el forat, la base emmascarada (negre). Cap capa solar hi té corona.

## La causa a l'origen (i no a la composició)

La fusió V38 (`b2_recomposicio.py`) emmascara cada fotograma amb `f2.mascara_lluna`: disc d'efemèride **455,5 px + GUARDA 2 + VORA 2**. La silueta aparent F4, definida pel màxim de derivada radial, fa **453,5**: cap fotograma aporta corona als seus 4–6 px més propers al limbe. A la dreta els fotogrames tardans (Lluna ja desplaçada) ho cobreixen; a l'esquerra, dalt i baix no ho cobreix ningú. TOT el que les V44–V49 feien al contorn penjava d'aquest buit.

## Què NO va valer

- **K0** (només màscara geomètrica): revela l'anell negre. **N1/N2** (foto 10 de Pere sota): costura marró (to diferent). Inverses de PSF (A/E/F/G/I): sense on agafar-se.
- **V50: capa d'anell** amb la corona dels fotogrames curts registrats a la Lluna, igualada al to de la base. Funcionava als números i **Pere la va refusar**: «estem tapant les incorreccions en capes», contra `RECOMANACIO_2026-09-11_RETOCS_MANUALS_CAMERA_RAW.md`. Norma: cap capa de compensació al contorn.

## Recepta històrica V51: recompondre la base amb la mateixa maquinària i la màscara correcta

`s4_origen.py`, 45 s: bucle A1/B2 de la V38 a la caixa lunar (996², ±1,13 R☉) amb els 67 fotogrames Vixen, el seu registre, pesos, offsets, camps phi, flat i correcció de vora, canviant NOMÉS la màscara lunar per fotograma, **per nivells**:

- nivell 1 = màscara vigent (`f2.mascara_lluna`, correcció B2) → la base NO canvia on ja tenia dada;
- nivells 2–4 només omplen on no hi ha nivell millor: curts D ≥ 0 / −2 / −4, mitjans D ≥ 0,5 / −0,5, llargs D ≥ 1,5 (D = distància al limbe MODELAT del fotograma); pesos de nivell 1 / 0,02 / 4e−4 / 8e−6; dins de cada nivell pes ∝ 1/correcció² (inversa de variància); als nivells 3–4 el valor central és la **mediana entre curts** (≥ 3 fotogrames), robusta al registre de cada fotograma;
- correcció de vora estesa al perfil A1 mesurat (`A1_franja_font.json`, mediana ln(fotograma/compost net)) per D < −1,75 (la taula B2 hi acaba).

Recepta de pantalla **exacta** de la base V42 (`b4e_bases_v42.py`, k = 1) reimplementada (reprodueix `base_corba_total_v42_u16` a 0 DN16) amb el **camp de color de 24 px congelat** al de referència: només canvia on canvia la lluminància. Guardarails obligatoris: amb la màscara vigent es reprodueix `vixen_total_v38` (p99,9 relatiu 2e−4); fora de 8 px del limbe ≤ 84 DN16 puntuals.

Al PSB: RGB de la base només a la caixa (i només a d < 6 px o on no tenia dada), màscara de la base oberta on hi ha dada (d ≥ −2), alfa de la capa lunar = rampa geomètrica −1…+1 px, forats sense dada a ±3 px omplerts amb el veí vàlid (declarat). Cap capa nova.

## Interpretació històrica V52, posteriorment qualificada: el «gradient» que Pere marca

La capa lunar revelada puja +40 % de −80 a −20 px del limbe i ×2–3,5 als últims 8 px, **igual a tots els sectors**: és llum de la corona dispersada per l'òptica, no relleu. Cap selecció d'exposicions no la treu (ala i earthshine escalen igual amb el temps). Cura (`s8_vel.py`): vel mesurat a la MATEIXA capa per sector de 5° (perfil radial mediana 2 px; nivell del disc a −260…−200; excés suavitzat σ 3 px en d i 10° en θ; monòton cap al limbe; taper −260→−200) i restat als tres canals (capa monocroma). Una iteració de refinament amb el residu a −70…0 i **taper continu** (1 a d ≥ −40, 0 a −70). El disc queda pla ±2 % fins al limbe, a 7–10k ≈ 0,18 de la corona (el nivell de Brno); Pere pot aclarir-lo després sense halos.

## Trampes (totes viscudes)

1. `from comu42 import *` exporta `CAU`/`OUT`: defineix les rutes DESPRÉS dels imports o els resultats van a `v29/cau_final/`.
2. La recepta b4e suavitza el color a 24 px: ampliar el suport canvia el color fins a 72 px enllà. Congela el camp de color de referència.
3. Els fotogrames curts dins de la seva silueta amb correcció ×2–9 contaminen on hi ha fotogrames millors: nivells + inversa de variància.
4. Píxels amb un canal ≤ 0 (matriu de color a píxels saturats) SÓN suport: excloure'ls fa forats a les protuberàncies.
5. Exigir ≥ 3 fotogrames a la mediana deixa forats aïllats al limbe que l'alfa lunar ensenya com a puntets foscos: omplir-los.
6. «Alfa 1 on la base no té dada» només a d ≤ 1,5 px; fora del limbe la capa lunar mai no es veu (si no: marc fosc a tota la ROI).
7. El R de la base és 1,0 (retallat) a tot el limbe: cap ajust de to en log amb píxels retallats.
8. Els `weight` de la V44 no codifiquen saturació: compara exposicions.
9. Un refinament aplicat només fins a −40 px amb tall sec deixa un graó de ±3–7 % que Pere veu en aclarir la Lluna: tot taper continu.
10. Rampes d'alfa d'1 px fan dents a 6×; 2 px no.

## Detectors històrics — no són un PASS vigent

- Perfil radial mediana de la CAPA LUNAR per sector de 30°, d de −300 a +8 px: ha de ser pla fins a 2 px del limbe; cap graó > 2 % entre bins veïns.
- Perfil del COMPOST per sector, d de −3 a +8: monòton del disc a la corona; el mínim a 0…8 px ≥ 90 % de la corona a 8–14.
- El criteri històric exigia les tres vores amb el mateix detector i coincidència a ±1 px. R03 comprova que F4, forat de la base i alfa lunar no es van mesurar amb el mateix detector; aquesta comparació no és una coincidència física verificada.
- Arcs alineats amb el limbe: en polar, part suau en θ (σ 10°) passa-alt radial 12 px; rms per d < 100 DN16.


## V70/V71 (16-09-2026): la taca ampla és vel amb component azimutal

Mesura (`3-RECERCA/tools/v71_marques_v69_20260916/a20_perfils_azimutals.py`, `a15_taca_fotogrames.py`): perfils per
sectors de 10° a r 0,45–0,65 R del disc normalitzat per anells. RAW Vixen 10 s: ±2 %, màxim a l'oest (az 130–170°),
mínims a l'est (0–50°) i al SSW (240–270°). Capa lunar V69: el mateix patró ×10 (r 0,957 amb el RAW). LROC: mínims a
l'est (mars) i màxim ×1,6–2,0 al sud (terres altes). Corona al limbe (1,03–1,10 R): mínim al SSW (0,61–0,63) i al NE,
màxim a l'oest. Correlacions: RAW disc–corona +0,60 (base) / +0,42 (RAW 0,5 s, saturat), RAW disc–LROC −0,09,
LROC–corona −0,54. La «taca» (az 259°, r 0,3–0,75 R) és la vall del vel cap al sector de limbe més feble; el vel
V52/V53 (radial per sector de 5°, nivell del disc a −260…−200 px) hi és cec per construcció. Els RAW situen la
depressió a (−62, +299) ± 6 px del centre lunar en 10 fotogrames de C2+11 s a C2+92 s (fixa a la Lluna, no al sensor).
Rotació llenç↔sensor Vixen 11,0°, escala 0,980 (R lunar 447 px natius contra 456 al llenç).
Cura possible només a l'origen: vel 2D (corona lineal ⊗ ala de PSF mesurada, els dos nuclis del model d'agost a
`4-RESULTATS/derivats/Earthshine/Earthshine_FINAL/earthshine_FINAL_halo_params.json`) o separació temporal (la Lluna
es mou 28 px respecte de la corona; l'albedo no). V71 aplica la correcció al revelat de Pere com a factor multiplicatiu suau (escales > 100 px, limbe i mitjana per anell intactes): vegeu `3-RECERCA/tools/v71_marques_v69_20260916/a28_vel2d.py` i `a29c_amplitud_final.py`; la cura exacta seria al vel de les fonts lineals (backup).
