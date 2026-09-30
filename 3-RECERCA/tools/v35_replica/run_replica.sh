#!/bin/zsh
cd "/Users/USUARI/Downloads/Eclipse 2026/research/tools/v35_replica"; export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=4; PY=~/.venvs/eines-ia-py312/bin/python
for s in b3_fusio.py b4a_capes_cadena.py "b4c_purs.py mgn wow" b4d_radial_vora.py "c4_psb.py build" "c4_psb.py verify"; do n=${s%% *}; echo "== $s $(date +%H:%M:%S)"; $PY -W ignore ${=s} > ${n}.${s##* }.log 2>&1 || { echo "ERROR $s"; tail -5 ${n}.${s##* }.log; exit 1; }; tail -1 ${n}.${s##* }.log; done; echo "== REPLICA V35 ACABADA $(date +%H:%M:%S)"
