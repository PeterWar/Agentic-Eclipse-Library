# 123 · El desenfoc radial zoom de Pere: el fons per raig — estudi, preu i operador formalitzat

**28 d'agost de 2026, vespre-nit.** Pere, després de la segona ronda de marques
(`research/122`), va resoldre els halos **a mà** amb un procés de Photoshop que
va declarar «l'única manera efectiva que he trobat de juntar el Vixen amb la
Sony», i va demanar estudiar-lo i incorporar-lo al pipeline. El fitxer és
`V18-DesenfocRadialZoom.psb` (953 MB, llenç 8156×5422 = retall 3:2 del llenç
V18 amb origen a (2196, 4124); Sol a (4273,2, 2633,6), NCC 0,89). Estudi fet
amb un workflow de 4 agents; tot mesurat, res suposat.

## 1. El que Pere va fer, mesurat sobre el fitxer

El seu relat: duplicar la imatge aplanada; cobrir les cantonades del duplicat
amb el color del cel; Desenfoque Radial mode **ZOOM** (quantitat màxima,
qualitat òptima); i una màscara que deixa passar el detall de l'original.
El que el fitxer conté de veritat:

- **La màscara és una rampa RADIAL pura**: m = 0 exacte fins a 2,45 R☉, 0,50 a
  2,85, 1,000 des de 3,25 fins a la vora. R² del model «només radi» = 0,992;
  l'energia de detall no explica **res** (correlació del residu amb el detall:
  −0,003). Ploma llarguíssima (transició p50 = 287 px; **cap** pas dur). O
  sigui: **no és una barreja local per marca — és un tall radial global**:
  original fins a ~2,6 R☉, fons desenfocat per a tot el camp exterior.
- **Les cantonades pintades**: cada cantonada duu el color del cel **local**
  d'aquell cantó (coincidència 0,1-0,3 % en nivell i croma exacta en B/G:
  1,137 contra 1,134) — per això les costures del pintat són invisibles. El
  pintat s'estén ~1.500-2.000 px per cantonada i deixa la variància a
  0,35-1,2 DN (contra 16-66 de l'original).
- **Dos experiments apagats** dins del fitxer: `capa0` = un primer intent amb
  desenfoc **isòtrop** gros (gaussiana σ≈128 px) i màscara pintada a mà,
  descartat; `capa3` = una capa d'**anotacions** amb traços verds (3,7-6,3 R☉)
  i taronges (~5,8) — les marques de Pere en aquest retall.

## 2. Què és el «Desenfoque Radial ZOOM», mesurat

- Les estrelles de l'original hi esdevenen **ratlles radials** (desviació
  mediana de l'orientació respecte del raig: **2,0°**); el centre de
  convergència és compatible amb el **Sol** (rms mínim al Sol, per sota del
  centre geomètric del llenç).
- El nucli del smear, mesurat a les ratlles i per log-polar: **abasta del ±10
  al ±20 % del radi** (proporcional a r, com mana un zoom), amb un component
  de còpia (~7 %) i cues llargues. En rugositat fina equival a una **gaussiana
  en ln r amb σ ≈ 0,2**.
- Atenuació del passa-alt (rms per anell, original → desenfocat): 243→61
  (2-3 R☉), 217→28 (3-4,5), 173→7 (4,5-6,5), 40→1,7 (6,5-9). El que esborra
  al camp llunyà són sobretot **anells concèntrics** (els halos) i el gra;
  el detall que hi sobreviu és radialment allargat (fracció tangencial de
  l'energia 0,58-0,87 contra 0,46-0,67 de l'original).

## 3. Per què funciona — la lliçó estructural

**Al camp mitjà i llunyà de la corona, l'artefacte i el senyal viuen en
dimensions ortogonals**: els halos, arcs, costures de fusió i esglaons són
variació **al llarg del raig** (perfil radial); els streamers són variació
**entre rajos** (azimutal), perquè són radials per física. Un suavitzat
**només al llarg de ln r** és un filtre selectiu d'estructura que mata el
100 % de la primera família i conserva la segona.

I la diferència de fons amb les nostres V18/V19: el ρ d'igualació necessitava
una **referència** (el Vixen) i moria on la referència moria (la vora del
mosaic, els sectors enverinats, la retenció, la fosa…). El fons per raig és
**autoreferent** — el fons és la mateixa imatge promediada al llarg del seu
raig — o sigui que **no té disputes de referència ni pot fer costures**, i
val fins a la cantonada del llenç. El preu és un altre (§5).

## 4. Les portes sobre el resultat de Pere (abans = original; després = el seu F)

- Bony radial a **les 17 marques** (8 de la ronda 2 + 9 de la ronda 1,
  re-derivades al retall): **15 de 17 a 0,000 exacte**. Residus: verd_1
  (0,027 mesurat en cru — però part és l'artefacte de població dels rajos que
  surten del llenç per dalt, a 5,78 R☉; amb la porta neta el màxim de sector
  de F queda a **0,0084**) i taronja_1 (0,0011).
- Escombrada 24 sectors: bony mediana **0,0155 → 0,00056**; tv croma en excés
  R/G **0,0219 → 0,0044**, B/G 0,0111 → 0,0000.
- El que el mètode NO toca (per construcció, no barreja azimuts): les
  asimetries azimutals de gran escala (±5-9 % entre sectors), que en bona part
  són el patró real heretat del Vixen (`research/122` §2.4).

## 5. El preu, quantificat

1. **Fonts puntuals: extinció total al camp exterior.** Supervivència
   d'estrelles = exactament 1−m (el desenfocat no aporta cap flux puntual):
   100 % fins a 2,8 R☉, 50 % a ~2,85, **0 % des de 3,1**. I les mortes no
   desapareixen: deixen **vetes radials febles d'11,6 σ** que un passa-alt
   posterior tornaria a treure.
2. **Detall tangencial**: forma preservada (correlació 0,65-0,95) però
   **−25-30 % d'amplitud** a r 4-7.
3. **Fotometria**: el zoom transporta llum de la corona interior cap enfora —
   **+3 a +4,4 % de nivell a r 3-4,5** (monòton: cap porta de bony ho veu,
   però és un canvi real del perfil).
4. **Estatus de la dada**: des de 3,25 R☉, el 99,9 % del que es veu al seu
   compost és la còpia desenfocada — **cosmètica, no dada**. Coherent amb D1
   (la via de la FOTO: el fusionat no és una mesura), però s'ha de declarar.

## 6. L'operador formalitzat («fons per raig») i el prototip

`scripts/operador_prototip.py` (20 s de punta a punta, determinista):

- graella polar **4080 rajos × 1200 mostres de ln r** (2,0→11,5 R☉),
  `cv2.remap` bilineal; **pes = remap d'uns** (0 fora del llenç) i tot
  suavitzat **normalitzat pel pes** — la feina de les cantonades pintades de
  Pere, sense pintar res;
- **B** = mediana d'11 mostres al llarg del raig (robusta a estrelles) +
  gaussiana en ln r amb **σ_lnr = 0,2** (triada per escombrat: reprodueix la
  rugositat del desenfocat de Pere i passa les portes); **zero suavitzat en
  azimut** — el que fa bo el mètode és conservar l'azimut;
- **F2** = original·(1−m) + B·m amb **la màscara de Pere**;
- **F3** = F2 + **re-injecció d'estrelles** (detecció sobre un fons de
  detecció B_det amb σ=0,05 — amb el B llis la detecció cau de 2117 a 31:
  el fons de detecció i el de composició han de ser diferents).

Resultats (F1 = el de Pere / F2 / F3): bony màxim de sector **0,0084 / 0,0071
/ 0,0086**, mediana **0,00082 / 0,00059 / 0,00063**; croma lleugerament millor;
fidelitat azimutal igualada a r=3, 4 i 5 (l'únic dèficit real és −0,025 a r=6;
a r=8 el que falta és gra incoherent del cel, i en senyal lent hi ha empat
0,9982/0,9996); **estrelles supervivents: 1 / 2 / 2.097 de 2.102** (99,8 %).
La vista de diferència ×16 ensenya els dos defectes del mètode manual que el
prototip evita: les vetes radials de cada estrella morta i les **empremtes de
les cantonades pintades arrossegades cap endins pel zoom**. |F2−F1|: mediana
0,21 %, p99 1,16 %.

## 7. Què s'incorpora al pipeline

1. **Operador nou de fons: `fons_per_raig`** (suavitzat normalitzat en ln r
   per raig, autoreferent, amb pesos per a les vores) com a **via canònica
   per al camp exterior** de qualsevol compost fusionat: substitueix les
   nostres cures amb referència allà on el que hi ha és fons, i **no pot fer
   halos ni costures per construcció**.
2. **Divisió del llenç en dos règims**, amb un radi de detall declarat
   (Pere: rampa 2,45→3,25 R☉, smoothstep, ploma ≥250 px): a dins, dada
   (i allà el ρ del `research/121` continua sent la cura bona per a la
   fusió entre trens); a fora, fons per raig. **La rampa és estètica i la
   tria Pere.**
3. **Cap sacrifici d'estrelles**: detecció sobre B_det (σ=0,05) + re-injecció
   després del fons. El «SACRIFICI» que Pere declarava queda eliminat.
4. **La lliçó estructural com a norma de disseny**: tota cura anti-halo del
   camp exterior ha d'operar **al llarg de ln r i prou**; qualsevol operació
   que barregi azimuts (o que foni per canal radialment) pinta artefactes
   nous — ho hem mesurat dues vegades (`research/122` §4).
5. **Declaració de règim al rebut**: més enllà del radi de detall el producte
   és fons estilitzat, no dada; el biaix fotomètric del mètode manual
   (+3-4,4 % a 3-4,5 R☉) al prototip queda substituït pel de B (mesurable i
   ajustable si es vol re-anivellar al perfil de l'original).

## 8. Fitxers

Tot a `research/tools/capes_totals_v14/cau_v19/desenfoc/`: extraccions
(`capa1/2_rgb16.npy`, màscares, `geometria.json`), mesures dels agents
(`fable5/` portes i preu; `fable/` màscara, cantonades i experiments;
`geometria_fable/` nucli del zoom), prototip a `operador/` (B, F2, F3,
estrelles, `informe.json`, vistes del llenç sencer) i `scripts/`
(`operador_prototip.py` i tots els de mesura). Lliurat a Pere:
`V18-DesenfocRadial_F3_operador_estrelles.tif` (16 bits, al costat del seu
PSB). El seu fitxer: **només lectura, intacte**.
