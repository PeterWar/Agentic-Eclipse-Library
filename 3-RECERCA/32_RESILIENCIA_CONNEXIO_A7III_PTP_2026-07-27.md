# Resiliència de connexió A7III — USB, `ptpcamerad` i PTP

Data: 27-07-2026  
Estat: implementat i verificat amb preflight físic; pendent d'integrar-se al
gate de captura `screen 3/3`.

## Problema observat

La pantalla de l'A7III podia quedar-se a `Connecting…` i `gphoto2` detectava
el cos de manera intermitent. El mateix símptoma visual amagava tres classes
de fallada diferents:

1. la càmera era físicament al bus USB, però `ptpcamerad` de macOS retenia
   la interfície PTP abans que `gphoto2 --auto-detect` la pogués enumerar;
2. el controlador acceptava un `--port usb:BUS,DEVICE` d'una connexió
   anterior, tot i que aquest endpoint és volàtil;
3. `gphoto2 --shell` mostrava el prompt mandrós però la primera ordre
   `get-config` fallava amb `I/O in progress (-110)`.

El log de 2024 conserva un cas en què el cos ja havia estat detectat i la
interfície reclamada, però `OpenSession` va expirar repetidament durant més de
50 segons. Repetir lectures dins el mateix shell no era una recuperació
fiable.

## Evidència local del 27-07-2026

- IORegistry veia físicament `ILCE-7M3`, VID Sony `0x054c`, PID `0x0c34`,
  sèrie USB `[SÈRIE]` i enllaç de 5 Gbit/s.
- Un run forçat amb el port antic `usb:002,001` va fallar amb `-110`.
- L'autodetecció viva va trobar el port real `usb:000,001`.
- El primer shell que va arribar a respondre va publicar encara sentinels:
  `capturemode=Unknown value 0000`, `DRO=Unknown value 0000`, ISO `0` i
  obturació `65535/65535`. El preflight antic els va confondre amb un ajust
  manual incorrecte.
- Una segona sessió va publicar immediatament els valors reals i va passar:
  `Single Shot`, `DRO Off`, ISO 100 i `1/8000`.

Runs preservats:

- `controller/runs/20260727T230045_..._preflight`: port caducat i `-110`;
- `controller/runs/20260727T230314_..._preflight`: sentinels inicials;
- `controller/runs/20260727T230343_..._preflight`: primera lectura estable
  amb el codi anterior;
- `controller/runs/20260727T231704_..._preflight`: primer preflight físic amb
  la nova màquina d'estats.

## Solució implementada a v0.3.0

No es permet cap mutació ni tret fins arribar a `PTP_READY`:

1. `DISCOVER`: el guard de `ptpcamerad` comença **abans** de
   `gphoto2 --auto-detect`; hi ha un intent immediat i, si cal, dos reintents
   curts a 250 i 500 ms.
2. Un `--port` explícit també es compara amb l'inventari viu. Si no coincideix
   amb el port actual del model esperat, es rebutja com a caducat.
3. `OPEN_VERIFY`: s'obre un shell persistent sota un altre guard i es llegeix
   la sèrie exacta. El prompt inicial no compta com a sessió oberta.
4. Si la primera obertura retorna `-110`, es mata el shell complet, es torna a
   detectar el port i es fa **una sola** reobertura neta. No es repeteix cap
   write ni cap trigger.
5. `IDENTITY_OK`: una sèrie diferent falla immediatament i no es reintenta.
6. Abans de `PTP_READY`, quatre propietats es llegeixen com un bloc coherent.
   `Unknown value`, ISO `0` o `65535/65535` es tracten com a estat transitori,
   no com a configuració manual. La finestra és finita, de 3 s.
7. El lock local és model+sèrie, no model+port; una reconnexió no pot esquivar
   l'exclusió mútua canviant de número USB.
8. Si el procés no pot inspeccionar/alliberar `ptpcamerad`, falla abans
   d'obrir PTP amb una instrucció explícita. No continua amb una protecció
   fictícia.

La mateixa adquisició resilient s'utilitza al controlador principal i a
`qualify_mid_drain_windows.py`. La sonda independent
`verify_pc_jpeg_route.py` també reobre la sessió per aquesta via.

## Resultat físic

Després de tancar les vores de deadline, guard continu i cleanup, es va
executar una sèrie final de deu preflights físics consecutius amb la mateixa
versió exacta, tots exclusivament de lectura:

- completats: `10/10`;
- preflight `ok=true`: `10/10`;
- detecció: primer intent `10/10`;
- obertura i identitat: primer intent `10/10`;
- una sola lectura de sèrie per run: `10/10`;
- sentinels inicials: `0/10`;
- fallades de connexió: `0/10`;
- cicles de guard continus: 10, amb 2 terminacions efectives de
  `ptpcamerad`;
- port viu: `usb:000,001`;
- bateria: 74%;
- durada total registrada per preflight: 249–294 ms;
- tirs: 0.

Això demostra repetibilitat de la ruta normal i que el guard ha intervingut
realment. No demostra encara estadísticament totes les branques de recuperació:
el `-110`, el port caducat i els sentinels estan coberts per tests automatitzats,
però faltava provocar-los deliberadament amb maquinari en una sessió controlada.

### Arrencada freda del 28-07-2026

Després d'apagar i tornar a encendre el cos, la pantalla mostrava
`Connecting...`. El run
`controller/runs/20260728T001447_candidate_a7m3_ap130_short_hybrid_5x3_then_9x1_preflight`
va adquirir el port `usb:000,001`, va verificar la identitat al primer intent
i va observar físicament la branca de sentinels:

- intents 1 i 2: `Unknown value`, ISO `0` i `65535/65535`;
- intent 3: només `capturemode` continuava sent `Unknown value`;
- intent 4: bloc coherent i estable;
- resultat: `preflight ok=true`, cua zero, cleanup correcte i zero tirs;
- durada externa aproximada: 1,88 s, dins el deadline finit de 3 s reservat
  per a la preparació PTP.

Aquesta prova tanca la incògnita de recuperació de sentinels en maquinari
real. No acredita encara una recuperació física deliberada de `-110` o de
desconnexió/reconnexió durant una sessió.

## Tests de regressió

La suite té 369 proves correctes. Les noves cobreixen com a mínim:

- port explícit viu acceptat i port caducat rebutjat;
- autodetecció buida seguida d'una detecció correcta;
- `pkill rc=3` falla tancat;
- sentinels seguits de valors estables, sense cap write;
- `-110` provoca dos shells i dues autodeteccions, no quatre lectures dins el
  mateix shell;
- lock estable per sèrie;
- cos amb sèrie incorrecta sense mutacions ni drenatge.

## Pendent abans de producció

1. Executar el `screen 3/3` del drenatge adaptatiu amb Silent Shooting i
   comprovar 45 ARW a la SD.
2. Fer un assaig controlat de desconnexió/reconnexió física per observar la
   branca de reobertura real; el despertar amb sentinels ja està acreditat.
3. Repetir un preflight amb Internet desconnectat i el Mac en la configuració
   de camp.
4. No promocionar el perfil a producció fins superar després el `qualify
   10/10`, validar els ARW sense comprimir i congelar hashes.
