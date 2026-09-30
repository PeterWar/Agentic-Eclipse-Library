# Capes Totals V63 · perles, protuberància superior i cobertura del contorn

13-09-2026. Correcció de composició fotogràfica lliurada per revisar a Photoshop. Pere ha acceptat explícitament la retirada del reflex vermell ample de V62; el RGB d'aquella correcció es conserva exacte.

Producte: `@PRODUCT@`  
SHA-256: `@SHA@`  
Mida: @BYTES@ bytes; 10551 × 7506, RGB16, Adobe RGB (1998), 24 capes principals. Interiors 06–12 editables dins l'objecte intel·ligent. Marques de Pere conservades i ocultes. V62 original intacta.

## Canvi visible i límit

Les perles i el peu de la protuberància superior reben ara la contribució completa de la fotografia 06–12 seleccionada per Pere. El disc d'Earthshine ja no la retalla una segona vegada. Disminueix el pedestal clar de la protuberància superior i la franja blanca a l'oest. La circumferència lunar té cobertura completa: 1.465 píxels parcialment transparents a V62 passen a zero en el ROI de 2000 × 2000.

La revisió inclou els deu blaus de Pere, vistes ampliades de les perles i la protuberància, tota la vora en polar i el llenç complet. Persisteix una transició molt fina en alguns sectors, amb suavitat de la font i mostreig visibles en ampliació forta. **No es declara absència global d'artefactes ni un nou registre astronòmic absolut validat.** La millora d'encaix d'aquesta ronda és de composició; no s'ha aplicat cap nova translació, gir o escala. La discrepància local NW anterior no queda convertida en PASS geomètric.

## Causes i correcció

1. **Protecció antiga sota la nova fotografia.** Les sis màscares dels filtres multiplicatius conservaven una protecció ampla de la representació antiga de les protuberàncies. Sota la fotografia fina deixava una franja blanca o un pedestal clar. Es retira aquesta protecció només segons la selecció ja pintada per Pere: 17.001 píxels a ID41 i 15.221 en cadascuna d'ID42–46. Fora de la selecció, màscares exactes. No s'ha pintat una nova regió ni una nova ploma. RGB, alfa de font, opacitat i mode dels filtres exactes.
2. **Doble atenuació i forats de cobertura.** La base i la Lluna tenien totes dues cobertura parcial en alguns píxels. S'ha fet opaca la màscara de la base en 1.895 píxels amb RGB coronal existent i alfa de font completa sota cobertura lunar parcial. No s'ha interpolat ni afegit RGB. En altres 347 píxels sense font coronal, tots opacs abans de l'edició de Pere, s'ha restituït aquella opacitat lunar. Es mantenen les altres 3.286 edicions de la seva màscara. Els 347 es troben a l'oest, x4924–4935/y3681–3858, no en tota la circumferència.
3. **Ordre de la fotografia 06–12.** S'ha situat l'objecte d'interiors sobre Earthshine mantenint exactament la selecció de Pere i la matriu anterior. La fotografia ja conté l'ocultació observada del Sol; una màscara d'Earthshine aplicada després retallava de nou part del seu primer pla. Es conserva la geometria relativa de les set exposicions de V57. Aquest canvi no demostra que tots els instants tinguin una única vora astronòmica.
4. **Opacitat indefinida del fons negre intern.** C2 calculava una cobertura amb un continu estimat per un denominador gaussià. Dins la Lluna, sense suport, el denominador era zero i soroll molt baix dividit pel terra 1e-8 es convertia en opacitat 1. S'ha restringit la cobertura a la validesa del mateix denominador, amb `min(den/1e-8,1)`. Es conserva el terra existent; no hi ha radi lunar nou. Canvien 549.816 píxels de la màscara del grup intern. Els set originals i la capa Divide són exactes.

Les correccions 2–4 són conjuntes. Restituir els 347 píxels deixant les interiors sota Earthshine (B4) ocultava contribucions de fins a 18.507 DN16 i es va rebutjar. Moure les interiors sense corregir la validesa C2 (B5) descobria taques fosques internes i també es va rebutjar. No són alternatives publicades.

## Validació i qualificació dels resultats

El protocol `research/tools/v63_encaix_contorn_20260913/C0_PROTOCOL.md` es va fixar abans de la validació final. Rebuts a `output/v63_encaix_contorn_20260913/`:

- `D1_integrity.json`: @CHECKS@ comprovacions de canals; 24 capes i IDs conservats; RGB i alfas de totes les fonts exactes, inclosos base/color acceptat i Earthshine. Només les vuit màscares principals declarades i la màscara del grup intern canvien. La selecció principal de Pere és exacta. Els set originals interns i Divide exactes. Màscares natives contra les calculades: màxim 1 DN16. Matriu exacta. ICC exacte. La previsualització transformada de l'objecte es regenera, com correspon a la seva màscara nova; no és RGB de font nou.
- `B6_foreground_validity.json`: 1.376.725 píxels de primer pla de la fotografia original amb maxRGB ≥ 0,05 conserven la cobertura exacta. El fons sense continu vàlid té RGB màxim 0,007599. No es proclama nova mesura física d'opacitat en senyal feble.
- `C1_foreground_checks.json`: 1.411.784 píxels transformats dins el suport de la fotografia original més la petjada de remostreig de 3 píxels. RGBA natiu abans/després **0 DN16**. La selecció d'interiors inclou 3.850 píxels abans atenuats per Earthshine; la nova disposició no torna a multiplicar-los per aquella màscara. És una prova de transmissió del mateix primer pla, no d'informació solar nova.
- La primera implementació del control C1 va prendre la brillantor de la previsualització transformada antiga com a jutge i va fallar. Hi havia **18 valors espuris brillants dins fons lunar fosc**, amb veïnatge 7 × 7 de la fotografia original ≤ 0,004700. S'han catalogat a `C1_invalid_background_outliers.json`. El control correcte usa el primer pla de la fotografia original que especifica el protocol, amb la mateixa tolerància 4 DN16; no la brillantor del proxy afectat. Els 18 valors no es declaren estructures solars conservades: provenien del fons invàlid. No es canvia cap llindar per obtenir PASS.
- La identitat V62 de recomposar tota la fotografia sobre negre a 0 DN16 queda **qualificada**: també incloïa soroll/fons lunar amb opacitat indefinida. V63 conserva els originals editables i el primer pla solar comprovat, i retira la influència d'aquell fons com si fos primer pla solar.
- `C1_foreground_checks.json`: cobertura del ROI lunar 1.465 píxels no opacs → 0; el contorn final és igual sobre fons blanc o negre. No equival a una prova d'absència de tots els halos.
- `D2_VISUAL_REVIEW.md`: revisió real de tots els sectors marcats, 360 graus i llenç. Millora clara al peu superior i oest; canvi petit a diversos punts inferiors i SE. El filet fi residual queda declarat.
- El model exploratori B0 no reproduïa exactament la composició en transparències parcials (màxim 3.658,95 DN16). No es fa servir com a prova de fidelitat final; la prova final és la recomposició nativa.
- Porta obligatòria: **@GATE@**. Segon lector: `@READER@`. ImageMagick etiqueta genèricament sRGB; el perfil efectiu verificat amb els bytes ICC i Photoshop és Adobe RGB (1998).
- `E2_final_open.log` i `E3_final_readback.json`: fitxer publicat reobert; recomposició forçada sobre còpia pròpia de totes les capes; exportació de tot el llenç contra candidata nativa, màxim **@READBACK@ DN16**. Exterior del ROI lunar, respecte de V62: **@EXTERIOR@ DN16**. Fitxer publicat continua amb el mateix SHA després de reobrir.
- Observació auxiliar de finestra: @UI@. Les previsualitzacions inspeccionades provenen dels exports natius, no d'una captura de pantalla inventada.

La correcció del color coronal acceptada per Pere manté la validació Sony de V62 i el RGB exacte. Les proves noves són de composició, suport i retenció fotogràfica. No substitueixen un jutge astronòmic entre trens i instants, ni permeten declarar resolt aquell registre absolut. No s'han modificat RAW, reconstruccions independents d'Earthshine o la cadena científica.

## Represa exacta

- Producte vigent general: V63 indicat a dalt. Earthshine independent continua V56, SHA `edee45ad76f08f8450beed3e85ed0d226eb0b1e11347478d2e998d74281ce12e`.
- Font V62: `.../Capes Totals/V62.psb`, SHA `6f6d1ae849f0524a5479857a8b1c212094d12469322e8f9c0c582c88592efdc3`; còpia exacta `output/v63_encaix_contorn_20260913/V62_input.psb`.
- V61 simplificada per Pere, 24 capes, es conserva; no restaurar les capes que ell havia suprimit. Font de la selecció: la seva màscara de V61, normalitzada a V62 i exacta a V63.
- Productor final: B0 màscares dels sis filtres; B1/B2 cobertura; B6/B7 validesa del grup; D0 nom i desament Photoshop; D1 fidelitat; E0 publicació; E1 porta i lector; E2/E3 reobertura completa.
- `V63_pilot.psb` és la font desada nativament del producte. `V63_pilot_serialized.psb` és una prova de serialització invàlida: no publicar-la. psd-tools escurçava el bloc lnk2 116 bytes; B3 conserva el bloc natiu i el fitxer final s'ha desat de nou amb Photoshop.
- Matriu d'interiors exacta: `[905.1545006775716,400.5652578211652,9417.128639148827,421.5477742709833,9400.647306326518,7107.527460574883,888.6731678552641,7086.544944125065]`.
- Pendent de judici visual de Pere: detall de les perles, peu superior i transició fina residual. Si cal continuar, investigar la font i el suport/temps abans de modificar geometria; no convertir la millora fotomètrica NW en prova de rotació o escala.
- Cap decisió addicional de mescla pendent: Pere ja l'ha indicada amb la màscara. La continuació autoritzada no requereix un altre «ok» entre pilots acotats.
- Manifest: `research/tools/v63_encaix_contorn_20260913/delivery_manifest.json`. Rebut d'autoritats: `output/v63_encaix_contorn_20260913/E5_authorities.json`. Alliberament: `output/v63_encaix_contorn_20260913/E6_release.json`; consultar-lo per l'estat del claim.
