# 117 — CapesTotalsV14: la maqueta de Pere amb la dada calibrada, i què embrutava el limbe

Encàrrec de Pere, 27-08-2026: «agafa CapesTotalsV13.psd i estudia'l en profunditat […] fes
CapesTotalsV14.psd en el que per cada capa i màscara que tenia la V13, fes una capa amb la
imatge calibrada corresponent i preserva la màscara que hi ha ara a la V13», amb tres
diferències: **el llenç d'avui** (el que encabeix la Sony), **alineació amb la corona**
—imatges i màscares— i **el limbe lunar net a cada capa**.

Tot el que hi ha aquí és de **només lectura** sobre els actius: la V13, el run `017` i els
RAW no s'han tocat. Fitxers nous: aquest document, `research/tools/capes_totals_v14/` i
`CapesTotalsV14.psd` + `CapesTotalsV14_REBUT.md` + `CapesTotalsV14_vistes/` al costat de la
V13.

---

## 0. Resum en sis línies

1. **El llenç de la V13 està identificat i mesurat**, no suposat: és la **graella del sensor
   de la Vixen sense girar**, amb la zona visible del RAW a l'offset (457, 463) d'un llenç
   de 7648×5353 (§1).
2. ⛔ **I les seves capes NO estan registrades entre elles**: cada una seu a la posició
   **crua** del seu fotograma. El limbe lunar hi cau a **≤2,3 px** d'on la cadena diu que és
   la Lluna d'aquell fotograma, **sense aplicar-hi cap desplaçament**. Entre la capa de
   1/3200 (t = 13,1 s) i la de 10,3 s (t = 42,2 s) el Sol es mou **8 px**: aquesta és
   l'alineació que faltava (§1).
3. **El limbe brut de la V13 té una causa sola i es pot escriure en una frase**: *una
   màscara demana píxels que la seva exposició no té.* Passa dins del disc lunar —la capa de
   10,3 s hi té la màscara a 0,33— i a la **vora interior** de cada esglaó, que és el radi
   on deixa d'estar saturat i que renderitzat és exactament un halo (§2).
4. **La cura no pinta res**: `màscara_V14 = màscara_V13 · validesa_de_la_capa`, amb la
   validesa mesurada del pes de la composició. El disc lunar passa de **0,137** (V13) i
   **0,024** (V13_Pere) a **0,0000** (§3).
5. **El perfil radial es gira**: la V13 té el màxim a **2,0 R☉** —o sigui que la corona
   interior hi és més fosca que la mitjana— i la V14 el té a **1,07 R☉** i baixa monòtona
   d'allà cap enfora (§3).
6. ⏭️ **El muntatge per capes reinstal·la, atenuat, el defecte de fusió que el LDIC evita
   per construcció**: l'ondulació a les fronteres val **0,21 % del nivell**, contra l'1,1-1,3 %
   que `research/100` va mesurar entre esglaons veïns. Les màscares suaus de Pere el
   divideixen per cinc (§4).

---

## 1. Què és el llenç de la V13, i què hi falta

`research/108` ja havia establert què és la V13 —12 capes planes, 7648×5353, la corba de to
que el projecte fa servir avui— però no on seu. Es mesura així:

- els marges del RAW de la R6 III són `left_margin` 172 i `top_margin` 108, i la zona
  visible fa 6960×4640; les capes de la V13 tenen la bbox **(457, 463)–(7417, 5103)**, que
  fa exactament 6960×4640. O sigui `sensor_x = X13 − 285`, `sensor_y = Y13 − 355`;
- s'ajusta el **limbe lunar** a cada capa de la V13 per **màxim de gradient** (no per
  llindar: les capes estan tonificades i un llindar de mig nivell es mou amb la corba) i es
  compara amb el que la cadena mesura al fotograma que la va originar.

| capa | fotograma | t (s) | Lluna V13 → sensor | Lluna de la cadena | diferència |
|---|---|---:|---|---|---|
| 12 | 572A2956 | 13,08 | (3751,11 · 2385,04) | (3751,61 · 2385,95) | (−0,50 · −0,91) |
| 11 | 572A2968 | 21,37 | (3751,33 · 2383,62) | (3751,24 · 2383,27) | (+0,09 · +0,35) |
| 10 | 572A2969 | 22,27 | (3751,71 · 2383,46) | (3751,20 · 2382,98) | (+0,52 · +0,48) |
| 09 | 572A2975 | 28,34 | (3748,61 · 2380,74) | (3750,91 · 2381,02) | (−2,29 · −0,28) |
| 08 | 572A2970 | 23,19 | (3750,29 · 2382,43) | (3751,15 · 2382,68) | (−0,86 · −0,25) |
| 06 | 572A2971 | 24,12 | (3749,98 · 2381,59) | (3751,10 · 2382,38) | (−1,12 · −0,79) |

**Sense cap desplaçament de registre**, el limbe cau a ≤2,3 px. La pitjor és la capa 09 i té
motiu propi: és un apilat de dos fotogrames separats **62 s**, o sigui que la seva Lluna ja
hi surt escombrada 17 px i el cercle ajustat n'és la mitjana.

⚠️ **L'escala és 1.** El limbe mesurat a la V13 val 451,8-453,7 px i la cadena en mesura
**452,36** de mediana als seus 56 fotogrames: són píxels del mateix sensor. (El 455,50 del
rebut és el radi d'**efemèride**, que no és una mesura del limbe — la diferència és el
mateix biaix del màxim de gradient als dos costats.)

⏭️ **Conseqüència per a la V14**: cada màscara es porta amb el **Sol del seu fotograma**, no
amb un de comú. La imatge la torna a registrar la cadena; la màscara ha de seguir el mateix
registre. És el que vol dir «ajusta tant imatges com màscares».

---

## 2. Què embrutava el limbe: una màscara demanant el que no hi ha

Dos llocs, un sol mecanisme:

- **Dins del disc lunar.** La capa de 10,3 s hi té la màscara a **0,33** i al limbe a
  **0,50** (`research/87` §1): és el vel que renta la Lluna. Allà no hi ha dada de cap
  exposició llarga —està tota saturada o tapada—, o sigui que el que entrava era
  desbordament, no imatge.
- **A la vora interior de cada exposició.** Cada esglaó deixa d'estar saturat a un radi
  propi, i aquella vora renderitzada **és un halo al voltant de la Lluna**:

| capa | exposició | vora interior de la dada |
|---|---|---|
| 12 | 1/3200 s | 1,02 R☉ |
| 11 | 1/500 s | 1,03 |
| 10 | 1/125 s | 1,03 |
| 09 | 1/60 s | 1,04 |
| 08 | 1/30 s | 1,09 |
| 07 | 1/15 s | 1,15 |
| 06 | 1/8 s | **1,17** |
| 05 | 1/4 s | 1,23 |
| 04 | 1/2 s | 1,31 |
| 03 | 1 s | 1,41 |
| 02 | 2 s | 1,53 |
| 01 | 10,3 s | **1,96** |

⏭️ La de 1/8 s és **la que Pere va marcar el 27-08** creient que era un artefacte del
producte, i tenia tota la raó de marcar-la: res no li deia que aquella vora és el límit de
l'exposició.

---

## 3. La cura, i què mesura

**`màscara_V14 = màscara_V13 · validesa_de_la_capa`**, amb la validesa = els tres canals amb
pes per damunt del que és **assolible al mateix radi** (`comu.mascara_dada`) i una vora suau
de σ 1,6 px. Cap píxel de màscara s'ha repintat.

Cinc portes, totes sobre el fitxer escrit:

| porta | resultat |
|---|---|
| **A** · el transformat | limbe a **0,97 px** de mediana i 2,31 de màxim (llindar 3) · PASSA |
| **B** · cap màscara demana el que no hi ha | **0 px** de 12 capes · PASSA |
| **C** · el disc lunar és net | **0,0000** de mitjana i de p99, contra **0,137** (V13) i **0,024** (V13_Pere) · PASSA |
| **D** · perfil monòton | màxim a **1,07 R☉** (la V13 el té a **2,0**), 8 pujades de 238 calaixos, la pitjor 0,00026 · PASSA |
| **E** · cap halo | ondulació màxima **0,208 %** del nivell (llistó 1,1 %) · PASSA |

El perfil del nivell mostrat:

| r (R☉) | V13 | maqueta de Pere | **V14** |
|---|---|---|---|
| 1,09 | 0,518 | 0,631 | **0,688** |
| 2,15 | **0,719** (màxim) | 0,404 | 0,331 |
| 3,74 | 0,484 | 0,212 | 0,265 |
| 5,33 | 0,429 | 0,175 | 0,249 |

⏭️ **La V14 segueix la forma de la maqueta fins a ~2,7 R☉ i d'allà s'aplana a 0,245**, perquè
allà **el que hi ha és el cel** i el compost el porta com un terra pla. A la V13 el cel no
s'havia tret i el seu propi nivell queia amb el radi —el vinyetatge—, i això li donava un
gradient que semblava corona.

---

## 4. El preu d'un muntatge per capes, mesurat

⛔ **El LDIC de la cadena no té fronteres i per això no té costures**; un muntatge per capes
sí que en té, una a la vora interior de cada esglaó. `research/100` va mesurar que els
esglaons veïns d'aquesta escala discrepen **1,1-1,3 % amb el signe alternat** (dues mitges
escales de 2 EV que són dos instants diferents, amb la transparència caient un 8 % durant la
totalitat): aquell és el terra físic de qualsevol muntatge per capes d'aquesta dada.

A la V14 l'ondulació val:

| capa | vora | ondulació |
|---|---|---|
| 07 · 1/15 s | 1,15 R☉ | +0,000 % |
| 06 · 1/8 s | 1,17 | −0,002 % |
| 05 · 1/4 s | 1,23 | +0,003 % |
| **04 · 1/2 s** | **1,31** | **+0,208 %** |
| 03 · 1 s | 1,41 | −0,076 % |
| 02 · 2 s | 1,53 | +0,056 % |
| 01 · 10,3 s | 1,96 | +0,000 % |

O sigui **cinc vegades per sota** del terra de l'escala, i com una ona ampla d'1,25 a 1,50 R☉,
no com una vora. Les màscares suaus de Pere fan de filtre. **No és zero i no s'ha
d'oblidar**: si algun dia el muntatge per capes passa a ser el lliurable, aquesta és la seva
signatura, i la cura és la del §1 quater de `CLAUDE.md` (escala monòtona el 2027).

---

## 5. Dues decisions que calia prendre, i per què

**La capa 12 va amb UN SOL fotograma.** A les altres, combinar els fotogrames del seu esglaó
és estrictament millor —l'escena és la corona i no es mou—, però aquí l'escena **sí** que
canvia: les perles són la fotosfera desapareixent darrere les muntanyes de la Lluna, i el
`max` sobre la finestra de C2 que fa `f4.psb_contactes` en dibuixa la **unió**, un collaret
que no va existir a cap instant. La V13 en tria un (572A2956) i la V14 tria el mateix.

**Els píxels saturats d'aquella capa es declaren COTA INFERIOR, no mesura.** A 1/3200 s la
fotosfera de les perles satura i **no hi ha cap exposició més curta que la rescati** (tota la
finestra de C2 de la R6 III va a 1/3200). Deixats com a «sense dada» —que és el que la
cadena fa— les perles surten clapejades de forats. S'omplen amb el sostre de la finestra i el
rebut diu quants n'hi ha.

---

## 6. El que NO s'ha fet

- **cap màscara repintada**, cap capa d'ajust, cap corba a sobre;
- **cap filtre circular** (norma del rectangle): el que talla és la manca de dada;
- **cap capa de la Sony**: l'encàrrec era capa per capa sobre la V13, que és Vixen sola. El
  llenç és el comú i hi cap; afegir-l'hi és un pas a part;
- **cap capa de detall**: el que hi ha a cada capa és la **BASE calibrada**. Els plomalls que
  la V13 ensenyava els porta el revelat directe dels RAW; a la cadena d'avui el detall va a
  part, en Superposar, i viu al PSB del run.

---

## 6 bis. La Lluna no era rodona, i el Sol hi faltava

Pere, en obrir la primera V14: «respecte el Sol i la Lluna que hi havia a la V13,
posa'ls a la V14». Tenia raó i és mesurable.

**El mecanisme.** El llenç va centrat al **Sol**, o sigui que **la Lluna hi
llisca**: 24,8 px en x i 13,9 en y al llarg de la totalitat —28,5 px, el **6,3 %
del seu radi**—. Si cada capa es queda amb el forat dels seus propis fotogrames,
la silueta que en surt no és un cercle sinó la **intersecció** dels discos. A la
primera V14, contra el disc de C2:

| | px |
|---|---:|
| corona **dins** del disc de C2 (el costat que la Lluna deixa enrere) | **16.643** |
| negre **fora** del disc de C2 (la mossegada, fins a **23 px** enllà del limbe) | **8.293** |

I la mossegada queia justament sobre la **protuberància**, que sortia escapçada.

⚠️ **I una capa no ho pot arreglar sola**: al creixent, les capes coronals tenen
dada al **65 %** dels píxels i prou —el 19 % perquè la Lluna hi era a tots els
seus fotogrames, i el 21 % perquè la **màscara global del run** tampoc no hi
arriba—. Els píxels just fora del disc de C2 pel costat de darrere **no els té
cap fotograma coronal**: els té només el bloc de contacte de C2.

**La cura és la decisió que Pere ja havia pres el 27-08** —treballar només en C2
perquè la Lluna surti rodona—, aplicada també DINS de la totalitat:

1. **la Lluna es DECLARA**: un sol disc, centrat a (4057,94 · 4470,31) px, que és
   la posició mitjana de la Lluna als quatre fotogrames de contacte de C2
   (dispersió **0,27 px**), amb el radi d'efemèride i la mateixa guarda i vora
   que `f2.mascara_lluna`. **Totes** les màscares hi van a zero;
2. **el Sol el posa una capa 13**, les protuberàncies de C2 en mode **Aclarir**,
   que és exactament la que la cadena posa al seu propi producte
   (`f4.psb_resultat`, capa 09). Torna a tancar l'anell del limbe que el disc
   declarat i les vores de cada exposició deixen obert.

**Porta F, nova**: el radi de la silueta negra, raig a raig sobre 720 azimuts.

| | primera V14 | ara |
|---|---:|---:|
| desviació màxima del radi | **23 px** | **1,5 px** |
| rms | — | **0,49 px** |

⚠️ **El preu, declarat**: es perd la mica de corona que als fotogrames tardans es
veia dins del disc de C2. És el mateix preu que Pere ja havia acceptat.

⏭️ **I una cosa que la V13 tenia i la V14 no**: el seu disc lunar no era negre
del tot (0,024 al `V13_Pere`). **No és earthshine**: mesurat, el nivell puja
monòtonament del centre (0,0168) al limbe (0,0689) i **no hi ha cap detall
lunar** — és llum de la corona escampada per l'òptica. L'earthshine de veritat
demana una pila a part, emmascarada al revés i registrada a la **Lluna** i no al
Sol (`research/112` §7), i continua pendent.

⚠️ **Defecte de mètode destapat pel camí**: el selector «el darrer run VIXEN
CIENCIA» va agafar el `018` **mentre s'estava executant** i la cadena va petar
buscant un rebut que encara no existia. Ara el selector exigeix que hi siguin
**tots** els fitxers que l'eina llegeix.

---

## 7. ⛔ La trampa que va deixar el fitxer sense obrir-se

El primer `CapesTotalsV14.psd` es va escriure bé segons tots els controls que hi
havia: `psd-tools` el rellegia amb les seves dotze capes i les seves màscares, i
les cinc portes de contingut passaven. **Photoshop el va refusar**: «no és
compatible amb aquesta versió».

Aïllat amb una matriu de **2 formats × 4 compressions** (fitxers de 600×400,
llegits amb `sips`, que és ImageIO de macOS):

| compressió de la secció `Image Data` | PSD | PSB |
|---|---|---|
| `RAW` | obre | obre |
| `RLE` | obre | obre |
| **`ZIP`** | **NO** | **NO** |
| **`ZIP_WITH_PREDICTION`** | **NO** | **NO** |

⏭️ **No era el format.** La sospita fàcil era que el projecte sempre havia escrit
PSB i aquell era el primer PSD; la matriu ho descarta en cinc segons. El que no
admet ZIP és la **imatge fusionada**. Les **capes** sí que hi van —i per això tot
semblava bé—. `f4.set_merged` ja feia servir `RAW` per defecte, que és per què
cap lliurable anterior del projecte no ho havia destapat: el defecte va entrar en
«optimitzar» la mida del fitxer.

⏭️ **La regla que se'n treu no és de PSD:** *el lector que et diu que un fitxer
està bé no pot ser el mateix que l'ha escrit.* Ara `fes_v14.py` acaba amb
`comprova_obrible()`, que exigeix **dos lectors independents** —`psd-tools` per a
l'estructura de capes i **`sips`** per a la fusionada— i falla allà mateix.
Comprovació d'una línia per a qualsevol PSD/PSB futur:

```bash
sips -g pixelWidth -g pixelHeight fitxer.psd
```

Si en torna `<nil>`, Photoshop tampoc no l'obrirà.
