# Estat de Codex

## V29 — IN_PROGRESS

- status: IN_PROGRESS · serial_writes: HELD · owner: Codex
- claim_id: CODEX_V29_20260905 · acquired_utc: 2026-09-05T09:51:11.394809+00:00
- Objectiu de Pere A-E: recuperar detall ACHF de V25 al camp exterior;
  corregir les marques blaves de V28_Artefactes.psb preservant detall;
  replantejar ACHF gran/ample; millorar passa-alt 24; verificar alineació de
  totes les capes i suport coronal de la UNIÓ temporal descoberta per la Lluna.
- Autorització: nou V29 no-clobber amb proves i porta Photoshop necessàries.
  Les fonts V24/V25/V28 i V28_Artefactes, runs i RAW queden només lectura.
- Arrencada: context complet llegit a la recepció; AGENTS i estats revalidats,
  claim absent, CLAUDE.md sense canvis de data, intèrpret detectat.
- V28.psb ha canviat per save de Pere (3.215.328.980 bytes a les 11:40);
  el hash de la recepció ja no acredita aquest save. Es capturen hashes nous.
- Dues revisions acotades només lectura; root és l'únic escriptor.

## Handoff V28 llegit — RELEASED

- status: RELEASED · serial_writes: RELEASED · owner: null
- claim_id: CODEX_ACK_V28_20260905T092618Z · released_utc: 2026-09-05T09:26:35Z
- Punt de represa: V28, runs 019_VIXEN_CIENCIA i 016_SONYTOT_CIENCIA,
  etapes de research/tools/v25_lineal; geometria azimutal, detall exterior
  del TOTAL des de 4 R☉ i correccions d'artefactes a l'origen.
- Verificació pròpia limitada: V28.psb existeix i el SHA-256 recalculat
  coincideix amb V28_REBUT.md:
  3ba0fbedd4b2c51e62933d14db723f4e2083d37d3f3c6d6ab99e17bdd3f66e40.
  Inspeccionat PS28_render_tal_com_es_lliura.png. Les portes, correlacions
  i fidelitat de capes són evidència documentada de Claude; no reexecutades.
- Desfasament documental: IA/README.md i MAPA_RUTES_I_OUTPUTS.md daten del
  22-08, ESTAT_ACTUAL.md del 23-08 i ACTIVE.json del 25-08; continuen
  descrivint pauses i pilots superats. Per a aquesta represa prevalen
  AGENTS.md, el handoff explícit V28 i les entrades del 05-09 de CLAUDE.md.
  El rebut V28 també conserva literals antics sobre la base oculta i el
  radi del ghost, matisats per les notes finals; no s'han corregit aquí.
- Deutes rebuts: ampliar la cobertura Sony; un sol remostreig; A/B amb
  V24 + Camera Raw de Pere; variància per canal; puntet del ghost a 3 R☉
  i rombe de cobertura exterior. Cap execució d'aquests deutes iniciada.
- Únic fitxer persistent tocat: .coordination/CODEX_STATUS.md, afegint
  entrades i conservant íntegres les anteriors. Cap codi, imatge, RAW,
  PSB/TIFF, run, càmera, PTP, GUI o Photoshop tocat. Sense ordres git.
- Handoff: assimilació completada; següent treball segons l'encàrrec de
  Pere. Totes les ordres pròpies acabades, zero processos propis vius.

## Lectura del handoff V28 i assimilació del context — IN_PROGRESS

- status: IN_PROGRESS · serial_writes: HELD · owner: Codex
- claim_id: CODEX_ACK_V28_20260905T092618Z · acquired_utc: 2026-09-05T09:26:18Z
- Abast: únicament aquest diari; encàrrec de Pere de posar-se al dia amb el
  handoff `.coordination/HANDOFF_2026-09-05_CODEX_V28.md`.
- Lectures: AGENTS.md, CLAUDE.md sencer, blocs efectius dels dos diaris,
  handoff V28, IA/README.md, ESTAT_ACTUAL.md, MAPA_RUTES_I_OUTPUTS.md,
  camps d'estat d'ACTIVE.json, research/131-133, V28_REBUT.md i les skills
  postprocessat-corona (amb normes_i_portes.md) i corregeix-artefactes.

## Sincronització d'autoritat IA del pilot Vixen — RELEASED

- status: RELEASED_AUTHORITY_SYNC
- updated_utc: 2026-08-23T14:12:31Z
- acquired_utc: 2026-08-23T14:07:53Z
- released_utc: 2026-08-23T14:12:31Z
- claim_id: `C3A03773-AC97-42D5-8FFA-7B1A076491F5`
- serial_writes: RELEASED
- owner: null
- result: l'autoritat viva de Desktop queda sincronitzada amb el preflight
  canònic `BLOCKED_UPSTREAM_GATES`, `phase2_ldic_executed: false`, F0/F1
  bloquejats i la tasca visual anterior encara `PAUSED_BY_PERE`.
- desktop_status: `/Users/USUARI/Desktop/Eclipse 2026/IA/ESTAT_ACTUAL.md`,
  SHA-256 `e63b165a4dea395e878e3bba214d9007819f22a9af1940c93db1770b37a7d2ea`.
- desktop_active: `/Users/USUARI/Desktop/Eclipse 2026/IA/ACTIVE.json`,
  JSON estricte vàlid, SHA-256
  `5d0c86d6f59dcadc505fa1f4cfb3a1772fcd1a28eaacd9fadaa9cf25027f6632`.
- desktop_handoff:
  `/Users/USUARI/Desktop/Eclipse 2026/IA/Coordinació/HANDOFF_VIGENT.md`,
  SHA-256 `05227242bf80f740aef17fa8d591235515ccd1f8fff53c707a3189a4e8a53215`.
- qa: hashes canònics revalidats, referències antigues de «candidat de pilot»
  corregides, claus JSON úniques i revisió independent final `CLEAN`.
- safety: zero canvis en actius, outputs científics, RAW, darks, flats, S6,
  PSB/TIFF o codi; zero càmera, PTP, `gphoto2`, GUI física o Photoshop.

## Sincronització d'autoritat IA del pilot Vixen — IN_PROGRESS

- status: IN_PROGRESS
- updated_utc: 2026-08-23T14:09:03Z
- acquired_utc: 2026-08-23T14:07:53Z
- claim_id: `C3A03773-AC97-42D5-8FFA-7B1A076491F5`
- serial_writes: HELD
- owner: Codex
- task: sincronitzar exclusivament `ESTAT_ACTUAL.md`, `ACTIVE.json` i
  `Coordinació/HANDOFF_VIGENT.md` de l'autoritat IA de Desktop amb el resultat
  fail-closed ja congelat del pilot Vixen.
- scope: cap actiu fotogràfic, output científic, RAW, dark, flat, S6, PSB/TIFF,
  codi, càmera, PTP, `gphoto2`, GUI física o Photoshop.

## Pilot Vixen des de zero, fases 0-1-2 — RELEASED_FAIL_CLOSED

- status: RELEASED_FAIL_CLOSED_HANDOFF_READY
- updated_utc: 2026-08-23T14:06:08Z
- acquired_utc: 2026-08-23T13:12:01Z
- released_utc: 2026-08-23T14:06:08Z
- claim_id: `1A0D404D-1FA2-417B-A529-75885E3EA733`
- serial_writes: RELEASED
- owner: null
- result: el preflight s'ha materialitzat amb estat
  `BLOCKED_UPSTREAM_GATES`; no s'ha executat LDIC ni fase 2 perquè F0 i F1 no
  tenen evidència positiva Vixen suficient.
- canonical_build:
  `output/pilot_vixen_ldic_20260823/20260823T140401Z_preflight_canonical_v4/`;
  `STATUS.json` SHA-256
  `9e849564dabdb5968c6b2cdfe93b02eec1aed343fb485b136a67612da49861ed`;
  `PAYLOAD_SHA256SUMS.txt` SHA-256
  `f0c27142dee12ef965a21d6e648cf9ad8c1943dc24feb4c943ea749386397649`.
- inputs: 124 CR3 vius, no 129; 68/68 del manifest i ledger PASS, 15
  exposicions; 768 darks a l'arrel, 239 seleccionats, 15 parelles de màster
  ancorades; 125 flats i productes PASS; llarg físic 10,079368399159 s.
- blockers: el `+1,019/R²=0,981` és Sony; la Vixen només té 0,1149 % de
  palanca i eix no independent; placa 0,424193 px i geometria 0,487192 px
  fallen 0,3 px; 0,138859 px cobreix només cinc parelles.
- qa: 37/37 proves adversarials PASS, shell PASS, dos revisors independents
  `CLEAN`; rehash terminal 519 fitxers / 13.823.377.138 bytes PASS; payload
  7/7 PASS; `ERROR.json` absent; no-clobber reexecutat amb codi 2 i fingerprint
  invariant `524d00a1454fa685aca4075ad7c0596abfb70cdb6ff7f5d5870c3cc15c5745c3`.
- authority: `research/98_PILOT_VIXEN_PREFLIGHT_FAIL_CLOSED_2026-08-23.md`
  SHA-256 `c1c6f9374ae35e237c073e7c92a7707b118a40dc1c4e1ff348e1755a1e90a0c0`;
  `.coordination/HANDOFF_2026-08-23_CODEX_PILOT_VIXEN.md` SHA-256
  `b78b10cdd69db06da5974942dd9370b9b031bdf681d976697dc9c556dfaa8b11`.
- safety: zero càmera, PTP, `gphoto2`, captura, GUI física, Photoshop,
  Sony/earthshine/filtres; zero mutacions de RAW, darks, flats, S6, PSB/TIFF
  o productes històrics; worktree brut preexistent preservat.
- next_gate: Pere ha de proporcionar/autoritzar evidència F0 pròpia de la
  Vixen o reformular explícitament el contracte; després cal oracle F1
  held-out per frame. Només després es pot congelar i executar F2.

## Pilot Vixen des de zero, fases 0-1-2 — IN_PROGRESS

- status: IN_PROGRESS
- updated_utc: 2026-08-23T13:12:01Z
- acquired_utc: 2026-08-23T13:12:01Z
- claim_id: `1A0D404D-1FA2-417B-A529-75885E3EA733`
- serial_writes: HELD
- owner: Codex
- task: executar el traspàs viu `.coordination/HANDOFF_2026-08-23_PILOT_VIXEN.md`: pilot d'una sola tirada amb la Vixen, des dels RAW, fases 0 Calibració, 1 Registre i 2 Composició LDIC al llenç comú, amb rebuts i controls adversarials.
- scope: codi i proves nous sota `research/tools/pilot_vixen_ldic/`, outputs no-clobber sota `output/pilot_vixen_ldic_20260823/`, documentació viva estrictament necessària i aquest journal. RAW, darks, flats, PSB/TIFF previs, càmeres, PTP, `gphoto2`, GUI física, Photoshop automatitzat, Sony i earthshine són immutables.
- startup: `AGENTS.md`, `CLAUDE.md` sencer, autoritat IA post-eclipsi, handoff viu, contracte de fases, `research/95-97`, trampes, skills `apilatge-imatges-eclipsi` i `postprocessat-corona`, els dos status, `ACTIVE.json` i worktree brut llegits; canvis preexistents preservats.
- discovered_before_write: l'arrel de totalitat conté literalment 124 CR3, no 129 com diu el handoff; els 68/68 CR3 indexats pel manifest existeixen i cobreixen 15 exposicions. La discrepància de recompte no canvia l'entrada declarada del pilot, que és el manifest.
- safety: cap càmera, PTP, `gphoto2`, captura, GUI física, Photoshop automatitzat, Sony o earthshine; cap reset, checkout, clean, stash ni sobreescriptura global.

## Reparació Kimi/Gemini i branca Python Druckmüller — RELEASED

- status: RELEASED_HANDOFF_CLAUDE_READY
- updated_utc: 2026-08-22T19:57:53Z
- acquired_utc: 2026-08-22T19:27:04Z
- released_utc: 2026-08-22T19:57:53Z
- claim_id: `8153E64F-C335-4F84-A306-9BC71046922B`
- serial_writes: RELEASED
- owner: null
- central_finding: Pere ha provat els resultats de les llibreries Python de
  Druckmüller i diu que **«pinten molt, molt bé»**. El handoff a Claude ho
  tracta com la troballa visual prioritària amb estat
  `HIGH_PROMISE_BY_PERE_PENDING_CONTROLLED_S6_PILOT`, mai com a S6 acceptat.
- preservation: workspace Antigravity 72/72 i 4.687.614 bytes; outputs Gemini
  51/51 —38 TIFF, 12 JPEG, un JSX— i 4.521.150.878 bytes; hashes
  origen↔snapshot coincidents i zero inodes compartits. 38/38 TIFF passen
  `tiffinfo -D`. Originals documentals Gemini/Kimi exactes.
- originals: cap pèrdua o corrupció demostrada de RAW, S6, PSB/PSD o TIFF
  canònic. `CapesTotalsV4.psb` i V4b continuen exactes, SHA-256 `2a75cc69…` i
  `1d08d2f1…`; cap pipeline V4, Photoshop ni PSB executat o obert.
- repair: imports i claims Gemini corregits amb originals congelats; overlay
  viu explicita FOV pendent, dues Sony separades, V4b no canònic, earthshine
  pausat i NRGF/FNRGF només com a controls diagnòstics. La ruta Kimi V4b queda
  completa. Referència astromètrica projecte/skill idèntica, SHA-256
  `43590fcd…`.
- v4_fail_closed: `05/06/07/10`, `g5_11_gate.py` i el verificador exigeixen
  ordre i estat final canònics, G5.10+G5.11 no vacus, artefactes i predecessors
  hashejats contra els bytes vius, visibilitat completa i no-clobber inclosos
  symlinks. El verificador no fa cap `unlink` i escriu en mode exclusiu.
- qa_code: 17/17 proves PASS, AST 7/7 PASS, fuzz adversarial independent PASS;
  round-trip uint16→float32→uint16 amb 0 discrepàncies sobre 65.536 valors;
  `git diff --check` verd i `ACTIVE.json` vàlid.
- qa_material: Vixen S6 319/319 i Sony S6 335/335 hashes PASS; snapshots
  Antigravity/Gemini revalidats íntegrament; freeze Python coincideix i MGN
  passa smoke finit 64×64 amb imports correctes.
- authority: auditoria SHA-256
  `67e081bd0586ac4478ea135e78a193a3ce353eece5f9cb0031d456315bcfd533`;
  delta `8AF0A726-1B0F-49AF-9B15-D7438E271322` SHA-256
  `a0f90a12adef65e1ea0b491e5ae9ab8590b3e9f3a982a6378c33f817812e2a16`;
  validació final SHA-256
  `574fff158c2a4602299e119b08ba2b6d5cd57dcd703f1a25bc09d15a80cf8358`;
  estat `PENDENT_CLAUDE_ACK`, `PERSISTED_IN_IA_NO_PONT_USED`.
- handoff_hashes: `ESTAT_ACTUAL` `00808094…`; mapa `975c53ee…`; handoff viu
  `af8d7dab…`; handoff formal `c2bded74…`; tots coincideixen amb
  `ACTIVE.druckmuller_handoff`.
- safety: zero càmera, PTP, `gphoto2`, captura, GUI física, Photoshop o
  earthshine; zero processos propis pendents. Worktree brut preexistent
  preservat sense reset, checkout, clean, stash ni sobreescriptura global.
- next_gate: la branca visual continua `PAUSED_BY_PERE`. Quan Pere l'aixequi:
  S6 acceptat → dues Sony 8 s independents → decisió explícita de FOV → pilot
  1:1 amb G5.10/G5.11/G7.07, nulls i ablacions → decisió visual de Pere.

## Reparació Kimi/Gemini i branca Python Druckmüller — IN_PROGRESS

- status: IN_PROGRESS
- updated_utc: 2026-08-22T19:27:04Z
- acquired_utc: 2026-08-22T19:27:04Z
- claim_id: `8153E64F-C335-4F84-A306-9BC71046922B`
- serial_writes: HELD
- owner: Codex
- task: auditar i reparar sense destrucció el que Kimi/Gemini hagin pogut
  desquadrar, preservar la branca Python Druckmüller que Pere valora molt
  positivament i deixar-ne un handoff verificable i prioritari a Claude.
- scope: documentació viva i handoffs; snapshot no-clobber dels experiments;
  gates fail-closed G5.11 de CapesTotals V4; paritat de la referència
  d'astrometria de `postprocessat-corona`. RAW, S6, PSB/TIFF canònics,
  càmeres, PTP, `gphoto2`, GUI i Photoshop són immutables.
- startup: `AGENTS.md`, `CLAUDE.md` sencer, els tres documents IA obligatoris,
  `ACTIVE.json`, handoff vigent, handoff formal, dos status i worktree brut
  rellegits després de l'alliberament del claim de flats; skills
  `coordina-amb-claude` i `postprocessat-corona` llegides; zero accions de
  maquinari.

## Màsters flat posteriors Vixen i Sony 300 mm — RELEASED

- status: RELEASED
- updated_utc: 2026-08-22T19:25:35Z
- acquired_utc: 2026-08-22T18:57:25Z
- released_utc: 2026-08-22T19:25:35Z
- claim_id: `3310560C-8FF4-4C45-A35C-A0B1059E7CED`
- serial_writes: RELEASED
- owner: null
- task: construir i auditar màsters flat posteriors a l'eclipsi per al Vixen/R6 III i el Sony A7RIIIA/300 mm, quantificar què és transferible malgrat rotació, transport i deu dies de retard, i no aplicar-los als màsters S6 fins que passin una porta mesurada.
- scope: eines i rebuts nous no-clobber a `research/tools/flat_field_20260822/` i `output/flats_20260822/`; documentació viva actualitzada. RAW, darks, màsters S6, PSB/TIFF previs, càmeres, PTP, `gphoto2`, GUI física i Photoshop immutables. Per ordre posterior explícit de Pere, només els JPEG de les dues carpetes de flats s'han mogut recuperablement a la Paperera.
- startup: `AGENTS.md`, `CLAUDE.md` sencer, autoritat IA post-eclipsi, handoff, estats efectius, worktree brut i skill `apilatge-imatges-eclipsi` amb les dues referències obligatòries llegits; `git status --short` preservat; cap procés de captura viu.
- inventory: 125 CR3 Canon i 53 ARW Sony únics; 178/178 acceptats. Els 52 ARW Sony dins `Flats R6III` són còpies byte-idèntiques i no compten com mostres independents.
- masters: dos paquets nous, 4.427.625.357 bytes i 44 fitxers globals. Vixen en reixa S6 4640×6960, Sony en 5320×7968; FITS RGGB + NPY CFA4 `R,G1,G2,B`, full/radial/even/2-D/fine, cobertura, variàncies, splits, blocs, previews, rebuts i hashes.
- vixen_result: `FINE_SENSOR=VALIDATED_COMPONENT_NOT_APPLIED`; r amb PRNU de l'eclipsi 0,894–0,921, splits 0,978–0,986 i null independent millorat als quatre plans. Radial candidat de pilot; full/2-D/pols quarantena per rotació i asimetria RMS 2,10%.
- sony_result: `OPTICAL_RADIAL=VALIDATED_COMPONENT_NOT_APPLIED`; r contra donor S6 0,9999957–0,9999972 i p95 0,16–0,55%. Fine quarantena perquè splits r=0,192–0,524; full/2-D/pols quarantena per gradient, transport i asimetria RMS 2,78%.
- jpeg_cleanup: 106 JPEG, 83.361.792 bytes, moguts a `/Users/USUARI/.Trash/Flats_JPEG_Eclipse_2026_20260822T190159Z`; zero JPEG/JPG a origen; 230 camins RAW invariants; Paperera no buidada. Rebut SHA-256 `3b4ddae2fa4639a56dd6f0641c05216747c7a7f779488847c72832056085b846`.
- receipts: Vixen `7a61ccd802f46032f053a663fd4977a943e4d6c34f92f12bb13dc86a17eb073d`; Sony `84488a5160ffa1491aad0e229ee3a4660608def93acbfbc582b6fa1f70f319e0`; transfer `09b561965c3e18e3c4b5b0747f8d274841f0d720497251128794489cd4ae06cf`.
- qa: 178/178 SHA-256 de fonts revalidats; manifests 38/38 + 2/2 PASS; FITS checksum/datasum, dimensions i mapping CFA PASS; JSON i sintaxi PASS; `git diff --check` verd; checker de la skill `Tot a punt`; zero processos de captura.
- authority: `research/90_MASTERS_FLAT_POSTERIORS_VIXEN_SONY_2026-08-22.md`; auditoria IA SHA-256 `e4dd442a331c7cf4c6b8c5871b7fd21a267fd8b9eeccfa231509393d1b9acebe`; delta `042DA4EE-6598-49DE-B4CD-60AB75E6EF8D`, SHA-256 `2aa95dd2e90fb2bb483beab6d1f171bfb225791093dd51208fce7b68a3310f15`, `PENDENT_CLAUDE_ACK`, `NO_PONT_USED`.
- next_gate: conservar els S6 com a control; qualsevol pilot recalibra RAW originals en output nou perquè flat i warp no commuten. No reprendre la branca visual `PAUSED_BY_PERE`.

## Recerca futura Sony amb RAW/JPEG repartits entre dues targetes — RELEASED

- status: RELEASED
- updated_utc: 2026-08-22T18:51:21Z
- acquired_utc: 2026-08-22T18:50:34Z
- released_utc: 2026-08-22T18:51:21Z
- claim_id: `EC9BA1E9-BDA2-4042-B684-C1F424BDB742`
- serial_writes: RELEASED
- owner: null
- task: anotar com a investigació futura d'Eclipse Command si separar RAW i
  JPEG entre les dues targetes d'una Sony augmenta la velocitat sostinguda.
- scope: nota nova `research/89_RECERCA_FUTURA_DOBLE_TARGETA_SONY_RAW_JPEG.md`,
  entrada a `research/README.md` i aquest journal. Cap perfil, codi, bundle,
  càmera, targeta, PTP, `gphoto2`, GUI o actiu fotogràfic tocat.
- result: pregunta registrada com a hipòtesi, no com a conclusió. El gate
  futur compara A) RAW+JPEG a l'Slot 1, B) RAW a l'Slot 1 i JPEG a l'Slot 2,
  i C) RAW només a l'Slot 1, amb cadència, cua/drenatge, manifests per
  targeta, integritat ARW i fallades. Als A7III/A7RIIIA només l'Slot 1 és
  UHS-II; per això B pot millorar, ser neutre o empitjorar.
- qa: `git diff --check` verd; document i índex rellegits; zero processos
  propis d'Eclipse Command, hosts, controladors o `gphoto2`.
- next_gate: cap canvi operatiu. Només amb una autorització física futura,
  executar el gate body-specific amb les mateixes targetes i coreografia;
  no promoure B si no millora repetiblement el pitjor cas sense pèrdues ni
  fragilitat nova.

## Estat, cronologia i handoff Codex → Claude — RELEASED

- status: RELEASED_HANDOFF_CLAUDE
- updated_utc: 2026-08-22T16:23:55Z
- acquired_utc: 2026-08-22T16:10:39Z
- released_utc: 2026-08-22T16:23:55Z
- claim_id: `0BE3259D-1D49-4684-BDE7-2B11CECCA259`
- serial_writes: RELEASED
- owner: null
- task: deixar l'estat i la cronologia post-eclipsi perfectament indexats i
  preparar un traspàs verificable perquè Pere pugui alternar Codex i Claude.
- scope: onboarding viu sota `Desktop/Eclipse 2026/IA`, aquest journal,
  `AGENTS.md`, el bloc inicial de `CLAUDE.md` i el nou handoff formal del
  worktree. Cap RAW, màster, TIFF, PSB, JPEG, càmera, PTP, `gphoto2`, GUI o
  Photoshop modificat o generat; la branca visual continua `PAUSED_BY_PERE`.
- onboarding_result: `IA/ACTIVE.json` passa a esquema 3 i distingeix les dues
  arrels canòniques, la neteja reversible, les autoritats S6, la causa dels
  arcs, el FOV pendent, la pausa visual i l'alternança d'IAs. `IA/README.md`,
  `ESTAT_ACTUAL.md`, `MAPA_RUTES_I_OUTPUTS.md`, `DECISIONS.md` i
  `Coordinació/HANDOFF_VIGENT.md` són coherents amb aquest estat.
- chronology_and_audit:
  `IA/Coordinació/CRONOLOGIA_POSTECLIPSI_2026-08-22.md`, SHA-256
  `63ca078ef4c40286b8201881106ea0526bef38a674524630b6317b8ea9b5171f`,
  i `IA/Coordinació/AUDITORIA_REPRESA_VIXEN_SONY_2026-08-22.md`, SHA-256
  `1812c3fea698cf97ca2ed71185467290b69f9de3eceda85c518e496cb25e9a0d`.
- claude_delta:
  `IA/Coordinació/DELTA_CODEX_a_CLAUDE_22-08-26_ECLIPSE_POSTPROCESSAT.md`,
  `delta_id=8384B473-B855-4093-AEAA-0C4B11437EE1`, SHA-256
  `f3bc7115518474112dca63a5df366eaa301abb81e445487926d2a4eda966045b`,
  estat `PENDENT_CLAUDE_ACK`; persistit localment, `NO_PONT_USED`.
- handoffs: `IA/Coordinació/HANDOFF_VIGENT.md`, SHA-256
  `09b1708cc74efa5486521845d2df7d957d0334d9b7164e72563798fb0c1bb03b`,
  i `.coordination/HANDOFF_2026-08-22_ALTERNANCA_CODEX_CLAUDE.md`, SHA-256
  `6f9d46d4ddd85c9796613d3c5a59ba8205bbbefa6adffc52fdf5fcb589e2018c`.
  El handoff del 20 d'agost queda preservat com a història.
- processing_authority: Vixen S6 319/319 i Sony S6 335/335; els vuit Vixen
  `STABLE` són reutilitzables amb resegelat de contracte. `DSC06987` i
  `DSC06993` continuen íntegres, en quarantena contractual antiga i
  obligatòries com a contribucions coronals independents; `DSC06990` continua
  rebutjada per moviment intraexposició. Els arcs provenen dels salts
  1,2/1,5/2,0 Rsol de `sony_cross_train_c_v2`.
- visual_reference:
  `/Users/USUARI/Downloads/Maqueta de resultat esperat.tif`, 110.750.130
  bytes, SHA-256
  `5d25d4cca0896c04147c75b5b9ad1c0b76a382a00a852fa596371de4c2b69e17`;
  guia estètica i d'enquadrament, no autoritat científica ni font de píxels.
- qa: JSON vàlid; hashes registrats 6/6 coincidents inclosa la maqueta;
  skills local/global byte-idèntiques; checker des del worktree i des de
  `/tmp` acaba `Tot a punt`; rutes provisionals absents; zero JPEG/JPG a
  `IA/output`; cap fitxer fora d'`IA` a Desktop modificat durant el claim;
  tres RAW Sony de 8 s amb hashes invariants; `git diff --check` verd.
- next_gate: Claude comença per `IA/README.md` i registra l'ACK del delta al
  seu journal. Cap IA reprèn el processat fins a una ordre nova de Pere; quan
  arribi, cal resegelar S6, tancar les dues Sony 8 s per separat i aturar-se a
  `FALTA DECISIÓ DE FOV` abans del pilot 1:1. Earthshine continua fora d'abast.

## Paritat de skill i auditoria de represa Vixen–Sony — RELEASED_VISUAL_PAUSADA

- status: RELEASED_VISUAL_PAUSADA
- updated_utc: 2026-08-22T16:06:00Z
- acquired_utc: 2026-08-22T15:59:16Z
- released_utc: 2026-08-22T16:06:00Z
- claim_id: `D16C2D2A-99E7-4117-9607-68D4332DFD1D`
- serial_writes: RELEASED
- owner: null
- task: sincronitzar les rutes reorganitzades de la skill
  `apilatge-imatges-eclipsi` i auditar en mode lectura les bases Vixen, Sony i
  la composició editable abans d'una eventual represa.
- scope: tres recursos de la skill global, el resolutor d'entorn local/global
  i aquest status. Cap RAW, màster, TIFF/PSB, càmera, PTP, `gphoto2`, GUI,
  Photoshop o JPEG modificat o generat.
- skill_result: les còpies local i global són idèntiques, resolen les rutes
  reorganitzades tant des del worktree com des de `/tmp`, eviten l'automatch
  de `pgrep` i acaben `Tot a punt`; sintaxi i `git diff --check` correctes.
- vixen_result: `vixen_s6_ACCEPTED` és íntegre —319/319 hashes— i els vuit
  stacks `STABLE` que consumeix `vixen_natural_stable_v5.json` són
  reutilitzables. Abans d'un `ACCEPTAT` S6 nou cal resegelar rebuts amb rutes
  vives, ús, domini, residus i limitacions explícites; singles i `LATE2`
  continuen separats.
- sony_8s_result: `DSC06987` i `DSC06993` i els seus derivats independents són
  íntegres; el `FAIL` estel·lar de `06987` no veta `CORONA_SOLAR`. Resten fora
  del final perquè l'antic materialitzador les deixa en `QUARANTENA`, sense
  màscara/domini S6, i tracta covariància pendent com a veto global.
  `DSC06990` continua rebutjada per moviment durant l'exposició.
- artefact_result: els arcs circulars provenen de la capa Sony cross-train:
  el constructor introdueix fronteres radials literals de contribució a 1,2,
  1,5 i 2,0 Rsol. No són estructura coronal.
- composition_result: el PSB natural editable v3 conserva 6/6 hashes i és de
  contrast tècnicament moderat, però no incorpora cap 8 s, no resol el FOV
  Sony–Vixen i no és el resultat final demanat. `CapesTotalsV4b` tampoc és una
  base acceptada perquè G5.11 falla.
- next_gate: la branca visual continua pausada per Pere. Quan la reprengui,
  primer resegelar sense recalibrar a cegues els vuit Vixen `STABLE` i les
  dues Sony de 8 s com a contribucions independents; després executar només
  un pilot 1:1 reversible amb decisió explícita de FOV, màscares de validesa
  no radials, ablation de cada 8 s i G5.10/G5.11/G7.07. Earthshine fora
  d'abast.

## Neteja de `Deprecat` i `No se que fa això aquí` — RELEASED

- status: RELEASED
- updated_utc: 2026-08-22T15:51:44Z
- acquired_utc: 2026-08-22T15:12:57Z
- released_utc: 2026-08-22T15:51:44Z
- claim_id: `DBC63AC4-B75F-4088-84BB-741EAF104581`
- serial_writes: RELEASED
- owner: null
- task: auditar els dos contenidors provisionals, conservar i recol·locar el
  material útil i retirar de manera reversible allò redundant, obsolet o
  declarat experimental.
- scope: arbre d'actius de `Desktop/Eclipse 2026`, eines i rutes vives del
  worktree, documentació d'`IA`, rebuts sota `output/cleanup` i aquest status.
  Cap RAW, càmera, PTP, `gphoto2`, GUI o Photoshop; cap JPEG generat.
- result: els dos contenidors ja no existeixen. El material útil queda
  classificat sota `Derivats`, `Publicacio`, els projectes Photoshop i
  `IA/Coordinació/Historic`; sis TIFF de `Corona_HDR_Vixen` absents a l'arbre
  reorganitzat s'han restaurat del backup i verificat 6/6 per SHA-256.
- reversible_prune: 1.014 fitxers regulars i dos enllaços ja trencats, amb
  21.809.186.154 bytes lògics, traslladats al lot dedicat
  `~/.Trash/Eclipse2026_cleanup_20260822T151257Z`; la Paperera no s'ha buidat.
- scratch_preservation: els treballs únics `CapesTotals` v2b, v3b i v3c han
  sortit de `/private/tmp` cap a
  `Derivats/Vixen/CapesTotals_work/{v2b,v3b,v3c}`: 354 fitxers,
  15.742.589.155 bytes, inodes i empremtes preservats; defaults v3b/v3c
  actualitzats.
- path_migration: migrades les rutes reutilitzables afectades cap a la nova
  estructura, inclosa l'astrometria mutable i els resultats d'acceptació
  preservats. `IA/ACTIVE.json`, estat, mapa, decisions, handoff i auditoria
  descriuen l'estat actual perquè una IA nova el pugui reprendre.
- qa: RAW d'arrel invariants —572 ARW, 1.139 CR3, empremta
  `8d1927d8e2bc5247cbccb5f40a97efa0f67620ff6b50efa6c7b52b89718ba843`—;
  sis TIFF 6/6; zero enllaços simbòlics vius a Desktop; checker d'entorn
  `Tot a punt`; astrometria preservada 22/22; 298 fonts Python validades amb
  Python 3.12; `git diff --check` verd.
- debt: `~/Desktop/HDR3` continua sent una selecció manual de dotze CR3 sense
  substitut segur automàtic. Cinc utilitats històriques de CapesTotals V1
  encara depenen del scratch desaparegut `v5out/ct1` i s'han de regenerar o
  parametritzar abans de reutilitzar-les.
- next_gate: la tasca visual continua aturada per Pere. No reprendre apilatge,
  composició ni earthshine fins que ho demani explícitament.

## Ruta canònica JPEG a `IA/output` — RELEASED

- status: RELEASED
- updated_utc: 2026-08-22T15:09:19Z
- acquired_utc: 2026-08-22T15:07:23Z
- released_utc: 2026-08-22T15:09:19Z
- claim_id: `38999BB4-9A24-43EC-9609-A3EB30DD7077`
- serial_writes: RELEASED
- owner: null
- task: resoldre la ruta canònica dels JPEG/JPG nous generats per IA d'acord
  amb la decisió expressa de Pere: `IA/output`, no `IA/Skills/output`.
- scope: documentació d'onboarding sota `Desktop/Eclipse 2026/IA`, l'`AGENTS.md`
  de l'arbre de dades i aquest status. Cap JPEG històric, imatge, output
  tècnic, RAW, TIFF o PSB mogut ni modificat.
- result: `/Users/USUARI/Desktop/Eclipse 2026/IA/output/` queda registrada
  com a única ruta prospectiva dels JPEG/JPG generats per una IA;
  `IA/Skills/` queda reservada a l'índex i les instruccions de les skills i no
  s'hi crea cap `output/`. Afegit `IA/output/README.md` i actualitzats els
  punts d'entrada, norma, estat, decisions, índex de skills, handoff,
  auditoria i `ACTIVE.json`.
- qa: `ACTIVE.json` vàlid; zero marcadors antics de bloqueig o desambiguació;
  ruta existent; zero JPEG/JPG presents a `IA/output`; `git diff --check`
  verd.
- next_gate: la ruta JPEG ja no és pendent. Resten la decisió sobre els sis
  TIFF recuperables i la migració explícita de les 62 fonts vives o
  reutilitzables amb rutes obsoletes.

## Auditoria de la reorganització i onboarding canònic d'IA — RELEASED

- status: RELEASED_AMB_UNA_DECISIO_DE_RUTA_PENDENT
- updated_utc: 2026-08-22T15:06:00Z
- acquired_utc: 2026-08-22T14:57:02Z
- released_utc: 2026-08-22T15:06:00Z
- claim_id: `C36248CE-F1A9-4FF7-84FB-058EDE6041E2`
- serial_writes: RELEASED
- owner: null
- task: auditar tota la reorganització manual contra el backup del disc 4TB i
  convertir `Desktop/Eclipse 2026/IA` en el punt d'entrada suficient per a una
  IA nova.
- scope: documents nous a l'arbre de dades i `IA`; blocs de ruta afegits a
  `AGENTS.md` i `CLAUDE.md` del worktree; aquest status. Cap RAW, DNG, TIFF,
  PSB, output històric, backup, càmera, PTP, `gphoto2`, GUI o Photoshop.
- inventory_result: BEFORE 8.769 fitxers regulars sense AppleDouble; AFTER
  manual 8.772. Excloent `.DS_Store`, 8.745/8.751 fitxers de contingut
  conciliats i zero contingut nou orfe. Els 4.809 RAW/DNG preservats per
  nom+mida+mtime, mostra SHA-256 24/24 i Sony 8 s crítics byte-idèntics.
- only_material_delta: sis TIFF derivats de `Corona_HDR_Vixen`, 589.683.216
  bytes, només al backup; no restaurats. `CapesTotalsV4b.psb` byte-idèntic al
  backup, SHA-256 `1d08d2f13de9faa0838e3610e1b1e9e342a279d03dc3805f9f0a179a0e6e3695`.
- path_audit: 378 fitxers/3.569 línies amb rutes ara trencades: 62 fonts vives
  o reutilitzables, 92 scripts de rescat, 2 snapshots, 192 rebuts/manifests,
  12 docs vives i 18 d'històriques. El checker d'apilatge confirma nou errors
  de dades; no s'ha fet cap substitució global.
- ia_result: creats `IA/README.md`, `NORMES_I_AUTORITAT.md`,
  `ESTAT_ACTUAL.md`, `DECISIONS.md`, `MAPA_RUTES_I_OUTPUTS.md`, `ACTIVE.json`,
  índex de skills, auditoria i handoff; creat també l'`AGENTS.md` de l'arbre de
  dades. Downloads continua sent el worktree Git i Desktop l'arbre d'actius.
- jpeg_policy: cap JPEG creat. La norma prospectiva queda bloquejada fins que
  Pere desambigüi `IA/output` contra el literal `IA/Skills/output`; els JPEG
  històrics no s'han mogut.
- qa: `ACTIVE.json` vàlid i 20/20 rutes resoltes; zero JPEG dins `IA`;
  `git diff --check` verd; hash auditoria
  `ba3cec082a1057c425b131e37b37086d57488fa4573d6974cafa3886851a0a03` i hash
  `ACTIVE.json` `db506138cdfa48574f910a6e8b6a8d50789d77d3aa9a2e748101bd30b6b6be7e`.
- next_gate: Pere confirma la ruta JPEG i decideix si vol restaurar els sis
  TIFF. Després, migrar només les 62 fonts vives cap al registre central de
  rutes; no reescriure rebuts, manifests ni snapshots històrics.

## Sony 8 s coronals i final natural editable — RELEASED

- status: RELEASED_ATURAT_PER_PERE
- updated_utc: 2026-08-22T14:08:32Z
- acquired_utc: 2026-08-22T14:03:39Z
- released_utc: 2026-08-22T14:08:32Z
- claim_id: `EF5E9823-7B41-4238-9926-D35EAEDCC0E2`
- serial_writes: RELEASED
- owner: null
- task: incorporar obligatòriament `DSC06987` i `DSC06993` com a contribucions independents de corona Sony de 8 s, mantenir `DSC06990` exclosa per moviment real, corregir la skill i publicar un nou lliurable editable natural sense anells.
- scope: aquest status; còpies projecte/global de `apilatge-imatges-eclipsi`; eines, manifests, rebuts i derivats nous no-clobber sota `research/tools/apilatge_integral_20260822/` i `output/postprocessat_final_20260822/`. RAW, calibradors i finals previs són immutables; earthshine queda fora; cap càmera, PTP, `gphoto2`, GUI física, Photoshop o LaunchServices.
- startup: autoritat canònica, traspàs viu, `handoff.md`, worktree brut preexistent i skills/referències obligatòries revisats; tres auditories read-only en paral·lel. Criteri fixat: l'autoritat d'admissió és el marc solar de la corona; el residual estel·lar és diagnòstic i no veto.
- result: Pere atura explícitament la ronda abans de construir cap capa o final nou. La skill sí queda corregida i validada a les còpies projecte/global: admissió per marc×ús×regió, `CONTRIBUCIO_UNICA`, residual estel·lar no transferible com a veto coronal i xifra de covariància `+0,42` retirada. Cap derivat 8 s, manifest v4, PSB o TIFF nou creat.
- next_gate: només si Pere reprèn la tasca, materialitzar `DSC06987` i `DSC06993` com dues capes solars independents i visibles, mantenir `DSC06990` exclosa i validar el v4 natural amb ablacions i QA anti-anell. Earthshine continua fora.

## Diagnòstic visual del registre estel·lar de DSC06987 — RELEASED

- status: RELEASED_CORRECTED_PREMISE
- updated_utc: 2026-08-22T13:56:39Z
- acquired_utc: 2026-08-22T13:51:02Z
- released_utc: 2026-08-22T13:56:39Z
- claim_id: `D051AB61-00C2-47B3-9BF6-A6C897FBBE34`
- serial_writes: RELEASED
- owner: null
- task: reconstruir i mostrar sobre les dades reals quines regions/estrelles de `DSC06987` no coincideixen després del registre actual, diferenciant translació, rotació i moviment intraexposició.
- scope: aquest status, un script de diagnòstic reproduïble a `research/tools/apilatge_integral_20260822/` i derivats nous a `output/postprocessat_final_20260822/diagnostics/DSC06987_stellar_registration/`. RAW, TIFF calibrats i productes previs són immutables; cap càmera, PTP, `gphoto2`, GUI física ni Photoshop.
- progress: startup canònic i skill `apilatge-imatges-eclipsi` llegits; `git status --short` brut preexistent preservat; lock adquirit; zero processos de càmera o QA propis.
- result: Pere detecta correctament que un control estel·lar no pot vetar per si sol una capa de corona de 8 s en seguiment solar. Les vuit estrelles només demostren dispersió de centroides en el marc estel·lar, no una regió local de corona mal registrada; la translació coronal es tanca independentment sobre el centre solar. Diagnòstic gràfic aturat abans d'executar-lo i script provisional retirat; cap derivat creat.
- next_gate: reavaluar `DSC06987` exclusivament en marc solar, amb estrelles emmascarades i null/continuïtat contra el 2 s del mateix segment, abans de decidir-ne l'ús visual exterior.

## Apilatge integral Vixen + Sony i imatge final — RELEASED

- status: RELEASED
- updated_utc: 2026-08-22T13:07:59Z
- acquired_utc: 2026-08-22T09:48:57Z
- released_utc: 2026-08-22T13:07:59Z
- claim_id: `018B4B91-F9CE-476B-AF62-8F67E03B2FE8`
- serial_writes: RELEASED
- owner: null
- task: construir i validar apilats de totes les captures independents utiles dels trens Vixen/R6 i Sony 300 mm segons `apilatge-imatges-eclipsi`, i derivar una composicio final propera a la maqueta sense artefactes circulars.
- scope: aquest status, eines i rebuts nous de postprocessat, una area derivada no-clobber i pilots/finals nous. Originals RAW, calibradors, stacks/PSB/TIFF existents, cameres, PTP, `gphoto2`, captures, GUI fisica, bundle i LaunchServices queden immutables.
- startup: `AGENTS.md`, `CLAUDE.md` sencer, estats efectius, traspas post-eclipsi, `handoff.md` de Kimi, skills `apilatge-imatges-eclipsi` i `postprocessat-corona` i les seves referencies obligatories llegits; `git status --short` brut preexistent preservat.
- progress: auditoria read-only Vixen/Sony i comparacio visual maqueta↔V4b en paral·lel; cap original ni producte existent modificat.
- progress_2026-08-22T11:12:52Z: inventari 273 CR3 Vixen + 194 ARW Sony tancat sense duplicats canonics; Vixen 68/68 processats, amb 10,079368399159 s corregit i 1/3200 separat C2/C3; candidat 26-en-1 i 10,3 s antics en quarantena. Sony combined A-C rebutjat pel null, segments A/C en curs; pilot primari CFA4 del segment C a 1/4 s passa split 1,006-1,016 sigma. Branca visual fixada a NATURAL, contrast moderat i edicio reversible.
- progress_2026-08-22T11:25:38Z: auditoria Vixen tancada amb 13 stacks ACCEPTAT + 10 singles com a contribucions lineals, 68/68 RAW unics i 9 combinacions antigues supersedides. Sony RGB A/C v2 repetit amb radi solar DE440+IAU correcte 295,6472 px, factor espuri de variancia 8 s retirat i segments A/C encara independents; CFA4 en correccio final de procedencia i plans de fons per pla. Cap original modificat.
- progress_2026-08-22T12:27:08Z: autoritats finals de stacks materialitzades sense mutar fonts. Vixen `vixen_s6_ACCEPTED`: 68/68 RAW unics, 13 stacks + 10 singles, 319/319 checks i SHA arrel `b140cc7b...`; Sony `sony_s6_ACCEPTED`: 14 processats, 2 rebutjats, 2 quarantena, tres repeticions C acceptades CFA4 i 335/335 checks, SHA arrel `3cec9ea0...`. La corona Vixen v5 harmonitza globalment les vuit exposicions, propaga `I/Var/InvVar`, ploma només el suport de saturacio de 2 s/10,079 s, passa anti-anell fins 8,5 Rsol a llindar 1 %, zero clipping i zero mascara radial lliure. C2/C3 v2 queden separats i ACCEPTAT/ACCEPTAT amb zero clipping natural. Cross-train Sony C v2 `ACCEPTADA_PER_FUSIO`, rotacio +33,0806 graus, escala 1,4896447, alfa maxima 0,1342 i QA de costura PASS; A, singles i 8 s no consumits. En curs: adaptadors Adobe/editable, earthshine i detall opcional molt suau.
- result_2026-08-22T13:07:59Z: lliurable canonic natural v3 a `output/postprocessat_final_20260822/final/eclipse_natural_editable_v3/`. PSB editable RGB16 Adobe RGB (1998) de 6595x4281 amb 11 capes, SHA-256 `6f36c45ae09a64236d797d6ee9f60ea01ba3234d8dfbf65b7f26980ce818e9e0`; TIFF merged SHA-256 `168887502b460967d05fdbc58cc1f098bc670772ef165c576aef6bb67ac95eb8`; preview sRGB SHA-256 `03cfb3c74d46e8796d4923be99b75fac9fb13cd7681ac66ef7e138e5bc108f6c`; rebut SHA-256 `07db41a59051c460577476cc34cbcf7c5967b9ec0df1039c32bfa709d3184be8`. `SHA256SUMS.txt` cobreix 6/6 i té SHA-256 `edd4a9c3fc11650d59f2f32474de5fc8f7235367842c5be89e9b5aa7f5c042fe`.
- visual_policy: merged deliberadament natural i poc contrastat. Visibles nomes base Vixen immutable, detall suau Normal 48/255 i Sony exterior en domini acceptat. C2/C3, prominencies, nivell lunar i earthshine queden amagats però editables. L'earthshine validat acaba a 401,7 px al llenç davant un limbe lunar de 453,8 px i produia un segon cercle; no s'ha ampliat la mascara ni inventat relleu. La prominencia C3 produia un arc taronja intradisc i també queda amagada. La maqueta i Kimi no aporten cap pixel o mascara.
- qa_final: Vixen 319/319, Sony 335/335 i final v3 6/6 hash checks PASS; constructor 9/9 self-tests; `git diff --check` PASS; 0 candidats d'anell entre 1,15 i 8,5 Rsol, 0 clipping alt, p99 final/base 1,0002317, fora del suport visible byte-identic a la base, TIFF/ICC i PSB/Lr16/mascares/merged round-trip exactes. Guia pedagogica i d'edicio a `LLEGEIX-ME_FINAL.md`, SHA-256 `83df90d0e9dba4f472129a2bef506d445f5d19acce72d4e6794477c7d10cfcf8`.
- evidence_and_safety: v1/v2 intermedis es conserven com a evidencia del gate visual; dues reconstruccions supersedides de l'adaptador Sony creades durant aquesta ronda es van moure recuperablement a la Paperera. Cap RAW, dark, flat, font, PSB/TIFF preexistent, camera, PTP, `gphoto2`, GUI o bundle modificat; zero processos propis persistents al release.

## Regla de llenç i FOV multitelescopi a `postprocessat-corona` — RELEASED

- status: RELEASED
- updated_utc: 2026-08-20T23:36:52Z
- acquired_utc: 2026-08-20T23:35:40Z
- released_utc: 2026-08-20T23:36:52Z
- claim_id: `10F580F6-4A00-4D34-8B18-8D71D64C2B02`
- serial_writes: RELEASED
- owner: null
- task: atomitzar la regla de Pere per combinar capes de telescopis/càmeres diferents: llenç regit per la dimensió màxima, font menor centrada sense píxels inventats i consulta obligatòria si la font amb menys píxels té més FOV efectiu.
- scope: aquest status i les còpies de projecte/global de `postprocessat-corona`; cap PSB, RAW, stack o producte visual es modifica.
- result: regla incorporada: `W=max(W_i)`, `H=max(H_i)` després d'orientació comuna; la font menor conserva el mostreig natiu, es centra pel marc registrat i deixa marges transparents amb pes zero. Si la càmera amb menys píxels té més FOV, la composició s'atura amb `FALTA DECISIÓ DE FOV` i pregunta a Pere abans de retallar, ampliar o remostrejar. Drizzle mai automàtic; si s'autoritza, es deriva upstream amb `apilatge-imatges-eclipsi` i es revalida.
- qa: `quick_validate.py` PASS a les dues còpies; projecte/global byte-idèntiques, SHA-256 `a4df38a22e08a1a949fb9cc00bdc8d0e1aba2dc82b758ac1a1de6bc241ad371d`; `git diff --check` PASS.

## Atribucio i correccio de l'artefacte radial de les capes exteriors — RELEASED

- status: RELEASED
- updated_utc: 2026-08-20T23:33:32Z
- acquired_utc: 2026-08-20T22:49:01Z
- released_utc: 2026-08-20T23:33:32Z
- claim_id: `CAC3DA15-0517-410C-A684-6A216119DB27`
- serial_writes: RELEASED
- owner: null
- task: reproduir offline les combinacions visibles de Photoshop, aillar IDs `8/9/10/11/12/13/16/17`, identificar la primera capa que introdueix l'artefacte radial i corregir nomes aquella amb `postprocessat-corona`, sense demanar maniobres manuals a Pere.
- attribution: la captura de les 00:46 mostra visibles IDs `8/11/12/13` sobre llenç transparent; IDs `9/10/16` són apagades i ID10 (`06_1-8s`) no participa. La primera fallada canònica sobre el fonament C2 és ID8 (`08_1-30s`): 3 mínims sectorials nous a r=462/484/491 px; la resta de la cadena queda invalidada per torre de Pisa.
- g3: cap warp promogut. Les fases ID8↔ID7 depenen de l'escala i la rotació no és significativa; remostrejar no millora la continuïtat fotomètrica.
- g2_g4: no hi ha banda lineal de 100 px que mantingui un guany global estable radialment i als 24 sectors sota el gate estricte. La millor rampa 1,95–2,60 R☉ passa perfils RGBY però el render/DIF 1:1 dibuixa un anell ample amb modulació azimutal. El darrer model físic `ID7=k·ID8+pla additiu` també falla el gate visual; una auditoria independent mesura millores holdout molt per sota del 25 % i coeficients inestables. Veredicte `REBUTJAR ID8`; cap màscara, raster derivat o compensació posterior promoguts.
- result: no s'ha creat `CapesTotalsV3.psb` perquè una porta dura falla. `CapesTotalsV2.psb` continua immutable (1.515.301.942 bytes, SHA-256 `d264374e85d0c089c955c4ab6da7c6baf2aa25b94a8e598791ef4efe48079c0f`) i el seu estat desat correcte manté visibles només IDs `3/4/5/7`; totes les exteriors resten ocultes i en quarantena.
- skill: `postprocessat-corona` ara exigeix atribució offline del PSB i de captures amb estat no desat abans de demanar cap maniobra manual. Còpies de projecte/global validades, byte-idèntiques, SHA-256 `6bebdee016bc070b88daee38eba492e5570a31cde2b6b6bba73f4af9a4b6a8e3`.
- receipts: `/private/tmp/capes_totals_v2_CAC3DA15/raw_audit/raw_audit_full.json`, `id8_registration/registration_audit_phase.json`, `id8_registration/linear_holdout_reaudit.json`, `id8_registration/last_physical_plane_result.json` i els pilots 1:1 associats.
- safety: cap Photoshop/GUI, camera, PTP, `gphoto2`, captura, RAW/TIFF/DNG ni font viva tocada; `Corretgint2.psb`, `CapesTotalsV1.psb` i `CapesTotalsV2.psb` verificats immutables; worktree brut preexistent preservat.

## Unió capa a capa de `Corretgint2.psb` amb les fonts de `CapesTotalsV1.psb` — RELEASED

- status: RELEASED
- updated_utc: 2026-08-20T22:08:40Z
- acquired_utc: 2026-08-20T21:00:00Z
- released_utc: 2026-08-20T22:08:40Z
- claim_id: `B2D5FE3B-E679-4322-8725-AA29206D8722`
- serial_writes: RELEASED
- owner: null
- task: substituir el fonament antic de `CapesTotalsV1.psb` per `Corretgint2.psb` i incorporar la resta de capes font una a una, sense cap filtre de detall/realçament, prioritzant plomes gaussianes de màscara que no introdueixin halos ni gradients.
- scope: aquest status, `postprocessat-corona`, eines noves a `research/tools/capes_totals_v2/` i un derivat nou `CapesTotalsV2.psb`; `Corretgint2.psb`, `CapesTotalsV1.psb` i tots els seus píxels font són immutables.
- result: `/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/CapesTotalsV2.psb`, 1.515.301.942 bytes, SHA-256 `d264374e85d0c089c955c4ab6da7c6baf2aa25b94a8e598791ef4efe48079c0f`; promoció atòmica no-clobber. Conté 12 capes font planes en ordre IDs `3,4,5,7,8,9,10,11,12,13,16,17`; només el fonament corregit `3/4/5/7` és visible. Les vuit fonts exteriors resten presents però ocultes i amb raster, transparència i màscara crus byte-idèntics a `CapesTotalsV1.psb`.
- layer_gate: ID8 (1/30 s), primera dependent, queda `REBUTJADA`: hard-core augmenta l'arc; una gaussiana local σ8 exclosa de P3/P4 no el resol; la guarda radial R+10→R+42 crea un mínim global nou a r=478 px. La cadena s'atura aquí; IDs9–16 no s'accepten per dependència i ID17 manté també el seu rebuig per halo-gradient. Cap correcció compensadora ni filtre s'ha incorporat.
- skill: `postprocessat-corona` queda simplificada a composició de màsters ja apilats, amb SNR/calibratge separats a `apilatge-imatges-eclipsi`; la gaussiana només és candidata local sobre màscara/pes, amb zeros durs reimposats i pilot 1:1 obligatori. Si la primera capa falla, s'atura la cadena.
- qa: verifier final `PASS`: PSB v2 RGB 16-bit 7.648×5.353, merged RGBA4, `Lr16`+`Mt16`, 12 capes `Normal`, zero grups/efectes/filtres, estructura i canals crus round-trip. Perles/diamant exactes `0 DN`; nucli ampli de limbe/protuberàncies conserva capes exactes i el merged queda dins quantització (13 valors de canal a 1 DN màxim). Alfa estructural: zero fora del frame i 65.535 dins. Manifest: `CapesTotalsV2.manifest.json`, SHA-256 `99fdac7499260ec897a6ff6de4f83e5a37d01eed720b4140651a8fdbc5a79eb5`.
- sources_after: `Corretgint2.psb` immutable SHA-256 `1777d41f29e9644faae527c1b4aed3be25f3ff1079f1418aabbcc58d9109e052`; `CapesTotalsV1.psb` immutable SHA-256 `4d0480f1d6508c225f5dbb13fb5c4e608d35a07b58acc2625853284ba48f2a28`.
- safety: cap RAW/TIFF/DNG, càmera, PTP, `gphoto2`, captura, Photoshop/GUI o projecte aliè tocat; cap fitxer font sobreescrit; worktree brut preexistent preservat.

## Separació de skill d'apilatge i correcció final de `Corretgint2.psb` — RELEASED

- status: RELEASED
- updated_utc: 2026-08-20T20:49:16Z
- acquired_utc: 2026-08-20T20:20:12Z
- released_utc: 2026-08-20T20:49:16Z
- claim_id: `EC8859FC-8D1C-4F62-988E-A0814B0B2049`
- serial_writes: RELEASED
- owner: null
- task: separar calibratge/apilatge/SNR en una skill nova, simplificar `postprocessat-corona` perquè parteixi de stacks Vixen/Sony ja validats, i reprendre la correcció visual del PSB amb un únic pilot H40 abans del build complet.
- scope: aquest status, les dues skills de projecte i globals, `research/tools/corretgint2/` i la substitució reversible de `/Users/USUARI/Downloads/Corretgint2.psb`; `Corretgint.psb`, RAW/TIFF/DNG i tots els stacks font són immutables.
- optimization: cap nova auditoria de SNR; es reutilitzen els intermedis verificats i les alternatives ja descartades; només un build PSB complet després del pilot 1:1 i una auditoria independent final.
- skills: `postprocessat-corona` queda reduïda a composició/Photoshop/QA científic a partir de màsters lineals ja validats; la nova `apilatge-imatges-eclipsi` concentra calibratge RAW, selecció, registre, apilatge, variància i SNR. Còpies de projecte i globals byte-idèntiques i validades amb `quick_validate.py`.
- result: `/Users/USUARI/Downloads/Corretgint2.psb`, 557.302.530 bytes, SHA-256 `1777d41f29e9644faae527c1b4aed3be25f3ff1079f1418aabbcc58d9109e052`; promoció atòmica des del candidat auditat. Còpia anterior preservada a `/Users/USUARI/Downloads/Corretgint2_before_perles_20260820.psb`, SHA-256 `84f670ab08f4c0db86840d7f6a730c93f8b6d1ebd52f813b3b69a77c1512e10d`.
- qa: PSB v2 RGB 16-bit, quatre capes IDs `3/4/5/7`, `Normal/100 %/100 %`; RGB/alfa font byte-idèntics; màscares i merged round-trip exactes. Perles/diamant: 263 px i quatre components `[135,85,32,11]`, nucli P3 `0 DN`. Limbe/protuberàncies: nucli P4 657.192 px, `0 DN`; discs ID4/5/7 amb alfa zero. H40: 69.296 px, zero fora del domini declarat i sense contorn, halo ni bombolla nous al render 100 %; auditoria independent final `PASS`.
- source_after: `/Users/USUARI/Downloads/Corretgint.psb` continua immutable, SHA-256 `d8afed2a997f8a449180be804561e6ed17eeaee30146970364a5daeba911730b`.
- safety: cap reauditoria ni modificació dels stacks Vixen/Sony; cap RAW/TIFF/DNG, càmera, PTP, `gphoto2`, captura o GUI física tocats; worktree brut preexistent preservat.

## Preservació fail-closed de fenòmens de contacte i correcció de `Corretgint2.psb` — RELEASED

- status: RELEASED_STOPPED_BY_USER
- updated_utc: 2026-08-20T19:27:32Z
- acquired_utc: 2026-08-20T16:46:11Z
- released_utc: 2026-08-20T19:27:32Z
- claim_id: `D2896CDB-0E14-45E2-80F4-FF261D948328`
- serial_writes: RELEASED
- owner: null
- task: corregir la skill perquè perles de Baily, diamant, protuberàncies i limbe quedin congelats des de la capa inferior protegida abans de construir màscares; reconstruir `Corretgint2.psb` i rebutjar el resultat si qualsevol estructura protegida desapareix o canvia dins el seu nucli.
- scope: aquest status, `.claude/skills/postprocessat-corona/`, `research/tools/corretgint2/` (inclòs `.build_perles_D2896CDB/` temporal), `/private/tmp/corretgint2_perles_D2896CDB/`, la còpia global de la skill i la substitució reversible de `/Users/USUARI/Downloads/Corretgint2.psb`. `Corretgint.psb` i totes les fonts fotogràfiques són immutables.
- result: aturat expressament per Pere abans de promoure cap candidat. El PSB viu continua byte-idèntic al d'abans (`84f670ab…1512e10d`); la còpia de seguretat també. El candidat temporal ocult `71700a58…98e4d7` queda rebutjat i no s'ha de promoure: preserva nuclis/perles però imprimeix un ribet de transició sota el gate visual estricte.
- skill: còpies de projecte i global sincronitzades i vàlides (`SKILL.md` `ee85dc4f…a4fc3f`; protocol `372bff83…b2e7`), però la regla nova de ploma queda pendent de reconciliar amb la incompatibilitat observada entre preservació exacta i absència d'empremta; no declarar la correcció final.
- temporals: `research/tools/corretgint2/.build_perles_D2896CDB/` conserva 9,7 GB i 113 fitxers, inclosos quatre PSB candidats, per no fer cap eliminació destructiva en aturar. `/Users/USUARI/Downloads/.Corretgint2_new_D2896CDB.psb` és només staging rebutjat.
- safety: `Corretgint.psb`, `Corretgint2.psb` i la còpia de seguretat verificats; cap font RAW/TIFF/DNG, càmera, PTP, `gphoto2`, Photoshop/GUI o projecte aliè tocat. Worktree brut preexistent preservat.

## Neteja reversible de versions de vídeo de l'eclipsi — RELEASED

- status: RELEASED
- updated_utc: 2026-08-20T16:43:57Z
- acquired_utc: 2026-08-20T16:36:25Z
- released_utc: 2026-08-20T16:43:57Z
- claim_id: `54A33609-3009-4709-9EC2-17AFF31CB558`
- serial_writes: RELEASED
- owner: null
- task: conservar intactes l'original, el màster documental ProRes WB, la totalitat v3 final i l'informe complet de shadow bands; moure recuperablement a la Paperera només els paquets de totalitat v1 i v2 supersedits.
- scope: aquest status, `output/cleanup/20260820T163625Z_video_versions/`, les dues carpetes v1/v2 i `/Users/USUARI/.Trash/Eclipse2026_Video_versions_antigues_20260820T163625Z/`. Cap reencodat ni canvi de contingut; fonts KEEP només lectura.
- result: v1 i v2 mogudes senceres a la Paperera; 22 fitxers i 230.440.555 bytes al destí, amb path relatiu, mida i SHA-256 idèntics 22/22. Les dues fonts ja no són a l'arrel activa i l'única carpeta `Video_Totalitat_Recuperada_v*` que hi resta és v3.
- keep: original MP4 `e7eb709b…c8fd`; ProRes WB `1c35edb2…9bab`; v3 `127e3e3c…f655`; informe shadow bands `874944cb…678d`. Mides, inodes i mtimes invariants després del moviment; v3 22/22 i shadow bands 26/26 manifests OK.
- quality: ProRes WB descodificació integral PASS; 15.060 frames/602,400 s/4K25 i PCM bit-exact preservats. Contra la transformació WB lossless: PSNR mitjà 56,296 dB i SSIM 0,997816; pèrdua numèrica mínima, cap degradació visual material. No és lossless globalment: WB no reversible i pista Sony RTMD absent; per això l'original es conserva.
- legacy_caveat: v1 ja tenia una entrada absent al manifest (`evidencia/QA_timeline_montage.jpg`); 11/12 entrades disponibles passaven. Els 12 fitxers realment existents han arribat byte per byte i tot continua recuperable fins que es buidi la Paperera.
- receipt: `output/cleanup/20260820T163625Z_video_versions/VALIDATION.md`, manifests abans/després i `SHA256SUMS.txt`, 4/4 rebuts OK.
- safety: cap esborrat permanent, reencodat o canvi als elements KEEP; cap RAW/TIFF/DNG/PSB ni projecte aliè tocat; cap càmera, PTP, `gphoto2`, captura, GUI física, build o LaunchServices; worktree brut preexistent preservat.

## Correcció canònica de `Corretgint.psb` → `Corretgint2.psb` — RELEASED

- status: RELEASED
- updated_utc: 2026-08-20T16:35:41Z
- acquired_utc: 2026-08-20T16:01:42Z
- released_utc: 2026-08-20T16:35:41Z
- claim_id: `9A7714FA-836A-452E-B87B-424BB6224DA5`
- serial_writes: RELEASED
- owner: null
- task: aplicar les correccions dictades per `postprocessat-corona` al fonament de `Corretgint.psb` i lliurar una còpia nova com `/Users/USUARI/Downloads/Corretgint2.psb`.
- scope: aquest status, `research/tools/corretgint2/`, `/private/tmp/corretgint2_build_9A7714FA/` i el nou PSB. `Corretgint.psb` és font immutable. Exclosos RAW/TIFF/DNG originals, càmeres, PTP, `gphoto2`, captures, GUI física, build i LaunchServices.
- source_before: inode `137824669`, 708.214.002 bytes, mtime `2026-08-20T17:39:51+0200`, SHA-256 `d8afed2a997f8a449180be804561e6ed17eeaee30146970364a5daeba911730b`.
- result: `/Users/USUARI/Downloads/Corretgint2.psb`, inode `137836246`, 557.548.266 bytes, PSB v2 RGB 16-bit 7.648×5.353, SHA-256 `84f670ab08f4c0db86840d7f6a730c93f8b6d1ebd52f813b3b69a77c1512e10d`.
- corrections: eliminada només la còpia PSD redundant/desplaçada `(+1,+1)` de l'1/60, conservat el raster canònic byte-idèntic; màscares radials 16-bit reconstruïdes amb portes lunars per capa i cascada de saturació; base amb màscara explícita; vores blanques invàlides de Capa 1/2 tancades; transició 1/60 resolta a la mateixa màscara sense capa compensadora ni empremta el·líptica; noms traçables i quatre capes `Normal/100 %/100 %`.
- qa: `psd-tools` obre el document; `Lr16` present i `Mt16` absent; quatre capes IDs `3,4,5,7`; tots els canals font conservats byte a byte; quatre màscares 16-bit amb fons negre; merged round-trip exacte; cap raster duplicat; cap mínim radial local 452–620 px; vores netes; doble auditoria independent estructural i visual `PASS`.
- source_after: inode `137824669`, 708.214.002 bytes, mtime `2026-08-20T17:39:51+0200`, SHA-256 `d8afed2a997f8a449180be804561e6ed17eeaee30146970364a5daeba911730b`; invariant exacte.
- reproducibility: `research/tools/corretgint2/build_corretgint2.py` i `analyze_geometry.py`; QA temporal a `/private/tmp/corretgint2_build_9A7714FA/work/qa.json`.
- safety: cap font fotogràfica ni PSB original modificat; cap càmera, PTP, `gphoto2`, captura, Photoshop/GUI, build o LaunchServices; worktree brut preexistent preservat.

## Auditoria de `Corretgint.psb` amb la skill de capes — RELEASED

- status: RELEASED
- updated_utc: 2026-08-20T15:53:06Z
- acquired_utc: 2026-08-20T15:41:42Z
- released_utc: 2026-08-20T15:53:06Z
- claim_id: `2D67AB40-C0C5-469C-8DFC-4D8619186EB4`
- serial_writes: RELEASED
- owner: null
- task: provar `postprocessat-corona` sobre `/Users/USUARI/Downloads/Corretgint.psb`, extraure'n estructura i derivats temporals de QA, i aplicar les portes G0–G11 sense obrir Photoshop ni modificar el PSB.
- scope: aquest status i `/private/tmp/corretgint_psb_audit_2D67AB40/`; font PSB estrictament de només lectura. Exclosos originals RAW/TIFF/DNG, PSB viu, càmeres, PTP, `gphoto2`, captures, GUI física, build i LaunchServices.
- source_before: inode `137824669`, 708.214.002 bytes, mtime `2026-08-20T17:39:51+0200`, SHA-256 `d8afed2a997f8a449180be804561e6ed17eeaee30146970364a5daeba911730b`.
- result: veredicte del document `QUARANTENA` i de la doble capa `09_1-60s_572A2975_apilat2.dng` `REPROCESSAR`. Les dues capes tenen píxels decodificats byte-idèntics però posicions separades `(+1,+1)` i màscares diferents que se solapen; no són captures independents ni aporten SNR addicional. La geometria efectiva varia espacialment entre les dues posicions i la diferència diagnòstica ressegueix limbe, protuberàncies i corona interior.
- structure: PSB 7.648×5.353, RGB 16-bit Display P3, cinc capes píxel planes, totes visibles `Normal/100 %/100 %`; `12_1-3200s` sense màscara; `Capa 1`=`11_1-500s`; `Capa 2`=`10_1-125s`; dues còpies d'`09_1-60s`. Cap grup, Smart Object, clipping, efecte ni capa d'ajust.
- gates: `G1/G6/G7/G9` fallen materialment per redundància PSD, doble geometria, màscara absent/solapada i canvi estructural; `G0/G2–G5/G8/G11` no tenen rebut complet dins el PSB; `G10` no aplica a aquest subconjunt de fonts interiors i la cadena exterior no es pot validar aquí. Cal una sola `09` en geometria canònica, fusionar-hi només les regions vàlides de les màscares, reconstruir des del primer fonament modificat i revalidar totes les dependències.
- qa: reconstrucció del fusionat codificat contra la previsualització PSB amb diferència mediana `2,08e-5`; 32.282.801 píxels de solapament entre les dues còpies; correlació de màscares `r=0,947`; totes dues pesen almenys 1 % en el 14,22 % del llenç. Derivats i mètriques a `/private/tmp/corretgint_psb_audit_2D67AB40/`.
- source_after: inode `137824669`, 708.214.002 bytes, mtime `2026-08-20T17:39:51+0200`, SHA-256 `d8afed2a997f8a449180be804561e6ed17eeaee30146970364a5daeba911730b`; invariant exacte.
- safety: cap fitxer de Photoshop ni font fotogràfica modificat; cap Photoshop, càmera, PTP, `gphoto2`, captura, GUI física, build o LaunchServices; worktree brut preexistent preservat.

## Skill canònica d'acceptació de capes Photoshop — RELEASED

- status: RELEASED
- updated_utc: 2026-08-20T11:29:10Z
- acquired_utc: 2026-08-20T11:18:16Z
- released_utc: 2026-08-20T11:29:10Z
- claim_id: `b12b1cc4-e8f8-4342-94f2-a5e7140c1ef7`
- serial_writes: RELEASED
- owner: null
- task: atomitzar les regles de Pere per acceptar una capa nova al compost Photoshop, integrar-les a la skill `postprocessat-corona` i contrastar-les amb fonts primàries de l'equip Druckmüller.
- scope: `.claude/skills/postprocessat-corona/`, aquest fitxer d'estat i una instal·lació global byte-idèntica a `/Users/USUARI/.codex/skills/postprocessat-corona/` subjecta a permís de filesystem. Exclosos originals, PSB/TIFF/DNG vius, càmeres, PTP, `gphoto2`, captures, GUI física, build i LaunchServices.
- result: skill existent `postprocessat-corona` ampliada, sense crear triggers paral·lels; nou `references/acceptacio_capes_photoshop.md` amb portes atòmiques `G0–G11`, vocabulari `DEMOSTRAT/FALTA/N/A`, veredictes fail-closed, rebut obligatori i matriu de compatibilitat regla per regla. `agents/openai.yaml` generat amb l'eina oficial de `skill-creator`.
- corrections: captures repetides independents s'apilen i només les capes PSD redundants es rebutgen; 85 % és sostre lineal específic i no objectiu d'histograma; corona, Lluna i estrelles usen marcs separats; extinció, fons, refracció i camp instrumental tenen portes distintes; denoise no decideix admissió; `Normal/100 %/100 %` queda restringit a capes font; calibratge, registre i normalització només en derivats traçables.
- sources: contrast amb Druckmüller–Rušin–Minarovjech 2006, correlació de fase 2009, tesi Druckmüllerová i treball modern Boe et al.; contrast local amb `research/73`, `74`, `78`, `80`, `82`–`86`.
- installation: còpia global autoritzada a `/Users/USUARI/.codex/skills/postprocessat-corona/`; `diff -qr` contra la còpia canònica del projecte sense diferències.
- hashes: `SKILL.md` `b4f01924849bc1c100afcc80c7beb1242b58bf9998f639ce4b7742c18a0f944b`; protocol `ed8a9fab01490bf0a444f7478c4c5aa53651a18312a9fb4cf9ea18f96bf11f75`; `agents/openai.yaml` `bc9c450bd913d882e1773c77692d861de3cd929bd82b1d1845d1163ae5b591bb`.
- qa: `quick_validate.py` PASS tant al projecte com a la instal·lació global; `git diff --check` PASS en l'estat propi; prova externa a cegues PASS: va conservar tres repeticions útils per SNR però va dictaminar `REPROCESSAR` pel denoise correlacionat, màscara lunar compartida, vora dura i manca de rebut ABANS/DESPRÉS.
- safety: worktree brut preservat; zero originals, PSB/TIFF/DNG vius o fitxers aliens modificats; cap càmera, PTP, `gphoto2`, captura, GUI física, build ni LaunchServices; cap procés propi persistent.

## Autoritat Codex post-eclipsi i neteja JPEG — RELEASED

- status: RELEASED
- updated_utc: 2026-08-20T11:09:15Z
- acquired_utc: 2026-08-20T10:53:46Z
- released_utc: 2026-08-20T11:09:15Z
- claim_id: `0d390ffe-37bb-45c8-a2b2-5cbc1c10e240`
- serial_writes: RELEASED
- owner: null
- authority: decisió expressa de Pere del 20-08-2026; Codex és el punt de represa viu perquè Claude no disposa de prou context/tokens. Jerarquia i protocol atòmic consolidats a `AGENTS.md`; traspàs canònic nou `.coordination/HANDOFF_2026-08-20_POSTECLIPSI_CODEX.md`. Els status són journals i els traspassos previs són històrics.
- task: consolidar l'autoritat post-eclipsi, retirar de manera reversible totes les imatges JPEG del projecte viu, preservar TIFF/RAW i corregir contradiccions documentals, científiques o mecàniques sense canviar cap càlcul físic.
- scope: `/Users/USUARI/Downloads/Eclipse 2026`, `/Users/USUARI/Desktop/Eclipse 2026`, documentació canònica, índex de recerca, eines de reproductibilitat i rebuts. Exclosos càmeres, PTP, `gphoto2`, captures, GUI física, build i LaunchServices.
- jpeg_result: 4.930 fitxers regulars, 1.927.335.912 B, moguts a `/Users/USUARI/.Trash/Eclipse_2026_JPEG_cleanup_2026-08-20T105346Z`; 4.930/4.930 SHA-256 i mides verificats al destí, cap fitxer no-JPEG al lot, zero JPEG als dos arbres per extensió i zero signatures JPEG entre 28.731 fitxers regulars finals.
- preservation: TIFF 459 fitxers / 40.665.466.222 B / fingerprint `cc3f47ec282ca111154eef81a86e78a921cd4180468ccad9a3cb38033f87ea9e`; RAW 5.281 / 149.046.489.190 B / fingerprint `d695f996c54df79a61953cf4424858d9152fb57bf9afce198253454478d09e42`; invariants abans/després.
- receipts: `output/cleanup/20260820T105346Z_jpeg_cleanup/` amb manifest SHA-256 per fitxer i `VALIDATION.md`; `output/cleanup/20260820T105346Z_project_hygiene/VALIDATION.md`; eina `research/tools/cleanup_project_jpeg.py`.
- hygiene: còpia orfe `de440s.bsp` byte-idèntica a la cau (SHA-256 `c1c7feea…`) moguda recuperablement a `/Users/USUARI/.Trash/Eclipse_2026_orphan_de440s_2026-08-20T105346Z.bsp`; loaders actius ara usen `EFEMERIDE`/cau explícita; `requirements_validated.txt` substitueix la instrucció cap a un fitxer inexistent.
- contradictions_fixed: V1.02 congelada i fase post-eclipsi; handoff del 10 marcat històric; PSB actual separat del rebut antic; duplicat research/81 renombrat i privat; link research/53 absent neutralitzat; research/70 marcat implementat; 0,662″ i σ(ε)=0,53 etiquetats correctament com a predicció/forecast, no detecció. `CLAUDE_STATUS.md` no s'ha editat i el seu titular contrari queda explícitament supersedit.
- evidence_boundary: acceptance astromètrica 22/22 reproduïda només a `_prova_skill_estrelles`; el path live per defecte conserva 4/22 checks i en té 18 no trobats. Cap dels dos resultats és una detecció relativista.
- qa: `git diff --check` PASS; AST 6/6; `comprova_entorn.py` acaba `Tot a punt`; deu versions del requirements coincideixen; DE440s carrega i `massa_aire(8,4)` passa; acceptance de prova 22✓/0✗/0 absent; selector final JPEG 0 i fingerprints TIFF/RAW invariants; 136/136 deletions tracked són JPEG i zero non-JPEG tracked deletions.
- safety: cap càmera, PTP, `gphoto2`, captura, GUI física, Eclipse Command, build ni LaunchServices; el comprovador no troba cap procés de captura viu. Moviments recuperables a Paperera, no esborrat permanent.

## PDF auditat del run real de l'eclipsi del 12 amb cobertura HDR — RELEASED

- status: RELEASED
- updated_utc: 2026-08-20T03:14:42Z
- acquired_utc: 2026-08-20T02:58:18Z
- released_utc: 2026-08-20T03:14:42Z
- serial_writes: RELEASED
- owner: null
- task: conservar en PDF l'informe auditat del run operatiu real de l'eclipsi, incorporant el grafic de cobertura HDR i l'annex foto a foto.
- scope: `output/pdf/`, `tmp/pdfs/` i aquest fitxer d'estat. Cap camera, PTP, `gphoto2`, captura, GUI fisica, build, LaunchServices ni original del run modificat.
- safety: worktree brut i artefactes originals preservats; generacio derivada, renderitzat integral i QA pagina per pagina abans del lliurament.
- result: `output/pdf/Informe_auditat_run_Eclipse_Command_20260812T202219.pdf`, A4 apaïsat, 19 pagines, 2.209.709 bytes, SHA-256 `2f243ef63d3d5da6758ec75ec8c4c0e0bcf9ac2d9540294dfc200e14297d90f0`.
- contents: portada i veredicte auditat; matriu ledger/JPEG/RAW; reconciliacio Sony i Canon; correccio explicita de `391 committed`, `0 missed` i `0 divergent exposures`; incidencies i pendents; cobertura HDR vectorial integrada; rebut SHA; annex complet de 377 files foto a foto.
- qa: `pdfinfo` 19 pagines A4, PDF 1.4 tagged i text extraïble; `qpdf --check` PASS; totes les pagines renderitzades a PNG i inspeccionades, sense retalls, solapaments, glifs defectuosos, pagines buides ni titols orfes; files finals Sony 153 i Canon 224 visibles; text clau i hashes PASS.
- invariance: SHA originals invariants — HTML `1d8958e8...a41ec`, Markdown `513a2e3d...b110`, SVG `6bf61a71...3f5d` i `mission_events.jsonl` `8ec67780...214`; intermedis propis eliminats. Les sessions headless propies s'han aturat explicitament; la sandbox no permet la comprovacio final amb `pgrep`.

## Correcció temporal v3 de les transicions de totalitat — RELEASED

- status: RELEASED
- updated_utc: 2026-08-19T20:44:41Z
- acquired_utc: 2026-08-19T19:47:25Z
- released_utc: 2026-08-19T20:44:41Z
- serial_writes: RELEASED
- owner: null
- task: eliminar les bandes de llum que avancen «a onades» quan entra i surt la totalitat, preservant intacte el tractament visual del tram central de la v2 i els 25 fps.
- scope: lectura immutable de l'original `/Users/USUARI/Desktop/Eclipse 2026/Eclipse2026-Video.MP4` i dels paquets v1/v2; pilots sota `/private/tmp`; paquet nou `/Users/USUARI/Desktop/Eclipse 2026/Video_Totalitat_Recuperada_v3`; aquest estat. No s'ha sobreescrit l'original, la v1 ni la v2.
- cause: la memòria recursiva `hqdn3d=5:4:14:10` de la v2 retardava els canvis foscos i feia que diferents blocs travessessin els pocs codis útils en moments diferents; l'HEVC no era la causa principal.
- method: dues branques contínues, `hqdn3d=5:4:1:1` durant els extrems i la recepta v2 `5:4:14:10` al centre; foses cosinus de 4 s en 16 bits. Frames `0–400` i `2192–2592` a `1:1`, `401–499` i `2093–2191` en fosa, i `500–2092` exactament amb la recepta central v2.
- result: retard robust contra la branca `1:1` de `0,000 s` per correlació LF i màxims de creuament `0,056/0,091 s`; W, ACF, foses i quatre juntes PASS. El tau escalar amb pendents de només `0,06 codi/s` queda honestament NO AVALUABLE pel terra de quantització, no com a fallada física; amb suport identificable i controls independents passa el gate de `0,30 s`.
- output: `/Users/USUARI/Desktop/Eclipse 2026/Video_Totalitat_Recuperada_v3/Eclipse2026_Totalitat_Transicions_Suaus_v3_4K_HEVC10.mov`, 121.055.830 bytes, SHA-256 `127e3e3cefbfb855addea0f76ad0b1a85de4c757e570d24fc5c36a4eeec6f655`; 103,720 s, 2.593 frames, 3840×2160 25 fps, HEVC Main 10 `hvc1` BT.709 + AAC 48 kHz estèreo. Paquet de 23 fitxers; `SHA256SUMS.txt` SHA-256 `21aba76409f48f9733a6cd4c9460104b18b303f6dd884fcbbc8c6968ebc37a79`.
- verification: manifest 22/22 entrades PASS després de copiar; descodificació integral vídeo+àudio PASS, zero errors; PTS exactes de 0 a 103,68 s en passos de 0,04 s; àudio vs font correlació `0,999931931` i lag 0 ms; centre contra v2 PSNR mitjà `96,402759 dB` i SSIM `1,000000`; compatibilitat QuickTime estructural PASS. Original, v1 i v2 conserven els SHA-256 canònics.
- safety: cap càmera, PTP, `gphoto2`, captura, GUI física, Eclipse Command, build ni LaunchServices; cap procés propi de vídeo queda actiu segons els controls disponibles, tot i que la sandbox no permet enumerar processos del sistema.

## Correcció conservadora v2 del vídeo de totalitat — RELEASED

- status: RELEASED
- updated_utc: 2026-08-19T19:38:36Z
- acquired_utc: 2026-08-19T19:13:26Z
- released_utc: 2026-08-19T19:38:36Z
- serial_writes: RELEASED
- owner: null
- task: reduir la claredat excessiva, els gradients visibles i la posterització de la v1, preservant un aspecte natural de la totalitat, Venus i l'halo coronal realment suportat pel vídeo.
- scope: lectura immutable de l'original `/Users/USUARI/Desktop/Eclipse 2026/Eclipse2026-Video.MP4` i de la v1; pilots sota `/private/tmp`; paquet nou `/Users/USUARI/Desktop/Eclipse 2026/Video_Totalitat_Recuperada_v2`; aquest estat. No sobreescriure ni l'original ni la v1.
- method: WB fixa `R×0,794 G×1,090 B×1,095`, denoise temporal fix, corba global conservadora (`0,01→0,012`, `0,02→0,026`), saturació 0,42, sense CAS/clarity/contrast local/debanding/gra/IA; HEVC Main 10 CRF12 amb `aq-mode=3` per protegir els codis foscos.
- result: el cel queda aproximadament a un terç de la mediana, rang i macrogradient de la v1 i pràcticament coincideix amb la referència directa processada; QA visual de gradients/macroblocs PASS. Venus i l'anell/halo ampli es conserven; zero estrelles addicionals reivindicades.
- output: `/Users/USUARI/Desktop/Eclipse 2026/Video_Totalitat_Recuperada_v2/Eclipse2026_Totalitat_Natural_v2_4K_HEVC10.mov`, 93.035.105 bytes, SHA-256 `b170617bfdfe4d2978dfabd120417199f8853e33b4b7c345a3a8d8125863c74c`; 103,720 s, 2.593 frames, 3840×2160 25 fps, HEVC Main 10 `hvc1` BT.709 + AAC 48 kHz estèreo. Paquet de 10 fitxers amb comparativa original/v1/v2, timeline, informes, script i manifest; `SHA256SUMS.txt` SHA-256 `3430e3fad49f369a8d62d7479aac7c2b909dc4beb9c894eca191cdcaae75731e`.
- verification: manifest 9/9 entrades PASS després de copiar; vídeo i àudio descodificats integralment, zero errors; `moov` abans de `mdat`; àudio vs font correlació 0,999931931 i lag 0 ms; original inode `135940053`, 7.340.208.783 bytes i mtime invariants; v1 inode `137609502`, 131.321.139 bytes i mtime invariant. Compatibilitat QuickTime estructural PASS; cap GUI oberta.
- safety: cap càmera, PTP, `gphoto2`, captura, GUI física, Eclipse Command, build ni LaunchServices.

## Recuperació de cel, corona i estrelles del vídeo A7III — RELEASED

- status: RELEASED
- updated_utc: 2026-08-19T17:18:34Z
- acquired_utc: 2026-08-19T16:45:46Z
- released_utc: 2026-08-19T17:18:34Z
- serial_writes: RELEASED
- owner: null
- task: augmentar claredat i textura del cel durant la totalitat del vídeo A7III i provar de recuperar corona o estrelles sense inventar senyal.
- scope: lectura immutable de `/Users/USUARI/Desktop/Eclipse 2026/Eclipse2026-Video.MP4`; pilots sota `/private/tmp`; paquet nou `/Users/USUARI/Desktop/Eclipse 2026/Video_Totalitat_Recuperada_v1`; aquest estat. Cap sobreescriptura de l'original ni dels derivats previs.
- method: vídeo amb denoise temporal fix, WB `R×0,794 G×1,090 B×1,095`, corba tonal global fixa, saturació 0,50 i exportació HEVC de 10 bits; branca científica de 380 mostres a 5 fps registrada subpíxel al cel/Sol, controls split-half, parell/senar, patró fix i injecció. Cap IA generativa, inpainting ni equalització local.
- safety: cap càmera, PTP, `gphoto2`, captura, GUI física, Eclipse Command, build ni LaunchServices.
- result: Venus demostrada i identificada per trajectòria + JPL DE440s; present 998/1000 mostres i moviment celeste d'uns 17 px durant totalitat. Zero estrelles/planetes addicionals validats. Corona defensable només com anell, silueta lunar i halo gruixut fins aproximadament r=28–32 px; detall azimutal fi rebutjat (`split-half r=0,125`).
- output: vídeo recomanat `Eclipse2026_Totalitat_Cel_Recuperat_v1_4K_HEVC10.mov`, 131.321.139 bytes, 103,720 s, 2.593 frames, 3840×2160, 25 fps, HEVC Main 10 BT.709 + AAC 48 kHz estèreo; SHA-256 `ad5a3d0fb61a83980ef32c9fad42dda559e95851da667d2bc9e44af3c79e9878`. Inclou apilat de cel 76 s, corona natural 4×, comparativa, README, scripts/CSV/JSON i manifest.
- sensitivity: injecció post-decode requantitzada a 8 bits: 0/6 a 0,5 codi de pic i 6/6 a 1 codi; no mesura senyal destruït pel còdec abans del decode.
- verification: manifest 12/12 PASS després de copiar; vídeo i àudio descodificats integralment; PNG/JPEG/CSV/JSON/scripts PASS. Original invariant: inode `135940053`, `7.340.208.783` bytes, mtime `2026-08-12T20:32:06+0200`, SHA-256 `e7eb709b429245c89005a4b32cec0493e9776b8e72861fa0c2a27a15f740c8fd`.

## Detecció de shadow bands al vídeo A7III — RELEASED

- status: RELEASED
- updated_utc: 2026-08-19T16:26:54Z
- acquired_utc: 2026-08-19T15:27:44Z
- released_utc: 2026-08-19T16:26:54Z
- serial_writes: RELEASED
- owner: null
- task: localitzar C2/C3 i buscar shadow bands sobre el llençol del vídeo A7III, amb una branca científica separada del màster de color.
- scope: lectura immutable de `/Users/USUARI/Desktop/Eclipse 2026/Eclipse2026-Video.MP4`; mostres, codi i pilots sota `/private/tmp`; derivats nous només sota `/Users/USUARI/Desktop/Eclipse 2026/Video_Shadowbands/`; aquest estat. Cap sobreescriptura ni transcodificació de l'original.
- method: estabilització del llençol, luminància/canal verd, detrend temporal i espacial fix, comparació amb controls fora del llençol i trams lluny dels contactes; cap WB automàtic ni normalització que pugui fabricar o cancel·lar bandes.
- safety: cap càmera, PTP, `gphoto2`, captura, GUI física, Eclipse Command, build ni LaunchServices.
- contacts: C2 físic `403,0 ±0,7 s` (`00:07:02:05`) i C3 físic `506,7 ±0,7 s` (`00:08:45:22–23`); àncores operatives `404,00/507,20 s`. El gran angular saturat no permet millorar aquesta precisió.
- result: NO DETECCIÓ DEMOSTRABLE; veredicte `INCONCLUSIU` sobre presència física. Zero blocs `383–393 s` amb acord Y/G simultani en geometria rectificada/nativa; el candidat `402–403 s` falla estabilitat angular i queda a `2,89–4,31` codis útils. Totalitat/post-C3 i el salt ISO `290,60–292,76 s` produeixen falsos patrons iguals o més forts.
- sensitivity: després de tornar a passos d'un codi de 8 bits, injecció cega `1–2%` = `0/6`; llindar optimista `6/6` de `3%` semiamplitud a `383–393 s` i `5%` a `393–403 s`, encara sense reencode H.264. No es poden excloure bandes reals més febles.
- output: paquet nou `/Users/USUARI/Desktop/Eclipse 2026/Video_Shadowbands/Analisi_Shadowbands_v1`, 27 fitxers amb informe, tres controls PNG, muntatge, vídeo exploratori, CSV/JSON, scripts i manifest; `MANIFEST_SHA256.txt` = `aa97d9fc104e00e4119c1857632937fa14bef91e7e86273c1c2c8a66ffa0e021`.
- verification: 26/26 entrades del manifest PASS després de copiar; vídeo exploratori `550/550` frames, `22,000 s`, `25 fps`, 512×256, descodificació integral PASS; PNG/CSV/JSON/scripts PASS. Original invariant: inode `135940053`, `7.340.208.783` bytes, mtime `2026-08-12T20:32:06+0200`, SHA-256 `e7eb709b429245c89005a4b32cec0493e9776b8e72861fa0c2a27a15f740c8fd`.

## Balanç de blancs vídeo shadow bands A7III — RELEASED

- status: RELEASED
- updated_utc: 2026-08-19T12:20:41Z
- acquired_utc: 2026-08-19T11:36:35Z
- released_utc: 2026-08-19T12:20:41Z
- serial_writes: RELEASED
- owner: null
- task: analitzar i ajustar el balanç de blancs del vídeo de l'eclipsi capturat amb la Sony A7III astromodificada i el Sigma 14 mm, preservant les shadow bands i l'original.
- scope: lectura de `/Users/USUARI/Desktop/Eclipse 2026/Eclipse2026-Video.MP4`; mostres i anàlisi sota `/private/tmp`; escriptura només de derivats nous de vídeo/QA sota `/Users/USUARI/Desktop/Eclipse 2026/` i d'aquest estat. Cap sobreescriptura del MP4 original.
- safety: cap càmera, PTP, `gphoto2`, captura, Eclipse Command, GUI física, build ni LaunchServices; l'original queda immutable i qualsevol transcodificació conserva l'àudio.
- result: creat `/Users/USUARI/Desktop/Eclipse 2026/Video_Shadowbands/Eclipse2026-Video_WB_documental_v1_ProRes422HQ.mov`, 53.281.189.052 bytes, ProRes HQ 4:2:2 de 10 bits, amb correcció fixa `R×0,794 G×1,090 B×1,095` i protecció estàtica de highlights. Comparativa i informe QA al mateix directori.
- verification: PASS estructural i descodificació integral; 602,400 s, 15.060/15.060 frames a 25 fps, 3840×2160, àudio PCM 48 kHz estèreo i timecode `00:00:19:05`; SHA-256 derivat `1c35edb27ebb87ab7c5eeaac05127348dd3c6ec5d691085125b8ced7ee6d9bab`.
- original: inode `135940053`, mida `7.340.208.783` i mtime `2026-08-12T20:32:06+0200` invariants; SHA-256 `e7eb709b429245c89005a4b32cec0493e9776b8e72861fa0c2a27a15f740c8fd`. La pista RTMD queda només a l'original perquè el remux MOV de prova no en preservava la semàntica de manera fiable.
- limit: màster documental, no calibració fotomètrica/espectral; l'anàlisi de shadow bands s'ha de derivar de l'original en luminància o canal verd, sense normalització fotograma a fotograma.

## Restauració dels darks Sony addicionals a 40 graus — RELEASED

- status: RELEASED
- updated_utc: 2026-08-15T16:18:30Z
- acquired_utc: 2026-08-15T16:16:31Z
- released_utc: 2026-08-15T16:18:30Z
- serial_writes: RELEASED
- owner: null
- task: recuperar de la Paperera tots els darks a 40 graus exactes dels shutters 1/4, 1, 2 i 8 s que s'havien apartat només pel sostre de 25.
- scope: `/Users/USUARI/.Trash/Sony_ARW_reserva_termica_2026-08-15_Tlg7PP`, `/Users/USUARI/Desktop/Eclipse 2026/Darks A7RIIIA Eclipse` i aquest estat. No tocar 1/8 s, shutters ràpids, FITS, càmera, PTP ni GUI.
- expected: restaurar 73 ARW: 10 de 1/4 s, 20 d'1 s, 24 de 2 s i 19 de 8 s; resultants 35/45/49/44, tots a 40 graus.
- result: restaurats els 73 ARW previstos; resultants 1/4 s = 35, 1 s = 45, 2 s = 49 i 8 s = 44, tots exactament a 40 graus. 1/8 s continua en 25 (12 a 39 graus i 13 a 40 graus).
- manifest: `/private/tmp/sony_trash_40c_non_eighth_73.paths.txt`, SHA-256 `ea90e4cf82b03d9f39d8d2ff2fac69aed7802cf914d185104bc61f2d0c629399`.
- verification: manifest 73/73 a origen, 0 a Paperera, 0 missing; origen 378 ARW, 7 FITS, zero JPEG i zero fitxers buits; el lot de reserva conserva 718 ARW i cap altre tipus, 61.233.797.120 bytes. Shutters ràpids intactes i cap càmera/PTP/GUI tocat.

## Selecció tèrmica final de 25 darks Sony per shutterspeed — RELEASED

- status: RELEASED
- updated_utc: 2026-08-15T16:14:05Z
- acquired_utc: 2026-08-15T16:07:27Z
- released_utc: 2026-08-15T16:14:05Z
- serial_writes: RELEASED
- owner: null
- task: conservar exactament 25 ARW per cadascun dels shutters Sony llargs 1/8, 1/4, 1, 2 i 8 s, prioritzant 40 graus i enviant la resta a la Paperera de manera recuperable.
- scope: `/Users/USUARI/Desktop/Eclipse 2026/Darks A7RIIIA Eclipse`, un lot nou sota `/Users/USUARI/.Trash` i aquest estat. No tocar shutters ràpids, FITS, càmera, PTP, `gphoto2`, captura ni GUI física.
- safety: preflight complet amb manifest keep/discard disjunts; 25 per grup; 1/8 conserva 13 a 40 graus i 12 a 39 graus, la resta conserva 25 a 40 graus; selecció temporalment distribuïda dins cada bin; cap esborrat permanent.
- result: 791 ARW llargs sobrants (67.459.517.440 bytes) moguts a `/Users/USUARI/.Trash/Sony_ARW_reserva_termica_2026-08-15_Tlg7PP`; queden 125 llargs, exactament 25 per shutter, més els 180 ràpids intactes, total 305 ARW i 7 FITS.
- thermal_selection: 1/8 s = 12 a 39 graus + 13 a 40 graus, mediana 40; 1/4, 1, 2 i 8 s = 25 a 40 graus exactes cadascun. ISO 100, 8000x5320, RAW descomprimit de 14 bits, APS-C off i LENR off.
- manifests: keep `e0a45cfc7ed7bf6c7ce8187e87e1257998976af8f4b19b164fb2f237fcb69585`; discard `f34a1a510b5a66191c32aac25f3c8061b4cdc9e33312a222bb09b3b552dbf575`; preserve-fast `74c9d96455be734dd13c40188a3bd9a3560e4f15f615852058dfc75e95bd9af5`.
- verification: keep 125/125 a origen, discard 791/791 a Paperera, preserve-fast 180/180 a origen, zero missing i zero interseccions; origen coincideix exactament amb keep+fast, zero JPEG i zero fitxers buits; Paperera conté només els 791 ARW. Cap càmera, PTP, procés de captura o GUI tocat.

## Rebaseline i neteja JPEG després del trasllat a Desktop/Eclipse 2026 — RELEASED

- status: RELEASED
- updated_utc: 2026-08-15T15:59:14Z
- acquired_utc: 2026-08-15T15:38:01Z
- released_utc: 2026-08-15T15:59:14Z
- serial_writes: RELEASED
- owner: null
- task: validar que el trasllat de les carpetes d'eclipsi ha acabat, retirar els JPEG reintroduïts i fixar un baseline abans d'una nova ronda de darks.
- scope: `/Users/USUARI/Desktop/Eclipse 2026`, dos lots recuperables sota `/Users/USUARI/.Trash` i aquest estat. Cap càmera, PTP, `gphoto2`, captura, APP/GUI física, build ni LaunchServices.
- result: còpia estable en dos snapshots, zero fitxers de 0 bytes; 938 JPEG Sony (327.090.176 bytes) moguts a `/Users/USUARI/.Trash/JPEG_Sony_reintroduits_2026-08-15_Dg2zst`; 303 ARW incompatibles amb Eclipse Command moguts a `/Users/USUARI/.Trash/Sony_ARW_descart_EC_2026-08-15_xreHKL` (187 a 1/2 s, 16 a 6 s i 100 APS-C/ISO incompatible).
- audit: queden 1.096 ARW Sony validats i zero JPEG fotogràfics; el lot nou canònic és de 378 ARW, tot ISO 100/full-frame/RAW 14-bit/LENR off, 38-41 graus, amb zero senyal del reflex antic. Els 257 antics reintroduïts compatibles també han superat la prova lineal de reflex.
- verification: `sony_invalid_ec_303.txt` = 0 a origen/303 a Paperera; `sony_new_ec_378.txt` = 378 a origen; `sony_old_compatible_quarantine_257.txt` = 257 a origen; cap duplicat SHA-256 entre els 1.399 ARW pre-neteja; cap RAW útil mogut. No s'ha iniciat cap procés de càmera o GUI.

## Eliminació reversible global JPEG de darks i captures d'eclipsi — RELEASED

- status: RELEASED
- updated_utc: 2026-08-15T15:16:39Z
- acquired_utc: 2026-08-15T15:15:35Z
- released_utc: 2026-08-15T15:16:39Z
- serial_writes: RELEASED
- owner: null
- task: retirar tots els fitxers regulars `.jpg`/`.jpeg` independents de les carpetes de darks i captures d'eclipsi de l'Escriptori perquè el flux treballi només amb RAW.
- scope: `Darks A7RIIIA Eclipse`, `Darks Canon R6III Eclipse`, `Eclipse 2026 300mm`, `Eclipse Vixen`, `Eclipse Vixen Unfiltered` i `6D Eclipse 2026`, recursivament; lot recuperable sota `/Users/USUARI/.Trash` i aquest estat. `Eclipse meteo` queda fora perquè el seu JPEG és evidència meteorològica, no captura.
- safety: només fitxers regulars per extensió case-insensitive `.jpg`/`.jpeg`, sense seguir symlinks; no tocar ARW/CR3/CR2/FITS, previews incrustades ni altres carpetes de l'Escriptori; cap esborrat permanent.
- audit: cinc de les sis arrels ja tenien zero JPEG; els únics 124 eren previews sRGB derivats, tots dins `Eclipse Vixen Unfiltered/Calibrated_Claude/previews_sRGB`, 23.741.292 bytes, sense cap fitxer no-JPEG al directori.
- result: la carpeta `previews_sRGB` sencera s'ha enviat a `/Users/USUARI/.Trash/JPEG_eclipsi_i_darks_2026-08-15_Xa7Gea`; lot recuperable amb 124 JPEG, zero fitxers d'altres tipus i bytes exactes.
- verification: les sis arrels queden amb zero `.jpg`/`.jpeg`; romanen 4.856 RAW (461 ARW Sony dark, 768 CR3 Canon dark, 194 ARW Sony eclipsi, 247+124 CR3 Vixen i 3.062 CR2 6D) i 23 FITS de masters. El JPEG `Eclipse meteo/evidencia_roses_20260808T1718Z.jpg` no s'ha tocat perquè és evidència meteorològica, no captura.

## Neteja reversible darks Sony del lot 15-08 — RELEASED

- status: RELEASED
- updated_utc: 2026-08-15T15:13:30Z
- acquired_utc: 2026-08-15T15:09:32Z
- released_utc: 2026-08-15T15:13:30Z
- serial_writes: RELEASED
- owner: null
- task: enviar a la Paperera els darks Sony del lot nou que no poden servir per calibrar l'eclipsi i tots els JPEG nous, conservant els RAW tèrmicament o científicament potencialment útils.
- scope: `/Users/USUARI/Desktop/Darks A7RIIIA Eclipse`, un lot recuperable nou sota `/Users/USUARI/.Trash` i aquest fitxer d'estat. Cap càmera, PTP, `gphoto2`, captura, APP/GUI física, build ni LaunchServices.
- safety: manifest exacte i verificació independent abans del moviment; cap esborrat permanent; no tocar els ARW antics ni els 7 FITS existents; worktree brut preservat.
- result: 436 ARW (36.256.429.568 bytes) i 529 JPEG (208.863.232 bytes), total 965 fitxers / 36.465.292.800 bytes, enviats a `/Users/USUARI/.Trash/Darks_Sony_descartats_2026-08-15_EvhWE7` en subcarpetes `ARW` i `JPEG`.
- discarded_arw: 19 APS-C incompatibles; 15 amb ISO incorrecte; 1 únic de 4 s no canònic; 20 de 1/8 s, 56 de 1/4 s i 154 d'1 s massa calents; 89 de 2 s a 42–45 °C; 82 de 8 s a 43–45 °C. Categories exclusives, suma 436.
- kept_new: `DSC09160–DSC09252`, 93 ARW / 7.931.397.120 bytes: 38 de 8 s a 36–40 °C i 55 de 2 s a 40–41 °C, tots ISO 100, 8000×5320 i ILCE-7RM3A. Empremta ruta+inode+mida abans/després `3ac1e9c59fecc76f1c130cf8acc11a33a51ea376afc6655bafcdcf334ac25f2e`.
- verification: origen amb 461 ARW, zero JPEG i 7 FITS recursius; zero candidats del manifest encara presents. Paperera amb 436 ARW i 529 JPEG i bytes exactes. Cap procés de càmera iniciat per Codex; la sandbox no permet enumerar processos aliens.

## Eliminació reversible JPG dels originals d'eclipsi — RELEASED

- status: RELEASED
- updated_utc: 2026-08-14T19:27:53Z
- acquired_utc: 2026-08-14T19:25:55Z
- released_utc: 2026-08-14T19:27:53Z
- serial_writes: RELEASED
- owner: null
- task: enviar a la Paperera tots els JPG/JPEG de `Eclipse Vixen` i `Eclipse 2026 300mm`, sense tocar cap RAW.
- scope: `/Users/USUARI/Desktop/Eclipse Vixen`, `/Users/USUARI/Desktop/Eclipse 2026 300mm`, un lot recuperable nou sota `~/.Trash` i aquest fitxer d'estat. Cap càmera, PTP, `gphoto2`, captura, APP/GUI física, build ni LaunchServices.
- safety: selecció estricta de fitxers regulars per extensió case-insensitive `.jpg`/`.jpeg`, sense seguir symlinks; inventari previ de 0 JPG a Vixen i 190 JPG a 300mm; 247 CR3 i 194 ARW fora de la selecció; verificació posterior obligatòria.
- result: 190 JPG de `DSC06932.JPG` a `DSC07121.JPG`, 91.815.936 bytes, moguts a `/Users/USUARI/.Trash/JPG Eclipse Vixen i Eclipse 2026 300mm 2026-08-14T192555Z`; `Eclipse Vixen` ja en tenia zero.
- verification: queden zero JPG/JPEG als dos directoris i el lot de Paperera conté 190 JPG i zero RAW. Els 247 CR3 (5.287.585.932 bytes) i 194 ARW (16.552.478.720 bytes) conserven exactament les empremtes prèvies de ruta, inode i mida `53b4a336...` i `7d1562ae...`.

## Neteja tèrmica reversible darks Canon i Sony — RELEASED

- status: RELEASED
- updated_utc: 2026-08-14T18:52:01Z
- acquired_utc: 2026-08-14T18:45:50Z
- released_utc: 2026-08-14T18:52:01Z
- serial_writes: RELEASED
- owner: null
- task: enviar a la Paperera els darks Canon massa calents del lot nou i rescanejar Sony per aplicar-hi el mateix procés tèrmic acordat.
- scope: `/Users/USUARI/Desktop/Darks Canon R6III Eclipse`, `/Users/USUARI/Desktop/Darks A7RIIIA Eclipse`, lots recuperables a `~/.Trash` i aquest fitxer d'estat. Cap càmera, PTP, `gphoto2`, captura, APP/GUI física, build ni LaunchServices.
- safety: manifest exacte i recompte previ abans de cada moviment; cap esborrat permanent; worktree brut preservat.
- canon_result: 99 CR3 a 45–46 °C enviats a `/Users/USUARI/.Trash/Darks Canon massa calents 45-46C 2026-08-14`; en queden 768 i l'escaneig posterior dona zero fitxers a 45 °C o més.
- sony_audit: 169 ARW nous `DSC08428–DSC08596`, tots ISO 100 i 25–38 °C; zero massa calents amb el tall acordat de 43 °C o més. Els nous incloïen 169 JPEG i 21 ARW a 1/2 s, fora de la seqüència Eclipse Command.
- sony_result: 169 JPEG i 21 ARW a 1/2 s enviats a `/Users/USUARI/.Trash/Darks Sony nous fora politica 2026-08-14`, en subcarpetes separades. Queden 368 ARW, zero JPEG, zero 1/2 s, zero ARW a 43 °C o més i 7 MasterDarks FITS antics intactes.
- verification: Sony per exposició `1/6400=36, 1/800=36, 1/400=52, 1/100=36, 1/30=20, 1/8=58, 1/4=46, 1s=22, 2s=27, 8s=35`; Canon 768 CR3. Manifestos temporals amb SHA-256 `98905a5e...`, `b47bb402...` i `00b1c11f...`.
- thermal_limit: els Sony nous no són massa calents, però els llargs són molt més freds que els 40 °C de l'eclipsi: 1 s 31–33 °C, 2 s 27–31 °C i 8 s 25–27 °C; conservar-los no equival a declarar-los tèrmicament ideals per calibratge.

## Eliminació reversible darks Sony > 1/4 s — RELEASED

- status: RELEASED
- updated_utc: 2026-08-14T18:28:13Z
- acquired_utc: 2026-08-14T18:26:31Z
- released_utc: 2026-08-14T18:28:13Z
- serial_writes: RELEASED
- owner: null
- task: enviar a la Paperera tots els ARW Sony A7RIIIA i MasterDarks APP amb exposició estrictament superior a 1/4 s; conservar 1/4 s i més ràpids.
- scope: `/Users/USUARI/Desktop/Darks A7RIIIA Eclipse` i aquest fitxer d'estat. Cap càmera, PTP, `gphoto2`, captura, GUI física, build ni LaunchServices.
- result: 57 ARW enviats a la Paperera —19 d'1 s, 20 de 2 s i 18 de 8 s— més els tres MasterDarks FITS d'1, 2 i 8 s. Batch recuperable: `/Users/USUARI/.Trash/Darks Sony mes de 0.25s 2026-08-14`.
- verification: queden 220 ARW amb exposicions de 1/4 s o més ràpides i 7 MasterDarks; l'escaneig EXIF posterior no troba cap ARW amb `ExposureTime > 0.25`.

## Pipeline de postprocessat corona 2026 — RELEASED

- status: RELEASED
- updated_utc: 2026-08-14T01:13:29Z
- acquired_utc: 2026-08-14T00:16:16Z
- released_utc: 2026-08-14T01:13:29Z
- serial_writes: RELEASED
- owner: null
- task: recerca Druckmuller, auditoria read-only dels RAW, contrast amb Claude
  i OpenRouter, i informe PDF breu de maxim quatre pagines.
- scope: recerca i artefactes de postprocessat; informe final a `output/pdf/`
  i aquest fitxer d'estat. No cameras, PTP, `gphoto2`, captures, GUI fisica,
  LaunchServices ni modificacio dels originals de l'Escriptori.
- safety: originals i worktree brut preservats; qualsevol derivat analitic es
  crea fora de les carpetes font o sota un directori nou i auditable.
- result: pipeline pilot-only de sis gates amb dos masters lineals per cos,
  registre corona/Lluna separat, decoder dual, branca sense flat, HDR float64,
  model PSF/halo, controls d'injeccio i radi de validesa. No comprar MATLAB
  ara; la col.laboracio directa amb Druckmuller te mes retorn.
- dataset: nucli 154/154 RAW present (121 Canon + 33 Sony); carpetes actuals
  247 CR3 Canon i 178 ARW + 178 JPG Sony. `DSC06990` exclosa per moviment.
- review: Claude Fable 5 Extra i Opus 5 Extra, 2/2 consens `APPROVE WITH
  CHANGES`; panel OpenRouter de vuit llinatges, 8/8 `APPROVE WITH CHANGES` i
  8/8 `DEFER MATLAB`.
- openrouter: `zdr=false`, `data_collection=allow` sota autoritzacio explicita;
  cap RAW enviat. Cost de la ronda completa, reintents inclosos: 0.33052390 USD.
- pdf: `output/pdf/Informe_pipeline_postprocessat_eclipsi_2026.pdf`, A4 4/4
  pagines, 87.127 bytes, SHA-256
  `de0ad373640e2f27cfa1f8f6c2e8b3a6a860be4c59d30ead5256c37a93a2adaf`.
- qa: `pdfinfo` 4 pagines; text extractable; `qpdf --check` PASS; render 150 dpi
  i inspeccio visual pagina per pagina PASS.
- processes: zero processos de camera iniciats per Codex. Continua visible el
  servei macOS preexistent `/usr/libexec/ptpcamerad`; no s'ha tocat.
- touched: `.coordination/CODEX_STATUS.md`, `tmp/pdfs/` i `output/pdf/`.

## Mirador actiu al mode Satel.lit — RELEASED

- status: RELEASED
- updated_utc: 2026-08-12T14:57:00Z
- acquired_utc: 2026-08-12T14:50:00Z
- released_utc: 2026-08-12T14:57:00Z
- serial_writes: RELEASED
- owner: null
- task: evitar que el mode Satel.lit torni silenciosament a PROVA — Roses;
  obrir-lo a MIRADOR FINAL 2 i fer inequívoc el punt que alimenta les dades.
- scope: generador i HTML de `~/Desktop/Eclipse meteo/`, copia Dropbox i
  aquest estat.
- cause: els finals eren seleccionables, pero `D12.punt` arrencava a null i
  `omplePuntsD12()` triava sempre el primer element, `PROVA — Roses`, a cada
  carrega. El canvi manual si funcionava i retornava dades de FINAL 2.
- result: Satel.lit s'obre i es recarrega a `MIRADOR FINAL 2`; el cap de la
  seccio mostra sempre `Mode dia 12 · <punt actiu>`. FINAL 1 i FINAL 2 canvien
  correctament el nom i les dades.
- browser_qa: PASS. Carrega inicial selecciona FINAL 2, mostra totalitat
  103,8 s, azimut 282 graus, K 0,90 i el fotograma EUMETSAT 14:30 UTC;
  selector FINAL 1 -> FINAL 2 actualitza els dos caps correctament.
- validation: JavaScript PASS als tres HTML; web local i Dropbox sincronitzats.
- hashes: web local
  `f9efc4a0bad18c7d7ba645b981dfdce190c4c8cf88afd776a173bcefbb5c4293`;
  generador `5d8988b553a5f79367bc184c9f01359df1045c3cc95e3d2b009fb2f8434fc923`;
  index Dropbox `c50965750a14504f1b826d39b48e347e5e407050ae273f19f94e79ef25e427af`.
- exclusions: cap camera, PTP, `gphoto2`, captura, GUI fisica de camera,
  KMZ, dades meteorologiques, build o LaunchServices.

## Finals visibles a Satel.lit i AEMET — RELEASED

- status: RELEASED
- updated_utc: 2026-08-12T14:34:00Z
- acquired_utc: 2026-08-12T14:25:00Z
- released_utc: 2026-08-12T14:34:00Z
- serial_writes: RELEASED
- owner: null
- task: garantir que MIRADOR FINAL 1 i 2 surtin sempre al selector Satel.lit
  i siguin inequivocament visibles als mapes AEMET.
- cause: Satel.lit filtrava per temps de la base activa; els finals nomes
  tenen ruta B_Medina i desapareixien amb Delta/Ferrol. AEMET els tenia al
  JSON pero amb radi ordinari de sis pixels.
- result: Satel.lit posa FINAL 1 i FINAL 2 sempre al principi del selector,
  independentment de Medina, Delta o Ferrol. AEMET els pinta a tots dos mapes
  amb radi 10, vora lila fosca de 3 px i etiqueta permanent.
- browser_qa: PASS real sobre localhost. Medina mostra 24/79 min; Delta i
  Ferrol mostren els dos finals encara sense ruta pròpia. AEMET mostra dues
  etiquetes finals a cadascun dels dos mapes.
- consistency: text operatiu corregit de 95 a 97 miradors finals. Web local,
  index i HTML Dropbox coherents; JavaScript PASS; KMZ no modificat.
- hashes: web
  `6df420d4cdf7f7b0e41c6a0e1c12a7211789c198dffbff7c1ac7c8dc2eb70b50`;
  generador `f27ecf91defa1f6edeb882ce7ac46fcaeb3f3f12c74a4bfd0283a905920fa3c1`;
  index Dropbox `c94e2bcac98cf90ed842b3242119857ba25aeb6ee008080c5717ed5ca6e10f8b`.
- exclusions: cap camera, PTP, `gphoto2`, captura, GUI fisica de camera,
  build, LaunchServices, canvi meteorologic o canvi del KMZ.

## MIRADOR FINAL 2 i reassignacio lila/verd — RELEASED

- status: RELEASED
- updated_utc: 2026-08-12T14:16:00Z
- acquired_utc: 2026-08-12T14:05:00Z
- released_utc: 2026-08-12T14:16:00Z
- serial_writes: RELEASED
- owner: null
- task: afegir MIRADOR FINAL 2 a 42.299407,-5.02503; deixar nomes FINAL 1
  i FINAL 2 en lila i passar tots els antics liles a verd; refer KMZ i web.
- scope: `~/Desktop/FINAL2026.kmz`, `~/Desktop/Eclipse meteo/`, Dropbox i
  aquest estat.
- safety: treball temporal, backups abans d'instal.lar, meteo completa del
  nou punt i validacio de colors de punts i raigs.
- result: FINAL 2 a cota model 798 m, 103.8 s de totalitat, C2 20:28:45 i
  C3 20:30:29 CEST; OSRM 79 min i 57.4 km de Medina. Punt i raig de 41 nodes.
- colors: nomes FINAL 1 i FINAL 2 conserven estil lila, punts i raigs. Els
  cinc antics liles/top (Aralla, Ancares, Cueto Negro, Mont Caro i Sotillos)
  son verds al KMZ, ranquing, AEMET i contaminacio luminica.
- weather: FINAL 2 amb cinc ensembles, sis posicions, falca, capes, AOD i
  pols; cache 45/45.
- web: 45 files, 78 punts AEMET i 97 punts de contaminacio luminica;
  JavaScript PASS; local i Dropbox coherents.
- validation: KMZ ZIP/CRC PASS amb 195 punts i 98 LineStrings; KMZ Dropbox
  byte a byte identic. Backups previs a `.backups/*20260812T1359Z*`.
- hashes: KMZ
  `6977f24384bc97d9e18affeb0f0decc5711b17bc4546adcf2b3e9ecd39f8fe8a`;
  web `def09e1fa16fa69ff6027cce12ceb866f99c9902a91443e8d1cc86e932527b08`;
  cache `4c1d5e5c751eadf2b2bbf9b5603991af0bf5d0762fc35736f08cd2b345c37ebf`;
  index Dropbox `0a2b05bac377f9399268c62189eaefed3e118b8c26c88f4a093194a57d7c467a`.
- limit: cota i raig son model/astronomia, no certificacio LIDAR ni visual
  d'arbres/edificis; comprovar l'horitzo O-NO al lloc.
- exclusions: cap camera, PTP, `gphoto2`, captura, GUI fisica de camera,
  build o LaunchServices.

## Nou MIRADOR FINAL 1 i actualitzacio integral — RELEASED

- status: RELEASED
- updated_utc: 2026-08-12T13:56:00Z
- acquired_utc: 2026-08-12T13:42:00Z
- released_utc: 2026-08-12T13:56:00Z
- serial_writes: RELEASED
- owner: null
- task: afegir `MIRADOR FINAL 1` a 42.0635, -5.19044 al KMZ final i a tots
  els apartats web, amb raig solar i meteo completa.
- scope: `~/Desktop/FINAL2026.kmz`, `~/Desktop/Eclipse meteo/`, copia Dropbox
  i aquest estat.
- result: punt a cota model 766 m, totalitat 95.9 s, C2 20:29:14 i C3
  20:30:50 CEST, Sol 9.03 graus / azimut 281.82 graus; OSRM 24 min i 24.5 km
  des de Medina. Raig astrononomic de 41 nodes afegit al KMZ.
- weather: registre nou complet amb cinc ensembles, sis posicions, falca,
  capes baixes/mitjanes/altes, AOD i pols; cache 44/44.
- web: 44 files al ranquing, 77 punts als mapes AEMET i 96 al mapa de
  contaminacio luminica. `MIRADOR FINAL 1` present exactament una vegada a
  cada apartat. JavaScript PASS.
- correction: `nuvols_aemet.py` llegeix ara `FINAL2026.kmz`, la mateixa font
  que obre el boto web; el canonic vell ja no podia representar el nou punt
  ni el filtre final.
- backups: KMZ anterior i cache/fonts anteriors preservats a
  `~/Desktop/Eclipse meteo/.backups/*_20260812T1351Z_pre_mirador_final_1.*`.
- hashes: KMZ nou
  `8ea5ec9e123c0524f7bd652b2fadae3491d0595b7754d6f5b2374419b14b69d0`;
  web local `f28ac9d723bfb8496870e564ee72e8d4b4d296515e7da6ce6c8c770744fcbea6`;
  cache `5f38ebecbe5a0a2beede2d95e7adac700c045d4f42a63a4f9e075e75d9e01314`;
  index Dropbox `ff591291b6dc1d52a1e731812e8becd2f28bde70ca8a1f4bf621a2974c92763b`.
- validation: KMZ ZIP/CRC PASS, 194 punts i 97 LineStrings, local/Dropbox
  coherents, KMZ Dropbox byte a byte identic.
- limit: el raig es la direccio astronomica, no una certificacio LIDAR de
  l'horitzo; arbres, edificis i vista real O-NO s'han de comprovar al lloc.
- exclusions: cap camera, PTP, `gphoto2`, captura, GUI fisica de camera,
  build o LaunchServices.

## Refresc meteo de tots els miradors excepte Ferrol — RELEASED

- status: RELEASED
- updated_utc: 2026-08-12T12:08:00Z
- acquired_utc: 2026-08-12T11:56:00Z
- released_utc: 2026-08-12T12:08:00Z
- serial_writes: RELEASED
- owner: null
- task: tornar a descarregar les dades meteorologiques i de particules dels
  miradors de la web final, excepte qualsevol registre associat a Ferrol.
- scope: `~/Desktop/Eclipse meteo/`, copia de Dropbox i aquest bloc d'estat.
- safety: congelar byte-semanticament els dos registres Ferrol, construir el
  cache nou a `/tmp`, validar-lo complet abans de substituir res i preservar
  `~/Desktop/FINAL2026.kmz` immutable.
- exclusions: cap camera, PTP, `gphoto2`, captura, GUI fisica de camera,
  build, registre de l'app o LaunchServices; cap canvi al KMZ.
- result: 41/41 registres no-Ferrol descarregats de nou entre 11:56 i 12:04
  UTC, cadascun amb cinc ensembles, sis punts de falca, capes baixes/mitjanes/
  altes, AOD i pols. Els dos registres Ferrol (`HOTEL` i traca) es conserven
  semanticament identics als del cache anterior.
- backup: cache anterior preservat a
  `~/Desktop/Eclipse meteo/.backups/cache_meteo_miradors_20260812T1156Z_pre_refresh_sense_ferrol.json`,
  SHA-256 `f794a3e81651932ea99e6433a6937c3d1585a746186f614e52bea5ca95f9e7fe`.
- validation: cache 43/43 complet, ordre web-cache exacte, JavaScript PASS,
  Dropbox cache byte a byte identic i HTMLs autoportants de 43 files PASS.
- hashes: cache nou
  `5ea794e336afd404e3d832480f28588d612311449f4841006da8f36becd4e88d`;
  web local `2aa20895fdc645703d66e7fed4184def7a9ba67f1b624a335ea2656fc73bde50`;
  index Dropbox `ac786fb3dd01c7a30cd3bddf330a4872684f2187ec92d9ec89b137b3ead96d54`.
- immutabilitat: `~/Desktop/FINAL2026.kmz` i copia Dropbox continuen identics,
  SHA-256 `fddab2b44b0c8570d7b86e97bc956251f28f3cbb8d31acd9a08d150b1ec28ad6`.
- limit: el port local 8765 no escoltava al QA final; cal reobrir/recarregar
  la web des del fitxer o tornar a iniciar el servidor local per veure el nou
  contingut a la pestanya antiga.

## Operacio final meteo, AEMET, filtre KMZ i riscos — RELEASED

- status: RELEASED
- updated_utc: 2026-08-12T10:47:00Z
- acquired_utc: 2026-08-12T08:07:15Z
- released_utc: 2026-08-12T10:47:00Z
- serial_writes: RELEASED
- owner: null
- task: incorporar l'ultim butlleti AEMET, eliminar de la web els miradors amb
  nuvol potencialment bloquejant dins la falca solar, crear `FINAL2026.kmz`,
  refrescar meteo i particules dels supervivents i auditar riscos de ruta.
- scope: `~/Desktop/Eclipse meteo/`, `~/Desktop/FINAL2026.kmz`, copia de
  Dropbox, recerca web actual i aquest bloc d'estat.
- safety: preservar canvis previs i cache vell fins que el nou sigui complet;
  no tocar el KMZ canonic; filtre auditable sobre la falca real cap al Sol;
  respectar el ritme d'Open-Meteo i prioritzar fonts oficials actuals.
- exclusions: cap camera, PTP, `gphoto2`, captura, GUI fisica de camera,
  build, registre de l'app o LaunchServices; cap canvi al KMZ.
- aemet: butlleti final 12/08/2026 11:50 CEST, HARM 00 UTC H+18 i
  ENS-IFS valids a les 20:00 CEST. Dos mapes peninsulars reprojectats amb QA
  de reixa 1430/1570 i 1658/1848 punts a menys d'un pixel.
- filtre: regla auditada sobre la falca solar: nuvol baix/mitja >=13 % o alt
  dens >=64 %. Dels 99 punts canonics, 4 exclosos i 95 conservats: km 700
  Mirador de Galeria, Cinctorres, Olocau-Tronchon i Cabanas de Juarros.
- kmz: l'original queda immutable amb SHA-256
  `55f24954789b1dffbce74bcaacd5d60e6f8e9730889846a7ca4874fe9c193380`.
  `~/Desktop/FINAL2026.kmz` te 4 punts i 3 raigs menys; Cabanas no tenia
  raig. ZIP/CRC/XML PASS, 282 Placemarks, SHA-256
  `fddab2b44b0c8570d7b86e97bc956251f28f3cbb8d31acd9a08d150b1ec28ad6`.
- weather: 45/45 miradors font descarregats sequencialment; despres del filtre
  en queden 43/43 al cache final, tots amb cinc conjunts, falca, sis mostres
  de capes, AOD i pols superficial CAMS. Cache SHA-256
  `f794a3e81651932ea99e6433a6937c3d1585a746186f614e52bea5ca95f9e7fe`.
- web: 43 files totals i 19 dins 3 h 05 de Medina, 95 punts al mapa de
  contaminacio luminica, 76 als mapes AEMET, filtre i avis operatiu visibles,
  pols superficial explicitada i boto al KMZ final. HTML SHA-256
  `8af080d328ee0a3ac057108cf3fded5e347e2e0947484e357bef138a65b36385`.
- transit: snapshot DGT/INFORCYL revalidat 12:44 CEST. Persistien els talls
  VA-913, A-52, A-6 Becerrea-Pedrafita i A-67; Valtuille controlat pero no
  extingit; incident AP-66 ja no actiu. Avis volatil integrat a la web.
- dropbox: `Pere Guerra/Eclipse meteo/index.html` normalitzat nomes per fer
  l'enllac `FINAL2026.kmz` autoportant. Web, generador, cache, filtre, mapes
  AEMET i KMZ final copiats; KMZ byte a byte identic. Index SHA-256
  `4fbf9c4fb0e87f60e89ae7d7d861f79d93e77974cf156277ad835343d01a6c92`.
- validation: JavaScript PASS; 43/43 cache complet; absencia dels 4 exclosos
  a llista/mapes PASS; navegador real PASS amb dos mapes AEMET i pols CAMS;
  iPhone 393x852 sense overflow; servidor temporal aturat i zero processos.

## Mapa de contaminacio luminica natiu — RELEASED

- status: RELEASED
- updated_utc: 2026-08-11T22:05:11Z
- acquired_utc: 2026-08-11T21:58:47Z
- released_utc: 2026-08-11T22:05:11Z
- serial_writes: RELEASED
- owner: null
- task: substituir el visor extern amb pins per un mapa web Leaflet com els
  mapes AEMET, mantenint els 99 miradors com a cercles web interactius.
- scope: generador i HTML de `~/Desktop/Eclipse meteo/`, actiu local de la
  capa Sky Brightness 2025, copia iPhone de Dropbox i aquest bloc d'estat.
- safety: preservar tots els canvis previs de Pere i Claude; no refrescar
  meteorologia, no alterar el KMZ canonic i no contactar cap camera.
- exclusions: cap camera, PTP, `gphoto2`, captura, GUI fisica de camera,
  build, registre de l'app o LaunchServices.
- result: l'iframe oficial i els pins vermells han desaparegut. El mode usa
  un mapa Leaflet natiu amb fons clar, relleu o satel.lit, capa local Sky
  Brightness 2025 i 99/99 cercles amb el color del KMZ, nom, tooltip i popup.
- navegacio: selector de 99 punts i boto `Centra'l al mapa`; San Vicente
  Martir de Colle comprovat com a punt 99, amb popup i zoom 11.
- capa: fotografia WMS georeferenciada 1600x1000, bounds
  `39.143831,-8.58029` a `43.83623,1.29678`, opacitat 68 %, atribucio visible
  a Jurij Stare/lightpollutionmap.info i NASA Black Marble. Actiu i metadades
  a `cau_llum/`; no hi ha connexio WMS en obrir la web.
- compatibilitat: els quatre modes funcionen; AEMET conserva 2/2 mapes i 78
  punts; contaminacio luminica conserva els 99 punts. QA a 393x852 confirma
  la reixa d'eines apilada i el mapa dins l'amplada de l'iPhone.
- dropbox: `Pere Guerra/Eclipse meteo/index.html`, `miradors_local.html`,
  generador i `cau_llum/` actualitzats. L'index carrega 99 opcions, un mapa i
  el PNG 1600 px; l'enllac KMZ apunta al fitxer local de la carpeta.
- immutabilitat: cache meteorologic i KMZ no han canviat. SHA-256 cache
  `c15a51aad35d4ae030b378eb37d59e0f79f72c6dd4bd2bbce43e83c9b5dd2091`;
  KMZ `55f24954789b1dffbce74bcaacd5d60e6f8e9730889846a7ca4874fe9c193380`.
- validation: Python/regeneracio amb dependencies completes PASS; JavaScript
  PASS; cap `iframe`, estat de pins o Mercator antic; QA visual desktop,
  centrat de Colle i iPhone PASS; copia Dropbox normalitzada byte a byte;
  `git diff --check` PASS; pestanyes, fitxer QA i ports 8774-8775 tancats.
- hashes: generador
  `4867fc8b9144ad8d58304428453243c2032d9b47c89f0bbb533509a4caa054b6`;
  HTML font
  `852d4f4ec9830fa10b16ad452fab7c688c51a3af048d22ea3706afa5d64321d3`;
  PNG `c6521f44f94a5ba59e3aee37faec95c2e1b9c6fd1ecccb4248cb8e4dec4a97d1`;
  index Dropbox
  `8e9168ec2afb9d67e057bb13f05f1037eac8c97e177bca5a86966b2dd0dc1a31`.

## Mapa de contaminacio luminica amb tots els miradors — RELEASED

- status: RELEASED
- updated_utc: 2026-08-11T21:50:05Z
- acquired_utc: 2026-08-11T21:39:42Z
- released_utc: 2026-08-11T21:50:05Z
- serial_writes: RELEASED
- owner: null
- task: afegir a la web un apartat que superposi tots els miradors del KMZ
  canonic sobre la capa Sky Brightness 2025 de lightpollutionmap.info.
- scope: generador i HTML de `~/Desktop/Eclipse meteo/`, copia iPhone de
  Dropbox i aquest bloc d'estat.
- safety: preservar tots els canvis previs de Pere i Claude; usar el mapa
  oficial incrustat amb marcadors persistits a l'URL i atribucio completa,
  sense reutilitzar el WMS privat ni refrescar dades meteorologiques.
- exclusions: cap camera, PTP, `gphoto2`, captura, GUI fisica de camera,
  build, registre de l'app o LaunchServices; cap canvi al KMZ canonic.
- result: mode nou `Contaminacio luminica` amb els 99/99 miradors puntuals
  del KMZ, inclosos tots els colors i San Vicente Martir de Colle. Els pins
  son numerats i el selector relaciona numero, nom, categoria i coordenades;
  cada punt te un enllac que obre la vista oficial centrada.
- capa: Sky Brightness 2025 al 60 %, exactament la vista aportada per Pere.
  El mapa oficial queda incrustat amb els marcadors persistits al `state` de
  la seva URL. Atribucio visible a Jurij Stare/lightpollutionmap.info i NASA
  Black Marble. No s'ha hotlinkat el WMS, que el FAQ demana acordar.
- interpretacio: el bloc diu explicitament que es brillantor artificial
  nocturna modelada, no transparencia, calitja ni pronostic de nuvols.
- iphone: reixa d'eines apilada a 393 px, selector i dos enllacos d'amplada
  completa; QA real de la seccio dins un marc 393x852 sense tall lateral.
- dropbox: `Pere Guerra/Eclipse meteo/index.html` actualitzat i autoportant;
  99 opcions i mapa incrustat verificats, amb el KMZ local al mateix directori.
- immutabilitat: cache meteorologic i KMZ no han canviat. SHA-256 cache
  `c15a51aad35d4ae030b378eb37d59e0f79f72c6dd4bd2bbce43e83c9b5dd2091`;
  KMZ `55f24954789b1dffbce74bcaacd5d60e6f8e9730889846a7ca4874fe9c193380`.
- validation: 99 ids/noms/coordenades Mercator uniques i round-trip PASS;
  Python i JavaScript PASS; els quatre modes i AEMET 2/2 preservats; mapa
  oficial amb tots els pins i obertura centrada de Colle comprovats; Dropbox
  normalitzat PASS; `git diff --check` PASS; pestanyes, fitxer QA i ports
  8774-8775 tancats, zero processos propis.
- hashes: `fes_web_local.py`
  `541ca45f204f9c29ca7c736c396f9fadf899942e13bc99a4a87337fc6540b137`;
  HTML font `391b7b670efb34bcad2ad37dbc33223357f82bd5522080c68b48bec05822496b`;
  index Dropbox `b5d34008f11db788d46b07cdbc4f7e397e93894e646ce072ef98397d4681cce7`.

## Refresc Medina, Colle i copia iPhone a Dropbox — RELEASED

- status: RELEASED
- updated_utc: 2026-08-11T21:28:00Z
- acquired_utc: 2026-08-11T16:40:04Z
- released_utc: 2026-08-11T21:28:00Z
- serial_writes: RELEASED
- owner: null
- task: tornar a actualitzar tots els miradors, interpretar la transparencia,
  afegir San Vicente Martir de Colle amb raig solar al KMZ i a la web, adaptar
  la web a iPhone 15 i copiar tota la carpeta a Dropbox/Pere Guerra.
- scope: `~/Desktop/Eclipse meteo/`, KMZ canonic de l'Escriptori, copia nova
  `~/Library/CloudStorage/Dropbox/Pere Guerra/Eclipse meteo/` i aquest
  bloc d'estat.
- exclusions: Delta i Ferrol conserven 0 dades meteorologiques; cap camera,
  PTP, `gphoto2`, captura, GUI fisica de camera, build, registre de l'app o
  LaunchServices.
- claude: intent de conciliacio en nomes lectura mitjancant el pont local,
  fallit explicitament per `Failed to authenticate: OAuth session expired`.
  El fitxer compartit de Claude declarava tots els blocs `RELEASED` i cap
  lock actiu. La feina va partir dels hashes de la seva ultima web/KMZ i va
  preservar la resta del directori; no s'ha presentat el pont com a exit.
- colle: coordenades 42.843610, -5.251080 (parroquia de Colle, Bonar); LIDAR
  1113,9 m; totalitat 107,8 s; Sol a C2 9,62 graus / azimut 281,3; horitzo de
  terreny 1,73 graus i marge 7,89; 118 min i 131 km des de Medina; carretera
  a 17 m. El KMZ incorpora punt `pg_fita`, estil `pg_ray_fita` i raig de 42
  km a les 18:30 UTC; backup recuperable a `.backups/`.
- weather: refresc final sequencial 21/21 entre 21:16 i 21:20 UTC, amb cinc
  centres, cinc falques, sis punts de capes i CAMS per a tots. Colle queda
  numero 20, R 15, 70 % de cel clar, 10 % de nuvol, discrepancia +/-44 i
  JUST. Tariego numero 1, R 45, 96 %, +/-17 i JUST; hotel Medina numero 2,
  R 42, 97 %, +/-11 i NET.
- transparencia: Medina AOD 0,090 i extincio total modelada 1,37 mag;
  Tariego 0,098 i 1,48 mag; Colle 0,149 i 1,69 mag. L'extrem desfavorable es
  el sector Burgos oriental, amb AOD fins a 0,22 i 2,50 mag amb el Sol baix.
- iphone: media query <=700 px amb botons d'amplada completa i files en
  targetes. QA visual real a 393x852: cap tall lateral; capcalera, controls,
  targetes i fila de Colle llegibles. El primer QA va detectar overflow i el
  segon solapament R/Cotxe; tots dos corregits abans de copiar.
- dropbox: copia completa de 429 fitxers font mes `index.html`, KMZ autoportant
  i `OBRE_AQUEST_FITXER.txt` (432 fitxers, 211 MB). Entrada recomanada:
  `Dropbox/Pere Guerra/Eclipse meteo/index.html`. QA des del mateix index:
  21 files/21 caches, Colle present, link KMZ local, AEMET 2/2; Delta 0 i
  Ferrol 0. Tots els fitxers font coincideixen per SHA excepte el canvi
  intencional de ruta del KMZ a l'HTML de Dropbox.
- audit: KMZ 289 Placemarks i 24 carpetes, Jubier intacte, 99/99 xifres
  verificables correctes; XML/ZIP PASS. Python i JavaScript PASS; integritat
  cache 21/21 PASS; `git diff --check` PASS; ports 8774-8776 tancats.
- hashes: KMZ canonic i copia Dropbox
  `55f24954789b1dffbce74bcaacd5d60e6f8e9730889846a7ca4874fe9c193380`;
  `fes_web_local.py`
  `e68014a169b2698d6fde13fbdf41068704dd2c30ce5c0f98368d3f4177fd33b4`;
  cache `c15a51aad35d4ae030b378eb37d59e0f79f72c6dd4bd2bbce43e83c9b5dd2091`;
  HTML font `c3e3c2f754e77a6abf0b68755ba8b174e30cc1eeb44be0ab0834c4388cf3384c`;
  index Dropbox `ba5a6f53e20d01b86738e99fa773fa2cd83dc4bf17517d3058acac1cb5dcb5c0`.

## Actualitzacio meteorologica completa Medina — RELEASED

- status: RELEASED
- updated_utc: 2026-08-11T14:41:27Z
- acquired_utc: 2026-08-11T14:33:06Z
- released_utc: 2026-08-11T14:41:27Z
- serial_writes: RELEASED
- owner: null
- task: refer la web meteorologica amb les ultimes dades disponibles dels
  miradors situats a un maxim de 3 h 05 min de Medina de Rioseco.
- scope: web i cache de `~/Desktop/Eclipse meteo/`, regeneracio amb el
  butlleti AEMET disponible i aquest bloc d'estat.
- exclusions: cap actualitzacio meteorologica del Delta de l'Ebre ni de
  Ferrol; cap camera, PTP, `gphoto2`, captura, GUI fisica de camera, build,
  registre de l'app o LaunchServices.
- safety: preservar tots els canvis preexistents de Pere i Claude i el KMZ
  canonic de l'Escriptori, verificat amb SHA-256
  `8478801b5cffa57e04326f4890540bf62263cad8e60761876f1bf1560e7bece0`.
- result: web regenerada sobre l'ultima versio de Claude, inclos el mode
  operatiu del dia 12; els 20 miradors de Medina s'han actualitzat
  sequencialment entre 14:34 i 14:38 UTC amb cinc centres, cinc falques, sis
  punts de capes i aerosol. Cache persistent i HTML 20/20.
- aemet: butlleti oficial disponible elaborat el dimarts 11 d'agost a les
  12:03, amb text complet i dos mapes reprojectats sobre 77 punts del KMZ.
- exclusions_comprovades: origen net amb Delta 0/17 i Ferrol 0/8; no s'hi ha
  fet cap descarrega meteorologica.
- ranking: Tariego numero 1, R 42, 94 % de cel clar, consens +/-17 i JUST;
  hotel Medina numero 2, R 41, 97 %, consens +/-6 i NET; Santa Maria del
  Campo numero 3, R 40, 94 %, consens +/-13 i NET; Belbimbre numero 4, R 37.
- validation: sintaxi Python i JavaScript PASS; cache 20/20 i integritat
  completa PASS; quatre grocs, tall de 185 min i AEMET 2/2 mapes PASS;
  `git diff --check` PASS; QA real i origen net PASS, zero errors de consola;
  pestanyes i dos servidors tancats, zero processos propis.
- hashes: `cache_meteo_miradors.json`
  `b865ba6b19ab96bd3f43d78f76a33a623e2dccb596243714e08c8920fee6667c`;
  `miradors_local.html`
  `89ca5197917ad2a36582983ba121250a6300666d33b5d8a8af9f05c9bbe76776`.

## KMZ canonic nou i mirador groc de Belbimbre — RELEASED

- status: RELEASED
- updated_utc: 2026-08-11T09:29:32Z
- acquired_utc: 2026-08-11T09:26:18Z
- released_utc: 2026-08-11T09:29:32Z
- serial_writes: RELEASED
- owner: null
- task: reconciliar la web amb la darrera versio real de
  `TSE_2026_08_12_miradors_Pere.kmz` i incorporar al filtre de Medina el
  mirador groc que havia quedat ocult per falta de temps de cotxe.
- scope: dades derivades i web de `~/Desktop/Eclipse meteo/`, cache meteo de
  Medina i aquest bloc d'estat.
- exclusions: cap mutacio del KMZ canonic; cap camera, PTP, `gphoto2`,
  captura, GUI fisica de camera, build, registre de l'app o LaunchServices.
- safety: preservar tots els canvis preexistents de Pere i Claude; usar el
  KMZ actual de l'Escriptori, SHA-256 `8478801b5cffa57e04326f4890540bf62263cad8e60761876f1bf1560e7bece0`,
  i no la copia `.previous`.
- result: els quatre grocs de la versio actual del KMZ coincideixen 4/4 amb
  el cataleg derivat. Belbimbre rep temps OSRM de 89 min des de Medina,
  enriquiment complet d'acces, terreny i aerosol, i entra com el mirador 20;
  Morella queda reconciliada amb el nom canonic `+4.5 graus`.
- weather: Belbimbre actualitzat individualment a les 09:27 UTC; cache
  persistent de Medina 20/20, cinc centres, cinc falques, sis punts de capes
  i aerosol. Delta i Ferrol no han descarregat meteorologia.
- ranking: Belbimbre numero 4 per R, R 42, 97 % de cel clar, consens +/-10 i
  NET; cotxe 1.5 h, durada 106 s, cota 793 m i Sol a 8.3 graus.
- audit: KMZ actual 287 punts i 24 carpetes; Jubier intacte; 98/98 xifres
  verificables quadren i zero divergeixen.
- validation: sintaxi Python i JavaScript PASS; grocs KMZ-JSON-HTML 4/4;
  cache visible 20/20; AEMET 2/2 mapes preservats; `git diff --check` PASS;
  QA real i origen net PASS, zero errors de consola, pestanyes i servidors
  tancats.
- hashes: `punts_kmz.json`
  `72b37d0aeb2b0e22c4b1ba28ea6050465029a5977693558efcac688691046ffe`;
  `bases_temps.json`
  `9d00af7996150fb0a30bd8bb0287d5c8e24a5cb879d58705555329c6bd1bc890`;
  `acces_punts.json`
  `4c91622552856f6e4d8970216872b229caaac1e2cc1cdb0c987f0c2045624cbc`;
  `mobilitat_punts.json`
  `73bd710dd8b8e248968a8b0ea2e32777358c36d6048a8833071197a98dc6a710`;
  `cota_casella.json`
  `316788d512cd54986f9521f310f7799d43d8e3d9eb9c8c3aaabe2322a51d4ddc`;
  `cache_meteo_miradors.json`
  `c4ae9ea5e81cdeacc4c9d772ec5944958bb07908127103a854b10aefe6fe43b6`;
  `miradors_local.html`
  `31172cc78bdc765f49a64ffcda9e865b61913ebbcb321b6c444f4db8f673dc28`.

## Assimilacio Claude i actualitzacio meteo Medina 3 h 05 — RELEASED

- status: RELEASED
- updated_utc: 2026-08-11T09:21:17Z
- acquired_utc: 2026-08-11T09:10:48Z
- released_utc: 2026-08-11T09:21:17Z
- serial_writes: RELEASED
- owner: null
- task: assimilar els canvis actuals de Claude a la web meteorologica, reduir
  el tall operatiu de Medina a 185 minuts i actualitzar sequencialment les
  dades dels miradors que hi queden inclosos.
- scope: `~/Desktop/Eclipse meteo/bases_temps.json`, generador i HTML actuals,
  cache meteorologic de Medina i aquest bloc d'estat.
- exclusions: cap actualitzacio meteorologica del Delta de l'Ebre ni de
  Ferrol; cap camera, PTP, `gphoto2`, captura, GUI fisica de camera, build,
  registre de l'app o LaunchServices.
- safety: preservar tots els canvis preexistents de Pere i Claude; el refresc
  regional no s'executara fins que el tall efectiu sigui 185 minuts.
- result: tall global reduit de 225 a 185 minuts; web de Claude assimilada
  amb 44 punts de ranquing i els seus dos mapes AEMET reprojectats. Medina
  queda amb 19/19 miradors actualitzats sequencialment entre 09:12 i 09:16
  UTC, cinc centres, cinc falques de visio, sis punts de capes i aerosol.
- exclusions_comprovades: Puerto de Ancares (197 min) queda fora del cache;
  en origen net Delta conserva 0/15 dades i Ferrol 0/8, sense cap descarrega.
- ranking: Santa Maria del Campo numero 1, R 45, 97 % de cel clar, consens
  +/-10 i NET; Tariego numero 2, R 43; hotel Medina numero 3, R 43, 99 %,
  consens +/-0 i NET.
- validation: sintaxi Python i JavaScript PASS; integritat 19/19 PASS;
  capes AEMET 2/2 sobre 77 punts PASS; `git diff --check` PASS; QA real i
  origen net PASS; cap error de consola, pestanyes i servidors tancats.
- hashes: `bases_temps.json`
  `f721a465cc0a7d5d49f9fbcd3e54032137390e26123628d9dbf3a6cf16e96a4b`;
  `fes_web_local.py`
  `cffb05e946c0708bb01bf3df00e02668623e5d1966dae4a18c1ef5dae996799d`;
  `miradors_local.html`
  `07c377c8e99db29119b02b19217f5d314515ba5843dc49a8f8dd7107faddff73`;
  `cache_meteo_miradors.json`
  `9baf6829dd5a434ca1304f406c03948a6736ae2745ead77abdef42c30ee7cc6e`.

## Correccio de l'ordre per cel clar — RELEASED

- status: RELEASED
- updated_utc: 2026-08-10T21:35:40Z
- acquired_utc: 2026-08-10T21:34:47Z
- released_utc: 2026-08-10T21:35:40Z
- serial_writes: RELEASED
- owner: null
- task: fer que el selector `cel clar` ordeni pel mateix valor visible a la
  columna, el pitjor entre el mirador i la falca de 25 km cap al Sol.
- scope: `~/Desktop/Eclipse meteo/fes_web_local.py`, HTML regenerat i aquest
  bloc d'estat; conservar sense canvis les dades meteorologiques guardades.
- exclusions: cap crida API nova, cap Delta/Ferrol, cap camera, PTP,
  `gphoto2`, captura, GUI fisica de camera, build o LaunchServices.
- result: el comparador usa ara el minim de `p30` entre el mirador i la
  falca, exactament el mateix valor que mostra la columna `Cel clar`.
- validation: Python i JavaScript PASS; `git diff --check` PASS; QA real amb
  els 20 valors en ordre descendent PASS (98, 96, 95, ... 57); Sotillos passa
  de la posicio incorrecta 4 a la correcta 17 amb 73 %. Cache meteorologic
  immutable i servidor/pestanya de prova tancats, zero processos propis.
- hashes: `fes_web_local.py`
  `00f2a7b09883fd3c1744432c4961d09b4c8f1de113aebe1a14ef975c5377d289`;
  `miradors_local.html`
  `4936ef8312c898a0102443c0bd04ce7a1c354dc7d42a553bec58a71766892257`;
  cache sense canvis
  `1a5ca6a8777c92e5f1b209341ff8bd771a8ecf91d9264dcf67ff9fd8f64e65d5`.

## Actualitzacio AEMET i meteorologia de Medina — RELEASED

- status: RELEASED
- updated_utc: 2026-08-10T21:18:24Z
- acquired_utc: 2026-08-10T21:08:57Z
- released_utc: 2026-08-10T21:18:24Z
- serial_writes: RELEASED
- owner: null
- task: incorporar el butlleti especial AEMET elaborat el 10 d'agost a les
  15:37 i actualitzar sequencialment els vint miradors situats a un maxim de
  3 h 45 min de Medina de Rioseco.
- scope: `~/Desktop/Eclipse meteo/fes_web_local.py`,
  `~/Desktop/Eclipse meteo/miradors_local.html`, cache meteorologic dels
  miradors de Medina mitjancant la UI i aquest bloc d'estat.
- exclusions: cap actualitzacio meteorologica del Delta de l'Ebre ni de
  Ferrol; cap camera, PTP, `gphoto2`, captura, GUI fisica de camera, build,
  registre de l'app o LaunchServices.
- result: AEMET 15:37 incorporat amb text oficial complet, quatre mapes i PDF;
  cache persistent de Medina amb 20/20 miradors, cinc centres, sis punts de
  linia de visio i aerosol, descarregats sequencialment entre 21:10 i 21:14
  UTC. El cache queda separat per hotel base: validacio neta Medina 20/20,
  Delta 0/18 i Ferrol 0/11.
- ranking: Tariego de Cerrato numero 1, R 42, 96 % de cel clar, consens +/-11
  i NET; hotel Medina numero 3, R 39, 98 %, consens +/-6 i NET.
- validation: parser/Python PASS, JavaScript syntax PASS, integritat cache
  20/20 PASS, `git diff --check` PASS i QA real des d'un origen net PASS;
  pestanyes i dos servidors locals tancats, zero processos propis.
- hashes: `fes_web_local.py`
  `c0b47cc97c2bd701fe40b500ca7fa7e1aa253408e00f146a73034e1443a70807`;
  `miradors_local.html`
  `1fc6638186bf8a5848c310daac26545cf01434adb6f51ae6ed223144489c57a5`;
  `cache_meteo_miradors.json`
  `1a5ca6a8777c92e5f1b209341ff8bd771a8ecf91d9264dcf67ff9fd8f64e65d5`.

## Butlletí especial AEMET del 10 d'agost — RELEASED

- status: RELEASED
- updated_utc: 2026-08-10T11:10:57Z
- released_utc: 2026-08-10T11:10:57Z
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-10T11:08:01Z
- task: incorporar íntegrament a la web meteorològica el nou butlletí
  especial AEMET elaborat el 10 d'agost de 2026 a les 12:47.
- scope: `~/Desktop/Eclipse meteo/fes_web_local.py`, HTML regenerat i aquest
  bloc d'estat; cap descàrrega meteorològica de miradors ni contacte de càmera.
- safety: preservar l'arbre brut i adaptar el parser al nou format d'AEMET
  abans de regenerar, perquè el format antic perdia el text del butlletí.
- result: butlletí oficial del 10 d'agost a les 12:47 incorporat amb text
  general i de nuvolositat, calor, IPIF, quatre mapes peninsulars i PDF.
- preserved: 41 punts, quatre miradors marrons, tall de 225 minuts i caché
  meteorològic per mirador sense cap descàrrega automàtica.
- validation: parser i Python PASS; dades JSON i JavaScript PASS;
  `git diff --check` PASS; QA real al navegador PASS amb els quatre mapes i
  els set enllaços oficials correctes.
- hashes: `fes_web_local.py`
  `d513818a3b291b451fc4fe3a1ec9a25ba9d5441d8add3658b7f2864f80b3a0e6`;
  `miradors_local.html`
  `587896040206087cee764a7ab1fb5f0dec40bbb7e43d3b975895e161dae86537`.
- boundary: zero descàrregues meteorològiques de miradors; zero càmera,
  PTP, `gphoto2`, captures, GUI física, build o LaunchServices; pestanya QA i
  servidor local tancats, zero processos propis.

## Miradors marrons i tall de 3 h 45 min — RELEASED

- status: RELEASED
- updated_utc: 2026-08-10T10:30:20Z
- released_utc: 2026-08-10T10:30:20Z
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-10T10:27:34Z
- task: incorporar els quatre miradors `pg_marro` del KMZ canònic a la web
  meteorològica i limitar cada selector de base a 225 minuts de cotxe.
- scope: `~/Desktop/Eclipse meteo/` i aquest bloc d'estat; cap càmera, PTP,
  gphoto2, captura, GUI física, LaunchServices, build ni registre de l'app.
- safety: preservar íntegrament l'arbre brut i els canvis preexistents.
- result: 96 punts al catàleg font, quatre marrons exactes 4/4 contra el KMZ,
  41 punts a la web; visibles per base a 225 min: Medina 20 (4 marrons),
  Delta 18 (0) i Ferrol 11 (0).
- enrichment: `acces_punts.json`, `mobilitat_punts.json` i
  `cota_casella.json` complets 96/96; els quatre marrons són accessibles en
  cotxe i conserven els temps OSRM 61/89/108/146 min des de Medina.
- validation: Python AST, JSON, JavaScript syntax, `git diff --check` i
  comparació KMZ/dades/web PASS; QA real al navegador PASS per a les tres
  bases, text exacte 3 h 45 min i quatre etiquetes marrons només a Medina.
- hashes: font web
  `e79627ea6fe29756ca1ba27a464874724176786d2dc7893661fed7cf9fda66c2`;
  HTML `e090c7c01b67a0cfe649ea945626356f69bd94fad267054d2716c82b84ae75c1`;
  punts `b534d28e0477bb0bd26696c4bffa5d9afdd896ef91d5b9b61a9b49f3ff1551cd`;
  temps `5da50521afb6f200e6487305cba13c26ff608632fff1b168333c07949ec31fb3`.
- physical_boundary: zero descàrrega meteorològica automàtica, càmera, PTP,
  gphoto2, trigger, GUI física, LaunchServices, build o registre; pestanya i
  servidor local de QA tancats, zero processos propis.

## Publicació GitHub V1.02 filtrada — RELEASED

- status: RELEASED
- updated_utc: 2026-08-10T10:27:11Z
- released_utc: 2026-08-10T10:27:11Z
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-10T10:11:07Z
- task: preparar el codi públic de la V1.02 sobre el `main` públic, excloure
  qualsevol referència o artefacte del SDK de Canon, publicar-lo a GitHub i
  crear el tag/release corresponent.
- scope: Git/GitHub i aquest bloc d'estat; cap càmera, PTP, gphoto2, captura,
  GUI física, LaunchServices, build o registre de l'app.
- safety: preservar tots els canvis preexistents; no publicar l'historial de
  la branca privada; gate textual i d'inventari fail-closed abans del push.
- result: `main` públic a
  `45d6eb7cc4e818b171f6aef4c8304c235855d3b3`; tree Git
  `46fc3e19d9880827aa7891218602ebc4ea678d4f`; tag anotat `v1.0.2` i
  release normal/Latest a
  `https://github.com/PeterWar/Eclipse-Command/releases/tag/v1.0.2`.
- public_filter: export nou sobre `public/main`, sense historial privat;
  zero noms, literals o artefactes del SDK de Canon, zero identitats reals,
  zero runs/evidència, `.coordination`, bundle o arxiu de release; els perfils
  públics conserven els vuit placeholders `*_REPLACE_ME`.
- validation: GUI 513/513; controlador públic 1.057 descobertes, 171 skips
  explícits d'evidència privada i zero errors/failures; fuzz 67.392/67.392;
  porta 7.044 `PORTA OBERTA`; frontera pública 4/4; perfils i diff-check PASS.
- physical_boundary: zero càmera, PTP, gphoto2, captura, missió, GUI física,
  LaunchServices, build o registre de l'app; l'app oberta per Pere no s'ha
  tocat i no queda cap procés propi.

## Caché i descàrrega per mirador de la web meteo — RELEASED

- status: RELEASED
- updated_utc: 2026-08-10T10:10:08Z
- released_utc: 2026-08-10T10:10:08Z
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-10T10:03:01Z
- task: conservar al rànquing qualsevol dada meteorològica guardada, sense
  refresc massiu automàtic; carregar un mirador cada vegada i afegir un botó
  explícit per actualitzar seqüencialment tota la regió.
- files: `~/Desktop/Eclipse meteo/fes_web_local.py` i
  `~/Desktop/Eclipse meteo/miradors_local.html` regenerat; tota la resta de
  feina preexistent s’ha preservat.
- behavior: caché sense caducitat automàtica i edat visible per fila; obrir o
  refrescar baixa un mirador complet; el botó regional els recorre un per un,
  mostra progrés i s’atura entre miradors; `fetch` té timeout de 90 s.
- validation: Python AST i JavaScript syntax PASS; 9 comprovacions estructurals
  PASS; prova local real PASS amb 1/19 al caché després del clic i del reload;
  botó regional 5 actualitzats, aturada demanada i zero inici del sisè.
- hashes: font
  `b34d5ead68cddf15f9a82e3e59c226bbde3dab75b37daaf4a87f55fe8bb03ad3`;
  HTML `839aa55684f3312ed747d189e213f9252cb6c5aab6df1785f1eef0bb0edc253c`.
- physical_boundary: zero GUI física de càmeres, PTP, gphoto2, càmera,
  trigger, LaunchServices, build o registre de l’app; servidor local de prova
  i pestanya de navegador tancats, zero processos propis.

## Descàrrega meteorològica API 10 d’agost — RELEASED

- status: RELEASED
- updated_utc: 2026-08-10T09:42:22Z
- released_utc: 2026-08-10T09:42:22Z
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-10T09:26:28Z
- task: baixar i validar l’última passada dels cinc conjunts meteorològics
  per als 56 punts i la falca occidental del protocol.
- result: `arxiu_conjunts_20260810T0926Z.json`, 231.187 bytes,
  SHA-256 `66b583083fe2625b03ca6960eb2338e2d888b779c8a51accb1ce741d6f2e41c0`.
- validation: 80/80 ubicacions i tres passos natius; membres complets a tots
  els llocs i hores: ECMWF 51, ICON 40, GFS 31, GEM 21 i UKMO 18.
- preservation: cap canvi preexistent dels dos repositoris no s’ha alterat;
  l’únic artefacte nou de la passada és l’arxiu JSON i la cau ignorada.
- physical_boundary: zero GUI física, PTP, gphoto2, càmera, trigger,
  LaunchServices, build o registre de l’app.

## V1.02 audit, fixes, bundle and verification — RELEASED 2026-08-09

- status: RELEASED
- updated_utc: 2026-08-09T23:23:31Z
- released_utc: 2026-08-09T23:23:31Z
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-09T22:59:42Z
- task: auditar de nou la V1.01; contrastar troballes amb Claude Opus xHigh;
  implementar la V1.02 (`1.0.2`) amb UI compacta, quatre avisos de veu i
  inici R6 a C2−15; corregir deriva confirmada; construir i provar el bundle.
- baseline_read_only: GUI 511/511, controlador 1.106/1.106, fuzz i porta
  60–110 s verds; bundle V1.01 coherent 51/51 i QA portable 11/11.
- claude_contrast: Opus, esforç xHigh, mode plan i eines Read/Glob/Grep;
  tooltip, deriva documental i geometria C2−15 confirmats o matisats abans
  de qualsevol mutació de la font.
- implementation:
  - noms curts + f-ratio i tooltip breu amb identitat exacta;
  - cues one-shot C2−5 min, −2 min, −1 min i C4−1 min;
  - R6 setter C2−15, primera foto −14,75 i només vuit captures eliminades;
  - text stale corregit als perfils A7III, A7RIIIA, 6D i R6;
  - autoritat viva actualitzada a AGENTS/CLAUDE/README/QA.
- r6_proof: 1.503 geometries PASS; delta −8 exacte només al prefix; sufix
  des de C2−5,65 bit a bit invariant; GUI i worker idèntics. A 91 s,
  captures 122→114, nucli 117→109, totalitat 55, post-C3 34 i setters 29.
- validation:
  - GUI 513/513 i controlador 1.107/1.107 PASS;
  - fuzz, perfils, porta 60–110 s i `git diff --check` PASS;
  - regressió agregada PASS en 140,0 s;
  - build literal PASS al primer intent;
  - QA portable final 11/11 PASS, 51/51 fonts coherents i manifests idèntics.
- bundle:
  - app `gui/dist/Eclipse Command.app`, 1.0.2, arm64, ad-hoc, 122,6 MiB;
  - executable `61227d418ec7a74a6fa11c934970d85218466ffd067754ec68efbc3334ba9f4f`;
  - manifest `d06de97146e521afeb1871c3cfd06c5944faf3c40dbd96898f53c30d734a2f6a`;
  - QA `gui/QA_REPORT_1.0.2_2026-08-10.md`.
- physical_boundary: app V1.02 registrada i oberta; capçalera V1.0.2,
  R6 III i A7RIIIA READY amb els noms nous. Cap missió, captura, format o
  replay; aquesta versió encara no té TEST RUN de dispars propi.
- retention: vuit `.previous-*` al dist; quatre bundles antics traslladats
  recuperablement a
  `/Users/USUARI/Downloads/Eclipse_2026_bundle_quarantine_20260810_v102`.
- handoff: rollback immediat V1.01 i rollback físic 0.9.3 preservats; zero
  app, worker, mission_host, controlador, gphoto2, PyInstaller o QA propi;
  SERIAL_WRITES alliberat.

## ISO controls rehabilitation + conservative cleanup 0.8.1 — RELEASED 2026-08-05

- status: RELEASED
- updated_utc: 2026-08-05T21:24:50Z
- released_utc: 2026-08-05T21:24:50Z
- task: Rehabilitar els botons ISO 100/200/400 com a writes preflight
  explícits i no bloquejants, netejar només artefactes regenerables i
  preparar un bundle privat 0.8.1 verificat.
- phase: PRIVATE_BUNDLE_VERIFIED
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-05T21:12:00Z
- source:
  - HEAD privat `5388b63458c1d62682ca875af9043a0cf92918b4`;
  - worktree net i backup verificat a `dropbox/main`;
  - tag/release pública 0.8.0 immutable i fora d'abast.
- mission_first:
  - ISO continua advisory i operator-owned;
  - cap valor ISO pot bloquejar Start mission, degradar altres canals o
    produir FAILED en missió;
  - només un clic explícit autoritza un write preflight, amb identitat exacta,
    una mutació + readback i resultat SET/NOT SET;
  - Busy només es reintenta si declara literalment `was not set`;
  - els botons queden deshabilitats durant missió, scan, Sync UTC o qualsevol
    operació de càmera.
- cleanup_boundary:
  - preservar tots els runs, tests, evidence, outputs, certificacions,
    EDSDK privat, worktree històric i venv activa;
  - apartar en quarantena recuperable només caches fora de venv, ZIP local
    regenerable i rollbacks d'app superats;
  - conservar sempre app actual i rollback immediat.
- physical_boundary:
  - zero GUI física, PTP, gphoto2, càmera, targeta, trigger o LaunchServices.
- result:
  - branca privada `codex/iso-controls-cleanup-0.8.1`;
  - botons ISO 100/200/400 visibles només quan el preflight és segur;
  - cap delta en controladors, perfils, shutters, timings, buffers, setters o
    backends R6/6D/Sony;
  - app local 0.8.1 executable
    `dc1837ff40b2944dc5b4180885ed1b11651e46bf7f886277584ad710c6b26a7a`;
  - manifest 49 fonts
    `6c2f50c6054a4e2737f6bc41b063d25b9ca2a26071c26540ff8a1915b4333b36`;
  - rollback immediat 0.8.0 preservat a
    `gui/dist/Eclipse Command.app.previous-20260805T211937Z-92423`;
  - 29 rollbacks superats, set caches i artefactes regenerables apartats a
    `/Users/USUARI/Downloads/Eclipse_2026_cleanup_quarantine_20260805_llu9An`
    (3,5 GiB, zero eliminació permanent).
- validation:
  - GUI 429/429; controlador 1.033/1.033; fuzz 67.392/67.392;
  - beta offline 4/4 i 20/20, rebut
    `2bf8589e7ad33dcad92461bdf732061935589bc9d53c6a314d974933bb07dc4f`;
  - QA portable complet PASS, EDSDK/backend privat absent;
  - `git diff --check`, proves focals ISO i revalidació bundle PASS.
- handoff:
  - release pública 0.8.0, tag i remot públic intactes;
  - 0.8.1 és candidat privat local, encara sense gate físic ISO;
  - zero processos propis de GUI, controlador, gphoto2, PyInstaller o QA;
  - `SERIAL_WRITES` alliberat a 2026-08-05T21:24:50Z.

## Dropbox main verified backup — RELEASED 2026-08-05

- status: RELEASED
- updated_utc: 2026-08-05T18:50:56Z
- released_utc: 2026-08-05T18:50:56Z
- task: Guardar el snapshot Git complet del projecte canònic al remot privat
  `dropbox`, branca `main`, i verificar referència, arbre i objectes.
- phase: DROPBOX_MAIN_PUSHED_AND_VERIFIED
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-05T18:50:12Z
- source:
  - worktree canònic net;
  - HEAD `5388b63458c1d62682ca875af9043a0cf92918b4`;
  - `dropbox/main` actual `ae328ae649d5f57d5c65b28d8955c804fa3bdfa1`;
  - l'HEAD és descendent fast-forward del main remot.
- safety:
  - zero force-push, reset, checkout, clean o stash;
  - repositori públic i release 0.8.0 fora d'abast;
  - cap GUI, PTP, gphoto2, càmera, trigger, build o LaunchServices.
- result:
  - fast-forward `ae328ae649d5f57d5c65b28d8955c804fa3bdfa1` ->
    `5388b63458c1d62682ca875af9043a0cf92918b4` a `dropbox/main`;
  - tree Git `6258c8e49718ac0557e47f34858401cc25264efd`;
  - 800 fitxers tracked, 199.530.887 bytes i 13 commits accessibles;
  - SHA-256 de `git archive` local i remot idèntic:
    `01928d736d77fe7d9c9cc75919f37d7ea30a8b46d46050b8555ea1b679795628`;
  - repositori bare Dropbox 126 MiB, `git fsck --full --no-dangling` PASS,
    1.186 objectes empaquetats, zero garbage.
- handoff:
  - `SERIAL_WRITES` alliberat a 2026-08-05T18:50:56Z;
  - worktree canònic net i zero processos propis de GUI, controller, gphoto2
    o QA;
  - cap fitxer de projecte reescrit i cap contacte de maquinari.

## Public contributions workflow — RELEASED 2026-08-05

- status: RELEASED
- updated_utc: 2026-08-05T18:44:34Z
- released_utc: 2026-08-05T18:44:34Z
- task: Obrir el repositori públic a contribucions amb fork, branques i pull
  requests, documentar les fronteres de seguretat i habilitar els canals
  comunitaris de GitHub.
- phase: PUBLIC_COMMUNITY_WORKFLOW_LIVE
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-05T18:42:16Z
- scope:
  - només documentació, plantilles i configuració del repositori públic;
  - cap codi operatiu, perfil, timing, setter, shutter, backend o bundle;
  - cap PTP, gphoto2, càmera, trigger, build o LaunchServices.
- live_gui_boundary:
  - la GUI física 0.8.0 de Pere es va observar oberta amb PID 88735 i zero
    controller, mission_host o gphoto2 associats;
  - al checkpoint final ja no era activa; Codex no la va aturar, modificar
    ni registrar.
- result:
  - PR https://github.com/PeterWar/Eclipse-Command/pull/2 fusionada;
  - `main` públic a `39c8e7cf1d13f241160de6c0a55208211f00ed74`;
  - `CONTRIBUTING.md`, plantilla de PR i formularis de bug/nova càmera;
  - README documenta fork -> branch -> pull request i que les branques
    upstream directes exigeixen invitació explícita com a col·laborador;
  - Issues i Discussions activats, `allow_forking=true`,
    `allow_update_branch=true` i `delete_branch_on_merge=true`.
- validation:
  - `git diff --check` PASS;
  - tres formularis GitHub YAML parsejats correctament;
  - frontera d'export públic 4/4 PASS;
  - perfil comunitari de GitHub reconeix `CONTRIBUTING.md`;
  - zero canvis a runtime, perfils, shutters, timings, bundle o release 0.8.0.
- handoff:
  - `SERIAL_WRITES` alliberat a 2026-08-05T18:44:34Z;
  - arbre canònic net i zero processos Eclipse Command, controller, gphoto2
    o QA propis;
  - cap PTP, càmera, trigger, build, GUI o LaunchServices.

## Main public release cadence + universal onboarding — RELEASED 2026-08-05

- status: RELEASED
- updated_utc: 2026-08-05T18:25:26Z
- released_utc: 2026-08-05T18:25:26Z
- task: Publicar Eclipse Command 0.8.0 amb una acció documental per minut
  entre C1 i C2-30 s i entre C3+30 s i C4, actualitzar la guia universal
  d'alta agentic AI i preservar estrictament la frontera pública/privada.
- phase: GITHUB_RELEASE_0_8_0_PUBLISHED_AND_REMOTE_VERIFIED
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-05T17:53:41Z
- release:
  - repositori públic: https://github.com/PeterWar/Eclipse-Command
  - release: https://github.com/PeterWar/Eclipse-Command/releases/tag/v0.8.0
  - PR final: https://github.com/PeterWar/Eclipse-Command/pull/1
  - `main` i tag `v0.8.0` apunten al commit
    `4f73eacacb0201f5c9941966b72103327b0535d4`;
  - asset: `Eclipse-Command-0.8.0-macos-arm64.zip`, 48.012.053 bytes;
  - ZIP SHA-256
    `205cd9b229a237a30722ef3532d5b1c7f4b5550b6d86e118c5a3b78e703873ac`;
  - executable SHA-256
    `913b2c571cff2e5c5db2ae39d323b39b9a5943c2e4ee0ecb9d22743636577589`;
  - manifest 49 fonts SHA-256
    `68fea4132d56963d70f25da6bc0457d755a6b4eb28a9219c1951f98a3d0c74ff`;
  - rebut beta SHA-256
    `9ff6101f4a7573ad5dfe23df0e7ba7ddc39ed8aef2bf8024cd97b0dc2dc02ed3`.
- remote_verification:
  - l'asset publicat s'ha tornat a descarregar i el SHA-256 coincideix;
  - integritat ZIP PASS i zero entrades `__MACOSX`;
  - repo PUBLIC, branca única `main`, arbre final de 271 fitxers;
  - zero runs/evidence/RAW/JPEG, identificadors físics, rutes locals,
    secrets o payload EDSDK/backend privat;
  - el commit contaminat `5388b63` no existeix al repositori públic;
  - l'antic repositori amb els refs contaminats queda renombrat
    `PeterWar/Eclipse-Command-Quarantine-20260805` i PRIVATE.
- qa:
  - GUI 429/429 PASS;
  - controlador públic 989 PASS amb 171 certificacions d'evidència privada
    explícitament skipped; arbre privat preexport 1.033/1.033 PASS;
  - fuzz 67.392/67.392 PASS;
  - beta operador 4/4 runs i 20/20 checks PASS;
  - QA portable del bundle sanititzat PASS: metadata, signatura, relocació,
    114 Mach-O autocontinguts, perfils, worker/controlador, auditoria,
    dispatch R6, host bloquejat i GUI offscreen fake-gphoto2.
- mission_first:
  - captures parcials noves independents i `late_policy=skip`;
  - cap fallada parcial elimina contactes/totalitat ni atura altres canals;
  - trigger ambigu consumit i zero replay; identitat/propietat divergent,
    write amb estat físic desconegut o ledger insegur aturen només aquell cos;
  - controls ISO absents de la GUI pública però implementació dormant
    preservada al fork de desenvolupament.
- public_private_boundary:
  - publicació exclusivament gphoto2/libgphoto2;
  - zero headers, frameworks, binaris, codi o material llicenciat EDSDK;
  - identitats dels perfils públics substituïdes per `*_REPLACE_ME`;
  - cap evidència física privada reescrita ni requalificada.
- physical_boundary:
  - cap PTP, gphoto2, càmera, targeta, trigger ni LaunchServices durant
    build, QA, commit, push o release;
  - el bundle públic es va construir en staging separat i no substitueix el
    bundle privat canònic;
  - la R6 i els seus runs/certificats es conserven immutables.
- cloudy_nights:
  - tasca separada `019fd2e8-360b-75f2-a2bd-2bab7b383c27` completada amb
    un esborrany anglès; cap publicació externa feta.
- handoff:
  - `SERIAL_WRITES` alliberat a 2026-08-05T18:25:26Z;
  - arbre canònic net;
  - zero processos Eclipse Command, controller, mission_host, gphoto2,
    PyInstaller, QA o inspectors propis.

## Main R6 full-release correction + 0.7.18 — RELEASED 2026-08-05

- status: RELEASED
- updated_utc: 2026-08-05T16:54:02Z
- released_utc: 2026-08-05T16:54:02Z
- task: Corregir `Press Full MF -> Release Full` a
  `Press Full MF -> Release` exclusivament per la R6 III i demostrar que
  allibera el setter shutter sense degradar Mission First.
- phase: ECLIPSE_COMMAND_0_7_18_READY_PHYSICAL_TEST_PENDING
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-05T16:24:18Z
- authorization:
  - Pere confirma que la R6 continua encesa després d'haver rebut el pla
    exacte: primer Release total + setter/restore sense captura; si passa,
    correccio offline i un unic AEB3 amb manifest +3 CR3.
  - Pere ordena construir igualment la versió nova i provar la correcció
    directament des del bundle candidat, sense exigir abans el gate AEB3 LAB.
- scope:
  - identitat exacta; zero-capture `Release`, setter 1/320 -> 1/160,
    readback i restore 1/320;
  - correccio body-specific R6, QA offline i, només si tot és verd, un únic
    AEB3 fail-fast amb release total, setter/readback/restore i +3 CR3.
- excluded:
  - cap replay, G6, G40/H90, GUI física, EDSDK o contacte de càmera durant
    el build; la 0.7.18 queda candidata fins al TEST RUN físic.
- mission_first:
  - qualsevol trigger ambigu es consumeix; Busy net conserva l'últim
    shutter conegut; estat post-write desconegut o ledger insegur atura només
  R6; cap canvi als altres cossos.
- zero_capture_result:
  - identitat PTP exacta Canon EOS R6 Mark III, sèrie [SÈRIE];
  - una única ordre `Release` total, setter 1/320 -> 1/160 adoptat i
    readback exacte; Pere va observar físicament el canvi;
  - restore 1/320 adoptat i readback exacte; zero captures, retry, replay o
    estat físic desconegut; sessió tancada amb exit 0.
- correction:
  - només la R6 migra a `Press Full MF` -> `Release`; la Canon 6D conserva
    el seu contracte body-specific;
  - perfils R6 vius regenerats amb el contracte exacte i guards que rebutgen
    `Release Full`; cap run, certificat o snapshot físic històric reescrit;
  - S2 event-drain queda només com a recerca/evidència històrica i no forma
    part de la llista de perfils empaquetats; no entra a la release pública;
  - abans del build s'ha eliminat el runtime S2 del controlador públic i el
    perfil LAB S2 executable; la recerca i els runs històrics es conserven;
  - el programa dinàmic 0.7.16 es conserva byte-equivalent en shutters,
    blocs, 40 press, sis setters i timings; l'únic delta operatiu del trigger
    és `Release Full` -> `Release`.
- offline_qa:
  - focal final R6/GUI 58/58 i controlador focal 74/74 PASS;
  - controlador complet final 1.033/1.033 PASS;
  - GUI completa 428/428 PASS;
  - fuzz timeline 67.392/67.392 PASS;
  - beta operador offline 4/4 recorreguts i 20/20 proves PASS; rebut
    `gui/BETA_USER_RUNS_0.7.18_2026-08-05.json`, SHA-256
    `ddb69d824329431b72fe61d894e685698f6b46cecb85aa5813b7404e0540f9b8`;
  - perfils curts, `py_compile` i `git diff --check` PASS;
  - zero Qt físic, PTP, càmera, gphoto2, LaunchServices o bundle durant QA.
- bundle_0_7_18:
  - `gui/dist/Eclipse Command.app`, versió plist 0.7.18, arm64, signatura
    ad-hoc, `LSMinimumSystemVersion=26.0`, no notaritzat;
  - executable SHA-256
    `ca00f2a6b3b5b8835178df9effbc2562eef53b6b9dd2eeb6ba55501b0916444e`;
  - manifest de 49 fonts SHA-256
    `bef19209652ff7285e10c9415819b8159d97b924028cb4af6387754cbbd00574`;
  - QA portable PASS: metadata/signatura, relocació, 114 Mach-O, perfils
    congelats, worker/controlador, auditoria 3/3, dispatch R6 dinàmic,
    rebuig prelaunch i GUI offscreen amb gphoto2 fals;
  - rollback immediat 0.7.16:
    `gui/dist/Eclipse Command.app.previous-20260805T165100Z-59059`, executable
    SHA-256 `91496f9d07e69d20229d8b73c0d21fcc57f20091ea3ff29b9e96ab8ae71f5c55`;
  - QA publicada a `gui/QA_REPORT_0.7.18_2026-08-05.md`.
- next_gate:
  - amb la càmera recarregada, una única AEB3 amb `Release` total, setter i
    readback/restore, manifest CFexpress pre/post i delta exclusiu +3 CR3;
  - zero replay i stop al primer error; cap app nova abans del PASS físic.
- handoff:
  - `SERIAL_WRITES` alliberat a 2026-08-05T16:54:02Z;
  - zero processos Eclipse Command, mission_host, controladors, gphoto2,
    PyInstaller, QA o inspectors propis;
  - càmera apagada per recarregar; cap contacte físic durant build o QA;
  - la 0.7.18 és candidata offline verda, no qualificació física AEB3.

## Main R6 S1-12s + S2 offline discriminator — RELEASED 2026-08-05

- status: RELEASED
- updated_utc: 2026-08-05T16:20:41Z
- released_utc: 2026-08-05T16:20:41Z
- task: Tancar S1 release+12 s i preparar offline el discriminator S2 de
  cua d'events Canon sense modificar l'app operativa.
- phase: R6_S2_EVENT_DRAIN_PHYSICAL_GATE_PENDING
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-05T16:03:01Z
- s1_12_result:
  - FAIL de readiness net: un unic setter enviat a release+12,018956 s va
    rebre `0x2019 PTP Device Busy / was not set`; zero retry/replay;
  - shutter 1/320 confirmat al cleanup, `physical_state_unknown=false`,
    `cleanup_ok=true`;
  - inventaris CFexpress 927 -> 930 i delta immutable exactament +3 CR3:
    `572A3359.CR3`, `572A3360.CR3`, `572A3361.CR3`;
  - inspeccions PASS: 1/320 (0 EV), 1/2500 (-3 EV), 1/40 (+3 EV), RAW
    Electronic, identitat i ordre AEB exactes.
- s1_12_evidence:
  - run: `controller/runs/20260805T180334_lab_r6m3_s1_release_12s_shutter_readiness_v1_run`;
  - result SHA-256: `5955f55602a069478975c22c6399facba4fe6a459e779674a7aa4913edbf7ffd`;
  - manifest SHA-256: `e402c07ce1ec01e0db97afba3911d39d3ef3000abf968fbaeb1867d714e2806a`;
  - profile snapshot SHA-256: `55736c02118e2aa8c27ce4f41c7857621c64f38fd03d59c1ce75145ab27e8ffb`;
  - events SHA-256: `704d0e002ec17d0e6adf831bb06146042165123c05fcdd027739287957ee2779`;
  - delta SHA-256: `a8eff04e27039f552758f7eef796ae6cee116794db63a07f4902fb974bb95d79`;
  - inspections SHA-256: `8913510231297f9c47047a462690e95d0f3174c5b5a0bbb9f8d174a1229e5f6a`,
    `41a35b44f83998c42a81dc4749175222f23dbfd1e7999f79f98491e6e3512d83`,
    `7848f03a8180aa0e68878148a0dc4247aeb0edd6cb9bd0d0083d2c037a29af54`.
- direct_setter_observation:
  - a les 18:20 CEST, una sessio gphoto2 nova va verificar model/sèrie i
    shutter writable 1/320; `Choice 37` era 1/160;
  - un unic `set-config-index ...shutterspeed=37` va reproduir el mateix
    Busy net; readback immediat 1/320, zero captura, retry o estat desconegut;
  - observacio interactiva, no certificat immutable.
- s2_offline:
  - nou tipus LAB `card_only_event_drain`: exactament `wait-event 2500ms`,
    mai download, payload local prohibit i zero Busy retry;
  - perfil `lab_r6m3_s2_event_drain_2500ms_shutter_readiness_v1.json`,
    SHA-256 `8570195ca1f4674243b71f802a9b5b4373fe013d1fc69d7843be6f00caa4403f`;
  - dry-run worker PASS, result SHA-256
    `dcd23a12e8eac901fda3d3e9491c852ad0a8ba465041d7f7e302dc706de9da14`;
  - proves focals 60/60 i regressio controlador 1.036/1.036 PASS;
  - cap GUI, LaunchServices, EDSDK, bundle, perfil operatiu o app modificat.
- demonstrated:
  - S1 6/8/12 s materialitzen +3 CR3 pero tots refusen el setter;
  - el refús es reprodueix amb setter directe post-campanya;
  - S2 és compilable, auditable i fail-closed només offline.
- missing:
  - adopcio fisica 1/160 després del drenatge d'events;
  - acotar latencia, G6, G40/H90 i tres histories C1-C4.
- next_gate:
  - una unica execucio fisica S2 amb manifest pre/post, un AEB3 consumible,
    `wait-event` card-only, setter unic, restore i inspeccio exacta +3 CR3;
  - cap promocio ni app nova abans d'un PASS fisic i la resta de gates.
- handoff:
  - `SERIAL_WRITES` alliberat;
  - zero processos Eclipse Command, eclipse_capture_r6m3, gphoto2,
    snapshots, downloads o inspectors a les 2026-08-05T16:20:41Z.

## Main R6 S1-8s physical campaign — RELEASED 2026-08-05

- status: RELEASED
- updated_utc: 2026-08-05T15:58:17Z
- released_utc: 2026-08-05T15:58:17Z
- task: Executar i certificar S1 release+8 s amb un AEB3 i +3 CR3 exclusius.
- phase: R6_S1_12S_PHYSICAL_AUTHORIZATION_PENDING
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-05T15:53:57Z
- authorization:
  - Pere autoritza manifest CFexpress pre/post, una captura AEB3, setter
    1/320 -> 1/160 a release+8 s, readback, restore 1/320 i inspeccio dels
    tres CR3; stop al primer error i zero replay.
- scope:
  - identitat exacta i inventari CFexpress pre sense captura;
  - un unic press/release AEB3 i un unic setter release-anchored a +8 s;
  - restore 1/320, inventari post, delta +3, download/inspeccio dels tres
    CR3 nous i certificat immutable nomes si tota l'evidencia PASS quadra.
- excluded:
  - cap segon trigger, S1-12, G6, G40/H90, GUI, LaunchServices, EDSDK,
    bundle o release publica.
- mission_first:
  - trigger ambigu es consumeix i no es repeteix;
  - Busy net `was not set` conserva 1/320 conegut i no es reintenta;
  - identitat divergent, write ambigu/estat desconegut o ledger insegur
    atura nomes R6; cap altre canal queda afectat.
- result:
  - S1 release+8 s: FAIL de readiness body-specific;
  - un unic AEB3 amb press/release ACK i ledger de 3 RAW, zero replay;
  - setter enviat una vegada a release+8,002403 s;
  - resposta literal `0x2019 PTP Device Busy / was not set`;
  - 1/320 conegut abans i confirmat de nou al cleanup;
  - `physical_state_unknown=false`, `cleanup_ok=true`.
- raw_evidence:
  - inventari pre 924 i post 927, identitat exacta i CFexpress 00010001;
  - delta immutable exactament +3 CR3, zero removals;
  - `572A3356.CR3`: 1/320, 0 EV, RAW Electronic, inspeccio PASS;
  - `572A3357.CR3`: 1/2500, -3 EV, RAW Electronic, inspeccio PASS;
  - `572A3358.CR3`: 1/40, +3 EV, RAW Electronic, inspeccio PASS;
  - ordre AEB `0,-,+`, 3 shots, model i body serial exactes.
- evidence:
  - run S1: `controller/runs/20260805T175453_lab_r6m3_s1_release_8s_shutter_readiness_v1_run`;
  - result SHA-256: `20fde8cc6796419a909914babe92b411d3c225eace120ac020468dd008e8aaef`;
  - manifest SHA-256: `cbfec1a79991eb9f95cb8809dcfe0e153ba579d20235aea08ae8b0dea0ac4ebc`;
  - snapshot SHA-256: `33b02b5215e3e27486a21beb3ca55644aa1091b329a42c2c59ea48e91099a314`;
  - events SHA-256: `7f1a3e0056a6668d0b986d8cd019bc867c6fa0bbc6d450a62d31ab3f58ebc8f6`;
  - inventaris SHA-256 pre/post: `bb683900...df62`, `13e7c0ac...7030`;
  - delta SHA-256: `1d8929424f5122d96301bb05cdba045821104a6871172808cd2691c7b1358cbb`;
  - inspections SHA-256: `26b24a2d...ba25`, `2398913d...1b75`,
    `cd5ae07b...42c1`.
- demonstrated:
  - AEB3 materialitzat com +3 CR3 integres en ordre body-specific;
  - release+8,002 s encara no permet setter shutter en aquest context.
- missing:
  - primer delay post-release amb adopcio shutter; cap certificat S1 PASS;
  - S1-12, G6, G40/H90 i tres histories completes.
- next_gate:
  - S1 release+12 s, nova captura AEB3 i manifests +3 CR3; requereix
    autoritzacio fisica fresca i concreta.
- release_impact:
  - 6 i 8 s queden refutats; 120 i 114 RAW C2-C3 no es poden promocionar;
  - nomes queda candidata la frontera de 35 grups/105 RAW si S1-12 PASS;
  - cap perfil operatiu, app, bundle o release publica modificat.
- handoff:
  - `SERIAL_WRITES` alliberat;
  - zero processos Eclipse Command, eclipse_capture_r6m3, gphoto2,
    snapshots, downloads o inspectors a les 2026-08-05T15:58:17Z;
  - cap S1-12, G6/G40, GUI, LaunchServices, EDSDK, bundle o release executat.

## Main R6 S1-6s physical campaign — RELEASED 2026-08-05

- status: RELEASED
- updated_utc: 2026-08-05T15:51:17Z
- released_utc: 2026-08-05T15:51:17Z
- task: Executar i certificar S1 release+6 s amb un AEB3 i +3 CR3 exclusius.
- phase: R6_S1_8S_PHYSICAL_AUTHORIZATION_PENDING
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-05T15:47:02Z
- authorization:
  - Pere autoritza manifest CFexpress pre/post, una captura AEB3, setter
    1/320 -> 1/160 a release+6 s, readback, restore 1/320 i inspeccio dels
    tres CR3; stop al primer error i zero replay.
  - treball desates amb maxima prioritat dins d'aquest abast exacte.
- scope:
  - identitat exacta i inventari CFexpress pre sense captura;
  - un unic press/release AEB3 i un unic setter release-anchored a +6 s;
  - restore 1/320, inventari post, delta +3, download/inspeccio dels tres
    CR3 nous i certificat immutable si tota l'evidencia quadra.
- excluded:
  - cap segon trigger, S1-8/12, G6, G40/H90, GUI, LaunchServices, EDSDK,
    bundle o release publica.
- mission_first:
  - trigger ambigu es consumeix i no es repeteix;
  - Busy net `was not set` conserva 1/320 conegut i no es reintenta;
  - write ambigu/estat desconegut o ledger insegur atura nomes R6.
- result:
  - S1 release+6 s: FAIL de readiness body-specific;
  - un unic AEB3 amb press/release ACK i ledger de 3 RAW, zero replay;
  - setter enviat una vegada a release+6,018203 s;
  - resposta literal `0x2019 PTP Device Busy / was not set`;
  - 1/320 conegut abans i confirmat de nou al cleanup;
  - `physical_state_unknown=false`, cleanup net.
- raw_evidence:
  - inventari pre 921 i post 924, identitat exacta i store CFexpress 00010001;
  - delta immutable exactament +3 CR3, zero removals/canvis visibles;
  - `572A3353.CR3`: 1/320, 0 EV, RAW Electronic, inspeccio PASS;
  - `572A3354.CR3`: 1/2500, -3 EV, RAW Electronic, inspeccio PASS;
  - `572A3355.CR3`: 1/40, +3 EV, RAW Electronic, inspeccio PASS;
  - ordre AEB `0,-,+`, 3 shots, model i body serial exactes.
- evidence:
  - run S1: `controller/runs/20260805T174758_lab_r6m3_s1_release_6s_shutter_readiness_v1_run`;
  - result SHA-256: `a1de1820132e93d94387f5c63d4f268eec8640f7a1371b1ac06440a1d58dfffe`;
  - manifest SHA-256: `04531b96f10e2b9198f9d6050ed00e13685aabf095162cf03b45174153e4e8b9`;
  - snapshot SHA-256: `5d45d1601b74a7faa199f96a6668501f9fa5272e5bfda04d05a1d3a4ce45bd27`;
  - events SHA-256: `0a25fe9a317692e1abd460cfacf6fef97e4986105a67ee2a24bf779472ee7156`;
  - delta SHA-256: `f24a54fdc50a21eb0631da7c1ac5c868ed3016c00c3470f4b6cf4e5324e29c23`;
  - inspections SHA-256: `a362ae3b...e58df`, `73850f15...e42a`,
    `462822f8...27c7`.
- demonstrated:
  - AEB3 materialitzat com +3 CR3 integres en ordre body-specific;
  - release+6,018 s encara no permet setter shutter en aquest context.
- missing:
  - primer delay post-release amb adopcio shutter; cap certificat S1 PASS;
  - G6, G40/H90 i tres histories completes.
- next_gate:
  - S1 release+8 s, nova captura AEB3 i manifests +3 CR3; requereix
    autoritzacio fisica fresca i concreta.
- handoff:
  - `SERIAL_WRITES` alliberat;
  - zero processos Eclipse Command, mission_host, eclipse_capture, gphoto2,
    snapshots, downloads o inspectors externs a les 2026-08-05T15:51:17Z;
  - cap S1-8/12, G6/G40, perfil operatiu, bundle o release executat.

## Main R6 S0-B normal-screen retry — RELEASED 2026-08-05

- status: RELEASED
- updated_utc: 2026-08-05T15:39:57Z
- released_utc: 2026-08-05T15:39:57Z
- task: Executar S0-B amb AEB +/-3, pantalla normal i USB reconnectat.
- phase: R6_S1_6S_PHYSICAL_AUTHORIZATION_PENDING
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-05T15:36:20Z
- authorization:
  - `AEB +/-3, pantalla normal i USB connectat; autoritzo S0-B.`
- scope:
  - una sola obertura amb identitat exacta;
  - exactament 1/320 -> 1/160 -> 1/320 si el preflight es complet;
  - zero captures, zero reintents i stop al primer error.
- excluded:
  - S1, triggers, CR3, G6/G40/H90, GUI, LaunchServices, EDSDK i release.
- mission_first:
  - qualsevol error consumeix aquest intent sense replay;
  - write ambigu/estat desconegut atura nomes R6; les altres cameras continuen.
- result:
  - `S0_MODE_DISCRIMINATOR_PASS` fisic amb identitat R6 exacta;
  - 1/320 -> 1/160 adoptat/readback en 432,222 ms totals;
  - 1/160 -> 1/320 adoptat/readback en 427,902 ms totals;
  - un intent per write, zero captures, Busy, retries, recovery, skips o replay;
  - cleanup i restore nets; AEB +/-3 i shutter final 1/320 confirmats;
  - bateria 31% advisory, no gate.
- evidence:
  - run: `controller/runs/20260805T173647_lab_r6m3_s0b_continuous_aeb_on_shutter_readiness_v1_run`;
  - result SHA-256: `4ff4af6364044f064afd5097500900786189322575a8586da45c12098d4d97fd`;
  - manifest SHA-256: `8961c14640c103fed81fd0308aab99a508edeb40f9986408e49b1f677a978d19`;
  - snapshot SHA-256: `6a4c996fd43135d00ea7c274c915bfdd44557f23ea7b016cd46fe024303b02f1`;
  - events SHA-256: `7bb705af4fff9cbef8d3e4ee1d7e122e41a4039cd79e7c7d6e1c55fd748ad0c8`;
  - certificat SHA-256: `9e3760ae01c2d3b1287d40a7e9058e65fb89ddeb441de29ca8de8b5c4fb64191`.
- offline_fix:
  - el certificador ara exigeix `final_release_confirmed=None` en S0 sense
    trigger i `True` en S1 amb trigger; evita inventar un release en zero-capture;
  - focal certificador 10/10 i controlador complet 1.032/1.032;
  - una primera suite completa va mostrar un unic flake d'ordre en un test
    Canon generic; el test focal, el modul sencer i la suite completa repetida
    van passar.
- demonstrated:
  - setter shutter funciona en Continuous high speed + AEB +/-3 sense captura.
- missing:
  - adopcio release-anchored despres d'un AEB3, delta exclusiu +3 CR3 i
    inspeccio dels tres RAW; G6, G40/H90 i tres histories C1-C4.
- next_gate:
  - S1 release+6 s, una captura AEB3 i un setter 1/320 -> 1/160, amb manifest
    CFexpress pre/post, +3 CR3, inspeccio i restore; exigeix autoritzacio fresca.
- handoff:
  - `SERIAL_WRITES` alliberat;
  - zero processos Eclipse Command, mission_host, eclipse_capture, gphoto2 o
    suites QA externs detectats a les 2026-08-05T15:39:57Z;
  - cap perfil operatiu, bundle ni release promocionat.

## Main R6 S0-B physical retry — RELEASED 2026-08-05

- status: RELEASED
- updated_utc: 2026-08-05T15:33:00Z
- released_utc: 2026-08-05T15:33:00Z
- task: Repetir exclusivament S0-B despres que Pere ha activat AEB +/-3.
- phase: R6_S0_B_CAMERA_MENU_EXIT_PENDING
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-05T15:31:58Z
- authorization:
  - `Autoritzo repetir S0-B: identitat i 1/320 -> 1/160 -> 1/320,
    zero captures, stop al primer error.`
- scope:
  - validar de nou port i identitat exacta;
  - executar una sola timeline de dos writes amb readback;
  - zero captures, zero reintents i aturada al primer error.
- excluded:
  - S1, triggers, CR3, manifests de targeta, G6/G40/H90, GUI,
    LaunchServices, EDSDK i qualsevol canvi de bundle/release.
- mission_first:
  - Busy net `was not set` conserva l'estat anterior conegut i no es repeteix;
  - write ambigu/estat desconegut o identitat divergent atura nomes R6.
- result:
  - model i PTP serial exactes llegits abans de fallar la readiness;
  - immediatament despres, gphoto2 ha retornat `/main not found in
    configuration tree` en llegir `autoexposuremode`;
  - fallada abans del preflight complet i abans de qualsevol mutacio;
  - zero `set-config`, zero captures/triggers, zero reintents/recovery;
  - cleanup net, estat fisic no marcat desconegut i lock alliberat.
- evidence:
  - run: `controller/runs/20260805T173232_lab_r6m3_s0b_continuous_aeb_on_shutter_readiness_v1_run`;
  - result SHA-256: `edceada1acf5e07fc4e7394198a4608abbb4ab7d47f4f706ae8263c96a27f0f1`;
  - manifest SHA-256: `df73676c49f8ccdafbb6f66992098c179ed459bf887f00eafb23add795c0667a`;
  - snapshot SHA-256: `6a4c996fd43135d00ea7c274c915bfdd44557f23ea7b016cd46fe024303b02f1`;
  - events SHA-256: `2b225ae1f59383d00142104c1efd1bd1bf236fd3dd63285a58b3b3598a46b951`.
- next_gate:
  - sortir completament del menu de camera sense apagar-la i tornar a la
    pantalla normal de fotografia; qualsevol nou S0-B exigeix autoritzacio
    fresca i exacta.
- handoff:
  - `SERIAL_WRITES` alliberat;
  - zero processos Eclipse Command, mission_host, eclipse_capture, gphoto2 o
    suites QA detectats a les 2026-08-05T15:33:00Z;
  - cap write ni captura executats.

## Main R6 S0-B physical gate — RELEASED 2026-08-05

- status: RELEASED
- updated_utc: 2026-08-05T15:18:27Z
- released_utc: 2026-08-05T15:18:27Z
- task: Executar exclusivament el gate fisic S0-B autoritzat per Pere.
- phase: R6_S0_B_AEB_MANUAL_PRECONDITION_PENDING
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-05T15:16:31Z
- authorization:
  - Pere ha respost `fet` despres de la peticio exacta d'engegar la R6 i
    autoritzar identitat read-only mes exactament dos writes
    1/320 -> 1/160 -> 1/320, zero captures.
- scope:
  - resoldre port per identitat USB i validar model/series exactes;
  - executar S0-B una sola vegada, un intent/readback per write;
  - aturar-se al primer error i no repetir cap accio ambigua.
- excluded:
  - cap captura, S1, snapshot/descarga CR3, G6, G40/H90, GUI,
    LaunchServices, EDSDK o canvi de bundle/release.
- mission_first:
  - un Busy net `was not set` conserva l'estat conegut i no es reintenta;
  - estat fisic desconegut o identitat/propietat divergent atura nomes R6;
  - cap altra camera queda bloquejada.
- result:
  - intent unic tancat abans de la timeline: `aeb=off`, esperat `+/- 3`;
  - identitat exacta validada (model R6 Mark III, PTP serial i body serial);
  - shutter llegit `1/320`, estat fisic conegut, `physical_state_unknown=false`;
  - zero `set-config`, zero captures/triggers, zero retries/recovery;
  - cleanup net i lock de camera alliberat.
- evidence:
  - run: `controller/runs/20260805T171746_lab_r6m3_s0b_continuous_aeb_on_shutter_readiness_v1_run`;
  - result SHA-256: `c4dff6b8e7500d79acbb8b8b1f8020432988836c8d0aeff56fc70850a1e283a9`;
  - manifest SHA-256: `e4c7f179996f85a5b3c854be30f425418d5eccfcced673b4c2301998967c63c9`;
  - snapshot SHA-256: `6a4c996fd43135d00ea7c274c915bfdd44557f23ea7b016cd46fe024303b02f1`;
  - events SHA-256: `5a656286381ec3fad461edef5c6e92769ef76c9aadf66a27a6f39e0dcc971e78`.
- next_gate:
  - Pere ha de reactivar manualment AEB `+/- 3`; qualsevol nou intent S0-B
    necessita autoritzacio fresca i exacta.
- handoff:
  - `SERIAL_WRITES` alliberat;
  - zero processos Eclipse Command, mission_host, eclipse_capture, gphoto2 o
    suites QA detectats a les 2026-08-05T15:18:27Z;
  - cap write ni captura executats.

## Main R6 release-anchored readiness repair — RELEASED 2026-08-05

- status: RELEASED
- updated_utc: 2026-08-05T15:10:16Z
- released_utc: 2026-08-05T15:10:16Z
- task: Reparar el handoff S1 perquè cap setter shutter comenci abans del
  `config_ready` real ancorat al release.
- phase: R6_S0_B_CAMERA_POWER_AND_AUTHORIZATION_PENDING
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-05T15:07:21Z
- discovered_offline:
  - S0-B dry-run PASS amb zero captures i dos setters;
  - S1 6 s dry-run FAIL abans de qualsevol contacte: el setter a release+6 s
    se solapa 50 ms amb la finestra config, perquè l'auditor incorpora la
    tolerancia del capture;
  - el runtime accepta readiness dins la tolerancia pero encara no espera
    explicitament fins a `config_ready_until_ns` abans d'un setter.
- safety:
  - corregir el runtime R6 perquè esperi readiness dins la tolerancia;
  - readiness mes enlla de la tolerancia conserva skip/fail existent;
  - zero camera, PTP, gphoto2 fisic, trigger, GUI o bundle.
- implemented:
  - S1 declara un handoff acotat entre el capture i el setter;
  - el runtime R6 espera fins a `config_ready_until_ns` quan readiness cau
    dins la tolerancia; readiness fora de tolerancia conserva skip/fail;
  - el validador admet el mateix handoff amb deadline relatiu
    `must_finish_by_s`, no nomes amb contactes C2/C3.
- qa:
  - S0-B i S1 6/8/12 `dry-run` del worker: 4/4 COMPLETE;
  - focal compilador/certifier/worker 55/55;
  - controlador complet 1.031/1.031;
  - `git diff --check` verd i zero EDSDK als artefactes tocats.
- next_gate:
  - confirmacio d'encesa i autoritzacio fresca d'S0-B; zero captures, dos
    writes 1/320 -> 1/160 -> 1/320 amb readback i stop al primer error.
- handoff:
  - `SERIAL_WRITES` alliberat;
  - zero processos Eclipse Command, mission_host, eclipse_capture, gphoto2 o
    suites QA detectats a les 2026-08-05T15:10:16Z;
  - cap contacte fisic executat.

## Main R6 deterministic frontier schedules — RELEASED 2026-08-05

- status: RELEASED
- updated_utc: 2026-08-05T15:03:52Z
- released_utc: 2026-08-05T15:03:52Z
- task: Convertir la frontera RAW S1 6/8/12 s en cronologies candidates
  deterministes sense escollir bases ni activar cap programa no qualificat.
- phase: R6_S0_B_CAMERA_POWER_AND_AUTHORIZATION_PENDING
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-05T15:02:00Z
- scope:
  - nomes compilador S0/S1, perfils lab derivats, proves i recerca R6;
  - zero app/bundle, Sony/6D, UTC, backend, EDSDK o contacte fisic.
- physical_boundary:
  - S0-B espera confirmacio d'encesa i autoritzacio fresca de Pere;
  - camera, PTP, gphoto2, triggers i GUI fisica fora d'abast.
- result:
  - cada opcio de frontera inclou ara targets absoluts des de C2, gaps
    normals, gaps de transicio i indexs de canvi deterministes;
  - el primer grup i els dos ultims grups de totalitat queden reservats a
    1/320; les bases interiors continuen diferides a G6 i Exposicions;
  - totes les cronologies son `candidate_only` i no executables.
- qa:
  - focal compilador/certifier/worker 54/54;
  - controlador complet 1.030/1.030;
  - `git diff --check` verd i zero EDSDK als artefactes tocats.
- handoff:
  - `SERIAL_WRITES` alliberat;
  - zero processos Eclipse Command, mission_host, eclipse_capture, gphoto2 o
    suites QA detectats a les 2026-08-05T15:03:52Z;
  - espera exclusiva de confirmacio d'encesa i autoritzacio S0-B de Pere.

## Main R6 totality RAW frontier — RELEASED 2026-08-05

- status: RELEASED
- updated_utc: 2026-08-05T15:00:50Z
- released_utc: 2026-08-05T15:00:50Z
- task: Maximitzar els RAW R6 dins C2-C3 per cada retard de canvi que S1
  pugui demostrar, sense activar setters no qualificats ni degradar Mission
  First.
- phase: R6_S0_B_CAMERA_POWER_AND_AUTHORIZATION_PENDING
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-05T14:57:19Z
- physical_boundary:
  - Pere ha apagat la R6; zero GUI fisica, PTP, gphoto2, trigger o contacte;
  - S0-B i S1 continuen exigint autoritzacio fresca i concreta.
- preserved:
  - programa public/del bundle 0.7.16 intacte;
  - fallback operatiu font fix 1/320, G40, zero setters post-arm;
  - cap canvi Sony/6D, UTC, backend o EDSDK.
- intended_delta:
  - calcular la frontera exacta entre nombre de transicions, grups AEB3 dins
    totalitat i cinc grups parcials per als delays S1 6/8/12 s;
  - deixar la decisio i les cronologies candidates com infraestructura
    offline no executable fins als gates fisics S0/S1/G6/G40-H90.
- result:
  - frontera exacta amb canvi+restore minim: S1 6 s permet 40 grups/120 RAW
    C2-C3 i zero parcials; 8 s permet 38/114 i dos parcials; 12 s permet
    35/105 i cinc parcials;
  - conservant els cinc grups parcials, els maxims son 4/3/2 transicions i
    35 grups/105 RAW C2-C3 per delays 6/8/12 s;
  - els tres perfils S1 publiquen `post_s1_totality_raw_frontier` com
    `candidate_only=true`, `operational_compile_ready=false`; cap app ni
    materialitzacio operativa ha canviat.
- qa:
  - focal compilador/certifier/worker 54/54;
  - controlador complet 1.030/1.030;
  - perfils checked-in deterministes i `git diff --check` verd.
- next_gate:
  - encendre la R6 i obtenir autoritzacio fresca per S0-B: zero captures,
    exactament dos writes 1/320 -> 1/160 -> 1/320, un intent i readback;
  - si S0-B passa, S1 6 s i aturar al primer PASS; cap versio nova abans de
    G6/G40-H90 i prova fisica des del bundle candidat.
- handoff:
  - `SERIAL_WRITES` alliberat;
  - zero processos Eclipse Command, mission_host, eclipse_capture, gphoto2 o
    suites QA detectats a les 2026-08-05T15:00:50Z;
  - camera encara apagada i zero contacte fisic executat.

## Main R6 automatic shutter recovery — RELEASED 2026-08-05

- status: RELEASED
- updated_utc: 2026-08-05T14:54:02Z
- released_utc: 2026-08-05T14:54:02Z
- task: Fer que la R6 III adopti automaticament el shutter durant totalitat i
  maximitzar RAW dins C2-C3 sense violar Mission First.
- phase: R6_S0_B_PHYSICAL_AUTHORIZATION_PENDING
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-05T14:42:48Z
- proved_gap:
  - el run fisic `20260805T155615...r6m3...run` va executar quatre setters
    shutter, tots aproximadament 5,46 s despres del press anterior, i els
    quatre van acabar `0x2019 PTP Device Busy / was not set` amb readback
    previ 1/320 writable;
  - l'espera publicada de 5,4 s esta ancorada al press, o sigui nomes deixa
    aproximadament 4,4 s des del release real d'un hold d'1 s; zero
    transicions dins timeline estan demostrades;
  - Pere va demanar Stop despres del press 28: els grups finals absents no
    demostren supressio automatica, i 84 commits esperats/Available Shots no
    acrediten un manifest CR3;
  - abans de redissenyar la missio cal discriminar si el lock depen d'AEB on,
    de l'activitat post-captura o de la sessio, amb S0/S1 body-specific i
    readback; cap timing d'un altre cos es transferible.
- frozen_safety:
  - Busy net `was not set` conserva l'ultim shutter conegut, zero retry i
    totes les captures futures segures;
  - write ambigu, identitat/propietat divergent o ledger insegur aturen nomes
    la R6; els altres canals continuen;
  - cap ACK, ledger card-only o comptador de capacitat es dira prova RAW.
- exclusions:
  - zero GUI fisica, PTP, gphoto2, triggers o contacte amb camera;
  - zero canvis Sony/6D, UTC, EDSDK o backend.
- implemented:
  - detectada i corregida una contradiccio latent de la font 0.7.17: la
    geometria dinamica no qualificada ja no es materialitza automaticament
    per durada; mentre el certificat fisic no existeix, el programa
    executable es el fallback fix G40 a 1/320, sense setters post-arm;
  - el controlador selecciona el guard per `planning_tier` immutable i
    rebutja qualsevol setter injectat o contracte dinamic no promocionat;
    la geometria de sis transicions es conserva nomes com preview lab
    explicitament no executable;
  - compilador offline determinista S0/S1 i sis perfils lab ocults: S0-A,
    S0-B, S0-C i S1 a 6/8/12 s des del release real;
  - S0 executa zero captures; S1 executa un sol press AEB3, un sol setter i
    cleanup 1/320 nomes si hi ha adopcio demostrada;
  - l'escombrat S1 no repeteix els delays 2/4 s ja refutats i s'atura al
    primer PASS;
  - capacitat offline: un PASS a 6/8/12 s admet com a maxim 4/3/2
    transicions mantenint els 35 grups/105 RAW qualificats dins totalitat.
  - certifier offline immutable S0/S1: vincula perfil, manifest, result i
    events per hash; exigeix una sola ordre+readback per setter i rebutja
    Busy/fallback, retry, reconnexio, estat desconegut o cleanup divergent;
  - S1 no passa sense retard mesurat des del release real, restore 1/320,
    delta CFexpress exacte +3 i tres CR3 reoberts en ordre
    1/320, 1/2500, 1/40; el rebut prohibeix promocio de missio/release.
- qa:
  - compilador focal S0/S1 5/5 i certifier focal 9/9;
  - controlador complet 1.029/1.029;
  - GUI offscreen 428/428;
  - `git diff --check` verd i zero EDSDK als artefactes nous.
- next_gate:
  - amb autoritzacio fresca, executar primer S0-B (zero captures, dos writes);
  - si S0-B falla, S0-C; si passa, S1 6 s i nomes continuar 8/12 s fins al
    primer PASS;
  - no modificar ni construir el perfil public fins que el resultat fisic
    fixi el nombre real de transicions i el gate G6/G40-H90 reconcilii CR3.
- handoff:
  - `SERIAL_WRITES` alliberat;
  - Pere ha apagat la R6 per preservar bateria; queda fora de contacte fins
    que la torni a encendre i autoritzi concretament S0-B;
  - zero processos Eclipse Command, mission_host, eclipse_capture, gphoto2 o
    suites QA detectats a les 2026-08-05T14:54:02Z;
  - cap contacte fisic, LaunchServices ni GUI fisica executats.

## Main R6 throughput/shutter recovery / 0.7.16 — RELEASED 2026-08-05

- status: RELEASED
- updated_utc: 2026-08-05T13:34:39Z
- released_utc: 2026-08-05T13:34:39Z
- task: Corregir la regressio fisica 0.7.15 de la R6: Busy net del primer
  setter va aturar 36/40 press; recuperar canvi dinamic i maxim RAW Mission
  First.
- phase: APP_0_7_16_PORTABLE_QA_PASS_PHYSICAL_GATE_PENDING
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-05T13:16:11Z
- proved_from_run:
  - `20260805T145506...r6m3...run` va compilar 40 press/120 RAW i sis
    setters, pero el primer `1/320 -> 1/160` a C2+2,365 s va rebre
    `was not set (PTP Device Busy)`;
  - el cos havia conservat 1/320 conegut, pero el wrapper el va marcar
    `physical_state_unknown` i va acabar amb nomes 4 press/12 RAW esperats;
  - reconnexio read-only exacta va tornar a estar llesta a C2+5,327 s.
- frozen_delta:
  - Busy net `was not set` conserva l'estat anterior i degrada nomes el
    setter; mai cancella captures futures ni genera replay;
  - conservar 40 grups totals, 35 dins totalitat i 105 RAW esperats C2-C3;
  - sis intervals de canvi de 5,95 s, resta >=2,2 s (G40 demostrat), setter
    0,5 s abans del grup seguent i `config_ready_s=5,4`;
  - dynamic nomes si totalitat >=98,7 s; per sota, G40 fix 1/320 sense setters;
  - write ambigu, identitat/propietat divergent o ledger insegur continuen
    aturant nomes la R6.
- exclusions:
  - zero canvis Sony/6D, UTC, EDSDK o backend;
  - zero GUI fisica, PTP, gphoto2, triggers o contacte amb camera.
- app_state_at_acquire: app i processos de camera tancats.
- implemented:
  - Busy net `was not set` ja no marca estat desconegut, no reconnecta i no
    repeteix el write; el setter queda degradat i les captures futures usen
    l'ultima base confirmada;
  - el cas 98,8 s conserva 40 grups/120 RAW esperats, 35/105 dins totalitat;
    sis gaps de canvi 5,95 s, 28 gaps normals 2,204 s i `config_ready_s=5,4`;
  - dinamic nomes amb totalitat >=98,7 s; per sota, fallback G40 fix 1/320;
  - controller R6 `0.4.7-r6m3-dynamic-aeb3-v2`, zero canvis a altres cossos.
- qa_and_bundle:
  - focal R6 88/88, GUI 426/426, controlador 1.015/1.015, fuzz
    67.392/67.392, perfils curts, beta 4/4 i 20/20, QA portable PASS;
  - Eclipse Command 0.7.16, executable SHA
    `91496f9d07e69d20229d8b73c0d21fcc57f20091ea3ff29b9e96ab8ae71f5c55`;
  - manifest 49 fonts SHA
    `ffacec927d0a9958f6819df56c168d022af221ed2bf1a82738b943ea0ecc258d`;
  - rollback 0.7.15 verificat a
    `gui/dist/Eclipse Command.app.previous-20260805T133203Z-22474`.
- physical_boundary:
  - reparacio i cronologia demostrades offline; adopcio dels setters sota
    carrega encara no demostrada;
  - falten autoritzacio fresca, S0/S1/G6/G40-H90 dinamic i historia C1-C4
    40/40 amb delta CFexpress/EXIF, readbacks/fallbacks i estat final conegut.
- handoff:
  - `SERIAL_WRITES` alliberat; pid GUI i build lock absents;
  - zero processos Eclipse/gphoto2 propis; el build va usar nomes el refresc
    de metadata `lsregister -f` previst i no va obrir l'app.

## Main UTC 400 ms / 0.7.15 — RELEASED 2026-08-05

- status: RELEASED
- updated_utc: 2026-08-05T13:08:38Z
- released_utc: 2026-08-05T13:08:38Z
- task: Fer `BOUNDED` inclusiu fins a 400 ms i `DEGRADED` nomes per sobre
  de 400 ms fins a 1 s, sense alterar Mission First.
- phase: APP_0_7_15_PORTABLE_QA_PASS_PHYSICAL_GATES_UNCHANGED
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-05T13:00:39Z
- frozen_delta:
  - `BOUNDED`: max error <=400 ms;
  - `DEGRADED`: max error >400 ms i <=1 s;
  - `HOLDOVER/TIME ERROR`: max error >1 s;
  - UTC continua advisory i no es prerequisit de `Start mission`.
- scope: constant i proves UTC, textos canònics, versio 0.7.15, QA i bundle.
- exclusions:
  - zero canvis a timings, shutters, buffers, setters, perfils o backends;
  - zero deltes nous R6, Sony o Canon 6D;
  - zero GUI fisica, PTP, gphoto2, triggers o contacte amb cameras.
- app_state_at_acquire: app i processos de camera tancats.
- result:
  - Eclipse Command 0.7.15 construit i validat;
  - executable SHA
    `7af96b5f11c2bed8f4babbd2e4d2b65a59a4d1223ddfeaef48f49d595729a27d`;
  - manifest 49 fonts SHA
    `07b9cfa300862acc0ea5d59bae116c83f38ad4b9ccb00825e1b2fa22b2baee58`;
  - focal UTC 50/50, GUI 426/426, controlador 1.015/1.015, fuzz
    67.392/67.392, perfils curts, diff-check, beta 4/4 i 20/20, QA portable
    PASS;
  - lectura passiva final durant QA: `TIME_OK`, 275 ms, `BOUNDED`;
  - rollback 0.7.14 verificat a
    `gui/dist/Eclipse Command.app.previous-20260805T130623Z-16792`.
- handoff:
  - `SERIAL_WRITES` alliberat amb zero processos propis;
  - zero GUI fisica, PTP, gphoto2, triggers o cameras;
  - el build ha executat nomes el refresc de metadata `lsregister -f` previst;
  - cap evidencia fisica ni qualificacio R6 ha estat reescrita.

## Main combined 0.7.14 release — RELEASED 2026-08-05

- status: RELEASED
- updated_utc: 2026-08-05T12:53:22Z
- released_utc: 2026-08-05T12:53:22Z
- task: Publicar coherentment els llindars UTC advisory i la reparacio
  body-specific R6 de shutter dinamic com Eclipse Command 0.7.14.
- phase: APP_0_7_14_PORTABLE_QA_PASS_PHYSICAL_GATES_PENDING
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-05T12:42:34Z
- frozen_deltas:
  - GUI UTC: BOUNDED <=180 ms, DEGRADED <=1 s, >1 s HOLDOVER, sempre advisory;
  - R6: 40 brackets AEB3/120 RAW esperats amb sis setters agrupats dins
    totalitat >=96 s i fallback fix 1/320 per sota de 96 s;
  - zero canvis de release nous per Sony o Canon 6D.
- release_gate:
  - Exposicions: parcials R6 continuen 1/320 al cas canonic 10 graus/700 m;
    l'escala nova afecta nomes la totalitat;
  - Localitzacions: cap lloc ni compensacio d'airmass entra al codi;
  - Guia universal: ordre+readback, zero retries, identitat exacta,
    physical_state_unknown hard-stop del canal i ledger/no-replay preservats;
  - public/privat: gphoto2 unic backend operatiu; zero EDSDK al paquet public.
- physical_boundary:
  - el programa dinamic es candidat offline, no qualificacio fisica;
  - `post_arm_shutter_setter_qualified=false`; falten S0, S1, G6, G40/H90,
    delta CFexpress/EXIF i tres histories completes.
- authorization_boundary:
  - build i QA exclusivament offline; zero GUI fisica, PTP, gphoto2, triggers
    o cameras; LaunchServices limitat al refresc de metadata del build.
- qa_and_bundle:
  - GUI 426/426; controlador 1.015/1.015; fuzz 67.392/67.392;
  - perfils curts i diff-check PASS; beta offline 4/4 i 20/20;
  - QA portable PASS, 114 Mach-O, arm64, macOS 26.0;
  - executable SHA
    `0f85a3ffa13f0a4b2e958c56e689a3c34cc5d74790853d2aef90442c141afd82`;
  - manifest 49 fonts SHA
    `edb45e894ae3234da7ad46622836dd56eeb03bba2f6cc73fc481715620bf65cd`;
  - rollback 0.7.13 verificat a
    `gui/dist/Eclipse Command.app.previous-20260805T125027Z-11632`.
- execution_note:
  - zero GUI fisica, PTP, gphoto2, trigger o camera contactats;
  - el build canonic va executar el `lsregister -f` obligatori del script per
    refrescar metadata de LaunchServices; no va obrir l'app;
  - el primer build sandboxed va fallar abans d'activar res perquè no podia
    obrir el shlock; la repeticio autoritzada va completar atomicament.
- handoff:
  - informe `gui/QA_REPORT_0.7.14_2026-08-05.md` publicat;
  - zero processos propis pendents i SERIAL_WRITES alliberat.

## R6 dynamic shutter repair — RELEASED 2026-08-05

- status: RELEASED
- updated_utc: 2026-08-05T12:39:50Z
- released_utc: 2026-08-05T12:39:50Z
- task: Reparar la materialitzacio body-specific R6 perquè variï la base AEB
  durant la totalitat sense sacrificar els 40 press Mission First.
- phase: R6_SOURCE_OFFLINE_QA_PASS_BUNDLE_AND_PHYSICAL_GATES_PENDING
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-05T12:26:30Z
- proved_from_latest_run:
  - `20260805T140828...r6m3...run` va usar encara la 0.7.13 fixa:
    40/40 accions, 120/120 commits, zero skips, estat final conegut i cap
    setter; `fixed_preflight_shutter=true` i base unica 1/320;
  - per tant el problema era la materialitzacio deliberadament fixa, no una
    ordre de canvi perduda pel controlador.
- implemented:
  - el cas canonic C2-C3 de 98,8 s conserva 40 brackets/120 RAW esperats i
    intercala sis setters agrupats abans dels grups 5, 12, 19, 25, 31 i 37:
    1/160 -> 1/80 -> 1/40 -> 1/20 -> 1/10 -> 1/320;
  - els grups C2 i C3 es mantenen a 1/320; la unio esperada te 12 shutters
    fisics diferents entre 1/2500 i 0,8 s;
  - per sota de 96 s el compilador conserva el fallback G40 fix 1/320 sense
    setters; el llindar exacte 96 s passa auditoria temporal estricta;
  - Busy/no-adopcio neta degrada l'HDR i conserva tots els press segurs amb
    la triada del darrer shutter conegut; estat post-write desconegut atura
    nomes la R6, i cap trigger ambigu es repeteix;
  - worker anti-tamper reconeix exactament 46 accions dinamiques o les 40 del
    fallback, gphoto2 continua sent l'unic backend operatiu i no entra EDSDK.
- files:
  - `gui/eclipse_command/adaptive_profiles.py`;
  - `gui/tests/test_adaptive_profiles.py`;
  - `controller/eclipse_capture_r6m3.py`;
  - `controller/profiles/candidate_r6m3_vsd90ss_cfexpress_cardonly_v1.json`;
  - `controller/tests/test_r6m3_dedicated_controller.py`;
  - `research/52_R6M3_DYNAMIC_SHUTTER_GATE_2026-08-05.md`.
- qa:
  - GUI 426/426; controlador 1.015/1.015;
  - fuzz adaptatiu 67.392/67.392; `git diff --check` PASS;
  - materialitzacio canònica exacta, fallback 95,999 s, frontera 96 s,
    readback Mission First i mutacio anti-tamper coberts explícitament.
- preserved:
  - delta UTC de Main intacte: BOUNDED 180 ms, DEGRADED 1 s i >1 s
    HOLDOVER; cap canvi propi a time_health, main_window UTC, tests o docs;
  - cap fitxer Sony/6D, timing, buffer, backend o qualificacio transferit.
- bundle:
  - no construit ni substituit: l'app de Pere continuava oberta en 0.7.13;
  - la reparacio viu a la font i requereix una release coherent posterior.
- pending_physical:
  - setters dinàmics continuen `post_arm_shutter_setter_qualified=false`;
  - falten S0, S1, G6, G40/H90, delta CFexpress/EXIF i tres histories abans
    de declarar-los fisicament qualificats.
- handoff:
  - zero GUI fisica, LaunchServices, PTP, gphoto2, trigger o camera contactats;
  - zero processos propis pendents i SERIAL_WRITES alliberat.

## Main UTC advisory thresholds — RELEASED 2026-08-05

- status: RELEASED
- updated_utc: 2026-08-05T12:24:56Z
- released_utc: 2026-08-05T12:24:56Z
- task: Relaxar exclusivament els llindars de salut UTC de la GUI a BOUNDED
  fins a 180 ms, DEGRADED fins a 1 s i error temporal per sobre d'1 s,
  preservant Mission First.
- phase: UTC_SOURCE_QA_PASS_BUNDLE_DEFERRED_APP_OPEN
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-05T12:17:55Z
- scope:
  - `gui/eclipse_command/time_health.py`, textos GUI, proves UTC i
    documentacio directament afectada;
  - salut UTC sempre advisory: cap prerequisit de Start mission, cap stop
    global i cap degradacio d'un canal de camera;
  - preservar tots els canvis preexistents i l'app fisica que Pere executa.
- exclusions:
  - zero canvis a shutters, timings, buffers, setters, perfils o backend R6;
  - zero build/replace del bundle mentre l'app estigui oberta;
  - zero GUI fisica, LaunchServices, PTP, gphoto2, triggers o cameras.
- implemented:
  - `BOUNDED` inclusiu fins a 180 ms, `DEGRADED` inclusiu fins a 1 s i
    `HOLDOVER` per sobre d'1 s o kernel no disciplinat;
  - el dialeg i la verificacio explicita Sync UTC comparteixen el llindar de
    180 ms, sense alterar el gate fisic Canon Stage A de 50 ms;
  - qualsevol salut UTC no BOUNDED continua com a warning advisory i mai
    canvia Start mission, el nombre de canals llançables o l'estat d'un cos.
- qa:
  - `test_time_health` 50/50;
  - `test_main_window_discovery` 66/66;
  - GUI completa 423/423;
  - `git diff --check` PASS.
- bundle:
  - no construit ni substituit: Pere manté oberta l'app 0.7.13 PID 1948
    durant un run i el task R6 ha de poder incorporar el seu delta abans de
    la proxima release coherent.
- r6_handoff:
  - SERIAL_WRITES queda disponible per al task R6; ha de reauditar l'arbre,
    preservar aquest delta UTC i adquirir el lock abans d'editar;
  - cap shutter, timing, buffer, setter, perfil o backend R6 ha estat modificat
    per Main.
- handoff:
  - zero GUI fisica, LaunchServices, PTP, gphoto2, trigger o camera contactats;
  - zero processos propis pendents i SERIAL_WRITES alliberat.

## Main card-only operational evidence — RELEASED 2026-08-05

- status: RELEASED
- updated_utc: 2026-08-05T12:04:16Z
- released_utc: 2026-08-05T12:04:16Z
- task: Eclipse Command 0.7.13; separar confirmacio local Sony del contracte
  Canon card-only sense relaxar Mission First.
- phase: APP_0_7_13_PORTABLE_QA_PASS_PHYSICAL_RECONCILIATION_PENDING
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-05T11:37:21Z
- scope:
  - classificacio terminal, supervisor, GUI, tests, documentacio i build;
  - preservar tots els canvis preexistents i el handoff acabat del task R6;
  - zero canvis a shutters, timings, buffers, setters, perfils o backend R6;
  - zero GUI fisica, LaunchServices, PTP, gphoto2, triggers o cameras.
- release_gate:
  - card_only complet pot ser COMPLETE operatiu amb ledger exacte;
  - CR2/CR3 no reconciliat continua deute fisic informatiu;
  - skips, commits parcials, trigger ambigu, interrupcio, cleanup/restore,
    identitat o ledger insegur continuen WARNING/stop per canal.
- implemented:
  - el contracte explicit `card_only` amb `local_payload_required=false` no
    exigeix fitxers locals: conserva `confirmed_image_count` numeric i declara
    `local_confirmation_applicable=false`;
  - `card_only_committed` exigeix timeline neta, ledger exacte, pla complet,
    postflight, cleanup i restore correctes; una reconciliacio posterior exacta
    pot elevar l'evidencia a `card_only_verified`;
  - contractes desconeguts o antics continuen `committed_unverified`, i zero
    concloent, commits parcials o estat ambigu continuen WARNING;
  - Mission First conserva aillament per canal i accio ambigua consumida sense
    replay; checklist, ISO i deute H90/optica/ciencia continuen informatius;
  - `controller/eclipse_capture.py` Sony conserva exactament el seu SHA previ;
    cap timing, shutter, buffer, setter, perfil o backend R6 ha canviat.
- qa_and_bundle:
  - focal 43/43; GUI 423/423; controlador 1.015/1.015;
    fuzz 67.392/67.392; beta offline 4/4 i 20/20; diff-check PASS;
  - bundle 0.7.13 QA portable PASS, 114 Mach-O, arm64, macOS 26.0;
  - executable SHA
    `afac869ab60cb60b146a75bf09544ef1ca6824fed221b948c7693307a5b0cad7`;
  - manifest 49 fonts SHA
    `69ada25471b9552621ba1713691622457de41d2d2354de1c6eb3b18c328cb0ac`;
  - rollback 0.7.12 verificat a
    `gui/dist/Eclipse Command.app.previous-20260805T115201Z-94986`.
- pending_physical:
  - COMPLETE `card_only` acredita execucio operativa, no prova RAW a targeta;
    CR2/CR3 requereixen reconciliacio body-specific per ser verified;
  - es mantenen els deutes fisics de cada cos publicats al QA 0.7.13.
- handoff:
  - cap GUI, LaunchServices, PTP, gphoto2, trigger o camera contactats;
  - zero processos propis pendents i SERIAL_WRITES alliberat.

## Main feedback 12:21 — RELEASED 2026-08-05

- status: RELEASED
- updated_utc: 2026-08-05T10:59:28Z
- released_utc: 2026-08-05T10:59:28Z
- task: Corregir latencia del checklist durant Sync UTC, separar recordatoris
  i deute extern dels WARNING operatius, diagnosticar el control ISO global i
  definir el cami segur per variar l'obturacio base R6.
- phase: APP_0_7_12_PORTABLE_QA_PASS_PHYSICAL_GATES_PENDING
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-05T10:31:09Z
- scope:
  - codi, tests, documentacio i build; arbre brut preservat;
  - zero trigger, PTP, gphoto2 o contacte fisic nou amb cap camera;
  - auditats nomes els logs ja creats pel run de Pere.
- proved:
  - el run 12:22 completa 40/40 grups AEB3 i 120/120 commits esperats amb
    grups C2 -5,4/-2,7/0,0 i C3 -1,4/+1,3/+4,0 s;
  - la base R6 continua fixa a 1/320 per disseny, i cada grup genera
    1/2500, 1/320 i 1/40;
  - els dos clics ISO 100 van arribar a la R6 exacta, pero el cos va declarar
    `PTP Device Busy`, `was not set` i va conservar ISO 400.
- implemented:
  - checklist exclusivament recordatori: desmarcat mai genera WARNING,
    degradacio o gate START i continua editable durant Sync UTC;
  - candidate/timing/H90/optica/ciencia son informacio de programa, no WARNING
    operatiu, inclosos resultats antics persistits;
  - R6 StorageID corrent exacte acceptat quan PTP no exposa choices;
  - ISO reintenta nomes Busy net `was not set`, persisteix resultat causal i
    mostra `ISO ... NOT SET` amb el valor conservat si s'esgota;
  - gate dinamic R6 documentat a `research/52_R6M3_DYNAMIC_SHUTTER_GATE_2026-08-05.md`;
    cap setter post-arm no qualificat activat al programa viu.
- qa_and_bundle:
  - focal 214/214 GUI i 57/57 ISO/R6;
  - GUI 419/419; controlador 1.011/1.011; fuzz 67.392/67.392;
  - quatre beta runs offline 4/4 i 20/20; perfils curts i diff-check PASS;
  - bundle 0.7.12 QA portable PASS, 114 Mach-O, arm64, macOS 26.0;
  - executable SHA
    `82e0f221c7255c8ecbbbf9e75fee391bd3718ce4bb700b7aac44e9b1de17d80e`;
  - manifest 49 fonts SHA
    `d98f7795323982dd59c0b26757d36b6dbea2887808b4bc9a52d12645bb32530a`;
  - rollback immediat a
    `gui/dist/Eclipse Command.app.previous-20260805T105550Z-77277`.
- pending_physical:
  - repetir ISO 100 a la R6: la 0.7.12 garanteix resultat exacte, no adopcio;
  - executar S0/S1/G6/G40-H90 i tres histories abans d'activar shutters
    dinamics; H90/optica/ciencia continuen informacio pendent.
- handoff:
  - build lock net, cap gui.pid i zero processos propis pendents;
  - SERIAL_WRITES alliberat; cap camera/PTP/gphoto2 contactat.

## Main run 11:38 — RELEASED 2026-08-05

- status: RELEASED
- updated_utc: 2026-08-05T10:14:58Z
- released_utc: 2026-08-05T10:14:58Z
- task: Auditar el run R6 11:38 i corregir causes WARNING, verificacio
  automatica, regressio ISO/Mission First i cobertura C2/C3.
- phase: APP_0_7_11_PORTABLE_QA_PASS_PHYSICAL_RECHECK_PENDING
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-05T09:52:10Z
- scope:
  - codi, tests, documentacio i build; preservar arbre brut;
  - zero trigger/replay fisic ambigu; cap contacte de camera mentre no sigui
    necessari per un gate explicit.
- proved:
  - el preflight R6 automatic era rebutjat pel controlador per aplicar la
    restriccio RUN materialitzat tambe a mode preflight;
  - els botons ISO només feien emergir accidentalment una prova PTP parcial;
    ISO no era ni sera un gate de missio;
  - el run `20260805T113838_candidate_r6m3_vsd90ss_cfexpress_cardonly_v1_run`
    completa 40/40 brackets i 120 CR3 esperats, pero deixa 74 s sense presses
    entre C3-4 s i C3+70 s.
- implemented:
  - preflight R6 Mission First acceptat sense materialitzacio RUN ni accio ISO;
    RUN i recover-disconnects conserven els gates exactes;
  - START continua independent d'ISO, settings, checklist i UTC; guardrails
    documentals i proves explicites afegits;
  - causa exacta de WARNING propagada des de controller stderr/result i
    separada dels advisories a la GUI;
  - mateix envelope 40 AEB3/120 CR3 redistribuit: C2 -5.4/-2.7/0.0 s i
    C3 -1.4/+1.3/+4.0 s, sense setters post-arm, retry ni replay;
  - textos R6 corregits a AEB3 1/2500, 1/320 i 1/40.
- qa_and_bundle:
  - focal GUI/materialitzador/host 132/132; focal R6 43/43;
  - GUI 416/416; controlador 1008/1008; fuzz 67.392/67.392;
  - quatre beta runs offline 4/4 i 16/16; `git diff --check` PASS;
  - bundle 0.7.11 QA portable PASS, 114 Mach-O, arm64, macOS 26.0;
  - executable SHA
    `b401ea162247a949488dc3bbab562e99e8ac18e0824eae6789c882846eb67739`;
  - manifest 49 fonts SHA
    `96ef22a86aeb0c2a5a717fc31d9fe1536ce61a72d6d38020688c02c879bcc6b8`;
  - rollback immediat a
    `gui/dist/Eclipse Command.app.previous-20260805T101058Z-66516`.
- pending_physical:
  - repetir autocheck i TEST RUN amb 0.7.11 per qualificar la nova geometria;
  - H90, HDR, VSD90SS/optica/focus solar i ciencia CR3 continuen warnings.
- handoff:
  - zero processos propis pendents; cap camera/PTP/gphoto2 fisic contactat;
  - SERIAL_WRITES alliberat i arbre brut preservat sense reset/clean/stash.

## Fix dispatch preflight R6 — RELEASED 2026-08-05

- status: RELEASED
- updated_utc: 2026-08-05T09:32:47Z
- released_utc: 2026-08-05T09:32:47Z
- task: Corregir el ValueError de `Check cameras now` que rebutja el pont
  preflight R6 abans de llançar cap controlador.
- phase: APP_0_7_10_PORTABLE_QA_PASS_PHYSICAL_RECHECK_PENDING
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-05T09:15:49Z
- evidence:
  - sessio `20260805T111348_candidate_r6m3_vsd90ss_cfexpress_cardonly_v1_preflight`
    buida: zero launch spec, worker, PTP, write o trigger;
  - `validate_controller_argv_binding` exigeix sempre el controlador dedicat
    i no admet encara `controller/eclipse_camera_setup.py` per mode preflight;
  - RUN ha de continuar acceptant exclusivament el controlador R6 dedicat.
- scope:
  - codi/tests/build; zero camera, PTP, gphoto2, GUI fisica o captures;
  - preservar arbre brut i invariants Mission First.
- implemented:
  - `controller/eclipse_camera_setup.py` admès per perfils dedicats només en
    preflight, tant per path font exacte com per dispatch congelat exacte;
  - RUN conserva obligatori el controlador R6 dedicat i el `run_root` exacte;
  - versio promoguda a 0.7.10 i documentacio canonica actualitzada.
- qa_and_bundle:
  - focal 158/158; GUI 413/413; controlador 1007/1007; fuzz 67.392/67.392;
  - perfils curts PASS, packaging focal 32/32 i `git diff --check` PASS;
  - QA portable complet PASS: manifest/signatura, relocacio, 114 Mach-O,
    dispatch, mission audit, R6 i smoke GUI offscreen;
  - executable SHA
    `bc257738b77101965f7415b10e7fbe39d0c6d336773657e7dba81d7fd0363911`;
  - manifest 49 fonts SHA
    `c032f27b85f197ce126163c97c45b97e69b4b80a1c28ebae88e002e4b80a4525`;
  - rollback 0.7.9 preservat a
    `gui/dist/Eclipse Command.app.previous-20260805T092958Z-57636`.
- pending_physical:
  - Pere ha de repetir `Check cameras now` amb la R6 carregada; aquest hotfix
    no ha contactat cap camera i no converteix QA offline en gate fisic.
- handoff:
  - zero processos propis Eclipse Command, controlador, QA o PyInstaller;
  - SERIAL_WRITES alliberat; arbre brut preservat sense reset/clean/stash.

## Main auditoria nocturna + convergencia + beta publica — RELEASED 2026-08-05

- status: RELEASED
- updated_utc: 2026-08-05T01:13:09Z
- released_utc: 2026-08-05T01:13:09Z
- task: Auditar el run 20260805T014632, depurar Check cameras/R6 i perdua
  de bateria, convergir A7RIIIA/6D, afegir control ISO global, executar quatre
  beta runs, completar configuracio GitHub, actualitzar guia universal i
  encarregar recerca EDSDK sense implementacio al task R6.
- phase: APP_0_7_9_PORTABLE_QA_PASS_PHYSICAL_REVALIDATION_PENDING
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-05T00:05:39Z
- authorization:
  - Pere autoritza campanya desatesa concreta; A7RIIIA i Canon 6D engegades;
    R6 III apagada i carregant;
  - autoritzats GUI fisica, PTP/gphoto2, captures i beta runs dins aquest pla;
    cap publicacio externa ni repositori public.
- invariants:
  - identitat USB -> PTP model+serie abans de cada write/trigger;
  - trigger ambigu consumit una sola vegada, zero replay/catch-up;
  - continuacions futures segures per canal; cap incidencia atura els altres;
  - cap contacte fisic R6 mentre continua apagada.
- audit_result:
  - run `20260805T014632_multi_camera_mission_run`: A7RIIIA 75/75 JPEG i
    72 totalitat; 6D 31 press/93 commits esperats; R6 amb bateria 1%, catorze
    accions concloses i la quinzena amb release sense ACK, zero replay;
  - Check R6 anterior va verificar model/serie/PTP i va fallar per contracte
    0.7.8 obsolet: esperava Timer 2 s mentre el cos era Continuous high;
  - cap cos detectat per gphoto2 durant aquest cicle final; R6 respectada OFF.
- implemented:
  - pont preflight `controller/eclipse_camera_setup.py`, zero captures; ISO
    100/200/400 global per totes les cameres PTP suportades, aillament per cos;
  - 6D cold-start AEB off -> 1/250 -> Continuous -> AEB +/-3 abans del
    controlador immutable; A7RIIIA contactes 1/4000..1/15, 72 totalitat i
    21 shutters al tier 98,8 s;
  - R6 future-only exact-identity recovery despres de bateria/USB: accio actual
    consumida, mai replay; programa 40 press AEB3, 120 CR3, 105 totalitat;
  - cronograma/audio START/STOP, Camera Settings sense telemetria fantasma i
    Sync UTC sense Internet coberts; guia universal actualitzada Mission First;
  - GitHub validat `isEnabled=false` fora del projecte i `true` dins; zero
    repositoris creats, commits, pushes o publicacio.
- qa_and_bundle:
  - GUI 408/408; controlador 1007/1007; fuzz 67.392/67.392; quatre recorreguts
    beta offline 4/4 i 16/16; `git diff --check` i manifest live PASS;
  - app 0.7.9 executable SHA
    `a50b97dcaf6cbc4a8f1533fcc0d7758b5b7614bf5994a045151dd79d9aa2d7a5`;
  - manifest 49 fonts SHA
    `816be130a2c720da22b49e1822846071b96ef4faab7003f42ff9819aee87f92e`;
  - QA portable PASS: signatura ad-hoc, relocacio, 114 Mach-O, dispatch,
    mission audit 3/3, R6 exacta i smoke GUI; informe
    `gui/QA_REPORT_0.7.9_2026-08-05.md`.
- pending_physical:
  - repetir Check + TEST RUN 0.7.9 A7RIIIA/6D; R6 amb bateria carregada;
  - RAW/SD i solar/optica per cos, Stage B 6D, H90/HDR/VSD90SS R6;
  - Developer ID, hardened runtime i notaritzacio abans de release publica.
- handoff:
  - zero processos propis Eclipse Command, controlador, QA, PyInstaller o
    app-server; locks historics preservats, no eliminats;
  - arbre brut preservat sense reset, checkout, clean ni stash;
  - SERIAL_WRITES alliberat per la propera tasca.

## R6 III auto-convergence + AEB3 — PAUSED/RELEASED 2026-08-04

- status: RELEASED
- updated_utc: 2026-08-04T23:41:53Z
- released_utc: 2026-08-04T23:41:53Z
- task: Fer que l'app porti automaticament cada cos al seu estat optim despres
  de detectar-lo i, si una correccio neta no adopta, dispari igual sota
  Mission First. Implementacio autoritzada ara nomes per a la R6 III; A7III,
  A7RIIIA i 6D han rebut la politica pero tenen ordre explicita de no
  implementar fins a nova autoritzacio de Pere als seus tasks.
- phase: OPERATOR_PAUSED_WIP_NOT_PROMOTED
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-04T22:19:44Z
- physical_demonstrated:
  - setters R6 exactes High ISO NR `High -> Off`, shutter `1/640 -> 1/320`,
    drive `Single -> Continuous high speed` i AEB `off -> +/- 3`, tots amb
    un unic write, readback exacte, cleanup net i estat fisic conegut;
  - G1 AEB3 PASS i delta CFexpress exclusiu +3; els tres CR3 reoberts donen
    `1/320, 1/2500, 1/40`, ordre 0,-,+, cos/serie exactes i contenidor integre;
  - G5 PASS 5/5, 15 commits i delta exclusiu +15;
  - G40 PASS 40/40, 120 commits, zero skips/warnings/recovery/replay i delta
    exclusiu `572A2603..2722` +120 sense canvis ni eliminacions.
- source_wip:
  - el perfil candidat declara 12 correccions startup-only, un intent i zero
    Busy retries: modes M, Continuous AF Off, RAW als dos slots, Memory card,
    CFexpress `00010001`, autoapagada 0, High ISO NR Off, 1/320, Continuous
    high i AEB +/-3; ISO continua operator-owned i mai s'escriu;
  - el materialitzador emet 40 grups AEB3, 120 RAW esperats i 105 durant
    totalitat, `3 + 35 + 2`, sense cap setter, drain, recovery, retry o replay
    despres d'armar;
  - un setter rebutjat netament continua com warning i no impedeix les 40
    pressions; physical_state_unknown despres d'un write atura nomes la R6;
  - la GUI activa `--apply-safe-config --mission-first` tant al preflight
    automatic posterior a deteccio com al RUN R6.
- offline_evidence:
  - perfil font `validate` PASS, zero contacte de camera;
  - materialitzacio temporal PASS: 40 actions, 120 expected, fases 3/35/2;
  - perfil materialitzat `validate` PASS i `dry-run` complete amb 120 expected;
  - cinc tests dirigits dels darrers errors PASS;
  - la suite GUI completa es va interrompre immediatament per ordre de Pere;
    havia mostrat un `F` sense arribar a imprimir quin test era. Per tant la
    font continua WIP i NO esta promocionada ni empaquetada.
- pending_resume_order:
  - reprendre la suite GUI per identificar/corregir el test restant;
  - executar controlador complet i fuzz, actualitzar proves/docs/version,
    construir una app nova i QA portable;
  - nomes despres fer un TEST RUN C1-C4 des del bundle nou.
- handoff:
  - app instal·lada 0.7.8 intacta; no s'ha fet build, registre ni obertura GUI;
  - la regressio offline s'ha tallat amb Ctrl-C i el proces ha sortit;
  - cap PTP, gphoto2, trigger, setter o camera obert despres del G40;
  - `git diff --check` PASS; arbre brut preservat sense reset/clean/stash.

## R6 III AEB3 physical gates — ACTIVE OPTIMIZATION 2026-08-04

- status: ACTIVE
- updated_utc: 2026-08-04T23:12:33Z
- released_utc: null
- task: Qualificar fisicament G1, G5 i G40 AEB3 per arribar a 105 RAW dins
  C2-C3 i, nomes si passen, promocionar el programa R6 sense perdre el
  fallback Mission First 40/35.
- phase: ACQUIRED_FOR_ACTIVE_PREMISSION_CONFIGURATION
- serial_writes: HELD
- owner: Codex R6 III AEB3 performance
- reacquired_after_timer_removed_utc: 2026-08-04T23:12:33Z
- reacquired_utc: 2026-08-04T23:09:43Z
- acquired_utc: 2026-08-04T22:19:44Z
- authorization: Pere ha tornat a encendre la R6 i ha autoritzat
  explicitament optimitzacio fisica desatesa.
- retry_authorization: Pere demana explicitament tornar-ho a provar despres
  d'arrencar l'app i executar un run.
- configuration_authorization: Pere confirma que el Timer 2 s s'ha retirat i
  ordena aplicar Mission First activament: modificar els parametres necessaris
  per portar la R6 a l'estat optim abans de missio.
- retry_result:
  - el run app `20260805T003208_multi_camera_mission_run` no va tocar la R6;
    la va excloure per `ptp_identity_unverified`;
  - preflight read-only `20260805T010956_lab_r6m3_readonly_preflight` PASS,
    amb drive `Timer 2 sec`, AEB off, 1/640, ISO 1600 i bateria 14%;
  - primer gate aturat abans del write: drive ja era `Continuous timer`, fora
    del preestat declarat `Timer 2 sec`;
  - segon gate aturat abans del write: drive ja era `Single`, fora del
    preestat declarat `Continuous timer`;
  - tots dos: `writes=0`, zero captures, identitat exacta, cleanup net i
    `physical_state_unknown=false`; no hi ha hagut Busy ni setter enviat.
- scope:
  - nomes Canon EOS R6 Mark III, serie PTP esperada
    `6d67c9923f453163358971b1b13d4c5f`, body serial `[SÈRIE]`;
  - ordre obligatori read-only -> snapshot -> G1 +3 -> snapshot/delta ->
    G5 +15 -> snapshot/delta -> G40 +120 -> snapshot/delta;
  - zero replay, recovery o retry de trigger ambigu i cap contacte amb les
    Sony o la Canon 6D;
  - app 0.7.8 conserva 40/35 fins a evidencia fisica completa.
- demonstrated:
  - preflight read-only `20260805T002145_lab_r6m3_readonly_preflight` PASS;
    identitat exacta, un sol intent PTP, cleanup net i estat fisic conegut;
  - firmware `3-1.1.0`, CFexpress `00010001`, RAW i target `Memory card`;
  - estat observat: M, Timer 2 s, AEB off, 1/640, ISO 1600 i bateria 35%;
  - el setter remot de drive continua contraindicat per evidencia previa
    `PTP Device Busy 0x2019` / `-110`; no s'ha repetit.
- waiting_operator:
  - configurar al cos M, Electronic shutter, Continuous high speed,
    AEB +/-3 de tres preses amb ordre 0,-,+, 1/320, ISO 100, Continuous AF
    Off, RAW a CFexpress i autoapagada desactivada; despres reconnectar USB.
- hard_stops:
  - identitat o propietari PTP divergent, trigger ambigu, delta CR3 diferent,
    estat fisic desconegut o ledger no garantible aturen nomes la R6;
  - Busy o timeout en un perfil lab fail-fast consumeix l'accio i atura el
    gate; no s'escala al gate seguent.

## R6 III >=105 RAW C2-C3 — CHECKPOINT RELEASED 2026-08-04

- status: RELEASED
- updated_utc: 2026-08-04T21:51:16Z
- released_utc: 2026-08-04T21:51:16Z
- task: Auditar el TEST RUN 0.7.7 i preparar una optimitzacio R6 III que
  materialitzi com a minim 105 RAW dins C2-C3 sense degradar el fallback
  Mission First fisicament demostrat de 35 RAW.
- phase: SOURCE_CANDIDATE_QA_PASS_WAITING_PHYSICAL_G1
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-04T21:38:43Z
- authorization: Pere ha demanat treball desates, analisi del run i un minim
  del triple de RAW durant totalitat; la bateria de la R6 es carrega.
- scope:
  - cap PTP, gphoto2, captura ni contacte amb cap camera mentre es carrega;
  - comparar un candidat Single dens de 105 RAW amb 35 grups AEB3 de 105 RAW;
  - preservar sense canvis el programa operatiu 40/35 fins a un gate fisic
    exclusiu amb identitat exacta i delta CFexpress;
  - zero setters, drains, recovery, retry o replay despres d'armar.
- demonstrated:
  - run 0.7.7 `20260804T232835_multi_camera_mission_run`: R6 exclosa abans
    de launch per `ptp_identity_unverified`, zero RAW R6 i la resta de canals
    van continuar;
  - gate Single propi `20/20` a inicis de 0,5 s amb delta CFexpress exclusiu
    `+20`, cleanup net i estat fisic conegut;
  - gate Timer 2 s propi `40/40` a 2,2 s amb delta exclusiu `+40`;
  - AEB R6 exposat com `+/- 3` i Drive inclou `Continuous high speed`, pero el
    G1 AEB3 i H90 encara no tenen evidencia fisica.
- hard_stops:
  - cap promocio a l'app ni substitucio del fallback 40/35 sense gate fisic;
  - identitat o propietat PTP divergent, trigger ambigu, delta CR3 incorrecte,
    replay potencial o estat fisic desconegut aturen nomes el canal R6.
- result:
  - decisio candidata: AEB3, 35 grups dins C2-C3, 105 RAW de totalitat i
    120 totals, ordre per grup 1/320, 1/2500, 1/40;
  - amb els contactes del run 0.7.7, separacio de grups 2,788235 s;
  - perfils G1/G5/G40 compilats offline per 3/15/120 RAW, sense setters,
    drains, recovery, retry ni replay;
  - previsualitzacio no armable afegida a `adaptive_profiles.py` amb
    `promotion_ready=false`; el selector operatiu continua a 40/35.
- qa:
  - GUI 405/405, controlador 1004/1004 i fuzz 67.392/67.392 PASS;
  - G1/G5/G40 `validate` PASS i G40 `dry-run` complete amb 120 imatges;
  - sintaxi Python, JSON i `git diff --check` PASS;
  - document d'autoritat provisional:
    `research/51_R6M3_TRIPLE_RAW_AEB3_2026-08-04.md`.
- pending:
  - reconnectar la R6 carregada i executar `Check cameras` per lligar la ruta
    USB actual a model i serie PTP exactes;
  - configurar manualment Electronic, Continuous high speed, AEB +/-3,
    1/320, RAW CFexpress i fer per ordre G1 +3, G5 +15 i G40 +120;
  - nomes despres integrar el candidat al materialitzador operatiu, construir
    una app nova i fer un TEST RUN C1-C4 complet.
- handoff:
  - zero processos propis de GUI, controlador, gphoto2, mission host o QA;
  - cap camera tocada i cap trigger o write executat durant aquest checkpoint;
  - app 0.7.7 i fallback fisic 40/35 no modificats ni reconstruits.

## R6 III duplicació de RAW — RELEASED 2026-08-04

- status: RELEASED
- updated_utc: 2026-08-04T21:21:15Z
- released_utc: 2026-08-04T21:21:15Z
- task: Integrar i empaquetar el programa Mission First R6 fix de 40 RAW
  després del gate físic `40/40`, sense presentar-lo com a HDR o ciència.
- phase: APP_0_7_7_PORTABLE_QA_PASS_PHYSICAL_APP_RUN_PENDING_RECONNECT
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-04T20:54:32Z
- result:
  - programa exacte de 40 Single RAW a 1/320, Timer 2 s, 35 totalitat i cinc
    parcials, zero setters post-arm, drain, recovery, retry o replay;
  - contracte mínim: totalitat 88 s, separació de press 2,47 s;
  - dispatch R6 dedicat i `run_root` lligat fail-closed a GUI i mission host;
  - app canònica 0.7.7 executable
    `a3d3e18ad2f335f7b1fb1aecb41f718530639c889c72325eb441755a83507cd3`;
  - manifest de 48 fonts
    `a29f90a76354e5d0e9df8a9df0217354c111e0f50053614b6d81ef29ba02f288`.
- evidence:
  - gate físic controlador 40/40, 40 commits, zero skips/warnings/recovery,
    `cleanup_ok=true`, `physical_state_unknown=false`;
  - delta CFexpress exclusiu +40 `572A2545..2584`, SHA
    `769cc420df80acdbeb1a2ce257add75c04607c36a6b97060c1407d2df8d074aa`;
  - GUI 402/402, controlador 997/997, fuzz 67.392/67.392, perfils curts,
    JSON, sintaxi Python i `git diff --check` PASS;
  - QA portable complet PASS, inclosos manifest, signatura, relocació,
    dispatch congelat i GUI offscreen.
- pending:
  - el TEST RUN físic des del bundle 0.7.7 no s'ha executat perquè IORegistry
    no mostrava la R6 i `gphoto2 --auto-detect` era buit;
  - H90, HDR, tracking/òptica VSD90SS, focus solar i ciència CR3 continuen
    warnings; el perfil segueix `CANDIDATE_NOT_PRODUCTION`.
- handoff:
  - zero processos propis de GUI, controlador, mission host, QA físic o
    `gphoto2` a l'alliberament;
  - no s'ha tocat l'A7RIIIA i no s'ha repetit cap write o trigger ambigu.

## A7RIIIA rendiment C2-C3 — RELEASED 2026-08-04

- status: RELEASED
- updated_utc: 2026-08-04T22:10:57Z
- task: Millorar físicament el rendiment de la Sony A7RIIIA amb el 300 mm a
  partir de la fotometria canònica i els límits propis de buffer/transport.
- phase: BUNDLE_0P7P8_PHYSICAL_75_OF_75_PASS
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-04T20:53:23Z
- reacquired_utc: 2026-08-04T21:37:24Z
- previous_release_utc: 2026-08-04T20:53:59Z
- prior_checkpoint_release_utc: 2026-08-04T21:38:10Z
- reacquired_after_r6_utc: 2026-08-04T21:51:47Z
- released_utc: 2026-08-04T22:10:57Z
- authorization: Pere ha connectat la càmera i ha demanat explícitament
  millorar-ne el rendiment en aquest task.
- scope:
  - només ILCE-7RM3A sèrie PTP
    `[SÈRIE]` i USB `[SÈRIE]`;
  - conservar 72 fotos C2-C3 i la ladder coronal fins a 3,2 s;
  - explorar una ladder de contacte ràpida sense superar el deute demostrat
    de 36 ni reutilitzar timings d'un altre cos;
  - cap replay de write o trigger ambigu i cap contacte amb la R6.
- safety:
  - relleu R6 rebut amb zero processos i cap propietari PTP;
  - els cinc fitxers WIP R6 del handoff queden fora d'abast;
  - aturada immediata per identitat divergent, Busy/-110/timeout ambigu o
    estat físic desconegut després d'un write.
- demonstrated:
  - IORegistry veu `ILCE-7RM3A`, USB `[SÈRIE]`, port físic `02100000`,
    High-Speed 480 Mbit/s;
  - `gphoto2 --auto-detect` no veu cap càmera i l'obertura explícita
    `usb:001,001 --summary` retorna `No camera found`: no hi ha PTP exposat;
  - zero processos propis i cap configuració ni trigger executat.
  - TEST RUN 0.7.7 `20260804T232835_multi_camera_mission_run`: identitat
    exacta, zero Busy/replay i estat físic final conegut, però el ledger de
    75 és només compromís esperat, no 75 fotos demostrades;
  - hi ha exactament 63 JPEG amb EXIF íntegre: cada un dels sis brackets
    ràpids dona 7/9 i perd sempre els dos darrers passos `-4 EV` i `+4 EV`
    (`1/500` i `1/2`); els dos brackets llargs sí que donen 9/9;
  - causa demostrada: `hold_s=1,6` qualificat amb darks és massa curt amb
    escena real; no és un coll d'ampolla de bytes ni dotze events aleatoris;
  - els 63 JPEG fan 345.628-367.461 bytes, gairebé igual que els foscos;
  - el gate històric amb `hold_s=3,0` va donar 27/27 en tres 9x1, de manera
    que 3,0 s és el fallback físic segur.
  - preflight read-only PASS a `20260804T233802_lab_a7r3a_readonly_preflight`:
    `usb:002,001`, model i sèrie PTP exactes, firmware 1.0, bateria 100%,
    cua 0, M/Manual/RAW+JPEG/Single/card+sdram i cleanup net;
  - ISO observat 400 és advisory de l'operador i no ha bloquejat res.
  - dos intents G1 previs van fallar abans de cap trigger: el primer per
    adopció tardana del mode 9x1 i el segon perquè el preflight encara exigia
    Single quan la càmera ja havia adoptat 9x1; tots dos amb cua 0, cleanup
    net i estat físic conegut;
  - G1 escena real PASS:
    `20260804T235514_lab_a7r3a_300gm_real_scene_9x1_hold2p5_g1_run`, un
    únic press de 2,5 s, 9/9 JPEG únics, ordre EXIF exacte
    `1/30..1/500..1/2`, cua 9 -> 0, zero warning/recovery/replay i restore
    net;
  - G4 buffer escena real PASS:
    `20260804T235631_lab_a7r3a_300gm_real_scene_9x1_hold2p5_g4_run`, quatre
    press de 2,5 s a cadència 2,9 s, 36/36 JPEG únics, quatre ordres EXIF
    exactes, deute 36, drenatge 20,254 s, zero skip/warning/recovery/replay,
    cleanup i restore verds; result SHA
    `2dfd4e86c76cd61a8a103de05f2c28abb59b0410a9a61ee1237e319bdebeecdc`
    i downloads SHA
    `7895d95243a3b189e188de2dcfe911455d20ec9f5154104820b2838eddd8fdee`;
  - materialitzador A7RIIIA corregit: fast 9x1 `hold_s=2,5` i
    `drain_ready_s=2,8`; exposicions, cadència 2,9, watchdog/retrigger 2,8,
    màxim deute 36, brackets llargs i 72 fotos C2-C3 no canvien;
  - regressió font completa PASS: GUI 405/405, controlador 1004/1004 i fuzz
    67.392/67.392.
  - bundle canònic 0.7.8 construït i QA portable PASS: arm64, signatura
    ad-hoc, 114 load paths autocontinguts, dispatch congelats i GUI offscreen;
    executable SHA
    `82958b396e8a13e8548a1e797f24ee0e99dbf297cb83026bc08d8517d9f8a88c`
    i manifest de 48 fonts SHA
    `98060fb7360a98f24c895470b70b2be8e09b5e411a7bddadd139b22a85830f1e`;
  - el bundle manté la R6 exactament a 40 Single RAW, 35 dins totalitat,
    Timer 2 s i AEB off; el preview AEB3 continua inert i no empaquetat;
  - TEST RUN del controlador congelat 0.7.8 PASS físic:
    `20260805T000451_candidate_a7r3a_300gm_short_checkpointed_1x5_3x9_run`,
    75/75 JPEG únics, 72/72 durant totalitat, sis fast 9x1 complets amb hold
    2,5 s, dos long 9x1 complets fins a 3,2 s, drenatges 27/36/9 de
    15,341/21,112/5,050 s, zero skips/timeline warnings/recovery/replay,
    cua final zero, restore/cleanup verds i estat físic conegut;
  - l'estat agregat `warning` és només `manual_checklist_incomplete`; ISO 400
    és advisory i les exposicions/EXIF quadren. Result SHA
    `c4d5a335d0977673ac4953d79af8466bbc7d25a27a2f612143f43e8662848127`
    i downloads SHA
    `5b4b5cf0a4c6e8cab88d8c31328e64ce96e35a6656ee36f1f8d28caca7f605d4`.
- pending:
  - delta SD/ARW exclusiu i gate solar/òptic continuen separats; aquest gate
    acredita timing/buffer/JPEG d'escena real, no RAW científic de missió.
- release_safety:
  - tots els gates han drenat a zero, el TEST RUN ha restaurat Single Shot,
    `1/1250`, RAW+JPEG Std i `card+sdram`, ha tancat gphoto2 i ha alliberat el
    lock de càmera;
  - checkpoint final: zero Eclipse Command, mission/worker host, controlador
    o gphoto2 propi; estat físic conegut, R6 i Canon no tocades;
  - SERIAL_WRITES alliberat explícitament. Cap commit ni push.

## R6 III duplicació de RAW — CHECKPOINT RELEASED 2026-08-04

- status: RELEASED
- updated_utc: 2026-08-04T20:52:44Z
- task: Auditar el TEST RUN R6 III acabat per Pere, mesurar el coll
  d'ampolla real i preparar/qualificar un programa Mission First d'almenys
  40 Single RAW sense replay ni transferir evidència d'un altre cos.
- phase: PHYSICAL_40_RAW_GATE_PASS_SOURCE_REFACTOR_INCOMPLETE
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-04T20:32:04Z
- released_utc: 2026-08-04T20:52:44Z
- handoff_to: task A7RIIIA performance, per prioritat física autoritzada per Pere
- scope:
  - autorització desatesa de Pere per millorar el rendiment de la R6 III;
  - identitat exacta, un únic propietari PTP i delta CFexpress abans de
    qualsevol promoció;
  - les parcials filtrades continuen a 1/320, ISO advisory i Electronic;
  - cap replay d'un write o trigger ambigu i cap canvi a les altres càmeres.
- demonstrated:
  - el run fet per Pere va confirmar el coll d'ampolla: primer RAW comès i el
    setter dinàmic següent va retornar `Device Busy/-110`; no es va repetir;
  - identitat PTP exacta, CFexpress `00010001`, RAW card-only i Timer 2 s;
  - G1 exacte `+1 CR3`, prova intermèdia `+5 CR3` i prova principal fixa
    `40/40` en 85,879351 s, sense skips, recovery, replay, warnings de
    cronologia ni `physical_state_unknown`;
  - delta CFexpress exclusiu `+40 CR3`, de `572A2545.CR3` a `572A2584.CR3`,
    sense fitxers retirats ni metadades canviades;
  - `gphoto2`, controladors de captura i Eclipse Command absents en el
    moment del handoff.
- evidence:
  - run: `controller/runs/20260804T224312_lab_r6m3_timer2_single_40x2p2s_cfexpress_20260804_run`;
  - snapshot posterior:
    `controller/runs/20260804T224458_lab_r6m3_readonly_r6m3-media-snapshot`;
  - delta: `controller/evidence/r6m3_cfexpress_deltas/20260804T224213_to_20260804T224458_exact_plus40.json`;
  - SHA-256 delta:
    `769cc420df80acdbeb1a2ce257add75c04607c36a6b97060c1407d2df8d074aa`;
  - SHA-256 resultat:
    `141ec9b1cd14dd74d9f28954448bbbb776202a092007186f0c487e9ccc49f9bc`;
  - SHA-256 manifest:
    `4b4d95d0fdb83107b33e12e838eec1da37163b385ab0b26a675d769031cb1c8b`.
- source_wip_do_not_promote:
  - el canvi de 20 HDR amb setters a 40 captures fixes a 1/320 i Timer 2 s és
    incomplet i encara no ha passat regressió, build ni TEST RUN des de l'app;
  - `controller/eclipse_capture_r6m3.py` conserva referències antigues al
    validador exacte i no s'ha de considerar llest;
  - fitxers WIP que no s'han de tocar des d'un altre task:
    `gui/eclipse_command/adaptive_profiles.py`,
    `controller/eclipse_capture_r6m3.py`,
    `controller/profiles/candidate_r6m3_vsd90ss_cfexpress_cardonly_v1.json`,
    `controller/profiles/lab_r6m3_drive_single_cfexpress_preflight.json` i
    `controller/tests/test_r6m3_cfexpress_g1_profiles.py`.
- pending:
  - readquirir `SERIAL_WRITES` després del relleu A7RIIIA;
  - completar el validador exacte, GUI, tests i documentació del programa de
    40 captures fixes;
  - executar regressions completes, construir el bundle i fer un TEST RUN
    físic de l'app amb delta CFexpress abans de qualsevol promoció.
- safety:
  - cap procés propi viu, cap propietari PTP i cap trigger ambigu pendent;
  - cap contacte ni canvi a l'A7RIIIA;
  - els 40 CR3 acrediten transport i materialització a targeta, no integritat
    del payload CR3 ni qualificació científica/solar.

## Exposicions solars canòniques 10° — SOURCE READY 2026-08-04

- status: RELEASED
- updated_utc: 2026-08-04T19:59:28Z
- task: Tancar la fotometria empírica A7RIIIA/R6 III, fixar la referència
  única a Sol 10°, 700 m i visibilitat 7/10, i aplicar el delta mínim als
  perfils sense crear un sistema multiperfil.
- phase: SOURCE_QA_COMPLETE_BUILD_WAITING_FOR_APP_CLOSE
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-04T19:30:23Z
- released_utc: 2026-08-04T19:59:28Z
- handoff_to: Pere / Main quan Eclipse Command estigui tancat
- scope:
  - només font, tests, documentació, bundle i missatges als tasks dedicats;
  - zero càmera, PTP, gphoto2, captures, LaunchServices o GUI física;
  - preservar tots els canvis preexistents i no fer reset, clean, checkout o
    stash;
  - mantenir 20 RAW i 18 exposicions de totalitat a la R6; cap multiperfil per
    ubicació i cap transferència de valors entre cossos sense evidència pròpia.
- completed:
  - autoritat única documentada a
    `research/50_EXPOSICIO_SOLAR_FILTRADA_CANONICA_10G_2026-08-04.md`;
  - R6 III + VSD90SS + OD 5,0: parcials filtrades pre/post a ISO 100,
    Electronic i 1/320; el worker estricte i el perfil font comparteixen el
    mateix contracte, sense blocker per deute científic;
  - A7RIIIA + 300/2,8 + OD 5,1: parcials Single filtrades pre-C1 i post-C3 a
    ISO 100, Silent/Electronic i 1/400 en el fixed 9x1 de 90-100 s; després de
    C3 drena, torna a Single i substitueix el bracket documental 9x1 per una
    sola captura útil;
  - ladders sense filtre C2-C3 intactes, sense multiperfil ni compensació
    automàtica d'airmass;
  - contrast Claude corregit: confirma els valors al cas 10°/700 m i retira
    la seva lectura errònia de 15 minuts;
  - relleu enviat als tasks dedicats R6 i A7RIIIA, amb prohibició d'editar
    durant aquest SERIAL_WRITES;
  - focal 48/48, GUI 400/400, controlador 997/997, fuzz 67.392/67.392, JSON i
    `git diff --check` PASS.
- pending:
  - bundle i QA portable acumulats no executats: `Eclipse Command.app`
    continua oberta amb PID 18260; no s'ha forçat el tancament ni s'ha tocat
    la GUI física;
  - quan l'app estigui tancada, readquirir SERIAL_WRITES, construir, executar
    QA portable i publicar els hashes nous.
- safety:
  - zero càmera, PTP, gphoto2, captures, LaunchServices o GUI física;
  - worktree brut preservat sense reset, clean, checkout ni stash.

## Main Camera Settings sense estat fantasma — SOURCE READY 2026-08-04

- status: RELEASED
- updated_utc: 2026-08-04T19:09:15Z
- task: Evitar que Camera Settings mostri un informe recordat o d'una camera
  anterior quan no hi ha cap cos actual connectat i coincident.
- phase: SOURCE_QA_COMPLETE_BUILD_WAITING_FOR_APP_CLOSE
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-04T19:00:13Z
- released_utc: 2026-08-04T19:09:15Z
- handoff_to: Pere / Main quan Eclipse Command estigui tancat
- root_cause:
  - l'arrencada carregava camera/last_settings_report abans que discovery
    acredites cap camera viva; el perfil coincident feia visible estat antic.
- completed:
  - cap informe recordat es restaura visualment a l'arrencada o canvi de
    perfil;
  - cada informe viu queda vinculat al port actual de la camera de detall;
  - desconnexio, canvi de cos o canvi de ruta buiden files, port i segell;
  - estat buit explicit: No connected camera o Waiting for fresh camera check;
  - regressio nova de cache inicial i desconnexio: 2/2;
  - discovery 61/61, GUI 400/400, controlador 997/997, fuzz 67.392/67.392,
    perfils curts i git diff --check PASS.
- pending:
  - build/QA portable acumulats amb la maquetacio Sync UTC: app encara oberta
    amb PID 18260; build exit 3 abans de substituir cap bundle;
  - tancar l'app i readquirir SERIAL_WRITES per empaquetar, validar i publicar
    hashes/docs.
- safety:
  - cap camera, PTP, gphoto2, captura, LaunchServices ni GUI fisica;
  - cap bundle substituit, cap build lock/staging i zero processos propis;
  - worktree brut preservat sense reset, clean, checkout ni stash.

## Main Maquetacio dialog Sync UTC — SOURCE READY 2026-08-04

- status: RELEASED
- updated_utc: 2026-08-04T18:59:11Z
- task: Millorar la jerarquia, llegibilitat i botons del dialeg de confirmacio
  de Sync UTC, mantenint Cancel com a decisio segura per defecte.
- phase: SOURCE_QA_COMPLETE_BUILD_WAITING_FOR_APP_CLOSE
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-04T18:50:32Z
- released_utc: 2026-08-04T18:59:11Z
- handoff_to: Pere / Main quan Eclipse Command estigui tancat
- completed:
  - dialeg natiu amb titular separat, icona informativa i tres passos
    escanejables;
  - llindar fresh kernel bound <=50 ms i avís de possible ajust del rellotge
    en bloc propi;
  - botons explicits Sync UTC / Cancel, amb Cancel com a default i Escape;
  - prova estructural nova; focal UTC 50/50, GUI 398/398, controlador 997/997,
    fuzz 67.392/67.392, perfils curts i git diff --check PASS;
  - render offscreen validat a 405 x 211 px.
- pending:
  - build i QA portable no executats: Eclipse Command continua obert amb PID
    18260; l'intent ha sortit amb exit 3 abans de substituir el bundle;
  - tancar l'app i readquirir SERIAL_WRITES per acabar bundle, hashes i docs.
- safety:
  - cap camera, PTP, gphoto2, captura, LaunchServices ni GUI fisica;
  - cap bundle substituit i cap build lock o staging temporal pendent;
  - zero processos propis pendents; worktree brut preservat sense reset,
    clean, checkout ni stash.

## Main Auto-sync UTC al footer — COMPLETE 2026-08-04

- status: RELEASED
- updated_utc: 2026-08-04T18:47:39Z
- task: Afegir una accio Auto-sync UTC al costat de Test audio amb
  autenticacio nativa, verificacio kernel i bloqueig durant operacions.
- phase: SOURCE_BUNDLE_QA_COMPLETE
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-04T18:33:39Z
- released_utc: 2026-08-04T18:47:39Z
- handoff_to: Pere / proper task Eclipse autoritzat
- completed:
  - boto Sync UTC al footer, al costat de Test audio, amb estat live
    Sync UTC / UTC bounded / Checking NTP / Authorizing / Verifying;
  - sonda read-only `/usr/bin/sntp -t 3 time.apple.com` abans de qualsevol
    auth; timeout d'app 10 s;
  - sense Internet, DNS o NTP: NO INTERNET / NTP UNREACHABLE, zero auth,
    zero clock write i Start mission torna disponible;
  - amb NTP: autenticacio nativa macOS, hora automatica i exit nomes amb
    `ntp_gettime` BOUNDED <=50 ms; Error:-99 no domina el kernel;
  - auth cancelada o helper absent mai es presenta com exit;
  - control i qualsevol launch bloquejats mentre sync es actiu; cap sync
    durant missio, START pendent o worker de camera;
  - focal UTC 49/49, discovery 59/59, GUI 397/397, controlador 997/997,
    fuzz 67.392/67.392, perfils curts i git diff --check PASS;
  - QA portable PASS: arm64, signatura ad hoc, 114 Mach-O autocontinguts,
    relocalitzacio, manifest i GUI offscreen;
  - bundle actiu gui/dist/Eclipse Command.app v0.7.6;
  - executable SHA256
    757df18180f291e514539ce01a147a17abbb692540e6d302cbe8c23dde297d44;
  - manifest 48 fonts SHA256
    8dfca14b6c49c23638da0f1cc6e9b2904c9ec04aa7d12c0865bbf17cdbf3c7f8;
  - rollback immediat
    gui/dist/Eclipse Command.app.previous-20260804T184548Z-15357.
- safety:
  - cap ajust UTC executat en QA: QProcess, xarxa i auth simulats;
  - zero cameres, PTP, gphoto2, captures o GUI fisica en aquesta ronda;
  - GUI pid i build lock absents; zero Eclipse Command, worker, controlador,
    gphoto2, sntp, osascript o QA propi pendent;
  - worktree brut i canvis aliens preservats sense reset, clean, checkout ni
    stash.

## Main STOP terminal de cronograma — COMPLETE 2026-08-04

- status: RELEASED
- updated_utc: 2026-08-04T18:15:17Z
- task: Preservar l'estat terminal STOPPED i suprimir CONTACTS ALREADY
  IN PROGRESS/ELAPSED despres d'un Stop safely acceptat.
- phase: SOURCE_BUNDLE_QA_COMPLETE
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-04T18:06:04Z
- released_utc: 2026-08-04T18:15:17Z
- handoff_to: Pere / proper task Eclipse autoritzat
- completed:
  - Stop safely conserva el pla congelat i el marcador STOPPED quan el
    worker acaba; CONTACTS ALREADY IN PROGRESS/ELAPSED queda ocult;
  - editar contactes, TEST RUN o activar una missio nova obre deliberadament
    un cicle de pla nou;
  - focal cronograma 23/23, GUI 390/390, controlador 997/997, fuzz
    67.392/67.392, perfils curts i git diff --check PASS;
  - QA portable PASS: arm64, signatura ad hoc, 114 Mach-O autocontinguts,
    relocalitzacio, manifest i GUI offscreen;
  - bundle actiu gui/dist/Eclipse Command.app v0.7.6;
  - executable SHA256
    20bfdfb89afcfd8ccc422b48f32880d2c4a02166619b3cbbbffb7b5823562187;
  - manifest 48 fonts SHA256
    b984b3b74703db9f8b963ef2745015c88bb18597e7cd24ab246d44654589f746;
  - rollback immediat
    gui/dist/Eclipse Command.app.previous-20260804T181343Z-9848.
- safety:
  - zero cameres, PTP, gphoto2, captures o GUI fisica en aquesta ronda;
  - GUI pid i portable-build lock absents; taula de processos sense cap
    Eclipse Command, worker, controlador, gphoto2 o QA propi pendent;
  - worktree brut i canvis aliens preservats sense reset, clean, checkout ni
    stash.

## Main Mission First cronograma/audio/HDR R6 — COMPLETE 2026-08-04

- status: RELEASED
- updated_utc: 2026-08-04T17:59:08Z
- task: Corregir cronograma/audio i substituir la R6 fixa per un programa HDR
  de totalitat sense vulnerar Mission First.
- phase: SOURCE_BUNDLE_QA_COMPLETE_PHYSICAL_REQUALIFICATION_PENDING
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-04T17:54:40Z
- released_utc: 2026-08-04T17:59:08Z
- handoff_to: Pere / proper task fisic R6 autoritzat
- completed:
  - cronograma i avisos automatics esperen Start mission; Stop safely congela
    el cronograma i atura la veu; Test audio continua explicit;
  - R6 exacta: 20 setters + 20 Single RAW, amb 18 shutters de totalitat
    1/8000..2s, una parcial a C1 i una a C4-8s;
  - setter fallit netament conserva captura amb darrera obturacio coneguda i
    accions futures; write/trigger ambigu no es reprodueix;
  - literal Mission First `costi el que costi` integrat amb limits de canal;
  - GUI 389/389, controlador 997/997, fuzz 67.392/67.392, focal 213/213,
    perfils curts, JSON i git diff --check PASS;
  - QA portable PASS: signatura ad hoc, arm64, 114 Mach-O autocontinguts,
    relocalitzacio, pins de 48 fonts, workers congelats i GUI offscreen;
  - bundle actiu gui/dist/Eclipse Command.app v0.7.6;
  - executable SHA256
    b33290a913811b03bba9e4498acae8addc0e1afae27827f529794bc4f0a84df9;
  - manifest 48 fonts SHA256
    a1b28fd2383a775e866e0e801267152d31b86d364a198e47e9e450ba1f582fdb;
  - rollback immediat
    gui/dist/Eclipse Command.app.previous-20260804T175514Z-4521.
- pending_physical_debt:
  - H90, timing real dels setters, tracking/VSD90SS, focus/filtre, buffer i
    ciencia CR3; cap QA offline els declara qualificats.
- safety:
  - zero cameres, PTP, gphoto2, captures o GUI fisica en aquesta ronda;
  - GUI pid i portable-build lock absents; zero processos propis pendents;
  - worktree brut i canvis pont/GitHub en HOLD preservats sense reset, clean,
    checkout ni stash.

## Main repren build Mission First R6 2026-08-04

- status: ACTIVE
- updated_utc: 2026-08-04T17:54:40Z
- task: Activar i validar el bundle 0.7.6 amb cronograma/audio i HDR R6.
- phase: REACQUIRED_VERIFYING_GUI_CLOSED
- serial_writes: ACTIVE
- owner: Main task 019fc4aa-8dac-7831-84af-8ce9cb6a13e3
- acquired_utc: 2026-08-04T17:54:40Z
- released_utc: null
- handoff_from: task 019fcdd8-edd9-76b3-ab41-1e5dca418864
- owned_paths:
  - codi, tests i documentacio del checkpoint Mission First R6 anterior
  - gui/dist/Eclipse Command.app
  - .coordination/CODEX_STATUS.md
- safety:
  - no forcar ni obrir GUI; build nomes si el PID d'app ja no es viu;
  - zero cameres, PTP, gphoto2 o captures;
  - preservar el worktree brut i els canvis de pont/GitHub en HOLD;
  - alliberar amb hashes, QA portable i zero processos propis.

## Connector GitHub només per a Eclipse 2026 — HOLD / RELEASED 2026-08-04

- status: HOLD
- updated_utc: 2026-08-04T17:54:14Z
- task: Desactivar el connector GitHub per defecte i habilitar-lo només dins
  del projecte canònic Eclipse 2026.
- phase: CONFIG_APPLIED_VALIDATION_PENDING_HOLD_BY_PERE
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-04T17:52:44Z
- released_utc: 2026-08-04T17:54:14Z
- handoff_from:
  - Pont task 019fcd79-f5d1-7503-966f-4f549424103c
  - Main task 019fc4aa-8dac-7831-84af-8ce9cb6a13e3
- handoff_to: Main task 019fc4aa-8dac-7831-84af-8ce9cb6a13e3
- owned_paths:
  - /Users/USUARI/.codex/config.toml
  - /Users/USUARI/Downloads/Eclipse 2026/.codex/config.toml
  - .coordination/CODEX_STATUS.md
- safety:
  - zero cameres, PTP, gphoto2, captures, LaunchServices o GUI fisica;
  - preservar íntegrament el worktree brut i no tocar codi ni bundle;
  - retornar RELEASED immediatament a Main després de validar la precedencia.
- checkpoint:
  - aplicat deny global a
    /Users/USUARI/.codex/config.toml amb l'id complet del connector;
  - creada excepcio local enable=true a
    /Users/USUARI/Downloads/Eclipse 2026/.codex/config.toml;
  - autenticacio GitHub existent comprovada abans del canvi;
  - validacio global/projecte/altre projecte INCOMPLETA: els dos thread/start
    de prova van fallar per un literal sandbox incorrecte abans de crear-se;
  - zero threads temporals creats i servidor app-server propi aturat;
  - reprendre nomes amb nova autoritzacio de Pere i readquirint SERIAL_WRITES.

## Pont global Mac/PC — HOLD / RELEASED 2026-08-04

- status: HOLD
- updated_utc: 2026-08-04T17:52:16Z
- task: Fer el pont invocable des de tots els projectes Codex i Claude a Mac
  i PC, reinstal·lar-lo al Mac i crear backups verificats a Dropbox.
- phase: CANDIDATE_VALIDATED_NOT_INSTALLED_HOLD_BY_PERE
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-04T17:42:47Z
- released_utc: 2026-08-04T17:52:16Z
- handoff_from: Main task 019fc4aa-8dac-7831-84af-8ce9cb6a13e3
- handoff_to:
  - Main task 019fc4aa-8dac-7831-84af-8ce9cb6a13e3
  - GitHub connector task 019fcdd8-edd9-76b3-ab41-1e5dca418864
- owned_paths:
  - /Users/USUARI/.codex/skills/pont/
  - /Users/USUARI/.claude/skills/pont/
  - /Users/USUARI/.pont/
  - /Users/USUARI/.local/bin/pont*
  - /Users/USUARI/Downloads/Pacto de Socios Claude/eines/pont*
  - /Users/USUARI/Downloads/Pacto de Socios Claude/eines/instal_pont.sh
  - /Users/USUARI/Downloads/Pacto de Socios Claude/eines/instal_skills.sh
  - /Users/USUARI/Downloads/Pacto de Socios Claude/eines/instal_skills.ps1
  - /Users/USUARI/Downloads/Pacto de Socios Claude/eines/pont-skills/
  - /Users/USUARI/Library/CloudStorage/Dropbox/Pere Guerra/Pacto de Socios Juny 2026/IA Benidorm/Skills/
  - .coordination/CODEX_STATUS.md
- safety:
  - no tocar captura, GUI, PTP, cameres, gphoto2 ni LaunchServices;
  - preservar tots els canvis bruts aliens sense reset, clean, checkout o stash;
  - retornar RELEASED a Main tan bon punt acabin validacio i backups.
- checkpoint:
  - candidat portable preservat nomes a
    /private/tmp/pont-portable-v7.tHDbA2;
  - suite pont amb binaris falsos PASS i quick_validate PASS a Codex i Claude;
  - zero canvis aplicats a skills globals, repositori canonic o Dropbox en
    aquesta fase;
  - reprendre nomes quan Pere ho autoritzi, readquirint SERIAL_WRITES;
  - no hi ha processos propis pendents.

## Mission First cronograma/audio/HDR R6 — checkpoint temporal 2026-08-04

- status: RELEASED
- updated_utc: 2026-08-04T17:42:05Z
- task: Cronograma i avisos automatics nomes des de Start mission; Stop safely
  els congela; programa R6 de 20 Single amb 18 exposicions HDR de totalitat.
- phase: SOURCE_AND_OFFLINE_QA_COMPLETE_WAITING_FOR_GUI_CLOSE_AND_BUNDLE
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-04T17:19:45Z
- released_utc: 2026-08-04T17:42:05Z
- handoff_to: task 019fcd79-f5d1-7503-966f-4f549424103c
- completed:
  - cronograma WAITING FOR START i zero avis automatic abans de Start;
  - Stop safely congela cronograma i atura veu;
  - R6 materialitza 20 setters + 20 captures, 18 HDR C2-C3 1/8000..2s;
  - Mission First R6 continua amb l'ultima obturacio coneguda despres d'un
    setter fallit netament; cap replay ambigu;
  - literal `costi el que costi` integrat a AGENTS.md i CLAUDE.md amb limits;
  - GUI 389/389, controlador 997/997, fuzz 67.392/67.392, perfils curts i
    git diff --check PASS.
- pending:
  - Eclipse Command PID 12091 continua obert; el build oficial ha fallat
    tancat abans d'activar cap bundle;
  - quan Pere tanqui l'app, reacquirir SERIAL_WRITES, construir, executar QA
    portable, actualitzar hashes/documentacio i alliberar definitivament.
- safety:
  - zero processos propis pendents i cap bundle nou activat;
  - zero cameres, PTP, gphoto2, captures o GUI fisica;
  - worktree brut preservat sense reset, clean, checkout ni stash;
  - el pont pot completar nomes la seva configuracio global i ha de tornar
    RELEASED abans de reprendre aquest build.

## Mission First — cronograma, audio i HDR R6 2026-08-04

- status: ACTIVE
- updated_utc: 2026-08-04T17:19:45Z
- task: Fer que cronograma i avisos automatics nomes avancin des de Start
  mission, que Stop safely els aturi, i substituir el fallback R6 fix per una
  seqüencia HDR centrada en C2-C3 basada en el pla optic VSD90SS.
- phase: IMPLEMENTATION
- serial_writes: ACTIVE
- owner: Main task 019fc4aa-8dac-7831-84af-8ce9cb6a13e3
- acquired_utc: 2026-08-04T17:19:45Z
- released_utc: null
- handoff_from: task 019fcd79-f5d1-7503-966f-4f549424103c
- owned_paths:
  - gui/eclipse_command/widgets.py
  - gui/eclipse_command/main_window.py
  - gui/eclipse_command/adaptive_profiles.py
  - gui/tests/
  - controller/profiles/candidate_r6m3_vsd90ss_cfexpress_cardonly_v1.json
  - controller/eclipse_capture_r6m3.py
  - controller/tests/
  - documentacio i QA del bundle 0.7.6
  - .coordination/CODEX_STATUS.md
- safety:
  - feina exclusivament offline; zero cameres, PTP, gphoto2, captures,
    LaunchServices o GUI fisica;
  - preservar tot el worktree brut, sense reset, clean, checkout ni stash;
  - mantenir identitat exacta, cap replay i independencia entre canals.

## Pont global — índexs locals Claude/Codex 2026-08-04

- status: RELEASED
- updated_utc: 2026-08-04T17:19:21Z
- task: Ampliar la descoberta validada del pont als índexs locals reals de
  projectes de Claude i Codex, sense cerques difuses ni worktrees històrics.
- phase: PONT_LOCAL_REGISTRY_DISCOVERY_COMPLETE_RELEASED_TO_MAIN
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-04T17:15:35Z
- released_utc: 2026-08-04T17:19:21Z
- handoff_to: Main task 019fc4aa-8dac-7831-84af-8ce9cb6a13e3
- owned_paths:
  - /Users/USUARI/.codex/skills/pont/
  - /Users/USUARI/.claude/skills/pont/
  - /Users/USUARI/.pont/
  - /private/tmp/pont-global-v6.cfQ50p/
  - .coordination/CODEX_STATUS.md
- safety:
  - índexs `~/.claude/projects` i `~/.codex/state_5.sqlite` només en lectura;
  - zero models reals, càmeres, PTP, GUI o fitxers de captura.
- handoff:
  - instal·lació global v6 completada abans del handoff;
  - gate final contra `/Users/USUARI/.pont/pont`: PASS;
  - suite confirma neteja de workers detached, locks i temporals; zero processos propis pendents;
  - Main pot adquirir `SERIAL_WRITES` per cronograma/àudio/HDR R6;
  - no es reprendrà cap mutació global fins a un nou handoff `RELEASED` de Main.

## Reparació global de la skill pont — represa 2026-08-04

- status: RELEASED
- updated_utc: 2026-08-04T17:13:22Z
- task: Reparar `pont` perquè sigui invocable globalment, descobreixi contextos
  locals relacionats i apliqui els models/esforços fixats per Pere en les dues
  direccions Codex↔Claude.
- phase: PONT_GLOBAL_REPAIR_COMPLETE
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-04T17:02:54Z
- released_utc: 2026-08-04T17:13:22Z
- handoff_from: Main task 019fc4aa-8dac-7831-84af-8ce9cb6a13e3
- owned_paths:
  - /Users/USUARI/.codex/skills/pont/
  - /Users/USUARI/.claude/skills/pont/
  - /Users/USUARI/.pont/
  - /Users/USUARI/.local/bin/pont
  - /private/tmp/pont-global-v6.cfQ50p/
  - .coordination/CODEX_STATUS.md
- safety:
  - zero càmeres, PTP, `gphoto2`, captures, LaunchServices o GUI física;
  - proves només amb binaris falsos: cap consulta ni despesa d'IA real;
  - no tocar cap fitxer de captura ni cap canvi preexistent del worktree.
- result:
  - Codex skill instal·lada a `/Users/USUARI/.codex/skills/pont/`;
  - Claude skill instal·lada a `/Users/USUARI/.claude/skills/pont/`;
  - motor global publicat a `/Users/USUARI/.local/bin/pont`;
  - SHA-256 comú del motor: `2ec8b05a63bfaf9691d2f15dc807a2c38fac19d981e87074fed43a88d08543da`;
  - context Eclipse resolt com `shared-workspace` en les dues direccions;
  - rutes RHODE explícites preservades i resoltes en les dues direccions;
  - suites staging Codex, staging Claude i executable instal·lat: PASS;
  - `quick_validate.py`: PASS en les dues skills;
  - zero consultes reals a Claude/Codex durant la validació i zero processos propis pendents.

## Correcció Mission First: consumeix l'acció ambigua i continua — 2026-08-04

- status: RELEASED
- updated_utc: 2026-08-04T17:02:16Z
- task: Aplicar la política Mission First en què una captura amb resultat ambigu
  queda consumida i en quarantena, sense replay, però el mateix canal conserva
  les accions futures mentre identitat, propietat i estat operatiu siguin segurs.
- phase: MISSION_FIRST_AMBIGUOUS_ACTION_CORRECTION_COMPLETE
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-04T16:43:06Z
- released_utc: 2026-08-04T17:02:16Z
- handoff_to: task 019fcd79-f5d1-7503-966f-4f549424103c per reprendre `pont`
- owned_paths:
  - controller/eclipse_capture.py
  - controller/eclipse_capture_canon_v2.py
  - controller/eclipse_capture_r6m3.py
  - controller/tests/
  - gui/eclipse_command/main_window.py
  - gui/tests/
  - gui/tools/qa_macos_portable.py
  - AGENTS.md
  - CLAUDE.md
  - README.md
  - controller/README.md
  - gui/README.md
  - gui/QA_REPORTS.md
  - gui/QA_REPORT_0.7.6_2026-08-04.md
  - .coordination/CODEX_STATUS.md
- safety:
  - treball exclusivament offline; zero càmeres, PTP, `gphoto2`, captures,
    LaunchServices o GUI física;
  - conservar íntegrament el worktree brut i els canvis previs de Pere;
  - cap replay de l'acció ambigua, ni immediat ni tardà.
- handoff:
  - una captura operativa amb resultat ambigu consumeix només aquella acció,
    queda `degraded` i no es repeteix; les accions futures del mateix cos es
    conserven mentre la sessió verificada continuï operativa;
  - l'host no passa `--recover-disconnects` a cap run. El controlador Sony
    compartit conserva el hash físic immutable
    `b9c4b28233350b225edaa4bbb09f3d6fb5d52fc7fc7c10ca5bf592e575f4421d`;
    no s'ha repinat cap evidència històrica;
  - Canon 6D i R6 només admeten `--mission-first` en la materialització C1-C4
    operativa exacta; font, perfil lab o materialització divergent fallen
    abans del worker. Recovery, retry i setters post-primer-RAW continuen
    prohibits;
  - proves: focal 102/102, GUI 387/387, controlador 996/996, fuzz
    67.392/67.392, perfils curts `--check` i `git diff --check` verds;
  - bundle 0.7.6 reconstruït i QA portable repetida verda: signatura ad hoc,
    relocalització, 114 Mach-O, dispatch congelat i GUI offscreen;
  - executable SHA-256
    `ca71af19c8f225d1e7b74af74d582f4f7c52162fbf5423022874f65bacae3de7`;
  - manifest de 48 fonts SHA-256
    `c05f395261d27ddf8bf71acdbe8996b9d90c12b08aadc3ab81985df3c07a6ed3`;
  - Canon v2 font SHA-256
    `592b3b7d234ab2237b417014551a6aa32db74c29df7880fa6aeb4533f80a64b5`;
  - R6 v6 font SHA-256
    `a90ea6e1c9fb49913fb6db0fabf22444b5d0fde0e074f237cc61cee845c39eeb`;
  - rollback immediat preservat a
    `gui/dist/Eclipse Command.app.previous-20260804T165941Z-70071`;
  - zero processos `Eclipse Command`, worker, `mission_host` o `gphoto2` al
    handoff; no s'ha obert ni registrat l'app ni s'ha contactat cap càmera;
  - H90, VSD90SS, AEB/HDR R6, focus, filtre, buffer superior a 20 i ciència
    CR3 continuen com a deute visible; cap QA offline els qualifica.

## Reparació global de la skill pont — 2026-08-04

- status: RELEASED
- updated_utc: 2026-08-04T16:42:42Z
- task: Reparar `pont` perquè sigui invocable globalment, descobreixi contextos
  locals relacionats i apliqui els models/esforços fixats per Pere en les dues
  direccions Codex↔Claude.
- phase: PONT_GLOBAL_REPAIR_CHECKPOINT_RELEASED_TO_MAIN
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-04T16:32:27Z
- released_utc: 2026-08-04T16:42:42Z
- handoff_to: Main task 019fc4aa-8dac-7831-84af-8ce9cb6a13e3
- handoff:
  - checkpoint coherent: canvis del pont preservats només a `/private/tmp/pont-global-v6.cfQ50p`;
  - cap canvi global instal·lat i cap codi de captura tocat;
  - zero processos propis llançats o pendents; la lectura global de `ps` ha estat denegada pel sandbox;
  - Main queda autoritzat a adquirir `SERIAL_WRITES` per la correcció Mission First;
  - la reparació del pont continuarà en lectura/proves i readquirirà només després d'un handoff `RELEASED`.
- owned_paths:
  - /Users/USUARI/.codex/skills/pont/
  - /Users/USUARI/.claude/skills/pont/
  - /Users/USUARI/.pont/pont
  - /Users/USUARI/.local/bin/pont
  - .coordination/CODEX_STATUS.md
- safety:
  - zero càmeres, PTP, `gphoto2`, captures, LaunchServices o GUI física;
  - proves només amb binaris falsos: cap consulta ni despesa d'IA real;
  - no tocar ni netejar els canvis preexistents del worktree Eclipse.

- status: RELEASED
- updated_utc: 2026-08-04T16:09:07Z
- task: Restaurar Mission First: fer llançable la R6 amb el fallback segur
  de 20 Single RAW i deixar H90 com a warning, no com a bloqueig.
- phase: R6_MISSION_FIRST_UNBLOCK_COMPLETE
- serial_writes: RELEASED
- owner: null
- acquired_utc: 2026-08-04T15:47:27Z
- released_utc: 2026-08-04T16:09:07Z
- owned_paths:
  - gui/eclipse_command/main_window.py
  - gui/eclipse_command/adaptive_profiles.py
  - gui/eclipse_command/themes.py
  - controller/profiles/candidate_r6m3_vsd90ss_cfexpress_cardonly_v1.json
  - controller/tests/test_r6m3_operational_profile.py
  - gui/tests/test_adaptive_profiles.py
  - gui/tests/test_domain.py
  - gui/tests/test_main_window_discovery.py
  - gui/tests/test_visual_contract.py
  - gui/tools/qa_macos_portable.py
  - AGENTS.md
  - CLAUDE.md
  - README.md
  - gui/README.md
  - controller/README.md
  - gui/QA_REPORTS.md
  - gui/QA_REPORT_0.7.6_2026-08-04.md
  - gui/tests/test_runtime_manifest.py
  - .coordination/CODEX_STATUS.md
- handoff:
  - COMPLET: amb identitat PTP exacta i C1-C4 vàlids, la R6 queda `READY`,
    compta a `Start mission` i ja no deixa la missió a `0 cameras`;
  - el perfil font continua `CANDIDATE_NOT_PRODUCTION`,
    `timing_qualified=false` i `materialization_required=true`, però no porta
    `mission_capture_blocked_reason`; només la materialització exacta pot crear
    una ordre RUN;
  - fallback R6: exactament 20 Single RAW a 1/640, repartits C1-C4, C4-8 s,
    separació estàtica mínima de 620 ms i zero setters, drains, recovery o
    replay; la font directa, sintètica, divergent o amb geometria inviable
    falla abans del worker;
  - H90, AEB/HDR, VSD90SS, focus, filtre, buffer >20 i ciència CR3 continuen
    pendents i visibles a fila/banner/Activity com a warnings, no hard stop;
  - R6 sola en Mass Storage no crea una missió buida; R6 KO + Sony READY
    llança només la Sony i audita la R6 exclosa;
  - QA: focal Mission First 135/135, descoberta 59/59, GUI 387/387,
    controlador 994/994, fuzz 67.392/67.392, perfils `--check`, packaging
    23/23 i `git diff --check` verds;
  - bundle canònic `gui/dist/Eclipse Command.app`, versió 0.7.6;
  - executable SHA-256 `398c5ccd5eb4239ff47bd6dd65d36eeb62adfaaf719962a725a00add25ad9439`;
  - manifest de 48 fonts SHA-256 `b210701bcbaebbb56b828ec48ac5affc648a587378d160894240faa1732d104b`;
  - worker R6 font viu i congelat SHA-256
    `68ce66a866319940785704563661c30acd0c1e51af9105b889f9a581465cbc9a`;
  - `Run SOLAR PILOT` queda ocult i `Start mission` és l’única acció de
    captura visible; no s’ha refactoritzat el pilot històric;
  - `Buy me a beer :)` i `Stop safely` tenen hover clar amb contorn reforçat;
  - QA portable repetida verda: manifest, signatura ad hoc, relocalització,
    114 Mach-O, controladors congelats, host, dispatch R6 acotat i GUI
    offscreen; app no oberta;
  - rollback immediat:
    `gui/dist/Eclipse Command.app.previous-20260804T160355Z-60441`;
  - `gui/dist` conserva 11 rollbacks històrics; no se n’ha eliminat cap perquè
    era fora del delta i una neteja destructiva no estava autoritzada;
  - zero PTP, `gphoto2`, setter, trigger o captura en aquesta ronda;
  - zero processos propis de GUI/worker/controlador/PTP al release.
- safety:
  - autorització fresca de Pere: fer avui els ajustos pertinents al programa
    i preparar Eclipse Command per repetir l'experiment filtrat a uns 10 i 5
    graus abans de la posta;
  - aquesta fase comença offline: zero càmera, PTP, `gphoto2`, captures o GUI
    física fins que el build estigui validat i Pere doni el vistiplau de run;
  - els pilots són fotosfera amb els filtres declarats, no promoció ni
    qualificació de perles, diamant, corona, cara lunar o totalitat;
  - conservar l'arbre brut de Pere i limitar els canvis al delta mínim;
  - autorització fresca de Pere: fer tots els canvis necessaris per arrencar
    l'app i obtenir un run d'eclipsi R6 III reeixit; cobreix aquesta campanya
    escalonada de codi, build, LaunchServices, GUI i contacte físic, però no
    elimina els hard stops ni permet repetir cap trigger ambigu;
  - reconciliació inicial `2026-08-04T10:31:21Z`: zero processos de captura,
    Claude `RELEASED` i cap Canon enumerada per macOS; per tant, zero PTP fins
    que USB + model + sèrie es puguin resoldre de nou;
  - l'autorització anterior `segueix amb la implementació` no es va consumir:
    macOS no ha enumerat cap Canon per USB en cap comprovació i no s'ha obert
    PTP ni executat `gphoto2`. Queda tancada amb aquest handoff i no es pot
    reutilitzar; queda supersedida per l'autorització explícita actual;
  - l'autorització fresca `segueix` ja s'ha consumit amb exactament una sessió
    preflight read-only v4 `013353`, sense `--apply-safe-config`, setters,
    triggers, captures, drains, downloads, recovery o replay;
  - la prohibició anterior de recontacte PTP queda supersedida per
    l'autorització explícita actual; la bateria observada al 5% continua sent
    advisory i no un gate mission-first;
  - les autoritzacions desateses anteriors són història consumida; només
    l'autorització explícita actual habilita aquesta nova campanya;
  - campanya escalonada: una sola incògnita física per gate, manifest CFexpress
    abans/després i zero replay; no començar AEB/buffer dens sense haver
    tancat cardinalitat i retrigger anteriors;
  - Sigma 35/1.4 és proxy fotogràfic autoritzat per càrrega/escriptura; no
    transfereix qualificació solar, focus o òptica al VSD90SS;
  - ISO i bateria són advisory operator-owned; no modificar ISO i no bloquejar
    per bateria baixa si encara hi ha una cronologia conservadora segura;
  - no format, delete, EDSDK, GUI física ni altres càmeres; primer Busy,
    timeout, `-110`, identitat/propietari PTP ambigu, trigger ambigu, delta
    CR3 incorrecte o `physical_state_unknown`: hard stop del canal, zero replay.
- latest_r6m3_h2_and_drive_hard_stop_2026_08_04:
  - USB/PTP re-resolt: `Canon Digital Camera` a 10 Gb/s, model
    `Canon EOS R6 Mark III`, sèrie PTP
    `6d67c9923f453163358971b1b13d4c5f`, cos `[SÈRIE]`, firmware
    `3-1.1.0`; IORegistry continua sense sèrie USB;
  - setter únic `20260804T124429` PASS `1/1250 -> 1/640`, readback exacte,
    bateria 81% advisory, zero trigger/captura/retry/drain/recovery/replay;
  - H2 `20260804T124524` PASS: 20/20 Single RAW, inicis cada 500 ms, accions
    `52,950..56,003 ms`, zero skips/warnings/recovery, cleanup/restore/release
    final verds i estat físic conegut;
  - inventaris `124439 -> 124548` acrediten exactament `98 -> 118`, només
    `572A2386..2405.CR3`; vint descàrregues manifest-bound i vint inspeccions
    ISO-BMFF/EXIF PASS, payloads únics, RAW 6960x4640, 1/640, Single, AEB off,
    ISO 100 advisory i obturador electrònic;
  - receipt H2
    `controller/evidence/r6m3_cardonly_certificates/20260804T124524_h2_single_20x500ms_exact_plus20.json`,
    SHA-256 `8d18586b...e25f`: certifica transport Single/card-only, una exposició;
    no promou HDR, VSD90SS, ciència solar ni producció;
  - setter drive `20260804T124807` HARD STOP: una sola ordre
    `Single -> Continuous high speed` rebutjada amb `0x2019 PTP Device Busy`
    i `-110`; preestat Single, Canon declara property not set i
    `clean_busy_was_not_set=true`, però no hi ha readback post-error; captures
    0, cleanup net i `physical_state_unknown=false`;
  - no repetir el setter drive, no executar AEB i no tornar a obrir PTP en
    aquesta sessió física. Següent contacte només després de power-cycle o
    canvi manual extern confirmat, amb identitat completa re-resolta;
  - treball actual exclusivament offline: materialitzador fallback Single
    limitat per H2, QA del bundle, regressions i build. `SERIAL_WRITES` segueix
    `HELD`; cap altre canal ha de tocar R6/PTP/GUI física.
- latest_r6m3_offline_h2_certifier_2026_08_04:
  - la Canon no ha aparegut a `system_profiler SPUSBDataType`; zero PTP,
    `gphoto2`, setter, trigger, captura, drain, download, EDSDK, GUI física o
    LaunchServices durant aquesta ronda;
  - nou G1 VSD90SS v2 `29e16f03...79eb`: focus Manual, manifest fresc,
    minimum 1 MB i zero ISO/inventari caducats, setters, drains, recovery o
    replay; l'històric queda preservat;
  - nou H2 candidat `0262e8d9...b8e7`: 20 Single RAW a inicis de 500 ms,
    hold 50 ms, bounds de 0,35 s, zero setters/drain/retry/replay i hashes H1
    exactes. Declara explícitament que el worker v1 no qualifica el v5;
  - nou certifier offline `certify_r6m3_cardonly_gate.py`, SHA-256
    `49bd3315...1e87`: reconcilia result, manifest, snapshot, delta i un CR3
    reobert per commit; rebutja cleanup/release/reconnect/recovery/estat
    ambigu, deltes i metadades divergents, inspeccions absents/duplicades i
    payloads repetits. No promou missió ni ciència RAW/solar;
  - H1 falla tancat al certifier per 2 inspeccions sobre 10 commits. Conserva
    PASS parcial de transport/delta, no certificació completa;
  - el blocker operatiu ara descriu H1/V2 sense afirmar `only one CF RAW`;
    AEB/HDR i el compilador C1-C4 continuen deliberadament absents fins H/S;
  - la GUI falla tancat si un perfil R6 futur es desbloqueja mentre encara
    exigeix una confirmació manual que el checklist genèric no pot certificar;
    `--mission-first` i reconnect continuen prohibits al worker R6;
  - packaging coherent amb certifier + `immutable_json`: 31/31. El manifest
    font candidat tindria 46 inputs, SHA-256 `a3063e8f...ea7f`, però no s'ha
    construït ni publicat; l'app activa segueix stale amb 44 fonts;
  - regressió: controlador 983/983, GUI 368/368, R6 focal 142/142, dedicat
    35/35, fuzz 67.392/67.392, perfils curts, 15 JSON R6, `py_compile` i
    `git diff --check` verds, tot offline;
  - handoff `2026-08-04T09:38:01Z`: zero processos propis. Els sis `.lock`
    trobats són artefactes Sony de 25-29 de juliol amb PIDs inexistents i es
    conserven sense esborrar-los. `SERIAL_WRITES` alliberat;
  - ordre següent: amb càmera enumerada i autorització fresca, resoldre
    identitat exacta i executar una sola adopció preflight v5
    `1/1250 -> 1/640`; després G1 VSD v2 si el VSD és muntat o H2 si encara hi
    ha el Sigma. Cap AEB abans de cardinalitat/ordre manual real.
- latest_r6m3_v5_setter_ready_2026_08_04:
  - preflight read-only `20260804T013353` PASS: identitat exacta, firmware
    `3-1.1.0`, Manual, Single, AEB off, RAW SD/CF, ISO 100 advisory, shutter
    fresc `1/1250`, `Memory card`, CFexpress `00010001`, 7081 captures
    disponibles i bateria 5% advisory;
  - 25 lectures, zero setters/triggers/releases/captures, cleanup net,
    `capture_may_have_started=false` i `physical_state_unknown=false`;
    resultat `2a2789f6...09cd`, events `e4d86ae0...b4ce1`, manifest
    `3fa68dd2...f2ef`, worker v4 immutable `43379d7f...4530` i perfil
    `6d190a91...451a`;
  - `production_eligible=true` al resultat v4 és un defecte de metadata, no una
    promoció: manifest `CANDIDATE_NOT_PRODUCTION`, timing no qualificat, mode
    preflight i zero accions. La font v5 ho corregeix per a resultats futurs;
  - worker v5 `c43a2387...b439`: publica l'intent abans d'escriure i qualsevol
    commit dubtós o fallada de settle/readback marca `physical_state_unknown`;
    cap restore, drain, reconnect, recovery ni segona ordre en aquest estat;
  - perfil següent
    `lab_r6m3_shutter_1_640_from_1_1250_cfexpress_preflight.json`, SHA-256
    `34ecfd2b...6ef6`: preflight-only, únic setter possible `1/1250 -> 1/640`,
    un intent, zero Busy retries, captures, drains, recovery o replay;
  - dry-run final `20260804T015752` PASS amb zero ordres de càmera/captures;
    resultat `1a713759...052a`, events `3ba80bdb...895c`, manifest
    `f0757ebf...610e` i snapshot de perfil `34ecfd2b...6ef6`;
  - auditoria independent: cap P1/P2 restant; gap P3 no bloquejant, sense test
    integrat de tot el `finally`, però guards i `restore()` coberts;
  - regressió final: controlador `976/976`, R6 focalitzat `135/135` (dedicat
    `35/35`), GUI `367/367`, packaging/manifests `31/31` i fuzz
    `67.392/67.392`; perfils curts, 46 JSON, `py_compile` i
    `git diff --check` verds, tot offline;
  - handoff `2026-08-04T00:03:36Z`: zero processos propis gphoto2, worker,
    snapshot, tests, fuzz o app; cap lock obert i `SERIAL_WRITES` alliberat;
  - ordre viu: esperar autorització fresca i càrrega suficient per executar
    una sola adopció preflight. La R6 encara no és capture-ready.
- latest_r6m3_vsd90ss_baseline_readonly_fix_2026_08_04:
  - decisió operativa: `1/640` és el baseline immediat de
    transport/laboratori i candidat d'ancoratge C2-C3 per al VSD90SS. H1 ja
    l'ha demostrat amb 10 RAW CFexpress a 500 ms. No és baseline solar ni HDR
    final i no transfereix cap timing, bracket o buffer d'un altre cos;
  - snapshot únic `20260804T011252` PASS: model R6 III, sèrie PTP
    `6d67c992...c5f`, cos `[SÈRIE]`, firmware `3-1.1.0`, CFexpress
    `00010001`, `Memory card`, RAW complet a SD/CF amb 23 opcions, 98 CR3 fins
    `572A2385`, bateria 16% advisory i zero mutació/captura/download;
  - inventari byte-idèntic a l'anterior, SHA-256 `8d32db17...031`; resultat
    `67dd612f...112`, events `0fa1a23c...396` i transcript
    `dde3761d...243`. Aquest snapshot no llegeix shutter: `1/125` només és
    l'últim valor històric, no el preestat actual;
  - preflight read-only `20260804T011350` hard stop abans del preflight
    funcional: el perfil v3 heretava el sentinel Sony inexistent
    `/main/capturesettings/capturemode`. Model i sèrie PTP havien respost;
    zero setters/triggers/captures, `capture_may_have_started=false`,
    `physical_state_unknown=false`, cleanup net i cap replay;
  - resultat del hard stop `ea4e3440...f4e`, events `6def6f51...9af`,
    transcript `89576257...f3`, manifest `6427271e...289` i perfil immutable
    `b6dadeb07...53e`. És un defecte determinista de perfil, no de càmera, i
    no requereix power-cycle;
  - correcció offline: worker R6 v4 SHA-256 `43379d7f...530`, perfil read-only
    `6d190a91...51a` i test dedicat `c1e9fa20...ccc`. Els sentinels explícits
    són `autoexposuremode`, `drivemode`, `imageformatcf` i `shutterspeed`; els
    paths Sony `capturemode`/`dro` queden exclosos;
  - regressió offline: R6 `122/122`, controlador `963/963`, GUI `367/367` i
    fuzz `67.392/67.392`; zero càmera/PTP/gphoto2. Bundle 0.7.4 continua stale
    amb worker v2 i no s'ha reconstruït ni registrat;
  - ordre viu: esperar autorització fresca -> exactament un preflight
    read-only v4 -> si és verd, crear perfil setter des del shutter fresc
    exacte cap a `1/640` si cal. Un intent, Busy retries 0, zero trigger,
    drain, recovery o replay; si ja és `1/640`, zero write. Després AEB,
    obturadors, H buffer, VSD90SS+MF i S. R6 encara no és capture-ready.
  - handoff `2026-08-03T23:22:27Z`: zero processos propis gphoto2, Python,
    worker, snapshot, tests, fuzz o app; cap lock obert; `SERIAL_WRITES`
    alliberat. El següent contacte físic requereix autorització fresca.
- superseded_r6m3_v2_raw_closed_2026_08_04:
  - checkpoint històric superat per
    `latest_r6m3_vsd90ss_baseline_readonly_fix_2026_08_04`; no conté cap ordre
    executable ni autoritza contacte PTP;
  - snapshot únic recuperat `20260804T001823` PASS: model/sèries/firmware
    exactes, CFexpress `00010001`, 98 CR3 fins `572A2385`, bateria 20% advisory
    i zero mutació/captura/download; resultat SHA-256 `6174a2d1...614c` i
    inventari `8d32db17...031`;
  - delta write-once `97 -> 98` PASS: només
    `/store_00010001/DCIM/100EOSR6/572A2385.CR3`, zero removals, topologia
    estable i 97 entrades preservades; SHA-256 `c79cc82e...d5ddf`;
  - descàrrega manifest-bound `20260804T002140` PASS: un únic `get`, inventaris
    abans/després byte-idèntics, zero trigger/mutació i CR3 de 38.626.516 bytes,
    SHA-256 `e0f14d22...6c255`; resultat `34b78c0a...cf13` i inspecció
    `4447989d...95bae`;
  - inspector: cos `[SÈRIE]`, RAW 6960x4640, 1/1250, Single, AEB off i
    Electronic. ISO12800, Sigma 35/1.4 i One-shot AF són lab/advisory;
    `scientific_raw_verified=false` continua pendent. V2 és PASS V/RAW i mai
    es repeteix;
  - el snapshot també exposa `imageformatsd=L` i `imageformatcf=L`, amb una
    única opció `L` a cada path. Això no invalida el CR3 V2 existent, però
    bloqueja qualsevol captura nova i prohibeix forçar RAW absent;
  - restore transport-only `20260804T002833` hard stop prewrite: shutter actual
    `1/125`, fora de l'únic preestat autoritzat `1/1250` per target `1/640`;
    `writes=0`, captures 0, cleanup net i `physical_state_unknown=false`.
    Resultat SHA-256 `25bed659...c049`; no ampliar la precondició ni repetir;
  - font viva R6 v3 SHA-256 `9ba28e6c...6e487`; gate CR3 viu
    `68c587e2...4f15`; perfil restore `68dff753...8aa3`. La descàrrega física
    queda lligada a la revisió intermèdia del gate `093a2857...0e3b`, no al
    hash viu posterior;
  - regressió offline actual: R6 `122/122` (dedicat `23/23`), controlador
    `963/963`, GUI `367/367`, fuzz `67.392/67.392`; zero càmera/PTP/gphoto2 en
    aquestes proves. Packaging/manifests `31/31`, perfils curts, JSON,
    `py_compile` i `git diff --check` verds;
  - bundle 0.7.4 anterior: executable `dd7c9513...2ad3`, manifest de 44 fonts
    `15aad3ce...9ed7`, worker R6 v2 `f29f53d5...127a`. És stale respecte de la
    font v3/gate CR3 viu i no s'ha reconstruït perquè el builder registra
    LaunchServices, fora d'aquest canal;
  - ordre històric anul·lat: RAW ja s'ha recuperat i el snapshot posterior ja
    s'ha executat. No repetir V2, download, restore ni aquest ordre;
  - handoff `2026-08-03T22:39:24Z`: zero processos propis gphoto2, worker,
    eines R6, tests, fuzz o app; cap lock R6 viu; `SERIAL_WRITES` alliberat.
- superseded_r6m3_a2_v2_before_raw_closure_2026_08_03:
  - checkpoint històric superat per
    `latest_r6m3_vsd90ss_baseline_readonly_fix_2026_08_04`; no conté
    instruccions executables;
  - snapshot fresc `20260803T232242` PASS: mateixa identitat PTP/cos/firmware,
    CFexpress `00010001`, RAW card-only i exactament els mateixos 97 CR3 fins
    `572A2384`; inventari SHA-256 `cfd8b264...25b`, bateria 9% advisory;
  - A2 `20260803T232318` PASS: preestat 1/640, exactament un setter, ACK
    43,184 ms, readback 1/1250, zero captures/errors, cleanup net i estat
    conegut; resultat SHA-256 `12191e5e...e373`;
  - pre-V2 `20260803T232343` confirma encara 97 CR3. V2 `20260803T232406`
    PASS només de trigger/ledger: un press/release, expected images 1, zero
    setter de paràmetres, Busy, timeout, recovery, skip o replay, release final
    confirmat i estat conegut; resultat SHA-256 `f86916ff...2681`;
  - post-snapshot únic `20260803T232427` hard stop: model visible a autodetect,
    `PTP Timeout` al primer `get-config cameramodel`, sessió tainted, cleanup
    incomplet i cap inventari. Zero write/trigger/download/delete/format en el
    snapshot; resultat SHA-256 `95661b12...f0b9`;
  - no s'ha repetit V2 ni executat restore. Últim shutter demostrat 1/1250;
    estat actual, delta CF i CR3 desconeguts. Següent ordre després de canvi
    físic extern: snapshot únic -> delta exacte esperat 97->98 -> inspecció del
    nou CR3 -> restore únic des de preestat 1/1250. Perfil missió encara
    bloquejat; cap contacte físic addicional en aquest handoff.
  - el log macOS demostra owner churn entre gphoto2, `Image Capture` i
    `ptpcamerad`; sosté `572A2385.CR3` i catàleg 98, però no substitueix
    l'inventari exclusiu, delta o integritat. Evidència:
    `controller/evidence/r6m3_ptp_owner_churn_20260803T232408Z.md`;
  - worker viu v2 SHA-256 `f29f53d5...127a`: corregeix AEB natiu amb shutter
    fix de menú i suma totes les exposicions físiques. H1/A2/V2 continuen
    lligats al v1 immutable `6f438b1d...dff3`; no s'han reetiquetat;
  - snapshot viu SHA-256 `11aef47e...c1b7` i CR3 gate
    `76c802ec...6161f`: guard únic discovery->primer ACK i hard fail abans de
    PTP si `Image Capture` és obert, sense controlar la GUI;
  - regressió offline final: R6 `119/119` (dedicat `22/22`), controlador
    `960/960`, GUI `367/367`, fuzz `67.392/67.392`, perfils curts i QA portable
    verds. Bundle 0.7.4: executable `dd7c9513...2ad3`, manifest de 44 fonts
    `15aad3ce...9ed7`; no registrat ni obert físicament;
  - handoff final `2026-08-03T21:50:55Z`: zero processos propis gphoto2,
    worker, snapshot, CR3 gate, tests, fuzz o app; `SERIAL_WRITES` alliberat.
    Els blocs històrics han quedat marcats `superseded` i no autoritzen replay.
    El hard stop físic continua vigent fins que Pere asseguri `Image Capture`
    tancat, faci power-cycle/reconnect i ho confirmi. Després: un únic
    snapshot; mai repetir V2.
- superseded_checkpoint_r6m3_h1_before_completed_a2_v2_2026_08_03:
  - bloc històric superat pel bloc
    `latest_r6m3_vsd90ss_baseline_readonly_fix_2026_08_04`; no conté
    instruccions executables i mai autoritza repetir A2 o V2;
  - H1 PASS físic `20260803T225705`: 10/10 Single RAW CFexpress, hold 50 ms,
    inicis 500 ms, 10 press/release ACK, zero Busy, timeout, replay, recovery,
    skip o estat desconegut; resultat SHA-256
    `160386e7a7b61642a8e3e66e318710de7622c835abfad74508e1bbcdc2498d80`;
  - manifest CF exacte `87 -> 97`, només `572A2375..2384`, zero removals;
    evidència write-once SHA-256
    `502ead65be86910b03224b18b2f81a9b06fe07ecaf34bb7ed1b5fd7c203bfe0a`;
  - extrems manifest-bound `2375/2384` descarregats una sola vegada: RAW
    6960x4640, 1/640, Single, Electronic, payloads SHA-256
    `f84cb69b...55f2e` i `09ee8d26...a7a8f4a`; Sigma 35/1.4, One-shot AF i
    ISO12800 són lab/advisory, no VSD90SS;
  - A2 `20260803T230505` ha fet hard stop abans de sessió: zero coincidències
    USB/PTP, zero gphoto shell, write, setter o trigger. Resultat SHA-256
    `d4394c8eef70dd9cfadf21fe390bace5a9b1357a9cfcb0e8b7d96b0ee9fdd103`;
    no contactar de nou fins a canvi físic extern;
  - preparats offline: forward shutter `1/640 -> 1/1250` SHA
    `edf9c853...56d6`, V2 un RAW 1/1250 SHA `873e96ea...c80b` i restore
    `1/1250 -> 1/640` SHA `d1ca65cc...38dd`; cadascun aïlla una sola mutació
    o trigger, zero retry. El perfil de missió continua bloquejat fins H/S.
  - regressió final offline: R6 `108/108`, controlador `949/949`, GUI
    `367/367`, fuzz `67.392/67.392`, JSON, py_compile,
    `build_short_profiles.py --check` i `git diff --check` verds;
  - handoff històric coherent: zero processos propis. L'ordre que llavors era
    pendent (`snapshot -> A2 -> V2 -> restore`) ja es va consumir fins al V2;
    queda anul·lat i no s'ha d'executar. L'únic ordre viu és el del bloc
    `latest_r6m3_vsd90ss_baseline_readonly_fix_2026_08_04`; no autoritza cap
    replay.
- superseded_progress_r6m3_gphoto_integration_2026_08_03:
  - cronologia històrica superada; els valors vius són exclusivament els del
    bloc `latest_r6m3_vsd90ss_baseline_readonly_fix_2026_08_04` i no s'ha
    d'executar cap ordre d'aquest
    bloc;
  - Pere confirma ara `M` i `1/640` fisics i autoritza continuar
    desatesament. Aquesta confirmacio habilita snapshot/preflight/H1/post
    exactes, sempre amb zero replay i stop al primer error;
  - Pere confirma `fet` despres del hard stop; es registra com a canvi fisic
    extern/power-cycle confirmat. L'autoritzacio s'ha consumit amb exactament
    un snapshot fresc; no autoritza replay ni saltar directament a H1;
  - snapshot `20260803T224748` PASS: identitat exacta, arbre recuperat,
    CFexpress `00010001`, RAW, card-only, bateria 4% advisory, zero mutacio i
    inventari complet de 87 CR3 `572A2288..2374`. Els 13 noms `2362..2374`
    son preexistents a H1 i no s'atribueixen al controlador. Inventari SHA-256
    `f05e439e159a0e650d936b13dc73b0f63d69212d2f42f40a2043306b40d44fa2`;
  - preflight H1 unica `20260803T224829`: identitat, `Single`, AEB `off`,
    RAW CF, card-only i storage correctes, pero hard fail abans de mutacio per
    dial `AV` i shutter `auto` en lloc de `Manual`/`1/640`. Zero
    `set-config`, trigger o captura; cleanup net,
    `capture_may_have_started=false` i `physical_state_unknown=false`.
    Resultat SHA-256
    `b7698aeb39882ce971edf7a5481c70ac9d0e236326e66795d06dbf2c1bfe8a9c`;
  - estat històric de la sessió `224829`: H1 no s'hi va executar i no se'n va
    repetir cap trigger. Posteriorment s'ha completat sota el checkpoint H1 i
    el bloc viu A2/V2 anteriors;
  - primer snapshot de la campanya `20260803T203543`: identitat USB/PTP/cos i
    firmware exactes, bateria 1% advisory; la sisena lectura ha rebut
    `/main not found in configuration tree` a `availableshots`. Hard stop abans
    de `storage-info`: zero targeta, setter, trigger, download, delete o format;
    sessio no tainted, cleanup i lock nets, zero processos residuals. Resultat
    SHA-256 `cd7ce5afdea1089966074fba808da32b1e84732a442e0debecc61b4be18cf9b5`;
  - cap reintent fisic fins que Pere confirmi un canvi extern real posterior:
    bateria canviada/recarregada o cos apagat i tornat a encendre. El blocker
    no es l'1%: es la desaparicio real de l'arbre de configuracio;
  - `Canon Digital Camera` sense serie USB mai acredita identitat. IORegistry,
    port i un unic model gphoto nomes creen una fila `candidate`, sense
    `body_id` inventat; la GUI queda `CONNECTING` fins a `PTP_READY` exacte al
    mateix port. Canvi, desaparicio o ambiguitat invaliden la prova i el run
    queda exclos amb `ptp_identity_unverified`;
  - a la font viva, perfil de missio R6 visible/verificable
    `candidate_r6m3_vsd90ss_cfexpress_cardonly_v1`, encara bloquejat abans de
    captura fins H/S, SHA-256
    `620287b45d3980c859cd313bd2cc01b74e6c3c2cb2f35397f7b1270f67e2c380`.
    El bundle 0.7.4 ja l'incorpora, executable SHA-256
    `3438ca8f28e34e1e4a5681eb823b60c68ab7d4c54b7cc10eff9888b57f1d8315`
    i manifest de 44 fonts SHA-256
    `04c3181b0e886b2f46bc36e9904c374b80a5bfcf2aad61856d767b482b764d22`;
  - primer gate preparat i validat inicialment en dry-run, i posteriorment
    executat físicament segons el bloc latest:
    `lab_r6m3_dense_single_10x500ms_cfexpress`, deu Single, hold 50 ms, inicis
    cada 500 ms, cap setter/drain/recovery/replay; PASS exclusiu `+10 CR3`,
    SHA-256 `627ba7623648e6195ef0e86334e77333fb25af14d2b4454fb1821df69644f9ec`;
    run dry-run `20260803T222508` complet 10/10, zero ordres de camera,
    manifest SHA-256
    `59c2f602716ba0ddb4f3e838e7c4e9d61b2531a569dcc08b2c6989fa3409eb75`
    i resultat SHA-256
    `472eb4bc759d547e6ffcfe40f4332f9e60c73125d95b6c5a1a336da452b30c3e`;
  - reconciliador CFexpress offline nou: exigeix identitat exacta, store
    `00010001`, topologia estable, zero desaparicions i delta CR3 cardinal
    exacte. G1 PASS `73 -> 74`, només `572A2361.CR3`; evidència write-once
    SHA-256 `5387cf0eee356508f1e2f3c75adbc639b2b3a288f929d1602605dce43280a6a9`.
    No afirma bytes antics immutables ni integritat nova sense descàrrega;
  - en aquest checkpoint històric la R6 es despatxava exclusivament a
    `controller/eclipse_capture_r6m3.py`, versio
    `0.4.3-r6m3-gphoto-cardonly-v1`, SHA-256
    `6f438b1d44540b23fd00cdfb6711114dd51ac43d485a713a676f88251e2ddff3`.
    Shared i Canon v2 continuen byte-exactes a
    `b9c4b28233350b225edaa4bbb09f3d6fb5d52fc7fc7c10ca5bf592e575f4421d`
    i `720d7fd2266fe38d4edeb7f9b820e62f722de40be4128d78700597f8e7bee6e0`;
  - worker R6 fail-fast per contracte: rebutja `--mission-first` i recovery
    abans d'artefactes/PTP; autodetect, PTP open, setters, restore i -110 tenen
    un sol intent, Busy zero retries i unknown-state no es travessa.
    `mission_host` manté les altres cameres. Bateria semantica es advisory;
    transport/identitat/trigger/config-tree continuen hard stop del canal;
  - `fixed_preflight_shutter` prohibeix setters d'obturacio, `set_exposure` i
    `held_bracket`, pero zero writes totals continua sent contracte del perfil.
    L'entrypoint exigeix CR3 card-only, sense payload local ni raw_integrity, i
    acredita `inspect_cr3.py`;
  - comparator viu amb la mateixa geometria del TEST RUN: A7III 44 imatges
    C2-C3 i 60 totals. Objectiu R6 provisional: >=84 C2-C3, >=100 totals i
    >=5 exposicions distintes, pero cap recompte/cadencia CF queda promogut
    abans dels gates fisics propis;
  - validacio offline del patch final: R6 focalitzat 108/108, dedicat 18/18,
    controlador 949/949, GUI 367/367 i fuzz 67.392/67.392. Build final, H1
    dry-run, `build_short_profiles.py --check`, manifest i QA frozen verds:
    signatura ad-hoc valida, arm64, macOS minim 26.0, 114 load paths
    autocontinguts, perfils sense contacte, cadena worker-controlador, missio
    3/3, blocker sintetic i GUI offscreen;
  - handoff històric: zero processos propis i `SERIAL_WRITES` alliberat a
    `2026-08-03T20:51:11Z`. La condició antiga `M`/`1/640` va ser consumida;
    no és una instrucció vigent ni autoritza contacte PTP;
- handoff_r6m3_cfexpress_g1_2026_08_03:
  - autorització consumida sense ampliar abast: un únic setter separat
    `Drive -> Single`, un únic `Press Full MF` gphoto, cap replay, format,
    delete o captura EDSDK; bateria 16% final és advisory mission-first;
  - setter: una escriptura, readback `Single` en 7,043 ms després del commit,
    zero captures i cleanup net; preflight posterior independent amb M,
    Single, 1/640, AEB off, RAW CF, Memory card i `storageid=00010001`;
  - G1 `20260803T200855`: lateness 0,755 ms, ACK 43,218 ms, hold 1006,961 ms,
    un commit/release confirmat, zero Busy/timeout/recovery/replay/skip i
    `physical_state_unknown=false`; resultat SHA-256
    `6cf7fab30a4da70829a63e936d854ff638d69ce9f3e3c90870bcfa0fe8edff15`;
  - delta CFexpress exacte 73 -> 74: només
    `/store_00010001/DCIM/100EOSR6/572A2361.CR3`, zero removals; inventari post
    SHA-256 `1b6848317c92e34fa42bb56d95a4a59583ce94420512bd6418fc7c2269fe27cd`;
  - descàrrega manifest-bound: un `get`, dos inventaris remots complets i
    idèntics, 39 ordres auditades i zero ordre amagada/mutació; CR3 de
    26947796 bytes, SHA-256
    `4f710a0273a27ccd01ecc235c736e8cddfd1d11f2272d4b452b959fddd46a94d`;
  - inspector: ISO-BMFF complet, identitat exacta, RAW 6960x4640, Single,
    1/640, ISO160 advisory, AEB off i Electronic; ciència RAW continua
    pendent;
  - discrepància obligatòria: `572A2361` declara One-shot AF, Whole Area AF,
    35 mm f/1.4 i LensID Sigma 35/1.4; PASS només de transport/CFexpress, no de
    VSD90SS. Els CR3 `2338..2360` són MF i sense lent electrònica identificada,
    però tampoc proven per EXIF que siguin el VSD;
  - el perfil viu queda separat en G1 transport genèric i G1 VSD90SS estricte,
    que exigeix PTP Manual i confirmació física; inspector ampliat amb camps
    òptics/AF. Perfil immutable del run SHA-256
    `84e6f3ae4e7830efdf2b1b1b0e6ccbec9bc289109d3793b590bda9ded9e0d2b6`;
  - QA offline final: focalitzats 27/27, controlador 905/905, GUI 352/352,
    fuzz 67.392/67.392, py_compile i diff-check verds;
  - EDSDK continua en quarantena i no és backend operatiu; gphoto és el
    backend demostrat actual. Següent gate físic: VSD90SS confirmat + MF/focus
    locked + Single + CFexpress + delta/CR3 en un mateix run, sense considerar
    això un replay del G1 ja completat;
  - zero processos propis, PTP, gphoto2, EDSDK, tests o fuzz vius;
    `SERIAL_WRITES` alliberat a `2026-08-03T18:25:32Z`.
- handoff_r6m3_cfexpress_inventory_mission_first_2026_08_03:
  - regla corregida per ordre explícita de Pere: bateria `100%` és recomanació;
    `0%`, baixa, absent, no interpretable o error semàntic sincronitzat són
    warning no bloquejant. Busy, timeout, `-110`, taint, transport i identitat
    divergent continuen hard stop del canal;
  - política verificada 37/37 i revisió independent sense findings P0-P2;
    controlador 886/886, GUI 352/352, fuzz 67.392/67.392, py_compile i
    diff-check verds; eina SHA-256
    `fc8522bb472d2e49292aa1c4bf28d244b677c84742ffe3a711b5b27f617024ac`;
  - única sessió física `20260803T184748`: identitat exacta conservada,
    firmware `3-1.1.0`, bateria `46%` advisory, RAW CF, Memory card,
    `storageid=00010001`, un únic store `CFe` read-write;
  - inventari complet: 50 CR3 únics i contigus `572A2288.CR3` a
    `572A2337.CR3` dins `/store_00010001/DCIM/100EOSR6`; 6 directoris al store,
    7 globals, cap pendent/error/taint; això no prova mida, hash ni integritat
    del payload;
  - auditoria: 25 ordres read-only, un `storage-info`, 7 `cd`, 7 `ls`, zero
    ordre invàlida, setter, trigger, download, delete o format; zero commits o
    possible captura; cleanup i lock nets;
  - resultat SHA-256
    `006dd3bd91d7c28019d7455f5b544d15f7d1529aef46e06cd86a3f642ecf13df`;
    inventari `83f81d565ca03e262454b5e4f324bc21f240505833475fb6079e4007a5cbaa56`;
    evidència a
    `controller/runs/20260803T184748_lab_r6m3_readonly_r6m3-media-snapshot/`;
  - següent gate: Pere ha de decidir explícitament si conserva, descarrega amb
    gate separat o autoritza formatar aquests 50 CR3. Fins llavors no tocar-los.
- handoff_r6m3_cfexpress_battery_preflight_2026_08_03:
  - inventor CFexpress read-only endurit: perfil fixa backend/model/path de
    sèrie i cos `[SÈRIE]`; parser tolera opcionals Canon però exigeix
    basedir, particiona tots els stores, conserva raw+SHA i evidència parcial,
    reconcilia l'arrel i talla en Busy/timeout/`-110`/taint sense replay;
  - firewall limitat a `get-config`, un `storage-info`, `cd` i `ls`; cleanup
    exacte `release=false`, `recover_tainted=false`; zero format, setter,
    trigger, download o delete compilat al camí;
  - revisió adversarial final sense findings P0-P2; snapshot 33/33,
    controlador 882/882, GUI 352/352 i fuzz 67.392/67.392; eina SHA-256
    `24f9991de7855d19da2d30ae61208c0b804994a79748bdf9bea9bc1b849f0dce`;
  - única sessió física `20260803T183348`: model `Canon EOS R6 Mark III`,
    sèrie PTP `6d67c9923f453163358971b1b13d4c5f`, cos `[SÈRIE]`,
    firmware `3-1.1.0` i bateria `53%`; aturada abans de `storage-info`;
    exactament cinc lectures, zero ordre de targeta/mutació, zero commits o
    possible captura, sessió no tainted, cleanup i lock nets;
  - resultat SHA-256
    `aa474b956b69b6ea63f821aaf807b471cd13013e290a520bc51cb0a237b7aef2`;
    evidència a
    `controller/runs/20260803T183348_lab_r6m3_readonly_r6m3-media-snapshot/`;
  - no s'ha fet cap reintent. Següent gate: LP-E6P al 100% i autorització
    fresca per una única execució read-only; inventari i format continuen
    pendents, i cap format queda autoritzat encara que la targeta sembli buida.
- handoff_r6m3_cfexpress_readonly_2026_08_03:
  - capabilities CFexpress 83/83 i 87 ordres auditades, zero setter o trigger;
    identitat exacta conservada, `storageid=00010001`, RAW CF, card-only,
    7168 captures disponibles; preestat actual `Super high speed continuous
    shooting` i `1/16000`, per tant cap trigger autoritzat;
  - `storage-info` demostra un suport `CFe`, `/store_00010001`, read-write,
    `250042112 KB` totals i `250039296 KB` lliures; no demostra que sigui buit
    perquè encara no s'ha enumerat l'arbre;
  - primera execució del nou inventor read-only aturada perquè Canon omet els
    camps opcionals `label` i `freeimages`; cleanup i lock verds, 11 lectures,
    zero format/setter/trigger/download/delete, resultat SHA-256
    `e808542b15bd466ae772d5f6944e993bb50fd3471d23df96c5c5f684144b4549`;
  - parser corregit offline, perfil pinat també a sèrie de cos, 10/10 tests
    focalitzats, controlador 859/859, py_compile i diff-check verds;
  - revisió independent posterior: abans d'una nova execució cal separar
    inventari per store, conservar evidència incremental, admetre tots els
    camps opcionals de `storage-info`, reconciliar qualsevol entrada fora de
    `/store_*` i afegir test integral de cleanup/timeout/zero commits;
  - bateria última observada 20%; per protocol no s'ha repetit la primera
    execució física fallida. Següent gate: bateria 100% o LP-E6P carregada i
    autorització fresca per una única repetició read-only; no formatar sense
    inventari complet i autorització explícita separada;
  - informe actualitzat a
    `controller/R6M3_QUALIFICATION_2026-08-03.md`; zero processos propis o
    sessions PTP vius; `SERIAL_WRITES` alliberat.
- handoff_r6m3_qualification_2026_08_03:
  - identitat demostrada: USB `04a9:3323@01200000`, model
    `Canon EOS R6 Mark III`, sèrie PTP
    `6d67c9923f453163358971b1b13d4c5f`, cos `[SÈRIE]`, firmware
    `3-1.1.0`; `gphoto2 2.5.32`/`libgphoto2 2.5.34`;
  - capabilities read-only 83/83 i 87 ordres auditades, zero error, setter o
    trigger; M, Single, RAW/SD RAW, Memory card, MF, Continuous AF off, AEB off,
    High ISO NR off, 1/80, ISO 100 advisory i auto-power-off 0;
  - 11 captures gphoto Single/RAW card-only sobre SD provisional: G1 1/1,
    hold ladder 5/5 (`750/500/250/100/50 ms`) i dens 5/5 cada `500 ms`, amb
    11/11 pressos i releases, zero Busy/timeout/replay/skip/estat desconegut i
    deltes exactes `0 -> 1 -> 6 -> 11`;
  - sis CR3 manifest-bound descarregats i validats ISO-BMFF/ExifTool: model,
    sèrie, RAW complet, 6960x4640, ISO 100, 1/80, Single, AEB off, MF i
    Electronic coherents; `scientific_raw_verified=false`; els cinc CR3 densos
    només tenen manifest remot;
  - EDSDK 13.20.21 arriba a `CAPTURE_READY=true` però el probe endurit acaba en
    timeout de cleanup, exit 142, després dels unsets; cap trigger compilat ni
    enviat. Canal EDSDK en quarantena, captura SDK no provada;
  - inspector EDSDK privat corregit construït només offline, no executat,
    bundle verificat i sense `EdsSendCommand`; executable SHA-256
    `a86de6ba355788f013a3dd1442d87f5110b94c382150a253ea74b22a52f0951d`;
    SDK i codi privat exclosos per `.gitignore`, DMG desmuntat;
  - informe i taula E/A/V/H/S a
    `controller/R6M3_QUALIFICATION_2026-08-03.md`; perfils nous continuen
    `CANDIDATE_NOT_PRODUCTION` i no extrapolen SD a CFexpress;
  - regressió offline final: CR3 9/9, controlador 849/849, GUI 352/352, fuzz
    67.392/67.392, JSON, py_compile, codesign i diff-check verds;
  - bateria última observada 56%; zero processos propis, PTP, captures, tests o
    mounts vius. Els quatre fitxers de `controller/locks/` són històrics i no
    s'han tocat; `SERIAL_WRITES` alliberat.
- handoff_r6m3_initial_2026_08_03:
  - gphoto2 2.5.32/libgphoto2 2.5.34 reconeix la R6 III; bolcat read-only
    complet 83/83, 87 ordres auditades, zero errors, zero ordres prohibides i
    zero pressos. Model `Canon EOS R6 Mark III`, sèrie PTP
    `6d67c9923f453163358971b1b13d4c5f`, sèrie Canon `[SÈRIE]`, firmware
    `3-1.1.0`;
  - preestat SD provisional: RAW/card-only/MF/AEB off/Continuous AF off i
    auto-power-off 0; divergències P, ISO Auto, Drive Super high speed i High
    ISO NR High. ISO és advisory; P i Drive impedeixen una foto única segura;
  - perfil nou `controller/profiles/lab_r6m3_readonly.json`, bloquejat a
    `operator_capture_enabled=false`, `mission.enabled=false` i
    `preflight_only=true`; validació offline i pla read-only verds;
  - primer intent EDSDK es va bloquejar abans de `main` per Gatekeeper; zero
    sessió SDK demostrada i zero trigger. El framework Canon i bundles interns
    passen `codesign --deep --strict`, Developer ID Canon `XE2XNRRXZ5`; ZIP
    SHA-256 `689002d6c68d5531d0ce406b1404f772541437ffa846cc261a6fb3b88e90367f`;
  - wrapper privat local `/tmp/R6EDSDKProbe-private-20260803T1415.app`
    construït i verificat sense quarantena, encara no executat. No fer servir
    el guard `ptpcamerad` de gphoto2 amb EDSDK, que depèn d'ImageCaptureCore;
  - IORegistry mostra dos Canon: R6 III PID `0x3323` a 10 Gb/s i Canon 6D PID
    `0x3250` a 480 Mb/s. No repetir EDSDK fins aïllar/autoritzar el cos i
    corregir físicament M + Single; amb SD, cap gate de buffer o cronologia;
  - zero processos propis, sessions PTP, mounts o triggers vius;
    `SERIAL_WRITES` alliberat.
- handoff_0_7_4_2026_08_03:
  - correcció completada: la Canon 6D viva declara ISO 1600 per desplaçar la
    finestra AEB nativa de 6 EV cap a la corona feble; continua operator-owned,
    advisory i impossible de convertir en `FAILED`, bloqueig o exit no-zero;
  - GUI: una lectura ISO 100 amb preferència 1600 es mostra com `ADVISORY`,
    conserva `failed=0` i no desverifica la càmera; actor, valors i guies es
    deriven del perfil i els checks ISO d'operador guanyen els avisos genèrics;
  - història separada: Stage B v2 es reconstrueix exactament a ISO 100 només
    amb el snapshot explícit `7c14c5f2…`; contra el controlador viu
    `720d7fd2…` falla tancada. No s'afirma recompilació històrica byte a byte,
    RAW/CR2 exclusiu ni qualificació física ISO 1600;
  - A7III: evidència AP130 arxivada en dos gates independents 3/3 i 2/2,
    sense transferir-la al perfil 300GM actual; checklist 300GM separat;
  - run interromput manualment `20260803T004303`: A7III 58/60, Canon 90/93,
    A7RIIIA 74/83 commits i 65 JPEG locals; cap Busy, timeout, trigger ambigu
    o replay. Els 9 no executats i els 9 commits no drenats són conjunts
    diferents;
  - rectificació de `.coordination/CLAUDE_STATUS.md`: els quatre fitxers de
    `controller/locks/` que atribueix al run eren antics; els locks reals del
    run eren tres fitxers de runtime. No s'ha editat l'estat de Claude;
  - regressió final verda: GUI 352/352, controlador 840/840, fuzz
    67.392/67.392, perfils generats exactes, gates AP130, `git diff --check`
    i QA portable completa;
  - bundle actiu `gui/dist/Eclipse Command.app` 0.7.4; executable SHA-256
    `35a447713e0b6ebdce803e6016abd0cf35b794507fa65f6811b7849288719870`;
    manifest de 37 fonts SHA-256
    `aeec3ad6413330c528ed8a7615840e1602022412281068f9bcc27bcaae1df954`;
  - informe canònic `gui/QA_REPORT_0.7.4_2026-08-03.md`; cap GUI física,
    LaunchServices, PTP, `gphoto2`, trigger o càmera contactats;
    `EDSDKv132021M/` preservat intacte i fora del manifest;
  - zero processos propis vius; `SERIAL_WRITES` alliberat.
- handoff:
  - handoff Claude preparat: `CLAUDE.md` és el context canònic curt i actual;
    `AGENTS.md` és l'arrencada obligatòria, `README.md` la vista d'operador i
    `gui/QA_REPORTS.md` + `research/README.md` separen baseline viu d'història;
  - l'única prova útil del worktree Claude supersedit s'ha migrat a
    `gui/tests/test_packaged_profiles_coherence.py`; el worktree històric es
    conserva intacte i queda explícitament no canònic;
  - neteja recuperable a
    `/Users/USUARI/.Trash/Eclipse-2026-cleanup-20260802T1307Z`: 26 apps
    històriques, la venv 3.9 obsoleta, caches i auxiliars, 3,8 GB; a `gui/dist`
    només queden 0.7.2 i el rollback immediat 0.7.1;
  - Eclipse Command 0.7.2 construït i QA portable verd a
    `gui/dist/Eclipse Command.app`; executable SHA `7aeb0077…fcbc`, manifest
    37 inputs SHA `36c55d2a…de1`;
  - probes Sony operatius desactivats: primera captura dels tres cossos a C1;
    cap trigger exacte a C4, finestra quieta mínima 8 s;
  - Canon visible com `AEB +/-3 · 3 RAW/trigger`: 31/31 pressos, 93/93 commits
    al TEST RUN final; inventari SD posterior 815 CR2, coherent amb 629 + dos
    runs posteriors de 93;
  - A7RIIIA successor: 72/72 dins totalitat, 83/83 JPEG totals, dos EXIF de
    3,2 s, drains 27/36 en 19,297/26,423 s i bracket 9x1 a C3-3,1 s;
  - TEST RUN GUI final `20260802T140916`: `ok=true`; A7III 60/60, A7RIIIA
    83/83, Canon 93/93 commits; zero misses, skips o warnings de cronologia,
    cleanup verd i estat conegut als tres canals;
  - regressions GUI 345/345, controlador 834/834 i fuzz 67.392/67.392;
    mission-first, àudio, dry-run, routing USB, perfils curts, JSON,
    diff-check, coherència de manifest i QA portable verds;
  - informe `gui/QA_REPORT_0.7.2_2026-08-02.md`; recerca
    `research/49_POLIMENT_CONTACTES_I_C3_A7RIIIA_2026-08-02.md`;
  - límits: falta delta SD ARW fixed9 A7RIIIA i proves solar/òptiques; Canon
    Stage B/solar-òptica i R6 III/CR3 encara són qualificacions pendents;
  - QA portable del bundle 0.7.2, perfils curts, links Markdown i
    `git diff --check` verds; zero GUI, worker, mission_host, controller,
    gphoto2, build o test viu; cap PTP/càmera/LaunchServices tocat;
    SERIAL_WRITES alliberat.
- canon6d_hold_v7_hard_stop_2026_08_01_215340Z:
  - G1 v7 3/3 verd i certificat immutable SHA `9566467e…`; hold 0,9, 0,8,
    0,7, 0,6 i 0,5 s, cadascun 3/3 verd amb delta exacte, CR2 íntegres,
    ordre `1/250 -> 1/2000 -> 1/30`, hashes/EXIF/ledger i storageid
    `00020001` verificats;
  - endpoint hold canònic: evidència
    `certifications/canon6d_hold_v7_prefix_h0p5_20260801T214843Z.json`, SHA
    `0afa8908d4d34344ce9329d74e167bd44ac55b447ff1b6b9f1a98d125e3e3e28`;
    mínim verd 0,5 s i selecció operativa 0,6 s amb guard contractual +0,1 s;
  - hard stop h0p4, primera repetició: un únic Press/Release inequívoc i
    confirmat, hold real aproximadament 414 ms, controller/release/cleanup
    verds, zero Busy/0x2019/-110/timeout/warning/recovery, però la SD només
    passa 70 -> 72 amb `IMG_2365.CR2` i `IMG_2366.CR2`; ledger esperava 3;
  - no hi ha replay ni cap rung h0p3/h0p2/h0p1; els dos CR2 del rung vermell
    no tenen hash/EXIF/integritat perquè el card-gate va tallar abans de la
    descàrrega i la lectura estable; h0p4 no contamina l'evidència h0p5;
  - no cal power-cycle: `final_release_confirmed=true`, `cleanup_ok=true`,
    `physical_state_unknown=false` i cap warning/recovery. No tocar cos, AEB,
    ISO, cables ni Sony; només falta ACK explícit per iniciar una fase física
    nova i mai repetir h0p4;
  - preparació offline completada: bundle cadence 3,0 -> 2,0 -> 1,5 -> 1,25 s,
    G=2, hold=0,6 s, manifest SHA
    `35d5d22d93fe7a86f8479c7f696055081efdec7a09e2c43a17b2bb439bdd0db0`;
    runner `run_cadence_v7.zsh` SHA
    `97ac9451aaea9b2f7754d0f56e5ab6ccf88596d37bf4b74caf65b6dacae42449`,
    syntax verda; verifica SHA del manifest abans de cada repetició, compara
    cada snapshot amb l'inventari estable predecessor, pína l'inventari h0p4
    SHA `985f1c87…`, exigeix zero setters/restores globals i rebutja execució
    sense el token explícit de Pere; reauditoria independent final VERDA;
  - regressió completa posterior: controlador 803/803 verd; `zsh -n`, prova
    negativa sense ACK (exit 64), SHA d'inventari, scan d'events i
    `git diff --check` verds;
  - checkpoint OS post-hard-stop: zero GUI, worker, controlador, gphoto2,
    card-gate, runner o reconciliació vius;
  - `PROGRAM BLOCKED`, Stage A/B UTC, GUI, build/dist i Sony continuen
    intactes; SERIAL_WRITES es conserva ACTIVE per protegir l'estat Canon.
- canon6d_cadence_v7_resume_2026_08_01_220538Z:
  - Pere autoritza literalment `continua amb cadence sense repetir h0p4` i
    ordena `Acaba-ho tot`; token del runner habilitat només per aquesta fase;
  - revalidats owner/lease ACTIVE, Claude RELEASED, hashes controller/card-gate/
    certifier/builder/runner/manifest exactes i checkpoint OS amb zero GUI,
    worker, controlador, gphoto2, card-gate, runner, build o reconciliació;
  - no es repetirà h0p4 ni es tocaran les Sony; primer gate físic és snapshot
    SD exacte contra l'inventari h0p4 SHA `985f1c87…`.
  - primer snapshot `20260802T000601…` verd: exactament 72 CR2, últim
    `IMG_2366.CR2`, storageid/identitat/media binding verds i zero residual;
  - run `20260802T000602…` aturat al preflight abans de mutació o trigger:
    `capture_may_have_started=false`, commits=0, cleanup verd, però shutter
    viu `1/30` amb choice única en lloc de `1/250`; és estat AEB divergent
    heretat del bracket h0p4 incomplet;
  - zero Busy/timeout/recovery i zero processos finals. Cap replay ni segon
    run; dependència manual actual: power-cycle Canon OFF -> apagada completa
    -> ON, sense tocar cap setting/cable/Sony. Després cal repetir cold-start
    v7 zero-captura abans de cadence.
- canon6d_cadence_v7_complete_2026_08_01_222722Z:
  - Pere confirma el power-cycle manual posterior; el nou stage 1
    `20260802T001510…` falla tancat abans de mutació/captura perquè el cos
    conserva Drive `Continuous`, però demostra AEB `off`, shutter `1/250`,
    `capture_may_have_started=false`, commits=0, cleanup verd i estat conegut;
  - branca de represa auditada: no repetir stages 1-3; després del gap >7 s i
    checkpoint OS net, stage 4 immutable SHA `ffcc583b…f3b7` admet exactament
    el preestat observat i convergeix AEB `off -> +/- 3` amb un únic write,
    ACK 74,173 ms, readback/finals/cleanup verds, zero captures, Busy,
    -110, timeout, warning, recovery o replay;
  - snapshot inicial cadence exacte: 72 CR2, últim `IMG_2366.CR2`; cap
    `IMG_2367` residual tardà. Campanya immutable hold 0,6 s, G=2 completada
    12/12 verda per `P=3,0 -> 2,0 -> 1,5 -> 1,25 s`;
  - cada repetició aporta delta exacte +6 CR2 amb ordre
    `1/250 -> 1/2000 -> 1/30`, card-gate/hashes/integritat/EXIF/ledger i
    storageid validats pel runner; targeta 72 -> 144, següent `IMG_2439`;
  - certificacions de prefix: p3 SHA `54284154…b95b`, p2 SHA
    `1296bc11…fb0f`, p1p5 SHA `ac7a3288…572c`, p1p25 SHA
    `f8fc5d3f…79f1`; runner exit 0 i `CADENCE_CAMPAIGN_COMPLETE`;
  - PTP queda alliberat mentre s'audita el següent gate de buffer. Sony, GUI,
    build/dist, perfil operatiu i `PROGRAM BLOCKED` continuen intactes.
- canon6d_buffer_v7_ready_2026_08_01_224448Z:
  - auditoria cadence independent VERDA 12/12: 24 press commits inequívocs,
    72/72 CR2 nous `IMG_2367..IMG_2438`, hashes actuals/integritat/EXIF/ordre/
    ledger verds i zero Busy/-110/timeout/warning/recovery/replay/setters;
  - bundle buffer tail-only create-new G=1 -> 2 -> 4 -> 5, hold 0,6 s i
    P=1,25 s: manifest SHA
    `c9a3c3e19585cd29d4b05bf5bb09b50b525d434d8ecaa01de4cf2716d6edece5`,
    verificat offline; predecessor cadence SHA `f8fc5d3f…79f1` reobert;
  - inventari inicial pinat a 144 CR2/últim `IMG_2438`, SHA
    `10bfd31a7b35319e890a833c91a39f092b8d43489296e01b7f3897864578010c`;
    si tots 12 runs són verds, final esperat 252/`IMG_2546`, següent 2547;
  - runner `campaigns/run_buffer_v7.zsh` SHA
    `82c4034211951d28169ffb0bcfacaa99ce41e15127dbe2bedc8ee1ac359c0e99`,
    executable i sintaxi/diff/prova negativa verds; lease/owner/últim estat
    Claude, verifier immediat, sentinel one-shot durable, G1 certifier-grade i
    guards finals reaudits;
  - sentinel encara absent i zero PTP/run buffer iniciat. Hard stops i zero
    replay intactes; `G_ok` tail-only no equival a `G_ok_tail` ni a buffer ple.
- canon6d_buffer_v7_complete_2026_08_01_225701Z:
  - runner one-shot exit 0 i sentinel durable `complete`; campanya buffer
    tail-only G=1,2,4,5 completada 12/12 verda, tres repeticions per rung;
  - deltes exactes per run +3/+6/+12/+15, targeta 144 -> 252 CR2,
    `IMG_2439..IMG_2546` consecutius i següent esperat `IMG_2547`;
  - certificacions prefix G2 SHA `d053a89b…f8f7`, G4 SHA
    `c1fa1706…190c` i G5 final SHA
    `839ec5fe1592ef283039e4af7ee6420e9d4d3e674c8c90bb30fc0d35a57cb17e`;
  - evidència final `REPEATEDLY_GREEN_PREFIX`, hold 0,6 s, P=1,25 s,
    `G_ok=5`, `production_group_limit=4`, `boundary_only=false`; el G1 3/3
    va ser reobert certifier-grade abans d'avançar, sense crear un certificat
    invàlid de límit zero;
  - checkpoint OS posterior: zero GUI, worker, controller, gphoto2, card-gate,
    runner o reconciliació vius. Sony no tocades; PTP Canon alliberat;
  - límit explícit: és capacitat repetida amb tail inicialment buit, no
    `G_ok_tail`, no `BUFFER_FULL` i no qualifica encara tota la història C2-C3
    ni C1-C4. `PROGRAM BLOCKED`, perfil històric i app 0.6.7 intactes.
- canon6d_post_buffer_stage_ab_checkpoint_2026_08_01_230210Z:
  - auditoria independent del buffer final VERDA: certificat final
    `839ec5fe...cb17e` reconstruït, 108 CR2 reoberts/rehashejats/reinspeccionats,
    36 grups i 12/12 runs exactes, zero Busy/-110/timeout/warning/recovery/
    setter/replay; bateria observada al límit admès del 50 %;
  - el card-gate històric SHA `5f973244...` està pinat pels manifests físics
    hold/cadence/buffer i queda immutable; l'enduriment Stage A/B es farà en
    una eina nova versionada, sense invalidar evidència existent;
  - mostra read-only fresca `ntp_gettime`: `TIME_OK` i sincronitzada, però
    `maxerror_us=211108` (211,108 ms), per sobre del bound contractual de
    50 ms. Stage A queda fail-closed abans de gphoto2/lock/PTP; cap trigger o
    ordre PTP nova mentre el bound no sigui verd;
  - continuen offline l'enduriment gphoto2 Stage A/B, la derivació temporal
    relativa i el disseny del perfil operatiu nou. Perfil històric,
    `PROGRAM BLOCKED`, app 0.6.7 i Sony intactes.
- canon6d_timing_and_v2_offline_checkpoint_2026_08_01_232423Z:
  - bundle temporal v7 append-only complet a
    `timing/canon6d_cadence_buffer_timing_v7_20260801T2310Z`: 24/24 runs,
    60 pressos i 180 CR2 vinculats; manifest SHA
    `2ad2b8f0c5a80515fad2ad6d95cd0098fee8a717db1b5064378dd9db13255434`,
    index SHA `a5b7710f784d6cd529caa0ef607de01fb1ed5c3104e95843626b3597d018e9e5`
    i COMPLETE SHA
    `f6a9d2a83911e5ca0c3ee406f14cf5a31952ebdc148abd2d6671c5528dacecab`;
  - el bundle manté explícitament `physical_qualification_granted=false`,
    bounds UTC `null`, Stage A=false, `u` nominal no qualificat i cap claim
    `G_ok_tail`/`BUFFER_FULL`; P=1,25 s i hold són evidència relativa, no una
    localització absoluta respecte C3;
  - mostra de rellotge fresca read-only: kernel `TIME_OK`, però
    `maxerror_us=161982`; consulta SNTP sense ajustar el sistema:
    `+0.088292 +/- 0.026454 time.apple.com`. Stage A continua bloquejat abans
    de gphoto2/lock/PTP i no s'ha enviat cap ordre nova a la Canon;
  - entrypoint Canon v2 separat creat; controller legacy continua exactament
    SHA `b9c4b282...f4421d`, perfil històric `13b8fea1...f37c` i card-gate v1
    `5f973244...1063a` byte-for-byte. El v2 rebutja flags globals insegurs,
    un run bloquejat abans de crear artefactes, bindings legacy i Stage B
    sense binding controller+gphoto; regressió focal inicial 7/7 verda;
  - perfil/dispatch/packaging Canon v2 i enduriment final Stage A/B continuen
    en revisió offline. No build/dist, GUI, LaunchServices, PTP ni Sony.
- canon6d_g1_v7_active_2026_08_01_211735Z:
  - checkpoint OS verd: zero GUI, worker, controlador, gphoto2, card-gate o
    build viu; IORegistry mostra una sola `Canon Digital Camera`;
  - `media_identity` operator-attested preservat literalment: `aquesta és una
    ScanDisk Extreme Pro 200MB/s, molt més ràpida del que la 6D té com a
    límit, no serà mai un coll d'ampolla`;
  - la capacitat no és obligatòria pel validador viu: el token no buit, no
    sintètic, de 120 caràcters ha superat el pla offline sense contactar ni
    mutar la càmera;
  - hashes verificats abans de PTP: controller `b9c4b282…f4421d`, G1 v7
    `887da805…c7dd`, card-gate `7c6954a1…a2d98`, certifier
    `e94b3f1c…6e143`;
  - hard stops: zero replay i zero reintents; aturar al primer `0x2019`,
    `-110`, timeout, trigger ambigu o delta/hash/ordre/EXIF/ledger CR2 incorrecte;
    no tocar Sony, GUI, build/dist ni retirar `PROGRAM BLOCKED`.
- planned_checks:
  - completats: GUI 324/324, controlador 802/802, py_compile, shell syntax,
    diff-check, build transaccional, QA portable i checkpoint OS final
- handoff:
  - Eclipse Command 0.6.7 actiu a `gui/dist/Eclipse Command.app`; versió
    visible/interna 0.6.7, arm64, macOS mínim 26.0, signatura ad-hoc vàlida,
    no notaritzat i `gphoto2` extern
  - manifest 35/35 verd, SHA
    `1caffeb45ab6668f90c88ae901b8a706a99849c80dc502646a7553a5a5ba0e60`;
    executable SHA
    `29b80e2791258de1d0574695daefd16144a14fcac51a7d24ea543a2027fc4c1b`
  - controlador v7 empaquetat SHA `b9c4b282…`; perfil Canon preservat byte a
    byte en `13b8fea1…` perquè els artefactes físics v7 el pinen
  - QA portable verd: relocació, 114 Mach-O, frozen validate/worker, tres
    seleccionades, dues llançades, Canon exclosa i GUI offscreen amb gphoto fals
  - bundle anterior preservat a
    `gui/dist/Eclipse Command.app.previous-20260801T205940Z-49108`
  - informe nou `gui/QA_REPORT_0.6.7_2026-08-01.md`; README, guia GUI,
    packaging i CLAUDE actualitzats al baseline 0.6.7
  - checkpoint final: zero GUI/worker/controller/gphoto2/build/QA viu, zero
    staging i zero locks de build/GUI; cap PTP, trigger, captura o càmera tocada
  - Canon continua `PROGRAM BLOCKED`; cold-start v7 no substitueix la
    identitat de SD, G1, ladder/buffer, CR2 ni Stage A/B
- canon6d_cold_v7_physical_release_2026_08_01_204405Z:
  - cold-start v7 completat físicament i verd, sempre amb identitat Canon
    exacta, `open_attempt_count=1`, `ptp_open_max_attempts=1`,
    `open_failures=[]`, zero `0x2019`/`-110`/timeout/warnings, zero captures i
    cleanup/restore confirmats;
  - stage 1 `20260801T224234…`: AEB `off`, no-op, writes=0; stage 2
    `20260801T224252…`: obturació `1/250`, no-op, writes=0;
  - stage 3 `20260801T224312…`: `Single -> Continuous`, un write, ACK
    70,8 ms i readback verd; stage 4 `20260801T224330…`: AEB
    `off -> +/- 3`, un write, ACK 74,3 ms i readback verd;
  - estat final demostrat: Continuous, AEB +/-3, 1/250, RAW, ISO 100,
    capturetarget Memory card, Image review None i mirror lock 0;
  - regressió prèvia: focals 150/150 i controlador complet 802/802;
    `py_compile` i `git diff --check` verds;
  - checkpoint OS posterior: zero Eclipse Command, worker, controlador,
    gphoto2, card-gate o build; només `ptpcamerad` del sistema, rellançat
    després d'alliberar la sessió. Cap PTP o ordre a les Sony;
  - hard stop actual abans del primer trigger G1: falta la identificació
    literal impresa de la SD (marca, capacitat i model/serial o marca
    distintiva) per al `media_identity` operator-attested. `PROGRAM BLOCKED`,
    Stage A/B i el rebuild de l'app continuen intactes; totes les rutes i
    SERIAL_WRITES queden alliberats fins a la resposta de Pere.
- canon6d_program_blocker_and_offline_ladder_release_2026_08_01_201416Z:
  - causa del run de Pere demostrada: la Canon constava seleccionada/READY a
    la GUI antiga però el seu `mission_capture_blocked_reason` la va ometre
    abans de crear worker; no va rebre cap PTP, trigger ni captura;
  - contracte nou: `PROGRAM BLOCKED` sobreviu scan/preflight/canvis de port;
    START mostra 2 càmeres i audita 3 seleccionades, 2 llançades i Canon
    exclosa (`pre_start_gate`, `failed_physical_gate`, motiu 0x2019). Builder
    i host rebutgen qualsevol RUN que intenti incloure el perfil bloquejat;
  - perfils malmesos queden visibles com `PROGRAM KO` sense ocultar els
    perfils vàlids; amb zero perfils vàlids la GUI falla abans del discovery;
  - ladder Continuous offline hardenitzada: baseline canònic G1 v6 SHA
    `fd30acf73caad2c67625037808087d8b82fd3018ad57d4133eaf31632b798992`,
    CR2 reoberts/reinspeccionats, identitat física SD + storageid heretats,
    reús/tamper rebutjats i predecessor reconstruït transitivament;
  - regressió final: GUI 324/324, controlador 793/793, focal ladder/card-gate/
    C3 111/111; QA mission-first, permutació USB i dry-run verdes;
    `py_compile`, `sh -n` i `git diff --check` verds; QA visual 1024x720
    revisat sense clipping;
  - QA portable corregida perquè validi l'A7RIIIA operativa densa i no el
    perfil legacy de dues accions. Bundle 0.6.6 reconstruït/activat a
    `gui/dist/Eclipse Command.app`; anterior preservat a
    `gui/dist/Eclipse Command.app.previous-20260801T201329Z-28158`;
  - QA portable final verda: manifest/font, signatura ad-hoc, relocació,
    114 Mach-O autocontinguts, 3 seleccionades/2 workers/Canon exclosa,
    rebuig frozen del RUN Canon bloquejat i GUI offscreen; payload 120,6 MiB,
    executable SHA-256
    `bc8edb8f9dfb277e987b00aeb8f708bfedeaed519010fd630b5df07ae32e959f`;
  - hashes font finals: domain `d7d5c52d…`, main_window `22c39c06…`,
    mission_host `2dc8375e…`, controller `b5df9d9b…`, perfil Canon
    `13b8fea1…`, ladder builder `3c049eda…`, certifier `26a3191e…`, card gate
    `bcd85512…`; manifest incrustat verificat contra la font viva;
  - checkpoint OS final: zero Eclipse/mission/worker/controller/gphoto2/build,
    zero locks, zero staging i zero worker_state no terminal. Cap PTP, captura
    o maquinari Canon executat en aquesta unitat;
  - hard stop físic mantingut: falta power-cycle manual posterior a l'últim
    Busy i la cota UTC observada és encara superior als 50 ms d'Stage A. La
    Canon no queda qualificada ni armada; el pas següent exigeix Pere despert.
- gui_canon_blocker_checkpoint_2026_08_01_193016Z:
  - causa del run demostrada: la Canon estava seleccionable i apareixia READY,
    però `mission_capture_blocked_reason` la feia caure durant materialització;
    el run només va congelar/llançar A7III+A7RIIIA i la Canon no va rebre cap
    worker, PTP ni trigger;
  - UI separa ara seleccionada/comprovable, capturable i llançada: la Canon es
    mostra `PROGRAM BLOCKED`, START compta 2 càmeres, el blocker sobreviu
    rescans i canvis de port USB, i un preflight no la torna falsament READY;
  - `launch_spec.json`, `mission_started` i `mission_result.json` conserven els
    3 canals seleccionats, els 2 workers reals i l’exclusió Canon estructurada
    (`pre_start_gate`, `failed_physical_gate`, motiu 0x2019); l’exclusió força
    WARNING sense inventar deute d’imatges ni totals per un worker inexistent;
  - proves: GUI 315/315, controlador 765/765, tres QA offline mission-first /
    routing dinàmic / dry-run verds, `py_compile` i `git diff --check` verds;
    QA visual 1024x720 revisat sense clipping;
  - bundle 0.6.6 reconstruït i activat a `gui/dist/Eclipse Command.app`;
    anterior preservat a
    `gui/dist/Eclipse Command.app.previous-20260801T192917Z-8966`; QA portable
    verd (manifest/signatura/relocació, 114 Mach-O, quatre perfils, worker,
    missió tres canals validate i GUI offscreen); payload 120,6 MiB;
  - hashes empaquetats: domain
    `cd29449bf3d2a8bd9b9ac031c63bb08db8d87949abc8263e5818eab61498832f`,
    main window
    `adc6f0bb2749f9d3e79fb10b36f372d51a93dadbbd9951fb9fc606ef5045b01b`,
    mission host
    `10962a372ffadae67e5c91d27c32c2baf8249b620954d08b15887204536ed818`,
    widgets
    `3ea3c6a604873460e662eb4f410a6b7979f524b47c47afd0439f59aa47776946`;
    controlador/perfil Canon preservats en `b5df9d9b…` / `13b8fea1…`;
  - checkpoint postbuild: zero GUI/worker/controller/gphoto2/build viu i zero
    staging `.portable-build.*`; la GUI antiga PID 1220 s’ha tancat. Cap gate
    físic Canon nou iniciat.
  - hard stop actual: falta confirmació d’un power-cycle físic de la 6D
    posterior a l’últim Busy. La nova execució no va crear canal Canon i no ho
    demostra; l’autorització desatesa no permet inventar aquesta acció manual.
- planned_checks:
  - tancar/controlar explícitament la GUI externa PID 62383 i verificar zero
    mission/worker/controller/gphoto2 abans del primer patch
  - proves focals de copy, icones, singular/plural i tooltip WARNING
  - regressions GUI+controller completes i QA visual a 1024x720
  - rebuild transaccional, QA portable, checkpoint OS final i handoff Canon
- safety:
  - zero maquinari, PTP, gphoto2 o captures; només tancament controlat de la
    GUI externa i `lsregister -f` estrictament necessari del rebuild final
  - Stage B i qualsevol PTP continuen bloquejats fins al power-cycle físic
    posterior a l'últim Busy i fins que el pont UTC sigui verificat
  - preservar tots els canvis preexistents i el bundle 0.6.6 acabat de congelar
  - no editar `CLAUDE_STATUS.md`
- gui_beer_rocket_warning_release_2026_08_01_185335Z:
  - `Buy me a beer :)` incorpora SVG de gerra i `Start mission` incorpora SVG
    de coet; el copy és ara `Start mission · N camera(s)` amb singular,
    plural, tooltip i accessibilitat coherents;
  - el pill superior queda definit com a resultat de l'operació, separat de
    la flota viva: tooltip amb causes retingudes, avisos previs resolts marcats
    a Activity i cap promesa d'èxit quan el resultat del controlador és
    absent o inconcloent;
  - eliminat el fals arrossegament d'avisos de settings: només s'eliminen si
    aquest mateix preflight ha produït evidència verificable; outcomes
    multicàmera READY/WARNING es preserven per canal i una cache anterior no
    pot maquillar el resultat actual;
  - causa concreta del screenshot: el límit UTC era `DEGRADED` a ≤253 ms
    (per sobre del límit bounded de 100 ms), juntament amb avisos de programes
    candidate/card-only; són avisos mission-first, no un duplicat de la
    connexió READY;
  - proves focals 40/40, GUI completa 308/308 i controlador complet 765/765
    verds; QA geomètric 1024×720 i revisió visual offscreen verds; diff-check
    verd;
  - bundle 0.6.6 activat a `gui/dist/Eclipse Command.app`; anterior preservat
    a `gui/dist/Eclipse Command.app.previous-20260801T185252Z-77797`;
    QA portable verd: manifest/signatura, relocació, 114 Mach-O, quatre
    perfils, worker, missió tres canals i GUI offscreen; 120,6 MiB;
  - manifest empaquetat: `main_window.py`
    `4455170169d6efe26562eb909946cccb9e770f05b2ae0d9f1a6105ce23d96934`,
    `beer.svg` `6bb371d85fd1d539b16c166a04aaf4f6b1c328cd8f4990ec1ad71311fc708cee`,
    `rocket.svg` `827c8ef0ded4f2ead6a685f7f0d4f37d3e27aaff5821b9b74ab35a33b312db43`
    i controlador Canon
    `b5df9d9bdbd6a973df0630f93207afac6bfefb1021b1a9535c019ea29f72a4c3`;
  - checkpoint final: zero GUI/worker/controller/gphoto2/build viu, zero
    staging `.portable-build.*`, cap PTP, captura o maquinari tocat; totes les
    rutes i SERIAL_WRITES alliberats per reprendre Canon.
- canon6d_v6_gui_override_release_2026_08_01_183343Z:
  - override GUI rebut i Canon aturat al primer checkpoint coherent; cap procés
    de prova/subagent propi, escriptura o reconciliació resta viu;
  - productor `timeline_clock_bridge.json` implementat abans de gphoto2/lock/PTP
    per full-history: dues mostres `ntp_gettime`, event timeline complet,
    O_EXCL/fsync, fingerprints i hard-stop inclòs mission-first;
  - card-gate i planner reobren bridge/events amb O_NOFOLLOW, mateixos bytes i
    SHA, i repeteixen run/perfil/timing/bound/bracket/residual/event ordering;
  - ABI macOS `ntptimeval` corregida a `tai: long`, contrastada amb SDK local;
    lectura actual TIME_OK però maxerror aproximat 0,20 s, massa alt per ε=0,05;
  - focals pont+C3+GUI clock: 127/127 verds; migració cold/preconfigured v6:
    81/81 verds, verifier cold, validate/dry-run, py_compile i diff-check verds;
  - controller SHA-256
    `b5df9d9bdbd6a973df0630f93207afac6bfefb1021b1a9535c019ea29f72a4c3`;
    cold v6 manifest
    `c74f86f3e97597e4a72a927c3faf7d15666f46a5633a9b94437dedaab8a026ec`;
    stages `ad508d3d9314c038beef429b413bf9324552ec0cb8ae2ac685be52089d6ea3c3`,
    `436651e599e4a07ad4ff0e3ab6439bf00e0fb131748a18e601afecad9243d35b`,
    `bb868c5f6e26e30d90df4402a70024131226b60ecd0ba5fee411c859dcf266da`
    i `1974296d27c334a2afc3e11a5701c824a7f9d54fe08c3ea99f36ebd67e1c08dc`;
    preconfigured v6
    `fd30acf73caad2c67625037808087d8b82fd3018ad57d4133eaf31632b798992`;
  - v1-v5 preservats immutables i v5 quarantinat; cap suite completa ni build
    executats encara després d'aquesta unitat;
  - zero PTP/captura/maquinari del task Canon. Inventari OS final detecta una
    GUI externa preexistent `Eclipse Command.app` PID 62383 (PPID 1) i, en el
    primer mostreig, el seu fill temporal gphoto2 de bateria; no els hem obert,
    tancat ni modificat. El task GUI n'assumeix el gate explícitament.
- canon6d_reacquire_2026_08_01_180755Z:
  - handoff GUI rebut RELEASED a 18:06:46Z; totes les rutes alliberades;
  - inventari OS previ: zero Eclipse Command, mission/worker/camera host,
    controlador, gphoto2 o reconciliació vius;
  - represa només offline; cap ordre a la Canon fins als hard gates indicats.
- utc_map_tenths_release_2026_08_01_180646Z:
  - C1-C4 exposen només una dècima (`HH:MM:SS.s`); TEST RUN arrodoneix cap
    amunt només el residu sub-dècima, conserva els trams i el rollover UTC;
  - `UTC` és un link intern accessible per ratolí i teclat; tres polsos en
    aproximadament 0,8 s emmarquen exclusivament el rellotge UTC superior,
    amb contrast 7,41:1 i sense salt de layout;
  - eliminat `CONTACTS VALID`; errors i `ALREADY IN PROGRESS/ELAPSED` es
    conserven. Ajuda permanent obre exactament el mapa Xavier Jubier al
    navegador i no omple C1-C4;
  - regressió GUI completa 303/303 verda; després de la neteja final del
    tooltip, focal 56/56 verda; contracte visual/contrast 71/71 verd;
    `qa_persistence.py`, `py_compile` i `git diff --check` verds;
  - QA visual offscreen revisat a mida mínima en estat normal, flash, error i
    contactes ja en curs: cap clipping i target del flash correcte;
  - bundle 0.6.6 reconstruït i activat a `gui/dist/Eclipse Command.app`;
    anterior preservat a
    `gui/dist/Eclipse Command.app.previous-20260801T180536Z-57931`;
  - manifest empaquetat fixa `gui/eclipse_command/main_window.py` amb SHA-256
    `2d216b8f3e286e376434a55ffbf01b80327877766d6885305c91d2245e0e5f82`,
    idèntic a la font viva;
  - QA portable verd: metadata, manifest, signatura, relocació, 114 Mach-O,
    macOS mínim 26.0, quatre perfils congelats, worker, missió de tres canals,
    GUI offscreen i runtime QtTextToSpeech; payload 120,5 MiB;
  - checkpoint final OS: zero Eclipse/worker/controller/gphoto2/build viu i
    zero staging `.portable-build.*`; cap PTP, captura ni maquinari tocat.
- app_0_6_6_release_2026_08_01_174534Z:
  - nou bundle activat a `gui/dist/Eclipse Command.app`; l'anterior queda
    preservat a
    `gui/dist/Eclipse Command.app.previous-20260801T174448Z-51027`;
  - build canònic `./gui/build_macos_portable_app.sh` complet: staging,
    doble verificació del manifest, quatre `validate` congelats, derivació
    `LSMinimumSystemVersion=26.0`, signatura ad-hoc, activació transaccional i
    `lsregister -f` verds;
  - QA portable complet verd: metadata/signatura/manifest; relocació amb PATH
    de sistema; 114 Mach-O autocontinguts; controlador congelat per quatre
    perfils; worker; missió tres canals; GUI offscreen amb gphoto2 fals;
  - payload 120,5 MiB, versió visible i interna `0.6.6`, macOS mínim 26.0;
    build local arm64 ad-hoc, no notaritzat; `gphoto2` continua extern;
  - QtTextToSpeech verificat dins el bundle: binding, framework i backend
    `speechdarwin`; el manifest fixa `main_window.py` amb SHA-256
    `a5afac98bc2188a274b0acd7f29d001fb9fd6dbed1c0cb2167d0698ee5a0dab4`,
    idèntic a la font que mostra `Buy me a beer :)`;
  - checkpoint prebuild: hashes Canon idèntics al handoff, locks absents,
    zero processos i zero worker_state no terminal. Checkpoint post-QA:
    manifest revalidat, locks absents i zero GUI/worker/controller/gphoto2/
    build viu;
  - baseline empaquetat: controlador 756/756, C3 81/81, runtime/cold/lab
    79/79 + 9/9 i GUI 298/298, tots verds abans del freeze;
  - zero PTP, gphoto2 real, captures o maquinari. Stage B Canon continua
    bloquejat per observació UTC immutable i power-cycle físic pendent; aquest
    build no és qualificació física.
- canon6d_packaging_handoff_2026_08_01_174239Z:
  - checkpoint offline complet: controlador 756/756; unitat C3 81/81;
    runtime/cold/lab 79/79 i runtime específic 9/9; GUI offscreen 298/298;
    `py_compile` i `git diff --check` verds;
  - cold-start v5 immutable verificat: manifest SHA-256
    `e55d51a307d2958d202d8fbe3016e246854902748f99d7e703bdce6c545ce206`;
    stages `7fc31e87f7a0ecab90350b23a71e1f7a012f060f237418e51df1ec30646959f4`,
    `2bfd05fa51826efd7164a6025011461ceffea7311fed06458543099c1c78a1b8`,
    `72c6e9df2eab25820aa33daa72c965ee01689023b2f4830341632a06090002e7`
    i `ce1d998c776ac2c954db60ff204dafd4f493ae66742e63a45032b0a5526c08fe`;
  - perfil preconfigured v5 SHA-256
    `8763b479f954dbe46b3d9c8b3e6f75802a29a843524114ecbcf6e0ba126c09b0`;
  - inputs aptes per empaquetar: controlador
    `4533e6db01c4711a0d3628790569392e13a46a113ede640676135aab8f763f56`,
    perfil Canon font
    `13b8fea1f0abd980e145a7f395152834f1927f8de4be7339ff2500996679f37c`,
    card-gate `4689735b504a7321fff375c3c1f832476a16864807f0b54825989edf3e01e3b0`,
    planner `3308336dfe4b4e98bd3051e5875ecced32205d98eefe4f866e3f915af68d7537`
    i compiler `31a531dc46855d229b8915c517488ea6b296f9abe86afcb083fe2e8d3f8b8ab3`;
  - cap build/dist, LaunchServices, GUI interactiva, PTP, gphoto2, captura o
    maquinari executat en aquesta unitat;
  - Stage B físic continua deliberadament bloquejat: falta una observació UTC
    immutable correlacionada amb la cronologia i el power-cycle físic posterior
    a l'últim Busy; l'evidència offline no és qualificació física;
  - la GUI externa PID 21124 queda delegada explícitament al task GUI/build.
- canon6d_resume_after_beer_label_2026_08_01_173605Z:
  - handoff GUI RELEASED rebut a 17:35:51Z; Canon reacquirit després;
  - es reprèn exactament del checkpoint C3 80/81, sense repetir feina física;
  - cap PTP, gphoto2, captura o maquinari fins a tancar els gates pendents.
- buy_me_a_beer_release_2026_08_01_173551Z:
  - etiqueta visible canviada de `Donate via PayPal` a `Buy me a beer :)` a
    `gui/eclipse_command/main_window.py`; URL, tooltip i comportament PayPal
    preservats byte per byte;
  - expectativa focal actualitzada exclusivament a
    `gui/tests/test_main_window_discovery.py`;
  - 2/2 proves PayPal offscreen verdes; `py_compile`, `git diff --check` i
    comprovació literal amb `rg` verdes;
  - zero Canon/controlador/bundles, build/dist, GUI interactiva,
    LaunchServices, PTP, gphoto2, captura o maquinari. El bundle obert antic
    no s'ha reconstruït i PID 21124 continua intacte;
  - cap procés de prova viu; SERIAL_WRITES i totes les rutes alliberades per
    reprendre el checkpoint Canon 80/81.
- canon6d_gui_override_release_2026_08_01_173450Z:
  - override GUI rebut i Canon aturat al primer checkpoint coherent; cap test,
    escriptura o procés Canon queda viu;
  - afegit gate executable de dependències abans de qualsevol mode/PTP;
    cold-start v1-v4 i preconfigured v2-v4 queden quarantinats per absència o
    SHA divergent;
  - cold-start v5 immutable generat i verificat, manifest
    `e55d51a307d2958d202d8fbe3016e246854902748f99d7e703bdce6c545ce206`;
    preconfigured v5 SHA
    `8763b479f954dbe46b3d9c8b3e6f75802a29a843524114ecbcf6e0ba126c09b0`;
  - regressió focal runtime/cold/lab: 79/79 i runtime específic 9/9 verds;
  - unitat card-gate/planner/compiler sintàcticament coherent: 80/81; l'únic
    vermell és una regex antiga que espera `C2-C3 divergent`, mentre el nou
    gate talla abans amb `timing_request divergeix del run_manifest pinat`;
  - Stage B exigeix ara observació UTC estructurada; cap manifest físic actual
    la conté, de manera que queda bloquejada deliberadament;
  - no s'ha executat cap suite completa postcanvi, build/dist, GUI,
    LaunchServices, PTP, gphoto2, captura o maquinari;
  - GUI externa PID 21124 continua com a gate heretat, no tocada en aquesta
    unitat. El power-cycle posterior a l'últim Busy continua pendent.
- canon6d_resume_2026_08_01_171805Z:
  - handoffs GUI i producte rebuts RELEASED; reserva Canon adquirida després;
  - la modificació parcial del card-gate anterior queda declarada no verificada
    i es completarà i provarà com una sola unitat;
  - GUI externa preexistent PID 21124 segons el handoff: cap build,
    LaunchServices o gate físic fins a revalidar-la i tancar el checkpoint;
  - cap PTP, gphoto2, captura o maquinari en aquesta represa offline.
- product_objectives_release_2026_08_01_171756Z:
  - `README.md` incorpora al principi els tres objectius principals del
    projecte, en l'ordre fixat per Pere: Mission first, simplicitat i disseny
    perquè l'usuari la munti amb Agentic AI per optimitzar la seva càmera;
  - `CLAUDE.md` incorpora la mateixa secció dins de `Què és aquest projecte`,
    abans del resultat final buscat;
  - l'Agentic AI queda restringida a assistència de configuració,
    qualificació i optimització; el camí crític continua local, offline i
    determinista;
  - s'han preservat tots els canvis preexistents. `git diff --check --
    README.md CLAUDE.md` és verd i l'ordre 1/2/3 s'ha verificat als dos
    documents;
  - zero proves de codi perquè el canvi és només Markdown; zero maquinari,
    PTP, gphoto2, captures, GUI, build, packaging o LaunchServices;
  - totes les rutes i `SERIAL_WRITES` queden alliberats perquè Canon pugui
    reprendre.
- gui_audio_release_2026_08_01_171614Z:
  - TEST RUN conserva la precisió interna, eleva el residu a la centèsima
    següent i mostra exactament dues xifres als quatre contactes, al resum i a
    la cronologia; rollover UTC preservat;
  - `Contact audio` és ara un botó accessible només amb icona: altaveu normal
    significa àudio actiu i altaveu tatxat significa silenciat; `Test audio`
    prova la veu i cau a dos bips si no hi ha motor anglès capaç;
  - cues angleses d'una sola emissió i sense replay tardà a C1−10 s, C2−20 s
    (retirar filtre), C2−10 s i C3 (tornar a posar el filtre). Els patrons
    independents 1/2/3/4 bips es conserven, inclòs C3 davant errors TTS
    asíncrons; els errors de backend desactiven les veus posteriors però mai
    bloquegen una missió;
  - `UTC` queda blau `#0B52AE`, subratllat i amb nom accessible en text pla;
  - packaging fail-closed ampliat a binding, framework i backend speechdarwin
    de QtTextToSpeech; PyInstaller declara també l'import explícit i el QA del
    bundle exigeix els tres artefactes;
  - proves focals: 74/74; suite GUI completa: 298/298; `qa_audio_patterns.py`
    PASS; `py_compile` i `git diff --check` verds. Motor offscreen local:
    `darwin`, capacitat Speak i locales en_US/en_GB/en_AU disponibles;
  - render Fusion offscreen inspeccionat a
    `/private/tmp/eclipse-ui-audio.FqenSA/`
    `eclipse-command-test-run-audio-centiseconds-final.png`: geometria neta,
    centèsimes, UTC i icona correctes;
  - no s'ha reconstruït ni activat `gui/dist/Eclipse Command.app`: el bundle
    actual és anterior, no conté QtTextToSpeech i ja falla la coherència de
    font al primer canvi (`controller/eclipse_capture.py`). Reconstruir-lo
    substituiria l'app i invocaria LaunchServices, fora de l'autorització;
  - zero processos de prova, controlador, gphoto2 o fills de captura creats per
    aquesta unitat. Inventari OS final detecta una GUI externa preexistent
    `Eclipse Command.app` PID 21124, iniciada 18:46:44 local, PPID 1 i sense
    fills; no l'hem obert, tancat ni modificat. Qualsevol gate físic ha de
    tractar-la explícitament abans d'armar;
  - zero PTP, gphoto2, captures, maquinari, GUI interactiva o LaunchServices;
    `CLAUDE_STATUS.md`, `README.md` arrel, `CLAUDE.md` i rutes Canon intactes
    durant aquesta unitat.
- canon6d_v4_checkpoint_for_gui_2026_08_01_165931Z:
  - la nova petició GUI de Pere interromp la unitat Canon en un checkpoint
    només offline; zero PTP, gphoto2, captures, GUI o LaunchServices;
  - es preserven sense editar ni executar els bundles immutables v3/v4 i el
    perfil preconfigured v3 sota
    `controller/runs/codex_20260801_canon6d_optimization/profiles/`;
  - la unitat Canon havia tocat el controlador, generadors, planificador,
    card-gate, proves i documentació Canon. No es reverteix ni es fusiona res;
  - cap regressió final Canon queda reclamada en aquest checkpoint. Abans de
    reprendre o usar v4 cal reauditar SHA, manifests, TOCTOU i suites pròpies;
  - propietat de totes les rutes Canon alliberada; aquesta unitat GUI no les
    tocarà.
- a7m3_final_release_2026_08_01_163110Z:
  - Dense Single qualificat físicament a 1,250, 1,125 i 1,000 s: tres runs
    20/20, hashes JPEG únics, cues a zero, drenatges finals de 9,489, 9,468 i
    9,468 s, sense warning, skip, recovery ni estat desconegut;
  - 5x3 fix a 10,2 s: cinc grups, 25/25 JPEG, ordre EXIF repetit
    -6,-3,0,+3,+6, cua 25->0 i drenatge final 10,896 s, cleanup/restore verds;
  - 9x1 fix a 8,2 s: tres grups, 27/27 JPEG, ordre EXIF -4..+4, cua 27->0 i
    drenatge final 12,432 s, cleanup/restore verds;
  - hard stop al rung següent 9x1: quatre press/release ACK però només 27/36
    JPEG, exactament tres brackets complets, `d215=0`, drenatge normal 120 s i
    drenatge d'emergència 120 s tots dos esgotats. Zero retry, reconnexió,
    recovery o replay; no s'ha enviat cap altre trigger després del dèficit;
  - `cleanup_ok=false` del hard stop prové exclusivament del 27/36 persistent;
    restauracions individuals de `Single Shot` i `1/8000` amb ACK/readback,
    release final confirmat i `physical_state_unknown=false`;
  - el límit qualificat A7III queda en 3x9 a 8,2 s; 4x9 a aquesta cadència és
    prohibit. No s'ha promocionat cap core: el candidat MISSION FIRST conserva
    la geometria A7III històrica Single + 1x5 + 3x9;
  - ISO 100 ha estat la base dels labs, però la missió no escriu, restaura ni
    corregeix ISO; qualsevol canvi manual de Pere continua sent advisory;
  - una GUI externa PID 5212 només fou detectada entre gates; els seus workers
    ja havien acabat sense missió/captura. Es va tancar abans d'armar res i el
    preflight estricte posterior fou verd: bateria 93 %, cua zero, ISO 100,
    `Single Shot`, `1/8000`, zero writes/triggers i cleanup conegut;
  - rebut offline final a
    `research/47_OPTIMITZACIO_A7III_C2_C3_2026-08-01.md`; 12 perfils lab,
    generador `--check`, 6/6 proves focals i validate+dry-run 12/12 verds;
  - queda fora d'aquesta qualificació: core híbrid propi, transicions amb cua,
    delta SD/ARW exclusiu, gate òptic/solar i resiliència física USB;
  - checkpoint OS-level final buit: zero Eclipse Command, gphoto2,
    `eclipse_capture.py`, mission/worker/camera worker o reconciliació. No hi ha
    cap procés ni operació física A7III viva; SERIAL_WRITES queda alliberat.
- a7m3_physical_checkpoint_2026_08_01_161358Z:
  - controlador físic congelat SHA-256
    `9d6b23d465a332931505999328e623af815cf2c39dd13bb93bc9c288f1d443cd`;
  - Dense Single A7III complet a 1,250 s, 1,125 s i 1,000 s: tres runs
    20/20, cues 20->0, hashes JPEG únics, zero warnings/skips/recovery,
    cleanup/restore verds i estat final conegut;
  - primer gate fix 5x3, tres grups a 10,2 s, va executar físicament 15/15
    amb tres press/release ACK, cua 15->0, zero warnings/skips/recovery i
    cleanup/restore verds. El `result.json` queda immutable `failed` perquè el
    perfil antic esperava erròniament ordre centre-alternat; no hi va haver
    Busy, -110, timeout, dèficit ni trigger ambigu i no s'ha fet replay;
  - evidència EXIF del run: ordre real repetit -6,-3,0,+3,+6 i obturacions
    1/2000,1/250,1/30,1/4,2 s. Reavaluació offline contra el contracte
    corregit dona bias/shutter/physical-EV verds, desviació màxima 0,058894 EV
    sota tolerància 0,35 EV;
  - corregits exclusivament el generador i els nou labs A7III de brackets a
    l'ordre fosc-a-clar ja declarat pel candidat viu; afegit gate manual
    `Bracket Order = - -> 0 -> +`. Generador `--check`, 6/6 tests focals i
    validate+dry-run amb controlador viu 12/12 verds;
  - hard stop respectat durant diagnòstic/correcció offline. Es reprendrà només
    amb un gate no executat; el run 15/15 fallit no es reescriu ni es repeteix.
- a7m3_post_iso_override_resume_2026_08_01_160029Z:
  - `SERIAL_WRITES` rebut RELEASED del task ISO a 15:58:48Z i adquirit després
    d'un checkpoint independent OS-level buit;
  - controlador congelat SHA-256
    `9d6b23d465a332931505999328e623af815cf2c39dd13bb93bc9c288f1d443cd`;
  - política de Pere: baseline ISO 100, cap write ISO, canvis manuals sempre
    advisory i MISSION FIRST. No es demanarà cap intervenció entre gates verds;
  - el task Canon6D i els seus 34 errors/quarantenes queden explícitament fora
    d'abast i no rebran missatges ni canvis des d'aquesta campanya.
- iso_mission_first_override_release_2026_08_01_155848Z:
  - regressió focal ISO verda 13/13 per `100`, `200`, `800`, `Auto`,
    `Auto ISO`, `0` i `Unknown value 0000`: preflight continua, reconnect
    continua, la timeline dispara exactament un cop i `main` persisteix exit 0;
  - regressions relacionades verdes 97/97; controlador fora dels tres mòduls
    Canon quarantinats 656/656; GUI completa 285/285; `py_compile`, tres JSON,
    generador curt `--check` i `git diff --check` verds;
  - la descoberta completa del controlador executa 704 proves i conserva 34
    errors Canon separats: 24 són el fail-closed esperat del bundle v2 lligat
    als SHA antics, i 10 són fixtures del planificador/compilador Canon encara
    incompatibles amb sis arguments nous. No s'han maquillat ni corregit dins
    l'override ISO;
  - SHA-256 final del controlador:
    `9d6b23d465a332931505999328e623af815cf2c39dd13bb93bc9c288f1d443cd`;
    perfil Canon actiu:
    `13b8fea1f0abd980e145a7f395152834f1927f8de4be7339ff2500996679f37c`;
    perfil A7III:
    `f66b01b2d551d120af2d6fb4cbadad8247e1aa0b099380dc0cf04749d69264fc`;
    perfil A7RIIIA:
    `fd2f4ec7e5c6a8f65b0508e2b6b5b4c3b90ffb0e433dd204a55b1620bd1bf004`;
  - handoff Canon: reprendre només després d'adquirir SERIAL_WRITES, afegir el
    contracte separat `allowed_initial_values` i generar un ID nou inequívoc
    (`v3` o post-override); no sobreescriure v1/v2;
  - comprovació OS final buida: zero Eclipse Command, `eclipse_capture.py`,
    gphoto2, mission/worker host o reconciliació. `gui/dist/Eclipse Command.app`
    no s'ha reconstruït perquè aquesta unitat tenia cap GUI/LaunchServices.
- urgent_iso_mission_first_handoff_2026_08_01_154518Z:
  - autoritat nova de Pere: CAP valor ISO ha de provocar `FAILED`; és una
    regla global MISSION FIRST. El hard-fail per Auto/0/Unknown i
    `OperatorIsoPolicyError` és incorrecte i s'ha de retirar;
  - treball aturat en checkpoint segur abans de cap PTP, captura, GUI,
    LaunchServices o publicació;
  - el bundle
    `controller/runs/codex_20260801_canon6d_optimization/profiles/canon6d_cold_start_preflight_bundle_v2/`
    sí que s'havia materialitzat a `2026-08-01T15:42:38.849903Z`, lligat al
    controlador SHA `6088684dad3ee9050120171d3e4d0ac1eba81149f3246b4b4e9fed9746fc37fb`
    i al perfil Canon SHA
    `104a8225c5cde74f1e5f7084d403685296cd534629d0a6ddcbef2363b7e97d97`;
    queda QUARANTINAT, no publicable i sense cap execució física;
  - també queda quarantinat el perfil generat
    `controller/runs/codex_20260801_canon6d_optimization/profiles/canon6d_preconfigured_v2/canon6d_lab_aeb_continuous_p3_g1_cadence3_0_hold1_0_preconfigured_v2.json`;
  - fitxers tocats durant aquesta unitat abans de l'override:
    `controller/tools/build_canon6d_cold_start_preflight_bundle.py`,
    `controller/tools/build_canon6d_lab_profile.py`,
    `controller/tools/plan_canon6d_c3_buffer_peak.py`,
    `controller/tools/CANON6D_COLD_START_PREFLIGHT_BUNDLE.md`,
    `controller/tests/test_build_canon6d_cold_start_preflight_bundle.py`,
    `controller/tests/test_build_canon6d_lab_profile.py` i
    `research/45_CANON_6D_AUDITORIA_OPTIMITZACIO_HARD_STOP_2026-08-01.md`;
  - no hi ha regressió post-override ni SHA nou vàlid. Qualsevol resultat verd
    anterior pertany a la política ISO revocada i no autoritza publicar v2;
  - següent pas: el task origen adquireix SERIAL_WRITES, corregeix controlador,
    proves i docs, i només després regenera v2 sota un identificador/manifest
    inequívoc amb els SHA nous.
- iso100_operator_policy_handoff_2026_08_01_153823Z:
  - tres perfils operatius (`mission.enabled=true`) exigeixen ISO 100 manual
    a l'arrencada, declaren l'opció 100 i contenen zero writes ISO a
    `auto_configure`, `configure` o timeline; Auto ISO queda prohibit;
  - després del gate, qualsevol ISO manual numèrica positiva és
    operator-owned, també entre C2 i C3: cap setter, restore, avís o fallada
    postflight per divergència; l'EXIF real continua auditat;
  - ISO 0/Unknown transitori pot estabilitzar-se a una ISO numèrica; si
    persisteix, o una reconnexió observa Auto ISO/0/Unknown, talla abans del
    trigger amb `OperatorIsoPolicyError`, estat terminal `failed` i codi no
    zero fins i tot sota `mission-first`;
  - l'A7RIIIA operativa passa de 400 a 100 sense multiplicar silenciosament
    les obturacions per quatre: perd 2 EV nominals i conserva obert el gate
    fotomètric/solar; tots els perfils lab/històrics retenen ISO exacta;
  - fitxers ISO tocats: `controller/eclipse_capture.py`, els tres perfils
    operatius, `controller/tools/build_short_profiles.py`, proves focals del
    controlador/GUI, `gui/eclipse_command/camera_settings.py`, documentació
    viva, checklist A7III i `research/46_POLITICA_ISO100_OPERADOR_2026-08-01.md`;
  - regressions offline verdes: política ISO 18/18, perfils curts 26/26,
    adaptatius 30/30, camera settings 5/5, controlador complet 703/703 i GUI
    completa 285/285; `py_compile`, generador `--check` i `git diff --check`
    verds;
  - SHA-256 finals: controlador
    `6088684dad3ee9050120171d3e4d0ac1eba81149f3246b4b4e9fed9746fc37fb`;
    perfil Canon actiu
    `104a8225c5cde74f1e5f7084d403685296cd534629d0a6ddcbef2363b7e97d97`;
    perfil A7III
    `f37b725881d95528a88a5c42729ca4c14a5f5cb336678086340897058836209f`;
    perfil A7RIIIA
    `96ea43331c0db09f8d57d286057740372509ba7e22b1ec4be097e37f1d0907e3`;
  - el bundle immutable Canon cold-start v1 no s'ha editat, però els dos SHA
    que lliga han canviat: queda invàlid i el task Canon ha de generar v2;
  - cap maquinari, PTP, gphoto2, captura, GUI interactiva ni LaunchServices;
    comprovació OS-level final buida de GUI, gphoto2, controlador, hosts,
    workers i reconciliació. El bundle `gui/dist/Eclipse Command.app` no s'ha
    reconstruït i queda stale fins a autorització concreta de rebuild;
  - pendent físic separat: demostrar a cada cos que canviar ISO manualment amb
    la sessió PTP oberta no bloqueja ni pausa el canal. Cap test offline ho
    qualifica.
- a7m3_resume_iso100_2026_08_01_145915Z:
  - Pere confirma SD acabada de formatar i bateria correcta; el gate manual
    d'espai queda satisfet per declaració de l'operador;
  - Pere fixa ISO 100 com a base immutable i es reserva personalment qualsevol
    canvi futur per meteorologia. Aquesta campanya no pot escriure ISO;
  - auditoria offline: 12/12 perfils exigeixen `/main/imgsettings/iso=100` i
    contenen zero accions de write sobre ISO;
  - handoff logo RELEASED a 14:58:15Z i comprovació independent OS-level buida
    abans d'adquirir: zero gphoto2, controlador, GUI, host, worker o reconciliació;
  - reprendre sense checkpoints evitables entre gates verds i aturar al primer
    hard stop, sense replay.
- a7m3_external_gui_reaper_hard_stop_2026_08_01_150617Z:
  - preflight estricte post-format verd a
    `controller/runs/20260801T170009_candidate_a7m3_ap130_short_checkpointed_1x5_3x9_preflight/`:
    A7III exacta, bateria 100 %, ISO 100, Single, 1/8000, `card+sdram`, cua 0,
    zero warnings, writes, triggers o captures;
  - un primer intent del gate Single ha estat rebutjat abans de lock o càmera
    perquè `--qualification-run` exigeix C2/C3 fins i tot en perfils relatius;
    no és evidència física ni replay;
  - únic gate físic iniciat: `lab_a7m3_ap130_dense_single_1250ms`, SHA-256
    `028995375438e796606b001c6a1f5524c71412a04828adc6841475efc1d88957`,
    a `controller/runs/20260801T170203_lab_a7m3_ap130_dense_single_1250ms_run/`;
  - el write únic `1/8000 -> 1/30` es va comprometre a 15:02:08.597Z; abans
    de cap trigger, el pseudo-terminal gphoto2 fou acabat amb codi -9. Hard
    stop immediat: ledger 0, zero captures, zero retry/recovery/replay;
  - restore i emergency drain no es pogueren executar en aquella sessió;
    l'estat de shutter fou declarat desconegut i el lock es va alliberar;
  - interferència externa demostrada: `Eclipse Command` PID 65866, iniciat a
    15:00:53Z després del handoff logo, executava preflights A7III/Canon cada
    minut. El seu reaper envia SIGTERM i després SIGKILL als gphoto2 externs
    que no figuren com a missió pròpia; és coherent amb el codi -9 observat;
  - l'artefacte GUI posterior de 15:03:02Z va llegir shutter 1/30 i el seu
    auto-configure el va restaurar a 1/8000 amb ACK de 4,018 s i readback verd;
    ISO va romandre 100. Un altre preflight a 15:04:08Z confirma 1/8000,
    ISO 100, Single, cua 0, bateria 100 %, cleanup verd i zero captures;
  - PID 65866 tancat graciosament per seguretat; checkpoint final després de
    més d'un cicle: zero GUI, gphoto2, host, worker, controlador o reconciliació
    i cap run nou després de 15:04:10Z;
  - el gate Single no queda qualificat. No reprendre cap gate físic sense una
    nova autorització explícita de Pere després d'aquest hard stop. Abans de
    reprendre, exigir GUI absent de manera estable i resoldre el forat pel qual
    el reaper no reconeix controladors externs legítims.
- handoff_logo_photo_2026_08_01_145815Z:
  - logo vectorial anterior preservat byte a byte a
    `gui/docs/branding/eclipse-command-script-backup-2026-08-01.svg`,
    SHA-256 `8a3fad2f89d0d7ecaa88db65b444f8b78f26e085e806121928258aa4d702ef73`;
  - `Logo.jpg` s'ha usat només com a font; crop central 1024x1024 reencodat
    sense metadades Sony/Lightroom i incrustat dins l'SVG canònic, SHA-256
    font/bundle `50ee8dc6eda32a304c4ce077c6122f7f84f276630fa982eb105a117f6e063e8b`;
  - XML verd i renders amb alpha 16/32/128/1024 inspeccionats; la corona i el
    diamant continuen recognoscibles a 16x16;
  - regressions focals `test_macos_packaging` + `test_runtime_manifest`:
    14/14 verdes;
  - build portable 0.6.6 verd; bundle anterior preservat com
    `gui/dist/Eclipse Command.app.previous-20260801T145717Z-62729`;
    ICNS nou SHA-256
    `a64c27fc1e7838fed19df4e5523ba1b5d790568e07f0710fe2b452b419d19756`;
  - QA portable complet verd: manifest/signatura, relocació, 97 Mach-O,
    macOS 26.0, perfils, controlador, worker, missió de tres canals i GUI
    offscreen amb `gphoto2` fals;
  - cap GUI interactiva oberta, PTP, gphoto2, càmera o captura; checkpoint
    OS-level final sense processos. SERIAL_WRITES queda alliberat perquè
    l'A7III reprengui amb prioritat.
- a7m3_manual_sd_checkpoint_2026_08_01_145318Z:
  - preflight físic estricte de només lectura verd, sense `mission-first`,
    `apply-safe-config`, trigger ni write: identitat exacta ILCE-7M3, sèrie
    PTP `[SÈRIE]`, USB `[SÈRIE]`, firmware 4.0,
    bateria 100 %, M/MF/ISO 100/1/8000/Single, RAW+JPEG Std, DRO/crop Off,
    `card+sdram` i cua zero;
  - evidència a
    `/Users/USUARI/Downloads/Eclipse 2026/controller/runs/20260801T164120_candidate_a7m3_ap130_short_checkpointed_1x5_3x9_preflight/`;
    ledger zero, cleanup/release verds i estat físic conegut;
  - probe de capacitat PTP també estrictament de només lectura: `storage-info`
    retorna el resum buit i no exposa bytes lliures, capacitat ni imatges
    disponibles; zero writes/captures. Evidència a
    `/Users/USUARI/.codex/worktrees/3a5f/Eclipse 2026/controller/runs/20260801T144330_candidate_a7m3_ap130_short_checkpointed_1x5_3x9_storage-info/`;
  - dependència manual única abans del primer trigger: confirmar almenys
    10 GiB lliures a la SD per Mass Storage. No se substitueix per cap valor
    PTP desconegut o estimació;
  - lot offline immutable preparat: 3 escales Single (20 a 1,250/1,125/1,000
    s), 5 esglaons fixos 5x3 (1..5 brackets a 10,2 s) i 4 esglaons fixos 9x1
    (1..4 brackets a 8,2 s); són hipòtesis A7III no qualificades, amb setters
    explícits, `max_attempts=1`, zero recovery/replay i hard stop al primer
    error;
  - 12/12 perfils validen, 12/12 dry-runs verds, prova focal 5/5 i regressió
    completa del controlador 668/668. El generador és
    `controller/tools/build_a7m3_c2c3_gate_profiles.py`, SHA-256
    `4a49c10213067c58f848c32a37c2607643f06a9a65de3d713640bc8df11cb20a`;
  - checkpoint OS-level final buit: zero gphoto2, controlador, Eclipse Command,
    mission/worker/camera worker o reconciliació. Cap captura física executada;
  - SERIAL_WRITES cedit temporalment al task logo. L'A7III el pot reacquirir
    amb prioritat després del handoff final del logo i la confirmació manual
    dels 10 GiB, sense repetir checkpoints evitables entre gates verds.
- handoff_logo_2026_08_01_143834Z:
  - GUI externa identificada exactament com
    `gui/dist/Eclipse Command.app/Contents/MacOS/Eclipse Command` i tancada
    graciosament pel task del logo; verificació OS final sense GUI,
    mission_host, worker_host, camera_worker, controlador ni gphoto2;
  - preflights GUI auditats: quatre Canon i un A7III entre 14:33Z i 14:36Z,
    tots amb zero trigger, captura, commit i write; cleanup verd i estat físic
    conegut. Canon continua AEB +/-3, 1/250, Drive Single, mirror 0 i review
    None; els seus preflights són WARNING per divergència respecte del perfil
    històric bloquejat;
  - cap reconciliació o operació física en curs; generador cold-start pausat
    en un checkpoint offline abans del handoff;
  - no iniciar cap PTP ni cap nou stage Canon fins que el task del logo
    publiqui l'alliberament explícit de SERIAL_WRITES.
- handoff_paypal_build_2026_08_01_143111Z:
  - preflight i escaneig final OS-level: zero GUI, mission host, worker,
    controlador o gphoto2; `gui.pid` i `.portable-build.pid` absents;
  - regressions prèvies verdes: GUI 285/285 i controlador 663/663;
  - build canònic complet i LaunchServices refrescat; versió 0.6.6/0.6.6,
    executable SHA-256
    `6168e6cd9724ad061136bf1fcdf3fc2ebbc5d2fb5fd4d68520c380dceca07f21`
    i CDHash `5d29bffca0a5e69cff9a0dcd87f219eaa1680b5a`;
  - bundle anterior preservat com
    `gui/dist/Eclipse Command.app.previous-20260801T142819Z-39433`;
  - manifest de 33 entrades exacte; `main_window.py` font/manifest SHA-256
    `4dee1263f626e1114b2a49e67c9c843c828741729b0426db29af2548af7c94bd`
    i URL PayPal viva present;
  - QA portable verd: signatura, relocació, 97 Mach-O, macOS 26.0, tots els
    perfils, controlador, worker, missió de tres canals i GUI offscreen;
  - alerta de drift auditada: el generador cold-start Canon nou no entra al
    bundle; spec i manifests allowlisten únicament `inspect_arw.py`;
  - rebut complet a `gui/QA_REPORT_0.6.6_PAYPAL_2026-08-01.md`;
  - cap pàgina PayPal o GUI interactiva oberta, cap pagament, PTP, captura o
    operació física; el paquet continua ad-hoc i no notaritzat.
- next_owner: lliure; el task Canon pot reprendre només després de rellegir
  aquest RELEASED i adquirir formalment `SERIAL_WRITES`.
- canon6d_aeb_off_busy_hard_stop_2026_08_01_142159Z:
  - autorització continuada de Pere registrada; no es demanaran checkpoints
    entre gates verds, però no elimina hard stops ni permet replay;
  - únic stage executat: perfil immutable
    `canon6d_lab_drive_stage_01_aeb_off_v1`, SHA-256
    `721105759d922c9f4d02c48cc7a32e871ae8aa2b69c826120c7a0779a53a5b23`;
  - auto-detect únic `Canon EOS 6D` a `usb:001,001`; model i sèrie PTP exactes,
    bateria 50 %, Manual/MF/RAW/ISO100/Memory card, 1/250, Drive Single,
    AEB +/-3, review None i mirror 0;
  - l'únic write `set-config-index /main/capturesettings/aeb=0` ha rebut
    `PTP Device Busy 0x2019` i `-110` al primer intent, 9,532 ms després;
  - zero trigger, captura, retry, recovery, restore o stage posterior;
    `capture_may_have_started=false`, estat físic declarat conegut, cleanup i
    lock verds i cap procés gphoto2/controlador/GUI/worker viu;
  - evidència a
    `controller/runs/codex_20260801_canon6d_optimization/20260801T162039_canon6d_lab_drive_stage_01_aeb_off_v1_preflight/`;
  - inferència de treball: després dels RAW, el firmware rebutja tant Drive com
    AEB encara en idle; preparar offline un cold-start que fixi shutter,
    Continuous i AEB abans del primer RAW. No executar cap altre PTP fins a
    resoldre la dependència física d'un power-cycle/estat inicial AEB off.
- handoff_paypal_2026_08_01:
  - URL pública fixada literalment a
    `https://www.paypal.com/donate/?hosted_button_id=84YSCU3C44SDQ`;
    sintaxi verificada offline: HTTPS, host exacte `www.paypal.com`, path
    `/donate/` i un únic `hosted_button_id` alfanumèric;
  - el botó obre exactament aquest QUrl amb `QDesktopServices`; tooltip i
    README vius ja no el descriuen com a placeholder;
  - dues proves focals verdes: obertura exacta i warning si el sistema rebutja
    l'URL; regressió GUI completa 285/285 verda i `git diff --check` verd a
    les tres rutes tocades;
  - no s'ha obert el navegador ni s'ha executat cap pagament; receptor,
    divisa i pàgina final no s'han confirmat en viu;
  - paquet actiu NO reconstruït: el manifest 0.6.6 ja difereix de quatre
    inputs vius (`controller/eclipse_capture.py`, perfil Canon,
    `camera_settings.py` i `main_window.py`) i el builder activa tots quatre;
  - `build_macos_portable_app.sh` executa obligatòriament `lsregister -f`
    durant activació i rollback. Cal autorització concreta de Pere per al
    rebuild/LaunchServices i un preflight de processos fora del sandbox;
    fins llavors, la font és correcta però l'app actual conserva el botó vell.
- next_owner: lliure; Canon requereix un cold-start físic abans de reprendre
  PTP. El rebuild/QA PayPal continua separat i requereix autorització concreta
  de LaunchServices.
- previous_task_released_utc: 2026-08-01T13:39:25Z; la campanya Canon queda
  tancada al hard stop anterior i no es reprèn en aquesta tasca.
- canon6d_offline_drive_and_c3_ready_2026_08_01_141129Z:
  - cap PTP, gphoto2, GUI, captura ni ordre física després del hard stop de
    13:39:25Z; `SERIAL_WRITES` continua RELEASED i no s'ha alterat el handoff
    PayPal més recent;
  - contracte `lab_execution_contract.preflight_only=true`: exigeix perfil lab
    candidat, missió desactivada, `configure=[]` i `sequence.actions=[]`; `run`
    i `drain` fallen abans de crear artefactes o obrir PTP;
  - bundle immutable de tres stages materialitzat sota
    `controller/runs/codex_20260801_canon6d_optimization/profiles/canon6d_drive_transition_preflight_bundle_v1/`:
    AEB off, Drive Continuous i AEB +/-3; un setter per stage,
    `max_attempts=1`, `busy_retries=0`, zero captures/timeline/restore;
  - manifest del bundle verificat, SHA-256
    `1c4c1659bc4be5d02e813729b6818bf90aff2ab2656b429f939c48b4085773cc`;
    guard interstage 7,0 s explícitament lab-only i no Q-qualificat;
  - planner/compiler C3 no circular: Stage A només declara
    `G_TRIAL_NOT_G_OK_TAIL`; el certificador revalida pla, perfil, run i
    card-gate; Stage B exigeix aquella evidència semànticament verda i lliga
    ISO, mirror, review, modes, storage ID i identitat SD;
  - no s'ha creat cap Stage B real: Continuous, offsets, identitat SD i
    `G_ok_tail` same-history continuen sense evidència física;
  - regressió offline final verda: controlador 663/663, conjunt Canon dirigit
    79/79, `py_compile`, verificació immutable del bundle i `git diff --check`;
    la GUI no s'ha executat.
- canon6d_drive_busy_hard_stop_2026_08_01_133925Z:
  - perfil Continuous d'un bracket validat offline, SHA-256
    `4f746329f0c29b25d617d5a76a04034fc8723d98e8a5c02cdfa06f5faba7cf7f`;
    menú PTP limitat a base `1/250` i ordre CR2 esperat complet preservat;
  - preflight físic exacte: identitat verda, bateria 50%, fase AEB zero
    (`Current=1/250`), AEB +/-3, Single, M/MF/RAW/ISO100/Memory card,
    review None i mirror 0;
  - shutter i AEB ja coincidien i han fet zero writes; l'únic write intentat,
    `Drive Single -> Continuous`, ha estat rebutjat al primer intent amb
    `PTP Device Busy 0x2019` i `-110`;
  - zero trigger, zero captura, zero retry, recovery o replay; Drive continua
    `Single`, cap estat físic ambigu, cleanup/lock verds i cap procés viu;
  - hard stop aplicat abans del run Continuous; no queda qualificat Continuous,
    buffer, `G_ok_tail`, cadència ni pic post-C3;
  - treball següent només offline: gate transitori sense captures que apagui
    AEB abans de canviar Drive i el torni a activar, amb readbacks, zero retries,
    zero restore i aturada al primer error.
- canon6d_aeb_phase_zero_green_2026_08_01_133326Z:
  - el preflight v1 ha fallat només en lectura i abans de cap mutació/captura:
    amb AEB actiu la 6D exposa per PTP únicament la fase actual, `1/30`;
    cleanup verd i zero trigger;
  - perfil v2 immutable lligat al gate AEB Single, SHA-256
    `5199b8073a1b4ba554e2e6d4f521b635087dc2d6e2e070aa9756f821d3843937`,
    preflight exacte `Current=1/30`, una sola pressió i zero setters;
  - run físic v2 verd: 1/1 press+release, zero Busy, retry, recovery, warning o
    replay; cleanup i release verds;
  - delta SD exclusiu `IMG_2310.CR2`, 19.155.250 bytes, hash únic, cos/ISO
    exactes, 1/30 i payload RAW íntegre; tercera lectura estable;
  - gate de continuïtat verd: `tail 2 -> 0`, sufix exacte `1/30` i
    `phase_zero_verified=true`;
  - següent gate: Continuous d'un sol bracket, amb el menú PTP Canon restringit
    al shutter base i l'ordre físic complet verificat exclusivament als CR2.
- canon6d_aeb_single_green_2026_08_01_131918Z:
  - preflight posterior al power-cycle verd: identitat exacta a `usb:001,001`,
    bateria 50%, 1/250 i AEB +/-3 convergits al primer intent, Single, M/MF,
    RAW, ISO 100, Memory card, review None i mirror 0;
  - `IMG_2301.CR2`, creat abans del preflight, inspeccionat només en lectura i
    etiquetat `UNATTRIBUTED_PREEXISTING_CR2`; cos/ISO/1/4000/CR2 íntegres;
  - AEB Single físic complet: 8/8 press+release i ledger 8, zero Busy, setter,
    retry, recovery, warning o replay;
  - delta SD exclusiu `IMG_2302.CR2`–`IMG_2309.CR2`, 153.292.134 bytes, 8
    hashes únics, cos exacte, ISO 100, payloads RAW íntegres i tercera lectura
    estable;
  - descoberta AEB verda: `p=3`, ordre físic
    `1/250 -> 1/2000 -> 1/30`, dues voltes completes i `tail=2`; EXIF bias 0
    en les tres posicions;
  - següent gate: exactament una pressió Single esperada a 1/30, lligada al
    gate de descoberta, per demostrar fase zero abans de Continuous.
- canon6d_powercycle_unattended_resume_2026_08_01_131236Z:
  - Pere declara que ha apagat i tornat a encendre la Canon perquè semblava
    bloquejada, i autoritza continuar desatesament i provar tots els gates;
  - nova campanya: no repetir el setter v3; configurar shutter/AEB/Drive només
    abans del primer RAW i després usar exclusivament press/release;
  - Claude RELEASED, els quatre PIDs dels locks són morts i una enumeració de
    processos no troba gphoto2, controlador, GUI, camera_worker o mission_host;
  - primer AEB Single card-only; si és verd, normalització de fase, Continuous,
    escala de grups, `G_ok_tail`, offsets i pic post-C3;
  - continuació automàtica entre gates verds; hard stop al primer Busy, retry,
    warning, trigger ambigu, delta divergent o CR2 invàlid.
- canon6d_post_stop_offline_audit_2026_08_01_130636Z:
  - documentació viva i blocker del perfil corregits: 7,012 s amb
    `Image review=None` és físicament vermell i no s'ha de repetir ni ampliar
    per intuïció;
  - AEB Single exploratori fa vuit presses i pot deixar `tail != 0` per
    `p=3/5/7`; queda prohibit passar directament a Continuous sense demostrar
    la normalització de fase amb inventari SD immutable;
  - el planificador de pic C3 només produeix àlgebra/JSON, no un perfil
    executable; falten calibratge absolut press monotònic->EXIF i
    `G_ok_tail` amb la mateixa història prèvia C2-C3;
  - regressió offline final del controlador: 613/613 verda;
  - tot aquest bloc és auditoria offline: zero PTP, captures, GUI o maquinari;
    `SERIAL_WRITES` continua RELEASED.
- canon6d_v3_device_busy_hard_stop_2026_08_01_130023Z:
  - nova autorització de Pere aplicada; exclusivitat i preflight v3 verds amb
    `reviewtime=None`, mirror 0, Single, AEB off, M/MF/RAW/ISO 100/Memory card,
    1/4000, identitats exactes i zero warnings;
  - manifest previ estable de cinc CR2, `IMG_2295.CR2` a `IMG_2299.CR2`;
  - un únic press/release ACK ha compromès una imatge; el setter únic
    `1/4000 -> 1/2500` s'ha enviat aproximadament 7,012 s després del release
    i ha rebut `PTP Device Busy 0x2019` al primer intent;
  - zero Busy retries, recovery, reconnexió o replay; cleanup verd, release
    confirmat, estat físic resolt a 1/4000 i cap procés de càmera viu;
  - `IMG_2300.CR2` reconciliat: delta 1/ledger 1, 19.174.667 bytes, SHA-256
    `1da746dc2b5a03d790aa801441d24b14c1bc6debb4fee3a18427c9bc8cc94980`,
    EXIF 12:58:37.74, 1/4000, ISO 100, cos [SÈRIE] i RAW íntegre;
  - el gate és només `capture_reconciliation_only`; el run font continua KO i
    7,012 s amb `Image review=None` queda físicament vermell;
  - AEB Single, Continuous, buffer, cadència i pic C3 no s'han executat ni
    qualificat; la campanya s'ha aturat al primer error tal com exigeix el
    contracte viu.
- canon6d_v3_unattended_resume_2026_08_01_125734Z:
  - Pere autoritza explícitament reprendre i continuar desatesament després
    del hard stop anterior;
  - exclusivitat verificada: Claude RELEASED i cap procés gphoto2,
    controlador, GUI, mission host o worker viu;
  - primer gate: preflight estricte, snapshot, un únic RAW i setter v3 a
    7,12 s de target estàtic, seguit de card gate complet;
  - només si és verd: AEB Single, AEB Continuous, ladder de grups complets,
    offsets/drenatge i planificació del pic post-C3;
  - autorització limitada a Canon 6D fosca/card-only i gates del pla viu;
    zero GUI, Sony, delete/format, replay o retry ambigu; hard stop al primer
    error, Busy, identitat divergent, dèficit o CR2 invàlid.
- canon6d_scheduler_readiness_hard_stop_2026_08_01_123737Z:
  - preflight físic estricte verd amb `reviewtime=None`, mirror lock 0,
    Single, AEB off, RAW, M/MF, ISO 100 i identitats exactes;
  - `IMG_2298.CR2` s'ha inspeccionat només en lectura i queda etiquetat
    `UNATTRIBUTED_PREEXISTING_CR2`: EXIF 12:25:47, anterior al preflight,
    integritat CR2 verda, cap ledger atribuït i inventari SD estable;
  - el run quiet ha fet exactament un press/release ACK i ha compromès una
    imatge; cap setter d'obturació no ha arribat a PTP;
  - hard stop: el scheduler ha rebutjat `quiet_set_shutter` perquè el target
    fix a 6,32 s precedia el readiness real ancorat al release en aproximadament
    0,333 s; zero `0x2019`, zero Busy retry, recovery, reconnexió o replay;
  - `IMG_2299.CR2` reconciliat: delta 1/ledger 1, 19.163.801 bytes, SHA-256
    `abbc39af84f261f4566e5708ad8095193b652148d3afb9efa1c653a4d5dbe56f`,
    EXIF 12:34:45.41, 1/4000, ISO 100, cos [SÈRIE] i RAW íntegre;
  - el gate és només `capture_reconciliation_only`; el run font continua KO i
    no qualifica el quiet gap, AEB, Continuous, buffer, cadència ni pic C3;
  - cap procés gphoto2/controlador/GUI/worker viu en alliberar SERIAL_WRITES;
    la campanya física queda aturada i la correcció continua només offline.
  - causa offline corregida: el setter quiet/buffer diagnòstic ara es programa
    després de `worst_case_s + quiet_gap_s`, no `hold_s + quiet_gap_s`;
  - perfil immutable següent, no executat:
    `canon6d_lab_quiet_gap6_2_review_required_v3.json`, setter a 7,12 s,
    SHA-256
    `aa3477ddc04e4b4f7d7f358b01d55bd74436418f5817842ef16f6213ddaccdf5`;
  - validate i dry-run offline verds; regressió controlador 613/613;
  - `SERIAL_WRITES` continua RELEASED i no es farà cap gate v3 sense nova
    autorització posterior al hard stop.
- canon6d_manual_review_off_resume_2026_08_01_122813Z:
  - Pere confirma `fet` en resposta al canvi manual Image review Off i a la
    continuació desatesa;
  - exclusivitat verificada: Claude RELEASED i cap procés gphoto2,
    controlador, GUI, mission host o worker viu;
  - primer gate: preflight estricte en lectura de `reviewtime=None`; després
    un únic RAW->setter amb zero retries i card gate complet;
  - si és verd, AEB Single, Continuous, buffer ladder, offsets i pic C3;
  - hard stop al primer Busy, identitat divergent, trigger ambigu, dèficit o
    CR2 invàlid; zero replay, delete/format, GUI, Sony o prova solar.
- canon6d_offline_hardening_2026_08_01_114007Z:
  - el camí físic `Press Full MF`/`Release Full` força zero Busy retries encara
    que Canon l'expressi com a `set-config`; queda tancat el possible replay
    heretat del retry genèric;
  - els perfils lab paren una fallada de captura abans de recovery de transport
    o retry precommit;
  - AEB Single, AEB Continuous i buffer fix convergeixen obturació/AEB/Drive al
    preflight persistent amb `remember=False`, `configure=[]` i cap restore
    post-RAW;
  - contracte `no_post_capture_config_writes` validat i auditor card-only que
    rebutja setters, restore o retry després del primer press;
  - planificador offline del pic C3 afegit: usa `p`, `P`, `u[j]`, `u_end` i
    `G_ok` físicament mesurats; només declara `PEAK_ENVELOPE_SCHEDULED` i
    `PEAK_ENVELOPE_CONFIRMED`, mai `BUFFER_FULL`;
  - perfil següent ja materialitzat però no executat:
    `canon6d_lab_aeb_single_base1_250_v1.json`, base 1/250, ±3 EV, vuit
    presses Single, SHA-256
    `dbf8c52fca70b7c2cfc9bafbaa4e650a7bd7b2bfdfa7cd742f919939869a036c`;
  - regressió final verda: controlador 610/610 i GUI offscreen 284/284;
  - tot aquest bloc és evidència offline; AEB, Continuous, buffer, cadència i
    pic C3 continuen sense qualificació física.
- canon6d_reviewtime_hard_stop_2026_08_01_112430Z:
  - el CR2 pendent s'ha reconciliat abans de mutar: `IMG_2297.CR2`, delta
    1/ledger 1, CR2 íntegre i correlacionat; el gate només lectura és verd;
  - identitat exacta i estat preflight verd excepte `reviewtime=Hold`;
  - una única ordre `set-config-index /main/settings/reviewtime=0` ha intentat
    `Hold -> None` en repòs i ha rebut `PTP Device Busy 0x2019`;
  - zero trigger, zero captura nova, zero retry, zero recovery i cleanup verd;
  - hard stop aplicat i `SERIAL_WRITES` alliberat immediatament;
  - dependència física demostrada: Pere ha de posar Image review/Revisió
    d'imatge a Off al cos. No es pot automatitzar per PTP en aquest estat;
  - la feina continua només offline: perfils AEB fixos sense setters post-RAW,
    ladder de grups complets i planificador del pic post-C3.
- canon6d_unattended_resume_2026_08_01:
  - autorització explícita nova de Pere per continuar desatesament i optimitzar
    cada dècima, amb objectiu de pic de buffer immediatament després de C3;
  - primer reconciliar sense trigger el CR2 pendent; després una única escriptura
    verificada `reviewtime=None` abans de capturar i gate causal RAW->setter;
  - si queda verd: AEB Single, AEB Continuous, escala incremental del buffer,
    mesura de cadència/drenatge i coreografia fosca C2-C3;
  - cap checkpoint humà entre gates verds; es mantenen hard stops automàtics per
    identitat divergent, Busy, trigger ambigu, dèficit o CR2 invàlid;
  - zero replay, zero delete/format, cap GUI, cap Sony i cap prova solar.
- canon6d_resume_scope:
  - només Canon EOS 6D amb model/sèrie PTP exactes;
  - màxim tres hores i només gates físics enumerats al task viu;
  - cap GUI, cap Sony, cap prova solar, cap canvi manual, cap delete/format;
  - primer tancar sense trigger el delta CR2 pendent; després preflight,
    setter idle, quiet ladder, AEB Single/Continuous, buffer i coreografia;
  - zero retries als writes Canon de qualificació, sense recovery/replay i
    hard stop al primer Busy, identitat divergent, dèficit, CR2 invàlid o
    trigger ambigu.
- canon6d_hard_stop_2026_08_01_110234Z:
  - el CR2 orfe anterior `IMG_2296.CR2` s'ha tancat abans del run: delta
    1/ledger 1, 19.144.464 bytes, SHA-256
    `f051ac76a12c557b462fab3555a846297ea2e06ad8fee2b2e2f2007ed4e51067`,
    CR2 2.0, cos `[SÈRIE]`, RAW 5568x3708, ISO 100 i 1/4000;
  - preflight viu verd: Canon/sèrie exactes, bateria 100%, M, MF, RAW,
    ISO 100, Memory card, 1/4000, Single, AEB off, mirror lock 0;
  - setter-idle verd: 1/4000 -> 1/2500 -> 1/4000, dos ACK/readback al primer
    intent, zero captures, zero Busy/recovery i inventari SD immutable;
  - hard stop físic: un RAW a 1/4000 amb press/release ACK i ledger 1; el
    setter únic a 1/2500, 20,120 s nominals després del press i aproximadament
    20 s després del release, rep `PTP Device Busy 0x2019` al primer intent;
  - zero Busy retries, zero recovery, zero replay i cap altra ordre física;
    cleanup verd, estat físic resolt per readback a 1/4000 després del guard
    de 50 s; el nou CR2 probable queda a la SD sense reconciliar;
  - AEB, Continuous, buffer, Q[g] i coreografia C2-C3 continuen sense
    qualificació i no s'han executat.
  - el bolcat complet anterior als dos Busy llegia
    `/main/settings/reviewtime = Hold` i `/main/settings/autopoweroff = 0`;
    segons el manual Canon, Hold manté la imatge fins a l'autoapagada. És una
    hipòtesi causal forta, no una qualificació física.
  - el perfil de missió, el generador lab i la font GUI ara exigeixen Image
    review Off/`None` abans de qualsevol captura; el bundle no s'ha reconstruït.
  - següent gate, només amb nova autorització de Pere: reconciliar sense trigger
    el CR2 nou, canvi manual a Image review Off, preflight estricte i una sola
    transició RAW->setter amb zero retries. Fins llavors, cap PTP/run Canon.
  - regressió offline posterior verda: controlador 597/597 i GUI 284/284;
    la GUI només s'ha provat offscreen, no s'ha obert l'aplicació.
- previous_a7r3a_integration_scope:
  - `controller/profiles/candidate_a7r3a_300gm_short_checkpointed_1x5_3x9.json`;
  - `gui/eclipse_command/adaptive_profiles.py` i proves A7RIIIA vinculades;
  - llistes/manifest de packaging només si cal, `gui/build/` i `gui/dist/`;
  - documentació i informe QA nou només si el protocol de build ho exigeix;
  - cap PTP, `gphoto2`, captura, obertura interactiva ni acció física; el
    builder pot refrescar el registre local de LaunchServices del paquet.
- integration_result:
  - core adaptatiu A7RIIIA a 97,3 s: 74 imatges exactes, zero surplus;
  - programa C1-C4 a 97,3 s: 79 totals; `TEST RUN` 60/158/82: 114 totals;
  - surplus llarg: Single d'1 s, drenatges de 16/14 s i deute màxim 36;
  - controlador 580/580, GUI 284/284 i fuzz 67.392/67.392 verds;
  - dry-runs exactes 79/79 i 114/114, `status=complete`;
  - paquet macOS reconstruït i QA portable verd: manifest 33, 97 Mach-O,
    signatura ad-hoc, relocació, controller/worker/missió i Qt offscreen;
  - executable SHA-256
    `d453ab640a37c2741456ad4ada9ee58d8385313651abbf6a03200435f4d1b77f`;
    CDHash `31ab909e48b72c2ed8404466f50582ca6099db86`;
  - paquet anterior preservat com
    `gui/dist/Eclipse Command.app.previous-20260801T102352Z-42569`;
  - cap procés Eclipse/controller/gphoto2 viu al tancament; cap PTP ni càmera.
- previous_canon_scope:
  - contracte, perfils lab, compilador, proves i documentació específics Canon 6D;
  - evidència nova sota `controller/runs/codex_20260801_canon6d_optimization/`
    només després d'identitat i preflight segurs;
  - eines Canon de manifest SD/CR2 i gates físics, sense esborrat ni format;
  - `CODEX_STATUS.md` com a únic fitxer de coordinació editable per Codex.
  - cap GUI, cap Sony i cap acció manual; només Canon 6D, PTP serial i
    captures fosques amb tapa dins de l'autorització continuada de Pere.
- safety:
  - cap trigger ni escriptura PTP si falla identitat, preflight, targeta,
    filtre o exclusivitat de procés;
  - preservar tots els canvis preexistents i no editar `CLAUDE_STATUS.md`.
  - autorització continuada de Pere per executar desatesament els gates
    Canon 6D ja enumerats, sense reconfirmar cada preflight/run; primer error,
    identitat divergent o trigger ambigu aturen la campanya. Esborrat,
    format, ampliació d'abast, accions manuals i proves solars no queden
    automatitzats.
- canon6d_initial_live_gate_2026_08_01:
  - bolcat read-only verd: model `Canon EOS 6D`, sèrie PTP
    `[SÈRIE]`, cos `[SÈRIE]`, port resolt
    `usb:001,001`, firmware `3-1.1.9` i 85 paths sense cap write/trigger;
  - estat viu: bateria 100%, 2469 exposicions, M, MF, RAW, ISO 100,
    `Memory card`, 1/4000, Drive Single, AEB off, mirror lock 0 i
    autoapagada 0;
  - preflight estricte complet, no advisory, cap divergència i cap acció
    manual; en aquest punt, abans del gate físic, encara zero captures noves.
- verified_baseline:
  - Eclipse Command 0.6.6 a `gui/dist/Eclipse Command.app`.
  - GUI 281/281 i controlador 580/580 proves correctes després del hardening
    Canon offline.
  - Fuzz adaptatiu: 67.392 cronologies estrictes correctes.
  - QA del paquet portàtil correcte: manifest, signatura, relocació, Mach-O,
    controlador/worker congelats i arrencada offscreen.
  - SHA-256 executable:
    `13a7abac5238c191884274016a20c5c345f9ad9c2e8648c0a1d1900e96107f83`.
  - CDHash: `f0fead7dd5b25a5705cdf2c74543418382855934`.
  - Canvi de ports/cables verificat amb identitats estables.
  - A7RIIIA: preflight USB-C verd; F3M directe acumulat 80/80, F3 Single
    acumulat 440/440, gates 5x3/9x1 amb SD RAW i pantalla temporal híbrida
    de darks verda amb 1 passada a 100 s + 3/3 a 97,3 s; delta híbrid agregat
    verificat amb 280 ARW + 280 JPEG i partició exacta dels cinc runs. Un run
    addicional sense tapa a 97,3 s ha completat 55/55 amb JPEG de
    373.608-1.089.784 bytes i drenatges 6,076/2,623/15,207 s.
  - Campanya densa final: 20/20 Single a 0,75 s; límit verd 4x9/36 i hard
    stops reproduïbles a Single 0,50 s (19/20) i 5x9 (36/45); coreografia
    16 Single C2 + 1x5 + 4x9 + 17 Single C3 completa 74/74 a 97,3 s.
- main_changes:
  - Envolupants adaptatives A7III/A7RIIIA independents, amb pressupost propi
    per a cadències, offsets, drenatges, handoffs i floor de l'A7RIIIA.
  - Comparador offline Single, 5x3 fix, 9x1 fix i híbrid, sense copiar
    cadències de l'A7III.
  - Gates F3 Single complet i arestes F3M directes executats; perfils de
    retrigger 5x3/9x1 preparats amb manifest SD obligatori.
  - `Single -> 5x3`: 1,7 s en micro-USB i 1,4 s en USB-C; el candidat conserva
    1,7 s com a envolupant portable i el llindar híbrid independent a 97,3 s.
  - Single modelat amb el pitjor F3 propi: 80,85 s per una escombrada i retorn;
    no cap en cap totalitat candidata fins a 99,7 s.
  - Mateix cos: micro-USB High-Speed 480 Mb/s i USB-C SuperSpeed 5 Gb/s.
    Els drenatges A7RIIIA han quedat qualificats en USB-C.
  - El restore retardat espera només amb lectures quan Sony publica
    `capturemode` temporalment read-only; no consumeix cap write fins que el
    path és writable i conserva el límit de dues ordres de restauració.
  - Gate físic verd de canvi d'obturació amb 11/11 JPEG pendents. El perfil
    directe reordena `shutter -> drain` per als blocs d'11 i 27, amb un
    handoff acotat; la sessió PTP continua estrictament serial.
  - La compilació adaptativa llarga conserva provisionalment `drain ->
    shutter` fins qualificar l'overlap també per als blocs surplus; 280/280
    regressions GUI verdes. L'app oberta no s'ha reconstruït ni substituït.
  - Paquet macOS regenerat després de la correcció: 32/32 entrades del
    manifest de font exactes, signatura, relocació, 97 Mach-O, controlador,
    worker, missió de tres canals i arrencada offscreen verdes. Bundle
    anterior preservat com
    `gui/dist/Eclipse Command.app.previous-20260731T191418Z-92092`.
  - Resolució estable del port de runtime i expectativa nativa de bràqueting A7RIIIA.
  - La finestra Canon de 6,0/6,2 s ha quedat físicament refutada per un únic
    `PTP Device Busy 0x2019`; el perfil de missió Canon ara falla tancat abans
    d'armar-se fins que una nova envolupant sigui qualificada.
  - Perfils desconeguts o mal formats fallen de manera explícita.
  - Proteccions headless, correccions d'estats GUI i absència de cossos.
  - Eina de bolcat de capacitats només lectura.
  - Protocol R6 Mark III/CR3 i auditoria fotomètrica actualitzats.
  - Perfils lab 5x3/9x1 amb `production_event_date_utc=2026-08-12`; l'override
    de qualificació queda prohibit el dia de producció.
- evidence:
  - Informe: `gui/QA_REPORT_0.6.6_2026-07-31.md`.
  - A7RIIIA:
    `controller/runs/codex_20260731_a7r3a_full_choreography/20260731T043522_candidate_a7r3a_300gm_short_checkpointed_1x5_3x9_run`.
  - Preflight viu:
    `controller/runs/codex_20260731_a7r3a_optimization/20260731T150515_lab_a7r3a_300gm_choreography_f3_f3m_preflight`.
  - F3M directe:
    `controller/runs/codex_20260731_a7r3a_optimization/20260731T150549_lab_a7r3a_300gm_choreography_f3_f3m_f3m-capturemode`.
  - F3 Single:
    `controller/runs/codex_20260731_a7r3a_optimization/20260731T151224_lab_a7r3a_300gm_single_ladder_f3_f3-shutter`.
  - Preflight USB-C:
    `controller/runs/codex_20260731_a7r3a_optimization/20260731T162042_lab_a7r3a_300gm_choreography_f3_f3m_preflight`.
  - F3M USB-C:
    `controller/runs/codex_20260731_a7r3a_optimization/20260731T162110_lab_a7r3a_300gm_choreography_f3_f3m_f3m-capturemode`.
  - F3 Single USB-C:
    `controller/runs/codex_20260731_a7r3a_optimization/20260731T162209_lab_a7r3a_300gm_single_ladder_f3_f3-shutter`.
  - Manifest SD previ 5x3: 382 fitxers, 22.490.815.488 bytes, 263 ARW i
    119 JPEG; SHA-256 del JSON
    `58c2e038c16e8b50e48f4981f999d5d03b6e4a178fb3183a0f1f569cce8eda62`:
    `controller/runs/codex_20260731_a7r3a_optimization/GATE_A7R3A_FIXED_5X3_sd_before.json`.
  - Preflight 5x3 rebutjat abans de qualsevol mutació o trigger:
    `controller/runs/codex_20260731_a7r3a_optimization/20260731T163916_lab_a7r3a_300gm_fixed_5x3_retrigger_preflight`.
  - Preflight 5x3 posterior verd, `3.0 EV x5`, `1/30`, bateria 89 %, cua zero
    i zero captures:
    `controller/runs/codex_20260731_a7r3a_optimization/20260731T164528_lab_a7r3a_300gm_fixed_5x3_retrigger_preflight`.
  - Intent armat rebutjat abans de lock/PTP/trigger per manca de C2/C3; zero
    captures i cap estat ambigu:
    `controller/runs/codex_20260731_a7r3a_optimization/20260731T170016_lab_a7r3a_300gm_fixed_5x3_retrigger_run`.
  - Gate físic 5x3 USB-C complet: cinc retriggers a 10 s, 25/25 commits, cua
    màxima 25, 25 JPEG únics, postflight verd, drenatge complet en 16,291 s,
    neteja/restauració verdes i estat físic conegut:
    `controller/runs/codex_20260731_a7r3a_optimization/20260731T172713_lab_a7r3a_300gm_fixed_5x3_retrigger_run`.
  - Manifest SD posterior: 448 fitxers, 25.317.179.392 bytes; delta 66 afegits,
    0 modificats i 0 eliminats. Els 25 ARW `DSC01532-DSC01556` del run passen
    8000x5320, 14 bits, compressió 1, bits baixos i correlació EXIF. El delta
    conté també vuit parelles anteriors `DSC01524-DSC01531`; el gate estricte
    queda vermell i `scientific_raw_verified=false`:
    `controller/runs/codex_20260731_a7r3a_optimization/GATE_A7R3A_FIXED_5X3_sd_delta.json`.
  - `verify_sd_raw_gate.py` ja respecta `media_route_probe.enabled=false` i
    exigeix zero probes en aquests perfils, sense relaxar l'exclusivitat del
    delta.
  - Preflight de repetició 5x3 verd: identitat exacta, 5x3, 1/30, ISO 400,
    RAW+JPEG, `card+sdram`, bateria 87 %, cua zero, cap autofix i zero
    captures:
    `controller/runs/codex_20260731_a7r3a_optimization/20260731T182306_lab_a7r3a_300gm_fixed_5x3_retrigger_preflight`.
  - Repetició 5x3 completa i verda: 25/25 commits, cinc brackets exactes,
    cua 25 -> 0, 25 JPEG únics, cap warning/recovery, cleanup/restore verds i
    estat físic conegut. Fitxers `DSC01557-DSC01581`:
    `controller/runs/codex_20260731_a7r3a_optimization/20260731T185122_lab_a7r3a_300gm_fixed_5x3_retrigger_run`.
  - Gate SD RAW 5x3 tancat: delta exclusiu 50 entrades, 25 ARW + 25 JPEG
    `DSC01557-DSC01581`, 448 fitxers previs intactes, 0 modificats i 0
    eliminats. 25/25 ARW a 8000x5320, 14 bits, compressió 1, bits baixos
    actius i EXIF concordant; `scientific_raw_verified=true`:
    `controller/runs/codex_20260731_a7r3a_optimization/GATE_A7R3A_FIXED_5X3_REPEAT_sd_verify.json`.
    SHA-256 manifest/delta/report: `7dbbc05b...3065c`, `31fde959...03ec`,
    `73eded65...abd4`.
  - Primer preflight 9x1 fallit tancat abans de cap mutació/trigger: el cos
    continua en `Bracketing C 3.0 Steps 5 Pictures`; identitat, 1/30, ISO 400,
    bateria 86 % i cua zero eren verds. Pere ha de seleccionar manualment
    `Bracketing C 1.0 Steps 9 Pictures`:
    `controller/runs/codex_20260731_a7r3a_optimization/20260731T193856_lab_a7r3a_300gm_fixed_9x1_retrigger_preflight`.
  - Preflight 9x1 posterior verd: identitat exacta, mode 1.0 EV x9, 1/30,
    ISO 400, RAW+JPEG, `card+sdram`, bateria 86 %, cua zero i zero captures:
    `controller/runs/codex_20260731_a7r3a_optimization/20260731T194231_lab_a7r3a_300gm_fixed_9x1_retrigger_preflight`.
  - Run 9x1 complet: tres brackets, 27/27 commits/JPEG, ordre físic
    `0,-1,+1,-2,+2,-3,+3,-4,+4`, cua 27 -> 0, cap warning/recovery,
    cleanup/restore verds i estat conegut. Fitxers `DSC01582-DSC01608`:
    `controller/runs/codex_20260731_a7r3a_optimization/20260731T194255_lab_a7r3a_300gm_fixed_9x1_retrigger_run`.
  - Gate SD RAW 9x1 tancat: delta exclusiu 54 entrades, 27 ARW + 27 JPEG
    `DSC01582-DSC01608`, 498 fitxers previs intactes, 0 modificats i 0
    eliminats. 27/27 ARW a 8000x5320, 14 bits, compressió 1, bits baixos
    actius i EXIF concordant; `scientific_raw_verified=true`. Drenatge
    observat 27 -> 0 en 16,995 s:
    `controller/runs/codex_20260731_a7r3a_optimization/GATE_A7R3A_FIXED_9X1_sd_verify.json`.
    SHA-256 manifest/delta/report: `bbde94c4...b90e`, `ca5f2998...359b`,
    `d4162a82...a60c`.
  - Dry-run híbrid de 100 s verd: 36 accions, 55 imatges, ordre físic
    centre-alternat corregit i pressupostos A7RIIIA independents. Regressions
    posteriors: controlador 531/531 i GUI 280/280.
  - Primer preflight híbrid rebutjat abans d'obrir PTP: IORegistry confirma
    encara Mass Storage/USB classe 8 i `gphoto2 --auto-detect` no veu cap
    càmera. Zero mutacions i zero captures:
    `controller/runs/codex_20260731_a7r3a_optimization/20260731T201844_candidate_a7r3a_300gm_short_checkpointed_1x5_3x9_preflight`.
  - Primer híbrid corregit a 100 s: 36/36 accions i 55/55 JPEG, però resultat
    top-level vermell exclusivament perquè el cleanup va llegir `Single Shot`
    com `Readonly: 1` i no va poder enviar el restore explícit. Un preflight
    posterior va confirmar estat físic conegut, Single i cua zero:
    `controller/runs/codex_20260731_a7r3a_optimization/20260731T203119_candidate_a7r3a_300gm_short_checkpointed_1x5_3x9_run`.
  - Repetició verda a 100 s: 36/36, 55/55 JPEG únics, ordre EXIF exacte,
    drenatges 11/5/27 en 6,587/2,880/16,814 s, zero warnings/recovery, cua
    final zero, restore i cleanup verds. El gate readonly va observar dues
    lectures bloquejades i va esperar 240,005 ms abans d'una sola ordre:
    `controller/runs/codex_20260731_a7r3a_optimization/20260731T204540_candidate_a7r3a_300gm_short_checkpointed_1x5_3x9_run`.
  - Cribratge híbrid 3/3 a 97,3 s complet. Tots tres runs: 36/36, 55/55,
    postflight, restore i cleanup verds, zero warning/skip/recovery i estat
    físic conegut. Pitjors drenatges: 7,253 s per 11, 2,795 s per 5 i
    17,423 s per 27, dins 7,8/4,3/17,8 s:
    `20260731T205258...`, `20260731T205839...`, `20260731T210446...`.
    Límit d'evidència: tots són darks amb JPEG S de només 360-426 KiB. El
    pitjor drenatge de 27 és 17,423/17,8 s; no qualifica encara la mida ni el
    temps de transferència d'una escena real.
  - Gate SD/RAW híbrid complet: contra el baseline de 552 fitxers, el delta
    agregat afegeix exactament 560 entrades, 280 ARW + 280 JPEG
    `DSC01609-DSC01888`, sense modificacions ni eliminacions. Els cinc blocs
    consumeixen els 560 fitxers una sola vegada; cada bloc té una sonda i 55
    RAW científics. Tots els ARW passen 8000x5320, 14 bits, compressió 1,
    bits baixos actius, ISO 400 i correlació d'obturació/bias. El report
    declara `scientific_raw_verified=true`; quatre runs són `complete` i el
    primer conserva `failed` per la restauració posterior:
    `controller/runs/codex_20260731_a7r3a_optimization/GATE_A7R3A_HYBRID_5RUNS_sd_verify.json`.
    SHA-256 manifest/delta/report: `226b3fd9...568d`, `18f9a05f...b799`,
    `95a02837...1465`.
  - Un intent previ a la primera mostra 97,3 s va ser rebutjat abans d'obrir
    PTP perquè faltaven 0,683 s del lead mínim; zero mutacions/captures:
    `controller/runs/codex_20260731_a7r3a_optimization/20260731T205240_candidate_a7r3a_300gm_short_checkpointed_1x5_3x9_run`.
  - Gate shutter amb cua pendent complet: 11/11 JPEG encara a `d215` després
    del setter verificat, drenatge 6,142 s, postflight/restore/cleanup verds:
    `controller/runs/codex_20260731_a7r3a_overlap_optimization/20260731T231059_lab_a7r3a_300gm_shutter_before_drain_run`.
  - Run híbrid reordenat sense tapa a 97,3 s complet: 36/36, 55/55, zero
    warnings/skips/recovery, drenatges 11/5/27 de 6,076/2,623/15,207 s,
    JPEG científics 373.608-1.089.784 bytes, sonda 944.614 bytes, cua final
    zero i restore/cleanup verds:
    `controller/runs/codex_20260731_a7r3a_overlap_optimization/20260731T231728_candidate_a7r3a_300gm_short_checkpointed_1x5_3x9_run`.
  - Gate 4x9 verd: quatre brackets a 3,0 s, 36/36, cua 35 -> 0, EXIF exacte,
    drenatge de 36 en 22,356 s i cleanup verd:
    `controller/runs/codex_20260801_a7r3a_deep_optimization/20260801T003450_lab_a7r3a_300gm_dense_9x1_gate_run`.
  - Hard stop 5x9: cinc press/release confirmats però només 36/45 fitxers i
    `d215=0`; cap replay:
    `controller/runs/codex_20260801_a7r3a_deep_optimization/20260801T003623_lab_a7r3a_300gm_dense_9x1_gate_run`.
  - Gate Single 0,75 s verd: 20/20, intervals 750,2-751,3 ms, cua 18 -> 0,
    postflight i cleanup verds:
    `controller/runs/codex_20260801_a7r3a_deep_optimization/20260801T005252_lab_a7r3a_300gm_dense_single_gate_run`.
  - Hard stop Single 0,50 s: vint ACK però 19/20 fitxers i `d215=0`; cap
    replay:
    `controller/runs/codex_20260801_a7r3a_deep_optimization/20260801T005414_lab_a7r3a_300gm_dense_single_gate_run`.
  - Coreografia densa final a 97,3 s: 47/47 accions, 74/74 JPEG, zero
    warnings/skips/recovery, drenatges 16/5/36 de 9,778/2,772/22,827 s,
    postflight, restore i cleanup verds:
    `controller/runs/codex_20260801_a7r3a_deep_optimization/20260801T004802_lab_a7r3a_300gm_dense_full_choreography_run`.
  - Preflight final només lectura: Single Shot, 1/1250, ISO 400, RAW+JPEG
    Std, `card+sdram`, bateria 72 %, cua zero, cap warning i cleanup verd:
    `controller/runs/codex_20260801_a7r3a_deep_optimization/20260801T005851_lab_a7r3a_300gm_dense_full_choreography_preflight`.
- remaining_field_gates:
  - Firmware literal `1.00` confirmat. Gate 5x3 complet, incloent retrigger,
    drenatge JPEG, delta SD exclusiu, integritat RAW i EXIF.
  - Gate 9x1 complet, incloent retrigger, drenatge JPEG, delta SD exclusiu,
    integritat RAW i EXIF.
  - Gate SD/RAW híbrid complet, incloent la partició exacta dels cinc runs i
    275 RAW científics + cinc sondes. Una passada sense tapa també és verda,
    però el seu delta SD no parteix d'un manifest exclusiu nou.
  - Fer el gate solar/òptic i el delta SD/RAW exclusiu de la coreografia 74;
    no promoure el perfil amb una sola mostra completa.
  - Validació solar/òptica i A/B fotomètric.
  - Run físic de la cronologia Canon nova.
  - Cable-pull i bateria de l'A7RIIIA.
  - Alta física R6 Mark III, mostres CR3 i inspector compatible.
  - Passada Cocoa amb sessió gràfica desbloquejada.
  - Promoció/checkpoint explícit dels perfils candidats.
- handoff:
  - Cap commit ni push.
  - Canvis preexistents de l'usuari preservats.
  - Gates RAW 5x3/9x1/híbrid tancats i nova coreografia 74/74 qualificada en
    timing/JPEG; continua candidata fins al delta SD propi, gate solar/òptic,
    cable-pull, bateria i promoció explícita.
  - Estat final confirmat a PC Remote: identitat exacta, Single Shot, 1/1250,
    ISO 400, RAW+JPEG Std, `card+sdram`, bateria 72 %, cua zero, cleanup verd,
    estat físic conegut i cap procés `gphoto2`/controlador viu.
  - L'A7RIIIA va alliberar `SERIAL_WRITES` explícitament i el task Canon el va
    adquirir després. La Canon també l'ha alliberat ara arran del hard stop;
    cap dels dos tasks iniciarà cap altre PTP/run sense autorització nova.

## Tancament Canon EOS 6D — 2026-08-01

- physical_campaign: HARD_STOP_0X2019
- serial_writes: RELEASED
- scope:
  - la Canon va adquirir `SERIAL_WRITES` només després del handoff explícit
    de l'A7RIIIA;
  - no es va executar la GUI, no es va tocar cap Sony i, després del primer
    error de càmera, no es va enviar cap altre PTP ni trigger.
- live_read_only_gate:
  - identitat exacta: model `Canon EOS 6D`, sèrie PTP
    `[SÈRIE]`, número de cos `[SÈRIE]`,
    firmware `3-1.1.9`, port resolt adaptativament `usb:001,001`;
  - estat observat: M, MF, RAW, ISO 100, targeta, `1/4000`, Drive Single,
    AEB off, mirror lock 0, autoapagada 0, bateria 100 % i 2.469 exposicions;
  - preflight estricte verd, no advisory, sense divergències ni accions
    manuals;
  - evidència:
    `controller/runs/codex_20260801_canon6d_optimization/20260801T010919_candidate_canon6d_contacts_cardonly_capabilities`
    i
    `controller/runs/codex_20260801_canon6d_optimization/20260801T011022_candidate_canon6d_contacts_cardonly_preflight`.
- sd_before:
  - manifest remot verd amb una única entrada `IMG_2295.CR2`, zero writes i
    zero triggers:
    `controller/runs/codex_20260801_canon6d_optimization/20260801T011609_candidate_canon6d_contacts_cardonly_canon-card-snapshot`.
- decisive_gate:
  - un únic RAW press/release i un únic setter `1/4000 -> 1/2500`;
  - `busy_retries=0`, `max_attempts=1`, zero reconnects i zero replay;
  - el setter enviat 6,221 s després del press, 6,101 s després del release
    enviat i 6,091 s després de l'ACK del release va rebre
    `PTP Device Busy 0x2019` i no va canviar la propietat;
  - l'artefacte final registra `1/4000`, release confirmat, `restore_ok=true`,
    `cleanup_ok=true` i cap recovery; això és estat al final de l'artefacte,
    no una lectura viva posterior;
  - evidència:
    `controller/runs/codex_20260801_canon6d_optimization/20260801T011708_canon6d_lab_quiet_v1_run`.
- raw_boundary:
  - el ledger té un commit, però no hi ha inventari SD posterior, descàrrega,
    hash, integritat ni EXIF perquè el hard stop va prohibir més PTP;
  - hi ha un probable CR2 nou a la targeta, encara no verificat i no
    qualificat.
- offline_hardening:
  - perfil Canon de missió bloquejat fail-closed al materialitzador i al
    controlador abans de PTP;
  - contracte lab només qualification-run, zero busy retries, sense recovery,
    autofix ni replay i stop al primer error;
  - readiness post-RAW ancorada al `Release Full` real i cleanup lab amb floor
    conservador de 30 s, encara no qualificat físicament;
  - eines card-only per manifest/delta/ledger/hash/CR2 i inspector CR2;
  - missatge d'identitat i protocol corregits; l'etiqueta auto-detect i el
    port USB no es tracten com a identitat.
- regression:
  - controlador: 580/580;
  - GUI offscreen: 281/281;
  - `git diff --check`: verd.
- qualification_boundary:
  - AEB, Continuous, recompte i ordre de bracket, fondària de buffer,
    `Q[g]`, nova coreografia C2-C3, integritat del CR2 actual i exposicions
    solars continuen sense qualificació física;
  - l'app existent no s'ha reconstruït i no incorpora el blocker nou: no
    s'ha d'usar per armar la Canon;
  - cap nou gate físic sense una autorització nova de Pere.
- report:
  - `research/45_CANON_6D_AUDITORIA_OPTIMITZACIO_HARD_STOP_2026-08-01.md`.

## Canon 6D Stage A v9 preparat — 2026-08-01T23:45:51Z

- serial_writes: ACTIVE; owner Canon EOS 6D; Claude continua RELEASED.
- el bundle Stage A v8 queda `INVALIDATED_DO_NOT_EXECUTE` sense modificar-ne
  cap byte. Rebut immutable adjacent SHA
  `c9812f301d363478a18759a9be338c9e3a76d3d4841e577f42a8eed6ae32b567`:
  `controller/runs/codex_20260801_canon6d_optimization/stage_ab/canon6d_full_history_stage_a_v8_invalidated_20260801T2341Z.json`.
- compiler corregit: totes les `held_capture` fixes declaren
  `finish_ready_for=retrigger`; SHA
  `57f28afe7103a58738f4afcf4c4d6a5b5343069859f8a31e7332628e26b746ce`.
  El runtime i l'auditoria estricta concorden amb marge mínim +0,03 s.
- successor immutable v9:
  `controller/runs/codex_20260801_canon6d_optimization/stage_ab/canon6d_full_history_stage_a_v9_20260801T234236Z`;
  pla SHA `d0867680b29ebdd5127f31252069bf4e157a73dbd95307559e37549be62c5126`,
  perfil SHA `51f5c40c957d20ee301a86994ecfb47aaca543aa28416fabf9cc25638885c314`;
  32 grups / 96 CR2, `finish_ready_for=retrigger` a 32/32 i dry-run 32/32
  complet amb zero comandes de càmera.
- regressions finals: controlador 830/830; compiler 22/22; GUI focal 92/92;
  auditoria independent GUI completa 335/335, Stage A/B 49/49 i integració
  v2 23/23; sintaxi i bindings SHA verds.
- snapshot SD v9 read-only verd i sessió PTP tancada: exactament els 252 CR2
  predecessors `IMG_2295.CR2..IMG_2546.CR2`, storageid `00020001`, identitat
  PTP Canon exacta i cap residual. Inventari SHA
  `d3688ae2769d80c41d92ea4da691ae8dfbb4814a149d7596009fd1fef9f20e3b`.
- hard stop viu únic abans del Stage A físic: `ntp_gettime` ha romàs
  `TIME_OK`, però l'última mostra read-only és `maxerror_us=223383`, superior
  al bound contractual de 50 ms. No s'ha iniciat Stage A ni cap trigger.
- següent pas autoritzat: monitoritzar sense mutar el rellotge i, només després
  d'un reset espontani amb mostra pròpia idealment <=45 ms, llançar v9; el
  controlador exigeix encara dues mostres pròpies <=50 ms abans de gphoto2,
  lock o PTP. Zero replay i tots els hard stops continuen vigents.

## HANDOFF FINAL Canon Stage A / Stage B offline — RELEASED 2026-08-02T00:01:45Z

- Stage A v9 físic complet i certificat sense replay:
  - pont UTC amb dues mostres pròpies `TIME_OK`, `maxerror_us=25986`;
  - 32/32 grups i 96 RAW esperats C2-totalitat-C3, fins a C3+5,75 s;
  - zero Busy `0x2019`, `-110`, timeout, warning, recovery, setter post-RAW,
    trigger ambigu o replay; cleanup i estat final verds;
  - card-gate v2: 252 -> 348 CR2, delta exacte `IMG_2547..IMG_2642`,
    96/96 CR2, 1.838.236.549 bytes, hashes, integritat, ISO 100, cos
    `[SÈRIE]`, ordre `1/250 -> 1/2000 -> 1/30`, ledger i inventari
    estable verds;
  - run result SHA `87498a8230006e84da5bc132a8f1c0b1e68550de9422321721470df1eed0e8e2`;
    card-gate result SHA
    `811ee862be4a024e54af767acbfbc91880e21059d8c83c35f6a46692d1e1f02e`.
- Evidència immutable `G_ok_tail=5`:
  `stage_ab/canon6d_full_history_stage_a_v9_20260801T234236Z/g_ok_tail_evidence.json`,
  SHA `868aec6850195b4c448a177922fe86510ab645fc08bc5360095703036336ae1a`,
  estat `PHYSICALLY_QUALIFIED_FULL_HISTORY`, fingerprint qualificat
  `fc195fd8f28df63a169a8d3b3c59897200f87f4eb31e959f6e15c1f9568a4248`.
- Defecte offline del certificador corregit sense tocar evidència física:
  `commits_by_action` es valida com a mapa; els tres ordres autoritatius
  continuen fail-closed. Planner SHA
  `8fdd5aa51d23c2fadf03a011ed826f52799d591d7dc3c25a71ea55519b194e60`.
- Stage B **només offline, no executat**:
  - successor canònic
    `stage_ab/canon6d_full_history_stage_b_v2_20260802T000019Z`;
  - pla SHA `48c0e5ef191f60c734ddf2adc0d785f98aa4e8e44944eb1aa4b3b0ead4dd99dc`;
  - perfil SHA `2256cf1636763564e04b8f73565a02e13664a10b3f174d0f2e011070ae0409b6`;
  - 31 grups / 93 CR2, quatre grups densos i reserva d'un grup,
    `PEAK_ENVELOPE_SCHEDULED`, dry-run 31/31 verd;
  - v1 està `SUPERSEDED_DO_NOT_EXECUTE`, rebut SHA
    `044ab990cc958bbd1e5e9c4a65f7e5379e95e39b4ea8bf3251e3ae6fab8469f7`.
- Perfil operatiu Canon v2 actualitzat honestament però encara
  `PROGRAM BLOCKED`, `materialization_ready=false`, `stage_b_qualified=false`:
  SHA `ebd997e86ff869d65a0a2ca9344bd31e118e41839dc41f943c6722ab203cc377`.
  Falten Stage B físic, geometria fosca C1-C4, simultaneïtat i A/B
  solar/òptic; cap d'aquests gates s'ha inventat ni heretat.
- Regressions finals postcanvi: controlador focal 80/80, GUI focal 123/123,
  Stage A/B 51/51 i integració v2 23/23; `git diff --check` i JSON/SHA verds.
  La regressió completa anterior al canvi de blocker va ser controlador
  830/830 i GUI independent 335/335.
- Preparat per build/app: empaquetar el perfil operatiu SHA `ebd997e8...` i
  el controlador dedicat SHA
  `7c14c5f2676336e4d3c4041f4499f6f96095c21e86947cccb37756eaebaf5fef`;
  la GUI ha de continuar mostrant `PROGRAM BLOCKED` i excloure Canon del run.
  Aquesta unitat no ha executat build/dist ni LaunchServices.
- Checkpoint OS final: zero Eclipse Command, mission/worker/camera host,
  controlador, gphoto2, card-gate, certificador o reconciliació vius; PTP
  alliberat. Sony no tocades. SERIAL_WRITES i totes les rutes RELEASED.

### V29 — avenç 05-09-2026, 12:25 CEST — IN_PROGRESS

- SERIAL_WRITES continua en poder de `CODEX_V29_20260905`.
- Entrades V28 i V28_Artefactes congelades amb SHA-256 a `research/tools/v29/cau/input_manifest.json`.
- Confirmats: esvaïment ACHF/PAL a zero ≥5R; forat circular a 1,05R; ghost reintroduït des del TOTAL cru; estimador de soroll blanc inadequat per CFA Sony remostrejat.
- Reproduïts 11.794 píxels interiors exclosos per CORONA, contra LDIC: 11.493 amb ≥2 fotogrames i 301 amb un. Rebut reproduïble `cau/limb_receipt.json`.
- Sony A/B i meitats temporals recompostes només a `research/tools/v29/`; cap canvi als runs. B és donant net del ghost, Vixen queda com a jutge independent.
- Pilots intermedis no acceptats: amplificació de gra, vora del rectangle intermedi i arcs. NO són V29 lliurada i no hi ha cap nou PSB.
- En curs: composició CFA directa a la graella existent 10551×7506 del PSB (mateix FOV i M), a `cau_final/`, per evitar el rectangle intermedi i el segon remostreig. Normalització de contrast després de filtrar per no introduir arcs de guany radial.
- Pendents abans de lliurar: jutge dels sectors marcats, verificació de retenció i soroll, tots els canals/màscares, composició real, porta Photoshop, rebut i handoff RELEASED.


### V29 — LLIURADA / RELEASED — 2026-09-05T11:01:34.167585+00:00

- status: COMPLETE · serial_writes: RELEASED · claim_id: CODEX_V29_20260905.
- Lliurament: `/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V29.psb`, 10.551 × 7.506, RGB16, 25 capes, 4223401864 bytes. SHA-256 `b5c2055b329305b7a8efe6f14159414b739da7a43077e8ba9b7b32288b4ac3ff`.
- Rebut: `V29_REBUT.md` al costat del PSB; explicació completa a `research/134_V29_detall_unio_temporal.md`. Manifest i QA a `research/tools/v29/cau_final/`.
- Photoshop: OBRE 10551 px x 7506 px · 25 capes; document de prova tancat sense desar. 20 capes originals amb tots els canals/màscares/coords/modos/opacitats idèntics. Cinc capes noves exactes; merged exacte; recomposició reoberta ≤1 DN de 16 bits.
- ACHF fi/PAL amb resposta exterior sense el tall de 5 R; Sony B neta primària; gran final angular per tren abans del blend, G positiu/finit; 04 ample retirada. Els pilots isotrops o amb donant circular NO es lliuren.
- Unió temporal: 40.863 píxels observats dins d'1,05 R; base i fi/PAL alineats amb el mateix suport. Gran exclou només 3 píxels sense G vàlid en cap tren. Llenç/FOV invariables; RAW i runs immutables.
- H1 estricte PASS; angles dels tres filtres 0° amb controls reals; judici angular local i transicions PASS; controls d'injecció/FFT PASS.
- Límit vigent: H1b del passa-alt 2,976 > llindar d'avís 2; no declarat corregit. Textura exterior 8–16 px no demostrada en general; conservar el límit de resolució/soroll. `Fons per raig` històric ocult amb pic feble −0,75°, no reinterpretar com a font alineada nova.
- Handoff explícit: feina V29 acabada i lliurada amb aquests límits; zero workers propis i cap document Photoshop propi obert. Les futures accions requereixen un nou claim; no tornar a empaquetar damunt de V29. Només s'ha actualitzat el diari de Codex.


### Skills — retallades circulars — IN_PROGRESS — 2026-09-05T11:05:03.130520+00:00

- SERIAL_WRITES adquirit: `CODEX_SKILL_CIRCULAR_20260905`. Petició explícita de Pere: advertir que probablement les retallades circulars fan més mal que bé.
- Abast: normes de postprocessat i correcció d’artefactes, còpies de projecte i Codex sincronitzades; revisió només documental.


### Skills — retallades circulars — COMPLETE / RELEASED — 2026-09-05T11:09:36.066867+00:00

- status: COMPLETE · serial_writes: RELEASED · claim_id: CODEX_SKILL_CIRCULAR_20260905.
- Incorporada la precaució expressa de Pere: probablement les retallades circulars fan més mal que bé; poden eliminar detall real de corona i crear halos, també amb ploma. Declarar el radi no valida la correcció.
- Retirades com a instruccions per defecte les receptes de pedaços neutres, inpainting/clonació, forat fix engrandit i esvaïments 3,5→5, 5→6,5 i 5→7 R☉. Evidència i exemples antics identificats com a històrics.
- Distingits suport temporal de corona vàlida, disc/earthshine C2, cobertura física, qualitat del pes, ponderació HDR i operacions polars. Les marques de Pere localitzen el problema; no són màscares d’esborrat. Centre solar per efemèride, separat de la geometria lunar.
- Revisió independent només de lectura; observacions incorporades. Validació formal `quick_validate.py`: 4/4 PASS. S’han reparat dues capçaleres YAML prèviament invàlides, mantenint íntegres noms i descripcions d’invocació.
- Tres documents idèntics entre `.claude/skills/` i `/Users/USUARI/.codex/skills/` (sis fitxers):
  - `postprocessat-corona/SKILL.md`: `216569d9da4615775e58e0402c9c114f0cbe2672f415cb32ae520e2ee6cb241c`.
  - `postprocessat-corona/references/normes_i_portes.md`: `bfe1d757c623921546e69eeb5118e22904f3774268d899e885f4b812cfa63165`.
  - `corregeix-artefactes/SKILL.md`: `c55235e09d77aa5073eb0ab9bf40ac10b9212ece873e3f81beea791a90d84138`.
- Handoff explícit: actualització documental acabada. Cap processat d’imatges, cap canvi al codi de processat ni als actius, cap acció física. Zero processos propis vius; les accions futures requereixen un nou claim.


### V29 — pentagonals de capa 03 — IN_PROGRESS — 2026-09-05T11:17:16.816212+00:00

- Claim `CODEX_PENTAGONALS_20260905`. Pere accepta explícitament `01 ACHF fi 2-32 · V29` i `02 Passa-alt 24 · V29`; queden congelades.
- Referència de marques: `/Users/USUARI/Downloads/pentagonals.tif`. Diagnòstic i correcció limitada a capa 03; V29 i fonts immutables; mateix llenç i FOV.


### V29 — pentagonals inspeccionats / RELEASED — 2026-09-05T11:27:05.939885+00:00

- serial_writes: RELEASED · claim_id: CODEX_PENTAGONALS_20260905. Inspecció completada; correcció de la capa 03 encara pendent.
- ACCEPTADES PER PERE: `01 ACHF fi 2-32 · V29` i `02 Passa-alt 24 · V29`, congelades sense canvis. `03 ACHF azimutal 8-128 · V29` NO ACCEPTADA visualment pels pentàgons.
- Informe: `research/135_V29_pentagonals.md`; codi i rebuts a `research/tools/v29_pentagonals/`; vistes al directori IA/output/v29_pentagonals_20260905.
- Contorns mitjans alineats amb l’entrada dels tres Vixen 10 s (pes +60); exterior amb Sony B 8 s (+16). Comparació Vixen individual 10s/2s: mediana 0,958 a2–2,5R i0,945 a2,5–3R, mentre2s/1s≈1. Evidència de desnivell radiomètric, no només canvi de soroll. Sony pendent del mateix contrast.
- H1 accentua, però no origina tot el defecte; angle fix provat i rebutjat com a solució. Cap retall, atenuació per marques ni tractament cosmètic. La QA anterior de la03 no certifica absència de costures HDR d’isòfotes.
- Handoff explícit: diagnòstic documentat, cap correcció lliurada ni nova versió PSB. Cap modificació de V29, capes01/02, codi V29, RAW o runs; cap GUI ni acció física. Zero processos propis vius. Per corregir cal nou claim i validar els grups d’exposicions amb fotogrames reservats.


### V29 — correcció autoritzada de capa03 — IN_PROGRESS — 2026-09-05T11:30:10.242982+00:00

- Claim `CODEX_V29_C03_FIX_20260905`. Pere: «corretgeix doncs aquesta capa en la V29». Únic canvi de contingut: capa03;24altrescapes preservades incloses01/02 acceptades.
- Còpia anterior verificada a `/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/Documentacio i QA/V29_abans_correccio_03_20260905`. SHA `b5c2055b329305b7a8efe6f14159414b739da7a43077e8ba9b7b32288b4ac3ff`. Sortida amb mateix nom, llenç i FOV; substitució final només després de QA.


### V29 — capa03 corregida i lliurada / COMPLETE / RELEASED — 2026-09-05T11:49:13.843470+00:00

- serial_writes: RELEASED · claim_id: CODEX_V29_C03_FIX_20260905. Complerta l'autorització de Pere de corregir la capa03 dins de V29. Només03RGB canviats;24altrescapes idèntiques en canals comprimits i registres de metadades, incloses01/02 acceptades.
- V29 viu: `/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V29.psb`. SHA `67169f0345c8abdf3fb9c3fd940d5b9f13d260864954d776c5d9277e15630676`;4.221.719.560bytes;10551×7506 RGB16,25capes. Alfa,màscara,geometria,visibilitat,nom,Superposar i opacitat38/255 de03 preservats;merged actualitzat.
- Còpia anterior i rebut preservats a `Capes Totals/Documentacio i QA/V29_abans_correccio_03_20260905/`; SHA anterior`b5c2055b329305b7a8efe6f14159414b739da7a43077e8ba9b7b32288b4ac3ff`.
- Correcció additiva global per fotograma/canal calibrat a partir de captures comunes; sectors reservats i jutge independent. Projectada amb pesos/registres originals, mateix operador8/32/64/128, escala i resolució. Sense retall circular ni ús de marques com a màscara.
- ContornSE: pas visible0,0217→0,00436; cru0,0444→0,00019. Inspecció100%PASS amb residuals declarats; filamentscorr0,997/0,991/0,978. Amplitud exterior82,8%de l'anterior; no s'atribueix tota reducció a soroll. Rampa de llargues: residus fins−1,84%Vixen/−1,23%Sony; no és nova certificació absoluta del màster.
- H1max0,011040; angle0°Pearson0,8071; controls±1°/180° rebutjats. H1b03=3,211756 AVÍS, sense anell nou visible; PAL2,976378intacte. Suport03=70.395.267px,40.860dins1,05R; fora màscara03delta compost=0.
- Verificació del PSB reobertPASS; recomposició≤1DN16bits. Photoshop real`OBRE10551px x7506px ·25capes`, sobre staging propi, tancat sense desar; mode de diàlegs restaurat. Substitució atòmica només després de reconfirmarSHAviu=backup.
- Evidència: `research/136_V29_capa03_corregida.md`, `research/tools/v29_c03_fix/delivery_manifest.json`,rebutsQA i pilots100%aIA/output/v29_c03_fix_20260905. `V29_REBUT.md` actualitzat; el rebut anterior queda amb el backup.
- Handoff explícit: correcció lliurada i auditada, pendent únicament del judici visual de Pere com a operador. Cap RAW,run,cau_final,capa01/02,CLAUDE_STATUS o skill modificat en aquesta ronda. Zero treballadors propis de càlcul,cap document de verificació obert. Qualsevol acció futura adquireix nou claim.


### V30 — minicercles i variants ACHF — IN_PROGRESS — 2026-09-05T12:02:31.505945+00:00

- Claim CODEX_V30_MINICERCLES_20260905. Autoritzat per Pere: V30.psb, suavitzar/eliminar minicercles de minicerclesConcentrics.psb, conservar filtres actuals i afegir variants del01, actualitzar skill si funciona i reconciliar documentació viva.
- V29 corregida immutable; mateix llenç i FOV. Només root escriu; dos revisors independents de lectura. Cap RAW/run/PTP ni càmera.
