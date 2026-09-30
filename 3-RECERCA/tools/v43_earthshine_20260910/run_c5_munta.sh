#!/bin/zsh
cd "$(dirname "$0")"; export PYTHONDONTWRITEBYTECODE=1; PY=~/.venvs/eines-ia-py312/bin/python
for pas in build verify gate publish; do
  echo "== $pas $(date +%H:%M:%S)"; $PY -W ignore c5_earthshine_v43.py $pas > c5_$pas.log 2>&1 || { echo "ERROR a $pas"; tail -6 c5_$pas.log; exit 1; }
  tail -1 c5_$pas.log | cut -c1-220
done
echo "FET $(date +%H:%M:%S)"
