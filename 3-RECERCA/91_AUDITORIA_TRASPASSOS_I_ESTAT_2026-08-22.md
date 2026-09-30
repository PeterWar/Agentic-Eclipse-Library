# 91 — Auditoria del 22-08 al vespre: els traspassos Codex/Kimi/Gemini i l'estat real del disc

Data: 22 d'agost de 2026, vespre. Demanada per Pere: «audita novament el
projecte i mira els handoff que t'han preparat».

Auditoria de **només lectura**. Cap fitxer del projecte no s'ha mogut,
esborrat ni modificat fora de l'abast declarat al lock
(`research/91`, `research/README.md`, `.coordination/CLAUDE_STATUS.md`).
Zero càmeres, PTP, `gphoto2`, Photoshop, GUI i git-mutacions.

Mètode: vuit línies de verificació independents més vuit contrastos
adversarials —setze agents, 3,0 M tokens, 784 crides d'eina—, cadascun
obligat a **reproduir amb les seves pròpies ordres** el que l'altre afirmava.
Els contrastos han refutat catorze troballes; les que queden són les que dos
auditors independents han pogut reproduir.

## 1. El que els traspassos afirmen i és cert al disc, avui

Això és el gruix, i cal dir-ho primer: **la cadena de rebuts del 22 d'agost
aguanta**.

- **Els nou hashes de coordinació coincideixen exactament**: els tres deltes
  Codex → Claude, l'auditoria payload, el rebut `FINAL_VALIDATION`, la
  maqueta de Pere (110.750.130 B i `5d25d4cc…`) i els tres originals
  Gemini/Kimi preservats.
- **Vixen S6**: `shasum -c` dona **319 OK de 319**, cap absent, cap sobrant, i
  el `SHA256SUMS.txt` té el `b140cc7b…` declarat. Els vuit stacks `STABLE` del
  `vixen_natural_stable_v5.json` existeixen i encadenen bé; els 68 RAW i els
  32 calibradors són byte-idèntics.
- **Sony S6**: **335 de 335** i el manifest té el `3cec9ea0…` declarat.
  `segment_A/8s` és DSC06987 i `segment_C/8s` és DSC06993 —comprovat als
  rebuts de fotograma, no pel nom de la carpeta—, tots dos **`QUARANTENA` i
  mai `REBUTJAT`**, fotograma únic i fitxers separats. DSC06990 consta
  `REBUTJAT` amb motiu literal `MOVIMENT_DURANT_EXPOSICIO_8S`.
  `sony_cross_train_c_v2` declara `eight_second_consumed: false` i els salts
  cauen a 1,20000 / 1,50000 / 2,00000 R☉ exactes.
- **Flats posteriors**: els dos manifests verifiquen sencers, els 178 RAW font
  (125 CR3 + 53 ARW) tornen a donar el mateix SHA-256, inode i mida, i els
  números citats a `ESTAT_ACTUAL.md` són literalment els del JSON —PRNU fi
  Vixen 0,894–0,921; radial Sony 0,9999957–0,9999972; p95 0,16–0,55 %—.
  **Cap S6 s'ha tocat**: cap fitxer de `postprocessat_final` té mtime
  posterior i cap rebut S6 cita els flats nous.
- **Els originals de l'eclipsi no s'han tocat.** El fingerprint
  `8d1927d8…` es reprodueix **bit a bit** amb el mètode del propi script del
  projecte (`research/tools/cleanup_deprecat_noseque_20260822.py`), excloent
  només les dues carpetes de flats.
- **Els 50 moviments verificables de `moves.tsv` quadren** fitxer per fitxer i
  byte per byte; `Deprecat` i `No se que fa això aquí` han desaparegut; els sis
  TIFF restaurats de `Corona_HDR_Vixen` tenen el SHA-256 declarat.
- **La preservació Gemini és impecable**: 51/51 outputs (38 TIFF + 12 JPEG +
  1 JSX, 4.521.150.878 B) i 72/72 fitxers Antigravity verifiquen hash a hash a
  origen i a destinació, sense inodes compartits.
- **L'entorn Python és real**: Python 3.9.6, `sunkit-image` 0.5.1, els tres
  imports exactes funcionen, l'incorrecte és rebutjat i el smoke de MGN 64×64
  surt finit. El freeze viu és byte-idèntic al rebut.
- **La reparació fail-closed de Kimi/V4 és real**: 17/17 proves unitàries i
  AST 7/7. G5.11 falla de veritat i els números de Codex són exactes
  —S4 117, S5 143, S7 15; cadena S11/S12/S13/S16/S17 = 1/2/6/7/11—, amb G5.10
  passant als dotze estats. El 12/12 del verificador és compatible amb el
  fracàs de G5.11 perquè només comprova fidelitat de bytes.
- **El repositori està net de locks**: `.coordination/claim.lock` no existia i
  cap fitxer d'estat no reté `SERIAL_WRITES` viu. Els research 73–90 existeixen
  i estan indexats.

## 2. Troballes ALTES

### 2.1. 273 GiB d'autoritat material sense cap còpia, i `git clean` se'ls enduria

`git rev-list --count HEAD --not --remotes` → **25 commits** sense remot. El
bare de Dropbox només té dues refs i totes dues apunten a `9b2a127`, del 5
d'agost (0.8.1). No hi ha upstream. `tmutil destinationinfo` → cap destinació.
`/Volumes/4TB` no està muntat.

Mentrestant, l'untracked del worktree suma **289,77 GiB**, dels quals
`output/postprocessat_final_20260822` en fa **273,14 GiB** —`vixen_s6_ACCEPTED`
46 G i `sony_s6_ACCEPTED` 50 G—, i **no hi ha cap altra còpia** ni a Downloads
ni a Desktop.

El detall que ho converteix en ALTA: `git check-ignore -v output/postprocessat_final_20260822`
surt amb codi 1, o sigui que **`output/` no és a `.gitignore`**. L'ordre que
`CLAUDE.md` prohibeix explícitament, `git clean -fdx`, esborraria els 273 GiB
sencers, i el bare de Dropbox només arribaria al 5 d'agost.

Què cal: o afegir `output/` a `.gitignore`, o —millor— una còpia dels dos
paquets S6 fora del Mac. Decisió de Pere.

### 2.2. El run canònic de l'eclipsi viu fora de les dues arrels i cap document viu no en dona la ruta

`CLAUDE.md` §1 bis declara canònic `20260812T202219_multi_camera_mission_run`
**sense ruta**. És a
`~/Library/Application Support/Eclipse Command/state/runs/20260812T202219_multi_camera_mission_run`,
87 MB. A les dues arrels només hi ha el derivat
`output/pdf/Informe_auditat_run_Eclipse_Command_20260812T202219.pdf`.
`MAPA_RUTES_I_OUTPUTS.md` i `ACTIVE.json`: zero encerts d'«Application Support».

L'evidència primària de l'únic eclipsi del projecte —ledger, cronologia i
`result.json` dels tres cossos— no és al repositori, ni a l'arbre d'actius, ni
a cap bàckup. Un reinstal·lament o una neteja de l'estat de l'app deixaria
l'informe auditat sense font.

### 2.3. 20,92 GiB solts a l'arrel de `~/Downloads`, inclosa la maqueta amb hash pinat a vuit llocs

96 fitxers, 22.458.365.120 B. Els més grossos: `Emperlada.tif` 3,2 GB,
`NoEncaixa.tif` 3,1 GB, `Prototip1.tif` 2,1 GB, `UnintCapesX.psb` 1,3 GB,
`Corretgint.psb`, `Corretgint2.psb`. **Cap no té còpia enlloc.**

La maqueta de referència de Pere és aquí i el seu hash el fixen **vuit**
documents vius. Si es perd, es detecta a l'instant i no es recupera.
Cap document viu no adverteix que la maqueta viu fora de les dues arrels
declarades.

### 2.4. ⚠️ RECTIFICADA — vegeu `research/92`

> **La conclusió d'aquesta secció era falsa i queda rectificada a
> `research/92_REGISTRE_DRUCKMULLER_CORREGIT_2026-08-22.md`.**
> `hdr_vixen_countss.npy` **està construït amb el Sol al centre exacte
> (3479, 2319)** —ho declara el seu propi `LLEGEIX-ME.md`—, o sigui que el
> valor escrit a mà és correcte **per a aquella matriu**. Vaig comparar-lo
> contra `final_solution.json`, que és l'astrometria d'un **fotograma cru**
> (`572A2983`) i no de la matriu HDR.
> El defecte real és un altre i és pitjor: la matriu `M` està ajustada amb
> estrelles de la **graella del sensor** i s'aplica a la matriu HDR, que viu
> en una graella desplaçada **(+89,775, −48,647) px** —mesurat amb 19
> estrelles del catàleg, σ = (0,25, 0,13)—. La capa Vixen queda desregistrada
> **68,8 px = 0,230 R☉** respecte de la base Sony.
> **El número de 71 px era correcte; la causa i, per tant, la reparació, no.**
> Validat amb el disc lunar: 69,06 px de desregistre amb el warp original i
> **0,28 px** amb el corregit.

#### Text original, conservat

El centre solar de la branca Gemini és el centre geomètric de la matriu, 71,2 px fora de l'astrometria del projecte

Aquesta és **la troballa tècnica del dia** i afecta directament la branca que
Pere ha dit que «pinta molt, molt bé».

Els scripts fan `sun_v = [3479.0, 2319.0]` a mà
(`build_full_rectangular_masters.py:95`, `build_perfect_corona_v2.py:93`,
`build_ultimate_corona_daylight.py:111`, `build_corona_masters_flawless.py:70`).
`hdr_vixen_countss.npy` té forma `(4638, 6958, 3)`: **6958/2 = 3479 i
4638/2 = 2319**. El «centre del Sol» és el centre geomètric del fitxer, no
cap mesura.

L'astrometria pròpia del projecte
(`Resultats_acceptacio_2026-08-17/final_solution.json`) dona
`r6_radial.sun = (3570,96, 2267,02)` amb n=22 i rms=0,424, i
`sony_radial.sun = (3894,01, 2768,67)` amb n=38 i rms=0,713. Passant el centre
astromètric Vixen per **la mateixa matriu M** de Gemini s'arriba a **0,24 px**
del centre astromètric Sony: **la matriu és excel·lent i l'error és
exclusivament el centre escrit a mà**. Passant el (3479, 2319) hardcoded surt
(3822,96, 2764,34), a **71,18 px** del bo — 227,9″, o sigui **0,238 R☉**.

Tota la geometria radial del pipeline penja d'aquí: `dist_rsol`, la zona de
solapament [1,5–2,8] R☉ de la calibració fotomètrica, la sigmoide de fusió
Vixen↔Sony a 2,8 R☉, la `inner_limb_mask` a 0,985 R☉ i el disc d'earthshine de
`build_5_masters.py:180`. **Una màscara de limbe descentrada 0,238 R☉ talla
dins la cromosfera per un costat i deixa un creixent de disc lunar per
l'altre.**

Es corregeix canviant dues xifres. El valor bo és a la referència canònica de
la skill (`astrometria_i_deflexio.md`, SHA `43590fcd…`, línia 48).
El `Handoff_a_Claude.md` viu encara publica el valor erroni com a «Autoritat
del Llenç» (línies 176 i 257), tot i que aquest document **no** és a l'ordre
de lectura obligatori.

### 2.5. Deu JSX poden mutar el document de Photoshop obert

Al snapshot congelat hi ha 13 JSX. Quatre agafen `app.activeDocument` **sense
cap comprovació** (`prototype_v10.jsx:5`, `v11.jsx:31`, `v12.jsx:47`,
`test_ps_levels.jsx:5`) i sis més hi cauen per `catch`, perquè el `app.open`
que haurien d'usar apunta a `1-Unint Capes/CapesTotalsV2.psb` i
`CapesTotalsV7.psd`, que **ja no existeixen** —els CapesTotals viuen ara a
`1-Unint Capes/Capes Totals/`—, o sigui que el `catch` dispara **sempre**.

`prototype_v10.jsx:18-30` aplica `applyGaussianBlur(20)` a les màscares de
totes les capes que continguin `FONT_HDR`. `prototype_v5.jsx:31-33` fa
`while (app.documents.length > 0) app.activeDocument.close(DONOTSAVECHANGES)`
abans d'obrir res. I els `saveAs` **sí que tenen destí viu**
(`1-Unint Capes/` existeix), o sigui que deixarien un PSB destrossat dins la
carpeta del projecte.

Photoshop no s'està executant ara: **el risc és latent, no en curs**. Però
executar qualsevol d'aquests deu amb un PSB obert agafa el document actiu de
Pere. Els SHA que `FINAL_VALIDATION` preserva no protegeixen de res, perquè el
dany passa dins l'aplicació.

### 2.6. Vuit scripts fan `append` sobre el `Handoff_a_Claude.md` viu, sense idempotència ni lock

`append_corrections.py`, `append_daylight.py`, `append_flawless.py`,
`append_audit.py`, `append_kimi.py`, `append_handoff.py`, `append_section_11.py`
i `append_section_12.py` obren el fitxer viu en mode `'a'`. Cap comprova si la
secció ja hi és; cap adquireix cap lock. Una segona execució hi deixa una §11 o
una §12 duplicades sense avís.

I el rebut de preservació **només congela §11 i §12** (5.945 B congelats contra
25.395 B vius): §1–§10 —on hi ha la matriu M de §5.1 i el centre solar erroni
de §8— **no es poden recuperar del rebut**.

### 2.7. Les rutes d'origen del paquet Vixen apunten a una carpeta que ja no existeix

Les 68 rutes d'entrada del `LEDGER_68.json` i les 32 dels calibradors apunten
a `Desktop/Eclipse 2026/Vixen Unfiltered/…`. Aquesta carpeta **no existeix**;
la viva és `Vixen R6III/Vixen Fase totalitat/`. Resultat literal de la
comprovació: **0 de 68 i 0 de 32 resolubles a la ruta declarada**, però
**68 de 68 i 32 de 32 íntegres i byte-idèntics a la ruta viva**.

El paquet es va segellar a les 13:48 i la reorganització de l'Escriptori és de
les 16:43–17:32: **les rutes eren bones quan es van escriure**. El problema és
que el rebut arrel declara un `hash_verification: 68/68 PASS` que **avui ningú
no pot tornar a executar** sense saber, per fora del paquet, el canvi de nom.
Això és exactament el que el traspàs anomena «resegellar amb rutes vives», i
és documental, no de reprocessat.

El mateix passa al Sony: **116 referències a `Desktop/Eclipse 2026/300mm/`
repartides en 41 fitxers** del paquet, quan la carpeta viva és `300mm A7RIIIA`.

## 3. Troballes MITJANES

1. **`ESTAT_ACTUAL.md` diu «572 ARW + 1.139 CR3 invariants» i avui n'hi ha
   677 i 1.264.** No s'ha tocat cap original: el que ha passat és que a les
   21:00, quatre hores després del rebut, **les dues carpetes de flats s'han
   posat DINS les arrels canòniques de càmera**. Una re-execució del validador
   del projecte dona `017c45eb…` i no `8d1927d8…`, i **no hi ha cap regla
   d'exclusió documentada**. Cal escriure-la, o el proper agent conclourà que
   els originals han canviat.
2. **El «zero JPEG» està desmentit**: 27 al Desktop i 261 al worktree.
   Dels 27, 12 són legítims (`IA/output/gemini_druckmuller_20260822/`); els
   altres 15 són 14 a `Derivats/Vixen/HDR4/qa/` del 17 d'agost —van entrar a
   l'arbre el 22 en moure HDR4 des de fora del perímetre, i el rebut del 20 no
   els va veure mai— més un del 22. Al worktree, 136 són tracked i restaurats
   de Git el 21. **Cap és una pèrdua**; el que cal és no citar «zero JPEG» com
   a estat present.
3. **Contradicció d'estat dins el paquet Vixen**: els 24 `AUTHORITY_RECEIPT.json`
   diuen `ACCEPTAT` i els 23 `STACK_RECEIPT.json` diuen
   `STACK_PENDING_SPLIT_LOO_VISUAL_ACCEPTANCE`, amb `decision_status:
   MEASURED_PENDING_STRUCTURED_RESIDUAL_REVIEW` als 23. **319/319 prova
   integritat de bytes, no acceptació científica**, i el nom del directori diu
   el contrari del que diu el rebut de sota. Això és el que «contractes a
   resegelar» vol dir de veritat, i el traspàs no ho concreta.
4. **El paquet d'autoritat comparteix inode amb els candidats i és
   escrivible.** `vixen_s6_ACCEPTED/accepted_stacks/corona/STABLE/2s/MASTER_linear_float32_ADU_s.tif`
   i `vixen_rsun_v3_stable_candidates/2s/MASTER_…` tenen el **mateix inode**,
   `nlink 2`, `-rw-r--r--`; 269 dels 320 fitxers tenen `nlink>1`. Tornar a
   executar l'ordre que el mateix rebut registra **corromp en silenci el
   paquet d'autoritat**. Recomanació d'enduriment: `chmod -R a-w` abans de
   qualsevol ronda nova. No hi ha dany produït (`source_content_mutations: 0`
   i les 319 sumes donen OK).
5. **L'esglaó dels arcs és a 1,5 R☉, no repartit entre tres.** Mesurat al
   producte lliurat: el salt de 2,0 R☉ val ≤0,4 % als tres canals —dins la
   banda de soroll—; el d'1,5 R☉ és **entre 15 i 20 vegades més gran**, arriba
   al +10 % en B i varia per azimut de 0 a 11 %. **És l'únic que produeix l'arc
   de color que Pere veu.** El traspàs els llista com si fossin equivalents.
6. **Els arcs també són a `sony_cross_train_c_v1`, i els píxels són
   byte-idèntics als de la v2.** Els dos derivatius RGB donen el mateix
   `e171d99c…` i els dos candidats visuals el mateix `584530c1…`. Retirar la v2
   no elimina res: qui agafi la v1 com a alternativa reintrodueix l'esglaó
   idèntic. Són el mateix producte amb dos rebuts.
7. **Els 38 màsters Gemini són `uint16` amb corba de to, no float32.** El codi
   fa `percentil 99,8 → clip → log1p → uint16` abans de desar, contra el que
   el mateix Handoff declara a §7.3. Són **display-referred, no fotomètrics**,
   i no es poden barrejar amb productes S6 al mateix llenç sense un pont
   documentat.
8. **Cinc camps de rebut que semblen mesurats són constants escrites a mà**:
   `OPERATION_PRE_POST_RAW_FINGERPRINT = "162e4573…"` és una constant de mòdul
   a `audit_jpeg_cleanup.py:16`, i els booleans `operation_pre_and_post_fingerprint_equal`
   i `unchanged_by_jpeg_move` són literals; el script no calcula cap fingerprint
   previ. Aquesta xifra sosté un `PASS_RECOVERABLE` a `ACTIVE.json` i s'afirma
   com a fet a `research/90` i a l'auditoria de flats. La substància es pot
   salvar per altres vies —el fingerprint viu i els SHA de font sí que es
   recalculen—, però la xifra no és auditable.
9. **El rebut §5.3 de la carpeta V4b és el de la ronda V4, copiat.** Els dos
   exemplars són byte-idèntics (`98c964b2…`) i el camp `state` apunta a una
   ruta que ja no existeix. El §5.3 **no s'ha tornat a executar per a la V4b**.
   I la seva columna `mestre_ADUs` no es reprodueix amb el màster viu: recalculada
   xifra a xifra dona +0,03 % a +0,64 %, amb forma de decalatge additiu que se
   satura a ~+3,0 ADU/s —possible nivell de cel diferent, no tancat—.
10. **El `LLEGEIX-ME` que viu al costat del PSB presenta la V4b sense cap
    reserva**: «les 12 capes acceptades a pes 1,0, 0 defectes de costura…
    verificació reoberta 12/12 OK», sense una sola menció de G5.11.
    `grep "G5.11"` a tot l'arbre del PSB: cap resultat. La correcció existeix,
    però a `MAPA_RUTES_I_OUTPUTS.md` i al worktree, no al costat del fitxer.
11. **`CLAUDE.md` §1 conserva dos imperatius de represa de feina de captura**:
    «Si reprens la feina de l'A7RIIIA…» i «Si reprens la feina de l'A7III…».
    El tercer germà sí que es va reescriure a «Si audites la feina històrica»,
    cosa que fa llegir aquests dos com a deliberats i vius. Un agent nou entra
    per §1 —el bloc que `AGENTS.md` declara «el context canònic actual»— i hi
    troba una cua de feina amb pendents «al cos», que exigeix càmeres i PTP.
12. **`CLAUDE.md` té dues seccions «## 1 bis»** (línia 83, «Estat post-eclipsi
    verificat», nova; i línia 145, «Els tres objectius científics
    innegociables», antiga), amb la «1 ter» encaixada entremig. Quatre
    documents citen «§1 bis» i ara la primera coincidència és la secció
    equivocada.
13. **Quatre documents apunten encara al traspàs del 20 d'agost com a viu**
    —capçalera de `CLAUDE_STATUS.md`, capçalera de `KIMI_STATUS.md`, cos de
    `handoff.md` i banner de `HANDOFF_2026-08-10_CODEX.md`— i **el del 20 no
    apunta enlloc**. Com que `CLAUDE.md` §1 obliga a llegir el bloc d'estat del
    principi dels status, **cap camí de lectura que comenci pels status no
    arriba al traspàs del 22**. (La capçalera de `CLAUDE_STATUS.md` queda
    corregida amb aquesta ronda; les altres tres no són del meu abast.)
14. **`KIMI_STATUS.md` declara a la capçalera un lock adquirit i viu que no
    existeix**: `status: ACTIVE`, `serial_writes: ACQUIRED`, claim
    `FC0611A4…` del 21 a les 18:53. El tancament és 70 línies més avall. El
    primer que un agent llegeix diu que hi ha un escriptor viu.
15. **Hi ha un tercer agent amb journal propi que cap document d'autoritat no
    reconeix.** `KIMI_STATUS.md` té 150 línies i escriu fins al 22 a les 19:22,
    amb claims i tancaments propis. `grep -c -i kimi`: **0** a `AGENTS.md`,
    **0** a `CLAUDE.md`, **0** a `NORMES_I_AUTORITAT.md`, **0** a
    `DECISIONS.md`. El model documentat és de dues IA i el disc en té tres, i
    la disciplina de lock no diu com hi participa la tercera.
16. **La còpia viva del `handoff.md` de Kimi té una edició al cos**, no només
    l'overlay: la ruta de `CapesTotalsV4b.psb` s'hi reescriu de
    `1-Unint Capes/` a `1-Unint Capes/Capes Totals/…`. L'auditoria diu que
    «manté el cos històric», i no és exacte. (L'original preservat sí que és
    intacte: `93632d57…` verificat.)

## 4. El que NO és un defecte, tot i semblar-ho

Els contrastos adversarials han refutat catorze troballes. Val la pena
registrar-ne quatre, perquè són trampes on tornarà a caure qui auditi:

- **DSC06987 no és un problema amagat.** El seu residu estel·lar surt `FAIL` i
  no té domini acceptat, però (a) el paquet **iguala les dues 8 s** —«BOTH 8 s
  contributions stay quarantined»—, (b) `research/72` diu que la 06987 és la
  **més nítida** de les dues (~0,5 px contra ~0,75), (c) incorporar-les totes
  dues és **decisió expressa de Pere** i «una estrella no perfecta no és un
  veto», i (d) el `HANDOFF_VIGENT` **obliga** a llegir on consta el FAIL i
  prescriu tractar-les **per separat**. No és un defecte.
- **El manifest `vixen_natural_stable_v5.json` sí que ancora per hash** els
  vuit masters, per dues vies encadenades, encara que les entrades no portin
  el camp `hash` directament.
- **Els 52 ARW Sony duplicats dins la carpeta de flats del Vixen** (4,14 GiB)
  són reals i **estan documentats** a `MAPA_RUTES_I_OUTPUTS.md` («52 còpies ARW
  Sony no compten»).
- **El `Handoff_a_Claude.md` de Gemini no és autoritat viva.** Té un banner de
  22 línies que el desactiva sencer i no surt a l'ordre de lectura obligatori
  d'`IA/README.md`, ni a `ACTIVE.json`, ni a `MAPA_RUTES_I_OUTPUTS.md`. Les
  seves directives (FOV Sony, earthshine, «5 màsters finals») no manen.

## 5. Límits d'aquesta auditoria

Dues coses **no** s'han pogut comprovar i cap conclusió no hi pot penjar:

- **Els dos lots de Paperera són il·legibles** des d'una sessió d'agent:
  `ls`, `find`, `du` i `os.listdir()` donen tots «Operation not permitted»
  (privadesa de macOS), també amb el sandbox desactivat. L'única cosa que
  funciona és `stat` del directori, i **els inodes coincideixen amb els
  rebuts**. Els 1.014 fitxers i 21.809.186.154 B del lot del 22, i els 106
  JPEG i 83.361.792 B del lot de flats, són avui **afirmacions autocertificades**.
  ⚠️ El primer intent amb l'error silenciat (`ls ~/.Trash | wc -l`) donava
  **0** i hauria fet concloure falsament que la Paperera és buida.
- **`/Volumes/4TB` no està muntat.** «El backup continua intacte» no es pot
  comprovar avui. Els sis TIFF restaurats sí que tenen el SHA declarat al
  destí local, però això és coherència interna, no una comprovació del backup.

## 6. Qüestions per a Pere

1. **Còpia de seguretat.** 273 GiB d'autoritat material en una sola còpia, en
   un directori untracked, en un Mac sense Time Machine i amb el disc de 4 TB
   desmuntat. ¿Munto el 4 TB i verifico, afegeixo `output/` al `.gitignore`,
   o totes dues coses?
2. ~~**El centre solar de la branca Druckmüller.**~~ **FET** el mateix 22 al
   vespre, per ordre de Pere, i pel camí va rectificar el diagnòstic: no era
   el centre sinó el **registre**. Vegeu `research/92` i el build
   `output/druckmuller_centre_corregit_20260822/20260822T2130Z_registre/`.
3. **El run de l'eclipsi.** ¿El copio de `~/Library/Application Support/` a
   `output/` perquè quedi dins una arrel declarada?
4. **La maqueta i els 20,92 GiB de `~/Downloads`.** ¿Els moc a una arrel, o
   n'anoto la ruta als documents vius i prou?
5. **FOV**: continua obert i cap IA no l'ha de resoldre per inferència.

## 7. Estat de la pausa

La branca visual continua `PAUSED_BY_PERE`. Aquesta auditoria **no** aixeca la
pausa, no autoritza apilatge, composició, Photoshop ni earthshine, i no
promociona cap producte. Els tres deltes Codex → Claude queden en `ACK_READ`
al diari de Claude; cap d'ells no és `APLICAT`.
