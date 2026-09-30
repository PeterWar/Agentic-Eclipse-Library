# Autòpsia causal de la captura de 2024

## Veredicte

El 2024 no va fallar una sola cosa ni es pot atribuir tot al búfer. Hi ha dos
falliments principals, diferents i demostrables:

1. **A7S: el programa disparava, però la configuració de velocitat quedava
   majoritàriament desalineada de la càmera.** En la reconstrucció
   ordre-a-RAW de totalitat, **35 de 45 captures (77,8%)** no tenen la
   velocitat que corresponia al seu slot del guió. A més, un dels valors
   demanats, `1/2`, ni tan sols figura entre les opcions que l'A7S exposava a
   gphoto2: la forma admesa era `5/10`.
2. **A7III: la seqüència HDR es va interrompre dues vegades, 30 s i 125 s.**
   El segon buit cau exactament entre la parella de 2 s i la parella de
   0,8 s d'una mateixa escala; durant el buit l'ISO passa de 200 a 100.

La causa sistèmica comuna és una arquitectura sense confirmació d'estat ni
límit temporal: els `set-config` no identificaven el cos, cada ordre obria un
procés i una sessió PTP nous, els errors no es comprovaven, no hi havia
`readback`, `timeout`, watchdog ni log estructurat, i una funció bloquejada no
podia ser interrompuda en arribar C2 o C3.

La descàrrega síncrona de cada RAW explica la baixa cadència de l'A7S i va
contribuir a perdre el C3 curt. En canvi, **el búfer/targeta continua sent una
hipòtesi plausible per als buits de l'A7III, però els fitxers disponibles no
permeten declarar-lo causa única ni principal**.

## Com llegir aquest informe

S'utilitzen tres etiquetes:

- **FET:** literal del codi, metadada RAW, hash o log conservat.
- **RECONSTRUCCIÓ:** resultat derivat de combinar fets amb una correspondència
  explícita i comprovable.
- **INFERÈNCIA:** explicació causal compatible amb els fets, però no registrada
  directament el dia de l'eclipsi.

Escala de confiança:

- **molt alta:** la conclusió no depèn d'una hipòtesi causal;
- **alta:** encaixa de manera específica amb diverses fonts independents;
- **mitjana:** plausible i important, però falta una dada discriminant;
- **baixa:** possible, sense evidència específica suficient.

## Fonts auditades

Per abreujar, en aquest document:

- `FINAL` =
  `/Users/USUARI/Dropbox/Astrofotografia/Eclipse Solar 2024/Script/Versió final que es va fer servir`
- `RAW` =
  `/Users/USUARI/Dropbox/Astrofotografia/Eclipse Solar 2024/Eclipse (short)`

Artefactes reproduïbles del projecte:

- `research/data/2024_raw_timeline.csv`
- `research/data/2024_exposure_runs.csv`
- `research/data/2024_raw_summary.csv`
- `research/tools/extract_2024_raw_timeline.py`

No s'ha modificat cap script ni RAW de 2024.

## 1. Quin script es va executar realment?

### 1.1 A7S: identificació molt forta de `A7SFinal.sh`

**FETS**

- Els 58 fitxers de la seqüència crítica tenen noms
  `YYYYMMDD_HHMMSS total.arw`.
- `A7SFinal.sh:5` és l'única instrucció de tot l'arbre que genera literalment
  el sufix `total.arw`; n'hi ha dues còpies idèntiques, una al directori pare
  i una a `FINAL`.
- Les dues còpies tenen el mateix SHA-256:
  `5f856efcc441cb2ee1bb24a7be5e31a186eeffe18b3404a6682ae77906949c82`.
- Els contactes del fitxer, C2 `11:08:49` i C3 `11:13:17`
  (`A7SFinal.sh:32-36`), coincideixen amb les transicions dels noms:
  `1/5000` a C2−5 i C2−2, primera `1/320` a C2+4, i transició post-C3.
- La seqüència crítica fa servir exactament el mecanisme de la línia 5:
  captura, descàrrega, nom local amb `total.arw` i conservació a càmera.

**CONCLUSIÓ — confiança molt alta**

`A7SFinal.sh` és el codi que va governar aquesta seqüència, o una còpia
byte-a-byte idèntica. La pista `*total.arw` elimina la principal incertesa de
proveniència que sí que existeix per a l'A7III i la Canon.

### 1.2 A7III: identificació de família, no de fitxer exacte

**FETS**

- Els RAW observen aquest ordre a C2 i totalitat:
  `1/400`, `1/8000`, i després
  `1/500 → 1/250 → 1/100 → 1/30 → 1/15 → 1/8 → 0,4 → 1 → 2 → 0,8 s`,
  habitualment per parelles.
- Aquest ordre coincideix literalment amb
  `FINAL/OLD/A7IIIFINAL-backup.sh:36-117`.
- El fitxer actual `FINAL/A7IIIFINAL.sh` no coincideix: demana 10, 5 i 3 s
  (`:78-88`), valors absents dels RAW, i conserva data de prova
  `2024-03-21` (`:34-38`).
- `FINAL/A7III.sh` conserva una data de prova i és sintàcticament invàlid.
- El backup que sí coincideix en exposicions conserva data
  `2024-03-19`, no 8 d'abril.

**RECONSTRUCCIÓ — confiança alta en la família, mitjana en el fitxer**

L'A7III va ser governada per una versió de la família
`A7IIIFINAL-backup.sh`, amb els contactes del dia real, però aquesta còpia
exacta no s'ha conservat o no s'ha identificat. No és rigorós afirmar que el
fitxer anomenat `A7IIIFINAL.sh` actual fos l'executable real.

### 1.3 Canon: controlador exacte desconegut

**FETS**

- Els 146 CR2 formen una escala densa i regular, aproximadament cinc
  escombrats, sense cap buit superior a 3,59 s.
- `FINAL/Canon6DFinal.sh` té un `fi` sense `if` a la línia 26 i no passa
  `bash -n`.
- Aquell fitxer només repeteix una mateixa captura i no pot generar la
  seqüència de quinze velocitats observada.
- El `Canon6DFinal.sh` del directori pare tampoc reprodueix tota l'escala
  observada.

**CONCLUSIÓ — confiança molt alta**

La seqüència Canon prové d'un altre guió, intervalòmetre o procediment que no
ha quedat preservat de manera inequívoca. És la cadena més regular de 2024,
però no se'n pot copiar honestament el mecanisme fins a identificar-lo o
reconstruir-lo experimentalment.

## 2. Prova quantitativa: el 77,8% de divergència de l'A7S

### 2.1 Seqüència programada

`A7SFinal.sh:83-111` executa set slots per volta:

| Slot | Velocitat demanada |
|---:|---|
| 1 | `1/320` |
| 2 | `1/40` |
| 3 | `1/20` |
| 4 | `1/8` |
| 5 | `1/2` |
| 6 | `1 s` |
| 7 | `0,8 s` (`8/10`) |

La funció principal torna a cridar aquesta escala mentre encara és abans de
C3−10 (`A7SFinal.sh:149-151`).

### 2.2 Seqüència real

Entre la primera presa de totalitat (`11:08:53`) i l'última abans de la
finestra C3 (`11:13:14`) hi ha 45 RAW. Els blocs EXIF reals són:

| Ordinals | Hora | RAW | Velocitat real |
|---|---|---:|---|
| 1–16 | 11:08:53–11:10:18 | 16 | `1/320` |
| 17–26 | 11:10:26–11:11:17 | 10 | `1/20` |
| 27–31 | 11:11:22–11:11:51 | 5 | `1 s` |
| 32–36 | 11:11:59–11:12:24 | 5 | `1/8` |
| 37–44 | 11:12:28–11:13:07 | 8 | `1/40` |
| 45 | 11:13:14 | 1 | `1/20` |

Font: `research/data/2024_exposure_runs.csv`, blocs 97–102.

No hi ha cap `1/2` ni cap `0,8 s` a la seqüència crítica.

### 2.3 Càlcul

**RECONSTRUCCIÓ**

Quaranta-cinc captures equivalen a sis voltes completes de set slots més els
tres primers slots de la setena volta. En assignar cada RAW al slot successiu
del guió:

- coincideixen els ordinals
  `1, 8, 15, 17, 24, 27, 32, 37, 44 i 45`;
- **10 de 45** coincideixen;
- **35 de 45** no coincideixen;
- `35 / 45 = 0,777…`, és a dir, **77,8% de divergència**.

La forma dels blocs reforça la correspondència. Els canvis reals apareixen
just en slots que demanaven aquell valor: `1/20` a l'ordinal 17, `1 s` al 27,
`1/8` al 32, `1/40` al 37 i de nou `1/20` al 45. És el patró esperable quan
algunes escriptures de configuració tenen èxit, moltes fallen, i la càmera
conserva l'últim valor acceptat.

**LÍMIT**

El 77,8% és una reconstrucció i no un log d'ACK, perquè el 2024 no es va
guardar cap log d'ordres. Pressuposa que el procés no es va reiniciar dins
la totalitat; no hi ha cap indici de reinici i l'alineació dels canvis amb els
slots ho fa molt improbable. Encara que s'abandonés aquesta assignació
ordinal, el fet robust no canvia: el guió ordenava una escala alterna de set
valors i els RAW mostren blocs llargs d'un sol valor.

### 2.4 Divergències directes als contactes

Aquestes comparacions no depenen de repetir l'escala de set slots:

- Entre C2−24 i C2−15, la branca activa havia executat
  `shutterspeed=1/100` (`A7SFinal.sh:54-63`), però els tres RAW són `1/640`.
- A C2−5 i C2−2, la branca següent havia executat `1/5000` (`:65-72`) i els
  dos RAW sí que són `1/5000`.
- A C3+4, la branca curta havia executat `1/8000` (`:115-124`), però el RAW
  continua a `1/20`.
- A C3+11 i C3+14, la branca posterior executa `1/400` (`:126-133`) i els
  dos RAW sí que són `1/400`.

**FET**

En un mateix executable, unes transicions de configuració s'aplicaven i
d'altres no. Això descarta que tota la discrepància sigui només un error
d'alineació teòrica del càlcul del 77,8%.

## 3. Error literal: `1/2` no era un valor admès

**FETS**

- `A7SFinal.sh:96` executa:
  `gphoto2 --set-config shutterspeed=1/2`.
- La configuració guardada de la mateixa A7S
  (`FINAL/OLD/sony_a7s_settings.txt:450-509`) enumera totes les opcions
  exposades per gphoto2.
- Entre `1 s` i `0,4 s`, les opcions són `8/10`, `6/10`, **`5/10`** i
  `4/10` (`:470-474`).
- No hi ha cap opció literal `1/2`.
- Cap RAW crític té 0,5 s.
- El codi font oficial de
  [gphoto2 2.5.28](https://github.com/gphoto/gphoto2/blob/v2.5.28/gphoto2/actions.c)
  —la versió documentada al log antic de l'A7III— primer busca una
  coincidència literal, només interpreta un índex si **tota** la cadena és un
  enter, i finalment prova el valor directe. Per tant, `1/2` no es podia
  confondre amb l'índex `1`; havia de ser acceptat pel setter flexible o
  retornar error.

**CONCLUSIÓ — confiança molt alta**

`1/2` no era una elecció vàlida dins el perfil de configuració capturat. La
representació que s'havia d'haver validat contra la càmera era `5/10`. No
tenim el codi de retorn del dia, i no consta la versió gphoto2 de l'host de
l'A7S; per això el fet estricte és «valor absent del menú i no observat als
RAW», no un missatge d'error concret reconstruït a posteriori.

Aquest error explica de manera directa almenys el fracàs sistemàtic del slot
de 0,5 s. No explica per si sol que fallessin també ordres vàlides com
`1/40`, `1/20`, `1/8`, `1` o `8/10`; per a això calen els mecanismes de
comunicació i estat descrits a continuació.

## 4. Per què fallaven també velocitats vàlides?

### 4.1 Configurar un cos i disparar-ne potencialment un altre

**FETS**

- A `A7SFinal.sh`, la captura sí usa
  `--port "$CAMERA_PORT"` (`:5`).
- Cap dels 14 `set-config` del mateix fitxer usa `--port`
  (`:38, 41, 56, 65, 83, 85, 87, 94, 96, 103, 110, 117, 126, 159`).
- A la família A7III passa el mateix: les configuracions no fixen ni port ni
  número de sèrie.
- `FINAL/OLD/gphoto2-log.txt:30-36` mostra una invocació sense model ni port
  que carrega `~/.gphoto/settings` i decideix autodetectar.
- El mateix log autodetecta l'A7III i desa globalment model i port a
  `~/.gphoto/settings` (`:95-111`).

**INFERÈNCIA — confiança alta si compartien host; mitjana si eren hosts
separats**

En un mateix ordinador amb més d'un cos, un `set-config` no qualificat podia
anar al cos seleccionat per l'estat global, mentre la captura posterior,
qualificada amb `--port`, anava a l'A7S. L'alternança de processos de
diversos scripts podia canviar aquell estat global.

No s'ha de convertir aquesta inferència en fet sense reconstruir la topologia
del dia. `A7SFinal.sh` usa `date -d` de GNU/Linux i els scripts A7III usen
`date -j` de BSD/macOS; és possible que l'A7S corregués en una altra màquina.
Si cada Sony tenia host exclusiu, desapareix la contaminació entre cossos,
però no la dependència d'autodetecció, ni la manca de readback, ni els
falliments PTP.

### 4.2 Una sessió PTP nova per cada ordre

**FETS**

- Cada `gphoto2 --set-config` és un procés independent.
- Cada captura A7III de la família identificada obre dos processos
  `gphoto2 --trigger-capture --wait-event=CAPTURECOMPLETE`
  (`A7IIIFINAL-backup.sh:16-23`).
- No hi ha cap sessió persistent ni bloqueig exclusiu de càmera.
- `FINAL/OLD/gphoto2-log.txt` no és del dia de l'eclipsi, però documenta la
  mateixa A7III i versions gphoto2/libgphoto2 2.5.28/2.5.31.
- En aquell log, obrir una sessió PTP falla tres vegades als 8,52, 16,83 i
  25,26 s (`:121-144`); gphoto2 torna a inicialitzar i repeteix els timeouts
  fins a acabar als **50,57 s** (`:177-209`).

**INFERÈNCIA — confiança alta com a vulnerabilitat; mitjana com a causa del
buit concret**

L'entorn ja havia demostrat abans de l'eclipsi que una sola invocació nova
podia consumir uns 50,6 s només intentant obrir PTP. Dues o més operacions
encadenades, o una espera d'esdeveniment perdut, són compatibles amb un buit
de 125 s. Com que aquell log és de febrer, no prova quina crida es va aturar
el 8 d'abril.

### 4.3 Errors invisibles i estat mai verificat

**FETS**

Els scripts no tenen:

- comprovació sistemàtica del codi de retorn;
- lectura posterior de velocitat o ISO;
- timeout extern;
- reintent acotat;
- watchdog;
- registre d'hora d'inici, ACK, final i error;
- verificació que el RAW resultant té l'exposició sol·licitada.

La família A7III envia només `stdout` a `/dev/null`; `stderr` no queda
conservat. L'A7S incrementa el comptador després de la crida sense comprovar
si l'estat aplicat era correcte.

**CONCLUSIÓ — confiança molt alta**

El controlador no podia distingir entre «ordre enviada» i «càmera
configurada». Aquest és el motiu que converteix una errada transitòria en una
seqüència llarga incorrecta.

## 5. A7S: cost de la descàrrega i C3 perdut

**FETS**

- Cada captura fa `--capture-image-and-download` i després `sleep 0.8`
  (`A7SFinal.sh:3-7`).
- Les funcions de C2/C3 afegeixen `sleep 1` (`:61, 70, 122, 131`).
- Els 58 RAW crítics sumen 726.493.184 bytes, uns 693 MiB.
- La cadència mediana és 6 s; de la primera presa de totalitat a l'última
  abans de C3 són 45 RAW en 261 s.
- El guió ordena `1/8000` per al C3 fins a C3+5 (`:115-124`).
- El RAW de C3+4 continua a `1/20`; no existeix cap `1/8000` a C3.
- A C3+11 i C3+14 apareixen dues `1/400`, la branca posterior
  (`:126-133`).

**RECONSTRUCCIÓ — confiança molt alta**

La funció de totalitat estava executant una cadena bloquejant i va arribar a
C3 amb molt poc marge. A C3+4 encara va entrar una vegada a la branca curta i
va ordenar `1/8000`, però el canvi no es va aplicar: el RAW va quedar a
`1/20`. La captura, descàrrega i espera van consumir la resta de la finestra
C3+5; en la iteració següent el programa ja va entrar a la branca `1/400`.
No hi havia preempció per deadline: el temps només es tornava a mirar després
de grups de captures i descàrregues.

**CONCLUSIÓ**

Descarregar cada RAW dins C2–C3 no només va reduir el volum de captures; va
deixar una sola oportunitat curta a C3. La pèrdua efectiva de `1/8000` és la
combinació de **configuració no aplicada** i **cadència bloquejant**.

## 6. A7III: què sabem del buit de 125 s

### 6.1 Fets incontestables

- La numeració `DSC06585`–`DSC06640` és contínua; no falten números.
- `DSC06613` és 0,8 s a 19:09:05; el següent RAW és a 19:09:35:
  **30 s**.
- `DSC06631` és 2 s, ISO 200, a 19:10:21.
- `DSC06632` és 0,8 s, ISO 100, a 19:12:26:
  **125 s**.
- La parella de 0,8 s és el pas que el guió fa immediatament després de la
  parella de 2 s (`A7IIIFINAL-backup.sh:89-97`).
- No es va crear cap RAW durant el buit de 125 s.
- Els 56 ARW sumen 2.741.542.912 bytes, uns 2,55 GiB; cada fitxer fa uns
  46,7 MiB.
- Els primers 29 RAW, abans del buit de 30 s, generen aproximadament
  1,36 GiB en 71 s. Els 18 següents, abans del buit de 125 s, generen uns
  841 MiB en 46 s.

### 6.2 Hipòtesis que encaixen

| Hipòtesi | A favor | En contra o dada absent | Confiança causal |
|---|---|---|---|
| Sessió PTP/USB bloquejada | log previ amb 50,6 s de timeouts; procés nou per ordre; buit dins una escala | no hi ha log del 8 d'abril | mitjana-alta |
| `wait-event=CAPTURECOMPLETE` no retorna | espera sense deadline; següent pas reprèn exactament on tocava | no hi ha stderr ni traça de l'esdeveniment | mitjana-alta |
| Búfer ple o targeta lenta | producció sostinguda de RAW grans; pauses després de blocs llargs; `capturetarget=card+sdram` apareix en un perfil antic | no coneixem targetes, slot, mode redundant, velocitat real ni indicador de búfer | mitjana |
| Interferència d'un altre procés o acció manual | l'ISO canvia 200→100 sense ordre ISO dins l'escala | no sabem quins processos compartien cos/host | mitjana |
| Fitxers perduts en copiar | cap | numeració contínua i hashes únics | molt baixa |

### 6.3 Conclusió causal prudent

**INFERÈNCIA**

El buit de 125 s s'explica millor com una operació bloquejant no limitada
—PTP, espera d'esdeveniment, càmera ocupada o drenatge de búfer— dins una
funció que no podia preemptar-se. El canvi simultani d'ISO indica, a més, que
l'estat de càmera va canviar fora del flux HDR aparent.

No hi ha base per escriure «gphoto2 va ser l'únic culpable», però tampoc per
escriure «va ser només la targeta». L'error de disseny provat és que qualsevol
d'aquests incidents podia congelar el calendari complet durant minuts.

## 7. Per què el calendari no podia protegir els contactes

**FETS**

- El control temporal usa segons de rellotge civil amb `date +%s`, no un
  rellotge monotònic.
- Les funcions HDR són bloquejants.
- A l'A7III, els primers dos parells es disparen abans de comprovar la
  finestra (`A7IIIFINAL-backup.sh:56-65`).
- Les comprovacions següents només arriben després de grups de dos o tres
  parells (`:67-97`).
- A l'A7S passa el mateix, agreujat per la descàrrega.
- No hi ha cancel·lació d'una ordre tardana ni reserva dura de temps per
  Baily/diamond ring.
- Els rellotges de les tres càmeres no eren comparables: A7S amb EXIF 2014,
  A7III amb offset `+01:00` i Canon amb una altra hora.

**CONCLUSIÓ — confiança molt alta**

Els `if` per C2/C3 només protegien el moment d'entrada a una funció. Un cop a
dins, una crida lenta podia travessar el contacte sense que el procés principal
recuperés el control. El calendari era una seqüència de comprovacions, no un
scheduler amb deadlines.

## 8. Taula causal prioritzada

| Prioritat | Mecanisme | Estat epistemològic | Símptoma 2024 | Confiança | Mesura obligatòria 2026 |
|---:|---|---|---|---|---|
| 1 | `set-config` sense identitat i sense readback | fet estructural; causalitat condicionada a la topologia | blocs A7S incompatibles; 77,8% de slots divergents | molt alta en vulnerabilitat; alta/mitjana en causa | cos lligat a serial+port; `set → get → compare`; no disparar si divergeix |
| 2 | valor A7S `1/2` absent del menú | fet | slot de 0,5 s no validat ni observat | molt alta | construir perfil només amb valors llegits de la càmera i validar-lo offline |
| 3 | procés/sessió PTP nou per cada acció | fet | latència, timeouts i possibles competències | alta | un únic propietari persistent del cos durant tota la seqüència |
| 4 | espera sense deadline ni watchdog | fet | buits A7III de 30 i 125 s; C3 no preemptible | alta com a vulnerabilitat; mitjana-alta en causa concreta | deadline monotònic per acció; cancel·lació i degradació segura |
| 5 | descàrrega RAW síncrona A7S | fet causal | mediana 6 s i només una oportunitat curta a C3 | molt alta | cap descàrrega C2–C3; gravar a targeta/búfer i drenar després |
| 6 | búfer/targeta A7III | inferència no resolta | pauses després de blocs de RAW grans | mitjana | assaig amb les mateixes targetes/slots/mode; telemetria de busy i temps de commit |
| 7 | estat extern o segon procés | inferència sustentada pel canvi d'ISO | ISO 200→100 dins el buit | mitjana | lock exclusiu, tancar apps, registrar processos i readback ISO per cada fase |
| 8 | font executable no preservada | fet | no es pot reproduir exactament A7III/Canon | molt alta | manifest immutable amb hash de script, perfil, gphoto, firmware i contactes |
| 9 | rellotges incoherents | fet | alineació entre cossos impossible | molt alta | UTC sincronitzat per a auditoria; monotònic per governar la captura |

## 9. Què no hem de concloure

1. **No:** «l'A7S va seguir l'escala però era lenta».
   **Sí:** era lenta i, a més, l'estat de velocitat va divergir massivament.
2. **No:** «el valor de mig segon era correcte perquè fotogràficament
   equival a `5/10`».
   **Sí:** la càmera exposava el literal `5/10`; el guió enviava un literal
   absent, `1/2`.
3. **No:** «el buit de 125 s prova que el búfer estava ple».
   **Sí:** el búfer és plausible, però el log PTP, l'espera sense límit i el
   canvi d'ISO impedeixen atribució única.
4. **No:** «el fitxer `A7IIIFINAL.sh` conservat és exactament el que es va
   executar».
   **Sí:** els RAW identifiquen una altra família d'escala; falta la còpia
   executable exacta.
5. **No:** «la Canon demostra que gphoto2 sempre funcionava».
   **Sí:** la Canon demostra que una escala densa i regular era possible,
   però el mecanisme exacte de la seva captura no està identificat.

## 10. Requisits derivats per a qualsevol primera versió de 2026

Aquest informe no implementa el controlador. Fixa, però, criteris de
pass/fail que s'han de satisfer abans d'utilitzar-lo:

1. **Identitat:** cada procés ha de verificar model, serial i port abans
   d'escriure o disparar.
2. **Exclusivitat:** una sola sessió/propietari per càmera; cap app o segon
   script amb accés concurrent.
3. **Perfil validat:** totes les velocitats i ISO del pla han d'existir
   literalment al menú llegit del cos connectat.
4. **Readback:** tota transició crítica ha de quedar confirmada abans del
   dispar; la divergència ha de generar error visible i una política de
   degradació.
5. **Deadline:** cap ordre pot menjar-se la reserva de C2/C3; una escala
   tardana s'abandona.
6. **Sense descàrrega crítica:** C2–C3 es dispara a targeta/búfer. La
   transferència va després.
7. **Telemetria offline:** log local JSONL o CSV amb temps monotònic i UTC,
   ordre, valor demanat, valor llegit, ACK/error, latència i número de
   captura.
8. **Manifest:** hash del programa, perfil, contactes, versions de gphoto2,
   firmware, targetes, slots i mode de gravació.
9. **Postflight automàtic:** comparar pla versus RAW/EXIF, inclòs recompte,
   cadència, ISO, velocitat i buits.
10. **Assaig de saturació:** reproduir una totalitat completa amb les SD
    definitives i després forçar cable desconnectat, càmera busy, targeta
    lenta, configuració refusada i esdeveniment absent.

## 11. Dades que encara poden tancar la causalitat

Cal documentar de memòria o reconstruir amb material del viatge:

- quina màquina controlava cada cos;
- si A7III i Canon compartien Mac;
- quines targetes hi havia a cada slot de l'A7III;
- si es gravava en un sol slot, simultani o relay;
- si algun altre programa Sony, gphoto2 o script estava obert;
- si hi va haver intervenció manual durant els buits;
- si existeix en un altre directori, terminal history o backup la versió
  A7III del 8 d'abril i el controlador real de la Canon;
- quin indicador de càmera es va observar durant el buit de 125 s: LED
  d'escriptura, pantalla busy, USB o cap resposta.

Aquestes respostes poden discriminar «host/port», «PTP» i «targeta/búfer».
No alteren la conclusió d'enginyeria: el controlador de 2024 no verificava
l'estat real ni contenia el cost temporal d'una fallada.

## 12. Empremtes dels fitxers clau

| Fitxer | SHA-256 |
|---|---|
| `FINAL/A7SFinal.sh` | `5f856efcc441cb2ee1bb24a7be5e31a186eeffe18b3404a6682ae77906949c82` |
| `FINAL/A7IIIFINAL.sh` | `41a0d86849e47e484cfa63ff0ddf9f2b8f562ae44b62d5c4b4d6d35d3f198e88` |
| `FINAL/OLD/A7IIIFINAL-backup.sh` | `c42dabaad285efc3c2adf3e11ee1cf62ee7a0da898ce1ebdcb7994387210ec52` |

## Conclusió operativa

La lliçó central de 2024 no és simplement «fer gphoto2 més ràpid». És
**substituir ordres optimistes per una captura governada per identitat,
confirmació i deadline**.

L'A7S prova que una càmera pot continuar produint RAW mentre obeeix malament
el pla d'exposició. L'A7III prova que una sola operació no limitada pot
eliminar gairebé mitja totalitat. Per al 2026, l'ús intel·ligent del búfer és
important, però només és segur si queda dins una arquitectura que sap quin
cos controla, quin estat té i quant temps resta abans del contacte següent.
