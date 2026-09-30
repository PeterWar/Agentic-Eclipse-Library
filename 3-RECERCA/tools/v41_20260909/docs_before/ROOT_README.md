- [158 — Nubols.psb: les marques verdes de la RHEF no són núvols (cel de la totalitat + corona feble; el gra fi és un patró fix del sensor Vixen que camina amb la deriva)](158_NUBOLS_LES_MARQUES_VERDES_DE_LA_RHEF_NO_SON_NUVOLS_20260909.md)
- [157 — V40: el gra fora de la corona amb Wiener regional + garrote per banda, soroll mesurat a totes les vores i sense terme creuat](157_V40_GRA_FORA_DE_LA_CORONA_WIENER_REGIONAL_I_GARROTE_20260909.md)
- [156 — V39: el soroll dels filtres fora de la corona, curat amb un guany de Wiener per escala i el soroll mesurat en meitats](156_V39_SOROLL_DELS_FILTRES_GUANY_WIENER_SOROLL_MESURAT_20260909.md)
- [155 — V38: la Lluna a l'inici, la franja de l'oest mesurada a la font (cromosfera, no un artefacte), i el projecte complet](155_V38_LLUNA_A_L_INICI_FRANJA_A_LA_FONT_I_PROJECTE_COMPLET_20260908.md)
- [154 — V37: el limbe: capes ACHF saturades contra el forat, farcit que conserva els anells parcials, i la franja de la unió temporal](154_V37_LIMBE_CONDICIO_DE_CONTORN_I_FRANJA_20260908.md)
- [153 — V36: la vora quadrada dels 8 s de la Sony (vinyetatge), els anells discrets de NRGF/RHEF, i l'errata de la LUT Sony](153_V36_MARQUES_V35_VORA_8S_I_ANELLS_DISCRETS_20260908.md)
- [152 — Replicació quasi determinista dels RAW a la V35: mapa de la cadena, paràmetres congelats, portes, història d'errors i guardarails per a LLM](152_REPLICACIO_DETERMINISTA_RAW_A_V35_20260908.md)
- [151 — V35: les marques de la V34 mesurades a la font i curades a l'origen (vora Vixen, trampa del forat, limbe dels operadors isotròpics, relleu); i què causava el MGN](151_V35_VORA_VIXEN_FORAT_I_LIMBE_20260908.md)
- [150 — V34 a l'origen: entrada gradual, Sony lineal, fusió per variància; NRGF/RHEF amb anell sencer](150_V34_A_L_ORIGEN_20260907.md)
- [149 — Què causava les marques de la V33: la V33 mateixa; i a sota, graons de gra a les entrades, canvi de tren per radi, i la Sony no lineal](149_CAUSA_DE_LES_MARQUES_V33_20260907.md)
- [148 — V33: resolució que segueix el S/N i NRGF/RHEF sense la vora del llenç](148_V33_RESOLUCIO_SN_I_VORA_LLENC_20260907.md)
- [147 — Revisió del PSB anotat de la V32: l'interior és corona; el que queda és dels filtres](147_REVISIO_MARQUES_V32_20260907.md)
- [146 — V32: els arcs lila i blaus, trobats a la font i curats a la font](146_V32_ARCS_A_LA_FONT_20260907.md)
- [145 — Revisió capa a capa del PSB anotat per Pere](145_REVISIO_MARQUES_V31_20260907.md) — 07-09-2026. 19 capes; marques grogues/blaves/liles, verds dubtosos; originals intactes.
- [144 — Geometria dels arcs: orientació tangencial i centre indeterminat](144_GEOMETRIA_ARCS_SOLARS_20260906.md) — 06–07-09-2026. Cercles/el·lipses amb centre lliure; control H1 circular, geometria de les capes finals no demostrada; V31 preservada.
- [143 — Gramòfon: funcions contínues 2D, preservació i prova de font](143_GRAMOFON_FUNCIO_CONTINUA_2D_20260906.md) — 06-09-2026. Recerca acabada; cap candidat promogut, V31 preservada.
- [142 — V31: filtres independents, inventari i límits](142_V31_FILTRES_PURS_20260906.md) — 06-09-2026; rectificació posterior de l'abast del jutge extern.

# Índex de recerca i evidència

`research/` conserva decisions, mesures i contrasts. No és un segon fitxer
d’estat. Per reprendre el projecte, l’ordre és:

1. `../AGENTS.md` i el bloc inicial de `../CLAUDE.md`;
2. `../.coordination/HANDOFF_2026-09-05_V31.md`;
3. `../output/pdf/Informe_auditat_run_Eclipse_Command_20260812T202219.pdf`
   per al run real, o `../gui/QA_REPORT_1.0.2_2026-08-10.md` només per a la
   baseline de captura;
4. el document específic d’aquest índex i els runs/manifests que cita.

## Estat operatiu actual

- `139_V31_mes_suavitzat.md` — actual: minicercles en filtres NO azimutals segonsPere; cinc suavitzats, azimutals intactes i cost de detall declarat.

### Antecedents V30 i V29

- `137_V30_minicercles_i_variants.md` — V30: reducció d'arcs de soroll a03, originals preservats i cinc capes noves; evidència i límits.
- `138_V30_auditoria_coherencia.md` — punts d'entrada reconciliats, snapshots i scripts històrics que no s'han d'usar com a vigents.
- `136_V29_capa03_corregida.md` — correcció radiomètrica dels pentàgons de03 dinsV29; és l'entrada immutable deV30.
- `135_V29_pentagonals.md` — diagnòstic anterior a la correcció136.
- `134_V29_detall_unio_temporal.md` — construcció deV29 i preservació de corona temporal.

## Antecedents històrics (les receptes superades no són instruccions)

- `133_LA_V28_EL_CAMP_DE_BRNO_I_LA_CORONA_SOLA_QUE_MENTIA_2026-09-05.md` — **V28.psb, mesurada anell a anell contra les quatre fotos finals de Brno** (mètode del 114, `etapa6_compara_brno.py`): ⛔ la corona sola de la descomposició (CORONA_c) s'anticorrelaciona amb Brno de 5 R☉ enfora (fins a −0,8) mentre que el TOTAL (corona + cel) segueix el 200 mm de Brno a 0,75-0,80 fins a 8,6 R☉; el camp que «faltava» no era cobertura (la Sony arriba a 13,7 R☉ al llenç) sinó els esvaïments dels filtres; capa nova `04 ACHF ample 9R` (passa-alt azimutal 256-1024 px d'arc, font híbrida corona sola ≤3 → total ≥4 R☉) fins a 9,6 R☉, base cel/4 visible; ghosts de Pere esborrats a l'origen; contrast azimutal del compost al nivell del 200 mm de Brno fins a 7 R☉. Deute: llenç més gran per a la Sony (fase 2).
- `132_LA_V27_LA_GEOMETRIA_GIRADA_I_LA_PROVA_AZIMUTAL_2026-09-05.md` — **V27.psb**: ⛔ la base de la V25/V26 anava GIRADA 138,5° respecte de les capes de Pere (ell ho va dir dues vegades) i les tres «proves» d'alineació (finestres de fase, escaquer, forat lunar) eren rotació-invariants; la prova que ho veu és la correlació circular en azimut del perfil polar (pic a −138,5°, també sobre els renders del Photoshop); geometria refeta (−46,6° OpenCV, centre en polar, escala 1,0 declarada, forat lunar a 2,5 px del disc C2). Les marques de Pere als filtres: arcs concèntrics (graons HDR amplificats) → detall gran com a passa-alt només azimutal; ghost de 3 R☉ → inpainting a l'origen abans de tots els filtres. Noms curts de projecte i capes. Regla nova: prova azimutal i control nul a tota geometria.
- `131_LA_V26_ELS_ARTEFACTES_I_LA_SKILL_QUE_ELS_CORREGEIX_2026-09-04.md` — **CapesTotalsV26_lineal_B.psb** i la skill `corregeix-artefactes`: les marques de Pere sobre la V25 estudiades una a una (sis ghosts de la lent Sony a ~8 R☉, vores rectes de l'extensió sintètica, ratllat del patró fix de la Sony en dues famílies a 27,5 px), la prova que la base SÍ està alineada amb les capes 09/10 de Pere (0,0 px, escaquer; el desplaçament de 7-9 px és de les capes 01-03 en quarantena), i la troballa de fons: el cel iguala la corona a 2,5 R☉ i la supera ×5 a 4 i ×10 a 5 R☉, o sigui que la base amb cel surt plana de 2,7 R☉ enfora → capa nova de detall ACHF 32-256 px sobre la corona sola (NRGF complet, 3,5·MAD per anell) i base alternativa oculta corona + 0,25·cel. El detall fi (2-32 px, σ24) és gra de 3,5 R☉ enfora i s'esvaeix 3,5→5. Quatre trampes noves més tres de la ronda 3.
- `130_LA_V25_LA_BASE_LINEAL_A_LA_GRAELLA_DE_PERE_2026-09-02.md` — **CapesTotalsV25_lineal_B.psb**: la base de la V24 substituïda per la fusió lineal dels dos trens (runs 019 i 016, ρ per canal, fons per raig) amb la corba B triada per Pere (0,22/0,74/0,045) i el detall ACHF 2-32 px en Superposar (H1 0,0007), a la graella de la V23 (rotació −91,97° mesurada sobre la corona; residu local 1,5 px); capes de Pere intactes, perles/limbe/earthshine/estrelles/reflex manen; porta Photoshop OBRE. Cinc trampes noves (dos `comu.py`, 0×NaN, fusionada de 4 canals, ordre de capes de la V24 i banda de l'earthshine, forat lunar de la cadena ≠ disc C2).
- `129_AUDITORIA_GENERAL_I_PLA_2027_2026-09-02.md` — **auditoria general del projecte** per ordre de Pere: balanç, què ha funcionat i què no, taula DEMOSTRAT/FALTA/IRREDUCTIBLE per fase, les deu lliçons més cares, i el pla per a les quatre esperances (més detall: el compost lineal a la graella de la V23 amb la corba com a última passa; Eclipse Command 2027: la V1.02 no cobreix 271 s; web meteo 2027: en mode proves amb restes del 2026; automatització: pipeline per fases sobre `cadena.py`). Respon la pregunta dels halos de Claridad/Neblina (no mesurats; pila lineal substituta i prova A/B). Skills reescrites el mateix dia. ⚠️ Verificació adversària parcial (76 de 117 agents) i cost del 21 % del pressupost setmanal: cap flux massiu més. Les 11 preguntes a Pere al §13.
- `125_CAPES_TOTALS_V21_ESTRELLES_I_EARTHSHINE_2026-08-28.md` —
- `126_EARTHSHINE_DOS_TRENS_I_EL_MAPA_LROC_2026-08-29.md` — l'earthshine dels dos trens (8 fotogrames al marc lunar comú) i la validació amb el mapa LROC de la NASA: r=+0,792 a 7,0σ, orientació predita per efemèride, Vixen×Sony=+0,928.
- `127_RECERCA_EARTHSHINE_SNR_I_LA_VARA_UNICA_2026-08-30.md` — inventari de les 9 versions d'earthshine amb la mateixa vara; el coll d'ampolla era el model de vel; V4 amb les portes de Codex (injecció cega 0,958, r=+0,877; significança citable = 126).
- `128_LA_V24_EL_TO_FOSC_I_EL_REFLEX_DE_LA_FLAMARADA_2026-09-01.md` — la V24: la Lluna al to del DSC06984, el reflex de la flamarada per la cadena exacta, el biaix del limbe fotogràfic (3,6 px) i, al §7, el perímetre amb la dada real del DSC06993 (la guarda i el sostre LDIC buiden el trànsit: per això un fotograma sol guanyava l'agregat).
  **CapesTotalsV21.psb: les estrelles fetes bé i la capa d'earthshine.** El
  «lio» d'estrelles que Pere va veure, mesurat: **el salt d'apuntament de la
  Sony va incloure una rotació de camp de +7,9′** (7-8 px de doblament a la
  vora) més 2-5 px de translació per fotograma; la deriva sideral és només
  0,15-0,42 px. Plate-solve relatiu (correlació de fase per finestres, rms
  0,04-0,06 px; fonts brillants entre apuntaments, rms 1,13 px), apilat >1 s
  registrat a les estrelles (base DSC06993, el 8 s amb la Lluna centrada;
  alineació amb la capa Sony −0,14 px) → capa ESTRELLES (1.263 fonts,
  elongació mediana 1,97→1,48) i apilat registrat a la LLUNA (rotació
  compensada, només disc) → capa EARTHSHINE. ⛔ Trampes: el total de la
  correlació de finestres es refereix al CENTRE (l'origen deixa un biaix de
  WIN/2 que un rms de 0,06 px no delata); la finestra ha de ser lliure a
  TOTES DUES imatges; el gra correlacionat mata la correlació entre
  apuntaments (pics ≤0,03).

- `124_CAPES_TOTALS_V19_FONS_PER_RAIG_2026-08-28.md` — **CapesTotalsV19.psb:
  l'operador `fons_per_raig` aplicat al llenç sencer i LLIURAT** (4,35 GB, 16
  capes, Photoshop OBRE): les capes de Pere byte a byte + `FONS_PER_RAIG`
  (màscara editable = la seva rampa exacta) + `ESTRELLES` (2.456 fonts,
  additiva). Portes: 16/17 marques a bony 0,0000 (la 17a → 0,019 = gradient
  real del cel, declarat), sectors 0,0100→0,0004, cobertura 0,68→1,00.
  ⛔ Tres regles noves: el fons autoreferent menja valors DES-PREMULTIPLICATS
  (a la vora de màscara la «dada» és cel×màscara); el gra correlacionat del
  drizzle mata el filtre adaptat (el catàleg NR de Pere és el detector); un
  gradient de cel no és un arc (la porta monòtona no els distingeix).

- `123_EL_FONS_PER_RAIG_DESENFOC_RADIAL_DE_PERE_2026-08-28.md` — **el mètode
  manual de Pere que mata els halos (Desenfoque Radial ZOOM + rampa radial),
  estudiat i formalitzat com a operador `fons_per_raig`**: al camp exterior
  l'artefacte és variació AL LLARG del raig i el senyal és variació EN AZIMUT,
  o sigui que un suavitzat només en ln r (autoreferent, sense referència que
  es pugui enverinar) mata el 100 % dels halos i conserva els streamers.
  Mesurat: màscara = rampa radial pura 2,45→3,25 R☉ (R² 0,992), nucli del zoom
  ±10-20 % de r (σ_lnr≈0,2), 15/17 marques a bony 0,000. ⛔ Preu del mètode
  manual: estrelles mortes des de 3,1 R☉ (amb vetes radials d'11,6 σ), −25-30 %
  d'amplitud tangencial a 4-7, +3-4,4 % de nivell a 3-4,5, i des de 3,25 R☉ el
  producte és cosmètica. ⏭️ El prototip (`operador_prototip.py`) iguala o
  millora totes les portes i **recupera 2.097 de 2.102 estrelles** (Pere: 1).

- `122_CAPES_TOTALS_V19_SEGONA_RONDA_HALOS_2026-08-28.md` — **la segona ronda
  de marques (VERD lluminància / TARONJA to) diagnosticada: les dues famílies
  eren de la V18** — el fit del ρ es va menjar la vora enverinada del mosaic
  Vixen (px saturats, zeros i rolloff; la referència sana s'acaba a r=5,0 al
  pitjor sector) i la fosa per canal de la finestra pintava un viratge de to
  del 12 %/R☉. Disseny V19 (referència robusta ≤4,9, mediana, k≤4, retenció
  global, fosa de croma cap al to uniforme) amb portes que passen a 1/4;
  ⚠️ el PSB mai no es va escriure (la sessió va morir a mig construir) i el
  mètode del `123` el supera al camp exterior. ⛔ Dues caçades: el r_stop
  variable per azimut pinta esglaons azimutals; el contrast local sense
  control aparellat per radi es contamina de perfil radial.

- `121_CAPES_TOTALS_V18_HALOS_I_FORMAT_CANONIC_2026-08-28.md` — **els halos de
  la fusió Sony↔Vixen morts per igualació en BAIXA FREQÜÈNCIA** (S′ = S·ρ, ρ =
  radial × Fourier azimutal k≤2 per canal, finestra declarada ≤5,5→7 R☉):
  pitjor bony 0,0024 contra els 0,03-0,07 dels 9 arcs que Pere va pintar, camp
  llunyà intacte (p99 dif 0,0000 fora de 7 R☉). ⛔ Dues versions de ρ caçades
  per les portes (camp lliure que perseguia la costura d'apuntaments; mostreig
  clavat a l'últim calaix que tocava el camp llunyà): el model suau PER
  CONSTRUCCIÓ i la finestra DECLARADA són la lliçó. ⏭️ I **el format canònic de
  la Sony queda après** (Camera Raw de Pere, mesurat i desat a
  `FORMAT_CANONIC_SONY_PERE.json`): interior ~0,90 → cel fosc i blau, ombres
  p0,5 ≈ 0,08-0,10 — cap render pla de la cadena com a lliurable estètic.

- `120_CAPES_TOTALS_V17_SONY_MES1S_I_WB_2026-08-28.md` — **la V16 de Pere
  (re-escenificada: llenç 12415×12095, Vixen rotada +10,880° mesurada, Lluna al
  mig) amb l'apilat Sony de TOTS els >1 s** (2s×3 + 8s×2, dos apuntaments; la
  dada interior avança de 2,77 a 1,95 R☉), compost del RAW en un re-mostreig a
  la seva geometria i alineat a (−0,10, +0,08) px dels plomalls de la seva capa
  01. ⛔ Lliçó de mètode: el WB/nivell va perseguir el NEGRE dues vegades
  (fusionada i capa 09, totes dues fosques a l'anell amb les capes 08-01
  apagades) — la referència bona és **la capa 01 (10,3 s), la capa el paper de
  la qual assumeix la Sony**: convergència al 3r decimal, guanys R×1,001 ·
  B×1,188. Màscara de mescla smoothstep 2,00-2,65 R☉ (zero exacte dins de la
  vora de saturació: cap halo). Limbe de la 09 net (disc mesurat al contingut,
  198 kpx). Fidelitat byte a byte de tota la resta; porta Photoshop OBRE.

- `119_CAPES_TOTALS_V15_LLENC_ESTES_I_SONY_8S_2026-08-28.md` — **la V14 amb el
  llenç estès (7648×5353 → 14572×14196) i la capa dels 8 s de la Sony** a baix
  de tot: un fotograma per apuntament (DSC06987/DSC06993; la moguda fora),
  recepta exacta de les capes LDIC del run 016, dada 2,77-14,87 R☉, un sol
  re-mostreig del RAW a la graella nova. ⛔ Troballa de geometria: **els dos
  runs no comparteixen pa_north** (VIXEN 57,19°, SONY 90,27°; la diferència,
  33,1°, és la rotació entre trens de la calibració). Les 12 capes de la V14
  hi van byte a byte; alineació Sony↔V14 verificada a (+0,18, −0,17) px.
  Lliurable `CapesTotalsV15.psb` (PSB: passa de 2 GB) amb rebut i vistes.

- `118_CAPES_TOTALS_V14_ALINEADA_I_LIMBE_NET_2026-08-28.md` — **la V14 refeta
  sobre la V13_Pere mateixa** («overwrite de l'actual, que no serveix per
  res»): píxels de Pere byte a byte, només moviments enters d'1 a 3 px i
  màscares multiplicades dins del disc lunar. ⏭️ **La desalineació mesurada
  sobre la corona refuta les DUES hipòtesis prèvies**: les capes cauen en tres
  grups separats per desplaçaments quasi exactament ENTERS — retocs manuals de
  Pere amb les fletxes sobre DNG que ja compartien la geometria de 572A2969.
  Residu re-mesurat al fitxer escrit: **0,23 px** (abans 2,9). ⛔ **El vel del
  limbe no el posaven les màscares 10-12** que l'encàrrec assenyalava: era la
  capa 01 (màscara 0,08-0,11 dins del disc × bloom 0,50-0,87); cura
  multiplicativa amb el disc de C2 declarat, vel **0,038-0,090 → 0,0004-0,0017**
  i silueta p95 **6,0 → 3,5 px** (el màxim de 6,5 és la protuberància, real).
  ⛔ Trampa nova: als documents de 16 bits **`topil()` de psd-tools retorna la
  màscara a 8 bits** — re-codificar des d'allà deixa el canal a la meitat i el
  fitxer corromput; cada canal editat s'ha de tornar a DESCODIFICAR abans de
  desar. Substitueix el lliurable del `117` (apartat a `Documentacio i QA/`).

- `117_CAPES_TOTALS_V14_LA_MAQUETA_CALIBRADA_2026-08-27.md` — **la V13 refeta
  amb la dada calibrada**, per encàrrec de Pere. ⏭️ **El llenç de la V13 queda
  identificat**: és la graella del sensor de la Vixen sense girar, amb la zona
  visible del RAW a (457, 463), i ⛔ **les seves capes NO estan registrades
  entre elles** (el limbe hi cau a ≤2,3 px de la posició crua del seu fotograma;
  entre la primera capa i l'última el Sol es mou 8 px). ⏭️ **El limbe brut té
  una causa sola**: *una màscara demana píxels que la seva exposició no té* —el
  vel de la capa de 10,3 s dins del disc, i la vora interior de cada esglaó, que
  renderitzada és un halo (la de 1/8 s a 1,17 R☉ és la que Pere va marcar)—. La
  cura no pinta res: `màscara_V14 = màscara_V13 · validesa_de_la_capa`. Disc
  lunar **0,137 → 0,0000**; el màxim del perfil passa de **2,0 R☉ a 1,07**.
  ⏭️ **§6 bis: la Lluna no sortia rodona** —el llenç va centrat al Sol i la
  Lluna hi llisca 28,5 px, o sigui que la silueta era la INTERSECCIÓ dels
  discos: 16.643 px de corona dins del disc de C2 i una **mossegada de 23 px**
  que es menjava la protuberància—. Curat **declarant un sol disc lunar** (el
  de C2) i posant-hi a sobre la capa de **protuberàncies de C2 en Aclarir**:
  desviació del radi **23 px → 1,5**. Porta F nova.
  ⚠️ I un preu mesurat: **un muntatge per capes reinstal·la la costura que el
  LDIC evita per construcció**, aquí a **0,21 % del nivell** contra l'1,1-1,3 %
  que el `100` va mesurar entre esglaons veïns. ⛔ I una trampa nova al §7, que va deixar el fitxer sense obrir-se: **la imatge fusionada d'un PSD/PSB no admet `ZIP`** (Photoshop diu «no és compatible»; les capes sí que hi van), i el lector que et diu que un fitxer està bé no pot ser el mateix que l'ha escrit — `sips -g pixelWidth`. Lliurable:
  `~/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/CapesTotalsV14.psd`.

- `116_ELS_QUATRE_DEUTES_FLAT_BLAU_DERIVA_ESTRIAT_2026-08-27.md` — les
  ⏭️ **§7: decisió de Pere — el mode de color MEMORIA queda DEPRECAT** i el
  projecte segueix només amb CIENCIA (blanc sobre el Sol, AM0). La cadena
  refusa arrencar-ne un de nou; els runs vells es continuen llegint i el
  `DSC06991` continua fent de CONTROL, no de referència de render.
  ⏭️ **§9: els runs es numeren** (`NNN_TREN_COLOR_segell`, cronològic i comú
  a tots els trens), s'esborren els set incomplets (36 GB) i cada carpeta de
  `2-OUTPUT` diu de quin run ve. Mapa generat des del disc a
  `2-OUTPUT/MAPA_DE_CARPETES.md`.
  quatre feines que el `115` va deixar obertes. ⏭️ **El flat de la Sony,
  mesurat pel salt de muntura, s'ADOPTA**: valida fora de mostra (dona el guany
  que promet) i **la deriva fotomètrica contra la Vixen cau del 13,51 % al
  7,43 %**; ⛔ però **no** recupera el detall fi (1,8°: 0,890 → 0,884) i **no**
  mou la porta de brillantor, o sigui que **el `115` §13 i §15 queden
  rectificats**: el sistemàtic bimodal per apuntament és **el cel canviant en el
  temps**, no el flat, i la coincidència de magnitud (7-9 % contra 7,7-9,7 %) era
  una coincidència. ⏭️ **El blau queda descompost**: dels 5-11 %, **~3 punts són
  les dues càmeres** —i la matriu de color en prediu **més**, o sigui que no és
  cap defecte— i la resta la posa la cadena (2 la composició, de 3 a 8 la resta
  del cel). ⛔ **La quincunx del verd queda REFUTADA** (G/(R,B) = 1,12) i
  «l'estriat fi és només de la Vixen» era massa fort: la Sony també el té.
  Tres trampes de mètode noves.
- `115_LA_SONY_ENTRA_A_LA_CADENA_2026-08-27.md` — el segon tren entra al
  llenç comú i es converteix en **jutge independent**: Vixen × Sony dona
  0,985-0,998 de 90° a 4,5°, millor que l'acord de Brno amb ella mateixa a
  4,5°. La «quarantena» era **el segon apuntament** (salt de 749 px) i només
  cinc fotogrames van moguts de veritat. Fase 0 de l'A7RIIIA mesurada (pedestal
  512 pla dels darks: aquest cos **no té zona emmascarada**), sis suposicions de
  la Vixen que eren seves i dos defectes reals. ⚠️ Les seves §13 i §15 queden
  **rectificades pel `116`**.
- `114_AUDITORIA_ESTRUCTURA_CONTRA_BRNO_2026-08-27.md` — l'estructura de la nostra corona contra els quatre composts de Brno, amb el seu acord mutu de control: el detall fi PASSA (0,89–0,96 d'1,8° a 12°), la forma gran també (0,91–0,99), la protuberància de θ≈133° és real i queda un dèficit modest per sota d'1,12 R☉ que la Sony ha de desempatar. Porta nova F3.2 (tancament HDR per BRILLANTOR) i sis errors de mètode meus.
- `108_LA_MAQUETA_V13_I_LA_CORBA_DE_TO_2026-08-26.md` — ⏭️ **per què el
  projecte està encallat, i és UN sol número**: la maqueta de Pere demana
  **0,166 de nivell per dècada de B/B☉** i `estira_log` en fa **0,503**
  (×3,03). La dada abasta **3,92 dècades** i l'estirament n'ensenya **2,25**:
  ⛔ **es cremen 1,67 dècades** —329.659 px a 0,998 **fins a 1,45 R☉**, o
  sigui cromosfera, protuberància i corona interior senceres— i la corona
  exterior s'ensorra. ⏭️ **La corba que Pere va aplicar a mà a
  `CapesTotalsV13_Pere.psd` el 21-08 a les 14:21 diu exactament el mateix**
  (negres a terra, ombres amunt, **altes llums avall fins a −0,14**), i de
  passada **arreglava el rentat de la Lluna** que `research/87` va veure a la
  V13 de les 13:22 (0,137 → 0,024): el veredicte del `87` és de pedigrí, no
  d'aspecte. ⛔ **Regressió**: `research/93` (23-08) ja tenia les cures i el
  pilot no les va heretar — l'escalar únic ×1,119 deixa la Sony amb **el R
  un 19 % baix i el B del 19 al 35 % alt** (guanys per canal reals
  1,074/0,858/0,904; residu 0,1 % un cop igualat), el cel es resta com a
  **constant** quan varia del 28 al 65 % pel camp, i la base surt **grisa**
  perquè els factors de `research/75` §5.2 són **per píxel verd** i R/B no
  estan calibrats. L'enquadrament no és un problema de dada: la caixa 3:2
  amb **100 % de cobertura** és de ±8,58 × ±5,72 R☉. Prova d'aspecte
  reproduïble: `research/tools/prova_aspecte_maqueta/prova_aspecte.py`.

- `107_LA_CACERA_FINAL_LA_MEDIANA_I_EL_MUR_2026-08-25.md` — ⏭️ **la cacera
  de l'artefacte, tancada**: vuit candidats jutjats en una nit; **el detall
  final passa a la MEDIANA de les tres realitzacions de canal** (jutge
  +0,00347 ± 0,00178, correlació amunt a 4 de 5 bandes; mètrica de Pere
  −8,54 → **−2,93·10⁻⁴**, el 66 % de l'anomalia fora; H1/G/rectangle PASS).
  ⛔ El terç restant és IRREDUCTIBLE amb aquestes dades — §2 cartografia el
  mur: la direcció cromàtica dels arcs ≡ corona E; l'amplitud no discrimina;
  l'estadística anular s'autoemmascara; el nul honest treu cel COMPARTIT i el
  jutge el penalitza; i el model físic de barreja (v6) explica el 67-81 % de
  la desviació cromàtica global però ZERO als arcs (hi manen les diferències
  DINS de cada esglaó — les dues aparicions separades 40-80 s — que demanen
  un desconegut per fotograma que no es pot restringir). R i B sols mesurats
  NETS als traços (+0,77/−0,78). Eina nova per a Pere:
  `Eclipsi_2026_parpelleig.psb` (les realitzacions per capes, mateixa escala).
  Cura completa = protocol 2027.

- `106_LA_LLUMINANCIA_DE_BRNO_I_LA_CURA_RGB_2026-08-25.md` — ⏭️ **la ronda
  final del pilot**: el detall de la fase 3 passa de G sol a **LLUMINÀNCIA**
  (ln L = (lnR+2lnG+lnB)/4) — **PASS del jutge +0,00686 ± 0,00221 (3,1 σ)**,
  més gran que el de la cura del cel, amb la mètrica de Pere a la meitat
  (−8,54 → −4,04·10⁻⁴), la mateixa quantitat de detall i totes les portes
  PASS: la tercera via que supera A i B alhora. La **cura del cel estesa a R
  i B** (0,18 % / 0,34 %; el B pitjor, com mana el mecanisme) surt **EMPAT
  als dos jutges** i s'adopta com a *compleció* de la cura G aprovada (la G
  sola fabricava un desequilibri cromàtic). ⚠️ Confusor nou: els camps
  cromàtics dels dos trens correlacionen 0,55-0,98 (cel compartit + retenció
  Bayer semblant) — el jutge cromàtic és parcialment cec. Producte final amb
  fusionat (G PASS, rectangle PASS) i projecte Photoshop a
  `output/pilot_vixen_fable_20260825_lliurament/`.

- `105_COM_HO_FA_BRNO_EL_PROTOCOL_DRUCKMULLER_CONTRASTAT_2026-08-25.md` — ⏭️
  resposta documentada a «com ho soluciona l'equip Druckmüller?» (el mecanisme
  del 104): **ho maten a la captura** (escala monòtona de factor 2 amunt-avall
  tota la totalitat, 8-50 aparicions per esglaó, cadència 0,3-3 s/foto;
  Habbal 2011) **i el detall mai no es compon per canal** (una sola
  lluminància; color com a amplitud minúscula, saturació ×50-400; tesi
  Druckmüllerová 2014); la transparència restant es tracta per selecció,
  redundància i k(φ),q(φ) per segment dins el LDIC — **cap cura 2D per
  fotograma publicada: la nostra del 103 va més enllà del seu públic**. La
  Lluna, amb pes −1 per fotograma i disc ancorat a UN instant declarat.
  Confirma els requisits 1 i 2 del §1 quater. I **Brno ja ha publicat tres
  composts del 12-08-2026** des de Pico Trigaza (208-298 imatges, Sol a 7°):
  benchmark extern directe.

- `104_LA_MASCARA_DE_PERE_I_LA_DECISIO_DEL_VERD_2026-08-25.md` — ⏭️ amb
  ARTEFACTE_PERE.psb com a veritat-terra: el que Pere marca és **anomalia
  només-G, només-Vixen** (−14,7·10⁻⁴; R/B/Sony nuls) a 1,42-2,15 R☉;
  l'arbitratge cromàtic a+b=1 l'esborra (−14,5 → +0,3) però el **jutge el
  refusa** (−0,0148): s'emporta corona E (Fe XIV) i l'excés de nitidesa de G
  (focus cromàtic, vist a les parcials). **La tria A/B és de Pere** (§4).

- `103_CURA_DEL_CEL_PER_FOTOGRAMA_2026-08-25.md` — ⏭️ l'execució de les cures
  del 102: **la cura del cel per fotograma a la Vixen APROVADA pel jutge**
  (+0,00305 ± 0,00070; totes les portes PASS; el fusionat candidat = Vixen
  curada + Sony viva, a `output/pilot_vixen_fable_20260825_cura/`); ⛔ la
  mateixa cura a la Sony REFUSADA (treu corona: dos apuntaments amb residus de
  rotació); ⛔ l'anell verd sense curar (el model no passa els seus controls);
  el gra fi λ<31 px fora de la banda curable. Quatre versions del disseny,
  les tres primeres tombades pels seus propis números.
- `102_NI_FUSIO_NI_MOIRE_EL_CEL_I_UN_ANELL_VERD_2026-08-25.md` — ⏭️ **canvia el
  marc dels artefactes residuals: el que Pere veu NO és la fusió HDR.** El
  control aparellat pel SOSTRE (0,85 → 0,60 mou totes les fronteres i cap corba
  visible no es mou; el 74-91 % de l'amplitud «de frontera» persisteix) ho
  decideix. Dues famílies noves: **cel per fotograma** (bandes i estries de
  transparència de 0,10-0,50 % rms que es mouen amb el vent — la «malla»; la
  hipòtesi de l'escaquer CFA queda refutada) i **un anell verd instrumental a
  ~1,85 R☉** (només canal G, només Vixen, a cada fotograma cru; PRNU, foscos,
  flat i sostre exculpats; hipòtesi de ghost pendent). El residu genuí de fusió
  queda acotat a 0,01-0,15 %. Mesures a `output/pilot_vixen_fable_20260825/`.
- [99 — El pilot de la Vixen executat, i les portes reformulades](99_PILOT_VIXEN_LDIC_EXECUTAT_2026-08-23.md):
- `100_FLATS_INVERTITS_I_ANELLS_DEL_PERFIL_RADIAL_2026-08-24.md` — **§E: els arcs
  que Pere va marcar en groc i en lila.** Són artefactes i tenen **dues** causes:
  les **costures de fusió**, que segueixen isofotes i venen d'un desacord entre
  esglaons d'exposició de **1,1-1,3 % amb el signe alternat** —la R6 fa dues
  escales de 2 EV entrellaçades a instants diferents i la transparència va caure
  un **8 % durant la totalitat**—, i **anells realment circulars** del 0,13 al
  0,41 % que surten del **Savitzky-Golay del meu propi perfil radial** (es mouen
  amb la finestra i cap finestra no els mata). ⛔ Hi ha la **retractació d'un
  «60 σ»** que vaig declarar i que els meus propis controls desmenteixen: quatre
  isofotes que NO són frontera donen els mateixos 2,7-3,8 σ. Cura als dos trens:
  ajust de transparència per fotograma amb gauge que **no toca l'escala
  absoluta**, i **segona passada NRGF després de l'ACHF**. Tres portes noves
  (H1/H2/H3), i el deute de captura per al 2027 a `CLAUDE.md` §1 quater.
  I els 28 flats
  amb el cos girat 173,5° validen el flat radial de la Vixen (2,2-3,4 % de la
  seva amplitud entre dos cels independents), promocionen l'EVEN180 i confirmen
  la quarantena del SMOOTH2D; l'eix òptic queda declarat no mesurable amb flats.
  I les quatre causes dels anells amb dents de serra de la fase 3, que valien el
  54 % del detall declarat, més el colze de la rampa de saturació.
  **CANÒNIC del pilot.** El compost LDIC dels 68 fotogrames al llenç comú
  (7686 × 8378 px, nord amunt, B/B☉): passen F1, F, E, E2, G i el rectangle, i
  F0 passa 5 dels 6 anells —la fotometria es declara fins a 3,2 R☉—. Reformula F0
  i F1, que tal com estaven escrites **no les podia passar cap dada de la
  Vixen**. Tres troballes: els temps d'exposició del manifest són els nominals
  del menú i el cos fa una escala binària (**fins a −6,25 %**); el `sol_x` del
  manifest **no és una mesura** i està 3,65 px fora del limbe; i el nivell de
  blanc efectiu **no és 16383**, o sigui que la màscara dura de saturació no
  atrapa res. §8 hi afegeix la Sony, §9 **rectifica** el centre —el bo és el de
  l'efemèride, i el limbe hi està 8,0 ″ desplaçat als DOS trens per igual— i
  **§11 troba la causa de tot plegat: més enllà de 2,41 R☉ el compost és CEL**
  (a 5 R☉ el cel val 9,2× la corona), l'anivellament només l'iguala sense
  treure'l, i els dos trens discrepen 1,1384 sobre la corona i 1,0824 sobre el
  cel — perquè no tenen el mateix espectre. Documenta que la porta **G no té dents** contra un graó de fusió
  i afegeix la **E2**, que sí que en té
- `101_LA_SONY_SENSE_COHERENCIA_I_ELS_FILTRES_2026-08-25.md` — ⛔ **la fase 3
  de la Sony no havia fet servir mai el compost amb coherència**: dos llocs
  construïen el sufix a mà i tots dos es menjaven el `_coh` (costures del tren
  92,6 % → **7,98 %** en arreglar-ho). ⛔ El **flat queda descartat** com a causa
  de la dependència amb el nivell (`flat=no` la deixa igual, correlació 0,984) i
  la **no-linealitat del pou també** (el signe alterna): són **ofsets per
  esglaó**. ⏭️ `PILOT_SOSTRE` **es queda a 0,85**. L'arc verd de Pere **no té
  component circular** (mediana per anell ≤ 0,008 % als dos trens). Filtres de
  Brno nous —passa-alt, desenfoc radial i azimutal, NRGF, FNRGF, MGN, WOW,
  NAFE— i el projecte de Photoshop dels dos trens.
- [98 — Preflight de Codex, fail-closed](98_PILOT_VIXEN_PREFLIGHT_FAIL_CLOSED_2026-08-23.md):
  auditoria d'entrada del pilot, amb tots els números exactes (verificats un per
  un). Va deixar el pilot bloquejat per F0 i F1; el `99` explica per què aquelles
  dues portes eren impossibles i les substitueix. Segueixen vives les seves dues
  troballes: **replicar la vora del fosc costa fins a 64 ADU a 10 s** i el
  `+1,019/R²=0,981` **és de la Sony**
- [97 — Les dues decisions del 23-08](97_DECISIONS_VIA_FOTO_I_PILOT_VIXEN_2026-08-23.md):
  **CANÒNIC.** (D1) es va per la **via de la FOTO** de Druckmüller ajuntant els
  dos trens, i ⛔ **el producte fusionat NO és una mesura** —amb `k(φ)` lliure,
  l'acord entre trens s'hi ha imposat—; (D2) **pilot d'una sola tirada amb la
  Vixen** al llenç comú. Hi ha el preu de cada decisió, què queda ajornat, què
  caldria si algun dia es vol la mesura, i què va canviar el contrast amb Codex
  i cinc llinatges externs (entre altres: el **«0,662″ al limbe» era fals** —és
  HIP 46345 a 2,646 R☉— i **la porta E es podia falsejar** amb `k(φ)` lliure).

- ⏭️ **Traspàs viu de la reestructuració:**
  `.coordination/HANDOFF_2026-08-23_REESTRUCTURACIO_PER_FASES.md`. Contracte de
  les quatre fases (**0 Calibració · 1 Registre · 2 Composició LDIC · 3 Filtres**,
  més rebuts), amb les quatre esmenes a l'esborrany de Pere i els números que
  les sostenen. ⛔ **Res implementat.** Tres coses que hi canvien el disseny: el
  pla tangent ha de ser **aparent** i les estrelles s'han de mesurar fotograma a
  fotograma (un registre per semblança deixa 0,561″ rms = **0,85× el senyal GR**);
  **`.apparent()` de Skyfield ja aplica la deflexió** i per això el residu de
  placa no la pot contenir; i **el camp d'extinció no està calibrat** (k=0,402 es
  va mesurar sobre ΔX≈0,13 i s'extrapola a X=4,3–10,2, i els dos trens
  discrepen 2,1–2,7σ).

- [96 — El camp de la Sony va caure: dos apuntaments, no un](96_SALT_DE_MUNTURA_I_ORDRE_NOU_2026-08-23.md):
  **DOCUMENT CANÒNIC.** Troballa de Pere: la muntura va patinar **750 px
  (−233, +713)** a mig de la totalitat i els 10 fotogrames apilats són a **dos
  apuntaments** (13,50 s i 11,25 s). D'una sola causa en surten les «zones de
  cobertura» (78,34 % amb els 10), la costura de `y = 4578`, el graó
  **multiplicatiu** (el mateix cel a dues posicions del sensor = vinyetatge) i
  el fotograma de 8 s perdut (`DSC06990`). El llenç no aguanta la unió i es van
  llençar **697 px** en silenci. **I el salt és un dither que pot mesurar el
  flat de `research/90`.** Conté també què fa de veritat l'equip de Druckmüller
  —l'**LDIC** amb la seva fórmula, els pesos pintats a mà, i la rectificació
  que «cosits» del `research/82` §1 és inferència nostra— i **l'ordre nou del
  projecte en quatre fases**, consensuat amb Pere i pendent d'acabar.

- [95 — Els dos artefactes del pas alt: causa mesurada i correcció](95_PASSALT_ARTEFACTES_CORREGITS_2026-08-23.md):
  ⛔⛔ **Hi ha la NORMA DEL RECTANGLE, que val per a qualsevol filtre**: un
  filtre s'aplica a TOT el rectangle de la imatge, mai a una circumferència, o
  queden halos; l'única cosa que el pot aturar és que no hi hagi dada, i si
  l'exterior surt lleig es repara aigües amunt, mai retallant un cercle.
  **Pere va marcar dos artefactes damunt del pas alt v12 i cap dels dos era del
  pas alt.** El vermell: el compost lineal anava multiplicat per **`validesa²`**
  —comprovat exacte a quatre decimals— i el `max()` que la defineix té cantonada
  a 2,5 R☉: el factor valia 0,56 a 2,4 R☉ i 1,00 a 2,6. Contrafactual: el rms a
  2,476 R☉ passa de **0,6404 a 0,0450**. L'ocre: la rampa exterior era un `clip`
  lineal que acabava **exactament** a 6,505 R☉, i una textura que s'atura deixa
  vora encara que la mitjana no canviï. Pel camí, dos defectes més: **el control
  de costura era fals** (85 % de zeros exactes → «0,000 σ» sempre) i **el
  pedestal per zona era una funció esglaonada** (24,75 s → 13,50 s en una fila
  a y=4578). Tres comprovacions noves —**E** perfil radial monòton, **F**
  compost ≡ mescla, **G** envolupant isotònica decreixent— i totes tres saben
  fallar: G dona ×2,105 sobre la v12 i ×1,149 sobre la v22. Rectifica també una
  troballa meva: alimentar el filtre amb el cel dins era un **guany**, no la
  causa que es morís l'exterior.

- [94 — Pas alt de la corona](94_PASSALT_CORONA_2026-08-23.md):
  **reapilat Sony v3 (reprodueix el publicat: correlació 1,000000, p99 de la
  diferència 0,011 %) i filtre de pas alt en escala de grisos, sense Lluna ni
  protuberàncies.** Bandes log-polars en graus, Wiener amb el soroll mesurat de
  les dues meitats de l'apilat, convolució normalitzada i finestra per distància
  a la vora. ⚠️ **Els «0,000 σ» de les costures que aquest document declara són falsos**:
  el control estava trencat i `research/95` §4.1 ho documenta. Sigmoide de
  fusió **0,105 σ** sí que era real. Dos errors propis
  trobats mesurant: **doble emmascarament** (fabrica una vora que es MOU amb la
  màscara) i un **gate de cobertura llegint un pes suau** (apagava d'1,2 a
  2,7 R☉). Queda un contorn a **2,475 R☉** que NO es mou amb la màscara i que
  no s'ha tapat.
- [93 — Catàleg d'artefactes de composició](93_CATALEG_ARTEFACTES_COMPOSICIO_2026-08-23.md):
  **els sis artefactes que Pere veu al compost, mesurats, amb la causa i la
  regla per no repetir-los.** Regla mare: cada màscara ha de mesurar allò que
  diu que mesura. (A) escaló rectangular = l'apilat Sony v3 només té cobertura
  completa al 78,3 % del llenç i ningú no llegia el mapa de pes → pedestal per
  zona, escaló a 0,37 σ; (B) anell de color a 2,8 R☉ = igualar una sola
  mediana de luminància quan els quocients per canal són R 2,143 · G 2,605 ·
  B 3,059 → guany i pedestal per canal, variació de color 108 % → ≈30 %;
  (C) gradient de cel = vinyetatge, i la seva correcció és el flat abans de
  l'apilat, no una quàdrica després; (D) el que tapa el Sol és la Lluna, disc
  1,019 R☉; (E) **mai `distanceTransform` sobre un mapa de cobertura** — el
  forat de la Lluna i els de saturació es tornen vores i la corona interior
  sortia ×0,03 a 1,05 R☉, defecte que la recepta Gemini també té; (F) les
  estries de 1,05–1,6 R☉ són a `hdr_vixen_countss.npy` mateix. Stack lliurat
  en B/B☉ float32 a `output/stack_calibrat_20260822/20260823T0130Z_v8/`; les
  regles queden a `postprocessat-corona/references/trampes.md`.
- [92 — La branca Druckmüller amb el registre corregit](92_REGISTRE_DRUCKMULLER_CORREGIT_2026-08-22.md):
  **rectifica `91` §2.4 i arregla el defecte de veritat.** El centre
  `(3479, 2319)` **no era cap error**: `hdr_vixen_countss.npy` està construït
  amb el Sol al centre exacte i ho diu el seu propi LLEGEIX-ME. El defecte és
  que la matriu `M` de Gemini està ajustada amb estrelles de la **graella del
  sensor** i s'aplica a la matriu HDR, que viu en una graella desplaçada
  **(+89,775, −48,647) px** (19 estrelles, σ 0,25/0,13): la capa Vixen queda
  desregistrada **68,8 px = 0,230 R☉** respecte de la Sony. La matriu nova surt
  de compondre les dues solucions de placa (22 i 38 estrelles) pel pla tangent
  al Sol; escala i rotació no canvien, només la translació. Validat de manera
  independent amb el limbe del disc lunar: **69,06 px → 0,28 px**. Build A/B
  `20260822T2130Z_registre` amb els quatre màsters de la recepta original més
  el compost lineal float32. Continua `EXPERIMENTAL_NOT_CANONICAL`: les
  entrades són apilats històrics i l'apilat Sony v3 ja fon `DSC06987` amb
  `DSC06993`.
- [91 — Auditoria del 22-08 al vespre: els traspassos i l'estat real del disc](91_AUDITORIA_TRASPASSOS_I_ESTAT_2026-08-22.md):
  **la cadena de rebuts del 22 aguanta —319/319 Vixen, 335/335 Sony, els nou
  hashes de coordinació, els originals invariants i la preservació Gemini—,
  però hi ha set troballes altes.** Les tres de preservació: 273 GiB
  d'autoritat material sense cap còpia i amb `output/` fora del `.gitignore`;
  el run canònic de l'eclipsi viu a `~/Library/Application Support/` i cap
  document viu no en dona la ruta; 20,92 GiB, inclosa la maqueta, solts a
  `~/Downloads`. La tècnica: la branca Druckmüller té la capa Vixen
  desregistrada ~69 px (0,23 R☉) respecte de la Sony ⚠️ **la causa que dona
  §2.4 —el centre solar— està RECTIFICADA a `research/92`: el centre és bo i
  el que falla és la graella del warp.** I tres de risc: deu JSX poden mutar el PSB obert, vuit scripts fan `append`
  sense idempotència sobre un document viu, i les rutes d'origen dels dos
  paquets S6 apunten a carpetes anteriors a la reorganització (68/68 i 32/32
  íntegres a la ruta viva, però el `PASS` del rebut no es pot reexecutar).
  Setze agents, només lectura, catorze troballes refutades pels contrastos.
- [90 — Màsters flat posteriors Vixen i Sony](90_MASTERS_FLAT_POSTERIORS_VIXEN_SONY_2026-08-22.md):
  **178/178 RAW únics acceptats i màsters lineals CFA4/FITS nous, sense tocar
  S6.** El PRNU fi Vixen coincideix entre èpoques (`r=0,894–0,921`) i millora
  un null independent: validat, encara no aplicat. El perfil radial Sony
  coincideix amb el donor S6 (`r>0,999995`, p95 0,16–0,55%): validat, encara
  no aplicat. Full 2-D i pols dels dos trens queden en quarantena; el PRNU fi
  Sony no passa r≥0,8. Els 106 JPEG de flats s'han mogut a un lot recuperable
  de la Paperera, amb zero JPEG a origen i els RAW invariants.
- [89 — Recerca futura: dues targetes Sony amb RAW i JPEG separats](89_RECERCA_FUTURA_DOBLE_TARGETA_SONY_RAW_JPEG.md):
  **pregunta oberta, no implementada ni qualificada.** Cal comparar en el
  mateix cos RAW+JPEG a l'Slot 1 contra RAW a l'Slot 1 i JPEG a l'Slot 2, amb
  manifests per targeta, integritat ARW, cadència sostinguda, pitjor temps de
  drenatge i absència de pèrdues. Als A7III/A7RIIIA només l'Slot 1 és UHS-II,
  de manera que el segon slot UHS-I pot ajudar, no canviar res o alentir; no
  es modifica la recomanació ni cap perfil actual.
- [88 — CapesTotals V4: la normalització desencalla la cadena sencera (12→01)](88_CAPESTOTALS_V4_NORMALITZACIO_2026-08-21.md):
  **evidència històrica preservada, no fonament acceptat:** V4/V4b passen la porta de costura
  G5.10 i la verificació reoberta, però fallen cobertura G5.11. Els scripts `05/06/07/10` ara
  fallen tancat i els rebuts històrics sense segell explícit no són promocionables. Revelats
  normalitzats offline (ACR scriptat no dona 16 bits a PS 27.9.1; renderer
  propi amb DNG Converter + rawpy, RENDER_RECEIPT per capa, t_ref = 1/15 s, 01 a 10,08 s
  fotomètric). q entre veïnes 1,00 ± 0,05 (V3c: 2,0–3,9). Validesa re-calibrada: plateau de
  saturació + SNR. §5.3 contra el màster calibrat: FORA del ±10 % (+14 % extern, +23 % intern),
  descomposat: ~11 % de divergència d'escala absoluta PREEXISTENT entre els apilats HDR4 i el
  màster de research/76 + cel no restat + excés intern pendent. Decisió d'ancoratge absolut,
  de Pere. V3c congelada com a checkpoint; no s'hi ha tornat.
- [87 — Auditoria del 21-08: les dues skills, CapesTotals V1→V13, Antigravity i el bloqueig d'ID8](87_AUDITORIA_SKILLS_CAPESTOTALS_ANTIGRAVITY_2026-08-21.md):
  **només lectura, 8 lectors + 8 verificadors adversaris amb `psd-tools`.** Cap CapesTotals del disc té
  rebut vàlid: V2 va ser re-desat a mà per Pere a les 02:02 (visibilitats, opacitat de la 01 i màscares
  canviades) i V3…V13 d'Antigravity es descarten (V13 renta la Lluna amb la 10,3 s al 33 %; el «Sant
  Greal» no es va executar; V10–V12 no van canviar res). La «torre de Pisa» de la capa 01 és real
  (+1,4, −0,9 px per estrelles) però ve de la col·locació al llenç del 18-08, no de l'apilador; les
  1/500 i 1/125 van a (458,464), un píxel fora de la cadena. El rebuig d'ID8 es reprodueix i els tres
  mínims fan 0,08/0,11/1,19 % amb un terra de 8 DN: és un encreuament de pesos no normalitzats que una
  transició de σ 24–96 px esborra; V1 passava per la capa compensadora VORA. Skills: la cadena
  d'astrometria no arrenca, `Corona_HDR_Vixen` no és al disc, l'apilatge decideix el soroll que
  `85` deixa obert, la regla de llenç/FOV és incoherent i falta una porta de re-derivació de màscares.
  Repositori: 136 fitxers tracked de `runs/` esborrats, 25 commits sense remot, 12,3 GB no ignorats.
  Respon les deu preguntes del `Skill_ECLIPSE.docx` i llista les vuit decisions que són de Pere.
- [86 — CapesTotalsV1: la unió de l'HDR interior (V5) amb l'exterior i els filtres](86_CAPES_TOTALS_V1_UNIO_INTERIOR_EXTERIOR_2026-08-20.md):
  **rebut històric de matinada, no vigent per al save actual.** El PSB del path
  de lliurament es va tornar a desar després: ara té 36 capes, 2.370.519.442 B,
  SHA-256 `4d0480f1d6508c225f5dbb13fb5c4e608d35a07b58acc2625853284ba48f2a28`
  i no conté `EDITAT PERE`, mentre que el rebut descriu 37 capes, 2,98 GB i
  `f0ce3e8bf2606cf1…`. Cal re-QA abans d'usar-lo com a lliurament. El document
  conserva a continuació què demostrava el fitxer de matinada:
  el projecte únic amb TOTES les capes (les 12 de la V5 + la cadena exterior de CapesExteriors amb
  porta radial 1,35→1,95 R☉ + els 15 filtres de la SEMIFINAL10 tal qual), possible per tres
  equivalències: `Aplicant_Filtres.tif` == compost de CapesExteriors (≤3/65535), benchmark ==
  SEMIFINAL10, i el compositor extern == Photoshop (màx 11/65535, amb la trampa de la **cobertura
  del bbox**). Les màscares de 04/03 s'acaben per ordre de Pere (el vel del fotograma d'1 s era la
  causa de les **bombolles del limbe**: discos lunars dels apilats transparentant-se) i tres capes
  radials noves (VORA lunar-cèntrica al nivell del benchmark des de 452 px, PONT i PERFIL) tanquen
  el fossat que el panell extern (Codex/Opus/Gemini/Grok) va declarar artefacte. Perfil lunar final
  dins ±3,8 % del benchmark (468–708 px), sense mínims locals. Codex: APTE; els dos bloqueigs
  d'Opus són contingut V5 heretat, desmentits amb els seus propis tests (§5). Codi:
  `tools/capes_totals_v1/`.
- [85 — Quant soroll admet una capa per entrar a un apilat?](85_QUANT_SOROLL_ADMET_UNA_CAPA_PER_APILAR_2026-08-20.md):
  **fil obert, només preguntes** (Pere, 20-08). Fins avui cap capa no s'ha exclòs mai d'un apilat
  per soroll —la 06990 i la 06988 van fora per **salts i traços**, i la 06991 hi és amb 11 px de
  trailat (`83` §9.2)—, el pes és sempre l'exposició, i la porta de soroll que sí que existeix
  (`82`; `83` §8, §9.6) decideix quina **estructura** és real, no quin **fotograma** és admissible.
  Amb el «denoise suau a les fraccions de segon» de `84` ja aplicat, el criteri de facto ja és
  post-denoise i no consta enlloc. Set coses per definir abans de respondre: soroll per anell o per
  fotograma, vàlida per a què, llindar contra pes per variància inversa, què vol dir «poc
  agressiva», de quin costat de la porta va el denoise, la correlació que hi introdueix, i què fer
  quan el que limita és el cel i no els fotons. Eina: les **meitats A/B** (σ real, validada al
  96–99 %).
- [84 — CapesInteriorsV4: màscares netes per a l'HDR interior de Photoshop](84_CAPES_INTERIORS_V4_MASCARES_RADIALS_2026-08-19.md):
  les màscares de V3 (contorns de lluminositat + pinzell) modulaven la brillantor un **±10–18 %
  per azimut** a 1,05–1,5 R☉ (+40 % al forat coronal vora el limbe) i deixaven l'estructura real a
  0,34–0,82 del seu contrast. V4 final (decisió de Pere: «prefereixo la V3, manen les capes
  inferiors»): **les mateixes màscares de Pere promitjades per anell** (radials: cap estructura),
  cascada de protecció al creixent i la protuberància (1/125 cremada → 1/500; 1/500 cremada →
  les perles de la 1/3200), disc lunar → 1/3200 (Lluna negra), Capa 4/5 retallades al marc i tot
  a la geometria del 18-08 (V3 era a +1,+1 px d'Exteriors). Perfil = V3 ±7 %, anells 0,18 % rms,
  correlació amb les capes soles 0,986–0,998. El primer disseny (radial de nou encuny, altiplà +
  Color Dodge, contrast 1,0) està documentat i conservat com a referència. Codi a
  `tools/capes_interiors_v4/`.
- [83 — El flat artificial del camp i FiltresSEMIFINAL3.psb](83_FLAT_CAMP_I_SEMIFINAL3_2026-08-19.md):
  la base de Pere corregida contra la **lluminància calibrada dels dos trens** (LUT + guany per
  anell; el que sobra és artefacte): arcs de màscara a 8,6 i 10,3 R☉, caixa Vixen, triangles del
  marc Sony, costura polar a x = x_Sol i gradient del cel, sense cap graó radial nou (la part suau
  no entra fins a 5–6,5 R☉ per no tocar l'halo de color ni fer colze; les vores dures des de 3,5);
  capes «camp net» dels tres filtres actius i tres prototips (Espenak multiescala, ACHF-lite
  isòtrop, Espenak ampli). Codi a `tools/filtres_druckmuller/{flat_camp,capes_semifinal3,construeix_semifinal3}.py`.
  **§6, el HALO → `FiltresSEMIFINAL4.psb`**: era un genoll de la corba de to (terra dur del blau a
  L<356 = 5,6 R☉) sobre corona K+F real (1,9·10⁻⁹ B☉ a 5 R☉); els DBE de PixInsight (ABE grau 4,
  GraXpert) eren radials centrats al Sol i s'emportaven el 60–100 % de la llum. Correcció:
  envolupant inferior per anell en L (p25, rampa C2 3,2→5,5 R☉) + corba sense terra + terme radial,
  sense baixar mai del cel, protuberàncies intactes (`halo_uniforme.py`, `construeix_semifinal4.py`).
  **§7**: apilat Sony v2 de 13 fotogrames (+1,5 % de SNR: els curts no porten fotons) i capa DETALL
  EXTERIOR per coherència Vixen–Sony amb control nul (`detall_exterior_v2.py`) → `FiltresSEMIFINAL5.psb`;
  Codex + Gemini + Grok: halo 0–1 a la SEMIFINAL4/5 contra 2–3 a la de Pere. **§7.5**: cel blau-gris
  (mateix to, saturació 0,53 → 0,32) → `FiltresSEMIFINAL6.psb`. **§8, els filtres profunds →
  `FiltresSEMIFINAL7.psb`**: RADIALS (Espenak multiescala), MGN i NRGF calculats sobre la referència
  profunda (Vixen HDR + Sony v2 ≥ 1/8 s) **amb el flat del 300 mm tornat a posar** (la costura havia
  deixat la combinada amb la vinyeta sense flat del Vixen: +2 % a 8,5–9 R☉) i fons de Fourier per anell;
  porta de soroll entre trens, mitjana zero per anell, bandes amples esvaïdes abans (a 7 R☉ 9° són 500 px,
  l'escala de les incerteses de flat/cel) (`filtres_profunds_v7.py`, `construeix_semifinal7.py`). **§9 →
  `FiltresSEMIFINAL8.psb`**: apilat Sony v3 (els 10 fotogrames > 1/8 s amb meitats A/B; la 06988 cau per traços),
  l'HDR del Vixen ja és la pila de llargues (93 % del pes ≥ 1 s a r > 4); la costura σ 200 tenia biaix de vora (sot
  −0,1…−0,2 % a 100 px: poly4 + residu i correcció de la vora del Vixen → 0,00); porta de soroll real i local de les
  meitats, cap taper de caixa, tot acabat a 8 R☉; les capes velles de Pere netes (el v2_40 fosc als triangles era la
  causa dels cantons); test d'acceptació `sf3/v8/qa_capes.py`. **§9.6 → `FiltresSEMIFINAL9.psb`**: cap tall radial
  («cada píxel compta»): porta per coherència entre les meitats de la Sony per grup de muntura (desplaçades 713 px: el
  fix al sensor es mou, el cel no), NRGF amb anells parcials (`filtres_profunds_v9.py`).
- [82 — Filtres «Druckmüller» per a la corona externa: lectura dels papers, els filtres de Pere, i les capes dels dos trens](82_FILTRES_DRUCKMULLER_CORONA_EXTERNA_2026-08-18.md):
  **lectura d'implementació dels 55 papers** (l'ACHF amb fórmula és el nucli en (Δr, arc)
  de la tesi §5.2, la porta de soroll és el criteri —només WOW i NAFE en tenen—, i per a
  alçades grans la mateixa Brno diu FNRGF/NRGF, normalitzar per anell); els filtres radial
  i tangencial d'Astrofalls de Pere llegits amb Druckmüller (cecs a les tangencials, fase
  a tot el rang, en color); i **11 capes de detall al llenç 7648×5353 fetes amb els dos
  trens alhora** (HDR Vixen + apilat Sony ≥ 1 s aparellat i registrat per la corona,
  σ combinada 0,75 la de la Vixen), en log-polar amb porta de significació per banda,
  variant additiva (jerarquia conservada, γ < 1 del Corona) i blanquejada per anell
  (FNRGF), porta de coherència entre trens. **La coherència Vixen–Sony per banda a
  3,6–5 R☉ diu quines escales són reals: 0,35 a 0,44–0,71°, 0,71 a 0,71–1,16°, ≥ 0,88 a
  partir d'1,16°**; correlació global 0,926. Codi `tools/filtres_druckmuller/`;
  lliurables a `Projecte photoshop/2-Filtres/Druckmuller_2026-08-18/`; lectures a
  `data/lectures_druckmuller_2026-08-18/`.
- [81 — El tutorial d'Astrofalls, pas per pas, i el seu encaix al projecte](81_TUTORIAL_ASTROFALLS_POSTPROCESSAT_CORONA_2026-08-18.md):
  **el flux d'edició sencer del curs d'Astrofalls** (Vimeo 904827483, 1 h 44 min),
  distil·lat del dataset d'un eclipsi **a prop del màxim solar** —el mateix règim
  que el 12-08-2026: corona de llaços, no de plomalls—. És un flux **estètic** de
  Photoshop (no conserva fotometria), o sigui que alimenta el lliurable WOW, no el
  compost calibrat. Tres coses que aporta: **(1) treure el gradient de color
  atmosfèric** —DBE de PixInsight o el truc Color/Subtract + re-injecció del blau
  per Screen—, que **resol directament el «gradient circular concèntric de colors»
  del `NoEncaixa.tif`** de Pere (`research/80`), i la corona neta surt lleugerament
  verda; **(2) blur MOLT més fort a les màscares HDR** —tot anell és subblur, creix
  10→400 px cap enfora—, rellevant al graó HDR del Vixen; **(3) al màxim solar el
  path blur és inútil, mana el filtrat tangencial (zoom), radis radials petits, i
  hi ha vermell per tot el limbe i una CME a les exposicions llargues**. Segon cop
  que Astrofalls entra al projecte (el primer és `research/68`). Transcripció
  verbatim a `81A_TRANSCRIPCIO_PRIVADA_ASTROFALLS_ECLIPSE_VIDEO.md` (material
  privat, exclòs de qualsevol exportació pública).
- [80 — Encaix de la capa Sony 300 mm al compost de Photoshop, i les estrelles mogudes](80_ENCAIX_CAPA_SONY_AL_COMPOST_I_ESTRELLES_2026-08-18.md):
  **l'anell de colors del `NoEncaixa.tif` de Pere no era la màscara, era la capa**:
  la Sony cremada fins a 3,25–3,75 R☉ amb el rim taronja/verd de la saturació per
  canals, i 2–3× més clara i càlida que la Vixen a tot radi. Encaix per LUT de
  quantils per canal + residu de baixa freqüència (σ 80 px) restat, Vixen dins la
  zona cremada (fit − Vixen ≤ 0,07 % per anell); 31 estrelles amb traça de 25″ a 47°
  arrodonides amb el mateix flux; detall exterior en bandes angulars al domini estès
  amb component d'anell zero (≤ 0,03 %). L'enfosquiment de vora de la capa Vixen
  (la meitat a les últimes 300 files) i les dues variants de capa. §7–8: l'apilat
  Sony ≥ 1 s posat al llenç, el halo del creuament de color, el detall tangencial.
  **§9 (tarda): el FE 300 mm f/2,8 GM a f/2,8 vinyeta −1,5 EV al cantó (0,70 a
  10 mm) i hi havia flat a l'Escriptori sense fer servir**; el `.lcp` de `75` es
  queda quatre vegades curt; l'apilat aplanat coincideix amb la Vixen lineal a ±1 %
  de 4 a 8,8 R☉ (la Vixen no vinyeta al llenç); la capa Vixen de Pere és una corba
  de to global excepte rampes de ~700 px a dalt (×0,61) i a la dreta (×0,54).
  Perfil del flat a `tools/encaix_sony/flat_sony300_f28_perfil_radial.csv`. Codi a
  `tools/encaix_sony/`; lliurables a `~/Downloads/Encaixada_2026-08-18/`. **§14 (vespre):
  els filtres de pas alt de Pere (tres llenços diferents) i els del pipeline, tots al llenç
  E de 7648×5353** (Tangencials + (456, 462), radials + (599, 549), reixa del pipeline
  + (542,6, 418,5) ± 0,1); `a`, `b` i `radial A` van invertits; codi a
  `tools/capes_photoshop/`, lliurable a `Projecte photoshop/2-Filtres/`.
- [79 — Validació dels passos del postprocessat de la corona, abans de la skill](79_VALIDACIO_PASSOS_POSTPROCESSAT_2026-08-17.md):
  **l'auditoria del 17-08 al vespre de tot el postprocessat fet** (71–78, les
  eines, dotze sessions de xat i els seus scratchpads), pas per pas contra la
  llista de nou passos que Pere creia fets. ✅ Correctes: eines, deriva,
  placa i efemèrides Sol–Lluna (registre al Sol, mai a la Lluna). ⚠️ A mitges:
  relativitat —σ(ε)=0,53 és forecast de Fisher, no detecció mesurada—;
  l'extinció (k = 0,402) només és a l'HDR4 i
  no al compost; la refracció està mesurada i no es corregeix enlloc; el filtre
  viu és `detall_logpolar` (DoG en graus, additiu sobre la pantalla), no
  l'ACHF; l'apilat només és del Vixen (**la Sony no està composta**); no hi ha
  drizzle 2× possible (ditherat 1-D) i les perles d'abans de C2 no s'han apilat.
  Els dotze passos que falten, per ordre, i el disseny de la skill.
  Productes de la mateixa sessió: la skill **`.claude/skills/postprocessat-corona/`**
  (SKILL.md, `references/{pipeline_vixen,constants,trampes}.md`,
  `scripts/{comprova_entorn.py,pipeline_vixen.sh}`) i el rescat al repositori
  del codi que només vivia als scratchpads de `/private/tmp`
  (`tools/rescat_scratchpad_2026-08-17/ORIGEN.md`: placa i estrelles, deflexió
  i APOD, diagnòstics de l'HDR, halo sense LROC, JSX de Photoshop). I, a
  petició de Pere el mateix vespre, **la cadena d'astrometria sencera promoguda
  a `tools/astrometria/`** (predicció → detecció cega Sony/Vixen → creuament i
  placa → fotometria absoluta → escèptic → deflexió → APOD; `comu.py`,
  `pipeline_estrelles.sh --prova`, `test_acceptacio.py`, `MAPA.md`), provada
  d'un sol cop des dels RAW en 11 min amb 22/22 números d'acceptació dins
  `_prova_skill_estrelles` i els catàlegs byte a byte idèntics als del 16-08.
  El path live actual no conserva 18 intermedis de `Estrelles/_work`: per
  defecte el test només pot comprovar 4/22 línies.
- [78 — HDR4: apilats per exposició del Vixen, i l'extinció dins de la totalitat](78_APILATS_HDR4_VIXEN_I_EXTINCIO_DINS_TOTALITAT_2026-08-17.md):
  **la selecció HDR3 de Pere amb la corona apilada.** Nou DNG lineals que
  apilen tots els fotogrames de la mateixa exposició de dins la totalitat (26
  en apilats de 2–4), registrats a la corona amb el model de `Corona_HDR_Vixen`
  i tots en una mateixa geometria (el Sol al lloc de 572A2969: alineats entre
  ells a ≤ 0,08 px); els tres CR3 de contacte i curts, tal qual
  (`~/Desktop/HDR4`, eina `tools/apila_hdr4_vixen.py`).
  ✅ Model de registre validat a **≤ 0,09 px** als 17 parells, també al 10,3 s.
  ⛔ **La corona baixa un 5,5 % de C2 a C3, multiplicativament**: el Sol es pon
  (massa d'aire 6,02 → 6,20) i surt **k = 0,402 ± 0,036 mag/massa d'aire**
  (14 parelles, mesura diferencial sense vinyetatge), que confirma el 0,37 del
  projecte i corregeix `research/76` §5 bis, que havia atribuït tota la
  correlació amb el temps al cel. Cada membre es normalitza a la massa d'aire
  de C2+8,4 s i tots els apilats al mateix fons de cel; continuïtat entre
  esglaons ≤ 1 % (1,7 % al pitjor). ⛔ La correlació de fase de la corona s'ha
  de suavitzar (σ = 3 px) i deixar fora les protuberàncies (r > 600 px), o
  surt 0,25 px del model. ⛔ El pou de la R6 III clava a **16382**, no 16383,
  i **Adobe hi posa el blanc a 13995** (= el sostre del 85 %). ⛔ **El mapa de
  PRNU v1 portava les traces de les estrelles** (bonys de +0,04 a +0,135 al
  llarg de la deriva) i deixava clots foscos en diagonal al costat de cada
  estrella i li treia fins a un 10 % del pic: refet amb màscara d'estrelles
  (`prnu_vixen.py` v2), i el compost de `research/76` refet amb ell.
- [77 — Provar la relativitat general el 2027: què caldria de veritat](77_PLA_RELATIVITAT_2027_QUE_CALDRIA.md):
  **el pla per a l'eclipsi del 2 d'agost de 2027**, amb tres revisions
  adversàries que van tombar la primera versió. Per al 2026, σ(ε)=0,53
  (equivalent teòric a 1,9σ) és una **previsió de Fisher, no una mesura**.
  ✅ **La banda honesta per al 2027 és 5-10 %**: detecció a
  3σ pràcticament garantida i Einstein contra Newton a ≥5σ molt probable, el
  ±10 % d'Eddington a l'abast, el ±3 % de Bruns una estirada de debò i res per
  sota del 3 % defensable abans de mesurar el nostre terra. ⛔ **El que mana és
  l'altura del Sol**: de 9,2° a 81,8° divideix la refracció per 41, la
  compressió del camp per 33 i la dispersió per 43, i no costa res. ⛔ **La
  fondària no compra gairebé res**: el 97 % del pes estadístic és a les 177
  estrelles més brillants que V=9. ⛔ **La sèrie nocturna de distorsió a alt/az
  igualat és geomètricament impossible des d'Espanya** (cal latitud 9,6-26,1° N)
  i **no hi ha cap codi de control de muntura a tot el projecte**. El pas que
  ho decideix tot és l'**assaig general del 30 de gener / 15 de febrer de
  2027**, que mesura el nostre terra sistemàtic en lloc d'assumir-lo.
- [76 — Primer HDR de la corona amb el tren Vixen](76_HDR_CORONA_VIXEN_2026-08-16.md):
  **el primer compost HDR del projecte.** 68 fotogrames de dins la totalitat,
  15 exposicions, **15,0 EV**, drizzlejats sobre la reixa crua i centrats al
  **Sol**. ✅ **El perfil absolut surt el K+F de manual sense cap ajust**:
  3,3×10⁻⁶ B☉ a 1,02 R☉ i 1,0×10⁻⁹ a 5 R☉ — la millor validació independent de
  la cadena sencera. ✅ Criteri 2 del G5 superat: continuïtat **0,08 % de
  mitjana i 0,77 % de màxim** contra el 3 % exigit. ⛔ **La corona no deriva a
  la velocitat de les estrelles**: 0,578 ″/s per dos camins independents contra
  els 0,610 estel·lars de `research/75`, i la diferència és el moviment del Sol
  sobre el fons (0,041 ″/s) perquè la muntura anava a taxa **solar**. Alinear
  amb el número estel·lar hauria escombrat la pila 3,4 px. ⛔ **La gota del
  drizzle ha de ser de 2,0 píxels de sortida** —l'única que dona partició de la
  unitat sobre la reixa de Bayer—; per sota surt un escaquer a la diagonal de
  Nyquist i el cost mesurat de fer-la gran és <1 % del senyal real. El límit de
  tot plegat **és el cel**: la corona l'iguala als 3 R☉.
- [75 — Mesures del 16-08: foscos, resolució, guany i calibratge absolut](75_MESURES_16-08_RESOLUCIO_GUANY_I_CALIBRATGE_ABSOLUT.md):
  **evidència mesurada que corregeix el 73 i el 74.** ✅ **Calibratge absolut fet
  als dos trens** amb 38 i 22 estrelles identificades: B/B☉ = 1,134×10⁻¹¹·I
  (Sony) i 2,772×10⁻¹¹·I (R6), ±10 %, **coincidents al 5 %** sobre la corona
  —l'estat de l'art és un factor 2—. **Camp resolt**: nord real a PA 90,27° i
  57,19°, i l'eix nord lunar astromètric (71,97°) **confirma el 71,5° que
  `Earthshine_FINAL` havia ajustat contra LROC sense saber res d'estrelles**.
  ⛔ **No hi havia cap dark dolent**: era un artefacte d'una mètrica cega a la
  imatge. ⛔ **El seeing no era de 4,6–12,2 ″**: sostre mesurat ≤4,0 ″ a massa
  d'aire 6,4. **Resolució real 5,8 ″ (Vixen) i 8,3 ″ (Sony)**, i la Sony ja
  anava tova mitja hora abans de C2 **amb el filtre posat** —cau la culpa del
  filtre—. **Guanys 5,08 i 3,41 e⁻/ADU**; les protuberàncies van a 257:1 i les
  limita la PSF, no els fotons. Cada **pla de Bayer va submostrejat 1,7×** i la
  deriva de la muntura és el ditherat que un drizzle necessita.
- [74 — Pla aplicat de postprocessat de la corona](74_PLA_APLICAT_POSTPROCESSAT_2026-08-15.md):
  el pla d'obra, gate per gate, amb números concrets i criteris objectius de
  pas. **La v1.1 corregeix la v1.0 en tres punts grossos:** el model de halo
  **ja existeix i està validat** a `Earthshine_FINAL/` (r=0,68/0,73 contra
  LROC WAC), o sigui que el G3 és reajustar-lo i no descobrir-lo; el **G0 només
  cobreix 322 fitxers de 3.650** (falten `Vixen/`, el 6D sencer i les dues
  carpetes HDR); i **no s'ha de desbayerar** —superpíxel 2×2 amb els quatre
  plans—. Hi ha una **porta nova, el G7**: estrelles, resolució astromètrica
  i dades externes del mateix dia (LASCO C2/C3, K-Cor, Predictive Science),
  que és l'única validació que no comparteix atmosfera, lloc ni operador.
- [73 — Assessorament científic de postprocessat de corona](73_ASSESSORAMENT_CIENTIFIC_POSTPROCESSAT_CORONA_2026-08-15.md):
  la referència de mètodes. Qui és qui a l'escola de Brno i qui ha vingut
  després; la cadena sencera de filtres —unsharp radial, ACHF, NRGF, FNRGF,
  MGN, WOW, RHEF— amb **les fórmules exactes**, els paràmetres publicats i què
  destrueix cadascun; l'alineació per correlació de fase pas a pas amb les
  seves errates; el que va abans del realçat (linealitat, foscos, camp pla,
  HDR lineal, model de halo); i la fotometria de validació (K+F+E, Baumbach,
  van de Hulst, calibratge absolut a la manera Bemporad). ⚠️ Porta **set
  correccions** que van sortir d'una fase adversarial i tenen prioritat sobre
  el cos del document: entre altres, que l'equació de compensació de soroll
  del FNRGF publicada a l'ApJ **la repudia la seva pròpia autora**, i que la
  prova unitària que el mateix paper proposa **és falsa**.
- [72 — Skywatcher: dos salts a mig de la totalitat i el misteri de l'àncora resolt](72_SKYWATCHER_SALTS_I_ANCORES_SONY_2026-08-15.md):
  la muntura Sony va fer **dos salts d'eix** (+223 px x, −715 px y ≈ 12′ i 39′)
  entre C2+30 i C2+57. **Causa (testimoni de Pere): en treure el filtre va
  moure la lent**; la pertorbació es va alliberar amb retard i **la DSC06990
  va quedar moguda perquè la muntura va cedir durant l'exposició**. Entre salts, estabilitat de 0,5-1 px i les
  dues àncores de 8 s supervivents tenen **0,5-0,75 px de moguda interna**
  (contra 3,5 del Vixen): l'earthshine bo és Sony. Escala mesurada
  **3,234″/px** (focal ef. ~288 mm). **§4: EARTHSHINE DETECTAT** — el patró
  de mars surt a la pila Sony 2×8 s i coincideix fotograma a fotograma
  (r=0,90; nuls 0,14-0,21) i **entre Sony i Vixen** (r=0,89 a 327,25° de
  rotació relativa; nuls mediana 0,32) i **identificat contra LROC** (Sony
  r=0,68, Vixen 0,51; triangle de rotacions tancat a 0,25°). **§6: model
  físic de halo (dos nuclis d'ales de PSF sobre la corona real) i portes per
  capa: la pila única final és la Sony 2×8 s** (r=0,68/0,73 amb LROC fora de
  mostra); les capes curtes i el Vixen no passen la porta; color no fiable
  (només luminància). Lliurable a `~/Desktop/Eclipse 2026/Earthshine_FINAL/`.
- [71 — Seguiment, deriva i calibratge del Vixen + R6 III, MESURATS](71_SEGUIMENT_DERIVA_I_CALIBRATGE_VIXEN_R6III_2026-08-15.md):
  **coneixement canònic post-eclipsi del tren Vixen.** Taxa **solar
  verificada**; la deriva aparent residual és **~0,13″/s ≈ la refracció a 9°
  d'altura**, no la muntura. Escala de placa mesurada **2,158″/px** (focal
  494 mm ✓). **Contactes reals llegits de les imatges**: totalitat real
  103,7 s, clavada a la predicció del FINAL 2. ⚠️ El negre de metadata de
  libraw per a la R6 III és fals ([0,31,94,63]); el pedestal real és **511-512
  pla**. Masters APP 15/16 validats; el de 0,5 s, defectuós per barreja
  tèrmica. Sensor a 41-43 °C; vel de cel 3.400-4.300 ADU als 10,3 s. Inclou
  les sis trampes de mesura (dipol, forat-àncora, flare fix al sensor…).
- [70 — Escales noves de l'A7RIIIA i la R6, ACCEPTADES](70_ESCALES_A7R3A_I_R6_ACCEPTADES_2026-08-09.md):
  **La R6** hi porta dos canvis més: bloc fosc de **2 s ×3 i 10,3 s ×3 al mig
  de la totalitat** —10,3 s és el valor òptim de flota i 4,7 s més barat que
  el 15 s d'avui, i el forat màxim de flota baixa de 1,96 a **1,58 EV**— i la
  **finestra de contacte de C3 allargada de C3+4,0 a C3+24,0**, que no costa
  cap segon de totalitat perquè després hi havia 25,75 s buits. El preu és
  l'escala, que baixa de 4,7 a 2-3 fotogrames per esglaó sense perdre'n cap.
  El disseny d'escala d'exposicions fou **acceptat per Pere el 9 d'agost i
  implementat a la V1.00; la V1.02 en conserva la geometria**. Contactes a
  **base 1/800** —l'únic valor amb un fotograma ben
  endins de les dues bandes de perla— i una muntanya de base al mig: 1/4 → 1 s
  → 1/4. Passa de sis esglaons amb salts de 3,00 EV a **nou amb 2,00 màxim**, i
  de tres exposicions a mig eclipsi a sis. Modalitat triada: **3+3**, tres
  tríades de base 1 s i tres de 1/4, amb **tres subfotogrames a cada esglaó**.
  **Branca per durada**: 3+3 a partir de **89,5 s**, 3+2 de 83,3 a 89,5 i 3+1
  de 70 a 83,3; per damunt no creix perquè el sostre de cua és ple. ⚠️ El preu
  és que l'earthshine queda a **24 s, el terra exacte de la porta**. Hi ha
  també la taxa de seguiment —**solar als dos trens, 0,585 ″/s** de moviment
  lunar relatiu— i per què N=3 **no** rebutja píxels calents.

- [69 — El balanç de blancs passa a correcció d'arrencada, i el Mac ja no s'adorm](69_BALANC_DE_BLANCS_AUTOMATIC_I_ANTISUSPENSIO_2026-08-08.md):
  tanca el «que NO s'ha fet» del `68`. **Els quatre perfils de missió declaren
  `/main/imgsettings/whitebalance` = `Daylight` com a correcció d'arrencada**,
  amb un sol intent, readback i un fracàs net que no atura el canal; va
  l'última de la llista a propòsit i sense `allowed_initial_values`, que seria
  un hard stop. I **mentre hi ha un run en marxa el Mac no s'adorm**, també
  amb bateria: els dos hosts detached retenen `caffeinate -i -m -w`, que és
  l'única bandera que actua sense corrent i que es mor sola si el host cau.
  Cap run físic encara amb cap de les dues coses.

- [68 — El balanç de blancs anava en Auto als dos cossos de missió](68_BALANC_DE_BLANCS_EN_AUTO_ALS_DOS_COSSOS_2026-08-08.md):
  troballa sortida de revisar el tutorial de processament d'Astrofalls, que no
  té secció de captura però hi imposa requisits. **L'A7RIIIA i la R6 anaven
  amb Auto WB** —bolcats `20260808T173224` i `20260803T195235`, i l'EXIF de 29
  runs ho confirma al primer— mentre que l'A7III ja hi anava en manual. El RAW
  guarda els multiplicadors del moment del dispar i Camera Raw els aplica amb
  «As Shot», o sigui que amb Auto WB cada esglaó de l'escala escala el vermell
  i el blau diferent i la barreja HDR perd coherència **de color**. És la
  mateixa família d'ajust que el DRO, que la checklist sí que caçava. Corregit
  a les dues checklists físiques; no s'ha tocat cap càmera ni cap geometria.
  Hi queden anotades dues observacions estructurals: **l'extrem llarg de
  l'escala de la R6 té dos fotogrames per esglaó** i les repeticions d'una
  mateixa exposició no són consecutives en aquest cos.

- [67 — El `-110` de la R6 no és el cable: és cadència sense marge](67_DIAGNOSTIC_DEL_110_DE_LA_R6_NO_ES_EL_CABLE_2026-08-08.md):
  diagnostica les 34 pèrdues del run `20260808T173855` i **descarta el cable**:
  la sessió PTP no es va perdre ni una vegada (`connection_epoch` = 1) i les
  recuperacions van durar 6-42 ms. Són dues causes de pressupost: la cadència
  de contacte de **0,40 s no té marge per construcció** —el forat compilat és
  exactament el terra del cos— i en aquesta sessió el cos només acceptava una
  pulsació cada **0,80 s**, d'on surt el patró alternat; i el forat es compila
  amb l'obturació **prevista**, o sigui que un setter rebutjat deixa el
  fotograma anterior més llarg del que el pla creu. La comparació amb
  `20260807T172151` —mateixa geometria, **115/115**, pulsació de 54 ms contra
  121— demostra que el que ha canviat és el cos i que el programa no tenia ni
  una dècima per absorbir-ho.

- [66 — L'àncora de 8 s mesurada i la NR dels dos Sony](66_ANCORA_8S_MESURADA_I_NR_DELS_DOS_SONY_2026-08-08.md):
  tanca el número que mancava a `65`: **una àncora costa 11,21 s**, contra
  els 11,6 assumits, o sigui que el disseny de blocs i les seves sis àncores
  a 90 s es mantenen. De retruc demostra que **la reducció de soroll
  d'exposició llarga està apagada als dos cossos** —cap dels dos la publica
  per PTP i es mesura pel temps que triga la imatge a entrar a la cua—, dona
  els números per decidir cada quant es drena —**partir la cua per la meitat
  costa 1,3 àncores de sis**— i identifica la causa mecànica del desastre de
  la nit: **l'app mata a senyal qualsevol `gphoto2` que no sigui seu**, i un
  `gphoto2` mort a mig drenatge deixa el cos inservible fins a treure-li la
  bateria.
- [65 — Mesures al banc dels dos cossos Sony](65_MESURES_SONY_BLOCS_NIT_2026-08-08.md):
  tres mesures noves i sòlides —**el fotograma ràpid és el segon de tres**, la
  cadència per sota de 2,5 s **mata la sessió gphoto2**, i l'A7III drena
  **1,55× més ràpid** que l'A7RIIIA—, el tetris de blocs que en surt (sis
  àncores d'earthshine a 90 s contra les dues d'avui), i dues coses que
  calia dir: **l'app oberta roba els cossos a qui hi estigui treballant**, i
  la campanya s'ha aturat perquè **tots dos cossos han quedat caiguts a
  nivell PTP** i necessiten un cicle d'alimentació. Part de la culpa és del
  mètode, i queda escrita.
- [64 — L'earthshine primer: totalitats curtes a l'A7RIIIA](64_A7R3A_EARTHSHINE_PRIMER_TOTALITATS_CURTES.md):
  amb l'earthshine declarat missió principal de la Sony, el defecte no és de
  pressupost sinó **d'ordre de construcció**: el compilador col·loca primer
  contactes i drenatges i a l'earthshine li dona el que sobra, fins al punt
  que `_a7r3a_earthshine_burst_count()` retorna zero per sota de 88 s. Els
  tres objectius caben en **tres pulsacions i 30,9 s**, perquè la ràfega
  d'earthshine ja és una passada de corona de 12 EV. Codex hi ha refutat la
  meva primera versió —barrejar dos modes de bracket obliga a escriure
  `capturemode` amb la cua plena, i això el cos ho rebutja— i el disseny bo
  és **un sol mode `C 3.0 Steps 5` tota la totalitat canviant només la base**.
  I aquest disseny **ja existeix qualificat i és codi mort**:
  `_materialize_a7r3a_fixed5_midpoint()`, 35 fotogrames sense cap drenatge
  intern, no es crida des d'enlloc.
- [63 — Determinisme a les dues càmeres](63_DETERMINISME_DUES_CAMERES_2026-08-07.md):
  el primer run multicàmera va donar Sony 60/60 i R6 **67 de 120 físics a la
  targeta**, amb 70 fotogrames disparats amb una exposició que no era la
  prevista. La causa no és el codi, ni la geometria, ni la cadència, ni la
  bateria, ni la targeta: és un **estat intermitent del transport USB de la
  R6** que acaba en una desaparició sencera del bus. Dues correccions:
  un `-110` ja no costa una sessió PTP sencera sinó un probe de
  resincronització de mil·lisegons, i **els brackets de contacte de la Sony
  ara travessen C2 i C3** —abans tancaven l'obturador 0,23 s abans del segon
  anell de diamant i el perdien—. La segona està verificada al cos: 60/60,
  C2−2,89 a +2,90 i C3−2,00 a +0,91, 13 exposicions de 1/4000 a 8 s.
- [62 — El setter no el paga el transport](62_EL_SETTER_NO_EL_PAGA_EL_TRANSPORT_R6_2026-08-07.md):
  dels 445 ms d'un canvi d'exposició, **400 eren un `sleep` fix del nostre
  worker**: l'escriptura costa 12 ms i la comprovació 4. Reparat amb una
  enquesta que comença immediata i frena després, amb el mateix sostre i
  sense moure cap garantia. Porta també dues millores de geometria que no
  demanen res de nou al cos —patró `tail_only` i finestra de C3 elàstica—
  que valen **+8 fotogrames i dotze més a 1/2000**. Falta la mesura
  d'adopció al cos: si adopta ràpid, la ranura baixa i el programa passa de
  94 a 118-122 fotogrames.
- [61 — La cadència de la R6 i l'earthshine de 15 s](61_CADENCIA_I_EARTHSHINE_DE_15_S_R6_2026-08-07.md):
  el terra de pulsació de 400 ms val també per gphoto2: **94/94 fotogrames,
  delta CFexpress exclusiu +94, 48/48 setters i retard màxim 0,0 ms**. I una
  troballa que no és la que semblava: després d'un fotograma de **15 s** el
  cos refusa el canvi d'obturació fins a **2,10 s**, mentre que després d'un
  de 2 s l'accepta a 0,30 —o sigui que no és proporcional ni és la foto fosca
  de la reducció de soroll—. El programa passa a 0,40 s d'interval, 0,55 de
  setter i earthshine de 15 s. Dos defectes reparats: el lease de l'obturador
  ja no es confon amb l'espera fins a l'ordre següent, i el restore de
  cleanup deixa de disparar massa aviat.
- [60 — EDSDK contra gphoto2: la mesura](60_EDSDK_CONTRA_GPHOTO_MESURAT_R6_2026-08-07.md):
  dotze execucions del programa sencer per l'SDK contra el cos. **L'SDK és
  divuit vegades més barat al setter i compra un +22 % de fotogrames —112
  contra 92—, i tot i així la recomanació és quedar-se amb gphoto2**: quan
  falla es penja, i d'un penjat només se surt apagant el cos, a un sol esglaó
  de geometria del punt de treball. Delta CFexpress global +510 i menú intacte
  a 58 opcions: sense ràfegues, el col·lapse no apareix ni per l'SDK. Porta
  també **el que la mesura regala a gphoto2**: el terra de pulsació del cos és
  400 ms, no els 500 que fa servir la missió, i estrènyer-lo val +11 % de
  fotogrames i un earthshine més; i el temps mort que deixa l'empaquetat
  d'escales senceres, de 2,7 s a 98,8 s i fins a 8,0 s al pitjor cas.
- [59 — El programa portat a l'EDSDK](59_PORT_DEL_PROGRAMA_A_L_EDSDK_R6_2026-08-07.md):
  el port sencer a l'SDK de Canon, compilat i encaixat, amb l'obturador
  electrònic com a gate i la taula de codis Tv treta de l'exemple oficial. La
  mesura física va quedar bloquejada per la bateria. Hi ha el runbook i, més
  útil, **el criteri de decisió escrit abans de mesurar**: fer el setter
  quatre vegades més ràpid només compra un +22 %, perquè a partir d'aquí mana
  el terra de 0,50 s entre pulsacions. L'SDK només val la pena si **també**
  aguanta pulsar més sovint.
- [58 — El programa de la R6: una foto per exposició](58_PROGRAMA_UNA_FOTO_PER_EXPOSICIO_R6_2026-08-07.md):
  el programa de missió nou, ja implementat i mesurat al cos. **92/92
  fotogrames, delta CFexpress exclusiu +92, 54 setters amb readback exacte,
  retard màxim 0,0 ms i el menú a 58 opcions abans i després.** EXIF
  verificat a 1/2000 als contactes i **8 s reals** a l'earthshine. Cap
  ràfega enlloc, o sigui que la regla dura es compleix per construcció.
  Substitueix el nucli dens: 74 fotogrames dins totalitat en comptes de 318,
  però tots a l'exposició triada i cobrint 15 velocitats de 1/2000 a 8 s.
- [57 — La filosofia del 2024 no mata el menú](57_FILOSOFIA_2024_A_LA_R6_2026-08-07.md):
  fotos soltes amb procés nou per ordre, com el `Canon6DFinal.sh` de 2024.
  48 canvis d'exposició de 48, menú intacte a 58 opcions, cap col·lapse.
  Canviar d'exposició costa **0,38 s**, no els 2,00 s que reserva el nucli
  dens, i una foto costa 0,9 s més el temps d'exposició. L'earthshine passa
  a ser `shutterspeed=8` i prou.
- [56 — El menú col·lapsat és del cos](56_PROVA_REOBERTURA_SESSIO_R6_2026-08-06.md):
  executat. Tres sessions PTP independents veuen el mateix menú de dues
  opcions: tancar i reobrir no el cura, o sigui que no és una còpia
  degenerada de libgphoto2. Tanca la porta de l'EDSDK per a aquest defecte.
  I el llindar no és fix: 82 pulsacions als runs de missió, **12** al banc.
- [55 — El menú d'obturació de la R6 es col·lapsa](55_MENU_OBTURACIO_COLLAPSAT_R6_2026-08-06.md):
  per què tres canvis de base i la restauració van fallar al run
  `20260806T184228`. El cos passa de 58 opcions a dues enmig de la ràfega i
  no en torna a publicar més en tota la sessió; ni bateria, ni buffer, ni
  transició curta. Cost fotogràfic i prova discriminant pendent.
- [54 — Nit d'optimització de captura](54_NIT_OPTIMITZACIO_CAPTURA_2026-08-06.md):
  el port de gphoto no identifica cap cos i la reparació del routing per
  sèrie PTP; sostre físic real de la R6 —5 CR3/s sostinguts i canvi de base
  a 1 s— i el nucli dens v4 que en surt; parcials a 30 s; anàlisi del marge
  Sony i el conflicte entre earthshine i la política d'ISO 100.
- **53 — Pla del backend EDSDK per a la R6** *(referència històrica: el fitxer
  citat no és present al worktree actual)*: què limitava gphoto en aquest cos,
  on podia guanyar l'EDSDK i l'ordre de gates proposat. Els resultats físics
  posteriors són a [60 — EDSDK contra gphoto mesurat](60_EDSDK_CONTRA_GPHOTO_MESURAT_R6_2026-08-07.md).
- [52 — Gate R6 III d'obturació base dinàmica](52_R6M3_DYNAMIC_SHUTTER_GATE_2026-08-05.md):
  diagnòstic dels runs 12:22 i 14:55, reparació Mission First del Busy net,
  escala objectiu i ordre de gates físics abans de qualificar els setters.
- [51 — Candidat R6 III triple RAW amb AEB3](51_R6M3_TRIPLE_RAW_AEB3_2026-08-04.md):
  auditoria del TEST RUN 0.7.7, comparacio Single/AEB3 i gates G1, G5 i G40
  per arribar a 105 RAW dins C2-C3 sense substituir encara el fallback 40/35.
- [50 — Exposició solar filtrada canònica a 10°](50_EXPOSICIO_SOLAR_FILTRADA_CANONICA_10G_2026-08-04.md):
  ancoratges RAW/JPEG propis de l’A7RIIIA i la R6 III, extrapolació a 700 m i
  obturadors parcials únics sense multiperfil.
- [49 — Poliment de contactes i C3 A7RIIIA](49_POLIMENT_CONTACTES_I_C3_A7RIIIA_2026-08-02.md):
  successor físic 83/83, 72 fotos durant totalitat i dues exposicions de 3,2 s.
- [48 — Pipeline fixed9 de l’A7RIIIA](48_A7RIIIA_FIXED9_BUFFER_PIPELINE_2026-08-02.md):
  disseny i gates del buffer 9×1.
- [47 — Midpoint fixed5 A7RIIIA](47_A7RIIIA_FIXED5_MIDPOINT_2026-08-02.md):
  predecessor del perfil actual.
- [46 — Política ISO](46_POLITICA_ISO100_OPERADOR_2026-08-01.md): ISO 100
  recomanat; cap ISO pot fallar una missió.
- [45 — Canon 6D](45_CANON_6D_AUDITORIA_OPTIMITZACIO_HARD_STOP_2026-08-01.md):
  auditoria i evidència de la branca Canon. Consulta també l’estat resumit de
  `../CLAUDE.md`, que és posterior.
- [44 — A7RIIIA + 300 GM](44_OPTIMITZACIO_A7RIIIA_300GM_C2_C3_2026-07-31.md):
  hipòtesis i mesures que van originar la coreografia actual.
- [43 — Discrepància fotomètrica](43_AUDITORIA_DISCREPANCIA_FOTOMETRICA_2026-07-31.md):
  deute científic encara obert.

## Arquitectura i resiliència

- [42 — Tres càmeres](42_TRES_CAMERES_A7III_A7RIIIA_CANON_2026-07-29.md)
- [41 — Backend Canon](41_CANON_6D_COEXISTENCIA_I_BACKEND_2026-07-29.md)
- [38 — Desconnexió A7III](38_RESILIENCIA_DESCONNEXIO_EN_CALENT_V036_2026-07-28.md)
- [36 — Arquitectura multicàmera](36_ARQUITECTURA_MULTICAMERA_CANON_UI_2026-07-28.md)
- [35 — Cronologia completa](35_GATE_CRONOLOGIA_COMPLETA_V035_2026-07-28.md)
- [34 — Drenatge i handoff HDR](34_QUALIFICACIO_DRENATGE_I_HANDOFF_HDR_2026-07-28.md)
- [32 — Resiliència PTP](32_RESILIENCIA_CONNEXIO_A7III_PTP_2026-07-27.md)
- [31 — Drenatge adaptatiu](31_DRENATGE_ADAPTATIU_I_DRO_OFF_2026-07-27.md)

## Fonaments científics i forense 2024

- `00`–`17`: resum, genealogia, ciència i pipeline Druckmüller, auditoria
  2024, contracte temporal i card-only RAW.
- `19`–`30`: desenvolupament i qualificació inicial de l’A7III.
- [39 — Metodologia SNR](39_METODOLOGIA_DXOMARK_SNR_CAMERES_2026-07-28.md)
- [FONTS.md](FONTS.md): fonts i traçabilitat.

## Material històric o auxiliar

- [CLAUDE_PROMPT.md](CLAUDE_PROMPT.md): prompt de revisió adversarial
  històric. No és una instrucció viva per a Claude.
- [OPENROUTER.md](OPENROUTER.md) i els documents `08`, `17`, `29`, `32` i
  `33` de contrast extern: opinions i triangulació, no prova física.
- Els tancaments de ronda `24`–`29` descriuen versions supersedides.

No eliminis un document antic perquè sembli contradictori: pot ser la
proveniència d’un gate. Marca’l com a històric i resol l’estat viu a
`../CLAUDE.md`.
