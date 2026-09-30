# 128 · La V24: el to fosc del DSC06984 i el reflex de la flamarada

**1 de setembre de 2026.** Ordre de Pere: V24 sobre la seva V23 (canvis seus
a les perles de Baily, mida del llenç 10551×7506 i contorn exterior), amb dues
decisions artístiques: la Lluna al grau de lluminositat del seu
`DSC06984.psb` (Downloads; revelat del RAW DSC06984, just després de C2) i el
REFLEX VERMELL de la flamarada sobre la lent al limbe lunar (marcat en verd a
la capa 1 del seu PSB) integrat al muntatge.

## 1. Les mesures que ho ancoren

- **El disc de la V23** (limbe de les capes 11-12, ajust de cercle, 705-720
  punts, rms 0,9-1,1 px): centre **(5361,9 · 3774,7), R = 453,5 px** — el
  retall del llenç de Pere conserva l'escala, i les capes lunars de la V22
  hi queden CLAVADES (centre de tessel·la 5361,8 · 3774,8): cap re-ancoratge
  calgut.
- **El to del disc al DSC06984.psb**: mediana RGB **(0,104 · 0,098 · 0,098)**
  — fosc, quasi neutre. La capa `EARTHSHINE al to DSC06984` porta la mateixa
  estructura validada (r=0,885) re-mapejada linealment a aquest pedestal amb
  contrast p10-p90 ≈ 0,045 (el del seu revelat).
- **El reflex**: al PSB de Pere és una llengua carmesí al limbe, marcada en
  verd (centre de la marca al px (3445, 3274)). El disc del PSB:
  (3662,5 · 3475,2), R=301,7 (fotogràfic; l'astromètric del registre és
  305,8 → el quocient 1,013 és el mateix biaix fotogràfic-vs-astromètric que
  la V22). **Offset del revelat: (+8,5, +7,7) px** entre el PSB i la graella
  del RAW (el retall del marge d'overscan).

## 2. La geometria del reflex: la cadena del run, cap rotació inventada

El DSC06984 és un dels 11 fotogrames de l'apilat d'earthshine: la seva cadena
geomètrica (marc lunar → RAW, amb el fit del salt i el registre del run) ja
existeix i està validada. El reflex viatja per **exactament aquella cadena**
(+ l'offset del revelat), i cau a **azimut −172° (limbe W)** — al costat de
la flamarada real de la V23. ⛔ El primer intent amb una rotació manual de
−44° el posava al nord: la rotació d'un contingut entre marcs NO es tria a mà
quan la cadena mesurada existeix.

La capa `REFLEX flamarada` és **additiva (Linear Dodge)**: l'excés de llum
del fotograma (reflex + el glow càlid de la vora interior del disc, que és
part del look del DSC06984) sobre el fons del disc, sense tapar res. El gra i
el color són els del revelat de Pere.

## 3. El fitxer

`CapesTotalsV24.psb` (NOU) = les 18 capes de la V23 **byte a byte** + les
dues noves. La fusionada surt del composite de Photoshop de la V23 amb les
dues capes compostes a la regió del disc. Portes: fidelitat 18/18, porta
Photoshop. Eines: `v24_capes.py`, `v24_munta.py`; mesures a
`cau_v21/{limbe_v23,d84_geo,v24_meta}.json`.

## 4. La segona ronda (01-09): el desajust de les perles i el perímetre

Pere: (1) «hi ha un desajust negre entre les perles — va passar temps entre el
Vixen d'abans de C2 i el DSC06984»; (2) «com podem rascar més detall del
perímetre lunar?». Mesures i cures:

1. ⛔ **La capa tapava les perles**: la llum del composite V23 comença a
   mediana **454,5 px** del centre del disc (i a 446 en alguns sectors), i la
   capa era opaca fins a 458 — la vora fosca de la capa s'interposava entre
   les perles. Cura: **màscara ADAPTATIVA per azimut** (720 sectors): la capa
   acaba 1,5 px abans d'on comença la llum del V23, sector a sector
   (tall mediana 453,0; min 445,7; max 455,0). Cap forat i cap tapament,
   per construcció.
2. **El perímetre torna a tenir textura REAL**: el camp suau de la vora
   (V22) se substitueix per pedestal suau + el **passa-alt del residu
   científic estès** (earthshine4_Gdisp, vàlid fins a 0,975 R; el passa-alt
   no pateix el vel), remapat amb el re-ancoratge i escalat a ×1,4
   l'amplitud del disc interior (èmfasi lleu declarat).

Porta Photoshop: OBRE · 20 capes; fidelitat 18/18. Eina: `v24_vora_b.py`.

## 5. La tercera ronda (01-09): la posició de Pere i el glow amb relleu

Pere va moure la capa REFLEX **4 px a l'esquerra** al seu Photoshop («les
perles són molt més fidedignes») i va demanar més detall encara al perímetre.

1. **La seva posició mana**: el muntatge nou parteix de LA SEVA V24 (les
   seves 18 capes + el seu retoc d'1 px a la capa [11] + el reflex a left
   4862), i tot pedaç del composite es fa per diferència exacta. La posició
   del reflex queda com ell l'ha deixada.
2. **El detall del perímetre tenia dos colls d'ampolla**: (a) el residu que
   hi posava passava pel Wiener de producte (λ<4 ×0,06) — per a l'ANELL de
   vora es regenera amb un **Wiener suau** (×0,35/0,85/1) i èmfasi ×2,2; i
   (b) ⏭️ la troballa que mana: **el GLOW additiu llis TAPAVA la textura** —
   la cura és modular el glow amb el relleu real:
   `glow' = glow · (1 + 0,7·HP_norm)` (β declarat) — el detall apareix DINS
   de la llum de la vora, que és on l'ull el busca (llum rasant).

Composite verificat: disc a mediana (0,109 · 0,102 · 0,101) — el to del
DSC06984 —, portes OBRE·20 i 19/19 capes intactes. Eines: `v24_vora_c.py`,
`v24_glow_modula.py`, `v24_munta_c.py`, `v24_munta_c2.py`.

## 6. Per què calien els 4 px de Pere: el biaix del limbe fotogràfic

Mesurat (fit de cercle per sectors sobre el DSC06984.psb): el centre del
limbe surt a **(3660,8 · 3474,3)** ajustant només el costat brillant (W/NW,
el glow de la corona) i a **(3664,4 · 3476,4)** ajustant només el fosc (E/SE)
— **3,6 px de diferència**. Just després de C2 el glow eixampla la transició
i desplaça el màxim de gradient; el meu ancoratge (fit complet, la barreja)
portava ~2-4 px d'error en la direcció de la il·luminació. La correcció de
Pere contra les perles era la bona per construcció: **les perles són un
contacte geomètric real, no un llindar fotomètric**.

⏭️ Regla: un limbe pel màxim de gradient sota il·luminació asimètrica porta
biaix de llindar (aquí 3,6 px); per ancorar fi: el costat fosc sol, o un
contacte real (perles). I quan l'operador ajusta contra les perles, la seva
posició mana.

## 7. La quarta ronda (01-09, nit): el perímetre amb la DADA REAL (V24d)

Pere, amb el `DSC06993.psb` a Downloads (marques verdes al perímetre): «la
part que marco s'adapta molt millor al contorn real de la Lluna que el que
has fet tu. No entenc com una sola imatge dona molt millor resultat que tot
l'agregat. Corregeix i repassa l'alineament, que 3,6 px no són 4 px.»

### 7.1 Per què l'agregat no tenia el contorn: dues exclusions de ciència

⛔ **La capa no tenia DADA al perímetre, i era per construcció**:

1. **La guarda de les tessel·les**: totes les tessel·les lunars científiques
   (`v21_lluna_tren`) porten `GUARDA_PX = 8` — la dada acaba 8 px DINS del
   limbe (per excloure corona i protuberàncies de l'estimació d'earthshine).
2. **El sostre LDIC**: fins i tot sense guarda, el glow de corona del 8 s és
   SATURAT al voltant del limbe (i fins ~20 px DINS del disc a la majoria
   d'azimuts): el pes de validesa el treu. Comprovat regenerant la tessel·la
   amb guarda −16: la dada composta acaba igualment a ~445 px.

O sigui: de ~447 px enfora la capa era **pedestal + textura fabricats**, i la
llum del perímetre la posava l'**anell additiu** de la capa REFLEX — que mor
a **452 px, 5 px DINS del contorn real** (453,5). El forat fosc entre l'anell
i la llum del muntatge era exactament el que Pere marcava. El fotograma sol
(el seu PSB) sí que porta el trànsit sencer disc→glow→corona: **per això una
sola imatge guanyava l'agregat al perímetre** — no per SNR, sinó perquè
l'agregat científic exclou el trànsit per disseny.

El contorn del PSB de Pere, mesurat: el màxim de gradient hi és a R≈291 px
del sensor (astromètric 305,8) amb **rms 7,5 px en azimut** — el contorn
viu és la frontera del glow, irregular i real, no una circumferència.

### 7.2 La cura: una fórmula per a tota la tessel·la

    E′_c = E_int_c · (1 − u) + L_fora_c(θ) · u

- **E_int**: el contingut actual de la capa (interior de l'apilat, intacte).
- **u**: la fracció de llum del DSC06993 SENCER (compost al marc V24 amb la
  cadena exacta, calibratge complet, pes = només zona activa — variant de
  DISPLAY declarada), normalitzada del nivell de disc al sostre de
  saturació. El gra, el flood i el contorn irregular són els del fotograma.
- **L_fora(θ)**: la llum del muntatge de Pere (composite V23) AL RADI
  D'EMPALME, per sector de 0,5° interpolat continu: on u→1 el valor és el
  seu i l'empalme és continu per construcció.
- Màscara fins a la seva llum (tall = Rllum per sector, interpolat), fora el
  marge d'1,5 px i el suavitzat de 7 sectors que arrodonien el contorn.

⛔ Tres trampes caçades pel camí, totes amb porta:

1. **u per canal tenyeix de VERD el trànsit**: el G satura abans (sostre més
   baix després del WB) i el seu u puja més ràpid → fracció ÚNICA de
   luminància; el croma del glow el posa L_fora.
2. **La mediana de la llum «més enfora» sobrevalora l'empalme**: la llum
   puja amb r; L_fora s'ha de llegir a Rllum+0,5..+2,5, no a +1..+6 (salt
   mediana +0,055 → −0,043).
3. **El terme de glow sense porta radial contamina l'interior**: les terres
   altes brillants de l'earthshine donen u~0,3; porta a r>408 (max|Δ|
   interior: 0,31 → 0,0000).

### 7.3 L'alineament, ara sí sub-px

La tessel·la del D93 s'ancora amb la cadena F1.3 (validada a 0,21 px entre
trens) i es corregeix el residu del re-ancoratge V22: el disc de contingut
queia a (495,80 · 495,80) de tessel·la i el disc de les perles del muntatge
és a **(495,877 · 495,741)** — el desplaçament de **(+0,077 · −0,059) px**
s'aplica DINS del re-mostreig únic (cap arrodoniment). Els «3,6 px no són
4»: la posició del reflex és la de Pere i no es toca; la banda nova va
ancorada al disc de les perles al centèsim.

### 7.4 Portes del lliurament

| porta | abans | ara |
|---|---|---|
| interior intacte (r<390, max·Δ·) | — | **0,0000** |
| salt d'empalme (mediana) | −0,089 (el muntatge actual) | **−0,043** |
| salt d'empalme (p95 abs) | 0,572 | 0,601 (estructural: la vora de l'anell vermell, present als dos) |
| forma del perfil radial vs dada real (mediana r) | +0,599 | **+0,702** |
| forma, pitjor decil (p10) | +0,102 | **+0,476** |
| croma del trànsit | tint verd (u per canal) | net (u de luminància) |

La capa REFLEX de Pere ([19]) es conserva amb els mateixos valors, posició
(left 4862) i mode. Eines: `v24_d93_geometria.py` (cadena + offset PSB,
descartat per warp del revelat), `v24_d93_display.py`, `v24_perimetre_d93.py`,
`v24_munta_d.py`; mesures a `cau_v21/{d93_disp_meta,portes_d93,porta_forma_d93}.json`.

⚠️ El PSB de Pere NO és la font de píxels: la correlació amb el RAW encaixat
surt a 0,31 amb offsets per quadrant dispersos (~4 px) — el revelat porta
reducció de soroll i probablement correcció de lent (warp). La font és el
RAW per la cadena exacta; el PSB és el jutge visual.

## 8. La cinquena ronda (02-09): els tres arcs, i la fórmula refeta (V24e)

Pere (marques sobre la V24d): arcs blau (NW, dins del disc) i lila (W i E) —
«estem generant artefactes on no n'hi han d'haver; el DSC06993 no té aquests
defectes». Mesurat als perfils radials: **els tres eren de la fórmula V24d**,
no de la dada (el fotograma real hi és monòton i llis):

1. ⛔ **Blau NW / lila W**: vall a r≈412-424 — interferència entre la textura
   vella de la vora (E_int duia el pedestal+èmfasi de vora_b/c) i l'esglaó de
   la porta radial r>408.
2. ⛔ **Lila E**: la dada hi està SATURADA de 444 px enfora, però el nivell
   d'empalme estava clavat al valor FOSC del composite just fora de Rllum —
   la fórmula reproduïa l'anell fosc d'ell en lloc de cobrir-lo.
3. ⛔ I la llum del perímetre l'estava posant l'**anell additiu sintètic** de
   la capa REFLEX (tot el perímetre): amb el glow real a la capa, duplicava
   la llum i feia un bony-i-caiguda que la realitat no té.

### 8.1 La fórmula V24e (cada peça per construcció, cap porta geomètrica)

- **u = EXCÉS sobre la línia de base d'earthshine**: l'apilat lineal validat
  (11 fot, pesos del rebut V4) fa de baseline per regressió (L93 ≈ 414 +
  0,650·S, r<400), llindar = 2σ_MAD del soroll (47 comptes). Res de porta
  radial: l'interior queda net perquè el flood hi ÉS zero.
- **El flood de display ha d'estar CONNECTAT al limbe** (component connex):
  una taca que només té el fotograma sol i l'apilat no confirma (fantasma a
  r≈220, az −88°) mor sola.
- ⛔ **El baseline i E_int s'estenen llisos des de r<426**: l'apilat porta
  les ONZE vores de guarda desplaçades (±2 px per fotograma) i de r>430 cau
  a zero PER TRAMS — si el baseline les hereta, el flood surt amb arcs
  foscos DISCONTINUS (guionets). Va costar tres iteracions de trobar-ho:
  la fuita era pel baseline, no pel contingut.
- **La corba tonal del trànsit, CLONADA del revelat de Pere**: h_c(u) es
  mesura aparellant píxel a píxel el flood amb el seu render (40 calaixos,
  monòtona, genoll arrodonit). El camí càlid és al peu (u=0,05 → R 0,32 /
  G 0,16 / B 0,00): el marró-taronja és mesurat, no imitat. ⚠️ h està
  lligada a la DEFINICIÓ d'u: si es recalibra u, h es re-mesura sola.
- **El traspàs es fa on el contingut d'ell S'HI QUEDA al nivell**: objectiu
  = p90 del seu perfil MÉS ENLLÀ del solc (el llavi brillant amb solc
  darrere ja no enganya el criteri: mínim rodant de 8 px ≥ 0,92·objectiu),
  fre de derivada azimutal ALÇANT valls (escapçar pics tornava a fallar al
  braç NW), i contingut de banda = max(meu, seu): res d'ell tapat mai.
- **La capa REFLEX es garbella al sector de la flamarada** (|az|>130°,
  finestra suau): el vermell on és real i on Pere el va posar; l'anell
  sintètic de la resta del perímetre fora.

### 8.2 Les portes i els dos jutges externs

Verificació adversària amb agents independents (2 rondes + 1 focalitzada):
el guarda de regressions PASS (interior p99 0,041; nucli r<0,75R idèntic,
correlació d'estructura 0,966; protuberància i flamarada intactes; les 3
portes del JSON), i el caçador d'artefactes va tombar dues iteracions
senceres (vall del 4-5 % a l'empalme; esglaons; costura d'arcs al S; vall
del 15-20 % al braç brillant NW) fins a la fórmula d'aquí dalt. Mètriques
finals: valls (mediana per sector) 0,166 → **0,011**; al braç NW el mínim
rere el llavi queda a l'**1,9 %** de l'altiplà receptor (el jutge focalitzat
va tombar el 7 % anterior: el llindar de permanència del 0,92 «autoritzava
per construcció» un 8 % de fossat — ara 0,98 i objectiu = l'altiplà de
veritat, p90 a [Rllum+8, Rllum+30]);
forma del perfil vs dada real: mediana +0,60 → +0,70, p10 +0,10 → +0,48.
Residus declarats: taca vermellosa preexistent a l'E (també a la V24d, del
contingut receptor) i l'enfosquiment prop del limbe on abans hi havia el
glow sintètic (garbell declarat, mai més fosc que el to del disc).

Eines: `v24_perimetre_e.py`, `v24_munta_e.py`; portes a
`cau_v21/portes_e.json`. ⚠️ Lliçó de mètode de la ronda: la meitat dels
defectes (guionets, vall d'empalme, costura del S) només els va veure o
acotar bé **un jutge extern mirant la imatge**; les portes numèriques que
jo mateix havia triat hi eren cegues fins que el jutge va dir on mirar.
