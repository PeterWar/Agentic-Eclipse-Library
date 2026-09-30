# 75 — Mesures del 16 d'agost: foscos, resolució, guany i calibratge absolut

**16 d'agost de 2026 · evidència mesurada sobre les dades de l'eclipsi**

Quatre auditories i una campanya de fotometria estel·lar, totes amb fase
adversarial. **On l'escèptic va trobar un error, mana ell**, i està dit a cada
punt. Aquest document és evidència: `research/73` és la referència de mètodes i
`research/74` el pla d'obra, i tots dos queden corregits pels números d'aquí.

Marcatge: **MESURAT** (sobre els fitxers) · **INFERIT** · **NO VERIFICAT**.

---

## 1. El banc de foscos: no hi havia cap dark dolent

⛔ **Es retira l'afirmació que un dels setze darks de 0,5 s «no era fosc».** Era
un artefacte de la mètrica.

**MESURAT** sobre els setze CR3 de 0,5 s, regió visible, sense desbayerar:
mediana **512,0 exacta** als setze, pedestal 512 als quatre plans de Bayer,
mitjanes que es diferencien en **0,022 ADU** entre elles, desviació 2,909–3,107.
Cap fitxer és anòmal. L'escombrada independent dels **768 darks** no en troba
cap de dolent (només cinc píxels solts d'impacte còsmic).

**L'origen del fals positiu, reproduït xifra per xifra:** el `frame_std` del
generador és `raw_image[::4,::4].std()` sobre el **RAW sencer, marge òpticament
emmascarat inclòs**. 572A3444 dona 55,0986 contra el 55,09858703613281 del JSON;
572A4030 dona 4,2956 contra 4,295562744140625. **La mètrica és cega a la imatge.**

**L'artefacte físic real existeix, i és fora de la imatge.** Les **files 0 a 7**
del marge emmascarat pugen de 512 a **525–1.576 ADU** a l'esglaó de 0,5 s, i
escalen amb la temperatura del cos: **133 ± 15 ADU/°C**, r = 0,962. Els
*lights* de la totalitat a 0,5 s el porten igual (572A2972 a 42 °C hi té
959–992 ADU), o sigui que és del cos i no del dark.

⛔ **Conseqüència dura: cap pas del postprocessat no pot estimar el nivell de
negre per fotograma amb les files de dalt del marge emmascarat**, ni als darks
ni als lights.

### 1.1 Les tres correccions de mètode que sí que calen

1. **No treguis cap fotograma del master de 0,5 s.** Refer-lo amb 11 mou la
   imatge +0,039 ADU i **puja el soroll de 1,171 a 1,273 ADU**. ⛔ Elimina del
   pla la instrucció «descarta qualsevol fotograma amb σ > 3,5»: **descartaria
   els setze**.
2. **Mitjana per píxel, no mediana.** La mediana deixa la imatge **0,132 ADU**
   massa baixa, perquè els enters estan molt quantitzats. El soroll també és
   lleugerament millor per mitjana (1,162 contra 1,171).
3. **El master de 10 s: pedestal real 511,50 ± 0,11**, no 511,0. El 511,0 surt
   de fer la mediana d'enters que seuen just entre 511 i 512. El dèficit real el
   governa la temperatura: **−0,0549 ± 0,004 ADU/°C** (r = −0,950). **Per a
   l'earthshine s'ha de fer servir el subconjunt de 41 °C** (vuit darks, nivell
   511,5667), que és la temperatura dels tres fotogrames de 10,3 s de la
   totalitat (572A2982 a 42 °C, 572A2983 i 572A2984 a 41 °C). El master de
   43–44 °C **sobre-resta 0,20 ADU** i importa 43 píxels calents per fotograma
   en lloc de 16.

### 1.2 Troballa que ningú buscava: la R6 canvia de mode de lectura

**MESURAT, tres proves independents.** Entre **0,5 s i 1 s** el cos canvia de
mode de lectura:

| | t < 1 s | t ≥ 1 s |
|---|---|---|
| Desviació de la imatge | 2,82–3,11 ADU | **1,12–1,21 ADU** |
| Mida de fitxer | ~20 MB | ~13 MB |
| Histograma | amb forats | continu |

**Cap etiqueta EXIF ho declara.** Conseqüència directa al G5: els fotogrames
d'earthshine tenen **2,6 vegades més abast útil** del que el pla els donava.

---

## 2. La resolució real dels dos trens

**MESURAT** amb un sol codi idèntic per als dos trens —tall de ganivet al limbe
lunar amb 240 sectors del **mateix arc angular** i ESF sobremostrejada— i
**desbiaixat** (l'estimador té biaix de signe oposat a cada tren).

| Tren | FWHM total, verd | Coll d'ampolla |
|---|---|---|
| Vixen VSD90SS + R6 III | **5,8 ± 0,4 ″** | el cel |
| Sony 300 GM + A7RIIIA | **8,3 ± 0,5 ″** | **difuminat propi** |

⚠️ **Els dos factors, i no es poden citar junts:** **1,51** és la raó **crua**
(5,5 / 8,3) i **1,40 ± 0,10** és la **desbiaixada** (5,8 / 8,3). Tres
estimadors independents convergeixen a 1,36–1,45.

**Per canal, al Vixen** (i és **de l'òptica, no del cel**: la Sony és
acromàtica amb el mateix cel als mateixos segons):

| | Vermell | Verd | Blau |
|---|---:|---:|---:|
| Vixen | **4,2–4,6 ″** | 5,5–5,8 ″ | 6,5–6,7 ″ |
| Sony | 8,8 ″ | 8,3 ″ | 8,7 ″ |

⛔ **La lluminància del Vixen ha de sortir del vermell i el verd.** El blau va
1,4 vegades més gruixut i és focus cromàtic residual del VSD90SS.

### 2.1 El seeing va ser molt millor del que s'havia estimat

L'estimació teòrica de `research/73` deia **4,6–12,2 ″** per extrapolació de
Kolmogorov a massa d'aire 6,4. **El valor real cau per sota de tot l'interval.**

El que està **MESURAT** és un **sostre**: el FWHM total del Vixen al vermell,
desbiaixat, val 4,76 ″; traient-ne el fotosit (2,158 ″) i la difracció (1,46 ″)
queda **≤ 3,98 ″ al vermell i ≤ 4,08 ″ al verd** per a seeing més òptica. Al
zenit, **≈ 1,3 ″** (INFERIT amb l'exponent 0,6).

⛔ **El valor central de 3,5 ″ i el terra de 2,8 ″ que un agent va publicar
queden retirats** per l'escèptic: el seu únic suport era una tendència amb el
temps d'exposició que s'esfuma quan es fan servir sectors comuns.

### 2.2 La Sony anava tova, i no per treure el filtre

**MESURAT als dos trens als mateixos segons, sobre el limbe solar FILTRAT:**

| Hora | Sony | Vixen |
|---|---:|---:|
| 19:38–19:47 | 4,68–5,42 ″ | 4,56 ″ (19:27) |
| 20:01 | **7,57 ″** | 4,08 ″ |
| 20:23:50 | **9,25 ″** | 5,62 ″ |
| Totalitat (C2 = 20:28:41) | 8,0–8,7 ″ | 5,5 ″ |

La pèrdua queda tancada dins el forat **19:50:42 → 20:01:22**, o sigui **27–38
minuts abans de C2 i amb el filtre posat**.

⛔ **Cau el lligam amb el testimoni de `research/72`.** Els salts de muntura sí
que van ser el filtre; **la pèrdua de nitidesa no**. La lliçó del 2027 canvia:
no és «comprova el focus després de treure el filtre», és **comprova'l cada deu
minuts durant tota la fase parcial**.

⚠️ Conseqüència de selecció: **les parcials filtrades de la Sony a partir de les
20:01 no serveixen com a referència de nitidesa**; les d'abans de les 19:50 sí.

### 2.3 El mostreig: la reixa crua va bé, els plans de Bayer no

| | Pas | Mostres per FWHM | |
|---|---:|---:|---|
| Reixa crua | 2,158 ″ | 2,5 | ben mostrejat |
| Cada pla de color | 4,32 ″ | **1,27** | **submostrejat 1,7×** |

**La prova, sense cap model:** la potència del senyal **supera la del soroll fins
al Nyquist mateix**, sense cap paret de resolució abans — raó **1,4–3,1** al
Nyquist de la reixa verda en quincunx (període 6,10 ″) i **3,3–5,8** al d'un pla
(8,63 ″). Un sistema limitat per la borrositat cau **abans** d'arribar-hi.
Contrast residual: **MTF 0,23** al Nyquist del pla i **0,08** al de la reixa
verda.

✅ **I la deriva de la muntura és el ditherat que cal per recuperar-ho.** El
Vixen derivava **0,610 ± 0,010 ″/s = 0,28 px/s** de manera **constant tota la
totalitat**, o sigui que fotogrames separats pocs segons tenen fase subpíxel
diferent. N'hi ha **25 dins la totalitat només a 1/3200**. El drizzle **no
canvia el FWHM** sinó que recupera el contrast a les escales que ara s'alienen
i deixa la PSF ben mostrejada perquè la deconvolució hi pugui treballar.

---

## 3. Guany, soroll i les protuberàncies

**MESURAT** amb corba de transferència de fotons sobre parelles de fotogrames
(diferència → variància per fotograma). Ajust var = S/g + RN².

| | Guany | Soroll de lectura |
|---|---|---|
| **R6 III, ISO 100** | **5,08 ± 0,10 e⁻/ADU** (verd) | **2,72 ADU** si t < 1 s · **1,05 ADU** si t ≥ 1 s |
| **A7RIIIA, ISO 100** | **3,41 ± 0,07 e⁻/ADU** | **1,22 ADU** |

Poisson pur confirmat: variància / (S/g + RN²) = **0,92–0,98** (R6) i
**1,02–1,09** (Sony), d'1 a 12.000 ADU.

**Les protuberàncies NO estan limitades per fotons.** Al pic, a 1/125 s, el R6
hi recull **66.000 e⁻ per píxel cru** → **S/N de Poisson 257:1**; a 1/2000
encara 68:1. A la banda espacial més fina, S/N = 34 al vermell. **El que les
limita és la PSF**, o sigui que la deconvolució té marge real.

**Tres avisos MESURATS:**

- ⛔ **El pla blau del R6 dona 4,33 ± 0,04 e⁻/ADU**, un 15 % per sota del verd,
  repetible i sense explicació. **Exclòs de tot càlcul de pesos i de fotometria**
  fins que s'expliqui.
- ⚠️ **L'A7RIIIA filtra espacialment el RAW als 8 s**: autocorrelació del soroll
  **+0,42 a lag 1** (contra +0,04 als 2 s) i **20–29 % menys variància** de la
  que els fotons imposen. Cau **justament sobre les tres àncores d'earthshine**:
  l'apilat hi guanya menys de √N i la resolució ja s'ha perdut al fitxer. El R6
  no ho fa a cap exposició.
- ⚠️ Entre fotogrames separats 6 s, la diferència a les protuberàncies és
  **2,5–6,3 vegades** el soroll de fotons: visió anisoplanàtica. Cal **registre
  subpíxel local**, no global rígid.

---

## 4. Els flats: veredicte matisat

**Per a la imatge, no calen. Per a la fotometria del camp, sí que ajudarien.**

**MESURAT o llegit de font primària:**

- **Sony 300 GM a f/2,8: −0,214 EV a la cantonada**, del perfil `.lcp` d'Adobe
  del Mac, confirmat pels paràmetres de fàbrica dins de cada ARW (∝ r²).
- **VSD90SS**: cercle d'imatge de 60 mm amb >90 % d'il·luminació a la vora; la
  cantonada de format complet cau a r = 21,6 mm → **< 0,15 EV** (INFERIT de la
  fitxa oficial).
- **Sobre el camp que ocupa la corona** (fins a 3 R☉): variació **1,8 %** (Sony)
  i **1,6 %** (R6).
- **Pols: 0,10 % rms i ≤ 0,3 % de pic** al R6, ≤ 0,33 % a la Sony. Cap anell ni
  donut. I és del sensor: correlació +0,78 alineat al sensor, −0,63 alineat al
  Sol.
- **PRNU ≲ 0,2 %**.

**Què fer:** a la Sony, aplicar el polinomi del `.lcp` **en domini lineal**, amb
el pedestal restat i abans de qualsevol estirada:
`T(r) = 1 − 22,133597 r² − 4187,240553 r⁴ + 642257,67942 r⁶`, amb
`r = px × 4,51 µm / 300 mm`. Al R6, deixar-ho estar o bé `1 − 0,15 (r/rc)²`.
Hi ha **tres flats de fotosfera gratuïts**: `572A2906`, `572A2907`, `572A2908`.
⛔ **`572A2905` no**: té 99.332 píxels a nivell blanc.

⚠️ **Matís del §5.3, i és el que reobre la qüestió**: sense flats,
**extinció i vinyetatge no se separen**. Els dos trens miraven la mateixa
atmosfera i donen gradients de **0,416 ± 0,050** i **0,723 ± 0,037** mag per
massa d'aire: **5,0 σ**. Almenys un està dominat pel vinyetatge. Un joc de flats
fet **ara**, amb la mateixa òptica i obertura, els separaria — **la pols haurà
canviat, però el vinyetatge no**, si no s'ha tocat el diafragma.

---

## 5. Estrelles: camp resolt i calibratge absolut

Cerca **cega** als dos trens —sense catàleg— i creuament posterior amb Tycho-2 +
Hipparcos i skyfield/DE440s.

| Tren | Fonts cegues | Identificades | Residu de placa | Espera per atzar |
|---|---:|---:|---:|---:|
| Sony | 38 | **38 de 38** | 0,54 px (màx. 1,79) | 0,02 coincidències |
| R6 III | 24 | **22 de 24** | 0,32 px (màx. 0,65) | 0,00 |

Cap estrella satura: el pic més alt és 15.161 ADU contra un sostre de 16.383.
Hi són **8 Leonis** (V=5,73; magnitud reconstruïda amb **0,004 mag** d'error),
**HIP 46232** (6,31), **7 Leonis** (6,32), **HIP 45874** (6,57), **HIP 46713**
(6,92)… La més feble identificada és **V = 9,18**.

**El que limitava no era el sensor ni l'exposició: era el cel.** Brillantor de
fons mesurada a 8 R☉: **9,34 (Sony) i 9,15 (R6) mag/arcsec²** —coincideixen a
0,19 mag—, entre 1,7 i 4,9 magnituds més brillant que qualsevol hipòtesi prèvia.

### 5.1 El camp resolt

| | Sony | R6 III |
|---|---|---|
| Escala | **3,2020 ″/px** (−0,99 % del 3,234) | **2,1495 ″/px** (−0,39 %) |
| **Nord celeste** | **PA 90,27°** | **PA 57,19°** |
| Est | 358,64° | 325,59° |
| Mirall | no | no |
| Centre del **Sol** | (3894,7 , 2768,7) px | (3570,8 , 2267,1) px |
| Residu rms | 0,71 px (2,3 ″) | 0,42 px (0,9 ″) |

⚠️ **L'escala de la Sony no passa la porta de l'1 %.** Amb 38 estrelles i
0,71 px de residu, l'astrometria és molt més forta que l'ajust del diàmetre
lunar. La focal implicada passa de 288 a **290,5 mm**. **Recomanació: adoptar
3,2020 ″/px** i deixar la discrepància oberta.

**Refracció diferencial, i és metodològica.** Amb el Sol a 9° el camp queda
comprimit **0,77 % (Sony) i 0,80 % (R6)** en vertical, i els dos cossos donen la
mateixa no-perpendicularitat aparent (−0,438° i −0,457°): **és el cel, no
l'òptica**. Al marc horitzontal refractat cau a −0,026° i −0,006° i les dues
càmeres passen a ser similituds pures. ⛔ **El G4 i qualsevol apilat de gran
camp han de treballar en alt/az refractat.**

✅ **Validació de regal, i no es buscava.** Amb la solució de placa, l'eix nord
lunar cau a **71,97°** al sensor Sony. El producte `Earthshine_FINAL` havia
**ajustat 71,5°** contra el mapa LROC **sense saber res d'estrelles**.
**Coincideixen a 0,47°**, tan bo com el mètode permet distingir.

### 5.2 El calibratge absolut

| | Sony (X=6,08) | R6 (X=6,02) |
|---|---|---|
| **Punt zero** | **+14,17 ± 0,08 mag** | **+14,21 ± 0,08 mag** |
| **Factor a B/B☉** (per ADU/s i píxel verd) | **1,134 × 10⁻¹¹** | **2,772 × 10⁻¹¹** |
| Incertesa | **±10 %** | **±10 %** |

**Els dos trens coincideixen**: diferència de punt zero −0,038 ± 0,076 mag, i
sobre la corona real entre 1,15 i 3 R☉ el quocient R6/Sony és **0,95**. L'estat
de l'art en aquest terreny és un factor 2 (el mateix Bemporad discrepa d'un
factor ~2 amb MLSO); **estem a un 5 %**.

**Tres correccions de l'escèptic, i manen elles:**

1. **Els factors publicats primer eren erronis.** Faltava el terme de color al
   Sol: `F☉ = 10^(0,4·(ZP + 26,75 − 0,653·c))`. Biaix −4,5 % i +9,4 %, de signe
   contrari. ⛔ **Corregit, el quocient de corona passa de 0,83 a 0,95 i la
   hipòtesi de llum difosa interna del 300 GM es retira: no queda res per
   explicar.**
2. ⛔ **`k = 0,416` NO és el coeficient d'extinció** (§4). El 0,37 del projecte
   **no queda ni confirmat ni desmentit**. El punt zero al centre del camp,
   això sí, amb prou feines es mou (+14,09 a +14,22 en cinc models).
3. **Els SNR de la cerca cega s'han de dividir per 1,5–2.** Soroll combinat
   mesurat amb obertures buides: 53 ADU/s a 9–14 R☉, 79 a 6–9, 87 a 4–6, 162 a
   2,6–4 i **1.780 a 1,6–2,6**. ⛔ **HIP 46335 i HIP 46345 no s'han de fer
   servir per calibrar.** I **HIP 45824 / TYC 1403-1015 és una doble no
   resolta**: fora dels calibradors.

**El que sí que està provat per injecció**: la fotometria d'obertura amb anell
26–40 px és **insesgada al 3–4 %** de 2,6 a 14 R☉.

⚠️ **El criteri de Bemporad de 0,1 mag no es compleix globalment** (mediana 0,16
i 0,20; només un terç dins de 0,10). Substituir-lo per **la diferència entre
trens**, on la V de catàleg cancel·la: **0,32 mag per fora de 6 R☉** i 0,96 per
dins.

### 5.3 Les ales de la PSF: objectiu no lliurat, i és un límit dur

**MESURAT** amb la prova d'integral: el perfil estel·lar és fiable **fins a
13 px (42 ″) a la Sony** i **fins a 30 px (64 ″) a la R6**. Més enllà s'infla
fins a 11,8 vegades el flux de l'estrella: allò ja és corona.

⛔ **No es pot validar el model de halo amb estrelles**, i el motiu és físic: el
model dispersa el 4,30 % de la llum però **el 97,5 % cau més enllà de 100 px**,
i a 87,5 px el model prediu 7,4×10⁻⁸ per píxel mentre el terra sistemàtic
mesurat és 2,1×10⁻⁴ — **2.800 vegades per damunt**. **La corona interior és
~200.000 vegades més brillant que l'estrella més brillant del camp i el seu
propi halo enterra qualsevol halo estel·lar.**

Al tram estret on se solapen (3–13 px) **la forma casa**: pendent mesurat
r^−2,3 contra r^−2,2 del nucli s=6, β=1,5. Això **no és un defecte del model**:
aquell tram és el nucli de seeing i el halo s'ajusta dins del disc lunar.

➡️ **La validació del halo ha de venir de la fotosfera filtrada de la fase
parcial, no d'estrelles.** Anotar-ho com a límit dur, no com a deute.

### 5.4 I dues coses del muntatge que valen més que el catàleg

- ⚠️ **El salt de la muntura Sony va portar una rotació de camp de 0,138°**, no
  només translació, i hi queden **2,2 px de distorsió òptica** que cap
  translació no arregla. Qui apili els segments amb una translació pura, ho
  paga.
- ✅ **La deriva del Vixen queda resolta i el 18 % de discrepància desapareix.**
  Mesurada dues vegades per camins independents: **0,610 ± 0,010 ″/s** del
  moviment fotograma a fotograma i **0,625 ± 0,042 ″/s** de la llargada del traç
  dins de cada exposició de 10,3 s (traç real **6,4 ″ = 3,0 px**). Direcció
  −45,0° al sensor i **constant tota la totalitat**: aquest tren **no va fer cap
  salt**. Confirma el 0,61 ″/s de `research/71` per a la totalitat i deixa clar
  que el **0,689 ″/s d'aquell document és el valor post-C3**, un 11 % més alt
  perquè hi pesa més la refracció amb el Sol més baix.

---

## 6. Números que canvien als altres documents

**A `research/74`:**

- **G1 es tanca** reescrivint §4/R3: no hi ha «dos defectes sense diagnosticar».
- **G2-bis**: el sostre de linealitat del 85 % es calcula amb el pedestal real →
  verd = 511,5 + 0,85·(16383 − 511,5) = **14.002 comptes**, no 13.940. El guany
  ja no s'hi deriva: està mesurat (§3).
- **G5**: el terra de 5σ **no és 14 comptes per a tota l'escala**. Per a
  t < 1 s, 13,6; **per a 2 s i 10,3 s, 5,3 comptes**. I els pesos trapezoïdals
  se substitueixen pels òptims: **w = 1/(S/g + RN²)**.
- **G7a**: el R6 passa la porta de l'1 %; **la Sony falla** (−0,99 %). Adoptar
  3,2020 ″/px. El criteri de Bemporad se substitueix per la diferència entre
  trens (≤ 0,35 mag per fora de 6 R☉). L'objectiu «ala de la PSF» **no es
  lliura** (§5.3).
- **Radis, amb l'escala nova i el centre del SOL** (no el lunar; eren 3,1 px i
  6,4 px de biaix): Sony, radi solar 296,5 → **295,8 px** i radi lunar 305,7 →
  **308,7 px**; R6, radi lunar 458,2 → **460,0 px**.
- **G3/G5 guanyen ancoratge absolut**: amb B/B☉ = 1,134×10⁻¹¹·I (Sony) i
  2,772×10⁻¹¹·I (R6), ±10 %, el compost es pot comparar amb **LASCO C2 i K-Cor**
  sense mesurar la densitat òptica del filtre. **Afegir-ho com a criteri de pas
  del G5.**
- **G7b (el 6D) puja de prioritat**: el cel feia 9,2 mag/arcsec² i és la
  component dominant que el G3 no sap separar.

**A `research/73`:** l'estimació de seeing de 4,6–12,2 ″ del §2.8 queda
**desmentida per mesura** (§2.1 d'aquí), i el veredicte «l'ACHF guanya pel
detall fi que aquests trens no poden cobrar» **es reforça però per un altre
motiu**: no és que el cel no donés per a més —en donava—, és que **cada pla de
Bayer no ho podia mostrejar** (§2.3).
