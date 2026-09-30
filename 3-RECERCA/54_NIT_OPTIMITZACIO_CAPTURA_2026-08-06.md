# Nit d'optimització de captura: 5→6 d'agost de 2026

Branca: `claude/nightly-capture-optimization-20260806`
Cossos connectats tota la nit: A7III, A7RIIIA i R6 Mark III. La 6D no.

## 1. El bug de routing que va excloure la R6, i el que hi havia a sota

### L'incident

Al run de Pere `20260806T012735` la R6 va quedar exclosa amb
`ptp_identity_unverified` i no va disparar. Les dues Sony van continuar. La
6D, apagada però endollada, continuava enumerada i libgphoto2 l'etiquetava
com una segona «Canon EOS R6 Mark III»; amb dues files del mateix model i
cap sèrie USB —les Canon no en publiquen a IORegistry— la reconciliació les
marcava totes dues en conflicte i el routing es rendia.

### El que s'ha mesurat aquesta nit

Amb els tres cossos connectats i la 6D **desendollada**, `gphoto2
--auto-detect` continua publicant tres files, dues d'elles «Canon EOS R6
Mark III»:

```
Canon EOS R6 Mark III          usb:000,001
Sony ILCE-7RM3A (PC Control)   usb:002,001
Canon EOS R6 Mark III          usb:001,001
```

Però només hi ha una Canon. La segona fila és **l'A7III mal etiquetada**.

I encara més important, sondejant per PTP:

| Ordre | Sèrie que respon |
|---|---|
| `--camera "Sony Alpha-A7 III (PC Control)" --port usb:000,001` | `…[SÈRIE]` (A7III) |
| `--camera "Canon EOS R6 Mark III" --port usb:000,001` | `6d67c992…` (R6) |

**El mateix port retorna cossos diferents segons el model que li demanis.**
El port de gphoto no identifica cap cos: qui mana és `--camera`. Els tres
controladors ja el fixen, i per això cap missió ha dirigit mai un cos
equivocat; el defecte era només a la capa de routing de la GUI.

### La reparació

El pas 4 del protocol obligatori de CLAUDE.md §6 —confirmació exacta de
model i sèrie per PTP— és precisament el que desfà l'empat, i no s'executava.
Ara, quan un perfil no té ruta exacta, cada port candidat rep un
`get-config` acotat amb el model fixat i només s'encamina el que respon la
sèrie documentada. Diverses files amb la mateixa sèrie són un sol cos
enumerat més d'una vegada i col·lapsen al port més baix; una sèrie diferent
deixa de bloquejar el perfil que no és seu; cap sèrie no encamina res.

També compta com a absent una ruta que existeix però no és verificable: el
fallback per model retorna una fila `unassigned` que el gate de RUN rebutja
igualment, així que també se sondeja.

### El segon defecte que va destapar

El sondeig de bateria de la GUI cridava gphoto **només amb `--port`**. Amb
els tres cossos connectats, mesurat:

| Fila | El que mostrava | El que era de veritat |
|---|---|---|
| A7III | 62 % | **30 %** |
| R6 III | 62 % | 62 % |
| A7RIIIA | 77 % | 77 % |

O sigui que l'app ensenyava la càrrega de la R6 a la fila de l'A7III i
amagava justament el cos més a prop de morir. Ara tota crida fixa el model
de la fila, i el descobriment corre amb `LC_ALL=C` com ja fan els
controladors.

## 2. El sostre real de la R6 III per gphoto

Totes les mesures amb delta CFexpress exclusiu, zero Busy, sobre el cos
exacte `6d67c9923f453163358971b1b13d4c5f`.

### Cadència de ràfega AEB3

| Interval | Hold | Grups | CR3 esperats | Observats | Veredicte |
|---:|---:|---:|---:|---:|---|
| 2,20 s | 1,00 s | 12 | 36 | 36 | PASS |
| 1,80 s | 0,80 s | 12 | 36 | 36 | PASS |
| 1,50 s | 0,60 s | 12 | 36 | 36 | PASS |
| 1,20 s | 0,50 s | 12 | 36 | 36 | PASS |
| 1,00 s | 0,40 s | 15 | 45 | 45 | PASS |
| 0,90 s | 0,35 s | 15 | 45 | 45 | PASS |
| 0,80 s | 0,30 s | 20 | 60 | 60 | PASS |
| 0,70 s | 0,25 s | 20 | 60 | 60 | PASS |
| 0,60 s | 0,15 s | 20 | 60 | 60 | PASS |
| 0,55 s | 0,10 s | 25 | 75 | **39** | FAIL |

El terra és el **hold**, no l'interval: a 0,10 s el release talla la ràfega
AEB. El cos dispara les seves tres imatges entre 0,10 i 0,15 s, o sigui a
20-30 fps efectius.

### Aguant a durada de totalitat

| Interval | Hold | Grups | Durada | CR3 | Veredicte |
|---:|---:|---:|---:|---:|---|
| 0,80 s | 0,25 s | 125 | 100 s | 375/375 | PASS |
| 0,60 s | 0,15 s | 165 | 99 s | 495/495 | PASS |

**5,00 CR3/s sostinguts durant tota una totalitat, sense perdre'n cap.** El
nucli anterior en feia 105 en el mateix temps.

### Latència de transport

Mesurada als events del run a 0,70 s, 79 ordres: **4,3 ms de mediana,
21,8 ms de p90, 186 ms el pitjor cas**. La reserva de 2,20 s per grup no
tenia res a veure amb el host.

### Preparació del setter després de ràfega

El perfil reservava 5,95 s per transició perquè `config_ready_s` era 5,40 s.
Escala de sis esglaons, quatre blocs de cinc ràfegues denses amb un canvi de
base entre blocs:

| Retard del setter | CR3 | Setters verificats | Veredicte |
|---:|---:|---:|---|
| 5,40 s | 60/60 | 3/3 | PASS |
| 4,00 s | 60/60 | 3/3 | PASS |
| 3,00 s | 60/60 | 3/3 | PASS |
| 2,00 s | 60/60 | 3/3 | PASS |
| 1,50 s | 60/60 | 3/3 | PASS |
| 1,00 s | 60/60 | 3/3 | PASS |

**El canvi de base costa 1 s, no 6.** Això també desmenteix els gates
aïllats del 5 d'agost, que fallaven amb Busy a 6, 8 i 12 s: el problema no
era el temps d'espera.

## 3. El nucli dens v4

| Paràmetre | Abans | Ara | Base |
|---|---:|---:|---|
| Interval de grup | 2,20 s | 0,75 s | entre els dos punts amb aguant demostrat |
| Hold | 1,00 s | 0,15 s | 495/495 a l'assaig d'aguant |
| Transició de base | 5,95 s | 2,00 s | doble del mínim verificat |
| Tolerància de retard | 0,15 s | 0,27 s | per damunt del pitjor retard observat |

La geometria ara es dimensiona sola a partir de la durada. **El que no es
mou** és la finestra de 1/320 a banda i banda de cada contacte, on hi ha
l'anell de diamant i les perles de Baily. **El que escala** és el
repartiment de les cinc bases lentes del mig.

| Totalitat | CR3 dins totalitat | Factor |
|---:|---:|---:|
| 45 s | 126 | 1,20× |
| 60 s | 180 | 1,71× |
| 98,8 s | **318** | **3,03×** |
| 120 s | 402 | 3,83× |
| 180 s | 612 | 5,83× |

L'escala d'exposicions no canvia: sis bases separades 1 EV que donen dotze
velocitats úniques entre 1/2500 i 0,8 s, exactament com havia calculat
Codex. La comprovació és correcta.

Una restricció física que el disseny ha de respectar: la tríada de la base
1/10 suma 0,9125 s d'obturació pura, o sigui que aquell bloc eixampla el seu
propi interval i la seva readiness. La resta corren al nominal.

## 4. Els dos gates físics del nucli dens

### `20260806T032240`, primer gate

216/243 CR3, els sis setters adoptats amb readback. Les nou ràfegues
perdudes: sis quarantenes per `-110 I/O in progress` al press i tres més
saltades per arribar entre 181 i 239 ms tard just després. Amb 0,05 s de
tolerància un entrebanc de transport n'encadena un segon. D'aquí surt el
repartiment de paràmetres de l'apartat anterior.

### `20260806T033714`, segon gate

161/240 i el canal aturat. La causa no és la cadència: amb el cos al **13 %
de bateria**, `/main/capturesettings/shutterspeed` va publicar només dues
opcions —«Unknown value 0d00» i «1/20»— i el setter de la base 1/10 no va
trobar el seu índex.

Això va destapar un defecte Mission First de primer ordre. `index_for`
refusa **abans** de compondre cap ordre: no s'ha enviat res pel bus i el
valor anterior continua vigent, o sigui que l'estat físic és perfectament
conegut, més net fins i tot que un `was not set` de Canon. Tot i així la R6
sencera s'aturava i el cleanup saltava la restauració.

`choice_list_is_truncated_read` ja documentava aquest fenomen al preflight i
deia literalment que qui ho ha de resoldre és el setter en runtime degradant
només aquell canal. Ara ho fa: conserva l'última base coneguda, no repeteix
el setter, no sacrifica cap pulsació futura i reescriu les captures
dependents amb la base confirmada.

**Deute obert:** el nucli dens sencer encara no té una passada neta. Cal
repetir-la amb bateria plena.

## 5. Parcials a 30 s

Fet, per a tota la flota, entre C1 i C2−30 s i entre C3+30 s i la finestra
quieta de C4. La constant viu duplicada a propòsit —el worker R6 recalcula la
cronologia pel seu compte i refusa qualsevol materialització que en
divergeixi— i les dues s'han mogut juntes.

Impacte a 98,8 s de totalitat amb una hora de parcials: A7III 31→60 per
banda, A7RIIIA 31→60, R6 99→186.

## 6. Sony: anàlisi feta, implementació pendent

### On hi ha marge de veritat

**A7III**, 55 imatges dins totalitat. Els drenatges són el que menja temps:

| Finestra | Ocupació | Marge lliure |
|---|---|---:|
| C2+5 → C2+21 | drena 11, després dos setters | ~6 s |
| C2+31 → C2+37 | drena 5, després un setter | ~1,7 s |
| C2+62 → C2+90 | drena 27, després dos setters | **~10 s** |

Uns 16 s lliures dins totalitat. A 8,2 s per bracket de nou, hi caben dos
brackets més: 55 → 73, que és **+33 %**. Cal re-pressupostar els drenatges:
18 imatges més són uns 9 s més de drenatge a 0,51 s/imatge.

**A7RIIIA**, 72 imatges dins totalitat, amb dos drenatges de 27 que ocupen
uns 28 s dels 98,8. El sostre teòric amb el pipeline actual és ~119 imatges
(0,83 s/imatge amortitzat), o sigui que +30 % —fins a 94— hi cap, però
demana reordenar el pipeline, no només afegir-hi blocs.

### Dos gates físics a l'A7RIIIA aquesta nit

| Run | Geometria | Resultat |
|---|---|---|
| `20260806T034759` | totalitat 100 s, parcials 90 s | **78/78 confirmades**, cleanup i restore nets, únic avís el checklist manual |
| `20260806T035346` | totalitat 98,8 s, parcials 70 s | **78/78 confirmades**, igual |
| `20260806T040903` | totalitat 110 s, parcials 70 s | 83/91; tres drenatges intermedis no verificats |

Els dos primers **validen físicament la cadència parcial de 30 s** de punta a
punta: el cos la sosté sense perdre ni una imatge.

El tercer no. A 110 s de totalitat l'A7RIIIA tria un tier més dens i el seu
`dense_drain_9x1` n'espera 36 però només n'hi arriben 28, amb la cua a zero.
Vuit imatges que no s'han fet mai. Això és **fora de la geometria
qualificada** —l'evidència física del cos és a 98,8 s— i no té res a veure
amb el canvi de parcials, perquè el drenatge que falla és dins totalitat.
És, això sí, exactament el terreny que haurà de trepitjar l'objectiu del
+30 %: el pipeline dens de l'A7RIIIA no aguanta encara les geometries
llargues.

Un apunt de mètode: un quart intent (`20260806T035848`) el vaig matar jo amb
un timeout massa curt al meu propi guió, no el worker. La càmera va
recuperar-se sola i sense processos penjats, però les 83 JPEG d'aquell
directori són d'un run interromput i no valen com a evidència.

### Earthshine: hi ha un conflicte que has de resoldre tu

Les dues Sony corren a **ISO 100**, i la missió no escriu mai ISO.

Amb el 300 mm f/2,8, una exposició d'earthshine correcta són **uns 8 s a
ISO 100** (partint de la referència habitual de 2 s a f/5,6 ISO 1600: dos
punts de guany per l'òptica, quatre de pèrdua per la sensibilitat).

| Cos | Exposició més llarga actual | Distància a l'earthshine |
|---|---:|---:|
| A7RIIIA | 3,2 s | 1,3 punts per sota |
| A7III | 2 s | 2 punts per sota |
| R6 III (f/5,5) | 0,8 s | ~5,5 punts per sota |

L'A7RIIIA ja produeix quatre fotogrames de 1,6 s o més al bloc de mig de
totalitat, i a 1,3 punts per sota són **recuperables en RAW**. La R6, no: a
ISO 100 i f/5,5 l'earthshine no hi és.

Tens tres camins i la decisió és teva, perquè l'ISO és de l'operador:

1. **Pujar l'ISO d'una Sony a 1600** per a tot el run. Guanyes l'earthshine
   de veritat i perds soroll a la corona.
2. **Deixar-ho a ISO 100** i afegir un bloc dedicat de tres exposicions de
   3,2, 5 i 8 s a mig de totalitat a l'A7RIIIA. A 300 mm el moviment relatiu
   de la Lluna en 8 s és ~1,3 px: no arrossega. Aquesta és l'opció que no
   toca res del que ja està qualificat.
3. **Acceptar** els quatre fotogrames actuals de ≥1,6 s com l'intent
   d'earthshine i no afegir res.

La meva recomanació és la 2 per a l'A7RIIIA i renunciar explícitament a
l'earthshine de la R6, que no hi arribarà mai a ISO 100.

## 6 bis. Obturacions: el càlcul de Codex és correcte, però l'A7III no quadra

### El que sí quadra

L'escala de sis bases de la R6 separades 1 EV dona **exactament dotze
velocitats úniques** entre 1/2500 i 0,8 s —les tríades ±3 EV se solapen tal
com deia Codex— i cobreix 11 EV. Verificat: `1/2500, 1/1250, 1/640, 1/320,
1/160, 1/80, 1/40, 1/20, 1/10, 1/5, 1/2,5, 1/1,25`. Sis de les divuit
exposicions són repeticions, cosa que no és malbaratament: repetir la
mateixa velocitat en instants diferents permet apilar.

Els dos ancoratges fotomètrics mesurats també quadren amb el que compila la
missió:

| Cos | Ancoratge documentat a `research/50` | El que compila |
|---|---|---|
| A7RIIIA + 300 GM + ASTF-120 OD 5,1 | ISO 100, 1/400 | 1/400 |
| R6 III + VSD90SS + ASSF100 OD 5,0 | ISO 100, 1/320 | base 1/320 |

### El que no quadra

L'A7III compila la **parcial filtrada a 1/1250**, i el seu perfil declara el
mateix 300 mm f/2,8 i la mateixa ISO 100 que l'A7RIIIA. Són **1,64 EV** de
diferència entre dos cossos amb la mateixa òptica i la mateixa
sensibilitat apuntant al mateix Sol.

**Correcció del 6 d'agost al matí.** En una primera lectura vaig escriure
que l'A7III no podia fer servir el mateix 1/1250 per a la parcial filtrada i
per al bloc de contacte sense filtre, perquè un AstroSolar OD 5 atenua uns
16,6 EV. **Aquest raonament era erroni.** La parcial filtrada exposa per a la
fotosfera; el bloc de contacte exposa per a la cromosfera i la corona
interna, que són molt més febles. Les dues coses cauen legítimament a prop:
el mateix A7RIIIA ho demostra, amb 1/400 filtrat i base 1/250 al contacte,
només 0,68 punts de diferència.

El que sí que continua sense explicació és el **1,64 EV entre les dues Sony
a la parcial filtrada**.

`research/50` documenta la mesura de l'A7RIIIA i la de la R6. **De l'A7III no
n'hi ha cap.** El seu 1/1250 no té cap ancoratge fotomètric propi, i el nom
intern de les accions —`c2_1_8000_*`, `verify_c2_1_8000`— delata que ve d'un
1/8000 anterior que es va reajustar sense tornar a mesurar.

Això no ho puc resoldre jo: depèn de quin filtre i quina òptica porta
físicament l'A7III el dia de l'eclipsi, que és cosa teva. El que sí que puc
dir amb seguretat és que **tal com està, un dels dos usos del 1/1250 dona una
exposició inservible**, i que si l'A7III duu el mateix tren que l'A7RIIIA la
seva parcial filtrada hauria de ser 1/400, no 1/1250.

## 6 ter. Contrast amb la guia ràpida de PhotoPills

Pere ha aportat les dues fitxes de PhotoPills per a l'eclipsi de 2026. La
que ens toca és la 2/2 (Nikon, Sony, Fuji i Canon); la 1/2 és d'Olympus i
treballa a ISO 200.

PhotoPills dona **f/8** a totes les fases. Els nostres trens no hi són: el
300 GM va a f/2,8 (3,03 punts més de llum) i el VSD90SS a f/5,5 (1,08 punts
més). Sense normalitzar l'obertura, cap número és comparable.

### Parcial filtrada: la diferència és la densitat del filtre

| | Obturació | Normalitzat a f/8 |
|---|---|---|
| PhotoPills | 1/500 a f/8 | 1/500 |
| Nostre A7RIIIA, migdia, OD 5,1 | 1/640 a f/2,8 | 1/78 |

Són **2,67 punts**, que corresponen a una densitat implícita de PhotoPills
d'**OD ≈ 4,3**. Nosaltres fem servir OD 5,0 i 5,1. Un cop tens en compte
l'obertura i el filtre, les dues fonts diuen el mateix; PhotoPills no
declara la densitat que suposa, i aquí és on està tota la diferència.

El nostre valor de missió, 1/400, és 0,68 punts més lent que el de migdia:
és el marge d'extinció a 10° d'altura, coherent amb la k=0,37 mag/massa
d'aire mesurada al projecte.

### Totalitat: la nostra escala és més ampla per les dues bandes

| | Rang normalitzat a la nostra obertura |
|---|---|
| PhotoPills Sony, 9×1 EV sobre 1/15 f/8 | 1/1959 … 1/8 a f/2,8 |
| **Nostre A7RIIIA**, tres bases | **1/4000 … 3,2 s** |
| PhotoPills Canon, 7×1,3 EV sobre 1/15 f/8 | 1/474 … 1/2 a f/5,5 |
| **Nostre R6 III**, sis bases | **1/2500 … 0,8 s** |

L'A7RIIIA guanya 1,0 punt per dalt i **4,6 punts per baix**; la R6, 2,4 per
dalt i 0,8 per baix. Aquest excés per baix no és casualitat: és on viuen la
corona externa i la llum cendrosa, i un sol bracket centrat com el de
PhotoPills no hi arriba. És exactament el que justifica el disseny de
diverses bases.

### Contactes: PhotoPills confirma l'A7RIIIA i torna a assenyalar l'A7III

PhotoPills posa 1/500 a f/8 per a l'anell de diamant i les perles.
Normalitzat:

| Cos | PhotoPills a la nostra obertura | El que fem | Diferència |
|---|---|---|---|
| A7RIIIA f/2,8 | 1/4082 | extrem ràpid **1/4000** | **+0,03 punts** |
| R6 III f/5,5 | 1/1058 | extrem ràpid 1/2500 | −1,24 punts (conservador, però bracketa fins a 1/40) |
| A7III f/2,8 | 1/4082 | **fix 1/1250** | **+1,71 punts, sobreexposa** |

L'extrem ràpid de l'A7RIIIA cau a tres centèsimes de punt del que diu
PhotoPills. És una coincidència independent notable i dona confiança al
tren mesurat.

L'A7III, en canvi, torna a quedar despenjat, i ara per la banda contrària
que a la parcial. Dues fonts independents apuntant al mateix cos.

### El que PhotoPills fa i nosaltres no: bracketejar la parcial

PhotoPills posa **3× @ 1 EV** a les dues fases parcials. Nosaltres hi posem
**una sola exposició fixa**: 1/400 abans i 1/400 després a l'A7RIIIA, base
1/320 abans i després a la R6.

Amb el Sol alt això seria una diferència d'estil. El 12 d'agost no ho és,
perquè el Sol es pon durant l'eclipsi. Amb la k=0,37 mag/massa d'aire
mesurada al projecte:

| Altura | Massa d'aire | Punts respecte 15° |
|---:|---:|---:|
| 20° | 2,90 | −0,45 |
| 15° | 3,81 | 0,00 |
| 10° | 5,59 | +0,87 |
| 7° | 7,73 | +1,92 |
| 5° | 10,31 | +3,19 |
| 3° | 15,15 | +5,57 |
| 2° | 19,43 | +7,68 |

**Si el Sol baixa de 15° a 5° durant la parcialitat, calen 3,2 punts més
d'exposició; de 15° a 3°, 5,6 punts.** Una sola obturació fixa per a tota la
fase parcial no pot ser correcta als dos extrems, i la parcial posterior a
C3 és la que ho pateix més perquè el Sol ja és més baix.

Això no ho havia mirat aquesta nit i és, probablement, el defecte fotomètric
més gros que queda obert. El bracket de PhotoPills en cobreix ±1 punt, que
tampoc no arriba; el que caldria és **lligar l'obturació parcial a l'altura
solar prevista de cada instant**, que és informació que el pla de contactes
ja té.

## 7. Estat dels cossos en tancar

| Cos | Bateria | Estat |
|---|---:|---|
| R6 III | 11 % | **obturació a 1/20, no 1/320**; menú col·lapsat a dues entrades; cal cicle d'alimentació |
| A7RIIIA | 77 % | intacte |
| A7III | 30 % | intacte |

Targeta CFexpress de la R6: ~3.500 CR3, no s'ha formatat res ni s'ha
esborrat cap fitxer.

## 8. Earthshine: implementat i verificat al cos (6 d'agost, matí)

Requisit de l'operador: earthshine obligatori amb el 300 mm f/2,8.

### Mesures prèvies, abans d'escriure cap línia de perfil

| Què | Resultat |
|---|---|
| `Bracketing C 3.0 Steps 5 Pictures` amb base 1/8 | produeix **1/500, 1/60, 1/8, 1 s i 8 s** |
| Cost del canvi de mode de captura | **0,41 s** |
| Reducció de soroll d'exposició llarga | **desactivada**: cost marginal d'una presa de 8 s = 8,18 s, factor 1,02 |

El cost del canvi de mode és la troballa que ho fa possible. El comentari del
drenatge parlava de 19,5 s i feia semblar intocable el selector dins la
totalitat; aquells 19,5 s eren el *readback*, no l'escriptura.

### Run físic `20260806T111952`

Programa sencer de l'A7RIIIA amb totalitat de 98,8 s: **59/59 imatges
confirmades**, exit 0, cleanup i restore nets. Distribució EXIF real dels
fotogrames descarregats:

| Exposició | Quantitat |
|---|---:|
| 1/4000 … 1/15 (escala de contacte) | 49 |
| 1/8 | 2 |
| 1 s | 2 |
| **8 s** | **2** |

Els dos fotogrames de 8,00 s són les àncores d'earthshine. És la primera
vegada que aquest programa arriba a aquesta exposició: el màxim anterior era
3,2 s, 1,3 punts per sota.

### El preu

Dinou imatges menys de totalitat en aquest cos: marxen el tram de 1/30 i els
dos brackets llargs de base 1/5. Cap dels dos hauria enregistrat mai
l'earthshine. Els quatre brackets de contacte —dos a C2 i dos a C3— queden
intactes.

Amb 98,8 s de totalitat hi caben **dues** àncores. El recompte el deriva la
geometria, no una constant: amb totalitats més llargues n'hi caben més, i si
no n'hi cap cap el cos torna al tram de brackets llargs que ja tenia en
comptes de refusar de compilar.


## 9. El sostre de gphoto a la R6, trobat de veritat (6 d'agost, matí)

Amb bateria nova al 78 % vaig provar l'única palanca que quedava sense
tocar: el mode de ràfega `Super high speed continuous shooting`. Manté AEB
+/-3, RAW i 1/320, i canviar-hi costa 0,53 s.

| Interval | Hold | Mode | CR3 | Veredicte |
|---:|---:|---|---:|---|
| 0,60 s | 0,15 s | Continuous high speed | 60/60 | PASS |
| 0,55 s | 0,10 s | Continuous high speed | **39/75** | FAIL, ràfega tallada |
| 0,60 s | 0,15 s | **Super high speed** | 60/60 | PASS |
| 0,55 s | 0,10 s | **Super high speed** | **75/75** | **PASS** |
| 0,50 s | 0,10 s | Super high speed | 3/75 | FAIL, `-110 I/O in progress` |

Dues conclusions netes:

1. **Super high speed acaba la tríada AEB més de pressa.** On el mode normal
   tallava la ràfega a hold 0,10 s, aquest la completa. Això puja el sostre
   de 5,00 a **5,46 CR3/s**.
2. **A 0,50 s el que falla ja no és el cos, és el transport.** El segon press
   torna `-110 I/O in progress` i el run s'atura. Amb marges d'amfitrió
   retallats a poc més del triple de la p90 mesurada, el resultat no canvia.

O sigui que **el sostre de gphoto en aquest cos és 0,55 s entre pulsacions**,
i està limitat pel transport PTP, no per l'obturador ni pel buffer ni per la
targeta. És exactament el punt on l'operador va dir de passar a l'SDK.

El nucli dens de missió corre a 0,75 s, deliberadament per damunt d'aquest
terra: el marge extra és el que absorbeix els entrebancs de transport que
van fer perdre nou ràfegues al primer gate. Pujar el nucli a Super high speed
donaria un 9 % més, però canvia l'estat físic contractat del perfil i demana
requalificació; queda documentat com a opció, no aplicat.
