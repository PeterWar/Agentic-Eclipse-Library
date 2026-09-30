# Tancament de la ronda nocturna — A7III + AP130

> Supersessió puntual 27-07-2026: ISO 200 va ser una compensació d'última
> hora pels núvols de 2024. El candidat de cel net vigent restaura ISO 100;
> vegeu `30_DECISIO_ISO100_CEL_NET_2026-07-27.md`. La resta d'evidència
> temporal d'aquest tancament es conserva.

Data: 27 de juliol de 2026  
Estat: **arquitectura substitutiva preparada; captures RAW pendents**

## Decisió

No s'ha d'intentar reproduir el 2024 amb quinze canvis d'obturació gphoto
dins de la totalitat. F3 n'ha refutat el pressupost temporal.

La direcció vigent és:

1. conservar l'A7III astromodificada amb l'AP130GTX + QUADCC i ISO 200;
2. conservar `gphoto2 --shell` persistent com a trigger offline;
3. generar la corona amb bràqueting continu nadiu a base `1/30`;
4. provar primer el fallback fix `5 × 3 EV`;
5. si els salts de 3 EV no donen prou solapament, usar l'híbrid agrupat
   `N × 9EV1 → un switch verificat → N × 5EV3`.

El perfil que reconstruïa les 56–61 captures de 2024 queda com a evidència,
amb `timing_qualified=false`, i **no s'ha d'armar**.

## Resultat físic acumulat

| Gate | Producte | Resultat | Abast |
|---|---|---:|---|
| F3 | 15 salts d'obturació | 150/150 funcionals; temps FAIL | zero captures |
| F3B | `1/8000 ↔ 1/30` | 20/20; 6,8 s provisionals per sentit | zero captures |
| F3M | matriu `Single ↔ 9EV1 ↔ 5EV3` | 60/60; 1,4 s provisional per transició | càmera en repòs, zero captures |

F3M va observar l'adopció del mode entre 0,697 i 0,879 s després del commit de
l'ordre. Una auditoria posterior va reconciliar exactament totes les ordres
permeses dels tres runs i va endurir l'eina contra deriva tardana.

En acabar les proves físiques:

- cap run F3/F3B/F3M havia disparat l'obturador;
- l'últim readback directe era `Single Shot` i `1/125`;
- no quedava cap sessió gphoto deliberadament oberta;
- la resta de la ronda es va limitar a codi, perfils, documents i proves
  offline.

## Controlador que queda preparat

La v0.2.3-candidate incorpora:

- una sola ordre per canvi de configuració d'adopció retardada i després
  només readbacks;
- distinció entre sessió PTP sincronitzada i estat físic conegut;
- bloqueig de qualsevol trigger o mutació si una ordre enviada pot continuar
  pendent;
- pressupostos explícits per a la fase prèvia, els readbacks, el jitter del
  planificador i el màxim físicament qualificat d'adopció tardana;
- doble quarantena: lectura iniciada després del límit de l'ordre original
  abans de restaurar i lectura també iniciada després del mateix límit de
  l'ordre de restauració;
- detecció de deriva i un màxim de dues ordres de restauració;
- marcador de commit publicat dins del mateix lock que completa l'escriptura
  física al procés gphoto2;
- parser offline ARW/TIFF i JPEG APP1 Exif;
- postflight dels JPEG amb ordre d'obturació, biaix, ISO i coherència EV;
- cap dependència de xarxa;
- suite offline final: **216/216 proves correctes**.

La primera suite de 207 proves havia quedat verda, però dues auditories
independents van construir contraexemples temporals que podien enganyar la
restauració. El tancament de 216 proves ja inclou regressions per adopció
posterior al timeout, lectures que travessen el límit, oversleep dins del
jitter declarat, excepció immediata post-commit i fallada d'una restauració
després d'haver-se enviat.

Perfils de gate:

- `controller/profiles/lab_a7m3_ap130_1ev9_base_1_30.json`;
- `controller/profiles/lab_a7m3_ap130_3ev5_base_1_30.json`.

Són `CANDIDATE_NOT_PRODUCTION`, exigeixen triple autorització explícita per a
una prova física i no escriuen ISO, obturació ni `capturemode`: aquests
valors s'han de preparar manualment i el preflight només els verifica.

## Punt de represa manual

Abans de la pròxima captura:

1. alimentació fiable, SD UHS-II al Slot 1 i Slot 2 buit;
2. `Still Img. Save Dest. = PC+Camera`;
3. `File Format = RAW & JPEG`;
4. `RAW File Type = Uncompressed`;
5. `RAW+J PC Save Img = JPEG Only`;
6. JPEG petit, qualitat Standard;
7. mode `M`, ISO 200, base `1/30`;
8. `Bracket Order = − → 0 → +`;
9. `Silent Shooting = On`, `Long Exposure NR = Off`, `Auto Review = Off`;
10. focus manual i manifest immutable de la SD abans d'entrar a PC Remote.

Després cal fer, en aquest ordre:

1. un bracket `9 × 1 EV`;
2. un bracket `5 × 3 EV`;
3. sortir de PC Remote i validar els 9 + 5 ARW de la SD;
4. mesurar durada real de cada bracket i activitat de targeta;
5. provar `2 + 2` brackets agrupats: 28 RAW;
6. provar `3 + 3`: 42 RAW;
7. intercalar el switch de mode en la posició real, sota càrrega RAW;
8. fer tres simulacions completes amb alimentació, cable i targeta de camp.

## Criteri de promoció

No hi haurà perfil de producció fins que:

- els JPEG confirmin exactament les dues escales fosc → clar;
- els ARW de la SD siguin íntegres, sense comprimir i de 14 bits;
- 28 i 42 RAW quedin demostrats sense pèrdua ni col·lapse de cua;
- el switch sota càrrega compleixi el seu deadline i restauri estat estable;
- el fallback `5 × 3 EV` s'hagi comparat sobre el Sol amb l'híbrid;
- tres simulacions completes acabin sense intervenció.
