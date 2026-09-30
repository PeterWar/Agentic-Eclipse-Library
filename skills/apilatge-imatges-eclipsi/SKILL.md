---
name: apilatge-imatges-eclipsi
description: >-
  Calibració i apilatge lineal dels RAW CR3/ARW de l'eclipsi: Vixen R6 III, Sony 300 mm, darks, flats, flats invertits, pedestal, saturació, PRNU, linealitat, soroll, pesos, variància i cobertura. Usa-la per revisar o reproduir les fases 0–2 de cadena.py i les fonts lunars posteriors. Distingeix la cadena base dels productors V56/V68; la reconstrucció completa RAW→PSB encara no està demostrada. Contracte general a postprocessat-corona.
---

# Apilatge d'imatges de l'eclipsi

Estat: 15-09-2026. Aquesta skill ja no és un orquestrador. La calibració, el
registre i la composició LDIC els fa
`3-RECERCA/tools/eclipse_determinista/cadena.py` (fases 0, 1 i 2), amb runs
immutables a `2-ARXIU/reconstruccio_compactacio_20260915/neteja_20260916/eclipse_determinista_docs/1-RUNS/` i manifest amb SHA-256.
Llegeix `.claude/skills/postprocessat-corona/SKILL.md` §0 a §2 i
`references/normes_i_portes.md` d'aquella skill: són el contracte viu.

**Abast actual:** fases 0–2 de la base històrica, no reconstrucció completa
de V68/V56. Per al mapa posterior i les entrades manuals, llegeix
`../postprocessat-corona/references/estat_i_reproductibilitat.md`.
El reapilat lunar de 88 RAW de setembre té un productor separat:
`3-RECERCA/tools/earthshine_max_detail_20260913/a1_native_rgb.py --all`.
Llegeix els seus inputs abans d'executar-lo: usa calibradors dels runs 019/016,
geometria/camps congelats i comprovacions contra fonts anteriors. No el llancis
amb un claim històric ni sobre la carpeta existent; el wrapper ha de separar
lectures i sortides noves. La seva variància és condicional i no inclou tota
la incertesa compartida dels màsters.

**Prova F0 del 15-09:** dues reconstruccions per tren, 56/56 FITS i rebuts
exactes. **F1/F2 també repetides dues vegades per tren:** 52/52 FITS exactes
als històrics, 26/26 entre rondes i 20 JSON amb dades històriques exactes.
Dither Sony aplicat, no reestimat; RAW→PSB complet pendent. Resultat/recepta:
`2-ARXIU/reconstruccio_compactacio_20260915/raw_replay/RESULTAT_F12.md`.


V29 mostres/confiança i ajustos additius també repetits des de RAW amb els F0/F12 nous: 8/8 NPY exactes als històrics, 4/4 entre rondes; tots els JSON exactes en dades. Matriu V27 declarada, no reestimada. OpenCV 6 segons aquest productor. Prova: `2-ARXIU/reconstruccio_compactacio_20260915/raw_replay/RESULTAT_OFFSETS.md`.

## Què fa la cadena a les fases 0 a 2 (i on)

- `f0.py`: pedestal mesurat (marge emmascarat a la Vixen, darks a la Sony;
  mai el negre de libraw), màsters de dark per exposició, flat radial amb la
  porta dels flats invertits (≤ 8 %) o del dither del salt de muntura
  (`flat_dither_SONY.json`, `3-RECERCA/tools/sony_entrada/flat_pel_salt.py`).
  El flat sempre abans de qualsevol warp.
- `f1.py`: centre del Sol per efemèride, llenç comú declarat, segments
  d'apuntament, registre fi per correlació de fase.
  ⛔ **Deute (29-09-2026, norma obligatòria de Pere):** cada tren entra al llenç
  només amb escala, angle de posició i translació. **Falta el model de
  distorsió de cada òptica.** Resultat mesurat: la Vixen difereix de la Sony
  3–7 px a les estrelles i fins a 0,25° als raigs, amb un patró que canvia amb
  l'angle. A la fusió (pes de la Vixen del 35–87 % entre 2 i 6 R☉) el detall
  surt desdoblat. **Amb més d'una òptica, cal corregir la distorsió de cada tren
  ABANS de fusionar**, amb la porta de la regla 9 de `postprocessat-corona`.
  El 2027, a més, cal fer camps d'estrelles de calibratge de la distorsió
  amb cada òptica (vegeu el protocol de captura).
  **Com es va resoldre el 2026 (V120, 30-09):** DESPRÉS de l'apilat, i no a
  `f1.py`. La Sony es va deformar a la geometria de la Vixen amb un camp: afí per
  estrelles + correcció tangencial per raigs, esvaïda a la vora del marc
  (`3-RECERCA/tools/v120_20260929/camp_v120.py`, `f5_warp_sony.py`). Amb les
  estrelles de la Sony, el rms va baixar de 8,4 a 0,9–1,5 px, i els raigs, a 0,2–0,4 px.
  El deute de `f1.py` continua obert per a un apilat nou.
- `f2.py`: una sola suma ponderada g = Σ w k f / Σ w amb sostre 0,85 i terra
  12 DN, màscara lunar per fotograma, coherència per fotograma dins de
  [1/2, 2], cel separat pel color. N i D es desen per canal. Mai apilar per
  exposició i després fusionar.

Constants per tren a `comu.TRENS`: escala, pa_north, radi solar del dia,
pedestal, saturació, font del pedestal, fotogrames de contacte, flat_dither.
Un tren nou entra escrivint-hi; és el millor detector de constants a mà.

## Normes que manen aquí

- RGGB a cada resultat (Pere, 26-08, error recurrent): R/G i B/G d'una zona
  coneguda al rebut; balanç de dia a cada producte des dels RAW; G1 i G2 són
  dos plans; cap mitjana sobre el mosaic cru.
- Flats del mateix dia o dither (31-08): la pols del sensor es mou; els flats
  del 22-08 no porten la mota del R6 (correlació 0,00).
- El soroll d'un component mai només per diferències entre germans (31-08).
- Els RAW, darks i flats són immutables; `0-ENTRADES/` només es llegeix.
- Cap intèrpret escrit a pèl: `scripts/comprova_entorn.py --python`.

## Deutes de la cadena base 0–2 (no extrapolar als productors de setembre)

- Temps d'exposició nominals de l'EXIF, no els físics del MakerNote
  (3-RECERCA/99 §2: fins a −6,25 %); la coherència per fotograma els absorbeix
  només com a escalar.
- Darks per mediana sense selecció de temperatura; el màster de 10 s torna
  a portar el pedestal a 511,0 a la zona activa (3-RECERCA/75 §1.1 demana
  mitjana i finestra de temperatura; `3-RECERCA/tools/masters_vixen_v2.py` ho fa
  fora de la cadena).
- Variància per canal no desada ni propagada (només `PES_c`).
- Cap drizzle: re-mostreig bilineal dels subplans (l'antic
  `3-RECERCA/tools/hdr_corona_vixen.py` en feia amb gota 2,0).
- Cap meitats A/B dins de la cadena.

## Soroll i denoise: PROPOSTA de recerca futura

Per ordre de Pere del 21-08 (3-RECERCA/87 §11.5): «per futurs projectes
d'eclipse sí que val la pena fer les reformes de soroll i denoise; apunta-ho
com a recerca futura però ara no és el moment». Els criteris de
`references/criteris_snr_i_apilatge.md` (cap llindar universal, admissió per
contribució mesurada, meitats A/B, covariància espacial) es conserven com a
proposta per al 2027, no com a norma vigent. Els números mesurats que hi
han de sobreviure: guany R6 5,08 e⁻/ADU (B 4,33, anòmal), RN 2,72 i 1,05 ADU
segons el mode de lectura, Sony 3,41 e⁻/ADU i 1,22 ADU (3-RECERCA/75 §3).

## Història (no executar com a cadena viva)

- `scripts/pipeline_vixen.sh` i `references/pipeline_vixen.md`: la cadena
  del 17-08 (masters_vixen_v2 → prnu_vixen → hdr_corona_vixen → apila_hdr4).
  Els seus productes porten R☉ 959 ″ en lloc del 947,068 ″ del dia i una
  correcció d'exposició al revés (3-RECERCA/99 §21). Conserva tres peces que la
  cadena no té i que el 2027 hauria de recuperar: darks per temperatura amb
  mitjana retallada, PRNU amb estrelles emmascarades i drizzle amb gota 2,0.
- `--prova DIR` d'aquell orquestrador no protegeix els màsters ni el PRNU
  (3-RECERCA/87 §5).

## Referències

- `scripts/comprova_entorn.py`: detecció de l'intèrpret i de les dades, només
  lectura. És l'única peça d'aquesta skill que continua viva.
- `references/criteris_snr_i_apilatge.md`: proposta de criteris de SNR.
- `references/pipeline_vixen.md`: la cadena del 17-08, història.
- `3-RECERCA/75`, `78`, `85`, `99`, `100`, `115`, `116`: evidència.


## Nota del 16-09-2026 (neteja profunda)

Per ordre de Pere s'han retirat a la Paperera els ràsters intermedis (output d'agost i setembre,
`3-RECERCA/tools/*/cau` i staging, replays, RAW copiats a `0-ENTRADES`, runs 005–018, PSB
supersedits del Desktop i Derivats). Els rebuts JSON, notes, codi i vistes es conserven i cada
carpeta afectada té `LLEGEIX-ME_NETEJA_20260916.md`. Les rutes citades en aquesta skill que ja no
existeixen es resolen amb `2-ARXIU/reconstruccio_compactacio_20260915/neteja_20260916/MOVIMENTS_<lot>.jsonl`.
Lliçons consolidades: `../postprocessat-corona/references/llicons_consolidades.md`.
