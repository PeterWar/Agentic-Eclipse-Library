# V88 — com es fa cada capa (a partir de la V87 de Pere)

Tots els scripts treballen amb rutes relatives a l'arrel del projecte (la carpeta de `CLAUDE.md`).
- **Entorn:** el primer Python que tingui numpy, scipy, opencv, psd-tools i tifffile (avui `~/.venvs/eines-ia-py312`).
- **Claim:** cada pas comprova que n'hi hagi un de viu a `.coordination/claim.lock`.
- **Operadors:** els filtres fan servir els operadors de la V86 (`3-RECERCA/tools/v86_neta_20260923/v86_operadors.py`).
- **Fonts:** la suma lineal i els fotogrames de la caixa de la Lluna de la V85 (`4-RESULTATS/v85_regeneracio_20260922/`), que no es toquen.

## Ordre dels passos (sortides a `4-RESULTATS/v88_20260923/`)

| Pas | Script | Què fa |
|---|---|---|
| 0 | `c0_marques_v87.py` | Extreu les marques de la capa «Artefactes V87» per color i en calcula la geometria respecte del limbe → `MARQUES_V87.json`. |
| 1 | `b1_vistes_v87.jsx` | Photoshop fa les vistes natives de la V87 sense la capa de marques (i sense la Lluna) i la tanca sense desar → `vistes_v87/`. |
| 2 | `a3a_franja_un_instant.py` | La dada d'un sol instant de la franja escombrada per la Lluna. Parteix de la V86, amb tres canvis:<br>• la vora interior del domini és una **corba llisa per azimut** (`DMIN`);<br>• la dada es **suavitza σ 1,3 px** per igualar-ne el soroll al de la fusió (hi tenia ~3 vegades més soroll fi);<br>• `W_CURT` es calcula sobre els pesos positius, i a més de 8 px del limbe n'hi ha prou amb 5 fotogrames.<br>→ `A3A_*` |
| 3 | `a3_filtres.py E1`, `E6`, `E2`, `E3`, `E4` | Els 16 ràsters de filtre (recepta V58) → `filtres/`, `A3_E*.json`. |
| 3b | `a3b_compara_v84.py` | Comparació amb la V84 lluny del limbe → `A3B_COMPARA_V84.json`. |
| 4 | `a4_franja.py` | Fosa **suau** de la dada i la continuació sobre la distància analítica a la corba (VORA 2 px, rampa de 3 px). La continuació és **radial**: el valor a la distància on la dada ja és plena, allargat cap endins. → `filtres_finals/`, `A4_FRANJA.json` |
| 5 | `e1_earthshine_apilat.py` | Apilat lineal de la Lluna des de zero amb 14 fotogrames Vixen ≥ 0,25 s: un sol registre sobre la Lluna, cap píxel al costat d'una saturació i guarda del moviment. Serveix de prova, no entra al PSB. → `E1_*` |
| 6 | `e2_earthshine_v88.py` | Capa «Earthshine V88»: l'earthshine de Pere (225) a l'interior; a l'anell de la vora, sense l'estructura fina no lunar (suavitzat radial σ 5 px des de més enllà de 12 px, azimutal σ 4 px, rampa de 24 a 12 px). Alfa de la 225. → `E2_*` |
| 7 | `b2_munta_v88.py` | Munta `V88_stage.psb` des de la V87:<br>• filtres «· V88»;<br>• «Earthshine V88» a sobre de la 225, que queda oculta;<br>• cantonada regenerada;<br>• marques ocultes;<br>• la resta, byte a byte. |
| 8 | `b3_desa_natiu.jsx` | Photoshop desa `1-PHOTOSHOP/V88.psb` (sense sobreescriure) i en fa les vistes → `vistes/`. |
| 9 | `b4_qa.py` | Proves predeclarades P1–P3, P5, P6, P8, P9 i P10 → `B4_QA.json`. |
| 10 | `b5_laminas.py` | Làmines de revisió → `LAMINA_V88_*.png`. |

**Mòduls:**
- `v88_comu.py`: rutes, claim i rebuts.
- `v88_compost.py`: el compositor de la V86 més el mode «Aclarir».
- `a5_cantonada.py`: còpia del de la V86.
- `corre_jsx.sh`: executa un JSX al Photoshop obert, amb `$.evalFile`.

A la porta de Photoshop (`3-RECERCA/tools/capes_totals_v14/porta_photoshop.sh`) cal passar-li la **ruta absoluta**.

**Cantonada del logo:** es regenera amb el mateix script de la V86, `3-RECERCA/tools/v86_neta_20260923/regenera_cantonada.jsx`.

**Proves de diagnòstic de la tarda:** apilats alternatius, meitats independents, compost emulat i mesures. Són a `4-RESULTATS/v88_20260923/proves/`, i els intents descartats a `descartat_*`.
