#!/bin/zsh
# REPLICA_V35 · Refà, en carpetes NOVES i sense tocar res del canònic, la composició V34 (a1→b1→b2) i la V35 (b3→b4a→b4c→b4d→c4 build/verify)
# a partir dels runs immutables de la cadena (019 VIXEN, 016 SONYTOT), dels artefactes V29 (cau_final) i dels paràmetres congelats,
# i després compara amb els artefactes canònics (verifica_replica.py). No publica res. Durada ~25 min (Mac M-series, 69 GB).
# Ús: research/tools/v35_20260908/replica_v35.sh [nom]   (per defecte: replica_<data>)
set -e
ROOT="/Users/USUARI/Downloads/Eclipse 2026"; T="$ROOT/research/tools"; NAME="${1:-replica_$(date +%Y%m%dT%H%M%S)}"
PY="$($HOME/.venvs/eines-ia-py312/bin/python -c 'import sys; print(sys.executable)' 2>/dev/null || true)"; [ -n "$PY" ] || { echo "Cap intèrpret amb les biblioteques (cal ~/.venvs/eines-ia-py312; vegeu CLAUDE.md global)"; exit 2; }
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=4
R34="$T/v34_$NAME"; R35="$T/v35_$NAME"; [ -e "$R34" -o -e "$R35" ] && { echo "$R34 o $R35 ja existeixen"; exit 3; }
mkdir -p "$R34" "$R35/purs/sources" "$R35/staging" "$ROOT/output/v34_$NAME" "$ROOT/output/v35_$NAME"
for f in comu34.py a1_pesos_per_fotograma.py b1_camps_per_fotograma.py b2_recomposicio.py; do cp "$T/v34_20260907/$f" "$R34/"; done
sed -i '' -e "s#OUT34 = ROOT / 'output/v34_20260907'#OUT34 = ROOT / 'output/v34_$NAME'#" -e "s#IAOUT34 = Path('/Users/USUARI/Desktop/Eclipse 2026/IA/output/v34_20260907')#IAOUT34 = ROOT / 'output/v34_$NAME/IA_dummy'#" "$R34/comu34.py"
for f in comu35.py b3_fusio.py b4a_capes_cadena.py b4c_purs.py b4d_radial_vora.py c4_psb.py; do cp "$T/v35_20260908/$f" "$R35/"; done
cp "$T/v35_20260908/purs/"*.dylib "$R35/purs/"; cp "$T/v35_20260908/purs/sources/"* "$R35/purs/sources/"
sed -i '' -e "s#OUT35 = ROOT / 'output/v35_20260908'#OUT35 = ROOT / 'output/v35_$NAME'#" -e "s#IAOUT35 = Path('/Users/USUARI/Desktop/Eclipse 2026/IA/output/v35_20260908')#IAOUT35 = ROOT / 'output/v35_$NAME/IA_dummy'#" "$R35/comu35.py"
sed -i '' -e "s#output/v35_20260908/lliurables/vistes#output/v35_$NAME/lliurables/vistes#" -e "s#REB35 = ROOT / 'output/v35_20260908/4-rebuts'#REB35 = ROOT / 'output/v35_$NAME/4-rebuts'#" "$R35/b4c_purs.py" "$R35/b4d_radial_vora.py"
# la V35 llegeix la composició per grup de CAU34 (comu34 del canònic). Per replicar-la de debò, apunta el comu35 de la rèplica a la rèplica V34:
sed -i '' -e "s#sys.path.insert(0, str(ROOT / 'research/tools/v34_20260907'))#sys.path.insert(0, str(ROOT / 'research/tools/v34_$NAME'))#" "$R35/comu35.py"
run() { local d="$1"; shift; echo "== $d: $* $(date +%H:%M:%S)"; (cd "$d" && "$PY" -W ignore "$@" > "$d/${1}.${2:-run}.log" 2>&1) || { echo "ERROR a $*"; tail -8 "$d/${1}.${2:-run}.log"; exit 1; }; }
run "$R34" a1_pesos_per_fotograma.py; run "$R34" b1_camps_per_fotograma.py; run "$R34" b2_recomposicio.py
run "$R35" b3_fusio.py; run "$R35" b4a_capes_cadena.py; run "$R35" b4c_purs.py mgn wow; run "$R35" b4d_radial_vora.py; run "$R35" c4_psb.py build; run "$R35" c4_psb.py verify
echo "== verificació contra el canònic $(date +%H:%M:%S)"; "$PY" "$T/v35_20260908/verifica_replica.py" "$R34" "$R35" --json "$ROOT/output/v35_$NAME/VERIFICACIO_REPLICA.json"
echo "== Porta Photoshop (obre i tanca sense desar): "; /bin/zsh "$T/capes_totals_v14/porta_photoshop.sh" "$R35/staging/V35.psb"
echo "== REPLICA ACABADA $(date +%H:%M:%S) · resultats a $ROOT/output/v35_$NAME/"
