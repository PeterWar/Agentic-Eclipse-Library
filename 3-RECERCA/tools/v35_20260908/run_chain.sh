#!/bin/zsh
# Cadena V35: b3 → b4a → b4c → b4d. S'atura al primer error. (a1/b1/b2 són els de la V34: no es repeteixen.)
cd "/Users/USUARI/Downloads/Eclipse 2026/research/tools/v35_20260908"
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=6
PY=~/.venvs/eines-ia-py312/bin/python
run() { echo "== $1 $(date +%H:%M:%S)"; $PY -W ignore "$@" > "$1.log" 2>&1 || { echo "ERROR a $1"; tail -20 "$1.log"; exit 1; }; tail -1 "$1.log"; }
[ -n "$DES_DE_B4" ] || run b3_fusio.py
run b4a_capes_cadena.py
run b4c_purs.py mgn wow
run b4d_radial_vora.py
echo "== CADENA V35 (b3–b4d) ACABADA $(date +%H:%M:%S)"
