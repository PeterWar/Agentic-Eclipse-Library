# 174 · La geometria fina del limbe (LOLA, nord 45,25°) i el detall de baix des de 0,5 px (V106, 26-09-2026)

Encàrrec de Pere: «Endavant fent la inversió conjunta i el perfil LOLA. Mantenim la Lluna actual i lluitarem per cada píxel de detall.»
- Informe i xifres: `4-RESULTATS/v106_inversio_20260926/RESULTAT.md`.
- Codi: `3-RECERCA/tools/v106_inversio_20260926/` (amb `lola_fi/` i `separacio/`, els guions dels dos agents).
- Producte: `1-PHOTOSHOP/V106.psb`, candidata.

## Què s'ha après

1. **La vora real de la Lluna es pot calcular amb l'altimetria LOLA (NASA PDS), i funciona.** El perfil es fa amb JPL Horizons des del lloc real (Mirador Final 2) i a l'instant de la Lluna de presentació: per a cada angle de posició, el radi màxim del terreny projectat en perspectiva.
   - Contra la vora mesurada a 67 fotogrames: ρ 0,96 per sobre de 4° i 0,81 a 1–4°.
   - L'escala del relleu surt bé: k = 1,002 ± 0,005.
   - LOLA-64 (474 m) prediu els fotogrames reservats millor que la vora empírica.
2. **⛔ El nord celeste al llenç és 45,253° ± 0,017°, no 44,25°.**
   - L'ajust a escala de 2° amb LOLA-16 va donar 44,25°, i a escala fina el relleu hi queda en **contrafase** (ρ −0,25).
   - El valor bo coincideix amb el de les estrelles (45,34°).
   - La cadena de registre en diu 43,41°. Aquesta diferència de gairebé 2° no està explicada, i caldria mirar si hi ha algun producte que la faci servir.
   - **Lliçó:** abans d'usar un relleu fi, ajusta l'orientació a l'escala fina, amb validació creuada.
3. **Cada fotograma té una deformació pròpia de la vora** (seeing o refracció variable): ~0,3 px per sobre de 4° i ~0,1 px a 1–4°. Dura ~1 s i LOLA no la pot predir.
   - La **dispersió atmosfèrica** desplaça el centre lunar del vermell +0,62 px i el del blau −0,76 px (vertical).
   - La refracció d'ordre 2 es mou 0,27 px en 100 s.
4. **El detall tangencial de cada fotograma, dividit per la seva transmissió T calculada amb la geometria fina, deixa de moure's amb la Lluna** (c1f).
   - A 240–300° és corona des de 0,5–1 px: la fracció lunar agregada és ≤ 0,1, amb un soroll de ±0,05–0,15.
   - A la V105 era corona només des de 2,5 px.
   - La mateixa divisió amb la geometria dolenta (c1b: LOLA-16, 44,25°) ho empitjorava.
5. **On la prova «Lluna o corona» (m1) no discrimina:** a 140–200° i a 320–340° la Lluna s'hi mou de manera gairebé radial i el desfasament previst és < 1,5 px. Les fraccions grans que hi surten (±1–3) són inestabilitat de l'ajust, no pas relleu lunar. Fes-la per sectors de 20° i amb el soroll de desfasaments falsos (`m1e_agregat_sectors.py`).
6. **La separació conjunta (corona fixa al Sol + relleu fix a la Lluna) no és a l'abast d'aquesta dada.**
   - Arran de la vora, el soroll de cada fotograma (~0,1 en ln L) es multiplica per 2–3.
   - Fins i tot el bessó amb el model exacte dona ρ 0,19 a d 1 px.
   - Amb la dada real, hi afegeix un patró lunar a d 2,5–4.
   - Descartada. Resultat a `4-RESULTATS/v106_inversio_20260926/separacio/`.
7. **El nivell dels primers píxels no es pot validar al 2 % a l'esquerra (120–240°):** allà la vora de la Lluna queda a 0–2,5 px de la del Sol i la cromosfera hi queda destapada, diferent a cada fotograma (a3e, deixant-ne un fora: +10…+33 %). Per això la V106 no toca els filtres, només el detall tangencial.

## La V106
**Detall.** És un detall híbrid (`h1_hibrid_delta.py`): la c1f a 100–290° i el de la V105 a la resta.

**Porta per angle**, triada amb la prova m1 per sectors de 20°:
- 195–240°: 3 px;
- 240–260°: 1 px;
- 260–295°: 0,5 px;
- resta: com la V105.

**Capa.** Guany i ràster amb el mateix mètode de la 305 (`c2b`, que reprodueix la 305 byte a byte amb les dades de la V105). Capa 306, amb la 305 oculta; 20 913 píxels actius (+16 %).
- Jutge Brno: a baix i a baix-esquerra, a favor (+0,1…+0,5); a dalt-esquerra, mixt.
- Cap artefacte a les làmines.
- A l'esquerra (150–210°) no hi entra res.

## Trampes
- `c1b` i `b1` fan servir el nord 44,25° (malament). Els bons són `lola_fi/c1f_detall_tangencial_fi.py` i `lola_fi/b1f_psf_fina.py`, amb `geom_fina.py` (θN 45,253°).
- Els guions de `lola_fi/` escriuen a la seva pròpia carpeta (`HF`) i llegeixen el projecte de `~/Desktop/Eclipse 2026`. Per refer-los, copia'ls a una carpeta de treball. `D_FINA_nucli.npy` (501 MB) no s'ha desat: es refà amb `g2_mapes.py`.
- La m1 fila per fila té un soroll de ±0,1–0,4. No decideixis una porta per una sola casella: fes servir la m1e agregada.
