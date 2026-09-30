#!/bin/zsh
# Pilot V40 (sense PSB): espera els mapes de soroll nous (totes les vores, dues particions), regenera ACHF + MGN/WOW/bilateral amb la regla wg k=3
# sense creuat, i passa les portes: c3 (rms per anell), c3c (Brno), c3d (vores i gra), A3b (corba de preu). Després: mirar les vistes. Cap PSB.
cd "/Users/USUARI/Downloads/Eclipse 2026/research/tools/v39_20260909"; export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=6; PY=~/.venvs/eines-ia-py312/bin/python
nou() { [ -f "$1" ] && [ "$1" -nt cau/.marca_v40 ]; }

echo "== PILOT 2 (soroll total, ref Sony) $(date +%H:%M:%S)" >> cadena_v40.log
run() { echo "== $1 $(date +%H:%M:%S)" >> cadena_v40.log; $PY -W ignore "$@" > "$1.v40.log" 2>&1 || { echo "ERROR a $1" >> cadena_v40.log; tail -20 "$1.v40.log" >> cadena_v40.log; exit 1; }; tail -1 "$1.v40.log" >> cadena_v40.log; }
run b4a_capes_cadena.py; run b4c_purs.py mgn wow; run c3_portes.py; run c3c_jutge_brno.py
run c3d_vores_i_etapes.py candidata 01=cau/01_v39_u16.npy 04=cau/04_v39_u16.npy 06=cau/06_v39_u16.npy P03=purs/cau/P03_MGN_u16.npy P04=purs/cau/P04_WOW_u16.npy P05=purs/cau/P05_WOW_bilateral_u16.npy
for w in 1.6R 3.7R 5.5R; do echo "== a3b $w $(date +%H:%M:%S)" >> cadena_v40.log; A3B_TAU=1.0 $PY -W ignore a3b_injeccio_neta.py $w > a3b_v40_$w.log 2>&1 || echo "ERROR a3b $w" >> cadena_v40.log; done
echo "== PILOT V40 FET $(date +%H:%M:%S)" >> cadena_v40.log
