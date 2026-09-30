"""v1 (V106, Claude, 26-09-2026) · Validació de la banda LOLA abans de filtrar.
1. DEIXA-UN-FORA a la banda (on no hi ha veritat independent): per a cada fotograma k de la banda, la corona estimada SENSE k (els altres
   fotogrames de la banda, dividits per la seva T) prediu el que k hauria de veure, g_k·T_k·B_(−k); es compara amb el que k veu, per sector i per
   distància al limbe real de k. Si la vora LOLA i la PSF són bones, el residu és soroll (mediana ~0); si no, és sistemàtic.
2. CONTINUÏTAT amb el règim net i amb la V104: el nivell de la franja V106 contra la de la V104 (E) on totes dues tenen dada, per sector i d.
Canal G de càmera. Sortida: 4-RESULTATS/v106_inversio_20260926/A/V1_VALIDA_BANDA.json"""
import os, json, numpy as np
from pathlib import Path
from scipy.special import erf
R0 = Path(__file__).resolve().parents[3]
LF = R0 / '4-RESULTATS/v106_inversio_20260926/limb_frames_sense_llindar'; RA = R0 / '4-RESULTATS/v106_inversio_20260926/A'
meta = json.loads((LF / 'METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']
num = np.load(LF / 'numerator.npy', mmap_mode='r'); wt = np.load(LF / 'weight.npy', mmap_mode='r'); Dm = np.load(LF / 'distance_model.npy', mmap_mode='r')
geo = json.loads((R0 / '4-RESULTATS/v97_refundacio_20260924/lineal_v97_franja/A2_GEOMETRIA.json').read_text())['lluna_presentacio']; cx, cy, R = geo['cx'], geo['cy'], geo['R']
Rm = float(meta['radius_model']); hb, wb = by1 - by0, bx1 - bx0; yy, xx = np.mgrid[by0:by1, bx0:bx1]
sil = np.load(R0 / '4-RESULTATS/v99_banda_20260925/D21_silueta_o2.npz'); SPA = np.asarray(sil['pa'], float); SE = np.asarray(sil['e'], float)
B1 = {c: {r['j']: r for r in json.loads((R0 / f'4-RESULTATS/v106_inversio_20260926/b1/B1_PSF_LOLA_canal{c}.json').read_text())['fotogrames']} for c in range(3)}
TH_N = json.loads((R0 / '4-RESULTATS/v106_inversio_20260926/b1/B1_PSF_LOLA_canal1.json').read_text())['nord']
L = np.load(R0 / '4-RESULTATS/v106_inversio_20260926/lola/PERFIL_prova.npz'); lh = L['h_km'] * R / 1737.4; ang = (TH_N + L['pa']) % 360; o = np.argsort(ang)
grid = np.arange(0, 360, 0.05); rl = np.interp(grid, ang[o], lh[o], period=360); A = np.stack([np.ones_like(grid), np.cos(np.radians(grid)), np.sin(np.radians(grid)), np.cos(2 * np.radians(grid)), np.sin(2 * np.radians(grid))], 1)
cf, *_ = np.linalg.lstsq(A, rl, rcond=None); RLOLA = rl - A @ cf
def centre(j):
    D = np.asarray(Dm[j], np.float64); gy, gx = np.gradient(D); iy, ix = hb // 2, wb - 100
    return ix + bx0 - (D[iy, ix] + Rm) * gx[iy, ix], iy + by0 - (D[iy, ix] + Rm) * gy[iy, ix]
def dfina(j):
    cxj, cyj = centre(j); p = B1[1][j]; cxj += p['dx']; cyj += p['dy']; a = (np.degrees(np.arctan2(-(yy - cyj), xx - cxj)) + 360) % 360
    return np.hypot(xx - cxj, yy - cyj) - R - np.interp(a, SPA, SE, period=360) - np.interp(a, grid, RLOLA, period=360)
def psf_T(D, s1, f, s2): return (1 - f) * 0.5 * (1 + erf(D / (np.sqrt(2) * s1))) + f * 0.5 * (1 + erf(D / (np.sqrt(2) * s2)))
rep = json.loads((RA / 'lineal_v106_franja/A3D_FRANJA_BANDA.json').read_text()); noms = [f['nom'] for f in rep['fotogrames_banda']]
J = [j for j, f in enumerate(fr) if f['name'] in noms and f['time'] < 40]              # la banda del costat d'avanç: fotogrames primerencs
dP = np.hypot(xx - cx, yy - cy) - R; aP = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
zona = (dP > -4) & (dP < 12); C = 1
DF = {}; Tm = {}; V = {}; Wg = {}
for j in J:
    DF[j] = dfina(j); p = B1[C][j]; Tm[j] = psf_T(DF[j], p['s1'], p['f'], p['s2']); w = np.asarray(wt[j, :, :, C], np.float64); Wg[j] = w; V[j] = np.where(w > 0, np.asarray(num[j, :, :, C]) / np.maximum(w, 1e-30), 0)
def ss(x, a, b): q = np.clip((x - a) / (b - a), 0, 1); return q * q * (3 - 2 * q)
Nt = np.zeros((hb, wb)); Wt = np.zeros((hb, wb))
for j in J:
    g = B1[C][j]['g']; adm = ss(Tm[j], 0.5, 0.7); Nt += V[j] * Wg[j] * adm * g * Tm[j]; Wt += Wg[j] * adm * (g * Tm[j]) ** 2
secs = {'dalt 60-120': (60, 120), 'dalt-esq 120-150': (120, 150), 'esquerra 150-210': (150, 210), 'baix-esq 210-250': (210, 250)}
out = {'deixa_un_fora': {}, 'fotogrames': [fr[j]['name'] for j in J]}
for j in J:
    g = B1[C][j]['g']; adm = ss(Tm[j], 0.5, 0.7); Nk = Nt - V[j] * Wg[j] * adm * g * Tm[j]; Wk = Wt - Wg[j] * adm * (g * Tm[j]) ** 2
    Bk = np.where(Wk > 0, Nk / np.maximum(Wk, 1e-30), np.nan); pred = g * Tm[j] * Bk
    ok = zona & (Wg[j] > 0) & np.isfinite(pred) & (pred > 0) & (Wk > 0.3 * np.nanmedian(Wt[zona & (Wt > 0)]))
    r = {}
    for nm, (lo, hi) in secs.items():
        s = ok & (aP >= lo) & (aP < hi)
        for d0, d1 in [(0.5, 1.0), (1.0, 1.5), (1.5, 2.0), (2.0, 3.0), (3.0, 5.0)]:
            m = s & (DF[j] >= d0) & (DF[j] < d1)
            if m.sum() >= 150: r[f'{nm} · D {d0}-{d1}'] = dict(biaix_pct=round(float(np.median(V[j][m] / pred[m]) - 1) * 100, 2), n=int(m.sum()))
    out['deixa_un_fora'][fr[j]['name']] = dict(t=fr[j]['time'], exp=fr[j]['exposure'], res=r)
    print(fr[j]['name'], round(fr[j]['time'], 1), ' '.join(f"{k.split(' · ')[0][:8]}|{k.split(' D ')[1]}:{v['biaix_pct']:+.1f}" for k, v in r.items()), flush=True)
# continuïtat amb la V104 (franja E) on totes dues tenen dada
Q6 = np.load(RA / 'lineal_v106_franja/A3C_franja_silueta.npz'); Q4 = np.load(R0 / '4-RESULTATS/v103_banda_20260926/E/lineal_v103_franja/A3C_franja_silueta.npz')
E6 = Q6['E'][..., 1]; E4 = Q4['E'][..., 1]; d6 = Q6['domini_E']; d4 = Q4['domini_E']; cont = {}
for nm, (lo, hi) in list(secs.items()) + [('dreta 330-30', (330, 390))]:
    aa = np.where(aP < lo, aP + 360, aP) if hi > 360 else aP; s = (aa >= lo) & (aa < hi)
    for d0, d1 in [(-1, 0), (0, 1), (1, 2), (2, 3), (3, 4), (4, 6), (6, 10), (10, 20)]:
        m6 = s & d6 & (dP >= d0) & (dP < d1); m = m6 & d4 & (E4 > 0) & (E6 > 0)
        cont[f'{nm} · d {d0}..{d1}'] = dict(cobertura_V106=round(float(m6.sum() / max((s & (dP >= d0) & (dP < d1)).sum(), 1)), 2), cobertura_V104=round(float((s & d4 & (dP >= d0) & (dP < d1)).sum() / max((s & (dP >= d0) & (dP < d1)).sum(), 1)), 2),
                                             V106_sobre_V104_pct=(round(float(np.median(E6[m] / E4[m]) - 1) * 100, 2) if m.sum() >= 100 else None))
out['continuitat_V104'] = cont
for k, v in cont.items(): print(k, v)
(RA / 'V1_VALIDA_BANDA.json').write_text(json.dumps(out, indent=1, ensure_ascii=False))
