"""On cau cada imatge de «Projecte photoshop/2-Filtres» dins el llenç E de 7648×5353 (CapesInteriors /
CapesExteriors / Aplicant_Filtres). Correlació creuada (sense blanquejar) del passa-alt σ6 sobre retalls de
1024 px al voltant del Sol, subpíxel per DFT (skimage, upsample 50). Referència: la fusionada
d'Aplicant_Filtres.tif, que ja és E. Només lectura.

Convenció: per a cada font es dona un NOMINAL (E = font + (ox, oy)); es retalla la font a (x0−⌊ox⌋, y0−⌊oy⌋) i es
mesura on cau el seu contingut respecte del retall E: si cau a s = (dx, dy), la col·locació bona és
⌊nominal⌋ − s (⚠️ el signe: «cau a −1,7» vol dir que s'ha de posar 1,7 px MÉS a la dreta). Amb el nominal
exacte i un pas alt del mateix signe, s = −(part fraccionària del nominal).

Resultat del 18-08-2026 (vespre): filtres_Tangencials.tif → E + (456, 462) i filtres_radials.tif → E + (599, 549),
tots dos a 0,00 px; reixa del pipeline (Corona_HDR_Vixen, 6958×4638) → E + (542,6, 418,5) ± 0,1 px, coherent amb
P → reixa DNG (85,50, −44,02) [documentat (84,89, −44,34)] i DNG → E (457,0, 462,7).
"""
import os, sys, json, numpy as np, tifffile, cv2
from scipy import ndimage as ndi
from skimage.registration import phase_cross_correlation
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capes_tiff import TiffCapes

D = os.path.expanduser("~/Desktop/Eclipse 2026/Projecte photoshop/2-Filtres/")
BASE = os.path.join(D, "Recursos", "Base", "Aplicant_Filtres.tif")
ALINEATS = os.path.join(D, "Recursos", "Alineats", "alineades_7648x5353")
CHV = os.path.expanduser("~/Desktop/Eclipse 2026/Derivats/Vixen/Corona_HDR_Vixen/")
SUN_E = (4020.0, 2737.0)          # el Sol a E, aproximat (només per triar retalls)
S = 1024
OFFS = [(-1400, -512), (400, -1500), (-1400, 500), (300, 400), (-600, -1500), (600, -900), (-1900, -200), (900, 200), (-300, 700), (-1000, -1400)]

def lum_tif(p): return tifffile.imread(p).astype(np.float32).mean(-1) / 65535
def lum_capa(p, k):
    return TiffCapes(p).rgb(k).astype(np.float32).mean(-1) / 65535
def lum_png(p):
    a = cv2.imread(p, cv2.IMREAD_UNCHANGED)
    if a.ndim == 3: a = a[..., ::-1].mean(-1)
    return a.astype(np.float32) / (255.0 if a.dtype == np.uint8 else 65535.0)

def hp(a, m, s=6):
    A = np.where(m, a, np.nanmedian(a[m]) if m.any() else 0)
    A = A - ndi.gaussian_filter(A, s); A = A * m
    if m.any(): A -= A[m].mean()
    return A * m

def mesura(a, b, signe=+1.0):
    """(dx, dy, ncc): on cau b respecte d'a. signe = −1 si b és un pas alt invertit."""
    m = np.isfinite(a) & np.isfinite(b)
    if m.mean() < 0.5: return None
    A = hp(a, m); B = signe * hp(b, m)
    if A.std() < 1e-7 or B.std() < 1e-7: return None
    sh, err, _ = phase_cross_correlation(A, B, upsample_factor=50, normalization=None)
    ncc = float((A * B).sum() / np.sqrt((A * A).sum() * (B * B).sum()))
    return -sh[1], -sh[0], ncc      # sh és el que cal moure B perquè coincideixi amb A → B cau a −sh

def patch(img, x0, y0, s=S):
    h, w = img.shape
    out = np.full((s, s), np.nan, np.float32)
    ix0, iy0, ix1, iy1 = max(x0, 0), max(y0, 0), min(x0 + s, w), min(y0 + s, h)
    if ix1 > ix0 and iy1 > iy0:
        out[iy0 - y0:iy1 - y0, ix0 - x0:ix1 - x0] = img[iy0:iy1, ix0:ix1]
    return out

if __name__ == "__main__":
    REF = lum_tif(BASE)
    a0 = patch(REF, 2500, 1200); b0 = np.roll(np.roll(a0, 3, axis=1), -2, axis=0)
    print("prova de signe (b = a desplaçat (+3, −2)) →", mesura(a0, b0)[:2])
    FONTS = [
        ("Tangencials capa 0 (3)", lambda: lum_capa(D + "filtres_Tangencials.tif", 0), (456, 462), +1),
        ("Tangencials capa 4 (a)", lambda: lum_capa(D + "filtres_Tangencials.tif", 4), (456, 462), -1),
        ("Tangencials capa 3 (b)", lambda: lum_capa(D + "filtres_Tangencials.tif", 3), (456, 462), -1),
        ("Radials Background", lambda: lum_capa(D + "filtres_radials.tif", 0), (599, 549), +1),
        ("Radials filtre radial B", lambda: lum_capa(D + "filtres_radials.tif", 1), (599, 549), +1),
        ("Radials filtre radial A", lambda: lum_capa(D + "filtres_radials.tif", 2), (599, 549), -1),
        ("PASSALT_FORT (retall P a (40,85))", lambda: lum_tif(D + "corona_vixen_PASSALT_FORT.tif"), (582.6, 503.5), +1),
        ("detall.png (reixa P)", lambda: lum_png(D + "corona_vixen_detall.png"), (542.6, 418.5), +1),
        ("radial.png (reixa P)", lambda: lum_png(D + "corona_vixen_radial.png"), (542.6, 418.5), +1),
    ]
    res = {}
    for nom, carrega, (ox, oy), signe in FONTS:
        img = carrega()
        oxi, oyi = int(np.floor(ox)), int(np.floor(oy)); fx, fy = ox - oxi, oy - oyi
        print(f"\n== {nom} ({img.shape[1]}x{img.shape[0]}): nominal E = font + ({ox}, {oy}) → si és exacte, cau a ({-fx:+.2f}, {-fy:+.2f})")
        vals = []
        for (dx0, dy0) in OFFS:
            x0, y0 = int(SUN_E[0] + dx0), int(SUN_E[1] + dy0)
            r = mesura(patch(REF, x0, y0), patch(img, x0 - oxi, y0 - oyi), signe)
            if r is None: continue
            dx, dy, ncc = r
            print(f"   retall @({dx0:+5d},{dy0:+5d}): cau a ({dx:+.2f}, {dy:+.2f})   NCC {ncc:+.3f}")
            vals.append((dx, dy, ncc))
        v = np.array(vals); bo = v[:, 2] > 0.05
        med = np.median(v[bo, :2], axis=0) if bo.sum() >= 2 else np.median(v[:, :2], axis=0)
        print(f"   → mediana ({med[0]:+.2f}, {med[1]:+.2f})  ⇒  col·locació bona E = font + ({oxi - med[0]:.2f}, {oyi - med[1]:.2f})")
        res[nom] = dict(nominal=[ox, oy], collocacio=[float(oxi - med[0]), float(oyi - med[1])], n=int(bo.sum()))
    out = os.path.join(ALINEATS, "mesura_alineacio.json")
    if os.path.isdir(os.path.dirname(out)):
        json.dump(res, open(out, "w"), indent=1, ensure_ascii=False); print("\n→", out)
