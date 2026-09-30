# 65 — Mesures al banc de l'A7RIIIA i l'A7III per al disseny de blocs

Nit del 7 al 8 d'agost de 2026, desatès. Encàrrec de Pere: mesurar què és
determinista de veritat als dos cossos Sony per poder «jugar al tetris» amb
blocs, assumint una totalitat de més de 60 s i amb quatre objectius: perles i
anells a C2, protuberàncies just després de C2, rang dinàmic sencer de corona,
i earthshine amb SNR de sobres.

**Resum honest**: hi ha tres mesures noves i sòlides (§1, §2, §3), una
troballa operativa important que no buscava (§4), i **la campanya s'ha aturat
perquè els dos cossos han quedat caiguts a nivell PTP** (§5). Part de la culpa
és del mètode, i queda escrita.

## 0. Condicions del banc, i què invaliden

- **Cap dels dos cossos porta òptica**: tapa posada. Tots els fotogrames són
  negres i tots els JPEG surten amb la mateixa mida.
- Silent Shooting **ON** als dos.
- La reducció de soroll d'exposició llarga de l'A7RIIIA **estava activada**
  sense que ho sabéssim; Pere la va desactivar aquesta nit. **Tota mesura
  anterior de fotogrames de 8 s en aquest cos queda sota sospita.**

**Què és vàlid i què no**, per una raó concreta: el perfil declara RAW **sense
comprimir**, o sigui que la mida a la targeta **no depèn del contingut**. Per
tant són vàlides les mesures de durada de ràfega, cadència, escriptura a
targeta i límits de cua; **no** ho és el cabal de drenatge cap al Mac, que
descarrega JPEG, i el JPEG d'un fotograma negre és molt més petit que el d'una
corona.

## 1. L'ordre dels fotogrames dins una ràfega — MESURAT

`Bracketing C 3.0 Steps 3 Pictures` des de base 1/640, run `20260808T021550`,
EXIF dels dotze fitxers:

| Posició | Exposició | Biaix |
|---|---|---|
| 1r | 1/640 | 0 EV |
| **2n** | **1/5000** | **−3 EV** |
| 3r | 1/80 | +3 EV |

**El fotograma ràpid és el segon de tres**, no el primer. Amb ràfegues de cinc
l'ordre és 0, −3, +3, −6, +6 i el ràpid és el **quart de cinc**. Qualsevol
ràfega de contacte s'ha d'ancorar per aquest fotograma, no pel seu inici.

## 2. Cadència de re-disparament — MESURAT, i el límit no és net

Ràfegues de tres fotogrames ràpids a l'A7RIIIA, retenció de 0,5 s:

| Cadència | Resultat | Sessió |
|---|---|---|
| 2,5 s | 12/12 | viva |
| 2,0 s | 15/15, 15/15, després 3/15 | morta al tercer intent |
| 1,8 s | 0/15 tres vegades | **morta sempre** |

Mecanisme, del run `20260808T022111`: la primera ràfega va bé; **la segona
pulsació, enviada 1,8 s després, mata el procés `gphoto2`** amb
`OSError(5, 'Input/output error')`, i el transcript acaba amb `Cancelling...`.

**Conclusió operativa**: es manté la cadència qualificada de **2,9 s**. Per
sota de 2,5 s està demostrat insegur, i 2,0 s falla un cop de cada tres, que
per un eclipsi és que no.

## 3. Drenatge: l'A7III és 1,55 vegades més ràpid — MESURAT

Mateixa prova als dos cossos, dotze imatges:

| Cos | Temps | Per imatge | JPEG mitjà |
|---|---:|---:|---:|
| A7RIIIA (42 MP) | 6,53 s | **0,544 s** | 334 KB |
| **A7III (24 MP)** | **4,21 s** | **0,350 s** | 246 KB |

La intuïció de Pere es confirma. El factor de drenatge (1,55×) és més gran que
el de mida (1,36×): hi ha també una part de protocol per imatge que l'A7III
paga més barata.

**Matís que canvia la conclusió**: això fa els drenatges més barats, però **no
apuja el sostre de cua**, que és un recompte i no un cabal. Amb un disseny de
«no drenar dins la totalitat», els dos cossos topen igual. L'A7III només
guanya si el pla accepta drenar pel mig.

## 4. La troballa que no buscava: l'app roba els cossos

A mitja campanya vaig descobrir que **l'aplicació Eclipse Command estava
oberta** i feia el seu autocheck periòdic als dos cossos: hi havia un procés
seu fent un preflight a l'A7III mentre jo mesurava. Cada sondeig seu reclama
el dispositiu i **mata la sessió PTP de qui hi estigui treballant**.

Això és un **perill operatiu real per al dia de l'eclipsi**, no una anècdota
de banc: si algú deixa l'app oberta mentre una altra eina toca les càmeres,
o si l'autocheck no queda ben inhibit, es pot menjar una sessió de captura.
Val la pena revisar que l'autocheck estigui completament inhibit durant tota
la finestra de missió, no només durant el run.

## 5. Per què s'ha aturat la campanya, i què hi tinc a veure

Després d'una trentena de runs encadenats, **els dos cossos han deixat de
respondre a PTP**. Estat final comprovat:

- tots dos presents a l'IORegistry, bateria 95 %, targetes formatades;
- `ptpcamerad` no corre; l'app ja tancada;
- **fins i tot una captura simple per línia d'ordres falla**:
  `Timeout reading from or writing to the port`;
- el perfil de missió qualificat, que aquesta mateixa nit havia fet 60/60 tres
  vegades, dona 0/60.

O sigui que **no és cap defecte dels perfils de mesura ni del controlador: són
els cossos, que necessiten un cicle d'alimentació**.

**La part que em toca**: he encadenat sessions PTP amb segons de diferència,
he provat cadències que ja sabia que eren per sota del qualificat, i he
truncat ràfegues amb retencions curtes. El perfil qualificat ja advertia que
1,6 s trunca una ràfega de nou a 7/9; jo he retingut 0,4-0,5 s en ràfegues de
tres. Una campanya de banc en aquests cossos vol **pauses de minuts, no de
segons**, i cada mesura s'ha de dissenyar per no deixar el driver a mitges.

## 6. Estat de les preguntes

| Pregunta | Estat |
|---|---|
| Ordre dins la ràfega | **MESURAT** (§1) |
| Cadència mínima segura | **MESURAT**: ≥2,5 s; es manté 2,9 (§2) |
| Drenatge relatiu dels dos cossos | **MESURAT** (§3) |
| Cost real d'una àncora de 8 s amb la NR desactivada | **PENDENT** — cap intent ha sobreviscut |
| Límit real de la cua | PENDENT |
| Cost del canvi de base sota deute | PENDENT |
| Factor d'escala del drenatge per a imatges reals | **No es pot fer al banc**: sense òptica tots els JPEG són negres i iguals |

## 6 bis. El tetris de blocs que en surt, amb el que hi ha mesurat

Un sol `capturemode` tota la totalitat —`Bracketing C 3.0 Steps 3 Pictures`—
i només dos valors de base. Catàleg:

| Bloc | Base | Exposicions | Img | Cadència | Origen |
|---|---|---|---:|---:|---|
| **A — contacte** | 1/640 | 1/5000 · 1/640 · 1/80 | 3 | 2,9 s | **mesurat** |
| canvi de base | → 1 s | | 0 | 4,47 s | **mesurat** |
| **E — àncora** | 1 s | 1/8 · 1 s · **8 s** | 3 | 11,6 s | *assumit* |

**El bloc A cobreix dos objectius alhora.** Les perles i l'anell de diamant
volen el fotograma de 1/5000, i **les protuberàncies just després de C2**
volen 1/640 i 1/80, que és exactament el que la mateixa ràfega ja porta. Per
això el bloc A ha de travessar C2 i **allargar-se uns segons per la banda de
després**: no costa cap exposició nova.

Quantes àncores hi caben, amb dues ràfegues al bloc A:

| Totalitat | Àncores (= fotogrames de 8 s) | Imatges | Acaba a | Limita |
|---:|---:|---:|---:|---|
| 60 s | **4** | 18 | C2+55,9 | temps |
| 75 s | **5** | 21 | C2+67,5 | temps |
| 90 s | **6** | 24 | C2+79,1 | temps |
| 105 s | **8** | 30 | C2+102,3 | temps |
| 120 s | **9** | 33 | C2+113,9 | temps i cua |

**Amb ràfegues de tres el que mana és el temps, no la cua** —fins a 105 s—, al
revés que amb les de cinc. Això vol dir que **el número que decideix tot el
disseny és la cadència real d'una àncora**, avui assumida en 11,6 s a partir
del perfil qualificat de cinc fotogrames. Si la real fos ~10 s, hi cabria una
àncora més a cada durada.

És, exactament, la mesura que aquesta nit no ha sobreviscut.

**Comparació amb el que hi ha avui**: el programa actual fa **dues** àncores a
98,8 s. Aquest disseny en fa **sis a 90 s**, o sigui **1,73× més senyal/soroll**
en earthshine, i manté 1/5000 a 8 s = 15,3 EV de rang.

## 6 ter. El perfil ja està escrit i validat en sec

Quatre perfils al directori de treball de la sessió, un parell per cos:
`lab_*_blocs_2c_6anc` (dues ràfegues de contacte, 24 imatges) i
`lab_*_blocs_3c_6anc` (tres ràfegues, 27 imatges, el recomanat). Un sol
`capturemode`, un sol canvi de base. **Tots passen `validate` i `dry-run`
complets**, que no toquen la càmera.

A més, hi ha una **represa automàtica armada**: un procés vigila els dos cossos
cada cinc minuts i, quan tornin, executa sol la campanya pendent amb pauses de
60 s entre runs, en aquest ordre: cost de l'àncora de 8 s, perfil de blocs
sencer, i control de contacte. L'informe queda a `informe_represa.txt`.

El `dry-run` ha servit per a alguna cosa més que un vistiplau: ha detectat que
**cada àncora ha de declarar de quina escriptura de configuració depèn**
(`requires`). Sense això el pla no és determinista, perquè res no garanteix
que la base d'1 s ja hi sigui quan dispara. És exactament la mena de cosa que
el contracte del projecte hauria d'exigir i exigeix.

## 6 ter bis. Les protuberàncies volen una tercera ràfega, i quasi és gratis

L'objectiu (B) —protuberàncies just després de C2— el serveix la mateixa
ràfega de contacte: les protuberàncies volen 1/640 i 1/80, que hi són totes
dues. El que cal és **arribar-hi amb prou mostres per la banda de després**.

Amb tres ràfegues en comptes de dues, els fotogrames de 1/5000 cauen a
**C2−1,40, C2+1,50 i C2+4,40**, i cada una porta el seu 1/640 i 1/80 per a les
protuberàncies.

Cost, en àncores:

| Totalitat | 2 ràfegues | 3 ràfegues | 4 ràfegues |
|---:|---|---|---|
| 60 s | 4 àncores | **4 àncores** | 4 àncores |
| 75 s | 5 | **5** | 5 |
| 90 s | 7 | **6** | 6 |
| 105 s | 8 | **8** | 7 |
| 120 s | 9 | **8** | 7 |

**A 60, 75 i 105 s la tercera ràfega és gratis.** A 90 i 120 costa una àncora,
que en senyal/soroll són un 8 %. Amb quatre objectius sobre la taula i les
protuberàncies essent un d'ells, la recomanació és **tres ràfegues de
contacte**. La quarta ja no compensa: no afegeix res que la tercera no doni i
costa una àncora a la meitat de les durades.

## 6 quater. Quant depèn el disseny del número que falta

L'única entrada important que no s'ha pogut mesurar és **la cadència real
d'una àncora**, avui assumida en 11,6 s des del perfil qualificat de cinc
fotogrames. Nombre d'àncores segons la cadència real:

| Cadència real | 60 s | 75 s | 90 s | 105 s | 120 s |
|---:|---:|---:|---:|---:|---:|
| 9,5 s | 5 | 6 | 8 | 9 | 9 |
| 10,0 s | 5 | 6 | 8 | 9 | 9 |
| 10,5 s | 4 | 6 | 7 | 9 | 9 |
| 11,0 s | 4 | 5 | 7 | 8 | 9 |
| **11,6 s (assumit)** | **4** | **5** | **6** | **8** | **9** |
| 12,5 s | 4 | 5 | 6 | 7 | 8 |
| 14,0 s | 3 | 4 | 5 | 6 | 7 |

**El disseny és robust a aquest número**: entre 9,5 i 12,5 s de cadència, a
90 s de totalitat surten entre 6 i 8 àncores, i qualsevol d'aquests valors ja
és tres vegades el que fa el programa d'avui. Només si la cadència real fos
de 14 s el disseny perdria una àncora respecte del previst.

Senyal/soroll de l'earthshine apilat: 2 àncores donen 1,41×, sis en donen
**2,45×**, nou en donen 3,00×. El programa actual en fa dues.

## 7. El que cal de Pere, i és una sola cosa

**Apagar i tornar a encendre els dos cossos.** Amb això la campanya es reprèn
on ha quedat. Les proves ja estan escrites i preparades; la primera que
s'executarà és el cost real de l'àncora de 8 s, que és el número que mana
sobre tot el disseny d'earthshine.

I una recomanació que surt de §4: **no deixar l'app oberta** mentre es mesura.
