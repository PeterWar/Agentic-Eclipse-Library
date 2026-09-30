# V60: anell verd i cremallera lunar de la V59

Producte: `@PRODUCT@` · SHA-256 `@SHA@` · @BYTES@ bytes. 31 capes, 10551 × 7506, RGB16, Adobe RGB (1998). V59 de Pere preservada exactament; la capa superior de marques es conserva oculta. Oberta a Photoshop per revisar-la.

## Canvis

**Verd.** Les màscares de protecció retiraven el detall i també l'enfosquiment mitjà dels 2 NRGF i 4 RHEF en mode Multiplicar. Per això fins i tot un filtre constant produïa un anell clar. S'ha separat el nivell mitjà de la protecció del detall en aquestes sis capes: el nivell continua fins al límit físic de la base, i el detall conserva la protecció V58. La continuació usa una mitjana normalitzada sigma16 de píxels vàlids exteriors; no ajusta cap radi ni modifica la radiància de la base. Només canvia una regió de 41.870 píxels per filtre, on la protecció lunar prèvia és inferior a 1 i la base té suport. La protecció cromàtica de perles/protuberàncies es manté exactament. C0, que també n'abaixava el nivell, es va refusar visualment; C2 és el productor final.

El control amb filtre constant elimina el salt de guany als sectors reservats; 24/24 injeccions de detall conservat donen guany 1. El transport de les fonts fixes Vixen/Sony és idèntic on el detall és vàlid i no està protegit. Aquestes identitats comproven la composició i la no-regressió, no són una demostració de detall astronòmic nou dins de la franja protegida. Les cures dels anells periòdics i de les estrelles de V58 es conserven fora d'aquesta petjada. La base i les geometries de totes les capes són exactes.

**Lila.** La cremallera radial és a la màscara lunar heretada. `v44_earthshine_20260910/f5_render.py` produïa un pes fotogràfic per a suma additiva (`min(coverage,1-lin/outer)`); V45 el reutilitzà com a alfa NORMAL. S5 de V53 substituí només els últims 8–10 px pel contorn geomètric i conservà el pes interior. Aquest pes conté textura i una fuita radial fins al centre. La cerca inicial d'una costura al RGB no la localitzava: B3 mostra directament la forma a la màscara.

La màscara V60 és opaca a l'interior; conserva literalment els últims 3 px del suport existent i tot l'exterior. Els 622.471 píxels que realment canvien són a 9,055 px o més del límit: el contorn acceptat no canvia. El RGB lunar, l'alfa de capa, el revelat, l'escala i la posició són idèntics. No s'ha interpolat ni filtrat textura. El control amb fons injectat dona fuita 0; a la recomposició de Photoshop els 643.382 píxels de màscara opaca coincideixen exactament amb el RGB original. L'alfa del compost canvia a l'interior, precisament perquè es corregeix aquella transparència incorrecta.

**Blau: pendent.** La marca ocupa [4897,3535,4967,3744] en coordenades del llenç. Els 1816 píxels pintats tenen protecció lunar 1: són fora de la banda que ha originat l'anell verd. La inspecció separada de fonts i filtres no ha identificat una correcció simple validada a l'origen. La zona blava queda exactament igual, 0 DN16 de canvi; no se n'ha fet interpolació ni s'ha usat la pintura com a màscara correctora. `C4_blue_source_channels.png` és diagnòstic, no prova d'una causa única.

## Verificació i límits

- Photoshop: `@GATE@`; segon lector: `@READER@`.
- Reobertura i recomposició natives: màxim@READBACK@DN16 respecte del renderitzat anterior.
- 25 canals modificats redescodificats i verificats;128 canals restants exactes en bytes comprimits. Mateix ordre, opacitats, modes de fusió, geometries i estats de màscara. Només s'oculta la capa de marques.
- Fora de la ROI 2000 × 2000, canvi del compost 0 DN16. RGB lunar/base originals intactes. V59, V58 i Earthshine_V56 verificats per SHA-256.
- La memòria d'imatge fusionada conserva l'alfa nativa. Photoshop desa el RGB fusionat sobre blanc; el TIFF nadiu retorna alfa associada. S'ha verificat aquesta semàntica contra V59 abans de reconstruir la memòria. No forçar alfa opaca al llenç ni confondre la prova provisional amb el producte final.
- El fitxer independent `Capes interiors/Earthshine_V56.psb` es conserva intacte: la correcció de la màscara és dins de la V60 general. Si es reprèn el projecte lunar independent, cal incorporar-hi explícitament aquesta correcció, sense sobreescriure V56.
- No nova resolució lunar, equivalència DHS, recuperació absoluta del limbe ni absència de tots els artefactes. Els límits de V58, incloent el candidat estel·lar ambigu, continuen vigents. El blau i la revisió visual de Pere queden oberts.

## Represa exacta

Manifest: `@MANIFEST@`. Handoff: `@HANDOFF@`.

Productors: `b4_physical_mask.py`, `c2_keep_prominences.py`, `d0_build.py`, `d3_cache.py`. Les correccions parteixen de la còpia immutable `output/v60_marques_v59_20260913/V59_Pere_input.psb`. No executar scripts històrics per importar funcions: alguns tenen escriptures a nivell de mòdul.

Criteris previs: `A4_PROTOCOL.md` i `A4b_CAUSAL_PROTOCOL.md`. Proves: `B4_physical_mask.json`, `C3_frozen_controls.json`, `D4_native_review.json`, `D6_final_QA.json`, `E2_sources_unchanged.json`. Vistes natives: `vistes/V60_luna_1a1.png`, `vistes/D4_native_limbs_1a1.png`; causa de la cremallera: `vistes/B3_lunar_mask_leak_x200.png`.

Per al blau: comparar fonts/capes a la caixa fixada sense convertir la marca en màscara. La protecció lunar V58 no hi actua; distingir resposta de l'operador, protecció de protuberàncies i canvi real de font abans de proposar una cura. Cap correcció blava està promoguda.
