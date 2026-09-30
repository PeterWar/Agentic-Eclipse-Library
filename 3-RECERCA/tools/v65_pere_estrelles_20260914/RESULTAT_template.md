# V65 · encaix de Pere, color del limbe i 60 estrelles

Producte: `@PRODUCT@`  
SHA-256: `@SHA@`  
10551 × 7506, RGB16, Adobe RGB (1998), **31 capes**. Photoshop obert en la V65 desada. Font de Pere intacta.

## Resultat fotogràfic

S'ha utilitzat la font real desada **V64_Artefactes.psb** (27 capes, SHA `4ead6376a09b12a71a3d0572b578549552bc622fdc8ba72ab4888714e2127fc1`), anomenada V64_CanvisPere al missatge. La seva capa96, `07 1/15 x2 quar`, és la fotografia que Pere ha superposat per recuperar el detall de les perles. Aporta senyal real; la còpia83 continua sense aportació visible en el retall lunar. Totes dues es conserven exactes.

**Cap canvi d'alineament:** bboxes, RGB de l'earthshine, alfa, totes les màscares originals, ordre de les fonts i la fotografia de perles són exactes. La capa76 és el raster que Pere havia col·locat manualment; no s'ha restaurat cap objecte intel·ligent ni aplicat cap matriu de V61–V64. Només s'han canviat RGB de la base3 i el color local de76, sense moure cap píxel. Les anotacions originals continuen editables i ocultes.

### Marques 1, 3, 4, 5 i 6: blanc de la corona interior

La blancor ja apareixia a la base. El productor antic comprimía el color de les llums altes cap al blanc quan el vermell arribava al límit de representació. Els filtres en reforçaven l'aparença. També hi havia píxels vàlids afegits per la recomposició V53 que encara quedaven fora del primer pilot de correcció.

S'ha substituït aquest comportament per una corba suau de llums altes que conserva la cromaticitat fotogràfica mesurada. Llindar relatiu0,9 del límit de gamut; continuïtat de valor i pendent. L'estimador de color manté l'exclusió V62 de les protuberàncies vermelles: **no torna el reflex vermell ample**. Cap filtre espacial nou sobre el detall. Canvi en127.367píxels RGB de la base, inclosos píxels amagats. Les cinc zones milloren en els dos quocients de color davant de la Sony independent, amb el guany congelat abans d'aquest assaig (`B12_independent_colour.json`). És una comprovació de color, no una validació astronòmica global del limbe.

### Marca 2: protuberància superior taronja

La mescla de la capa76 diluïa el color del senyal de línia amb continu coronal. La referència és el color de la fotografia11 original, corroborat amb10. S'ha ajustat únicament el transport d'aquesta referència de color: la part inferior de la tija, reservada, dóna correlació0,927. La geometria de la imatge de Pere no es transforma.

Correcció cromàtica en601píxels de76, mantenint la forma i els canals de cobertura. El peu i la tija recuperen un vermell més coherent amb les fotografies curtes. Les proves de registre global B6 i B8b es rebutjaren i no s'han aplicat.

### Marques 7–11: petites irregularitats fosques inferiors

Part del defecte és una pèrdua de cobertura en la superposició de rampes d'opacitat de la base i la Lluna. S'han normalitzat **763píxels** on totes dues fonts ja tenen cobertura vàlida. La capa nova `Contorn · normalització del compost V65` conserva la proporció de la mescla i en restaura l'opacitat. No amplia cap radi, no circularitza la Lluna i no inventa dades fora del suport.

La primera prova amb un suport sota els filtres fou rebutjada: els filtres tornaven a modificar el color del suport. La normalització validada va damunt del compost i reprodueix el resultat matemàtic amb màxim1DN16. El relleu fosc restant no s'ha esborrat. **No hi ha prou evidència per identificar-lo com a cràters**, ni per declarar que tota irregularitat del contorn és un artefacte. Les màscares i l'encaix de Pere queden exactes.

## Estrelles

**60 fonts puntuals corroborades, 62 identificacions de catàleg.** Dues parelles a0,52 i1,37píxels no es presenten com quatre estrelles resoltes: cadascuna es representa amb un únic punt, sense sumar dues vegades els mateixos fotons. Magnituds de catàleg aproximadament6,31–10,33 dins del llenç vàlid; no s'han dibuixat objectes de catàleg sense senyal repetit als RAW.

S'han mesurat directament els quatre plans CFA de **15RAW**, 7Sony i8Vixen, amb dark de l'exposició i flat físic abans de qualsevol interpolació. Inclouen totes les exposicions d'almenys1s dels dos conjunts utilitzats. La cerca addicional a la Sony recupera cobertura nativa que es perdia al rectangle de l'apilat antic. S'ha separat detecció, fotometria, registre del camp d'estrelles i representació fotogràfica.

Criteris congelats: SNRtotal≥8 i suport≥4 en dues preses/apuntaments o instruments independents, amb controls reflectits tractats de la mateixa manera. **0 acceptacions en1.219posicions de control diferents**, sobre1.132posicions de catàleg examinades. No és una prova de completesa absoluta. El catàleg conserva procedència, flux mesurat, error formal, color, posició i mètode. Els candidats antics que no passen el suport fotogràfic no es fabriquen.

### PSF i moviment

La PSF nativa es mesura per exposició. Exemples Sony: dispersió aproximadament0,92×0,95píxels a DSC06984, però1,01×2,11 a DSC06993 i1,02×3,70 a DSC06991. Les traces de muntura es modelen separadament del punt de sortida. El camp es transporta des de les coordenades natives per les solucions existents fins al llenç V42; **no es fa cap placa astromètrica nova amb el HDR ni es mou la imatge existent**. El mapa Sony C→A manté un terç de les estrelles reservat: residu mediana0,512píxels natius, màxim1,630. No es promet registre absolut subpíxel de totes les fonts.

La nova capa utilitza una **gaussiana circular integrada al píxel, sigma1,5píxels finals (FWHM del model3,53píxels)**. És una regularització fotogràfica de fonts puntuals confirmades, no superfície estel·lar resolta ni nova resolució òptica. La llum de traces antigues encara mesurable s'ha separat amb una capa de resta en16posicions; només es retira el component puntual mesurat, sense reconstruir ni clonar el fons coronal. En44posicions no hi havia una traça restant prou significativa per justificar-ne la resta.

Les estrelles tenen una corba de presentació declarada per fer visibles també les febles: pic0,74 × (flux/fluxmàxim)^0,55. El perfil gaussià es defineix en els valors del document; el catàleg manté a part la fotometria lineal nativa. Balanç de dia, matrius de càmera, guanys de color i conversió a AdobeRGB declarats. El color feble té regularització espectral i incertesa atmosfèrica.

### Controls i límits de les estrelles

- Quadratura de7punts davant de3: error màxim7,82×10⁻⁷ en la PSF normalitzada.
- Injecció condicional del mateix model sobre fons CFA real:168/168 dins del10% de flux; no equival a una prova de descoberta completa.
- Ajust amb soroll/fons real, SNR100:36/36 dins del10%, posició mediana0,018píxels natius; a SNR30:35/36, mediana0,062; a SNR10 la dispersió fotomètrica és substancial. Les estrelles febles conserven incertesa.
- Prova deliberada amb una PSF escombrada diferent de la gaussiana:33/168 surten del10%, amb biaix màxim33,8%. **No es declara precisió fotomètrica universal del10%**. La calibració per obertura només fa servir estrelles d'entrenament; les reservades mostren límits, especialment a572A2982. Els errors formals del CSV no inclouen tots els sistemàtics de PSF/extinció.
- Les parelles molt properes continuen sense resoldre i no s'atribueix estructura nova a cap estrella. Cap píxel estel·lar nou queda retallat per saturació al compost final.

## Capes i fitxers per a Pere

Les27capes de la font es mantenen; les quatre capes addicionals són:

1. `Contorn · normalització del compost V65`, visible.
2. `Estrelles · retirada de traces mesurades V65`, visible, modeResta; funciona juntament amb la capa següent.
3. `Estrelles · 60 fonts · PSF gaussiana V65`, visible, modeSobreexposició lineal/Afegir.
4. `Mapa de 60 estrelles · HIP i TYC · V65`, **oculta per defecte**. Activa-la per veure les identificacions.

Fitxers complementaris a `@ASSETS@`:

- `V65_estrelles_marcades.png`: vista completa amb les identificacions, estil de la referència de Derivats.
- `V65_estrelles_anotacions.png`: anotacions transparents separades.
- `V65_estrelles.csv` i `V65_cataleg_estrelles.json`: catàleg i procedència.
- `V65_previsualitzacio.png`: vista general sense anotacions.

Per comparar les estrelles amb l'estat anterior, alternar conjuntament les dues capes d'estrelles visibles. Les anotacions i la normalització del contorn són independents.

## Validació del fitxer

- **148comprovacions de canals**: tots els canals originals no editats exactes; RGB de3/76 coincideixen amb la correcció esperada amb màxim1DN16; totes les geometries, màscares i alfa originals exactes. RGB/alfa/màscara de l'earthshine30 i de les perles96 exactes.
- Composició Photoshop davant del càlcul: màxim1DN16; **0DN16 fora de les regions editades**. La nova contribució estel·lar afecta10.153píxels de suport en un llenç de79,2milions.
- Porta nativa: `@GATE@`.
- Segon lector: `@READER@`; ICC AdobeRGB verificat byte a byte.
- Reobertura del fitxer lliurat i recomposició forçada de tot el llenç: **@READBACK@DN16** màxim respecte del candidat natiu desat.
- Font V64_Artefactes i còpia congelada amb SHA exacta;15RAW amb identitat, mida i data exactes, hashes registrats; flats exactes. Documents originals de Pere oberts i desats, sense modificacions.
- Revisió visual del llenç complet,60estrelles a escala ampliada, protuberància superior, perles i12sectors del contorn. @UI@

No es declara absència universal d'artefactes, una nova resolució lunar ni un PASS astronòmic absolut del contacte temporal. El resultat és una V65 fotogràfica revisable amb les correccions i les capes d'estrelles acabades, respectant l'encaix manual.

## Represa tècnica i vies rebutjades

Codi: `research/tools/v65_pere_estrelles_20260914/`. Evidència: `output/v65_pere_estrelles_20260914/`. `B0_PROTOCOL.md` i `S19_PROTOCOL.md` fixen l'abast i els controls. La font congelada és `V64_Pere_input.psb`.

Cadena acceptada: A1/A2/A3 → B9/B10 (taronja) + B11k0,9/B12 (blanc) → D4/D5/D6 → D7/D10 (normalització sobre el compost) → S7/S9/S10 + S11/S12/S13 → S14/S15 + S16/S17 → S19/S21/S22/S23/S24 + S20/S25/S26 → D11b/D12/D13/D14 → E0/E1/E2/E3/E5. S26 neteja els no-disponibles a null i afegeix els límits al catàleg. Les sortides diagnòstiques anteriors es conserven com a evidència, no com a productes acceptats.

Rebutjats/superats: B3 deixava fora píxels nous V53; B6/B8b no tenien registre cromàtic prou fiable; D7 amb la normalització sota els filtres era incorrecte i D10 la substitueix; S2/S5 abans del mapa C→A refinat no són el catàleg final. El PSB petit S24 amb previsualització fusionada ZIP fou refusat per Photoshop; S24b amb previsualització RAW va obrir correctament. El primer AppleEvent de desament D13 va caducar als120s, però el Photoshop va acabar el mateix desament, verificat pel log i el hash: **no es va repetir una operació amb resultat ambigu**.

Les dades intermitges grans exclusivament nostres es poden eliminar després de la validació, amb rebut; mai la font de Pere ni els RAW. El PSB natiu i el lliurat són còpies APFS verificades, no nous càlculs independents. No es reclama reproducció RAW→PSB en dos directoris nets.
