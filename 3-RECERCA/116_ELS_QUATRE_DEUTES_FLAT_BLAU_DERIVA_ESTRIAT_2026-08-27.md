# Els quatre deutes del 27 d'agost: el flat, el blau, la deriva i l'estriat

*27 d'agost de 2026, tarda i vespre. Per ordre de Pere: «segueix amb totes les
tasques 1, 2, 3 i 4».* Són les quatre coses que `research/115` va deixar
obertes. Aquest document les tanca o les acota, i **rectifica dues conclusions
del `115`** i **una del treball dels dos trens**.

Eines noves, totes a `research/tools/`:
`sony_entrada/flat_pel_salt.py` (refet, amb tres controls),
`sony_entrada/flat_creuada.py`,
`dos_trens_jutge/color_per_exposicio.py`,
`dos_trens_jutge/color_compost_vs_crus.py`,
`dos_trens_jutge/deriva_fotometrica.py`,
`dos_trens_jutge/un_sol_cel.py`,
`dos_trens_jutge/estriat_per_canal.py`,
`dos_trens_jutge/estriat_resolucio.py`,
`dos_trens_jutge/estriat_gira.py`,
`dos_trens_jutge/vistes_quatre_deutes.py`.

Run nou: **`SONYTOT_CIENCIA_20260827T142411Z`** (17,5 min, totes les portes
PASSA), amb el flat corregit. Vista: `2-OUTPUT/DOS_TRENS/QUATRE_DEUTES_27-08.png`.

---

## 1. El resum, per si no llegeixes res més

| deute | veredicte |
|---|---|
| **1 · el flat de la Sony** | ⏭️ **mesurat i ADOPTAT**. Valida fora de mostra i **la deriva fotomètrica entre trens cau del 13,51 % al 7,43 %**. ⛔ Però **no** fa el que el `115` §15 predeia: l'estructura fina no es recupera (1,8°: 0,890 → 0,884). |
| **2 · el blau** | ⏭️ **descompost**: dels 5-11 % de desacord, **~3 punts són les dues càmeres** (i la matriu de color en prediu encara més) i **la resta la posa la nostra cadena** — 2 punts la composició i de 3 a 8 la resta del cel, que creix cap enfora. |
| **3 · la deriva fotomètrica** | ⏭️ **la meitat era el flat**. El que queda (7,4 %) **no és el nivell del cel**: la prova conjunta el descarta. És estructurat: +4,6 % a 1,15 R☉ i −2,2 % a 2,5 R☉. |
| **4 · l'estriat fi** | ⛔ **la quincunx del verd queda REFUTADA** (G/(R,B) = 1,12: hi és igual als tres canals). I ⚠️ **«només de la Vixen» era massa fort**: la Sony també el té (×4,1-4,9 contra ×6,6-7,9). Mecanisme **obert**, amb tres hipòtesis eliminades. |

I dues rectificacions que manen sobre el `115`:

⛔ **`research/115` §13 atribuïa al flat el sistemàtic bimodal de la porta de
brillantor** (7,7-9,7 % a l'apuntament A contra 2,0-2,9 % al B) perquè el número
coincidia amb l'error de flat mesurat (7-9 %). **És fals.** Amb el flat
corregit el sistemàtic **no es mou** (mediana 5,27 → 6,48 %, dispersió
7,70 → 7,53 %). Era una **coincidència de magnitud**, i la regla de `trampes.md`
—mou el paràmetre abans de declarar la causa— ja hi era escrita per a les
coincidències de posició. Ara també val per a les de magnitud.

⛔ **`research/115` §15 predeia que corregir el flat recuperaria l'escala fina.**
No ho fa. El detall que el segon apuntament paga té una altra causa.

---

## 2. Deute 1 · el flat de la Sony, mesurat pel dither

### 2.1 La mesura

L'A7RIIIA no té flats invertits i el seu flat radial no tenia porta. El salt de
muntura de 749 px fa de **dither**: el mateix punt del cel cau a dues posicions
del sensor molt separades, i amb prou parells s'inverteix el flat sense flats
(`ln q = const + lnF(rA) − lnF(rB)`, mínims quadrats sobre una graella radial,
gauge lnF(0) = 0). **7 parelles, 57 milions de parells de radis per canal.**

| canal | amplitud de l'error |
|---|---:|
| R | 7,63 % |
| G1 | **9,03 %** |
| B | 7,16 % |
| G2 | 8,75 % |

⏭️ I és quasi **acromàtic**: el B/G només varia un **2,29 %** pel camp. Per tant
el flat **no pot explicar** el blau del deute 2, i el `115` §11 ja ho deia.

### 2.2 Els tres controls (dos són nous)

El control que hi havia —meitats de **píxels**— només mesura soroll: els dos
subconjunts surten de les mateixes parelles i comparteixen qualsevol
sistemàtic. Se n'hi afegeixen dos que sí que poden desmentir la mesura:

| control | R | G1 | B | G2 | què desmenteix |
|---|---:|---:|---:|---:|---|
| meitats de **píxels** | 0,51 % | 0,10 % | 0,04 % | 0,04 % | soroll |
| meitats per **PARELLA** | 1,98 % | 1,35 % | 1,30 % | 1,27 % | que sigui **el CEL** |
| per **NIVELL** (curtes/llargues) | 4,65 % | 3,57 % | 4,25 % | 3,65 % | que sigui **ADDITIU** |

El de nivell semblava dolent (la meitat de l'amplitud), però el que decideix no
és el desacord sinó **la forma**:

| canal | amplitud curtes | amplitud llargues | raó | forma curtes × llargues |
|---|---:|---:|---:|---:|
| R | 10,91 % | 8,08 % | 1,35 | 0,677 |
| G1 | 8,84 % | 9,18 % | **0,96** | **0,958** |
| B | 7,96 % | 9,33 % | 0,85 | 0,781 |
| G2 | 8,09 % | 9,25 % | **0,87** | **0,949** |

Als dos verds, curtes i llargues veuen **la mateixa forma amb la mateixa
amplitud** → el residu és **multiplicatiu**, o sigui flat, i no llum dispersa
additiva (que hauria donat amplituds molt diferents). ⚠️ El canal **R és el
menys ben determinat** (forma 0,68) i queda declarat com a tal.

### 2.3 La validació que faltava: fora de mostra

Un model radial de 40 graus de llibertat sempre baixa el residu de les dades amb
què s'ha ajustat. `flat_creuada.py` fa **deixa'n una fora**: ajusta amb sis
parelles i prediu la setena. I hi arregla un defecte de mètode de la primera
versió: **la constant per parella es restava com a mediana de `q`**, que no és
el mateix que ajustar-la (cada parella cobreix una distribució de radis
diferent, i forçar-ne la mediana injecta senyal a `lnF`). Ara és una incògnita
més. La forma resultant és idèntica (correlació 1,000) i l'amplitud canvia menys
d'un 0,1 %.

El guany absolut és petit —de +1,1 a +2,0 % de rms— **però el soroll de fotons
per píxel domina el residu d'una parella**, i per això el número que val és
guany **assolit contra guany esperat**:

| canal | guany mitjà | assolit / esperat |
|---|---:|---:|
| R | +1,1 % | 24-176 %, mitjana ≈ 100 % |
| G1 | +2,0 % | ídem |
| B | +1,6 % | ídem |
| G2 | +2,0 % | ídem |

⏭️ **El model dona, fora de mostra, exactament el guany que promet.** És una
mesura, no una memorització.

### 2.4 Com entra a la cadena

Com una **constant declarada del tren**, igual que el pedestal:
`flat_dither_SONY.json` al costat del codi, **hashejat al manifest** (`SCRIPTS`
de `cadena.py` el congela), i `f0.flat_radial` només l'aplica:
`FLAT_corregit(r) = FLAT(r) · exp(lnF(r))` per canal CFA. Gauge lnF(0) = 0:
**l'escala absoluta no es toca**. La Vixen no en porta i no es toca.

### 2.5 Els jutges

| jutge | abans | després | |
|---|---|---|---|
| **fotometria contra la Vixen** (1,15-4,20 R☉) | 13,51 % | **7,43 %** | ⏭️ **−45 %** |
| estructura × Vixen 90° | 0,996 | 0,994 | ≈ |
| estructura × Vixen 30° | 0,997 | 0,997 | = |
| estructura × Vixen 12° | 0,987 | 0,988 | ≈ |
| estructura × Vixen 4,5° | 0,974 | 0,973 | ≈ |
| estructura × Vixen 1,8° | 0,890 | **0,884** | ⛔ una mica pitjor |
| porta interna de brillantor (mediana) | 5,27 % | 6,48 % | ⛔ no millora |
| porta interna de brillantor (dispersió) | 7,70 % | 7,53 % | ⛔ no millora |

⏭️ **S'adopta**, i el motiu és el primer: el jutge més independent que tenim
—l'altre instrument, mesurant la mateixa corona— millora un 45 %, i la mesura
passa la validació fora de mostra. El cost és **0,006 de correlació a 1,8°**, i
es declara. Un calibratge mesurat no es deixa d'aplicar per 0,6 punts de mil·lè
de correlació; però tampoc no es diu que ha arreglat el detall fi, perquè no ho
ha fet.

### 2.6 Què mesurava, doncs, la porta de brillantor

La porta compara **percentils** dins de cada anell. Al run vell, a 3-3,6 R☉ la
desviació anava de **+8,7 % al percentil 10 a −9,5 % al 90**: el quocient
compost/fotograma **depèn de la brillantor del píxel**, que és la signatura d'una
**diferència de nivell additiva** entre el compost i el fotograma de control.

⏭️ Això és **el cel canviant en el temps**, no el flat: el compost és una
mitjana temporal i un fotograma és un instant. És la mateixa causa que el `115`
§12 va mesurar per al color (12 % de B/G en 100 s), i explica per què és
**bimodal per apuntament**: els controls de l'apuntament A són de t = 16-28 s i
els del B de t = 80-88 s.

---

## 3. Deute 2 · el blau, descompost

### 3.1 Tres trampes de mètode, i totes tres van picar

Per mesurar el color de la corona fotograma a fotograma:

1. ⛔ **Mesurar cada fotograma als seus propis píxels vàlids.** El tall de
   soroll és un tall en DN i el canal B és el més feble: a les exposicions
   curtes hi sobreviuen els píxels amb més blau i **el B/G puja sol**. Sortia
   una dispersió del **127 %** dins d'un mateix tren, que és la selecció, no la
   dada.
2. ⛔ **La intersecció dels píxels vàlids.** Hereta el tall del fotograma més
   curt i torna a triar els blaus (B/G 1,05, més blau que el cel).
3. ⛔ **La intersecció era en píxels de SENSOR.** Amb el salt de 749 px, el
   mateix píxel del sensor mira **un tros de corona diferent** a cada
   apuntament: sortia un factor 1,6 de brillantor i B/G 0,69 contra 0,43, que no
   són de la càmera sinó de la corona.

⏭️ **La cura: cap tall per baix.** Màscara només de geometria i no-saturació,
anell ancorat al **Sol de cada fotograma** (o sigui, al cel), i **mitjana**, no
mediana: una mitjana sobre 300.000 píxels de soroll simètric és insesgada encara
que cada píxel sigui soroll. Un tall per baix mai no ho pot ser.

### 3.2 Els fotogrames crus: el calibratge queda exculpat

Amb el mètode bo, fotogrames ben exposats (cap saturació, error estadístic
< 0,5 %), tots mirant **el mateix tros de cel**:

| anell | tren | n | R/G | B/G | dispersió R/G | dispersió B/G |
|---|---|---:|---:|---:|---:|---:|
| 1,30-1,70 | Vixen | 26 | 1,7228 | 0,5022 | 2,18 % | 5,80 % |
| 1,30-1,70 | Sony | 9 | 1,7138 | 0,4887 | 3,81 % | 4,66 % |
| 1,05-1,30 | Vixen | 44 | 1,8077 | 0,4928 | 5,46 % | 6,81 % |
| 1,80-2,20 | Vixen | 31 | 1,5395 | 0,6078 | 6,10 % | 20,65 % |
| 1,80-2,20 | Sony | 13 | 1,5508 | 0,5861 | 6,94 % | 12,15 % |

⏭️ **Dins de cada tren el color és estable** a través d'un factor de 200 a 1000
en exposició. **El calibratge (linealitat, pedestal, flat) queda exculpat.**

I entre trens, sobre la dada crua: **B/G −2,69 %** a 1,3-1,7 R☉ i **−3,57 %** a
1,8-2,2, amb R/G a −0,53 % i +0,73 %.

### 3.3 On apareix la resta: a la nostra cadena

Als **mateixos anells** i al **mateix espai de càmera**:

| anell | crus | + composició LDIC | + resta del cel (CORONA) |
|---|---:|---:|---:|
| 1,05-1,30 | — | −5,03 % | −6,09 % |
| 1,30-1,70 | **−2,69 %** | −5,06 % | −6,02 % |
| 1,80-2,20 | **−3,57 %** | −1,97 % | −5,32 % |
| 2,50-3,20 | — | −2,52 % | **−10,92 %** |

⏭️ El repartiment: **~3 punts són les càmeres**, **~2 els posa la composició
LDIC** a la corona interior —cada canal compon cada radi amb una barreja de
fotogrames diferent, que és el mecanisme del `research/104`— i **de 3 a 8 la
resta del cel**, creixent cap enfora, que és exactament el que ha de fer: a
3 R☉ el cel val 2,3 vegades la corona i restar-lo amplifica qualsevol error.

### 3.4 I els ~3 punts de càmera són ESPERATS

⛔ **Comparar el color de dos cossos en espai de càmera no vol dir res.** El
balanç de dia iguala **un espectre de llum de dia**, i la corona d'aquest
eclipsi és un continu solar endurit per l'extinció a massa d'aire ~6.

Amb la matriu de color de cada cos (convenció dcraw), `T = M_sony⁻¹·M_vixen`
prediu quin B/G hauria de llegir la Sony si totes dues veiessin **el mateix
color**:

| | predit per la matriu | mesurat | residu |
|---|---:|---:|---:|
| corona 1,1 R☉ | B/G 0,4436 (−13,4 %) | 0,4699 (−8,3 %) | +5,9 % |
| corona s (1,05-1,30) | 0,4278 | 0,4702 | +9,9 % |
| cel | 0,8645 | 0,8793 | +1,7 % |

⏭️ El signe i la major part de la magnitud del «−8,5 % de blau» **els prediu la
matriu**: no és un defecte d'un tren. El que queda és **error metamèric** de les
matrius d'Adobe sobre un espectre molt fora del seu disseny, i és més petit al
cel (+1,7 %) que a la corona (+5,9 a +9,9 %), que és el que ha de passar.

⚠️ **Conseqüència pràctica**: l'acord de color entre els dos trens té un **terra
de ~3 %** que no es pot baixar sense calibratge espectral, i cap dels dos no és
«el bo». I **el color de la Vixen i el de la Sony no es comparen mai en espai de
càmera sense la matriu**.

---

## 4. Deute 3 · la deriva fotomètrica

La raó `G_vixen(r) / G_sony(r)` hauria de ser **constant** de 1,2 a 4,2 R☉ —els
dos veuen la mateixa corona i el que canvia és l'obertura, que és un escalar—.

| | deriva 1,15-4,20 R☉ |
|---|---:|
| flat de cel | **13,51 %** |
| flat corregit pel dither | **7,43 %** |

⏭️ **La meitat era el flat**, i el guany és el més gran allà on el flat era més
dolent: a 3,9 R☉ la raó passa de 0,9624 a 0,9929.

### 4.1 El que queda NO és el nivell del cel

Prova conjunta (`un_sol_cel.py`): **un sol escalar** sobre el nivell de cel de la
Sony, i **dos símptomes independents**.

| f del cel de la Sony | deriva fotomètrica | desacord de B/G a 2,5-3,2 R☉ |
|---:|---:|---:|
| 0,91 | 74,75 % | **+0,35 %** |
| 0,95 | 44,07 % | −4,21 % |
| **1,00** | **7,43 %** | −10,92 % |
| 1,05 | 48,65 % | −20,42 % |

⛔ **El mínim de la fotometria és a f = 1,00 i el color només quadraria a
f = 0,91.** Els dos mínims cauen lluny: **no són la mateixa causa**, i el nivell
del cel ja és el que ha de ser per a la fotometria. Un desplaçament additiu
òptim només compra 0,9 punts més (7,43 → 6,55 %, amb d = −1,0 % del cel).

### 4.2 El que queda és estructurat

| R☉ | 1,15 | 1,37 | 1,63 | 1,94 | 2,12 | 2,52 | 3,01 | 3,58 | 3,91 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| raó normalitzada | **1,046** | 1,020 | 1,016 | 1,013 | 0,990 | **0,978** | 0,998 | 0,986 | 0,993 |

No és una deriva monòtona: és **un excés del +4,6 % a 1,15 R☉** —que enllaça amb
el dèficit de corona interior que el `research/114` va deixar obert per sota
d'1,12 R☉— i **una vall del −2,2 % a 2,1-2,5 R☉**, que cau just on l'exposició
més curta deixa de contribuir al compost (la capa de 0,01 s val fins a
2,55 R☉). Fora d'aquests dos punts, de 1,25 a 3,9 R☉ el recorregut és del
**4,3 %**.

---

## 5. Deute 4 · l'estriat fi

La hipòtesi a provar era la **quincunx del verd**: al mosaic Bayer el pla G és
una xarxa girada 45°, i amb el drizzle sobre fotogrames ditherats hauria de
deixar traça en diagonal. Si fos això, la família hauria de viure **al canal G i
no a R ni a B**.

⛔ **Refutada.** Excés de la família fina (λ 6-10 px), canal a canal, sobre la
mateixa dada i amb la mateixa mesura —l'excés sobre la mediana de la seva pròpia
longitud d'ona, que és adimensional i ja descompta que R, G i B tenen relacions
senyal/soroll molt diferents—:

| tren | R | G | B | G / mitjana(R,B) |
|---|---:|---:|---:|---:|
| Vixen | 7,49 | 7,85 | 6,57 | **1,12** |
| Sony | 6,13 | 4,59 | 5,53 | 0,79 |

**Hi és igual als tres canals.** No és el mosaic.

### 5.1 I «només de la Vixen» era massa fort

`estriat_dos_trens.py` comparava els dos trens **sense igualar la resolució**,
que és justament el que `jutge.py` sí que fa. Comprovat: passant la Vixen pel
mateix camí de remostreig que la Sony (×1,49 avall i amunt amb la mateixa
interpolació), l'excés **es queda al 101-102 %** — la mesura és una **raó a
longitud d'ona fixa** i per tant invariant sota un desenfoc isòtrop.

⏭️ O sigui que no era un artefacte de resolució, **però la Sony també el té**:
×4,05-4,88 contra ×6,57-7,85 de la Vixen sobre `CORONA`. El correcte és «**més
fort a la Vixen**», no «només de la Vixen».

### 5.2 Direcció: tangencial, no diagonal de sensor

Amb el tensor d'estructura sobre la banda λ 6-12 px (sense cap FFT, per evitar
vores), l'orientació dominant és a **73° de la radial a la Vixen i a 89° a la
Sony**: la família és **tangencial** —de la mateixa gent que els anells— i no una
diagonal fixada al sensor.

⛔ **Mecanisme obert**, amb tres hipòtesis eliminades: no és la quincunx del
verd, no és la resolució i no és una direcció de sensor.

⚠️ **Trampa nova, i em va picar**: partir l'anell en sectors i fer-hi una FFT
**no serveix**. La vora de la falca és una discontinuïtat dura dins de la caixa i
la seva fuita domina l'espectre: sortien «pics» de **×245** a 45,5° i 134,5°, que
són **les diagonals de la caixa**. Va a `trampes.md`.

---

## 6. Què queda obert

1. **L'escala fina que paga el segon apuntament** (1,8°: 0,909 amb 14
   fotogrames, 0,884 amb 27). No és el flat. La hipòtesi que queda és que
   barrejar dos apuntaments molt separats barreja dues PSF diferents del mateix
   objectiu; **no està provat**.
2. **L'excés del +4,6 % a 1,15 R☉** entre trens, que enllaça amb el `research/114`.
3. **La vall del −2,2 % a 2,1-2,5 R☉**, on la capa de 0,01 s deixa el compost.
4. **El terra de ~3 % del color entre trens**: només es baixa amb calibratge
   espectral dels dos cossos, i no el tenim.

---

## 7. Decisió de Pere: el mode de color MEMORIA queda DEPRECAT

*27 d'agost de 2026, vespre. Literal: «depreca el mode de color MEMORIA, seguim
amb ciència».*

El projecte segueix **només amb `CIENCIA`**: blanc adoptat = **el Sol de sobre
l'atmosfera (AM0)**, guany `(0,9302 · 1 · 1,1261)`. El que queda a la imatge és
l'**extinció de León** —més l'enrogiment propi de la corona F, les línies E i
els residus instrumentals—, i això és una afirmació física que el rebut declara
i que qualsevol pot desfer amb el vector d'extinció.

### Què s'ha fet, exactament

- `comu.MODES_COLOR` només té `CIENCIA`. `MEMORIA` passa a
  **`comu.MODES_DEPRECATS`**, sencer.
- **`Run.nou` refusa** arrencar un run `MEMORIA`, amb el motiu i la data
  escrits, i **abans de crear cap directori**. Comprovat:
  `cadena.py VIXEN MEMORIA` → *«el mode de color MEMORIA està DEPRECAT des del
  27-08-2026… Modes vius: ['CIENCIA']»*, i no queda cap carpeta òrfena.
- **`Run.obre` continua llegint-lo**: un run és immutable i el seu rebut ha de
  continuar tenint sentit. Verificat sobre
  `VIXEN_MEMORIA_20260826T155138Z`.
- `comparativa_modes.py` queda marcat com a **històric**: és la proveniència de
  la decisió, no una tria oberta.
- A l'`2-OUTPUT`: capçalera nova a `LLEGEIX-ME.md`, entrada a `TRIES_DE_PERE.md`
  i `DEPRECAT.md` dins de `VIXEN_MEMORIA/`. **No s'ha esborrat res.**

### Tres coses que NO s'han perdut, i per què

1. El **guany `(1,1528 · 1 · 1,0249)` és una mesura**, no una preferència: és el
   terme de càmera i vidre entre els dos trens, mesurat a 2,18-4,82 R☉ amb
   1,3 % i 2,2 % de dispersió. Esborrar-lo seria perdre una mesura.
2. El run vell existeix i **és immutable**. Un mode que no es pot llegir
   trencaria el seu rebut.
3. ⏭️ **El `DSC06991.ARW` no queda retirat.** Continua sent el **control extern**
   del color a cada run (`F3.control_testimoni_DSC06991`), i allà **mesura, no
   afirma**. El que s'ha deprecat és **renderitzar contra ell**, no
   comparar-s'hi. Al run `CIENCIA` aquest control marca **18,5 % de mediana**,
   i això no és un error: és, per disseny, la distància entre el blanc del Sol i
   el color d'aquell fotograma.

---

## 8. Estat de la «quarantena» de la Sony (pregunta de Pere)

⛔ **El nom de la carpeta enganya.** `0-ENTRADES/SONY-A7RIIIA/quarantena` (18
fotogrames, DSC06973-06990) **no són descarts**: és el **primer apuntament**, i
`totalitat` (14, DSC06991-07004) és el **segon**. El tall és el salt de muntura,
no la qualitat. `research/115` §1.

**Sí que es fan servir.** El tren `SONYTOT` llegeix les dues carpetes
(`carpetes_llum`) i el lliurament d'avui, `SONYTOT_CIENCIA_20260827T142411Z`,
en porta **27 de 32**, dels quals **15 vénen de `quarantena`**. El tren `SONY`
(14) és el que en prescindeix, i es conserva perquè mesura una cosa diferent.

### Els cinc que queden fora, un per un

| fotograma | exp | ovalitat del limbe | rms | veredicte |
|---|---|---:|---:|---|
| DSC06988 | 1 s | 3,72 px | 5,32 | mogut durant el salt |
| DSC06989 | 1/8 s | 4,87 px | 4,17 | mogut durant el salt |
| **DSC06990** | **8 s** | 0,52 px | 6,44 | ⛔ **destruït** (R ajustat 163 px) |
| DSC06991 | 1 s | 2,56 px | 2,04 | primer del segon apuntament, sense assentar |
| DSC06993 | 8 s | 3,60 px | 3,14 | ídem |

⏭️ **Mirant-los** (`2-OUTPUT/DOS_TRENS/QUARANTENA_els_cinc_exclosos.png`, cada
un al costat d'un BO de la mateixa exposició, fotograma **sencer**):

- **DSC06990 és el pitjor de tots i el criteri deia el contrari.** El disc de la
  Lluna hi surt com una **llenca horitzontal**, no com un disc: l'escombrada és
  de l'ordre del radi lunar. L'ajust del limbe li donava «ovalitat 0,52 px»
  perquè va enganxar-se a aquella llenca i li va posar un cercle de R = 163 px.
  ⚠️ **Una ovalitat baixa sobre un objecte que no és el que creus és el pitjor
  fals negatiu possible.**
- Els altres quatre **es veuen bé a ull**. El que sembla un desplaçament al
  06991 i al 06993 **és el canvi d'apuntament**, no un defecte.

### Què costa i què compraria readmetre'ls

El run d'avui té **un sol fotograma a 1 s i un sol fotograma a 8 s**:

```
LDIC 1s (1 fot.) · val 1,70-12,84 R☉ · cobertura G 81,9 %
LDIC 8s (1 fot.) · val 2,75-12,87 R☉ · cobertura G 77,7 %
```

I entre els exclosos hi ha **dos de 8 s** (06990, 06993) i **un altre d'1 s**
(06988). O sigui que el graó que sosté **tota la corona exterior de la Sony**
descansa en un únic fotograma, sense possibilitat de rebutjar ni un raig còsmic.

⏭️ **El candidat clar és el DSC06993**: 8 s, escombrada de ~3-4 px (10-13 ″), i
la seva capa només serveix de **2,75 R☉ cap enfora**, on 3 px no es veuen.
Doblaria el graó de 8 s.

⚠️ **El DSC06991 és cas a part i no s'hauria de readmetre encara que fos net**:
és el **testimoni de Pere** i fa de **control extern del color** a cada run
(`F3.control_testimoni_DSC06991`). Un control que entra al producte deixa de
ser un control.

⚠️ Un intent de mesurar l'escombrada ajustant quin desenfoc direccional
converteix el fotograma bo en l'exclòs **no va funcionar**: el residu només
baixa del 0,1 al 2,7 % perquè la comparació la domina el nucli saturat, i al
06990 —que la imatge ensenya destruït— en donava 1,75 px. **La imatge va decidir
i l'instrument no.**

### 8.1 La decisió de Pere, i el que ha passat en aplicar-la

*27-08, vespre, després de mirar-los un per un:* «DSC06988 a DSC06990 estan
efectivament inservibles… els altres jo els veig perfectament bé… de DSC06991
en endavant jo els veig tots perfectament bé i és una pena que no els
aprofitem, pensa que cada foto compta».

**`0-ENTRADES/SONY-A7RIIIA` queda reorganitzat**, amb els 32 fotogrames
verificats un per un abans i després (mateix SHA-256, cap perdut):

| carpeta | què hi ha | la llegeix |
|---|---|---|
| ⛔ `quarantena/` | — | **desapareix** |
| `descentrats/` | 15 · DSC06973-06987, **primer apuntament** | `SONYTOT` |
| `totalitat/` | 14 · DSC06991-07004, **segon apuntament** | `SONY` i `SONYTOT` |
| `inservibles/` | 3 · DSC06988, 06989, 06990 | **ningú** |

`exclou` queda buit: el que no serveix viu a una carpeta que no es llegeix. Un
nom de carpeta que menteix costa més que una llista d'exclusions. Les dues
carpetes noves porten el seu `LLEGEIX-ME.md`, i el manifest de cada run hasheja
també `inservibles/`: consta que existeixen i que no s'han fet servir.

**Run `SONYTOT_CIENCIA_20260827T171516Z`, 29 fotogrames, 17,6 min, totes les
portes PASSA.** El que compren els dos que Pere ha fet entrar:

| | 27 fot. | **29 fot.** |
|---|---:|---:|
| capa **1 s** | 1 fot., cobertura G 81,9 % | **2 fot., 95,0 %** |
| capa **8 s** | 1 fot., cobertura G 77,7 % | **2 fot., 91,1 %** |
| pes del compost a 1,7-2,7 R☉ | — | **×1,12 a ×1,47** |
| pes del compost a >2,9 R☉ | — | **×1,36 a ×1,56** |
| estructura × Vixen 90° | 0,994 | 0,994 |
| estructura × Vixen 30° | 0,997 | **0,998** |
| estructura × Vixen 12° | 0,988 | **0,992** |
| estructura × Vixen 4,5° | 0,973 | **0,978** |
| estructura × Vixen 1,8° | 0,884 | **0,889** |
| control del color (F2.4) | 0,162 % | **0,137 %** |
| deriva fotomètrica 1,15-4,20 R☉ | **7,43 %** | 9,53 % |

⏭️ **Pere tenia raó i el jutge extern ho diu**: amb els dos fotogrames dins,
l'acord d'estructura amb l'altre instrument **millora a quatre de les cinc
escales** i el graó de 8 s —que sostenia tota la corona exterior amb **un sol
fotograma**— passa a tenir-ne dos, amb un 56 % més de pes.

⛔ **I té un preu, localitzat i mesurat.** Comparant els dos runs entre ells, el
nivell de la corona exterior **baixa un 3,4 % a partir de 3 R☉** i puja un 2 %
a 2,5-2,7, o sigui un graó a l'aresta on comença la capa de 8 s (2,80 R☉).
Contra la Vixen això es llegeix com una deriva de 7,43 → 9,53 %.

⚠️ **No està atribuït.** Dues explicacions compatibles amb la mesura: (a)
l'escombrada del 06993 redistribueix llum del nucli brillant cap enfora, o (b)
el 06993 és de t ≈ 92 s i el cel havia baixat, i **a 3 R☉ el cel val 2,3 vegades
la corona**, o sigui que qualsevol canvi de la barreja temporal hi surt
amplificat (§3.3). La segona és més probable i és **la mateixa debilitat que ja
teníem declarada**, no una de nova.

⏭️ **S'adopta el run de 29** —el jutge independent millora i el producte fusionat
no és una mesura (D1)—, amb la incertesa del nivell exterior declarada. El
remei barat, si algun dia molesta: pujar l'aresta interior de la capa de 8 s
per damunt del graó.

---

## 9. Els runs es numeren, i els fallits marxen

*27-08, nit. Pere: «torno a tenir lio en l'estructura de carpetes… pots fer que
cada run tingui un número cronològic?… esborra també els runs fallits».*

### Què ha canviat

- **Un run es diu `NNN_TREN_COLOR_segell`**, amb `NNN` cronològic i **comú a
  tots els trens**: ordenar per nom és ordenar per temps, i el número més alt és
  sempre l'últim. ⛔ **El segell no marxa**: és el que lliga el run amb els
  documents que el citen; el número és per a l'ull.
- **Set runs incomplets esborrats** (`_FALLIT` i `_AVORTAT`), 36 GB. `1-RUNS`
  passa de 228 a **192 GB** i de 21 carpetes a **14**. Cap run bo tocat.
- **Les carpetes de `2-OUTPUT` porten el MATEIX número**: `NNN_TREN_COLOR`.
  `2-OUTPUT/014_SONYTOT_CIENCIA/` ve del run `1-RUNS/014_SONYTOT_CIENCIA_…/`
  sense haver de mirar res. ⛔ Amb això **desapareix el sufix `_anterior`**: la
  còpia d'abans es queda amb el seu número, que ja diu que és més vella. Se'n
  conserven les **dues últimes** de cada tren+color i la cadena diu quina
  retira. Cada carpeta porta a més un `DE_QUIN_RUN_VE.txt`.
- **Mapa de carpetes generat des del disc**:
  `2-OUTPUT/MAPA_DE_CARPETES.md`, per `mapa_carpetes.py`. No s'escriu a mà, o
  sigui que no pot quedar desfasat.

### El detall que ho feia arriscat

Posar un número al davant hauria trencat **totes** les eines alhora: cadascuna
tenia la seva còpia de `startswith(f"{tren}_{mode}_")`, i disset fitxers més
portaven la ruta absoluta d'un run concret escrita a pèl.

⏭️ **Cura**: un sol lloc que sap com es diu un run. `comu.runs_llista()`,
`comu.darrer_run()`, `comu.numero_de()`, `comu.sense_prefix()` i
`comu.run_per_segell()` —aquesta última resol un run **pel segell**, que és el
que citen els documents, tant si porta número com si no—. Les rutes literals
dels disset fitxers s'han reescrit perquè es resolguin pel segell.

⚠️ **Lliçó**: una convenció de noms repetida a onze llocs no és una convenció,
és onze còpies esperant divergir. El dia que la vols canviar, ho descobreixes.

---

## 10. Només C2: la Lluna torna a ser rodona

*27-08, nit. Pere: «oblidem-nos del requisit de fer la simetria amb els dos
contactes, treballarem només en C2, que no m'agrada el resultat de posar C2 i
C3 i deformar la Lluna».*

⏭️ **Tenia raó i el motiu estava escrit al codi des del primer dia.** El llenç va
centrat al **Sol** i la Lluna hi llisca ~28,5 px entre C2 i C3, o sigui que unir
els dos extrems deixa com a negre la **intersecció dels dos discos lunars** —una
llentia, no un cercle—. El comentari de `f4.protuberancies` ja ho deia
(«el negre que en queda és la INTERSECCIÓ dels dos discos lunars, no un
cercle»); el que ningú havia fet era **mirar-ho**.

**Constant nova i declarada**: `comu.CONTACTES_AL_PRODUCTE = ("ingress",)`.

- `f4.protuberancies` només compon els contactes declarats, i anota els altres
  al rebut sota `fora_del_producte`: **que no surtin al producte no vol dir que
  no s'hagin vist**.
- El **nom de la capa surt dels grups que hi entren de veritat**
  (`09 PROTUBERÀNCIES · C2 (ingress) · Aclarir`), no d'un literal. Un nom de capa
  que promet C3 quan no hi ha C3 és un defecte que sobreviuria a la decisió.
- ⛔ **La capa de contactes de C3 no es toca**: el segon anell de diamant viu al
  seu propi PSB, com a capa a part, i allà no deforma res.

Runs refets: **015 (Vixen)** i **016 (SONYTOT)**, totes les portes PASSA.
Vista: `2-OUTPUT/DOS_TRENS/PROTUBERANCIES_C2_contra_C2C3_*.png`.

⚠️ **Conseqüència per al tren `SONY`** (14 fotogrames, només el segon
apuntament): no té cap fotograma d'ingress, o sigui que **es queda sense capa de
protuberàncies**. El `SONYTOT` en té sis i no li passa.

---

## 11. Les tres marques de Pere al `capes_LDIC`, i què són

*27-08, nit. Pere marca en magenta tres coses sobre
`Eclipsi_2026_SONYTOT_CIENCIA_capes_LDIC.tif`.* Localitzades pel color —magenta
és **el verd com a mínim clar**, cosa que ni la corona (taronja) ni el cel
(blau fluix) fan mai—: `dos_trens_jutge/marques_del_tiff.py`. Vista:
`2-OUTPUT/DOS_TRENS/MARQUES_PERE_SONYTOT_localitzades.png`.

### Marques 1 i 2 · les dues costures de cobertura

Dues línies verticals, a **+6,22 R☉** i **+8,65 R☉**. Cauen **exactament** sobre
els dos esglaons del mapa de pes (+6,21 i +8,59 R☉):

| | pes | LDIC | CORONA | soroll |
|---|---:|---:|---:|---:|
| esquerra de +6,21 R☉ | 50,1 | 1244,5 | 99,3 | 2,37 |
| dreta | 27,3 | 1204,2 | 87,7 | 3,06 |
| **salt** | **×0,55** | **−3,2 %** | **−11,6 %** | **+29 %** |

⏭️ És la costura que `research/115` §16 havia **declarat però no ensenyat mai**:
a partir de +6,21 R☉ només hi contribueix un apuntament i a partir de +8,59 no
hi ha dada. El salt de nivell és del **−3,2 %** al compost i es converteix en
**−11,6 %** un cop restat el cel, perquè allà el cel val ~9 vegades la corona
(§3.3 una altra vegada).

### Marca 3 · un GHOST de l'objectiu, i queda identificat

Una taca de **75×75 px** a **r = 3,00 R☉, θ = 292°**. Mesurada al compost: un
**disc perfecte de 27,2 px de radi** (58 ″, 0,062 R☉), vora dura, uniforme, amb
**G +47 %, R +56 % i B +141 %** sobre el fons local, i **el mapa de pes no la
veu** (+0,2 %).

Set proves que la tanquen:

1. ⛔ **No és el cel**: la **Vixen no hi té res** (+0,1 %), als deu runs.
2. ⛔ **No és de la Sony sencera**: el tren `SONY` (només el segon apuntament)
   tampoc (+0,3 %). Hi és **només** quan entren els `descentrats`.
3. ⏭️ **Hi és a TOTS els fotogrames del primer apuntament** (+47,8 a +51,1 %) i
   a **cap** del segon (±0,5 %), remapats amb el codi de la cadena.
4. ⏭️ **És independent de l'exposició** —el mateix +48 % de 0,01 s a 8 s—, o
   sigui una **fracció fixa de la llum**, no llum afegida.
5. ⛔ **No és brutícia**: els flats són plans en aquell píxel (+0,20 %).
6. ⏭️ **És al centre òptic**: el disc és al sensor a (2660, 4000) i el centre de
   la zona activa és (2660, **3984**) — **16 px, el 0,17 % de la diagonal**.
7. ⏭️ **I això explica per què només el veu un apuntament**: al primer, el Sol
   és a **878 px de l'eix = 2,97 R☉**, i el ghost cau **a la corona**; al segon,
   el Sol és a **145 px = 0,49 R☉** i el ghost cau **darrere de la Lluna**.

⏭️ **Veredicte: un reflex intern de l'objectiu, sobre l'eix.** Un ghost
desenfocat forma la imatge del **diafragma** —per això és un disc uniforme de
vora dura—, val una fracció fixa de la llum de l'escena i el **domina el blau**,
que és el que fan els tractaments antireflex.

⏭️ **Cura proposada, no aplicada**: treure del pes un disc de ~25 px de radi al
**centre òptic de cada fotograma**. On el ghost molesta —el primer apuntament—
el segon hi té dada bona, i on el segon el té, ja hi ha la Lluna. **No costa
res i no toca la resta.** Falta fer-la i jutjar-la.

---

## 12. `--reusa`: les fases 0, 1 i 2 no es tornen a calcular

*27-08, nit. Pere: «a cada run nou no fa falta que refacis les primeres fases,
el VIXEN ja fa LDIC molt bé».*

```bash
python3 cadena.py VIXEN CIENCIA --reusa          # de l'últim run del tren
python3 cadena.py VIXEN CIENCIA --reusa 015      # d'un run concret
```

Les fases **0 (calibració), 1 (registre) i 2 (composició LDIC)** es **munten per
enllaç dur** des del run d'origen i es refan només la **3 (filtres)**, la **4
(PSB)** i la **5 (vistes)**.

| | run sencer | amb `--reusa` |
|---|---:|---:|
| temps | **25,8 min** | **12,6 min** |
| bytes nous al disc | 14 GB | **8 GB** (6,1 GB són enllaços) |

⏭️ **I el resultat és el mateix, bit a bit.** El `DETALL_PASSA_ALT.npy` del run
017 —calculat de nou a partir de la fase 2 enllaçada— és **idèntic** al del run
015, que la va calcular des dels RAW. Això és la prova que reusar no és
aproximar.

### Les tres coses que ho fan honest

1. ⛔ **Falla tancat si el codi ha canviat.** Si `comu.py`, `f0.py`, `f1.py`,
   `f2.py` o una taula de constants no són byte a byte els del run d'origen, es
   refusa. Reusar productes fets amb un altre codi seria mentir al manifest.
   `--igualment` ho força i llavors el manifest ho declara.
2. ⛔ **Falla tancat si han canviat les ENTRADES.** Es compara el SHA-256 de
   cada fotograma amb el que el run d'origen va hashejar. Si algú ha mogut un
   fitxer de carpeta —cosa que avui mateix hem fet— les fases 0-2 ja no valen.
3. ⏭️ **Queda escrit.** El manifest del run nou porta un bloc `reusat` amb
   l'origen, els fitxers enllaçats i els hashes del codi que va produir les
   fases reusades, i hi ha un rebut `F0-2_REUSADES.json`.

⚠️ **Enllaços durs, no còpies**: els fitxers d'un run no es modifiquen mai un
cop escrits, o sigui que compartir l'inode és segur i costa zero. Si esborres el
run d'origen, el nou continua sencer. ⛔ El que **no** s'ha de fer és editar un
fitxer de dins d'un run: amb enllaç dur, l'editaries als dos alhora. Ja no es
feia; ara hi ha un motiu més.

---

## 13. Les ratlles diagonals del passa-alt: eren els CALAIXOS del perfil

*27-08, nit. Pere mira el passa-alt de prop al PSB i marca en lila unes **ratlles
diagonals** regulars: «això em contamina molt el filtre».*

### No són diagonals: són ANELLS

La direcció és sempre la **perpendicular al radi** i el període **creix amb el
radi**. A 4,5 R☉ al nord-est l'anell hi passa a 45°, i per això semblen ratlles
diagonals.

| radi | λ predita pels calaixos | λ mesurada | direcció |
|---|---:|---:|---|
| 1,8 R☉ | 3,5 px | 4,8 px | radial |
| 2,6 R☉ | 5,1 px | 7,0 px | radial |
| 3,6 R☉ | 7,1 px | 9,5 px | radial |
| 5,0 R☉ | 9,9 px | 12,9 px | radial |
| 7,0 R☉ | 13,8 px | 25,8 px | radial |

⏭️ **La raó mesurada/predita valia 1,33 = 1200/900**, i això va identificar el
culpable: no és `anivella` (1200 calaixos) sinó **`perfil_azimutal` (900)**.

### La causa, en una línia de codi

`perfil_azimutal` tornava **`mu[idx]`**: el perfil radial **indexat pel
calaix**, o sigui una **escala de 900 graons en radi**. En restar-lo del camp
en log, cada graó queda com un **anell de vora dura**, i el passa-alt i l'MGN
—que són justament els filtres que conserven les vores— el conserven sencer.
`anivella` feia el mateix amb els seus 1200.

⚠️ El perfil **ja es suavitzava** (nucli de 14 calaixos). No servia de res:
suavitzar el perfil no treu els graons de **com s'aplica**.

### On era, i on és ara

Potència a la freqüència dels calaixos (1 = res):

| filtre | abans (900) | després | abans (1200) | després |
|---|---:|---:|---:|---:|
| **PASSA_ALT** | **×937** | **×1,97** | 1,56 | — |
| **MGN** | **×4021** | **×1,61** | 0,58 | — |
| NRGF | ×9,03 | ×0,98 | 0,87 | — |
| RADIAL | ×0,01 | ×0,22 | 0,22 | — |

⏭️ El `RADIAL` no en tenia mai: treballa en polars i qualsevol cosa que sigui
funció només del radi hi desapareix per construcció.

### La cura i la porta

**La cura**: tornar i aplicar el perfil **interpolat linealment entre centres de
calaix** en lloc del valor del calaix. És exacte al centre, continu a tot arreu,
i no canvia què corregeix la funció — només com ho reparteix. Dues funcions,
`perfil_azimutal` i `anivella`.

**La porta nova, H1b · `anells_de_calaix`**: la potència del detall a la
freqüència de cada graella de calaixos (900 i 1200), contra les freqüències
veïnes. Va al rebut de cada filtre.

⛔ **Per què la porta H1 no ho havia vist mai**: H1 mesura el **nivell** mitjà
de cada anell, i una escala de graons petits el compleix perfectament (0,010 al
passa-alt). **Un anell és una FORMA i la porta mirava un NIVELL** — exactament
la lliçó del `research/111`, que ara torna a picar en un altre lloc. La cura és
la porta nova, no afluixar la vella.

Run **018**, 13,1 min amb `--reusa`. Totes les portes PASSA.

---

## 14. Norma de Pere: el fons dels filtres no pot ser estàtica

*27-08, nit. Pere: «tots els filtres tenen encara un fons molt sorollós, molt
diferent dels passa-alt que faig manualment… hi ha molta estàtica i brutícia al
fons».*

### El fet, mesurat

La banda fina (λ<5 px, que a la corona només pot ser soroll blanc) contra la
banda estructurada, al que es lliurava (run 018): **0,19-0,42 dins** i
**1,0-1,6 de 3 R☉ enfora** — a fora, l'estàtica igualava o superava el senyal.
⛔ L'atenuació per S/N que ja hi havia no ho pot curar: **atenua soroll i
estructura per igual**. L'única cosa que separa soroll blanc d'estructura és
**promitjar**.

### La cura: la resolució segueix el S/N (`f3.suavitza_sn`)

La filosofia de l'ACHF de Druckmüller, autocalibrada des del mateix camp, sense
cap mapa extern: `n_loc` = rms local de la banda fina; `s_loc` = rms local de la
banda mitjana neta de la fuita β=0,0128 del soroll blanc (mesurada amb soroll
sintètic sobre els mateixos nuclis); **σ(x) = n/(2√π·t·s)**, que és la σ exacta
perquè el soroll residual quedi a t vegades l'estructura — la fórmula 1/(2σ√π)
queda validada contra soroll sintètic al 1 %. Aplicat amb piràmide gaussiana i
barreja contínua per píxel; cap llindar dur, cap circumferència (el mapa és de
DADA). Calibratge: **t=0,18, una passada, σ màx 16 px**; el σ p90 exterior surt
de 2,4-5,8 px, per sota dels ~15 px de l'estructura real més fina (0,5° a 4 R☉,
`research/82`).

### Resultat (fina/mitjana; l'objectiu és el nivell d'on hi ha senyal, ~0,2)

| anell | PASSA_ALT | NRGF | MGN | RADIAL |
|---|---|---|---|---|
| 1,3-1,6 R☉ | 0,21 → **0,21** | 0,16 → **0,16** | 0,42 → **0,33** | 0,14 → **0,14** |
| 3,0-3,5 | 1,24 → **0,21** | 1,26 → **0,21** | 1,48 → **0,19** | 0,50 → 0,36 |
| 5,0-5,5 | 1,23 → **0,31** | 1,09 → **0,51** | 1,58 → **0,20** | 0,47 → 0,39 |
| 7,0-7,5 | 1,01 → **0,40** | 0,76 → **0,54** | 1,17 → **0,57** | 0,58 → 0,52 |

⏭️ **On hi ha senyal no es toca res** (fila de dalt), i el fons exterior baixa
al nivell de la corona interior. El RADIAL ja n'hi tenia poc: el seu suavitzat
radial ja promitjava.

Run **019** (12,8 min amb `--reusa`), totes les portes PASSA, H1 ≤0,014 i H1b
0,25-2,04. El rebut porta el bloc `suavitzat_SN` amb σ mediana/p90 i % de camp
tocat per filtre.

⚠️ **Límits declarats**: NRGF i MGN es queden a 0,51-0,57 a 7-7,5 R☉ (el soroll
hi és tan gran que caldria σ > 16 px, i allà s'estimaria més no inventar); i el
suavitzat és **presentació** — cap mesura fotomètrica no passa pels camps de
detall.

---

## 15. Les dues línies «recurrents» del passa-alt i l'MGN (28-08, matinada)

*Pere marca en lila dues línies al passa-alt del Vixen: «que coi són aquests dos
artefactes? recurrents des de fa molt temps».* Una a **y=5507** (r 2,52 R☉,
~430 px, quasi horitzontal, amb aspecte de cantonada) i una a **y=4653**
(r 3,70 R☉, horitzontal EXACTA a −0,04°, el «fosc gran» que travessa el camp).

### La cadena de proves

1. **Neixen a la fase 2** (són al compost LDIC a −0,5 % i −1,1 %), amb el mapa
   de pes **perfectament pla** (0,000 %): no són cap costura ni cap graella.
2. **Hi són a TOTS els fotogrames ben exposats**, amb contrast constant
   (−0,5 ± 0,05 % de t=25 a t=106): una cosa **estàtica respecte del Sol**
   durant tota la totalitat.
3. ⏭️ **LA SONY LES VEU TOTES DUES**, al mateix lloc del cel i amb el mateix
   signe (y5507: −0,36 % · y4653: −1,44 % al seu LDIC). Dos instruments amb
   òptica, sensor, muntura i apuntament diferents: **no és cap artefacte de
   pipeline**.
4. ⏭️ **El color del dèficit és EXACTAMENT el de la corona** (R/G 1,77-1,80 ·
   B/G 0,47-0,50, contra 1,72-1,75 · 0,50-0,53 de la corona local), i **no** el
   de la llum total (1,19-1,40 · 0,69-0,79). ⛔ Això descarta també la
   transparència compartida: un vel de cirrus absorbiria corona I cel, i el
   dèficit tindria color de llum total. La llum que falta és **només llum
   coronal**.

### Veredicte

**Són estructura REAL de la corona**: carrils foscos (voids) entre streamers.
El de y=4653 apunta gairebé radialment —el buit clàssic entre dos streamers— i
el de y=5507, amb la seva cantonada, és la vora de l'arcada del complex sud.
⚠️ **Que semblin artificials és culpa nostra en un sentit només**: el passa-alt
i l'MGN conserven les vores, i amb el fons ara net (§14) aquests carrils
queden nítids com mai. L'horitzontalitat exacta del de 3,7 R☉ és una
coincidència que enganya — per això calia la cadena de proves sencera i no
l'aspecte.

⛔ **No es toca res.** Cap cura: esborrar-los seria esborrar corona. Vista:
`2-OUTPUT/DOS_TRENS/MARQUES_PERE_les_dues_linies_als_DOS_trens.png`.

⚠️ De la cacera n'ha sortit un dubte de metrologia meu (el contrast del
producte CORONA contra el del LDIC no quadrava amb el CEL suau entremig; les
dues funcions de mesura ad-hoc no deien el mateix) — sense conseqüències per al
veredicte, que penja de les proves 2-4, mesurades cadascuna amb una sola
funció aplicada per igual als dos costats.

### 15.1 · L'arbitratge de Brno (28-08): Pere tenia raó a mitges — i jo també

*Pere: «si fossin reals, les imatges de Druckmüller les contemplarien també».*
Exacte. És el jutge que el §15 no havia passat, i **parteix el veredicte**:

| línia | Brno 800 | 200 | 400 | 530 | veredicte |
|---|---:|---:|---:|---:|---|
| y4653 (r 3,70) | **−30 % (t 30)** | **−19 % (t 39)** | **−23 % (t 41)** | **−38 % (t 34)** | ⏭️ **CORONA REAL** |
| y5507 (r 2,52) | −1,7 % (t 1,7) | −0,6 % | −1,0 % | −0,3 % | ⛔ **NO és corona** |

El processat de Brno amplifica les estructures reals ×17-35 (calibrat amb la
de 3,70): si la de 2,52 fos corona al contrast que mesurem, allà sortiria a
−9/−18 %. Surt a −0,3/−1,7: **queda exclosa amb marge ×10**.

**I aleshores què és?** Als fotogrames crus de la Sony hi és **als dos
apuntaments** (mediana −0,41 % i −0,50 %), amb el Sol a zones del sensor
separades 749 px: és a la **llum que arriba al nostre lloc**. Estàtica respecte
del Sol tota la totalitat, recta, ~15,5′ de llarg visible: una **franja
d'extinció local** — un contrail o filament de cirrus alineat amb el flux en
alçada (que avança al llarg de si mateix i per això sembla estàtic). ⚠️ El test
de color del §15 (que deia «color de corona») queda **desautoritzat**: la seva
metrologia ja estava marcada com a inconsistent, i Brno mana.

⛔ **Lliçó de mètode, la grossa**: l'acord entre els nostres dos trens **no pot
distingir corona d'atmosfera local**, perquè **comparteixen el cel**. El
confusor ja estava documentat (`research/103` §jutge, `research/106`), però
aquí és la primera vegada que m'hauria fet declarar «corona real» una franja
de cirrus. **El jutge d'això és un compost d'UN ALTRE LLOC.**

**Conseqüència per al producte**: la línia de r 2,52 R☉ és a la dada dels dos
trens i és **atmosfera nostra**; cap cura automàtica honesta (és estàtica:
degenerada amb la corona per a tot el que no sigui un altre observatori). Queda
**declarada**; treure-la és una decisió de retoc de Pere. La de r 3,70 és
corona i no es toca. Vista: `2-OUTPUT/DOS_TRENS/MARQUES_PERE_arbitratge_BRNO.png`.

### 15.2 · El guardrail (28-08, demanat per Pere: «fes els ajustos necessaris»)

**`research/tools/auditoria_estructura/es_corona.py`** — la regla del §15.1,
mecanitzada perquè no depengui de recordar-la:

```bash
python3 es_corona.py --seg H 5507 3440 3850     # ÉS corona això?
python3 es_corona.py --prova                    # autotest
```

Tres columnes, i la tercera **obligatòria**: (1) els dos trens, (2) la
significància contra un **nul honest** —el mateix segment girat a 36 azimuts
aleatoris del mateix radi, a la mateixa imatge, o sigui autocalibrat i sense
cap factor d'amplificació entre processats—, i (3) **els quatre composts de
Brno** pel registre del `research/114`. Les z dels dos trens es combinen
(Stouffer) exigint el mateix signe.

| veredicte | condició |
|---|---|
| ⏭️ CORONA REAL | trens coherents (z comb ≥ 2,5) **i** Brno mediana \|z\| ≥ 3, mateix signe |
| ⛔ NO ÉS CORONA | trens coherents però Brno mediana \|z\| < 1,5 → llum del NOSTRE lloc |
| INDECÍS | qualsevol altra cosa — i **mai** es pot declarar corona sense Brno |

**Verificat**: reprodueix els dos casos reals (r 3,70 → CORONA REAL amb z de
Brno −3,3/−16,4; r 2,52 → NO ÉS CORONA amb Brno a ±0,7) i passa l'autotest
(una línia sintètica del −3 % injectada NOMÉS als dos trens surt NO ÉS CORONA;
un lloc buit no dona cap veredicte fort).

⛔ **La norma que en penja**: cap declaració «és corona real» —meva ni de cap
altra sessió— sense el veredicte d'aquest instrument o l'equivalent manual amb
un compost d'un altre lloc. Escrita a `trampes.md` i a la memòria.
