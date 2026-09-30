# 149 — Què causava les marques de la V33: la V33 mateixa, i el que hi ha a sota

07-09-2026 (nit). Claude, claim `CLAUDE_MARQUES_V33_20260907`. Pere: «no vull que corregeixis estèticament el problema sense atacar-lo d'arrel; tampoc vull sacrificar detall; què els està causant?» i `V33_Artefactes.psb`. Codi: `research/tools/revisio_marques_v33_20260907/`. Rebuts: `output/revisio_marques_v33_20260907/4-rebuts/`. Vistes: `.../lliurables/vistes/`.

## 1. Resultat en un minut

**La V33 queda retirada com a mètode.** Els 29 traços de Pere a la V33 (7 al MGN, 12 al WOW, 10 al WOW bilateral; cap a les capes de cadena ni a NRGF/RHEF) són, a les finestres comparades a 1:1, costures que **la V33 va fabricar**: al mateix lloc, el MGN de la V32 és uniforme i el de la V33 té la costura exactament on el suavitzat canvia de σ (dins nítid, fora borrós). `V32_vs_V33_L08-M04.png`, `V32_vs_V33_L08-M02.png`, `V32_vs_V33_L09-M10.png`. La causa mecànica: f3.suavitza_sn posa σ = 0 per sota de 0,7 px i el mapa de coherència canvia per tessel·les; on el soroll comença a manar la resolució salta de cop, i un filtre que normalitza pel contrast local hi dibuixa un arc. Els quatre arcs de 3,3–4,4 R☉ del WOW són el mateix mecanisme (gradient del mapa σ dins del traç). **És l'exemple exacte del que la norma nova prohibeix.**

Sota la V33 hi ha el que la V32 ja tenia i que el 147 va deixar mig dit. Mesurat a la font:

| candidat a causa | mesura | veredicte |
|---|---|---|
| nivell: fotogrames veïns discrepen a l'altiplà (amb k, offsets c03 i camps φ de la V32) | Vixen 10 s/2 s ≤ 0,1 %, 2 s/1 s ≤ 0,1 %, 1 s/0,5 s −0,2 %, 0,5/0,25 −0,3…−0,4 %, 0,25/0,125 −0,1…−0,7 %; Sony 8 s/2 s ≤ 0,06 %, 2 s/1 s ≤ 0,3 % (`A10b_linealitat_parelles.png`) | no és la causa als 2 s i 10 s; residu de 0,2–0,7 % als curts (limbe) |
| no-linealitat del sensor prop de la saturació (resolució completa, DN absoluts, 3 sectors, subpla G) | **Vixen: lineal fins al 85 % (±0,13 %)**, −0,27 % al 92 %, −0,78 % al 97 %. **Sony: −0,4/−0,5 % del 60 al 85 %, −0,9 % al 87 %, −1,2 % al 92 %, −1,7 % al 97 %** (`R33_linealitat_sensor.png`) | Vixen: no. **Sony: sí, defecte d'origen a corregir** (afecta les seves entrades a 1,56, 1,74, 2,7 R☉ i el desacord A/B) |
| ⚠️ prova anterior per cel·les d'1/4 (a10) que deia −0,5…−2 % a la rampa de la Vixen | artefacte de la prova: mitjana ponderada per finestra dins de cel·les de 4×4 a la rampa | descartada (trampa: no mesuris linealitat amb cel·les ponderades) |
| resolució: els fotogrames llargs són més borrosos (moguda de la muntura, 0,28 px/s) | transferència 10 s/2 s corregida pel soroll (parell 2 s/2 s): 0,98/0,94/0,96/0,98 a λ 3–4/4–6/6–8/8–12 px | 2–6 %: no és la causa |
| **soroll: el gra del compost cau de cop on entra cada fotograma** | entrada dels 10 s (10→90 % del pes) en 60 px (az −50°) i 104 px (az 110°); rms fi 0,124 → 0,075 % i 0,194 → 0,087 % en 44 i 136 px (`R33_roi_rampa2.json`); a la base V32, −24 % a 1,21, −13 % a 1,33, −18/−23 % a 1,96–2,05 (A8 del 147) | **causa real a la V32** per als filtres que normalitzen pel soroll (MGN, WOW): un graó del 40 % en 40 px es veu com un contorn |
| **canvi de tren Vixen→Sony (2,0–2,65 R☉)** | gra fi: Vixen 0,10 %, Sony B 0,137 %; la base passa de 0,089 (2,3) a 0,137 (2,65): +54 % en 0,3 R☉ | **causa real**: la fusió és per radi (smoothstep) i entrega el camp a un tren més sorollós |

## 2. Per què el gra fa graons

Els pesos LDIC són ∝ t_exp × finestra. Els tres 10 s de la Vixen pesen 5× més que els 2 s: només que la finestra de sostre passi de 0,2, el compost ja és «dels 10 s». La finestra actual va del 70 al 85 % de la saturació (una rampa de 15 punts): en radi són 16–60 px. Una rampa gradual (smoothstep del 35 al 85 %) només duplica l'amplada de l'entrada (60 → 136 px; 104 → 156) i del graó (44 → 88; 136 → 196 px), sense canviar el gra final (`R33_roi_rampa2.json`, `ROI2_rampa_MGN_az-50.png`). L'origen de debò és de captura: salts de 5× entre exposicions (2 s → 10 s) amb tres fotogrames per esglaó; Druckmüller entra cada fotograma amb 1 EV de salt i 8–50 aparicions per esglaó (research/105; requisit 2027 al §1 quater de CLAUDE.md). Per a la dada del 2026 el que queda a l'origen és (1) l'entrada gradual i (2) fer servir TOTA la dada allà on és menys sorollosa (fusió per variància entre trens i entre apuntaments), que baixa el gra sense tocar cap detall.

## 3. El que NO són (rectificació del 147 mantinguda)

L'estructura interior que els traços ressegueixen és corona (A7 del 147: correlació 2D Vixen×Sony +0,67, nul −0,01). El que MGN/WOW hi afegeixen són contorns de canvi de gra (V32) o de canvi de σ (V33). Cap dels dos és de la corona i cap dels dos es cura suavitzant.

## 4. V34, a l'origen (cap suavitzat, cap retall, cap pèrdua de detall)

1. **Linealitat de la Sony corregida** amb la corba mesurada (LUT en x = DN/(sat−ped), mediana de parelles i sectors), aplicada al pla calibrat abans del flat. Vixen: sense correcció (lineal ±0,13 % fins al sostre).
2. **Entrada gradual dels fotogrames**: finestra de sostre smoothstep del 35 al 85 % de la saturació als dos trens (píxels lineals a la Vixen; a la Sony, corregits). Pesos A1 i camps B1 recalculats.
3. **Fusió per variància**: Vixen sola fins a 2,0 R☉ (resolució), i de 2,0 enfora pesos ∝ 1/σ² mesurats a cada tren (variància local del gra, suavitzada), en lloc del smoothstep per radi; A i B de la Sony fusionats per variància al seu solapament (guany 2D A→B, ghost de 3 R☉ exclòs) amb porta: correlació amb la Vixen a 2,5–5 R☉ millor que B sola, o es descarta.
4. Filtres amb la recepta exacta de la V32 (mapa de resolució congelat de la V29, com abans). Res del snmap.
5. PSB lleuger: base lineal V34 + les 10 capes, amb la mateixa vara (gra per radi, polars V32|V34, retalls a les marques V32 i V33).

## 5. Fitxers

`revisio_marques_v33_20260907/`: `extract.py`, `catalog.py`, `a9_causa.py` (graó de soroll, fotogrames, color, σ V33 per marca), `a10_linealitat_entrada.py` (⚠️ prova per cel·les, refutada), `a10b_parelles.py` (parelles a l'altiplà i a la rampa), `roi_rampa.py`, `roi_rampa2.py` (ROI amb k/offsets/φ, tres rampes), `roi_blur.py` (transferència per bandes), `roi_linealitat.py` (corba de linealitat per sensor). Rebuts `R33_*.json`.
