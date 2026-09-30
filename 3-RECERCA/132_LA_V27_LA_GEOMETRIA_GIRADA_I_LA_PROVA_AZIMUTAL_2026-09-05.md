# 132 · La V27: la geometria de la V25/V26 estava girada 138,5°, la prova azimutal que ho veu, i els arcs que un filtre azimutal no pot fer

**5 de setembre de 2026 (matinada).** Ordre de Pere sobre la V26 (`V26_artefactes.psb`, amb
les seves marques): (1) «les capes que he deixat invisibles segueixen girades uns 90 graus
en sentit contrari a les agulles del rellotge respecte a les visibles, que són les de la
geometria que vull»; (2) noms de projecte i de capes més curts; (3) artefactes marcats a
color a cada filtre, «encara tenim el reflex circular recurrent»; (4) una V27.

Lliurable: `Projecte photoshop/1-Unint Capes/Capes Totals/V27.psb` (rebut `V27_REBUT.md`
al costat), vistes a `IA/output/v27_20260905/`, eines `research/tools/v25_lineal/etapa2d_*.py`
(geometria), `etapa1b_*.py` (detall gran azimutal), `etapa4_munta_v27.py`. La V24, la V25, la
V26 i el seu `V26_artefactes.psb` no s'han tocat.

## 1. Pere tenia raó dues vegades: la base anava girada 138,5°

Al `research/131` §1 vaig escriure que l'alineació era «0,0 px, mesurada de tres maneres».
Les tres eren cegues a una rotació:

| «prova» de la V25/V26 | per què no veia el gir |
|---|---|
| 48 finestres de correlació de fase (band-pass 4-40 px), residu 1,5 px | el gradient radial domina la fase: mesurat el 05-09, dona «0,1 px de residu» amb la imatge girada **93°** |
| escaquer de 128 px base ↔ capes 10/09/13 | els raigs són radials a qualsevol angle i «continuen» tessel·la a tessel·la |
| forat lunar de la cadena a 4 px del disc C2 | el forat és concèntric: no diu res de l'angle |

La prova que ho destapa és la **correlació circular en azimut** del perfil polar en ln
(r 1,15-2,0 R☉ × θ, mitjana per anell restada) entre la meva base i les capes 10/09 de
Pere: pic a **−138,5°**, tant amb els renders del Photoshop de veritat (JSX: una capa
visible, aplanar, PNG) com amb psd-tools. Pere deia «uns 90° antihoraris»: el sentit era el
bo; l'angle, a ull.

**Geometria V27** (`etapa2d_geometria_azimutal.py`): angle gros = pic azimutal (+46,58° de
retard → **−46,6° en la convenció d'OpenCV**; la V25/V26 duien −91,97°); centre afinat en
polar (retard radial per sector ajustat a dx·cosθ + dy·sinθ: 0,1 px de correcció); escala
**declarada 1,0** (mateixa escala de píxel; el retard radial per bandes de radi es deixa
enganyar pels anells HDR comuns i donava 0,992). Validació: residu azimutal **+0,24° /
−0,02° / −0,50°** contra les capes 10, 09 i 13; control nul (referència girada 180°) a
0,01 a les finestres; i, independent de qualsevol correlació, **el forat lunar de la cadena
(cercle de 451,5 px, centre a 2 px del Sol) cau a (+0,2, −2,5) px del disc C2 de Pere** amb
la geometria nova (R 453,45 vs 451,5: 0,4 %).

⛔ Regla nova (`normes_i_portes.md`, skill `corregeix-artefactes` família **A**): tota
geometria entre llenços porta la prova azimutal (0 ± 0,5°) i un control nul; les finestres
de fase només valen sobre imatges sense perfil radial i amb el control nul; i les vistes es
miren també en polar (r × azimut), on un gir és un desplaçament horitzontal evident.

## 2. Les marques de Pere sobre els filtres de la V26

`V26_artefactes.psb` (25 capes; ell va deixar visibles les 0-13 i invisibles les 14-24; els
filtres els va posar en Normal al 100 % per pintar-hi). Marques (saturació > 0,08):

| capa | marques | què són | cura a la V27 |
|---|---|---|---|
| `03 DETALL ACHF 32-256` | arcs concèntrics verds a 1,3-2,5 R☉ (E i W) | anells: graons HDR de la Vixen i costura de fusió a radis fixos, amplificats pel passa-alt de 128-256 px i per la normalització per anell | el detall gran passa a ser un **passa-alt NOMÉS en azimut** (polar ln r × θ; bandes < 64 px i 64-256 px d'arc): una variació al llarg del raig no hi pot existir per construcció (prova sintètica: anells 0,21 → 0,004 rms; streamer 0,50 → 0,37) |
| `03` | punts rosa al streamer S (2,4 R☉) i al streamer E | la saturació de la tanh als raigs més brillants (línia blanca) | el mateix filtre azimutal amb 3,5·MAD i terra a 3,5 R☉ |
| `03`, `01`, `02` | cercle vermell a 3,0 R☉ SW | **el ghost de la Sony**: a la V26 era una «moneda» plana (mediana anular, r 45) amb halo | esborrat **a l'origen per inpainting** (Telea, radi 32 = el nucli de 25 px mesurat) a la base amb cel i a la corona sola, ABANS de la corba i de tots els filtres (etapes 1 i 1b); cap pedaç posterior |

## 3. Noms curts

Projecte `V27.psb`; capes de Pere amb el nom curt (la taula completa al rebut: «12 1/3200
perles», «11 1/500 limbe», «10 1/125», «09 1/60 x2», «08 1/30 x4 quar» … «13 Sony >1s»,
«Fons per raig», «Earthshine v2», «Compara D87», «Compara LROC», «Estrelles», «Earthshine
V24e», «Reflex»); les meves: «00 Base», «00b Base sense cel», «03 ACHF gran azimutal»,
«01 ACHF fi 2-32», «02 Passa-alt 24». Els píxels i les màscares de les seves capes no es
toquen (fidelitat comprovada); la descripció llarga viu al rebut.

## 4. Dues rondes de la V27

**Ronda 1** (geometria nova, noms curts, detall gran azimutal, ghost per inpainting r 32):
totes les portes PASSA, prova azimutal 0,00°, i sobre els renders del Photoshop de veritat
−0,5° (base) i −0,25° (fusionada). Però la vista tal com es lliura ensenyava (a) un **rombe**:
la cobertura del llenç comú girada −46,6° cau sencera dins del llenç V23 (0,75 del llenç) i
la igualació de les capes de Pere, ajustada a 6-8,5 R☉ i extrapolada constant, deixava un
graó a la vora (8-12 R☉); (b) **un anellet al ghost**: la ploma del pedaç (radi 32, ploma 10)
queia DINS de la vora del nucli (25 px) i en deixava un 3 %, i a la corona sola el compost
porta un bol de −1,5 % fins a ~105 px que el detall gran ensenyava com una taca fosca.

**Ronda 2**: finestra d'igualació 6-11 R☉ i ploma 250 px; ghost: radi 40 (ploma per fora
del nucli) i **bol dividit per la seva corba radial** (`corregeix_bol`: es conserva la
textura; prova sintètica: residu < 0,3 %) a la corona sola abans de tots els filtres.
**Ronda 3**: la ronda 2 encara ensenyava el pedaç com una **moneda llisa** de 80 px dins
d'un camp amb textura (i un anellet): la cura és la del tampó de clonar de Pere,
`clona_textura` — al disc inpaintat s'hi afegeix la textura d'alta freqüència (B − G(B; 8 px))
d'un veí al MATEIX radi (120 px en direcció tangencial), amb ploma, a la base i a la corona
sola. Declarat al rebut.

**Ronda 4**: la ronda 3 encara deixava un anellet: la ploma del pedaç (radi 40: de 30 a
50 px) queia just on la corona sola té el bol més fondo (−4,5 % a 32-60 px al canal G) i
els filtres hi dibuixaven −0,015 (fi) i −0,03 (gran); la base i el total ja eren nets.
Radi 50 (ploma sencera dins de la zona corregida pel bol, que comença a 40 px) i veí de
clonatge a 140 px. Lliçó: **la ploma d'un pedaç ha de quedar sencera dins de la zona
corregida**, i el que queda del ghost es mesura CAPA PER CAPA (perfil radial de la base,
del total, de la corona sola i de cada capa de detall), no només a la vista.
**Ronda 5**: la ronda 4 deixava un puntet de ~8 px al centre del disc (la costura del
Telea al centre de l'ompliment, +0,018 a la capa gran): l'ompliment es fon amb σ 3 px abans
de la ploma.

**Ronda 6 (la lliurada)**: a la ronda 4 hi havia un altre «punt» a 2,64 R☉ (az 147°): la capa
gran hi era SATURADA (0,99) en un disc de ~100 px — una **estrella**: el passa-alt azimutal
de 16-64 px converteix cada punt en un disc brillant. Abans del detall gran, les estrelles
de la corona sola s'inpainten amb radi 12; les capes fines i la capa `Estrelles` de Pere les
conserven. ⛔ Amb un llindar de 6 MAD en sortien **13.808** (gra, no estrelles): el criteri
lliurat és DoG 1,5-6 px > 20 MAD amb pic ≥ 25 MAD, 4-400 px, i com a molt les 300 més
brillants (les que saturen el detall gran són poques). Portes: al rebut `V27_REBUT.md`.
Residu final del ghost, mesurat capa per capa: base i total plans, capes fines ±0,004, capa
gran +0,023 als 8 px centrals (costura de l'ompliment) → un puntet de ~10 px a la vista,
declarat al rebut. Set rondes en una nit; cada una la va tombar una mesura nova o una
vista, mai una porta que ja hi fos.

## 5. Deutes

- La V26 (`CapesTotalsV26_lineal_B.psb`) queda com a evidència de la trampa; no s'ha de
  fer servir.
- Un sol re-mostreig del RAW a la graella V23 (fase 2 de la cadena amb la geometria nova).
- La prova A/B amb la mateixa vara contra la V24 amb el Camera Raw de Pere.
