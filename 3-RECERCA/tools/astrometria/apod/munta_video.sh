#!/bin/zsh
# Els tres passos de l'APOD que el 16-08-2026 es van fer a mà (ordres recuperades
# de la transcripció de la sessió 604fa71e), ara guionitzats:
#
#   1. ffmpeg: fotogrames d'animacio.py → where_newton_would_have_put_it.mp4 i .gif
#   2. poster.jpg = fotograma f00324 (fase «blink», estat «what the sensor recorded»)
#   3. JPEG a 2400 px (qualitat 88, progressius) de les dues netes (render_net.py) i
#      les dues marcades (mascara_estrelles.py), i imgs.json amb els sis data-URI
#      base64 que espera munta.py: vixen_net, vixen_mark, sony_net, sony_mark, video, poster
#
# Rutes: totes de comu.py (ESTRELLES_WORK, ESTRELLES_OUT, APOD_OUT).
#   fotogrames    $ESTRELLES_WORK/apod/frames/f%05d.png       (animacio.py)
#   netes         $APOD_OUT/eclipsi_{sony_300mm,vixen_vsd90ss}_net.png   (render_net.py)
#   marcades      $ESTRELLES_OUT/estrelles_{sony,vixen}_marcades.png     (mascara_estrelles.py)
#   surt          $APOD_OUT/where_newton_would_have_put_it.{mp4,gif}
#                 $ESTRELLES_WORK/apod/{poster.jpg, sony_net.jpg, sony_mark.jpg,
#                                       vixen_net.jpg, vixen_mark.jpg, imgs.json}
#
# Ús:  munta_video.sh            # els tres passos
#      munta_video.sh video      # només mp4+gif
#      munta_video.sh poster     # només el poster
#      munta_video.sh imgs       # només JPEG + imgs.json (necessita el mp4 i el poster fets)
#
# Cap intèrpret escrit a pèl: el detecta comprova_entorn.py (regla global de Pere).

set -euo pipefail
AQUI="${0:A:h}"                       # research/tools/astrometria/apod
ASTRO="${AQUI:h}"                     # research/tools/astrometria
REPO="${ASTRO:h:h:h}"                 # arrel del repositori
COMPROVA="$REPO/.claude/skills/postprocessat-corona/scripts/comprova_entorn.py"

PY="$(python3 "$COMPROVA" --python)" || {
  echo "✗ cap intèrpret Python amb les biblioteques (PIL); executa comprova_entorn.py" >&2
  exit 1
}
FFMPEG="$(command -v ffmpeg || true)"
[[ -n "$FFMPEG" ]] || { echo "✗ falta ffmpeg (brew install ffmpeg)" >&2; exit 1; }

# rutes del contracte comu.py
WORK="$(cd "$ASTRO" && "$PY" -c 'import comu; print(comu.work("apod"))')"
OUT_EST="$(cd "$ASTRO" && "$PY" -c 'import comu; print(comu.out())')"
OUT_APOD="$(cd "$ASTRO" && "$PY" -c 'import comu; print(comu.apod())')"
FRAMES="$WORK/frames"
MP4="$OUT_APOD/where_newton_would_have_put_it.mp4"
GIF="$OUT_APOD/where_newton_would_have_put_it.gif"

if [[ $# -eq 0 ]]; then PASSOS=(video poster imgs); else PASSOS=("$@"); fi

for p in "${PASSOS[@]}"; do
  case "$p" in
    video)
      [[ -f "$FRAMES/f00000.png" ]] || { echo "✗ no hi ha fotogrames a $FRAMES: executa animacio.py" >&2; exit 1; }
      echo "▶ ffmpeg → $MP4"
      "$FFMPEG" -y -loglevel error -framerate 30 -i "$FRAMES/f%05d.png" \
        -c:v libx264 -pix_fmt yuv420p -crf 19 -preset slow -movflags +faststart "$MP4"
      echo "▶ ffmpeg → $GIF"
      "$FFMPEG" -y -loglevel error -i "$MP4" \
        -vf "fps=12,scale=800:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=160[p];[b][p]paletteuse=dither=bayer:bayer_scale=4" \
        "$GIF"
      ls -la "$MP4" "$GIF"
      ;;
    poster)
      [[ -f "$FRAMES/f00324.png" ]] || { echo "✗ falta $FRAMES/f00324.png: executa animacio.py" >&2; exit 1; }
      echo "▶ poster.jpg ← f00324.png"
      "$PY" - "$FRAMES/f00324.png" "$WORK/poster.jpg" <<'PYEOF'
import sys
from PIL import Image
Image.open(sys.argv[1]).convert('RGB').save(sys.argv[2], quality=84, optimize=True)
print("  ", sys.argv[2])
PYEOF
      ;;
    imgs)
      [[ -f "$MP4" ]] || { echo "✗ falta $MP4: fes primer el pas video" >&2; exit 1; }
      [[ -f "$WORK/poster.jpg" ]] || { echo "✗ falta $WORK/poster.jpg: fes primer el pas poster" >&2; exit 1; }
      echo "▶ JPEG 2400 px + imgs.json → $WORK"
      "$PY" - "$WORK" "$OUT_APOD" "$OUT_EST" "$MP4" <<'PYEOF'
import base64, json, os, sys
from PIL import Image
W, D, E, MP4 = sys.argv[1:5]
jobs = [('vixen_net',  os.path.join(D, 'eclipsi_vixen_vsd90ss_net.png')),
        ('vixen_mark', os.path.join(E, 'estrelles_vixen_marcades.png')),
        ('sony_net',   os.path.join(D, 'eclipsi_sony_300mm_net.png')),
        ('sony_mark',  os.path.join(E, 'estrelles_sony_marcades.png'))]
uris = {}
tot = 0
for nom, src in jobs:
    if not os.path.exists(src):
        sys.exit(f"✗ falta {src} (render_net.py / mascara_estrelles.py)")
    im = Image.open(src).convert('RGB'); w = 2400
    im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    out = os.path.join(W, f'{nom}.jpg')
    im.save(out, quality=88, optimize=True, progressive=True)
    n = os.path.getsize(out); tot += n
    uris[nom] = 'data:image/jpeg;base64,' + base64.b64encode(open(out, 'rb').read()).decode()
    print(f'   {nom:12s} {n/1024:7.0f} KB')
uris['video'] = 'data:video/mp4;base64,' + base64.b64encode(open(MP4, 'rb').read()).decode()
uris['poster'] = 'data:image/jpeg;base64,' + base64.b64encode(open(os.path.join(W, 'poster.jpg'), 'rb').read()).decode()
json.dump(uris, open(os.path.join(W, 'imgs.json'), 'w'))
print(f'   video b64 {len(uris["video"])/1024/1024:.2f} MB · poster {len(uris["poster"])/1024:.0f} KB · '
      f'imgs.json {os.path.getsize(os.path.join(W, "imgs.json"))/1024/1024:.2f} MB')
PYEOF
      ;;
    *) echo "✗ pas desconegut: $p (video | poster | imgs)" >&2; exit 2 ;;
  esac
done
