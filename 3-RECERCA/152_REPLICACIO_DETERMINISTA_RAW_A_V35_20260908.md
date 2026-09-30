# 152 — Replicació quasi determinista: dels RAW originals a la V35, amb la història d'errors i els guardarails (08-09-2026)

> Actualització 16-09-2026: aquest és el mapa històric V35. Les proves noves i els límits vius són a `output/reconstruccio_compactacio_20260915/README.md`. V29 perfils ja s’ha reproduït exactament en dues rondes: refine amb helper antic de quatre passades, després recentrat PCHIP recuperat i gran angular final. Usar una sola versió del helper per a totes les etapes canviaria el resultat. Recepta i procedència a `raw_replay/RESULTAT_V29_PROFILES.md` del paquet; la prova completa RAW→V68/V56 encara està pendent.

Ordre de Pere (08-09, nit): «repassa tots els passos que hem anat fent, els errors comesos i com ho hem anat subsanant; deixa-ho ben documentat, amb guardarails, perquè LLM menys llestos puguin replicar els mateixos resultats amb el mateix input (RAW originals i calibratge) i obtinguin un output molt semblant, quasi determinista.»

Aquest document és el mapa sencer. Les normes viuen a `.claude/skills/postprocessat-corona/references/normes_i_portes.md`, les trampes a `trampes.md` (índex `trampes_INDEX.md`) i les famílies d'artefactes a `.claude/skills/corregeix-artefactes/SKILL.md`; aquí no es repeteixen: es lliguen a cada etapa. L'entrada d'un replicador és `research/tools/v35_20260908/replica_v35.sh` (§6).

## 0. Què vol dir «quasi determinista» aquí, i per a qui és

- **Entrades**: els RAW de `0-ENTRADES/` (Vixen R6 III: 124 fotogrames de totalitat, 768 darks, 125 flats, 28 flats invertits; Sony A7RIIIA: 14 de totalitat + 16 del primer apuntament, 378 darks, 53 flats), amb el SHA-256 de CADA fitxer al `MANIFEST.json` del run que els va consumir.
- **Sortida**: `Capes Totals/V35.psb` (SHA-256 `50c8e1cfb7144794db67c227324238fb33b9ccaf91502ff33fb6f954692aa6d4`) i les 15 matrius canòniques de `research/tools/v34_20260907/cau` i `v35_20260908/cau|purs/cau` (hashes a `v35_20260908/frozen/INVENTARI_REPLICACIO_V35.md`).
- **Tolerància declarada** (`verifica_replica.py`): matrius float32 amb diferència relativa màxima ≤ 1e-4 i ≤ 5 % d'elements diferents (el BLAS amb fils mou l'últim bit); capes u16 amb ≤ 2 DN16 de diferència màxima i ≤ 2 % de píxels diferents; el PSB es considera equivalent si totes les capes u16 passen encara que el SHA del contenidor difereixi. La prova real d'aquest dia és a §6.
- **Tres nivells d'autoritat**, de més a menys congelat: (1) els runs de `cadena.py` (fases 0–2), immutables, amb el codi copiat dins; (2) la geometria a la graella de Pere i els artefactes de la V29 (`cau_final`: suports, pesos, mapa de resolució, perfils de contrast), amb rebuts i hashes; (3) la composició V34 (a1→b2) i la V35 (b3→c4), scripts curts i rebuts JSON a cada pas.
- **Regla per a l'LLM que ho repliqui**: executa l'etapa, comprova el rebut i el hash, i si una porta falla ATURA'T i informa. No «arreglis» res amb un suavitzat, una màscara, un retall o un farcit del producte: cada vegada que s'ha fet, ha costat una versió (§4).

## 1. El mapa de la cadena, dels RAW a la V35

| # | etapa | codi (dir sota `research/tools/`) | entrades | sortides i rebut | durada | porta que atura |
|---|---|---|---|---|---|---|
| E0 | Calibració, registre i composició LDIC per tren | `eclipse_determinista/cadena.py VIXEN CIENCIA` → run `019_VIXEN_CIENCIA_20260827T212404Z`; `cadena.py SONYTOT CIENCIA` → run `016_SONYTOT_CIENCIA_20260827T183356Z` | RAW + darks + flats (+ flats invertits Vixen); efemèride; `comu.TRENS` | `1-RUNS/NNN/`: `MANIFEST.json`, `codi/`, `0-calibracio` (pedestal, màsters de dark, flat radial F0.3), `1-registre` (F1.1 limbe, F1.2 Sol i llenç comú 8096×8960 a 2,1495″/px, F1.3 registre fi), `2-ldic` (F2.2 coherència k, F2.4 cel), `4-rebuts/*.json` | ~17 min per tren | F0.1 pedestal/saturació, F0.3 flat ≤ 8 %, F1.2 dos contactes, F2.2 k ∈ [1/2, 2], F2.4 ≤ 3 %, tancament HDR ≤ 5 % |
| E1 | Geometria del llenç comú a la graella de Pere (V23: 10551×7506) | `v25_lineal/etapa2d` (research/132) | capes de Pere de la V23 (immutables), llenç comú | `v25_lineal/cau_v25/geometria_v27.json` (`M_llenc_a_v23`; còpia congelada a `v35_20260908/frozen/params/`) | – | prova AZIMUTAL (pic a 0 ± 0,5°) + control nul girat 180° (la V25/V26 anaven girades 138,5° amb totes les proves «rotació-invariants» en verd) |
| E2 | Fonts i pesos a la graella final, mapa de resolució, perfils de contrast | `v29/` (V29_FINAL_GRID=1): `prepare_sources` → `prepare_final_grid` → `merge_pointings` → `coherent_resolution` → `fuse_and_filter` → `refine_detail` → (`gran_azimuthal`, `qa_rasters`, `audit_geometry`, `build_canvas`, `package_psb`, `finish_receipt`) | runs 019/016 (F1.3, F2.2), `geometria_v27.json` | `v29/cau_final/`: `vixen_support`, `sony_support`, `fusion_support`, `vixen_weight_G`, `sony_weight_G`, `sony_A_weights`, `sony_B_weights`, `sony_A_blend_weight`, `resolution_sigma`, `refined_detail_receipt.json` (perfils de contrast per canal + `scale_tanh`), `coherent_resolution.json`, `pointing_merge_receipt.json`, `delivery_manifest.json` | ~40 min | H1 ≤ 0,05 per capa, geometria azimutal PASS, porta Photoshop |
| E3 | Constants heretades per les capes de cadena | `v29_c03_fix/apply_offsets.py` (`offset_model.json`: offsets additius c03 per fotograma), `v30/fine_variants.py` (`fine_variants_receipt.json`: `scale_tanh` de 04/05/06), `v31/package_v31.py` (σ extern 3 px; 1,5 per a 04) | cau_final | JSON congelats a `frozen/params/` | – | H1, H1b |
| E4 | Operadors purs i receptes de pantalla | `v31_purs/` (`radial_filters`, `local_filters`, `wow_filters`, `sparse_conv.dylib` compilat de `sparse_conv.cpp`, `nafe_native.dylib`) | base G | `receipts/*.json` (paràmetres, LUT de pantalla) | – | injecció, jutge extern, cap H1/tanh/suavitzat als purs |
| E5 | Composició per grup a resolució completa (V34) | `v34_20260907/comu34.py` (instal·la la finestra gradual i el `plans` amb la LUT de linealitat Sony `R33_linealitat_sensor.json`), `a1_pesos_per_fotograma.py` → `b1_camps_per_fotograma.py` → `b2_recomposicio.py`; usa `v32_arcs_20260907/comu32.py` (flat Sony suavitzat σ32, grups A/B, offsets) | runs 019/016 (RAW rellegits!), `geometria_v27`, cau_final (suports, pesos), `offset_model.json` | `v34_20260907/cau/{vixen,sony_A,sony_B}_total_v34.npy` (H,W,3), `*_meta.json`, camps φ per fotograma i canal; rebuts `B1_camps_*.json` | 1 + 3 + 3 min | residu a l'altiplà per fotograma (informa), pesos = V29 (comprovat) |
| E6 | Fusió i capes (V35) | `v35_20260908/comu35.py`, `b3_fusio.py` → `b4a_capes_cadena.py` → `b4c_purs.py mgn wow` → `b4d_radial_vora.py` → `c4_psb.py build/verify/gate/publish` → `c5_rebut.py` → `d1_autoritat.py` | E5, cau_final, `refined_detail_receipt`, `fine_variants_receipt`, `resolution_sigma`, receptes de pantalla (V32 purs per a P01/P02, V34 purs per a P03–P05), modes/màscares de les 10 capes (de `V32.psb`, congelats a `frozen/modes_mascares_v32.npz`) | `cau/fusion_total_v35.npy`, `base_G_v35`, `support_v35`, `weight_vixen_v35`, `rho_v35`, `delta_v35`; `cau/{01,02,04,05,06}_v35_u16.npy`; `purs/cau/P0*_u16.npy`; `staging/V35.psb` → `Capes Totals/V35.psb`; rebuts `B3_fusio.json`, `B4a_capes_cadena.json`, `B4c_purs.json`, `C3_portes.json`, `C3b_vora_aparellada.json`, `C4_*.json` | 1 + 2 + 5 + 0,1 + 1 (build) + 1 (verify) + 0,3 (gate) min; C3 30 min | porta A+B (correlació amb la Vixen no baixa), δ holdout, pes Vixen = 1 a 1,0–1,9, H1 ≤ 0,05, geometria azimutal PASS, graó aparellat a les vores dins del nul, biaix d'anell al limbe ≤ 1,5 σ, porta Photoshop `OBRE 10551 px x 7506 px · 11 capes` |

Notes de dependència: E5 rellegeix els RAW (per `rawpy`) amb la calibració del run (darks, flat, pedestal, saturació) i el registre F1.3; per tant els RAW i els runs han d'existir a les rutes de `comu.TRENS`/`RUNS`. `c4` copia alfa, màscara, mode, opacitat i visibilitat de la capa homònima de `V32.psb` (9,6 GB); la còpia congelada `frozen/modes_mascares_v32.npz` (6,4 MB; 6 màscares diferents, totes rampes radials de la V29; 01/02 Superposar 36/20 %, 04/05/06 Superposar 36 % apagades, P0x Normal apagades) permet reconstruir-ho sense el PSB.

## 2. Paràmetres congelats (i on són)

| paràmetre | valor | on es declara | des de |
|---|---|---|---|
| llenç comú de la cadena | 8096×8960 px, 2,1495″/px, nord amunt; Sol per efemèride | `comu.LLENC_COMU`, F1.2 | 26-08 |
| graella final (Pere, V23) | 10551×7506; `M_llenc_a_v23`; CX 5361,768 CY 3775,748; R☉ 440,603 px | `geometria_v27.json`, `v29/common.py` | 05-09 (V27) |
| mode de color | CIENCIA (0,9302 · 1 · 1,1261) | `cadena.py` | 27-08 |
| pesos LDIC | w = terra(12→48 DN) · (1 − smoothstep(f, 0,35·alt, alt)) · t_exp, alt = 0,85·(sat − ped); màscara lunar per fotograma (guarda 2 px) | `comu34.finestra_v34` (V32 i abans: rampa lineal 0,70→0,85) | 07-09 |
| linealitat Sony (⛔ NO aplicada a V34/V35 per l'errata de l'etiqueta del run; aplicada des de la V36) | ln L(x) mesurat: 0 fins a x 0,425; −0,42 % (0,625), −0,53 (0,675), −0,56 (0,725), −0,45 (0,775), −0,51 (0,825), −0,92 (0,875), −1,2 (0,925), −1,66 (0,975); aplicat a (raw − dark)/L abans del flat; Vixen sense correcció | `frozen/params/R33_linealitat_sensor.json`, `comu34.lin_corr_sony` | 07-09 |
| flat Sony | perfil radial suavitzat σ 32 px del sensor, centre (2660, 4000) | `comu32.flat_ripple_correction` | 07-09 |
| camps de nivell per fotograma | σ 128 px per fotograma i canal natiu, gauge σ 512 px, ajust a l'altiplà | `v34/b1` | 07-09 |
| offsets c03 | `offset_model.json` | `v29_c03_fix` | 05-09 |
| guany A→B (Sony) | grau 2 en blocs de 128 px + residu local σ128 a 1/8; ghost de A exclòs (dist > 220–250 px) | `b3.merge_pointings` | 05-09/07-09 |
| pesos A/B | ∝ 1/σ² (variància del DoG 1,5/3 de ln G, σ 48), ghost 200→320 px, esvaïment 480 px a la vora del suport PLE; porta: correlació amb la Vixen a 2,5–5 R☉ (σ12 i σ24) no baixa més de 0,005 | `b3` V35 | 08-09 |
| ρ Sony→Vixen | per canal, σ 256 px, ajust a 1,5–4 R☉, extrapolat pel veí | `b3.fuse_trains` | 07-09 |
| δ Vixen→Sony·ρ | ⟨ln(V/(S·ρ))⟩ σ 256 a tot el solapament (sectors parells; holdout senars), entrada smoothstep 2,0→2,65 R☉ | `b3` V35 | 08-09 |
| pes Vixen | max(1 − smoothstep(r, 1,9, 3,5 R☉), fracció 1/σ²) · smoothstep(dist a la vora Vixen PLENA, 0, 720 px); ploma 160 px on s'acaba la Sony | `b3` V35 | 08-09 |
| capes 01/02/04/05/06 | ACHF(ln TOTAL_c) amb σ {2,4,8,16,32} / {24} / {1,2,4,8,16} / {2,4,8,16,32,48} / {4,8,16,32,64}, dividit pel perfil de contrast V29 per canal, mediana RGB, tanh amb `scale_tanh` V29/V30, `sn_smooth` amb `resolution_sigma` V29, `centre_rings` (H1), suavitzat extern σ 3 px (1,5 per a 04) | `b4a`, `refined_detail_receipt`, `fine_variants_receipt` | 05/06-09 |
| P01 NRGF, P02 RHEF | anells d'1 px; més enllà de la primera vora del llenç (8,48 R☉), anell sencer estimat per la forma azimutal dels 40 últims sencers; RHEF = CDF empírica; LUT de pantalla dels receipts V32 | `b4d` | 07-09 |
| P03 MGN | σ {1,25, 2,5, 5, 10, 20, 40}, k 0,7, h 0,7, γ 3,2, límits min/max de la base al suport | `v31_purs/local_filters` | 06-09 |
| P04/P05 WOW | à trous B3, 11 escales, sense denoise, bilateral (eq. 18) al P05 | `v31_purs/wow_filters` | 06-09 |
| condició de contorn dels purs | entrada = base al suport + exp(perfil azimutal mitjà de ln B) al forat i fora del suport (continuació lineal en ln dins, pendent dels 20 primers anells sencers); sortida al suport físic; LUT de pantalla dels receipts V34 | `b4c_purs` V35 | 08-09 |
| PSB | base lineal RGB escalada pel màxim dins del suport → 65535, alfa = suport; capes gris u16 amb alfa/màscara/mode/opacitat de V32.psb; compost = base + capes visibles (Superposar) | `c4_psb` | 07-09 |

## 3. Portes i llindars que un replicador ha de veure en verd

A més de la taula C de `normes_i_portes.md` (F0–F4, H1, H1b, H4, control nul, injecció): porta A+B (`B3_fusio.json → pointings.porta.acceptada_A+B = true`; valors d'avui σ12 0,036 → 0,044, σ24 0,165 → 0,199); δ holdout (`trains.channels.*.holdout_delta_despres_median_abs_pct`: G 0,39, R 0,76, B 0,65 %); pes Vixen per anell (`trains.perfil_pesos`: 1,00 a 1,0–1,9 R☉); H1 pitjor per capa (`B4a_capes_cadena.json`: 0,0075/0,0105/0,0252/0,0138/0,0083) i `geometria_azimutal.PASS` a les cinc; biaix d'anell al limbe (`B4c_purs.json`/receipts: P03 1,4 σ, P04 0,7, P05 0,1); graó aparellat a la vora Vixen dins del nul a 9 de 10 capes (`C3b_vora_aparellada.json`); `C4_verification.json PASS` i `C4_photoshop_gate.json` amb el literal OBRE.

## 4. Història d'errors i cures (el que un LLM ha de saber abans de tocar res)

| data | on | símptoma | diagnòstic ERRONI (si n'hi va haver) | causa real | cura | guardarail |
|---|---|---|---|---|---|---|
| 18-08 | CapesTotals V1–V5 | anell de colors, ratlla a 1,8 R☉ | capa Sony mal encaixada | graó HDR i capa desplaçada | encaix mesurat | RGGB al rebut; balanç a tot producte |
| 21-08 | corba de to | tot «rentat» o cremat | «no serveix» | `estira_log` per percentils cremava 1,67 dècades | corba DECLARADA (pendent 0,17/dècada, sostre = màxim de la dada) | «la corba és un paràmetre, mai un percentil» |
| 23-08 | filtres | halos i vores | – | filtre aplicat en circumferència; distanceTransform sobre cobertura amb el forat lunar (la Sony posava el 91 % del detall interior) | tot el rectangle; suport ple per a distàncies | norma del rectangle; **trampa del forat (1a)** |
| 24-08 | detall fase 3 | arcs concèntrics amb dents de serra | corona | perfil radial restat per CALAIX | perfil en log r interpolat; H1/H1b | «tota correcció per calaixos, interpolada» |
| 24-08 | flats | – | – | flats del 22-08 a 12,4° de l'orientació de l'eclipsi | flat radial validat amb flats invertits | flats del mateix dia o dither |
| 25-08 | Vixen | corbes a 1,25/1,51/1,97 | «patró periòdic» del sensor (fals: modes de la finestra FFT) | fronteres HDR = isofotes amb bony; anell verd del canal G | mediana de les tres realitzacions de canal; cura del cel per fotograma (Vixen) | «una coincidència de posició no és una causa: mou el paràmetre»; el jutge extern decideix |
| 25-08 | Sony | costures 92,6 % | – | la fase 3 no feia servir el compost coherent (sufix `_coh` perdut) | sufix arreglat | rebut amb paràmetres |
| 26-08 | color | corona 2,6× massa blava | – | balanç sense matriu; negre fals de libraw (real 512) | matriu CIENCIA; pedestal mesurat | RGGB i pedestal al rebut |
| 27-08 | pesos | «vara del pes» dins la Lluna | – | màxim global | assolible al mateix radi; màscara lunar per fotograma a TOTS els llocs que comparen | una sola funció de màscara |
| 27-08 | PSB | «no compatible» a Photoshop | – | fusionada en ZIP; blocs 8BIM/8B64; `topil()` torna 8 bits | RAW per a la fusionada; re-descodificar; `porta_photoshop.sh` | cap PSB sense la porta real |
| 28-08 | V18 | halos a 3,6–4,6 R☉ | – | Sony 8–18 % més brillant a la banda de la màscara | igualació en baixa freqüència (ρ radial × k≤2) | ρ suau i finestra declarada |
| 28-08 | V19 | fals bony 0,24 | – | fons autoreferent sobre valor PREMULTIPLICAT a la vora d'una màscara | des-premultiplicar | «a la vora d'una màscara el compost és premultiplicat» |
| 29-08 | estrelles | 1.263 «estrelles» | detecció cega | 97 % era gra | catàleg → imatge; control nul aparellat (puresa 95,8 %) | cap llista per llindar sense control nul |
| 30-08 | earthshine | −17 % de senyal | – | Wiener DoG amb cues | filtres per bandes en Fourier; injecció cega 0,90–1,10 | vara única entre versions |
| 31-08 | earthshine | «cràter» | tret lunar | mota de pols del sensor (no és als flats de 10 dies després) | pes 0 en 22 px | cap tret puntual sense posició predita |
| 02-09 | V25 | «cal Camera Raw» | – | base no lineal | fusió lineal + corba B declarada | base lineal, corba última |
| 04-09 | V25/V26 | «capes girades» | alineació 0,0 px per finestres/escaquer (rotació-invariants) | rotació de 138,5° | correlació circular en AZIMUT del perfil polar + nul | prova azimutal obligatòria |
| 04-09 | V26 | franja fosca 1,0–1,27 | – | ploma d'un camp exterior mesurada amb el forat lunar dins (**trampa del forat, 2a**) | `binary_fill_holes` només a la màscara auxiliar | mirar les vistes abans de lliurar |
| 05-09 | V28 | «falta camp» | cobertura | esvaïments 3,5→5 / 4→5; CORONA_c anticorrelada amb Brno de 5 R☉ enfora | TOTAL de 4 R☉ enfora; capa ampla a 9,6 | anell a anell contra Brno abans de lliurar |
| 05-09 | V30/V31 | minicercles | – | soroll allargat pel kernel angular; suavitzat cartesià | regularització radial; σ 3 px (V31) | H1 verd no exclou arcs de soroll |
| 07-09 | V32 | arcs lila i blaus 3,2–4,6 | corona? | ondulació fina del flat Sony (dither) impresa invertida; fronteres HDR amb desnivell; guany escalar amb tall sec | flat suavitzat σ32; camps de nivell per fotograma; ρ 2D; ploma | un artefacte igual a totes les fotos d'un apuntament només el veu l'altre tren |
| 07-09 | V32 marques | interior 1,15–2,3 marcat | artefacte | CORONA (correlació Vixen×Sony +0,67, nul −0,01) | res | el test creuat amb nul girat decideix; no discrimina al limbe |
| 07-09 | V33 | «suavitzat que segueix el S/N» | cosmètic | fabricava costures noves on canviava σ | REFUSADA | **norma: causa arrel, mai cosmètica, mai sacrificar detall** |
| 07-09 | V34 | graons de GRA a les entrades, +54 % al canvi de tren; Sony no lineal | – | pesos ∝ t amb salts 5×, finestra estreta | entrada gradual 0,35→0,85; LUT Sony; fusió per variància | filtres normalitzats = instrument de diagnòstic de la cadena |
| 07-09 | prova de linealitat | «la Vixen també falla» | cel·les 4×4 ponderades | artefacte de la prova | parelles a resolució completa | mesurar a la font sense ponderar |
| 08-09 | V34 marques | contorn del FOV Vixen a tots els filtres | – | ρ ajustat només a 1,5–4 (Vixen −2,9 % a la vora) + pes 0,36→0 en 160 px | δ σ256 + esvaïment 720 px | fila K de la skill; porta aparellada amb nul |
| 08-09 | V34 | P05 al limbe | – | **trampa del forat lunar (3a)** a `distanceTransform` | suports plens | pes per anell 1,0–1,5 al rebut de tota fusió |
| 08-09 | P03/P04/P05 | anells al limbe «recurrents»; rectangles al WOW | fusió/gra | mitjana d'un sol costat dels operadors isotròpics contra el forat; à trous dispers copia la silueta a ±2^s | condició de contorn declarada (perfil azimutal mitjà, només entrada) | fila O de la skill |
| 08-09 | porta | «graó −15 a NRGF» | – | calaixos dins/fora a radis diferents | porta aparellada al llarg de la normal + nul | «una porta hereta la geometria d'on va néixer» |

| 08-09 (tarda) | V34/V35 | «linealitat Sony corregida» als rebuts | – | la condició `run.tren == 'sony'` era falsa (el run és `SONYTOT`): la LUT no es va aplicar mai; ningú va comprovar que el canvi hagués entrat | V36: condició `startswith('SONY')` i prova amb/sense | **cap canvi declarat sense prova que ha entrat** (hash de sortida diferent o delta mesurat) |

Les tres vegades de la trampa del forat lunar (23-08, 04-09, 08-09) són la lliçó més cara: qualsevol funció que mesuri «distància a la vora» ha de rebre el suport amb el forat tapat (`suport | r < 1,6 R☉`), i el rebut ha de portar el pes per anell d'1,0 a 1,5 R☉.

## 5. Guardarails per a un LLM (llista de comprovació abans, durant i després)

Abans:
1. Llegeix `CLAUDE.md` sencer, `AGENTS.md`, l'última entrada de `CODEX_STATUS.md` i `CLAUDE_STATUS.md`; adquireix `.coordination/claim.lock/` (mkdir atòmic + `owner.json`) abans d'escriure; no facis mai cap ordre git en aquest arbre.
2. Intèrpret: `~/.venvs/eines-ia-py312/bin/python` (comprova amb `.claude/skills/apilatge-imatges-eclipsi/scripts/comprova_entorn.py --python`); `PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=4`. Cap ruta d'intèrpret escrita a pèl en un script nou.
3. Comprova els hashes del grup A–D de `frozen/INVENTARI_REPLICACIO_V35.md`. Si un difereix, no continuïs: algú ha canviat una entrada o un paràmetre.
4. No toquis càmeres, PTP, RAW ni runs (`1-RUNS/` és immutable); Photoshop només per `capes_totals_v14/porta_photoshop.sh`.

Durant:
5. Executa etapa per etapa amb el seu log; llegeix el rebut JSON i compara amb §3. Una porta en vermell atura; un avís (H1b) es declara.
6. Tota distància a una vora: suport PLE. Tota estadística per anell: anells complets o estimació declarada de l'anell sencer (b4d). Tot operador isotròpic: condició de contorn declarada al forat lunar.
7. Cap filtre a una circumferència; cap màscara feta de marques de Pere; cap inpainting, retall, esvaïment radial ni suavitzat com a correcció; cap píxel de Brno al producte. Si el resultat té un artefacte, es mesura a la FONT (a1–a3 del V35 com a model) i es cura a l'origen.
8. Els números del rebut es comparen amb la MATEIXA vara a la versió anterior (gra per radi, graó aparellat amb nul, biaix d'anell, H1); no es canvia la mètrica a mig camí.

Després:
9. Mira les vistes tu mateix (retalls 1:1 al limbe, a la vora Vixen, al relleu; polars) abans d'enviar res: Pere hi troba el que cap porta no veu.
10. PSB: `build` → `verify` (reobre i compara canal a canal) → `gate` (Photoshop real, literal OBRE) → `publish` (mai sobre un fitxer existent) → rebut al costat del PSB → punters d'autoritat (`d1_autoritat`) → `CLAUDE_STATUS` RELEASED → claim fora → cap procés propi viu.
11. Documenta al rebut CADA paràmetre i CADA preu (on s'ha perdut què). Un rebut sense paràmetres no és un rebut.
12. **Cap canvi declarat sense la prova que ha entrat**: abans de dir «la V_n aplica X», ensenya que la sortida canvia (hash o delta mesurat amb/sense X). La V34 i la V35 van declarar una LUT de linealitat Sony que una condició falsa (`run.tren == 'sony'` contra `SONYTOT`) va deixar sense aplicar mai.

## 6. Protocol de replicació i prova de determinisme

`research/tools/v35_20260908/replica_v35.sh [nom]` copia els scripts de la V34 (a1, b1, b2) i de la V35 (b3, b4a, b4c_purs, b4d, c4) a carpetes noves `v34_<nom>` i `v35_<nom>`, hi redirigeix les sortides (`output/v34_<nom>`, `output/v35_<nom>`), executa la cadena (~25 min) a partir dels runs 019/016, de `cau_final` i dels paràmetres congelats, construeix i verifica el PSB a `staging/`, passa `verifica_replica.py` (toleràncies de §0) i la porta Photoshop. No publica res i no toca cap fitxer canònic. Requisits: els runs a `1-RUNS/`, els RAW a `0-ENTRADES/` (E5 els rellegeix), `cau_final` de la V29, `V32.psb` (o adaptar `c4` a `frozen/modes_mascares_v32.npz`).

**Prova feta el 08-09-2026 (02:23–02:36)**, carpetes `research/tools/v34_replica` i `v35_replica` (logs conservats; matrius esborrades després de verificar), rebuts a `output/v34_20260907_replica/` i `output/v35_20260908_replica/`, verificació a `output/v35_20260908/4-rebuts/VERIFICACIO_REPLICA_20260908.json`:

| artefacte | resultat |
|---|---|
| `vixen_total_v34`, `sony_A_total_v34`, `sony_B_total_v34` (E5, rellegint els RAW) | **bit a bit idèntics** (max_abs 0, 0 elements diferents) |
| `sony_corrected_total_v35`, `fusion_total_v35`, `base_G_v35`, `weight_vixen_v35`, `rho_v35`, `delta_v35` (E6 b3) | **bit a bit idèntics** |
| `01/02/04/05/06_v35_u16` (b4a), `P01/P02` (b4d), `P03/P04/P05` (b4c) | **0 DN16 de diferència, 0 píxels diferents** |
| `staging/V35.psb` (c4 build+verify) | **SHA-256 idèntic al publicat** `50c8e1cf…ec6d4`, 4,481,840,046 bytes |

Amb `OPENBLAS_NUM_THREADS=4` al mateix Mac, la cadena E5+E6 és **determinista bit a bit** (no només «quasi»): els operadors són convolucions OpenCV/scipy, l'à trous en C amb fils per files (cada fila independent) i la lectura RAW per rawpy; cap pas depèn de l'ordre de reducció en paral·lel. En un altre ordinador o amb una altra versió de numpy/OpenCV/rawpy pot haver-hi diferències a l'últim bit dels float32; la tolerància de §0 les absorbeix i `verifica_replica.py` les quantifica. Durada real: E5 7 min, E6 12 min (b3 1, b4a 2,5, b4c 5,5, b4d 1,5, c4 2).

## 7. Què NO està congelat, i deutes

- La E2 (V29) no té un sol punt d'entrada: els seus scripts es van executar a mà en l'ordre de §1 i els seus artefactes de `cau_final` es conserven amb hash; refer-los des de zero exigeix seguir aquell ordre (els logs `.log` del directori en són la traça). El pla del 2027 (research/129) els ha de portar dins de `cadena.py` com a fases 6 i 7.
- La E1 depèn de les capes de Pere de la V23 (per ajustar `M`); el JSON congelat evita tornar-hi.
- Pere edita a mà: modes, opacitats i màscares de les capes al PSB són seus (congelats a `frozen/modes_mascares_v32.npz`); qualsevol versió nova els hereta.
- Residus declarats de la V35: entrades dels fotogrames (graó de gra 0,93; captura), vora A al P04, primer anell 1,00–1,03, anells blaus de la Vixen, taca NE, registre dels fotogrames llargs Sony.
- El BLAS amb fils no és bit a bit; la tolerància de §0 ho absorbeix. Amb `OPENBLAS_NUM_THREADS=1` el resultat és més estable però 3–4× més lent.
