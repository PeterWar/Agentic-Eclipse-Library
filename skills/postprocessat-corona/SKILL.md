---
name: postprocessat-corona
description: >-
  Postprocessat de la corona de l'eclipsi del 12-08-2026 (Vixen VSD90SS + Canon R6 III; Sony A7RIIIA + 300 mm), dels RAW al PSB de Photoshop, amb
  la cadena V103 (`3-RECERCA/tools/v103_banda_20260926/cadena_v103.sh D`, sobre la V99/V101 i els apilats de la cadena V97): calibració i apilats per tren regenerats bit a
  bit des dels RAW, fusió dels trens, franja d'un sol instant arran del limbe, base de pantalla, els 16 filtres (NRGF, RHEF, RHEF local, MGN, WOW,
  ACHF), jutge predeclarat contra la versió anterior, muntatge del PSB i desament natiu com a còpia. Usa-la per refer o millorar la imatge, per
  diagnosticar un artefacte a l'origen (la «torre de Pisa» de Pere), per jutjar una versió nova, per replicar el resultat en un altre ordinador, i
  per a qualsevol feina sobre LDIC, artefactes, anells, costures, graons, polígon de color, limbe lunar, perles, protuberàncies, earthshine, LROC,
  estrelles, Brno o Druckmüller, porta Photoshop o CapesTotals.
---

## Porta de la torre de Pisa · 28-09-2026

Abans de promoure una correcció, llegir `IA/GUARDRAILS_POSTPROCESSAT.md` a l'arrel del projecte i executar la porta de mètode sobre el PSB efectiu. Els ràsters causants corregits han d'estar actius al seu lloc; tots els ajustos dependents s'han de recompondre. Cap compensació de compost o residual antic congelat al damunt, tampoc per conservar la presentació. Traçar totes les capes noves visibles i separar retoc manual, identitat del fitxer i validesa científica. El control negatiu V109 ha de fallar la porta. Una discrepància amb el compost manual antic s'exposa; no es resol saltant aquesta regla.

# Postprocessat de la corona (cadena V97)

**Llegeix això sencer abans de tocar res.** Aquesta skill és per a qualsevol model, també un de menys potent:
- segueix els passos en ordre;
- compara cada número amb el valor esperat;
- atura't si una porta falla.

Altres fonts:
- la skill anterior (fins a la V96): `references/SKILL_fins_V96_20260924.md`; la de la V97: `references/SKILL_fins_V97_20260925.md`; la de la V98: `references/SKILL_fins_V98_20260925.md`;
- les normes detallades: `references/normes_i_portes.md`;
- les lliçons: `references/llicons_consolidades.md`.

## 1. Vuit regles que no es trenquen mai

1. **⛔ Res inventat, res reflectit** (norma canònica de Pere, 24-09-2026).
   - **Cap píxel que no vingui de dada observada:** ni farcits, ni continuacions, ni miralls, ni pull-push, ni Laplace, ni textures o models en lloc de dada.
   - **On no hi ha dada:** transparent (capes en Superposar o Diferència) o NOMÉS el nivell al llarg de l'arc (capes en Multiplicar, decisió B de Pere).
   - Si alguna cosa no es pot fer sense inventar, es pregunta a Pere.
2. **La torre de Pisa** (mètode de Pere, 20/21-08). Un defecte es cura al pis on neix i es refà tot el de sobre. Mai s'apedaça on es veu.
3. **El jutge, abans de construir.**
   - Tota versió nova es mesura amb la MATEIXA vara que l'anterior (`j0_jutge.py` + `j9_veredicte.py`), amb els llindars escrits abans de veure-la.
   - «Millor» vol dir el veredicte, més les làmines, que has de mirar TU abans de lliurar.
4. **Photoshop: desa sempre COM A CÒPIA** (`'Cpy ' true`), i passa dues portes:
   - la p6: el compost fusionat ha de coincidir amb la vista renderitzada;
   - `porta_photoshop.sh`, amb el literal `OBRE`.

   El 24-09, desant sense còpia, el compost va sortir malmès 4 vegades.
5. **Sense Git; sense escriptor únic (30-09-2026).**
   - Ja no cal claim: diversos xats poden escriure alhora (Pere: «hem d'acabar tasques ràpid»).
   - Noms nous, mai sobreescriure el que un altre pot tenir obert; Photoshop d'un en un.
   - Cap ordre `git` en aquest arbre. En acabar: traspàs si cal i zero processos propis.
6. **Les entrades de Pere són intocables.** Mai se sobreescriu cap fitxer: noms nous. Són intocables:
   - els RAW, els calibradors i els PSB existents;
   - les seves capes, màscares, modes, opacitats i capes d'ajust (239–244);
   - l'encaix de les capes interiors;
   - els documents que tingui oberts al Photoshop. ⛔ Obrir un fitxer que ja té obert NO en fa una còpia: et torna el SEU document, i tancar-lo li perd els canvis (vegeu el §1i, regla 8).
7. **Cap intèrpret escrit a pèl.**
   - Fes servir el primer Python que tingui numpy, scipy, opencv, rawpy, numexpr, psd-tools i tifffile (avui `~/.venvs/eines-ia-py312`). `cadena_v97.sh` ja el busca.
   - Exporta `PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=4`.
8. **Cap canvi declarat sense la prova que ha entrat** (el hash, o la diferència mesurada amb i sense el canvi). Un rebut sense paràmetres no és un rebut.
9. **⛔ Amb més d'una òptica, la distorsió de cada òptica es corregeix ABANS de fusionar** (norma de Pere, 29-09-2026: «és un pas que s'ha de fer obligatòriament si captures l'eclipsi amb més d'una òptica. La distorsió òptica importa»).
   - **Què va passar:** el registre de la cadena (`f1.py`) només fa escala, angle de posició i translació per tren. Al llenç, la Vixen i la Sony A difereixen 3–7 px a les estrelles i fins a 0,25° als raigs (5–10 px a 3–5 R☉), i el desplaçament no és una rotació pura: canvia amb l'angle. La fusió barreja la Vixen i la Sony amb pesos del 35–87 % entre 2 i 6 R☉, i allà el detall fi dels raigs surt desdoblat. Pere ho va detectar perquè les estrelles de Brno no quadraven amb les nostres; l'apilat de la Vixen ja es sabia «girat 0,13°» (§1i), però només es va tractar com a fantasmes d'estrelles.
   - **El pas obligatori:** per a cada tren, un model de distorsió (com a mínim afí; millor un polinomi de 2n–3r grau o un camp suau) cap a la geometria de referència. La referència, per defecte, és el tren que quadra amb el catàleg d'estrelles (el 2026, la Sony). **El 2026 Pere va triar la Vixen** (opció 3, V120): la Lluna, la corona interior i els seus retocs hi són a sobre i no es mouen. Conseqüència: el llenç segueix la Vixen i no el catàleg (3–7 px, fins a 17,5 px a les cantonades), i per a l'astrometria cal fer servir les posicions d'abans de la deformació (`x_V114`, `y_V114` del catàleg). S'ajusta amb les estrelles de cada tren contra el catàleg i amb la correlació del detall de la corona entre trens.
   - **Porta abans de fusionar, al solapament de cada parella de trens** (sense ella no es fusiona):
     - estrelles de cada tren contra el catàleg: residu rms ≤ 1 px i sense patró amb l'angle ni amb el radi;
     - desplaçament angular del detall de raigs (correlació per finestres al llarg de l'arc) i desplaçament radial del detall d'arcs (correlació al llarg del radi): mediana ≤ 0,5 px i p90 ≤ 1 px a cada tram de radi;
     - mapa de desplaçament continu: cap salt entre mostres veïnes (la lliçó de la 416 de la V118, costures de ~3 px).
   - **El camp s'esvaeix a zero a la vora del marc de cada tren** (lliçó de la V120, 29-09-2026). Si el tren es deforma sencer fins a la vora, surt del seu propi marc (fins a ~13 px el 2026) i:
     - a la vora del llenç la base queda sense dada: tira negra de 2–4 px, rampa de 6 px i les capes de detall aclarides 20–30 px;
     - allà on la vora d'un tren talla el camp d'un altre, creix la zona coberta només per l'altre (la cantonada de la B amb la Vixen a 9,3 R☉ va sortir com una taca ovalada brillant).
     - **Com:** marc = on hi ha dada a TOTES les variants del tren i pes > 0, amb els forats interiors omplerts i la vora del llenç inclosa; u × smoothstep(d / 200 px). A la deformació, on el peu de la interpolació cúbica tocaria la vora de la dada, bilineal NORMALITZAT (només amb dada): una erosió de 2 px «per seguretat» torna a fer la tira negra. Eines: `3-RECERCA/tools/v120_20260929/f10_marcs_sony.py`, `camp_v120.py` (clau «vora» del model) i `f5_warp_sony.py`. Abans d'aplicar-ho, comprova que la franja no toca cap zona on el tren pesi a la fusió (el 2026: A hi pesava un 8 %, i la Vixen, un 0,6 % a la de B).
     - **Porta:** el marc del tren deformat ha de ser idèntic al de l'original (cap píxel de la base de vàlid a 0), i el mapa V(nou)/V(vell) − 1 no pot mostrar cap línia ni taca a les vores.
   - **La deformació ho arrossega tot:** les llistes d'estrelles de la D4 (amb una còpia Vixen de cada canònica a la mateixa posició, perquè la D4 hi continuï extraient la Vixen), el catàleg, la capa 202 (segells traslladats, llum conservada), el mapa 203, les capes de Brno per estrelles i els testimonis dels filtres. Eines: `v120_20260929/f7`, `f8`, `f9`.
   - **Qualsevol capa que combini trens o fonts** (filtres de testimonis, capes de detall) es registra a la geometria del COMPOST on s'aplica, no a la d'una font. Eines: `3-RECERCA/tools/v118_20260929/b8_filtre_registrat.py` i `v119_20260929/b8b_ordit_registrat.py` (angle), `v119_20260929/b9_trama_tres_testimonis.py` (radi).

## 1i. ⛔ Estrelles, capes de referència i documents oberts (28-09-2026): llegeix-ho abans de tocar cap estrella

**Què va passar entre la V82 i la V113** (cada punt va costar una versió):
- **Brno mal encaixat:** les capes de Brno 230–232 es van encaixar per la corona, i les seves estrelles quedaven a 11–29 px de les nostres. Les nostres eren bones (0,42 px del catàleg).
- **Estrelles afegides sense prou dada:** un agent va afegir 4 estrelles de catàleg (capa 413) que la V65 ja havia rebutjat. Tenien S/N 5,7–6,9 només a la Sony, sense cap segon conjunt independent, i una duia el flux tret de la magnitud en lloc de mesurat.
- **Estrelles doblades:** 13 estrelles sortien dues vegades. La 202 suma la llum, i la real encara era a la base.
- **Fantasmes:** l'apilat de la Vixen està girat 0,13° respecte del cel i deixava còpies de les estrelles 10–12 px al costat.
- **Capa negra opaca:** una capa d'estrelles negra i opaca feia opac el document i tocava 1.173 píxels del limbe.
- **Extracció descentrada:** la D4 treia les estrelles centrades en posicions enteres, fins a 3–4 px de la llum real. A les estrelles brillants quedava un dipol que els filtres amplifiquen.
- **Document de Pere tancat:** una eina de render va reutilitzar un document que Pere tenia obert al Photoshop i el va tancar sense desar.
- **Quatre estrelles de la 202 sense prou dada:** l'auditoria de la V114 va trobar que la V65 havia acceptat les S57–S60 per escletxes del seu criteri. Hi entraven per mesures al pic cercat i no a la posició de catàleg, per la via conjunta sense comprovar la coincidència, per un sol pla de color o un sol píxel, i per un sol fotograma.

**Regles:**
1. **Cap estrella de catàleg sense dada.** Val el criteri congelat de la V65, que no es toca:
   - S/N total ≥ 8;
   - S/N ≥ 4 en DOS conjunts independents (dos apuntaments o dos instruments);
   - ≥ 300 controls mesurats igual, i cap d'acceptat;
   - flux MESURAT als RAW.

   No rebaixis el llindar per a una estrella concreta, ni busquis amb més paciència on el catàleg diu que n'hi ha: amb 1.132 posicions provades, n'hi ha que passen per atzar. Una estrella rebutjada per la V65 només entra amb dada nova que compleixi el criteri. Afegir-ne o treure'n de la 202 és una decisió de Pere (§7).

   **Proves d'integritat (des de la V114).** Tanquen les escletxes per on la V65 va acceptar quatre estrelles (S57–S60) que, tornades a mesurar, no se sostenen. El llindar no canvia.
   - **Mesura forçada** a la posició de catàleg, mai al pic trobat buscant a ±3 px.
   - **Coincidència ≤ 2,5 px** entre apuntaments, també a la via conjunta.
   - **Color coherent per pla:** verd ≥ 0,6× la multibanda, i cap excés concentrat en un sol pla o en un sol píxel (a la S59 era un píxel R del sensor).
   - **El criteri ha d'aguantar traient el fotograma que més hi pesa.**
   - **Flux mesurat/esperat ≤ 2:** si la V dona un S/N esperat per sota del llindar, un pas just és biaix d'Eddington (S60: V 10,33, S/N esperat 3,8).
   - **L'altre instrument no la pot contradir.**
   - **Z calibrada amb ≥ 300 nuls propis**, al costat de la nominal.

   Catàleg vigent i motius: `4-RESULTATS/v114_estrelles_20260928/CATALEG_ACCEPTAT_V114.json`, amb 56 estrelles. Les S57–S60 hi consten com a «llum present, no confirmada».
2. **Detectable no vol dir detectada.** Amb 90–107 mm d'obertura, el cel brillant (Sol a 5° i pols) i el vinyetatge de les vores, una V 8,6–9,4 pot quedar per sota del límit en aquell punt del camp. Calcula l'S/N esperat abans de buscar-la, i compara'l amb el mesurat.
3. **Les estrelles pintades són models declarats** (gaussiana circular de σ 1,5 px, recepta V65). La forma perfecta és per disseny. El que cal demostrar és que la font existeix a la dada, no que el dibuix sigui bonic.
4. **Tota estrella pintada es treu de la base** (D4), a cada font (fusió, Vixen i Sony) i al lloc on hi ha la seva llum (el centroide a la font, `--recentra` des de la V114), no a la posició de la llista. Si no, la llum surt doble o queda un dipol.
5. **Registre per tren.** Mesura el camp d'estrelles de cada apilat (Vixen, Sony A i Sony B) contra el catàleg (`3-RECERCA/tools/v113_estrelles_20260928/f2_estrelles_vixen.py`). Si un tren es desvia (gir o escala), extreu-ne les còpies (EXTRA_ESTRELLES) o registra de nou el tren. Això segon mou el limbe i és decisió de Pere.
6. **Capes de referència (Brno o qualsevol altra externa):**
   - s'encaixen per les ESTRELLES, amb ≥ 10 estrelles i l'RMS de les reservades; mai només per la corona;
   - abans de dir que les nostres estrelles estan malament, compara-les amb el catàleg: mana el catàleg, no Brno.
7. **Capes additives noves:**
   - transparents fora de la llum;
   - el compost no pot perdre el canal de transparència;
   - el limbe no pot canviar.
9. **Mapa d'estrelles (capa 203):** Pere el fa servir per saber quina estrella és cadascuna.
   - Cada etiqueta, alineada amb la seva estrella (a la dreta o a l'esquerra; si no hi cap, a sobre o a sota).
   - Cap etiqueta damunt d'un altre cercle o d'una altra etiqueta.
   - El punt de l'etiqueta més proper a la seva estrella ha de ser almenys 1,6× més a prop d'ella que de qualsevol altra.
   - Una línia guia només si cal allunyar-la.
   - Generador: `3-RECERCA/tools/v114_estrelles_20260928/m6_mapa_203_v2.py`. El de la V65 només evitava que les etiquetes es trepitgessin entre elles (S23/S47, S36/S45).
   - Si canvia el catàleg, es regenera el mapa sencer; no s'hi pinta a sobre.
8. **Photoshop: mai no obris un fitxer que Pere tingui obert.** `app.open()` d'un fitxer ja obert no l'obre de nou: retorna el document de Pere, i el `close(DONOTSAVECHANGES)` final el tanca i en perd els canvis no desats. Les eines comproven `jaObert` i s'aturen amb `OBERT_PER_PERE`. `porta_photoshop.sh` diu `NO EXECUTADA`. Si cal aquell fitxer, pregunta-ho a Pere.

**Porta executable:** `scripts/porta_estrelles.py` (`--cataleg` amb el catàleg acceptat de la versió), amb el render natiu SENSE les capes d'estrelles (`3-RECERCA/tools/v112_claude_20260928/r5_render.sh <psb> <carpeta> "202,…"`) i el model de fantasmes F2. Comprova cinc coses:
- **E1:** inventari contra el criteri;
- **E2:** llum doble;
- **E3:** fantasmes, amb control aparellat girat;
- **E4:** capa neta;
- **E5:** referències encaixades per estrelles.

Una versió amb estrelles noves o tocades només es lliura amb E1–E5 PASSA (una «NO AVALUABLE» s'ha de declarar). Proves negatives reals, a `4-RESULTATS/v114_estrelles_20260928/PORTA_ESTRELLES_*.json`:
- **V113 del migdia:** falla E2 (S04), E3 (p 0,0008) i E5 (29/11/19 px);
- **V113:** falla E1 (les 4 Tycho) i E2 (S04);
- **`V113_capa413_opaca.psb`:** falla E4.

Prova positiva: la **V114** (`1-PHOTOSHOP/V114.psb`, SHA `6515a416…`) PASSA de E1 a E5, amb 56 estrelles, la D4 amb `--recentra --nucli-fi` i sense les S57–S60. E3 hi passa just al límit (p 0,0104). Rebut `1-PHOTOSHOP/V114_REBUT.md`.

## 1h. Estat al 27-09-2026: la V108 (llegeix-ho primer)

La V108 (`1-PHOTOSHOP/V108.psb`, candidata; recerca `3-RECERCA/176_…`, traspàs `.coordination/HANDOFF_2026-09-27_V108.md`) és la V107 de Pere amb la base i els 16 filtres regenerats amb el flat 2D, i la NRGF amb l'opció (a) de les zones negres.
1. **⛔ Qualsevol línia o taca fixa al camp exterior: mira primer el FLAT.** El FLAT_RADIAL de la cadena només té la part radial, i les RHEF locals, la WOW, l'ACHF i l'MGN multipliquen per ~100 l'estructura fixa del sensor.
   - Cura: `flat2d_v5/` (C comuna i sense anells a la Sony, porta de pols per grup, fusió/franja/REC congelades).
2. **Prova cura/injecció s = (E_després − E_abans)/|Δ|²**, amb nuls a la mateixa imatge.
   - A la Sony, fes-la amb el cel anul·lat: A − B, gràcies als dos apuntaments separats 749 px.
   - Un traç es mesura amb geometria FIXA, mai amb una cerca.
3. **Zones negres = la NRGF normalitza el gradient del cel.**
   - L'opció (a), `negres_v2/g1_nrgf_genoll.py CEL_G_MAX_T_e30_W_H0`, depèn de les opacitats i màscares de la V107: si es toquen, torna-la a córrer.
   - La cura d'origen del residu és un guany per banda segons el S/N dins de les capes en Superposar, i està per fer.
4. **Mesura sempre al compost que desa el Photoshop,** i la flamarada sense els harmònics m ≤ 3 (el gradient del cel).

## 1g. Estat al 26-09-2026 (vespre): la V106 (llegeix-ho primer)

La V106 (`1-PHOTOSHOP/V106.psb`, candidata; informe `4-RESULTATS/v106_inversio_20260926/RESULTAT.md`, recerca `3-RECERCA/174_…`, traspàs `.coordination/HANDOFF_2026-09-26_V106.md`) és la V105 amb la capa 306 de detall arran del limbe refeta amb la geometria fina, i la 305 oculta.
1. **⛔ Nord celeste al llenç: 45,253°** (no 44,25°, i la cadena en diu 43,41°). Ajusta l'orientació a l'escala fina, amb validació creuada, abans de fer servir cap relleu lunar.
2. **Vora real de la Lluna:** LOLA-64, més el radi i el centre mesurats a la vora de cada fotograma, més la refracció comuna i lenta (`lola_fi/geom_fina.py`). La dispersió atmosfèrica desplaça el centre del vermell i el del blau ±0,7 px en vertical.
3. **Detall `c1f`:** cada fotograma dividit per la seva T calculada amb aquesta vora, i admès des de T ≥ 0,7. Amb una geometria dolenta, dividir per T **empitjora** la prova Lluna/corona.
4. **Prova «Lluna o corona»:** fes-la per sectors de 20° i agregada per franges de d, amb el soroll de desfasaments falsos (`m1e_agregat_sectors.py`). A 140–200° i 320–340° no discrimina, perquè el moviment de la Lluna hi és radial.
5. **Detall híbrid** (`h1_hibrid_delta.py`) i porta per angle (`h1/GATE_PA_V106.json`): 195–240° des de 3 px, 240–260° des d'1 px i 260–295° des de 0,5 px.
6. **Descartat:** la separació conjunta corona/relleu. El soroll de cada fotograma arran de la vora (~0,1 en ln L) la fa inviable (doc. 174 §6).
7. **Màscares dels filtres** (doc. 175): ⛔ no emmascaris un filtre amb la seva pròpia imatge.
   - En Multiplicar és cec al signe, i en Superposar el detall queda a la meitat i asimètric.
   - Les zones negres les fan la NRGF 41/42 i la 56: s'han de curar dins d'aquestes capes.

## 1f. Estat al 26-09-2026 (tarda): la V105 (llegeix-ho primer)

La V105 (`1-PHOTOSHOP/V105.psb`, candidata; informe `4-RESULTATS/v105_limbe_20260926/RESULTAT.md`, recerca `3-RECERCA/173_…`, codi `3-RECERCA/tools/v105_limbe_20260926/`, traspàs `.coordination/HANDOFF_2026-09-26_V105.md`) és la V104 de Pere amb tres canvis: una capa 305 de detall tangencial observat, la 56 amb la resolució que segueix el S/N a la franja de banda, i la 303 oculta.
1. **La tira llisa arran del limbe no és falta de dada.** La base (la de la V96) hi és llisa, i els filtres no arriben al pes ple fins a DMIN + 2–3 px. Mesura-ho amb la transferència τ (regressió del detall tangencial del compost sobre el detall observat, per d i sector), no a ull.
2. **Detall arran del limbe: TANGENCIAL i fotograma a fotograma** (`c1`). ln L de cada fotograma menys la seva mitjana al llarg de l'arc, només on el fotograma veu el píxel a una D_real mínima. La PSF s'anul·la al llarg de l'arc i la mitjana és zero: no hi pot haver cap anell.
3. **Guany (`c2`):**
   - només el que falta perquè l'ENERGIA de textura arribi a la de just a fora del forat dels filtres;
   - porta de fiabilitat ABSOLUTA de ρ entre grups independents (0,35→0,80; el p95 dels nuls és ≤ 0,30); ⛔ no la normalitzis per la ρ de referència, que també cau als nuls;
   - menys guany sota la vora translúcida de la Lluna 258;
   - mitjana zero imposada també als píxels del llenç;
   - DMAX 12 px.
4. **⛔ Prova «Lluna o corona» abans de mostrar detall als primers px** (`m1_fraccio_lunar.py`): dos grups de fotogrames amb la Lluna desplaçada; la corona queda fixa i el relleu lunar es mou.
   - A 195–295° els primers 2–3 px són relleu lunar: la capa no hi entra.
   - La ρ entre meitats NO ho discrimina.
   - Contrasta-ho amb el jutge Brno (`m2_jutge_brno.py`, correlació del detall AFEGIT).
5. **La filera de punts foscos a ~3 px** és soroll de la franja de banda (2–3 fotogrames, ×2,2) que la WOW blanqueja. Cura a l'entrada de la 56: promig per S/N sobre G/P, només escales 0–2 (`fila/reprodueix_REC.sh`).
   - Descartades: la potència al llarg de l'arc (no treu els punts), el promig isòtrop (anell de l'1,5 %) i atenuar escales (contra la norma).
6. **Trampes:**
   - per substituir un canal d'un PSB desat, parteix del canal REAL del PSB: l'`estat_*` guarda els valors d'abans de la quantització del Photoshop;
   - la 303 de Pere és opaca i és a sobre de tot;
   - l'ajust «Claridad y borrar neblina» és no local (≤ 78 DN lluny).

## 1e. Estat al 26-09-2026 (matinada): la V103

La V103 (variant **D**, rampa 2,75→3,75 a dalt: nivell validat ≤ 2 %) i la V104 (variant **E**, rampa 2→3 a dalt: tot el detall que la dada permet, ±4 % de nivell a 2,25 px) són la V101 amb els 16 filtres refets sobre una linealitzada que arriba més a prop del limbe, i la capa 302 oculta (informe `4-RESULTATS/v103_banda_20260926/RESULTAT.md`; recerca `3-RECERCA/172_…`). Codi a `3-RECERCA/tools/v103_banda_20260926/`: `cadena_v103.sh <variant> [des_del_pas]` (`LLIURA=D` per als passos 9–10 de la V103; `lliura_v104.sh` per a la V104). Sota els 2 px no hi ha corona recuperable amb la silueta d'ordre 2.
1. **On es perdia el detall:** a l'ENTRADA dels filtres. La franja a3c (V99) només admet un fotograma que vegi el píxel a ≥ 4 px del seu limbe real; al costat d'avanç de la Lluna cap fotograma no ho compleix als primers 4 px. No era cap apilat que ignorés la Lluna (b2 i a3c la tenen per fotograma).
2. **`a3d_franja_banda.py`** = a3c + **règim de banda** només on el net no arriba (porta g = 1 − smoothstep(n_nets, 1, 4)): els **11 fotogrames de l'instant** (|t − 18,43 s| ≤ 4 s) que veuen el píxel a D_real ≥ lo, amb rampa per PA (**2,75→3,75 a dalt, 3→4 a l'esquerra i baix-esquerra**), cadascun dividit per la seva **T de vora per classe i canal, mesurada al mateix conjunt a la dreta contra els tardans nets** (t > 40 s) i **validada creuadament i post-matriu** (G′, L′): ±2 % a 2,75 px, ≤ 0,6 % des de 3,25. Pes·T². Sense T (variant C) surt una tira fosca de −2…−8 %. ⛔ La T és una calibració EMPÍRICA transferida de la dreta a dalt i a l'esquerra (Codex): declara-ho sempre com a hipòtesi; per fer-la vigent cal validar-la amb l'apilat complet (rampes, T², pesos, barreja) sobre sectors reservats i amb transferència injectada.
3. **Qui mana a la banda:** el pes LDIC ∝ exposició: el 1/125 s porta el 62–69 %, el 1/500 s el 15–17 %; fotogrames efectius 2–3. Les meitats han de ser fotogrames DIFERENTS (1/125 contra 1/500), no parells/senars de la mateixa classe.
4. **Jutges nous:** `j17_banda.py` (cobertura per sector, residu a la transició 4,5–6,5 px contra el nul de la V99, costura banda − net només on el net domina (g ≤ 0,5), |V103 − V99| on tots dos tenen dada = 0); `r7_laminas_franja.py`; el diagnòstic `diag_banda.py` (rms i ρ de meitats per calaix de D) i `t_instant.py`.
5. **Trampes:** un «graó» a 2–4 px respecte de la recta de 6–12 px és curvatura real; la interpolació lineal en polar barreja els zeros de fora del domini (veí més proper); un comptador NF sobre el denominador acumulat menteix; `rm` amb un glob buit en zsh avorta TOTA l'ordre (`setopt nullglob`).
6. **Decisions de Pere:** baixar a 2→3 a dalt (variant B: ±4 % a 2,25 px); sota els ~2,75 px cal la silueta real a dècimes (relleu, LOLA); la base arran del limbe continua sent la de la V96.

## 1d. Estat al 26-09-2026: la V100

La V100 → **V101** (`1-PHOTOSHOP/V101.psb`, la vàlida; informe `4-RESULTATS/v100_detall_20260925/RESULTAT.md`, recerca `3-RECERCA/171_…`) és la V99 + UNA capa, «Detall real de la banda · V100» (Superposar, damunt de la 56 i sota la 258). Codi a `3-RECERCA/tools/v100_detall_20260925/`:
- `d29` (dada: primerencs amb D_real ≥ 2 dividits per T);
- `d35b` (capa: detall tangencial amb guany de veritat);
- `d36`, `d37b` i `v4` (contrast igualat en transferència);
- `b2_munta_v100` (insereix una capa en un PSB sense tocar res més);
- `desa_natiu.sh` (Photoshop, desar com a còpia);
- `v2` (verificació).

Regles noves:
1. **Detall arran de la vora: només TANGENCIAL**, al llarg de l'arc a d fix; la mitjana és zero per arc, i així no pot fer cap anell. El guany de cada escala és el pendent contra la VERITAT (d38), i zero per sota de D_real 2,75 px.
2. **El nivell de la banda no es calibra:**
   - T canvia amb l'època (d30);
   - KLL té un gradient degenerat (d31, d32);
   - els curts no es calibren amb guany + negre (d33).
3. **Guarda per observació, no pel màxim del píxel.** Mitjana local zero imposada al contingut final (d40). Res on manen les capes de Pere.
4. **Contrast: igualar la transferència** (el pendent de dada a compost), no l'energia de textura. Es mesura amb renders de prova, perquè Superposar i les capes d'ajust de Pere no es poden deduir. La regressió ha de ser robusta, perquè les protuberàncies l'enganyen.

## 1c. Estat al 25-09-2026 (vespre): la V99

La V99 (`1-PHOTOSHOP/V99.psb`, informe `4-RESULTATS/v99_banda_20260925/RESULTAT.md`, recerca `3-RECERCA/170_…`) només canvia la corona arran del limbe de la V98. Codi a `3-RECERCA/tools/v99_banda_20260925/`, punt d'entrada `cadena_v99.sh <variant>` (la variant lliurada és la B; el `CONFIG.env` de cada variant diu la silueta i les rampes).
1. **⛔ La Lluna observada NO és el cercle del model.** És una el·lipse d'~0,8 % (±1,9 px en horitzontal; sembla refracció amb el Sol baix) amb el centre desplaçat (−1,1; +0,8) px, comuna a tots els fotogrames i estable. La vora real respecte del cercle és: dalt −0,5, esquerra +3,5, baix −2,2, dreta +1,3 px. Silueta d'ordre 2: `D21_silueta_o2.npz` (d21; validació per blocs; l'ordre 4 no millora).
2. **`a3c_franja_silueta.py`:** l'a3b de la V98 amb D_real = D_model + DR − e(PA_j), on PA_j és l'angle respecte del centre del model d'aquell fotograma (cercle exacte: centre = p − (D+R_model)·∇D). Rampa comuna 4→6,5 px sobre D_real. Cap correcció fotomètrica: la variant A amb transmissió (TCORR) està descartada.
3. **Amb D_real, el dèficit de vora de tots els sectors col·lapsa** (curts −5…−16 % a 2 px, 0…−4 % a 4). El dèficit «per sector» de la V98 era geometria.
4. **La porta:** exclusió a la dreta (d23) i inversa a dalt i a l'esquerra (d25), sobre el verd i la lluminància POST-MATRIU (el que llegeixen els filtres), |biaix| ≤ 2 %.
5. **Banda que queda:** dalt 3,4–4,2 px (V98: 5,0–5,7). Baixar-ne demana calibrar la transmissió (±2–5 % entre sectors) o curar a la base els fotogrames de 1/3200 i 1/2000 s, que estan descalibrats en color (d26/d27). Decisió de Pere.

## 1b. Estat al 25-09-2026: la V98 (llegeix-ho abans de la resta)

La V98 (`1-PHOTOSHOP/V98.psb`, informe `4-RESULTATS/v98_20260925/RESULTAT.md`) canvia quatre coses de la V97. Tot és a `3-RECERCA/tools/v98_20260925/`, amb un sol punt d'entrada, `cadena_v98.sh` (parteix dels apilats de `cadena_v97.sh`).
1. **La corona arran del limbe amb SELECCIÓ FÍSICA per fotograma** (`a9b_limb_frames_comuna.py` + `a3b_franja_neta.py`), en lloc de la franja d'un instant (11 fotogrames suavitzats, que feia la «lupa»). Per a cada píxel, tots els fotogrames Vixen que el veuen net: pes × smoothstep de la distància al SEU limbe observat (curts 6→9 px, mitjans 5→8, llargs 6→10). On cap fotograma no el veu net (dalt i esquerra, ~5,7 px), NO HI HA DADA. Doc. `3-RECERCA/169_…`.
2. **La fusió b3 sense el residu local A→B de la Sony** (`b3d4_v98.py --b3-sense-residu-local`): el graó diagonal no s'havia curat a la V97, s'havia desplaçat (de 430 a 990 px de la vora del camp). Porta: `d8_diagonal_perfil.py` (perfil perpendicular a la vora del camp; cap pendent > 3 ‰ en 60 px fora de la vora).
3. **Els operadors a la vora de la dada** (`f3_filtres_v98.py`): MGN i ACHF isòtrops amb mitjana local d'ordre 1; ACHF azimutals amb ordre 1 al llarg de l'arc (`angular_polar1.py`) i alfa amb fosa de 4 px a la vora; RHEF local amb parells simètrics i ≥ 200 mostres (`rhef_local_sim.py`) i els 2 primers px al nivell (1→3 px); RHEF amb la fosa de r_in a 64 px; WOW sense la «vora difuminada»; el nivell del buit (Multiplicar) es calcula a 2–8 px de la vora; la vora de l'alfa és max(DMIN, 0).
   - **Prova discriminant de vora** (`d13_vora_operador_o_dada.py`, i l'opció `--retalla-vora N` de f3): retalla N px la dada; si el vorell es desplaça amb la vora, és de l'operador; si es queda, és de la dada.
4. **La Lluna neta** (`r3_estat_v98.py`): als 16 filtres, alfa 0 i màscara 0 dins del cercle de presentació on la Lluna de Pere (258) és opaca i a tot 150–210°; a la vora translúcida de dalt i baix, el nivell de les capes en Multiplicar hi continua (si no, línia clara).

Jutges nous: `j13_pentagon_factorial.py` (pentàgons), `j14_anells_lupa.py` (anells a 1–9 px i «lupa» per capa), `j15_compost_limbe.py` (compost al limbe), `j16_arcs_llunyans.py` (arcs centrats al Sol), `d8`, `d9` (dèficit a les primeres files), `d12` (guany per fotograma). Làmines de les marques de Pere: `r4_laminas_marques.py`.

## 2. La cadena V97, pas a pas

> **⚠️ Estat (25-09, després de l'auditoria):**
> - **La cadena no s'ha fet córrer mai d'una tirada.** La V97 es va fer pas a pas, a mà, i `cadena_v97.sh` es va escriure després. Abans de refiar-t'hi, fes-la córrer sencera en una carpeta nova i compara'n els SHA amb els de la V97.
> - **El pas 5, amb `--compara-v96`,** necessita que `v96_ref/` existeixi. Fes abans `r2_extreu_v96.py` (pas 7).
> - **El veredicte `j9`** només pot jutjar A3 (el render natiu) quan hi ha les vistes del pas 10.
> - **Els scripts de `cadena_raw/`** exigien un claim viu amb `claim_id` = `CLAUDE_REFUNDACIO_V97_20260924` (la constant `CID`); des del 30-09-2026 `a4_sources.guard()` ja no el comprova.
> - **Les rutes de sortida** són fixes (`4-RESULTATS/v97_refundacio_20260924/`). Per a una V98, copia la carpeta de codi i canvia-hi `RES`/`O`.
> - **Les opacitats** són en l'escala de Photoshop 0–255: la taula del §3 les dona en %.

Una sola ordre, des de l'arrel del projecte: `zsh 3-RECERCA/tools/v97_refundacio_20260924/cadena_v97.sh [des_del_pas]`.
- Cada pas escriu a `4-RESULTATS/v97_refundacio_20260924/` i se salta si la seva sortida ja existeix.
- Durades al Mac de Pere (16 nuclis, 64 GB).
- Els scripts són a `3-RECERCA/tools/v97_refundacio_20260924/`.

| pas | script | què fa | durada | porta: valor esperat |
|---|---|---|---|---|
| 0 | `cadena_raw/a2_calibration.py`, `cadena_raw/a10_run_baseline.py` | Calibració dels RAW (pedestal, darks, flat radial, dither de la Sony); apilats LDIC per tren i apuntament (Vixen, Sony A, Sony B); fusió V42; fonts sense estrelles d4; caixa lunar per fotograma. És una còpia literal de la cadena V85 de Codex, amb els paràmetres congelats de `2-ARXIU/.../raw_replay/` | 13 + 11 min | Cada etapa escriu `COMPLETE.json` amb `PASS: true` i compara els SHA amb els congelats (bit a bit). Si un SHA no quadra, atura't: algú ha canviat una entrada |
| 1 | `cadena_raw/b2_v97.py vixen --finestra comuna --vora taula` | La Vixen amb UNA finestra LDIC per cel·la Bayer: el sostre, pel subpla més exposat; el terra, pel G | 2,5 min | `j2_poligon.py`: ràtio ≤ 1,8 i salt ≤ 0,002 (V97: 1,63 i 0,0012; amb `--finestra canal`, 3,25 i 0,0154). Prova de port: `--finestra canal --vora taula` ha de donar el SHA `de3515dc…` |
| 2 | `cadena_raw/b3d4_v97.py --vixen … --b3-local-esvaeix` | La fusió dels trens (b3), amb el residu A→B de la Sony que s'esvaeix fora del solapament, i les fonts sense estrelles (d4) | 2 min | `d1_grao_sony.py`: \|graó\| ≤ 0,5 ‰ (V97: 0,03 ‰; control: −3,2 ‰). Sense opcions, ha de reproduir el control (tots els SHA iguals) |
| 3 | `a3a_franja_un_instant.py` (`V97_SORT`, `V97_FONTS`) | La franja escombrada per la Lluna, amb dada d'un sol instant (t ≤ 22,3 s): la recepta V88 | 1 min | Sobre el control, idèntica a `4-RESULTATS/v88_20260923/A3A_franja_un_instant.npz` |
| 4 | `f2_lineal_v97.py` | La linealitzada V97 (la d4 amb la franja). És la MATEIXA per a la base i per als filtres | 1 min | `LINEAL_REBUT.json` |
| 5 | `f2b_base.py --espai assigna`, `f2c_base_limbe.py` | La base (capa 3), amb la recepta b4e: L = (R+2G+B)/4; corba 0,74 + 0,22·log10(L/70736,47); color per ràtios σ24; valors sRGB assignats; espatlla s75c90. Arran del limbe (< 150 px, amb fosa fins a 250), la base de la V96 | 10 s | Sobre el control, amb `--compara-v96`: diferència mediana 0 i p95 ≤ 2 DN16 a 1,3–6 R☉ |
| 6 | `f3_filtres_v97.py E1 E6 E4 E3 E2` (en paral·lel) | Els 16 filtres (taula del §3) | 9 min | Cada etapa escriu `F3_E*.json`; el pas 8 els jutja |
| 7 | `r2_extreu_v96.py`, `r3_estat_v97.py` | La versió anterior en ràsters (la referència) i l'«estat» nou: base i filtres nous, i la resta idèntica | 2 min | — |
| 8 | `j0_jutge.py`, `d1`, `j2`, `j7`, `j9_veredicte.py`, `j10`, `r4_laminas.py` (a més, `j11`: el soroll de la finestra; `j12`: la fosa de la base al render natiu) | El jutge (§4), el veredicte i les làmines | 3 min | Vegeu el §4. **Mira les làmines tu mateix**: el 24-09, la base nova arran del limbe passava les mètriques, però a la làmina era clarament blanquinosa |
| 9 | `b2_munta_v97.py` | El PSB de pas: la V96 byte a byte, amb la base i els filtres substituïts i la base anterior oculta com a referència | 1 min | Reobre el PSB i el compara canal a canal (asserts) |
| 10 | `b3_desa_natiu.jsx` (via `corre_jsx.sh`), `p6_compost_fusionat.py`, `porta_photoshop.sh` | El Photoshop el desa COM A CÒPIA a `1-PHOTOSHOP/V97.psb` i en fa les vistes | 3 min | p6 `PASSA`; porta `OBRE 10551 px x 7506 px · 39 capes`; cap retall RGB nou al render natiu |

## 3. Els filtres (pas 6) i les seves regles

| capa | filtre | mode (V96) | com es fa a la V97 |
|---|---|---|---|
| 41 | P01 NRGF | Multiplicar 39 % (99/255) | Anells d'1 px centrats al Sol. Els anells interiors parcials (r < r_in = 469) es completen amb el patró azimutal dels 40 anells complets |
| 42 | P01b NRGF «estès» | Multiplicar 14 % (36/255) | La mateixa NRGF, amb el seu rang de pantalla (la μ i la σ log-lineals de la V58 feien el cercle a r_in) |
| 43/44 | RHEF, RHEF Υ 0,35 | ocultes (12 % i 16 %) | CDF per anell. Als anells parcials, la CDF de z dels 40 anells complets (fosa a r_in ± 4 px) |
| 45/46 | RHEF local 60°/30° | Multiplicar 3 % (8/255) | CDF per sector a radi fix, només amb dada |
| 47/48/49 | ACHF angular r0/r4/r8 | Superposar | Pas alt al llarg de l'arc a cada tren (convolució normalitzada), amb els pesos Vixen/Sony |
| 50/51/52/53 | ACHF isòtrop 01/04/05/06 | Superposar (la 51 visible, al 8 % = 20/255) | **Sobre el ln de la LLUMINÀNCIA**, mai canal per canal (el color hi feia el polígon) |
| 54 | MGN | Diferència (oculta) | Només sobre el domini (convolució normalitzada) |
| 55/56 | WOW / WOW bilateral | Superposar 3 % / 37 % (8 i 94 /255) | L'operador V95 (parells simètrics, vora difuminada, centratge per escala), amb la rampa de completesa de les escales gruixudes a **0,6 → 0,995** (amb 0,95 feia els arcs lila de la V95) |

**Regles comunes:**
- entrada NOMÉS de dada: el domini és el suport fora del disc de presentació, més la franja d'un instant;
- cap continuació;
- al buit, el nivell (Multiplicar) o transparent (Superposar i Diferència);
- alfa del domini, amb una fosa d'1,5 px;
- les màscares de Pere, sense tocar;
- el rectangle sencer.

## 4. El jutge (pas 8) i els valors de referència

`j0_jutge.py <estat> <font_lineal> <sortida.json> [--contra <estat anterior>]` mesura sobre el compost emulat per sota de la capa 234 (sense les capes d'ajust de Pere) i sobre cada filtre:
- **A2:** el polígon B/G.
- **A4:** el cercle r_in, només als azimuts on la Lluna és a més de 20 px de r = 464.
- **A5:** les costures d'escala (la z de la derivada del contrast al mateix d, a tots els sectors).
- **A6:** la textura arran del limbe i els píxels amb alfa dins del limbe.
- **A8:** les línies al llarg del limbe (la fracció coherent en 60 px d'arc).
- **B:** la correlació del detall amb els quatre composts de Brno (capes 230–233), per anells.
- **D:** el gra relatiu al cel.
- **E:** la regressió contra la versió anterior.

`j9_veredicte.py` hi aplica els llindars (vegeu la capçalera del script).

| criteri | V96 | V97 | llindar |
|---|---|---|---|
| A1 graó de la Sony | −3,2 ‰ | +0,03 ‰ | ≤ 0,5 ‰ |
| A2 polígon (ràtio / salt) | 3,25 / 0,0154 | 1,63 / 0,0012 | ≤ 1,8 / ≤ 0,002 |
| A4 salt medià a r_in (42 / 43 / 44) | −0,006 / −0,004 / −0,005 | 0,000 / +0,001 / +0,001 | reducció ≥ 50 % |
| A5 costura del compost (z) | 3,46 | 1,91 | ≤ V96 (el pla demanava −50 %: −45 %) |
| A6 alfa dins del limbe (Superposar) | 126.720 px | 0 | 0 |
| B Brno (4 anells) | 0,552 / 0,760 / 0,324 / 0,023 | 0,548 / 0,761 / 0,319 / 0,023 | ≥ V96 − 0,01 (passa, però baixa una mica a dos anells) |
| D gra relatiu | 0,0139 | 0,0140 | ≤ 1,05 × |
| E regressió (predeclarada / neta, `j10`) | — | 0,971 / 0,991 | ≥ 0,99 |
| A3 retall al render natiu (Lluna, R) | 61 | 60 | cap de nou |
| A7 vora clara de la linealitzada | 30 % (control) | 1,4 % | ≤ 2 % |

Veredicte de la V97: passen 9 dels 11 criteris; A4 i E no passen. Amb el llindar estricte del pla (reducció ≥ 50 %), A5 (−45 %) i A8 (0 %)
tampoc no passarien. **`j9` surt amb codi 1 si algun criteri falla, i la cadena s'atura** (només continua amb `ACCEPTA_V97=1` i la justificació escrita al RESULTAT).

Les làmines (`r4_laminas.py`) són obligatòries: el limbe a 1:1 a quatre azimuts, la franja diagonal i el polígon.

## 5. Com es cura un artefacte nou (el mètode de la torre de Pisa, amb eines)

1. **Localitza'l** a la làmina o a la marca de Pere. Mesura'l amb una mètrica i un nul (una posició girada, o una vora desplaçada).
2. **Puja pis a pis** i mesura'l a cada sortida:
   - el fotograma (`limb_frames`);
   - l'apilat per tren (`b2_*`);
   - T0/T1;
   - la correcció A→B (`sony_A_corr_v42`);
   - la fusió, la d4 i el filtre.

   El primer pis on apareix és on neix. Exemple del 24-09: el graó diagonal no era a l'apilat de la Sony A (0,03 ‰), però sí a `sony_A_corr_v42` (−3,2 ‰). El feia la b3.
3. **Fes una prova factorial abans de canviar res.** Activa o desactiva cada causa possible per separat (p. ex. la finestra per canal o comuna × la φ original o zero). La causa és la que mou la mètrica.
4. **Cura'l al pis on neix**, com a opció nova del script (mai editant la còpia congelada). Comprova que, sense l'opció, el pis reprodueix el control bit a bit.
5. **Refés tots els pisos de sobre** amb `cadena_v97.sh <pas>` i torna a passar el jutge i les làmines.

## 6. Trampes conegudes (cada una va costar hores)

- **Els «pentàgons» dels ACHF azimutals = la finestra LDIC PER CANAL** (graó ≈ 0,1 % a una isofota de cada canal, barrejat al verd per la matriu de color; les isofotes són polígons). Qualsevol apilat, també els parcials (`limb_frames`), amb la finestra comuna. Doc. `3-RECERCA/168_…`.
- **No barregis fotogrames amb la Lluna a llocs diferents arran del limbe** sense descartar-ne la vora: cada fotograma té dèficit als primers px del SEU limbe. ⛔ **Mesura la distància des del limbe REAL** (la silueta d21), no des del cercle del model. Amb el cercle, la corba sembla canviar amb l'azimut (curts de +1 % a −57 % a 2 px); amb la silueta col·lapsa (−5…−16 %). La V98 va dir «no es pot calibrar» per aquest error (doc. 170).
- **La porta de biaix es fa sobre el senyal que llegeix l'operador** (verd o lluminància POST-MATRIU), no sobre el verd cru. El blau té la cua de dèficit més llarga (dispersió atmosfèrica), però la matriu el compensa en part.
- **Si tots els fotogrames d'un píxel veuen el limbe a la mateixa distància** (dalt, on la Lluna es mou poc en vertical), una rampa no rebaixa el biaix de la mitjana: jutja el biaix del resultat (Codex).
- **Els fotogrames de 1/3200 i 1/2000 s no quadren en color** (R −6 %, B −10 %; el verd té un excés als nivells febles). Al primer píxel d'una rampa només hi entren ells, i fa −2 a −3 % en lluminància. Pendent de curar als RAW (doc. 170 §4).
- **`cadena_vNN.sh <var> N` executa del pas N fins al final** (`pas()` compara DES ≤ N), no només el pas N.
- **Una franja de pocs fotogrames suavitzada fa «lupa»** amb la WOW i l'MGN: igualen el contrast per escala, i un gra gros i fluix s'hi veu com una ampliació.
- **Una mitjana local d'un sol costat (ordre 0) té el biaix del gradient**: a la vora de la dada, ordre 1 (pla local). Amb suport complet dona exactament l'ordre 0.
- **Els operadors d'anells centrats al Sol (RHEF local, ACHF azimutals) arran de la Lluna** veuen el suport d'un sol costat (la Lluna és 14 px a la dreta del Sol): parells simètrics, ordre 1 al llarg de l'arc. Encara hi queda un vorell al primer píxel de dada (doc. 169 §6).
- **Una correcció mesurada només en una zona (el residu A→B a A∩B) i aplicada a tota una dada fa un graó on s'acaba**, s'esvaeixi com s'esvaeixi. Mesura on és ara el graó, no on era (la D1 de la V97 mirava el lloc antic).
- **Alfa 0 dins de la Lluna a les capes en Multiplicar** fa una línia clara sota la vora translúcida de la Lluna de Pere (hi surt la base sense filtrar). Zero només on la Lluna és opaca.
- **`until ! pgrep -f "<script>"` no s'acaba mai** si el mateix shell porta el nom del script a la línia d'ordres: `pgrep -f` s'hi troba. Espera els fitxers de sortida, no els processos.
- **Un reemplaçament de text que hi posa un comentari** (`# …`) al mig d'una línia amb `;` comenta la resta de la línia (dues vegades a la V98: el nivell del buit i `w_out`). Revisa la línia sencera després de cada pegat.

- **La Paperera no és un magatzem.** El 24-09 es va buidar amb els apilats a dins. La cadena els regenera des dels RAW en 25 min, bit a bit (pas 0).
- **Una finestra LDIC per canal fa un graó de color a la isofota.** Cada canal canvia d'exposició a una brillantor diferent. Fes servir la finestra comuna. També cura el blau massa alt (+4,4 %) arran del limbe, que ve del vessament dels píxels vermells saturats a les exposicions llargues.
- **Una convolució normalitzada amb nucli truncat fora del suport fa un graó a ~4σ.** Una correcció no s'extrapola fora d'on es mesura: s'esvaeix amb la confiança (`smooth(gw, 0, 0.5)`).
- **La recepta de la base reprodueix la V96 amb els valors sRGB ASSIGNATS al document Adobe RGB,** sense conversió. Si els converteixes, et desvies un 1–3 %.
- **Arran del limbe, la base nova surt més clara i blanquinosa** que la de la V96 (la recepta sobre la franja d'un instant, contra les correccions V53–V56). Fins que no es validi una recomposició nova, es conserva la de la V96 a < 150 px.
- **Els ACHF isòtrops amb convolució normalitzada tenen un biaix de vora arran del limbe:** una banda fosca de −0,03 a −0,05 al filtre, un 1–2 % al compost. A la V96 era una banda clara de +0,1, feta amb la continuació inventada. Pendent: parells simètrics, com a la WOW V95.
- **Les mètriques d'anell al voltant del Sol veuen el buit de la Lluna,** desplaçada 14 px a la dreta. Exclou els azimuts on la Lluna és a prop.
- **El compost emulat no porta les capes d'ajust de Pere.** Mira també el render natiu (les vistes del pas 10): no hi ha d'haver cap retall RGB nou. L'«artefacte verd» de la V84 era el vermell retallat per la capa «Luz 1».
- **Els programes congelats arriben compilats.** Per pegar-ne un (la b3), canvia el TEXT abans de `literal_programs`.
- **zsh no parteix les paraules de `$v`.** Fes servir `v=a:b:c` i `${v%%:*}`.
- **Les capes ocultes 52 i 53 (ACHF isòtrops) tenen una costura NOVA a d ≈ 43 px** (z 15 i 10; a la V96, 2,9 i 3,8). Probablement és on s'acaba la franja d'un instant (45 px). Diagnostica-la abans d'encendre-les.
- **Codex (des del 25-09-2026): fes servir el pont.** `cd "$HOME/Desktop/Eclipse 2026" && ~/.pont/pont contrasta --tema <tema> "…"` va a gpt-6-astra (`estrategia`, xhigh; `pregunta`, gpt-6-sol), tria sol el Codex de l'app ChatGPT i manté el mode de només lectura. Des de `Downloads/Eclipse 2026` no hi ha ruta i s'atura. (El 24-09 el pont encara tenia gpt-5.6 i es va cridar Codex a mà.)
- **Un filtre de gran escala (la trama, fins al 12 % de r) no pot deixar els peus d'estrella neutres** (V119 → V120, Pere: «un petit artefacte fosc al voltant de l'estrella més propera al limbe, a les 6»). Al voltant, la trama valia +0,94 %, i el disc neutre es veia fosc. Als peus hi va el NIVELL de gran escala del voltant, amb convolució normalitzada a dues escales (σ 30 px a la vora i 120 px al centre dels peus grans, de fins a 206 px; el nucli de 4σ del σ 30 no hi arriba). Tampoc no hi pot quedar el cercle d'1–2 px entre el peu i la màscara que ve del pla polar reduït. L'ordit, que és detall de mitjana zero, sí que hi va neutre. Porta: salt dins/voltant ≤ 0,1 % a tots els peus (`v4_vistes_V120.py`, S20).
- **El κ dels filtres de testimonis es calibra contra el COMPOST COMPLET** (els ajustos de Pere inclosos), com el `V115_natiu` de la V117–V119. Contra la pila sense ajustos, el β surt un 12–20 % més baix i la capa canvia de força sense que ningú ho hagi decidit.
- **La 301 (cantonada del logo) torna la seva alfa de la recepta:** si la geometria canvia (vora del camp), l'alfa canvia amb raó. `regenera_301_v120.py` prova primer que la recepta sobre el render VELL torna exactament l'alfa del PSB vell (així l'alfa no és cap retoc de Pere), i llavors accepta l'alfa nova.
- **Claim als passos de la cadena: retirat el 30-09-2026.** La V120 i els mòduls comuns (`v97_comu.claim`, `comu_v108.claim`) ja no el demanen. Si copies un pas més antic (V119 o abans) que en porta l'`assert`, treu-ne la línia; a cada versió nova, canvia la ruta al `cadena_vNNN.sh` abans de córrer.

## 7. Decisions que són de Pere (no les prenguis tu)

- les estrelles de model de la capa 202;
- la cantonada inventada de la 255 (si canvien les capes de sota, es regenera amb `v86_neta_20260923/regenera_cantonada.jsx`);
- la μ i la σ modelades de l'NRGF;
- retirar la 42;
- el desplaçament de 5 px de la 224;
- ajuntar la 96 i la 224 amb la 76;
- la recomposició nova del limbe a la base;
- l'Earthshine per bandes (la V97 manté la V88; vegeu `4-RESULTATS/v97_refundacio_20260924/RESULTAT.md`);
- la llicència i la publicació del repositori;
- la banda que queda a dalt (~3,4 px): deixar-la, calibrar la transmissió o curar abans els curts a la base (doc. 170).

## 8. Mapa

- **Producte:** `1-PHOTOSHOP/V100.psb` (V99 + capa de detall real de la banda; candidata; la V96 és la vigent). Informe: `4-RESULTATS/v100_detall_20260925/RESULTAT.md`. Anterior: `1-PHOTOSHOP/V99.psb`, `4-RESULTATS/v99_banda_20260925/RESULTAT.md`. Anteriors: `1-PHOTOSHOP/V98.psb` (`4-RESULTATS/v98_20260925/RESULTAT.md`) i `V97.psb`.
- **Codi:** `3-RECERCA/tools/v99_banda_20260925/` (`cadena_v99.sh B`) sobre `3-RECERCA/tools/v98_20260925/` (`cadena_v98.sh`) i `3-RECERCA/tools/v97_refundacio_20260924/` (`cadena_v97.sh`, els apilats).
- **Paràmetres congelats:** `2-ARXIU/reconstruccio_compactacio_20260915/raw_replay/`.
- **Normes i autoritat:** `IA/NORMES_I_AUTORITAT.md`.
- **Captura (Eclipse Command):** `5-CAPTURA/`, amb el contracte a `.coordination/arxiu_context_20260915/CLAUDE.md`.
- **Skills germanes:**
  - `apilatge-imatges-eclipsi`: l'apilat genèric;
  - `corregeix-artefactes`: la història d'artefactes V26–V96. Algunes de les seves recomanacions ja estan superades (vegeu la seva capçalera).
