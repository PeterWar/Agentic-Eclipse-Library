# 115 · La Sony entra a la cadena (27-08-2026)

**Encàrrec de Pere**: incorporar el segon tren (A7RIIIA + FE 300 mm f/2,8 GM
sobre Skywatcher), començant per un run amb les imatges de quarantena fora.

## 1. La quarantena NO són fotogrames dolents: és l'altre apuntament

⛔ **Rectifica la premissa del pla.** Mesurat el limbe lunar als 32 fotogrames
(`research/tools/sony_entrada/apuntaments.py`, rebut a `apuntaments.json`):

| | fotogrames | centre al sensor | ovalitat del limbe |
|---|---|---|---|
| **apuntament A** | DSC06973–06987 (15) | x 3670, y 3484 (±3 px) | ~1,0 · nets |
| **el salt** | DSC06988, 06989 | x 3882 → 3895 | **3,7 i 4,9** |
| | **DSC06990** | l'ajust del limbe dona **R = 163 px** en lloc de 304 | trencat |
| **apuntament B** | DSC06991–07004 (14) | x 3895, y 2768 (±3 px) | ~1,1 · nets |

El salt és **(+224, −715) px = 749 px**, que confirma els +223 i −715 del
`research/72`. La carpeta `quarantena` són els 18 primers i `totalitat` els 14
últims: **el tall cau entre l'àncora 2 i la 3 d'earthshine**, que és on la
muntura va cedir.

⏭️ **La cadena registra fotograma a fotograma**, o sigui que dos apuntaments no
li fan cap mal: són un **dither**, i és el que `research/96` deia que pot
mesurar el flat. Treure la quarantena sencera costa **15 fotogrames bons** —el
bloc de contacte de C2 sencer (perles, diamant, cromosfera: 1/6400 · 1/800 ·
1/100 tres vegades) i **dues de les tres àncores d'earthshine**— per desfer-se
de 3.

⚠️ **DSC06991 i DSC06993 també van moguts** (ovalitat 2,56 i 3,60 contra 1,08
d'un 1 s net): són els dos primers de l'apuntament B, just després del salt.
**El DSC06991 és el testimoni de color de Pere**; per al color és inofensiu,
per a l'estructura no.

**Criteri de neteja declarat**: ovalitat < 2,0 px **i** |R − mediana(R)| < 6 px.
La segona condició hi és perquè el DSC06990 fa 0,52 d'ovalitat i està trencat:
un radi que no és el radi vol dir que el que s'ha ajustat no és el limbe.

## 2. Fase 0 de l'A7RIIIA, mesurada

| | valor | com |
|---|---|---|
| pedestal | **512,00 DN, pla** | mediana als 378 darks; dispersió **0,00 DN** entre darks i entre canals |
| saturació | **16383** | retalla al valor declarat: 1.034.049 px exactes, veïns a ~75 (⚠️ la R6 III retalla a **16382**) |
| escala | **3,2020 ″/px** | `research/75` §5.1, 38 estrelles, residu 0,71 px |
| nord | **PA 90,27°** | id. |
| flat | radial | el camp 2-D sencer és en quarantena des de `research/90` |

⛔ **Aquest cos NO TÉ CAP ZONA EMMASCARADA.** `raw_width` 8000 contra `width`
7968: les 32 columnes que sobren **veuen llum** (a 8 s marquen 3436 DN contra
4758 de la zona activa). El camí del pedestal de la R6 III —mesurar-lo al marge
esquerre, fotograma a fotograma, que és millor perquè segueix la temperatura—
**allà no existeix**, i el pedestal ha de sortir dels darks: un número per run.

## 3. Quatre suposicions de la Vixen que el tren nou ha destapat

Totes quatre eren codi que funcionava perfectament amb un sol tren.

1. **El llenç anava 1:1 amb el sensor.** `Ctx.mapes` era rotació + translació
   sense escala. Ara hi ha un factor `k = escala_llenç / escala_sensor`, que val
   1 a la Vixen i **0,6713** a la Sony (hi entra remostrejada ×1,49).
2. **`R_LLUNA_NOMINAL = 460.0`**, escrit a mà. És de la Vixen; a la Sony li
   toquen 306, i amb 460 la cerca del limbe s'enganxava a un altre gradient:
   donava **R = 477 px i només 4 fotogrames de 14**. Ara surt del tren.
3. **La finestra de cerca dels contactes s'ancorava al primer fotograma**
   (`tmig = t0 + 65`). Amb la Vixen el primer és 14 s **abans** de C2 i
   funcionava; amb els 14 de la Sony el primer ja és **59 s dins** de la
   totalitat, la finestra engolia C2 i C3 alhora i `brentq` fallava amb
   *«f(a) and f(b) must have different signs»*. Ara es busca el canvi de signe
   sobre una graella ampla i s'exigeix que n'hi hagi **exactament dos**.
4. **`revela_frame` i `zona_fosca` ddonaven per fet que hi ha marge fosc.**
   Ara el pedestal pot arribar declarat.

**Regressió de la Vixen** (es va tocar codi compartit): els offsets Lluna−Sol
dels 121 fotogrames surten **bit a bit idèntics** i els contactes canvien
**1,3·10⁻⁸ s**, que és la tolerància de `brentq` amb un interval de partida
diferent. Aquests 13 ns només poden moure el flag `coronal`, que té un llindar
d'un segon: cap producte de la Vixen no canvia.

## 4. El llenç comú

Perquè un tren pugui fer de **jutge** de l'altre han d'estar a la mateixa
graella. `comu.LLENC_COMU` declara **8096 × 8960 px a 2,1494813525884373 ″/px**,
Sol al centre per efemèride i nord amunt, i un tren amb `llenc_de` l'hereta.

⚠️ El camp de la Sony és **més ample i més baix** que el llenç: cobreix ±13,5 R☉
en horitzontal (el llenç només n'hi demana ±9,2) i **±8,6 a ±9,4 en vertical**
contra els ±10,2 del llenç. Els pesos ja ho porten; el que falta és dada, no
una decisió.

⏭️ **El discriminador que això compra**: els dos sensors estan **girats 33,08°**
al cel (PA nord 57,19° i 90,27°) i tenen escales diferents. Al llenç comú, una
estructura del **cel** surt al mateix angle als dos; una del **sensor** surt
girada 33,08°; i una de la mida del **píxel del sensor** surt, a més, ×1,49 més
gran a la Sony. Amb un sol tren cap de les tres no es podia distingir.

## 5. Dos defectes més, i la porta nova disparant a la primera

### 5.1 El filtre del limbe no mirava l'rms del seu propi ajust

`sol_i_llenc` triava els fotogrames per al model del Sol amb `n_punts ≥ 400` i
`|R − mediana(R)| ≤ 3 px`. **No mirava l'rms de l'ajust del cercle.**

A la Sony, els fotogrames de **2 s i 8 s** tenen la corona interior cremada i el
que l'algorisme troba no és el limbe: en surt un centre **128–234 px fora** amb
un rms de **15–16 px**… i un radi que **encara cau dins del ±3 px**. Dos
d'aquests (DSC06996 i DSC06999) passaven el filtre.

| fotograma | exp | rms de l'ajust | lluna_cx | passava? |
|---|---|---|---|---|
| DSC06992 | 1/8 s | **1,17** | 3895,55 | sí ✓ |
| DSC06996 | 2 s | **16,05** | **3767,98** | ⛔ **sí** |
| DSC06999 | 2 s | **16,20** | **3768,17** | ⛔ **sí** |
| DSC06993 | 8 s | 14,93 | 3661,93 | no (pel radi) |

⏭️ **Conseqüència**: la detecció de segments d'apuntament (§3) veia el salt de
128 px entre els bons i els dos dolents i declarava **CINC apuntaments on n'hi
ha UN**, amb segments d'un sol fotograma i model de grau 0.

**Cura**: `rms ≤ max(3,0 ; 4 × mediana(rms))`. A la Sony la mediana és 1,18 px →
llindar 4,71 → **10 → 8 fotogrames**, fora exactament el 06996 i el 06999, i la
dispersió del centre baixa a 1,40 × 4,94 px: **un sol segment**. A la Vixen la
mediana és 1,65 px → llindar 6,58 → **49 → 49, res fora**: el defecte hi era
latent i no hi havia picat mai.

### 5.2 Una cadena que falla marcava com a fallits runs que no eren seus

`_marca_fallit()` escombrava **tot** `1-RUNS` i renombrava qualsevol carpeta
sense `CADENA.json`. Amb dues cadenes en paral·lel, **la que peta declarava
fallida la que anava bé**; i un run marcat a mà es quedava amb un
`_AVORTAT_FALLIT` absurd, que és com va sortir. Ara marca **només el run
d'aquest procés**.

### 5.3 La porta F3.2 va disparar al seu primer contacte amb dada nova

La porta de **tancament HDR per BRILLANTOR**, afegida el mateix matí de
l'auditoria contra Brno (`research/114` §6), va aturar el run amb el model del
Sol dolent: **sistemàtic 21,20 %, pitjor 27,98 %, NO PASSA** sobre un llindar
del 8 %. Al run bo de la Vixen valia **2,02 %**.

⚠️ Amb honestedat: part d'aquell 21 % pot ser del **control** i no del compost
—el fotograma que va triar era el DSC06996, un dels dos amb el limbe mal
mesurat, i `revela_frame` també li mesura el centre pel limbe—. Però la porta
va fer la seva feina: **va aturar un run que tenia un defecte real**.

## 6. El primer run de la Sony: les portes

Run `SONY_CIENCIA_20260827T104917Z`, 14 fotogrames, **12 coronals**.

| porta | Sony | Vixen (referència) |
|---|---|---|
| F0.1 pedestal / blanc | 512,00 · 16383 · PASSA | 512,00 · 16382 · PASSA |
| F0.3 flat | vinyetatge 67 % · control 0,01–0,03 % ⚠️ **sense invertits** | 4,60 % · PASSA |
| F1.1 limbe | 12/14 · R 302,93 px | 121 · R 455,5 |
| F1.2 contactes | C2 −58,86 s · C3 +46,33 s · **totalitat 105,20 s** | **105,20 s** |
| F1.3 registre fi | 8/12 · desplaçament màx **0,040 px** | 29/67 |
| F2.2 coherència | dispersió **2,78 %** · p5 0,969 · p95 1,057 | 6,67 % |
| F2.4 cel pel color | angle **22,29°** · condició 5,20 · control **0,154 %** · PASSA | angle **22,47°** · 5,16 · 0,190 % |
| F3 tancament color | R/G −2,4 % · B/G +1,4 % · sist. **2,4 %** · PASSA | 3,8 % |
| **F3.2 tancament per brillantor** | **2,63 %** · PASSA | 2,02 % |
| F3b protuberàncies | egress (2 fotogrames) · PASSA | ingress + egress |

⏭️ **La totalitat surt 105,20 s als dos trens**, mesurada des de dos cossos i
dues òptiques diferents. I el **cel pel color** dona angle 22,29° contra 22,47°:
la geometria cromàtica que separa corona i cel (`research/109`) queda
**confirmada per un segon instrument**.

⚠️ **La Sony recull MÉS llum total que la Vixen**: Σt = 13,70 s a f/2,8 contra
41,36 s a f/5,5 = **10,72 s equivalents**. Però la seva llum és concentrada a
les llargues (12 dels 13,7 s són el 8 s i els dos de 2 s): on és prima és a la
**corona interior**, que depèn de les curtes, i d'aquelles només en té una de
cada.

## 7. El jutge: Vixen contra Sony

⏭️ **És el primer control d'aquest projecte amb dos instruments de veritat
independents**: altres òptiques, altre sensor, altra muntura, altre apuntament,
altra escala de placa i **33,08° de gir** entre els sensors.

| escala angular | **Vixen × Sony** | Brno × Brno |
|---|---|---|
| 90° (m 1–4) | 0,985 | 0,995 |
| 30° (m 5–12) | **0,998** | 0,993 |
| 12° (m 13–30) | **0,997** | 0,987 |
| 4,5° (m 31–80) | **0,989** | 0,976 |
| 1,8° (m 81–200) | **0,907** | 0,961 |

**A 4,5° els nostres dos trens s'entenen millor que els quatre composts de Brno
entre ells**, i ells comparteixen equip i pipeline.

⚠️ **La cautela honesta**: els nostres dos trens comparteixen **el lloc, el cel
i el meu codi**. Són independents en òptica, sensor, muntura, apuntament,
escala i orientació, però no en atmosfera ni en mètode.

### 7.1 Es tanca el forat del `research/114` §3

| radi | **Vixen×Sony** | Vixen×Brno | Sony×Brno | Brno×Brno |
|---|---|---|---|---|
| 1,03–1,12 R☉ | **0,996** | 0,692 | 0,722 | 0,915 |
| 1,12–1,30 | **0,999** | 0,839 | 0,845 | 0,992 |
| 1,30–1,80 | **0,988** | 0,862 | 0,878 | 0,995 |
| 1,80–2,60 | **0,975** | 0,758 | 0,802 | 0,991 |

Ahir la corona interior de la Vixen discrepava de Brno més del que el soroll
explicava i no es podia decidir de qui era. **Ara sí**: la Sony hi coincideix
amb la Vixen al **0,996** i **no** es posa del costat de Brno (0,722 contra
0,692). La discrepància és **nostra en comú** —del lloc o del mètode—, i **no
un defecte de la Vixen**.

## 8. L'estriat del `research/113`, resolt: són DUES coses diferents

### 8.1 La família de λ ≈ 50–160 px a 10°/80° és del CEL

Els pics de la Vixen surten a la Sony **al mateix angle i a la mateixa mida**,
amb la hipòtesi del cel guanyant la del sensor per ×2,9 a ×6,2:

| pic de la Vixen | CEL | SENSOR (−33,1°) | PÍXEL (−33,1° i ×1,49) |
|---|---|---|---|
| λ 63,9 px · 12,5° | **8,41** | 2,44 | 1,42 |
| λ 100,8 px · 85,5° | **8,00** | 2,44 | 1,73 |
| λ 159,2 px · 93,5° | **8,58** | 1,38 | 0,23 |
| λ 36,9 px · 83,5° | **8,01** | 2,05 | 2,25 |
| λ 48,6 px · 10,5° | **5,32** | 1,82 | 1,70 |

⏭️ **No és instrumental.** I tampoc no és transparència atmosfèrica que es
mogui amb el vent: dues preses separades **80 s** es posen d'acord al 0,98–0,99
a aquestes escales (`research/114` §4). El que queda és **estructura del cel que
no es mou en 80 s**, i això és la corona.

⚠️ **Rectificació de mètode**: la FFT d'un camp de streamers radials també fa
pics direccionals. Que el `research/113` en digués «dues famílies d'estriat» era
una interpretació, no una mesura; la mesura era que hi ha potència a 10° i 80°.

### 8.2 La família de λ ≈ 4–12 px és NOMÉS de la Vixen

| λ (px de llenç) | VIXEN | SONY |
|---|---|---|
| 4,13 | 167,5° **×2,92** | 143,5° ×1,25 |
| 5,95 | 168,5° **×5,02** | 96,5° ×1,75 |
| 7,83 | 165,5° **×5,57** | 169,5° ×1,40 |
| 9,39 | 168,5° **×5,96** | 84,5° ×1,50 |

I la prova de «píxel del sensor» (λ×1,49, girada −33,1°) dona **×0,78–1,07** a
la Sony: res. ⏭️ La direcció diu d'on ve: **167,5° al llenç són 44,7° al marc
del sensor de la Vixen**, és a dir la **diagonal**, que és l'orientació de la
quincunx dels seus plans verds. La hipòtesi és el remostreig dels subplans CFA
a través d'un gir de 57,19°; **queda per confirmar**, però la localització
—només un tren, a la diagonal del seu sensor— ja és una mesura.

⚠️ El `research/113` la descrivia «alineada amb els eixos» a λ 4,1 px; ara surt
a la **diagonal** i amb el gruix de la potència a λ 6–9 px.

## 9. Els halos que Pere va marcar al `capes_LDIC.psb`

**Els va marcar bé. No són un defecte del producte: són el límit de cada
exposició, i el fitxer no ho deia.**

Traç magenta al voltant de la Lluna a **r = 1,18–1,53 R☉** (tres blobs que la
dilatació separa, però visualment un sol arc de ~270°). El PSB s'obre amb la
capa **`LDIC 0.125s` visible**, i la seva **vora interior és a 1,19 R☉**.

| capa | vàlida de | fins a |
|---|---:|---:|
| 1/6400 s | *(mai per damunt de 0,5)* | — |
| 1/800 s | 1,04 | 1,38 |
| 1/100 s | 1,04 | 2,25 |
| 1/30 s | 1,05 | 5,96 |
| **1/8 s** ← s'obre visible | **1,19** | 9,00 |
| 1/4 s | 1,28 | 9,00 |
| 1 s | 1,57 | 9,00 |
| 2 s | 1,77 | 9,00 |
| 8 s | 2,88 | 9,00 |

**El que s'ha comprovat:**

1. **Cada capa és zero fora del seu rang i la seva màscara és correcta.** Al
   8 s, de 1,2 a 2,4 R☉ la màscara val 0,000 **i el RGB de sota val 0,0000**:
   no hi ha res amagat sota cap màscara.
2. **El lliurable final no en té cap rastre**: la derivada segona del perfil
   radial a 1,18–1,53 R☉ val **0,0–0,7 σ** al compost lineal i al passa-alt. A
   la capa que Pere va marcar, en canvi, hi ha **+3,4 σ a 1,177 R☉**, que és
   exactament la vora de la màscara.
3. La còpia que Pere va desar **havia perdut la màscara** (va passar a ser
   transparència), i la vora es va quedar sola i visible.

⚠️ **Mesura per anell contra mesura local**: el perfil radial mitjà no veu res a
1,31–1,39 R☉ perquè **no és un anell sencer**; i la prova aparellada contra
controls al mateix radi tampoc dona res fort (−2,2 σ el màxim). **Cap de les
dues no podia trobar-ho, perquè un halo és una FORMA i totes dues mesuren un
NIVELL.** El que ho va resoldre va ser mirar la vora de validesa de la capa.

⏭️ **Cura**: `f4.nom_capa_ldic` — el nom de cada capa duu ara el seu rang
(`LDIC 0.125s (1 fot.) · val 1.19-9.00 R☉`), a les dues PSB que porten capes
LDIC. La vora s'explica sola en obrir el fitxer.

## 10. El color entre trens: rectificació

⛔ **Una primera lectura deia que el R/G de la Sony surt 11–14 % per damunt del
de la Vixen. Era FALSA**: sortia de `color_renderitzat_sRGB_lineal` (fase 3),
que és **després de la corba de to** i és una magnitud de presentació.

⚠️ **I la primera EXPLICACIÓ d'aquell error també era falsa.** Vaig dir que la
causa era el nivell absolut (àncora L 7,07·10⁴ contra 2,10·10⁵). Provat amb un
pedaç sintètic del mateix color lineal a àncores de 10⁴ a 10⁶: el renderitzat
surt **idèntic** (1,6304 / 0,5609 a totes), o sigui que **no depèn del nivell**.
El que fa que els números renderitzats discrepin més que els lineals **queda
sense identificar**; els candidats són la restitució del croma a baixa
freqüència sobre camps diferents i el pes de gamut, i cap no està mesurat.

A la **dada lineal** (rebut F2.4, abans de tonificar):

| | Vixen | Sony | Δ |
|---|---|---|---|
| cel `b_cel` | [1,0121 · 1 · 0,8786] | [1,0393 · 1 · 0,8639] | R **+2,7 %** · B −1,7 % |
| corona `s_corona` | [1,752 · 1 · 0,4981] | [1,7661 · 1 · 0,4683] | R **+0,8 %** · B −6,0 % |
| R/G a 1,1 / 2 / 3 / 5 R☉ | 1,7527 / 1,7067 / 1,7656 / 1,7700 | 1,7794 / 1,6877 / 1,7506 / 1,7688 | **+1,5 / −1,1 / −0,8 / −0,1 %** |
| B/G a 1,1 / 2 / 3 / 5 R☉ | 0,5123 / 0,5097 / 0,5135 / 0,5141 | 0,4679 / 0,4842 / 0,4577 / 0,4702 | **−8,7 / −5,0 / −10,9 / −8,5 %** |

⏭️ **El R/G dels dos trens coincideix a 0,1–1,5 %**: és una confirmació
independent de l'enrogiment mesurat, i dels bons. **El que discrepa és el BLAU**,
amb una constant de ~**−8,5 %** a la corona i només −1,7 % al cel. Que la
discrepància creixi amb com de vermell és l'objecte apunta a la **matriu 3×3
del blau extrapolant lluny del lloc geomètric de la llum de dia**, no a un error
de nivell. Queda obert.


## 11. El salt de muntura mesura el flat (el control que a aquest tren li faltava)

L'A7RIIIA no té flats invertits: la porta que valida el flat radial de la Vixen
(`research/100`) **allà no existeix**. El salt de la Skywatcher la substitueix:
el mateix punt del cel cau a **dues posicions del sensor separades 737 px**, o
sigui que és un **dither**, i amb prou parells es pot invertir el flat sense
flats.

**Mètode**: per a cada parella de fotogrames de la mateixa exposició, un de cada
apuntament, `ln q = const + lnF(rA) − lnF(rB)` resolt per mínims quadrats sobre
una graella radial (autocalibració clàssica; el gauge fixa lnF(0) = 0, i la
constant per parella és la transparència, que **no** és error de flat).
7 parelles, **57 milions de parells de radis** per canal.
Eina: `research/tools/sony_entrada/flat_pel_salt.py`.

### El resultat

| r sensor (px) | R | G1 | B | G2 | B − G |
|---|---:|---:|---:|---:|---:|
| 420 | +2,38 | +1,38 | +2,65 | +1,37 | +1,28 |
| 1501 | −1,80 | −2,61 | −2,60 | −2,63 | +0,02 |
| **2581** | **−4,85** | **−4,21** | **−3,66** | **−4,25** | +0,57 |
| 3662 | −2,86 | −1,03 | −0,82 | −1,15 | +0,27 |
| 4742 | +0,72 | +3,50 | +2,47 | +3,30 | −0,93 |

| canal | amplitud | desacord entre meitats |
|---|---|---|
| R | 7,63 % | 0,54 % |
| G1 | **9,03 %** | **0,10 %** |
| B | 7,16 % | 0,05 % |
| G2 | 8,75 % | 0,04 % |

⏭️ **El flat radial que fem servir té un error de 7 a 9 % pel camp**, i el
control de meitats (0,04–0,54 %, un 1 % del senyal) diu que **és una mesura**.

⏭️ **I és quasi ACROMÀTIC**: el B/G només varia un **2,29 %** pel camp. Per tant
**el flat NO explica** el −7,3 % de blau que va fer caure la porta de color.

## 12. Per què queia la porta de color: el CEL canvia durant la totalitat

Mesurat fotograma a fotograma, **sense cap compost pel mig**, el B/G a
1,8–3,6 R☉:

| t (s) | 16–18 | 28–29 | 62 | 80–82 | 85–88 |
|---|---|---|---|---|---|
| B/G | **0,579** | 0,543 | **0,507** | 0,524 | 0,535 |

**Un 12 % en 100 s.** La corona no canvia en 100 s: és el **cel**, i lliga amb
el 8 % de transparència que `research/100` va mesurar.

⛔ **El defecte era del CONTROL, no del compost.** El compost és una **mitjana
temporal** i la porta el comparava amb **un sol instant**. Amb un apuntament el
recorregut era de 46 s i passava (2,4 %); amb els dos, de 104 s, i queia
(7,3 %). El mateix compost contra controls a instants diferents dona **7,3 % a
t=18 s i 1,4 % a t=28 s**.

⏭️ **Cura**: `comu.controls_repartits` + la porta jutja la **mediana sobre
controls repartits en el temps** i **declara la dispersió** (si és gran, el cel
va canviar). Verificat als tres runs abans d'adoptar-la:

| run | control únic | mediana repartida | pitjor |
|---|---|---|---|
| Vixen | 3,8 % | **3,48 %** | 4,66 % |
| Sony (1 apuntament) | 2,4 % | **1,79 %** | 2,84 % |
| SONYTOT (2 apuntaments) | **7,3 % NO PASSA** | **3,09 %** | 7,32 % |

⚠️ **Això fa passar un run que queia, i cal dir-ho clar.** El que ho justifica
no és que passi: és la mesura del §12, feta **independentment de la porta**, i
que a la Vixen el número gairebé no es mou (3,8 → 3,48), que és el control de
que no s'ha afluixat res.

## 13. La mateixa cura NO servia a la porta de brillantor, i per què

Aplicant a la porta de brillantor la mateixa mediana sobre controls repartits,
els sis controls del Run 2 surten així:

| control | t (s) | apuntament | sistemàtic |
|---|---:|---|---:|
| DSC06982 | 16 | **A** | **8,5 %** |
| DSC06984 | 18 | **A** | **7,7 %** |
| DSC06985 | 28 | **A** | **9,7 %** |
| DSC06994 | 80 | B | 2,9 % |
| DSC06996 | 82 | B | 2,7 % |
| DSC06999 | 88 | B | 2,0 % |

⛔ **No és una tendència temporal: és BIMODAL per apuntament.** I els 7,7–9,7 %
de l'apuntament A **coincideixen amb l'error de flat mesurat pel dither**
(7–9 %, §11). Amb dos apuntaments el compost barreja **dues vistes amb
calibratges de flat diferents**, i això és real: la porta el detecta.

⛔ **La mediana ho amagaria** (5,27 %, passaria). Per això aquesta porta jutja la
mediana **i la dispersió**: si el compost no representa cap dels controls, la
mediana no el salva.

| run | mediana | dispersió | veredicte |
|---|---|---|---|
| Vixen | 2,02 % | 1,8 % | PASSA |
| Sony (1 apuntament) | 2,63 % | 2,6 % | PASSA |
| SONYTOT (2 apuntaments) | 5,27 % | **7,7 %** | PASSA, **al límit** |

⚠️ Als dos runs que ja passaven, la mediana surt **idèntica** al valor d'un sol
control (2,02 i 2,63): la cura no afluixa res, i el que canvia només canvia allà
on hi ha alguna cosa a veure.

⏭️ **Conseqüència per al producte**: el compost de dos apuntaments **carrega
l'error de flat** i el Run 2 no és, fotomètricament, millor que el Run 1 pel fet
de tenir més fotogrames. Guanya cobertura i senyal/soroll; paga en homogeneïtat
de calibratge. La cura de fons és **corregir el flat amb el que el dither ha
mesurat**, i això encara no s'ha fet ni jutjat.

## 14. Una porta que jutjava una capa on la capa no viu

El Run 2 va caure a **F4.3** amb «capes VERDES: C2 · perles i PRIMER ANELL DE
DIAMANT». La capa era **bona**.

`mesura_color` jutja als anells **1,1 · 2 · 3 · 5 R☉**, que són **coronals**. Una
capa de **contacte** —feta amb 1/6400, 1/800 i 1/100 s— allà no hi té senyal:

| jutjat a | R/G | B/G | veredicte |
|---|---|---|---|
| **contacte** (1,00 · 1,05 · 1,10 R☉) | 1,814 · 1,874 · 1,816 | 0,429 · 0,454 · 0,477 | **OK** |
| coronals (1,1 · 2 · 3 · 5) | 1,874 · 1,457 · 0,387 · **0,048** | 0,454 · 0,669 · 0,788 · 0,143 | ⛔ VERD |

A 1,05 R☉ la capa té **exactament el color que mesurem a tot arreu**. A 5 R☉ el
R/G val 0,048 perquè allà **no hi ha res**, i el que la porta mesurava era soroll
amb el biaix positiu que el `fmax` hi deixa al canal amb més píxels.

⛔ **La capa de C2 només existeix al `SONYTOT`** (els seus fotogrames són a la
quarantena), o sigui que aquesta porta mal aplicada **no havia picat mai**.

⏭️ **Cura**: cada capa es jutja **on viu** — les de contacte a 1,00–1,10 R☉ i les
coronals als anells de sempre —, i el color als anells coronals es continua
desant com a informació, amb la nota que allà és soroll. La protecció de debò
contra el verd la fa la porta **F4.2** sobre les capes LDIC, que sí que tenen
corona; repetir-la aquí no protegia de res.

## 15. Un apuntament o dos? Els dos, i són complementaris

Jutjat contra la Vixen, que és l'instrument independent:

| escala | Vixen × **SONY** (14 fot.) | Vixen × **SONYTOT** (27 fot.) | |
|---|---|---|---|
| 90° (m 1–4) | 0,985 | **0,996** | ⏭️ **millora** |
| 30° (m 5–12) | 0,998 | 0,997 | = |
| 12° (m 13–30) | 0,997 | **0,987** | ⛔ empitjora |
| 4,5° (m 31–80) | 0,989 | **0,974** | ⛔ empitjora |
| 1,8° (m 81–200) | 0,909 | **0,890** | ⛔ empitjora |

I els dos productes del **mateix tren** s'entenen només al **0,947 a 1,8°**: la
diferència és real, no soroll de mesura.

⏭️ **El segon apuntament compra escala gran i paga escala fina.** Té la mecànica
que toca: més cobertura i més fotogrames constrenyen millor la forma global,
mentre que barrejar **dues vistes amb l'error de flat aplicat a llocs diferents
del sensor** (§11, §13) difumina el detall.

⛔ **Cap dels dos runs no és «el bo»**: el de 14 mana al detall fi i el de 27 a
la forma gran. La resposta a la pregunta de Pere («fem primer un run amb la
quarantena fora?») és que **calien tots dos**, i no per prudència sinó perquè
mesuren coses diferents.

⏭️ **El pas següent que això dibuixa**: corregir el flat amb el que el dither ha
mesurat i refer el de 27. Hauria de recuperar l'escala fina sense perdre la
gran. **No està fet ni jutjat.**

### 14.1 Per què no havia picat mai, exactament

Les capes de contacte de la **Vixen** només produeixen mesura a **1,1 R☉**: als
anells de 2, 3 i 5 R☉ no hi arriben als 200 píxels que `mesura_color` exigeix i
els descarta **en silenci**. La Vixen es jutjava, de fet, **a un sol anell**, i
aquell està bé (R/G 1,828 · B/G 0,686).

La Sony no. Els seus fotogrames de contacte són de **1/100 s** —contra 1/3200 de
la Vixen— i el seu camp és més gran, o sigui que **sí que posen més de 200
píxels a 3 i 5 R☉**: píxels que passen el recompte i **no porten senyal**.

⛔ **La guarda `s.sum() < 200` protegeix d'anells BUITS, no d'anells
SOROLLOSOS.** Amb la cura (jutjar a 1,00 · 1,05 · 1,10 R☉) la Vixen manté
l'anell que ja passava i n'afegeix dos amb més senyal: més robust, no menys.


## 16. La costura dels dos apuntaments, mesurada i acotada

A la vista d'estructura del `SONYTOT` hi ha una **banda vertical clara a la
dreta**, amb la vora recta d'una petjada de sensor. És la frontera entre el que
cobreixen **els dos apuntaments** i el que en cobreix **un**.

| r (R☉) | dos apuntaments | un apuntament | quocient | pes dos / un |
|---|---|---|---|---|
| 6,5 | 48,5 | 132,2 | **×2,73** | 32,1 / 9,3 |
| 7,5 | 26,5 | 103,5 | **×3,90** | 32,1 / 9,3 |
| 8,5 | 30,8 | 86,8 | **×2,82** | 32,1 / 9,3 |

⏭️ **Acotada, i és el que la salva**: la banda **només existeix per damunt de
~6 R☉**. Per sota no hi ha prou píxels d'un sol apuntament ni per mesurar-los:
**la corona la cobreixen els dos sencera**. I a 6,5–8,5 R☉ el compost ja és
sobretot **cel** (`research/99`), o sigui que el que discrepa és el **residu de
la resta de cel** calculat amb **3,4 vegades menys fotogrames**.

Toca el **9,6 % del llenç útil** (89,2 % el cobreixen els dos i 1,2 % ningú) i
**no toca res del jutge d'estructura**, que va d'1,1 a 3 R☉ — per això les
correlacions del §15 surten netes tot i haver-hi aquesta costura al camp llunyà.

⚠️ **Per al lliurable**: si el `SONYTOT` es fa servir per a res més enllà de
6 R☉, aquesta banda hi és i s'ha de declarar. Per a la corona, no hi és.

## 17. El Run 2, acabat

`SONYTOT_CIENCIA_20260827T120934Z`, **16,1 min**, 27 fotogrames, 19 coronals,
totes les portes passades:

| porta | valor |
|---|---|
| F1.2 apuntaments | **2** (10 fot. t 0–29 s · 8 fot. t 62–104 s) · deriva 0,41 ″/s |
| F2.2 coherència | dispersió dins de rang |
| F2.4 cel pel color | PASSA |
| F3 tancament de color | mediana de 6 controls **3,1 %** · PASSA |
| F3.2 tancament per brillantor | mediana **5,27 %** · dispersió **7,70 %** · PASSA (al límit) |
| F4.3 contactes | C2 **OK** · C3 **OK** (jutjats a 1,00–1,10 R☉) |
| F3b protuberàncies | **ingress 13,0 Mpx + egress 0,63 Mpx** — els dos extrems |

⏭️ És la primera vegada que la Sony pot fer les protuberàncies **dels dos
extrems**: les d'ingress són el bloc de contacte de C2, que viu a la quarantena.
