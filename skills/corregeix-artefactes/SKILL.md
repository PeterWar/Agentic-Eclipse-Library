---
name: corregeix-artefactes
description: >-
  Detecta i corregeix els artefactes recurrents del postprocessat de la corona (eclipsi 12-08-2026 i futurs) ABANS d'aplicar cap filtre nou i DESPRÉS de cada muntatge: ghosts del Sol a la lent (Sony, Sol descentrat), ratllat del patró fix del sensor, vores rectes de cobertura o d'extensions inventades, franja fosca o clara al limbe, anells del perfil radial, nivell per anell de les capes de detall (H1), i les marques que Pere pinta sobre un TIF (Artefactes.tif). Usa-la sempre que es parli d'artefactes, halos, anells, ghosts, ratlles, costures, seams, vores, marques de Pere, abans de filtrar, o quan un filtre de detall (ACHF, passa-alt, MGN, NRGF, Claridad, Textura) hagi d'entrar a un PSB.
---

## Porta de la torre de Pisa · 28-09-2026

Abans de promoure una correcció, llegir `IA/GUARDRAILS_POSTPROCESSAT.md` a l'arrel del projecte i executar la porta de mètode sobre el PSB efectiu. Els ràsters causants corregits han d'estar actius al seu lloc; tots els ajustos dependents s'han de recompondre. Cap compensació de compost o residual antic congelat al damunt, tampoc per conservar la presentació. Traçar totes les capes noves visibles i separar retoc manual, identitat del fitxer i validesa científica. El control negatiu V109 ha de fallar la porta. Una discrepància amb el compost manual antic s'exposa; no es resol saltant aquesta regla.

> **24-09-2026 (nit) · V97 · LLEGEIX PRIMER `postprocessat-corona` (la cadena V97 i el seu jutge).** Aquesta skill conserva la història d'artefactes
> V26–V96, però **aquestes recomanacions seves estan SUPERADES** (van contra la norma canònica o les ha substituïdes una cura a l'origen):
> - la continuació radial i el mirall de la textura a la vora de la Lluna (blocs V86, V88 i V92) → al buit, NOMÉS el nivell (Multiplicar) o transparent (Superposar);
> - el suavitzat radial dels filtres prop del limbe (bloc V90) → substituït per la treta de línies per coherència (V93) i, a la V97, per filtres sense continuació;
> - la «cantonada que es regenera» (V86) → la seva recepta inventa (reflecteix el gra): és una decisió de Pere;
> - l'«anell llis» o les franges interpolades → mai.
>
> Causes trobades a l'origen el 24-09 (V97):
> - el graó diagonal de la Sony (el «marró») neix a la b3, perquè el residu A→B s'estenia fora del solapament amb un nucli truncat;
> - el polígon B/G de la Vixen neix a la finestra LDIC per canal.
>
> Cures, diagnosis i trampes: `postprocessat-corona` §5–§6.

**⛔ NORMA CANÒNICA (Pere, 24-09-2026): res inventat, res reflectit.** Cap operació no pot posar píxels que no vinguin de dada observada: ni farcits, ni continuacions, ni extrapolacions, ni còpies radials, ni miralls, ni pull-push/Laplace, ni textures o models en lloc de dada. Només ho pot excusar una ordre explícita de Pere per a una cosa trivial. On no hi ha dada, es diu i no s'omple.


# Corregeix artefactes (abans de filtrar, després de muntar)

**24-09-2026 (nit) · V93:** al buit sense dada de la vora, NOMÉS el nivell (ni còpia ni mirall). Les línies es treuen per coherència al llarg del limbe, no suavitzant. La 76, la 96 i la 224 són a sobre de l'Earthshine. Les línies fosques rectes del camp exterior són unions de la Sony amplificades per la WOW. Vegeu la secció V93 de [les lliçons de la V90](references/v90_linies_limbe_suavitzat_radial.md).

**24-09-2026 (matinada) · V92:** si hi ha una «lent» fina arran del limbe, mesura l'estirament radial de la textura amb pas alt NOMÉS en azimut. Cap continuació no ha de copiar valors al llarg del radi: fes mirall de la textura. Una capa que suma llum porta el color de l'excés real. Vegeu la secció V92 de [les lliçons de la V90](references/v90_linies_limbe_suavitzat_radial.md).

**23-09-2026 (nit) · V91:** tota cura local (com el suavitzat radial de la V90) va NOMÉS on hi ha el defecte. Fora d'aquí, fa un defecte nou (la «lent»). Abans de desar amb Photoshop, torna a comprovar el SHA de la font de Pere. Vegeu la secció V91 de [les lliçons de la V90](references/v90_linies_limbe_suavitzat_radial.md).

**23-09-2026 (vespre) · V90:** si hi ha línies paral·leles al limbe i «no és cap capa», llegeix [les lliçons de la V90](references/v90_linies_limbe_suavitzat_radial.md).
- **La causa:** detall radial fals de TOTS els filtres arran del limbe.
- **La cura:** suavitzat NOMÉS RADIAL dels filtres prop del limbe (σ 4 px → 0 a 14 px, aplicat com a diferència), com fa Brno.
- **⛔ No funcionen:** les unions (continuacions, vora nova de la Lluna) fan línies noves, i l'alfa de la Lluna de Pere no es toca.
- **Hipòtesi Hα/verd:** refutada (mesura abans d'explicar).
- **Si «no és cap capa»:** amaga les capes d'ajust en una còpia renderitzada per Photoshop.

**23-09-2026 (tarda) · V88:** abans de tocar la franja d'un instant, la intensitat dels filtres arran del limbe o l'earthshine, llegeix [les lliçons de la V88](references/v88_cremallera_soroll_franja_i_earthshine.md).
- **Cremallera o pixelat arran del limbe:** abans d'abaixar cap filtre, busca'n la causa a la dada. Hi havia dues causes:
  - soroll d'un instant ~3 vegades el de la fusió → suavitzat σ 1,3 px abans dels filtres;
  - vora binària esglaonada → fosa suau sobre la distància analítica a una corba llisa, amb continuació radial.
- **Vora de l'earthshine:** si dues meitats coincideixen però LROC no, és llum dispersa, no Lluna. L'anell es deixa llis i l'interior és el de Pere.

**23-09-2026 · V86:** abans de tocar el limbe, les màscares lunars o la cantonada del logo, llegeix [les lliçons de la V86](references/v86_franja_un_instant_forats_i_cantonada.md).
- **La imatge final** és la pila per sota de PixInsight, i els forats es mesuren com a cobertura en aquesta pila.
- **La franja escombrada per la Lluna** s'omple amb dada d'un sol instant. Interpolar-la fa un anell llis.
- **La distància al limbe** es mesura des del limbe **observat** (el rebut de la cadena va al radi de l'efemèride, 2,5 px més enfora), amb una rampa de pes per fotograma i un nivell constant. La continuació parteix de 2 px dins de la dada.
- **Cada canvi va en una capa**, i la cantonada es regenera.

**22-09-2026 · Limbe mòbil i color de presentació:** abans de corregir verd,
WOW/MGN/ACHF o màscares lunars, llegir [les lliçons de V85](references/lunar_boundary_and_display.md).
Separar suport físic, domini del filtre i validesa de la seva sortida.
Les versions datades més avall són història; l’estat viu el fixen
`IA/ACTIVE.json` i el handoff de l’arrel del projecte.


**Estat 15-09-2026:** V68 general i Earthshine V56 són les referències de
Pere. La taca taronja ampla de V68 continua oberta; cap V69 ni cura nova.
LROC és una textura CGI de referència morfològica amb fotometria no equivalent.
Que una depressió aparegui en RAW dels dos trens no separa albedo, resposta
instrumental i llum dispersada. S8 altera senyal ample; arreglar el seu error
de mig sector no cura la taca. La recepta històrica de resta per sector de la
família E **no és una correcció general validada**. No la reapliquis a V68.
Encaix manual, màscares, alfa i Camera Raw de Pere són entrades protegides.
Vegeu `../postprocessat-corona/references/estat_i_reproductibilitat.md`.

Norma de Pere (04-09-2026), després de la V25: «els filtres són magnífics
però estan plens d'artefactes; fes una skill per corregir-los que s'executi
sempre abans de fer un filtre nou». Aquesta skill és aquesta rutina. Mòdul:
`scripts/artefactes.py` (detectors i correccions); ingestió de marques:
`scripts/marques_pere.py`. Exemple històric: `3-RECERCA/tools/v25_lineal/etapa4_munta_v26.py`.

**Precaució de Pere (05-09-2026): probablement les retallades circulars fan
més mal que bé: poden eliminar detall real de corona i crear halos, també
amb ploma.** No són una correcció per defecte. Aquesta norma substitueix les
receptes històriques de pedaços i esvaïments a radis fixos; conservar-ne el
codi o declarar-les al rebut no les valida. Llegeix «Retallades circulars» a
`../postprocessat-corona/references/normes_i_portes.md` per distingir un
retall arbitrari de la validesa lunar temporal i la cobertura física.

**Miniarcs concèntrics (V30, 05-09):** un filtre només azimutal pot estirar
el soroll tangencialment i convertir-lo en arcs curts. H1 verd no ho exclou.
Abans de reutilitzar aquest operador, llegeix
`references/miniarcs_i_anisotropia.md`: ablació de perfils, prova de soroll,
resposta injectada i jutge independent fix. La correcció es fa a l'operador
amb suport físic normalitzat, mai amb cercles pintats sobre les marques.

## Quan

1. **Abans** de calcular o d'inserir qualsevol capa de detall: la base ha de
   passar els detectors G, R, V, L i M; si no els passa, es corregeix la base,
   no la capa de detall (un passa-alt és un detector d'artefactes: tot el que
   la base té de dolent, el detall ho amplifica).
2. **Després** de cada muntatge, sobre la fusionada: M, L, H i, si Pere ha
   pintat marques, P. Declara detectors fallits, abast i limitacions; no
   inventis una correcció ni alteris el llindar per obtenir un PASS. Si la
   porta falla també a la referència, documenta la discrepància sense
   transformar-la en una validació. Lliurament revisable no vol dir absència
   global d'artefactes.

## Les famílies, per ordre d'execució

| codi | artefacte | causa mesurada | detector (`artefactes.py`) | correcció | on s'ha vist |
|---|---|---|---|---|---|
| **G** ghosts | taques rodones febles (100-500 px) al camp exterior; també a 3,0 R☉ | reflex del Sol a la lent de la Sony amb el Sol descentrat (primer apuntament): un ghost per apuntament a la posició simètrica respecte de l'eix òptic; ~8 R☉ el 2026 | `blobs_rodons` sobre la CAPA DE DETALL (a la base són <4σ) i sobre la base; DoG 40-140 px, >3,5σ, rodonesa >0,55 | identificar la font contaminada i aprofitar observacions netes de la mateixa zona celeste amb geometria validada; qualsevol exclusió es justifica per fotograma i conserva la dada vàlida alternativa. `tapa_blob` i els discs a 0,5 són recursos històrics, no una correcció automàtica | 3-RECERCA/116; V25 (3,0 R☉); V26 (sis marques de Pere a ~8 R☉) |
| **R** ratllat | ratlles diagonals al camp exterior, molt visibles al passa-alt | patró fix del sensor (Sony: −45° a la graella V23; Vixen: diagonal del sensor) | `ratllat`: pic espectral d'una finestra de 1024 px del detall; alarma si pic/anell > 30 | diagnosticar les famílies del sensor i validar la retenció de corona abans d'acceptar un `notch_direccional`; ni rampa radial ni esvaïment a 5→7 R☉ per defecte. El radi no demostra que només hi hagi cel | 3-RECERCA/113/116 (estriat); V26: 240× abans |
| **V** vores rectes | línies rectes, escales de to o de gra | fi de la cobertura d'un tren, extensió INVENTADA (per raig, constant), rectangle d'una capa | `arestes_rectes` (Canny + Hough ≥400 px) sobre el detall; i mirar-ho a l'ull | mai extensió sintètica: fora de cobertura hi va DADA (l'altre tren, o la capa de Pere) igualada en to en baixa freqüència (ρ radial × k≤2, finestra declarada) amb ploma ≥100 px; o llenç transparent | V25 (extensió per raig: refusada per Pere); V19 (cantonades) |
| **L** limbe | franja fosca o clara entre les perles i la corona | forat lunar de la cadena més gran que el disc de C2 (fins a 22 px); banda exterior d'una capa d'earthshine tonificada a un altre nivell; màscara de la base massa oberta | `limbe`: perfil per anells de 0,01 R☉ de 0,98 a 1,16; alarma si hi ha caiguda >0,03 seguida de pujada | màscara lunar real per fotograma i unió temporal de corona vàlida; disc i earthshine ancorats a C2. Ni forat fix engrandit, ni llindar opac universal a 1,012 R☉, ni ompliment per raig de píxels no observats | 3-RECERCA/128 §8; V25 (5 rondes) |
| **M** monotonia | anell clar o fosc a qualsevol radi | igualació entre trens amb finestra que no cobreix el traspàs; capes a nivells diferents | `perfil_radial` + `monotonia` (cap pujada >0,005 per 0,1 R☉ d'1,2 a 12 R☉) | igualar a la base tot el que va fora, no la base a fora; finestra de ρ que inclogui la vora | V25 (anell fosc 2,5-4 R☉) |
| **H** nivell del detall | anell sencer aclarit o enfosquit per una capa Superposar | nivell per anell ≠ 0,5 | `h1_nivell` ≤ 0,05 | `f3.anivella` (interpolat, mai per calaix) | 3-RECERCA/111 |
| **C** cel que aplana | contrast exterior baix o font separada que anticorrela amb l'altre observador | la descomposició cel/corona també pot absorbir corona real | taula cel/corona, contrast per anell i correlació amb observador independent | La recepta V25/V26 de CORONA sola amb NRGF a tot radi és històrica i està superada: 3-RECERCA/133 demostra fallada exterior. V29/V30 filtren TOTAL segons el seu manifest. Justifica la font per zona i conserva tot el suport observat; un radi de canvi de font no autoritza un tall del detall | V25/V26 històriques; V28–V30 |
| **I** anisotropia | molts arcs curts concèntrics de poca extensió azimutal | el kernel angular pot allargar soroll en direcció tangencial | espectre polar per escales, ablació H1/perfils, soroll sintètic i altre tren fix | regularització radial normalitzada al suport físic, només després de mesurar la transferència i el detall corroborat; paràmetres i pèrdua declarats, sense màscara de marques | V30, 3-RECERCA/137 |
| **A** alineació | les capes noves surten GIRADES respecte de les de Pere (V25/V26: 138,5°) | geometria entre llenços «validada» amb proves rotació-invariants (finestres de fase dominades pel gradient radial, escaquer de raigs radials, forat lunar, anells) | `prova_azimutal`: correlació circular en azimut del perfil polar en ln; PASSA si el pic és a 0 ± 0,5° i el control nul (ref girada 180°) no correla | refer la geometria amb l'angle azimutal com a pas gros (`etapa2d`), centre solar per efemèride i escala declarada; contrastar a part la geometria lunar temporal, sense confondre el seu forat amb el disc C2. Cap PSB amb capes noves sense aquesta prova al rebut | V27 (05-09) |
| **P** marques de Pere | el que ell pinta sobre un TIF de la fusionada | localitza el problema observat; la causa s'ha de comprovar | `marques_tif` → components amb color, mida, r, azimut; `marques_pere.py` fa el panell TIF ↔ fusionada | classificar cada marca en una família i corregir-la a l'origen; el rebut diu marca per marca què s'ha fet | V18, V19, V24, V26 |
| **F** flat amb soroll | arcs quasi concèntrics amb el Sol a 3–5 R☉ a TOTS els filtres no azimutals i a un sol fotograma; anisotropia tangencial fina (σ4) només a un tren | un flat estimat de les dades (`FLAT_RADIAL` de la Sony, self-calibration del dither) amb ondulació fina (0,09 % rms a 8–30 px) que divideix totes les fotos i s'hi imprimeix INVERTIDA, centrada al centre del SENSOR (0,5 R☉ del Sol a l'apuntament B) | `a4` (anisotropia per anell: +0,06 Sony, 0,00 Vixen) i `a6` (correlació fotograma↔flat en coordenades del sensor: −0,80, pendent −1,00) | suavitzar el perfil radial del flat per sota del soroll coherent (σ 32 px) i refer F0.3; MAI a la capa | V32 (3-RECERCA/146) |
| **B** fronteres HDR | contorns transversals interiors (1,0–2,2 R☉) i arcs a l'entrada dels 8 s (2,6–2,8 R☉), amb colzes: segueixen isofotes | canvi del joc de fotogrames del compost LDIC amb desnivell entre fotogrames que varia pel camp (transparència, cel, registre) | `a1`/`a3` (fracció de pes per fotograma cel·la a cel·la: mapa de fronteres) i `a5` (graó al llarg de la frontera d'entrada, diferencial contra l'altre tren) | camp de nivell suau per fotograma i canal (σ 128 px) amb gauge σ 512 px, aplicat ABANS de recompondre (`b1`, `b2`); els pesos no es toquen | V32 |
| **N** graons de GRA | contorns transversals interiors (isofotes a 1,2–2,1 R☉), arc al canvi de tren (2,0–2,7) i contorns que MGN i WOW dibuixen encara que el NIVELL sigui pla; també al MGN «recurrent» de la V29–V33 | el compost LDIC canvia de joc de fotogrames: pesos ∝ t amb salts de 5× (0,5→2→10 s) i finestra de sostre estreta (70→85 % sat) → el gra del compost cau del 40 % en 40–140 px a cada entrada; al canvi de tren (Vixen sola → Sony) puja un 54 % en 0,3 R☉. MGN/WOW normalitzen pel σ local a cada escala i converteixen cada canvi d'amplitud del gra en un contorn; l'ACHF el mostra directament | `a8_gra_per_radi` (rms del passa-alt fi 1,5/3 de ln G per calaix de 0,02 R☉ i al llarg de cada entrada: quocient fora/dins) i `a9_causa` (gra per fotograma) | a l'ORIGEN: entrada GRADUAL de cada fotograma (finestra de sostre smoothstep 35→85 % de la saturació: `finestra_v34`), fusió per VARIÀNCIA (A+B i entre trens, pesos ∝ 1/σ² mesurats amb porta contra l'altre tren), relleu entre trens llarg (1,9→3,5 R☉) i pesos CONTINUS a tota vora. ⛔ MAI suavitzar la capa per amagar-ho (V33: fabricava costures noves) | V34 (3-RECERCA/149/150: MGN la majoria fora, confirmat per Pere el 08-09); V35 (3-RECERCA/151) |
| **K** contorn d'un camp dins l'altre | rectangle (girat) del FOV Vixen visible a TOTS els filtres dins del camp Sony; línia de la vora de l'apuntament A dins de B | on un tren (o apuntament) s'acaba, el seu pes cau a zero: si porta un desajust de nivell en baixa freqüència (Vixen −2,9 % a la seva vora: ρ ajustat només a 1,5–4 R☉) i un gra diferent (fusió 0,077 % contra Sony sola 0,102 %), la vora és un graó de nivell (−0,8 % a la base) i de gra en 160 px | `a1_vora_vixen`/`a3_vora_sonyA`: perfils contra la distància AMB SIGNE a la vora del suport (ple): pes, ln(V/(S·ρ)) σ64, graó de la fusió, gra fi/mitjà | conformar el tren que s'acaba al que continua en baixa freqüència (δ σ256 a tot el solapament, holdout per sectors) i esvair el seu pes en ≥ 4× l'escala del filtre més gran (Vixen 720 px, A 480 px) sobre el suport PLE; el gra que queda és un gradient, no una vora | V34 (nou artefacte, marcat per Pere); V35 |
| **E** limbe lunar de l'earthshine | franja blanca als últims píxels de la Lluna, vall fosca esglaonada fora, protuberàncies «que volen», gradient ampli dins del disc | tres vores diferents: silueta aparent 453,5 px, forat de la base = disc MODELAT 455,5 + guarda 2 + rampa 2 (la fusió V38 no té corona als 4–6 px del limbe de cada fotograma), alfa lunar = pes fotogràfic V44; i l'ala de la PSF de la corona dins del disc (+40 % de −80 a −20 px, ×2–3,5 als últims 8) | `m1_vores.py` (mateix detector a les tres vores), perfil radial de la capa lunar per sector, arcs polars | recompondre la fusió a la caixa lunar amb la maquinària V38 i la màscara al limbe aparent per nivells; recepta b4e exacta amb color congelat; vel de l'ala mesurat per sector i restat; ⛔ cap capa de compensació (V50 refusada per Pere). Detall: `references/limbe_lunar_earthshine.md` | V50–V53 (12/13-09) |
| **O** operadors isotròpics contra el forat lunar | anell clar al limbe (1,0–1,3 R☉) al MGN i als dos WOW a TOTES les versions; al WOW, rectangles a ±2^s px del Sol (costats a CX ± (2·2^s + R_forat)) | la mitjana local D'UN SOL COSTAT contra el forat (suport absent) amb un gradient de ×2 cada 44 px: biaix positiu coherent a cada escala (4–5 σ a 1,0; MGN fins a 1,2, WOW fins a 1,5 R☉); l'à trous B3 dispers a més copia la silueta del forat a ±2^s, ±2·2^s i les envolupants són rectangles | `a2_p05_limbe_roi`: mediana per anell / σ de la sortida (0,98–1,6, 0,01 R☉): un anell coherent és biaix; prova d'un sol paràmetre en una ROI (suport tal qual / forat omplert / entrada normalitzada) | condició de contorn DECLARADA de l'operador: entrada = imatge on hi ha suport i perfil azimutal mitjà (ln) de la pròpia imatge al forat i fora del suport; sortida només al suport físic (cap píxel farcit al producte). Biaix 4,8 → 1,8 σ (WOW bil.), 4,9 → 2,3 (WOW), 4,3 → 2,9 (MGN) a la ROI. Les capes ACHF de cadena ja ho tapaven amb H1 (anivellament per anell) | V31–V34 (P03/P04/P05 «error recurrent»); V35 (3-RECERCA/151) |

## Lliçons de la V26 (rondes 2 i 3, 04-09-2026)

- ⛔ **TRAMPA RECURRENT (V26 i altra vegada V34): tota distància a «la vora del suport» es calcula sobre el suport PLE** (`suport | (r < 1,6 R☉)`): amb el forat lunar dins, `distanceTransform` diu que a 1,0–1,3 R☉ s'és «a la vora» i qualsevol ploma hi fa entrar l'altre tren (V34: Sony al 96 % a 1,0–1,1 R☉, 70 % a 1,1–1,2; P05 marcat al limbe). Porta: perfil del pes per anell d'1,0 a 1,5 al rebut de tota fusió.
- **La ploma d'un camp exterior es mesura a la vora EXTERIOR**: la distància a
  «fora de cobertura» compta també el forat lunar; sense omplir-lo, la base es
  barreja amb la capa exterior (zero dins de 2,6 R☉) fins a 120 px del limbe →
  franja fosca 1,0-1,27 R☉. `binary_fill_holes` només sobre la màscara auxiliar
  per calcular aquesta distància: mai sobre la validesa física ni la radiància.
- **El tall del detall FI a 3,5→5 R☉ era una recepta d'aquell pilot, ara
  retirada com a norma general (05-09)**. Research/82 situava l'estructura
  real a 30-45 px a 4 R☉, però això no justifica esborrar tot el detall d'un
  anell. Mesura senyal i soroll per escala i zona, amb jutge independent;
  els blobs del detector poden ser gra, i el radi sol no els classifica.
- **Una vora de fotograma de la Sony és a ±45° a la V23** (la capa 13 de Pere
  la té igual): on un apuntament s'acaba, el soroll del compost canvia de cop i
  el detall fi hi dibuixa una RECTA (3.200 px a 4,7 R☉). No es tapa: el detall
  s'ha de revisar a la cobertura i als pesos del compost. Que la banda gran
  no la mostri no justifica eliminar circularment la banda fina.
- **Ratllat: famílies a finestres d'azimuts diferents** (`families_ratllat`):
  un patró del sensor surt al mateix angle a totes; una estructura real, no.
  Dues famílies al mateix període 27,5 px (−45° i −36°) a la V26. I l'angle és
  el del PIC ESPECTRAL (el que torna `ratllat`), no el de les ratlles.
- **Res es lliura sense mirar les vistes**: les portes numèriques de la ronda 2
  van passar (H1, fidelitat, OBRE) amb una franja fosca al limbe i el detall
  saturat de gra; ho van dir `limbe`, `monotonia` i els ulls.

## Regles
- **Prova azimutal obligatòria** a tota capa nova que vagi a un PSB amb capes de
  Pere (`prova_azimutal`, pic a 0 ± 0,5°, control nul). Les finestres de fase i
  els escaquers NO valen com a prova d'alineació: s'enganyen amb el que és
  radial. I mira les vistes en POLAR (r × azimut): un gir hi és evident.
- **Ghosts a l'ORIGEN**: identifica l'apuntament contaminat i busca dada
  neta de la mateixa zona celeste; comprova geometria, suport i transició.
  La recepta històrica `corregeix_bol` + `tapa_inpaint` + `clona_textura`
  no és una correcció per defecte: una textura clonada no recupera la corona
  observada. Mesura el residu i la retenció de detall CAPA PER CAPA. Una
  moneda plana (V26) o un anellet a la ploma (V27) també són artefactes.

- **Un artefacte idèntic a totes les fotos d'un apuntament és invisible a tota comparació entre fotos**: es cancel·la en quocients i diferències, no té frontera a sota i les portes del flat (2–8 %) no el veuen. Els únics jutges són l'altre tren sol (`a4`) i la correlació amb la calibració mateixa (`a6`). Els anells amb aspecte de gramòfon no vénen només del filtre (tesi de Druckmüllerová): a la V31 venien del flat.
- **La causa d'un arc es busca per ordre**: joc de fotogrames (`a3`) → un sol fotograma (`a4`) → calibració (`a6`) → filtre. Un filtre radial només fa d'eco dels anells de l'entrada: si l'anell és a la base, curar-lo a la capa és tapar.
- Tot detector torna un número i un veredicte; tot el que es corregeix queda
  al rebut amb la coordenada, el radi i el mètode. Un pedaç no declarat és un
  frau; un pedaç declarat és cosmètica.
- **Cap retall circular per defecte**, encara que estigui declarat: ni
  discs neutres ni esvaïments a radis fixos per ocultar un artefacte. Els
  filtres treballen sobre tot el rectangle amb dada; els perfils radials i
  les màscares de validesa física no són una autorització per amputar corona.
- La base es corregeix ABANS del detall; el detall es recalcula des de la
  font i la validesa verificades, sense heretar pedaços a 0,5 ni esvaïments
  històrics. Mai corregir només la capa de detall per tapar un error de base.
- Un pic espectral, una vora recta o un blob que apareix DESPRÉS d'un filtre i
  no era a la base és del filtre: es canvia el filtre, no es tapa.
- Cada marca de Pere s'atribueix a una família o s'obre una família nova; la
  taula conserva l'evidència històrica, però les receptes superades es marquen
  i deixen de ser instruccions actives. Una marca localitza el problema;
  no autoritza a esborrar tota la zona marcada.


- **Noms de capa (Pere, 17-09): com a molt 9 paraules.** Capa nova: el què i la data. Capa modificada: no afegir sufixos de versió al nom (b11 `noms` = cap o «· V7x» curt, mai acumular); la història va al rebut i al LLEGEIX-ME.

## Ordre d'una passada

```text
base (lineal, fusionada)  →  F (a4/a6: anisotropia per tren i flat)  →  B (a3/a5: fronteres HDR)  →  C (cel/corona per anell: on és la dada)  →  G (blobs a la base
  i al detall on hi ha senyal)  →  V (vores, extensions, ploma a la vora exterior)  →  L (limbe)
  →  M (perfil monòton)  →  [detall fi 2-32 · gran 32-256]  →  R (famílies a diverses
  finestres; correcció només validada)  →  suport real i retenció del detall, sense tall
  circular per defecte  →  H (H1)
  →  I (anisotropia i transferència del filtre; H1 no basta)
  →  muntatge  →  M, L a la fusionada  →  P (marques de Pere)  →  VISTES  →  rebut
```

## Fitxers

- `scripts/artefactes.py`: `blobs_rodons`, `tapa_blob`, `ratllat`,
  `pics_espectrals`, `families_ratllat`, `notch_direccional`, `arestes_rectes`,
  `perfil_radial`, `monotonia`, `limbe`, `h1_nivell`, `marques_tif`.
- Exemples històrics, no receptes vigents de retall: `3-RECERCA/tools/v25_lineal/etapa1b_corona_gran_i_base_k.py`
  (corona sola, detall gran, base k) i `etapa4_munta_v26.py` (muntatge amb G, V,
  L, R, E, H i vistes).
- `scripts/marques_pere.py <Artefactes.tif> <fusionada.psb|.tif> <sortida/>`:
  llista de marques (JSON) i panell de finestres TIF ↔ fusionada.
- Evidència: `3-RECERCA/116` (ghost), `121` (halos de fusió), `123` (fons per
  raig), `128` (limbe), `130` (V25), `131` (V26 i aquesta skill), `146` (V32: flat
  amb soroll i fronteres HDR; eines `3-RECERCA/tools/v32_arcs_20260907/a1–a6`, `b1–b3`).


## Nota del 16-09-2026 (neteja profunda)

Per ordre de Pere s'han retirat a la Paperera els ràsters intermedis (output d'agost i setembre,
`3-RECERCA/tools/*/cau` i staging, replays, RAW copiats a `0-ENTRADES`, runs 005–018, PSB
supersedits del Desktop i Derivats). Els rebuts JSON, notes, codi i vistes es conserven i cada
carpeta afectada té `LLEGEIX-ME_NETEJA_20260916.md`. Les rutes citades en aquesta skill que ja no
existeixen es resolen amb `2-ARXIU/reconstruccio_compactacio_20260915/neteja_20260916/MOVIMENTS_<lot>.jsonl`.
Lliçons consolidades: `../postprocessat-corona/references/llicons_consolidades.md`.

## Lliçons de V70 → V71 (16-09-2026, nit): les 8 marques de Pere a V69

Codi: `3-RECERCA/tools/v71_marques_v69_20260916/` (`psb69.py` lector lleuger de PSB, `compo.py`
recomposició Photoshop, a1–a33, `dentat_*`, `corona_*`). Informe: `4-RESULTATS/v71_marques_v69_20260916/RESULTAT.md`.
V70 (primer intent) la va refusar Pere: «has espatllat la finura del limbe lunar, que ara surt dentat».

- ⛔ **Cap cercle booleà a la graella de píxels en una màscara.** `np.where(rr<453, 1, M)` va convertir la
  rampa suau de 3 px de Pere en un graó d'1 px als sectors on la seva vora començava més endins (dalt 450,9,
  sud 452,4): índex de dentat ×4 (0,055 → 0,193 px). Porta obligatòria abans d'escriure un PSB: **índex de
  dentat** = std del passa-alt azimutal (σ 1°) del radi de la vora 50 % (1440 azimuts), per sectors de 10°,
  igual a la versió de Pere ±0,01 (`a16d_mascares_v71.py`); i ablació capa a capa si puja (`dentat_2_mascara30.py`).
- ⛔ **Cap retall de la cobertura lunar de Pere ni clau d'alfa a les seves fotos** (V70: línia fosca fina i
  contribució a trossos). Si una foto és més fosca a la ploma, es declara i ho decideix Pere.
- **Família O al ràster (quan l'operador no es pot recalcular):** component RADIAL coherent en azimut a
  d ≤ 22 px del forat (ACHF micro saturat 0,99 dalt, −0,4 a l'oest; bombolla a d 10–25 als 4–64): polar
  (θ 0,25°, d 0,5 px), suavitzat en θ (σ 6°), referit a d 32–48, restat amb taper 22→32 (`a14`). **Control
  nul** a una vora falsa +170 px: el que hi surt és estructura legítima que la correcció pot atenuar.
- **Taló de les màscares multiplicatives** (0,9 → 1 en 14 px fora del forat = −3,7 % multiplicatiu): omplir,
  sense tocar els sectors amb selecció de Pere (màscara < 0,7 del nivell a d 2–6).
- **El compost desat d'un PSB va aplanat sobre BLANC** (stored = C·a + (1−a)): màscara al 99 % dins del disc
  = fil blanc a qualsevol exportació. Omplir només l'interior lluny de la vora (mínim 7×7 > 0,95).
- ⛔ **Un «clot» de lluminància al limbe no és un dèficit fins que es mesura per canal**: era la cromosfera
  vermella (R 0 %, G −36…−69 %, B −9…−36 %); correcció revertida.
- **Família E, la taca ampla = vel amb component AZIMUTAL.** A r 0,45–0,65 R el patró del disc (RAW i capa)
  segueix la corona al limbe (r +0,60) i no LROC (−0,09). Model 2D: vel = corona lineal (HDR dels RAW,
  negre real 512 DN14; libraw en llegeix un d'absurd per canal) ⊗ K(d) = 1/(1+(d/d0)^q), zero dins del disc;
  component azimutal per anell ajustada al disc RAW (R² 0,82; control nul corona girada 90°: 0,11); a la capa
  revelada: capa′ = capa/(1 + c(r)·Gaz), c per anell (regressió amb LROC de covariable), reescalat perquè el
  residu quedi tan anticorrelat amb el vel com LROC (LROC = jutge, cap píxel seu), taper al limbe, tres canals
  iguals, mitjana per anell intacta; validació creuada per sectors (`a28_vel2d.py`, `a29c_amplitud_final.py`).
  Detall: `references/limbe_lunar_earthshine.md` (secció V70/V71).
- **psd-tools 1.18:** `flags.visible` ja és visible; nom real al bloc `luni`; registres round-trip byte a byte;
  canals ZIP-predicció: PSB nou copiant tot el que no canvia (`a31_escriu_psb.py`) + porta OBRE.
- **Ultracode:** tres agents en paral·lel (dentat capa a capa, corona HDR dels RAW, escèptic) van aïllar el
  culpable del dentat i van construir la corona lineal en 10 minuts.

## Lliçons de V72 → V73 (17-09-2026): verds de la part linealitzada, WOW obert i el terra del vel

Codi: `3-RECERCA/tools/v73_marques_v71_20260917/`. Informe: `4-RESULTATS/v73_marques_v71_20260917/RESULTAT.md`.

- **Un «anell verdós» pot ser només color.** Mesura R/G i B/G (no la lluminància) en funció de la distància al
  forat, per sectors, amb mediana circular en θ i control nul a +170 px. La base tenia +2–3 % de B/G als primers
  40 px (NE/N); la cura és un anivellament de color per sector amb retall ±6 % i taper, G intacte (`b8`).
- **Una foto de perles/interiors a la seva ploma és més fosca i més blava** que el compost de sota (L ×0,86,
  B/G +9–31 %): igualació en baixa freqüència per canal (σ 24 px) mesurada als píxels sense protuberància i
  estesa per convolució normalitzada; alfa i màscares intactes (`b9`). No fer-ho amb claus d'alfa.
- **Quan Pere obre la màscara d'un filtre**, destapa la banda de contorn que no s'havia mesurat (el suport de
  la mesura ha de ser el ràster, no la màscara) i el ràster val 0 dins del disc (el filtre enfosqueix la Lluna):
  corregir amb tot el suport i posar el ràster al nivell local dins del disc amb transició (`b7`).
- **Vel 2D v2:** dos nuclis (3 i 160 px, β 1,5) més un dipol de cel (el crepuscle: 1,8 % per radi) expliquen el
  87 % del disc RAW (un nucli: 82 %) i deixen la taca sense residu; el dipol és física (Sol a 5°).
- **PSB re-desat per Photoshop:** tots els canals canvien ±1 DN16 (requantització a 15 bits): compara amb
  llindar, i localitza els blocs llegint-los (l'escriptor no pot tenir offsets fixos).
- ⛔ **Una correcció exacta pot ser invisible al to de l'usuari.** A V72 la taca ja era al nivell del seu anell i
  la capa correlava +0,73 amb LROC, però el terra del vel (part isòtropa, ≈ 98 % del senyal del disc als RAW,
  conservat pel vel V52 com a «nivell del disc») comprimia el contrast d'albedo 6× (pendent 0,15 respecte de
  la LROC): Pere hi veia només un canvi de gradient. Porta: mirar la capa lunar amb el terra restat (p2 → negre,
  `c5`) i comparar amb LROC; cura: contrast d'albedo al voltant de la mitjana per anell (V73: ×2,5, pendent 0,37).
- ⛔ **La línia verda del limbe era una capa BLANCA sota la rampa lunar** (POWAAAH3 amb la mateixa alfa que la
  capa lunar, visible a la V71 de Pere): a d −1…+1 el blanc es cola (B/G 0,81 contra 0,61). Mira el compost capa a
  capa a ±2 px del limbe (`c7`) i les capes que l'usuari ha canviat de visibilitat entre versions.

## Lliçons de V74 → V76 (17-09-2026, nit): el moviment del limbe lunar i els filtres (research/165)

**REGLA NOVA, la primera de totes a la corona interior:** la Lluna es va moure 28,5 px durant la totalitat; la franja r 456 → ~496 px de la base és agregat (arcs foscos del dèficit de vora de cada fotograma) i **cap filtre no la pot veure**: abans de calcular un filtre, aquesta franja es tracta com a «sense dada» (farcit A des de ~496, mesurar-ho) o s'omple amb un sol instant (C2). Els filtres són ràsters estàtics: si la base canvia, es recalculen; si no es poden recalcular, el pedaç va al ràster del filtre (Pere ho va provar: interpolar la base no arregla res; interpolar el WOW bilateral sí).

- Un artefacte «negre» a la corona interior: mira primer els ràsters dels filtres a 456–500, capa a capa; jutja amb vores (black-hat, gradient, retalls al 300–400 % amb el WOW obert), no amb mitjanes per marca.
- «Hi és a l'HDR lineal» no vol dir «corona real»: l'HDR també és una fusió en el temps.
- El compost desat per Photoshop porta les marques pintades: recomposa sense elles abans de mesurar-hi.
- Producte lunar: acaba a la silueta (alfa erf 456 σ 1); els últims 5–8 px del fotograma són llum del limbe, no albedo (nivell del sector); la base sota el limbe al mateix nivell; una màscara a mà que surt de la silueta tapa corona (l'alfa del producte ho limita).
- Taca de l'earthshine: llum dispersada als RAW (−0,5 %) amplificada ×8–10 per la corba; cap model de vel la treu; pendent ESF de la PSF. No prometre'n la cura.
- Fotos de Pere (76/96) en mode normal: cel de 1/15 s contra corona = vel i solc a l'oest; clau de lluminància només amb el seu sí.
- Diagnosi de marques: flux de 3 lectors + 1 escèptic; l'escèptic tomba afirmacions. Mai una diagnosi d'un sol lector.
- Eines: `3-RECERCA/tools/v75_marques_v74_20260917/` (compo74, e1 inventari, d3b, agents), `b13_afegeix_capa.py` (afegir una capa nova a un PSB sense tocar la resta).

## Lliçons de V85 → V86 (23-09-2026, nit): forats, franja d'un instant i cantonada

Detall a `references/v86_franja_un_instant_forats_i_cantonada.md`. En una línia cadascuna:
- **Forats:** mesura la cobertura de la pila per sota de PixInsight. Les màscares a negre a tota la silueta i la vora suau de la Lluna fan un anell transparent. Cura: màscara × (1 − Lluna opaca).
- **Franja escombrada:** la dada d'un sol instant no fa arcs. Es fa amb els primers fotogrames (≥ 8 d'11), a ≥ 1 px del limbe **observat**, amb rampa de pes arran del limbe de cada fotograma, CFA σ 0,8 abans de la matriu i un nivell **constant**. La interpolació fa un anell llis i l'aplanat radial, perles.
- **Continuació:** arrenca a 2 px dins de la dada (prova de 0–3 px al compost emulat).
- **⛔ Distàncies i nivell:** `distance_model` va al radi de l'efemèride. Amb aquesta distància es perden ~3 px de corona i queda una tira llisa de 4–6 px (la primera V86 del 23-09). A més, una c(d) ajustada a la fusió n'importa la vora clara artificial (+27..+47 % a 1 px).
- **Judici:** al compost natiu de Photoshop, 1:1 a diversos azimuts, i amb el perfil de lluminància del compost.
- **Torre de Pisa:** una màscara d'una capa de l'usuari no es canvia: se'n fa una capa nova i l'original queda oculta.
- **Cantonada del logo:** capa pròpia i regenerable (`regenera_cantonada.jsx`), mai dins de PixInsight.

## Lliçons de V87 → V88 (23-09-2026, tarda): cremallera, soroll d'un instant i vora de l'earthshine

Detall a `references/v88_cremallera_soroll_franja_i_earthshine.md`. En una línia cadascuna:
- **Marques:** primer se n'extreuen l'azimut i la distància al limbe (`c0_marques_v87.py`). Colors diferents poden ser una sola família: el verd, el marró i el blau clar eren la vora de la franja.
- **Pixelat:** la dada d'un instant té ~3 vegades el soroll fi de la fusió. σ 1,3 px abans dels filtres, triat pel soroll i mai per la prova (σ 1,5 deixava la franja massa llisa).
- **Cremallera:** una vora binària d'un cercle sempre és esglaonada. La cura és una fosa suau sobre la distància analítica a una corba llisa, amb continuació radial. La de piràmide i Laplace fa una línia arran de la vora.
- **⛔ `W_CURT` = 0 a la V86:** una condició que no descarta cap píxel és sospitosa. Llegeix el valor dels llindars derivats al rebut.
- **Earthshine:** meitats independents contra LROC. Si coincideixen entre elles però no amb LROC, és llum dispersa i l'anell es deixa llis. L'apilat Vixen des de zero és pitjor que la capa de Pere a l'interior.
- **Mirar:** el compositor emulat no fa les capes d'ajust (el jutge és Photoshop). L'estirament per separat a 6:1 fa una línia puntejada falsa al limbe, i els mosaics de vistes adjacents fan formes falses.
