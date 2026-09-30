# 95 · Els dos artefactes del pas alt: causa mesurada i correcció

## ⛔⛔ NORMA DEL RECTANGLE (ordre de Pere, 23-08-2026)

> «El filtre de pas alt ha d'aplicar a **TOT el rectangle** de la imatge, no
> només a una circumferència, sinó quedaran **HALOS**. És un error molt comú i
> recurrent que fas i que hem d'evitar a tota costa.»
> I, tot seguit: «aplica la norma del rectangle a **tot tipus de filtre** que
> et demani.»

Val per a pas alt, MGN, NRGF, FNRGF, WOW, ACHF, màscares de detall i qualsevol
capa de realçat. Una capa que s'apaga **dins** de la zona que encara té dades
deixa una regió plana a gris neutre, i muntada a Photoshop aquella frontera
**és un halo**: no importa que la transició sigui suau ni que el salt de
mediana mesuri zero, perquè el que l'ull veu és el canvi de règim.

**L'única cosa que pot aturar un filtre és que no hi hagi dada.** Si l'exterior
surt lleig, es repara aigües amunt i mai retallant un cercle. Detall i les
quatre formes que l'error va prendre en un sol dia: §10.


**23 d'agost de 2026.** Pere va pintar damunt del pas alt v12 i el va desar com
a `PASSALT_PERE.tif`: **en vermell** un anell que va dir «horrorós», **en ocre**
un arc que va dir «petit». Aquest document diu què eren, què els causava i què
s'ha canviat perquè no tornin.

Lliurable: `output/passalt_corona_20260823/20260823T0310Z_v22/`, sobre el
compost `output/stack_calibrat_20260822/20260823T0230Z_pedsuau/`.

## 1. Què deien les marques, mesurat

Les marques s'han extret del TIFF per to i s'han portat a coordenades del Sol.

| marca | píxels | radi | forma |
|---|---:|---|---|
| vermell | 2.306.722 | 1,20–3,64 R☉, mediana 2,53 | anell |
| ocre | 287.491 | 5,77–6,81 R☉, mediana 6,28 | **cercle centrat al Sol** |

L'ocre s'ajusta a un cercle centrat al Sol amb σ = **81 px**, contra 368 px
d'una recta i 198 px de la vora del marc de la Vixen. O sigui que és una porta
radial nostra, no una vora de camp.

## 2. L'anell vermell: el compost estava multiplicat per `validesa²`

`build_stack_calibrat.py` formava el compost lineal així:

```python
corona = (vixw*wv3 + sony_ns*(1-wv3)) * limb[...] * validesa[...] * validesa[...]
```

**`validesa` hi entrava dues vegades.** Comprovat dividint el compost pel
mesclat pur reconstruït dels lliurables 01, 02 i 03: el quocient és
**exactament `validesa²` a tots els radis, a quatre decimals** (error relatiu
medià 2,9·10⁻⁸ sobre 3,5 milions de píxels).

I `validesa = max(w_sony · zona_ok, wv)` té una **cantonada de `max()`**:

| R☉ | 1,4 | 2,0 | 2,4 | **2,6** | 3,0 |
|---|---:|---:|---:|---:|---:|
| factor aplicat | 0,941 | 0,777 | **0,557** | **1,000** | 1,000 |

Un graó del **+79 % en 0,2 R☉** dins d'un fitxer que es diu «calibrat en
B/B☉». A la imatge amb corba de to no es veu; un pas alt el dibuixa com un
contorn dur. **Contrafactual**: refent el filtre amb l'única diferència de
dividir per `validesa²`, el rms del pas alt a 2,476 R☉ passa de **0,6404 a
0,0450**, i el rms global de 0,2075 a 0,0793. El contorn dentat del pas alt i
la vora del binari `{validesa == 1}` són **el mateix polígon**, osca de
l'esquerra inclosa.

Són **tres conflacions encadenades**, i la tercera només és la que ho fa
visible:

1. `wv` barrejava QUIN tren mana (sigmoide de radi), ON hi ha camp Vixen
   (`w_edge`) i ON el Sol està tapat (`limb`);
2. `validesa` es derivava de `wv` i de `zona_ok`, que **no diu si hi ha dada**
   sinó si aquella zona de cobertura va poder tenir pedestal de cel. La corona
   interior no arriba mai a r > 8,5 R☉ i per això hi valia 0;
3. i el compost es multiplicava per `validesa` dues vegades.

⚠️ El quadrat **agreuja, no és l'arrel**: amb un sol factor el graó encara
seria ×1,468. L'arrel és fer servir una màscara de presència com a factor
fotomètric — la regla mare de `research/93`.

### Correcció

Mescla convexa **normalitzada per cobertura**, i el compost lineal no es
multiplica per cap màscara:

```python
wa = gauss20(sigmoide(R) * cobertura_Vixen)
wb = gauss20((1-sigmoide(R)) * cobertura_Sony)
corona = (vixw*wa + sony_ns*wb) / (wa+wb)      # convexa, sense cap màscara
corona[wa+wb <= 1e-3] = NaN                    # cap dada ≠ zero llum
validesa = clip(max(cob_sony, cob_vixen),0,1) * limb    # es lliura a part (07)
```

On només hi ha un tren, en surt aquell tren a pes ple i **sense enfosquir**.

### Abast real, i què NO explica

Per sota d'**1,95 R☉** `validesa` és exactament constant en azimut, o sigui un
terme additiu constant per columna en log, i la resta del fons azimutal de
Fourier (que inclou m=0) se l'endú sencer. **`validesa²` no pot fabricar res
per sota d'1,9 R☉**: l'abast efectiu és **1,9–3,2 R☉**, amb el pic a 2,48. El
25 % interior de la marca vermella són les estries del màster HDR de la Vixen
(artefacte F de `research/93`), que la v12 va deixar destapades. Amb el compost
corregit ja no se'n veuen: la component azimutalment coherent de l'interior és
com a molt **0,0155 contra una dispersió de 0,19** (coherència ≤ 0,123).

## 3. L'arc ocre: una rampa que s'acabava amb cantonada

`r_ext` era un `clip` lineal de 5,0 a 6,5 R☉: continu però **no derivable**, i
D valia **exactament zero a partir de 6,505 R☉**. Dues coses la fan visible i
només una és la cantonada:

- la discontinuïtat de derivada (banda de Mach);
- i sobretot, que **la textura de gra s'acaba en sec**. Una vora de textura es
  veu encara que la mitjana no canviï gens.

S'ha comprovat per eliminació que era l'única porta activa allà: la de
cobertura `r_ok` val 1,0000 fins a 7,24 R☉.

### Correcció

Esvaïment **gaussià, que no té final**: `e_hi` només diu on val 0,1, no on
s'acaba. I totes les rampes, finestres i portes del fitxer passen per una
funció `suau()` amb derivada zero als extrems.

## 4. Dos defectes més que van sortir pel camí

### 4.1 El control de costura era fals

`vora_marc_Vixen` i `vora_cobertura_Sony` deien **«0,000 σ» a totes les
versions**. Motiu: comparaven medianes de dues franges al voltant de tot el
perímetre, i el **85 % d'aquells píxels són exactament zero** perquè cauen fora
del radi viu del filtre. Les dues medianes valien 0 i la resta donava 0.

**Un control que no pot fallar no és un control.** Ara: només s'avalua on el
filtre lliura (envolupant declarada ≥ 50 % del màxim), es refusa la mostra si
té més d'un 20 % de zeros exactes o menys de 5.000 píxels —i llavors diu
`MOSTRA_DEGENERADA` o `MOSTRA_INSUFICIENT`, mai un número—, i el gra es mesura
a la vora, no a tot el camp.

### 4.2 El pedestal per zona era una funció esglaonada

A **y = 4578** el pes acumulat de la Sony passa de **24,75 s a 13,50 s en una
sola fila**, i el pedestal per zona hi feia un salt dur de 5,35·10⁻¹¹ B/B☉. Al
cel no hi ha cap vora: la diferència entre zones és de comptabilitat. Era la
banda fosca horitzontal de sota.

I el context que fa que això importi tant: **a 6 R☉ el cel val 78 vegades la
corona.** Un 2,5 % de cel mal restat hi és el 200 % del senyal — el compost hi
cau un 97,6 % creuant la vora.

Correcció: el mapa de pedestal es **desenfoca** (σ = 150 px) abans de restar-lo,
i l'esvaïment exterior del filtre s'ha escurçat a 3,6–5,6 R☉ perquè a 6,04 R☉
ja hi arribi negligible. Resultat a la vora: rms **0,00130 = 1,1 nivells de 8
bits**, sota el llindar de visibilitat.

## 5. Rectificació d'una troballa meva

Vaig dir que alimentar el filtre amb `06` (amb el cel dins) en lloc de `06b`
era **per què el filtre es moria més enllà de 3 R☉**. Un contrast adversari ho
va refutar i té raó: en un pas alt logarítmic el pedestal de cel és un **guany
local pur**. Els mapes fets amb `06` i amb `06b` estan correlacionats 0,9977 /
0,9832 / 0,9726 a 3 / 4 / 5 R☉ i el quocient de rms és exactament el factor de
compressió. **No mou cap pes de Wiener ni cap S/N.**

El canvi a `06b` es manté —hi guanya ×2,5 a 3 R☉ i ×5,6 a 5, i sense ell no es
poden reobrir les bandes amples—, però **no aporta informació nova**: el que
buidava l'exterior del lliurable era que l'anell de 2,48 R☉ es menjava tota
l'escala de grisos.

⚠️ I porta una trampa: `06b` es torna **negatiu** a partir d'uns 7,5 R☉ (20 %
dels píxels a 8 R☉, 73 % a 10) perquè la quàdrica de cel es va ajustar a
r > 8,5 R☉, on la corona F encara val ~3,9·10⁻¹⁰ i per tant se sobreresta. Per
això el terra de luminància ja **no és global**: es posa en polars i **relatiu
al perfil llis local** (15 %), i es registra quants píxels el toquen (10,6 %).

## 6. Dues coses que vaig trencar i he desfet

- Treure l'esvaïment exterior del tot: surten les estrelles i el residu del
  flat òptic de la Sony. **La rampa cal.**
- Treure la Lluna de la morfologia i acostar-li el suport 50 px: hi entren la
  cromosfera i les protuberàncies i el pas alt les converteix en **taques
  ovalades**. La geometria correcta és la de sempre (9 px d'erosió i 60 px de
  rampa), però **analítica**, no per morfologia — l'element estructurant de
  61 px deixava les seves cares al suport de càlcul.

## 7. Les tres comprovacions noves, i què hauria vist cadascuna

Les que hi havia miraven **vores concretes** i **quocients entre canals**. Un
factor gris i radial no mou cap de les dues. Ara:

| | on | què afirma | llindar | avui |
|---|---|---|---|---|
| **E** | compost | la mediana azimutal del compost sense cel **decreix** amb el radi i el seu pendent logarítmic no fa salts | pendent < 0; salt < 1,5 | −2,120 · 0,769 ✅ |
| **F** | compost | el compost és **exactament** la mescla: cap màscara no hi entra com a factor | < 10⁻³ | **0,0** ✅ |
| **G** | pas alt | el rms radial no sobresurt de la seva **envolupant decreixent** (regressió isotònica), descomptada l'envolupant que el filtre declara | < 1,30 | 1,149 ✅ |

- **F** hauria cantat `validesa²` el primer dia: hauria donat 0,56–1,00 en lloc
  d'1,000.
- **E** hauria cantat el graó: el perfil pujava de 1,43·10⁻⁸ a 2,4 R☉ a
  1,96·10⁻⁸ a 2,6, que és un pendent logarítmic **positiu**.
- **G** sap fallar, i s'ha comprovat: sobre el perfil real de la v12 dona
  **×2,105 → FALLA**; sobre el de la v22, ×1,149 → PASSA.

## 8. Estat del lliurable v22

`--capa 06b · --r-corona 1,25,1,45 · --r-ext 3,6,5,6 · --amplitud 0,15`

- `PASSALT_corona_gris_uint16.tif` — un sol canal, `minisblack`, 7648×5353
- `PASSALT_corona_D_float32.tif` i `PASSALT_mascara_valid_float32.tif`
- D rms 0,0337; p0,1–p99,9 −0,279…+0,443; saturat 0,95 %
- escala de soroll ADU/s → B/B☉: constant 1,1340·10⁻¹¹ contra pendent mesurat
  1,1238·10⁻¹¹, **−0,9 %**
- sigmoide de fusió a 2,8 R☉: **0,031 σ**
- vora del marc Vixen i vora de la caixa Sony: `MOSTRA_INSUFICIENT`, perquè
  totes dues cauen fora del radi on el filtre lliura. És la resposta honesta,
  no un aprovat.

## 9. Deutes que continuen oberts

- **El flat òptic de la Sony (`research/90`) segueix sense aplicar-se.** És el
  que impedeix reobrir les bandes amples (≥ 4,9°), que és on hi ha l'estructura
  coronal de 10–30° a 4–6 R☉. Mentre no hi sigui, l'exterior és del cel.
- La quàdrica de cel s'ajusta a r > 8,5 R☉ i **hi sobreresta corona F**.
- Les estries del màster HDR de la Vixen són a `hdr_vixen_countss.npy` i la
  reparació és refer la fusió aigües amunt, no pintar-hi a sobre.

---

## 10. Segona ronda: la norma del rectangle i set defectes germans

Una escombrada adversarial de vuit agents sobre els dos fitxers va tornar
**33 troballes**. Set eren reals i importants, i totes són de la mateixa
família que les quatre primeres. I pel mig Pere va dictar la norma del
rectangle, que va invalidar la solució que jo havia triat per a l'arc ocre.

### 10.1 La norma del rectangle invalida l'esvaïment radial

La meva correcció de l'arc ocre havia estat **esvair suaument** el realçat cap
enfora (gaussiana, 3,6–5,6 R☉). Això treu la cantonada però **no treu la
frontera**: el llenç queda amb una zona plana a gris neutre a fora. És un halo.

L'esvaïment radial s'ha eliminat (`R_EXT = 0` per defecte) i amb ell **la porta
de cobertura azimutal** (`cob > 0,98`), que era un esglaó de 4,4 px de radi
disfressat de rampa i dibuixava un quadrat arrodonit a 8,2 R☉. Cap de les dues
mesurava res de les dades: la cobertura parcial ja la tracten bé la convolució
normalitzada `G(x·m)/G(m)` i la finestra `dist_vora` per banda.

El que hi havia a fora i justificava el tall s'ha resolt **al seu lloc**:

- **les estrelles** es lleven (0,15 % del llenç, excés > 4 σ sobre la mediana
  local de 5 px, només a r > 2,2 R☉);
- **el graó de cobertura** s'anivella (§10.3);
- **el logaritme** deixa d'explotar amb un terra absolut al nivell del soroll
  del cel (§10.4).

### 10.2 El soroll de la Sony era 4,975 vegades massa gran

`s_sony = |A−B|·√(w_A·w_B/(w_A+w_B))` quan la fórmula del pes ponderat és
`|A−B|·√(w_A·w_B)/(w_A+w_B)`. **És la mateixa expressió amb l'arrel mal
col·locada**, i el quocient és exactament **√(w_A+w_B) = 4,975** amb el pes
típic de 24,75 s. A més era dimensionalment incoherent (ADU/s·√s). Es comprova
sol: amb `w_A = w_B` ha de donar `σ(A−B)/2`, i la forma bona ho fa.

Conseqüència: els pesos de Wiener de les bandes fines quedaven a 0,07–0,20 i
**el detall fi no arribava mai a la sortida**.

| banda (°) | abans | després |
|---|---:|---:|
| 0,17–0,27 | 0,073 | **0,314** |
| 0,27–0,44 | 0,146 | **0,500** |
| 0,44–0,71 | 0,206 | **0,673** |
| 0,71–1,16 | 0,341 | **0,816** |

I la comprovació que ho havia d'haver vist era d'un sol costat:
`f_sist = max(1, rms_cel/n_cel)`. Amb el model 4,975× massa gran el quocient
cru valia ~0,23 i el `max()` el tapava com a 1,00. Ara el quocient cru s'anota
sempre i val **1,16**, que és una confirmació independent que el model nou és
bo a un 16 %.

I el desenfoc de 24 px del mapa de soroll **no era normalitzat**: `A−B` té un
4,9 % de NaN —els forats de saturació dels fotogrames de 8 s— i una gaussiana
corrent els escampava fins al **23 %** del llenç. Cada NaN acabava a
`sig_log = 1,0` per `nan_to_num`, o sigui senyal/soroll = 1, que apaga el
filtre en un anell de vora dentada. Un NaN és manca de **mesura**, no soroll
infinit: ara s'omple amb el veïnat per convolució normalitzada.

I el soroll de la Vixen era **inventat**: `sig = s_sony·(1 − 0,75·Wv)`. El
fitxer de variància s'obria i es llençava, i el model de soroll acabava essent
**la màscara de fusió** —cosa que lliga la porta de Wiener a la sigmoide de
2,8 R☉ i hi pinta una rampa de guany, dins de la banda que Pere va marcar de
vermell—. Ara es fa servir la variància mesurada, warpada amb la mateixa M, i
es combinen amb els pesos reals: `σ² = (wv·σ_vixen)² + ((1−wv)·σ_sony)²`.

### 10.3 El graó entre zones de cobertura és MULTIPLICATIU

A la vora inferior de la caixa (y = 4578, on el pes passa de 24,75 s a 13,50 s
en una fila) la **diferència additiva varia 2,7 vegades** al llarg de la vora
(−2,05·10⁻¹⁰ a −7,6·10⁻¹¹) mentre que el **quocient es manté entre 0,978 i
0,989**. No és un pedestal de cel: és un **guany** d'un 1,4 % entre subconjunts
de fotogrames, la signatura del flat òptic que falta (`research/90`).

Tres canvis, cadascun mesurable:

1. **anivellament per les vores, no pel camp llunyà.** Una zona és a diversos
   llocs del llenç i la seva mediana llunyana no representa cap d'ells: el
   pedestal ajustat així valia 0,69 % i el graó real n'era 2,5 %;
2. **multiplicatiu**, resolt en log amb un sistema lineal petit i la zona de
   cobertura completa com a referència;
3. **zones = regions connexes**, no valors d'exposició: dues taques amb els
   mateixos 13,5 s poden venir de subconjunts diferents. El residu del sistema
   baixa de 0,0065 a **0,0021** en ln.

I el desenfoc de la correcció passa de 150 px a **8**: una correcció ha de
tenir la forma de la cosa que corregeix, i el graó és nítid. (Els 150 px eren
correctes per al pedestal antic **justament perquè no coincidia** amb el salt
local.)

| costura | ahir | ara |
|---|---:|---:|
| inferior | −2,064 % | **−0,754 %** |
| esquerra | −2,569 % | **−0,841 %** |
| dalt | −1,711 % | **−0,995 %** |

⚠️ El ~0,8 % que queda **és el flat òptic de la Sony que no s'ha aplicat**. Es
lliura visible, no tapat.

### 10.4 Dos terres, i cap d'ells pot ser una frontera

El compost sense cel es torna **negatiu** a partir d'uns 7,5 R☉ i el logaritme
hi explota. Es resol amb `ln(L + c)` i `c` = **σ del cel** (1,272·10⁻⁹ B/B☉),
que és una **constant** i per tant no pot dibuixar cap frontera. Amb això la
compressió del contrast a 3 R☉ és de ×1,2, contra ×2,5 si es filtra el compost
amb el cel a dins.

Dues coses que van sortir provant-ho:

- amb el terra absolut posat, el **terra relatiu** (15 % del perfil llis) sobra
  i **aplana l'11 % dels píxels** a un valor constant: les bandes hi donen zero
  exacte i queden altiplans de vora dentada. Es desactiva;
- el terra dur no pot ser `1e-30`: allà on `L + c` és negatiu, `ln` hi salta a
  −69 i deixa **un arc dur a 8 R☉**. Es limita a **un quart de `c`**, o sigui
  una excursió acotada a ln(0,25) = −1,39.

### 10.5 I el mapa polar no embolcallava l'azimut

`a_imatge` feia `remap` amb `BORDER_CONSTANT`: la fila θ = 0 es barrejava amb
el buit i deixava **una ratlla d'un píxel que sortia del Sol cap a la dreta i
travessava tota la corona**, perdent fins al 75 % de l'amplitud amb el radi.
L'angle és periòdic i ara s'embolcalla.

### 10.6 Estat final

`20260823T0500Z_FINAL2`, sobre el compost `20260823T0410Z_conn2`:

| control | valor | mostra |
|---|---:|---:|
| vora del marc Vixen | **0,032 σ** | 2.417.678 px |
| vora de la caixa Sony | **0,040 σ** | 1.934.614 px |
| sigmoide de fusió a 2,8 R☉ | **0,020 σ** | 631.252 px |
| G (envolupant isotònica) | **×1,044** | porta 1,5–6,9 R☉ |
| saturació del lliurable | **0,010 %** | amplitud automàtica p99,99 |

Les tres costures es mesuren ara sobre **milions de píxels reals**, no sobre
mostres de zeros. I el filtre arriba a les quatre cantonades del llenç.
