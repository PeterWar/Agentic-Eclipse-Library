#!/bin/zsh
# Encadena la cadena d'astrometria de l'eclipsi del 12-08-2026 (predicció del
# camp, detecció cega d'estrelles als dos trens, creuament i placa, fotometria
# absoluta, auditoria escèptica, deflexió, màscares i lliurables de l'APOD), en
# l'ordre en què s'ha de fer. Només lectura sobre els RAW i els darks; escriu a
# $ESTRELLES_WORK (intermedis), $ESTRELLES_OUT (productes) i $APOD_OUT
# (lliurables) tal com els resol comu.py (per defecte, l'Escriptori).
#
# Ús:
#   pipeline_estrelles.sh                       # tot: catalegs prediccio sony vixen xmatch fotometria
#                                               #      esceptic deflexio mascara apod acceptacio
#   pipeline_estrelles.sh sony vixen xmatch     # només aquestes etapes, en aquest ordre
#   pipeline_estrelles.sh --nomes-mostra        # ensenya les ordres i no executa res
#   pipeline_estrelles.sh --prova DIR etapes…   # ESTRELLES_WORK=DIR/Estrelles_work, ESTRELLES_OUT=DIR/Estrelles,
#                                               # APOD_OUT=DIR/APOD: els productes vius de l'Escriptori no es toquen
#
# Etapes (l'ordre exacte de cada MAPA_*.md; les rutes són absolutes i s'executa des de l'arrel del repositori):
#   catalegs    prediccio/baixa_catalegs.sh (hip_main.dat, tyc2.tsv, tyc2_deep.tsv a $CATALEGS) i comprova l'efemèride
#   prediccio   sol_planetes estrelles combina final                              (< 2 s)
#   sony        darks runall reg3 numden refine moon mf3 stack2 reg4 boot boot2 scan groups warp fitwarp imgs cat clean final2 final3   (~6,5 min, ~8,5 GB)
#   sony_extra  build gain   (opcionals: F_*.npy i evidència del guany 3,323; NO és a la llista per defecte)
#   vixen       mkdark center2 proc reg stack stack2 stack3 detect final2 rb cat_final fitpsf fit2   (~3 min, ~4,8 GB)
#   xmatch      cat cat2 solve refine3 final_solve                                (~10 s)
#   fotometria  phot2 cog2 zp zp2 bemporad identificacions corona2 wings wings2 orient summary   (~35 s)
#   esceptic    inject2 zprefit chain cross cross2 unic amb sat                   (~8 s)
#   deflexio    fusiona_csv deflexio retall_estrella moviments                    (~5 s)
#   mascara     mascara_estrelles sony · vixen                                    (~10 s)
#   apod        render_net figures animacio munta_video.sh munta                  (~65 s; ffmpeg)
#   acceptacio  test_acceptacio.py (sempre al final)
#
# ⚠ Advertiments de disseny (síntesi §7):
#   · «esceptic» i «deflexio» només valen amb els intermedis FRESCOS de «sony» i «xmatch»/«fotometria»
#     (offsets6.pkl, masterdark_*.npy, bkg_*.npy, cogf_*.npz, cat2_*.csv, zp_*.csv, IDENTIFICACIONS_*.csv,
#     final_match_*.csv): si es criden sols contra un WORK buit, fallen o barregen sessions.
#   · «apod» no es pot completar sense apod.tpl.html al costat de munta.py (astrometria/apod/apod.tpl.html,
#     font escrita a mà que no genera ningú); «mascara» ha d'anar abans d'«apod».
#   · «identificacions» va a «fotometria», després de bemporad.py (flux_tot/Vobs/dV surten de bemp_*.csv).
#   · Cada ordre deixa la seva sortida (stdout+stderr) a $ESTRELLES_WORK/_registres/<script>.log; test_acceptacio.py
#     hi llegeix el σ(ε) de deflexio.py.
#
# Variables d'entorn que passen a les eines (vegeu comu.py): DADES_300MM, DADES_VIXEN_UNF, DADES_VIXEN, DARKS_SONY,
# DARKS_R6, CATALEGS, HALO_PARAMS, EFEMERIDE, ESTRELLES_WORK, ESTRELLES_OUT, APOD_OUT.
#
# Cap intèrpret escrit a pèl: el detecta comprova_entorn.py (regla global de Pere).

set -euo pipefail
AQUI="${0:A:h}"                 # research/tools/astrometria/
REPO="${AQUI:h:h:h}"            # astrometria/ → tools/ → research/ → arrel
ENTORN="$REPO/.claude/skills/postprocessat-corona/scripts/comprova_entorn.py"

MOSTRA=0
if [[ "${1:-}" == "--nomes-mostra" ]]; then MOSTRA=1; shift; fi
if [[ "${1:-}" == "--prova" ]]; then
  [[ -n "${2:-}" ]] || { echo "✗ --prova vol un directori" >&2; exit 2; }
  PROVA="${2:A}"; shift 2
  export ESTRELLES_WORK="$PROVA/Estrelles_work" ESTRELLES_OUT="$PROVA/Estrelles" APOD_OUT="$PROVA/APOD"
  mkdir -p "$ESTRELLES_WORK" "$ESTRELLES_OUT" "$APOD_OUT"
  echo "Passada de prova: ESTRELLES_WORK=$ESTRELLES_WORK  ESTRELLES_OUT=$ESTRELLES_OUT  APOD_OUT=$APOD_OUT (els productes vius no es toquen)"
fi

PY="$(python3 "$ENTORN" --python)" || {
  echo "✗ cap intèrpret Python amb les biblioteques del postprocessat; executa comprova_entorn.py" >&2
  exit 1
}
export PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

# On són el WORK i l'efemèride segons comu.py (respecta les variables d'entorn).
WORK="$("$PY" -c 'import sys; sys.path.insert(0, sys.argv[1]); import comu; print(comu.ESTRELLES_WORK)' "$AQUI")"
EFEM="$("$PY" -c 'import sys; sys.path.insert(0, sys.argv[1]); import comu; print(comu.EFEMERIDE)' "$AQUI")"
REG="$WORK/_registres"

if [[ $# -eq 0 ]]; then
  ETAPES=(catalegs prediccio sony vixen xmatch fotometria esceptic deflexio mascara apod acceptacio)
else
  ETAPES=("$@")
fi

executa() {
  echo
  echo "▶ $*"
  if [[ $MOSTRA -eq 1 ]]; then return 0; fi
  # nom del registre: <script>[_args].log
  local nom="" a
  for a in "$@"; do
    if [[ -z "$nom" ]]; then
      if [[ "$a" == *.py || "$a" == *.sh ]]; then nom="${${a:t}%.*}"; fi
    else
      nom="${nom}_${a}"
    fi
  done
  [[ -n "$nom" ]] || nom="ordre"
  mkdir -p "$REG"
  ( cd "$REPO" && "$@" ) 2>&1 | tee "$REG/$nom.log"
}

# skyfield busca de440s.bsp al directori de treball si no és a la cau: que hi sigui.
if [[ ! -f "$EFEM" ]]; then
  echo "⚠ falta l'efemèride $EFEM; comu.efemeride() fallarà (baixa-la a ~/.cache/skyfield/ o exporta EFEMERIDE)" >&2
fi

if [[ $MOSTRA -eq 0 ]]; then
  echo "Intèrpret: $PY"
  echo "WORK: $WORK   registres: $REG"
fi

for e in "${ETAPES[@]}"; do
  case "$e" in
    catalegs)
      executa "$AQUI/prediccio/baixa_catalegs.sh" ;;
    prediccio)
      for s in sol_planetes estrelles combina final; do
        executa "$PY" "$AQUI/prediccio/$s.py"
      done ;;
    sony)
      for s in darks runall reg3 numden refine moon mf3 stack2 reg4 boot boot2 scan \
               groups warp fitwarp imgs cat clean final2 final3; do
        executa "$PY" "$AQUI/sony/$s.py"
      done ;;
    sony_extra)
      executa "$PY" "$AQUI/sony/build.py"      # opcional (F_SNR/F_DEN/F_COV/F_IMG/F_WT.npy)
      executa "$PY" "$AQUI/sony/gain.py" ;;    # opcional, evidència del GAIN 3,323
    vixen)
      for s in mkdark center2 proc reg stack stack2 stack3 detect final2 rb cat_final fitpsf fit2; do
        executa "$PY" "$AQUI/vixen/$s.py"
      done ;;
    xmatch)
      for s in cat cat2 solve refine3 final_solve; do
        executa "$PY" "$AQUI/xmatch/$s.py"
      done ;;
    fotometria)
      for s in phot2 cog2 zp zp2 bemporad identificacions corona2 wings wings2 orient summary; do
        executa "$PY" "$AQUI/xmatch/$s.py"
      done ;;
    esceptic)
      for s in inject2 zprefit chain cross cross2 unic amb sat; do
        executa "$PY" "$AQUI/esceptic/$s.py"
      done ;;
    deflexio)
      for s in fusiona_csv deflexio retall_estrella moviments; do
        executa "$PY" "$AQUI/deflexio/$s.py"
      done ;;
    mascara)
      executa "$PY" "$AQUI/deflexio/mascara_estrelles.py" sony
      executa "$PY" "$AQUI/deflexio/mascara_estrelles.py" vixen ;;
    apod)
      executa "$PY" "$AQUI/apod/render_net.py"
      executa "$PY" "$AQUI/apod/figures.py"
      executa "$PY" "$AQUI/apod/animacio.py"
      executa "$AQUI/apod/munta_video.sh"
      executa "$PY" "$AQUI/apod/munta.py" ;;
    acceptacio)
      executa "$PY" "$AQUI/test_acceptacio.py" ;;
    *) echo "✗ etapa desconeguda: $e" >&2; exit 2 ;;
  esac
done

echo
echo "Fet. Comprova 38/24, 38/38 i 22/24, escala 3,2020/2,1495, ZP 14,167/14,205 i B/B☉ 1,134e-11/2,772e-11 a la sortida de 'acceptacio'."
