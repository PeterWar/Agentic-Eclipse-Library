# 109 · El color de Brno, mesurat sobre els seus composts del NOSTRE eclipsi

**Data:** 26 d'agost de 2026. **Pregunta de Pere:** *«com ho resol això l'equip
de Druckmüller?»*, i tot seguit *«t'he guardat les imatges a Fotos Finals,
estudia-les amb deteniment»*.

**Material:** quatre composts publicats de l'eclipsi del **12-08-2026** des de
**Pico Trigaza** (Burgos, Sol a **8,01°** a C2 — el nostre a León, molt a prop),
a `~/Desktop/Eclipse 2026/Drukmuller fotos finals/`: 200, 400, 530 i 800 mm.
PNG de ~1500 px, sRGB sense perfil incrustat.

**Mètode:** `research/tools/estudi_druckmuller/` (5 scripts). Centre i radi
lunars pel **màxim de gradient radial abans del cim de brillantor** —sense cap
llindar, perquè tres dels quatre porten earthshine i la Lluna hi és més clara
que el cel de les cantonades—. Validació independent: els radis lunars de
200:400:530 mm surten en proporció **1,961 : 2,629** contra els **2,00 : 2,65**
que manen les focals (**2 %**), i el radi mesurat val **R_Lluna/R_Sol = 1,0324**
contra el **1,0335** de l'efemèride (**0,1 %**).

⚠️ Els anells que surten del rectangle es declaren per **cobertura**; res del
que hi ha per sota del 100 % de cobertura no s'usa com a absolut (és la trampa
de l'NRGF del `100`).

---

## 1. La resposta: la corona es lliura NEUTRA i el cel es deixa BLAU

Mesura del **color de l'estructura** —brillants menys foscos del mateix anell,
o sigui amb el cel cancel·lat per construcció— entre 1,05 i 5,0 R☉, només
anells sencers:

| Compost | EST R/G | EST B/G |
|---|---:|---:|
| Trigaza 800 mm | **1,013** | 0,960 |
| 530 mm | **0,999** | 0,994 |
| 400 mm | **1,022** | 0,958 |
| 200 mm | **1,010** | 0,947 |
| **el nostre (dada lineal)** | **1,765** | **0,497** |

**Quatre composts, dues càmeres, quatre òptiques: la corona és neutra a ±5 %.**
És el que la física demana —la corona K és dispersió de Thomson, **acromàtica**
(`research/105` §4)— i el que Brno lliura.

I el cel **no el resten**: el deixen posat i és blau.

| Compost | color del cel (lineal) R/G | B/G |
|---|---:|---:|
| 530 mm a 4,6 R☉ | 0,565 | 2,087 |
| 400 mm a 5,5 R☉ | 0,559 | 2,064 |
| 200 mm a 9,7 R☉ | 0,528 | 2,060 |
| **el nostre `b_cel / s_corona`** | **0,577** | **1,764** |

⏭️ **Aquesta última fila ho tanca.** El nostre cel mesurat és
`b = (1,0122 · 1 · 0,8786)` i la nostra corona `s = (1,7547 · 1 · 0,4982)`. El
quocient dona **0,577 · 1,764**, i el cel que Brno lliura val **0,53-0,57 ·
2,06**. **El R/G coincideix al 3 %** amb una mesura nostra feta per un mètode
completament diferent (la descomposició de dos vectors del `100` §D). El B/G
queda un 15 % més blau a Trigaza, cosa esperable: 1655 m contra els nostres
798 m, o sigui menys aerosol.

**Conclusió:** `s_corona` **no és el color de la corona: és la resposta de
l'instrument i de l'atmosfera.** Dividir-hi deixa la corona neutra **i alhora**
posa el cel al blau que Brno mesura. Un sol número explica les dues coses.

## 2. El control que ho demostra: què queda després de dividir

⛔ Una normalització que esborri tot el color no serveix de res. El control és
si sobreviu la física que sabem que hi ha.

| Prova | Resultat |
|---|---|
| **el continu queda neutre?** | `u_R/u_G` **0,977–1,010** i `u_B/u_G` **0,987–1,052** d'1,1 a 4 R☉. **Un sol vector constant se n'endú tot.** |
| **les protuberàncies continuen vermelles?** | **SÍ**: a l'anell 1,00–1,06 R☉, `u_R/u_G` p99,9 = **3,74**, màxim **5,44**, i el **9,86 %** de l'anell passa d'1,5, concentrat a **dos grups d'azimut** (130–150° i 220–240°). És Hα, i sobreviu. |
| **hi ha Fe XIV (corona E)?** | **+0,29 / +0,49 / +0,31 %** d'excés verd a 1,06–1,20, 1,20–1,40 i 1,40–1,60 R☉, i **negatiu** a fora. Signe i radi correctes. |

**Traiem l'instrument i deixem la física.** ⚠️ Però el Fe XIV val **+0,4 %**
contra un soroll cromàtic per píxel de **1,8–4,6 %**: **no és visible píxel a
píxel**, només en mitjana. Per això Brno fa el **color a baixa freqüència** i
el multiplica per **×50–400**.

## 3. La corba de to de Brno, mesurada

Nivell mostrat (sRGB 0–1) contra el B/B☉ del mateix eclipsi (taula del `108` §3):

| r (R☉) | 800 mm | 530 mm | 400 mm | 200 mm | maqueta | V13 | nostre 26-08 |
|---|---|---|---|---|---|---|---|
| 1,09 | 0,710 | 0,742 | 0,713 | — | 0,631 | 0,518 | **0,998** |
| 1,62 | 0,435 | 0,459 | 0,466 | 0,481 | 0,510 | 0,689 | 0,561 |
| 2,15 | 0,276 | 0,302 | 0,333 | 0,344 | 0,404 | 0,719 | 0,263 |
| 2,68 | 0,233 | 0,258 | 0,293 | 0,303 | 0,297 | 0,640 | 0,160 |
| 3,74 | — | 0,228 | 0,257 | 0,276 | 0,212 | 0,484 | 0,092 |
| 5,33 | — | — | 0,228 | 0,258 | 0,175 | 0,429 | 0,061 |
| 8,51 | — | — | — | 0,251 | 0,133 | 0,041 | 0,041 |

Pendent de nivell per dècada de B/B☉ entre 1,1 i 3,0 R☉:

| | pendent | r |
|---|---:|---:|
| 800 mm | 0,233 | 0,998 |
| 530 mm | 0,240 | 0,998 |
| 400 mm | 0,202 | 0,998 |
| 200 mm | 0,225 | 0,998 |
| maqueta de Pere (`108`) | 0,166 | 0,894 |
| **nostre lliurament 26-08** | **0,524** | 1,000 |

⏭️ **Brno va a 0,20–0,24 per dècada**, o sigui **entre la maqueta de Pere i
res més**: 2,2–2,6 vegades més suau que `estira_log`. La maqueta de Pere és
lleugerament més suau encara que Brno.

I tres coses de la forma que no es dedueixen del pendent:

1. ⛔ **NO CREMEN RES.** Excloent la línia blanca del marc, els quatre composts
   tenen **zero píxels a ≥0,99** dins la imatge. El seu cim val **0,72–0,76 a
   1,07 R☉**. El nostre del 26-08 en tenia **329.659 fins a 1,45 R☉**.
2. ⛔ **El terra NO és negre: és el cel**, a **0,216–0,250**. Tota la imatge
   viu entre 0,22 i 0,75, o sigui **mig rang de pantalla**. Res no cau a zero,
   i per això no hi ha **cap vora ni cap gradient lleig** al caire del camp.
3. **El recorregut útil és de només 0,49–0,54** en nivell. La imatge no és
   contrastada: és **suau i llarga**.

## 4. La Lluna

| Compost | disc (mediana) | relleu intern | cel |
|---|---:|---:|---:|
| 800 mm | **0,0000** | 0,000 | 0,220 |
| 530 mm | 0,1307 | 0,047 | 0,217 |
| 400 mm | 0,1229 | 0,086 | 0,229 |
| 200 mm | 0,1255 | 0,084 | 0,249 |

Tres dels quatre porten **earthshine amb els mars visibles**, a **la meitat del
nivell del cel**. La Lluna hi és un disc gris fosc, **no un forat negre**. El de
800 mm sí que la posa negra i és allà on la seva pàgina diu que el negre «no és
un cercle sinó la intersecció de dos cercles» (mesurat: el radi hi varia un
**3,9 %**, contra l'1,4 % del 530 mm).

## 5. Prova sobre la nostra dada

`research/tools/estudi_druckmuller/prova_brno2.py`. ⚠️ **No és cap lliurable ni
cap mesura.** Recepta:

```
u   = (CORONA + CEL) / s_corona      el cel NO es resta: el terra ha de ser cel
L   = (u_R + 2 u_G + u_B) / 4        una sola lluminància
q   = suau(u, σ=24 px) / suau(L)     color de BAIXA FREQÜÈNCIA (Brno)
y   = corba declarada sobre L        corba ESCALAR, mai per canal
RGB = srgb( lineal(y) · (1 + s·(q−1)) )
```

⚠️ **El croma s'aplica en LINEAL i es torna a codificar.** Aplicat sobre el
valor de pantalla, el cel sortia amb B/R = **3,06** quan Brno en fa **1,87**.

Resultat mesurat amb la mateixa vara (`pend 0,24 · àncora 0,75`):

| r | nostre nou | Brno 400 mm |
|---|---|---|
| 1,2 | R/G 1,005 · B/G 1,007 | R/G 1,012 · B/G 0,986 |
| 8,2 | R/G 0,572 · B/G 1,774 | R/G 0,528 · B/G 2,060 (200 mm) |
| nivell 1,5 → 5,0 | 0,444 → 0,261 | 0,470 → 0,228 |

Vistes a `2-OUTPUT/ESTUDI_DRUCKMULLER/` (`COMPARATIVA_BRNO.png`,
`PROVA_BRNO_brno_x8.png`), sempre **llenç sencer**.

## 6. El que se n'aprèn, per ordre

1. ⏭️ **`s_corona` és instrument, no corona.** Dividir-hi és obligatori, i té
   control propi (§2). Això **substitueix** la proposta de la lluminància que
   jo havia fet i **coincideix amb la recomposició de Codex** (`u = C/s`),
   derivada per un altre camí.
2. ⏭️ **El cel no s'ha de restar al producte visual.** Restar-lo és el que
   fabrica el terra negre, la vora dura i el gradient que Pere va marcar. El
   producte **científic** continua sent els FITS lineals amb el cel restat: són
   **dos productes, no un**.
3. ⏭️ **Corba escalar sobre una lluminància, pendent 0,20–0,24, cim a ~0,75,
   terra = cel.** Mai per canal (això fa monocroma, `108`) i mai per percentils
   (això crema, `108`).
4. ⏭️ **El croma va a baixa freqüència i en lineal.** El residu útil és de
   0,4 % contra 2–5 % de soroll: sense suavitzar no és senyal.
5. ⏭️ **La Lluna ha de portar earthshine**, a la meitat del nivell del cel.
   És el millor material de la flota (`research/72`) i avui és un forat negre.
6. ⚠️ **Que la corona surti neutra NO demostra que no hi hagi extinció.**
   A X ≈ 6,5 l'extinció diferencial R−B val ~1,4 mag, que és exactament el
   factor 3,55 que mesurem. La normalització per `s_corona` l'absorbeix junt
   amb la resposta de la càmera i **no els separa**. ⛔ Per tant `s_corona`
   **no és un calibratge de color**: és un punt blanc pres sobre l'únic objecte
   del camp del qual sabem el color a priori.
7. ⛔ **Cau la porta del `comu.py` que declara «sospitosa» una corona neutra.**
   La dada no demostra que R/G 1,76 sigui extinció, i Brno lliura neutre.
   Codex ho havia dit; això ho confirma amb mesura.

## 7. El que la prova encara NO resol

- **Soroll**: el nostre camp mitjà (2–5 R☉) surt granulós i el seu és llis. El
  passa-alt amplifica on el senyal/soroll és baix; el seu ACHF és adaptatiu.
- **Abast de l'estructura**: els seus plomalls arriben a la vora del camp; els
  nostres moren cap a 3 R☉.
- **L'anell fosc a ~1,05 R☉** de la prova és un artefacte del passa-alt contra
  la vora de la màscara lunar, no de la recepta de color.
- **El cel nostre pesa més**: el recorregut ens queda a 0,44 → 0,26 contra
  0,47 → 0,23. Part és el lloc (798 m contra 1655) i part és per ajustar.

---

# ADDENDA · El repàs del balanç de blancs, i dos defectes nostres

**Demanat per Pere:** *«els raws han d'estar tots el daylight balance, i no he
tocat res, però valdria la pena que ho repassessis. Crec que la millor base per
a estudiar el color que vaig veure és DSC06991.ARW»*.

## 8. El repàs: Pere té raó

`WhiteBalance: Daylight` a l'EXIF dels **dos** cossos, i el Canon ho demostra
amb els seus propis nivells:

```
WB_RGGBLevelsAsShot:   1990 1024 1024 1699
WB_RGGBLevelsDaylight: 1997 1024 1024 1742      -> 0,35 % i 2,5 %
```

⚠️ El que **sí** que difereix és el `daylight_whitebalance` de **LibRaw**
(2,1678 · 1 · 1,3555) contra el «Daylight» del propi Canon (1,950 · 1 · 1,701):
**11 % més de vermell i 20 % menys de blau**. No és cap contradicció: són dues
coses diferents, i cadascuna només val **acompanyada de la seva matriu**.

## 9. ⛔ Defecte 1: apliquem el balanç SENSE la matriu de color

Els multiplicadors sols no són colorimetria. Amb la matriu de la R6 III
—convenció dcraw: es normalitzen les files de la matriu **endavant**
(sRGB→cam) i després s'inverteix— la corona del compost passa de

| | R/G | B/G |
|---|---:|---:|
| sense matriu (el que lliuràvem) | 1,755 | **0,498** |
| **amb matriu (sRGB lineal)** | **1,928** | **0,194** |

**Rendíem la corona 2,6 vegades massa blava.** Era exactament el defecte que
Codex havia assenyalat («L no està definida colorimètricament») i que jo havia
apuntat sense corregir.

⚠️ I la convenció importa: normalitzant les files de la matriu **enrere**
(cam→sRGB) en lloc de l'endavant, el cel sortia **verdós**. És un error fàcil i
silenciós.

## 10. ⛔ Defecte 2: el negre declarat de la R6 III continua sent fals

`rawpy` declara `black_level_per_channel = [0, 29, 94, 61]`; el mesurat al
marge emmascarat és **[512, 512, 512, 512] pla**. És la trampa de
`research/71`, i és **viva**: revelant amb el negre de metadata, el R/G de la
corona externa **puja** fins a 2,68 a 9 R☉ i el cel surt magenta. La nostra
cadena mesura el pedestal i no hi cau; qualsevol revelat de tercers, sí.

## 11. La prova dels DOS COSSOS (la que demanava Pere)

`DSC06991.ARW` (Sony A7RIIIA · 300 mm f/2,8 · 1 s · 20:29:44) contra
`572A2996.CR3` (Canon R6 III · VSD90SS · 1 s · 20:30:04). **La mateixa
atmosfera, dos sensors i dues òptiques diferents.** Tot controlat a mà:
pedestal mesurat, binning 2×2 del mosaic sense interpolar, balanç de dia i
matriu, primàries sRGB lineals.

| r (R☉) | Sony R/G | Sony B/G | Canon R/G | Canon B/G | dif R/G | dif B/G |
|---|---:|---:|---:|---:|---:|---:|
| 2,20 | 1,817 | 0,431 | 1,591 | 0,372 | +14,2 % | +16,0 % |
| 2,60 | 1,654 | 0,503 | 1,376 | 0,506 | +20,1 % | **−0,6 %** |
| 3,10 | 1,398 | 0,615 | 1,216 | 0,599 | +15,0 % | **+2,7 %** |
| 3,70 | 1,305 | 0,655 | 1,157 | 0,632 | +12,8 % | **+3,6 %** |
| 4,40 | 1,230 | 0,687 | 1,066 | 0,681 | +15,4 % | **+0,9 %** |
| 5,20 | 1,124 | 0,731 | 1,032 | 0,697 | +9,0 % | +4,9 % |

**El B/G coincideix a menys del 5 %.** El R/G difereix un +9 a +20 % constant
(la Sony més vermella), que és el terme de **càmera i òptica** —vidre del
300 GM contra el del VSD90SS—. **El groc, doncs, és atmosfera.**

## 12. La predicció, ara feta bé

Espectre solar (Planck 5772 K) × transmissió atmosfèrica, integrat contra les
CIE 1931 i portat a sRGB lineal amb blanc D65:

| X | R/G | B/G |
|---|---:|---:|
| **0,00** | **1,075** | **0,888** |
| 4,00 | 1,516 | 0,400 |
| **6,12 (la nostra)** | **1,818** | **0,250** |

| mesurat | R/G | B/G |
|---|---:|---:|
| Canon 572A2996 a 1,70 R☉ (~5 % de cel) | **1,796** | **0,243** |
| compost Vixen amb matriu, cel restat | 1,928 | 0,194 |

**1,2 % i 2,8 % de desacord** amb el fotograma. ⚠️ **Rectificació (contrast de
Codex):** vaig escriure que «totes les mesures cauen dins la banda» i és FALS.
La banda de sensibilitat (AOD 0,18–0,30, α 1,0–1,6) dona R/G 1,71–1,95 i B/G
0,29–0,21, i el **B/G 0,194 del compost queda un 7,6 % PER SOTA** del límit
inferior. El que cau dins la banda és el **fotograma**, no el compost.

⏭️ **I una troballa que explica Druckmüller:** amb **zero atmosfera** la corona
tampoc no surt neutra contra D65, sinó **1,075 · 0,888**, perquè el Sol és de
5772 K i D65 de 6504 K. Que Brno la lliuri **exactament** neutra vol dir que
**es blanqueja sobre la corona mateixa**, no sobre D65. La seva neutralitat és
una **decisió declarada**, no una mesura.

## 13. ⚠️ El cel del GraduantColor NO és a la dada

| a 7–9 R☉, sRGB lineal | R/G | B/G |
|---|---:|---:|
| Sony DSC06991 | 1,03 | 0,77 |
| Canon 572A2996 | 0,97 | 0,73 |
| **GraduantColor.tif de Pere** | **0,58** | **1,24** |

Els **dos** cossos, amb pedestal mesurat i cadena de color sencera, diuen que
el cel de la totalitat era **càlid-neutre**, no blau — cosa esperable amb el
Sol a 9° i AOD 0,24. **El blau del GraduantColor no surt dels RAW**: ha
d'entrar al processat. El sospitós és la **resta del gradient de color
atmosfèric** (DBE/Subtract, `research/81`): si el que es resta és un gradient
càlid, el que queda es torna blau.

⚠️ Aquesta és l'única cosa d'aquesta ronda que **no queda resolta amb la dada**.


---

# ADDENDA 2 · El contrast de Codex i la tria del blanc (26-08, vespre)

Contrast demanat per Pere abans de fer els dos lliurables definitius.

## 14. La tria: el blanc és el SOL, no D65

| opció | corona resultant | veredicte |
|---|---|---|
| (a) D65 tal qual | 1,928 · 0,194 | control colorimètric, **no** «tal com es veia» |
| **(b) blanc sobre el Sol AM0** | **1,793 · 0,218** | ⏭️ **TRIADA** |
| (c) blanc sobre la corona (Brno) | 1,000 · 1,000 | auto-referencial |
| (d) corregida a X=1 | 1,242 · 0,560 | contrafactual |

**L'argument que ho decideix:** D65 és **llum diürna mitjana**, no el blanc al
qual l'ull de Pere estava adaptat. Dir «D65 = tal com es veia» seria fals. Amb
el **Sol** com a blanc adoptat, el que queda a la imatge és **l'extinció de
León** —més l'enrogiment propi de la F, les línies E i els residus
instrumentals—, i això sí que és una afirmació física.

Guany del mode `CIENCIA`: **1/(1,075 · 1 · 0,888) = (0,9302 · 1 · 1,1261)**.

⚠️ **El residu que queda**: la corona amb blanc AM0 val 1,7935 · 0,2185 i
l'extinció **sola** en prediu 1,691 · 0,2815. Sobra un **+6,1 % de vermell** i
falta un **−22,4 % de blau**. Això **no és soroll**: és corona F, línies E,
resposta instrumental i error de model, i **no es pot separar** amb tres bandes
amples. La separació K/F demanaria bandes de 0,5 nm i **polarimetria**, que és
justament l'observable que no tenim.

Per això el PSB de `CIENCIA` porta **dues** capes de diagnòstic i no una: la
`07` divideix per l'extinció **declarada** i la `08` pel color **mesurat** de la
corona (Brno). **La diferència entre les dues ÉS aquest residu.**

## 15. El control que decideix si el color del compost val

⏭️ **Tancament HDR**: el compost contra un **fotograma solt del mateix tren**,
als **MATEIXOS anells**. Implementat a `comu.tancament_hdr`, és porta de la
fase 3.

| anell (R☉) | compost R/G | foto R/G | dif | compost B/G | foto B/G | dif |
|---|---:|---:|---:|---:|---:|---:|
| 1,8–2,0 | 1,664 | 1,697 | −1,9 % | 0,309 | 0,303 | +1,9 % |
| 2,3–2,7 | 1,426 | 1,412 | +1,0 % | 0,500 | 0,485 | +3,2 % |
| 3,1–3,6 | 1,205 | 1,192 | +1,1 % | 0,633 | 0,612 | +3,5 % |
| 4,2–4,9 | 1,062 | 1,057 | +0,5 % | 0,712 | 0,685 | +4,0 % |

**Mediana R/G +0,8 %, B/G +3,5 %; pitjor 4,0 %. PASSA** (llindar 5 %).

⚠️ Codex l'havia donat per **NO PASSA provisional** (+7,35 % i −20,16 %) a
partir dels agregats que jo li havia enviat — i ell mateix advertia per què:
**comparar radis diferents barreja proporcions K/F distintes**. Amb els anells
igualats, tanca. **La lliçó és seva: un control de color s'ha de fer a la
mateixa obertura.**

## 16. Altres coses que Codex refuta i que quedaven a l'aire

- ⛔ «Planck + CIE + matriu dcraw» **no és calibratge espectral absolut**. El
  desacord vermell Sony/Canon (+9 a +20 %) ho demostra. Per a un definitiu
  caldria l'espectre solar **TSIS-1 HSRS** en lloc d'un cos negre.
- ⚠️ Els 20 s de separació i la coincidència en B fan **probable** un terme
  instrumental en R, però **no demostren** que sigui només càmera i vidre.
- ⚠️ El camp a 7–9 R☉ **no és cel pur**: és corona F + cel + llum dispersa, i
  amb aquestes dades no se separen.
- ⏭️ **I una troballa de Codex sobre el cel blau**: blanquejant sobre la corona
  (opció c), el nostre cel de **1,0 · 0,75** es convertiria en **≈0,52 · 3,87**.
  **El cel blau de Brno —i probablement el del `GraduantColor` de Pere— surt
  principalment d'haver blanquejat la corona, no de ser blau al RAW.** Això
  tanca el §13 sense necessitat de cap dada nova.
- El cel del producte visual ha de portar **el mateix blanc global** que la
  corona. Donar-li un blanc propi és etalonatge creatiu, no colorimetria.
