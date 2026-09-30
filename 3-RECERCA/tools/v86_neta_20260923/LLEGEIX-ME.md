# V86 neta — com es fa cada capa i com es regenera la cantonada

Tots els scripts de la V86 són en aquesta carpeta i treballen amb rutes relatives a l'arrel del projecte (la carpeta de `CLAUDE.md`).

**Entorn:** el primer Python que tingui numpy, scipy, opencv, numexpr, psd-tools i tifffile (avui `~/.venvs/eines-ia-py312`). Cap script no n'anomena cap de concret.

**Claim:** cada pas comprova que hi ha un claim viu a `.coordination/claim.lock` (SERIAL_WRITES) abans d'escriure. La construcció del 23-09 va anar amb `CLAUDE_V86_NETA_20260923`.

**Fonts:** la suma lineal reproduïda des dels RAW a `4-RESULTATS/v85_regeneracio_20260922/d4_baseline/products/sources` i els fotogrames de la caixa de la Lluna a `…/limb_frames`. Totes dues són de Codex (V85) i no es toquen.

## Ordre dels passos

| Pas | Script | Què fa | Surt a `4-RESULTATS/v86_neta_20260923/` |
|---|---|---|---|
| 1 | `a1_linealitat.py` | Comprova la suma lineal que alimenta els filtres: negatius, sostre, color, i que la base sigui una corba punt a punt. | `A1_LINEALITAT.json` |
| 2 | `a2_geometria.py` | Situa la Lluna de presentació (la teva capa Earthshine) i la trajectòria de la Lluna als 67 fotogrames. També marca la franja que va escombrar la Lluna. | `A2_GEOMETRIA.json`, `A2_geometria.npz` |
| 3a | `a3a_franja_un_instant.py` | Posa dada d'**un sol instant** a la franja escombrada. És la suma dels fotogrames amb t ≤ 22,3 s, amb:<br>• ≥ 8 dels 11 fotogrames per píxel;<br>• ≥ 1 px fora del limbe **observat** de cada fotograma (la distància del rebut va al radi de l'efemèride, 2,5 px més gran);<br>• pes de cada fotograma en rampa arran del seu limbe (1→3 px els curts, 2→6 px els llargs);<br>• buits del mosaic CFA omplerts (σ 0,8 px);<br>• matriu de color;<br>• nivell amb un factor constant per canal. | `A3A_franja_un_instant.npz`, `A3A_FRANJA_UN_INSTANT.json` |
| 3 | `a3_filtres.py E1`, `E6`, `E2`, `E3`, `E4` | Fa els 16 ràsters de filtre des de la suma lineal: a la franja, amb la dada d'a3a; fora del disc de presentació, amb el domini. Les etapes són independents i es poden córrer en paral·lel. Els operadors són a `v86_operadors.py`. | `filtres/`, `A3_E*.json` |
| 3b | `a3b_compara_v84.py` | Compara els filtres nous amb els de la V84 lluny del limbe. | `A3B_COMPARA_V84.json` |
| 4 | `a4_franja.py` | Continua els filtres als píxels sense dada tocant la Lluna: el disc i la tira d'≈1–2 px arran del limbe observat. Parteix de 2 px dins de la dada (prova de 0, 1, 2 i 3 px). | `filtres_finals/`, `A4_FRANJA.json` |
| 5 | `a5_cantonada.py` | Continua el cel a la cantonada del logo, amb la recepta de la V79. El criden a7 i `regenera_cantonada.jsx`. | — |
| 6 | `a6_mascares.py` | Fa les màscares (decisió A): les teves de la V83, obertes sota la vora suau de la Lluna i tancades on la Lluna és opaca. | `mascares/`, `A6_MASCARES.json` |
| 7 | `a7_munta_psb.py` | Munta `V86_stage.psb` des de la V85 amb les capes noves i els canvis. La resta hi va byte a byte. La memòria cau de canals porta l'empremta del contingut. | `V86_stage.psb`, `A7_*.json`, `canals_psb/` |
| 8 | `a8_desa_natiu.jsx` | Photoshop el desa com a `1-PHOTOSHOP/V86.psb` (sense sobreescriure) i en fa les vistes. | `vistes/`, `A8_NATIU.log` |
| 9 | `a9_qa.py`, `a9b_vistes.py` | Fa les proves predeclarades (cobertura, capes intactes, ràsters, continuïtat al limbe, costura de la cantonada, i P6/P7: textura i nivell arran del limbe al compost natiu) i les làmines. | `A9_QA.json`, `A9B_*.json`, `LAMINA_V86_*.png` |
| 10 | `a10_prova_cantonada.jsx` | Prova `regenera_cantonada.jsx` sobre la V86 desada i la tanca sense desar. | `A10_*.log`, `A10_*.json` |

**Mòduls i eines:**
- `v86_comu.py`: rutes, claim i rebuts.
- `v86_operadors.py`: NRGF, RHEF, MGN, WOW, ACHF i les continuacions.
- `v86_compost.py`: la composició de capes com a Photoshop.
- `corre_jsx.sh <fitxer.jsx>`: executa un JSX al Photoshop obert des del terminal, amb `$.evalFile`, així que les rutes són relatives. `do javascript` amb un alias fa l'error 8800.

**Retirat, conservat per història:**
- `a4_franja_interpolacio_retirada.py`: la decisió B literal. Interpolava tota la franja des de fora i deixava un anell llis sense detall de 20–50 px.
- `a3a_franja_un_instant_radi_efemeride_retirat.py`: mesurava la validesa des del radi de l'efemèride i ajustava el nivell per distància a la fusió. Perdia ~3 px de corona real i importava la vora clara de la fusió; deixava una tira llisa de 4–6 px arran del limbe.

Els intents descartats són a `4-RESULTATS/v86_neta_20260923/descartat_*`, cadascun amb el seu LLEGEIX-ME.

## La cantonada del logo es regenera sola

La capa **«Cantonada del logo · es regenera»** és a sota de les capes d'ajust i a sobre de les estrelles. Omple el triangle sense imatge del racó inferior dret de l'enquadrament final continuant el cel de les capes que té a sota. Fa servir la mateixa recepta que la V79, declarada al whitepaper: un gradient suau ajustat al cel del voltant i gra proper reflectit a través de la vora. No afegeix informació observacional.

**Si canvies qualsevol capa de sota** (filtres, base, opacitats…), regenera-la:

1. Amb la V86 (o posterior) oberta a Photoshop, fes **Fitxer > Scripts > Explora…** i tria `regenera_cantonada.jsx` d'aquesta carpeta.
2. Photoshop compon les capes de sota, `a5_cantonada.py` calcula el cel i la capa se substitueix. És **un sol pas de l'historial** (Cmd+Z el desfà) i triga uns 14 s.
3. Desa quan vulguis. L'script no desa res pel seu compte.

Si l'enquadrament final canvia de lloc, cal canviar `CAIXA` a l'script i `MARC_FINAL` a `a5_cantonada.py`. Ara és el marc del V78-FINAL: x 1325–9348, y 1142–6263 del llenç.
