# 100 · Els flats girats 180° validen el flat de la Vixen, i quatre maneres de fer anells

**24 d'agost de 2026.** Dues coses independents que van caure el mateix dia.

**A.** Pere va fer **28 flats amb el cos girat**, que era el deute que
`.coordination/HANDOFF_2026-08-24_PILOT_EXECUTAT.md` marcava com a «feina de
Pere, no d'anàlisi». Amb ells, **el flat radial de la Vixen queda validat**, el
màster EVEN180 passa de candidat a òptica provada, el SMOOTH2D es confirma que
havia d'estar en quarantena, i l'**eix òptic queda declarat no mesurable** amb
una raó demostrada en lloc d'una sospita.

**B.** Pere va veure **anells concèntrics amb dents de serra** als productes de
la fase 3 i a les previsualitzacions. N'hi havia **quatre causes** a la mateixa
funció, més **tres defectes germans**, i el control que existia per caçar-ho
**no tenia dents**. El detall que la fase 3 declarava era **artefacte meu en un
54 %**.

⛔ I una lliçó de mètode que val per les dues meitats: **la mediana no és
additiva**. `mediana(A) − mediana(B) ≠ mediana(A − B)`, i amb un gradient
azimutal gros això fa que un «perfil radial» calculat amb medianes sigui **mal
definit a l'1-2 %**. Els dos camins de càlcul em van donar resultats de signe
contrari fins que ho vaig veure.

---

# A · Els flats girats

## A.1 · Què hi ha, i si serveix

28 CR3, `~/Desktop/Eclipse 2026/Vixen R6III/Flats invertits Vixen`, 24-08 de
les 16:22:44 a les 16:23:02, **1/640 a ISO 100**. Fets a **Roses**, apuntant al
**nord-est**, cel ennuvolat amb clarianes, apuntats a una clariana de cel blau,
transparència 4/10 declarada per Pere.

Cap d'aquestes condicions és ideal i totes són irrellevants per al que es vol
mesurar, perquè **el que decideix no és el cel que hi havia sinó que sigui un
cel DIFERENT del de la sessió d'abans**. Ho és, i molt.

| | valor |
|---|---|
| nivell per pla, sobre el pedestal | R 1.156 · G 3.014 / 3.016 · B 2.492 ADU (≈20 % del pou) |
| **variació del nivell entre els 28** | **0,30 – 0,54 %** ⇒ cap núvol va passar pel mig |
| dispersió temporal de la forma | 0,145 – 0,216 % rms per píxel |
| **error de la mitjana** | **0,027 – 0,041 %** |
| saturació | zero píxels per damunt de 13.995 |

L'error de la mitjana és **set vegades millor** que el terra del màster del
22-08 (`odd_even_difference` rms 0,236 %). Amb 28 fotogrames de 18 segons.

El conjunt de referència és `Flats R6III`: **125 fotogrames del 22-08** entre
les 20:26:06 i les 20:27:42, a 1/320 (18), 1/100 (83), 1/40 (2) i 1/25 (22).

## A.2 · L'inclinòmetre del cos ho tanca, i destapa una cosa que ningú havia mirat

La R6 escriu `RollAngle` i `PitchAngle` al MakerNote. Són de fiar: el pitch de
la totalitat, **9,4°**, és l'alçada del Sol aquell moment.

| sessió | Roll | Pitch |
|---|---:|---:|
| **totalitat 12-08** | **−6,9°** | 9,4° |
| flats 22-08 (el màster viu) | **+5,5°** | 42,4° |
| **flats invertits 24-08** | **+179,0°** | 43,1° |

- gir **A → B = 173,5°**, no 180. Pere ja ho havia dit: «el millor que he pogut».
- ⚠️ **gir eclipsi → A = 12,4°**: els flats del 22 **tampoc estaven a
  l'orientació de l'eclipsi**. Això no consta enlloc del projecte.
- gir eclipsi → B = 185,9°.

Que el màster viu sigui el **radial** —invariant a una rotació del cos— no era
només prudència: **era necessari**, i ningú no ho sabia.

## A.3 · L'estructura fina és fixa al SENSOR, i queda validada entre èpoques

Correlació del passa-alt logarítmic (σ=6 px sobre el pla CFA binat 4), a tot el
rectangle:

| pla | sostre A | sostre B | **A·B a la identitat** | A·B girat 180° |
|---|---:|---:|---:|---:|
| R | 0,9716 | 0,9576 | **+0,9478** | +0,0041 |
| G1 | 0,9846 | 0,9679 | **+0,9716** | +0,0084 |
| G2 | 0,9846 | 0,9679 | **+0,9725** | +0,0050 |
| B | 0,9797 | 0,9601 | **+0,9677** | +0,0114 |

Els «sostres» són la correlació entre meitats independents del **mateix**
conjunt: el màxim que es pot demanar. La correlació creuada hi arriba
**després de dos dies, un altre lloc, un altre cel i un gir de 173,5°**.

✅ `MASTER_FINE_SENSOR`, que el rebut del 22 deixava com
*«CANDIDATE; requires cross-epoch sensor-coordinate validation»*, **queda
validat**. I la meitat girada, +0,004 a +0,011, diu que **no hi ha estructura
fina fixa al telescopi**: ni pols al corrector ni al filtre.

⚠️ **Compte amb el que això NO prova.** Que la fina correlacioni a la identitat
és el que passaria **hagi girat el cos o no**, perquè és fixa al sensor. El gir
el prova l'inclinòmetre, no aquesta correlació.

## A.4 · La diferència dels dos flats no porta sensor

En log, amb A i B tots dos en coordenades de sensor:

```
log A = s(u) + t(u)   + k_A(u)
log B = s(u) + t(ρu)  + k_B(ρu)
```

`s` fix al sensor, `t` fix al telescopi, `k` el cel de cada sessió, `ρ` el gir
de 173,5°. **`D = log A − log B` anul·la `s` exactament**, i si `t` fos radial
al voltant del centre de gir, `t(ρu) = t(u)` i D seria **només cel**.

| pla | rms(D) | amplitud | residu d'un pla | d'una quàdrica | d'ordre 4 | terra |
|---|---:|---:|---:|---:|---:|---:|
| R | 2,581 % | 11,54 % | 0,259 % | 0,162 % | 0,157 % | 0,086 % |
| G1 | 2,472 % | 11,03 % | 0,280 % | 0,103 % | 0,096 % | 0,051 % |
| G2 | 2,474 % | 11,06 % | 0,283 % | 0,102 % | 0,096 % | 0,051 % |
| B | 2,286 % | 10,24 % | 0,229 % | 0,102 % | 0,096 % | 0,058 % |

**Una quàdrica explica tota la diferència de l'11 %**, i passar a ordre 4 no en
guanya res. L'excés sobre el terra és de **0,068 %**. O sigui: entre les dues
sessions **no hi ha estructura no-radial i no-suau del telescopi per damunt del
0,07 %**; el que hi ha és el cel de cadascuna.

## A.5 · L'eix òptic: no és mesurable, i ara se sap per què

Escanejant el centre i l'angle del gir per minimitzar el residu de D:

```
sense girar res (la D directa)          residu 0,0980 %   (terra 0,0707 %)
el millor amb gir                       residu 0,4892 %
```

**Girar B empitjora el residu cinc vegades.** El motiu és que el gir
desregistra l'estructura fixa al sensor, que és la que domina el passa-alt. És
la tercera via independent que diu el mateix: **no hi ha res fix al telescopi
sobre el qual registrar**, i per tant no hi ha palanca per trobar el centre de
gir.

L'altra via —quin centre minimitza la dispersió azimutal— tampoc serveix, i el
seu fracàs també és informatiu:

- l'estadístic no té un mínim interior: baixa **monòtonament** cap a la vora de
  l'escaneig;
- **A i B no coincideixen** en l'òptim (A a (+480,+480) px, B a (+480,−120));
- i el nivell del residu és molt diferent (1,94 % contra 3,13 % al centre
  geomètric), o sigui que **el que domina és el gradient de cel de cada
  sessió**, no l'òptica.

⛔ **L'eix òptic de la Vixen no és mesurable amb flats**, i el §19 de
`research/99` tenia raó per un motiu més fort del que deia: no és que la
vinyeta sigui massa plana, és que l'estadístic el domina el cel i **dos cels
independents no s'hi posen d'acord**.

**No cal.** El màster que s'aplica és radial al voltant del centre geomètric
del sensor, i el §A.6 demostra que dos cels independents el reprodueixen.

## A.6 · El flat radial queda VALIDAT

La cadena del màster viu (`build_master_flats.py`) és **lineal sencera en log**
—even180, gaussiana σ=25, mitjana per anell d'1 px, `gaussian_filter1d` σ=8—, o
sigui que aplicar-la a les dues sessions i restar és inequívoc.

| pla | amplitud A | amplitud B | \|A−B\| rms | \|A−B\| màx | terra | **dif/amplitud** |
|---|---:|---:|---:|---:|---:|---:|
| R | 9,444 % | 8,976 % | 0,209 % | 0,514 % | 0,004 % | **2,2 %** |
| G1 | 9,462 % | 8,777 % | 0,306 % | 0,751 % | 0,002 % | **3,2 %** |
| G2 | 9,642 % | 8,886 % | 0,324 % | 0,829 % | 0,003 % | **3,4 %** |
| B | 11,288 % | 10,695 % | 0,263 % | 0,665 % | 0,002 % | **2,3 %** |

✅ **Dos cels sense res a veure reprodueixen el flat radial al 2,2-3,4 % de la
seva pròpia amplitud**, contra un terra de precisió del 0,002-0,004 %. Deixa de
ser `CANDIDAT DECLARAT`.

La discrepància creix amb el radi —−0,07 % a 1.000 px, −0,33 % a 2.000, −0,72 %
a la cantonada extrema de 4.128 px— que és exactament la forma que tindria un
terme quadràtic residual del cel.

## A.7 · I els altres dos productes del màster

Mateix criteri, aplicat als altres dos camps òptics que el rebut del 22 deixava
sense provar:

| producte | dif/amplitud | veredicte | estat que tenia |
|---|---:|---|---|
| **EVEN180** | 2,3 – 3,0 % | **ÒPTICA** | *CANDIDATE; test against eclipse before promotion* |
| **SMOOTH2D** | 18,4 – 19,5 % | **MIXT**, 2,5 % rms és cel | *QUARANTINE_GRADIENT until eclipse null tests* |

✅ L'EVEN180 **queda promocionat**, i per una via millor que la que el rebut
proposava: dos cels independents discriminen més que l'eclipsi, on el cel és un
de sol.

✅ La quarantena del SMOOTH2D **era correcta**, i ara està quantificada:
gairebé una cinquena part de la seva amplitud és el gradient de cel de la
sessió de flats.

## A.8 · Val la pena passar de RADIAL a EVEN180?

`EVEN180 / RADIAL` sobre els màsters vius: rms 0,66-1,21 %, màxim 2,3-3,8 %.
Sobre el llenç de l'eclipsi, però, el que compta és on cau:

| r | mediana de la diferència | dispersió azimutal |
|---|---:|---:|
| 1,05 R☉ | −0,026 % | 0,047 % |
| 2,00 R☉ | +0,038 % | 0,133 % |
| 3,00 R☉ | +0,022 % | 0,259 % |
| 5,00 R☉ | +0,200 % | 0,901 % |
| 7,00 R☉ | +0,337 % | 0,806 % |

A la corona interior **no canvia res** (0,05 %). On sí que canvia és a
**5-7 R☉, amb 0,8-0,9 % de dispersió azimutal**, i allà hi ha una cosa que sí
que importa: **és on s'ajusta el model de cel** (`research/99` §13, quàdrica
ajustada a r > 2,5 R☉). Un error de flat azimutal del 0,9 % just allà
s'incorpora al model de cel i d'allà a tota la fotometria.

⏭️ **Recomanació**: adoptar EVEN180 **per a l'ajust del model de cel**. Per a
la corona interior és indiferent i no val la pena refer res.

---

# B · Els anells: quatre causes i tres germans

## B.1 · El defecte que Pere va marcar

A `fase3_achf_fisiques_flat-si.png`, «moltíssims artefactes radials concèntrics
amb dents de serra», qualificat d'**error greu**. I a
`fisiques_flat-si_normalitzat_radialment.png`, els mateixos anells però **de
color verd i blau**.

Tenia raó a les dues, i les dues surten del mateix lloc.

## B.2 · Les quatre causes, totes a `treu_perfil_radial`

**1. Restar el perfil per calaix** (`med[idx]`) en lloc d'interpolar.

La fase 3 corre sobre la reixa pròpia de la Vixen, **6.958 × 4.638**, amb `rr`
de 0 a 9,4895 R☉: 600 calaixos donen **Δr = 6,9684 px = 14,98 ″**, i hi caben
~530 anells dins del camp i ~87 dins de 2,5 R☉ —«moltíssims», tal com deia
Pere—. La frontera d'un calaix és una **circumferència rasteritzada sobre la
graella de píxels**, amb trams de x constant de fins a 31 px de llarg a
r = 550 px: aquí hi cau l'esglaó, i **això és la dent de serra**.

Esglaó del perfil entre calaixos veïns, i el serrell **realment mesurat al
`DETALL_ln` lliurat** (sha256 `75fc9493…`):

| r | esglaó del perfil | serrell al producte | serrell / rms local |
|---|---:|---:|---:|
| 1,15 R☉ | 8,91 % | — | — |
| **1,19 R☉** | **10,55 %** (màxim) | — | — |
| 1,25 R☉ | — | **5,43 %** | **1,00 – 1,13** |
| 1,48 R☉ | 7,02 % (a 1,50) | 3,97 % | 1,00 – 1,13 |
| 1,70 R☉ | — | 2,43 % | 1,00 – 1,13 |
| 1,93 R☉ | — | 1,36 % | 1,00 – 1,13 |
| 2,16 R☉ | 2,86 % (a 2,00) | 0,64 % | — |
| 2,38 R☉ | — | 0,32 % | — |
| 3,00 R☉ | 0,48 % | 0,10 % (a 2,84) | — |

⛔ **El quocient serrell / rms local val 1,00-1,13 de 500 a 2.000 px: a la
corona interior, el «detall» ERA el serrell.** La fracció de variància purament
radial del detall lliurat: **73,0 %** a 505-700 px, **62,8 %** a 700-1.000,
24,2 % a 1.000-1.500, 3,4 % a 1.500-2.500 i 0,5 % més enllà.

Arranjat, mesurat sobre el mateix retall amb la mateixa ACHF: el serrell a
505-700 px passa de 0,02284 a **0,00014** en ln (**÷163**), a 700-1.000 px de
0,00731 a 0,00002 (÷366), i la fracció de variància radial de 73,0 % a **4,0 %**
i de 62,8 % a **0,2 %**.

⛔ **I pujar el nombre de calaixos NO és el fix**: amb n = 1.200 el serrell
encara val 0,01068 —tan gran com tot el senyal real—, perquè l'error d'un
esglaonat baixa només ∝ Δr mentre que el de la interpolació baixa ∝ Δr². La
interpolació guanya **76×** sobre pujar n al doble. Una spline cúbica no aporta
res sobre `np.interp` (0,00013 contra 0,00014).

Sobre la reixa del **llenç comú** (8.378 × 7.686, calaixos de 9,475 px) i amb
una corona sintètica de Baumbach perfectament llisa —o sigui que tot el que se'n
mesura és artefacte—, les quatre causes juntes donen:

| banda | abans | després | guany |
|---|---:|---:|---:|
| 1,00 – 1,15 R☉ | **9,99 %** | 0,232 % | ×43 |
| 1,15 – 1,50 R☉ | 3,77 % | 0,0051 % | ×743 |
| 1,50 – 2,50 R☉ | 1,65 % | 0,0025 % | ×664 |
| 2,50 – 5,00 R☉ | 0,51 % | 0,0006 % | ×811 |

**2. Definir els calaixos sobre tot el mapa de radis** i no sobre el rang on hi
ha dada. Els de dins del disc lunar queden buits, s'omplen per extrapolació
plana i el suavitzat els barreja amb els primers bons: **1,62 % just al limbe**.

**3. Suavitzar amb `mode="nearest"`**, que repeteix una constant als extrems i
esbiaixa la vora exterior d'un perfil que baixa dret: **0,32 %**.

**4. Calaixos uniformes en r i un suavitzat que no preserva la curvatura.** És
la que queda quan les altres tres estan arreglades, i no és petita. Sobre una
corona de Baumbach amb 300 calaixos:

| variable | suavitzat | residu global | al limbe |
|---|---|---:|---:|
| lineal | gaussiana | 0,256 % | 0,832 % |
| lineal | Savitzky-Golay 2 | 0,119 % | 0,549 % |
| **log r** | gaussiana | 0,059 % | 0,216 % |
| **log r** | **Savitzky-Golay 2** | **0,043 %** | **0,194 %** |

⛔ **En log r i amb un suavitzat que preserva la curvatura: sis vegades millor
amb els mateixos calaixos.** El motiu és físic: la corona és una suma de lleis
de potències, o sigui **una recta en log-log**, i allà ni interpolar ni
suavitzar esbiaixen. De propina, els calaixos surten estrets on el perfil és
dret i amples on és pla, que és on convé cadascun.

I una cinquena cosa que no és una causa sinó un límit: **el que mana al limbe
és el NOMBRE de calaixos, no la finestra del suavitzat**. Doblant-los, el
residu del limbe passa de 0,00101 a 0,00035; canviant la finestra de 15 a 5 no
es mou (0,00101 → 0,00102). El terra és d'un píxel d'amplada de calaix: a
1,04 R☉ l'anell té 2.878 px de circumferència i hi ha mostra de sobres.

## B.3 · Els tres germans

**G1 · La previsualització normalitzada radialment, i els anells DE COLOR.**
`pilot.py` dividia per un perfil de **700 calaixos calculat per canal**: cada
canal tenia la seva pròpia escala d'esglaons, i per això els anells sortien
verds i blaus (G−B 1,95 %, G−R 2,25 %). ⛔ I aquesta vista **existeix
justament perquè s'hi vegin els anells de fusió**, o sigui que n'hi posava 700
de falsos. Arranjada, l'ondulació radial del resultat passa d'**1,62 % a
0,064 %**, i a sota hi havia els plomalls, els radis polars i les protuberàncies.

**G2 · La previsualització dels dos trens verdejava.** El pipeline no aplica
balanç de blancs ni matriu de color a propòsit, o sigui que el lineal surt verd.
Mesurat al PNG que verdejava: medianes R 17.080, G 25.132, B 21.641, o sigui el
verd **+47,1 % sobre el vermell i +16,1 % sobre el blau**, to 154° i saturació
32,0 % en HSV. La vista d'un tren sol ja ho neutralitzava i la dels dos no.

⛔ **No és cap error de CFA.** L'ordre RGGB és correcte —ho diuen `raw_pattern`
i `raw_colors_visible`, i les medianes de G1 i G2 al RAW coincideixen a 580,00
contra 580,00—, i sobretot: **una permutació R↔B deixa el verd al mateix lloc**,
o sigui que un CFA girat donaria un biaix vermell/blau i **no pot** produir un
domini verd.

⛔ **I s'ha de neutralitzar CADA TREN PER SEPARAT.** A 2-3 R☉ la Vixen té
G/R 1,642 i G/B 2,360 i la Sony 2,037 i 1,936: un sol factor comú deixaria una
**costura de color del 24 % en R/G i del 22 % en B/G** justament on es toquen
els dos trens. El primer arranjament que vaig fer aplicava un factor comú i era
incomplet; ho va destapar la verificació adversària.

**G3 · El control d'entrada llisa no tenia dents, per dos motius alhora.**

- El seu criteri era `rms(detall) / rms(entrada)` < 1 %. Però la dispersió de
  l'entrada està **dominada pel perfil radial que acabem de treure**, o sigui
  que divideix per un número enorme. Amb l'escala d'esglaons posada donava
  **0,33 % i PASS**, i el que hi havia valia més de la meitat del detall.
- I corria **sense disc lunar** i amb una `r^-2,5` que divergeix al centre: el
  **98 % del «detall» que mesurava vivia a r < 1,04 R☉**, on de veritat hi ha
  la Lluna i no hi ha dada. Amb la geometria bona el número baixa **14 vegades**.

Ara porta la Lluna i una corona de Baumbach, i el criteri és **quina fracció
del detall declarat podria ser artefacte, banda per banda** —perquè l'artefacte
viu al limbe i una mitjana sobre tot el camp l'hi dilueix amb els milions de
píxels de fora.

**G4 · L'artefacte subtil: la rampa de saturació deixa un colze.**

Pere també va marcar «un artefacte subtil»: una **línia corba que serpenteja amb
una osca en V**. No és cap anell i no és cap vora de sensor.

És el **graó de cobertura** on els **tres fotogrames de 10,079 s** toquen el
sostre i surten de la mescla: la cobertura verda hi cau 318→306 i 294→279 —−54
contribucions per cel·la 2×2, és a dir 3 fotogrames × 18— i el compost hi val
1.333,9 ADU/s contra `SOSTRE`/10,0794 s = 1.338,5.

⛔ **I no és un graó fotomètric sinó un COLZE.** La rampa `taper` és lineal i
arriba a zero amb **pendent no nul**: el pes d'aquells fotogrames desapareix amb
una discontinuïtat de derivada, i el passa-alt de l'ACHF la converteix en una
**vall fosca**.

| | |
|---|---|
| amplitud | 0,0007 – 0,0014 en ln = **0,07 – 0,14 % de contrast** |
| amplada | ~15 px, centrada 6 px cap endins del contorn |
| significació | −0,00070 ± 0,00013 ln = **5,4 σ** |
| a la variant `cel-model` | 0,139 % |
| al PNG publicat | 1,4-2,7 % del rang = 3,5-7 nivells de 255 |
| geometria | corba tancada de 1,588 a 2,377 R☉, mediana 1,992 |
| l'osca en V | a (2.773, 1.550) px, r = 2,369 R☉, PA 317,4°, gir de 52° |

Serpenteja perquè **és una isofota de la corona**, no un cercle; l'osca en V és
la punta del lòbul que el plomall de PA ≈ 320° empeny cap enfora. I n'hi ha una
**família de cinc corbes niades**, una per esglaó d'exposició que se satura, a
r mediana 2,38 · 1,41 · 1,28 · 1,17 · 1,11 R☉.

⛔ **La vora de la petjada d'un fotograma queda descartada amb dos números**: el
Sol només es mou **27,7 px** entre els 68 fotogrames, o sigui que les vores de
sensor només poden viure a ~30 px del perímetre del llenç; i dins de r < 5,16 R☉
el **100,00 %** dels píxels amb cobertura per sota del màxim pertanyen al niu de
saturació al voltant de la Lluna. A 2 R☉ no hi ha, ni hi pot haver, cap vora de
petjada. A més una vora de sensor seria recta amb cantonada de 90°.

**Arranjat amb una `smoothstep`** als dos trens, perquè el pes surti amb
derivada nul·la als dos extrems:

```python
u = np.clip((SOSTRE - brut) / (RAMPA_SOSTRE * SOSTRE), 0.0, 1.0)
taper = u * u * (3.0 - 2.0 * u)
```

No retalla res i no toca la norma del rectangle: només fa C¹ el que era C⁰.

⚠️ **I no és la cura de fons.** L'amplitud del colze és proporcional al
**desacord entre esglaons d'exposició** —la porta F0, que passa 5 dels 6
anells—; la smoothstep només impedeix que aquell desacord es concentri en una
línia i el reparteix pels ~200 px de la rampa. La causa arrel va per la
coherència entre esglaons (temps físics, fosc, linealitat), no per la rampa.
Pujar `RAMPA_SOSTRE` de 0,80 a 1,00 només baixaria el pendent final un 20 % i
no ho resol.

⚠️ **Aquest arranjament canvia el compost**, o sigui que la fase 2 s'ha de
tornar a compondre perquè tingui efecte. Al codi ja hi és; el producte encara no.

## B.4 · Què canvia als productes

**Fase 3 sobre `fisiques_flat-si`:**

| | 23-08 | 24-08 |
|---|---:|---:|
| detall rms (ln) | 0,004757 | **0,002183** |
| contrast | 0,477 % | **0,218 %** |
| porta G | PASS (1,0079) | PASS (1,0389) |
| rectangle | PASS | PASS |

⛔ **El 54 % del detall que la fase 3 declarava era artefacte meu.** Per escala:
−94 % a σ=2 px, −89 % a σ=4, −73 % a σ=8, −46 % a σ=16 i −21 % a σ=32, que és
la signatura d'un artefacte de mida fina.

El control nou, banda per banda:

| banda | artefacte | detall declarat | fracció |
|---|---:|---:|---:|
| **1 – 1,5 R☉** | 0,002130 | 0,011920 | ⚠️ **17,9 %** |
| 1,5 – 2,5 R☉ | 0,000036 | 0,004611 | 0,8 % |
| 2,5 – 5 R☉ | 0,000008 | 0,000603 | 1,4 % |
| 5 – 99 R☉ | 0,000014 | 0,000518 | 2,8 % |

✅ **PASS.** Fora d'1,5 R☉ el detall és real al 97-99 %. ⚠️ **Al limbe encara hi
ha un 17,9 % que podria ser artefacte**, i queda declarat: allà el perfil és tan
dret que ni amb calaixos d'un píxel no s'esborra del tot.

**Fase 3 sobre `fisiques_flat-si_cel-model`:** detall 0,0111 → 0,00725 (un 34 %
era artefacte). La porta G hi **continua fallant** —2,15 abans, 2,63 ara— i no
és cap regressió: aquell producte només té el **31,4 %** del rectangle amb
S/N ≥ 5 i ja fallava.

## B.5 · Les proves

`test_portes.py` passa de 34 a **39**, amb una classe nova `PerfilRadial` que
té l'entrada dolenta coneguda de cada causa: una corona de Baumbach
perfectament radial amb el disc lunar fora per pes, la versió per calaix
reproduïda al mateix règim que el llenç (ha de sortir ≥10× pitjor), el terra
d'un píxel per calaix, i que els calaixos siguin de veritat en log r.

⛔ La corona de prova és **Baumbach i no una potència pura**: el que el suavitzat
esbiaixa és la curvatura, i una potència pura n'amaga la meitat.

---

# B bis · Cinc germans més, i tres eren greus

L'escombrada de defectes de la mateixa família (workflow de 10 agents, tres
diagnosis confirmades i **cap refutada** en quatre intents amb lents diferents)
en va treure cinc més. Tots arranjats, amb la mesura de cada un.

## B bis.1 · ⛔ La trampa canònica del projecte, tornant a aparèixer

`pilot.py`, `fase_dos_trens_filtrats`:

```python
dist = distance_transform_edt(bo_v)
pv   = np.clip(dist / 200.0, 0.0, 1.0)
```

`distance_transform_edt` mesura la distància al zero **més proper**, i `bo_v`
val 0 **dins del disc lunar**: per a la corona interior el zero més proper és el
forat de la Lluna, o sigui que la rampa sortia **del limbe cap enfora** en lloc
de la vora de la petjada. I era una **circumferència de 200 px centrada al Sol**,
en una funció el docstring de la qual declara que no hi ha cap tall circular.

| anell | pes de la Vixen ABANS | DESPRÉS |
|---|---:|---:|
| 1,12 – 1,20 R☉ | **0,090** | **1,000** |
| 1,20 – 1,30 | 0,289 | 1,000 |
| 1,30 – 1,40 | 0,509 | 1,000 |
| 1,40 – 1,50 | 0,729 | 1,000 |
| 1,50 – 1,60 | 0,941 | 1,000 |

⛔ **A la corona interior el detall el posava la Sony al 91 %**, exactament el
contrari de la regla declarada tres línies més amunt («mana la Vixen on té dada
perquè mostreja 1,49× més fi»). El fix és **omplir els forats interiors** abans
de la transformada: llavors els únics zeros són els de fora de la petjada i la
rampa segueix la vora del sensor, que és un rectangle girat. I la rampa passa a
`smoothstep`, pel mateix motiu que el `taper`.

Efecte al producte: G del fusionat 1,066 → **1,055**, costura 0,51 % → 0,46 %.
El percentatge global amb prou feines es mou perquè la corona interior és el
0,6 % del llenç; **el que canvia és justament on hi ha la corona**.

## B bis.2 · La porta E2 mesurava amb una regla que canviava de llargada

`portes.py` feia `dlr = median(diff(log10(r)))` —**un sol** pas— sobre calaixos
uniformes en r, on `diff(log r)` va com 1/r i varia un factor 4,5 entre 1,15 i
5,2 R☉. I la calibració per injecció també era una sola mediana.

Amb un graó injectat del **+5,00 %**, el que la porta en deia:

| radi | abans | després |
|---|---:|---:|
| 1,20 R☉ | **+1,42 %** | +4,17 % |
| 1,50 | +2,41 % | +5,09 % |
| 2,00 | +3,12 % | +5,05 % |
| 3,00 | — | +5,03 % |
| 5,00 | **+8,33 %** | +5,02 % |

⛔ **Factor 5,9 de sensibilitat entre els dos extrems del domini, i les CINC
transicions reals del pilot** —1,175 · 1,266 · 1,418 · 1,570 · 2,097 R☉— queien
totes a la meitat cega. Corregit amb el pas **local** (`np.gradient(lr)`) i una
resposta d'injecció **interpolada** en lloc d'una mediana: la no-uniformitat
passa de ×5,9 a **×1,22**.

⚠️ **I això rectifica un número publicat.** El `pitjor_grao` de **−0,49 %** a
1,1753 R☉ que consta a `research/99` és, mesurat bé, **−1,46 % a 1,1551 R☉**:
tres vegades més gros. Continua passant el límit del 2 %, però just.

## B bis.3 · El camí de la Sony estava codificat a la variant `anell`

`dos_trens`, `filtres_sony` i `dos_trens_filtrats` llegien **sempre**
`sony_llenc_comu`, també quan la Vixen venia de `_cel-model`: es comparava una
Vixen amb el cel 2-D restat contra una Sony **només anivellada per anell**, en
silenci, i els subparsers ni tan sols tenien `--cel`.

Quocient `anell/model` del compost Sony al verd:

| anell | × |
|---|---:|
| 1,5 – 2,0 R☉ | 1,25 |
| 2,0 – 3,0 | **2,51** |
| 3,0 – 4,0 | 5,72 |
| 4,0 – 5,5 | **16,3** |
| 5,5 – 8,0 | 74,1 |

⛔ **Qualsevol quocient Sony/Vixen calculat així és soroll pur més enllà de
2 R☉, i és exactament el número del qual penja el ±14 % de `research/99` §15.**
Corregit amb `_dir_sony()`, que deriva la variant de l'etiqueta i **falla
tancat** si no hi és.

## B bis.4 · La màscara lunar era un clip lineal als dos trens

Trenta línies per sota del `taper` que ja s'havia passat a `smoothstep` pel
mateix motiu. Deixava **dos** colzes C⁰, a `d_ll` = 464 i 478 px, esbarriats per
la deriva Lluna–Sol de ±14 px fins a 1,02–1,117 R☉. Avui no mossega el producte
declarat però viu dins del llenç i de les previsualitzacions. Passada a
`smoothstep` als dos trens.

## B bis.5 · El warp de la Vixen no renormalitzava per l'alfa; el de la Sony sí

`out = warp(dades)` amb `borderValue=0` i després `out[alfa<0,5] = nan`, **sense
dividir per l'alfa**: el numerador es barreja amb els zeros de fora del pes i la
vora hereta el biaix cap avall. Mesurat: la mediana no es mou, però al percentil
1 el valor surt **−42,9 % a 1,02–1,04 R☉** i −15,3 % a 1,04–1,06. Corregit als
dos llocs, warpant `dades·valid` i dividint per l'alfa warpada amb el **mateix**
nucli.

## B bis.6 · I la porta que hauria d'haver caçat tot això no podia fallar

`porta_rectangle` només mesurava **`rmax` per sector**, o sigui la frontera
**exterior**: per construcció **no podia fallar** davant d'un tall circular
*interior* ni d'una rampa de pes circular. Hi donava `PASS` amb
`variacio_del_radi_maxim = 0,523`.

Ara mesura també la frontera **interior**, amb el criteri que la fa caure:
l'única frontera interior legítima és **l'ocultador**, que és la Lluna i és un
cercle de radi conegut. Un forat circular **més enllà** de l'ocultador l'ha
posat algú. I sense `r_ocultador_px` declarat la comprovació **no s'executa i el
rebut ho diu**, per no convertir un silenci en un aprovat.

⛔ **I la va caçar de seguida**: `_filtra` tenia un `rr > 1,12`, que és un cercle
imposat. La banda que llençava —**1,085 a 1,120 R☉**— té S/N mediana **298** i
p5 **255**, i el **100 %** dels seus píxels passen el llindar: és indistingible
de 1,12–1,20. Tret. El terra interior queda ara a `R_LLUNA_PX + 4 + 14` =
**477,9 px**, que és on la màscara lunar acaba de pujar, i la porta ho confirma:
«circular i a l'ocultador: és la Lluna».

## B bis.7 · Què en surt, mesurat

| | 23-08 | 24-08 final |
|---|---:|---:|
| detall de la Vixen | 0,477 % | **0,229 %** |
| fracció del rectangle | 95,48 % | **95,61 %** |
| porta G de la Vixen | 1,0079 | 1,0333 |
| **E2, pitjor graó** | −0,49 % (mal mesurat) | **−1,46 %** |
| G del fusionat | — | 1,0547 |
| costura Vixen/Sony | 0,51 % | **0,46 %** |
| pes de la Vixen a 1,12–1,20 R☉ | 0,090 | **1,000** |

Proves: **45**, totes verdes (eren 34 el 23-08).

# D · El COLOR separa la corona del cel, i això mou dos deutes

Va sortir d'una nota al marge de la verificació adversària: després d'aplicar a
cada tren el seu balanç de fàbrica, **el cel queda neutre en vermell/verd als
dos, però el blau no hi coincideix** —G/B residual 1,12 a la Sony contra 1,56 a
la Vixen, **1,39× de desacord mirant el mateix cel**—.

## D.1 · No és un error de calibratge: és que el cel és blau

Els quocients de canal dels dos trens al llenç comú:

| anell | Sony/Vixen R/G | Sony/Vixen B/G |
|---|---:|---:|
| 1,2 – 1,6 R☉ | ×0,798 | ×0,962 |
| 1,6 – 2,2 | ×0,807 | ×1,100 |
| 2,2 – 3,0 | ×0,806 | ×1,229 |
| 3,0 – 4,5 | ×0,807 | ×1,312 |
| 4,5 – 6,0 | ×0,802 | ×1,334 |
| 6,0 – 9,0 | ×0,799 | ×1,358 |

⛔ **El vermell discrepa un factor CONSTANT** (0,798-0,807 a tots els radis): és
un desplaçament de punt zero entre trens, res més. **El blau no**: va de 0,96 a
1,36 **amb el radi**.

La causa és física i es pot provar: **la corona és de color solar i el cel és
blau**. On mana la corona els dos trens coincideixen; on mana el cel, cadascun
ensenya el seu cel residual, i el seu color.

## D.2 · La descomposició, i per què és una prova i no un ajust

```
I_canal = a · k_corona[canal] + b · k_cel[canal]
```

**Tres equacions i dues incògnites**: li queda **un grau de llibertat per
fallar**. Els dos vectors de color no es trien: `k_corona` es mesura a
1,10–1,35 R☉ —on el cel encara no mana— i `k_cel` a 7–10 R☉ —on mana ell.

| tren | corona R/G · B/G | cel R/G · B/G |
|---|---|---|
| Vixen | 0,806 · 0,359 | 0,458 · 0,472 |
| Sony | 0,643 · 0,341 | 0,365 · 0,647 |

**Residu de l'ajust: 0,01 a 1,26 %** a tots els anells i als dos trens.

⛔ **I la prova que no és circular**: els dos trens tenen sensors, filtres i
calibratges diferents, i les seves fraccions de cel **coincideixen a 1,0 punt de
mediana i 1,7 de màxim** a tots els radis.

| r | cel/total Vixen | cel/total Sony |
|---|---:|---:|
| 1,30 R☉ | 0,001 | 0,010 |
| 1,75 | 0,171 | 0,161 |
| **2,40** | **0,512** | **0,505** |
| 3,30 | 0,763 | 0,752 |
| 5,00 | 0,928 | 0,911 |
| 8,00 | 1,000 | 0,988 |

**El cel iguala la corona a ~2,4 R☉**, que és el **2,41 R☉** que `research/99`
va treure per la via **temporal**. Dues vies sense res a veure, el mateix número.

## D.3 · La discrepància entre trens és un factor CONSTANT, no una forma

Amb el cel tret pel color, el quocient de la **corona sola**:

| r | corona Sony/Vixen |
|---|---:|
| 1,30 R☉ | ×1,1519 |
| 1,50 | ×1,1439 |
| 1,75 | ×1,1443 |
| 2,05 | ×1,1385 |
| 2,40 | ×1,1392 |
| 2,80 | ×1,1396 |
| 3,30 | ×1,1584 |

**Mediana ×1,1439, dispersió 0,60 %**, sobre un factor 2,5 en radi.

⚠️ **Això rectifica el §15 de `research/99`**, que deia que amb el cel restat
els dos trens «discrepen d'un 15 a un 18 % **sobre la corona sola** dins de
2 R☉». Mesurat pel color, **la discrepància és un factor constant del 14,4 % i
la FORMA coincideix al 0,6 %**.

⛔ **I això canvia el que falta.** No és que el fusionat tingui una forma
incerta: és que li falta **un sol número**, i és exactament el que un ancoratge
extern —LASCO C2, K-Cor o una estrella als dos trens— donaria. La via de la
foto, que treballa amb contrast relatiu, ja no en depèn de res.

Més enllà de 3,6 R☉ el quocient de la corona sola es dispara (×1,35 a 5 R☉,
×1,51 a 6,25, ×92 a 8) perquè allà la corona és del 4 % al 0 % del senyal i la
descomposició és degenerada. És esperat i queda dit.

## D.4 · La part constant del cel: acotada, no mesurada

El model de cel de `research/99` §13 porta el seu propi avís:

> «S·f(t) és el cel **VARIABLE**. La part constant queda dins C i aquesta via no
> la veu: el cel que se'n treu és una **fita inferior**.»

El color no té aquest problema: veu el cel **sencer**, constant i variable.

| via | cel al verd (B/B☉) |
|---|---:|
| temporal (`research/99` §13), només la part variable | 1,318·10⁻⁸ |
| **color, Vixen** | **1,209·10⁻⁸** |
| **color, Sony** | **1,295·10⁻⁸** |

Coincideixen al **8 %** i a l'**1,7 %**. Si la part constant fos gran, el color
—que la veu— hauria de donar **més** que el temporal; en dona una mica menys.

⚠️ **Fita, no mesura.** La sensibilitat del color és de ±4 % per ±5 % d'error
als vectors, els dos trens difereixen un 7 %, i **el compost pondera els
fotogrames per `t²/var`**, o sigui que el seu cel efectiu no és la mateixa
mitjana temporal que la normalització del model de `research/99`. Amb tot això,
el que es pot dir és: **la part constant del cel és compatible amb zero i queda
acotada a l'ordre del 10 % del cel** —≲1,3·10⁻⁹ B/B☉, que a 2 R☉ és **≲4 % de
la corona**—. El deute deia que calia «una altra latitud dins l'ombra, un model
d'ombra o una referència nocturna»; ara hi ha una fita sense res d'això.

⚠️ **I els vectors de color s'han de mesurar al MATEIX espai que les dades.** El
color del cel de `research/99` §13 és **instrumental** (ADU/s per pla CFA) i
aquí les dades són **calibrades** (B/B☉ per canal): posar-hi aquell dona un 26 %
menys de cel. No és una contradicció, són espais diferents.

## D.5 · ⛔ El blau del cel de `research/99` §13 és un 36 % massa alt, i això va trencar un producte

Comprovant els vectors de color contra els de `research/99` §13 va saltar una
cosa que no quadrava, **en el mateix espai i al mateix anell** (4,4–5,1 R☉, reixa
de la Vixen):

| | R/G | B/G |
|---|---:|---:|
| `research/99` §13 | 0,4856 | **0,6330** |
| mesurat al compost | 0,4897 | **0,4662** |

**El vermell coincideix al 0,8 % i el blau difereix un 36 %.** I el mesurat és el
que **convergeix**: B/G val 0,4481 a 3,0–3,6 R☉, 0,4662 a 4,4–5,1, 0,4706 a
5,5–6,5 i **0,4718 a 6,5–7,5** — una asímptota neta cap al color del cel.

⛔ **La causa**: els números de `research/99` §13 són exactament els quocients de
`cel_S_adu_s_per_pla` (230,25 / 474,4 = 0,4856 i 300,12 / 474,4 = 0,6330), o
sigui **les amplituds S de l'ajust temporal per pla**, no una mesura directa —
malgrat que el camp `color_del_cel` declara «mesurat on el cel és el 96 % del
senyal». El mateix document ja avisava que l'ajust temporal per pla **feia sortir
el blau negatiu** de 3,2 R☉ enfora; el problema no s'havia resolt, s'havia
canviat de lloc.

⛔ **I va trencar el producte `cel-model`.** Amb el blau sobre-restat un 36 %:

| r | R/G | B/G | píxels de blau negatius |
|---|---:|---:|---:|
| 1,1 – 1,3 R☉ | 0,811 | 0,355 | 0,00 % |
| 2,2 – 2,6 | 0,856 | 0,331 | 0,00 % |
| 3,0 – 3,6 | 0,938 | 0,279 | **19,86 %** |
| 4,4 – 5,1 | **−0,700** | **2,295** | **64,52 %** |

⚠️ **Això rectifica el diagnòstic de `research/99`**, que atribuïa el fracàs
d'aquell producte —31,4 % del rectangle amb S/N ≥ 5, porta G a 2,15— al fet que
restar el cel deixa un producte sorollós. **No: el que el trenca és un error del
36 % al color del blau.** Amb el color mesurat bé, aquell producte s'ha de poder
refer.

## D.6 · ⛔ Per píxel NO es pot, i la imatge ho va dir

El primer mapa que en vaig treure tenia una lluïssor difusa a tot el camp que no
podia ser corona. La causa és el **número de condició**: els dos colors només
estan separats per ΔB/G = 0,113, i la pseudo-inversa **amplifica el soroll ×2,8
a ×3,1**. A 3 R☉, un 1 % de soroll per canal es converteix en un **11,8 %** sobre
la corona; un 3 %, en un 35 %.

El que sí que es pot, i és físic: **el cel no té estructura fina** —`research/99`
§13 l'ajusta amb una quàdrica—, o sigui que es resol sobre una versió molt
suavitzada (convolució **incompleta i normalitzada pel pes**, que és la norma del
rectangle ben feta) i el mapa de cel resultant es resta a **resolució sencera**.
La corona conserva tot el detall i el cel no n'hi posa cap. I s'hi posen dues
fites físiques: el cel no pot ser negatiu ni superar el total.

El mapa de cel que en surt és **llis i sencer**: 1,151·10⁻⁸ a 1,30 R☉ pujant
suaument a 1,17·10⁻⁸ a 5,00, amb **zero píxels retallats**. I la quàdrica hi
ajusta al **2,8 %** (Vixen) i **1,5 %** (Sony), o sigui que **el cel realment és
una quàdrica** — que és el que `research/99` §13 havia assumit i que ara està
comprovat per una altra via.

## D.7 · Fins on val, i què hi queda de circular

⚠️ **Radi de validesa: 5,25 R☉.** El quocient entre la corona i la seva pròpia
dispersió per píxel puja fins a **7,3 cap a 3,5-4 R☉** i s'ensorra passats 5,25
—allà la corona és el 9 % del cel—. Més enllà, el mapa de corona és soroll
amplificat i **es veu com una lluïssor difusa que no és corona**.

⛔ **El radi de validesa es DECLARA, no s'aplica.** Els `.npy` conserven tot el
rectangle; només el pintat s'hi retalla. Retallar el producte a una
circumferència faria justament el halo que la norma prohibeix.

⚠️ **I queda una circularitat petita, declarada.** `k_corona` es mesura a
1,10–1,35 R☉ suposant que allà el cel no compta; la quàdrica hi diu que el cel
val el **2,8 %** del senyal. Corregit, el B/G de la corona passaria de 0,359 a
0,3557: **un 1 %**. Es podria iterar; no s'ha fet, i queda dit.

## D.8 · El que se n'ha corregit al codi

`fase_cel` mesura ara el color del cel **al compost i a l'asímptota** (6,5–7,5
R☉), no de la mediana per fotograma dels mapes per pla. Amb les dades del pilot
passa de `R/G 0,4856 · B/G 0,6330` a **`R/G 0,4638 · B/G 0,4718`**. Si el compost
encara no existeix, cau al camí antic **dient-ho al registre**.

Eina: `research/tools/pilot_vixen_claude/cel_per_color.py`.

## D.9 · I amb el cel del color restat, el producte de corona sola funciona

El model de cel temporal, fins i tot amb el color corregit, **sobre-resta**. Els
píxels negatius del compost amb el cel restat, per anell i canal:

| variant del cel | 2,2–2,6 R☉ | 3,0–3,6 | 4,4–5,1 |
|---|---|---|---|
| temporal, blau 0,633 (23-08) | 0/0/0 % | 0/0/**19,9** % | **40,8/56,1/64,5** % |
| temporal, blau 0,472 (24-08) | 0/0/0 % | 0/0/0 % | **21,6/55,5**/0 % |
| **del color** | 0/0/0 % | 0/0/0 % | **0/0/0,01 %** |

⛔ **El que sobre-resta no és el color sinó el NIVELL.** El cel temporal val
1,318·10⁻⁸ i el del color 1,209·10⁻⁸, un **9 % més**, i aquell 9 % és més gran
que la corona que hi queda —el 7 % del total a 5 R☉—. Un model que només veu la
part **variable** del cel n'és una fita inferior, **però pot sobre-restar
igualment**, perquè la seva forma espacial extrapolada cap enfora no té per què
coincidir amb la del cel de veritat.

Passant la fase 3 als tres productes:

| producte | rectangle amb S/N ≥ 5 | detall | porta G |
|---|---:|---:|---|
| sense restar el cel | **95,6 %** | 0,229 % | PASS 1,033 (domini 1,2–5 R☉) |
| cel temporal | 31,9 % | 0,750 % | **FAIL 2,609** a 4,88 R☉ |
| **cel del color** | **75,0 %** | 0,645 % | FAIL 1,715 a 4,93 R☉ |

L'amplitud del passa-alt del producte amb el cel del color cau de 0,00753 a
1,22 R☉ fins a un **mínim de 0,000532 a 2,89 R☉** i **torna a pujar** a 0,00131 a
4,88: és el soroll relatiu creixent quan la corona cau i el cel ja no hi és per
esmorteir-lo. Amb el domini retallat:

| domini de la porta G | veredicte |
|---|---|
| 1,2 – 5,0 R☉ | FAIL 1,715 |
| 1,2 – 4,0 | PASS 1,216 |
| **1,2 – 3,5** | **PASS 1,061** |
| 1,2 – 3,0 | PASS 1,040 |

⏭️ **El producte de corona sola és bo fins a 3,5 R☉**, i això és el que s'ha de
declarar. ⚠️ **I hi ha una tensió que val la pena dir**: el compost **sense**
restar el cel passa la porta G fins a 5 R☉ **precisament perquè allà el senyal
no és corona** —el cel és llis i esmorteeix el contrast relatiu—. Una porta que
passa perquè el senyal està diluït no diu que el producte sigui bo.

### Un contrast extern: contra Baumbach

La corona sola de la Vixen, contra el model **K+F de Baumbach (1937)**, que és
independent de tot el que hi ha aquí:

| r | nostre (B/B☉) | Baumbach | quocient |
|---|---:|---:|---:|
| 1,20 R☉ | 7,73·10⁻⁷ | 5,47·10⁻⁷ | ×1,413 |
| 1,60 | 9,28·10⁻⁸ | 7,04·10⁻⁸ | ×1,318 |
| 1,90 | 3,21·10⁻⁸ | 2,67·10⁻⁸ | ×1,204 |
| 2,35 | 1,15·10⁻⁸ | 9,89·10⁻⁹ | ×1,158 |
| 2,85 | 5,77·10⁻⁹ | 4,81·10⁻⁹ | ×1,199 |
| 3,40 | 3,35·10⁻⁹ | 2,77·10⁻⁹ | ×1,212 |

**Mediana ×1,212 amb un 8,1 % de dispersió** sobre un factor 3 en radi. Baumbach
és un model **mitjà** i un eclipsi a prop del màxim solar hi va per damunt, o
sigui que un 20 % de més és el que toca. ⚠️ Això **no és un ancoratge absolut**
—Baumbach no té la precisió del ±14 %— però sí que diu que ni el nivell ni la
forma no són absurds.

Producte: `output/pilot_vixen_claude_20260824/fisiques_flat-si_cel-color/`.
Eina: `cel_per_color.py --resta-a <directori de fase 2>`.

## D.10 · Els dos trens amb el cel tret, i què els separa de veritat

Aplicant el mateix a la Sony —amb **el seu** vector de color, que no és el de la
Vixen: R/G 0,374 · B/G 0,639 contra 0,464 · 0,472— el compost surt igual de net:
**zero píxels negatius** a tots els canals i anells, quàdrica al **1,5 %**.

⚠️ **I un número que enganya si es llegeix sol.** La fase 3 sobre la Sony amb el
cel tret diu «21,9 % del rectangle», contra el 80,8 % sense restar. No és una
pèrdua: el rectangle és el **llenç comú**, que a la cantonada arriba a ~15 R☉.
La cobertura per radi:

| r | sense restar | amb el cel tret |
|---|---:|---:|
| 2 – 5 R☉ | 100 % | **100 %** |
| 6 | 100 % | 75,3 % |
| 8 | 100 % | 3,5 % |
| 10 | 83,2 % | 0,7 % |

**El producte és sencer on hi ha corona** i desapareix on no n'hi ha, que és el
que ha de fer.

### La deriva del quocient mesura una cosa concreta

Amb els **dos** trens amb el cel tret, el quocient Sony/Vixen ja no és pla: va de
×1,157 a 1,13 R☉ fins a ×0,793 a 5,27. Ajustant `Sony = k·Vixen − Δ`:

| | |
|---|---|
| **k** | **1,1476** |
| **Δ** | **3,94·10⁻¹⁰ B/B☉ = 3,01 % del cel de la Sony** |

⛔ **El `k` coincideix amb el ×1,1439 de la descomposició de color per una via
completament diferent.** I el que fa derivar el quocient no és la corona: és que
**els dos trens difereixen un 3 % en la seva estimació del cel**, i aquell 3 %
va pesant més a mesura que la corona cau. El model quadra a millor del 2 % fins
a 4,35 R☉ i es trenca a 4,8–5,3, on la corona és uns pocs per cent del cel.

### El límit, i és el mateix per als tres productes

| producte | porta G fins a |
|---|---|
| Vixen sola, cel del color | **3,5 R☉** (1,061) |
| fusionat, els dos amb el cel del color | **3,5 R☉** (1,094) |
| Sony sola, cel del color | FAIL a 5 R☉ (1,822) |

L'amplitud del passa-alt del fusionat cau fins a un **mínim a 3,13 R☉** i torna a
pujar: el soroll relatiu creixent. ⏭️ **El producte de corona sola, sigui d'un
tren o dels dos, es declara bo fins a 3,5 R☉.**

⚠️ **La Sony sola no hi arriba** (G 1,822 a 5 R☉): té 14 fotogrames contra 68 i,
restat el 90 % del senyal, el que li queda no aguanta el filtre a la mateixa
distància. Al fusionat no fa mal perquè a dins de 3,5 R☉ hi mana la Vixen.

## D.11 · ⛔ Una porta radial no pot mesurar una frontera que és una isofota

Mirant el detall fusionat amb la mitjana per anell treta i estirat a ±1 σ, hi ha
un **arc fosc tènue a ~2 R☉** que **no és circular**: segueix una isofota. I el
perfil radial **no el veu**: el seu residu més fort és 0,236 % a 1,295 R☉ —la
transició d'exposició declarada a 1,266— i a 2 R☉ val 0,019 %.

El motiu és geomètric i es mesura:

| | |
|---|---|
| la isofota de saturació del fotograma de 10,08 s | de **1,583 a 2,370 R☉** |
| recorregut radial | 0,788 R☉ |
| amplada de la vall | ~15 px = 0,034 R☉ |
| **fracció de la frontera dins d'un calaix radial de l'amplada de la vall** | **4,3 %** |

⛔ **Un estadístic radial dilueix la frontera per un factor ~23.** La porta E2
mesura el perfil radial: **per construcció infravalora un graó que viu sobre una
isofota**, i per això diu que està bé mentre l'ull hi veu l'arc.

⚠️ **I la mida de la vall continua sense estar resolta.** La meva mesura al
contorn dona 0,0085 % (0,86 σ) al producte sense restar el cel i 0,0042 %
(0,31 σ) al del color —cap de les dues significativa—, i una mesura independent
amb una finestra diferent en va donar 0,070 % a 5,4 σ. **No he reconciliat les
dues**, i l'ull veu alguna cosa que cap de les dues declara. El que sí que és
cert per construcció és que el pes ara és C¹.

⏭️ **I la cura de fons no és la rampa**: l'amplitud del colze és proporcional al
**desacord entre esglaons d'exposició**, que és la porta F0 —la que passa 5 dels
6 anells—. La `smoothstep` només impedeix que aquell desacord es concentri en una
línia.

# C · Què queda, i què no s'ha de fer

## E · ⛔ Els arcs de Pere: dues famílies, dues causes, i la retractació d'un «60 σ»

Pere va marcar **en groc** uns arcs concèntrics amb la Lluna que «es deformen en
base als jets de la corona», i tot seguit **en lila** un segon arc arrapat a la
frontera més exterior. La resposta és que **són artefactes**, però no d'una causa
sinó de dues, i barrejar-les impedia veure'n cap.

### E.0 · ⛔ Primer, la retractació

Vaig declarar-li que una costura es veia a **60 σ**. **Era fals.** Amb sectors
azimutals honestos baixa a **3,2 σ**, per permutació a **1,5 σ**, i el número que
ho tanca: **quatre isofotes que NO són cap frontera van donar de 2,7 a 3,8 σ**,
els mateixos valors. El que es mesurava era **el mètode**.

Amb controls, de **sis** fronteres només **dues** superen el terra —i són
exactament les dues que Pere havia marcat mirant la imatge: **11→12 a 1,42 R☉ i
13→14 a 2,10 R☉**—. La norma que se'n deriva és a `trampes.md`: **tota mesura al
llarg d'un contorn ha de portar contorns de control del mateix tipus**, i el
llindar **se'l calibren els controls**.

### E.1 · Que són isofotes, i no cercles, està demostrat

- al llarg de cada frontera la brillantor és constant a **1,4–4,9 %**, i al llarg
  d'un **cercle** del mateix radi varia **11,6–38,1 %**: guany de ×6,6 a ×16;
- la brillantor a cada frontera val **0,60 × SOSTRE/t**, que és el que la
  `smoothstep` prediu **analíticament** per a un salt de factor 2;
- el radi de la frontera correlaciona **+0,79 a +0,99** amb la brillantor coronal
  local, i la de fora es mou **+136 px cap enfora per cada factor 2**. Això és,
  literalment, l'observació de Pere que «es deformen en base als jets»;
- **la prova creuada**: sobre la mateixa isofota —definida per la Vixen, o sigui
  cega per a l'altre tren— la Vixen hi té un clot de **−0,32 %** i la Sony
  **−0,00 % ± 0,012**, que hi hauria vist un 0,32 % a 25 σ. Isofotes de control:
  planes als dos;
- i apilant a **radi fix** el clot gairebé desapareix (−0,039 %) mentre que sobre
  la **isofota** hi és (−0,103 %): per això cap porta radial no el veia.

### E.2 · La causa arrel: dues escales entrellaçades i l'aire que canvia

Component **cada esglaó per separat** i comparant els veïns **píxel a píxel**:

| parell | desacord | | parell | desacord |
|---|---:|---|---|---:|
| 1/512 → 1/256 | **+0,519 %** | | 1/64 → 1/32 | **−1,095 %** |
| 1/256 → 1/128 | **−1,105 %** | | 1/32 → 1/16 | **+1,301 %** |
| 1/128 → 1/64 | **+1,275 %** | | 1/16 → 1/8 | **−1,062 %** |

⛔ **El signe alterna**: els esglaons senars i els parells són dues famílies. I la
causa surt de l'ordre de captura —la R6 fa **dues escales de 2 EV
entrellaçades**, senars a t = 6,6–11,6 s i parells a t = 12,7–16,5 s— més el fet
que **la transparència va caure un 8 % durant la totalitat**: el mateix 1/128 s
val **1,0598 a t = 8 s i 0,9779 a t = 89 s**.

⚠️ **Això és un deute de CAPTURA i queda anotat per al 2027** a `CLAUDE.md`
§1 quater, per petició expressa de Pere del 24-08-2026.

**La cura al postprocessat** és un ajust `P_i(r) = c_i·(C(r) + s_i)`: dos escalars
per fotograma i per pla contra 220 anells de dada. ⛔ Un escalar global **no pot
fabricar estructura** —només puja o baixa el fotograma sencer—, i aquesta és la
salvaguarda que el fa legítim, al contrari de `k(φ)` lliure entre trens, que té un
paràmetre per sector i **s'hi imposa l'acord** (research/97). Gauge
`mediana(ln c) = 0`: ⚠️ **l'escala absoluta no es toca** i el ±14 % de research/99
continua exactament on era.

### E.3 · La segona família: els anells del meu propi suavitzat

Els anells **realment circulars** —del 0,13 al 0,41 %, o sigui **més forts que les
costures**— surten del **Savitzky-Golay del perfil radial**. Refent la fase 3 amb
finestres de **9, 29 i 61** calaixos, a 1,182 R☉ el lòbul val **+0,179 %,
+0,074 % i −0,038 %** i a 1,303 R☉ **−0,250 %, −0,153 % i −0,040 %**: **es mouen
amb la finestra**. I cap finestra no els mata: el rms circular es queda entre 0,13
i 0,15 % a les tres.

La cura és una **segona passada NRGF després de l'ACHF**, i el número diu per què
hi pot ser exacta: després del passa-alt l'error típic de la mediana d'anell cau a
**0,005 %**, quaranta vegades per sota de l'artefacte. Amb calaixos de mig píxel
—calibrat ×64 amb un píxel, **×272 amb mig**, i a un quart no en guanya— la
component circular queda a zero **per construcció**, i ⛔ no toca res que no sigui
circular.

### E.4 · Les tres portes noves, i els tres errors que van destapar

| porta | què vigila | terra |
|---|---|---|
| **H1** | cap anell concèntric al detall | rms de la mediana azimutal ≤ 6 % del rms del detall |
| **H2** | cap vall que segueixi una frontera de fusió | **el pitjor control APARELLAT**, no un número triat |
| **H3** | desacord entre esglaons veïns | 0,4 %, contra el 2,5–4,3 % de F0 |

Totes tres amb entrada dolenta coneguda a `test_portes.py`, inclosa una prova que
demostra que **F0 deixa passar el cas real** perquè és cega per construcció.

⛔ **Construir-les va destapar tres errors meus, i tots tres els va destapar un
número que no quadrava, no una revisió de codi:**

1. **Els controls per NIVELL no existeixen.** Amb l'escala d'1 EV els nivells de
   frontera van de ×1,25 en ×1,25 i **no queda cap nivell lliure**: a 1,97 R☉ el
   «control» donava 0,1472 % i la frontera 0,1471 %. El control ha de ser
   **aparellat**: el mateix contorn, desplaçat 110 px. El terra passa de 6,36 σ
   a **2,81 σ**.
2. **`s` no és el cel, és la desviació**, i pot ser negatiu. Clavar-lo a zero
   feia que els tres fotogrames de 10,079 s —tots a mig eclipsi, on el cel és
   mínim— es mengessin la desviació dins de `c` i caiguessin a 0,947-0,994 en
   lloc d'1,00. Resultat: **una costura NOVA a 1,97 R☉ de 0,147 % a 11,8 σ** que
   el producte sense corregir no tenia. ⛔ Una correcció que arregla una costura i
   en crea una altra s'ha de mesurar **a totes dues bandes**.
3. **Un anell que no és un anell.** El criteri d'inclusió ha de ser la
   **cobertura del cercle**, no un recompte: una escletxa de 256 px amb un 3,9 %
   de cobertura a la vora de la dada de la Sony feia declarar un 14,2 % d'anells
   quan fora d'ella el residu era de ±0,008 %.

### E.5 · La confirmació creuada: els dos trens mesuren el mateix aire

L'ajust no sap res d'atmosfera; només sap que la corona no canvia. I el que en
surt és física:

- **la transparència cau de manera suau i monòtona** durant la totalitat, i tots
  els esglaons d'exposició cauen sobre la **mateixa corba**: **−8,07 % cada 100 s
  a la Vixen** i **−7,15 % a la Sony**, mesurats per separat amb dos telescopis,
  dos cossos i dues escales d'exposició diferents;
- **la desviació de cel ajustada fa una V amb el mínim a mig eclipsi**
  (+58 → −52 → +72 ADU/s), que és exactament la forma que el projecte ja
  coneixia —a prop de C2 i C3 el punt d'observació és a tocar de la vora de
  l'ombra— i que **a l'ajust no se li ha dit enlloc**.

## E.6 · ⛔ La correcció més cara: les costures són DENSES, i la mesura per contorn les subestima

Pere va dir «encara veig arcs concèntrics en el Vixen» quan els meus números ja
deien que la família circular era morta (27,5 % → 0,6 %) i que les costures
mesurables valien 0,07-0,12 %. **Tenia raó ell.**

Amb quinze exposicions d'1 EV, la corona interior té fins a **trenta fronteres de
fusió** —dues per esglaó— separades **×1,25 en nivell**, o sigui **20-60 px** a
1,2-1,6 R☉. La mesura per contorn treu una base local ajustada a ±60 px: **la
base està contaminada per les costures veïnes** i el control aparellat de ±110 px
**aterra sobre una altra costura**. Per això el terra de control sortia de 0,17 a
0,34 % a 1,25-1,51 R☉, més gros que el senyal.

La mesura bona quan les costures són denses és la de l'**espai de nivell**: la
mediana del detall per calaix de nivell. Aquella diu **88,6 %** del rms del
detall — un ordre de magnitud per damunt del que la mesura per contorn declarava.

⛔ **I la que ho va veure va ser una imatge, no un número**: realçat per anell,
amb les fronteres de fusió que el programa d'exposicions prediu dibuixades a
sobre. El patró de pana hi seguia els contorns exactament. És la confirmació
literal de la norma de la casa: **genera-li vistes de diagnòstic a cada etapa**.

**La cura** és la passada per nivell, alternada amb la radial fins a convergir:
les dues famílies són `f(radi)` i `h(nivell)`, els dos espais se solapen molt
—el nivell baixa amb el radi— i l'alternança de projeccions hi convergeix a poc
a poc. ⚠️ Tres voltes no basten (88,6 % → 22,6 %) i el bucle s'ha d'aturar per
convergència, no per comptador.

## E.7 · ⛔ El veredicte: el que queda a la pantalla és CORONA

Pere va continuar veient arcs quan els números ja deien que les dues famílies
eren mortes. La resposta la donen **tres proves independents**, totes 2-D i per
banda radial —⛔ **no per sector amb calaixos radials fins**, que és com les vaig
fer primer i em van donar el contrari perquè estaven dominades pel soroll de la
mediana per calaix—:

| prova | què separa | r a 1,1–1,75 R☉ |
|---|---|---:|
| **meitats A/B** (35 + 33 fotogrames, alternats DINS de cada esglaó) | senyal / soroll | **+0,96** |
| **Vixen × Sony** (a resolució comuna, σ = 1,10 px) | corona / sistemàtic d'un tren | **+0,93 a +0,95** |
| **sostre 0,85 × sostre 0,60** | corona / fronteres de fusió | **+0,97 a +0,99** |

O sigui: **no és soroll** —les dues meitats coincideixen al 96 %—, **no és de la
fusió** —moure totes les fronteres mig EV no el toca— i **no és un sistemàtic de
la Vixen** —surt igual a l'altre tren, amb una altra òptica, un altre sensor, un
altre flat i un altre joc d'exposicions—. És l'arcada de nanses de la base dels
plomalls, vista amb el realçat més agressiu possible.

⚠️ **Límit de la prova creuada**: els dos trens comparteixen llenç, warp, màscara
lunar i filtre de fase 3. Un artefacte introduït per **aquelles** etapes també
correlacionaria. El que la prova sí que exclou del tot és el que NO comparteixen:
òptica, sensor, fosc, flat, escala d'exposicions i fronteres de fusió.

### E.7 bis · L'estat final dels dos trens

| | Vixen + R6 III | Sony A7RIIIA |
|---|---|---|
| anells circulars | 27,5 % → **0,4 %** | 34,9 % → **0,5 %** |
| costures (per nivell) | 88,6 % → **4,6 %** | 92,6 % → **5,4 %** |
| desacord entre esglaons | ±3 % alternant → **±0,3 %** | −4,17 % → **+0,13 %** |
| voltes d'alternança | 20 | 20 |
| portes | H1 · G · rectangle **PASS** | H1 · G · rectangle **PASS** |
| detall que és estructura real | **96 %** a 1,1–1,75 R☉ | — |

## E.8 · ⛔ Els arcs que Pere va marcar en lila, i per què NO se n'han de treure

Pere va marcar tres arcs a la Vixen que a la Sony no hi són. Cauen a **r ≈ 1,37 i
1,95 R☉**, que són `SOSTRE/1 s` (1,33) i la frontera de 2 s / 10,08 s (1,98).
**Són costures de fusió, i són azimutalment LOCALS**: s'inflen on la corona és
brillant i desapareixen on és fosca.

**Què s'ha provat i què ha dit cada prova:**

| candidat | el seu propi número | el JUTGE EXTERN |
|---|---|---|
| ordre de la rampa 3 → 5 → 7 | costura exterior −26 % | sense efecte |
| pes sobre senyal suavitzat (σ=3) | idèntic | sense efecte |
| rampa de fusió 0,80 → 0,98 | idèntic | **FAIL** (Δ −0,0009) |
| calaixos de nivell adaptatius | 12,7 % → 2,9 % | empat (Δ −0,0011) |
| **resta per nivell i SECTOR** | **costura d'1,33 R☉ ×8 millor** | ⛔ **FAIL** (0,930 → **0,849**) |
| **les dues passades globals** | 88,6 % → 4,6 % | ✅ **PASS** (0,894 → **0,952**) |

⛔ **La conclusió és que aquests arcs NO s'han de treure amb el que sé avui.**
L'única correcció que els esborra —la resta per sector— **treu corona**, i això
no és una opinió: fa caure l'acord amb l'altre tren de 0,930 a 0,849 a
1,10-1,30 R☉. Un artefacte del 0,05 % no val el que costaria.

**On sí que es poden atacar**: aigües amunt, a la coherència de l'escala
d'exposicions, que és el que la geometria de captura limita. És exactament el
deute del 2027 de `CLAUDE.md` §1 quater — **si els esglaons veïns fossin veïns en
el temps, aquestes costures no existirien**.

⚠️ I una acotació honesta de fins on arriba la mesura: **a l'estadístic
azimutalment promediat, l'única frontera mai detectable va ser la d'1,98 R☉**
(0,0272 % contra un terra de 0,0150 %), i ara està per sota del terra. Les altres,
inclosa la d'1,37 R☉ que Pere veu, **són per sota del terra fins i tot sense
corregir**: només es veuen perquè són locals en azimut i l'ull integra al llarg
de l'arc molt millor que una mediana global.

## E.9 · Set candidats, cap millora: la taula completa (25-08-2026)

Pregunta de Pere: **com s'arregla el Vixen sense menjar-se corona?** Resposta
mesurada, amb el jutge creuat com a tribunal i el detector de costures com a
segona lectura:

| # | candidat | el seu propi número | jutge (Δr) | detector |
|---|---|---|---:|---|
| 1 | rampa d'ordre 3 → 5 → 7 | costura exterior −26 % | ~0 | — |
| 2 | pes sobre senyal suavitzat σ=3 | idèntic | ~0 | — |
| 3 | rampa de fusió 0,80 → 0,98 | idèntic | **−0,0009** | — |
| 4 | calaixos de nivell adaptatius | 12,7 % → 2,9 % | **−0,0011** | — |
| 5 | resta per nivell **i sector** | costura d'1,33 R☉ **×8 millor** | ⛔ **−0,081** | — |
| 6 | només la **família senar** d'esglaons | meitat de fronteres | ⛔ **−0,0032** | — |
| 7a | pesos, ajust **després** de les passades | δ físics, PASS | **+0,0001** | ⛔ **re-injecta** 1,98 R☉ (0,0222 %) |
| 7b | pesos, ajust **abans** (ordre correcte) | δ físics | **−0,0008** | 1,98 R☉ **neta** (0,0001 %) |

**Conclusió, i ⛔ RECTIFICADA per un contrast de Codex del 25-08-2026:** la
formulació correcta és **«encara no s'ha demostrat cap correcció segura amb
aquesta dada»**, no «és impossible». La diferència no és retòrica:

- l'única correcció que esborra els arcs de debò (5) fa caure l'acord entre
  trens de 0,930 a 0,849, i **això sí que és evidència forta** contra ella;
- les que no fan mal (7a, 7b) no aporten res;
- ⛔ **però el rebuig de (6) NO era vàlid.** El jutge **confon pèrdua de
  senyal/soroll amb pèrdua de corona**: mesurat, les **meitats A/B** —que no
  treuen ni un gram de corona, només la meitat dels fotogrames— cauen
  **−0,0169 i −0,0236**, de cinc a set vegades més que el −0,0032 de la família
  senar. El seu penal és **compatible amb pura pèrdua de S/N** i el candidat 6
  **queda sense atribuir**.

⚠️ I una segona feblesa que el contrast destapa: el veredicte **depèn de
l'agregació**. Amb sectors de 5° en lloc de la correlació global, el candidat
adaptatiu passa de −0,00109 a **+0,000066** i `pes3` de +0,000065 a
**−0,000123** — o sigui que aquells dos veredictes **són dins del soroll** i H4
els hauria de donar amb interval d'incertesa (bootstrap per blocs angulars),
no com a números secs.

⏭️ **La via bona és aigües amunt**, i és exactament `CLAUDE.md` §1 quater.

### E.9 bis · Dues lliçons de mètode d'aquesta ronda

1. ⛔ **El jutge creuat és necessari però NO suficient.** Diu si una correcció
   fa mal a la corona; **no diu si fa la feina que havia de fer**. El candidat
   7a el va passar (Δ +0,0001) i el detector el va enxampar re-injectant una
   costura. **Calen els dos.**
2. ⛔ **Un ajust mal condicionat dona bona imatge amb paràmetres impossibles.**
   Els regressors `f_k` sumen 1 a cada píxel: sense prior, δ = +954 %, −3182 %.
   I amb prior mal escalat —λ amb el soroll **per píxel**, ignorant la
   correlació espacial— encara δ = +32 %. λ ha d'anar amb el nombre **efectiu**
   de mostres, `N/(2πσ²)`. El senyal d'alarma **no és el residu, són els
   paràmetres**.

## C.1 · Deutes que aquest document tanca

| deute | estat |
|---|---|
| flat radial de la Vixen | ✅ **validat** al 2,2-3,4 % de la seva amplitud |
| `MASTER_FINE_SENSOR` cross-epoch | ✅ **validat**, correlació al sostre |
| `MASTER_OPTICAL_EVEN180` | ✅ **promocionat a òptica** |
| `MASTER_OPTICAL_SMOOTH2D` | ✅ quarantena **confirmada i quantificada** |
| eix òptic de la Vixen | ⛔ **declarat no mesurable**, amb la raó demostrada |
| anells de la fase 3 | ✅ arranjats, amb proves i amb el que queda declarat |

## C.2 · El que continua obert

- **part constant del cel**: cal una altra latitud dins l'ombra, un model
  d'ombra o una referència nocturna. Sense canvis.
- **escala absoluta al ±14 %**: cal LASCO C2, K-Cor o una estrella als dos
  trens, i el R☉ del dia posat abans. Sense canvis.
- **earthshine**: la recepta continua al §20 de `research/99`.
- **el 17,9 % del limbe**: per baixar-lo caldrien calaixos sub-píxel, i llavors
  la mediana per anell la farien massa pocs píxels. És un límit, no un deute.

## C.3 · ⛔ El que NO s'ha de fer

1. ⛔ **No prendre l'orientació dels flats del 22 com la de l'eclipsi.** Hi
   estan **12,4° girats**. Qualsevol producte de flat que no sigui radial o
   even180 sobre el centre s'hi ha de girar.
2. ⛔ **No fer servir `MASTER_OPTICAL_SMOOTH2D`.** Una cinquena part de la seva
   amplitud és el cel del 22 d'agost al vespre.
3. ⛔ **No buscar l'eix òptic amb més flats.** No hi ha estructura fixa al
   telescopi sobre la qual registrar, i l'estadístic azimutal el domina el cel.
4. ⛔ **No restar mai un perfil radial per calaix**, i no calcular-lo mai en r
   uniforme sobre una corona. En log r, interpolat, i amb un suavitzat que
   preservi la curvatura.
5. ⛔ **No creure's un control que es normalitza per la dispersió de la seva
   pròpia entrada** quan aquella dispersió està dominada pel que s'acaba de
   restar.

## C.4 · On són les coses

```
research/tools/pilot_vixen_claude/filtres.py       treu_perfil_radial reescrita
research/tools/pilot_vixen_claude/pilot.py         previsualitzacions i control per banda
research/tools/pilot_vixen_claude/refes_previs.py  refà previs d'un compost ja fet
research/tools/pilot_vixen_claude/test_portes.py   39 proves
output/pilot_vixen_claude_20260824/                fase 3 refeta (enllaços a la resta)
~/Desktop/Eclipse 2026/IA/output/pilot_vixen_claude_20260824/   previsualitzacions noves
```

Els productes del 23-08 **no s'han tocat**: la tirada nova viu a un arrel a part
amb enllaços simbòlics a tot el que no es refà. Els arrels són configurables per
entorn (`PILOT_SORTIDA`, `PILOT_PREVIS`).
