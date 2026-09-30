# 127 · La recerca d'earthshine: totes les versions amb la mateixa vara, i l'SNR

**30 d'agost de 2026 (matinada).** Ordre de Pere: «n'has fet de millors; potser
amb una sola foto de 8 s de la Sony hi ha més qualitat; l'SNR d'apilar
3×10 s Vixen + Sony ≥1 s ha de ser molt més gran; sospito que no tens en
compte la geometria; investiga a fons, contrasta el pla amb Codex xhigh i
executa'l desatès.» Inventari complet + diagnòstic + producte V3.

## 1. El diagnòstic: la geometria era bona, el VEL era el coll d'ampolla

Tres mesures que ho separen:

1. **Registre lunar entre fotogrames: NET.** Correlació de fase de
   l'estructura lunar (vel restat) de cada fotograma contra la referència:
   residuals **≤0,26 px** (l'únic 0,61 px és DSC06999, amb pic 0,07 — mesura
   dominada pel seu vel). El registre no emborrona res.
2. **Blur intrínsec, declarat i no corregible**: la Lluna es mou 0,585″/s
   respecte del marc solar → **2,7 px** (10 s) i **2,2 px** (8 s) del llenç
   DINS de cada exposició. Igual per a tothom; no és de l'apilat.
3. ⛔ **El coll d'ampolla era la RESTA DEL VEL**: el polinomi 2D ajustat fins
   a r<0,975 s'empassava el gradient del limbe i contaminava tot el disc.
   Ajustat NOMÉS dins r<0,85 (regió declarada per física: el gradient del
   vel s'accelera cap al limbe), cada fotograma sol passa de ~0,78 a
   **0,86-0,90** de correlació amb el mapa LROC.

**I la resposta a la pregunta de Pere**: sí, una sola foto de 8 s (DSC06987,
neteja bona) fa **r=+0,857** i superava el producte lliurat (0,777) — però
l'apilat ben fet la supera: **+0,876** i SNR ×3 (13 contra 4-5).

## 2. Totes les versions amb la MATEIXA vara

Vara única: neteja v3 + validació al marc V21 (σ=8, r<0,85 erosionat,
mapa LROC a l'orientació PREDITA, control nul girs 40-320°).

| versió | r(LROC) | z |
|---|---:|---:|
| 15-08 `Earthshine_FINAL` re-mesurat (producte, halo Moffat) | +0,655 | 3,4σ |
| 15-08 stack Sony 2×8 s (lineal, neteja v3) | +0,813 | 9,3σ |
| **DSC06987 SOL (8 s Sony)** | **+0,857** | 9,7σ |
| 572A2984 sol (10 s Vixen) | +0,875 | — |
| Sony apuntament 1 (2 fot) | +0,846 | 9,7σ |
| Vixen 3×10 s | +0,866 | 11,1σ |
| producte V2 lliurat ahir (ajust fins 0,975) | +0,777 | 9,1σ |
| **PRODUCTE V3 (8 fotogrames)** | **+0,876** | **10,9σ** |

L'encaix del marc del 15-08 amb el nou: rotació 316,0° trobada per
correlació amb la mateixa dada (r=+0,755), coherent amb la geometria.
⏭️ **La inversió Sony↔Vixen entre el 15-08 i ara té explicació documentada**:
el màster dark de 10 s del R6 del 15-08 duia el pedestal a 511 en lloc de
512 (⚠️ ja anotat a research/73/74: un 5 % del fons de l'earthshine) i la
cadena `Eclipse determinista` del 27-08 el va recalibrar — per això el Vixen
d'ara és el tren net (r sol +0,87) quan al 15-08 fallava (0,40 a mitja escala).

## 3. L'SNR, mesurat per banda (senyal per creuades entre components
independents; soroll per parells del mateix component; σ=8, comptes lineals)

| banda (px) | senyal | soroll/fot Vixen | ap1 | ap2 | SNR apilat | Wiener g |
|---|---:|---:|---:|---:|---:|---:|
| 0-4 | 0,72 | 4,3 | 3,8 | 10,2 | 0,3 | 0,06 |
| 4-8 | 0,74 | 0,56 | 0,87 | 9,3 | 1,6 | 0,71 |
| 8-16 | 1,06 | 0,24 | 0,45 | 14,9 | 5,0 | 0,96 |
| 16-32 | 1,60 | 0,13 | 0,26 | 19,7 | 14,1 | 0,995 |
| 32-64 | 1,93 | 0,11 | 0,20 | 14,4 | 20,0 | 0,998 |
| >64 | 1,94 | 0,14 | 0,20 | 6,3 | 17,2 | 0,997 |

- El senyal lunar viu a les bandes 8-64 px; per sota de 8 px no n'hi ha
  (SNR<1,6) — **el suavitzat deixa de ser un σ a ull i passa a ser el filtre
  de Wiener g=SNR²/(1+SNR²) per banda**.
- Pesos per banda: Vixen 70-81 %, Sony ap1 19-30 %, ap2 ~0 % (el seu vel
  fluctua entre fotogrames: el parell el detecta).
- El destripat Bayer passa a tenir porta: mediana de ratlles per fotograma
  **6,52 → 1,62** → ADOPTAT (el de la v2 s'havia adoptat sense porta).

## 4. El producte V3 i les seves portes

- **r(LROC) = +0,876 · control nul −0,062±0,086 → 10,9σ** · màxim de
  l'escombrada d'orientació **exactament a 0°** · contrast real 0,30 %.
- Porta del vel per regions: nucli (r<0,85, poli 2D grau 4) **r=+0,831**;
  vora (0,85-0,95, mediana+Fourier azimutal k≤2 per anell) **r=+0,368** —
  la vora és mig senyal mig residu i l'amplificació de la capa hi va
  esvaïda (0,92→0,96), DECLARAT.
- Capa: monocroma (G), disc fins a 0,985 R☾ (452 px visibles), amplificació
  ×66 declarada, tanh ±2,5σ, fosca de limbe 22 % display.

Eines: `v21_earthshine_v3.py` (neteja per regions + SNR per banda),
`v21_earthshine_v3_final.py` (pesos/Wiener/portes/validació),
`v21_capa_earthshine4.py`, `v21_munta8.py`. Mesures: `cau_v21/earthshine3_*`,
`v3_bandes.json`. Inventari complet de les 9 versions històriques (V0-V8 amb
fitxers i avisos): al transcript de la sessió del 30-08 i resumit aquí.

## 5. Regles noves que en surten

⏭️ **La regió d'ajust d'un model de fons es declara per física i es valida
amb una porta pròpia per regió** (nucli/vora per separat contra el jutge
extern) — mai un sol número global que barregi regions de qualitat diferent.
⏭️ **Tota versió nova es compara amb les velles AMB LA MATEIXA VARA** abans
de lliurar-la (la taula de §2 és el precedent; el 29-08 es va lliurar una
capa pitjor que un fotograma sol sense saber-ho).
⏭️ **El suavitzat d'un producte de senyal feble surt del Wiener mesurat per
banda**, no d'un σ triat a ull.

## 6. El contrast amb Codex (xhigh) i la V4

El pla es va sotmetre a Codex (estrategia/xhigh, tema `earthshine-v3`).
Veredicte: **ATURA'T abans de l'execució desatesa** — la detecció del 126 no
cau, però la V3 tenia quatre forats. Tots acceptats i executats:

1. ⛔ **G-AZI: fora el model azimutal k≤2 de la vora.** La seva prova
   sintètica: transferència **0,000** als modes lunars k=1 i k=2 (el model
   els elimina exactament), i el LROC real a 0,85-0,97 perd el **38 % de
   l'RMS**. La ciència es declara vàlida a **r<0,85** i prou; la vora de la
   capa és pedestal cosmètic amb l'estructura esvaïda des de 0,85 (declarat).
2. ⛔ **G-VEL: la selecció de r_fit=0,85 va ser assistida pel mapa** → cap
   "z" nou no és una detecció: la **significança citable és la del
   `research/126` (7,0σ)**, i la r de la V4 és millora de producte. El nested
   null de 999 surrogats que Codex oferia com a alternativa queda DESCARTAT
   per cost, dit explícitament.
3. **G-PESOS: dos nivells.** Dins de component, pes ∝ t_exp (model fotònic
   declarat; abans 8 s i 2 s entraven iguals — defecte real). Entre
   components, UN pes escalar (senyal/soroll² a la banda 8-64); cap pes per
   banda (invalidable amb 3+2+3 fotogrames). Component NOU: **Vixen 3×2 s**.
   Pesos finals: **vixen10 76,4 % · ap1 19,1 % · vixen2 4,5 % · ap2 0,03 %**.
4. **G-RATLLES: destripat OFF per defecte** amb porta held-out per meitats de
   files (la porta de la v2/v3 era circular): millora held-out **+48 %** →
   adoptat legítimament.
5. ⏭️ **G-INJECCIÓ, la porta que va caçar un defecte nou**: la transferència
   del pipeline a una textura cega d'escala 10 px era **0,83** — el "Wiener
   per bandes" fet amb DIFERÈNCIES DE GAUSSIANES té cues (la "banda 4-8"
   arriba a λ~40 px) i menjava el 17 % del senyal. Refet en **Fourier amb
   bandes netes en λ** → transferència **0,958 PASS**. ⛔ Regla: un filtre
   per bandes DoG no és un filtre per bandes; les portes d'injecció existeixen
   per això.

**La V4 final**: r(LROC) = **+0,877** (nul −0,061±0,083; màxim d'orientació a
0°), injecció 0,958 PASS, destripat held-out PASS, 11 fotogrames, contrast
real 0,31 %. Deutes declarats: variància no propagada (l'SNR és un proxy);
intersecció de cobertura (94 % de l'àrea) en lloc d'unió; el model de vel
podria millorar amb un halo físic per component (la via del 15-08) — cua
oberta. Eines: `v21_earthshine_v4.py`, `v21_capa_earthshine5.py`,
`v21_munta9.py`; rebut `cau_v21/earthshine4_rebut.json`.

## 7. Els defectes marcats per Pere (31-08) i la capa natural

Pere va marcar en blau a `defectes_lluna.png`: (1) tot l'anell del limbe
«gruixut i sense detall, simplement pintat en gris», i (2) «un cràter on no
hi hauria de ser». I el criteri estètic: DSC06987_cal ensenya un earthshine
perfectament natural. Tres diagnòstics, tres cures:

1. ⛔ **El «cràter» era una MOTA DE POLS DEL SENSOR R6.** Jo l'havia batejat
   d'Aristarc sense comprovar-ho: la posició predita d'Aristarc per
   l'efemèride és (294, 181) del marc de capa i el punt era a (330, 528) —
   350 px lluny. Obertura fixa: **+33,4 ± 6,4 comptes als 6 fotogrames Vixen
   i +5,0 ± 4,5 a la Sony** (una estructura lunar real la veurien tots dos
   trens igual). Fix al sensor a (3579, 2374). ⚠️ I **NO és al flat fi del
   22-08** (correlació 0,00 amb el defecte mesurat: la pols es va moure en
   10 dies) — el flat posterior no pot corregir motes del dia de l'eclipsi.
   Cura: **pes Vixen → 0 en 22 px al voltant de la mota; la Sony, neta,
   omple**. El producte científic puja a **r = +0,887**.
2. ⛔ **L'anell pintat**: la capa V4 tenia pedestal pla + fosca cosmètica de
   0,85 a 1,0. Fora tot: la capa nova és el DISC LINEAL APILAT (vel i gra
   inclosos, com el fotograma real), i l'estructura de la vora surt de
   l'extensió del model del nucli fins a 0,975 (estètica declarada; la
   ciència acaba a 0,85, amb el realç reduït ×0,35 a la vora).
3. **El render natural**: com el gest de Pere amb DSC06987_cal — estirament
   lineal de finestra en monocrom, amb DUES transformacions declarades: el
   vel del model comprimit ×0,30 (el residu — mars, cràters, gra — passa
   1:1) i realç multiplicatiu ×12 de l'estructura validada. Cap corba de to
   de corona (aixafava el contrast del disc a res).

⛔ Lliçó de la mota per al 2027 i per a tot flat: **una mota de pols és del
DIA de la captura** — cap flat fet dies després no la porta (aquí, 10 dies i
correlació 0,00). L'única defensa és el dither (el salt d'apuntament de la
Sony aquí ha fet de dither accidental i ha salvat la zona) o flats del mateix
dia.

## 8. El walking noise (31-08, segona marca de Pere) i els pesos que giren

Pere va marcar traços diagonals «per tota la lluna» com a walking noise, i va
demanar més pes per a la Sony (especialment DSC06987). Tenia raó a totes dues,
i estan lligades:

1. **El walking noise és real i és el FPN del sensor caminat.** El gra fi del
   producte surt orientat a **75°** i el moviment de la Lluna sobre el sensor
   Vixen és a **77°** amb 12,3 px de recorregut: el patró fix del sensor
   s'estampa desplaçat a cada fotograma i deixa traços. ⏭️ La prova fina: la
   correlació de banda fina entre germans **creix quan el desplaçament
   disminueix** (Vixen 2 s, Δt 3 s → r=0,44; Vixen 10 s, Δt 13 s → r=0,03;
   Sony ap2, deriva 0,18 px/s → r=0,65).
2. ⛔ **L'estimador de soroll per parells NO veu el FPN** (les diferències
   entre germans el cancel·len a lag petit): el soroll del Vixen estava
   subestimat i el seu pes inflat. Estimador corregit per a tots els
   components: soroll² = potència total de banda − senyal² (senyal per la
   creuada entre SENSORS diferents, neta de FPN). **Pesos nous: Sony ap1
   51,2 % (DSC06987 sol: 41 %) · Vixen10 33,9 % · Vixen2 14,8 %** — el gir
   que Pere demanava, amb la mesura al davant. r es manté (+0,885) i la
   injecció PASS (0,957).
3. **El flat fi del 22-08 REFUSAT per porta** també per al FPN: aplicar-lo
   PUJA el gra per fotograma (4,96→7,20 al Vixen10): aquell màster porta
   soroll propi i la seva PRNU no redueix la del dia de l'eclipsi.
4. **El display de la capa passa pel mateix Wiener mesurat** (la base lineal
   portava el gra cru): l'anisotropia de la banda fina de la capa cau de
   **43× a 2,0×** (el residu a 75° és senyal allargat pel blur intrínsec de
   l'exposició, declarat i no corregible sense deconvolució).

⏭️ Regla: **el soroll d'un component mai no es mesura NOMÉS amb les
diferències entre els seus fotogrames** — el FPN comú s'hi cancel·la; cal
l'estimador per potència total menys senyal creuat entre sensors independents.

## 9. La V22: l'earthshine amb les dues vares al costat (31-08, vespre)

Per ordre de Pere: **`CapesTotalsV22.psb`** (fitxer nou; la V21 intacta) = les
seves 14 capes byte a byte + `EARTHSHINE natural v2` (visible) + dues capes de
comparació OCULTES i alineades per construcció al mateix marc lunar:
`COMPARA · DSC06987 SOL` (el fotograma de 8 s amb la MATEIXA recepta de
display: vel ×0,3, Wiener mesurat, realç ×12 — parpelleig just) i
`COMPARA · MAPA LROC WAC (NASA)` (l'orientació predita per l'efemèride, res
ajustat) + `ESTRELLES`. Porta Photoshop: OBRE · 18 capes. Eines:
`v22_capes_extra.py`, `v22_munta.py`; vista
`V22_tres_capes_parpelleig.png`. ⚠️ Incidència reparada: una substitució de
nom no aplicada va fer que el primer muntatge sobreescrivís la V21; re-muntada
amb `v21_munta11.py` (OBRE · 16 capes) i la V22 re-muntada al seu fitxer.

### §9 bis · El re-ancoratge al disc del muntatge (31-08, nit)

Pere: «sobra un espai enorme al limbe dret; agafa de referència les capes 11
i 12». ⛔ **Tenia raó i el mecanisme és net**: jo ancorava les capes lunars al
centre de la Lluna del fotograma base (t=70 s de la totalitat), però el disc
del muntatge (les perles de C2) és la Lluna A C2 — i la Lluna es mou 0,585″/s.
Mesurat el limbe de les seves capes 11 i 12 (ajust de cercle pel màxim de
gradient, 695-720 punts, rms 0,8-1,1 px; les dues capes coincideixen a <1 px):
**centre (6481,8 · 6758,8), R = 453,5 px** — el meu ancoratge era a
(+16,4, +6,2) px i un 0,45 % més gran (l'astromètric vs el fotogràfic).
Cura: les tres capes reescalades ×0,9956 i re-ancorades (verificació:
desviació de centres 0,0 px), i la vora reparada per construcció (camp suau
radial-azimutal 434-446, extensió amb decaïment fins a 460, màscara fins a
458): cap escletxa entre el disc i la corona. ⏭️ Regla: **l'ancoratge d'una
capa lunar al muntatge es mesura DEL MUNTATGE** (les capes de Pere porten
retocs manuals de posició), mai de l'astrometria del run.
