#!/bin/zsh
# cadena_v108.sh · LA CADENA DE LA V108 (Claude, 26-09-2026, nit): la de la V104–V107 (cadena_v103.sh, variant E) amb GANXOS per a les cures,
# i el muntatge sobre la V107 DE PERE. Sense cap ganxo, reprodueix la base i els 16 filtres de la V107 (control: vegeu LLEGEIX-ME.md).
#   fonts (d4 sources) → 3 franja a3d → 4 linealitzada f2 → 5 base f2b + f2c → 6 filtres f3 (E2 E1 E6 E4 E3) + ganxos per capa → assemblatge
#   → 7 estat r3 + la 56 amb la REC de la filera de punts (c0) → 8 comparació (c8) → 9 PSB de pas des de la V107 (b2) → 10 verificació (v1)
#   → 11 desament natiu COM A CÒPIA al Photoshop (només amb V108_DESA=1: Pere hi ha de donar el sí).
# Cada pas se salta si la seva sortida ja existeix (per refer-lo, esborra'n la sortida). Sortides: 4-RESULTATS/v108_20260926/cadena/<variant>/.
# GANXOS (variables d'entorn; rutes relatives a l'arrel del projecte, sense espais):
#   V108_FONTS=<carpeta sources>   fonts sense estrelles (base_G, fusion_starless, vixen_starless, sony_starless, support, star_footprints);
#                                  per defecte, 4-RESULTATS/v98_20260925/cadena_v98/d4/products/sources (la cura dels marrons en donarà una altra)
#   V108_LF=<limb_frames>          fotogrames Vixen de la caixa lunar (per defecte, 4-RESULTATS/v98_20260925/cadena_raw/limb_frames_comuna)
#   V108_CONFIG=<CONFIG.env>       A3C_RAMPES, A3C_SILUETA, A3D_BANDA (per defecte, la de la variant E: 4-RESULTATS/v103_banda_20260926/E/CONFIG.env)
#   V97_WV=<weight_vixen.npy>      pes Vixen/Sony dels ACHF azimutals (E4); passa tal qual al f3 (per defecte, el de la V97)
#   V108_F41 … V108_F56="<guió.py> [args]"   guió alternatiu per a UNA capa de filtre (41/42 NRGF, 54 MGN, 56 WOW bilateral, o qualsevol de 41–56).
#                                  Corre amb V97_SORT=<carpeta pròpia> V97_FONTS=<linealitzada> V98_FRANJA=<franja> V108_CAPES="<ids>"
#                                  V108_BASE=<base de pantalla nova, u16 RGB> V108_R=<carpeta de la variant>, i ha
#                                  d'escriure <V97_SORT>/filtres/<etiqueta>_u16.npy i <etiqueta>_alfa_u16.npy (format del f3; també s'accepta
#                                  <V97_SORT>/<una sola subcarpeta>/<etiqueta>…). «fitxers:<carpeta>» = ràsters ja calculats. Si diverses capes
#                                  porten el MATEIX guió i arguments, corre una sola vegada. Si totes les capes d'una etapa f3 tenen ganxo, l'etapa
#                                  estàndard no corre.
#   V108_FILA56=<carpeta REC>|regenera|cap   la cura de la filera de punts de la 56 (REC de la V105): per defecte, la REC calculada amb la
#                                  linealitzada E; «regenera» = la refà amb la linealitzada d'aquesta variant (fila/*_v108.py, ~4 min); «cap» = la 56
#                                  de la cadena tal qual. ⛔ Amb fonts noves que canviïn la 56 arran del limbe, la REC per defecte ja no hi correspon
#                                  i c0 ATURA (posa «regenera»); amb un ganxo per a la 56, posa «cap» (o que el ganxo ja porti la cura).
#   V108_ALFA_BASE=<npy u16>       alfa de la base (per defecte, la de l'estat V97 = la de la V107)
#   V108_REUSA=<variant>           clona (APFS, sense cost de disc) franja, linealitzada, base i filtres estàndard d'una altra variant amb les MATEIXES
#                                  fonts, fotogrames i configuració (per provar només ganxos de filtres sense refer-ho tot)
#   V108_PARAL=1|2|5               etapes f3 alhora. Per defecte 1 (en sèrie, ~19 min, pic ~12 GB: la norma dels 16 GB amb altres agents);
#                                  2 = E2 en un carril i E1 E6 E4 E3 a l'altre (~10 min, pic fins a ~22 GB); 5 = totes alhora (només amb la màquina lliure)
#   V108_MUNTA=1 [V108_B2_ARGS="--forca totes"]   pas 9: munta el PSB de pas (7,3 GB)       V108_FINS=<pas>: para després d'aquest pas
#   V108_DESA=1                    pas 11: desament natiu al Photoshop COM A CÒPIA a 1-PHOTOSHOP/V108.psb (mai no sobreescriu)
# Ús: [GANXOS] zsh 3-RECERCA/tools/v108_20260926/cadena/cadena_v108.sh <variant> [des_del_pas]
# ⛔ No editis aquest fitxer mentre una tirada corre: el zsh el llegeix a trossos i executaria fragments del fitxer nou.
set -e
cd "$(dirname "$0")/../../.."   # V113: la còpia és una carpeta menys endins que l'original
T=3-RECERCA/tools/v108_20260926/cadena; T103=3-RECERCA/tools/v103_banda_20260926; T98=3-RECERCA/tools/v98_20260925; T97=3-RECERCA/tools/v97_refundacio_20260924
R8=4-RESULTATS/v98_20260925; E=4-RESULTATS/v103_banda_20260926/E; R0=4-RESULTATS/v114_estrelles_20260928/cadena
VAR=${1:?"ús: cadena_v108.sh <variant> [des_del_pas]"}
[[ "$VAR" =~ '^[A-Za-z0-9_.-]+$' ]] || { echo "ATURAT: el nom de la variant només pot tenir lletres, xifres, _ . -"; exit 2; }
R=$R0/$VAR; DES=${2:-0}; FINS=${V108_FINS:-99}; pas() { [ "$DES" -le "$1" ] && [ "$1" -le "$FINS" ]; }
# ---- Python: el primer candidat que tingui el que cal (cap intèrpret escrit a pèl) ----
PY=""; for c in "${V108_PY:-}" "$HOME/.venvs/eines-ia-py312/bin/python" "$(command -v python3 2>/dev/null || true)" /opt/homebrew/bin/python3.12; do
  if [ -n "$c" ] && [ -x "$c" ] && "$c" -c "import numpy, scipy, cv2, numexpr, psd_tools" 2>/dev/null; then PY="$c"; break; fi; done
[ -n "$PY" ] || { echo "ATURAT: cap Python amb numpy/scipy/opencv/numexpr/psd-tools (afegeix-los a ~/.venvs/eines-ia-py312 o posa V108_PY)"; exit 3; }
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=${OPENBLAS_NUM_THREADS:-6}
$PY -c "import json; o=json.load(open('.coordination/claim.lock/owner.json')); assert o.get('serial_writes')=='HELD', o" 2>/dev/null || { echo "ATURAT: cal un claim SERIAL_WRITES viu"; exit 4; }
# ---- ganxos ----
FONTS=${V108_FONTS:-$R8/cadena_v98/d4/products/sources}; LF=${V108_LF:-$R8/cadena_raw/limb_frames_comuna}; CONFIG=${V108_CONFIG:-$E/CONFIG.env}
FILA56=${V108_FILA56:-4-RESULTATS/v105_limbe_20260926/claude/fila_REC}; PARAL=${V108_PARAL:-1}
for f in base_G.npy fusion_starless.npy vixen_starless.npy sony_starless.npy support.npy star_footprints.npy; do [ -f $FONTS/$f ] || { echo "ATURAT: falta $FONTS/$f"; exit 2; }; done
[ -f $LF/METADATA.json ] || { echo "ATURAT: falten els fotogrames de la caixa lunar ($LF)"; exit 2; }
[ -f $CONFIG ] || { echo "ATURAT: falta $CONFIG"; exit 2; }
[ "$FILA56" = cap ] || [ "$FILA56" = regenera ] || [ -f $FILA56/L56_G_moon.npy ] || { echo "ATURAT: falta $FILA56/L56_G_moon.npy (o posa V108_FILA56=cap o regenera)"; exit 2; }
[ -z "${V108_ALFA_BASE:-}" ] || [ -f "$V108_ALFA_BASE" ] || { echo "ATURAT: falta $V108_ALFA_BASE"; exit 2; }
source $CONFIG; export A3C_RAMPES A3C_SILUETA A3D_BANDA
typeset -A GANXO; for id in {41..56}; do eval "c=\${V108_F$id:-}"; [ -n "$c" ] && GANXO[$id]="$c"; done
# ---- l'entorn queda escrit: una variant no pot canviar de ganxos a mig camí ----
mkdir -p $R/temps
estat_fitxer() { [ -e "$1" ] && stat -f '%z %m' "$1" || echo absent; }
{ echo "FONTS=$FONTS"; for f in base_G fusion_starless vixen_starless sony_starless support star_footprints; do echo "  $f.npy $(estat_fitxer $FONTS/$f.npy)"; done
  echo "LF=$LF $(estat_fitxer $LF/numerator.npy)"; echo "CONFIG=$CONFIG $(shasum -a 256 $CONFIG | cut -c1-16)"; echo "V97_WV=${V97_WV:-}"; } > $R/.entorn_fonts
{ for id in ${(ko)GANXO}; do echo "V108_F$id=${GANXO[$id]}"; done; echo "FILA56=$FILA56"; echo "ALFA_BASE=${V108_ALFA_BASE:-}"; } > $R/.entorn_filtres
for n in fonts filtres; do
  if [ -f $R/ENTORN_${n:u}.txt ]; then cmp -s $R/.entorn_$n $R/ENTORN_${n:u}.txt || { echo "ATURAT: la variant $VAR es va fer amb uns altres ganxos ($R/ENTORN_${n:u}.txt); fes-ne una de nova"; diff $R/ENTORN_${n:u}.txt $R/.entorn_$n || true; rm -f $R/.entorn_fonts $R/.entorn_filtres; exit 5; }
  else mv $R/.entorn_$n $R/ENTORN_${n:u}.txt; fi; done; rm -f $R/.entorn_fonts $R/.entorn_filtres
echo "$(date '+%F %T') · variant $VAR · des del pas $DES · $PY" >> $R/cadena.log
# ---- cronòmetre: temps real i memòria màxima (RSS) de cada pas a TEMPS.tsv ----
[ -f $R/TEMPS.tsv ] || printf "pas\tsegons\tRSS_max_GB\tquan\n" > $R/TEMPS.tsv
cronometra() { local nom=$1; shift; local rc=0; /usr/bin/time -l -o $R/temps/$nom.txt "$@" || rc=$?
  printf "%s\t%s\t%s\t%s\n" $nom "$(awk '/ real /{print $1; exit}' $R/temps/$nom.txt)" "$(awk '/maximum resident set size/{printf "%.2f", $1/1073741824}' $R/temps/$nom.txt)" "$(date '+%T')" >> $R/TEMPS.tsv; return $rc; }
FR=$R/franja/A3C_franja_silueta.npz
# 1 · reutilitza la part de dalt d'una altra variant (mateixes fonts, fotogrames i configuració)
if pas 1 && [ -n "${V108_REUSA:-}" ] && [ ! -f $R/franja/A3D_FRANJA_BANDA.json ]; then
  RR=$R0/$V108_REUSA; cmp -s $RR/ENTORN_FONTS.txt $R/ENTORN_FONTS.txt || { echo "ATURAT: $V108_REUSA es va fer amb unes altres fonts/fotogrames/configuració"; exit 5; }
  for d in franja lineal base filtres_std; do [ -d $RR/$d ] && [ ! -e $R/$d ] && cp -c -R $RR/$d $R/$d; done
  echo "$(date '+%F %T') · clonades franja, lineal, base i filtres_std de $V108_REUSA" >> $R/cadena.log; fi
# 3 · la franja arran del limbe (a3d: règim net + règim de banda de l'instant)
if pas 3 && [ ! -f $R/franja/A3D_FRANJA_BANDA.json ]; then
  mkdir -p $R/franja; cp -c $R8/lineal_v98_franja/A2_GEOMETRIA.json $R8/lineal_v98_franja/A2_geometria.npz $R/franja/
  cronometra 3_a3d env A3B_LF=$LF V97_SORT=$R/franja V97_FONTS=$FONTS $PY -B $T103/a3d_franja_banda.py > $R/a3d.log 2>&1; fi
# 4 · la linealitzada (les fonts amb la franja a la caixa lunar)
if pas 4 && [ ! -f $R/lineal/LINEAL_REBUT.json ]; then cronometra 4_f2 $PY -B $T97/f2_lineal_v97.py $FONTS $FR $R/lineal > $R/f2.log 2>&1; fi
# 5 · la base (recepta b4e; la de la V96 arran del limbe)
if pas 5 && [ ! -f $R/base/base_v108_final_u16_REBUT.json ]; then mkdir -p $R/base
  cronometra 5a_f2b $PY -B $T97/f2b_base.py $R/lineal/fusion_starless.npy $R/lineal/support.npy $R/base/base_v108_u16.npy --espai assigna > $R/f2b.log 2>&1
  cronometra 5b_f2c $PY -B $T97/f2c_base_limbe.py $R/base/base_v108_u16.npy $R/base/base_v108_final_u16.npy > $R/f2c.log 2>&1; fi
# 6 · els 16 filtres: les etapes f3 estàndard (menys les que tenen totes les capes amb ganxo) i els ganxos per capa; després, l'assemblatge
typeset -A CAPES_ETAPA; CAPES_ETAPA=(E1 "41 42 43 44" E6 "45 46" E4 "47 48 49" E3 "50 51 52 53" E2 "54 55 56")
typeset -A TAG; TAG=(41 P01_NRGF 42 P01_NRGF_extrap 43 P02_RHEF 44 P02b_RHEF_ups0.35 45 P02c_RHEF_local60_native 46 P02d_RHEF_local30_native 47 03 48 03v30 49 07
  50 01 51 04 52 05 53 06 54 P03_MGN 55 P04_WOW 56 P05_WOW_bilateral)
if pas 6 && [ ! -f $R/filtres_v108/ORIGEN.tsv ]; then
  mkdir -p $R/filtres_std; cal=()
  for e in E2 E1 E6 E4 E3; do
    lliures=0; for id in ${=CAPES_ETAPA[$e]}; do [ -z "${GANXO[$id]:-}" ] && lliures=1; done
    [ $lliures = 1 ] && [ ! -f $R/filtres_std/F3_$e.json ] && cal+=$e; done
  corre_f3() { cronometra 6_f3_$1 env V97_SORT=$R/filtres_std V97_FONTS=$R/lineal V98_FRANJA=$FR $PY -B $T98/f3_filtres_v98.py $1 > $R/filtres_std/f3_$1.log 2>&1; }
  if [ ${#cal} -gt 0 ]; then
    echo "$(date '+%T') · etapes f3: $cal (V108_PARAL=$PARAL)"
    if [ "$PARAL" -ge 5 ]; then for e in $cal; do corre_f3 $e & done; wait || true
    elif [ "$PARAL" -ge 2 ]; then
      ( for e in $cal; do [ $e = E2 ] && corre_f3 E2; done ) & ( for e in $cal; do [ $e != E2 ] && corre_f3 $e; done ) & wait || true
    else for e in $cal; do corre_f3 $e; done; fi
    for e in $cal; do [ -f $R/filtres_std/F3_$e.json ] || { echo "ATURAT: l'etapa $e dels filtres ha fallat ($R/filtres_std/f3_$e.log)"; exit 6; }; done; fi
  # ganxos: un cop per guió+arguments diferents («fitxers:<carpeta>» = ràsters ja calculats, sense córrer res)
  typeset -A GRUP; for id in ${(ko)GANXO}; do GRUP[${GANXO[$id]}]="${GRUP[${GANXO[$id]}]:-}${GRUP[${GANXO[$id]}]:+ }$id"; done
  typeset -A DIR_DE
  troba() {   # troba <carpeta> <etiqueta+sufix>: <carpeta>/filtres/X.npy, <carpeta>/X.npy o una ÚNICA <carpeta>/*/X.npy
    local m; for m in $1/filtres/$2.npy $1/$2.npy; do [ -f $m ] && { echo $m; return 0; }; done
    m=( $1/*/$2.npy(N) ); [ ${#m} -eq 1 ] && { echo ${m[1]}; return 0; }
    echo "ATURAT: no trobo $2.npy (o n'hi ha més d'un) a $1: el ganxo ha d'escriure <V97_SORT>/filtres/$2.npy" >&2; return 1; }
  for c in ${(k)GRUP}; do
    ids=${GRUP[$c]}; nom=alt_${ids// /_}
    if [[ "$c" == fitxers:* ]]; then D=${c#fitxers:}; [ -d $D ] || { echo "ATURAT: no existeix $D"; exit 6; }
      [ -z "${V108_FONTS:-}" ] || echo "AVÍS: les capes $ids són ràsters ja calculats ($D) i la variant té fonts pròpies: comprova que es van calcular amb aquestes fonts"
    else D=$R/filtres_alt/$nom
      if [ ! -f $D/FET.txt ]; then mkdir -p $D
        echo "$(date '+%T') · ganxo per a les capes $ids: $c"
        cronometra 6b_$nom env V97_SORT=$D V97_FONTS=$R/lineal V98_FRANJA=$FR V108_CAPES="$ids" V108_VARIANT=$VAR V108_R=$R V108_BASE=$R/base/base_v108_final_u16.npy $PY -B ${=c} > $D/guio.log 2>&1 || { echo "ATURAT: el ganxo de les capes $ids ha fallat ($D/guio.log)"; exit 6; }
        { echo "$c"; echo "capes: $ids"; date '+%F %T'; } > $D/FET.txt; fi; fi
    for id in ${=ids}; do DIR_DE[$id]=$D; for s in _u16 _alfa_u16; do troba $D ${TAG[$id]}$s > /dev/null || exit 6; done; done; done
  # assemblatge: cada capa, de l'etapa estàndard o del seu ganxo (clons APFS)
  mkdir -p $R/filtres_v108; printf "capa\tetiqueta\torigen\n" > $R/filtres_v108/.origen
  for id in {41..56}; do tg=${TAG[$id]}; D=${DIR_DE[$id]:-$R/filtres_std}
    for s in _u16 _alfa_u16; do f=$(troba $D $tg$s) || exit 6; rm -f $R/filtres_v108/$tg$s.npy; cp -c $f $R/filtres_v108/$tg$s.npy; done
    printf "%s\t%s\t%s\n" $id $tg ${f%_alfa_u16.npy}_u16.npy >> $R/filtres_v108/.origen; done
  mv $R/filtres_v108/.origen $R/filtres_v108/ORIGEN.tsv; fi
# 7 · l'estat (r3: màscares netes dins de la Lluna, nivell sota la vora translúcida) i la 56 amb la REC de la filera de punts (c0)
if pas 7 && [ ! -f $R/estat_v108/CAPES_V98.json ]; then cronometra 7a_r3 $PY -B $T98/r3_estat_v98.py $R/filtres_v108 $R/estat_v108 $R/base/base_v108_final_u16.npy > $R/r3.log 2>&1; fi
if pas 7 && [ "$FILA56" = regenera ] && [ ! -f $R/fila_REC/REC_56/L56_G_moon.npy ]; then   # la REC de la 56 refeta amb la linealitzada i la franja d'aquesta variant
  [ -z "${GANXO[56]:-}" ] || { echo "ATURAT: V108_FILA56=regenera és per a la 56 estàndard; amb un ganxo per a la 56, posa V108_FILA56=cap"; exit 7; }
  MUS=$($PY -c "import json,sys; print(json.dumps(json.load(open(sys.argv[1]))['capes']['P05_WOW_bilateral']['mitjanes_escala']))" $R/filtres_std/F3_E2.json)
  cronometra 7b_fila_sn env V108_FILA_LINEAL=$R/lineal V108_FILA_FRANJA=$FR V108_FILA_ESTAT=$R/estat_v108 V108_FILA_OUT=$R/fila_REC $PY -B $T/fila/a3_mapa_sn_v108.py 40 > $R/fila_sn.log 2>&1
  cronometra 7b_fila_wow env V108_FILA_LINEAL=$R/lineal V108_FILA_FRANJA=$FR V108_FILA_ESTAT=$R/estat_v108 V108_FILA_OUT=$R/fila_REC V108_FILA_MUS="$MUS" $PY -B $T/fila/w_wow_v108.py REC_56 --pre snp --sn-esc 0.7 --pre-escales 0,1,2 > $R/fila_wow.log 2>&1; fi
if pas 7 && [ ! -f $R/estat_v108/FILA56.json ]; then
  if [ "$FILA56" = regenera ]; then REC=$R/fila_REC/REC_56; TOL=1000000; else REC=$FILA56; TOL=${V108_FILA56_TOL:-32}; fi
  cronometra 7b_c0 env V108_FILA56_TOL=$TOL $PY -B 3-RECERCA/tools/v114_estrelles_20260928/c0_fila56_v114.py $R/estat_v108 $REC > $R/c0.log 2>&1 || { tail -2 $R/c0.log; exit 7; }; fi
if pas 7 && [ -n "${V108_ALFA_BASE:-}" ] && [ ! -f $R/estat_v108/ALFA_BASE.txt ]; then
  rm -f $R/estat_v108/L3_alfa.npy; cp -c $V108_ALFA_BASE $R/estat_v108/L3_alfa.npy; echo "$V108_ALFA_BASE" > $R/estat_v108/ALFA_BASE.txt; fi
# 8 · comparació amb la variant E, l'estat de la V105 i la V107 (quines capes canviarien)
if pas 8 && [ ! -f $R/C8_COMPARA.json ]; then cronometra 8_c8 $PY -B $T/c8_compara_v108.py $R > $R/c8.log 2>&1; tail -4 $R/c8.log; fi
# 9 · el PSB de pas des de la V107 de Pere (7,3 GB; només amb V108_MUNTA=1) · 10 · la seva verificació
if pas 9 && [ "${V108_MUNTA:-0}" = 1 ] && [ ! -f $R/V108_stage_MUNTATGE.json ]; then
  [ -f $R/V108_stage.psb ] && { echo "ATURAT: hi ha un $R/V108_stage.psb sense rebut (muntatge interromput?): revisa'l i treu-lo a mà"; exit 9; }
  cronometra 9_b2 $PY -B $T/b2_munta_v108.py $R/estat_v108 $R/V108_stage.psb ${=V108_B2_ARGS:-} > $R/b2.log 2>&1; tail -1 $R/b2.log; fi
if pas 10 && [ -f $R/V108_stage_MUNTATGE.json ] && [ ! -f $R/V1_STAGE.json ]; then cronometra 10_v1 $PY -B $T/v1_verifica_v108.py $R/V108_stage.psb $R/estat_v108 $R/V1_STAGE.json > $R/v1.log 2>&1; tail -1 $R/v1.log; fi
# 11 · el desament natiu al Photoshop COM A CÒPIA (⛔ només amb el sí de Pere: V108_DESA=1), les portes i la verificació final
if pas 11 && [ "${V108_DESA:-0}" = 1 ]; then
  [ -f 1-PHOTOSHOP/V108.psb ] && { echo "ATURAT: 1-PHOTOSHOP/V108.psb ja existeix (mai no se sobreescriu)"; exit 11; }
  grep -q '"veredicte": "PASSA"' $R/V1_STAGE.json 2>/dev/null || { echo "ATURAT: el v1 del PSB de pas no passa (o no hi és)"; exit 11; }
  mkdir -p $R/vistes; zsh $T/desa_natiu_v108.sh $R/V108_stage.psb 1-PHOTOSHOP/V108.psb $R/vistes
  $PY $T97/p6_compost_fusionat.py 1-PHOTOSHOP/V108.psb $R/vistes/V108_llenc_sencer.tif | tee $R/P6_COMPOST.txt
  bash 3-RECERCA/tools/capes_totals_v14/porta_photoshop.sh "$PWD/1-PHOTOSHOP/V108.psb" 2>&1 | tail -1 | tee $R/PORTA.txt
  shasum -a 256 1-PHOTOSHOP/V108.psb | tee $R/SHA_V108.txt
  $PY -B $T/v1_verifica_v108.py 1-PHOTOSHOP/V108.psb $R/estat_v108 $R/V1_V108.json | tail -1; fi
du -sk $R | awk '{printf "disc de la variant (du, els clons APFS hi compten sencers): %.1f GB\n", $1/1048576}'
echo CADENA_V108_${VAR}_FETA
