#!/bin/zsh
# Cadena V34: a1 → b1 → b2 → b3 → b4a → b4c → c3 → c4 build+verify. S'atura al primer error.
cd "/Users/USUARI/Downloads/Eclipse 2026/research/tools/v34_20260907"
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=6
PY=~/.venvs/eines-ia-py312/bin/python
run() { echo "== $1 $(date +%H:%M:%S)"; $PY -W ignore "$@" > "$1.log" 2>&1 || { echo "ERROR a $1"; tail -20 "$1.log"; exit 1; }; tail -1 "$1.log"; }
[ -n "$DES_DE_B3" ] || run a1_pesos_per_fotograma.py
[ -n "$DES_DE_B3" ] || run b1_camps_per_fotograma.py
[ -n "$DES_DE_B3" ] || run b2_recomposicio.py
run b3_fusio.py
run b4a_capes_cadena.py
run b4c_capes_pures.py radial local wow
run c3_portes.py
rm -f staging/V34.psb
$PY -W ignore c4_psb.py build > c4_build.log 2>&1 || { echo "ERROR c4 build"; tail -5 c4_build.log; exit 1; }
$PY -W ignore c4_psb.py verify > c4_verify.log 2>&1 || { echo "ERROR c4 verify"; tail -5 c4_verify.log; exit 1; }
tail -1 c4_verify.log; echo "== CADENA V34 ACABADA $(date +%H:%M:%S)"
