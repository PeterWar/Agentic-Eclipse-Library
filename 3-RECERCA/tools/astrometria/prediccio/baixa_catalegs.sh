#!/bin/zsh
# Comprova que els catàlegs de la cadena d'estrelles són a comu.CATALEGS
# (per defecte ~/Desktop/Eclipse 2026/Derivats/Astrometria/Estrelles/catalegs;
# variable CATALEGS
# per redirigir-ho) i baixa del CDS/VizieR els que faltin, amb curl:
#
#   hip_main.dat    Hipparcos CDS I/239 (53.316.318 B, sense comprimir; el .gz no
#                   existeix al servidor i torna un HTML d'error)
#   tyc2.tsv        Tycho-2 I/259, centre 142,10549 +14,90721, radi 4,2°, VT<9,0
#                   (predicció: combina.py)
#   tyc2_deep.tsv   Tycho-2 I/259, mateix centre, radi 5,0°, VT<12,5, amb pmRA/pmDE
#                   (creuament: xmatch/cat.py)
#
# Les URL són les de les capçaleres dels fitxers rescatats (estrelles_placa_flats_16-08/
# tyc2.tsv i xmatch/tyc2_deep.tsv). Si els tres fitxers hi són, no fa res.
# Una consulta nova a VizieR pot donar un fitxer amb capçalera de data diferent
# però les mateixes files; per això, si el fitxer ja existeix, NO es torna a baixar.
#
# Ús:  baixa_catalegs.sh            # comprova i baixa el que falti
#      baixa_catalegs.sh --nomes-mostra   # només diu què faria
#
# Cap intèrpret escrit a pèl: el detecta comprova_entorn.py (regla global de Pere);
# només es fa servir per llegir comu.CATALEGS. Si no n'hi ha cap, es cau al
# defecte de comu.py.

set -euo pipefail
AQUI="${0:A:h}"                       # prediccio/
ASTRO="${AQUI:h}"                     # astrometria/
REPO="${ASTRO:h:h:h}"                 # astrometria/ → tools/ → research/ → arrel

MOSTRA=0
if [[ "${1:-}" == "--nomes-mostra" ]]; then MOSTRA=1; shift; fi

DETECTA="$REPO/.claude/skills/postprocessat-corona/scripts/comprova_entorn.py"
CAT=""
if [[ -f "$DETECTA" ]]; then
  PY="$(python3 "$DETECTA" --python 2>/dev/null || true)"
  if [[ -n "$PY" ]]; then
    CAT="$(cd "$ASTRO" && "$PY" -c 'import comu; print(comu.CATALEGS)' 2>/dev/null || true)"
  fi
fi
if [[ -z "$CAT" ]]; then
  CAT="${CATALEGS:-$HOME/Desktop/Eclipse 2026/Derivats/Astrometria/Estrelles/catalegs}"
fi
echo "Catàlegs a: $CAT"
mkdir -p "$CAT"

URL_HIP='https://cdsarc.cds.unistra.fr/ftp/I/239/hip_main.dat'
URL_TYC2='https://vizier.cds.unistra.fr/viz-bin/asu-tsv?-source=I/259/tyc2&-c=142.10549+%2B14.90721&-c.rd=4.2&-out.add=_RAJ2000,_DEJ2000,_r&-out=TYC1,TYC2,TYC3,BTmag,VTmag,HIP&-out.max=6000&VTmag=%3C9.0'
URL_TYC2_DEEP='https://vizier.cds.unistra.fr/viz-bin/asu-tsv?-source=I/259/tyc2&-c=142.10549+%2B14.90721&-c.rd=5.0&-out.add=_RAJ2000,_DEJ2000,_r&-out=TYC1,TYC2,TYC3,BTmag,VTmag,HIP,pmRA,pmDE&-out.max=30000&VTmag=%3C12.5'

baixa() {   # baixa NOM URL MIDA_MINIMA_BYTES
  local nom="$1" url="$2" minim="$3" dest="$CAT/$1"
  if [[ -s "$dest" ]]; then
    echo "✓ $nom ja hi és ($(stat -f %z "$dest") B)"
    return 0
  fi
  echo "▶ falta $nom → $url"
  if [[ $MOSTRA -eq 1 ]]; then return 0; fi
  curl -fsSL --retry 3 --max-time 900 -o "$dest.part" "$url"
  local mida; mida=$(stat -f %z "$dest.part")
  if (( mida < minim )) || head -c 300 "$dest.part" | grep -qi '<html'; then
    echo "✗ $nom: la baixada no sembla el catàleg ($mida B; potser un HTML d'error). Es deixa a $dest.part" >&2
    return 1
  fi
  mv "$dest.part" "$dest"
  echo "✓ $nom baixat ($mida B)"
}

baixa hip_main.dat  "$URL_HIP"       50000000
baixa tyc2.tsv      "$URL_TYC2"      5000
baixa tyc2_deep.tsv "$URL_TYC2_DEEP" 100000

# skyfield: l'efemèride DE440s no és un catàleg però la cadena la vol a la cau.
EFEM="${EFEMERIDE:-$HOME/.cache/skyfield/de440s.bsp}"
if [[ -f "$EFEM" ]]; then
  echo "✓ efemèride $EFEM"
else
  echo "⚠ falta l'efemèride $EFEM (32,7 MB): comu.efemeride() fallarà; baixa-la a ~/.cache/skyfield/ (https://ssd.jpl.nasa.gov/ftp/eph/planets/bsp/de440s.bsp)" >&2
fi
