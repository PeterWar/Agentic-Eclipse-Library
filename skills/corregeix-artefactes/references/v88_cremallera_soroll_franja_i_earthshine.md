# V88: la «cremallera» de la franja, el soroll d'un instant i la vora de l'earthshine

Lliçons comprovades el 23-09-2026 (tarda), a partir de les marques de Pere a la V87 (capa «Artefactes V87»).
- **Evidència:** `4-RESULTATS/v88_20260923/` (rebuts `A3A_*`, `A4_*`, `E1_*`, `E2_*`, `B2_*`, `B4_QA.json`, `B6_*`, `RESULTAT.md`, intents descartats amb el seu LLEGEIX-ME).
- **Codi:** `3-RECERCA/tools/v88_20260923/`.
- **Producte:** `1-PHOTOSHOP/V88.psb`.

Continua les lliçons de la V86 (`v86_franja_un_instant_forats_i_cantonada.md`). Una prova que passa no vol dir que no hi hagi artefactes: la mirada de Pere mana.

## Les marques, llegides abans de tocar res
- **Extracció:** `c0_marques_v87.py` extreu la capa de marques per to (HSV) i en dona, per component, l'azimut i la distància al limbe de la Lluna de presentació. En aquest cas:
  - verd a 0–20 px fora;
  - marró i blau clar a 0–6 px fora;
  - lila a 1–11 px **dins** del disc;
  - taronja a 23–41 px, sobre la protuberància.
- **Com es llegeixen:** marques de colors diferents poden ser la mateixa família. El verd, el marró i el blau clar eren tots la vora de la franja d'un instant. El to diu què hi veu Pere, no la causa.
- **Vistes natives:** es fan de la versió de Pere sense la capa de marques (`b1_vistes_v87.jsx`: obre, amaga, exporta i tanca sense desar).

## Verd «pixelat, cosit de cremallera»: dues causes, cap a la intensitat dels filtres
Pere suggeria abaixar la WOW o l'ACHF, però abans calia buscar-ne la causa. N'hi havia dues, i totes dues eren de la dada.

**1. Soroll: la dada d'un instant té ~3 vegades el soroll fi de la fusió** (k = 2,8–3,1, a 20–45 px del limbe).
- **Per què:** són 11 fotogrames curts, dominats pel d'1/125 s, contra els 67 de la fusió. La WOW i l'ACHF micro el realcen i en fan un gra puntejat.
- **Cura:** convolució gaussiana normalitzada σ 1,3 px de la dada d'un instant, dins del seu domini i **abans** dels filtres. És la norma «la resolució segueix el S/N».
- **Com es tria σ:** per igualar el soroll de l'escala més fina al de la fusió (quocient 1,00–1,03), mai per passar una prova.
  - σ 1,5 ja deixava la franja massa llisa (P8 0,64–0,81), i va quedar descartat.
- **Què queda:** a tres sectors, la franja té un 20–27 % menys de gra fi que la corona de 25–40 px, i la prova P8 hi falla (0,73–0,79). Es declara, no es maquilla.

**2. Les dents: la vora del domini era binària i esglaonada.** Una màscara binària d'un cercle sempre fa graons de píxel, i els filtres no lineals (NRGF, RHEF local, ACHF, WOW) hi responen a cada graó. Al compost es veuen com una cremallera o perles.
- **No n'hi ha prou amb alisar la corba del domini.** Amb una corba llisa per azimut (`DMIN`), però amb el tall binari, les dents hi continuaven igual.
- **Cura:** fosa **suau** sobre la **distància analítica** (subpíxel) a la corba llisa: `pes = smoothstep(d − DMIN(θ), VORA − 1, VORA + 2)`, amb VORA 2.
- **La continuació ha de ser radial:** a cada azimut, el valor a `R + DMIN + VORA + 2` s'allarga cap endins (`cv2.remap` polar, `INTER_LINEAR`, `BORDER_REPLICATE`).
  - La continuació de piràmide i Laplace de la V86 tira, arran de la vora, cap a la mitjana del disc. Amb la fosa suau hi va fer una línia fosca a 214°.
- **Com es fa `DMIN`** (`a3a`):
  - per a cada azimut (1440 calaixos), el màxim de les distàncies dels píxels sense dada a 0–8 px, més 0,25;
  - després, `maximum_filter` de 5 i una gaussiana de 4;
  - per acabar, el màxim amb el `maximum_filter` de 3, perquè la corba mai quedi per sota d'un píxel dolent.
- **⛔ No busquis a massa distància.** Buscant fins a 30 px, un pedaç aïllat amb NF 5–7 a 240–260° (d 21–30) va empènyer la corba fins a 15 px. Es busca fins a 8 px, i més enllà n'hi ha prou amb 5 fotogrames.
- **Fitxers:** `a3a` desa `DMIN` i el centre (`cx`, `cy`, `R`) a l'npz perquè `a4` hi pugui fondre.

## ⛔ Error de la V86: `W_CURT` sortia 0
La condició «pes efectiu mínim d'1,5 fotogrames curts» no feia res, perquè la referència es calculava amb la mediana de tots els pesos i en sortia 0.
- **Cura:** mediana dels pesos **positius**.
- **Com es comprova:** llegeix sempre el valor d'un llindar derivat al rebut. Una condició que no descarta cap píxel és sospitosa.

## Lila: la vora de l'earthshine té massa textura
**Què es veu:** a la capa lunar de Pere (225), arcs paral·lels al limbe (un limbe doble o triple), estries i línies. A 1–11 px dins del disc, la textura és 4–12 vegades la de l'interior, sense cap correlació amb LROC.

**Hipòtesi de Pere, confirmada:** arran del limbe, els fotogrames llargs estan saturats a pedaços.
- Els de 10 s només hi tenen el 54–57 % dels píxels vàlids, i els que queden són els foscos, una **selecció**.
- A més, la Lluna es mou 2,8 px en 10 s.

**Apilat des de zero (`e1`, prova), amb els 14 fotogrames Vixen ≥ 0,25 s:**
- **Registre:** un sol registre sobre la Lluna. Els centres surten d'un cercle ajustat (Kasa) a la distància del model per fotograma, i la trajectòria quadràtica s'avalua a t = 18,43 s (residu 0,26 px).
- **Saturació:** radi de saturació per grau (el primer calaix de 0,5 px amb < 99,5 % vàlid). Es talla a 3–7 px d'aquest radi, amb una rampa.
- **Guarda del moviment:** v · exposició / 2 + 1 px.
- **⛔ Valor per defecte:** si el radi de saturació per defecte és 0, es talla cada fotograma a 3 px del limbe. Ha de ser 10 (sense límit).

**El test que decideix: meitats independents contra LROC.**
- **Arran del limbe (−30..−2 px):** dues meitats independents de l'apilat reprodueixen el relleu (0,88–0,99), però LROC no (0,01–0,21). És **estructura real de la llum dispersa** de la corona, no la Lluna.
  - Coincidir entre meitats demostra que no és soroll, no que sigui lunar.
- **Interior:** l'apilat Vixen des de zero és **pitjor** que la capa de Pere (LROC 0,52 contra 0,66 a 6 px, i 0,35 contra 0,66 a 12 px), que ve de Sony + Vixen i de la feina de la V56.
- **Models de vel de la llum dispersa:** tots queden per sota:
  - radial global: LROC 0,20;
  - adaptatiu σ 25: correlació negativa;
  - rang 1: 0,08;
  - per sectors de 4° (σr 3): 0,52, el millor.

**Solució, capa nova «Earthshine V88» (`e2`):**
- **Interior:** l'earthshine de Pere, idèntic a més de 24 px de la vora.
- **Anell:** es treu l'estructura fina no lunar. Hi ha un suavitzat radial σ 5 px que llegeix només a més de 12 px de la vora, i un d'azimutal σ 4 px en coordenades polars.
  - La transició va de −24 (res) a −12 px (tot). La mateixa alfa, byte a byte.
- **Resultat:** la textura de l'anell queda en 0,13 vegades la de l'interior (la 225, 2,84).
- **⛔ No alimentis l'anell amb els últims píxels.** Amb una font a 1–6 px de la vora surten flames radials (a 280°).
- **Límit:** l'anell (~12 px) és llis, perquè amb aquestes dades no hi ha detall lunar mesurable. Qualsevol realç hi mostraria llum dispersa.

## Comprovacions i trampes de mirar
- **Compositor emulat:** `v88_compost.py` afegeix «Aclarir» (la capa 76 de la V87 hi és). No reprodueix les capes d'ajust, i per això el jutge és el compost natiu de Photoshop.
- **Hipòtesis refutades amb una mesura:**
  - patró del mosaic CFA;
  - la màscara binària de la Lluna sota l'alfa de la 225 (0 píxels afectats);
  - el mode «Aclarir» de la 76 com a causa de la cremallera;
  - saturació dels llargs a la franja (cap).
- **Estirament per separat a 6:1** (la Lluna i la corona cadascuna amb el seu rang): fa una línia puntejada just al limbe que no és a la imatge. Cal dir-ho a la làmina.
- **Mosaics de vistes adjacents:** fan veure formes (les «V» de `final_4a1`) que són la juxtaposició. Cal mirar cada vista sola o el llenç sencer.
- **P8:** la V87, marcada com a pixelada per Pere, la passa (1,01–1,24). La mesura no capta el caràcter puntejat, així que no s'ha d'ajustar res per passar-la. La mesura del soroll és la que mana, i la prova es declara tal com surt.

## Ordre dels passos
- **Font:** V87 de Pere → `c0` (marques) → `b1` (vistes natives de la V87) → `a3a` (franja d'un instant amb `DMIN` i σ 1,3) → `a3_filtres` → `a4` (fosa suau i continuació radial).
- **Earthshine:** `e1` (evidència) → `e2` (capa).
- **Muntatge:** `b2` (muntatge amb la cantonada regenerada) → `b3` (desament natiu i vistes) → `b4` (proves) → `b5` (làmines) → `b6` (prova de la cantonada a Photoshop).
