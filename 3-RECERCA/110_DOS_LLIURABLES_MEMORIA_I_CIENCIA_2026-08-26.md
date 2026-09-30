> ⛔ **HISTÒRIC des del 27-08-2026.** Pere ha **deprecat el mode `MEMORIA`** i
> el projecte segueix **només amb `CIENCIA`**. Aquest document és la
> **proveniència de la decisió** —el que es va mirar per prendre-la—, no una
> tria oberta. La cadena ja no arrenca cap run `MEMORIA`. `research/116` §7.
> ⏭️ El que d'aquí continua VIU: el guany `(1,1528 · 1 · 1,0249)` com a
> **mesura** del terme de càmera i vidre entre trens, i el `DSC06991` com a
> **control** extern del color.

# 110 · Dos lliurables: el color que Pere recorda i el color que es pot defensar

**Data:** 26 d'agost de 2026, vespre. **Encàrrec de Pere:** dos runs del Vixen
des de zero — «el primer que s'assembli al màxim al color que veig a
`DSC06991.ARW`, que és el que recordo d'haver viscut això; el segon amb la
calibració de color que trobis més adient i sigui científicament vàlida, alhora
que realista». Contrast amb Codex autoritzat i executat.

**Els dos runs comparteixen TOT menys el blanc adoptat**: la mateixa dada, la
mateixa geometria, els mateixos filtres i **la mateixa corba de to**. Comparar-
los aïlla una sola variable.

---

## 1. El que va canviar a la cadena, i per què

Tres defectes de revelat, tots documentats a `research/109`, i una peça nova:

1. ⛔ **La matriu de color de la càmera no s'aplicava.** Els multiplicadors del
   balanç de blancs sols no són colorimetria: sense la matriu la corona surt
   **2,6 vegades massa blava** (B/G 0,498 en lloc de 0,194) i el producte
   sortia «tirant a cafè». `comu.matriu_srgb`, convenció dcraw —files de la
   matriu **endavant** normalitzades i després invertida—, amb autocontrol que
   el neutre surti neutre.
2. ⛔ **El color derivava amb el radi.** Tonificar cada canal afegeix un
   desplaçament constant en logaritme i, com que el nivell cau, el quocient de
   pantalla es dispara: **R/G d'1,06 a 1,35 amb la dada plana a 1,76**. Era
   exactament el que Pere veia a les capes externes. Ara hi ha **una sola corba
   escalar sobre la lluminància** i el croma es restitueix a **baixa
   freqüència** (σ 24 px), amb el gamut acotat per un pes i **mai retallant per
   canal**.
3. ⛔ **El cel es restava al producte visual**, i això és el que fabricava el
   terra negre i el gradient del caire. Ara **el terra és cel**, com a Brno. El
   producte científic continua sent els FITS lineals amb el cel restat: **són
   dos productes, no un**.
4. ⏭️ **Porta nova, `comu.tancament_hdr`** (§3).

La corba és **pendent 0,22 per dècada, àncora 0,74 a 1,05–1,15 R☉, terra
0,045**. Els 0,22 són dins la banda de Brno (**0,202–0,240** mesurats sobre els
seus quatre composts del nostre eclipsi) i entre la maqueta de Pere (0,166) i
`estira_log` (0,524, que cremava 1,67 dècades).

## 2. Els dos blancs

### `MEMORIA` — el testimoni

Guany **(1,1528 · 1 · 1,0249)** aplicat després de la matriu. És el terme de
**càmera i vidre** entre els dos trens, mesurat comparant `DSC06991.ARW` (Sony
A7RIIIA, 300 mm, 1 s, 20:29:44) amb `572A2996.CR3` (Canon R6 III, VSD90SS, 1 s,
20:30:04) sobre 2,18–4,82 R☉: **1,3 % i 2,2 % de dispersió** sobre set radis.

⚠️ **No és un producte colorimètric i no ho pretén.** És la nostra dada
renderitzada perquè coincideixi amb el fotograma que Pere recorda. Va declarat.

### `CIENCIA` — el blanc és el Sol

Guany **1/(1,075 · 1 · 0,888) = (0,9302 · 1 · 1,1261)**, o sigui blanquejar
sobre **l'espectre solar extraterrestre (AM0)**.

L'argument és de Codex i és el que decideix: **D65 és llum diürna mitjana, no
el blanc al qual l'ull de Pere estava adaptat.** Dir «D65 = tal com es veia»
seria fals. Amb el **Sol** com a blanc adoptat, el que queda a la imatge és
**l'extinció de León**, i això sí que és una afirmació física i auditable.

⛔ Les altres tres opcions i per què no: **(a) D65 tal qual** és un control
colorimètric, no una escena; **(c) blanquejar sobre la corona** (Brno) és
auto-referencial —absorbeix al blanc el color mitjà d'una barreja K/F que depèn
del radi i de l'azimut—; **(d) corregir a X = 1** és un contrafactual.

## 3. Els controls, i un que va donar un fals negatiu

**Tancament HDR** — el compost contra un **fotograma solt del mateix tren**,
als **MATEIXOS anells**:

| anell (R☉) | compost R/G | foto R/G | dif | compost B/G | foto B/G | dif |
|---|---:|---:|---:|---:|---:|---:|
| 1,8–2,0 | 1,664 | 1,697 | −1,9 % | 0,309 | 0,303 | +1,9 % |
| 2,3–2,7 | 1,426 | 1,412 | +1,0 % | 0,500 | 0,485 | +3,2 % |
| 3,1–3,6 | 1,205 | 1,192 | +1,1 % | 0,633 | 0,612 | +3,5 % |
| 4,2–4,9 | 1,062 | 1,057 | +0,5 % | 0,712 | 0,685 | +4,0 % |

**Mediana R/G +0,8 %, B/G +3,5 %; pitjor 4,0 % → PASSA** (llindar 5 %).

⚠️ **Amb radis DIFERENTS el mateix control dona −20 % i falla.** La proporció
K/F canvia amb el radi, o sigui que **un control de color s'ha de fer a la
mateixa obertura**. És la lliçó de mètode d'aquesta ronda.

**Tancament del model** — extinció predita 1,818 · 0,250 contra 1,796 · 0,243
mesurats al fotograma a 1,70 R☉: **1,2 % i 2,8 %**.

**Control del testimoni** — el color lliurat contra el perfil del `DSC06991`,
anell per anell, escrit al rebut de cada run.

### 3 bis. La porta va enxampar TRES defectes meus abans de deixar passar res

⏭️ **Val la pena escriure-ho perquè és el que justifica tenir la porta.** Cap
dels tres no s'hauria vist mirant la imatge.

1. ⛔ **El control agafava el primer fitxer de la carpeta**, que és
   `572A2936.CR3`, de **1/3200 s** —un fotograma de CONTACTE—, i allà no hi ha
   corona a 2–5 R☉. Tornava `SENSE DADA`… **i la porta el deixava passar
   igual**. Un control que no es pot computar és un control que no s'està fent.
   Ara els candidats van **de més llarga a més curta** i, si cap no dona quatre
   anells, **la cadena s'atura**.
2. ⛔ **El control comparava el compost AMB el guany del mode aplicat** contra
   un fotograma sense guany, o sigui que **mesurava el guany**: al mode
   `CIENCIA` donava −5,1 % i +8,4 % de mediana, que són exactament 0,9302 i
   1,1261. El control ha de comprovar la **dada**, no la presentació.
3. ⛔ **La màscara de saturació es mesurava després del balanç de blancs i
   sobre el mosaic ja binat.** Amb el balanç, el multiplicador del vermell val
   2,17 i movia el llindar per canal; amb el binat, un píxel saturat promitjat
   amb un que no ho és baixa del llindar i **la saturació s'hi colava**.

⚠️ **I una quarta cosa, que no era un defecte sinó una lliçó:** amb el
fotograma de **10 s**, l'anell de 1,8–2,0 R☉ donava **−42,7 %** sense que hi
hagués res malament al compost. La causa és **biaix de selecció**: en un anell
mig saturat, els píxels que sobreviuen són **els més foscos**, i la seva
barreja K/F no és la de l'anell sencer. Ara es descarta qualsevol anell amb
menys del 80 % de píxels vius, i el 10 s queda **rebutjat sencer** (només 3
anells vàlids de 7).

**El candidat que la porta tria és el de 2 s**, i el resultat és:

| fotograma | anells | sistemàtic | pitjor | veredicte |
|---|---:|---:|---:|---|
| 10 s | 3 | — | — | rebutjat (pocs anells) |
| **2 s** | **7** | **3,8 %** | **5,3 %** | **PASSA** |
| 1 s | 7 | 4,7 % | 6,1 % | passaria |
| 0,5 s | 7 | 8,5 % | 11,7 % | NO passaria |

⏭️ **La porta jutja el SISTEMÀTIC** (mediana sobre els anells), no l'anell
pitjor: l'anell interior és on la saturació i la llum dispersa piquen més fort
i no descriu el color del compost. El pitjor es declara igualment.

⚠️ **El sistemàtic de 3,8 % és real i no és soroll**: el compost i un fotograma
solt discrepen un **+4 % en R/G i un −3 % en B/G** de manera constant amb el
radi. Candidats: la no-linealitat per canal a la vora del pou que el LDIC
barreja, el flat, i el gauge de coherència. Queda **declarat i obert**.

## 4. El residu que l'extinció NO explica

Amb blanc AM0 la corona surt **1,7935 · 0,2185** i l'extinció **sola** en
prediu **1,691 · 0,2815**: sobra un **+6,1 % de vermell** i falta un **−22,4 %
de blau**.

⛔ **Això no és soroll i no es pot separar amb el que tenim.** És corona **F**
(pols, que conserva l'espectre fotosfèric més el seu enrogiment), **línies E**,
resposta instrumental i error de model. Una separació K/F demanaria bandes de
**0,5 nm** i **polarimetria** —l'observable que justament no tenim—; amb tres
bandes amples només se'n pot fer un ajust condicionat, que no és una mesura.

Per això el PSB de `CIENCIA` porta **dues** capes de diagnòstic i no una:

- **`07 SOBRE L'ATMOSFERA`** — dividida per l'extinció **declarada**;
- **`08 CORONA NEUTRA`** — dividida pel color **mesurat** de la corona, que és
  el que fa Brno.

⏭️ **La diferència entre la 07 i la 08 ÉS aquest residu**, i es pot mirar.

## 5. La troballa que tanca el cel blau

Blanquejant sobre la corona, el nostre cel de **1,0 · 0,75** es converteix en
**blau**. Mesurat sobre la nostra pròpia dada en fer la capa `08`.

⏭️ **El cel blau de Druckmüller —i probablement el del `GraduantColor` de
Pere— surt d'haver blanquejat la corona, no de ser blau al RAW.** Tanca la
pregunta oberta del `research/109` §13 sense cap dada nova.

## 6. El que continua obert

- ⛔ «Planck + CIE + matriu dcraw» **no és calibratge espectral absolut**. El
  desacord vermell entre Sony i Canon (+9 a +20 %) ho demostra. Per a un
  definitiu caldria l'espectre solar **TSIS-1 HSRS** en lloc d'un cos negre.
- ⚠️ Que el terme Sony/Canon sigui **només** càmera i vidre és **probable**
  (coincideixen en B a menys del 5 %) però **no demostrat**: hi ha 20 s de
  separació entre els dos fotogrames.
- ⚠️ El camp a 7–9 R☉ **no és cel pur**: és corona F + cel + llum dispersa.

---

## 7. Els dos runs, executats

`VIXEN_MEMORIA_20260826T155138Z` (18,2 min) i `VIXEN_CIENCIA_20260826T153314Z`
(18,4 min), tots dos amb el **mateix codi congelat** (SHA-256 idèntic als nou
scripts).

| | `MEMORIA` | `CIENCIA` |
|---|---|---|
| guany | (1,1528 · 1 · 1,0249) | (0,9302 · 1 · 1,1261) |
| corona 1,1 R☉ | R/G **2,251** · B/G **0,210** | R/G **1,818** · B/G **0,224** |
| corona 2 R☉ | 1,881 · 0,357 | 1,518 · 0,393 |
| corona 3 R☉ | 1,464 · 0,605 | 1,181 · 0,665 |
| corona 5 R☉ | 1,171 · 0,750 | 0,945 · 0,824 |
| contra el `DSC06991` | **mediana 4,7 %** · pitjor 8,0 % | 19,5 % (per disseny) |
| tancament HDR | 3,8 % · **PASSA** | 3,8 % · **PASSA** |
| gamut acotat | 0,25 % | 0,06 % |
| croma p1–p99 de R−G | 0,2527 | 0,2125 |

⏭️ **El `CIENCIA` a 1,1 R☉ dona 1,818 · 0,224** i la predicció de Codex n'havia
dit **1,793 · 0,218**: **1,4 % i 2,7 %**.

⏭️ **El `MEMORIA` cau a 4,7 % de mediana del testimoni de Pere**, amb el R/G a
−1,6 / −0,3 / +1,1 % i el B/G a −8,0 / +3,4 / +4,7 % a 2, 3 i 5 R☉.

### Prova que només els diferencia el color

Dels **60 fitxers comuns**, **52 són idèntics bit a bit**. Les fases **0, 1 i
2 ho són senceres**. Els vuit que difereixen són exactament els que han de
diferir: `BASE_rgb.npy`, els rebuts de F3 i F4, el manifest i les dues vistes.

**No és una afirmació: és una comprovació de hash.**
