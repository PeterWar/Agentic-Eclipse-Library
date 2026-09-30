# Exposició solar filtrada canònica a 10° — 4 d’agost de 2026

## Decisió operativa

Una única referència de missió, sense perfils per ubicació:

| Equip | Filtre | ISO i obturador | Ús |
|---|---|---|---|
| Sony A7RIIIA + FE 300 mm f/2,8 GM | Baader ASTF-120, AstroSolar OD 5,1 | ISO 100, Silent/Electronic, **1/400 s** | fotosfera parcial amb filtre |
| Canon EOS R6 Mark III + Vixen VSD90SS f/5,5 | Baader ASSF100, AstroSolar OD 5,0 | ISO 100, Electronic, **1/320 s** | fotosfera parcial amb filtre |

La referència ambiental és Sol a **10°**, observador a **700 m** i
visibilitat subjectiva **7/10**. No és una entrada adaptativa del programa:
és el cas únic escollit per a l’eclipsi de 2026. La meteorologia continua
sent un risc visible, no un selector de perfil.

Per a una prova de qualificació R6 fora de la missió, l’escala canònica és
**1/500 ×3 → 1/320 ×3 → 1/250 ×3**, sempre a ISO 100, Electronic i amb el
filtre posat. La missió no afegeix aquests nou fotogrames: conserva el sostre
H2 de 20 RAW i les 18 exposicions de totalitat, i usa el centre **1/320** en
les dues úniques fotos parcials filtrades.

## DEMOSTRAT — R6 III, cos i tren exactes

Sèrie local:
`/Users/USUARI/Desktop/Prova pilot/Sol 8-5graus/R6III/572A2512.CR3`
fins a `572A2537.CR3`.

- 26/26 fitxers passen l’inspector CR3 del projecte: contenidor ISO-BMFF
  complet, `CRAW`, RAW complet 6960×4640, model `Canon EOS R6 Mark III` i
  número de cos `[SÈRIE]`; 26 payloads i SHA-256 diferents.
- Durada real: **20:16:34–20:19:02 CEST, 2 min 28 s**. No són 15 minuts.
- L’operador fixa el Sol representatiu a aproximadament **7,3°** i 15 m
  d’altitud. Totes les captures declaren obturador `Electronic`.
- El disc mesura aproximadament 872 píxels de diàmetre al JPEG de 6960×4640,
  coherent amb el VSD90SS a focus natiu; el limbe i les taques són visibles.
- Repetibilitat del `JpgFromRaw` de màxima resolució, percentil 99,9 interior:
  - ISO 100, 1/400: 103,7/255;
  - ISO 100, 1/250 ×4: 145,4–147,6/255;
  - ISO 100, 1/125 ×3: 201,6–202,5/255;
  - ISO 100, 1/40: 250,1/255 i 0,0264 % de píxels amb el canal vermell
    a 254 o més.
- ISO 800, 1/2000 ×3 és exactament equivalent a ISO 100, 1/250 i produeix
  146,0–147,5/255: reciprocitat de guany i obturador pròpia d’aquest cos.
- Hi ha sis ancoratges equivalents a ISO 100, aproximadament 1/320:
  ISO 250, 1/800 ×3 i ISO 1600, 1/5000 ×3. Per tant, **1/320 no és una
  interpolació entre dos valors d’un altre cos**.

Límit honest: macOS reconeix el `CIRAWFilter`, la mida i les metadades de la
R6 III, però el seu decoder actual retorna píxels nuls en renderitzar el
mosaic. El clipping anterior és del `JpgFromRaw`, no una prova del white level
del mosaic. `scientific_raw_verified` continua sent `false`.

## DEMOSTRAT — A7RIIIA, cos i tren exactes

Sèrie local:
`/Users/USUARI/Desktop/Prova pilot/Sol 8-5graus/A7RIIIA/`.

- Tren: ILCE-7RM3A + FE 300 mm f/2,8 GM + ASTF-120 OD 5,1.
- 23 ARW sense comprimir de 14 bits, Sol dins la banda 8–5°, 15 m,
  visibilitat declarada 4/10 i núvol fi ocasional.
- Mesura directa del mosaic, pedestal negre restat, p99,9 interior:
  ISO 100 1/200 = 13,5–15,2 %, 1/80 = 32,5–33,2 %, 1/50 = 48,3–50,0 %;
  ISO 100 1/25 satura inequívocament amb 60.838 píxels RAW a 16.380 o més.
- La sèrie de migdia del mateix cos/tren/filtre situa ISO 100 1/640 a
  93,2–93,5 %, 1/1000 a 58,8–58,9 % i 1/2000 a 29,6 % amb obturador
  electrònic. Això acota el risc de cel excepcionalment transparent.

Per aquest cos, **1/400** és el compromís canònic de missió: és més segur que
1/320 si desapareix l’atenuació dels núvols i continua produint senyal útil a
10°. No es transfereix la xifra 1/320 de la R6. En el programa fixed 9×1 de
90–100 s, el setter i les captures parcials Single anteriors a C1 adopten
1/400. Després de C3, un cop drenada la cua, el cos torna a Single i fa una
única parcial filtrada a 1/400; l’escala sense filtre de C2–C3 no canvia.

## Extrapolació a 10° i 700 m

Amb Kasten–Young,

```text
X(7,3°) = 7,445
X(10°)  = 5,586
P(700 m) / P(15 m) ≈ 0,920
```

Per una extinció plausible `k = 0,15–0,37 mag/airmass`, passar de la sèrie R6
a 10°/700 m guanya aproximadament **0,46–1,13 EV**. La deriva màxima durant
els 2 min 28 s de la sèrie és de l’ordre de **0,2 EV**, no 1,3 EV. La
visibilitat 7/10 no té una conversió fotomètrica universal; queda absorbida
pel marge entre 1/500, 1/320 i 1/250, no per una falsa fórmula precisa.

## Abast i límits de la decisió

- Aquests valors només governen la **fotosfera parcial amb el filtre posat**.
- No canvien les exposicions sense filtre de perles de Baily, anells de
  diamant, cromosfera/protuberàncies, corona o cara lunar.
- No promouen `scientific_raw_verified` de la R6 ni qualifiquen per si sols
  tracking, focus, setters dinàmics, buffer o una cronologia C1–C4 completa.
- Sí que eliminen el deute concret «obturació solar filtrada sense ancoratge»:
  el programa pot mantenir el canal disponible si identifica el cos correcte
  i materialitza aquests valors, mostrant la resta de deutes com a warnings.
- `1/80` no és acceptable com a parcial filtrada R6: ja cau al genoll alt del
  render a 7,3° i perd marge en millorar l’altura/transparència.

## Contrast independent

Claude Opus 5 va confirmar l’escala R6 `1/500–1/320–1/250`, va detectar que
els sis equivalents a 1/320 eren evidència pròpia i, després de rebre els
timestamps correctes, va retirar la seva deriva inicial exagerada: la sèrie
dura 2 min 28 s, no 15 minuts. El segon contrast confirma `1/320` per al cas
de referència 10°/700 m, amb marge fins i tot en el seu escenari brillant.

També va assenyalar correctament que una captura etiquetada C4 pot trobar el
Sol molt per sota de 10° segons els contactes i el lloc. Aquesta decisió no ho
confon amb una predicció: per instrucció operativa s’adopta **un sol cas
canònic de 10°**, sense multiperfil ni compensació automàtica d’airmass. Per
tant, `1/320` a ambdós costats és la veritat operativa del cas escollit, no una
afirmació que l’exposició física sigui òptima a qualsevol altura C1/C4.
