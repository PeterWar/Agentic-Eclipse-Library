# 120 — CapesTotalsV17: l'apilat Sony >1 s a la geometria de Pere, el WB mesurat i el limbe de la 09

Encàrrec de Pere (28-08-2026, migdia), sobre la seva V16: netejar el limbe lunar de la
màscara de la capa 09, substituir la capa Sony de 8 s per **un apilat de tots els
fotogrames de més d'1 segon** («a veure si podem rascar més corona externa», centrats i
descentrats), i ajustar **balanç de blancs** + **màscara de desenfoc gaussià** perquè
encaixi amb les capes Vixen. Continua `research/118` i `119`. Lliurable:
`CapesTotalsV17.psb` (3,67 GB) + rebut + vistes; la V16 intacta.

## 0. Resum en sis línies

1. **La V16 és una re-escenificació de Pere**: llenç 12415×12095, **totes les capes Vixen
   rotades +10,880°** (mesurat per correlació, resposta 1,04; escala 1), Lluna prop del
   mig, la capa Sony transformada a mà A DALT de les Vixen, capes 08-01 apagades i una
   capa «Pasalt» seva. Tota la feina s'hi fa a la SEVA geometria, mesurada i no suposada.
2. L'apilat nou: **5 fotogrames >1 s** (2 s ×3 + 8 s ×2, els dos apuntaments), recepta
   LDIC del run 016, **un re-mostreig del RAW a la graella V16** via la transformació
   mesurada — la vora interior de la dada avança de 2,77 a **1,95 R☉** (p99) i la
   integració de 16 a 22 s. Alineació verificada contra els plomalls de la capa 01 de
   Pere: **(−0,10, +0,08) px** (2,6 Mpx de zona).
3. ⛔ **La referència del WB/nivell va necessitar tres intents, i la lliçó és de mètode**:
   la fusionada de la V16 (1r) i la capa 09 (2n) són quasi NEGRES a l'anell de solapament
   —les capes 08-01 són apagades, i 1/60 s no grava corona a 2,2 R☉— i l'ajust «perseguia
   el negre» (àncora ×94 i ×67 cap avall). La referència correcta és **la capa 01
   (10,3 s): la corona externa del muntatge de Pere, la capa el paper de la qual assumeix
   la Sony**. Amb ella la convergència és al 3r decimal: seu (0,866 · 0,751 · 0,653) ↔
   meu (0,867 · 0,751 · 0,653) a 2,15-2,60 R☉; guanys lineals **R ×1,001 · B ×1,188**.
4. **La màscara de mescla no és un desenfoc literal**: un Gaussià sobre una rampa
   obriria la màscara PER DINS de la vora de saturació (el halo del `117`). És un
   *smoothstep* radial de **2,00 a 2,65 R☉** — arrenca a la vora de saturació mesurada
   (p99 1,95 + guarda) amb **zero exacte per dins** i 296 px de transició — × la solidesa
   del pes.
5. **Capa 09**: la màscara de Pere entrava 2-10 % dins del disc (vel). Cura de la V14 amb
   el disc **mesurat al contingut de la mateixa capa a la V16** (centre (6480,1 · 6756,0),
   R 452,4, 164 raigs, rms 0,71): 198 kpx canviats, tots dins del disc, res repintat.
6. Fidelitat: **tota la resta byte a byte** (les 12 Vixen menys el canal de màscara de la
   09, i «Pasalt» sencer); blocs globals heretats fora (trampa 8BIM/8B64); porta
   Photoshop: **OBRE**.

## 1. Notes de mètode que queden

- **La geometria del muntatge d'altri es MESURA**: rotació per escombrat amb correlació
  (grossa a 1/4, fina a resolució completa amb finestra Hanning: 10,75° → 10,880°, i el
  0,08° de diferència eren 2,8 px al braç de 2000 px), translació pel centre del bbox +
  residual de correlació. Les bbox de Photoshop d'una capa rotada donen l'angle
  analíticament (sistema 2×2 amb els dos costats) però no el signe ni el subgrau.
- **Compondre a la geometria final en un pas** estalvia el re-mostreig doble que té
  transformar a mà una capa ja re-mostrejada.
- ⚠️ **Un ajust iteratiu contra una referència no vigilada convergeix cap on sigui** (aquí,
  cap al negre, dues vegades). La referència s'ha de mirar abans: nivell absolut,
  cobertura, i si és la cosa que l'encàrrec vol dir («les anteriors capes de la VIXEN» =
  les capes, no l'estat actual del compost).
- ⚠️ Al llenç de la V16 queda **un anell fosc entre ~1,5 i 2,0 R☉**: és l'estat del
  muntatge (08-01 apagades) i cap apilat Sony no hi pot arribar (saturació dels 2 s a
  1,95). El pont és de Pere (tornar a encendre 08/07/06 o les seves màscares). Declarat
  al rebut, no tocat.
- Els fotogrames d'exactament 1 s (DSC06985/06991) queden FORA per literalitat de
  l'encàrrec («més de 1 segon»); afegir-los és una línia a `FRAMES_MES1S` de
  `fes_v17.py`.

Eines: `research/tools/capes_totals_v14/{fes_v17,vistes_v17}.py` (el fes porta les
mesures i el rebut JSON a `cau_v17/`).
