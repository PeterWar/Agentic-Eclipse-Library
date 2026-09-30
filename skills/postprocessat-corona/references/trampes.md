# Trampes del postprocessat de corona

## ⛔⛔ NORMA ZERO (24-08-2026): cap correcció d'artefacte es declara bona sense el JUTGE EXTERN

Aquell dia vaig declarar **quatre vegades** que un artefacte estava arreglat, i
**quatre vegades Pere el va veure a la imatge** quan el meu número deia que no hi
era. L'error no era de cap estadístic concret: era **de mètode**. Cada mesura que
em vaig inventar tenia un punt cec que no havia comprovat, i el pitjor cas va ser
una resta per sector que **millorava el seu propi número ×8 mentre treia corona**.

> **El jutge és l'ALTRE TREN.** Una correcció que treu **artefacte** fa **pujar**
> la correlació entre trens; una que treu **corona** la fa **baixar**.

No es pot autoenganyar, perquè la Sony i la Vixen veuen la mateixa corona amb una
altra òptica, un altre sensor, un altre fosc, un altre flat, una altra escala
d'exposicions i unes altres fronteres de fusió. Mesurat: les dues passades
globals **0,894 → 0,952** (bones); la resta per sector **0,930 → 0,849**
(dolenta, i el seu número deia el contrari).

⚠️ **Límit**: els dos trens comparteixen llenç, warp, màscara lunar i filtre de
fase 3. Un artefacte d'**aquelles** etapes també correlacionaria.

**Eina**: `3-RECERCA/tools/pilot_vixen_claude/jutge_creuat.py` · **porta**: `H4`.

## ⛔⛔ UNA COINCIDÈNCIA DE POSICIÓ NO ÉS UNA CAUSA: MOU EL PARÀMETRE

25-08-2026, i és la trampa que va costar dos dies sencers de perseguir la
fusió HDR. Les corbes que Pere marcava **coincidien** amb els nivells de les
fronteres de fusió (0,05–0,72 % al llarg del contorn, radis clavats), i tothom
—dues IA i cent proves— va donar la identificació per feta. Era falsa: amb el
sostre a 0,60 **totes les fronteres es mouen** (fins a 0,35 en ln de nivell,
desenes de píxels en radi) i **cap de les corbes visibles no es va moure**
(perfils per nivell amb desplaçament 0,000; superposició R/G sense cap serrell
de color; del 74 al 91 % de l'amplitud «de frontera» persistint als mateixos
contorns). El que hi havia era el **cel per fotograma** i un **anell verd
instrumental** que viuen prop d'aquells radis per casualitat. `3-RECERCA/102`.

⏭️ Les dues regles que se'n treuen:

1. **Tota identificació d'artefacte ha de moure la causa proposada** abans de
   declarar-se: si dius «és de la fusió», mou el sostre; «és del flat», compon
   sense flat; «és del filtre», canvia'n l'escala. Una signatura que no segueix
   el paràmetre no és d'aquell mecanisme, per bé que hi coincideixi.
2. **El control aparellat pel PARÀMETRE és l'únic net quan les fronteres són
   denses**: el mateix contorn, mesurat al producte amb el paràmetre mogut. La
   corona es cancel·la exactament (mateixa corba, mateix cel) i cap densitat
   de fronteres no el contamina — el desplaçament espacial (±110 px) i el
   nivell de control no ho poden garantir mai amb una escala d'1 EV.

I el corol·lari que va destapar l'anell: **un dèficit que només és d'un canal
no és llum** (el cel i la corona surten als tres); i **abans d'atribuir una
corba a una isofota, mesura si està clavada en nivell o en radi** — l'anell
tenia cv 13 % en radi i 48 % en nivell, o sigui que era òptica, no fotometria.

## ⛔ QUE LA LLIBRERIA QUE HO ESCRIU HO PUGUI TORNAR A LLEGIR NO DEMOSTRA RES

25-08-2026. Un PSB de 12 capes que **`psd-tools` obria perfectament** —llistava
les dotze capes amb els seus noms, modes i màscares— i que **Photoshop refusava**
amb «s'ha trobat un final de fitxer inesperat».

Caminant el fitxer byte a byte, **cap longitud estava malament**: la de «layer and
mask information», la de «layer info», la de cada `ChannelInfo` i la del bloc
`Lr16` eren totes de 8 bytes com el PSB exigeix, i les tres fronteres queien al
mateix byte amb diferència **0**. El que fallava era l'última secció:

| | |
|---|---:|
| bytes a «Image data» | **47.187.468** |
| bytes que la capçalera exigeix (3966×3966×3×2) | **94.374.936** |
| raó | **exactament 2,0000** |

⛔ **La previsualització fusionada estava escrita a 8 bits en un document declarat
de 16.** Photoshop calcula la mida a partir de la capçalera i topa amb el final
del fitxer a mig camí; `psd-tools` no, perquè per llistar capes ni tan sols toca
aquella secció.

**La causa mecànica**, i és més interessant que l'error: `set_merged()` desa la
previsualització bona i apaga una bandera que vol dir «no la recomponguis».
`finalize_lr16()` crida `_update_record()`, que **la torna a encendre sense
dir-ho**. Llavors `save()` es refà la previsualització amb `composite()`, que
retorna una imatge **PIL**… i PIL no sap fer RGB de 16 bits.

⏭️ **Dues lliçons, i la segona val per a tot el projecte:**

1. **L'ordre importava i la docstring ja ho deia** —«DESPRÉS de l'últim append i
   ABANS de `set_merged`»— i jo el vaig posar al revés. Llegeix les docstrings
   del codi que reutilitzes.
2. ⛔ **Una promesa que depèn d'una bandera que qualsevol altra crida pot tornar
   a activar no és una promesa.** La cura no és només posar les crides en ordre:
   és **tornar a garantir la condició a l'instant en què ha de ser certa** —just
   abans de desar— i, sobretot, **comprovar el producte contra el que diu la seva
   pròpia capçalera**, no contra la llibreria que l'ha escrit.

La porta és `verifica_psb()` a `munta_photoshop.py`, amb quatre proves: un fitxer
bo passa, un amb la meitat dels bytes falla, un amb el doble també, i una que
exigeix que la longitud es llegeixi de **8 bytes** i no de 4 —perquè si es
llegís de 4, l'inici d'«Image data» sortiria desplaçat i el veredicte seria fals—.

## ⛔ UN SUFIX CONSTRUÏT A MÀ A DOS LLOCS SE'N MENJA UN EN SILENCI

25-08-2026, i és el defecte més car de tot el postprocessat fins avui. La fase 3
de la Sony triava el compost d'entrada amb aquest bucle:

```python
for cand in ("_cel-model", "_cel-color"):
    if cand in etiqueta: sufix = cand
```

`filtres_sony --coh` construïa el sufix `_coh`, **aquí es descartava**, i el
producte etiquetat `filtres_sony_coh` sortia del compost **sense coherència de
transparència**. O sigui que **la cura de les costures de fusió no s'havia
aplicat mai a aquell tren**. I el mateix bucle, copiat, era a la fusió dels dos
trens: aparellava una Vixen coherent amb una Sony que no ho era.

Mesurat en arreglar-ho: les costures de la Sony al compost passen del **92,6 %
al 7,98 %**. No era que aquell tren fos més brut; era que no havia rebut la cura.

**Com es detecta**: el rebut ho deia a la cara —`etiqueta: "sony_llenc_comu"` en
un fitxer que es diu `fase3_sony_coh.json`— i ningú no l'havia llegit. ⏭️ **Quan
un producte tingui una variant al nom, comprova que el seu rebut declara la
mateixa variant a l'entrada.** És una comparació de dues cadenes i hauria
estalviat un dia.

**La cura**: una funció pura compartida pels dos llocs, amb proves pròpies, i una
que exigeix literalment que si l'etiqueta declara coherència el sufix també.

## ⛔ UN FILTRE QUE DIVIDEIX PER UNA DISPERSIÓ HA DE TENIR UN TERRA MESURAT

25-08-2026, enxampat per les proves dels filtres nous abans de sortir. El NRGF,
el NAFE, el MGN i el WOW normalitzen dividint per una dispersió local o per
anell. Amb una entrada llisa de veritat aquella dispersió és **zero**, i llavors:

- el NRGF donava `(residu d'arrodoniment)/(≈0)` = O(1) a tot el camp;
- el NAFE saturava a **±1 a tot el camp**, o sigui pintava una imatge sencera;
- el WOW feia un **marc brillant** seguint la vora del rectangle, on la dispersió
  local cau perquè hi ha menys veïns.

⛔ Els tres **inventaven estructura on no n'hi havia cap**, que és el pitjor
error possible en aquest projecte. I el marc del WOW el va destapar **mirar el
full de contacte**, no llegir el codi.

El terra no pot ser un número triat a ull. Es **mesura** de la mateixa imatge amb
les diferències entre píxels veïns (`1,4826·MAD/√2`), i mai per sota d'una part
per milió de la dispersió pròpia; si la dispersió global és zero, el filtre
retorna zeros i ho diu al rebut.

## ⛔ UN CALAIX TÉ AMPLADA: CONDICIONAR PER CALAIX NO ÉS CONDICIONAR

25-08-2026. Per separar si una cosa depèn del **nivell** o del **radi** —que a la
corona estan molt correlacionats— es fan calaixos de radi i dins de cada calaix
es compara el tercil alt contra el baix de nivell. **No n'hi ha prou**: dins del
calaix el nivell continua caient amb el radi, o sigui que triar el tercil alt de
nivell **també tria el radi petit**. Amb aquesta versió, una dependència
purament radial passava per «és el sensor» a més de 3 σ.

La cura és treure la **tendència lineal del confusor dins de cada calaix** abans
de comparar. I la prova que ho garanteix és la que injecta una dependència
purament radial i exigeix que el marginal sigui gros i el condicionat, petit.

## ⛔ UN FLAT MULTIPLICATIU ES CANCEL·LA EN UN QUOCIENT AL MATEIX PÍXEL

Val la pena tenir-ho present abans de gastar-hi una nit: si dues exposicions es
comparen **al mateix píxel**, el flat les divideix totes dues igual i **no pot
produir cap desacord**. Només s'hi pot filtrar per la deriva d'apuntament, o
sigui pel camí de la muntura. Entre esglaons veïns de la Vixen, separats ~6 s,
la deriva és de **2 px**: perquè el flat expliqués un 1,2 % caldria un gradient
de 0,04 %/px, un 80 % sobre el camp.

Comprovat igualment amb la prova d'un sol paràmetre —compondre amb `flat=no`—:
el desacord entre esglaons correlaciona **0,984** amb i sense flat, i la mitjana
passa de 0,123 % a 0,122 %.

⏭️ **I la lliçó general**: quan dues hipòtesis donen la mateixa signatura, busca
primer si una de les dues pot **cancel·lar-se per construcció**. És més barat
que qualsevol estadístic.

## ⛔⛔ PROMEDIAR SOBRE LA VARIABLE EQUIVOCADA ÉS NO VEURE RES

25-08-2026, i és **la trampa mare de tot el postprocessat d'aquest eclipsi**.

Pere va marcar tres corbes al detall de la Vixen. **No eren circumferències: eren
isofotes**, i queien exactament sobre tres fronteres de fusió HDR. Les mateixes
fronteres, amb els nostres dos estadístics de sempre, sortien **netes**:

| estadístic | què deia | per què era cec |
|---|---|---|
| detector per **nivell** | **0 de 12** fronteres | busca un **GRAÓ** a través de la frontera. Si l'artefacte és un **BONY** centrat a la frontera, la discontinuïtat val **zero** |
| **mediana per anell** | **≤ 0,008 %** | una isofota està **escampada en radi** —la del fotograma de 10,08 s va de 1,57 a 2,35 R☉— i un calaix radial n'agafa el 4,3 %: dilució **×23** |
| **al llarg del contorn** | **0,05 a 0,72 % a 2,9-4,1 σ** | ✅ l'únic que segueix la mateixa corba que l'ull |

⛔ **Les mesures no estaven equivocades en el seu propi terme. Promediaven sobre la
variable equivocada.** I això va costar dos dies perseguint una cosa que ja estava
curada mentre la que Pere veia continuava allà.

⏭️ **Les tres preguntes que s'han de fer davant de qualsevol estadístic d'artefacte:**

1. **Quina corba segueix l'artefacte?** Si segueix una isofota, cap estadístic radial
   el veurà. Si segueix un radi, cap d'azimutal.
2. **Quina forma té: un graó o un bony?** Un detector de discontinuïtats és **cec a
   un bony** per construcció, i un bony és el que deixa un canvi de **curvatura** —
   que és exactament el que fa una rampa de fusió, encara que sigui C².
3. **El control, dispara?** Si dispara, l'estadístic **no és específic** en aquella
   zona i el seu PASS no vol dir res. Aquí la porta H2 donava PASS amb un terra de
   control de 4,32 σ i una frontera de 4,14: **el control li tapava la troballa**.

## ⛔ UN CONTROL QUE DISPARA DIU QUE EL TEU ESTADÍSTIC NO ÉS ESPECÍFIC

25-08-2026, a l'arc que Pere va marcar en verd. La mesura al llarg del contorn
donava 0,49 % a 4,1 σ a la frontera de fusió... i **el control aparellat** —el
mateix contorn desplaçat 110 px, on no hi ha cap frontera— donava 0,22 % a 3,7 σ.

Un control que dispara **no és una anècdota**: vol dir que allà l'estadístic no
distingeix la frontera de la corona. A la corona interior hi ha estructura fina
de veritat i la base transversal la llegeix com un tret.

⏭️ **La mesura que sí que decidia** era una altra: la mediana per anell del
detall als **dos** trens. Val ≤ 0,008 % a tots dos, seixanta vegades menys que
el contorn, i la Vixen **no hi té cap frontera**. Allà no hi ha cap anell.

## ⛔ UN REBUT QUE NO DIU AMB QUINS PARÀMETRES S'HA FET NO ÉS UN REBUT

25-08-2026, enxampat per **Codex** llegint un traspàs meu. Vaig escombrar sis
valors del tall de saturació, en vaig treure una recomanació de producció, i el
traspàs **la va anomenar amb el nom d'un altre paràmetre**. Va passar per dues
raons alhora, i les dues són trampes:

1. **Dos paràmetres veïns amb noms que s'assemblen i valors que s'assemblen.**

   ```python
   taper = C.rampa((C.SOSTRE - brut_pes) / (C.RAMPA_SOSTRE * C.SOSTRE))
   w[brut > C.SOSTRE] = 0.0
   ```

   `PILOT_SOSTRE` és el **tall dur** de saturació (producció 0,85) i
   `RAMPA_SOSTRE` és **l'amplada del degradat** de pes (producció 0,80). Jo
   havia provat tots dos en dies diferents. ⚠️ Les fronteres de fusió cauen a
   `SOSTRE/t`: **només el tall les mou**; la rampa només en canvia la forma.

2. **Els rebuts no enregistraven cap dels dos.** Sis sortides amb sostres
   diferents tenien JSON indistingibles, o sigui que **no hi havia manera de
   comprovar la nomenclatura contra les dades**. Sense això, l'error no es podia
   enxampar llegint el producte: calia llegir el codi.

**La mesura**: `desa()` —el pas obligat de tots els rebuts de totes les fases—
hi estampa `parametres_del_pilot`: les variables `PILOT_*` presents i els
derivats (`sostre_fraccio`, `sostre_adu`, `rampa_amplada`,
`pes_ple_per_sota_adu`, `ordre_rampa`). Un sol lloc, perquè no es pugui oblidar
en una fase nova.

⏭️ **Segona ronda, i el meu arranjament també mentia.** El vaig posar a
`desa()` estampant `C.SOSTRE`, que és el de la **Vixen**, a **tots** els rebuts.
La Sony té el seu tall i el tenia com a literal `0.85` amagat a `sony.py`, o
sigui que amb `PILOT_SOSTRE=0.80` un rebut de la Sony **declarava 0,80 quan els
píxels s'havien tallat a 0,85**. La cura no és endevinar de qui és el rebut:
és **declarar sempre els dos trens**, i donar a cadascun la seva variable
(`PILOT_SOSTRE` i `PILOT_SOSTRE_SONY`). ⚠️ I en va sortir una limitació que no
sabia que tenia: com que la Sony no llegia la variable, **l'escombrada de
sostres només havia mogut un tren**.

⛔ **I una tercera, de coordinació, que val per a qualsevol índex compartit.**
Resegellant els SHA-256 vaig fer `re.sub(..., count=1)` sobre `ACTIVE.json` i
`"delta_sha256"` **surt a tres blocs**: el `count=1` va encertar el primer, que
era el d'una branca aliena, i **li vaig trepitjar el hash**. Es va poder
restaurar perquè n'hi havia còpia. La regla: **en un fitxer d'índex compartit,
acota sempre l'edició al teu bloc** —localitza'l i edita per línies dins seu—, i
**diff contra la còpia abans de dir que està resegellat**. Dir «SHA-256
resegellats» sense comprovar-ho és exactament la mateixa falta que declarar un
artefacte arreglat sense el jutge.

⏭️ **I la lliçó que va més enllà del nom.** Per anomenar bé el paràmetre s'ha
d'entendre què fa, i entendre-ho va canviar la decisió: el tall **descarta
píxels alts**, o sigui que baixar-lo és una **cura** si el problema és no
linealitat del pou i un **pal·liatiu** si és el flat. Les dues hipòtesis donaven
el mateix número i veredictes contraris. **Una errada de nomenclatura pot amagar
que encara no saps què estàs decidint.**

## ⛔ L'ULL: com mirar una corona sense equivocar-se

El motiu pel qual un model de visió s'encalla amb aquests artefactes és concret i
val la pena tenir-lo escrit: **les imatges que rep van reescalades i a 8 bits**,
i un esglaó de fusió del 0,05 % hi desapareix. La conseqüència operativa no és
«mirar millor» sinó **no decidir mirant**: la imatge serveix per **localitzar**,
el número per **decidir**, i el jutge extern per **validar**.

I hi ha dues vistes que separen per construcció allò que en cartesianes es
confon. Totes dues amb `skimage.transform.warp_polar` i matplotlib per als eixos
(`3-RECERCA/tools/pilot_vixen_claude/vista_polar.py`):

| vista | eix vertical | què hi surt RECTE |
|---|---|---|
| `--eix radi` | log **r** | **horitzontal** = arc concèntric · **vertical** = plomall |
| `--eix nivell` | log **nivell** | **horitzontal** = costura de fusió |

⛔ **I per què la de nivell és imprescindible**: una frontera de fusió **no és una
circumferència sinó una isofota**. Al pilot, la del fotograma de 10,08 s va de
**1,58 a 2,37 R☉** —un recorregut de 0,8 R☉— mentre que **en nivell és un punt**.
Per això la vista polar radial no ensenyava cap ratlla horitzontal i la de nivell
sí. I per la mateixa raó, ⛔ **buscar pics de `∂I/∂r` en polars NO detecta
costures**: marca tota la corona interior, on el gradient radial és enorme de
veritat.

**Detector automàtic**: `detecta_costures.py`. Deriva —de fet, resta la
tendència— respecte del **logaritme del nivell**, sobre el **detall** i no sobre
la imatge crua, i el llindar **se'l calibren nivells triats a l'atzar lluny de
cap frontera**. Validat amb entrada dolenta coneguda: sobre el detall sense
corregir dispara **2 de 12** fronteres (les dues de 1,98 R☉, 0,0272 % contra un
terra de 0,0150 %) i sobre el corregit **0 de 12** (totes per sota de 0,0005 %).

⚠️ **Dos errors que vaig cometre construint-lo, tots dos de la mateixa família:**

1. **el control s'ha de construir EXACTAMENT com la mesura.** Barrejant els
   valors en lloc de les etiquetes de nivell, el terra sortia **4.000 vegades**
   més gros que el senyal;
2. **amb calaixos adaptatius, cap derivada.** Els Δx són molt desiguals i
   `np.gradient` hi explota. Cal reamostrar a graella uniforme i fer servir el
   **residu contra la tendència suau**, no la derivada segona.

## ⛔ I les tres regles que se'n deriven

1. **Tota mesura ha de portar el seu control**, i el llindar se'l calibren els
   controls, no es tria. Un «detector» sense control mesura el mètode.
2. **Quan els artefactes són més densos que la finestra de la mesura, cal
   mesurar-los a l'espai on són escassos**, no a l'espai on són densos.
3. **Un estadístic que promedia sobre azimut no pot veure el que és local.** Si
   l'artefacte varia amb l'angle, la porta ha de reportar **el pitjor cas**, no
   la mediana.
4. **La imatge mana sobre el número.** Genera la vista de diagnòstic a cada
   etapa, amb les fronteres dibuixades a sobre, i **mira-te-la tu** abans de
   declarar res.


## ⛔⛔ NORMA DEL RECTANGLE — val per a QUALSEVOL filtre

**Ordre de Pere, 23-08-2026, i diu que és un error MEU RECURRENT.**

> Un filtre s'aplica a **TOT el rectangle de la imatge**, no a una
> circumferència. Si no, **quedaran halos**.

Val per a **tot tipus de filtre**: pas alt, MGN, NRGF, FNRGF, WOW, ACHF,
màscares de detall, capes de realçat, el que sigui. No és una preferència
estètica: una capa de filtre que s'apaga **dins** de la zona que encara té
dades deixa una regió plana a gris neutre, i quan es munta a Photoshop
—Overlay, Soft Light, el que sigui— aquella frontera **és un halo**. No importa
que la transició sigui suau, ni que l'amplitud hi sigui petita, ni que el salt
de mediana mesuri zero: el que l'ull veu és el **canvi de règim**, i una
textura que s'atura es veu encara que la mitjana no canviï gens.

Formes que pren l'error, totes vistes en un sol dia:

- una rampa radial `r_ext` que arriba a zero a un radi triat a mà;
- una porta de cobertura azimutal amb un llindar (`cob > 0,98`), que és un
  esglaó de quatre píxels disfressat de rampa;
- un terra de luminància que aplana una regió i hi deixa un altiplà de vora
  dentada;
- un `max(x, 1e-30)` davant d'un logaritme, que hi planta un arc dur.

**L'única cosa que pot aturar un filtre és que no hi hagi dada.** Si l'exterior
surt lleig, la reparació és **aigües amunt** —el flat òptic, el cel, les
estrelles, el registre— i **mai** retallar un cercle. I si un defecte de fora
no es pot arreglar avui, es lliura visible i s'escriu al rebut: tapar-lo amb
una màscara circular és canviar un defecte que es pot mesurar per un que no.

Comprovació: el lliurable ha de tenir valors **fins a les quatre cantonades**
del llenç, i cap control de costura pot dir `MOSTRA_DEGENERADA` per excés de
zeros exactes.

# Trampes ja pagades — no les tornis a descobrir

Cada línia ha costat almenys una tarda. Font entre parèntesis.

## Registre

- **La corona no deriva a la velocitat de les estrelles** (0,578 contra 0,610
  ″/s): la muntura anava a taxa solar. Alinear amb el número estel·lar escombra
  3,4 px. (`76` §2)
- **La correlació de fase de la corona enganya dues vegades**: sense suavitzar
  (σ = 3 px a mitja resolució) surt 0,25 px del model; amb radi interior a 490
  px s'enganxa a les protuberàncies (saturades) i al que la Lluna descobreix,
  que es mou amb la Lluna. Radi interior ≥ 600 px o 1,25× el radi de saturació.
  (`78` §1)
- **El flare i el patró de difracció són fixos al sensor** i ancoren la
  correlació a zero prop del Sol (falsa deriva nul·la). Restar una plantilla
  estàtica també pica a zero per construcció. (`71` §3)
- **El matched filter de «disc fosc» clava el centre a un racó pel vinyetatge**;
  cal centre-vora. (`71` §3)
- **El signe de `scipy.ndimage.shift`** va doblar el desajust d'un apilat (17
  px). Tot apilat porta verificació independent del limbe (< 0,5 px entre
  membres). (`71` §3)
- **Sense ancoratge a la placa estel·lar, el centre solar porta 3,64 px de
  biaix**; i el centre de referència és el del **Sol**, no el lunar (3,1 px
  Sony, 6,4 px R6 de biaix als radis). (`75` §5, `76`)
- **Alt/az refractat per a qualsevol apilat de gran camp**: una translació pura
  ignora el 0,8 % de compressió vertical i els 0,138° de rotació del salt Sony.
  (`75` §5)
- **`astroalign` no serveix** (cap font puntual fiable) i el radial blur de
  Photoshop **mai** (cec a tangencials, canvia la fase). (`73` §2.1, §3.7)

## HDR

- **El cel de la totalitat no és estacionari** (V de ±20 %); com que cada radi
  el domina un esglaó pres en un instant diferent, sense anivellar el fons per
  fotograma surten arcs a les fronteres de saturació. (`76` §5 bis)
- **Encadenar raons entre esglaons és un passeig aleatori**: cal ajust global.
  I el que aquell ajust mesurava era cel **i extinció** (k = 0,402): els
  factors es van retirar i el compost és PENDENT de refer amb la normalització
  per massa d'aire. (`76` §4, `78` §3)
- **La gota del drizzle és de 2,0 px de sortida, ni un menys**: un píxel d'un
  pla de Bayer fa dos de sortida i només 2,0 dona partició de la unitat; per
  sota, escaquer a la diagonal de Nyquist (5.620× la potència mitjana amb 1,70).
  Cost real de fer-la gran: < 1 %. (`76` §3)
- **No hi ha drizzle 2×** amb aquestes dades: la deriva és una recta i el
  ditherat és 1-D. Més resolució = deconvolució. (`78` §9)
- **Anivellar cada apilat al seu propi valor mitjà** deixava 50 ADU/s entre el
  2 s i el 10,3 s (6 % de corona a 1,96 R☉): fons **comú** a tots, el més clar,
  s'afegeix pedestal i mai se'n treu. (`78` §4)
- **La màscara lunar dura** feia anell (20 %): suau, 14 px. (`76`)
- **La rampa de saturació**: 0,25 → 0,80. (`76`)

## Realçat i revelat

- **Dividir per la desviació local iguala el contrast a tots els radis** (cel a
  5 R☉ amb el mateix gra que la corona a 2): jerarquia real 124:1 → 2,7:1, i
  els «radial spokes», les vores dures i la trama fina eren les tres la mateixa
  causa. Detall additiu, guany declarat per banda, encongiment de Wiener, mai
  dividir per l'amplitud local. (`76` §5 decies)
- **Bandes en graus (log-polars), no en píxels**: 10 px és 1,1° a 1,2 R☉ i
  0,3° a 4 R☉; no hi ha guany bo als dos radis. (`76` §5 undecies)
- **El detall va sobre la pantalla, després de la corba**: el pendent de la
  corba és 0,00–0,07 a 1,03–1,5 R☉ i 2,0–2,3 al cel; abans de la corba se'l
  menja a la corona interior (×12 → ×0,4) i el dobla al cel. (`76` §5 undecies)
- **La corba es calibra sobre L sense realçar**; calibrada sobre la realçada,
  tocar un guany mou els ancoratges i crema la corona interior. Les bandes es
  prenen del **logaritme** del contrast. (`76` §5 nonies)
- **No dividir pel perfil radial abans de la corba** (s'aplana a 0,7–0,9,
  s'inverteix a 0,92): la caiguda radial és el que fa que sembli una foto.
- **No extrapolis el perfil radial amb llei de potència fora del cercle
  inscrit**: allà ja no hi ha corona sinó halo i cel, `L/perfil` passa d'1,0000
  a 1,125 i surt un gradient circular. Sectors azimutals iguals a tots els radis
  i unió C¹. (`76` §5 decies)
- **Cap estadística per columna sobre un conjunt d'angles que canvia**: passat
  el cercle inscrit, mitjana o Fourier canvien de forma quan les files cauen →
  graó → arcs. (`76` §5 undecies)
- **El terra de soroll d'una banda no és el seu rms al cel** (mesura
  estructura, tanca la porta on hi ha senyal): realització sintètica amb la
  correlació del compost (soroll blanc ⊛ gota), més el sistemàtic d'escala fina
  ×2,97. I l'estimador **emmascarat i robust** (una gaussiana sense màscara a
  la vora va deixar la porta de Wiener 7× tancada tota una tarda). (`76` §5
  terdecies)
- **«Finit» no vol dir vàlid**: les files 41–84 del compost tenen cobertura
  3–260; la validesa és la caixa `RETALL`. Un diagnòstic ha d'usar la mateixa
  màscara que el codi que diagnostica. (`76` §6)
- **El test d'anells es fa per sectors i sobre D nu**: els arcs de Pere eren als
  sectors de dalt i de baix (vora del fotograma) i el test «net» mirava els
  laterals; la corba de la foto els amaga i la capa de pas alt els ensenya.
  Finestra de guany per distància a la vora (2,5 σ) i unió C¹: un graó de 0,05 %
  × guany 5 ja és un arc. (`76` §5 terdecies)
- **La corba del sketch és un spline pels seus nivells, no una log-quadràtica**
  (pendent 2,3–2,5 al cel per construcció; el sketch demana ~1). Color per tres
  ancoratges **en sRGB** (l'objectiu 1,28/0,68 era Display P3 sense convertir).
  I mesura la geometria del sketch abans d'afirmar-ne res (R_lluna 1028 px, no
  1160). (`76` §5 duodecies)
- **Les línies radials del limbe són corona**, no artefacte: les mateixes
  crestes al segon tren al mateix PA a 0,08–0,22°. El test de centratge al Sol
  tot sol no ho tanca (un reflex intern també segueix la font). (`76` §5 octies)
- **El color daurat és físic** (massa d'aire 6,4): balanç mesurat sobre la
  pròpia corona a 1,1–1,3 R☉; el factor de guany del blau no s'aplica al color.
  (`76` §5 ter)
- **El gradient de fons és la corona**: una eina d'extracció de gradient se te
  la menja. (`Corona_HDR_Vixen/LLEGEIX-ME`)
- **Filtres publicats**: l'ACHF viu no està publicat i el de la tesi és el
  predecessor; el FNRGF de l'ApJ 2011 té l'equació de soroll repudiada per
  l'autora (sumar V_n, no restar) i la prova unitària A₀=S₀=1 és falsa; ordre
  recomanat WOW > MGN > RHEF > FNRGF > ACHF. (`73` §0, §2)

## Earthshine i halo

- **La fotometria absoluta de l'earthshine és degenerada** (pedestal de
  halo/cel indistingible d'una constant): criteris d'estructura, no de nivell.
  (`73` §0.1)
- **El model de halo ja existeix** (dos nuclis d'ales de PSF sobre la corona
  real + pla de cel); un model radial `E + A(R−r+r₀)^−α` és pitjor perquè
  absorbeix l'asimetria de la corona dins d'`E`. (`73` §0.1)
- **Les ales de la PSF no es poden mesurar amb estrelles** (límit físic: la
  corona interior és ~200.000× més brillant que l'estrella més brillant); la
  validació del halo ha de venir de la fotosfera filtrada de la parcial.
  (`75` §4)
- **`halo_sony2_full.py` porta `with_lroc=True`; el producte final és SENSE
  LROC** (`halo_sony2_noLROC.py`, rescatat a `3-RECERCA/tools/rescat_…/
  earthshine_halo_15-08/`).

## Fitxers i higiene

- **Photoshop `Load Files into Stack` posa la primera de la llista a la capa de
  DALT** (comprovat al 27.9 amb tres fitxers de prova). Els DNG porten prefix
  d'ordre per això. (`78` §6)
- **DNG lineal per a la R6 III**: negre 512, blanc **13995** (Adobe = 85 % del
  pou), `BaselineExposure` 0,26, matrius del DCP «Adobe Standard», retall Canon
  6960×4640 (libraw es queda un píxel curt), `extrasamples=False`; passar-lo
  pel DNG Converter i comprovar píxels idèntics. (`78` §6)
- **Cap script no anomena un intèrpret concret** (regla global de Pere).
- **Cap ruta de l'Escriptori antiga**: `Eclipse Vixen Unfiltered`, `Eclipse
  2026 300mm`, `6D Eclipse 2026` ja no existeixen; tot és sota
  ``.
- **Un `load("de440s.bsp")` relatiu baixa 32 MB a l'arrel del repositori**: usa
  sempre `~/.cache/skyfield/de440s.bsp`.

## Encaix de capes al Photoshop de Pere (`80`)

- **Un TIFF `II` amb capes de Photoshop porta el tag 37724 en little-endian
  (capçaleres i longituds de 8 bytes) però les DADES DE CANAL en big-endian.**
  Llegides com `<u2` surten com soroll uniforme. (`tools/encaix_sony/parse_layers.py`)
- **Un anell de colors a la costura de dues capes no s'arregla desenfocant la
  màscara** si les capes no coincideixen en to i color al mateix radi: la Sony
  hi anava cremada fins a 3,25–3,75 R☉ (rim taronja/verd de la saturació per
  canals) i 2–3× més clara i càlida que la Vixen. Es fa LUT de quantils per canal
  + residu de baixa freqüència restat, i dins del cremat la capa és la Vixen.
- **La capa Vixen aplanada de Pere s'enfosqueix a les vores** (la meitat a les
  últimes 300 files de dalt): un DoG de 280–600 px hi veu un marc; el detall es
  calcula al domini estès (la Sony hi arriba) i sense perfil radial.
- **La component d'anell d'un detall amb coring no és zero**: el coring és
  simètric però la corona té cues positives (+1,6–1,9 % de mitjana per anell).
  Restar la mitjana per anell **sobre tots els píxels on s'aplica**, després del
  coring i dels guanys; els pesos han de ser exactament els mateixos que l'aplicació.
- **`ndi.binary_opening` posa a False la vora de l'array**: fora del llenç
  (domini estès) això fa la capa negra. Erosió amb `border_value=1` + dilatació.
- **Les traces de les estrelles de la Sony al llenç de Pere són totes iguals**
  (12 px = 25″ a 47°): la direcció global és el criteri que separa estrelles de
  taques de textura; els plomalls i el raig recte queden fora per mida i residu.
- **El FE 300 mm f/2,8 GM a f/2,8 vinyeta −1,5 EV al cantó del sensor (0,70 a
  10 mm, 0,54 a 15 mm) i HI HA FLAT**: `~/Desktop/Sony Calibration/Calibració
  A7III 04-2025/Flats NETS 300mm {3200,6400}/` (A7III, a f/2,8; simetritzar 180°
  i reescalar pel pitch: `tools/encaix_sony/flat_sony300.py`, perfil a
  `flat_sony300_f28_perfil_radial.csv`). Cap mesura de la Sony d'abans del 18-08 a
  la tarda no el portava. El `.lcp` de `75` §4 dona 0,86 al cantó: quatre vegades
  curt. Comprovació: Sony aplanada / Vixen lineal = 0,99–1,01 de 4 a 8,8 R☉; la
  Vixen (VSD90SS) no vinyeta al llenç.
- **La capa Vixen de Pere és una corba de to global de la Vixen lineal a ±1 %,
  excepte dues rampes de ~700 px**: ×0,61 a la fila 0 i ×0,54 a l'última columna
  (no 300 px i no només a dalt). Qualsevol residu de baixa freqüència contra la
  seva capa s'ha d'estimar amb `LUT(Vixen lineal)` dins d'aquestes bandes
  (`diag_capa_vixen_pere.py`), i llavors es pot estimar fins a les vores.
- **El «10,3 s» de la R6 III és una etiqueta de libgphoto2: l'exposició real del
  terç de pas és 2^(10/3) = 10,08 s** (l'apilat de 10,3 s de l'HDR4 surt un 2 %
  més fosc que el de 2 s, i 10,08/10,3 = 0,979 ho clava; l'EXIF dels CR3 diu 10 s).
  Divideix per 10,08, no per 10,3; i a la fusió HDR de Photoshop el DNG s'ha de
  declarar 10,08 s. Si no, **la fusió deixa un graó del 2 % al contorn on el
  10,3 s satura** (r 1,6–2,2), que on el contorn és recte es veu com una ratlla
  tangencial (`80` §10).
- **Els cantons del llenç són un ~20 % més foscos que els punts mitjans de les
  vores i és cel** (Vixen lineal, Sony aplanada i capa de Pere ho diuen igual):
  no ho persegueixis com a artefacte; si no s'ha de veure, `_CELPLA` (cosmètic,
  luminància, rampa 4,8–6,2 R☉).

## Filtres de detall amb els dos trens (`3-RECERCA/82`, 18-08 vespre)

- **Correlació de fase amb la mateixa màscara a les dues imatges = pic fals a l'origen** (0,0
  exacte, err 0,999): per registrar corona contra corona, correlació creuada PLANA amb màscara
  suau (σ 25 px) i paràbola al pic. Signe: `xcorr(a, b)` retorna l amb b(x) ≈ a(x + l).
- **Problema d'obertura per sectors**: sobre raigs radials cada sector només fixa la component
  tangencial; la global de tot l'anell sí que està determinada; l'escala Sony/Vixen no s'observa
  així (estrelles).
- **Blanquejar per σ local (MGN) omple el camp de grumolls igualats; per ANELL (FNRGF) no.** I la
  variància per anell s'ha de fer amb mitjana NO robusta: un `fons_fourier` amb rebuig MAD sobre
  b² es menja els raigs i el que queda es dispara.
- **La porta w = 1 − n²/v sense llindar deixa passar grumolls a S/N ~ 1**: llindar de
  significació per banda (3 → 1 de la fina a l'ampla), com els n_s = {5,3,1} del WOW.
- **La vora de la caixa Vixen dins la combinada surt com una línia** si la Sony no s'aparella a
  baixa freqüència (σ 200 px) i la Vixen no s'esvaeix cap a la vora (150 px).
- La σ de la Sony per píxel Sony s'ha de multiplicar per l'escala (1,49) abans de comparar-la
  amb la de la Vixen per píxel del llenç (mateixa potència per àrea).

## Flat del camp d'un compost de Photoshop (`3-RECERCA/83`, 19-08 nit)

- **La referència no és la base: és la lluminància calibrada del mateix llenç.** Un DBE fet sobre la
  base sola no distingeix un raig de 600 px d'una franja fosca de 700 px. La base és una LUT
  estreta de ln L_c (σ 1–3 nivells) més un **guany per anell** sobre l'estructura no radial (Pere
  hi va posar 2× a 4–5 R☉); el que sobra d'això és artefacte. Sense el guany, el flat esborra els
  raigs exteriors.
- **Cap rampa radial suau no pot començar on base i referència encara difereixen de manera llisa**
  (halo de color, guany): si entra a 3,5 R☉ apareix un colze a 5,5 (la referència toca el terra
  del cel abans que la base) que es veu com «la corona s'acaba aquí». Part suau de 5 a 6,5 R☉;
  vores dures (arcs, costures, marc) des de 3,5; part radial de 6 a 7,5.
- Els graons són no radials encara que siguin circulars: l'arc de màscara a 8,6 R☉ canvia de signe
  amb l'angle. Tracta'ls com a zones de vora exactes (bandes geomètriques + detecció) i no només via
  el perfil azimutal.
- La vora d'un marc registrat (Sony girat) deixa una tira brillant a la lluminància combinada:
  erosiona la validesa 40 px abans d'usar-la com a referència, i apaga les zones de vora on el
  model és sorollós.
- Les capes de detall en Overlay/Linear Light han de tenir el camp llunyà neutre (0,5 o el propi
  perfil azimutal): el radial B tenia un pedaç de 0,43 al racó i el NRGF ±0,5, i tornaven a
  embrutar el camp que el flat havia netejat.

## El «halo» d'un compost i els DBE (`3-RECERCA/83` §6, 19-08 tarda)

- Abans de restar cap fons, mira la **corba de to per canal contra la lluminància física**: un
  anell clar que s'acaba de cop pot ser un genoll de la corba (terra dur en B a L<356, tram dret
  després) i no llum de més. Test decisiu: per sectors, el genoll cau a L constant (corba) o a r
  constant (màscara).
- La llum de 4–9 R☉ d'aquest compost és corona K+F real (1,9·10⁻⁹ B☉ a 5 R☉ amb el factor de
  `3-RECERCA/75`): treure el «halo» = restar la component azimutalment uniforme (envolupant
  inferior per anell en L, rampa C2), com LASCO; dir-ho així. Un ABE de grau 4 o un GraXpert sobre
  tota la imatge surten radials centrats al Sol i s'emporten el 60–100 % de la llum de 3 a 9 R☉.
- Després de restar en L, mapa amb una corba **sense terra amb pendent zero** (els raigs moririen
  al terra): pendent de la corda; i al vermell (sense terra) no toquis la corba.
- L'additiu pot empènyer el fons entre raigs per sota del cel: satura el Δ negatiu a −(V − terra)
  sense aixecar el que ja estava per sota (el sud fosc de Pere és seu).
- Els filtres Overlay deixen una mitjana radial al camp exterior (1–1,5 nivells) que el halo
  amagava: una capa radial a dalt de tot la compensa; recalcular-la si canvien opacitats.
- **Per ensenyar estructura a la corona exterior (3,5–6 R☉) sense pintar-la**: coherència entre els dos
  trens per banda (correlació creuada normalitzada local, no el signe), amplitud en règim lineal, entrada
  radial molt gradual (2,8→4,2 R☉), opacitat 25 %; i **control nul** girant un tren (90/137/180°): si
  l'estructura no cau un factor ≥ 4, és del filtre. El blanquejat per anell (WHITE) i la porta amb soroll
  sintètic sol no serveixen al camp exterior: el sistemàtic (flat, costures) hi domina. Més SNR de fotons
  (fotogrames curts) no arregla el halo: +1,5 %.

## Filtres «profunds» de la corona exterior (`3-RECERCA/83` §8, 19-08 nit)

- **`lum_llenc` L_c duu el camp del Vixen, que no té flat.** La costura de `prepara_lluminancia.py`
  resta a la Sony la diferència σ 200 px amb el Vixen perquè no hi hagi graó a la caixa: la combinada
  queda amb la vinyeta del VSD90SS (≤ 3 %, +2 % a 8,5–9 R☉). Per al camp llunyà, suma-hi `corr_lf`
  (recuperable exactament repetint el warp i l'aparellament; `sf3/v7/corr_lf.npy`): la Sony sí que té
  flat mesurat. Després, fons de Fourier per anell (m ≤ 4) en ln: el pla del cel i la vinyeta
  descentrada són m = 0, 1, 2 i cap filtre no els veu.
- **Les bandes amples no poden arribar al camp llunyà**: a 7 R☉ una banda de 9° són 500 px, l'escala on
  viuen les incerteses de flat i cel entre trens (el ±3 % de corr_lf), comparables a la corona (3 % del
  cel). Esvaïment per banda, ample i gradual (2,5–3 R☉): 9° 4,5→7, 18° 4→6,5, ≤ 2° fins a 7,5→9. Amb
  les amples fins a 9 R☉ el cel surt mollat («núvols») i hi ha un anell de textura que s'acaba de cop.
- **L'MGN local pur «pinta»**: iguala el contrast a tot arreu. Pis d'anell a la normalització
  (√(v_local + n² + rms_anell²)): local on hi ha estructura, d'anell on és feble; les dues bandes més
  amples a la meitat i a un quart.
- Mitjana zero per anell **després** dels esvaïments (correcció c(r) dins del taper), i ANELL recalculat;
  fora de la caixa Vixen (un sol tren) només bandes fines a mig pes; mesura el perfil radial de la
  composició (ha de moure's < 0,001) i la rms per anell (ha de caure suaument, sense graó).
- Opacitats: RADIALS 40, MGN 30, NRGF 8 %; a 50/40/12 ja es veia pintat a l'escombrada.

## Costura de la caixa Vixen, meitats i «artefactes a les cantonades» (`3-RECERCA/83` §9, 19/20-08)

- **La convolució normalitzada σ 200 té biaix de vora**: no segueix cap gradient als últims ~200 px de la zona
  vàlida → la costura Sony↔Vixen deixava un sot de −0,1…−0,2 % a 100 px dins de la caixa, que els passa-banda veien
  com una línia. Correcció: poly4 del nucli + residu σ 200 calculat SENSE la franja de 150 px; i la caiguda del
  Vixen a la vora es mesura per vora (detrendada amb una recta a 300–500 px) i s'afegeix a L_v. Comprova sempre
  L_d − L_s_crua a 0–300 px de les quatre vores REALS (valid_v: 583..7372 × 504..5013, no la caixa nominal de Pere).
- **Cap taper de caixa als filtres**: un taper fix desplaçat fa una franja morta visible; el que decideix és una
  porta de soroll REAL i LOCAL: meitats A/B independents de l'apilat Sony (σ² = var(A−B)·wA·wB/(wA+wB)²), vàlida
  també on només hi ha Sony; res d'extrapolar «last value».
- **Mira les capes velles de Pere abans de buscar el culpable als filtres nous**: una capa de to (imatge log) amb
  el camp llunyà fosc i la màscara a 0 als triangles fa els triangles del marc Sony 3 punts més clars al compost.
  Tota capa Overlay ha de ser 0,5 EXACTE fora de dades i al camp llunyà; un «neutre» a 0,61 és un offset global.
- Res més enllà de 8 R☉: la corona és el 3 % del cel i el que passa la porta a les zones només-Sony té l'escala
  dels residus del flat (pols, 100–200 px, comuns a totes les preses). Emmascara les estrelles brillants abans
  de filtrar (anell fosc). L'HDR del Vixen ja és la pila de llargues (93 % del pes ≥ 1 s a r > 4): no en facis una
  altra. La 06988 (1 s) va trailada 25 px: fora.
- **Si Pere vol «cada píxel del fotograma», no tallis radialment**: la prova de realitat que arriba a l'última cantonada
  és la coherència entre les dues meitats de la Sony per GRUP de muntura (desplaçades 713 px pel salt): pols, flat i
  PRNU es mouen, el cel no; control nul girant una meitat 180°. Però l'anivellament per fotograma (pla + σ 300 contra la
  referència) fa que a > 300 px les meitats comparteixin la BF: allà la coherència no discrimina. I el NRGF amb anells
  parcials: ajusta el fons de Fourier mentre hi hagi ≥ 10 % de cobertura (`frac_min_fit`), no l'extrapolis (cercle a c_ple).

## Sis costures de composició entre trens (`3-RECERCA/93`, 22/23-08 nit)

**Regla mare: cada màscara i cada correcció han de mesurar allò que diuen que mesuren.** Les sis d'aquesta nit
són, sense excepció, una màscara que mirava la magnitud equivocada. Pere en va marcar tres sobre el preview 4K;
les altres tres van sortir mesurant i eren pitjors.

- **Mai facis `distanceTransform` sobre un mapa de cobertura o de validesa de píxel.** Respon «a quina distància
  ets del zero més proper», i el forat de la Lluna i els forats de saturació de la corona interior són zeros: cada
  forat es converteix en una vora i l'apodització planta un polígon fosc de vores dentades al voltant del disc.
  Mesurat: la corona interior sortia multiplicada per **0,03 a 1,05 R☉** i per **0,20 a 1,2 R☉**, amb el perfil
  radial invertit —el màxim a 2 R☉ en lloc del limbe—. La recepta Gemini (`vixen_valid = vix_warp[...] > 0`) té
  aquest defecte. **L'apodització es mesura sobre el marc del sensor**: el warp d'una imatge de uns.
- **La igualació entre trens és per canal, sempre.** Els quocients Sony/Vixen a l'anell 1,5–2,8 R☉ són
  **R 2,143 · G 2,605 · B 3,059** (±18 %). Un escalar de luminància deixa la Vixen vermellosa i la Sony blavosa:
  variació de color radial del **108 %** i un anell que l'ull situa exactament a la sigmoide de fusió. Amb guany
  i pedestal per canal, la dispersió residual és **0,64 %**.
- **Si un apilat porta mapa de pes, llegeix-lo.** L'apilat Sony v3 té cobertura completa (24,75 s) només al
  **78,3 %** del llenç, dins la caixa x 264–7926, y 40–4578; fora baixa a 13,5 s i menys. Cada zona és un
  subconjunt diferent de fotogrames amb la seva pròpia mitjana de cel: d'aquí el rectangle al fons. Es treu amb
  un **pedestal constant per zona**. ⛔ Un pla o una quàdrica per zona sobreajusta i planta fanals de color als
  cantons: provat i descartat.
- **El que tapa el Sol és la Lluna.** Amb magnitud 1,03 el disc lunar fa **1,019 R☉** i no és concèntric amb el
  Sol. Tallar la màscara de limbe a 0,985 R☉ del Sol deixa un anell de 10 px. Mesura el disc al limbe (cercle a
  144 azimuts) i talla-hi.
- **Un model de fons només val dins el domini on s'ha ajustat.** Una quàdrica ajustada a `r > 8,5 R☉` i
  extrapolada cap endins deixa residus de baixa freqüència pitjors que el gradient original. Si el que sobra és
  **vinyetatge**, la correcció és el **flat**, i va abans de l'apilat: flat i warp no commuten. Mentre el
  `MASTER_OPTICAL_RADIAL` Sony de `3-RECERCA/90` no s'apliqui, queda una variació de color radial del **≈30 %**
  entre 1,8 i 5,8 R☉, i és honest deixar el cel com a **capa** en lloc de restar-lo.
- **Abans de culpar la composició, renderitza l'entrada sola amb el mateix estirament.** Les estries circulars de
  1,05 a 1,6 R☉ són a `hdr_vixen_countss.npy` mateix —residus dels esglaons de la fusió HDR de les quinze
  exposicions—, no al muntatge. Corregir-les component seria pintar-hi a sobre.
- **L'escala entre trens no és un paràmetre lliure.** Amb els factors de `3-RECERCA/75` §5.2 (Sony 1,134×10⁻¹¹ i
  R6 2,772×10⁻¹¹ per ADU/s i píxel verd) i el quocient de corona 0,95, la predicció és **2,573** i la mesura a
  l'anell de solapament dona **2,605**: coincideixen a l'**1,2 %**. Calibra i comprova; no ajustis.
  I la **neutralització també és física**: la dispersió Thomson és acromàtica, o sigui que la corona mitjana ha
  de sortir neutra. ⛔ Les matrius `cam2srgb` de la branca Gemini són nombres inventats i diferents per tren.

## Un pas alt és un detector de defectes (`3-RECERCA/95`, 23-08)

Pere va marcar dos artefactes damunt d'un pas alt. Cap dels dos era del pas
alt: **tots dos eren coses que la imatge amb corba de to amagava i que un pas
alt amplifica**. La lliçó operativa: si vols saber si un compost està bé,
passa-li un pas alt abans de creure't cap previsualització.

Set regles noves, totes mesurades:

- ⛔ **El compost lineal no es multiplica per CAP màscara.** Ni la validesa, ni
  la cobertura, ni el pes de fusió. Un fitxer que es diu «calibrat en B/B☉» ha
  de ser fotometria; les màscares es lliuren a part i les aplica qui consumeix.
  El 22-08 el compost anava multiplicat per `validesa²` i com que
  `max()` té cantonada, el factor valia 0,56 a 2,4 R☉ i 1,00 a 2,6: un graó del
  +79 % en 0,2 R☉. **Comprovació F**: compost dividit pel mesclat reconstruït
  ha de donar 1,000 arreu (llindar 10⁻³).
- ⛔ **Una mescla de dos trens ha de ser convexa i NORMALITZADA per cobertura**:
  `(A·wa + B·wb)/(wa+wb)`. On només hi ha un tren, ha de sortir aquell tren a
  pes ple i sense enfosquir. On no n'hi ha cap, **NaN** — cap dada no és el
  mateix que zero llum.
- ⛔ **Cada pes mesura una sola cosa.** QUIN tren mana, ON hi ha camp de cada
  tren i ON el Sol està tapat són tres coses; barrejar-les en un sol pes fa que
  després no es pugui fer servir cap d'elles per separat sense arrossegar les
  altres.
- ⛔ **Cap rampa, finestra o porta pot ser un `clip` lineal, un `max()` o un
  llindar.** Són contínues però no derivables, i l'ull veu les discontinuïtats
  de derivada. I una rampa que arriba a zero a un radi concret deixa una **vora
  de textura** —dins hi ha gra i fora no— que es veu encara que la mitjana no
  canviï gens. Esvaïment **gaussià**, que no té final.
- ⛔ **Un pedestal per zona no pot ser una funció esglaonada.** Al cel no hi ha
  vores: la diferència entre zones de cobertura és de comptabilitat. Es
  desenfoca (σ ≈ 150 px) abans de restar-lo. I recorda l'escala del problema:
  **a 6 R☉ el cel val 78 vegades la corona**, o sigui que un 2,5 % de cel mal
  restat hi és el 200 % del senyal.
- ⛔ **Un control que no pot fallar no és un control.** Els de costura deien
  «0,000 σ» a totes les versions perquè el 85 % dels píxels que miraven eren
  zeros exactes fora del radi viu. Tot control ha de (a) avaluar-se només on el
  producte lliura, (b) refusar la mostra si és degenerada i dir-ho amb un estat,
  mai amb un número, i (c) haver-se provat contra un cas que **sap fallar**.
- ⛔ **Un control radial no pot jutjar el que el filtre fa a propòsit.** Cal
  descomptar l'envolupant declarada abans de mesurar. La bona forma és la
  **regressió isotònica decreixent**: l'amplitud d'un pas alt honest de la
  corona baixa amb el radi, i el que en sobresurt és un anell. Comparar amb una
  mediana mòbil no serveix: una finestra curta segueix l'anell i el fa
  invisible, i una de llarga confon una pujada llarga i legítima amb un defecte.

I dues coses per no repetir-les:

- **Treure l'esvaïment exterior del tot no és una opció**: surten les estrelles
  i el residu del flat òptic de la Sony.
- **La Lluna no pot passar per la morfologia** (`distanceTransform` sobre una
  màscara amb el forat lunar), però **tampoc se li pot acostar el suport**:
  entre 1,03 i 1,23 radis lunars hi ha la cromosfera i les protuberàncies, i si
  entren al càlcul el pas alt les converteix en taques ovalades. La geometria
  correcta és la de sempre (9 px d'erosió i 60 px de rampa), feta amb un cercle
  analític i no amb un element estructurant.

## Compta els apuntaments abans de tocar cap màscara (`3-RECERCA/96`, 23-08)

**El camp de la Sony va caure 750 px a mig de la totalitat.** Els 10 fotogrames
de l'apilat v3 són a **dos apuntaments** (13,50 s i 11,25 s), i d'aquí surt tot:

- ⛔ **Les «zones de cobertura» no són una propietat de l'instrument: són la
  petjada d'una avaria mecànica.** Anivellar-les és anivellar **un mosaic de
  dues peces**. Abans de tocar cap màscara de composició, **mira el mapa de pes
  i pregunta't quants apuntaments hi ha**.
- ⛔ **Un graó entre zones de cobertura és MULTIPLICATIU, no additiu**, perquè
  el mateix cel es veu a dues posicions del sensor: és **vinyetatge**.
  Comprovació: si el **quocient** és constant al llarg de la vora i la
  **diferència** varia, és un guany. (Mesurat: quocient 0,978–0,989 contra
  diferència que varia ×2,7.)
- ⛔ **El llenç el dimensiona la UNIÓ de tots els apuntaments, no el sensor.**
  El nostre en llençava 697 px en silenci. I **un sol llenç declarat**: el de
  Photoshop no coincidia amb el de l'apilat i en perdia el 3,4 %.
- ⛔ **El flat va ABANS de qualsevol warp**: no commuten. Si el pipeline no hi
  deixa lloc, l'ordre del pipeline és el defecte.
- ✅ **Un salt de muntura és un dither**: la zona comuna entre dos apuntaments
  dona el quocient del vinyetatge entre dos punts, o sigui que pot **mesurar**
  el flat que falta.

I l'escala del problema, per no oblidar-la: **a 6 R☉ el cel val 78 vegades la
corona**. Un 1,4 % de cel mal restat hi és ~100 % del senyal.

## Nou trampes del pilot LDIC (`3-RECERCA/99`, 23/24-08)

**Vuit de les nou van sortir perquè un control va donar un número impossible, no
perquè algú mirés la imatge.**

- ⛔ **Els temps d'exposició de l'EXIF són els NOMINALS del menú.** El físic és
  al MakerNote: `TargetExposureTime` (Canon), `SonyExposureTime` (Sony). Als dos
  cossos, **1/60, 1/30 i 1/15 són de fet 1/64, 1/32 i 1/16 — un −6,25 %**; el
  «10,3 s» de la R6 és **10,079368399159**. Deu dels quinze esglaons de la Vixen
  van per damunt de l'1 %. **Física per escalar, nominal per indexar** el màster
  dark, i totes dues s'han de portar: confondre-les fa que el màster no es trobi
  o, pitjor, que se'n triï un altre.
- ⛔ **Un `sol_x` que ajusta un model lineal amb residu 0,000000 px NO és una
  mesura.** Avaluar-hi un oracle és avaluar el model contra ell mateix. Al
  manifest de la Vixen ho era, i la primera versió de la porta de registre hi
  donava 0,00217 px i era **vàcua**.
- ⛔ **El centre del limbe lunar mesurat està biaixat ~8 ″**, i el biaix és
  **el mateix als dos trens** (3,65 px a la Vixen i 3,85 a la Sony al llenç
  comú, coincidents a 0,21 px): és la corona asimètrica que vessa per damunt de
  la vora fosca. El radi ajustat també en surt un 1 % gran i **decreix amb
  l'exposició**. **L'efemèride és millor.** El que decideix no és model contra
  mesura: és posar-hi un segon instrument.
- ⛔ **El nivell de blanc efectiu no és el `white_level`.** A la R6, al fotograma
  de 10,08 s, la mediana a 1,05–1,15 R☉ val 15.857 ADU sobre el fosc —el pou
  n'és 15.872— i la màscara `cru >= 16383` només n'atrapa el **0,9 %**. El tall
  que serveix és `SOSTRE` (0,85 del pou).
- ⛔ **Si restes el cel, la SATURACIÓ i la VARIÀNCIA es jutgen amb el valor
  CRU.** Un píxel que és al pou hi és tant si el cel hi és com si no. Sense
  aquesta separació, el fotograma llarg saturat passava a ser el dominant, el
  denominador es multiplicava per **61** i el compost queia un **94 %** a
  1,15–1,25 R☉.
- ⛔ **Un model de cel ajustat per píxel segueix la corona a dins de 2 R☉ i se
  la resta** (perfil negatiu de 1,18 a 1,99 R☉). El cel és una superfície
  **llisa**: ajusta-li una quàdrica **només on la corona és petita** i avalua-la
  a tot el camp. I ⛔ **el seu COLOR no es pot treure de l'ajust temporal de cada
  pla** —la palanca és 1/0,30 i el blau surt negatiu—: mesura'l on el cel mana.
- ⛔ **Amb un tren que ha canviat d'apuntament, el cel s'ajusta al LLENÇ i no al
  sensor.** El cel és fix al cel. Per píxel de sensor, amb el salt de 750 px de
  la Sony, la quàdrica dona un residu del **51,5 %**; al llenç, **3,1 %**.
- ⛔ **Un passa-alt sobre `ln I` s'inventa estructura si no li treus el perfil
  radial primer**: la CURVATURA del perfil és el que llegeix com a detall (6,6 %
  sobre una corona perfectament llisa; 0,33 % si el treus). I ⛔ **les escales
  d'un multi-σ comparteixen entrada, o sigui que el seu soroll se suma
  COHERENTMENT** (1,66 σ sumant a pèl, 0,40 σ amb pesos que sumen 1). I ⛔ **`ln I`
  on el senyal va a zero es dispara i passa qualsevol porta de soroll**: posa-hi
  un terra de S/N.
- ⛔ **L'anivellament de cel NO treu el cel, l'iguala entre fotogrames.** Més
  enllà de **2,41 R☉** el compost és sobretot cel (a 5 R☉ n'és 9,2 vegades, i
  dins el disc lunar el **85 %**). Cap fotometria coronal per damunt de 2 R☉
  sense restar-lo.

### I dues portes que no tenien dents

- ⚠️ **La porta G (excés sobre l'envolupant isotònica < 1,30) NO caça un graó de
  fusió de la lluminància.** Mesurat sobre un perfil `r^-2,5`: un anell del 45 %
  dona 1,17–1,23 i un graó multiplicatiu del 40 % dona 1,15 — tots dos PASSEN.
  El PAVA els absorbeix agrupant-los amb els veïns. **La G és per al perfil
  d'amplitud d'un PAS ALT**, i allà sí que serveix.
- ⚠️ **Un llindar que és un màxim sobre moltes proves s'ha de calibrar amb la
  seva pròpia distribució nul·la**, no triar-se. I ⛔ **el nul no es pot fer
  permutant els residus observats** si el que busques hi és a dins: amb un salt
  de muntura de 750 px, el p-valor permutat sortia **0,26**. Compara **models**
  (recta contra recta-més-graó) i simula el nul amb el soroll net.

---

## Trampes del 24-08: anells, flats girats i controls sense dents

Detectades perquè **Pere va mirar la imatge**, no perquè cap control cantés. Les
tres primeres són la mateixa malaltia a tres llocs. Canònic: `3-RECERCA/100`.

### ⛔ Restar un perfil radial per calaix fa una escala d'esglaons

`imatge - med[idx]`, amb `idx` d'un `np.digitize`, resta una **funció
esglaonada**: salta de cop a cada frontera de calaix, i com que la frontera és
una **circumferència rasteritzada sobre la graella de píxels** —amb trams de x
constant de fins a 31 px—, cada salt surt amb **dents de serra**.

Mesurat al `DETALL_ln` lliurat pel pilot, amb calaixos de 6,97 px: serrell de
**5,43 % a 1,25 R☉**, 3,97 % a 1,48 i 2,43 % a 1,70. I el quocient
**serrell / rms local val 1,00-1,13 de 500 a 2.000 px**: a la corona interior el
«detall» ERA el serrell. La fracció de variància purament radial del detall
valia **73 %** a 505-700 px.

**El fix és `np.interp`, no més calaixos.** Amb n = 1.200 el serrell encara val
tant com tot el senyal real: l'error d'un esglaonat baixa ∝ Δr i el de la
interpolació ∝ Δr². Una spline cúbica no aporta res sobre `np.interp`.

### ⛔ I el perfil radial d'una corona es fa en log r, no en r

Una corona és una suma de lleis de potències, o sigui **una recta en log-log**.
Amb calaixos uniformes en r i una gaussiana, tant la interpolació com el
suavitzat **esbiaixen la curvatura**. Sobre una corona de Baumbach amb 300
calaixos: uniforme+gaussiana 0,256 % i 0,832 % al limbe; **log r +
Savitzky-Golay d'ordre 2, 0,043 % i 0,194 %** — sis vegades millor amb els
mateixos calaixos. De propina, els calaixos surten estrets on el perfil és dret.

Dues coses més de la mateixa funció: els calaixos s'han de definir **sobre el
rang on hi ha dada** (amb el disc lunar dins del rang, els de dins queden buits,
s'omplen per extrapolació plana i el suavitzat els barreja amb els primers bons:
**1,62 % just al limbe**), i el suavitzat no pot fer `mode="nearest"`, que
repeteix una constant i esbiaixa la vora exterior (0,32 %).

### ⛔ Un perfil per calaix calculat PER CANAL fa els anells DE COLOR

Si la vista normalitzada radialment divideix per un perfil per canal, cada canal
té la seva pròpia escala d'esglaons i **els anells surten verds i blaus**
(mesurat: G−B 1,95 %, G−R 2,25 %). I aquella vista existeix **justament perquè
s'hi vegin els anells de fusió**: n'hi posava 700 de falsos. Arranjada,
l'ondulació radial passa d'1,62 % a **0,064 %**.

### ⛔ Un lineal de Bayer sense balanç de blancs verdeja, i NO és un CFA girat

El verd hi és **+47 % sobre el vermell** perquè el pipeline no aplica balanç ni
matriu de color a propòsit. ⛔ **Una permutació R↔B deixa el verd al mateix
lloc**: un CFA mal ordenat donaria un biaix vermell/blau i **no pot** produir un
domini verd. I si hi ha dos trens, **cada un porta el seu factor**: a 2-3 R☉ la
Vixen té G/R 1,642 i la Sony 2,037, i un factor comú deixaria una costura de
color del 24 %.

### ⛔ Una rampa lineal de saturació deixa un colze que el passa-alt converteix en vall

`clip((SOSTRE − x)/(k·SOSTRE), 0, 1)` arriba a zero amb **pendent no nul**: quan
una exposició surt de la mescla ho fa amb una discontinuïtat de derivada, i un
passa-alt la pinta com una **vall fosca de 0,07-0,14 % i ~15 px d'ample** que
**segueix una isofota** —serpenteja, i té osques en V allà on un plomall empeny
el contorn—. N'hi ha una per esglaó d'exposició que se satura.

El fix és `u·u·(3−2u)`: fa C¹ el que era C⁰. ⚠️ **No és la cura de fons**:
l'amplitud del colze és proporcional al desacord entre esglaons d'exposició, i
la smoothstep només el reparteix per la rampa en lloc de concentrar-lo en una
línia.

### ⛔ Un control que es normalitza per la dispersió de la seva pròpia entrada és cec

El control d'entrada llisa dividia `rms(detall)` per `rms(entrada)`. Però la
dispersió de l'entrada està **dominada pel perfil radial que s'acaba de
treure**, o sigui que divideix per un número enorme: amb l'escala d'esglaons
posada donava **0,33 % i PASS** mentre l'artefacte valia més de la meitat del
detall.

I corria **sense disc lunar**, amb una `r^-2,5` que divergeix al centre: el
**98 % del «detall» que mesurava vivia a r < 1,04 R☉**, on de veritat hi ha la
Lluna. Amb la geometria bona el número baixa **14 vegades**.

⛔ Un control ha de tenir **la geometria de veritat**, i el seu criteri ha de ser
**quina fracció del que declarem podria ser artefacte, banda per banda** —perquè
l'artefacte viu al limbe i una mitjana sobre tot el camp l'hi dilueix amb els
milions de píxels de fora.

### ⛔ La mediana no és additiva

`mediana(A) − mediana(B) ≠ mediana(A − B)`. Amb un gradient azimutal gros i de
direcció diferent a cada conjunt, els dos camins donen resultats **de signe
contrari** (mesurat: +1,5 % contra −0,7 %). Vol dir que un «perfil radial» fet
amb medianes és **mal definit a l'1-2 %** en aquest règim. Si el que has de fer
és comparar dos perfils, fes servir un estimador **lineal** (mitjana en log) i
la comparació és inequívoca.

### ✅ I una trampa que no ho era: com es valida un flat

Amb **dos conjunts de flats amb cels independents** i el cos girat entremig. En
log, `log A − log B` **anul·la exactament** el terme fix al sensor, i si la
vinyeta és radial al voltant del centre de gir també anul·la el telescopi: el
que queda és cel. I si s'aplica als dos la **cadena del màster** —que ha de ser
lineal en log per ser inequívoca— la diferència dels dos màsters radials és la
contaminació de cel, mesurada i no suposada.

⚠️ Dues coses que aquest disseny **no** pot donar: l'**eix òptic** (si no hi ha
estructura fixa al telescopi, no hi ha res sobre què registrar, i l'estadístic
azimutal el domina el cel de cada sessió) i la separació entre **vinyeta i
gradient de cel** de baix ordre, que són degenerats perquè tots dos giren amb el
cos.

⚠️ I mira l'**inclinòmetre del cos** (`RollAngle`/`PitchAngle` al MakerNote)
abans de suposar cap orientació: al projecte, els flats del 22-08 estaven **12,4°
girats respecte de la totalitat** i ningú no ho havia mirat.

---

## Trampes i vies del 24-08 (segona ronda): fusió, portes i color

### ⛔ MAI `distance_transform_edt` sobre un mapa de cobertura amb el forat de la Lluna

Ja era la nota canònica del projecte i hi vam tornar a caure. La transformada
mesura la distància al **zero més proper**, i el pes val 0 dins del disc lunar:
per a la corona interior el zero més proper és **el forat**, o sigui que la
rampa surt del limbe cap enfora i és **una circumferència centrada al Sol**.

Mesurat: el pes del tren bo valia **0,090 a 1,12-1,20 R☉** i no arribava a 1
fins a 1,60, o sigui que **l'altre tren posava el 91 % del detall de la corona
interior**, el contrari de la regla declarada tres línies més amunt.

**El fix és `binary_fill_holes` abans de la transformada**: llavors els únics
zeros són els de fora de la petjada i la rampa segueix la vora del sensor, que
és un rectangle girat. I la rampa, `smoothstep`, no un clip lineal.

### ⛔ Una derivada logarítmica amb un sol Δlog r és una regla que canvia de llargada

Amb calaixos uniformes en r, `diff(log r)` va com 1/r. Multiplicar la punta de
la derivada per la **mediana** del pas converteix el resultat en un graó amb un
error que depèn del radi: mesurat amb un graó injectat del +5 %, la porta en
deia **+1,42 % a 1,20 R☉ i +8,33 % a 5,00** —factor **5,9**— i les transicions
reals queien totes a la meitat cega. Amb `np.gradient(lr)` i una calibració
d'injecció **interpolada** en lloc d'una mediana, queda en ×1,22.

⚠️ Això va **rectificar un número publicat**: el pitjor graó de fusió no era
−0,49 % sinó **−1,46 %**.

### ⛔ Un camí codificat a una variant compara coses incompatibles en silenci

Tres funcions llegien sempre el compost del segon tren de la variant «anivellada
per anell», també quan el primer venia de la variant amb el cel restat. El
quocient entre les dues variants val **×2,51 a 2-3 R☉ i ×74 a 5,5-8**: qualsevol
comparació així és soroll pur. **Deriva la variant de l'etiqueta i falla tancat
si no hi és.**

### ⛔ Una porta que només mira la frontera EXTERIOR no pot caçar un tall interior

`porta_rectangle` mesurava `rmax` per sector i donava PASS a un `rr > 1,12`
imposat. Ara mira també la frontera interior, amb el criteri que la fa caure:
**l'única frontera interior legítima és l'ocultador**, que és la Lluna i és un
cercle de radi conegut; un forat circular **més enllà** l'ha posat algú. I sense
el radi de l'ocultador declarat, **la comprovació no s'executa i el rebut ho
diu**, per no convertir un silenci en un aprovat.

La va caçar de seguida: la banda que el tall llençava té S/N mediana **298** i el
**100 %** dels píxels per damunt del llindar.

### ✅ El COLOR separa la corona del cel, i és una prova, no un ajust

**La corona és de color solar i el cel és blau.** Amb
`I_canal = a·k_corona[canal] + b·k_cel[canal]` hi ha **tres equacions i dues
incògnites**: un grau de llibertat per fallar. Els vectors no es trien —`k_corona`
es mesura on el cel encara no mana i `k_cel` on mana ell—. Residu mesurat al
pilot: **0,01 a 1,26 %**.

⛔ **La prova que no és circular**: dos trens amb sensors, filtres i calibratges
diferents donen fraccions de cel que **coincideixen a 1 punt a tots els radis**,
i el cel iguala la corona a **~2,4 R☉**, el mateix número que la via temporal.

Tres coses que se'n treuen i que la via temporal no pot donar:

- el cel **sencer**, constant i variable, mentre que un ajust `total(t) =
  corona + S·f(t)` només veu el variable i és una **fita inferior**;
- amb el cel tret, la discrepància entre trens sobre la **corona sola** resulta
  ser un **factor constant** (dispersió 0,60 % sobre un factor 2,5 en radi) i no
  una forma: el que falta és **un sol número**;
- i per tant una **fita** sobre la part constant del cel sense cap dada nova.

⛔ **Però per píxel NO es pot.** Els dos colors només estan separats per
ΔB/G ≈ 0,11 i la pseudo-inversa **amplifica el soroll ×2,8 a ×3,1** (número de
condició 7,4): a 3 R☉, un 1 % de soroll per canal es converteix en un 11,8 %
sobre la corona, i el mapa surt ple d'una lluïssor difusa que **no és corona**.
El que sí que es pot, i és físic: **el cel no té estructura fina**, o sigui que
es resol sobre una versió molt suavitzada —convolució **incompleta normalitzada
pel pes**— i s'ajusta una quàdrica **on el cel està determinat** (r ≥ 2 R☉),
que s'avalua a tot el rectangle. Retallar el cel a zero a dins deixa **un forat
molt més gran que la Lluna**, i un forat és físicament fals.

⚠️ **I els vectors de color s'han de mesurar al MATEIX espai que les dades.** Un
color instrumental (ADU/s per pla CFA) posat sobre dades calibrades (B/B☉ per
canal) dona un 26 % menys de cel. No és una contradicció: són espais diferents.

### ⛔ El color del cel es mesura ON i COM es restarà

Dues maneres de fer-ho malament, totes dues vistes el 24-08:

1. **Deduir-lo de les amplituds d'un ajust temporal per pla.** Dona un blau
   **36 % massa alt**, i amb ell el producte amb el cel restat surt amb el
   **64,5 % dels píxels de blau negatius** a 4,4-5,1 R☉. El número bo és el que
   **convergeix**: mesurat al compost, B/G val 0,4481 a 3,0-3,6 R☉, 0,4662 a
   4,4-5,1, 0,4706 a 5,5-6,5 i 0,4718 a 6,5-7,5 — una asímptota neta.
2. **Mesurar-lo amb un pes diferent del que farà servir el compost.** La
   mediana per fotograma i la mitjana ponderada per `t²/var` no donen el mateix
   quan el senyal és feble.

⚠️ **I l'amplitud del cel també.** Amb el color corregit, el blau del producte
queda net però el **verd** hi surt negatiu al 55 %: el cel temporal val
1,318·10⁻⁸ i el del color 1,209·10⁻⁸, un **9 % més**, i aquell 9 % és més gran
que la corona que hi queda (7 % del total a 5 R☉). ⛔ **Un model de cel que
només veu la part variable és una fita inferior del cel PERÒ pot sobre-restar
igualment**, perquè la seva forma espacial extrapolada cap enfora no té per què
coincidir amb la del cel de veritat.

### ⛔ Una porta RADIAL no pot mesurar una frontera que és una ISOFOTA

Les fronteres de fusió d'un HDR **no són circumferències**: són isofotes, o
sigui que segueixen la corona i van a radis diferents a cada azimut. Mesurat al
pilot, la isofota de saturació del fotograma llarg va de **1,583 a 2,370 R☉**
—un recorregut de 0,788 R☉— mentre que la vall que hi deixa el colze fa
**0,034 R☉** d'ample: un calaix radial de l'amplada de la vall n'agafa el
**4,3 %** de la frontera.

⛔ **Qualsevol estadístic radial la dilueix per un factor ~23.** Una porta que
mesura el perfil radial dirà que està bé mentre l'ull hi veu l'arc. Per mesurar
una frontera d'aquestes s'ha de **seguir el contorn a l'espai** i treure-hi una
base local per azimut — i encara així, compte: dues finestres diferents em van
donar 0,004 % (0,3 σ) i 0,070 % (5,4 σ) sobre la mateixa dada, i no les vaig
reconciliar.

⏭️ I la cura de fons d'aquestes valls **no és la forma de la rampa**: l'amplitud
del colze és proporcional al **desacord entre esglaons d'exposició**. Una
`smoothstep` només impedeix que aquell desacord es concentri en una línia i el
reparteix per la rampa.

### ✅ I el 24-08-2026 es va trobar el desacord, i era del 1,2 % ALTERNANT

Component **cada esglaó d'exposició per separat** al llenç i comparant els veïns
**píxel a píxel** —milions de píxels, no medianes d'anell—, el desacord surt
així a la Vixen:

| parell | desacord | | parell | desacord |
|---|---:|---|---|---:|
| 1/512 → 1/256 | **+0,519 %** | | 1/64 → 1/32 | **−1,095 %** |
| 1/256 → 1/128 | **−1,105 %** | | 1/32 → 1/16 | **+1,301 %** |
| 1/128 → 1/64 | **+1,275 %** | | 1/16 → 1/8 | **−1,062 %** |

⛔ **El signe ALTERNA**, i això no és soroll: vol dir que els esglaons senars i
els parells són **dues famílies** que no s'ajusten entre elles. La causa surt de
l'ordre de captura: el programa de la R6 fa **dues escales de 2 EV
entrellaçades** per mostrejar 1 EV, i cada escala és **un pas diferent en el
temps** —els senars a t = 6,6-11,6 s i els parells a t = 12,7-16,5 s—. Entremig
l'aire ha canviat.

I es confirma mirant **el mateix esglaó a instants diferents**: 1/128 s val
**1,0598 a t = 8 s i 0,9779 a t = 89 s**, o sigui una caiguda de transparència
del **8 % durant la totalitat** (el cel d'aquell run varia un 85,5 %). No és
electrònica ni temps d'obturació: és atmosfera.

⛔ **La porta F0 no ho podia veure mai**, i no estava trencada: era **cega per
construcció**. Compara medianes d'anell sencer amb dos a quatre fotogrames per
esglaó, i el seu terra de precisió és del **2,5 al 4,3 %** — deu vegades per
damunt del que s'havia de detectar. La lliçó general: **una porta amb un terra
de precisió declarat no vigila res per sota d'aquell terra**, i cal dir-ho al
seu costat, perquè un PASS d'una porta cega es llegeix com un PASS.

**La cura**: un ajust `P_i(r) = c_i·(C(r) + s_i)` — dos escalars per fotograma i
per pla, contra 220 anells de dada. ⛔ **Un escalar global no pot fabricar
estructura**: només puja o baixa el fotograma sencer, i aquesta és la
salvaguarda que el fa legítim (compareu-ho amb `k(φ)` lliure entre trens, que
té un paràmetre per sector i **s'hi imposa l'acord**). El gauge és
`mediana(ln c) = 0`: ⚠️ **l'escala absoluta no es toca**.

⚠️ Dues coses que l'ajust va ensenyar i que valen per a qualsevol repetició:

- **el terra radial són 1,15 R☉ i no es pot abaixar.** La temptació hi és
  —a 1,16 R☉ l'exposició d'1/3251 s només porta 12 ADU i no s'hi ajusta—, però
  **la Lluna es mou 0,065 R☉ durant la totalitat** i el seu limbe arriba a
  1,108: per sota d'1,15 els fotogrames ja no comparen la mateixa escena.
  Mesurat: baixant a 1,09 el residu puja de 0,15-0,17 % a **0,31-0,37 %**;
- **un fotograma que no s'ajusta no es pot quedar a c = 1 en silenci.** La
  transparència és una corba suau en el temps: el que li toca és el valor
  d'aquella corba al seu instant, dit al rebut.

### ⛔ Els anells concèntrics del NRGF: en calen DUES passades, i la segona exacta

Pere va marcar arcs concèntrics amb la Lluna al detall de la fase 3. N'hi havia
**dues famílies alhora**, i confondre-les costa el diagnòstic:

1. les **costures de fusió**, que segueixen isofotes (secció anterior);
2. **anells de veritat circulars**, del 0,13 al 0,41 %, que són **més forts que
   les costures** i que surten del **suavitzat del propi perfil radial**.

La primera passada del NRGF **ha de** suavitzar el perfil, i no és una tria: a
`ln I` la dispersió dins d'un anell la domina la corona —σ ≈ 0,3, o sigui un
30 % azimutal— i l'error típic de la mediana d'un anell de 3.300 px val
**0,65 %**, tres vegades tot el detall que es declara. Restar la mediana crua
hi injectaria un tremolor circular enorme.

⛔ **I el suavitzat és el que deixa els lòbuls.** Un Savitzky-Golay d'ordre 2 amb
finestra F no reprodueix la curvatura dins de F i el residu és un ondulat de
període ~F. La prova que ho tanca: refer la fase 3 amb finestres de **9, 29 i 61
calaixos**. A 1,182 R☉ el lòbul val **+0,179 %, +0,074 % i −0,038 %**; a
1,303 R☉, **−0,250 %, −0,153 % i −0,040 %**. **Es mouen amb la finestra: són del
filtre.** I cap finestra no els mata —el rms circular es queda entre 0,13 i
0,15 % a les tres—, o sigui que **triar-ne una de bona no és la solució**.

**La cura és una segona passada, DESPRÉS de l'ACHF**, i el número diu per què hi
pot ser exacta: després del passa-alt la dispersió dins d'un anell ja no és la
corona sinó **el detall**, σ ≈ 0,0023, i l'error típic de la mediana cau a
**0,005 %**, quaranta vegades per sota de l'artefacte. Amb calaixos de **mig
píxel** —calibrat: ×64 de guany amb un píxel, ×272 amb mig, i a un quart ja no
en guanya— restar la mediana d'anell crua deixa la component circular a zero
**per construcció**.

⛔ Això no és cosmètica sinó cura: tant se val QUÈ hagi deixat la primera passada
—lòbuls, vores de calaix, un centre desplaçat—, perquè tot això és circular i
aquí es cancel·la. I no toca res que no sigui circular: **restar una constant per
anell no pot crear ni destruir estructura azimutal**, i les costures, que són
isofotes, sobreviuen senceres i s'han de curar a la fase 2.

### ⛔ Un «detector d'isofotes» sense CONTROLS no és una porta

El 24-08-2026 vaig declarar-li a Pere que una costura es veia a **60 σ**. Era
fals, i el que ho va desmentir va ser el meu propi control: mesurant amb sectors
azimutals honestos baixava a **3,2 σ**, per permutació a **1,5 σ**, i —el número
que ho tanca— **quatre isofotes que NO són cap frontera van donar de 2,7 a
3,8 σ**, o sigui els mateixos valors. El que es mesurava era el mètode.

La regla que se'n treu: **tota mesura al llarg d'un contorn ha de portar
contorns de control del mateix tipus que no siguin frontera**, i el llindar
**se'l calibren els controls**, no es tria. Amb això, de sis fronteres només
**dues** superen el terra dels controls — i són exactament les dues que Pere
havia marcat a la imatge.

### ⛔ Amb una escala d'1 EV no existeix cap isofota de CONTROL

La secció anterior demana controls. Però al pilot, els nivells de frontera van
de **×1,25 en ×1,25** —cada exposició en dona dos, `SOSTRE/t` i `0,2·SOSTRE/t`,
i les dues famílies s'entrellacen—, o sigui que **no queda cap nivell lliure**:
un «control» triat a mig camí entre dues fronteres cau **dins de la zona de
fusió del veí**. Mesurat el 24-08-2026 a 1,97 R☉: el control per nivell donava
**0,1472 %** i la frontera **0,1471 %**. La porta quedava sense dents.

**El control ha de ser APARELLAT**: el **mateix contorn**, amb la mateixa forma
i la mateixa llargada, **desplaçat radialment** fora de la zona de fusió (110 px
va bé, amb una finestra transversal de ±60). Amb això el terra de control va de
6,36 σ a **2,81 σ** i la porta torna a tenir dents.

### ⛔ Al model `P = c·(C + s)`, `s` NO és el cel: és la DESVIACIÓ

I per tant **pot ser negatiu**, i clavar-lo a zero trenca l'ajust. Amb el gauge
`mitjana(s) = 0`, el cel mitjà viu dins de `C(r)` i `s_i` només diu quant se
n'aparta aquell fotograma. El cel de la totalitat fa una **V amb el mínim al
mig**, o sigui que els fotogrames de mig eclipsi en tenen **menys** que la
mitjana i els toca un `s` negatiu de ple dret.

Mesurat el 24-08-2026, amb el clip a zero posat: els tres fotogrames de
**10,079 s** —tots de t = 33 a 60 s, o sigui just al mínim del cel, i vàlids
només més enllà d'1,97 R☉ on el cel ja mana— es menjaven la desviació dins de
`c` i queien a **0,947-0,994** quan els seus veïns de 2 s tenien 1,03-1,05. El
resultat era una **costura NOVA a 1,97 R☉ de 0,147 % a 11,8 σ** que el producte
sense corregir no tenia. ⛔ **Una correcció que arregla una costura i en crea una
altra s'ha de mesurar a totes dues bandes abans de declarar-la bona.**

### ⛔ Un anell que no és un anell: el criteri ha de ser COBERTURA, no recompte

La mesura de «quant del detall és circular» agafa la mediana azimutal per anell.
El criteri d'inclusió de cada anell ha de ser **quina fracció del cercle té
dada**, no quants píxels té: amb un llindar de 200 píxels, una **escletxa de
256 px amb un 3,9 % de cobertura** a la vora interior del tren Sony feia que la
porta declarés un **14,2 %** d'anells concèntrics quan fora d'aquella escletxa
el residu era de **±0,008 %**. Amb el criteri de cobertura al 50 %, el mateix
producte dona **0,7 %**. Una vora de la dada no és un anell concèntric.

### ⛔ Amb costures MÉS JUNTES que la finestra, mesurar-ne una és mesurar-ne tres

La trampa més cara del 24-08-2026, i la va destapar **una imatge de Pere**, no cap
número meu. Amb quinze exposicions d'1 EV, la corona interior té fins a **trenta
fronteres de fusió** —dues per esglaó, `SOSTRE/t` i `0,2·SOSTRE/t`—, separades
només **×1,25 en nivell**. A 1,2-1,6 R☉ això vol dir que dues fronteres veïnes
estan a **20-60 píxels** l'una de l'altra.

I la mesura per contorn treu una base local ajustada als extrems d'una finestra de
**±60 px**. O sigui que:

- **la base local està contaminada per les costures del costat** i cada costura
  surt subestimada;
- **el control aparellat de ±110 px aterra sobre una altra costura**, i el terra
  de control s'infla: a 1,25-1,51 R☉ donava 0,17-0,34 %, més gros que el senyal
  que s'hi buscava.

⛔ **Amb això, els meus números per contorn deien 0,07-0,12 % i la porta H2 deia
que a 1,25-1,51 no es podia distingir res.** La imatge, amb realçat per anell i
les fronteres dibuixades a sobre, ensenyava un patró de pana ben visible que
seguia els contorns exactament.

**La mesura que sí que val quan les costures són denses és la de l'espai de
NIVELL**: la mediana del detall per calaix de nivell, comparada amb el rms del
detall. Aquella deia **88,6 %**, i és el número honest. Regla general: **quan els
artefactes són més densos que la finestra de la mesura, cal mesurar-los a l'espai
on són escassos**, no a l'espai on són densos.

### ⛔ Per decidir si un patró és corona, correlaciona en 2-D i per BANDA

El 24-08-2026 vaig fer la correlació entre trens **per sector azimutal amb
calaixos radials fins** i em va donar **r = +0,04**: «no és corona». Era fals.
Amb 320 calaixos sobre un sector de 60°, la mediana de cada calaix té poca mostra
i el que domina és el soroll. La **mateixa dada**, correlacionada píxel a píxel en
2-D dins d'una banda radial i portant els dos trens a resolució comuna, dona
**r = +0,93**.

Les tres proves que decideixen, i cadascuna exclou una cosa diferent:

1. **meitats A/B** —fotogrames alternats **dins de cada esglaó**, de manera que
   les dues meitats tenen les mateixes exposicions i, per tant, les mateixes
   fronteres— separen **senyal de soroll**;
2. **els dos trens** separen **corona de sistemàtic d'un instrument**;
3. **moure el SOSTRE** (0,85 → 0,60) separa **corona de fronteres de fusió**,
   perquè les mou totes de radi sense tocar ni la corona ni el filtre.

⚠️ I el límit de la (2): els dos trens comparteixen llenç, warp, màscara lunar i
filtre. Un artefacte d'**aquelles** etapes també correlacionaria.

### ⛔ Un ajust mal condicionat dona una imatge bona amb paràmetres impossibles

Model legítim: si l'esglaó `k` porta un error multiplicatiu `δ_k`, l'error del
compost és `Σ_k f_k(píxel)·δ_k`, amb `f_k` la **fracció de pes mesurada**. Quinze
escalars contra trenta milions de píxels: sembla impossible que absorbeixi res.

⛔ **Però els regressors sumen 1 a cada píxel** —per construcció, són fraccions—
i uns quants esglaons tenen pes gairebé nul a tot el camp. El sistema queda mal
condicionat i l'ajust lliure se'n va per direccions degenerades. Mesurat el
24-08-2026: δ de **+954 %, −3182 % i −1963 %**, amb un model que valia el 28,5 %
del detall i que **hauria deixat la imatge millor**.

⚠️ **El senyal d'alarma no és el residu, són els PARÀMETRES.** Un ajust
degenerat encaixa bé i mestreja valors sense sentit físic. La regla: **tot
paràmetre ajustat ha de tenir un ordre de magnitud esperat, declarat abans, i
s'ha de comprovar.** Aquí el prior no és inventat: la mesura de coherència diu,
independentment, que després de corregir la transparència el desacord entre
esglaons veïns queda en **±0,3 %**. Amb aquest prior l'ajust queda ben plantejat.

I encara així, la decisió **no és de l'ajust**: passa pel jutge extern com
qualsevol altre candidat.

## Trampes del pilot REAGRUPEM (26-08, Vixen sol des de zero)

### ⛔ Una estadística AZIMUTAL sobre un sensor RECTANGULAR fa una vora dura

L'NRGF —i el FNRGF, i qualsevol filtre que normalitzi per anells— fa, a cada
radi *r*: calcula el nivell típic de l'anell **μ(r)**, la seva dispersió
**σ(r)**, i substitueix cada píxel per **(I − μ(r))/σ(r)**. Així cada anell
queda centrat i amb el mateix contrast, i l'estructura de tots els radis es veu
igual de bé. **Tot el mètode descansa en una sola suposició: que μ i σ surten de
l'anell SENCER.**

⛔ **Cap petjada de dada no és un disc centrat al Sol. Tots els sensors són
rectangles**, i al llenç comú hi van a més **girats**. Mesurat el 26-08 amb el
Vixen (rectangle girat 57,195° dins d'un llenç de 8064×8928):

| radi | quant queda de l'anell |
|---|---|
| fins a **5,21 R☉** | sencer, 100 % |
| **7,53 R☉** | la meitat |
| **9 R☉** | **el 9 %** — només els quatre cantons |

I els cantons **no són una mostra justa**: són **azimuts fixos** —les diagonals—
i la corona no és uniforme en azimut. Preguntar «quin és el nivell típic
d'aquest anell?» i respondre mirant sempre els mateixos quatre trossets no dona
el nivell de l'anell: dona el d'aquells trossets. Com que el número es **resta**
i després s'hi **divideix**, l'error va a tots els píxels d'aquell radi; i com
que el canvi de mostra passa **de cop** a un radi concret, μ(r) fa un **salt** i
la imatge en fa un altre: **un disc brillant amb vora dura**, exactament al radi
on el cercle deixa de cabre-hi.

⏭️ **El criteri per saber que és artefacte i no corona**: el radi on surt
depèn de **la geometria del sensor i del llenç**, no del Sol. Gira el llenç i el
salt es mou; canvia'n la mida i es torna a moure. **Una frontera que obeeix el
teu enquadrament i no el cel és teva.**

⛔ **I la cura NO és retallar al cercle més gros que hi càpiga**, que és la
temptació immediata i és **doblement dolenta**: llences dada real —als cantons
hi ha corona mesurada fins a 9-10 R☉— i **no t'estalvies la vora**, perquè te'n
surt una altra, la del retall, que és el halo de sempre. És la norma del
rectangle.

⏭️ **La cura és fer el perfil INCAPAÇ de saltar**, i són tres coses juntes:

1. **calcular-lo en log r**, no en r lineal, perquè els calaixos exteriors no
   siguin enormes i el perfil tingui la mateixa resolució relativa a tot arreu;
2. **pesar cada calaix per la seva COBERTURA azimutal** —cobertura al quadrat—,
   de manera que un anell del qual només en veus el 9 % pesi cent vegades menys
   que un que veus sencer: deixa de manar just quan deixa de ser fiable;
3. **suavitzar el perfil al llarg de log r**, perquè on la cobertura s'ensorra
   el perfil **continuï la tendència** dels radis ben mesurats en lloc de saltar
   al valor dels cantons.

El filtre segueix aplicant-se a tot el rectangle i el que hi fa servir a fora és
una **extrapolació declarada** del que diu la part ben mesurada. No és una
mesura, i es diu al rebut; però no fabrica cap frontera.

⚠️ Qui **no** pateix això: el MGN i el passa-alt, que treballen amb veïnatges
locals i no els importa la forma del camp. Qui sí: tot el que divideixi per una
estadística per anell.

### ⛔ Una corba de to ancorada PER CANAL esborra el color, i no ho diu

Corba declarada de `3-RECERCA/108`: `y_c = 0,68 + 0,17·log10(v_c / va_c)`, amb
`va_c` la mediana del canal a l'anell 1,05-1,15 R☉. Sembla innocent i **és
catastròfica per al color**.

La mediana és positivament homogènia: si `v_c → α_c·v_c`, llavors
`va_c → α_c·va_c` i **el quocient no es mou**. O sigui que **qualsevol constant
per canal és INVISIBLE**: el balanç de blancs, la neutralització, el gauge.
Mesurat el 26-08: `max|y(α·G) − y(G)| = 0,000`. Pitjor: com que `y_c` és
monòtona, la mediana hi és equivariant i **`mediana_anell(y_c) = 0,68 per als
tres canals, sempre**.

⛔ **Resultat: la imatge surt MONOCROMA.** La dada té `I_R/I_G` d'1,84 a 1,69 i
`I_B/I_G` de 0,49 a 0,53 —0,26 dècades de color, i la corona vermella de veritat
per l'extinció cromàtica a X≈6— i la base renderitzada ho ensenya dins de
**±0,002**. El croma que en sobreviu és només la *desviació local* respecte del
color de l'anell, comprimida ×0,17.

⏭️ **La cura**: **una sola àncora comuna** —la del verd— per als tres canals.
`y_c = 0,68 + 0,17·log10(v_c / va_G)`. Llavors el color de la dada arriba a
pantalla, comprimit pel mateix pendent que la lluminància, que és el que la
maqueta demana.

⚠️ **I el senyal d'alarma que no vaig veure**: una imatge de corona que surt
**perfectament neutra** no és una imatge ben balancejada, és una imatge a la
qual algú li ha tret el color. La corona real, a 9° d'altura i massa d'aire 6,
**ha de sortir vermella**.

### ⛔ Un `nan` a l'àncora enverina TOT el llenç, i surt opac

`np.nanmedian([])` dona `nan` amb un `RuntimeWarning` que ningú no mira. I
llavors `np.maximum(x, nan)` **propaga el `nan` a tots els píxels** (numpy 2.x),
`log10` el manté, i el `np.where(np.isfinite(y), y, TERRA)` final el converteix
en **el valor de terra, opac, a tot arreu**.

Mesurat: la capa `LDIC 10s` del PSB lliurat tenia **min = max = mediana =
0,044999** i **un sol valor únic** als tres canals. Una capa morta que no es
distingeix d'una capa fosca legítima.

⏭️ La regla: **comprova que l'àncora existeix abans de fer-la servir**, i si no
hi és, falla amb un missatge, no amb un terra. I les capes amb exposicions
llargues **perden l'anell d'àncora per saturació** (a 10 s hi queden 0 px de
45.204), o sigui que el cas no és rar: és el normal.

### ⛔ Restar un mapa BALANCEJAT a una dada CRUA treu 2,17× massa vermell

L'error d'unitats més car de la nit. Un script nou refà la composició des dels
RAW (sense balanç de blancs) i li resta el **mapa de cel del compost**, que sí
que el porta. Com que el balanç és R ×2,1678 i B ×1,3555, es treu **2,17 vegades
massa cel al vermell i 1,36 al blau**.

Mesurat: **el 88,45 % del R i el 87,57 % del B** queden ≤ 0 (contra el 18 % del
verd), i de 3,5 R☉ enfora, **el 100 %**. La corba de to converteix aquell no-dada
en terra opac per canal, i el resultat és **VERD PUR al 78-85 % de la petjada**.

⏭️ **La norma que se'n deriva** (Pere, 26-08, marcada com a error recurrent): **a
cada resultat, mesura R/G i B/G en una zona coneguda i escriu-los al rebut.** Un
producte que surt verd vol dir que el verd del Bayer —el doble de píxels i el
doble de sensible— no s'ha equilibrat. ⚠️ **I alguns «artefactes» poden ser
això**, no defectes de la dada.

### ⛔ Citar el projecte per dir el contrari del que diu

El 26-08 vaig escriure que la muntura del Vixen «no és suau» i que els 0,549 px
rms de separació d'un quadràtic eren «les correccions manuals de Pere, que el
projecte ja documentava». **Les dues meitats eren falses.**

- **Tren equivocat**: l'única pertorbació de muntura dins de la totalitat és de
  la **Sony + Skywatcher** (`3-RECERCA/72`: en treure el filtre es va moure la
  lent de 300 mm). Les correccions manuals del tren Vixen + iOptron són a les
  **parcials filtrades**, fora de la totalitat (`3-RECERCA/71`: salt de +183 px a
  **C3+90 s**).
- **Finestra equivocada**: la mesura surt de 49 fotogrames entre C2+5,6 s i
  C3−2,3 s, i `3-RECERCA/71` diu literalment que **durant la totalitat ningú no
  toca res**.

⏭️ **La causa real, mesurada, és l'error de l'AJUST DEL LIMBE**, i té quatre
proves: el model quadràtic ja era bo a **0,095 px** (mesurat per correlació de
fase, independent del limbe); el residu és **blanc** —el 74 % canvia de signe
entre veïns a menys d'un segon— i **una correcció manual és un ESGLAÓ**, no
soroll; el residu **escala amb la qualitat de l'ajust** (r = +0,52 amb el rms del
limbe, i 0,404 px amb cobertura sencera contra 0,683 amb cobertura parcial); i el
**glare de la corona es menja el limbe**, de manera que el radi ajustat decreix
1,3 px de 1/1000 s a 1 s i el centre es desplaça fins a **0,44-0,51 px per grup
d'exposició** — que és exactament la beta que `3-RECERCA/71` ja advertia.

⚠️ **Conseqüència de disseny**: registrar amb la posició mesurada de cada
fotograma, en lloc del model, **injecta ~0,4 px de soroll de mesura** on el model
en tenia 0,095. **Amb un limbe, el model suau guanya.**

## Una màscara nova s'ha d'aplicar a TOTS els llocs que comparen (27-08-2026)

**Símptoma.** S'afegeix la màscara lunar per fotograma a la composició, i el
compost surt **49 vegades massa brillant** a partir de 2 R☉, amb guanys de
coherència de fins a **206** i una dispersió del **2488 %** (abans: 0,86–1,14 i
8,3 %).

**Causa.** La màscara es va posar a `compon` i **no** a `coherencia`. Aquesta
ajusta el guany de cada fotograma amb la mediana de `compost / fotograma` sobre
els píxels brillants. Amb la màscara només a una banda, `ref` és la corona de
veritat i `a` és la Lluna fosca d'aquell fotograma: **el quocient es dispara**.

**La regla.** Qualsevol màscara nova que canviï QUINS píxels entren al compost
s'ha d'aplicar **idènticament a tots els llocs que comparen un fotograma amb el
compost** —composició, coherència, registre fi, control de tancament—. La
manera de garantir-ho és **una sola funció compartida** (`f2.mascara_lluna`),
no una còpia a cada lloc.

**I la porta que ho hauria d'haver aturat.** Un guany de coherència fora del
rang `[1/2, 2]` no pot passar en silenci: la transparència va caure un 8 % en
tota la totalitat, o sigui que cap fotograma no en pot demanar el doble. La
porta hi és des del 27-08 i escup els fotogrames culpables.

⚠️ **El rebut ja deia «dispersió 2488 %» i ningú no ho mirava.** Un número al
rebut sense porta és documentació, no control.

## Ajustar un paràmetre amb una dada que no el constreny (27-08-2026)

Un registre entre dues imatges de corona ajustat maximitzant la correlació de
**l'estructura sencera** deixa **l'escala gairebé lliure**: els streamers són
radials, o sigui que estirar el radi no canvia gaire la forma azimutal. L'ajust
lliure donava un ±1,5 % de dispersió i semblava prudent ancorar-lo a la física.
No ho era: l'àncora arrossegava un error del 6 %, i **amb aquell registre el
detall fi de la nostra corona correlacionava 0,38 amb Brno quan de veritat
correlaciona 0,94**. Estava a punt d'escriure que les nostres capes de detall
s'ho inventaven tot.

**La regla**: si el que fas servir per ajustar un paràmetre no el constreny,
ajusta'l amb el que sí. Aquí, jutjant amb la banda d'harmònics m = 13–80
apareixia un òptim net. I valida'l **fora de la mostra** (ajust a 1,2–1,8 R☉,
jutge a 1,8–2,4 R☉).

**El senyal d'alarma**, per si torna a passar: el defecte **es movia de radi
quan movia un paràmetre del mètode**. Un defecte de la dada es queda on és.

## No filtris amb FFT un anell que té forats (27-08-2026)

Omplir el forat de zeros i filtrar per FFT fa **fuita de la vora**. I la fuita
no és neutra: entre dues imatges del mateix equip és **idèntica** (mateix
contingut) i entre les seves i la nostra és **diferent**, o sigui que **inflava
el control i desinflava el nostre alhora**. Sobre un arc parcial, els harmònics
s'han d'ajustar per **mínims quadrats** als azimuts vàlids.

## El disc lunar de l'altre no és corona (27-08-2026)

Els composts de Druckmüller porten un disc lunar **pintat, d'un sol instant i no
centrat al Sol** (mesurat: desplaçat 0,050–0,070 R☉, i **més petit** que la
Lluna de veritat: R_lluna/R☉ d'1,007 a 1,028 contra 1,0338). Correlacionar la
nostra corona contra aquella taca constant donava una **anticorrelació de
−0,29** a 1,05–1,08 R☉ que no era cap mesura. Emmascara'l abans de comparar.

## Un filtre de qualitat ha de mirar el RESIDU, no només els paràmetres (27-08-2026)

La tria de fotogrames per al model del Sol demanava `n_punts ≥ 400` i que el
radi caigués dins del ±3 px de la mediana. **No mirava l'rms de l'ajust del
cercle.** Als fotogrames de 2 s i 8 s de la Sony la corona interior és cremada i
el que l'algorisme troba no és el limbe: en surt un centre **128 px fora**, un
rms de **16 px**… i un radi que **encara cau dins del ±3 px**. Passaven.

I la conseqüència no va ser un error petit: la detecció de salts de muntura
veia aquells 128 px i declarava **cinc apuntaments on n'hi ha un**.

**La regla**: si ajustes un model, filtra pel seu **residu**. Els paràmetres
d'un ajust dolent poden sortir perfectament plausibles. A la Vixen aquest
defecte hi era latent des del primer dia i no hi havia picat mai.

## Una neteja ha de tocar NOMÉS el que ha creat (27-08-2026)

La cadena marcava els runs incomplets escombrant **tot** `1-RUNS` i renombrant
qualsevol carpeta sense `CADENA.json`. Sembla prudent i no ho és: **amb dues
cadenes en paral·lel, la que peta declara fallida la que va bé**. Es va veure
perquè va posar `_AVORTAT_FALLIT` a un run que ja estava marcat a mà.

## Un tren nou és el millor detector de constants escrites a mà (27-08-2026)

Incorporar la Sony va destapar **sis** coses que amb un sol tren funcionaven
perfectament: el llenç anava 1:1 amb el sensor, el radi lunar nominal era una
constant de mòdul (460 px, el de la Vixen), la finestra de cerca dels contactes
s'ancorava al primer fotograma, una porta demanava 20 fotogrames coronals com a
mínim absolut quan volia vigilar la referència temporal, els noms dels
fotogrames de protuberància eren els de la R6 III, i `revela_frame` donava per
fet que el cos té marge fosc (l'A7RIIIA no en té cap).

**Cap era un error de programació**: totes eren suposicions certes per a un tren
i falses per a l'altre. Si algun dia s'hi afegeix un tercer cos, compta que
n'apareixeran més, i que apareixeran **una a una i fallant tancat**, que és
exactament el que ha de passar.

## Un halo és una FORMA: cap mesura de nivell el trobarà (27-08-2026)

Pere va marcar halos al voltant de la Lluna. Dues mesures raonables no hi van
trobar res:

- **el perfil radial mitjà**: derivada segona de 0,0 a 0,7 σ. Cec perquè el que
  hi havia **no era un anell sencer**;
- **la prova aparellada** contra controls al mateix radi: −2,2 σ el màxim. Cega
  perquè compara **medianes**, i un halo no canvia la mediana d'una zona: en
  canvia el PERFIL.

El que ho va resoldre va ser una tercera cosa: mirar **d'on venia la vora**. Era
el radi on una exposició deixa d'estar saturada, o sigui el límit de validesa
de la capa. **Quan una mesura de nivell no troba el que l'ull veu, el que veu
l'ull probablement és una vora, i les vores es busquen al mapa de validesa, no
a l'histograma.**

## Un fitxer que s'obre amb una capa visible ha de dir què és aquella capa (27-08-2026)

El PSB de capes LDIC obria amb la capa d'1/8 s visible. La seva vora interior
—1,19 R☉, el radi on aquella exposició deixa d'estar cremada— renderitzada amb
la corba de to és **exactament un halo al voltant de la Lluna**. Res al fitxer
deia que allò fos el límit de la capa i no un defecte del producte.

Ara el nom de cada capa duu el seu rang: `LDIC 0.125s (1 fot.) · val 1.19-9.00
R☉`. **Un lliurable que no s'explica sol fa perdre el temps a qui el mira, i el
temps que fa perdre és el de trobar artefactes de veritat.**

## Un compost és una MITJANA TEMPORAL: el seu control també ho ha de ser (27-08-2026)

La porta de tancament de color comparava el compost —una suma ponderada de tota
la totalitat— amb **un sol fotograma**. Sembla el control més net possible i no
ho és: **el cel canvia durant la totalitat**. Mesurat a la Sony, el B/G d'un
fotograma a 1,8–3,6 R☉ va de **0,579 (t=16 s) a 0,507 (t=62 s) i torna a 0,535
(t=88 s)**: un 12 % en 100 s.

Amb un apuntament (46 s de recorregut) la porta donava 2,4 % i passava; amb els
dos (104 s), 7,3 % i queia. **El mateix compost** contra un control de t=18 s
dona 7,3 % i contra un de t=28 s, 1,4 %.

**La regla**: quan el producte és una mitjana sobre el temps, el control ha
d'abastar el mateix temps. Ara la porta jutja la **mediana sobre controls
repartits** i **declara la dispersió** — que si és gran, és informació: vol dir
que el cel va canviar.

⚠️ I la cautela: **això fa passar un run que queia**. El que ho justifica no és
que passi, sinó (a) que la mesura del cel es va fer independentment de la porta
i (b) que al tren que ja passava el número gairebé no es mou (3,8 → 3,48).
Sense (b), canviar una porta que et falla és moure la porteria.

## Un salt de muntura és un DITHER, i mesura el flat sense flats (27-08-2026)

L'A7RIIIA no té flats invertits: la porta que valida el flat radial de la Vixen
allà no existeix. Però la Skywatcher va saltar **737 px** a mig de la totalitat,
o sigui que **el mateix punt del cel cau a dues posicions molt separades del
sensor**. Amb parelles de fotogrames de la mateixa exposició, un de cada
apuntament, `ln q = const + lnF(rA) − lnF(rB)` s'inverteix per mínims quadrats i
en surt el flat.

Resultat: el flat radial que fem servir té un **error del 7 al 9 % pel camp**,
amb un desacord entre meitats del 0,04-0,54 % (un 1 % del senyal). **Un
contratemps de captura pot ser la millor calibració que tens.**

## Jutja cada capa ON VIU (27-08-2026)

La porta del color mesurava R/G i B/G als anells 1,1 · 2 · 3 · 5 R☉ —coronals— i
els aplicava **també a les capes de contacte** (perles, anell de diamant), fetes
amb 1/6400, 1/800 i 1/100 s. Allà una capa de contacte **no hi té senyal**: el
R/G li queia a **0,048 a 5 R☉** i el veredicte deia «⛔ VERD». Als radis on la
capa sí que viu (1,00–1,10 R☉) el color era **1,81 / 0,45**, exactament el que
mesurem a tot arreu.

Va tombar un run sencer amb una capa perfectament bona. I no havia picat mai
perquè aquella capa només existeix quan entren els fotogrames de contacte de C2.

**La regla**: una porta hereta els seus radis, llindars i anells d'on va néixer.
En arribar un producte nou, comprova que aquells radis són on el producte nou té
senyal — i si no, la porta no està mesurant el producte, està mesurant el fons.

⏭️ **I el detall que ho fa perillós**: la guarda que aquella mesura tenia era
`s.sum() < 200`, o sigui un recompte de píxels. **Protegeix d'un anell BUIT,
no d'un anell SOROLLOS.** A la Vixen els anells exteriors de la capa de contacte
no arribaven als 200 píxels i es descartaven sols —per casualitat, la porta
quedava bé—; a la Sony, amb fotogrames de contacte de 1/100 s i un camp més
gran, sí que hi arribaven, i el que hi mesurava era soroll. **Un llindar de
quantitat no substitueix mai un llindar de qualitat.**


## Una coincidència de MAGNITUD tampoc no és una causa (27-08-2026)

`trampes.md` ja tenia «una coincidència de **posició** no és una causa: mou el
paràmetre». Cal el bessó, perquè em va picar amb números en lloc de radis.

El `3-RECERCA/115` §13 va veure que el sistemàtic de la porta de brillantor era
**bimodal per apuntament** —7,7-9,7 % a l'A i 2,0-2,9 % al B— i que l'error de
flat mesurat pel dither valia **7-9 %**. Els dos números coincidien, i el `115`
en va deduir que el compost de dos apuntaments «carrega l'error de flat».

**Fals.** Amb el flat corregit i el run refet, el sistemàtic **no es mou**
(mediana 5,27 → 6,48 %, dispersió 7,70 → 7,53 %). El que la porta mesura és
una **dependència amb la brillantor del píxel** dins de cada anell (+8,7 % al
percentil 10, −9,5 % al 90), que és la signatura d'una **diferència de nivell
additiva** entre el compost i el fotograma de control: **el cel canviant en el
temps**. Els controls de l'apuntament A són de t = 16-28 s i els del B de
t = 80-88 s, i el compost és una mitjana temporal.

**La regla**: dos números que s'assemblen no són una causa. La prova és moure
el paràmetre i mirar si el símptoma el segueix.

## Un tall per BAIX tria per COLOR (27-08-2026)

Per mesurar el color de la corona fotograma a fotograma vaig posar el tall de
sempre: píxels per damunt del fosc més 60 DN i per sota de la saturació. **El
tall per baix és un tall en DN i el canal B és el més feble**, o sigui que a les
exposicions curtes hi sobreviuen preferentment els píxels amb més blau i el B/G
puja sol. Sortia una dispersió del **127 %** dins d'un mateix tren, que no és una
mesura sinó la selecció.

I la cura òbvia —agafar la **intersecció** dels píxels vàlids de tots els
fotogrames— **hereta el tall del fotograma més curt** i torna a triar els blaus
(B/G 1,05, més blau que el cel).

**La cura de debò: cap tall per baix.** Màscara només de geometria i
no-saturació, i **mitjana**, no mediana: una mitjana sobre 300.000 píxels de
soroll simètric és insesgada encara que cada píxel sigui soroll. Una mediana amb
un tall per baix no ho pot ser mai.

## Una màscara «dels mateixos píxels» ha de ser del mateix CEL (27-08-2026)

Germana de l'anterior i pitjor, perquè sembla el mètode rigorós. Vaig fer la
intersecció dels píxels vàlids **en coordenades de SENSOR**. Amb el salt de
muntura de 749 px, el mateix píxel del sensor **mira un tros de corona diferent
a cada apuntament**: sortia un factor **1,6** de brillantor i **B/G 0,69 contra
0,43** entre els dos grups, i no era de la càmera, era de la corona.

**La regla**: «els mateixos píxels» vol dir el mateix **cel**. Ancora sempre
l'anell al Sol de cada fotograma i comprova que tots els fotogrames que compares
en cobreixen la mateixa fracció.

## Una FFT per sectors mesura la vora de la falca (27-08-2026)

Per saber si una família d'estriat **gira amb l'azimut** (corona) o està clavada
al llenç (graella), vaig partir l'anell en sectors de 45° i fer-hi una FFT.

**No serveix.** La vora de la falca és una discontinuïtat dura dins de la caixa
i la seva fuita domina l'espectre: els «pics» sortien tots a **45,5° i 134,5°**
—les diagonals de la caixa— amb excessos de **×245**, que no són de la dada. La
finestra de Hann de `espectre()` apoditza la caixa, no la màscara de dins.

**La cura**: per a una pregunta d'orientació local, no facis FFT global. Filtra
la banda (diferència de gaussianes) i fes servir el **tensor d'estructura**, que
és local i no té vores.

## Un lliurable escrit no està verificat fins que un ALTRE lector l'obre (27-08-2026)

`CapesTotalsV14.psd` es va escriure, `psd-tools` el va rellegir amb les seves
dotze capes i les seves màscares, les cinc portes de contingut van passar… i
Photoshop el va refusar: **«no és compatible amb aquesta versió»**.

La causa, aïllada amb una matriu de **2 formats × 4 compressions**:

| compressió de la secció `Image Data` | PSD | PSB |
|---|---|---|
| `RAW` | obre | obre |
| `RLE` | obre | obre |
| **`ZIP`** | **NO** | **NO** |
| **`ZIP_WITH_PREDICTION`** | **NO** | **NO** |

O sigui que **no era el format** (la sospita fàcil, perquè aquell fitxer era el
primer PSD d'un projecte que sempre havia escrit PSB): és que la **imatge
fusionada** no admet ZIP. Les **capes** sí que hi van, i per això tot semblava
bé. `f4.set_merged` ja feia servir `RAW` per defecte i per això cap lliurable
anterior no ho havia destapat; el defecte va entrar en «optimitzar» la mida.

⏭️ **La regla, i no és de PSD:** *el lector que et diu que un fitxer està bé no
pot ser el mateix que l'ha escrit.* `psd-tools` llegia feliçment el que
`psd-tools` havia escrit. El que ho va destapar en cinc segons va ser **`sips`**
—ImageIO de macOS, zero línies de codi compartides—, que llegeix la **imatge
fusionada**: `sips -g pixelWidth fitxer.psd`. Si en torna `<nil>`, Photoshop
tampoc no l'obrirà.

⛔ **Tota eina que escrigui un PSD/PSB ha d'acabar comprovant-ho**, amb els dos
lectors, i fallar allà mateix. A `capes_totals_v14/fes_v14.py` és
`comprova_obrible()`. És la mateixa lliçó de sempre en un altre lloc: **un
número al rebut sense porta és documentació, no control** — i aquí el número era
«el fitxer s'ha desat».

## Una correcció per CALAIXOS s'aplica INTERPOLADA (27-08-2026)

Pere va marcar unes ratlles diagonals regulars al passa-alt. No eren diagonals:
eren **anells**, i només ho semblaven perquè a 4,5 R☉ al nord-est l'anell hi
passa a 45°.

`perfil_azimutal` calculava el perfil radial per calaixos —cosa correcta— i el
tornava **`mu[idx]`**, o sigui **indexat pel calaix**. Restar això és restar una
**escala de 900 graons en radi**, i cada graó és una vora dura. El passa-alt i
l'MGN, que conserven les vores, la conservaven sencera: potència a la freqüència
dels calaixos **×937 i ×4021**.

⚠️ **El perfil ja se suavitzava** (nucli de 14 calaixos) i no servia de res:
suavitzar el perfil no treu els graons de **com s'aplica**.

⏭️ **La cura**: interpolació lineal entre centres de calaix. Exacta al centre,
contínua a tot arreu, i no canvia què corregeix la funció. 937 → 1,97.

**La regla**: si has calculat una correcció per calaixos, aplica-la interpolada.
Indexar pel calaix imprimeix la graella al producte. I si la graella és
logarítmica, el període creix amb el radi — que és com es va identificar quina
de les dues funcions era (la raó mesurada/predita valia **1,33 = 1200/900**).

⛔ **I la porta que no ho veia**: H1 mesura el NIVELL de cada anell, i una
escala de graons petits el compleix perfectament. **Un anell és una FORMA i la
porta mirava un NIVELL.** La cura és una porta nova (H1b, potència a la
freqüència dels calaixos), no afluixar la vella.

## L'acord entre els dos trens NO distingeix corona d'atmosfera local (28-08-2026)

Pere va marcar dues línies rectes al passa-alt. Vaig passar el circuit sencer:
neixen a la fase 2, pes pla, **a tots els fotogrames**, contrast constant, **la
Sony les veu al mateix lloc del cel** — i vaig declarar totes dues «corona
real». Pere: «si fossin reals, les imatges de Druckmüller les contemplarien
també». **Brno en tenia una i l'altra no**: la de r 3,70 R☉ hi surt a −19/−38 %
(t 30-41) als quatre composts; la de r 2,52, que si fos corona hi hauria de
sortir a −9/−18 % (amplificació calibrada ×17-35), surt a −0,3/−1,7. És una
franja d'extinció del NOSTRE cel (contrail/cirrus alineat amb el flux, que
avança al llarg de si mateix i sembla estàtic).

**La regla**: els dos trens comparteixen el CEL, o sigui que el seu acord només
demostra que una cosa és **a la llum que arriba al lloc** — no que sigui corona.
Per separar corona d'atmosfera local cal un observador d'UN ALTRE LLOC. El
confusor ja era conegut dels jutges de detall (3-RECERCA/103/106); aquí és la
primera vegada que hauria colat un veredicte fals de «corona real».

⚠️ I el test de color que semblava tancar-ho (dèficit amb color de corona) tenia
la metrologia marcada com a inconsistent — un test amb la metrologia en dubte
no pot ser la peça que decideix. Brno mana.

⏭️ **L'instrument que ho mecanitza**:
`3-RECERCA/tools/auditoria_estructura/es_corona.py` — dona-li el segment
(`--seg H y x0 x1`) i jutja les TRES columnes alhora: els dos trens, la
significància contra un nul honest (el mateix segment girat a 36 azimuts del
mateix radi, a la mateixa imatge: autocalibrat, sense factors d'amplificació) i
**els quatre composts de Brno pel registre del `3-RECERCA/114`**. Veredictes:
CORONA REAL / NO ÉS CORONA / INDECÍS. Té autotest (`--prova`: una línia
sintètica compartida pels dos trens ha de sortir NO ÉS CORONA) i reprodueix
els dos casos del 28-08. ⛔ **Cap declaració «és corona real» sense el seu
veredicte** — o sense l'equivalent fet a mà amb un compost d'un altre lloc.

## `topil()` menteix sobre la profunditat de les màscares (28-08-2026)

Als documents PSD/PSB de 16 bits, Photoshop desa **les màscares a 16 bits** —
psb_utils ho advertia per ESCRIURE (`create_mask` a 8 bits parteix les files)—
però la trampa simètrica és en LLEGIR: **`layer.mask.topil()` de psd-tools
retorna la màscara convertida a 8 bits** sense dir-ho. Re-codificar el canal
des d'aquella lectura el deixa amb **exactament la meitat dels bytes**
(40,9 MB per 81,9 a la V14): `sips` no ho veu (només llegeix la fusionada),
psd-tools tampoc fins que DESCODIFICA la màscara, i Photoshop es trobaria el
canal corromput.

**La regla, que estén la del 27-08**: el lector que et diu que un fitxer està
bé no pot ser el mateix que l'ha escrit, i **no n'hi ha prou amb l'estructura
i la fusionada: cada canal EDITAT s'ha de tornar a descodificar** abans de
desar. La lectura bona és el canal cru amb la profunditat del document:
`decompress(cd.data, cd.compression, w, h, depth_del_document, versió)`.

## El «no compatible» de PSB: les signatures 8BIM/8B64 dels blocs globals (28-08-2026)

La V15 passava psd-tools, `sips` (ImageIO), `exiftool -validate` i ImageMagick
`identify` — i Photoshop la refusava. Bisecció amb el Photoshop de debò
(ExtendScript sense diàlegs): el verí eren els **blocs globals heretats** d'un
document que Photoshop havia escrit i psd-tools re-serialitzava com a PSB.

**El mecanisme, mesurat als PSB del mateix Photoshop (V3b/V4b)**: a PSB,
Photoshop escriu `cinf` i `FMsk` amb signatura **`8B64`** (longitud de 8
bytes) i `CAI `/`OCIO`/`GenI`/`Pat2` amb `8BIM` + 4 bytes; psd-tools ho
re-serialitza tot amb `8BIM`, i als que posa 8 bytes (`cinf`, `FMsk`)
Photoshop hi llegeix 4 → es desalinea al primer bloc i refusa el fitxer
sencer. A PSD v1 totes les longituds són de 4 bytes: per això el mateix
document com a PSD s'obria.

**Les regles**:
1. en re-serialitzar amb psd-tools un document LLEGIT com a **PSB**, fora tots
   els blocs globals menys `Lr16`/`Mt16` (metadades de sessió que Photoshop
   regenera);
2. ⛔ **cap lector independent no substitueix el de debò**: la porta final de
   tot PSD/PSB és obrir-lo amb Photoshop per ExtendScript
   (`3-RECERCA/tools/capes_totals_v14/porta_photoshop.sh`, `DialogModes.NO`,
   tanca sense desar). psd-tools és l'escriptor, `sips` només llegeix la
   fusionada, i ImageMagick tolera el que Photoshop no tolera.

## La porta de Photoshop que «refusa» i és el rellotge (29-08-2026)

`porta_photoshop.sh` no portava clàusula de temps, i l'AppleEvent per defecte
caduca als **120 s**. Un PSB de 3+ GB triga més a obrir-se: la porta tornava
`error … -1712 (Tiempo límite superado)`, que **sembla un rebuig i no ho és**.
Cura: `with timeout of 3600 seconds` al voltant del `do javascript`. ⛔ Un
error de transport de la porta no és mai un veredicte de la porta: si no diu
literalment `OBRE` o `REFUSA`, la porta **no s'ha executat**.

## Una llista triada per llindar sense control nul (29-08-2026)

Fotometria forçada a 1.084 posicions de catàleg, llindar 3,5σ: 87 «estrelles».
El **control nul aparellat** —les mateixes posicions **girades al voltant del
Sol** (mateix radi, mateix anell de soroll, mateixa mesura)— diu que la falsa
alarma real és del **2,8 % per posició**, no del 0,02 % d'una gaussiana: el
gra del drizzle és correlacionat i es pren el màxim de 49 px. De les 18 fonts
de V 10-11,5, **15 eren gra**. ⛔ El catàleg dona la IDENTITAT, no la
DETECCIÓ: cada posició predita és una prova independent. Comprovació barata
que ho delata sense muntar el control: **el flux mesurat ha de seguir la
magnitud** (aquí r = +0,18 → després de purgar, +0,71); si el flux queda
clavat al terra a totes les magnituds febles, la llista és el llindar.

⛔ I corol·lari: **cap correcció fina no es calibra contra una llista que
encara no s'ha netejat**. La d'aquesta ronda sortia d'aparellar contra el gra
i estava 2,7 px fora de la bona.

## El limbe fotogràfic amb llum asimètrica menteix uns px (01-09-2026)

L'ajust de cercle pel màxim de gradient sobre un disc amb il·luminació
asimètrica (p.ex. just després de C2: glow enlluernador a l'W, fosc a l'E)
dona un centre esbiaixat cap a la llum: mesurat al DSC06984, **3,6 px** de
diferència entre el fit del costat brillant i el del fosc. ⛔ Cap ancoratge
fi sobre un fit de limbe complet en aquestes condicions: fes servir el costat
fosc sol, o —millor— un contacte real (les perles de Baily són geometria,
no fotometria). Els 4 px que Pere va haver de corregir a mà a la V24 eren
exactament aquest biaix.

## Les tessel·les de ciència no serveixen per al limbe de display (01-09-2026)

Les tessel·les lunars científiques exclouen el trànsit disc→corona **per
construcció**: la guarda (8 px dins del limbe) i el sostre de validesa LDIC
(el glow del 8 s satura fins ~20 px DINS del disc). Qualsevol capa de display
feta només amb elles acaba amb el perímetre pintat (pedestal, anell additiu),
i un fotograma sol «guanya l'agregat» — no per SNR: perquè l'agregat no porta
la dada del trànsit. ⛔ Per al limbe de display: compon el fotograma SENCER
(variant declarada, pes = només zona activa) i deixa que el flood i el
contorn irregular siguin els del fotograma. I tres sub-trampes del mapatge:
**u per canal tenyeix** (el G satura abans → fracció única de luminància, el
croma el posa la llum de destí); **el nivell d'empalme es llegeix AL radi
d'empalme** (la mediana més enfora sobrevalora, la llum puja); i **el terme
de glow vol porta radial** (les terres altes de l'earthshine també donen
u~0,3).

## Les vores de guarda desplaçades es filtren pel BASELINE (02-09-2026)

Un apilat registrat a la Lluna porta la vora de guarda de CADA fotograma a
un radi lleugerament diferent (centres ±2 px): a la zona on cauen, la
barreja val zero PER TRAMS. Si aquest apilat fa de línia de base d'una
resta (flood = fotograma − ajust(apilat)), els clots per trams reapareixen
al producte com a arcs foscos DISCONTINUS (guionets) — i costen de trobar
perquè la fuita no és al contingut sinó al baseline. ⛔ Tota línia de base
feta d'un apilat amb guarda s'estén llisa des de DINS de la zona vàlida
abans de restar. I dues germanes de la mateixa ronda: **el traspàs entre
continguts es fa on el receptor S'HI QUEDA al nivell** (mínim rodant), mai
on un pic el creua (un llavi brillant amb solc darrere enganya el criteri);
i **el fre de derivada azimutal d'un radi de traspàs alça les valls, mai
escapça els pics** (escapçar torna a posar el traspàs abans del solc).

## Cinc trampes de la V25 (02-09-2026, 3-RECERCA/130 §3)

1. **Dos `comu.py` al `sys.path`** (pilot i cadena): el primer guanya i `comu.Run`
   no existeix. Carrega cada família amb la seva ruta al davant i treu el mòdul
   de `sys.modules` abans de carregar l'altre.
2. **0 × NaN = NaN a una suma ponderada**: fora de la cobertura de cada tren els
   FITS porten NaN i el pes zero no els salva. `nan_to_num` ABANS de fusionar.
3. **La fusionada d'un PSB de 16 bits amb bloc `Mt16` té QUATRE canals**: amb
   tres, Photoshop diu «no se puede abrir… las opciones de apertura no son
   correctas». Copia el quart pla del fitxer d'origen.
4. **Llegeix l'ordre i les màscares de les capes de Pere abans de reordenar**: a
   la V24 les perles i el limbe són les de MÉS AVALL amb màscares quasi opaques
   (posar-les a dalt pinta un rectangle negre), i la capa EARTHSHINE V24e porta
   una banda exterior fins a ~1,08 R☉ amb el compost V23 a nivell 0,51 («banda =
   max(meu, seu)») que sobre una base més clara és una FRANJA FOSCA.
5. **El forat lunar de la cadena no és el disc de C2 de Pere** (vora de la base
   a 1,010-1,050 R☉ segons l'azimut): cap capa hi té dada. I registrar contra un
   anell prim que contingui el limbe s'enganxa a la vora del disc (89,94° contra
   −91,97° reals): registra contra la corona sencera i comprova per finestres.

## Vuit trampes de la V26 i dels artefactes (04-09-2026, 3-RECERCA/131)

1. **Un blob «rodó» pot ser un anell que abraça el Sol**: la component d'un DoG
   llindarejat que envolta el disc té el centroide AL SOL i una caixa de
   5.000 px; sense sostre de mida ni criteri d'ompliment (àrea/caixa) el
   detector de ghosts la va prendre per un ghost i el pedaç (radi 3.051 px) va
   aplanar la corona sencera. Tot pedaç porta sostre de radi (`radi_max=400`)
   i tot blob exigeix compacitat (costat ≤ 700 px, ompliment ≥ 0,45).
2. **L'orientació d'un pic espectral NO és l'orientació de les ratlles** (són
   a 90°). El primer tall direccional de la V26 es va fer a l'angle de les
   ratlles i va caure a 90° del pic: 240 → 254, no va treure res, i cap porta
   interna ho hauria dit si no s'hagués MESURAT el pic abans i després. La
   funció rep el número que torna `ratllat` i el rebut porta abans/després.
3. **Una extensió sintètica del cel (per raig, constant) deixa VORES RECTES**
   allà on s'acaba la cobertura d'un tren: Pere les va marcar en vermell i
   verd a la V25. Fora de cobertura hi va DADA (l'altre tren, o la capa de
   Pere) igualada en baixa freqüència i amb ploma ≥ 100 px, mai un invent.
4. **Els ghosts de la lent no es veuen a la base i sí a les capes de detall**
   (a la base són < 4σ del gra; el passa-alt els fa sortir): el detector G
   s'executa sobre la capa de detall i la correcció va a la base I al detall.
   I `cv2.HoughLinesP` torna (N,1,4) o (N,4) segons la versió: `reshape(-1,4)`.
5. **La ploma d'un camp exterior es mesura a la vora EXTERIOR**: la distància a
   «fora de cobertura» compta també el forat lunar; sense `binary_fill_holes`
   la base es barreja amb la capa exterior (zero dins de 2,6 R☉) fins a 120 px
   del limbe → franja fosca 1,0-1,27 R☉ que H1, fidelitat i OBRE no veuen.
6. **Un streamer recte ÉS una recta radial**: l'atenuador de costures (Hough)
   va caçar un streamer de 900 px a 57 px del centre. Tota recta detectada
   porta la distància al Sol; una costura de fotograma és a ~4,7 R☉ (2.100 px)
   del centre i una estructura real hi passa a < 1,5 R☉.
7. **La normalització per anell (MAD) amplifica els anells de sistemàtics**: de
   5 R☉ enfora la corona sola és el residu del model de cel (CEL/C ×10) i el
   MAD hi és petit → el detall gran saturava un arc fosc a 5,3 R☉ (el residu
   del segon apuntament, 40 comptes). El MAD no baixa del valor a 3,5 R☉ i la
   banda de 128-256 px s'esvaeix 4→5 R☉. I l'escala global (p99 de tot el
   llenç) tampoc: la manava el soroll de 6-8 R☉ i deixava els streamers de
   3,5-4,5 R☉ a 0,04 d'amplitud.
8. **El cel aplana la corona a la base**: CEL/CORONA = 1 a 2,5 R☉, 5 a 4, 10 a
   5, 21 a 6 (luminància). Amb el cel dins, una corba de 0,22/dècada deixa la
   modulació real (13-27 % fins a 5 R☉) a ±0,005: els streamers NO es veuen i
   cap detall de 2-32 px els pot tornar (fan centenars de px). La cura és el
   detall gran sobre la corona SOLA i, si es vol, la base corona + k·cel.

## La geometria de la V25/V26 estava girada 138,5° i cap porta meva no ho veia (05-09-2026, 3-RECERCA/132)

Pere ho va dir dues vegades («les capes linealitzades estan girades») i les
meves portes deien 0,0 px: **48 finestres de correlació de fase** (band-pass
4-40 px, residu 1,5 px), **un escaquer de 128 px** i **el forat lunar** que
queia a 4 px del seu disc. Tot era ROTACIÓ-INVARIANT: el gradient radial
domina la fase de qualsevol finestra (mesurat: 0,1 px «de residu» amb la
imatge girada 93°), els raigs són radials a qualsevol angle i continuen
tessel·la a tessel·la, els anells HDR i el forat són concèntrics. La prova
que ho destapa és la **correlació circular en AZIMUT** del perfil polar en ln
(mitjana per anell restada) entre la base i les capes de Pere: pic a −138,5°.
⛔ Regles: (1) tota geometria entre llenços porta la prova azimutal (pic a
0 ± 0,5°) i el **control nul** (referència girada 180°: la porta ha de fallar);
(2) les finestres de fase només valen sobre imatges SENSE perfil radial
(mediana per anell restada) i amb el control nul; (3) el retard radial en
polar es deixa enganyar pels anells comuns (graons HDR): l'escala es declara
(1,0: mateixa escala de píxel) i el centre es contrasta amb el forat lunar;
(4) mira les vistes també en POLAR (r × azimut): un gir hi és un desplaçament
horitzontal, evident a l'ull.

## La corona sola de la descomposició de color MENTEIX de 4 R☉ enfora (05-09-2026, 3-RECERCA/133)

Mesurat contra les fotos finals de Brno (correlació de l'estructura azimutal
anell a anell, mètode del 114): la CORONA SOLA (CORONA_c de la fase 2) va de
0,9 amb Brno a 3 R☉ a **−0,8 a 8 R☉** —anticorrelada—, mentre que el TOTAL
(corona + cel) hi va a **0,75-0,80 fins a 8,6 R☉**, com Brno amb si mateix. El
model de cel per color s'empassa l'estructura azimutal de la corona (que és
neutra, com el cel no ho és) i la deixa en negatiu al residu. ⛔ De 4 R☉
enfora cap filtre no pot menjar de CORONA_c: el detall es treu del TOTAL (la
mediana per anell i el passa-alt azimutal ja treuen el cel llis). I a
l'inrevés: de 3 R☉ endins la corona sola és més neta que el total.

## Els anells de gramòfon venien del FLAT, i quatre trampes de la V32 (07-09-2026, 3-RECERCA/146)

**La trampa mare: un artefacte idèntic a TOTES les fotos d'un apuntament és invisible
a tota comparació entre fotos.** El flat radial de la Sony (`FLAT_RADIAL`, self-calibration
del salt de muntura, F0.3) porta una ondulació fina del 0,09 % rms a 8–30 px que és soroll
del seu ajust, no estructura del sensor. Com que divideix TOTES les fotos, s'imprimeix
invertida a cadascuna (correlació −0,80 amb l'ondulació del flat, pendent −1,00: la
prova és en coordenades del SENSOR, no del Sol), centrada al centre del sensor, que a
l'apuntament B és a 0,5 R☉ del Sol. Resultat: arcs quasi concèntrics amb el Sol a
3,2–4,6 R☉, a un sol fotograma de 8 s, a totes les fotos per igual (2 s i 8 s), sense cap
frontera HDR a sota, deu vegades per sota del soroll de píxel i per això invisibles a
cada foto però coherents al llarg de l'anell: tot filtre que treu soroll els fa aparèixer.
Cap comparació entre fotos del mateix apuntament el pot veure (es cancel·la), cap porta
del flat el veia (llindars al 2–8 %), i el jutge amb la Vixen mirava bandes de 32–64 px.
Ho veuen: l'altre tren sol (anisotropia tangencial per anell, `a4`: Sony +0,06, Vixen 0,00
a σ4) i la correlació foto↔flat al sensor (`a6`). Cura: perfil radial del flat suavitzat
(σ 32 px del sensor) → l'ondulació anular del 8 s baixa del 0,115 % al 0,075 % (= soroll).
Regla: **un flat estimat de les dades porta el seu soroll com a anells; suavitza'n el
perfil radial per sota del soroll coherent i comprova la correlació fotograma↔flat.**

**Les fronteres HDR necessiten camps, no constants.** Els offsets constants del c03 no
cobreixen un desnivell que varia pel camp (transparència, cel, registre d'1–3 px dels
fotogrames llargs). Camp de nivell suau (σ 128 px) per fotograma i canal contra el
compost del grup, gauge suau (σ 512 px): el residu creuat entre trens a les marques
interiors baixa del 0,36 % al 0,21 %.

Quatre trampes de codi de la mateixa nit:

1. **Gauge amb doble ponderació.** `norm_smooth(Σ eps·pw, Σ pw)` multiplica el valor
   ja ponderat pel pes una altra vegada: el nivell global del compost Vixen queia un 2 %
   i tots els φ sortien positius. La mitjana ponderada es fa PRIMER i es suavitza DESPRÉS.
2. **Un fotograma sense suport dona NaN i mata tot el compost.** Un llindar relatiu al
   màxim dels pesos (no al màxim del suavitzat) deixava frames curts sense cap cel·la
   vàlida → eps NaN → φ NaN → T NaN a la iteració següent → total Vixen sencer NaN.
   Guarda: cap camp sense suport entra al gauge ni corregeix; `assert isfinite(phi)`.
3. **Una ploma a la vora d'un suport s'ha d'esvair TAMBÉ a la vora de l'altre.** La
   ploma de 160 px perquè la Vixen agafés el relleu a la vora del suport Sony feia una
   costura en V allà on el suport Vixen s'acabava dins de la zona de ploma:
   `edge = (1−smooth(d_sony))·smooth(d_vixen)`.
4. **`from common import *` sobreescriu `HERE`.** Tot mòdul que defineix `HERE` abans
   d'importar el `common` d'una altra carpeta perd la seva ruta (B6 buscava els u16 a
   `v29/cau`). Redefineix `HERE` després de l'import, o no facis `import *`.

- **Photoshop (28-09-2026): `app.open()` d'un fitxer que Pere ja té obert NO l'obre de nou.** Retorna el SEU document (amb les seves capes enceses, p. ex. el mapa 203), i el `close(DONOTSAVECHANGES)` final el tanca i en perd els canvis. Totes les JSX han de comprovar `jaObert(SRC)` abans d'obrir.
- **D4 amb posicions enteres de la llista (28-09-2026):** a les estrelles brillants, el centre queda a 3–4 px de la llum i el model restat deixa un dipol que els filtres amplifiquen. Cal centrar a la llum de cada font (`b3d4_v114.py --recentra`).
