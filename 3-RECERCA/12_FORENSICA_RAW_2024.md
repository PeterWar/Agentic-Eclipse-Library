# Forense dels RAW crítics de 2024

## Veredicte

El problema de 2024 no sembla una única limitació del búfer. Els fitxers
demostren tres comportaments diferents:

1. **Canon 6D:** captura contínua i regular durant 290 s, sense cap buit
   anòmal.
2. **A7III:** una seqüència útil, però amb buits reals de **30 s** i
   **125 s**. El de 125 s cau entre els dos últims passos d'una mateixa
   escala HDR.
3. **A7S:** cap buit enorme, però una cadència lenta per la descàrrega de cada
   RAW i, sobretot, velocitats reals que no segueixen l'ordre programat. A C3
   no hi ha cap `1/8000`, tot i que era l'exposició que el script ordenava.

La causa arquitectònica més perillosa és visible als scripts: les captures
Sony sí que fixaven `--port`, però **cap ordre `--set-config` fixava el port**.
Amb més d'una càmera al mateix ordinador, es podia configurar un cos i
disparar-ne un altre. A això s'afegeixen una sessió PTP nova per cada ordre,
errors ignorats, absència de readback, descàrrega síncrona de l'A7S i funcions
temporals que podien acabar després del límit de fase.

Per tant, la lectura més ben sustentada és:

> El 2024 va fallar principalment la coordinació entre identitat de càmera,
> estat confirmat i temps límit de les ordres; el búfer pot haver contribuït,
> però els RAW no permeten convertir-lo en la causa principal.

## Abast i traçabilitat

Directori real auditat, només en lectura:

`/Users/USUARI/Dropbox/Astrofotografia/Eclipse Solar 2024/Eclipse (short)`

La ruta real no conté `Scripts`. El directori dels scripts és `Script`, en
singular. `Versió final que es va fer servir` està codificat en Unicode NFD
(`o` + accent combinant), no en NFC.

S'han llegit les estructures TIFF/EXIF directament, sense `exiftool` i sense
revelar ni copiar els RAW. Per detectar duplicats exactes s'ha calculat el
SHA-256 complet dels 260 fitxers.

El número de cos està present a l'EXIF estàndard de la Canon. Els dos Sony
no exposen `BodySerialNumber` en aquests ARW; no s'ha intentat convertir una
cadena opaca del MakerNote en número de sèrie sense documentació.

Resultats reproduïbles:

- `research/data/2024_raw_timeline.csv`: una fila per RAW, amb EXIF,
  seqüència, mida, hash, cadència i distància als contactes de l'A7S;
- `research/data/2024_exposure_runs.csv`: blocs consecutius de velocitat i
  ISO;
- `research/data/2024_raw_summary.csv`: resum per sistema;
- `research/tools/extract_2024_raw_timeline.py`: extractor offline.

## Resum quantitatiu

| Sistema | RAW | Font temporal | Interval | Mediana | Màxim | Buits anòmals | Números absents | Duplicats SHA-256 |
|---|---:|---|---:|---:|---:|---|---:|---:|
| Canon 6D + 300 mm | 146 | EXIF amb centèsimes | 289,93 s | 2,03 s | 3,59 s | cap | 0 de 9428–9573 | 0 |
| A7III + AP130/QUADTCC | 56 | EXIF, només segons | 291 s | 2 s | **125 s** | 30 s i **125 s** | 0 de 6585–6640 | 0 |
| A7S + Questar | 58 | nom creat pel controlador | 325 s | 6 s | 10 s | cap >10 s | no numerat | 0 |

La continuïtat `DSC06585`–`DSC06640` i `_MG_9428`–`_MG_9573`
és important: dins els intervals seleccionats no hi ha salts de numeració.
El buit de l'A7III no és conseqüència d'haver oblidat copiar uns fitxers
intermedis: la càmera no va assignar cap número entre `DSC06631` i
`DSC06632`. Tampoc hi ha timestamps d'anàlisi repetits en cap dels tres
sistemes.

## A7III: reconstrucció del buit crític

### Seqüència observada

La primera escala és coherent i conté dues preses per nivell:

`1/500 → 1/250 → 1/100 → 1/30 → 1/15 → 1/8 → 0,4 → 1 → 2 → 0,8 s`

Va de `DSC06594`, 19:08:13, a `DSC06613`, 19:09:05. Després:

- hi ha **30 s** fins a `DSC06614`;
- la segona escala comença anòmalament a `1/200`, després passa a `1/250`,
  i continua fins a `2 s`;
- `DSC06631`, ISO 200 i 2 s, és de les 19:10:21;
- `DSC06632`, ISO 100 i 0,8 s, és de les 19:12:26;
- entre totes dues hi ha **125 s sense cap RAW**;
- després venen sis `1/8000` i un `1/400`, tots a ISO 100.

El detall decisiu és que `0,8 s` és el pas que seguia `2 s` en l'escala
guardada. Per tant, el buit no és simplement una espera neta entre dues
escales: cau al mig de la transició final de l'escala.

A la cadència mediana observada de 2 s, el buit de 125 s equival a unes
**61 oportunitats de captura** entre els dos fotogrames; el de 30 s, a unes
14. Són estimacions de capacitat perduda, no una afirmació que el guió
preveiés exactament 75 ordres.

### Què prova i què no prova

**Provat pels RAW**

- no es va desar cap foto durant 125 s;
- no hi ha números de fitxer absents;
- l'ISO canvia de 200 a 100 durant el buit;
- la velocitat reprèn a l'últim pas de l'escala, `0,8 s`;
- tots els ARW són de 6.048 × 4.024, RAW sense comprimir, etiqueta de 14 bits;
- els 56 SHA-256 són diferents.

**Inferència forta**

Una ordre PTP, un canvi de configuració o la reobertura de sessió va quedar
bloquejada o va perdre el control del cos. El canvi inesperat d'ISO reforça
la possibilitat d'una reconfiguració o interferència d'un altre procés.

**No demostrable amb els RAW**

- quina crida concreta de `gphoto2` va quedar bloquejada;
- si el retard va ser USB/PTP, competència entre processos, targeta/búfer o
  una combinació;
- si l'ISO 100 el va posar el mateix script, un segon script o una acció
  manual.

## A7S: el script i la càmera van divergir

L'EXIF de l'A7S conserva l'any **2014**. Els noms
`20240408_HHMMSS...` els crea el Mac abans d'invocar
`--capture-image-and-download`; són temps de petició, no timestamps exactes
del sensor. Tot i això, el rellotge EXIF i aquests noms avancen els mateixos
325 s de principi a final, de manera que l'ordre relatiu és sòlid.

### Blocs reals

| Velocitat | RAW | Patró |
|---|---:|---|
| `1/640` | 8 | 3 abans de C2 i 5 després de C3 |
| `1/5000` | 2 | just abans de C2 |
| `1/320` | 16 | bloc continu després de C2 |
| `1/20` | 12 | 10 + 2 |
| `1 s` | 5 | bloc continu |
| `1/8` | 5 | bloc continu |
| `1/40` | 8 | bloc continu |
| `1/400` | 2 | després de C3 |

En canvi, `A7SFinal.sh` programava dins cada volta de totalitat:

`1/320 → 1/40 → 1/20 → 1/8 → 1/2 → 1 → 0,8 s`

Els RAW no alternen aquesta escala. A més, no existeix cap captura a
`1/100`, `1/2`, `0,8 s` ni `1/8000`, tot i que són valors ordenats pel
fitxer guardat.

La comparació posicional entre el bucle i els 45 RAW creats durant la
finestra de totalitat és encara més concloent: **35 de 45 (78%)** no tenen
la velocitat que el guió acabava de demanar per a aquella presa. Els canvis
reals arriben en blocs tardans —primer `1/20` al frame 17, `1 s` al 27,
`1/8` al 32 i `1/40` al 37—, no en l'escala alternada prevista.

Una de les ordres era invàlida per al vocabulari exposat per aquell cos:
`OLD/sony_a7s_settings.txt` enumera mig segon com a `5/10`, no `1/2`.
Com que el guió no inspeccionava el codi de retorn ni rellegia la velocitat,
disparava igual després d'un `set-config` rebutjat.

Això és evidència directa que les configuracions no van ser aplicades a
l'A7S com s'esperava. La cerca de scripts reforça la identificació:
`A7SFinal.sh` és l'únic fitxer de tot l'arbre que genera el sufix
`total.arw`, exactament el dels 58 RAW.

La correlació de mtime és també significativa. Els RAW descarregats tenen
mtime nou hores i només 0–2 s per davant del HH:MM:SS del nom quan es
visualitzen ara en zona Europe/Madrid. Aplicant el mateix offset, el mtime de
`A7SFinal.sh`, 19:57:10 CEST, correspon a les 10:57:10 del rellotge del
controlador: uns 11 min 39 s abans de C2. Això fa molt probable que sigui la
versió preparada immediatament abans d'executar-la, no un retoc posterior.
El patró de blocs és incompatible amb una execució correcta de les
configuracions d'aquest bucle.

### Contactes del controlador

`A7SFinal.sh` fixa:

- C2: 11:08:49;
- C3: 11:13:17;
- totalitat programada: 268 s.

Respecte dels noms generats pel controlador:

| Contacte | Abans | Després | Lectura |
|---|---|---|---|
| C2 | `1/5000` a −5 s i −2 s | `1/320` a +4 s | cobertura curta útil de C2 |
| C3 | `1/20` a −3 s | `1/20` a +4 s; `1/400` a +11 i +14 s | **cap `1/8000`; Baily C3 no cobert com estava previst** |

El motiu lògic del C3 perdut també és visible al codi: les funcions fan
captures i descàrregues bloquejants, i `CURRENT` només s'actualitza entre
grups. Quan la funció de totalitat retorna després de C3+5, la branca
`1/8000` ja no és elegible i el programa salta directament a `1/400`.

## Canon 6D: la referència de robustesa

La Canon conserva `DateTimeOriginal` amb centèsimes i el número de cos
`[SÈRIE]`. Els 146 fitxers:

- són consecutius de `_MG_9428` a `_MG_9573`;
- no tenen cap buit superior a 3,59 s;
- són tots ISO 200;
- no tenen cap duplicat exacte;
- cobreixen 15 velocitats, de `1/4000` a `1 s`.

La part central repeteix escales denses de dues preses per nivell:

`1/4000 → 1/2500 → 1/1000 → 1/500 → 1/200 → 1/80 → 1/30 → 1/15 → 1/8 → 1/4 → 0,4 → 0,6 → 1 s`

Hi ha aproximadament cinc escombrats, amb una sola presa d'1 s en diversos
d'ells. És la cadena temporalment més regular de les tres.

El `Canon6DFinal.sh` minúscul que hi ha dins `Versió final...` és posterior
a l'eclipsi i sintàcticament invàlid. El `Canon6DFinal.sh` del directori
pare és més complet, però tampoc no reprodueix literalment l'escala EXIF.
No s'ha conservat de manera inequívoca el script exacte de la seqüència
Canon.

## Per què el sistema de 2024 podia fallar

### 1. Configuració sense identitat de càmera

Comptatge literal dels scripts:

| Script | Ordres config | Config amb `--port` | Ordres captura | Captures amb `--port` |
|---|---:|---:|---:|---:|
| `A7SFinal.sh` | 14 | **0** | 1 funció | 1 |
| `A7IIIFINAL.sh` | 17 | **0** | 2 per parella | 2 |
| `Script/Canon6DFinal.sh` | 16 | **0** | 2 per parella | **0** |

Per tant, en un host amb diversos cossos:

1. `--set-config shutterspeed=...` podia actuar sobre el cos autodetectat;
2. `--trigger-capture --port ...` podia disparar un cos diferent;
3. el script no llegia el valor després d'escriure'l;
4. el RAW era l'únic lloc on, massa tard, quedava constància de la velocitat
   real.

El log de depuració confirma a més que `gphoto2` desava `model` i `port` a
la configuració global d'usuari `~/.gphoto/settings`. Una ordre posterior
sense identitat explícita podia dependre d'aquest estat mutable, alterat per
un altre procés. Amb scripts concurrents, no era només un risc teòric
d'autodetecció: compartien una selecció global persistent.

Si el 2024 cada cos s'executava en un ordinador físic diferent, desapareix la
possibilitat de contaminació entre cossos, però continua existint la manca
d'identitat verificable i de readback.

Hi ha un indici que obliga a mantenir aquesta condició oberta:
`A7SFinal.sh` usa `date -d` de GNU/Linux, mentre els scripts A7III/Canon usen
`date -j` de BSD/macOS. L'A7S podria haver corregut en un host diferent.
Cal confirmar amb l'operador quins cossos compartien ordinador; el risc de
contaminació continua sent especialment directe entre A7III i Canon si
compartien el Mac.

### 2. Una sessió PTP nova per cada pas

Els scripts no mantenen una sessió. Cada canvi de velocitat i cada
`trigger-capture` obre un procés `gphoto2` nou, negocia USB/PTP, executa una
ordre i tanca.

Hi ha una evidència de laboratori anterior a l'eclipsi:

`OLD/gphoto2-log.txt`, del 10 de febrer de 2024, mostra `gphoto2 2.5.28`
autodetectant explícitament `Sony Alpha-A7 III (PC Control)` i intentant
obrir-la. La crida acumula timeouts PTP als 8,52, 16,83 i 25,26 s, torna a
intentar-ho i acaba a **50,70 s**.

No és el log del 8 d'abril i no prova que sigui la crida exacta del buit de
125 s. Sí que prova que aquesta arquitectura ja havia exhibit, abans del
viatge, bloquejos d'una durada suficient per destruir una finestra crítica.

### 3. Errors silenciosos

No hi ha:

- comprovació sistemàtica de `$?`;
- `set -e` o gestió d'errors per ordre;
- timeout extern;
- reintent acotat;
- lectura posterior de velocitat o ISO;
- log amb hora monotònica, cos i número d'ordre.

L'A7III envia la sortida normal de captura a `/dev/null`. Una ordre fallida
podia consumir desenes de segons i el guió continuava sense saber quin estat
tenia la càmera.

### 4. Descàrrega dins la finestra crítica

L'A7S fa `--capture-image-and-download` per cada foto, després `sleep 0.8` i,
en alguns trams, un altre `sleep 1`. La mediana real és 6 s, tres vegades la
de l'A7III i la Canon.

La descàrrega bloquejant no només redueix el nombre de RAW: retarda la
reavaluació de C2/C3 i pot fer que una branca crítica quedi saltada.

### 5. Fitxer “final” no reproduïble

- `A7IIIFINAL.sh` conserva una data de prova de març i ordena exposicions de
  10, 5 i 3 s que no apareixen als RAW.
- `A7SFinal.sh` té data real, però l'ordre d'exposicions no concorda amb els
  RAW.
- el `Canon6DFinal.sh` del subdirectori “final” no pot generar la seqüència
  observada.

Sense hash del script executat, còpia immutable i log d'ordres, no es pot
atribuir retrospectivament cada RAW a una línia concreta.

## Hipòtesis causals, ordenades

| Hipòtesi | Valoració | Evidència |
|---|---|---|
| Configuració i captura no adreçades al mateix cos | **molt plausible** si compartien host | tots els `set-config` sense port; patrons EXIF divergents |
| Sessió PTP/USB bloquejada o en competència | **molt plausible** | buit de 125 s al mig d'una escala; log previ amb bloqueig de 50,7 s |
| Sobreeiximent temporal de funcions bloquejants | **demostrat a l'A7S C3** | `1/8000` absent i retorn després de la finestra |
| Descàrrega RAW durant totalitat | **demostrat i costós** | mediana A7S de 6 s |
| Búfer/targeta saturats | possible, no provat | podria afegir espera, però no explica sol els estats/ISO erronis |
| RAW capturats però perduts en copiar | poc probable dins el tall | numeració Sony/Canon contínua i hashes únics |

## Implicacions obligatòries per al controlador 2026

1. Una identitat de cos immutable per procés: port i número de sèrie
   verificats abans de qualsevol escriptura.
2. La mateixa sessió persistent per configurar, disparar i llegir resposta.
3. `set → readback`; si el valor no coincideix, no es dispara a cegues.
4. Cap descàrrega durant C2–C3; escriure a targeta/búfer i drenar després.
5. Deadline per acció i per fase: una escala tardana s'avorta abans de
   menjar-se Baily/diamond ring.
6. `capture=1` i `capture=0` amb watchdog i alliberament d'emergència.
7. Registre UTC + monotònic de l'instant real d'enviament, ACK, estat,
   cua i error.
8. Hash del perfil i del controlador executats, guardat amb el run.
9. Postflight automàtic: previstos versus número, EXIF, ISO, velocitat i
   cadència real.
10. Prova multi-càmera explícita: ordres simultànies i verificació que cap
    cos rep configuració destinada a l'altre.

## Límit de la reconstrucció temporal

No es poden alinear els tres cossos a nivell de segon absolut:

- A7III: hora 19:xx, `OffsetTimeOriginal=+01:00`, sense subseconds;
- Canon: hora 20:xx, sense offset, però amb centèsimes;
- A7S: data 2014; només els noms del controlador tenen data de 2024.

Per això els C2/C3 exactes només s'han correlacionat amb l'A7S, el cos que
incorpora als noms l'hora del mateix controlador que definia els contactes.
Per a A7III i Canon, les transicions de `1/8000`/`1/4000` a escala HDR i
viceversa permeten identificar qualitativament els voltants de C2/C3, però
no són una base vàlida per assignar offsets absoluts.
