# Handoff vigent — 23-08-2026

> ⏭️ **25-08-2026 · SUPERAT PER A LA BRANCA DEL PILOT.** El testimoni torna a
> **Codex**. El traspàs formal viu és
> `/Users/USUARI/Downloads/Eclipse 2026/.coordination/HANDOFF_2026-08-25_CODEX_COSTURES_I_SOSTRE.md`
> (SHA-256 `1a22a6ea0c059d027e3fd5ffe191aa2b27538c9fc37749e6523fe86f9f4040a9`), amb el delta
> `DELTA_CLAUDE_a_CODEX_25-08-26_TRASPAS_ARCS_I_SOSTRE.md`
> (SHA-256 `67f2fd2705852c74f400bd445c85bbd4ea0262231ecf1e185741590e5fc87f36`).
>
> ⛔ La secció «PRIORITAT VIVA 23-08 — PILOT VIXEN BLOQUEJAT A F0/F1» d'aquest
> document **ja no descriu l'estat**: el pilot està executat
> (`research/99`) i les portes F0/F1 originals van resultar impossibles. Es
> conserva com a història.
>
> ⚠️ **Estat real dels artefactes, i no és «curat» a seques** (corregit el 25-08
> després que Codex hi trobés una contradicció amb el traspàs formal): la ronda
> del 24 i el 25 (`research/100`) ha curat **els anells circulars als dos trens**
> —Vixen 27,5 % → 0,441 %, Sony 34,9 % → 0,462 %— i **les costures de fusió**
> —88,6 % → 4,6 % i 92,6 % → 5,4 %—, però ⛔ **queda una regressió OBERTA a la
> Sony** a r = 1,263/1,266 R☉, on les dues passades de resta empitjoren l'arc en
> lloc de treure'l. Manen els números del traspàs formal, no aquest resum.

Actualitzat per a l'alternança Codex ↔ Claude. Aquest document és agent-neutral;
Claude té els deltes verificables
`DELTA_CODEX_a_CLAUDE_22-08-26_ECLIPSE_POSTPROCESSAT.md` i
`DELTA_CODEX_a_CLAUDE_22-08-26_FLATS_POSTERIORS.md`. El delta prioritari nou
és `DELTA_CODEX_a_CLAUDE_22-08-26_BRANCA_DRUCKMULLER_GEMINI_KIMI.md`.

## Arrencada obligatòria

1. Llegeix `../README.md`, `../ESTAT_ACTUAL.md`,
   `../MAPA_RUTES_I_OUTPUTS.md` i `../ACTIVE.json`.
2. Llegeix `AUDITORIA_REPRESA_VIXEN_SONY_2026-08-22.md` i
   `CRONOLOGIA_POSTECLIPSI_2026-08-22.md`. Per a la branca visual prioritària,
   llegeix també
   `AUDITORIA_RECUPERACIO_KIMI_GEMINI_DRUCKMULLER_2026-08-22.md` i el rebut
   `output/auditoria_kimi_gemini_20260822/FINAL_VALIDATION_2026-08-22.md` del
   worktree.
3. Si ets Claude, registra nom, SHA-256, `delta_id` i timestamp del delta al
   teu `CLAUDE_STATUS.md`; un ACK no equival a haver-lo aplicat.
4. Abans d'escriure al worktree, llegeix `AGENTS.md`, `CLAUDE.md`, els dos
   status, executa `git status --short` i adquireix `SERIAL_WRITES`.

## PRIORITAT VIVA 23-08 — PILOT VIXEN BLOQUEJAT A F0/F1

El handoff formal viu del pilot és
`/Users/USUARI/Downloads/Eclipse 2026/.coordination/HANDOFF_2026-08-23_CODEX_PILOT_VIXEN.md`
(SHA-256
`b78b10cdd69db06da5974942dd9370b9b031bdf681d976697dc9c556dfaa8b11`).
L'informe tècnic és
`/Users/USUARI/Downloads/Eclipse 2026/research/98_PILOT_VIXEN_PREFLIGHT_FAIL_CLOSED_2026-08-23.md`
(SHA-256
`c1c6f9374ae35e237c073e7c92a7707b118a40dc1c4e1ff348e1755a1e90a0c0`).

- Autoritat canònica no-clobber:
  `/Users/USUARI/Downloads/Eclipse 2026/output/pilot_vixen_ldic_20260823/20260823T140401Z_preflight_canonical_v4/`.
  `STATUS.json` és terminal `BLOCKED_UPSTREAM_GATES`, SHA-256
  `9e849564dabdb5968c6b2cdfe93b02eec1aed343fb485b136a67612da49861ed`;
  la fase 2 no s'ha executat. Les v1–v3 són predecessores immutables obsoletes.
- Correcció d'inventari: hi ha 124 CR3 vius, no 129; el manifest efectiu de
  68/68 CR3 únics passa integritat i cobreix 15 exposicions.
- F0 falla perquè `+1,019/R²=0,981` és evidència Sony. La Vixen només aporta
  0,1149 % de palanca radial i no identifica independentment l'eix òptic.
- F1 falla perquè 0,424193 px de placa i 0,487192 px de geometria superen el
  contracte de 0,3 px. El valor 0,138859 px només valida cinc parelles, no els
  68 fotogrames, el gir ni la placa completa.
- Ordre de gates: (1) evidència F0 específica de la Vixen o reformulació
  explícita del contracte científic; (2) oracle F1 held-out per fotograma;
  (3) congelar F2; (4) només llavors executar LDIC i auditar el resultat.
- QA: 37/37 proves adversarials, dos revisors independents `CLEAN`, payload
  7/7 i rehash terminal de 519 fitxers / 13.823.377.138 bytes.
- No reprendre automàticament LDIC, composició, Photoshop, Sony, earthshine o
  filtres. La tasca visual antiga continua `PAUSED_BY_PERE`.

## TROBALLA PRIORITÀRIA — DRUCKMÜLLER PYTHON

Pere ha provat els resultats i afirma que **«pinten molt, molt bé»**. Aquesta
és la valoració visual positiva més forta del projecte i Claude ha de
preservar i prioritzar una reproducció controlada del mètode.

- Estat: `HIGH_PROMISE_BY_PERE_PENDING_CONTROLLED_S6_PILOT`.
- Entorn verificat: `/Users/USUARI/Downloads/eclipse_venv`, Python 3.9.6,
  `sunkit-image 0.5.1`.
- Imports: `mgn` des d'`sunkit_image.enhance`; `nrgf` i `fnrgf` des de
  `sunkit_image.radial`.
- Preservació: 51/51 outputs i 72/72 fitxers Antigravity amb snapshot i hash.
- Límit: els TIFF Gemini actuals són `EXPERIMENTAL_NOT_CANONICAL`; parteixen
  d'apilats històrics i no tenen G5.10/G5.11/G7.07.
- Kimi: V4/V4b es conserven, però G5.11 falla. La reparació passa 17/17 proves
  i AST 7/7; els scripts i el verificador bloquegen ordre parcial, G5.10/G5.11
  no vàlids, hashes stale, visibilitat incompleta, clobber i symlinks.

El propòsit dels gates és reproduir fidelment el resultat que Pere troba tan
prometedor sobre fonaments canònics, no descartar-lo.

## Estat efectiu

- La reorganització i la neteja estan tancades i són reversibles.
- `Deprecat` i `No se que fa això aquí` no existeixen i no es recrearan.
- Sis TIFF Vixen absents s'han restaurat; els originals de les arrels
  canòniques continuen invariants:
  572 ARW + 1.139 CR3, fingerprint
  `8d1927d8e2bc5247cbccb5f40a97efa0f67620ff6b50efa6c7b52b89718ba843`.
- Workspaces CapesTotals V2b/V3b/V3c preservats a
  `Derivats/Vixen/CapesTotals_work/`; ja no depenen de `/private/tmp`.
- JPEG/JPG nou d'IA: només `IA/output/`.
- Dos paquets flat posteriors nous viuen a
  `/Users/USUARI/Downloads/Eclipse 2026/output/flats_20260822/`; són
  calibradors candidats/validats no aplicats, no una substitució silenciosa
  dels S6.
- Els 106 JPEG dels flats són al lot recuperable
  `/Users/USUARI/.Trash/Flats_JPEG_Eclipse_2026_20260822T190159Z`;
  zero JPEG a origen i RAW invariants.

Les dues arrels tenen funcions diferents:

- `/Users/USUARI/Desktop/Eclipse 2026`: actius, Photoshop i memòria IA;
- `/Users/USUARI/Downloads/Eclipse 2026`: únic worktree Git, recerca,
  rebuts i output tècnic.

Referència visual exacta de Pere:
`/Users/USUARI/Downloads/Maqueta de resultat esperat.tif`, 110.750.130
bytes, SHA-256
`5d25d4cca0896c04147c75b5b9ad1c0b76a382a00a852fa596371de4c2b69e17`.
És una guia estètica i d'enquadrament, no autoritat científica ni font de
píxels; els artefactes circulars de vora no formen part de l'objectiu.

## Autoritats de represa

### Vixen

`/Users/USUARI/Downloads/Eclipse 2026/output/postprocessat_final_20260822/masters/vixen_s6_ACCEPTED/`

319/319 entrades verificades. Reutilitza només els vuit stacks `STABLE` de
`manifests/vixen_natural_stable_v5.json`; cal resegelar-ne els contractes S6,
no recalcular-ne els píxels.

### Sony

`/Users/USUARI/Downloads/Eclipse 2026/output/postprocessat_final_20260822/masters/sony_s6_ACCEPTED/`

335/335 entrades verificades. `segment_A/8s` és `DSC06987` i
`segment_C/8s` és `DSC06993`; són contribucions independents obligatòries,
encara en quarantena contractual antiga. `DSC06990` queda rebutjada per
moviment intraexposició.

Els HDR/apilats històrics de `Desktop` són context, no substituts dels dos
paquets S6. Les rutes `.../300mm/` dins rebuts antics són procedència
històrica; la ruta RAW viva és `300mm A7RIIIA/`.

## Flats posteriors — autoritat nova però no aplicada

Arrel:
`/Users/USUARI/Downloads/Eclipse 2026/output/flats_20260822/`.

- Vixen: `FINE_SENSOR` validat entre èpoques i en null independent;
  `OPTICAL_RADIAL` bloquejat a F0 pel preflight del 23-08 —contracte/evidència
  de tren incorrectes, palanca insuficient i eix no identificat—;
  full/2-D/pols en quarantena.
- Sony: `OPTICAL_RADIAL` validat contra el donor S6; fine/full/2-D/pols en
  quarantena.
- Cap producte no s'ha aplicat a `Masters_v2`, `vixen_s6_ACCEPTED` ni
  `sony_s6_ACCEPTED`.
- Flat i warp no commuten. Primer cal tancar F0 i F1; si aquests gates passen,
  l'execució posterior haurà de recalibrar RAW originals en una branca nova i
  mai dividir un S6 ja registrat.

Auditoria:
`AUDITORIA_FLATS_POSTERIORS_2026-08-22.md`.

## Artefacte conegut

`composites/sony_cross_train_c_v2` no consumeix cap 8 s i introdueix salts de
contribució a 1,2, 1,5 i 2,0 Rsol. Aquests salts produeixen els arcs marcats
per Pere. No reutilitzis aquesta capa tal qual com a font final.

`CapesTotalsV4b.psb` és referència històrica d'auditoria, no fonament
acceptat: G5.11 falla. `eclipse_natural_editable_v3` és un control tècnic
íntegre però no aprovat, sense 8 s i amb FOV pendent.

## Tasca visual aturada

`PAUSED_BY_PERE`: no reprendre automàticament apilatge, composició, Photoshop
o earthshine. Quan Pere l'autoritzi, l'ordre és:

1. resegelar els vuit Vixen `STABLE`;
2. tancar màscara, null solar i domini de `DSC06987` i `DSC06993` per separat;
3. aturar-se amb `FALTA DECISIÓ DE FOV` fins que Pere decideixi entre el camp
   Sony complet i l'enquadrament de la maqueta;
4. pilot 1:1 Vixen, `+06987`, `+06993`, `+ambdues`, amb diferències,
   ablacions i G5.10/G5.11/G7.07;
5. sobre el mateix compost lineal acceptat, comparar control i MGN com a
   `DETAIL_CANDIDATE`; usar NRGF/FNRGF com a
   `DIAGNOSTIC_VISUALIZATION_CONTROLS`. Cap filtre és `FONT_HDR`; exigir
   nulls, diferències i G6;
6. només després d'un PASS i de la preferència visual de Pere, PSB nou
   no-clobber, editable, natural i amb un únic ajust tonal global suau.

Earthshine continua fora d'abast.

## Retirada reversible i deutes separats

- No buidis sense ordre
  `/Users/USUARI/.Trash/Eclipse2026_cleanup_20260822T151257Z`: 1.014
  fitxers, dos symlinks trencats i 21.809.186.154 bytes lògics.
- No buidis sense ordre
  `/Users/USUARI/.Trash/Flats_JPEG_Eclipse_2026_20260822T190159Z`: 106
  JPEG de flats i 83.361.792 bytes lògics.
- `research/tools/apila_hdr4_vixen.py` encara espera la selecció manual absent
  `~/Desktop/HDR3`; no l'apuntis al directori complet.
- Cinc utilitats CapesTotals V1 encara esperen `v5out/ct1`; no les reutilitzis
  sense entrada explícita o regeneració del compost V5.

## Disciplina d'alternança

- Claude actualitza només `CLAUDE_STATUS.md`; Codex, només `CODEX_STATUS.md`.
- Després de qualsevol canvi d'estat, actualitza `IA/ESTAT_ACTUAL.md`,
  `ACTIVE.json` i aquest handoff sota `SERIAL_WRITES`.
- Deixa un delta o handoff per a l'altra IA amb fets, decisions, paths, hashes,
  proves i pendents. Sense font suficient, usa `QUESTIÓ-PER-A-PERE`.
