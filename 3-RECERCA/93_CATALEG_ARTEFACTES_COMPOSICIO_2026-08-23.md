# 93 — Catàleg d'artefactes de composició: què els causa i com no tornar-hi

Data: 22-23 d'agost de 2026, nit. Pere va marcar els artefactes sobre el
`00_PREVIEW_4K` amb traç taronja i va demanar dues coses: un stack nou
d'imatges calibrades i **actualitzar el coneixement perquè no me'ls torni a
trobar**. Aquest document és la segona.

Les tres marques de Pere: dues **rectes** que resseguien la vora inferior
esquerra, un **cercle** al voltant de la corona, i quatre **arrels petites** al
fons de la dreta. Totes tres estan mesurades aquí. Al mig en van sortir tres
més que ell no havia marcat i que eren pitjors.

---

## Regla general

> **Cada màscara i cada correcció han de mesurar allò que diuen que mesuren.**
> Els sis artefactes d'aquesta nit són, sense excepció, una màscara o una
> correcció que mirava la magnitud equivocada: la cobertura en lloc del marc,
> la luminància en lloc dels tres canals, el Sol en lloc de la Lluna, un
> escalar en lloc de tres.

---

## A — Escaló rectangular al fons *(marcat per Pere)*

**Què es veu.** Una vora recta, alineada amb els eixos, que talla el cel a la
part esquerra i inferior del llenç. Pere la va resseguir amb dues línies.

**Mesura.** L'apilat Sony v3 **no té cobertura uniforme**. El seu mapa de pes
(`Sony300_apilat_v3_pes_s_float32.tif`) val 24,75 s —els deu fotogrames— dins
la caixa **x 264–7926, y 40–4578**, que és el **78,3 %** del llenç. Fora
d'allà baixa a 13,5 s, 8,75 s, 11,25 s… La resta del camp (**1,6 %**) no té
cap fotograma.

**Causa.** La recepta antiga consumia l'apilat **sense mirar-ne el mapa de
pes**. Cada zona és un subconjunt diferent de fotogrames i té la seva pròpia
mitjana de cel; la diferència entre zones no té cap contingut físic, però
dibuixa el rectangle.

**Correcció.** Un **pedestal constant per zona de cobertura**, mesurat al camp
llunyà (`r > 8,5 R☉`) contra la zona de referència, restat abans de compondre.
Les zones sense prou camp llunyà queden **marcades invàlides**, no
extrapolades.

⛔ **Provat i descartat**: ajustar un **pla o una quàdrica per zona** en lloc
d'un pedestal. Sobreajusta i planta fanals de color als cantons, on el model
extrapola fora del seu domini d'ajust.

**Resultat.** L'escaló baixa a **0,37 σ** del soroll del cel a la vora
inferior, i a la vora esquerra la zona de fora queda declarada invàlida.

**Regla.** *Si un apilat porta mapa de pes, la composició l'ha de llegir.
Un apilat sense mapa de pes no es pot compondre a escala de camp.*

---

## B — Anell de color a ~2,8 R☉ *(marcat per Pere)*

**Què es veu.** Un anell al voltant de la corona: càlida a dins, freda a fora.
El cercle que Pere va dibuixar, ajustat als seus píxels, dona **2,93 R☉** —i
la sigmoide de fusió Vixen↔Sony és a **2,8 R☉**.

**Mesura.** A l'anell de solapament 1,5–2,8 R☉, els quocients Sony/Vixen per
canal són **R 2,143 · G 2,605 · B 3,059**: una dispersió del **±18 %**. Al
compost antic això es traduïa en una variació de color radial del **108 %**
tant a R/G com a B/G entre 1,2 i 6 R☉.

**Causa.** La «calibració fotomètrica» antiga igualava **una sola mediana de
luminància**: un escalar per a tres canals. Amb un sol nombre, la Vixen queda
vermellosa i la Sony blavosa, i l'ull llegeix el pendent com un anell just on
la fusió canvia de mà.

**Correcció.** **Guany i pedestal per canal**, ajustats per mínims quadrats a
l'anell de solapament. Dispersió residual: **0,64 %**.

**Regla.** *La igualació entre trens és per canal, sempre. Un escalar de
luminància no és una calibració de color: és un anell garantit.*

---

## C — Gradient de cel i soroll de crominància *(marcat per Pere)*

**Què es veu.** Un canvi de to al fons de la dreta i un gra blau molt marcat.
Pere hi va posar quatre arrels petites.

**Mesura.** A 9–13 R☉ el fons Sony val **217 / 589 / 377 ADU/s** en RGB. No és
corona: és cel, i porta un gradient pel camp.

**Causa.** El cel no es restava, i el gra blau és el soroll de crominància del
canal blau amplificat per la matriu de blanc inventada de la recepta antiga.

**Correcció parcial.** La neutralització física (vegeu més avall) treu el
biaix de color del gra. El **model de cel** —una quàdrica per canal ajustada a
`r > 8,5 R☉`— es calcula i **es lliura com a capa** (`05_Model_de_cel`), però
**no es resta al compost principal**.

⚠️ **Per què no es resta.** Restar-la deixa residus de baixa freqüència més
lletjos que el gradient original: la quàdrica està constreta només al camp
exterior i cap endins és extrapolació. El fons d'aquest camp **no és una
quàdrica**: és cel més **vinyetatge**, i el vinyetatge té la seva pròpia
correcció mesurada i validada —el `MASTER_OPTICAL_RADIAL` Sony de
`research/90`— que **encara no s'ha aplicat**.

**Deute obert i quantificat.** Al compost nou queda una variació de color
radial del **≈30 %** entre 1,8 i 5,8 R☉ (contra el 108 % d'abans). La causa
dominant és el flat òptic Sony no aplicat. **No es pot arreglar en aquest
punt de la cadena**: flat i warp no commuten, i l'apilat v3 ja està registrat.
Es resol a la branca nova que recalibra des dels RAW, que és el gate S6.

**Regla.** *Un model de fons només val dins el domini on s'ha ajustat. Si el
que sobra és vinyetatge, la correcció és el flat i va abans de l'apilat, no
una quàdrica després.*

---

## D — Anell prim al limbe *(no marcat; detectat mesurant)*

**Mesura.** La màscara antiga tallava a **0,985 R☉ del Sol**. El disc **lunar**
mesurat al limbe, ajustant un cercle a 144 azimuts, té **R = 305,24 px =
1,019 R☉** i el seu centre és a 0,28 px del Sol astromètric. Entre 0,985 i
1,019 R☉ hi queda un anell de 10 px on la màscara deixava passar el que hi
hagués a sota.

**Causa.** Confondre el disc del Sol amb el disc de la Lluna. Amb magnitud
local 1,03 no són el mateix cercle, i durant la totalitat tampoc són
concèntrics.

**Correcció.** El tall surt del **disc lunar mesurat**, amb 6 px de marge.

**Regla.** *El que tapa el Sol és la Lluna. Tota màscara de limbe es mesura al
limbe, no es dedueix de R☉.*

---

## E — L'apodització de vores es menja la corona interior *(no marcat; el pitjor dels sis)*

**Què passava.** La corona interior sortia multiplicada per **0,03 a 1,05 R☉**
i per **0,20 a 1,2 R☉**. El perfil radial del compost quedava **invertit**: el
màxim no era al limbe sinó a 2 R☉. Justament la part que la Vixen aporta.

**Causa.** L'apodització de vores es calculava amb una transformada de
distància sobre **la cobertura** de la Vixen. La cobertura té el **forat de la
Lluna** i, a la corona interior, **forats de saturació** emmascarats fotograma
a fotograma. Per a la transformada de distància, cada forat és una vora: el
resultat és un polígon fosc de vores dentades que envolta el disc.

Es va caure dues vegades la mateixa nit: primer amb el forat de la Lluna, i
després —havent-lo tapat— amb els forats de saturació.

**Correcció.** L'apodització es mesura sobre **el marc del fotograma**: el warp
d'una imatge de uns amb la mateixa matriu. Res més.

**Resultat.** El perfil radial torna a ser monòton: **2,35×10⁻⁶ B/B☉ a
1,05 R☉ → 1,29×10⁻⁸ a 4 R☉**.

⚠️ **La recepta original de la branca Gemini té aquest defecte**
(`vixen_valid = vix_warp[:, :, 0] > 0`). Qualsevol reproducció d'aquella
cadena l'arrossega.

**Regla.** *Una transformada de distància respon «a quina distància ets del
zero més proper». Si el que vols és la vora del sensor, la màscara d'entrada
ha de ser el sensor sencer, no les dades. Mai facis `distanceTransform`
sobre un mapa de cobertura o de validesa de píxel.*

---

## F — Anells d'escaló d'exposició dins el màster Vixen *(no marcat; és de l'entrada)*

**Què es veu.** Amb guany radial, entre **1,05 i 1,6 R☉** apareixen estries
circulars concèntriques al voltant del disc.

**On és.** **A `hdr_vixen_countss.npy` mateix**, no al muntatge: es veuen
igual renderitzant només aquella matriu, sense res del pipeline de composició.

**Causa probable.** Residus dels esglaons de la fusió HDR de les quinze
exposicions a la zona on el fotograma llarg satura i el curt pren el relleu.
És exactament el terreny que la línia CapesTotals V4 de Kimi ataca amb el
revelat normalitzat.

**No es corregeix aquí.** Corregir-ho a la composició seria pintar-hi a sobre.
Es corregeix refent la fusió HDR aigües amunt.

**Regla.** *Abans de culpar la composició, renderitza l'entrada sola amb el
mateix estirament. Si l'artefacte hi és, no és teu i no s'arregla aquí.*

---

## El que sí que és calibratge, i no un ajust

Els dos trens passen a **B/B☉** amb els factors de `research/75` §5.2, mesurats
amb 38 i 22 estrelles: **Sony 1,134×10⁻¹¹** i **R6 2,772×10⁻¹¹** per ADU/s i
píxel verd, ±10 % cadascun.

**Comprovació que tanca l'escala.** El quocient verd Sony/Vixen mesurat a
l'anell de solapament és **2,605**. Els dos factors absoluts, amb el quocient
de corona **0,95** que el mateix document mesura entre 1,15 i 3 R☉, prediuen
**2,573**. **Coincideixen a l'1,2 %.** O sigui que l'escala entre trens ja no
és un paràmetre lliure que s'ajusta: és una mesura que es comprova.

**La neutralització també és física, no estètica.** La corona és llum solar
dispersada per electrons lliures: la dispersió Thomson és acromàtica. Els
factors calibren el canal **verd**; R i B es reescalen perquè la corona a
1,8–2,2 R☉ surti neutra. Aquest és el color que la física diu que ha de tenir.

⛔ **Les matrius `cam2srgb` de la branca Gemini són nombres inventats**, i a
sobre diferents per a cada tren. Són l'origen material de l'artefacte B.

---

## Ordre correcte de les operacions

1. **registre** — matriu de les dues solucions de placa, no de sis estrelles
   soltes; i comprovar-la amb el **disc lunar** (`research/92`);
2. **calibratge absolut** a B/B☉, per tren;
3. **escaló entre zones de cobertura** de cada apilat;
4. **igualació entre trens per canal**, guany i pedestal, a l'anell de
   solapament;
5. **neutralització** al radi de referència;
6. **màscares**: limbe al disc lunar mesurat; apodització sobre el marc del
   sensor; fusió per radi;
7. **detall** (MGN) sobre el compost lineal, mai sobre una capa sola;
8. **fons del cel**: com a capa, no restat, mentre el flat òptic no s'apliqui
   abans de l'apilat.

---

## El stack lliurat

`output/stack_calibrat_20260822/20260823T0130Z_v8/`, en **B/B☉ float32**:

| Fitxer | Què és |
|---|---|
| `01_Base_Sony_calibrada_BBsol_float32.tif` | base de gran camp, escaló de zones tret |
| `02_Overlay_Vixen_calibrada_BBsol_float32.tif` | Vixen registrada, igualada per canal i apoditzada |
| `03_Mascara_fusio_float32.tif` | pes de la Vixen |
| `04_Detall_MGN_gris50_uint16.tif` | detall MGN a sis escales, gris 50 %, per a *Linear Light* |
| `05_Model_de_cel_BBsol_float32.tif` | cel mesurat — **capa, no restat** |
| `06_Compost_LINEAL_BBsol_float32.tif` | el compost |
| `06b_Compost_LINEAL_sense_cel_BBsol_float32.tif` | el compost menys el cel (experimental, vegeu C) |
| `07_Mascara_validesa_float32.tif` | on hi ha dades modelades |
| `08_Compost_corba_declarada_uint16.tif` | 16 bits amb la corba escrita al manifest |

Eina: `research/tools/druckmuller_centre_corregit/build_stack_calibrat.py`.
Entorn: `~/Downloads/eclipse_venv` (Python 3.9.6, `sunkit-image` 0.5.1),
localitzat amb `detecta_python.py`, que no fixa cap intèrpret.

⚠️ **Continua `EXPERIMENTAL_NOT_CANONICAL`**: parteix d'apilats històrics i no
dels paquets S6, i l'apilat Sony v3 **ja fon `DSC06987` amb `DSC06993`**, o
sigui que les dues 8 s no hi són com a contribucions independents. El pilot S6
continua sent el gate següent, i ara té dos motius més per fer-se: el flat
òptic Sony (artefacte C) i la fusió HDR de la Vixen (artefacte F) només es
poden arreglar allà.
