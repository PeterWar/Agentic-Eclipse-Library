#!/bin/zsh
cd "/Users/USUARI/Downloads/Eclipse 2026/research/tools/v39_20260909"; export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=6; PY=~/.venvs/eines-ia-py312/bin/python
nou() { [ -f "$1" ] && [ "$1" -nt cau/.marca_a2b ]; }
while ! nou cau/soroll_escales_1q.npz || ! nou cau/soroll_escales_1q_c0.npz || ! nou cau/soroll_escales_1q_c2.npz || ! nou cau/soroll_bilateral_1q.npz; do sleep 20; done
sleep 10
run() { echo "== $1 $(date +%H:%M:%S)" >> cadena.log; $PY -W ignore "$@" > "$1.log" 2>&1 || { echo "ERROR a $1" >> cadena.log; tail -20 "$1.log" >> cadena.log; exit 1; }; tail -1 "$1.log" >> cadena.log; }
run b4a_capes_cadena.py; run b4c_purs.py mgn wow; run c3_portes.py; run c3b_transferencia_real.py; rm -f staging/V39.psb
echo "== c4 build $(date +%H:%M:%S)" >> cadena.log; $PY -W ignore c4_projecte_v39.py build > c4_build.log 2>&1 || { echo "ERROR build" >> cadena.log; tail -8 c4_build.log >> cadena.log; exit 1; }; tail -1 c4_build.log >> cadena.log
echo "== c4 verify $(date +%H:%M:%S)" >> cadena.log; $PY -W ignore c4_projecte_v39.py verify > c4_verify.log 2>&1 || { echo "ERROR verify" >> cadena.log; tail -8 c4_verify.log >> cadena.log; exit 1; }; tail -1 c4_verify.log >> cadena.log
echo "== c4 gate $(date +%H:%M:%S)" >> cadena.log; $PY -W ignore c4_projecte_v39.py gate > c4_gate.log 2>&1 || { echo "ERROR gate" >> cadena.log; tail -8 c4_gate.log >> cadena.log; exit 1; }; tail -1 c4_gate.log >> cadena.log
echo "== V39 LLEST PER PUBLICAR $(date +%H:%M:%S)" >> cadena.log
