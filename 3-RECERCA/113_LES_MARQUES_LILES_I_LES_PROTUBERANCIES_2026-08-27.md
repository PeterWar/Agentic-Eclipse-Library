# 113 · Les marques liles de Pere, i les protuberàncies dels dos extrems

**Data:** 27 d'agost de 2026, matinada. **Encàrrec de Pere:** un PSB
(`MARQUESLILES.psb`) amb els artefactes que veu marcats en lila, i la llibertat
creativa de fer com Druckmüller amb les protuberàncies **d'ingress i d'egress
alhora**, fent servir `572A3016.CR3` per a l'egress.

---

## 1. On eren les marques

⚠️ No hi havia cap capa nova. Pere va pintar **damunt de les capes de filtre**,
que són grises per construcció (`R = G = B`), o sigui que n'hi va haver prou
buscant els píxels **no grisos**:

| capa | píxels no grisos | dels quals liles |
|---|---:|---:|
| 01 passa-alt | 231.986 | 227.764 |
| 02 radial | 49.993 | 49.048 |
| 04 MGN | 228.623 | 224.350 |
| **03 NRGF** | **0** | — |

**Set traços**, tots entre **1,56 i 2,43 R☉**, i un d'ells de 1074×62 px.

## 2. Què tracen: NO són anells ni costures

⛔ Les dues explicacions que teníem a mà queden descartades **amb mesura**:

- **anells** (H1, mediana azimutal per radi): després de la cura del 26-08 el
  pitjor val **0,017** sobre un llindar de 0,05. Un arc que ocupa 60° d'azimut
  **gairebé no mou la mediana**, o sigui que H1 hi és cec — però és que a més
  el que Pere marca **no és un anell sencer**;
- **costures** (H2, mediana per calaix de nivell): passa-alt **0,024**, radial
  0,013, MGN 0,030. Petites.

El que hi ha, mirant-ho de prop, és **estriat**: una corrugació fina i
bandes suaus de gran longitud d'ona.

## 3. La mesura de l'estriat: dues famílies

FFT direccional sobre finestres de 512 px a 2 R☉:

| finestra | direcció dominant | λ | contrast direccional |
|---|---:|---:|---:|
| nord | 90° | **4,1 px** | 14,7× |
| est | 0° | **4,1 px** | 24,9× |
| sud | 10° | **50,8 px** | 58,0× |
| oest | 80° | **51,1 px** | 14,5× |

⏭️ **Família A**: λ ≈ **4,1 px**, **alineada amb els eixos del llenç**.
⏭️ **Família B**: λ ≈ **51 px**, a 10° i 80°.

## 4. ⛔ Dues cures provades i TOTES DUES REFUSADES

### (a) La cura del cel per fotograma (`research/103`)

Portada a la cadena i mesurada **contra les marques de Pere**, amb control
aparellat (la zona marcada dilatada 25 px contra tota la resta):

| | zona marcada | control | quocient |
|---|---:|---:|---:|
| abans | 0,08456 | 0,08736 | 0,9679 |
| després | 0,08593 | 0,08777 | **0,9791** |

**L'estriat PUJA un 1,6 % a la zona marcada i el quocient empitjora un 1,2 %.**
A sobre treu **1,4–2,9 % rms** quan el `research/103` parlava de **0,10–0,50 %**
—i l'rms del vermell (1,468) supera el seu propi p99 (1,219), o sigui que hi
mana una cua de píxels extrems, no les bandes—, i el pitjor cas del tancament
HDR passa de **5,3 a 9,0 %**.

**Tres senyals en contra i cap a favor.** El codi queda a
`f2.cura_cel_fotograma` amb la mesura escrita al costat, **desactivat**.

### (b) El batec de remostreig

La família A és alineada amb els eixos i λ ≈ 4,1 px ≈ 2 píxels de subpla, o
sigui que semblava un batec entre la graella d'origen i la del llenç. Provat
canviant la interpolació d'un fotograma:

| interpolació | potència relativa a λ = 4,1 px |
|---|---:|
| LINEAR (la que fem servir) | **0,945** |
| CUBIC | 1,406 |
| LANCZOS4 | 1,772 |

⛔ **Refutada**: LINEAR és la que menys en té, i les altres l'**empitjoren**.

## 5. El que queda

**No s'aplica cap cura.** L'estriat està **mesurat i caracteritzat** (dues
famílies, amb longitud d'ona i direcció) i **no identificat**. Aplicar una
tercera cura sense jutge seria exactament el que la norma zero prohibeix.

⏭️ **El que sí que desbloqueja el diagnòstic és el TREN DE LA SONY**: dos
instruments independents mirant el mateix cel. Si l'estriat hi és als dos amb
la mateixa geometria **al cel**, és atmosfèric; si hi és amb la mateixa
geometria **al sensor**, és instrumental; si només hi és a un, és d'aquell
tren. És la feina de demà.

## 6. Les protuberàncies dels dos extrems

⏭️ **Llibertat creativa DECLARADA**, presa de Druckmüller: la imatge ensenya
alhora les protuberàncies de just **després de C2** i de just **abans de C3**.
No és un instant: és la **unió de dos instants**, i el negre que en queda és la
**intersecció dels dos discos lunars**, no un cercle.

| grup | fotogrames | t | exposició |
|---|---|---|---|
| ingress | 572A2963–2966 | 17,6–19,6 s | 1/3200 s |
| egress | 572A3014–3018 | 110,4–113,0 s | 1/3200 s |

`572A3016.CR3` (C3−7,5 s) és el que va triar Pere i és al mig del grup
d'egress. Cada fotograma hi entra **amb la seva pròpia màscara lunar**, i els
dos grups es combinen pel **màxim**: la Lluna es mou i cada fotograma en
destapa un tros diferent.

Les protuberàncies ja eren al compost —mesurades a **azimut 221,6° / r 1,055
R☉** (R/G p99 = **75,3**) i **44,7° / 1,027 R☉** (p99 = 7,5)—; el que faltava
era una capa que les fes visibles. Va al PSB com a **`09 PROTUBERÀNCIES`** en
mode **Aclarir**, amb la seva màscara pròpia.
