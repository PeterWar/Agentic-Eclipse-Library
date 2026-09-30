# 60 — EDSDK contra gphoto2 a la R6 III: la mesura

7 d'agost de 2026. Dotze execucions del programa d'una foto per exposició per
l'SDK de Canon contra el cos exacte, totes amb l'obturador **electrònic**
verificat abans i després. Evidència crua a
`controller/runs/edsdk_20260807T1215/`.

## 1. La resposta curta

**L'SDK és clarament més ràpid i dona un +22 % de fotogrames. I tot i així la
recomanació és quedar-se amb gphoto2**, perquè quan falla es penja, i d'un
penjat només se surt apagant el cos.

## 2. El cara a cara, mateixa geometria de missió

Programa sencer, 98,8 s de totalitat, 92 fotogrames i 53 canvis d'exposició.

| | gphoto2 | EDSDK |
|---|---:|---:|
| Fotogrames | 92/92 | **92/92** |
| Setters verificats | 54/54 | **53/53** |
| **Cost del setter** | **415–453 ms** | **≤ 24,3 ms** |
| Pulsació + alliberament | **53–61 ms** | 111–143 ms |
| Rebuigs `DEVICE_BUSY` | — | **0** |
| Retard màxim | **0,0 ms** | 8,6 ms |
| Terra de pulsació sostingut | 500 ms | **400 ms** |

El setter de l'SDK és unes **divuit vegades** més barat: `kEdsPropID_Tv`
s'escriu amb un codi d'un byte i el cos l'adopta en microsegons. El camí de
pulsació, en canvi, és **el doble de car** que el de gphoto2; el que compensa
és que el cos accepta pulsacions més sovint, 400 ms contra 500.

## 3. El que compra, mesurat

Amb la geometria atapeïda que aquests números permeten —setter 0,15 s,
interval de fotograma 0,40 s— i la mateixa totalitat:

| | Fotogrames | Dins totalitat | Earthshine |
|---|---:|---:|---:|
| gphoto2, geometria de missió | 92 | 74 | 2 |
| **EDSDK, geometria atapeïda** | **112** | **94** | **3** |

Execució neta: 112/112, 73/73 setters, zero rebuigs, retard màxim 8,8 ms,
cleanup net i electrònic verificat al final.

## 4. Evidència de targeta

Amb el cos reiniciat i la guarda de `ptpcamerad` activa, gphoto2 torna a obrir
sessió i compta la CFexpress:

- base verificada a les 02:29: **4.331 CR3**;
- després de tota la campanya EDSDK: **4.841 CR3**;
- **delta exclusiu: +510**.

Els registres de les execucions netes en declaren **438**. Els **72** restants
són del run que es va penjar: la seva sortida estava en memòria intermèdia i
el `kill -9` se la va endur, o sigui que va disparar 72 fotogrames i només 49
van arribar al log. El total quadra.

I una dada que confirma el disseny: **els 510 fotogrames no han tocat el menú
d'obturació**, que continua publicant 58 opcions. Sense ràfegues, el col·lapse
no apareix ni per l'SDK.

## 5. On es trenca, i com

Empenyent el setter a 0,06 s amb l'interval a 0,40 —118 fotogrames— **la
sonda s'ha penjat**: zero CPU, cap sortida durant dos minuts, `kill -9` i
cicle d'alimentació.

**On es penja no se sap, i deixar escrit que era el tancament de sessió era un
error meu.** Contrastat amb Codex el 7 d'agost i verificat log a log: a les
tretze execucions on `EdsCloseSession` es va arribar a cridar, va tancar
**net** —`CLEANUP_END ok=true` a totes—, incloses les quatre de l'escala de
pulsació, que acumulen 21 i 22 rebuigs `DEVICE_BUSY`. L'única sense tancament
net és `step6_tighter.log`, i allà el tancament **no es va cridar mai**: el
fitxer s'acaba a mitja línia de `FRAME index=49`, sense `capture_failed`,
sense `CLEANUP_BEGIN` i sense `close_session`. O sigui que el penjat és dins
el bucle de fotogrames —pulsació, alliberament, setter o bombeig
d'esdeveniments—, no al tancament.

La causa reparable més plausible, també de Codex i confirmada al codi: el
camí terminal de l'ajudant va directe de `take_frame=false` a `finish()` i
**es salta el `pump_events(0.50)`** que sí que fa el camí net
(`r6m3_single_hdr.mm:678`), i el header de Canon demana explícitament cridar
`EdsGetEvent` amb regularitat a les aplicacions de consola (`EDSDK.h:1379`).
La geometria que es va penjar és justament la que menys temps passa bombejant
esdeveniments. **És una hipòtesi, no una mesura**, i es confirma o es desmenteix
amb tres coses: registre sense buffer amb `CALL_BEGIN/END` i thread a cada
crida, un `sample`/spindump del procés penjat, i una A/B d'error terminal amb
i sense drenatge.

Que no estigui diagnosticat no canvia la decisió operativa —un canal que per
recuperar-se demana que algú apagui el cos no és operable el 12 d'agost—, però
sí que canvia què s'hauria de fer si algun dia es reprèn: mirar el bucle de
fotogrames, no el tancament.

Aquest és el punt que decideix, i no és de rendiment:

- **gphoto2 falla consumint l'acció** i continuant, o aturant el canal amb
  estat conegut. Tot recuperable dins la missió, que és el literal de Mission
  First;
- **l'EDSDK falla penjant-se**, en un punt que no s'ha localitzat. El marge
  entre «112 fotogrames nets» i «penjat irrecuperable» és **un sol esglaó de
  geometria**.

## 6. Un error meu que va falsejar la primera lectura

Val la pena deixar-ho escrit perquè va estar a punt de tancar la investigació
amb la conclusió contrària.

Els tres primers intents del programa sencer es van aturar als fotogrames 26,
27 i 29, amb un setter de 443 ms de mediana —pràcticament igual que gphoto2—.
La lectura hauria estat «l'SDK no compra res».

Era un defecte de l'ajudant: llençava el setter just després de la pulsació
anterior, quan el cos encara exposa. `kEdsPropID_Tv` queda rebutjada amb
`DEVICE_BUSY` mentre dura l'exposició, i l'espera creix amb ella:

| Exposició anterior | Espera fins que accepta el canvi |
|---|---:|
| 1/2000 | ~300 ms |
| 1/8 | 330 ms |
| 0,5 s | 630 ms |
| 2 s | 928 ms |
| 8 s | > 2.700 ms |

El worker de gphoto2 programa el setter a `instant_del_fotograma − setter_gap`
i per això no hi topa mai. Amb el setter a la seva ranura, la v2 va donar
**92/92 amb zero rebuigs i un setter de 24 ms**. La xifra dolenta era meva, no
del cos.

## 7. Recomanació

**Quedar-se amb gphoto2 per a la missió del 12 d'agost.**

El +22 % és real i l'earthshine extra també. El preu, a cinc dies de
l'eclipsi:

- un mode de fallada **irrecuperable sense tocar el cos**, a un esglaó del
  punt de treball;
- un backend **privat i no empaquetable**, fora del contracte de 49 inputs
  que la GUI verifica;
- una **dependència de TCC**: l'ICA demana permís de volums extraïbles i
  l'atribueix a l'aplicació responsable. Un procés sense cadena d'atribució
  rep zero càmeres i cap error visible;
- un **conflicte de piles** permanent: mentre l'ICA reté el cos, gphoto2 no
  el pot obrir. Recuperar-lo demana la guarda de `ptpcamerad` matant-lo en
  bucle, i el preflight, el ledger i l'inventari CFexpress hi van tots.

Si algun dia es reprèn, l'ordre és clar: primer resoldre el penjat, després
empaquetar, i només llavors parlar del +22 %.

## 8. El regal que la mesura fa a gphoto2

Hi ha un número d'aquesta campanya que **no és de l'SDK sinó del cos**, i per
tant val per als dos camins: el **terra de pulsació sostinguda**.

| Interval demanat | Fotogrames | Rebuigs `DEVICE_BUSY` | Retard màxim |
|---:|---:|---:|---:|
| 200 ms | 12 | 22 | 2.316 ms |
| 250 ms | 12 | 21 | 1.637 ms |
| 300 ms | 12 | 21 | 1.211 ms |
| **400 ms** | **12** | **0** | **10,7 ms** |

El cos accepta una pulsació cada 400 ms i no cada 300. **El programa de
missió va a 500 ms**, i el setter de gphoto2, mesurat entre 415 i 453 ms
sobre 54 canvis, en té reservats **620**. Hi ha marge als dos costats i no
l'ha destapat l'SDK: l'ha destapat el cos.

Recompilant el nucli viu amb constants alternatives —offline, sense tocar cap
càmera— surt això a 98,8 s de totalitat:

| setter | interval | Fotogrames | Dins totalitat | Earthshine |
|---:|---:|---:|---:|---:|
| 0,62 | 0,50 (missió d'avui) | 92 | 74 | 2 |
| 0,55 | 0,45 | 91 | 71 | 3 |
| **0,55** | **0,40** | **102** | **79** | **3** |
| 0,50 | 0,40 | 102 | 79 | 3 |
| 0,15 | 0,40 (com l'SDK) | 132 | 109 | 3 |

**+11 % de fotogrames i un fotograma d'earthshine més, per gphoto2.** És la
meitat del que compra l'SDK, sense el mode de fallada que el desaconsella.
Que 0,45 doni menys que 0,50 no és un error: és la quantificació de la secció
següent.

Això **no està demostrat al cos per gphoto2**. La pulsació de gphoto2 és més
barata que la de l'SDK —53-61 ms contra 111-143— i el rebuig és del cos, no
del transport, o sigui que hi ha bones raons per esperar que aguanti; però
mentre no hi hagi un run net amb delta CFexpress exclusiu i el menú comptat
abans i després, és una hipòtesi.

I el marge guanyat té una segona destinació, que és la que Pere ha triat:
**pagar un earthshine més llarg**. A f/5,5 i ISO 100 un fotograma de 8 s
queda uns dos punts per sota dels 8 s de l'A7RIIIA a f/2,8; amb la cadència
estreta, pujar-lo a **15 s** dona **94 fotogrames i dos d'earthshine** —contra
els 92 i dos de 8 s d'avui— o sigui que el fotograma llarg surt de franc. Un
de 30 s també hi cabria (98 fotogrames, un de sol), però demanaria un lease
de 30,45 s i el sostre s'ha mogut només fins a 16,00.

La mesura ho prova tot alhora, i no cal tocar cap constant de missió:

```bash
controller/tools/run_r6m3_single_hdr_probe.py --port usb:001,001 \
  --output controller/runs/single_hdr_tight15_20260807.json \
  --totality-s 98.8 --setter-gap-s 0.55 --frame-min-gap-s 0.40 \
  --frame-overhead-s 0.40 --frame-ready-floor-s 0.30 \
  --frame-ready-overhead-s 0.30 --deep-tail 2,15
```

## 9. Un defecte de quantificació que no necessita cap SDK

L'empaquetat del tram del mig és cobdiciós i només hi posa **escales
senceres**: una escala que no hi cap no s'hi posa. El que sobra queda **mort**
—cap fotograma— fins que obre la finestra de C3:

| Totalitat | Temps mort | Del tram del mig |
|---:|---:|---:|
| 30 s | 4,05 s | 20,3 % |
| 80 s | 7,41 s | 10,6 % |
| **98,8 s** | **2,70 s** | 3,0 % |
| 158,8 s (pitjor cas) | **8,00 s** | 5,0 % |

És exactament el que fa que estrènyer a 0,45 doni *menys* fotogrames que
0,50: el marge guanyat no arriba a pagar una escala sencera més i es
converteix en temps mort. Omplir-lo a l'obturació de contacte —o sigui obrir
la finestra de C3 abans— són **5 fotogrames més a 98,8 s i 14 a 80 s**, sense
cap valor nou, sense cap cadència nova i sense trencar cap escala.

## 10. On l'SDK sí que és insubstituïble

El **tipus d'obturador**. Dels 82 paths que libgphoto2 publica en aquest cos,
cap no és el mecànic/electrònic. L'SDK el llegeix i l'escriu, i el canvi
sobreviu el cicle d'alimentació. Eina de preparació abans de la missió, no
camí de captura. Això encaixa amb el contracte actual i no demana res nou.

## 11. Límits i estat físic

- **El delta de +510 és global, no per execució.** Cada run net té el seu
  recompte al log, però no s'ha fet una instantània abans i després de
  cadascun: mentre l'SDK treballa, gphoto2 no pot llistar la targeta.
- Òptica Sigma 35 mm, no el VSD90SS. No qualifica tren òptic ni ciència.
- **Estat en tancar**: cos reiniciat, bateria **81 %**, menú **sa a 58
  opcions**, i restaurat a l'estat de missió —**1/320, Single, AEB off**—.
  4.841 CR3 a la CFexpress, zero esborrats, zero formats.
- Les seccions 8 i 9 són **anàlisi offline**, no mesura: recompilen la
  geometria viva amb constants alternatives. Els números de fotogrames són
  deterministes; que el cos els aguanti per gphoto2, no.
