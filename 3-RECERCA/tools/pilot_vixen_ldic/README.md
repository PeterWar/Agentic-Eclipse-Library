# Pilot Vixen LDIC · preflight fail-closed

Aquest paquet és la branca nova i aïllada per al pilot Vixen de les fases
0 → 1 → 2 del traspàs del 23-08-2026. No modifica cap RAW, dark, flat,
màster, PSB ni producte històric.

## Estat actual

El pilot complet **no es pot executar encara** sense violar les portes del
mateix traspàs:

- la porta F0 `coeficient 1,00 ± 0,05; R² >= 0,95` és una mesura dels dos
  apuntaments **Sony**, no una validació del flat radial Vixen;
- el radial Vixen es va construir al centre geomètric. Amb una sola orientació
  de flat, un descentrament de l'eix i un pla multiplicatiu són degenerats a
  primer ordre; per tant el radial no conté una mesura independent de l'eix;
- `final_solution.json:r6_radial.rms = 0,424193 px`, per damunt de la porta
  F1 de `0,3 px`; les cinc parelles de `deriva_corona.json` donen una evidència
  parcial bona, però no cobreixen els 68 fotogrames ni el gir temporal.

`preflight.py` materialitza aquest veredicte en un build no-clobber, amb
inventari, hashes, contracte de reixa, geometria derivada i controls
adversarials. Només després d'una nova evidència positiva F0 i d'un oracle F1
per fotograma podrà existir una ordre `run` de producció.

## Contractes ja congelats i límits

- entrada: 124 CR3 presents; els 68 noms únics i `usat=True` del manifest;
- exposició física llarga: `10,079368399159 s`; el dark continua al nivell
  nominal `10 s`;
- reixa: crop cru `(y=108, x=172, h=4640, w=6960)`, RGGB;
- dark històric `4638×6958`: les dues files i columnes que falten **no es
  fabriquen** repetint la vora. Queden `NaN/no-data` i tindran pes zero; per
  recuperar-les cal reconstruir un dark real de `4640×6960`;
- ordre: `RAW - master_dark`, després divisió només per
  `MASTER_OPTICAL_RADIAL_CFA4.npy`, abans de qualsevol warp; cap segona resta
  de pedestal i cap clip;
- el llenç afí diagnòstic és nord amunt, Sol al centre i
  `2,1494813525884373 arcsec/px`, amb dimensions derivades de la unió dels
  perímetres. **No és encara el llenç F1 de producció**: falta congelar
  projecció aparent, època per fotograma i inversió dels termes radials de la
  placa;
- LDIC: autoritat fora de Photoshop, amb una sola suma per fotograma
  `N = sum(w J)`, `D = sum(w)`, `g = N/D`; el PSB futur només serà una
  interfície reversible de pesos i un derivat de previsualització. Això és
  encara una **direcció de disseny**: l'arquitectura de producció no queda
  congelada fins que existeixin el ledger F1 d'inclusió, l'ordre filtrat i els
  hashes per fotograma de `f/w/k/q/J`, el gauge/iteracions, el domini i floor
  de F, el dtype i el round-trip de pesos de Photoshop.

Les fonts d'autoritat consumides (manifest, geometria, placa, deriva i els
dos `SHA256SUMS.txt` de flats/S6) tenen SHA-256 congelat al codi. El ledger de
68 RAW, cada `STACK_RECEIPT` S6 i el rebut/productes de flat es verifiquen a
través d'aquesta cadena **abans** de parsejar-los o usar-los.

## Execució

`run_preflight.sh` detecta un Python que tingui `numpy`, `scipy` i `rawpy` i
falla amb un missatge útil si no en troba cap; cap script fixa una ruta
d'intèrpret. Exemple des de l'arrel canònica:

```bash
research/tools/pilot_vixen_ldic/run_preflight.sh \
  --out output/pilot_vixen_ldic_20260823/BUILD_ID
```

L'output és exclusiu: si el directori ja existeix, l'execució falla abans de
tocar-lo. Mentre les portes anteriors continuïn igual, el build acaba amb
`STATUS.json = BLOCKED_UPSTREAM_GATES`, no amb `COMPLETE`. `STATUS.json` és el
commit terminal publicat complet amb hard-link atòmic i no-clobber; referencia
`PAYLOAD_SHA256SUMS.txt`, que es verifica abans del commit. Un error anterior conserva el build parcial amb
`ERROR.json`, però mai afegeix `ERROR.json` després d'un `STATUS.json` vàlid.

Els contractes i controls dolents s'executen amb:

```bash
cd research/tools/pilot_vixen_ldic
PYTHONDONTWRITEBYTECODE=1 /RUTA/A/PYTHON_AMB_NUMPY_SCIPY_RAWPY \
  -m unittest -v test_contracts.py test_preflight.py
```
