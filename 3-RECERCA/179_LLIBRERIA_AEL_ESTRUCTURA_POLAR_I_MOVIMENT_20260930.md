# 179 — La llibreria executable `ael`: imatge d'estructura, corona desplegada i moviments de la corona

**30 de setembre de 2026 (nit) · Claude, de manera desatesa, per encàrrec de Pere**

Pere va enviar dues imatges de referència d'un altre fotògraf: una corona d'estructura en gris blavós, amb protuberàncies roses, i la mateixa corona desplegada en coordenades polars. També va enviar una animació publicada per un tercer amb els moviments de la corona durant la totalitat. L'encàrrec: «segueix desenvolupant la Agentic Eclipse Library perquè es puguin fer resultats com aquest i animacions com aquesta; no ens podem quedar enrere». Marcatge: **MESURAT** · **INFERIT** · **PENDENT**.

## 1. Què s'ha fet

- **Un paquet de Python executable, `ael`** (`3-RECERCA/tools/ael/`, en anglès perquè va al repositori públic):
  - funciona amb les dades de qualsevol eclipsi, no només amb les nostres;
  - mòduls: geometria, polar, filtres, presentació, moviment, calibratge, anotació, fitxers i rebuts, dades sintètiques i portes;
  - canonades completes a `ael/pipelines.py` i ordre `python -m ael`;
  - **11 proves amb veritat coneguda**, cadascuna amb el seu control negatiu.
- **Aplicació a les dades del 2026** (`3-RECERCA/tools/ael_2026/p0`–`p4`):
  - resultats a `4-RESULTATS/ael_20260930/`;
  - vistes a `IA/output/ael_20260930/`.
- **Skill nova**, `.claude/skills/corona-visualizations/`.

## 2. Imatge d'estructura (a partir de la fusió lineal de la V120)

`estructura = B(r) + g·(ℓ − ⟨ℓ⟩(r)) + a·d·B(r)^γ`:
- **ℓ**: logaritme suau de la lluminància menys el cel (sense forats on el cel restat és negatiu);
- **B(r)**: perfil de presentació **dissenyat i declarat**, en lloc de la caiguda radial;
- **d**: detall multiescala blanquejat (WOW) amb terra de soroll.

Tres versions:
- **mono**;
- **blava**: to fred declarat, a l'estil de la referència, amb les protuberàncies del color mesurat;
- **daurada**: el color local mesurat.

Troballes (MESURAT):
1. **El soroll de la fusió és correlacionat.** A les escales 2–4 del starlet n'hi ha de 6 a 14 vegades més del que prediu el soroll blanc; factors mesurats més enllà de 6 R☉: 0,89 · 1,25 · 1,02 · 0,63.
   - Amb els factors de soroll blanc, la corona exterior sortia tacada.
   - El llindar suau fa taques: descartat.
2. **El color s'ha d'aplicar en llum lineal.** Multiplicar el gris ja corbat per les ràtios lineals el saturava: la daurada sortia taronja.
   - Amb les ràtios elevades a 1/2,2: R/G 1,30 i B/G 0,52 a 1,15–1,6 R☉.
   - La V120 de Pere, a 1,1–1,8 R☉: 1,33–1,35 i 0,46–0,48.
3. **Lluna del llenç ajustada:** centre (5391,2; 3777,4), radi 469,2 px, rms 0,81 px.
   - És la vora de la dada fusionada: la unió de les Llunes de tota la totalitat, a 29,5 px del Sol.
4. **Porta «res fora de la dada»: PASSA** (0 píxels).

## 3. Corona desplegada

- `ael.polar`: anada i tornada exactes (≤ 1 %), anti-aliasing provat i NaN on el suport de la interpolació surt de la dada.
- Vistes de 360° × 0,95–4 R☉ al voltant del Sol i de la Lluna (limbe pla), i trams de 120° (≈ 16:9).

## 4. Moviments de la corona (Vixen, 6 èpoques)

**Dades.** La Vixen va repetir l'escala 1/2000–1/2 s i 1/1000–1 s. En surten sis èpoques: C2 + 11, 18, 73, 79, 86 i 92 s (temps ponderat per l'exposició). El centre del Sol és el del manifest de `Corona_HDR_Vixen` (validat ≤ 0,09 px, recerca 78). Coordenades del sensor sencer = manifest + (172, 108).

Troballes, en l'ordre en què van aparèixer:
1. **El sensor semblava moviment.** Amb només el flat radial, el 68 % de les finestres (3.601 de 5.282) es movia exactament amb la deriva del telescopi al marc del Sol (MESURAT).
   - **Causa:** la sensibilitat fina dels píxels (PRNU): 1,09 % rms al verd, refeta amb els 125 flats del 22-08, amb la recepta de la recerca 90. Aquell mapa s'havia retirat el 16-09 i no s'havia aplicat mai.
   - **Curada a la calibració** (torre de Pisa): 185 de 5.282 (3,5 %), amb les mateixes finestres i el mateix filtre.
   - ⛔ **Trampa:** la correlació entre dues èpoques separades 6 s NO mesura aquesta cura. Totes dues comparteixen el patró fix (desplaçat només 1,6 px), i amb el mateix filtre gairebé no canvia (0,64 → 0,66 a 1,3–1,7 R☉). Una primera xifra «0,20 → 0,66» comparava dos filtres diferents i s'ha retirat.
2. **La Lluna.** Arran del limbe, l'inici i el final correlacionen només 0,4–0,6 (0,95 entre èpoques tardanes). Són canvis lunars:
   - la Lluna es mou 21 px respecte del Sol;
   - amaga la protuberància gran d'un costat i destapa la cromosfera de l'altre (vist a ull).
3. **El Sol es pon.** Igualació fotomètrica: les èpoques tardanes són −4,7 a −6,1 % (coherent amb k = 0,40 de la recerca 78).
4. **Sistemàtics globals:** un camp afí de ~0,6 px de translació i ~¼ px per 1.000 px de compressió (refracció i deriva del registre). Es resta abans de qualsevol afirmació local.
5. **Els raigs llisquen sobre si mateixos** (problema d'obertura): al llarg del raig només es mesura amb un pic de correlació fort.
6. **El segon testimoni no pot compartir fotogrames.** Parelles disjuntes: A = E1 → E3+E4 i B = E1b → E2+E2b. La primera versió compartia l'època inicial, i els falsos positius s'hi repetien.
7. ⛔ **Un nul de tota la cadena amb Δt de 6 s no és just:** les zones de moviment fals queden a sobre del zero i s'ho mengen tot. Els nuls han de ser locals, finestra a finestra.
8. **La revisió visual és l'última porta.** Els 10 candidats que passaven totes les proves numèriques eren lliscaments al llarg de raigs o soroll (full `moviment_candidats_revisio_visual.png`).

**Resultat (MESURAT):** cap moviment coronal per sobre de **44 km/s** (3σ del nul local, en 78 s, a 2,15″/px) per a trets compactes entre 1,1 i 2,2 R☉. Al llarg dels raigs no es pot mesurar. La canonada general (`python -m ael motion` amb `MOTION_CONFIG_VIXEN_2026.json`) reprodueix exactament el resultat fet a mà.

**Animacions:**
- `moviment_6_epoques.gif/.mp4` i `moviment_parpelleig_inici_final.gif/.mp4`: passa-banda, alineades al Sol i orientades com la imatge de Pere. El sensor està girat 10,6° respecte del llenç, amb la mateixa paritat (correlació 0,998).
- Cap fletxa, perquè cap moviment no s'ha confirmat.
- La demostració sintètica (`demo_sintetica/`) mostra com surt quan sí que hi ha moviment.

## 5. PENDENT

- **Segon instrument.** La Sony (A i B, 3,2″/px) com a testimoni independent del moviment. No fet: amb aquesta resolució el llindar seria més alt.
- **Per al 2027** (INFERIT; enllaça amb «escales entrellaçades»):
  - repetir una escala curta cada ~10 s durant tota la totalitat;
  - fer exposicions més llargues a 1,5–3 R☉;
  - el llindar baixa amb el nombre d'èpoques i el desplaçament creix amb el temps. El 2027, la totalitat serà molt més llarga.
- **Publicar al repositori:** la còpia local ja té el commit fet; només cal el sí de Pere per fer el `push`.
