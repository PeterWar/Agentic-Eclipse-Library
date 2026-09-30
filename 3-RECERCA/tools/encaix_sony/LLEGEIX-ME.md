# Encaix de la capa Sony 300 mm al compost Vixen de Photoshop (18-08-2026)

Codi de la sessió que va treure l'anell de colors del document `NoEncaixa.tif` de Pere
(vegeu `research/80`). Tot va sobre `~/.venvs/eines-ia-py312` i escriu al scratchpad de
la sessió (rutes relatives); els lliurables van a `~/Downloads/Encaixada_2026-08-18/`.

| Script | Què fa |
|---|---|
| `parse_layers.py TIFF` | llegeix l'estructura de capes de Photoshop del tag 37724 d'un TIFF `II` (little-endian, longituds de 8 bytes; **les dades de canal són big-endian**) → `layers_index.json` |
| `extract_layers.py` | bolca cada canal de cada capa a `.npy` (uint16) |
| `crop_and_verify.py` | retalla la capa Sony al llenç i comprova que `vixen·(1−màscara) + sony·màscara` reprodueix l'aplanat (3·10⁻⁵) |
| `diag_seam.py` | perfils radials i de color per canal de les dues capes, la màscara i el compost |
| `arregla_estrelles.py in out` | traces curtes → gaussiana rodona del mateix flux i centroide (ajust el·líptic + criteris de direcció/mida/S/N) |
| `encaixa_sony.py in out [σ] [vora]` | LUT per canal (quantils) + residu de baixa freqüència per convolució normalitzada; Vixen dins la zona cremada (versió del llenç sol) |
| `realca_i_lliura.py [SUAU\|FORT]` | detall exterior en bandes angulars sobre el llenç sol (versió anterior a `pipeline_ext.py`; té el problema de les vores) |
| `pipeline_ext.py` | **la versió bona**: tot el pipeline sobre el domini estès (llenç + marges 550/250/600/300), dues variants de residu (segueix la Vixen / vores netes), detall SUAU i FORT amb component d'anell zero, i tots els TIFF |

Ordre: `parse_layers` → `extract_layers` → `crop_and_verify` → (extreure el domini estès i
`arregla_estrelles` sobre ell) → `pipeline_ext`.

## Segona ronda (mateixa nit)

| Script | Què fa |
|---|---|
| `halo_fix.py` | prova de treure l'«espatlla» de luminància per pendent isotònic log-log: efecte < 0,5 % (el perfil ja era llis); queda com a evidència |
| `halo_variants.py` | el tractament bo del halo: croma × CM i luminància × G amb rampa 2,6→4,5 R☉ (A 0,35/0,95, B 0,20/0,90, C 0,50/1,00) |
| `apila_sony.py` | apilat lineal (ADU/s) dels 7 Sony ≥ 1 s a la reixa de DSC06993: offsets6 + similitud A→C de `astrometria/sony`, plans de Bayer per convolució normalitzada, saturació emmascarada, **cel anivellat per fotograma** (anell 4,5–6 R☉, referència 06993) |
| `sony_stack_al_llenc.py` | primera col·locació al llenç per correlació de la corona (dona el signe del gir); la similitud definitiva surt de 7 estrelles comunes (escala 1,48860, gir 33,088°, rms 0,52 px; el codi és a `research/80` §7) |
| `pipeline_stack.py` | `pipeline_ext.py` amb l'apilat com a entrada (validesa = cobertura i r > 3,0; LUT des de 3,05 R☉; estrelles rodones detectades per compacitat; capa anterior anivellada als cantons sense apilat) → `APILAT_*` |

## Tercera ronda (matí del 18)

- `apila_sony.py` (v3): anivellament per fotograma contra 06993 amb pla + residu suavitzat (σ 300 px, a 1/8 per blocs), a = 1 fixat; només píxels del tot dins del vàlid.
- `pipeline_stack.py` (v3): corredor del raig recte (θ 129,6°, ±60 px ploma 40, 2,8–6 R☉) amb la Vixen suavitzada; reserva anivellada als cantons i al tros sense apilat.
- `pipeline_tangencial.py`: detall només azimutal en polars (0,6–2°, 2–6°, 6–16°; SUAU/MITJA/FORT) + EXTENSIO radial (k 1→1,4 sobre base − camp llunyà) → `APILAT_*TANGENCIAL*`, `*EXTENSIO*`.

## Quarta ronda (tarda del 18): les ombres dels cantons — flat, referència i D fins a les vores

| Script | Què fa |
|---|---|
| `diag_ombres.py`, `diag_ombres2.py` | el diagnòstic: camp llunyà estirat, quocients capa/Vixen a baixa freqüència, perfils a les vores; hi surt que la capa Vixen de Pere s'enfosqueix a dalt (×0,58) i a la dreta (×0,51) i que la Sony s'enfosqueix als cantons |
| `flat_sony300.py` | **el flat del FE 300 mm f/2,8 GM a f/2,8** dels flats de cel de l'A7III (06-04-2025, jocs 3200 i 6400): black restat, mitjana, plans de Bayer, simetrització 180° (el gradient del cel és senar), σ 25 px, i reescalat a la reixa de l'A7RIIIA (pitch 5,94 → 4,51 µm). Vinyeta 0,70 a 10 mm, 0,54 a 15 mm, 0,34 al cantó (−1,5 EV); simètric a ±0,3 %. Perfil radial a `flat_sony300_f28_perfil_radial.csv` |
| `flat_al_llenc.py` | comprova la similitud (reprodueix `sony_stack_ext_rgb.npy` exactament) i porta el flat al domini estès; escriu l'apilat aplanat `sony_stack_ext_rgb_FLAT.npy` |
| `test_flat_vs_vixen.py` | **la prova**: apilat aplanat contra l'apilat lineal de 10,3 s de la Vixen (HDR4): quocient 0,99–1,01 de 4 a 8,8 R☉ (sense flat: 1,03 → 0,77) |
| `diag_capa_vixen_pere.py` | LUT per canal Vixen lineal → capa de Pere: la capa és una corba de to global a ±1 % excepte les rampes de ~700 px de dalt i de la dreta; desa `vix_ref_rgb.npy` (la capa sense l'enfosquiment) |
| `pipeline_stack_v4.py` | `pipeline_stack.py` amb l'apilat aplanat, la referència mixta (capa de Pere / vix_ref amb rampes de 200 px), D estimat fins a les vores (VORA = 0), corredor i tros sense apilat amb la mateixa referència; detall SUAU/FORT (DoG) → `APILAT_*` v4 |
| `cel_pla.py` | variant cosmètica `_CELPLA`: luminància del camp llunyà (r > 5,6, σ 250) al nivell de 5,6–6,2 R☉, rampa 4,8–6,2, un factor per als tres canals |
| `compara_ombres_v4.py` | abans/després per a Pere (v1 marcada contra v4) |
| `pipeline_tangencial.py` (v4) | igual, però ja no reescriu la base |

## Afegit de la quarta ronda: la ratlla tangencial de la fusió HDR (Vixen)

| Script | Què fa |
|---|---|
| `diag_artefacte_tangencial.py` | marc girat sobre la línia de Pere: perfils perpendiculars de la capa de Pere, la meva i els apilats lineals de l'HDR4 amb la seva saturació → el contorn de saturació del 10,3 s cau a 37 px de la línia i la capa hi té +0,7 % |
| `corregeix_grao_hdr.py` | primer intent global (perfil per valor del 10,3 s / distància, a tot el contorn): massa barrejat amb l'estructura real; només evidència |
| `corregeix_grao_local.py`, `corregeix_grao_local_v.py` | primera passada al sector θ −160…−78° (per distància / per valor del 10,3 s); `K_grao_local.npy` |
| `corregeix_grao_local2.py` | segona passada: perfil coherent a y fix al marc girat; `K_grao_total.npy`; amb `APPLY=1` multiplica tots els TIFF d'`APILAT/` (no PASSALT) |

## UnintCapes4.psb: el projecte de Photoshop amb els retocs com a capes imatge + màscara

| Script | Què fa |
|---|---|
| `psb_utils.py` | escriure PSB de 16 bits amb psd-tools 1.18: `new_psb` (versió 2, ICC i recursos copiats), `add_pixel_layer` (RGB uint16 + màscara uint8, ZIP amb predicció, nom Unicode), `finalize_lr16` (les capes al bloc `Lr16` i la secció clàssica buida, com fa Photoshop als documents de 16 bits; ⚠️ `TaggedBlocks.set_data` vol els arguments del constructor, no una instància), `add_mask16` (⚠️ les màscares van a la profunditat del document: `Layer.create_mask` de psd-tools les escriu a 8 bits i als documents de 16 bits surten amb mitja fila), `set_merged` |
| `v4_intermedis.py` | `pipeline_stack_v4.py` retallat: regenera `g − D`, `w`, `fbk`, `valid_px`, `vref` sense reescriure cap TIFF |
| `construeix_unintcapes4.py` | el document: les tres capes de Pere d'UnintCapes3 (1 s rasteritzada, 2 s i 10,3 s reutilitzades byte a byte amb màscara i opacitat, desplaçades +457/+463), la Vixen de referència, la Sony aplanada i encaixada + màscara = w, i tres capes Linear Light (graó HDR + màscara del sector, detall tangencial MITJA, extensió radial) més el cel pla oculta; fusionada = el TIFF ESTESA v4b |
| `verifica_unint4.py` | rellegeix el PSB i compon sis retalls amb les dades rellegides (Normal i Linear Light) contra el TIFF |

## Els dos projectes de Photoshop de Pere (CapesInteriors / CapesExteriors), mateix llenç

| Script | Què fa |
|---|---|
| `alineacio_projectes.py`, `alineacio_interiors.py` | mesura d'alineació entre capes (dins de cada projecte i entre projectes) per correlació de fase del passa-alt sobre anells de retalls al voltant del Sol; ⚠️ el signe: `shift(a,b)` de la primera versió retorna −(desplaçament de b) — la segona (`disp`) ja el retorna directe |
| `redimensiona_interiors.py` | CapesInteriors 6961×4641 → 7648×5353 amb totes les capes a +(456,+462) (mesurat: la 03_1s d'Interiors i la d'Exteriors coincideixen a I+(456,462) = E, pic 0,96; Capa 1 = TIFF a I(−457,−463) ↔ EDITAT PERE = TIFF a E(−1,−1)); treu Mt16 i SLICES, posa la fusionada nova i **`header.channels = 3`** (⚠️ l'original tenia 4 —RGB + alfa fusionada— i amb 3 canals de dades i 4 a la capçalera Photoshop no ho obriria); a Exteriors mou 01_10.3s (+2,−1) i les quatre Linear Light (−1,−1). Còpies `*_abans_*.psb` |
