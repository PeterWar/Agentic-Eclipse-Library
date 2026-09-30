"""Inventari de la carpeta 2-Filtres: capes de cada TIFF de Photoshop (previsualització ×8) i estadístiques,
i les imatges soltes. Només lectura. Desa previews PNG i luminàncies float16 al scratchpad."""
import os, sys, time, numpy as np, tifffile, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capes_tiff import TiffCapes

D = os.path.expanduser("~/Desktop/Eclipse 2026/Projecte photoshop/2-Filtres/")
BASE = os.path.join(D, "Recursos", "Base", "Aplicant_Filtres.tif")
SP = os.path.dirname(os.path.abspath(__file__))
OUTP = os.path.join(SP, "previews"); os.makedirs(OUTP, exist_ok=True)
LUM = os.path.join(SP, "lum"); os.makedirs(LUM, exist_ok=True)
t0 = time.time()
def log(*a): print(f"[{time.time()-t0:5.0f} s]", *a, flush=True)

def preview(nom, a, red=8):
    """a: float 0-1 (h,w) o (h,w,3)"""
    h, w = a.shape[:2]
    p = cv2.resize(a, (w // red, h // red), interpolation=cv2.INTER_AREA)
    p8 = np.clip(p * 255, 0, 255).astype(np.uint8)
    if p8.ndim == 3:
        p8 = p8[..., ::-1]
    cv2.imwrite(os.path.join(OUTP, nom + ".png"), p8)

def estad(nom, a):
    a = a.astype(np.float32) / 65535.0
    if a.ndim == 3:
        L = a.mean(-1)
    else:
        L = a
    q = np.percentile(L, [0.1, 1, 50, 99, 99.9])
    log(f"   {nom}: mitjana {L.mean():.4f}  p0.1 {q[0]:.4f} p1 {q[1]:.4f} mediana {q[2]:.4f} p99 {q[3]:.4f} p99.9 {q[4]:.4f}  "
        f"fracció a 0,5±0,002: {np.mean(np.abs(L-0.5)<0.002):.3f}")
    return L

for f, path in (
    ("Aplicant_Filtres.tif", BASE),
    ("filtres_Tangencials.tif", D + "filtres_Tangencials.tif"),
    ("filtres_radials.tif", D + "filtres_radials.tif"),
):
    tc = TiffCapes(path)
    log(tc.resum())
    base = os.path.splitext(f)[0]
    # imatge fusionada
    m = tifffile.imread(path)
    log(f"  fusionada {m.shape} {m.dtype}")
    L = estad(base + " (fusionada)", m)
    preview(base + "_fusionada", m.astype(np.float32) / 65535.0)
    np.save(os.path.join(LUM, base + "_fusionada.npy"), L.astype(np.float16))
    del m
    for c in tc.capes:
        k = c["idx"]
        rgb = tc.rgb(k)
        nomc = f"{base}_capa{k}_{c['nom'].replace(' ', '_').replace('/', '-')[:40]}"
        L = estad(nomc, rgb)
        preview(nomc, rgb.astype(np.float32) / 65535.0)
        np.save(os.path.join(LUM, nomc + ".npy"), L.astype(np.float16))
        # canal alfa / màscara
        for cid, tag in ((-1, "alfa"), (-2, "mascara")):
            a = tc.canal(k, cid)
            if a is not None:
                af = a.astype(np.float32) / 65535.0
                log(f"      {tag}: mitjana {af.mean():.4f} min {af.min():.3f} max {af.max():.3f} fracció opaca {np.mean(af>0.999):.3f}")
                preview(nomc + "_" + tag, af)
        del rgb

for f in ("corona_vixen_PASSALT_FORT.tif", "corona_vixen_PASSALT_FORT_llencPere.tif"):
    a = tifffile.imread(D + f)
    log(f"{f}: {a.shape} {a.dtype}")
    L = estad(f, a)
    preview(os.path.splitext(f)[0], a.astype(np.float32) / 65535.0)
    np.save(os.path.join(LUM, os.path.splitext(f)[0] + ".npy"), L.astype(np.float16))
for f in ("corona_vixen_detall.png", "corona_vixen_radial.png"):
    a = cv2.imread(D + f, cv2.IMREAD_UNCHANGED)
    log(f"{f}: {a.shape} {a.dtype}")
    if a.ndim == 3:
        a = a[..., ::-1]
    L = a.astype(np.float32) / 255.0
    if L.ndim == 3:
        L = L.mean(-1)
    log(f"   mitjana {L.mean():.4f}")
    preview(os.path.splitext(f)[0], a.astype(np.float32) / 255.0)
    np.save(os.path.join(LUM, os.path.splitext(f)[0] + ".npy"), L.astype(np.float16))
log("fet")
