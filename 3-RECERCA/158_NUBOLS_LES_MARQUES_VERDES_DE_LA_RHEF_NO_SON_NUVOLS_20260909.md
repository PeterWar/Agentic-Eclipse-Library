# 158 — Nubols.psb: les marques verdes de la RHEF no són núvols (i què són)

**09-09-2026, nit.** Pregunta de Pere mentre revisa la V40: «mira't `nubols.psb` a Downloads, el marcat en verd podrien ser núvols molt i molt fins? Jo ho dubto, però pregunto per si de cas. Qui va crear el tipus de filtre que ho ensenya i per què?». Resposta curta: **no són núvols**; el que la RHEF ensenya a 5–13 R☉ és corona feble més el cel de la totalitat (asimetria de brillantor compartida pels dos trens), i el gra fi de dins de la marca del NE és un **patró fix del sensor de la Vixen** que camina amb la deriva de la muntura. Eines: `research/tools/v39_20260909/g2_nubols.py`, `g2b_nubols_escales.py`, `g2c_deriva_i_desplacament.py`, `g2d_nubols_llenc.py`; `b2_meitats.py` accepta ara `inici`/`final` (primera i segona meitat de la totalitat, per grup d'exposició). Rebuts: `output/v39_20260909/4-rebuts/G2*.json`; vistes: `output/v39_20260909/lliurables/vistes/G2*.png` i `IA/output/v40_20260909/lliurables/vistes/G2_nubols_*.png`.

## 1. Què hi ha al fitxer

`~/Downloads/Nubols.psb` (2,04 GB, 5 capes): `00 Base amb cel · V32` (Normal), `P01 NRGF · V38` (Multiplicar, 99/255 = 39 %), `P02 RHEF · V38` (Normal, 39 %), `05 ACHF fi 2-48 · V38` (Superposar 7 %), `04 ACHF micro 1-16 · V38` (Superposar 3 %). ⚠️ La capa 04 hi és **desplaçada 211 px a la dreta** (caixa 211…10762): a 3 % no es veu, però és una capa moguda. El verd és pintat directament a la capa RHEF (pinzell tou; diferència contra la `P02 RHEF · V38` de la `V38.psb`: R −0,04, G +0,01, B −0,07). Cinc regions, totes a la meitat nord:

| marca | Mpx | r (R☉) | azimut | què conté |
|---|---:|---|---|---|
| M1 | 8,7 | 4,6–13,1 | −76…−30° | quadrant NE fins a la vora del llenç; la Vixen només en cobreix el 27 % |
| M2 | 5,2 | 2,9–7,7 | −170…−116° | l'ala NW amb els streamers grans i el ventall difús |
| M3 | 1,2 | 3,0–7,4 | −32…−14° | lòbul del NE a 5,5 R☉ (on el verd és més dens; caixa 7500–7800 × 2740–3120) |
| M4 | 0,9 | 9,7–10,7 | −145…−125° | cantonada NW del llenç (fora de la Vixen i fora de l'abast de Brno) |
| M5 | 0,3 | 6,2–7,0 | −117…−84° | arc prim al nord (fora de la Vixen) |

## 2. Els tres jutges, al llenç sencer (1/4, canal G)

Un núvol prim, per fi que sigui, és **davant dels dos telescopis alhora** i el vent el mou: un cirrus a 2 m/s a 10 km recorre ~40″/s = 19 px/s, o sigui ~1000 px entre la primera i la segona meitat de la totalitat. Per tant (T) canvia entre les meitats temporals i (T') canvia **igual** als dos trens; la corona, el cel llis i els residus d'instrument no fan cap de les dues coses. (S) L'estructura estàtica compartida pels dos trens és del cel (corona o cel); la que no és compartida és d'un tren. (B) Brno confirma la corona i no comparteix el nostre cel.

Banda 64–512 px, sense la mediana per anell de 32 px (només estructura azimutal), lluny de les vores dels suports (64 px):

| marca | rms ln(inici/final) Vixen | control meitats aleatòries | rms Sony | corr(ΔVixen, ΔSony) | rms estàtic V / S | V×S estàtic | Brno 200 / 400 (fusió) | sostre Brno×Brno |
|---|---:|---:|---:|---:|---|---:|---|---:|
| M1 | 0,0003 | 0,0002 | 0,0005 | +0,14 | 0,0092 / 0,0051 | +0,60 | +0,06 / +0,28 | 0,66 |
| M2 | 0,0004 | 0,0002 | 0,0005 | −0,07 | 0,0347 / 0,0295 | +0,92 | +0,42 / +0,53 | 0,75 |
| M3 | 0,0003 | 0,0001 | 0,0004 | −0,08 | 0,0113 / 0,0118 | +0,95 | +0,38 / +0,37 | 0,81 |
| fora, 4–6 R☉ | 0,0004 | 0,0002 | 0,0004 | +0,06 | 0,0174 / 0,0046 | +0,33 | — | — |

Lectura: **el que canvia amb el temps és ≤ 0,04 % rms** (dues vegades el terra de soroll, i explicable per la barreja diferent de fotogrames de cada meitat: les exposicions de 10 s són al mig de la totalitat) **i els dos trens no veuen el mateix canvi** (correlacions ±0,1). L'estructura que la RHEF ensenya és **de 0,5 a 3,5 % rms, estàtica i compartida** (V×S 0,60–0,95); Brno en confirma de 0,1 a 0,7 del seu propi sostre: a M2 és sobretot corona (els streamers), a M3 la meitat, a M1 poc. La part compartida, estàtica i no coronal és la **brillantor del cel de la totalitat**, que no és uniforme (el cel és més brillant cap a la vora de l'ombra i cap a l'horitzó; `research/147` ja va trobar «la taca taronja de la RHEF és el gradient del cel ordenat per anells»). La dada no pot distingir aquest cel d'un vel **absolutament immòbil** durant 100 s; físicament no n'hi ha. El residu de núvols de la mateixa totalitat és el que van mesurar els parells de fotogrames del 25-08 (`research/102`: bandes de 0,1–0,5 % que es mouen amb el vent): en la suma de 100 s queda per sota del 0,04 %, 10–100 vegades per sota del que la RHEF mostra.

## 3. El gra fi de dins de M3: un patró fix del sensor de la Vixen

A la caixa 7500–7800 × 2740–3120 (5,1–6,0 R☉, pes Vixen 0,35, els dos trens hi són), per bandes:

| banda px | Vixen parell×senar | Vixen inici×final | Sony pA×pB | Sony inici×final | Vixen×Sony |
|---|---:|---:|---:|---:|---:|
| 2–4 | +0,32 | +0,01 | −0,01 | +0,02 | +0,03 |
| 4–8 | +0,58 | +0,01 | +0,11 | +0,08 | −0,01 |
| 8–16 | +0,70 | +0,17 | +0,25 | +0,18 | −0,02 |
| 16–32 | +0,81 | +0,58 | +0,42 | +0,33 | +0,21 |
| 32–64 | +0,98 | +0,89 | +0,87 | +0,74 | +0,36 |
| 64–128 | +1,00 | +0,98 | +0,98 | +0,96 | +0,47 |
| 128–256 | +1,00 | +1,00 | +1,00 | +1,00 | +0,74 |

La Vixen hi té una textura de 2–32 px que les meitats **aleatòries** comparteixen (no és soroll) però les meitats **temporals** no (no és del cel: la Sony tampoc no la veu). I la prova que ho tanca: la correlació creuada amb retard entre les dues meitats temporals (banda 8–32) té el pic **fora del centre**, amb el patró de la segona meitat desplaçat **(−7, +11) px** respecte de la primera (correlació al pic +0,59; a retard zero +0,33; control de meitats aleatòries: pic a (0, 0)). La deriva del Sol sobre el sensor de la Vixen entre les dues meitats, del registre F1.3 amb pesos ∝ exposició i passada pel mateix mapa geomètric de la cadena, prediu que un punt fix del sensor es mou al llenç **(−6,5, +10,4) px**. Coincideixen a 1 px en els dos eixos. És el mateix mecanisme que el «walking noise» del 31-08 (`research/127` §8): un patró fix del sensor (flat, PRNU, l'estriat diagonal del 116) caminat per la muntura. ⏭️ Per a la V41 això és una via **a l'origen**: aquest patró és estàtic en coordenades del sensor i es pot estimar (mediana de fotograma/compost en coordenades del sensor, com es va fer amb l'earthshine) i restar abans de fusionar; és la mateixa cosa que el «N_total/N_meitats 5–7× a 16–32 px» del `157`.

## 4. Qui va fer el filtre que ho ensenya, i per què

La capa on Pere ho veu és la **RHEF, Radial Histogram Equalizing Filter, de Gilly i Cranmer (2025, *Solar Physics*, doi 10.1007/s11207-025-02578-x)**, amb la **NRGF de Morgan, Habbal i Woo (2006, *Solar Physics* 236, 263)** a sota en Multiplicar. Tots dos van néixer per veure la corona blanca sencera en una sola imatge: la brillantor cau tres o quatre ordres de magnitud de 1 a 6 R☉ i cap corba global no pot ensenyar alhora els streamers del limbe i l'estructura de 5 R☉. La NRGF resta a cada anell la seva mitjana i el divideix per la seva desviació; la RHEF va un pas més enllà i substitueix cada píxel pel seu **rang percentil dins del seu anell**, sense cap paràmetre, de manera que cada anell surt amb l'histograma pla i el contrast ple. Per construcció, doncs, **cada anell ensenya a contrast ple el que hi hagi**: a 1,5 R☉ són els streamers; a 6–10 R☉, on el cel és 10–20 vegades la corona, és la variació d'un pocs per cent del **cel** i, a la Vixen, el seu patró de sensor. La RHEF revela; no certifica. Per això les marques d'aquest fitxer es responen amb els tres jutges de §2, no mirant la RHEF.

## 5. Trampes d'aquesta ronda

- La primera versió de `g2d` treia «la mediana per anell» amb el radi en R☉ en comptes de píxels: només feia dos anells i deixava tot el perfil radial dins de la banda de 64–512 px (V×S sortia 0,99 pertot, per la caiguda radial compartida). Corregit; els números de §2 són els bons.
- La correlació de fase (espectre blanquejat) amb màscara no serveix per mesurar el desplaçament d'un patró de banda estreta: donava pics de 0,08 i valors negatius a zero. La correlació creuada normalitzada per retard (`ncc_map`) sí. El signe del retard s'ha calibrat amb un desplaçament sintètic.
- Les meitats temporals de la Vixen no tenen el mateix soroll ni la mateixa barreja d'exposicions (les de 10 s són al mig): es comparen sempre amb el control de meitats aleatòries, mai soles.
