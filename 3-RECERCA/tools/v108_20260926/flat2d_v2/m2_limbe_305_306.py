"""m2 (V108, flat2d_v2) · CANVIARIEN LES CAPES 305/306 (detall observat arran del limbe, V105/V106) si es refessin amb el flat 2D?
Les dues capes són el detall TANGENCIAL per fotograma de la caixa lunar: δ_j = ln L_j − mitjana gaussiana al llarg de l'arc (σ_c = 32 px),
L = (R' + 2G' + B')/4 post-matriu, combinat amb a_j = W_G,j · smoothstep(D_real, 0,6, 2) (c1_detall_tangencial.py de la V105). El flat 2D
només multiplica cada fotograma per 1/C (al sensor), o sigui que el canvi de la capa és Δδ = Σ a_j [Δ_j − arc(Δ_j)] / Σ a_j, amb
Δ_j = ln L_j(flat 2D) − ln L_j(control). Aquí es calcula Δδ exactament amb els fotogrames de la caixa lunar (limb_frames, finestra comuna)
del control i del flat 2D, i es compara amb δ mateix (la mateixa fórmula amb els fotogrames del control): rms(Δδ)/rms(δ) per bandes de
distància al limbe i per sectors. Els fotogrames «sense llindar» de la V105/V106 tenen els mateixos plans calibrats (el llindar només canvia
els pesos), o sigui que el canvi relatiu és el mateix. També es mesura l'amplitud de les capes 305/306 de la V107 (Superposar: |valor − 0,5|).
Sortida: 4-RESULTATS/v108_20260926/flat2d_v2/M2_LIMBE_305_306.json"""
import json, sys
from pathlib import Path
import numpy as np, cv2
ARREL = Path(__file__).resolve().parents[4]; OUT = ARREL / '4-RESULTATS/v108_20260926/flat2d_v2'
LF0 = ARREL / '4-RESULTATS/v98_20260925/cadena_raw/limb_frames_comuna'; LF1 = OUT / 'limb_frames_flat2d'
meta = json.loads((LF0 / 'METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']
N0 = np.load(LF0 / 'numerator.npy', mmap_mode='r'); W0 = np.load(LF0 / 'weight.npy', mmap_mode='r'); N1 = np.load(LF1 / 'numerator.npy', mmap_mode='r'); W1 = np.load(LF1 / 'weight.npy', mmap_mode='r')
Dm = np.load(LF0 / 'distance_model.npy', mmap_mode='r')
geo = json.loads((ARREL / '4-RESULTATS/v97_refundacio_20260924/lineal_v97_franja/A2_GEOMETRIA.json').read_text())['lluna_presentacio']; cx, cy, R = geo['cx'], geo['cy'], geo['R']
Rm = float(meta['radius_model']); DR = Rm - R
sil = np.load(ARREL / '4-RESULTATS/v99_banda_20260925/D21_silueta_o2.npz'); SIL_PA = np.asarray(sil['pa'], float); SIL_E = np.asarray(sil['e'], float)
Mx = np.array(meta['matrix'], np.float64); gain = np.array(meta['gain'], np.float64)
hb, wb = by1 - by0, bx1 - bx0; yy, xx = np.mgrid[by0:by1, bx0:bx1]
def dreal(j):
    Dj = np.asarray(Dm[j], np.float64); gy_, gx_ = np.gradient(Dj); iy_, ix_ = hb // 2, wb - 100
    cxj = ix_ + bx0 - (Dj[iy_, ix_] + Rm) * gx_[iy_, ix_]; cyj = iy_ + by0 - (Dj[iy_, ix_] + Rm) * gy_[iy_, ix_]
    PAj = (np.degrees(np.arctan2(-(yy - cyj), xx - cxj)) + 360) % 360
    return (Dj + DR - np.interp(PAj.ravel(), SIL_PA, SIL_E, period=360).reshape(hb, wb)).astype(np.float32)
dgrid = np.arange(-4.0, 40.0001, 0.25).astype(np.float32); nth = int(round(2 * np.pi * R / 0.5)); th = np.linspace(0, 2 * np.pi, nth, endpoint=False)
X = (cx + np.cos(th)[None, :] * (R + dgrid[:, None]) - bx0).astype(np.float32); Y = (cy - np.sin(th)[None, :] * (R + dgrid[:, None]) - by0).astype(np.float32)
def pol(a): return cv2.remap(np.ascontiguousarray(a, np.float32), X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
def ss(x): x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)
sc = 32.0 / 0.5
def arc(v, w):   # mitjana gaussiana normalitzada al llarg de l'arc (periòdica)
    from scipy.ndimage import gaussian_filter1d
    return gaussian_filter1d(v * w, sc, axis=1, mode='wrap') / np.maximum(gaussian_filter1d(w, sc, axis=1, mode='wrap'), 1e-9)
def lum(N, Wt, j):
    E = np.where(Wt[j] > 0, np.asarray(N[j], np.float64) / np.maximum(np.asarray(Wt[j], np.float64), 1e-30), 0.0)
    P = np.einsum('ij,...j->...i', Mx, E * gain); L = (P[..., 0] + 2 * P[..., 1] + P[..., 2]) / 4; return L, (Wt[j] > 0).all(-1) & (L > 0)
Sa = np.zeros((len(dgrid), nth)); Sd = np.zeros_like(Sa); Sdd = np.zeros_like(Sa); Sdd2 = np.zeros_like(Sa)
pesos_iguals = True
for j in range(len(fr)):
    L0, ok0 = lum(N0, W0, j); L1, ok1 = lum(N1, W1, j); pesos_iguals &= bool(np.array_equal(np.asarray(W0[j]), np.asarray(W1[j])))
    ok = ok0 & ok1; a = np.asarray(W0[j, :, :, 1], np.float64) * ss((dreal(j) - 0.6) / (2.0 - 0.6)) * ok
    lp0 = pol(np.where(ok, np.log(np.maximum(L0, 1e-30)), 0)); lp1 = pol(np.where(ok, np.log(np.maximum(L1, 1e-30)), 0)); ap = pol(a); okp = (pol(ok.astype(np.float32)) > 0.99) & (ap > 0)
    w = okp.astype(np.float64)
    d0 = np.where(okp, lp0 - arc(lp0, w), 0); dd = np.where(okp, (lp1 - lp0) - arc(lp1 - lp0, w), 0)
    aw = np.where(okp, ap, 0); Sa += aw; Sd += aw * d0; Sdd += aw * dd
    if j % 10 == 0: print('fotograma', j + 1, len(fr), flush=True)
delta = np.where(Sa > 0, Sd / np.maximum(Sa, 1e-30), np.nan); ddelta = np.where(Sa > 0, Sdd / np.maximum(Sa, 1e-30), np.nan)
res = dict(pesos_dels_fotogrames_iguals=pesos_iguals, sigma_arc_px=32.0, bandes={})
pa = (np.degrees(th)) % 360
for d0_, d1_ in ((0.5, 1), (1, 2), (2, 3), (3, 5), (5, 10), (10, 20), (20, 30), (30, 40)):
    kd = (dgrid >= d0_) & (dgrid < d1_); A_ = delta[kd]; B_ = ddelta[kd]; k = np.isfinite(A_) & np.isfinite(B_)
    if k.sum() < 100: continue
    row = dict(rms_delta=float(np.sqrt(np.mean(A_[k] ** 2))), rms_canvi=float(np.sqrt(np.mean(B_[k] ** 2))), max_abs_canvi=float(np.abs(B_[k]).max()))
    row['canvi_sobre_delta'] = row['rms_canvi'] / row['rms_delta']; sect = {}
    for s0 in range(0, 360, 45):
        ks = k & ((pa[None, :] >= s0) & (pa[None, :] < s0 + 45))
        if ks.sum() > 50: sect[s0] = dict(rms_delta=float(np.sqrt(np.mean(A_[ks] ** 2))), rms_canvi=float(np.sqrt(np.mean(B_[ks] ** 2))))
    row['per_sector_45'] = sect; res['bandes'][f'{d0_}-{d1_}px'] = row
    print(f'{d0_}-{d1_} px', f"δ rms {row['rms_delta']:.4f}  Δδ rms {row['rms_canvi']:.5f}  ({100*row['canvi_sobre_delta']:.1f} %)  màx {row['max_abs_canvi']:.4f}", flush=True)
# amplitud de les capes 305/306 de la V107 (Superposar: la desviació de 0,5) per bandes de distància al limbe de presentació
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917')); from psb69 import PSB
p = PSB(str(ARREL / '1-PHOTOSHOP/V107.psb')); capes = {}
for l in p.layers:
    if l['id'] in (305, 306):
        x0, y0, x1, y1 = l['bbox'] if 'bbox' in l else (l['left'], l['top'], l['right'], l['bottom'])
        ch = [p.channel_box(l['id'], c, (x0, y0, x1, y1)).astype(np.float32) / 65535 for c in (0, 1, 2)]; v = np.mean(ch, 0)
        al = p.channel_box(l['id'], -1, (x0, y0, x1, y1)).astype(np.float32) / 65535 if -1 in l['chans'] else np.ones_like(v)
        yy2, xx2 = np.mgrid[y0:y1, x0:x1]; dL = np.hypot(xx2 - cx, yy2 - cy) - R; row = {}
        for d0_, d1_ in ((0.5, 1), (1, 2), (2, 3), (3, 5), (5, 10), (10, 20), (20, 30), (30, 40)):
            k = (dL >= d0_) & (dL < d1_) & (al > 0.5)
            if k.sum() > 100: row[f'{d0_}-{d1_}px'] = dict(rms_desviacio_de_0_5=float(np.sqrt(np.mean((v[k] - 0.5) ** 2))), px=int(k.sum()))
        capes[l['id']] = dict(nom=l['name'], visible=l['visible'], opacitat=l['opacity'], caixa=[x0, y0, x1, y1], per_banda=row)
res['capes_V107'] = capes
(OUT / 'M2_LIMBE_305_306.json').write_text(json.dumps(res, ensure_ascii=False, indent=1)); print('FET', json.dumps({k: v.get('per_banda', {}).get('1-2px') for k, v in capes.items()}), flush=True)
