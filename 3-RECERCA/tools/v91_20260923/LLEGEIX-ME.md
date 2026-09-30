# V91 (23-09-2026, nit) · eines

Totes es corren des d'aquesta carpeta amb `~/.venvs/eines-ia-py312/bin/python` i un claim viu (`.coordination/claim.lock`). Les rutes són relatives a l'arrel del projecte (`v91_comu.py`) i la sortida va a `4-RESULTATS/v91_20260923/`.

**Ordre:**
1. **`a5c_radial_on_hi_havia_linies.py`:** els 16 ràsters de la V88 amb el suavitzat radial prop del limbe només a 104–228°, amb fosa a 99–104° i a 228–232°. Surt a `filtres_radial_c/` i `A5C_RADIAL.json`.
2. **`p1_detall_protuberancia.py`:** la capa de les guspires de la foto 76, amb `GUANY_GUSPIRES=3`. Surt a `P1_PROTUBERANCIA.npz`, el JSON i les làmines P0–P2.
3. **`b2_munta_v91.py`:** munta `V91_stage.psb` a partir de la V90 de Pere de les 22:06. Comprova el SHA, que sigui la V90 de les 22:06, i mai no sobreescriu.
4. **`b3_desa_natiu.jsx`:** amb `./corre_jsx.sh b3_desa_natiu.jsx`, Photoshop desa `1-PHOTOSHOP/V91.psb` i en fa les vistes. No toca cap altre document obert. Cal el permís de Pere si té documents sense desar.
5. **`b4_qa_v91.py`:** proves P2–P5 contra la V90 de Pere.
6. **`b5_laminas_v91.py`:** làmines del compost de Photoshop (lent, línies, protuberància i Lluna) i la diferència dels composts.

**Històric:**
- **`a5b_radial_limitat.py`:** el criteri de l'alçada del limbe, del segon desament, retirat perquè la lent hi quedava a 230–258°.
- **`a6_estructura_coherent.py`:** la mesura de l'estructura paral·lela al limbe. No discrimina, perquè la domina el salt de la Lluna.
