# 61 — La cadència de la R6 i l'earthshine de 15 s: mesurat

7 d'agost de 2026, tarda. Set execucions contra el cos `[SÈRIE]` amb el
menú comptat abans i després per un procés de gphoto2 nou. Tot per gphoto2:
l'SDK va quedar descartat al matí (`research/60`).

## 1. Les dues coses que s'han mesurat

**El terra de pulsació val també per gphoto2.** La campanya de l'SDK havia
trobat que el cos accepta una pulsació cada 400 ms i en rebutja a 300. Amb
l'interval a 0,40 s i el setter a 0,55, el worker de gphoto2 ha completat
**94 fotogrames de 94, amb delta CFexpress exclusiu +94, 48 setters de 48 amb
readback i un retard màxim de 0,0 ms sobre 141 accions**. El menú, 58 → 58.

**Una exposició llarga deixa el cos ocupat molt més enllà del seu final.** El
setter posterior a un fotograma de 15 s:

| Espera després de tancar l'obturador | Resultat |
|---:|---|
| 0,40 s | `PTP Device Busy 0x2019` |
| 1,10 s | `PTP Device Busy 0x2019` |
| **2,10 s** | **acceptat** |
| 4,10 · 8,10 · 16,10 s | acceptats |

I no és proporcional a l'exposició: després d'un fotograma de **2 s** el
mateix setter s'accepta a **0,30 s**, i després d'un de 8 s s'acceptava a
0,35 al run de la nit. Tampoc no és la foto fosca de la reducció de soroll
d'exposició llarga: si ho fos, caldrien uns 15 s i no 2.

## 2. El programa que en surt

| | Abans (0.8.7) | Ara (0.8.8) |
|---|---:|---:|
| Interval entre fotogrames | 0,50 s | **0,40 s** |
| Reserva per canvi d'exposició | 0,62 s | **0,55 s** |
| Reserva després d'un fotograma | 0,35 s | **0,30 s** |
| Suplement dels fotogrames llargs | — | **2,20 s** |
| Earthshine | 2 × 8 s | **2 × 15 s** |
| Fotogrames del nucli a 98,8 s | 92 | **94** |
| Finestres de contacte a 1/2000 | 40 | **53** |
| Velocitats úniques | 15 | 15 |

L'earthshine de 15 s és decisió de Pere: a f/5,5 i ISO 100, els 8 s quedaven
uns dos punts per sota dels 8 s de l'A7RIIIA a f/2,8, i 15 s ho deixa a un.
Amb la cadència nova el fotograma llarg surt pagat: **94 fotogrames contra
92**, i amb tretze fotogrames més a les finestres de contacte, que és on hi
ha les perles i l'anell de diamant.

El preu és al mig de la totalitat: les escales HDR passen de 52 fotogrames a
46, i dins totalitat se'n comptabilitzen 71 en comptes de 74 perquè les
finestres de contacte creixen cap enfora de C2 i C3.

## 3. Dos defectes reparats pel camí

**El lease de l'obturador i l'espera fins a l'ordre següent no són el mateix.**
El compilador els posava tots dos al mateix número. Amb un fotograma de 15 s i
el seu suplement, la reserva superava el sostre dur del worker i el perfil
quedava refusat abans de tocar el cos —correctament, però pel motiu
equivocat—. Ara el lease cobreix només l'exposició, que és el que garanteix
que la pulsació es tanqui i l'estat físic quedi conegut, i el suplement viu
als camps de readiness. El sostre puja de 15,0 a 16,00 s, just per al
fotograma de 15 s; el següent esglaó del menú, 20 s, continua quedant fora.

**El restore de cleanup disparava massa aviat.** És l'escriptura més justa de
tot el run: arriba exactament al final de la finestra del darrer fotograma,
mentre que un setter de la timeline sempre té la seva pròpia ranura al
davant. El cos li contestava `Device Busy` a 0,31 s de la pulsació i el
resultat era un cos que es quedava amb una obturació que no era la de missió
—va passar tres vegades avui—. El cleanup no té cap termini: ara paga 0,35 s
de marge i el run de validació va tancar sol a 1/320.

## 4. La frontera de C2 i C3

Amb l'interval a 0,40 s, entre l'últim fotograma ancorat a C2 i el primer
ancorat a C3 hi han de cabre la reserva del cos, la tolerància de retard i el
jitter del planificador. Amb la tolerància a 0,10 s no hi cabien per **19 ms**
i l'auditoria del worker refusava el perfil. La tolerància passa a 0,05 s, que
és exactament la del programa que s'ha mesurat al cos: 141 accions amb un
retard màxim de 0,0 ms, o sigui trenta vegades el pitjor cas observat.

## 5. Evidència

| Run | Geometria | Resultat |
|---|---|---|
| `20260807T141930` | 0,40/0,55, cua 2,15, sense suplement | 33 fotogrames i Busy al setter posterior al de 15 s |
| `20260807T142807` | suplement 0,70 | Busy igual, a 1,10 s |
| `20260807T143112` | suplement 15,70 | 15/15 |
| `20260807T143250` | suplement 7,70 | 15/15 |
| `20260807T143406` | suplement 3,70 | 15/15 |
| `20260807T143504` | suplement 1,70 | 15/15 |
| **`20260807T143855`** | **0,40/0,55, cua 2,15, suplement 2,20** | **94/94, delta +94, 48/48 setters, 0,0 ms, menú 58 → 58** |

Els cinc del mig van amb `--skip-snapshots`: el senyal que buscaven era el
setter, no el delta. El primer i l'últim porten inventari CFexpress exclusiu.

## 6. I el run sencer per l'app, que era el deute número u

`20260807T151346`, llençat pel **binari del bundle 0.8.8** amb el botó
TEST RUN, que porta una totalitat de **98,8 s** i contactes reals a C1, C2, C3
i C4:

- **99 accions de captura de 99**, i **delta CFexpress exclusiu +99**
  (5.041 → 5.140);
- **48 setters de 48** amb readback exacte i **zero Busy**;
- retard màxim **0,40 ms** sobre 147 accions;
- menú **58 → 58**, cleanup net, restore correcte a 1/320 i estat físic
  conegut;
- **EXIF de l'earthshine**: `572A7507.CR3` dona `ExposureTime` **15 s**,
  obturador **Electronic**, AEB **Off**, Single, ISO 100, RAW, cos
  `[SÈRIE]` i contenidor íntegre.

És el primer run per l'app amb totalitat llarga: l'anterior anava amb 30 s,
el mínim del programa, i per tant sense cap fotograma d'earthshine.

Una observació que no és de captura: el gate de `qa_physical_gui_test_run.py`
declara `frozen_dispatch_ok=false` perquè compta **dos** llançaments del
mission host, i n'espera un. El segon és l'autocheck que la GUI fa sola en
detectar el cos, que també passa pel binari congelat. La missió, en canvi,
hi dona verd: `r6_dynamic_gate_ok=true` amb 99 accions planificades i 99
completades.

## 7. Límits

- continua `card_only_committed`: no hi ha manifest ni inspecció CR3 lligats a
  cada acció;
- òptica Sigma 35 mm, no el VSD90SS: no qualifica tren òptic, focus ni
  seguiment;
- l'EXIF de 15 s ja està verificat, però el manifest CR3 exclusiu lligat a
  cada acció continua pendent;
- estat en tancar: cos a **1/320, Single, AEB off**, menú **58**, bateria
  83 % abans del run de l'app, **5.140 CR3** a la CFexpress, zero esborrats,
  zero formats.
