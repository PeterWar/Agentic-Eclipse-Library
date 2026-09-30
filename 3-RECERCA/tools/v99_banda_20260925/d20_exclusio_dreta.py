"""d20 (V99 banda) · Prova d'EXCLUSIÓ a la dreta (on hi ha veritat): la situació de la banda de dalt (només fotogrames primerencs, vistos a
poca distància del seu limbe) reproduïda on sí que se sap la resposta.
  · Conjunt de prova: els fotogrames CURTS primerencs (t < 32 s). La silueta e(PA) i la corba T es reajusten SENSE ells (exclusió estricta):
    silueta amb les vores de d18 (mitjans/llargs) i els creuaments de d17 de la resta de fotogrames; T_curts només de curts tardans.
  · Estimació A: mitjana ponderada dels curts primerencs amb rampes sobre D_real (i, en la variant «T», dividits per T_curts(D_real)).
  · Veritat B: mitjana ponderada de TOTS els altres fotogrames amb D_real ≥ 9 (independent d'A).
  · Mètriques per calaix de D_real (la distància a què els curts primerencs veuen el píxel, pes mitjà) i sector de PA (285–60°):
    ln(A/B) mediana (anell), p16–p84, i correlació del pas alt (σ 2 px) entre A i B (fidelitat de la textura), i la mateixa correlació
    entre dues meitats de B (sostre de soroll).
Només lectura. Sortida: D20_EXCLUSIO_DRETA.json."""
import json, sys
from pathlib import Path
import numpy as np, cv2
ARREL = Path(__file__).resolve().parents[3]; LF = ARREL / '4-RESULTATS/v98_20260925/cadena_raw/limb_frames_comuna'; O = ARREL / '4-RESULTATS/v99_banda_20260925'
meta = json.loads((LF / 'METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']; Rm = float(meta['radius_model'])
LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736; DR = Rm - RL
def classe(e): return 'curts' if e <= 1 / 800 else ('mitjans' if e <= 1 / 50 else 'llargs')
cls = np.array([classe(f['exposure']) for f in fr]); t = np.array([f['time'] for f in fr]); exps = np.array([f['exposure'] for f in fr]); nF = len(fr)
PROVA = np.flatnonzero((cls == 'curts') & (t < 32))
# --- silueta sense el conjunt de prova
z = np.load(O / 'D18_limbe_real.npz', allow_pickle=True); E18 = z['E']; PAc = z['pa']
d17 = json.loads((O / 'D17_VORA_PER_FOTOGRAMA.json').read_text()); d18 = json.loads((O / 'D18_LIMBE_REAL.json').read_text())
off = {c: d18['comparacio_d17'][c]['mediana'] for c in ('mitjans', 'llargs')}; off['curts'] = float(np.mean([off['mitjans'], off['llargs']]))
obs = []
for j in range(nF):
    if exps[j] > 1.01 or j in PROVA: continue
    for k in range(PAc.size):
        if np.isfinite(E18[j, k]): obs.append((PAc[k], E18[j, k]))
for js, r in d17.items():
    if int(js) in PROVA: continue
    for pa, dv in r['delta'].items():
        pa = float(pa)
        if r['t'] < 32 and 140 <= pa <= 210: continue
        obs.append((pa, dv - off[r['classe']]))
obs = np.array(obs)
def disseny(pa, n=4):
    a = np.radians(pa); cols = [np.ones_like(a)]
    for k in range(1, n + 1): cols += [np.cos(k * a), np.sin(k * a)]
    return np.stack(cols, 1)
A_ = disseny(obs[:, 0]); y_ = obs[:, 1]; w_ = np.ones_like(y_)
for _ in range(8):
    co = np.linalg.lstsq(A_ * w_[:, None], y_ * w_, rcond=None)[0]; r_ = y_ - A_ @ co; s_ = 1.4826 * np.median(np.abs(r_)) + 1e-6; w_ = 1 / np.maximum(1, np.abs(r_) / (2.5 * s_))
pag = np.arange(0, 360, 0.25); eg = disseny(pag) @ co
co_tot = np.load(O / 'D19_silueta.npz')['coef']; eg_tot = disseny(pag) @ co_tot
print('silueta sense la prova, dif. amb la comuna (px) cada 30°:', ' '.join(f"{a}:{eg[a*4]-eg_tot[a*4]:+.2f}" for a in range(0, 360, 30)))
# --- T_curts només dels curts tardans (d19)
d19 = json.loads((O / 'D19_SILUETA_I_COLLAPSE.json').read_text()); tab = d19['T']['curts_tard']
Dg = np.arange(0.0, 6.01, 0.5); lnT = []
for D in Dg:
    v = [row[f'{D:.1f}'] for row in tab.values() if f'{D:.1f}' in row]; lnT.append(float(np.median(v)) if v else np.nan)
lnT = np.array(lnT); ok = np.isfinite(lnT); lnT = np.interp(Dg, Dg[ok], lnT[ok]); lnT = np.minimum(np.minimum.accumulate(lnT[::-1])[::-1], 0)   # monòtona creixent cap a 0
lnT[-1] = 0.0
print('ln T_curts (tardans) per D:', dict(zip(Dg.round(1).tolist(), lnT.round(3).tolist())))
# --- dades
N = np.load(LF / 'numerator.npy', mmap_mode='r'); Wt = np.load(LF / 'weight.npy', mmap_mode='r'); Dm = np.load(LF / 'distance_model.npy', mmap_mode='r')
yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = (np.hypot(xx - LX, yy - LY) - RL).astype(np.float32); th = (np.degrees(np.arctan2(-(yy - LY), xx - LX)) + 360) % 360
caixa = (d > -12) & (d < 40) & ((th >= 285) | (th < 60)); ys, xs = np.nonzero(caixa); y0c, y1c, x0c, x1c = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
sl = (slice(y0c, y1c), slice(x0c, x1c)); YY = yy[sl].astype(np.float64); XX = xx[sl].astype(np.float64); hb, wb = YY.shape
def smoothstep(x, a, b): u = np.clip((x - a) / (b - a), 0, 1); return u * u * (3 - 2 * u)
def D_real(j, e_):
    Dj = np.asarray(Dm[j], np.float64); gy, gx = np.gradient(Dj); iy, ix = 700, 1300
    cx = ix + bx0 - (Dj[iy, ix] + Rm) * gx[iy, ix]; cy = iy + by0 - (Dj[iy, ix] + Rm) * gy[iy, ix]
    pa = (np.degrees(np.arctan2(-(YY - cy), XX - cx)) + 360) % 360
    return Dj[sl] + DR - np.interp(pa.ravel(), pag, e_, period=360).reshape(hb, wb), pa
V = {}; Wj = {}; Drj = {}
for j in range(nF):
    w = np.asarray(Wt[j, :, :, 1])[sl].astype(np.float64); n = np.asarray(N[j, :, :, 1])[sl].astype(np.float64)
    V[j] = np.where(w > 0, n / np.maximum(w, 1e-30), np.nan); Wj[j] = w; Drj[j], _ = D_real(j, eg)
# veritat B (i dues meitats per al sostre de soroll)
altres = [j for j in range(nF) if j not in PROVA]
def mitjana(js, filtre):
    num = np.zeros((hb, wb)); den = np.zeros((hb, wb))
    for j in js:
        m = filtre(j) & (Wj[j] > 0) & np.isfinite(V[j]); num += np.where(m, Wj[j] * V[j], 0); den += np.where(m, Wj[j], 0)
    return np.where(den > 0, num / np.maximum(den, 1e-30), np.nan), den
B, wB = mitjana(altres, lambda j: Drj[j] >= 9)
B1, _ = mitjana(altres[0::2], lambda j: Drj[j] >= 9); B2, _ = mitjana(altres[1::2], lambda j: Drj[j] >= 9)
def estimacio(lo, hi, amb_T):
    num = np.zeros((hb, wb)); den = np.zeros((hb, wb)); dmit = np.zeros((hb, wb))
    for j in PROVA:
        s = smoothstep(Drj[j], lo, hi); T = np.exp(np.interp(Drj[j], Dg, lnT, left=lnT[0], right=0.0)) if amb_T else np.ones((hb, wb))
        m = (Wj[j] > 0) & np.isfinite(V[j]) & (s > 0); w = np.where(m, Wj[j] * s * T ** 2, 0)
        num += np.where(m, Wj[j] * s * T * V[j], 0); den += w; dmit += w * np.where(m, Drj[j], 0)
    return np.where(den > 0, num / np.maximum(den, 1e-30), np.nan), den, np.where(den > 0, dmit / np.maximum(den, 1e-30), np.nan)
def pasalt(X, s=2.0):
    m = np.isfinite(X).astype(np.float32); Xf = np.where(m > 0, X, 0).astype(np.float32)
    g = cv2.GaussianBlur(Xf, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6); return np.where(m > 0, X - g, np.nan)
hB = pasalt(B); hB1 = pasalt(B1); hB2 = pasalt(B2); dd = d[sl]; tt = th[sl]
rep = dict(prova=[int(j) for j in PROVA], silueta_coef_sense_prova=co.tolist(), lnT_curts_tardans=dict(D=Dg.tolist(), lnT=lnT.tolist()), variants={})
for nom, (lo, hi, amb_T) in {'V98_equiv_Dreal_6_9': (6.0, 9.0, False), 'rampa_4_6': (4.0, 6.0, False), 'rampa_3_5.5': (3.0, 5.5, False),
                               'rampa_3_5.5_T': (3.0, 5.5, True), 'rampa_2_4_T': (2.0, 4.0, True), 'rampa_1.5_3.5_T': (1.5, 3.5, True)}.items():
    A, wA, Dmit = estimacio(lo, hi, amb_T); hA = pasalt(A); res = {}
    for sec_nom, (a0, a1) in {'285-330': (285, 330), '330-15': (330, 375), '15-60': (15, 60)}.items():
        sec = (((tt - a0) % 360) < (a1 - a0)); res[sec_nom] = {}
        for k0 in np.arange(1.0, 9.01, 0.5):
            z_ = sec & np.isfinite(A) & np.isfinite(B) & (A > 0) & (B > 0) & (Dmit >= k0) & (Dmit < k0 + 0.5) & (wB > 0)
            if z_.sum() < 150: continue
            lr = np.log(A[z_] / B[z_]); zh = z_ & np.isfinite(hA) & np.isfinite(hB) & np.isfinite(hB1) & np.isfinite(hB2)
            cAB = float(np.corrcoef(hA[zh], hB[zh])[0, 1]) if zh.sum() > 100 else None; cBB = float(np.corrcoef(hB1[zh], hB2[zh])[0, 1]) if zh.sum() > 100 else None
            res[sec_nom][f'{k0:.1f}'] = dict(n=int(z_.sum()), ln_A_B=round(float(np.median(lr)), 4), p16_p84=np.percentile(lr, [16, 84]).round(3).tolist(),
                                             corr_pasalt_AB=None if cAB is None else round(cAB, 3), corr_pasalt_B1B2=None if cBB is None else round(cBB, 3))
    rep['variants'][nom] = res
    print(nom); [print('  ', s_, ' '.join(f"{k}:{v['ln_A_B']:+.3f}/r{v['corr_pasalt_AB']}" for k, v in r.items())) for s_, r in res.items()]
(O / 'D20_EXCLUSIO_DRETA.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
