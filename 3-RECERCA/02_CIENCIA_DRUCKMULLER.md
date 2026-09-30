# La ciència de Druckmüller i els Solar Wind Sherpas

## Veredicte

Miloslav Druckmüller ha convertit la fotografia d'eclipsi en una cadena de mesura científica:

1. disseny experimental;
2. control sincronitzat de múltiples càmeres;
3. caracterització d'òptiques, filtres i sensors;
4. calibratge fotomètric;
5. registre geomètric subpíxel;
6. fusió lineal d'alt rang dinàmic;
7. separació de línia i continu;
8. realçament morfològic;
9. contrast amb satèl·lits, mesures *in situ* i models MHD.

La imatge espectacular que veiem al web és un producte de presentació. La ciència quantitativa es fa amb els màsters lineals calibrats. [Habbal et al., 2011](https://doi.org/10.1088/0004-637X/734/2/120) ho expliciten: ACHF/NRGF perden brillantor absoluta i no són la base de l'anàlisi quantitativa.

## 1. Organització real de l'equip

- **Shadia Habbal:** PI i preguntes de física coronal.
- **Miloslav Druckmüller:** matemàtica, planificació, control, calibratge, registre, fusió i realçament.
- **Hana Druckmüllerová:** correlació de fase, FNRGF, NAFE i modelatge quantitatiu recent.
- **Huw Morgan:** NRGF, FNRGF i MGN.
- **Benjamin Boe:** fotometria absoluta, línies Fe, *freeze-in*, F-corona i topologia.
- **Peter Aniol, Adalbert Ding, Judd Johnson, Pavel Štarha, Jana Hoderová i altres:** instrumentació, mecànica, adquisició i calibratge.
- **Enrico Landi / CHIANTI:** física atòmica.
- **Zoran Mikić, Cooper Downs / Predictive Science:** models MHD.

La [unitat de recerca espacial de VUT](https://math.fme.vutbr.cz/en/space-research) declara cinc eixos: processament, anàlisi, planificació experimental, control de sistemes d'imatge i disseny instrumental.

## 2. Què hi ha en una imatge coronal

### Llum blanca

- **K-corona:** llum fotosfèrica dispersada pels electrons; informa de densitat electrònica.
- **F-corona:** llum dispersada per pols interplanetària; domina progressivament la corona exterior.
- **E-corona:** línies d'emissió d'ions altament ionitzats.
- cel, llum difusa, reflexos, ghosts i resposta instrumental.

Una imatge RGB ampla combina tots aquests components. Pot mostrar la morfologia amb qualitat extraordinària, però no els separa automàticament.

### Línies prohibides

| Línia | Ió | Temperatura de resposta aproximada | Ús principal |
|---|---:|---:|---|
| Fe IX 435,9 nm | Fe⁸⁺ | ~0,6 MK | plasma relativament fred; línia feble |
| Fe X 637,4 nm | Fe⁹⁺ | ~1,0 MK | corona freda i estructura oberta |
| Fe XI 789,2 nm | Fe¹⁰⁺ | 1,2 ± 0,1 MK | línia extensa i vent solar |
| Fe XIII 1074,7 nm | Fe¹²⁺ | ~1,6 MK | plasma intermedi, infraroig |
| Fe XIV 530,3 nm | Fe¹³⁺ | 1,8 ± 0,1 MK | plasma calent i camps tancats |
| Ni XV 670,2 nm | Ni¹⁴⁺ | ~2,5 MK | component més calenta |
| Hα 656,3 nm | H | ~10⁴ K | prominències, no corona calenta |

«Fe XI» significa Fe¹⁰⁺: la numeració espectroscòpica és una unitat superior a la càrrega.

Aquestes temperatures són màxims de fracció iònica en equilibri, no un termòmetre directe de cada píxel.

## 3. Experiment de línia i continu

Cada línia es captura amb dos sistemes simultanis i gairebé idèntics:

- **on-band:** centrat en la línia;
- **off-band:** continu proper, fora de la línia.

La imatge on-band conté:

- línia iònica;
- K-corona;
- F-corona;
- cel i instrument.

L'off-band conté idealment:

- K-corona;
- F-corona;
- cel i instrument;
- no la línia.

La resta calibrada conceptual és:

\[
L_i =
\frac{E_{\rm on}-D_{\rm on}}{F_{\rm on}-Q_{\rm on}}
-
w
\frac{E_{\rm off}-D_{\rm off}}{F_{\rm off}-Q_{\rm off}}
\]

on \(w\) corregeix transmissió i diferències espectrals entre el continu solar, la F-corona i la font dels flats.

No és una simple resta de Photoshop. Necessita:

- simultaneïtat;
- linealitat;
- darks i flats;
- registre subpíxel;
- transmissió de filtres;
- temperatura dels filtres;
- color del continu;
- calibratge fotomètric.

### Exemple de 2010

L'experiment va usar:

- llum blanca amb Canon EOS 5D i Ritchey-Chrétien 203/1624 mm;
- 89 imatges entre 1/500 i 2 s, 61 seleccionades;
- aproximadament 1″/px;
- control MultiCan/MaD 2.0;
- Hα, Fe IX, Fe X, Fe XI, Fe XIII, Fe XIV i Ni XV;
- parell on/off de càmeres per línia;
- filtres de 0,5 nm FWHM estabilitzats prop de 45 °C;
- off-band aproximadament 1,1 nm cap al blau.

La simultaneïtat evita confondre:

- núvol amb senyal espectral;
- evolució temporal amb diferència de banda;
- moviment amb línia;
- canvi de filtre amb més de la meitat de totalitat perduda.

### Evolució de 2023

El sistema australià va incorporar:

- Nikon Z6 II a 1000 mm;
- Nikon D810 a 200 mm;
- parells Zeiss 300/4 on/off;
- ASI1600MM per Fe X i Fe XIV;
- ASI294MM per Fe XI;
- filtres Alluxa d'1–1,5 nm;
- off-band aproximadament 7 nm al blau;
- calibratge del disc solar amb filtre ND;
- validació contra LASCO-C2.

Troballes instrumentals molt útils:

- una ASI1600 variava fins aproximadament un 30% al llarg del rang digital;
- l'ASI294 va mostrar interferència tipus étalon no observada al laboratori;
- es van haver de modelar ghosts;
- la no-linealitat es va corregir abans de flat, apilat i resta espectral.

Font: [eclipsi australià 2023, ApJ 997:171](https://arxiv.org/abs/2512.01068).

## 4. Temperatura, excitació i *freeze-in*

Cal distingir:

- **temperatura electrònica \(T_e\):** inferida de proporcions de línies sota models de física atòmica;
- **temperatura iònica efectiva \(T_{\rm eff}\):** amplada Doppler, que inclou temperatura cinètica i moviments no tèrmics;
- **temperatura de formació:** màxim d'abundància d'un estat de càrrega en equilibri.

Dependències aproximades:

\[
I_{\rm coll}\propto n_e n_i
\]

\[
I_{\rm rad}\propto n_i
\]

\[
I_K\propto n_e
\]

A baixa altura domina l'excitació colisional. Més amunt, l'excitació radiativa i la proporció línia/continu permeten inferir abundància relativa de l'ió. Quan ionització i recombinació són més lentes que l'expansió, l'estat de càrrega queda «congelat».

No s'ha de confondre:

- \(R_t\): transició entre excitació colisional i radiativa;
- \(R_f\): radi físic de *freeze-in*.

El treball de 2018 va inferir \(R_f\) empíric per Fe¹⁰⁺ i Fe¹³⁺, amb valors dependents de forats coronals i regions obertes de streamers. [Paper](https://arxiv.org/abs/1805.03211).

Per sobre del *freeze-in*, la proporció de línies pot conservar la història tèrmica de més avall; no és necessàriament la temperatura electrònica local actual.

## 5. Contribucions científiques

### 2005–2010: de la imatge a la termodinàmica

- mètode HDR/ACHF;
- classificació física de raigs, plomes, helmet streamers i pseudostreamers;
- propagació d'un abrillantament de ploma polar;
- registre de fase generalitzat;
- mapes 2D de temperatura i estats de càrrega;
- connexió amb ACE/Ulysses;
- cavitats de prominències reinterpretades com embolcalls magnètics amb plasma calent.

Fonts:

- [mètode 2006](https://www.ta3.sk/caosp/Eedition/FullTexts/vol36no3/pp131-148.pdf)
- [PhaseCorr 2009](https://doi.org/10.1088/0004-637X/706/2/1605)
- [mapes de temperatura](https://doi.org/10.1088/0004-637X/708/2/1650)
- [hot prominence shrouds](https://doi.org/10.1088/0004-637X/719/2/1362)

### 2011–2014: línies múltiples i filtres adaptatius

- set línies simultànies;
- discriminació tèrmica d'uns 0,2 MK;
- comparació Fe X visible amb Proba2/SWAP;
- FNRGF;
- NAFE i MGN;
- anells de vòrtex, arcs encaixats, bombolles i estructures helicoïdals;
- connexió prominència–corona i expulsió d'helicitat;
- seguiment del cometa ISON dins la corona.

Fonts:

- [Thermodynamics of the Solar Corona and Evolution of the Solar Magnetic Field](https://doi.org/10.1088/0004-637X/734/2/120)
- [new class of coronal structures](https://doi.org/10.1088/0004-637X/785/1/14)
- [prominence–corona connection](https://doi.org/10.1088/0004-637X/793/2/119)
- [ISON](https://doi.org/10.1088/2041-8205/784/2/L22)

### 2017–2022: CMEs, camp i corona exterior

- fronts de xoc i petjades persistents de CMEs;
- sistemes prominència–CME «tethered»;
- primer *freeze-in* empíric;
- eclipsis com a banc de prova de models MHD;
- termodinàmica de CME amb tres llocs el 2017;
- orientació coronal de 14 eclipsis entre 1 i 6 R☉;
- IPC obert;
- separació cromàtica K/F;
- relació Fe XI/Fe XIV amb vent solar mesurat per ACE;
- brillantor absoluta de Fe X, XI i XIV fins a 3,4 R☉.

Fonts:

- [CME dynamics](https://doi.org/10.3847/1538-4357/aa8cd2)
- [tethered systems](https://doi.org/10.3847/2041-8213/aa9ed5)
- [freeze-in](https://doi.org/10.3847/1538-4357/aabfb7)
- [models MHD i eclipsi](https://doi.org/10.1038/s41550-018-0562-5)
- [CME thermodynamics](https://arxiv.org/abs/1911.11222)
- [magnetic topology](https://arxiv.org/abs/2004.08970)
- [F-corona](https://arxiv.org/abs/2103.02113)
- [solar-wind sources](https://arxiv.org/abs/2103.02128)
- [absolute Fe brightness](https://arxiv.org/abs/2206.10106)

### 2024–2026: dinàmica, turbulència i corona mitjana

- separació de fons i component dinàmica en EUV;
- escala d'injecció turbulenta d'aproximadament 1,5 Mm, associada inferencialment a granulació;
- línies Fe X, XI i XIV quantitatives de 1,03 a 6 R☉;
- primeres proporcions espacialment resoltes a la corona mitjana, segons els autors;
- comparació de set eclipsis amb WISPR/Parker Solar Probe;
- model de l'espectre K-coronal de Hana per inferir temperatura electrònica i, potencialment, sortida del plasma.

Fonts:

- [processament dinàmic EUV, 2024](https://doi.org/10.3847/1538-4365/ad8633)
- [escala turbulenta, 2025](https://arxiv.org/abs/2501.00676)
- [Fe fins a 6 R☉, 2026](https://doi.org/10.3847/1538-4357/ae2658)
- [eclipsi i Parker/WISPR, 2026](https://arxiv.org/abs/2601.10818)
- [espectre K-coronal, 2026](https://doi.org/10.3847/1538-4365/ae2fc2)

## 6. Tipus de connexió amb satèl·lits

No tot és «calibrar satèl·lits amb eclipsis». Cal diferenciar:

- comparació física: Fe X visible versus SWAP EUV;
- connexió remota–in situ: línies Fe versus ACE/Ulysses;
- calibratge transferit: contínuum posat en unitats amb K-Cor;
- validació independent: disc solar i LASCO-C2;
- cobertura espacial: eclipsi entre SDO/STEREO i LASCO;
- banc de prova de forward models MHD;
- comparació estadística amb WISPR/PSP, no sempre contemporània.

## 7. Claims que s'han de formular amb cautela

- Les estructures de densitat són un proxy de la direcció projectada del camp, no una mesura del vector complet.
- Les proporcions de línies són integrades al llarg de la línia de visió i depenen de CHIANTI i de les hipòtesis d'equilibri.
- Per sobre del *freeze-in*, no representen necessàriament \(T_e\) local.
- L'amplada de línia inclou turbulència.
- Els «vortex rings» comparats amb WISPR no són necessàriament els mateixos objectes seguits individualment.
- L'associació entre 1,5 Mm i granulació és una inferència.
- Els «first» són formulacions dels autors i s'han de citar així.

### Cometes

No s'ha d'afirmar que Druckmüller va descobrir:

- C/2008 O1 (SOHO), descobert per Hua Su abans de l'eclipsi;
- C/2020 X3, també detectat prèviament;
- ISON o Lovejoy.

El mèrit és detectar i estudiar objectes extremadament febles a tocar del Sol amb dades d'eclipsi. [C/2008 O1 i eclipsi](https://arxiv.org/abs/0907.1643).

## 8. Què podem fer amb les nostres Sony

### Sí

- corona blanca d'alta resolució;
- morfologia de streamers, plomes, loops i cavitats;
- prominències;
- Earthshine;
- estrelles i possibles cometes;
- HDR lineal calibrat;
- polarimetria només si s'afegeix un experiment dedicat i calibrat;
- comparació morfològica amb coronògrafs i models.

### No, només amb RGB de banda ampla

- mapes de Fe X/Fe XI/Fe XIV;
- temperatura electrònica fiable;
- radi de *freeze-in*;
- separació quantitativa K/F;
- brillantor absoluta sense calibratge addicional;
- diagnòstic d'ions només perquè la A7III està modificada.

Una càmera modificada amplia resposta. No substitueix:

- una càmera mono;
- un filtre on-band;
- un off-band simultani;
- calibratge fotomètric.

## 9. Lliçó transferible

La principal innovació no és fer visible la corona. És conservar una cadena que permeti preguntar:

- quin píxel venia de quina exposició;
- estava dins el tram lineal?;
- quants frames el sostenen?;
- l'estructura es repeteix?;
- apareix en una altra càmera?;
- sobreviu a un altre algoritme?;
- existeix també en un coronògraf o model?;
- és un resultat quantitatiu o només de visualització?

Aquest és el nivell de disciplina que hem d'importar a 2026.
