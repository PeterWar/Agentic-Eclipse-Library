# Contracte de temps i degradació del controlador

Data inicial: 25 de juliol de 2026  
Revisió card-only: 26 de juliol de 2026  
Estat: **especificació prèvia al backend de trigger de producció**

> **Actualització 27-07-2026 — A7III + AP130.** La decisió posterior de
> requalificar `gphoto2` per repetir la cadena òptica de 2024 reobre la ruta
> PTP com a candidata. Les prohibicions absolutes de PTP i `set-config`
> d'aquest document descriuen el disseny card-only, però ja no són el
> contracte únic del projecte. F3 ha rebutjat el perfil de quinze setters
> `candidate_a7m3_ap130_2024_choreography.json`; queda només com a evidència.
> La ruta vigent és el bràqueting nadiu descrit a
> `research/22_DISSENY_HDR_NADIU_A7III_AP130.md`, encara no promogut a
> producció.

## Principi

Una fotografia tardana no repara una fotografia perduda. Pot contaminar
l'escala següent, omplir el búfer i fer perdre C3.

Per tant:

> cada acció té un target absolut i un últim instant de commit; si ja ha
> vençut, es salta. Mai no es recupera executant-la immediatament.

Durant C2–C3 el contracte és deliberadament en llaç obert: el sistema pot
provar que ha enviat i alliberat un trigger, però no que la càmera ha escrit
un ARW. Intentar confirmar el fitxer violaria el mateix aïllament de dades
que protegeix la cadència.

## Autoritats

- C2 i C3 corregits pel perfil del limbe són inputs, no constants del codi.
- UTC serveix per preparar i auditar.
- Cada procés converteix una sola vegada UTC a rellotge monotònic.
- Després d'aquesta conversió, un salt del rellotge civil no mou la
  seqüència.
- El supervisor només arma quan els dos canals han confirmat identitat,
  configuració, targeta, bateria, trigger i target temporal futur.

## Aïllament

- un canal de trigger i un watchdog/release independent per cos;
- un lock físic/lògic per número de sèrie;
- una fallada A7III no cancel·la automàticament A7RIIIA;
- una fallada A7RIIIA no cancel·la automàticament A7III;
- cap cos depèn de la sessió PTP de l'altre;
- no hi ha cap sessió PTP oberta entre C2 i C3;
- el supervisor no envia captures: només distribueix targets i recull estat.

## Classes de política

| Política | Quan | Acció |
|---|---|---|
| `fatal_prearm` | identitat, mode, target, SD, bateria, cua o perfil incorrectes abans d'armar | no iniciar aquell cos |
| `skip_late` | el commit del trigger ja ha superat el deadline | registrar i saltar al target absolut següent |
| `abort_body` | identitat perduda, release no confirmat, trigger bloquejat o controlador desconnectat | enviar release físic `best effort` i no iniciar més polsos |
| `degraded_continue` | l'altra cadena o un disparador físic independent continua viu | mantenir la cadena sana; no improvisar reparacions |
| `fatal_system` | autoritat temporal invàlida abans d'iniciar o risc físic comú | no armar cap cos |

`degraded_continue` no significa continuar enviant ordres a una sessió
dubtosa. Significa conservar el producte mínim amb la cadena independent
que encara és fiable.

## Matriu d'errors

| Esdeveniment | Fora de finestra protegida | Dins de finestra protegida |
|---|---|---|
| `set-config` lent | es pot avortar el preparatiu i repetir preflight | impossible per disseny: no hi ha PTP |
| trigger encara no escrit i tard | `skip_late` | `skip_late` |
| trigger escrit després del deadline | release immediat, `abort_body` | release independent, `abort_body` |
| ACK del controlador perdut | un únic intent de resincronització si hi ha marge explícit | cap *catch-up*; watchdog i `abort_body` |
| telemetria de shutter/BLE inesperada | diagnosticar abans d'armar | no prova cap fitxer; mantenir deadlines |
| drenatge PTP | només després de sortir del mode crític | impossible per disseny |
| SD absent/plena/no gravable | `fatal_prearm` | no s'ha d'arribar a aquest estat |
| cable del Mac solt | rearmar només amb preflight complet | controlador local continua o passa a fallback |
| procés supervisor mort | rearmar només amb preflight complet | controlador local completa; release físic |
| una càmera falla | l'altra continua | l'altra continua |

## Finestres protegides

Les amplades exactes es fixaran amb el perfil final, però la semàntica és:

1. pre-C2 i C2: només triggers preconfigurats;
2. totalitat primerenca: triggers absoluts; cap canvi de qualitat/ISO/mode;
3. totalitat central: triggers preconfigurats; zero PTP i zero transferència;
4. pre-C3 i C3: només triggers preconfigurats;
5. post-C3: reconciliació, drenatge, restauració i diagnòstic.

C2–C3 es tracta com una sola zona card-only. No hi ha cap excepció de
drenatge central.

## Contracte d'una acció de captura

Cada acció de producció tindrà obligatòriament:

- `target_utc`;
- `target_monotonic_ns`;
- `commit_deadline_ns`;
- `hold_s`;
- `release_deadline_ns`;
- `expected_images`;
- `phase`;
- `late_policy`;
- identificador únic.

Seqüència:

1. esperar amb rellotge monotònic;
2. adquirir el lock d'escriptura;
3. tornar a comprovar STOP i deadline dins del lock;
4. escriure el press físic/BLE;
5. comptabilitzar el deute només després del commit;
6. alliberar abans de la lease màxima;
7. no esperar cap esdeveniment d'imatge;
8. saltar al target absolut següent.

## Prohibició de *catch-up*

Si un target dels segons 20, 24 i 28 falla i el procés torna al segon 26:

- el target 20 es perd;
- el target 24 es perd;
- no s'executen al segon 26;
- només es prepara el target 28.

Això evita una ràfega tardana i manté C3 protegit.

## Persistència i comprovació

- càmera fora de PC Remote;
- RAW sense comprimir a una SD UHS-II del Slot 1;
- cap JPEG i cap fitxer al Mac;
- la telemetria de shutter/BLE no prova cap ARW;
- la reconciliació exacta es fa després de C3 amb manifest SD;
- no s'apaga ni s'extreu la targeta fins que la llum d'accés s'ha apagat.
- cada SD es tracta com a única còpia fins a obtenir dues còpies verificades
  per hash; no es formata ni es reutilitza abans.

## Requisit encara bloquejant

El controlador PTP actual no satisfà aquest contracte. El backend nou ha de
demostrar:

1. Multi Terminal o Bluetooth dispara el bracket en mode normal;
2. un dispositiu extern limita el temps de pressió independentment del Mac;
3. si mor el supervisor o se'n treu el cable, el dispositiu completa o
   allibera el pols;
4. si falla un cos, l'altre conserva el seu calendari.

Sense aquesta prova no hi ha release de producció, encara que la seqüència
funcioni en condicions normals.

## Criteri de Gate 3

Gate 3 passa només si:

- totes les accions del perfil final tenen deadline;
- `late_policy=skip` supera la prova unitària actual i després una injecció
  de retards en la simulació completa;
- no hi ha *catch-up*;
- una càmera pot morir sense aturar l'altra;
- `abort_body` no inicia més polsos i intenta un release físic;
- el fallback físic ha estat provat;
- una simulació completa de 90 s acaba amb C3 intacte;
- el runbook manual no exigeix diagnòstic durant la totalitat.
