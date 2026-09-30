# 125 · CapesTotalsV21: el plate-solve de les estrelles i la capa d'earthshine

**28 d'agost de 2026, nit.** Ordre de Pere sobre la seva V19 re-desada (21:31,
sense la capa d'estrelles dolenta ni el Pasalt): (1) les «estrelles» de la V19
no eren estrelles netes — a l'apilat Sony >1 s les estrelles es desplacen
entre RAWs; (2) plate-solve, apilat >1 s registrat a les estrelles amb base el
8 s amb la Lluna centrada, i capa d'estrelles; (3) capa NOMÉS d'earthshine,
amb el moviment propi de la Lluna.

## 1. El «lio» de les estrelles, mesurat

Els 5 fotogrames >1 s (2s×3 + 8s×2) estan registrats AL SOL (correcte per a la
corona). Les estrelles, mesurades fotograma a fotograma contra la base:

| fotograma | t (s) | apuntament | desplaçament que deixava el registre solar | ajust (θ, t) | rms |
|---|---|---|---|---|---|
| DSC06993 (8 s) | 70 | 2 | — (BASE: la Lluna a 151 px del centre) | identitat | — |
| DSC06996 (2 s) | 82 | 2 | 3,7 px | θ≈0 · (+1,40, +3,43) | 0,04 px |
| DSC06999 (2 s) | 88 | 2 | 4,7 px | θ≈0 · (+2,10, +4,18) | 0,04 px |
| DSC06987 (8 s) | 37 | 1 | 8,1 px | **θ=+7,86′** · (+0,94, −4,94) | 1,13 px |
| DSC06984 (2 s) | 18 | 1 | ~8 px | θ=+7,86′ · (−0,68, −6,64) | ~1,1 px |

**La causa dominant: el salt d'apuntament va incloure una ROTACIÓ DE CAMP de
+7,9′** (0,13°) — a 3.000 px del centre són 7-8 px: les estrelles de les dues
meitats del temps queien doblades. La deriva sideral−solar predita (0,041″/s)
és només 0,15-0,42 px: **el lio era la muntura, no el cel.** Els ajusts fins
surten de correlació de fase per finestres de 512 px (52/35/35 finestres, rms
0,04-0,06 px) per als parells del mateix apuntament, i d'aparellament de fonts
puntuals (8 parelles brillants, rms 1,13 px) per al salt entre apuntaments —
el gra correlacionat fa inútil la correlació de finestres entre apuntaments
(pics ≤0,03).

⛔ Dues trampes de mètode caçades pel camí: el total de la correlació de
finestres s'ha de referir al CENTRE de la finestra (l'origen deixa un biaix
de WIN/2 exacte que un rms de 0,06 px no delata: 52 finestres «perfectes» amb
el desplaçament sistemàticament corregut −512 px); i la finestra ha de ser
lliure de corona i Lluna A TOTES DUES imatges, no només a una.

## 2. Els dos apilats (base DSC06993: el 8 s amb la Lluna centrada, t=70 s)

Recepta LDIC del run 016, un sol re-mostreig RAW→llenç V19, coherència K per
fotograma, WB i àncora tonal EXACTES de la capa Sony (rebut de la V17):

- **Apilat registrat a les ESTRELLES**: canvas → raw_base (àncora solar de la
  base) → raw_n per la cadena d'ajusts (raw_n = R(−θ)·(raw_base − sol_base −
  t) + sol_n). La Lluna de cada fotograma, exclosa (es mou 0,585″/s respecte
  del Sol). Alineació contra la capa Sony de la V19: **(−0,14, −0,13) px** —
  el marc solar de la base i la capa 12 coincideixen.
- **Apilat registrat a la LLUNA**: àncores = centres lunars mesurats per
  fotograma (la rotació de camp també gira el disc: compensada amb la mateixa
  θ). Només el disc (guarda 6 px dins del limbe, vora 6 px): NOMÉS earthshine,
  sense corona ni protuberàncies. Disc ple: 596 kpx, mediana render RGB
  (0,748 · 0,695 · 0,715) — el senyal d'earthshine dels 8 s hi és sencer.

## 3. Les capes de la V21

- **`ESTRELLES` (Linear Dodge)**: detecció sobre l'apilat registrat (ara les
  fonts són puntuals), discos suaus, contingut = excés sobre el fons local.
  La mètrica del lio: elongació mediana de les 120 fonts brillants —
  capa 12 (solar) vs apilat registrat (vegeu el rebut).
- **`EARTHSHINE` (Normal)**: el disc de l'apilat lunar a la posició de la
  Lluna de la base al llenç (6465,4, 6752,6 — el disc de C2 del muntatge de
  Pere), màscara suau 14 px dins del limbe. Pere en dosa l'opacitat.

## 3 bis. La segona ronda (28-08, nit tancada): el veredicte de Pere i les cures

Pere va refusar la primera ronda: «l'earthshine no es veu gens» i «estàs
interpretant estrelles que no són — tota estrella que pugui fer plate-solve,
la poses; les altres són fake». Tenia raó a totes dues:

1. **Estrelles: el 97 % de les 1.263 deteccions cegues era gra.** Creuades amb
   el catàleg de l'astrometria del 17-08 (Tycho-2/Hipparcos projectat al pla
   tangent + solució de placa radial de DSC06993 — exactament el nostre
   fotograma base — 38 estrelles, rms 0,71 px): només 35 aparellaven. La capa
   definitiva es construeix del catàleg cap a la imatge: **fotometria forçada
   a les 1.084 posicions predites** dins del llenç, llindar 3,5σ local →
   **87 estrelles, totes amb HIP/Tycho** (V 5,73 a 11,5;
   `cau_v21/estrelles_final_cataleg.json`). ⛔ Lliçó: una detecció cega sobre
   un compost amb gra correlacionat NO és un catàleg d'estrelles; el catàleg
   extern és l'única font d'identitat.
2. **Earthshine: no es veu perquè no hi pot ser, i ara està acotat.** El disc
   en lineal (mediana G 1565 comptes) separat en vel radial + residu
   asimètric (±150): la validació selenogràfica (model de rotació IAU +
   de421; libració lon +4,1° lat −1,1°; paritat i orientació verificades amb
   les 87 estrelles) diu que **les maria NO hi són** (3/8 fosques on toca;
   terres altes tampoc): el residu asimètric és l'asimetria del vel de
   corona, NO superfície lunar — i no es lliura com a earthshine. La física
   quadra: Sol a 9,1° → X=6,4, k≈0,40 mag/X → **extinció ×11 sobre
   l'earthshine**; el senyal de superfície queda **≲1,5 % de la llum del
   disc**, sota el soroll de 22 s. Troballa menor: un tret brillant real del
   limbe oest a 32 px de Grimaldi (moon-fixed: sobreviu el salt
   d'apuntament). ⏭️ Per al 2027 (Tarifa, Sol a ~35°): extinció ~×1,7 —
   l'earthshine hi sortirà.
3. La capa lliurada és `EARTHSHINE+VEL` (el disc registrat, la DADA, amb el
   nom honest) + `ESTRELLES` amb les 87 de catàleg. El PSB es remunta
   (v21_munta3) amb les mateixes portes.

## 3 ter. La tercera ronda (29-08): el control nul, i el camp era net

Pere, sobre les 87 de la ronda 2: «n'estàs detectant fora del camp teòric del
300 mm comptant amb el moviment que va fer la muntura». Tres mesures:

**(a) El camp és NET.** Cada posició lliurada, tornada del llenç a les
coordenades del sensor de cada fotograma amb la cadena geomètrica sencera
(rotació de camp del salt inclosa): **cap fora de la graella RAW** de com a
mínim dos fotogrames. La més exterior és **HIP 46910 a 4,05°** del Sol, i el
semicamp del 300 mm és 3,56° × 2,37° → **diagonal 4,27°**: és a la cantonada,
a dins. Repartiment: 68 vistes pels 5 fotogrames, 9 només per l'apuntament 1
i 8 només pel 2 — la franja que el salt de muntura va afegir.

**(b) Però la intuïció era bona, i el defecte era la PURESA.** Control nul
aparellat: **les mateixes posicions predites girades al voltant del Sol**
(11 angles) — mateix radi, mateix anell de soroll, mateixa fotometria
forçada. A 3,5σ la falsa alarma és del **2,8 % per posició** (no del 0,02 %
que diria una gaussiana: el gra del drizzle és correlacionat i es pren el
màxim de 49 px). Desglossat:

| V | posicions | detectades | control nul | excés | σ |
|---|---:|---:|---:|---:|---:|
| <8 | 33 | 30 | 1,0 | 29,0 | 29 |
| 8-9 | 40 | 21 | 0,8 | 20,2 | 20 |
| 9-10 | 141 | 18 | 3,5 | 14,5 | 7,8 |
| **10-11,5** | **520** | **18** | **15,2** | **2,8** | **0,7** |

⛔ **Les 18 més febles de la ronda 2 eren gra** (0,7σ): el catàleg dona la
identitat, però **no dona la detecció** — cada posició predita és una prova
independent, i amb 520 proves el llindar sol fabrica estrelles. El límit de
detecció real de l'apilat és **V ≈ 9,5**.

**(c) Dues correccions de mètode que van sortir de la mateixa auditoria.** La
correcció fina predicció→imatge de la ronda 2 (+0,94, +2,18) estava
**contaminada**: sortia d'aparellar contra les 1.263 deteccions cegues, que
eren gra. Mesurada amb centroide sobre les brillants: **(−1,19, +0,53) px**.
I hi ha **distorsió de camp residual** que la solució de placa radial no
porta: un model quadràtic en (x,y) baixa el residu de **2,74 a 1,42 px** de
mediana. Amb les dues cures, la finestra d'acceptació pot ser de ±2 px.

**El lliurable: 85 estrelles, puresa 95,8 % mesurada** (falses esperades 3,5),
V ≤ 9,5, finestra ±2 px, llindar 3,0σ — el tall el tria el control nul, no
l'ull. Prova independent que ara són estrelles: la **fotometria segueix la
magnitud del catàleg**, r = **+0,713** (a la ronda 2: +0,181 — la signatura
d'una llista seleccionada per un llindar, amb el flux clavat al terra a totes
les magnituds febles). Eina: `v21_estrelles_purga.py`, rebut a
`cau_v21/purga_rebut.json`.

⏭️ **Regla general que en surt**: una llista d'objectes triada per llindar no
es lliura mai sense un **control nul aparellat** que digui quants n'hi ha de
falsos. La correlació flux↔magnitud és la comprovació barata que ho delata.

## 4. El fitxer

`CapesTotalsV21.psb` = la V19 re-desada de Pere (14 capes, byte a byte;
auditoria del seu retoc: màscares Sony i FONS intactes — el retoc va ser
treure les dues capes velles) + les dues capes noves. Fusionada nova amb les
màscares vives. Portes: fidelitat byte a byte, porta Photoshop, vistes al
llenç sencer. Números finals al rebut (`cau_v21/rebut_v21.json`) i al
`CapesTotalsV21_REBUT.md` del costat del fitxer.

Eines: `research/tools/capes_totals_v14/{v21_explora,v21_ajust_estrelles,
v21_fits_finestres,v21_apilats,v21_munta,vistes_v21}.py` · mesures a `cau_v21/`.
