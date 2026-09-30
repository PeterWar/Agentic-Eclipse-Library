# V86: forats sota PixInsight, franja d'un sol instant i cantonada que es regenera

Lliçons comprovades el 23-09-2026 (nit). Evidència de projecte:
- `4-RESULTATS/v86_neta_20260923/` (rebuts `A1…A10`, `RESULTAT.md`, intents descartats amb el seu LLEGEIX-ME);
- codi a `3-RECERCA/tools/v86_neta_20260923/`.

Producte: `1-PHOTOSHOP/V86.psb`. Continuació (V88, 23-09 tarda): `v88_cremallera_soroll_franja_i_earthshine.md` (soroll de la franja, vora suau, earthshine). Una prova que passa no és absència global d'artefactes: la mirada de Pere mana.

## On acaba la imatge
Per a Pere, la «imatge final» és la pila de capes **per sota de la capa de PixInsight**, i PixInsight es deixa oculta. Tot defecte es busca i es cura en aquesta pila.
- Una capa rasteritzada de dalt (PixInsight, plaques) no pot sostenir res.
- **La cantonada del logo** vivia dins de PixInsight a la V79. Quan la V85 va retallar aquella capa, es va perdre (negra).

## Forats: mesura la cobertura, no el compost
- **Com es mesura:** cobertura = 1 − Π(1 − α · màscara · opacitat) de les capes visibles per sota de PixInsight, a resolució plena a la Lluna. Amb totes les capes visibles, el compost pot semblar ple i amagar el forat.
- **D'on venia:** una Lluna de presentació amb vora suau (≈2 px, fins a ≈12 px a la protuberància) i unes màscares posades a negre a tota la silueta (filtres de la V84 i base de la V85). Això deixa un anell mig transparent (r 451–465, mínim del 9 %).
- **La cura:** màscara de l'usuari × (1 − Lluna opaca), amb la Lluna opaca = alfa efectiva ≥ 0,999. A la zona lunar es continua cap endins el valor que la màscara de l'usuari té just a fora. Mai es tanca una màscara a tota la silueta.

## La franja escombrada per la Lluna: dada d'un sol instant
La Lluna es va moure 28,5 px; la franja on el limbe va passar barreja fotogrames i fa arcs (research/165). Dues sortides que semblen netes als ràsters es veuen malament al compost:
- **Interpolar la franja als filtres:** deixa un **anell llis de 20–50 px sense detall**, que és un altre forat, ara de detall.
- **Aplanar els arcs al llarg del raig:** escampa el perfil del limbe i fa un anell clar amb perles.

El que funciona és la **suma dels primers fotogrames**, que tenen el limbe on és la Lluna de presentació (t ≤ 22,3 s; la Lluna de Pere és de t ≈ 18,4 s):
- **Per fotograma:** només els píxels a ≥ 1 px del seu limbe **observat** (vegeu ⛔ més avall). Els pesos no són exactament 0 dins la Lluna, i sense aquesta condició hi entra soroll lunar.
- **Rampa de pes arran del limbe de cada fotograma:** smoothstep 1→3 px als curts i 2→6 px als llargs. (La condició de pes efectiu mínim d'1,5 fotogrames curts de la V86 no feia res: la referència sortia 0. Corregit a la V88.)
  - **Per què:** els llargs (81 % del pes) són més foscos arran del limbe als costats. A la dreta, per la vora més difuminada: a 1,5 px, −35..−63 % contra −4..−24 % als curts. A l'esquerra, a més, la Lluna hi va tapant la cromosfera, un dèficit **real**, perquè el limbe lunar hi és just sobre el solar. A dalt i a baix no n'hi ha.
  - **Sense la rampa:** línia fosca a dalt-esquerra i baix-esquerra.
  - **Abans de triar-la:** mesura el dèficit per azimut i per fotograma (valor a D ≈ 1,5/2,5/3,5 contra D ≈ 7–9).
- **Almenys 8 dels 11 fotogrames per píxel**, comptats al verd. Amb 3, la fila de vora amb 2–4 fotogrames fa una costura en ziga-zaga a ~5 px del limbe.
- **Buits del mosaic CFA:** s'omplen per convolució normalitzada (σ 0,8 px) per canal, *abans* de la matriu. Si el mínim de fotogrames s'aplica per canal, el R i el B es trenquen.
- **Validesa pel G:** el blau matricial dels curts pot sortir ≤ 0.
- **Nivell:** un factor **constant** per canal, la mediana de fusió/primerencs a 12–45 px. No es fa per distància (vegeu ⛔ més avall). S'usa només fins a 45 px, perquè més enllà el terra de la suma esbiaixa els curts.
- **Trampa de codi:** una assignació `validE = …` posterior va anul·lar la condició de fotogrames. Cal encadenar les condicions amb `&=`.

**⛔ La distància «al limbe» del rebut de la cadena no és la del limbe observat.** `limb_frames/distance_model.npy` mesura des del radi de l'**efemèride** (455,5 px). El limbe que es veu als fotogrames (màxim gradient dels primerencs) i la Lluna de Pere són a R ≈ 453,0: 2,5 px més endins.
- **Què passa si no ho corregeixes:** amb D_model ≥ 1 es perden ~3 px de corona real arran del limbe. Els filtres hi posen una continuació i al compost queda una **tira llisa i clara de 4–6 px** a dalt, a baix i a la dreta, visible a 2:1. Va passar a la primera V86 lliurada del 23-09, retirada abans que la veiés Pere.
- **Com es fa:** D_obs = D_model + (R_model − R_Lluna), i la validesa és D_obs ≥ 1.
- **Abans de fer servir qualsevol distància al limbe,** comprova on és el màxim gradient de les dades per sectors.

**⛔ Arran del limbe, la fusió porta una vora clara artificial.** Amb el nivell igualat lluny del limbe, a 1 px la fusió és un 27 % més clara que els primerencs (mediana a tot el voltant) i fins a un 47 % a dalt, on els primerencs no tenen cap dèficit. La hipòtesi és que la correcció de vora de la cadena es calcula amb el radi de l'efemèride. Probablement és la vora clara de la V84 i de la V85.
- **Conseqüència:** qualsevol correcció de nivell «per distància al limbe» ajustada a la fusió (c(d) = mediana fusió/primerencs) **importa la vora als filtres** (+9 % a 1 px, +4 % a 5 px).
- **Com es fa:** un factor constant per canal, mesurat on la fusió és neta (12–45 px).

## Continuació als píxels sense cap dada
Amb el limbe observat i la rampa, només ≈1–2 px arran del limbe no tenen dada neta de cap instant. Allà els filtres es continuen (pull-push i relaxació de Laplace dels valors de pantalla):
- **Des d'on:** la continuació parteix de **2 px dins de la dada**. A la vora del domini, els filtres responen d'un sol costat i hi arriba el dèficit residual. Ho vaig triar amb el compost emulat:
  - amb 0–1 px, línia fosca;
  - amb 3 px, torna una tira llisa a dalt i a baix.
- **Com es comprova:** a 2:1 i amb la prova P6 (textura a 2–4 px ≥ 0,5 de la de 8–15 px, en els sectors on la Lluna no tapa).
- **Què queda:** una vora lleugerament clara, de +4–11 % a 1–6 px, per la resposta de vora de l'ACHF micro. La V84 hi tenia fins a +27 %.

## Com es jutja
- **Mira el compost natiu de Photoshop:** l'anell llis de l'intent 1 només era evident al compost.
  - vistes 1:1 del limbe a 6 azimuts;
  - perfil radial de la lluminància del compost **per sectors**, només on la Lluna no tapa (alfa < 0,05); una mitjana global amaga una tira o una vora d'un sol costat;
  - **la textura per distància al limbe** (|L − gauss σ1,5|): una tira llisa hi surt com una caiguda de 10–50 vegades;
  - rugositat del perfil de cada filtre a r 440–560 contra V84 i V85.
- **Dues trampes de la comparació:**
  - un filtre que a la versió anterior era tapat o constant a la zona surt «més rugós» sense ser pitjor;
  - cal separar la rugositat que cau sota la Lluna opaca.

## Torre de Pisa a la pràctica
- **Cada canvi, en una capa nova.** Si cal canviar la màscara d'una capa de l'usuari, se'n fa una còpia nova (225 → «Correccions V77 · només la Lluna») i l'original queda oculta.
- **Comprovació:** les capes de l'usuari s'han de verificar byte a byte (P2).
- **Filtres des de zero:** `v86_operadors.py` reprodueix la V58 amb correlació 1,000. La condició de contorn nova (perfil ln, residu pull-push i Laplace) treu la franja fosca que l'ACHF tenia a la vora exterior dels camps.

## Cantonada que es regenera i Photoshop des del terminal
- **La capa:** «Cantonada del logo · es regenera», entre les estrelles i els ajustos. Fa servir la recepta de la V79 (polinomi 2D del cel més gra reflectit a la hipotenusa), calculada sobre el compost de les capes de sota.
- **`regenera_cantonada.jsx`, pas a pas:**
  1. amaga la capa i les de sobre;
  2. `doc.duplicate(…, true)` i retalla la caixa;
  3. desa un TIFF i crida `a5_cantonada.py` amb `app.system()`, detectant el Python;
  4. obre un TIFF RGBA amb alfa no associada (tifffile `extrasamples=[2]` + ICC), que arriba com a transparència;
  5. substitueix la capa en **un sol pas d'historial** (`suspendHistory` amb una funció *global*).
- **Prova:** la cantonada que fa Photoshop és igual a la de la construcció, amb 3·10⁻⁶ de diferència mitjana.
- **Des del terminal:** `do javascript "$.evalFile(new File('…'))"`. `do javascript (POSIX file … as alias)` dona l'error 8800.
- **Desament natiu:** un PSB es desa amb ActionDescriptor `largeDocumentFormat` + `maximizeCompatibility`. Després, `porta_photoshop.sh` amb la **ruta absoluta**: amb una de relativa, respon «REFUSA: Se esperaba una referencia a un archivo…».
- **⛔ Memòria cau de canals per nom:** si un muntador guarda els canals codificats amb el nom de la capa (`F_<filtre>.bin`), un segon muntatge reutilitza els filtres vells sense avisar. El nom ha de portar l'empremta del contingut (`a7_munta_psb.py`, des del 23-09).
