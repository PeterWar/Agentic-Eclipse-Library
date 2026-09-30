# 98 · Pilot Vixen: preflight fail-closed abans de LDIC

**23 d'agost de 2026.** Codex ha executat el traspàs
`.coordination/HANDOFF_2026-08-23_PILOT_VIXEN.md` fins al primer gate que es pot
defensar amb l'evidència viva. El resultat és un **preflight canònic bloquejat**,
no un apilat ni una composició:

`output/pilot_vixen_ldic_20260823/20260823T140401Z_preflight_canonical_v4/`

`STATUS.json` té SHA-256
`9e849564dabdb5968c6b2cdfe93b02eec1aed343fb485b136a67612da49861ed` i
estat `BLOCKED_UPSTREAM_GATES`. La fase 2 no s'ha executat.

## DEMOSTRAT

- L'arrel de totalitat té **124 CR3**, no 129. L'entrada contractual sí que és
  inequívoca: **68/68** noms únics del manifest, `usat=True`, tots presents,
  15 nivells d'exposició i bytes/hash coincidents amb `LEDGER_68.json`.
- L'ordre congelat 572A2958→572A3025 té SHA-256
  `950baed4b306155adc468415f70e680e1fbf607ea8e2a67cdac49a56f76e8530`.
- L'exposició llarga física és **10,079368399159 s**, per autoritat MakerNote
  S6; el màster dark continua indexat pel nominal de 10 s. El manifest
  històric no s'ha modificat.
- La reixa autoritzada és el crop cru `(y=108, x=172, h=4640, w=6960)`, RGGB.
  Els màsters dark històrics són `4638×6958`: les dues files i columnes
  absents són `NaN/no-data` des del mateix adaptador i han de tenir `w=0`.
- Hi ha 768 darks a l'arrel i **239 fonts úniques** seleccionades pels 15
  rebuts ancorats S6. Les 15 parelles NPY/JSON coincideixen byte a byte amb
  l'autoritat acceptada.
- Repetir la vora del dark no és científic. Amb 16 CR3 reconstruïts per
  control, el residu màxim de la vora replicada arriba a **15,43 ADU** a
  1/3200 s i **64,07 ADU** a 10 s; per això la vora queda sense dada.
- Les 125 fonts de flat, el rebut i tots els productes coincideixen amb la
  cadena SHA-256 congelada. Només el radial és candidat de política; full,
  2-D, fi i pols continuen exclosos del pilot.
- El llenç afí diagnòstic derivat de tots els perímetres és **7697×8613 px**,
  nord amunt, Sol al centre i `2,1494813525884373 arcsec/px`. No és encara el
  llenç F1 de producció perquè omet la inversió radial i l'època aparent per
  fotograma.
- El build terminal ha rehashejat **519 fitxers únics / 13.823.377.138 bytes**
  immediatament abans de `STATUS.json`; agregat
  `f92ef40f4a3cd7d0520bc394c377024206d43c103039c2c77f2d94f1f9d0ab4f`.
  `PAYLOAD_SHA256SUMS.txt` passa 7/7, no hi ha `ERROR.json` ni temporals.
- La reexecució sobre el mateix build ID retorna codi 2 abans d'escriure i el
  fingerprint del build resta idèntic:
  `524d00a1454fa685aca4075ad7c0596abfb70cdb6ff7f5d5870c3cc15c5745c3`.
- Contractes adversarials: **37/37 PASS**; sintaxi shell PASS. Dos revisors
  independents han retornat `CLEAN` sobre `preflight.py` SHA-256
  `330263708278841859c51cc449c0aa5a502db44964d94feedefe1cc63645f639` i
  `contracts.py` SHA-256
  `3994b2b10b369e106b2794b2fb29473be0ae253eedef8c392a9c663fe71c0876`.

## FALTA · F0

La porta positiva `coeficient +1,019; R²=0,981` citada al traspàs és de la
**Sony** i dels seus dos apuntaments separats uns 750 px. No valida el radial
Vixen.

La Vixen només desplaça el Sol `(+18,67, −20,41) px` entre el primer i l'últim
fotograma. Al domini diagnòstic `1,3–7 Rsol`, el predictor
`ln(F_B/F_A)` té `p95−p05 = 0,0011491`: només **0,1149 %** de palanca. No pot
promocionar el flat amb el contracte `beta=1,00±0,05`, CI95 dins l'interval i
`R²≥0,95`.

A més, el radial es va construir sobre el centre geomètric. Amb l'orientació
actual, desplaçament d'eix i pla multiplicatiu són degenerats; el producte no
és una mesura independent de l'eix òptic. F0 és
`BLOCKED_CONTRACT_MISMATCH_AND_INSUFFICIENT_LEVERAGE`, mai PASS per absència
d'evidència.

## FALTA · F1

- `final_solution.json:r6_radial.rms = 0,424193 px` → FAIL contra `≤0,3 px`.
- `geometria.json`: residu vectorial **0,487192 px** → FAIL.
- `deriva_corona.json`: **0,138859 px** sobre cinc parelles → evidència parcial,
  no oracle dels 68 frames ni del gir.

Falten residus held-out per cada frame admès, cobertura de camp i gir, ledger
d'inclusió/exclusió/interpolació, geometria als midpoints físics dels tres
10,079 s, inversió de la placa radial completa i projecció/època aparent
congelada per fotograma.

## FALTA · F2 i ordre de gates

L'arquitectura `N=Σ(wJ)`, `D=Σw`, `g=N/D` fora de Photoshop queda documentada
com a **direcció de disseny, no producció congelada**. Abans de fase 2 cal:

1. tancar F0 amb evidència Vixen independent o canviar explícitament el
   contracte científic; no es pot importar el PASS Sony;
2. tancar F1 per cada frame admès i congelar el ledger i l'ordre resultant;
3. congelar hashes `f/w/k/q/J`, gauge, ordre d'ajust, iteracions, domini i
   floor relatiu de F, dtype/no-data i persistència de `N/D/g`;
4. demostrar el round-trip dels pesos de Photoshop contra l'autoritat offline;
5. només llavors executar LDIC i les portes E/F.

Cap RAW, dark, flat, PSB/TIFF històric ni producte S6 s'ha modificat. No hi ha
hagut càmera, PTP, `gphoto2`, GUI física ni Photoshop automatitzat.
