# 99 · Pilot Vixen: les portes reformulades i el compost LDIC executat

**23 d'agost de 2026, vespre.** Claude ha reformulat les portes F0 i F1 del
traspàs `.coordination/HANDOFF_2026-08-23_PILOT_VIXEN.md` i ha executat el
pilot sencer —fases 0, 1 i 2— sobre els 68 fotogrames de totalitat de la
Vixen.

**Veredicte honest**: passen **F1, F, E, E2, G i la norma del rectangle**. **F0
passa 5 dels seus 6 anells**; i ⚠️ **el §9 rectifica una decisió de la §1**: el
centre absolut bo és el de l'efemèride i no el del limbe mesurat, i qui ho
demostra és el segon tren. el que falla és el de 3,2–4,2 R☉, per un motiu
identificat —l'anivellament de cel amb un sol anell—, i per això la fotometria
del compost es declara **fins a 3,2 R☉**. Producte:

```
output/pilot_vixen_claude_20260823/fisiques_flat-si/
  HDR_adu_s.npy                  6958 × 4638 × 3, compost lineal
  N_verd.npy · D_verd.npy        numerador i denominador per separat
  VAR_adu_s2.npy                 variància per píxel (1/Σw)
  COBERTURA.npy                  fotogrames que hi aporten (mediana 296)
  ESGLAO_DOMINANT.npy            quin esglaó d'exposició mana a cada píxel
  LLENC_COMU_BBsol_float32.tif   7686 × 8378, nord amunt, Sol al centre, B/B☉
```

Codi: `research/tools/pilot_vixen_claude/`. Proves: **34/34 PASS**.

## 0 bis · ⛔ RECTIFICACIÓ · el lloc d'observació és el MIRADOR FINAL 2

Aquest document deia dues vegades «el cel de **Medina**». **És fals i el corregeix
Pere.** L'eclipsi es va observar des del

    MIRADOR FINAL 2 · 42,299407 N · 5,02503 O · 798 m

que és el lloc que fan servir **totes** les eines del projecte: `hdr_corona_vixen.py`,
tota l'astrometria (`comu.py`, `cat.py`, `zp.py`, `final_solve.py`, `deflexio.py`…),
`mesura_deriva_v2.py` i la predicció que `research/71` confirma amb els contactes
reals (totalitat de 103,7 s, clavada).

**Medina de Rioseco (41,8831 N, 5,0439 O) era el candidat B de `research/11`**, que
és un document de **prospectiva PRE-eclipsi** amb tres llocs possibles —Ferrol,
Medina i Deltebre— dels quals se'n va triar un altre. Els dos punts estan a
**46,4 km** l'un de l'altre, i el mateix `research/11` avisa que «al voltant de
Medina, moure's desenes de quilòmetres pot canviar els contactes desenes de
segons».

⚠️ **Cap número d'aquest document canvia.** Tot el que hi ha mesurat surt de les
imatges, no d'un model del lloc; l'única cosa que el lloc hauria pogut tocar és
l'extinció, i entre els dos punts la massa d'aire a mig eclipsi va de 6,16 a
6,02, o sigui **0,056 mag = 0,05 EV**. El que canvia és el **nom**, i el nom
importa perquè un document que anomena malament el lloc d'observació no es pot
citar.

⛔ **La lliçó**: `research/11`, `research/00` i `research/66` diuen «Medina»
legítimament —són tots pre-eclipsi i parlen del candidat—, i jo els vaig llegir
com si diguessin on s'havia observat. És exactament la trampa que `CLAUDE.md`
avisa: **els documents antics són context, no estat**.

## 0 ter · Auditoria de les constants, arran de la rectificació del lloc

L'error del §0 bis és d'una classe —un valor de planificació llegit com si fos
mesurat—, i la resposta correcta no és corregir-lo i prou sinó **mirar si n'hi ha
més**. Totes les constants del pilot, contra la seva font:

| constant | valor | font | veredicte |
|---|---|---|---|
| escala | 2,1494814 ″/px | `final_solution.r6_radial.scale` | ✅ verificat |
| `pa_north` | 57,194989° | idem | ✅ |
| C2 | 12-08 20:28:45 local | predicció del **FINAL 2** | ✅ (vegeu sota) |
| R☉ del dia | 947,068 ″ | `suns.json` | ✅ **exacte** (vegeu sota) |
| R Lluna | 460,0 px | mesurat, `research/75` §5.3 | ⚠️ (vegeu sota) |
| guany R6 / RN | 5,08 e⁻/ADU · 2,72 i 1,05 ADU | `research/75` §3 | ✅ |
| guany Sony / RN | 3,41 e⁻/ADU · 1,22 ADU | idem | ✅ |
| factors a B/B☉ | 2,772 i 1,134 ·10⁻¹¹ | `research/75` §5.2 | ✅ |
| pedestal | 511,5 (R6) · 512 (Sony) | rebuts dels màsters dark | ✅ |

### C2: és del FINAL 2, i el desfasament no importa

`C2_LOCAL = 20:28:45` és la **predicció del FINAL 2**, no la de cap candidat
—`research/11` donava 20:30:12 per a Medina i 20:28:00 per a Ferrol—. I
`research/71` la valida amb els contactes llegits de les imatges: **C2 real a
−1,0 ± 0,7 s** i totalitat real de **103,7 s** contra 103,8 predits.

⚠️ O sigui que tots els meus `t_rel_c2` van **1,0 s endavant** del C2 de veritat.
**No afecta res**: la forma temporal del cel, el model de deriva i el
desplaçament Sol−Lluna són tots **diferencials en t**, i un desplaçament comú
l'absorbeix l'ordenada a l'origen de cada ajust.

### R☉: exacte, però 1,26 % més petit que el dels documents antics

Comprovat contra DE421 al FINAL 2 a mig de la totalitat: el radi solar aparent
és **947,068 ″**, clavat al que el pilot fa servir.

⚠️ **Però el pipeline antic fa servir 959,0 ″** —el valor MITJÀ—, i
`research/96` ja ho havia detectat. Amb 947,068 el radi solar val **440,60 px** i
amb 959,0, **446,15**: un **1,26 %**. O sigui que **els radis en R☉ d'aquest
document són un 1,26 % més grans que els de `research/76` a `research/96` per a
la mateixa posició física**. El «el cel iguala la corona a **2,41 R☉**» del §11
es llegiria **2,38** amb la convenció antiga. No canvia cap conclusió, però sense
dir-ho les xifres no es poden comparar entre documents.

### R Lluna: l'efemèride diu 455,50 px i el projecte en fa servir 460,0

Al mateix instant, DE421 dona un radi lunar aparent de **979,09 ″ = 455,50 px**,
i magnitud **1,0338**. El projecte fa servir **460,0 px**, mesurat
(`research/75` §5.3): un **+1,0 %**. I `research/71` mesura radis que **decreixen
amb l'exposició** —453,8 px a curta i 446,7 a 10,3 s— perquè «el glow de l'anell
saturat menja la vora».

⛔ **És exactament la lliçó del §9 una altra vegada**: el limbe mesurat està
contaminat per la corona que hi vessa per damunt, i **l'efemèride és millor**.
Aquí la conseqüència és petita i va del costat segur: la màscara lunar del pilot
tapa fins a `460 + 4 = 464 px` i puja en 14 px, o sigui **8,5 px més enllà del
limbe real**. Es perd la corona de 1,000 a 1,019 R☉ sencera i fins a 1,049
parcialment, i a canvi **l'earthshine no entra mai** a la corona, que és el que
el traspàs exigeix. Es deixa com està i es declara.

### Massa d'aire

DE421 al FINAL 2 dona el Sol a **9,07°** i **X = 6,11**, coherent amb els 6,02 i
6,08 que `research/75` §5.2 va fer servir per als dos trens i amb els 6,16 que
`research/11` predeia per a Medina. La diferència entre els dos llocs, **0,05 EV
d'extinció**, és la que el §0 bis ja declarava.

## 0 · Per què calia reformular les portes

`research/98` va deixar el pilot bloquejat. Els seus números són exactes —els he
verificat tots un per un— però **les dues portes que el bloquejaven no es podien
passar mai, i una d'elles ni tan sols mesurava el que deia**.

**F0.** Deia «el flat aplicat ha de reproduir el que es va mesurar, coef.
1,00 ± 0,05». Aquella mesura és de la **Sony** i existeix perquè la seva muntura
va saltar 750 px. La Vixen mou el Sol **27,6 px** en tota la totalitat i el flat
radial hi canvia un **0,11 %**. No hi ha palanca i no n'hi pot haver. Codex ho
va veure bé; el que no va fer és substituir la porta per una que sí que en
tingui.

**F1.** Deia «residu ≤ 0,3 px rms al llenç comú», i es va avaluar contra el
residu de la **solució de placa** (0,424 px sobre 22 estrelles). Això és un
error de categoria: **n'hi ha una sola solució de placa per als 68 fotogrames**,
o sigui que el seu error és COMÚ —desplaça, gira i escala el llenç sencer igual
per a tothom— i **no desenfoca l'apilat**. El que el desenfoca és el centre per
fotograma.

I hi ha una cosa pitjor que ningú havia mirat: **el `sol_x, sol_y` del manifest
no és una mesura**. Ajustat contra el temps, el residu és **0,000000 px**: surt
d'un model lineal exacte. Qualsevol oracle avaluat sobre aquells números avalua
el model contra ell mateix. La meva primera versió d'F1 hi donava
**0,00217 px** i era **vàcua**.

## 1 · F1' · registre, i PASSA

El que sí que és mesurat és `lluna_mes_x, lluna_mes_y`, el centre del limbe
lunar, present a **42 dels 68** fotogrames.

- la seva dispersió respecte d'un model lineal de deriva és **0,55 px rms**;
- però la muntura no es mou a batzegades: la deriva és llisa i el que oscil·la
  és l'ajust del limbe. La posició adoptada és la del **model**, i el que s'ha
  de mesurar no és la dispersió d'una mesura sinó **quant es mouria el model si
  les dades fossin unes altres**.

Dos oracles, perquè cap dels dos sol no basta:

| oracle | què mesura | resultat |
|---|---|---|
| **split-half alternat** | precisió: dos models de 21 fotogrames disjunts | separació màxima **0,199 px** |
| **ruptura simulada** | adequació: hi cabria un graó? | 0,481 px, **p = 0,49** |

⚠️ **El split-half sol no serveix**: si la muntura patina, les dues meitats
pateixen el mateix salt, s'hi ajusten igual i coincideixen tan tranquil·les.
Provat: un salt de **6 px** el deixa passar. I ⛔ **el nul del detector de
ruptura no es pot fer permutant els residus**: si hi ha un salt, els residus el
porten a dins i el màxim permutat surt igual de gran —amb un salt de **750 px**
el p-valor sortia **0,26**—. El nul es simula amb el soroll que queda **després**
de posar-hi el graó. Calibrat així, la porta caça un salt d'**1 px** sobre
0,4 px de soroll i recupera'n la magnitud (750 px → 750,110).

**F1' PASSA a 0,199 px**, amb una exclusió que té mesura pròpia:

⚠️ **Les exposicions llargues tenen el centre del limbe biaixat i no poden
entrar a l'ajust.** Respecte del model dels curts, el limbe surt desplaçat
**+0,538 px als 2 s i +1,185 px als 10,08 s** —arrossegament de 2,92 px per
pose més vessament de la corona interior—. Amb elles a dins, la porta detecta
una ruptura de **1,446 px (p = 0,005)** i FALLA. Sense elles, passa. Els 68
fotogrames es col·loquen igualment: el que s'exclou és la seva **contribució a
l'ajust**, no el fotograma.

⚠️ **I el centre del manifest és 3,65 px diferent del que dona el limbe
mesurat** —0,83 % de R☉—. Al principi vaig adoptar el del limbe. ⛔ **Era un
error i el §9 el rectifica**: qui està desplaçat és el limbe, no l'efemèride, i
ho demostra el segon tren. El pilot canònic va amb el centre d'efemèrides.

## 2 · TROBALLA · l'escala d'exposició del manifest no és la del cos

Els temps del manifest són els **nominals del menú**. L'escala física surt de
`TargetExposureTime` del MakerNote i és una escala **binària**:

| nominal | físic | diferència |
|---|---|---:|
| 1/60, 1/30, 1/15 | 1/64, 1/32, 1/16 | **−6,25 %** |
| 1/2000 … 1/125 | 1/2048 … 1/128 | −2,34 % |
| «10,3 s» | **10,079368399159 s** | −2,14 % |
| 1/3200 | 1/3251 | −1,57 % |
| 1/8 · 1/4 · 1/2 · 1 · 2 s | exactes | 0 |

Mesurat al compost, fer servir els nominals biaixa la fotometria **−3,10 % a
1,10 R☉** i **−1,7 % constant** per damunt de 3 R☉, o sigui un **gradient
radial d'1,4 %** inventat entre 1,1 i 3 R☉.

## 3 · F0' · calibratge, i passa 5 de 6 anells

L'estadístic bo és **corona menys cel**: la taxa d'un anell menys la de
4,2–5,1 R☉. És cec a un cel additiu —i el cel de la totalitat varia un ±20 %—
i sensible a qualsevol error **multiplicatiu**. I es jutja **anell per anell**,
amb els esglaons que hi tenen senyal de debò: a 2 R☉ una pose d'1/3250 s recull
**0,2 ADU** de corona, i el que s'hi mesuraria és un sistemàtic de sub-ADU
amplificat per 1/t.

⛔ **El llindar no es tria: el calibra la mesura.** Cada esglaó té de dos a
quatre fotogrames i la seva dispersió interna diu amb quina precisió es pot
mesurar.

| anell | esglaons | rms entre esglaons | terra de precisió | |
|---|---:|---:|---:|---|
| 1,05–1,15 R☉ | 8 | 1,54 % | 1,26 % | PASS |
| 1,15–1,30 R☉ | 7 | 1,30 % | 1,50 % | PASS |
| 1,30–1,60 R☉ | 6 | 1,43 % | 2,14 % | PASS |
| 1,60–2,20 R☉ | 7 | 1,59 % | 1,77 % | PASS |
| 2,20–3,20 R☉ | 5 | 1,34 % | 1,17 % | PASS |
| 3,20–4,20 R☉ | 3 | 3,54 % | 0,76 % | **FAIL** |

**Amb els temps nominals fallen els sis.** La porta discrimina.

⚠️ El que falla, 3,20–4,20 R☉, és l'anell enganxat al d'anivellament: allà la
corona val la meitat que el cel, i el que hi queda és que **anivellar el cel amb
un sol anell no pot treure un canvi de la seva forma radial**. La fotometria del
compost es declara bona **fins a 3,2 R☉**; més enllà, hi ha aquest deute.

**El flat radial s'aplica com a CANDIDAT DECLARAT**, amb la porta reduïda a una
fita d'amplitud: dins 1,3–7 R☉ val **4,97 % (0,0699 EV)**, i mesurat al compost
canvia **+0,05 % a 1,1 R☉ i −2,04 % a 4,9 R☉**. Aplicar-lo o no és una decisió
del 2 %; bloquejar el pilot per no poder validar-lo al 5 % era desproporcionat.
Les dues versions estan desades i es poden comparar.

## 4 · Dos defectes reals trobats pel camí

**1. El nivell de blanc efectiu no és 16383.** Al fotograma de 10,08 s, a
1,05–1,15 R☉, la mediana val **15.857 ADU sobre el fosc** —el pou n'és 15.872—
i la màscara `cru >= 16383` només n'atrapa el **0,9 %**: el cos no clava tots
els píxels saturats al mateix enter. El tall bo és `SOSTRE` (0,85 del pou).
Fiar-se de la màscara dura deixava entrar píxels del pou al mig d'una mesura de
corona i feia llegir **−98 %** on no hi havia res.

**2. La vora del fosc no s'ha de replicar** (confirmat de `research/98`): la
reixa autoritzada és 4640×6960 i el màster dark és 4638×6958. En comptes de
posar-hi NaN, el pilot treballa a **4638×6958**, que és exactament el que el
fosc cobreix: així **no hi ha cap vora sense dada** i no cal replicar res.

## 5 · Fase 2 · la composició, i les seves portes

Arquitectura, **una sola suma ponderada** sobre els 68 fotogrames de les 15
exposicions alhora, mai apilar per exposició i després fusionar:

```
N = Σ w·J        D = Σ w        g = N/D        w = t²/(S/g + RN²)
```

`N` i `D` es persisteixen per separat: són l'autoritat que Photoshop haurà de
reproduir, i la composició alfa **no** calcula Σ(wI)/Σw.

| porta | resultat |
|---|---|
| **F** compost ≡ mescla declarada | **PASS**, desviació relativa **6,1·10⁻⁸**, i invariant a l'ordre |
| **E** perfil radial monòton | **PASS** |
| **E2** graons de fusió | **PASS**, pitjor **−1,44 %** a 1,076 R☉ |
| **G** envolupant isotònica | **PASS**, excés 1,000 |
| **rectangle** | **PASS**, la frontera és la petjada del sensor, no una circumferència |

I a la fase 0, **5 dels 6 anells** (§3). El compost no és un producte tancat:
és un pilot amb el seu deute escrit.

### La porta G no té dents, i ara està escrit

Mesurada contra defectes injectats sobre un perfil `r^-2,5`, amb el límit d'1,30
que ve de `research/95`:

| defecte | excés | veredicte |
|---|---:|---|
| anell d'1 a 9 anells, ×1,45 | 1,17–1,23 | **PASS** |
| graó multiplicatiu ×1,40 | 1,15 | **PASS** |
| anomalia ×2,00 | 1,35–1,55 | FAIL |

El PAVA **absorbeix** una pujada agrupant-la amb els veïns, i com més fort baixa
el perfil, més se n'hi amaga. La G és per al perfil d'amplitud d'un pas alt, no
per a la lluminància.

### La porta E2, nova, i les dues maneres de fer-la malament

Un compost HDR mal escalat no trenca la monotonia ni sobresurt de l'envolupant:
hi posa un **salt multiplicatiu** al radi on canvia l'esglaó dominant. Se sap on
són aquests radis —aquí: **1,086 · 1,169 · 1,273 · 1,408 · 1,564 · 2,093 R☉**—,
o sigui que s'hi mira.

⛔ **Extrapolar rectes no serveix**: el perfil de la corona va de pendent −11,1 a
1,09 R☉ fins a −1,2 a 2,1 R☉, i dues rectes a banda i banda d'un punt llegeixen
aquella curvatura com un graó. Sobre un perfil **net** deia **−20 % a totes les
transicions**, sempre del mateix signe. ⛔ **Amb paràboles tampoc**: +7 %.

El que funciona: la **derivada logarítmica** d'un perfil llis també és llisa i un
graó hi posa una punta. El nul no es tria —**són els radis que no són
transicions**— i la resposta es calibra **injectant** un graó conegut. Sobre el
perfil net dona **−0,009 %**, i caça el graó del 6,25 %.

## 6 · El que en surt

- llenç comú **7686 × 8378 px**, 17,44 × 19,01 R☉, nord amunt, Sol al centre,
  escala 2,1494814 ″/px, en **B/B☉**;
- **95,83 %** de la reixa del sensor amb dada (al llenç girat, el rectangle de
  la petjada n'ocupa el **48,03 %** del rectangle envolupant, que és el que un
  gir de 57,2° fa), cobertura mediana **296** contribucions per píxel;
- el lòbul fosc de les 5 h **és corona real**: cobertura (296) i esglaó dominant
  (13) idèntics al costat oposat, i el contrast decau amb el radi (0,42 a
  1,2 R☉ → 0,89 a 3 R☉), que és com es comporta l'estructura i no un artefacte.

## 8 · La passada de la Sony, i els dos trens al mateix llenç

Feta a continuació, el mateix vespre. Producte:
`output/pilot_vixen_claude_20260823/sony_llenc_comu/` i `.../dos_trens/`.

### El problema de la Sony no és el de la Vixen

Aquí la muntura va **patinar 750 px** a mig de la totalitat (`research/96`), o
sigui que els 30 fotogrames de dins la totalitat són a **dos apuntaments** i el
segon encara s'assentava quan es van fer els primers de després. **No hi ha cap
model global de deriva que travessi el salt**, i per tant el registre no en surt.

En surt de dues coses: els **deu fotogrames ancorats per estrelles** de
`registre_v3_sony.json`, i, per als altres, **la ràfega**. Cada pulsació dona
tres subfotogrames i dins d'una ràfega el cos no es mou més del que la deriva
permet en els pocs segons que dura.

⛔ **Les ràfegues no es poden agrupar per un forat de temps sol.** Una ràfega
d'àncora dura més de nou segons —1 + 0,125 + 8— i el descans entre ràfegues
n'és de deu: amb un llindar de 5 s la ràfega es parteix i el fotograma del mig
es queda sense la seva segona àncora; amb un de 12 s, dues ràfegues es fonen.
El que les separa és **l'estructura del programa**: cada ràfega és una tríada i
no repeteix exposició. Amb això surten les deu ràfegues exactes.

⛔ **I la incertesa de l'herència no la pot fitar el model del grup.** L'EXIF de
la Sony **no porta subsegon**, o sigui que un fotograma heretat pot equivocar-se
la deriva d'un segon. Al grup C el model global dona 0,24 px/s, però entre
`DSC06991` (t=59) i `DSC06993` (t=67) la posició es mou **4,18 px en 8 s =
0,52 px/s**: la muntura encara s'assentava. La fita ha de sortir de la **taxa
local entre les àncores que envolten el fotograma**, i llavors `DSC06992` surt
a 0,52 px i queda **exclosa**.

| | |
|---|---:|
| admesos | **14** (10 per estrelles + 4 heretats de ràfega) |
| integració | **24,975 s** |
| pitjor incertesa d'herència | **0,175 px** → PASS |
| exclosos | 4 (`06988` traços, `06990` moguda, `06989` sense àncora, `06992` 0,52 px) |
| fora d'abast | 12 fotogrames de contacte |

⛔ Els blocs de contacte (1/6400, 1/800, 1/100) **no entren**: no tenen ni
estrelles ni limbe net, i amb `w = t²/…` la seva aportació a la corona és
menyspreable. Són per a les perles i l'anell.

### Un defecte de la composició amb rotació que la Vixen no tenia

A la Vixen la suma es fa amb translacions subpíxel a la seva pròpia reixa. La
Sony va a una altra escala i una altra orientació (3,2020 ″/px i PA 90,27°
contra 2,1495 i 57,19), o sigui que **cada fotograma s'ha de girar**.

Interpolar el pes i el producte pes×valor per separat i després dividir és
correcte **on hi ha pes** i **basura on no n'hi ha**: el nucli de Lanczos té
lòbuls negatius i a la vora del fotograma i a la de la màscara lunar deixa
píxels amb `w` pràcticament zero i numerador no nul. Sense terra, el compost
hi treia **−3,3 B/B☉**, trenta mil vegades el màxim real, i **la porta F ho va
caçar** (desviació 1,0007). Amb un terra relatiu al pes màxim del pla, F torna
a **9,3·10⁻⁸** i el rang és de −2,1·10⁻⁵ a 5,6·10⁻⁵ B/B☉.

### Els dos trens, sense cap paràmetre lliure

Llenç comú de la unió: **10450 × 12878 px**, 23,72 × 29,23 R☉, nord amunt, Sol
al centre. Solapament: **22,96 %**.

Cada tren hi arriba amb el seu propi factor absolut a B/B☉ —2,772·10⁻¹¹ la
Vixen i 1,134·10⁻¹¹ la Sony (`research/75` §5.2)— i el quocient es mesura tal
com surt:

| radi | Vixen (B/B☉) | Sony (B/B☉) | Sony/Vixen |
|---|---:|---:|---:|
| 1,13 R☉ | 1,30·10⁻⁶ | 1,41·10⁻⁶ | **1,089** |
| 1,59 R☉ | 1,09·10⁻⁷ | 1,24·10⁻⁷ | **1,141** |
| 2,51 R☉ | 2,09·10⁻⁸ | 2,33·10⁻⁸ | **1,112** |
| 3,43 R☉ | 1,52·10⁻⁸ | 1,67·10⁻⁸ | **1,097** |
| 5,27 R☉ | 1,29·10⁻⁸ | 1,39·10⁻⁸ | **1,086** |

**Mediana 1,0972, de 1,085 a 1,144.** Dues calibracions absolutes independents
que coincideixen al **9,7 %, o sigui 0,13 EV**, sense que ningú els hi hagi
ajustat res.

⚠️ El «rang azimutal» que aquesta secció donava està **rectificat al §10**: era
la vora de la màscara lunar, i l'estructura azimutal de veritat és de l'1 %.

⛔ **I això NO valida la fotometria del producte fusionat.** `research/97` (D1)
ho declara: amb `k(φ)` lliure l'acord entre trens s'hi imposa. El que aquí es
diu és una altra cosa i més petita: que les dues escales absolutes, cadascuna
mesurada pel seu costat, són consistents al 10 %. La forma del quocient —que
puja a 1,14 cap a 1,6 R☉ i baixa a 1,086 a 5,3 R☉— **no està explicada**, i és
el següent número a entendre.

⚠️ Els dos trens **no s'anivellen el cel al mateix anell**: la Vixen a
4,2–5,1 R☉ i la Sony a 6–8 R☉, perquè el camp de la Vixen no arriba a 8 R☉.
Això és una diferència additiva declarada entre els dos productes.

## 9 · RECTIFICACIÓ · el centre bo és el de l'efemèride, no el del limbe

Aquesta secció **corregeix una decisió de la §1** d'aquest mateix document, i
qui la va destapar és el segon tren.

Amb el compost de la Vixen centrat al **limbe mesurat** i el de la Sony centrat
a la seva **placa astromètrica**, els dos trens no comparteixen origen:

| centre de la Vixen | desplaçament Sony−Vixen | rang azimutal del quocient a 1,15 R☉ |
|---|---:|---:|
| limbe mesurat | **3,39 px** | **0,131** |
| efemèrides del manifest | **1,20 px** | **0,072** |

El desplaçament es mesura sense cap paràmetre lliure ajustant
`ln(S/V) = a + dx·∂lnV/∂x + dy·∂lnV/∂y`, i surt igual des de dominis radials
independents (3,35 px a 1,10–1,60 R☉ i 3,90 a 1,60–2,60).

⚠️ **Però aquesta comparació sola no decideix res**, i val més dir-ho: els dos
centres d'efemèrides surten de la mateixa efemèride, o sigui que coincideixin
no és evidència independent. El quocient entre trens només és sensible a la
**diferència** dels seus centres, no a un error comú.

### La prova que sí que decideix: mesurar el limbe també a la Sony

S'ha ajustat el limbe lunar a sis fotogrames de la Sony amb el mateix mètode
—màxim del gradient radial sobre 720 rajos i cercle robust— i s'ha comparat amb
la seva posició d'efemèride:

| tren | biaix del limbe respecte de l'efemèride, al llenç comú |
|---|---|
| **Vixen** R6 III + VSD90SS, 2,1495 ″/px, PA 57,19° | (−0,89, −3,54) px = **3,65 px** |
| **Sony** A7RIIIA + 300 GM, 3,2020 ″/px, PA 90,27° | (−0,98, −3,73) px = **3,85 px** |

**Coincideixen a 0,21 px.** Dos cossos diferents, dues òptiques diferents, dues
escales, dues orientacions i dos sensors, i **el mateix vector de 8,0 ″ al cel**.

Això exclou que sigui un defecte d'un instrument. Queden dues lectures, i una
cau tota sola:

- que l'efemèride de la Lluna estigui 8,0 ″ fora. **No**: 8 ″ de paral·laxi
  lunar demanarien uns **15 km** d'error a la posició de l'observador, i la de
  Pere es coneix amb metres;
- que el que està desplaçat sigui **la mesura**. És a dir: «el centre del cercle
  que millor ajusta el màxim del gradient al limbe» **no és** el centre de la
  Lluna quan la corona interior asimètrica vessa per damunt de la vora fosca.
  El radi ajustat ho corrobora: surt **292–302 px** contra els **309** esperats,
  o sigui de 2 a 5 % petit, que és exactament el que fa un gradient que la
  corona aplana per fora.

És el mateix mecanisme, en gran, que el biaix per exposició que la §1 ja havia
mesurat: **+0,538 px als 2 s i +1,185 px als 10,08 s**.

### Què canvia i què no

- **el centre absolut adoptat passa a ser el de l'efemèride**, als dos trens,
  i el pilot canònic s'ha reconstruït amb ell. `--centre limbe` continua
  disponible i el seu compost es conserva com a control;
- **el registre relatiu no canvia**: el biaix del limbe és **comú** —el mateix
  cel per a tots els fotogrames— i per tant no desenfoca res. La porta F1 i el
  seu oracle continuen valent, i el que demostren —que la Vixen **no** té cap
  salt de muntura— també;
- ⛔ **la lliçó de mètode**: la §1 va rebutjar el `sol_x` del manifest perquè
  «no és una mesura, és un model». El criteri era dolent. Un model d'efemèride
  pot ser millor que una mesura quan la mesura té un biaix físic, i aquí en té
  un de 8 ″. El que calia no era triar entre model i mesura sinó **posar-hi un
  segon instrument**.

### I una porta que mesurava la màscara

Amb el centre nou, la porta E2 va cantar un graó de **−2,77 % a 1,066 R☉**. No
era un graó de fusió: la màscara lunar val zero fins a `R☉ + 4 px` i puja en
14 px —fins a 1,085 R☉—, i com que **la Lluna es mou ±14 px respecte del Sol**,
en radi solar la seva vora queda escampada **fins a 1,117 R☉**. El perfil hi
mesurava la màscara. Amb el domini començant a **1,15 R☉**, els quatre composts
passen E i E2, i el pitjor graó del canònic és **−0,49 %**.

## 10 · De què està feta la discrepància entre trens

Descomposició de Fourier azimutal de `ln(Sony/Vixen)`, anell per anell, amb el
centre ja rectificat i el domini començant a 1,15 R☉:

| R☉ | m=0 | \|m=1\| | fase m1 | \|m=2\| | residu m>4 |
|---|---:|---:|---:|---:|---:|
| 1,25 | 0,1158 | 0,0106 | −130° | 0,0137 | 0,018 |
| 1,75 | 0,1222 | 0,0108 | −114° | 0,0077 | 0,006 |
| 2,55 | 0,1044 | 0,0068 | −18° | 0,0027 | 0,006 |
| 3,80 | 0,0891 | 0,0075 | −13° | 0,0049 | 0,004 |
| 4,65 | 0,0843 | 0,0066 | — | — | — |

⚠️ **Rectificació d'una xifra d'aquest mateix document**: la §8 parlava d'un
«rang azimutal del 13 % a 1,15 R☉». Aquell número sortia d'un anell que
començava a 1,05 R☉ i **estava mesurant la vora de la màscara lunar**. Amb el
domini bo, l'estructura azimutal és de l'**1 %**, no del 13.

I la **fase del dipol gira** amb el radi, de −130° a −13°. Un error de centre
donaria una fase **constant**: o sigui que el que queda no és un error de
centre. La resta és petita: m=2 i m=3 per sota de l'1,4 %, i el residu per
damunt de m=4, entre 0,4 i 1,8 %.

**El que queda per explicar és el terme radial `m=0`**, que va de +12,3 % a
1,25 R☉ a +8,4 % a 4,65.

### El que el flat de la Vixen hi fa, mesurat

Els dos composts, l'un amb el flat radial de la Vixen i l'altre sense, **i tots
dos amb el mateix centre** —⚠️ la primera comparació que vaig fer estava
confosa perquè el compost sense flat encara portava el centre antic, i donava
una reducció del dipol de 5× que **no existeix**—:

| | recorregut radial de m=0 | \|m=1\| mitjà |
|---|---:|---:|
| amb el flat de la Vixen | **4,72 %** | 0,0084 |
| sense | **3,34 %** | 0,0091 |

El flat millora el dipol un 8 % i **empitjora l'acord radial**, fins a
**+1,68 %** a 4,65 R☉.

### Qui corregeix quant

Els dos trens no vinyetegen igual ni de bon tros. Correcció que cada flat
aplica, respecte del seu valor a 1,25 R☉:

| R☉ | Vixen | Sony | diferència |
|---|---:|---:|---:|
| 2,55 | −0,40 % | −5,33 % | 4,93 % |
| 3,80 | −1,08 % | −10,71 % | 9,63 % |
| 4,65 | **−1,94 %** | **−14,42 %** | 12,49 % |

El desacord que el flat de la Vixen introdueix a 4,65 R☉ —1,68 %— és
**pràcticament tota la seva correcció allà** (1,94 %), i només el **12 %** de la
de la Sony. I la de la Sony està validada contra un donant S6 amb
r = 0,9999957–0,9999972 i p95 de 0,16–0,55 % (`research/90`), mentre que la de
la Vixen només era «candidat de pilot». **L'explicació més econòmica és que el
radial de la Vixen sobrecorregeix**, i aquesta és la primera evidència externa
que aquell flat ha tingut mai — exactament el que la porta F0 no podia donar
amb dades de la Vixen soles.

⛔ **Però no ho tanca**, i val més dir-ho: encara sense el flat de la Vixen
queda un **3,34 %** de tendència radial entre trens que **cap dels dos flats
explica**, i mentre no se sàpiga d'on ve, atribuir-li l'1,68 % restant a un sol
dels dos és una tria, no una mesura. El model additiu ja està descartat —ajusta
al 8,98 % contra l'1,94 % del multiplicatiu—, o sigui que **no és la diferència
d'anell d'anivellament de cel**. Queden la llum difosa dels dos trens, que van
a f/2,8 i f/5,5, i els factors absoluts a B/B☉.

## 11 · La causa: més enllà de 2,4 R☉ el compost és CEL, no corona

Això explica el 3,34 % que la §10 deixava obert, i és la troballa amb més
conseqüències de tot el pilot.

Els perfils radials dels dos trens s'ajusten a **corona física més cel**, amb el
model de Baumbach (1937) per a la corona K+F i **dos paràmetres per tren**:

```
total(r) = α · Baumbach(r) + cel
```

| | α | cel (B/B☉) | residu |
|---|---:|---:|---:|
| **Vixen** | 1,302 | **1,167·10⁻⁸** | 3,41 % |
| **Sony** | 1,482 | **1,263·10⁻⁸** | 3,23 % |

Amb un pendent al cel, el residu baixa a **2,80 %** als dos trens i el pendent
surt **+4,8·10⁻¹⁰ i +4,4·10⁻¹⁰ per R☉**: pràcticament el mateix, i **positiu**,
que és el que ha de passar quan mires cada vegada més lluny del centre de
l'ombra.

### La conseqüència

| | |
|---|---|
| **el cel iguala la corona a** | **2,41 R☉** |
| a 3 R☉ el cel és | **2,2×** la corona |
| a 5 R☉ el cel és | **9,2×** la corona |
| a 4,88 R☉ el cel és | **88,5 %** del total mesurat |

⛔ **El compost no porta el cel restat: l'anivellament de cel només l'IGUALA
entre fotogrames, no el treu.** O sigui que del compost, tal com és, **de
2,4 R☉ enfora se n'està mirant sobretot el cel del lloc**, no la corona.

Fins on es pot recuperar la corona depèn només de com bé es conegui aquell cel:

| error del cel | corona/incertesa > 10 fins a |
|---|---|
| 1 % | 5,15 R☉ |
| 2 % | 3,96 R☉ |
| 5 % | 2,91 R☉ |

I el cel **varia un ±20 % al llarg de la totalitat** (`research/76`) i té pendent
radial: conèixer-lo a l'1 % no és gratuït. Això confirma per una via
independent el límit de **3,2 R☉** que la §3 ja declarava, i explica per què la
porta F0 falla justament a l'anell de 3,2–4,2 R☉ —allà el senyal és **80 % cel**.

### I explica la discrepància entre trens

Separades les dues components, els dos trens no discrepen d'una manera sinó de
dues:

| | quocient Sony/Vixen |
|---|---:|
| **corona** | **1,1384** |
| **cel** | **1,0824** |

Barrejar-les en proporció que canvia amb el radi dona **exactament** la
tendència observada, de 1,13 a on mana la corona fins a 1,084 a on mana el cel.
No cal ni llum difosa ni res més: el 3,34 % de la §10 **és això**.

Que els dos quocients siguin diferents té una explicació natural i comprovable:
**el cel i la corona no tenen el mateix espectre** —el cel és llum solar
dispersada, més blava— i els dos cossos tenen filtres verds diferents. Els
factors absoluts a B/B☉ es van ancorar amb una sola d'aquestes dues llums, o
sigui que no poden valer per a totes dues alhora.

### El que això mana fer

1. **restar el cel, no anivellar-lo**, abans de qualsevol fotometria coronal
   més enllà de 2 R☉;
2. **no fusionar trens sense separar corona i cel abans**: el factor que els
   iguala no és un, són dos;
3. la α mesurada, **1,30 i 1,48 vegades la corona mitjana de Baumbach**, és
   coherent amb un eclipsi a prop del màxim solar i és el primer ancoratge
   absolut del pilot contra un model extern.

Rebut: `output/pilot_vixen_claude_20260823/separacio_corona_cel.json`.

## 12 · La separació que no depèn de cap model: el cel varia i la corona no

La §11 separa corona i cel **assumint** que la corona segueix Baumbach. Es pot
fer millor, i sense assumir res sobre la corona, perquè **el cel de la totalitat
varia amb el temps i la corona no**.

La forma temporal del cel, mesurada a l'anell de 4,4–5,1 R☉ amb els divuit
fotogrames de 0,125 s o més, fa una **V** neta:

| t−C2 | 10,4 s | 20,4 | 33,6 | **46,6** | 60,0 | 78,2 | 92,1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| cel relatiu | 1,174 | 1,025 | 0,924 | **0,876** | 0,879 | 0,945 | 1,129 |

**29,9 % de recorregut**, mínim al mig de la totalitat: és el punt d'observació
allunyant-se i tornant a la vora de l'ombra, tal com `research/76` ja descrivia.

Amb això, cada anell s'ajusta a `total(t) = corona + cel·f(t)` **sense cap model
de corona**:

| anell | corona (B/B☉) | cel (B/B☉) | cel/total | residu |
|---|---:|---:|---:|---:|
| 1,9–2,4 R☉ | 1,00·10⁻⁸ | 1,73·10⁻⁸ | 63,3 % | 1,87 % |
| 2,4–3,0 | 4,61·10⁻⁹ | 1,37·10⁻⁸ | 74,8 % | **0,43 %** |
| 3,0–3,7 | 1,63·10⁻⁹ | 1,35·10⁻⁸ | 89,2 % | **0,23 %** |
| 3,7–4,4 | 5,37·10⁻¹⁰ | 1,31·10⁻⁸ | 96,1 % | **0,14 %** |
| 4,4–5,1 | **0** | 1,29·10⁻⁸ | **100 %** | 0,00 % |

Els residus de 0,1 a 0,5 % diuen que el model de dues components **descriu les
dades gairebé exactament** allà on el cel mana.

⚠️ Als anells de dins de 1,9 R☉ l'ajust es trenca —corona negativa i residus del
20 %— perquè allà el que varia entre fotogrames no és el cel sinó els
sistemàtics de cada esglaó d'exposició. Aquesta separació **només val de
1,9 R☉ enfora**, que és justament on cal.

### Per què això és una fita i no una estimació

Si el cel de veritat és `S_var·f(t) + S_const`, l'ajust posa `S_const` dins el
terme constant. O sigui:

- la **corona** que en surt és una **fita SUPERIOR**;
- el **cel** que en surt és una **fita INFERIOR**.

I encara així: **a 3,7–4,4 R☉ la corona és com a molt el 3,9 % del que es
mesura**, i a 4,4–5,1 R☉ **com a molt zero**.

### I rebaixa la §11

Aquesta mesura és més severa que l'ajust de Baumbach. A 4,05 R☉ aquell donava
2,1·10⁻⁹ de corona i aquesta en dona **com a molt 5,4·10⁻¹⁰**: quatre vegades
menys. La α = 1,302 de la §11 estava **inflada** perquè el cel té un lleuger
pendent radial (+4,5·10⁻¹⁰ per R☉, §11) i un pendent radial és exactament el
que un model de corona sap imitar. **On les dues discrepen, mana aquesta**, que
no assumeix res sobre la corona.

### El que això mana fer, ara amb número

El cel es pot mesurar **fotograma a fotograma** amb la seva pròpia signatura
temporal, i el que en queda després de restar-lo és corona de veritat. El límit
pràctic surt de la part **constant** del cel, que aquesta via no veu: mentre no
hi hagi una segona palanca per a `S_const` —una altra latitud dins l'ombra, un
model d'ombra, o una nit de referència—, **la corona d'aquest conjunt no es pot
declarar mesurada més enllà d'uns 3 R☉**, i el que hi hagi més enllà és una
imatge del cel del MIRADOR FINAL 2 amb una mica de corona a sobre.

Rebut: `output/pilot_vixen_claude_20260823/separacio_per_temps.json`.

## 13 · El model de cel implementat, i dos defectes que va destapar

La §12 diu què s'ha de fer; això és fer-ho.
`pilot.py cel` mesura, i `pilot.py f2 --cel model` compon amb el cel restat.

**El model.** Per a cada cel·la d'una reixa binnada 16×16 i amb els divuit
fotogrames de 0,125 s o més, `taxa(t) = C + S·f(t)`, amb `f` la forma temporal
de l'anell de 4,4–5,1 R☉ —una V de **30,6 %** amb el mínim a t = 46,6 s—. El
cel restat de cada fotograma és `S·f(t)·exposició`.

**El cel té forma**: `S` va de **346 a 391 ADU/s** al llarg del camp, un **13 %**
de gradient espacial, i **cap número per fotograma no pot treure això**. És
exactament el que `anivella_fons` deixava enrere.

### Defecte 1 · el model seguia la corona i se la restava

Amb `S` cru, el perfil sortia **negatiu de 1,18 a 1,99 R☉** i a 1,45 R☉ es
restava **tres vegades** el que hi havia. La causa: a dins de 2 R☉ la corona
també varia entre fotogrames —rampa de saturació, sistemàtics de cada esglaó— i
l'ajust li ho atribueix al terme variable.

El cel és una superfície **llisa** i no té cap motiu per tenir estructura
justament al voltant del Sol. Ara `S` s'ajusta a una **quàdrica 2-D de sis
termes**, **només on la corona és petita** (r > 2,5 R☉, 110.532 cel·les, residu
**1,48 %**), i s'avalua a tot el camp. Això també compleix la norma del
rectangle: el model existeix a tot arreu i no s'atura a cap circumferència.

### Defecte 2 · restar el cel canviava el llindar de saturació

Aquest era pitjor i més silenciós. El pes és
`w = t²/(S/g + RN²)` amb rampa i tall a `SOSTRE`, i tot això es calculava sobre
el valor **ja restat**. Un píxel que és al pou hi és tant si el cel hi és com si
no: restar-li'l abans del llindar **el torna admissible**.

Mesurat: a 1,15–1,25 R☉ el fotograma de **10,08 s —saturat allà—** passava a ser
el dominant, el denominador es multiplicava per **61** i el compost hi queia un
**94 %**. Ara la saturació i la variància es jutgen amb el valor **cru** i el
valor amb el restat.

⚠️ I el defecte era **doble**: la porta F0 tenia el mateix, i amb el cel restat
cantava −98 % als anells de dins. Corregit als dos llocs.

### Defecte 3 · el cel no és del mateix color que la corona

La primera versió mesurava el cel com a **mitjana del mosaic** i el restava
igual als quatre plans de Bayer. El cel de la totalitat és llum solar
**dispersada** i no té el color de la corona: mesurat per pla, val
**R = 193, G = 473/474 i B = 344 ADU/s**. Restar-los a tots la mitjana deixava
un residu de color enorme i el compost sortia **verd de 2 R☉ enfora**.

⛔ **Però el color tampoc es pot treure de l'ajust temporal de cada pla.** `f(t)`
es mesura al verd, i si el cel canvia de color amb el temps —i en canvia, la
vora de l'ombra no és neutra— l'ajust dels altres plans surt esbiaixat amb una
palanca d'**1/0,30 = 3,3×**. Provat: el blau sortia **negatiu de 3,2 R☉ enfora**.

El color es mesura **on el cel mana**: a 4,4–5,1 R☉, on n'és el 96 % del senyal.
Respecte del verd: **R = 0,4856 · B = 0,6330**. El poc de corona que hi queda és
de color solar i hi pesa un 4 %.

### El producte

| R☉ | amb cel | cel restat | % de cel | × Baumbach |
|---|---:|---:|---:|---:|
| 1,18 | 8,85·10⁻⁷ | 8,74·10⁻⁷ | **1,2 %** | 1,41 |
| 1,86 | 4,85·10⁻⁸ | 3,79·10⁻⁸ | 21,8 % | 1,27 |
| 2,53 | 2,06·10⁻⁸ | 9,82·10⁻⁹ | 52,3 % | 1,34 |
| 3,55 | 1,50·10⁻⁸ | 4,18·10⁻⁹ | 72,1 % | 1,71 |
| 4,90 | 1,32·10⁻⁸ | 2,44·10⁻⁹ | **81,5 %** | 2,38 |

*(la taula de sobre és de la primera versió, amb el cel com a mitjana del
mosaic; amb el model per pla corregit el cel restat és més gran i el que en
queda, menys.)*

Amb el model definitiu —quàdrica al verd i color mesurat a 4,4–5,1 R☉— el
perfil és **decreixent a tot el domini** i les quatre portes hi passen: **E, E2,
G i rectangle**. A 1,5–3,0 R☉ val **1,037 vegades** la corona mitjana de
Baumbach, i els colors es mantenen coherents —R/G de 0,81 a 0,88 i B/G de 0,30
a 0,35— **fins a uns 3 R☉**.

⚠️ **I el domini de validesa és aquest, no més.** El verd creua zero a
**4,64 R☉** i el blau a **4,04**. No és un error de signe: allà la corona val
~1·10⁻⁹ i el cel ~1,2·10⁻⁸, o sigui que el **1,95 %** de residu que té el propi
model de cel ja n'és el 25 %. **El producte amb el cel restat val fins a uns
3–3,5 R☉**, exactament el que la taula del §12 anunciava.

### El que el model NO arregla

**La porta F0 no millora.** Amb el cel restat, 4 dels 5 anells passen —igual
que amb l'anivellament per anell— i el de 3,20–4,20 R☉ falla **més** (−9,85 %
contra −6,14 %). No és una contradicció: el model de cel té el seu propi residu
de l'1,3 al 1,5 %, i allà el cel és el **80 %** del senyal, o sigui que aquell
residu surt multiplicat per cinc sobre el que en queda. **Restar el cel millora
el producte i empitjora el test**, perquè el test passa a mesurar el residu del
model en lloc de la barreja.

Els dos composts es conserven: `fisiques_flat-si` (anivellament per anell, el
canònic per a la imatge) i `fisiques_flat-si_cel-model` (cel restat, el canònic
per a la fotometria fins a ~3 R☉).

## 14 · La Sony amb el cel restat, i el límit real de la comparació entre trens

El model de cel també s'ha fet per a la Sony, i amb ell la comparació entre
trens deixa de ser de «corona + cel» i passa a ser de **corona sola**. El
resultat és el més important d'aquesta passada, i és una limitació.

### El cel de la Sony s'ha d'ajustar al LLENÇ, no al sensor

Ajustat per píxel de sensor, com el de la Vixen, la quàdrica dona un residu del
**51,5 %**. La causa és el salt de muntura: **750 px = 2,5 R☉** entre els dos
apuntaments, o sigui que un mateix píxel del sensor mira dos punts del cel
diferents i l'ajust confon el salt amb la variació del cel. El cel és fix al
CEL. Ajustat en coordenades de llenç, sobre 1.523.401 mostres a r > 5 R☉ —el
camp de la Sony arriba a 13 R☉—, el residu baixa a **3,09 %**.

⛔ I la **forma temporal** es pren de la Vixen: divuit fotogrames repartits per
tota la totalitat contra onze de la Sony partits entre dos apuntaments. La Sony
hi aporta l'amplitud i la forma espacial, que és el que sap fer millor.

### El deute que aquest model porta a sobre

El terme constant de l'ajust —que hauria de ser la corona residual a r > 5 R☉—
surt **−206 ADU/s**. És impossible, i val el **18 % del senyal**. Es fixa a zero,
cosa que atribueix tot el que hi ha a r > 5 R☉ al cel, i per tant **aquest model
pot sobre-restar fins a un 18 %**. Amb un 30 % de variació temporal i onze
fotogrames, la separació constant/variable no està prou condicionada.

### El resultat, i el límit

| R☉ | q del TOTAL | q de la CORONA SOLA |
|---|---:|---:|
| 1,30 | 1,141 | **1,146** |
| 1,70 | 1,133 | **1,165** |
| 2,10 | 1,122 | 1,230 |
| 2,50 | 1,114 | 1,345 |
| 3,10 | 1,104 | 1,612 |
| 3,90 | 1,091 | 2,248 |
| 4,50 | 1,087 | **3,479** |

**El quocient del total és estable —recorregut del 4,9 %— i el de la corona sola
es dispara: 155 %.**

⛔ **I això no diu res de la corona: diu que els dos models de cel no són
consistents entre ells.** A 4,5 R☉ el residu de la Vixen val 3,9·10⁻¹⁰ i el de
la Sony 1,35·10⁻⁹, tots dos restes petites d'un cel de ~1,3·10⁻⁸: **una
diferència de pocs punts percentuals entre els dos models de cel es converteix
en un factor 3,5 sobre el que en queda**. És la mateixa aritmètica del §12 vista
des de l'altre costat.

### El que sí que en surt

**Fins a uns 2 R☉ la comparació de corona sola és bona**, perquè allà el cel és
minoria: el quocient val **1,146 a 1,183**, estable. O sigui que **els dos trens
discrepen d'un 15 a un 18 % sobre la corona**, més que el 9,7 % que donaven
sobre el total —que era una barreja amb el cel, on discrepen menys—.

**Aquest 15–18 % és el número que calia explicar**, i el **§15 el contesta**:
és la incertesa declarada dels dos factors absoluts (±10 % cadascun → ±14,1 %
sobre el quocient), o sigui **1,2 σ**. No hi ha res trencat.

## 15 · La resposta al 15–18 %: és la incertesa declarada, no un defecte

Abans de contestar, un defecte propi que calia treure del mig.

### La Sony té la mateixa trampa d'exposició que la Canon

Jo li estava passant l'`ExposureTime` de l'EXIF, que és el **nominal del menú**.
El MakerNote (`SonyExposureTime`) diu que **1/30 és de fet 1/32**, un
**−6,25 %**, i afecta els tres fotogrames de 1/30 de dins la totalitat. La resta
de l'escala d'aquest cos (1/8, 1/4, 1, 2, 8 s) sí que és exacta; els blocs de
contacte van tots **−1,4 %** i queden fora d'abast igualment.

⚠️ I en corregir-ho van sortir dos efectes col·laterals que valen per a
qualsevol pipeline d'aquest projecte: les **tríades del programa** es declaraven
amb els valors nominals i van deixar d'aparellar-se —tres fotogrames van caure
del registre sense dir res—, i el **màster dark** va deixar de trobar-se, perquè
va indexat pel nom del menú. **Física per escalar, nominal per indexar**, i
totes dues s'han de portar.

### El número, amb l'escala física als dos trens

| R☉ | q del total | q de la corona sola |
|---|---:|---:|
| 1,30 | 1,157 | **1,166** |
| 1,70 | 1,134 | **1,172** |
| 1,90 | 1,126 | **1,190** |
| 2,50 | 1,116 | 1,346 |
| 3,10 | 1,107 | 1,622 |

A **1,2–2,0 R☉**, on el cel és minoria i la comparació val: **Sony/Vixen =
1,1706**, o sigui **R6/Sony = 0,854**.

### I això què és

`research/75` §5.2 dona els dos factors absoluts amb **±10 % cadascun**. Dues
incerteses independents del 10 % fan **±14,1 %** sobre el quocient.

**El desacord mesurat és del 17 %, o sigui 1,2 σ.** No hi ha res a explicar:
**els dos trens són consistents dins de la incertesa que ells mateixos
declaren**. La hipòtesi de la llum difosa, la del flat i la de l'espectre no
calen per a aquest número —cadascuna pot valer per a la seva pròpia signatura,
però el nivell global ja queda explicat.

⚠️ El mateix `research/75` §5.2 donava **R6/Sony = 0,95** sobre la corona de
1,15 a 3 R☉, i jo en dono **0,854**: un **10 %** de diferència entre dues
determinacions del mateix. És esperable —entremig hi ha l'escala d'exposició
corregida als dos cossos, el centre d'efemèrides, el flat i el cel restat— i
totes dues cauen dins la mateixa banda del 14 %.

### El que això vol dir per a la via de la FOTO

- **l'escala absoluta del producte fusionat és incerta al ±14 %**, i cap acord
  entre trens no la millora: l'acord ja hi és, dins d'aquella banda;
- **qualsevol `k` que iguali els dos trens és un paràmetre lliure** amb la
  mateixa justificació que qualsevol altre valor dins del 14 %. Triar-lo és una
  decisió estètica, no una mesura, i `research/97` (D1) ja ho declara;
- **per baixar del 14 % caldria un ancoratge extern comú** —LASCO C2, K-Cor o
  una estrella de calibratge mesurada als dos trens el mateix dia—, no més
  feina sobre aquestes imatges.

## 16 · Fase 3 · Filtres, i el que els dos controls van caçar

Amb això el contracte de les quatre fases queda tancat per a un tren.
`pilot.py filtres <etiqueta>`.

### L'ACHF, llegit bé

La tesi de Brno §5.2 dona l'única fórmula publicada:
`C = exp(−[(r−ρ)² + (r(φ−ϕ))²]/2σ²)`. Això és una gaussiana en (Δr, arc), i
(Δr, arc) **són les coordenades locals de la imatge**: o sigui que el nucli de
l'ACHF **és isòtrop**, una gaussiana normal i corrent. El que el fa diferent
d'un unsharp qualsevol és l'altra meitat: **la convolució incompleta
normalitzada pel pes**,

    g = (I·w) ⊗ G_σ / (w ⊗ G_σ)

⛔ **I això és la norma del rectangle ben feta**: el filtre s'avalua a TOT el
rectangle i l'única cosa que el limita és que no hi hagi dada, cosa que entra
pel **pes** i no per cap circumferència.

I una cosa que aquest projecte pot fer i els filtres publicats no: `research/82`
diu que **la porta de soroll és el criteri**, i que només WOW i NAFE en porten
una de veritat. Aquí el compost **porta el seu mapa de variància per píxel**
(`1/Σw`), o sigui que el llindar **no s'estima, es calcula**. La porta és la de
WOW —`d·erf(|d|/(n_s·σ_d))`, suau, sense vores— amb l'escala de n_s decreixent
amb σ.

### Els dos controls, i els tres defectes que van caçar

⛔ La fase no s'accepta sense **dues entrades dolentes conegudes**: una corona
perfectament llisa —que no pot donar detall— i soroll pur —que ha de quedar per
sota de la porta—. Van fallar totes dues a la primera, i cada fallada era real:

| defecte | símptoma | correcció |
|---|---|---|
| l'ACHF sobre `ln I` cru | corona llisa → **6,6 %** de detall inventat | treure primer el **perfil radial** (NRGF), com Brno prescriu; baixa a **0,33 %** |
| escales sumades a pèl | soroll pur → **1,66 σ** a la sortida | els σ comparteixen entrada i el soroll se'ls suma **coherentment**: pesos que sumen 1; baixa a **0,40 σ** |
| `ln I` on el senyal va a zero | l'amplitud del passa-alt baixava de 1,2 a 3,1 R☉ i **pujava set vegades** fins a 4,8 | terra de **S/N ≥ 5**: el logaritme d'un valor que tendeix a zero es dispara i **passa qualsevol porta** |

El tercer el va caçar la **porta G**, amb un excés de 4,70 al radi 4,98. És la
primera vegada en tot el pilot que la G serveix per a alguna cosa —el §5 ja
havia mesurat que contra un graó de lluminància no té dents—, i és perquè aquí
sí que se li dona el que és seu: **el perfil d'amplitud d'un passa-alt**.

### El resultat

| | compost complet | amb el cel restat |
|---|---:|---:|
| rectangle amb dada i S/N ≥ 5 | **95,5 %** | 31,4 % |
| contrast del detall | 0,48 % | 1,12 % |
| **porta G** | **PASS** (excés 1,008) | FAIL (2,15) |
| rectangle | PASS | PASS |
| control d'entrada llisa | **0,33 %** PASS | 0,33 % PASS |
| control de soroll pur | **0,40 σ** PASS | 0,40 σ PASS |

σ = 2, 4, 8, 16 i 32 px, amb n_s = 6, 5, 4, 3 i 2.

**El producte de fase 3 és el del compost complet**: cobreix el 95,5 % del
rectangle i passa les quatre portes. El del cel restat té més contrast —lògic,
el cel el diluïa— però només cobreix el 31 % i la seva amplitud encara puja a
fora, o sigui que és per mirar, no per publicar.

⚠️ **Això és detall, no fotometria.** El filtre treballa en `ln I` i el que
lliura és **contrast relatiu**: no conserva B/B☉ i no es pot barrejar amb el
compost lineal sense declarar-ho.

## 17 · Els dos trens filtrats, i per què la FOTO no pateix el ±14 %

Fase 3 feta també a la Sony —**80,7 %** del rectangle, **G PASS** (excés 1,251),
rectangle PASS, control d'entrada llisa 0,44 %, control de soroll 0,40 σ— i el
producte dels dos trens al llenç comú.

### L'argument tècnic que la decisió D1 no tenia

El §15 diu que **l'escala absoluta del producte fusionat és incerta al ±14 %**
perquè els dos factors a B/B☉ ho són, i que qualsevol `k` que iguali els trens
és un paràmetre lliure.

⛔⛔ **Però un passa-alt sobre `ln I` lliura contrast RELATIU, i el contrast
relatiu no depèn de l'escala absoluta**: un factor multiplicatiu és una constant
additiva en logaritme, i el passa-alt la treu. O sigui que **la via de la FOTO
no pateix el problema que la via de la mesura sí que té.** És el millor argument
tècnic que la decisió D1 de `research/97` ha rebut, i no s'havia dit.

### La combinació, que és una decisió i no una mesura

⛔ **No pot anar per inversa de la variància.** Els dos trens tenen mostreig
diferent —2,1495 contra 3,2020 ″/px— i el compost de la Sony s'ha remostrejat
1,49× cap amunt en portar-lo al llenç: el seu Σw per píxel queda inflat un
factor ~2,2 que **no és senyal/soroll, és mostreig**. Provat: així la Sony
guanyava el **80,6 %** del llenç i la Vixen es quedava amb el **0,2 %**.

La regla és **declarada**: mana la **Vixen** on té dada —mostreja 1,49× més fi i
integra 24,975 s amb 68 fotogrames contra 14— i la **Sony** omple més enllà, amb
una rampa de 200 px perquè no hi quedi costura. Repartiment resultant: Vixen
**21,0 %**, Sony **59,8 %**, cobertura total **80,7 %** del rectangle.

### Fins on val

L'amplitud del passa-alt baixa de **0,0222 a 1,24 R☉** fins a un terra de
**0,000133 a 4,3–4,9 R☉** —**167 vegades** menys— i a partir d'allà torna a
pujar lentament. **Aquell terra és el soroll**, i el que puja després no és
corona: amb el domini de la porta G fins a 8 R☉ la G falla (excés 1,545) i és
ella qui ho diu. Amb el domini fins a 5 R☉, **G PASS**.

**El detall dels dos trens val fins a uns 4,5 R☉.** Més enllà hi ha el terra de
soroll, que en una imatge estirada es veurà com a textura i no és estructura.

## 18 · Pot Photoshop fer la suma ponderada? Mesurat, i la resposta és no en 16 bits

El traspàs demanava **decidir l'arquitectura numerador/denominador de Photoshop
abans de muntar cap PSB de producció**, i `research/98` demanava «demostrar el
round-trip dels pesos de Photoshop contra l'autoritat offline». Això ho contesta
amb números en lloc d'opinions.

### L'arquitectura que caldria

Photoshop no té cap mode que calculi `Σ(wI)/Σw` d'una tirada, però la té en dues:

- grup **N**: una capa per fotograma amb `w_i·J_i`, en **Linear Dodge (Add)** —
  que és literalment una suma;
- grup **D**: una capa per fotograma amb `w_i`, també en Linear Dodge (Add);
- el grup N sobre el D en **Divide**.

⛔ El que **no** funciona és el mode Normal amb opacitat: és composició alfa,
depèn de l'ordre, i la porta F ja té una prova que ho demostra
(`test_composicio_alfa_dependent_de_l_ordre_falla`).

### El problema és el rang, i es mesura

Photoshop **retalla la suma a 1,0**, o sigui que l'escala de cada capa no la fixa
el seu propi màxim sinó el **màxim de la suma a tot el llenç**. Mesurats al
compost del pilot: `max Σ(w·J) = 93,95` i `max Σw = 0,2392`.

Quantitzant les capes amb aquelles escales i recomponent:

| radi | 16 bits | 32 bits enter | 32 bits coma flotant |
|---|---:|---:|---:|
| 1,3 R☉ | **6,65·10⁻³** ⛔ | 2,0·10⁻⁷ | 1,1·10⁻⁷ |
| 2,2 R☉ | 4,8·10⁻⁵ | 4,5·10⁻⁹ | 1,4·10⁻⁷ |
| 4,0 R☉ | 4,6·10⁻⁶ | 4,7·10⁻¹⁰ | 2,5·10⁻⁷ |

**El límit de la porta F és 10⁻³.** En 16 bits, a **1,3 R☉ el falla per un
factor 6,6**: allà el pes màxim val 9,7·10⁻⁵ contra un màxim de llenç de 0,2392,
o sigui que les capes hi queden quantitzades a **1/2.500 de l'escala** i s'hi
perden onze bits.

I hi ha dues coses més que el 16 bits no pot fer de cap manera:

- el quocient `(Σn)/(Σd)` amb aquelles escales **va de −71 a +2069**, o sigui
  tres ordres de magnitud fora de l'interval [0,1] que un Divide de 16 bits
  admet;
- **hi ha valors negatius** —el compost baixa a −2,8·10⁴ ADU/s en píxels de
  fons—, i en enter sense signe **no existeixen**.

### La decisió

**En 32 bits de coma flotant sí que es podria** —Photoshop els admet, i sense
retall a 1,0—, i l'error hi seria de 10⁻⁷, mil vegades per sota de la porta.

⛔ **Però no s'ha de fer.** Muntar seixanta-vuit capes en dos grups per
reproduir una suma que l'autoritat offline ja fa —i que la porta F certifica a
**6,1·10⁻⁸**— és canviar una cosa provada per una de fràgil, i cada capa hi
afegeix una manera d'equivocar-se (ordre, opacitat, màscara, mode). **La
composició es queda a fora, i Photoshop rep el `g = N/D` acabat**, en 32 bits de
coma flotant, amb `N` i `D` al costat com a rebut per si algú vol refer-ho.

Això no treu res a Photoshop: **la fase 3 i la composició de capes visuals sí que
hi són**, i allà la seva composició alfa no fa cap mal perquè el que s'hi
barreja ja no és una mesura sinó contrast.

## 19 · L'eix òptic: mesurable a la Sony, no a la Vixen

L'última de les «tres coses barates» del traspàs. `research/98` deia que l'eix no
és identificable perquè **un desplaçament d'eix i un pla additiu són degenerats**,
i ho demostrava amb un màxim absolut de 5,55·10⁻¹⁷. ⚠️ Però aquella degeneració
és exacta **només per al model quadràtic**: un vinyetatge real no és una
paràbola. Amb un **perfil radial lliure** —una funció qualsevol de r— la
degeneració es trenca, i llavors la pregunta és si el mínim existeix de veritat.

Mètode: per a cada eix de prova, mediana per anell + pla ajustat alternadament, i
es mira la **dispersió** del que queda. L'eix bo és el que la minimitza.

| | Vixen VSD90SS | Sony 300 GM |
|---|---:|---:|
| dispersió al centre geomètric | 0,006613 | 0,004619 |
| dispersió a l'òptim | 0,006133 | **0,002174** |
| baixada | **7,3 %** | **52,9 %** |
| pla ajustat | 6,22 % del camp | 2,41 % |
| eix trobat | 1585 px (68,3 % del semieix) | **106 px = 5,7 ′ = 4,0 %** |
| **moure l'eix 100 px puja la dispersió** | **0,3 %** | **99,2 %** |

### Sony: mesurat

L'eix òptic del 300 GM és a **(+60, +88) px** del centre del sensor, o sigui
**106 px = 5,7 ′**. El mínim és fort —moure'l 100 px dobla la dispersió— i la
dispersió residual cau a la meitat. És un descentrament d'objectiu perfectament
normal.

### Vixen: no es pot, i se sap per què

⛔ **La funció objectiu és plana**: moure l'eix 100 px la puja un **0,3 %**. El
«mínim» a 1585 px no vol dir res —seria el 68 % del semieix curt, impossible per
a un eix òptic— i el que hi ha és soroll.

I el motiu és mesurable: **el vinyetatge de la Vixen és molt poc profund**. El
seu flat radial val **9,2 % del centre a la cantonada** i només **4,97 % dins el
domini de la corona**, mentre que el màster 2-D porta un **pla del 6,22 %** —el
mateix que `research/90` li va posar en quarantena—. Amb el senyal i el
contaminant de la mateixa mida, no hi ha res a localitzar.

### El que això tanca

- el `research/98` tenia raó en el fons —l'eix de la Vixen no és identificable—
  però el seu argument (la degeneració quadràtica) **no era el motiu**: el motiu
  és que **el vinyetatge és massa pla per a l'error que porta el màster**;
- i és coherent amb tot el que el pilot ha trobat: el flat de la Vixen és petit
  (4,97 %), el seu efecte sobre l'acord entre trens és d'**1,7 %** (§10), i
  **cap dada disponible no pot decidir si és bo**. S'aplica declarat i prou;
- ⛔ **el que NO s'ha de fer és insistir**: la manera de resoldre-ho no és més
  anàlisi d'aquestes imatges sinó un flat nou amb el cos **girat 180°**, que
  separa el que és del sensor del que és de l'òptica. `research/90` ja té el
  producte `MASTER_OPTICAL_EVEN180` preparat per a això.

Rebut: `output/pilot_vixen_claude_20260823/eix_optic.json`.

## 20 · L'earthshine: el pedestal que es declarava indeterminat és el cel, i val el 85 %

El pilot va excloure l'earthshine a propòsit, i el producte `Earthshine_FINAL`
—Sony 2×8 s, `DSC06987` + `DSC06993`, amb model físic de halo, validat contra
l'albedo LROC WAC amb r = 0,68 fora de mostra— ja existeix i **no s'ha tocat**.
El que aquí s'aporta és una mesura que aquell producte no podia fer i el pilot sí.

### El que el producte declara

> «Fotometria absoluta: **NO** (pedestal de halo/cel **degenerat amb una
> constant**).»

És honest i és cert **amb dos fotogrames**: entre t = 34 s i t = 67 s el cel
només varia un 4 %, o sigui que no hi ha palanca per separar-lo. Però el pilot no
necessita que sigui degenerat: **el cel ja està mesurat** (§13 i §14), amb la
seva forma temporal, la seva forma espacial i el seu color.

### La mesura

Aplicant el model de cel de la Sony als dos mateixos fotogrames, dins el disc
lunar a 0,2–0,7 R_lluna:

| fotograma | t | mesurat (B/B☉) | cel del model | earthshine + halo | **cel/total** |
|---|---:|---:|---:|---:|---:|
| DSC06987 | 34 s | 1,521·10⁻⁸ | 1,281·10⁻⁸ | 2,40·10⁻⁹ | **84,2 %** |
| DSC06993 | 67 s | 1,444·10⁻⁸ | 1,244·10⁻⁸ | 2,00·10⁻⁹ | **86,2 %** |

⚠️ **Dins el disc lunar, el cel és el 85 % del que es mesura.** El pedestal que
el producte no podia separar **no era una constant qualsevol: era el cel de la
totalitat**, i ara està mesurat.

El que en queda —2,0 a 2,4·10⁻⁹ B/B☉— és earthshine **més halo**, i els dos
fotogrames hi discrepen un **17 %**, cosa coherent amb un halo que depèn de la
posició de la corona i amb l'error propi del model.

### Dues coses més que l'auditoria destapa

⚠️ **L'escala del producte és la nominal, no la mesurada.** Diu 3,234 ″/px, que
és el `scale_ref` de `final_solution`; el valor **mesurat** és **3,2019914**, un
**1,0 %** menys. És la mateixa classe d'error que el R☉ mitjà del §0 ter.

⚠️ **I el radi lunar també.** El producte fixa la Lluna a **R = 302 px**;
l'efemèride, a l'escala mesurada, en dona **305,8**: un **1,2 %**. Sobre una
comparació amb un mapa d'albedo LROC, un 1 % d'escala és una cosa que la
correlació nota.

### El que això mana, si algú reprèn l'earthshine

⛔ **No refer el producte sense demanar-ho**: el `Earthshine_FINAL` va sortir de
portes acordades (`research/72` §5-6) i no és meu. El que hi ha per fer, si es
reprèn, és curt i està tot al pilot:

1. **restar el model de cel** dels dos fotogrames de 8 s abans d'ajustar el halo
   —el 85 % del senyal se'n va, i el que quedi per ajustar és halo de veritat—;
2. **passar a l'escala mesurada** (3,2019914 ″/px) i al radi lunar
   d'**efemèride** (305,8 px), no al mesurat: §0 ter i §9 diuen per què el limbe
   mesurat està biaixat;
3. i llavors **la fotometria absoluta deixa de ser impossible**: el que queda
   degenerat és el halo, no el cel.

## 21 · Inventari d'impacte: què de la branca antiga porta els valors vells

Les correccions del pilot no s'han propagat enlloc, i **no s'han de propagar a
cegues**: refer un producte acceptat és una decisió de Pere, no meva. El que sí
que es pot fer, i és el que falta, és dir **exactament** qui porta què i quant
costa.

### L'escala d'exposició

`hdr_corona_vixen.py` —l'eina que va fer el `manifest.csv` i els màsters S6
acceptats— declara `EXP_REAL = {0.0003125: 1/3200, 10.0: 10.3}` i deixa la resta
al nominal del menú. Contra el físic del MakerNote:

| nominal | branca antiga | físic | error |
|---|---:|---:|---:|
| 1/3200 | 1/3200 | 1/3251 | **+1,59 %** |
| 1/2000 … 1/125 (5 esglaons) | el nominal | 1/2048 … 1/128 | **+2,40 %** |
| **1/60 · 1/30 · 1/15** | el nominal | 1/64 · 1/32 · 1/16 | **+6,67 %** |
| 1/8 · 1/4 · 1/2 · 1 · 2 s | exactes | exactes | 0,00 % |
| «10,3 s» | 10,3 | **10,0793684** | **+2,19 %** |

**Deu dels quinze esglaons van per damunt de l'1 %**, i el pitjor per +6,67 %.
⚠️ I el `10,0 → 10,3` que la branca antiga sí que corregeix **va en direcció
contrària**: el físic és 10,079, o sigui que la correcció allarga l'exposició un
2,19 % de més.

Mesurat al compost del pilot, fer servir l'escala antiga en lloc de la física
biaixa la fotometria **−3,10 % a 1,10 R☉** i **−1,7 % constant** per damunt de
3 R☉ — o sigui un **gradient radial d'1,4 % inventat** entre 1,1 i 3 R☉.

### El radi solar

| | valor | R☉ en px |
|---|---:|---:|
| `hdr_corona_vixen.py`, `filtres_druckmuller/comu.py`, `prepara_lluminancia*.py` | 959,0 ″ (mitjà) | 446,15 |
| el del dia, verificat contra DE421 | **947,068 ″** | **440,60** |

Un radi que la branca antiga anomena **X R☉** val **1,0126·X** amb el valor bo.
`research/96` ja ho havia detectat; el codi encara no.

### Qui està net i qui no

| eina o producte | escala d'exposició | R☉ | escala Sony |
|---|---|---|---|
| `pilot_vixen_claude/` | ✅ física | ✅ 947,068 | ✅ 3,2019914 |
| `llenc_prova_dos_trens/munta.py` | — | ✅ 947,068 | ✅ mesurada |
| `astrometria/comu.py` | — | ✅ 947,07 | ✅ coneix les dues |
| `hdr_corona_vixen.py` | ⛔ nominal | ⛔ 959,0 | — |
| `filtres_druckmuller/comu.py` | — | ⛔ 959,0 | ✅ 3,2020 |
| `prepara_lluminancia*.py` | — | ⛔ 959,0 | ✅ 3,2020 |
| `Earthshine_FINAL` | ✅ (8 s és exacte) | — | ⛔ 3,234 |
| màsters S6 acceptats i tot el que en penja | ⛔ nominal | ⛔ 959,0 | — |

### Què en faria jo, i què no

⛔ **No tocaria el codi de la branca antiga sense que Pere ho digui.** Els
màsters S6 estan acceptats amb rebut, i `CapesTotals`, els projectes de
Photoshop i els filtres hi pengen: refer-los és una cadena llarga.

El que sí que és barat i val la pena, per ordre:

1. **Escriure la conversió** allà on es citin radis: qualsevol «X R☉» de
   `research/76`–`96` és **1,0126·X** en la convenció del pilot. Sense això, les
   xifres dels dos costats no es poden comparar i ja s'han comparat.
2. **Corregir `EXP_REAL`** a `hdr_corona_vixen.py` si algun dia es torna a
   generar un manifest: són tres línies i evita un gradient radial d'1,4 %.
3. **Deixar els productes acceptats com estan** i declarar-hi el biaix, que és
   el que aquesta secció fa.

## 22 · Com posar això al projecte de Photoshop, i una verificació que no buscava

El pilot ha fet els seus productes al seu llenç. El projecte de Photoshop de
Pere en té un altre —**7648 × 5353 amb el Sol a (4021,35 · 2737,90)**—, i sense
la transformació els productes del pilot no serveixen de res allà.

### La resposta és curta

El compost del pilot viu a la **reixa del sensor de la Vixen amb el Sol al
centre** (6958 × 4638, Sol a 3479 · 2319), que és exactament on vivia el compost
antic. O sigui que hi entra amb **el mateix desplaçament de sempre**:

    +542,35 columnes · +418,90 files

⛔ **I no s'ha de girar res.** El llenç de Photoshop és en orientació de sensor
(PA 57,19°), no nord amunt; el `LLENC_COMU_BBsol_float32.tif` del pilot **sí que
és nord amunt** i no és el que hi va. El que hi va és el `HDR_adu_s.npy` (o el
seu TIFF), sense rotació.

### La verificació que no buscava

Correlació de fase entre el compost del pilot i el compost antic
(`hdr_vixen_countss.npy`), sobre l'estructura fina de la corona i en quatre
retalls de 768 px repartits:

| retall | desplaçament | resposta |
|---|---:|---:|
| nord | (+0,005 · −0,005) px | 0,9983 |
| sud | (+0,009 · −0,006) px | 0,9966 |
| oest | (+0,005 · −0,002) px | 0,9981 |
| est | (+0,003 · −0,005) px | 0,9979 |

**Mitjana: 0,007 px.** Els dos composts comparteixen origen astromètric a set
mil·lèsimes de píxel.

⛔ **I això és una verificació independent del §9.** La §1 havia adoptat el
centre del **limbe mesurat**, que és 3,65 px lluny del de l'efemèride; el §9 ho
va rectificar i el compost canònic va tornar al de l'efemèride —que és el que
el manifest porta i el que el pipeline antic sempre havia fet servir—. Si la
rectificació hagués anat en la direcció equivocada, aquesta correlació donaria
**3,65 px**. Dona **0,007**.

### Què canvia respecte del compost antic

Mateixa geometria, i la fotometria es mou poc:

| R☉ | pilot / antic |
|---|---:|
| 1,22 | **+1,42 %** |
| 1,61 | +0,38 % |
| 2,40 | +0,48 % |
| 3,19 | **+0,07 %** |
| 4,77 | +0,81 % |

Mediana **+0,42 %**, de +0,07 a +1,42 %. És el net de totes les correccions
—escala d'exposició física, flat radial, anivellament—, i és petit i llis: **cap
capa de Photoshop existent no es desalinea ni canvia de to de manera visible**
si se substitueix la base per la del pilot.

⚠️ El que sí que canvia són **els radis**: el pilot els compta amb R☉ = 440,60 px
i el projecte de Photoshop amb 446,15 (§21). ⛔ Però **això no vol dir tocar cap
màscara**: el §23 separa els tres casos i diu que les màscares existents estan
bé —el que està malament és la seva etiqueta— i que on fa mal de veritat és a
qualsevol **comparació fotomètrica amb un model o un altre instrument**, on el
sistemàtic puja al **6–9 %**.

## 23 · El canvi de R☉: què es mou, què no, i on fa mal de veritat

El §21 i el §22 avisen que els radis de les dues branques difereixen un 1,26 %.
Aquell avís, tal com estava, era massa gruixut per fer-hi res. Aquí està separat
en els tres casos, que no es comporten igual.

### A · Una màscara ja posada NO s'ha de moure

Pere va posar les màscares mirant la imatge. Estan on ell les volia; el que està
malament és **l'etiqueta**, no la posició:

| l'eina en diu | és a (px) | de veritat és |
|---|---:|---:|
| 1,2 R☉ | 535,4 | **1,215 R☉** |
| 3,0 R☉ | 1338,5 | **3,038 R☉** |
| 4,5 R☉ | 2007,7 | **4,557 R☉** |
| 5,5 R☉ | 2453,8 | **5,569 R☉** |
| 8,0 R☉ | 3569,2 | **8,101 R☉** |

⛔ **No s'ha de tocar cap màscara existent.** Moure-les seria desfer una decisió
visual que ja estava presa bé.

### B · Recalcular-la d'un número sí que la mou

Si algú regenera una màscara escrivint «4,5 R☉» amb el R☉ correcte, l'aresta es
desplaça:

| radi | desplaçament |
|---|---:|
| 1,2 R☉ | −6,7 px |
| 3,0 R☉ | −16,7 px |
| 4,5 R☉ | −25,0 px |
| 5,5 R☉ | −30,5 px |
| 8,0 R☉ | −44,4 px |

Trenta píxels a l'aresta d'una màscara de transició es veuen. **Qui regeneri una
capa ha de decidir si vol l'etiqueta o la posició**, i normalment voldrà la
posició: llavors ha de multiplicar el número per **1,0126**.

### C · I comparar fotometria amb un model o un altre instrument sí que és un error

Aquest és el cas que fa mal, i és més gros del que sembla, perquè **la corona
és molt costeruda**. Un error d'1,26 % en el radi es converteix en un error de
brillantor que val el pendent local vegades això:

| R☉ | pendent local | error en brillantor |
|---|---:|---:|
| 1,6 | −6,78 | **8,9 %** |
| 2,0 | −5,69 | **7,4 %** |
| 2,5 | −4,48 | 5,8 % |
| 3,0 | −4,54 | 5,9 % |
| 3,8 | −7,17 | **9,4 %** |

⛔ **Qualsevol comparació de la fotometria radial del projecte contra Baumbach,
LASCO C2, K-Cor o l'altre tren, feta amb la convenció de 959 ″, porta un
sistemàtic del 6 al 9 %** que no ve de la fotometria sinó de l'etiqueta del
radi.

⚠️ I això és **del mateix ordre que el ±14 % de l'escala absoluta** (§15). O
sigui que no es pot ignorar: qui vulgui comparar amb un instrument extern ha de
posar el R☉ del dia abans de fer-ho, i no és una correcció cosmètica.

## 7 · El que queda obert

1. **La fotometria es declara fins a 3,2 R☉, i el §12 diu per què amb número**:
   de 3,7 R☉ enfora la corona és **com a molt el 3,9 %** del que es mesura. El
   cel es pot restar fotograma a fotograma per la seva signatura temporal, però
   la seva part **constant** no la veu cap de les dues vies: cal una segona
   palanca (una altra latitud dins l'ombra, un model d'ombra, o una referència
   nocturna).
2. **El flat radial continua sense validació pròpia** i s'aplica declarat. La
   mesura de l'eix òptic continua pendent, i la degeneració que `research/98`
   descriu és exacta **només per al model quadràtic**: amb el perfil radial
   sencer es podria trencar — i el §19 ho ha provat: **es trenca, però només
   serveix a la Sony**. L'eix del 300 GM surt a 106 px (5,7 ′) amb un mínim
   fort; el de la Vixen **no es pot mesurar** perquè el seu vinyetatge (4,97 %)
   és més pla que el pla que el màster 2-D porta (6,22 %). Les «tres coses
   barates» del traspàs queden totes tres tancades.
3. **Els dos trens hi són (§8), la discrepància està descomposta (§10) i
   explicada (§11)**: el compost és corona **més cel**, el cel iguala la corona
   a **2,41 R☉**, i els dos trens discrepen **1,1384 sobre la corona i 1,0824
   sobre el cel**. Barrejar-los dona la tendència observada. ⛔ El que ara mana
   és **restar el cel**, no anivellar-lo, i **no fusionar sense separar-lo
   abans**: el factor que iguala els trens no és un, són dos.
4. **La fase 3 està feta (§16)** amb l'ACHF de Brno, la seva convolució
   incompleta i una porta de soroll calculada de la variància pròpia del
   compost; quatre portes PASS sobre el 95,5 % del rectangle. El que no s'ha
   fet és **composar-la amb res**: és contrast relatiu, no fotometria.
5. **L'earthshine queda fora del pilot**, com mana el traspàs, però el §20 hi
   aporta la mesura que li faltava: **dins el disc lunar el cel és el 85 % del
   senyal**, i amb el model de cel del pilot el pedestal que `Earthshine_FINAL`
   declarava indeterminat deixa de ser-ho. ⛔ El producte no s'ha tocat.

Cap RAW, dark, flat, PSB/TIFF històric ni producte S6 s'ha modificat. Cap
càmera, PTP, `gphoto2`, GUI ni Photoshop.
