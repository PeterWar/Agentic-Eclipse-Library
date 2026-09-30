# Estat actual — V31 comparativa

V31 comparativa de filtres independents és el lliurable actual: `/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V31_FiltresPurs.psb`.
10551 × 7506, RGB16, 40 capes; 9,593,292,748 bytes.
SHA-256 `89d509bcc53982307cf9e3d78b0a84ed7548f4045e8cbb95d9f8594e4e877dfd`.

Les 30 capes anteriors i el compost inicial són exactes; s'afegeixen 10 vistes Normal100%, apagades. Base comuna G corregida i match global Sony→Vixen0,3411462604999542. NRGF, RHEF, MGN, WOW/bilateral, NAFE, precursor ACHF16/32, SWAP pilot i control passa-alt. Cap H1/tanh/suavitzat extern ni retall circular als mètodes nous; operacions intrínseques i discretització documentades.

És una comparació amb limitacions visibles, no una correcció certificada de tots els arcs. RHEF pot crear bandes; hi ha arcs de la base, soroll exterior i resposta forta d'ACHF al limbe. FNRGF queda com a array de domini vàlid; no s'inventen sectors. Inventari i exclusions justificats a `/Users/USUARI/Downloads/Eclipse 2026/research/142_V31_FILTRES_PURS_20260906.md`.

Photoshop real: OBRE 10551 px x 7506 px · 40 capes. Les 30 capes originals i tots els nous RGB/màscares verificats. Els documents V31.psb/V30.psb estaven oberts amb canvis sense desar i no s'han substituït. Backup de disc: `/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V31_abans_filtres_purs_20260906.psb`.

Handoff: `/Users/USUARI/Downloads/Eclipse 2026/.coordination/HANDOFF_2026-09-06_V31_FILTRES_PURS.md`. Manifest: `/Users/USUARI/Downloads/Eclipse 2026/research/tools/v31_purs/delivery_manifest.json`. Guia i vistes: `/Users/USUARI/Desktop/Eclipse 2026/IA/output/v31_purs_20260906`. No hi ha tasca automàtica nova; l'avaluació visual de Pere resta oberta.

## Històric 05-09-2026

# Estat actual — V31

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

La petició de suavitzar els no azimutals està executada; no hi ha nova missió ni tasca automàtica. Els experiments sigma5 i04sigma3 no són lliurables.
