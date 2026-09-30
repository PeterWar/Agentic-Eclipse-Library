# Handoff Earthshine V47 — 2026-09-11T16:09:35.829276+00:00

**Producte fotogràfic revisable:** `/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors/Earthshine_V47.psb`. SHA `cd30789f64d4b6f736d176ff5eaac2f76a3ebbb546661d3b117462d26fca6227`. 25 capes RGB16; 24 capes de Pere exactes, màscara física heretada sense canvis, nova capa de detall fi de les fonts. Photoshop OBRE i readback PASS: màxim 4 DN16. V47 oberta per revisar; documents originals 79/140 preservats sense desar.

Informe complet: `/Users/USUARI/Downloads/Eclipse 2026/output/earthshine_validation_20260911/RESULTAT.md`. Cadena i controls: `/Users/USUARI/Downloads/Eclipse 2026/research/tools/earthshine_validation_20260911/PIPELINE.md`. Manifest: `/Users/USUARI/Downloads/Eclipse 2026/research/tools/earthshine_validation_20260911/delivery_manifest.json`. Figures: `/Users/USUARI/Downloads/Eclipse 2026/output/earthshine_validation_20260911/vistes`.

## Decisió i límits

- Es rebutgen els desplaçaments globals de la Lluna inferits de la vora aparent a la ronda anterior: perjudiquen la textura corroborada amb la Sony. V47 usa el registre de textura V45.
- C0: 67 fonts Vixen, sis amb CFA ordinari i validesa contínua, ponderacions temporals iguals entre dos estimadors previs. Compositor de diferències de fonts vàlides, asinh, Poisson 8 px i transició 8–16 px. Sony independent com a jutge, cap textura LROC/DHS introduïda.
- G: conserva l'estructura ampla del revelat anterior, substitueix el detall fi per la font recomposta a tot el rectangle i reaplica Camera Raw. Calibració de to global; cap màscara nova, cercle ni degradat manual. Capa original i retoc manual V46 queden ocults, disponibles.
- V47 millora visualment les dents i manté el to i textura general de Pere. La font original i la corona no s'han sobreescrit. Chroma original exacte abans de quantitzar; màxim 4 DN16 en Photoshop, 0 RGB on la màscara és zero.
- No es declara recuperació completa de tot el llimb ni resolució equivalent a DHS, ni recuperats exactament els sliders històrics Camera Raw. Controls C1/C3 amb regressions explícites; operador C4 passa injecció amb pesos fixos, no tota la cadena RAW.
- D/E són assaigs no promoguts. E tenia un identificador de capa duplicat i fallava la recomposició; G crea una identitat nova i passa. No reusar aquell patró de clonació.

## Represa

L'objectiu global de màxim detall continua actiu, amb una versió concreta ja lliurada. No cal nova confirmació. Primer jutjar el detall final G a les marques verdes amb les captures independents i determinar els límits S/N/llum dispersa. No tornar a fer ajustos globals amb la brillantor del llimb, ni una cerca oberta contra els mateixos jutges. No promoure recuperació només perquè el contorn sigui més suau. Conservar la V47 i el revelat de Pere.

Scripts c0 → g0 → g1 → g2 → g3 → g4 → f0 G4. Inputs i outputs a `/Users/USUARI/Downloads/Eclipse 2026/output/earthshine_validation_20260911`; Python `/Users/USUARI/.venvs/eines-ia-py312/bin/python`. Les sortides estan protegides contra sobreescriptura. Cap procés propi pendent al release; cap maquinari/PTP/Git, cap delegació.
