# PLA APLICAT DE POSTPROCESSAT — Eclipsi total del 12 d'agost de 2026

**Destinatari:** Pere Guerra
**Data del pla:** 15 d'agost de 2026
**Abast:** de l'estat actual (G0–G2 tancats, G3 obert) fins a la imatge final de corona
**Dades:** 124 fotogrames R6 Mark III + Vixen VSD90SS · 194 fotogrames A7RIIIA + Sony FE 300 mm f/2,8 GM

---

## Avís preliminar: tres coses del dossier que s'han hagut de corregir

Abans del pla, les tres correccions de la fase adversarial que canvien la feina. No són matisos: canvien què s'ha de fer primer.

**1. Els TIFF calibrats actuals no serveixen per a fotometria, i el motiu és el balanç de blancs.** Els dos scripts de calibratge (`research/tools/lot_calibratge_vixen.py` i `research/tools/lot_calibratge_300mm.py`) fan `raw.postprocess(use_camera_wb=True, ...)` amb el retall d'altes llums per defecte de LibRaw. Amb els guanys de balanç de blancs de la R6 (R=1,943 · B=1,659) el canal vermell es retalla a 8.430 comptes crus, o sigui **1,00 EV per sota del pou real**; a la Sony (R=2,504) el retall cau a 6.543 comptes, **1,32 EV per sota**. Verificat sobre `572A2982.CR3` (l'exposició de 10,3 s): el RAW té un 0,068 % de fotolocalitats vermelles al blanc i el TIFF n'hi té un **5,55 %**, 81 vegades més. Per tant **65535 al TIFF no vol dir sensor saturat** i qualsevol màscara de pesos construïda sobre aquest número és falsa.

**2. El terra està censurat.** El calibratge fa `np.clip` a zero i LibRaw resta el negre: al R6, el **44,0 %** dels píxels de l'exposició d'1/2000 són exactament 0, el 41,2 % a 1/1000 i el 34,9 % a 1/500; a la Sony, `DSC06974` (1/6400, bloc de contacte) té el 40,8 / 52,5 / 38,8 % (RGB) a zero. La prova de linealitat ho tanca: a 5 R☉ la raó 1/500→1/125 dona **9,0** quan hauria de ser 4,0, mentre que 1/30→1/8 dona 4,28 contra 4,167 esperat. Un model de halo ajustat sobre aquests fitxers ajustaria una variable truncada.

**3. L'exposició més profunda del R6 està mal apuntada.** El manifest diu 10,000 s perquè el llegeix de Spotlight (`mdls`) i no de l'EXIF; el programa declara **10,3 s** i el `ShutterSpeedValue` diu 10,4. Dividir per 10,0 posa **0,04–0,06 EV** d'error sistemàtic justament a l'esglaó que porta l'earthshine.

**Conseqüència:** G3 no es pot obrir sobre `Calibrated_Claude/` i `300mm/calibrated/` tal com són avui. La primera peça de feina és refer el calibratge. És més barat del que sembla i s'explica al punt 1.

---

## 1. On és el projecte i quina és la següent peça

### Estat real

| Porta | Què és | Estat |
|---|---|---|
| G0 | Procedència: quin fitxer surt de quina pulsació, amb quina exposició i quin instant | **FET** (manifest de 124 i 194 files, amb EXIF creuat) |
| G1 | Banc de darks a la temperatura de treball (40–41 °C) | **FET amb dos defectes** (vegeu §4) |
| G2 | Consistència de camp: escala de placa, contactes reals, deriva, salts de muntura | **FET** (`research/71` i `research/72`) |
| G3 | Model de halo / llum difusa | **OBERT — front actiu** |
| G4 | Doble registre corona / Lluna | pendent |
| G5 | Composició HDR lineal en float64 | pendent |
| G6 | Visualització controlada | pendent |

### La següent peça: **G2-bis, recalibratge fotomètric**

No és una porta nova, és la reobertura tècnica de G1/G2 durant una sessió. Consisteix a regenerar els dos lots de TIFF **sense balanç de blancs, sense matriu de color, sense retall d'altes llums i sense retall a zero**.

**Per què aquesta i no G3 directament.** Perquè les tres coses que G3 necessita mesurar —el pedestal de fons a 4–8 R☉, el perfil de caiguda de la llum difusa i el sostre de senyal útil de cada exposició— són exactament les tres que els TIFF actuals destrueixen. Ajustar un model de halo sobre un fons on el 44 % dels píxels és zero per retall no dona un halo: dona el llindar del `clip`. I un pes de composició que consideri saturat qualsevol píxel a 65535 llençarà el 5,5 % del canal vermell de l'exposició de 10,3 s que en realitat és bo.

**Per què no anar directament a G4 (registre) i deixar G3 per després.** Perquè el registre per correlació de fase de Druckmüller (2009) es fa sobre imatges auxiliars filtrades que no són el producte, i els TIFF actuals hi servirien igual. Però el registre s'ha d'executar **una sola vegada** i s'ha d'aplicar als fitxers definitius; fer-lo dues vegades és regalar una tarda. I la deriva instrumental que hem de mesurar per a G4 és més neta sobre dades no retallades.

### Què s'ha de produir a G2-bis

Dos directoris nous, **sense esborrar els vells**:

```
/Users/USUARI/Desktop/Eclipse 2026/Vixen Unfiltered/Linear_v2/
/Users/USUARI/Desktop/Eclipse 2026/300mm/linear_v2/
```

Format: **TIFF de 3 canals, float32, unitats de comptes crus del sensor amb pedestal conservat** (no ADU de 14 bits reescalats, no 16 bits enters). Nomenclatura idèntica a l'original amb sufix `_lin`. Un `manifest_v2.csv` per directori amb aquestes columnes, totes verificables:

`fitxer, t_exif_utc, t_relatiu_C2_s, exposicio_s_exif, iso, black_R, black_G1, black_G2, black_B, white_level, n_sat_raw_R, n_sat_raw_G, n_sat_raw_B, fons_raw_ADU_R, fons_raw_ADU_G, fons_raw_ADU_B, r_fons_Rsol, centre_sol_x, centre_sol_y, centre_lluna_x, centre_lluna_y, bloc_programa`

La crida de LibRaw ha de ser exactament aquesta:

```python
rgb = raw.postprocess(
    output_bps=16,
    use_camera_wb=False,
    use_auto_wb=False,
    user_wb=[1.0, 1.0, 1.0, 1.0],
    output_color=rawpy.ColorSpace.raw,
    no_auto_bright=True,
    gamma=(1.0, 1.0),
    highlight_mode=rawpy.HighlightMode.Ignore,
    demosaic_algorithm=rawpy.DemosaicAlgorithm.AHD,
    four_color_rgb=False,
)
```

I la resta de dark **sense `np.clip(0)`**: es fa en float32 i els valors negatius es conserven. Un fons de cel amb soroll ha de tenir la meitat de les mostres per sota de la mediana; si les talles, ja no és mesurable.

**Correcció de l'exposició:** llegir `ExposureTime` de l'EXIF amb `exiftool`, i **substituir manualment 10,0 → 10,3 s** als tres fotogrames de l'esglaó profund del R6 (`572A2982`, `572A2983`, `572A2984` segons el manifest; verifica els noms exactes abans). El programa és l'autoritat: 10,3 és literal del menú del cos.

**Criteri objectiu de pas de G2-bis** (tots quatre s'han de complir):

1. **Cap fitxer amb més del 0,5 % de píxels exactament al valor de negre** al canal verd, excepte els tres 1/6400 de contacte de la Sony i els 1/3200 del R6, on s'admet fins al 5 % perquè el cel hi és realment per sota d'un comptatge.
2. **Prova de linealitat:** mediana anular al canal verd a 3,0 R☉ i a 5,0 R☉ sobre les quatre exposicions consecutives del R6 dins de 2,7 s (`572A2986`–`572A2989`, 1/500 · 1/125 · 1/30 · 1/8). Les tres raons consecutives han de sortir **4,167 ± 0,15** a totes dues alçades. Avui a 5 R☉ la primera raó surt 9,0.
3. **Recompte de saturació:** el nombre de fotolocalitats a `white_level` al RAW i el nombre de píxels al sostre del TIFF de sortida han de coincidir dins d'un factor 1,3. Avui difereixen per 81.
4. `manifest_v2.csv` amb 124 i 194 files, cap `exposicio_s_exif` nul·la i cap valor de 10,000 al R6.

**Cost de càlcul:** 318 fotogrames × ~2,5 s de demosaic AHD + E/S = **13–15 minuts** al Mac, més la lectura d'EXIF (~40 s amb `exiftool -stay_open`). El disc: 124 × 6960×4640×3×4 B ≈ **48 GB** al Vixen i 194 × 7952×5304×3×4 B ≈ **98 GB** a la Sony. **Comprova l'espai lliure abans d'engegar** i, si va just, escriu els TIFF amb compressió `zstd` de tifffile (baixa a ~55 % sense pèrdua i costa un 15 % més de temps).

---

## 2. Les quatre portes que queden

---

### G3 — Model de halo i llum difusa

#### Què s'ha de produir

Tres artefactes, tots dos cossos per separat:

```
G3/psf_r6m3_vsd90ss.npy         perfil radial de la PSF estesa, float64, 1 col. per radi
G3/psf_a7r3a_300gm.npy          idem
G3/halo_model_<cos>.json        paràmetres de l'ajust + covariància + interval de validesa
G3/<cos>/<fitxer>_deglared.tif  TIFF float32, mateixes unitats que Linear_v2
```

Unitats: comptes crus per segon d'exposició (o sigui `(TIFF − pedestal) / t_exp`), que és l'única escala on els 16 esglaons del R6 són comparables.

#### Amb quin mètode i per què aquell

**No fer servir el mètode de Druckmüller.** Cal dir-ho clar perquè tot el dossier gira al voltant d'ell: **en tot el corpus del grup de Brno no hi ha cap model de halo, de llum difusa instrumental ni de PSF**. La seva manera de tractar-ho és absorbir-ho dins la composició, amb el compositor LDIC que ajusta una transformació lineal (k, q) per separat en **60 segments angulars** —tal com descriu el §4.1.4 de la tesi completa de Druckmüllerová—, i el motiu declarat és precisament poder compondre imatges amb distribucions diferents de llum difusa a l'òptica. Això és una absorció, no un model: fa que les imatges casin entre elles, però deixa la llum parasitària dins del resultat com si fos corona.

El camí bo és el que ja tens a la carpeta i que ve de fora d'aquest grup: **deconvolució amb PSF estesa mesurada**, seguint Hofmeister (2024), amb la caracterització de veiling glare de Talvala (2007) i les mesures de PSF de Yeo (2014) i Wedemeyer-Böhm (2008).

**Per què es pot fer amb aquestes dades i no amb unes altres.** Perquè tens el que la majoria d'observadors no té: **la Lluna**. El disc lunar durant la totalitat és un objecte de brillantor pròpia negligible comparada amb la corona interior i té una vora dura i coneguda. Tot el senyal que mesuris **dins** del disc lunar, més enllà del que hi posa l'earthshine, és llum difusa: PSF de l'òptica més dispersió atmosfèrica més reflexions internes. I en tens **dues mesures independents**, una per tren, amb òptiques radicalment diferents (un refractor apocromàtic de 90 mm f/5,5 i un teleobjectiu de 300 mm f/2,8 amb moltes més superfícies aire-vidre).

I tens el segon regal: **les tres àncores d'earthshine de la Sony (1/8 · 1 s · 8 s)** et donen el nivell real de l'earthshine amb 24 s d'integració, o sigui que pots **separar** la component astronòmica (earthshine, uniforme sobre el disc, ~9,8 magnituds per sota de la Lluna plena) de la component instrumental (halo, que decau amb la distància al limbe).

#### Paràmetres concrets

**Pas 1 — Perfil de llum dins del disc lunar.**

Sobre els fotogrames profunds del R6 (els tres de 10,3 s i els tres de 2 s) i les tres àncores de 8 s de la Sony:

- Centre lunar: ajustat per la vora amb un Canny + Hough circular sobre el fotograma de contacte més curt (1/3200 al R6, 1/6400 a la Sony), i propagat als profunds amb el model de deriva de G2.
- Radi lunar: al R6, **R☉ = 959″/2,158 = 444,4 px**; amb magnitud local ~1,031 el radi lunar és **458,2 px**. A la Sony, R☉ = 959/3,234 = **296,5 px** i el radi lunar **305,7 px**.
- Mostrejar la mediana en 40 anells concèntrics de 10 px de gruix, des de r = 0 fins a r = radi lunar − 20 px, **excloent** un sector de ±25° al voltant de qualsevol protuberància visible i excloent el sector on el fotograma estigui fora de camp.
- El resultat és `I_dins(r)`. La component plana d'aquest perfil, mesurada al centre (r < 100 px), és **earthshine + halo de fons**; el gradient cap al limbe és **halo**.

**Pas 2 — Separar earthshine de halo.** L'earthshine és plana sobre el disc dins d'un 5 % (és una superfície il·luminada per un hemisferi terrestre, no per un punt). El halo, en canvi, decau com una llei de potència. Ajusta:

```
I_dins(r) = E + A · (R_lluna − r + r0)^(−α)
```

amb `E` (earthshine), `A`, `α` i `r0` lliures. Valors d'arrencada: α = 2,0 (el rang habitual de veiling glare és 1,5–2,5), r0 = 5 px. Ajust amb `scipy.optimize.least_squares` amb pèrdua `soft_l1` i `f_scale` a la desviació típica del soroll de fons.

**Pas 3 — Construir la PSF estesa.** El nucli és el pes d'una font puntual que arriba a distància θ:

```
PSF(θ) = δ(θ) · (1 − f) + f · K · (θ² + θ0²)^(−α/2)
```

on `f` és la fracció de flux dispersada. Per a un teleobjectiu modern net, `f` és típicament 0,5–2 %; per a un refractor apocromàtic amb menys superfícies, 0,2–0,8 %. El valor exacte surt d'imposar que, convolucionant la corona mesurada amb aquesta PSF, es reprodueixi el `A` i l'`α` del pas 2.

**Els números que has de treure, no assumir:**

| Magnitud | R6 + VSD90SS | Sony + 300 GM |
|---|---|---|
| Escala de placa | **2,158 ″/px** (mesurada) | **3,234 ″/px** (mesurada) |
| Radi solar en px | 444,4 | 296,5 |
| Radi lunar en px | 458,2 | 305,7 |
| `f` esperat (a verificar) | 0,2–0,8 % | 0,5–2 % |
| Rang d'ajust | 1,05 a 6,0 R☉ | 1,05 a 4,0 R☉ |

El límit exterior de la Sony és més baix perquè el seu camp és més estret en radis solars i perquè els seus fotogrames profunds són només tres.

**Pas 4 — Deconvolució.** Richardson-Lucy amb la PSF estesa, **20 iteracions**, sobre la imatge composta HDR i **no** sobre fotogrames individuals. Per tant aquest pas s'executa físicament després de G5, però el model es mesura ara. Motiu: la deconvolució amplifica el soroll, i el compost HDR té 20–50 s d'integració efectiva contra els 0,3 ms d'un fotograma de contacte.

⚠️ **Alternativa conservadora si el pas 3 no convergeix:** restar el halo com a camp additiu en comptes de deconvolucionar. Perds la restitució de contrast però no inventes res. És el camí a agafar si `α` surt amb una incertesa superior al 20 %.

#### Criteri objectiu de bo

1. **Prova de coherència entre trens:** el nivell d'earthshine `E`, un cop convertit a brillantor de superfície absoluta (comptes → mag/arcsec² amb la calibració d'exposició i l'obertura de cada tren, normalitzat a f/2,8 ISO 100 amb el pont de **1,95 EV** que ja tens documentat), ha de coincidir entre els dos cossos dins de **0,3 EV**. Són òptiques diferents que miren el mateix objecte: si el mateix earthshine surt diferent, el que has ajustat no és earthshine.
2. **Prova del residu:** després de restar el model, el perfil dins del disc lunar ha de ser pla dins d'**±8 %** entre r = 0,2 i r = 0,9 radis lunars.
3. **Prova del fons llunyà:** el fons a 8 R☉ del R6, després de la correcció, ha de baixar respecte del valor sense corregir en la fracció que el model prediu, i el descens mesurat i el predit han de coincidir dins del **25 %**.
4. **Prova de no-inventar:** cap píxel de la imatge corregida pot quedar per sota de −3σ del soroll de lectura. Si n'hi ha, has sobrerestat.

#### Cost de càlcul

Ajust del model: **minuts**. La mesura dels perfils sobre 12 fotogrames: ~3 min. La deconvolució Richardson-Lucy de 20 iteracions sobre un compost de 6960×4640 amb una PSF de 2001×2001 píxels via FFT: **25–40 min per canal**, o sigui unes dues hores per al compost del R6 i una hora i mitja per al de la Sony. És el pas més car de tot el pipeline.

---

### G4 — Doble registre corona / Lluna

#### Què s'ha de produir

```
G4/transforms_corona_<cos>.json   una fila per fotograma: dx, dy, rotacio_graus, escala, sigma_usat, pic_snr
G4/transforms_lluna_<cos>.json    idem, per a la pila lunar
G4/registered_corona/<cos>/*.tif  float32, mateixes unitats
G4/registered_lluna/<cos>/*.tif   només els fotogrames on el disc lunar es pugui mesurar
```

#### Amb quin mètode i per què

**Correlació de fase modificada de Druckmüller (2009), ApJ 706, 1605.** És el mètode dissenyat exactament per a aquest problema i el paper el justifica bé: durant la totalitat no hi ha punts de referència útils —les estrelles no surten a les curtes, la vora lunar està cremada a les llargues, i tant la Lluna com les estrelles **es mouen** respecte de la corona.

Les tres modificacions del paper són les que el fan funcionar amb dades reals i totes tres t'afecten:

**(a) Regularització.** `N_{p,q} = C · [(|A|+p)(|B|+q)]⁻¹`. Sense les constants, la normalització divideix per valors propers a zero a les freqüències de baixa amplitud i el pic desapareix.

**(b) Filtre tangencial `H_ρ`.** Aquest és el punt clau i el motiu de fons és directament aplicable al teu cas: *el gradient radial extrem de la brillantor coronal, més qualsevol no-linealitat de l'escala (saturació, llum difusa no homogènia), fa que les freqüències espacials en direcció radial no siguin fiables*. La solució és eliminar les freqüències baixes **només en direcció tangencial**, i això obliga a fer-ho a l'espai, no a la freqüència.

**(c) Màscara en anell.** Aquest és el mecanisme del doble registre i és més simple del que sembla: **per registrar la corona, la Lluna es treu**. La màscara val 1 dins de l'anell `r1 < r < r2` i 0 fora, amb `r1` una mica més gran que el radi lunar i `r2` una mica més petit que el cercle inscrit al fotograma.

#### Paràmetres concrets

Del paper, adaptats a les teves mides:

| Paràmetre | R6 (6960×4640) | Sony (7952×5304) | Origen |
|---|---|---|---|
| `p` = `q` | 0,01 % del màxim de \|A\| | idem | valor dels assajos reals del paper |
| `σ` (gaussiana de la freqüència) | escombrar 0,02n → 0,3n, amb n = 6960 | n = 7952 | el paper diu 0,01n–n i que σ **s'ha d'escombrar** |
| `ρ` (filtre tangencial) | **8** | **8** | valor dels assajos reals |
| `ω₁,ω₂` | ±16 (= ±2ρ) | ±16 | regla del paper |
| `ε` (moments subpíxel) | **3** | **3** | valor dels assajos reals |
| `r1` (interior de la màscara) | **480 px** (= radi lunar + 22) | **325 px** | radi lunar + marge |
| `r2` (exterior) | **2200 px** | **2600 px** | menor que el cercle inscrit |

⚠️ **Tres avisos d'implementació que el paper no resol i que et faran perdre una tarda si no els tens presents.** Primer: l'equació (4) està impresa com `a(r + cos(φ+ω), r + sin(φ+ω))`, amb signe més; és una errata, ha de ser `a(r·cos(φ+ω), r·sin(φ+ω))`. Segon: l'equació (4) no porta constant de normalització — has de dividir pel sumatori del pes gaussià o el filtre no dona zero sobre una regió plana. Tercer: l'equació (7) del centroide subpíxel no suma `(x₀,y₀)`; la coordenada absoluta és `x₀ + M₁₀/M₀₀`.

**Escombrada de σ.** El paper és explícit: *«the value of σ must be varied over a wide range which makes it impossible to automate the alignment»*, i un σ massa alt causa **identificació incorrecta del màxim**, no una degradació suau. Com que el paper no dona cap criteri per triar, en necessites un: **relació pic/soroll**, definida com el valor del màxim dividit per la desviació típica de `n` fora d'un radi de 20 px al voltant del pic. Escombra σ en 8 valors logarítmicament espaiats de 0,02n a 0,3n i queda't amb el que dona la relació pic/soroll més alta, **sempre que superi 6,0**. Per sota de 6,0, el registre d'aquell fotograma es marca com a dubtós i es revisa a mà.

**Estratègia de mestra.** Alinea-ho tot contra **una sola imatge mestra per cos**, no en cadena: la cadena acumula error. Per al R6, la mestra ha de ser una de les tres de 2 s (bon senyal coronal a mitja alçada, disc no cremat). Per a la Sony, la del bloc de la muntanya de mig eclipsi a 1/4.

**Registre de la Lluna: mètode diferent.** No facis correlació de fase sobre la Lluna. Fes-ho amb el **centroide de la vora**: sobre els fotogrames curts (1/3200 del R6, 1/6400 i 1/1000 de la Sony), detecta la vora amb un llindar al 50 % entre el fons i la corona interior, ajusta-hi una circumferència per mínims quadrats amb `skimage.measure.CircleModel` + RANSAC, i pren el centre. Als fotogrames profunds la vora és cremada i el centre s'ha d'**interpolar** del model lineal de la deriva, no mesurar.

**El model de deriva relativa que has de fer servir.** La Lluna es desplaça respecte del Sol a **0,5905 ″/s** (valor viu de `research/71`; el 0,585 de `CLAUDE.md` és el número previ a l'eclipsi i està caducat). Sobre 103,7 s de totalitat això són **61,2″**, o sigui **28,4 px al R6** i **18,9 px a la Sony**. Entre la primera i la tercera àncora d'earthshine de la Sony (42 s de separació segons l'EXIF) són **24,8″ = 7,7 px**.

#### Criteri objectiu de bo

1. **Residu del registre de corona:** creuant els fotogrames de la mateixa exposició separats en el temps, la posició d'una mateixa estructura coronal després del registre ha de coincidir dins de **0,3 px**. El paper declara <0,01 px prop de la vora lunar en dades sintètiques i fins a 0,40 px en dades reals verificades contra el centroide lunar; 0,3 px és exigent però assolible.
2. **Consistència del model de deriva:** els centres lunars mesurats sobre els fotogrames curts, ajustats a una recta contra el temps, han de donar un pendent compatible amb 0,5905 ″/s dins del **10 %**, i el residu de l'ajust ha de ser inferior a **1,0 px** de desviació típica.
3. **Prova de no-contaminació:** repeteix el registre de corona amb `r1` augmentat 40 px. Si els desplaçaments canvien més de 0,5 px, la màscara estava deixant entrar la vora lunar i `r1` era massa petit.
4. **Prova de la rotació:** les dues muntures són equatorials amb alineació polar; α ha de sortir inferior a **0,05°** a tots els fotogrames. Si en surt més, o hi ha rotació de camp real (i llavors s'ha de corregir) o el registre ha fallat.

#### Cost de càlcul

Amb FFT de `numpy` sobre matrius farcides a 8192×8192 en complex128 (~1 GB per matriu), unes **8–12 s per fotograma i per valor de σ**. Amb 8 valors de σ i 318 fotogrames, són **6–8 hores**. Es pot baixar a **1,5 hores** de tres maneres: (a) treballar a 4096×4096 amb reducció prèvia per a l'escombrada de σ i refinar només amb el σ guanyador a mida completa; (b) implementar `H_ρ` remostrejant a graella polar i convolucionant en 1D en lloc d'integrar píxel a píxel; (c) fer servir `float32`/`complex64`, que és sobrat per a una cerca de màxim. **Fes les tres.**

---

### G5 — Composició HDR lineal

#### Què s'ha de produir

```
G5/hdr_r6m3.tif      float64 (o float32 amb un .npy float64 al costat), 3 canals, comptes/s
G5/hdr_a7r3a.tif     idem
G5/hdr_pesos_<cos>.npz    suma de pesos per píxel: mapa de quantes exposicions han contribuït
G5/hdr_report_<cos>.json  imatge de referència triada, llindars, cobertura mínima
```

Unitats: **comptes crus per segon a f/2,8 ISO 100 equivalent**. El pont entre trens és **1,95 EV** (el VSD90SS a f/5,5 recull 1,95 EV menys llum que el mateix temps al 300 GM). ⚠️ Els 0,65 EV que van circular surten de comparar les dues parcials filtrades i **només valen per a la fase parcial**, no aquí.

#### Amb quin mètode i per què

**Mitjana ponderada amb pesos per píxel de Druckmüller, Rušin i Minarovjech (2006), equacions (3) i (4).** Aquí sí que el mètode del grup de Brno és el bo i no té competidor: és una mitjana ponderada de valors calibrats, fotomètricament coherent per construcció, i el mecanisme dels pesos resol el problema de la Lluna que es mou.

La regla que ho fa funcionar i que no és òbvia: **el disc lunar porta pes −1, no 0**. La funció `f(w)` de l'equació (3) diu que si la Lluna tapa un píxel a la imatge de referència **o** a la imatge candidata, la candidata no hi contribueix. Amb pes 0 el compositor només sabria «aquí no hi ha senyal»; amb −1 sap «aquí hi ha un altre objecte». I a la imatge de referència mateixa el pes que s'aplica és el **valor absolut**, o sigui que el disc lunar del resultat és el d'aquella imatge concreta i el compost representa el Sol **a l'instant de la referència**.

⚠️ La construcció dels pesos, al paper, es fa **subjectivament, a mà**, i els autors ho declaren com el problema obert del mètode: *«how to find such values of pixel weights which would minimize the noise in the resulting image»*. Tu no ho has de fer a mà: tens un banc de darks propi i el nivell de soroll mesurat, o sigui que pots derivar els pesos objectivament.

#### Paràmetres concrets

**Sostre útil per exposició.** Del recalibratge de G2-bis, sobre comptes crus del sensor:

- R6: pou a **16.383**, pedestal per canal `[0, 31, 94, 63]`. El llindar de linealitat del 85 % que dona la tesi de Druckmüllerová aplicat al rang útil per canal: verd `94 + 0,85·(16383−94) = 13.940` comptes. **Aquest és el sostre, no 16.383.**
- Sony: mesura el `white_level` i el `black_level_per_channel` reals i aplica el mateix 85 %.

**Terra útil.** El senyal ha de superar **5σ** del soroll de lectura del master dark corresponent. Amb σ ≈ 2,8 comptes al R6 (mesurat als masters, excepte els dos defectuosos de §4), això són **14 comptes** per damunt del pedestal.

**Funció de pes.** Amb `x` el valor cru menys pedestal:

```
w = 0                              si  x < 5σ  o  x > sostre_85
w = (x − 5σ)/(20σ − 5σ)            si  5σ ≤ x < 20σ        (rampa d'entrada)
w = 1                              si  20σ ≤ x ≤ 0,75·sostre_85
w = (sostre_85 − x)/(0,25·sostre_85)  si  0,75·sostre_85 < x ≤ sostre_85
w = −1                             si el píxel és dins del disc lunar
```

Amb σ = 2,8 al R6: rampa d'entrada de 14 a 56 comptes, pes ple de 56 a 10.455, rampa de sortida de 10.455 a 13.940.

**Màscara del disc lunar per fotograma.** Es construeix del model de deriva de G4: cercle de radi **458,2 px (R6) / 305,7 px (Sony)** centrat a la posició lunar interpolada per a l'instant d'aquell fotograma, **eixamplat 6 px** perquè el limbe té una transició real de tres o quatre píxels. Aquest eixamplament és el que evita l'anell brillant al voltant de la Lluna, que és el defecte de compost més comú.

**Imatge de referència `j`.** El paper demana *«a correctly-exposed innermost part of the corona»*. Al R6, un dels dos fotogrames de **1/500** de la meitat de la totalitat; a la Sony, un dels **1/100** del bloc de contacte de C2 no, millor un dels **1/30** de la muntanya de mig eclipsi. Tria el que estigui més a prop del mig de la totalitat, perquè el compost representarà **aquell instant** i vols que sigui el centre, no un extrem.

**Correcció per canal, no global.** Cada canal té el seu pedestal i el seu llindar de saturació. Fes els pesos per canal i composa canal a canal. La correlació espacial entre canals ja te la dona el registre; barrejar-los als pesos només et faria heretar el retall del vermell.

⚠️ **El fons no és estacionari i s'ha de treure abans de composar.** Mesurat: a la mateixa exposició d'1/8 s, el camp difús del R6 cau de −7 % a 1,5 R☉ a **−23 % a 6 R☉** entre C2+9 i C2+71. Un sol número de fons per exposició no descriu les dades. Resta el fons **per fotograma i en coordenades heliocèntriques**, amb el model de G3.

#### Criteri objectiu de bo

1. **Cobertura:** el mapa `hdr_pesos` no pot tenir cap píxel amb suma de pesos zero dins de la regió de 1,05 a 6,0 R☉. És el requisit (e) del paper i és fail-closed: si en surt un, falta una exposició o la màscara lunar és massa gruixuda.
2. **Continuïtat entre esglaons:** pren un anell a 2,0 R☉ i compara la mediana que hi aporten dos esglaons consecutius de l'escala, cadascun sol. Han de coincidir dins del **3 %**. Si no, la calibració d'exposició està malament (i el sospitós número u és el 10,0 contra 10,3 s).
3. **Sense costura al limbe lunar:** el perfil radial del compost, mesurat en 36 sectors de 10°, no pot tenir cap salt superior al **5 %** en creuar r = radi lunar + 6 px.
4. **Rang dinàmic assolit:** la raó entre el percentil 99,9 dins d'1,1 R☉ i la mediana a 6,0 R☉ ha de superar **10⁴**. El paper diu que la corona sola cobreix ~1:1000 i que amb protuberàncies i cromosfera puja a 1:10⁶; amb la Lluna tapant les perles i sense el disc, 10⁴ és el que hauries de veure.
5. **Coherència entre trens:** un cop normalitzats a f/2,8 ISO 100, els perfils radials dels dos compostos han de coincidir dins de **0,25 EV** entre 1,5 i 3,5 R☉. Aquesta és la prova que tanca tot el calibratge: dos instruments diferents, dos operadors de calibratge diferents, la mateixa corona.

#### Cost de càlcul

Una passada per fotograma amb aritmètica de float64: **~4 s per fotograma** al R6 (32 M píxels × 3 canals) i ~5 s a la Sony. Total **25 minuts**. La memòria és el problema: no carreguis els 124 alhora (serien 48 GB). Acumula incrementalment el numerador i el denominador de l'equació (4) i llegeix un fotograma cada cop. Pic de memòria: **~2,5 GB**.

---

### G6 — Visualització controlada

#### Què s'ha de produir

```
G6/vis_wow_<cos>.tif       16 bits, per mirar
G6/vis_mgn_<cos>.tif       16 bits
G6/vis_achf_<cos>.tif      16 bits (reimplementació)
G6/vis_final.png           8 bits, sRGB, la imatge que es publica
G6/params_visualitzacio.json
```

⚠️ **Cap d'aquests fitxers no torna a entrar en cap càlcul.** El producte científic és `G5/hdr_*.tif`. Aquesta porta produeix representacions per mirar, i totes destrueixen la fotometria a propòsit.

#### Amb quin mètode i per què — aquí el dossier s'ha de corregir

El dossier recomanava l'ACHF de Druckmüller com a primera opció. **No ho ha de ser, per quatre motius que es poden comprovar:**

**(a) L'ACHF publicat no és implementable.** El paper de 2006 no dona cap fórmula de nucli: dona quatre condicions i els autors mateixos escriuen que *«these requirements, of course, do not define C(k,l) uniquely and several parameters must be set intuitively»*, amb 38 paràmetres a la versió 3.0. La fórmula sí que existeix, però a la tesi completa de Druckmüllerová (§5.2, eqs. 5.1 i 5.2), i allà mateix es diu que és **el predecessor** de l'ACHF viu: l'actual (Corona 4.1) hi afegeix un joc de filtres amb σ diferents combinats més *«nonlinearity in the use of filtered images»* que no està descrita enlloc. El programa no es distribueix i no té versió de macOS.

**(b) L'única font que diu «el millor» és el seu autor, i és de 2013.** La frase de la tesi és *«the best nowadays used structure enhancement technique»*. És una autoavaluació amb un «nowadays» ancorat fa tretze anys.

**(c) El criteri pel qual l'ACHF guanya és el que aquests trens no poden cobrar.** El seu avantatge declarat és el **detall més fi**. Amb 2,158 ″/px, el R6 no resol res per sota d'uns **4,3 ″** (dos píxels; la difracció del VSD90SS, 1,26 ″, no mana); la Sony a 3,234 ″/px es queda cap a **6,5 ″**. Druckmüller declara 2–3 ″ de resolució a les seves compostes. Estàs submostrejat per un factor 1,5–2 respecte del terreny on l'ACHF és superior. La frase del dossier «amb 2,158 ″/px la R6 hi és just» confon mostreig amb resolució: hi és **curt**.

**(d) Hi ha tres alternatives obertes a la mateixa carpeta que no s'havien avaluat:** MGN (Morgan i Druckmüller 2014), **WOW** (Auchère et al. 2023) i RHEF (Gilly i Cranmer 2025). Les tres tenen codi corrent i públic.

**Primera opció: WOW.** Motius verificats al seu propi text: criteri objectiu en lloc d'ajust subjectiu (*«most of them require the ad hoc tweaking of parameters... our aim was... based on an objective criterion»*), l'únic paràmetre lliure són els nivells de significació del soroll, és ~2× més ràpid que MGN i —el que decideix per a aquest projecte— la seva variant amb pesos bilaterals per la variància local existeix explícitament *«to suppress the undesirable halos otherwise produced by discontinuities in the data»*. El teu front obert és el halo; el filtre que el nomena guanya.

**Segona opció: MGN**, `sunkit_image.enhance.mgn`.

**Tercera: RHEF**, `sunkit_image.radial.rhef`, sense paràmetres, per a una lectura ràpida i reproduïble.

**Quarta: reimplementació de l'unsharp mask polar** de l'eq. (5.1)+(5.2) de la tesi, per curiositat i per comparar.

#### Paràmetres concrets

⚠️ **Abans de res: `sunkit-image` no és instal·lat a cap dels tres intèrprets del Mac.** Comprovat. Cal `~/.venvs/eines-ia-py312/bin/pip install sunkit-image` (la versió provada és la **0.7.0**).

**WOW** — `pip install` des de `github.com/frederic-auchere/wavelets`. Fes servir la variant *edge-aware*. Nivells de descomposició: **6** al R6 (cobreix de 2 a 64 px, o sigui de 4,3 ″ a 138 ″) i **6** a la Sony. Nivell de significació del soroll: **3σ**, amb σ pres del master dark corresponent propagat pel compost.

**MGN** — la signatura real, comprovada a la 0.7.0:

```python
mgn(data, *, sigma=None, k=0.7, gamma=3.2, h=0.7, weights=None,
    truncate=3, clip=True, gamma_min=None, gamma_max=None)
```

Tres avisos verificats executant-la: **tots els paràmetres després de `data` són només per nom** (una crida posicional peta amb `TypeError`); **exigeix `dtype` float i dades normalitzades pel temps d'exposició** (amb `uint16` el `clip` es desactiva en silenci perquè `1e-15` trunca a 0); i **modifica l'array del cridant en el lloc** i retorna `float32`, no `float64` — passa-li sempre una còpia.

Valors per a aquestes dades: `sigma=[1.25, 2.5, 5, 10, 20, 40]` (el defecte, i cobreix bé el teu mostreig), `k=0.7`, `gamma=3.2`, `h=0.7`, `clip=True`. Entrada: el compost de G5 dividit pel seu percentil 99,9 i en `float32`.

**RHEF** — ⚠️ els filtres radials **no accepten arrays**: `fnrgf(array)` peta amb `AttributeError: 'numpy.ndarray' object has no attribute 'wcs'`. El primer argument es diu `smap` i vol un `sunpy.map.GenericMap` amb metadades WCS. Per a TIFF d'eclipsi has de construir la capçalera a mà: `CRPIX1/2` al centre solar mesurat, `CDELT1/2` = 2,158 o 3,234 arcsec/px, `RSUN_OBS` = 959,0, `CUNIT` = arcsec.

**Unsharp mask polar (el «pre-ACHF»)** — eq. (5.1) de la tesi:

```
C(ρ,φ) = exp( −[(r−ρ)² + (r(φ−ϕ))²] / 2σ² )
```

amb convolució **incompleta** normalitzada pel sumatori de `C·w`, on `w` és el pes de pertinença a la corona (0 dins del disc lunar, 1 fora). Rang útil de σ: **0,5 a 64**; límits d'integració ±2σ. Fes-ho amb el joc {2, 4, 8, 16, 32} i combina'ls amb pesos iguals. La normalització pel sumatori de `C·w` és el que respon la pregunta que el paper de 2006 deixa oberta —si el nucli es renormalitza després d'anul·lar-ne coeficients—: **sí**.

**⛔ El que no s'ha de fer servir:** el filtre *Radial Blur / Spin* de Photoshop. La tesi demostra que és direccional (mai realça les estructures tangencials) i que el seu espectre de fase arriba a valors de tot el rang 0–2π, o sigui que **desplaça estructures i n'inventa**. L'argument històric de la tesi és fort: durant anys es va creure que els models de camp magnètic estaven equivocats perquè no mostraven el que sortia a les imatges filtrades així, i els equivocats eren les imatges.

#### Criteri objectiu de bo

1. **Prova de fase zero:** convoluciona una imatge sintètica amb dues línies fines creuades (una radial i una tangencial) amb el mateix filtre. Cap de les dues no es pot desplaçar més de **0,2 px** i les dues han de sortir amb amplituds dins d'un factor **1,5**. És la prova que separa un filtre isòtrop d'un de direccional.
2. **Prova de no-invenció:** aplica el filtre a un camp de soroll gaussià pur amb el mateix perfil radial que el compost. No hi poden aparèixer estructures radials ni tangencials coherents per damunt de **4σ**.
3. **Comparació de les quatre eines:** genera les quatre sortides sobre el mateix compost, superposa-les per parelles en canals de color diferent (el truc de la figura 5 del paper de 2006: un en blau i l'altre en taronja; si són idèntiques surt gris) i mira on discrepen. **No triïs per bellesa: tria per on les quatre coincideixen.** El que apareix en tres de quatre és estructura; el que apareix en una és probablement del filtre.
4. **Contrast entre trens:** les estructures a gran escala (bagues, plomalls polars) han de ser **les mateixes** als dos cossos. Són òptiques i sensors diferents mirant el mateix Sol amb 20 minuts d'escala de temps solar: una estructura que només surti en un és un artefacte.

#### Cost de càlcul

WOW: **1–3 minuts** per compost. MGN: **2–5 minuts**. RHEF: menys d'un minut. L'unsharp mask polar amb cinc σ i convolució incompleta píxel a píxel: **hores** si es fa ingènuament; remostrejant a graella polar i convolucionant en 2D separable, **10–15 minuts**.

---

## 3. Decisions que ha de prendre Pere

### D1 — Quin instant representa el compost

L'equació (3) fa que el compost representi el Sol **a l'instant de la imatge de referència**. Amb 103,7 s de totalitat i la Lluna movent-se 28,4 px al R6, tries quin.

| Opció | Cost |
|---|---|
| Mig de la totalitat | La corona d'un extrem hi entra amb pes reduït per la màscara lunar. **Recomanat.** |
| Just després de C2 | Guanyes les perles i el primer anell; perds la corona del costat de C3 |
| Just abans de C3 | Al revés |

**Recomanació de l'equip: mig de la totalitat**, un fotograma de 1/500 del R6. La pèrdua als extrems és de ~28 px sobre un disc de 916 px de diàmetre: un 3 %. Els contactes tenen les seves pròpies imatges i no s'han de barrejar amb la corona.

### D2 — Un compost per tren o un de fusionat

| Opció | Cost |
|---|---|
| Dos compostos separats | Cada un conserva la seva escala de placa i el seu calibratge. **La prova de coherència entre trens (0,25 EV) continua sent possible i és la millor validació que tens.** Recomanat. |
| Un de fusionat | Guanyes ~1,3× de senyal a les alçades on tots dos hi arriben, però has de remostrejar un dels dos (1,50× d'escala) i llavors la prova de coherència es converteix en circular |

**Recomanació: dos compostos separats, i la fusió com a exercici posterior si de cas.** El paper de 2006 fusiona instruments diferents (figura 14), o sigui que es pot fer; però ells no tenien dues mesures independents per validar-se i tu sí.

### D3 — Deconvolucionar o restar el halo

| Opció | Cost |
|---|---|
| Deconvolució Richardson-Lucy, 20 iteracions | Restitueix contrast real i és el mètode físicament correcte. Amplifica el soroll i costa ~3,5 h de càlcul. Si la PSF està mal mesurada, **inventa** estructura |
| Restar el halo com a camp additiu | Segur, ràpid, no inventa. No restitueix el contrast que la PSF ha destruït |

**Recomanació: decidir-ho pel criteri numèric de G3, no per gust.** Si `α` surt amb una incertesa inferior al 20 % i les dues òptiques donen un earthshine coherent dins de 0,3 EV, deconvoluciona. Si no, resta i documenta que el contrast està subestimat.

### D4 — Què fer amb els 34 fotogrames Sony sense dark propi

Hi ha 34 fotogrames (1/1000 ×21, 1/500 ×11, 1/640 ×2) que no pertanyen a cap bloc del programa i que es van calibrar amb el master de 1/6400 com a bias.

| Opció | Cost |
|---|---|
| Excloure'ls | Perds 34 de 194, però cap del nucli de totalitat (que en són 33) |
| Conservar-los amb bias | El bias d'1/6400 és bo com a bias; el corrent fosc d'1/1000 a 40 °C és menor que el soroll de lectura |

**Recomanació: conservar-los, però marcats.** No entren als anells d'ajust de G3 ni a la prova de linealitat. Poden entrar a G5 amb pes normal.

### D5 — Fins on publicar

Quan tinguis quatre visualitzacions del mateix compost i totes siguin defensables, la tria és estètica i és teva. **L'única regla de l'equip: publica al costat el criteri i els paràmetres.** Si a `params_visualitzacio.json` hi ha WOW amb 6 nivells i 3σ, qualsevol pot reproduir-ho; si hi ha un ajust a mà de corbes, ningú.

---

## 4. Riscos concrets d'aquestes dades

### R1 — Els dos salts de la Sony

Mesurats amb exposicions aparellades: **+228 px en x** entre C2+25,6 i C2+42,6, i **−710 px en y** entre C2+42,6 i C2+58,6. `research/72` en diu +223 i −715 a C2+30 i C2+50. Causa documentada per testimoni: **en treure el filtre solar es va moure la lent de 300 mm** i la pertorbació es va alliberar amb retard, en dos temps.

**Conseqüència operativa:** la Sony té **tres segments d'apuntat estables**, no un. Dins de cada segment l'estabilitat és de 0,5–1 px, que és excel·lent. Entre segments, l'apuntat canvia més que qualsevol residu de registre.

**Què s'ha de fer:** registrar cada segment **contra la mestra global**, no contra el fotograma anterior. La correlació de fase se'n surt bé —un desplaçament de 710 px és petit comparat amb el camp— però **la màscara en anell s'ha de recentrar per segment** o `r2` deixarà part del fotograma fora. I si el pic/soroll baixa de 6,0 als fotogrames del salt mateix, és perquè aquell fotograma està mogut, no perquè el registre falli.

### R2 — La DSC06990

És la **segona àncora d'earthshine** de la Sony i està **moguda perquè la muntura va cedir durant l'exposició de 8 s**. Aquest fotograma:

- **Queda fora** de l'ajust del model de halo de G3. És la mesura més profunda que tens del disc lunar, i és la que menys pots fer servir.
- **Queda fora** de G5 amb pes 0 explícit al `manifest_v2.csv`, no per llindar automàtic (el llindar no detecta una moguda).
- **Les àncores 1 i 3 sí que hi entren**, i són la millor font d'earthshine de tota la flota: 0,5–0,75 px de moguda interna.

Amb dues àncores de 8 s en lloc de tres, la integració d'earthshine de la Sony baixa de 24 s a **16 s**. El terra de la porta de durades era 24 s amb zero marge: no el compleixes. **No és fatal per al postprocessat** —el terra era un requisit de captura, no de reducció— però el senyal/soroll de l'earthshine baixa un 18 % i s'ha de dir a qualsevol resultat que en depengui.

### R3 — El pedestal fals de libraw a la R6 III

Documentat a `research/71`: **el negre de metadata de libraw és fals; el pedestal real és 511–512, pla.** Els `black_level_per_channel` que retorna rawpy són `[0, 31, 94, 63]`, que no descriuen res.

**Què s'ha de fer:** al recalibratge, **no restar el negre de LibRaw**. Restar el **master dark**, que ja porta el pedestal real dins, i verificar que el pedestal del master és 512,0. Els masters del R6 el tenen a 512,0 **excepte el de 10 s, que el té a 511,0** — precisament l'esglaó de l'earthshine. Un compte de diferència sobre un fons de ~20 comptes és un **5 %** d'error al fons més profund que tens.

**Acció concreta:** torna a construir el master de 10 s amb els mateixos darks, comprova si el 511,0 ve d'un fotograma dolent (mira'n la desviació típica un a un) i, si el 511,0 és real, documenta'l i fes servir 511,0 per a aquells tres fotogrames. **No l'arrodoneixis a 512 per estètica.**

I el segon defecte del banc: **el master de 0,5 s té fotogrames amb desviació típica de 4,3 a 55,1 comptes** quan tots els altres van de 2,7 a 2,9. Com a mínim un d'aquells 16 «darks» no és fosc. Torna'l a construir amb rebuig de valors atípics: descarta qualsevol fotograma amb σ per damunt de **3,5**.

### R4 — La deriva de 29 px

De `research/71`: la deriva lliure post-C3 mesurada és **0,689 ″/s**, de la qual ~0,21 és refracció i ~0,48 muntura (error polar ~2°, alineació diürna). A totalitat, la deriva resolta és **~0,61 ″/s ≈ 29 px**, compartida per Sol i Lluna. La meva mesura independent per correlació de fase sobre el R6 dona **0,71–0,75 ″/s** en quatre parelles: un 18 % més alta, mateix ordre, i probablement inclou un tros de correcció manual.

**El punt important i que és fàcil d'equivocar:** aquesta deriva és **comuna** al Sol i a la Lluna. El **relatiu no es toca**. La deriva de 29 px l'absorbeix el registre de corona sencera; el que **no** l'absorbeix és el moviment relatiu Lluna–Sol de 0,5905 ″/s. Si intentes corregir la deriva i el moviment relatiu amb la mateixa transformació, en perdràs un dels dos.

**A `research/71` també hi ha que les correccions manuals de Pere són visibles als fotogrames.** Això vol dir que la deriva **no és una recta**: té esglaons. Un ajust lineal global de l'apuntat contra el temps donarà residus grossos. Ajusta **lineal a trossos**, amb punts de ruptura detectats pels residus, o simplement fes servir el desplaçament mesurat de cada fotograma sense model.

### R5 — El flare de l'òptica fix al sensor

Aquest és el risc silenciós i el paper de 2006 l'avisa expressament: *«a particularly complicated problem is caused by dust on sensors. The global maximum in the image C often represents the correct alignment for dust particles and not for coronal structures»*.

**El mecanisme:** qualsevol patró fix al sensor —pols, un reflex intern de l'òptica, un gradient d'amplificador— és **idèntic a tots els fotogrames** i correlaciona molt més fort que unes estructures coronals de contrast baixíssim. El màxim global surt a desplaçament zero i el registre no fa res.

**Símptoma diagnòstic:** si els desplaçaments mesurats surten sistemàticament propers a (0,0) quan el cel s'ha mogut de veritat, el registre s'ha enganxat al sensor.

**Tres defenses, i cal posar-les totes tres:**

1. **El flat-field ja tret** al recalibratge treu la pols i part del gradient fix.
2. **El filtre tangencial `H_ρ`** treu les freqüències baixes en direcció tangencial, que és on viu un flare llis.
3. **La comprovació explícita del paper:** si el màxim global és a menys de 2 px de (0,0) i el temps entre els dos fotogrames és superior a 5 s, **rebutja'l i busca el següent màxim local**. Amb 0,61–0,75 ″/s de deriva, 5 s són 1,4–1,7 px al R6, o sigui que el llindar és just: fes-lo servir amb parelles separades més de 10 s, on el desplaçament esperat és 3–4 px.

I una defensa addicional que tens gratis: **compara els dos trens**. Un flare és de l'òptica; si el R6 i la Sony donen la mateixa estructura al mateix lloc del cel, no és flare.

---

## 5. El que NO s'ha de fer

**1. No aplicar cap filtre de realçat abans de l'HDR.** WOW, MGN, RHEF, ACHF, NRGF i FNRGF són tots operacions **no lineals i dependents del contingut**. Aplicats fotograma a fotograma i després apilats, l'apilat ja no és una mitjana de brillantors: és una mitjana de contrastos locals, i el resultat no vol dir res. La tesi de Druckmüllerová ho declara com a precondició del filtre: l'entrada ha de ser *«a result of the sequence of steps starting from image acquisition including image calibration, registration and composition in one high-dynamic-range image»*. G6 va **després** de G5, sempre, i sobre una còpia.

**2. No alinear corona i Lluna alhora.** Es mouen l'una respecte de l'altra a 0,5905 ″/s: **28,4 px al R6 i 18,9 px a la Sony al llarg de la totalitat**. Una sola transformació no pot fer coincidir les dues. Si intentes un registre de compromís, tindràs la corona moguda 14 px i la Lluna moguda 14 px, o sigui les dues coses malament. Dues piles, dues transformacions, i al final es componen amb la màscara de pes −1.

**3. No fer servir 65535 com a llindar de saturació.** Ja s'ha explicat: al canal vermell el retall és 1,00 EV (R6) i 1,32 EV (Sony) per sota del pou real, i el 5,55 % del vermell de l'exposició de 10,3 s que el TIFF declara cremat no ho està.

**4. No retallar a zero.** Un fons amb soroll ha de tenir mostres negatives. `np.clip(0)` converteix la mediana en un estimador esbiaixat i fa que la prova de linealitat doni 9,0 on hauria de donar 4,0.

**5. No fer servir el rectangle fix de «cel».** Els dos scripts fan servir files 300:1300 i columnes W−1700:W−200. Al R6 la cantonada més propera d'aquest rectangle és a **4,2–5,1 R☉** i el centre a **6,2–7,1 R☉**: és de ple dins del domini de corona F i de halo instrumental, que és exactament el que G3 ha de modelar. A la Sony és 11,5–14,6 R☉, millor però tampoc net. I és fix en píxels mentre l'apuntat es mou 739 px. El fons es mesura **per fotograma i en coordenades heliocèntriques**.

**6. No fer servir la prova unitària «A₀ = S₀ = 1 i la resta zero ha de donar el NRGF».** El paper de 2011 ho afirma i **és fals**. Comprovat numèricament amb una corona sintètica de 801×801, n_s = 50 segments: la mitjana coincideix dins del 0,1–0,2 %, però la mitjana de les desviacions típiques dels segments queda **89 % per sota** de la desviació típica de l'anell sencer, perquè per la llei de la variància total li falta la variància **entre** segments. La imatge sortiria unes 9 vegades més estirada. La reducció exacta al NRGF és **n_s = 1**, tal com diu la tesi.

**7. No implementar l'eq. (9) del FNRGF-N tal com està publicada.** El paper de 2011 diu de **restar** `m·√(DN)` al denominador. La mateixa autora ho repudia a la tesi de 2013: *«a misleading idea»* que porta a **amplificació infinita** a les zones que només tenen soroll. El que funciona és **sumar** una variància artificial `V_n` a les variàncies locals abans de l'arrel, amb `√(V_n)` entre el **10 % i el 15 %** de la desviació del soroll.

**8. No programar l'apèndix del centre solar del FNRGF sense corregir-ne les errates.** (A2) defineix la «normal» al moviment lunar com `(Mdx, −Mdy)`, que **no és perpendicular** a `(Mdx, Mdy)`; ha de ser `(Mdy, −Mdx)`. (A4) escriu `n_x` a les dues components; la segona ha de ser `n_y`. I la definició de `h` fa servir un símbol `N` que no es defineix enlloc; és `B`. De tota manera, **no et cal**: tens els contactes reals llegits de les imatges (C2 a −1,0 s i C3 a +102,7 s del predit, totalitat real 103,7 s) i les escales mesurades. Aquest apèndix serveix a qui no té les dues coses.

**9. No aplicar la condició (d) de l'ACHF tal com està impresa.** El paper de 2006 diu *«c(k,l)_{i,j} = 0 if pixels a_{k,l} and a_{i,j} belong to significantly different parts»*. Els píxels a comparar són `[x,y]` i `[x+i, y+j]`, com escriu bé la tesi. Implementat literalment, compararies cada píxel amb el píxel absolut `(i,j)` del cantó de la imatge.

**10. No fer servir el *Radial Blur / Spin* de Photoshop** (ja argumentat a G6). I no fer servir cap ajust de corbes «a ull» sobre el compost lineal.

**11. No esborrar `Calibrated_Claude/` ni `300mm/calibrated/`.** Són evidència del que es va fer. El recalibratge crea directoris nous.

**12. No prendre els «124 fotogrames de totalitat» i els «194» com el que diuen.** Els 124 del R6 abasten **207,65 s d'EXIF**, el doble de la totalitat: amb C2 ancorat a la primera foto (C2−14,75 de la V1.02), només **~68 cauen dins [C2, C3]** —23 són abans de C2, 30 després de C3 i 3 són parcials documentals a 1/320 a C3+30/+60/+90 s. Els 194 de la Sony abasten **6.297 s** (1 h 45 min) i el **nucli de totalitat són 33**; 122 són parcials filtrades a 1/400. **Conseqüència de registre:** als 53 fotogrames del R6 de fora de totalitat la referència no és la corona sinó un creixent fotosfèric, i una correlació de fase sobre estructura coronal s'hi enganxarà al creixent. Aquests fotogrames van a una pila a part, no a la de corona.

---

## 6. Ordre de treball

### Sessió 1 — Recalibratge (mig dia)

1. Comprovar espai lliure: calen ~150 GB (o ~85 GB amb `zstd`).
2. Copiar `lot_calibratge_vixen.py` i `lot_calibratge_300mm.py` a versions `_v2` i canviar-hi: `use_camera_wb=False`, `user_wb=[1,1,1,1]`, `output_color=raw`, `highlight_mode=Ignore`, `gamma=(1,1)`, `no_auto_bright=True`, sortida `float32`, cap `np.clip(0)`.
3. Reconstruir el master dark de 0,5 s del R6 amb rebuig de σ > 3,5. Investigar el pedestal 511,0 del master de 10 s.
4. Llegir l'exposició de l'EXIF (`exiftool`) i corregir 10,0 → **10,3 s**.
5. Executar els dos lots (~15 min de càlcul).
6. **Fita 1:** els quatre criteris de G2-bis en verd. Si la prova de linealitat no dona 4,167 ± 0,15 a 3 i a 5 R☉, **para i diagnostica**; no continuïs.

### Sessió 2 — G3, mesura del halo (un dia)

7. Ajustar els centres lunars sobre els fotogrames curts; construir el model de deriva lineal a trossos.
8. Extreure `I_dins(r)` en 40 anells sobre els 12 fotogrames profunds (menys la **DSC06990**).
9. Ajustar `E`, `A`, `α`, `r0` per cos.
10. **Fita 2:** l'earthshine dels dos trens coincideix dins de **0,3 EV** i el residu és pla dins del **±8 %**. Aquí es decideix **D3** (deconvolucionar o restar).

### Sessió 3 — G4, registre (dos dies, la major part de càlcul desatès)

11. Implementar `H_ρ` per graella polar (amb les tres correccions d'errates).
12. Escombrada de σ a 4096×4096 sobre 10 fotogrames de prova; fixar la finestra bona de σ.
13. Executar el registre de corona sencer amb el σ guanyador, a mida completa, contra la mestra de cada cos. **Deixar-ho corrent de nit.**
14. Registre de la Lluna per centroide de vora + RANSAC sobre els curts; interpolació als profunds.
15. **Fita 3:** residu de corona < 0,3 px, pendent de deriva compatible amb 0,5905 ″/s dins del 10 %, rotació < 0,05°, i la prova de `r1` + 40 px sense canvis > 0,5 px.

### Sessió 4 — G5, composició (mig dia)

16. Construir els mapes de pes per fotograma i per canal amb els llindars de §G5 (5σ = 14 comptes, sostre 13.940 al verd del R6).
17. Màscares lunars del model de G4, eixamplades 6 px.
18. Triar la referència `j` (decisió **D1**) i acumular numerador i denominador incrementalment.
19. Aplicar la correcció de halo de G3 (restada o, si toca, deconvolució de ~3,5 h).
20. **Fita 4:** els cinc criteris de G5. El decisiu és el **5**: els dos trens dins de **0,25 EV** entre 1,5 i 3,5 R☉. Si no hi arriben, hi ha un error de calibratge i no es passa a G6.

### Sessió 5 — G6, visualització (mig dia)

21. `~/.venvs/eines-ia-py312/bin/pip install sunkit-image` i el paquet de WOW.
22. Generar les quatre sortides sobre el mateix compost.
23. Proves de fase zero i de no-invenció sobre imatges sintètiques.
24. Superposició per parelles en colors oposats; identificar on coincideixen les quatre.
25. Comparació entre trens: tota estructura a gran escala que només surti en un cos, marcada com a dubtosa.
26. **Fita 5:** `vis_final.png` amb `params_visualitzacio.json` al costat, i el `G5/hdr_*.tif` intacte com a producte científic.

### Resum de temps

| Fase | Càlcul | Persona |
|---|---|---|
| G2-bis | 15 min | 3 h |
| G3 | 10 min (+3,5 h si deconvolució) | 6 h |
| G4 | 1,5–8 h (desatès) | 5 h |
| G5 | 25 min | 3 h |
| G6 | 10 min | 4 h |

**Total realista: cinc sessions, unes tres setmanes a ritme de cap de setmana.** El coll d'ampolla no és el nombre de fotogrames —Druckmüller en fa servir «almenys 10 o més» amb 20–50 s de temps efectiu total, i tu tens 68 i 33 dins de totalitat— sinó **la qualitat del registre i la fiabilitat del model de halo**. Les dues fites que decideixen si el resultat és publicable són la **Fita 2** (coherència de l'earthshine entre trens) i la **Fita 4** (coherència dels perfils radials dins de 0,25 EV). Si totes dues surten, tens una corona defensable; si en falla alguna, tens un error de calibratge que cap filtre de visualització no arreglarà.