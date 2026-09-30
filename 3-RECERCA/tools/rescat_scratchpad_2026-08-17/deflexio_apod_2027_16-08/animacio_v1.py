#!/usr/bin/env python3
"""«Where Newton would have put it» — animació per a l'APOD.

Del fotograma real 572A2983 (Vixen VSD90SS + Canon R6 Mark III, 10,3 s) fins a
HIP 46345, la llum de la qual va passar a 2,65 radis solars del centre del Sol.
Al final, la mateixa estrella tal com la va registrar el sensor i tal com
l'hauria registrat si la deflexió fos la de Newton.
"""
import math
import os
import numpy as np
import rawpy
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont

FRAMES = ("/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/"
          "604fa71e-4fd9-4d66-a0e5-157c6621ceb3/scratchpad/frames")
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
with rawpy.imread("/Users/USUARI/Desktop/Eclipse 2026/Vixen Unfiltered/572A2983.CR3") as r:
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
    """Model de corona per mediana en blocs: un gradient enorme i suau."""
    hh, ww = a.shape[0] // box, a.shape[1] // box
    med = np.median(a[:hh*box, :ww*box].reshape(hh, box, ww, box), axis=(1, 3))
    med = ndimage.gaussian_filter(med, suau)
    return ndimage.zoom(med, (a.shape[0]/hh, a.shape[1]/ww), order=3)[:a.shape[0], :a.shape[1]]


print("restant la corona de tot el fotograma…")
NETG = (G - fons(G, 24)).astype(np.float32)

# ── finestra local amb la corona restada (pla ajustat a l'anell exterior)
HW = 60
gx0, gy0 = int(round(SEMENT[0])) - HW, int(round(SEMENT[1])) - HW
loc = G[gy0:gy0 + 2*HW + 1, gx0:gx0 + 2*HW + 1].copy()
yy, xx = np.mgrid[0:2*HW+1, 0:2*HW+1]
rr = np.hypot(yy - HW, xx - HW)
anell = rr > HW - 10
A = np.stack([np.ones(anell.sum()), xx[anell], yy[anell],
              xx[anell]**2, yy[anell]**2, xx[anell]*yy[anell]], 1)
coef, *_ = np.linalg.lstsq(A, loc[anell], rcond=None)
pla = (coef[0] + coef[1]*xx + coef[2]*yy + coef[3]*xx**2 + coef[4]*yy**2 + coef[5]*xx*yy)
NET = loc - pla

# ── centroide iteratiu (el de la primera passada anava desplaçat ~1 px)
cx, cy = float(HW), float(HW)
for _ in range(8):
    d2 = (xx - cx)**2 + (yy - cy)**2
    m = d2 <= 5.0**2
    w_ = np.clip(NET, 0, None) * m
    cx = float((xx * w_).sum() / w_.sum())
    cy = float((yy * w_).sum() / w_.sum())
CENT = (gx0 + cx, gy0 + cy)
PIC = float(NETG[gy0:gy0+2*HW+1, gx0:gx0+2*HW+1][rr <= 6].max())
print(f"centroide {CENT[0]:.2f},{CENT[1]:.2f}  pic {PIC:.0f} ADU")

dx, dy = (CENT[0] - SOL[0]) * ESC, (CENT[1] - SOL[1]) * ESC
rad = math.hypot(dx, dy)
RSOL = rad / R_SOL
UX, UY = dx / rad, dy / rad
GR_AS = ALPHA / RSOL
GR_PX, NW_PX = GR_AS / ESC, GR_AS / 2 / ESC
print(f"r = {RSOL:.3f} R☉ · Einstein {GR_AS:.3f}″ = {GR_PX:.3f} px · "
      f"Newton {GR_AS/2:.3f}″ = {NW_PX:.3f} px")

P_E = CENT
P_N = (CENT[0] - UX * NW_PX, CENT[1] - UY * NW_PX)
P_0 = (CENT[0] - UX * GR_PX, CENT[1] - UY * GR_PX)
NET = NETG
# nomes es mou l'estrella: la resta del cel, soroll inclos, queda clavada
_S = 30
_sy, _sx = int(round(CENT[1])) - _S, int(round(CENT[0])) - _S
_win = NETG[_sy:_sy+2*_S+1, _sx:_sx+2*_S+1]
_desp = ndimage.shift(_win, (-UY * NW_PX, -UX * NW_PX), order=3, mode="nearest")
_yy, _xx = np.mgrid[0:2*_S+1, 0:2*_S+1]
_d = np.hypot(_xx - (CENT[0] - _sx), _yy - (CENT[1] - _sy))
_w = np.clip((9.0 - _d) / 3.0, 0.0, 1.0)
_w = (_w * _w * (3 - 2 * _w)).astype(np.float32)
NET_NEWTON = NETG.copy()
NET_NEWTON[_sy:_sy+2*_S+1, _sx:_sx+2*_S+1] = _win * (1 - _w) + _desp * _w


def estira_local(a):
    return np.clip(np.clip(a, 0, None) / PIC, 0, 1) ** 0.55 * 0.96 + 0.02


def tinta(a, calid=True):
    v = np.clip(a, 0, 1)
    c = np.array([0.28, 0.15, -0.09]) if calid else np.array([-0.06, 0.06, 0.26])
    rgb = np.stack([v]*3, -1) + np.clip(v*0.9, 0, 1)[..., None] * c
    return Image.fromarray((np.clip(rgb, 0, 1)*255).astype(np.uint8), "RGB")


def vista(cx_, cy_, half, arr=None, calid=True):
    """W×H del fotograma, centrada a (cx_,cy_), semiample `half` píxels."""
    hh = half * H / W
    barreja = 0.0 if half > 230 else (1.0 if half < 165 else (230 - half) / 65.0)
    i0 = max(int(math.floor(cx_ - half)) - 2, 0)
    j0 = max(int(math.floor(cy_ - hh)) - 2, 0)
    i1 = min(int(math.ceil(cx_ + half)) + 2, FW)
    j1 = min(int(math.ceil(cy_ + hh)) + 2, FH)
    sub = GLOBAL[j0:j1, i0:i1].copy()
    if barreja > 0 or arr is not None:
        src = NET if arr is None else arr
        n = estira_local(src[j0:j1, i0:i1])
        sub = n if arr is not None else sub * (1 - barreja) + n * barreja
    im = Image.fromarray((np.clip(sub, 0, 1)*255).astype(np.uint8), "L")
    res = Image.NEAREST if half < 50 else Image.LANCZOS
    im = im.resize((W, H), res, box=(cx_ - half - i0, cy_ - hh - j0,
                                     cx_ + half - i0, cy_ + hh - j0))
    return tinta(np.asarray(im).astype(np.float32)/255.0, calid)


# miniatura de tot el fotograma, per no perdre mai el context
_TW = 340
_TH = int(round(_TW * FH / FW))
_mini = Image.fromarray((np.clip(GLOBAL, 0, 1)*255).astype(np.uint8), "L").resize(
    (_TW, _TH), Image.LANCZOS)
_a = np.asarray(_mini).astype(np.float32)/255.0
MINI = Image.fromarray((np.clip(np.stack([_a]*3, -1) +
                                np.clip(_a*0.9, 0, 1)[..., None]*np.array([0.28, 0.15, -0.09]),
                                0, 1)*255).astype(np.uint8), "RGB")


def situacio(img, d, alfa=1.0):
    """Mapa de situació a dalt a la dreta: on som dins l'eclipsi."""
    if alfa <= 0.02:
        return
    x0, y0 = W - _TW - 40, 40
    if alfa < 1.0:
        base = img.crop((x0, y0, x0+_TW, y0+_TH))
        img.paste(Image.blend(base, MINI, alfa), (x0, y0))
    else:
        img.paste(MINI, (x0, y0))
    d.rectangle([x0, y0, x0+_TW, y0+_TH], outline=(70, 78, 90, int(255*alfa)), width=1)
    mx = x0 + CENT[0]/FW*_TW
    my = y0 + CENT[1]/FH*_TH
    d.ellipse([mx-11, my-11, mx+11, my+11], outline=GROC + (int(255*alfa),), width=2)
    d.line([mx, my-19, mx, my-13], fill=GROC + (int(255*alfa),), width=2)
    ombra(d, (x0, y0+_TH+8), "YOU ARE HERE", FMs, tuple(int(v*alfa) for v in GRIS))


def pant(px, py, cx_, cy_, half):
    hh = half * H / W
    return ((px - (cx_ - half)) / (2*half) * W, (py - (cy_ - hh)) / (2*hh) * H)


def graella(d, cx_, cy_, half, alfa):
    if alfa <= 0:
        return
    hh = half * H / W
    i = math.floor(cx_ - half)
    while i <= cx_ + half + 1:
        X, _ = pant(i + 0.5, 0, cx_, cy_, half)
        d.line([X, 0, X, H], fill=(122, 134, 150, alfa), width=1)
        i += 1
    j = math.floor(cy_ - hh)
    while j <= cy_ + hh + 1:
        _, Y = pant(0, j + 0.5, cx_, cy_, half)
        d.line([0, Y, W, Y], fill=(122, 134, 150, alfa), width=1)
        j += 1


def creu(d, x, y, c, r=30, g=3, buit=11, dash=False):
    seg = ((buit, r), (-r, -buit))
    for a, b in seg:
        d.line([x+a, y, x+b, y], fill=c, width=g)
        d.line([x, y+a, x, y+b], fill=c, width=g)
    if not dash:
        d.ellipse([x-3, y-3, x+3, y+3], fill=c)


def ombra(d, xy, s, f, c, anchor="la"):
    d.text((xy[0]+1.5, xy[1]+1.5), s, font=f, fill=(0, 0, 0, 190), anchor=anchor)
    d.text(xy, s, font=f, fill=c, anchor=anchor)


def lupa(img, d, cx_, cy_, half, quins, factor=5.0, centre=(322, 306), R=196,
         arr=None, fosc=0.26, anella=None, etiqueta="\u00d75  magnified"):
    """Cercle magnificat x`factor`, ancorat al mateix punt del camp."""
    sub_half = half / factor
    v = vista(P_N[0], P_N[1], sub_half, arr=arr)
    if fosc < 1.0:
        v = Image.fromarray((np.asarray(v).astype(np.float32) * fosc + 6).astype(np.uint8))
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).ellipse([centre[0]-R, centre[1]-R, centre[0]+R, centre[1]+R], fill=255)
    off = v.crop((W//2 - centre[0], H//2 - centre[1],
                  W//2 - centre[0] + W, H//2 - centre[1] + H))
    img.paste(off, (0, 0), mask)
    d2 = ImageDraw.Draw(img, "RGBA")
    # graella de pixels dins la lupa
    hh = sub_half * H / W
    i = math.floor(P_N[0] - sub_half)
    while i <= P_N[0] + sub_half + 1:
        X, _ = pant(i + 0.5, 0, P_N[0], P_N[1], sub_half)
        X += centre[0] - W//2
        d2.line([X, centre[1]-R, X, centre[1]+R], fill=(150, 165, 185, 210), width=1)
        i += 1
    j = math.floor(P_N[1] - hh)
    while j <= P_N[1] + hh + 1:
        _, Y = pant(0, j + 0.5, P_N[0], P_N[1], sub_half)
        Y += centre[1] - H//2
        d2.line([centre[0]-R, Y, centre[0]+R, Y], fill=(150, 165, 185, 210), width=1)
        j += 1
    for p, c, dash in quins:
        X, Y = pant(p[0], p[1], P_N[0], P_N[1], sub_half)
        X += centre[0] - W//2; Y += centre[1] - H//2
        if (X-centre[0])**2 + (Y-centre[1])**2 < (R-16)**2:
            creu(d2, X, Y, c, 34, 4, 11, dash)
    if anella is not None:
        X, Y = pant(anella[0], anella[1], P_N[0], P_N[1], sub_half)
        X += centre[0] - W//2; Y += centre[1] - H//2
        RR = 40
        d2.ellipse([X-RR-2, Y-RR-2, X+RR+2, Y+RR+2], outline=(0, 0, 0, 170), width=6)
        d2.ellipse([X-RR, Y-RR, X+RR, Y+RR], outline=GROC + (245,), width=3)
    d2.ellipse([centre[0]-R, centre[1]-R, centre[0]+R, centre[1]+R],
               outline=(150, 162, 178, 235), width=3)
    ombra(d2, (centre[0], centre[1]+R+16), etiqueta, FMs, GRIS, anchor="ma")
    return d2


def escala(d, half, y=H-58):
    amp = 2*half*ESC
    for val, lab in ((3600., "1°"), (1800., "30′"), (600., "10′"), (120., "2′"),
                     (60., "1′"), (20., "20″"), (10., "10″"), (5., "5″"), (2., "2″")):
        if 0.13 < val/amp < 0.45:
            px = val/amp*W
            d.line([80, y, 80+px, y], fill=BLANC, width=3)
            d.line([80, y-8, 80, y+8], fill=BLANC, width=3)
            d.line([80+px, y-8, 80+px, y+8], fill=BLANC, width=3)
            ombra(d, (80+px/2, y-32), lab, fnt(26), BLANC, anchor="ma")
            return


def llegenda(d, files, y0=560):
    """Panell dret amb les tres posicions."""
    x0, w0 = W-486, 452
    h0 = 44 + 62*len(files)
    d.rounded_rectangle([x0, y0, x0+w0, y0+h0], 10, fill=(8, 10, 14, 218),
                        outline=(46, 54, 66, 255), width=1)
    ombra(d, (x0+26, y0+20), "WHERE THE STAR SITS", FMs, GRIS)
    for i, (c, tit, sub, dash) in enumerate(files):
        yy_ = y0 + 56 + 62*i
        creu(d, x0+44, yy_+12, c, 15, 2, 5, dash)
        ombra(d, (x0+76, yy_), tit, F3, c)
        ombra(d, (x0+76, yy_+26), sub, FMs, GRIS)


# ───────────────────────────────────────────────────────────────── guió
GUIO = [("obertura", 3.2), ("marca", 2.6), ("zoom", 5.6), ("graella", 2.2),
        ("cap_sol", 2.8), ("newton", 3.2), ("einstein", 3.6), ("enrere", 2.2),
        ("blink", 11.0), ("tanca", 4.0)]
HALF0, HALF1, HALF2 = FW/2, 14.0, 40.0
CICLES = 10          # anades i tornades del blink
C0 = (FW/2, FH/2)
print(f"durada {sum(d for _, d in GUIO):.1f} s")

LL_0 = (GRIS, "No Sun", "where the catalogue puts it", True)
LL_N = (PLATA, "Newton  +0.33″", "0.15 of a pixel outward", True)
LL_E = (GROC, "Einstein  +0.66″", "0.31 px — what we photographed", False)

n = 0
for escena, dur in GUIO:
    nf = int(dur*FPS)
    for f in range(nf):
        u = f/nf
        e = u*u*(3-2*u)
        if escena in ("obertura", "marca"):
            half, cx_, cy_ = HALF0, C0[0], C0[1]
        elif escena == "zoom":
            half = HALF0*(HALF1/HALF0)**e
            p = min(1.0, u/0.55)
            p = p*p*(3-2*p)          # el centre arriba a l'estrella al 55 % de l'escena
            cx_ = C0[0] + (CENT[0]-C0[0])*p
            cy_ = C0[1] + (CENT[1]-C0[1])*p
        elif escena == "enrere":
            half = HALF1 + (HALF2 - HALF1)*e
            cx_, cy_ = CENT[0], CENT[1]
        elif escena in ("blink", "tanca"):
            half, cx_, cy_ = HALF2, CENT[0], CENT[1]
        else:
            half, cx_, cy_ = HALF1, CENT[0], CENT[1]

        blink_newton = (escena == "blink" and int(u*CICLES*2) % 2 == 1)
        img = vista(cx_, cy_, half,
                    arr=NET_NEWTON if blink_newton else None)
        d = ImageDraw.Draw(img, "RGBA")

        al = 0 if half > 28 else int(62 + 103*min(1.0, max(0.0, (26-half)/14)))
        graella(d, cx_, cy_, half, al)

        # mapa de situació: apareix quan la corona ja no cap al quadre
        if escena == "zoom":
            a_sit = min(1.0, max(0.0, (u - 0.42) / 0.30))
        elif escena in ("obertura", "marca"):
            a_sit = 0.0
        else:
            a_sit = 1.0
        situacio(img, d, a_sit)

        if escena == "marca":
            X, Y = pant(CENT[0], CENT[1], cx_, cy_, half)
            a = min(1.0, u/0.35)
            d.ellipse([X-48, Y-48, X+48, Y+48], outline=GROC+(int(255*a),), width=3)
            if u > 0.3:
                ombra(d, (X+64, Y-32), "HIP 46345", F2, GROC)
                ombra(d, (X+64, Y+4), "V = 6.83   ·   2.65 solar radii from the Sun's centre",
                      F3, BLANC)

        if escena in ("cap_sol", "newton", "einstein", "enrere", "blink", "tanca"):
            X0, Y0 = pant(P_0[0], P_0[1], cx_, cy_, half)
            Xn, Yn = pant(P_N[0], P_N[1], cx_, cy_, half)
            Xe, Ye = pant(P_E[0], P_E[1], cx_, cy_, half)
            # eix radial i fletxa cap al Sol, mantinguda dins del quadre
            L = 122
            L0 = 74 if escena in ("enrere", "blink", "tanca") else 0
            bx, by = X0 - UX*L0, Y0 - UY*L0
            ax, ay = X0 - UX*(L + L0), Y0 - UY*(L + L0)
            d.line([bx, by, ax, ay], fill=(150, 160, 175, 170), width=2)
            for s in (-1, 1):
                d.line([ax, ay, ax+UX*20 - s*UY*11, ay+UY*20 + s*UX*11],
                       fill=(150, 160, 175, 200), width=2)
            ombra(d, (ax - UX*26, ay - UY*26), "to the Sun", FMs, GRIS,
                  anchor="mm" if abs(UX) < 0.7 else ("ra" if UX > 0 else "la"))

            petit = escena in ("enrere", "blink", "tanca")
            files = [LL_0]
            if not petit:
                creu(d, X0, Y0, GRIS, 26, 2, 9, True)
            if escena in ("newton", "einstein", "enrere", "blink", "tanca"):
                a = min(1.0, u/0.45) if escena == "newton" else 1.0
                a = a*a*(3-2*a)
                xn, yn = X0+(Xn-X0)*a, Y0+(Yn-Y0)*a
                if not petit:
                    d.line([X0, Y0, xn, yn], fill=PLATA, width=4)
                if escena != "blink":
                    creu(d, xn, yn, PLATA, 15 if petit else 28, 2 if petit else 3,
                         6 if petit else 10, True)
                if a > 0.9:
                    files.append(LL_N)
            if escena in ("einstein", "enrere", "blink", "tanca"):
                a = min(1.0, u/0.5) if escena == "einstein" else 1.0
                a = a*a*(3-2*a)
                xe, ye = Xn+(Xe-Xn)*a, Yn+(Ye-Yn)*a
                if not petit:
                    d.line([Xn, Yn, xe, ye], fill=GROC, width=5)
                if escena == "blink":
                    R_ = 44
                    d.ellipse([xe-R_, ye-R_, xe+R_, ye+R_], outline=GROC + (235,), width=3)
                    for ang in (0, 90, 180, 270):
                        vx, vy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
                        d.line([xe+vx*(R_-11), ye+vy*(R_-11), xe+vx*(R_+11), ye+vy*(R_+11)],
                               fill=GROC + (235,), width=3)
                else:
                    creu(d, xe, ye, GROC, 17 if petit else 32, 2 if petit else 4,
                         6 if petit else 11)
                if a > 0.9:
                    files.append(LL_E)
            if escena in ("cap_sol", "newton", "einstein"):
                llegenda(d, files, y0=548)
                quins = [(P_0, GRIS, True)]
                if len(files) > 1:
                    quins.append((P_N, PLATA, True))
                if len(files) > 2:
                    quins.append((P_E, GROC, False))
                d = lupa(img, d, cx_, cy_, half, quins)
            elif escena == "enrere":
                llegenda(d, [LL_N, LL_E], y0=636)
            elif escena == "blink":
                d = lupa(img, d, cx_, cy_, half, [], factor=4.0, centre=(300, 452), R=196,
                         arr=NET_NEWTON if blink_newton else None, fosc=1.0,
                         anella=P_E, etiqueta="\u00d74  the same star, magnified")

        if escena in ("enrere", "blink"):
            if blink_newton:
                ombra(d, (W/2, 62), "IF NEWTON HAD BEEN RIGHT", F1, PLATA, anchor="ma")
                ombra(d, (W/2, 120), "only the target star is moved \u2014 everything else is untouched",
                      F3, GRIS, anchor="ma")
            else:
                ombra(d, (W/2, 62), "WHAT THE SENSOR RECORDED", F1, GROC, anchor="ma")
                ombra(d, (W/2, 120), "10.3 s  \u00b7  Canon EOS R6 Mark III  \u00b7  12 Aug 2026",
                      F3, GRIS, anchor="ma")
            if escena == "blink":
                ombra(d, (W/2, H-52), "the ring is fixed where the sensor recorded it \u2014 watch the star step out of it",
                      F3, GRIS, anchor="ma")

        if escena in ("graella", "cap_sol", "newton", "einstein"):
            ty = 64 if escena == "graella" else H - 214
            ombra(d, (80, ty), "ONE STAR, AT 2.65 SOLAR RADII", fnt(23), GRIS)
            ombra(d, (80, ty + 34), "HIP 46345", F1, BLANC)
            if escena == "graella":
                a = min(1.0, u/0.45)
                ombra(d, (80, ty + 94), "one square = one sensor pixel = 2.15 arcseconds",
                      F3, tuple(int(v*a) for v in GRIS))
            else:
                ombra(d, (80, ty + 94),
                      "Its light grazed the Sun. Both theories bend it \u2014 by different amounts.",
                      F3, GRIS)

        if escena == "obertura":
            a = min(1.0, u/0.3)*(1-max(0.0, (u-0.82)/0.18))
            if a > 0.02:
                ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                dv = ImageDraw.Draw(ov)
                A_ = int(255*a)
                dv.text((80, H-214), "TOTAL SOLAR ECLIPSE", font=fnt(23), fill=(178, 186, 197, A_))
                dv.text((80, H-178), "12 August 2026  ·  León, Spain", font=F1,
                        fill=(241, 232, 211, A_))
                dv.text((80, H-116),
                        "103.7 seconds of totality  ·  56 background stars recorded",
                        font=F3, fill=(178, 186, 197, A_))
                img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
                d = ImageDraw.Draw(img, "RGBA")

        if escena == "tanca":
            a = min(1.0, u/0.28)
            ov = Image.new("RGBA", (W, H), (5, 6, 9, int(214*a)))
            dv = ImageDraw.Draw(ov)
            A_ = int(255*a)
            dv.text((W/2, 250), "The difference is 0.33 arcseconds.", font=F1,
                    fill=(241, 232, 211, A_), anchor="ma")
            dv.text((W/2, 318), "On this sensor, 0.15 of a pixel.", font=F1,
                    fill=(255, 200, 60, A_), anchor="ma")
            dv.text((W/2, 416), "That gap is the whole of the 1919 experiment,", font=F2,
                    fill=(178, 186, 197, A_), anchor="ma")
            dv.text((W/2, 458), "and the reason it took an eclipse to see it.", font=F2,
                    fill=(178, 186, 197, A_), anchor="ma")
            dv.text((W/2, 556),
                    "Einstein's value has since been confirmed to five decimal places by radio",
                    font=F3, fill=(150, 158, 168, A_), anchor="ma")
            dv.text((W/2, 590),
                    "interferometry. This is not a test of relativity — it is a portrait of it.",
                    font=F3, fill=(150, 158, 168, A_), anchor="ma")
            dv.text((W/2, 726), "Pere Guerra  ·  Vixen VSD90SS + Canon EOS R6 Mark III",
                    font=F4, fill=(118, 126, 137, A_), anchor="ma")
            img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")

        if escena in ("obertura", "marca", "zoom", "graella"):
            escala(ImageDraw.Draw(img, "RGBA"), half)

        img.save(f"{FRAMES}/f{n:05d}.png")
        n += 1

print(f"{n} fotogrames escrits")
