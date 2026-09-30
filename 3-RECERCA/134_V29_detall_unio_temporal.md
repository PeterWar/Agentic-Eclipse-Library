# V29 — detall exterior, ghost i unió temporal de la corona

Derivat visual editable del 05-09-2026, sobre el mateix llenç de Pere.

## Fitxer i comprovació real

- PSB: `/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V29.psb`.
- 10551 × 7506 píxels, RGB de 16 bits, 25 capes, 4,223,401,864 bytes.
- SHA-256: `b5c2055b329305b7a8efe6f14159414b739da7a43077e8ba9b7b32288b4ac3ff`.
- Photoshop: **OBRE 10551 px x 7506 px · 25 capes**. Obert i tancat sense desar.
- Reobertura psd-tools: 20 capes originals preservades amb tots els canals comprimits, alfa, màscares, coordenades, modes i opacitats idèntics. Les cinc capes noves coincideixen exactament amb els ràsters i les màscares de construcció. El merged coincideix exactament amb la previsualització; la recomposició de capes reobertes difereix com a màxim 1 DN de 16 bits per quantització.

## Canvis A–E

**A — ACHF fi i corona exterior.** S'ha eliminat el tall que reduïa el filtre a zero a partir de 5 R☉. L'ACHF 2/4/8/16/32 i el passa-alt 24 treballen sobre ln TOTAL, amb normalització de contrast després del filtre, mediana de les realitzacions RGB vàlides, resolució contrastada per bandes i centrat H1. No es resten perfils radials abans del filtre ni s'apliquen les antigues osques direccionals globals. Això conserva resposta exterior sense identificar tot el gra de V25 com a detall solar.

**B — 03 ACHF azimutal i marques blaves.** La font Sony B és primària dins del seu camp; A només aporta les vores de cobertura o el camp que B no cobreix. Al ghost, el resultat és RGB idèntic a B en 1.200 × 1.200 píxels: desapareix el canvi circular de donant. El filtre ample final és angular: G8 − (G32 + G64 + G128)/3, amb sigmes expressades en píxels d'arc i convolució FFT periòdica. Cada tren es filtra amb la seva pròpia màscara abans de combinar-los. No s'introdueix la normalització fotomètrica entre càmeres dins del filtre ni es filtra deliberadament en radi. La interpolació bilineal de la graella polar continua sent una aproximació declarada. Les marques de Pere són finestres de verificació, mai màscares d'esborrat.

El judici independent amb el mateix operador angular dona Vixen–Sony r=0,365 al ghost (corroboració moderada), r=0,496–0,941 al SE i r=0,931–0,994 en moltes marques petites/NW. La fidelitat del nou gran a Sony al ghost és r=0,986. Els 161 cercles de control al voltant de 2 i 2,65 R☉ no detecten un anell additiu de la barreja: mitjana crua màxima 1,51×10⁻⁶ i 7,61×10⁻⁷. La taula completa i els límits són a `independent_review.json`.

**C — 04 ACHF ample 9R.** S'ha retirat: el seu desenfoc azimutal molt ample i el límit polar no aportaven una capa útil diferenciada. No hi ha una còpia oculta que es pugui activar accidentalment.

**D — Passa-alt 24 i ghost del fi.** Comparteixen la font Sony neta i recuperen cobertura exterior. Els filtres es conserven a amplitud completa dins del PSB. La força inicial resideix només en l'opacitat editable: ACHF fi 14.12%, passa-alt 7.84%, azimutal 14.90%, tots en Superposar. Aquesta escala inicial és una decisió visual; no s'han esborrat píxels de detall per aconseguir-la.

**E — Geometria i Lluna en moviment.** S'ha mantingut la transformació V27/V28 ajustada contra les capes de Pere, corregint la referència del centre a l'índex real de l'apilat. Centre solar del PSB: (5361.768112, 3775.747534); R☉=440.603048830 px. Les dades s'han recompost directament des dels plans CFA cap al llenç PSB existent amb una sola interpolació bilineal. No hi ha canvi de FOV, dimensions o retall. Base i detall utilitzen la unió real de la corona observada en les diferents fotografies; no un forat circular d'1,05 R☉.

El suport té 70,395,270 píxels i recupera 40,863 píxels dins d'1,05 R☉. La intersecció que sempre fou ocultada continua exclosa. El filtre ample G descarta només 3 píxels sense G positiu/finit en cap dels dos trens; el fi/PAL poden usar altres realitzacions RGB vàlides. El càlcul directe recupera 11.159.171 píxels respecte de l'antic rectangle intermedi. Només es modula la vora física exterior segons el suport del nucli del filtre: 96 px al fi, 72 al passa-alt i 384 a l'azimutal. No hi ha una amputació circular de la corona externa.

## Mesures i límits

H1 estricte: totes les medianes dels anells observats, inclosos els parcials del limbe i de les vores, es comproven sense excloure la franja recuperada. Llindar 0,05:

| Filtre | Màxim absolut de mediana − 0,5 |
|---|---:|
| achf | 0.004036 |
| passalt24 | 0.011414 |
| gran | 0.011421 |

Alineament solar amb Pearson real, control girat 180° i controls ±1° rebutjats:

| Filtre | Pearson a 0° | Control 180° | Pic residual |
|---|---:|---:|---:|
| achf | 0.610575 | -0.023599 | 0.00° |
| passalt24 | 0.615511 | -0.023137 | 0.00° |
| gran | 0.805394 | -0.055231 | 0.00° |

Les capes originals s'han auditades segons el seu marc: solar, lunar, estel·lar o comparació. L'antic `Fons per raig` té un pic feble desplaçat −0,75° i queda ocult com a font històrica; no s'ha girat a cegues ni es declara que totes les capes històriques passin el mateix control. La capa ampla antiga també fallava aquest control i s'ha retirat. L'alineament solar no s'aplica a earthshine, estrelles, LROC o perles com si fossin la mateixa referència temporal.

Les injeccions aparellades a la correcció Sony i els controls de transferència de la resolució passen: True. Els controls analítics angulars i el nul radial passen: True. Els controls angulars validen el nucli FFT; no certifiquen automàticament tota la interpolació ni tota textura fotogràfica.

**Avís que es manté:** H1b del passa-alt és 2.976, per damunt del llindar d'avís 2 (abans del darrer centrat: 2.159). No es declara resolt aquest avís espectral. No s'ha aplicat una osca global destructiva només per fer baixar aquest número. L'ACHF fi i l'azimutal tenen H1b 1.909 i 0.800.

L'evidència independent de 8–16 px a l'exterior és feble o nul·la en els controls estudiats. Les bandes de 32–64 i 64–128 px estan més ben corroborades segons el sector. La textura fina no es presenta íntegrament com a estructura solar demostrada. Usar B com a font primària redueix el nombre d'observacions combinades i pot augmentar el soroll respecte d'A+B; les dades d'A es conserven i aporten el camp descobert. Les capes són derivats visuals, no nous màsters radiomètrics acceptats.

La reproducció exacta de 11.794 píxels interiors recuperats en la graella comuna anterior queda a `cau/limb_receipt.json`: 301 tenien una única observació. Aquest recompte és d'aquella graella, no s'ha confós amb el recompte nou del PSB.

## Reproducció i evidència

Arrel de codi: `/Users/USUARI/Downloads/Eclipse 2026/research/tools/v29`. Branca de càlcul lliurada: `cau_final`, amb `V29_FINAL_GRID=1`. `cau` conté entrades congelades i diagnòstics previs; els pilots isotrops i de donant circular són rebutjats i no són V29.

Ordre principal: `prepare_final_grid.py` → `merge_pointings.py` → `coherent_resolution.py` → `fuse_and_filter.py --source-only` → `refine_detail.py` → **`gran_azimuthal.py`** → `build_canvas.py --base-only` → `qa_rasters.py`, `qa_transfer.py`, `qa_angular_controls.py` → `select_delivery.py` → `make_delivery.py` → inspecció visual → `package_psb.py` → `verify_psb.py` → `porta_photoshop.sh`. L'empaquetat del PSB impedeix sobreescriure un V29 existent; els scripts de càlcul sí que regeneren els NPY de treball. El centrat final és PCHIP amb els centres radials realment observats, 200 bins, extrems de pendent zero i mínimes passades fins al llindar declarat.

Entrades RAW i calibracions: runs Vixen 019 i Sony 016 d'`Eclipse determinista/1-RUNS`; geometria i cel preexistents declarats en els scripts. Els hashes dels scripts V29, dels PSB d'entrada i dels ràsters lliurats són a `delivery_manifest.json`.

Evidència de QA: `raster_qa.json`, `psb_verification.json`, `pointing_merge_receipt.json`, `gran_azimuthal_receipt.json`, `independent_review.json`, `transfer_receipt.json`, `angular_control_receipt.json`, `footprint_taper_receipt.json` i `passalt_spectral_warning.json` a `/Users/USUARI/Downloads/Eclipse 2026/research/tools/v29/cau_final`.

Previsualització real i panells 1:1: `/Users/USUARI/Desktop/Eclipse 2026/IA/output/v29_20260905` (`V29_…`). Els altres fitxers `PILOT_…` i `CANDIDAT_…` són evidència de treball.
