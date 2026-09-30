# El balanç de blancs anava en Auto als dos cossos de missió

8 d'agost de 2026, nit. Troballa sortida de revisar el tutorial de
processament d'Astrofalls que Pere fa servir com a referent per a l'eclipsi.
Els tres PDF no tenen cap secció de captura, però el mètode de barreja HDR que
descriuen imposa requisits a la captura, i un d'ells no es complia.

## Conclusió

**Els dos cossos de missió —A7RIIIA i R6 Mark III— tenien el balanç de blancs
en Automàtic, i cap de les dues checklists físiques el mirava.** L'A7III, que
és el cos de reserva, ja hi anava en manual: els dos cossos Sony no anaven
igual.

Corregit afegint una línia a la checklist física dels dos perfils de missió.
No s'ha tocat cap càmera, cap codi de captura ni cap geometria.

## Per què importa: què demana el mètode de processament

El tutorial insisteix dos cops, i és el pilar de tot el procediment:

- registre i integració, punt 1: cal carregar els RAW a Adobe Camera Raw i
  **no tocar-hi res** —ni reducció de soroll, ni nivells, res—;
- barreja HDR, punt 7: el mètode funciona perquè Camera Raw linealitza el RAW
  i **la lluminositat de qualsevol tros de corona és coherent entre
  exposicions** mentre no toquis res. La barreja no fa cap emmascarament
  pintat a mà: només fa una suma ponderada de les exposicions.

Perquè això valgui, **entre fotogrames només pot canviar l'obturació**. El
balanç de blancs no és una decisió de revelat que es pugui deixar per després:
el fitxer RAW hi guarda els multiplicadors del moment del dispar i Camera Raw
els aplica amb «As Shot». Amb Auto WB, cada esglaó de l'escala d'exposicions
escala el vermell i el blau amb un factor diferent, i la barreja perd
coherència **en color**, no en lluminositat. Amb un balanç fix, els
multiplicadors són idèntics a tots els fotogrames i el problema desapareix.

L'agreujant és que l'automatisme mira una escena que no ha vist mai: corona
sense filtre primer i earthshine després, amb catorze o quinze parades de
diferència entre els extrems de l'escala.

## Evidència

| Comprovació | Resultat |
|---|---|
| Bolcat read-only A7RIIIA `20260808T173224` | `/main/imgsettings/whitebalance` = **Automatic**, `Readonly: 0` |
| EXIF de **29 runs** de l'A7RIIIA, del 6 al 8 d'agost | `WhiteBalance = 0` (Auto) als 29 |
| EXIF dels runs de l'A7III | `WhiteBalance = 1` (manual) |
| Bolcat read-only R6 `20260803T195235` | `whitebalance` = **Auto**, `Readonly: 0`; `colortemperature` = 5200, també escrivible |
| Checklist física de l'A7RIIIA abans d'avui | 15 línies de menú i **cap** de balanç de blancs |
| Correccions d'arrencada declarades de la R6 | M, AF continu off, RAW, CFexpress, targeta, apagada automàtica, NR d'ISO alt off, 1/320, Single, AEB off. **Cap de balanç de blancs** |

El bolcat de l'A7RIIIA és el mateix de 105 camins que va servir per demostrar
que aquest cos no publica cap camí de data ni hora.

## Per què se'ns havia escapat

La checklist de l'A7RIIIA ja caça la resta de la família. Hi ha línia per a
`RAW File Type = Uncompressed`, per a `Long Exposure NR = Off`, per a
`High ISO NR = Off` i fins i tot per al DRO, amb aquesta nota:

> el bolcat del 29-07-2026 va trobar aquest cos amb DRO Auto: es un ajust que
> toca el revelat i el perfil anterior d'aquest cos ni tan sols el mirava.

El balanç de blancs és exactament la mateixa categoria —un ajust que toca el
revelat i que el preflight no vigila— i s'havia colat pel mateix forat que el
DRO, un cop tapat aquell.

## Què s'ha canviat

- `controller/profiles/candidate_a7r3a_300gm_short_checkpointed_1x5_3x9.json`:
  línia nova de `manual_preflight`, just darrere la del DRO. Comprovació
  **només visual**: el preflight d'aquest cos no llegeix ni corregeix el WB.
- `controller/profiles/candidate_r6m3_vsd90ss_cfexpress_cardonly_v1.json`:
  línia nova de `manual_preflight` com a `OPERATOR-ONLY, ALWAYS AT POWER-ON`,
  al costat de la de la reducció de soroll d'exposició llarga, i nota a la
  línia de correccions d'arrencada dient que el WB no hi és a propòsit.

Recomanació operativa: **Daylight**, o una temperatura de color fixa, als dos
cossos. A la R6 hi ha 5200 K disponible i llegible.

## El que NO s'ha fet, i per què

- **No s'ha convertit en correcció d'arrencada de la R6.** A diferència de la
  reducció de soroll d'exposició llarga, en aquest cos libgphoto2 sí que
  publica `whitebalance` i `colortemperature` com a escrivibles, o sigui que
  es podria automatitzar. Seria un canvi al contracte de correccions del
  worker i queda fora de l'encàrrec d'avui. Si algun dia s'hi posa, val la
  mateixa regla que la resta: un sol intent, readback, i que un fracàs net no
  aturi el canal.
- **No s'ha tocat cap càmera.** L'app de Pere estava oberta durant tota la
  feina i, per la regla de `CLAUDE.md` §6, cap altra eina no toca cap càmera
  mentre ho està.
- **No s'ha refet el bundle.** Els dos perfils són inputs del manifest, o sigui
  que el bundle 0.9.0 instal·lat ja no té el mateix SHA que la font viva en
  aquests dos fitxers. La decisió de refer-lo és de Pere.

## Dues observacions estructurals que el tutorial destapa, i que no són defectes

Cap de les dues demana cap canvi ara; queden anotades perquè descriuen on és
prim el material que arribarà al processament.

**L'extrem llarg de l'escala de la R6 té dos fotogrames per esglaó.** Comptant
les 120 captures del perfil materialitzat del run `20260807T181413`:

```
1/2000 x62   1/1000 x4   1/500 x5   1/320 x5   1/250 x4   1/125 x5
1/60   x4    1/30   x5   1/15  x4   1/8   x5   1/4   x4   0,5   x5
1      x4    2      x2   15    x2
```

Quinze velocitats a passos d'1 EV: molt més del que el tutorial demana, que
en fa servir vuit. Però la corona externa —la part més sorollosa, i on el
tutorial fa servir els desenfocaments de màscara més grossos, de 120 i 180
px— surt **només dels dos fotogrames de 2 s i els dos de 15 s**. Apilar-ne
dos dona 1,41x de senyal/soroll. Si algun dia apareix marge de temps en
aquest cos, val més gastar-lo aquí que a mig escala; però un fotograma de
15 s paga 2,20 s de suplement de readiness, o sigui que no és barat.

**Les repeticions d'una mateixa exposició no són consecutives a la R6.** Cada
velocitat surt un cop per passada i les quatre o cinc repeticions queden
escampades per tota la totalitat. El tutorial ho contempla —tot el primer PDF
va d'això, i insisteix que fer servir la Lluna com a referència de registre
està malament— però vol dir que caldrà emmascarar el limbe lunar de cada
bracket. A l'A7RIIIA és al revés i millor: les tríades són ràfegues natives i
els tres fotogrames van a menys d'un segon l'un de l'altre.

## El que el tutorial confirma que ja fem bé

- **RAW no comprimit** a l'A7RIIIA. El comprimit de Sony posteritza justament
  les transicions brutals, que aquí són el limbe lunar i les protuberàncies.
- **Reducció de soroll d'exposició llarga i d'ISO alt apagades** als tres
  cossos.
- **DRO apagat.**
- **`RAW & JPEG` amb JPEG Standard mida S** a l'A7RIIIA. Val la pena **no
  tocar-ho**: l'ARW sencer es queda a la targeta i pel cable només hi baixa un
  JPEG de telemetria de 946 KB. Passar a RAW sol, pensant que s'estalvia
  temps, faria explotar el drenatge, que ara costa 0,57 s per imatge.

## Una consideració d'enquadrament

El PDF d'afilat treballa amb desenfocaments radials i de gir centrats a la
Lluna, i el de barreja HDR avisa que el desenfocament gros de les màscares
—fins a 180 px— ennegreix la vora del fotograma i obliga a retallar. O sigui
que **el Sol ha d'anar centrat i el quadre no s'ha d'omplir**.

A l'A7RIIIA hi ha marge de sobres: amb 3,10 ″/px i un disc de 613 px, l'eix
curt dona uns 4,3 radis solars des del centre fins a la vora. **El del tren de
la R6 no està mesurat al repositori** i, per una estimació ràpida, queda més
just. És una comprovació de camp pendent, no una xifra verificada.

## Fonts

Tutorial d'Astrofalls, tres PDF a
`~/Library/CloudStorage/Dropbox/Pere Guerra/Astrofotografia/Eclipse Solar 2024/Projecte Eclipse/`:
registre i integració de brackets, barreja HDR, i filtres d'afilat. Són
documents de processament, no de captura; tot el que hi ha aquí és una
conseqüència del mètode, no una recomanació explícita seva.
