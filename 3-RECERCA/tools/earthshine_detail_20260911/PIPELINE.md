# Represa reproduïble — V48

Arrel de codi: `/Users/USUARI/Downloads/Eclipse 2026`. Escriptor únic amb `SERIAL_WRITES`; llegir autoritats vives. No tornar a executar directament sobre les sortides publicades: els muntadors exigeixen destins inexistents. Per reproducció, preparar un destí nou i registrar els canvis de ruta. No obrir ni desar els documents originals 79/140 com a candidats.

Python: `/Users/USUARI/.venvs/eines-ia-py312/bin/python`, `PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1`.

## Cadena executada

1. `b0_all_native.py --check-six`, després `b0_all_native.py`: calibració i remapat de 88 RAW a CFA verd ordinari. Font de l'inventari: `output/v45_earthshine_20260910/4-rebuts/B1_inputs.json`. El camp antic `path` d'aquest inventari apunta a un NPY, no al RAW. La ruta i SHA reals són als nous rebuts `native/{tren}_{stem}.json`.
2. `b1_full_native_ensemble.py`: font Vixen 67 amb compositor fix C0 de V47. `b2_sony_reference.py`: les 21 Sony separades i la mateixa preferència temporal/ghost preexistent. G1/G2 són controls condicionals, no càmeres independents.
3. `b3_native_change.py`, `b4_full_source_judge.py`, `b5_full_native_limb.py`: diferències, jutge entre trens amb cobertura per referència i contorn en 24 sectors. Noms antics `V45`/`C5` de B5 equivalen a font V47 antiga/font V48 nova.
4. `c0_display.py`: estructura ampla fotogràfica heretada + detall fi Vixen renovat, transició DCT 8–16 px sobre tot el rectangle. `c1_camera_raw.py`: recepta coneguda nativa en el PSD complet. `c2_calibrate.py`: corbes globals congelades de `output/earthshine_validation_20260911/B1_global_tone_diagnostic.json`. `c3_neutral_chroma.py`: mateix delta enter als tres canals, sense clipping.
5. `c4_package.py`: nou PSB amb les 24 capes originals exactes +1. No copiar `LAYER_ID` ni `METADATA_SETTING` a la nova capa: una identitat duplicada havia impedit recompondre candidats antics. Màscara i alfa originals exactes.
6. `c5_verify_gate.py C4`: fingerprint, segon lector, porta Photoshop i exportació TIFF amb comparació real. `c6_retention.py`: retenció fotogràfica; no és el jutge independent. `c7_protection.py`: alfa, rectangle exterior, regió càlida i màscara zero. `c8_publish.py`: còpia exclusiva i SHA, obrir només V48.
7. `z0_preservation.py`: 88 SHA RAW, V46/V47, XMP i documents. `z1_handoff.py`: inventari, autoritats i release.

`C6_retention_changes.json` té claus `gain` i `loss` (singular). Les taules resum B4/C6 es van extraure dels rebuts detallats, sense tornar a optimitzar el candidat.

## Dependències heretades

Sortides noves: `output/earthshine_detail_20260911/`. Anterior: `output/earthshine_validation_20260911/`. Calibració, rendiment del sensor i Sony LUT: mòduls `comu45`, `comu36` i cadena històrica; no substituir el `ctx.plans` ajustat per una lectura Sony sense linealitzar.

Original viu congelat: `output/earthshine_reconstruction_20260911/V46_Detall_live_source.psd`, SHA `a871047937872e0a426b4c61dad524ab43fcb16141a9328f42f99142632a5b57`. Font pre-Camera Raw: `research/tools/v46_earthshine_20260911/V45_live_source.psd`, seleccionar la capa pel nom `V45 font G · dos trens · preferència temporal · vel present`, mai per índex entre arxius. RGB prefiltre: `research/tools/v46_earthshine_20260911/cau/live_lunar_rgb_u16.npy`.

Llenç 10551×7506; rectangle lunar (4677,3077) de 1400×1400. Centre local (699,568111973117; 699,6475341408573). FOV, màscara i àncora temporal lunar heretats. No introduir LROC/DHS al reconstructor; LROC només al jutge. Les capes originals de Pere poden contenir LROC i Sony i continuen intactes.

## Assaigs no promoguts i trampes

- `b7_joint88.py`, `b8_joint88_limb.py`: barreja directa de totes les 88 fonts; pitjor en diversos sectors. No entra a V48.
- `b6_motion_estimate.py`: trajectòria nominal separada per apuntament. `B6_REJECTED_cross_pointing.json` barrejava el repuntat Sony A/B i produïa un moviment fals; no usar-lo.
- `native/rejected_float32_variance/`: primer candidat d'optimització amb fraccions float32 alterava variàncies. La versió final resta índexs enters i equival a les sis fonts de control.
- `a0_final_V47_judge.py`, `a1_rotation_controls.py`: auditen retenció i sensibilitat dels controls. No són prova independent perquè la foto hereta estructura Sony. B4 separa les captures.
- Retenir el registre V45 per textura. Els desplaçaments ajustats a la vora aparent, el mosaic FFT64/pas8 i l'ajust PSF uniforme anterior són rebutjats. Cap resta nova de vel promoguda.

Abast honest: producte fotogràfic verificat, millora parcial del contorn; cap PASS de recuperació completa ni injecció integral RAW. Vegeu `output/earthshine_detail_20260911/RESULTAT.md` abans de continuar.
