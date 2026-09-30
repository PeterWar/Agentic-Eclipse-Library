# 59 — El programa d'una foto per exposició, portat a l'EDSDK

7 d'agost de 2026. Encàrrec de Pere: migrar el programa de la R6 III a l'SDK
de Canon en la seva totalitat, repetir la prova i comparar, mantenint
l'obturador **electrònic en tot moment**.

**Estat: portat, compilat i encaixat de punta a punta. La mesura física està
bloquejada per la bateria del cos, que es va acabar a les 02:42.** Aquest
document deixa el port llest i el runbook a una sola ordre.

## 1. Què s'ha portat

L'ajudant privat `controller/private_edsdk/r6m3_single_hdr.mm` executa el
mateix programa que ja vola per gphoto2: una foto per exposició, cap ràfega,
un setter d'obturació abans de cada canvi.

Modes, del més barat al més compromès:

| Mode | Què fa | Toca el cos |
|---|---|---|
| `--plan-only` | resol cada etiqueta a un codi Tv de Canon i imprimeix la timeline | **no**, ni tan sols obre l'SDK |
| `--read` | identitat, tipus d'obturador, codis Tv que el cos publica, drive, bràqueting, dispars disponibles | només lectura |
| `--ladder V,V,...` | recorre unes obturacions mesurant cada set i cada pulsació | sí |
| `--program FITXER` | executa la timeline compilada sencera | sí |

La timeline la genera `controller/tools/compile_r6m3_single_hdr_edsdk_program.py`,
que **no s'inventa cap geometria**: crida el mateix `build_timeline` que
compila la sonda de gphoto2 i llegeix els valors per defecte del worker. Amb
98,8 s de totalitat emet exactament els **92 fotogrames i 53 canvis
d'exposició** del programa de missió. Una prova ho fixa
(`test_compile_r6m3_single_hdr_edsdk_program.py`): si algú canvia la
geometria de missió i no aquesta eina, la prova ho diu.

## 2. Les tres coses que aquest port fa diferent

### 2.1 L'obturació es mou per codi Tv, no per etiqueta

gphoto2 escriu `shutterspeed=1/2000` per valor i el cos triga **415–453 ms**.
L'EDSDK escriu `kEdsPropID_Tv` (0x00000406) amb un codi d'un byte. La taula de
codis surt de l'exemple oficial de Canon, `Sample/Objective-C/CameraControl/
view/TVPopUp.m`, no de memòria: 1/2000 = 0x90, 1/320 = 0x7B, 8 s = 0x20.

I no s'hi confia a cegues: després d'obrir sessió es llegeix
`EdsGetPropertyDesc(kEdsPropID_Tv)`, que diu **quins codis accepta el cos ara
mateix**, i el programa es refusa sencer si li'n falta cap. És l'equivalent
per SDK del gate de menú sa que la banda de gphoto ja té.

### 2.2 L'obturador electrònic és un gate, no una preferència

Es llegeix `kEdsPropID_ShutterType`, s'escriu si no és electrònic, es verifica
el readback, i **no es dispara ni un fotograma si no ho és**. Es torna a
verificar al final. Aquesta propietat és l'única cosa que l'SDK sap fer i
gphoto2 no: dels 82 paths que libgphoto2 publica en aquest cos, cap és el
tipus d'obturador.

### 2.3 Un `DEVICE_BUSY` a la pulsació es reintenta; una pulsació acceptada, mai

L'exemple de Canon tracta `EDS_ERR_DEVICE_BUSY` com a reintentable, i té raó:
una pulsació rebutjada **no ha fet cap fotograma**, o sigui que tornar-la a
enviar és un reintent i no un replay. Una pulsació acceptada no es repeteix
mai, digui el que digui l'alliberament. Els dos casos es compten per separat i
surten al resultat.

## 3. El que la mesura ha de respondre, i no és el que semblava

Abans de tocar el cos val la pena saber què compraria cada millora. Amb la
geometria real i 98,8 s de totalitat:

| Setter | Interval de fotograma | Fotogrames | Dins totalitat | Earthshine | vs gphoto |
|---:|---:|---:|---:|---:|---:|
| **0,62 s** | **0,50 s** | **92** | **74** | **2** | — |
| 0,40 s | 0,50 s | 94 | 76 | 3 | +2 % |
| 0,25 s | 0,50 s | 106 | 88 | 3 | +15 % |
| 0,15 s | 0,50 s | 112 | 94 | 3 | +22 % |
| 0,15 s | 0,40 s | 132 | 109 | 3 | **+43 %** |
| 0,10 s | 0,35 s | 135 | 109 | 4 | +47 % |
| 0,05 s | 0,30 s | 163 | 132 | 4 | +77 % |

**La conclusió és incòmoda i important: fer el setter quatre vegades més
ràpid només compra un +22 %.** A partir d'aquí mana el terra de 0,50 s entre
fotogrames. El salt de debò (+43 %) demana que **també** baixi l'interval
entre pulsacions, de 0,50 a 0,40 s.

O sigui que l'SDK no guanya per escriure l'obturació més de pressa. Guanya
només si **també** aguanta pulsar més sovint. Amb gphoto2 el sostre és 0,55 s
entre pulsacions i el limita el transport PTP, no el cos; si el camí de
pulsació de l'SDK és més lleuger, aquell sostre es pot moure. Si no es mou, el
port no val la pena i la resposta és quedar-nos amb gphoto2.

Això canvia l'ordre de la prova física: **primer l'escala de cadència, després
el programa sencer.**

## 4. Runbook per quan la bateria estigui carregada

Precondicions: cos carregat i encès, una sola càmera al bus, cap sessió de
gphoto2 oberta, `Image Capture` tancat, i la reducció de soroll d'exposició
llarga **desactivada** al menú del cos.

```
H=controller/private_edsdk/build/R6EDSDKSingleHDR_20260807.app/Contents/MacOS/R6EDSDKSingleHDR
```

**Pas 0, gratis i sense escriure res.** Confirma identitat, que l'obturador és
electrònic i que el cos publica tots els codis Tv que el programa necessita:

```
$H --usb-anchor 04a9:3323@01200000 --read
```

**Pas 1, l'escala de cadència.** És la que decideix si el port val la pena.
Baixa el `--gap-ms` fins que aparegui el primer `DEVICE_BUSY` o el primer
retard gros:

```
$H --usb-anchor 04a9:3323@01200000 --ladder 1/2000,1/500,1/125,1/30 \
   --frames 8 --gap-ms 500
$H ... --gap-ms 400
$H ... --gap-ms 300
```

**Pas 2, el programa sencer**, amb inventari CFexpress i menú comptats abans i
després, igual que la banda de gphoto2:

```
gui/.venv312/bin/python controller/tools/run_r6m3_single_hdr_edsdk.py \
  --helper $H --output controller/runs/edsdk_single_hdr_match_YYYYMMDD.json
```

Sense cap flag de gap reprodueix **la geometria de missió exacta**, que és el
que fa la comparació justa. Amb `--setter-gap-s` i `--frame-min-gap-s` es
compila la geometria atapeïda que el pas 1 hagi demostrat.

El runner ja s'encarrega de tres coses que altrament es mengen el matí:

- **el traspàs entre piles**. L'SDK va per l'ICA d'Apple i gphoto2 per libusb;
  després d'una sessió de gphoto2 el cos triga a reaparèixer per a l'ICA, que
  és exactament com el primer passi d'EDSDK va tornar `CAMERAS count=0`. Hi ha
  una espera explícita (`--ica-settle-s`, 20 s per defecte) i un
  `CAMERAS count=0` es reintenta en comptes de comptar com a fallada;
- **el penjat**. Després d'un error de captura la sessió EDSDK no es pot
  tancar i cal cicle d'alimentació. Tot va sota temporitzador extern i un
  timeout es reporta com a tal, amb la instrucció a la sortida;
- **la comparació**. Publica les mateixes xifres que la banda de gphoto2:
  delta CFexpress exclusiu, menú abans i després, setters verificats, retard
  màxim i costos per operació.

## 5. Criteri de decisió, escrit abans de mesurar

- **Es queda gphoto2** si l'SDK no baixa l'interval de pulsació per sota de
  0,50 s de manera sostinguda. El guany seria menor del 22 % i el preu és un
  backend privat, no empaquetable, amb un defecte de tancament de sessió
  conegut.
- **Val la pena l'SDK** si aguanta 0,40 s o menys entre pulsacions **i** el
  `close_session` tanca net en tres passades seguides amb el programa sencer.
  Llavors el guany és del +43 % o més i justifica la feina.
- **Bloquejant en tot cas**: mentre un error de captura deixi la sessió sense
  poder tancar-se, l'SDK no pot ser el camí de missió. Això no és una qüestió
  de rendiment sinó de Mission First: un canal que per recuperar-se necessita
  que algú apagui i encengui el cos no és operable el dia de l'eclipsi.

## 6. Estat físic i límits

- Cap fotograma s'ha fet per l'SDK aquesta sessió: la bateria era a l'1 % i el
  cos es va apagar. Tot el que hi ha aquí està compilat i encaixat, no mesurat.
- L'ajudant compila amb `-Wall -Wextra -Werror`. Binari
  `4aeb15fabcc8c4fcd41afb3869a1438afa90fd8786486990247c771a2a577477`,
  framework `44bcd0ece1ac0a1b92f2586f81f4c34e9952b65270b5e9d5e9563865f3643f44`.
- Dos defectes propis trobats i reparats abans de sortir:
  - llegia el descriptor de Tv acceptant fins a 256 elements quan
    `EdsPropertyDesc::propDesc` només en té 128. Ara el límit surt del
    `sizeof` de l'estructura;
  - el rellotge del programa arrencava **abans** del primer canvi
    d'exposició, o sigui que el cost sencer d'aquella escriptura queia sobre
    el primer fotograma com a retard. Amb un setter de 430 ms això hauria
    fet semblar l'SDK pitjor del que és per un artefacte de mesura, i just a
    la xifra que decideix el port. Ara el primer setter va pre-armat i el
    rellotge arrenca amb el cos ja a l'exposició d'obertura, que és el que
    diu el format del programa: els desplaçaments es compten des del primer
    **fotograma**;
  - un `DEVICE_BUSY` a l'escriptura d'obturació avortava el programa sencer.
    Una escriptura rebutjada no ha canviat res, o sigui que reintentar-la és
    un reintent i no un replay —Canon fa el mateix al seu exemple—, i avortar
    hauria cremat un cicle d'alimentació al primer intent físic, perquè
    després d'un error la sessió no es pot tancar. Ara hi ha reintent acotat i
    comptat a part;
  - el readback es feia immediatament i el cos adopta les propietats de
    manera asíncrona, o sigui que podia llegir el valor anterior i fer fallar
    una escriptura perfectament bona. Ara es sondeja fins a un termini i **el
    temps d'adopció es publica a part** (`adopt_ms`): resulta que és
    justament la xifra que cal comparar amb els 415–453 ms de libgphoto2.
- L'SDK, les seves capçaleres, el framework i l'ajudant `.mm` continuen fora
  del repositori: `controller/private_edsdk/` és a `.gitignore` i el bundle
  0.8.7 manté els seus 49 inputs sense cap material de Canon.
- Res d'això toca el programa de missió que vola. La R6 continua governada per
  gphoto2 fins que la mesura digui el contrari.
