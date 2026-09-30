# Criteris de SNR i apilatge per a l'eclipsi 2026

## Abast

Aplica aquests criteris a captures que encara no s'han convertit en un màster
lineal. No els reexecutis sobre un stack que Pere hagi declarat validat quan la
tasca actual sigui composició Photoshop.

## Decisions que no s'han d'improvisar

- **Sense llindar universal.** Una desviació estàndard única no decideix si un
  fotograma entra. Compara la variància final amb i sense la presa, la
  cobertura que aporta i el residu estructurat.
- **Repetició no és duplicació.** Preses independents amb la mateixa exposició
  s'apilen. Un fitxer byte-idèntic comptat dues vegades s'exclou.
- **Denoise no és calibratge.** Mesura, selecciona i apila sense denoise. Si
  després se'n fa un derivat visual, conserva el control lineal i la
  diferència; no reivindiquis més fotons ni SNR científic.
- **Linealitat local.** Avalua per canal i regió sobre dades lineals. El 85 %
  és, com a màxim, un sostre específic validat per detector i revelador; no és
  un objectiu d'histograma.
- **Sistemàtica no és soroll aleatori.** Calima, gradient de cel, ghost,
  vinyetatge, flat residual, PRNU, patró de lectura o mala alineació no es
  curen afegint més pes ni amb denoise.

## Vixen / Canon R6 Mark III

- Conserva el pedestal real dels darks; no substitueixis silenciosament el
  negre del fabricant per un valor de libraw.
- El mode de lectura canvia amb l'exposició; darks i estimació de soroll han de
  coincidir amb cada grup.
- El PRNU s'estima amb estrelles emmascarades i estimador robust. Un mapa que
  absorbeix estrelles imprimeix clots al màster.
- Corona i earthshine tenen registres diferents: seguiment solar no anul·la el
  moviment lunar entre preses.
- El producte de cada exposició ha de conservar cobertura i variància, no
  només un TIFF renderitzat.

Constants mesurades: pedestal 511,5 ADU; pou 16382; sostre lineal validat
13.490,8 sobre el fosc i blanc Adobe 13995; guany 5,08 e⁻/ADU en R/G i 4,33
en B; soroll de lectura 2,72 ADU per sota d'1 s i 1,05 ADU a partir d'1 s;
PRNU 1,3–1,6 %. Els darks útils són els de 40–41 °C.

## Sony 300 mm / A7RIIIA

- Aplica el flat real del tren Sony abans de jutjar el SNR espacial; el
  vinyetatge del cantó no és soroll.
- Separa els segments creats pels salts de la muntura i registra cada presa
  amb transformació pròpia.
- Les preses llargues poden portar filtratge espacial RAW i soroll correlacionat;
  no assumeixis l'escalat de soroll blanc. Mesura-ho amb meitats independents
  quan existeixen; en una presa única declara que aquest control no aplica i
  conserva separades la variància diagonal i la covariància pendent.
- No transfereixis ni darks, ni flats, ni transformacions del Vixen.

Constants mesurades: pedestal 512 ADU; pou 16383; guany 3,41 e⁻/ADU; soroll
de lectura 1,22 ADU; corrent fosc negligible al master de 8 s. El flat del
300 mm corregeix aproximadament −0,214 EV al camp. La xifra d'autocorrelació
`+0,42` i el factor `1,408`/«20–29 % menys variància» queden **RETIRATS**:
provenien d'una diferència A−C sense registre i barrejaven escena i muntura.
Els parells de dark de 8 s donen lag-1 aproximadament `0,07–0,11`, semblant als
2 s, però això no mesura tota la covariància espacial de la imatge. Conserva
la variància diagonal sense factor inventat (`factor=1,0`) i declara
`spatial_covariance=PENDENT`; no projectis un guany `sqrt(N)`.

## Prova d'admissió d'una presa

Per una candidata dubtosa, conserva dos màsters idèntics excepte per la seva
presència. Accepta-la només si, dins la regió que aporta:

1. augmenta cobertura o redueix la incertesa estimada;
2. no crea residu coherent amb sensor, registre, màscara o atmosfera;
3. no empitjora PSF ni duplica estructura;
4. el resultat es reprodueix en una partició A/B o en una font independent
   quan hi ha prou captures. Si és una presa única, substitueix aquest control
   impossible per tancament del registre target, solapament amb l'exposició
   veïna, inspecció de residu estructurat i guany de suport útil.

No tenir repeticions no és no tenir evidència. `QUARANTENA` només si, després
dels controls alternatius en el marc objectiu, encara no es pot decidir la
validesa per l'ús declarat; si el defecte és reparable, `REPROCESSAR`; si no
aporta informació recuperable, `REBUTJAT`.

### Precedent Sony 8 s d'aquest eclipsi

- `DSC06987` (segment A) i `DSC06993` (segment C) són preses úniques que s'han
  de processar independentment per `CORONA_SOLAR`. No es poden excloure d'aquest
  ús per un `FAIL` estel·lar, per manca d'A/B o per covariància pendent si el
  registre solar, la continuïtat i el suport útil passen.
- No les declaris repeticions ni construeixis un stack A+C: cada una conserva
  transformació, màscara, variància i rebut propis i pot contribuir aigües
  avall com a `CONTRIBUCIO_UNICA`.
- `DSC06990` sí queda `REBUTJAT` per `MOVIMENT_DURANT_EXPOSICIO_8S`, un defecte
  intraexposició real que degrada també el marc solar.
- Aquesta decisió és exclusivament coronal. Earthshine no s'avalua ni s'infereix
  amb aquesta porta.

## Trampes de calibratge ja demostrades

- No desbayeris en un flux fotomètric: el superpíxel 2×2 conserva els quatre
  plans i `G1−G2`; l'AHD correlaciona veïns i altera saturació i variància.
- El balanç de blancs de rawpy retalla el vermell abans del pou. Mesura sempre
  la saturació al cru; 65535 en un TIFF no és el pou del sensor.
- No facis `clip(0)` abans d'estimar el terra: censura els residus curts i
  falseja les raons entre exposicions.
- A la R6, ignora el negre fals de libraw i conserva el pedestal 511,5 dins el
  master.
- Construeix masters de dark amb mitjana compatible, no amb mediana d'enters
  quantitzats; no mesuris el marge emmascarat com si fos imatge.
- El pou R6 és 16382, no 16383; el pla blau té guany 4,33 e⁻/ADU i queda fora
  dels pesos fotomètrics validats.
- L'A7RIIIA de 8 s té soroll correlacionat: no projectis un guany √N.
- Emmascara estrelles abans d'estimar PRNU; si no, el mapa aprèn les traces i
  imprimeix clots invertits.
- Usa exposicions EXIF: el valor nominal 10,0 s correspon a aproximadament
  10,3–10,4 s, i 0,0003125 s és 1/3200.

## Rebut mínim del stack

```text
STACK_RECEIPT
id:
train: VIXEN_R6 | SONY_300MM
frame: CORONA_SOLAR | LLUNA | ESTRELLES
intended_use:
statistical_role: STACK | CONTRIBUCIO_UNICA
source_hashes:
groups_by_exposure_mode_time:
calibration_chain:
accepted_frames:
rejected_frames_and_reason:
duplicates:
reference_geometry:
transforms_and_residuals:
linear_range_by_channel:
variance_product:
coverage_product:
split_half_or_null_test:
repeatability_status:
spatial_covariance_status:
usable_support_gain:
validity_domain:
verdict_by_frame_and_use:
limitations:
output_hashes:
verdict: ACCEPTAT | REPROCESSAR | QUARANTENA | REBUTJAT
```
