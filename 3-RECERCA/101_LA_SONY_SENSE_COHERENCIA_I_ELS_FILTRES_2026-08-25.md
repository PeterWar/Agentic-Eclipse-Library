# 101 · La Sony componia sense coherència, el flat queda descartat, i els filtres

**25 d'agost de 2026, matinada.** Sessió desatesa amb autoritat de Pere per
resoldre els últims artefactes i arribar al projecte de Photoshop.

Aquest document mana sobre `research/100` en tot el que toqui la fase 3 de la
Sony, l'atribució de la dependència amb el nivell i el sostre de fusió.

---

## §1 ⛔ El defecte gros: la fase 3 de la Sony no ha fet servir MAI el compost coherent

`_dir_sony()` triava el compost de la Sony a partir de l'etiqueta de la Vixen,
i **només mirava la variant de cel**:

```python
for cand in ("_cel-model", "_cel-color"):
    if cand in etiqueta: sufix = cand
```

`filtres_sony --coh` construïa el sufix `_coh`, aquí es descartava, i el
producte que sortia etiquetat `filtres_sony_coh` es calculava **del compost
sense coherència**. Els dos rebuts de fase 3 de la Sony ho deien a la cara i
ningú no ho havia llegit:

```
fase3_sony.json        etiqueta = 'sony_llenc_comu'
fase3_sony_coh.json    etiqueta = 'sony_llenc_comu'     ← hauria de dir _coh
```

⛔ **I el mateix defecte era a un segon lloc**: `fase_dos_trens_filtrats`
construïa el sufix pel seu compte amb el mateix bucle, o sigui que **la fusió
dels dos trens aparellava una Vixen coherent amb una Sony que no ho era**, en
silenci.

Tots dos arreglats amb una funció pura compartida, `sufix_sony()`, amb sis
proves pròpies.

### Què canvia, mesurat

| fase 3 de la Sony | compost SENSE coherència | compost AMB coherència |
|---|---:|---:|
| costures per nivell, **abans** de les passades | **92,59 %** | **7,98 %** |
| costures per nivell, **després** | 5,42 % | **2,86 %** |
| anells circulars, després (H1) | 0,462 % | 0,467 % |

⏭️ **La coherència de transparència se n'emporta el 91 % de les costures de la
Sony al compost**, abans que cap filtre les toqui. És el mateix ordre de
magnitud que ja feia a la Vixen, i explica per què aquell tren semblava més
brut: no és que fos més brut, és que **no havia rebut la cura**.

⚠️ **Conseqüència sobre el jutge creuat**: totes les decisions del 24 i del 25
es van prendre comparant contra una Sony no coherent. **No invaliden res** —la
referència era fixa i el que es comparava era el candidat—, però la referència
era pitjor del que podia ser.

---

## §2 L'arc verd de Pere, mesurat fins al final

Pere va marcar un arc molt subtil sobre el disc lunar de la Sony. És on cau una
frontera de fusió: **t = 1/32 s pes→1 a 1,266 R☉** i **t = 0,125 s pes→0 a
1,263**, amb la de t = 0,25 s a 1,271.

Amb el compost coherent, l'amplitud **al llarg del contorn** millora poc:

| frontera | abans | ara |
|---|---:|---:|
| t=1/32 s pes→1 · r = 1,266 | 0,526 % (4,40 σ) | **0,494 % (4,07 σ)** |
| t=0,125 s pes→0 · r = 1,263 | 0,444 % (3,45 σ) | **0,405 % (3,16 σ)** |

⛔ **Però el control APARELLAT també dispara**: el mateix contorn desplaçat
−110 px dona 0,159-0,222 % a 2,97-3,69 σ. Un control que dispara vol dir que
l'estadístic **no és específic de la frontera** en aquella zona: la corona
interior hi té estructura fina de veritat i la base transversal la llegeix com
un tret.

⏭️ **I la prova que decideix**: la mediana per anell del detall, calaixos de
0,004 R☉, als **dos** trens:

| r (R☉) | Vixen | Sony |
|---:|---:|---:|
| 1,260 | +0,0030 % | +0,0014 % |
| 1,264 | −0,0054 % | −0,0011 % |
| 1,268 | −0,0033 % | −0,0004 % |
| 1,272 | +0,0052 % | +0,0024 % |

**Allà no hi ha cap anell**, ni a la Vixen —que no hi té cap frontera— ni a la
Sony. La component circular hi és **seixanta vegades més petita** que el que
mesura el contorn. El que queda a 1,26 R☉ segueix una isofota i té mediana
azimutal zero: no és una circumferència.

---

## §3 ⛔ El flat queda DESCARTAT, i la no-linealitat del pou també

`research/100` deixava obert que la dependència amb el nivell podia ser el flat
o el pou, i que les dues signatures eren degenerades perquè el nivell
correlaciona amb el radi. Tancat per tres vies independents.

### 3.1 La prova d'un sol paràmetre: compondre amb `flat=no`

| parell d'esglaons | flat = SÍ | flat = NO | canvi |
|---|---:|---:|---:|
| 0,0625 → 0,125 | +0,211 % | +0,277 % | +0,067 % |
| 0,25 → 0,5 | +0,171 % | +0,193 % | +0,022 % |
| 0,5 → 1 | +0,018 % | −0,018 % | −0,036 % |
| **mitjana \|desacord\|** | **0,123 %** | **0,122 %** | — |
| **pitjor** | 0,463 % | 0,448 % | — |
| **correlació entre els dos jocs** | — | — | **0,984** |

⛔ **Treure el flat sencer no canvia res.** Amb r = 0,984 entre els dos jocs, el
flat **no pot ser** la causa.

I hi ha l'argument físic que hi lliga: un flat multiplicatiu **es cancel·la
exactament** en un quocient entre dos esglaons al mateix píxel. Només pot
filtrar-s'hi per la deriva d'apuntament, i entre esglaons veïns de la Vixen
—separats ~6 s— la deriva és de **2 px**. Perquè el flat expliqués un 1,2 %
caldria un gradient de 0,04 %/px, o sigui un 80 % sobre el camp.

### 3.2 L'eina nova: `atribueix_nivell.py`

Separa una dependència del **nivell** d'una del **radi** condicionant l'una a
l'altra: dins de cada calaix de radi es treu la tendència radial i es compara
el tercil alt contra el baix de nivell, i a l'inrevés. La palanca és que **la
corona no és circular**: a radi fix hi ha serpentines i forats.

⛔ Validada amb quatre casos sintètics de resposta coneguda, **inclòs el cas
que la fa perillosa**: una dependència purament radial produeix un efecte de
nivell marginal gros, i la prova l'ha de matar en condicionar. La primera
versió no ho feia i la prova la va enxampar.

Sobre les dades reals, als parells que porten corona:

| parell (s) | efecte del nivell a radi fix | efecte del radi a nivell fix | veredicte |
|---|---:|---:|---|
| 0,03125 → 0,0625 | −0,335 % (2,2 σ) | −0,553 % (4,5 σ) | CAMP |
| 0,0625 → 0,125 | **−0,780 % (4,5 σ)** | −0,261 % (1,4 σ) | SENSOR |
| 0,125 → 0,25 | +0,036 % (0,3 σ) | −0,272 % (2,0 σ) | CAP |
| 0,25 → 0,5 | **−0,434 % (3,2 σ)** | −0,104 % (0,7 σ) | SENSOR |
| 0,5 → 1 | **+0,549 % (3,5 σ)** | +0,160 % (1,3 σ) | SENSOR |
| 1 → 2 | +0,209 % (1,1 σ) | −0,108 % (0,6 σ) | CAP |
| 2 → 10,08 | −0,556 % (2,9 σ) | +0,215 % (1,2 σ) | CAP |

L'efecte del radi és ≤ 0,27 % i per sota de 2 σ a cinc dels set parells. El del
nivell mana. **Però el seu signe ALTERNA**: −0,335, −0,780, +0,036, −0,434,
**+0,549**, +0,209, −0,556.

⛔ **Una no-linealitat de pou no pot alternar de signe.** Una corba de resposta
és monòtona: si a nivell alt es perd senyal, es perd a tots els parells que
mostregen aquell nivell.

### 3.3 La conclusió

**No és el flat i no és el pou: són OFSETS PER ESGLAÓ**, de ±0,1 a ±0,5 %, cada
un al seu tram de nivell. És exactament el residu que la coherència de
transparència deixa quan el seu model d'un escalar per fotograma no acaba de
tancar.

---

## §4 ⏭️ Decisió: `PILOT_SOSTRE` es queda a 0,85

**Rectifica el traspàs del 25 al matí.** Allà es recomanava baixar-lo a 0,80
perquè les costures queien a la meitat. Amb §3 resolt, aquella millora és un
**pal·liatiu**: baixar el tall no ataca cap causa —no hi ha saturació no lineal
que corregir— i **costa senyal/soroll** (el jutge extern el penalitza amb
Δz = −0,0062 ± 0,0007).

⛔ **No es toca.** El comentari de `comu.py` que diu que el valor de producció
és 0,85 i que qualsevol altre és només per a la prova de moure fronteres queda
confirmat, no superat.

---

## §5 ⛔ La correcció per esglaó, provada i REFUSADA

`corregeix_costures.py` ajusta `error = Σ_k f_k·δ_k`, un escalar per esglaó,
amb el gauge Σδ = 0 i la regularització calibrada. Amb el λ correcte l'ajust
surt **sa per primera vegada**: tots els |δ| < 1 %, de +0,830 % (0,125 s) a
−0,896 % (2 s), i el patró alterna igual que el §3.

| jutge extern | **EMPAT** · Δz = +0,00065 ± 0,00070 |
|---|---|
| detector de costures, abans | **0 de 12** fronteres per damunt del terra |
| detector de costures, després | **2 de 12** (0,0222 %) |
| terra dels 182 controls | 0,0005 % → **0,0123 %** (×25) |

⛔ **Refusada.** El jutge diu que és innòcua —no menja corona— però el detector
diu que **crea** dues costures i multiplica per 25 el terra de control, o sigui
que injecta estructura que segueix l'eix del nivell. I sobretot: **no calia**,
perquè el producte ja tenia 0 de 12 fronteres per damunt del terra.

---

## §6 Els filtres: `filtres_druckmuller.py`

Demanats per Pere: un passa-alt, un desenfoc radial, i tot el que sigui útil de
la família de Brno. Set filtres, tots amb pes, tots al rectangle sencer.

| filtre | què normalitza | quan serveix |
|---|---|---|
| `passa_alt` | res: treu la part suau | veure detall a una escala triada |
| `desenfoc_radial` | res: suavitza en polars | soroll fora **sense** matar els raigs |
| `nrgf` | mitjana i dispersió per anell | aplanar la caiguda radial |
| `fnrgf` | mitjana i dispersió per anell **i azimut** | corona molt asimètrica |
| `mgn` | dispersió local a cada escala | detall a totes les escales alhora |
| `wow` | dispersió per escala + porta | màxim detall amb soroll controlat |
| `nafe` | rang local difús | contrast local sense cremar |

Les tres regles que els governen: **norma del rectangle**, **convolució
incompleta** (`G(w·I)/G(w)`, mai `G(I)`) i **porta de soroll suau** (`erf`, mai
un llindar dur).

⚠️ **El desenfoc porta els dos sentits i no s'han de confondre**: l'**azimutal**
suavitza al llarg dels anells i allarga els raigs —és el «radial blur · zoom»
de Photoshop—; el **radial** fa el contrari i reforça justament els anells i les
costures, o sigui que a la corona sol ser el que NO vols. Hi és perquè és la
manera de mesurar quanta senyal circular hi ha.

**Catorze proves**, i tres van enxampar defectes reals abans de sortir:

- ⛔ **NRGF i NAFE dividien per una dispersió que podia ser zero.** Amb una
  entrada exactament llisa el NRGF donava O(1) i el NAFE saturava a ±1 al camp
  sencer: **inventaven un camp on no hi havia res**. Curat amb un terra
  **mesurat** (`soroll_per_diferencies`, l'estimador de les diferències entre
  veïns) i mai per sota d'una part per milió de la dispersió pròpia.
- ⛔ **El FNRGF tornava a indexar amb la màscara una llista ja filtrada.**
- ⛔ **El WOW feia un marc brillant a la vora del rectangle**, per la mateixa
  divisió sense terra. Ho va destapar el full de contacte, no el codi.

I la prova que val per a tots: **cap filtre no pot fabricar un anell**. Se'ls
dona una entrada amb estructura **només azimutal** —la seva mediana per anell
és zero per construcció— i s'exigeix que la component circular de la sortida
es quedi per sota del **20 %**. Els vuit hi passen.

---

## §7 El projecte de Photoshop

`munta_photoshop.py` escriu un PSB de 16 bits amb els dos trens i un filtre per
capa, al llenç comú i retallat quadrat a ±6 R☉.

| capa | mode |
|---|---|
| `00 · BASE corona · dos trens (calibrada)` | Normal, visible |
| `01 · DETALL fusionat · ACHF multi-σ (fase 3)` | Superposar, visible |
| `02…10` · passa-alt ×2, desenfoc ×2, NRGF, FNRGF, MGN, WOW, NAFE | Superposar, apagades |

⛔ **La base és l'única capa amb sentit fotomètric.** Tota la resta són maneres
de veure. I el retall és **quadrat**, no circular: el que limita cada capa és el
seu mapa de dada.

---

## §7 quater ⏭️ LES MARQUES DE PERE, i per què les nostres mesures eren cegues

**Migdia del 25.** Pere ha marcat sobre la vista dels dos trens: **tres corbes
tancades** al voltant de la Lluna a la Vixen (≈ 1,25 · 1,51 · 1,97 R☉) i **un arc
curt** a la Sony (≈ 1,18 R☉). ⛔ **No són circumferències: són isofotes.**

Mesurat **al llarg del contorn**, les fronteres de fusió de la Vixen hi cauen
clavades i **sí que disparen**:

| radi | amplitud | σ | frontera | marca |
|---:|---:|---:|---|---|
| 1,241 | **0,7151 %** | 2,86 | t=0,25 s pes→0 | verd interior |
| 1,251 | **0,5605 %** | **3,56** | t=0,0625 s pes→1 | verd interior |
| 1,513 | 0,0820 % | 2,90 | t=0,5 s pes→1 | verd mig |
| 1,969 | 0,0500 % | **4,14** | t=2 s pes→1 | verd exterior |
| 1,971 | 0,0474 % | **3,93** | t=10,08 s pes→0 | verd exterior |

⛔ **I les mateixes fronteres surten netes amb els altres dos estadístics.** Això és
el nus de tot el que hem fet malament aquests dies:

| estadístic | veredicte | per què és cec |
|---|---|---|
| detector per **nivell** | 0 de 12 | busca un **GRAÓ**; si és un **BONY** centrat a la frontera, la discontinuïtat val zero |
| **mediana per anell** | ≤ 0,008 % | la isofota està escampada en radi (la de 10,08 s de 1,57 a 2,35 R☉): dilució **×23** |
| **al llarg del contorn** | 0,05-0,72 % a 2,9-4,1 σ | ✅ segueix la mateixa corba que l'ull |

⏭️ **Les mesures no eren errònies: promediaven sobre la variable equivocada.**

⚠️ I la porta **H2 dona PASS** perquè el seu control aparellat té un terra de 4,32 σ
i la pitjor frontera val 4,14. El control dispara perquè la corona interior té
estructura fina pertot arreu. **Una porta a qui el control li tapa la troballa no és
una porta**, i s'ha de repensar.

⏭️ **La hipòtesi que se'n deriva, i és d'un sol paràmetre**: un desajust de nivell
faria un **graó**; un **bony** és la resposta d'un passa-alt a un canvi de
**curvatura**, i el `taper` de fusió n'és un encara que sigui C². Ja està mesurat que
pujar l'ordre de la rampa el va reduint —clip → smoothstep → smootherstep—, o sigui
que la prova següent és **`PILOT_ORDRE_RAMPA = 7`**.

## §7 ter ⛔ El PSB que Photoshop refusava: la previsualització anava a 8 bits

El primer PSB lliurat no s'obria: «s'ha trobat un final de fitxer inesperat».
⚠️ I `psd-tools` **sí que l'obria**, amb les dotze capes, els noms, els modes i
les màscares. Diagnosticat amb quatre vies independents i cadascuna refutada per
un agent a part; cap de les quatre refutacions va tombar la conclusió.

Caminant el fitxer byte a byte, **cap longitud estava malament**: les de «layer
and mask information», «layer info», cada `ChannelInfo` i el bloc `Lr16` eren
totes de **8 bytes**, com el PSB exigeix, i les tres fronteres queien al mateix
byte amb diferència **0**. El que fallava era l'última secció:

| | trencat | arreglat |
|---|---:|---:|
| bytes a «Image data» | **47.187.468** | **94.374.936** |
| exigits per la capçalera (3966×3966×3×2) | 94.374.936 | 94.374.936 |
| raó | **2,0000** | 1,0000 |

⛔ **La previsualització fusionada estava escrita a 8 bits en un document
declarat de 16.**

**La causa**: `set_merged()` desa la previsualització bona i apaga la bandera que
diu «no la recomponguis»; `finalize_lr16()` crida `_update_record()`, que **la
torna a encendre sense dir-ho**; llavors `save()` la refà amb `composite()`, que
retorna una imatge **PIL**, i PIL no sap fer RGB de 16 bits. La docstring de
`finalize_lr16` ja avisava de l'ordre —«DESPRÉS de l'últim append i **ABANS** de
`set_merged`»— i jo el vaig posar al revés.

**Tres cures, no una:**

1. l'ordre correcte;
2. ⛔ **tornar a apagar la bandera just abans de desar**, perquè una promesa que
   depèn d'un senyalador que qualsevol altra crida pot reactivar no és una
   promesa;
3. **la porta `verifica_psb()`**, que comprova el fitxer desat **contra la seva
   pròpia capçalera** i falla tancat. Quatre proves: un fitxer bo passa, un amb
   la meitat dels bytes falla, un amb el doble també, i una que exigeix que la
   longitud es llegeixi de 8 bytes i no de 4 —si es llegís de 4, l'inici d'«Image
   data» sortiria desplaçat i el veredicte seria fals—.

⏭️ **La lliçó que va més enllà d'aquest format**: que la llibreria que escriu un
producte el pugui tornar a llegir **no demostra res**. La comprovació ha de ser
contra el contracte, no contra l'escriptor.

## §7 bis ⏭️ EL CAP OBERT NOU: un patró periòdic al detall, diferent a cada tren

Mirant el producte muntat amb el mode Superposar —que és com el veurà Pere— i
ampliant el quadrant superior dret entre 1,4 i 2,0 R☉, hi ha **una trama de
línies fines**, i **no són anells**: són rectes.

Mesurat per Fourier sobre una finestra de 512 px al mateix lloc dels dos trens:

| tren | període | orientació | contrast sobre la mediana |
|---|---:|---:|---:|
| Vixen + R6 III | **114,5 px** | +63,4° | 634 |
| Sony A7RIIIA | **90,5 px** | −135,0° | **6.330** |

⛔ **Període i orientació són DIFERENTS a cada tren**, o sigui que **no és
corona**: la corona és la mateixa per als dos i el patró no ho és.

⚠️ **Hipòtesi principal, no comprovada**: la **porta de soroll de l'ACHF a
l'escala gran**. `erf(|d|/(n_s·σ_d))` amb σ = 32 px deixa passar o no segons el
soroll local, i això pot pintar una textura amb grumolls de l'ordre de 3σ ≈
100 px. Encaixa amb els dos períodes i explica per què és diferent a cada tren:
els seus mapes de soroll ho són.

⏭️ **Com es comprova, i és barat**: compondre la fase 3 amb la porta de soroll
apagada (`n_soroll` molt gran) i tornar a mesurar el pic de Fourier. Si el pic
cau, és la porta. I si és la porta, la cura no és treure-la —serveix per a una
cosa— sinó **suavitzar-la a l'escala gran**.

⛔ **El que NO s'ha de fer**: sortir a buscar-ho amb un filtre direccional. El
patró té una causa i s'ha de trobar, no tapar.

## §8 El que queda obert

- ⚠️ **L'arc que Pere veu a 1,26 R☉ no té component circular mesurable**, però
  el seu contorn dona 0,49 % a 4 σ **amb el control aparellat disparant també**.
  Cal una mesura que sigui específica de la frontera en una zona amb estructura
  real, o acceptar que allò és corona.
- Les propostes de Codex que continuen pendents: validació δ amb meitat
  retinguda i la corba d'un sol coeficient amb `x₀` per validació retinguda.
- El **sostre de la Sony no s'ha escombrat mai** —fins avui era un literal
  amagat—; ara és `PILOT_SOSTRE_SONY` i es pot fer.
- La cadena sencera de la Vixen **no s'ha refet** amb els arranjaments d'avui:
  no calia, perquè el defecte del `_coh` era del costat Sony, però el producte
  final barreja dates i això s'ha de dir.
