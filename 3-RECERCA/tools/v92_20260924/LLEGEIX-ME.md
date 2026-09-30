# V92 (24-09-2026, matinada) · eines

Totes es corren des d'aquesta carpeta amb `~/.venvs/eines-ia-py312/bin/python` i un claim viu (`.coordination/claim.lock`). La sortida va a `4-RESULTATS/v92_20260924/`.

**Ordre:**
1. **`a4m_continuacio_mirall.py`:** els 16 ràsters de la V88 abans de la continuació (`4-RESULTATS/v88_20260923/filtres/`). Els píxels sense dada plena tocant la Lluna es continuen amb mirall de la textura, i el nivell al llarg de l'arc. Surt a `filtres_mirall/`.
2. **`a5c_radial_v92.py`:** el suavitzat radial de la V91 a 104–228°. Surt a `filtres_v92/`.
3. **`p1b_guspires_color_real.py`:** la 267 amb el color real de les guspires (de `4-RESULTATS/v91_lent_residual_20260923/C7_COLOR_GUSPIRES.json`). Surt a `P1B_GUSPIRES.npz`.
4. **`b2_munta_v92.py`:** munta `V92_stage.psb` a partir de la V91 de Pere tal com estigui desada. En registra el SHA i comprova que no canviï durant el muntatge.
5. **`b3_desa_natiu.jsx`:** amb `./corre_jsx.sh b3_desa_natiu.jsx`, Photoshop desa `1-PHOTOSHOP/V92.psb` i en fa les vistes. Cal el permís de Pere si té documents sense desar.
6. **`b4_qa_v92.py` i `b5_laminas_v92.py`:** les proves P2–P5 i les làmines del compost de Photoshop.

**Proves emulades** (abans de Photoshop): `c1_avalua_v92_emulat.py`, `c2_previsualitza_protuberancia.py` i `c3_components_guspires.py`.
