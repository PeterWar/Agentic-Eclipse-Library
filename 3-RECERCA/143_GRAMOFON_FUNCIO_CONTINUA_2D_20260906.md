# Gramòfon: recerca amb funcions contínues bidimensionals

06-09-2026 · Codex · estudi exploratori acabat · canal G · cap candidat promogut al PSB.

**Resultat:** una estimació local contínua elimina per construcció dos mecanismes concrets: els salts entre bins radials i la propagació d'una estructura brillant a tot el seu anell. Això no elimina tots els halos ni preserva automàticament tota la corona. Els candidats provats encara fallen en arcs amples, senyal feble o cobertura incompleta. La prova addicional de correcció 2D per fotograma millora alguns desacords de font, però el benefici global és modest i desigual. No s'ha trobat encara un remei integral validat.

Pere ha autoritzat investigar la causa, en lloc d'interpolar els píxels dels cercles. S'ha implementat i contrastat aquesta via, sense canviar V31, els RAW, la graella o les màscares físiques. El protocol inicial i les extensions motivades pels resultats són a [PLAN.md](</Users/USUARI/Downloads/Eclipse 2026/research/tools/gramofon_2d_20260906/PLAN.md>). No s'han ajustat els llindars per convertir una fallada en èxit.

## 1. Quatre passos executats

1. **Separar mecanismes:** bins, dependència de tot l'anell, resposta del model al perfil radial i defectes ja presents a la base. No hi ha evidència que tots els cercles tinguin una única causa o una separació constant.
2. **Construir el fons 2D continu:** models locals Q2 i LR, directament a la graella original. Primer la resta del fons amb guany fix; després una prova separada de normalització del contrast.
3. **Intentar refutar-los:** nuls, cobertura irregular, Fourier amb fase i orientació, arcs reals injectats, soroll, halos i refit robust. Els controls que simplement esborren el senyal fallen.
4. **Contrastar amb dades independents:** Sony sola contra Vixen original fix, sis finestres natives. Addicionalment, diferències entre fotogrames Sony per estudiar un fons additiu 2D abans de filtrar.

## 2. Funció contínua: què garanteix i què no

Siguin `z_i = log(I_i)` les intensitats positives observades a `p_i`. Per a cada posició de consulta `x`, s'ajusta un model amb pesos locals

`K_h(p_i-x) = (1-t)^4 (1+4t)`, si `t=||p_i-x||/h < 1`; zero altrament.

És un nucli C2 de suport compacte. Les observacions invàlides tenen pes zero, sense inventar dades. El fons és el valor del model ajustat a `x`; el detall és `D(x)=log(I(x))−B(x)`, avaluat als píxels originals.

- **Q2:** mínims quadrats ponderats amb sis bases `1, ux, uy, ux², ux·uy, uy²`, coordenades locals normalitzades per `h`.
- **LR:** ajust local `log I ≈ β0(x)+β1(x) log r`. Els coeficients canvien amb la posició i només comparteixen dades dins del veïnat cartesià; no es calculen estadístiques d'un anell complet.
- **Controls:** mitjana local de `log I`, NRGF amb bins i amb perfils interpolats, i MGN publicat al pilot real.

Amb observacions i pesos de certesa fixos, els moments i el terme independent són C2 respecte de `x`. On la matriu té rang complet, la inversa i el fons també són C2. Això exclou discontinuïtats de binning. El suport compacte limita la influència a `h`: un canvi local no pot alterar l'altre costat del Sol si queda fora d'aquest veïnat. El codi comprova rang/condicionament; als casos provats queda definit tot el suport observat.

La continuïtat no garanteix un fons físicament correcte. Un model continu també pot absorbir corona o generar lòbuls negatius. A més, restar un fons local és matemàticament un operador que atenua les freqüències baixes: no s'ha de vendre com una sortida que conserva totes les escales. No s'ha afegit cap filtre clàssic a les capes científiques de V31.

**Identitat que evita una falsa novetat:** `log r` és harmònica fora del centre solar. En el model continu, amb suport circular complet que no conté el centre, la mitjana local radial de `log r` coincideix amb el valor central. Per això LR es redueix a una mitjana local de `log I` en aquell interior; la seva diferència útil apareix en suports incomplets. A la discretització provada, LR i la mitjana coincideixen aproximadament a 10⁻¹⁴ als cinc cores reals amb suport complet. El sisè, pentagon_NE, conté 5.493 píxels amb veïnat parcial i una diferència de correlació de fins a 1,01·10⁻⁵. No són dos descobriments independents.

El marc és regressió polinòmica local coneguda; aquí s'han fet una implementació i proves específiques per aquesta corona, sense afirmar prioritat matemàtica. Referència primària: [Zhang i Chan, regressió polinòmica local multivariant](https://link.springer.com/article/10.1007/s11265-010-0495-4).

## 3. Nuls, transferència i contraproves

Escena sintètica 1280², centre solar subpíxel `(639,37; 639,63)`, radi 100 px, disc físic, cobertura diagonal incompleta i forat rectangular. Suports `h=96/160 px`. L'interior comú es defineix per distància a **totes** les dades absents i al límit del llenç superior a 162 px; la normalització amb dues dependències usa 322 px. La franja de vora també es mesura i es mostra, no s'oculta.

La validació algebraica independent dona PASS: reproducció de polinomis/log-potències, mínims quadrats directes, rotació de 90° i invariància exacta davant canviar valors absents per 0, NaN o 10³⁰. Error màxim de reproducció del test de suport irregular: Q2 `1,86·10⁻¹⁰`, LR `1,67·10⁻¹²`; referència WLS directa ≤`6,67·10⁻¹⁶`. Són proves d'implementació, no una certificació fotogràfica.

| Nul amb h=160 | Q2 | LR |
|---|---:|---:|
| `I∝r^-3`, RMS log a l'interior | 2,13·10⁻¹⁴ | 1,43·10⁻¹⁵ |
| Mateixa potència, RMS log a la vora | 0,02968 | pràcticament zero |
| Potència + pedestal 0,03, RMS log interior | 0,0001115 | 0,01351 |

Q2 falla fort al limbe parcial, i un pedestal additiu trenca l'exactitud del model de potència. Un altre nul suau `r^-2 + 0,4r^-6 + cel2D` deixa RMS interiors `8,61·10⁻⁵` i `0,00540` respectivament. Tots dos superen el criteri experimental `2·10⁻⁵` —1% d'una injecció feble de 0,002 en log—; tampoc no es resol tot traient el cel conegut. No confondre una família analítica exacta amb una corona general.

Transferència Fourier a 45°, suport complet, guany fix 1, sense ajustar-lo per banda:

| Operador | 16 px | 32 px | 64 px | 128 px | 256 px |
|---|---:|---:|---:|---:|---:|
| Q2 h96 | 0,99992 | 0,99731 | 0,79906 | 0,14744 | 0,01225 |
| LR h96 | 0,99997 | 0,99901 | 0,96708 | 0,54919 | 0,17662 |
| Q2 h160 | 0,999994 | 0,999794 | 0,990917 | 0,590339 | 0,07983 |
| LR h160 | 0,999998 | 0,999922 | 0,997278 | 0,903283 | 0,42174 |

La franja de preservació és 0,90–1,10. Q2 h160 conserva les ones de 16–64 px a l'interior provat, però perd aproximadament el 41% d'amplitud a 128 px. LR arriba a 128 px en aquest interior, amb les limitacions descrites.

La prova adversària afegeix 3 orientacions × 3 fases × 14 zones. Exigeix simultàniament guany 0,90–1,10, quadratura ≤0,05 i RMS inexplicat relatiu ≤0,10. Incloent vores i limbe, Q2 passa 123/126, 122/126, 110/126 i 0/126 casos a 16/32/64/128 px; LR 126/126, 123/126, 114/126 i 54/126. **Cap operador té PASS general a tot el llenç.**

La normalització separada `D/sqrt(W(D²)+0,002²)`, calibrada analíticament amb factor global 0,002 per tenir pendent unitat al residual zero, atenua fortament les petites injeccions en una escena estructurada. El terra 0,002 és experimental, no soroll de sensor mesurat. Aquest efecte contextual impedeix interpretar el contrast visual com amplitud preservada. El mètode MGN també usa normalitzacions locals multiescala, però aquesta ablació no es presenta com una reproducció de tot MGN: [Morgan i Druckmüller 2014](https://arxiv.org/abs/1403.6613).

## 4. Acoblament anular i arcs reals

Una pertorbació compacta de radi 20 px i pic 0,1 en log deixa canvi màxim llunyà inferior a `1,3·10⁻¹⁶` als operadors locals fora de `h+20`. En canvi, el mateix canvi altera el costat oposat en NRGF, també quan els seus perfils s'interpolen: RMS aproximat 0,038 en les seves unitats, o 0,00053 després d'una calibració analítica fixa a unitats log. La interpolació redueix salts de discretització, però no elimina aquesta dependència de tot l'anell.

Aquest control prova un mecanisme, no que tots els arcs observats siguin NRGF. Si una ondulació radial de període 32 px ja és a l'entrada, els models locals la transmeten prop de la unitat. La mateixa forma pot representar corona real o un error: un filtre que només veu aquella imatge rep exactament les mateixes dades en tots dos casos. Cal informació addicional per distingir-los; la forma circular sola no basta.

Les injeccions d'arcs locals coneguts revelen un altre cost que les sinusoides no exposen prou. Per amplituds de forma fixada i amplades radials σ=4/12/24/48 px, Q2 h160 conserva guanys aproximats `0,832/0,546/0,298/0,158`; LR `0,912/0,752/0,581/0,425`. També apareixen halos negatius. Conservar una banda Fourier no equival a conservar la forma i el flux d'un arc aïllat.

**Extensió robusta:** després del primer ajust Q2, pesos suaus `w=1/sqrt(1+(D/0,002)²)` i una sola reestimació. És un refit a partir d'un residual pilot, no IRLS exacte per cada consulta ni una probabilitat de certesa física. La dependència passa a 2h. Es recalculen pesos en cada injecció positiva/negativa; també es mesuren resposta central, distorsió parella i halo fora de l'arc sobre tot el suport vàlid.

En una geometria reservada i 18 casos per signe —σ=4/12/24; pics 0,0002/0,002/0,02; soroll 0/0,001— només **1/18 arcs positius** supera conjuntament guany, forma i halo. El cas estret i fort sense soroll arriba a guany 0,938, error de forma 0,084 i halo 0,0345. Amb soroll, guany 0,926 però error 0,100399: **FAIL literal**, sense arrodonir-lo a PASS. Els arcs forts amb σ12/24 i soroll queden a 0,723/0,476. Els febles tampoc es conserven prou. Aquesta extensió ajuda una classe limitada; no és la solució universal.

## 5. Pilot real: Sony sola i jutge Vixen fix

Fonts anteriors immutables: `v29/cau_final/sony_corrected_total.npy`, `vixen_total.npy`, màscares Sony/Vixen; font Sony amb offsets corregits: `v29_c03_fix/sony_corrected_G.npy`. Canal G, sense nova calibració RAW. Centre solar `(5361,7681;3775,7475)`, radi 440,6030 px.

Sis finestres d'entrada 1024² amb core 512²: NE3,5R `(5890,2326)`, S3,5R `(5089,5294)`, NE4R `(5965,2120)`, S4R `(5056,5511)`, pentàgon NE `(6198,3638)` i pentàgon Sony `(6376,4342)`. Els marges de 256 px cobreixen el suport Q2/LR 160 i la dependència MGN 240. **Cap entrada fusionada amb Vixen.** No s'ajusta localment el candidat contra el jutge. Una escala escalar d'intensitat desapareix en aquests residuals log.

Anàlisi comuna: detrend quadràtic, finestra Tukey 0,25, bandes FFT exactes 4–8/8–16/16–32/32–64/64–128/128–256 px. Nul: Vixen girada localment 180°. Les bandes més amples només contenen 2–4 cicles; no es dona significança estadística ni es tracta cada píxel com independent.

Les 48 injeccions sobre Sony real confirmen els guanys interiors: Q2 passa 16/32/64 i falla 128 en les sis finestres; LR passa les quatre escales. Però la correlació real de 4–32 px a les quatre zones exteriors va aproximadament de −0,062 a 0,030: no acredita detall coronal fi.

Hi ha millores locals i regressions: al pentàgon Sony, banda 64–128, Q2 correlaciona 0,594 amb Vixen davant 0,523 de MGN, mentre LR/mitjana arriba a 0,689. A NE3,5R, 128–256, Q2 queda a 0,223 davant 0,412 de MGN i 0,888 de l'entrada log. Les correccions d'offset existents ajuden algunes zones NE i no totes les zones S. No hi ha superioritat global ni prova que cada textura sigui solar.

S'han inspeccionat el context de tot el llenç i les sis plaques natives, amb display fix `gris=0,5+32D`, sense estirar cada ROI per separat. És una vista exigent de diagnosi: retalla valors de pantalla als streamers intensos; els NPY float32 conserven la sortida. Les imatges mostren textura fina compatible amb soroll dominant a l'exterior i pèrdua/halos al voltant d'estructures amples. Les correlacions baixes no mesuren directament la fracció de soroll ni exclouen diferències de resolució. No són un retoc fotogràfic final.

**Rectificació d'una conclusió anterior:** el jutge de `v31_purs/qa_science.py` comprova cores Sony, però alguns marges de filtratge poden arribar a píxels fusionats amb Vixen. Per a les quatre ROIs exteriors, l'empremta MGN més anàlisi de ±560 px conté respectivament 152.320 / 152.028 / 16.197 / 0 píxels amb pes Vixen positiu; NAFE més anàlisi (±352 px), 7.027 / 169 als dos primers. Són dependències potencials, no amplitud mesurada de contaminació. La independència de totes les correlacions anteriors no quedava demostrada. Es conserva el rebut original i s'afegeix rectificació a research/142. El nou pilot Sony-only resol aquesta dependència d'entrada en el seu abast limitat i no valida retroactivament tota V31.

## 6. Actuar abans del filtre: fons additiu per fotograma

Prova addicional, sobre mostres existents separades 24 px: corregir cada fotograma amb `b_i(x,y)=c_i+a_i·u+d_i·v`. A les coincidències observades s'ajusta

`(I_i−I_j)+(b_i−b_j) ≈ 0`.

La corona comuna es cancel·la amb suport i disseny fixos. És una via causal per mesurar desacords espacials entre exposicions, sense declarar que un arc és fals. No resol el fons absolut: fixar una àncora deixa indeterminat qualsevol pla compartit amb aquesta.

Guanys i pesos RAW congelats. Canal G, grups d'apuntament A/B, àncores DSC06984/DSC06996. Confiança >0,995 en ambdós fotogrames, quocient d'exposicions ≤8, fins a 400 mostres deterministes per parella. Entrenament en sectors alterns de 22,5° entre 1,08–4,5R, amb marges angulars; validació en els altres sectors i extrapolació 4,5–8,5R separada. Ajust robust `soft_l1`, mateixa mostra per comparar constant/pla. Rang complet; condicionament de columnes normalitzades 2,739/2,435. DSC06980 i DSC07001 queden desconnectats: els zeros dels seus coeficients són placeholders, no mesures.

| Grup / validació | RMS relatiu: constant | Pla 2D | Parelles que milloren |
|---|---:|---:|---:|
| A, sectors reservats | 2,1154% | 2,1129% | 7/11 |
| A, exterior | 2,1692% | 2,0715% | 7/9 |
| B, sectors reservats | 2,3293% | 2,2816% | 16/26 |
| B, exterior | 1,8995% | 1,8489% | 11/16 |

La taula dona medianes per parella, no un error de tota la fotografia. Les medianes dels quocients aparellats pla/constant són 0,99749/0,95498 per A i 0,99661/0,96613 per B, interior/exterior. Benefici interior molt modest. B6993–6999 exterior millora 1,4844%→0,7849%; B6991–6993 empitjora 1,5509%→1,7408%. El biaix absolut mediana B també empitjora lleument.

El model no s'ha projectat a la imatge nativa ni contrastat després amb Vixen. El registre, la PSF, el guany i la selecció de saturació poden influir els ajustos; la invariància a corona comuna assumeix aquests elements fixos. Les mostres a 24 px serveixen per fotometria ampla, no per certificar arcs fins. **No es promou aquest pla al PSB.**

## 7. Conclusió de recerca i següent hipòtesi

El component aprofitable és una normalització local sense bins ni dependència de l'anell complet, amb la seva banda de transferència explícita. Encara no hi ha un candidat que superi nul general, vora, arcs febles/amples i jutge real simultàniament. La regularització/robustesa del fons ha de protegir millor les estructures i tenir paràmetres vinculats a incertesa real, no al contrast desitjat.

La següent prova causal justificada seria demostrar que els desacords entre exposicions produeixen les marques del compost: reconstrucció nativa controlada amb una sola variable canviada, injeccions comunes abans de fusionar, sectors/exposicions reservats i Vixen fix. Només si hi ha millora independent i preservació de detall es justificaria adoptar una correcció. El pedestal/gradient compartit requereix informació addicional o un model físic identificable; augmentar el grau del polinomi no l'identifica per si sol.

Aquest estudi acota una via viable i descarta dreceres concretes. No demostra impossibilitat d'una solució futura amb els RAW i els dos trens. Tampoc converteix un nul sintètic perfecte en evidència que s'han eliminat els cercles de Pere.

## 8. Reproducció, rebuts i inspecció

Scripts: [gramofon_2d_20260906](</Users/USUARI/Downloads/Eclipse 2026/research/tools/gramofon_2d_20260906>). Sortides via `comu.Run.vista/lliurable/rebut`: [output](</Users/USUARI/Downloads/Eclipse 2026/output/gramofon_2d_20260906>). Les rutes de font, versions de biblioteques i hashes són al manifest final.

Des de l'arrel canònica, amb SERIAL_WRITES adquirit per a una nova execució:

```sh
export MPLCONFIGDIR=/private/tmp/gramofon_mpl
export OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 OMP_NUM_THREADS=1
export PYTHONDONTWRITEBYTECODE=1
/Users/USUARI/.venvs/eines-ia-py312/bin/python research/tools/gramofon_2d_20260906/qa_core.py
/Users/USUARI/.venvs/eines-ia-py312/bin/python research/tools/gramofon_2d_20260906/experiment.py
/Users/USUARI/.venvs/eines-ia-py312/bin/python research/tools/gramofon_2d_20260906/qa_adversarial.py
/Users/USUARI/.venvs/eines-ia-py312/bin/python research/tools/gramofon_2d_20260906/robust_study.py
/Users/USUARI/.venvs/eines-ia-py312/bin/python research/tools/gramofon_2d_20260906/real_pilot.py
/Users/USUARI/.venvs/eines-ia-py312/bin/python research/tools/gramofon_2d_20260906/source_planes.py
```

Els scripts reescriuen els seus rebuts/vistes i els NPY propis de `native_pilots`; `close_research.py` també genera la guia i el manifest. Conservar el manifest d'aquesta execució abans de repetir. L'estudi usa float64 intern; els cores guardats són float32. No crea un run RAW immutable ni canvia cap PSB.

Rebuts finals: `core_validation.json`, `synthetic.json`, `adversarial.json`, `robust_arcs.json`, `real_pilot.json`, `source_planes.json` i `previous_judge_scope.json` (reproduïble amb `audit_judge_scope.py`). Es conserven tres rebuts **SUPERSEDED** sense valor probatori final: interior que no descomptava tots els forats/vores, prova robusta només central, i un Jacobian que SciPy podia modificar in-place. Els defectes s'han corregit i les proves afectades repetit.

Revisió paral·lela només de lectura: Halley, àlgebra/model i ajustos de font; Raman, geometria/dependències del jutge i criteris de preservació. Autor únic dels canvis: Codex root. La V31 continua com a producte comparatiu anterior amb les seves limitacions.
