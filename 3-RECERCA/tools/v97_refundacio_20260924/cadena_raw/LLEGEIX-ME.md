# cadena_raw — els apilats per tren, refets des dels RAW (V97)

Còpia literal dels scripts de Codex de la V85 (`3-RECERCA/tools/v85_regeneracio_20260922/`: a2, a4, a5, a8, a9, a10), amb només dos canvis:
la carpeta de sortida (`4-RESULTATS/v97_refundacio_20260924/cadena_raw`) i l'identificador del claim.

**Per què:** el 24-09 al vespre la Paperera es va buidar i els apilats per tren (`vixen_total_v38`, `sony_A_total_v36`,
`sony_B_total_v42`), la fusió V42 i els màsters de calibració van desaparèixer. Aquesta cadena els torna a fer des dels RAW,
amb la calibració, el registre i els paràmetres congelats de `2-ARXIU/reconstruccio_compactacio_20260915/raw_replay/`.
Cada etapa comprova els SHA-256 contra les referències congelades: la sortida és bit a bit la mateixa.

**Ordre:** `a2_calibration.py VIXEN`, `a2_calibration.py SONYTOT`, després `a10_run_baseline.py`
(grid → v36 → sony_A → vixen → sony_B → b3 → s4 → d4 → limb_frames). Durada de la V85: ~11 min sense la calibració.
