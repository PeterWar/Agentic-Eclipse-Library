# V68 · artefactes marcats a V67

Nova versió: **[@NAME@](<@PRODUCT@>)**. SHA-256 `@SHA@`.

La font és `/Users/USUARI/Downloads/V67.psb`, desada per Pere. S'ha congelat a `output/v68_artefactes_20260914/V67_Pere_input.psb`. El fitxer original i el document V67 obert amb canvis no desats s'han conservat. Mateix llenç de 10551 × 7506 píxels, RGB16, Adobe RGB (1998), 31 capes. Cap translació, gir, canvi d'escala o màscara nova.

## Marques i resultat

| Marca | Diagnòstic i correcció | Límit |
|---|---|---|
| Verda superior, x5357–5482, y3314–3334 | El mode Luz fuerte de l'earthshine reforçava una segona vora fosca en la superposició. Earthshine passa a Normal amb la mateixa cobertura i posició. | Vora fosca reduïda. La transició clara exterior molt fina continua visible; no se'n declara resolta tota la resposta òptica. |
| Dos punts taronja sud-oest, al voltant de (4993,4029) i (5010,4053) | L'exclusió que protegia les protuberàncies també havia exclòs aquests píxels de la correcció de llums altes V65. S'hi completa el mateix productor de color a partir del senyal lineal mesurat. | Es conserva el senyal de color i la forma fotogràfica; no es pinta el contorn. |
| Petit punt verd est, (5796,3954), 7 píxels de marca | Mateix mecanisme de llums altes. Inclòs en la correcció i en la comparació amb Sony. | No s'ha omès per la mida petita de la marca. |
| Marca taronja ampla a l'interior inferior | Component fi repetible fix al detector, principalment a escales de 4–12 píxels, fora del domini de la correcció anterior. Estimat en 12 fonts Vixen i transportat al revelat existent. | Reducció parcial de la trama, no eliminació de tot el gra. Les formes fosques amples tenen correspondència en les referències i es conserven. |

La interpretació de la marca interior és la trama fina. Es va demanar opcionalment si Pere es referia a aquesta trama o a la forma ampla; sense resposta, s'ha conservat la forma ampla corroborada.

## Evidència

- **Color:** 25.658 píxels RGB de la base modificats, sempre dins la protecció de color ja existent. S'utilitza la luminància anterior a V65 per evitar aplicar dues vegades la corba de llums altes. L'error de color davant la referència Sony disminueix als tres sectors: sud-oest, est i superior. Rebut `B4_colour_pilot.json`.
- **Patró fi:** estimació global a partir de fonts Vixen, amb separació d'escena i detector pels desplaçaments observats. Dues meitats temporals regulen quins components repetibles es poden restar. Sony, LROC i les marques no entren en aquest ajust. Protocol previ `B9_PROTOCOL.md`.
- **Revelat lunar:** resta igual als tres canals, entre −239 i +301 DN16, sense retall de rang. 630.705 píxels RGB modificats. La dispersió de la banda fina reservada passa de 81,46 a 70,98 DN16; és reducció de patró/soroll, **no guany de resolució**.
- **Validació externa de fonts:** correlació mediana amb Sony en la banda 8–16: 0,08193 → 0,09372; amb LROC: 0,26837 → 0,30603. El senyal 4–8 davant Sony continua massa feble per afirmar detall resolt. Les comparacions del revelat final amb Sony són de retenció, perquè aquest revelat ja conté una component ampla Sony.
- **Retenció:** 93 de 93 comprovacions prèvies conservades. Això no equival a amplitud exacta en totes les bandes: la menor relació d'amplitud fina és 0,826 després de retirar el component estimat. Les 12 injeccions diferencials amb operador fix passen; aquestes proves condicionals no substitueixen una reconstrucció independent completa des dels RAW.

S'ha rebutjat el pilot B5 de condició de contorn ACHF: sortia del rang vàlid i no millorava prou la marca superior. Cap canvi d'aquest pilot entra a V68. Els filtres NRGF, RHEF, ACHF, MGN i WOW es conserven exactes.

## Integritat i Photoshop

@CHANNELS@ comprovacions de canals. Totes les geometries, màscares i alfa originals són exactes. Les capes interiors i la fotografia de perles 96, les estrelles i el mapa ocult conserven tots els canals exactes. Es respecta la supressió de capes i les opacitats de Pere, inclosa la capa de perles al 89%. La capa de traces estel·lars continua oculta com a V67. La capa de marques es conserva oculta al capdamunt.

Només es modifiquen els RGB de les capes 3 i 30, el mode de fusió de la 30 i els noms corresponents. La cobertura del compost final és exacta; fora de la regió examinada de 2000 × 2000 píxels el compost canvia **0 DN16**.

Porta nativa: `@GATE@`. ImageMagick reconeix el PSB de 10551 × 7506 i 16 bits; psd-tools verifica els canals i el perfil ICC exacte. Reobertura i recomposició de tot el llenç: **@READBACK@ DN16** de diferència. El pilot retallat i el document complet difereixen @PILOTMAX@ DN16. El control matemàtic independent del pilot passa amb un màxim de 9,55 DN16 i percentil 99 d'1,01 DN16. Es va corregir el lector d'aquest control perquè el TIFF de Photoshop declara alfa associat; no es va modificar el llindar per fer-lo passar.

V68 queda oberta i desada a Photoshop. La verificació visual es basa en exportacions natives completes i ampliacions; la captura directa de la GUI no estava disponible. No es declara absència global d'artefactes, identificació dels petits relleus foscos com a cràters ni nou alineament astronòmic absolut.

## Represa

Codi: `research/tools/v68_artefactes_20260914/`. Evidència: `output/v68_artefactes_20260914/`. Seqüència: A1–A6 diagnòstic; B4 color; B9–B13 detector, transport, retenció i injeccions; D3 pilot; D4–D6 muntatge i integritat; E publicació i reobertura. B5/B7 són proves rebutjades i no s'han d'incorporar.

Conservar l'encaix manual de V67. Si es revisa la transició exterior fina, cal una nova prova causal i corroboració; no recuperar les matrius antigues ni ampliar la Lluna per ocultar-la. Earthshine V56 independent continua intacta.
