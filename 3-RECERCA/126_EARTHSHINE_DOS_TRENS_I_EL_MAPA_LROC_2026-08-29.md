# 126 · L'earthshine dels DOS TRENS, i el mapa de la NASA hi diu que sí

**29 d'agost de 2026.** Ordre de Pere: (1) no fabricar res — «no pintis
estrelles que haurien de ser allà d'acord amb el plate-solve; el plate-solve
el tenim de comprovació, perquè identifiquis on són»; (2) fer una imatge de
mida real de l'earthshine **apilant les imatges de més d'1 s de la Sony amb
les de més de 9 s del Vixen**, amb tots els moviments de la Lluna i de les
dues muntures resolts; (3) tornar a fer la correlació amb les textures de la
NASA. ⏭️ **I n'ha sortit la detecció, amb el mapa d'albedo confirmant-la a
7,0σ**, cosa que rectifica el veredicte negatiu del `research/125` §3 bis.

## 1. Què va fallar el 28 i per què ara surt

El 28 es va mirar **només la Sony**, i pitjor: **els cinc fotogrames barrejats
en un sol apilat**. El segon apuntament porta un vel de llum escampada
gegant (residu **40,2 comptes** contra 5,7 del primer) i s'empassava el
senyal. Amb els fotogrames separats per apuntament i el Vixen a taula, el
senyal hi és i és inequívoc.

## 2. L'apilat conjunt: el marc lunar comú

Els 8 fotogrames —Vixen 3 × 10 s (572A2982-84) i Sony 2 s×3 + 8 s×2— aterren
al **mateix marc lunar**: l'origen és el centre de la Lluna al llenç V16
(6465,40 · 6752,63), on cau la Lluna de DSC06993 al muntatge de Pere.

| | Vixen VSD90SS + R6 III | Sony 300 GM + A7RIIIA |
|---|---|---|
| fotogrames | 3 × 10 s | 2 s×3 + 8 s×2 |
| escala del sensor | 2,1495″/px (**1:1 amb el llenç**) | 3,2020″/px |
| pa_north | 57,195° | 90,270° |
| Lluna | 455,5 px de radi | 305,8 px |
| moviment resolt | Lluna 0,581″/s + deriva de muntura per fotograma | + **rotació de camp +7,86′** del salt |

⏭️ **Dues comprovacions independents diuen que la geometria és bona:**

- els dos apilats lunars **s'alineen a (−0,07, +0,01) px** (correlació de fase);
- el quocient de nivells Sony/Vixen surt **3,13 · 3,10 · 3,04** per canal, i la
  predicció purament geomètrica —obertura (107/90)² × àrea de píxel 1,49²—
  val **3,13**. La fotometria dels dos trens quadra sense tocar res.

## 3. El producte: pesos mesurats, cap fotograma llençat

El vel de llum escampada es resta amb un model declarat ABANS de mirar el
mapa: perfil radial per anell + polinomi 2D de grau 4, dins de r < 0,90 R☾.
Els pesos **no els tria ningú**: per a cada component es mesura el soroll amb
la dispersió entre els seus propis fotogrames, i el senyal lunar amb les
covariàncies creuades entre components independents
(s_i² = cov(i,j)·cov(i,k)/cov(j,k)).

| component | rms | gra | senyal | no-senyal | pes |
|---|---:|---:|---:|---:|---:|
| Vixen 3 × 10 s | 5,51 | 0,43 | 5,80 | 0,43 | **97,8 %** |
| Sony apuntament 1 (8 s + 2 s) | 5,74 | 0,81 | 5,06 | 2,72 | 2,2 % |
| Sony apuntament 2 (8+2+2 s) | 40,22 | 2,86 | 2,99 | 40,11 | 0,01 % |

⏭️ **La prova que no depèn de cap model**: el Vixen i el primer apuntament de
la Sony —dos telescopis, dues càmeres, dos apuntaments i dues òptiques
diferents— **coincideixen a r = +0,928** sobre la superfície lunar. El segon
apuntament hi és a 0,08: el seu vel no és senyal.

## 4. El mapa de la NASA: la validació, i res ajustat

Mapa: **LROC WAC color poles 4k (NASA SVS 4720)**, projectat ortogràficament.
⛔ **L'orientació NO s'ajusta, es prediu**: la libració i l'angle de posició
del pol lunar surten de l'efemèride (de421 + model de rotació IAU/WGCCRE 2009
amb els 13 termes E) i el nord del llenç surt **de les estrelles del catàleg**
—el plate-solve fent exactament la feina que Pere li assigna—.

- libració sub-observador: **lon +3.61° · lat -0.25°**
- angle de posició del pol lunar: **+16.79°**
- orientació del llenç amb 85 estrelles: escala **2.1510″/px**
  (declarada 2,1495: acord del 0,07 %), nord a -45.51°

| producte | r amb LROC | control nul | z |
|---|---:|---:|---:|
| Vixen sol (3 × 10 s) | **+0,798** | −0,066 ± 0,123 | 7,0σ |
| Sony apuntament 1 (2 f) | **+0,745** | −0,061 ± 0,132 | 6,1σ |
| Sony apuntament 2 (3 f) | +0,063 | −0,009 ± 0,083 | 0,9σ |
| **DOS TRENS (8 fotogrames)** | **+0,792** | −0,070 ± 0,123 | **7,0σ** |

Control nul: el mateix mapa **girat** de 40° a 320° cada 10°. ⛔ Els girs de
menys de 40° NO són un nul —a 10° el mapa encara se solapa amb ell mateix i
dona r = 0,51—: és una trampa que cal declarar.

⏭️ **I la comprovació que ho tanca: l'escombrada fina d'orientació té el màxim
exactament a 0°**, la predicció de l'efemèride (r cau a +0,29 a −16° i a
+0,19 a +16°). No hi ha cap paràmetre lliure que hagi trobat el senyal: el
senyal era on l'efemèride deia.

**Amplitud física**: nivell del disc 1528 comptes, estructura lunar rms
**5,52 comptes = 0,36 % del disc**. Coherent amb la cota del `research/125`
(≲1,5 %) i amb l'extinció ×11 amb el Sol a 9,1°.

## 5. Dos defectes propis caçats pel camí

⛔ **El pic fabricat al centre del disc.** El perfil radial per anells deixava
a **zero** els anells amb menys de 40 px —els més interiors—, o sigui que al
centre no es restava res i hi sortia un pic de **253 comptes que no és a cap
fotograma** (als fotograms individuals hi ha 6-28). Cura: interpolar el perfil
als anells buits. Regla: *un perfil per calaixos ha de tenir valor a TOTS els
calaixos, també allà on no hi ha estadística*.

⛔ **El criteri creuat entre trens NO serveix per triar el model de vel**: els
dos trens miren la MATEIXA corona, o sigui que una part del vel també és
comuna. Triar el grau del polinomi maximitzant l'acord entre trens porta a
graus baixos que deixen vel. El model es declara per física i es valida amb el
mapa, que queda fora de mostra.

## 6. Les capes

- **`EARTHSHINE`**: el disc mesurat pels dos trens amb el vel restat, al llenç
  sencer. El contrast real és del **0,36 %**: la capa el porta **amplificat
  ×30, declarat al nom**. Màscara fins a 0,945 R☾.
- **`ESTRELLES`**: ⛔ **cap disc dibuixat**. El contingut i la màscara surten
  de la llum realment enregistrada a l'apilat (excés sobre el fons local); el
  catàleg només diu quines d'aquelles fonts són estrelles. 85 fonts, puresa
  95,8 % mesurada (`research/125` §3 ter).

Eines: `v21_lluna_tren.py` (apilat lunar per tren i per fotograma) ·
`v21_lroc.py` (efemèride, orientació i renderitzat del mapa) ·
`v21_earthshine_producte.py` (pesos, producte i validació) ·
`v21_capes_finals.py` · `v21_munta6.py` · `v21_vistes_earthshine.py`.
Mesures a `cau_v21/`.

## 7. La segona iteració de la capa (29-08, matinada): monocroma i disc sencer

Pere, sobre la capa lliurada: «el disc de la lluna és massa petit; hi ha un
patró de línies verticals de color brutal, algunes verdes, altres taronges;
repassa el projecte com t'havia demanat, que era un bon punt de partida».
Tres defectes, tots tres mesurats i curats:

1. ⛔ **El disc retallat a 0,90 R☾** (radi visible 410 px quan el disc del
   muntatge en fa 455,5): la màscara d'ANÀLISI s'havia colat com a màscara de
   CAPA. Ara: disc fins a 0,985 R☾ amb fosa al limbe (radi visible 452 px);
   el vel s'ajusta fins a 0,975.
2. ⛔ **El color amplificat era soroll**: el residu R−G té 15 comptes de
   desviació amb el senyal G a 5,5 — amplificar cada canal pel seu compte
   pinta taques verdes i taronges que no són de la Lluna. **La lliçó ja era
   escrita al LLEGEIX-ME d'Earthshine_FINAL del 15-08** («el color de gran
   escala NO és fiable; el residu del halo al canal R és tres vegades pitjor;
   no fer-lo servir com a color d'earthshine») i no es va rellegir. La capa
   passa a **MONOCROMA del canal G**, com aquell producte.
3. ⛔ **Les línies verticals** són el patró de re-mostreig dels subplans
   Bayer: alineades amb les columnes del LLENÇ (no del sensor, que hi està
   girat 10,9°), R 0,91 comptes per columna, G 0,27. Cura: mediana per
   columna i per fila del passa-alt, restada dins del disc.

Més dues decisions de display, totes DECLARADES al nom de la capa i al rebut:
compressió tanh a ±2,5σ (els arcs de residu del limbe no cremen; cap mar és
per sobre de 2σ) i fosca de limbe del 22 % del pedestal (display: l'anell
exterior deixa de ser un cèrcol pla; l'estructura hi va esvaïda 0,92→0,96 on
el vel residual mana).

**La validació es manté i puja**: r = **+0,777** amb el mapa LROC, control nul
−0,031 ± 0,089 → **9,1σ** (el nul baixa perquè el destriat treu variància
compartida). Pesos: Vixen 96,5 % · Sony ap.1 3,5 % · ap.2 0,02 %. Contrast
real de l'estructura: **0,52 %** del nivell del disc (amplificació de
contrast ×50, declarada). Eines: `v21_earthshine_producte2.py`,
`v21_capa_earthshine3.py`, `v21_munta7.py`.

⏭️ **Regla que en surt** (i que Earthshine_FINAL ja tenia): en un senyal al
límit del gra, **el color per canal no es lliura mai amplificat** — el residu
de vel per canal és més gran que el senyal i el croma resultant és fabricat
encara que cap píxel no ho sigui. Estructura en monocrom; el color, si mai,
com a mesura a part amb la seva pròpia validació.
