# Síntesi de les quatre auditories — 16 d'agost de 2026

Aquest informe incorpora les dues refutacions. On l'escèptic ha trobat un error, mana ell.

---

## 1. El dark dolent

**No n'hi ha cap.** L'alarma era de la mètrica, no de les dades.

- **MESURAT** (els setze CR3 de 0,5 s, regió visible, float64, sense desbayerar): mediana 512,0 exacta als setze, pedestal 512/512/512/512 als quatre plans de Bayer, mitjana entre 512,2264 i 512,2486 ADU (dispersió total **0,022 ADU**) i desviació típica de 2,909 a 3,107 ADU. Cap fitxer és anòmal.
- **MESURAT i REPRODUÏT xifra per xifra**: el `frame_std` del generador és `raw_image[::4,::4].std()` sobre el **RAW sencer**, marge òpticament emmascarat inclòs. 572A3444 dona 55,0986 contra 55,09858703613281 del JSON; 572A4030 dona 4,2956 contra 4,295562744140625. La mètrica és **cega a la imatge**.
- L'artefacte físic real existeix però és fora de la imatge: **les files 0 a 7 del marge emmascarat** pugen de 512 a 525–1576 ADU a l'esglaó de 0,5 s, escalant amb la temperatura del cos (r = 0,962; pendent 133 ± 15 ADU/°C, residu 68 ADU). Correcció a la versió anterior del diagnòstic: **són vuit files, no quatre** — als cinc fotogrames de 44 °C les files 2, 3, 6 i 7 també pugen (514,7–520,4 contra 513,3). Els *lights* de la totalitat a 0,5 s el porten igual, o sigui que és del cos.
- **Escombrada independent dels 768 darks** amb estadístics de la regió visible: cap fitxer dolent (només cinc píxels solts d'impacte còsmic). L'EXIF és homogeni.

**Què canvia arreglar-ho:**

1. **No treguis cap fotograma del master de 0,5 s.** Refer-lo amb 11 mou la imatge +0,039 ADU i puja el soroll de 1,171 a 1,273 ADU (MESURAT). El que sí que val la pena és **mitjana per píxel en lloc de mediana**: la mediana deixa la imatge 0,132 ADU massa baixa (enters molt quantitzats).
2. **El 511,0 del master de 10 s és mig real i mig arrodoniment.** Nivell veritable **511,4995 ± 0,113 ADU** (25 darks, cap fora de distribució); la mediana d'enters que seuen entre 511 i 512 exagera el dèficit 0,5 ADU. El dèficit real el governa la temperatura: **−0,0549 ± 0,004 ADU/°C** (r = −0,950).
3. **Per a l'earthshine, el subconjunt correcte és el de 41 °C** — vuit darks, nivell 511,5667, soroll 3,067 ADU — perquè els tres fotogrames de 10,3 s de la totalitat són 572A2982 (42 °C), 572A2983 i 572A2984 (41 °C). El master «calent» de 43–44 °C que s'havia recomanat **sobre-resta 0,20 ADU** i importa 43 píxels calents per fotograma en lloc de 16. La distribució no és bimodal: 38 °C×2, 39×1, 40×4, 41×8, 43×2, 44×8.
4. **Cap pas del postprocessat no pot estimar el negre per fotograma amb les files de dalt del marge**, ni als darks ni als lights.
5. **Segona signatura, no vista abans i més gran que la primera:** entre 0,5 s i 1 s el cos **canvia de mode de lectura**. Desviació de la imatge 2,82–3,11 ADU fins a 0,5 s i **1,12–1,21 a 1 s**, mida de fitxer de 20 MB a 13 MB, i l'histograma deixa de tenir forats. Cap etiqueta EXIF ho declara (MESURAT, tres proves independents).

---

## 2. La resolució real

Números **MESURATS** amb un sol codi idèntic per als dos trens, en arcsec, i **desbiaixats** segons l'auditoria (l'estimador té biaix de signe oposat a cada tren: −4/−5 % al Vixen i +4/+6,5 % a la Sony):

| Tren | FWHM total, verd | Coll d'ampolla |
|---|---|---|
| Vixen VSD90SS + R6 III | **~5,8 ± 0,4 ″** | el cel (seeing + dispersió) |
| Sony 300 GM + A7RIIIA | **~8,3 ± 0,5 ″** | ell mateix (difuminat propi) |

**Guanya el Vixen per un factor 1,40 ± 0,10 en angle i ~1,9 en àrea** — no els 1,51 i 2,28 publicats. Tres estimadors independents hi convergeixen: per sector 6,0 contra 8,4 (1,40), amplada crua 10–90 % 6,7 contra 9,45 (1,41), apilat desbiaixat 1,36–1,45.

Dues correccions obligades:

- **La mitjana Sony és 8,27 ″, no 8,04.** DSC07000 i DSC07003 tenen 3,7 % i 2,9 % de píxels a nivell blanc: és la fotosfera sortint a C3. El «rang real 6,78–8,71» s'ha de reescriure **7,8–8,7**.
- **La causa de la degradació de la Sony NO és treure el filtre solar.** MESURAT als dos trens als mateixos segons, sobre el limbe **solar filtrat**: a les 20:01 la Sony ja anava a 7,57 ″ i el Vixen a 4,08 ″; a les 20:23:50, 9,25 contra 5,62. C2 va ser a ~20:28:41. La pèrdua queda tancada dins el forat de 19:50:42 → 20:01:22, o sigui **27–38 minuts abans de C2, amb el filtre posat**. Cauen les 23–25 µm de desplaçament de focus com a explicació del *quan* (segueixen valent com a ordre de magnitud del *quant*) i cau el lligam amb el testimoni de `research/72`.

Això **reforça** el veredicte de coll d'ampolla: el difuminat propi de la Sony es veu amb filtre, sense corona ni cromosfera a la vora i amb el Vixen simultani com a testimoni del cel.

**El seeing i si en Pere tenia raó.** Sí, en tenia, però amb menys marge del que es va publicar. El que està MESURAT és un **sostre**: el vermell del Vixen desbiaixat val 4,76 ″ total; traient el fotosit (2,158 ″) i la difracció (1,46 ″) queda **≤3,98 ″ al vermell i ≤4,08 ″ al verd** per a seeing més òptica, a massa d'aire 6,4 — o sigui **≤1,3 ″ al zenit** (INFERIT amb l'exponent 0,6 de manual). L'estimació teòrica de 4,6–12,2 ″ s'equivocava per sobre de tot l'interval, però el límit inferior només és **1,1 vegades massa gros**, no 1,3, i el superior 3,0. **El valor central de 3,5 ″ i el terra de 2,8 ″ s'han de retirar**: el seu únic suport era la tendència amb el temps d'exposició, que amb sectors comuns s'esfuma (els fotogrames d'1/8 s perden més de la meitat dels sectors per saturació).

---

## 3. El soroll de Poisson a les protuberàncies

**Sí que hi és, i és exactament el que toca.** MESURAT: variància / (S/g + RN²) = 0,92–0,98 (R6) i 1,02–1,09 (Sony), d'1 a 12.000 ADU. La corba de transferència és una recta amb un sol pendent.

| | Guany (e⁻/ADU) | Soroll de lectura |
|---|---|---|
| R6 III, ISO 100 | **5,08 ± 0,10** (verd) | **2,72 ADU = 13,8 e⁻** si t < 1 s; **1,05 ADU = 5,3 e⁻** si t ≥ 1 s |
| A7RIIIA, ISO 100 | **3,41 ± 0,07** (els quatre canals) | **1,22 ADU = 4,15 e⁻** |

Validació creuada INFERIDA i independent: el mateix pic de protuberància vist pels dos trens dona 279 contra 238 e⁻/s/arcsec²/mm², un 17 % (0,22 EV).

**Què vol dir:** les protuberàncies **no estan limitades per fotons ni de lluny**. Al pic, a 1/125 s, el R6 hi recull 66.000 e⁻ per píxel cru → **S/N de Poisson 257:1**; a 1/2000 encara 68:1. A la banda espacial més fina, S/N = 34 al vermell. **El que les limita és la PSF**, i el pic satura a 1/60 i 1/30.

Tres avisos MESURATS:

- **El canal blau del R6 dona 4,33 ± 0,04 e⁻/ADU**, un 15 % per sota del verd, repetible a totes les parelles i sense explicació. **No el facis servir per a pesos ni fotometria.**
- **L'A7RIIIA filtra espacialment el RAW als 8 s**: autocorrelació del soroll +0,42 a lag 1 (contra +0,04 als 2 s) i 20–29 % menys variància de la que els fotons imposen. Cau **justament sobre les tres àncores d'earthshine**. El R6 no ho fa a cap exposició.
- Entre fotogrames separats 6 s, la diferència a les protuberàncies és **2,5–6,3 vegades** el soroll de fotons (visió anisoplanàtica): cal **registre subpíxel local**, no global rígid.

---

## 4. Els flats

**Veredicte: no calen, i fer-los ara seria pitjor que no fer-los.**

- **Vinyetatge Sony 300 GM a f/2,8**: **−0,214 EV a la cantonada de format complet**, MESURAT per Adobe i llegit del perfil `.lcp` del Mac. La corba de fàbrica dins de cada ARW (`VignettingCorrParams`) confirma la mateixa forma ∝ r². El meu ajust sobre el cel de la totalitat dona −1,23 a −1,30 EV, però és un **LÍMIT SUPERIOR contaminat per l'aurèola solar** (els dos termes són centrats i col·lineals: residus 1,45 % contra 1,45 %).
- **Vixen VSD90SS**: cercle d'imatge de 60 mm amb >90 % d'il·luminació a la vora; la cantonada de FF cau a r = 21,6 mm → **<0,15 EV** (INFERIT de la fitxa oficial). Límit superior mesurat −0,41 EV.
- **Sobre el camp que ocupa la corona** (fins a 3 R☉ cau a 0,357 i 0,394 del radi de cantonada): variació **1,8 % (Sony) i 1,6 % (R6)** amb les corbes documentades.
- **Pols**: MESURAT 0,10 % rms i ≤0,3 % de pic al R6 (i és del sensor: correlació +0,78 alineat al sensor, −0,63 alineat al Sol), ≤0,33 % a la Sony. Cap donut ni anell. A f/2,8 una mota queda escampada sobre 105 px crus.
- **PRNU ≲ 0,2 %**, la meitat de l'1 % que se suposava.

**Què s'ha de fer en comptes:** (a) a la Sony, aplicar el polinomi del `.lcp` **en domini lineal**, amb el pedestal ja restat i abans de qualsevol estirada: dividir per T(r) = 1 − 22,133597r² − 4187,240553r⁴ + 642257,67942r⁶ amb r = px × 4,51 µm / 300 mm. Efecte ~2 %. (b) Al R6, deixar-ho estar, o bé 1 − 0,15(r/rc)². (c) Fer servir **572A2906, 572A2907 i 572A2908** com a tres flats de fotosfera gratuïts. (d) **No fer servir mai 572A2905**: té 99.332 píxels a nivell blanc i dona un camp pla fals.

---

## 5. Què canvia del pla (`research/74`)

**G1 — es tanca, però reescrivint §4/R3.** No hi ha «dos defectes sense diagnosticar». Elimina la instrucció «descarta qualsevol fotograma amb σ per damunt de 3,5»: **descartaria els setze**. El master de 0,5 s es refà per **mitjana dels setze**. El de 10 s es refà per **mitjana dels vuit darks de 41 °C** (nivell 511,5667), no del grup de 43–44 °C. El pedestal escalar `511,0` es corregeix a **511,50**; sobre un fons d'earthshine de 20 ADU, l'error era del 2,5 %, i restant el master píxel a píxel baixa a 0,062 ADU.

**G2-bis — dues correccions numèriques.** (1) El sostre de linealitat del 85 % s'ha de calcular amb el pedestal **real**, no amb `[0, 31, 94, 63]` de libraw (que el mateix R3 declara fals): verd = 511,5 + 0,85·(16383 − 511,5) = **14.002 comptes**, no 13.940. (2) El guany ja no s'ha de derivar aquí: **g = 5,08 ± 0,10 (R6) i 3,41 ± 0,07 (Sony) e⁻/ADU**, MESURATS. **El pla blau del R6 queda exclòs de tot càlcul de pesos** fins que s'expliqui el seu 4,33.

**G2-bis / R5 — el flat-field deixa de ser una defensa.** La primera de les tres defenses contra el segrest del registre per pols era «el flat-field ja tret»; no hi haurà flat i **no cal**: el contrast de la pols és ≤0,3 % contra estructura coronal del 100 %. Manté les altres dues defenses i afegeix-hi l'avís: el risc torna a ser real si algun dia registres imatges gairebé sense estructura.

**G5 — el canvi més gros.** El terra de 5σ **no és 14 comptes per a tota l'escala**: el R6 té dos modes de lectura. Per a t < 1 s, σ = 2,72 ADU → terra 13,6; **per a 2 s i 10,3 s, σ = 1,05 ADU → terra 5,3 comptes**, o sigui que els fotogrames d'earthshine tenen **2,6 vegades més abast útil** del que el pla els donava. I els pesos trapezoïdals de Druckmüller es poden substituir pels òptims, ara que hi ha guany: **w = 1/(S_ADU/g + RN²)**, amb RN² = 7,40 ADU² (R6, t < 1 s), **1,10 ADU² (R6, t ≥ 1 s)** i 1,48 (Sony).

**G3 — les tres àncores d'earthshine de la Sony arrosseguen un filtre del cos.** Als 8 s el soroll és correlacionat (+0,42): **l'apilat hi guanya menys de √N**, la resolució ja s'ha perdut al fitxer i qualsevol estimació de soroll basada en g = 3,41 hi estarà malament (guany aparent 4,78). Amb la DSC06990 fora (R2), l'earthshine de la Sony queda a 16 s.

**D3 — hi ha nucli de deconvolució, i és per canal.** R6: **~4,8 / 5,8 / 6,7 ″** (vermell / verd / blau; el verd i el vermell MESURATS i desbiaixats, el blau INFERIT amb el mateix biaix). Sony: **~8,3 ″ i pràcticament acromàtic**. La lluminància del R6 ha de sortir del vermell i el verd. Afegeix registre de canals: **3,1 ″ (1,4 px) de desplaçament vermell–blau** i elongació del blau a PA 130–150 °, tots dos MESURATS.

**D2 — la Sony no entra a la capa de detall.** El forat és de factor 1,40 (no 1,51) i continua sent decisiu: on el Vixen passa contrast al 10 % (6,8 ″), la Sony ja és per sota. La Sony aporta rang dinàmic, corona externa i earthshine.

**G7a i selecció de fotogrames.** Les **parcials filtrades de la Sony a partir de les 20:01 van toves (7,6–9,3 ″)**: no serveixen com a referència de nitidesa; les d'abans de les 19:50 sí. I tria els fotogrames del R6 **pel FWHM mesurat un a un** (oscil·la entre 4,8 i 6,2 ″), no pel temps d'exposició: amb sectors comuns, 1/2000 i 1/8 no es distingeixen.