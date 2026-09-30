# Escales noves de l'A7RIIIA i la R6 — ACCEPTADES, no implementades

9 d'agost de 2026, nit. Disseny d'escala d'exposicions nou per a l'A7RIIIA,
**acceptat per Pere** al final d'una sessió de disseny iterativa. Substitueix,
quan s'implementi, la geometria d'exposicions del disseny de blocs actual.

## Estat

> ✅ **IMPLEMENTAT a la V1.00, el 10 d'agost de 2026.** Aquest document deixa
> de ser un disseny pendent i passa a ser el **perquè** de l'escala viva. El
> **què** exacte —constants, llindars reals i les tres coses que aquí no
> estaven previstes— és a `CLAUDE.md` §3 «El que canvia la V1.00».

Diferències entre el que aquí es va dimensionar i el que el compilador
produeix, totes a favor:

| | Aquest document | V1.00 |
|---|---|---|
| Llindars de tríada (Sony) | 70 / 83,3 / 89,5 s | **69,8 / 81,9 / 87,7 s** |
| Marge davant del bloc de C3 a 91 s | +1,46 s | **+4,29 s** |
| Finestra de C3 de la R6 | C3+24 | **C3+20** (mana el traspàs) |
| Obturació de contacte de la R6 | no s'hi tractava | **1/3200** (mana el traspàs) |

Els llindars i el marge surten de la separació entre accions: aquí es va fer
servir un padding de 0,45 s i el compilador empaqueta a 0,25.

⚠️ **Tres coses que aquest document no havia previst i que van caldre:**

1. **El bloc fosc de la R6 no cap per sota de 72,4 s.** Deixar-lo caure treia
   tot l'earthshine d'aquest cos de 60 a 72 s. Es retalla a 2+2 fotogrames i,
   si calgués, a 1+1; una **escala** continua sense retallar-se mai.
2. **La finestra de C3 s'havia d'acotar per C4.** Amb un C3−C4 d'assaig de
   dotze segons, C3+20 xocava amb la quietud de C4 i el compilador refusava el
   programa. Ara s'escurça sola fins al valor històric de 4 s.
3. **Per damunt d'uns 120 s de totalitat la muntanya no pot cobrir-la.** Amb
   sis disparaments i el sostre de cua ple, el forat màxim arriba a 65 s a
   l'A7RIIIA i 74 a l'A7III, per damunt dels 40 de sempre. Es declara
   (`A7R3A_BLOCS_TOTALITY_MAX_GAP_S`) en lloc de deixar caure el cos al tram
   genèric, que hi posaria 36 imatges i perdria els anells de C3 en silenci.
   Al rang exigit de 60 a 110 s el forat real no passa de 30 s.

## El disseny

Contactes a **base 1/800** i una muntanya de base al mig: puja a 1/4, es queda
a 1 s per a l'earthshine, i torna a baixar per 1/4 abans de tornar als
contactes.

**Modalitat triada per Pere: 3+3** — tres tríades de base 1 s i tres de base
1/4.

```text
C2 −3,35 / −0,45 / +2,45   base 1/800   1/6400 · 1/800 · 1/100
C2 +12,10                  base 1/4     1/30 · 1/4 · 2 s
C2 +25,36 / +37,36 / +49,36   base 1 s   1/8 · 1 s · 8 s
C2 +68,02 / +74,28         base 1/4     1/30 · 1/4 · 2 s
C2 (C3−2,45) / (C3+1,45)   base 1/800   1/6400 · 1/800 · 1/100
```

Escala resultant, a f/2,8 ISO 100 — **nou esglaons, 15,64 EV**:

| Esglaó | 1/6400 | 1/800 | 1/100 | 1/30 | 1/8 | 1/4 | 1 s | 2 s | 8 s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Fotogrames | 5 | 5 | 5 | 3 | 3 | 3 | 3 | 3 | 3 |
| Salt fins al següent | 3,00 | 3,00 | 1,74 | 1,91 | 1,00 | 2,00 | 1,00 | 2,00 | — |

**Tres subfotogrames a cada esglaó de mig eclipsi**, que és el que Pere buscava
i el que fa la modalitat regular: cap nivell queda amb una sola mostra.

Els dos salts de 3,00 EV són **interns a la tríada de contacte** i no es poden
tocar: són el mateix disparament. De 1/100 cap amunt el salt màxim és 2,00 EV.

Avui aquest cos té **sis** esglaons amb salts de 3,00, i **només tres a mig
eclipsi** (1/8 · 1 s · 8 s), perquè la tríada de contacte només existeix als
contactes.

## La branca per durada — el matís que Pere vol constatat

**Pere pot no saber la durada de la totalitat fins una hora abans.** El nombre
de tríades de base 1/4 que hi caben depèn de la durada, i el llindar és nítid:

| Totalitat | Configuració | Imatges | Earthshine |
|---|---|---:|---:|
| **≥ 89,5 s** | 3 àncores + **3 tríades** de 1/4 — la triada | **33** | 24 s |
| 83,3 – 89,5 s | 3 àncores + **2 tríades** de 1/4 | 30 | 24 s |
| 70,0 – 83,3 s | 3 àncores + **1 tríada** de 1/4 | 27 | 24 s |
| < 70,0 s | cap tríada de 1/4; cau al disseny d'avui | — | — |

O sigui que **la tercera tríada de 1/4 apareix a 89,5 s**, just per sota d'1 min
30 s. Cada esglaó del llindar val una tríada, i sempre és la de base 1/4: les
tres àncores no es toquen mai en aquesta família.

⚠️ **89,5 s és on hi CAP, no on va còmode.** La distància entre el final de
l'últim canvi de base i el bloc de contacte de C3, que és el marge que protegeix
l'objectiu 2:

| Totalitat | Marge amb el pressupost de 6,55 s | Amb el cost mesurat de 5,30 s |
|---|---:|---:|
| 89,5 s | **−0,04 s** | +1,21 s |
| 90,0 s | +0,46 s | +1,71 s |
| **91,0 s — terra de planificació** | **+1,46 s** | **+2,71 s** |
| 93,0 s | +3,46 s | +4,71 s |
| 95,0 s | +5,46 s | +6,71 s |
| 100,0 s | +10,46 s | +11,71 s |
| *disseny d'avui, a 108,8 s* | *+3,60 s* | *+4,85 s* |

**El terra de planificació és 91,0 s**: decisió de Pere del 9 d'agost, perquè
és la durada al punt d'observació previst —l'hotel—. Amb aquest terra la
modalitat 3+3 hi cap sempre, i el marge no queda al límit: perquè el bloc de
contacte de C3 arribés tard, el canvi de base hauria de durar més de **8,01 s**,
un **51 %** per damunt del cost mesurat i un **22 %** per damunt del pressupost.

⚠️ **El calendari d'aquest document té 0,45 s de separació entre accions, i
això és padding meu, no cap constant del projecte.** Són nou separacions,
4,05 s en total. Si el compilador les empaqueta a 0,20 s, el marge a 91 s passa
de +2,71 a **+4,96 s**, per damunt dels +4,85 del disseny d'avui. **El número
que val és el que produeixi el compilador**, i s'ha de verificar quan
s'implementi; el d'aquesta taula és el cas conservador.

Queda una cosa per mesurar abans de volar-ho: **els 5,30 s del canvi de base
són una xifra única, no una distribució**. Aquest és exactament el mode de
fallada del 8 d'agost, on el pressupost es va posar al màxim de 53 mostres
d'una mesura que no era la bona i va treure dos blocs de contacte amb 969 i
570 ms de retard. Convé mesurar-ne la dispersió, no afegir marge a cegues.

Per sota del terra de planificació, la variant **3+2** deixa 6,7 s a 90 s.

⛔ **I per damunt de ~95 s la configuració ja no creix.** El sostre de cua de
33 imatges deixa 18 per a mig eclipsi, o sigui sis tríades, i a 95,3 s ja hi
són totes. El temps extra per damunt d'això compra **marge, no fotogrames**:
a 100 s l'aproximació al bloc de contacte de C3 és d'11,25 s, contra els 10,15
del disseny d'avui.

Alternativa que hi cap al mateix tram i que **no** s'ha triat: a partir de
94,0 s també hi caben **5 àncores + 1 tríada** (33 imatges, earthshine 40 s,
però un sol subfotograma a cada esglaó nou). S'ha preferit 4 + 2.

## Per què cada número

### Contactes a base 1/800, no 1/320

La base d'avui (1/320 → 1/2500 · 1/320 · 1/40) **no entra mai a la banda de
perla compacta**: el seu fotograma més ràpid es queda 0,41 EV curt pel costat
lent, i a 1,54 EV del centre de la banda. Contra les dues bandes mesurades de
`research/66`:

| Base | Tríada | Al centre de la perla compacta | Al centre de la cromosfera |
|---|---|---:|---:|
| 1/320 (avui) | 1/2500 · 1/320 · 1/40 | 1,54 EV — **mai hi entra** | 0,49 EV |
| **1/800** | 1/6400 · 1/800 · 1/100 | **0,22 EV** | **0,83 EV** |
| 1/1000 | 1/8000 · 1/1000 · 1/125 | 0,11 EV | 1,15 EV — **al caire** |

**1/800 és l'únic valor amb un fotograma ben endins de cada banda.** Es va
considerar 1/1000, que clava més el pic de la perla, i es va descartar perquè
deixa el 1/1000 a 0,008 EV del caire de la banda de cromosfera — i aquella
banda és **l'única cosa que cap altre cos de la flota no cobreix**: les
finestres de contacte de la R6 van a 1/2000, que a f/2,8 equival a 1/7717 i
cau al centre de la perla compacta, no a la de cromosfera.

⚠️ **Cap cos pot arribar a l'extrem ràpid de la banda.** Amb cel net del tot,
la perla al seu pic demanaria 1/16635 i l'obturador de la Sony s'acaba a
1/8000: 1/6400 hi queda +1,38 EV i 1/8000 +1,06. El pic es cremarà una mica i
no hi ha res a fer en aquest cos. **El coixí de veritat és a la R6**, que té
1/16000 al menú —1/61735 equivalents a f/2,8— i en fa servir 1/2000.

### Segona base 1/4, no 0,4 s

Escombrat el menú sencer del cos amb l'objectiu correcte, que és el salt
màxim **des del membre lent de la tríada de contacte cap amunt** —no només a
mig eclipsi—:

| Base | Pont des de 1/100 | Mig eclipsi | **Pitjor** |
|---|---:|---:|---:|
| **1/4** | 1,74 EV | 2,00 EV | **2,00 EV** |
| 0,3 s | 2,00 EV | 1,74 EV | 2,00 EV |
| 0,4 s | 2,32 EV | 1,68 EV | 2,32 EV |
| 1/2 s | 2,74 EV | 2,00 EV | 2,74 EV |

Una versió anterior d'aquesta anàlisi recomanava 0,4 s. **Era un error de
mètrica**: mesurava només el salt de mig eclipsi i ignorava el pont. Afinar el
mig obrint el pont dona un resultat net pitjor.

### Tres àncores i tres tríades: la decisió de Pere, i què costa

El sostre de cua deixa **sis** tríades de mig eclipsi (15 imatges de contacte
+ 18 = 33), i l'única llibertat és com repartir-les:

| Repartiment | Esglaons nous | Earthshine | Cal T ≥ |
|---|---:|---:|---:|
| **3 + 3** — la triada | **N=3** | **24 s** (terra de la porta) | 89,5 s |
| 4 + 2 | N=2 | 32 s | 95,3 s |
| 5 + 1 | N=1 | 40 s | 94,0 s |

Pere tria **3+3**: escala regular, cap nivell amb menys de tres mostres, i el
llindar de durada més baix dels tres, que amb una totalitat que pot no
conèixer-se fins una hora abans no és poca cosa.

⚠️ **El que costa és tot el marge d'earthshine.** 3 × 8 s = 24 s és
**exactament** `min_earthshine_integration_s` de
`gui/tools/qa_totality_duration_gate.py`. Zero coixí: una acció saltada, una
àncora perduda per un rebuig net del setter, i el canal falla la porta amb
l'objectiu científic número u. Amb quatre àncores n'hi hauria 32 i un punt
sencer de marge. **Aquesta és la conseqüència a acceptar conscientment.**

I una correcció que va motivar la tria i que convé no arrossegar malament:
**N=3 no rebutja píxels calents.** Amb muntura equatorial i seguiment solar el
píxel calent és fix al sensor i la corona també; entre dos fotogrames del
mateix esglaó el Sol només deriva ~0,041 ″/s respecte de les estrelles, o sigui
**~1 px en 30 s**. Sense dither la mediana no els pot separar. Els píxels
calents es maten amb **biblioteca de fotogrames foscos** feta abans del dia a
la mateixa temperatura i ISO. El que N=3 compra de veritat és **√3 = 1,73×**
de senyal/soroll (contra 1,41 amb N=2) i el rebuig de transitoris —raigs
còsmics, un satèl·lit, una ratxa de vent—, que no és poc però no és el que es
va argumentar.

### El seguiment ho reforça

De la discussió amb Codex del mateix dia: la Lluna es mou **0,585 ″/s**
respecte del Sol (topocèntric; la mitjana geocèntrica sinòdica és 0,508 i es
queda un 15 % curta). El número es comprova sol: amb una totalitat de 100 s
implica un excés de diàmetre de 58″, o sigui magnitud local 1,031.

Amb seguiment **solar**, aquest moviment es transfereix a la Lluna dins de
cada exposició, i és **lineal amb el temps d'exposició**:

```text
1 × 16 s  = 16 s d'integració  ->  3,0 px de moguda per fotograma
2 ×  8 s  = 16 s d'integració  ->  1,5 px
4 ×  4 s  = 16 s d'integració  ->  0,8 px
```

Conseqüència directa: **a integració constant, més fotogrames i més curts són
més nítids**. Això va matar una idea que s'havia posat sobre la taula —una
tríada de base 2 s amb membre de 16 s— i **reforça les quatre àncores contra
les tres**: 4 × 8 s dona més integració amb la mateixa nitidesa per fotograma.

Xifres per al postprocessat: 1,5 px de moguda als 8 s de la Sony (0,24 % del
disc de 613 px) i 4,1 px als 15 s de la R6 (0,46 % de 883 px). Entre la
primera àncora i la quarta, 48 s, la Lluna es desplaça **28″ = 9 px** respecte
de la corona: la pila d'earthshine i la de corona **no poden compartir
alineació**.

⚠️ **`CLAUDE.md` §1 ter declara que els dos trens porten seguiment però no diu
mai a quina taxa.** La decisió operativa contrastada és **solar als dos, cap
canvi entre C2 i C3**, i no per nitidesa —el guany del seguiment lunar seria
1,5 px sobre 613, invisible— sinó perquè un canvi de taxa abans de C2 és una
acció d'operador al pitjor minut del dia. **Encara no s'ha escrit a §1 ter.**

## El que continua fluix

- **L'earthshine va al terra exacte de la porta, 24 s, amb zero marge.** És el
  preu conscient de la modalitat 3+3 i el punt més fràgil de tot el disseny.
- Els esglaons nous tenen tres subfotogrames, que dona √3 d'SNR i rebuig de
  transitoris, **però no de píxels calents**: això continua depenent de la
  biblioteca de darks.
- De 89,5 a ~93 s de totalitat el marge davant del bloc de contacte de C3 baixa
  per sota del que té el disseny d'avui. En aquell tram convé la variant 3+2.
- El salt de 2,00 EV entre 1/4 i 1 s i entre 2 s i 8 s. Amb tríades rígides de
  ±3 EV i sis unitats de mig eclipsi no es pot fer millor sense sacrificar
  earthshine.
- Mig eclipsi continua **sense cap fotograma a la banda de prominències**
  (1/1006 – 1/201): el més ràpid és 1/30. Ho cobreix la R6 amb 1/250, 1/125 i
  1/60 a cada passada. Una Sony sola no tindria prominències de mig eclipsi.

## La R6 Mark III: dos canvis, també ACCEPTATS i no implementats

Mateixa sessió, mateix estat. Els números surten de compilar el perfil de
missió viu a 91,0 s amb `_materialize_payload`, no d'un esbós.

### 1. Bloc fosc a mig eclipsi: 2 s ×3 i 10,3 s ×3

Avui, a 91,0 s, aquest cos fa **un sol fotograma de 2 s i un de 15 s**. El
llindar on n'hi caben dos de cada està declarat a `KNOWN_TIER_EDGES_S` i és
**91,071 s**: el terra de planificació hi queda 71 mil·lisegons per sota.

| | Avui | Proposta |
|---|---|---|
| Fotogrames profunds | 2 s ×1, 15 s ×1 | **2 s ×3, 10,3 s ×3** |
| Col·locació | C2+5,7 i C2+8,6 | **al mig, C2+18 a C2+53** |
| Salt del tram fosc | 1,00 · **2,91 EV** | 1,00 · **2,36 EV** |
| Escala per esglaó | 4,7 | **2 o 3** |
| Esglaons perduts | — | **cap** |
| Fotogrames dins totalitat | 108 | 88 |

**Baixar de 15 a 10,3 s no és renunciar a res: és el valor òptim de la flota.**
En equivalent f/2,8 la Sony del disseny 3+3 té 1 s i 8 s al tram fosc, i el
fotograma profund de la R6 és el que parteix aquell forat de 3,00 EV:

| Profund de la R6 | Equiv f/2,8 | Forats de flota | Màxim |
|---|---:|---|---:|
| 15 s (avui) | +1,96 EV | 1,96 i 1,04 | 1,96 |
| **10,3 s** | **+1,42 EV** | 1,42 i 1,58 | **1,58** |
| 8 s | +1,05 EV | 1,05 i 1,95 | 1,95 |

A sobre és **4,7 s més barat** que el de 15 s.

⚠️ **El preu és l'escala: de 4,7 a 2-3 fotogrames per esglaó, −0,53 EV** de
senyal/soroll a tota la corona de 1/2000 a 1 s. Cap esglaó desapareix i els
dotze salts d'1,00 EV es mantenen; el que perd és gruix, no forma. El
repartiment no és uniforme: **dues passades abans del bloc fosc i tres
després**, o sigui tres fotogrames als sis esglaons de les passades parelles i
dos als sis de les senars.

**Per què els fotogrames llargs són tan cars**: no és el temps d'exposició,
és el suplement. Després d'un fotograma llarg el cos refusa canviar
d'obturació fins a 2,10 s, i el compilador ho pressuposta.

| Valor | Cost real | = fotogrames d'escala |
|---|---:|---:|
| 2 s | 2,90 s | 2,8 |
| 4 s | 7,10 s | 7,0 |
| **10,3 s** | **13,40 s** | **13,1** |
| 15 s | 18,10 s | 17,7 |

**Es va descartar el graó de 4 s** que hauria tancat el salt de 2,36 EV: costa
**20,8 s, vint fotogrames d'escala**, i amb ell la petició original —2 s ×3,
4 s ×3, 10,3 s ×3— deixava només **9 fotogrames d'escala** i **perdia tres
esglaons sencers**: 1/15, 1/4 i 1 s. El 2,36 EV queda per sota del límit de
3 EV que Pere va posar i està cobert de sobres pel rang útil per fotograma.

### 2. La finestra de contacte de C3 s'allarga fins a C3+24 s

Verificat a `adaptive_profiles.py`: hi ha `R6M3_SINGLE_HDR_CONTACT_HEAD_S` i
`..._TAIL_S` a 5,0 i un `..._PRE_C2_S` a 17,0 que la 0.9.2 va afegir, però
**no existeix cap constant per a després de C3**. Resultat a 91,0 s: la
finestra va de **C3−7,0 a C3+4,0**, o sigui que pesa davant — i el segon anell
de diamant és **a C3 i just després**, com diu el mateix `CLAUDE.md`.

I just allà hi ha **25,75 s de programa completament buit**: l'últim fotograma
de contacte és a C3+4,00 i l'acció següent, el setter de la primera parcial
filtrada, a C3+29,75.

| | Avui | Proposta |
|---|---|---|
| Finestra de C3 | C3−7,0 → **C3+4,0** | C3−7,0 → **C3+24,0** |
| Fotogrames | 18 | **48** |
| Tolerància a un C3 tardà | +4,0 s | **+24,0 s** |
| Cost en segons de totalitat | — | **zero** |
| Canvis d'exposició nous | — | **zero** |

Amb `research/11` dient que el relleu lunar pot moure els contactes 1-3 s, i
sense saber el lloc exacte fins una hora abans, +4,0 s era tot el marge que
protegia un objectiu innegociable.

⚠️ **C3+24 és gairebé el màxim.** Deixa **5,1 s** abans del setter de la
primera parcial filtrada; per damunt d'uns C3+28 hi xocaria. I a partir d'uns
C3+5 el valor fotogràfic és nul —la fotosfera ja torna i el filtre es posa—:
**tot l'allargament és assegurança contra un C3 mal estimat**, i com que no
costa res, s'accepta igualment.

### Total dels dos canvis

108 → **118 fotogrames**. Es perden 26 fotogrames d'escala a mig eclipsi i se
n'hi guanyen 4 de profunds i 30 després de C3. Cap segon de totalitat gastat
a la finestra de C3.

## Procedència

Sessió de disseny del 9 d'agost de 2026 amb Pere, sobre el run
`20260809T132408`. Bandes de fenomen de `research/66`; pressupostos d'acció,
cadència i canvi de base mesurats i recollits a `CLAUDE.md` §7; llindars de la
porta a `gui/tools/qa_totality_duration_gate.py`. Contrast extern de Codex
sobre la taxa de seguiment.
