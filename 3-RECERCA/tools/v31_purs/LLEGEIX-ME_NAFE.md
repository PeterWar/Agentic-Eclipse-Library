# La capa NAFE de la recerca de setembre i per què el seu codi ja no és aquí (retirat a la 1.4.2, 2-11-2026)

**El mètode NAFE** (*Noise Adaptive Fuzzy Equalization*) és de **Miloslav Druckmüller**:
M. Druckmüller (2013), «A noise adaptive fuzzy equalization method for processing solar extreme ultraviolet images»,
*The Astrophysical Journal Supplement Series* 207, 25. DOI 10.1088/0067-0049/207/2/25.
El seu programa per a Windows i la seva documentació: <http://www.zam.fme.vutbr.cz/~druck/Nafe/>.

**La capa P06 de la V31** (una de les capes de prova d'aquesta carpeta, del 06-09-2026) feia servir la implementació en
Python d'Eric Buchlin (`medocimage/nafe.py` del dipòsit <https://git.ias.u-psud.fr/ebuchlin/aia-movie>). Aquell dipòsit es
publica sota llicència **GPLv3**. Aquí n'hi havia una còpia (`sources/nafe_published.py`), el guió que la cridava
(`nafe_filter.py`) i una traducció a C++ verificada contra ella (`nafe_native.cpp`), i les carpetes de les versions de prova
següents (de `v32_arcs_20260907` a `v42_20260910`) en duien onze còpies més, a `purs/sources/nafe_published.py`. Copiats en
aquest repositori MIT i sense l'avís de la GPLv3, no complien la llicència. **Els retirem del repositori públic amb la versió
1.4.2 (2-11-2026).** Les versions anteriors del repositori i el seu historial de Git encara els contenen. El projecte de
l'autor els conserva per a ús privat.

Es queden els rebuts, que són nostres: `receipts/P06_NAFE.json` (paràmetres) i `receipts/NAFE_reference_validation.json` (la
traducció reproduïa el codi publicat dins de 2·10⁻⁶). Els guions d'aquelles carpetes (`b4c_*.py`) comparen aquests fitxers
byte a byte amb els de `v31_purs` i criden `nafe_filter.py` per refer la P06: sense ells ja no poden refer aquella capa. Com tota
la carpeta `tools/`, no corren des d'aquest repositori.

**Aquella recepta no era el NAFE de l'article.** Barrejava 0,8 de la imatge equalitzada amb 0,2 de la imatge en gamma
(l'article: pes 0,2, de 0,05 a 0,3) i feia servir un veïnat de 65 px (l'article: 129).

**El NAFE de la llibreria** (`ael.filters.nafe`, `make_filter('nafe', …)`, del 28-10-2026, publicat a la 1.4.2) està escrit
de zero a partir de les equacions de l'article (eq. 11–14) i no fa servir cap línia del codi d'en Buchlin. És MIT, com la resta
de la llibreria.
