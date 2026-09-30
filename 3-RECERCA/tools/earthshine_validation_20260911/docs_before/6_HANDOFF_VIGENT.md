# Handoff — candidat Earthshine a l’origen, C5

Continuació autònoma de Pere, sense confirmacions entre assaigs. Goal actiu. Cap versió fotogràfica nova publicada; **no marcar-lo complet**. Preservar Camera Raw i originals; correcció a l’origen, no retoc de màscares. Sense Git, maquinari, agents nous o accions destructives.

Represa directa: `/Users/USUARI/Downloads/Eclipse 2026/output/earthshine_reconstruction_20260911/RESULTAT.md`. Codi del mateix nom a `research/tools`; manifest al directori de codi. El següent pas és validar el candidat existent, no reobrir tota la recerca ni repetir sensibilitats.

## Candidat fixat

`C5_signed_frequency_compositor.npz`, camp `band8_16`. 67fonts Vixen, sis nous renders RAW al rectangle1400; Sony només jutge. Poisson de gradients observats amb longitud8; només escales fines a la sortida, transició cartesiana8–16 en asinh(G/20); radiància transformada gruixuda de la suma67 exacta. Cap canvi de radi, màscara o textura externa. Mescla lineal C4 refusada per ringing negatiu. C3 gradients a totes les escales refusat per regressions de textura.

Pilot superior comparable: V45Vixen salt91,22%/irregularitat0,379px; suma67 78,32%/0,260px; C5 59,37%/0,180px; presa curta58,94%/0,160px. No minimitzar el salt real a zero.

Nou registre de les ales no saturades: correccions només2977/2978 respecte de2976, incorporades abans de l’únic remap CFA. B1: cicle0,326px, inversió0,471px (límit0,5), contrast amb vores òptiques completes0,163/0,049px. No és precisió absoluta ni PSF demostrada. 61fonts encara amb geometria V45. Fitxers B0/B1/B3.

## Portes obertes — no ocultar regressions

D2 compara les9marques verdes en4bandes, lineal/log, 11rotacions nul·les, LROC només jutge. Superior40–64: C5 passa V/SB8, V/L i SB8/L on V45Vixen no passava. Conserva els PASS de suma67 a40–64 en les9marques. Però respecte de V45 continua faltant el PASS lineal40–64 de marca3; V45 també conserva8–16 a marca6 ambSB8, lineal/log, que C5 no passa. C5 perd un PASS lineal24–40 de suma67 a marca3 ambSA8. No és cura global ni recuperació de tot l’últim llimb.

Continuar: validar altres sectors de vora, entendre regressions3/6 i injecció abans del CFA remap amb pesos recalculats. No triar altres paràmetres mirant repetidament el mateix jutge. C0 només tenia controls d’injecció després del remap i pesos fixos; no valen com a gate final. Cap PSB fins a fonts/estètica/gates pertinents.

## Camera Raw i Photoshop

Source `/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors/Earthshine_V46_Detall.psb`, SHA0af484cb7f1919900a51267f053467974c57902414258e67f54fe98638d2eb3a.
Snapshot de l’estat obert actual `output/.../V46_Detall_live_source.psd`; capa21 pel nom `V45 font G · dos trens · preferència temporal · vel present`. L’arxiu antic `research/tools/v46_earthshine_20260911/V45_live_source.psd` té26capes i la capa equivalent és23. Seleccionar sempre pel nom, no per un índex heretat.

`Previous.xmp`12:19 conté exposició−2,10/ombres−100/blancs16/negres40/textura100/claredat40/LNR69/monocrom. No equivalència provada. A4 context complet: mediana548DN16, màxim1028; canviar negres35 o5 tampoc reprodueix Pere. No atribuir sliders inferits a l’usuari ni inventar una equivalència. Descriptors retornats poden ometre camps d’entrada. Fonts/prefs originals intactes, `Z0_preservation.json`.

Documents vius79 V45Fonts i140 V46Detall, tots dos24capes, saved=false. No desar ni tancar. CUA va denegar permís visual; no eludir-lo amb captures/teclat alternatius. L’API nativa de documents establerta al projecte (`photoshop_api.py`, osascript/do javascript) funciona en còpies/arxius temporals. No s’ha fet una porta Photoshop de lliurable.

Un sol escriptor; alliberament explícit en CODEX_STATUS amb zero processos propis. Intèrpret `/Users/USUARI/.venvs/eines-ia-py312/bin/python`, PYTHONDONTWRITEBYTECODE=1, OPENBLAS_NUM_THREADS=1. El claim dels scripts és `CODEX_EARTHSHINE_RECONSTRUCTION_20260911`; adaptar-lo de manera declarada en reprendre amb claim nou.
