# V90: les línies paral·leles al limbe, i com es van curar (23-09-2026, tarda i vespre)

**Evidència:**
- diagnosi: `4-RESULTATS/v88_marques_pere_20260923/DIAGNOSI.md` (amb dues rectificacions);
- proves: `4-RESULTATS/v89_proves_20260923/PROVES.md`, `4-RESULTATS/v89_claredat_20260923/RESULTAT.md` i `4-RESULTATS/v90_20260923/` (RESULTAT i `descartat_intent1_A_B`);
- producte: `1-PHOTOSHOP/V90.psb`.

**Símptoma:** marques de Pere a la vora esquerra de la Lluna (104–229°): línies fines paral·leles al limbe a 2–7 px (fosques i clares), grans foscos i un arc clar. «No en sé trobar una sola capa com a causa.»

## Què era i què no
- **No és cap capa sola.** La línia hi és a TOTS els filtres alhora: la fosa a4 és la mateixa per als 16 i tots dibuixen el mateix detall radial fals.
- **Les capes d'ajust la poden fer créixer.** Per saber-ho, amaga-les en una còpia i fes-la renderitzar per Photoshop. La claredat («Claridad y borrar neblina») hi feia un halo i les feia més visibles, però no n'era la causa: sense la claredat, Pere hi continuava veient les línies.
- **⛔ Hipòtesi refutada: que la matriu càmera → Adobe RGB «foradi» el verd de l'Hα.**
  - Mesura: l'excés de color de la protuberància té G/R ≈ −0,02, és a dir, l'Hα gairebé no toca el verd matricial.
  - Y/G_m és alt (1,4–2,8) perquè l'Hα és vermella, no perquè el verd baixi.
  - Es va explicar a Pere abans de mesurar-ho i s'ha hagut de rectificar. **Mesura abans d'explicar.**
- **⛔ L'alfa de la Lluna de Pere no és un error.** És ampla a l'esquerra (la Lluna sumada al llarg del temps), però quadra amb la línia vermella de la cromosfera de les seves fotos (+2..+3,5 px). Una alfa «de l'instant» hi obria una franja clara (prova A, pitjor). Confirma «no tocar mai el limbe».
- **⛔ Qualsevol unió arran del limbe fa una línia on es troba amb la dada:**
  - la continuació plana de la V88 (bandes de Mach a DMIN i DMIN+4);
  - l'entrada continuada des de la cresta de la pujada (a3c);
  - la continuació amb valor i pendent continus (a4_c1);
  - una vora nítida nova de la Lluna.

  Totes es van provar: les línies hi continuaven o se n'hi feien de noves.

## La cura (V90)
**Menys resolució RADIAL dels filtres prop del limbe**, com fa Brno, on els filtres no pesen arran del limbe.
- **El suavitzat:** gaussià només al llarg del radi, σ_r = 4 px fins a 4 px del limbe, que s'apaga a 14 px (smoothstep).
- **Com s'aplica:** en polars (0,05° × 0,25 px) i com a **diferència**: tornada del suavitzat menys tornada sense suavitzar. Així, més enllà de 14 px el ràster és bit a bit el d'abans.
- **Què es conserva:** els raigs (estructura azimutal real). Les línies paral·leles al limbe (detall radial fals) desapareixen.
- **Què no es toca:** ni la Lluna, ni les màscares, ni cap capa de Pere. Proves P2 = 0, P3 i P4 (canvis a d ≤ 13,94 px).
- **Codi:** `3-RECERCA/tools/v90_20260923/a5_radial.py`.

## Trampes de mesura
- **L'«energia de curvatura»** (derivada segona radial) a la zona de la vora la domina el mateix salt de la Lluna: no va veure la millora del suavitzat radial. **Jutja amb vistes a 4:1 a les marques**, primer emulades i després natives de Photoshop.
- **Proves amb Photoshop:**
  - munta còpies (stage PSB), obre-les, exporta la caixa i tanca-les sense desar;
  - **no obris res mentre Pere té documents sense desar sense preguntar-li-ho** (el risc de memòria i el d'interrompre la seva feina són seus).
- **Màscara per lluminositat:** una màscara feta amb una selecció per lluminositat d'una foto curta (la 262 de Pere, 14/255 a tot el camp) aplica un 5 % de la capa a tot el camp i en marca el rectangle. La cura és Nivells a la màscara (negre a ~20).

## V91 (23-09-2026, nit): la cura, NOMÉS on hi ha el defecte
- **Símptoma:** marques roses de Pere a la V90, una «lent», un efecte lupa a la corona interior, a dalt, a la dreta i a baix (0–32°, 45–98° i 230,5–305°).
- **Causa:** el mateix suavitzat radial, aplicat a TOT el voltant. On no hi havia línies no treia res de fals: estirava radialment la textura real dels primers 14 px.
- **Cura:** el suavitzat només on hi havia les línies (marques de Pere a la V88: 104–229°): S(θ) = 4 px × smoothstep(θ, 99, 104) × (1 − smoothstep(θ, 228, 232)). Fora, els ràsters de la V88 bit a bit.
  - Codi: `3-RECERCA/tools/v91_20260923/a5c_radial_on_hi_havia_linies.py`.
  - Producte: `1-PHOTOSHOP/V91.psb`.
- **⛔ Criteris que no van servir:**
  - **L'alçada del limbe lunar sobre el solar** (`a5b`): encara suavitzava a 230–258°, i la lent hi quedava.
  - **L'índex d'estructura paral·lela al limbe** (`a6`): no discrimina, perquè el salt de la Lluna domina el detall radial dels primers píxels a tots els azimuts.

  Quan la mesura no discrimina, **el jutge són les marques de Pere** dels dos defectes: on hi havia línies i on hi ha lent.
- **Regla:** tota cura local s'aplica **només on hi ha el defecte**. Fora d'aquí, la mateixa operació és un defecte nou. Comprova-ho a 4:1 al compost natiu, a les marques del defecte **i també a les del costat**.
- **Pere desa mentre treballes:** la V90 va canviar a les 22:06, entre el muntatge i el desament natiu, i el primer desament de la V91 no portava la seva màscara nova de la 56.
  - **Abans de desar amb Photoshop,** torna a comprovar el SHA de la font.
  - **Si ha canviat,** compara tots els registres de capa (tagged blocks, canals i propietats) per saber què és seu, i torna a muntar a partir de l'última.
- **Capes que depenen de les de sota** (com les guspires, amb un guany relatiu al compost local): si la font canvia, recalcula-les i compara. A la V91 la diferència va ser de 32 DN16 i no calia refer-les.

## V92 (24-09-2026, matinada): la lent que quedava era la continuació de la vora, i els grisos, el color
- **Símptoma:** Pere, sobre la V91: «encara veig una mica d'efecte lent», on eren les marques roses de la V90, més subtil. També «artefactes grisos» a la protuberància esquerra, a la capa de guspires.
- **La mesura bona de la lent:** l'índex d'estirament radial de la textura, E_d/E_s a 16–30 px dividit pel mateix arran del limbe. S'ha de fer amb **pas alt només en azimut**, perquè el salt de la Lluna i el perfil radial no canvien amb l'azimut i així no el confonen. Dona 1 si la vora és com la corona del costat; per sobre d'1 és lent.
  - Mesura-ho per capa i per distància, i amagant els filtres d'un en un al compost emulat, per saber d'on ve.
  - Codi: `3-RECERCA/tools/v91_lent_residual_20260923/`.
- **Causa:** la continuació radial d'a4 (V88). Als ~4–6 px sense dada plena tocant la Lluna, copiava el valor de r_ref al llarg del radi, a tots els filtres. La textura hi queda estirada: és una lent. La 56 WOW bilateral la porta més perquè té més opacitat.
- **⛔ Regla:** cap continuació a la vora de la Lluna no ha de copiar valors al llarg del radi. Tampoc no ha de fer pull-push ni Laplace sobre la textura.
- **Cura:** mirall de la textura a través de r_ref; el nivell es continua al llarg de l'arc (gaussiana d'azimut, només dada), i així el nivell mitjà no canvia (< 0,0001).
  - Codi: `3-RECERCA/tools/v92_20260924/a4m_continuacio_mirall.py`.
  - Resultat: l'estirament a 1–5 px passa de 4,8 a 1,3 al compost natiu.
- **No va servir:** el mirall a l'entrada de la WOW (continua_ln). Hi queda un estirament suau a 5–14 px a baix, que ja era a la V88 i pot ser real; no s'ha tocat.
- **Els grisos:** una capa que SUMA llum (Sobreexposició lineal) ha de portar el color de l'**excés** real sobre el seu fons (foto − obertura del mateix canal), no el color mitjà de l'objecte.
  - El rosa del cos de la protuberància (G/R 0,64) destenyia la corona taronja cap al gris.
  - L'excés de les guspires a la 76 és G/R 0,26 i B/R 0,37.
  - Abans de filtrar taques com a soroll, comprova-ho amb histèresi (llavor a kσ): aquí eren estructures reals de 12 i 124 σ.
- **Pere retoca mentre treballes:** va desar la V91 a les 00:14 i a les 00:23. Munta sempre des de l'última, compara-la capa per capa i conserva els seus retocs byte a byte (aquí, l'alfa de la 267).

## V93 (24-09-2026, nit): ni còpia ni mirall, només nivell; les línies es treuen per coherència; ordre de la pila
- **⛔ Al buit sense dada tocant la Lluna no hi va textura inventada.**
  - Copiada al llarg del radi (a4 de la V88) fa una **lent**.
  - En mirall (a4m de la V92), Pere hi veu el **mirall**: «la línia actua com a mirall, un vertical mirror flip along the line».
  - **Cura (a4v):** només el nivell mitjà al llarg de l'arc. La dada entra on entrava (VORA 2). Amb VORA 1 la vora dreta s'enfosquia un 1,6 %.
- **⛔ Les línies paral·leles al limbe no es treuen suavitzant al llarg del radi:** el suavitzat també s'enduu la textura. Pere ho descriu com «queda el color però no la textura».
  - **Cura (a5d):** detall radial fi (ràster − gaussiana radial σ 4 px), i la seva part coherent al llarg de l'arc (gaussiana d'azimut de 6 px d'arc). Se'n resta només la part coherent.
  - Amb arcs de 12 i 24 px en queda un rastre a 8:1; les mètriques globals no ho veuen. **Jutja a 8:1.**
- **⛔ Mira l'ordre de la pila:** la 76, la 96 i la 224 són a SOBRE de l'Earthshine (258). Les seves restes de màscara dins la Lluna s'hi pinten (fins a un 1 %).
  - **Neteja:** màscares a 0 només on la 258 és opaca i a més de 8 px dins del limbe. Mai a la franja del limbe.
- **Línies fosques rectes al camp exterior:** són unions de camp de la Sony (vores d'apuntament o de fotograma, −0,1 % a la base lineal), que la WOW amplifica per més de cent.
  - **Diagnosi:** perfil perpendicular al traç (compost, sense filtres, cada ràster, base_G, pesos A/B de la Sony) i renders natius d'una còpia clonada amb variants de visibilitat.
  - **Cura a la torre de Pisa:** refer l'apilat de la Sony amb vores amb rampa. No es fa sense Pere.

## V94 (24-09-2026, migdia): la WOW, sobre la dada i neutra
- **«Ombra quadrada» que no és al ràster:** mira el nivell mitjà del filtre en Superposició. La WOW de la V86–V93 tenia de mitjana 0,39–0,47 i enfosquia dins de la màscara de Pere (un quadrat arrodonit), així que la vora de la màscara dibuixava l'ombra.
  - **Cura:** detall de nivell neutre: escales ≤ 128 px i sense el residu gruixut.
  - **Comprovació:** l'efecte de nivell de la capa (compost amb la capa ÷ compost amb la capa a 0,5 − 1, suavitzat) ha de ser ≈ 0.
- **«No hi ha textura a 1–9 px del limbe»:** el filtre es calculava sobre l'interior de la Lluna omplert, i el farcit llis hi aixafava la potència local.
  - **Cura** (`3-RECERCA/tools/v94_20260924/wow_domini.py`): convolució normalitzada NOMÉS al domini. A la vora s'ajusta un pla local (ordre 1), perquè una mitjana d'un sol costat té biaix quan hi ha pendent. On no hi ha dada, alfa 0.
  - ~~**El biaix de curvatura que en queda:** es resta el component coherent al llarg de l'arc de la mateixa sortida.~~ ⛔ **Rectificat a la V95:** aquesta resta posterior feia arcs i anells a la vora de la seva fosa (marques liles i verdes de Pere a WOW.psb).
  - **L'alfa:** es fon en 1,5 px sobre la vora contínua de la dada, no sobre el graó dels píxels.

## V95 (24-09-2026, tarda): el WOW a l'arrel, sense cap correcció posterior
- **Símptoma:** marques de Pere a `1-PHOTOSHOP/WOW.psb`, sobre les dues WOW de la V94.
  - Lila: arcs a 86–126 px (352° i 282°).
  - Verd: arcs a 5–95 px.
  - Vermell: la vora de 1,5–6,4 px, llisa o fosca.
- **Causa:** amb el suport incomplet, una escala gruixuda només es queda amb els tocs que van al llarg de l'arc. Per la curvatura de la Lluna, aquests tocs cauen més lluny del Sol, on la corona és més fosca, i l'escala surt clara on s'engega: l'escala 6, a 80–120 px, +0,02. La V94 ho restava a posteriori i hi deixava els arcs.
  - **Com es troba:** la contribució de cada escala al nivell, per distància i per sector.
- **Cura** (`3-RECERCA/tools/v95_20260924/wow_v95.py`). Lluny de les vores, l'operador és l'original: k igual i correlació 1,00 al detall fi.
  1. **Parells simètrics:** un toc compta només si el seu simètric té dada.
  2. **Vora difuminada de la Lluna:** a d < 12 px, comptats des de la CRESTA de ln G de cada azimut, només compten els parells a la mateixa distància del limbe. Amb la zona fixa tornaven les línies de la V88 a l'esquerra, on la cresta és a 5–7 px.
  3. **Escales ≥ 3:** entren només amb una completesa de 0,95–0,995.
  4. **Nivell per escala dins l'operador:** constant global per escala, més la mitjana local (σ = min(150, max(32, 4·2^s))) × la participació radial de l'escala (la fracció del pes en parells que veuen el perfil radial, sense el toc central). El biaix de nivell és la curvatura del perfil radial; a la zona de vora, on només hi ha parells al llarg de l'arc, no hi és i no es toca. Si no es pondera, la finestra d'un sol costat mou la vora. Amb σ > 150 a les escales 6–7 queda un anell fosc ample (150–500 px), que una màscara de Pere dibuixaria com a ombra.
  4b. **Tolerància «mateixa distància»:** 0,5–1,5 px a la bilateral i 0,25–0,75 px a la lineal (P04), que sense pes de rang fa un anell clar a la cresta.
  5. **Potència local:** la de l'original (nconv).
- **⛔ No simetritzis el pes de rang de la bilateral** (fer-ne la mitjana dels dos tocs d'un parell): treu el biaix del pendent, però canvia el caràcter de la P05 a TOT el llenç (grumollós, correlació 0,85–0,96). Pere l'estima tal com és.
- **⛔ No restis l'anell coherent del ràster a posteriori:** s'endú la textura (1–6 px, del 0,79 al 0,64).
- **Jutge:**
  - làmines a 4:1 a les marques, amb el ràster × alfa sobre gris i contrast ×4;
  - vista de NIVELL (pas baix σ 6 px, ×8) de tot l'entorn de la Lluna;
  - índex de lent (V92);
  - detall coherent paral·lel al limbe per distància, a l'esquerra contra la dreta.
- **⛔ El compost fusionat d'un desament natiu pot sortir malmès** tot i que les capes siguin bones (V95 de les 16:43: mitjana 51.182 en lloc de 10.396, alfa aleatòria). La porta del Photoshop (OBRE) no ho veu, perquè el Photoshop recompon. **Porta p6:** compara el compost desat (Image Data) amb la vista del llenç que el Photoshop ha renderitzat (`3-RECERCA/tools/v95_20260924/p6_compost_fusionat.py`).
- **Quocient de composts:** suavitza'l NOMÉS amb els píxels que tenen imatge. Les zones negres del llenç el falsegen (fins a un −73 % inexistent a les cantonades).

## V96 (24-09-2026, vespre): NRGF, els anells parcials del Sol
- **Símptoma:** una franja clara entre el limbe i un cercle centrat al SOL a r = r_in (469 px). A dalt i a baix cau a d ≈ 16, i a la dreta a d ≈ 2. Els filtres per anells (NRGF i RHEF) la tenen tots dos.
- **Causa:** la Lluna està desplaçada 14 px respecte del Sol. Sota r_in, la Lluna tapa part de cada anell, i l'estadística de l'arc visible està esbiaixada. `radial_v36` completava només els anells exteriors (`inner = []`).
- **Cura:** `complete_from_partial` també per als anells interiors, amb el patró de r_in…r_in+40. Lluny de la Lluna no canvia res. Codi: `3-RECERCA/tools/v96_nrgf_20260924/w1_nrgf_v96.py`.
- **Trampa de mesura:** el cercle és centrat al Sol, no a la Lluna. Ajusta cercles a les marques de Pere per saber de quin centre són.
- **Capes en Multiplicar:** transparent NO és neutre, perquè no enfosqueix. El buit sense dada dona una línia clara. Pere ha decidit: només el nivell en els píxels sense dada.
- **⛔ Desament natiu:** desant el document (`'Cpy ' false`), el compost fusionat va sortir malmès 4 vegades, fins i tot amb el Photoshop buit. **Desa com a còpia** (`'Cpy ' true`) i passa la porta p6 sempre.
