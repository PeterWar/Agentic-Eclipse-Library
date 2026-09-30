# Eclipse 2026 — context canònic per a Claude

Última actualització efectiva: 07 de setembre de 2026 (handoff Codex → Claude, revisió de marques V31). El projecte és en fase
**post-eclipsi**. El bloc inicial d'aquest document, `AGENTS.md` i el traspàs
vigent substitueixen qualsevol indicació de represa datada que aparegui més
avall. Les seccions antigues es conserven com a història i disseny de captura;
no són una cua de feina viva.

## 0. Reorganització d'actius del 22 d'agost

El codi canònic, sense Git des del02-09-2026, continua exclusivament a `/Users/USUARI/Downloads/Eclipse
2026`, però els actius fotogràfics i Photoshop vius s'han reorganitzat sota
`/Users/USUARI/Desktop/Eclipse 2026`. Abans de qualsevol feina
post-eclipsi sobre imatges, llegeix completament
`/Users/USUARI/Desktop/Eclipse 2026/IA/README.md` i segueix el mapa de
rutes que indexa. El backup anterior és
`/Volumes/4TB/Eclipse 2026-22Agost/Eclipse 2026` i no és una arrel de treball.

No interpretis les rutes de Desktop que apareixen més avall o en documents
datats com a rutes vigents sense resoldre-les amb
`/Users/USUARI/Desktop/Eclipse 2026/IA/MAPA_RUTES_I_OUTPUTS.md`. Els rebuts
històrics conserven les rutes originals i no es reescriuen.

## 1. Punt de represa

⏭️ **09-09-2026 — V39 LLIURADA: `.coordination/HANDOFF_2026-09-09_V39.md` i `research/156_V39_SOROLL_DELS_FILTRES_GUANY_WIENER_SOROLL_MESURAT_20260909.md`.** Per ordre de Pere (/goal V39 des de `V38_everythingNOTawesome.psb`). `/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V39.psb` (SHA-256 `fcf3b386660d5bd07f94a3cd3cd2f9cab622fb7edede28cc53446416847c7570`, OBRE 10551 px x 7506 px · 38 capes; 9,107,558,966 bytes). Causa del soroll fora de la corona: MGN i WOW normalitzen cada escala per la seva energia LOCAL (on domina el soroll l'amplifiquen a contrast unitat); l'ACHF en part; mesurat en meitats, de 3,5 R☉ enfora el 90–100 % de l'energia de les bandes ≤ 20 px és soroll. Cura dins dels operadors, per BANDA entre σ consecutives: g = max(g_Auchère, g_creuat) — llindar tou erf(|w|/(√2·k·σ_banda)) amb k = 2 i el soroll MESURAT de la banda (meitats de fotogrames alternats, ⛔ no els mapes var_*; per canal a l'ACHF), i el terme CREUAT (potència que Vixen i Sony veuen alhora / potència de la fusió: els sorolls dels dos sensors són independents). τ = 0 → V38 exacta. rms a 3,5–5 R☉: P03 0.245→0.151, P04 0.172→0.133, P05 0.137→0.109, 01 0.041→0.029, 04 0.045→0.025, 06 0.051→0.042. ⛔ TRES RECTIFICACIONS: (1) el «jutge extern» de les V34–V38 (Vixen original a 4 finestres) NO era independent (pes Vixen 0,37–0,44 a la base; cap finestra amb pes < 0,03): el jutge independent és BRNO (mètode v30 congelat; `c3c_jutge_brno.py`; a 3–5 R☉ Brno×Brno només 0,38); (2) l'estimador de soroll per meitats és INVÀLID als 16 px de la vora del forat lunar (les meitats hi tenen la vora a sub-píxel: ×32 a 1 px) i feia un anell al limbe → `comu39.lluny_del_forat`; (3) un guany per PASSA-ALT atenua l'estructura confirmada quasi tant com el soroll (cov ×0,4–0,7) encara que la correlació es conservi → guany per banda + creuat. Jutge Brno (3–5 R☉, 1°): P03 corr +0.07→+0.09 (transf. n/d, rms ×0.64), P04 corr +0.34→+0.39 (transf. 0.96, rms ×0.84), P05 corr +0.21→+0.26 (transf. n/d, rms ×0.78), 01 corr +0.24→+0.27 (transf. 0.97, rms ×0.83), 06 corr +0.32→+0.33 (transf. 1.01, rms ×0.96); a 1,2–3 R☉ transferència 0,95–1,00 a totes les capes. PORTES DECLARADES (Codex ronda 3, PARCIAL): injecció A3b NO passa a les cel·les d'1 %/2 px (0,73–0,82; 36 de 135 < 0,90; cota inferior: el creuat no veu injeccions); H1 de 01/04/05 (0,077/0,063/0,056) HERETAT de la V38 (idèntic), H1b millora; el creuat pot inflar coherència a 2,0–2,4 R☉ prop de l'entrada de la Sony (efecte ≤ 0,1 al guany: el llindar ja hi val 0,89–1,00); guarda sense nul empíric. Per això la V39 és CANDIDATA amb portes declarades, no successora certificada. Bases de pantalla amb la corba declarada (total visible, cel/4 oculta; recepta V29 new_tone). Capes tal com Pere les va deixar; 02 passa-alt i P06–P09/C01 DEPRECATS; P01b en ln r. RHEF no tocat. Judici de Pere obert.

⏭️ **08-09-2026 (nit) — V38 LLIURADA, PROJECTE COMPLET: `.coordination/HANDOFF_2026-09-08_V38.md` i `research/155_V38_LLUNA_A_L_INICI_FRANJA_A_LA_FONT_I_PROJECTE_COMPLET_20260908.md`.** Per ordre de Pere («fem A… fes la V38 ja amb totes les capes… munta-ho tot en un projecte»). `/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V38.psb` (SHA-256 `f74b25a72c65595ae74e56a41ec8f0d85b1db578ce1ca818fd9e8e6ffc87687f`, OBRE 10551 px x 7506 px · 42 capes; 10,435,812,802 bytes). **La Lluna (earthshine ×4 + Reflex, R 455,5 px) és a l'INICI de la totalitat** (t 15 s, centre a (+14,8, +0,9) px del Sol; desplaçament (+15, +1)); totes les capes de base i de filtre porten màscara = fora d'aquest disc (+2 px). Així la flamarada de l'oest i la cromosfera queden senceres i les miniflamarades del SE queden sota el disc (opció A; la D —dos instants declarats— anotada com a millora possible al bloc de tasca futura). ⛔ RECTIFICACIONS: el forat és la INTERSECCIÓ de les posicions lunars (no la «unió»); la franja de l'oest NO té gra ×10: són 15–17 fotogrames (soroll ×2–2,6) i els 3–4 primers anells són CROMOSFERA vista per 2–10 fotogrames de 1/3200 s; cap arc coherent d'1 px. L'únic biaix real (dèficit de llum de cada fotograma prop de la SEVA vora lunar, −7 % a 2,5 px als curts) es corregeix a l'origen (B2) amb taula mesurada; fusió idèntica a la V36 a r > 1,12. Capes: 13 de Pere, Fons per raig, Estrelles byte a byte; bases V32 ocultes; base lineal V38; 03 r0/r4/07 (recepta V32 recuperada), 01/02/04/05/06, P01 (+ P01b μ/σ extrapolats, oculta), P02–P05 (recepta V37); P06–P09/C01 de la V32 ocultes. Judici de Pere obert.

⏭️ **08-09-2026 (vespre) — V37 LLIURADA: `.coordination/HANDOFF_2026-09-08_V37.md` i `research/154_V37_LIMBE_CONDICIO_DE_CONTORN_I_FRANJA_20260908.md`.** Per ordre de Pere («els d'a prop del limbe els veig claríssims»). `/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V37.psb` (SHA-256 `9706226c1878c836038cbb1afecefb5b7a9d990ab010aecf3159749a3d6385ec`, OBRE 10551 px x 7506 px · 11 capes; lleugera; base V36 idèntica). Mesurat: (1) les capes ACHF 01–06 estaven SATURADES al voltant de la Lluna per la mitjana d'un sol costat contra el forat (|d/escala| > 25 al limbe, > 1 fins a 1,08–1,16 R☉; banda sense estructura; des de la V29) → condició de contorn al forat també per a l'ACHF de cadena; (2) el rivet clar del MGN/WOW a la vora del forat era el farcit V35 extrapolat des del primer anell SENCER amb un pendent 7× més suau que el del limbe → farcit B (mitjanes dels anells parcials conservades, pendent local que decau); (3) la FRANJA de la unió temporal de la Lluna (oest, 1,005–1,046 R☉, 18 px): 13–16 fotogrames, pes 3–4× menor, gra 7–9 % (10×): tots els filtres la mostren; la norma del 27-08 la conserva; **DECISIÓ PENDENT DE PERE** (conservar o forat circular al radi màxim de la unió). Refusats amb número: dues màscares (rivet 9,7 σ), NRGF amb μ/σ extrapolats (5,2 σ). Judici de Pere obert. ⏭️ **08-09 (nit): les DUES versions existeixen perquè Pere triï** («les vull veure i després decidir»): `V37.psb` (franja conservada) i `V37_forat_circular.psb` (SHA-256 `59ac0b98c9a37257c406892258b3d8294573a1a9a6b23071ac4cf68a0d3cf85f`, OBRE 10551 px x 7506 px · 11 capes; forat circular a 1,046 R☉, mateixa recepta; NO és una cura, és enquadrament; rebut `V37_forat_circular_REBUT.md` al costat; eines `research/tools/v37fc_20260908/`). Quan Pere triï, l'altra s'arxiva.

⏭️ **08-09-2026 (tarda) — V36 LLIURADA: `.coordination/HANDOFF_2026-09-08_V36.md` i `research/153_V36_MARQUES_V35_VORA_8S_I_ANELLS_DISCRETS_20260908.md`.** Per ordre de Pere («mira V35_Artefactes»: petits artefactes al limbe). `/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V36.psb` (SHA-256 `fb3f3cefd9492eb8740315b1e567c447787f6af8b3504a6d2a36e5d11385d1bf`, OBRE 10551 px x 7506 px · 11 capes; lleugera). Marques V35 (26): el QUADRAT gruixut del P05 i la franja del 06 a 3,3–3,8 R☉ són la vora d'entrada dels 8 s de la Sony (quadrat arrodonit pel VINYETATGE del 300 mm sobre el cel; gra −35 % en ~110 px) → dues cures provades i REFUSADES (finestra quadràtica dels 8 s: +14 % de gra a tot el camp; esvaïment espacial 900 px: bony +30 % en 1200 px): residu declarat d'origen de captura (salt ×4); els arcs del NRGF a 1,04–1,06 = pics d'anells d'1 px a l'oest (residu; la compleció dels anells parcials del forat es va provar i refusar); les línies horitzontals de la RHEF = bandes de fase del rang discret prop dels eixos → rang en radi continu. ⛔ **ERRATA V34/V35: la LUT de linealitat Sony NO s'havia aplicat mai (`run.tren == 'sony'` contra `SONYTOT`)**; la V36 l'aplica. Guardarail nou (152 §5.12): cap canvi declarat sense prova que ha entrat. Farcit dels operadors isotròpics: el de la V35 (dues alternatives refusades en ROI, A8); residu fi al limbe oest = franja de la unió temporal. Judici de Pere obert.

⏭️ **TASCA FUTURA (Pere, 08-09-2026): «quan tinguem la certesa que hem acabat la feina»**: (1) convertir les tres trampes recurrents en assercions de codi (distància a una vora només sobre suport PLE; operadors isotròpics només amb condició de contorn al forat lunar; cap geometria sense prova azimutal + control nul al rebut) i fer-les córrer a `replica_v35.sh` i a tota fusió; (2) fitxa d'alta d'un tren nou per al 2027 i per a fotos d'amics (què demanar: RAW, darks, flats o dither, focal, lloc/hora/seguiment; què mesurar: pedestal, saturació, placa i nord, linealitat, ghosts). No és feina viva fins que Pere ho digui. Memòria `tasca-futura-assercions-i-fitxa-tren-nou`. ⏭️ **MILLORA POSSIBLE (Pere, 08-09 nit): l'opció D del limbe** — la Lluna a l'INICI (t 15 s, flamarada de l'oest sencera) i, al SE (az +31…+50°), la corona de la franja (dada dels últims fotogrames) dibuixada per SOBRE de la vora del disc perquè les miniflamarades també es vegin: compost de dos instants, lícit només declarat al rebut. No és la V38 (que és l'opció A: Lluna a l'inici, franja de l'oest curada a la font).

⏭️ **08-09-2026 (matinada) — V35 LLIURADA, curada a l'ORIGEN: `.coordination/HANDOFF_2026-09-08_V35.md` i `research/151_V35_VORA_VIXEN_FORAT_I_LIMBE_20260908.md`.** Per ordre de Pere («Mira V34_artefactes i fes V35»; MGN: la majoria fora, documentat a 151 §1; nou artefacte: contorn del FOV Vixen a tots els filtres; P05 mai corregit). `/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V35.psb` (SHA-256 `50c8e1cfb7144794db67c227324238fb33b9ccaf91502ff33fb6f954692aa6d4`, OBRE 10551 px x 7506 px · 11 capes; lleugera). Mesurat a la font: la Vixen anava −2,9 % a la seva vora (ρ ajustat només a 1,5–4) i el seu pes queia 0,36→0 en 160 px (graó −0,8 % de nivell i 30 % de gra a la base); ⛔ la V34 tenia la TRAMPA DEL FORAT LUNAR a `distanceTransform` (la Sony entrava al 96 % a 1,0–1,1 R☉); el «recurrent» del P05 (i P03/P04) és la mitjana local D'UN SOL COSTAT dels operadors isotròpics contra el forat (biaix 4–7 σ al limbe) i, al WOW, la còpia de la silueta del forat a ±2^s (rectangles). Cures: suports plens, δ σ256 (Vixen→Sony·ρ, residu G 1,10→0,39 %), esvaïments 720/480 px, relleu 1,9→3,5, condició de contorn declarada als operadors (biaix P05 3.0→0.1 σ). Queden: entrades dels fotogrames (captura), anells blaus, taca NE. Judici de Pere obert. ⏭️ **Replicació (08-09, matinada 2): `research/152_REPLICACIO_DETERMINISTA_RAW_A_V35_20260908.md`** (mapa RAW→V35 E0–E6, paràmetres congelats, portes, història d'errors i cures, guardarails per a LLM); `research/tools/v35_20260908/replica_v35.sh` + `verifica_replica.py` + `frozen/` (inventari de hashes, paràmetres, modes/màscares fora del PSB). Rèplica real feta: E5+E6 **bit a bit idèntiques**, PSB amb el mateix SHA.

⏭️ **07-09-2026 (nit) — V34 LLIURADA, curada a l'ORIGEN: `.coordination/HANDOFF_2026-09-07_V34.md`, `research/149` (causa) i `research/150` (rebut).** `/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V34.psb` (SHA-256 `fa49221cad3352c4e4e7840018ee305e7ec360b3aad4e28c6c175ea3f0d50917`, OBRE 10551 px x 7506 px · 11 capes; lleugera: base lineal V34 + 10 filtres amb la recepta V32, cap suavitzat). Tres canvis a la composició: finestra d'entrada gradual (0,35→0,85 sat), LUT de linealitat de la Sony (mesurada: −0,5 % del 60 al 85 %), fusió per variància (A+B acceptada per porta contra la Vixen; Vixen mai per sota de la V32, afegida de 2,65 enfora). NRGF/RHEF amb anell sencer a la vora del llenç. Gra de la base −30…−44 % de 2,5 a 6 R☉ sense cap suavitzat; graons d'entrada atenuats; +14 % a 2,0–2,1 declarat. Judici de Pere obert.

⏭️ **07-09-2026 (nit) — LA V33 QUEDA RETIRADA; causa mesurada a `research/149`.** Els 29 traços de `V33_Artefactes.psb` són costures fabricades pel suavitzat de la V33 (a 1:1 la V32 hi és uniforme; `V32_vs_V33_*.png`). A sota, mesurat a la font: nivells plans (≤ 0,1 % als 2 s/10 s), Vixen lineal fins al sostre (±0,13 %), **Sony NO lineal (−0,5 % del 60 al 85 % de saturació, −1,2 % al 92 %)**, resolució igual (2–6 %), i **el gra cau del 40 % en 40–140 px on entren els fotogrames** (pesos ∝ t amb salts de 5×) i **puja un 54 % al canvi de tren per radi (2,0–2,65)**. ⏭️ V34 a l'origen: LUT de linealitat Sony, entrada gradual (35→85 %), fusió per variància entre trens i apuntaments amb porta contra la Vixen, filtres amb la recepta V32, cap suavitzat. Producte vigent: V32.psb.

⛔ **NORMA DE PERE (07-09, nit): cap correcció estètica d'un artefacte sense atacar-ne la causa a l'origen, i cap sacrifici de detall per eliminar-lo.** La V33 (suavitzat S/N fins a 30 px a fora) queda REFUSADA com a mètode: els artefactes hi continuen (`V33_artefactes.psb`). Ordre obligat: mesurar a la font fins a tenir la causa → curar-la allà → regenerar filtres amb la mateixa recepta.

⏭️ **07-09-2026 (vespre) — V33 LLIURADA (lleugera): `.coordination/HANDOFF_2026-09-07_V33.md`.** Per ordre de Pere («fes la V33»; taronja = zona pixelada sense detall). `/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V33.psb` (SHA-256 `79424a49c459953ce02b8ae26d9c0400bdb524861eaa0a38c31b617d9f6b33f3`, OBRE 10551 px x 7506 px · 11 capes): base lineal V32 + 10 filtres iterats. Dos canvis, només als filtres: **resolució que segueix el S/N** (σ = max del mapa mesurat per coherència entre trens λ_mín/4, i f3.suavitza_sn; 0,7 a l'interior, 13,5 px a 4 R☉, 30 a 8: gra fi 10–100× més baix) i **NRGF/RHEF sense la vora del llenç** (anell sencer estimat per la forma azimutal dels últims anells sencers; cercle a 8,5 R☉: +0,89 → +0,20 NRGF, +0,66 → 0,00 RHEF). V32.psb intacta. Judici visual de Pere obert.

⏭️ **07-09-2026 (tarda) — REVISIÓ DEL PSB ANOTAT DE LA V32: `.coordination/HANDOFF_2026-09-07_MARQUES_V32.md` i `research/147_REVISIO_MARQUES_V32_20260907.md`.** Pere ha pintat 78 components en 10 de 22 capes (64 de les 137 marques de la V31 ja no hi són: la diagonal i el gramòfon de 3,2–4,6 R☉, que a la vista polar la base V31 té i la V32 no). Mesurat a la font amb control nul aparellat: **l'interior (1,15–2,3 R☉, 36 liles + 3 verds) és CORONA** (correlació 2D Vixen×Sony B al traç mediana +0,67, nul −0,01; el nul no exclou cel comú, i de 1,9 R☉ enfora l'argument és que la correlació cau on el cel puja); el que els filtres hi afegeixen són graons de GRA a les entrades dels fotogrames (−13…−24 %), no de nivell. Els arcs de 3,6–4,7 de 05/06 no tenen cap estructura a cap tren (correlació +0,01): és la vora on el filtre passa d'streamers a gra. Els cercles de NRGF/RHEF a 8,44–8,68 i 11,56–12,04 són la VORA DEL LLENÇ (8,47/8,57/11,78/12,17 R☉). La taca taronja de la RHEF és el gradient del cel ordenat per anells (idèntic a la V31). Taca NE: −0,12 % (z −2,2) només a la Sony B, no es pedaça. De passada: anells del CANAL BLAU de la Vixen (±2–3 % a 1,1–2,0 R☉, V29 1,31 % → V32 0,96 % rms) i discrepància A/B de la Sony (±2–3 %). ⏭️ V33 (norma: només filtres, una base lineal): NRGF/RHEF amb estadística d'anell llisa més enllà de la vora del llenç i cel restat; 04/05/06/MGN/WOW amb resolució/guany que segueixin el S/N mesurat (A8); interior i verds: res a tocar. Cap PSB modificat.

⛔ **NORMA DE PERE (07-09-2026, després de la V32): mentre quedin artefactes als filtres, cada versió nova itera NOMÉS sobre els filtres amb UNA sola capa base linealitzada; no s'arrossega el projecte no-linealitzat sencer (40 capes, 9,6 GB per versió és «una pèrdua de temps i espai»).** Empaquetador lleuger: `research/tools/v32_arcs_20260907/b6b_psb_lleuger.py`. La versió completa, només quan Pere la demani.

⏭️ **07-09-2026 (nit) — V32 LLIURADA: `.coordination/HANDOFF_2026-09-07_V32.md` i `research/146_V32_ARCS_A_LA_FONT_20260907.md`.** Per ordre de Pere («nova versió de tots els filtres eliminant els artefactes lila i blaus»). Els arcs tenen tres causes mesurades a la FONT: fronteres de fusió HDR amb desnivell entre fotogrames (interior 1–2,2 R☉ Vixen; 8 s Sony a 2,6–2,8), **l'ondulació fina del flat radial de la Sony impresa invertida a cada fotograma (arcs de 3,2–4,6 R☉, centrats al centre del sensor a 0,5 R☉ del Sol)**, i el guany escalar entre trens amb tall sec a la vora. Cura a l'origen (camps per fotograma, flat suavitzat σ32, ρ 2D, ploma) i 18 filtres regenerats amb les receptes exactes: `/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V32.psb` (SHA-256 `dcfc8f531e286bfdf529d20880c9772785a38a4e6d0c09094883a7c8f7743c7d`, OBRE 10551 px x 7506 px · 40 capes). V31_FiltresPurs preservada. Abans/després al `V32_REBUT.md`. Judici visual de Pere obert; deutes: registre dels fotogrames llargs Sony, flat a F0.3, taca NE.

Pere ha demanat explícitament continuar amb Claude per economitzar tokens de Codex. **Handoff consolidat vigent:** `.coordination/HANDOFF_2026-09-07_CODEX_A_CLAUDE.md`. Començar per aquest document i `research/145_REVISIO_MARQUES_V31_20260907.md`; guia amb les 19 capes i comparacions a `output/revisio_marques_v31_20260907/lliurables/RESULTAT.md`.

Revisió del PSB anotat acabada: groc/blau/lila són artefactes confirmats per Pere, les vuit components verdes continuen dubtoses. La diagonal groga és interna a la cobertura (383–454px de distància mediana al límit); hi ha diverses famílies de contorns, també interiors. La coincidència local Vixen/Sony a les verdes no valida cada ondulació. Cap correcció aplicada; els dos PSB intactes. La recerca contínua2D i geomètrica de143/144 no ha promogut cap remei; circularitat perfecta i centre comú dels arcs visibles continuen indeterminats. Les noves capes pures no hereten H1/rho40/contrast120/sigma3 de les antigues01/02. Cap experiment en curs ni feina programada.

La documentació IA de Desktop conserva el lliurament fotogràfic del06-09, que no canvia. Aquest handoff actualitza la represa de recerca/revisió; abans d'escriure, consultar el RELEASED de CODEX_STATUS i adquirir un claim propi.

### Producte fotogràfic vigent — lliurament del06-09-2026

V31 comparativa de filtres independents és el lliurable actual: `/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V31_FiltresPurs.psb`.
10551 × 7506, RGB16, 40 capes; 9,593,292,748 bytes.
SHA-256 `89d509bcc53982307cf9e3d78b0a84ed7548f4045e8cbb95d9f8594e4e877dfd`.

Les 30 capes anteriors i el compost inicial són exactes; s'afegeixen 10 vistes Normal100%, apagades. Base comuna G corregida i match global Sony→Vixen0,3411462604999542. NRGF, RHEF, MGN, WOW/bilateral, NAFE, precursor ACHF16/32, SWAP pilot i control passa-alt. Cap H1/tanh/suavitzat extern ni retall circular als mètodes nous; operacions intrínseques i discretització documentades.

És una comparació amb limitacions visibles, no una correcció certificada de tots els arcs. RHEF pot crear bandes; hi ha arcs de la base, soroll exterior i resposta forta d'ACHF al limbe. FNRGF queda com a array de domini vàlid; no s'inventen sectors. Inventari i exclusions justificats a `/Users/USUARI/Downloads/Eclipse 2026/research/142_V31_FILTRES_PURS_20260906.md`.

Photoshop real: OBRE 10551 px x 7506 px · 40 capes. Les 30 capes originals i tots els nous RGB/màscares verificats. Els documents V31.psb/V30.psb estaven oberts amb canvis sense desar i no s'han substituït. Backup de disc: `/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V31_abans_filtres_purs_20260906.psb`.

Handoff: `/Users/USUARI/Downloads/Eclipse 2026/.coordination/HANDOFF_2026-09-06_V31_FILTRES_PURS.md`. Manifest: `/Users/USUARI/Downloads/Eclipse 2026/research/tools/v31_purs/delivery_manifest.json`. Guia i vistes: `/Users/USUARI/Desktop/Eclipse 2026/IA/output/v31_purs_20260906`. No hi ha tasca automàtica nova; l'avaluació visual de Pere resta oberta.

### Història de la V31 anterior (05-09-2026)

V31 és el lliurable editable actual: `/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V31.psb`.
10551 × 7506, RGB16, 30 capes; 6,193,861,172 bytes.
SHA-256 `bbbb2b93a49a0e09226b89467754f6364d1c6b929bc147bd34387a1c66d7affe`.

Pere ha precisat que veu els minicercles només als filtres NO azimutals.
V31 suavitza les capes 01, 02, 05 i 06 amb una gaussiana cartesiana de sigma
3 px, i la 04 amb sigma 1,5 px. Les altres 25 capes, incloses les azimutals
03 i 07, són íntegrament idèntiques. Les 30 màscares, alfa, opacitats,
visibilitats i ordre es preserven. V30 queda immutable. No hi ha retall
circular, canvi de FOV ni nou perfil radial.

H1 passa als cinc filtres, inclòs el limbe parcial; H1b conserva avisos a 01,
04 i 05. El suavitzat també atenua detall real petit: sigma 3 conserva
aproximadament un 74–75% del coherent a 16–32 px i un 92% a 32–64 px en
quatre finestres interiors.
No s'afirma eliminació completa de minicercles ni validació del gra exterior.
Reobertura de canals, recomposició amb error màxim d'1 DN16 i obertura de les
30 capes a Photoshop comprovades. L'acceptació visual final de Pere queda pendent.

Handoff: `/Users/USUARI/Downloads/Eclipse 2026/.coordination/HANDOFF_2026-09-05_V31.md`. Explicació: `research/139_V31_mes_suavitzat.md`.
Manifest: `/Users/USUARI/Downloads/Eclipse 2026/research/tools/v31/delivery_manifest.json`. Vistes: `/Users/USUARI/Desktop/Eclipse 2026/IA/output/v31_20260905`.

### Història anterior a V31 (no instruccions de represa)

V30.psb és el lliurable visual actual, creat el 05-09-2026: 10551 × 7506,
RGB16, 30 capes, 6,233,044,488 bytes. SHA-256 `0d1f23fe5c56acf60bb35d3e24acea02fffaaf333d04d7a3aa17e0aac4f3f8c0`.
Ruta: `/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V30.psb`.

Conserva les 25 capes de V29 corregida: píxels, alfa i màscares idèntics.
01 ACHF fi 2–32 i 02 Passa-alt24 acceptades per Pere continuen visibles.
La 03 V29 original es conserva oculta; la 03 V30 visible regularitza radialment
l'operador azimutal amb sigma4 px. 07 sigma8 és una alternativa més suau,
oculta. 04 micro1–16, 05 fi2–48 i 06 estructura4–64 són alternatives ocultes
del01; activar-ne una substituint el pare evita sumar contrast involuntari.

Minicercles suavitzats, no eliminació total certificada: RMS radial4–32 px
de quatre zones a0,476–0,550 de V29 amb03r4. La resposta injectada relativa
és0,967–1,011 a longituds96/160/256 px; r8 atenua96px a0,873–0,891 i ho
declara. No hi ha tall circular nou ni canvi de llenç/FOV. H1 i geometria
passen; avisos H1b declarats. Reobertura de canals, recomposició i Photoshop
real comprovats al rebut. El judici estètic final de Pere continua obert.

Represa: `/Users/USUARI/Downloads/Eclipse 2026/.coordination/HANDOFF_2026-09-05_V30.md`; explicació `research/137_V30_minicercles_i_variants.md`,
auditoria `research/138_V30_auditoria_coherencia.md`, manifest
`research/tools/v30/delivery_manifest.json`. Les fotos Brno són jutges, mai
fonts de píxels. La comparació exterior >5R no valida el gra ni tota la corona.

Les entrades següents conserven la història, també errors després corregits.
No són una cua vigent ni autoritzen retalls, inpainting, fades o reprendre un
pilot antic. La constatació sobre Git del02-09 queda substituïda per AGENTS.

### Història anterior a V30 (no instruccions de represa)

⏭️⏭️⏭️⏭️⏭️⏭️⏭️⏭️ **02-09-2026 — AUDITORIA GENERAL DEL PROJECTE I PLA PER AL
2027: `research/129_AUDITORIA_GENERAL_I_PLA_2027_2026-09-02.md`.** Per ordre
de Pere (balanç, què ha funcionat i què no, quatre esperances: més detall,
Eclipse Command 2027, web meteo 2027, automatització). Deu lectors, sis
síntesis, verificació adversària parcial (76 de 117 agents; §14 del 129).
⛔ **Va costar el 21 % del pressupost setmanal de Pere: cap flux massiu
d'agents més.** Conclusions que manen: (1) el detall que falta és a la BASE,
no a cap fotograma: compost LDIC lineal a la graella de la V23 amb les capes
de Pere a sobre byte a byte, i la corba declarada com a última passa (el PSB
no es pot linealitzar); (2) Claridad/Neblina no estan mesurats al projecte
però fabriquen halos per construcció (radi gran sense perfil radial, vores de
màscara, per canal): la pila lineal NRGF→ACHF→mediana→S/N→fons per raig +
capes Superposar ho substitueix, i cal la prova A/B amb la mateixa vara;
(3) la V1.02 no cobreix 271 s (porta 60-110, blocs Sony 200 s, sostres de cua);
(4) la web 2027 és en mode proves amb restes del 2026; (5) **el risc més gran
és la còpia: un sol disc, `.git` amb ~173 GiB de brossa, res commitat des del
23-08**. ⏭️ **Les dues skills s'han reescrit** des de `cadena.py`
(`normes_i_portes.md` nou amb les normes de Pere i la taula de portes;
`trampes_INDEX.md`); còpia de Codex sincronitzada. Les 11 preguntes a Pere
són al §13 del 129.
⏭️⏭️⏭️⏭️⏭️⏭️⏭️⏭️⏭️⏭️⏭️ **05-09-2026 (matinada) — LA V28, EL CAMP DE BRNO I LA CORONA SOLA QUE MENTIA: `research/133`.** Objectiu de Pere: comparar amb les fotos finals de Druckmüller, «falta camp», iterar. Mesurat anell a anell (mètode del 114): ⛔ **la corona sola de la descomposició de color s'anticorrelaciona amb Brno de 5 R☉ enfora (−0,8)** mentre que **el TOTAL (corona + cel) segueix el 200 mm de Brno a 0,75-0,80 fins a 8,6 R☉**: de 4 R☉ enfora el detall es treu del TOTAL, mai de CORONA_c. El camp que faltava era dels esvaïments (fi 3,5→5, gran 4→5), no de la cobertura (la Sony arriba a 13,7 R☉ al llenç; a la V23 les cantonades > 9-11 R☉ són de les capes 12/13 de Pere: llenç més gran = deute). V28: capa `04 ACHF ample 9R` (passa-alt azimutal 256-1024 px d'arc, font híbrida, 3,5·MAD per anell) fins a 9,6 R☉, base cel/4 VISIBLE (com Brno), els sis ghosts de Pere esborrats a l'ORIGEN (`etapa0_ghosts_llenc.py`), la capa ampla pel tall del ratllat i sense pedaços. Tota versió es mesura amb `etapa6` (correlació i contrast per anell contra Brno) abans de lliurar. Traspàs a Codex: `.coordination/HANDOFF_2026-09-05_CODEX_V28.md`.
⏭️⏭️⏭️⏭️⏭️⏭️⏭️⏭️⏭️⏭️ **05-09-2026 — LA V27: LA GEOMETRIA DE LA V25/V26 ESTAVA GIRADA 138,5°: `research/132`.** Pere ho va dir dues vegades («girades») i les meves proves (48 finestres de fase a 1,5 px, escaquer, forat lunar) deien 0,0 px: totes rotació-invariants (el gradient radial dona «0,1 px» amb la imatge girada 93°). ⛔ **La prova que ho veu és la correlació circular en AZIMUT del perfil polar** (pic a −138,5°, també als renders del Photoshop via JSX). Geometria refeta (`etapa2d`): −46,6° OpenCV, centre en polar, escala 1,0 declarada; validació azimutal ≤0,5° a tres capes, control nul, i el forat lunar de la cadena a 2,5 px del disc C2. **Norma nova: tota geometria porta la prova azimutal + control nul; mira les vistes en polar.** Marques de Pere als filtres: els arcs concèntrics del detall gran (graons HDR amplificats) → passa-alt NOMÉS azimutal; el ghost de 3 R☉ → inpainting a l'origen abans de tots els filtres (cap moneda). Noms curts (`V27.psb`, «00 Base», «03 ACHF gran azimutal»…). ⛔ La V26 no s'ha de fer servir.
⏭️⏭️⏭️⏭️⏭️⏭️⏭️⏭️⏭️ **04-09-2026 — LA V26 I LA SKILL `corregeix-artefactes`: `research/131`.** Pere sobre la V25: «els filtres són magnífics, un pas de gegant» però (1) «les capes linealitzades no estan alineades, girades» i (2) «plens d'artefactes» (marques a `~/Downloads/Artefactes.tif`). ✅ **L'alineació és 0,0 px** contra les seves capes 10 i 09 (correlació per finestres i escaquer `V26_PROVA_SUPERPOSICIO_escaquer.png`); el desplaçament de 7-9 px que es veu a la fusionada V24 és de les capes 01-03 en QUARANTENA però visibles — ⏭️ cal preguntar-li contra quina capa va mirar. Els artefactes, un a un: sis **ghosts de la lent Sony** a ~8 R☉ (a la base < 4σ, visibles al detall) → pedaç declarat amb sostre de radi; **vores rectes** = l'extensió sintètica de la V25 → fora de cobertura hi va la DADA de Pere (capes 12+13) igualada amb ploma a la vora EXTERIOR (⛔ el forat lunar hi comptava i feia una franja fosca 1,0-1,27 R☉); **ratllat** = dues famílies de la Sony al mateix període 27,5 px (−45° i −36°: mateix angle a 10 finestres = sensor) → notch en falca. ⛔ **Troballa de fons: el cel aplana la corona** — CEL/CORONA = 1 a 2,5 R☉, 5 a 4, 10 a 5, 21 a 6: amb el cel dins, la corba B deixa la modulació real (13-27 % fins a 5 R☉) a ±0,005 i la corona «s'acaba» a 2,7 R☉. Cures (etapa 1b): capa `03 DETALL ACHF 32-256 px` sobre la corona SOLA (NRGF complet, 3,5·MAD per anell, esvaïda 5→6,5) i base OCULTA `00b` corona + 0,25·cel (mateixa àncora). El detall fi és gra de 3,5 R☉ enfora → esvaït 3,5→5. ⛔ Norma: cap capa de detall entra a un PSB sense passar la skill, i cap lliurament sense mirar les vistes (la ronda 2 passava H1/fidelitat/OBRE amb la franja fosca al limbe). Skill i trampes (`trampes.md` «Quatre trampes de la V26») sincronitzades a Codex.
⏭️ **02-09 (nit) — LA V25 LINEAL: `research/130`.** Pere va triar la corba B
(0,22/0,74/0,045) entre dues vistes i va demanar la base lineal que no calgui
corregir amb Camera Raw. Lliurada `CapesTotalsV25_lineal_B.psb` (porta OBRE):
fusió lineal dels dos trens + corba B + ACHF 70 % en Superposar, a la graella
de la V23, amb les seves capes intactes. Deutes: un sol re-mostreig (fase 2 de
la cadena al llenç V23), 1,5 px de residu local, VAR per canal. ⏭️ Següent: la
prova A/B amb la mateixa vara (Pere exporta la V24 amb el seu Camera Raw).
⏭️ **02-09 (tarda): còpia verificada al 4TB i neteja** (rebut
`output/cleanup/20260902_neteja/REBUT.md`). ⛔ **I el projecte ja no té git**:
per decisió de Pere el `.git` s'ha retirat; la història és al paquet de
`.coordination/git_historic_20260902/` i al 4TB. Cap ordre git en aquest
arbre; el `claim.lock` i els fitxers d'estat continuen manant.

⏭️⏭️⏭️⏭️⏭️⏭️⏭️ **30-08-2026 — LA RECERCA D'EARTHSHINE I LA V4: totes les
versions amb la mateixa vara, i les portes de Codex (`research/127`).** Per
ordre de Pere (inventari, SNR, sospita de geometria, contrast xhigh, execució
desatesa). ✅ **La geometria era bona** (registre ≤0,3 px); ⛔ el coll
d'ampolla era el MODEL DE VEL: ajustat a r<0,975 contaminava el disc (la
capa del 29 feia r=0,777 quan UN SOL fotograma de 8 s ben netejat fa 0,857 —
Pere ho va veure). Amb la vara única: Earthshine_FINAL del 15-08 = 0,655; el
seu stack renetejat 0,813; **la V4 nova = +0,877** (11 fotogrames: Vixen
3×10s+3×2s + Sony >1s; pesos vixen10 76,4/ap1 19,1/vixen2 4,5/ap2 0). El
Vixen s'ha invertit des del 15-08 perquè aquell dia el dark de 10 s duia
pedestal 511 (recalibrat el 27-08). ⛔ **Codex (xhigh) va aturar el pla i
tenia raó**: fora el model azimutal de vora (matava k=1,2 lunars; ciència
NOMÉS r<0,85), la selecció del radi és assistida pel mapa (**la significança
citable és la del 126: 7σ**; el 0,877 és producte), pesos ∝ t_exp dins de
component, destripat només amb porta held-out (+48 % PASS), i **la porta
d'injecció cega va caçar que el Wiener DoG menjava el 17 % del senyal** (les
"bandes" DoG tenen cues fins a λ~40 px) → refet en Fourier, transferència
0,958 PASS. ⏭️ Regles noves: tota versió es compara amb les velles AMB LA
MATEIXA VARA abans de lliurar; el suavitzat surt del Wiener mesurat per
banda (en Fourier, mai DoG); tota cadena de senyal feble porta porta
d'injecció. Capa `EARTHSHINE V4` a la V21; deutes: variància no propagada, halo físic
per component com a via de millora (cua). ⏭️ **31-08, els dos defectes
marcats per Pere (`research/127` §7)**: el «cràter» fals era una **MOTA DE
POLS DEL SENSOR R6** (+33 comptes als 6 Vixen, +5 a la Sony; fixa al sensor
a 3579,2374; ⚠️ NO és als flats del 22-08 — r=0,00: la pols es mou; lliçó
2027: flats del mateix dia o dither) → pes Vixen a 0 en 22 px, la Sony
omple, r puja a **+0,887**; i el limbe pintat és fora: la capa passa a ser
el DISC LINEAL APILAT natural (vel ×0,3 i realç ×12 declarats, estirament
lineal, res de corba de corona ni pedestal). ⛔ Regla: cap tret puntual no
es bateja (Aristarc…) sense la posició PREDITA per l'efemèride al costat.
⏭️ **31-08 (tarda), el WALKING NOISE marcat per Pere (`research/127` §8)**:
gra orientat a 75° = FPN del sensor caminat per la deriva lunar (77°,
12,3 px); ⛔ els parells entre germans NO el veuen (es cancel·la: r fina
0,44 a Δt 3 s però 0,03 a Δt 13 s) → estimador corregit (potència total −
senyal creuat entre sensors) i **els pesos giren: Sony ap1 51 % (DSC06987
sol 41 %), Vixen10 34 %, Vixen2 15 %** — com Pere demanava. Flat fi del
22-08 refusat per porta (puja el gra). Display pel Wiener mesurat:
anisotropia 43× → 2×. Regla: el soroll d'un component mai només per
diferències entre germans.

⏭️⏭️⏭️⏭️⏭️⏭️ **29-08-2026 — L'EARTHSHINE HI ÉS, I EL MAPA DE LA NASA HO
CONFIRMA A 7σ (`research/126`).** Per ordre de Pere (no fabricar res; apilar
la Sony >1 s AMB el Vixen >9 s; refer la correlació amb les textures NASA).
⛔ **Rectifica el veredicte negatiu del `125` §3 bis**: el 28 es va mirar
només la Sony i amb els 5 fotogrames barrejats, i **el segon apuntament porta
un vel de 40,2 comptes de residu** (contra 5,7 del primer) que s'ho empassava.
Amb els **8 fotogrames** (Vixen 3×10 s + Sony 2s×3 i 8s×2) al mateix marc
lunar —moviment de la Lluna 0,581″/s, deriva de cada muntura i rotació de camp
+7,86′ resolts—: **r = +0,792 amb el mapa LROC WAC de la NASA, control nul
−0,070 ± 0,123 → 7,0σ**. ⏭️ **Res ajustat**: libració i pol lunar de
l'efemèride (de421 + IAU 2009), nord del llenç **de les estrelles del
catàleg**, i l'escombrada fina d'orientació té el **màxim exactament a 0°**.
⏭️ **La prova que no depèn de cap model**: Vixen × Sony-apuntament-1 = **+0,928**
entre ells (dos telescopis, dues òptiques, dos apuntaments). Geometria
validada dues vegades: alineació entre trens **(−0,07, +0,01) px** i quocient
de nivells **3,13** per canal contra la predicció geomètrica **3,13**.
Amplitud real **0,36 % del disc** (per això no es veia). ⛔ Dos defectes
propis caçats: el perfil radial per anells deixava a **zero** els anells amb
menys de 40 px i fabricava un pic de **253 comptes al centre** que no és a cap
fotograma (cura: interpolar); i el **criteri creuat entre trens NO val per
triar el model de vel**, perquè els dos trens miren la mateixa corona i part
del vel també és comuna. Capes: `EARTHSHINE` (dos trens, vel restat,
amplificat ×30 DECLARAT) i `ESTRELLES` (⛔ cap disc dibuixat: contingut i
màscara = llum mesurada; el catàleg només diu quines ho són).

⏭️⏭️⏭️⏭️⏭️ **29-08-2026 — V21 TERCERA RONDA: EL CONTROL NUL, i el camp era
net (`research/125` §3 ter).** Pere: «n'estàs detectant fora del camp teòric
del 300 mm». ✅ **El camp surt NET**: cada estrella, tornada del llenç al
sensor de cada fotograma amb la cadena sencera (rotació del salt inclosa),
cau dins del RAW de 2+ fotogrames; la més exterior és HIP 46910 a **4,05°**
i la diagonal del semicamp és **4,27°**. ⛔ **Però la sospita era bona i el
defecte era la PURESA**: amb el **control nul aparellat** —les mateixes
posicions predites GIRADES al voltant del Sol, mateix radi i mateix soroll—
la falsa alarma a 3,5σ és del **2,8 % per posició** (gra correlacionat + màxim
de 49 px), i de les 18 estrelles de V 10-11,5 de la ronda 2, **15 eren gra**
(excés 2,8, 0,7σ). El límit de detecció de l'apilat és **V ≈ 9,5**. Dues cures
de mètode: la correcció fina de la ronda 2 estava contaminada (sortia
d'aparellar contra el gra; la bona és **(−1,19, +0,53) px**) i hi ha
**distorsió de camp residual** que la placa radial no porta (model quadràtic:
residu 2,74 → **1,42 px**). Lliurable: **85 estrelles, puresa 95,8 %
MESURADA**, V≤9,5, i la prova independent que ara ho són: **flux ↔ magnitud
r = +0,713** (ronda 2: +0,181). ⏭️ **Regla**: cap llista triada per llindar no
es lliura sense control nul aparellat que digui quantes en són de falses.

⏭️⏭️⏭️⏭️ **28-08-2026 (nit tancada) — V21 SEGONA RONDA: NOMÉS ESTRELLES DE
CATÀLEG, i l'earthshine ACOTAT (`research/125` §3 bis).** Pere va refusar la
primera: «estrelles fake» (⛔ el 97 % de les 1.263 deteccions cegues era gra:
només 35 casaven amb el catàleg) i «l'earthshine no es veu gens». Cures:
**capa ESTRELLES del catàleg cap a la imatge** — Tycho-2/Hipparcos de
l'astrometria del 17-08 + placa radial de DSC06993 (rms 0,71 px) +
fotometria forçada 3,5σ → **87 estrelles amb HIP/Tycho** (V 5,7-11,5) — i
**l'earthshine mesurat i acotat**: el disc lineal separat en vel + residu
asimètric, i la validació selenogràfica (IAU+de421, libració +4,1°/−1,1°,
paritat verificada amb les estrelles) diu que **les maria NO hi són** (el
residu és asimetria del vel de corona; NO es lliura com a earthshine). Física:
Sol a 9,1° → X=6,4 → **extinció ×11**; superfície lunar **≲1,5 % de la llum
del disc**. Capa lliurada: `EARTHSHINE+VEL` (la dada, nom honest); troballa
menor: tret brillant moon-fixed a 32 px de Grimaldi. ⏭️ 2027 Tarifa (Sol
~35°): extinció ~×1,7 — l'earthshine sortirà. Photoshop: OBRE · 16 capes.

⏭️⏭️⏭️ **28-08-2026 (nit) — CapesTotalsV21.psb: LES ESTRELLES FETES BÉ I LA
CAPA D'EARTHSHINE, i és `research/125`.** Pere va re-desar la V19 (fora la
capa d'estrelles dolenta i el Pasalt) i va manar: plate-solve, apilat Sony
>1 s registrat a les estrelles amb base el 8 s amb la Lluna centrada, capa
d'estrelles, i capa només d'earthshine. ⛔ **El «lio» mesurat: el salt
d'apuntament va incloure una ROTACIÓ DE CAMP de +7,9′** (7-8 px de doblament
d'estrelles a la vora) més 2-5 px de translació per fotograma; la deriva
sideral−solar és 0,15-0,42 px — el lio era la muntura, no el cel. Ajusts:
correlació de fase per finestres (rms 0,04-0,06 px, mateix apuntament;
⛔ el total es refereix al CENTRE de la finestra o queda un biaix de WIN/2
exacte, i la finestra ha de ser lliure a TOTES DUES imatges) i aparellament
de fonts brillants entre apuntaments (rms 1,13 px; el gra correlacionat del
drizzle mata la correlació de finestres entre apuntaments). **Base:
DSC06993** (t=70 s, Lluna a 151 px del centre). Capes noves sobre la V19:
`ESTRELLES` (apilat registrat a les estrelles, alineat a −0,14 px de la capa
Sony; 1.263 fonts; **elongació mediana 1,97→1,48**) i `EARTHSHINE` (apilat
registrat a la LLUNA, rotació compensada, només disc amb guarda de 6 px dins
del limbe; disc a (6465, 6753), mediana render 0,70-0,75 amb ~2,6 %
d'estructura ampla; ⚠️ porta earthshine MÉS vel de llum escampada — separar-
los és feina de to de Pere). Eines `v21_*.py` + `cau_v21/`; porta Photoshop
OBRE · 16 capes.

⏭️⏭️ **28-08-2026 (nit tancada) — CapesTotalsV19.psb LLIURADA: el fons per
raig al llenç sencer, i és `research/124`.** Per ordre de Pere («Endavant,
monta la nova versió»): les seves capes byte a byte (fora la còpia de
marques) + **`FONS_PER_RAIG`** (B en ln r σ0,2 per raig del compost
DES-PREMULTIPLICAT, pesos de cobertura; màscara EDITABLE = la seva rampa
exacta 2,36→3,12 R☉) + **`ESTRELLES`** (2.456 fonts en Linear Dodge: 343
pròpies a 5σ + les 2.113 del seu retall — al cru són a ~1σ del gra
correlacionat del drizzle i el filtre adaptat NO hi guanya; el catàleg NR de
Pere és el detector). Portes: **16/17 marques de les dues rondes a bony
0,0000** (la verd de +98,4°: 0,142→0,019, i el residu és el GRADIENT REAL del
cel del render, +1,5 %/R☉, declarat — un gradient no és un arc i cap fosa no
l'ha de tocar); sectors 0,0100→0,0004 de mediana; croma −0,19; **cobertura
0,68→1,0000** (cantonades plenes amb l'extensió de cel per raig, cosmètica
declarada més enllà de ~15 R☉). Photoshop: OBRE 12415×12095 · 16 capes.
⛔ Regla nova de l'operador: a la vora d'una màscara el compost duu el valor
PREMULTIPLICAT — el fons autoreferent menja C/α o s'empassa l'esvaïment (el
primer intent va inflar un fals bony de 0,24). Rebut i 6 vistes al costat del
PSB; el V18 de Pere i el seu DesenfocRadialZoom intactes.

⏭️ **28-08-2026 (nit) — EL FONS PER RAIG: el mètode manual de Pere contra els
halos, estudiat i formalitzat, i és `research/123`.** La segona ronda de
marques de Pere (VERD=lluminància, TARONJA=to) va destapar que els halos de la
V18 eren nostres (referència Vixen enverinada a la vora + fosa per canal que
pintava to: `research/122`; el PSB de la V19 dissenyada MAI no es va escriure
— la sessió va morir a mig construir). Pere ho va resoldre a mà:
`V18-DesenfocRadialZoom.psb` (retall 3:2 8156×5422) = original fins a ~2,6 R☉
+ **duplicat amb Desenfoque Radial ZOOM** per a tot el camp exterior (màscara
= rampa radial pura 2,45→3,25, R² 0,992). ⏭️ **La lliçó estructural que mana**:
al camp exterior l'artefacte (halos, arcs, costures) és variació AL LLARG del
raig i el senyal (streamers) és variació EN AZIMUT — un suavitzat només en
ln r (autoreferent: cap referència que es pugui enverinar) mata el 100 % dels
halos per construcció i conserva els streamers. Mesurat: 15/17 marques de les
dues rondes a bony 0,000. ⛔ Preu del mètode manual, quantificat: estrelles
MORTES des de 3,1 R☉ (supervivència = 1−m; vetes radials d'11,6 σ), −25-30 %
d'amplitud tangencial a 4-7, +3-4,4 % de nivell a 3-4,5, i des de 3,25 R☉ el
compost és cosmètica, no dada (coherent amb D1, declarat). ⏭️ **L'operador
formalitzat `fons_per_raig`** (polar 4080×1200 en ln r, mediana-11 + gaussiana
σ_lnr=0,2 per raig, normalitzat per pesos — les «cantonades pintades» sense
pintar) iguala o millora totes les portes del resultat de Pere i **recupera
2.097 de 2.102 estrelles** (Pere: 1): `cau_v19/desenfoc/scripts/
operador_prototip.py`, lliurat com a `V18-DesenfocRadial_F3_operador_
estrelles.tif`. El ρ del `research/121` queda per a la zona de dada (fusió
entre trens ≤ radi de detall); el fons per raig, per al camp exterior.

⏭️ **28-08-2026 (tarda) — CapesTotalsV18.psb MATA ELS HALOS DE LA FUSIÓ, i és
`research/121`.** Pere va corregir a mà la capa Sony (Camera Raw) i va pintar
9 arcs de halo (3,6-4,6 R☉): la banda de la seva màscara, on la Sony era un
8-18 % més brillant que el Vixen. La cura: **igualació en baixa freqüència**
(S′ = S·ρ; ρ = radial × Fourier azimutal k≤2, per canal, finestra declarada
≤5,5→7 R☉) — pitjor bony 0,0024 (abans 0,03-0,07), camp llunyà intacte,
qualsevol màscara esdevé lliure de halos per construcció. ⛔ Dues versions de
ρ caçades per les portes: cap camp lliure (persegueix costures) i cap
mostreig clavat a l'últim calaix (toca el camp llunyà) — model suau PER
CONSTRUCCIÓ i finestra DECLARADA. ⏭️ **El format canònic de la Sony és el de
Pere** i queda desat i mesurat a `FORMAT_CANONIC_SONY_PERE.json` (interior
~0,90 → cel fosc i blau 0,28-0,41 amb B/G 1,22, ombres p0,5 0,08-0,10): cap
render pla de la cadena no torna a sortir com a lliurable estètic.

⏭️ **28-08-2026 (migdia) — CapesTotalsV17.psb: L'APILAT SONY >1 s A LA
GEOMETRIA DE PERE, i és `research/120`.** La V16 és una re-escenificació SEVA
(llenç 12415×12095, Vixen rotada +10,880° — mesurada, no suposada—, capes
08-01 apagades): la V17 hi posa l'apilat dels 5 fotogrames Sony >1 s (dada
des d'1,95 R☉, 22 s d'integració) compost del RAW en un re-mostreig, alineat
a 0,1 px de la seva capa 01, amb WB/nivell iguals a la capa 01 al 3r decimal
(guanys R×1,001 · B×1,188) i màscara smoothstep 2,00-2,65 R☉ (zero exacte
dins de la vora de saturació). El limbe de la màscara de la 09 net (disc
mesurat al contingut de la V16). ⛔ Lliçó: un ajust iteratiu contra una
referència no vigilada convergeix cap on sigui — aquí va perseguir el negre
dues vegades fins a triar la capa 01 com a referència. ⚠️ Queda l'anell fosc
1,5-2,0 R☉: és el muntatge de Pere (08-01 apagades), no cap defecte.

⏭️ **28-08-2026 (matinada) — CapesTotalsV15.psb ESTÉN EL LLENÇ I AFEGEIX ELS
8 s DE LA SONY, i és `research/119`.** Per ordre de Pere sobre la V14 (que ell
havia retocat a la capa 01): llenç 7648×5353 → **14572×14196** (fins on arriba
tota la dada), les 12 capes de la V14 **byte a byte** només desplaçades
(+3387, +5109), i a baix de tot la capa
`13_8s_DSC06987+DSC06993_apilat2_SONY300` — un fotograma per apuntament, la
recepta exacta de les capes LDIC del run `016_SONYTOT_CIENCIA`, dada
2,77-14,87 R☉, un sol re-mostreig del RAW. Alineació Sony↔V14 verificada:
(+0,18, −0,17) px. ⛔ Geometria que mana: **els dos runs NO comparteixen
`pa_north`** (VIXEN 57,19°, SONY 90,27°; els 33,1° de diferència són la
rotació entre trens): tota transformació entre llenços va en DOS passos amb
els números de cada run. El format passa a **PSB** (el fitxer fa 3,24 GB).
⛔ I la trampa del «no compatible» de PSB queda caçada i tancada amb porta
permanent: psd-tools re-serialitza `cinf`/`FMsk` amb `8BIM`+8 bytes quan
Photoshop els vol `8B64` — fora blocs globals heretats en re-serialitzar, i
**cap PSD/PSB no es lliura sense passar `porta_photoshop.sh`** (l'obre el
Photoshop real, sense diàlegs). `research/119` §5 i `trampes.md`.

⏭️ **28-08-2026 — CapesTotalsV14.psd ÉS LA V13_PERE ALINEADA I AMB EL LIMBE
NET, i és `research/118`.** Per ordre de Pere («overwrite de l'actual, que no
serveix per res; limita't a alinear les imatges amb la corona i deixar net el
limbe lunar»): píxels de Pere **byte a byte** (la seva corba del 21-08
intacta), moviments **enters d'1 a 3 px** mesurats sobre la corona mateixa
—residu 0,23 px al fitxer escrit— i màscares només multiplicades dins del disc
lunar de C2 declarat (vel 0,038-0,090 → 0,0004-0,0017; silueta p95 6,0 → 3,5
px). ⛔ Dues troballes que manen: **la V13 no seia «cada capa al seu
fotograma»** (rectifica `research/117` §1) sinó en tres grups amb retocs
manuals ENTERS de Pere sobre la geometria comuna de 572A2969; i **el vel del
limbe el posava la capa 01** (10,3 s), no les màscares 10-12. ⛔ Trampa nova de
PSD 16 bits: `topil()` retorna les màscares a 8 bits — cada canal editat s'ha
de tornar a DESCODIFICAR abans de desar (`trampes.md`). El lliurable del `117`
queda apartat a `Documentacio i QA/V14_calibrada_20260827_superseded/`.

⏭️ **26-08-2026 — EL QUE ENS TENIA ENCALLATS ÉS LA CORBA DE TO, i és
`research/108_LA_MAQUETA_V13_I_LA_CORBA_DE_TO_2026-08-26.md`.** Per ordre de
Pere («desencalla el projecte; agafa CapesTotals13 com a maqueta»). ⛔ **El
lliurable de qualsevol muntatge no pot sortir d'`estira_log`**: els seus
percentils `[0,5 · 99,7]` donen **2,25 dècades** quan la dada n'abasta
**3,92**, o sigui que **cremen 1,67 dècades** —**329.659 px a 0,998 fins a
1,45 R☉**: cromosfera, protuberància i corona interior senceres— i deixen el
pendent a **0,503 per dècada de B/B☉** quan la maqueta de Pere en demana
**0,166** (×3,03). El paràmetre passa a ser **declarat i no derivat**:
**pendent 0,17/dècada, àncora 0,68 a 1,05–1,15 R☉, terra 0,045**, i el sostre
surt del **màxim de la dada**, mai d'un percentil. ⏭️ La corba que Pere va
aplicar a mà a `CapesTotalsV13_Pere.psd` el 21-08 a les 14:21 diu el mateix
número, i **ja hi arreglava el rentat de la Lluna** que `research/87` va
descriure (0,137 → 0,024): el «no serveix» del `87` és de **pedigrí**, no
d'aspecte. ⛔ **I hi ha una regressió del 23 al 26**: `research/93` ja tenia
les cures i el pilot no les va heretar — **igualació entre trens PER CANAL**
(l'escalar únic ×1,119 deixa la Sony amb **el R un 19 % baix i el B del 19 al
35 % alt** sobre el mateix cel; els guanys reals són 1,074/0,858/0,904 i el
residu cau al 0,1 %), **neutralització** a 1,8–2,2 R☉ —obligatòria perquè els
factors de `research/75` §5.2 són **per píxel VERD** i R/B **no estan
calibrats**— i **el cel com a quàdrica PER CANAL**, que varia del 28 al 65 %
pel camp i per això una constant no el pot treure. ⏭️ **L'enquadrament no és
un problema de dada**: la caixa 3:2 centrada al Sol amb **100 % de cobertura**
dels dos trens fa **±8,58 × ±5,72 R☉**, més que la maqueta. Prova d'aspecte
reproduïble (⚠️ **no és un lliurable ni una mesura**):
`research/tools/prova_aspecte_maqueta/prova_aspecte.py`; vistes a
`~/Desktop/Eclipse 2026/IA/output/prova_aspecte_maqueta_20260826/`.

⏭️⏭️⏭️ **EL PILOT JA ESTÀ EXECUTAT: el resultat canònic és
`research/99_PILOT_VIXEN_LDIC_EXECUTAT_2026-08-23.md`** (23-08-2026, vespre).
Fases 0, 1 i 2 senceres —passen F1, F, E, E2, G i el rectangle; F0 passa 5
dels 6 anells i la fotometria es declara **fins a 3,2 R☉**— amb el compost al
llenç comú a `output/pilot_vixen_claude_20260823/`. Hi ha tres troballes que manen
sobre qualsevol feina aigües avall: **els temps d'exposició del manifest són
els nominals del menú** i el cos en fa uns altres (fins a −6,25 %); **el
`sol_x` del manifest no és una mesura** i està 3,65 px fora del limbe; i **el
nivell de blanc efectiu no és 16383**. I una **rectificació**: el centre absolut
bo és el de l'**efemèride**, no el del limbe mesurat — el limbe hi està 8,0 ″
desplaçat i **els dos trens hi coincideixen a 0,21 px**. I una troballa que mana
sobre tot el postprocessat: **més enllà de 2,41 R☉ el compost és CEL**, no
corona (a 5 R☉ el cel n'és 9,2×), i l'anivellament només l'iguala entre
fotogrames sense treure'l: **cal restar-lo abans de qualsevol fotometria
coronal**. Amb el cel restat als dos trens, **discrepen d'un 15 a un 18 % sobre
la corona sola** dins de 2 R☉, i això **és la incertesa que els dos factors
absoluts ja declaren** (±10 % cadascun → ±14 % sobre el quocient, 1,2 σ): no hi
ha res trencat, però **l'escala absoluta del fusionat és incerta al ±14 %** i
cap acord entre trens no la millora. `research/98` és l'auditoria d'entrada
de Codex, amb tots els números exactes, i el seu bloqueig queda resolt pel
`99`, que explica per què les portes F0 i F1 originals eren impossibles.

⏭️⏭️⏭️⏭️ **LA SEGONA RONDA DEL 24 ÉS
`research/100_FLATS_INVERTITS_I_ANELLS_DEL_PERFIL_RADIAL_2026-08-24.md`**, i
mana sobre flats, filtres i previsualitzacions. Pere va portar **28 flats amb
el cos girat 173,5°**: amb ells **el flat radial de la Vixen queda VALIDAT**
—dos cels independents el reprodueixen al 2,2-3,4 % de la seva amplitud—, i amb
ell `MASTER_FINE_SENSOR` i `MASTER_OPTICAL_EVEN180`; el `SMOOTH2D` es queda en
quarantena amb un 18-20 % de la seva amplitud que és cel; i **l'eix òptic queda
declarat NO MESURABLE amb flats**, perquè no hi ha estructura fixa al telescopi
sobre la qual registrar. ⚠️ **Els flats del 22-08 no estaven a l'orientació de
l'eclipsi: hi estan 12,4° girats**, o sigui que triar el màster radial no era
prudència sinó necessitat. I Pere va marcar anells amb dents de serra: ⛔ **el
54 % del detall que la fase 3 declarava era artefacte** d'un perfil radial
restat **per calaix** —a la corona interior el quocient serrell/senyal valia
1,00-1,13, o sigui que el «detall» ERA el serrell—. Arranjat en **log r**, amb
39 proves, i la fase 3 refeta a `output/pilot_vixen_claude_20260824/`. La cadena
sencera està refeta a `output/pilot_vixen_claude_20260824/`, amb **cinc defectes
germans més** arranjats —entre ells la **trampa canònica del `distanceTransform`
sobre un mapa de cobertura amb el forat de la Lluna**, que feia que **la Sony
posés el 91 % del detall de la corona interior**—. ⏭️ **I n'ha sortit una via
nova: el COLOR separa la corona del cel** (§D). La corona és solar i el cel és
blau; la descomposició té un grau de llibertat per fallar i el residu és del
0,01 al 1,26 %, i **els dos trens hi coincideixen a 1 punt**. ⚠️ **Rectifica el
§15 del `99`**: la discrepància entre trens sobre la corona sola **no és del 15
al 18 % variable sinó ×1,1439 CONSTANT amb un 0,60 % de dispersió** —la forma
coincideix i el que falta és **un sol número**—. I **acota la part constant del
cel a ≲10 %** sense cap dada nova.

⏭️⏭️⏭️⏭️⏭️ **LA NIT DEL 25 ÉS
`research/101_LA_SONY_SENSE_COHERENCIA_I_ELS_FILTRES_2026-08-25.md`**, i mana
sobre la fase 3 de la Sony, l'atribució del nivell i el sostre de fusió.
⛔ **La fase 3 de la Sony no havia fet servir MAI el compost amb coherència**:
`_dir_sony` i la fusió dels dos trens construïen el sufix a mà i tots dos es
menjaven el `_coh`, o sigui que el producte etiquetat `filtres_sony_coh` sortia
del compost **sense** la cura de les costures, i la fusió aparellava una Vixen
coherent amb una Sony que no ho era. Arreglat: **les costures de la Sony passen
del 92,6 % al 7,98 %** al compost. ⛔ **I el flat queda DESCARTAT**: compondre
amb `flat=no` deixa el desacord entre esglaons **igual** (correlació 0,984,
mitjana 0,123 → 0,122 %). ⛔ **I la no-linealitat del pou també**, perquè el
seu signe **alterna**. El que hi ha són **ofsets per esglaó** de ±0,1 a ±0,5 %.
⏭️ **D'això en surt que `PILOT_SOSTRE` es queda a 0,85**: baixar-lo era un
pal·liatiu que costa senyal/soroll (jutge Δz = −0,0062). I l'arc que Pere va
marcar en verd **no té component circular mesurable**: la mediana per anell val
≤ 0,008 % als dos trens, i la Vixen no hi té cap frontera. Filtres nous a
`research/tools/pilot_vixen_claude/filtres_druckmuller.py` (passa-alt, desenfoc
radial i azimutal, NRGF, FNRGF, MGN, WOW, NAFE) i projecte de Photoshop a
`munta_photoshop.py`. **96 proves.**

⏭️⏭️⏭️⏭️⏭️⏭️⏭️⏭️⏭️⏭️ **LA CACERA DE L'ARTEFACTE ESTÀ TANCADA A
`research/107_LA_CACERA_FINAL_LA_MEDIANA_I_EL_MUR_2026-08-25.md`** (25-08,
nit tancada, sota mandat de Pere «acaba d'una vegada per totes amb aquest
artefacte»). Vuit candidats jutjats en una nit i **el detall final del
producte passa a la MEDIANA de les tres realitzacions de canal**: jutge
extern +0,00347 ± 0,00178 (correlació amunt a 4 de 5 bandes; acumulat des
del G antic +0,0104), **mètrica de Pere −8,54 → −2,93·10⁻⁴** (el 66 % fora),
H1/G/rectangle PASS. R i B sols mesurats NETS als traços de Pere
(+0,77/−0,78): la confirmació final del mecanisme del 104. ⛔ **El terç
restant és IRREDUCTIBLE amb aquestes dades** (§2 del 107, el mur: la direcció
cromàtica dels arcs és idèntica a la de la corona E; l'amplitud no
discrimina; l'estadística anular s'autoemmascara; el nul honest treu cel
compartit i el jutge el penalitza −0,0018; el model físic de barreja explica
el 67-81 % de la desviació global i zero als arcs perquè hi manen les
diferències DINS de cada esglaó, no restringibles amb 2 equacions per píxel).
La cura completa és la captura del 2027 (§1 quater). Lliurables:
`dos_trens_filtrats/` refet amb la mediana (l'anterior a
`dos_trens_filtrats_llum121/`), `photoshop_mediana/Eclipsi_2026_dos_trens_
MEDIANA.psb`, i **l'eina de parpelleig de Pere**
`photoshop/Eclipsi_2026_parpelleig.psb` (mediana, lluminància, G, R i B per
capes a la mateixa escala — perquè l'artefacte és una DIFERÈNCIA entre
realitzacions i només una comparació el pot ensenyar). ⚠️ Lliçó de mètode:
la meitat dels candidats haurien passat qualsevol control intern; els va
tombar el jutge extern. La norma zero va d'això.

⏭️⏭️⏭️⏭️⏭️⏭️⏭️⏭️⏭️ **EL PRODUCTE FINAL DEL PILOT ÉS
`research/106_LA_LLUMINANCIA_DE_BRNO_I_LA_CURA_RGB_2026-08-25.md`** (25-08,
nit, sota mandat de Pere «avança com creguis»), i resol la tria A/B del 104
amb una tercera via que domina les dues: ⏭️ **el detall de la fase 3 passa de
G sol a LLUMINÀNCIA** (ln L = (lnR+2lnG+lnB)/4, variància propagada exacta) —
**PASS del jutge extern +0,00686 ± 0,00221 (3,1 σ)**, més gran que el de la
cura del cel, amb **la mètrica de Pere a la meitat** (−8,54 → −4,04·10⁻⁴),
la mateixa quantitat de detall (0,229 %) i totes les portes PASS. És la porta
que Brno té tancada (`105` §4) i nosaltres teníem oberta. ⏭️ I **la cura del
cel s'estén a R i B** (0,18 %/0,34 %; el B pitjor, com mana el mecanisme):
**EMPAT als dos jutges** (cromàtic −0,004 ± 0,012; detall +0,00007 ± 0,00017)
i adoptada com a *compleció* de la cura G aprovada — la G sola fabricava un
desequilibri cromàtic nou. ⚠️ Confusor nou del jutge cromàtic: els camps
cromàtics dels dos trens correlacionen 0,55-0,98 (cel compartit + retenció
Bayer semblant) — parcialment cec per construcció. **El producte final és
`output/pilot_vixen_fable_20260825_lliurament/`**: compost RGB curat +
detall en lluminància + Sony viva, fusionat (mana la Vixen al 21,3 %, G PASS,
rectangle PASS) i projecte Photoshop `Eclipsi_2026_dos_trens_LLUM.psb`.
L'anomalia fina continua DINS del canal G del compost (només es dilueix al
detall); l'anell de ~1,97 i la Sony en lluminància queden com a cues (§4 del
106).

⏭️⏭️⏭️⏭️⏭️⏭️⏭️⏭️ **LA NIT DEL 25 ÉS
`research/104_LA_MASCARA_DE_PERE_I_LA_DECISIO_DEL_VERD_2026-08-25.md`**, amb
**ARTEFACTE_PERE.psb com a veritat-terra**: el que Pere marca és una anomalia
**NOMÉS del canal G** (−14,7·10⁻⁴ sobre control aparellat; R/B nuls), **NOMÉS
de la Vixen** (Sony neta), a les dues meitats i als fotogrames, a 1,42-2,15 R☉,
i **cap cura aprovada fins ara no la tocava**. L'**arbitratge cromàtic amb
restricció a+b=1** l'esborra al criteri del mateix Pere (−14,5 → +0,3·10⁻⁴)
⛔ però **el jutge el refusa** (Δz −0,0148): s'emporta també estructura verda
REAL — la **corona E (Fe XIV, màxim solar)** i l'**excés de nitidesa de G**
(focus cromàtic: les ales de PSF de R són més amples, vist directament al G−R
de la parcial 572A3090). ⏭️ **La tria és de Pere** (§4 del 104): (A) producte
conservador (cura del cel, jutge PASS) amb l'anomalia visible, o (B) estètic
(arbitratge cromàtic, anomalia fora, −0,0148 de detall verd real) — legítima
sota D1 si es tria mirant les dues imatges. ⛔ Cap versió pintada sobre la
màscara ni cap ajust que optimitzi el jutge. ⏭️ **MECANISME TANCAT (104 §7,
destapat per una observació de Pere a l'animació)**: cada canal compon cada
radi amb un joc de fotogrames DIFERENT (el verd, més sensible, perd cada
fotograma abans; G/R 1,37, G/B 2,62) i el cel va canviar durant els 100 s →
la imatge verda de cada banda és d'un «instant mitjà» diferent que R/B: les
corbes només-G són les estries de transparència de la barreja verda, més el
desplaçament mesurat de +1,45 px a 1,15 R☉ per l'ocultació lunar canviant.
Les finestres de retenció per canal reprodueixen TOTES les zones marcades
(0,5 s → 1,08-1,20; 1 s → 1,16-1,33; 2 s → 1,28-1,46; 10,08 s → 1,62-1,97,
amb l'anell de 1,85 al mig), G1=G2 (no és el sensor), i la paradoxa del sostre
queda dissolta (dins de zones d'exclusió solapades, els dos sostres expressen
la mateixa barreja). ⛔ **L'opció B queda desqualificada pel mecanisme** (mou
les línies a la realització R/B i desplaça estructura interior real);
recomanació: **opció A**, i la cura de fons és igualar la barreja temporal
entre canals (cura del cel també a R i B). Per al 2027: reforça §1 quater.

⏭️⏭️⏭️⏭️⏭️⏭️⏭️ **EL VESPRE DEL 25 ÉS
`research/103_CURA_DEL_CEL_PER_FOTOGRAMA_2026-08-25.md`**, l'execució de les
cures del 102: **la cura del cel per fotograma a la VIXEN queda APROVADA pel
jutge extern** (Δz aparellat **+0,00305 ± 0,00070**; H1/G/rectangle PASS,
costures per nivell 2,9 %) i **el fusionat candidat passa a ser Vixen curada +
Sony viva** a `output/pilot_vixen_fable_20260825_cura/`. La cura és exacta
sense refer el drizzle (els pesos només depenen del cru): ΔC = Σ(w·S_i)/Σw amb
S_i el residu suau de cada fotograma contra una referència t² de zones a pes
ple, banda-limitada a λ<500 px. ⛔ **La mateixa cura a la SONY queda REFUSADA
pel jutge** (−0,0051/−0,0057, també amb la Vixen curada d'àrbitre: treu corona;
mecanisme probable: dos apuntaments amb rotació/compressió residuals que la
fuita de registre global no absorbeix). ⛔ **La cura de l'anell verd NO s'ha
aplicat** (el model no passa els seus controls; norma zero); la corba de
~1,97 R☉ **encara és al producte**. El gra fi (λ<31 px) tampoc no es toca (la
variant σ12 la refusa el jutge). ⚠️ Confusor nou documentat al jutge: els dos
trens **comparteixen el cel**; per això la Sony s'ha jutjat també contra la
Vixen curada. Vistes d'inspecció a `output/pilot_vixen_fable_20260825/entrega/`.

⏭️⏭️⏭️⏭️⏭️⏭️ **LA TARDA DEL 25 ÉS
`research/102_NI_FUSIO_NI_MOIRE_EL_CEL_I_UN_ANELL_VERD_2026-08-25.md`**
(Fable 5, contrast adversari demanat pel traspàs
`HANDOFF_2026-08-25_FABLE5_ARTEFACTE_RESIDUAL.md`), i **canvia el marc**:
⛔ **el que Pere veu NO és la fusió HDR**. La prova que ho decideix és el
**control aparellat pel SOSTRE**: amb `PILOT_SOSTRE` 0,85 → 0,60 totes les
fronteres es mouen fins a 0,35 en ln i **cap corba visible no es mou** (perfils
per nivell amb desplaçament 0,000; del 74 al 91 % de l'amplitud «de frontera»
persistint als mateixos contorns). El que hi ha són **dues famílies noves**:
**(1) estructura de transparència del cel per fotograma** —parells de la
mateixa exposició ensenyen bandes i estries de 0,10-0,50 % rms que es mouen amb
el vent; és la «malla de rectes», i la hipòtesi de l'escaquer CFA queda
REFUTADA— i **(2) un anell fosc quasi circular a ~1,85 R☉ (cv 13 % en radi, 48 %
en nivell), NOMÉS del canal verd (G −0,098 %, R/B als controls), NOMÉS de la
Vixen (la Sony hi és neta), present a CADA fotograma cru** i més fondo prop dels
contactes; PRNU, foscos, flat, sostre i meitats exculpats; hipòtesi de mecanisme
(ghost verd desenfocat de la corona interior) PENDENT de confirmar amb les
parcials. El residu genuí de fusió queda acotat a **~0,01-0,15 %** i deixa de
ser la prioritat. ⚠️ El detall de la fase 3 és **només el canal G**: l'anell hi
entra sencer. La trampa nova («una coincidència de posició no és una causa: mou
el paràmetre») és a `trampes.md`, i la porta H2 s'ha de refer amb el control de
sostre. Mesures reproduïbles a `output/pilot_vixen_fable_20260825/`.

⏭️⏭️⏭️ **EL TRASPÀS VIU ÉS
`.coordination/HANDOFF_2026-08-25_CODEX_COSTURES_I_SOSTRE.md`** (25-08-2026), i
el testimoni és de **Codex**. Porta els arcs i les costures curats als dos
trens, la **NORMA ZERO** —cap correcció d'artefacte no es declara bona sense el
jutge extern—, una decisió de producció esperant —`PILOT_SOSTRE` 0,85 → **0,80**,
que **va després** de la prova `flat=no`— i dos deutes oberts: la dependència amb el nivell **no és atribuïble** (flat i no
linealitat del sensor són degenerats) i una **regressió a la Sony** a
r = 1,263/1,266 R☉.

⏭️⏭️ **El traspàs anterior és
`.coordination/HANDOFF_2026-08-24_PILOT_EXECUTAT.md`** (24-08-2026), que porta
les coses que NO s'han de fer, les constants que manen i què desbloqueja
cada deute obert. Continua vigent en tot el que no toqui arcs, costures,
coherència ni sostre de fusió.

⏭️ **EL TRASPÀS QUE VA ORDENAR EL PILOT ÉS
`.coordination/HANDOFF_2026-08-23_PILOT_VIXEN.md`** (23-08-2026), i és HISTÒRIC. Pere ha pres
dues decisions que manen sobre tot el que hi ha més avall d'aquesta secció:
**(D1)** es va per la **via de la FOTO** de Druckmüller, ajuntant els dos
telescopis — amb el preu, acceptat conscientment, que **el producte fusionat no
és una mesura**; i **(D2)** es fa un **pilot d'una sola tirada, des de zero, amb
la Vixen** al llenç comú. Canònic: `research/97`. El contracte de les quatre
fases (0 Calibració · 1 **Registre** · 2 Composició LDIC · 3 Filtres) és a
`.coordination/HANDOFF_2026-08-23_REESTRUCTURACIO_PER_FASES.md`.

⏭️ El traspàs anterior és
`.coordination/HANDOFF_2026-08-22_ALTERNANCA_CODEX_CLAUDE.md`. Pere ha
decidit alternar Codex i Claude amb deltes auditables; cap IA té autoritat
permanent sobre els fitxers. El delta específic Codex → Claude és a
`/Users/USUARI/Desktop/Eclipse 2026/IA/Coordinació/` i queda indexat per
`IA/ACTIVE.json`. La V1.02 (`1.0.2`) continua congelada com a baseline privat
de captura; la feina viva és auditoria, preservació i postprocessat. El
traspàs del 20 d'agost a Codex i els anteriors són històrics.

Treballa exclusivament des de:

```text
/Users/USUARI/Downloads/Eclipse 2026
```

No reprenguis des de `.claude/worktrees/gallant-hamilton-e9c6bd`. És un
worktree històric: les seves dues modificacions d’empaquetatge ja estan
superades per l’arrel, i la seva prova útil de coherència ja s’ha migrat a
`gui/tests/test_packaged_profiles_coherence.py`. Es conserva temporalment
perquè una sessió local el podria tenir obert.

**Si reprens la feina de l’A7RIIIA, llegeix primer
`.coordination/PLA_SUBSTITUCIO_A7R3A_BLOCS.md`**: hi ha el disseny de blocs
sencer, què s’ha implementat a la 0.9.0, les cinc coses que el pla no havia
previst i què continua pendent de fer al cos.

**Si reprens la feina de l'A7III, llegeix primer §3 «El que canvia la 0.9.2»**:
aquest cos ja fa el disseny de blocs, i el seu sostre de cua i l'ordre de la
seva ràfega **no** són els de l'A7RIIIA.

**Si audites la feina històrica d’optimització de captura, pots llegir
`.coordination/HANDOFF_2026-08-08_MATINADA.md`**: és el traspàs d'aquella ronda, amb el
commit `919b638`, el que va quedar a mitges de la campanya de mesura dels dos
cossos Sony i, sobretot, la troballa que una sessió morta amb imatges pendents
**deixa el cos inservible fins que li treus la bateria**. El traspàs de la
tarda del 7 queda com a context:
`.coordination/HANDOFF_2026-08-07_TARDA.md`: els tres deutes del matí ja
estan tancats —cadència, earthshine de 15 s i run sencer per l'app—, i allà
hi ha què s'ha fet i què queda. Aquest fitxer et dona els invariants; aquell
et dona el següent pas. Els traspassos del matí, la nit i el dia 6 queden com
a context històric.

Abans d’actuar:

1. llegeix aquest fitxer sencer;
2. llegeix el bloc d’estat efectiu al principi de
   `.coordination/CODEX_STATUS.md` i `.coordination/CLAUDE_STATUS.md`;
3. executa `git status --short` i assumeix que tots els canvis són de Pere;
4. si escriuràs, adquireix atòmicament `.coordination/claim.lock/` i registra
   el mateix `claim_id` al teu fitxer d'estat; si ja existeix, no escriguis;
5. no toquis PTP, càmeres, captures, LaunchServices ni GUI física sense
   autorització concreta.

Mai editis `.coordination/CODEX_STATUS.md`. No facis `git clean`, `reset`,
`checkout`, `stash`, ni reescriguis canvis aliens. El repositori està brut a
propòsit: molta feina viva encara no està commitada.

## 1 bis. Estat post-eclipsi verificat

- El run operatiu canònic del 12 d'agost s'identifica com
  `20260812T202219_multi_camera_mission_run`. El seu informe auditat és
  `output/pdf/Informe_auditat_run_Eclipse_Command_20260812T202219.pdf`.
- `CapesTotalsV1.psb` **ja no és el fitxer cobert pel rebut de matinada**.
  L'estat actual té 36 capes, 2.370.519.442 bytes i SHA-256
  `4d0480f1d6508c225f5dbb13fb5c4e608d35a07b58acc2625853284ba48f2a28`;
  no conté una capa anomenada `EDITAT PERE`. El rebut antic descriu 37 capes,
  2,98 GB i el prefix `f0ce3e8bf2606cf1…`. Cal revalidar el save actual; no
  presentis el rebut antic com si el cobrís.
- La xifra 0,662″ és una predicció GR de catàleg i σ(ε)=0,53 és un forecast
  de Fisher: **no són una detecció relativista mesurada**. El projecte sí que
  demostra identificació d'estrelles, solució de placa i calibratge fotomètric.

## 1 ter. Els dos trens porten seguiment, sempre

Declarat per Pere el 8 d'agost de 2026 i marcat com a important, perquè fins
llavors **no constava enlloc del projecte** i un contrast advers extern ho va
detectar com a possible defecte fatal del disseny d'earthshine:

- **Sony FE 300 mm f/2,8 GM** (A7RIIIA, i A7III de backup) → muntura
  **Skywatcher**;
- **Vixen VSD90SS** (R6 Mark III, i 6D de backup) → muntura **iOptron**.

**Cap exposició llarga no queda limitada per la deriva sidèria.** Sense
seguiment, a 300 mm l'escala és 3,10 ″/px i la deriva 14,54 ″/s amb el Sol a
declinació +14,9°: 23 px de moguda en 5 s i 38 px en 8 s sobre un disc lunar
de 613 px, i l'apilat no desfà la moguda de dins del fotograma. Amb seguiment,
l'àncora d'earthshine es dimensiona només per fotometria.

**La taxa és SOLAR als dos trens, i no es toca entre C2 i C3.** Decisió de
Pere del 9 d'agost de 2026; fins llavors §1 ter declarava seguiment però no la
taxa. Sideri contra solar és irrellevant —el Sol es mou 0,041 ″/s respecte de
les estrelles, o sigui **1,3 px en tota la totalitat**—; l'única tria real
seria lunar, i es descarta.

Amb seguiment solar la Lluna es desplaça **0,585 ″/s** respecte del Sol
(topocèntric per al 12 d'agost; la mitjana geocèntrica sinòdica és 0,508 i es
queda un 15 % curta). El número es comprova sol: amb una totalitat de 100 s
implica un excés de diàmetre de 58″, o sigui magnitud local 1,031.

Conseqüències, totes petites però amb signe:

- dins de cada exposició: **1,5 px** als 8 s de la Sony —0,24 % d'un disc de
  613 px— i **2,8 px** als 10,3 s de la R6 —0,32 % de 883 px—. Sobre l'earthshine,
  que és llis i de baix contrast, no es veu;
- el seguiment lunar no guanyaria res: transferiria la mateixa moguda a la
  corona d'aquells mateixos fotogrames, on tampoc importa perquè als 8 s la
  corona ja va tres punts cremada. **L'argument per anar a solar no és la
  nitidesa, és no fer cap canvi de taxa al pitjor minut del dia**;
- la moguda és **lineal amb el temps d'exposició**, o sigui que a integració
  constant convenen més fotogrames i més curts: 1×16 s dona 3,0 px, 2×8 s en
  donen 1,5 i 4×4 s, 0,8. Això descarta qualsevol tríada amb un membre de 16 s;
- entre la primera àncora i la quarta, 48 s, la Lluna es desplaça **28″ = 9 px**
  respecte de la corona: al postprocessat, la pila d'earthshine i la de corona
  **no poden compartir alineació**.

⚠️ Això és a `CLAUDE.md` i a `research/70`, però **encara no a la checklist
física de cap perfil**: afegir-hi la línia canvia el SHA-256 dels perfils i
invalida el bundle, i és una decisió a part.

## 1 ter bis. Els arcs del postprocessat, i què els cura

⏭️ **24 d'agost de 2026, nit.** Pere va marcar arcs concèntrics al detall de la
fase 3. N'hi havia **dues famílies**, i totes dues estan curades **als dos
trens**; el que encara es veu a la pantalla **és corona**, demostrat amb tres
proves independents. Canònic: `research/100` §E.

| | Vixen + R6 III | Sony A7RIIIA |
|---|---|---|
| anells circulars | 27,5 % → **0,4 %** | 34,9 % → **0,5 %** |
| costures de fusió (per nivell) | 88,6 % → **4,6 %** | 92,6 % → **5,4 %** |

Les cures, totes dues a `research/tools/pilot_vixen_claude/`:

1. **Coherència de transparència per fotograma** (`fase_coherencia`,
   `coherencia_sony`): `P_i(r) = c_i·(C(r) + s_i)`, dos escalars per fotograma i
   per pla. ⚠️ Gauge `mediana(ln c) = 0`: **l'escala absoluta no es toca**.
2. **Dues passades de resta, alternades fins a convergir**: la mediana per calaix
   de **radi** (els anells) i la mediana per calaix de **nivell** (les costures,
   que són isofotes per construcció).

I les mesures perquè no tornin: portes **H1** (anells), **H2** (costures, amb
control **aparellat** — el mateix contorn desplaçat, perquè amb una escala d'1 EV
no existeix cap nivell de control lliure) i **H3** (desacord entre esglaons,
píxel a píxel; F0 és cega per sota del 2,5-4,3 %). 62 proves a `test_portes.py`.

## 1 quater. Deute de captura per a l'eclipsi del 2027

⏭️ **Demanat per Pere el 24 d'agost de 2026 com a recordatori explícit per a
futures versions d'Eclipse Command.** No és una decisió de disseny presa: és un
fet mesurat i el requisit que se'n deriva.

**El fet.** El nucli `single HDR` de la R6 III mostreja 1 EV **entrellaçant dues
escales de 2 EV**, i les dues escales són **dos passos diferents en el temps**.
Al run de l'eclipsi del 12 d'agost, els esglaons senars són de t = 6,6–11,6 s i
els parells de t = 12,7–16,5 s. I **la transparència va caure un 8 % durant la
totalitat**: el mateix 1/128 s val **1,0598 a t = 8 s i 0,9779 a t = 89 s**, amb
el cel del run variant un 85,5 %.

**La conseqüència.** Els esglaons veïns discrepen **1,1–1,3 % amb el signe
alternat**, i com que **cada frontera de fusió HDR cau justament entre dos
esglaons veïns**, la imatge final porta una vall visible a cada frontera. Són els
arcs concèntrics que Pere va marcar al postprocessat. ⛔ **La porta F0 no ho podia
veure**: el seu terra de precisió és del 2,5 al 4,3 %, deu vegades per damunt.

**Què ha de complir el programa de captura del 2027:**

1. **Els esglaons veïns han de ser veïns EN EL TEMPS.** Una sola escala monòtona
   d'1 EV, repetida, en lloc de dues mitges escales de 2 EV complementàries. Amb
   ~1 s entre esglaons en lloc de ~6, el desacord cau del 1,2 % a ~0,1 %.
2. **Cada esglaó ha d'aparèixer a dos instants ben separats com a mínim**, o el
   postprocessat no pot resoldre la seva transparència i l'ha d'interpolar. Al
   run del 12 d'agost, els quatre esglaons més curts no es van poder ajustar.
3. **Un monitor de transparència**: una exposició mitjana, no saturada en un rang
   radial ample, repetida cada ~10 s durant tota la totalitat.
4. **Val per als DOS trens.** La Sony té la mateixa malaltia amb el seu joc
   d'exposicions, i la seva pròpia costura a 1,525–1,547 R☉.

⚠️ Qualsevol canvi concret ha de passar per les regles que ja hi ha: els tres
objectius de §1 bis, el sostre de cua de cada cos, la porta de durades de 60 a
110 s (§9) i la norma de §11 que **tot canvi d'obturació o de nombre de fotos es
pinta abans de discutir-lo**. Detall i números:
`research/100_FLATS_INVERTITS_I_ANELLS_DEL_PERFIL_RADIAL_2026-08-24.md`.
⏭️ **Els requisits 1 i 2 queden confirmats pel protocol documentat de l'equip
Druckmüller** (escala monòtona de factor 2 recorreguda amunt i avall tota la
totalitat, 8-50 aparicions per esglaó, 0,3-3 s per fotograma; i el 2019 van
partir l'escala entre dues muntures bessones per doblar la cadència):
`research/105_COM_HO_FA_BRNO_EL_PROTOCOL_DRUCKMULLER_CONTRASTAT_2026-08-25.md`.

⚠️ **Reserva de Pere (25-08-2026, nit): el REQUISIT està acceptat però la
SOLUCIÓ proposada no està decidida.** El dibuix de l'escala monòtona amunt-avall
(pintat el 25-08 amb el widget de dos panells) és UNA implementació possible;
Pere ha dit explícitament que no n'està convençut. Qualsevol disseny concret
del 2027 s'ha de tornar a pintar, contrastar i decidir per ell.

⏭️ **Tres addicions del 25-08 (la cacera del 107 i les animacions per canal):**

5. **El mecanisme és PER CANAL i el disseny s'ha de validar per canal**: el
   verd satura 1,37× abans que el vermell i 2,62× abans que el blau, o sigui
   que cada canal reté cada esglaó fins a un radi diferent i compon amb una
   barreja temporal pròpia. La cobertura HDR de l'informe de run
   (`render_hdr_coverage.py`) hauria de pintar les finestres de retenció
   per canal RGB, no només l'escala global.
6. **El postprocessat ha de desar la variància PER CANAL** a tots els
   composts (el llenç Sony del 2026 només guarda la del G, i això ha impedit
   productes per canal sense aproximacions).
7. **Cada canal necessita prou fotogrames per barreja**: la Sony, amb 14
   fotogrames i dos apuntaments, surt 1,7-2× més bruta per canal que la
   Vixen amb 68 (mesurat a `research/107` i a les animacions del 25-08).

## 1 bis. Els tres objectius científics innegociables

Decisió de Pere del 7 d'agost de 2026, vespre. Aquests tres surten sempre, i
cap optimització, retall ni degradació els pot sacrificar. Si una totalitat
no dona per a tot, es retalla qualsevol altra cosa abans que un d'aquests:

1. **Earthshine.** És la **missió principal de l'A7RIIIA**, no un extra. Si
   aquest cos només pogués fer una cosa, faria earthshine.
2. **Perles de Baily i anells de diamant travessant C2 i C3.** Travessant:
   les perles i el primer anell són **abans** de C2, i el segon anell és **a
   C3 i just després**. Un bloc que no creua el contacte no serveix.
3. **Bracketing de corona amb moltes EV.**

Pere es compromet, si la meteorologia ho permet, a observar des d'un punt amb
**més de 60 s de totalitat**. Aquest és el cas de disseny mínim: el programa
ha de saber escurçar-se dinàmicament fins a 60 s **sense perdre cap dels
tres**. La R6 ho compleix de 40 a 200 s. **L'A7RIIIA també, des de la 0.9.0**:
el disseny de blocs manté els dos contactes travessats i l'earthshine de 60 a
200 s, i el que baixa amb la durada és el nombre d'àncores —sis a partir de
96 s, tres a 60—, no cap dels tres objectius. Era el deute obert més important
del projecte i queda tancat al compilador; la geometria nova encara no té run
físic propi.

## 2. Objectius, per ordre

1. **Mission first.** Un error o warning d’una càmera no pot impedir que les
   altres capturin, UNA CAMERA DEGRADADA s'ha d'intentar seguir utilitzant per
   la missió, costi el que costi. Aquest literal obliga a esgotar les
   continuacions segures del canal; no autoritza repetir un trigger ambigu ni
   continuar amb identitat o propietat divergent, estat físic desconegut
   després d’un write o un ledger que no es pugui garantir. Aquests límits
   aturen només el canal afectat.
2. **Simplicitat.** L’operador veu què passarà i només intervé quan cal una
   acció física real.
3. **Agentic AI abans de la missió.** Els agents poden descobrir, mesurar i
   compilar perfils. Durant la captura, el sistema és local, offline,
   determinista i no depèn de cap LLM.

No introdueixis salvaguardes que converteixin evidència científica pendent en
un bloqueig operatiu. Un perfil conservador materialitzable ha de poder
capturar i mostrar el deute com a informació, mai com a `WARNING` operatiu.
Només poden aturar tota la missió
un pla global invàlid/no compilable, la pèrdua d'aïllament entre canals o la
impossibilitat de mantenir un ledger determinista que consumeixi cada acció
ambigua sense replay. Identitat o propietat PTP incorrectes exclouen només el
cos afectat.
Cap funcionalitat auxiliar nova —ISO, Camera Settings, checklist, Sync UTC o
equivalent— pot esdevenir directament o per efecte lateral un prerequisit de
`Start mission`. Només la identitat/propietat física necessària per dirigir
amb seguretat el cos pot retenir el seu canal.

## 3. Baseline verificat

### Aplicació

**Aquesta versió és el terra operatiu del projecte, i des de la 0.9.3 ho és
als dos extrems del rang de durades.** Tres runs físics multicàmera seguits
el 9 d'agost, tots pel binari del bundle i **cap amb una sola foto perduda ni
una sola exposició divergent**:

| Run | Totalitat | A7III | A7RIIIA | R6 III | Retard màxim |
|---|---:|---:|---:|---:|---:|
| `20260809T030522` | **60,0 s** | 32/32 | 32/32 | 84/84 | 1,196 ms |
| `20260809T031220` | **110,0 s** | 35/35 | 41/41 | 111/111 | 1,106 ms |
| `20260809T031909` | 98,8 s | 35/35 | 41/41 | 102/102 | 20,939 ms |

Els dos extrems del rang que Pere pot trobar-se ja han volat, i el tram de
tres àncores —el que surt si acaba al mínim— no havia volat mai. El tercer
run és el de referència i és el primer que la QA física certifica sencer amb
els **tres** cossos: `ok=true`, `frozen_dispatch_ok=true`. El seu retard
màxim de 20,9 ms és 20 vegades l'habitual i s'explica pel Mac ocupat amb tres
runs seguits; queda molt dins la tolerància de 50 ms dels blocs, però és el
número a vigilar si es repeteix amb la màquina en repòs.

Si el 12 d'agost arribés sense cap millora més, s'hi aniria amb aquesta.
**Volable no vol dir qualificat**: els gates d'òptica, RAW i seguiment
continuen oberts i cap perfil no passa a `PRODUCTION` ni a
`timing_qualified=true`. Informe:
`gui/QA_REPORT_0.9.3_2026-08-09.md`.

| Element | Valor verificat |
|---|---|
| App instal·lada | `gui/dist/Eclipse Command.app` |
| Versió | **V1.02 candidat privat local**: interfície compacta, quatre avisos de veu, deriva d’operador corregida i inici ràpid R6 a C2−15. Release pública 0.8.0 immutable |
| Executable SHA-256 | `61227d418ec7a74a6fa11c934970d85218466ffd067754ec68efbc3334ba9f4f` |
| Manifest de 51 fonts | `d06de97146e521afeb1871c3cfd06c5944faf3c40dbd96898f53c30d734a2f6a` (51 entrades, `app_version` 1.0.2) |
| Perfil de missió A7RIIIA | `f32a769514c73802bffe1303914a0348e9e4dffd44a38e2ffe0d1319e6c36b43` |
| Perfil de missió A7III | `9e83b9dc5e6917870580ec932bbbf1c1ba4014d30ba2b8bf9fe0fcf521ae6f59` |
| Plantilla de blocs A7RIIIA | `09783b4a37d732ecc28c3bc9d0d4621eb16cd6ce2388202cda1e5be4df9a529a` |
| Plantilla de blocs A7III | `bf5ed75b2486331895f254893af177625216db82289dab90df6e08d1f83def81` |
| Controlador Sony compartit | `2c8b3237b0d368c515d8c621a3db840c40bef44926e2b98e7b205a91382322c7` |
| Controlador Canon 6D dedicat | `1dbd7a84feffb2aabe25b9111aa0ece24dd239e8eda8bf08da5e2d3f6d2c2e1e` |
| Perfil de missió 6D | `7c7b8865dba771cd97f7b89d7c69e6aff0fd6b1b3905ddee23acb2f57304d192` |
| Controlador R6 | **`858112011125536b049767585858c1b588fdfa3bf83aa19e4df80124660b4b42`** |
| Perfil de missió R6 | `3dccf954bd51ca66d673ff5cb11dea98a991c8ac2b4d91fecf64777f448234d8` |
| Antisuspensió | `d153c0e17f93d10a537fd6fd1df50669342f32a7c78985cb8413f6796190a3d0` |
| Pont de setup/preflight | **`15424646b6e993322780250b05f0f51c9dd70f48dad3696a14a5cf85edf1ae19`** (canviat a la V1.01) |
| QA | **`gui/QA_REPORT_1.0.2_2026-08-10.md`**, amb els de la V1.01/V1.00 i els de la 0.9.x al costat |

**El bundle V1.02 coincideix amb la font viva**: els **51** inputs incrustats
tenen el mateix SHA que el repositori i el QA portable dona els **onze PASS**.
Ad-hoc, arm64, no notaritzat, `LSMinimumSystemVersion` 26.0, 122,6 MiB.

**Primer run físic de l'escala de la V1.00**, i surt exacta. Run
`20260809T223829` pel binari del bundle, totalitat de 91,0 s: **A7RIIIA 41/41
i A7III 35/35**, zero saltades, zero recuperacions, **zero exposicions
divergents** i retard màxim 1,473 ms. L'EXIF confirma la muntanya sencera —
contactes a 1/6400 · 1/800 · 1/100, tríades de base 1/4 a 1/30 · 1/4 · 2 s i
àncores a 1/8 · 1 s · 8 s— i l'ordre de lliurament propi de cada cos.

**I el run de flota, amb els tres cossos alhora**: `20260809T233027`, **198
fotos, retard màxim 1,458 ms, zero degradades, zero recuperacions i zero
exposicions divergents** —A7RIIIA 41/41, A7III 35/35 i R6 151/151 accions—.
L'únic avís de tot el run és la bateria de l'A7III al 36 %, dit pel seu nom.

**I un setè run que ho torna a donar tot net**, `20260809T234629`, amb
l'A7RIIIA i la R6 —l'A7III no hi era— i totalitat de 91,0 s: **163/163 fotos,
zero saltades, zero recuperacions, zero exposicions divergents, retard màxim
1,473 ms, 38/38 setters verificats i cap `mission_warning` a cap canal**. La
geometria surt clavada a l'informe: cua de **33 imatges** dins totalitat —el
sostre operatiu de l'A7RIIIA— i **117 fotogrames de nucli** a la R6 més cinc
documentals. Els dos advisories de l'A7RIIIA són els de sempre, checklist i
timing no qualificat, que §5 declara que mai poden ser `WARNING`.

⚠️ **La finestra de C3 de la R6 depèn de l'estat de la targeta.** Amb la
CFexpress plena i tres runs seguits en va perdre 32 de 122, sempre del
fotograma 73 al 119 i sempre dos sí / un no; amb la targeta **formatada**,
cap. La geometria és idèntica als sis runs (`de5e61fb2e38`), o sigui que no és
del programa. **El dia de l'eclipsi la targeta ha d'anar formatada de fresc.**
El llindar exacte no queda acotat: entre l'últim run net amb la targeta vella
(6497 fotografies lliures) i el primer degradat (6412) hi ha vuitanta-cinc
fotografies de diferència. El setè run hi afegeix un punt per l'altre extrem:
amb `availableshots` a **7019** —unes 149 fotografies des del format— encara
va **zero degradades**.

⚠️ **El rollback amb evidència física continua sent la 0.9.3**,
`gui/dist/Eclipse Command.app.previous-20260809T110322Z-12217`. Els
`.previous` més recent és la V1.01
(`Eclipse Command.app.previous-20260809T231819Z-18877`).

✅ **La retenció torna a ser de vuit bundles antics.** Els quatre més vells
(0.9.0, 0.9.0, 0.9.1 i 0.9.2) s’han mogut, sense esborrar-los, a
`/Users/USUARI/Downloads/Eclipse_2026_bundle_quarantine_20260810_v102`.

### El que canvia la V1.02: interfície compacta, avisos i C2−15

- La fila i el selector de càmera mostren només el nom curt i l'obertura de
  disseny: `A7III · f/2.8`, `6D · f/5.5`, `A7RIIIA · f/2.8` i
  `R6 III · f/5.5`. El hover ja no aboca `description` ni `manual_preflight`:
  dona un resum breu i conserva model, sèrie, device ID, port i estat PTP.
- La veu afegeix C2−5 min, −2 min i −1 min, i C4−1 min. Continua one-shot;
  cues caducats o silenciats es consumeixen sense replay. El cue de retirar
  el filtre continua a C2−20.
- La R6 comença el setter d'aproximació a **C2−15,00** i la primera foto a
  **C2−14,75**. S'eliminen només vuit `1/3200` —C2−19,95…−15,40— i no es
  redistribueixen. Tot el sufix des de C2−5,65, inclosos totalitat, HDR,
  earthshine, C3, C4 i setters, és idèntic a la V1.01.
- A 91 s: nucli 117→109, total amb cinc documentals 122→114, totalitat 55,
  parcial posterior 34 i setters 29 invariants. Simulació exhaustiva: 1.503
  geometries, totalitats 60–110 s en passos de 0,1 i tres spans C1/C4.
- L'auditoria també corregeix text d'operador stale als perfils A7III,
  A7RIIIA, 6D i R6; qualificació pendent continua essent advisory, mai
  `WARNING` operatiu.

### El que canvia la V1.01: set defectes d'operador, i quatre eren un

**Cap canvi de geometria, d'exposició ni de cadència.** Els tres objectius
científics no es toquen i els tres cossos compilen exactament el mateix
programa que la V1.00. El que canvia és què veu i què pot prémer l'operador,
i com se li explica una fallada.

**1. El dial fora de M ja es diu pel seu nom, i era quatre bugs alhora.**

El 9 d'agost la R6 va quedar fora d'una missió sencera amb el dial a **B**.
En aquella posició el cos obre la sessió PTP i respon, però publica una
configuració degenerada a cada lectura:

| Camí | Cos a M | Cos a B |
|---|---|---|
| `imageformatcf` | 23 opcions, RAW entre elles | **1 opció: `L`** |
| `drivemode` | vàries | **1 opció** |
| `shutterspeed` | 58 opcions, de 30 s a 1/16000 | **31, de 1/8 a 1/8000** |

El gate d'estabilització ho classificava com «no inicialitzat», esperava 3 s,
reintentava, i **quatre minuts i mig** després es rendia amb un
`CameraTransportLostError`. D'aquí sortien **quatre** dels defectes reportats:
el cos no disparava, la identitat quedava pendent, el balanç de blancs es
quedava a AWB i el botó d'ISO no el corregia —el `.operator_setup` del canal
ho registra amb `operator_iso_not_set` i el mateix missatge—. Cap dels quatre
és un incompliment de Mission First: §5 diu que un cos sense ruta PTP viva
queda exclòs, i amb el dial a B **el programa era impossible**, perquè sense
RAW i sense exposicions més llargues d'1/8 no hi ha ni bloc fosc ni
earthshine. El defecte era **no dir-ho**.

Ara `r6m3_mode_dial_diagnosis` reconeix la signatura i llança un
`ManualCameraActionRequired`, que **no és retryable**: es diu una vegada i es
deixa que l'operador giri el dial. Exigeix **dues** evidències independents
—menú de format d'una sola opció **i** cap exposició llarga— perquè amb una
de sola podria ser la finestra d'inestabilitat de sempre, que sí que es
resol reintentant.

**2. Un estat físic que era conegut ja no es declara desconegut.** Quan el
setup d'operador fallava, `write_setup_failure_result` marcava
`physical_state_unknown` sobre el camí d'ISO fos quina fos la causa —fins i
tot quan la càmera no s'havia arribat a obrir i no s'havia intentat cap
write—. Ara només ho declara si el motor ha llançat el seu
`PhysicalStateUnknownError`, que és l'únic cas en què el valor es pot haver
adoptat tard. Un estat desconegut atura el canal (§5); declarar-ne un de fals
és regalar un cos.

**3. Els warnings diuen qui, per què i com s'arregla.** La pastilla de dalt
duu ara el nom del cos —`WARNING · R6 III`— i el tooltip comença per l'acció,
amb una fletxa per causa reconeguda (`WARNING_FIX_HINTS`). Desapareixen les
tres línies genèriques que hi havia: «this is the persistent result of that
operation», «not the live camera-readiness list below» i «this WARNING does
not by itself stop other independently safe camera channels». Els advisories
no es barregen amb la causa, però tampoc s'amaguen: quan **tot** el WARNING
és advisory, el títol passa a ser «nothing to fix on the cameras».

I la pastilla **deixa de cridar quan la causa ja no és certa**: si el cos que
la va provocar ja no està connectat, el veredicte i les seves causes es queden
a Activity i la pastilla torna a IDLE. No s'amaga res; el que es deixa de fer
és presentar en present una cosa que ja no passa.

**4. El rètol de totalitat segueix els camps.** El latch de la línia de temps
sobrevivia a la missió, i llavors prémer TEST RUN canviava els quatre
contactes sense que el rètol es mogués. Ara el latch val mentre la missió
corre —i mentre dura la presentació terminal d'un STOP—, i no més.

**5. `Stop safely` no s'arma sense res a aturar.** Un escaneig de flota
encenia el control igualment. Ara, si el que hi ha de fons és un escaneig,
només s'arma si s'ha encallat més enllà de la gràcia declarada.

**6. `Test audio` no sona amb la veu apagada**, i el botó queda deshabilitat
amb el motiu al tooltip.

**7. Dues coses que Pere va demanar.** La **versió va al costat del nom** a la
capçalera —amb dos bundles a `gui/dist` saber quin està obert no pot dependre
de recordar-ho— i la columna **Program** surt de *Detected cameras*: deia el
rol, que ja és a dos llocs més, i el que sí que aportava —el seu tooltip amb
la descripció del perfil i les comprovacions advisory— passa a la cel·la de
càmera.

### El que canvia la V1.00: les escales noves dels tres cossos

**És l'únic canvi de geometria d'exposicions des del disseny de blocs, i és
gros: toca els tres cossos alhora.** Ve del traspàs
`.coordination/HANDOFF_2026-08-09_NIT.md`, que Pere havia acceptat i deixat
sense implementar, i del raonament de `research/70`.

⚠️ **Cap dels canvis d'aquesta versió té run físic propi.** El terra operatiu
continua essent el de la 0.9.3 i els seus tres runs del 9 d'agost; això està
verificat per regressió, per la porta de durades i pel QA portable, i **la
mecànica** de blocs i de finestres és la que aquells runs van demostrar. El
que no ha volat mai és **l'escala**.

**Els tres objectius de §1 bis es conserven a tot el rang de 60 a 110 s**, i
la porta ho afirma cas per cas: 7.044 casos, porta oberta.

**1. Els dos Sony: contactes a base 1/800 i una muntanya a mig eclipsi.**

```text
C2 −3,35 / −0,45 / +2,45   base 1/800   1/6400 · 1/800 · 1/100
mig eclipsi, pujada        base 1/4     1/30 · 1/4 · 2 s
mig eclipsi, earthshine    base 1 s     1/8 · 1 s · 8 s   (tres àncores)
mig eclipsi, baixada       base 1/4     1/30 · 1/4 · 2 s
C3 −2,45 / +1,45           base 1/800   1/6400 · 1/800 · 1/100
```

L'escala passa de sis esglaons amb salts de 3,00 EV a **nou amb 2,00 EV de
màxim**, i de **tres** exposicions a mig eclipsi a **sis, amb tres
subfotogrames a cadascuna**. La base 1/320 d'abans no entrava mai a la banda
de perla compacta de `research/66`; 1/800 hi té un fotograma ben endins i un
altre dins la de cromosfera, que és **l'única banda que cap altre cos de la
flota no cobreix**.

**Les àncores són sempre tres** i el que escala amb la durada són les tríades
de base 1/4. El sostre no és el rellotge sinó la cua del cos: quinze imatges
de contacte més tres per disparament de mig eclipsi. A l'A7RIIIA hi caben sis
unitats —3 àncores + 3 tríades, 33 imatges— i a l'A7III quatre —3 + 1, 27.

| Totalitat | A7RIIIA | A7III |
|---|---|---|
| 60,0 – 69,8 s | 3 àncores | 3 àncores |
| 69,8 – 81,9 s | 3 + 1 tríada | 3 + 1 tríada (fins a 110) |
| 81,9 – 87,7 s | 3 + 2 tríades | — |
| **≥ 87,7 s** | **3 + 3 tríades** | — |

⚠️ **L'earthshine queda a 24 s, el terra exacte de
`min_earthshine_integration_s`, amb zero marge.** És la conseqüència que Pere
ha acceptat conscientment de la modalitat 3+3: una àncora perduda i el canal
falla la porta amb l'objectiu científic número u.

El compilador col·loca la muntanya sol, tan compacta com és segur, i deixa tot
el que sobra **davant del bloc de contacte de C3**, que és el marge que
protegeix el segon anell de diamant. A 91,0 s el marge surt de **4,29 s**,
per damunt dels +1,46 que l'esbós del traspàs preveia amb el seu padding de
0,45 s: el compilador empaqueta a 0,25 i el guanya. Perquè el bloc de C3
arribés tard, el canvi de base hauria de durar més de **10,8 s**, el doble del
cost mesurat.

⚠️ **La tríada de base 1/4 no té cap mesura al cos.** El seu pressupost —5,0 s
per 2,283 s d'exposició acumulada— porta més marge fix que els dos
disparaments que sí que estan mesurats, però és el deute de mesura d'aquesta
escala i està anotat al contracte.

**2. La R6 Mark III: 1/3200, finestres més llargues i el bloc fosc al mig.**

| | 0.9.4 | V1.00 |
|---|---|---|
| Obturació de contacte | 1/2000 | **1/3200** |
| Finestra de C2 | C2−17 → C2+4,75 | **C2−20** → C2+4,75 |
| Finestra de C3 | C3−~5 → **C3+4** | C3−~5 → **C3+20** |
| Bloc fosc | 2 s ×1, 15 s ×1, al davant | **2 s ×3, 10,3 s ×3, al mig** |
| Escala | 12 esglaons, 4,7 fotogrames cadascun | 12 esglaons, **2 cadascun** |
| Fotogrames a 91,0 s | 108 | **117** |

Cap dels tres primers canvis costa un sol segon de totalitat ni un sol canvi
d'exposició: 1/3200 té el mateix forat de 0,65 s entre fotogrames que 1/2000,
i les dues finestres creixen cap a temps que abans era **mort**. El de C3
n'ocupa 20 dels 25,75 s buits que hi havia entre l'últim fotograma de contacte
i el setter de la primera parcial filtrada, i és assegurança pura contra un C3
mal estimat: `research/11` diu que el relleu lunar pot moure els contactes
1-3 s i el lloc pot no saber-se fins una hora abans.

**10,3 s és el valor òptim de flota, no una retallada**: parteix el forat de
3,00 EV que la Sony deixa entre 1 s i 8 s en 1,42 i 1,58 EV, contra 1,96 i
1,04 amb els 15 s d'abans, i a sobre és 4,7 s més barat. El que sí que costa
és gruix d'escala. El compilador hi posa **quatre mitges passades** a 91,0 s
—dues abans del bloc fosc i dues després—, o sigui **dos fotogrames a cadascun
dels dotze esglaons**: `research/70` en preveia cinc i un repartiment desigual
de 3 i 2, i la cinquena es queda a 0,19 s de cabre-hi. **No es perd cap esglaó**
i els dotze salts d'1 EV es conserven. `10.3` és literal del menú del cos.

⚠️ **El senyal de veu «retira el filtre» és a C2−20**, o sigui que ara la
finestra obre al mateix instant que la veu i els primers fotogrames poden
sortir negres amb el filtre posat. No fa cap mal i Pere ho sap; el que no es
pot fer és arribar tard a les perles.

**Dues coses que el traspàs no havia previst i que s'han hagut de resoldre:**

- **El bloc fosc sencer costa 48,9 s i per sota d'uns 72,4 s de totalitat no
  hi cap.** Deixar-lo caure hauria tret **tot** l'earthshine de la R6 de 60 a
  72 s, que és perdre l'objectiu número u per no tenir-hi lloc. Una **escala**
  que no hi cap sencera continua sense posar-s'hi; el **bloc fosc** es retalla
  a 2+2 fotogrames i, si calgués, a 1+1. A 60 s hi caben dos de 10,3 s.
- **La finestra de C3 s'havia d'acotar per C4.** Amb un C3−C4 curt —les
  geometries d'assaig en tenen dotze segons— C3+20 xocava amb la quietud de
  C4 i el compilador refusava el programa. Ara s'escurça sola fins al valor
  històric de 4 s, exactament com la d'aproximació a C2 fa amb C1.

**3. Dues coses de l'operador.**

- **El TEST RUN dura 1 min 31 s**, el terra de planificació de Pere, en lloc
  dels 98,8 s de la mitjana de tres punts candidats. Assajar per damunt de la
  durada real amaga justament el tram que va just.
- **El rètol de totalitat hi és sempre i es llegeix**: `Totality 1min31.0s
  (91.0s) · C1–C4 span 0h56min40s`, un 22 % més gros i en negreta, i quan
  encara no hi ha contactes surt amb guions en lloc de desaparèixer.
- **El botó `Stop safely` ja no es mou sota el cursor.** Tenia la vora d'1 px
  en repòs i de 3 px en passar-hi, o sigui que creixia 4 px d'alt i d'ample i
  el text quedava arrapat a la vora. Ara la vora és de 3 px als tres estats i
  només hi canvia el color.

### El que canvia la 0.9.4: quatre correccions d'una auditoria externa

**Cap canvi de geometria, d'exposició ni de cadència.** Cap dels tres
objectius científics no es toca i la R6 fa exactament el mateix programa. El
que canvia és què veu l'operador, què escriu l'app al cos abans de la missió
i si el Mac s'adorm.

⚠️ **Aquesta versió no té cap run físic propi.** Hereta el terra operatiu de
la 0.9.3 i els seus tres runs del 9 d'agost, però les quatre correccions
d'aquí només estan verificades per regressió i pel QA portable.

Ve d'una auditoria de Codex sobre el candidat 0.9.3, verificada punt per punt
contra el codi i contra el run `20260809T031909`. Quatre correccions:

**1. Una missió perfecta ja no acaba en `WARNING`.** Al run de referència els
dos Sony van lliurar 35/35 i 41/41 amb `warnings: []` propis i van acabar
igualment en `WARNING`; la R6, amb els mateixos tres flags al perfil, va
sortir `COMPLETE`. La causa era `classify_mission_first_result`, que deriva
l'outcome del canal de `mission_warnings`, i els motors Sony i 6D hi posaven
els tres deutes d'autorització que §5 declara que **mai** poden ser un
`WARNING` operatiu. La R6 ja tenia la correcció feta i no s'havia portat als
altres dos. Ara els tres controladors comparteixen
`record_mission_first_authorization`, **byte-idèntica** als tres fitxers, que
els anota a `mission_advisories`. `WARNING` torna a voler dir que l'operador
ha de mirar alguna cosa. Proves:
`controller/tests/test_mission_first_authorization_advisories.py` (nou, exigeix
el mateix comportament als tres i inclou la prova que el defecte encara seria
detectable) i una d'integració a `test_mission_host.py`.

**2. El preflight dels dos Sony convergeix a 1/400 i no a 1/1250.** L'app
escrivia al cos un valor que el programa esborrava tot seguit: la primera
acció del disseny de blocs és `set_exposure` a 1/400, i a 1/1250 no hi surt
cap fotograma. Si aquell primer setter hagués estat refusat, les parcials
documentals haurien sortit **1,6 EV fosques** amb l'última base coneguda. La
R6 ja tenia aquesta coherència (1/320 als dos costats). Constant nova
`MISSION_STARTUP_SHUTTER_300GM` al generador, separada de l'obturació de
contactes dels perfils històrics, i el text d'operador i de recuperació manual
diuen el mateix número.

**3. La GUI descrivia el programa dens retirat a la 0.8.7.** Deia «40-group
AEB3 core», «105 CR3 in totality» i «dynamic HDR» a tres llocs, i els tests hi
fixaven el text. Ara diu el que la R6 fa de veritat: single HDR, una foto per
exposició, cap ràfega.

**4. L'antisuspensió ja no és una declaració, és una comprovació.** `held` es
posava just després del `Popen`, sense mirar si l'ajudant havia mort d'entrada
ni si el nucli publicava l'assercio. Ara hi ha una espera acotada que vigila
les dues coses i anota `assertion_verified` al registre; el camí sa costa
**23 ms** i queda confirmat contra `pmset -g assertions`. Un `False` o un
`None` no aturen res: continua sense ser mai un prerequisit. I s'ha tapat el
forat que quedava obert: **la GUI no retenia res**. Els dos hosts detached
retenen mentre dirigeixen una càmera, però entre obrir l'app i prémer START
—entrar els contactes i esperar C1 sense tocar teclat ni ratolí, que és
exactament el que macOS necessita per adormir-se— no hi havia ningú. Ara la
finestra reté des de `showEvent` i allibera al tancament.

⚠️ **La cadena de qualificació cold-start de la 6D de l'1 d'agost queda
tancada, i és el preu de la correcció 1.** Tres generadors de la 6D pinaven
`eclipse_capture.py` byte a byte, o sigui que declaraven immutable el motor de
missió dels dos Sony. **Cap fitxer de `controller/runs/` s'ha tocat** i el seu
binding continua essent cert: el que passa és que la font d'avui ja no
reprodueix aquells artefactes, i ni el verificador ni el carregador vius els
accepten. Les eines i les proves ho diuen ara explícitament, amb la constant
`V7_CHAIN_CONTROLLER_SHA256` separada del checkpoint viu. Decisió de Pere del
9 d'agost, amb el precedent del re-ancoratge del Canon v2 del dia 8.

### El que canvia la 0.9.3: el rang de 60 a 110 s deixa de ser una esperança

**Pere pot no saber on observarà fins una hora abans de l'eclipsi, i la
totalitat pot ser de 60 s a 1 min 50 s.** Fins ara ningú no comprovava que el
programa lliurés la missió a totes aquelles durades: es comprovava que
compilés. La 0.9.3 tanca aquesta diferència i corregeix les dues coses que
l'escombrada va destapar.

**1. Hi ha una porta d'acceptació per durada**, `gui/tools/qa_totality_
duration_gate.py`, descrita a §9. Escombra **7.044 casos** —quatre perfils,
tres geometries de parcials, de 60,0 a 110,0 s a passos de 0,1 s més les
fronteres de tram a la mil·lèsima— en **45 s**, i afirma els tres objectius,
la cua i el marge de C3. Té prova pròpia que sap fallar
(`gui/tests/test_totality_duration_gate.py`), inclosa una que refusa el
disseny que hi havia el 8 d'agost.

**2. El bloc de contacte posterior a C3 dels dos Sony passa de C3+0,45 a
C3+1,45.** Era el marge més prim de tot el sistema: si la totalitat real
sortia només **mig segon** més llarga que la que l'operador entra, cap
fotograma Sony no queia després del C3 de veritat i aquell cos es quedava
sense segon anell de diamant. Mesurat, compilant el programa i avaluant-lo
contra un C3 desplaçat:

| Error de C3 tolerat | R6 III | Sony, abans | Sony, ara |
|---|---:|---:|---:|
| totalitat real **més llarga** | +3,36 s | **+0,45 s** | **+1,45 s** |
| totalitat real **més curta** | −5,04 s | −2,45 s | −2,45 s |

La banda que travessa C3 passa de 2,9 a 3,9 s i deixa de ser d'un sol costat.
No costa cap fotograma. La cua de sortida diferida —el retorn a Single i la
base filtrada quan C3−C4 no dona per al drenatge— es desplaça el mateix segon
(`A7R3A_BLOCS_DEFERRED_SINGLE_S` 3,1 → 4,1 i `..._PARTIAL_S` 4,7 → 5,7):
sense això l'auditoria estricta refusava el perfil per 0,920 s de solapament.

**3. El setter que obre la finestra de C3 de la R6 ja no penja d'un sol
intent.** Cada setter del nucli single HDR declara
`clean_rejection_retries: 1`, i el worker el fa servir **només** si el cos ha
refusat amb un `was not set` net —mai per un menú col·lapsat, mai amb la
sessió tainted, mai per un `-110` o un timeout— i **només** si hi cap una
temptativa sencera de pitjor cas dins del deadline que el setter ja tenia. No
allarga cap finestra, no desplaça cap fotograma i no repeteix cap acció
ambigua: un rebuig net vol dir que el cos ha declarat que no ha adoptat el
write i que l'estat anterior continua conegut. És la mateixa regla que el
worker ja aplicava al camí de reconnexió (`safe_retry_used`). Sis proves
noves cobreixen els sis casos, inclosos els tres en què **no** s'ha de
reintentar.

⚠️ **Contrast amb Codex**: hi coincideix en el disseny però hauria posat el
camp només al setter de C3. S'ha mantingut a tots els setters del nucli
perquè el worker reconstrueix la llista d'accions i la compara **acció per
acció**: una regla condicional és una font de divergència, i una divergència
del mirall no degrada un fotograma, exclou el cos sencer de la missió. El
cost de la uniformitat és zero quan tot va bé.

**4. La QA física ja pot certificar els tres cossos i a qualsevol durada.**
`qa_physical_gui_test_run.py` refusava tot perfil amb confirmació manual que
no fos la R6 —i tots els perfils de missió en porten—, cosa que va obligar a
conduir el run del 9 d'agost amb un driver de sessió. Ara els dos Sony tenen
la seva pròpia porta: han d'entrar pel disseny de blocs i amb la seva
plantilla. I hi ha `--totality-s`, perquè el botó TEST RUN només sap fer
98,8 s i el tram curt no havia volat mai.

**Què NO ha canviat**: cap exposició, cap cadència, cap pressupost mesurat al
cos, i cap dels tres objectius. La geometria de la R6 és idèntica.

### El que canvia la 0.9.2: l'A7III fa blocs i hi ha més fotos abans de C2

**Dues coses demanades per Pere el 9 d'agost de 2026.**

**1. L'A7III executa el disseny de blocs, i el cos ha dit dues coses noves.**
El perfil de missió d'aquest cos apunta ara a una plantilla pròpia,
`lab_a7m3_blocs_choreography.json`, amb la seva identitat i el mateix nucli
declarat: bloc de contacte de C2 a C2−3,35/−0,45/+2,45, àncores d'earthshine a
base 1 s i bloc de C3 a C3−2,45/+1,45. El disseny és d'un programa, no d'un
cos. El que **no** s'hereta és res que sigui del cos, i el run del 9 d'agost
n'ha destapat dues coses que el pla no havia previst:

- ⚠️ **El sostre de cua de l'A7III són 30 imatges, no 36.** Mesurat amb
  `lab_a7m3_sostre_cua`, run `20260809T011523`: setze ràfegues sense drenar,
  la cua creix +3 per ràfega fins a **30** i les sis últimes ràfegues **no
  produeixen res**, sense cap error —30 confirmades de 48—. Amb la mateixa
  reserva d'una ràfega sencera que l'A7RIIIA, el sostre operatiu d'aquest cos
  són **27 imatges**: nou de contacte a C2, sis a C3 i **quatre àncores**. No
  és teòric: el run multicàmera `20260809T005844`, encara amb sis àncores, hi
  va portar 30 imatges pendents i **va perdre `blocs_contacte_05` sencer —el
  segon anell de diamant— en silenci**, que és exactament el mode de fallada
  que el sostre existeix per evitar. Els tres objectius científics es
  conserven: earthshine, els dos contactes travessats i el rang d'exposicions.
- ⚠️ **L'A7III entrega la ràfega en un altre ordre: −3, 0, +3.** L'A7RIIIA
  entrega la base primer (0, −3, +3) i aquest cos no. Verificat a l'EXIF de
  dos runs independents, `20260808T123003` (1/8 · 1 s · 8 s) i
  `20260809T005844` (1/2500 · 1/320 · 1/40). És el menú `Bracket order` de
  cada cos, no una diferència de model: si Pere vol igualar-los, és una
  entrada de menú. Mentrestant la plantilla declara el que el cos fa de
  veritat, que és el que va caldre fer amb l'A7RIIIA el 8 d'agost.

Per damunt d'uns 174 s de totalitat, quatre àncores ja no cobreixen el forat
que l'envolupant permet i l'A7III **torna al seu programa històric** en lloc
de quedar-se sense: el camí de sempre continua viu i provat.

**2. Més captures entre C2−25 i C2, sense arrossegar res després de C2.**
Aquesta és la condició que Pere va posar, i a cada cos vol dir una cosa
diferent perquè el que s'arrossega és diferent:

- **R6 Mark III: de 8 a 26 captures a la finestra.** La finestra de contacte
  de C2 obre ara a **C2−17** en lloc de C2−5, tres segons després del senyal
  de veu que diu de retirar el filtre. Són **18 fotogrames més** a la mateixa
  obturació fixa d'1/2000, o sigui **cap canvi d'exposició nou, cap ràfega i
  cap cua** —aquest cos escriu a CFexpress i no envia res al Mac—. I la
  graella creix **cap enrere des de C2−5**, de manera que cap instant a partir
  d'allà no es desplaça: l'escala HDR del mig, els dos fotogrames de 15 s i la
  finestra de C3 són exactament els d'abans. A 98,8 s el programa passa de 84
  a **102 fotogrames** i la totalitat continua tenint-ne 65.
- **Els dos Sony: de 2 a 5 captures a la finestra.** Tres parcials documentals
  més a C2−24,7/−23,5/−22,3, **amb el filtre encara posat i a 1/400**, que és
  l'exposició correcta mentre hi és. Van dins l'últim bloc de JPEG i **el seu
  drenatge s'acaba abans que el nucli comenci**, o sigui que la cua que entra
  a la totalitat continua essent zero. El selector de bràqueting i el canvi de
  base es col·loquen **tan tard com és segur** —C2−16,1 i C2−14,4, calculats
  enrere des de la primera pulsació— i **cap dels dos pressupostos no es
  toca**: el canvi de base continua tenint els seus 10 s, que és el doble del
  cost mesurat, i entre el seu final i el primer bloc de contacte hi queda un
  segon de reserva.

**Per què als Sony només n'hi caben tres.** Entre C2−20 i C2−3,35 el canal no
està lliure: hi ha el canvi de selector i el canvi de base, i just abans el
drenatge del bloc de parcials. I qualsevol fotograma **sense filtre** afegit
allà hauria de ser una ràfega de tres, que passaria la cua de 33 a 36 imatges
—el punt exacte on l'A7RIIIA deixa de disparar en silenci— i posaria en risc
el segon anell de diamant de C3. Amb la condició de Pere, el que hi cap són
les tres parcials filtrades.

### El que canvia el 8 d'agost a la nit: dues coses que ja no depenen de l'operador

**El balanç de blancs el comprova i el corregeix l'app.** Els quatre perfils
de missió declaren `/main/imgsettings/whitebalance` = `Daylight` a
`preflight.required`, `required_choices` i `auto_configure`. La regla és la de
sempre: **un sol intent, readback exacte, i un fracàs net no atura el canal**
—es registra el valor real i es continua capturant—. Dues decisions que no són
òbvies i que no s'han de desfer sense llegir `research/69`:

- **va sempre l'última de la llista de correccions.** Al worker Sony i al
  Canon v2, un rebuig net atura la cadena de correccions següents; aquesta és
  l'única que no decideix si el programa es pot executar;
- **sense `allowed_initial_values`.** Aquest camp converteix un valor inicial
  inesperat en `ConfigWritePreconditionError`, que sí que és un hard stop del
  canal. Un cos que arrenqui a `Cloudy` ha de convergir igualment.

`Daylight` i no una temperatura fixa perquè als Sony `colortemperature` és de
només lectura mentre el balanç no sigui `Choose Color Temperature`: la
temperatura numèrica exigiria dos writes encadenats i un estat intermedi.
**Cap run físic encara**: està verificat per regressió i pels bolcats de
capacitats, i s'exercirà al primer preflight.

**Mentre hi ha un run en marxa, el Mac no s'adorm, també amb bateria.** Els
dos hosts detached —`worker_host` mentre té un controlador viu, i
`mission_host` durant tota la missió— retenen
`/usr/bin/caffeinate -i -m -w <pid>`. `-i` és **l'única bandera que actua sense
corrent**; `-s` només val amb corrent i no s'hi posa; `-w` fa que l'ajudant es
mori sol si el host cau, o sigui que cap procés orfe no sobreviu un run. Es
reté per a qualsevol mode i no només `run`: una suspensió durant un preflight
mata la sessió PTP igual, i per `research/66` una sessió morta amb imatges
pendents deixa el cos inservible fins a treure-li la bateria. Es reté sempre i
no només amb bateria, perquè desendollar el cable enmig d'un run és justament
el cas; la font d'energia es llegeix (`pmset -g ps`, només lectura) i s'anota
al registre. Si `caffeinate` no hi és o no arrenca, es registra i es continua:
mai és un prerequisit. **No cobreix** tancar la tapa, la bateria esgotada, una
suspensió demanada per l'operador ni l'estona d'abans d'arrencar el run.

Regressió de la font actual:

- GUI 467/467 offscreen, amb el bloc de proves de l'A7RIIIA reescrit per al
  disseny de blocs, una prova nova que manté viu el camí retirat, i els
  fitxers nous `test_power.py` i `test_white_balance_convergence.py`;
- controlador 1.085/1.085 en aquesta branca, incloses les del pont EDSDK i
  `test_white_balance_startup_correction.py`;
- fuzz adaptatiu 67.392/67.392;
- perfils curts, JSON, `py_compile` i `git diff --check` verds;
- el bundle 0.9.0 instal·lat ha superat els **onze PASS** de
  `qa_macos_portable.py` —manifest, signatura, relocació, dispatch congelat,
  auditoria de missió i obertura/tancament GUI offscreen— amb 49 inputs, i
  els 49 tenen el mateix SHA que la font viva. Ad-hoc, arm64, no notaritzat,
  `LSMinimumSystemVersion` 26.0, 122,5 MiB. El bundle anterior queda a
  `gui/dist/Eclipse Command.app.previous-20260808T181737Z-18268`.

### El que canvien la 0.8.7 i la 0.8.8: la R6 ja no fa ràfegues

**El programa de missió de la R6 passa a ser una foto per exposició.** És el
canvi de comportament de captura més gros des de fa dies i té una sola causa:
les ràfegues AEB natives maten el menú d'obturació d'aquest cos —de 58
opcions a dues, sense tornada fins a un cicle d'alimentació— a un nombre de
pulsacions que **no es pot pressupostar** (82 a dues missions, 12 al banc).
Un programa que no pot preveure quan perdrà la capacitat de canviar
d'exposició no és determinista.

Tier nou `r6m3_vsd90ss_single_hdr_v1`, que substitueix el dens v4:

- **cap ràfega enlloc.** La regla «cap ràfega abans d'un canvi d'exposició»
  es compleix per construcció, no per ordenació;
- **estat físic nou**: Drive `Single` i bràqueting **`off`**. És l'estat que
  **sobreviu un cicle d'alimentació**: obturació i disparament són
  persistents, i el bràqueting, que s'esborra en cada cicle, ara ha d'estar
  apagat, que és exactament com queda. Amb el programa antic calia tornar a
  posar l'AEB a mà cada vegada;
- **finestres de contacte** a C2−5/+5 s i C3−5/+4 s, totes a **1/2000** fixa
  i a **0,40 s** per fotograma: és on hi ha les perles i l'anell de diamant,
  i 0,40 és el terra de pulsació del cos, no una tria;
- **escales HDR senceres** al mig: dues de 2 EV entrellaçades més una cua
  profunda de 2 s i **15 s**. Dues passades consecutives mostregen 1 EV;
- **una escala que no hi cap sencera no s'hi posa.** El que sobra és marge;
- mínim de totalitat **30 s**; per sota, el canal queda exclòs;
- a 98,8 s: **115 fotogrames al nucli, 92 dins totalitat, 62 a les finestres
  de contacte, 14 velocitats úniques de 1/2000 a 15 s i dos fotogrames
  d'earthshine**, amb 60 canvis d'exposició.

Evidència física del 7 d'agost a la tarda, run `20260807T143855` amb la
geometria exacta: **94/94 fotogrames, delta CFexpress exclusiu +94, 48 setters
amb readback exacte (417–466 ms), retard màxim 0,0 ms sobre 141 accions i el
menú a 58 opcions abans i després.** Al matí, amb la geometria de 0,50/0,62 i
earthshine de 8 s, el run `20260807T012943` havia donat 92/92 amb l'EXIF
verificat a 1/2000 i **8 s reals**, Electronic, AEB Off, Single, RAW
6960×4640, cos `[SÈRIE]`.
El perfil de missió materialitzat també té evidència pròpia: preflight
`20260807T020749` complete i zero avisos, i **run sencer llençat pel binari
del bundle**, `20260807T022642`, amb contactes reals: **54/54
fotogrames, delta CFexpress exclusiu +54, 14/14 setters amb readback, retard
màxim 1,42 ms i menú 58 → 58**. L'EXIF hi prova l'ordre complet
1/320 → 1/2000 → **1/320 després de C3**, que és exactament el que un
programa de ràfegues no pot fer. Detall: `research/58`.

**La cadència i l'earthshine de 15 s són de la 0.8.8**, i el que els fa
possibles és una mesura que no és proporcional a res: després d'un fotograma
de 15 s el cos refusa el canvi d'obturació amb `Device Busy` fins a **2,10 s**,
mentre que després d'un de 2 s l'accepta a 0,30 i després d'un de 8 s a 0,35.
Per això els fotogrames llargs paguen un suplement de **2,20 s** que els
altres no paguen, i per això el **lease de l'obturador** —el que garanteix que
la pulsació es tanqui— ha deixat de confondre's amb l'espera fins a l'ordre
següent. Detall: `research/61`.

El **run sencer per l'app amb la geometria definitiva**: `20260807T181413`,
pel binari del bundle 0.8.9 amb TEST RUN i totalitat de 98,8 s, dona **120
accions de captura de 120, delta CFexpress exclusiu +120** (5.357 → 5.477),
**61/61 setters** amb readback i zero Busy, retard màxim **0,010 ms** sobre
181 accions, menú 58 → 58, cleanup net, restore correcte a 1/320 i
`frozen_dispatch_ok=true`. El run anterior, `20260807T151346`, anava amb la
geometria de 94 fotogrames i va donar 99/99 amb delta +99. L'**EXIF de l'earthshine** ho tanca:
`572A7507.CR3` és de **15 s reals**, Electronic, AEB Off, Single, ISO 100,
RAW i cos `[SÈRIE]`. L'**EXIF de l'earthshine** el va tancar el run anterior: `572A7507.CR3` és de
**15 s reals**, Electronic, AEB Off, Single, ISO 100, RAW i cos
`[SÈRIE]`.

### El vespre del 7: el primer run multicàmera i el que va destapar

El run `20260807T210529`, el primer amb les dues càmeres alhora, va donar
**Sony 60/60 i R6 67 de 120**, amb 92 accions saltades, 20 reconnexions i
**70 fotogrames disparats amb una exposició que no era la prevista, 44 d'ells
a 0,5 s**. El delta CFexpress ho tanca: 67 CR3 exactes (`572A9196`–`572A9262`).

La causa **no** és el codi (mateix SHA als runs bons i dolents), ni la
geometria (tres runs de laboratori amb la mateixa van fer 175/175 accions),
ni la cadència (també va petar la geometria lenta), ni la bateria (va fallar
a 81-79 % i va anar bé a 78-76 %), ni la targeta, ni la segona càmera (els
runs trencats de les 18:48 i 19:02 tenien un sol cos al bus). És un **estat
intermitent del transport USB de la R6**: als runs dolents la pulsació té
mediana de 114 ms contra 20, i el `-110 I/O in progress` torna en 3 ms. A les
22:08 el cos **va desaparèixer sencer del bus** amb `USB_PHYSICAL_BLOCKED`.
**Comprovació física pendent: cable i connector de la R6.**

⚠️ **El run multicàmera `20260808T173855` posa el cable en dubte com a causa.**
La R6 hi va perdre **34 fotogrames de 120** i **42 de 61 setters** amb el
mateix `-110`, però **el patró de pèrdues és alternat**: 25 de les 33
distàncies entre pèrdues consecutives són exactament 2, en dos trams llargs
—fotogrames 6 a 26 i 87 a 117— on cau un sí i un no. Un connector
intermitent no fa això; això té la forma d'un cicle de pulsació que deixa el
cos ocupat i fa que la pulsació següent xoqui, es recuperi, i torni a xocar.
Zero incidències durant el drenatge de 33 imatges de la Sony: la interferència
entre cossos queda descartada per aquest run.

✅ **Diagnosticat, i no és el cable.** Detall: `research/67`. Són dues causes
de pressupost de temps, cap de transport:

- **27 de les 34 pèrdues**: la cadència de 0,40 s de les finestres de contacte
  **no té marge per construcció** —`r6m3_single_hdr_frame_gap_s("1/2000")` dona
  exactament el terra de 0,40— i en aquesta sessió el cos només acceptava una
  pulsació cada **0,80 s** (mesurat: 0,797–0,807 sobre quinze fotogrames). La
  pulsació arriba aviat, el cos la refusa, la recuperació costa 12 ms i la
  següent ja hi és a temps: d'aquí l'alternança;
- **7 de les 34**: el forat es compila amb l'obturació **prevista**; quan un
  setter és rebutjat, el fotograma anterior és més llarg del que el pla creu i
  la pulsació següent xoca. El worker sí que ho sap i hauria de pagar el
  suplement de l'exposició real.

El cable queda descartat per **`connection_epoch` = 1 tot el run**: la sessió
PTP no es va perdre ni una vegada, i les 34 recuperacions van durar 6-42 ms.
Bateria 98 %, ajustos idèntics al run bo i **més** espai a la targeta.

⚠️ **No és un terra fix, és una cadència sostinguda.** El cos absorbeix dues
pulsacions a 0,40 s i després només en sosté una cada 0,80. L'indicador és la
durada de la pulsació: **54 ms aïllada, 121 ms en seqüència**. El run
`20260807T172151`, amb la **mateixa** geometria, va fer 115/115 amb 54 ms de
mediana i 55 intervals seguits a 0,401 s. El mateix codi i la mateixa cadència,
o sigui que el que ha canviat és el cos —`availableshots` ha passat de 3.756 a
7.168, o sigui targeta formatada o **una altra targeta**— i el programa no
tenia ni una dècima per absorbir-ho. Això explica també el run trencat del 7 al
vespre, que tenia la mateixa signatura de 114 ms.

✅ **Corregit el 8 d'agost al vespre.** Pere confirma que no s'havia canviat
res —mateix cable, mateixa CFexpress—, i el número era l'equivocat des del
principi: **els 400 ms venien de la campanya EDSDK de `research/60`, dotze
pulsacions seguides i una altra pila de programari**. La mesura bona ja era al
repositori sense fer-se servir: l'escala de cadència del 6 d'agost, **per
gphoto2 i amb resistència**, diu que **0,60 aguanta 165 grups seguits, 0,55 és
marginal —un PASS i un FAIL— i 0,50 s'ensorra**.

`R6M3_SINGLE_HDR_FRAME_MIN_GAP_S` passa a **0,65** als dos testimonis
independents, el compilador de la GUI i el worker congelat. A 98,8 s el
programa passa de 115 a **88 fotogrames**, 69 dins la totalitat, i **conserva
les 15 exposicions úniques**; les finestres de contacte passen de 25 a 16 a C2
i de 22 a 14 a C3. El run del 8 d'agost, amb 25 previstos, en va lliurar 14.
**Menys sobre el paper i més a la targeta.**

**Segona ronda, run `20260808T192218` amb la cadència a 0,65.** Va fer el que
havia de fer i va destapar el defecte de sota: **el bloc de contacte de C2 va
sortir sencer i perfecte per primera vegada, 16 de 16**, i el conjunt va
millorar —77 de 88 fotogrames contra 86 de 120, 25 accions saltades contra 76,
11 recuperacions contra 34—. **Però la finestra de C3 es va perdre sencera**:
7 de 14 i **cap a l'exposició bona**.

La causa és la mateixa malaltia en un altre lloc. El pla va posar el setter que
obre C3 a **0,90 s d'un fotograma de 0,5 s**, el cos el va refusar amb
`was not set`, i com que **aquella finestra no té cap més canvi d'exposició per
disseny**, els tretze fotogrames del segon anell van sortir a 0,5 s. El model
de readiness deia exposició + 0,30, calibrat exactament sobre les mesures a 2,
8 i 15 s —marge zero— i **extrapolat a 0,5 s, on mai no s'havia mesurat**.

Corregit amb `R6M3_SINGLE_HDR_SETTER_AFTER_FRAME_GUARD_S = 0,35`: l'interval
entre fotogrames ara ha de cobrir també la readiness del setter que ve darrere,
`max(0,65 ; exposició + 0,40 ; ready + 0,35)`. El cas que va fallar passa de
0,90 a **1,15 s**; les finestres de contacte, a 1/2000, no es mouen. A 98,8 s
el programa passa de 88 a **84 fotogrames** amb les 15 exposicions úniques i
els dos de 15 s intactes; **per sota de 96 s es perd un dels dos de 15 s**, que
és el preu de no perdre el segon anell de diamant.

✅ **Verificat al cos.** Run `20260808T202023`, multicàmera a 98,8 s amb les
dues correccions posades: **84 fotogrames de 84, 49 setters de 49 sense cap
rebuig, zero accions saltades, zero recuperacions, retard màxim 0,011 ms sobre
133 accions**, bloc de C2 16/16 i **bloc de C3 14/14, tots a l'exposició
correcta**, 15 exposicions úniques, els dos fotogrames de 15 s, postflight
sencer correcte i el canal en **COMPLETE**. És el primer run en què aquest cos
no perd res, i confirma que les dues causes eren les dues i no n'hi havia cap
tercera.

⚠️ Queda la peça que faria la finestra de C3 robusta de debò: **un reintent
acotat** del seu setter. Aquest run no n'ha necessitat cap, però la finestra
continua depenent d'un sol setter: si algun dia el refusa, la torna a perdre
sencera. El contracte ho permet per a un `was not set` net i el worker ja en té
la maquinària.

Dues correccions, totes dues amb la regressió sencera verda (GUI 445/445,
controlador 1.079/1.079, fuzz 67.392/67.392):

- **un `-110` ja no costa una sessió PTP sencera.** Abans, cada incidència
  tancava i reobria el shell —0,9 s— i s'enduia dues o tres accions per tard:
  20 incidències van costar 53 fotogrames. Ara s'intenta primer
  `resync_live_transport`: probe de resincronització més rellegida real de
  l'obturació, amb pressupost dur de 300 ms, i només si falla es va al camí
  car. L'acció ambigua continua consumida, sense replay ni identitat nova. El
  camí sa no es degrada (151 s de run amb la correcció: 65 fotogrames, 40
  setters, zero incidències). **Falta exercir-lo sobre un `-110` recuperable
  real**;
- **els brackets de contacte de la Sony ara travessen C2 i C3.** Vegeu la
  secció de l'A7RIIIA.

**Determinisme demostrat amb les dues càmeres alhora.** La R6 va tornar al
bus i, amb les dues correccions posades, s'han fet un run sol
(`20260807T224123`: 181/181 accions, delta CFexpress exclusiu +120) i **dos
runs multicàmera concurrents** amb els dos cossos disparant a la vegada,
`20260807T224852` i `20260807T225500`, **idèntics mètrica per mètrica**:

| | Accions | Saltades | Recuperacions | Setters | Commits | Delta CF |
|---|---:|---:|---:|---:|---:|---:|
| R6 run 1 | 181/181 | 0 | 0 | 61/61 | 120 | **+120** |
| R6 run 2 | 181/181 | 0 | 0 | 61/61 | 120 | **+120** |
| Sony run 1 i 2 | 27/27 | 0 | 0 | — | 60/60 | 13 exposicions úniques |

La segona càmera al bus no degrada la primera: la pulsació de la R6 amb la
Sony disparant en paral·lel té mediana de 20,5 i 20,3 ms, contra 18,75 sola i
114 al run trencat.

**La geometria de la R6 no s'ha estret i és deliberat.** Mesura fresca sobre
61 setters: mediana 27,96 ms, p95 62,40, màxim 84,00, amb una ranura de
250 ms, o sigui **3× de marge**. Baixar-la a 200 ms compraria set fotogrames
de 120 i deixaria 2,4× en una acció d'un sol intent on un retard costa el
fotograma i l'escaló d'exposició. Els 0,40 s entre fotogrames són el terra de
pulsació del cos, no un cost nostre.

**Robustesa a la durada de la totalitat.** La R6 la té: de 40 a 200 s manté
sempre els dos contactes travessats, 14,9 EV i els fotogrames de 15 s.
L'A7RIIIA no la tenia: el seu tram bo només s'aplicava entre 90 i 100 s, i el
sostre de 100 no descrivia cap límit físic. Amb 98,8 s previstos, **dos
segons d'error a l'estimació la feien caure a `dense_74`: 10 EV i cap àncora
d'earthshine en comptes de 15 EV i dues.** Sostre pujat a **104 s**, que és
fins on el tram conserva la densitat temporal que el projecte exigeix. El
terra de 90 s sí que és físic —per sota de 88 el bracket de 3,2 s del punt
mitjà se solapa amb la finestra de re-trigger— i es conserva. Verificat al
cos a 101 s, run `20260807T233944`: R6 186/186 accions i delta CFexpress
exclusiu **+119**; Sony 60/60 amb els contactes a C2−2,90/+0,01/+2,91 i
C3−2,00/+0,91.

⚠️ Aquests dos paràgrafs descriuen el tram **fixed9**, que la 0.9.0 ha
retirat: el llindar de 90 s, el sostre de 104 i la pèrdua d'earthshine per
sota de 90 ja no descriuen el programa viu. Es conserven com a context del
run del 7 al vespre, que sí que es va fer amb aquell tram.

**La Sony fa la meitat de fotogrames que la R6 i és del cos, no del
programa.** Un terç de la seva totalitat (31,8 s de 98,8) se'n va en
descàrrega, i no es pot treure: `/main/settings/capturetarget` només ofereix
`sdram` i `card+sdram`, o sigui que **no hi ha mode només-targeta** i cada
fotograma ha de passar per la SDRAM cap a l'amfitrió a 0,51 s per imatge. La
R6 escriu a CFexpress i no envia mai res al Mac.

Detall complet: `research/63`.

### El que canvien la 0.8.3 i la 0.8.4 respecte de la 0.8.2

Cap canvi de comportament de captura: continuar amb l'última base coneguda,
zero replay, cap estat físic nou desconegut. El que canvia és el diagnòstic.

- **El menú d'obturació col·lapsat es diu pel seu nom.** Un valor absent del
  menú viu ja no es registra com `clean_busy_was_not_set` —no hi ha cap Busy—
  sinó com `unavailable_choice_menu`, amb el menú observat. L'excepció
  dedicada és `UnavailableChoiceError` i l'esdeveniment nou és
  `config_choice_menu_unavailable`.
- **La restauració rellegeix abans de rendir-se**, dins una finestra de
  cleanup de 6 s només de lectura, i escriu un sol cop si el valor reapareix.
- **El cost fotogràfic es diu en una frase**: `summarize_exposure_fallbacks`
  agrega a `mission_advisories` quantes captures i quants fotogrames han
  sortit amb una base que no era la prevista. És informació, mai un
  `WARNING` operatiu, i de moment només viu a `result.json`.
- **El preflight registra `choice_count`** a cada observació, que és el número
  que distingeix un menú sa d'un de col·lapsat amb una sessió nova.
- **La reducció de soroll d'exposició llarga entra a la checklist física de
  la R6.** No es pot escriure per programari: libgphoto2 publica 82 paths i
  cap és aquest —`highisonr` és la d'ISO alt—, `customfuncex` retorna `bad
  length`, i a l'EDSDK v13.20.21 `kEdsPropID_NoiseReduction` és `EdsImageRef`
  i de només lectura. Si queda activada, cada exposició llarga en porta una
  de fosca igual al darrere i qualsevol àncora d'earthshine costa el doble.
- **Un canal amb identitat PTP pendent ja no queda exclòs.** Si el cos té una
  ruta PTP viva, el canal s'arrenca igualment i el worker exigeix model i
  sèrie exactes abans de qualsevol write o trigger; si no els prova, falla
  dins el seu canal. Excloure'l abans d'arrencar era una segona porta
  redundant. Sense cap ruta PTP viva —mass storage o absent— sí que queda
  exclòs, amb `reason_code: no_live_ptp_route`, perquè no hi ha res a
  intentar. El botó `Start mission` compta aquests cossos i ho diu:
  `· N unverified`.
- **Sonda d'earthshine per a la R6**:
  `controller/tools/compile_r6m3_earthshine_probe.py`. L'AEB d'aquest cos
  topa a ±3 EV amb tres fotogrames, o sigui que el nucli dens no passa de
  0,8 s i els 8 s només s'obtenen amb la base a **1 s** (tríada 1/8, 1, 8).

El forense complet és a
`research/55_MENU_OBTURACIO_COLLAPSAT_R6_2026-08-06.md`. La prova de
reobertura de sessió ja està feta i és a
`research/56_PROVA_REOBERTURA_SESSIO_R6_2026-08-06.md`: **el menú mort és
del cos, no de libgphoto2** —tres sessions PTP independents el veuen igual—
i el llindar no és un comptador de pulsacions, perquè al banc va caure a la
12 i a les dues missions a la 82.

### El que canvia respecte de la 0.8.1

La 0.8.2 incorpora, tot verificat al cos:

- **routing per sèrie PTP**: el port de gphoto no identifica cap cos —el
  mateix `usb:000,001` respon A7III o R6 segons el `--camera`— i quan no hi
  ha ruta exacta cada port candidat rep un `get-config` acotat. Al run
  `20260806T184228` cap canal va quedar exclòs;
- **nucli dens R6 v4**: 318 CR3 compilats dins totalitat a 98,8 s contra els
  105 anteriors, amb la geometria dimensionada per la durada;
- **àncores d'earthshine a l'A7RIIIA**: dos fotogrames de 8,00 s verificats a
  l'EXIF del run `20260806T111952`;
- **parcials a 30 s** per a tota la flota;
- **el sondeig de bateria fixa el model**: abans mostrava la càrrega d'un cos
  a la fila d'un altre.

Afegir o canviar un input del manifest invalida el bundle fins reconstruir-lo.
El footer incorpora `Sync UTC`: primer consulta `time.apple.com` només en
lectura; sense Internet/DNS/NTP no demana autorització ni toca el rellotge. Si
el servidor respon, macOS demana autenticació nativa, activa l'hora automàtica
i la GUI només declara èxit amb un bound nou `BOUNDED` de 400 ms o millor. No
està disponible durant cap missió, START pendent o operació de càmera.
⚠️ El paràgraf que hi havia aquí descrivia el primer single-HDR de la 0.8.2
(1/2000, 8 s, 0,50/0,62 s i 74 fotogrames) com si fos viu. És evidència
històrica, no autoritat actual. El programa vigent és el de §3/V1.02:
1/3200, 10,3 s, 0,65/0,25 s i inici nominal C2−15. H90, HDR RAW,
tracking/òptica VSD90SS i ciència continuen visibles com a informació de
programa, no com a `WARNING` operatiu.

El trigger body-specific R6 usa `Press Full MF` -> `Release`. Libgphoto2
implementa el press MF complet com half+full; `Release Full` deixava el
half-press actiu i causava els Busy post-AEB. El run `20260805T185716` valida
sota AEB les sis adopcions i el restore, però només com a ledger
`card_only_committed`; no eleva els CR3 a RAW verificats.

L’evidència física A7RIIIA de la 0.7.8 va completar 75/75 JPEG, 72 durant
totalitat, sis brackets ràpids 9/9 i dos llargs 9/9 fins a 3,2 s, sense skips,
recovery ni replay. La font 0.8.0 amplia C2/C3 a 1/4000–1/15 per cobrir millor
perles i anells, però encara no té gate físic RAW/solar. `Check cameras now`
passa pel pont preflight sense captures. La 0.8.0 permet `--mission-first`
amb el perfil font R6 en preflight, sense exigir una acció ISO accidental;
RUN continua obligat a usar el controlador R6 dedicat i la materialització
C1-C4 exacta. La 6D convergeix en quatre
etapes. El candidat privat exposa ISO 100/200/400 com a writes preflight
explícits, amb identitat exacta, readback i aïllament per canal. L'autocheck i
la missió no depenen dels botons i cap valor o resultat ISO bloqueja cap canal.
Si una operació acaba WARNING, el host incorpora la darrera causa exacta del
controlador —inclòs stderr quan falta `result.json`— i la GUI la separa dels
advisories que no han causat l’operació. La detecció inicia l’autocheck i les
correccions declarades segures automàticament; l’operador no ha de prémer ISO
per fer llançable una càmera amb identitat exacta.

`confirmed_images` només és gate quan el contracte exigeix payload local. En
un perfil explícit `card_only`, timeline, ledger, postflight, cleanup i restore
complets donen `COMPLETE` operatiu amb `card_only_committed`; el manifest
CR2/CR3 i l’inspector continuen com a evidència física pendent, no es dedueixen
del ledger ni del resultat verd de l’app.

### TEST RUN físic històric de referència (0.7.2)

Run agregat:

```text
controller/runs/codex_20260802_gui_072_final/runs/
20260802T140916_multi_camera_mission_run
```

Amb totalitat de 98,8 s. L’A7III encara usava l’AP130 i la Canon es va
executar a ISO 100; no transfereix qualificació al perfil 300GM ni a la
finestra ISO 1600 actual:

| Cos | Resultat | Dins totalitat | Última captura planificada |
|---|---:|---:|---:|
| Sony A7III | 60/60 JPEG | mínim >30 | C4−8 s |
| Sony A7RIIIA | 83/83 JPEG | 72 | C4−30 s |
| Canon 6D | 31 triggers AEB, 93/93 commits esperats card-only | >30 | C4−38,575 s |

No hi va haver misses, skips, warnings de cronologia ni trigger exacte a C4.
La primera captura dels tres cossos és exactament C1. Cleanup i estat final
van quedar coneguts als tres canals.

L’A7RIIIA va completar dos brackets llargs amb exposicions EXIF de 3,2 s i un
bracket final 9×1 a C3−3,1 s. Els drains de 27 i 36 JPEG van durar 19,297 s i
26,423 s. Evidència específica:
`research/49_POLIMENT_CONTACTES_I_C3_A7RIIIA_2026-08-02.md`.

La Canon usa AEB ±3 en Continuous: cada press produeix deliberadament tres
RAW en ordre `1/250 → 1/2000 → 1/30`. No intentis commutar obturació o AEB
després d’un RAW: el cos real ha retornat `PTP Device Busy 0x2019`. La GUI ha
de mostrar `AEB +/-3 · 3 RAW/trigger`, no presentar-ho com tres triggers.

## 4. Perfils operatius

| Cos | Perfil de missió |
|---|---|
| A7III | `controller/profiles/candidate_a7m3_300gm_short_checkpointed_1x5_3x9.json` (plantilla `lab_a7m3_blocs_choreography.json`) |
| A7RIIIA | `controller/profiles/candidate_a7r3a_300gm_short_checkpointed_1x5_3x9.json` (plantilla `lab_a7r3a_blocs_choreography.json`) |
| Canon 6D | `controller/profiles/candidate_canon6d_fixed_aeb3_continuous_cardonly_v2.json` |
| Canon R6 Mark III | `controller/profiles/candidate_r6m3_vsd90ss_cfexpress_cardonly_v1.json` |

La Canon 6D es despatxa a `controller/eclipse_capture_canon_v2.py`; la R6 Mark
III a `controller/eclipse_capture_r6m3.py`; les Sony comparteixen
`controller/eclipse_capture.py`. El perfil font R6 és visible,
`CANDIDATE_NOT_PRODUCTION`, `timing_qualified=false` i
`materialization_required=true`, però ja no porta un blocker de captura. Només
la materialització exacta del core single HDR pot crear una ordre
RUN; H90 i els gates físics/òptics continuen com a warnings explícits. No
transfereixis timings, buffers, opcions PTP o gates entre models.

H1 R6 ja és PASS físic: 10/10 RAW Single CFexpress a inicis de 500 ms, delta
exacte `87 -> 97` (`572A2375..2384`) i extrems CR3 íntegres, diferents i
coherents amb 1/640. És Sigma/One-shot AF/ISO12800 advisory, no VSD90SS. A2
també és PASS: una sola adopció `1/640 -> 1/1250`, readback exacte i zero
captures. V2 és PASS complet de trigger i V/RAW: el snapshot únic recuperat
fixa 98 CR3, el delta `97 -> 98` afegeix només `572A2385.CR3` i la descàrrega
manifest-bound confirma RAW 6960x4640, 1/1250, Single, AEB off i cos exacte;
zero replay. El snapshot fresc `20260804T011252` confirma que Pere ha recuperat
`RAW` complet tant a SD com a CF, amb les 23 opcions de format disponibles i
els mateixos 98 CR3 byte-idèntics a l'inventari anterior. No llegeix
l'obturació: `1/125` és només l'últim valor històric observat, no el preestat
actual. El restore històric s'havia refusat correctament abans de write; zero
writes/captures, cleanup net i `physical_state_unknown=false`. No repetir V2,
descàrrega ni restore.

`1/640` continua sent només el baseline històric de transport H1. La sèrie
solar nova del cos i tren exactes —26 CR3 R6 III + VSD90SS + ASSF100 OD 5,0 a
~7,3°— fixa la fotosfera filtrada de missió a `1/320`, ISO 100 i Electronic per
al cas canònic únic de 10°/700 m. No hi ha multiperfil per ubicació. Això tanca
l'ancoratge d'exposició filtrada, però no declara H90, tracking, focus,
setters dinàmics ni ciència RAW final.

H1, A2 i V2 es van executar amb el worker v1 immutable, SHA-256
`6f438b1d44540b23fd00cdfb6711114dd51ac43d485a713a676f88251e2ddff3`.
El primer preflight read-only `20260804T011350`, encara amb v3, es va aturar
pel path Sony inexistent `/main/capturesettings/capturemode`; zero
setters/triggers/captures, cleanup net i estat físic conegut. La v4 va corregir
els sentinels R6 i `20260804T013353` ja n'ha validat físicament la lectura,
també amb zero escriptures o captures. El worker v5, SHA-256
`c43a2387f87549ce76fa79a43bb638ba817cc267d4679a00c7ec8f6d456fb439`,
va afegir el contracte post-write fail-fast. El worker viu v6, SHA-256
`b133181c2fa0e7b6b859e175bc62b442e02144b88ff55d5db2adf3e3c812f0f1`,
consumeix sense replay una acció operativa ambigua i conserva les següents si
la mateixa sessió continua segura; no activa recovery ni hereta cap
qualificació física nova. Les eines de snapshot i CR3 mantenen un únic guard de
`ptpcamerad` fins al primer ACK i fallen abans de PTP si `Image Capture` és
obert; mai el tanquen automàticament.

Els perfils de `controller/profiles/lab_*` són assajos, no programes visibles
d’operador. Els perfils legacy es conserven per regressió, però no són
autoritat per canviar la missió actual.

## 5. Mission-first i classificació d’incidències

### Informació que mai no és WARNING

- checklist incomplet: és només un recordatori visual i continua editable
  durant Sync UTC;
- perfil candidat, timing/H90 no qualificat i deute científic o òptic: han de
  quedar visibles a la descripció del programa, però no degraden l'estat
  operatiu de l'app.

### Advisory operatiu: registra i continua el canal si és possible

- bateria baixa;
- setting divergent o lectura incompleta;
- acció tardana que ja no cap;
- fitxer RAW de targeta encara no reconciliat;
- salut UTC degradada per a un TEST RUN relatiu;
- qualsevol valor ISO.

Regla ISO sagrada: les Sony recomanen ISO 100. La Canon 6D declara ISO 1600
per desplaçar la finestra AEB nativa de 6 EV cap a la corona feble, perquè no
pot fer un canvi ràpid de 9 EV només amb bràqueting. Són baselines advisory:
`Auto`, `0`, `Unknown`, absent o qualsevol altre valor no pot produir
`FAILED`, bloquejar un stage, cancel·lar captures ni causar sortida no-zero
amb `mission.enabled=true`. La missió no escriu ni restaura ISO. El candidat
privat V1.02 (`1.0.2`) exposa ISO 100/200/400 només com a writes preflight
ordenats per un clic explícit. Exigeix identitat exacta, una mutació per cos,
readback i resultat `SET`/`NOT SET`; només un Busy literal `was not set` es
pot reintentar de forma acotada. Els botons no estan disponibles durant
missió, scan, Sync UTC o una altra operació i mai poden convertir l'ISO en
gate. La release pública 0.8.0 continua immutable i sense aquests controls.

### Continuïtat Mission First i hard stops per cos

- Abans de capturar, model/sèrie divergents, propietari PTP ambigu o una sessió
  anterior no tancable exclouen només aquell cos.
- Durant una missió operativa materialitzada, un Busy, `-110`, timeout o
  trigger possiblement compromès consumeix aquella acció i la posa en
  quarantena. No hi ha replay immediat ni tardà; si el mateix cos conserva
  identitat, propietat i estat operatiu segurs, s'intenta la següent acció
  programada.
- Els runs operatius de l'app no activen recovery: així cap reconnexió pot
  reexecutar l'acció consumida. Si una futura política específica d'un cos
  arribés a admetre recovery, només podria preparar accions futures.
- Una identitat divergent, una mutació de configuració amb estat físic
  desconegut o la impossibilitat de garantir el ledger sí que aturen aquell
  canal. Els perfils lab que declaren `stop_on_first_error=true` conserven el
  seu fail-fast de qualificació.
- Un delta RAW divergent queda com a deute d'evidència i mai autoritza
  catch-up. Cap incidència d'un cos atura les accions segures dels altres.

## 6. USB, PTP i processos

L’ordre dels cables canviarà sovint, també el dia de l’eclipsi. No conservis
mai `usb:BUS,DEVICE` entre deteccions.

Ordre obligatori:

1. inventari read-only d’IORegistry;
2. resolució de port per vendor/product/serial USB;
3. obertura exclusiva PTP;
4. confirmació exacta de model + serial PTP;
5. preflight i només després writes/triggers autoritzats.

`gphoto2 --auto-detect` pot etiquetar malament els cossos quan conviuen. És
una pista, no autoritat. La GUI conserva una càmera vista prèviament com
`Not connected` durant una caiguda transitòria; una càmera mai vista no
s’inventa. Cada cos té worker, sessió i resultat independents.

Abans d’un build, prova física o handoff comprova que no queden processos
propis `Eclipse Command`, `mission_host`, `eclipse_capture`, `gphoto2` o QA.
`ptpcamerad` del sistema pot reaparèixer i no s’ha de matar per rutina.

**Mentre l'aplicació és oberta, cap altra eina no toca cap càmera.** No és una
recomanació d'higiene: cada cicle d'escaneig, i com a molt un cop cada 30 s,
`reap_stray_gphoto_processes` envia **SIGTERM i després SIGKILL a tot procés
`gphoto2` que no pertanyi a una missió viva de l'app**. És una decisió
d'operador del 30 de juliol de 2026 i està al codi a propòsit: un `gphoto2`
orfe reté una càmera com un ostatge. La conseqüència, però, és que una ordre
manual llançada amb l'app oberta pot morir **a mig drenatge**, i llavors el
cos es queda amb imatges marcades com a pendents i ningú a l'altra banda.
**Aquest estat no el desfà apagar i encendre: només treure la bateria.**
Durant un run de veritat el risc és baix —`monitor.active` fa retornar el
tick abans de tocar res—; el perill és la preparació. Detall: `research/66`.

**Un `caffeinate` fill d'un host propi no és un procés perdut.** Des del 8
d'agost de 2026, `worker_host` i `mission_host` en llancen un cadascun per
impedir que el Mac s'adormi mentre dirigeixen una càmera. Porten
`-w <pid del host>`, o sigui que **es moren sols quan mor qui els ha
demanat**, també si el host cau de cop. Al handoff no s'han de matar a mà: si
no queda cap host propi viu, tampoc en queda cap `caffeinate` propi. Detall:
`research/69`.

## 7. Què està demostrat i què falta

### A7III

**Des de la 0.9.2 aquest cos executa el disseny de blocs**, amb plantilla
pròpia i amb dues coses que són seves i no de l'A7RIIIA: el **sostre de cua
de 30 imatges** —27 operatives, quatre àncores— i l'**ordre de lliurament de
la ràfega, que és −3, 0, +3**. Les dues estan mesurades i el detall és a §3.
Per damunt d'uns 174 s de totalitat torna al programa històric d'aquest bloc,
que continua viu i provat.

Demostrat històricament amb AP130: cronologia curta, routing resilient i TEST
RUN 60/60. Amb el perfil 300GM actual, el run interromput `20260803T004303`
va confirmar 58/60 JPEG i obturació real `1/1250`; no va completar C1–C4.
Falta un gate SD/ARW específic del cos, solar/òptica 300GM i els assajos de
desconnexió/canvi de bateria. No heretis evidència de l’A7RIIIA ni de l’AP130.

### A7RIIIA + Sony 300 mm f/2,8

✅ **Post-eclipsi (15-08): l'Skywatcher va fer DOS SALTS a mig de la totalitat**
(+223 px i −715 px, ~12′ i ~39′). **Causa, per testimoni de Pere: en treure el
filtre solar va moure la lent de 300 mm**; el filtre era fora abans de C2
(contactes ben exposats) i la pertorbació es va alliberar amb retard en dos
temps (C2+30 i C2+50). **La DSC06990 (àncora 2 d'earthshine) va quedar moguda
perquè la muntura va cedir durant l'exposició** — misteri resolt. Entre salts,
estabilitat de 0,5-1 px; les àncores 1 i 3 tenen només 0,5-0,75 px de moguda
interna i són la millor font d'earthshine de la flota. Escala de placa
mesurada **3,234″/px**. Canònic: `research/72`.

✅ **L'escala nova de `research/70` està IMPLEMENTADA des de la V1.00.**
Contactes a base **1/800** —tríada 1/6400 · 1/800 · 1/100— i una muntanya de
base a mig eclipsi —1/4 → 1 s → 1/4—, amb **tres àncores d'earthshine sempre**
i d'una a tres tríades de base 1/4 segons la durada. Els llindars reals que el
compilador produeix són **69,8 / 81,9 / 87,7 s**, més favorables que els
70 / 83,3 / 89,5 de l'esbós perquè empaqueta a 0,25 s i no a 0,45. El detall és
a §3 «El que canvia la V1.00».

⚠️ El preu, acceptat conscientment: l'earthshine queda a **24 s, el terra
exacte de la porta de durades, amb zero marge**. I la tríada de base 1/4 **no
té cap mesura al cos**.

**El que segueix descriu la mecànica de blocs —instants, cua, drenatge,
pressupostos— que continua essent exactament la mateixa.** On digui base
1/320, ara és 1/800; on digui «fins a sis àncores», ara són tres més les
tríades.

#### El programa viu és el disseny de blocs (0.9.0, 8 d'agost al vespre)

**La coreografia densa i el tram fixed9 que en derivava ja no els tria cap
perfil.** El perfil de missió apunta a la plantilla nova
`controller/profiles/lab_a7r3a_blocs_choreography.json`
(`mission_choreography_core: a7r3a_blocs`) i el compilador en fa un programa
de **33 fotogrames de totalitat en onze ràfegues natives de tres**:

- **bloc de contacte de C2** a C2−3,35/−0,45/+2,45, base **1/320**, tríada
  **1/320 · 1/2500 · 1/40** —el cos entrega sempre la base primer, i les
  perles i el primer anell són abans de C2—;
- **fins a sis àncores d'earthshine** a base **1 s**, tríada
  **1 s · 1/8 · 8 s**, la primera a C2+11,90 i cadència **12,00 s**;
- **bloc de contacte de C3** a C3−2,45/**+1,45** —+0,45 fins a la 0.9.3, que
  deixava el segon anell penjant de mig segon de marge; §3—, mateixa base i
  tríada —el segon
  anell surt a C3 i just després—;
- **cap drenatge dins la totalitat i una sola posició de selector de C2 a
  C3.** Les 33 imatges es paguen senceres després de C3.

El nombre d'àncores el deriva la durada i **no es refusa mai un programa**:
sis a partir de 96 s, cinc a 90, quatre a 72, tres a 60. Per sota de 60 s el
cos cau al tram compacte de l'envolupant; per damunt de 200 s, al tram
genèric, que amb totalitats llargues hi posa més fotogrames dels que el
sostre de cua permetria aquí. **El sostre operatiu són 33 imatges** (mesurat
36, reservada una ràfega sencera): el cos deixa de disparar en silenci i el
que perdria serien els últims fotogrames, que són els anells de C3.

Conseqüència declarada i vigilada: com que no es drena res entre C2 i C3, el
cos arriba a C3 amb 33 imatges i **la primera parcial documental posterior no
pot ser abans de C3+43,2 s**. El forat de la fase `partial_after` puja de 30 a
**42,77 s** amb la geometria de l'eclipsi —50,8 s al pitjor cas de tot el
rang—, sempre per sota del minut, i el compilador falla tancat si passa de 52.
El retorn a `Single Shot` va **darrere** el drenatge i no abans: el TEST RUN
del 2 d'agost va demostrar que una escriptura d'obturació es completa amb 36
JPEG pendents però que **canviar el selector amb aquell deute no és fiable**.

Tornar enrere és un camp de JSON —`mission_choreography_template_id`— i el
camí retirat continua provat (`test_a7r3a_retired_dense_choreography_still_compiles`).

**Verificat al cos pel binari del bundle**, run `20260808T170650` amb
totalitat de 98,8 s, C1−C2 de 60 s i C3−C4 de 82 s: **38/38 confirmades i
descarregades, 0 perdudes**, 26/26 accions, **zero saltades, zero avisos de
cronologia, zero recuperacions**, identitat verificada, cleanup i restore
correctes i `physical_state_unknown=false`. **Retard màxim 0,056 ms.** Els
moments reals són exactament els previstos: contactes a C2−3,35/−0,45/+2,45 i
C3−2,45/+0,45 —el bloc de sortida va a +1,45 des de la 0.9.3, o sigui que
aquest run no descriu la geometria viva—, àncores de C2+11,90 cada 12,00 s.
El **drenatge de 33 imatges
va durar 18,308 s** sobre un pressupost de 24 —cua 33 → 0 en onze intents— i
va acabar amb el selector escrivible, que és el que autoritza el retorn a
Single de després. L'EXIF de les 38 confirma sis àncores amb **1 s · 1/8 ·
8 s reals** a ISO 100, cinc blocs de contacte amb 1/320 · 1/2500 · 1/40 i
cinc parcials a 1/400, totes del cos `ILCE-7RM3A`.

D'aquell run en va sortir **un sol defecte, i era nostre**: la plantilla
declarava la tríada de contacte com `1/2500 · 1/320 · 1/40` quan el cos
l'entrega **sempre amb la base primer**, i les àncores com `1` quan l'EXIF
diu `1 s`. Els biaixos declarats `[0, −3, +3]` ja eren correctes i van passar.
El postflight, que sí que exigeix ordre exacte, ho va convertir en WARNING amb
38/38 imatges bones. Corregit a la plantilla, al contracte i a les proves.
⚠️ Els perfils de laboratori `lab_a7r3a_blocs_*` conserven l'ordre antic
perquè porten `require_exact_shutter_order=false` i són evidència d'uns runs
concrets; no els prenguis com a autoritat de l'ordre d'entrega.

El que segueix és l'evidència que ho sosté i el context del programa anterior.

Demostrat: 83/83 JPEG, 72 durant totalitat, drains mesurats i bracket fins
C3. El tram del mig de la totalitat ja no fa els dos brackets llargs de base
1/5, que topaven a 3,2 s: ara hi ha les **àncores d'earthshine**, dues
ràfegues de cinc a base 1/8 que donen 1/500, 1/60, 1/8, 1 s i **8 s**. El run
`20260806T111952` ho verifica a l'EXIF, amb 59/59 confirmades. Quantes
àncores hi caben ho decideix la geometria; si no n'hi cap cap, el cos torna
al tram anterior en comptes de refusar de compilar.

**Els brackets de contacte travessaven els contactes pel costat equivocat i
això ja està corregit.** El tram els posava a C2+0,0/+2,9/+5,8 i a
C3−6,0/−3,1, amb un comentari que deia que a C3−6 s hi ha el segon anell de
diamant. És fals: a C2 el Sol ja és tapat i les perles i el primer anell
passen **abans** de C2; a C3 el segon anell surt **a C3 i just després**. El
programa tancava l'obturador 0,23 s abans del segon anell. La conseqüència
operativa era pitjor que la fotogràfica: **els dos anells depenien només de
la R6**, i al run del 7 d'agost no en va quedar cap. Ara els blocs són
**C2−2,9/0,0/+2,9** i **C3−2,0/+0,9**. El drenatge posterior a C3 i els tres
passos de sortida ja no s'ancoren a offsets fixos de C3 sinó al final del
bracket i del drenatge; la finestra d'earthshine es continua calculant contra
una reserva de 6,0 s perquè el llindar dels 90 s no es mogui.

Verificat al cos, run `20260807T222902`: **60/60 confirmats i descarregats**,
27/27 accions, zero saltades, zero reconnexions, pla complet, moments reals
**C2−2,89/+0,01/+2,90** i **C3−2,00/+0,91**, i EXIF amb **13 exposicions
úniques de 1/4000 a 8 s** i les dues àncores de 8 s reals a ISO 100. Els ARW solars del cos i tren exactes fixen la parcial
filtrada a ISO 100, Silent/Electronic i `1/400` per al cas canònic 10°/700 m.
El fixed 9x1 aplica aquest valor tant a les parcials Single pre-C1 com a una
única parcial Single post-C3, després del drain i del retorn qualificat a
Single; la totalitat queda intacta.
Falta delta SD ARW exclusiu de missió amb hash/integritat/EXIF/ledger i la
resta del gate òptic. JPEG/ACK no és prova de RAW a targeta.

**El cost d'una àncora de 8 s ja està mesurat**: l'acció sencera dura
**11,21 s** i la cadència demostrada d'extrem a extrem és **12,0 s**. Els
11,6 s que el disseny de blocs assumia queden entre els dos, o sigui que la
suposició era bona. No prenguis els 11,21 s com a cadència: és la durada de
l'acció, no un interval provat entre pulsacions. Run `20260808T120011`: tres ràfegues
`C 3.0/3` des de base 1 s, **9/9 confirmades**, retenció de 9,61 s, retard
màxim 0,003 ms, drenatge i restore complets, i EXIF amb l'ordre
**1 s · 1/8 · 8 s** a ISO 100 —o sigui `0, −3, +3 EV`, amb l'extrem al mig i
no al principi—. Amb els pressupostos que l'auditoria estricta exigeix, el
compilador en treu **sis a partir de 96 s i cinc a 90**; el disseny de paper
en deia sis a 90 perquè no pagava ni la tolerància de retard ni el jitter.
La cadència **mínima** no s'ha mesurat i no es persegueix:
compraria una setena àncora, un 8 % de senyal/soroll, al preu de la cacera de
marge que la nit del 7 al 8 va costar dues bateries i dues targetes.

**El rellotge de l'A7RIIIA no es pot escriure ni llegir per PTP, i el seu
desfasament s'ha de tornar a mesurar.** El bolcat read-only complet del cos
—`controller/runs/20260808T173224_..._capabilities`, 105 camins, zero
mutacions, identitat verificada— no publica **cap** camí de data o hora:
`/main/settings` només té `capturetarget`, i entre les propietats PTP
estàndard hi ha `0x5010` i `0x5013` però **`0x5011` (DateTime) és absent**.
L'únic camí és el menú del cos, que ajusta al minut.

El desfasament es **mesura** millor del que s'ajusta. Creuant les 16 pulsacions
del run `20260808T170650` amb les seves marques EXIF, l'únic valor compatible
amb totes les exposicions curtes era **entre −0,95 i −0,85 s**: el cos anava
**0,90 s endarrerit** amb una incertesa de 0,1 s. El mètode és bo i es pot
repetir amb els fotogrames de qualsevol run.

Pere va reajustar el rellotge a mà el 8 d'agost al vespre i aquella mesura va
quedar invalidada. **Mesura vigent, del run `20260808T173855`: el cos va
+0,38 s AVANÇAT** respecte del Mac, amb la finestra entre +0,30 i +0,45 s
sobre deu exposicions curtes. L'ajust manual va anar bé —el senyal horari es
va prémer prou fi—, però el que val és el número mesurat, no l'ajust.

⛔ **Si es torna a tocar el rellotge, aquest +0,38 s deixa de valer.** La
mesura nova surt sola dels fotogrames de qualsevol run; no cal sonda dedicada.
El **rellotge de la R6 continua sense mesurar** i no es pot mesurar per aquesta
via: és `card_only` i no baixa cap fitxer al Mac. Caldrà llegir l'EXIF dels CR3
de la CFexpress després d'un run amb contactes coneguts.

⚠️ **L'EXIF d'aquests cossos marca el final de l'exposició, no el principi.**
Les tres imatges d'una àncora surten de la mateixa pulsació i porten
`:41, :41, :49`: la de 8 s va vuit segons més tard. En creuar earthshine amb
la R6, el fotograma **va començar 8 s abans del que diu la seva marca**.

**La reducció de soroll d'exposició llarga està apagada als dos cossos
Sony.** `libgphoto2` no publica aquest ajust a cap dels dos, igual que a la
R6, o sigui que es mesura: un fotograma Single de 8 s i una lectura de
`/main/other/d215` **1,5 s després d'alliberar**. Amb la NR apagada la imatge
ja hi és; amb la NR encesa el cos encara fa un fotograma fosc igual de llarg i
no hi pot ser fins als ~16 s. A7III `20260808T120939` i A7RIIIA
`20260808T121317` donen tots dos **1 · 2 · 3**, i de l'A7RIIIA ja se'n sabia
la NR apagada per una via independent —la ràfega de tres, amb 9,125 s
d'exposició acumulada, li cap en 9,6 s de retenció—. Confirmació definitiva
pendent, i són deu segons: mirar el menú de l'A7III.

**L'àncora costa el mateix als dos cossos Sony, i el drenatge no.** El run
bessó a l'A7III, `20260808T123003`, dona 9/9 i **11,205 s** d'acció contra
11,215 de l'A7RIIIA: el que mana és la suma d'exposicions de la ràfega, que
no depèn del cos. El drenatge sí que en depèn: amb nou imatges exactes,
l'A7RIIIA en vol **tres intents i 6,32 s** i l'A7III **dos i 4,07 s**, o
sigui 4 contra 6 imatges per intent i un factor **1,55×** que coincideix amb
el que `65` havia mesurat per una altra via. La granularitat de ~2 s per
intent és el `wait_window_s` del perfil, no del cos.

**El sostre de la cua de l'A7RIIIA són 36 imatges, i falla en silenci.** Run
`20260808T132331`, setze ràfegues de tres sense drenar pel mig: la cua creix
+3 fins a **36** i les quatre últimes ràfegues **no produeixen res**. El cos
no es queixa ni s'encalla; deixa de disparar. En un pla que en demanés més,
els fotogrames perduts serien **els últims**, que és on hi ha el bloc de C3 i
el segon anell de diamant. Amb això, el disseny de blocs ja no el limita el
temps sinó la cua: nou fotogrames de contacte a C2 i sis a C3 en deixen 21,
o sigui **set àncores**, que és el mateix que permetia el temps amb l'extrem
a 8 s. Escurçar l'àncora a 4 s —base 1/2 s, verificat a l'EXIF com
1/2 · 1/15 · 4 s, acció de 7,61 s— allibera temps que **ja no es pot gastar**,
i deixa les mateixes set àncores amb menys llum.

**Decisió tancada el 8 d'agost al vespre, després de dos contrastos
adversaris (Codex i Fable 5): sis àncores amb l'extrem a 8 s, 33 fotogrames.**
Base **1 s** → tríada **1 s · 1/8 · 8 s**.

Una decisió anterior del mateix dia deia set àncores de 5 s i **estava mal
argumentada**: comparava set de 5 s contra set de 8 s —que no caben— i **mai
comparava sis de 8 s**, que és l'alternativa real i que domina en tot: **33
fotogrames** amb tres de coixí contra el sostre, **48 s d'integració contra
35** (+17 % de senyal/soroll) i el bloc de C3 travessant el contacte igualment.
L'argument del cremat també cau: amb l'earthshine ~9,8 mag per sota de la
Lluna plena, a f/2,8 ISO 100 el gris mitjà cau a ~15-16 s a Medina amb cel net
i la saturació a ~80-90 s, o sigui que **a 8 s el disc queda ~3,5 EV per sota
del cremat**. El que sí que pot velar-lo és el pedestal de llum difosa del cel
a X=6,4, que continua sense quantificar. La penalització d'apilar per soroll
de lectura és de 0,3-0,7 % per fotograma: numèricament buida.

**El sostre operatiu és 33 i no 36.** Un run 36/36 demostra que pot anar, no
que tingui marge, i la fallada silenciosa es menja els últims fotogrames, que
són els anells de C3.

**La transferència fotomètrica d'aquest document és 0,2-0,3 EV optimista**:
escalar tot el coeficient d'extinció per pressió només val per al Rayleigh, i
si l'AOD del CAMS ja és la columna sobre el lloc, escalar-la el descompta dues
vegades. Corregit, el requisit d'earthshine amb calima puja a ~8-8,6 s.

Verificat al cos, perfil `lab_a7r3a_blocs_3c_6anc_8s`, run `20260808T152215`:
**33/33, 13/13 accions, zero saltades, zero avisos de cronologia, zero
recuperacions, retard màxim 0,674 ms**, cua màxima 33, i EXIF amb
1/2500·1/320·1/40 cinc vegades i **1 s · 1/8 · 8 s sis vegades**.

**El pla sencer ja s'ha provat al cos amb òptica**, perfil
`lab_a7r3a_blocs_3c_7anc_5s`, run `20260808T142826`: **36/36 confirmades,
14/14 accions, zero saltades, zero avisos de cronologia, zero recuperacions,
retard màxim 0,502 ms**, cua màxima 36, drenatge final de 21,65 s i EXIF amb
1/640·1/5000·1/80 cinc vegades i 1/2·1/13·**5 s** set vegades. El run anterior,
`20260808T142307`, va destapar un defecte de disseny nostre: **el canvi de
base costa ~5,3 s i el pla li pressupostava 4,47**, que era el màxim de 53
mostres històriques, i això feia sortir els dos blocs de contacte de C3 amb
969 i 570 ms de retard. Corregit ampliant els marges dels dos canvis de base a
6,55 i 12,05 s, tots dos trets del repòs que ja hi havia: **no costa cap
fotograma**. Qualsevol geometria futura ha de pressupostar **5,3 s** per canvi
de base.

**Amb òptica posada cauen dues suposicions més.** El **sostre de 36 no depèn
de la mida de la imatge**: amb JPEG reals de 946 KB de mitjana contra els
341,5 KB dels fotogrames negres, la corba és idèntica, o sigui que és un
recompte i no un pressupost de memòria. I el **drenatge amb imatges reals
només és un 9 % més car** —0,573 s per imatge contra 0,526, i els mateixos
quatre per intent—, cosa que desmenteix l'advertència del `65` que calia un
factor d'escala gran.

**La base dels blocs de contacte és 1/320, no 1/640.** La fixen dues fotos del
mateix instant de Durango 2024, aportades per Pere amb els CR2 originals i el
KMZ de Jubier. Les circumstàncies ja no s'assumeixen: el màxim va ser a
−104,139/25,289 a les 18:17:17 UTC, el rellotge de la 6D anava en hora
peninsular i la seqüència situa `_MG_9570` **cinc segons després de C3**, amb
el **Sol a 70,14°** i X = 1,063. Normalitzades a f/2,8 ISO 100, les dues
referències són **1/1250** (6D, perla amb cromosfera i corona interior, només
0,006 % de píxels saturats) i **1/20663** (A7III a f/4,5, perla compacta sense
corona): **quatre EV de separació**. No es contradiuen —són dues fotos
diferents del mateix instant— i vol dir que **l'escena al contacte abasta 4 EV**.
Transferides a Medina donen dues bandes: **1/1006–1/201** per a la foto amb
corona i **1/16635–1/3325** per a la perla compacta. Amb base **1/320** la
tríada **1/2500 · 1/320 · 1/40** cobreix les dues: 1/2500 a 0,4 EV de la perla
compacta, 1/320 dins la banda de la foto amb corona, i el 1/40 no perd corona
interior perquè el **1/13** de les àncores ja la cobreix. Verificat al cos,
run `20260808T145426`: **36/36, 14/14 accions, zero avisos de cronologia,
retard màxim 0,570 ms** i EXIF amb la tríada exacta.

⚠️ **Rectificació**: una versió anterior d'aquest bloc deia que 1/5000 era
«3,6 EV per sota de res del que hi ha a l'escena». **Era fals**, i sortia
d'ancorar-ho tot a la referència del 6D sola. Allà baix hi ha la perla al seu
instant més brillant. Detall: `research/66` §4 quinquies.

**Sobre cada quant drenar, els números hi són i la decisió és de Pere.**
Sobre les 27 imatges del disseny a 90 s, partir la cua per la meitat costa
**1,3 àncores de sis a l'A7RIIIA** i 0,9 a l'A7III; drenar després de cada
àncora en costa 2,3 i 2,2. El cos car és justament el que porta l'earthshine,
i el senyal/soroll li cau de 2,45× a 2,17×. Amb l'earthshine com a objectiu
número u, la recomanació és **no drenar dins la totalitat** i atacar el risc
per l'altra banda, que és no deixar morir cap sessió. Detall: `research/66`.

### Canon 6D

Demostrat a ISO 100: Stage A físic, comportament AEB, timing i 93 commits
card-only al TEST RUN. La reconciliació 629→815 CR2 quadra amb dos runs de
93, però el darrer run no té manifest pre/post exclusiu lligat a cada action
ID. ISO 1600 és la decisió de missió per arribar a detalls coronals més
febles, no un gate físic ja superat. Falten Stage B físic amb el runtime viu,
manifest exclusiu, simultaneïtat qualificada i prova solar/òptica. Aquest
deute és informació, no `WARNING`: no tornis a posar `PROGRAM BLOCKED` si el perfil v2
continua materialitzable.

### Canon R6 Mark III

✅ **Post-eclipsi (15-08): seguiment verificat amb les imatges de la
totalitat.** Taxa solar confirmada (sideral i lunar excloses). **La deriva
real està mesurada de les parcials: 0,689″/s de deriva lliure post-C3, de la
qual ~0,21 és refracció i ~0,48 muntura (error polar ~2°, alineació diürna);
les correccions manuals de Pere són visibles als fotogrames.** A totalitat la
deriva resolta és ~0,61″/s ≈ 29 px, compartida per Sol i Lluna: el relatiu no
es toca. Escala de placa mesurada **2,158″/px** (focal 494 mm ✓). Contactes
reals llegits de les imatges: C2 −1,0 s i C3 +102,7 s del predit → totalitat
real 103,7 s, clavada a la predicció. Sensor a 41-43 °C. I el calibratge dels
CR3 té una trampa documentada: el negre de metadata de libraw és fals; el
pedestal real és 511-512 pla. Canònic: `research/71`.

✅ **Els dos canvis d'escala de `research/70` estan IMPLEMENTATS des de la
V1.00**, i n'hi ha un tercer que s'hi va afegir. (1) El bloc fosc passa de
**2 s ×1 i 15 s ×1** a **2 s ×3 i 10,3 s ×3, al mig de la totalitat**. (2) La
finestra de contacte de C3 s'allarga fins a **C3+20** amb la constant nova
`R6M3_SINGLE_HDR_CONTACT_POST_C3_S`, acotada per C4 i amb terra al valor
històric de 4 s. (3) L'obturació de les dues finestres passa de 1/2000 a
**1/3200**. La V1.00 obria C2 a −20; la V1.02 la retalla nominalment a
**C2−15**, amb primera foto a −14,75, i conserva C3+20. A 91,0 s la V1.01
tenia 117 fotogrames de nucli i la V1.02 en té **109**. El detall és a §3.

Alta parcial demostrada via gphoto: identitat exacta, RAW card-only, Single,
CFexpress i un delta exclusiu `+1 CR3` amb contenidor ISO-BMFF íntegre. El G1
es va fer amb Sigma 35 mm, One-shot AF i ISO 160 advisory; no acredita el
VSD90SS, focus manual, AEB, buffer ni cronologia d’eclipsi. L’inspector propi
és `controller/tools/inspect_cr3.py`; no reutilitzis l’inspector TIFF de
CR2/ARW ni activis `require_raw_integrity` dins el worker card-only.

H2 continua demostrant 20/20 Single RAW card-only a 1/640, amb inicis cada
500 ms i delta exclusiu +20. El gate fix històric va demostrar 40/40 captures
amb Timer 2 s i delta CFexpress exclusiu `572A2545..2584`. Els gates natius
AEB3 G1, G5 i G40 van demostrar respectivament +3, +15 i +120 CR3, amb
Continuous high speed, AEB +/-3 i base 1/320.

El core R6 viu materialitza una foto per exposició. A 91 s són **109 captures
de nucli**, 55 dins totalitat, amb 0,65 s de cadència mínima i 0,25 s reservats
per setter; les quinze obturacions de captura van de 1/3200 a 10,3 s. Un
setter pot reintentar-se una vegada només davant un rebuig net que demostri
que el valor no s'ha adoptat. El worker no espera l'exposició, o sigui que el
cost del fotograma viu sencer dins la reserva de readiness i aquesta ha
d'incloure el temps d'obturació. Qualsevol geometria o acció divergent falla
abans d’escriure el perfil. L’ordre RUN R6
usa `--allow-candidate --mission-first --recover-disconnects`: la recuperació
és exclusivament per a accions futures després d’una pèrdua de bateria/USB;
l’acció ambigua queda consumida i no es repeteix.

El programa afegeix, fora d'aquest core body-specific, un fotograma
documental per minut entre C1 i C2-30 s i entre C3+30 s i la finestra quieta
de C4, a 1/320 filtrada. Aquest delta és QA offline, no endurance físic
transferible.

Això no declara H90 PASS, HDR RAW ni ciència de totalitat. El run físic
`20260807T012943` acredita 92/92 fotogrames, delta CFexpress exclusiu +92 i
54 setters amb readback exacte, i l'EXIF confirma 1/2000 i 8 s reals, però
continua `card_only_committed`. Falten manifest/inspecció CR3 exclusius, un
run físic sencer del perfil de missió materialitzat amb ancoratge real a
C2/C3, tres històries C1-C4,
tracking/VSD90SS/òptica, focus solar i ciència RAW final;
la GUI ho mostra com a deute persistent. Electronic, estabilització, focus i filtre són
comprovacions físiques de l’operador, i els CR3 s’han de reconciliar després a
CFexpress. Un write o trigger ambigu es consumeix sense replay, i identitat/propietat
divergent, estat físic desconegut o ledger no garantible aturen només la R6.
EDSDK està autoritzat per a estudi i desenvolupament específic R6, però no
substitueix cap gate físic ni autoritza una implementació de rendiment sense
un delta separat; cap dada de la 6D o les Sony es pot transferir a aquest cos.
El repositori i el bundle públics són exclusivament gphoto2/libgphoto2: EDSDK,
headers, frameworks, binaris, llicències i el backend privat queden exclosos.

**L'EDSDK ja està mesurat i la decisió és gphoto2.** Dotze execucions del
programa sencer contra el cos el 7 d'agost: setter divuit vegades més barat
—24 ms contra 415-453—, 92/92 amb la geometria de missió, **112/112 amb una
d'atapeïda (+22 %)**, delta CFexpress global +510 i menú intacte a 58 opcions.
No es fa servir perquè **quan falla es penja**, a un sol esglaó de geometria
del punt de treball, i només se'n surt apagant el cos. **On es penja no està
diagnosticat**: a les tretze execucions on es va arribar a cridar
`EdsCloseSession` va tancar net, i l'única que es va penjar ho va fer dins el
bucle de fotogrames, sense arribar al tancament. La hipòtesi viva és que el
camí d'error no drena la cua d'esdeveniments que Canon demana bombejar. A més és privat i no empaquetable, depèn de TCC i no es passa el cos
netament amb libusb. Si algun dia es reprèn: primer el penjat, després
empaquetar, i només llavors el +22 %. Detall: `research/60`.

**Decisió de Pere, 7 d'agost de 2026.** L'eclipsi del 12 es fa **amb gphoto2**,
i l'EDSDK queda reduït a **eina de preparació abans de la missió**: escriure el
**tipus d'obturador** —cap dels 82 paths de libgphoto2 no el publica i el canvi
sobreviu el cicle d'alimentació— i, si algun dia cal, algun altre ajust que
gphoto2 no pugui tocar. Fora d'això no entra a cap camí de captura. La regla
pràctica que se'n deriva: **l'SDK escriu, s'apaga el cos, s'encén, i la missió
sencera va per gphoto2**, perquè les dues piles no es passen el cos netament i
mentre l'ICA el reté gphoto2 no el pot ni obrir.

Compte amb què **no** arregla l'SDK: la **reducció de soroll d'exposició
llarga** no es pot escriure per cap dels dos camins —`customfuncex` retorna
`bad length` i `kEdsPropID_NoiseReduction` és `EdsImageRef` i de només
lectura—, o sigui que continua essent una comprovació física de l'operador. El
run del 7 d'agost en dona evidència indirecta que és apagada: després d'una
exposició de 15 s el cos torna a acceptar ordres a 2,10 s, i amb la foto fosca
en caldrien uns quinze.

Aquesta decisió es revisa si algun dia es donen les tres condicions, i per
aquest ordre: penjat diagnosticat i reparat, backend empaquetable dins el
contracte d'inputs, i traspàs entre piles acotat i mesurable. Hi ha eclipsis
nous el 2027, o sigui que la revisió té sentit; per al del 12 d'agost de 2026,
no.

De la mateixa campanya en surt una dada **del cos i no de l'SDK**: el terra de
pulsació sostinguda és de **400 ms** —a 300 el cos rebutja amb 21 `DEVICE_BUSY`
sobre 12 fotogrames—, i el programa hi va ara. Aquest terra és el que mana la
geometria: no és nostre i no es pot tocar.

**I una troballa que sí que era nostra: el setter no el pagava el transport.**
Dels 445 ms d'un canvi d'exposició, **400 eren un `sleep` fix del worker**
entre l'escriptura i la comprovació. Mesurat al cos: l'escriptura costa 12 ms,
la lectura 4, i **el cos ja ha adoptat el valor quan torna l'ACK** —adopció de
3,4 ms de mediana i 16 de màxim, sempre confirmada a la primera rellegida—.
L'espera cega passa a ser una enquesta amb el mateix sostre, i l'acció de
setter sencera baixa a **28,8 ms de mediana i 67,8 de màxim**. Amb això la
ranura del setter cau de 0,55 a **0,25** i el programa passa de 94 a **115
fotogrames a 98,8 s**, 92 dins totalitat: el mateix +22 % que hauria comprat
l'EDSDK, per gphoto2. Validat al cos: run `20260807T172151`, **115/115, delta
CFexpress exclusiu +115, 61/61 setters, retard màxim 0,023 ms i menú 58 → 58**.
Detall: `research/62`.

El gate G1 VSD90SS v2 continua pendent d’execució física.
`controller/tools/certify_r6m3_cardonly_gate.py` exigeix un CR3 reobert per
cada commit i reconcilia snapshot, manifest, ledger i delta CFexpress; H1
falla deliberadament aquesta certificació completa perquè només se'n van
inspeccionar els dos extrems. La GUI falla tancat per font directa, perfil
sintètic, materialització divergent, identitat PTP no verificada o
`materialization_ready=false`. Cap d’aquests guards qualifica el programa HDR,
H90, VSD90SS o ciència solar.

## 8. Arquitectura i fitxers d’autoritat

```text
gui/eclipse_command/main_window.py   GUI i estat d’operador
gui/eclipse_command/domain.py        perfils visibles i routing
gui/eclipse_command/adaptive_profiles.py  compilació C1–C4
gui/eclipse_command/mission_host.py  supervisor multicàmera
gui/eclipse_command/worker_host.py   host detached d'un sol canal
gui/eclipse_command/power.py         antisuspensió del Mac durant un run
gui/tools/report_run.py              informe foto a foto d'un run, només lectura
gui/tools/render_hdr_coverage.py     repartiment de l'HDR de corona entre la flota
gui/tools/qa_totality_duration_gate.py  porta d'acceptació per durada (§9)
gui/tools/run_regression.py          la regressió de §9, repartida entre nuclis
controller/eclipse_capture.py        motor Sony compartit
controller/eclipse_capture_canon_v2.py motor Canon 6D congelat
controller/eclipse_capture_r6m3.py   worker R6 card-only sense recovery/replay
controller/profiles/                 perfils font i laboratori
gui/packaging/macos/                 inventaris i recepta PyInstaller
controller/runs/                     evidència física; no netejar
research/README.md                   índex d’evidència i recerca
```

Els tres inventaris fixos de perfils empaquetats han de coincidir exactament:

- `gui/packaging/macos/runtime_manifest.py`;
- `gui/packaging/macos/EclipseCommand.spec`;
- `gui/packaging/macos/source_manifest.py`.

La prova `gui/tests/test_packaged_profiles_coherence.py` ho fa fail-closed.
Quan afegeixis un perfil de missió, actualitza les tres llistes i la prova
abans de construir.

## 9. Proves offline

Executa sempre des de l’arrel. `QT_QPA_PLATFORM=offscreen` és obligatori.
No canalitzis la sortida per `tail`.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=gui QT_QPA_PLATFORM=offscreen \
  gui/.venv312/bin/python -u -m unittest discover -s gui/tests

PYTHONDONTWRITEBYTECODE=1 \
  gui/.venv312/bin/python -m unittest discover -s controller/tests

PYTHONDONTWRITEBYTECODE=1 gui/.venv312/bin/python \
  gui/tools/qa_adaptive_timeline_fuzz.py .

PYTHONDONTWRITEBYTECODE=1 gui/.venv312/bin/python \
  gui/tools/qa_totality_duration_gate.py .

PYTHONDONTWRITEBYTECODE=1 gui/.venv312/bin/python \
  controller/tools/build_short_profiles.py --check

git diff --check
```

**El fuzz i la porta de durades no comproven el mateix, i cap dels dos no
substitueix l'altre.** El fuzz diu que un pla compila, valida i es resol; la
porta diu que el programa **lliura la missió**. La diferència no és teòrica:
dels 1.081 casos que el fuzz dona per bons a l'A7RIIIA, 520 no tenen cap
àncora d'earthshine i 104 tenen amplitud EV zero. Passen igualment, perquè
ningú no els ho preguntava. I el fuzz **no té la R6**, que és el cos que
porta el bracketing de corona i les dues finestres de contacte contínues.

La porta afirma, per a **cada** durada de 60,0 a 110,0 s i per als quatre
perfils, els tres objectius de §1 bis més dues coses que ja han costat
fotogrames de veritat: que la **cua fins a C3** no passi del sostre del cos
—és el que va fer emmudir l'A7III i li va costar el segon anell— i que hi
hagi **marge davant un error de C3**, perquè la durada real pot no ser la
que l'operador entri.

Si un error de compilació obre un `QMessageBox`, el test headless pot semblar
penjat. Investiga el modal; no esperis indefinidament ni matis processos
aliens.

## 10. Build macOS

Només amb `SERIAL_WRITES`, zero GUI/worker/controlador/gphoto2 propi i inputs
congelats:

```bash
gui/build_macos_portable_app.sh

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=gui QT_QPA_PLATFORM=offscreen \
  gui/.venv312/bin/python gui/tools/qa_macos_portable.py \
  "gui/dist/Eclipse Command.app"
```

Després:

1. verifica versió, signatura, arquitectura i manifest del bundle real;
2. comprova que cada input incrustat té el mateix SHA que la font viva;
3. executa les proves offscreen del bundle;
4. només si Pere ha autoritzat GUI física, registra/obre la nova app;
5. publica l’enllaç `gui/dist/Eclipse Command.app` i el SHA nou;
6. conserva com a màxim la versió actual i **vuit** bundles antics
   `.previous-*`. El rollback immediat és el més recent que sigui vàlid, i
   quan n'hi hagi algun que no ho sigui —una intermèdia, una versió que un
   run va desmentir— s'ha de dir explícitament a `§3` i al QA, perquè el
   criteri «el més recent» sol, amb vuit, ja no basta. En passar de vuit,
   esborra pel final i mai el rollback vigent.

No confonguis build verd amb qualificació física. No notaritzat significa que
Gatekeeper pot demanar una obertura explícita; `gphoto2` continua sent una
dependència externa.

## 11. Documentació i evidència

- `README.md`: vista d’operador i estat actual.
- aquest `CLAUDE.md`: contracte d’agent i punt de represa.
- `AGENTS.md`: arrencada curta per qualsevol agent.
- `gui/QA_REPORTS.md`: índex de QA; V1.02 és el candidat privat local i 0.8.0
  continua sent la release pública immutable.

**La regressió es pot passar en paral·lel.** `gui/tools/run_regression.py`
executa exactament les mateixes ordres de §9, una per procés: **128 s contra
372 s**. Les ordres de §9 continuen essent la referència; això és com
executar-les de pressa, no una alternativa amb un abast diferent.
- `research/README.md`: índex temàtic; documents antics són context, no estat.

**Analitzar un run vol dir generar-ne l'informe, no resumir-lo.** Decisió de
Pere del 8 d'agost de 2026: cada vegada que es mira com ha anat un run, se li
ha de donar l'informe foto a foto —instant teòric contra real i exposició
prevista contra la de veritat, una fila per fotograma i per cos—, no només un
resum en text. L'eina és `gui/tools/report_run.py`, és de només lectura i
sense arguments agafa el run més recent de l'arrel d'estat de l'app:

```bash
gui/.venv312/bin/python gui/tools/report_run.py --markdown
```

El teòric el treu del **perfil materialitzat** que va executar el run, no del
perfil font; el real, de l'instant de la pulsació; i l'exposició real, de
l'EXIF de la imatge baixada. Un cos `card_only` no en baixa cap i llavors
l'eina posa el readback del setter vigent i ho diu, perquè és evidència més
fluixa. `gui/tools/` no entra al manifest de fonts, o sigui que tocar aquesta
eina no invalida cap bundle.

**I tot informe acaba amb el repartiment de l'HDR de corona entre la flota.**
Decisió de Pere del 9 d'agost de 2026, al costat de la cobertura de fenòmens.
L'eina és `gui/tools/render_hdr_coverage.py`, també de només lectura, i emet un
SVG autònom a partir dels perfils materialitzats del run:

```bash
gui/.venv312/bin/python gui/tools/render_hdr_coverage.py -o cobertura.svg
```

Ho **normalitza tot a equivalent f/2,8 ISO 100**, que és l'única manera de
posar els dos trens al mateix eix: el VSD90SS va a f/5,5 i recull **1,95 EV**
menys llum que el mateix temps al 300 GM. ⚠️ Aquest 1,95 EV és el pont bo per
als fenòmens **sense filtre**; els 0,65 EV que van circular surten de comparar
les dues parcials filtrades i **només valen per a la fase parcial**.

L'obertura de cada tren és intenció de disseny i no la comprova cap preflight
(§7), o sigui que l'eina llegeix la real de l'EXIF de les imatges baixades i
avisa si divergeix. Al run `20260809T134344` va cantar l'A7III a **f/14 amb un
Sigma 50 mm**, −4,64 EV respecte de la calibració, que és exactament el forat
que el recompte de fotogrames no veu.

⚠️ **Fins al 10 d'agost aquest dibuix no arribava mai al paper.** L'eina
emetia el rectangle de fons de l'SVG amb `width="100%%"` —un escapat de
`%`-format en una cadena que no hi passa—; els navegadors ho toleren i
WeasyPrint refusa l'SVG sencer i el deixa en blanc. Corregit. Si algun dia
tornes a veure la cobertura en blanc en un PDF, mira primer si l'SVG porta
`%%`. I si el converteixes a paper, **A4 apaïsat**: en vertical la taula
foto a foto perd les tres columnes de la dreta, que són l'exposició prevista,
la real i l'evidència.

**I tot canvi d'obturació o de nombre de fotos es pinta abans de discutir-lo,
un dibuix per cada càmera afectada.** Norma de Pere del 9 d'agost de 2026. No
val descriure el canvi amb una taula: amb tríades rígides de ±3 EV i un sostre
de cua, moure un sol número mou l'escala sencera, i on cau cada esglaó respecte
de les bandes de fenomen no es dedueix llegint el perfil.

El format és fix i són **dos panells**: a dalt l'escala, amb un carril «ara» i
un carril «proposta», un punt per esglaó amb l'obturació i el nombre de
subfotogrames, i les bandes de fenomen de fons; a baix, temps contra exposició,
amb C2 i C3 marcats i **una línia que segueix la base del bràqueting**, que és
el que ensenya la forma del programa. ⛔ No el converteixis en un diagrama de
barres ni en cap altra cosa: aquesta versió ja es va refusar una vegada.

Ha de portar sempre els quatre números que decideixen: els salts en EV entre
esglaons, les imatges usades contra el sostre de cua del cos, la integració
d'earthshine contra el mínim de 24 s de la porta de durades, i la distància del
canvi de base al bloc de contacte de C3. I tot **normalitzat a equivalent f/2,8
ISO 100**, pel mateix motiu del paràgraf anterior.
- `PROTOCOL_UNIVERSAL_ALTA_CAMERA_LLM.md`: procediment compacte per donar
  d’alta qualsevol cos amb un model agentic.

No esborris ni compactis `controller/runs`, `tests`, `runs`, `outputs`,
`certifications` o `stage_ab`: contenen evidència física i artefactes
immutables. Caches, venv antigues i apps històriques sí són regenerables.

`research/CLAUDE_PROMPT.md` és un prompt crític històric; no és una ordre viva
ni substitueix aquest document.

## 12. Handoff obligatori

Abans d’alliberar:

1. atura només els teus processos;
2. comprova que no queda cap PTP o captura pròpia;
3. anota fitxers tocats, proves exactes, resultats i límits pendents;
4. posa `status: RELEASED`, `serial_writes: RELEASED`, `owner: null` i
   `released_utc` al teu fitxer d’estat;
5. envia handoff explícit a l’altre agent si n’hi ha un d’actiu.

Si hi ha contradicció entre un document històric i la font viva, prevalen, en
aquest ordre: identitat/evidència física immutable, codi i perfils actuals,
QA V1.02, aquest document, i finalment recerca històrica. No omplis buits per
inferència: marca `DEMOSTRAT`, `FALTA` i l’ordre dels gates.
