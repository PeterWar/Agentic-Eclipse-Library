# 86 — CapesTotalsV1: la unió de l'HDR interior (V5) amb l'exterior i els filtres (20-08-2026, matinada)

Encàrrec de Pere abans d'anar a dormir: un sol projecte Photoshop, `CapesTotalsV1.psb`, amb
TOTES les capes de la més interior a la Sony — les 12 de `CapesInteriorsV5.psb`, les capes
exteriors amb les seves màscares, i a dalt els filtres en la línia de `FiltresSEMIFINAL10.psb`
— unides amb màscares sense cap artefacte, amb les perles, protuberàncies i limbe lunar
mantinguts com a la V5, i objectivament millor que `Benchmark20Agost.tif`. A mitja nit, ordre
addicional de Pere: la màscara de `03_1s` no estava acabada — repassar que protegeixi
protuberàncies, vora lunar i perles, i corregir-ho A LA BASE (res de torre de Pisa).

Lliurament: `~/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/CapesTotalsV1.psb`
(+ `LLEGEIX-ME_CapesTotalsV1.md` al costat). Codi: `research/tools/capes_totals_v1/`.
Xats font digerits sencers: «Filtres Drukmuller» (SF3→SF10) i «CapesInteriorsV4 màscares i
artefactes» (V4/V5), llegits un cop acabats, com Pere va demanar.

> **Avís de vigència (auditoria del 20-08, 12:13 CEST):** aquest document i el
> `LLEGEIX-ME` descriuen el fitxer lliurat de matinada, no el save que ocupa ara
> el mateix path. El fitxer actual té 36 capes, 2.370.519.442 bytes, SHA-256
> `4d0480f1d6508c225f5dbb13fb5c4e608d35a07b58acc2625853284ba48f2a28` i
> no conté `EDITAT PERE`; per tant no queda cobert pel rebut de 37 capes,
> 2,98 GB i prefix `f0ce3e8bf2606cf1…`. Cal revalidar-lo.

## 1. Les tres equivalències estructurals que ho fan possible

1. **`Aplicant_Filtres.tif` (la base de tots els FiltresSEMIFINAL) és exactament el compost de
   `CapesExteriors.psb`**: reproduïda la cadena sencera (03_1s → 02_2s → 01_10,3s → EDITAT PERE
   → 4 correccions Linear Light) en espai codificat, la diferència és ≤3/65535 a tot el camp
   fora del limbe. La capa «EDITAT PERE» és gairebé opaca pertot (màscara ≥0,93): el compost
   de Pere és, de fet, EDITAT PERE + correccions; les capes 02/01 de sota són quasi vestigials.
   **Conseqüència:** conservant la cadena exterior, els 15 filtres de la SF10 valen sense
   recalcular res (FLAT i HALO són LUT/deltes de la base; DETALL/RADIALS/MGN/NRGF v9 són de la
   lluminància; l'ANELL de la SF10 és zero per dins de 3 R☉ a propòsit).
2. **`Benchmark20Agost.tif` == compost de la SEMIFINAL10** (mediana |dif| ~2/65535: només
   arrodoniment d'exportació).
3. **El compositor extern reprodueix Photoshop**: espai codificat Display P3, màscares com a
   alfa, Normal/Linear Light/Overlay, i — trampa que va costar un ANELL de 0,197 — la
   **cobertura del bbox**: fora dels píxels d'una capa, Photoshop la tracta com a transparent
   encara que la màscara hi sigui oberta. Validat: SF10 sencera reproduïda a mediana 1,8 i màx
   11/65535 del benchmark; la V5 a 0,2/65535 del compost del xat V4.

## 2. L'acabat de les màscares de 04/03 (ordre de Pere) i les bombolles

Mesurat sobre la V5: la màscara de la 03 posava fins a un **22 % del fotograma d'1 s sobre la
protuberància** i un 5–17 % de vel sobre l'anell del limbe (04: 2–4 %). Aquest vel era la causa
de les **bombolles/festons del limbe inferior**: els discos lunars dels apilats d'1 s i 2 s
(centres que ballen ~3 px, radis 449,5–451,8) transparentant-se. Al benchmark quedaven amagades
sota el resplendor del compost antic; a la V5 nua es veien.

Acabat aplicat a la base: **màscara × (1 − P)**, P = anell centrat a la LLUNA (ple ≤~470 px,
rampa fins a 540) ∪ el·lipse estreta de la protuberància (70×100 px, ploma 0,35), tot amb
gaussiana σ 8 px. Contingut de capa intacte. Resultat: bombolles eliminades, perles i limbe =
capes protegides de sota, protuberància neta (canvi mediana 0,4 %).

## 3. Les tres capes radials noves (VORA, PONT, PERFIL) i el fossat

Treure el vel deixava un **fossat de −8/−15 % al voltant del disc** (440–540 px). El panell
extern del 20-08 — Codex 5.6 SOL xHigh (pont), Opus 5 xHigh, Gemini 3.1 Pro preview i Grok 4.6
(OpenRouter, visió) — el va declarar **unànimement artefacte** («collar negre»; físicament la
corona K és màxima al limbe), tot beneint la resta. La solució és la corba radial que
research/84 §5 ja beneïa («la brillantor es recupera amb una corba radial, mai amb les
màscares»), iterada dues vegades amb el criteri d'acceptació que va posar Opus:

- **VORA** (Linear Light, radial centrada a la LLUNA): porta la mediana per anell del candidat
  al nivell del benchmark des de **452 px** (la primera versió començava a 455+ i Opus/Codex la
  van refusar: el defecte vivia entre el limbe i ~1,15 R☉). Les bombolles **no poden tornar**:
  eren azimutals i la capa és radial pura. La finestra d'earthshine d'EDITAT PERE s'estén fins
  a 448 px (la franja negra earthshine↔limbe que Codex va assenyalar).
- **PONT** (Linear Light, radial solar): porta el perfil per anell del compost V5 al de la base
  des d'1,35 R☉ (sense això, V5 és fins a un 25 % més brillant/blava a 2–3 R☉ i el traspàs
  faria una banda de color).
- **PERFIL** (Linear Light, radial solar): porta el perfil radial del compost al del benchmark
  entre 1,28 i 3,0 R☉ (mediana per anell, suau) — recull el que els filtres Overlay amplifiquen
  diferent sobre l'interior nou.

**Acceptació final (D4)**: mediana per anell lunar-cèntrica dins **±3,8 %** del benchmark a
totes les anelles de 468 a 708 px (criteri: ±5 %), **cap mínim local** (l'anell 452–464 queda a
0,49 pel disseny: és la vora fosca real del disc travessant l'anell), test d'anells solar
1,09–8,5 R☉: **0,283 %** (benchmark 0,213 %; la resta és el limbe nítid real, no arrissat).

## 4. Arquitectura de CapesTotalsV1.psb (37 capes, 2,98 GB, SHA-256 f0ce3e8bf2606cf1…)

1–12. Les 12 capes de la V5, contingut byte-fidel; màscares de 04/03 acabades (§2).
13. VORA. 14. PONT. 15–21. Cadena exterior de CapesExteriors (02_2s, 01_10,3s op 68 %,
EDITAT PERE amb finestra d'earthshine, graó HDR, detall tangencial, extensió radial, cel pla),
cadascuna amb la màscara de Pere × porta radial smootherstep **1,35→1,95 R☉** (variant D del
panell: les textures treballades de Pere manen d'1,95 enfora — Codex i Grok la van triar sobre
la B, que allargava l'interior nou fins a 2,8 i era «massa tova»). 22–36. Els 15 filtres de la
SEMIFINAL10, contingut/màscares/opacitats/visibilitats tal qual. 37. PERFIL.

## 5. QA contra el benchmark

| Mètrica | Benchmark | CapesTotalsV1 |
|---|---|---|
| bombolles del limbe inferior | presents (amagades pel resplendor) | **eliminades de la base** |
| limbe lunar (mediana \|dif\| amb l'interior corregit) | ~8800/65535 | **86/65535** |
| perles/creixent | ~8400 | **481** |
| dins la Lluna | — | earthshine de Pere (= benchmark a ~1 %) |
| exterior ≥3 R☉ | — | = benchmark a ≤9/65535 |
| perfil lunar 468–708 px | — | dins ±3,8 % del benchmark, sense mínims locals |
| estructura azimutal r=1,3 | 68 | **107** (l'estructura real que les màscares velles aplanaven) |
| test d'anells 1,09–8,5 R☉ | 0,213 % | 0,283 % |

Veredictes finals del panell sobre la D4: **Codex: APTE** («collar i franja resolts; cap
defecte bloquejant; una línia lleugerament freda al S/SE al 100 %, no bloquejant» — mesurada:
el terminador és càlid a tots els sectors, R>B pertot; la «fredor» és la foscor del terminador
contra el resplendor). **Opus: NO APTE**, amb dos bloqueigs que els seus propis tests
objectius, executats, desmenteixen com a defectes de la unió:

- «pèrdua d'estructura fina a 452–620 px»: el rms del passa-alt (DoG 3–8 px) del candidat és
  ≥ el de l'interior nu de la V5 a totes les bandes (les capes radials no treuen alta
  freqüència per construcció; n'hi afegeixen via filtres). El dèficit respecte del benchmark
  (43–77 %) **ja és a la V5 nua**: és la decisió de research/84 — la «textura» extra del
  benchmark en aquella zona era en part empremtes de màscara (±10–18 % a 1,02–1,5 R☉) i el vel
  del fotograma d'1 s cremat.
- «taca fosca a les 10–11 h vora la protuberància»: el test de sectors azimutals (24 sectors ×
  anelles 452–620) dona desviacions del candidat **idèntiques a les de la V5 nua**
  (−29/+26 → −47/+34 % contra −28/+25 → −44/+33): és contingut protegit de Pere, no cap capa
  de la unió. El benchmark hi té menys desviació (−32/+11) justament perquè el vel aplanava.
- el «sagnat rosa al limbe»: l'arc cromosfèric real de la V5, que el vel antic emblanquia —
  contingut que Pere ha manat mantenir.

Tots dos veredictes i els tests queden a l'expedient; la decisió d'entregar amb l'interior V5
és de l'encàrrec de Pere (V5 com a base, perles/protuberàncies/limbe com a V5), i és
**reversible amb capes**: el contingut antic és sencer a EDITAT PERE (porta 1,35→1,95) — obrir
la seva màscara cap a dins retorna la textura antiga d'1,0–1,5 R☉ si mai es vol.

## 6. Deutes i notes

- Les capes amb **NoiseXTerminator** de Pere segueixen sense ser al disc (xat V4): quan les
  desi, refer la V5 (`compon_v5.py` + `escriu_v5.py`) i tornar a copiar l'interior a
  CapesTotals (o refer CapesTotals amb `construeix_capestotals.py`).
- `filtres_profunds_v9.py` del repositori encara té l'error d'unitats de la màscara del DETALL
  (la bona és `MASCARA_detall_SF10.tif`); `extreu_pixels_v4e.py` només viu al scratchpad de la
  sessió 47c293ed.
- **VORA, PERFIL i ANELL s'han de recalcular si es canvien capes, màscares o opacitats.**
- La «línia freda al S/SE» del dubte de Codex: és la vora fosca de la V5 (terminador); queda
  anotada per revisar-la al TIFF de 16 bits al 100 %.
- El detall fi interior (1,0–1,5 R☉) és deliberadament el de la V5, més suau que el benchmark:
  les «textures» antigues d'aquella zona eren en part empremtes de màscares (research/84 §2).
  Decisió coherent amb l'autoritat estètica del V4 editat de Pere; Opus ho hauria reinjectat,
  Gemini no — queda dit i és reversible (el contingut antic és a la capa EDITAT PERE, gated).
