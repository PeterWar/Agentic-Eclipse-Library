# V90 — com es fa (a partir de la V88 de Pere, 18:50)

Tots els scripts treballen amb rutes relatives a l'arrel. Fan servir el Python amb numpy/scipy/opencv/psd-tools/tifffile (`~/.venvs/eines-ia-py312`) i demanen un claim viu.

| Pas | Script | Què fa |
|---|---|---|
| 1 | `a5_radial.py` | Suavitzat només radial prop del limbe dels 16 ràsters finals de la V88 (σ 4 px fins a 4 px del limbe, 0 a 14 px; en polars i aplicat com a diferència) → `filtres_radial/` |
| 2 | `b2r_munta_v90.py` | `V90_stage.psb`: la V88 de Pere amb les 16 capes de filtre noves («· V90»). La resta, byte a byte |
| 3 | `c1_comprova_stage.py` | Comprovació emulada abans de Photoshop: cobertura, polars i marques a 4:1, la Lluna i controls |
| 4 | `b3_desa_natiu.jsx` | Photoshop desa `1-PHOTOSHOP/V90.psb` i en fa les vistes (`corre_jsx.sh`). La porta: `porta_photoshop.sh` amb ruta absoluta |
| 5 | `b4_qa_v90.py`, `b5_laminas_v90.py` | Proves P2, P3 i P4, i làmines |

**Intent descartat A + B** (`4-RESULTATS/v90_20260923/descartat_intent1_A_B/LLEGEIX-ME.md`): `a3c_sense_pujada.py`, `a3_filtres.py`, `a4_c1.py`, `v1_linia_cromosfera.py`, `v2_lluna_vora_nitida.py`, `b2_munta_v90.py`.
