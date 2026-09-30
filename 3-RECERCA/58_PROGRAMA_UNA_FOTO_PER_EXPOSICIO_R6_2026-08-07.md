# 58 — El programa de la R6: una foto per exposició

7 d'agost de 2026. Proves físiques a la R6 III autoritzades per Pere.
Runs: `controller/runs/single_hdr_stage1_20260807.json`,
`single_hdr_full_conservative_20260807.json`,
`single_hdr_full_tight_20260807.json`.

## 1. L'encàrrec i la restricció

Pere volia la **màxima cadència en mode determinista** que cobrís perles de
Baily, anell de diamant, earthshine i una corona completa. Amb gphoto.

La restricció que ho decideix tot ja estava mesurada (`research/55`, `56`):
**les ràfegues AEB natives maten el menú d'obturació d'aquest cos.** Passa de
58 opcions a dues i no torna fins a un cicle d'alimentació. Tres sessions PTP
independents el veuen igual, o sigui que és del cos. I el llindar **no és un
comptador de pulsacions**: 82 a dues missions, 12 al banc. No es pot
pressupostar.

Un programa que no pot pressupostar quan perdrà la capacitat de canviar
d'exposició no és determinista. Aquesta és tota la justificació del canvi.

## 2. La forma nova

Una foto per exposició, cap ràfega enlloc:

| Tram | Què hi ha | Obturació |
|---|---|---|
| Parcials documentals | una imatge cada 30 s | 1/320 filtrada |
| Finestra de contacte C2 | C2−5 s a C2+5 s, cadència màxima | 1/2000 fixa |
| Mig de la totalitat | escales HDR senceres | 1/2000 → 8 s |
| Finestra de contacte C3 | C3−5 s a C3+4 s, cadència màxima | 1/2000 fixa |

Les escales són dues de 2 EV entrellaçades —A: 1/2000, 1/500, 1/125, 1/30,
1/8, 0,5; B: 1/1000, 1/250, 1/60, 1/15, 1/4, 1— i una **cua profunda** de 2 s
i 8 s que s'afegeix a les passades «deep». Cada passada sola cobreix 12 EV;
dues passades consecutives mostregen el mateix interval **cada 1 EV**, que és
més fi del que una sola passada es pot permetre a aquesta cadència.

El patró és `deep, A, B, A, deep, B` i s'omple de forma cobdiciosa: **una
escala que no hi cap sencera no s'hi posa**. Una escala truncada és un joc
d'exposicions trencat i el que sobra val més com a marge.

**La regla dura del traspàs es compleix per construcció**, no per ordenació:
si no hi ha cap ràfega, cap ràfega pot precedir un canvi d'exposició.

## 3. El que s'ha mesurat al cos

Tres runs, tots amb delta CFexpress exclusiu i el menú comptat abans i després
per un procés de gphoto2 nou.

| Run | Fotogrames | Delta CF | Setters | Retard màx. | Menú |
|---|---:|---:|---:|---:|---:|
| Etapa 1, 40 s | 24/24 | +24 | 16/16 | 0,0 ms | 58 → 58 |
| Sencer conservador, 98,8 s | 73/73 | +73 | 42/42 | 0,1 ms | 58 → 58 |
| **Sencer atapeït, 98,8 s** | **92/92** | **+92** | **54/54** | **0,0 ms** | **58 → 58** |

Cap error, cap Busy, cap quarantena, cap fotograma perdut.

Costos, molt constants sobre 54 mesures:

| Operació | Mesurat | Pressupostat |
|---|---:|---:|
| Canvi d'exposició per valor, dins la sessió del worker | **415–453 ms** | 620 ms |
| Pulsació i alliberament d'un fotograma Single | **53–61 ms** | — |
| Reserva per fotograma ràpid | — | 350 ms |
| Interval entre fotogrames ràpids | — | 500 ms |

El worker **no espera l'exposició**: la pulsació i l'alliberament costen 54 ms
tant si l'obturació és 1/2000 com si és de 8 s. Per això el cost real del
fotograma viu sencer dins la reserva de readiness, i per això la reserva ha
d'incloure l'exposició o l'ordre següent arribaria amb l'obturador obert.

Els 500 ms entre fotogrames no són un número inventat: és exactament el valor
que el gate H2 va demostrar 20/20 i que aquesta nit ha aguantat 45 pulsacions
seguides a la finestra de contacte. El setter té un 37 % de marge sobre el
pitjor cas mesurat.

## 4. L'EXIF, que és el que tanca l'argument

El ledger diu que les exposicions s'han adoptat. L'EXIF diu què va fer el cos.
Tres CR3 del run atapeït, descarregats lligats al manifest i inspeccionats:

| Fitxer | Posició | `ExposureTime` | Resta |
|---|---|---|---|
| `572A6617.CR3` | fotograma 1, contacte | **1/2000** | Electronic, AEB Off, Single, ISO 100, RAW 6960×4640 |
| `572A6645.CR3` | fotograma 29, earthshine | **8 s** | idem |
| `572A6708.CR3` | fotograma 92, contacte | **1/2000** | idem |

Cos exacte `[SÈRIE]` als tres. **L'earthshine hi és de debò**, i sense
cap truc: `shutterspeed=8` i una foto. No cal la base a 1 s ni la tríada AEB
que `research/54` havia hagut d'inventar per arribar-hi.

## 5. Què costa i què guanya

El nucli dens feia 318 CR3 dins totalitat. Aquest en fa **74**.

Però dels 318, dos terços sortien a una base equivocada des del col·lapse del
menú, i **cap arribava a l'earthshine**: l'AEB del cos topa a ±3 EV i per
tant el programa dens no passava de 0,8 s. Els 74 d'ara són tots a
l'exposició que s'ha triat, cobreixen **15 velocitats úniques de 1/2000 a
8 s** —14,3 EV— i inclouen dos fotogrames d'earthshine.

Es perd cadència als contactes: 2 fotogrames/s a exposició fixa contra els 4
CR3/s de l'AEB3. A canvi, la finestra de contacte és **fixa a 1/2000** i no
depèn de si el menú encara és viu.

## 6. Conseqüències operatives

- **El bràqueting queda apagat.** El programa el declara `off` a la
  convergència d'arrencada, i això treu de sobre l'operador la feina de
  tornar-lo a posar després de cada cicle d'alimentació, que és quan
  s'esborra.
- **Drive passa a `Single`.**
- **La reducció de soroll d'exposició llarga continua sent feina física.** Amb
  ella activada, cada fotograma de 2 s i de 8 s en porta un de fosc al
  darrere i l'escala ja no cap al seu lloc.
- El mínim de totalitat baixa a **30 s**: és on encara hi cap una escala HDR
  sencera entre les dues finestres de contacte. Per sota, el canal queda
  exclòs i cap altre cos se n'assabenta.

## 7. Escalat

| Totalitat | Fotogrames del nucli | Earthshine |
|---:|---:|---:|
| 30 s | 52 | 0 |
| 45 s | 54 | 1 |
| 60 s | 66 | 1 |
| 88 s | 80 | 2 |
| **98,8 s** | **92** | **2** |
| 110 s | 94 | 3 |
| 140 s | 118 | 3 |
| 200 s | 146 | 5 |

Escombrada completa de 30,0 a 200,0 s amb resolució de 0,1 s: cap geometria
falla.

## 8. Un defecte trobat i reparat pel camí

A certes durades el setter que obre la finestra de contacte de C3 trepitjava
la finestra de configuració de l'últim fotograma de l'escala, i l'auditoria
de cronologia del worker refusava el perfil —correctament—. La frontera on
s'encaixen les escales ara reserva un interval de setter sencer abans de
C3−5 s. A 98,8 s no canvia res: continuen sent els mateixos 92 fotogrames.

## 9. El run per l'app, que tanca la cadena

`20260807T022642`, llençat pel **binari del bundle** amb el despatx
`--eclipse-command-controller-r6m3`, amb contactes reals i C1–C4 comprimit
(totalitat 30 s):

| | |
|---|---:|
| Estat | **complete**, `card_only_schedule_and_ledger_complete` |
| Fotogrames | **54/54** |
| Delta CFexpress exclusiu | **+54**, contigu `572A6709..6762` |
| Setters verificats per readback | **14/14** |
| Retard màxim | **1,42 ms** |
| Menú d'obturació | **58 → 58** |
| Saltades, Busy, quarantenes, avisos | **cap** |

I l'EXIF prova l'ordre complet d'exposicions, que és el que el programa de
ràfegues no podia fer:

| Fitxer | Tram | `ExposureTime` |
|---|---|---|
| `572A6709.CR3` | primera parcial documental | **1/320** filtrada |
| `572A6711.CR3` | finestra de contacte | **1/2000** |
| `572A6762.CR3` | parcial documental **després** de C3 | **1/320** |

El darrer és el que importa: **el cos torna a l'obturació filtrada després de
la finestra de contacte**. Amb ràfegues el menú ja seria mort i aquella
parcial hauria sortit negra.

El gate dinàmic de `qa_physical_gui_test_run.py` dona **verd** sobre aquest
run: transport, readback de setters i ledger.

El binari era el de la 0.8.6. La 0.8.7 que hi ha instal·lada ara només
canvia una eina de QA: el controlador R6 i el perfil de missió hi tenen el
mateix SHA, o sigui que el camí de captura és byte per byte el mateix.

## 10. El que continua pendent al cos

- **Preflight i run curt fets, run llarg no.** El run per l'app va anar amb
  una totalitat de 30 s, que és el mínim del programa i no porta cap
  fotograma d'earthshine. El de 98,8 s amb els dos fotogrames de 8 s està
  demostrat per la sonda `single_hdr_full_tight_20260807`, però no encara
  des de l'app amb ancoratge de contactes. Va quedar per fer perquè la
  bateria era al 6 %.
- **Tren òptic.** Tot això s'ha mesurat amb la Sigma 35 mm f/1,4, no amb el
  VSD90SS. No qualifica focus, seguiment, camp ni ciència solar.
- **Fotometria.** L'escala cobreix 14,3 EV, però l'ancoratge absolut per al
  VSD90SS a f/5,5 no està mesurat. En particular: 8 s a f/5,5 ISO 100 és
  ~2 stops per sota de l'equivalent dels 8 s de l'A7RIIIA a f/2,8. Si Pere
  vol earthshine amb el mateix senyal, el fotograma llarg hauria d'anar cap
  a 30 s, i això costa un terç de la totalitat. La decisió és seva.
- **CR3 exclusius de missió.** Continua `card_only_committed`: falta el
  manifest exclusiu lligat a cada acció.
