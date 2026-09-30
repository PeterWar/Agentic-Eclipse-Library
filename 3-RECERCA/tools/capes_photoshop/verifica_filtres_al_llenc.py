"""QA dels lliurables: reobre els TIFF plans i el PSB, comprova mides/perfil/valors i torna a mesurar
l'alineació de cadascun contra la fusionada d'Aplicant_Filtres (E) amb el mateix mètode de mesura_alineacio3."""
import os, sys, numpy as np, tifffile
from scipy import ndimage as ndi
from skimage.registration import phase_cross_correlation
from psd_tools import PSDImage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capes_tiff import TiffCapes

D = os.path.expanduser("~/Desktop/Eclipse 2026/Projecte photoshop/2-Filtres/")
BASE = os.path.join(D, "Recursos", "Base", "Aplicant_Filtres.tif")
OT = os.path.join(D, "Recursos", "Alineats", "alineades_7648x5353")
REF = np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lum", "Aplicant_Filtres_fusionada.npy")).astype(np.float32)
SUN_E = (4020.0, 2737.0); S = 1024
OFFS = [(400, -1500), (-1400, 500), (300, 400), (-600, -1500), (600, -900), (-1900, -200), (900, 200), (-300, 700)]

def hp(a, s=6):
    b = a - ndi.gaussian_filter(a, s); return b - b.mean()
def mesura(a, b, signe=1.0):
    A = hp(a); B = signe * hp(b)
    if B.std() < 1e-7: return None
    sh, err, _ = phase_cross_correlation(A, B, upsample_factor=50, normalization=None)
    ncc = float((A * B).sum() / np.sqrt((A * A).sum() * (B * B).sum()))
    return -sh[1], -sh[0], ncc

SIGNE = {"filtres_Tangencials_a_E7648": -1, "filtres_Tangencials_b_E7648": -1, "filtres_radials_filtre_radial_A_E7648": -1}
print("== TIFF plans")
for f in sorted(os.listdir(OT)):
    if not f.endswith(".tif"): continue
    with tifffile.TiffFile(os.path.join(OT, f)) as t:
        p = t.pages[0]
        icc = 34675 in p.tags
        a = p.asarray()
    L = a.astype(np.float32).mean(-1) / 65535
    vals = []
    for dx0, dy0 in OFFS:
        x0, y0 = int(SUN_E[0] + dx0), int(SUN_E[1] + dy0)
        r = mesura(REF[y0:y0 + S, x0:x0 + S], L[y0:y0 + S, x0:x0 + S], SIGNE.get(f[:-4], 1))
        if r: vals.append(r)
    v = np.array(vals)
    print(f"  {f:48s} {a.shape} {a.dtype} ICC={icc}  cantó (0,0)={a[0,0].tolist()}  "
          f"desplaçament respecte d'E: mediana ({np.median(v[:,0]):+.2f}, {np.median(v[:,1]):+.2f}) "
          f"[{v[:,0].min():+.2f}..{v[:,0].max():+.2f}, {v[:,1].min():+.2f}..{v[:,1].max():+.2f}]  NCC {np.median(v[:,2]):.2f}")

print("== PSB")
psd = PSDImage.open(os.path.join(D, "Filtres_alineats_7648x5353.psb"))
print("  document", psd.width, psd.height, psd.depth, psd.color_mode, "capes:", len(psd))
for l in psd:
    print(f"   {l.name[:70]:70s} bbox={l.bbox} {l.blend_mode.name:13s} op={l.opacity} vis={l.visible}")
# píxels d'una capa de Pere contra la font
T = TiffCapes(D + "filtres_Tangencials.tif")
src = T.rgb(4)
lay = [l for l in psd if l.name.startswith("Tangencials · a")][0]
a = lay.numpy()  # float32 (h,w,4) 0-1
got = np.rint(a[..., :3] * 65535).astype(np.uint16)
print("  capa «Tangencials · a» del PSB vs font: forma", got.shape, src.shape, " màx |dif|", int(np.abs(got.astype(int) - src.astype(int)).max()),
      " bbox", lay.bbox, "(esperat (456, 462, 7417, 5103))")
# i la capa PASSALT contra el TIFF pla corresponent
lay = [l for l in psd if l.name.startswith("corona_vixen_PASSALT")][0]
a = lay.numpy(); got = np.rint(a[..., :3] * 65535).astype(np.uint16)
flat = tifffile.imread(os.path.join(OT, "corona_vixen_PASSALT_FORT_E7648.tif"))
l0, t0, l1, t1 = lay.bbox
print("  capa PASSALT del PSB vs TIFF pla al mateix rectangle: màx |dif|", int(np.abs(got.astype(int) - flat[t0:t1, l0:l1].astype(int)).max()))
# fusionada
m = psd.numpy()
print("  fusionada del PSB:", m.shape, " igual a la base d'Aplicant?", bool(np.array_equal(np.rint(m[..., :3] * 65535).astype(np.uint16), tifffile.imread(BASE))))
