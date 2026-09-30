# Durada d'assaig — mitjana corregida de tres ubicacions

Data: 27-07-2026  
Àmbit: durada C2–C3 per a proves de l'A7III + AP130GTX + QUADCC.

## Decisió

La durada habitual dels assajos serà **98,8 s —1 min 38,8 s—**.

Aquesta és la separació sintètica C2→C3, no la vida sencera del procés. Amb
aquest span, els targets van de `C2−20` a `C3+5` —123,8 s— i l'últim
deadline queda a `C3+6,15` —124,95 s des del primer target. El procés
s'engega encara abans per lead, preflight i configuració.

És la mitjana aritmètica dels tres valors `lunar limb corrected` mostrats
pel calculador:

| Coordenada | Totalitat geomètrica | Corregida pel limbe |
|---|---:|---:|
| 40.71934, −0.07962 | 98,4 s | 99,4 s |
| 42.04987, −4.98015 | 98,5 s | 99,7 s |
| 43.60830, −8.18487 | 95,3 s | 97,3 s |

Càlcul autoritatiu en decisegons enters:

`(994 + 997 + 973) / 3 = 988 ds = 98,8 s`

La mitjana geomètrica seria 97,4 s, però no és la que governa els contactes
fotogràfics. Els grans de Baily, l'anell de diamant i l'aparició o
desaparició de fotosfera depenen del perfil real del limbe lunar.

## Precisió i discrepàncies aparents

No s'han recalculat les durades a partir dels C2/C3 visibles perquè aquests
temps i les columnes `LC` ja estan arrodonits per separat:

- el segon punt donaria 99,8 s amb les xifres visibles, però el calculador
  mostra 99,7 s;
- el tercer dona 95,4 s entre els contactes visibles, però l'etiqueta
  geomètrica mostra 95,3 s.

Per això es conserven com a autoritat les durades mostrades directament i es
guarden en decisegons, sense inventar mil·lisegons.

Les fonts i els seus SHA-256 estan inventariats a:

`controller/scenarios/practice_average_three_sites_2026-07-27.json`

Pere ha confirmat que els punts estan ben triats. El Delta de l'Ebre queda
descartat com a ubicació operativa perquè el parc estarà tancat; la seva
captura continua servint només com una de les tres durades de banc rebudes.

## Política de proves

Quatre spans:

| Cas | Durada | Funció |
|---|---:|---|
| Habitual | 98,8 s | Mitjana de les tres ubicacions |
| Curt real | 97,3 s | Punt més exigent dels tres |
| Llarg real | 99,7 s | Punt més permissiu |
| Advers | 88,0 s | Regressió de degradació segura |

Per a un dry-run sintètic:

```bash
/usr/bin/python3 controller/eclipse_capture.py dry-run \
  --profile controller/profiles/candidate_a7m3_ap130_short_hybrid.json \
  --c2-at 2026-08-12T18:28:00Z \
  --c3-at 2026-08-12T18:29:38.800Z \
  --time-scale 0
```

Les hores són deliberadament sintètiques. En producció no s'usa mai la
mitjana: s'introdueixen els C2/C3 corregits pel limbe per a la coordenada
final.

## Impacte sobre la coreografia actual

El generador i el perfil vigent contenen:

- 11 contactes C2 i 12 contactes C3;
- tres brackets obligatoris `5×3 EV`;
- dos brackets obligatoris `9×1 EV`;
- un tercer `9×1 EV` opcional a `C2+67,15 s`.

Per tant:

- nucli obligatori: **56 imatges**;
- màxim amb l'opcional: **65 imatges**;
- llindar exacte actual de l'opcional: **93,37 s**;
- mínim matemàtic actual del nucli híbrid: **84,67 s**;
- a `97,3`, `98,8` i `99,7 s`: **65 imatges**;
- fallback fix a `98,8 s`: **53 imatges**.

A `93,36 s` l'opcional s'omet perquè el slack és `0,490 s`, inferior al
guard de `0,500 s`; a `93,37 s` ja entra. El cas real més curt, `97,3 s`,
conserva `3,93 s` sobre aquest llindar.

Hi ha un únic drenatge dins C2–C3: els 11 JPEG de contacte a `C2+4,90 s`.
Després no es torna a descarregar res fins passat C3. Qualificar el perfil
continua exigint proves físiques tant a `98,8 s` com a `97,3 s`, perquè el
retorn final a Single Shot encara ha de conviure amb l'escriptura dels RAW
al Slot 1.
