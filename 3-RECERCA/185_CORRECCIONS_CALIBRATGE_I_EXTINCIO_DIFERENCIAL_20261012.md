# 185 — Correccions del calibratge i extinció diferencial (12-10-2026)

**12 d'octubre de 2026 · Claude.** L'11 i el 12-10 vam calibrar el compost lineal en brillantor solar mitjana (MSB = B/B☉). Era una proposta rebuda per a la revisió 10 de l'article sobre la imatge *[editat per a la publicació: sense el nom d'un corresponsal]*. Verificadors independents ho van refer amb codi propi, en dues rondes. Pel camí van sortir coses que fèiem malament des de l'agost. Aquesta nota les recull: què fèiem, la prova, el valor corregit i on és el detall.

- No reescriu cap nota vella. La taula del final diu què queda superat.
- La imatge no s'ha tocat. No s'ha enviat ni publicat res.
- Rutes relatives a `4-Photoshop/`. `MSB/` vol dir `3-RECERCA/resultats/msb_calibrat_20261011/`.
- Tot és provisional fins que Pere ho vegi.

## En poques frases

1. **Extinció diferencial.** Amb el Sol a 9°, la corona de cap a l'horitzó arriba més apagada que la de cap al zenit. Respecte del centre, un 9 % a 1,5 R☉ i un 23 % a 4 R☉; cap al zenit, al revés. Són xifres calculades amb k = 0,40. No s'havia corregit mai. La imatge continua sense corregir-la.
2. **Cel.** El cel que restàvem portava corona, i el pla del cel s'empassava part del dipol d'extinció. La corona de fora queda massa baixa (4 / 9 / 16 % a 3 / 4 / 5 R☉). I la prova del valor de k depèn del cel.
3. **K-Cor (01-10).** Comparàvem la brillantor total amb només la corona K, des d'una GIF i amb un anell dins la franja lunar. El «+13–15 %» era sobretot la corona F. Ara: 1,06–1,12, compatible.
4. **C2 (01-10).** Només fèiem servir el calibratge de SolarSoft, un 13,5 % per sota del de Colaninno i Howard (2015). Ara: 1,14–1,40 amb Colaninno i Howard (dins d'1σ) i 1,32–1,62 amb SolarSoft. La causa de la diferència no està resolta.
5. **Punt zero.** No és ±10 % simètric: és −17 % / +2 %. El terme de color no és significatiu (±9,4 %, a part). Sobre els apilats, les dues càmeres donen 0,83, no 0,95. Obert.
6. **Continua valent:** l'estructura en angle contra K-Cor, C2 i SDO, l'orientació, les protuberàncies i l'acord amb el K-Cor (ara dins de la incertesa).

## 1. L'extinció diferencial no s'havia corregit mai

**Què fèiem.** Tota la cadena tracta el camp com si tingués una sola massa d'aire.
- `3-RECERCA/tools/eclipse_determinista/comu.py` (`EXTINCIO`) declara un sol vector de color per a X = 6,12 (Sol a 9,07°): `nomes_extincio` = (1,691; 1; 0,2815). Va als rebuts.
- `f4.py` només el fa servir per a una capa oculta («07 SOBRE L'ATMOSFERA»). Canvia el color igual a tot el camp. La base no el porta: Pere es queda el daurat que va veure.
- La caiguda en el temps (el Sol es pon durant la totalitat) sí que es compensa: un guany global per fotograma (`f2.py`, `coherencia`; nota 78). La diferència entre punts del camp, no.
- Cap imatge ni perfil d'abans de l'11-10 no portava la massa d'aire per píxel. Només l'ajust del punt zero en feia servir una per estrella.

**Calculat (model geomètric + k predeclarat).** No és una mesura. Ho calcula `3-RECERCA/tools/msb_calibrat_20261011/msb_comu.py` (astropy, altura aparent, Kasten–Young). El verificador ho refà amb codi propi: diferència ≤ 3 × 10⁻⁴. La mesura que ho sosté és a «La prova a les dades».
- Mirador a 42,299407 N, −5,02503 E, 798 m. Hora del mapa, 18:29:34 UT. Sol a 9,17° d'altura aparent.
- Massa d'aire al centre del Sol: 6,053. A l'instant del punt zero: 6,024.
- A 2 R☉ del Sol, en vertical: **5,751** cap al zenit i **6,387** cap a l'horitzó.
- El zenit és a l'angle de posició solar **33,2°**. L'horitzó, a l'oposat (213°).
- **k = 0,40** mag per massa d'aire. És el valor predeclarat (model de la nota 109 §12). La nota 78 el mesura per una altra via: **0,402 ± 0,036**, de la baixada de la corona entre C2 i C3 als mateixos píxels.
- Factor de correcció, E = 10^(0,4·k·(X − X☉)), en vertical:

| r | Cap al zenit | Cap a l'horitzó |
|---|---:|---:|
| 1,5 R☉ | 0,919 | 1,095 |
| 4 R☉ | 0,809 | 1,297 |

- Dit a l'inrevés (amb k = 0,40): sense corregir, la banda de l'horitzó surt un 9 % fosca a 1,5 R☉ i un 23 % a 4 R☉. La del zenit surt un 9 % i un 24 % massa clara.
- Amb k de 0,35 a 0,72, la correcció a 4 R☉ cap a l'horitzó va de +26 % a +60 %.
- A la mediana de cada anell l'efecte és ≤ 2,6 %. El perfil radial gairebé no canvia. El que canvia és la diferència entre dalt i baix.

**La prova a les dades.** Sense corregir, el quocient nostra/LASCO C2 té un dipol de **+0,17 a +0,28** (en ln) a 2,4–3,3 R☉. Apunta a PA 30–37°, amb tots els models de cel. És el signe i la direcció de l'extinció. Amb k = 0,40 i el cel adoptat queda en +0,040 / +0,008 / −0,013 / −0,021 / −0,042 / −0,092 (anells de 2,4–2,6 a 4,5–5,5 R☉).

**Color.** El color G/R de la corona també té un dipol cap al zenit. L'anàlisi es va fer després de veure les dades. És compatible amb una k diferent per canal: k_verd − k_vermell ≈ 0,16–0,19. La dispersió atmosfèrica (1,4″, uns 0,65 px entre el verd i el vermell) en fa el 20–26 %; si es treu, ≈ 0,13–0,14. No és una mesura de k per canal.

**Corregit:** al mapa MSB (`MSB/v2/mapa/msb_mapa_2x2_v2.fits`), píxel a píxel, referit a la massa d'aire del punt zero. A la imatge, no: és decisió de Pere (vegeu «Pendent»).

**Detall:** `MSB/v2/mapa/RESULTAT_mapa_v2.md` §1; `MSB/v2/mapa/dipol_c2/DIPOL_C2_v2.json`; `MSB/v2/CORRECCIONS_v3.md`, punts 1 i 4.

## 2. El cel portava corona, i el pla s'empassava part del dipol

**Què fèiem** (nota 76 §5.3, comparació de l'01-10 i mapa v1 de l'11-10):
- una constant: la mediana de la imatge a r > 7,2–7,3 R☉;
- més un pla ajustat al residu a r > 3,5 R☉, sobre dades sense corregir l'extinció.
- La nota 76 ho justificava així: «un pla no pot absorbir una corona radialment simètrica». Des de terra, la corona no és simètrica: porta el dipol de la secció 1.

**2a. La constant porta corona K+F.** Entre 7 i 13 R☉ encara hi ha corona. Passant el model de van de Hulst (1950) pel mateix estimador:
- el cel surt +7,0 ADU/s massa alt al centre (1,94 × 10⁻¹⁰ B☉; les variants del model donen ×0,73 a ×1,31);
- la corona queda massa baixa un 0,8 % a 2 R☉, un **3,9 %** a 3, un **9,1 %** a 4 i un **16,5 %** a 5 R☉ (el verificador: 3,85 / 8,99 / 16,4).
- És un biaix d'un sol sentit i surt d'un model. No es corregeix: es declara (pla SKY_BIAS del FITS).
- S'ha calculat per als cels de l'11–12-10 (constant: +6,95 ADU/s; pla nou: +7,0). La nota 76 i l'01-10 feien servir el mateix tipus de constant. Suposició, no calculada: hi tenien un biaix del mateix ordre.

**2b. El pla s'empassava part del dipol.** Amb el mateix model, atenuat per l'extinció:
- pla vell (residu a r > 3,5 R☉): gradient vertical −4,12 ADU/s per R☉, del qual −0,79 (un 19 %) era corona, sobretot el seu dipol d'extinció;
- pla nou (ajustat directament a r ≥ 8 R☉): −3,74 ± 0,36, del qual −0,37 (un 10 %) era corona; el dipol sol hi fa −0,42;
- un cop treta aquesta part, els dos coincideixen (−3,37 i −3,32). El gradient és sobretot del cel o de llum difusa: 0,85 % per R☉ cap a PA 25°.
- **Conseqüència:** el cel i k es confonen.
  - Amb un cel constant, el dipol del C2 només s'anul·laria amb k ≈ 0,57–0,63 a 2,4–3,3 R☉, i amb cap k únic més enfora.
  - L'ajust conjunt predeclarat de cel i corona és degenerat (correlació −0,9998).
  - Per tant, el dipol del C2 és una prova de coherència condicionada al pla del cel. No és una mesura independent de k. El suport independent de k = 0,40 és el de la nota 78.

**El cel mana fora de 3 R☉.**
- Del mapa v1 al v2, la corona puja un 6 / 15 / 31 % a 3 / 4 / 5 R☉. Gairebé tot ve del cel, que baixa 9,15 ADU/s; la resta és l'1,1 % de la referència de l'extinció (secció 7).
- La incertesa sistemàtica hi és de −28,5 / +23,3 %, −50,7 / +48,4 % i −87,5 / +86,3 %.
- A r ≥ 8 R☉ el cel fa, a més, una cúpula de +32 ADU/s al centre respecte del pla. Causa no resolta.

**Corregit:** cel nou (constant + pla a r ≥ 8 R☉), triat amb una regla escrita abans de cap quocient amb el C2 (`MSB/v2/mapa/PREDECLARACIO_CEL_v2.md`). Biaix declarat. Dipol donat per a tots els cels.

**Lliçó:** el pla del cel es mesura on la corona no hi pesa. I el dipol es dona per a tots els cels, no només per a l'adoptat.

**Detall:** `MSB/v2/mapa/RESULTAT_mapa_v2.md` §1, §2 i §5; `MSB/v2/mapa/cel/CEL_v2.json`; `MSB/v2/mapa/dipol_c2/K_I_PLA_posthoc.json`.

## 3. La comparació amb el K-Cor de l'01-10

**Què fèiem** (`3-RECERCA/resultats/comparacio_sdo_lasco_20261001/RESULTAT.md`, `c9_brillantor.py`):
- Dividíem el pB del K-Cor pel grau de polarització de Thomson (pB/p). Això és només la corona K. La nostra foto és K+F, i la F no es restava.
- El pB sortia de la GIF pública (8 bits, «Intensity^0,8»). Era la mitjana de 2 min de les 18:29:32, que acaba després del C3.
- L'anell 1,10–1,15 R☉ queia dins la franja del moviment lunar: la vora de la franja va d'1,091 a 1,155 R☉ segons l'angle. Amb la regla d'ara (fora tota casella que toqui un píxel de franja), en queden 54 de 360.
- Resultat d'aleshores: la foto, un 12,8–14,5 % per sobre. Abans de la revisió de Codex, la nota 180 deia «dins del 2–11 %» i que el calibratge «queda validat per un instrument independent».

**Què hem trobat:**
- La F és el 10 / 11 / 19 % de la nostra brillantor a 1,15–1,25 / 1,25–1,40 / 1,40–1,70 R☉.
- La GIF sobreestimava el pB un 2,3–2,7 % a 1,10–1,40 R☉. Més enllà d'1,4 R☉ no serveix.
- A 1,15–1,25 R☉ el quocient fa aquest camí: 1,13 (01-10) → 1,14 (mapa nou) → 1,17 (FITS en lloc de GIF) → **1,05** (restant la F). L'excés el fa, sobretot, la corona F que no es restava (segons el model de van de Hulst). La GIF anava en sentit contrari.
- Les unitats del K-Cor (brillantor mitjana del disc) ara estan comprovades a la capçalera. L'01-10 les suposava.

**Valor corregit** (7 fotogrames de nivell 2 dins la totalitat; densitat de Baumbach–Allen i F de van de Hulst; amb extinció):
- quocient de medianes **1,06 / 1,06 / 1,12**; mediana dels quocients 1,10 / 1,10 / 1,19;
- amb tots els models (3 densitats, 2 corones F, F × 0,5–1,5, amb i sense extinció): 0,94–1,41;
- amb la nostra sistemàtica (−20 % / +11 %): 0,76–1,57. **Compatible.** No es pot dir «més alt».
- Avís: el pB de nivell 2 d'aquell dia és negatiu més enllà d'1,95 R☉. Si el mateix desplaçament hi fos a dins, els quocients baixarien a 1,01 / 0,98 / 0,89. Per això el K-Cor només s'usa fins a 1,7 R☉.

**Detall:** `MSB/v2/comparacions/RESULTAT_comparacions_v2.md` §A; el camí GIF → FITS, a `MSB/comparacions/RESULTAT_comparacions.md` §A; `MSB/v2/comparacions/kcor/KCOR_v2.json`.

## 4. El calibratge del LASCO C2

**Què fèiem** (01-10): només el calibratge de SolarSoft (`c2_calibrate.pro`, 6,562 × 10⁻¹²), sense la correcció d'exposició. Resultat: la foto menys el cel feia 1,2–1,8 vegades el C2 (medianes 1,2–1,5). La nota 180 deia que «l'excés creix amb el radi», i ho atribuïa a la llum difusa nostra, al calibratge del C2 «extrapolat fins al 2026» i al cel.

**Què hem trobat:**
- Colaninno i Howard (2015, eq. 8) donen 7,589 × 10⁻¹² per a aquell dia. SolarSoft queda un **13,5 % per sota**: amb Colaninno i Howard, el C2 surt un 15,7 % més brillant.
- La diferència ja era del 16,7 % el 2013, dins del període que van ajustar. No ve de cap extrapolació: és de nivell. Del 2013 al 2026, Colaninno i Howard només pugen un 2,5 %.
- L'ajust refet de la seva Taula 2 reprodueix l'eq. 8 (3,927 × 10⁻⁵ per dia; 5,20). Per al 2026 dona 7,61 ± 0,07.
- No hi ha un tercer calibratge per al 2026: Llebaria et al. (2021) no en dona cap xifra. El vinyetatge de Colaninno i Howard és, molt probablement, el mateix que fem servir. No s'ha pogut confirmar.
- La correcció d'exposició fa +0,06 i +0,09 %: negligible.

**Valor corregit** (cel nou, k = 0,40; quocient de medianes als anells de 2,4–2,6 a 4,5–5,5 R☉):
- Colaninno i Howard: **1,14 / 1,27 / 1,32 / 1,35 / 1,37 / 1,40** (mediana dels quocients, 1,12–1,33);
- SolarSoft: **1,32 / 1,47 / 1,53 / 1,57 / 1,58 / 1,62** (1,29–1,54).
- Amb el mateix criteri que el K-Cor: amb Colaninno i Howard, el quocient és dins de la nostra sistemàtica d'1σ a tots els anells. Amb SolarSoft, la supera només a 2,4–3,3 R☉.
- A 2,6–3,8 R☉ la pendent sense escala és 0,96–1,01: la diferència és de nivell, no de forma.
- L'«excés ×1,2–1,8» era, en part, la tria del calibratge. En part, una incertesa nostra massa estreta: ±10 %, quan a 3 R☉ és −28,5 / +23,3 %. Amb SolarSoft el quocient fins i tot puja, perquè el cel nou és més baix.
- La causa queda oberta: llum difusa nostra, el cel, el calibratge del C2 o la segona càmera (~+20 %, secció 5). El biaix del cel la faria créixer (fins a 1,63 amb Colaninno i Howard).

**Detall:** `MSB/v2/comparacions/RESULTAT_comparacions_v2.md` §B i §C; `MSB/v2/comparacions/lasco/LASCO_v2.json`; `MSB/v2/CORRECCIONS_v3.md`, punt 3.

## 5. El punt zero i les dues càmeres

**Què fèiem** (nota 75 §5.2): punt zero ±0,08 mag i factor ±10 % simètric. R6/Sony = 0,95 a la corona: «estem a un 5 %». El terme de color feia passar el quocient de 0,83 a 0,95, i es retirava la hipòtesi de llum difusa del 300 GM.

**Què hem trobat** (`MSB/zp_canal/`):
- El control verd es reprodueix bit a bit: ZP +14,2052 ± 0,040, factor 2,7714 × 10⁻¹¹, 14 estrelles. El valor no canvia. Canvia la incertesa.
- Bootstrap del factor verd (2.000 mostres): mediana −5,9 %; 68 % entre −16,7 % i −0,6 %; 95 % entre −22,7 % i +3,9 %. El valor adoptat queda per sobre del percentil 84.
- Les 7 estrelles que treu el retall queden totes per sobre de la recta (+0,29 a +0,73 mag). Sense retall, el factor baixa un 12,9 %.
- Terme de color: la permutació no el detecta. p = 0,18 (vermell), 0,23 (verd), 0,78 (blau) i 0,55 (Sony). Posar-lo o no mou el factor un 9,4 %.

**Valor corregit:**
- punt zero −16,7 % (bootstrap) / +2,0 % (error formal de l'ajust), més ±9,4 % del terme de color, a part;
- total dels termes constants: −19,8 % / +10,8 %. A 1,15–1,9 R☉, on només hi ha la Vixen: **−20 % / +11 %**;
- en queden fora la segona càmera, el halo i el biaix del cel.

**Les dues càmeres: obert.** Sobre els apilats V42, amb els dos factors, Vixen/Sony = **0,83** a 1,3–1,9 R☉ (0,82–0,83 fins a 4 R☉). La nota 75 donava 0,95 sobre fotogrames crus.
- El 0,95 depèn dels dos termes de color, i cap no és significatiu. Amb les medianes del bootstrap passaria a ~0,85. És indicatiu, no una mesura.
- Més enllà d'1,9 R☉ el mapa és Sony·ρ, calibrat a través de la Vixen. El punt zero propi de la Sony donaria ~+20 %. No és dins la banda sistemàtica.
- La llum difusa del 300 GM, doncs, no es pot donar per retirada. Altres candidats: el flat, la normalització per fotograma, el centre i la definició dels anells.

**Detall:** `MSB/zp_canal/RESULTAT_zp_canal.md` §6; `MSB/v2/mapa/RESULTAT_mapa_v2.md` §3.

## 6. Què continua valent

- **Estructura en angle** (nota 180 i `RESULTAT.md` de l'01-10, revisat): K-Cor 0,90–0,95 fins a 1,75 R☉ (0,74 a 1,75–1,98); C2 de 0,82 a 0,42 (2,4–6 R☉), i el detall fi de 0,88 a 0,58; SDO a 211 Å 0,87–0,89 (el K-Cor contra l'SDO fa 0,94–0,97). L'orientació, de −0,5° a +0,8° (fins a +9° al perfil sencer del C2 a 5–6 R☉). Les tres protuberàncies, a ull, són on les veu l'SDO a 304 Å.
  - Es va fer sense corregir l'extinció i no s'ha refet. Suposició, no mesurada: no baixaria. El detall < 12° no veu un dipol suau, i la correlació per caselles amb el C2 va pujar de 0,77–0,92 a 0,86–0,99 en corregir l'extinció.
  - El límit de la prova continua: compara angles. Una transformació a(r)·I + b(r) la passaria igual.
- **K-Cor:** acord dins de la incertesa (1,06–1,12).
- **Forma contra el C2:** correlació per caselles de 0,92–0,99 a 2,4–4,5 R☉ (0,83 a 4,5–5,5), i pendent sense escala de 0,96–1,01 a 2,6–3,8 R☉.
- **Punt zero:** el valor del 17-08 es reprodueix bit a bit. La rèplica de la Sony, també (1,1352 × 10⁻¹¹; 30 estrelles).
- **La cadena:** el mapa v2 reprodueix el perfil de la nota 76 (0,98 / 1,02 / 1,00 / 1,07 a 1,5 / 2 / 3 / 5 R☉). És coherència de la cadena, no una validació del calibratge.
- **El nivell del cel:** en verd de càmera, 1,22 × 10⁻⁸ B☉ (≈ 9,16 mag/arcsec²). Quadra amb els 9,15 de la nota 75. Les xifres de 0,78–1,08 × 10⁻⁸ de la 76, de l'01-10 i de la 180 eren d'una altra variable (lluminància): el cel és blau.

## 7. Errors més petits de la mateixa feina (ja corregits a la v2 i la v3)

- Referència de l'extinció: la v1 feia servir X = 6,053 (hora del mapa) en lloc de 6,024 (hora del punt zero). El mapa quedava un 1,1 % baix.
- Deriva de C2 a C3 per la massa d'aire: −6,8 %, no −7,3 %.
- La σ estadística del mapa no és una cota alta: els píxels veïns estan correlacionats (0,81 a 1 px).
- R/G de la corona: no és 0,77 ± 0,01. Segons l'estimador del punt zero vermell, va de 0,77 a 0,97.
- Figura de l'article: la banda d'un quocient a 1σ és [1/(1 + σ amunt), 1/(1 − σ avall)], de 0,90 a 1,25 a 1,15–1,9 R☉. La v2 dibuixava 0,80–1,11. Bona: `fig_msb_profile_v3` i `fig_msb_profile_v4` (mida d'impressió).
- El dipol sense corregir és de +0,17 a +0,28, no de +0,17 a +0,23.

**Detall:** `MSB/v2/mapa/CANVIS_v2.md`, `MSB/v2/comparacions/CANVIS_v2.md` i `MSB/v2/CORRECCIONS_v3.md`.

## Què queda superat a cada nota

| On | Deia | Ara |
|---|---|---|
| Nota 75 §5.2 (i el ±10 % del §6) | Factor ±10 % simètric. R6/Sony 0,95, «estem a un 5 %». Es retira la llum difusa del 300 GM. | −17 % / +2 %, i ±9,4 % del color; −20 % / +11 % a 1,15–1,9 R☉. Sobre els apilats, 0,83: obert. La llum difusa no es pot retirar. |
| Nota 76 §5.3 | Cel de 283 ADU/s i 1,2 % per R☉. «Un pla no pot absorbir una corona radialment simètrica.» | Des de terra la corona porta el dipol d'extinció. Un pla d'aquest tipus se n'empassava un 19 % (calculat per al pla de l'11-10). La constant porta K+F: la corona de fora surt un 4 / 9 / 16 % baixa (calculat per als cels de l'11–12-10; per a la 76, suposició del mateix ordre). En verd de càmera: 439 ADU/s, 0,85 % per R☉ cap a PA 25°, i una cúpula de +32 ADU/s. |
| Nota 180, «Brillantor absoluta» i capçalera de revisió | «Fita 6 PASSA»; K-Cor «dins del 2–11 %» i calibratge «validat» (revisat: +12,8–14,5 %); C2 1,24–1,5 (revisat: 1,2–1,8), «l'excés creix amb el radi», per llum difusa, C2 extrapolat i cel; cel 1,08 × 10⁻⁸ B☉. | K-Cor 1,06–1,12, compatible. C2 1,14–1,40 (Colaninno i Howard, dins d'1σ) o 1,32–1,62 (SolarSoft); causa oberta. Cel 1,22 × 10⁻⁸ B☉ en verd de càmera. |
| `3-RECERCA/resultats/comparacio_sdo_lasco_20261001/RESULTAT.md`, «Brillantor absoluta (v2)» | Lluminància (G + 0,566·R)/2, amb un pas Q que varia 1,03–1,21. Sense extinció diferencial. Cel a r76 > 7,2 i pla a r76 > 3,5. ±10 %. K-Cor de la GIF, sense restar la F i amb l'anell 1,10–1,15: +12,8–14,5 %. C2 només amb SolarSoft i sense correcció d'exposició: 1,2–1,8. | Verd de càmera per inversió exacta, sense pas Q. Extinció per píxel. Cel a r ≥ 8 R☉ i biaix declarat. −20 % / +11 %. K-Cor de FITS, amb la F i sense la franja: 1,06–1,12. C2 amb els dos calibratges i l'exposició. |

Les parts d'estructura de la nota 180 i del `RESULTAT.md` continuen valent (secció 6).

## Pendent

1. **Corregir l'extinció a la imatge, o no.** Decisió de Pere.
   - Si es fa, al pis on neix: el compost lineal (`fusion_total_v42`, restaurat el 12-10 a la cau b3), amb la massa d'aire per píxel. Després es refà tot el que hi ha a sobre (filtres i PSB). Mai una compensació del compost final.
   - Proposta: referir-la al centre del Sol (E = 1 allà). Així no canvia el color global. Sí que canvia el gradient de dalt a baix: −8 / +10 % a 1,5 R☉ i −19 / +30 % a 4 R☉ (zenit / horitzó, amb k = 0,40), i una mica el color si k depèn del canal.
   - Cap canvi de color sense un costat a costat abans. El daurat és de Pere.
2. **Funció a l'AEL.** L'AEL no té cap funció d'extinció diferencial: només el guany per fotograma de `ael/motion.py`. Proposta: massa d'aire per píxel (astropy, Kasten–Young, direcció del zenit) i factor E, amb proves. Push i versió, només amb el sí de Pere.
3. **Les dues càmeres** (0,83 contra 0,95). Fer el mapa MSB de la Sony sola, amb el seu factor, al mateix llenç.
4. **Halo i llum difusa** de la nostra òptica: sense model (G3 obert). Hi poden tenir a veure la cúpula del cel i la diferència amb el C2.
5. **k per canal i k independent del cel.** Refer la fotometria d'estrelles amb el mateix flat del compost. Explicar la tendència del dipol residual amb el radi (de +0,04 a −0,09; amb les σ del cel adoptat, χ² ≈ 14 per a 6 anells, segons el re-verificador) i la component perpendicular al zenit (+0,04 a +0,12 fora de 3,3 R☉).
6. **Menors.** El pB negatiu del K-Cor (preguntar-ho a l'MLSO, amb el sí de Pere). Confirmar el vinyetatge de Colaninno i Howard.

**Fonts d'aquesta nota:** `MSB/v2/mapa/RESULTAT_mapa_v2.md`, `MSB/v2/comparacions/RESULTAT_comparacions_v2.md`, `MSB/v2/CORRECCIONS_v3.md`, `MSB/zp_canal/RESULTAT_zp_canal.md`, `MSB/comparacions/RESULTAT_comparacions.md`, i els informes dels agents i verificadors, copiats sense canvis a `MSB/v2/verificacions_rev10/` (`scout.json`, `calcul.json` i `fixes.json`). Codi: `3-RECERCA/tools/msb_calibrat_20261011/`.

---

## Annex (12-10, tarda): el que s'ha fet dels pendents 1 i 2
- **Costat a costat per a Pere** (pendent 1, la decisió encara és seva): `4-Photoshop/Sortides/extincio_diferencial_20261012/`. Cal llegir el `LLEGEIX-ME_v2.md`. El codi és a `3-RECERCA/tools/extincio_diferencial_20261012/` i els resultats a `3-RECERCA/resultats/extincio_diferencial_20261012/`.
  - **Pis 1, el compost lineal**, on neix el defecte: amb la correcció, la diferència de brillantor entre el zenit i l'horitzó es redueix i a 3–4 R☉ gairebé s'iguala.
  - **Pis 2, la V125-FINAL:** és una aproximació visual, no una cura. El canvi és de −7 % i +7 % a 1,5 R☉, i menor a fora, on la final té la corona a prop del seu fons segons el cel estimat.
  - **Color:** el to de la corona no canvia, perquè la correcció és acromàtica; el de la barreja amb el cel, una mica. La part cromàtica no s'ha aplicat.
- **AEL** (pendent 2): branca local `claude/extincio-diferencial-20261012` del repositori `3-AEL/repo`, amb els commits 49a7460, f1b7354 i 3a31ceb.
  - Mòdul `ael/extinction.py` i ordre `ael extinction`.
  - 47 de 47 proves bé, entre elles les de veritat coneguda i les negatives (cel ajustat sense corregir, cel constant amb corona).
  - Verificada amb mutacions.
  - No s'ha pujat ni fusionat amb `main`: espera el sí de Pere.

*[Afegit en publicar-la a l'AEL 1.3.0 (13-10-2026): la funció d'extinció i la comparació amb els coronògrafs ja són a la llibreria (`ael.extinction`, `ael.coronagraph`).]*
