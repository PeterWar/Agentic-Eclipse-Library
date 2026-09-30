# V61: encaix de les capes interiors restaurat; filet blau encara pendent

Producte: `@PRODUCT@` · SHA-256 `@SHA@` · @BYTES@ bytes. 10551 × 7506, RGB16, Adobe RGB (1998). La V60 que Pere ha desat amb 32 capes i les marques blaves es conserva exactament, així com `Vista_V57_correcte.psb` i la còpia font V57.

## Capes interiors

La prova factorial separa dues modificacions V58: el gir independent de 06–11 (12 es deixà fixa) i, sobretot, l'extensió de la màscara 11 per sota del contorn. Aquesta extensió tapava perles que provenien de 12. Restituir la màscara original fa reaparèixer les perles; restituir també tots els RGB i geometries 06–12 retorna l'encaix relatiu de V57. La vista de Pere correspon a 07–12 visibles, amb 06 oculta.

S'han restituït els set originals sense remostreig. Només es retiren 9.281 píxels de l'antiga màscara 11 dins de la Lluna ja plenament opaca, incloent-hi la taca accidental que Pere havia mostrat. A Photoshop, el compost 07–12 restaurat coincideix **exactament, 0 DN16**, amb `Vista_V57_correcte` a tots els píxels fora de la zona lunar plenament opaca; també a perles i protuberàncies. Dins del disc, la supressió de la taca canvia 3.819 píxels en més de 4 DN16, màxim 800 DN16. No es toca el RGB fotogràfic.

L'encaix del conjunt amb `00 Base corba · limbe corregit V56` requereix un **sol gir comú de +0,1412371774°**, amb desplaçament (−0,15087452; −0,43907974) px al centre solar (5361,76811197; 3775,74753414). Escala exactament 1. El registre es basa en estructures exteriors, excloent el límit del disc (r lunar 466–510 px), i no en ajustar-ne el radi aparent. Dos sectors ajusten; la protuberància superior es reserva. Correlacions: oest 0,738→0,769; sud-est 0,517→0,542; superior reservada 0,788→0,860; oest inferior de comprovació 0,820→0,823. Els pilots C0/C1 no es promouen; el primer pilot superior havia emprat una caixa situada massa a l'esquerra. C2 usa la posició de la protuberància identificada a la referència de Pere.

Controls: identitat recuperada a menys de 3e−6 px; injecció (1,25; −0,75; 0,17°) recuperada amb errors (0,009; −0,022; 0,0020°). Photoshop aplica la matriu a totes les cantonades amb error màxim 1,82e−12 px. Les 10 estructures protegides retenen el flux cromàtic entre 0,99985 i 1,00067 respecte de la referència sotmesa al mateix gir, i els pics entre 0,99956 i 1,00227. Són comprovacions de retenció fotogràfica, no una nova resolució astronòmica.

## Com està preparat a Photoshop

- **`Interiors 06–12 · alineades amb la base · V61`** és un objecte intel·ligent incrustat, amb les set capes editables a dins. Doble clic a la miniatura per obrir-les. La transformació comuna s'aplica a l'objecte complet, preservant els RGB i l'encaix entre les capes; no es remostreja cada màscara per separat.
- **`Interiors 06–12 · referència original V57`** conserva també les set capes directes en el marc original, per comparar-les amb la vista de Pere.
- Tots dos estan ocults, damunt els filtres de corona i sota l'earthshine. La capa 12 té un fons opac: activar tot el conjunt substitueix també la corona de sota. S'ha plantejat a Pere si prefereix decidir la mescla o rebre una màscara comuna; no hi havia resposta en preparar aquesta disposició. No s'ha inventat una màscara de mescla addicional.
- El compost antic V58 es conserva ocult com a comparació perquè contenia l'encaix i la màscara anteriors. Les dues capes de marques es conserven ocultes. Earthshine està visible, amb el RGB, l'alfa, la màscara interior V60 i la geometria exactes.

## Filet blau: no resolt completament

S'ha comprovat un error de composició petit però real: als sis NRGF/RHEF, la màscara tornava a multiplicar la transparència parcial que ja tenia la base. S'ha retirat aquesta segona aplicació només al suport físic ja existent; es manté la protecció de protuberàncies i tot el raster dels filtres. Amb un filtre constant, el guany ha de ser independent de la transparència de la base: el control passa de variar 0,216 a variar 0. La lectura nativa de les sis màscares noves es verifica dins de 2 DN16.

Aquesta correcció **no elimina tot el filet** assenyalat per Pere. La banda se situa a la unió entre la base i la rampa lunar; al nord, la màscara de base passa pel 50% a r≈450,7 i la lunar a r≈452,2, amb solapament deliberat. Quan l'earthshine està ocult, queda exposat aquest solapament sobre el disc de les exposicions interiors. També amb l'earthshine visible queda un filet fi. No s'ha validat una causa única ni una correcció final del RGB de la base, de l'operador ACHF o de la vora lunar; aquests continguts es preserven.

La primera impressió visual que atribuïa la marca superior al compost 09 es va descartar: les diferències numèriques en les caixes blaves són 0 DN16 en desactivar-lo. No és una causa confirmada del blau i no s'ha de reprendre com si ho fos. Tampoc es declara que les marques laterals estiguin resoltes. No s'ha pintat ni interpolat la zona, ni s'ha ampliat arbitràriament el disc per amagar-la.

## Verificació i represa

@GATE@. Aquesta porta compta 26 capes d'art de primer nivell; hi ha, a més, un grup (27 elements a l'arrel). Hi ha 32 capes de píxels originals, un objecte intel·ligent i un grup; l'objecte conté la còpia editable de les set interiors. Segon lector: @READER@.

192 comprovacions de canals, incloent tots els originals, les set capes incrustades i les màscares corregides. RGB, alfa, geometria i perfil dels originals no modificats exactes; les noves màscares tenen només la quantització nativa màxima de 2 DN16. Reobertura del fitxer publicat i recomposició: màxim @READBACK@ DN16. V60, Vista V57 i font V57 verificades per SHA-256.

Font V60 desada per Pere: SHA `48a1f0b329b77454c112e490d5728fff585d7b29cf801f980cc4d55d54f1fc52`. Referència Vista V57: SHA `39cf0987fb36f836b35a3eff69db2d83e25eeab27dfd149e7e9e86c4ddce147b`. Font V57: SHA `84d2998588d536a49a9ba42e0e989ef9fd776a17b96954202fe9f64ab7ce8783`.

Scripts: `research/tools/v61_interiors_limbe_20260913/`. Fonts i proves: `output/v61_interiors_limbe_20260913/`. Recepta: A0 fonts; A1 protocol; A2 factorial; A3 coincidència; B0/B1 transparència; C2 registre comú; C3 controls; C4 retenció; D0 restauració; D3 objecte intel·ligent natiu; D5 integritat; E0 publicació; E1 reobertura. `D3_smart_default.tif` no s'usa: un canvi de referència DOM deixà temporalment visible el grup original. Es va corregir abans del Save As; `V61_saved_readback.tif` i `V61_final_readback.tif` són els controls finals. Evitar `var path` a JSX: col·lideix amb un nom nadiu; E1 usa un identificador específic.

Continuació oberta: decidir la mescla de les interiors i investigar el filet blau a l'origen amb les fonts i els criteris congelats. No nova resolució, absència global d'artefactes ni recuperació absoluta del limbe declarades. El projecte lunar independent continua V56 intacte; V61 conserva la correcció de màscara lunar de V60.
