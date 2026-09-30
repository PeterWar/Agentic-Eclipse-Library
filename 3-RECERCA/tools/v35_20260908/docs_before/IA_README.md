# 07-09-2026 (nit) — V34 lliurada, curada a l'origen

`/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V34.psb` (lleugera: base lineal V34 + 10 filtres amb la recepta V32, cap suavitzat; OBRE 10551 px x 7506 px · 11 capes; SHA-256 `fa49221cad3352c4e4e7840018ee305e7ec360b3aad4e28c6c175ea3f0d50917`). Entrada gradual dels fotogrames, Sony linealitzada amb la corba mesurada, fusió per variància (A+B i Vixen afegida de 2,65 enfora): gra de la base −30…−44 % de 2,5 a 6 R☉. Rebut: `V34_REBUT.md`. Vistes V32|V34 (retalls a les teves marques de la V32 i la V33, polars, gra per radi): `/Users/USUARI/Desktop/Eclipse 2026/IA/output/v34_20260907/lliurables/vistes/`. Causa de les marques de la V33: `research/149`.

---

# 07-09-2026 (nit) — V33 retirada

Els artefactes marcats a `V33_Artefactes.psb` els va fabricar el suavitzat de la V33 (research/149; vistes `IA/output/revisio_marques_v33_20260907/`). Producte vigent: `V32.psb`. Norma nova de Pere: cap correcció estètica sense causa a l'origen, cap sacrifici de detall. Ve una V34 a l'origen.

---

# Actualització 07-09-2026 (vespre) — V33 lliurada

`/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V33.psb` (lleugera: base lineal + 10 filtres; OBRE 10551 px x 7506 px · 11 capes; SHA-256 `79424a49c459953ce02b8ae26d9c0400bdb524861eaa0a38c31b617d9f6b33f3`). Resolució que segueix el S/N (gra fi 10–100× més baix de 4 R☉ enfora) i NRGF/RHEF sense el cercle de la vora del llenç. Rebut: `V33_REBUT.md` al costat. Vistes V32|V33: `/Users/USUARI/Desktop/Eclipse 2026/IA/output/v33_20260907/lliurables/vistes/` (polars per capa i tram, retalls a les marques). Traspàs: `.coordination/HANDOFF_2026-09-07_V33.md`.

---

# Actualització 07-09-2026 (tarda) — revisió del PSB anotat de la V32

Pere ha pintat `V32_Filtres_Artefactes.psb` (78 components en 10 de 22 capes). Revisió mesurada a la font, en polar i amb control nul: **les marques interiors (1,15–2,3 R☉) són corona** (correlació Vixen×Sony al traç +0,68, nul −0,03); el que queda és dels filtres: cercles de NRGF/RHEF a la vora del llenç (8,47/8,57/11,78/12,17 R☉), vora streamers→gra a 3,6–4,7 (05/06), graons de gra a les entrades dels fotogrames (04/MGN/WOW), zona taronja de la RHEF = gradient del cel; taca NE = clot de 2σ només a la Sony B. Cap PSB modificat.

Revisió capa a capa i vistes: `/Users/USUARI/Desktop/Eclipse 2026/IA/output/revisio_marques_v32_20260907/lliurables/RESULTAT.md` (comença per `00_totes_les_capes_anotades.png`, `00_mapa_marques_sobre_base.png` i els retalls polars `R32_A6_zoom_*.png`). Informe: `/Users/USUARI/Downloads/Eclipse 2026/research/147_REVISIO_MARQUES_V32_20260907.md`. Traspàs: `.coordination/HANDOFF_2026-09-07_MARQUES_V32.md`. Pla de V33 (només filtres) al traspàs.

---

# Actualització vigent 07-09-2026 — V32

V32 és el lliurable editable actual: `/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V32.psb`.
10551 × 7506, RGB16, 40 capes; 9,574,799,408 bytes.
SHA-256 `dcfc8f531e286bfdf529d20880c9772785a38a4e6d0c09094883a7c8f7743c7d`.

Les 18 capes de filtre (03 V29, 03 V30, 07, 01, 02, 04, 05, 06 i les deu vistes pures P01–P09/C01) s'han regenerat amb les receptes
exactes de la V29/V30/V31 sobre una base curada A L'ORIGEN: camps de nivell suaus per fotograma i canal (fronteres de fusió HDR),
perfil radial del flat de la Sony suavitzat (la seva ondulació fina, impresa invertida a cada fotograma, era la causa dels arcs
de 3,2–4,6 R☉), guany 2D suau entre trens i ploma a la vora del suport Sony. Cap retall circular, cap màscara de marques, cap
inpainting. Les altres 22 capes (bases, capes de Pere, estrelles, reflex) són byte a byte les de V31_FiltresPurs, que es conserva.

Photoshop real: **OBRE 10551 px x 7506 px · 40 capes**. Mesures abans/després (anisotropia tangencial, graons a les fronteres, residu creuat entre trens,
jutge extern fix, injecció cega, H1/geometria de cada capa) al rebut `V32_REBUT.md` al costat del PSB. El judici visual de Pere queda obert.

Traspàs: `/Users/USUARI/Downloads/Eclipse 2026/.coordination/HANDOFF_2026-09-07_V32.md`. Explicació: `research/146_V32_ARCS_A_LA_FONT_20260907.md`. Codi i rebuts: `research/tools/v32_arcs_20260907/`,
`output/v32_arcs_20260907/`. Vistes: `/Users/USUARI/Desktop/Eclipse 2026/IA/output/v32_arcs_20260907`.

Les referències a la V31_FiltresPurs més avall són històriques (producte preservat).

---

# Actualització vigent 06-09-2026 — V31 comparativa

V31 comparativa de filtres independents és el lliurable actual: `/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V31_FiltresPurs.psb`.
10551 × 7506, RGB16, 40 capes; 9,593,292,748 bytes.
SHA-256 `89d509bcc53982307cf9e3d78b0a84ed7548f4045e8cbb95d9f8594e4e877dfd`.

Les 30 capes anteriors i el compost inicial són exactes; s'afegeixen 10 vistes Normal100%, apagades. Base comuna G corregida i match global Sony→Vixen0,3411462604999542. NRGF, RHEF, MGN, WOW/bilateral, NAFE, precursor ACHF16/32, SWAP pilot i control passa-alt. Cap H1/tanh/suavitzat extern ni retall circular als mètodes nous; operacions intrínseques i discretització documentades.

És una comparació amb limitacions visibles, no una correcció certificada de tots els arcs. RHEF pot crear bandes; hi ha arcs de la base, soroll exterior i resposta forta d'ACHF al limbe. FNRGF queda com a array de domini vàlid; no s'inventen sectors. Inventari i exclusions justificats a `/Users/USUARI/Downloads/Eclipse 2026/research/142_V31_FILTRES_PURS_20260906.md`.

Photoshop real: OBRE 10551 px x 7506 px · 40 capes. Les 30 capes originals i tots els nous RGB/màscares verificats. Els documents V31.psb/V30.psb estaven oberts amb canvis sense desar i no s'han substituït. Backup de disc: `/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V31_abans_filtres_purs_20260906.psb`.

Handoff: `/Users/USUARI/Downloads/Eclipse 2026/.coordination/HANDOFF_2026-09-06_V31_FILTRES_PURS.md`. Manifest: `/Users/USUARI/Downloads/Eclipse 2026/research/tools/v31_purs/delivery_manifest.json`. Guia i vistes: `/Users/USUARI/Desktop/Eclipse 2026/IA/output/v31_purs_20260906`. No hi ha tasca automàtica nova; l'avaluació visual de Pere resta oberta.

Les referències a la V31 del05-09 més avall són històriques. Les normes generals i rutes de RAW continuen vigents.

---

# IA — punt d’entrada viu — V31

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

Llegir README, ESTAT_ACTUAL i MAPA_RUTES_I_OUTPUTS en aquest ordre; després ACTIVE.json i el handoff. AGENTS/CLAUDE i el lock de Downloads manen les normes. Snapshots V30 a `/Users/USUARI/Downloads/Eclipse 2026/research/tools/v31/docs_before/IA`.
