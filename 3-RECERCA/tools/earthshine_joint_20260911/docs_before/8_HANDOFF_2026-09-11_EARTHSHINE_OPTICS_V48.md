# Handoff — V48 preservada, prova òptica rebutjada — 2026-09-11T17:42:31.901552+00:00

**Producte vigent al disc sense canvis:** `/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors/Earthshine_V48.psb`, SHA `48715be427ebd5ea654eeea746e0a295201f9f0a354e4f5e37fbf40df47443a5`. No hi ha V49 ni nova correcció incorporada. **V48 oberta, document1297 amb canvis NO DESATS observats al final; no s'ha desat ni alterat aquest document en la ronda.** No s'afirma identitat dels píxels vius ni se n'ha fet una còpia nova; inspeccionar i preservar aquest estat abans de construir qualsevol producte posterior. Originals79/140 sense desar i preservats. V46/V47/V48 al disc, fonts88 i caches consumits verificats byte a byte; tres XMP exactes. No es repeteix una porta Photoshop: no hi ha cap PSB nou.

Informe `/Users/USUARI/Downloads/Eclipse 2026/output/earthshine_optics_20260911/RESULTAT.md`. **Represa concreta:** `/Users/USUARI/Downloads/Eclipse 2026/research/tools/earthshine_optics_20260911/REPRESA.md`. Fonts externes i abast: `/Users/USUARI/Downloads/Eclipse 2026/output/earthshine_optics_20260911/FONTS_I_HIPOTESI.md`. Manifest `/Users/USUARI/Downloads/Eclipse 2026/research/tools/earthshine_optics_20260911/delivery_manifest.json`.

## Evidència nova

- A0/A1: perfils de88 captures,48 sectors, només columnes completament vàlides. Sigma curt Vixen1,514px iSony2,143px; FWHM3,57/5,05px. Predicció en altres preses curtes: error mediana0,057/0,087px; el·lipse no aporta guany clar. A partir0,5s no hi ha perfils complets qualificats amb aquest criteri.
- A2: l'error aparentment petit del perfil (aprox1% de la corona) equival a1,04vegades la brillantor interior local alVixen. No n'hi ha prou per una resta precisa del vel ni per provar textura feble.
- B0: inversió gaussiana/Tikhonov de dos HDR de6preses, Vixen2(+12,575…17,915s C2) iVixen5(+74,285…79,625s). Convergeix numèricament i compleix la discrepància de soroll prevista, però crea8.618/6.655píxels negatius a r435–454, mínims−36.098/−14.799 i anells visibles. **Rebutjada.** No retallar els negatius ni amagar-los amb màscara.
- B1 entre fonts Vixen iSony/LROC: 1guany i1pèrdua puntuals (verd5/verd4,40–64px, lineal/asinh) a la font primerenca; cap canvi nominal a la tardana. No recuperació global. B2 està escrit peròNOEXECUTAT: el candidat ja falla fidelitat; capPASS d'injecció.
- B3: en la graella lunar els centres solars canvien entre captures; alinear solarment millora la corona exterior respecte del control contrari de mateixa magnitud, però deixa residus alts a la vora. Residual efectiu mediana~0,06–0,07 interior i8,5–9,4 al llimb. Els desplaçaments calculats inclouen registre heretat i no són moviment físic pur. Fotometria, seeing i mostreig també poden contribuir: no s'ha aïllat una causa única.

## Següent model, encara no implementat

Model directe separat per captura, amb textura lunar compartida i corona en coordenades solars pròpies, ocultació física observada i resposta òptica/sensor. Primer dues èpoques de6preses, mateixos inputs/pesos; prediccions reservades i control de moviment, abans d'ampliar a88 o construir un PSB. Fórmula, rutes i cauteles a REPRESA.md. No repetir la mateixa inversió estàtica només canviant força. No reaplicar desplaçaments del Sol a tota la Lluna ni retornar al registre de vora aparent que perjudicava textura.

L'objectiu global continua actiu; no s'ha recuperat tot l'últim llimb ni l'equivalència DHS. Continuació autònoma autoritzada, pas mesurat i claim nou. Cap fitxer de Claude, Git, maquinari o delegació. Zero processos propis pendents al release.
