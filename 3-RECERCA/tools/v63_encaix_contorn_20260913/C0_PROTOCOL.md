# V63 · criteris de la correcció de composició

Font V62 SHA 6f6d1ae849f0524a5479857a8b1c212094d12469322e8f9c0c582c88592efdc3. Pere valida el color coronal sense reflex vermell. Mateix llenç, RGB16, perfil i originals. Tres diagnòstics causals: protecció antiga de la representació ampla sota la nova foto; doble cobertura parcial i forats de màscara; interiors sota Earthshine amb opacitat de fons negre invàlida dins la Lluna.

Correcció candidata conjunta: retirar la protecció antiga dels sis filtres multiplicatius només segons la selecció ja pintada per Pere; cobertura completa de base als 1.895 píxels on hi ha RGB vàlid sota una Lluna parcial; restituir només els 347 píxels de màscara lunar que Pere havia obert sense font coronal (tots opacs a la màscara anterior); interiors damunt d'Earthshine, preservant la seva selecció; restringir la cobertura calculada per C2 a la validesa del seu denominador, amb el mateix terra 1e-8, per evitar opacitat inventada al fons lunar negre. No tocar els set originals ni el divisor.

La restauració de màscara lunar NO és acceptable sola: B4 tapa contribucions vermelles de les interiors (fins a 18.507 DN16). Cal validar-la juntament amb la disposició de la font solar davant del disc lunar. B5 mostra que moure la font sense corregir la validesa C2 revela taques fosques internes; tampoc és producte.

Portes abans de publicar:

1. RGB i alfas de totes les capes de V62 exactes, incloent el color acceptat i Earthshine. Només vuit màscares principals i la màscara interna declarades; tots els altres canals/màscares exactes. Set originals interiors i divisor exactes. Matriu de l'objecte exacta; cap nova translació, gir o escala.
2. Zona de protecció dels filtres canviada només dins la selecció de Pere; no nous discs o plomes pintades. La prova és de composició fotogràfica, no nova informació astronòmica.
3. Nova màscara de base només on existien RGB coronal no nul i alfa de font completa; no interpolar dades. Els 347 píxels de màscara lunar ja eren opacs abans de l'edició que obria els forats; resta de l'edició de Pere exacta.
4. Denominador C2: tots els píxels fotogràfics maxRGB >= 0,05 han de conservar exactament la cobertura; zero anul·lació de cap component solar brillant. Native readback de l'objecte: error màxim 4 DN16 al primer pla vàlid. La identitat antiga de tota la foto sobre negre es qualifica: incloïa soroll/fons lunar que no és primer pla solar i l'alfa no hi estava definida.
5. Cap transparència residual al voltant de la Lluna en el compost natiu; comparar sobre negre i blanc. Control d'opacitat constant i resposta del primer pla: no tornar a multiplicar el detall de les interiors per la màscara d'Earthshine.
6. Revisió nativa del resultat, lent acumulada, tota la vora en polar i els deu blaus de Pere, perles i protuberància superior. Rebutjar nous anells, taques o estructures duplicades. No substituir aquesta revisió per una correlació del llimb.
7. Photoshop OBRE, segon lector, recomposició forçada després de publicar <=4 DN16 a tot el llenç. Originals externs SHA exactes. La concordança astronòmica absoluta de cada instant no es declara provada per aquestes portes de composició.

No hi ha cap nou ajust geomètric autoritzat per un resultat de correlació local a la vora; si encara es veu desajust cal investigar la font, no deformar-la.
