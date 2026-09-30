# Disseny HDR nadiu — A7III + AP130GTX + QUADCC

Data: 27 de juliol de 2026  
Estat: **disseny candidat; `capturemode` qualificat en repòs, càrrega RAW NO qualificada**

## Decisió executiva

La millor aproximació nadiua al producte HDR obtingut el 2024 no és repetir
únicament un bracket de `5 × 3 EV`. Aquesta opció cobreix més rang, però deixa
salts de fins a **3,059 EV** entre exposicions consecutives.

El candidat fotogràfic principal és un híbrid agrupat, sempre a ISO 100 i
base `1/30 s`:

1. `N` brackets continus de `9 × 1 EV`;
2. un únic canvi de `capturemode`;
3. `N` brackets continus de `5 × 3 EV`.

Amb dues repeticions de cada mode s'obtenen 28 RAW; amb tres, 42 RAW. Agrupar
els brackets evita alternar el mode a cada escala i redueix el disseny a una
sola mutació interna de `capturemode`.

Aquesta continua sent una recomanació **fotogràfica**, no encara un perfil de
producció. F3M del 27 de juliol sí que ha qualificat en repòs totes les arestes
directes de la matriu `Single ↔ 9EV1 ↔ 5EV3 ↔ Single`:

- 10/10 canvis per sentit a `Single ↔ 3EV5`;
- 10/10 canvis per sentit a `Single ↔ 1EV9`;
- 10/10 canvis per sentit a `3EV5 ↔ 1EV9`;
- una única ordre de mutació gphoto2 per mostra, sense retry i sempre
  confirmada per readback;
- pressupost d'enginyeria de **1,4 s per transició**.

L'ACK arriba molt abans que el mode sigui efectiu; la confirmació observada va
trigar entre 0,697 i 0,879 s. Per tant, el controlador ha de reservar 1,4 s i
verificar el readback. El bloquejador que queda no és la matriu lògica de
modes, sinó comprovar-la mentre hi ha captures RAW i activitat de buffer/SD.
El fallback de màxima simplicitat continua sent un únic mode `5 × 3 EV`
preconfigurat i repetit, si una prova solar valida els salts de 3 EV.

## Abast

Els càlculs fotogràfics d'aquesta anàlisi són offline. La secció F3M incorpora
tres proves físiques de canvi de mode; no s'hi va fer cap captura. Es basa en:

- els RAW i manifests locals de 2024;
- les proves A7III de bracketing fetes el 25 de juliol de 2026;
- les tres proves físiques F3M del 27 de juliol de 2026;
- el menú exposat als logs de gphoto;
- el manual oficial de Sony;
- el codi oficial de libgphoto2 2.5.34.

El càlcul pressuposa:

- A7III astromodificada;
- AP130GTX + QUADCC;
- mode `M`;
- ISO 100 fix, que era el pla inicial de cel net; ISO 200 el 2024 va
  compensar a última hora una capa fina de núvols;
- RAW sense comprimir;
- `Long Exposure NR = Off`;
- base comuna `1/30 s`;
- bracketing d'exposició mitjançant temps d'obturació, no ISO.

Sony confirma que, en mode manual amb un ISO diferent d'Auto, el bracketing
varia la velocitat d'obturació.

## Autoritat fotogràfica: ladder A7III/AP130 de 2024

La primera volta HDR completa observada als RAW conté dues preses per nivell:

`1/500 → 1/250 → 1/100 → 1/30 → 1/15 → 1/8 → 0,4 → 1 → 2 → 0,8 s`

Ordenada per exposició física, la cobertura és:

| Exposició | Offset respecte `1/30` | Gap anterior |
|---:|---:|---:|
| `1/500` | −4,059 EV | — |
| `1/250` | −3,059 EV | 1,000 EV |
| `1/100` | −1,737 EV | 1,322 EV |
| `1/30` | 0,000 EV | 1,737 EV |
| `1/15` | +1,000 EV | 1,000 EV |
| `1/8` | +1,907 EV | 0,907 EV |
| `0,4 s` | +3,585 EV | 1,678 EV |
| `0,8 s` | +4,585 EV | 1,000 EV |
| `1 s` | +4,907 EV | 0,322 EV |
| `2 s` | +5,907 EV | 1,000 EV |

Resum:

| Magnitud | Ladder 2024 |
|---|---:|
| Frames | 20 |
| Exposicions úniques | 10 |
| Repeticions per nivell | 2 |
| Rang físic | 9,966 EV |
| Gap màxim | 1,737 EV |
| Suma física d'exposicions | 8,882 s |
| Interval RAW, primera → última | 52 s |

Els 20 RAW van de `DSC06594` a `DSC06613`, entre 19:08:13 i 19:09:05.
El sensor només va estar integrant uns 8,9 s: la major part dels 52 s es va
consumir en captures, mutacions PTP, reobertures de sessió i esperes.

## Opció A — només `5 × 3 EV`, base `1/30`

Amb l'arrodoniment als passos físics disponibles de l'A7III:

| Ordre fosc → clar | Exposició | Offset real | Gap anterior |
|---:|---:|---:|---:|
| 1 | `1/2000` | −6,059 EV | — |
| 2 | `1/250` | −3,059 EV | 3,000 EV |
| 3 | `1/30` | 0,000 EV | 3,059 EV |
| 4 | `1/4` | +2,907 EV | 2,907 EV |
| 5 | `2 s` | +5,907 EV | 3,000 EV |

| Magnitud | `5 × 3 EV` |
|---|---:|
| Frames per bracket | 5 |
| Exposicions úniques | 5 |
| Rang físic | 11,966 EV |
| Gap màxim | 3,059 EV |
| Suma física d'exposicions | 2,288 s |
| Canvis PTP dins del bracket | 0 |

### Avantatges

- cobreix dos EV més pel costat curt que el ladder HDR de 2024;
- conserva l'extrem llarg de 2 s;
- un sol trigger compromet les cinc exposicions;
- es pot repetir sense cap mutació PTP;
- és la ruta més simple i fail-safe de les estudiades.

### Limitacions

- els salts són aproximadament de 3 EV;
- no hi ha `1/500`, `1/100`, `1/15`, `1/8`, `0,4`, `0,8` ni `1 s`;
- repetir el bracket millora redundància, SNR i mostreig temporal, però
  **no omple cap gap EV**;
- la primera presa curta seria `1/2000`, no el `1/8000` mesurat per als
  contactes C2/C3.

Aquesta opció només pot guanyar si una simulació solar demostra solapament
radial i SNR suficients entre els cinc nivells, inclòs el registre a través
dels salts de 3 EV.

## Opció B — només `9 × 1 EV`, base `1/30`

| Ordre fosc → clar | Exposició | Offset real | Gap anterior |
|---:|---:|---:|---:|
| 1 | `1/500` | −4,059 EV | — |
| 2 | `1/250` | −3,059 EV | 1,000 EV |
| 3 | `1/125` | −2,059 EV | 1,000 EV |
| 4 | `1/60` | −1,000 EV | 1,059 EV |
| 5 | `1/30` | 0,000 EV | 1,000 EV |
| 6 | `1/15` | +1,000 EV | 1,000 EV |
| 7 | `1/8` | +1,907 EV | 0,907 EV |
| 8 | `1/4` | +2,907 EV | 1,000 EV |
| 9 | `1/2` | +3,907 EV | 1,000 EV |

| Magnitud | `9 × 1 EV` |
|---|---:|
| Frames per bracket | 9 |
| Exposicions úniques | 9 |
| Rang físic | 7,966 EV |
| Gap màxim | 1,059 EV |
| Suma física d'exposicions | 1,006 s |
| Canvis PTP dins del bracket | 0 |

És molt més dens que `5 × 3 EV` i reprodueix bé el centre del ladder 2024.
Però acaba a `1/2 s`: deixa fora `0,8`, `1` i `2 s`, amb un buit de 2 EV
entre `1/2` i l'extrem llarg de 2024.

## Opció C — híbrid `9 × 1 EV` + `5 × 3 EV`

Amb la mateixa base `1/30`, la unió física és:

`1/2000, 1/500, 1/250, 1/125, 1/60, 1/30, 1/15, 1/8, 1/4, 1/2, 2 s`

| Magnitud | Híbrid |
|---|---:|
| Frames totals per parella | 14 |
| Exposicions úniques | 11 |
| Duplicats | `1/250`, `1/30`, `1/4` |
| Rang físic | 11,966 EV |
| Gap màxim | 2,000 EV |
| Gap màxim al centre `1/500…1/2` | 1,059 EV |
| Suma física de les 14 exposicions | 3,294 s |
| Mutacions de mode, una parella aïllada | 1 |

La correspondència amb el ladder 2024 és:

| Valor 2024 | Híbrid més proper | Diferència |
|---:|---:|---:|
| `1/500` | `1/500` | 0,000 EV |
| `1/250` | `1/250` | 0,000 EV |
| `1/100` | `1/125` | 0,322 EV |
| `1/30` | `1/30` | 0,000 EV |
| `1/15` | `1/15` | 0,000 EV |
| `1/8` | `1/8` | 0,000 EV |
| `0,4 s` | `1/2` | 0,322 EV |
| `0,8 s` | `1/2` | 0,678 EV |
| `1 s` | `1/2` | 1,000 EV |
| `2 s` | `2 s` | 0,000 EV |

L'híbrid conserva el rang de `5 × 3 EV` i la densitat central de
`9 × 1 EV`. El punt feble queda concentrat als extrems:

- `1/2000 → 1/500`: 2 EV;
- `1/2 → 2 s`: 2 EV.

És, per tant, l'equivalent nadiu més proper al ladder 2024 sense reintroduir
deu setters d'obturació.

## Per què s'ha d'agrupar

Alternar:

`9×1 → 5×3 → 9×1 → 5×3`

obligaria a fer un canvi de mode a gairebé cada bracket. La forma correcta
de conservar redundància és:

`N × (9×1) → un switch verificat → N × (5×3)`

Exemples:

| Disseny | Frames | Exposicions úniques | Repetició nominal | Switch intern |
|---|---:|---:|---:|---:|
| `1 × 9EV1 + 1 × 5EV3` | 14 | 11 | 1 | 1 |
| `2 × 9EV1 + 2 × 5EV3` | 28 | 11 | 2 | 1 |
| `3 × 9EV1 + 3 × 5EV3` | 42 | 11 | 3 | 1 |

L'ordre dels dos grups és provisional per raons fotogràfiques i de càrrega de
buffer, no per manca d'una aresta disponible: F3M ha qualificat tant les
entrades i sortides directes de `Single Shot` com el switch intern
`9EV1 ↔ 5EV3`.

## F3M: matriu qualificada en repòs

Tres runs físics han cobert les sis arestes directes amb 10 mostres cadascuna,
60/60 canvis correctes:

| Transició | n | Mediana | Màxim | Pressupost |
|---|---:|---:|---:|---:|
| `3EV5 → 1EV9` | 10 | 815,660 ms | 835,890 ms | 1,4 s |
| `1EV9 → 3EV5` | 10 | 817,405 ms | 844,078 ms | 1,4 s |
| `Single → 3EV5` | 10 | 816,060 ms | 839,370 ms | 1,4 s |
| `3EV5 → Single` | 10 | 818,584 ms | 838,438 ms | 1,4 s |
| `Single → 1EV9` | 10 | 813,435 ms | 878,636 ms | 1,4 s |
| `1EV9 → Single` | 10 | 819,774 ms | 836,846 ms | 1,4 s |

Condicions:

- A7III, firmware 4.04 confirmat físicament per l'operador;
- gphoto2 2.5.32 i libgphoto2 2.5.34;
- zero captures i zero commits de press;
- firewall limitat a identitat i `capturemode`;
- una sola ordre de mutació gphoto2 per mostra, cap retry;
- polls cada 100 ms durant un màxim de 3 s;
- restauració exacta a `Single Shot`;
- cap xarxa.

El run curt anterior havia llegit encara `3EV5` aproximadament 0,4 s després
del write i es va aturar. Les 60 mostres noves situen la primera confirmació
positiva entre 696,518 i 878,636 ms després del commit. Per tant, aquella
lectura demostrava que l'ACK no equival a adopció immediata, però **no que el
write hagués estat ignorat**: es va observar massa aviat.

El resultat complet i els hashes dels artefactes són a
[`23_F3M_A7III_CAPTUREMODE.md`](23_F3M_A7III_CAPTUREMODE.md). F3M qualifica la
matriu sense càrrega; encara no demostra la latència ni la fiabilitat mentre la
càmera captura o buida RAW sense comprimir.

## Bytes i pressió sobre el buffer

Els RAW A7III de les proves locals de 2026 ocupen exactament
48.838.144 bytes cadascun, són sense comprimir i compatibles amb 14 bits.
Els 56 RAW A7III/AP130 de 2024 fan una mitjana molt semblant:
48.956.123 bytes.

| Frames | Bytes | GB decimals | GiB |
|---:|---:|---:|---:|
| 1 | 48.838.144 | 0,049 | 0,045 |
| 5 | 244.190.720 | 0,244 | 0,227 |
| 9 | 439.543.296 | 0,440 | 0,409 |
| 14 | 683.734.016 | 0,684 | 0,637 |
| 20 | 976.762.880 | 0,977 | 0,910 |
| 28 | 1.367.468.032 | 1,367 | 1,274 |
| 42 | 2.051.202.048 | 2,051 | 1,910 |
| 55 | 2.686.097.920 | 2,686 | 2,502 |
| 70 | 3.418.670.080 | 3,419 | 3,184 |
| 90 | 4.395.432.960 | 4,395 | 4,094 |

### Límit conegut

La prova local més forta només ha demostrat:

- 15 RAW sense drenatge entre brackets;
- 5/5 RAW `5 × 3 EV` íntegres a base `1/125`;
- RAW de 48.838.144 bytes, 14 bits, hashes únics;
- cap prova sostinguda card-only de 28, 42, 55, 70 o 90 RAW.

Per tant, **el límit del buffer i l'escriptura sostinguda a SD encara són
desconeguts**. Una seqüència que cap astronòmicament dins la totalitat no és
automàticament compatible amb la càmera i la targeta.

## Compatibilitat amb una totalitat de 75,95–aprox. 90 s

El perfil anterior reservava per a HDR la finestra:

`C2 + 1,5 s → C3 − 16,2 s`

La durada útil és:

`HDR = (C3 − C2) − 17,7 s`

| Totalitat | Finestra HDR protegida |
|---:|---:|
| 75,95 s | 58,25 s |
| 90,00 s | 72,30 s |

### Pressupostos de disseny, encara no qualificats

No s'ha fet encara un bracket real base `1/30`. El `5 × 3 EV` necessita com
a mínim 2,288 s només per integrar les cinc exposicions. Fins que es mesuri,
s'usen dues hipòtesis de slot:

| Slot `5 × 3 EV` | Brackets en 58,25 s | Frames | Brackets en 72,30 s | Frames |
|---:|---:|---:|---:|---:|
| 4 s | 14 | 70 | 18 | 90 |
| 5 s | 11 | 55 | 14 | 70 |

Aquests recomptes només proven que el temps astronòmic no és el coll
d'ampolla. No autoritzen 55–90 RAW sense la prova de buffer.

Per al candidat agrupat, s'adopten provisionalment:

- 4 s per `9 × 1 EV`;
- 5 s per `5 × 3 EV`;
- 1,4 s per cada transició verificada de `capturemode`.

| Disseny agrupat | Pressupost provisional | Frames | GB |
|---|---:|---:|---:|
| `2 × 9EV1 + switch + 2 × 5EV3` | 19,4 s | 28 | 1,367 |
| `3 × 9EV1 + switch + 3 × 5EV3` | 28,4 s | 42 | 2,051 |

Tots dos caben amb marge dins la finestra mínima de 58,25 s. Els temps són
pressupostos per dissenyar el Gate, no mesures de producció.

## Bracket Order `− → 0 → +`

Sony ofereix a l'A7III:

- `0 → − → +`;
- `− → 0 → +`.

El manual descriu el segon com l'ordre fosc → estàndard → clar. En `M` amb
ISO fix, la càmera fa el bracketing canviant el temps d'obturació; per tant,
el costat fosc correspon a la presa més curta.

L'ordre esperat amb `− → 0 → +` és:

- `5 × 3 EV`, base `1/30`:
  `1/2000 → 1/250 → 1/30 → 1/4 → 2 s`;
- `9 × 1 EV`, base `1/30`:
  `1/500 → 1/250 → 1/125 → 1/60 → 1/30 → 1/15 → 1/8 → 1/4 → 1/2`.

Els RAW locals actuals només validen l'ordre de fàbrica
`0, −3, +3, −6, +6`:

`1/125, 1/1000, 1/15, 1/8000, 1/2`

No hi ha encara cap run local de cinc o nou RAW amb `− → 0 → +`. S'ha de
validar l'ordre exacte per EXIF abans de convertir-lo en precondició de
camp.

### Gphoto no exposa l'ajust Sony

libgphoto2 2.5.34 sí que enumera al `capturemode`:

- brackets continus `C` de 3, 5 i 9 fotos;
- passos 0,3 / 0,5 / 0,7 / 1 EV;
- `2 × 3/5 EV`;
- `3 × 3/5 EV`;
- les variants individuals `S`.

Però `bracketorder` només està implementat per Nikon:

- taula `_Nikon_BracketOrder`;
- propietat `PTP_DPC_NIKON_BracketOrder`;
- entrada de menú Nikon `bracketorder`.

No existeix una entrada equivalent Sony ni
`PTP_DPC_SONY_*BracketOrder` a la versió auditada. Per tant:

1. s'ha de configurar manualment a la càmera abans de PC Remote;
2. no es pot confiar en un path gphoto amb nom estable;
3. el preflight només podrà exigir una confirmació manual i una prova EXIF
   prèvia, tret que es descobreixi i qualifiqui una propietat Sony no
   documentada en un Gate separat.

## Altres opcions natives

| Opció | Rang | Gap màxim | Frames | Veredicte |
|---|---:|---:|---:|---|
| `5 × 2 EV`, base `1/30` | aprox. 8 EV | aprox. 2 EV | 5 | Dominada per `9 × 1 EV` si el buffer aguanta |
| `9 × 0,7 EV` | aprox. 5,6 EV | aprox. 0,7 EV | 9 | Massa estreta per substituir 2024 |
| `9 × 0,5 EV` | 4 EV | 0,5 EV | 9 | Massa estreta |
| `9 × 0,3 EV` | 2,4 EV | 0,3 EV | 9 | Massa estreta |
| `Bracketing S` | igual al mode equivalent | igual | 1 per trigger | Massa sensible a un trigger perdut |
| Dues bases diferents | pot omplir gaps | configurable | variable | Reintrodueix el setter lent d'obturació |

`Bracketing S` evita canviar l'obturació via PTP, però exigeix un trigger per
fotograma. Si se'n perd un, l'estat intern del bracket queda desplaçat i el
controlador no pot reconstruir de forma segura quina exposició farà la
següent pulsació. `Bracketing C` és preferible perquè un sol press/release
compromet l'escala completa.

## Gate necessari abans d'implementar el perfil final

1. Configurar manualment `Bracket Order = − → 0 → +`.
2. Fer un `5 × 3 EV` base `1/30`, ISO 100, RAW sense comprimir:
   - exactament cinc RAW;
   - ordre EXIF curt → llarg;
   - valors físics esperats;
   - durada press → cinquè frame;
   - temps d'activitat SD.
3. Fer un `9 × 1 EV` equivalent:
   - exactament nou RAW;
   - ordre i offsets físics;
   - durada real.
4. Revalidar sota càrrega el camí concret de producció:
   - totes les arestes directes ja han superat F3M en repòs amb una sola
     ordre de mutació gphoto2;
   - reservar 1,4 s per transició i exigir readback;
   - intercalar el switch després d'un bracket RAW, amb activitat real de
     buffer/SD;
   - abortar si s'exhaureix el deadline, sense retry ocult.
5. Executar `2 + 2` brackets agrupats i verificar 28 RAW a la SD.
6. Executar `3 + 3` i verificar 42 RAW.
7. Fer tres simulacions completes de 90 s amb la targeta i alimentació de
   camp.
8. Comparar sobre el Sol:
   - clipping per canal;
   - SNR per zona radial;
   - solapament entre nivells;
   - registre a través dels gaps de 2/3 EV;
   - nitidesa a 1/2 i 2 s.

## Conclusió

La totalitat de 75,95–90 s ofereix temps suficient per substituir el ladder
PTP de 2024 per bracketing nadiu. La matriu de canvis de mode ja no és el
bloquejador en repòs; queden obertes la validació fotogràfica dels brackets i
la qualificació de captures, buffer i switch sota càrrega RAW.

1. Si `5 × 3 EV` dona prou solapament malgrat els gaps de 3 EV, és la ruta
   més robusta perquè elimina totes les mutacions internes.
2. Si els gaps de 3 EV són insuficients, l'híbrid agrupat és fotogràficament
   superior i s'aproxima molt al ladder 2024.
3. L'híbrid ha superat F3M en repòs en totes sis direccions, amb una única
   ordre de mutació gphoto2 i un pressupost provisional de 1,4 s per
   transició; encara ha de repetir el camí sota càrrega RAW real.
4. Cap de les dues rutes és release d'eclipsi fins demostrar el buffer i
   l'escriptura sostinguda de RAW sense comprimir a SD.

## Fonts locals

- `research/12_FORENSICA_RAW_2024.md`
- `research/data/2024_exposure_runs.csv`
- `research/data/2024_raw_timeline.csv`
- `research/data/2024_raw_summary.csv`
- `tests/2026-07-25_GATE7_A7III_BUFFER_DUAL_HDR.md`
- `controller/runs/20260725T235014_lab_a7m3_silent_3ev5_unclipped_run/downloads_manifest.json`
- `controller/runs/20260725T235509_lab_a7m3_silent_3ev5_unclipped_run/gphoto_transcript.log`
- `controller/runs/20260727T023618_candidate_a7m3_ap130_2024_choreography_f3m-capturemode/events.jsonl`
- `controller/runs/20260727T023618_candidate_a7m3_ap130_2024_choreography_f3m-capturemode/result.json`
- `controller/runs/20260727T024315_candidate_a7m3_ap130_2024_choreography_f3m-capturemode/result.json`
- `controller/runs/20260727T024354_candidate_a7m3_ap130_2024_choreography_f3m-capturemode/result.json`
- `controller/runs/20260727T024429_candidate_a7m3_ap130_2024_choreography_f3m-capturemode/result.json`
- `research/23_F3M_A7III_CAPTUREMODE.md`

## Fonts oficials

- [Sony A7III — Bracket Settings](https://helpguide.sony.net/ilc/1720/v1/en/contents/TP0001653143.html)
- [Sony A7III — Cont. Bracket](https://helpguide.sony.net/ilc/1720/v1/en/contents/TP0001629684.html)
- [libgphoto2 2.5.34 — modes Sony de bracketing](https://github.com/gphoto/libgphoto2/blob/v2.5.34/camlibs/ptp2/config.c#L4543-L4584)
- [libgphoto2 2.5.34 — `Nikon_BracketOrder`](https://github.com/gphoto/libgphoto2/blob/v2.5.34/camlibs/ptp2/config.c#L6893-L6897)
- [libgphoto2 2.5.34 — entrada `bracketorder` Nikon](https://github.com/gphoto/libgphoto2/blob/v2.5.34/camlibs/ptp2/config.c#L11818-L11830)
- [libgphoto2 2.5.34 — propietat PTP Nikon BracketOrder](https://github.com/gphoto/libgphoto2/blob/v2.5.34/camlibs/ptp2/ptp.h#L2431-L2436)
