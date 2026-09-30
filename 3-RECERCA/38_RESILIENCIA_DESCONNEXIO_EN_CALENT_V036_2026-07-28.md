# Resiliència en calent v0.3.6 i reobertura física PTP

Data: 28-07-2026  
Cos: Sony A7III `ILCE-7M3`  
Sèrie autoritzada: `[SÈRIE]`  
Perfil: `candidate_a7m3_ap130_short_checkpointed_1x5_3x9`  
Estat: **CANDIDATE_NOT_PRODUCTION**

## Conclusió

La v0.3.6 converteix una pèrdua USB/PTP d'un abort global inevitable en una
recuperació finita, exactament lligada al mateix cos i al calendari
monotònic original. Prioritza dues coses alhora:

1. no duplicar mai una fotografia que podria haver començat;
2. salvar les fases futures que encara siguin temporalment i físicament
   segures.

El perfil no ha canviat. El hash exacte de la v0.3.6 ha superat **2/2
cronologies físiques completes a 97,300 s**, una amb pèrdua controlada del
procés `gphoto2` abans de C2 i una de neta. Això requalifica la cronologia
del codi exacte, però no una extracció física del cable ni un canvi real de
bateria. Per això l'estat continua sent candidat.

## Canvis de control

- Reconnexió opt-in amb `--recover-disconnects`.
- Autodetecció viva a cada epoch; cap reutilització cega del port USB.
- Mateix lock model+sèrie durant tot el run.
- Tancament del procés gphoto2 vell abans d'obrir-ne un de nou.
- Sèrie exacta obligatòria a cada reobertura; un cos diferent falla sense
  cap write.
- Durant lead/keepalive, preflight complet de lectura i sense repetir la
  sonda física.
- Durant la timeline, primer write de la sessió nova: release idempotent
  `capture=0`.
- Revalidació de bateria `≥50%`, ISO, ruta `card+sdram`, DRO, crop i altres
  gates estàtics.
- Revalidació de l'obturació i `capturemode` dinàmics que el ledger espera
  en aquell instant.
- Targets C2/C3 monotònics immutables; cap *catch-up*.
- Finestra per defecte de 8 s dins d'una acció.
- Cleanup amb fins a tres reobertures finites de 60 s per confirmar release,
  drenatge i restore.

## Regla de trigger

El punt de commit és la línia completa, inclòs el newline, escrita al PTY de
gphoto2:

- si no existeix token de commit, el procés vell ja està tancat i queda marge
  dins del deadline original, s'admet exactament un retry;
- si existeix token o l'estat és ambigu, no es repeteix el press;
- després d'un press ambigu, la sessió nova confirma release, l'acció queda
  degradada i només es permeten dependències futures explícitament segures;
- qualsevol reconnexió de timeline impedeix que el resultat acabi com a
  `complete`.

## Drenatge i payloads parcials

Una fallada de `wait-event-and-download` pot haver escrit alguns JPEG abans
de perdre el prompt. La v0.3.6 no els descarta ni torna a començar des d'un
nombre estàtic. Recalcula:

`deute pendent = captures compromeses − fitxers de captura locals`

i reprèn només aquest deute. Cap recuperació de drenatge pot enviar un nou
trigger. La SD continua sent l'autoritat dels ARW científics.

## Evidència offline

Ordre:

```bash
/usr/bin/python3 -m unittest discover -s controller/tests -v
```

Resultat: **419/419** proves correctes.

La cobertura nova inclou:

- `EIO`, `EPIPE` i pèrdua abans del write amb retry únic;
- write parcial sense token de commit;
- ACK de press ambigu, zero replay i deute preservat;
- ACK ambigu d'obturació o `capturemode`: zero replay del setter i un únic
  readback desambiguador després de reconnectar;
- pèrdua en lectura de cua abans i després del press;
- drenatge parcial amb JPEG local;
- canvi de port;
- sèrie incorrecta fatal;
- bateria i invariants estàtics/dinàmics;
- timeout estricte d'obertura dins del deadline absolut;
- reconnexió durant preflight, sonda de ruta i keepalive pre-trigger;
- ledger incremental després d'una excepció;
- release, drenatge i restore sobre una sessió reoberta, inclòs cleanup
  protegit i fins a tres epochs.

El dry-run del perfil a `C3=C2+97,300 s` manté:

- 36/36 accions;
- 55 captures planificades;
- zero skips;
- els mateixos offsets i el mateix hash de perfil.

## Evidència física prèvia

### Preflight

Resultat:

`controller/runs/20260728T193153_candidate_a7m3_ap130_short_checkpointed_1x5_3x9_preflight/result.json`

Va demostrar:

- una sola A7III detectada a `usb:001,001`;
- sèrie exacta;
- bateria 55%;
- cua zero;
- Single Shot;
- ISO 100;
- `1/8000`;
- DRO Off;
- Sensor Crop Off;
- `capturetarget=card+sdram`;
- zero errors, cleanup correcte i cap captura.

### Reobertura de procés PTP

Eina:

`controller/tools/qualify_transport_reconnect_readonly.py`

Resultat:

`controller/runs/20260728T173242_candidate_a7m3_ap130_short_checkpointed_1x5_3x9_transport-reconnect-readonly/result.json`

Procediment i resultat:

- lock adquirit una sola vegada;
- preflight complet inicial;
- mort deliberada només del procés gphoto2 propietat de l'eina;
- redetecció i reobertura al primer intent;
- mateixa sèrie exacta;
- segon preflight complet;
- epoch de connexió `2`;
- 258,608 ms entre la injecció i el final del segon preflight;
- 56 ordres, totes `get-config`;
- zero writes, zero triggers i zero fitxers de captura;
- lock i sessions alliberats.

La prova acredita reobertura de procés i PTP. No equival a treure físicament
el cable USB-C, ni acredita el release de sessió nova després d'un press real.

## Dos runs físics complets del hash v0.3.6

S'ha respectat el límit estricte de **DOS** runs físics, amb `C3=C2+97,300
s`, C2 prou lluny per completar preflight i armat, i les opcions
`--arm --confirm-manual-checklist --allow-candidate --qualification-run
--recover-disconnects`. No s'ha desactivat cap interlock.

### Run 1: pèrdua de procés abans de C2

Resultat:

`controller/runs/20260728T193451_candidate_a7m3_ap130_short_checkpointed_1x5_3x9_run/result.json`

Després de la sonda de ruta i durant el keepalive pre-trigger, es va matar
només el fill `gphoto2` propietat del controlador. La reobertura va:

- redetectar i verificar la mateixa sèrie exacta;
- repetir el preflight basal complet;
- arribar a l'epoch `2` en 292,922 ms;
- conservar C2/C3 i tots els targets originals;
- completar 36/36 accions, 55/55 captures i zero skips;
- acabar sense degradació de timeline, perquè la pèrdua va ser abans de la
  primera acció científica;
- confirmar cua zero, cleanup, restore i release final.

### Run 2: control net

Resultat:

`controller/runs/20260728T194123_candidate_a7m3_ap130_short_checkpointed_1x5_3x9_run/result.json`

Va completar 36/36 accions, 55/55 captures, zero skips, cap reconnexió, cua
final zero, cleanup, restore i release final. En tots dos runs:

- `status=complete`;
- zero espera o retard artificial de 20 s;
- JPEG de telemetria únics, ISO 100 i seqüència Exif correcta;
- hash del controlador i del perfil verificats, així com els hashes de
  payload;
- `scientific_raw_verified=false`, perquè els ARW no s'han descarregat ni
  inspeccionat.

El gate temporal conjunt dels dos resultats nous va passar amb verificació
dels fitxers actuals i dels payloads: 2×36 accions, 2×55 captures, 0 skips i
span exacte de 97,300 s.

## Comparació temporal

| Mètrica | v0.3.5, 3 runs qualificats | v0.3.6, 2 runs nous |
|---|---:|---:|
| Trigger físic màxim | 0,879 ms | 3,019 ms |
| Lateness màxima d'acció | 0,022 ms | 0,022 ms |
| Canvi d'obturació màxim | 4.872,475 ms | 4.860,014 ms |
| Canvi de `capturemode` màxim | 848,053 ms | 777,265 ms |
| Drenatge C2 pitjor | 5.500,802 ms | 5.688,439 ms |
| Drenatge 5×3 pitjor | 2.343,169 ms | 2.336,069 ms |
| Drenatge 3×9 pitjor | 14.340,958 ms | 14.552,795 ms |
| Marge de deadline mínim | 771,680 ms | 842,024 ms |
| Marge llest abans de C3 | 1.060,838–1.072,060 ms | 1.052,024–1.060,981 ms |

El coll d'ampolla principal continua sent el drenatge dels 27 JPEG del bloc
3×9, ara amb pitjor cas de 14,553 s. El segon és el canvi a/de `1/30`, al
voltant de 4,86 s. La reconnexió pre-trigger de 292,922 ms queda molt per
sota del lead disponible i no ha alterat la timeline. Els marges són sans,
però el marge llest abans de C3 és només d'uns 1,05 s: no convé estrènyer el
perfil sense una nova qualificació física.

## Compatibilitat amb l'evidència v0.3.5

El gate offline dels tres runs curts antics continua passant amb rehash dels
165 JPEG:

- 3/3 runs;
- 36 accions per run;
- 55 imatges per run;
- 97,300 s;
- zero skips;
- hash v0.3.5:
  `c9afc078b2d62b07a6b3d9ce9bbf00f79e24b3071be6d05557b94e66f38b120e`.

La comprovació s'ha executat amb `--no-verify-current-files` perquè és
evidència històrica, no una qualificació del codi actual.

Hashes exactes després d'aquesta ronda:

- controlador v0.3.6:
  `208030cb9316622aee8b9f2ecd74eb2a1abaf0679514621e74466236e379d8c0`;
- perfil, sense canvis:
  `d6ee636db3697df581675ecb2661be2690bbbd0909e0b1c06297a31f1e8d887e`;
- eina de reconnexió:
  `71adf2a3b9a6b83840921dfc6ade212d011260a0694bea85babd3c356be75f8f`.

## Gate pendent

Abans de considerar la v0.3.6 apta per a l'eclipsi cal:

1. assaig supervisat amb extracció i reconnexió física del cable;
2. assaig supervisat de canvi real de bateria, preferentment abans de C2;
3. demostrar en una pèrdua dins la timeline mateixa sèrie, release de la
   sessió nova, cap press duplicat, anchors intactes i resultat degradat;
4. gate correlacionat dels 56 ARW + 56 JPEG de la SD, separant la sonda;
5. simulació òptica de camp i promoció explícita del perfil.

La versió exacta ja té evidència offline, reobertura PTP i dues cronologies
físiques completes. El límit de dos runs d'aquesta campanya queda exhaurit.
Fins completar els punts anteriors, continua sent **CANDIDATE_NOT_PRODUCTION**
i no s'ha de presentar com a release de l'eclipsi.

## Estat segur de tancament

L'últim run va confirmar:

- cua final zero;
- restauració verificada a `Single Shot` i `1/8000`;
- release final confirmat;
- `physical_state_unknown=false`;
- cleanup correcte;
- cap `gphoto2` ni procés `eclipse_capture.py`;
- tots els locks persistents del controlador lliures.

No s'ha enviat cap ordre PTP de power-off. L'interruptor físic continua en
`ON` i el mecanisme previst és `Pwr Save Start Time = 30 Min`. macOS,
tanmateix, torna a crear automàticament `/usr/libexec/ptpcamerad` mentre
l'USB-C continua connectat: es va provar TERM i KILL, i el procés va
reaparèixer. Per garantir que no queda cap sessió PTP del sistema i permetre
el repòs, l'única acció manual pendent és **desconnectar físicament l'USB-C
de la càmera**. No s'ha desactivat cap servei del sistema.
