# 84 — CapesInteriorsV4: les màscares de l'HDR interior no poden inventar estructura (19-08-2026, nit)

Pere sospitava que algunes de les estructures radials que miràvem de realçar a
`CapesInteriorsV3.psb` eren artefactes de les màscares, i va demanar un V4 amb màscares que
no interfereixin, sense halos a les unions. Aquest document diu què es va mesurar a V3, què
fa V4 i amb quins números es comprova. Lliurament: `~/Desktop/Eclipse 2026/Projecte
photoshop/1-Unint Capes/CapesInteriorsV4.psb` (+ `LLEGEIX-ME_CapesInteriorsV4.md` i
`CapesInteriorsV4_QA/`). Codi: `tools/capes_interiors_v4/`.

## 1. Què és el projecte

Deu capes de píxels, de baix a dalt: `12_1-3200s` (base, sense màscara) · Capa 4 (= `11_1-500s
_572A2968.CR3`) · Capa 5 (= `10_1-125s_572A2969.CR3`) · `09_1-60s` · `08_1-30s` · `07_1-15s` ·
`06_1-8s` · `05_1-4s` · `04_1-2s` (oculta) · `03_1s` (oculta), totes amb màscara menys la base.
És un HDR manual «invers»: la curta a baix, i cada exposició més llarga a sobre amb una màscara
que l'obre on la de sota és massa fosca. El document és Display P3 a 16 bits i Photoshop barreja
**en l'espai codificat** (comprovat reproduint el fusionat a 1·10⁻⁵).

Les capes surten totes del mateix revelat: contra l'HDR lineal calibrat, la corba de to és
la mateixa per a totes i té **γ local ≈ 1,0–1,15 fins a e ≈ 0,2**, 0,7 a 0,3, 0,5 a 0,6 i
0,2 a 0,9. Per sota de 0,2 les capes són «lineals» i proporcionals (×2 per pas); per sobre,
comprimeixen. Entre capes adjacents el color difereix un 2–6 % en R/G (la més llarga és menys
vermella) i la brillantor un 2,0–2,2× (els apilats 05 i 06 van un 5–10 % clars).

## 2. Diagnòstic de V3

1. **Les màscares tenien estructura azimutal.** En polars, les de 09/08 porten ratlles
   radials i una osca al forat coronal (θ 230–265°); la de 07 és un anell que segueix el
   contorn de saturació (puja a 1,3 R☉ al forat, baixa a 1,6 als raigs); la de 05 té una
   ratlla clara al forat i un contorn ondulat; la de Capa 5 és clara a mig camp i fosca a
   l'altre (`QA/06`, `07`). Desviació azimutal de les màscares: 0,19–0,26 (Capa 5), 0,08–0,15
   (09, 08), 0,09–0,16 (07) a 1,1–1,5 R☉.
2. **Efecte mesurat.** Compost V3 dividit pel mateix apilat amb les màscares promitjades per
   anell: desviació azimutal del quocient **10,8 % a 1,02, 18,4 % a 1,2, 10,2 % a 1,5 R☉**,
   percentils 5/95 0,86/1,52; un blob de **+40 %** al forat coronal vora el limbe i taques a
   100° i 130°. El signe dominant era **aplanar**: contrast de l'estructura de V3 respecte de
   cada capa sola (pendent del log-ratio a la mediana d'anell) **0,34** (1,0–1,2 R☉, Capa 5),
   0,57 (1,25–1,6, 08), 0,68 (1,4–1,9, 07), 0,82 (1,55–2,2, 06); correlacions 0,88–0,99.
3. **Capes comprimides i saturades al limbe.** A 1,02 R☉, Capa 5 pesava 0,40, Capa 4 0,10,
   09 0,17, 08 0,14, 07 0,07, 06 0,04, 05 0,07: la meitat del pes en capes amb el canal màxim
   a 0,7–1,0. γ efectiu del compost: 0,53 (1,02), 0,61 (1,1), 0,74 (1,3), 0,92 (1,5), ≥ 1 de
   1,7 enfora.
4. **Marc blanc**: Capa 4 i Capa 5 són de tot el llenç amb blanc fora del marc; la màscara de
   Capa 5 hi era 1 (fusionat amb marc blanc). **Lluna**: el disc de la màscara de Capa 4 (radi
   428 px, centre a (−10,5, −12,0) del Sol) volia la 1/3200 a dins, però les màscares grises de
   sobre hi deixaven Capa 5 al 68 %: interior a 0,017 (resplendor de les llargues).
5. **Alineament.** Les deu capes estan alineades entre elles a ≤ 0,1 px (correlació de fase de
   la corona; la 1/3200, sense corona, via la protuberància: (+0,09, −0,07) respecte de Capa 4).
   **Però tot el projecte és a (+1, +1) px de CapesExteriors.psb** (EDITAT PERE a (−1,05,
   −1,08) i 03_1s a (−1,04, −0,87) respecte de les capes de V3, 9–24 retalls) i del llenç E de
   tots els filtres: a V2/V3 els DNG són a (458, 464) i el 18-08 eren a (457, 463).

## 3. Disseny final (el que hi ha a `CapesInteriorsV4.psb`)

Pere va refusar el primer disseny (màscares radials de nou encuny, amb perfil objectiu monòton,
altiplà a 0,168, la 1/3200 dalt de tot i una capa de guany Color Dodge): «prefereixo la V3, les
perles i les protuberàncies s'han de protegir, manen les capes inferiors a les superiors». El
disseny final és **V3 amb les màscares netejades**, no un compost nou:

- **Ordre i filosofia de V3**: la 1/3200 a baix sense màscara, les llargues a sobre, 04 i 03
  ocultes; cap capa nova, cap capa de guany; el perfil de brillantor de V3 (±7 %, idèntic de
  1,5 R☉ enfora) perquè les màscares són les seves.
- **Màscares = les de V3 promitjades per anell** (mitjana azimutal en bins de 0,002 R☉,
  suavitzada σ 0,02 R☉, només dins del marc de contingut): conserven el repartiment radial de
  Pere i perden toda l'estructura azimutal.
- **Cascada de protecció** («manen les capes inferiors»): on el canal màxim de la 1/125 puja de
  0,60 a 0,85 (creixent, nucli de la protuberància; 4 722 px a 0,95–1,15 R☉) es tanquen les
  màscares de la Capa 5 cap amunt → es veu la 1/500; on també la 1/500 està cremada (2 219 px)
  es tanca la seva → es veuen les perles de la 1/3200. Rampa suau + ploma d'1,5 px.
- **Disc lunar** (centre (4034,8, 2736,3), radi 437 px, vora 4 px): totes les màscares de sobre
  a 0 → la 1/3200, Lluna negra (V3 hi deixava un 1,7 % gris).
- Capa 4/5 retallades al marc (fora eren blanc) i geometria del 18-08 (capes a (457, 463), la
  1/3200 a (456, 462)). Fitxer 1,16 GB, màscares a 16 bits (psb_utils), rellegit i recompost
  a 3·10⁻⁵.

## 4. Comprovacions (disseny final)

| Prova | V3 | V4 |
|---|---|---|
| Perfil radial | — | = V3 ±7 % (1,0–3,0 R☉); idèntic de 1,5 enfora |
| Test d'anells (1,09–2,9 R☉) | 0,20 % rms | **0,18 % rms** |
| Modulació azimutal de les màscares | ±10–18 % | 0 (fora de la cascada) |
| Correlació estructura vs capes soles (Capa 5/08/07/06) | 0,88/0,98/0,99/0,99 | **0,986/0,998/0,998/0,997** |
| Contrast de l'estructura real | 0,34/0,57/0,68/0,82 | **0,60/0,77/0,83/0,91** |
| Creixent/protuberància | nucli cremat blanc | estructura de la 1/500 i la 1/3200 |
| Lluna | gris 1,7 % | negra |

El contrast no és 1,0: el compost barreja les capes com V3 (condició de Pere); el que
desapareix és la dependència azimutal de la barreja. El primer disseny (contrast 0,99–1,05,
γ ≈ 1 al limbe) queda a `CapesInteriorsV4.psb.anterior-disseny-claude` com a referència del
sostre del que les capes no comprimides poden donar.

## 5. Lliçons

- Una màscara de lluminositat desenfocada **és un halo per construcció** (la barreja depèn
  del veïnat); una de lluminositat sense desenfocar és una corba de to puntual; una de pinzell
  imprimeix el que es pinta. L'única que no interfereix amb l'estructura és la radial (o la
  que segueix contorns que no són de la imatge).
- Amb capes a 1 EV i rampes curtes, el perfil del compost bota ±25 % a cada relleu (dent de
  serra del sostre vàlid): per no fer anells cal un perfil objectiu monòton i suau i pagar-lo
  amb la capa fosca o amb la parella adjacent; el preu és un altiplà on les capes vàlides no
  donen més. La brillantor es recupera després amb una corba **radial** (Color Dodge), mai
  amb les màscares.
- El revelat de Camera Raw és lineal fins a e ≈ 0,2: per sobre de 0,3 una capa ja comprimeix
  les bases dels raigs (γ 0,5–0,7), i per sobre de 0,6 les aplana. Els llindars de validesa
  que han sortit (p50 ≤ 0,46, p95 ≤ 0,66) són la frontera raonable.
- Photoshop barreja en l'espai codificat del document (aquí Display P3) — qualsevol càlcul
  de màscares s'ha de fer amb els valors codificats i reproduir el fusionat abans de res.
- El que el primer disseny ensenya i queda per al futur: el sostre no comprimit és un altiplà a
  0,168 (1,17–1,6 R☉) i per tenir el perfil de V3 amb γ ≈ 1 caldria recuperar la brillantor amb
  una corba radial (Color Dodge) en lloc de capes comprimides; Pere ha triat conservar l'aspecte
  de V3, que és una decisió d'aspecte, no de mètode.

## 6. CapesInteriorsV5 (matinada del 20-08): el V4 editat de Pere + les màscares de 04/03 refetes

Pere va editar `CapesInteriorsV4.psb` (03:24): hi va afegir una segona `12_1-3200s` a (457,463) i
una segona `09_1-60s` a (458,464) (geometria de V3), hi va tornar les Capa 1/Capa 2 (les velles
Capa 4/5 de V3, llenç sencer), va repassar el **limbe lunar** a les màscares de la 09 i la 08
(0,96 %/1,05 % dels píxels; també Capa 2, 9,7 %) i va encendre les 04/03. El limbe s'havia de
repassar perquè **la Lluna es mou entre exposicions** (centres que ballen ~3 px, radis 449,5–451,8
px per capa, mesurats) i tant el disc únic com el promitjat radial centrat al Sol hi fabricaven un
artefacte (el limbe lunar no és concèntric amb el Sol).

`CapesInteriorsV5.psb` (1,30 GB) = el V4 editat **byte a byte** (12 capes, píxels, màscares, noms,
visibilitats) amb NOMÉS les màscares de `04_1-2s` i `03_1s` substituïdes:
**m_nova = màxim(màscara vella de Pere, màscara neta radial)**, on la neta és el perfil de la
vella fet monòton, aplanat de 3 R☉ enfora, tallat a zero fins a 1,15/1,25 R☉ (rampa 0,3 R☉) i
gaussianes (σ 0,04 R☉ 1-D + 3 px 2-D). La vella mana pertot on és més oberta (vel del limbe,
protuberàncies, perles: **es veuen exactament igual**, diff ≤ 0,0001 dins d'1,3 R☉ i ≤ 0,004 fins
a 4 R☉); la neta només tapa el **forat-anell de la 04 entre 4 i 6 R☉** (0,96 → 0,02 → 0,12 sense
difuminar) i la caiguda exterior de la 03. Perfil final monòton (0,58 a 1,2 → 0,22 a 9), test
d'anells **0,11 % rms** (1,09–8,5 R☉).

Dues notes: (1) les versions amb **NoiseXTerminator** de les capes de fraccions de segon que Pere
diu haver fet **no eren al disc** en construir la V5 (V3 de les 02:22 i V4 de les 03:24
byte-idèntiques a les capes velles a totes les zones provades): quan es desin, refer la V5 és
re-executar `escriu_v5.py` (les màscares no canvien). (2) El primer intent de màscares 04/03
(zero fins a 1,9 R☉) creava una **vall fosca a 1,2–1,6 R☉** contra el vel que les velles posen al
voltant del limbe: treure un vel existent també és un anell; per això el màxim amb la vella.

**Normes canòniques declarades per Pere (20-08)**, incorporades a la skill `postprocessat-corona`:
(A) prohibit introduir artefactes radials a les màscares, i menys sense desenfoc gaussià — recepta
segura d'halos que persegueixen les capes exteriors; (B) les capes interiors són els fonaments: no
s'arregla en capes posteriors (torre de Pisa) el que ja s'hereta de dins; més el limbe lunar per
capa, les protuberàncies/perles sagrades amb les capes inferiors manant, i el denoise suau a les
capes de baixa exposició.
