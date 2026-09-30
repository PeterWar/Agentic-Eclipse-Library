# 108 — La maqueta V13 contra tota la recerca: el que ens ha encallat és la corba de to

Encàrrec de Pere, 26-08-2026: «hem de desencallar aquest projecte; torna't a mirar
CapesTotals13, que és l'últim projecte que visualment era acceptable, l'hem d'agafar com a
maqueta; contraposa el que hi ha a tota la recerca que hem fet».

Tot el que hi ha aquí és de **només lectura** sobre els actius: cap PSB, PSD, TIFF, NPY, RAW
ni producte s'ha modificat. Els fitxers nous són aquest document, l'eina
`research/tools/prova_aspecte_maqueta/prova_aspecte.py` i set vistes a
`~/Desktop/Eclipse 2026/IA/output/prova_aspecte_maqueta_20260826/`.

---

## 0. Resum en set línies

1. **`CapesTotals13.psb` no existeix.** Hi ha `CapesTotalsV13.psd` (21-08, 13:22) i
   `CapesTotalsV13_Pere.psd` (21-08, **14:21**). El bo és el segon: és el re-desat de Pere.
2. **El que Pere hi va fer a mà a les 14:21 és una corba de to**, i està mesurada aquí
   (§2): negres a terra, mitjos baixos amunt i **altes llums avall fins a −0,14**. És a dir,
   **menys pendent a la part brillant**.
3. **La maqueta diu exactament el mateix número.** El seu perfil demana **0,166 de nivell
   per dècada de B/B☉**; `estira_log`, que és el que fa la base de tots els lliuraments del
   25 i el 26, en fa **0,503**: **3,03 vegades més pendent** (§3).
4. **La conseqüència és aritmètica i és el defecte que es veu**: la dada abasta **3,92
   dècades** i l'estirament només n'ensenya **2,25**. Les **1,67 dècades de dalt** —un factor
   **47**— van a blanc: **329.659 píxels a 0,998 fins a 1,45 R☉**. La cromosfera, la
   protuberància i tota la corona interior són un borrall blanc. I les de baix es fonen: a
   3,7 R☉ el nivell és 0,092 contra 0,212 de la maqueta.
5. **⛔ Regressió documentada**: `research/93` (23-08) ja tenia les cures d'aquest defecte
   —igualació entre trens **per canal**, neutralització a 1,8–2,2 R☉, cel com a **model per
   canal**, ordre de vuit operacions— i el pilot del 23 al 26 **no les va heretar**. Mesurat
   avui: l'escalar únic ×1,119 que fa servir `munta_photoshop.py --igualar-trens` deixa la
   Sony amb **el R un 19 % baix i el B del 19 al 35 % alt** respecte de la Vixen, sobre el
   mateix cel i al mateix radi (§4).
6. **La causa arrel de §5 és de calibratge**: els factors absoluts de `research/75` §5.2 són
   **per píxel VERD**. R i B viatgen en espai de càmera cru i **els dos cossos no hi
   coincideixen**. No és un error de ningú: és un pas que no té amo.
7. **La dada bona SÍ que fa la foto bona.** La prova d'aspecte (§6) agafa el compost calibrat
   del 25-08 sense tocar-lo, hi aplica l'ordre del 93 i la corba de la maqueta, i surt la
   imatge que Pere vol: sense limbe cremat, sense costura, amb els plomalls fins a ~4 R☉.

---

## 1. Quin fitxer és, i què hi ha a dins

| | `CapesTotalsV13.psd` | `CapesTotalsV13_Pere.psd` |
|---|---|---|
| data | 21-08-2026 13:22 | 21-08-2026 **14:21** |
| bytes | 1.532.027.498 | 1.532.338.660 |
| SHA-256 | `f76c6d7bdf33abc4…` | `dc57861cbac1742c…` |
| disc lunar (nivell mostrat) | **0,137** | **0,024** |

Els dos són **7648×5353, 16 bits, 12 capes planes** —cap grup, cap capa d'ajust—, del
`12_1/3200` a la `01_10,3 s`, totes visibles i totes amb màscara. Els noms encara porten les
etiquetes de la V2 (`QUARANTENA OCULTA · REBUTJADA`): són literals morts, no un estat.

`research/87` §1 ja havia dit què és la V13 —«V9 → blur 10/25/50; el Levels 128 tenia el
descriptor invàlid»— i que **rentava la Lluna**: el disc a 8.700/65535. Això és cert de
`CapesTotalsV13.psd`. **⏭️ Rectificació: no és cert del que Pere va desar una hora després.**
El `_Pere` té el disc a 0,024, o sigui que **Pere ja havia arreglat el rentat de la Lluna a
mà**, i el veredicte «No serveix» de `research/87` s'ha de llegir com a veredicte del
**pedigrí** (V3…V13 són experiments d'Antigravity sense rebut), no de l'aspecte.

⚠️ El marc blanc que envolta la imatge no és un defecte de composició: és el **marge blanc de
les capes 1/500 i 1/125**, que tenen la bbox del llenç sencer amb la imatge a les columnes
458–7417 i les files 464–5103 (`research/87` §2, torre-de-pisa T5). Els cantons valen 1,000
exacte als dos fitxers.

---

## 2. El que Pere hi va fer a mà a les 14:21 ÉS la mesura del que vol

El 78,9 % dels píxels canvien entre les 13:22 i les 14:21, i no és cap pinzell: és una corba
global. Mediana per calaix de nivell:

| V13 | 0,14 | 0,16 | 0,31 | 0,49 | **0,64** | 0,76 | 0,81 | 0,91 |
|---|---|---|---|---|---|---|---|---|
| V13_Pere | **0,03** | 0,19 | 0,36 | 0,51 | **0,64** | 0,71 | **0,67** | **0,81** |

Llegit per zones: dins el disc 0,137 → 0,024; al limbe 0,568 → 0,303; a la corona interior
0,838 → 0,688; i al camp llunyà 0,445 → **0,474**, o sigui **amunt**.

**Traducció:** negre a terra, ombres amunt, **altes llums avall**. És una corba de **menys
pendent a la part brillant i més a la fosca**. És, exactament, el que la maqueta demana i el
que `estira_log` fa al revés.

---

## 3. La mesura que ho decideix: el nivell mostrat contra la brillantor real

Perfil radial del **nivell mostrat** (0–1), amb el centre lunar mesurat a cada fitxer:

| r (R☉) | maqueta | V13_Pere | lliurament 26-08 | B/B☉ mesurat |
|---|---|---|---|---|
| 1,09 | 0,631 | 0,518 | **0,998** | 1,61·10⁻⁶ |
| 1,62 | 0,510 | 0,689 | 0,561 | 7,28·10⁻⁸ |
| 2,15 | 0,404 | 0,719 | 0,263 | 1,96·10⁻⁸ |
| 2,68 | 0,297 | 0,640 | 0,160 | 1,25·10⁻⁸ |
| 3,74 | 0,212 | 0,484 | 0,092 | 9,26·10⁻⁹ |
| 5,33 | 0,175 | 0,429 | 0,061 | 8,11·10⁻⁹ |
| 8,51 | 0,133 | — | 0,041 | 7,56·10⁻⁹ |

Ajust del nivell contra `ln B` entre 1,1 i 3,0 R☉:

| | pendent per dècada de B/B☉ | r |
|---|---|---|
| **maqueta de Pere** | **0,166** | 0,894 |
| **lliurament 26-08** (`estira_log`) | **0,503** | 0,998 |

**⛔ El defecte és aquest sol número, i tota la resta en surt.** `estira_log` tria els extrems
amb percentils `[0,5 · 99,7]` de `ln B` sobre la regió amb dada. Sobre el llenç del pilot això
dona un rang de **2,25 dècades**, quan la dada n'abasta **3,92** (del píxel més brillant del
limbe, 6,19·10⁻⁵, al cel, 7,5·10⁻⁹):

- **es cremen 1,67 dècades**, un factor 47: **329.659 píxels a ≥0,999**, fins a **1,45 R☉**.
  Dins d'aquest cercle hi ha la cromosfera, la protuberància i tota la corona interior;
- **s'ensorra el que queda**: amb 3,03 vegades massa pendent, a 3,7 R☉ el nivell cau a 0,092
  quan la maqueta el vol a 0,212, i la corona exterior desapareix en negre.

⚠️ **La V13 falla per l'altre costat i també és mesurable**: el seu perfil **no és
monòton** —0,518 al limbe, **màxim 0,731 a 2,0 R☉**—, o sigui que **la corona interior hi
és més fosca que la mitjana**. És el vel de la capa de 10,3 s que `research/87` §1 descriu
(màscara 0,33 dins el disc i 0,50 al limbe). I el cel no s'hi treu: el fons val 0,40–0,55.
**La V13 no és el producte; és la corba de to del producte.**

---

## 4. La regressió del 23 al 26: el 93 ja tenia les cures

`research/93` (23-08) va catalogar sis artefactes de composició amb la seva regla i el seu
ordre de vuit operacions. El pilot que comença el mateix dia (`research/97`→`107`) reconstrueix
la cadena **des de zero i amb la Vixen sola**, i quan hi torna a entrar la Sony (24-08) no
recupera tres d'aquelles regles. Mesurat avui sobre el compost del 25-08:

### 4.1 Igualació entre trens: un escalar de luminància on calen tres

`munta_photoshop.py --igualar-trens` divideix la Sony pel quocient **verd** per radi
(mediana ×1,11937). Sobre el **mateix cel** i al **mateix radi**, els dos trens no hi
coincideixen de color:

| anell | Vixen R/G | Sony R/G | Vixen B/G | Sony B/G |
|---|---|---|---|---|
| 2,0–2,5 R☉ | 0,649 | 0,526 (**−19 %**) | 0,404 | 0,479 (**+19 %**) |
| 3,0–3,5 R☉ | 0,541 | 0,440 (−19 %) | 0,438 | 0,569 (+30 %) |
| 4,5–5,5 R☉ | 0,485 | 0,391 (−19 %) | 0,457 | 0,617 (**+35 %**) |

Ajustant **guany i pedestal per canal** a l'anell de solapament 1,5–2,8 R☉, com mana
`research/93` §B, surten guanys **1,0737 · 0,8576 · 0,9035** —quan l'escalar únic diria
0,8934 als tres— i el residu cau a **G +0,15 %, R/G −0,06 %, B/G +0,09 %** a 2,0–2,5 R☉ i a
**~1,2 %** a 4,5–5,5. És el 0,64 % del 93, reproduït sobre la dada nova.

**⛔ Amb l'escalar únic, la costura entre petjades és invisible en verd i és un graó de color
del 19 al 35 % en vermell i blau.** La vista `6_lliurament_26-08_en_color…jpg` ho ensenya
sense cap mesura: la petjada Sony hi és blava i la Vixen, verdosa.

**Causa arrel, i no és de ningú d'aquesta ronda:** els factors absoluts de `research/75` §5.2
—Sony 1,134·10⁻¹¹ i R6 2,772·10⁻¹¹— són **per ADU/s i píxel VERD**. R i B no estan calibrats;
viatgen en espai de càmera cru, i dos cossos amb filtres de Bayer diferents **no poden
coincidir** sobre un cel blau. `research/93` ho resolia amb la **neutralització** (R i B
reescalats perquè la corona a 1,8–2,2 R☉ surti neutra, que és el color que la dispersió
Thomson imposa). El pilot no la fa: per això la seva capa `00` és grisa.

### 4.2 El cel: una constant on cal una quàdrica per canal

`cel_per_asimptota` treu **un sol número** (1,208·10⁻⁸). Però el cel té gradient: ajustant una
quàdrica 2-D per canal al camp llunyà del mateix retall, el fons **varia un 27,6 % en verd i
un 63–65 % en vermell i blau** d'una punta a l'altra. Restar-ne una constant deixa residus de
signe contrari a cada canal, i és exactament el que es veu a la capa `00b` del lliurament
(`7_lliurament_26-08_cel_tret_per_asimptota.jpg`): un borrall blanc amb la vora esfilagarsada
i una diagonal de residu.

⏭️ `research/93` §C ja ho tenia: **quàdrica per canal ajustada a r > 8,5 R☉, lliurada com a
CAPA i no restada**. La regla del 93 —«un model de fons només val dins el domini on s'ha
ajustat»— continua sent la bona.

### 4.3 L'enquadrament: 77 % de llenç sense dada

El llenç comú fa **10450×12878 px = 23,7 × 29,2 R☉**, i el muntatge del 26-08 el treu sencer
(`--radi-max 15`). **Només el 23 % té dada de la Vixen**; la resta és marge. La maqueta fa
±7,6 × ±4,9 R☉ i la V13 ±8,7 × ±6,1, totes dues **apaïsades 3:2**.

**No és un problema de dada.** Mesurat: la caixa 3:2 més gran centrada al Sol **amb el 100 %
de cobertura** dels dos trens és de **7560×5040 px = ±8,58 × ±5,72 R☉** — més gran que la
maqueta i pràcticament la de la V13. L'enquadrament que Pere vol hi cap sencer.

---

## 5. Contraposició, punt per punt

| | V13_Pere (21-08) | pilot 25/26-08 | qui té raó |
|---|---|---|---|
| corba de to | pendent suau, però **perfil NO monòton** | 2,25 dècades, **crema 1,67** | cap: la bona és la de la maqueta, 0,166/dècada sobre 3,92 dècades |
| limbe | net, sense cremar | **0,998 fins a 1,45 R☉** | V13 |
| corona interior | **envelada** per la capa de 10,3 s | correcta i mesurada | pilot |
| enquadrament | 3:2, Sol ben posat | quadrat o vertical, 77 % buit | V13 |
| costura entre trens | no n'hi ha (només Vixen) | **graó de color 19–35 %** | cap: la cura és el 93 §B |
| cel | **no tret**, fons a 0,45 | constant restada → residus | cap: la cura és el 93 §C |
| color | de l'ACR, sense rebut | **cap**: base grisa | cap: la cura és la neutralització del 93 |
| detall | **no n'hi ha** | fase 3 auditada (106/107) | pilot |
| fotometria | cap: ADU d'ACR sense normalitzar | **B/B☉ ±10 %**, portes F/E/G/H | pilot |
| registre | 1 px de torre de Pisa (`87` §2) | 0,21 px entre trens (`99`) | pilot |

**En una frase:** la V13 té l'**aspecte** i cap **dada**; el pilot té la **dada** i cap
**aspecte**. Cap dels dos és el producte, i el pont —l'ordre d'operacions— ja estava escrit el
23 d'agost a `research/93`.

---

## 6. La prova d'aspecte: la dada bona amb l'ordre del 93

`research/tools/prova_aspecte_maqueta/prova_aspecte.py`. Llegeix el compost calibrat del
25-08 **sense modificar-lo** i fa, per aquest ordre: retall 3:2 a l'enquadrament de la maqueta
· igualació entre trens **per canal** · costura amb rampa des de la vora de la petjada Vixen
amb els forats interiors plens abans · **neutralització** a 1,8–2,2 R☉ · **cel per quàdrica
per canal** · mapa logarítmic de **pendent declarat 0,175/dècada** ancorat a 1,05–1,15 R☉ ·
detall de la fase 3 sumat **en logaritme** (que és una raó, no una suma).

Resultat: `3_PROVA_ASPECTE_calid.jpg` i `4_..._natural.jpg`, 6654×4436.

- limbe **no cremat**, cromosfera i protuberància visibles;
- plomalls polars i serpentines fins a ~4 R☉;
- **cap costura visible** i cap taca de color;
- cel fosc amb gradient suau, corona neutra (versió natural) o tèbia (versió càlida).

⚠️ **Què NO és això.** No és un lliurable ni una mesura: és una prova que la dada aguanta
l'aspecte. La versió càlida multiplica el nivell per (1,045 · 1,00 · 0,90): **és estètica pura
i és una decisió de Pere sota D1**, no física. I la quàdrica del cel s'hi ajusta a r > 6 R☉,
on la corona encara hi és a un ~11 % (`research/99`): plana lleugerament la corona exterior.
Amb el camp sencer de la Sony el domini d'ajust ha de tornar a r > 8,5 R☉ com al 93.

---

## 7. Què proposo, per ordre

1. **Adoptar la corba de to com a paràmetre declarat i no derivat.** Substituir els percentils
   d'`estira_log` per **pendent + àncora + terra**, escrits al rebut. El número de partida és
   el mesurat aquí: **0,17 de nivell per dècada de B/B☉, àncora 0,68 a 1,05–1,15 R☉**.
   ⛔ Cap estirament pot cremar: el sostre s'ha de treure del **màxim de la dada**, no d'un
   percentil.
2. **Tornar a posar les tres regles del 93** al muntatge: igualació **per canal**,
   neutralització a 1,8–2,2 R☉ i cel com a **model per canal**, lliurat com a capa.
3. **Retallar.** El llenç de lliurament és el 3:2 de ±8,5 × ±5,7 R☉, que és on hi ha el
   100 % de dada. El llenç comú de 23,7 × 29,2 R☉ és de treball, no de lliurament.
4. **Calibrar R i B, o declarar que no ho estan.** És el deute que hi ha sota §4.1 i el que
   fa que la neutralització sigui obligatòria en lloc d'opcional.
5. **El PSB per a Pere surt d'aquí**: base neutra + capa de cel + capa de detall + capa de
   tebior, totes separables, i el timó tonal a les seves mans. És el que Fable 5 va proposar
   el 26 a la matinada («el timó passa al Photoshop de Pere») i ara té una base que ho aguanta.

⏭️ Res d'això toca l'artefacte del `107`. El terç irreductible continua sent-ho, i amb la
corba de la maqueta —tres vegades menys pendent— **es veu tres vegades menys**.

---

## 8. Rebut

- Llegit i no modificat: `CapesTotalsV13.psd`, `CapesTotalsV13_Pere.psd`,
  `Maqueta de resultat esperat.tif`, `output/pilot_vixen_fable_20260825_lliurament/`
  (`photoshop_complet/`, `photoshop_mediana/`, `dos_trens/`, `dos_trens_filtrats/`),
  `output/pilot_vixen_claude_20260824/sony_llenc_comu_coh/`,
  `output/stack_calibrat_20260822/20260823T0410Z_conn2/`.
- Escrit: aquest document, `research/tools/prova_aspecte_maqueta/prova_aspecte.py`, i set
  vistes a `~/Desktop/Eclipse 2026/IA/output/prova_aspecte_maqueta_20260826/`.
- Zero contacte amb càmeres, PTP, GUI o Photoshop. Zero processos vius al final.
