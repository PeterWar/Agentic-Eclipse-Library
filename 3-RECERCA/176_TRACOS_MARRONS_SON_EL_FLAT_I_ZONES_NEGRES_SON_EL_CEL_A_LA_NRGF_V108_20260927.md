# 176 · Els traços marrons són el flat; les zones negres són el cel dins de la NRGF (V108, 26–27-09-2026)

Encàrrec de Pere, sobre la V107:
1. «Els artefactes marrons documentats a la V92 segueixen allà, és el primer tema a resoldre.»
2. «Ajustar la capa dels filtres perquè no es notin tant les zones negres.»

- Informe i xifres: `4-RESULTATS/v108_20260926/RESULTAT.md`, més els INFORME.md de cada ronda.
- Codi: `3-RECERCA/tools/v108_20260926/`.
- Producte: `1-PHOTOSHOP/V108.psb`, candidata.

## Què s'ha après
1. **⛔ Els traços marrons NO són unions de camp de la Sony** (la hipòtesi de la V93 queda refutada: cap pes no canvia quan es travessen). **Són el flat.**
   - El FLAT_RADIAL de la cadena (F0.3) només té la part radial.
   - Els flats reals de les dues càmeres tenen estructura fixa al sensor: línies de files, arcs, pols i textura de guany.
   - Passa a cada apilat, i els filtres que normalitzen localment la multipliquen per ~100: RHEF locals 45/46, WOW 55, ACHF 49, MGN 54 i NRGF 41.
   - Una línia de −1…−2 ‱ a la base es converteix en −150…−200 ‱ al compost.
2. **La cura és un flat 2D, al pis de la calibració** (`flat2d_v5/`). Són 5 rondes, cadascuna amb un verificador adversari.
   - **Sony:** C comuna als canals i sense els anells cromàtics de la llum dels flats.
     - La prova A − B (el mateix cel vist amb dos llocs del sensor separats 749 px) mostra que aquests anells no són a les llums (β = 0,00).
     - Només es queden les línies de files.
   - **Pols:** porta per estructura, amb el cel anul·lat i encongiment bayesià de grup. On la pols s'havia mogut entre els flats i l'eclipsi (â ≈ 0), només textura fina.
   - **Congelat al control, perquè l'únic canvi sigui el flat:** fusió, pesos, franja i REC de la 56. Sense congelar, la Vixen guanyava 10 punts de pes a 3–6 R☉.
   - **Protuberància:** els píxels fràgils del nucli (G' post-matriu ≈ 0, f < 0,002) es congelen al control.
3. **Resultats del flat 2D:**
   - T2 curat.
   - **T1 NO és del sensor:** és al mateix lloc del cel als dos apuntaments de la Sony. No es pot treure sense inventar.
   - **Prova s:** s = (E_després − E_abans)/|Δ|²; −1 = cura, +1 = injecció; el nul, a la mateixa imatge.
   - **Trampes que ha destapat la prova:**
     - el color injectat per la part cromàtica que no és a les llums;
     - les taques «noves» de pols moguda;
     - la cerca de ±60 px que trobava una recta de files i no T2.
   - **Per mesurar un traç:** geometria FIXA i nuls a la mateixa imatge (abans i després), mai una cerca.
4. **El calaix 0 del FLAT_RADIAL de la cadena és buit** (r < 18,5 px del RAW) i l'omple la mediana del perfil. D'aquí surt el «ghost de l'eix òptic» de l'agost (+49 % a la Sony). Ara és inert, perquè la fusió hi posa pes 0 a l'apuntament A; si mai es descongela, torna.
5. **⛔ Les zones negres (més fosques que el cel a 1,3–4,5 R☉) les fabrica la NRGF.**
   - Normalitza cada anell com si tota la variació fos corona, però al camp exterior la variació és el gradient del cel: cel ×1,54 entre sectors al compost, contra ×1,05 a la base.
   - La corona hi és només un 4–11 % per sobre del cel, i un buit enfosquit un ~19 % hi cau per sota.
   - Emmascarar el filtre amb la seva pròpia imatge (doc. 175) no és la cura.
6. **La cura triada, opció (a)** (`negres_v2/g1_nrgf_genoll.py CEL_G_MAX_T_e30_W_H0`):
   - es treu el gradient del cel del numerador de la NRGF;
   - s'hi posa un genoll continu que no deixa baixar la pila de Multiplicar per sota del cel (el més restrictiu de dos models de cel);
   - **no és una cura d'origen pura:** el CEL sol les empitjora, fins al 19 %, i el genoll depèn de la composició de la V107;
   - **cost** (compost desat): el cel es mou (dalt ×0,85–0,89, baix ×1,29–1,32) i la flamarada del sud baixa a ×0,53–0,67 a 4–5,5 R☉;
   - **la cura d'origen del residu**, les capes en Superposar (56, 51, 55), és un guany per banda segons el S/N dins de cada operador (research/156), i està per fer.
7. **Mesura sempre al compost que desa el Photoshop,** amb les capes d'ajust. L'emulació sense ajustos subestimava el cost de la flamarada (×0,78 contra ×0,74 a 4,5 R☉, i al sud molt més).
   - La «flamarada» s'ha de mesurar sense el gradient del cel (treure'n els harmònics m ≤ 3): si no, surt ×0,45 i és fals.

## Trampes
- La memòria de la fusió i de l'apilat de la Vixen arriba a 16–17,6 GB: han de córrer sols.
- `cadena_v108.sh` no s'ha d'editar mentre corre.
- Abans de desar, comprova a mà el SHA del PSB de pas.
- El compost fusionat i la miniatura del PSB de pas són els de la V107 fins que el Photoshop el desa.
- La carpeta `4-RESULTATS/v108_20260926/` fa ~290 GB. A la Paperera hi ha diversos centenars de GB, amb manifests (`MOVIMENTS_PAPERERA_*.jsonl`).
