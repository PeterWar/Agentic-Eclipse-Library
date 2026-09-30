# Geometria dels arcs: circularitat i centre solar

06–07-09-2026 · comprovació autoritzada per Pere · V31 preservada.

**Veredicte sobre els arcs visibles de les capes 01/02: INDETERMINAT.** Hi ha una preferència d'orientació tangencial mesurable, però les dades i els estimadors provats no determinen una família de cercles perfectes ni un centre estable. Sí que s'identifica una component circular centrada al Sol dins del delta H1 de 01: és coherent amb la definició radial d'aquella operació, no una prova de la forma de tota la corona o de tots els arcs observats.

La investigació respon la hipòtesi geomètrica. No corregeix cap píxel, no afegeix màscares i no produeix un PSB nou. L'estudi s'acota a 2,5–4,5 R☉ de les capes 01/02 que Pere havia identificat com a problemàtiques. No és un traçat manual de cadascuna de les marques ni permet extrapolar a altres radis, capes o fotografies.

## Què s'ha mesurat

La referència solar és `(5361,768112;3775,747534)` a la graella de 10551×7506, radi 440,603049 px. El centre lunar de C2 és `(5361,877320;3774,741218)`. La separació nominal és **1,012225px**. La dispersió 0,9–1,1 px dels punts amb què es va ajustar el limbe lunar no és una incertesa del centre; no es disposa aquí d'una covariància o d'un error sistemàtic que permeti discriminar amb confiança Sol i Lluna a aquesta separació.

Fonts de geometria: [direct_grid_receipt.json](</Users/USUARI/Downloads/Eclipse 2026/research/tools/v29/cau_final/direct_grid_receipt.json>) i [limbe_v23.json](</Users/USUARI/Downloads/Eclipse 2026/research/tools/capes_totals_v14/cau_v21/limbe_v23.json>). No s'ha reutilitzat el centre antic amb la convenció de mig píxel anterior a V29.

Les fonts principals són `research/tools/v31/cau/01_final_u16.npy` i `02_final_u16.npy`, verificades contra les capes de V31 en el seu lliurament i preservades a V31_FiltresPurs. Són sortides processades, amb contrast i H1 heretats; no radiància RAW. També s'analitza `achf_smoothed.npy` abans d'H1, i els deltes `u16/65535−0,5−smoothed` de 01/02 a `v29/cau_final`. Aquests deltes inclouen quantització/retall i precedeixen el suavitzat addicional σ3 de V31: no se'n presenta la magnitud com la contribució exacta al PSB actual.

## Primera prova: una forma radial que ha de predir dades reservades

En lloc de buscar sempre sobre cercles solars, s'ha ajustat als mateixos píxels cartesians un model forward:

`D(p) ≈ s(t)`, amb `t²=(p−c)ᵀ exp([[e1,e2],[e2,−e1]]) (p−c)`.

`s` és un perfil continu amb nusos cada 2 px. El centre `c` és lliure dins de ±128px en cada eix; `e1/e2` són lliures dins de ±0,06. El determinant unitari elimina la degeneració entre escala radial i mida de l'el·lipse. El cercle és el cas `e1=e2=0`; els radis dels possibles arcs no es fixen per endavant. Es comparen centre solar fix, cercle lliure i el·lipse lliure.

La geometria i el perfil s'ajusten només en sectors d'entrenament. Després es prediuen altres píxels, sense reajustar-ne l'amplitud, la fase o els pics. Es repeteix intercanviant els sectors. La cerca usa múltiples centres i formes inicials; a l'el·lipse es proven 729 combinacions de graella i s'optimitzen les millors de 24 centres diferents, més la millor solució circular. Això millora la recuperació del control el·líptic, però no és una prova d'òptim global.

Per separar escales s'usen dos filtres **només de diagnosi**, cartesians i fixos: Gaussian2−Gaussian16 i Gaussian8−Gaussian64, truncament 3σ. No són bandes Fourier ideals ni proves de preservació fotomètrica. Els cercles sintètics passen la mateixa cadena. Es mostregen coordenades enteres originals cada 4 px; no es reescala el producte.

La mostra final fina usa 12 sectors de 30° amb marges de 9°; l'ampla, 8 sectors de 45° amb marges de 15°. La distància mínima entre mostres d'entrenament i reservades supera el diàmetre diagonal del suport del filtre de diagnosi. La validesa dels veïnats quadrats es comprova amb distància chessboard. Això elimina la compartició de píxels a través d'aquests filtres addicionals; no converteix en independents físicament la corona ni les operacions radials heretades de V31.

**Resultat real:** el centre solar fix només explica aproximadament −0,5% a +0,5% de l'energia de les dades reservades de 01/02 en aquests dominis. Valors negatius volen dir que predir zero és millor per aquest criteri; no que la corona sigui negativa. Els centres lliures canvien molt entre particions, sovint arriben al límit de cerca i no donen una millora predictiva estable. No es poden interpretar com centres físics desplaçats.

Hi ha, a més, una fallada de qualificació explícita: quan un centre es desplaça, alguns radis reservats poden caure en nusos gairebé sense observacions d'entrenament. En un cercle ajustat a02, un coeficient arriba a 51,1 amb suport quadràtic només 1,21·10⁻⁶; el nus adjacent no té suport. El seu error reservat extrem **no és evidència contra els cercles**. S'han auditat tots els perfils, inclosos els controls; les prediccions amb suport insuficient es marquen al rebut. No s'han eliminat selectivament píxels de validació per fer passar cap geometria. Dels 72 ajustos, 27 tenen almenys una predicció amb suport insuficient; en els altres 45 no es detecten nusos febles amb aquest llindar. L’etiqueta `FULL_PREDICTION_SUPPORT` només comprova suport diagonal per nus: no certifica el rang ni el condicionament conjunt. Per reparar l'estimador amb extrapolació o regularització diferent caldria repetir-ne la qualificació.

La interpretació és acotada: no hem identificat un perfil radial signat compartit que permeti mesurar establement el centre de les capes reals. Això no exclou arcs circulars locals que només siguin visibles en alguns sectors o tinguin amplitud/polaritat variable.

## Segona prova: orientació dels arcs locals

Una família d'arcs pot tenir radis diferents segons sector i fallar la plantilla global. Per això s'han mesurat les orientacions locals a partir de la Hessiana cartesiana, amb σ3 px; no s’exigeix localitzar un extrem de cresta. Els punts es trien per anisotropia >0,6 i curvatura superior a la mediana d'entrenament, **sense seleccionar-los segons si apunten al Sol**.

Aquesta prova usa 24 sectors de 15°, amb marges de 2°. La puntuació és la mitjana ponderada de `cos(2·angle(normal, direcció radial))`: +1 correspon a crestes perfectament tangencials, −1 a crestes radials, i una distribució sense preferència dona aproximadament 0. No és un coeficient de correlació de brillantor ni un percentatge de píxels circulars.

| Font | Puntuació reservada respecte del centre solar, dues particions | Sectors amb signe positiu |
|---|---:|---:|
| 01 final | 0,0858 / 0,0729 | 19/24 |
| 02 final | 0,0953 / 0,0748 | 19/24 |
| 01 abans d'H1 | 0,0409 / 0,0295 | 14/24 |
| Delta H1 de 01 | 0,9989 / 0,9952 | 24/24 |
| Control de soroll correlacionat | 0,0108 / −0,0040 | 13/24 |

La preferència tangencial real és compatible amb el que veu Pere. És heterogènia: alguns sectors tenen signe contrari; a02 el rang és aproximadament −0,337 a +0,280. No es demostra simetria de rotació exacta de tota la imatge.

Quan es deixa lliure el centre en aquesta prova d'orientació, els ajustos de 01/02 acaben a la frontera nord-est de la cerca, i l'el·lipse també arriba a límits de forma. Això no determina un centre. En controls sorollosos, aquesta prova tampoc recupera el centre amb prou precisió; la seva utilitat aquí és descriure orientació, no fer metrologia subpíxel.

## Controls i la component H1

El detector forward recupera cercles sintètics descentrats uns 45 px amb errors de centre inferiors a 0,1 px. També recupera l'el·lipse coneguda de relació d'eixos aproximadament 1,041, amb error de centre inferior a 0,1 px a les dues particions després d'ampliar la cerca. No retorna sempre el centre de referència ni converteix tota el·lipse en cercle. Aquesta recuperació del centre conegut no qualifica totes les prediccions: els controls també tenen alguns radis amb nusos febles (0/3 píxels reservats al cercle lliure i 45/1 a l’el·lipse lliure, segons partició).

El control amb ondulació angular m3 de 8 px mostra desacord entre particions; el soroll correlacionat sol no dona predicció radial estable. Aquests són controls concrets amb una llavor fixa, no una taxa de falsos positius universal. Els indicadors de desplaçament de plantilla i de nul condicional es conserven com a diagnosi, no com intervals de confiança geomètrica o p-valors de física solar.

**El delta H1 de 01 és el positiu real més clar:** un cercle amb centre lliure queda a menys de 0,01 px del centre de càlcul solar en les dues particions i explica aproximadament 98% de l’energia reservada del senyal filtrat d’aquest delta en la mostra fina. És una precisió interna respecte de coordenades imposades pel codi, no una mesura astronòmica del centre solar a 0,01 px. H1 de 02 és menys ideal, perquè el delta també incorpora retall/quantització i estructura no radial.

Per tant, hi ha una component que sí que és pràcticament circular i centrada on treballa el filtre. No se'n dedueix que domini els minicercles visibles. [Research 141](</Users/USUARI/Downloads/Eclipse 2026/research/141_ARCS_SOLARS_DRUCKMULLER_20260906.md>) ja mostrava que retirar H1 no eliminava el component radial curt dominant.

## Què podem afirmar

- **Mesurat:** preferència tangencial en moltes regions de 01/02, i una component H1 de 01 molt pròxima a circumferències del centre solar de càlcul.
- **No demostrat:** que tots els arcs visibles siguin circumferències perfectes, comparteixin un únic centre o tinguin separació constant. No hi ha centre/el·lipticitat físics acceptats per al conjunt de les capes finals.
- **No discriminable amb aquest assaig:** centre solar contra centre lunar C2, separats només 1,01px.

La següent mesura que podria resoldre la geometria d'una marca concreta és seguir una cresta llarga identificada inequívocament en la imatge i ajustar-ne la curvatura sense imposar el centre, amb incertesa per segment. Un arc curt i sorollós té centre molt poc determinat. Aquest assaig estadístic no substitueix aquella identificació ni n'inventa la traça.

## Reproducció i traçabilitat

Protocol i codi: [geometria_arcs_20260906](</Users/USUARI/Downloads/Eclipse 2026/research/tools/geometria_arcs_20260906>). Rebuts, mostres fixes, perfils i vistes: [output](</Users/USUARI/Downloads/Eclipse 2026/output/geometria_arcs_20260906>). `study.py` calcula la predicció; `orientation.py`, la morfologia local; `refit_ellipses.py` amplia la cerca; `audit_profiles.py` qualifica el suport dels perfils. `render_results.py` genera context complet, finestres natives i figures. El manifest final identifica entrades, dependències, versions i hashes.

S'han conservat els pilots inicials com a SUPERSEDED: separació angular insuficient, comprovació euclidiana d'un suport quadrat i cerca d'el·lipse massa dependent del millor cercle. Les proves finals s'han repetit amb separació de suports i cerca ampliada. L'auditoria de nusos sense informació continua com a límit declarat, sense amagar-ne les prediccions.

Revisió independent de lectura: Halley, àlgebra i qualificació estadística; Raman, procedència i geometria solar/lunar. Perfil contra mínims quadrats densos: error 3,33·10⁻¹⁶; radi el·líptic contra exponencial matricial: 1,42·10⁻¹⁴. Aquests controls comproven el codi, no certifiquen la geometria de cada arc real.


## Addenda: absència aparent a la corona interior, observada per Pere

07-09-2026. Pere observa que els cercles no són visibles fins aproximadament un radi solar més enllà del limbe. S’interpreta provisionalment com **r ≈ 2 R☉ des del centre**. La prova principal començava a 2,5 R☉ i no havia comprovat l’interior; aquesta nova comparació amplia només la descripció morfològica a 1,2–4,5 R☉.

S’ha repetit la mesura d’orientació local a sigma 3 en les capes 01/02 intactes, amb 24 sectors i marges de 2°, per franges radials. El llindar de curvatura s’estima en els sectors d’entrenament de cada franja. Es manté la selecció per anisotropia >0,6, sense triar la direcció respecte del Sol, i suport quadrat vàlid >10 px. Les franges contigües no són observacions independents. No s’ha ajustat un radi d’aparició ni classificat cada marca com artefacte.

- A 1,2–2 R☉ predomina fortament l’orientació radial: puntuacions aproximadament −0,60 a −0,73, amb zero sectors de signe positiu a totes les franges interiors de les dues capes.
- Entre 2 i 2,75 R☉ aquesta dominància radial disminueix ràpidament.
- A partir de 3 R☉ la mitjana és tangencial, amb intensitat variable. Això no vol dir que el primer arc aparegui exactament a 3 R☉: pot ser visible abans mentre encara dominen altres estructures.

[Orientació per radi](</Users/USUARI/Downloads/Eclipse 2026/output/geometria_arcs_20260906/lliurables/vistes/05_orientacio_per_radi.png>) i [finestres natives nord/sud, escala de gris fixa](</Users/USUARI/Downloads/Eclipse 2026/output/geometria_arcs_20260906/lliurables/vistes/06_finestres_per_radi.png>). La finestra és només de diagnosi: no és una retallada o màscara aplicada a V31.

**Hi ha dues coincidències concretes amb el processat heretat de 01/02:**

1. La fusió comença a passar de Vixen a Sony a **2 R☉** i acaba a **2,65 R☉** (`fuse_and_filter.py`, línia 94).
2. En el mateix interval el mapa de suavitzat passa del valor interior constant **sigma 0,7 px** al mapa adaptatiu Sony (`coherent_resolution.py`, línia 49). Això precedeix el suavitzat addicional de V31.

La cobertura dels dos trens i les màscares 01/02 són completes entre 1,5 i 2,5 R☉: no hi ha un tall de màscara que expliqui l’aparició. La divisió pel contrast radial també augmenta el guany en sortir de la corona brillant; no té un llindar propi a 2 R☉ (el límit exterior explícit és a 3,5 R☉). Tampoc H1 té un inici especial a 2 R☉.

Això reforça la necessitat de distingir **canvi de font, canvi del processat i canvi de visibilitat sobre una corona amb morfologia i brillantor diferents**. La coincidència de radis prioritza aquests mecanismes, però no demostra que el blend o el suavitzat generin els arcs: un defecte ja present a Sony també podria emergir quan augmenta el seu pes. La comprovació causal pendent seria aplicar exactament el mateix filtre a Vixen i Sony separades, a les mateixes coordenades i amb el mateix guany, abans de comparar-ne la fusió. No s’ha executat aquesta intervenció en aquesta addenda.

La mesura nova cobreix 01/02; no valida per si sola l’observació de Pere a tots els altres filtres. Rebut `radial_onset.json`; codi `radial_onset.py`. El veredicte sobre circumferències perfectes i centre estable continua indeterminat.
