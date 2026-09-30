# 170 · La banda sense dada del limbe: la Lluna real no és el cercle del model (V99)

25-09-2026, vespre · Claude, amb Codex Astra (pla i verificació) · Encàrrec de Pere: «arregla la banda sense dada de V98… amb el màxim detall i sense lupa ni artefactes; la solució de Brno és adequada».

## 1. El problema
A la V98 (doc. 169), la corona arran del limbe es fa amb una selecció física per fotograma. Cada fotograma hi entra amb un pes smoothstep(D, lo, hi), on D és la distància al limbe d'aquell fotograma **calculada des del cercle del model**. Les rampes eren amples (curts 6→9, mitjans 5→8, llargs 6→10 px) perquè el dèficit de vora mesurat era enorme i canviava molt d'un sector a l'altre (D7). A dalt i a l'esquerra, on la Lluna avança, els primers 5–6 px no tenien cap fotograma net: una tira llisa visible a 4:1.

## 2. La causa: sobretot geometria (la PSF, una part petita i comuna)
- **D16. El dèficit per angle de posició lunar** (respecte del centre del model de cada fotograma) és fort al llarg de l'eix horitzontal i quasi nul en vertical. Curts a 2 px:
  - tardans a PA 180: −57 %; a PA 90: −7 %;
  - primerencs a PA 0: −26 %; a PA 270: +1 %.
- **D17 i D18. On és el limbe real de cada fotograma.** Hi ha dos detectors independents:
  - el creuament de T = 0,70 contra la referència neta;
  - el màxim de dV/dD, sense referència. Només funciona amb mitjans i llargs, perquè els curts pesen zero dins de la Lluna.

  Tots dos difereixen ~0,85 px, amb una variació moderada per sector. **La forma és la mateixa a 28 s i a 85 s:** esquerra +3 a +4,5, dreta +1,5, dalt ≈ 0, baix −1,5 a −3 px respecte del cercle.
- **D19 i D21. La silueta comuna.** L'ordre 2 es valida per blocs de fotogrames; l'ordre 4 no millora la predicció (0,474 contra 0,473 px). Els coeficients (px):
  - c0: +0,49;
  - cos PA: −1,12 i sin PA: +0,79 (centre desplaçat cap a l'esquerra i amunt);
  - cos 2PA: +1,85 i sin 2PA: +0,44 (el·lipse allargada en horitzontal, ~0,8 %).

  La silueta feta només amb tardans difereix com a molt 0,28 px, i no hi ha deriva temporal fora dels sectors amb cromosfera. **Interpretació:** refracció diferencial amb el Sol baix (aixafa en vertical) més un desplaçament fix del model d'efemèrides. La Lluna de Pere (capa 258) ja la dibuixava així: fora del cercle a esquerra i dreta, translúcida a dalt i a baix.
- **El col·lapse.** Amb D_real = D_obs − e(PA_j), les corbes de ln T de tots els sectors i totes dues èpoques coincideixen.

  | | 2 px | 3 px | 4 px |
  |---|---|---|---|
  | Curts | −5…−16 % | −1…−8 % | 0…−4 % |
  | Mitjans i llargs | semblant | | |

  **Conseqüència:**
  - a dalt, les rampes de la V98 perdien ~2 px de dada neta;
  - a l'esquerra, s'hi posava dada de dins de la penombra de la Lluna real, amb dèficit. D'aquí venia probablement el vorell fosc residual de dalt-esquerra i baix-esquerra de la V98 (doc. 169 §6), que es va atribuir, sense èxit, a una «ombra de llum difusa».

## 3. La porta: sobre el que veuen els filtres, i amb exclusió
Primer, **què llegeixen els filtres:**
- NRGF, RHEF, WOW i MGN: el verd post-matriu G' = −0,18 R + 1,69 G − 0,51 B;
- ACHF isòtrops: la lluminància post-matriu L' = (R' + 2G' + B')/4;
- ACHF azimutals: el G' de la Vixen.

El blau té una cua de dèficit més llarga a dalt: −5 % a 4 px, per dispersió atmosfèrica vertical (D22). Tot i així, al G' el dèficit del blau compensa part del del verd. Per això la porta es fa en post-matriu (D23).

**Les dues exclusions (porta de Codex: ≤ 2 %):**
- **A la dreta (D21, D23).** La prova són tots els fotogrames primerencs, que és exactament la situació de la banda. La veritat són els tardans nets, i la silueta surt només dels tardans.
- **Inversa, a dalt i a l'esquerra (D25).** La prova són els tardans, amb la mateixa barreja d'exposicions. La veritat són els fotogrames de t < 70 s.

**Resultat amb la rampa comuna 4→6,5 px sobre D_real:** |biaix| ≤ 2 % en G' i en la lluminància efectiva (amb els factors RGB de l'a3c) a partir de 0,5 px de la vora del domini (D28, amb la regla de validesa de l'a3c). Al primer mig píxel arriba a −2,4 %.

La correcció fotomètrica C (dividir per T mesurada) **no** s'aplica. La dispersió entre sectors és de ±2 % a 3 px i de ±5 % a 2 px, i la variant de prova A (rampa 3→5,5 amb C) feia clots d'un sol calaix als ACHF isòtrops.

## 4. Troballa lateral: els fotogrames més curts no quadren (D26, D27)
Respecte de la barreja i lluny del limbe, els fotogrames de 1/3200 s (25) fan R −5,6 %, G −1,4 %, B −9,6 %; en post-matriu, G' +1,6 % i L' −3,5 %. A 1/2000 s passa semblant, i a partir de 1/500 s tot queda dins de ±1 %.

**No és l'obturador**, que donaria un efecte acromàtic. Depèn de la brillantor: el verd té un excés additiu als nivells febles (+44 % a la desena més fosca, −2 % a la més clara) i el vermell i el blau, un dèficit de guany. **La causa és una hipòtesi:** la selecció de pesos LDIC, que depèn del senyal, també hi podria contribuir (Codex).

**Conseqüència:** al primer píxel d'una rampa només hi entren els curts, i el primer mig píxel surt un 2–3 % més fosc en L' a qualsevol rampa. Més en general, arran del limbe, on les llargues saturen i manen les curtes, la corona surt una mica menys blava. **Es cura als RAW (calibratge de les exposicions curtes), Torre de Pisa.** Pendent.

## 5. Brno
Druckmüller, Rušin i Minarovjech (2006) fan servir, de cada fotograma, els píxels que la Lluna real no tapa. La V99 (limbe real mesurat i guarda física) n'és la versió fidel. Codex hi afegeix que Brno també limita l'amplificació pel soroll i fixa una imatge de referència per a la presentació.

La presentació C2∩C3 no recupera dada absent. Només canvia la dreta, i no encaixa amb mantenir intacta la Lluna de Pere.

## 6. Resultat (V99, `4-RESULTATS/v99_banda_20260925/RESULTAT.md`)
- **Banda:** a dalt, de 5,0–5,7 px a 3,4–4,2 px; a baix-esquerra, de 4,3–6,1 px a 1,5–5,5 px. A l'esquerra passa de 5,9–6,3 px a 6,2–7,4 px (més honesta, i sota la Lluna de Pere).
- **Anells, sobre exactament els mateixos píxels (J14C):**
  - milloren als ACHF azimutals (47: −0,159 → −0,135; 48: −0,133 → −0,105) i a la NRGF i la RHEF;
  - els ACHF isòtrops (50–53) empitjoren al primer calaix comú de dalt (50: −0,121 → −0,160). És l'efecte de vora de l'operador al primer píxel de dada (±0,1–0,14), que s'ha mogut amb el domini. Al compost només hi és visible la 51.
- **Porta sobre el producte efectiu (D28):** ≤ 2 % a partir de 0,5 px dins de la vora; −2,4 % al primer mig píxel, dins de la fosa dels filtres.
- **Lluny del limbe només canvien les WOW:** fins a ~1 200 px, amb p99 ≤ 0,7 %. És la resposta dels seus nuclis grans al canvi real de la dada arran del limbe.
- **Transferència** (injecció d'una modulació de ±3 % al llarg de l'arc, t1/t2): a λ = 8 px passa gairebé íntegra fins a la vora (WOW 0,85–1,06; MGN 0,98–1,06; ACHF 51 0,93–0,96). A λ = 24 px s'atenua a la vora (WOW bilateral fins a 0,22), semblant a la V98 (0,33). No hi ha indici de lupa a escala fina, però la transferència no supera la porta de Codex (0,90–1,10).
- **Transferència completa (t3/t4):** amb les dues freqüències als mateixos píxels i la radial, la V99 respon com la V98 a la seva vora. Cap capa no amplifica el gra fi. La WOW bilateral i els ACHF ocults atenuen l'estructura prop de qualsevol vora, a totes dues versions.
- **Compost natiu (r6):** a 4–5 px, la textura és nova i amb la mateixa energia que més enfora; les diferències de nivell són ≤ 1,7 %.
- **Codex (tancament): PARCIAL.** Candidata revisable. Per fer-la vigent cal que Pere accepti explícitament els efectes de vora dels operadors (els mateixos que a la V98).
- **Lupa:** WOW, MGN i WOW bilateral sense canvi.
- **Vistes natives:** la tira de dalt passa de ~6 a ~4 px, sense cap artefacte nou.

## 7. Trampes per a la skill
- **Distància al limbe = distància al limbe REAL.** El cercle del model ho és a ±2–4 px. Qualsevol llindar sobre D_obs amaga error de geometria i es paga amb rampes amples.
- **Un dèficit que canvia per sector** no demostra que calibrar sigui inventar. Primer cal provar si col·lapsa amb una geometria millor.
- **La porta es fa sobre el senyal que llegeix l'operador** (post-matriu), no sobre el verd cru.
- **Si tots els fotogrames d'un píxel veuen el limbe a la mateixa distància**, una rampa no rebaixa el biaix: només compta el del resultat (Codex).
- **Llançar una cadena «des del pas N» executa també tots els passos següents** (`pas()` compara DES ≤ N).
