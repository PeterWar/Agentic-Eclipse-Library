"""a4 (V116, 29-09-2026) · Guany del realç sobre l'estructura AZIMUTAL (raigs i buits a radi fix), NOMÉS amb la nostra dada.
Al pla polar (r, θ) centrat al Sol (a 1/4 del llenç): z = ln X − ln mediana_θ(X) a cada anell (treu el gradient radial exacte) i z_loc = z − G_θ(z)
(σ 6°, treu el gradient del cel i l'asimetria gran de la corona); suavitzat lleu (σ_r 2, σ_θ 1 mostra) per al soroll. X = la fusió LINEAL sense
estrelles (fonts_c) o una sortida (compost desat). Per bandes de radi, fora de les marques de Pere, ajust robust per trams (medianes per quantils de
z_lin): g+ (z_lin > 0, raigs) i g− (z_lin < 0, buits); A = g−/g+ (1 = realç simètric; > 1 = foscor afegida). Per a cada marca, E = (⟨z_out⟩/⟨z_lin⟩ a
la marca)/g+ de la seva banda. Sortida JSON i, a més, els plans polars z_loc (npz) per a les vistes.
Ús: a4_guany_polar.py <sortida.json> <nom=render.tif|.npy> [...]"""
import sys, json, numpy as np, tifffile, cv2
from pathlib import Path
from scipy import ndimage as ndi
ARREL = Path(__file__).resolve().parents[3]; O = ARREL / '4-RESULTATS/v116_20260929'
lab = np.load(O / 'marques_V115_etiquetes.npy'); M = json.load(open(O / 'MARQUES_V115.json'))['marques']; H, W = lab.shape
def quart(x): return x[:H // 4 * 4, :W // 4 * 4].reshape(H // 4, 4, W // 4, 4).mean((1, 3))
def llum(path):
    a = np.load(path, mmap_mode='r') if str(path).endswith('.npy') else tifffile.memmap(path, mode='r')
    return np.mean([quart(np.asarray(a[..., c], np.float32)) for c in range(3)], 0).astype(np.float32)
SOL = (5361.768 / 4, 3775.748 / 4); RS = 440.603 / 4
R = np.arange(int(1.15 * RS), int(9.6 * RS)).astype(np.float32); NT = 7200; TH = np.arange(NT) * 2 * np.pi / NT
MX = (SOL[0] + R[:, None] * np.cos(TH)[None, :]).astype(np.float32); MY = (SOL[1] - R[:, None] * np.sin(TH)[None, :]).astype(np.float32)
lab4 = lab[:H // 4 * 4:4, :W // 4 * 4:4].astype(np.float32); LABP = cv2.remap(lab4, MX, MY, cv2.INTER_NEAREST, borderValue=0).astype(np.int16)
RP = (R / RS)[:, None] * np.ones((1, NT), np.float32)
def zloc(L):
    P = cv2.remap(L, MX, MY, cv2.INTER_LINEAR, borderValue=0); v = P > 1e-6
    lp = np.where(v, np.log(np.maximum(P, 1e-12)), np.nan)
    med = np.nanmedian(lp, 1, keepdims=True); z = lp - med
    zz = np.where(v, z, 0); vv = v.astype(np.float32); s = 6 / 360 * NT
    num = ndi.gaussian_filter1d(zz, s, axis=1, mode='wrap'); den = ndi.gaussian_filter1d(vv, s, axis=1, mode='wrap')
    zl = np.where(v & (den > 0.5), z - num / np.maximum(den, 1e-6), np.nan)
    num2 = ndi.gaussian_filter(np.nan_to_num(zl), (2, 1), mode=('nearest', 'wrap')); den2 = ndi.gaussian_filter(np.isfinite(zl).astype(np.float32), (2, 1), mode=('nearest', 'wrap'))
    return np.where(np.isfinite(zl) & (den2 > 0.5), num2 / np.maximum(den2, 1e-6), np.nan).astype(np.float32)
LIN = llum(ARREL / '4-RESULTATS/v114_estrelles_20260928/fonts_c/fusio/d4/products/sources/fusion_starless.npy'); zl_lin = zloc(LIN)
BANDES = ((1.3, 2.0), (2.0, 3.5), (3.5, 5.5), (5.5, 9.5))
def trams(x, y):
    q = np.quantile(x, np.linspace(0.01, 0.99, 50)); xm, ym = [], []
    for lo, hi in zip(q[:-1], q[1:]):
        s = (x >= lo) & (x < hi)
        if s.sum() > 100: xm.append(np.median(x[s])); ym.append(np.median(y[s]))
    xm, ym = np.array(xm), np.array(ym); n_, p_ = xm < 0, xm > 0
    return float(np.sum(xm[n_] * ym[n_]) / np.sum(xm[n_] ** 2)), float(np.sum(xm[p_] * ym[p_]) / np.sum(xm[p_] ** 2))
res = {}; plans = dict(lineal=zl_lin)
for arg in sys.argv[2:]:
    nom, path = arg.split('=', 1); zo = zloc(llum(ARREL / path)); plans[nom] = zo; r = dict(bandes={}, marques={})
    for a, b in BANDES:
        k = (RP >= a) & (RP < b) & (LABP == 0) & np.isfinite(zl_lin) & np.isfinite(zo)
        gm, gp = trams(zl_lin[k], zo[k]); r['bandes'][f'{a}-{b}'] = dict(g_fosc=round(gm, 3), g_clar=round(gp, 3), A=round(gm / gp, 3), sd_lin_pct=round(float(np.std(zl_lin[k])) * 100, 2))
    for m in M:
        kk = (LABP == m['marca']) & np.isfinite(zl_lin) & np.isfinite(zo); bn = next((f'{a}-{b}' for a, b in BANDES if a <= m['r_Rsol'] < b), None)
        if kk.sum() < 20 or bn is None: continue
        cl_, co_ = float(np.mean(zl_lin[kk])), float(np.mean(zo[kk])); gp = r['bandes'][bn]['g_clar']
        r['marques'][m['marca']] = dict(banda=bn, z_lineal_pct=round(cl_ * 100, 2), z_sortida_pct=round(co_ * 100, 2), esperat_pct=round(cl_ * gp * 100, 2),
                                         E=round((co_ / cl_) / gp, 2) if cl_ < -0.002 else None)
    res[nom] = r
np.savez_compressed(Path(sys.argv[1]).with_suffix('.npz'), **{k: v.astype(np.float16) for k, v in plans.items()}, LABP=LABP)
json.dump(dict(nota=__doc__.split('\n')[0], resultats=res), open(sys.argv[1], 'w'), ensure_ascii=False, indent=1)
for nom, r in res.items():
    print(nom, 'bandes:', json.dumps(r['bandes'], ensure_ascii=False))
    print('   marques (sortida / esperat, %; E):', ' '.join(f"{k}:{v['z_sortida_pct']:.1f}/{v['esperat_pct']:.1f}(E {v['E']})" for k, v in r['marques'].items()))
