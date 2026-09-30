# 171 · El detall real de la banda del limbe: capa tangencial calibrada contra la veritat (V100)

26-09-2026 · Claude, amb Codex Astra (pla i verificació) i 3 agents (història, píxels, dada) · Encàrrec de Pere: «fes l'estratègia que doni més detall als píxels sense inventar-te res; a la V75 i abans en teníem».

## 1. Què hi havia a la V75 i abans
- La base de la família de la V69 (V69–V84; la de la V80 de Pere) portava fotogrames reals vistos a poca distància del seu limbe (recomposició de la V51/V52), però amb tres coses que no eren dada:
  - un nivell de model (taula de dèficit, ×1,07–2,2);
  - 1.746 píxels omplerts amb el veí més proper;
  - filtres amb farcit dins de la Lluna, que feien una vora clara falsa a dalt, a 4–6 px.
- La V80 es registra exactament contra el llenç (retall a (1325, 1142), 0,05 px). Correlacionada amb la dada independent:
  - baix-esquerra 2–5 px i dalt-dreta ≥ 3 px: **real**;
  - dalt al centre 3–8 px: **no era dada** (ρ −0,37…0);
  - 0–2 px: la vora de la Lluna.
- La V98 i la V99 van perdre la corona real de baix-esquerra (rampes amb vora dura).

## 2. Què NO funciona per al NIVELL de la banda
- **La T per angle fi canvia amb el temps** (d30): entre èpoques, un 2–3 % en verd i un 6–9 % en vermell i blau (la PSF canvia amb el Sol baixant). Una T mesurada en fotogrames tardans no val per als primerencs.
- **Autocalibratge de Kuhn, Lin i Loranz (1991)** (d31, d32; el pla de camp d'imatges desplaçades d'una escena estàtica): funciona fins a D ≈ 2 px, però amb moviment en una sola direcció té el gradient degenerat. A la dreta oscil·la entre +0,7 i +5,8 % a 2,5–4 px, i a dalt és pitjor (la Lluna s'hi mou 1,3 px en radial).
- **Calibració de les exposicions amb guany i nivell de negre** (d33): els residus depenen de la brillantor. És la selecció de la finestra LDIC als seus límits (cada fotograma només conserva els valors de dins de la finestra).

## 3. Què sí: el detall TANGENCIAL
- **Al llarg de l'arc, a una distància fixa,** la transmissió de vora, la barreja de classes i els biaixos de nivell són constants i s'anul·len. Els raigs de la corona són precisament variació tangencial.
- **Prova amb veritat (d38):** a la dreta, els primerencs sols contra la veritat dels tardans nets.

  | D_real | r |
  |---|---|
  | 2–2,5 px | 0,34–0,43 (amplitud 2–3 vegades la real: contaminació de la vora de la Lluna i soroll) |
  | 2,5–3 px | 0,60 |
  | 3–3,5 px | 0,82 |
  | 3,5–4,5 px | 0,92 |
  | ≥ 4,5 px | 0,97 |

  El pendent E[veritat | A] per banda d'escala és el guany (Wiener calibrat contra la veritat).
- **Corroboració a la mateixa banda:** continuïtat radial amb la dada neta a 5–8 px (d34), meitats temporals i prova cel contra Lluna (agents). Parells i senars comparteixen les vores de la Lluna i el mosaic: no són prou independents.
- **La capa (d35b):**
  - bandes DoG al llarg de l'arc de 2–4, 4–8 i 8–16 px, per a un gra fi que no hi és;
  - cada banda multiplicada pel seu guany de veritat, que és zero per sota de D_real 2,75;
  - la mitjana és zero al llarg de cada arc, de manera que **no pot fer cap anell**.
- **Contrast (d36, d37b, v4):** el pendent amb què el compost natiu mostra la dada just fora de la banda es reprodueix dins la banda: 0,97–1,05 al render final. Es mesura amb renders de prova al Photoshop, perquè la resposta de Superposar amb les capes d'ajust de Pere no es pot deduir. **S'iguala la transferència, no l'energia.**

## 4. Lliçons per a la skill
- **Una textura antiga «amb detall» no és un jutge:** comparteix fotogrames i soroll amb la dada. Cal correlacionar-la amb la dada independent **i** exigir reproductibilitat entre meitats **i** continuïtat radial.
- **Parells i senars** comparteixen la posició de la Lluna i la fase del mosaic. Per a la vora cal fer servir meitats temporals, la prova cel contra Lluna i, sobretot, una prova amb veritat del mateix operador.
- **Una regressió de representació (β)** l'enganya una protuberància: cal regressió robusta.
- **Una capa nova** es pot muntar sense tocar res (b2_munta_v100: inserció del registre i dels canals en l'ordre dels registres).

## 5. V101 (després de la verificació de Codex)
Codex va trobar a la V100 quatre problemes:
- píxels retallats a la protuberància de l'esquerra;
- una mitjana logarítmica de −1,31 % a 210–240°;
- una guarda de D_real per píxel i no per observació;
- manca de validació amb mostra reservada.

La V101 corregeix els tres primers:
- guarda de 2,75 px a cada observació;
- res a 140–205°;
- mitjana local zero imposada (d40).

Els guanys de veritat es revaliden en 4 subsectors reservats (r 0,88–0,96). Resultat: pendent 0,89–1,01 i nivell ≤ 0,46 %.

**Pendent:** injeccions cegues a través de la cadena i sensibilitat a la calibració.

**Límit físic a l'esquerra de la protuberància de dalt (PA 105–130°):**
- d 0–1 px és darrere la Lluna real a tots els fotogrames;
- d 1–2 px el veuen només 2 fotogrames, amb detall contaminat.
