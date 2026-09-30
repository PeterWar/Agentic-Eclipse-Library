# Handoff vigent — V31

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
