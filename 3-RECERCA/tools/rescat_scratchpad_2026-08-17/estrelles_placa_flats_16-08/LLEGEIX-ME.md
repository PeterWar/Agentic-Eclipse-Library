# Estrelles a la totalitat — eclipsi del 12 d'agost de 2026

**Carpeta de record i de mètode. 16 d'agost de 2026.**

Durant els 103,7 segons de totalitat, els dos telescopis van captar estrelles de
fons. Aquesta carpeta les documenta: on són, quines són, i com es van trobar.
**No és decoració**: d'aquestes estrelles en surt el calibratge fotomètric
absolut de tot el projecte i l'orientació real del cel a cada sensor.

---

## 1. Què hi ha aquí

| Fitxer | Què és |
|---|---|
| `estrelles_sony_marcades.png` | La imatge marcada de la Sony (3984 × 2660) |
| `estrelles_sony_zooms.png` | Retalls ampliats de les set més brillants |
| `estrelles_sony.csv` | Les 38 deteccions, amb posició, flux, S/N, FWHM i nom |
| `estrelles_vixen_marcades.png` | La imatge marcada del Vixen (6959 × 4639) |
| `estrelles_vixen_zooms.png` | Els seus retalls ampliats |
| `estrelles_r6.csv` | Les 24 deteccions del Vixen |
| `mascara_estrelles.py` | El generador. Funciona amb els dos trens |

**Com llegir les imatges:**

- 🟡 **cercle groc** — estrella identificada al catàleg (Hipparcos / Tycho-2),
  amb nom i magnitud visual.
- 🟢 **cercle verd** — font confirmada als set fotogrames però sense
  identificació al retall que s'ha fet servir.
- ⭕ **cercle de trossos** — hi és, però **no arriba a S/N 4 en aquell fotograma
  sol**: cal la pila sencera per veure-la.

---

## 2. Els fotogrames

| | Sony A7RIIIA + FE 300 mm f/2,8 GM | Vixen VSD90SS + Canon R6 Mark III |
|---|---|---|
| Fotograma de la imatge | `DSC06993` · 8 s · f/2,8 | `572A2983` · 10,3 s · f/5,5 |
| Piles emprades a la cerca | 2×8 s + 3×2 s + 3×1 s | 3×10,3 s + 3×2 s + 2×1 s |
| Escala de placa | 3,2020 ″/px | 2,1495 ″/px |
| Camp | 7,14° × 4,77° | 4,17° × 2,78° |
| Fonts trobades | **38**, totes 38 identificades | **24**, 22 identificades |
| Visibles en un sol fotograma | 17 de 38 | **22 de 24** |

⚠️ La `DSC06990` —la segona àncora de 8 s— està **moguda** perquè la muntura va
cedir durant l'exposició, i queda exclosa de tot.

---

## 3. Com es va fer

### 3.1 Cerca a cegues

**La cerca es va fer sense catàleg, a propòsit.** Si dius a algú quines
estrelles ha de trobar, troba les estrelles que li has dit. Un agent va fer la
predicció per efemèrides —skyfield amb DE440s, catàlegs Hipparcos i Tycho-2—
**sense obrir cap imatge**, i dos agents més van buscar fonts a cada tren
**sense veure la predicció**. El creuament es va fer després.

Passos, per als dos trens per igual:

1. **Lectura crua**, sense desbayerar i sense `postprocess`. Es treballa amb el
   pla verd i es resta el pedestal real —512 a la Sony, 511,5 al Vixen; el negre
   de metadata de libraw per a la R6 (`[0,31,94,63]`) **és fals**.
2. **Resta de la corona**: model de fons per mediana en blocs, suavitzat, i
   tornat a resolució completa. La corona és un gradient enorme i suau; una
   estrella és un pic petit.
3. **Detecció** sobre el residu normalitzat pel soroll local, amb filtre adaptat
   a la mida de la PSF.
4. **Filtratge de falsos positius**: una font real ha de sortir a **més d'un
   fotograma**, **a la mateixa posició del cel**, i **als canals R i B a més del
   verd** —cosa que un píxel calent no pot fer, perquè viu en un sol color de la
   graella de Bayer.

### 3.2 La prova que són estrelles i no defectes

L'argument que ho tanca és geomètric i no necessita cap catàleg:
**totes es mouen amb el cel i no amb el Sol**. Entre el primer i l'últim
fotograma la Lluna es desplaça 13,9 px respecte de les estrelles. Un reflex
intern o una estructura de corona aniria amb el Sol; un píxel calent no aniria
enlloc.

I la taxa de coincidència per atzar amb el catàleg, mesurada barrejant les
llistes, és de **0,02 coincidències** esperades. N'hi va haver 38 i 22.

### 3.3 El que en va sortir

| | Sony | Vixen |
|---|---|---|
| Residu de placa | 0,54 px (2,3 ″) | 0,32 px (0,9 ″) |
| **Punt zero fotomètric** | **+14,17 ± 0,08 mag** | **+14,21 ± 0,08 mag** |
| **Factor a B/B☉** (per ADU/s, píxel verd) | **1,134 × 10⁻¹¹** | **2,772 × 10⁻¹¹** |
| **Nord celeste** | **PA 90,27°** | **PA 57,19°** |
| Centre del Sol al sensor | (3894,7 , 2768,7) px | (3570,8 , 2267,1) px |

**Els dos trens coincideixen al 5 %** sobre la corona real. L'estat de l'art en
calibratge absolut d'imatges d'eclipsi amb càmera comercial és un factor 2.

I una validació que no es buscava: amb la solució de placa, **l'eix nord lunar
cau a 71,97°** al sensor de la Sony. El producte d'earthshine havia **ajustat
71,5°** contra el mapa d'albedo LROC **sense saber res d'estrelles**.
Coincideixen a **0,47°**.

---

## 4. Detalls que val la pena recordar

**Les estrelles van retrobar el salt de la muntura.** La llista de la Sony està
referida al segment posterior al salt. En fer-la encaixar sobre la `DSC06993`,
la translació que surt és **(−227,6 , +706,5) px** — que és el salt documentat a
`research/72` (+228, −710) amb el signe canviat. Ningú no l'hi va dir.

**Als zooms es veu la dispersió atmosfèrica a ull.** Cada retall és un tros de
mapa de senyal/soroll ampliat. Les estrelles hi surten **lleugerament allargades
en vertical**, i no és desenfocament: és la refracció diferencial, mesurada en
**3,08 ″ de separació entre el vermell i el blau a angle de posició 170°**, que
és pràcticament l'eix vertical. Amb el Sol a 9° d'altura la refracció total val
5,6 minuts d'arc.

**El que limitava no era el sensor ni l'exposició: era el cel.** La brillantor
de fons durant la totalitat va ser de **9,34 (Sony) i 9,15 (Vixen)
mag/arcsec²** a 8 radis solars — els dos trens coincideixen a 0,19 mag. Això és
entre 1,7 i 4,9 magnituds més brillant del que cap hipòtesi prèvia deia. Passar
de 8 s a més temps hauria rendit poc: el guany va com l'arrel del temps.

**La més feble identificada és de magnitud 9,18**, i la van veure tots dos
trens: és la mateixa estrella.

**El que NO es pot fer amb aquestes estrelles**: mesurar les ales de la PSF més
enllà de 13 px (Sony) i 30 px (Vixen). La corona interior és unes **200.000
vegades** més brillant que l'estrella més brillant del camp, i el seu propi
halo enterra qualsevol halo estel·lar — a 87,5 px, 2.800 vegades per damunt.
És un límit físic, no de mètode.

---

## 5. Refer les imatges

```bash
~/.venvs/eines-ia-py312/bin/python mascara_estrelles.py sony
~/.venvs/eines-ia-py312/bin/python mascara_estrelles.py vixen
```

Amb un altre fotograma:

```bash
~/.venvs/eines-ia-py312/bin/python mascara_estrelles.py sony DSC06987.ARW
~/.venvs/eines-ia-py312/bin/python mascara_estrelles.py vixen 572A2984.CR3
```

L'script és **només lectura** sobre els RAW originals i deixa la sortida al seu
propi directori. Si li dones un fotograma d'un altre segment d'apuntat, busca
sol la translació que hi encaixa.

---

## 6. On és la resta

- `research/75` — l'informe de mesures sencer: foscos, resolució, guany i
  calibratge absolut, amb la fase adversarial i les seves correccions.
- `research/73` — la referència de mètodes de postprocessat.
- `research/74` — el pla d'obra, gate per gate.
