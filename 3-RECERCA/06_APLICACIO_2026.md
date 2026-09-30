# Aplicació a l'equip de 2026

## Equip considerat

- Astro-Physics AP130GTX + QUADTCC: aproximadament 585 mm f/4,5.
- Sony FE 300 mm f/2,8 GM.
- Sony FE 70–200 mm f/2,8 GM OSS II, a 200 mm com a alternativa.
- Sony A7RIIIA no modificada, 42,4 MP.
- Sony A7III astromodificada, 24 MP.
- Canon 6D, opcional.

La modificació exacta de l'A7III —filtre instal·lat i corba de transmissió— encara no està documentada en aquest dossier. És una dada necessària per interpretar color, halos i clipping.

## 1. Geometria

Fórmula d'escala:

\[
\text{arcsec/px}=206{,}265\frac{p_{\mu m}}{f_{mm}}
\]

Valors aproximats:

| Combinació | Escala | Sol en píxels | Camp horitzontal | Camp vertical |
|---|---:|---:|---:|---:|
| A7RIIIA + 585 mm | 1,59″/px | ~1.190 px | ~6,7 R☉ | ~4,5 R☉ |
| A7III + 585 mm | 2,09″/px | ~905 px | ~6,7 R☉ | ~4,5 R☉ |
| A7RIIIA + 300 mm | 3,10″/px | ~619 px | ~13 R☉ | ~8,7 R☉ |
| A7III + 300 mm | 4,08″/px | ~471 px | ~13 R☉ | ~8,7 R☉ |
| A7RIIIA + 200 mm | 4,65″/px | ~413 px | ~19 R☉ | ~13 R☉ |
| A7III + 200 mm | 6,12″/px | ~314 px | ~19 R☉ | ~13 R☉ |

`R☉` indica quants radis solars caben aproximadament des del centre fins a la vora, assumint el Sol centrat.

### Interpretació

- 585 mm dona resolució de corona interior i prominències, amb prou camp per als streamers mitjans.
- 300 mm manté molt camp per a corona exterior sense fer el disc massa petit.
- 200 mm és molt ampli: útil per ambient, paisatge o redundància, menys eficient com a segon màster coronal.

## 1A. Condicions geomètriques de 2026

Sense recomanar encara cap lloc, hi ha dos fets que afecten tot el disseny:

- totalitat molt més curta que el 2024;
- Sol baix al vespre.

L'[IGN](https://astronomia.ign.es/en/eclipses-de-sol-y-luna/eclipse-total-sol-de-12-de-agosto-2026) dona dos exemples: A Coruña, 76 s de totalitat i 12° d'altura, i Burgos, 104 s i 8°. Altres punts tindran valors diferents.

Conseqüències:

- no es poden extrapolar els 291 s de 2024;
- cal limitar la durada de cada escala;
- extinció i fons poden desplaçar el ladder;
- dispersió atmosfèrica pot limitar el guany dels 1,59″/px;
- cal alinear/revisar canals per separat;
- l'A/B de les càmeres s'ha de repetir a altura solar semblant.

## 2. Assignació provisional

### A7RIIIA + AP130GTX/QUADTCC

Funció:

- màster de màxima resolució;
- corona interior i mitjana;
- prominències;
- detall fi;
- referència de color stock;
- HDR lineal principal.

Avantatges:

- 42,4 MP aprofitats a la focal més alta;
- mostreig un 31% més fi que l'A7III;
- resposta espectral normal;
- menys risc de saturació espectral anòmala;
- millor separació de petits detalls si focus, seeing i registre ho permeten.

Riscos:

- fitxers més grans;
- búfer sense comprimir menor;
- més sensibilitat a focus i vibració;
- combinació no provada encara en eclipsi;
- els megapíxels poden quedar limitats pel seeing o l'òptica.

### A7III modificada + FE 300/2,8 GM

Funció:

- corona exterior;
- camp ampli;
- cross-backup parcial;
- segona cronologia;
- validació creuada;
- eventual sensibilitat extra a prominències, amb control de clipping.

Avantatges:

- 300/2,8 és ràpid;
- camp vertical ~8,7 R☉;
- 24 MP encara dona ~471 px de diàmetre solar;
- fitxers més petits;
- búfer nominal més gran;
- sistema complementari, no una còpia exacta.

Riscos:

- resposta espectral no estàndard;
- prominències poden clipejar abans;
- més aberració cromàtica efectiva;
- color no directament comparable;
- possible halo dependent del filtre modificat;
- menor resolució angular.
- un cel baix més vermell pot penalitzar especialment el camp exterior.

## 3. Per què el balanç de blancs no tanca el debat

El balanç de blancs:

- multiplica canals;
- pot fer que la foto diürna tingui aspecte normal;
- és molt útil per ús pràctic.

No:

- reinstal·la el filtre espectral original;
- elimina fotons addicionals capturats;
- recupera highlights saturats;
- corregeix desenfoc dependent de longitud d'ona;
- converteix el RAW en equivalent al d'una càmera stock.

Per tant, les dues afirmacions són compatibles:

- l'A7III modificada és usable de dia amb WB;
- la A7RIIIA stock és preferible com a referència coronal de màxima exigència.

Queda una objecció oberta: potser el fons vermell de baixa altura és pitjor amb la modificada just al 300 mm, on la corona és més feble. Si l'assaig ho confirma, l'assignació podria invertir-se:

- A7III modificada + AP, combinació provada;
- A7RIIIA + 300, corona exterior stock més neta.

## 4. La combinació provada continua tenint valor

El 2024, A7III modificada + AP va demostrar:

- bon enquadrament;
- bona qualitat òptica;
- utilitat real dels RAW;
- compatibilitat mecànica.

No s'ha d'abandonar aquesta evidència per una deducció teòrica. La decisió correcta és un A/B:

- A7RIIIA + AP;
- A7III modificada + AP;
- mateix motiu solar/alta llum;
- mateix ISO, exposició equivalent i focus;
- filtre solar adequat;
- comparació de MTF real, color, halo, clipping i focus per canal.

La A7RIIIA guanya el telescopi només si la diferència útil sobreviu:

- seeing;
- seguiment;
- vibració;
- registre;
- processament.

## 5. 300 versus 200 mm

### 300 mm

És la recomanació principal:

- disc més gran;
- més resolució;
- camp encara molt ampli;
- f/2,8;
- coincideix amb el consell de Hana Druckmüllerová.

### 200 mm

És útil si:

- es vol una composició amb paisatge;
- hi ha dubtes de seguiment;
- el vent penalitza el 300;
- és un tercer sistema;
- es necessita molt marge d'enquadrament;
- el 300 presenta ghosts/flare.

No és la millor manera d'aprofitar la segona Sony per corona si el 300 supera els assajos.

## 6. Separar funcions de captura

Un error de 2024 va ser fer recaure massa funcions en una sola màquina d'estats. Per a 2026 cal pensar en modes:

### Parcialitat

- filtre solar;
- cadència moderada;
- exposició fixa o poc variable;
- control de focus i seguiment;
- marge per revisió.

### Pre-C2

- diamant exterior;
- prominències emergents;
- preparació de la transició;
- exposicions curtes;
- cap descàrrega gran;
- estat de càmera ja preconfigurat.

### C2

- ràfega curta específica;
- Baily;
- diamant;
- cromosfera;
- alta freqüència temporal;
- velocitat fixa o patró mínim;
- no intentar en el mateix segon una escala de 15 RAW llargs.

### Totalitat central

- escales HDR curtes i repetides;
- bràqueting nadiu;
- temps suficient de drenatge;
- més repeticions de llargues si la cadència ho permet;
- màster temporal central.

### Pre-C3 i C3

- abandonar exposicions llargues amb prou marge;
- tornar a exposició de contacte;
- ràfega específica;
- no dependre d'una escala que podria acabar tard.

### Post-C3

- segon diamant;
- cromosfera;
- perles;
- tornar a parcialitat i filtre amb procediment segur.

## 7. Divisió entre càmeres

Hipòtesi:

- **A7RIIIA/AP:** prioritat HDR de corona i detall.
- **A7III/300:** en els contactes pot prioritzar una ràfega més temporal; al centre, una escala paral·lela de camp ampli.

Això redueix el risc que tots dos cossos estiguin fent exactament la mateixa exposició llarga en el moment d'una perla.

També es pot intercanviar la prioritat de contacte després dels assajos. La regla és:

- almenys un cos en mode curt al voltant de cada contacte;
- mai els dos atrapats simultàniament en una exposició llarga.

Les dues cadenes són **complementàries**, no redundants en sentit estricte. El 300 mm pot salvar una corona si falla l'AP, però no reemplaça el seu mostreig. La redundància real exigeix:

- una tercera cadena;
- o un mode de retorn cablejat/manual;
- i evitar punts únics de muntura, alimentació, USB i controlador.

## 8. Canon 6D opcional

La Canon del 2024 va ser la seqüència temporalment més robusta. Pot aportar:

- tercera cronologia;
- càmera stock;
- control independent;
- pla de seguretat;
- lent/camp alternatiu.

Només s'ha d'incorporar si:

- té òptica definida;
- no comparteix un punt únic de fallada;
- el controlador és simple i provat;
- no augmenta la càrrega humana;
- les seves calibracions són gestionables.

La repetició del Nikon 300/2,8 usat el 2024 seria una línia a valorar si aquell muntatge continua disponible. No s'ha de donar per fet.

## 9. Obturador

Variables a assajar:

- mecànic;
- EFCS;
- silenciós;
- vibració;
- rolling shutter;
- profunditat RAW;
- bandes;
- highlights extrems.

Punt inicial prudent:

- mecànic o EFCS per contactes;
- silenciós només si els assajos demostren absència d'artefactes;
- Long Exposure NR desactivat;
- reduccions automàtiques desactivades.

Sony adverteix que Silent Shooting pot produir distorsió o bandes en algunes condicions d'il·luminació. [Advertiments Sony](https://www.sony.com/electronics/support/a-mount-body-dslr-a700-series/dslr-a700/articles/00122352).

## 10. RAW sense comprimir

### Sense comprimir

- 14 bits documentats en bràqueting continu;
- més marge de processament;
- arxius més grans;
- menys capacitat de búfer.

El 26-07-2026 Pere fixa RAW sense comprimir com a requisit de qualitat,
també per als contactes. RAW comprimit es pot conservar en una prova de
caracterització, però no és candidat de producció ni una vàlvula de sortida
si la cadència falla.

La velocitat s'ha d'obtenir per:

- card-only fora de PC Remote;
- una sola UHS-II qualificada al Slot 1;
- cap JPEG ni duplicació al Slot 2;
- cadència que no superi l'escriptura sostinguda;
- trigger que aprofiti el bràqueting nadiu.

Si el Gate de 90 s no passa, es redueix el nombre de cicles; no es
comprimeix el RAW.

## 11. Fonts d'alimentació i independència

Cada cadena principal hauria de tenir:

- bateria interna carregada;
- alimentació externa amb prova de transició;
- targeta pròpia;
- cable propi;
- port/control propi;
- possibilitat de dispar físic;
- configuració pregravada;
- cap hub compartit no validat.

Un ordinador pot ser el supervisor comú, però durant C2–C3 els RAW crítics
només s'escriuen a la SD i el trigger ha de tenir release independent.

## Veredicte

La millor hipòtesi és:

> A7RIIIA stock al tren de 585 mm per a detall i color de referència; A7III modificada al 300/2,8 per a camp ampli i cross-backup parcial.

No és una decisió irrevocable. La combinació guanyadora serà la que superi l'assaig complet amb:

- focus;
- halos;
- clipping;
- cadència;
- profunditat RAW;
- búfer;
- vibració;
- recuperació de fallada;
- processament dels frames.
