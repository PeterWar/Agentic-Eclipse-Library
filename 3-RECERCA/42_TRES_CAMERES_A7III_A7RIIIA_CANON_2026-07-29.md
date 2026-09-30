# Tres càmeres: A7III, A7RIIIA i Canon 6D

**Data de comprovació:** 2026-07-29  
**Versió preparada:** Eclipse Command 0.4.3 /
`0.4.3-three-camera-usb-identity`

## Conclusió

El programa ja tracta els tres cossos com a identitats independents i no
confia només en l'etiqueta o el port que retorna `gphoto2 --auto-detect`.
La selecció efectiva té dos nivells:

1. la identitat USB exacta de macOS resol el port físic actual;
2. un cop obert el port, el controlador exigeix el model i la sèrie PTP
   exactes abans de qualsevol preflight, configuració o captura.

La Canon 6D i l'A7RIIIA han superat aquesta selecció física en coexistència,
en operacions exclusivament de lectura. L'A7III continua connectada com
`USB Charger`, de manera que no és encara visible com a càmera PTP i la seva
validació física simultània queda pendent. No s'ha disparat cap obturador ni
s'ha canviat cap ajust.

## Inventari físic observat

| Cos | Identitat USB observada | Port derivat | Identitat PTP |
| --- | --- | --- | --- |
| Sony A7RIIIA | `ILCE-7RM3A`, USB `[SÈRIE]` | `usb:000,001` | model `ILCE-7RM3A`, sèrie `[SÈRIE]` |
| Canon EOS 6D | `Canon Digital Camera`, producte `0x3250` | `usb:002,001` | model `Canon EOS 6D`, sèrie `[SÈRIE]` |
| Sony A7III | `USB Charger`, producte `0x0994` | no PTP | pendent fins que `USB Connection` sigui `PC Remote` |

Els ports són volàtils. No s'han copiat com a identitat persistent dins del
programa.

## Anomalia reproduïda

Amb la Canon i l'A7RIIIA connectades alhora, `gphoto2 --auto-detect` va
atribuir l'etiqueta `Canon EOS 6D` tant al port real de la Canon com al de
l'A7RIIIA. Obrir explícitament el segon port amb el driver Sony va confirmar
que el cos era realment l'A7RIIIA.

Per tant, l'etiqueta d'autodetecció no és autoritat suficient en aquest banc.
El nou resolver usa `IORegistry` només per trobar el port. Si la identitat USB
és absent, duplicada o contradictòria, si el port no apareix una sola vegada
en l'inventari PTP, o si després el model o la sèrie PTP no coincideixen,
l'operació falla tancada.

## Programes de càmera

- **Sony A7III:** conserva el programa de captura AP130 existent.
- **Canon EOS 6D:** conserva el programa candidat card-only de 23 contactes,
  amb trigger EOS propi i sense reutilitzar ordres Sony.
- **Sony A7RIIIA:** nou perfil `lab_a7r3a_readonly`; permet identificar i
  inspeccionar, però `operator_capture_enabled=false`. ARM, configuració
  automàtica i execució de captura estan bloquejats tant a la interfície com
  a la ruta interna de llançament.

La interfície no canvia automàticament de programa quan hi ha més d'una
càmera o les etiquetes d'autodetecció són ambigües.

## Preflights físics sense mutació

### A7RIIIA

La resolució per identitat USB va seleccionar `usb:000,001` malgrat
l'etiqueta d'autodetecció incorrecta. Després van coincidir model i sèrie PTP.
El preflight final 0.4.3 va observar bateria 15%, cua zero, mode M, enfocament manual,
RAW, ISO 100, `1/500`, temporitzador de 2 s i destí SDRAM.

Evidència:

```text
/private/tmp/eclipse-a7r3a-final-043-20260729-escalated/
  20260729T143409_lab_a7r3a_readonly_preflight/
```

### Canon EOS 6D

La resolució final 0.4.3 per identitat USB va seleccionar `usb:002,001` i
després van coincidir model i sèrie PTP. El preflight es va aturar de manera
segura per divergències d'ajustos: temporitzador de 2 s i obturació `30`,
mentre el perfil espera dispar únic i `1/4000`. També va observar Manual,
ISO 100, RAW, RAM interna, mirror lock 0 i bateria 50%.

No es va aplicar cap correcció.

Evidència:

```text
/private/tmp/eclipse-canon6d-final-043-20260729/
  20260729T143419_candidate_canon6d_contacts_cardonly_preflight/
```

Una primera invocació A7RIIIA dins el sandbox de desenvolupament va fallar
abans d'adquirir el lock local, amb `identity_verified=false`; no va arribar
a contactar cap càmera. El preflight físic anterior és l'únic executat un cop
autoritzat el lock.

## Verificació de programari

- controlador: 466 proves;
- GUI i empaquetat: 72 proves;
- QA mission-first amb inventari deliberadament mal etiquetat: correcta;
- perfil A7RIIIA: validació offline i inclusió obligatòria al bundle;
- bundle macOS 0.4.3: signatura ad hoc correcta, 96 binaris Mach-O sense
  rutes externes, reubicació correcta i 98,3 MiB de payload;
- els hashes del controlador i dels tres perfils coincideixen entre font i
  bundle;
- cap prova física d'aquesta ronda contenia ordres de configuració o captura.

## Pendent físic

Cal posar l'A7III a:

```text
MENU → Setup → USB Connection → PC Remote
```

Quan macOS deixi de mostrar `USB Charger`, s'ha de repetir un únic preflight
de lectura amb les tres càmeres connectades. El gate exigeix per a l'A7III la
sèrie USB `[SÈRIE]`, el model PTP configurat i la sèrie PTP
`[SÈRIE]`. Si qualsevol dada falla, no s'ha de
disparar ni canviar ajustos.
