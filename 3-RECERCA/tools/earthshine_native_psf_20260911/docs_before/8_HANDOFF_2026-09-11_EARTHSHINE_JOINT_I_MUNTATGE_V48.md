# Handoff — V48 preservada; model per captura i muntatge — 2026-09-11T18:44:42.120967+00:00

**Producte vigent:** `/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors/Earthshine_V48.psb`, SHA `48715be427ebd5ea654eeea746e0a295201f9f0a354e4f5e37fbf40df47443a5`. Cap V49 publicada. L’objectiu de recuperar el llimb continua actiu. Pere ha aclarit que les visibilitats modificades del document1297 eren només una inspecció; la V48 desada continua sent la referència estètica. La instantània viva d’aquesta ronda és arxivística, no una nova preferència.

Informe `/Users/USUARI/Downloads/Eclipse 2026/output/earthshine_joint_20260911/RESULTAT.md`. Represa acotada `/Users/USUARI/Downloads/Eclipse 2026/research/tools/earthshine_joint_20260911/REPRESA.md`. Manifest `/Users/USUARI/Downloads/Eclipse 2026/research/tools/earthshine_joint_20260911/delivery_manifest.json`. Arrel de codi Downloads; arrel d’actius Desktop. Sense Git, maquinari ni agents nous.

## Resultats i límits

- Model implementat de Lluna comuna i Sol mòbil: primer dues èpoques, després8 captures d’ajust i4 de predicció del nou model. La calibració anterior utilitzava les captures: no és holdout complet de RAW.
- A2 corregeix la integració4×4 de l’ocultació amb àrea píxel/polígon convergent. A4 detecta eixamplament del mesurador de perfils i calibra sigma de graella1,4275159 amb un fantoma. Cap d’aquestes proves identifica la PSF física real de totes les captures.
- B6, últim model: convergeix, però deixa1.119 valors negatius,543 en píxels íntegrament lunars, i prediccions irregulars. No es promou. B5 no és estimació conjunta d’ales òptiques, només una prova amb escenes congelades.
- **Rectificació conceptual:** la màscara heretada a V48 és l’encaix fotogràfic V44 ajustat a la resposta tonal de Pere09, amb validesa de font. No és només una màscara d’ocultació física. C1 la relaciona amb `join_coverage.npy` a1 DN16; radi d’àrea455,935 versus453,544 de la silueta òptica.
- C0/C1: quatre exports natius sobre còpia pròpia separen la font lunar alternativa i LROC visibles sota la font V48. Reforcen part de la franja; retirar-les no resol el vel i altera lleugerament la barreja interior. RGB de la font, CameraRaw i màscares originals intactes. Baseline native vsV48 esperada màxim3 DN16; recomposició d’una sola font màxim1 DN16.
- C2: aplicar suport geomètric al conjunt lunar deixa r<435 exacte, però crea un **anell negre**. Rebutjat, no convertir-lo en una màscara nova o una resta manual.

## Continuació autoritzada

Qualificar la resposta per captura al CFA natiu, separant el seu mostreig del que afegeixen el remapat i la mesura polar. Començar amb una època i la partició declarada a REPRESA. No ampliar la inversió a totes les preses llargues sense qualificar aquest operador; no inferir vores de l’última mostra no saturada. No tornar a la translació global de la vora que perjudicava textura, ni a una força de deconvolució escollida pel resultat visual.

Preservació: fonts93 exactes aZ0; V46/V47/V48 i tres XMP rehash després dels exports aZ1. Documents79/140/1297 continuen saved=false,1275 saved=true. `C0_V48_disk_test.psb` és còpia exacta de V48 i no conté les variants: es van exportar a TIFF des d’un document propi tancat sense desar. No hi ha procés de càlcul ni document propi obert al release. Cap porta Photoshop de producte nou invocada, perquè no s’ha produït cap candidat nou.
