# 62 — El setter de la R6 no el paga el transport, el pagava un `sleep` nostre

7 d'agost de 2026, tarda. Encàrrec de Pere: optimitzar al màxim gphoto2 per a
la R6 III. El resultat és que la despesa més gran del programa no era del cos
ni de libgphoto2.

## 1. El desglossament

Una acció de setter del run `20260807T143855`, mil·lisegon a mil·lisegon:

| | |
|---|---:|
| `get-config` del valor actual | 27 ms |
| **`set-config-index`, l'escriptura de debò** | **12 ms** |
| **espera fixa del worker** | **400 ms** |
| `get-config` de comprovació | 5 ms |
| **total de l'acció** | **445 ms** |

Sobre tot el run: `set-config-index` **17 ms de mediana** (8–31) i
`get-config` **4 ms** (0–186) sobre 134 lectures. La pulsació en costa 19 i
l'alliberament 4.

**Dels 445 ms d'un canvi d'exposició, 400 eren no fer res.** Era
`CameraController(settle_s=0.40)`, un `sleep` fix entre l'escriptura i la
rellegida de comprovació.

Això obliga a corregir una lectura d'aquest matí: la taula de `research/60`
compara «setter gphoto2 415-453 ms» contra «setter EDSDK ≤ 24 ms». Els dos
números són bons, però no comparen el mateix: el de l'SDK és la crida crua i
el de gphoto2 inclou aquesta espera nostra. **El transport de gphoto2 no és
lent.**

## 2. La reparació

L'espera passa a ser una **enquesta**: primera rellegida **immediata** —l'SDK
veu el cos adoptar `Tv` en microsegons, o sigui que pot estar fet quan torna
l'ACK— i després 8, 8, 16, 25, 25, 50, 50 i 100 ms, amb **el mateix sostre**
de 400 ms. Dins el sostre hi caben una dotzena de lectures.

El calendari afina al principi i frena després per una raó: si el cos no ha
adoptat als primers seixanta mil·lisegons, rellegir-lo sense parar no el farà
anar més de pressa i sí que carrega el transport.

**Cap garantia no es mou**: una sola escriptura, la lectura és de només
lectura, i si el valor no apareix dins el sostre la sortida és exactament la
d'abans —desajust i el camí de fallada de sempre—. En particular **no** és la
verificació diferida que el worker ja tenia: aquella tolera adopció tardana i
està **prohibida expressament per a l'obturació**, amb bon criteri, perquè una
exposició adoptada tard és un fotograma mal exposat.

Cada setter registra ara `adopted_ms` i `adoption_polls`.

## 3. Dues millores de geometria que no demanen res de nou al cos

Mesurades offline amb la geometria viva, a 98,8 s de totalitat:

**El pas «profund» repeteix l'escala A sencera abans de la cua.** Per això A
surt quatre vegades i B només dues, quan les dues escales estan entrellaçades
justament per mostrejar el mateix interval desplaçades 1 EV. Amb la cua sola
—patró `tail_only`— queden tres i tres.

**La finestra de contacte de C3 pot obrir-se tan aviat com el marge permeti**
en comptes de deixar-lo mort. Una escala que no hi cap sencera no s'hi posa, i
el que sobrava no tenia cap fotograma.

| Obturació | Avui | `tail_only` + elàstica | Delta |
|---|---:|---:|---:|
| 1/2000 | 53 | **65** | +12 |
| Escala A (1/500…0,5) | 5 de cada | 3 de cada | −2 |
| Escala B (1/1000…1) | 2 de cada | 3 de cada | +1 |
| 2 s i 15 s | 2 i 2 | 2 i 2 | = |
| **Total** | **94** | **102** | **+8** |

Mateixa cadència, mateixes exposicions, mateix settle: res que no estigui ja
demostrat al cos aquesta tarda. Una cerca sobre l'espai de patrons diu que
**102 és el sostre** amb la ranura de setter actual.

Van als dos costats alhora —tier i worker—, perquè la timeline del probe ha
de ser el mirall exacte de la del worker i una prova ho comprova. El
compilador de sonda conserva els patrons antics darrere `--pass-pattern` per
poder-los tornar a mesurar.

## 4. La mesura al cos: el `sleep` era tot

Run `20260807T171524`, 102 fotogrames amb delta CFexpress exclusiu +102 i el
menú 58 → 58, amb l'enquesta activada:

| | |
|---|---:|
| Adopció, mediana | **3,4 ms** |
| Adopció, màxim sobre 43 canvis | **16,3 ms** |
| Rellegides per setter | **1**, sempre |
| Acció de setter sencera, mediana | **34,8 ms** |
| Acció de setter sencera, màxim | **58,2 ms** |

**El cos ja havia adoptat el valor quan tornava l'ACK de l'escriptura.** Els
400 ms d'espera no compraven res: ni un sol setter de tot el run n'ha
necessitat una segona lectura.

## 5. La geometria que això obre, validada al cos

Amb el setter mesurat a 58 ms de pitjor cas, la ranura baixa de 0,55 a
**0,25** —quatre vegades el pitjor cas— i els pressupostos declarats deixen
de ser els de l'època del `sleep`: worst case 0,35 → **0,15**, tolerància
0,13 → **0,05**, deadline 0,50 → **0,23**.

I el patró de passades passa a **alternança pura**, `tail,A,B,A,B,A,B`: una
cua d'earthshine i després A i B alternant, que és el que el disseny
entrellaçat demana. Amb la ranura petita, el patró de parelles hi encabia una
tercera cua que costava vint segons; l'alternança els gasta en fotogrames.

Run `20260807T172151`, **la geometria de missió actual**:

| | |
|---|---:|
| Fotogrames | **115/115** |
| Delta CFexpress exclusiu | **+115** |
| Setters verificats | **61/61**, zero Busy |
| Acció de setter, màxim | 67,8 ms sobre un pressupost de 250 |
| Retard màxim | **0,023 ms** sobre 175 accions |
| Menú | 58 → 58 |
| Cleanup i restore | nets, estat físic conegut |

**De 94 fotogrames a 115: un +22 %**, que és exactament el que hauria comprat
l'EDSDK, per gphoto2 i sense el seu mode de fallada. Dins totalitat, de 79 a
92.

## 6. I el run sencer per l'app

`20260807T181413`, pel binari del bundle **0.8.9** amb TEST RUN i totalitat de
98,8 s:

| | |
|---|---:|
| Accions de captura | **120/120** |
| Delta CFexpress exclusiu | **+120** (5.357 → 5.477) |
| Setters amb readback | **61/61**, zero Busy |
| Retard màxim | **0,010 ms** sobre 181 accions |
| Menú | 58 → 58 |
| Cleanup, restore, estat físic | nets i conegut |
| `frozen_dispatch_ok` | **true** |

Contra el run per l'app d'aquest migdia, que anava amb la geometria de 94:
**99 accions → 120**.

## 7. On para el guany

La ranura no baixa més perquè el que mana ara és una altra cosa: **el terra de
pulsació del cos, 400 ms**, que no és nostre. Amb la ranura a 0,25, el setter
ocupa el 6 % del temps de la geometria i el 94 % restant són fotogrames a
cadència màxima. Baixar la ranura a 0,15 compraria cinc fotogrames més i
retallaria el marge de quatre vegades a dues i mitja sobre el pitjor setter
mesurat: no val la pena a cinc dies de l'eclipsi.

## 8. Límits

- Tot això és **card-only**: el delta CFexpress és exclusiu i comptat, però
  no hi ha manifest ni inspecció CR3 lligats a cada acció.
- Òptica Sigma 35 mm, no el VSD90SS.
- Regressió amb tots aquests canvis: GUI **445/445**, controlador
  **1.075/1.075**, fuzz **67.392/67.392**, perfils curts i `git diff --check`.
- Bundle **0.8.9**: executable
  `6c10adc45fd1bc0d51c13770a356ce5a3eef2f6648d9f226d6c12eebbd7d9840`,
  manifest `05602c6c442f3503f5fbdea176d37caa00bba86ce4b740fa3c9f9a4f29807b6b`,
  49 inputs i **dotze PASS** de `qa_macos_portable.py`.
