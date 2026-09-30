# V64 · cobertura del contacte lunar revisada; registre absolut encara qualificat

Producte revisable de Photoshop: **@PRODUCT@**. SHA-256 `@SHA@`; @BYTES@ bytes. Mateix llenç 10551 × 7506, RGB16 Adobe RGB (1998), **25 capes arrel**. Les tres marques verdes es conserven a la capa 87, oculta. Cap versió anterior sobreescrita.

## Què canvia

La màscara del grup incrustat Interiors 06–12 estima ara el continu de cada exposició abans de combinar-les amb els pesos originals. El mètode anterior estimava el continu després de barrejar exposicions amb nivells molt diferents: al peu superior, el llindar del 50% de l'opacitat quedava **4,666 px** més enfora que el de la màscara lunar. La foto 12 mateixa, en canvi, quedava a −0,197 px segons el mateix detector. Aquesta discrepància és una causa mesurada del pedestal blanc i de la protuberància aparentment flotant.

La nova cobertura només augmenta quan almenys dues de les tres fotografies curtes 12/11/10 tenen senyal per sobre del fons negre mesurat. Es preserva l'exclusió anterior de fons sense continu vàlid. No s'ha ampliat circularment la Lluna ni s'han pintat píxels al contacte. El productor incrementa 40.797 píxels de la màscara; zero reduccions respecte de la màscara nativa original abans de la interpolació de Photoshop. La quantització nativa es comprova separadament dins 2 DN16.

| Marca | Revisió nativa de V64 | Sensibilitat de la vora 50% a les proves de paràmetres |
|---|---|---:|
| 1, superior | El peu vermell arriba al disc; el pedestal blanc ample queda retirat en la vista ampliada. | 0,075 px |
| 2, NW | Franja pàl·lida reduïda i contacte vermell més continu. | 0,042 px |
| 3, perles oest | Reduïda la franja blanca difusa; es conserva la línia brillant de les perles de la fotografia. | 0,392 px |

El perfil puntual natiu D10 confirma, al centre de cada marca, les diferències entre els llindars 50% d'Interiors i la màscara lunar: superior −0,021 px, NW +1,509 px i perles oest −0,376 px. La marca NW continua, per aquest detector, per sobre d'un píxel; no s'oculta aquest límit. B1 usa el perfil agregat i D10 el punt central, per això les xifres anteriors no són idèntiques.

Aquestes xifres són sensibilitat d'un llindar fotogràfic; **no són errors absoluts d'alineament físic**. La nova opacitat canvia la contribució de les fotografies al muntatge, no aporta resolució ni radiància noves.

## Geometria: què està provat i què no

La matriu comuna d'Interiors és exactament la de V63/V61 i conserva l'encaix relatiu V57 que Pere havia indicat com a referència. Les comprovacions locals d'estructures externes de 06–12 contra la base no justifiquen una nova transformació comuna: hi ha residus diferents segons exposició i sector, alguns no mesurables amb fiabilitat. Per exemple, els punts externs de la capa 10 donen aproximadament 0,4–1,4 px i diversos punts de la 09, aproximadament 2–3 px; altres ajustos arriben al límit de cerca i no són proves vàlides. Es conserven els resultats complets C2, sense convertir la correlació del limbe en un certificat. **No es declara que totes set exposicions estiguin alineades a ≤1 px amb la corona arreu.**

La còpia nova 83 permet identificar un desplaçament respecte de la mateixa foto 12: (−1,6521, +0,6008) px, +0,02042°, escala 1,0000593. Però la seva màscara l'amaga completament en la regió lunar: l'exportació nativa amb/sense aquesta capa és **exactament igual, 0 DN16**. Per tant, aquest desplaçament no causa el defecte visible de V63 i **no s'ha promogut cap transformació de la còpia**. La capa 83 original queda exacta, amb la seva màscara i geometria. El diagnòstic inicial que atribuïa el rectangle buit a una conversió incorrecta de Photoshop queda retirat: era l'efecte del seu emmascarament. Els intents D4/D4c es van desfer completament.

L'estimador geomètric C6/C7 sobre la còpia sense màscara passa identitat, una injecció coneguda i nul girat 180°. La cota d'error de la injecció és 0,000013 px davant el límit congelat 0,15 px; el màxim residu local de la còpia és 0,181 px. Això només valida la mesura entre dues còpies de la mateixa fotografia, i **no valida el registre astronòmic de 06–12**. C3 i C5 havien fallat el control 0,15 px (0,204 i 0,220 px); s'ha corregit el biaix de remostreig amb un model directe cúbic, sense canviar-ne el llindar.

## Preservació i proves

- Font de Pere: V63 de 25 capes, SHA `f3dc9afbc8e7e90aefbd853f8436975b4442d105d51aef2389b80a9bab277e0c`. Còpia de disc i còpia nativa de l'estat obert preservades separadament.
- **@CHECKS@ comprovacions de canals**: RGB/alfa de totes les fonts originals exactes; les set interiors i el divisor exactes. El color V62 acceptat és exacte.
- **Totes les màscares arrel de Pere són exactes**, incloses les noves edicions de 41, Earthshine 30 i selecció d'Interiors 76. Només canvia la màscara del grup intern declarada a D0/B6. La transformació de l'objecte 76 és exacta; còpia 83 exacta.
- Fora de la selecció d'Interiors de Pere, el canvi RGB natiu és 0 DN16 en la regió lunar; 60.409 mostres RGB canvien dins la selecció. Reproducció abans/després de desar: 0 DN16.
- La V63 marcada de Pere ja tenia 11.916 píxels de transparència parcial lleu a la regió lunar, mínim aproximat 99,2%. V64 conserva el mateix nombre de píxels parcialment transparents; la interpolació nativa varia l'alfa compost entre −12 i +118 DN16 (1.869 increments i 282 disminucions), sense crear nous píxels transparents ni reduir el mínim anterior. La monotonia del productor no s'extrapola al resultat de la interpolació cúbica de Photoshop. No són forats nous ni es declara opacitat total.
- Porta Photoshop: `@GATE@`. Segon lector: `@READER@`. Reobertura nativa i recomposició forçada de tot el llenç: **@READBACK@ DN16** màxim. Aquestes portes validen el fitxer i la reproducció, no el registre astronòmic.
- Revisades les tres marques ampliades, la circumferència completa i tot el llenç. No s'ha observat un anell nou a les vistes revisades. La finestra real de Photoshop s'ha observat amb AX i captura CUA: V64 al 100%, Interiors V64 seleccionada i marques ocultes. El primer intent CUA havia caducat mentre es desava; la comprovació final ha reeixit. Estat final: @UI@.

La correcció de color coronal acceptada manté el RGB i la validació Sony de V62. Les proves noves són de cobertura, suport fotogràfic, sensibilitat i reproducció nativa. No hi ha un nou PASS d'un jutge astronòmic extern sobre l'últim contacte temporal; no es declara absència global d'artefactes ni geometria absoluta resolta. El judici visual de Pere de V64 continua obert.

## Represa i límits

Fonts i rebuts a `output/v64_geometria_20260914/`; scripts a `research/tools/v64_geometria_20260914/`. B0 fixa el protocol; B1/B6 localitzen el problema i produeixen cobertura; C2 conté els resultats geomètrics qualificats; C3/C5 conserven controls fallits; C6/C7 només validen el diagnòstic de la còpia; D7 corregeix la seva interpretació causal. D6 comprova la integritat i E3 la reobertura.

No reprendre D4/D4c ni substituir la còpia 83 per cap fitxer auxiliar Copy12: són proves descartades. Tampoc usar `Interiors_V64_exposure.psb`, el primer prototip amb disminucions d'1 DN per quantització. La font promoguda és `Interiors_V64_exposure_monotone.psb`. B4 introduïa soroll interior i es va substituir per B6 amb corroboració en dues exposicions.

El document temporal `Interiors_V63_validity.psb` que Pere tenia obert amb canvis no desats s'ha deixat intacte: no s'ha aplicat al pare ni s'ha tancat. V62 i V63 de Pere es preserven. Si cal resoldre el registre físic restant, continuar amb correspondències externes reservades i compatibilitat temporal per fotografia; no deduir un canvi de radi o rotació del sol llindar de brillantor.
