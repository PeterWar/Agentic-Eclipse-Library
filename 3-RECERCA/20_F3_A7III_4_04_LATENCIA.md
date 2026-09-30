# 20 — F3 A7III 4.04: latència real del canvi d'obturació

**Data:** 2026-07-27  
**Càmera:** Sony A7III (`ILCE-7M3`)  
**Firmware:** 4.04 confirmat per l'operador; el readback PTP exposa `4.0`  
**Control:** `gphoto2 2.5.32` + `libgphoto2 2.5.34`, USB PC Remote  
**Estat:** **F3a tancada amb FAIL**

## Decisió executiva

La coreografia candidata de 2024, traslladada tal qual a l'A7III, **no és apta per a l'eclipsi de 2026 si depèn de 15 canvis dinàmics de velocitat d'obturació durant el tram crític**.

F3 no invalida gphoto2 com a disparador. Invalida aquesta arquitectura concreta:

- 15 canvis `set-config-index` dins de la seqüència;
- pressupostos de temps basats en 34,25 s, insuficients davant les mesures físiques;
- dependència que cada canvi de velocitat acabi abans de poder continuar.

La via recomanada és conservar gphoto2 per als dispars, però eliminar o reduir radicalment els canvis de configuració durant la totalitat: blocs amb paràmetres fixos, ràfegues/bràqueting natiu i preparació prèvia de cada estat.

> **Precisió terminològica:** els temps de F3 no són una confirmació simple de la càmera. Són el temps fins al **retorn de l'ordre `set-config-index` de gphoto2/libgphoto2**, que inclou el bucle intern de polling i la lectura de confirmació de la propietat.

## Resultat físic

| Magnitud | Resultat |
|---|---:|
| Transicions provades | 15 |
| Repeticions per transició | 10 |
| Operacions correctes | 150/150 |
| Captures efectuades | 0 |
| Activacions de l'obturador | 0 |
| Restauració final | `1/125`, verificada |
| Temps total mesurat, 150 canvis | 408,594 s |
| Mínim individual | 1,249 s |
| Mediana global | 2,296 s |
| Mitjana global | 2,724 s |
| Màxim individual | 6,633 s |

La prova és, per tant, concloent en dues dimensions:

1. **Funcionalitat:** la càmera accepta els 150 canvis i retorna el valor correcte.
2. **Temps real:** l'operació és massa lenta i variable per inserir quinze salts dins d'una totalitat curta.

## Pressupost acumulat de la coreografia

| Pressupost dels 15 canvis | Temps | Diferència respecte del candidat |
|---|---:|---:|
| Candidat actual | **34,250 s** | — |
| Suma dels màxims observats | **49,043 s** | +14,793 s / +43,2% |
| Suma de pressupostos d'enginyeria recomanats | **61,300 s** | +27,050 s / +79,0% |

Els 61,3 s incorporen marge per transició a partir de les deu repeticions físiques; són 12,257 s més que la simple suma dels màxims observats.

Aquestes xifres són només el **pressupost de mutació de paràmetres al host**. No inclouen exposicions, cadència de captura, escriptura dels RAW, buidatge del buffer ni cap espera fotogràfica. Per tant, no s'han d'interpretar com la durada total de la seqüència: són temps que s'hi afegirien o que en bloquejarien l'execució.

## Resultat per transició

Temps en segons, des de l'enviament fins al retorn complet de l'ordre gphoto.

| # | Transició | Mín. | Mediana | Màx. | Candidat | Recomanat | Veredicte |
|---:|---|---:|---:|---:|---:|---:|---|
| 1 | `1/2500 → 1/400` | 2,926 | 2,951 | 3,796 | 4,00 | 4,4 | FAIL |
| 2 | `1/400 → 1/8000` | 2,928 | 3,775 | 4,656 | 3,50 | 6,2 | FAIL |
| 3 | `1/8000 → 1/500` | 2,937 | 3,801 | 4,265 | 3,00 | 5,6 | FAIL |
| 4 | `1/500 → 1/250` | 1,280 | 2,107 | 2,337 | 1,50 | 2,9 | FAIL |
| 5 | `1/250 → 1/100` | 1,899 | 2,103 | 2,311 | 1,50 | 2,9 | FAIL |
| 6 | `1/100 → 1/30` | 2,082 | 2,104 | 2,946 | 1,50 | 3,5 | FAIL |
| 7 | `1/30 → 1/15` | 1,255 | 2,103 | 2,325 | 1,25 | 2,9 | FAIL |
| 8 | `1/15 → 1/8` | 1,249 | 2,002 | 2,310 | 1,25 | 3,3 | FAIL |
| 9 | `1/8 → 0.4` | 1,900 | 2,106 | 3,138 | 1,50 | 3,8 | FAIL |
| 10 | `0.4 → 1` | 1,265 | 2,100 | 2,319 | 1,50 | 2,9 | FAIL |
| 11 | `1 → 2` | 2,087 | 2,102 | 2,321 | 1,25 | 2,9 | FAIL |
| 12 | `2 → 0.8` | 1,258 | 2,104 | 2,312 | 1,50 | 2,9 | FAIL |
| 13 | `0.8 → 1/8000` | 4,400 | 5,263 | **6,633** | 5,50 | **7,8** | FAIL |
| 14 | `1/8000 → 1/400` | 2,975 | 3,695 | 4,213 | 3,00 | 5,6 | FAIL |
| 15 | `1/400 → 1/2500` | 2,935 | 2,957 | 3,160 | 2,50 | 3,7 | FAIL |

Les dues transicions més compromeses són justament les que afecten els extrems crítics:

- C2, `1/400 → 1/8000`: màxim 4,656 s; pressupost recomanat 6,2 s.
- C3, `0.8 → 1/8000`: màxim 6,633 s; pressupost recomanat 7,8 s.

## Per què passa: camí Sony «mode 2» de libgphoto2

El resultat deixa de ser misteriós quan es llegeix el camí oficial del controlador PTP2 de libgphoto2.

### 1. El mode Sony 2 entra en un setter específic

Quan `sony_mode_ver == 2`, libgphoto2 deriva el canvi d'obturació a `_put_Sony_ShutterSpeedMode2`. El codi intenta primer una propietat directa `PTP_DPC_SONY_ShutterSpeed2`; si no està disponible, continua pel camí relatiu.

Font oficial: [`config.c`, selecció del mode i setter](https://github.com/gphoto/libgphoto2/blob/c58e2a19b1113fe139101e592c1e4609a55570a1/camlibs/ptp2/config.c#L5400-L5439) i [encaminament de `sony_mode_ver == 2`](https://github.com/gphoto/libgphoto2/blob/c58e2a19b1113fe139101e592c1e4609a55570a1/camlibs/ptp2/config.c#L5561-L5593).

### 2. El salt es converteix en moviment relatiu de diversos «clics»

En el camí relatiu, el driver:

1. localitza la posició actual i la posició sol·licitada dins de l'enumeració;
2. calcula la direcció;
3. envia la diferència de posicions com un salt de múltiples passos;
4. utilitza `ptp_sony_setdevicecontrolvalueb`.

Font oficial: [`config.c`, càlcul del salt relatiu i enviament](https://github.com/gphoto/libgphoto2/blob/c58e2a19b1113fe139101e592c1e4609a55570a1/camlibs/ptp2/config.c#L5440-L5505).

La funció es tradueix a l'operació Sony `SDIO_ControlDevice`; el codi oficial li assigna el valor **`0x9207`**.

Fonts oficials: [`ptp.c`, implementació de `setdevicecontrolvalueb`](https://github.com/gphoto/libgphoto2/blob/c58e2a19b1113fe139101e592c1e4609a55570a1/camlibs/ptp2/ptp.c#L4268-L4280) i [`ptp.h`, codis `0x9207` i `0x9209`](https://github.com/gphoto/libgphoto2/blob/c58e2a19b1113fe139101e592c1e4609a55570a1/camlibs/ptp2/ptp.h#L660-L668).

### 3. Després de l'ordre, libgphoto2 fa polling

El setter no retorna immediatament després d'enviar el control relatiu. Entra en un bucle que:

- demana repetidament totes les propietats Sony amb `GetAllExtDevicePropInfo`;
- torna a llegir la propietat d'obturació;
- comprova si hi ha hagut canvi i si ja s'ha arribat al valor objectiu;
- espera **200 ms** entre consultes;
- pot repetir el procés fins a completar el salt.

Fonts oficials: [`config.c`, bucle de polling i `usleep(200*1000)`](https://github.com/gphoto/libgphoto2/blob/c58e2a19b1113fe139101e592c1e4609a55570a1/camlibs/ptp2/config.c#L5509-L5559) i [`ptp.c`, `GetAllExtDevicePropInfo`](https://github.com/gphoto/libgphoto2/blob/c58e2a19b1113fe139101e592c1e4609a55570a1/camlibs/ptp2/ptp.c#L4228-L4231).

### 4. Interpretació de F3

F3 cronometra precisament aquesta operació síncrona completa. Per això:

- un canvi de configuració no equival a un paquet USB amb confirmació immediata;
- els salts llargs tendeixen a consumir més temps;
- el màxim de `0.8 → 1/8000` és coherent amb un salt relatiu gran més el polling;
- la variabilitat inclou el temps que libgphoto2 tarda a observar i confirmar el nou estat.

La traça F3 no és una traça de depuració interna de funcions, però el comportament físic mesurat, el tipus de control exposat per l'A7III i el camí oficial Sony mode 2 expliquen conjuntament l'escala i la dependència amb la magnitud del salt.

## Implicacions per al controlador de l'eclipsi

### El que queda descartat

- Reproduir les quinze mutacions de velocitat de 2024 durant la totalitat.
- Confiar en pauses de 1,25–5,5 s com si fossin suficients.
- Llançar el canvi de forma asíncrona i disparar «a cegues»: eliminaria el bloqueig, però també la certesa de quina velocitat té realment la càmera.

### El que no queda descartat

- gphoto2 com a **trigger** de captures amb la càmera ja configurada.
- Una sessió persistent i offline.
- La captura a targeta sense transferir els RAW al Mac.
- L'ús de gphoto2 abans o després del tram crític per preparar un estat estable.

El camí de captura no necessita executar el setter d'obturació de mode 2 en cada foto. Per tant, no s'ha de generalitzar el FAIL de `set-config-index` a la latència del disparador fins que la prova específica de captures ho mesuri.

## Arquitectura que ha de substituir la candidata

La següent iteració ha de partir d'aquestes regles:

1. **Zero canvis d'obturació per gphoto en el nucli C2–C3**, si és possible.
2. Preconfigurar abans de C2 un mode de càmera que generi la seqüència amb funcions natives: bràqueting, ràfega o blocs fixos.
3. Reservar gphoto2 per ordenar inici/fi de cada bloc i registrar-ne el temps.
4. Separar la cobertura:
   - un bloc optimitzat per cromosfera/perles/anell;
   - un bloc estable per corona;
   - retorn preconfigurat per C3.
5. Repetir una prova física de captura real en RAW sense descàrrega, mesurant:
   - `trigger → primera exposició`;
   - cadència sostinguda;
   - saturació i recuperació del buffer;
   - estabilitat del trigger persistent;
   - deriva temporal respecte del rellotge monotònic.

## Conclusió

**F3a = FAIL i `timing_qualified = false` per a la coreografia de quinze canvis.**

La causa no és un únic retard inexplicable de la càmera: és la combinació documentada del control relatiu Sony mode 2, el salt multi-posició via `0x9207` i el bucle de polling/readback de libgphoto2 cada 200 ms abans que retorni l'ordre gphoto.

La decisió correcta no és abandonar gphoto2, sinó **treure els setters d'obturació del camí crític** i qualificar per separat el disparador persistent amb paràmetres fixos.

## Evidència local

- [Informe físic F3](../controller/runs/20260727T021536_candidate_a7m3_ap130_2024_choreography_f3-shutter/F3_PHYSICAL_REPORT.md)
- [Resultat estructurat](../controller/runs/20260727T021536_candidate_a7m3_ap130_2024_choreography_f3-shutter/result.json)
- [Esdeveniments crus](../controller/runs/20260727T021536_candidate_a7m3_ap130_2024_choreography_f3-shutter/events.jsonl)
- [Transcripció gphoto](../controller/runs/20260727T021536_candidate_a7m3_ap130_2024_choreography_f3-shutter/gphoto_transcript.log)

Versió oficial de libgphoto2 auditada: commit [`c58e2a19b1113fe139101e592c1e4609a55570a1`](https://github.com/gphoto/libgphoto2/tree/c58e2a19b1113fe139101e592c1e4609a55570a1).
