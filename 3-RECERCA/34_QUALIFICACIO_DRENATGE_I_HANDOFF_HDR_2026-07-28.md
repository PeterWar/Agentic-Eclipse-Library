# Qualificació del drenatge C2 i handoff HDR — 28-07-2026

## 1. Decisió executiva

El checkpoint format pels onze contactes C2, el drenatge dels JPEG de
telemetria, el desbloqueig de `capturemode`, el canvi real a bracket `5×3`
i la restauració a `Single Shot` ha superat:

- cribratge: warm-up + **3/3**;
- qualificació: warm-up + **10/10**;
- mateix controlador, perfil, eina i política, vinculats per SHA-256.

Això valida aquest **subgate temporal i funcional** de la v0.3.4. No valida
encara el perfil complet de 98,8 s ni prova que els ARW existeixin i siguin
íntegres a la SD. Els dos resultats declaren explícitament
`scientific_raw_verified=false`; el perfil continua
`CANDIDATE_NOT_PRODUCTION` i `timing_qualified=false`.

## 2. Per què el contracte anterior era incorrecte

El criteri antic jutjava l'èxit gairebé només pel temps brut del drenatge:
`<4,70 s`, amb almenys 300 ms fixos abans del target HDR. Les proves físiques
han demostrat que aquest número no representa la dependència real:

1. els onze JPEG poden haver arribat i `d215` ser zero mentre Sony encara
   publica `capturemode` com a temporalment readonly;
2. el final d'una ordre `wait-event-and-download` no coincideix sempre amb
   el moment en què el prompt i les propietats tornen a estar disponibles;
3. el que protegeix la primera captura HDR no és una xifra arbitrària de
   drenatge, sinó que el setter real comenci i sigui adoptat abans dels seus
   deadlines.

El run T015441 va exposar una espera final de 500 ms que va superar el
timeout del prompt. La recuperació va preservar els onze JPEG, la cua zero i
la sessió, però `capturemode` no es va veure writable fins aproximadament
`C2+10,491`, massa tard per al target HDR. La campanya va fallar de manera
segura.

Després de substituir la cua final per polsos de 50 ms, T020211 va mostrar
l'altre cas límit: els onze JPEG i la cua eren correctes, però una mostra va
arribar al límit antic amb el mode encara readonly; la recuperació el va
veure writable a aproximadament `C2+10,071`. Hauria estat plenament útil si
el setter hagués començat immediatament. Això va motivar un handoff explícit,
acotat i auditable, no un simple augment del timeout.

## 3. Contracte físic qualificat

| Element | Contracte v0.3.4 |
|---|---|
| Contactes C2 | 11 triggers a offsets `−8,75…+3,75 s`, cada `1,25 s`, hold `120 ms` |
| Inici del drenatge | `C2+4,80 s` |
| Deute inicial | 11 JPEG |
| Finestres adaptatives | `2 s` amb deute ≥7; `1 s` amb 3–6; `50 ms` amb 1–2 |
| Purga Sony tardana | `50 ms` quan el ledger és complet però `d215>0` |
| Màxim modelat del drenatge | `5,28 s`; elapsed conservat com a telemetria |
| Gates de sortida | 11 JPEG exactes, 0 ARW per USB, `d215=0`, `capturemode` writable |
| Setter HDR nominal | `C2+10,05 s` |
| Handoff flexible | immediat quan acaba la dependència; inici real ≤`C2+10,15 s` |
| Adopció HDR | una sola escriptura a `Bracketing C 3.0 Steps 5 Pictures`, adoptada ≤`C2+11,57 s` |
| Restauració | una sola escriptura i estabilitat verificada a `Single Shot` |
| Catch-up | prohibit |

La tolerància flexible només existeix entre aquest drenatge i
`set_hdr_5ev3`. No relaxa solapaments, captures, altres setters ni deadlines.

## 4. Resultats físics

### Screen T020900

Resultat:
[result.json](../controller/runs/20260728T020900_candidate_a7m3_ap130_short_hybrid_5x3_then_9x1_mid_drain_screen_qualification/result.json)

- warm-up + 3/3 comptades, `all_ok=true`;
- drenatge: mínim `5,073 s`, mediana `5,111677 s`, pitjor `5,176383 s`;
- lateness màxima dels triggers: `3,874 ms`;
- headroom nominal mínim: `73,517 ms`;
- 33 JPEG comptats, 0 ARW per USB, cua final zero;
- setter HDR i restauració correctes a cada mostra;
- bateria de preflight: 58 %, gate de 50 % superat.

### Qualify T021121

Resultat:
[result.json](../controller/runs/20260728T021121_candidate_a7m3_ap130_short_hybrid_5x3_then_9x1_mid_drain_qualify_qualification/result.json)

- warm-up + 10/10 comptades, `all_ok=true`;
- drenatge: mínim `5,046 s`, mediana `5,145644 s`, pitjor `5,256883 s`;
- lateness màxima dels 110 triggers comptats: `4,658 ms`;
- headroom nominal mínim: `−6,971 ms`;
- en aquest cas frontera, el setter real va començar només `6,977 ms` tard,
  dins del límit de 100 ms;
- adopció després del commit: `431–535 ms`; pitjor
  `534,831 ms`, encara amb uns `975 ms` fins al deadline;
- 110 JPEG comptats, 0 ARW per USB, cua final zero;
- 10/10 setters HDR i 10/10 restauracions correctes;
- 1.054 ordres acceptades pel firewall, 0 rebutjades;
- cap sessió contaminada, cap error de cleanup i release final confirmat;
- bateria de preflight: 58 %, gate de 50 % superat.

El headroom negatiu d'una mostra no és una fallada: mesura la diferència
contra el target nominal, mentre que el contracte real permet fins a 100 ms
de handoff i exigeix l'adopció abans de `C2+11,57`. La mostra va complir
ambdós gates amb marge.

## 5. Vinculació criptogràfica

La qualificació referencia el resultat del `screen` i exigeix les empremtes
següents:

```text
controller  0b7684b99094e5f46974d5d75b8a07bf85114c8afe6ddc522f84d3a5cc1c4e6f
profile     2973b3ffdbd3c3d6d47cabf86047e50615fb7e90c12d38e8d67cb06acad8cb2b
tool        e1ac5e7c43d0ba4e312da8c65a1b62b6c0e657f2ff1f98b037489b16154e19c8
screen      f32532f27706c89f8f8456924373c93f75357f8e2492ba4ee8f3f324d6ea889f
```

Qualsevol canvi posterior al controlador, perfil o qualificador trenca
aquesta evidència i obliga a requalificar el subgate.

## 6. Què s'ha provat i què no

Queda provat per a aquesta A7III, firmware 4.04, connexió i configuració:

- timing i recompte dels onze triggers C2;
- recepció exacta dels onze JPEG de telemetria;
- absència d'ARW al bus USB;
- cua Sony final zero;
- desbloqueig funcional de `capturemode`;
- setter HDR real, adopció i restauració;
- funcionament offline i sense ús de xarxa;
- gate de bateria al 50 %, superat amb una lectura estable del 58 %.

No queda provat encara:

- que la SD contingui el nombre esperat d'ARW;
- que siguin full-frame, uncompressed, íntegres, de 14 bits i sense
  artefactes de Silent Shooting;
- la cronologia completa C2→C3 de 98,8 s amb tots els brackets;
- recuperació sota desconnexió, cable defectuós, cold boot, calor o SD
  lenta/plena;
- rendiment amb una altra targeta, cable, ordinador, cos o firmware;
- focus, filtre, exposició i qualitat òptica sota el Sol real.

`0 ARW per USB` demostra només que la ruta JPEG-only al PC funciona; no és
evidència de gravació RAW a la SD.

## 7. Gates següents

1. Manifest immutable de la SD abans i després d'un run controlat; verificar
   recompte, dimensions, compressió, EXIF i integritat dels ARW.
2. Run complet de 98,8 s amb tots els 65 frames previstos i conciliació
   exacta de ledger, JPEG i ARW.
3. Repeticions de cold boot, cable/reconnexió, temperatura i injecció de
   fallades sense ampliar els deadlines crítics.
4. Assaig òptic diürn amb AP130GTX+QUADCC, filtre i focus real.
5. Només després, promoció explícita del perfil i congelació del paquet de
   camp.

La conclusió actual és, per tant: **gphoto2 és viable per al checkpoint més
problemàtic que hem identificat, però el perfil complet encara no és un
release d'eclipsi**.
