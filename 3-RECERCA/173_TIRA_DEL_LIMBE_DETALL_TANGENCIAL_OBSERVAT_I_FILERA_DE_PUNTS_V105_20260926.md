# 173 · La tira llisa arran del limbe: detall tangencial observat, i la filera de punts dels filtres (V105, 26-09-2026)

Informe complet i xifres: `4-RESULTATS/v105_limbe_20260926/RESULTAT.md`. Codi: `3-RECERCA/tools/v105_limbe_20260926/`.

## Què s'ha après

1. **La tira llisa de la V104 té dues causes, i cap no és falta de dada:**
   - la base arran del limbe (la de la V96, < 150 px) és gairebé llisa: el detall tangencial hi té un rms de 0,001, contra 0,02 lluny;
   - els filtres de textura no arriben al pes ple fins a DMIN + 2–3 px.

   Entre la Lluna i aquest punt, la V104 transmet al compost un 5–40 % del detall observat. La foto sola de Pere (09, 1/60 s) en transmet un 25–55 %.
2. **El detall TANGENCIAL arran del limbe és real on el fotograma veu el píxel prou lluny del seu limbe:**
   - Mètode: per a cada fotograma, ln L menys la seva mitjana al llarg de l'arc. Al llarg de l'arc, la caiguda de llum de la vora (la PSF) és constant i s'anul·la, i la mitjana és zero per construcció: no pot fer cap anell.
   - Reproductibilitat entre grups independents (1/125 s contra curts): ρ 0,90–0,93 a dalt des de 2 px del cercle, i 0,78–0,85 a 1 px.
3. **Prova «Lluna o corona»:** en comparar dos grups de fotogrames amb la Lluna desplaçada (~2,6 px), la corona queda fixa i el relleu del limbe es mou.
   - A dalt, ≤ 20 % del detall es mou amb la Lluna.
   - A baix-esquerra (3–5 px) i a baix (0,5–1,5 px), el 50–100 %: allà el «detall» dels primers px és el relleu lunar vist a través de la PSF.
   - La ρ entre meitats NO ho discrimina (ja ho va dir el Codex el 26-09 de matinada). Aquesta prova, sí.
4. **Brno com a jutge del detall afegit** (correlació del canvi amb els composts de Brno, cap píxel seu no entra enlloc):
   - a dalt, +0,2…+0,7 amb tots quatre;
   - a baix-esquerra, als primers 2 px, negativa amb dos dels tres.

   És coherent amb la prova del punt 3.
5. **Com s'omple la tira sense fer línies:**
   - una capa en Superposar amb el detall observat i un guany per punt: el que falta perquè l'energia de textura del compost arribi a la de just a fora del forat dels filtres;
   - multiplicat per la fiabilitat (porta ABSOLUTA de ρ, 0,35→0,80; el p95 dels nuls és 0,12–0,30);
   - menys guany sota la vora translúcida de la Lluna;
   - mitjana zero imposada al llarg de l'arc, també sobre els píxels del llenç (el pas polar→llenç deixava un +0,1…+0,5 %);
   - escales fins a 32 px d'arc: amb 12 px, a la franja d'1–2 px, el detall sortia com a traços curts paral·lels al limbe.
6. **La filera de punts foscos a ~3 px** és el soroll de la franja de banda de la V103/V104, amplificat per la WOW:
   - la franja té 2–3 fotogrames efectius i un soroll fi ×2,2;
   - el mapa de resolució dels filtres és fix (σ 0,70, de la V85);
   - la WOW blanqueja per la potència local isòtropa, que a la franja queda infraestimada.

   Cura a l'origen: la resolució segueix el S/N (norma de Pere del 27-08) a l'entrada de la 56, sobre G/P per no tocar el perfil radial i només a les escales 0–2. Els punts foscos passen de ×6 a igual que fora.

   Tres cures que no funcionen:
   - la potència estimada al llarg de l'arc (no treu els punts);
   - el promig isòtrop (fa un anell de l'1,5 %);
   - atenuar les escales fines (contra la norma).
7. **Substituir la base arran del limbe** (Codex, P01–P07) topa amb el to aprovat: nivell alt, vermell a 0,87 i contracció de gamma. Afegir el detall en una capa a part, amb mitjana zero, conserva el nivell i el color aprovats.

## Trampes noves
- **Un «forat» definit per l'alfa d'un filtre pot estendre's fins on aquell filtre no arriba mai** (la protuberància gran de l'esquerra, a 40 px). Cal limitar-lo a la zona del limbe (DMAX).
- **L'estat d'una versió (`estat_v103/L*_G.npy`) guarda els valors d'abans de la quantització del Photoshop.** Per substituir una capa d'un PSB desat, parteix del canal REAL del PSB; si no, es canvien 35 milions de píxels en 1–2 DN.
- **La capa 303 de Pere a la V104 és opaca i és a sobre de tot.** Qualsevol render del PSB sencer amb la 303 encesa ensenya la 09, no el compost.
- **L'ajust «Claridad y borrar neblina» és no local:** un canvi arran del limbe mou uns quants DN lluny (≤ 78 DN). No és cap error de muntatge.

## La cobertura depèn de l'instant de la Lluna de presentació (26-09, vespre)
Visualització: `4-RESULTATS/v105_limbe_20260926/visualitzacio/COBERTURA_DEL_LIMBE.html` (generador `c5_visualitzacio_cobertura.py`).

Vistes netes (fotogrames que veuen el píxel a ≥ 2 px de la seva vora i sense saturar) a 1 px de la vora real de la Lluna de presentació:
- **Amb la Lluna del PSB (18,4 s):** dreta 41–43; dalt, dalt-esquerra, esquerra i baix-esquerra, 0; baix, 0–36.
- **Amb una Lluna de 45 s:** 17 a tot el costat esquerre, 36 a la dreta. Zero només als dos punts on la Lluna llisca paral·lela al limbe (~73° i ~253°).

**Lliçó:** abans de buscar operadors per al detall arran del limbe, mira quantes vistes netes té cada angle. Amb la Lluna de presentació a l'inici de la totalitat, el costat d'avanç no en té cap als primers px, i cap processat no l'hi pot donar. La palanca és l'instant de la Lluna de presentació (decisió de Pere: canvia quina part de les protuberàncies queda tapada) o la captura.
