# ARXIU HISTÒRIC — prompt de revisió crítica independent

> Aquest fitxer conserva un prompt de contrast anterior. No és el context
> canònic de Claude, no autoritza accions i no descriu l’estat actual. Per
> reprendre el projecte llegeix `../CLAUDE.md` i `README.md` d’aquest directori.

# Revisió crítica independent — projecte d'eclipsi total 2026

Actua com a revisor tècnic adversarial expert en fotografia d'eclipsi, control remot de càmeres Sony, HDR científic i processament coronal. No inventis fonts ni detalls propietaris. Separa sempre: (a) fet documentat, (b) inferència raonable i (c) assaig necessari.

No has d'implementar codi. Necessito una crítica que ajudi a consensuar el disseny.

## Context d'equip

- Eclipsi total de 2026 des d'Espanya; ubicació i meteorologia fora d'abast.
- AP130GTX + QUADTCC: 585 mm f/4,5.
- Sony FE 300 mm f/2,8 GM.
- Sony A7RIIIA no modificada: 42,4 MP, 7952×5304.
- Sony A7III astromodificada: 24 MP, 6000×4000.
- Canon 6D opcional.
- La combinació AP+QUADTCC+A7III modificada va donar bona qualitat òptica el 2024.
- L'equip de Miloslav Druckmüller va advertir personalment que una càmera normal és preferible: una modificada pot saturar prominències abans i la resposta espectral més ampla pot augmentar aberració cromàtica. També van preferir 300 mm a 200 mm.
- El propietari assenyala correctament que el balanç de blancs permet aparença diürna normal amb l'A7III modificada. Això no reverteix la resposta espectral física del RAW.

## Hipòtesi d'assignació

- A7RIIIA + AP/585 mm per al màster de màxima resolució i corona interior.
- A7III modificada + 300/2,8 per a camp ampli, corona exterior i redundància.
- Pla de retorn: conservar A7III+AP si l'assaig A/B no prova clarament que l'A7RIIIA manté focus, cadència i qualitat.

Escales aproximades:

- A7RIIIA+585: 1,59 arcsec/px, Sol ~1190 px, camp vertical ~4,47 radis solars.
- A7III+585: 2,09 arcsec/px, Sol ~905 px.
- A7RIIIA+300: 3,10 arcsec/px, Sol ~619 px, camp vertical ~8,72 radis.
- A7III+300: 4,08 arcsec/px, Sol ~471 px.

## Auditoria 2024

- A7III+AP: 56 RAW en 291 s, mediana 2 s, però buits de 30 s i 125 s.
- Canon 6D+300: 146 RAW en 290 s, mediana 2 s, cap buit >4 s; escales repetides de 1/4000 a 1 s.
- A7S+Questar: 58 RAW en 325 s, mediana 6 s; es descarregava cada RAW per USB.
- Els scripts conservats tenen dates de prova, errors de sintaxi, ordres sense port, inicialització que dispara, una nova invocació gphoto2 per captura, cap verificació/retry/log i no coincideixen exactament amb els RAW.
- Rellotges de càmera no sincronitzats; l'A7S encara marcava 2014.
- A7III: mostra RAW a 14 bits amb clipping creixent; 0,4 s clipeja ~7,4% i 2 s ~20,4%, però no arriba a la vora del camp.

## Pipeline Druckmüller reconstruït

Cadena acreditada per les pàgines 2024:

`RAW → dark/flat → PhaseCorr → LDIC 6.0 → Corona 6.0 → ACC 6.1`

Principis publicats:

- caracterització de linealitat, black level i clipping;
- calibratge bias/dark/flat al mosaic Bayer abans de demosaic;
- registre per correlació de fase sobre la corona, emmascarant Lluna i saturació;
- registre progressiu entre exposicions semblants;
- fusió HDR lineal ponderada, amb regressió sectorial per compensar gradients/llum difusa;
- màster lineal separat de la visualització;
- ACHF/Corona, MGN, FNRGF etc. només com a derivats morfològics;
- stack lunar/Earthshine separat pel moviment de la Lluna;
- validació d'estructures entre exposicions, càmeres i filtres.

Obert/reproduïble: IPC, NRGF, FNRGF, MGN; WOW i RHEF són benchmarks moderns.
Parcial o privat: LDIC 6, Corona 6, ACC 6.1, D3F2.

## Hipòtesi gphoto2/búfer

libgphoto2 declara A7III i A7RIII PC Control amb captura, trigger i configuració.

Un benchmark extern de febrer de 2026 fet amb A7III i A7RIIIA proposa:

- bràqueting continu nadiu de 5 imatges a 3 EV;
- tres velocitats base 1/80, 1/40 i 1/20;
- cada sèrie genera base ±3 i ±6 EV;
- les tres s'intercalen en 15 exposicions a passos aproximats d'1 EV, de ~1/5120 a 3,2 s;
- una acció PTP anomenada `bulb` actua com a pressió mantinguda i deixa que la càmera usi el búfer;
- només tres canvis de velocitat, en comptes de quinze;
- RAW a targeta i descàrrega diferida.

Punts pendents:

- provar si aquesta acció `bulb` manté realment 14 bits o activa una limitació de 12 bits;
- ordre real del bracket, latència, búfer, drenatge i targeta;
- RAW comprimit versus no comprimit;
- comparar pressió física Multi Terminal, gphoto2 persistent i triggers individuals;
- Sony documenta aproximadament 89 RAW comprimits/40 sense comprimir per A7III i 76/28 per A7RIII, però no són garanties en PC Remote.

## Preguntes per a la revisió

1. Quins errors conceptuals o sobreafirmacions veus?
2. És racional l'assignació A7RIIIA+585 i A7III modificada+300? Quins assajos la podrien refutar?
3. El bràqueting nadiu de 15 exposicions és apropiat per totalitat o té punts cecs? Proposa millores sense escriure codi.
4. Com separaries C2/C3, prominències, corona interior i corona exterior en termes de captura?
5. Quins punts únics de fallada queden?
6. Quines tres o cinc proves de banc donen més informació abans d'implementar?
7. Quins referents, papers o mètodes rellevants falten, si en coneixes amb confiança?
8. Dona un veredicte final curt: què conservar, què canviar i què no decidir encara.

Respon en català i sigues concret.
