#!/usr/bin/env python3
"""Màscara d'estrelles sobre una exposició llarga de l'eclipsi del 12-08-2026.

Funciona amb els dos trens. NOMÉS LECTURA sobre els RAW originals.

    python mascara_estrelles.py sony [DSC06993.ARW]
    python mascara_estrelles.py vixen [572A2982.CR3]

Genera, al costat d'aquest fitxer:
    estrelles_<tren>_marcades.png   la imatge amb les deteccions marcades
    estrelles_<tren>_zooms.png      retalls ampliats de les més brillants
"""
import csv, sys, re, os, glob, subprocess
import numpy as np
import rawpy
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))

TRENS = {
    "sony": dict(
        dir="/Users/USUARI/Desktop/Eclipse 2026/300mm",
        patro="*.ARW", defecte="DSC06993.ARW", csv="estrelles_sony.csv",
        pedestal=512.0, escala=3.2020, mitja_res=True, exp="8",
        titol="Sony A7RIIIA + FE 300 mm f/2,8 GM", peu="8 s · f/2,8 · ISO 100",
    ),
    "vixen": dict(
        dir="/Users/USUARI/Desktop/Eclipse 2026/Vixen Unfiltered",
        patro="*.CR3", defecte="572A2983.CR3", csv="estrelles_r6.csv",
        pedestal=511.5, escala=2.1495, mitja_res=False, exp="10", defecte_real="572A2983.CR3",
        titol="Vixen VSD90SS + Canon R6 Mark III", peu="10,3 s · f/5,5 · ISO 100",
    ),
}

tren = (sys.argv[1] if len(sys.argv) > 1 else "sony").lower()
T = TRENS[tren]

# ---------------------------------------------------------------- fotograma
if len(sys.argv) > 2:
    FRAME = sys.argv[2]
elif T["defecte"]:
    FRAME = T["defecte"]
else:                                    # tria el primer de l'exposició llarga per EXIF
    fitxers = sorted(glob.glob(os.path.join(T["dir"], T["patro"])))
    out = subprocess.run(["exiftool", "-q", "-p", "$FileName $ExposureTime"] + fitxers,
                         capture_output=True, text=True).stdout
    cands = [l.split()[0] for l in out.splitlines() if l.split()[-1] == T["exp"]]
    FRAME = cands[len(cands)//2] if cands else os.path.basename(fitxers[0])
print(f"tren {tren} · fotograma {FRAME}")

ref = [(d["id"], float(d["x"]), float(d["y"]), d["nom"])
       for d in csv.DictReader(open(os.path.join(AQUI, T["csv"])))]

def etiqueta(idd, nom):
    if not nom:
        return idd, None
    dreta = nom.split("=", 1)[1] if "=" in nom else nom
    cos = dreta.split(",")[0].strip()
    if "/" in cos:
        cos = cos.split("/")[-1].strip()
    mv = re.search(r"V\s*=\s*([0-9]+,[0-9]+)", nom)
    return cos, (mv.group(1) if mv else None)

# ---------------------------------------------------------------- lectura crua
with rawpy.imread(os.path.join(T["dir"], FRAME)) as r:
    raw = r.raw_image_visible.astype(np.float64) - T["pedestal"]
    col = r.raw_colors_visible.copy()

if T["mitja_res"]:
    ys, xs = np.where(col[:2, :2] == 1)
    oy, ox = int(ys[0]), int(xs[0])
    G = raw[oy::2, ox::2]                 # un sol subpla verd, a mitja resolució
    fac, off = 2.0, (ox, oy)
else:
    verd = (col == 1) | (col == 3)        # els dos subplans verds, en quincunx
    Gm = np.where(verd, raw, 0.0)
    # omplir els no-verds amb la mitjana dels quatre veïns ortogonals, que són verds
    k = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], float)
    su = ndimage.convolve(Gm, k, mode="nearest")
    nv = ndimage.convolve(verd.astype(float), k, mode="nearest")
    G = np.where(verd, raw, su / np.maximum(nv, 1))
    fac, off = 1.0, (0, 0)
H, W = G.shape
print(f"pla verd {W}x{H}" + ("  (mitja resolució)" if T["mitja_res"] else "  (resolució completa)"))

# ---------------------------------------------------------------- fons i S/N
def fons(a, box=16, suau=1.4):
    hh, ww = a.shape[0] // box, a.shape[1] // box
    med = np.median(a[:hh*box, :ww*box].reshape(hh, box, ww, box), axis=(1, 3))
    med = ndimage.gaussian_filter(med, suau)
    return ndimage.zoom(med, (a.shape[0]/hh, a.shape[1]/ww), order=3)[:a.shape[0], :a.shape[1]]

BOX = 16 if T["mitja_res"] else 24
bg = fons(G, BOX)
res = G - bg
sd = np.maximum(fons(np.abs(res), BOX) * 1.4826, 1e-6)
snr = res / sd

def px(x, y, dx=0.0, dy=0.0):
    return (x + dx - off[0]) / fac, (y + dy - off[1]) / fac

def encerts(dx, dy):
    n = 0
    for _, x, y, _ in ref:
        X, Y = px(x, y, dx, dy)
        if 12 < X < W-12 and 12 < Y < H-12:
            if np.nanmax(snr[int(Y)-3:int(Y)+4, int(X)-3:int(X)+4]) > 4:
                n += 1
    return n

cands = [(0, 0), (-227.6, 706.5), (227.6, -706.5)] if tren == "sony" else [(0, 0)]
millor = max(cands, key=lambda c: encerts(*c))
for _ in range(2):
    millor = max([(millor[0]+i, millor[1]+j) for i in (-6,-3,0,3,6) for j in (-6,-3,0,3,6)],
                 key=lambda c: encerts(*c))
DX, DY = millor
print(f"offset ({DX:+.1f},{DY:+.1f}) → {encerts(DX,DY)}/{len(ref)} amb S/N>4 en aquest fotograma sol")

# ---------------------------------------------------------------- composició
ctx = np.arcsinh(np.clip(G, 0, None) / 40.0)
lo, hi = np.percentile(ctx, 1), np.percentile(ctx, 99.9)
ctx = np.clip((ctx - lo) / (hi - lo), 0, 1)
punts = np.clip(snr / 9.0, 0, 1) ** 0.75
llindar = np.percentile(bg, 99.0)
pes = ndimage.gaussian_filter(1.0 / (1.0 + (np.clip(bg, 0, None)/max(llindar, 1e-6))**2), 12)
lum = np.clip(ctx * 0.46 + punts * pes * 0.95, 0, 1)
rgb = np.clip(np.stack([lum]*3, -1) + np.clip(ctx*0.42, 0, 1)[..., None]*np.array([0.30, 0.16, -0.10]), 0, 1)
img = Image.fromarray((rgb * 255).astype(np.uint8))

d = ImageDraw.Draw(img)
def fnt(sz):
    for p in ["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/System/Library/Fonts/Helvetica.ttc"]:
        try: return ImageFont.truetype(p, sz)
        except Exception: pass
    return ImageFont.load_default()
esc_t = 1.0 if T["mitja_res"] else 1.5           # el Vixen es dibuixa a resolució completa
F, Fs, Ft = fnt(int(30*esc_t)), fnt(int(24*esc_t)), fnt(int(20*esc_t))

GROC, VERD = (255, 200, 60), (105, 240, 165)
marcades = []
for idd, x, y, nom in ref:
    X, Y = px(x, y, DX, DY)
    if not (0 < X < W and 0 < Y < H):
        continue
    ok = (12 < X < W-12 and 12 < Y < H-12 and
          np.nanmax(snr[int(Y)-3:int(Y)+4, int(X)-3:int(X)+4]) > 4)
    c, R = (GROC, int(30*esc_t)) if nom else (VERD, int(26*esc_t))
    if ok:
        d.ellipse([X-R, Y-R, X+R, Y+R], outline=c, width=int(3*esc_t))
    else:
        for a0 in range(0, 360, 30):
            d.arc([X-R, Y-R, X+R, Y+R], a0, a0+16, fill=c, width=int(3*esc_t))
    d.line([X, Y-R-16*esc_t, X, Y-R-5*esc_t], fill=c, width=int(3*esc_t))
    et, mv = etiqueta(idd, nom)
    dyl = 0
    for _, ppx, ppy, _, _ in marcades:
        if abs(ppx - X) < 260*esc_t and 0 < (Y - ppy) < 46*esc_t:
            dyl = int(46*esc_t)
    d.text((X+R+9*esc_t, Y-16*esc_t+dyl), et, fill=c, font=(F if nom else Fs))
    if mv:
        d.text((X+R+9*esc_t, Y+14*esc_t+dyl), f"V = {mv}", fill=(205, 205, 200), font=Ft)
    marcades.append((idd, X, Y, nom, ok))

nok = sum(1 for m in marcades if m[4])
w0, h0 = int(1290*esc_t), int(250*esc_t)
d.rectangle([24, 24, 24+w0, 24+h0], fill=(10, 12, 14), outline=(120, 130, 130), width=2)
d.text((48, 44), f"{T['titol']}", fill=(240, 244, 242), font=F)
d.text((48, 44+int(36*esc_t)), f"{FRAME.rsplit('.',1)[0]} · {T['peu']} · pla verd cru",
       fill=(190, 196, 193), font=Fs)
yy = 24 + int(120*esc_t)
d.ellipse([52, yy, 52+int(30*esc_t), yy+int(30*esc_t)], outline=GROC, width=int(3*esc_t))
d.text((52+int(48*esc_t), yy), "identificada al catàleg", fill=(240, 244, 242), font=Fs)
yy += int(50*esc_t)
d.ellipse([54, yy, 54+int(26*esc_t), yy+int(26*esc_t)], outline=VERD, width=int(3*esc_t))
d.text((52+int(48*esc_t), yy), "confirmada, sense identificar en aquest retall", fill=(240, 244, 242), font=Fs)
yy += int(48*esc_t)
for a0 in range(0, 360, 30):
    d.arc([54, yy, 54+int(26*esc_t), yy+int(26*esc_t)], a0, a0+16, fill=(190, 195, 190), width=int(3*esc_t))
d.text((52+int(48*esc_t), yy), f"cal la pila per veure-la ({len(marcades)-nok} de {len(marcades)})",
       fill=(240, 244, 242), font=Fs)

img.save(os.path.join(AQUI, f"estrelles_{tren}_marcades.png"))
print(f"imatge desada · {nok} visibles en aquest fotograma sol, {len(marcades)} marcades")

# ---------------------------------------------------------------- zooms
sel = sorted([m for m in marcades if m[3] and m[4]], key=lambda m: m[0])[:7]
Z, ESC, ALT = (34, 4, 34) if T["mitja_res"] else (48, 3, 34)
if sel:
    tw = len(sel) * (Z*2*ESC + 10) + 10
    tira = Image.new("RGB", (tw, Z*2*ESC + ALT + 14), (10, 12, 14))
    dz = ImageDraw.Draw(tira)
    for i, (idd, X, Y, nom, ok) in enumerate(sel):
        cut = snr[int(Y)-Z:int(Y)+Z, int(X)-Z:int(X)+Z]
        if cut.shape != (2*Z, 2*Z):
            continue
        im = Image.fromarray((np.clip(cut/14.0, 0, 1)**0.65*255).astype(np.uint8))
        im = im.resize((Z*2*ESC, Z*2*ESC), Image.NEAREST).convert("RGB")
        pxx = 10 + i*(Z*2*ESC + 10)
        tira.paste(im, (pxx, 8))
        et, mv = etiqueta(idd, nom)
        dz.text((pxx+4, Z*2*ESC + 14), f"{et}  V={mv}" if mv else et, fill=(240, 240, 235), font=fnt(19))
    tira.save(os.path.join(AQUI, f"estrelles_{tren}_zooms.png"))
    print(f"tira de {len(sel)} zooms desada ({Z*2} px de costat, escala {ESC}x)")
