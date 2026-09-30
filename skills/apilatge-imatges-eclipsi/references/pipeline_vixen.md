# Pipeline Vixen (VSD90SS + R6 III), etapa per etapa

Font: lectura línia a línia de `3-RECERCA/tools/hdr_corona_vixen.py` (2.537
línies), `apila_hdr4_vixen.py`, `prnu_vixen.py`, `masters_vixen_v2.py` el
17-08-2026, i `3-RECERCA/76`, `78`. Rutes: totes surten de `Path.home()`.

Intèrpret: el que `scripts/comprova_entorn.py` detecti (avui
`~/.venvs/eines-ia-py312/bin/python`). Es treballa des de l'arrel del
repositori perquè `hdr_corona_vixen.py` carrega `de440s.bsp` amb ruta relativa
si no el troba a la cau (⚠️ per això hi ha un `de440s.bsp` orfe a l'arrel;
el bo és `~/.cache/skyfield/de440s.bsp`).

## Entrades i sortides

- `SRC = 0-RAW/Vixen R6III/Vixen Fase totalitat/` (124 CR3), `MASTERS = SRC/Masters_v2/`
- `OUT = 4-RESULTATS/derivats/Vixen/Corona_HDR_Vixen/`
- `HDR4 = 4-RESULTATS/derivats/Vixen/HDR4/`
- Darks: `0-RAW/Vixen R6III/Darks Canon R6III Eclipse/`

## 1. `masters_vixen_v2.py`

Per a cada exposició present als lights: els ≤ 16 darks més a prop de 41,5 °C
(`CameraTemperature` de l'EXIF), mitjana retallada mín/màx per píxel, **sense
restar cap pedestal** (el master el porta a dins: 511,5 real). Escriu
`Masters_v2/master_<exp>.npy` i un JSON amb quins darks hi entren. La R6 té dos
modes de lectura (σ 2,72 ADU si t < 1 s; 1,05 si t ≥ 1 s) i el master de 0,5 s
és sensible a la barreja tèrmica entre runs: per això mitjana i no mediana, i
per això la finestra de temperatura.

## 2. `prnu_vixen.py` (v2)

24 fotogrames ≥ 1/30 s, finestra 9×9, senyal mínim 40 ADU per damunt del fosc,
màscara d'estrelles independent (6 σ sobre la mediana 7×7, dilatada 3 px de
pla), mitjana local normalitzada, un rebuig a 3,5 σ, encongiment `2r/(1+r)`
(r ≈ 0,8). Escriu `Masters_v2/prnu.npz` (+ `prnu.json`). ⛔ Iterar el rebuig
sense màscara convergeix al mode equivocat; el v1 (sense màscara) és
`prnu_v1_amb_estrelles.npz`.

## 3. `hdr_corona_vixen.py geometria`

- `exiftool`: `SubSecDateTimeOriginal`, `ExposureTime`, `CameraTemperature`.
  L'EXIF de la R6 marca l'**inici**; `t_rel_c2 = inici + exp/2` amb C2 local
  20:28:45. `EXP_REAL` corregeix 0,0003125 → 1/3200 i 10,0 → 10,3.
- `dins_totalitat`: 0 ≤ t ≤ 103,7 s → 68 fotogrames.
- Limbe lunar al pla verd a mitja resolució: 360 angles, creuament al 50 %
  entre mediana interior i exterior en r ± 40 px, cercle robust (5 iteracions,
  3·MAD); acceptat si n ≥ 200 punts i rms < 1,5 px. Els 26 de 1/3200 no tenen
  limbe: fan servir el model.
- Model de deriva: recta robusta x(t), y(t). Centre solar = model lunar −
  `desplacament_lluna_sol` (skyfield, DE440s, `wgs84.latlon(LLOC)`, RA/Dec
  aparents projectats amb els vectors nord/est del PA), i després **ancoratge
  absolut**: tota la sèrie es desplaça perquè a 572A2983 el Sol caigui a
  `ANCORA_SOL = (3570,8, 2267,1)` (placa estel·lar, `3-RECERCA/75` §5.1).
- Sortida: `manifest.csv` (17 camps: nom, t_rel_c2, exp, temp, centres lunars
  model i mesurat, limbe_n/rms, sol_x/y, n_sat, escala_rel, usat, nota) i
  `geometria.json`. Valors vius: deriva 0,5764 ″/s; Lluna−Sol 0,5973 ″/s;
  residus del model lunar 0,28/0,40 px.

## 4. `deriva` (QA, no s'aplica)

Auxiliar = verd/exp amb els saturats a NaN, `normalitza_radial` (dividit pel
perfil azimutal medià en anells de 2 px des de R_LLUNA+30), finestra 2000×2000
amb Hanning, `phase_cross_correlation` (upsample 20, `normalization="phase"`)
entre parelles de la mateixa exposició amb Δt ≥ 8 s i `n_sat ≤ 12000`. Escriu
`deriva_corona.json`: **0,5781 ″/s a +46,5°, residu 0,11/0,08 px** (5 parelles).
Marca «enganxat al flare» si mesura < 2 px amb model > 4 px.

## 5. `escala` (QA, retirat de la composició)

Perfils anulars medians del verd (anells 0,04 R☉ de 1,06 a 6,6, fora del
disc+10), ajust global `p_f(r) = k_e·t_f·C(r) + c_f` amb rebuig 3·MAD; escriu
`escala_global.json` (factors 0,956–1,073) i grava `escala_rel` al manifest.
`ESCALA_UNITAT=1` per defecte: **l'HDR no els aplica**. `3-RECERCA/78` §3 va
demostrar que part d'aquella correlació amb el temps era **extinció**
(k = 0,402 mag/X, −5,5 % de C2 a C3) i la resta cel; refer-ho és PENDENT.

## 6. `hdr`

- Reixa = mida del mosaic (4638×6958), Sol al centre `(H/2, W/2)`.
- Per fotograma: `rn` segons el mode; `t = exp_s`; màscara lunar suau
  `clip((d − (460+4))/14)` amb el centre lunar del model; `anivella_fons`
  (mediana per pla a 4,2–5,1 R☉ dividida per `exp·escala_rel`, referència = la
  mediana dels 68, i es resta la diferència en comptes; `SENSE_FONS=1` ho
  apaga).
- Per pla de Bayer: `w = t²/(max(pla,0)/g + rn²)`, `taper = clip((SOSTRE −
  pla)/(RAMPA_SOSTRE·SOSTRE))` amb `RAMPA_SOSTRE=0,80` (el pes baixa linealment
  des de 0,2·SOSTRE), `w = 0` per damunt de SOSTRE (13.490,8 sobre el fosc);
  `val = pla/t`; dipòsit drizzle amb `pesos_gota` de `PIXFRAC=2,0` px de
  sortida, sumat per paritat a `num/den/ncon`.
- Sortides: `hdr_vixen_countss.npy` (float32 RGB, ADU/s, NaN on ningú va veure
  res), `hdr_vixen_var.npy` (1/den), `hdr_vixen_cobertura.npy` (uint16),
  amb `HDR_SUFIX`/`SUFIX` opcional. Cobertura mediana 294 a 1,05–6 R☉;
  112.699 píxels buits al disc.
- ⚠️ Inconsistència de codi coneguda: `anivella_fons` fa servir `escala_rel`
  i el pes/valor no. I la convenció del mig píxel del centre difereix de la
  d'`apila_hdr4_vixen.py` (≤ 0,5 px de «Sol al centre»). Cap de les dues afecta
  el registre entre fotogrames.

## 7. `vis` i `tiff`

- L = `0,5·(G + kr·R)` amb `kr` = mediana G/R a 1,3–1,5 R☉ (~1,25); el blau
  fora (guany anòmal 4,33 e⁻/ADU i FWHM 1,4× més gran).
- Cel = constant (mediana a rs > 7,2) + pla ajustat a `L − perfil` per rs > 3,5.
- `perfil_azimutal`: mitjana per anell fins al cercle inscrit (5,20 R☉), i més
  enllà **els mateixos sectors azimutals** enganxats per raó (mai llei de
  potència: dona un colze que surt com un cercle).
- Imprimeix el perfil en B/B☉ (× 2,772·10⁻¹¹) i la continuïtat entre esglaons
  (quadràtica local en log-log, 1,10–5,0 R☉). PNG: `_log`, `_radial`,
  `_detall`, `_color`, retalls de 3 i 1,55 R☉; `vis_luminancia.npy`.
- `tiff`: WB mesurat sobre la corona a 1,1–1,3 R☉ (`1,226 · 1 · 2,768`);
  `corona_vixen_lineal_16b.tif` (65535 = p99,7 del verd dins 1,06 R☉ =
  366.763 ADU/s = 1,02·10⁻⁵ B/B☉; ICC lineal), `_natural.tif` (WB D65 + corba
  log), `_FINAL.tif` (color del POWAAAH3 sobre `vis_luminancia`, presentació).

## 8. `foto` i `passalt`

- `valid` = finit **i dins la caixa `RETALL = (85, 4595, 40, 6830)`**.
- `DETALL=logpolar` (viu): reixa 8192×2048 de r = 400 px a la cantonada,
  `inpaint_radial` cap a dins, `fons_fourier` m ≤ 4 (ridge 5, dues passades,
  rebuig 4·MAD, suavitzat σ3 en ρ, extrapolació C¹ més enllà de l'última
  columna sencera); bandes DoG `BANDES_DEG` = 0,10 · 0,17 · 0,27 · 0,44 · 0,71 ·
  1,16 · 1,86 · 3,0 · 4,9 · 7,9 · 12,8 · 20,8° (isòtropes: σ_ρ = σ_θ·2πK/NA);
  soroll per banda i radi mesurat sobre soroll blanc convolucionat 2×2 i
  remostrejat; Wiener `1 − n²/v`; `GUANYS_DEG = 0,2,4,6,6,5.5,4.5,3.5,2.5,1.4,0`;
  guanys apagats sota σ_img 1,6 px i esvaïts 4,9 → 5,6 R☉; finestra de vora
  smoothstep a 2,5 σ; compressió `0,9·tanh(D/0,9)`.
- `DETALL=px` (antic, per comparar): `perfil_azimutal` + correcció 2-D σ250 +
  `detall_bandes` en píxels.
- Corba `CORBA=sketch` (PCHIP en log-log pels nivells mesurats del sketch de
  Pere; lo = p0,02·0,85 a 1,03–6 R☉, hi = p99,6 dins 1,06 R☉) o `logquad`.
  **Calibrada sobre L sense realçar**; després `t = t·exp(D)` amb genoll a 0,88.
- Color: `WB_DIURN` + `CAM_A_SRGB`, cromaticitat suavitzada σ10 pesada per L,
  tres ancoratges en sRGB: corona 1,35/0,64 (1,5–2,2 R☉), mig 1,17/0,865
  (2,7–3,3), cel 0,90/1,09 (6,2–7,0); desviació local comprimida (`EXP_C` 0,35).
- Earthshine: relleu de `earthshine_disc.npz` (etapa `earthshine`: els tres de
  10,3 s alineats al centre lunar del model, polinomi 2-D grau 4 dins 0,90 r_l),
  σ1,5, esvaït al 96,5 % del radi, 1,50–1,68× el cel de pantalla.
- `passalt`: `0,5 + 0,5·clip(D,±0,9)/0,9` en TIFF sRGB 16 bits (mateix retall
  que la FOTO) + `_D.npy`. Variant `_FORT` amb les bandes 0,3–1,9° a guany 7–10.
- Sortides: `corona_vixen_FOTO.tif`, `_PASSALT.tif`, `foto_params.json`.

## 9. `apila_hdr4_vixen.py`

Depèn del `manifest.csv` de `Corona_HDR_Vixen` (centres, exposicions).
Constants pròpies: retall Canon (108,172) 4640×6960 sobre `raw_image`,
`POU_FISIC` 16382, `SAT_RAW = POU_DNG = 13995`, `PEDESTAL_DNG` 512,
`K_EXTINCIO` 0,402, època comuna 572A2969 (C2+8,4 s), fons comú 572A2972
(0,5 s, C2+11,6 s: el més clar → s'afegeix pedestal, mai se'n treu),
`R_LLUNA_REAL` 453,8, matrius `ColorMatrix1/2` i `ForwardMatrix1/2` d'Adobe,
`BaselineExposure` 0,26.

- `mesura`: registre per correlació de fase (upsample 100, suavitzat σ3 → 6,
  radi interior 600 px o 1,25× el radi de saturació) contra el model, i
  extinció diferencial (`membre = a·ref + b` sobre medianes anulars 1,05–4,8
  R☉; `k = −2,5·log10(a)/ΔX`, Kasten-Young amb altura de skyfield). Escriu
  `qa/registre_mesures.csv`, `qa/extincio_mesures.csv`. El codi aplica la
  constant 0,402, no la mitjana d'aquell run.
- `apila` (`--geometria comuna|propia`, `--nomes 572A2970`): extinció
  `10^(0,4·k·(X−X0))`, anivellament additiu al fons comú, dins el disc de la
  referència només contribueix la referència (r_l + marge + transició 14),
  pesos iguals (0 si saturat), gota 2,0 amb partició de la unitat; escriu DNG
  1.4 LinearRaw 16 bits (`rint(mitja+512)`, buits → 13995, `AsShotNeutral` del
  CR3 de referència, EXIF copiat) i el compacta amb `Adobe DNG Converter -c
  -p1` només si els píxels queden idèntics. QA JSON i prèvia per apilat.
- `munta`: copia els 3 CR3 curts amb prefix d'ordre i escriu `HDR4/manifest.csv`.
- `protuberancies`: cinc grups (1/3200 ×9 a C2, ×17 a C3; 1/2000, 1/500, 1/125
  ×3 tardans), disc cenyit 453,8+2, transició 4 → `protuberancies/*.dng`.
- `capes`: HDR d'època a C2 (2958–2972, ref 2969) i C3 (2997–3025, ref 3005),
  excés d'Hα `E = R − ρ·G` (ρ mesurat a 1,05–1,4 R☉: 0,809/0,814), fons σ40
  restat, màscara 2σ confirmada a 1,5σ, color per la ColorMatrix2 →
  `capa_prot_C2|C3.tif`, `_lineal`, `_Halpha`, `_mascara`.

## Variables d'entorn de `hdr_corona_vixen.py`

`PIXFRAC` (2,0), `RAMPA_SOSTRE` (0,80), `SENSE_FONS`, `SENSE_PRNU`,
`ESCALA_UNITAT`, `SUFIX`, `HDR_SUFIX`, `FOTO_SUFIX`, `DETALL` (logpolar|px),
`CORBA` (sketch|logquad), `GUANYS_DEG`, `G_RAD`, `PASSALT`, `REALCAT`, `EXP_C`,
`EXP_U`, `GAMMA_TO`, `N_NUC`, `N_COR`, `N_CEL`, `NA_POLAR`, `NR_POLAR`,
`ANISO`, `DIAG_LP`.
