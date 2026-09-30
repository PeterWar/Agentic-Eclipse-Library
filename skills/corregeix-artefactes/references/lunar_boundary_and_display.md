# V85: color de presentació, limbe mòbil i domini de l'operador

Lliçons comprovades el 22-09-2026. Evidència de projecte:
`4-RESULTATS/v85_regeneracio_20260922/`. L'estat del producte i l'acceptació
de candidats són als seus rebuts; una execució acabada no és una cura validada.

## Diagnosticar el verd abans de tocar les dades

Una capa anomenada «linealitzada» dins d'un PSB no demostra que l'artefacte
sigui als RAW o a l'entrada lineal dels filtres. Comparar, amb renderitzat
natiu i mateix ICC, base sola, ajustos per separat i compost. A la V84 de
Pere, el verd marcat estava associat als ajustos de presentació i a retall
del vermell: una compressió suau de les altes llums, comuna a RGB, abans dels ajustos va reduir el
retall del 71,82% al 0% en la mostra marcada. Això no justifica una correcció
de G als RAW ni una nova calibració cromàtica.

Una capa rasteritzada de PixInsight situada per sobre de les capes noves
pot mostrar encara la corona antiga. Inventariar-ne ordre, opacitat i
màscara. Si també conté la lluna processada de Pere, protegir aquesta
contribució. Els ajustos espacials poden canviar la lluna indirectament
encara que els seus RGB i màscares originals siguin idèntics: comparar
el compost natiu de tota la lluna, no només els canals de les capes.

## Tres suports diferents

1. **Observació física:** validesa per fotograma i per canal, distància al
   limbe d'aquell instant i unió temporal de mesures. No eliminar corona
   observada amb un cercle engrandit. La distància al radi modelat pot ser
   negativa fora de la silueta aparent; registrar la distinció.
2. **Domini de càlcul del filtre:** definir-lo a partir de la validesa de
   la font i del senyal que es vol filtrar. No confondre la fotografia lunar
   de presentació amb el suport físic temporal. En la V85, excloure aquesta
   fotografia abans de filtrar també retirava 36.581 píxels acceptats pel
   productor físic. Això era una variant experimental, no una correcció
   causal demostrada. Tampoc conservar tot suport històric prova que sigui
   corona neta: cal distingir mesures coronalment vàlides, llum fotosfèrica,
   protuberàncies i mostres afectades pel limbe. Diagnosticar-ho abans de
   decidir el domini; aplicar coherentment la decisió a tots els suports
   auxiliars, perquè un OR amb S4 pot readmetre dades excloses.
3. **Validesa de la sortida del filtre:** excloure tota la Lluna segons la
   màscara de presentació autoritzada. Registrar també pèrdues per
   llindar estadístic. Un valor 0,5 no és neutre sota Multiply; no amagar
   un NaN amb gris mitjà i deixar-lo contribuir al compost.

El farciment és una condició numèrica, mai corona recuperada. Valors i
derivades incompatibles a la vora produeixen respostes als operadors.
Declarar equació, màscara exacta, dades de contorn i límits. Un solver
convergent no prova fidelitat fotogràfica; no donar per bona cap extensió
només perquè l'anell és menys visible. Conservar intacte tot píxel observat
exterior a la màscara declarada.

## Proves que no es poden substituir

- Regenerar a partir d'entrades manifestades, amb ordre i variants exactes.
  E6 local60/local30 natius substitueixen els E1 locals de la genealogia
  V58. Hi ha 16 rasters vigents per a 17 capes perquè un WOW és duplicat.
- Mesurar al limbe real, inclosos 1,03–1,13 R, per distància a la màscara
  i sectors. Una porta de Brno que comença a 1,15 R no avala la banda interior.
- En controls sintètics, reproduir el farciment concret de cada variant:
  P04 històric utilitza perfil B; P05 bilateral, A. V85 prova explícitament P04 amb A i en declara la desviació del productor històric. Injectar abans d'estimar perfil
  i contorn, comparar injectat menys no injectat contra veritat coneguda i
  declarar guany/error per escala, orientació i distància. Ni la mediana
  global ni un guany reajustat amaguen sectors amb biaix.
- Congelar els reservats abans de provar una correcció de fonts. Separar
  disminució de soroll, biaix, suport, contribucions i transferència de
  detall. L'antic comentari que «2 px basta» era una mesura històrica amb
  abast limitat, no una garantia per al limbe de qualsevol filtre posterior.
- La prova q16 de V85, amb pesos positius dependents de la distància, va
  crear quatre píxels G negatius en fusió abans positiva i va donar jutges
  mixtos. Va ser rebutjada; no reparar només els quatre píxels ni retocar
  el candidat després de veure els reservats per declarar PASS.
- La reconstrucció exacta de calibració, intermedis i filtres no demostra
  RAW→PSB íntegrament determinista si registre, displays, muntatge i
  decisions manuals són entrades congelades.

Preservar els intents fallits i les limitacions. Actualitzar el rebut amb
el mètode final i els resultats mesurats, sense convertir aquesta nota en
una afirmació d'absència global d'artefactes.

## Selecció V85 i límits que s’han de conservar

El farciment biharmònic sense límits va funcionar millor en alguns operadors
escalars, però va sobrepassar fortament el rang del residu logarítmic RGB
i va crear un anell gris ampli en ACHF. Aquesta variant E3 es va rebutjar.
La versió seleccionada usa L²+L, tensió unitària a la graella, dins la màscara;
no és una recepta universal ni s’ha d’exportar a altres resolucions sense proves.
WOW estàndard i bilateral seleccionen perfil A amb biharmònic; MGN, perfil B.

Els controls de V85 milloren error contra veritat coneguda, però fallen
l’interval de transferència 0,9–1,1 en 13/69 casos de WOW, 23/69 bilateral,
28/69 MGN i 14–20/69 ACHF segons escala. Predominen els primers píxels
del contorn; hi ha excepcions més llunyanes. No convertir RMS menor,
convergència del solver o correlació Brno millor en «tot el limbe recuperat».
E3 es va provar abans del display; Brno comença a 1,15 R i no avala color
ni pedestal radial. El lliurament és una millora amb límits per revisar.

Una placa petita de preservació del compost natiu original pot ser necessària
si ajustos espacials de presentació alteren indirectament la Lluna. Cal
mascara binària al suport estrictament afectat, mateixa geometria/ICC,
i igualtat del compost de **tota** la Lluna. És preservació d’una aparença
manual, no recuperació científica ni excusa per tapar corona exterior.

## Rectificació del domini i límits de R02

La prescripció inicial d’excloure sempre tota la foto lunar de l’entrada era
massa forta: R02 la rectifica explícitament. Eliminar-la del resultat del
filtre i evitar una entrada contaminada són dues obligacions diferents.
La variant que reté tot suport físic tampoc no s’ha acceptat automàticament:
el biharmònic sense tensió produeix sobreoscil·lacions importants i canvis
amples de llum. Un suport més justificat no valida la continuació numèrica.

Separar també domini, farciment i normalització. MGN usa extrems de la font:
el seu màxim pot canviar molt quan es readmeten píxels sota la fotografia
lunar, alterant el terme global a tot el llenç. Per a una prova causal del
farciment cal normalització comuna o separar explícitament els termes.
L’oracle i el candidat han d’usar els mateixos límits per cada escena.

Una diferència radiomètrica entre èpoques no justifica per si sola corregir
una exposició. Comparar parelles fixes i el seu pes real dins de l’apilat.
A les marques 246, la banda tardana D<0 amb dèficit tenia una fracció màxima
de pes CFA-G de 9,19·10⁻⁷. Un dèficit hipotètic del 36% tindria un efecte
lineal màxim de 3,31·10⁻⁷ relatiu, condicionat a radiància comuna; això no
és una cota del compost filtrat ni valida els valors de cada fotograma.
No s’ha aplicat una correcció uniforme d’exposició.

Els controls que injecten també en zona físicament desconeguda combinen
retenció del senyal observat i hipòtesi de continuació. Cal conservar les
fallades mesurades; un control addicional només visible o d’interior ocult
pot separar hipòtesis, però no converteix la prova anterior en PASS.

## Calibració existent i identificabilitat de la franja interior

Abans d'afegir una correcció temporal, seguir els numeradors: F2.2 ja aplica
guanys de coherència per fotograma; V36 incorpora offsets RGB i camps suaus
phi. Els residus temporals de R02 són posteriors a aquestes correccions.
No atribuir-los automàticament a transparència no calibrada.

La resposta B(D) s'ha de jutjar amb la població de fotogrames de cada punt,
també als veïns que usa el filtre. Un pes molt petit al centre d'una marca
no acota el pes al seu costat interior. A l'arc superior de V85, l'ablació
train mostra que B(D) canvia el signe del contrast normal, però el veí
interior no té cap observació train amb D>4. Això explica la sensibilitat;
no identifica la radiància correcta. No retirar B(D) ni ajustar-la per
aplanar la marca sense referència independent o model validat.

Una prova amb la font anterior a S4 ha de restaurar B3/B2 real, amb la
substracció estel·lar preservada i els suports auxiliars coherents. Posar
només la màscara B3 sobre D4 no elimina la radiància S4. Declarar els punts
que perden suport; que una marca deixi de ser mesurable no és recuperació
de corona. No aplicar una ampliació circular per ocultar-la.

Comparar la gravetat de les fallades, no només comptar-les. En el pilot de
moments quadràtics, 04 passa de 19 a 9 cel·les fora del llindar, però algunes
injeccions canvien de signe respecte de l'oracle. Els nulls polinòmics,
la bona condició numèrica i les millores exteriors de Brno no ho anul·len.
Aquest pilot no s'ha promogut. Els controls amb injecció oculta no mesuren
directament un percentatge de senyal observat perdut.

Evidències: `TEMPORAL_CALIBRATION_R02.json`, `bias_component_R02/RECEIPT.json`,
`fixed_pairs_R02/SUMMARY.json`, `MOMENT_R02_DECISION.json` i els rebuts de
cada domini dins del paquet V85. R02 continua en diagnosi; cap nova versió
PSB acceptada ni absència global d'artefactes acreditada per aquestes proves.

## R03: contorn aparent, PSF i selecció temporal

F4 mesura el màxim de derivada radial, mentre altres vores de la taula
històrica M1 usen el 50 %. No convertir-ne la diferència en un canvi físic
uniforme de radi. B(D) es va calibrar respecte del model: si es canvia la
coordenada de distància, cal transportar o recalibrar també la resposta,
no substituir simplement l'argument de la mateixa corba.

Les PSF estel·lars existents són condicionals, distants o d'altres èpoques;
les ales B0 són heretades d'un ajust lunar. No constitueixen una mesura
independent local per als curts d'1/3200. Es conserven com a informació per
a models futurs, sense promoure una desconvolució ni repetir inversions
òptiques ja refusades.

El pilot de sis curts primerencs, comparat amb dinou de la mateixa exposició
i seixanta-un de mixtes, no resol totes les marques. A l'arc superior els
primers ja dominen; altres millores de contrast conviuen amb més variació
i jutges Brno mixtos. Canviar època també pot canviar exposicions i soroll:
fer servir un comparador de la mateixa exposició i publicar-ne el suport.
Evidència: `GEOMETRY_PSF_R03.json` i `early_epoch_R03/DECISION.json`.

La descomposició per canals R03 confirma que la matriu RGB modula el contrast,
però la depressió del component1 ja existeix al verd de càmera calibrat abans
de la matriu. No atribuir una franja a coeficients negatius sense mesurar les
contribucions, ni substituir la font perquè baixa un RMS que pot incloure
estructura real. Prova train només, 902 triplets comuns, cap PSB canviat:
`camera_channels_R03/QA.json` i `DECISION.json`.
