# Auditoria de coherència després de V30 — 05-09-2026

Pere demana que les IAs següents no es confonguin ni facin passos enrere.
S'han reconciliat els punts d'entrada de codi i IA amb el lliurament V30.
És una revisió de coherència de la branca de postprocessat, no una nova
certificació de tots els RAW, l'app de captura o els scripts històrics.

## Inconsistències corregides

| Troballa | Canvi efectiu |
|---|---|
| AGENTS deia que no hi ha Git però ordenava `git status` | S'ha retirat aquella ordre; Downloads és arrel de codi sense Git; lock i escriptor únic conservats |
| AGENTS, README i índex enviaven a V28 o al handoff del22-08 | Punter vigent al handoffV30 i research137/138 |
| CLAUDE tenia capçalera d'agost i receptes superades al punt de represa | BlocV30 actual al davant; història expressament separada, sense reescriure resultats antics |
| IA/README, ESTAT_ACTUAL i HANDOFF_VIGENT mantenien S6/Gemini/PAUSED com a feina viva | Reconciliats ambV30; originals congelats abans d'editar |
| ACTIVE.json barrejava pilots d'agost amb autoritat actual | Schema4 amb producte, hash, manifest i estat actuals; objecte anterior complet en snapshot amb hash |
| Mapa de rutes descrivia màstersS6 com actuals | TaulaV30 al davant i mapa anterior marcat com històric; rutes originals preservades |
| IA/NORMES tenia una jerarquia divergent i ordresGit | Jerarquia alineada ambAGENTS/lock/CLAUDE/ACTIVE/handoff; Git retirat de l'arrencada |
| IA/NORMES deia earthshine fora d'abast tot i estar al producte | S'explicita que earthshine i estrelles ja són heretats i no es recalculen en feina dels filtres |
| CODEX_STATUS començava amb un IN_PROGRESS antic | Avís de llegir l'última entrada i el lock; entrades anteriors preservades |
| Skill postprocessat deia que el viu era CapesTotalsV24 | Resolució dinàmica viaACTIVE/handoff; brancaV29/V30 diferenciada dels runsRAW |
| Skill descrivia tota peça fora de cadena com sense manifest | Ara identifica les branques manifestades i els seus rebuts |
| TaulaC prescrivia CORONA sola ambNRGF a tot radi | ReceptaV25/V26 marcada històrica; evidència133 i fontsTOTAL dels manifestsV29/V30 |
| H1 verd podia induir a donar per bons els minicercles | Nova família d'anisotropia i referència amb ablacions, transferència i altre tren fix |
| `etapa6_compara_brno.py Vxx` canviava etiqueta però no fontsV27 | Advertència als punts d'entrada i nou `v30/compare_brno.py` amb compostos reals, hashes, color coherent i controls |

Les dues skills tornen a explicitar la precaució de Pere: probablement les
retallades circulars fan més mal que bé, perquè poden eliminar corona i crear
halos. No es converteixen els radis del diagnòstic en màscares. Sigma4 és un
paràmetre deV30 amb resposta mesurada, no un valor universal per futurs eclipsis.

## Traçabilitat

- `research/tools/v30/docs_before/`: còpies anteriors dels documents editats;
  `skills_codex_before/`: còpies anteriors de les skills globals modificades.
- `research/tools/v30/authority_changes.json`: hashes abans/després dels12
  punts d'entrada reconciliats. El diari propi pot tenir una entrada posterior
  de RELEASED; el hash de reconciliació és una instantània, no una promesa
  d'immutabilitat del diari.
- `research/tools/v30/skill_sync_receipt.json`: hashes de les còpies
  sincronitzades local/Codex; validació de frontmatter i estructura passada.
- `research/tools/v30/delivery_manifest.json`: identitat del PSB i codi;
  `final_audit.json`: verificació final dels punts d'entrada i requisits.

No s'ha tocat CLAUDE_STATUS, RAW, runs019/016 ni els caus V29. El handoffV28
i els informes antics continuen disponibles com a evidència. La nova
autoritat no reinterpreta els seus PASS com a validacions deV30.

## Límits que han de continuar visibles

1. V30 suavitza minicercles; no certifica que hagin desaparegut tots. Les
   variants ocultes tenen costos de detall i els avisosH1b es declaren.
2. El reforç del gra exterior no és més corona resolta. Brno no valida
   V29/V30 més enllà de5R en la vara actual; V27 hi obté correlació millor.
   No hi ha superioritat globalV30 ni permís per retallar aquest camp.
3. El PSB és una fotografia editable. No s'han tornat a calibrar RAW ni
   resolt deutes de tempsEXIF, darks tèrmics o variància per canal.
4. El llenç10551×7506 és el mateix. Ampliar-lo és una decisió futura deFOV;
   el gate històric de FOV no ha d'aturar la represa del producte ja demanat.
5. Els scripts de reconstrucció refusen sobreescriure V30. Per reproduir,
   cal una destinació nova i declarada, dependències verificades i un nou
   claim; no una ordre de repetir automàticament els scripts sobre el viu.

La tasca no deixa una campanya desatesa ni feina automàtica pendent. La
següent instrucció de Pere es treballarà sobreV30 i el seu manifest.
