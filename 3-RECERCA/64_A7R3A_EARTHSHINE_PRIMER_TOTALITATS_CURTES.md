# 64 — L'earthshine primer: com encabir els tres objectius a l'A7RIIIA amb 60 s

8 d'agost de 2026. Decisió de Pere: **l'earthshine és la missió principal de
l'A7RIIIA**, i el programa ha de saber escurçar-se fins a 60 s de totalitat
sense perdre cap dels tres objectius —earthshine, perles i anells travessant
C2 i C3, i bracketing de corona amb moltes EV.

Avui no ho compleix: per sota de 90 s el cos perd l'earthshine i baixa a
6,1 EV.

## 1. El defecte no és de pressupost, és d'ordre de construcció

`_a7r3a_earthshine_burst_count()` diu, literalment, que **zero àncores és una
resposta legítima**, i retorna zero per sota de 88 s. La finestra d'earthshine
es calcula «des del final del primer punt de control de memòria fins al moment
en què s'ha d'escriure la base del contacte de C3»: és a dir, **el compilador
col·loca primer els contactes i els drenatges, i a l'earthshine li dona el que
sobra**.

Amb la prioritat nova, això és exactament al revés. L'earthshine s'ha de
col·locar **primer** i la resta ha d'omplir al seu voltant.

## 2. Tres coses que el cos ja sap fer i no fèiem servir

### 2.1 Una sola ràfega d'earthshine ja és una passada de corona de 12 EV

`Bracketing C 3.0 Steps 5 Pictures` des de base 1/8 dona
**1/500, 1/60, 1/8, 1 s, 8 s**: dotze punts de rang en cinc fotogrames, amb
la lenta a l'àncora d'earthshine. No és un bloc que competeixi amb el
bracketing de corona: **és bracketing de corona i earthshine alhora**.

Unit a un sol bracket de contacte (1/4000..1/15, 8 EV), la unió dona
**1/4000 a 8 s = 15 EV**, que és exactament el rang que avui té el programa
sencer de 98,8 s.

**Conseqüència**: els tres objectius es compleixen amb **tres pulsacions**.

### 2.1 bis — CORRECCIÓ de Codex: el mode no es pot canviar amb la cua plena

La primera versió d'aquest document proposava contactes amb `C 2.0 Steps 5` i
earthshine amb `C 3.0 Steps 5`. **És un error i Codex l'ha enxampat.** Barrejar
dos modes obliga a escriure `capturemode` amb imatges pendents a la cua, i el
TEST RUN de tres càmeres del 2 d'agost va demostrar al cos les dues cares:
**l'escriptura d'obturació s'accepta amb 36 JPEG pendents, però el canvi de
`capturemode` sota aquest deute es rebutja** (verificat a
`gui/eclipse_command/adaptive_profiles.py:458` i al contracte del tram fixed5).

Per això el contracte viu declara `capturemode_value_changes_inside_totality:
0`, i el meu pla se'l saltava dues vegades.

**El disseny correcte és un sol mode per tota la totalitat i només canvis de
base d'obturació**, que és el que Codex proposa i el que adopto.

### 2.1 ter — I aquest disseny ja existeix, qualificat, i és codi mort

`_materialize_a7r3a_fixed5_midpoint()` (línia 5780) fa exactament això:
`C 3.0 Steps 5` fix de C2 a C3, set ràfegues, **35 RAW sobre quinze
exposicions de 1/5000 a 3,2 s**, `capturemode_changes_inside_totality: 0`,
`drains_inside_totality: 0`, `maximum_planned_jpeg_debt: 35`, i tot el
drenatge diferit a després de C3.

Porta qualificació física pròpia: run `20260802T032019`, **42 imatges
confirmades, 35 dins totalitat**, drenatge posterior de 35 en 23,88 s,
postflight, restore i cleanup nets, `timing_qualified: true`.

**I no es crida des d'enlloc.** La funció està definida i cap camí del
compilador hi arriba: el tram fixed9 la va substituir i la va deixar orfe.

Això canvia la feina: **no cal inventar un tram per a totalitats curtes, cal
ressuscitar-ne un de qualificat i fer-li dues coses**:

1. **pujar la seva exposició profunda de 3,2 s a 8 s**, que és l'àncora
   d'earthshine (base 1/8 en comptes de la que faci servir ara);
2. **moure els seus blocs de contacte perquè travessin C2 i C3**, el mateix
   defecte que ja s'ha corregit al tram fixed9.

### 2.2 El cos ofereix `Bracketing C 2.0 Steps 5 Pictures`

Llegit dels transcripts del cos (choice 27). Des de base 1/250 dona
**1/4000, 1/1000, 1/250, 1/60, 1/15**: el **mateix rang** que el bracket de
nou fotogrames que fem servir ara, amb **cinc**. Mateixos extrems, mostreig
cada 2 EV en comptes d'1.

A 0,51 s de drenatge per imatge, això és **44 % menys deute de cua** per
bracket de contacte. I permet més pulsacions travessant el contacte, que per
un fenomen que dura un o dos segons val més que afinar el mostreig.

### 2.3 Sota les 36 imatges no cal drenar gens dins la totalitat

El límit demostrat és 36 (una prova de 5×9 = 45 en va lliurar 36); el màxim
observat als runs reals és 28. Un pla que es mantingui sota aquest sostre
**no ha de drenar ni un segon dins la totalitat** i pot deixar tot el
drenatge per després de C3, on hi ha 82 s buits.

Avui el drenatge es menja **31,8 s dels 98,8**, el 32 %.

## 3. Els 400 ms que hi posem nosaltres

Desglossament real d'una escriptura d'obturació, 48 mostres de tots els runs
A7RIIIA:

| | mediana | p95 | màxim |
|---|---:|---:|---:|
| total | 2,129 s | 4,239 s | **4,474 s** |
| ACK del cos | 1,717 s | 3,820 s | 4,061 s |
| **espera fixa nostra** | **0,400 s** | 0,405 s | 0,410 s |
| lectures | 0,010 s | 0,018 s | 0,020 s |

És el mateix mal que la R6 (research/62), però menys greu: allà els 400 ms
eren el 90 % del cost, aquí en són el 19 %. L'ACK d'1,7 a 4,1 s **és del cos**
i no es pot negociar. Els 400 ms sí: substituir-los per una enquesta amb el
mateix sostre val **19,2 s repartits en 48 escriptures**, i dins una totalitat
concreta, entre 0,8 i 1,2 s.

El pressupost compilat és de **6,87 s per escriptura** contra un màxim real de
4,474: 1,5× de marge, que per una acció sense reintent és raonable i **no s'ha
tocat**. El que sí que es pot fer és treure'n l'espera nostra i, aleshores,
baixar-lo a ~6,1 conservant el mateix 1,5×.

## 3 bis. El programa candidat, ja amb la correcció de Codex

**Un sol mode tota la totalitat: `Bracketing C 3.0 Steps 5 Pictures`**,
escrit abans de C2 i no tocat fins després de C3. Només canvien les bases
d'obturació: `1/80 → 1/8 → 1/80`.

| Bloc | Base | Exposicions | Imatges |
|---|---|---|---|
| 2 ràfegues travessant C2 | 1/80 | 1/5000, 1/640, 1/80, 1/10, 0,8 s | 10 |
| 2 àncores d'earthshine | 1/8 | 1/500, 1/60, 1/8, 1 s, **8 s** | 10 |
| 2 ràfegues travessant C3 | 1/80 | 1/5000, 1/640, 1/80, 1/10, 0,8 s | 10 |
| **Total** | | **1/5000 a 8 s ≈ 15,3 EV** | **30** |

Trenta imatges deixen sis places de marge sota les 36 demostrades. **Zero
drenatges i zero canvis de mode dins la totalitat.** Si el gate de contacte
surt verd, una tercera ràfega a C2 el puja a 35, que és exactament el deute
que el tram fixed5 ja té qualificat.

**Avís de Codex que val or**: els offsets `−2,9 / 0 / +2,9` del bracket de nou
**no es poden reutilitzar**. En una ràfega de cinc a 3 EV l'ordre real és
0, −3, +3, −6, +6, o sigui que **el fotograma ràpid és el quart de cinc**, no
el primer. Si es col·loca la ràfega com si disparés de seguida, el fotograma
que ha d'atrapar l'anell de diamant arriba dos segons tard. Cal mesurar
l'instant real de cada exposició dins la ràfega i situar-la a partir d'això.

## 3 ter. Mesura del bràqueting ampliat, i el parany que hi porta

**Sostre del cos.** Llista sencera de `capturemode` llegida dels transcripts:
a passos de 0,3, 0,5, 0,7 i 1,0 EV el cos deixa fer 3, 5 o 9 fotogrames; **a
2,0 i 3,0 EV només en deixa fer 3 o 5**. O sigui que el bràqueting més ampli
possible en una sola pulsació és `C 3.0 Steps 5` = **±6 EV = 12 EV**. No
existeix cap `C 3.0 Steps 9`.

**Velocitat.** Mesurat de l'EXIF dels runs d'aquesta nit: una ràfega de nou
fotogrames lliura els nou en **~1,5 s** (els cinc primers dins un segon i els
quatre restants dins el següent). Una de cinc, proporcionalment, ~0,8 s.
**Dotze punts de rang en menys d'un segon** és exactament el que demana un
instant on la llum canvia per ordres de magnitud.

**El parany.** L'ordre de biaixos d'una ràfega Sony no és monòton: és
0, −3, +3, −6, +6. En una `C 3.0 Steps 5` això vol dir que **el fotograma més
ràpid és el quart de cinc**, i en una `C 1.0 Steps 9` el més ràpid (1/4000)
és el vuitè de nou, ~1,2 s després de la pulsació. Col·locar la ràfega com si
disparés de seguida posa el fotograma que ha d'atrapar l'anell de diamant un
segon llarg tard. **La ràfega s'ha d'ancorar pel seu fotograma ràpid, no pel
seu inici.**

## 3 quater. El rellotge del cos va 21 s avançat

Comprovat en **quatre runs independents** d'aquesta nit
(`20260807T222902`, `224852`, `225500`, `233944`): l'hora EXIF del cos, un cop
descomptada la zona horària, va sistemàticament **+21 s** respecte del
rellotge del Mac que dirigeix la captura.

No afecta la captura —el programa es guia pel rellotge del Mac— però sí
qualsevol comprovació posterior: **si algú creua l'EXIF amb les hores de
contacte, es desviarà 21 s, que és una cinquena part d'una totalitat de
100 s**.

**CORREGIT LA MATEIXA NIT.** Pere va posar el cos en hora i s'ha verificat
amb tres fotogrames disparats i esborrats: l'EXIF cau sempre al mateix segon
en què s'envia l'ordre (00:40:09 / 00:40:54 / 00:40:57 contra ordres a
:09,3 / :54,3 / :57,3), o sigui **desfasament per sota d'un segon**. Amb la
resolució d'un segon de l'EXIF d'aquest cos no es pot afinar més sense un
muntatge de temps dedicat, i per creuar fotogrames amb contactes ja no cal.

Queda com a recordatori de checklist: **el rellotge del cos deriva**, i entre
el 2 i el 7 d'agost havia acumulat 21 s. Val la pena tornar-lo a comprovar el
dia 12 amb aquest mateix mètode.

**Pendent: fer la mateixa comprovació a la R6 III.** No s'ha pogut fer perquè
el cos torna a ser fora del bus. El mètode és el mateix i costa un fotograma:
disparar-ne un amb l'hora del Mac anotada i comparar-la amb l'EXIF.

**Abast del defecte a l'evidència ja escrita**: les verificacions EXIF
d'aquest projecte són de *valors* —obturació, ISO, format, cos— i no d'hores
absolutes, o sigui que no queden invalidades. La col·locació dels contactes
que es va verificar la nit del 7 d'agost es va mesurar amb l'`utc` dels
esdeveniments del worker, no amb l'EXIF, i per tant tampoc. Però qualsevol
comprovació futura que vulgui creuar una hora EXIF amb un contacte ha de
descomptar primer el desfasament del cos.

## 4. El programa que en surt

Costos: bracket de nou 2,871 s (mesurat), ràfega d'earthshine 11,2 s
(pitjor cas del perfil), escriptura d'obturació 4,074 s (màxim real menys
l'espera nostra), escriptura de mode 0,89 s (p95 real), drenatge 0,51 s per
imatge.

| Nivell | Què hi ha | Temps | Imatges | Cua |
|---|---|---:|---:|---|
| **1 — intocable** | 1 bracket travessant C2 · 1 ràfega earthshine · 1 bracket travessant C3 | **30,9 s** | 23 | OK |
| 2 | + 2a àncora d'earthshine (apilable) | 42,1 s | 28 | OK |
| 3 | + 1 bracket més a cada contacte (amb 5×2) | 45,2 s | 30 | OK |
| 4 | + 3a àncora / passada de corona interleaved | 59,1 s | 51 | cal drenar |

**A 60 s de totalitat hi cap el nivell 3 sencer amb quinze segons de marge i
sense drenar ni un segon dins la totalitat.**

El nivell 1 compleix els tres objectius en 30,9 s. Tot el que hi ha per sobre
és densitat de mostreig, no cobertura.

## 5. L'ordre de degradació, copiat de la R6

La R6 ja té resolt aquest problema i el seu patró és
`("tail", "A", "B", "A", "B", "A", "B")`: **la cua profunda —les àncores
llargues— va primera**, i el que es perd quan falta temps són les passades
repetides del final. A més, no trunca mai una escala: «una escala truncada és
un joc d'exposicions trencat».

Traduït a l'A7RIIIA, de l'últim que es retalla al primer:

1. **Mai**: una ràfega d'earthshine, un bracket travessant C2, un travessant C3.
2. Es retalla l'últim: passades de corona addicionals.
3. Després: el segon bracket a cada contacte.
4. Després: la segona àncora d'earthshine (es perd l'apilat, no l'earthshine).
5. Mai s'arriba aquí: el nucli del punt 1.

## 6. Proves físiques que calen, per ordre de valor

1. **Hold real d'una ràfega de cinc fotogrames ràpids** (`C 2.0 Steps 5`).
   Tot el guany del 5×2 depèn d'aquest número i ara mateix és una estimació
   proporcional de 2,2 s. Si resulta ser 2,5 com la de nou, el 5×2 continua
   valent per la cua però no pel temps.
2. **Que 30 imatges seguides sense drenar dins la totalitat no bloquegin la
   cua.** El límit de 36 està demostrat, però no amb aquesta barreja.
3. **L'enquesta en comptes dels 400 ms fixos**, amb el mateix sostre, i
   comprovar que el readback continua sortint a la primera.
4. **Un run sencer a 60 s de totalitat** amb el pla del nivell 3.

## 7. Què no s'ha de fer

- **No tocar el pressupost de 6,87 s a la babalà.** El màxim real és 4,474 i
  el marge d'1,5× protegeix una acció d'un sol intent. Primer es treu l'espera
  nostra, es torna a mesurar, i llavors es rebaixa.
- **No estirar el tram per sobre de 104 s.** Ja s'ha comprovat: a partir de
  105 deixa de superar la graella de 20 s en densitat temporal.
- **No baixar el terra dels 90 s tocant només la constant.** El compilador ho
  accepta i l'auditoria de cronologia no: per sota de 88 s el bracket de 3,2 s
  del punt mitjà se solapa amb la finestra de re-trigger. El terra baixa
  només si el pla canvia de forma.
