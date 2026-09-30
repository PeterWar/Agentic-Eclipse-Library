# Handoff Earthshine V48 — 2026-09-11T17:01:55.833201+00:00

**Producte fotogràfic revisable lliurat:** `/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors/Earthshine_V48.psb`. SHA `48715be427ebd5ea654eeea746e0a295201f9f0a354e4f5e37fbf40df47443a5`; 25 capes RGB16, 10551×7506. Photoshop/readback PASS màxim 3 DN16. Les 24 capes originals, màscara i geometria queden preservades; les fonts antigues continuen disponibles. V48 oberta, document 1297 desat. Documents originals 79/140 sense desar i intactes; V46/V47 i els 88 RAW verificats per SHA, tres XMP exactes.

Informe: `/Users/USUARI/Downloads/Eclipse 2026/output/earthshine_detail_20260911/RESULTAT.md`. Cadena: `/Users/USUARI/Downloads/Eclipse 2026/research/tools/earthshine_detail_20260911/PIPELINE.md`. Manifest: `/Users/USUARI/Downloads/Eclipse 2026/research/tools/earthshine_detail_20260911/delivery_manifest.json`. Vista real Photoshop: `/Users/USUARI/Downloads/Eclipse 2026/output/earthshine_detail_20260911/vistes/C4_Photoshop_moon.png`.

## Estat i abast

- B0 renova 88 RAW (67 Vixen +21 Sony): radiància CFA ordinària, confiança separada, quatre mostres vàlides no saturades, negatius conservats. Mateixa geometria V45, calibració i rellotge. Sis controls exactes. No nous desplaçaments globals inferits de la vora aparent.
- B1 és font Vixen sola amb compositor fix C0 de V47; B2 és Sony separada. La V48 conserva l'estructura ampla de Pere (ja contenia Sony) i substitueix la part fina amb B1 abans de Camera Raw. Mateixa calibració tonal global congelada; cromaticitat original exacta abans de quantització. Cap retoc espacial ni màscara nova.
- Irregularitat de font: mediana 0,25048→0,22112 px, 21/24 sectors milloren; empitjoren 0°,330°,345°. No és una mesura suficient de resolució. El vel clar residual continua visible.
- B4 entre fonts independents: guany exploratori verd9,24–40 px,lineal/log. Cobertura per referència corregida: suport parcial a l'última franja 435–449 en dos sectors; regressió 120–150°,40–64,log,contra SA8. No recuperació uniforme.
- C6 és retenció fotogràfica, no independència entre trens: 0 pèrdues nominals vsV47 i 1 guany verd9,24–40,lineal. A0/A1 tampoc són prova independent perquè la foto conserva Sony. Els controls rotats i BH són exploratoris; no afirmació astronòmica calibrada.
- B7/B8 barreja directa de88 fonts: no promoguda. B6 moviment durant exposició: hipòtesi nominal, Vixen10s≈3,14–3,80px amb centres modelats. No PSF mesurada, cap deconvolució. Rebut `B6_REJECTED_cross_pointing.json` invàlid per barrejar apuntamentsSony.
- No PASS de recuperació completa del llimb, equivalència DHS ni injecció integral RAW/CFA/CameraRaw. Sliders històrics exactes no recuperats; estètica aproximada amb calibració global ja congelada. Capes Totals intacte.

## Represa acotada, sense nova confirmació

L'objectiu global continua actiu. La següent comprovació útil és mesurar resposta òptica i possible moviment a partir de perfils complets vàlids de preses curtes amb els CFA nous; separar perfil d'il·luminació de registre lunar per textura. Un model nou ha de predir captures reservades i passar una injecció en el domini de la font abans de substituir V48. No repetir l'ajust PSF uniforme refusat, les translacions de vora lluminosa, el mosaic FFT64/pas8 ni cercar paràmetres indefinidament contra els mateixos jutges. Sense guany corroborat, conservar V48 i declarar el límit mesurat.

Sortides `/Users/USUARI/Downloads/Eclipse 2026/output/earthshine_detail_20260911`; Python `/Users/USUARI/.venvs/eines-ia-py312/bin/python`; c0→c1→c2→c3→c4→c5 C4→c6→c7→c8. Els scripts rebutgen sobreescriptura del PSB i PSD; llegir PIPELINE abans de reproduir. Noms heretats de B5: V45=fontV47,C5=fontV48. C6 inclou mapa de noms. Zero processos propis pendents al release; cap Git, maquinari o delegació.
