# Tancament v0.2.6 — marge C3, contrast Claude i gate F3T

> **Actualització posterior:** les tres durades noves i el preset de 98,8 s
> es documenten a
> [Durada d'assaig: mitjana de tres ubicacions](28_DURADA_ASSAIG_MITJANA_3_UBICACIONS_2026-07-27.md).
> Aquest document conserva els recomptes anteriors com a evidència de la
> regressió curta.
>
> **Actualització ISO:** l'ISO 200 de l'ordre de represa va compensar els
> núvols de 2024; el candidat de cel net vigent usa ISO 100 segons
> `30_DECISIO_ISO100_CEL_NET_2026-07-27.md`.

Data: 27-07-2026  
Estat: `CANDIDATE_NOT_PRODUCTION`, `timing_qualified=false`  
Cadena: Sony A7III firmware 4.04 + AP130GTX + QUADCC  
Àmbit: captura offline; postprocessament fora de la ronda.

Entorn local verificat: `gphoto2 2.5.32`, `libgphoto2 2.5.34` i
`libgphoto2_port 0.12.2`.

## Veredicte executiu

La via `gphoto2` és ara un candidat coherent per a l'eclipsi curt, però
encara no està físicament qualificada. La reforma manté una única sessió
PTP, delega les ràfegues al bràqueting nadiu, no transfereix imatges durant
C2–C3 i usa deadlines absoluts: una fase tardana se salta, no arrossega les
següents.

Per a una totalitat de 88,00 s:

- perfil híbrid: **56 RAW**;
- perfil fix: **48 RAW**;
- cap espera exploratòria;
- cap setter repetit si el seu estat queda ambigu;
- cap reintent d'un press que pot haver disparat.

Els dos perfils continuen deliberadament desarmats fins a superar els gates
físics. La disponibilitat de l'A7RIIIA com a sistema independent justifica
una acceptació pràctica pròxima al 95%, però no converteix unes poques
simulacions en una garantia estadística del 95%.

## Millora nova de la v0.2.6

### Problema detectat

Els perfils v0.2.5 ometien correctament el bracket final quan no cabia, però
conservaven els setters de retorn ancorats a `C3−17,55` i `C3−15,95`.
Aquell espai ja no protegia cap captura: era marge desaprofitat.

### Solució

Cada setter pot declarar `timing_if_optional_omitted`. El compilador:

1. resol i audita el calendari obligatori;
2. decideix totes les opcionals abans de qualsevol accés PTP;
3. si l'opcional referenciada s'omet, retima target i deadline pel mateix
   delta;
4. reordena el calendari;
5. torna a auditar dependències, estat, solapaments, deadlines i tots els
   dominis físics.

La decisió és determinista, anterior a l'eclipsi i no muta el JSON del
perfil. No depèn de si una ordre real ha anat ràpid o lent.

### Resultat exacte

| Perfil | Omissió | Retorn a Single | Retorn a 1/8000 | Marge recuperat |
|---|---:|---:|---:|---:|
| Híbrid | `< 88,42 s` | `C2+62,20` | `C2+63,80` | 8,25 s |
| Fix | `< 92,82 s` | `C2+64,60` | `C2+66,20` | 5,85 s |

Els deadlines es mouen alhora:

- híbrid: `C2+63,75` i `C2+70,80`;
- fix: `C2+66,15` i `C2+73,20`.

Quan l'opcional entra, els setters tornen exactament als targets originals
`C3−17,55` i `C3−15,95`. Els mínims matemàtics no canvien:

- híbrid: 79,72 s;
- fix: 82,12 s.

Aquest marge es conserva de moment com a robustesa abans de C3. Convertir-lo
en més preses només serà raonable després de mesurar el temps físic de
setter, retrigger i escriptura amb la SD definitiva.

## Què queda eliminat de la fallada de 2024

La seqüència crítica de 2024 conserva 56 ARW consecutius, 14 bits i sense
comprimir. No hi ha evidència de fitxers perduts pel buffer. El patró
demostrat és:

- 35–38 RAW/min amb obturació fixa;
- aproximadament 22 RAW/min amb la ladder de setters;
- buits de 30 s i 125 s;
- una operació antiga amb sis sessions/timeouts que suma uns 50,7 s;
- uns 147 s, prop del 55% de la totalitat, consumits en setters, sessions i
  bloquejos.

La v0.2.6 elimina processos `gphoto2` nous per ordre, quinze setters dins la
totalitat, lectures de cua i descàrregues dins C2–C3.

## Contrast amb Claude Fable 5

Es va enviar un resum tècnic sense fitxers a la sessió local ja autenticada.
El veredicte va ser **PASS condicional**:

- l'arquitectura pot ser principal si supera un gate físic net;
- l'ACK PTP no prova per si sol que existeixi el RAW;
- els pressupostos de 8/10/1 s i la cua de 56–65 objectes encara no estan
  caracteritzats físicament;
- les fases han de conservar targets absoluts i «sacrificar, no
  arrossegar» quan una acció arriba tard.

La v0.2.6 ja compleix aquest últim criteri: tots els targets deriven de C2 o
C3 i les captures tolerants usen `late_policy=skip`. El retiming nou també
es resol abans de PTP i es torna a auditar completament.

Claude va estimar una confiança d'enginyeria de 74/100 abans del gate i
aproximadament 90/100 després d'una ronda física neta. No és una probabilitat
estadística ni una certificació.

Dues feines prèvies del pont local continuaven encallades com a `corrent` i
no se n'ha atribuït cap resultat. Les dues consultes OpenRouter autoritzades
—Gemini 3.1 Pro Preview i Kimi K3, ZDR i sense fitxers— van costar en total
aproximadament 0,05107 USD, però el wrapper no va poder interpretar-ne el
contingut; no se n'ha fabricat cap opinió.

## Gate F3T

`controller/tools/qualify_capture_alias_ab.py` compara el camí calent curt
`capture=1/0` amb `/main/actions/capture=1/0`.

Contracte:

- sense `--arm`: només pla JSON, cap càmera;
- armat: una sessió persistent;
- 32, 40 o 48 captures Single, per defecte 40;
- patró ABBA/BAAB equilibrat;
- hold de 120 ms i cadència d'1,25 s;
- cap descàrrega, `wait-event` ni lectura de fitxers;
- RAW exclusivament a SD i JPEG de telemetria pendent;
- cap reintent d'un press ambigu;
- un únic release d'emergència pel path complet i abort;
- firewall de comandes, ledger de commits i resultat atòmic;
- cua inicial zero i recompte final estable i exacte.

F3T decideix si l'àlies curt és temporalment no inferior al path complet.
No demostra el retard físic de l'obturador ni que els RAW existeixin: el
manifest pre/post de la SD és un gate separat i obligatori.

## Ordre de represa física

1. Desbloquejar el Mac i evitar que la sessió gràfica torni a bloquejar-se.
2. Despertar la A7III i deixar `Power Save Start Time = 30 min`.
3. Confirmar `PC Remote`, firmware 4.04, Silent Shooting, ISO 200,
   RAW+JPEG sense comprimir a SD, JPEG Only al PC, ordre de bracket
   `− → 0 → +`, LENR i Auto Review off.
4. Executar `gphoto2 --auto-detect` i copiar el port literal
   `usb:BUS,DEVICE`.
5. Fer F3T amb 40 cicles i conciliar exactament 40 RAW nous a la SD.
6. Qualificar un bracket `5×3` i un `9×1`.
7. Mesurar per separat `retrigger_ready_s`, `config_ready_s` i
   `drain_ready_s`.
8. Fer 2+2, 3+3 i el canvi `9×1 → Single` sota càrrega.
9. Fer cinc híbrids complets de 88 s i un fallback complet, offline, amb la
   SD, bateria, cable i sessió envellida definitius.
10. Assajar pèrdua USB i control manual de la càmera en menys de 10 s.

Només després d'això s'ha de decidir si es baixa algun pressupost i si els
8,25 s recuperats es gasten en preses addicionals o es conserven com a marge
de C3.

## Bloqueig físic d'aquesta ronda

En el darrer intent desatès el Mac constava bloquejat
(`IOConsoleLocked=Yes`, `CGSSessionScreenIsLocked=Yes`) i
`gphoto2 --auto-detect` no enumerava la càmera. No s'ha saltat el lock,
reiniciat USB, matat cap procés ni usat `sudo`. Per tant, aquesta ronda
només tanca programari, perfils, proves i protocol; no inventa cap resultat
físic.

## Estat de verificació

Verificació final:

- suite completa: **281/281**;
- F3T específic: **34/34**;
- `compileall`: correcte;
- generador dels perfils amb `--check`: correcte;
- validació dels perfils híbrid i fix: correcta;
- dry-run híbrid: 56 RAW a 88,00 s i 65 a 88,42 s;
- dry-run fix: 48 RAW a 88,00 s i 53 a 92,82 s;
- pla F3T de 40 cicles: correcte i sense contacte de càmera;
- `git diff --check`: correcte.

Cap d'aquestes proves substitueix la ronda física. Els JSON continuen amb
`timing_qualified=false`.
