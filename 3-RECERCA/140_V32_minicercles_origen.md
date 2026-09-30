# Minicercles residuals — diagnòstic; V32 no produïda

05-09-2026. Petició de Pere: «no els pots treure del tot?». Àmbit: els
filtres NO azimutals 01, 02, 04, 05 i 06. V31 continua sent el lliurable;
no s'ha modificat cap PSB, màscara, capes azimutals, RAW ni run.

**Resultat:** encara no hi ha una correcció validada que elimini tots els
residus conservant el detall. Els pilots següents no són un lliurament V32
i no s'han de promoure automàticament. Això no prova que una correcció
millor sigui impossible; delimita què no ha resolt el problema avui.

## Falta localitzar inequívocament el residu

Pendent de resposta de Pere: són arcs concèntrics centrats en el Sol, o
petites dianes amb centres repartits? Les marques antigues localitzen sectors,
però no identifiquen per si soles el patró residual que encara veu a V31.
No convertir aquesta falta de localització en l'afirmació que tot el gra
visible és el mateix artefacte. No reprendre la hipòtesi de les azimutals.

## Ablacions de la font: revisió independent només de lectura

`detail_review` ha comparat l'ACHF 01 en G amb contrast congelat, finestres
768² i centre analitzat 256², quatre sectors a 2,9 R i quatre a 4,2 R.
Canvis separats: interpolació C2 de ρ als mateixos nodes, i aplicació dels
G corregits d'HDR que ja existeixen a `v29_c03_fix`.

| Zona | C2 respecte de ρ lineal | HDR corregit |
|---|---|---|
| 2,9 R, 4–16 px | canvi del 0,30% de l'RMS original | RMS restant 90,5%, correlació 0,9641 |
| 2,9 R, 16–32 px | canvi de l'1,59% de l'RMS original | RMS restant 84,6%, correlació 0,9532 |
| 4,2 R, 4–64 px | canvi inferior a 2,8e−7 de l'RMS | RMS restant aproximadament 92,64%; correlació ≥0,999986 |

Per tant, ρ C2 no explica el granulat exterior; els offsets HDR hi baixen
l'amplitud gairebé uniformement, conservant la mateixa textura. No s'han
incorporat aquests canvis al producte. Resultats del revisor comunicats a la
tasca; no s'han inventat fitxers d'execució que el revisor no ha desat.

## Resposta del filtre i mapa de resolució

`mask_geometry_review` ha separat dues qüestions:

- Els filtres `x − Gσ(x)` tenen un lòbul negatiu al voltant d'un impuls.
  En un control d'impuls fort amb σ S/N 2,337856, aplicar tanh abans del
  suavitzat dona halo/centre de 48,4%; invertir l'ordre, 2,80%. Aquest control
  no identifica per si mateix les marques de Pere ni una causa de pols.
- A les zones N, S i exterior, A/B Sony no corrobora 8–64 px; els primers
  trams admesos són més amples. L'erosió mínima 3×3 del mapa propaga caps
  fins de finestres veïnes. Era una protecció conservadora del detall,
  però també deixa passar més gra local: no és un error aritmètic.

S'han generat quatre pilots COMPLETS de 01 amb escala, contrast, suport i
mètode H1 congelats (`research/tools/v32/sn_pilots.py`): reproducció original,
mapa sense erosió, canvi d'ordre tanh/SN i combinació dels dos canvis.
La reproducció original coincideix exactament amb el ràster V29: màxim
0 DN16. Els pilots passen H1, però el residu visual continua present.
Canviar només l'ordre pot augmentar el gra local; H1 verd no significa
artefactes eliminats.

Limitacions del pilot de mapa: usa centres NOMINALS 256+384i del rebut i
OpenCV INTER_LINEAR. Els centres geomètrics de les mostres són 255,5+384i.
Una implementació candidata hauria d'usar interpolació d'alta precisió i
revalidar tot el domini; aquest script exploratori no és una recepta final.
Sense erosió, la transferència lineal local a 64 px és ≥0,90244 a les tres
zones, però el bilineal pot superar el cap admès dins d'altres finestres.
Afegir també sigma3 de V31 la baixaria fins a 0,86414 localment. No hi ha
PASS global d'injecció ni autorització per afirmar que conserva tot el detall.

## Reducció de soroll abans del passa-alt

`source_denoise_pilot.py` prova non-local means sobre lnG abans d'ACHF,
amb h igual a 1 i 1,5 vegades un estimador wavelet del soroll; quatre
finestres 768² i vistes centrals 512², més context al llenç sencer.
Mateixos paràmetres posteriors; G sol i H1 omès igualment a les comparacions.

No elimina visualment el patró. L'estimador wavelet no és una variància RAW
calibrada i pot infravalorar soroll correlacionat després del registre.
Aquest resultat no valida augmentar h a cegues, ni classifica tota textura
com a soroll. No hi ha píxels generatius, inpainting ni màscares de marques.

## Fitxers i continuació

- Scripts i rebuts: `research/tools/v32/`.
- Vistes exploratòries: `output/v32_20260905/`; no s'han publicat al Desktop.
- V31 continua intacta i vigent, SHA-256
  `bbbb2b93a49a0e09226b89467754f6364d1c6b929bc147bd34387a1c66d7affe`.
- No s'ha produït V32.psb ni canviat ACTIVE.json o el handoff de producte V31.
- Següent pas útil: identificar un residu concret de V31 amb Pere abans de
  generalitzar cap atenuació. No augmentar el blur per poder dir «del tot».

Els pilots rebutjats no requereixen una porta Photoshop perquè no són PSB
ni es lliuren com a correccions bones. Qualsevol futura correcció candidata
haurà de passar el jutge extern, transferència, integritat i Photoshop.
