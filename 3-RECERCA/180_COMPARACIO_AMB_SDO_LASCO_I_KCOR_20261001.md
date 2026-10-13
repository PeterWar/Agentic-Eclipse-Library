# 180 · La final contra SDO/AIA, SOHO/LASCO i K-Cor: validació externa de l'estructura (01-10-2026)

**Origen:** un suggeriment rebut: comparar la imatge amb la de l'SDO, per veure la fidelitat del tractament, i amb SOHO/LASCO. *[Editat per a la publicació: sense el nom ni les paraules d'un missatge privat.]* Feia de model un mosaic publicat: l'eclipsi al centre, el LASCO C2 en vermell i el C3 en blau.

**Antecedent:** és la porta G7c del `research/74` («LASCO no comparteix res» amb els nostres dos trens), proposada el 15-08 i mai feta fins avui. La part de brillantor absoluta («Fita 6») continua pendent.

## ⚠️ Revisió de Codex (GPT-6 Astra, xhigh, 01-10 tarda): PARCIAL, corregida

- **Errors trobats:**
  1. `polar()` tractava com a perpendiculars els eixos d'una placa afí (90,43°). Les capes superposades quedaven desplaçades fins a 3,3 px al limbe i 19,9 px a 6 R☉. Les correlacions no en quedaven afectades: feien servir `px()`.
  2. La transferència de brillantor feia servir R☉ = 946,66″ contra els 959″ del `research/76`, i la brillantor quedava un 6 % baixa.
  3. Les pendents absorbien el gradient del cel, i hi havia medianes sobre suports diferents.
  4. La redacció anava més enllà del que proven les dades.
- **Tot corregit:** detall a `3-RECERCA/resultats/comparacio_sdo_lasco_20261001/REVISIO_CODEX_20261001.md`.
- **Les xifres de brillantor de sota** són les de la v1. Les vigents són a l'informe:
  - K-Cor: +12,8–14,5 % en medianes (+3–19 % segons les pendents);
  - C2: 1,2–1,8 vegades;
  - provisional, pendent d'un pressupost complet d'incerteses.
- **Segona ronda:**
  - la graella del PSB es dibuixa amb el·lipses del marc afí → `V125-FINAL_comparacio_v3.psb`;
  - corbes aparellades;
  - sensibilitat de Q al cel < 0,1 %;
  - 8 frases del PDF precisades: desplaçaments del màxim de correlació en lloc d'«encaix», protuberàncies «a ull», correlacions que acrediten coincidència angular i no exclouen artefactes locals.
- **Límit de la prova d'estructura:** compara angles. Una corba de to radial a(r)·I + b(r) la passaria igual.

## Resultat en una frase

Sense ajustar cap paràmetre amb els satèl·lits, l'estructura de la final coincideix amb la dels tres instruments:
- amb el K-Cor (1,1–2 R☉), una correlació d'angle de 0,90–0,95;
- amb el LASCO C2 (2,4–6 R☉), de 0,82 a 0,42, i el detall fi de 0,88 a 0,58;
- amb l'SDO a 211 Å, 0,87–0,89, quan el K-Cor contra l'SDO fa 0,94–0,97;
- l'orientació hi coincideix dins de ~0,5°;
- les tres protuberàncies són on les veu l'SDO a 304 Å.

Detall, taules, límits i fitxers: `3-RECERCA/resultats/comparacio_sdo_lasco_20261001/RESULTAT.md`.

## Mètode, per reutilitzar-lo

1. **Geometria de la final, independent dels satèl·lits:**
   - centre del Sol = centre de la Lluna mesurat − desplaçament de la DE421 (topocèntric, instant LOLA 18:28:49 UT);
   - nord celeste per les estrelles;
   - P de sunpy (15,191°).
   - ⚠️ El centre de la placa d'estrelles portat a la V120 queda 4,5 px més amunt. El llenç segueix la geometria de la Vixen; per a la corona, fes servir el de l'efemèride.
2. **Cada instrument en coordenades solars pròpies:** r en R☉ del seu observador i PA des del nord solar. El SOHO, a L1, veu R☉ = 957,22″, un 1,12 % més gran que des de la Terra. `comu_comp.Geo` fa la transformació de les dues bandes.
3. **Perfils d'angle per anells:**
   - NRGF per radi a cada imatge, mitjana de l'anell, suavitzat σ 1,5°;
   - Pearson a gir 0 i gir òptim;
   - control nul amb 151 girs a l'atzar (30–330°);
   - també el detall < 12° (passa-alt en angle): els perfils sencers tenen nuls amples per la forma bipolar de la corona.
4. **Protuberàncies:**
   - l'AIA 304 remostrejat al marc de la final;
   - contorns fora del disc i fora de la Lluna;
   - encaix per correlació en cartesià i per sectors.

## Trampes trobades

- **Pilar del LASCO:** és el tram contigu de PA ~288–356°. Un llindar global s'enduu forats coronals reals.
- **El LASCO de nivell 0,5 no es pot ensenyar amb un NRGF:** la corona F té forma d'angle. Cal treure els harmònics m ≤ 3 al C2, amb el vinyetatge de `c2vig_final.fts` (multiplicatiu).
  - El C3, sense el fons mensual, no queda net ni amb m ≤ 12.
- **Les GIF del K-Cor:** el cercle de punts «circle = photosphere» té radis diferents a les NRGF (127,79 px, ±2,0 R☉) i a les pB (170,39 px, ±1,5 R☉). Cal treure'n els rètols de les cantonades.
- **`sunpy` amb el LASCO de nivell 0,5:** posa l'observador a la Terra. Cal corregir R☉ amb la posició del SOHO (JPL Horizons).

## Brillantor absoluta (01-10, tarda): la «Fita 6» del `research/74` PASSA

- **Mètode:**
  - la nostra brillantor surt de `fusion_total_v42` (G), passada a ADU/s pel perfil absolut de `research/76` a 1,5 R☉ (1,198 unitats per ADU/s) i a B/B☉ amb el factor de `research/75`;
  - el C2 es calibra amb `c2_calibrate.pro` (calfac 6,562 × 10⁻¹² per a l'MJD 61264,77);
  - el K-Cor és el pB de la GIF.
- **Regressió per anells:** fotografia = pendent × instrument + fons. La pendent no depèn del cel.
- **K-Cor (1,1–1,4 R☉):** coincideix dins del **2–11 %**, si es divideix pel grau de polarització de Thomson (0,33 → 0,45).
  - El nostre calibratge del 16-08 queda validat per un instrument independent.
- **LASCO C2 (2,4–5,5 R☉):** la fotografia, sense el cel, fa **1,24–1,5 vegades** el C2 (pendent 1,40 ± 0,17 a 2,4–2,9 R☉).
  - És dins del factor 2.
  - L'excés creix amb el radi: deu ser la llum difusa nostra (G3 obert), el calibratge del C2 extrapolat fins al 2026 i el cel.
- **Cel de l'eclipsi:** 1,08 × 10⁻⁸ B☉ (≈ 9,3 mag/arcsec²), igual que el del `research/75`.
- Codi: `c9_brillantor.py` i `c10_figura_brillantor.py`; figura `FC_brillantor_absoluta.png`.

## PSB per comparar (01-10, tarda)

`1-PHOTOSHOP/V125-FINAL_comparacio.psb`: la V125-FINAL de Pere, intacta (49 capes byte a byte), més 6 capes ocultes:
- K-Cor;
- LASCO C2;
- SDO 304 Å;
- SDO 211·193·171 Å;
- contorns del 304 Å;
- graella solar.

Rebut al costat.

## Pendent

- **C3 net:** cal el fons mensual oficial de la NRL o les vistes processades de la NRL. Caldria una baixada nova, amb permís.
- **Separar el halo de l'excés exterior:** es podria fer amb el model de halo validat a la fase parcial (G3), si mai es fa.
- Les FITS de nivell 2 del K-Cor no són a la carpeta pública del dia: només hi ha GIF.
