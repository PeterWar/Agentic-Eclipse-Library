# 77 — Provar la relativitat general el 2027: què caldria de veritat

**16 d'agost de 2026 · pla amb fase adversarial**

Per a les posicions del 12 d'agost de 2026, el senyal GR **predit** és de
0,25–0,38 píxels. El pipeline calcula **σ(ε) = 0,53 com a previsió de Fisher**
a partir del soroll i de la geometria —equivalent a 1,9σ sota el model—, però
no ajusta ni mesura ε a les imatges. Per tant no hi ha cap detecció ni cap
discriminació Einstein–Newton. Aquest document diu què caldria per fer-ho de
debò el **2 d'agost de 2027**, amb números i amb el que la revisió adversària
ha tombat.

Marcatge: **MESURAT** (sobre les nostres dades o de font primària) · **INFERIT**
· **NO VERIFICAT**.

⚠️ **Tres revisions adversàries independents —física, viabilitat i
sobreafirmació— van refusar la primera versió del pla, totes tres amb severitat
«major».** El que queda escrit aquí ja incorpora les seves correccions. Les
xifres que van caure són a §8, i s'hi queden a propòsit: són el registre del
que no s'ha de tornar a prometre.

---

## 1. El veredicte, primer

| Objectiu | σ(ε) que exigeix | 2027, veredicte honest |
|---|---:|---|
| Detectar la deflexió a **3σ** | ≤ 0,333 | **pràcticament garantit** només per geografia |
| **Einstein contra Newton a 5σ** | ≤ 0,100 | **molt probable** |
| El **±10 %** d'Eddington | 0,100 | **a l'abast** |
| El **±5 %** | 0,050 | possible amb feina seriosa |
| El **±3 %** de Bruns 2017 | 0,030 | **estirada de debò**, condicionada a mesures que encara no tenim |
| Per sota del 3 % | < 0,030 | **no és defensable ex ante** |

**La banda realista és 5-10 %.** Qualsevol xifra per sota del 3 % promesa abans
d'haver mesurat el nostre propi terra sistemàtic és propaganda. Els equips
professionals van necessitar cinquanta anys per baixar del 10 %, i el millor
resultat òptic de la història —Bruns 2017— és un 3,4 % amb dos anys de
preparació, un pilar de formigó i un lloc triat després d'una campanya de
mesura de turbulència.

⛔ **I una cosa que cal dir en veu alta: això no comprova la relativitat.**
La deflexió està confirmada a 1,2×10⁻⁴ per VLBI geodèsic (γ = 0,99992 ±
0,00012, Lambert & Le Poncin-Lafitte 2011) i a 2,3×10⁻⁵ pel retard de Shapiro
de la Cassini. Un 5 % nostre és **tres mil vegades pitjor** que l'estat de
l'art. El valor de fer-ho és esportiu, pedagògic i de mètode, no científic. Que
això quedi escrit evita que el projecte es vengui el que no és.

---

## 2. Per què el 2026 no va donar: tot penja d'una sola xifra

**El Sol era a 9,2° d'altura, 6,1 masses d'aire.** Pràcticament tots els termes
de l'error en surten directament. **MESURAT** i comparat amb els llocs del 2027:

| | León 2026 | Cadis 2027 | Luxor 2027 |
|---|---:|---:|---:|
| Altura del Sol | 9,2° | 37,5° | **81,8°** |
| Massa d'aire | 6,23 | 1,64 | **1,01** |
| Refracció total | 5,81′ | 1,30′ | **0,14′** |
| Compressió del camp | 0,973 %/° | 0,078 %/° | **0,030 %/°** |
| Dispersió vermell-blau | 3,08″ | 0,65″ | **0,07″** |
| Seeing esperat (X⁰·⁶) | 5,80″ | 2,61″ | **1,95″** |
| Durada de la totalitat | 103,7 s | 178 s | **385 s** |

Luxor divideix la refracció per **41**, la compressió del camp per **33**, la
dispersió per **43** i el seeing per **3**. Els tres primers són exactament els
sistemàtics que ens van matar. **Anar on el Sol és alt no és una millora entre
d'altres: és la millora.** No costa ni un euro d'òptica.

### 2.1 Rectificació d'una cosa que vaig dir malament

⚠️ Vaig escriure que «tot el forat entre els 0,02″ del límit de fotons i els
0,90″ assolits és sistemàtic». **Això només val per a l'estrella més
brillant.** Per a la majoria feble el límit de fotons del cel ja era de
**0,23-0,69″** —V=8,0 → 0,233″; V=8,5 → 0,369″; V=9,18 → 0,691″— i pesa
**~35 % de la variància** aconseguida. La conclusió no canvia, però el mecanisme
sí: una bona part del nostre error el va posar **el cel brillant**, que també
és filla dels 9° d'altura.

La llei que mana, en règim limitat pel fons: **σ = 0,601 · FWHM / (S/N)**, o
sigui **σ ∝ FWHM² · √(cel) / flux**. El FWHM hi entra al quadrat.

### 2.2 Els quatre errors nostres, per ordre de cost

1. **Cap camp de comparació.** No en vam prendre mai. És l'única manera de
   restar la distorsió òptica pròpia, i és el que Eddington sí que tenia.
2. **Seguiment solar en lloc de sideri.** El Sol es mou 0,041″/s respecte de
   les estrelles: seguir a taxa solar les arrossega **15,2″ en 371 s**. Per a
   la corona el solar és correcte; per a l'astrometria és el pitjor.
   ⚠️ Són dos objectius amb taxes incompatibles, i cal decidir-ho per tren.
3. **Alineació polar de 2°** feta de dia → deriva de 610 mas/s i traç de 3 px
   dins de cada pose de 10,3 s. L'especificació per a aquesta feina és
   **< 35 mas/s** amb poses de 10 s: un factor **17**.
4. **La mà a la lent** en treure el filtre: dos salts de 12′ i 39′ i 0,138° de
   rotació de camp, el moviment més gros de tot el conjunt de dades.

---

## 3. El camp del 2027: bo, però no per la raó que sembla

**MESURAT** (Skyfield + DE440s i Tycho-2). Sol el 2027-08-02 a
**RA 8h 47m 53s, Dec +17,86°**, latitud galàctica **+33,5°** (el 2026: +41,4°).

| | 2027 | 2026 (volat) | 1919 Híades | 2017 (Bruns) |
|---|---:|---:|---:|---:|
| V<7, entre 2 i 15 R☉ | **29** | 18 | 24 | 10 |
| V<9 | **177** | 101 | 128 | 84 |
| V<11 | **944** | 636 | 627 | 564 |

I tres peces que no es repeteixen:

- **M44, el Pessebre**, centrat a **9,63 R☉** (PA 314°): un cúlmul obert sencer
  dins l'anell de deflexió.
- **Venus a 10,81 R☉** (PA 307°), **V = −3,91**, a 28,5′ de M44. Conjunció
  superior nou dies després.
- **δ Cancri**, V = 3,94, a **3,10 R☉**: una estrella brillant ben endins.
- I tres properes: **1,80 R☉** (V=7,22), **1,88** (V=7,87), **1,93** (V=8,26).
- ✅ **Les tres joies cauen al mateix quadrant, PA 291-314°**: una sola rotació
  de càmera les agafa totes.

⚠️ **Compte amb Venus**: no és una referència fixa gratuïta. La seva pròpia
deflexió és de **0,067″** contra els 0,162″ d'una estrella al mateix paràmetre
d'impacte (factor D_ls/D_s = 0,415, **MESURAT** amb DE440s). La diferència és
calculable, o sigui que Venus serveix — però com a objecte amb deflexió pròpia
coneguda, no com a clau fixa.

### 3.1 ⛔ La fondària no compra gairebé res, i això capgira el disseny

En règim limitat pel fons el senyal/soroll cau ×6,31 per magnitud mentre els
comptatges només pugen ×2,1. Conseqüència **calculada**:

- **el 97,2 % del pes estadístic és a les 177 estrelles més brillants que
  V = 9**;
- les 3.085 estrelles més febles que V = 11 hi aporten el **0,25 %**;
- el N efectiu de tot l'anell és **~1.100**, no 3.000.

⛔ **Per tant: la riquesa del camp del 2027 no és el que compra la precisió, i
un sensor més sensible tampoc.** Ho compren les trenta estrelles brillants, el
FWHM i el control dels sistemàtics. Qualsevol argument per comprar equip que es
basi en «arribarem més fondo» és fals.

---

## 4. El precedent que mana: Don Bruns, 2017

El millor resultat òptic de la història d'aquest experiment, i el va fer un
aficionat. **L = 1,7512″ ± 3 %** (Class. Quantum Grav. 35, 075009;
arXiv:1802.00343 diu 3,4 %).

| | |
|---|---|
| Telescopi | Tele Vue NP101is Petzval, **emmascarat de 101 a 87 mm**, 543 mm, f/6,2 |
| Càmera | FLI ML8051, CCD **monocrom** KAI-08051, refredat a −20 °C, 16 bits |
| Escala | **2,087″/px**, camp 1,9° × 1,4° |
| Filtre | Astrodon **Sloan r′**, encolat davant del sensor |
| Muntura | Paramount MyT sobre base de formigó, polar a **4′** |
| Lloc | Casper Mountain, Wyoming, **2.390 m**, Sol a **54,4°** |
| Dades | 45 fotogrames, **22 s integrats**, 20 estrelles d'1,51 a 4,82 R☉ |
| Residu per estrella | **0,065-0,086″** |
| Pressupost d'error | estrelles **3,1 %** ⊕ escala **1,23 %** = 3,4 % |

**El truc decisiu, i és el que hem de copiar:** va treure l'escala de placa de
**dos camps de calibratge a ±7,4° del Sol, fotografiats DINS la totalitat**.
Això trenca la degeneració entre escala i deflexió. **Reduïdes les seves
pròpies dades pel mètode clàssic d'un sol camp, surt L = 1,86″ ± 4 %** — un 6 %
fora de la veritat. El truc val, mesurat al nostre model, un factor **1,55**.

Altres coses seves que valen diners zero: **autoexposició per script** (ell diu
que és una de les dues coses que van fer que sortís), emmascarar l'obertura per
millorar el camp, i el filtre **encolat** perquè res no es mogui.

⚠️ **I el que no s'ha d'oblidar en comparar-s'hi**: el seu terme dominant, el
3,1 %, venia d'un residu per estrella de 0,065″ que **també era sistemàtic**,
no de fotons. Ell mateix diu que coincidir amb la relativitat al 0,05 % va ser
sort. La seva barra d'error mai no s'ha validat externament.

### 4.1 Els cinquanta anys d'encallada, i per què

**MESURAT de font primària.** El terme d'escala i el de deflexió són tots dos
radials i quasi degenerats: **un error fraccional d'escala de només 1×10⁻⁵
entre l'eclipsi i la comparació falsifica 0,2-0,3″ de «deflexió»**, o sigui el
15-20 % de l'efecte sencer. Freundlich & Ledermann (1944) ho van quantificar:
per arribar a σ(L) ≤ 0,1″ cal conèixer la focal entre les dues èpoques a
**δf/f < 4×10⁻⁶ a 1×10⁻⁵**, és a dir **0,016 a 0,084 mm**.

- **Potsdam 1929**: girar la càmera cap al camp d'escala li va canviar la focal
  1 part de 26.000 (0,13 mm), i el resultat sobre les **mateixes 30 estrelles**
  va passar de **0,11″ a 2,45″**.
- **Mikhailov 1936**: 45 °C de diferència entre l'eclipsi i la comparació.
- **Lick 1922**: 1,72 ± 0,11″ amb 92 estrelles — el millor clàssic.
- **Texas-Mauritània 1973**: 1,66 ± 0,18″ (11 %) amb 39 estrelles a 0,21″
  cadascuna, instrumentació moderna i un refractor de 2,1 m.

⛔ **El número que més importa de tota aquesta història**: el 1973 van fer un
**control nit-contra-nit**, on la resposta certa és zero, i els va sortir
**L = 0,15 ± 0,09″ i −0,07 ± 0,10″**. Això és un **terra sistemàtic mesurat del
6,3 %**. És l'únic terra que algú ha mesurat mai en aquest experiment, i és
quatre vegades el que qualsevol disseny nostre s'atrevia a assumir.

### 4.2 El parany tèrmic, en números nostres

Un tub d'alumini canvia l'escala **22-26 ppm/K**. Radialment, a 2° del centre:

| ΔT | desplaçament a 2° | Δε |
|---:|---:|---:|
| 0,5 K | 0,086″ | 0,04 |
| 1 K | 0,173″ | **0,08** |
| 5 K | 0,864″ | 0,39 |
| 10 K | 1,73″ | **0,78** |

Entre un calibratge nocturn i l'eclipsi hi pot haver 20 K: **dos cops la
deflexió sencera**. ⛔ **El calibratge nocturn serveix per a la FORMA de la
distorsió, no per a l'ESCALA.** Són dues coses i es mesuren en dos moments
diferents. Aquesta és tota la lliçó de Potsdam.

I la fuita de distorsió cap a ε, **calculada**: **Δε ≈ 0,45 × A**, amb A el
residu radial a la vora del camp. 1″ sense corregir → 45 %. 0,10″ amb model de
3r ordre → 4,5 %. 0,02″ amb calibratge dedicat (Bruns) → 0,9 %.

---

## 5. El pla, en dues branques

⛔ **La revisió de viabilitat va destapar que tots els dissenys assumien en
silenci un lloc fix, reconegut i ocupat durant dies.** Això xoca frontalment
amb la doctrina d'aquest projecte —`CLAUDE.md` §3: *«Pere pot no saber on
observarà fins una hora abans»*, i la porta de 7.044 casos existeix per això—.
No es pot tenir tot: cal triar i pagar-ho.

### Branca A — lloc fix (Egipte), per anar a buscar el 3-5 %

- Compromís de lloc **7 dies abans**, sense opció de moure's.
- Alineació polar **sobre estrelles** la nit abans, des del mateix punt.
- Sèrie nocturna de distorsió **al mateix alt/az** de l'eclipsi.
- Camps de calibratge dins la totalitat.
- **Preu**: si hi ha cirrus damunt d'aquell punt, es perd tot.

⛔ **I un impossible geomètric que cal saber**: el camp de l'eclipsi (Dec
+17,86°) **no puja mai per sobre de 65,6° des de Lleó, 66,5° des de Barcelona
ni 71,4° des de Cadis**. Igualar els 81,8° de Luxor exigeix latitud **9,6-26,1°
N**. O sigui que **la sèrie nocturna de distorsió a alt/az igualat no es pot fer
des d'Espanya**: o es fa dins d'aquella franja de latitud, o s'abandona el
requisit i s'assumeix el que costa.

### Branca B — mòbil, que és com aquest projecte treballa de veritat

- Lloc triat el mateix dia, alineació de dia, sense escapades a camps de
  calibratge.
- Escala ajustada **dins del mateix fotograma**, amb model de placa cúbic.
- **Previsió honesta: 4,5-7 %.** Continua sent el segon millor resultat òptic
  de la història i continua donant **> 10σ** a Einstein contra Newton.

**Recomanació: branca B, i que la branca A es guanyi el dret amb l'assaig de
febrer.**

### 5.1 Les accions per ordre de valor per euro

1. **Anar on el Sol és alt.** Gratis. Val un factor 3-6 tot sol.
2. **Seguiment sideri al tren d'astrometria** (el solar li arrossega 15″).
3. **Alineació polar sobre estrelles la nit abans**: de 2° a 5′ són 24×.
4. **No tocar l'òptica**: mecanisme de retirada del filtre que no carregui el
   tub. El 2026 això va ser el moviment més gran de tot el conjunt.
5. **Gaia DR3 en lloc de Tycho-2** (0,35 mas contra 91 mas propagats). Gratis.
6. **Reduir en alt-az refractat**, no en equatorial.
7. **Filtre vermell o Sloan r′**: mata la dispersió atmosfèrica i allarga la
   pose, que promitja turbulència.
8. **Autoexposició per script** — ja tenim la màquina per fer-ho.
9. **L'assaig general de febrer de 2027** (§6). És l'única acció que **mesura**
   el nostre terra en lloc d'assumir-lo, i decideix tota la resta.
10. **Només després**, plantejar-se una càmera monocroma.

⛔ **No compris el sensor monocrom abans de l'assaig de febrer.** Els termes que
millora no són els que manen (§3.1), i la decisió depèn d'un número que encara
no tenim.

---

## 6. L'assaig general de febrer de 2027 — el pas que ho decideix tot

**MESURAT amb Skyfield**: el camp de l'eclipsi del 2027 és observable de nit,
amb cel astronòmicament fosc, entre el **17 de novembre de 2026 i el 12 d'abril
de 2027**, i passa per l'altura de l'eclipsi:

| Lloc | altura durant l'eclipsi | quan hi passa de nit | moment central |
|---|---:|---|---|
| Luxor | 81,8° (culminació) | 17 nov 2026 – 12 abr 2027 | **30 gen 2027, 21:42 UTC** |
| Màlaga | 39,3°, azimut 97° | 15 nov 2026 – 16 mai 2027 | **15 feb 2027, 02:54 UTC** |

**Què s'hi ha de fer**: fotografiar el camp dues nits diferents amb el muntatge
sencer i passar-lo per la mateixa canonada de reducció, amb el Sol absent. La
resposta certa és **ε = 0**. El que en surti és **el nostre terra sistemàtic
mesurat**, exactament com va fer Jones el 1973.

Fins que aquest número no existeixi, el pla ha de citar el **6,3 % de Jones**
com a terra i dir «≤ 10 %, a revisar quan l'assaig mesuri el nostre». Això és
el que separa un pla honest d'un fullet.

---

## 7. Els deures d'enginyeria que ningú havia pressupostat

- ⛔ **No hi ha cap codi de control de muntura a tot el projecte.** Escombrada
  de 2.500 fitxers Python a `gui/` i `controller/`: zero coincidències d'ASCOM,
  INDI, Alpaca, LX200, SynScan, Celestron, iEQ o CEM. L'única «slew» que hi ha
  és la del rellotge NTP. **Eclipse Command no sap apuntar.** I la plataforma és
  macOS, on l'ecosistema estàndard (N.I.N.A., SharpCap, ASCOM) no corre. Els
  camps de calibratge de Bruns exigeixen escapades guionitzades: **és un segon
  projecte**, i o s'adopta INDI/Ekos o s'esborren les escapades del pla.
- ⚠️ **El repartiment del temps de totalitat no està resolt.** Els tres
  objectius innegociables de `CLAUDE.md` §1 bis —earthshine, perles i anells
  travessant C2 i C3, i el bràqueting de corona— continuen manant. Si els dos
  trens fan astrometria, s'han de cancel·lar; si no, cal ensenyar la línia de
  temps entrellaçada dels 383 s. Ningú no l'ha ensenyada.
- ⚠️ **El gradient de la corona esbiaixa el centroide.** Amb resta de fons
  convencional el biaix arriba a **−10″ a 2 R☉**, sis vegades el senyal sencer.
  Cal fons local quadràtic i mesurar el biaix per injecció.

---

## 8. El que la revisió adversària va tombar, i s'hi queda escrit

| Afirmació caiguda | Per què |
|---|---|
| σ(ε) = 0,017-0,022, «millor que el rècord de Bruns» | tres defectes acumulats; corregits, 0,026 aleatori i ~0,068 amb el terra mesurat |
| FWHM de 2,8″ i 3,5″ als pressupostos | **`research/75` §2.1 ja els havia retirat pel seu nom**. El que està mesurat és només un sostre: seeing+òptica ≤ 3,98″ a X=6,08, amb el repartiment desconegut. Banda vàlida a Luxor: **2,5-4,2″** |
| «3.000 estrelles a 0,09″» | N efectiu ~1.100 a l'anell sencer i ~700 al camp recomanat; el 97 % del pes és per damunt de V=9 |
| Terra correlacionat de l'1-1,5 % | ningú no l'ha demostrat mai; l'únic mesurat és el **6,3 %** de Jones 1976 |
| Sèrie nocturna de distorsió «a casa a alt/az igualat» | **geomètricament impossible des d'Espanya** (§5) |
| Seeing de Luxor millor que el de Lleó, segur | Lleó era a les 20:28 locals (capa límit assentada); Luxor és a **migdia solar sobre desert a 42 °C**, el pitjor règim convectiu del dia. L'extrapolació X⁰·⁶ és optimista, no conservadora |
| Importar l'escala de Bruns és pitjor que ajustar-la al fotograma | error de **forma**, no de magnitud (revisió de física) |

---

## 9. Calendari

| Quan | Què | Per què |
|---|---|---|
| **set-oct 2026** | decidir branca A o B; si A, triar zona i mirar permisos | tot el pla en penja |
| **nov 2026** | muntar la canonada de reducció (alt-az refractat, Gaia DR3, fons quadràtic, ajust cec) | ha d'estar feta **abans** de l'assaig |
| **des 2026** | primera nit de distorsió amb el muntatge sencer | veure la forma del residu |
| **30 gen / 15 feb 2027** | **ASSAIG GENERAL: dues nits, ε = 0** | mesura el nostre terra; decideix la resta |
| **feb-mar 2027** | si i només si l'assaig ho justifica, comprar sensor monocrom | §3.1 diu que probablement no cal |
| **abr-jun 2027** | mecanisme de filtre sense tocar el tub; alineació polar de 5′ assajada | els dos errors nostres més cars |
| **jul 2027** | assaig complet a la durada real, amb els tres objectius de §1 bis a la mateixa línia de temps | l'únic que encara ningú no ha ensenyat |
| **2 ago 2027** | eclipsi | |

---

## 10. La frase que cal conservar

**Anar on el Sol és alt val més que tot l'equip que es pugui comprar.** De
9,2° a 81,8° divideix per 41 la refracció, per 33 la compressió del camp i per
43 la dispersió atmosfèrica, multiplica per 3,7 el temps de totalitat i no
costa res. Tota la resta —el sensor, el filtre, els camps de calibratge— és
segon ordre comparat amb això i amb l'única cosa que realment falta: **mesurar
el nostre propi terra sistemàtic abans de creure's cap número.**

---

*Fonts primàries: Bruns 2018 CQG 35, 075009 (arXiv:1802.00343); Dyson,
Eddington & Davidson 1920; Campbell & Trumpler 1923/1928; Freundlich &
Ledermann 1944 MNRAS 104, 40; Mikhailov 1959 MNRAS 119, 593; Jones 1976 AJ 81,
455; Texas Mauritanian Eclipse Team 1976 AJ 81, 452; Lambert & Le
Poncin-Lafitte 2011 A&A 529, A70; Dittrich et al. 2025 BAAS 56(4) 040.
Efemèrides i circumstàncies recalculades amb Skyfield 1.55 i DE440s; comptatges
estel·lars de Tycho-2. Dades del 2026: `research/71`, `72` i `75`.*

---

## Addendum del 18-09-2026 — el 2026 no mesura res, i dues lliçons noves per al 2027

Vegeu `166_DEFLEXIO_GRAVITATORIA_2026_ABANDONADA_I_LLICONS_PER_AL_2027_20260918.md`. Resum: (1) es van trobar camps de calibratge de la mateixa nit per als dos trens i se'n va calibrar la distorsió amb Gaia DR3 (VSD90SS 12,7″ màx; 300 mm 137″ màx); l'escala nocturna del Vixen difereix un 0,19 % de la de l'eclipsi: **l'escala només es pot tenir amb camps dins de la totalitat**; (2) amb la distorsió fixada, les estrelles a 2–3 R☉ surten desplaçades **cap endins** 1–1,5″ pel gradient de la corona: **el biaix del centroide per la corona s'ha de modelar i validar amb injeccions** abans de cap ajust. Decisió de Pere: idea retirada de la imatge (v10) i del whitepaper (v0.12); es reprèn en preparar el 2027.
