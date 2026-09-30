# Hipòtesi geomètrica — protocol anterior als ajustos

Autorització de Pere: comprovar si els arcs reals són circulars i si comparteixen centre amb el Sol. No editar productes. Root únic escriptor.

Objecte principal: capes01/02 finals de V31, conservades idèntiques dins V31_FiltresPurs. Comparació amb residual abans d'H1 i deltaH1, ja congelats a v29/cau_final. La simetria d'H1 és un control de mecanisme, no una prova dels arcs de font.

Centre de referència solar (5361.768111973117,3775.747534140857), R440.60304883027544. Lunar C2 (5361.877319859359,3774.7412178166314). Separació1.012px; dispersió de punts del limbe no és incertesa del centre. No proclamar discriminació Sol/Lluna sense precisió suficient.

Mostra fixa de píxels CARTESIANS de l'anell de diagnosi2.5–4.5R, pas4px (coordenades enteres originals), sectors alterns de15° amb marges1.5°. La selecció de la mostra no canvia quan es mou el model. La cobertura de l'anell i els marges es verifica; no modifica cap màscara del producte.

Per separar gra/gradient, dues respostes diagnòstiques cartesianes fixes: Gaussian2−Gaussian16 i Gaussian8−Gaussian64, truncament3σ. No anomenar-les bandes Fourier ni portes de preservació. No s'apliquen a la fotografia. Es declaren perquè qualsevol filtre de diagnosi pot modificar el patró; controls recorren la mateixa cadena.

Model forward D(p)=s(t), t²=(p−c)' exp([[e1,e2],[e2,−e1]])(p−c). s és spline lineal de nusos2px; determinant1 evita degeneració d'escala. Comparar centre solar fix, cercle amb centre lliure±128px, el·lipse amb centre lliure i e1/e2±0.06. El radi de cada estructura queda contingut en s, sense radi predeterminat. No s'imposa cap pic d'entrada.

Ajust del perfil i geometria NOMÉS als sectors parells; mateixa família s i mateix suport per tots els models. Multistart en centre i forma. Predicció sobre píxels senars amb perfil/geometria congelats, sense ajustar amplitud ni fase. Repetir intercanviant sectors. Mesurar fracció de variància explicada, correlació i estabilitat del centre/relació d'eixos. Un mínim a la frontera o resultats molt discordants no determinen centre.

Controls: cercles sintètics descentrats, el·lipse, ondulacióm3 i soroll cartesià correlacionat, recorregut complet. Una geometria recuperada només al control no certifica els arcs de Pere. Si no hi ha perfil compartit predictiu sobre sectors reservats, no donar circularitat ni centre amb precisió falsa. Els desplaçaments radials reservats són només diagnòstic addicional, no correcció dels errors de predicció.

No es pot demostrar perfecció matemàtica amb píxels; la conclusió serà compatibilitat amb una geometria dins de la resolució/estabilitat mesurada, rebuig o resultat indeterminat.

## Extensió després del primer resultat

La capa01 no prediu un perfil radial comú als sectors reservats. Això pot deixar fora arcs locals de radi diferent segons sector. Afegir orientació local de crestes mitjançant Hessiana cartesiana a sigma3px: selecció d'anisotropia>0.6 i curvatura superior a la mediana d'entrenament, abans de cap ajust de centre. Comparar normals de les crestes amb gradient de la família cercle/el·lipse, centre lliure i sectors reservats. Puntuació cos(2angle) positiva=tangència circular, negativa=estructures radials. No seleccionar píxels segons si apunten al Sol. Controls de soroll/descentrament/el·lipse també passen aquesta branca. Aquesta mesura no prova la continuïtat d'un anell sencer ni que cada marca de Pere pertanyi a la component mesurada.

## Enduriment de la validació abans del resultat final

Els primers pilots queden SUPERSEDED. La cerca d'el·lipse s'amplia a una graella conjunta de centre i forma, perquè iniciar només al millor cercle no recuperava sempre el control el·líptic. Mostra final fine:12sectors de30°, marges9°; wide:8sectors de45°, marges15°. Orientació:24sectors de15°, marges2°. La separació mínima entre mostres entrenament/validació supera el diàmetre diagonal màxim dels suports de convolució; cap píxel de font és compartit entre sectors d'ajust i reservats per aquests filtres. La comprovació de suport passa a distància chessboard, coherent amb el nucli quadrat. Són comprovacions de separació de càlcul, no independència física de la corona ni p-valors calibrats. Els resultats finals es repeteixen amb aquests canvis.


## Extensió 07-09-2026 per observació de Pere

Absència visual dels arcs fins aproximadament un radi solar més enllà del limbe. Ampliar descripció d’orientació a1.2–4.5R, per franges, mateix sigma3 i selecció anisòtropa sense condicionar direcció. No ajustar un radi d’aparició ni confondre dominància radial amb absència d’arcs. Comparar amb transicions de codi i cobertura; cap canvi fotogràfic ni atribució causal sense intervenció.
