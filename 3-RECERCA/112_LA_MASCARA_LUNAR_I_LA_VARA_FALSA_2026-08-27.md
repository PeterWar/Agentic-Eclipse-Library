# 112 · La màscara lunar per fotograma, i una vara falsa que amagava la corona interior

**Data:** 27 d'agost de 2026, matinada. **Pregunta de Pere:** «entenc que just a
la corona interior al costat del borde lunar les imatges NO ensenyen res perquè
és la part on hi ha moviment, correcte?» I després: «implementa-ho, important
acostar-nos al màxim al limbe lunar i recuperar qualsevol tall de corona».

---

## 1. La resposta a la pregunta, i per què el mecanisme va al revés

El llenç està centrat al **Sol** per efemèride. Per tant **la corona no es mou:
la que llisca és la Lluna**, i ho fa **61,5″ = 28,6 px = 0,0650 R☉** al llarg
de la totalitat (0,585 ″/s topocèntric × 105,2 s).

⚠️ I **no és un anell**: és una translació, o sigui **dos creixents**. L'amplada
escombrada val 28,6 px en la direcció del moviment, 14,3 px a 60° i **zero** a
90°.

| regió | radi |
|---|---|
| sempre tapada (intersecció dels discos) | fins a **1,0014 R☉** |
| escombrada (recuperable fotograma a fotograma) | 1,0014 – 1,0663 R☉ |
| mai tapada (unió) | des de **1,0663 R☉** |

⛔ **I el defecte que la pregunta va destapar: `f2` no emmascarava la Lluna a
cap fotograma.** Dins d'aquells creixents, el compost feia la mitjana de píxels
que a uns fotogrames eren corona i a altres eren **Lluna fosca**, i el biaix
queia justament on la corona és més brillant.

## 2. La cura: `w = 0` al disc lunar de CADA fotograma

És el que fa Brno (`w = −1`). El vector Lluna−Sol de cada fotograma **ja el
desava `f1`** (`lluna_dx`, `lluna_dy`, per efemèride a l'instant **mig** de
l'exposició), o sigui que no calia mesurar res de nou. Guarda de 2 px per la
PSF del limbe i vora suau de 2 px.

**Resultat** (contra el run anterior, mateixa dada):

| r (R☉) | cobertura | corona G, quocient nou/vell |
|---|---:|---:|
| 1,030 | 87,6 % | **×6,54** |
| 1,040 | 97,1 % | **×2,11** |
| 1,050 | 100 % | ×1,10 |
| ≥1,070 | 100 % | **0,995 – 1,006** |

⏭️ **De 1,07 cap enfora els dos runs són idèntics**: la màscara no toca res que
no hagi de tocar, i tot el que canvia és el creixent recuperat.

## 3. ⛔ Però la màscara va destrossar la coherència, i és una lliçó general

Primer intent: el compost sortia **49 vegades massa brillant** a partir de
2 R☉, amb guanys de coherència de fins a **206** i dispersió del **2488 %**
(abans 0,86–1,14 i 8,3 %).

**Causa.** La màscara es va posar a `compon` i **no** a `coherencia`. Aquesta
ajusta el guany de cada fotograma amb la mediana de `compost / fotograma`
sobre els píxels brillants. Amb la màscara només a una banda, `ref` és la
corona de veritat i `a` és la Lluna fosca d'aquell fotograma: **el quocient es
dispara**.

⏭️ **La regla, i és general:** qualsevol màscara nova que canviï QUINS píxels
entren al compost s'ha d'aplicar **idènticament a tots els llocs que comparen
un fotograma amb el compost**. La manera de garantir-ho és **una sola funció
compartida** (`f2.mascara_lluna`), no una còpia a cada lloc.

⏭️ **Porta nova F2.2**: cap guany fora de `[1/2, 2]`. La transparència va caure
un 8 % en tota la totalitat, o sigui que cap fotograma no en pot demanar el
doble. ⚠️ **El rebut ja deia «dispersió 2488 %» i ningú no ho mirava: un número
al rebut sense porta és documentació, no control.**

Amb la màscara als dos llocs: **k mediana 1,0095, dispersió 6,67 %** —
*millor* que el 8,28 % d'abans, perquè l'ajust ja no es contamina.

## 4. ⛔ I una vara falsa, més vella que tot això

Fins ara, «on hi ha dada» es decidia amb `den > 0,02 × màxim GLOBAL del pes`.

**El màxim global era DINS DE LA LLUNA** (mesurat: r = **1,020 R☉**), perquè
els píxels foscos del disc lunar no saturen i reben pes ple de **tots** els
fotogrames. I prop del limbe només hi contribueixen les exposicions **curtes**
—la resta hi està saturada—, o sigui que el pes hi cau **dos ordres de
magnitud de manera legítima**.

Conseqüència: a **1,05 R☉ el llindar deixava fora el 75 % de l'anell**, i amb
la Lluna emmascarada (que treu el màxim fals) se n'hauria menjat encara més.

**La cura**: `comu.mascara_dada` compara el pes amb el que és **assolible al
MATEIX RADI** (percentil 99 per calaix de radi, suavitzat).

| r (R☉) | llindar global | **per radi** |
|---|---:|---:|
| 1,020 | 0,0 % | **46,0 %** |
| 1,030 | 1,8 % | **72,4 %** |
| 1,050 | 24,7 % | **99,5 %** |
| 1,070 | 65,3 % | **100 %** |
| 6 / 7 / 8 / 9 | 68,5 / 54,3 / 36,9 / 8,2 % | **idèntic** |

⏭️ **El radi més petit amb dada passa de 1,0330 a 1,0133 R☉**, i el camp
exterior no es mou ni una dècima: la vara nova no obre la porta als cantons del
rectangle.

## 5. El que queda declarat

- La regió **realment** sense dada és la intersecció dels discos lunars, i és
  un **lune**, no un cercle — la mateixa figura que Druckmüller declara al seu
  compost de 800 mm.
- Entre 1,013 i 1,05 R☉ la cobertura és **parcial** (46–99 %): hi ha corona,
  però de menys fotogrames i per tant més sorollosa. Va declarat al rebut.
- La guarda del detall baixa de **1,045 a 1,010 R☉**.


## 6. El resultat final, mesurat

`VIXEN_CIENCIA_20260826T233701Z`, contra el lliurament del 26 al vespre:

| r (R☉) | cobertura | corona G, quocient |
|---|---:|---:|
| 1,015 | 15,6 % | **×80,1** |
| 1,020 | 43,7 % | **×47,1** |
| 1,030 | 71,5 % | **×19,2** |
| 1,040 | 89,0 % | **×5,91** |
| 1,050 | 99,4 % | ×1,73 |
| 1,100 | 100 % | ×1,05 |
| 5,000 | 100 % | **0,996** |

**Radi més petit amb corona: 1,0133 R☉.** El camp exterior no es mou.

⏭️ **Porta H1 final**: pitjor 0,0167 (llindar 0,05), PASSA. Els quatre filtres:
MGN 0,114 → 0,017 · NRGF 0,096 → 0,001 · passa-alt 0,468 → 0,008 · radial
0,009 → 0,001.

⚠️ **Va caldre pujar la resolució de l'anivellament.** Amb la corona interior
recuperada, el nivell del passa-alt cau de **0,931 a 1,07 R☉ a 0,331 a 1,15**:
amb 600 calaixos i nucli σ=4 el resultat es quedava a **0,067 i no passava**;
amb **1200 i σ=3** cau a **0,008**. Dues iteracions abans havia provat de moure
la màscara del detall i **només movia l'artefacte de lloc** (el «abans» pujava
de 0,358 a 0,475): la vora dura no era la causa, era la resolució.

## 7. ⚠️ El preu: la Lluna es queda negra

La màscara lunar treu el disc de **tots** els fotogrames, o sigui que
l'**earthshine desapareix del compost de corona**. És correcte —el que hi
havia abans era earthshine contaminant la corona—, però l'earthshine és un dels
tres objectius científics del projecte.

⏭️ **La cura és una pila SEPARADA**, amb la màscara **inversa** (només dins del
disc lunar) i registrada **a la Lluna**, no al Sol. `CLAUDE.md` §1 ter ja ho
declarava: «entre la primera àncora i la quarta la Lluna es desplaça 28″ = 9 px
respecte de la corona: la pila d'earthshine i la de corona **no poden compartir
alineació**». Queda pendent.
