# 55 — El menú d'obturació de la R6 es col·lapsa i no torna

6 d'agost de 2026. Forense sobre evidència ja gravada: zero PTP, zero
gphoto2, zero càmera. Tot surt de dos runs físics que ja eren al disc.

## 1. La troballa, en una línia

Enmig d'una ràfega densa, la R6 III deixa de publicar el menú d'obturació:
passa de **58 opcions a dues** i **ja no torna en tota la sessió**. A partir
d'aquell moment cap canvi de base és possible, i el cos dispara la resta del
programa amb l'última base adoptada.

## 2. Les dues fonts

| Run | Bateria | Perfil |
|---|---:|---|
| `20260806T184228` (missió de Pere, canal r6m3) | 100 % | candidat R6 v1, nucli dens |
| `20260806T033433` (gate del matí) | 15 % | el mateix |

Els transcripts de gphoto2 conserven cada lectura de
`/main/capturesettings/shutterspeed` amb la llista sencera d'opcions. N'hi ha
prou de comptar-les.

### Run de missió `20260806T184228`

| Lectura | Current | Opcions |
|---:|---|---:|
| 1–9 | 1/320 → 1/40 | **58** |
| 10 | 1/40 | **2** — `Unknown value 1000`, `1/40` |
| 11 | 1/40 | 2 |
| 12 | 1/40 | 2 |
| 13 | 1/40 | 2 |

La lectura 9 és el readback que confirma la base 1/40, amb el menú sencer. La
10 és la lectura prèvia del canvi de base a 1/20, 16 s més tard, ja
col·lapsada. Les 11 i 12 són els altres dos canvis de base que van fallar; la
13 és la restauració final.

### Gate del matí `20260806T033433`

Mateixa forma, un esglaó més tard: lectures 1–11 amb 58 opcions —el canvi a
1/20 encara va adoptar— i la 12 amb dues, `Unknown value 0d00` i `1/20`.

## 2 bis. El segon run ho converteix en determinista

El run `20260806T204045`, ja amb la 0.8.3 i la instrumentació nova, repeteix
el fenomen **pulsació per pulsació**:

| Canvi de base | `20260806T184228` | `20260806T204045` |
|---|---|---|
| → 1/160 | OK a la pulsació 24 | OK a la pulsació 24 |
| → 1/80 | OK a la 43 | OK a la 43 |
| → 1/40 | OK a la 63 | OK a la 63 |
| → 1/20 | **falla a la 82** | **falla a la 82** |
| → 1/10 | falla a la 100 | falla a la 100 |
| → 1/320 | falla a la 112 | falla a la 112 |

Mateix sentinella `Unknown value 1000`, mateix menú de dues opcions, mateixa
restauració fallida. El cos va arrencar a 1/320 verificat, o sigui que el
cicle d'alimentació es va fer bé.

Això **descarta l'atzar**. Una corrupció esporàdica de transport no cau dues
vegades a la mateixa pulsació. El col·lapse és funció d'alguna cosa que
s'acumula —pulsacions, CR3 escrits, ocupació del buffer— i que en aquest
perfil se satura entre la pulsació 63 i la 82, o sigui **entre 189 i 246 CR3**.

Conseqüència pràctica immediata: hi ha una finestra fiable. **Qualsevol canvi
de base ha d'estar fet abans de la pulsació 63.** Després, no n'hi ha cap que
funcioni.

La rellegida acotada de sis segons que porta la 0.8.3 tampoc no el va
recuperar, tal com estava previst: `restore_choice_menu_unavailable`.

## 3. El que això descarta

**No és la bateria.** El col·lapse passa igual al 100 % que al 15 %. La
correlació que insinuava el docstring de `is_unavailable_choice_rejection`
era casual.

**No és un transitori de buffer.** Entre el primer col·lapse (t=189,9 s) i la
restauració (t=285,5 s) hi ha **96 segons**, dels quals els últims **15,8 s
sense cap captura**, amb el drenatge protegit ja complert i el release fet.
El menú continuava amb dues opcions. Cap espera raonable l'hauria recuperat.

**No és el valor demanat.** El matí va adoptar 1/20 sense problema i el
vespre no. No hi ha cap obturació prohibida.

**No és el nombre de pulsacions.** El vespre va col·lapsar cap a la pulsació
246; el matí, cap a la 51. El de menys pulsacions va aguantar més esglaons.

**No és la transició de 2,00 s.** Els tres setters van fallar a `index_for`,
abans de compondre cap ordre: pel bus no hi va passar res. Allargar la
transició no repobla una llista que va estar morta 96 s. La hipòtesi 2 del
traspàs queda descartada **com a causa del refús**; continua viva, en una
altra forma, a l'apartat 5.

## 4. Què diu la forma del menú col·lapsat

El menú sa acaba amb `Unknown value 00a5`, `1/16000`: gphoto2 imprimeix els
codis desconeguts com a `%04x` i el byte real hi és a la part baixa.

El menú col·lapsat porta `Unknown value 1000` i `Unknown value 0d00`: el byte
és a la part **alta**. Són `0x10` i `0x0d` amb els bytes girats.

I `0x10 − 0x0d = 3`, exactament els tres terços de punt que separen l'1/40 del
run de missió de l'1/20 del gate. O sigui que el sentinella no és soroll: és
un codi d'obturació que segueix el valor actual, llegit amb l'amplada o
l'ordre de bytes equivocats.

Això apunta a una **enumeració mal parsejada al costat de l'amfitrió**, no a
una política del cos. El controlador Canon de libgphoto2 serveix el menú des
d'una còpia que actualitza amb els esdeveniments de propietat que el cos
empeny; si un d'aquests esdeveniments arriba truncat enmig del trànsit d'una
ràfega, la còpia queda degenerada i no la refresca ningú mentre la sessió
visqui. Encaixa amb les tres observacions: apareix sota càrrega, sobreviu al
final de les captures i conserva el valor actual com a única entrada vàlida.

**No està demostrat.** És la hipòtesi que millor explica les dades, i té una
prova discriminant barata: provocar el col·lapse, tancar el shell de gphoto2,
obrir-ne un de nou contra el mateix cos i tornar a llegir el menú. Si torna
sencer sense tocar la càmera, la còpia de l'amfitrió n'és la responsable.

## 5. Què costa, fotogràficament

Al run de missió el col·lapse va arribar al grup 83 de 128. Des d'allà fins
al final —**46 grups, 138 CR3**— tot es va disparar a base 1/40 en comptes de
la rampa prevista:

| Acció | Base prevista | Base real |
|---|---|---|
| `r6m3_set_base_1_20_before_group_83` | 1/20 | 1/40 |
| `r6m3_set_base_1_10_before_group_101` | 1/10 | 1/40 |
| `r6m3_set_base_1_320_before_group_113` | 1/320 | 1/40 |

Es perd la meitat lenta de l'escala HDR —la corona externa— i, pitjor, el
retorn a 1/320 abans de C3: **l'anell de diamant i les perles de Baily de C3
i tota la parcial posterior van quedar 3 punts sobreexposats**. La
restauració final falla pel mateix motiu i el cos es queda a 1/40.

I encara hi ha un límit més gros, que el col·lapse només agreuja: amb la base
a 1/40 el fotograma més lent de cada tríada és **1/5 s**. Encara que tot
hagués adoptat, el programa dens sencer topa a **0,8 s** (base 1/10 → 1/10,
1/80, 0,8 s). O sigui que **tal com està, la R6 no pot arribar mai a
l'earthshine**, que a l'A7RIIIA són 8,00 s verificats a l'EXIF del mateix run.
Això no és culpa del menú: és el sostre del bràqueting d'aquest cos, i es
tracta a l'apartat 5 bis.

Mission First es va comportar com toca —cap pulsació sacrificada, cap replay,
el canal viu fins al final— però l'efecte fotogràfic és gros i el
comportament correcte no el compensa.

## 5 bis. Earthshine a la R6: per què ara és impossible

Requisit de Pere: com a mínim un parell d'exposicions capaces d'enregistrar
earthshine amb la R6 III + VSD90SS. A l'A7RIIIA ja hi són —dos fotogrames de
**8,000 s** verificats a l'EXIF del run `20260806T204045`— i a la R6 no n'hi
ha cap ni n'hi pot haver.

El motiu no és el col·lapse del menú, és el sostre del bràqueting del cos.
Llegit del menú viu al mateix run:

- `Auto Exposure Bracketing`: `off`, `+/- 1/3` … **`+/- 3`**. Deu opcions, i
  la més ampla és ±3 EV.
- `Bracket Mode`: **una sola opció**, `AE bracket`. No hi ha comptador de
  fotogrames: la tríada són tres i prou.

L'A7RIIIA arriba als 8 s perquè fa `Bracketing C 3.0 Steps 5 Pictures`: cinc
fotogrames a 3 EV de pas donen ±6 EV al voltant de la base, i per això la base
1/8 escup 1/500, 1/60, 1/8, 1 s i 8 s. La R6 només abasta ±3 EV.

Per tant, a la R6 **l'única manera d'arribar als 8 s és posar-hi la base**:

| Base | Tríada AEB3 ±3 EV |
|---|---|
| 1/10 | 1/80, 1/10, 0,8 s |
| 1/40 | 1/320, 1/40, 0,2 s |
| **1"** | **1/8 s, 1 s, 8 s** |

El menú sa conté `1` (comprovat: 58 opcions, de 30 s a 1/16000). O sigui que
una àncora d'earthshine a la R6 és **un canvi de base a 1" més un grup AEB3**,
i costa 1/8 + 1 + 8 ≈ **9,2 s d'obturació** per àncora. Dues àncores són uns
20 s dels 98,8 s de totalitat: comparable als 19 fotogrames que ja paga
l'A7RIIIA per les seves.

**Restricció dura de col·locació**: tant el canvi a 1" com el retorn a una
base ràpida han d'estar fets **abans de la pulsació 63**. Si el retorn cau
dins la zona morta, la resta de la totalitat es dispararia a base 1", que és
molt pitjor que quedar-se a 1/40.

### La reducció de soroll d'exposició llarga: resolta, i no és bona notícia

Pere ha confirmat que **estava activada**. Amb això, cada fotograma de 8 s en
porta un de fosc de 8 s al darrere i el grup passa de 9,2 s a uns 17.

**No es pot desactivar per programari.** Comprovat per les dues vies:

- **libgphoto2**: el llistat complet de capacitats del cos
  (`controller/runs/20260803T161512_lab_r6m3_readonly_capabilities/`) publica
  **82 paths** i cap és la NR d'exposició llarga. L'únic path de soroll és
  `/main/capturesettings/highisonr`, que és la NR d'ISO alt i ja es corregeix
  automàticament. `/main/settings/customfuncex`, que en cossos Canon antics
  portava les funcions personalitzades, retorna literalment `bad length`:
  libgphoto2 no sap parsejar el blob d'aquest cos.
- **Canon EDSDK v13.20.21**, la documentació oficial: de 841 mencions de
  `kEdsPropID_`, l'única de soroll és `kEdsPropID_NoiseReduction` (0x00000411),
  i la seva pàgina diu «Target object: **EdsImageRef**, Access type: **Read**».
  És metadada d'una imatge capturada, no un ajust de càmera. No hi ha cap
  propietat de funcions personalitzades a l'API documentada.

O sigui que **és una acció d'operador al menú del cos, i prou**. Ja és al
`manual_preflight` del perfil de missió com a punt fix d'engegada. L'EDSDK no
ho resol i no val la pena obrir-hi cap branca per això.

El que sí que podem fer és **verificar-ho per temps**: si el grup dura ~9,1 s
la NR és fora, i si dura ~17 s hi és. El worker limita el `watchdog_s` a 15 s
dur, cosa que converteix aquest límit en el discriminador: amb la NR fora el
grup passa còmodament, i amb la NR posada el watchdog salta.

### Les dues incògnites que queden

1. **Una tríada amb un membre de 8 s, acaba en `Continuous high speed`?** El
   `hold_s`, el `watchdog_s` i el `worst_case_s` del worker estan dimensionats
   per a grups de 0,6 s.
2. **El col·lapse depèn de les pulsacions o del temps?** Decideix si inserir
   un bloc de ~10 s desplaça la pulsació 82 o no, i per tant on pot viure
   l'àncora.

Totes dues es responen al banc, amb la R6 sola i sense geometria d'eclipsi.
El manual és a `56_PROVA_REOBERTURA_SESSIO_R6_2026-08-06.md`, apartat 9.

## 6. El que s'ha canviat al codi (ja fet)

Res que canviï el comportament de captura. Només qui diu la veritat i com:

1. **`UnavailableChoiceError`**, excepció dedicada que porta el `path`, el
   valor demanat, el `current` i **el menú observat**. El text del missatge no
   canvia, o sigui que els consumidors que el llegien com a cadena continuen
   igual.
2. **`config_choice_menu_unavailable`**, esdeveniment nou al ledger amb el
   recompte i la llista sencera d'opcions en el moment del refús. El forense
   de la sessió següent ja no dependrà de conservar el transcript de gphoto2.
3. **El motiu es diu pel seu nom.** Aquests refusos es registraven com
   `clean_busy_was_not_set` sense que hi hagués cap Busy, i això va desviar la
   diagnosi del traspàs. Ara hi ha `unavailable_choice_menu`, amb
   `observed_choices`. El tractament és idèntic: continua el canal, conserva
   l'última base, zero replay.
4. **La restauració rellegeix abans de rendir-se.** Finestra de 6 s només de
   lectura, i un sol write si el valor reapareix. En aquest run no hauria
   servit de res —el menú va estar mort 96 s— i hi és per al cas transitori.
   Quan no serveix, el resultat porta `reason: unavailable_choice_menu` i el
   menú observat en comptes d'un `repr` d'excepció.
5. La QA física compta els dos motius per separat i cap dels dos deixa passar
   un gate dinàmic verd.
6. **El cost fotogràfic es diu en una frase.** Cada captura afectada generava
   el seu avís: 46 línies idèntiques que no sumen res. Ara el resultat porta
   també un advisory de tancament —«46 captures (138 fotogrames) s'han
   disparat amb la base 1/40, que no era la prevista…»—, agregat per base i
   per fase. És informació, mai un `WARNING` operatiu. **De moment només és
   a `result.json`**: la GUI no llegeix `mission_advisories`, i portar-l'hi
   és una decisió sobre quant text ha de dur el panell durant una missió,
   no una conseqüència d'aquesta feina.

## 7. El que falta, per ordre

1. **Prova de reobertura de sessió.** Provocar el col·lapse amb un gate de
   cadència, i llegir el menú abans i després de tancar i reobrir el shell de
   gphoto2. Discrimina amfitrió contra cos amb una sola execució. El manual
   de tres passos és a
   `56_PROVA_REOBERTURA_SESSIO_R6_2026-08-06.md`; el preflight read-only ja
   registra `choice_count` a cada observació, que és el número que decideix.
2. **Trobar el llindar.** Amb la lectura del menú ara al ledger, cada gate de
   cadència mesura de franc quan es col·lapsa. Cal saber si depèn de la
   cadència, de la durada de la ràfega o del volum escrit.
3. **Decidir la mitigació.** Si és de l'amfitrió i una reobertura el cura, la
   política ha de dir quan es pot pagar una reconnexió: mai enmig de la
   totalitat, potser sí a la transició llarga abans del retorn a 1/320.
   Qualsevol reconnexió continua essent només per a accions futures.
4. **Contingència fotogràfica.** Mentre no hi hagi mitigació, val la pena
   preguntar-se si l'ordre de les bases hauria de posar el retorn a 1/320
   fora de l'abast del col·lapse, o si el nucli dens ha de fer menys canvis
   de base.

Cap d'aquests passos toca el contracte: el col·lapse no fa desconegut cap
estat físic, no atura cap canal i no autoritza cap replay.

## 8. Com reproduir la lectura

Els dos transcripts són a:

```text
~/Library/Application Support/Eclipse Command/state/runs/
  20260806T184228_multi_camera_mission_run/channels/r6m3/controller/
  20260806T184231_candidate_r6m3_vsd90ss_cfexpress_cardonly_v1_run/
  gphoto_transcript.log

controller/runs/20260806T033433_candidate_r6m3_vsd90ss_cfexpress_cardonly_v1_run/
  gphoto_transcript.log
```

Comptar les opcions de cada bloc `Label: Shutter Speed` fins al `END`
següent és tota la mesura.
