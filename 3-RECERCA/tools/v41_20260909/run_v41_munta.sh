#!/bin/zsh
# V41: build → verify → gate (Photoshop real) → publish. Logs al costat.
set -u; cd "$(dirname "$0")"; export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=4; PY=~/.venvs/eines-ia-py312/bin/python
for pas in build verify gate publish; do
  echo "== $pas $(date +%H:%M:%S)"; $PY -W ignore c4_projecte_v41.py $pas > c4_$pas.log 2>&1 || { echo "FALLA $pas"; tail -5 c4_$pas.log; exit 1; }
  tail -1 c4_$pas.log
done
echo "V41 PUBLICADA"
