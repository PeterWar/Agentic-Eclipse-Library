# Estat actual

Data d'autoritat: 23-08-2026, després del preflight fail-closed del pilot
Vixen i dels màsters flat posteriors Vixen/Sony.

## ACTUALITZACIÓ 23-08 · PILOT VIXEN FAIL-CLOSED

- El pilot Vixen des dels RAW s'ha aturat correctament abans de fase 2 amb
  estat terminal `BLOCKED_UPSTREAM_GATES`. L'autoritat canònica immutable és
  `/Users/USUARI/Downloads/Eclipse 2026/output/pilot_vixen_ldic_20260823/20260823T140401Z_preflight_canonical_v4/`;
  `STATUS.json` té SHA-256
  `9e849564dabdb5968c6b2cdfe93b02eec1aed343fb485b136a67612da49861ed`.
- La carpeta viva conté 124 CR3, no els 129 declarats al handoff d'entrada.
  Els 68/68 CR3 del manifest explícit existeixen, són únics i cobreixen 15
  exposicions; aquesta és l'entrada efectiva del pilot.
- F0 no passa: el pendent `+1,019` amb `R²=0,981` pertany a Sony, no a Vixen.
  En la Vixen, la palanca radial disponible és només 0,1149 % i l'eix òptic
  no queda identificat independentment amb una sola orientació.
- F1 tampoc passa: RMS de placa 0,424193 px i RMS del vector geomètric
  històric 0,487192 px, tots dos per sobre del límit 0,3 px. El control de
  deriva 0,138859 px cobreix només cinc parelles i no valida els 68 fotogrames,
  el gir ni la placa completa.
- Per tant no s'ha executat LDIC ni s'ha produït cap composició científica.
  El llenç afí diagnòstic 7697×8613 no és producció: falten la inversió radial
  completa i l'època aparent per fotograma.
- La porta següent és obtenir/autoritzar evidència F0 pròpia de la Vixen —o
  reformular explícitament el contracte científic— i, després, construir un
  oracle F1 held-out per fotograma. Només llavors es pot congelar i executar
  F2.
- Informe:
  `/Users/USUARI/Downloads/Eclipse 2026/research/98_PILOT_VIXEN_PREFLIGHT_FAIL_CLOSED_2026-08-23.md`.
  Handoff formal:
  `/Users/USUARI/Downloads/Eclipse 2026/.coordination/HANDOFF_2026-08-23_CODEX_PILOT_VIXEN.md`.
- Seguretat: zero contacte amb càmeres/PTP/GUI/Photoshop i zero mutacions de
  RAW, darks, flats, S6, PSB/TIFF o productes històrics.

## DEMOSTRAT

- Hi ha dos paquets de màsters flat posteriors, lineals i no-clobber, sota
  `/Users/USUARI/Downloads/Eclipse 2026/output/flats_20260822/`: 125/125
  CR3 Vixen i 53/53 ARW Sony únics acceptats. Inclouen FITS RGGB, NPY CFA4,
  cobertura, variàncies, splits, rebuts i hashes; cap S6 ha estat modificat.
- El `FINE_SENSOR` Vixen coincideix amb el PRNU mesurat durant l'eclipsi
  (`r=0,894–0,921`) i millora un null de quatre RAW 1/125 independents. Estat:
  `VALIDATED_COMPONENT_NOT_APPLIED`.
- L'`OPTICAL_RADIAL` Sony coincideix amb el donor òptic S6 a
  `r=0,9999957–0,9999972`, amb p95 del log-ratio 0,16–0,55%. Estat:
  `VALIDATED_COMPONENT_NOT_APPLIED`.
- El radial Vixen era candidat de pilot el 22-08, però el preflight del 23-08
  l'ha bloquejat a F0: manca evidència específica Vixen amb palanca i eix
  identificable. Els fulls 2-D/pols dels dos trens i el PRNU fi Sony continuen
  en quarantena; no hi ha autoritat per aplicar-los.
- La branca experimental Python Druckmüller descoberta per Gemini queda
  preservada i classificada
  `HIGH_PROMISE_BY_PERE_PENDING_CONTROLLED_S6_PILOT`: Pere n'ha provat els
  resultats i diu que **«pinten molt, molt bé»**. Hi ha snapshot verificat de
  51/51 outputs (38 TIFF, 12 JPEG i un JSX) i 72/72 fitxers Antigravity.
- L'entorn `/Users/USUARI/Downloads/eclipse_venv` és real i reproduïble:
  Python 3.9.6 i `sunkit-image 0.5.1`; `mgn` importa des d'`enhance`, mentre
  `nrgf` i `fnrgf` importen des de `radial`. MGN passa un smoke finit 64×64.
- L'auditoria Kimi/Gemini no troba pèrdua ni corrupció d'originals, S6 o PSB
  canònics. Sí que ha corregit claims, provenance i una promoció V4/V4b que
  no feia vinculant G5.11. `CapesTotalsV4b` es conserva com a evidència i
  continua no acceptat.
- La reparació fail-closed final passa 17/17 proves i AST 7/7; el fuzz
  independent confirma ordre/estat complet, G5.10+G5.11 no vacus, hashes vius
  encadenats, visibilitat canònica i no-clobber també al verificador. Vixen S6
  torna a passar 319/319 hashes i Sony S6, 335/335.
- Per ordre de Pere, 106 JPEG de flats —83.361.792 bytes— s'han mogut a
  `/Users/USUARI/.Trash/Flats_JPEG_Eclipse_2026_20260822T190159Z`.
  Queden zero JPEG/JPG a origen, els 230 camins RAW són invariants i la
  Paperera no s'ha buidat.
- `Deprecat` i `No se que fa això aquí` ja no existeixen: tot el contingut
  necessari s'ha reubicat per funció i els dos contenidors van quedar buits.
- La retirada és reversible. La Paperera conserva el lot únic
  `/Users/USUARI/.Trash/Eclipse2026_cleanup_20260822T151257Z`, amb 1.014
  fitxers regulars, dos symlinks que ja eren trencats i 21.809.186.154 bytes
  lògics. La Paperera no s'ha buidat.
- Els sis TIFF de `Corona_HDR_Vixen` que només eren al backup s'han restaurat
  al màster Vixen i verificat per SHA-256. El backup continua intacte.
- Els originals de les arrels canòniques de càmera no han canviat: 572 ARW i
  1.139 CR3, amb el mateix
  fingerprint abans i després,
  `8d1927d8e2bc5247cbccb5f40a97efa0f67620ff6b50efa6c7b52b89718ba843`.
- Els derivats útils ara viuen sota `Derivats/`; els PSB sota les tres famílies
  `Capes Totals`, `Capes interiors` i `Capes exteriors`; el QA de Photoshop és
  a `Documentacio i QA`; APOD és a `Publicacio/APOD`.
- Les rutes vives de les skills i eines reutilitzables afectades per la
  reorganització s'han adaptat. Els rebuts, manifests i rescats històrics no
  s'han reescrit.
- Els workspaces únics CapesTotals V2b/V3b/V3c s'han tret de `/private/tmp` i
  preservat a `Derivats/Vixen/CapesTotals_work/`: 354 fitxers i
  15.742.589.155 bytes, amb inodes i fingerprints invariants.
- La cadena d'astrometria escriu a `Estrelles/_work` i a l'arrel viva
  `Estrelles/`. `Work_2026-08-17` i `Resultats_acceptacio_2026-08-17` queden
  congelats com a evidència i no són destinacions d'escriptura per defecte.
- La passada astromètrica preservada torna a donar 22/22 checks, 0 errors i
  0 absències quan el test s'apunta explícitament a aquells dos directoris.
- No s'ha generat cap JPEG/JPG en aquesta operació. La regla prospectiva és
  `/Users/USUARI/Desktop/Eclipse 2026/IA/output/`.
- El rebut complet és a
  `/Users/USUARI/Downloads/Eclipse 2026/output/cleanup/20260822T151257Z_deprecat_noseque/`.
- L'autoritat material Vixen és
  `/Users/USUARI/Downloads/Eclipse 2026/output/postprocessat_final_20260822/masters/vixen_s6_ACCEPTED/`:
  319/319 entrades del manifest verificades. Els vuit stacks `STABLE` que
  consumeix `vixen_natural_stable_v5.json` són reutilitzables sense recalcular
  els píxels; els seus contractes s'han de resegelar amb els camps S6 actuals.
- L'autoritat material Sony és
  `/Users/USUARI/Downloads/Eclipse 2026/output/postprocessat_final_20260822/masters/sony_s6_ACCEPTED/`:
  335/335 entrades verificades. Els productes independents de `DSC06987` i
  `DSC06993` existeixen i són íntegres; el seu estat literal actual continua
  sent `QUARANTENA`, no `REBUTJAT`.
- Els arcs circulars estan localitzats a
  `composites/sony_cross_train_c_v2`: la capa només consumeix 1/30, 1/4 i 2 s
  del segment C i introdueix salts literals de contribució a 1,2, 1,5 i
  2,0 Rsol. No són estructura coronal.
- L'auditoria tècnica de represa és a
  `Coordinació/AUDITORIA_REPRESA_VIXEN_SONY_2026-08-22.md`.

## FALTA

- La radial Vixen ja no queda pendent d'una simple execució pilot: abans cal
  evidència F0 específica Vixen —o reformulació explícita del contracte— i un
  oracle F1 held-out per fotograma. L'anterior
  `VALIDATED_SESSION_CANDIDATE` no era ni és promoció S6.
- Abans de canviar cap calibració Sony, cal un pilot RAW amb donor contra
  radial exact-body pels mateixos warps. El PRNU fi Sony no supera r≥0,8.
- No s'ha de dividir cap S6 ja registrat: flat i warp no commuten. Qualsevol
  pilot ha de partir dels RAW i escriure en una branca nova.
- Falta reproduir el resultat visual prometedor de Gemini partint només de les
  entrades S6 acceptades. Els seus prototips actuals consumeixen apilats
  històrics, no mantenen les dues Sony de 8 s separades i no tenen rebuts
  G5.10/G5.11/G7.07; són evidència visual, no autoritat material.
- La Paperera encara ocupa espai. Buidar-la faria irreversible aquesta neteja
  i queda fora de l'operació actual.
- `research/tools/apila_hdr4_vixen.py` conserva una dependència anterior a la
  reorganització, `~/Desktop/HDR3`: era una selecció manual concreta de dotze
  CR3 i no hi ha un substitut 1:1 segur. No s'ha redirigit al directori sencer.
- Cinc utilitats antigues de CapesTotals V1 encara referencien un altre
  scratchpad `v5out/ct1` ja desaparegut. No afecten V2b/V3b/V3c ni V4, però
  abans de reutilitzar-les cal regenerar el compost V5 o parametritzar-ne
  l'entrada; no hi ha un substitut literal segur.
- El darrer paquet Codex `eclipse_natural_editable_v3` continua sent un resultat
  tècnic no aprovat estèticament per Pere. Té 6/6 hashes correctes, però no
  consumeix cap Sony de 8 s, conserva la capa cross-train amb fronteres
  radials i no resol el FOV.
- Resta refer la composició visual Vixen+Sony amb les dues Sony útils de 8 s,
  sense anells i amb contrast moderat. Aquesta tasca continua aturada per Pere.
- Abans de compondre falta una decisió explícita de FOV. Sony cobreix més camp
  angular que Vixen; no es pot retallar al canvas Vixen, ampliar, remostrejar
  o aplicar drizzle automàticament.

## ESTAT DE LA IMATGE

- Referència visual exacta de Pere:
  `/Users/USUARI/Downloads/Maqueta de resultat esperat.tif`,
  110.750.130 bytes, SHA-256
  `5d25d4cca0896c04147c75b5b9ad1c0b76a382a00a852fa596371de4c2b69e17`.
  Guia l'aspecte i l'enquadrament; no és autoritat científica ni obliga a
  reproduir-ne els artefactes.
- Objectiu: una corona extensa i detallada semblant a aquesta maqueta, però
  sense artefactes circulars al marge.
- Direcció estètica: natural, poc forçada i amb marge real perquè Pere faci els
  últims retocs a Photoshop.
- Sony 8 s: `DSC06987` i `DSC06993` són contribucions obligatòries; una estrella
  imperfecta amb seguiment solar no les veta. `DSC06990` queda exclosa perquè
  el fotograma sí que va sortir mogut.
- Artefactes: els arcs marcats per Pere provenen de les fronteres radials
  1,2/1,5/2,0 Rsol de la capa Sony cross-train actual.
- FOV: `FALTA DECISIÓ DE FOV` entre conservar el camp Sony i mantenir
  l'enquadrament de la maqueta.
- Detall: la branca Python Druckmüller és la candidata prioritària perquè Pere
  en valora molt positivament les proves. MGN és `DETAIL_CANDIDATE`;
  NRGF/FNRGF són `DIAGNOSTIC_VISUALIZATION_CONTROLS`. Tots s'han de comparar
  sobre el mateix compost lineal acceptat i cap no pot ser `FONT_HDR`.
- Earthshine: ajornat i fora d'abast.
- Situació: treball visual aturat per Pere; no hi ha cap final aprovat.

## SEGÜENT GATE

Quan Pere reprengui la imatge:

1. partir exactament dels dos paquets S6 indexats més amunt i no dels HDR o
   apilats històrics de Desktop;
2. resegelar documentalment els vuit Vixen `STABLE`, sense recalcular-los;
3. materialitzar `DSC06987` i `DSC06993` com dues
   `CONTRIBUCIO_UNICA × CORONA_SOLAR × domini`, amb màscara de validesa i null
   solar; mantenir `DSC06990` rebutjada;
4. obtenir de Pere la decisió de FOV;
5. fer només un pilot 1:1: Vixen, `+06987`, `+06993` i `+ambdues`, amb
   diferències, ablacions i G5.10/G5.11/G7.07;
6. si el compost font passa, comparar sobre els mateixos píxels el control
   sense filtre, MGN com a candidata de detall i NRGF/FNRGF com a controls
   diagnòstics, amb nulls, diferències al 100 %, G6 i absència d'halos/anells;
7. només després, construir un PSB nou no-clobber, editable i amb un únic
   ajust tonal global suau. Pere conserva l'acceptació visual final. No obrir
   encara earthshine.
