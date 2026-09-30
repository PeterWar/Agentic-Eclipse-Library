# V62 · prova de correccions després del diagnòstic exploratori

Autoritat: V61 simplificada per Pere, SHA 63d4c0dcab0e2b09dd7797c6c0854b21702cde35d1d8322fc0acb16840400221. 24 capes. No recuperar les capes eliminades. Mateix llenç, perfil i geometria solar/lunar.

B0: la similitud lliure demana escala 0,999586, no una reducció de l'1%; no es promou aquest ajust insignificant. NO inferir geometria de la vora fosca de la foto revelada. La comprovació NW no concorda amb la base: queda oberta, no es qualifica tot l'alineament com a exacte.

B1: reproducció del productor q24 dins 0,52 DN16; l'exclusió del senyal molt vermell del càlcul del color elimina la seva extensió ampla. Prova final fixa R/G>2,5 en la font Vixen que compon aquesta regió, només exclou del seu estimador de color, mai del producte. Conservar luminància de pantalla de la base. Conservar RGB de nuclis emissors amb protecció derivada de la font. Comparar amb Sony, igualació global de color mesurada fora de les marques i sense fer servir Sony per produir el candidat. No afirmar absència física absoluta de llum vermella ni usar Brno com a font.

B2 (només retallar negres): rebutjat, deixa un filet fosc separat. B3: pilot de despremultiplicació del fons negre, recomposició sobre la corona real. No és correcció del registre ni mesura nova de radiància. Prova final en coordenades ORIGINALS de l'objecte intel·ligent: component fosc connectat al centre maxRGB<0,05; continu local G amb gaussià8 i suport a més de5px del component; cobertura=max(maxRGB,G/continu), limitada a1 i canviada només a10px del component. Conservar exactament RGB*cobertura de la fotografia: no anul·lar llum baixa. Afegir divisor i màscara editables dins l'objecte, sense canviar els set originals. Matriu comuna existent preservada.

La màscara de Pere selecciona protuberàncies i perles; conservar traços i eliminar únicament el pedestal uniforme mínim de la màscara (0,00588998) si es confirma com a mode exterior. La màscara lunar de Pere es conserva.

Portes fixes: reproducció anterior<=4DN16; recomposició de la fotografia sobre negre<=4DN16 als píxels protegits; set originals exactes; mapa de cobertura coincideix dins2DN16; originals externs exactes per SHA; native Photoshop OBRE i segon lector; reobertura final<=4DN16. Verificació visual de TOT el llenç i cada marca. Si queda filet, declarar-lo: no canviar el jutge ni afirmar resolució completa.
