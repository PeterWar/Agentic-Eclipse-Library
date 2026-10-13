#!/bin/zsh
# Punts zero per canal (R, G, B) de les estrelles de camp del tren Vixen + R6 III
# (i rèplica G de la Sony). Tasca msb_calibrat_20261011/zp_canal, 11-10-2026.
#
# Ús (des de qualsevol directori):
#   corre.sh vixen            # cadena original de detecció cega del Vixen (còpia), al WORK nou
#   corre.sh sony             # cadena original de detecció cega de la Sony (còpia)
#   corre.sh xmatch           # creuament i placa (còpia)
#   corre.sh fotometria       # fotometria original G (phot2 cog2 zp zp2 corona2): el CONTROL
#   corre.sh canal            # fotometria per canal R, G, B i ajust (scripts nous)
#   corre.sh tot              # tot en aquest ordre
#
# Escriu només a 3-RECERCA/resultats/msb_calibrat_20261011/zp_canal/work/ (ho fixa
# original/comu.py) i a ../ (ZP_CANAL.json, rebut, registres). Els RAW es llegeixen i prou.
# Cap intèrpret escrit a pèl: el tria comprova_entorn.py (regla de Pere), i després
# es comprova que tingui pandas, photutils i skyfield.

set -euo pipefail
AQUI="${0:A:h}"                                   # .../tools/msb_calibrat_20261011/zp_canal
ORIG="$AQUI/original"
ARREL_PS="${AQUI:h:h:h:h}"                         # .../4-Photoshop
ARREL="${ARREL_PS:h}"                              # arrel del projecte
[[ "${ARREL_PS:t}" == "4-Photoshop" ]] || { echo "✗ no trobo 4-Photoshop des de $AQUI" >&2; exit 2; }
ENTORN="$ARREL/.claude/skills/postprocessat-corona/scripts/comprova_entorn.py"
RES="$ARREL_PS/3-RECERCA/resultats/msb_calibrat_20261011/zp_canal"
REG="$RES/work/_registres"
mkdir -p "$REG"

PY=""
if [[ -f "$ENTORN" ]]; then PY="$(python3 "$ENTORN" --python 2>/dev/null || true)"; fi
if [[ -z "$PY" ]]; then
  for c in $HOME/.venvs/*/bin/python(N) $(whence -pa python3 2>/dev/null); do
    if "$c" -c 'import numpy, scipy, rawpy, pandas, photutils, skyfield' 2>/dev/null; then PY="$c"; break; fi
  done
fi
[[ -n "$PY" ]] || { echo "✗ cap intèrpret amb numpy, scipy, rawpy, pandas, photutils i skyfield" >&2; exit 1; }
"$PY" -c 'import numpy, scipy, rawpy, pandas, photutils, skyfield' || {
  echo "✗ $PY no té pandas, photutils o skyfield; afegeix-los a l'entorn viu (pip install)" >&2; exit 1; }
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
echo "Intèrpret: $PY"

executa() {
  local nom="$1"; shift
  echo; echo "▶ $nom"
  local t0=$SECONDS
  "$PY" "$@" 2>&1 | tee "$REG/$nom.log"
  echo "  ($((SECONDS-t0)) s)"
}

etapa() {
  case "$1" in
    vixen)
      for s in mkdark center2 proc reg stack stack2 stack3 detect final2 rb cat_final; do
        executa "vixen_$s" "$ORIG/vixen/$s.py"
      done ;;
    sony)
      for s in darks runall reg3 numden refine moon mf3 stack2 reg4 boot boot2 scan \
               groups warp fitwarp imgs cat clean final2 final3; do
        executa "sony_$s" "$ORIG/sony/$s.py"
      done ;;
    xmatch)
      for s in cat cat2 solve refine3 final_solve; do
        executa "xmatch_$s" "$ORIG/xmatch/$s.py"
      done ;;
    fotometria)
      for s in phot2 cog2 zp zp2 corona2; do
        executa "fotometria_$s" "$ORIG/xmatch/$s.py"
      done ;;
    canal)
      executa "canal_fot" "$AQUI/fot_canal.py"
      executa "canal_zp" "$AQUI/zp_canal.py" ;;
    *) echo "✗ etapa desconeguda: $1" >&2; exit 2 ;;
  esac
}

if [[ $# -eq 0 ]]; then echo "Ús: corre.sh vixen|sony|xmatch|fotometria|canal|tot …" >&2; exit 2; fi
for e in "$@"; do
  if [[ "$e" == tot ]]; then
    for x in vixen sony xmatch fotometria canal; do etapa "$x"; done
  else
    etapa "$e"
  fi
done
echo; echo "Fet."
