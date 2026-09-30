#!/usr/bin/env python3
"""«Where Newton would have put it» — animació per a l'APOD.

Tres temps i prou: la foto sencera → el zoom → el moviment.

El cercle groc apareix sobre HIP 46345 al pla general i JA NO SE'N VA: la
càmera baixa amb ell, sempre centrat a l'estrella. El zoom s'atura cinc
vegades abans que a les versions anteriors —camp final de 140 píxels de
sensor, 5,0′ × 2,8′— i allà l'estrella parpelleja entre la posició que va
registrar el sensor i la que li tocaria si la deflexió fos la de Newton.
"""
import math
import os
import sys
from pathlib import Path
import numpy as np
import rawpy
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu  # noqa: E402

# abans: el scratchpad volàtil de la sessió 604fa71e; ara el WORK de l'APOD
FRAMES = str(comu.work("apod") / "frames")
os.makedirs(FRAMES, exist_ok=True)

W, H, FPS = 1600, 900, 30
ESC, R_SOL, ALPHA = 2.1495, 946.66, 1.7516
SOL = (3570.8, 2267.1)
SEMENT = (3091.35, 3333.33)          # HIP 46345 · A-06

GROC = (255, 200, 60)
BLANC = (241, 232, 211)
PLATA = (214, 224, 238)
GRIS = (150, 158, 168)


def fnt(sz, bold=True):
    p = ("/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold
         else "/System/Library/Fonts/Supplemental/Arial.ttf")
    try:
        return ImageFont.truetype(p, sz)
    except Exception:
        return ImageFont.load_default()


def mono(sz):
    for p in ("/System/Library/Fonts/Menlo.ttc", "/System/Library/Fonts/Monaco.ttf"):
        try:
            return ImageFont.truetype(p, sz)
        except Exception:
            pass
    return fnt(sz)


F1, F2, F3, F4 = fnt(46), fnt(31), fnt(25), fnt(21)
FM, FMs = mono(26), mono(21)

# ───────────────────────────────────────────────────────────── el fotograma
print("llegint el RAW…")
with rawpy.imread(str(comu.DADES_VIXEN_UNF / "572A2983.CR3")) as r:
    raw = r.raw_image_visible.astype(np.float64) - 511.5
    col = r.raw_colors_visible.copy()
verd = (col == 1) | (col == 3)
k = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], float)
su = ndimage.convolve(np.where(verd, raw, 0.0), k, mode="nearest")
nv = ndimage.convolve(verd.astype(float), k, mode="nearest")
G = np.where(verd, raw, su / np.maximum(nv, 1))
FH, FW = G.shape

ctx = np.arcsinh(np.clip(G, 0, None) / 40.0)
lo, hi = np.percentile(ctx, 1), np.percentile(ctx, 99.99)
GLOBAL = np.clip((ctx - lo) / (hi - lo), 0, 1).astype(np.float32)


def fons(a, box=24, suau=1.4):
    hh, ww = a.shape[0] // box, a.shape[1] // box
    med = np.median(a[:hh*box, :ww*box].reshape(hh, box, ww, box), axis=(1, 3))
    med = ndimage.gaussian_filter(med, suau)
    return ndimage.zoom(med, (a.shape[0]/hh, a.shape[1]/ww), order=3)[:a.shape[0], :a.shape[1]]


print("restant la corona…")
NETG = (G - fons(G, 24)).astype(np.float32)

# ── centroide fi de l'estrella
HW = 40
gx0, gy0 = int(round(SEMENT[0])) - HW, int(round(SEMENT[1])) - HW
_w0 = NETG[gy0:gy0+2*HW+1, gx0:gx0+2*HW+1]
yy, xx = np.mgrid[0:2*HW+1, 0:2*HW+1]
cx, cy = float(HW), float(HW)
for _ in range(8):
    m = ((xx - cx)**2 + (yy - cy)**2) <= 25.0
    w_ = np.clip(_w0, 0, None) * m
    cx = float((xx * w_).sum() / w_.sum())
    cy = float((yy * w_).sum() / w_.sum())
CENT = (gx0 + cx, gy0 + cy)
PIC = float(_w0[np.hypot(yy - cy, xx - cx) <= 6].max())

dx, dy = (CENT[0] - SOL[0]) * ESC, (CENT[1] - SOL[1]) * ESC
rad = math.hypot(dx, dy)
RSOL = rad / R_SOL
UX, UY = dx / rad, dy / rad
GR_AS = ALPHA / RSOL
GR_PX, NW_PX = GR_AS / ESC, GR_AS / 2 / ESC
print(f"HIP 46345 · r = {RSOL:.3f} R☉ · Einstein {GR_AS:.3f}\" = {GR_PX:.3f} px · "
      f"Newton {GR_AS/2:.3f}\" = {NW_PX:.3f} px")

# ── el fotograma «Newton»: només es mou l'estrella, la resta queda clavada
_S = 26
_sy, _sx = int(round(CENT[1])) - _S, int(round(CENT[0])) - _S
_win = NETG[_sy:_sy+2*_S+1, _sx:_sx+2*_S+1]
_desp = ndimage.shift(_win, (-UY * NW_PX, -UX * NW_PX), order=3, mode="nearest")
_y2, _x2 = np.mgrid[0:2*_S+1, 0:2*_S+1]
_d = np.hypot(_x2 - (CENT[0] - _sx), _y2 - (CENT[1] - _sy))
_wm = np.clip((9.0 - _d) / 3.0, 0.0, 1.0)
_wm = (_wm * _wm * (3 - 2 * _wm)).astype(np.float32)
NET_NEWTON = NETG.copy()
NET_NEWTON[_sy:_sy+2*_S+1, _sx:_sx+2*_S+1] = _win * (1 - _wm) + _desp * _wm


def estira(a, g=0.40):
    """Estirada del camp amb la corona restada. g petit = nucli més compacte."""
    return np.clip(np.clip(a, 0, None) / PIC, 0, 1) ** g * 0.96 + 0.02


def tinta(a):
    v = np.clip(a, 0, 1)
    rgb = np.stack([v]*3, -1) + np.clip(v*0.9, 0, 1)[..., None] * np.array([0.28, 0.15, -0.09])
    return Image.fromarray((np.clip(rgb, 0, 1)*255).astype(np.uint8), "RGB")


def vista(cx_, cy_, half, arr=None):
    hh = half * H / W
    barreja = 0.0 if half > 230 else (1.0 if half < 165 else (230 - half) / 65.0)
    i0 = max(int(math.floor(cx_ - half)) - 2, 0)
    j0 = max(int(math.floor(cy_ - hh)) - 2, 0)
    i1 = min(int(math.ceil(cx_ + half)) + 2, FW)
    j1 = min(int(math.ceil(cy_ + hh)) + 2, FH)
    sub = GLOBAL[j0:j1, i0:i1].copy()
    if barreja > 0 or arr is not None:
        src = NETG if arr is None else arr
        n = estira(src[j0:j1, i0:i1])
        sub = n if arr is not None else sub * (1 - barreja) + n * barreja
    im = Image.fromarray((np.clip(sub, 0, 1)*255).astype(np.uint8), "L")
    res = Image.NEAREST if half < 90 else Image.LANCZOS
    im = im.resize((W, H), res, box=(cx_ - half - i0, cy_ - hh - j0,
                                     cx_ + half - i0, cy_ + hh - j0))
    return tinta(np.asarray(im).astype(np.float32)/255.0)


def pant(px, py, cx_, cy_, half):
    hh = half * H / W
    return ((px - (cx_ - half)) / (2*half) * W, (py - (cy_ - hh)) / (2*hh) * H)


def ombra(d, xy, s, f, c, anchor="la"):
    d.text((xy[0]+1.5, xy[1]+1.5), s, font=f, fill=(0, 0, 0, 195), anchor=anchor)
    d.text(xy, s, font=f, fill=c, anchor=anchor)


# ── miniatura de situació
_TW = 320
_TH = int(round(_TW * FH / FW))
_m = np.asarray(Image.fromarray((GLOBAL*255).astype(np.uint8), "L").resize(
    (_TW, _TH), Image.LANCZOS)).astype(np.float32)/255.0
MINI = tinta(_m)


def situacio(img, d, alfa):
    if alfa <= 0.02:
        return
    x0, y0 = W - _TW - 40, 40
    base = img.crop((x0, y0, x0+_TW, y0+_TH))
    img.paste(Image.blend(base, MINI, alfa), (x0, y0))
    A = int(255*alfa)
    d.rectangle([x0, y0, x0+_TW, y0+_TH], outline=(72, 80, 92, A), width=1)
    mx, my = x0 + CENT[0]/FW*_TW, y0 + CENT[1]/FH*_TH
    d.ellipse([mx-10, my-10, mx+10, my+10], outline=GROC + (A,), width=2)
    ombra(d, (x0, y0+_TH+8), "YOU ARE HERE", FMs, tuple(int(v*alfa) for v in GRIS))


def anella(d, x, y, R, c, gruix=3):
    """El cercle groc: sempre el mateix, sempre sobre l'estrella."""
    d.ellipse([x-R-2, y-R-2, x+R+2, y+R+2], outline=(0, 0, 0, 170), width=gruix+3)
    d.ellipse([x-R, y-R, x+R, y+R], outline=c, width=gruix)
    for a in (0, 90, 180, 270):
        vx, vy = math.cos(math.radians(a)), math.sin(math.radians(a))
        d.line([x+vx*(R+7), y+vy*(R+7), x+vx*(R+17), y+vy*(R+17)], fill=c, width=gruix)


def escala(d, half, y=H-56):
    amp = 2*half*ESC
    for val, lab in ((3600., "1°"), (1800., "30′"), (600., "10′"),
                     (300., "5′"), (120., "2′"), (60., "1′"), (30., "30″")):
        if 0.13 < val/amp < 0.46:
            px = val/amp*W
            d.line([80, y, 80+px, y], fill=BLANC, width=3)
            d.line([80, y-8, 80, y+8], fill=BLANC, width=3)
            d.line([80+px, y-8, 80+px, y+8], fill=BLANC, width=3)
            ombra(d, (80+px/2, y-32), lab, fnt(26), BLANC, anchor="ma")
            return


# ─────────────────────────────────────────────────────────────────── guió
GUIO = [("plena", 3.0), ("marca", 2.2), ("zoom", 5.4), ("blink", 10.0), ("tanca", 3.2)]
HALF0, HALF1 = FW/2, 70.0
CICLES = 12
R_ANELLA = 30
C0 = (FW/2, FH/2)
print(f"durada {sum(x for _, x in GUIO):.1f} s · camp final "
      f"{2*HALF1:.0f} px = {2*HALF1*ESC/60:.1f}′")

n = 0
for escena, dur in GUIO:
    nf = int(dur*FPS)
    for f in range(nf):
        u = f/nf
        e = u*u*(3-2*u)

        if escena in ("plena", "marca"):
            half, cx_, cy_ = HALF0, C0[0], C0[1]
        elif escena == "zoom":
            half = HALF0*(HALF1/HALF0)**e
            p = min(1.0, u/0.55)
            p = p*p*(3-2*p)
            cx_ = C0[0] + (CENT[0]-C0[0])*p
            cy_ = C0[1] + (CENT[1]-C0[1])*p
        else:
            half, cx_, cy_ = HALF1, CENT[0], CENT[1]

        newton = (escena == "blink" and int(u*CICLES*2) % 2 == 1)
        img = vista(cx_, cy_, half, arr=NET_NEWTON if newton else None)
        d = ImageDraw.Draw(img, "RGBA")

        situacio(img, d, 0.0 if escena in ("plena", "marca")
                 else (min(1.0, max(0.0, (u-0.45)/0.28)) if escena == "zoom" else 1.0))

        # ── EL CERCLE GROC: surt a la marca i ja no se'n va
        if escena != "plena":
            X, Y = pant(CENT[0], CENT[1], cx_, cy_, half)
            a = min(1.0, u/0.4) if escena == "marca" else 1.0
            anella(d, X, Y, R_ANELLA, GROC + (int(255*a),))
            if escena == "marca" and u > 0.32:
                ombra(d, (X+R_ANELLA+34, Y-32), "HIP 46345", F2, GROC)
                ombra(d, (X+R_ANELLA+34, Y+4),
                      "V = 6.83   ·   2.65 solar radii from the Sun's centre", F3, BLANC)

        # ── el moviment
        if escena == "blink":
            if newton:
                ombra(d, (W/2, 66), "IF NEWTON HAD BEEN RIGHT", F1, PLATA, anchor="ma")
                ombra(d, (W/2, 124), "half the deflection  ·  only this star is moved",
                      F3, GRIS, anchor="ma")
            else:
                ombra(d, (W/2, 66), "WHAT THE SENSOR RECORDED", F1, GROC, anchor="ma")
                ombra(d, (W/2, 124), "10.3 s  ·  Canon EOS R6 Mark III  ·  12 Aug 2026",
                      F3, GRIS, anchor="ma")
            ombra(d, (W/2, H-58), "the ring never moves — the star does",
                  F3, GRIS, anchor="ma")
            x0 = W - 486
            d.rounded_rectangle([x0, 566, x0+446, 682], 10, fill=(8, 10, 14, 216),
                                outline=(46, 54, 66, 255), width=1)
            ombra(d, (x0+26, 584), "Einstein 0.66″   ·   Newton 0.33″", F3, BLANC)
            ombra(d, (x0+26, 622), "the gap: 0.15 of one sensor pixel", FMs, GRIS)
            ombra(d, (x0+26, 650), "1 pixel = 2.15″ = one small square", FMs, GRIS)

        if escena == "plena":
            a = min(1.0, u/0.3)*(1-max(0.0, (u-0.8)/0.2))
            if a > 0.02:
                A = int(255*a)
                ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                dv = ImageDraw.Draw(ov)
                dv.text((80, H-214), "TOTAL SOLAR ECLIPSE", font=fnt(23), fill=(178, 186, 197, A))
                dv.text((80, H-178), "12 August 2026  ·  León, Spain", font=F1,
                        fill=(241, 232, 211, A))
                dv.text((80, H-116),
                        "103.7 seconds of totality  ·  56 background stars recorded",
                        font=F3, fill=(178, 186, 197, A))
                img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
                d = ImageDraw.Draw(img, "RGBA")

        if escena == "tanca":
            a = min(1.0, u/0.3)
            A = int(255*a)
            ov = Image.new("RGBA", (W, H), (5, 6, 9, int(216*a)))
            dv = ImageDraw.Draw(ov)
            dv.text((W/2, 268), "The two theories differ by 0.33 arcseconds.", font=F1,
                    fill=(241, 232, 211, A), anchor="ma")
            dv.text((W/2, 336), "On this sensor, 0.15 of a pixel.", font=F1,
                    fill=(255, 200, 60, A), anchor="ma")
            dv.text((W/2, 434), "That gap is the whole of the 1919 experiment,", font=F2,
                    fill=(178, 186, 197, A), anchor="ma")
            dv.text((W/2, 476), "and the reason it took an eclipse to see it.", font=F2,
                    fill=(178, 186, 197, A), anchor="ma")
            dv.text((W/2, 566),
                    "Einstein's value is now confirmed to five decimal places by radio",
                    font=F3, fill=(150, 158, 168, A), anchor="ma")
            dv.text((W/2, 600),
                    "interferometry. This is not a test of relativity — it is a portrait of it.",
                    font=F3, fill=(150, 158, 168, A), anchor="ma")
            dv.text((W/2, 722), "Pere Guerra  ·  Vixen VSD90SS + Canon EOS R6 Mark III",
                    font=F4, fill=(118, 126, 137, A), anchor="ma")
            img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
            d = ImageDraw.Draw(img, "RGBA")

        if escena in ("plena", "marca", "zoom"):
            escala(d, half)

        img.save(f"{FRAMES}/f{n:05d}.png")
        n += 1

print(f"{n} fotogrames escrits")
