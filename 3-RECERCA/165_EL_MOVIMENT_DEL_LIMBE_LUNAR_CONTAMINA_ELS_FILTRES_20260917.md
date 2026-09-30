# 165 · El moviment del limbe lunar contamina els filtres (17-09-2026)

**Ordre de Pere:** «anota a recerca que és molt important que el moviment del limbe lunar no contamini els filtres, i qualsevol altre aprenentatge d'aquest pas; que la skill també ho tingui en compte.»

## 1. El fet

La Lluna es va moure 28,5 px sobre la corona durant la totalitat (V38). La base fusionada (V38 → V58) barreja, a la franja **r 456 → ~496 px** del centre lunar (silueta de C2 + recorregut + ala del dèficit de vora), fotogrames on el píxel era corona lliure amb fotogrames on era a tocar de la vora de la Lluna, on cada fotograma perd llum (dèficit de vora: −21 % a 0,5 px als curts, taula V38 B2). En queden arcs foscos que segueixen les posicions successives del limbe.

**Tots els filtres (NRGF 41/42, ACHF 47/49/51/53, RHEF 45/46, WOW 55, WOW bilateral 56) es van calcular sobre aquesta base** (V58, `e2_purs.py` amb farcit A des del «primer anell sencer» a 461 px) i **són ràsters estàtics**: porten els arcs gravats. El WOW bilateral, que preserva vores, els converteix en taques fosques de vora dura: són els «negres de la corona interior» que Pere marca (m2, m4, m5, m7 de la V74; totes entre r 459 i 481, cap fora de la franja).

## 2. Per què no ho vèiem

- Les mètriques de mitjana per marca (marca − entorn, −1…−3 L*) subestimen el que l'ull veu: l'ull veu la **vora** de la taca, no la mitjana. Cal comptar vores (gradient, black-hat) i mirar retalls al 300–400 % amb el WOW obert.
- Comparar amb «l'HDR lineal Vixen» no prova que sigui corona real: l'HDR és també una fusió en el temps amb la mateixa franja.
- Corregir la base (V75) no canvia res visible: els filtres no es recalculen sols. Pere ho va demostrar: interpolar la base lineal no arreglava els negres; interpolar el ràster del WOW bilateral sí.

## 3. Regles (per a la skill i per a qualsevol filtre futur)

1. **Cap filtre no pot veure la franja escombrada per la Lluna.** Abans de calcular qualsevol filtre, l'entrada ha de tenir r < 456 + recorregut + ala (≈ 496 px, mesurar-ho a cada versió) tractat com a «sense dada» (farcit A des d'aquest radi), o substituït per dada d'un sol instant (fotograma sencer de C2, norma del perímetre lunar).
2. **Els filtres són ràsters estàtics:** si la base canvia, els filtres es recalculen; si no es poden recalcular, el pedaç va al ràster del filtre, no a la base.
3. **Un artefacte a la corona interior es busca primer als ràsters dels filtres** a la franja 456–500, capa a capa (retorna_passos), i es jutja amb vores, no amb mitjanes.
4. **El limbe de display és un sol instant:** silueta R 456,0 (C2); tot el que hi ha a 447–456 a la base és agregat i no s'ensenya (V74/V75: base fosca al nivell de l'earthshine sota el limbe; producte lunar amb l'alfa a la silueta).
5. **El compost desat per Photoshop porta les capes de marques pintades:** no mesurar-hi mai dins de les marques; recomposar sense elles.

## 4. Altres aprenentatges d'aquest pas (V74 → V76)

- **Taca de l'earthshine (m6):** és als RAW Vixen de 10 s (llum dispersada, −0,5 % aparellat per anells, −1 % amb màscares; fixa en coordenades lunars; també a la Sony); la corba del revelat l'amplifica ×8–10 al nivell més fosc del disc. Cap model de vel (nuclis 3/160 px, dipol, vel 2D de V71, vel físic en lineal) la treu sense canviar el focus de llum de la Lluna o imprimir estructura del RAW. Cura pendent: ESF de la PSF Vixen al limbe lunar per sector → vel = corona ⊗ PSF. Mentrestant Pere l'ha aplanada a mà (Camera Raw + local: −4,6 % → +2,1 %).
- **Producte lunar al limbe:** els últims 5–8 px del fotograma d'earthshine són llum del limbe (L* 10 → 25), no albedo; a més hi ha forats de la mediana (V50). El producte ha d'acabar a la silueta (alfa erf 456 σ 1) i el contingut a r ≥ 448 ha de ser el nivell del sector; sota el limbe la base ha de tenir el mateix nivell, i així la vora de la màscara a mà no es veu (V75: ressalt 6,3 → 2,2 L*).
- **Una màscara a mà que surt de la silueta tapa corona amb gris** (az 165–207 a V71–V74): l'alfa del producte ho limita sense tocar la màscara.
- **Fotos de Pere (76/96) en mode normal:** el seu cel de 1/15 s (L* 55) contra corona L* 75–86 fa vel i solc (−5…−19 L*) a l'oest. Cura només amb el seu sí (clau de lluminància sobre el ràster de la foto).
- **Flux d'agents amb escèptic** (3 lectors + 1 verificador, 1 M tokens): l'escèptic va refutar 2 afirmacions del lector de la taca (factor V71 equivocat; «Claridad de Pere» sense prova). No lliurar cap diagnosi d'un sol lector.
- **Decisió de Pere (excepció declarada a la Torre de Pisa):** interpolar a mà els ràsters dels filtres a la franja i pujar els negres del disc amb Camera Raw; V76 porta aquestes correccions com a capa a dalt (223) perquè pugui seguir treballant. La cura a l'origen (§3.1) queda pendent del backup de `output/v58_correccions_20260913/sources` (base_G, support).

Fitxers: `4-RESULTATS/v74_marques_v71_20260917`, `4-RESULTATS/v75_marques_v74_20260917` (§7: comparació amb V75_Corretgit.tif), `3-RECERCA/tools/v75_marques_v74_20260917/agents/`.
