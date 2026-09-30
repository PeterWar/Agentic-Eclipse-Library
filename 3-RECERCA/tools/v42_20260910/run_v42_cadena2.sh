#!/bin/zsh
cd "$(dirname "$0")"; export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=6; PY=~/.venvs/eines-ia-py312/bin/python
run() { echo "== $1 $(date +%H:%M:%S)"; $PY -W ignore "$@" > "${1%.py}.log" 2>&1 || { echo "ERROR a $1"; tail -8 "${1%.py}.log"; exit 1; }; tail -1 "${1%.py}.log" | cut -c1-200; }
run b4a_capes_cadena_v42.py; run b4c_purs_v42.py mgn wow; run b4d_radial_vora_v42.py; run b4b_capes_azimutals_v42.py; run b4e_bases_v42.py; run b4f_rhef_variants_v42.py
echo "CADENA V42 (fins a B4f) FETA $(date +%H:%M:%S)"
