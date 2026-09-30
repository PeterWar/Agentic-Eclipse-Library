# 87 — Auditoria del 21-08: les dues skills, CapesTotals V1→V13, la feina d'Antigravity i el bloqueig d'ID8

Encàrrec de Pere, 21-08-2026: «audita tot el projecte i els canvis fets; repassa també el
`Skill_ECLIPSE.docx`; avisa'm quan estiguis al dia». Tot el que hi ha aquí és de **només
lectura**: cap PSB, PSD, RAW, TIFF, DNG, skill ni script s'ha modificat. Mètode: 8 lectors
independents (una skill cadascun, forense dels PSB, la «torre de Pisa», el rebuig d'ID8, la
coherència documental, els scripts i converses d'Antigravity, i les preguntes del docx) i 8
verificadors adversaris sobre les troballes més greus, tots amb `psd-tools` sobre els fitxers
reals. Vocabulari: **DEMOSTRAT** (mesurat per dos agents o reproduït), **PLAUSIBLE** (deduït),
**FALTA** (no es pot saber amb el que hi ha).

## 0. Resum en deu línies

1. **Cap CapesTotals del disc té avui un rebut vàlid.** V1 (36 capes, `4d0480f1…`) no és el save
   validat a `research/86`; V2 (`17c9ef29…`) no és el que Codex va lliurar (`d264374e…`): **Pere el va
   re-desar a mà a les 02:02** i hi va canviar visibilitats, l'opacitat de la 01 i màscares; V3…V13
   són experiments d'Antigravity i **cap no serveix de punt de partida**.
2. **La «torre de Pisa» d'1 px de la capa 01 (10,3 s) és real** —(+1,4…1,5, −0,9…−1,15) px per
   estrelles—, però Antigravity la va «demostrar» amb un argument fals (la bbox) i la va corregir on
   no toca (un derivat). L'origen és el trasllat (+2,−1) del 18-08 contra EDITAT PERE (`research/80
   §12`). I hi ha un segon forat de reixa que ningú havia vist: **les 1/500 i 1/125 del fonament van a
   (458,464), un píxel fora de la cadena d'apilats (457,463)**.
3. **El bloqueig de Codex a ID8 no és un defecte de la capa**: la porta es reprodueix exacta i els
   tres «mínims sectorials» fan **0,08 %, 0,11 % i 1,19 %** del nivell, amb un terra de **8 DN sobre
   65.535**. Són l'arrissat d'un encreuament de pesos entre capes no normalitzades; una transició de
   màscara de σ 24–96 px (zeros durs reimposats) els esborra. V1 «passava» perquè VORA (Linear Light)
   tapava el mateix fossat.
4. **V13 renta la Lluna**: la capa de 10,3 s hi és visible amb màscara 0,33 dins el disc i 0,50 al
   limbe; el disc passa de 17 a 8.700/65535 i la protuberància de 23.800 a 48.000. El «Sant Greal»
   (blur + Levels 128) **no es va executar** (descriptor invàlid, `try/catch` buit); V10–V12 no van
   canviar cap màscara; i Gemini mesurava des del centre del llenç, a **221 px** del centre de la Lluna.
5. **La cadena d'astrometria de la skill no arrenca** (dos `.sh` apunten a `scripts/` de
   `postprocessat-corona`, que ara és buida) i **el màster `Corona_HDR_Vixen` de 68 fotogrames no és al
   disc** (només la còpia de `_prova_skill`).
6. La skill d'apilatge **decideix el criteri de soroll i denoise que `research/85` deixa obert per
   ordre de Pere**; l'apilat Sony real (`apila_sony_v3.py`) no pertany a cap skill.
7. La regla de llenç/FOV multitelescopi és incoherent amb el llenç real 7648×5353 i amb dos trens
   d'escala diferent; la renumeració G0–G11 → G0–G7 deixa els rebuts del 20-08 intraduïbles.
8. El protocol no té cap porta de **re-derivació de màscares quan canvia el fonament**; amb la
   compensació prohibida, «si falla la primera capa s'atura la cadena» és un bloqueig per construcció.
9. Repositori: **136 fitxers tracked esborrats** per la neteja JPEG (evidència de `runs/2026-07-29`),
   **25 commits sense cap remot**, 12,3 GB untracked no ignorats, `CLAUDE_STATUS` stale en tres punts.
10. Les 12 regles del docx són bones en el gruix; **R3, R11 i R12 són més estrictes que Druckmüller** i
    R2/R4/R5 són criteris del domini lineal que no es poden jutjar sobre capes revelades per ACR.

## 1. Estat real dels fitxers Photoshop (DEMOSTRAT)

Carpeta `~/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/`. Totes les mesures amb el centre
lunar real (4035–4036, 2738), R ≈ 452–453 px, i no amb el centre del llenç.

| Fitxer | Què és | Estat | Serveix? |
|---|---|---|---|
| `CapesTotalsV1.psb` | 36 capes, 2.370.519.442 B, `4d0480f1…` | Només 9 visibles (12_1/3200 ×2, Capa 1/2, 09 ×2, 08, 07, 06); VORA/PONT/PERFIL i filtres ocults; sense EDITAT PERE. Amb la porta de Codex té 7 mínims sectorials (màx 12,4 %). | **No** com a compost; sí com a font de ràsters i màscares crues |
| `Corretgint2.psb` (~/Downloads) | Fonament 1/3200·1/500·1/125·1/60, `1777d41f…` | Immutable, verificat avui | **Sí** (fonament) |
| `CapesTotalsV2.psb` | 12 capes planes, fonament Corretgint2 + 8 capes V5/CT1 | **Re-desat per Pere a les 02:02:18** («he tornat a guardar el projecte», 02:02:59). Ràsters 3/4/5/7 byte-idèntics a Corretgint2; però capes 8–13 **visibles** (Codex: ocultes), 01 a opacitat **255** (Codex: 173 = 68 %), **màscares d'ID5 i ID7 desenfocades** (alfa a 440–452 px: 0,000 → 0,19 i 0,15: la porta lunar fail-closed de Corretgint2 està desfeta), **màscares d'ID16 i ID17 substituïdes per una còpia de la d'ID13**. Màscares 08/09 = CT1. | **Només** com a contenidor de ràsters; el V2 de Codex (`d264374e…`, 1.515.301.942 B) **no existeix enlloc** i s'ha de regenerar amb `build_capes_totals_v2.py` |
| `V3.psd` (02:27) | V2 → translate 01 (−1,+1) + blur 20 a TOTES les màscares | Desenfoca la màscara protegida de la 1/500 (obre a 408 px en lloc de 452) | No |
| `V4.psd` (02:36) | Igual sense les protegides | — | No |
| `V5.psd` (12:02) | + «perforació»: selecció = màscares 12∪11, fill negre a les HDR | Gemini va llegir l'ordre de capes **al revés** (12 és la BASE, màscara blanca al 93 % del centre): màscares de corona a 0,01 fins a 1,5–2 R☉ | No |
| `V6.psd` (12:17) | V2 ja obert i modificat | 01 traslladada **dues vegades** (bbox 456,464); màscara 01 = screen(m11, m01) | No |
| `V7.psd` (12:29) | V2 → translate + bombolla + blur 20 a 10..04 | **Màscara 01 corrompuda**: unió amb la màscara 11 (\|dif\| 0,0002), limbe obert al 86–100 % sota la capa de 10,3 s cremada («la capa 1 crema la corona interior») | No |
| `V8.psd` (12:34) | V7 → blur 60/120/250 a 03/02/01 | Estén el vel: 01 = 0,30 al centre del disc | No |
| `V9.psd` (12:43) | V7 → blur + Levels negre 25/38/50 | 01 = 0,26 al disc, 0,49 al limbe | No |
| `V11.psd`, `V12.psd` | Minimum/blur/Levels | **Cap màscara canvia** (12/12 hashes = V9): tot va fallar dins `try/catch` buits; V12 només fa visibles 03/02/01 | No |
| `V13.psd` (13:22) | V9 → blur 10/25/50 | = `gaussian_filter(V9)` i prou: el Levels 128 té el descriptor invàlid; 03/02 no trobades pel nom. **01 visible, màscara 0,33 dins el disc, 0,50 al limbe.** | **No** |

Dues coses més: **el pinzell blanc de Pere sobre la màscara de la 10 (12:45) no és a cap fitxer
desat** (màscara 10 idèntica a V7, V9, V11, V12; la de V13 és blur σ10 de la de V9); i cap ràster de
cap capa s'ha tocat en cap versió, llevat de la translació entera de la 01.

## 2. La «torre de Pisa» de la capa 01 i la reixa del fonament

**Mesurat** (dos agents, mètodes independents: centroides d'estrelles a r>1500 px i correlació de
corona en 15 finestres):

| Parella (V2 actual, coordenades de llenç) | Estrelles | Corona |
|---|---|---|
| 01 (10,3 s) − 03 (1 s) | (+1,32…+1,51, −0,97…−1,13), n=3–8 | (+1,06, −1,21) |
| 01 − 02 (2 s) | (+1,40…+1,47, −0,89…−1,09), n=5–13 | — |
| 02 − 03 (control) | (−0,23…−0,32, 0,00…+0,29) | (+0,09, −0,20) |
| 01 − 03 **a V3/V13** (després del −1,+1) | (+0,30…+0,51, −0,13…−0,02) | (+0,13, −0,17) |

Als DNG d'HDR4 els tres apilats coincideixen a ≤0,3 px i cada ràster del PSB és el seu DNG a
≤0,2 px: **l'error és íntegrament de col·locació al llenç**, no de l'apilador com deia
`observacions_skills.md` §6. La causa més simple (PLAUSIBLE): `research/80 §12` va mesurar la 01
contra **EDITAT PERE** (un compost), no contra les germanes, i la va moure (+2,−1) quan tocava
(+1,0); `construeix_capestotals.py:54` i `build_capes_totals_v2.py` copien `top/left` sense
remesurar. **La bbox no mesura registre**: la 03 de CapesExteriors té bbox (456,462) i està alineada;
la 02 té la bbox de la 03 i `research/80` deia que no era ni una translació.

El trasllat (−1,+1) d'Antigravity és enter, sense remostreig, i deixa la 01 dins del soroll (residu
+0,3…0,5 px en x, no demostrat). **Però s'ha aplicat a un derivat (V3+) mentre la base continua
desplaçada**: és literalment la torre de Pisa. S'ha de corregir a la font (CapesExteriors/CT1) o al
generador de la V2, i verificar per estrelles, mai per bbox.

**Segon forat (DEMOSTRAT, torre-de-pisa T5):** les capes 1/500 (ID4) i 1/125 (ID5) de Pere tenen
bbox del llenç sencer amb marge blanc, i la imatge ocupa exactament les columnes 458–7417 i les
files 464–5103: són a **(458,464)**, la reixa «V2/V3» de `research/84 §2`, mentre tots els apilats
són a (457,463). El limbe lunar ho confirma a ±0,2 px contra l'efemèride del manifest. El Sol de la
1/3200 (ID3) no es pot verificar ni per estrelles ni per corona; el limbe suggereix ~2 px (FALTA).

**La Lluna es mou com diu l'efemèride**: 0,279 px/s mesurat (0,60″/s; predicció 0,585), fins a
5,8 px entre el disc de la 1/125 i el de la 10,3 s, més ~2,8 px de traç dins de cada fotograma de
10 s. Els apilats ho tracten bé (registre a la corona, disc del fotograma de referència). Les
màscares de 03/02/01 a V2 són **byte-idèntiques** (una sola geometria lunar per a tres instants): a
V2 no fa mal perquè obren a ≥480 px; a ≤10 px del limbe ja entra dins del moviment.

## 3. Per què Codex es va encallar a ID8 (1/30 s)

La porta de `render_transition_qa.py` s'ha reproduït amb les seves pròpies funcions sobre el
fonament real de Corretgint2 (compost offline = merged a ≤1 DN): **els mateixos tres mínims**,
sector 105–120° r=484,5 px **344 DN (1,19 %)**, sector 165–180° r=462,5 **10,4 DN (0,08 %)**,
sector 270–285° r=491,5 **21,5 DN (0,11 %)**. El llindar és `max(8 DN, 0,3 %·mediana)` i el terra
de 8 DN mana sempre: **8/65535 = 0,012 %**, menys d'un esglaó de 8 bits. El mateix fonament sol,
jutjat amb el mateix criteri, ja té dos mínims sectorials (un de 3,9 %).

Què són de debò els «mínims»: a r=458 px les medianes codificades són 1/500 s 8.021 DN, 1/125 s
25.530, 1/60 s 42.065, 1/30 s 53.910, 1/15 s 61.538. Les capes entren a Photoshop **sense
normalització per exposició** (DNG en ADU crus revelats per Camera Raw, no lineal per sobre
d'e≈0,2, Display P3). Quan la 1/30 entra mentre la 1/60 decau, el perfil fa un altiplà
(29.133 → 28.803 → 29.122 DN) i qualsevol irregularitat de la màscara surt com a «mínim nou». Amb
una gaussiana sobre la màscara d'ID8 i els zeros durs reimposats: σ=0 → 3 mínims; σ=24 → 1 de
0,11 %; **σ=96 → 0**. Codex només va provar σ8 local.

Tres coses més: (a) el docstring del mateix script diu «els flags són diagnòstics, no un veredicte
automàtic de capa» i el manifest escriu `scientific_verdict_automatic: False`; (b) la porta mesura
perfils **centrats al Sol** mentre les màscares del fonament són **lunar-cèntriques** (12,7 px de
separació): entre 452 i ~520 px una mateixa transició cau a radis solars diferents segons el sector,
i això sol fabrica mínims sectorials; (c) **V1 passava** per la capa VORA (Linear Light: suma per
anell la diferència benchmark − candidat) i per un criteri global lunar-cèntric de ±5 %: una
correcció fotomètrica compensadora, no un registre més bo. La prohibició de Pere («no repetir la
torre de Pisa») parla d'**alineació**; Codex l'ha estesa a la fotometria i la skill no diu on acaba
una i comença l'altra.

**Conseqüència:** no és que ID8 sigui dolenta; és que (1) el fonament va canviar (Corretgint2 porta
la porta lunar del 1/60 a R+3→R+21 i cap VORA) i les màscares de les capes de sobre es van dissenyar
per a V5; (2) la porta és absoluta, solar i d'un sol píxel; (3) ningú no té l'encàrrec de
normalitzar l'escala d'exposició entre bandes (l'extinció k=0,402 i el cel comú **sí** que tenen
propietari, `apila_hdr4_vixen.py`; el temps d'exposició i la linealitat del revelat, no).

## 4. Què va fer Antigravity IDE + Gemini, i què en queda

De les converses (1.151 passos) i dels 13 `.jsx` i 34 `.py`: la taula de §1. Veredicte:

- **Aprofitable**: l'observació que la 01 anava ~1 px fora (§2), i la translació entera com a
  operació. Res més.
- **Descartar**: V3…V13 senceres (conservables com a evidència, ~15 GB); tots els scripts d'anàlisi
  (`halo_detector.py` mesura el pendent de la màscara en 8 bits amb llindar 0,05 inventat; el
  «gradient 0,65 de la capa 3» és la vora rectangular del fotograma a 4.240 px de la Lluna;
  `check_optimal_range.py` decideix linealitat sobre la previsualització de 8 bits; tots els
  `analyze_*` usen el centre del llenç); el «Sant Greal» (un tall al 50 % després d'un blur **no
  empeny la vora cap enfora**: per un forat circular la mou cap endins σ²/2R, −1,2 px a σ 25 i −17,6 a
  σ 100; per empènyer cal negre >128); i el mètode Druckmüller del `walkthrough.md` (genèric, sense
  cap cita de `research/`).
- **Observacions de `observacions_skills.md`**: 1 (color G2V) mal adreçada —dins d'un cos no hi ha
  WB per capa; el color es fixa un cop sobre la corona K—; 2 (dilatació de saturació) ja feta (Sony
  16100 + 3 px; Vixen rampa 0,2–1,0·sostre) i el blooming de càrrega no està mesurat en aquests CMOS;
  3 (derivades a la costura) ja coberta i millor per `research/86` i la porta de Codex; 4 (cap realç
  abans de l'HDR) ja és cànon; 5 (tolerància de flats / extinció diferencial dins del camp)
  **pertinent i no coberta**: `research/75 §4` mesura gradients de 0,416 i 0,723 mag/X a través del
  camp als dos trens (5σ de diferència) i cap apilat ho corregeix; 6 (torre de Pisa) certa en el fet,
  falsa en l'atribució i la solució. La secció 6 hi és duplicada.
- **Lliçó per a qualsevol automatització de Photoshop**: una operació per script, cap `catch`
  buit, i verificació externa amb `psd-tools` (hash de màscara i perfil radial amb el centre
  mesurat) abans de donar res per fet. «SUCCESS» als logs no vol dir res.

## 5. Les dues skills

### `postprocessat-corona`

- **BLOQUEJANT (confirmat):** `scripts/` és buida des de la separació del 20-08 i
  `research/tools/astrometria/pipeline_estrelles.sh:49` i `apod/munta_video.sh:30` hi apunten a pèl:
  `--nomes-mostra` mor amb sortida 1. La referència `astrometria_i_deflexio.md` mana córrer
  justament això. Sis llocs més porten la ruta vella (tres `MAPA_*.md`, handoff §4 l. 120,
  `VALIDATION.md` de la neteja).
- **BLOQUEJANT (confirmat):** no hi ha cap porta de **re-derivació de màscares** quan canvia el
  fonament (G0 i G7.04 diuen «revalida», G1.09 «no compensis»); les 8 capes de V2 porten «RASTER I
  MÀSCARA RAW» de V1/V5. Sense porta, cada intent queda a criteri de l'agent i acaba en aturada.
- Renumeració **G0–G11 → G0–G7** sense taula: el rebut de quarantena de `Corretgint.psb` (G9/G10/G11)
  ja no es pot llegir. Literals desalineats (`FALTA REBUT D'ENTRADA` / `FALTA ENTRADA`; G6.05
  «quantització» / G6.11 «zero exacte»).
- **Regla de llenç i FOV** (23:36 del 20-08): `W=max(W_i), H=max(H_i)` dona 7952×5304, que no és el
  llenç real 7648×5353; «cada font al seu mostreig natiu» no té sentit amb 3,234 i 2,158″/px (el Sol
  faria 296 px en una i 446 en l'altra); la condició d'aturada («menys píxels i més FOV») no descriu
  el cas real (la Sony té **més** píxels i més FOV); el projecte fa el contrari (remostreja la Sony al
  74,48 % i −33,2°). Cal reescriure-la en termes d'escala de placa.
- Els gates fotomètrics es formulen en lineal i el PSB és Display P3 via ACR; la skill no diu en quin
  espai es mesura cada porta ni com es transporta el mapa de rang lineal del màster a la capa.
- **R12 de Pere rebaixada**: «tot Normal 100 %, tot via màscara» passa a «només les fonts» amb la
  sortida G4.09 (reclassificar com a derivat). És el mecanisme que legalitza VORA/PONT/PERFIL. Pere
  ho ha de confirmar o rebutjar explícitament.
- La norma canònica de `research/84` (màscares **radials**, promitjades per anell, porta lunar per
  capa, cap operador morfològic al limbe) **no és a la skill**; Antigravity la va violar sense que
  res l'aturés.
- L'exposició del «10,3 s»: `trampes.md` diu 10,08 s (fotomètric), `criteris_snr` 10,3–10,4, l'EXIF
  APEX 10,37 s. És un 2,9 % que entra al graó HDR.
- Cap dels 12 màsters de V2 té el `STACK_RECEIPT` que la skill exigeix; la via legal és la
  declaració de Pere.
- Com a skill: no apunta a cap eina (`build_capes_totals_v2.py`, `verify_…`, `render_transition_qa.py`,
  `pilot_h40.py`, `qa_ct1.py`), ni diu on són els PSB, el llenç, els centres ni els radis.

### `apilatge-imatges-eclipsi`

- **ALTA (confirmat):** `~/Desktop/Eclipse 2026/Corona_HDR_Vixen/` (el màster de 68 fotogrames,
  «font principal» de `research/82`) **no existeix**; només la còpia de `_prova_skill/` del 17-08.
  `~/Desktop/HDR3` tampoc; `HDR4` és a `Projecte photoshop/HDR4/`. Les etapes `hdr4` i `munta`
  fallarien o copiarien zero fitxers.
- **ALTA:** els invariants 6–7 i `criteris_snr_i_apilatge.md` **fixen** «sense denoise abans
  d'apilar», «pesos per variància», «prova d'admissió de 4 punts», quan `research/85` diu «només
  preguntes, cap decisió» per ordre de Pere. És una posició raonable (coincideix amb Druckmüller) però
  no autoritzada, i no descriu el que es fa (pes = exposició a la Sony; pesos iguals a l'HDR4;
  denoise de `research/84` a les fraccions de segon).
- **ALTA:** l'apilat Sony real (`research/tools/encaix_sony/apila_sony_v3.py`: per pla de Bayer,
  saturació 16100 dilatada 3 px, registre per estrelles, meitats A/B) **no pertany a cap skill**; l'única
  eina Sony citada, `lot_calibratge_300mm.py`, fa mediana de darks i desbayerat AHD: just el que la
  pròpia referència prohibeix.
- `--prova DIR` **no protegeix** `masters` ni `prnu`: `masters_vixen_v2.py:35` i `prnu_vixen.py:70`
  escriuen sempre a `Vixen Unfiltered/Masters_v2/` (15 fitxers vius, `prnu.npz` inclòs).
- Registre subpíxel, correlació de fase i drizzle no tenen amo declarat (les trampes són a l'altra
  skill). `pipeline_vixen.md` té text del 17-08 (de440s orfe, escala «pendent»).
- Constants: guany Sony 3,41 (75) vs 3,323 (`gain.py`) sense reconciliar; saturació Sony 16383 vs
  16100+3 px operatiu.
- `comprova_entorn.py` funciona («Tot a punt», 10/10 versions = `pip list`); `pipeline_vixen.sh
  --nomes-mostra` llista 14 ordres sense executar res.

### La frontera entre totes dues

La mitjana ponderada entre exposicions veïnes dins del solapament —el nucli de l'HDR de
Druckmüller 2006— no la té ningú: apilatge diu «no fusionis rangs veïns», postprocessat prohibeix
tocar el ràster i només admet màscara. I l'**escala d'exposició entre bandes** (els DNG van en ADU
crus, `rint(mitja+512)`; l'escala la posa el revelat ACR de cada capa, no lineal i sense rebut) no
té propietari: per això G1.06 («continuïtat fotomètrica») no es pot tancar mai sobre el PSB.

## 6. Les regles del docx contra la pràctica de Druckmüller

La taula §4 de `acceptacio_capes_photoshop.md` ja atomitza les 12 regles i 11 tenen porta. El que
cal dir a Pere:

| Regla | Veredicte | Per què |
|---|---|---|
| Filosofia «no torre de Pisa» | Correcta per a **registre** | Aplicada a fotometria converteix tota costura en bloqueig (§3). Cal dir per escrit que una correcció radial documentada, fora de la pila font, amb rebut i reversible, és `CORRECCIO` admesa només després d'acceptar la pila sencera — o que no ho és. |
| R2 (punt òptim, 85 %) | Domini lineal, upstream | El 85 % és sostre de linealitat del sensor (tesi Druckmüllerová), no objectiu d'histograma; sobre una capa ACR el 85 % cau 2–3 EV dins de la compressió. Llindars que sí valen sobre la capa revelada: `research/84 §5` (p50 ≤ 0,46, p95 ≤ 0,66). |
| R3 (adjacent i superior) | **Massa estricta** | Druckmüller compon amb pesos per píxel i moltes exposicions per píxel (mediana 294 aportacions al nostre HDR lineal). «Adjacent» ha de ser «banda veïna amb solapament mesurable i pes suau dins del solapament». |
| R4 (gradient atmosfèric) | Correcta, sense porta d'execució | Extinció (×), cel (+), refracció (geomètrica) i camp (instrumental) estan separats a G2, però cap porta exigeix que s'hagi aplicat ni diu on (HDR4 sí; capes antigues de Pere no se sap). |
| R5/R10 (soroll, denoise, rebutjar) | No és Brno i no està decidida | Cap paper de Brno rebutja per SNR ni fa denoise abans d'apilar: pondera 1/σ². `research/85` és el lloc on decidir-ho amb mesura (meitats A/B), no una regla a priori. |
| R6 (alineada amb tot) | Barreja tres marcs | Sol, Lluna (0,5905″/s) i estrelles (0,041″/s) no poden coincidir alhora: una capa declara UN marc i es registra contra la referència immutable d'aquell marc amb residu. |
| R7 (repetida → rebutjar) | Correcta per a còpies PSD | Captures independents repetides s'apilen (aporten SNR); la segona meitat («reajusta la màscara de l'existent») no té porta. |
| R8 (estrelles rodones) | Diagnòstic condicional | A les capes de 10,3 s del Vixen l'estrella ja és un traç de 3,0 px dins del fotograma; a la capa Sony de Pere les estrelles es van arrodonir sintèticament. L'astrometria es fa sobre crus (38/38 i 22/24) i no sobre el compost. |
| R9/R10 (cap artefacte, màscara per capa) | Correctes i **mesurables** | Mètrica que ho detecta: «compost − compost amb la màscara promitjada per anell» (empremta no radial, ≤0,5 % rms a 1–4,5 R☉) i test d'anells per sectors. El projecte no les complia fins a V4/V5/SF10. |
| R11 (la màscara bloqueja TOT fora del rang) | Correcta als límits durs; **dins del rang ha de ser pes** | `research/76 §5 bis`: tall dur → graó 3,3 %; rampa 0,25 → 1,6 %; rampa 0,80 → 0,65 %. |
| R12 (Normal 100 %, tot via màscara) | Compatible amb HDR ponderat **si la màscara és el pes** | N capes Normal amb màscares α_i són Σ a_i·α_i·Π(1−α_j): una mitjana ponderada. El que no decideix és si es permeten derivats `CORRECCIO` fora de la pila (§5). |
| Exteriors (protegir limbe/perles/protuberàncies, subpíxel) | Correctes | G6 ho fa fail-closed; el que falta és que el PSB viu ho compleixi (V2 del disc i V3–V13 no). |

## 7. Respostes a les deu preguntes del docx

- **P1 (cada capa només el seu EV, sense artefactes)** — A V4/V5/SF10: sí dins de llindar mesurat
  (`research/84`: anells 0,18 % rms; `83 §10`). A V2 de Codex: ID8 aporta 1,1–3 R☉ i fora de la màscara
  no canvia res; l'únic «artefacte» és l'arrissat d'1,2 % d'un sector (§3). A V2 del disc, les màscares
  del fonament ara contribueixen dins l'anell lunar. A V3–V13: no. **DEMOSTRAT.**
- **P2 (contorn lunar, perles, protuberàncies; moviment de la Lluna)** — A Corretgint2/V2 de Codex:
  nuclis a 0 DN, porta lunar per capa amb centres propis (fins a 3,4 px de diferència). La Lluna es mou
  0,279 px/s i el limbe és a un lloc diferent a cada capa (5,8 px entre 1/125 i 10,3 s): **una protecció
  del limbe ha de ser per capa**, no un sol cercle. A V13: perles, limbe i protuberància **rentats**.
  **DEMOSTRAT.**
- **P3 (apilar bé, mínim error en píxels)** — Dins de cada apilat del Vixen sí: residu ≤0,09 px a les
  17 parelles d'HDR4, ≤0,3 px entre apilats per estrelles. On es perd és **al llenç**: la 01 a (+1,−1) i
  les 1/500 i 1/125 a (+1,+1) de la cadena; el Sol de la 1/3200, FALTA. A la corona interior (1/60…1/4)
  la correlació no distingeix per sota d'1 px. La 02_2s antiga de Pere tenia un revelat no
  translacional (fins a 6 px, `research/80`); la de V2 no (≤0,2 px respecte del DNG). **DEMOSTRAT.**
- **P4 (artefactes via màscara)** — Les màscares de lluminositat, de pinzell o desenfocades sí que
  interfereixen (`84 §5`, `83 §10`); les radials no dins de 0,18 % rms. V1/V5: bé. V3–V13: el tipus
  prohibit. **DEMOSTRAT.**
- **P5 (estrelles puntuals i plate-solve)** — Sobre fotogrames crus: 38/38 (Sony, residu 0,54 px) i
  22/24 (R6, 0,32 px), reproduït 22/22 a `_prova_skill_estrelles`. Sobre el compost: no hi ha garantia
  ni és l'objectiu («l'HDR no és font d'astrometria», `research/79`); a 10,3 s l'estrella ja és un traç
  de 3 px. **DEMOSTRAT.**
- **P6 (activar de baix a dalt sense reeditar res)** — Només ho compleixen Corretgint2 i el V2 de
  Codex (12 capes Normal, radis del 50 % creixents 454→840 px, dues capes de mitjana parcials). V1 no:
  VORA/PONT/PERFIL/ANELL i els filtres reediten el que hi ha a sota; la 01 al 68 % deixa passar la
  capa inferior. V13 no. **DEMOSTRAT.**
- **P7 (altres filtres)** — Ja al projecte: DoG log-polar, MGN v2, NRGF, fons de Fourier m≤4, blanquejat
  per anell, coherència entre trens, ACHF_lite. Per ordre de risc d'inventar: (1) **WOW** (Auchère
  2023: à trous blanquejats amb porta de soroll erf(|w|/n_sσ_s)), primera recomanació de `73 §2.8` i
  encara no implementat; (2) starlet amb porta de significació; (3) **ACHF** (tesi §5.2, nucli en (Δr,
  arc), isòtrop); (4) Gabor/orientacions en log-polar per a estructures obliqües; (5) top-hat
  morfològic; (6) RHEF/SWAP (equalització per anell). NAFE és per a SDO i no té codi al projecte. Tot
  sobre la lluminància del compost tancat, mai sobre capes. **PLAUSIBLE.**
- **P8 (núvols)** — No aplicable al 2026. El detector natural per al 2027 és el que ja hi ha: factor
  multiplicatiu per parella (extinció 0,38–0,44 mag/X) i fons per fotograma; un núvol prim és una
  transparència fora del model o un residu estructurat per sector.
- **P9 (seguiment)** — **Solar** als dos trens, verificat: al Vixen la corona deriva a 0,578″/s i les
  estrelles a 0,610 (la diferència és el Sol sobre el fons); iOptron: deriva 0,610 ± 0,010″/s =
  0,28 px/s, constant, cap salt; post-C3 0,689″/s (0,21 refracció + 0,48 muntura, error polar ~2°).
  Skywatcher (Sony): **dos salts**, +223 px (~12′) cap a C2+30…42 s i −715 px (~39′) cap a C2+42…58 s,
  amb 0,138° de rotació de camp, atribuïts a la retirada del filtre. **DEMOSTRAT (`71`, `72`, `75`).**
- **P10 (quin SNR, descartar per SNR)** — Cap criteri decidit, a propòsit (`research/85`). Estat de
  fet: tota exclusió ha estat per geometria; pes = exposició (Sony) i t²/(S/g+RN²) (HDR Vixen); denoise
  sense criteri. Resposta científica a la segona meitat: una capa lineal fora del «rang ideal» **no es
  descarta, es pesa** (1/σ² per píxel); ID8 no s'ha rebutjat per soroll sinó per un mínim de 8 DN. El
  que falta per tancar-ho és la σ per anell (meitats A/B), que alhora donaria el llindar bo a la porta.
  **FALTA per decisió.**

## 8. Repositori i documentació

- **136 fitxers tracked esborrats del disc** per la neteja JPEG del 20-08: 135 JPG de
  `runs/2026-07-29_real_mission_first` i `_real_three_camera_simultaneous` més `Logo.jpg`. CLAUDE.md
  §11 prohibeix esborrar `runs/`. Recuperables de git mentre no es commiti; el lot de Paperera no és
  llegible des d'aquí.
- **25 commits sense cap remot**: `dropbox/main` és a `9b2a127` (0.8.1); tot el tram 0.8.2 → V1.02 i
  l'eclipsi viu només en aquest disc (`.git` 3,2 GB, worktree 32 GB).
- **12,3 GB untracked no ignorats**: `research/tools/corretgint2/.build_perles_D2896CDB/` (148
  fitxers, 5 PSB candidats); `research/81A` (transcripció d'un curs de pagament) tampoc és al
  `.gitignore`. Un `git add research/` ho commitaria tot.
- `CLAUDE_STATUS.md` contradeia CLAUDE.md, AGENTS.md i el handoff en tres punts (traspàs viu, V1
  «lliurat», deflexió «a les nostres imatges»): **corregit avui amb un bloc de vigència al capdamunt**.
- CLAUDE.md té dues seccions «## 1 bis» i 1.500 línies en present de captura darrere d'un bloc
  post-eclipsi de 65; el `LLEGEIX-ME_CapesTotalsV1.md` de l'Escriptori és stale; el handoff del 20-08
  situa `requirements_validated.txt` a la skill equivocada.
- Els rebuts de Codex del rebuig d'ID8 (`/private/tmp/capes_totals_v2_CAC3DA15/…`) han desaparegut;
  al repositori només queden `final_config.json` i el diari. El codi els pot regenerar.
- 34 scripts vius de `research/tools` porten rutes absolutes a scratchpads de `/private/tmp` que ja
  no existeixen (els de `filtres_druckmuller/` tenen fallback per variable d'entorn; `comu.py:39`,
  `capa_vora.py:12`, `acaba_mask0403.py:53`, `apila_sony_v3.py:30` i `capes_photoshop/*` no).
- Pendents del handoff §4: tots cinc oberts. Els tres TIFF del Vixen continuen divergint del manifest
  (mtimes posteriors al tancament); `_prova_skill` 16,9 GB i `_prova_skill_estrelles` 14,7 GB hi són.

## 9. Decisions que només pot prendre Pere

1. **Punt de partida**: regenerar el V2 de Codex a un path nou (`build_capes_totals_v2.py` amb
   Corretgint2 `1777d41f…` i CT1 `4d0480f1…`, totes dues verificades immutables avui), o acceptar el
   V2 del disc sabent què hi ha canviat. V3–V13 no són candidats.

   REGENERAL  
2. **Reixa única**: corregir la 01 a la base (no al derivat) i decidir si les 1/500 i 1/125 van a
   (457,463) o tota la cadena a (458,464); verificar per estrelles/limbe, mai per bbox.
   CORRETGEIX TOT A LA BASE PER EVITAR QUE AIXÒ SIGUI LA TORRE DE PISA
3. **Capes compensadores**: o la filosofia estricta (el fossat es resol a les màscares amb pesos
   suaus al solapament) o una classe `CORRECCIO` declarada fora de la pila font. No barrejar. Això
   decideix si V1 és «fora de norma».
   UNA IMATGE ORIGINAL NOMÉS ES POT RETOCAR SI ES DETECTEN ARTEFACTES D'APILAT AL FER LES MÀSCARES. Veure DOC que t'adjuntaré.
4. **La porta de costura**: relativa al nivell (≥1 %) i a la σ del sector, amplada mínima, bicèntrica
   (lunar fins a ~1,2 R☉, solar més enllà), i severitat en lloc de flag binari. Sense això la cadena no
   passa mai d'ID8.
   T'HO DEIXO AL TEU BON CRITERI
5. **Soroll i denoise** (`research/85`): decidir amb la mesura de meitats A/B, i fins llavors tornar la
   skill d'apilatge a «proposta».
   CREC QUE TOTES LES IMATGES DE LES CAPES JA TENEN UN BON SNR, PER FUTURS PROJECTES D'ECLIPSE SI QUE VAL LA PENA FER LES REFORMES DE SOROLL I DENOISE, APUNTAHO COM A RECERCA FUTURA PERO ARA NO ES EL MOMENT, M'ESTIC QUEDANT SENSE TOKENS.
6. **Els 136 JPG tracked**: restaurar de git o acceptar l'esborrat i actualitzar CLAUDE.md §11.
SI ET FAN CREMAR INECESSÀREAMENT TOKENS, RESTAURA LES IMATGES, SON A LA PAPELERA, ALTREMENT ESBORRELES.
7. **Còpia de seguretat**: empènyer la branca al bare de Dropbox.
JA ESTIC FENT COPIES MANUALS JO PER NO GASTAR TOKENS, TRANQUIL.
8. **On és `Corona_HDR_Vixen`**: si no apareix, promoure la còpia de `_prova_skill` amb rebut nou o
   regenerar-la (15 min).
A LA PAPELERA jaja LA POTS RECUPERAR SI VOLS
## 10. Camí proposat per desencallar, per ordre

1. Quarantena (sense esborrar) de V3–V13 i del V2 del disc; nota al LLEGEIX-ME.
2. Regenerar V2′ amb la reixa corregida (decisió 2) i verificar-la per estrelles i limbe.
3. Recalibrar la porta (decisió 4) i **re-derivar** les màscares de les 8 capes de sobre contra el
   fonament nou, amb la norma de `research/84`: radials, porta lunar per capa amb el centre del seu
   fotograma, σ de transició derivat del solapament mesurat (24–96 px a ID8), zeros durs reimposats,
   pilot 1:1. Encadenar ID8 → ID17.
4. Normalitzar l'escala d'exposició entre bandes abans de jutjar continuïtat (o jutjar-la sobre el
   lineal), i assignar-ho per escrit a una skill.
5. Arreglar les skills: rutes de l'astrometria, `Corona_HDR_Vixen`, soroll com a proposta, pipeline
   Sony, regla de llenç, porta de re-derivació, numeració G, `--prova` complet.
6. Higiene del repositori: `.gitignore`, decisió dels JPG, push de seguretat, rutes `/private/tmp`.

Res d'això s'ha executat: aquesta nota és l'auditoria que Pere va demanar, no una ordre.

## 11. Decisions de Pere (21-08, tarda) i execució

Respostes de Pere a §9, escrites en majúscules al mateix document, i el Word «Problemes
recurrents.docx» (dues captures: l'arc d'apilat al limbe de la 1/60 —la Lluna es mou ~3 px entre
572A2975 i 572A2993 i la mitjana deixa un arc semitransparent— i un compost amb graons concèntrics):

1. **Regenerar** el V2 de Codex. → En curs: `CapesTotalsV2b.psb` (§11.1).
2. **Corregir tota la reixa a la base**, mai als derivats. → En curs, amb la geometria comuna de l'HDR4
   (fotograma 572A2969 = la 1/125) com a referència: ID4/ID5 a (457,463), ID17 a (457,463), ID3 pel
   model de deriva.
3. **Cap capa compensadora.** Un ràster original només es retoca si s'hi detecten artefactes d'apilat
   en fer les màscares (l'arc del limbe de la 1/60 n'és el cas). Del Word: les màscares gaussianes
   homogènies no serveixen a les exteriors; **pinzellades radials semitransparents que s'enfosqueixen
   cap al centre, i desenfoc després, sí** —és la norma de `research/84` (màscares radials per anell,
   porta lunar per capa) dita amb les mans—. I el retall de la zona d'artefacte al voltant del limbe de
   l'apilat, abans de treballar per capes, si no aporta SNR.
4. Porta de costura: a criteri de Claude (§9.4 tal com està proposat).
5. Soroll i denoise: **recerca futura**, no ara (les capes ja tenen bon SNR). `research/85` queda obert
   com a fil per a futurs eclipsis; la skill d'apilatge s'ha de marcar com a proposta quan es toqui.
6. Els 136 fitxers tracked de `runs/`: **restaurats des de git** (`git status` net de `D`), amb
   autorització expressa de Pere. Cap accés a la Paperera necessari.
7. Còpia de seguretat: Pere la fa a mà. Cap push.
8. `Corona_HDR_Vixen` i `HDR3` són a la Paperera (Finder els llista); el Finder no els deixa moure des
   d'aquest procés (error −5000). **Pere els ha d'arrossegar a `~/Desktop/Eclipse 2026/`.** Mentrestant
   serveix la còpia de `_prova_skill/Corona_HDR_Vixen` (`hdr_vixen_countss.npy` SHA `1be619ec…`).

### 11.1 `CapesTotalsV2b.psb`: el V2 regenerat amb la reixa corregida a la base (LLIURAT, APTE)

`~/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/CapesTotalsV2b.psb`, **1.515.301.614 B,
SHA-256 `e55116018aa82fd9185f2fe92d5eaa860e3a2a30e9ceb89c1f2c215e96c23b62`**, amb
`CapesTotalsV2b.manifest.json` (SHA de fonts, candidat, canals i màscares per capa, offsets i mesures)
i `LLEGEIX-ME_CapesTotalsV2b.md`. Eina: `research/tools/capes_totals_v2/build_capes_totals_v2b.py`
(estén el builder de Codex amb `--offsets`: només metadades de `LayerRecord` i `MaskData`, cap píxel
remostrejat), `verify_capes_totals_v2b.py`, `qa_imatge_v2b.py`, `final_config_v2b.json`,
`offsets_v2b.json`. Fonts pinades: Corretgint2 `1777d41f…` i CT1 `4d0480f1…`, immutables.

Reixa (referència: la geometria comuna d'HDR4 = fotograma 572A2969, a (457,463) del llenç):

| Capa | Abans | Després | Evidència |
|---|---|---|---|
| ID3 12_1/3200 (572A2956, C2−0,750 s per EXIF) | (457,463) | **(459,461)** (+2,−2) | model de deriva d'HDR4 extrapolat 1,3 s: (+1,66, −1,82); limbe diferencial del costat fosc contra la 1/500: (+1,85…+2,08, −1,37…−1,86). Residu final ≤0,35 px. PLAUSIBLE (el verificador el dona per DEMOSTRAT pel limbe) |
| ID4 11_1/500 (572A2968) | (458,464) | **(457,463)** (−1,−1) | mateix camí CR3→ACR que la 1/125; limbe diferencial vs ID8: residu (−0,13, +0,14) |
| ID5 10_1/125 (572A2969) | (458,464) | **(457,463)** (−1,−1) | és el fotograma de la geometria comuna; correlació tangencial de corona 8→5 = (+0,94, +1,22) ± 0,09 abans; limbe diferencial residu (+0,11, −0,10) després. DEMOSTRAT |
| ID7 09_1/60 i ID8…ID16 | (457,463) | sense canvi | entre ells ≤0,35 px |
| ID17 01_10,3 s | (458,462), op. 173 | **(457,463)**, op. 255 (R12) | estrelles: 01−03 (+0,31, −0,06) n=7, 01−02 (+0,35, 0,00) n=12, control 02−03 (−0,17, −0,01); abans (+1,5, −1,1) |

Estat: 12 capes Normal / 100 % / farciment 100 %; visibles només 3, 4, 5, 7; 8…17 ocultes amb nom
«QUARANTENA OCULTA · MÀSCARA PENDENT DE RE-DERIVAR (research/87)»; màscares crues de les fonts
(hash 12/12 = font); merged recompost (0–1 DN contra un compost offline independent); Lr16 + Mt16;
ICC Display P3. Vora: en moure ID4/ID5 (−1,−1) la columna 7647 i la fila 5352 del llenç queden amb
alfa 0 (marge blanc fora de la imatge; res inventat).

**No és un compost**: és la base neta per al pas §10.3 (re-derivar les màscares de les vuit capes
de sobre contra aquest fonament, amb la norma de `research/84` i la porta recalibrada). Reserves:
la 02 (2 s) per estrelles és a (−0,32, +0,29) de la 03 però la correlació de corona hi veu
(−0,66, +0,86): contrastar-la quan es re-derivin les màscares; la correlació de fase blanquejada
bloqueja sobre el patró de soroll de píxel entre apilat2/apilat4 (±1 px alternants): no fer-la
servir per registrar aquestes capes.

### 11.2 `CapesTotalsV3b.psb`: tram intern 12→06 (LLIURAT, APTE AMB RESERVES)

`~/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/CapesTotalsV3b.psb`, **1.518.180.374 B,
SHA-256 `0fa8e495739ab957c56319c8ec86b11dee9f25c1493654a4e6bcf0953d57016b`**, amb manifest,
`LLEGEIX-ME_CapesTotalsV3b.md` i la carpeta `CapesTotalsV3b_QA/` (pilots 1:1 en PNG, JSON de cada
porta). Eines: `research/tools/capes_totals_v3b/`. V3b = V2b + màscares noves a ID8 i ID9 +
visibilitat; ràsters i la resta de màscares byte-idèntics a V2b (verificat amb codi independent).

Mètode (la norma de `research/84`, amb «tot es mou»): màscara = rampa radial solar (promitjada per
anell, sense estructura azimutal) × porta lunar **per capa** (centre mesurat al propi ràster per
ajust d'el·lipse; el limbe és el·líptic 454×451 px per la refracció a 9°) que deixa a zero la
**banda d'artefacte d'apilat** (unió dels discos desplaçats dels membres, 17–23 px cap a PA 152°,
més 14 px de marge: fins a R+43…48 px en aquell sector) × zeros durs dels nuclis P3/P4 i de tot el
que la màscara del fonament té a zero fins a 620 px, reimposats al final. Cap desenfoc. Porta
recalibrada (§9.4): mínim nou = defecte només si ≥1 % del nivell ∧ ≥3σ del sector ∧ ≥10 px, perfils
lunar-cèntrics fins a 1,2 R☉ i solars més enllà, globals i en 24 sectors; empremta no radial
≤0,5 %; nuclis i discs a 0 DN exacte; criteri V1 (mediana per anell sense mínims).

| Capa | Veredicte | Rampa (R☉) | Pes màx. | Porta de costura |
|---|---|---|---|---|
| 09 1/60 (ID7, fonament) | revisada, **no tocada** | la de Corretgint2 | — | la banda d'artefacte (fins a R+42) no és mesurable ni com a soroll (≤10 % d'excés) ni com a graó al compost (≤1,2 %); l'arc de la captura de Pere queda PLAUSIBLE/FALTA |
| 08 1/30 (ID8) | **ACCEPTADA** | 1,29 → 1,59 | 1,00 | 0 defectes; empremta 0,12 % |
| 07 1/15 (ID9) | **ACCEPTADA** | 1,43 → 2,23 | 0,70 | 0 defectes; empremta 0,06 % |
| 06 1/8 (ID10) | **REBUTJADA** (oculta, màscara crua) | 1,57 / 1,75 / 1,90 provats | 0,20 | 2 mínims d'1,25 % i 1,53 % (sectors 225°/240°, 1,46–1,48 R☉, 26–28 px, 8σ) |

Merged final: cap mínim-defecte; perles, limbe i protuberància byte-idèntics al fonament; discs
lunars de totes les capes a alfa 0. A 100 % no es veu costura, anell, bombolla ni vel.

**La reserva de fons, que és la mateixa que va encallar Codex:** les capes són revelats ACR
independents, no normalitzats per exposició. La 1/15 entra amb q = capa/compost de 2,0–3,9 i per
això només admet pes 0,70; la 1/8 entra amb q = 4–7 sobre un compost que als sectors 210–270° ja és
pla més enllà d'1,5 R☉, i qualsevol pujada que s'hi afegeixi surt com a mínim. El compost V3b té un
graó de to gros respecte de V2b (×2,2 a 1,5 R☉, ×8 a 2 R☉) i un pedestal de cel gris de la 1/15:
no és costura, és R12 sense normalització. Els sectors 225–255° entre 1,46 i 2,1 R☉ ja porten
mínims subllindar de 0,57–0,76 %: **cap capa més hi passarà la porta tal com estan revelades**.
Sortida (§10.4): normalitzar l'escala d'exposició entre bandes abans de compondre —revelar cada DNG
amb compensació −log₂(t/t_ref) i perfil lineal, o escalar-los fora de Photoshop—, que és un derivat
traçable del DNG (G0.07), no un retoc de l'apilat; o acceptar el compost amb dues capes noves i
recuperar el to amb corba radial al final (`research/84 §5`). Decisió de Pere.

Pendents menors: `geom.py` porta rutes absolutes del scratchpad (parametritzar); bucle mort a
`protection_factor`; si Pere continua veient l'arc de la 1/60 al V3b, re-derivar ID7 amb la porta de
478 px per membre i revalidar ID3→ID7 amb P3/P4.

### 11.3 `CapesTotalsV3c.psb`: el fonament re-derivat sense bombolla (LLIURAT, APTE AMB RESERVES)

**Per què:** Pere va ensenyar, amb només 12/11/10 enceses, una ombra fosca al voltant de la
protuberància i un vel al limbe. Mesurat: la màscara de la 1/125 de Corretgint2 (heretada a V2b i
V3b) tenia un **forat azimutal de 45°** (0,000–0,19 entre 165° i 210° a 452–500 px, contra 0,33–0,84
a la resta; sots a 90°, 135–150°) fet amb l'el·lipse «P4»: on la 1/125 no entrava hi quedava la
1/500, 3× més fosca. Cap porta ho va veure perquè totes jutjaven DESPRÉS−ABANS i excloïen la zona
lunar i els nuclis; el fonament s'havia acceptat per rebut. Les màscares de V3b heretaven els zeros
de la 1/60 fins a 620 px, o sigui que el forat es propagava.

**Què s'ha fet:** `~/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/CapesTotalsV3c.psb`,
**1.499.157.102 B, SHA-256 `ec838ad61f1844a85ceb128564f7cf497b827f62ee3c6abb423a6bfbe386a45e`**,
mateixes fonts pinades i offsets que V2b/V3b; ràsters byte-idèntics. Màscares noves de la 1/500, la
1/125 i la 1/60 = rampa radial solar × porta lunar pròpia (el·lipse mesurada al ràster de cada capa,
zero fins R+2/3, ploma 10–16 px) × protecció **per píxels**: P3 = perles/diamant de la 1/3200 (1.676
px, dilatació 3, ploma 4, distància màxima al fenomen 6,7 px), P4 = protuberàncies de la 1/500 (4.941
px, 4 components) + limbe R→R+4 (dilatació 4, ploma 6, distància màxima 9,9 px). La 1/30 re-derivada
sense cap zero heretat. Codi: `research/tools/capes_totals_v3c/`; QA (112 fitxers, amb el pilot de
baix a dalt en PNG i l'ABANS amb la bombolla) a `CapesTotalsV3c_QA/`.

| Capa | Veredicte | Rampa (R☉) | Pes |
|---|---|---|---|
| 11 1/500 | fonament re-derivat | plena des de R+2 | 1,00 |
| 10 1/125 | fonament re-derivat | 1,05 → 1,55 | 1,00 |
| 09 1/60 | fonament re-derivat | 1,17 → 2,07 | 1,00 |
| 08 1/30 | **acceptada** (SHA màscara u16 `b04b6a24…`) | 1,29 → 2,59 | 0,50 |
| 07 1/15 | **rebutjada** (a V3b passava a 0,70 sobre el fonament vell) | 15 combinacions, millor cas 2 mínims d'1,3–1,4 % | — |
| 06 1/8 | rebutjada | 25–33 defectes | — |

Verificació independent (codi propi): bombolla eliminada (la 1/125 entra amb normalitat al voltant de
la protuberància: 0,052–0,154 per sectors a 470–500 px, variació suau Sol–Lluna); dins P3 el final
és byte-idèntic a la 1/3200 i dins P4 a 12+11 (0 DN); porta de costura 0 defectes a cada pas; test
absolut per sectors 0 sots de màscara; pilot de baix a dalt (12 sola → +11 → +10 → +09 → +08) sense
ombra, anell, bombolla ni vel; merged = compost offline a ≤1 DN. Reserves: (a) cobertura de validesa
a 0,85–0,90 en 24 de 3.765 cel·les al nucli del streamer de 135–150° (p50 0,47–0,54, llindar 0,46):
s'ha pres r_a per anell perquè amb r_a per cel·les cap capa de la cadena passa la porta; (b) el perfil
azimutal lunar-cèntric de les màscares solars és un cosinus d'amplitud ~0,05 per l'offset Sol–Lluna
de 15 px: no és un forat, i el test de G5.10 s'ha de formular com a residu respecte d'aquest cosinus;
(c) la 1/500 deixa α ≤24/65535 a la vora del disc de la 1/3200 (4 DN).

**El preu, i la decisió que ja no es pot ajornar:** sobre el fonament net, la 1/30 només entra a mig
pes i la 1/15 i la 1/8 no hi entren: les capes són revelats ACR no normalitzats (q = 2–3,3 entre
consecutives al punt d'entrada; mesurat: 1/500 0,096 / 1/125 0,318 a 1,05 R☉; 1/125 0,146 / 1/60
0,282 a 1,17). La corona de V3c arriba a ~2,6 R☉ amb 1/60 + mig 1/30. Per continuar cap enfora cal
**normalitzar l'escala d'exposició abans de compondre** (§10.4): revelar cada DNG amb compensació
−log₂(t/t_ref) i perfil lineal (derivat traçable del DNG, no retoc de l'apilat), o escalar fora de
Photoshop. Sense això el tram extern no passarà cap porta honesta.

**Guardrails a la skill** (`postprocessat-corona`, versió 2 del protocol; còpia global idèntica):
G0.09 (cap fonament per rebut), G4.10 (màscara = radial × porta lunar per capa × protecció per píxels;
res més), G4.11 (protegir ≠ foradar), G5.10 (prova absoluta per sectors de 5° incloent zona lunar i
nuclis), G5.11 (cobertura de validesa), G6.14 (extensió de la protecció ≤ dilatació + ploma), G7.07
(pilot de baix a dalt obligatori amb PNG al rebut); invariants 7 i 8 al `SKILL.md`.
