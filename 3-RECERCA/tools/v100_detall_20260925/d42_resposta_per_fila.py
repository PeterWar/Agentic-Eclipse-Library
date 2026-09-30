"""d42 (V102 detall) · La RESPOSTA del compost a la capa fila a fila: a tocar del limbe la base és fosca i Superposar hi multiplica el contrast
relatiu; cal que el compost mostri el detall de la banda amb el mateix pes a cada distància. Del render de prova (capa l) contra el de la V99:
γ(d, PA) = pendent de ln(C_prova/C_V99) sobre (l − 0,5)·alfa, per fila de 0,5 px de d i bloc de 15° de PA (regressió robusta). Referència: la γ mitjana a
d 3–5 px (on s'ha calibrat β). Correcció c = clip(γ_ref/γ, 0,1, 1,5), suavitzada; capa nova δ' = δ·c. Ús: d42_resposta_per_fila.py <capa.npz> <prova_lluna.tif> <sortida.npz>"""
import sys, json
from pathlib import Path
import numpy as np, tifffile
from scipy.ndimage import gaussian_filter
ARREL = Path(__file__).resolve().parents[3]; O = ARREL / '4-RESULTATS/v100_detall_20260925'
Z = np.load(O / sys.argv[1]); by0, by1, bx0, bx1 = [int(v) for v in Z['box']]; lay = Z['delta'] * Z['alfa']
C99 = tifffile.imread(ARREL / '4-RESULTATS/v99_banda_20260925/B/vistes/V99_lluna.tif')[..., :3].astype(np.float64); CP = tifffile.imread(sys.argv[2])[..., :3].astype(np.float64)
LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736
yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = np.hypot(xx - LX, yy - LY) - RL; th = (np.degrees(np.arctan2(-(yy - LY), xx - LX)) + 360) % 360
L = lambda X: (X[..., 0] + 2 * X[..., 1] + X[..., 2]) / 4 + 1
resp = np.zeros_like(lay); sl = (slice(by0 - 3000, by1 - 3000), slice(bx0 - 4600, bx1 - 4600)); resp[:] = np.log(L(CP[sl]) / L(C99[sl]))
DB = np.arange(-1.0, 8.01, 0.5); PB = np.arange(0, 360, 15); gam = np.full((DB.size, PB.size), np.nan)
for i, lo in enumerate(DB):
    for j, a in enumerate(PB):
        z = (d >= lo) & (d < lo + 0.5) & ((((th - a - 7.5) + 180) % 360 - 180) ** 2 < 15 ** 2) & (np.abs(lay) > 1e-4)
        if z.sum() < 60: continue
        x = lay[z]; y = resp[z]; b = np.sum(x * y) / np.sum(x * x)
        for _ in range(3):
            r = y - b * x; s = 1.4826 * np.median(np.abs(r)) + 1e-9; m = np.abs(r) < 3 * s
            if m.sum() < 40: break
            b = np.sum(x[m] * y[m]) / np.sum(x[m] ** 2)
        gam[i, j] = b
ref = np.nanmedian(gam[(DB >= 3) & (DB < 5)], axis=0); c = ref[None, :] / gam; c = np.where(np.isfinite(c), np.clip(c, 0.1, 1.5), np.nan)
okc = np.isfinite(c); cs = gaussian_filter(np.where(okc, c, 0), (0.6, 0.6), mode=('nearest', 'wrap')) / np.maximum(gaussian_filter(okc.astype(float), (0.6, 0.6), mode=('nearest', 'wrap')), 1e-6)
cs = np.where(gaussian_filter(okc.astype(float), (0.6, 0.6), mode=('nearest', 'wrap')) > 0.2, cs, 1.0); cs[DB >= 5] = 1.0
import cv2
fi = np.clip((d - DB[0]) / 0.5 - 0.5, 0, DB.size - 1).astype(np.float32); pj = (((th - 7.5) % 360) / 15.0).astype(np.float32)
cext = np.concatenate([cs, cs[:, :1]], 1).astype(np.float32); cmap = cv2.remap(cext, pj, fi, cv2.INTER_LINEAR)
np.savez_compressed(O / sys.argv[3], box=Z['box'], delta=(Z['delta'] * cmap).astype(np.float32), alfa=Z['alfa'], correccio=cmap.astype(np.float32))
for j, a in enumerate(PB):
    if a in (60, 75, 90, 105, 120, 210, 225, 240, 255): print(a, 'γ per fila d', ' '.join(f'{DB[i]:.1f}:{gam[i, j]:.2f}' for i in range(DB.size) if np.isfinite(gam[i, j]) and DB[i] < 5), '| c', ' '.join(f'{DB[i]:.1f}:{cs[i, j]:.2f}' for i in range(DB.size) if DB[i] < 4))
json.dump(dict(gamma=np.where(np.isfinite(gam), gam, None).tolist(), DB=DB.tolist(), PB=PB.tolist(), correccio=cs.tolist()), open(O / (Path(sys.argv[3]).stem + '_RESPOSTA.json'), 'w'), default=lambda v: None)
