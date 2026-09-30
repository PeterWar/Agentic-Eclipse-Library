# 111 · Els anells dels filtres: tres mecanismes, tots funció només del radi

**Data:** 26 d'agost de 2026, nit. **Marcat per Pere** sobre el
`LLIURAMENT_x8.png` del `VIXEN_CIENCIA`: «els filtres tenen artefactes
circulars (tema recurrent)».

⚠️ Les marques lila **no van arribar al disc** (el fitxer hi té zero píxels
lila). Els artefactes es van trobar i mesurar **sense elles**, i queda pendent
de contrastar-ho amb el que Pere havia marcat.

---

## 1. La mesura que ho identifica: el NIVELL per radi

En **Superposar**, un nivell diferent de 0,5 **enfosqueix o aclareix un anell
sencer**. Aquesta és la mètrica, i no la de l'amplitud contra la dispersió que
`research/100` feia servir —aquella s'enganya quan l'atenuació ensorra la
dispersió exterior i el quocient es dispara.

Mediana azimutal del detall, per radi (`VIXEN_CIENCIA_20260826T153314Z`):

| filtre | 1,2 | 1,6 | 2,0 | 2,5 | 3,0 | 4,0 | 5,0 | màx \|niv−0,5\| |
|---|---|---|---|---|---|---|---|---|
| passa-alt | 0,519 | 0,452 | 0,446 | 0,479 | 0,495 | 0,514 | 0,533 | 0,126 |
| radial | 0,523 | 0,513 | 0,480 | 0,479 | 0,490 | 0,502 | 0,514 | **0,033** ✓ |
| **NRGF** | 0,520 | 0,267 | **0,249** | 0,335 | 0,363 | 0,410 | 0,451 | **0,263** ⛔ |
| **MGN** | **0,681** | 0,414 | **0,268** | 0,341 | 0,454 | **0,555** | 0,546 | **0,248** ⛔ |

L'NRGF a **0,249 a 2 R☉** és el **bol fosc** del seu panell. L'MGN fa **anell
clar → fosc → clar**. El filtre radial ja era net perquè per construcció resta
una mitjana azimutal.

## 2. Tres causes, i l'ordre en què s'han d'arreglar importa

⛔ **(a) Del 8 al 12 % dels píxels estaven RETALLATS a 0 o a 1.** Un píxel
retallat no té estructura: és un pegat pla. La causa és que la σ de pantalla es
mesurava **després** d'atenuar, o sigui que **l'atenuació es realimentava al
guany**: com més s'atenuava, més s'amplificava. Amb la σ mesurada **abans** i
compressió **`tanh`** en lloc de retall dur, el retallat passa de **8,29 % a
0,37 %**, i amb la Lluna fora, a **0,03 %**.

⛔ **(b) El nivell per radi no s'anivellava enlloc.** La cura és la mediana
azimutal per calaix de **log r**, pesada per cobertura i suavitzada, iterada
(H1 de `research/100`).
⚠️ **Sobre dades RETALLADES no funciona**: la massa retallada no es mou, la
mediana no segueix el desplaçament i la cura **divergeix** —mesurat: el
passa-alt anava de 0,126 a **0,346**—. Per això (a) va **abans** que (b).

⛔ **(c) Els filtres travessaven el limbe lunar.** El nivell del passa-alt es
disparava a **r < 1,02 R☉**, o sigui **DINS de la Lluna**: allà hi ha un esglaó
de diversos ordres de magnitud i el desenfoc de `suau_mask` s'hi calcula amb el
forat a dins —una mostra d'un sol costat—, o sigui que el residu es dispara i
surt un **anell saturat que abraça la Lluna** (el passa-alt hi valia exactament
**1,000**). És el mateix parany que el `distanceTransform` sobre un mapa de
cobertura amb el forat de la Lluna.
⚠️ **Excloure la Lluna NO és violar la norma del rectangle**: la norma prohibeix
retallar el camp EXTERIOR a una circumferència. La Lluna **és** un cercle, i no
és corona. La màscara de detall és `r > 1,045 R☉` i deixa el **97,9 %** de la
dada.

I una quarta cosa que no és un defecte sinó una lliçó: el **passa-alt i l'MGN
es fan ara sobre el camp APLANAT en radi** (`lg − perfil_azimutal(lg)`), perquè
si no el pendent radial del limbe satura qualsevol passa-alt.

## 3. El resultat

| filtre | retallats abans | després | nivell abans | després |
|---|---:|---:|---:|---:|
| passa-alt | 8,29 % | **0,03 %** | 0,126 | **0,012** |
| NRGF | 12,14 % | **0,001 %** | 0,263 | **0,021** |
| MGN | 10,42 % | **0,000 %** | 0,248 | **0,030** |

⏭️ **Porta H1 nova**: `max |nivell de l'anell − 0,5| ≤ 0,05` als anells sencers
amb estructura. Falla tancat.

⚠️ **La resolució de l'anivellament importa**: amb 300 calaixos i nucli σ=5 el
passa-alt es quedava a **0,097 i NO passava**; amb **600 calaixos i σ=4** cau a
**0,012**. El nucli massa ample no pot seguir una vora estreta en radi.

## 4. El que continua sent radial i es declara

L'**atenuació per senyal/soroll** és, per construcció, gairebé una funció del
radi: baixa de 0,9 a **3,74 R☉** i de 0,5 a **5,05 R☉**. No es treu —mostrar
detall on no hi ha senyal és pitjor—, però **després de l'anivellament no pot
deixar cap nivell**: el que queda és una pèrdua de **contrast** cap enfora, que
és honesta i va declarada al rebut.
