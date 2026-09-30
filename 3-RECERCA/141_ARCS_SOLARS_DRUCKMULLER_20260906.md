# Arcs centrats en el Sol: revisió de Druckmüller i contrast amb V31

06-09-2026. Pere confirma sense dubtes que els minicercles són arcs centrats
en el Sol i que els veu només als filtres NO azimutals. Aquesta precisió
resol la pregunta pendent de research/140; no és una nova versió del producte.

**Conclusió:** hi ha un precedent explícit d'anells introduïts pel processament
radial. Tanmateix, els papers no demostren que els arcs de V31 siguin inevitables
en un ACHF ni que eliminar la nostra compensació H1 els resolgui. La mesura
causal nova descarta H1 com a origen dominant del component radial curt
mostrejat de 01/02 entre 2,5–4,5 R☉. V31 continua intacta.

## Què diuen les fonts originals

- **Druckmüller, Rušin i Minarovjech (2006), §4.2, pp.138–139, eqs.5–7:**
  passa-alt bidimensional de nucli variable. El nucli atén la separació
  Lluna/corona i la resposta a diferents orientacions; el paper no determina
  un únic algorisme ni publica tots els paràmetres de Corona.
  [Article original](https://www.astro.sk/caosp/Eedition/FullTexts/vol36no3/pp131-148.pdf).
- **Druckmüllerová, Morgan i Habbal (2011), eq.1 i §4.3:** NRGF resta la
  mitjana de cada anell i divideix per la desviació; FNRGF també s'adapta en
  angle. ACHF empra veïns de radis diferents, cosa que permet realçar detall
  tangencial. No s'ha de convertir tot filtre en exclusivament angular.
  [Article FNRGF](https://pure.aber.ac.uk/ws/portalfiles/portal/5092215/ENHANCING_CORONAL_STRUCTURES_WITH_THE_FOURIER_NORMALIZING_RADIAL_GRADED_FILTER.pdf).
- **Tesi de Druckmüllerová, pp.82–83 i106:** descriu anells de gramòfon al
  FNRGF perquè processa els radis independentment. La mediana radial ±2px
  provada no funcionà; proposa investigar una funció global2D. La tesi no
  presenta aquesta proposta com una correcció resolta. Les eqs.5.1–5.2,
  pp.67–68, descriuen el precursor d'ACHF amb gaussianes en radi i arc.
  [Còpia local llegida](</Users/USUARI/Desktop/Eclipse 2026/Papers Druckmuller/Druckmullerova_2013_tesi_doctoral_completa_filtres_adaptatius_corona.pdf>),
  [registre universitari](https://dspace.vut.cz/items/d5b33ccc-eb01-4fc5-bb8e-16fb033f831c).
  El nom local conté2013; la fitxa bibliogràfica del repositori data la defensa
  el2014. S'han llegit les pàgines i inspeccionat les figures6.3/6.4 locals;
  el servidor web del PDF ha fallat, sense impedir consultar l'original local.

## Què executa el nostre codi

`research/tools/v29/refine_detail.py:23–35` filtra `ln(TOTAL)` amb gaussianes
cartesianes normalitzades pel suport, divideix el residu per un contrast
radial robust de120nodes, i combina els canals amb mediana. Després aplica
`tanh`, suavitzat S/N i H1. Les variants04/05/06 hereten aquesta família.
És una implementació pròpia inspirada en ACHF amb normalització radial;
no és una reproducció íntegra del programa de Brno ni el NRGF literal.

El contrast120 ja es suavitza i interpola. H1 també interpola una compensació
de200nodes. Per tant, l'analogia amb cercles independents del FNRGF és una
hipòtesi a provar, no una identificació causal. El gate H1 mesura els mateixos
200bins emprats per corregir: no exclou ondulacions entre nodes ni canvis de
contrast amb mediana nul·la.

## Comprovació nova: contribució directa d'H1

`inspect_h1.py` compara els ràsters congelats abans/després d'H1 i V31,
amb vista del llenç sencer i finestres al100%. El delta es mostra ×10 i
inclou la quantització/retall final de16bits; no és una proposta de correcció.

`measure_h1.py` usa mostreig radial d'1px i1.440angles, vuit sectors de45°,
suport físic vàlid i bandes Butterworth d'ordre4 amb fasezero. No reutilitza
els200bins de la porta H1. Els resultats són sobre01/02 abans del suavitzat
addicional deV31: aïllen l'operació H1 heretada. No mesuren la puresa física
de tota textura ni el residu final de les altres tres capes.

| Franja2,5–4,5R | 01 | 02 |
|---|---:|---:|
| H1: RMS radial4–32px | 0,00002414 | 0,00004147 |
| H1 / RMS sectorial4–32px | 0,359% | 0,604% |
| H1 / RMS sectorial32–128px | 19,14% | 22,34% |
| Component radial comú32–128px abansH1 | 0,001554 | 0,002464 |
| Component radial comú32–128px desprésH1 | 0,001377 | 0,002065 |

H1 conté una contribució concèntrica mesurable, però la seva retirada no
elimina el component curt i augmenta el component ample mitjà en aquesta
comparació. No s'ha de confondre la figura del delta amb la demostració
que tots aquests anells siguin afegits indegudament al producte.

## Conseqüència per a la correcció pendent

El diagnòstic anterior que prioritzava dianes locals/soroll no responia a la
forma que Pere confirma ara. Cal seguir la resposta radial del senyal:

1. Ablació de tot el guany radial de contrast amb resta de passos congelats;
   comprovar nivell i contrast per sectors a resolució radial fina. Canviar
   només l'interpolador no suprimeix les variacions ja presents als nodes.
2. Separar el residu radial de `ln(TOTAL)` i la seva resposta al passa-alt,
   incloent les discontinuïtats HDR. La correcció de font aplicada a03 no
   s'ha aplicat a01/02/04–06.
3. Qualsevol ajust continu candidat ha de conservar el detall corroborat
   amb l'altre tren i injeccions. Una mediana radial zero no basta.

No s'ha aplicat cap suavitzat nou al producte, retall circular, canvi de
suport/FOV ni generat cap V32.psb. Les figures són de diagnòstic. La revisió
bibliogràfica està completada; la correcció completa continua sense validar.

Eines/rebut: `research/tools/arcs_druckmuller_20260906/`.
Figures: `output/arcs_druckmuller_20260906/`.
El handoff de PRODUCTE vigent continua `.coordination/HANDOFF_2026-09-05_V31.md`.
