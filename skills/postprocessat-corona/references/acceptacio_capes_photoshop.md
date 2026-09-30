# Acceptació canònica de capes ja apilades a Photoshop

Autoritat de projecte: Pere, 20-08-2026. Aquest protocol evita la **torre de
Pisa**: una capa nova no pot compensar un error d'un fonament anterior.

Versió 2 (21-08-2026): les portes marcades **[21-08]** s'afegeixen després de
`3-RECERCA/87 §11.2`: un fonament heretat amb rebut PASS tenia un forat azimutal
de 45° a la màscara de la 1/125 al voltant de la protuberància (0,006 on la
resta valia 0,38), i cap porta el va veure perquè totes jutjaven només
DESPRÉS−ABANS i excloïen la zona lunar i els nuclis. La numeració antiga
G0–G11 dels rebuts del 20-08 correspon a l'actual G0–G7 (G8→G5, G9→G6,
G10/G11→G7).

## 1. Abast i frontera amb l'apilatge

Aquest protocol comença amb màsters lineals ja acceptats per
`apilatge-imatges-eclipsi`. La selecció de fotogrames, calibratge, SNR,
variància, rebuig i denoise previ no es decideixen aquí.

Si Pere declara que els stacks Vixen i Sony són bons, aquesta declaració és la
precondició operativa. Només es torna a l'apilatge si una anomalia concreta del
compost apunta a un defecte upstream. La falta de rebut és `FALTA ENTRADA`, no
una invitació a repetir tota l'anàlisi.

Classes de capa:

- `FONT_HDR`: màster lineal que aporta un rang radiomètric.
- `FONT_PROTEGIDA`: màster curt dedicat a limbe, cromosfera,
  protuberàncies, perles, diamant o earthshine.
- `DETALL`, `COLOR`, `CORRECCIO`, `VISUALITZACIO`: derivats visuals; no formen
  part de la pila font ni tornen a càlculs científics.

Estats: `DEMOSTRAT`, `FALTA` o `N/A` justificat. Veredictes:
`ACCEPTADA`, `REPROCESSAR`, `QUARANTENA` o `REBUTJADA`. No existeix
`ACCEPTADA CONDICIONAL`.

## 2. Portes, en ordre

### G0 — Identitat i fonament immutable

- `G0.01` Registra document, capa, ruta font, mida i SHA-256.
- `G0.02` Registra tren, càmera, òptica, muntura, instant i exposició.
- `G0.03` Classifica la capa i declara'n una sola funció.
- `G0.04` Declara el marc: `CORONA_SOLAR`, `LLUNA` o `ESTRELLES`.
- `G0.05` Identifica el màster lineal upstream i el seu veredicte d'apilatge.
- `G0.06` Congela document i compost `ABANS` amb hash.
- `G0.07` Conserva font i píxels de la capa immutables; qualsevol transformació
  és un derivat nou i traçable.
- `G0.08` Demostra que cap calibratge, normalització o registre s'ha aplicat
  dues vegades.
- `G0.09` **[21-08]** Cap fonament s'accepta per rebut. Abans de construir-hi
  a sobre, torna a passar sobre el compost ABANS (fonament sol) les portes
  absolutes de G5.10 i G5.11 i el pilot de baix a dalt de G7.07. Un PASS antic
  de l'ABANS és història; el PASS d'avui es mesura avui.

Si canvia un fonament, invalida els rebuts de totes les capes dependents i
torna a derivar les màscares dependents des de zero amb G4.04 i G4.10; no les
reaprofitis ni n'heretis els zeros.

### G1 — Aportació radiomètrica i redundància PSD

- `G1.01` Delimita la regió i el rang de radiància que aporta la candidata.
- `G1.02` Demostra que aporta rang dinàmic, cobertura o un fenomen temporal
  que encara no aporta el compost inferior.
- `G1.03` Ordena les fonts per rang útil global, no per nom o posició actual.
- `G1.04` Identifica les bandes veïnes i un solapament mesurable.
- `G1.05` Demostra que no queda cap buit radiomètric.
- `G1.06` Mesura continuïtat fotomètrica dins el solapament.
- `G1.07` Rebutja una segona capa PSD que no afegeixi cap aportació de G1.02.
- `G1.08` No confonguis una capa PSD redundant amb captures independents: les
  repeticions útils ja s'han resolt upstream en un únic màster.
- `G1.09` Si falla la primera banda, reprocessa-la; no compensis la costura amb
  una capa posterior.

“Adjacent i superior” significa banda veïna amb solapament, no una ordre
visual rígida.

### G2 — Linealitat, atmosfera i camp

- `G2.01` Usa el mapa de rang lineal vàlid del màster; la màscara dona pes zero
  a saturació, no-linealitat i regions no cobertes.
- `G2.02` No converteixis el 85 % en un objectiu d'histograma Photoshop.
- `G2.03` Tracta extinció atmosfèrica com a terme multiplicatiu.
- `G2.04` Tracta cel i llum dispersa com a terme additiu separat.
- `G2.05` Tracta refracció, compressió, rotació i dispersió cromàtica com a
  efectes geomètrics.
- `G2.06` Tracta flat, vinyetatge, PRNU i ghosts com a efectes instrumentals,
  no atmosfèrics.
- `G2.07` No corregeixis tots aquests efectes amb una sola màscara opaca.
- `G2.08` A 8–10° d'altura, exigeix model o mesura abans de declarar un efecte
  negligible.
- `G2.09` Demostra que fons i normalització no eliminen corona F real.

### G3 — Registre, moviment i PSF

- `G3.01` Registra cada capa directament contra la referència immutable.
- `G3.02` No registris mai contra l'última capa acceptada.
- `G3.03` No transfereixis transformacions entre cossos, òptiques o muntures.
- `G3.04` Admet translació i rotació dependents del temps; escala i distorsió
  només si les mesures les exigeixen.
- `G3.05` Usa marc solar per corona, lunar per earthshine i estel·lar per
  astrometria. No deformis la corona per encaixar simultàniament els tres.
- `G3.06` Registra mètode, regió, transformació, residu i incertesa.
- `G3.07` Exigeix precisió subpíxel quan la resolució ho permet; no descriguis
  el registre com a “perfecte”.
- `G3.08` Mesura moviment intraexposició i PSF quan limitin detall.
- `G3.09` La rodonesa de les estrelles és un diagnòstic condicional, no prova
  suficient del registre coronal.
- `G3.10` No confonguis evolució física de cromosfera/corona amb error
  geomètric corregible.

### G4 — Estat de capa i màscara

- `G4.01` Cada `FONT_HDR` o `FONT_PROTEGIDA` té màscara explícita pròpia.
- `G4.02` La font és `Normal`, opacitat 100 % i farciment 100 %.
- `G4.03` No pintis, clonïs, esborris ni alteris tonalment els píxels font.
- `G4.04` Construeix la màscara amb geometria, rang vàlid i solapament; no
  segons l'estructura que es vol fer aparèixer.
- `G4.05` Bloqueja completament tot el que queda fora del rang declarat.
- `G4.06` No comparteixis una màscara lunar entre capes amb geometries
  lunars diferents.
- `G4.07a` Per unir dues `FONT_HDR` adjacents, prova primer una transició
  gaussiana aplicada exclusivament a la màscara o pes de la candidata. No
  desenfoquis mai el raster font ni el compost.
- `G4.07b` Limita la gaussiana a una banda explícita de solapament radiomètric
  i geomètric. Després del desenfocament, reaplica els zeros durs de cobertura,
  regions invàlides, disc lunar i nuclis protegits; fora del suport declarat
  no pot canviar cap píxel.
- `G4.07c` El radi o sigma és propi de cada parella, geometria i escala de
  document. Deriva'l de l'amplada mesurada del solapament, el residu de
  registre i la distància a regions protegides o invàlides. Cap valor validat
  anteriorment és una constant universal.
- `G4.07d` Valida diversos radis amb un pilot 1:1 `inferior | candidata |
  màscara | resultat | diferència` i tria el radi mínim que elimina la costura
  sense crear halo, gradient, anell, bombolla ni pèrdua d'estructura. Registra
  el paràmetre i l'amplada efectiva de la transició.
- `G4.07e` Accepta només si el nucli protegit continua exactament igual, fora
  del suport tot és byte a byte idèntic, la diferència no dibuixa la frontera
  i els perfils locals o sectorials no introdueixen cap extrem nou ni un pic de
  gradient centrat a la costura.
- `G4.08` No amaguis mala alineació o normalització canviant mode, opacitat o
  màscara.
- `G4.09` Si una capa necessita un altre mode o opacitat, reclassifica-la com
  a derivat visual i treu-la de la pila font.
- `G4.10` **[21-08]** La màscara d'una `FONT_HDR` és el producte de tres
  factors i res més: una rampa **radial** solar (funció del radi, promitjada
  per anell, sense estructura azimutal), una porta **lunar per capa** (centre i
  radi mesurats al ràster d'aquella capa, amb la banda d'artefacte d'apilat
  dels seus membres si n'és un) i la protecció de fenòmens de G4.11. Queden
  prohibits a la pila font: el·lipses, sectors, pinzellades, seleccions per
  lluminositat, operadors morfològics i desenfocs isòtrops globals. Tota la
  suavitat és radial. Els zeros d'una màscara antiga no s'hereten mai.
- `G4.11` **[21-08]** Protegir un fenomen vol dir alfa zero de les capes
  superiors **només sobre els píxels del fenomen** (nucli derivat de la
  `FONT_PROTEGIDA` per llindar, dilatat ≤3–4 px, ploma ≤4–6 px). Al voltant
  del fenomen la capa vàlida hi entra amb la seva rampa radial normal. Una
  protecció que deixi a la vista una capa més fosca al voltant del fenomen —un
  forat, una ombra, una bombolla— és un defecte, no una protecció.

### G5 — Artefactes i estructura

- `G5.01` Genera `DESPRÉS` afegint només la candidata.
- `G5.02` Genera `DESPRÉS-ABANS` dins i fora de la màscara.
- `G5.03` Visualitza la contribució real de cada capa, no només la màscara.
- `G5.04` Fes blink i inspecció a 100 % amb el mateix estirament.
- `G5.05` Busca costures, anells, halos, bombolles, dobles vores, gradients,
  ghosts i patrons de màscara.
- `G5.06` Comprova perfils locals i sectorials; un perfil radial global no és
  prova suficient.
- `G5.07` Rebutja qualsevol estructura que segueixi màscara, sensor o procés
  més que el Sol.
- `G5.08` Rebutja canvis fora del rang i suport declarats.
- `G5.09` Quan es reivindiqui detall nou, exigeix una font, tren o control
  independent si existeix.
- `G5.10` **[21-08]** Prova **absoluta** per sectors, a cada estat acumulat i
  també al fonament sol (no només sobre DESPRÉS−ABANS): mediana per anell
  lunar-cèntrica en sectors de 5° entre R+3 i R+120 px, i solar-cèntrica en
  sectors de 15° fins a 3 R☉. Cap sector pot quedar per sota del 85 % de la
  mediana dels seus quatre veïns de cada costat si la capa vàlida hi és la
  mateixa: un sot azimutal d'aquesta mida és màscara, no corona. Les zones
  lunar (des de R+3) i de nuclis NO s'exclouen d'aquesta prova; només s'hi
  interpreta el resultat amb la font inferior com a autoritat.
- `G5.11` **[21-08]** Prova de **cobertura de validesa**: per a cada cel·la
  (anell de 4 px × sector de 5° fins a 1,5 R☉; 15° fins a 3 R☉), la
  contribució efectiva de les capes que hi són vàlides (p50 ≤0,46 i p95 ≤0,66
  del canal màxim sobre la capa revelada, `3-RECERCA/84 §5`) ha de ser ≥0,9.
  Excepcions: els píxels de P3/P4 amb la seva ploma (l'autoritat inferior hi és
  vàlida per definició) i la banda d'artefacte declarada d'un apilat. L'empremta
  no radial de la màscara es mesura incloent la zona lunar des de R+3.

### G6 — Limbe, protuberàncies, perles i diamant

Aquesta porta s'aplica a **tota capa superior** que cobreixi geomètricament una
font protegida, encara que es digui interior, exterior, correcció o detall.

- `G6.01` Declara per fenomen la `FONT_PROTEGIDA` inferior que n'és l'autoritat
  temporal. Una capa posterior més neta o més llarga no la substitueix.
- `G6.02` Registra la font i congela el compost inferior abans de mirar o
  construir cap màscara superior.
- `G6.03` Deriva de la font inferior un nucli morfològic immutable per a limbe,
  cromosfera, cada protuberància, cada perla i el diamant.
- `G6.04` Força alfa efectiva exactament zero de totes les capes superiors al
  disc lunar i als nuclis protegits.
- `G6.05` Dins el nucli, el resultat reprodueix píxel per píxel el compost
  inferior fins a la quantització del document.
- `G6.06` Mesura components, àrea, centroides, pic i flux. Cap component pot
  desaparèixer, fusionar-se, moure's o perdre lluminositat.
- `G6.07` Si la protecció governa dues o més capes `Normal`, no multipliquis
  independentment totes les alfas pel mateix factor. Transforma-les
  conjuntament de dalt cap avall perquè el resultat sigui
  `inferior + q·(superior−inferior)`.
- `G6.08` Separa el **suport científic** del fenomen de la **zona de barreja**.
  El primer prové només de la font inferior. La segona pot estendre's fora del
  nucli únicament on la compatibilitat entre els dos compostos permet una
  transició suau; no implica que hi hagi fenomen en aquella ploma.
- `G6.09` Tria l'amplada mínima amb un pilot 1:1 `inferior | superior |
  resultat | diferència`. Un radi o amplada validat per un producte no és una
  constant universal.
- `G6.10` Prohibeix el desenfocament del raster, del suport científic o de tota
  la màscara sense domini. Es permet una transició gaussiana local a la zona de
  barreja si el nucli protegit es torna a imposar exactament després del blur,
  el domini és explícit i el pilot 1:1 supera els gates de contorn, gradient i
  halo. Dilatació, closing, fill o EDT genèrics no poden imprimir la geometria
  del suport.
- `G6.11` Al nucli, diferència exacta zero; a la ploma, error màxim d'1 DN
  contra la interpolació ideal; fora de la zona, màscares i render byte a byte
  idèntics.
- `G6.12` Renderitza font inferior, compost superior, resultat i diferència a
  100 %. Rebutja qualsevol contorn, halo, anell o bombolla nou.
- `G6.13` Si falta una sola perla, part del diamant, protuberància o canvia el
  limbe, dictamina `REPROCESSAR` i invalida qualsevol PASS posterior.
- `G6.14` **[21-08]** Mesura l'extensió de la protecció: àrea de P3/P4 i
  distància màxima de qualsevol píxel protegit al píxel de fenomen més proper.
  Si la distància supera la dilatació més la ploma declarades (≤10 px en
  total), la protecció és una bombolla (vegeu G4.11) i el veredicte és
  `REPROCESSAR` del fonament, no de la capa candidata.

### G7 — Acceptació, dependències i reversió

- `G7.01` Completa el rebut abans del veredicte.
- `G7.02` Desa hashes d'ABANS, DESPRÉS, màscares, nuclis i diferències.
- `G7.03` Registra posició, dependències i dependents de la capa.
- `G7.04` Si canvia una base, revalida des del primer fonament modificat cap
  enfora.
- `G7.05` Conserva una reversió que retiri només el candidat.
- `G7.06` No promoguis el PSB complet fins que el pilot 1:1 passi.
- `G7.07` **[21-08]** Pilot de **baix a dalt** obligatori abans de qualsevol
  promoció (el test de Pere): renderitza a 100 % el limbe amb la protuberància,
  les perles i la banda d'artefacte per a cada estat acumulat —la base sola,
  +1, +2, …— amb el mateix estirament i la diferència entre estats
  consecutius, i mira-ho. Si en algun estat apareix ombra, anell, bombolla o
  vel, la capa responsable és la de l'estat on apareix, i es corregeix allà.
  Els PNG van al rebut.

## 3. Rebut mínim

```text
REBUT_CAPA
id_rebut:
document_abans_sha256:
document_despres_sha256:
capa_id_nom_classe_funcio:
master_upstream_i_veredicte:
font_path_size_sha256:
marc_i_referencia:
transformacio_residu_incertesa:
rang_aportat_bandes_veines_solapament:
extincio_fons_refraccio_camp:
mascara_sha256_regio_zero_transicio:
mode_opacitat_farciment:
font_protegida_per_fenomen:
referencia_inferior_sha256:
nuclis_i_zona_barreja_sha256:
qa_nucli_exacte:
qa_components_centroides_pic_flux:
qa_interpolacio_ploma:
qa_fora_zona_byte_identic:
qa_100pct_i_diferencia:
qa_absoluta_sectors_5deg_G5_10:
qa_cobertura_validesa_G5_11:
qa_extensio_proteccio_G6_14:
pilot_baix_a_dalt_G7_07:
artefactes_buscats:
portes_G0_G7:
veredicte:
motiu:
dependents_invalidats:
reversio:
```

## 4. Correccions a les regles originals

| Regla original | Formulació canònica |
|---|---|
| Rang diferent i adjacent | Rang radiomètric incremental amb banda veïna i solapament mesurat. |
| Histograma i 85 % | Rang lineal upstream per canal; mai objectiu d'histograma Photoshop. |
| Gradient atmosfèric | Separar extinció, fons, refracció/dispersió i camp instrumental. |
| Soroll i denoise | Pertanyen íntegrament a `apilatge-imatges-eclipsi`. |
| Capa repetida | Rebutjar redundància PSD; les captures independents ja s'han apilat upstream. |
| Alineament de tot | Marcs solar, lunar i estel·lar separats, amb residu declarat. |
| Estrelles rodones | Diagnòstic condicional, no prova de registre coronal. |
| Màscara per capa | Mapa explícit de validesa i solapament, zero fora de rang. |
| Normal/100 % | Només fonts; els derivats visuals declaren la seva classe. |
| Protegir fenòmens | Congelar la font inferior i anul·lar totes les capes superiors al nucli. |
| Alineament perfecte | Objectiu mesurat, mai afirmació sense residu i incertesa. |

La compatibilitat metodològica amb Druckmüller es conserva: repeticions i
calibratge upstream, referència geomètrica immutable, compositor ponderat i
separació estricta entre radiometria i visualització.
