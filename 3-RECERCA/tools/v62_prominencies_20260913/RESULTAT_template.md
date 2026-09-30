# Capes Totals V62 · color de la corona i composició de les protuberàncies

13-09-2026. Versió revisable amb dues correccions principals; **el contorn fi i l'encaix local NW continuen oberts**. No es declara absència global d'artefactes ni recuperació nova de resolució lunar.

## Producte i autoritat

- Producte: `@PRODUCT@` — SHA-256 `@SHA@`, @BYTES@ bytes.
- Mateix llenç 10551 × 7506, RGB16, Adobe RGB (1998). 24 capes de primer nivell.
- Font autoritzada: **V61 simplificada i anotada per Pere**, SHA `63d4c0dcab0e2b09dd7797c6c0854b21702cde35d1d8322fc0acb16840400221`, 10.814.374.190 bytes. El V61 anterior de 27 elements ja no és la font de muntatge.
- Font de Pere intacta al seu lloc i instantània exacta a `output/v62_prominencies_20260913/V61_Pere_input.psb`. Les capes eliminades per Pere no es recuperen.
- La màscara lunar modificada per Pere (3.633 píxels respecte del lliurament anterior), RGB, alfa i geometria d'Earthshine es conserven exactes. El producte independent Earthshine_V56.psb també conserva SHA `edee45ad76f08f8450beed3e85ed0d226eb0b1e11347478d2e998d74281ce12e`.

## Correcció del vermell ample, a l'origen del color

El productor de la base V42 calcula un camp de color amb un gaussià de sigma 24 píxels. Això escampa el color de les protuberàncies i la cromosfera sobre la corona contigua. El productor antic es reprodueix dins de 0,513 DN16: és una causa confirmada del vermell ample d'aquest muntatge, no una interpretació basada només en l'absència aparent en una altra fotografia.

`c1_colour_final.py` exclou del càlcul d'aquest camp 7.154 píxels de font amb R/G > 2,5, mantenint el mateix sigma i la resta de la recepta. Els nuclis emissors es conserven exactes; cap font RAW ni el detall de luminància dels filtres es modifica. La luminància lineal de pantalla de la base es conserva amb error màxim 0,000011385 per quantificació. Canvien 321.116 píxels RGB de la base; la màscara, l'alfa i la geometria són exactes.

Sony queda reservada com a contrast extern i no entra al productor. La igualació global de color es calcula fora de les marques. En corona tranquil·la amb contribució Vixen > 0,999, l'error mediana absolut de log-color R baixa de 0,302499 a 0,031414 a l'oest (11.979 píxels), i de 0,286428 a 0,023990 a l'est (2.231 píxels). B baixa de 0,147842 a 0,012387 i de 0,143065 a 0,040604. Rebut: `C1_colour_validation.json`.

La capa es diu `00 Base corba · color coronal sense difusió vermella · V62`; deriva de `00 Base corba · limbe corregit V56` i conserva la seva geometria.

El vermell de les protuberàncies és radiació del plasma i inclou H-alfa; la [NASA descriu el plasma i el seu aspecte vermell](https://www.nasa.gov/image-article/what-solar-prominence/). Això no prova que tota llum vermella difusa sigui impossible, ni que la formació de les línies no tingui contribucions d'il·luminació solar. La correcció aquí és concreta: retirar una extensió introduïda pel càlcul del color. La fotografia concreta de Druckmüller no s'ha fet servir com a font ni com a patró de píxels.

## Interiors i pedestal negre

`Interiors 06–12 · protuberàncies de Pere · V62` queda visible amb la selecció que Pere ha pintat. La seva màscara tenia un pedestal uniforme de 386 DN16 (0,589 %) també fora dels traços; es normalitza a zero mantenint els traços blancs i la seva gradació relativa. Això retira la contribució feble no seleccionada de les interiors sobre tota la corona.

Dins l'objecte intel·ligent es mantenen exactes les set capes 06–12, amb els seus RGB, alfa, màscares, modes, opacitats i geometries. S'afegeixen un divisor gris editable i una màscara de grup que separen el fons negre de la fotografia abans de compondre-la amb la corona real. La cobertura deriva del component fosc connectat al centre i del continu local verd (sigma 8, suport a més de 5 píxels, transició màxima de 10 píxels), limitada per maxRGB per evitar retalls. No s'infereix un radi lunar nou a partir de la vora fosca revelada.

És una operació de composició fotogràfica, no una nova estimació de radiància. La prova nativa sobre negre reprodueix **exactament, 0 DN16**, els quatre milions de píxels RGB originals de la regió de 2000 × 2000. La cobertura nativa coincideix dins de 2 DN16. Això valida la conservació de la fotografia; no és una validació física independent de tot el contorn. El pedestal negre angular sota la protuberància superior desapareix en el compost sobre la corona. Hi queda un filet clar fi.

La matriu de l'objecte és exactament la de la V61 de Pere: cap nova rotació, translació ni escala. La prova de similitud només demana escala 0,999586 i gir relatiu −0,002724 graus; no es promou. Reduir globalment un 1 % empitjora molt els ancoratges oest i sud-est. La protuberància superior reservada manté correlació 0,8356. **NW no concorda** amb la base (correlació −0,023 amb l'encaix actual): no es declara alineament perfecte a tots els sectors ni s'aplica una deformació local per ocultar-ho. Vegeu `B0_geometry.json`.

## Revisió visual de les marques

| Zona de Pere | Resultat V62 |
|---|---|
| Blau superior, x5259–5300 / y3326–3341 | Pedestal negre corregit; filet clar fi encara present. |
| Blau NW, x4995–5041 / y3471–3530 | Fons negre reduït; vora clara/rosada visible i encaix local pendent. |
| Blau oest baix, x4920–4983 / y3812–4007 | Mescla més contínua; filet clar al costat lunar encara obert. |
| Blau SE, x5785–5803 / y3936–3973 | Vermell ample reduït; punt fi del contorn no declarat resolt. |
| Sis petits blaus inferiors, x5032–5301 / y4071–4221 | Sense millora decisiva demostrada; pendents. |
| Verds oest i est | Extensió ampla de color reduïda i contrastada amb Sony reservada. |

Revisats el llenç complet, els deu blaus i els dos verds. Vistes a `output/v62_prominencies_20260913/vistes/`. La capa `Marques de Pere · V61` es conserva exacta, oculta per a la presentació. Les geometries i els RGB dels filtres són exactes respecte de la V61 de Pere.

## Validació del fitxer

- @CHECKS@ comprovacions de canals de les capes principals i dels set originals incrustats; conservació exacta llevat dels canvis declarats de RGB de base i màscara de selecció. Rebut `E0_integrity.json`.
- Photoshop real: `@GATE@`.
- Segon lector: `@READER@`.
- Reobertura del producte publicat i recomposició forçada en una còpia amb totes les capes: màxim **@READBACK@ DN16** a TOT el llenç RGBA. `E3_final_readback.json`.
- Producte publicat obert nativament a Photoshop al 100 %, desat, interiors visibles, marques ocultes: estat retornat per Photoshop a `E2_final_open.log`. La captura auxiliar de la finestra no s'ha pogut comprovar perquè el Mac està bloquejat; Pere ha rebut una petició per desbloquejar-lo. `E4_UI.json` declara aquesta limitació. La revisió visual del llenç i les marques s'ha fet sobre les exportacions natives, i la reobertura publicada coincideix exactament amb aquestes.

## Proves no promogudes i trampes de represa

1. Retallar negres només per llindar deixa un filet fosc separat. B2 rebutjada.
2. Integració de la màscara lunar per àrea de píxel: no hi ha millora visual decisiva dels blaus. C3/D7 no promogudes; la màscara de Pere es manté exacta.
3. Retallar tots els filtres a la base tampoc resol el filet fi. D7 correcte només canvia 600 píxels més de 4 DN16. No es promou.
4. El primer pilot D5 no és vàlid perquè `grouped=true` a Photoshop activa capes ocultes. D7 restaura explícitament les visibilitats. El primer pilot D6 de màscara tampoc és vàlid perquè `layer.bounds` reflectia la màscara visible i va moure el RGB; D7 desactiva la màscara per mesurar els límits RGB abans de posicionar. Cap pilot invàlid entra al producte.
5. `psd-tools` reescrivia el bloc natiu `lnk2` 116 bytes més curt i Photoshop refusava `V62_work.psb`. **No usar aquest fitxer.** D3 preserva íntegrament el bloc natiu, i D4 obre, substitueix el contingut incrustat, força actualització i desa el producte amb Photoshop.
6. Photoshop retalla la màscara de grup a [4015,2901,4943,3829] amb fons blanc 255. L'auditoria compara en coordenades de l'objecte i comprova també el fons exterior; no exigeix les dimensions de l'array provisional. No s'ha canviat cap tolerància per obtenir PASS.
7. Fer servir `with timeout of 3600 seconds` a AppleScript: un timeout del client no atura un JSX ja en execució. Verificar el log abans d'enviar una altra mutació.

## Represa concreta

Arrel de codi `/Users/USUARI/Downloads/Eclipse 2026`. Producte vigent @PRODUCT@; productor i scripts a `research/tools/v62_prominencies_20260913/`, dades i rebuts a `output/v62_prominencies_20260913/`. Protocol congelat `C0_PROTOCOL.md`. Manifest `delivery_manifest.json`. Handoff `.coordination/HANDOFF_2026-09-13_CODEX_CAPES_TOTALS_V62.md`.

La següent investigació ha de separar l'encaix temporal/fotomètric NW i el filet fi del contorn, preservant els ancoratges que sí concorden i l'elecció de protuberàncies de Pere. Cap tria de mescla pendent: Pere ja l'ha indicada amb la seva màscara. No ampliar/reduir el disc globalment ni retocar localment la vora per fer desaparèixer una discrepància sense causa i validació noves. El judici visual de Pere i la resolució completa dels blaus continuen oberts.
