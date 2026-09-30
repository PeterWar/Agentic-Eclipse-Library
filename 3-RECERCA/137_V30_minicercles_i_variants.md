# V30 — minicercles suavitzats i variants ACHF

Lliurat el05-09-2026: `/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V30.psb`. SHA-256 `0d1f23fe5c56acf60bb35d3e24acea02fffaaf333d04d7a3aa17e0aac4f3f8c0`;
6,233,044,488 bytes; **10551 × 7506, RGB16, 30 capes**.

La capa03 nova redueix els arcs curts concèntrics; no se'n certifica
l'eliminació total. El llenç i el camp són els mateixos. V29 corregida queda
immutable, i totes les seves25 capes es conserven amb píxels, alfa i màscares
idèntics. Només s'amaga la03 anterior dinsV30. 01 i02 acceptades no canvien.

## Capes per provar

| Capa | Estat inicial | Ús |
|---|---|---|
| 03 ACHF azimutal8–128 · V30 | visible,38/255 Superposar | correcció moderada, sigma radial4px |
| 07 ACHF azimutal suau r8 · V30 | oculta,38/255 | substituir03 per suavitzar més; perd més detall intermedi |
| 04 ACHF micro1–16 · V30 | oculta,36/255 | substituir01; més pes relatiu del gra fi |
| 05 ACHF fi2–48 · V30 | oculta,36/255 | substituir01; alternativa més equilibrada |
| 06 ACHF estructura4–64 · V30 | oculta,36/255 | substituir01; reforça estructures més amples |

Activa una alternativa en lloc del seu pare per comparar a igual opacitat.
No s'apilen automàticament. Els números dels ACHF són sigmes dels kernels,
no vores d'una banda de freqüències pura. Les capes originals continuen
editables amb els seus noms i ordre relatiu. Estrelles i reflex queden a sobre.

## Causa i correcció

Les11 components blaves de `minicerclesConcentrics.psb` són a03;01 i02 no
contenen marques. Les marques localitzen quatre sectors; no són màscares de
correcció. S'han separat el pedestal HDR corregit a research/136, els perfils
radials i l'anisotropia del filtre. L'ablació d'H1 i splines més amples deixa
la major part dels arcs. El senyal cru angular Sony correlaciona0,988–0,998
amb les ondulacions dels sectors; no és principalment un anell global H1.

El kernel només angular allarga soroll tangencialment: el control de soroll
blanc amb llavor300506 dona correlació a retard8 angular0,4999 i radial
−0,00055; l'entrada plana dona zero exacte. Aquesta prova de kernel no és
una simulació completa del sensor. La correcció sigma4/sigma8 es calcula
sobre l'operador polar real amb `G_r(p*valid)/G_r(valid)`, abans de tornar
una sola vegada al llenç. Sigma0 reprodueix exactament el filtre V29 per tren.
Es conserven font corregida, contrast, tanh, S/N, H1 i suport temporal.

| RMS radial relatiu a V29, quatre sectors marcats | r4 | r8 |
|---|---|---|
| longitud4–32px |0,476–0,550|0,132–0,161|
|32–64px|0,858–0,880|0,557–0,608|
|64–128px|0,967–0,980|0,852–0,893|

R4 atenua aproximadament a la meitat les ondulacions curtes. No s'atribueix
tota potència atenuada a soroll. El jutge Vixen fix, sense suavitzar-lo amb
el candidat, conserva el guany coherent entre0,9981 i1,0031 a filaments
radials≥128px/tangencials100–300px de les quatre zones. És una banda
concreta; les textures tangencials20–100px són molt menys corroborades.

Injecció aparellada llavor300507, delta lnG=1e−4, a totes dues radiàncies
derivades, amb validesa i pesos fixats. Travessa l'operador, interpolació,
tanh, S/N, H1 refitat i clipping; delta abans de quantitzar. R4 conserva
0,967–1,011 a longituds radials96/160/256px, en quatre rangs1,2–7,5R.
R8 falla deliberadament el llindar0,90 a96px (0,873–0,891), passa a≥160px
i queda oculta. No és una injecció als RAW ni una MTF absoluta; es compara
amb la resposta de la mateixa cadena sigma0. Rebut complet a `cau/injection_receipt.json`.

## Variants del filtre fi: detall i textura

Sigmes efectius:04=[1,2,4,8,16],05=[2,4,8,16,32,48],06=[4,8,16,32,64].
Mateixa fusióTOTAL V29, perfils de contrast, medianaRGB, S/N i H1. La ploma
és a la vora física exterior,3·sigma màxim; el forat lunar només s'omple
en la màscara auxiliar de distància, mai en radiància o validesa.

Comparació a1,6R, mediana quatre finestres, RMS relatiu a01:

|Variant|4–8px|16–32px|32–64px|64–128px|
|---|---:|---:|---:|---:|
|04 micro|1,047|0,908|0,782|0,532|
|05 fi|0,950|0,961|1,055|1,253|
|06 estructura|0,842|0,941|1,056|1,281|

Vixen×Sony fixos a1,6R corroboren16–32px r=0,658 i32–64px r=0,749;
a2,6R32–64px r=0,483. A4,2R la correlació4–64px ronda zero: el reforç
exterior de05/06 és contrast de textura majoritàriament no corroborada,
no més corona resolta. Manca de correlació no classifica cada píxel com a soroll.
Finestres a1,6/2,6/4,2/5,5R i angles−70/−155/−10/100 graus;256px a1,6R,
512px a la resta; exclosesNE/S a5,5R per falta de coberturaVixen. FFT2 amb
pla retirat i Hann2D. Fonts fixes `v29/cau_final/vixen_total.npy` i `sony_B_total.npy`, canalG.

## Portes i inspecció

H1 sobre uint16 observat en200 anells; pic geomètric0° als cinc candidats;
quinze controls en total (±1°/180° per cadascun dels cinc candidats) rebutjats. H1 màxim:
r4=0,003517, r8=0,005241,04=0,003319,05=0,005745,06=0,003044.
H1b avisa a r4=2,023308,05=2,179758,06=2,720704; r8=1,881720 i04=1,355328.
No s'han amagat aquests avisos amb osques o retalls. S'han inspeccionat
llenç sencer, quatre limbes, quatre sectors marcats, filaments i variants al100%.
Hi ha textura residual i el limbe de presentació heretat; no s'afirma absència
de tot artefacte. Les vistes són a IA/output/v30_20260905.

Suport03 exacte70.395.267px,40.860 dins1,05R. Variants01:70.395.270px,
40.863 interiors. Fora suport els ràsters són32768; fora màscara03 la
diferència del compost és zero. No hi ha retall circular nou ni nou halo de
màscara detectat a les vistes. Metadata global/ICC preservats.

PSB reobert:tots els canals de les25 capes originals, alfa i màscares idèntics,24 registres
complets idèntics;03 antiga només canvia visibilitat. Cinc ràsters nous i
màscares exactes. Recomposició a partir de capes reobertes≤1DN16 per canal,
p99=0; merged coincideix exactament amb el previst. Photoshop real:
**OBRE 10551 px x 7506 px · 30 capes**, document propi tancat sense desar i diàlegs restaurats.

Color de display a1,2–1,8R, exclòs clipping: R/G=1,27521, B/G=0,52573,
1.097.806px. No són mesures fotomètriques dels RAW. Base, CIENCIA i corba
de to s'hereten de V29; no s'ha fet una calibració nova.

## Brno i vara única sobre compostos reals

`compare_brno.py` llegeix merged REALS V27/V28/V29 abans03, compost V29
corregit i V30. Els fingerprints són a `cau/brno_comparison.json`; registre
fix+46,58738327°, mateix centre/FOV. sRGB descodificat als dos costats,
luminància(R+2G+B)/4, suavitzat angular normalitzat pel suport.
Mediana radial de la mitjana Pearson amb les quatre referències disponibles;
valors1° /4,5°:

|Producte|1,2–3R|3–5R|5–9R|
|---|---|---|---|
|V27|0,9625/0,9673|0,5033/0,5275|0,2713/0,3156|
|V28|0,8713/0,8766|0,4314/0,4207|0,0722/0,1702|
|V29 abans03|0,9717/0,9723|0,5295/0,5085|−0,0971/−0,1070|
|V29 corregit|0,9723/0,9729|0,5284/0,5087|−0,0985/−0,1081|
|V30|0,9724/0,9728|0,5340/0,5091|−0,0988/−0,1076|
|Brno×Brno|0,9923/0,9941|0,3799/0,3627|0,0407/0,0419|

V30 millora una mica3–5R respecteV29; no supera V27 globalment. A5–9R,
nulV30=0,2154/0,2778 supera la correlació; queda manca de validació exterior.
Brno és heterogeni: a3–5R les referències200/400/530/800mm donen ambV30
0,77458/0,75392/0,73045/−0,07537 a1°. Cobertura parcial a finals de camp;
Brno×Brno no és un sostre matemàtic. No es retalla dada per aquest resultat.
Aquesta vara angular no valida la resolució dels minicercles. Les versions
V25/V26 de geometria incorrecta queden com a història, no se'ls força el
mateix registre. Els màsters i altres productes lunar/estel·lar tenen les
seves vares; aquesta taula cobreix la branca de compostos amb geometriaV27.

L'antic `etapa6_compara_brno.py` sempre recompón fontsV27: l'etiqueta de
sortida no en canvia els inputs. No es pot usar per certificarV30.

## Procedència i reconstrucció

Manifest: `research/tools/v30/delivery_manifest.json`; conté hashes de
V29, fonts, radiàncies, ràsters i scripts. Entrades congelades a `v30/cau`,
pilotsH1 a part. Ordre i precaucions no-clobber al handoffV30. Scripts:
angular_pilots→fine_variants→inject_angular→build_previews→compare_brno→
package_v30→verify_v30→photoshop_gate→finalize_delivery.

Skills `corregeix-artefactes` i `postprocessat-corona` actualitzades i
sincronitzades aCodex: família anisotropia, transferència, jutge fix i
precaució explícita que les retallades circulars probablement fan més mal
que bé. Reconciliació documental a research/138. No s'ha tocat cap RAW,
run immutable, càmera/PTP ni el diari deClaude.
