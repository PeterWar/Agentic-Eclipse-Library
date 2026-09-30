# Pipeline Druckmüller reconstruït

## Conclusió

La cadena acreditada a les pàgines de resultats de 2024 és:

```text
RAW
→ dark/flat
→ PhaseCorr
→ LDIC 6.0
→ Corona 6.0
→ ACC 6.1
```

No és possible reproduir-la bit a bit:

- `PhaseCorr 6`, `LDIC 6`, `Corona 6` i `ACC 6.1` no són oberts;
- la literatura permet reconstruir els principis;
- IPC, MGN, NRGF i FNRGF tenen implementacions obertes;
- ACHF i una fusió inspirada en LDIC són implementables, però no s'han d'etiquetar com el programari privat.

La informació feble existeix al resultat perquè ja existia en un màster net, redundant, lineal i ben registrat. Un filtre agressiu no pot crear SNR ni recuperar píxels saturats.

## 1. Captura

La font més completa del flux de treball és la tesi de Hana Druckmüllerová, [*Application of Adaptive Filters in Processing of Solar Corona Images*](https://www.vut.cz/www_base/zav_prace_soubor_verejne.php?file_id=81241).

### Principis

- RAW.
- Assaig complet de focus i temps.
- Netejar el sensor abans; desactivar la neteja automàtica fins després dels flats.
- Mateix ISO, obertura, focus i geometria entre llums i calibracions.
- Passos d'exposició d'1 EV o menys.
- Començar prou curt per preservar cromosfera i prominències.
- Arribar prou llarg perquè la corona exterior tingui SNR, però sense que la saturació central toqui la vora.
- Més repeticions en exposicions llargues.
- Escales curtes repetides.
- Diverses focals i sistemes redundants.

### Resultats 2024 publicats

| Lloc/sistema | Càmera i òptica | Frames | Exposicions | Programari declarat |
|---|---|---:|---|---|
| Sims WL | Nikon D810 + Nikkor 300/2,8 | 487 | 1/250–1 s | dark/flat, PhaseCorr, LDIC, Corona, ACC |
| Durango | Nikon Z6 + 80–400 a 400/5,6 | 139 | 1/400–3 s | pipeline equivalent |
| Canatlán | Nikon D810 + 200/2 | 120 | 1/250–1 s | només ~66 s clars |

Fonts:

- [Sims 300 mm](http://www.zam.fme.vutbr.cz/~druck/Eclipse/Ecl2024u/Sims/WL-300mm/0-info.htm)
- [Durango 400 mm](http://www.zam.fme.vutbr.cz/~druck/Eclipse/Ecl2024u/Durango/TSE_2024_400mm_md/0-info.htm)
- [Canatlán 200 mm](http://www.zam.fme.vutbr.cz/~druck/Eclipse/Ecl2024u/Canatlan/TSE_2024_200mm_Canatlan/0-info.htm)

El nombre de frames no és un ornament: permet apilar, rebutjar, cobrir núvols, reduir soroll i repetir escales temporalment compactes.

## 2. Model del detector i linealitat

Model publicat:

\[
s(x,y)=B(x,y)+tD(x,y)+tG(x,y)I(x,y)+R(x,y)
\]

on:

- \(B\): bias o offset;
- \(D\): corrent fosc;
- \(G\): guany relatiu, vinyetatge i pols;
- \(I\): flux incident;
- \(R\): soroll;
- \(t\): temps.

### No assumir que RAW és perfectament lineal

El treball de 2023 va caracteritzar detectors amb:

- font de tungstè estabilitzada;
- llum col·limada;
- temps d'exposició variables;
- ajust per mínims quadrats.

Una ASI1600 mostrava desviacions de l'ordre del 30% al llarg del rang. La correcció es va aplicar a:

- flats;
- imatges d'eclipsi;
- calibratge fotomètric;

abans de fer combinacions o restes.

Per a les Sony cal mesurar per ISO i mode:

- black level;
- relació senyal/temps;
- inici de compressió d'altes llums;
- clipping real per canal Bayer;
- RAW comprimit/no comprimit;
- estabilitat tèrmica;
- possibles canvis de guany.

El 85% del rang que apareix a la tesi és un exemple de llindar conservador, no un valor universal.

## 3. Bias, dark i flat

### Bias mestre

\[
\widetilde B(x,y)=\frac{1}{N}\sum_i b_i(x,y)
\]

### Dark mestre

Per darks de durada \(t_0\):

\[
\widetilde D'(x,y)=\frac1M\sum_i d_i(x,y)-\widetilde B(x,y)
\]

Escalat a \(t_1\):

\[
\widetilde D_M(x,y)=\widetilde B(x,y)+\frac{t_1}{t_0}\widetilde D'(x,y)
\]

Escalar darks pressuposa proporcionalitat amb el temps. Si la càmera introdueix processament o patrons dependents de l'exposició, és preferible disposar de darks per als temps exactes.

### Flat mestre

\[
\widetilde F_M(x,y)=\frac1K\sum_i[f_i(x,y)-D_M^F(x,y)]
\]

En un Bayer, la tesi normalitza separadament R, G i B:

\[
F_M^N(x,y)=\widetilde F_M(x,y)\frac{V}{V_c},
\quad c\in\{R,G,B\}
\]

Això evita que l'espectre del cel/difusor imposi un balanç de blancs fals.

La dada calibrada és:

\[
C(x,y)=
\frac{\overline F}{F_M(x,y)}
\left[s(x,y)-D_M(x,y)\right]
\]

Per estimar flux, caldria dividir també per temps i sensibilitat.

### Protocol de flats 2023

- cel blau net prop del zenit;
- lluny del Sol;
- difusor blanc translúcid;
- sis orientacions, rotant 60°;
- mateix focus, obertura i ISO;
- cap neteja o moviment del sensor entre eclipse i flat.

Els darks es van obtenir immediatament després de totalitat repetint les mateixes seqüències amb òptica tapada i coberta.

### Combinació robusta

- mitjana: eficient per soroll gaussià, sensible a outliers;
- mediana: robusta, menys eficient;
- mean-median: descarta valors més lluny de \(\kappa\sigma\), típicament \(\kappa=1,5\) o 2;
- sigma-clipping iteratiu.

## 4. Calibratge abans de demosaic

El calibratge s'ha de fer al mosaic CFA perquè:

- pols;
- vinyetatge;
- hot pixels;
- offset;
- guany per fotosite;

existeixen abans que la interpolació RGB.

Després cal demosaicar abans de:

- desplaçament subpíxel;
- rotació;
- canvi d'escala.

La tesi descriu demosaic bilineal com a explicació. No és prova que el programari actual D3F2 faci exactament això.

### Color

Druckmüller no equilibra necessàriament els canals al principi:

- multiplicar un canal feble n'amplifica també el soroll;
- el registre i la fusió poden conservar la resposta relativa original;
- el color perceptiu pertany a una etapa posterior.

Conseqüència:

- la A7RIIIA i la A7III modificada han de tenir perfils separats;
- no s'han de fusionar els seus RGB com si fossin el mateix instrument;
- el balanç de blancs només són guanys; no desfà la resposta espectral addicional.

## 5. Registre per correlació de fase

Font: [Druckmüller, *Phase Correlation Method for the Alignment of Total Solar Eclipse Images*](https://doi.org/10.1088/0004-637X/706/2/1605).

### Translació

\[
P_{1,2}=
\mathcal F^{-1}
\left\{
\frac{F_1F_2^*}{|F_1F_2|}
\right\}
\]

Una translació produeix un pic a la translació oposada.

Forma estabilitzada:

\[
P=
\mathcal F^{-1}
\left\{
H(\xi,\eta)
\frac{F_1F_2^*}
{(|F_1|+p)(|F_2|+q)}
\right\}
\]

amb \(H\) real i parell, i \(p,q>0\).

### Rotació i escala

- el mòdul espectral elimina la translació;
- en coordenades polars, la rotació és translació angular;
- en log-polar, l'escala \(\alpha\) és translació \(\ln\alpha\);
- estimades rotació i escala, es calcula X/Y.

S'usa \(\log(1+|F|)\) per reduir rang dinàmic i una finestra Hann o gaussiana per evitar discontinuïtats de la DFT.

### Subpíxel

\[
(\bar x,\bar y)=
\left(\frac{M_{10}}{M_{00}},\frac{M_{01}}{M_{00}}\right)
\]

El centroide es calcula al voltant del pic, sovint dins un radi de 3–8 píxels, i s'itera.

### Adaptacions d'eclipsi

Les vores més fortes són mals referents:

- la Lluna es mou;
- la frontera saturada canvia amb exposició;
- pols i defectes són fixos al sensor.

Procediment:

1. emmascarar Lluna;
2. emmascarar saturació i vora exterior;
3. aplicar passa-alt tangencial;
4. usar finestra circular o rectangular segons l'anell útil;
5. començar en una exposició intermèdia ben definida;
6. registrar progressivament exposicions veïnes;
7. construir un nou màster mitjà quan millori el pic;
8. filtrar prou per no registrar pols.

Passa-alt tangencial:

\[
T_\zeta f(r,\phi)=f(r,\phi)-
\frac{1}{\zeta\sqrt{2\pi}}
\int_{-3\zeta}^{3\zeta}
f\left(r,\phi+\frac l r\right)
e^{-l^2/(2\zeta^2)}\,dl
\]

\(\zeta\approx8\) és només un exemple per imatges nítides.

### IPC obert

Continuació moderna:

- [paper IPC](https://doi.org/10.3847/1538-4365/ab63d7)
- [repositori IPC](https://github.com/zdenyhraz/IPC)
- [implementació actual `shenanigans`](https://github.com/zdenyhraz/shenanigans)

Permet rotació, escala i translació, amb:

- Hann;
- band-pass;
- sobremostreig;
- refinament iteratiu;
- subpíxel.

És una base oberta excel·lent. No prova que sigui exactament PhaseCorr 6.

### QA de registre

- referència en R+B i imatge transformada en G;
- una alineació correcta és neutra;
- vores de color indiquen residu;
- guardar altura, amplada i unicitat del pic;
- guardar la transformació completa;
- revisar per canal per detectar aberració cromàtica.

## 6. Fusió HDR científica: LDIC

Forma publicada:

\[
g(r,\phi)=
\sum_{i=0}^{N-1}
w(f_i(r,\phi))
\left[k_i(\phi)f_i(r,\phi)+q_i(\phi)\right]
\]

### Pes

\(w\):

- zero al terra de soroll;
- creix cap al tram útil;
- manté pes al tram lineal;
- cau abans de la no-linealitat i saturació;
- usa transicions suaus.

El màster no ha de rebre:

- ombres sense SNR;
- highlights comprimits;
- píxels saturats;
- artefactes.

### Adaptació angular

La tesi descriu:

- 60 sectors angulars;
- regressió lineal de cada nova imatge contra la composició;
- coeficients \(k_i\) i \(q_i\);
- aproximació amb polinomis trigonomètrics d'ordre baix: 0, 1, 2 o 4;
- incorporació successiva.

Això pot compensar:

- núvol prim;
- llum difusa;
- flare;
- gradient angular;
- diferències abans/després del centre de totalitat.

### Què no s'ha publicat

- llindars exactes de pes;
- normalització interna;
- criteris de rebuig;
- tractament complet de color;
- moviment lunar/Earthshine;
- canvis de LDIC original a LDIC 6.

Una implementació oberta prudent seria:

\[
H=\frac{\sum_i w_iL_i}{\sum_iw_i}
\]

amb regressió sectorial robusta i mapes de:

- \(\sum w_i\);
- nombre efectiu de frames;
- font dominant;
- residus.

S'ha d'anomenar «fusió inspirada en LDIC», no LDIC 6.

## 7. Moviment de la Lluna i Earthshine

Model lineal:

\[
h_x(t)=h_{x,0}+t\,h_{dx}
\]

\[
h_y(t)=h_{y,0}+t\,h_{dy}
\]

Cal mesurar almenys:

- una presa curta després de C2;
- una presa curta abans de C3;
- centre i radi lunar;
- velocitat respecte de la corona.

Hi ha dos sistemes de coordenades:

- solar/coronal;
- lunar/Earthshine.

Solució auditable:

1. màster coronal en coordenades solars;
2. stack Earthshine en coordenades lunars;
3. instant de referència declarat;
4. màscara explícita;
5. conservar tots dos màsters.

Clonar una Lluna nítida dins l'HDR sense conservar els originals elimina traçabilitat.

## 8. ACHF i Corona

L'ACHF és l'avantpassat matemàtic de Corona.

Un kernel segur ha de tenir:

- fase quasi zero;
- resposta d'amplitud monotònica;
- simetria a alta freqüència;
- cap barreja entre Lluna i corona.

Kernel gaussià heliocèntric:

\[
C_{r,\phi}(\rho,\varphi)=
\exp\left[
-\frac{(r-\rho)^2+
\left(r(\phi-\varphi)\right)^2}
{2\sigma^2}
\right]
\]

Passa-alt:

\[
g=f-\operatorname{mitjana\ gaussiana\ local}
\]

Combinació:

\[
h=K_1f+K_2g
\]

La tesi dona \(\sigma\) entre aproximadament 0,5 i 64 píxels com a rang útil. Corona combina múltiples escales i passos no publicats.

### Avantatge sobre radial blur

Un filtre tangencial/radial clàssic:

- potencia raigs;
- pot perdre cims de loops tangencials;
- té resposta no monotònica;
- pot introduir ringing.

ACHF:

- és no direccional;
- redueix halos;
- conserva estructures radials i tangencials;
- separa la màscara lunar.

La tesi considera ACHF/Corona especialment adequat per a llum blanca d'alt SNR.

## 9. NRGF

\[
g(r,\phi)=
\frac{f(r,\phi)-E(r)}{S(r)}
\]

on \(E(r)\) i \(S(r)\) són la mitjana i desviació de l'anell complet.

Avantatges:

- automàtic;
- elimina gradient radial;
- fa visible l'estructura exterior.

Limitacions:

- tots els angles d'un radi comparteixen transformació;
- una regió sorollosa afecta l'anell;
- no conserva fotometria.

Implementació: [`sunkit_image.radial.nrgf`](https://docs.sunpy.org/projects/sunkit-image/en/stable/api/sunkit_image.radial.nrgf.html).

## 10. FNRGF

Procediment:

1. anells heliocèntrics complets;
2. divisió en \(n_s\) sectors;
3. mitjana \(E_s(r)\) i desviació \(S_s(r)\);
4. sèries trigonomètriques d'ordre \(\omega\);
5. atenuació amb seqüències \(A_k,C_k\);
6. normalització;
7. barreja amb original.

\[
g(r,\phi)=
\frac{f(r,\phi)-F_E(r,\phi)}
{F_S(r,\phi)}
\]

\[
h=K_1f+K_2g
\]

Condició:

\[
n_s\ge 2\omega+1
\]

Punt inicial conservador publicat:

- \(\omega=30\);
- \(A_k\) decreixent 0,05;
- \(C_k\) decreixent 0,1.

No són paràmetres universals.

### Soroll

Evitar un denominador massa petit:

\[
S_s^\prime(r)=\sqrt{S_s^2(r)+V_n}
\]

La tesi suggereix començar amb una desviació artificial de l'ordre del 10–15% del soroll exterior estimat.

Artefactes:

- anells de disc de gramòfon;
- falsos glimmers;
- soroll exagerat;
- contaminació angular per hot pixels o prominències.

Implementació: [`sunkit_image.radial.fnrgf`](https://docs.sunpy.org/projects/sunkit-image/en/stable/api/sunkit_image.radial.fnrgf.html).

## 11. NAFE i NAFE-VN

NAFE està especialment orientat a EUV i disc solar.

Equalització local:

\[
h_{x,y}(t)=
\sum_{i,j}C(i,j)\,
\delta(t,f(x+i,y+j))
\]

Funció acumulada local \(L_{x,y}(t)\):

\[
g_{x,y}(t)=g_0+(g_1-g_0)L_{x,y}(t)
\]

Es difumina en intensitat amb una gaussiana \(\sigma\) per no amplificar soroll.

NAFE-VN exclou veïns probablement pertanyents a una altra regió:

\[
\Delta_\varepsilon=
\begin{cases}
1,& |t-f(x+i,y+j)|<\varepsilon\\
0,& \text{altrament}
\end{cases}
\]

Fonts:

- [NAFE](https://doi.org/10.1088/0067-0049/207/2/25)
- [NAFE-VN](https://doi.org/10.1007/978-3-319-07148-0_23)

No és el nucli obligatori de la corona blanca RGB.

## 12. MGN

Per escala \(\sigma_i\):

\[
\mu_i=G_{\sigma_i}*f
\]

\[
s_i=\sqrt{G_{\sigma_i}*(f-\mu_i)^2}
\]

\[
C_i=\frac{f-\mu_i}{s_i}
\]

\[
C_i^\prime=\arctan(kC_i)
\]

Context global:

\[
C_g^\prime=
\left(
\frac{f-f_{\min}}{f_{\max}-f_{\min}}
\right)^{1/\gamma}
\]

Combinació:

\[
M=(1-h)\,\overline{C^\prime}+hC_g^\prime
\]

Punt inicial publicat:

- escales `[1.25, 2.5, 5, 10, 20, 40]`;
- \(k=0,7\);
- \(\gamma=3,2\);
- \(h=0,7\);
- pesos iguals.

Font: [paper MGN](https://arxiv.org/abs/1403.6613) i [implementació SunPy](https://docs.sunpy.org/projects/sunkit-image/en/stable/_modules/sunkit_image/enhance.html).

MGN és una excel·lent línia base oberta. No és Corona 6.

## 13. ACC i acabat

ACC és descrit com **Adaptive Contrast Control — Image Structure and Object Analyzer**.

No hi ha especificació pública suficient de:

- color;
- saturació;
- corbes;
- correccions locals;
- reintegració de prominències;
- cel;
- Earthshine.

Cal tractar-lo com a caixa negra.

Cadena oberta prudent:

1. HDR RGB lineal;
2. luminància realçada separada;
3. crominància d'un HDR normal ben exposat;
4. reintegració en espai de color documentat;
5. final de presentació etiquetat com a no fotomètric.

## 14. Ghosts i defectes òptics

El sistema 2023 mostra el nivell de disciplina:

- filtres inclinats 1,5° per expulsar un ghost del camp;
- ghost òptic modelat amb escala, translació, rotació, ampliació i desenfocament gaussià;
- ajust manual;
- incertesa addicional igual a la brillantor del ghost.

Per a 2026 cal buscar:

- reflexos del filtre solar abans de totalitat;
- ghosts sense filtre durant totalitat;
- halos per sensor modificat;
- flare del 300 mm;
- gradients del cel;
- reflexos de QUADTCC;
- canvis amb enquadrament i obertura.

## 15. Què és obert

| Component | Matemàtica publicada | Codi obert | Rèplica actual exacta |
|---|---:|---:|---:|
| calibratge RAW/Bayer | sí | implementable | D3F2 desconegut |
| PhaseCorr clàssic | sí | implementable | no PhaseCorr 6 |
| IPC | sí | sí, GPL | sí per al repo |
| LDIC | parcial | no | no |
| ACHF | nucli sí | implementable | no Corona 6 |
| NRGF | sí | sí | sí |
| FNRGF | sí | sí | no paràmetres 2024 |
| NAFE/NAFE-VN | sí | no s'ha verificat oficial | no |
| MGN | sí | sí | sí |
| ACC 6.1 | insuficient | no | no |
| Earthshine LDIC | només descrit | no | no |

## 16. Pipeline obert defensable per al projecte

```text
RAW originals immutables
  ↓
caracterització de black level, linealitat i clipping
  ↓
correcció de no-linealitat al CFA
  ↓
bias/dark/flat al CFA
  ↓
demosaic float sense white balance destructiu
  ↓
stack robust de repeticions equivalents
  ↓
luminància de registre + màscares Lluna/saturació
  ↓
IPC / correlació de fase subpíxel
  ↓
transformacions guardades i aplicades a RGB lineal
  ↓
fusió sectorial inspirada en LDIC
  ↓
MÀSTER HDR LINEAL
  ├── mesura
  ├── ACHF obert multiescala
  ├── MGN
  ├── FNRGF/NRGF
  ├── WOW/RHEF
  └── stack lunar/Earthshine separat
           ↓
composició visual i color documentats
```

## 17. Metadades mínimes

Per frame:

- hash;
- cos i número de sèrie;
- òptica, focal i obertura;
- ISO;
- temps nominal i aplicat;
- timestamp subsegon;
- posició dins el bracket;
- RAW/compressió;
- targeta/slot;
- calibratge associat;
- temperatura o proxy;
- focus;
- orientació;
- temps relatiu a C2/C3;
- acceptat/rebutjat i motiu;
- perfil de linealitat;
- black level i clipping;
- transformació;
- qualitat del pic;
- pes HDR.

Per producte:

- llista d'inputs;
- versió de codi;
- paràmetres;
- màscares;
- mapes de pes;
- espai de color;
- transformacions manuals;
- distinció lineal/realçat.

## 18. QA mínim

- residu de registre per canals;
- absència de vores de color;
- pic de fase únic;
- detall present en frames independents;
- detall present en les dues càmeres;
- estabilitat en ACHF/MGN/FNRGF/WOW/RHEF;
- inspecció d'halos, anells i ringing;
- histograma de residus HDR;
- monotonicitat del màster;
- cap clipping no declarat de prominències;
- mapes de diferència;
- detecció de ghosts;
- separació clara entre dada i presentació.

## Resum

El secret pràctic és la disciplina prèvia:

> calibrar abans de realçar, registrar la corona i no la Lluna, fusionar només el tram útil de cada exposició, conservar un màster lineal i exigir que cada detall sobrevisqui a controls independents.
