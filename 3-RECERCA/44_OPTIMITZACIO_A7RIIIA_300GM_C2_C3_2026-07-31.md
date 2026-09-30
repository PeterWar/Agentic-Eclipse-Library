# Optimització C2-C3 — A7RIIIA + Sony FE 300 mm f/2,8 GM

Data: 31 de juliol de 2026  
Estat: **F3/F3M, SD RAW i coreografia densa 74/74 complets; Sol pendent**

## Decisió de base

Fins que hi hagi proves solars del tren real, la Canon 6D amb un 300 mm f/2,8
de Mazatlán és el prior empíric més pròxim per a l'A7RIIIA amb el Sony FE
300 mm f/2,8 GM. No és una equivalència demostrada ni autoritza copiar una
correcció EV fixa. Tota proposta ha de conservar separades:

1. la fina capa de núvols alts de Mazatlán i la meteorologia 2026 desconeguda;
2. aproximadament 2.000 m a Mazatlán i 0-1.200 m a les opcions de 2026;
3. 69 graus d'altura solar a Mazatlán i 6,8 o 12 graus el 2026.

## Evidència pròpia del cos

- F3 històric de la coreografia: 20/20, `1/1250 -> 1/30` màxim 4,181 s i
  retorn màxim 4,209 s; pressupostos recomanats 4,9 i 5,2 s, sostre candidat
  6,8 s.
- F3M directe: micro-USB i USB-C han completat 40/40 cadascun. En micro-USB,
  `Single -> 5x3` va arribar a 1,124 s i exigia 1,7 s; en USB-C ha baixat a
  0,869 s i 1,4 s. Les medianes continuen prop de 0,85 s.
- F3 Single complet: micro-USB i USB-C han completat 220/220 cadascun amb
  decisió `PASS`. En USB-C, el màxim observat ha estat 3,148 s (`2 s ->
  0,5 s`) i el màxim recomanat 4,7 s (`1/2000 -> 1/500` per variabilitat),
  per sota dels 6,8 s del candidat. La suma conservadora de les 22 arestes
  puja de 63,6 a 67,1 s; s'adopta el pitjor cas.
- El contracte centre-alternat corregit ha completat, amb la tapa posada, una
  passada verda a 100 s i 3/3 passades verdes a 97,3 s. Cada run ha executat
  36/36 accions,
  55/55 JPEG únics, ordre d'obturació i bias exactes, zero warnings,
  recuperacions o skips, cua final zero, restore i cleanup verds.
- En les quatre passades, els drenatges C2 han costat 6,587-7,253 s, els 5x3
  2,739-2,880 s i els 27 JPEG dels 9x1 16,814-17,423 s, tots dins els sostres
  propis A7RIIIA de 7,8, 4,3 i 17,8 s.
- Aquesta és una pantalla temporal de darks, no encara una qualificació amb
  contingut representatiu. Els 280 JPEG de targeta pesen només 360-426 KiB
  cadascun perquè una imatge negra és extremadament compressible. El pitjor
  drenatge de 27 JPEG ja ocupa 17,423 s dels 17,8 s disponibles: no es pot
  assumir que una corona, paisatge o soroll real mantindran el mateix temps.
- El gate `20260731T231059_lab_a7r3a_300gm_shutter_before_drain_run` ha
  demostrat que el cos accepta `1/1250 -> 1/30` amb 11/11 JPEG encara
  pendents. El setter ha costat 4,040 s, el drenatge posterior 6,142 s i el
  run ha tancat 11/11, cua zero, EXIF, restore i cleanup verds. No hi ha dues
  ordres PTP simultànies: el guany prové del processament intern del cos
  mentre la sessió executa el setter.
- Amb la tapa retirada, el run complet reordenat
  `20260731T231728_candidate_a7r3a_300gm_short_checkpointed_1x5_3x9_run`
  ha completat 36/36 accions i 55/55 JPEG a 97,3 s, sense warnings, skips ni
  recuperacions. Els JPEG científics pesen 373.608-1.089.784 bytes i la
  sonda 944.614 bytes: hi ha contingut real i una càrrega de compressió
  clarament superior als darks.
- Els drenatges sense tapa han estat 6,076 s (11), 2,623 s (5) i 15,207 s
  (27), tots dins 7,8/4,3/17,8 s. Contra el run GUI immediat anterior, el
  bloc de 27 baixa 2,263 s i el d'11 baixa 0,583 s. Els targets conservadors
  encara converteixen part d'aquest guany en espera: és marge físic provat,
  no una reducció automàtica del C2-C3 autoritzat.
- El payload RAW sense comprimir és molt menys sensible al contingut:
  85.120.000 bytes de dades de sensor tant en darks com en les mostres solars.
  Els 280 ARW dark només varien 4.096 bytes; els 94 ARW solars reals existents
  varien 208.896 bytes, aproximadament un 0,25% del fitxer. El risc pendent és
  principalment la generació/escriptura/transferència dels JPEG de checkpoint.
- PC+Camera ha lliurat en cada run una sonda JPEG 3984x2656 i cap ARW pel
  cable. El delta SD agregat dels cinc runs corregits conté exactament 560
  entrades noves, 280 ARW + 280 JPEG, i conserva 552 fitxers previs sense
  cap canvi ni eliminació. La partició per números de càmera consumeix els
  560 fitxers una sola vegada: cada bloc té una sonda i 55 captures
  científiques.
- Els 280/280 ARW són 8000x5320, 14 bits, compressió 1, amb bits baixos
  actius i ISO 400. Els 275 RAW científics concorden amb obturació i bias
  dels JPEG USB; les cinc sondes concorden amb 1/1250, bias 0. El report
  declara `scientific_raw_verified=true`, sense sobrants ni stems reclamats
  per més d'un run.
- El primer run corregit va revelar que, després del drenatge, Sony podia
  publicar breument `Single Shot` com a `Readonly: 1`. El restore ara espera
  només amb lectures, sense gastar cap write, fins que el path torna a ser
  writable. Les quatre passades verdes han restaurat amb una sola ordre i
  23 lectures estables posteriors; el bloqueig previ observat ha estat de
  2,637-240,005 ms.

### Campanya desatesa de buffer — 1 d'agost de 2026

- La coreografia densa inicial de 55 imatges ha completat 36/36 accions i
  55/55 JPEG en 80,0 s, amb drenatges de 11/5/27 en
  6,391/2,804/16,299 s, cap warning, restore i cleanup verds. El primer
  intent havia fallat abans de cap captura perquè el perfil de laboratori no
  declarava keepalive durant l'espera; el perfil final ja el conserva.
- El gate 9x1 ha completat quatre brackets a cadència de 3,0 s i hold d'1,6 s:
  36/36 imatges, ordre EXIF exacte, cua màxima observada 35 i drenatge complet
  en 22,356 s. El cinquè bracket ha rebut ACK de press/release però no ha
  generat cap de les seves nou imatges: 36/45 fitxers, `d215=0`. Això fixa
  quatre brackets/36 imatges com a límit verd i descarta 5x9 sense replay.
- El gate Single ha completat 20/20 a 1,0 s i 20/20 a 0,75 s. A 0,75 s els
  inicis reals han quedat entre 750,2 i 751,3 ms, amb cua 18 -> 0, EXIF i
  cleanup verds. A 0,50 s, les vint ordres han rebut ACK però només han
  aparegut 19 fitxers amb `d215=0`; per tant 0,75 s és el sòl físic demostrat
  i 0,50 s és un hard stop.
- La coreografia final de laboratori usa una cadència encara prudent d'1,0 s
  als contactes: 16 Single de C2, 1x5, 4x9 i 17 Single de C3. A 97,3 s ha
  completat 47/47 accions i 74/74 JPEG, sense warning, skip ni recovery. Els
  drenatges 16/5/36 han costat 9,778/2,772/22,827 s dins pressupostos
  14,0/4,3/24,0 s; cua final zero, postflight, restore i cleanup verds.
- Evidència principal:
  `controller/runs/codex_20260801_a7r3a_deep_optimization/` i, dins seu,
  `20260801T003450...dense_9x1_gate_run`,
  `20260801T005252...dense_single_gate_run` i
  `20260801T004802...dense_full_choreography_run`. Els hard stops 5x9 i
  Single 0,50 s es preserven respectivament a `20260801T003623...` i
  `20260801T005414...`.
- Aquests runs qualifiquen cadència, búfer, JPEG USB, ordre EXIF i cleanup;
  no tenen un manifest SD nou i mantenen `scientific_raw_verified=false`.
  La ruta RAW a SD i la integritat ARW continuen demostrades pels gates
  exclusius anteriors, però la coreografia de 74 necessita el seu propi delta
  SD abans de promoció.

### Integració a Eclipse Command — 1 d'agost de 2026

- El perfil de missió declara ara
  `lab_a7r3a_300gm_dense_full_choreography` com a plantilla immutable del
  core adaptatiu. Les tres llistes de packaging la inclouen i una regressió
  impedeix tornar a construir un paquet que l'ometi.
- A 97,3 s el compilador conserva exactament 74 imatges al core i no genera
  cap trigger surplus. Els cinc fotogrames addicionals que apareixen al
  recompte C1-C4 són documentació parcial fora del core físic.
- L'auditoria estricta de missió reserva el watchdog complet de 3,5 s del
  5x3: per això desplaça 0,8 s el seu drenatge i el handoff posterior respecte
  del perfil lab. És una adaptació conservadora, no un gate físic nou, i el
  candidat continua amb `timing_qualified=false`.
- En el `TEST RUN` 60/158/82 s, el programa complet materialitza 114 imatges:
  74 del core, 35 Single en el temps addicional i cinc captures parcials. Els
  Single surplus es drenen en blocs de 16; el deute estàtic màxim és 36.
- Si C3-C4 és massa curt per al drenatge qualificat de 24 s, el compilador
  reserva una plaça de cua per a C4 i difereix el drenatge complet fins al
  `drain_after`; no etiqueta falsament com a drenatge d'una imatge una cua
  heretada de C3.
- El paquet macOS s'ha reconstruït sense PTP ni càmera. El manifest incrustat
  té 33 entrades i els SHA-256 del candidat i de la plantilla densa són
  idèntics a la font viva.

| C2-C3 | Run | drain 11 | drain 5 | drain 27 | wait readonly | Resultat |
|---:|---|---:|---:|---:|---:|---|
| 100,0 s | `20260731T204540...` | 6,587 s | 2,880 s | 16,814 s | 240,005 ms | verd |
| 97,3 s | `20260731T205258...` | 7,253 s | 2,752 s | 16,847 s | 223,308 ms | verd |
| 97,3 s | `20260731T205839...` | 6,680 s | 2,739 s | 17,097 s | 219,635 ms | verd |
| 97,3 s | `20260731T210446...` | 6,805 s | 2,795 s | 17,423 s | 2,637 ms | verd |

Els quatre `result.json` són sota
`controller/runs/codex_20260731_a7r3a_optimization/`; tots declaren
`restore_ok=true`, `cleanup_ok=true`, `physical_state_unknown=false` i una
sola escriptura explícita de restore.
- El gate fix 5x3 USB-C ha completat cinc brackets a 10 s: 25/25 commits,
  cua màxima 25, 25 JPEG únics, postflight verd i cap warning. El drenatge
  de 25 a zero ha estat monòton i ha costat 16,291 s. És evidència pròpia de
  retrigger i transport JPEG; no substitueix la conciliació dels 25 ARW.
- El manifest posterior té 448 fitxers i 25.317.179.392 bytes. Contra el
  baseline hi ha 66 afegits, 0 modificats i 0 eliminats: 25 parelles del run
  `DSC01532-DSC01556` i vuit parelles anteriors `DSC01524-DSC01531`.
  Els 25 ARW correlacionats passen 8000x5320, 14 bits, compressió 1, bits
  baixos actius, ISO, obturació i bias, però l'exclusivitat del delta falla.
  Per tant `scientific_raw_verified=false` i el gate s'ha de repetir des del
  manifest nou, sense esborrar ni reetiquetar cap fitxer.
- La repetició `20260731T185122...` ha tancat aquesta incertesa: el delta
  contra aquell manifest nou conté exactament 50 entrades, 25 ARW i 25 JPEG
  `DSC01557-DSC01581`, amb 448 fitxers antics intactes, 0 modificats i 0
  eliminats. Els 25 ARW passen 8000x5320, 14 bits, compressió 1, bits baixos
  actius i concordança ISO/obturació/bias. El report final declara
  `scientific_raw_verified=true`.
- L'inspector sí que és compatible amb l'ARW d'aquest cos: una mostra física
  anterior (`20260725T233934.../capt_DSC00024.ARW`) dona model
  `ILCE-7RM3A`, IFD RAW 8000x5320, 14 bits, compressió 1, els quatre estats
  dels dos bits baixos actius i EXIF d'obturació/ISO/biaix llegible. Això
  qualifica l'inspector, no la ruta SD de la coreografia nova.

## Separació A7III / A7RIIIA

`gui/eclipse_command/adaptive_profiles.py` conserva un sol algorisme Sony per
evitar divergències, però ara rep dues envolupants independents:
`A7III_CHOREOGRAPHY` i `A7R3A_CHOREOGRAPHY`. Cap canvi de constant de l'A7III
pot alterar silenciosament l'A7RIIIA. La coincidència numèrica només es manté
quan hi ha evidència pròpia o un sostre provisional explícit.

L'envolupant no separa només els drenatges: declara també cadència parcial,
blocs JPEG, finestres/polling, offsets compactes, extensió de totalitats
llargues, handoffs C3 i floor curt. L'algorisme és compartit; l'autoritat
temporal de cada cos no ho és.

Per a la cua intermèdia de 18 JPEG no s'interpola el sostre A7III de 12,5 s:
l'A7RIIIA usa conservadorament 17,8 s fins que hi hagi mesura pròpia.

## Enllaç micro-USB mesurat

La connexió micro-USB de l'A7RIIIA negociava `High-Speed`, 480 Mb/s. Amb
USB-C directe, el mateix cos i sèrie negocien `SuperSpeed`, 5 Gb/s: 10,4
vegades més de sostre nominal. La latència PTP i l'electrònica del cos
impedeixen deduir que cada operació sigui 10,4 vegades més ràpida.

Això no limita l'escriptura RAW a SD ni el bràqueting nadiu mentre no cal
drenar telemetria. Sí que pot limitar els checkpoints JPEG. Per això no es
copiarà cap durada de l'A7III. USB-C ha eliminat la cua lenta de F3M
`Single -> 5x3`, però F3 obturació no ha millorat i presenta una suma
conservadora superior. Els futurs drenatges queden qualificats amb USB-C.

## Comparació offline

Eina reproduïble:

```bash
PYTHONDONTWRITEBYTECODE=1 gui/.venv312/bin/python \
  controller/tools/audit_a7r3a_300gm_strategies.py
```

| C2-C3 | Single | 5x3 fix | 9x1 fix | 1x5 + 3x9 |
|---:|---|---:|---:|---:|
| 88,0 s | cap escombrada / 23 imatges | 3 brackets / 38 imatges | 3 brackets / 50 imatges | no hi cap |
| 97,3 s | cap escombrada / 23 imatges | 4 brackets / 43 imatges | 3 brackets / 50 imatges | 4 brackets / 55 imatges |
| 98,8 s | cap escombrada / 23 imatges | 4 brackets / 43 imatges | 3 brackets / 50 imatges | 4 brackets / 55 imatges |
| 99,7 s | cap escombrada / 23 imatges | 4 brackets / 43 imatges | 3 brackets / 50 imatges | 4 brackets / 55 imatges |

Tots els resultats fixos són **provisionals** i tots quatre continuen
`qualification_status=blocked`:

- 5x3 té arestes directes, cinc retriggers sota càrrega USB-C i delta SD
  exclusiu amb 25 ARW íntegres; només li falta la validació solar/òptica
  comuna abans d'una promoció de camp;
- 9x1 ja té les arestes de mode directes i tres brackets en un run anterior;
  el gate específic USB-C ja ha repetit tres brackets, drenat 27 JPEG en
  16,995 s i verificat un delta exclusiu de 27 ARW+27 JPEG;
- l'híbrid és el més complet científicament i té la pantalla temporal de
  darks verda a 100 s + 3/3 a 97,3 s i els cinc blocs SD/RAW íntegres;
  ja té una passada sense tapa i amb JPEG de 0,37-1,09 MB; continua bloquejat
  per repetició, validació solar/òptica i proves de fallada abans de promoció;
- Single ja té tota la matriu F3: una escombrada i el retorn costen 80,85 s,
  i dues escombrades 94,6 s abans de reservar els contactes. No cap en cap
  totalitat candidata fins a 99,7 s i queda descartada.

El mínim aritmètic actual de l'híbrid és 97,29 s. El tier complet s'activa a
97,3 s, amb només 0,01 s de slack formal. Aquest marge ha superat una passada
de darks a 100 s i 3/3 passades de darks exactes a 97,3 s, però encara no una
una escena interior sense tapa. És una mostra verda, no encara una campanya
solar ni un 3/3 representatiu; el perfil continua candidat.

## Gates offline preparats

1. `lab_a7r3a_300gm_single_ladder_f3.json`: completat, 22 arestes
   d'obturació, anada i tornada, 220 mostres amb 10 rondes i zero captures.
2. F3M directe: completat, `Single -> 5x3 -> Single -> 9x1 -> Single`, 40
   mostres amb 10 rondes i zero captures.
3. `lab_a7r3a_300gm_fixed_5x3_retrigger.json`: cinc brackets, 25 imatges,
   cadència candidata de 10 s, manifest SD obligatori i data de producció
   explícita per bloquejar l'override el 12-08-2026.
4. `lab_a7r3a_300gm_fixed_9x1_retrigger.json`: tres brackets, 27 imatges,
   cadència candidata de 8,2 s, manifest SD obligatori i el mateix bloqueig
   de data de producció.
5. El perfil de missió conserva `timing_qualified=false` i un postflight JPEG
   estricte amb l'ordre centre-alternat físic.
6. `verify_sd_raw_campaign.py`: delta agregat dels cinc runs híbrids
   particionat exactament per stems, amb integritat RAW, ISO/EXIF i sondes
   verificats sense convertir el primer run de restore fallit en `complete`.

El gate SD ha d'usar els paràmetres propis de l'A7RIIIA, no els defaults de
l'A7III: `--width 8000 --height 5320 --bits 14 --compression 1
--require-active-low-bits`, més `--science-images 25`, `27` o `55` segons el
perfil. Només `scientific_raw_verified=true` tanca integritat, EXIF i recompte.

## Regressió offline

- Controlador: **580/580** proves correctes.
- GUI: **284/284** proves correctes.
- Fuzz adaptatiu: **67.392/67.392** cronologies compilades, validades i
  auditades sense gaps de cobertura.
- Cap d'aquestes comprovacions ha importat Qt físic, obert PTP, executat
  `gphoto2` ni contactat cap càmera.

## Estat físic actual

La inspecció viva del 31-07-2026 ha confirmat:

- A7RIIIA `ILCE-7RM3A`, sèrie USB `[SÈRIE]`; USB-C directe a
  `usb:000,001`, SuperSpeed 5 Gb/s;
- cap Adobe Bridge ni procés de projecte competint; només `ptpcamerad`, que
  el guard del controlador gestiona;
- preflight 5x3 només lectura verd: M, focus manual, RAW+JPEG Std,
  `Bracketing C 3.0 Steps 5 Pictures`, 1/30, ISO 400, `card+sdram`, bateria
  89 % i cua zero;
- preflight USB-C verd, F3M acumulat 80/80 i F3 Single acumulat 440/440,
  restauració estable i cap captura.

El tancament del 01-08-2026 ha verificat novament, només amb lectures:
`Single Shot`, 1/1250, ISO 400, RAW+JPEG Std, `card+sdram`, bateria 72 %,
`d215=0`, cap warning, cleanup verd i cap procés `gphoto2` o controlador viu.

Les eines F3/F3M han mutat només obturació/mode i els han restaurat; no s'ha
disparat cap fotografia. Pere ha confirmat al menú firmware literal `1.00`;
PTP només exposa `deviceversion=1.0`.

El primer intent d'armar el gate 5x3 va ser rebutjat pel validador abans de
lock, PTP o trigger: faltaven C2/C3 explícits i els perfils de laboratori no
declaraven `production_event_date_utc`. El defecte es va corregir als perfils
5x3 i 9x1. Amb la nova autorització de Pere, el run
`20260731T172713_lab_a7r3a_300gm_fixed_5x3_retrigger_run` ha acabat
`complete`, exit 0: cinc accions, 25 imatges compromeses, desviació d'inici
entre 0,004 i 2,659 ms, durades de 4,507-4,510 s, cua 25 -> 0, 25 JPEG
descarregats, ordre d'obturació i biaixos exactes, `cleanup_ok=true`,
`restore_ok=true` i estat físic conegut. Continua sent només qualificació i
`scientific_raw_verified=false` fins al delta de la SD.

La SD UHS-II s'ha muntat com `/Volumes/Untitled`: 239 GiB útils i 218 GiB
lliures. El manifest previ complet s'ha tancat amb 382 fitxers i
22.490.815.488 bytes: 263 ARW i 119 JPEG. Els 263 ARW existents són
8000x5320, 14 bits, compressió 1 i tenen actius els quatre estats dels dos
bits baixos. SHA-256 del manifest:
`58c2e038c16e8b50e48f4981f999d5d03b6e4a178fb3183a0f1f569cce8eda62`.
No s'ha escrit, formatat ni esborrat res de la targeta.

## Ordre físic quan desaparegui el bloqueig

1. Fet: identitat només lectura i preflight sense autofix.
2. Fet: F3M de les quatre arestes directes.
3. Fet en micro-USB i USB-C: F3M directe i F3 Single complet; Single queda
   descartat perquè ni una escombrada cap fins a 99,7 s.
4. Fet: Mass Storage, manifest SD previ, retorn a PC Remote i preflight 5x3.
5. Fet: 5x3 fix amb C2/C3 sintètics explícits, cinc retriggers i 25 JPEG;
   repetició des de baseline net i 25 ARW/25 JPEG exclusius verificats.
6. Nou manifest previ; 9x1 fix; manifest posterior i verificació de 27 ARW.
   Fet: 27/27 ARW íntegres i EXIF concordant en delta exclusiu.
7. Fet amb darks: híbrid corregit, una passada verda a 100 s, 3/3 a 97,3 s
   i delta agregat exclusiu amb 280 ARW + 280 JPEG verificats.
8. Fet una vegada sense tapa: 55/55, JPEG de 0,37-1,09 MB i drenatges dins
   pressupost. Pendent repetir i fer el gate solar/òptic abans de promoció.
9. Comparació solar filtrada amb el 300 mm real.
10. Cable-pull i bateria sobre l'estratègia escollida; mai repetir un trigger
   ambigu.
11. Només amb tots els resultats verds: promoció explícita del perfil.
