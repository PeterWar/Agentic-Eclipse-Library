"""a7 (V116, 29-09-2026) · La línia fosca estreta sota el traç taronja: perfil a 1 px i extensió al llarg de la recta (ajust lineal del traç, extrapolat
a x 3000–10000). Per a cada font: fondària del clot a l'offset o* (el mínim a |o| ≤ 12) respecte de o ∈ [15, 40] a banda i banda, per trams de 100 px en x.
Fonts: sortida V115 (sense 414), les capes de filtre de la V115, la base 3, les entrades lineals de la cadena v114c i les de b1 (A, B)."""
import sys, json, numpy as np, cv2, tifffile
from pathlib import Path
R = Path(__file__).resolve().parents[3]; O = R / '4-RESULTATS/v116_20260929'; OUT = O / 'taronja'
sys.path.insert(0, str(R / '3-RECERCA/tools/v108_20260926/cadena'))
from comu_v108 import PSB
lab = np.load(O / 'marques_V115_etiquetes.npy', mmap_mode='r'); Y0, Y1 = 4300, 4800
sub = np.asarray(lab[Y0:Y1, 6000:7000]) == 11; cols = np.nonzero(sub.any(0))[0]; yc = np.array([np.nonzero(sub[:, c])[0].mean() for c in cols]) + Y0
a_, b_ = np.polyfit(cols + 6000, yc, 1); print(f'recta del traç: y = {a_:.5f}·x + {b_:.1f}  (pendent {np.degrees(np.arctan(a_)):.2f}°)', flush=True)
XA, XB = 3000, 10000
def fila(img_fn):
    """retorna el perfil 2D P[o, x] = detall(x, y(x)+o), o ∈ [−40, 40]"""
    return None
p = PSB(str(R / '1-PHOTOSHOP/V115.psb'))
yl = a_ * np.arange(XA, XB) + b_; ymin, ymax = int(yl.min()) - 120, int(yl.max()) + 120
def capa(lid):
    out = []
    for c in (0, 1, 2):
        a, (x, y) = p.channel(lid, c); z = np.full((ymax - ymin, XB - XA), np.nan, np.float32); h, w = a.shape
        ya, yb, xa, xb = max(ymin, y), min(ymax, y + h), max(XA, x), min(XB, x + w)
        if yb > ya and xb > xa: z[ya - ymin:yb - ymin, xa - XA:xb - XA] = a[ya - y:yb - y, xa - x:xb - x] / 65535
        out.append(z)
    z = np.stack(out, -1); return (z[..., 0] + 2 * z[..., 1] + z[..., 2]) / 4
def lum(a): a = np.asarray(a, np.float32); return (a[..., 0] + 2 * a[..., 1] + a[..., 2]) / 4 if a.ndim == 3 else a
Lc = R / '4-RESULTATS/v114_estrelles_20260928/cadena/v114c'
F = {'Sortida V115': lum(tifffile.memmap(R / '4-RESULTATS/v115_nrgf_20260929/V115_natiu/visible_complet.tif', mode='r')[ymin:ymax, XA:XB] / 65535.)}
for lid in (55, 56, 46, 45, 41, 47, 49, 51, 54, 3): F[f'capa {lid}'] = capa(lid)
F['base_v108_final (entrada)'] = np.asarray(np.load(Lc / 'base/base_v108_final_u16.npy', mmap_mode='r')[ymin:ymax, XA:XB], np.float32) / 65535 if np.load(Lc / 'base/base_v108_final_u16.npy', mmap_mode='r').ndim == 2 else lum(np.load(Lc / 'base/base_v108_final_u16.npy', mmap_mode='r')[ymin:ymax, XA:XB] / 65535.)
for nom, f in (('fusion_starless', 'lineal/fusion_starless.npy'), ('sony_starless', 'lineal/sony_starless.npy'), ('vixen_starless', 'lineal/vixen_starless.npy')): F[nom] = lum(np.load(Lc / f, mmap_mode='r')[ymin:ymax, XA:XB])
xs = np.arange(XA, XB); offs = np.arange(-40, 41); res = {}
for nom, S in F.items():
    S = np.nan_to_num(S).astype(np.float32); m = (S > 1e-5).astype(np.float32); x = np.log(np.maximum(S, 1e-5)) * m
    d = np.where(m > 0, x - cv2.GaussianBlur(x, (0, 0), 25) / np.maximum(cv2.GaussianBlur(m, (0, 0), 25), 1e-6), np.nan)
    P = np.full((len(offs), len(xs)), np.nan, np.float32)
    for i, o in enumerate(offs):
        yy = np.round(yl + o).astype(int) - ymin; P[i] = d[yy, xs - XA]
    prof = np.nanmean(P, 1) * 100; k0 = np.abs(offs) <= 12; ost = offs[k0][np.nanargmin(prof[k0])]
    fons = np.nanmean(prof[(np.abs(offs - ost) >= 15) & (np.abs(offs - ost) <= 40)])
    trams = {}
    for x0 in range(XA, XB, 250):
        kk = (xs >= x0) & (xs < x0 + 250); pr = np.nanmean(P[:, kk], 1) * 100
        if np.isfinite(pr).sum() > 40: trams[x0] = round(float(pr[offs == ost][0] - np.nanmean(pr[(np.abs(offs - ost) >= 15) & (np.abs(offs - ost) <= 40)])), 2)
    res[nom] = dict(o_min=int(ost), fondaria_global_pct=round(float(prof[offs == ost][0] - fons), 3), perfil_1px_o_m10_a_20=[round(float(v), 2) for v in prof[(offs >= -10) & (offs <= 20)]], trams_250px=trams)
    print(f'{nom:28s} o*={ost:+d}  fondària {res[nom]["fondaria_global_pct"]:+.2f} %  trams: ' + ' '.join(f'{k}:{v:+.1f}' for k, v in trams.items()), flush=True)
(OUT / 'A7_LINIA.json').write_text(json.dumps(dict(recta=dict(a=a_, b=b_), fonts=res), ensure_ascii=False, indent=1))
