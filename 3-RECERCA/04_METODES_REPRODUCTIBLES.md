# Mètodes reproduïbles de processament

## Objectiu

No podem copiar Corona 6, LDIC 6 ni ACC 6.1. Sí que podem construir un procés:

- obert;
- documentat;
- reversible;
- validable;
- capaç de conservar un màster lineal;
- prou flexible per comparar diversos realçaments.

El criteri no és «que s'assembli a Druckmüller» a qualsevol preu. És que aprofiti la mateixa disciplina matemàtica i que sapiguem d'on surt cada detall.

## Arquitectura de dades

```text
00_RAW_IMMUTABLE/
01_CALIBRATION_MASTERS/
02_CFA_CALIBRATED/
03_RGB_LINEAR/
04_REGISTERED/
05_HDR_LINEAR/
06_LUNAR_STACK/
07_ENHANCEMENTS/
08_PRESENTATION/
09_QA/
10_MANIFESTS/
```

Cap etapa sobreescriu l'anterior.

## Etapa 1 — ingesta immutable

Per cada fitxer:

- copiar sense modificar;
- calcular hash;
- extreure EXIF;
- assignar cos, sèrie, òptica i targeta;
- convertir hora a UTC;
- calcular temps relatiu a C2/C3;
- identificar bracket i posició;
- marcar incidències.

Controls:

- nombre esperat versus nombre real;
- duplicats;
- noms repetits;
- exposicions fora de patró;
- salts temporals;
- rellotges incoherents.

## Etapa 2 — caracterització

Per cos, ISO i mode RAW:

- black level;
- white level;
- linealitat senyal/temps;
- clipping per canal;
- soroll de lectura;
- banding;
- hot pixels;
- resposta a temperatura;
- RAW comprimit versus no comprimit;
- resposta modificada versus stock.

Productes:

- corba senyal/temps;
- llindar inferior de SNR;
- llindar superior lineal;
- perfil per canal;
- incertesa.

Una fusió HDR no ha d'usar una simple màscara basada en el valor normalitzat 0–1 si la resposta real no és lineal.

### Photon-transfer

La metodologia de James Janesick caracteritza un detector amb parelles de flats a nivells creixents:

- mitjana del senyal;
- variància de la diferència;
- guany e⁻/ADU;
- read noise;
- full well;
- rang dinàmic;
- linealitat.

Referència: [Janesick, *Photon Transfer*](https://www.spiedigitallibrary.org/ebooks/PM/Photon-Transfer/3/Photon-Transfer-Noise-Sources/10.1117/3.725073.ch3).

Per a una càmera fotogràfica, els RAW poden incorporar compressió, black-level metadata i altres transformacions. El test ha de tractar el fitxer final real que entrarà al pipeline, no només una especificació teòrica del sensor.

## Etapa 3 — calibratge CFA

Ordre:

1. correcció de no-linealitat, si es demostra necessària;
2. bias/offset;
3. dark;
4. flat normalitzat per classe CFA;
5. mapa de defectes.

Conservar:

- masters;
- nombre de frames;
- mètode de combinació;
- temperatura;
- estadístiques de rebuig;
- versió del perfil.

## Etapa 4 — demosaic lineal

Requisits:

- sortida float;
- cap corba gamma;
- cap reducció de soroll oculta;
- cap sharpening;
- balanç de blancs diferit o reversible;
- matriu de color documentada;
- canals sense clipping addicional.

Cal comparar almenys dos demosaics en una mostra:

- un de conservador;
- un de més sofisticat.

El guany aparent de detall no ha de crear zippering o fals color a prominències.

## Etapa 5 — apilat de repeticions

Agrupar només frames realment equivalents:

- mateixa càmera;
- mateixa exposició;
- mateix ISO;
- finestra temporal estreta;
- transparència comparable;
- focus comparable.

Mètodes:

- mitjana;
- mean-median;
- sigma-clipping;
- pes per nitidesa i SNR.

No apilar indiscriminadament abans d'haver registrat. No usar una mesura de nitidesa dominada pel limbe lunar o per highlights.

## Etapa 6 — registre

### Línia base oberta

- [IPC](https://github.com/zdenyhraz/IPC)
- [shenanigans](https://github.com/zdenyhraz/shenanigans)

Preparació:

- luminància lineal;
- màscara lunar;
- màscara de saturació;
- finestra Hann;
- passa-alt tangencial;
- baixa-passada contra pols/patró fix.

Estratègia:

- triar exposició intermèdia;
- registrar veïns d'exposició;
- construir referència progressiva;
- propagar transformacions;
- revisar cada salt;
- aplicar la mateixa transformació als RGB lineals.

Mètriques:

- pic/segon pic;
- amplada del pic;
- residu R/B–G;
- correlació local;
- transformació respecte del temps;
- outliers.

## Etapa 7 — fusió HDR lineal

### Aproximació inspirada en LDIC

Per cada frame:

- convertir a unitats relatives per temps;
- ajustar escala i offset respecte del màster;
- fer-ho per sectors angulars;
- suavitzar coeficients en angle;
- construir pes a partir de SNR i tram lineal;
- excloure saturació i defects.

\[
H=\frac{\sum_iw_iL_i}{\sum_iw_i}
\]

Guardar:

- `H`;
- suma de pesos;
- nombre efectiu de frames;
- exposició dominant;
- residu;
- mapa de saturació;
- mapa temporal.

### Pesat per soroll

Granados et al. proposen una fusió òptima per a càmeres lineals basada en un model calibrat de:

- photon shot noise;
- dark-current shot noise;
- read noise;
- photo-response non-uniformity;
- dark-current non-uniformity.

El mètode estima radiància i incertesa, i evita que una mesura sorollosa determini el seu propi pes. És un bon referent per superar una simple funció triangular d'HDR.

Font: [*Optimal HDR Reconstruction with Linear Digital Cameras*](https://vcai.mpi-inf.mpg.de/projects/opthdr/granados10_opthdr.pdf), DOI 10.1109/CVPR.2010.5540208.

### Finestra temporal

Cal fer més d'un HDR:

- HDR pròxim a C2;
- HDR central;
- HDR pròxim a C3;
- màster global opcional.

La Lluna i les prominències evolucionen. Un únic màster de tota la totalitat pot ser molt net però no representa un instant.

## Etapa 8 — Lluna i Earthshine

- registre en coordenades lunars;
- apilat separat;
- selecció d'instant de referència;
- composició amb màscara explícita;
- conservar versió sense reintegració.

Earthshine pot requerir:

- exposicions llargues;
- correcció de moviment;
- control de reflexos;
- reducció de soroll separada.

## Etapa 9 — realçaments independents

### ACHF obert

Ús:

- corona blanca d'alt SNR;
- estructura radial i tangencial;
- control de màscara a la Lluna;
- diverses escales gaussianes.

Riscos:

- halos;
- ringing;
- oversharpen;
- creació de textures.

### MGN

Implementació: [sunkit-image](https://docs.sunpy.org/projects/sunkit-image/en/stable/api/sunkit_image.enhance.mgn.html).

Punt inicial:

- \(\sigma\): 1,25; 2,5; 5; 10; 20; 40 px;
- \(k=0,7\);
- \(\gamma=3,2\);
- context global \(h=0,7\).

Riscos:

- soroll local;
- vores massa marcades;
- escales inadequades al mostreig.

### NRGF

Implementació: [sunkit-image](https://docs.sunpy.org/projects/sunkit-image/en/stable/api/sunkit_image.radial.nrgf.html).

Ús:

- control ràpid;
- corona exterior;
- comparació morfològica.

Riscos:

- normalització global d'anell;
- regions brillants influeixen tot el radi;
- pèrdua de context fotomètric.

### FNRGF

Implementació: [sunkit-image](https://docs.sunpy.org/projects/sunkit-image/en/stable/api/sunkit_image.radial.fnrgf.html).

Ús:

- adaptació angular;
- línies o sectors febles;
- control independent.

Riscos:

- anells;
- glimmers;
- paràmetres manuals;
- soroll exterior.

### WOW

Font: [Wavelet-Optimized Whitening](https://arxiv.org/abs/2212.10134).

Ús:

- informació multiescala;
- supressió de halos i soroll;
- benchmark modern.

### RHEF

Font: [Radial Histogram Equalization Filter](https://link.springer.com/article/10.1007/s11207-025-02578-x).

Ús:

- equalització per percentils en anells;
- control robust davant outliers;
- alternativa oberta recent.

## Matriu comparativa

| Mètode | Obert | Fotomètric | Multiescala | Adaptació angular | Risc característic |
|---|---:|---:|---:|---:|---|
| HDR lineal | sí, nostre | sí, si està ben calibrat | no necessàriament | possible | costures/pesos |
| ACHF obert | implementable | no | sí | per geometria | halos/ringing |
| MGN | sí | no | sí | local | soroll/vora |
| NRGF | sí | no | no | no | biaix d'anell |
| FNRGF | sí | no | parcial | sí | anells/glimmers |
| WOW | sí/descrita | no | sí | local | whitening excessiu |
| RHEF | sí | no | radial | radial | banding radial |
| Corona 6 | no | no | sí | adaptatiu | caixa negra |
| ACC 6.1 | no | no | desconegut | desconegut | caixa negra |

## Etapa 10 — color

Principi:

- luminància estructural i crominància no són la mateixa cosa.

Ruta:

1. conservar HDR RGB lineal;
2. obtenir luminància realçada;
3. estabilitzar crominància amb la càmera stock;
4. tractar la càmera modificada per separat;
5. recombinar en espai documentat;
6. controlar halos cromàtics;
7. preservar una versió sense saturació creativa.

No s'ha d'usar la A7III modificada com a referència física de color sense perfil.

## Validació d'estructures

Una estructura candidata és robusta si:

- apareix en múltiples exposicions;
- apareix en brackets diferents;
- existeix abans del realçament;
- és visible amb almenys dos mètodes;
- no segueix el sensor;
- no coincideix amb pols/ghost;
- apareix en les dues càmeres quan el camp ho permet;
- és coherent amb coronògrafs o models;
- no depèn d'un paràmetre extrem.

Etiquetes útils:

- `confirmada`;
- `probable`;
- `dubtosa`;
- `artefacte`;
- `fora de validació`.

## Dispersió atmosfèrica

El treball clàssic de Filippenko quantifica la refracció diferencial amb longitud d'ona. En el nostre cas:

- no hi ha escletxa espectroscòpica a orientar;
- sí que hi ha desplaçament de R/G/B;
- a baixa altura pot competir amb el mostreig de la A7RIIIA;
- el registre per canal corregeix el desplaçament entre canals, no el desenfoc dins de cada banda.

Font: [Filippenko, 1982, PASP 94:715](https://doi.org/10.1086/131052).

## Referents visuals: Horálek i Casado

El seu valor per al pipeline és diferent:

- seqüències separades per escala i contacte;
- dark/flat i apilat;
- multi-focal;
- composició ambiental;
- narrativa.

No hi ha prou informació pública per reproduir-ne exactament el controlador o el processament. No s'ha de convertir una inferència sobre els seus mètodes en un fet.

## Dades de 2024 com a banc de prova

Abans de tocar dades 2026, qualsevol prototip futur hauria de:

1. ingerir els 56 RAW A7III;
2. detectar automàticament els buits;
3. identificar bracket/exposició;
4. calibrar una mostra;
5. registrar exposicions separades;
6. produir un HDR lineal;
7. provar MGN/NRGF/FNRGF/WOW/RHEF;
8. comparar amb el resultat ja processat;
9. mostrar què millora i què no es pot recuperar.

El buit de 125 s és un recordatori: el processament pot aprofitar dades, però no inventar les que no es van capturar.

## Criteri d'èxit

El pipeline és bo si:

- produeix una imatge millor;
- conserva un màster lineal;
- permet reproduir el resultat;
- fa visibles els artefactes;
- quantifica la cobertura;
- no obliga a confiar en una única caixa negra.
