# Màsters flat posteriors Vixen i Sony — 22-08-2026

## Resposta curta

Sí, els flats aporten material útil, però no es pot usar un únic flat complet
per tren.

- **Vixen:** el PRNU fi del sensor és real, estable i transferible malgrat la
  rotació. La vinyeta radial és candidata de pilot. Camp 2-D, pols i flat
  complet queden en quarantena.
- **Sony 300 mm:** el perfil òptic radial és vàlid i confirma gairebé
  exactament el flat donant S6. El PRNU fi té senyal, però no supera la porta
  de repetibilitat; camp complet i pols queden en quarantena pels deu dies i el
  transport.

No s'ha recalibrat ni sobreescrit cap màster S6.

## Inventari i identitat

### Vixen / Canon EOS R6 Mark III

- 125 CR3 independents, `572A7121–572A7245`, 4.056.003.972 bytes.
- Cos `[SÈRIE]`, sèrie interna `[SÈRIE]`, ISO 100.
- Exposicions: 18×1/320, 83×1/100, 2×1/40 i 22×1/25.
- 27–32 °C, 20:26:06–20:27:42 +02.
- L'EXIF no identifica el telescopi; per això la identitat òptica Vixen és
  contextual, no demostrada per metadades.

### Sony A7RIIIA / FE 300 mm f/2,8 GM

- 53 ARW independents, `DSC00067–DSC00119`, 4.526.773.248 bytes.
- Sèrie interna `[SÈRIE]`, 300 mm, f/2,8, ISO 100, 1/200 s.
- 28–29 °C, 20:29:55–20:31:39 +02.
- Cos, objectiu, focal, obertura, ISO, RAW, enfocament a infinit, OSS i
  obturador coincideixen amb `DSC06987.ARW` de l'eclipsi.

Les 52 còpies ARW Sony dins `Flats R6III` són byte-idèntiques i no compten com
mostres. Els dos màsters consumeixen 125+53 RAW únics.

## Construcció

Eina: `research/tools/flat_field_20260822/build_master_flats.py`.

- CFA lineal RGGB, plans `R,G1,G2,B`, sense AHD, WB, denoise ni clip tonal.
- Canon sobre la reixa S6 4640×6960 i pedestal físic 511,5; no s'usa el black
  fals `[0,32,96,64]` de LibRaw.
- Sony sobre 5320×7968 i black 512.
- Normalització robusta separada per frame i pla en un anell central simètric.
- Mitjana ponderada pel senyal i rebuig per píxel a 5,5 sigma.
- Splits odd/even, quatre blocs temporals, cobertura, N efectiu, variància
  aleatòria i proxy sistemàtic del split.
- Separació multiplicativa en log: full, 180-even, radial, 2-D suau i PRNU fi.
- FITS mosaic RGGB i NPY CFA4, rebuts d'entrada i SHA-256 complets.

Resultat:

- Vixen: 125/125 acceptats; cobertura 125 a tots els píxels.
- Sony: 53/53 acceptats; cobertura mediana 53 i mínima 52.
- 44 fitxers, 4.427.625.357 bytes al paquet global.

## Transferència mesurada

Rebut decidible:
`output/flats_20260822/transfer_assessment_v1/TRANSFER_ASSESSMENT.json`.

### Vixen

El nou `FINE_SENSOR` coincideix amb el PRNU v2 mesurat durant l'eclipsi:

| Pla | r directe | r amb high-pass comú |
|---|---:|---:|
| R | 0,8686 | 0,8937 |
| G1 | 0,8906 | 0,9208 |
| G2 | 0,8915 | 0,9212 |
| B | 0,8889 | 0,9121 |

Els splits del nou flat donen r=0,978–0,986, per damunt de la porta 0,8. Un
null conservador sobre `572A2969`, `2987`, `2999` i `3005`, quatre RAW 1/125
que no van construir el PRNU antic, redueix l'RMS 0,40%, 2,22%, 2,21% i 0,44%
en R/G1/G2/B. L'antic mapa empitjora aquest mateix null 1,9–5,4%.

Per tant `FINE_SENSOR` és **VALIDATED_COMPONENT_NOT_APPLIED**. La rotació no
l'afecta perquè viu en coordenades del sensor. El camp complet té asimetria
logarítmica RMS 2,10%, massa alta per al pressupost 0,5%, i queda en
`QUARANTINE_ROTATION_AND_ASYMMETRY`.

La component radial cau aproximadament a 0,89–0,91 al cantó i és invariant a
rotació, però encara exigeix un pilot sobre RAW coronals abans de promoció.

### Sony

El nou `OPTICAL_RADIAL` i el flat òptic donant S6 tenen correlació de camp log
0,9999957–0,9999972. La discrepància absoluta p95 és:

| Pla | p95 | cantó nou | cantó donant |
|---|---:|---:|---:|
| R | 0,548% | 0,3624 | 0,3617 |
| G1 | 0,267% | 0,3689 | 0,3748 |
| G2 | 0,269% | 0,3690 | 0,3748 |
| B | 0,157% | 0,3688 | 0,3757 |

Això passa les portes r≥0,999 i p95≤0,6%. El perfil òptic és
**VALIDATED_COMPONENT_NOT_APPLIED**: el transport i els deu dies no l'han
desquadrat de manera material.

El camp complet té asimetria RMS 2,78% i queda en quarantena. Els splits del
PRNU fi Sony només donen r=0,192/0,522/0,524/0,354. El shrink evita
sobrecorrecció i el null independent millora lleument, però no arriba a r≥0,8:
`FINE_SENSOR` continua `QUARANTINE_SPLIT_R_BELOW_0.8`.

## JPEG retirats

Per ordre de Pere s'han mogut, no destruït, 106 JPEG de flats, 83.361.792
bytes, al lot recuperable:

`/Users/USUARI/.Trash/Flats_JPEG_Eclipse_2026_20260822T190159Z`

Queden zero JPEG/JPG a les dues carpetes de flats. Els 230 camins RAW presents
abans i després conserven el mateix fingerprint de l'operació
`162e4573554dc6add4726b69d8df1a94fbce7f66cc8d2aa729fa88d03eeef4e3`.
La Paperera no s'ha buidat. Rebut:
`output/flats_20260822/JPEG_CLEANUP_RECEIPT.json`.

## DEMOSTRAT / FALTA / ORDRE DE GATES

### DEMOSTRAT

- Els dos lots són lineals, no saturats i repetibles; 178/178 RAW únics
  acceptats.
- El PRNU Vixen nou transfereix entre èpoques i millora RAW independents.
- El perfil radial Sony nou reprodueix l'autoritat òptica vigent dins 0,6% p95.
- Originals, S6 i càmeres no han estat modificats.

### FALTA

- Promoure o descartar la radial Vixen sobre una recalibració RAW controlada.
- Fer el pilot Sony exact-body contra el donor a través dels mateixos warps.
- No hi ha evidència per transferir pols, camp 2-D complet ni PRNU Sony com a
  autoritat.

### ORDRE DE GATES

1. Congelar els S6 vigents com a control.
2. Recalibrar RAW originals en outputs nous; mai dividir un S6 ja registrat.
3. Vixen: control actual, radial nova, PRNU nou reemplaçant l'antic i full com
   a control negatiu.
4. Sony: donor actual, radial nova, radial+fine Wiener i full com a control
   negatiu; A i C continuen separats.
5. Promoure només si disminueix el patró fix sense anells ≥1%, canvis coherents
   >0,5%, pèrdua de PSF o empitjorament dels nulls S6.

## Rebuts principals

- Vixen `MASTER_FLAT_RECEIPT.json`: SHA-256
  `7a61ccd802f46032f053a663fd4977a943e4d6c34f92f12bb13dc86a17eb073d`.
- Sony `MASTER_FLAT_RECEIPT.json`: SHA-256
  `84488a5160ffa1491aad0e229ee3a4660608def93acbfbc582b6fa1f70f319e0`.
- `TRANSFER_ASSESSMENT.json`: SHA-256
  `09b561965c3e18e3c4b5b0747f8d274841f0d720497251128794489cd4ae06cf`.
- Rebut JPEG: SHA-256
  `3b4ddae2fa4639a56dd6f0641c05216747c7a7f779488847c72832056085b846`.

