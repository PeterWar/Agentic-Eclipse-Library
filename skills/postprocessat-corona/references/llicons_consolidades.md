# Lliçons consolidades del postprocessat 2026 — índex per no perdre res (16-09-2026)

Aquest fitxer és l'índex de les lliçons pagades entre el 15-08 i el 16-09-2026. Cada línia diu
la lliçó i on és l'evidència: `3-RECERCA/NNN` (documents a `3-RECERCA/`),
`trampes.md` (línia), `corregeix-artefactes`. Els ràsters intermedis s'han retirat el 16-09 per
ordre de Pere; els rebuts JSON, les notes i les vistes es conserven. Pere prioritza:
espai > aprenentatges documentats > skill; els scripts reproduïbles no són essencials.

## A. Normes de mètode (de Pere; manen sobre tot)

- **Causa arrel, mai cosmètica.** Cap suavitzat, retall o pedaç que amagui un artefacte sense
  curar-ne la causa a la font; la V33 és l'exemple del que no s'ha de repetir (3-RECERCA/149, 150).
- **Torre de Pisa: corregeix a la base, no a capes posteriors.** La capa 01 (10,3 s) de
  CapesTotals anava 1 px desplaçada al fonament i cada capa de sobre heretava la inclinació:
  s'arregla a la font (CapesExteriors/CT1), mai arreglant «en capes posteriors el que ja s'hereta
  de dins» (3-RECERCA/87 §2, 84, 86, 108 §taula «registre»).
- **Norma del rectangle.** Tot filtre a tot el rectangle, mai a una circumferència; l'exterior
  lleig es repara aigües amunt (3-RECERCA/93–95; `trampes.md` 332). Precaució de Pere 05-09:
  les retallades circulars fan més mal que bé.
- **Norma zero: jutge independent.** Cap correcció es declara bona sense un jutge no ajustat
  amb les mateixes dades; un tren que contribueix al compost és retenció, no independència
  (3-RECERCA/99, 105; `trampes.md` 3).
- **Brno és jutge, no font.** Cap píxel seu al producte; des del 28-08 també jutge de què és
  corona (`es_corona.py`; 3-RECERCA/105, 109, 114).
- **Control nul per a tota llista per llindar** (posicions girades); sobre gra correlacionat la
  falsa alarma és ~100× la gaussiana (3-RECERCA/125 §3 ter; `trampes.md` 1845).
- **Injecció cega 0,90–1,10 a la banda del senyal i vara única** entre versions; filtres per
  bandes en Fourier, mai diferències de gaussianes (3-RECERCA/127).
- **RGGB a cada resultat** (R/G i B/G al rebut; error recurrent), **llenç sencer** (cap vista
  retallada), **tot a Output** (`comu.vista()`/`lliurable()`), **vistes de diagnòstic a cada
  etapa i mira-te-les tu** (Pere hi troba defectes que cap porta veu).
- **Ajusta amb la dada que constreny**; si el defecte es mou amb un paràmetre del mètode, és del
  mètode (3-RECERCA/113, 116). Una coincidència de posició o de magnitud no és una causa
  (`trampes.md` 25, 1634).
- **Versions de filtres lleugeres** (07-09): mentre quedin artefactes, una base lineal + filtres,
  no el projecte sencer (9,6 GB per versió).
- **Avança sol, informa una vegada, parla planer, sense manuals** (06-08).

## B. Captura, calibració i color

- Pedestal real R6 III 512 pla; linealitat fins al 92 %; blanc Adobe R6 III 13995 (3-RECERCA/75, 78).
- Flats del mateix dia o dither: la mota de pols del R6 es va disfressar de cràter (31-08,
  3-RECERCA/116); el salt de muntura de la Sony ÉS un dither i mesura el flat sense flats
  (3-RECERCA/96; `trampes.md` 1596). Els flats girats 180° validen el flat Vixen (3-RECERCA/100).
- Temps d'exposició EXIF nominals (fins a −6,25 %, 3-RECERCA/99 §2); darks per mediana sense
  temperatura: deutes declarats de la cadena.
- Color: sense matriu la corona surt 2,6× massa blava; el groc és atmosfera; mode únic CIENCIA
  (0,9302 · 1 · 1,1261); MEMORIA deprecat (3-RECERCA/109, 110). La corona no és neutra
  (R/G 1,76, B/G 0,50) i el cel se separa per color, no per nivell (3-RECERCA/102, 103).
- La corba de to és un paràmetre declarat (pendent ~0,17–0,22/dècada), mai d'un percentil; el que
  encallava la maqueta V13 era la corba (3-RECERCA/108). Els halos eren un genoll de la corba (3-RECERCA/83).
- Captura 2027: escales monòtones entrellaçades, cada esglaó a dos instants, transparència cada
  ~10 s; Mission First i captura local sense LLM (3-RECERCA/46, arxiu CLAUDE 15-09).

## C. Registre i geometria

- Centre absolut = Sol per efemèride, mai el limbe (llisca 28,5 px durant la totalitat).
- ⛔ La geometria de V25/V26 estava girada 138,5° i cap porta ho veia: només la correlació
  AZIMUTAL amb control nul ho detecta (3-RECERCA/132; `trampes.md` 1966).
- L'apuntament B de la Sony va rotat +8,1′ (estrelles dobles); es passa explícitament
  (`delta_arcmin=8.10`, el default és zero) (3-RECERCA/160).
- Dos apuntaments de la Sony (750 px a mig de la totalitat): una sola causa per a cobertura,
  costura i graó (3-RECERCA/96). `pa_north` no és compartit entre trens (33,1°).
- Drizzle: cada pla Bayer va submostrejat 1,7× i la deriva ja és el dither (3-RECERCA/78).

## D. Composició LDIC i Lluna

- Una sola suma ponderada g = Σ w k f / Σ w; màscara lunar per fotograma (`w = 0` al disc de
  cada fotograma, una sola funció aplicada a tots els llocs que comparen) (3-RECERCA/112).
- ⛔ MAI `distance_transform` sobre un mapa de cobertura amb el forat de la Lluna (tres vegades:
  23-08, 04-09, 08-09; `trampes.md` 962). El forat lunar és la INTERSECCIÓ de les posicions
  (Lluna R 455,5 px moguda 28,5 px); la Lluna va a l'INICI; la franja de l'oest és cromosfera
  (3-RECERCA/155).
- Els artefactes residuals no eren la fusió: malla = cel per fotograma, corbes = anell verd;
  final = mediana sobre luminància (3-RECERCA/102, 107). El cel/corona és ×5 a 4 R☉: el cel
  aplana la corona (3-RECERCA/131).
- Perímetre lunar de display amb el fotograma SENCER (les tessel·les de ciència buiden el trànsit
  disc→glow) (3-RECERCA/128 §8). Només C2 per a les protuberàncies (unir C2 i C3 deforma el disc).

## E. Filtres i detall

- La resolució dels filtres segueix el S/N (`f3.suavitza_sn`, t = 0,18); σ = max(coherència
  entre trens λ/4, autocalibrada) (3-RECERCA/148).
- Anells del perfil radial: tota correcció per calaixos s'aplica INTERPOLADA; el perfil es fa
  en log r; mètrica = nivell per radi (porta H1) (3-RECERCA/111; `trampes.md` 851–883, 1733).
- Els cercles de NRGF/RHEF eren la vora del llenç; el taronja RHEF, el gradient del cel
  (3-RECERCA/147, 148). Els arcs de 3,2–4,6 R☉ eren el flat Sony ondulat imprès invertit
  (3-RECERCA/146). Les marques verdes de la RHEF no eren núvols: patró fix del sensor Vixen que
  camina amb la deriva (3-RECERCA/158).
- Guany per banda: llindar tou = 58 % del gra; Wiener regional + garrote k=3; l'estimador de
  meitats és invàlid als 16 px del forat; un jutge que pesa 0,37–0,44 al producte no és
  independent (3-RECERCA/156, 157). Pere refusa reduir soroll: «hi ha el que hi ha» (3-RECERCA/159).
- Capes ACHF saturades contra el forat des de V29 (3-RECERCA/154). Les estrelles surten dels
  filtres amb una capa de llum mesurada (V42, 3-RECERCA/160).
- Efecte 3D «Superposar» = detall × envolupant: dosar-lo, no automatitzar-lo (17-08).

## F. Earthshine i limbe

- Earthshine 2026 detectat amb els dos trens: r = +0,792 amb el mapa LROC (7σ), amplitud
  0,36 % del disc (3-RECERCA/126, 127). LROC és morfologia orientativa, no fotometria: no serveix
  per restar una taca (V68 taca taronja ampla: NO corregida).
- Brno evita el limbe (pes −1, un instant); el glow és l'ala de la PSF (3-RECERCA/161).
- Limbe V50–V53: tres vores que no coincidien (silueta 453,5 / forat 457,2 / alfa V44); cura a
  l'origen per nivells; 10 trampes (`comu import *` sobreescriu CAU/OUT, color 24 px, taper sec…)
  (`corregeix-artefactes/references/limbe_lunar_earthshine.md`).
- El revelat Camera Raw de Pere és una ENTRADA editorial (E02), no uns controls recuperables.

## G. PSB i Photoshop

- La fusionada mai en ZIP («no compatible»); el lector que valida no pot ser el que ha escrit
  (`sips -g pixelWidth`); `topil()` torna màscares 16 bits com a 8; signatura 8B64
  (`trampes.md` 55, 1794, 1811). `porta_photoshop.sh` amb el literal OBRE.
- Les capes de Pere byte a byte; cap re-mostreig; no reaplicar matrius a V67/V68; les capes
  06–12 anaven desplaçades ≈ (−12, −1) px des de V38 i una màscara comuna ho amagava (V42).
- V69.psb (16-09) és l'últim PSB de Pere: conservar tal qual.

## H. Coordinació i economia de tokens (16-09)

- Un claim per sessió i un traspàs al final; entrada curta (`ESTAT_CURT.json`); scripts que
  tornen veredictes; cap `cat` de fitxers > 8 KB; cap agent lector; cap flux massiu d'agents
  (117 agents = 21 % del pressupost setmanal, 02-09).
- Reproductibilitat (Codex 15/16-09): replays exactes fins a filtres V58 (rebuts
  `raw_replay/SUMMARY_*.json`); trampes: S4 V51 vs V52, D4→D4b, versió per productor a V29,
  E6 vs E1 locals, precisió de mtime_ns en JavaScript. Suspès per Pere: els scripts no són
  essencials; els replays s'han retirat com a duplicats exactes.
