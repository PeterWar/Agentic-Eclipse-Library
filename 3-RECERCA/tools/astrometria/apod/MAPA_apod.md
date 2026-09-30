# MAPA — subàrea `apod` (lliurables de «Stars Beside an Eclipsed Sun» / «Where Newton would have put it»)

Promoció del 17-08-2026 dels scripts del rescat
`research/tools/rescat_scratchpad_2026-08-17/deflexio_apod_2027_16-08/` (sessió 604fa71e del 16-08) i dels
assets que el rescat va copiar a `apod_assets/`. Cap algorisme ni constant no canvia; les rutes surten
totes de `../comu.py`, i els **tres passos que el 16-08 es van fer a mà** (ffmpeg, poster, imgs.json) ara
són `munta_video.sh`, escrit amb les ordres exactes recuperades de la transcripció de la sessió 604fa71e.

## 1. Fitxer promogut → origen

| Promogut (`research/tools/astrometria/apod/`) | Origen | Què canvia |
|---|---|---|
| `render_net.py` | `deflexio_apod_2027_16-08/render_net.py` | `SORTIDA` → `comu.apod()`; RAW → `comu.DADES_300MM/DSC06993.ARW`, `comu.DADES_VIXEN_UNF/572A2983.CR3`; marcades → `comu.out()/estrelles_*_marcades.png` |
| `figures.py` | `deflexio_apod_2027_16-08/figures.py` | `os.chdir(comu.work("apod"))` al principi: figA/figB.svg van al WORK en lloc del cwd. Els 15 moviments i els 38+24 r/R☉ continuen incrustats |
| `animacio.py` | `deflexio_apod_2027_16-08/animacio.py` | `FRAMES` (scratchpad volàtil 604fa71e) → `comu.work("apod")/frames`; RAW → `comu.DADES_VIXEN_UNF/572A2983.CR3` |
| `munta.py` | `deflexio_apod_2027_16-08/munta.py` | plantilla `apod.tpl.html` del costat de l'script; `figA/figB.svg` i `imgs.json` de `comu.work("apod")` (si les figures no hi són, agafa les còpies del rescat del costat); escriu `work("apod")/apod.html` **i** la còpia `comu.apod()/APOD_submission.html` (abans es feia amb `cp` a mà) |
| `munta_video.sh` | **NOU** (zsh): els tres passos no guionitzats | ffmpeg mp4+gif, poster (f00324, q84), JPEG 2400 px q88 progressius + `imgs.json` |
| `apod.tpl.html` | `apod_assets/apod.tpl.html` (font escrita a mà, 33.789 B) | còpia, sense tocar |
| `figA.svg`, `figB.svg` | `apod_assets/` (sortida de figures.py del 16-08) | còpia de referència; `figures.py` els regenera **byte-idèntics** |
| `poster.jpg` | `apod_assets/poster.jpg` | còpia de referència; `munta_video.sh poster` el regenera **byte-idèntic** |

## 2. Ordre d'execució (des de qualsevol cwd; `$PY` = `comprova_entorn.py --python`)

Requisits previs d'altres subàrees: `estrelles_*_marcades.png` a `comu.out()` (etapa `mascara`).

```
$PY research/tools/astrometria/apod/render_net.py       # ~10 s   → APOD/eclipsi_{sony_300mm,vixen_vsd90ss}_net.png + _2400.jpg, estrelles_*_marcades_2400.jpg
$PY research/tools/astrometria/apod/figures.py          # <1 s    → WORK/apod/figA.svg, figB.svg
$PY research/tools/astrometria/apod/animacio.py         # ~49 s   → WORK/apod/frames/f00000…f00713.png (714)
research/tools/astrometria/apod/munta_video.sh          # ~5 s    → APOD/where_newton_would_have_put_it.{mp4,gif}; WORK/apod/{poster,sony_net,sony_mark,vixen_net,vixen_mark}.jpg, imgs.json
$PY research/tools/astrometria/apod/munta.py            # <1 s    → WORK/apod/apod.html i APOD/APOD_submission.html
```

`munta_video.sh` també accepta un pas sol: `video`, `poster` o `imgs`.

## 3. Entrades i sortides

| Script | Llegeix | Escriu |
|---|---|---|
| `render_net.py` | DSC06993.ARW, 572A2983.CR3; `out()/estrelles_{sony,vixen}_marcades.png` | `apod()/eclipsi_sony_300mm_net.png` (3984×2660) i `_2400.jpg`; `apod()/eclipsi_vixen_vsd90ss_net.png` (6959×4639) i `_2400.jpg`; `apod()/estrelles_{sony,vixen}_marcades_2400.jpg` |
| `figures.py` | res (tot incrustat) | `work("apod")/figA.svg`, `figB.svg` |
| `animacio.py` | 572A2983.CR3; fonts Arial Bold/Arial/Menlo del sistema | `work("apod")/frames/f%05d.png` (714, 1600×900); stdout «HIP 46345 · r = 2,646 R☉ · Einstein 0,662″ = 0,308 px · Newton 0,331″ = 0,154 px» |
| `munta_video.sh` | frames; `apod()/eclipsi_*_net.png`; `out()/estrelles_*_marcades.png` | `apod()/where_newton_would_have_put_it.mp4` (h264 crf 19 preset slow, yuv420p, faststart) i `.gif` (fps 12, 800 px, 160 colors, bayer 4); `work("apod")/poster.jpg`, `{vixen,sony}_{net,mark}.jpg`, `imgs.json` (claus vixen_net, vixen_mark, sony_net, sony_mark, video, poster: data-URI base64) |
| `munta.py` | `apod.tpl.html` (script dir), `work("apod")/figA.svg`, `figB.svg`, `imgs.json` | `work("apod")/apod.html` → còpia `apod()/APOD_submission.html` |

Dependències externes: `ffmpeg` (`/opt/homebrew/bin/ffmpeg`, Lavf 62.12), fonts de macOS
(`/System/Library/Fonts/Supplemental/Arial Bold.ttf`, `Arial.ttf`, `/System/Library/Fonts/Menlo.ttc`),
Pillow, rawpy, scipy.

## 4. Què s'ha provat i amb quin resultat (17-08-2026, 19:36–19:38)

Variables: `ESTRELLES_WORK=~/Desktop/Eclipse 2026/_prova_skill/Estrelles_work`,
`ESTRELLES_OUT=…/_prova_skill/Estrelles`, `APOD_OUT=…/_prova_skill/APOD`; intèrpret
`~/.venvs/eines-ia-py312/bin/python`; cwd `/tmp`. Les marcades d'entrada eren les que
`mascara_estrelles.py` (subàrea deflexio) acabava d'escriure al mateix OUT de prova.

| Prova | Cost | Resultat contra el viu (`~/Desktop/Eclipse 2026/APOD/`, i el scratchpad 604fa71e que encara existeix) |
|---|---|---|
| `render_net.py` | 9,8 s | `eclipsi_sony_300mm_net.png`, `eclipsi_vixen_vsd90ss_net.png` i `eclipsi_sony_300mm_net_2400.jpg` **byte-idèntics** (cmp) |
| `figures.py` | 0,02 s | `figA.svg`, `figB.svg` **byte-idèntics** al rescat |
| `animacio.py` | 48,8 s | 714 fotogrames; f00000/00150/00324/00500/00713 **byte-idèntics** als del scratchpad 604; imprimeix **0,662″ = 0,308 px** (r = 2,646 R☉) |
| `munta_video.sh` | 5,0 s | mp4 (3.635.441 B) i gif (14.051.695 B) **byte-idèntics** al viu; `poster.jpg`, `sony_net.jpg`, `vixen_net.jpg` **byte-idèntics** als de `_fonts_apod_scratchpad_16-08/`; `sony_mark.jpg`/`vixen_mark.jpg` diferents (les marcades noves porten més etiquetes: vegeu MAPA_deflexio §5) |
| `munta.py` | 0,05 s | `APOD_submission.html` de 10,24 MB, zero placeholders; **idèntic al viu un cop substituïts els dos data-URI de les marcades** (verificat per programa) |

## 5. Què he hagut de canviar (línia a línia)

- `render_net.py`: `SORTIDA = "/Users/…/APOD"` → `str(comu.apod())`; els dos `path=`; `src = f"/Users/…/Estrelles/{base}.png"` → `str(comu.out() / f"{base}.png")`. Paràmetres (box 16/24, suau 1,4, arcsinh/40, percentils 1–99,9, 0,46/0,95, tint, q92 subsampling 0) intactes.
- `figures.py`: afegit `os.chdir(comu.work("apod"))`. Cap número tocat.
- `animacio.py`: `FRAMES = (".../604fa71e-.../scratchpad/frames")` → `str(comu.work("apod") / "frames")`; el `rawpy.imread` del CR3. Guió, mides, colors, textos: intactes.
- `munta.py`: reescrit només en rutes (plantilla al costat de l'script, figures/imgs al WORK, còpia final a APOD_OUT). La lògica (substitució de marcadors, entitats numèriques per al no-ASCII, ordre dels sis data-URI) és la mateixa; comprovat per l'HTML resultant.
- `munta_video.sh` (nou): les ordres són les de la transcripció del 16-08 (última iteració, la que va produir els fitxers vius): `ffmpeg -framerate 30 -c:v libx264 -pix_fmt yuv420p -crf 19 -preset slow -movflags +faststart`; gif `fps=12,scale=800:-1:flags=lanczos,palettegen=max_colors=160,paletteuse=dither=bayer:bayer_scale=4`; poster `frames/f00324.png` amb `quality=84, optimize=True`; JPEG `quality=88, optimize=True, progressive=True` a 2400 px LANCZOS. Rutes: `comu.work("apod")`, `comu.out()`, `comu.apod()` consultades a `comu.py` per l'intèrpret detectat.

## 6. Pendent / límits

- `figures.py` duu els 15 moviments (de `moviments.py`) i els 62 r/R☉ (de `deflexio.py`) **incrustats**: si mai es reculen els CSV, s'han de tornar a copiar a mà (mapes, nota 7).
- `apod.tpl.html` és font escrita a mà (text de l'APOD): no la genera ningú.
- Els JPEG marcats de l'HTML canvien respecte del lliurament del 16-08 perquè `fusiona_csv.py` posa nom a totes les identificades; si es vol l'HTML byte-idèntic al viu, s'ha de muntar amb `estrelles_*_marcades.png` de `~/Desktop/Eclipse 2026/Estrelles/`.
- No s'ha provat el camí sense `ffmpeg` ni sense fonts del sistema (animacio cau a `load_default`).
