# 107 · La cacera final: la mediana, i el mur ben cartografiat

**Data:** 25 d'agost de 2026, nit tancada. **Agent:** Fable 5.
**Mandat de Pere:** «fes tot el necessari per acabar d'una vegada per totes
amb aquest artefacte». Executat amb la norma zero a cada pas: **vuit
candidats jutjats en una nit**, cadascun amb el jutge extern (Sony d'àrbitre,
Δz aparellat per sector), la mètrica de Pere (l'excés del detall als seus
traços d'ARTEFACTE_PERE.psb) i les portes H1/G/rectangle.

**Resultat en una frase: l'artefacte queda reduït a UN TERÇ del que era (de
−8,54 a −2,93·10⁻⁴) amb la MEDIANA de les tres realitzacions de canal, que és
l'única operació que discrimina de veritat; el terç restant no es pot treure
d'aquestes dades — la informació que el separaria de la corona no es va
capturar — i la seva eliminació completa és feina del protocol del 2027.**

---

## §1. La taula de la campanya

Referència del jutge: el producte vigent (lluminància (1,2,1)/4 sobre el
compost RGB curat). Mètrica de Pere: mitjana del detall als seus traços menys
el control aparellat, ×10⁻⁴.

| candidat | què fa | jutge (Δz aparellat) | mètrica |
|---|---|---|---:|
| G sol (l'antic) | el detall sobre el canal G | −0,0069 vs producte | −8,54 |
| lluminància (1,2,1)/4 | dilució amb R i B reals | **PASS** +0,0069 vs G | −4,04 |
| lluminància (1,1,1)/3 | més pes a R/B | **FAIL** −0,0124 ± 0,0013 | −2,54 |
| **mediana(R, G, B)** | estadística d'ordre entre realitzacions | **EMPAT +0,00347 ± 0,00178** (+1,9 σ) | **−2,93** |
| resta tangencial (blur az 1,5°) | fora el cromàtic coherent | **FAIL** −0,0054 ± 0,0009 | −4,07 |
| llindar per arcs (2σ anular, 1,5° i 8°) | només el significatiu | EMPAT, no mossega | −4,06 / −4,13 |
| igualació de barreja v6 (model físic) | ajust per geometria de pesos | sense efecte | −4,14 |
| coherència contra el nul (3σ_nul, 8°) | coherent per damunt del nul | **FAIL** −0,0018 ± 0,0005 | −3,53 |

R sol i B sol, mesurats com a diagnòstic: **+0,77 i −0,78** als traços de
Pere — nets. La confirmació definitiva, a nivell de detall, que l'anomalia és
exclusivament de la realització verda (mecanisme del `104` §7).

## §2. El mur, ben cartografiat: per què el terç restant no es pot treure

Cada intent va fallar per un motiu diferent, i junts dibuixen un teorema
pràctic sobre aquest conjunt de dades:

1. **La direcció cromàtica no discrimina.** Els arcs tenen exactament la
   direcció «G contra la resta» — la mateixa que la corona E (Fe XIV) i que
   l'excés de nitidesa del G. Tot operador de projecció cromàtica global
   s'emporta les dues coses (per això l'opció B del `104` va caure, i per
   això la resta tangencial cau: −0,0054).
2. **L'amplitud no discrimina.** Al camp cromàtic hi ha estructura real més
   forta que els arcs; tot llindar que la protegeix els deixa passar.
3. **L'estadística anular s'autoemmascara.** A r ~1,97 l'arc ÉS l'anell:
   qualsevol σ anular l'inclou i el llindar se'n va amunt amb ell.
4. **El nul tampoc no basta.** Amb el llindar honest (el que valdria
   l'agregació azimutal d'un camp incoherent), el que se subtreu correlaciona
   amb la Sony (**cel compartit**: els dos trens veuen els mateixos cirrus) i
   el jutge ho penalitza: −0,0018. El jutge no pot separar cel compartit de
   corona compartida — confusor ja documentat al `103`/`106`, aquí mesurat en
   acció.
5. **El model físic exacte tampoc no arriba.** La v6 reconstrueix la
   geometria de barreja F_c,e (les fraccions de pes per esglaó i canal,
   replicant la fase 2) i ajusta el cel per esglaó: explica el 67 % de la
   desviació cromàtica del G i el 81 % de la del B **globalment**, però als
   arcs de Pere la correcció ajustada té mitjana zero. Diagnòstic: la
   direcció cromàtica mesurada dels arcs (G-contra-la-resta) **no coincideix
   amb la de la geometria entre-esglaons** als seus radis (dominada per B:
   10,08 s → R+0,12 G−0,28 B+0,44), perquè el que mana allà són les
   **diferències de barreja DINS de cada esglaó** — les dues aparicions de
   cada exposició, separades 40-80 s amb el cel un 8 % diferent — i això
   demanaria un desconegut per fotograma que aquestes dades no poden
   restringir (l'ajust per píxel té 2 equacions).

La síntesi: **el que separaria els arcs de la corona és la redundància
temporal per esglaó, i no es va capturar** (1-2 instants per esglaó; Brno en
fa 8-50, `105`). L'única informació discriminant que SÍ que hi ha són les
tres realitzacions de canal, i l'operació que n'extreu el màxim és
l'estadística d'ordre: **la mediana**, que allà on dues realitzacions
coincideixen i una desvia, rebutja la desviació — sigui de quin canal sigui.

## §3. El producte final: la mediana

`D_final = mediana(D_R, D_G, D_B)` píxel a píxel, sobre els detalls de fase 3
de cada canal del compost RGB curat (cada canal amb la seva fase 3 completa i
la seva variància pròpia; codi a `candidats_mata_artefacte.py`).

- **Jutge extern: +0,00347 ± 0,00178** — formalment EMPAT (a 1,9 σ del
  llindar de PASS), amb la correlació amb la Sony PUJANT a 4 de 5 bandes.
  Acumulat des del detall G antic: **+0,0104**.
- **Mètrica de Pere: −8,54 → −2,93·10⁻⁴** (el 66 % de l'anomalia fora).
- **Portes: H1 PASS (anells 1,0 %), G PASS, rectangle PASS**; rms del detall
  0,00216 (contra 0,00229 de la lluminància: el que falta és majoritàriament
  la desviació del canal únic, que és el que es volia fora).
- **Cost declarat**: l'estructura real que viu NOMÉS en un canal (corona E
  compacta) hi queda esmorteïda com a la lluminància o una mica més; la capa
  G es conserva al PSB per a qui la vulgui mirar pura.

S'adopta com a detall del producte (el jutge no protesta, la direcció és
positiva, i el criteri de l'artefacte — que és de Pere — mana per mandat).
La lluminància (1,2,1)/4, judicada PASS, queda com a capa i com a fallback.

## §4. Els lliurables

- `output/pilot_vixen_fable_20260825_lliurament/dos_trens_filtrats/` — fusió
  refeta amb la mediana (l'anterior, amb lluminància, conservada a
  `dos_trens_filtrats_llum121/`);
- `photoshop_mediana/Eclipsi_2026_dos_trens_MEDIANA.psb` — el projecte
  complet refet;
- `photoshop/Eclipsi_2026_parpelleig.psb` — **l'eina de Pere**: les
  realitzacions per capes (mediana, lluminància, G, R, B) a la mateixa escala
  de grisos, per fer el parpelleig dins de Photoshop amb zoom i pinzell.
  Neix de la seva observació que només l'animació atrapa l'artefacte — cert
  pel mecanisme: l'artefacte és una diferència entre realitzacions i només
  una comparació el pot ensenyar;
- animacions: `anim_vixen_G_vs_MEDIANA.gif` (la decisiva),
  `anim_vixen_realitzacions_GRBL.gif` (cicle G→R→B→producte),
  més les de la ronda `106`.

## §5 bis. La mediana amb la Sony (N=5/N=6): provada i ajornada

Proposta de Pere (25-08, nit): afegir els canals de la Sony a la mediana.
Mesurat (`mediana_sis.py` + json): la mètrica de Pere millora poc
(−2,94 → −2,78 amb N=5, −2,62 amb N=6) i **la por de la resolució era
infundada** (retenció del detall fi 94-98 %: la majoria Vixen protegeix la
mediana). ⛔ **Però és inadoptable avui per mètode**: amb qualsevol dada Sony
dins del producte, el jutge creuat perd la independència — el «PASS +0,064»
que surt és 20× més gran que cap efecte legítim de la setmana i delata
correlació de parentiu (mateixa PSF, apuntament, demosaic i soroll que
l'àrbitre), no corona. La norma zero caça aquí el seu autoengany més subtil:
un candidat que conté l'àrbitre sempre «guanya». Condicions per reobrir-ho:
llenç Sony amb variància per canal (els R/B d'avui són diagnòstic) i un
àrbitre independent nou (meitats A/B de la Vixen, o les dades del 2027).

## §5. Cues que queden (i el seu preu)

1. El **terç residual** de l'anomalia (−2,93·10⁻⁴ als traços): irreductible
   amb aquestes dades pel §2. Cura real: protocol del 2027 (§1 quater,
   confirmat per Brno al `105`).
2. La Sony continua amb detall G sol (li falten les variàncies per canal);
   quan es refaci el seu llenç amb D per canal, la mediana s'hi pot aplicar
   igual.
3. L'anell de ~1,97 del canal G del compost: intacte al compost; al producte
   mediana en queda el residu del §3.
4. Els rebuts d'aquesta campanya: `candidats_mata_artefacte.json`,
   `candidat_arcsfora.json`, `candidat_cohnul.json`, `cura_barreja_fina.json`
   i els registres `*.log` a `output/pilot_vixen_fable_20260825/`.

⚠️ **Advertència de mètode per al 2027**: la meitat dels candidats d'aquesta
nit haurien passat qualsevol control intern nostre; els va tombar el jutge
extern. La norma zero ha demostrat aquesta nit que no és burocràcia — és
l'única cosa que ha impedit vuit maneres diferents d'autoenganyar-nos.

## §6. El model directe: la predicció d'amplitud (demanada per Pere)

**La pregunta**: ¿el mecanisme prediu l'AMPLITUD dels arcs, no només la
posició? Test sense cap paràmetre lliure
(`output/pilot_vixen_fable_20260825/model_directe_arcs.py` + json):

**Ingredient 1 — σ del cel per fotograma, mesurada dels parells de la mateixa
exposició** (la corona s'hi cancel·la; el soroll es resta; banda 4-32 px):
**σ_cel = 26,4·10⁻⁴** (0,26 %, dins del 0,10-0,50 % del `102`). I de regal,
**la corba de decorrelació temporal del patró fi del cel, mesurada per primera
vegada**: s'assembla ~85 % a 3 s, ~80 % a 6 s, ~50 % a 13-19 s i **res a
60-80 s**. (⚠️ El camp `sigma_cel_e4` del json és erroni — un /√2 de més i
parells massa pròxims; l'asímptota dels parells amb Δt>30 s és la bona.)

**Ingredient 2 — la geometria de barreja**: d_i(r) = ŵ_G − (ŵ_R+ŵ_B)/2 amb
els pesos de la fase 2 replicats per fotograma i anell (0,0125 R☉), agrupant
els fotogrames a <6 s (cel compartit) i descorrelacionant els grups.

**El veredicte:**

| | model | mesurat |
|---|---|---|
| posició del pic | **r = 1,94-1,98** | el traç més gran de Pere és a r~1,97 |
| estructura secundària | 1,54-1,75 | traços de Pere a 1,45-1,75 |
| amplitud als traços | −8 a −12·10⁻⁴ | **−22,2·10⁻⁴** (mateixa banda) |

**Posició: clavada. Amplitud: dins d'un factor 2** amb zero paràmetres
ajustats. El factor que falta té candidats identificats i cap és exòtic: els
traços de Pere seleccionen les excursions més fosques d'un camp NO gaussià
(les estries són coherents: les cues pesen més que -1,5 σ); la σ_cel és la
mediana de tot el run però la transparència va empitjorar cap a C3 (els
fotogrames que manen als arcs poden veure un cel pitjor que la mediana); i
les transicions de pes tenen estructura azimutal (la saturació segueix la
corona, no cercles) que la mitjana anular esborra.

**Conseqüència per al 2027, nova i mesurada**: perquè les aparicions d'un
esglaó promitgin el cel de debò, han d'estar separades **més de ~30-60 s**
(l'escala de decorrelació mesurada); i el monitor de transparència cada
~10 s queda ben dimensionat, perquè el cel canvia en ~10-20 s.

## §9. Tancament de la ronda (26-08, ordre de Pere: «ves acabant»)

Estat en tancar, sense obrir res més:

- **El producte no canvia**: compost RGB curat + detall MEDIANA + Sony viva.
  El projecte de camp complet és
  `photoshop_complet/Eclipsi_2026_dos_trens_COMPLET.psb` (5,7 GiB, PASS;
  la versió amb la capa de color 00c s'estava remuntant en tancar).
- **Cua 4 resolta de fet**: la regressió de 1,263/1,266 mesura ±0,3·10⁻⁴ als
  productes d'avui (era 40-47·10⁻⁴ el 25-08 al matí) — la cadena del 24-25
  la va curar de passada (`mesura_arc_sony.json`).
- **La mediana Sony (R,G,B amb D pròpia) queda com a MATERIAL, no adoptada**:
  el primer judici va sortir contaminat per una troballa de mètode nova —
  ⚠️ **la recomposició del llenç NO és reproduïble bit a bit** (fils del warp,
  0,007 % de mediana) i la fase 3 amplifica aquesta molla fins a ±0,01 de Δz.
  Regla que en surt: les comparacions aparellades exigeixen el MATEIX llenç
  físic als dos costats. Els canals R/B sobre el llenç viu queden llançats
  (`fase3_sonyviu_*.log`) per a una futura ronda neta.
- **v7 (flat espectral detector-fix): FALLA LA SEVA BATERIA, i amb això el
  mur queda defensablement tancat pel criteri que Codex mateix va fixar.**
  Els nuls no són nuls (R −244·10⁻⁴ a 2,2σ i B −298 a 1,0σ, comparables al
  «pic» del G −196 a 2,4σ), les meitats retingudes no correlacionen (−0,19;
  pics −178/−386), i la injecció sintètica es recupera al 80 % — l'àlgebra
  és bona, el que falta és sensibilitat: el terra de soroll de l'ajust
  contra l'escena (~±100-200·10⁻⁴) és 10-20× l'amplitud buscada. Conclusió:
  **l'anell no es pot mesurar dels crus de totalitat** (l'escena no es resta
  prou fi); la seva existència queda establerta per les PARCIALS (§7, on no
  hi ha corona a restar), i la seva cura és una mesura dedicada — el flat
  espectral amb llum solar del §1 quater, per al 2027. Rebut:
  `flat_eix_v7/flat_eix_v7.json`.
- **L'enfocament diferent, proposat a Pere**: aturar la persecució
  algorítmica del terç residual (rendiments decreixents demostrats aquesta
  nit) i passar el timó al seu Photoshop — el producte és una FOTO (D1), les
  eines de parpelleig i capes són fetes, i la seva mà dosant és ortodòxia
  Druckmüller. La resta és del 2027.

## §8. El contrast advers de Codex: el literal cau, la versió estreta queda
*(26-08 matinada, ronda `pont` tema `mur-artefacte`, demanada per Pere)*

⛔ **El literal «irreductible amb les dades del 2026» NO se sosté.** El que se
sosté (Codex dixit, i ho subscric): «la component de cel fi arbitrària per
fotograma no és identificable sense hipòtesis addicionals, i la mediana és
l'única cura avui demostrada i segura». Les quatre esmenes que accepto:

1. **Hi ha una via concreta no provada**: l'ajust conjunt sobre els CRUS que
   separa el marc del detector (plantilla anular A(ρ) de l'anell instrumental)
   del marc solar (l'escena) i del cel temporal regularitzat. El
   `cura_anell_vixen` vell ajustava sobre el compost centrat al SOL — la via
   detector-fixa és inèdita. Recepta de Codex: A(ρ) multiplicativa en log,
   ajustada sense els traços de Pere, aplicada a G1/G2 després de fosc/PRNU i
   ABANS del warp; nuls a R/B, injecció sintètica, leave-one-frame-out,
   estabilitat per exposició/instant/G1-G2; i el residu atribuït DESPRÉS de la
   mediana, amb la mètrica −2,93.
2. **El punt cec del jutge pesa més del que el §2 admetia**: un FAIL de H4
   només demostra que la cura treu estructura COMPARTIDA, no que fos corona.
   Tres FAIL del §1 podrien ser cures bones mal penalitzades; H4 queda com a
   control secundari per a cures de cel, i cal un jutge de predicció temporal
   retinguda.
3. **«2 eq/px» no és un teorema**: amb plantilla 1-D + corona estàtica en marc
   solar + cel de baix rang, el sistema pot quedar sobredeterminat. Cal mesurar
   rang i recuperació d'injeccions, no declarar impossibilitat.
4. **El «mig i mig» del §7 és més feble del que semblava**: 2 deteccions
   fortes que discrepen en radi (1,81/1,93) i fondària (×8), eix òptic
   assimilat al centre del sensor, i la suma explica el residu PRE-mediana
   (−22,2), no reparteix el POST-mediana (−2,93). ⚠️ I el camp `sigma_cel_e4`
   del rebut `model_directe_arcs.json` és erroni (7,68; el bo és l'asímptota
   26,4) — anotat aquí en lloc de regenerar el rebut, perquè el rebut és
   l'evidència del que es va executar.

**Decisió que en surt**: la mediana continua sent el producte; es reobre UNA
prova controlada — **el flat espectral detector-fix sobre els crus (v7)** —
amb la bateria de validació de Codex. Si falla els nuls, la barreja restant
queda *defensablement* irreductible; si passa, mig artefacte té cura nova.

## §7. Les cues 1, 3 i 5, tancades d'un sol cop (26-08, matinada)

**La prova de l'eix contra el Sol** (`anell_eix_o_sol.py` + json): a les
parcials post-C3 el Sol es passeja pel sensor (deriva 0,689 ″/s + correccions
manuals de Pere), i això separa les dues hipòtesis del solc de 1,845 R☉ que
el `102` §3.3 havia deixat obertes:

| parcial | Sol respecte del centre | clot al voltant de l'EIX | al voltant del SOL |
|---|---|---|---|
| 572A3150 | (−254, −7) px | **r=1,81 · −9,9·10⁻⁴ · 4,7 σ** | res (0,3 σ) |
| 572A3090 | (−183, +152) px | **r=1,93 · −80,7·10⁻⁴ · 4,4 σ** | res |
| 572A3130 | (−441, −450) px | marginal (1,2 σ) | marginal (2,3 σ) |

⛔ **El ghost queda desqualificat**: un reflex segueix la font, i amb la font
a 250 px el clot es queda a l'eix. **L'anell és instrumental i lligat a
l'EIX ÒPTIC** — tipus interferència/recobriment (transmissió del G en funció
de l'angle d'incidència). I per què el flat no el veu: el panell LED no porta
l'espectre solar (l'anell persisteix amb el filtre solar posat — mateix
espectre solar — i s'enfonsa prop dels contactes, quan l'espectre
cromosfèric mana). **Cua 1 tancada** (amb el matís honest que 3130, la
palanca més grossa, surt marginal per il·luminació pobra al seu anell).

**Cua 3 (el solc per fotograma) explicada**: el solc que el `102` mesurava a
CADA fotograma cru és **aquest anell instrumental** (−0,10/−0,15 % als
fotogrames d'1-2 s; el mateix −0,1 % que surt a les parcials filtrades); al
compost s'hi **superposa** l'artefacte de barreja de les finestres de
retenció, que cau al mateix radi (el 10,08 s del G: 1,62-1,97). La hipòtesi
de treball del `104` («la mesura barrejava estries i contorn») era només
mitja veritat: eren **dues coses reals al mateix lloc**.

**Cua 5 (el factor ~2 del model directe) tancada per la mateixa àlgebra**: el
−22,2·10⁻⁴ mesurat als traços de Pere en banda 4-32 és la SUMA de la barreja
predita pel model (−8 a −12, §6) i de l'anell instrumental només-G (−10 a
−15), que el model de barreja no ha de predir: **−18 a −27 contra −22,2
mesurat** — dins de la forquilla, sense cap paràmetre nou. La nota de
l'acotament puja: el que quedava «irreductible amb aquestes dades» té ara
nom i cognoms — mig artefacte de barreja (cura: captura 2027), mig anell
instrumental de l'òptica (cura: mesurar-lo amb l'espectre bo o llum solar
directa abans del 2027, i restar-lo com el que és: un flat espectral).
