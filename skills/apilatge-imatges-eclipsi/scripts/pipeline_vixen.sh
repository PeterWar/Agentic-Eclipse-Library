#!/bin/zsh
# Encadena el pipeline de la corona del tren Vixen (VSD90SS + R6 III), en
# l'ordre en què s'ha de fer. Només lectura sobre els CR3; escriu a
# ~/Desktop/Eclipse 2026/Derivats/Vixen/Corona_HDR_Vixen i
# ~/Desktop/Eclipse 2026/Derivats/Vixen/HDR4.
#
# Ús:
#   pipeline_vixen.sh                       # tot: masters prnu geometria deriva escala hdr vis tiff earthshine foto passalt hdr4
#   pipeline_vixen.sh hdr vis tiff          # només aquestes etapes, en aquest ordre
#   pipeline_vixen.sh --nomes-mostra        # ensenya les ordres i no executa res
#   pipeline_vixen.sh --prova DIR etapes…   # tot el que escriu va a DIR/Corona_HDR_Vixen i DIR/HDR4
#                                           # (CORONA_OUT i HDR4_OUT): els productes vius no es toquen
#
# Variables d'entorn que passen a les eines (vegeu references/pipeline_vixen.md):
#   CORONA_OUT / HDR4_OUT           directoris de sortida alternatius (els posa --prova)
#   SUFIX / HDR_SUFIX / FOTO_SUFIX  per no sobreescriure dins el mateix directori
#   PIXFRAC (2.0)  RAMPA_SOSTRE (0.80)  DETALL (logpolar)  CORBA (sketch)  GUANYS_DEG ...
#
# Cap intèrpret escrit a pèl: el detecta comprova_entorn.py (regla global de Pere).

set -euo pipefail
AQUI="${0:A:h}"                 # scripts/
REPO="${AQUI:h:h:h:h}"          # scripts/ → apilatge-imatges-eclipsi/ → skills/ → .claude/ → arrel
TOOLS="$REPO/research/tools"

MOSTRA=0
if [[ "${1:-}" == "--nomes-mostra" ]]; then MOSTRA=1; shift; fi
if [[ "${1:-}" == "--prova" ]]; then
  [[ -n "${2:-}" ]] || { echo "✗ --prova vol un directori" >&2; exit 2; }
  PROVA="${2:A}"; shift 2
  export CORONA_OUT="$PROVA/Corona_HDR_Vixen" HDR4_OUT="$PROVA/HDR4"
  mkdir -p "$CORONA_OUT" "$HDR4_OUT"
  echo "Passada de prova: CORONA_OUT=$CORONA_OUT  HDR4_OUT=$HDR4_OUT (els productes vius no es toquen)"
fi

PY="$(python3 "$AQUI/comprova_entorn.py" --python)" || {
  echo "✗ cap intèrpret Python amb les biblioteques de l'apilatge; executa comprova_entorn.py" >&2
  exit 1
}

if [[ $# -eq 0 ]]; then
  ETAPES=(masters prnu geometria deriva escala hdr vis tiff earthshine foto passalt hdr4)
else
  ETAPES=("$@")
fi

executa() {
  echo
  echo "▶ $*"
  if [[ $MOSTRA -eq 1 ]]; then return 0; fi
  ( cd "$REPO" && "$@" )
}

# skyfield busca de440s.bsp al directori de treball si no és a la cau: que hi sigui.
if [[ ! -f "$HOME/.cache/skyfield/de440s.bsp" ]]; then
  echo "⚠ falta ~/.cache/skyfield/de440s.bsp; skyfield el baixarà on toqui el load() (potser a l'arrel del repositori)" >&2
fi

for e in "${ETAPES[@]}"; do
  case "$e" in
    masters)   executa "$PY" "$TOOLS/masters_vixen_v2.py" ;;
    prnu)      executa "$PY" "$TOOLS/prnu_vixen.py" ;;
    geometria|deriva|escala|hdr|vis|tiff|earthshine|foto|passalt)
               executa "$PY" "$TOOLS/hdr_corona_vixen.py" "$e" ;;
    hdr4)      executa "$PY" "$TOOLS/apila_hdr4_vixen.py" mesura
               executa "$PY" "$TOOLS/apila_hdr4_vixen.py" apila
               executa "$PY" "$TOOLS/apila_hdr4_vixen.py" munta ;;
    protuberancies|capes)
               executa "$PY" "$TOOLS/apila_hdr4_vixen.py" "$e" ;;
    *) echo "✗ etapa desconeguda: $e" >&2; exit 2 ;;
  esac
done

echo
echo "Fet. Comprova el perfil K+F i la continuïtat a la sortida de 'vis', i el test d'anell a 'foto'."
