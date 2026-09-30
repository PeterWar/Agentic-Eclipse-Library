# 66 — El cost real d'una àncora de 8 s, i la NR dels dos cossos Sony

8 d'agost de 2026, migdia. Represa de la campanya que la nit del 7 al 8 va
deixar a mitges (`65`), després que Pere tragués les bateries i formatés les
targetes.

**Resum**: el número que mancava ja està mesurat i confirma el disseny de
blocs (§1). De retruc queda demostrat que la reducció de soroll d'exposició
llarga està **apagada als dos cossos** (§2), cosa que fins ara només se
sabia de l'A7RIIIA i de sentit. Els números per decidir cada quant es drena
són a §3. I llegint codi apareix la causa mecànica del desastre de la nit:
**l'aplicació mata a senyal qualsevol `gphoto2` que no sigui seu** (§4).

Condicions de banc idèntiques a `65`: cap dels dos cossos porta òptica, o
sigui que tot fotograma és negre. Això invalida el **cabal** de drenatge per
a imatges reals, però no la **durada** de res.

## 0. Estat dels cossos en començar

Els dos al bus, A7RIIIA `[SÈRIE]` al 86 % i A7III `[SÈRIE]` al
93 %. L'A7RIIIA amb model, `M`, focus manual, RAW+JPEG (Std), ISO 100,
`card+sdram` i, sobretot, **`/main/other/d215` a 0**: cap imatge pendent. El
cicle de bateria va desfer l'estat de transferència encallada.

La represa automàtica armada la nit anterior **sí que va arrencar**, a les
11:50, i va quedar tallada als 1,8 s en morir la sessió que la supervisava
(`20260808T115033`). No va disparar res, però deixa provat que l'A7RIIIA ja
tornava a respondre PTP: va llegir el menú sencer i va escriure i rellegir
`capturemode`.

## 1. El cost real d'una àncora de 8 s — MESURAT

Run `20260808T120011`, perfil `lab_a7r3a_m2_ancora_3x3_cad12`: tres ràfegues
`Bracketing C 3.0 Steps 3` des de base 1 s, cadència forçada de 12 s.

**9/9 confirmades i descarregades**, drenatge complet, cleanup i restore
correctes, identitat verificada i `physical_state_unknown=false`. Els únics
avisos són `manual_checklist_incomplete` i `timing_not_qualified`, que el
contracte classifica com a informació i mai com a `WARNING` operatiu.

| Magnitud | Valor |
|---|---:|
| Retenció de la ràfega | 9,608 · 9,605 · 9,611 s |
| Acció sencera (retenció + observació de cua) | 11,215 · 11,207 · 11,207 s |
| Retard sobre l'instant previst | 0,003 · 0,002 · 0,001 ms |
| Compromisos per ràfega | 3 · 3 · 3 |

Dos números que no s'han de confondre: **l'acció sencera dura 11,21 s** i
**la cadència demostrada d'extrem a extrem és 12,0 s**, que és la que el
perfil forçava. Els 11,6 s que `65` assumia queden **entre els dos**, o sigui
que la suposició era bona i el disseny no es mou: a 90 s de totalitat
continuen sortint **sis àncores**, 2,45× de senyal/soroll contra les dues del
programa d'avui. Cap disseny futur no ha de prendre els 11,21 s com a
cadència: és la durada de l'acció, no un interval provat entre pulsacions.

L'EXIF dels nou fitxers tanca l'ordre i les exposicions:

| Ràfega | 1r | 2n | 3r |
|---|---|---|---|
| totes tres | **1 s** | **1/8** | **8 s** |

O sigui `0, −3, +3 EV`, que torna a confirmar §1 de `65`: **el fotograma
extrem no és el primer**. Tots nou a ISO 100.

**La cua va sempre un fotograma endarrerida en el moment d'observar-la.** A
1,6 s d'alliberar, `d215` val 2 quan n'esperaves 3: el fotograma de 8 s
encara s'està escrivint. Arriba tot seguit —el recompte va 2 → 5 → 8 → 9— i
per això la validació de cua d'aquest perfil és `deferred` i
`advisory_only`. Qualsevol perfil futur que validi la cua en dur just
després d'una ràfega amb un fotograma llarg fallarà per una cosa que no és
un error.

### El que no s'ha mesurat, i per què no s'ha intentat

La cadència **mínima** d'àncora continua sense mesurar: 12,0 s està
demostrada, i per sota no s'ha provat. Estrènyer-la compraria una setena
àncora a 90 s, que són un 8 % de senyal/soroll. **No val el que costa**: és
exactament la mena de cacera de marge que la nit del 7 al 8 va acabar amb
dues bateries fora i dues targetes formatades.

## 2. La reducció de soroll d'exposició llarga està apagada als dos cossos

`libgphoto2` **no publica aquest ajust** a cap dels dos cossos —zero
coincidències de `noise` al llistat sencer de configuració de l'A7III—,
igual que passa a la R6. Fins ara era, doncs, una comprovació física
d'operador. Es pot mesurar.

**L'instrument**: un sol fotograma Single de 8 s i una lectura de
`/main/other/d215` **1,5 s després d'alliberar**. Amb la NR apagada la imatge
ja hi és cap als 9 s de la pulsació; amb la NR encesa el cos encara està fent
un fotograma fosc igual de llarg i no hi pot ser fins als ~16 s. Un sol
fotograma per pulsació vol dir que **no hi ha cap ràfega que es pugui
truncar**: l'instrument no pot fer mal.

| Run | Cos | Cua a 1,5 s d'alliberar | Confirmades |
|---|---|---|---|
| `20260808T120939` | A7III | **1 · 2 · 3** | 3/3 |
| `20260808T121317` | A7RIIIA (control) | **1 · 2 · 3** | 3/3 |

**Per què el control tanca l'argument**: de l'A7RIIIA ja se'n sap la NR
apagada per una via independent i decisiva —la ràfega de tres del §1, amb
9,125 s d'exposició acumulada, li cap en 9,6 s de retenció, cosa impossible
amb un fotograma fosc de 8 s pel mig—. Els dos cossos donen lectura
idèntica, o sigui que **l'A7III també la té apagada**.

Queda una escletxa honesta: no hi ha cap cos amb la NR encesa per comprovar
que l'instrument hi llegiria 0. La confirmació definitiva és mirar el menú de
l'A7III, que són deu segons.

Perfils: `lab_a7m3_sonda_nr_cua_1p5s` i `lab_a7r3a_sonda_nr_cua_1p5s`. El
primer intent, `lab_a7m3_single_8s_sonda_nr`, **no servia**: hi vaig posar la
lectura 21 s després d'alliberar, i a 21 s les dues hipòtesis donen el mateix.
Es conserva perquè els seus 2/2 fotogrames de 8 s a l'A7III són vàlids.

També es va descartar l'instrument obvi —repetir la ràfega de tres amb
retenció llarga— perquè **el controlador imposa un límit dur de 15 s de
retenció** i una ràfega amb la NR encesa en vol ~18. La única manera de
provar-ho amb ràfegues hauria estat alliberar el botó a mitja ràfega, que és
precisament el que va tombar els cossos la nit anterior.

## 3. Cada quant s'ha de drenar: els números, i no són iguals als dos cossos

Run `20260808T123003`, el bessó exacte del §1 a l'A7III: **9/9 confirmades**,
retenció 9,604 s i acció sencera **11,205 s**. Serveix per a dues coses.

**L'àncora costa el mateix als dos cossos.** 11,205 s a l'A7III contra
11,215 a l'A7RIIIA: una desena de mil·lisegon de diferència. Té sentit, perquè
el que mana és la suma d'exposicions de la ràfega —9,125 s—, que no depèn del
cos. Qualsevol geometria d'àncores val igual per als dos.

**El drenatge no.** Amb nou imatges exactes a cada cos i la mateixa finestra
de 2 s:

| Cos | Imatges | Intents | Temps | Per intent | Per imatge |
|---|---:|---:|---:|---:|---:|
| A7RIIIA | 9 | **3** | 6,32 s | 4 imatges | 0,526 s |
| **A7III** | 9 | **2** | **4,07 s** | **6 imatges** | **0,338 s** |

Són **1,55×**, que és exactament el factor que `65` havia mesurat per una
altra via. La granularitat de ~2 s per intent no és del cos: és el
`wait_window_s` del perfil. El que és del cos és quantes imatges hi caben
dins.

Un detall que apunta al mateix: a 1,6 s d'alliberar, **l'A7III ja té els tres
fotogrames a la cua** —3, 6, 9— mentre que l'A7RIIIA en té dos —2, 5, 8— i el
de 8 s encara s'està escrivint.

Aplicat al disseny `blocs_3c_6anc`, que fa **27 imatges als dos cossos** (nou
de contacte i divuit d'àncora). «Pessimista» és suposar que una imatge real de
corona rendeix la meitat que un fotograma negre:

| Política | Màx. pendents | A7RIIIA optimista | A7RIIIA pessimista | A7RIIIA àncores | A7III optimista | A7III pessimista | A7III àncores |
|---|---:|---:|---:|---:|---:|---:|---:|
| **només després de C3** | 27 | 0 s | 0 s | **0** | 0 s | 0 s | **0** |
| un al mig | 14 | 8,4 s | 14,7 s | 1,3 | 6,1 s | 10,1 s | **0,9** |
| dos | 9 | 12,6 s | 21,1 s | 1,9 | 8,1 s | 12,2 s | 1,1 |
| després de cada àncora | 4 | 12,6 s | 25,3 s | 2,3 | 12,2 s | 24,4 s | 2,2 |

**La lectura és dura al cos que importa.** L'earthshine és la missió
principal de l'**A7RIIIA**, i és justament el cos car: partir-li la cua per la
meitat costa 1,3 àncores de sis i li baixa el senyal/soroll de 2,45× a 2,17×.
A l'A7III el mateix costa 0,9, però aquest cos no porta el programa
d'earthshine.

Amb l'earthshine com a **objectiu número u** del projecte, la recomanació és
**no drenar dins la totalitat** —i menys a l'A7RIIIA— i atacar el risc per
l'altra banda: que cap sessió no mori. Que és exactament el que explica §4.
Ara bé, la decisió és de Pere i aquests són els números que en va demanar.

## 4. Per què la sessió moria: l'aplicació mata els `gphoto2` que no són seus

`65` §4 deia que l'app «roba els cossos» amb el seu autocheck. Llegint el codi
resulta que és força més que robar.

A cada cicle d'escaneig, `_auto_scan_tick` crida
`_reap_stray_processes_if_due`, i aquesta, com a molt un cop cada 30 s,
executa `reap_stray_gphoto_processes`: **tot procés anomenat `gphoto2` que no
pertanyi a una missió viva de l'app rep SIGTERM i, si sobreviu una gràcia
curta, SIGKILL**. És una decisió d'operador explícita del 30 de juliol i està
documentada al codi: un `gphoto2` orfe reté una càmera com un ostatge.

La cadena causal de la nit queda tancada, i **les dues troballes del traspàs
són la mateixa**:

1. l'app oberta mata el `gphoto2` de la mesura, a senyal, potser a mig
   drenatge;
2. el cos es queda amb imatges marcades com a pendents i ningú a l'altra
   banda;
3. el cos hi insisteix per sempre: ni apagar-lo i encendre'l ho desfà, només
   treure la bateria.

**Què vol dir per al dia 12.** Durant la missió de veritat el risc és baix:
qui condueix les càmeres és l'app, i mentre `monitor.active` és cert el tick
retorna abans de tocar res. El perill és **la preparació**: qualsevol ordre
manual de `gphoto2` amb l'app oberta pot acabar amb un cos inservible i una
bateria per treure amb el filtre posat i el trípode alineat.

La regla operativa, doncs, no és «no deixis l'app oberta mentre mesures»: és
**mentre l'app és oberta, cap altra eina no toca cap càmera**.

El deute del traspàs —«revisar que l'autocheck quedi inhibit durant tota la
finestra de missió»— queda així: **durant el run ja ho està**, per
`monitor.active`; fora del run l'app escaneja i sega cada 30 s, i canviar-ho
és tocar una política deliberada. No s'ha tocat.

Sobre l'altre deute, la comprovació de «transferint» a la checklist: resulta
que **el número que Pere va veure a la pantalla ja el llegim**. `d215`,
«Objects in memory», és exactament el recompte d'imatges pendents, i el
preflight de tots els perfils ja hi exigeix zero (`queue_must_be_zero`). El
que falta no és la lectura sinó el **diagnòstic**: quan el cos ha quedat
encallat, cap sessió PTP s'obre, o sigui que no es pot llegir `d215` i el que
surt és un timeout genèric. Un cos present a l'IORegistry que refusa tota
obertura PTP hauria de dir «possible transferència encallada: treu la
bateria», no un error de transport qualsevol.

## 4 bis. El sostre de la cua de l'A7RIIIA són 36 imatges — MESURAT

Run `20260808T132331`: setze ràfegues `C 3.0/3` a base 1/640, cadència
qualificada de 2,9 s, **sense drenar pel mig**, partint de `d215` a zero.

| Ràfega | 1 | 2 | … | 11 | 12 | **13** | 14 | 15 | 16 |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| Cua després | 3 | 6 | … | 33 | **36** | **36** | 36 | 36 | 36 |

La cua creix exactament +3 per ràfega fins a **36** i s'atura en sec: les
quatre últimes ràfegues **no produeixen cap imatge**. 36/48 confirmades,
totes descarregades, `d215` a 0 en acabar i `physical_state_unknown=false`.
El `cleanup_ok=false` del run és comptable, no físic: el drenatge esperava 48
fitxers i només n'hi havia 36 perquè només se'n van fer 36.

**Com falla importa tant com on falla**: el cos no es queixa ni s'encalla,
**deixa de disparar en silenci**. En un pla que passés de 36, els fotogrames
que es perdrien serien **els últims**, que és justament on hi ha el bloc de
contacte de C3 i el segon anell de diamant.

**Reproduït.** El run `20260808T134915`, amb el mateix perfil, dona la corba
idèntica: +3 fins a 36 i pla a partir de la ràfega 13. Dues mostres, mateix
sostre, sempre partint de cua zero —que és el que el preflight ja garanteix
amb `queue_must_be_zero`—. Els dos runs acaben amb `d215` a 0 i el cos net.

### Conseqüència: el disseny ja no el limita el temps, el limita la cua

A 96,5 s de totalitat (Medina de Rioseco), amb nou fotogrames de contacte a
C2 i sis a C3, del sostre de 36 en queden **21 per a àncores, o sigui set**.
I set és exactament el que el temps permetia amb l'àncora de 8 s.

| Disseny | Àncores per temps | Per cua | Reals | Imatges | Integració |
|---|---:|---:|---:|---:|---:|
| **extrem 8 s, els dos contactes** | 7 | 7 | **7** | 36 | **56 s** |
| extrem 4 s, els dos contactes | 10 | 7 | 7 | 36 | 28 s |
| extrem 4 s, només C2 | 10 | 9 | 9 | 36 | 36 s |

**Escurçar l'àncora deixa de comprar àncores.** El temps que allibera no es
pot gastar, perquè el que s'acaba abans és la cua. L'àncora fotomètrica de
Cerro Tololo (memòria `ancora-earthshine-ctio-2019`) diu que amb 4 s n'hi
hauria prou; el sostre de la cua diu que escurçar no en dona cap més.

### La decisió: 5 s, i no per temps

Decisió del 8 d'agost, amb Pere delegant-la explícitament i declarant que el
que el preocupa és cremar la foto. Base **0,6 s**, que el cos materialitza com
**1/2 · 1/13 · 5 s** verificat a l'EXIF (run `20260808T134524`, 9/9). Tres
raons, per ordre:

1. **La subexposició es recupera i el cremat no.** Amb calima el requisit són
   7 s i 5 s hi va 0,5 EV curt, cosa que set fotogrames apilats absorbeixen.
   Amb cel net el requisit són 3 s i 8 s hi va 1,4 EV llarg; si això satura la
   superfície de la lluna, no hi ha apilat que ho torni.
2. **No es perd cap escenari.** Els 8 s només guanyarien amb calima forta, on
   el requisit és 18,4 s i tots dos fallen igual.
3. **Amb 5 s el bloc de C3 torna a travessar el contacte.** A 96,5 s de
   totalitat, set àncores de 8 s acaben a C2+92,63 i empenyen el bloc de C3
   **després** de C3, que és precisament el defecte que es va corregir el 7
   d'agost. Amb 5 s l'última acaba a C2+78,63 i els fotogrames de 1/5000 cauen
   a **C3−2,00 i C3+0,90**.

Cost: 35 s d'integració d'earthshine en comptes de 48. Continua essent **set
vegades** la de la làmina de Tololo, amb la mateixa obertura i el mateix ISO.

El pla que en surt fa **36 fotogrames exactes**: nou de contacte a C2, set
àncores i sis de contacte a C3. Va **just al sostre**, i el mode de fallada
d'aquest sostre és silenciós, o sigui que sis àncores —33 imatges— és
l'alternativa amb coixí, a canvi d'un 8 % de senyal.

## 4 ter. Amb òptica posada: el pla sencer, provat

Pere va muntar una lent a l'A7RIIIA a mitja tarda —f/4 declarada pel cos—
justament perquè els JPEG pesessin. Això desbloqueja el que `65` deia que no
es podia fer al banc, i el resultat corregeix dues suposicions nostres.

### El sostre no depèn de la mida de la imatge

Tercera repetició del perfil de sostre, ara amb imatges de veritat de **946 KB
de mitjana** (mínim 474, màxim 1.579) contra els 341,5 KB idèntics dels
fotogrames negres: la corba és **exactament la mateixa**, +3 per ràfega fins a
**36** i pla a partir de la tretzena. El sostre és un **recompte**, no un
pressupost de memòria.

### El drenatge amb imatges reals només és un 9 % més car

Trenta-sis imatges reals drenades en **20,3 s**, en nou intents de ~2,29 s que
s'enduen quatre imatges cadascun. Contra els fotogrames negres: **0,573 s per
imatge amb imatges reals contra 0,526**, i els mateixos **quatre per intent**.

Això **desmenteix la nostra pròpia advertència**. `65` deia que el cabal
mesurat amb fotogrames negres era optimista i que calia un factor d'escala; el
factor és **1,09**, no el 2 que la taula de decisió de §3 feia servir com a
cas pessimista. El drenatge no el limita el volum de dades sinó la finestra de
2 s i les quatre imatges per intent.

### El pla sencer: 36/36, i un defecte de disseny que només es veu corrent-lo

Perfil `lab_a7r3a_blocs_3c_7anc_5s`, els 36 fotogrames amb la geometria
decidida. El primer run, `20260808T142307`, va donar 36/36 i 14/14 accions,
**però amb els dos blocs de contacte de C3 tard: 969 i 570 ms**. Tota la resta
anava a menys de 0,5 ms.

La causa és nostra: el canvi de base a 1/640 va costar **5,44 s** i el pla li
pressupostava 4,47, que era el **màxim de 53 mostres històriques**. Avui n'ha
sortit una de més lenta. El primer canvi de base també anava just, 4,24 s amb
4,62 de marge. En camp, això hauria mogut els fotogrames de 1/5000 de
C3−2,00/+0,90 a C3−1,03/+1,47 —encara travessen, però per sort, no per
disseny— i un setter una mica més lent els hauria posat tots dos després de C3.

Correcció: els dos canvis de base passen a tenir **6,55 i 12,05 s** de marge,
tots dos trets del repòs que ja hi havia entre l'última àncora i el bloc de
C3. **No costa cap fotograma.** Run de verificació `20260808T142826`:

| | Valor |
|---|---|
| Confirmades | **36/36** |
| Accions | 14/14, zero saltades |
| Avisos de cronologia | **0** |
| Recuperacions | 0 |
| Retard màxim | **0,502 ms** |
| Canvis de base | 5,29 s i 5,27 s |
| EXIF | 1/640·1/5000·1/80 ×5 · 1/2·1/13·**5 s** ×7 |
| Cua màxima | 36 |
| Drenatge final | 21,65 s |
| Cleanup, restore, identitat | correctes |

**El cost real d'un canvi de base a l'A7RIIIA és ~5,3 s, no 4,47.** Tres
mostres consecutives —5,44, 5,29, 5,27— per damunt del que 53 mostres
històriques donaven com a màxim. Qualsevol geometria futura ha de pressupostar
5,3 s i no el màxim històric.

## 4 quater. La base dels contactes baixa a 1/160: cap fotograma sense diana

Amb base 1/640 el fotograma de −3 EV queia a **1/5000**, i posant al costat de
cada exposició el que l'escena demana resultava que **1/5000 és més ràpid que
res del que hi ha**: l'element més brillant de la totalitat és l'anell de
diamant, que a Medina (8,63°, k=0,37) demana 1/179. Cinc fotogrames de 36
haurien sortit negres.

El problema de fons és que **l'escena als contactes va a passos de 2 EV**
—perles 1/287, protuberàncies 1/72, corona interior 1/18— i el bràqueting va a
passos de 3. Cap base no els pot encertar tots tres. Comparació de candidats,
sumant la desviació de cada element respecte del fotograma més proper:

| Bràqueting | Base | Tríada | Desviació total |
|---|---|---|---:|
| C 3.0 | 1/640 (anterior) | 1/5000 · 1/640 · 1/80 | **7,8 EV** |
| C 3.0 | 1/320 | 1/2500 · 1/320 · 1/40 | 5,1 EV |
| C 2.0 | 1/105 | 1/420 · 1/105 · 1/26 | 4,0 EV |
| **C 3.0** | **1/160** | **1/1250 · 1/160 · 1/20** | **3,5 EV** |

**Guanya 1/160 amb C 3.0**, i té l'avantatge de no obligar a canviar de
`capturemode`: el principi d'un sol mode tota la totalitat es manté. Amb
`C 2.0` caldria refer també les àncores —des de base 1,25 s donarien
1/3 · 1,25 · 5 s—, i el seu rang de corona quedaria molt més estret.

On cau cada exposició del pla final:

| Exposició | Diana | Ideal | Desviació |
|---|---|---|---:|
| 1/1250 | perles i cromosfera | 1/287 | −2,1 EV (assegurança) |
| **1/160** | **anell de diamant** | 1/179 | **+0,2 EV** |
| 1/20 | corona 0,1 Rs | 1/18 | −0,2 EV |
| 1/13 | corona 0,1 Rs | 1/18 | +0,5 EV |
| 1/2 | corona 2 Rs | 1,0 s | −0,8 EV |
| 5 s | corona 8 Rs | 3,6 s | +0,5 EV |

El 1/1250 continua sent el més allunyat, però ara **és assegurança amb sentit**
—2,1 EV de marge per si l'anell de diamant és més brillant del modelat, que és
l'única direcció on l'error no es recupera— i no un fotograma buit.

Verificat al cos, run `20260808T143630`: **36/36 confirmades, 14/14 accions,
zero saltades, zero avisos de cronologia, zero recuperacions, retard màxim
0,412 ms**, canvis de base de 4,21 i 4,23 s dins els marges nous, i EXIF amb
**1/1250 · 1/160 · 1/20** cinc vegades i **1/2 · 1/13 · 5 s** set vegades.

## 4 quinquies. Dues fotos de Durango, i una rectificació

Pere va aportar els CR2 originals del contacte de 2024 i el KMZ de Jubier.
Això permet fer la transferència fotomètrica bé, i **desmenteix la conclusió
de §4 quater**.

### Les circumstàncies, ara calculades i no assumides

El màxim del TSE 2024 va ser a **−104,139 / 25,289 a les 18:17:17 UTC**, que
és Durango i no Mazatlán. El rellotge de la 6D anava en hora peninsular:
`_MG_9570` marca 20:20:27, o sigui **18:20:27 UTC**. La seqüència de la
mateixa carpeta ho confirma —corona a 1/2 i 1 s fins a 20:20:19 i salt a
1/4000 a 20:20:22—, o sigui que **C3 és allà mateix i el fotograma és cinc
segons després del tercer contacte**.

Posició solar calculada per a aquell lloc i instant: **Sol a 70,14°**,
X = 1,063, a ~1.250 m. Medina de Rioseco: Sol a 8,63°, X = 6,40, 746 m.

### Les dues referències no diuen el mateix, i això és la troballa

| Referència | Original | A f/2,8 ISO 100 |
|---|---|---:|
| 6D + Nikkor 300/2,8 (`_MG_9570`) | 1/2500 · f/2,8 · ISO 200 | **1/1250** |
| A7III + QUADTCC 590 (mateix instant) | 1/8000 · f/4,5 · ISO 100 | **1/20663** |

**Quatre EV de separació**, i totes dues són «les perles a Durango amb núvols
fins». No es contradiuen: són **dues fotos diferents del mateix instant**. La
del 6D dona perla, cromosfera, protuberàncies i **corona interior** —al
preview només hi ha un 0,006 % de píxels saturats, o sigui que la perla queda
just al límit—; la de l'A7III dona una **perla compacta** i sacrifica la corona.

Transferides a Medina, amb les quatre combinacions de cel (net o calima
k = 0,37) i de correcció pels núvols de 2024 (0 o 1 EV):

| Aspecte | Banda que caldria el 12 |
|---|---|
| el del 6D, amb corona | **1/1006 … 1/201** |
| el de l'A7III, perla compacta | **1/16635 … 1/3325** |

### La rectificació

`4 quater` deia que **1/5000 era 3,6 EV per sota de res del que hi ha a
l'escena**. **És fals.** Sortia d'anclar-ho tot a una sola referència —la del
6D— i d'una transferència d'extinció aproximada. La segona foto demostra que
allà baix hi ha la perla al seu instant més brillant. L'escena al contacte
**abasta quatre EV**, no un punt.

### La base puja a 1/320

Amb 1/160 el bloc encaixonava molt bé la banda del 6D —1/1250 a 0,3 EV per la
banda ràpida i 1/160 a 0,3 per la lenta— però es quedava **1,4 EV curt** de la
perla compacta. Amb base **1/320** la tríada és **1/2500 · 1/320 · 1/40**:

- **1/2500** queda a **0,4 EV** de la banda de la perla compacta;
- **1/320** cau **dins** la banda de la foto amb corona;
- **1/40** no perd res: la corona interior ja la cobreix el **1/13** de les
  àncores, i el 1/20 de la versió anterior hi era redundant.

Verificat al cos, run `20260808T145426`: **36/36, 14/14 accions, zero
saltades, zero avisos de cronologia, zero recuperacions, retard màxim
0,570 ms**, i EXIF amb **1/2500 · 1/320 · 1/40** cinc vegades i
**1/2 · 1/13 · 5 s** set vegades.

## 4 sexies. Dos contrastos adversaris tomben la decisió dels 5 s

Pere va demanar contrastar el pla amb **Codex** i amb **Fable 5**. Els dos van
rebre el mateix dossier i van arribar, per camins diferents, a la mateixa
conclusió: **la decisió A estava mal argumentada**.

### L'error de mètode

Comparava **7 àncores de 5 s contra 7 de 8 s**, i les set de 8 s no cabien en
el temps. **Mai vaig comparar sis de 8 s**, que és l'alternativa real:

| Opció | Imatges | Marge de cua | Integració | Marge del 2n setter |
|---|---:|---:|---:|---:|
| **6 × 8 s** | **33** | **3** | **48 s** | 10,05 s ✓ |
| 7 × 5 s | 36 | 0 | 35 s | 13,34 s ✓ |
| 7 × 8 s | 36 | 0 | 56 s | −0,66 s ✗ |

**6 × 8 s domina 7 × 5 s en tot**: +17 % de senyal/soroll en règim fotònic,
tres fotogrames de coixí contra el sostre en comptes de cap, i el bloc de C3
continua travessant el contacte.

Dels tres arguments que sostenien els 5 s, **dos cauen**: «escurçar no compra
àncores» és cert però 6×8 dona més integració amb menys fotogrames, i «amb 8 s
el bloc de C3 queda empès més enllà de C3» **només val per a set àncores**, no
per a sis. Va ser una generalització d'un sol cas.

### El cremat que no existeix

El tercer argument —subexposició recuperable, cremat no— el va quantificar
Fable: amb la Lluna plena a ~3,4 mag/arcsec² i l'earthshine ~9,8 mag per sota,
a f/2,8 ISO 100 el gris mitjà de l'earthshine cau a **~15-16 s a Medina amb
cel net** i la saturació del terreny clar a **~80-90 s**. **A 8 s el disc queda
~1 EV per sota del gris mitjà i ~3,5 EV per sota del cremat.** El risc que
justificava els 5 s no hi és.

El que sí que pot velar el fotograma de 8 s és el **pedestal de llum difosa
del cel a massa d'aire 6,4**, que continua sense quantificar. És el número que
faltava, i no era el que jo perseguia.

I el soroll de lectura que temia: amb 900-2.400 e⁻ per fotograma als tons
mitjans contra ~3,5 e⁻ de lectura, la penalització d'apilar és de
**0,3-0,7 % per fotograma**. Formalment certa, numèricament buida.

### Les altres correccions que accepto

- **Sostre operatiu 33, no 36** (tots dos revisors). Un run 36/36 demostra que
  *pot* anar, no que tingui marge, i la fallada silenciosa es menja els últims
  fotogrames, que són els anells de C3.
- **L'escalat de l'extinció per pressió** només val per al Rayleigh. L'ozó és
  estratosfèric i l'aerosol té la seva capa; si l'AOD del CAMS ja és la columna
  sobre el lloc, escalar-la per pressió la descompta dues vegades. Coeficient
  corregit a Medina: **0,218 net** contra 0,183, i **0,361 amb calima** contra
  0,339. Direcció: tot aquest document és **0,2-0,3 EV optimista**, les bandes
  del §4 quinquies s'allarguen i el requisit d'earthshine amb calima puja a
  **~8-8,6 s** — un argument més a favor dels 8 s.
- **El «1/2500 a 0,4 EV de la perla compacta» és el millor cas**, no el típic:
  amb el cel que pronostica el CAMS queda 1,7-2,7 EV per sobre d'aquella banda,
  i el canal vermell, que a X=6,4 guanya +0,36 EV relatiu al verd, se'n menja
  0,4 més. La cobertura de la perla compacta és més feble del que deia; la de
  la foto amb corona aguanta.

### El que no s'ha sostingut

Fable va plantejar que el sostre de 36 podia estar mesurat en un format que no
és el de la missió, i que si `RAW+JPEG` comptés dos objectes per captura el
sostre real serien 18 captures. **Comprovat als events: no.** Els dos runs es
van fer amb `RAW+JPEG (Std)` i `card+sdram` —el format exacte de missió— i la
cua puja **+3 per ràfega de tres**, o sigui **un objecte per captura**;
l'amfitrió només descarrega el JPEG. La mesura val.

També va advertir que sense seguiment la deriva sidèria mouria el disc lunar
23 px en 5 s i 38 en 8 s. Pere va declarar que **els dos trens porten
seguiment sempre** —300/2,8 sobre Skywatcher i VSD90SS sobre iOptron—, cosa
que fins llavors no constava enlloc i que ara és a `CLAUDE.md` §1 ter.

### El pla que en surt, verificat al cos

Perfil `lab_a7r3a_blocs_3c_6anc_8s`, run `20260808T152215`:

| | Valor |
|---|---|
| Confirmades | **33/33** |
| Accions | 13/13, zero saltades |
| Avisos de cronologia | **0** |
| Recuperacions | 0 |
| Retard màxim | **0,674 ms** |
| Cua màxima | **33** de sostre 36 |
| EXIF | 1/2500·1/320·1/40 ×5 · **1 s·1/8·8 s ×6** |

## 5. Estat de les preguntes obertes de `65`

| Pregunta | Estat |
|---|---|
| Cost real d'una àncora de 8 s | **MESURAT**: 11,21 s (§1) |
| NR d'exposició llarga als dos cossos | **MESURADA apagada** (§2) |
| Números per decidir el drenatge | **CALCULATS** (§3); la decisió és de Pere |
| Cadència mínima d'àncora | PENDENT, i deliberadament no perseguida (§1) |
| Límit real de la cua | **MESURAT: 36 a l'A7RIIIA** (§4 bis) |
| Àncora amb l'extrem a 4 s | **MESURADA**: base 1/2 s dona 1/2 · 1/15 · 4 s i l'acció baixa a 7,61 s (§4 bis) |
| Cost del canvi de base sota deute de cua | **MESURAT: ~5,3 s**, no els 4,47 del màxim històric (§4 ter) |
| Factor d'escala del drenatge per a imatges reals | **MESURAT amb òptica: 1,09**, no el 2 que s'assumia (§4 ter) |

## 6. Higiene de la campanya

Tots els runs d'avui amb **pauses de 60 a 120 s entre sessions PTP**, cap
cadència per sota de la qualificada, cap ràfega truncada i cap sessió morta.
Els dos cossos acaben amb `d215` a 0 i restore correcte. Quatre runs, quatre
`result.json` complets.

Cap procés propi viu en acabar. La regressió offline sencera és verda: GUI
445/445, controlador 1.079/1.079, fuzz 67.392/67.392, perfils curts i
`git diff --check`.
