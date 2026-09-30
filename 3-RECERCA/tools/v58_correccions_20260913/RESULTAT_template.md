# Capes Totals V58 · revisió dels sis punts de Pere

Nova versió general **V58.psb**, amb les 30 capes que Pere ha conservat a la seva V57. Fitxer: `@PRODUCT@`; SHA-256 `@SHA@`; @BYTES@ bytes. Manté el llenç 10551 × 7506, RGB16 i Adobe RGB (1998). Earthshine V56 conserva exactament RGB, alfa, màscara, geometria i revelat. No s'ha incorporat informació LROC a la fotografia ni s'ha fet una nova campanya de detall lunar.

## Fonts i conservació

La V57 d'entrada és la desada per Pere després de revisar el muntatge anterior: **30 capes**, SHA `84d2998588d536a49a9ba42e0e989ef9fd776a17b96954202fe9f64ab7ce8783`. No s'han restaurat les cinc capes que Pere havia eliminat. Una instantània byte a byte queda a `output/v58_correccions_20260913/V57_Pere_input.psb`. El V57 anterior publicat tenia 35 capes i un altre SHA; aquella autoritat és històrica.

El projecte Earthshine independent continua sent `Capes interiors/Earthshine_V56.psb`, SHA `edee45ad76f08f8450beed3e85ed0d226eb0b1e11347478d2e998d74281ce12e`. Tant aquest fitxer com la V57 de Pere s'han tornat a verificar: intactes. Els RAW i les fonts fotogràfiques no s'han escrit. A V58, els canals comprimits, màscares i geometria de 12/perles, les dues bases V42, la base corregida V56 i Earthshine V56 són exactes.

## 1. Alineament lunar i coronal

S'han separat els dos marcs. LROC s'ha registrat amb la textura lunar interior, reservant els sectors senars per comprovar l'ajust. El mateix ajust millora les quatre comprovacions locals (dues bandes, en lineal i log): translació −0,466/−0,319 px, rotació +0,15457° i escala 1,002219856 sobre el centre lunar declarat. La selecció visible LROC utilitza el contorn físic ja acceptat de V56. L'earthshine no es mou ni es redimensiona. B5 i B10 contenen ajust, controls i readback.

Les capes 06–11 tenien una petita rotació respecte de la corona general. S'han registrat amb estructura coronal, aplicant una sola transformació rígida per capa, sense canvi d'escala; girs +0,112–0,144°, translacions inferiors a un píxel per eix. Les sis capes milloren en els sectors reservats. El control amb desplaçament de 12 px i gir de 0,15° es recupera correctament. Els filtres es calculen directament al mateix llenç i coordenada solar de la corona; els 16 passen el control de pic angular i nul girat. No es promou un reajust radial del disc per forçar concordança.

La capa 12 de perles es manté exacta: una optimització amb poca corona empitjorava l'ajust i es va rebutjar. Dinou retalls de perles confirmen desplaçament mediana pràcticament nul respecte del compost acceptat. El compost alternatiu de perles/protuberàncies s'ha reconstruït a Photoshop a partir de 12+11+10+09 ja alineades. POWAAAH3 queda alineada com a referència antiga i oculta.

## 2. Protecció del limbe i de les protuberàncies

**Les 16 màscares de filtre estaven desactivades a la V57 desada.** La comprovació nativa ho va detectar perquè ampliar-les no canviava cap píxel del resultat. A V58 queden actives; és una correcció necessària per aplicar el suport real i la selecció del disc.

Els quatre RHEF tenen protecció editable fins a 4 px més enllà de la ploma lunar real, amb transició suau a força plena als 12 px. Les protuberàncies es protegeixen amb el criteri fotomètric ja existent R−G > 0,25, marge de 4 px i transició σ2. No es retalla el RGB del filtre: la fotografia base continua visible a la zona protegida. La revisió al 100% va identificar també inversió de protuberàncies als dos NRGF; reben la mateixa protecció.

La prova Photoshop compara cada RHEF i NRGF al 100% amb la base sense filtres: **@MASKMAX@ DN16 màxim** a la zona totalment protegida. Aquesta selecció de presentació no es fa servir com a prova científica de curació dels anells. La línia lluminosa fina que ja conté la base fotogràfica continua visible al 1:1; no es declara eliminada ni s'ha enfosquit la base per dissimular-la. Els altres filtres conserven el suport i la selecció física, sense una nova ampliació de presentació.

## 3. Anells concèntrics dels RHEF locals de 60° i 30°

La causa es reprodueix amb un camp analític llis: l'agrupació radial de 8 px de l'operador antic afegeix periodicitat que no existeix a la font. Els dos locals nous calculen distribucions a radi fix i avaluen el rang al valor natiu de cada píxel. No s'han suavitzat els anells a posteriori.

Sobre el resultat real sense màscara, el pic de potència al període de 8 px respecte dels veïns passa de **989,18 a 1,339** (60°) i de **1145,95 a 0,823** (30°). Sony independent i Vixen tampoc presenten aquest pic. Els controls causals C4 passen i les 16 injeccions C3 retenen aproximadament 98,4–99,2% del senyal respecte del rang ideal a radi fix. No és un percentatge de resolució. S'han descartat DR1, que només retenia 37–44%, i els ajustos anteriors inconsistents; els rebuts romanen conservats.

La correlació absoluta amb Sony sense filtrar és menor als locals nous (aprox. 0,499–0,531 davant 0,574–0,589). El rang exacte canvia el contrast; no es declara una millora universal de fidelitat per aquesta mètrica. El claim validat és la supressió del període artificial, amb retenció d'injeccions i geometria corroborada independentment.

## 4. Estrelles fora dels filtres

S'han examinat 764 posicions de catàleg dins del suport, amb controls de catàleg girat i comprovació entre fonts quan és disponible. Es retira la llum compacta de **52 fonts corroborades abans de calcular els 16 filtres**, incloent fonts que la supressió antiga de 21 estrelles no cobria. Model empíric no negatiu amb fons local ajustat separadament; no es clonen píxels ni soroll. Els casos sense detecció a Vixen es deixen intactes en aquesta font. Els filtres es regeneren amb les mateixes receptes i perfils de contrast declarats, excepte la correcció causal dels dos RHEF locals.

Les 120 injeccions coronals febles passen el control de retenció del retall complet, amb guany mínim 0,9157. Fora de les petjades estel·lars, la font queda exacta a precisió numèrica. No es reivindica recuperar la corona que hi ha sota una estrella. La llum separada es conserva a `sources/` per a la futura feina d'estrelles; no s'ha iniciat un altre projecte.

Resta **un candidat ambigu**, TYC 825-5-1, Vmag 12,43, prop de (7783,6383). No supera la corroboració reservada i no s'ha suprimit com si fos una estrella segura. D7 torna a provar tot el catàleg després de la neteja: aquest és l'únic candidat restant segons el detector. No es promet eliminar fonts sota el soroll ni totes les estrelles possibles fora del catàleg. Les estrelles de les bases fotogràfiques i dels originals es conserven; l'exclusió afecta els filtres.

## 5 i 6. Màscara 11 i falsa diferència de mida lunar

La taca de la captura és una illa de pinzell dins del forat de la màscara 11. A més, el forat era més gran que el contorn de V56: aproximadament 456,9 davant 453,6 px, mentre que el RGB de 11 ja contenia llum a la franja amagada. Això generava bona part del buit negre; no demostrava que la Lluna fos massa petita.

S'ha eliminat l'illa i s'ha corregit l'oclusió interior de 11 amb el solapament ja acceptat de la base V56. La selecció exterior de Pere queda conservada després de la transformació d'alineament, amb transició entre r465 i r480. La màscara és zero a tot l'interior r435. La prova nativa aïlla 11+12+Earthshine i comprova la desaparició de les taques i el tancament del buit de màscara. La doble atenuació produïda per dues màscares exactament complementàries es va detectar i descartar. No s'ha ampliat el disc ni modificat el revelat de V56. El contorn fotogràfic residual no es proclama perfecte a cada píxel o equivalent entre instants diferents.

## Validació i ús a Photoshop

- Photoshop real: **@GATE@**. Segon lector: @READER@.
- Els canals editats s'han tornat a descodificar i comparar amb els arrays previstos; @CHANNELS@ canals coincideixen. Les cinc capes preservades coincideixen també en canals comprimits, màscares i geometria.
- Reobertura i recomposició del paquet final: **@READBACK@ DN16 màxim** a tot el llenç respecte de la composició nativa prevista. La caché composta coincideix també amb el readback.
- Revisió visual del llenç sencer, els 16 filtres al 100%, les quatre zones RHEF a 1:1, les estrelles i la unió 11+12+Lluna. Les vistes PNG tenen conversió Adobe RGB → sRGB només per mostrar-les.
- Presentació inicial: base corregida V56 i Earthshine actives; RHEF υ0,35 a aproximadament 35%. Les alternatives romanen editables, amb l'ordre de les 30 capes de Pere. El compost solar alternatiu i les referències LROC/POWAAAH3 són ocults.

El perfil ICC i la resolució física del document coincideixen byte a byte amb la V57; l’etiqueta genèrica «sRGB» d’ImageMagick no substitueix la lectura de l’ICC Adobe RGB (1998).

La V58 queda oberta a Photoshop. El judici visual de Pere queda pendent; aquest lliurament no declara absència absoluta d'artefactes, nova resolució lunar ni equivalència DHS.

## Represa i rebuts

Codi: `/Users/USUARI/Downloads/Eclipse 2026/research/tools/v58_correccions_20260913`. Evidència: `/Users/USUARI/Downloads/Eclipse 2026/output/v58_correccions_20260913`. Manifest: `@MANIFEST@`. Handoff: `@HANDOFF@`.

A0/A1 congelen font i jutges. A2/A3/A4 declaren les noves causes i rectificacions; no s'ha esborrat un fracàs ni canviat un llindar per obtenir PASS. B valida geometria i màscara; C anells; D estrelles; E regeneració; F geometria i vistes de filtres; G–I muntatge i lectura nativa. Els intermedis G6/G9 amb caché RGB de tres plans i capçalera de quatre van ser refusats per Photoshop; la discrepància es va reparar abans de la porta final. Els paquets amb màscares encara desactivades tampoc són lliurables. **Només el V58.psb publicat amb el SHA anterior és la versió final.**

Abans de reprendre: AGENTS, CLAUDE complet, IA README → ESTAT → MAPA, lock viu i claim nou. Cap escriptura a CLAUDE_STATUS, cap Git i cap treball llançat a Claude. Estat d'alliberament efectiu a `J3_release.json` i CODEX_STATUS. Les autoritats anteriors es preserven senceres a `receipts/`. Després de verificar el lliurament s'han retirat només els nou PSB intermedis generats en aquesta tasca, amb inventari i SHA a J4; es mantenen la instantània V57 de Pere, el paquet final de QA, el V58 publicat, tots els arrays, codi, rebuts i renderitzats natius.
