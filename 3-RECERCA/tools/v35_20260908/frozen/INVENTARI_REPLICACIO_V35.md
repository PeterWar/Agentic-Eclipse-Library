# Inventari de replicació de la V35 (SHA-256)

Generat per `frozen/inventari.py`. Un replicador comprova cada fila abans (A–D) i després (E–H) de cada etapa.

## A. runs de la cadena (immutables; MANIFEST amb el SHA de cada RAW)

| fitxer | bytes | SHA-256 |
|---|---:|---|
| `/Users/USUARI/Desktop/Eclipse determinista/1-RUNS/019_VIXEN_CIENCIA_20260827T212404Z/MANIFEST.json` | 96,198 | `b2da16489e7dece64436e2da6839f2963cd1576408aa3f351bacc4ecbbc91454` |
| `/Users/USUARI/Desktop/Eclipse determinista/1-RUNS/016_SONYTOT_CIENCIA_20260827T183356Z/MANIFEST.json` | 44,388 | `410fc161b6814d6eb5b58e9f5b419baaa8762661a2f26e14ed921c12bd968870` |
| `/Users/USUARI/Desktop/Eclipse determinista/1-RUNS/019_VIXEN_CIENCIA_20260827T212404Z/4-rebuts/F1.3_registre.json` | 21,500 | `5df60e194ce54416c9b053ae353604e008176091fc92f30452240f1ded192a4c` |
| `/Users/USUARI/Desktop/Eclipse determinista/1-RUNS/016_SONYTOT_CIENCIA_20260827T183356Z/4-rebuts/F1.3_registre.json` | 6,997 | `4daec86aedc9769a32fff05e286bbd1523ff4b2dadc88de9e49f5ffacdbed42b` |
| `/Users/USUARI/Desktop/Eclipse determinista/1-RUNS/019_VIXEN_CIENCIA_20260827T212404Z/4-rebuts/F2.2_coherencia.json` | 2,669 | `c5fbb57847d2b0534437b465b491c0814f8ebdc3c12f6a2685a29c197e3d1158` |
| `/Users/USUARI/Desktop/Eclipse determinista/1-RUNS/016_SONYTOT_CIENCIA_20260827T183356Z/4-rebuts/F2.2_coherencia.json` | 911 | `6ea4a44ce69f3f82ea5083a6fd539e31cc2a8b60d0b5a84ff71663d73e60024a` |

## B. geometria a la graella de Pere i paràmetres congelats (còpia a frozen/params)

| fitxer | bytes | SHA-256 |
|---|---:|---|
| `research/tools/v25_lineal/cau_v25/geometria_v27.json` | 1,632 | `469cbcd18088d0ab0a8cab76ecce4eeeb8c5789f4c3ae19fe6e98c6ecb37225d` |
| `research/tools/v29/cau_final/refined_detail_receipt.json` | 26,539 | `bc58ab00042a45faee388093fe25cf2e23ac2ada25137f6a493427e6506305fa` |
| `research/tools/v29/cau_final/coherent_resolution.json` | 612,072 | `609ffb482db656df2210a28434bee73c4780c54af125f5c4dc862b67c8a8e587` |
| `research/tools/v29/cau_final/pointing_merge_receipt.json` | 2,500 | `f5e219ce62cd4e28a4b53a6af45e659d4eac68d7b4f7d55905fc4eddd96856a2` |
| `research/tools/v30/cau/fine_variants_receipt.json` | 51,018 | `d2f7e2bf535a6d790dfdcbc71625e15bec2c3ac0091027b3fc7418c27c8b2eca` |
| `research/tools/v29_c03_fix/offset_model.json` | 406,756 | `7372bb5c46dd6d6a7359d195ec4d07ef95d20228d4c61e702989ba9ff08e728c` |
| `output/revisio_marques_v33_20260907/4-rebuts/R33_linealitat_sensor.json` | 3,924 | `7cc788ead7dc1e24768ab862bc264af16814afbb3d00e8aba80d79416f3f2302` |

## C. artefactes de la V29 a la graella final (suports, pesos, mapa de resolució)

| fitxer | bytes | SHA-256 |
|---|---:|---|
| `research/tools/v29/cau_final/vixen_support.npy` | 79,195,934 | `328c150b13049012d243f3468956e65d89e47fa4eb5712d8e3802b7dad976bb6` |
| `research/tools/v29/cau_final/sony_support.npy` | 79,195,934 | `81102f968e40de2b380abdb82736ad615f7b3a3b8791e0a96ead6dfeb12e3dc9` |
| `research/tools/v29/cau_final/fusion_support.npy` | 79,195,934 | `72f67465aa43a26931a96a016c5a72e67ecf0fa66599bdd3d97abd947cfd8e4a` |
| `research/tools/v29/cau_final/vixen_weight_G.npy` | 316,783,352 | `ff000cb80ce886249df4ce65a3ea111d0a0edf4e5aaf0604ec626a1e50f439fe` |
| `research/tools/v29/cau_final/sony_weight_G.npy` | 316,783,352 | `09db9f7aa8bb56dc4cc161b190d0c5c36f1e3f3f9ec9c66d7f3cb59198235533` |
| `research/tools/v29/cau_final/sony_A_weights.npy` | 950,349,800 | `b879987a569f3ddedfe6e387bac987ce08c8dfc8541b370c9f057d02773f1f2f` |
| `research/tools/v29/cau_final/sony_B_weights.npy` | 950,349,800 | `067bf8833e70e51cb6c930f4441ffcc64a2ec831c351dd26cf1d81020b8ec434` |
| `research/tools/v29/cau_final/sony_A_blend_weight.npy` | 316,783,352 | `278432697f273ac3bfdb3ec433c5d040a01e852b4d0cfc3fe5ddfb07d465ec22` |
| `research/tools/v29/cau_final/resolution_sigma.npy` | 316,783,352 | `b7a3c8ff2d54cea85276bfc079231d04ef0eade5c64cd6fc9e47e1311e47755f` |

## D. codi (cadena determinista, v29 common, v31_purs operadors, v32/v34/v35)

| fitxer | bytes | SHA-256 |
|---|---:|---|
| `research/tools/eclipse_determinista/cadena.py` | 19,588 | `51c835d18a453e15b9704760949fba94c7b0ce142583d0390e4a520b02b315d6` |
| `research/tools/eclipse_determinista/comu.py` | 49,983 | `241f44b41389389a3ea0ac6277523b660362489f8cbdc5d9984af36b098fa04e` |
| `research/tools/eclipse_determinista/f0.py` | 15,723 | `081c1063867000e8ce45028101cfc9db718920d9d0592b27d240c97e9d7dc16d` |
| `research/tools/eclipse_determinista/f1.py` | 17,534 | `470a760e906a8a227cae331e45e1fa92ad7a393c0a65b83f775fd41f66320029` |
| `research/tools/eclipse_determinista/f2.py` | 22,364 | `2bdb0f2e301785b733f77c11eb76479d4d93d566f280dfd97aa252489458924a` |
| `research/tools/eclipse_determinista/f3.py` | 32,882 | `546355979034547a06c6bf7a71c17010a06fc6f3920854429ccd6858e73b3609` |
| `research/tools/v29/common.py` | 3,137 | `1e3966401c811d9921c6af2bc07b6fb78bdb27d5dd6856e2d311d75600f6da6d` |
| `research/tools/v29/fuse_and_filter.py` | 8,428 | `6877fbaa19d69f33223ec53122e51ed71379ffa38c08e1604c5b2ea82ea376b3` |
| `research/tools/v29/audit_geometry.py` | 3,702 | `69aca09b9f50fa4a4e4e4b6290dfcf40e322b30c75ae60f2286970967cf824cd` |
| `research/tools/v29/qa_rasters.py` | 2,405 | `be0b8fbf6df06f1e0d0685e935ba52a41700cdc88c4fc21f41a9118dabd8e9b3` |
| `research/tools/v29/inspect_inputs.py` | 4,220 | `348b570b71e115d326a8912c063056e7463a27ebf902fc1df8d1ad3e4c6e24d9` |
| `research/tools/encaix_sony/psb_utils.py` | 5,869 | `f6464a170f48f1a5cebe2a6b3064337c1d95fdefe501af44ce351ed8b53cf037` |
| `research/tools/v31_purs/common.py` | 2,589 | `01c72adae8006fef22a752702456239dc309263539e9f2191b97cbf0556c5aa4` |
| `research/tools/v31_purs/wow_filters.py` | 3,731 | `41920085bbf75ebf9223f084a631564936cdcb1caaf6d77dab74c1185b2221b4` |
| `research/tools/v31_purs/local_filters.py` | 1,581 | `a3ab14320ab085c156636ada947eeb8ac0189fed3bbb358b153c056a2c7b6544` |
| `research/tools/v31_purs/radial_filters.py` | 1,995 | `bc666dfed3ae16aefd27ebc03542af8c3c8034c22a3c694de82ce986ef6a25b7` |
| `research/tools/v31_purs/sparse_conv.cpp` | 1,101 | `ddfb17f496df182dba3b4fb7a4f09f1b50466dafd060fb33598db0bfc8161579` |
| `research/tools/v31_purs/sparse_conv.dylib` | 36,880 | `8ed49f17f5e5580acbc11d7373bd04ec04c2d6cc888a0d4f9d7152c7a5011d49` |
| `research/tools/v32_arcs_20260907/comu32.py` | 5,104 | `fe50ad4d4329dee3c5734ae4acd65d2970c9cc6c7064f79ed29d309f47364a32` |
| `research/tools/v34_20260907/comu34.py` | 3,878 | `5ffbb518e74da2fa99044077bc00a23a35b0e048c3fa0f4052f51fd69c0492e3` |
| `research/tools/v34_20260907/a1_pesos_per_fotograma.py` | 4,911 | `ae1d493e494ee44ff83aec2532d32904b9b5548cff42712f1660a10b6cfb1b44` |
| `research/tools/v34_20260907/b1_camps_per_fotograma.py` | 7,045 | `be9abc3771199229a58ac00c478d1aef7bb82669977efc7767551866ee422a60` |
| `research/tools/v34_20260907/b2_recomposicio.py` | 6,194 | `8d7f681a70aa98e47f0a29ca5c4173e54b1e46c9324b9a7b3be32bc8f2a8eac4` |
| `research/tools/v35_20260908/comu35.py` | 3,136 | `78beac783217e302134e832160f3b70e181506b042898413aabc2168d556ac4b` |
| `research/tools/v35_20260908/b3_fusio.py` | 14,838 | `f5ea144ac3980ba6a7ad8b44c9dfb373ce5b1996ce33492ac61aa842472e32ee` |
| `research/tools/v35_20260908/b4a_capes_cadena.py` | 5,282 | `e8ce6fc8341b79f7a0d6830aff16d2ba13c3b18ab477723082ee0e5eb4ff8f91` |
| `research/tools/v35_20260908/b4c_purs.py` | 7,265 | `6599ba58a09d7c05cf44f4de63e8e0fe7b487b4621313c4a8b54da1888a1d256` |
| `research/tools/v35_20260908/b4d_radial_vora.py` | 4,606 | `57bddeed32f61da654ed1d7f537142c633e02283fdfd110f5d5f9767e8751e43` |
| `research/tools/v35_20260908/c4_psb.py` | 10,132 | `9d9aefb493a33aac4680c3b155623760d9bdab612f52272e94ea6077681be9e6` |
| `research/tools/capes_totals_v14/porta_photoshop.sh` | 1,221 | `90cb498f1d9b1fc899b6c20d7fc3a847efa537779791e431ba0d5c19e50d16b1` |

## E. composició per grup (V34 a1/b1/b2)

| fitxer | bytes | SHA-256 |
|---|---:|---|
| `research/tools/v34_20260907/cau/vixen_total_v34.npy` | 950,349,800 | `fdf00ba50c5a3f7879bc702afd52ba7d30bef01cab5251e10f97226192c4b2a1` |
| `research/tools/v34_20260907/cau/sony_A_total_v34.npy` | 950,349,800 | `1dc07a695be5393d12faa26ee2bab1a009027f2dac5b484ede949a405fecd763` |
| `research/tools/v34_20260907/cau/sony_B_total_v34.npy` | 950,349,800 | `87eaf8f4f9460fb6a9940c239d543f836f4a0b4fa3dac439f9ad11a1ad18e56b` |
| `research/tools/v34_20260907/cau/vixen_meta.json` | 34,099 | `1ff5fed5a363f4ef5e257ae448e26eae7d8b5f369ae918e8acc93097ffaec14f` |
| `research/tools/v34_20260907/cau/sony_meta.json` | 11,685 | `7a1c6d13fb00bca02cfa909e9776d70af15966af1de61ceae7f1ac135f3251de` |

## F. fusió i capes V35

| fitxer | bytes | SHA-256 |
|---|---:|---|
| `research/tools/v35_20260908/cau/sony_corrected_total_v35.npy` | 950,349,800 | `96f441030ddb3d030d6638363b724600cfdac933becefcc7328e38814ab3816d` |
| `research/tools/v35_20260908/cau/fusion_total_v35.npy` | 950,349,800 | `9d1818feffed4ff571ba3f0ce61060135872ca27966cb459ec87ad9d174b7d47` |
| `research/tools/v35_20260908/cau/base_G_v35.npy` | 316,783,352 | `12c313caee7c5bd3b9c99e479cd40b4f2b8f270b65c44b260825b616ed01019f` |
| `research/tools/v35_20260908/cau/support_v35.npy` | 79,195,934 | `72f67465aa43a26931a96a016c5a72e67ecf0fa66599bdd3d97abd947cfd8e4a` |
| `research/tools/v35_20260908/cau/weight_vixen_v35.npy` | 316,783,352 | `36fd13578869632b9827735c1f949dfda0bf914f65012b6a6cbdbd140e0d9b80` |
| `research/tools/v35_20260908/cau/rho_v35.npy` | 950,349,800 | `3af624b424c0fdb739ac1286427be29f5c2085414037f18c7d064659dc1b9d91` |
| `research/tools/v35_20260908/cau/delta_v35.npy` | 950,349,800 | `332efb7b62303ff239c580c76bef5eb19a71cd6c05652d18c3ae20aa0be70855` |
| `research/tools/v35_20260908/cau/01_v35_u16.npy` | 158,391,740 | `0aa7263e3e143ccedeb91a4250643749d5cedf02532e2d04c197c2cf0a22ecf0` |
| `research/tools/v35_20260908/cau/02_v35_u16.npy` | 158,391,740 | `e4471e978e411b79093ae8809aa1eb5c932986a0d4626f2ccb87abcc52b45b53` |
| `research/tools/v35_20260908/cau/04_v35_u16.npy` | 158,391,740 | `77a8303e863350ea8c886c3d8968140c7c556deb4556d5af793ffb550ec757ef` |
| `research/tools/v35_20260908/cau/05_v35_u16.npy` | 158,391,740 | `2196e55d09f7df33fb44bac3a7f7bd0e5320cbd4f50063d0a0635a493d5c4d4f` |
| `research/tools/v35_20260908/cau/06_v35_u16.npy` | 158,391,740 | `b4df7e1e7fd9c958ba85780ba32c8d65a065c846c137555912fa833b60ae442c` |
| `research/tools/v35_20260908/purs/cau/P01_NRGF_u16.npy` | 158,391,740 | `8d7b9ad98aaebed72800791f939100a089a6acf85bf296e9ec0052e306691b17` |
| `research/tools/v35_20260908/purs/cau/P02_RHEF_u16.npy` | 158,391,740 | `5aa4c0a5b34eefed612702fcc12fcab5a7a9232126b5fdd7839a5ea139c4c22e` |
| `research/tools/v35_20260908/purs/cau/P03_MGN_u16.npy` | 158,391,740 | `100dd3b227422204f85bde22be8a3420329ea0571982c72ec2e634924eb13a37` |
| `research/tools/v35_20260908/purs/cau/P04_WOW_u16.npy` | 158,391,740 | `ecf75f532f9f15acb90833b7ee7e728f95a97008ef4f8322a79eb491a0154110` |
| `research/tools/v35_20260908/purs/cau/P05_WOW_bilateral_u16.npy` | 158,391,740 | `0eb6660ec24cbe7d5518276af4207a32f186505efe2b8ca820e3461f0db68a80` |

## G. modes i màscares de les capes (de V32.psb, congelats)

| fitxer | bytes | SHA-256 |
|---|---:|---|
| `research/tools/v35_20260908/frozen/modes_mascares_v32.npz` | 6,378,487 | `0833bba78ee0b6f3ebf9269aadbfec032c5eafabf53a106164a19100d1fc808f` |
| `research/tools/v35_20260908/frozen/modes_mascares_v32.json` | 5,992 | `6f83580e7992e1f7e3221dc65f7a41599aadac6569029d0a78433d02d620c9d6` |

## H. producte

| fitxer | bytes | SHA-256 |
|---|---:|---|
| `/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V35.psb` | 4,481,840,046 | `50c8e1cfb7144794db67c227324238fb33b9ccaf91502ff33fb6f954692aa6d4` |
| `/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V35_REBUT.md` | 8,405 | `392d4a6e66175fcaacba2313f1de30d26728075aca32ec153793a0dd15851661` |

