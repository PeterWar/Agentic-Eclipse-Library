"""p6 (pregunta de Pere, 26-09) · Per què a DALT i no a la resta? Per sector (dalt 80–125, baix-esquerra 215–255, baix 250–290, dreta 330–30):
  (1) detall tangencial (DoG 2→16 px d'arc, ln) de la BASE (capa 3 de la V101), del compost de la V101 i de la V80, per distància al cercle;
  (2) la DADA: dues meitats temporals independents (fotogrames primerencs i tardans barrejats per meitats de temps dins de cada classe, TOTS els
      fotogrames amb D_real ≥ 0,5 px, dividits per T): correlació del detall tangencial entre meitats i amb la dada neta a 6–10 px (continuïtat);
      i quants fotogrames veuen cada calaix i a quina D_real màxima.
Només lectura. Làmina: meitat A | meitat B | base | compost V101 | V80, 5×, a dalt i a la dreta."""
import sys, json, os, subprocess
from pathlib import Path
import numpy as np, cv2, tifffile
from scipy.ndimage import gaussian_filter1d
ARREL = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917'))
from psb69 import PSB
O = ARREL / '4-RESULTATS/v100_detall_20260925/pregunta_dalt'; T = ARREL / '3-RECERCA/tools/v100_detall_20260925'
LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736
Dz = O / 'D29_tots_05_10_temps.npz'
if not Dz.exists():
    env = dict(os.environ, D29_LO='0.5', D29_HI='1.0', D29_MEITATS='temps', D29_SORTIDA=str(Dz))
    subprocess.run([sys.executable, '-B', str(T / 'd29_candidat_banda.py')], env=env, check=True, capture_output=True)
Z = np.load(Dz); by0, by1, bx0, bx1 = [int(v) for v in Z['box']]
p = PSB(str(ARREL / '1-PHOTOSHOP/V101.psb')); base = np.stack([p.channel(3, c)[0][by0:by1, bx0:bx1].astype(np.float64) for c in (0, 1, 2)], -1)
comp = np.zeros((by1 - by0, bx1 - bx0, 3)); C = tifffile.imread(ARREL / '4-RESULTATS/v100_detall_20260925/final_V101/vistes/V100_lluna.tif')[..., :3].astype(np.float64)
comp[3000 - by0:3000 - by0 + C.shape[0], 4600 - bx0:4600 - bx0 + C.shape[1]] = C[:by1 - 3000, :bx1 - 4600] if False else 0
ys, xs = max(by0, 3000), max(bx0, 4600); ye, xe = min(by1, 3000 + C.shape[0]), min(bx1, 4600 + C.shape[1]); comp[ys - by0:ye - by0, xs - bx0:xe - bx0] = C[ys - 3000:ye - 3000, xs - 4600:xe - 4600]
V80 = tifffile.imread(ARREL / '1-PHOTOSHOP/V80.tif')[..., :3]; v80 = V80[by0 - 1142:by1 - 1142, bx0 - 1325:bx1 - 1325].astype(np.float64)
lum = lambda X: (X[..., 0] + 2 * X[..., 1] + X[..., 2]) / 4 + 1
DR_, DS_ = 0.25, 0.5; rr = np.arange(-2.0, 14.0, DR_); nth = int(round(2 * np.pi * RL / DS_)); tt = np.arange(nth) * 2 * np.pi / nth
R_, T_ = np.meshgrid(RL + rr, tt, indexing='ij'); mx = (LX + R_ * np.cos(T_) - bx0).astype(np.float32); my = (LY - R_ * np.sin(T_) - by0).astype(np.float32)
def pol(img, ok=None):
    ok = np.ones(img.shape, bool) if ok is None else ok
    a = cv2.remap(np.where(ok, np.log(np.maximum(img, 1e-6)), 0).astype(np.float32), mx, my, cv2.INTER_LINEAR); w = cv2.remap(ok.astype(np.float32), mx, my, cv2.INTER_LINEAR)
    return np.where(w > 0.999, a / np.maximum(w, 1e-6), np.nan)
def det(P):
    ok = np.isfinite(P); x = np.where(ok, P, 0); wv = ok.astype(float)
    g = lambda s: gaussian_filter1d(x * wv, s / DS_, axis=1, mode='wrap') / np.maximum(gaussian_filter1d(wv, s / DS_, axis=1, mode='wrap'), 1e-6)
    return np.where(ok, g(2) - g(16), np.nan)
okd = (Z['NF'] >= 2) & (Z['G'] > 0)
H1 = det(pol(Z['G_parells'], okd & (Z['G_parells'] > 0))); H2 = det(pol(Z['G_senars'], okd & (Z['G_senars'] > 0))); HF = det(pol(Z['G'], okd))
DB, DC, D8 = det(pol(lum(base))), det(pol(lum(comp))), det(pol(lum(v80)))
NFp = cv2.remap(Z['NF'].astype(np.float32), mx, my, cv2.INTER_NEAREST); DXp = cv2.remap(Z['DREAL_MAX'].astype(np.float32), mx, my, cv2.INTER_NEAREST)
thp = np.degrees(tt); rep = {}
def corr(a, b):
    m = np.isfinite(a) & np.isfinite(b); return round(float(np.corrcoef(a[m], b[m])[0, 1]), 2) if m.sum() > 150 else None
SECT = {'dalt 80-125': (80, 125), 'baix-esquerra 215-255': (215, 255), 'baix 250-290': (250, 290), 'dreta 330-30': (330, 30)}
for nom, (a0, a1) in SECT.items():
    sel = (((thp - a0) % 360) < ((a1 - a0) % 360)); net = np.nanmean(HF[(rr >= 6) & (rr < 10)][:, sel], axis=0); r = {}
    for lo, hi in ((0, 1), (1, 2), (2, 3), (3, 5), (5, 8)):
        rows = (rr >= lo) & (rr < hi); h1 = np.nanmean(H1[rows][:, sel], 0); h2 = np.nanmean(H2[rows][:, sel], 0); hf = np.nanmean(HF[rows][:, sel], 0)
        r[f'{lo}-{hi}'] = dict(fotogrames=float(np.nanmedian(NFp[rows][:, sel])), Dreal_max=float(np.nanmedian(np.where(DXp[rows][:, sel] > -50, DXp[rows][:, sel], np.nan))),
                               meitats_r=corr(h1, h2), continuitat_r=corr(hf, net), base_rms=round(float(np.nanstd(DB[rows][:, sel])), 4),
                               compost_rms=round(float(np.nanstd(DC[rows][:, sel])), 4), V80_rms=round(float(np.nanstd(D8[rows][:, sel])), 4))
    rep[nom] = r; print(nom); [print(f'   d {k}: fotogr {v["fotogrames"]:.0f} Dreal {v["Dreal_max"]:.1f} | meitats r {v["meitats_r"]} contin r {v["continuitat_r"]} | base {v["base_rms"]:.3f} compost {v["compost_rms"]:.3f} V80 {v["V80_rms"]:.3f}') for k, v in r.items()]
(O / 'P6_BASE_I_MEITATS_PER_SECTOR.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
# làmina: a dalt (PA ~88–112) i a la dreta (PA ~350–14), 5×, amb marques a d = 0, 1, 2, 3 px
def rect(pa0, pa1):
    s = (((thp - pa0) % 360) < ((pa1 - pa0) % 360)); rows = (rr >= -2) & (rr < 10); return rows, s
def img(P, lo, hi, rows, s):
    a = P[rows][:, s][::-1]; v = np.clip((a - lo) / (hi - lo), 0, 1); v = np.nan_to_num(v, nan=0.08); return cv2.resize((v * 255).astype(np.uint8), None, fx=2.5, fy=10, interpolation=cv2.INTER_NEAREST)
pan = []
for pa0, pa1, tit in ((85, 115, 'dalt'), (345, 15, 'dreta')):
    rows, s = rect(pa0, pa1); fil = []
    for P in (H1, H2, DB, DC, D8):
        q = P[rows][:, s]; sd = np.nanstd(q[np.isfinite(q)]) if np.isfinite(q).any() else 1; fil.append(img(P, -2.5 * sd, 2.5 * sd, rows, s))
    ww = fil[0].shape[1]; marca = np.full((fil[0].shape[0], 12), 255, np.uint8)
    for dmark in (0, 1, 2, 3):
        yrow = int((10 - dmark) / DR_ * 10 - 5); marca[max(0, yrow - 2):yrow + 2, :] = 0
    pan.append(np.hstack(sum([[marca, f] for f in fil], [])))
cv2.imwrite(str(O / 'P6_MEITATS_BASE_COMPOST_V80.png'), np.vstack([pan[0], np.full((20, pan[0].shape[1]), 255, np.uint8), pan[1][:, :pan[0].shape[1]] if pan[1].shape[1] >= pan[0].shape[1] else np.pad(pan[1], ((0, 0), (0, pan[0].shape[1] - pan[1].shape[1])), constant_values=255)]))
print('fet')
