# 74 — Pla aplicat de postprocessat de la corona

**Equip assessor privat · 15 d'agost de 2026 · v1.1**

Pla d'obra per a l'eclipsi del 12 d'agost de 2026. La referència de mètodes és
`research/73`; aquí hi ha què s'ha de fer, amb quins números i com es comprova.

⚠️ **Aquesta versió 1.1 corregeix la 1.0 en un punt gros:** el model de halo
**ja existeix i està validat**. El §0 diu què canvia. Si llegeixes una sola
secció, que sigui aquella.

> ⛔ **Actualització del 16-08-2026.** `research/75` mesura vuit coses que aquest
> pla donava per obertes o per suposades, i **la seva §6 llista número per número
> el que canvia aquí**. Els titulars: **el calibratge absolut ja està fet**
> (B/B☉ = 1,134×10⁻¹¹·I a la Sony i 2,772×10⁻¹¹·I al R6, ±10 %, els dos trens
> coincidents al 5 %); **el camp està resolt** amb el nord real a PA 90,27° i
> 57,19°; **no hi havia cap dark dolent**; **el guany està mesurat** (5,08 i
> 3,41 e⁻/ADU); i **els flats no calen per a la imatge però sí que ajudarien per
> a la fotometria del camp**, perquè sense ells extinció i vinyetatge no se
> separen. Llegeix `research/75` §6 abans d'executar cap gate.

## 0. El que canvia la v1.1

### 0.1 El G3 no està obert: està fet a mitges i ben fet

⚠️ **Verificat al disc.** `~/Desktop/Eclipse 2026/Earthshine_FINAL/` (15-08,
20:26) conté un model de halo tancat i validat **fora de mostra**: dos nuclis
d'ales de PSF per canal sobre **la corona real**, més un pla de cel, amb
correlació **r = 0,68** (escala completa) i **0,73** (mitja escala) contra
l'albedo LROC WAC. Paràmetres a `earthshine_FINAL_halo_params.json`; eines a
`research/tools/halo_sony2_full.py`, `halo_vixen_full.py`, `final_rgb_full.py`
i `mesura_sony.py`.

Tres conseqüències:

1. **El model radial que proposava la v1.0 —`I(r) = E + A·(R−r+r₀)^−α`— és
   pitjor i no s'ha de fer.** Assumeix simetria circular respecte del limbe,
   i el halo de dins del disc el genera la corona, que és asimètrica. Un ajust
   radial absorbeix l'asimetria dins d'`E`, i llavors `E` no és earthshine.
2. **El G3 es redefineix**: no és «mesurar un halo» sinó **reajustar el model
   existent sobre dades no retallades i estendre'l al Vixen i al compost**.
3. **La Fita 2 de la v1.0 no es pot complir i s'ha de substituir.** El
   `LLEGEIX-ME` declara que la fotometria absoluta és `NO`, amb el pedestal de
   halo/cel **degenerat amb una constant**. Exigir que l'earthshine dels dos
   trens coincideixi dins de 0,3 EV és comparar dues constants no
   identificables. El criteri nou és d'**estructura**, no de nivell: §G3.

I una restricció ja mesurada que s'ha de respectar: les capes Sony de 2 s i
1 s **i el Vixen sencer empitjoraven la validació fora de mostra**. El
producte bo és la pila Sony de **2×8 s** (DSC06987 + DSC06993).

### 0.2 El G0 no està fet: falta la meitat de les dades

Recompte real de `~/Desktop/Eclipse 2026/`:

| Carpeta | Fitxers | Estat a la v1.0 |
|---|---:|---|
| `Vixen/` | **249** | no inventariada |
| `Vixen Unfiltered/` | 128 | inventariada |
| `300mm/` | 200 | inventariada |
| `6D Eclipse/` | **3.063** | **no existeix per al pla** |
| `HDR/` | **8** | no inventariada |
| `HDR2/` | 2 | no inventariada |

El 6D no és corona —35 mm f/2,5, majoritàriament 1/4000— però **163 fotogrames
a 1/30 durant la totalitat** capten planetes i estrelles brillants. És una
tercera referència astromètrica i fotomètrica independent **i el registre de
com era el cel**, que és justament la component de llum difusa atmosfèrica que
no se sap separar. S'ha d'inventariar abans de tancar el G0 (vegeu G0-bis).

### 0.3 Quatre peces que la v1.0 no tenia

- **Estrelles i resolució astromètrica** (§G7): calibratge absolut sense
  mesurar el filtre solar, ala de la PSF per una segona via, i **orientació
  nord real** —el producte d'earthshine actual està en orientació de sensor—.
- **Dades externes del mateix dia** (§G7): LASCO C2/C3 (2–6 R☉), K-Cor de
  Mauna Loa (1,05–3 R☉) i la predicció MHD de Predictive Science. És l'única
  validació que no comparteix atmosfera, lloc ni operador amb tu.
- **Camp pla** (§Sessió 0): encara es pot fer, els trens no s'han desmuntat.
- **Guany i mapa d'incertesa** (§G2-bis i §G5): sense guany els pesos no són
  òptims i sense variància per píxel cap criteri és una porta.

### 0.4 No desbayeris

La recepta de la v1.0 mantenia `demosaic_algorithm=AHD`. Interpolar el mosaic
correlaciona píxels veïns i barreja canals, i **trenca tres criteris del mateix
pla**: el recompte de saturació contra el RAW, el llindar de 5σ i la màscara
per canal. Es treballa amb els **quatre plans R, G1, G2, B a mitja resolució**
(superpíxel 2×2), i **G1−G2 surt de franc com a estimador de soroll**.

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
| G0 | Procedència: quin fitxer surt de quina pulsació, amb quina exposició i quin instant | ⚠️ **A MITGES**: cobreix 322 fitxers de **3.650**. Falten `Vixen/` (249), `6D Eclipse/` (3.063), `HDR/` (8) i `HDR2/` (2) |
| G1 | Banc de darks a la temperatura de treball (40–41 °C) | **FET amb dos defectes** (vegeu §4) |
| G2 | Consistència de camp: escala de placa, contactes reals, deriva, salts de muntura | **FET** (`research/71` i `research/72`) |
| G3 | Model de halo / llum difusa | ⚠️ **FET I VALIDAT** a `Earthshine_FINAL/` (r=0,68/0,73 contra LROC). Queda **reajustar-lo** sobre dades no retallades |
| G4 | Doble registre corona / Lluna | pendent |
| G5 | Composició HDR lineal en float64 | pendent |
| G6 | Visualització controlada | pendent |
| **G7** | **Ancoratge extern: estrelles, cel i satèl·lits** | **porta nova de la v1.1** |

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

⚠️ **Correcció de la v1.1: no es fa servir `postprocess` ni cap demosaic.** El
que es llegeix és el mosaic cru i es parteix en els quatre plans de Bayer:

```python
raw = rawpy.imread(ruta)
m   = raw.raw_image_visible.astype(np.float64)   # mosaic cru, sense tocar
c   = raw.raw_colors_visible                     # 0=R 1=G1 2=B 3=G2

R  = m[0::2, 0::2]   # els índexs reals surten de raw_pattern; verifica'ls
G1 = m[0::2, 1::2]
G2 = m[1::2, 0::2]
B  = m[1::2, 1::2]
```

Sortida: quatre plans a **mitja resolució** (3480×2320 al R6, 3976×2652 a la
Sony), `float32`, en comptes crus **amb el pedestal conservat**, dins d'un sol
TIFF de quatre pàgines o d'un `.npz`. Cap `np.clip`, cap balanç de blancs, cap
matriu de color, cap gamma.

**Per què.** Interpolar el mosaic correlaciona píxels veïns i barreja canals.
Amb AHD, el recompte de píxels al sostre no pot quadrar amb les fotolocalitats
saturades del RAW (criteri 3 d'aquesta mateixa porta), la σ per píxel deixa de
ser la del sensor —i amb ella el llindar de 5σ del G5— i la màscara de
saturació per canal es contamina. **`G1 − G2` és soroll pur** i et dona la σ
per píxel sense cap mesura addicional.

Cost: la mitja resolució ja és 4,3 ″/px al R6 i 6,5 ″/px a la Sony, que és
**exactament la resolució efectiva real de cada tren** (§2.8 del dossier). No
es perd res que hi fos.

**Guany del sensor, aprofitant la mateixa passada.** Mitjana contra variància
d'un mateix pegat de corona als setze esglaons d'exposició del R6: el pendent
de la recta és **1/g**. Amb `g` els pesos del G5 passen de trapezoïdals a
òptims (inversa de la variància), i el mapa d'incertesa deixa de ser una
estimació. No calen flats per fer-ho.

I la resta de dark **sense `np.clip(0)`**: es fa en float32 i els valors negatius es conserven. Un fons de cel amb soroll ha de tenir la meitat de les mostres per sota de la mediana; si les talles, ja no és mesurable.

**Correcció de l'exposició:** llegir `ExposureTime` de l'EXIF amb `exiftool`, i **substituir manualment 10,0 → 10,3 s** als tres fotogrames de l'esglaó profund del R6 (`572A2982`, `572A2983`, `572A2984` segons el manifest; verifica els noms exactes abans). El programa és l'autoritat: 10,3 és literal del menú del cos.

**Criteri objectiu de pas de G2-bis** (tots quatre s'han de complir):

1. **Cap fitxer amb més del 0,5 % de píxels exactament al valor de negre** al canal verd, excepte els tres 1/6400 de contacte de la Sony i els 1/3200 del R6, on s'admet fins al 5 % perquè el cel hi és realment per sota d'un comptatge.
2. **Prova de linealitat:** mediana anular al canal verd a 3,0 R☉ i a 5,0 R☉ sobre les quatre exposicions consecutives del R6 dins de 2,7 s (`572A2986`–`572A2989`, 1/500 · 1/125 · 1/30 · 1/8). Les tres raons consecutives han de sortir **4,167 ± 0,15** a totes dues alçades. Avui a 5 R☉ la primera raó surt 9,0.
3. **Recompte de saturació:** el nombre de fotolocalitats a `white_level` al RAW i el nombre de píxels al sostre del TIFF de sortida han de coincidir dins d'un factor 1,3. Avui difereixen per 81.
4. `manifest_v2.csv` amb 124 i 194 files, cap `exposicio_s_exif` nul·la i cap valor de 10,000 al R6.

**Cost de càlcul:** 318 fotogrames × ~2,5 s de demosaic AHD + E/S = **13–15 minuts** al Mac, més la lectura d'EXIF (~40 s amb `exiftool -stay_open`). El disc: 124 × 6960×4640×3×4 B ≈ **48 GB** al Vixen i 194 × 7952×5304×3×4 B ≈ **98 GB** a la Sony. **Comprova l'espai lliure abans d'engegar** i, si va just, escriu els TIFF amb compressió `zstd` de tifffile (baixa a ~55 % sense pèrdua i costa un 15 % més de temps).

---

## 2. Les cinc portes que queden

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

**El model ja existeix. Aquesta porta el reajusta, no el descobreix.**

El mètode bo és el que ja hi ha a `Earthshine_FINAL/` i el descriu el seu
propi `LLEGEIX-ME`: **convolucionar la corona real mesurada amb dos nuclis
d'ales de PSF, més un pla de cel, i ajustar-ne només les amplituds**. No és
un ajust radial: és un model directe.

$$I_{\text{obs}} = I_{\text{vertader}} + A_1\,(I_{\text{corona}} \otimes k_1) + A_2\,(I_{\text{corona}} \otimes k_2) + P_{\text{cel}}$$

amb $k_i(\theta) \propto (\theta^2 + \theta_{0,i}^2)^{-\alpha_i/2}$. Els valors ajustats
sobre la pila Sony de 2×8 s, per canal:

| Canal | $k_1$ (escala px, índex) | $k_2$ | $A_1$ | $A_2$ | rms |
|---|---|---|---:|---:|---:|
| R | 12 · 1,5 | 320 · 2,5 | 0,01037 | 0,01011 | 918,9 |
| G | 6 · 1,5 | 320 · 1,5 | 0,01619 | 0,02677 | 326,4 |
| B | 6 · 1,5 | 320 · 1,5 | 0,01672 | 0,08581 | 293,1 |

⚠️ **El canal vermell té un rms tres vegades pitjor que els altres dos**, i
per això el `LLEGEIX-ME` marca el producte de color com a `EXPERIMENTAL` i diu
que **el color de gran escala no és fiable**. Aquesta és la pista més clara que
el reajust sobre dades no retallades val la pena: el vermell és **justament el
canal que el balanç de blancs retallava 1,32 EV per sota del pou** a la Sony
(§«Avís preliminar», punt 1). **INFERIT, i és la hipòtesi a provar primer:**
el rms del vermell podria ser un artefacte del retall i no del model.

**Per què es pot fer amb aquestes dades.** Perquè tens **la Lluna**: un
ocultador de mida i posició conegudes, amb vora dura, al mig del camp. Tot el
senyal de dins del disc que no sigui earthshine és llum difusa. I tens **dues
òptiques radicalment diferents** —un refractor apocromàtic de 90 mm f/5,5 i un
teleobjectiu de 300 mm f/2,8 amb moltes més superfícies aire-vidre— mirant el
mateix objecte.

#### Què s'ha de fer, per ordre

**Pas 1 — Reajustar sobre els plans de Bayer no retallats.** Mateixa
estructura de model, mateixos nuclis d'arrencada, dades del G2-bis. Deixar
lliures $A_1$, $A_2$, els índexs $\alpha_i$ i el pla de cel. Ajust amb
`scipy.optimize.least_squares`, pèrdua `soft_l1`, `f_scale` a la σ del fons.

**Pas 2 — Comprovar si el vermell millora.** Si el rms del canal R baixa fins
a l'ordre del verd i del blau, el color d'earthshine passa d'`EXPERIMENTAL` a
utilitzable i és un resultat propi. Si no baixa, el problema és del model i
s'ha de dir.

**Pas 3 — Estendre'l al Vixen.** El `LLEGEIX-ME` diu que el Vixen empitjorava
la validació fora de mostra **amb les dades retallades**. S'ha de tornar a
provar amb les noves, i acceptar el veredicte que surti.

**Pas 4 — Aplicar-lo al compost, no als fotogrames.** El model es mesura ara;
la correcció s'aplica després del G5, sobre el compost, que té 20–50 s
d'integració efectiva contra els 0,3 ms d'un fotograma de contacte.

**Pas 5 — Decidir restar o deconvolucionar (decisió D3).** Si els índexs
$\alpha_i$ surten amb incertesa inferior al 20 %, deconvolució amb **BID**
(Hofmeister 2024, §4.5 del dossier), que compta els fotons dispersats fora del
camp i és 1,8–7,1× més ràpid que Richardson-Lucy. Si no, resta additiva i
documentar que el contrast està subestimat.

**Els números mesurats que no s'han d'assumir:**

| Magnitud | R6 + VSD90SS | Sony + 300 GM |
|---|---:|---:|
| Escala de placa | **2,158 ″/px** | **3,234 ″/px** |
| Radi solar en px | 444,4 | 296,5 |
| Radi lunar en px (mag. 1,031) | 458,2 | 305,7 |
| Rang d'ajust | 1,05 – 6,0 R☉ | 1,05 – 4,0 R☉ |

#### Criteri objectiu de bo

⚠️ **La Fita 2 de la v1.0 queda anul·lada.** Exigia que l'earthshine dels dos
trens coincidís en nivell dins de 0,3 EV. El `LLEGEIX-ME` declara que el
pedestal de halo/cel és **degenerat amb una constant**: aquella comparació no
mesura res. Els criteris nous són d'estructura:

1. **Correlació amb LROC WAC**, fora de mostra, per tren per separat, amb la
   rotació i la libració ja resoltes (71,5°, +4/−1). Ha d'igualar o superar el
   que ja hi ha: **r ≥ 0,68** a escala completa i **≥ 0,73** a mitja escala.
   Si el reajust sobre dades netes no hi arriba, has empitjorat.
2. **El mateix mapa relatiu als dos trens.** El nivell absolut no és
   identificable, però el **patró** sí: la correlació entre el mapa
   d'earthshine del Vixen i el de la Sony, després de remostrejar-los a la
   mateixa escala, ha de superar **r = 0,6**. Són òptiques diferents mirant la
   mateixa Lluna.
3. **Residu pla dins del disc:** després de restar el model, el perfil dins del
   disc lunar ha de ser pla dins d'**±8 %** entre 0,2 i 0,9 radis lunars,
   **i sense estructura angular coherent** —aquesta segona part és la que
   detecta que l'asimetria de la corona s'ha colat dins d'`E`.
4. **Prova de no sobrerestar:** cap píxel de la imatge corregida per sota de
   **−3σ** del soroll de lectura, amb σ presa del mapa d'incertesa, no d'una
   estimació global.
5. **El vermell:** rms del canal R dins d'un factor **1,5** del de G i B, o
   una explicació del perquè no.

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

### G7 — Ancoratge extern: estrelles, cel i satèl·lits

Porta nova de la v1.1. És la que converteix un producte bonic en un producte
**ancorat**, i és barata comparada amb tot el que hi ha abans.

#### G7a — Estrelles i resolució astromètrica

**Què resol.** Quatre coses d'un cop, i totes quatre són forats declarats al
dossier: calibratge absolut **sense** haver de mesurar la densitat òptica del
filtre solar (§5.5); l'ala de la PSF per una segona via independent
(`elderflower`, §4.5); **l'orientació nord real** —ara mateix el producte
d'earthshine està en orientació de sensor, i sense nord no es pot comparar amb
res de fora—; i una verificació independent de l'escala de placa.

**Com.** Apilar les dues àncores bones de 8 s de la Sony (DSC06987, DSC06993)
i els tres fotogrames de 10,3 s del Vixen. Córrer un resolutor astromètric
sobre el resultat. Identificar les estrelles del catàleg que caiguin al camp i
fer-ne fotometria d'obertura. Amb dues estrelles de magnitud coneguda i la
magnitud aparent del Sol ($m_\odot = -26{,}75$) es tanca el calibratge, que és
exactament el que fa Bemporad (2020) amb α-Leo i ν-Leo.

**Criteri de bo.** La diferència de magnitud observada entre dues estrelles ha
de coincidir amb la del catàleg dins de **0,1 mag** —Bemporad hi arriba a
0,00— i l'escala de placa resolta ha de coincidir amb la mesurada
(2,158 i 3,234 ″/px) dins del **1 %**.

**Cost:** mitja hora de persona. És la millor relació valor/esforç de tot el
pla.

#### G7b — El 6D com a registre del cel

3.063 CR2 a 35 mm f/2,5, amb **163 fotogrames a 1/30** durant la totalitat.
No és corona, però és:

- una **tercera referència astromètrica i fotomètrica** independent (planetes i
  estrelles brillants);
- **el registre de com era el cel**, o sigui la component de llum difusa
  atmosfèrica que el G3 no sap separar de la instrumental. Amb el gradient de
  brillantor del cel al voltant de l'ombra mesurat a gran camp, el pla de cel
  del model de halo deixa de ser un paràmetre lliure i passa a ser una dada.

**Cost:** una tarda. **Prioritat:** després del G7a.

#### G7c — Dades externes del mateix dia

**INFERIT que existeixen; s'ha de comprovar.** El 12 d'agost de 2026 a
18:28–18:30 UTC:

| Font | Cobertura | Per a què |
|---|---|---|
| SOHO/LASCO C2 | 2–6 R☉ | **exactament la teva banda de solapament** |
| SOHO/LASCO C3 | 3,7–30 R☉ | corona externa i corona F |
| K-Cor, Mauna Loa | 1,05–3 R☉ | intercalibració; és el que fa servir Bemporad |
| Predictive Science | model MHD | topologia predita per a aquest eclipsi |

**Per què importa més que qualsevol prova interna.** La prova de coherència
entre trens és bona, però els dos trens comparteixen atmosfera, lloc, operador
i dia. **LASCO no comparteix res.** És l'única manera d'afirmar «aquesta
estructura existeix» sense dependre del propi muntatge.

**Criteri de bo.** El perfil radial del compost, normalitzat, ha de casar amb
el de LASCO C2 a la banda de solapament dins d'un **factor 2**. Sembla poc
exigent i no ho és: el mateix Bemporad discrepa d'un factor ~2 amb MLSO, i
aquest factor 2 és **l'estat de l'art** en aquest terreny.

**Cost:** una tarda de descàrrega i mitja de comparació.

---

## 3. Decisions que ha de prendre Pere

### D1 — Quin instant representa el compost

L'equació (3) fa que el compost representi el Sol **a l'instant de la imatge de referència**. Amb 103,7 s de totalitat i la Lluna movent-se 28,4 px al R6, tries quin.

| Opció | Cost |
|---|---|
| Mig de la totalitat | La corona d'un extrem hi entra amb pes reduït per la màscara lunar. **Recomanat.** |
| Just després de C2 | Guanyes les perles i el primer anell; perds la corona del costat de C3 |
| Just abans de C3 | Al revés |

⚠️ Correcció de la v1.1: la recomanació es manté, però el número de fotogrames
útils no és el que deia la v1.0. Dels 124 del R6, **~68 cauen dins [C2, C3]**;
dels 194 de la Sony, **33**. Tria la referència dins d'aquell subconjunt.

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

### D6 — Quina pregunta científica es respon (decisió nova, i és la primera)

**Aquesta decisió va abans que totes les altres i la v1.0 no la tenia.** El pla
acabava a `vis_final.png` i totes les fites decidien si la imatge era
*defensable*, no si **responia** res. El dossier té tota la maquinària de van
de Hulst i de Baumbach i el pla no la feia servir enlloc. Això és confondre
estètica amb ciència, i és el defecte més fàcil de cometre.

Les quatre candidates, amb el que costen i el que et donen:

| Pregunta | Què cal de més | Què en surt |
|---|---|---|
| **Perfil de brillantor radial per sector** amb la llei de tres termes $B(\rho)=P_1\rho^{-17}+P_2\rho^{-7}+P_3\rho^{-3}$ | G7a (estrelles) | densitat electrònica com a **límit superior** (sense polarímetre no separes K de F); és el que fa Bazin i Koutchmy |
| **Mapa d'earthshine contra LROC WAC** | ja el tens a r=0,68/0,73 | el més a prop d'estar acabat; el reajust del G3 el pot tancar |
| **Posició de plomalls i bagues contra PFSS** | G7c (Predictive Science) | topologia magnètica; és el que fa Boe (2024) |
| **Cap: imatge de divulgació** | res | legítim, però llavors les fites del G3 al G5 són sobredimensionades |

**Recomanació de l'equip: la segona, i la primera de propina.** L'earthshine ja
té resultat propi, validació externa i un defecte identificat i probablement
reparable (el canal vermell). És la que està més a prop de ser publicable i és
**l'objectiu científic número u declarat de la missió**. El perfil radial surt
gairebé de franc un cop tinguis el G7a.

**Tria-la abans del G5**, perquè decideix on cal precisió i on no.

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

### ⏰ Sessió 0 — El que caduca (aquesta setmana, dues hores)

Aquestes dues coses **es perden si es triga**, i la resta del pla no.

1. **Camp pla dels dos trens.** Els muntatges encara existeixen. Un flat de
   panell o de cel crepuscular a la mateixa obertura i focus. No serà perfecte
   —ni el focus ni la temperatura seran els del dia— però el vinyetatge d'un
   refractor i d'un teleobjectiu és estable si no es toca el diafragma. Sense
   flat, el vinyetatge queda dins del terme de halo i el model deixa de ser
   físic. **Documenta que és un flat posterior.**
2. **Quatre correus.** Cap costa res i tots poden estalviar setmanes:
   - **Miloslav Druckmüller** (`[adreça]`): demanar-li el
     **LDIC** —el compositor HDR, que és la peça que ens falta i que no es
     distribueix— o que passi un compost per Corona 4.1.
   - **Zdeněk Hrazdíra** (VUT Brno): el codi de correlació de fase **iterativa**
     de la seva tesi. És l'estat de l'art del mateix grup i és posterior al
     paper de 2009 que farem servir.
   - **Frédéric Auchère**: el WOW *edge-aware*, i si la variant bilateral està
     al paquet públic o només al paper.
   - **Benjamin Boe**: la separació K/F i si té dades de comparació d'aquest
     eclipsi.

### Sessió 1 — G0-bis: inventari sencer (dues hores)

3. Inventariar les **sis** carpetes, no les tres: `Vixen/` (249), `6D Eclipse/`
   (3.063), `HDR/` (8) i `HDR2/` (2) no estan al manifest. Del 6D, aïllar els
   **163 fotogrames a 1/30** de dins de la totalitat.
4. Tancar el **gate de procedència** de `Vixen/`: la cua 3152–3177 vista en una
   auditoria anterior i absent avui continua sense explicació.
5. **Fita 0:** un sol `inventari_global.csv` amb els 3.650 fitxers, el seu
   instant, exposició, cos i bloc de programa. Sense això el G0 no està fet.

### Sessió 2 — G2-bis: recalibratge fotomètric (mig dia)

6. Comprovar espai lliure. Amb superpíxel 2×2 i `float32` són **~24 GB al
   Vixen i ~50 GB a la Sony**, la meitat del que deia la v1.0.
7. Copiar els dos scripts de calibratge a versions `_v2` amb el camí de Bayer
   cru del §G2-bis: **cap demosaic**, cap balanç de blancs, cap `np.clip`.
8. Reconstruir el master dark de **0,5 s** del R6 amb rebuig de σ > 3,5.
   Investigar el pedestal **511,0** del master de 10 s (la resta és 512,0).
9. Llegir l'exposició de l'**EXIF** i corregir 10,0 → **10,3 s**.
10. Mesurar el **guany** amb la corba de transferència de fotons.
11. **Fita 1:** els quatre criteris del G2-bis en verd, i la prova de
    linealitat a 4,167 ± 0,15 a 3 i a 5 R☉. Si no, **para i diagnostica**.

### Sessió 3 — G7a: estrelles (mitja hora, i va abans del G3)

12. Apilar les dues àncores de 8 s i els tres de 10,3 s; resoldre el camp;
    fotometria d'obertura de les estrelles del catàleg.
13. **Fita 2 (substitueix la de la v1.0):** escala de placa resolta dins de
    l'1 % de la mesurada, diferència de magnitud entre dues estrelles dins de
    0,1 mag del catàleg, i **orientació nord** determinada.

> ⚠️ La Fita 2 antiga —«l'earthshine dels dos trens coincideix dins de
> 0,3 EV»— **queda anul·lada**: el pedestal de halo/cel és degenerat amb una
> constant i aquella comparació no mesura res.

### Sessió 4 — G3: reajustar el model de halo (un dia)

14. Reajustar els dos nuclis d'ales sobre els plans de Bayer no retallats,
    amb els paràmetres de `earthshine_FINAL_halo_params.json` d'arrencada.
15. Comprovar si el **rms del canal vermell** baixa a l'ordre del verd i del
    blau. Si baixa, el color d'earthshine deixa de ser `EXPERIMENTAL`.
16. Tornar a provar el **Vixen**, que amb dades retallades empitjorava.
17. **Fita 3:** r ≥ 0,68 / 0,73 contra LROC, correlació entre trens ≥ 0,6,
    residu pla dins de ±8 % **i sense estructura angular**. Aquí es decideix
    **D3** (restar o deconvolucionar amb BID).

### Sessió 5 — G4: registre (dos dies, la major part desatès)

18. Implementar `H_ρ` per graella polar, amb les tres correccions d'errates.
19. Escombrada de σ a 4096×4096 sobre deu fotogrames; fixar la finestra bona.
20. Registre sencer contra la mestra de cada cos. **Deixar-ho corrent de nit.**
21. Registre de la Lluna per centroide de vora + RANSAC sobre els curts.
22. **Fita 4:** residu de corona < 0,3 px, pendent de deriva compatible amb
    0,5905 ″/s dins del 10 %, rotació < 0,05°, i la prova de `r1` + 40 px.

### Sessió 6 — G5: composició (mig dia)

23. Pesos per píxel i per canal, ara **òptims** (inversa de la variància, amb
    el guany de la sessió 2) en lloc de trapezoïdals.
24. Màscares lunars del model del G4, eixamplades 6 px, amb pes **−1**.
25. Acumular numerador i denominador incrementalment, **propagant la variància**
    i lliurant `hdr_var_*.tif` al costat de `hdr_*.tif`.
26. **Fita 5:** els cinc criteris del G5. El decisiu continua sent el cinquè:
    els dos trens dins de 0,25 EV entre 1,5 i 3,5 R☉.

### Sessió 7 — G7c: ancoratge extern (una tarda)

27. Baixar LASCO C2/C3 de nivell 1 i K-Cor per a la finestra 17:00–20:00 UTC
    del 12-08-2026, i la predicció de Predictive Science.
28. **Fita 6:** el perfil radial casa amb LASCO C2 a la banda de solapament
    dins d'un factor 2.

### Sessió 8 — G6: visualització (mig dia)

29. `pip install sunkit-image` i el paquet de WOW a `~/.venvs/eines-ia-py312`.
30. Les quatre sortides sobre el mateix compost; proves de fase zero i de
    no-invenció; superposició per parelles en colors oposats.
31. **Fita 7:** `vis_final.png` amb `params_visualitzacio.json` al costat, i el
    `G5/hdr_*.tif` intacte com a producte científic.

### Sessió 9 — Dipòsit

32. Dipositar el compost lineal, el mapa d'incertesa, els paràmetres i els
    manifests a **Zenodo amb DOI**. És el que fa que la sèrie sigui citable i
    que la feina no es quedi al disc.

### Resum de temps

| Fase | Càlcul | Persona | Caduca? |
|---|---|---|---|
| **Sessió 0** (flat + correus) | — | **2 h** | **sí** |
| G0-bis inventari | — | 2 h | no |
| G2-bis recalibratge | 15 min | 3 h | no |
| **G7a estrelles** | minuts | **30 min** | no |
| G3 halo | 10 min (+3,5 h si BID) | 4 h | no |
| G4 registre | 1,5–8 h desatès | 5 h | no |
| G5 composició | 25 min | 3 h | no |
| G7c extern | 1 h | 3 h | no |
| G6 visualització | 10 min | 4 h | no |

---

## 7. Els forats que aquest pla no tanca

Per honestedat, i perquè es puguin atacar per ordre.

1. **No sabem quin filtre és el millor per a aquestes dades, i ningú no ho
   sap.** No hi ha cap comparació publicada entre ACHF, MGN, WOW i RHEF sobre
   un compost HDR real d'eclipsi en llum blanca. La sortida no és citar
   autoritat: és el criteri 3 del G6, passar-hi els quatre i mirar on
   coincideixen.
2. **No podem separar K de F.** Ni polarímetre ni bandes estretes. Qualsevol
   densitat electrònica serà un límit superior amb un $p(x)$ de model.
3. **L'ACHF viu no està publicat.** El que és reimplementable és el predecessor
   de Corona 1.0, no el de Corona 4.1.
4. **La discrepància de deriva del R6 no està resolta**: 0,71–0,75 ″/s per
   correlació de fase contra ~0,61 ″/s de `research/71`, un 18 %.
5. **El banc de darks té dos defectes sense diagnosticar**: un fotograma no
   fosc dins el master de 0,5 s i el pedestal 511,0 del de 10 s.
6. **Les unitats de $\varrho$ i $\omega$** del filtre tangencial no es defineixen
   al paper de 2009 i s'han de calibrar per assaig.
7. **El sostre real d'earthshine de la Sony són 16 s, no 24**, perquè la
   DSC06990 està moguda. El terra de la porta de durades era 24 s: no es
   compleix. No és fatal —era un requisit de captura, no de reducció— però el
   senyal/soroll baixa un 18 % i s'ha de declarar a qualsevol resultat.
