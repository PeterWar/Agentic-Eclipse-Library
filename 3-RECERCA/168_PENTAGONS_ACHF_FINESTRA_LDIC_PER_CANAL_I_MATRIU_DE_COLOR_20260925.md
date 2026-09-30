# 168 · Què causava els «pentàgons» dels ACHF (i com no tornar-los a fer)

25-09-2026 · Claude, V98 (desatès) · Pregunta de Pere: «07 ACHF azimutal suau r8 · V97 registra una millora boníssima, els artefactes pentagonals han desaparegut! Què els causava?»

## La resposta curta
Els pentàgons eren un **graó molt petit (≈ 0,1 %) al llarg d'una isofota de l'apilat de la Vixen**. Naixia a l'apilat HDR (LDIC): el pes de cada exposició es calculava **canal per canal** (R, G i B, cadascun amb el seu sostre de saturació i el seu terra). Cada canal, doncs, canviava d'exposició a una brillantor diferent. Allà on les exposicions no quadren perfectament (un 0,1–1 %), cada canal fa un graó just a la seva isofota de canvi.

Després, la **matriu de color** de la càmera barreja els canals (el verd de sortida és −0,18 R + 1,69 G − 0,51 B). Els graons de R i de B entren així al verd, que és el que fan servir els filtres.

Les isofotes de la corona interior no són cercles: tenen forma de polígon (els serrells). Un filtre que fa **pas alt al llarg de l'arc** (els ACHF azimutals 03 i 07) converteix un graó que travessa azimuts en una vora nítida. Surt una ratlla poligonal tancada a 150–330 px del limbe: el «pentàgon».

La V97 ho va curar a l'origen (el pis de l'apilat, torre de Pisa) amb la **finestra comuna**: un sol pes per cel·la Bayer, el del subplà que satura primer. Els quatre subplans barregen exactament les mateixes exposicions, i la matriu ja no pot convertir cap desacord entre canals en un graó.

## La prova (factorial, `4-RESULTATS/v98_20260925/J13_PENTAGON_FACTORIAL.json`)
Quatre apilats Vixen desats de la V97 (finestra per canal o comuna × camps de nivell φ originals o a zero), passats pel **mateix nucli de l'operador de la capa 49** (pas alt al llarg de l'arc sobre ln G, suavitzat radial r8), amb el mateix suport. Es compara amb el patró real que va desaparèixer (capa 49 de la V93, a Artefactes_V95, menys la capa 49 de la V97), a l'anell de 100–450 px del limbe:

| variant (menys la comuna amb φ original) | RMS (ln) | correlació amb el patró real | nul (patró girat 180°) |
|---|---|---|---|
| per canal, φ original | 0,00082 | **0,77** | −0,01 |
| per canal, φ zero | 0,00108 | **0,66** | −0,01 |
| comuna, φ zero | 0,00038 | 0,09 | 0,01 |

- Canviar només la finestra (per canal ↔ comuna) reprodueix el pentàgon, amb φ i sense.
- Canviar només φ no el fa.
- La imatge `J13_canal_taula_menys_comuna.png` n'és el dibuix: el polígon tancat al voltant de la Lluna.

## Per què només alguns filtres el veien
- Els ACHF **azimutals** (47–49) fan pas alt en azimut: una isofota poligonal es converteix en vores.
- Els ACHF **isòtrops** de la V93–V96 es calculaven canal per canal i hi sumaven el graó de color B/G: és la «família» de les ombres poligonals d'Artefactes_V95 (vegeu la revisió del 24-09).
- La WOW, la RHEF i l'NRGF normalitzen per escales o per anells i no el destaquen.

## Regles perquè no torni
1. **Un sol pes d'exposició per píxel per a tots els canals** (finestra comuna, `b2_v97.py --finestra comuna`). Mai una finestra LDIC per canal.
2. Tot conjunt de fotogrames que en surti (els `limb_frames` de la caixa lunar, qualsevol apilat parcial) s'ha de fer amb **la mateixa finestra** que l'apilat principal. A la V98 s'han refet els `limb_frames` amb la comuna (`a9b_limb_frames_comuna.py`); els de la V85 eren per canal, i la franja de la V86–V97 se'n feia.
3. **Porta:** abans de filtrar, `j2_poligon.py` (ràtio ≤ 1,8, salt ≤ 0,002) i, per als ACHF azimutals, el factorial `j13_pentagon_factorial.py` quan canviï l'apilat.
4. Quan una forma poligonal surti només en uns quants filtres, mira primer què tenen de diferent a l'entrada (el color per canal, la matriu), abans de sospitar de les màscares o dels operadors.
