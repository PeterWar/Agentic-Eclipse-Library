# 119 — CapesTotalsV15: el llenç estès i la capa dels 8 segons de la Sony

Encàrrec de Pere (28-08-2026, matinada): «fes la V15 basant-te en la V14 [on ell acabava de
modificar la capa 01], augmentant el tamany del llenç i afegint les imatges stackejades per
temps d'exposició de la Sony — les de 8 segons». Continua `research/118`.

Lliurable: `CapesTotalsV15.psb` (3,24 GB, **PSB**: amb el llenç nou el fitxer passa dels
2 GB del format PSD) + `CapesTotalsV15_REBUT.md` + `CapesTotalsV15_vistes/`, al costat de la
V14, que queda intacta. Eines: `research/tools/capes_totals_v14/{fes_v15,comprova_v15,
vistes_v15}.py`.

---

## 0. Resum en cinc línies

1. **Llenç 7648×5353 → 14572×14196**, estès fins on arriba TOTA la dada dels dos fotogrames
   de 8 s de la Sony (no fins al llenç comú de la cadena, que la retallaria): composem
   directament del RAW, o sigui que el retall del llenç comú no obliga (§2).
2. **Les 12 capes de la V14 van byte a byte** (la capa 01 que Pere havia modificat
   inclosa): l'únic que canvia és el rectangle (+3387, +5109). Porta de fidelitat per
   SHA-256 canal a canal (§3).
3. La capa nova és **la recepta exacta de les capes LDIC del run** `016_SONYTOT_CIENCIA`
   (`f4.psb_capes_ldic`): un fotograma de 8 s per apuntament (DSC06987 t=37 s, DSC06993
   t=70 s; la DSC06990 moguda és fora), màscara lunar per fotograma, coherència k=0,996,
   render declarat del run. **Dada de 2,77 a 14,87 R☉** (§2).
4. ⛔ **Els dos runs NO comparteixen `pa_north`**: el llenç comú és nord-amunt per a tots
   dos, però cada tren hi entra amb la seva rotació — pa(VIXEN) = 57,195°, pa(SONY) =
   90,27°. La diferència, **33,08°**, és la rotació entre trens de la calibració del 17-08
   (−33,2°). El primer esbós suposava pa compartit i «la rotació es cancel·la»: FALS (§2).
5. **L'alineació Sony↔V14 es verifica sobre el fitxer**: residual (+0,18, −0,17) px al
   solapament 3,0-4,2 R☉ — cap correcció necessària — amb l'honestedat declarada que la
   resposta de la correlació és feble (0,017) i l'autoritat és el registre de la cadena
   (`research/115`: acord entre trens 0,989) (§3).

---

## 1. Què s'afegeix, i d'on surt

Els fotogrames de 8 s del run SONYTOT són **dos**, un per apuntament (el salt de muntura de
`research/96` cau entre ells): `DSC06987` (t = 37 s, sol a (3667, 3480)) i `DSC06993`
(t = 70 s, sol a (3895, 2773)). Tots dos registrats pel MODEL de la cadena («correlacio
refusada», normal a 8 s: la corona interior hi és saturada i l'exterior és llis). La
`DSC06990` — l'àncora 2 d'earthshine, moguda perquè la muntura va cedir durant l'exposició
(`research/72`) — és als inservibles i ningú no la llegeix.

La capa es compon amb la maquinària del run (`f2.Ctx`, `plans`, finestra, màscara lunar per
fotograma, k de coherència) i es renderitza amb `comu.render_visual` i la corba declarada
del run (pendent 0,22, àncora 0,74, terra 0,045, àncora L del seu F3). **El cel no es
resta**, com a les capes LDIC germanes: la capa viu al mateix renderitzat que la resta.
Color lineal (norma del mosaic): R/G · B/G = 1,25 · 0,76 (3 R☉) → 1,07 · 0,84 (5) →
1,02 · 0,86 (8) — corona fonent-se en cel de crepuscle, com pertoca a X = 6,4.

⚠️ El forat central (saturació fins a 2,77 R☉ + disc lunar per fotograma) és transparent:
la V14 s'hi veu a sota. I el disc lunar d'aquesta capa **no és earthshine** — la composició
coronal emmascara la Lluna per fotograma; l'earthshine demana la pila registrada a la LLUNA
de `research/112` §7, que continua pendent.

---

## 2. La geometria: dos passos, els números de cada run

    V15 → sensor Vixen:   sx = X − padx − 285 ; sy = Y − pady − 355
    sensor → llenç comú:  d = A_vᵀ·(s − sol_vixen(572A2969))      [k_v = 1]
    llenç comú → RAW Sony: raw = A_s·(k_s·d) + sol_sony(fotograma)

amb A = [[cos θ, sin θ], [−sin θ, cos θ]], θ = −pa_north **de cada run**, i k_s =
2,1495/3,202 = 0,6713. **Un sol re-mostreig** (el llenç comú és només un marc intermedi de
coordenades; cap producte intermedi no es re-interpola).

El llenç nou surt de projectar les quatre cantonades de la zona vàlida del sensor de cada
fotograma a la graella V15 i englobar-hi la V14: **14572×14196**, pad (3387, 5109), Sol a
(7411, 7844). El camp Sony hi apareix girat 33,08° — les dues vores lleument desplaçades
del rectangle són els dos apuntaments.

---

## 3. Les portes

| porta | què | resultat |
|---|---|---|
| **A** | les 12 capes de la V14 **byte a byte** (SHA-256 de tots els canals), rectangles = original+pad, metadades iguals, la Sony a baix de tot | **PASSA** |
| **B** | residual Sony↔V14 per correlació (passa-alt, solapament 3,0-4,2 R☉) | **(+0,18, −0,17) px** · **PASSA** |
| **C** | el llenç conté la V14 sencera i tota la dada Sony | **PASSA** |
| **D** | obrible amb dos lectors (psd-tools + ImageIO), PSB versió 2 | **PASSA** |
| **E** | ⛔ l'obre el **Photoshop de veritat** (ExtendScript, sense diàlegs) — vegeu §5 | **OBRE 14572×14196 · 13 capes** · **PASSA** |

⚠️ Sobre la B: resposta 0,017 — feble, perquè compara la V13 tonificada amb el cel de 8 s.
El que afirma és «res no contradiu el registre de la cadena», no una mesura fina; s'ha
deixat el llindar de correcció a resposta ≥ 0,03 justament perquè una mesura feble no
mogui res.

---

## 4. Decisions declarades (i el que NO s'ha fet)

- **El nivell de la capa Sony és el render del run**, no la corba de Pere: la costura de
  nivell amb la vora de la V14 queda per a la seva corba sobre la capa — no s'ha cuit cap
  ajust per no decidir per ell. El lineal es conserva al cau de l'eina per si vol
  revelar-lo ell.
- Cap capa d'altres exposicions de la Sony (només els 8 s demanats); cap retoc a cap capa
  de la V14; cap correcció d'alineació (no calia).
- El format passa a PSB i **la fusionada continua en RAW** (mai ZIP a Image Data,
  `research/117` §7), RGBA amb matte blanc com la desa Photoshop.

---

## 5. ⛔ El «no compatible», la bisecció amb el Photoshop de debò, i la porta nova

**La primera V15 va sortir amb totes les portes verdes i Photoshop la refusava.** El
control de dos lectors (psd-tools + `sips`) té un forat estructural: psd-tools és el mateix
escriptor i `sips` només llegeix la fusionada; `exiftool -validate` i ImageMagick
`identify` també la donaven per bona. La bisecció amb el Photoshop de veritat (ExtendScript
via `osascript`, `DialogModes.NO`, obre→tanca sense desar) va aïllar el verí en tres
passes: la V14 re-serialitzada a PSB sense cap altre canvi ja REFUSAVA (X1); una
reproducció petita amb contingut propi OBRIA (el flip en si és net); i el flip sense els
blocs globals heretats OBRIA amb les 12 capes senceres (X2).

**El mecanisme, mesurat als PSB que Photoshop mateix havia escrit** (CapesTotalsV3b/V4b):
a PSB, Photoshop escriu els blocs globals `cinf` i `FMsk` amb signatura **`8B64`**
(longitud de 8 bytes) i `CAI `/`OCIO`/`GenI`/`Pat2` amb `8BIM` + 4 bytes. psd-tools ho
re-serialitza TOT amb `8BIM`, i als que posa longitud de 8 bytes (`cinf`, `FMsk`)
Photoshop hi llegeix 4 → es desalinea al primer bloc i refusa el fitxer sencer. A PSD v1
totes les longituds de bloc són de 4 bytes: per això la V14 (mateix contingut, v1)
s'obria, i per això la matriu del `research/117` §7 no ho podia veure.

**Les cures, totes dues aplicades**:

1. `fes_v15.py` treu els blocs globals heretats (tots menys `Lr16`/`Mt16` — metadades de
   sessió que Photoshop regenera) abans de desar;
2. **porta E nova i permanent**: `porta_photoshop.sh` — el fitxer l'obre el Photoshop DE
   VERITAT, sense diàlegs, i es tanca sense desar. És la porta final de qualsevol PSD/PSB
   del projecte: si no diu OBRE, no es lliura. (Amb Photoshop tancat o absent, la porta
   queda NO EXECUTADA i el fitxer no es pot declarar lliurable.)

Resultat final: **OBRE 14572×14196 · 13 capes**, i les cinc portes passen.
