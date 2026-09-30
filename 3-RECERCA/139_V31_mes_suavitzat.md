# V31 — suavitzat dels filtres no azimutals

Lliurable: `/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V31.psb`. 10551 × 7506, RGB16, 30 capes; 6,193,861,172 bytes.
SHA-256 `bbbb2b93a49a0e09226b89467754f6364d1c6b929bc147bd34387a1c66d7affe`.

## Correcció de l'abast

Pere ha precisat: «els minicercles els veig només en els filtres que NO son azimutals».
V31 segueix aquesta observació: modifica01/02/04/05/06. Les capes03 i07 deV30
continuen exactament igual, inclosa visibilitat. El fet que les marques blaves
del document anterior fossin pintades a03 no identifica el filtre causant
quan es veu un compost de capes. La interpretació anterior deV30 no s'ha de
reutilitzar com a diagnòstic dels minicercles que Pere acaba d'identificar.

## Operador i selecció

Gaussiana cartesiana positiva sobre el detall relatiu al gris neutre:
`0.5 + G_sigma((F-0.5)*support)/G_sigma(support)`; fora suport,32768.
Entrada: RGB gris REAL delPSBV30 congelat. Cinc ràsters delpilot i els reals
coincideixen dins1DN16. No es refitaH1 ni contrast; cap tall circular, nova
màscara, reescalat, polarització o canvi deFOV. V30 queda immutable.

| Capa | Sigma px | H1 màxim | H1b |
|---|---:|---:|---:|
| 01 | 3 | 0.008812 | 2.951969 |
| 02 | 3 | 0.010079 | 1.807819 |
| 04 | 1.5 | 0.036522 | 2.293744 |
| 05 | 3 | 0.013298 | 2.134089 |
| 06 | 3 | 0.010796 | 1.573741 |

H1 comprova tots els píxels del suport en200anells, també els parcials del
limbe. Llindar0,05: passen els cinc.04sigma3 s'ha rebutjat perquè H1=0,075372;
04sigma1,5 passa amb0,036522 sense afegir recentrat radial. H1b>2 és un AVÍS
que es conserva; no s'ha declarat absència de tota estructura espúria.
Sigma5 es descarta visualment per pèrdua excessiva de detall. Sigma1,5 general
deixa més granulat; es reserva al filtre04més fi.

## Jutge fix i cost de detall

SonyBlnG FIX sense suavitzar; quatre finestres256×256 a1,6R dominades perVixen.
Retirada d'un pla, Hann2D, FFT2, bandes fixes i mediana entre finestres.
El compost comparteix fonts amb el jutge: aquesta comprovació entre trens
és útil a l'interior dominat perVixen, no una prova independent universal.
Rebut amb coordenades i totes les capes: `fixed_judge.json`.

01, sigma3: RMS restant8–16px=0.3028; component
coherent restant16–32px=0.7425,32–64px=0.9162,
64–128px=0.9846. Correlació16–32px
0.6599→0.6736. Es redueix també detall
real fi, no només soroll.04sigma1,5 conserva aproximadament93% del coherent
16–32px. Injecció additiva sobre el detall abans de l'únic operador nou a
`candidate_qa.json`; és transferència d'aquest suavitzat, no MTF delsRAW.

Brno usa els merged REALS deV30/V31, registre i referències congelats,
mateixa descodificació sRGB i mètodeV30. Pearson mediana a1° per1,2–3/3–5/5–9R:
V30=[0.9724007970390196, 0.533973445148664, -0.0987833363881781]; V31=[0.9732886908826874, 0.547895453407524, -0.08216373847003301].
El resultat exterior>5R continua sense validació i no prova el microgra.
Les referències només jutgen; mai aporten píxels.

## Integritat i inspecció

25 capes deV30 preservades íntegrament; cinc canvien nomésRGB i nomV31.
Alfa, màscares, opacitats, visibilitats i ordre dels30 elements intactes;
metadades globals intactes. Recomposició delPSB reobert≤1DN16.
Fora la unió de màscares visibles modificades: {'pixels': 8800536, 'max_DN16': [0, 0, 0]}.
Photoshop real: **OBRE 10551 px x 7506 px · 30 capes**. Document propi tancat sense desar; diàlegs restaurats.
Vistes a `/Users/USUARI/Desktop/Eclipse 2026/IA/output/v31_20260905`:
llenç sencer, quatre limbes, filaments i sectors marcats al100%.
Suavitzat visible, amb textura residual; acceptació estètica final dePere pendent.

## Reproducció

Manifest de fonts i hashes: `research/tools/v31/delivery_manifest.json`.
Intèrpret `/Users/USUARI/.venvs/eines-ia-py312/bin/python`, amb
`PYTHONDONTWRITEBYTECODE=1`. Ordre: pilot_isotropic → check_candidate →
package_v31 → verify_v31/fixed_judge/compare_brno_v31 → photoshop_gate →
inspeccióvisual → finalize_delivery. Els scripts refusen sobreescriureV31;
una reconstrucció requereix noves destinacions declarades en una còpia.
No s'han modificatRAW, runs, maquinari niCLAUDE_STATUS.
