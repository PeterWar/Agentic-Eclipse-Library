"""s11 · EN COORDENADES DEL SENSOR (graella del subplà G, 2660 × 4000; G = mitjana de G1 i G2 calibrats amb el flat 2D del pilot, sense
registre): textura fina de cada fotograma (residu relatiu en dues bandes: ULTRAFINA σ 0,5–2 subplans, la que el flat 2D NO toca, i FINA
σ 2–7, dins de la banda del flat 2D), a la zona 3–9,5 R☉ de cada fotograma, fora de la Lluna. S'apila per meitats (A1, A2, B1, B2) SENSE
registrar: el patró fix al sensor s'hi suma; el cel s'hi mou amb la deriva (A: ~1 subplà; B: ~4) i, entre A i B, amb el salt (~370 subplans).
  · corr(A, B) al sensor → el patró PERMANENT del sensor (el mateix a tots dos apuntaments; el cel no hi pot correlacionar);
  · corr(A1, A2) − corr(A, B) → el que és NOMÉS d'A (la hipòtesi del fil o la pols durant A);
  · corr(·, flat) → si el patró és al flat (el residu no radial del màster de 53 flats, de la ronda 1).
I a T1 i T2: el perfil del traç al sensor, a la posició on el veu cada apuntament (p_A, p_B), a A1, A2, B1, B2 i al flat.
Variables: FLAT2D_SONY (npz del flat 2D; per defecte el del pilot) i S11_ETIQUETA (per defecte flat2d).
Sortida: S11_SENSOR_<etiqueta>.json, sensor_<etiqueta>/sensor_<meitat>_<banda>.npz (imatges del sensor per a les vistes) i la vista diag_sensor_*.png."""
import sys, json, time, math, os
from pathlib import Path
CRT = Path(__file__).resolve().parents[2] / 'v97_refundacio_20260924/cadena_raw'; sys.path.insert(0, str(CRT))
import a4_sources as _A4; _A4.CID = json.loads((_A4.R / '.coordination/claim.lock/owner.json').read_text())['claim_id']
assert _A4.CID == 'CLAUDE_V108_MARRONS_I_ZONES_NEGRES_20260926', _A4.CID
from a4_sources import *
sys.path.insert(0, str(Path(__file__).resolve().parent)); import comu_sonyA as CS
guard(); t00 = time.time(); OUT = CS.OUT
FL2D = Path(os.environ.get('FLAT2D_SONY') or CS.ARREL / '4-RESULTATS/v108_20260926/marrons/flat2d/SONYTOT_flat2d.npz'); ETIQ = os.environ.get('S11_ETIQUETA', 'flat2d')
SD = OUT / f'sensor_{ETIQ}'; SD.mkdir(exist_ok=True)
_C = np.load(FL2D)['C'].astype(np.float32); _orig_init = f2.Ctx.__init__
def _init_flat2d(s, run):
    _orig_init(s, run); s.flat = (s.flat * _C).astype(np.float32)
f2.Ctx.__init__ = _init_flat2d
ns, fr = context(); ns.update(FLAT_CENTRE_YX={'sony': (2660., 4000.)}, FLAT_SIGMA_PX=32.)
definition(fr['sources']['common32']['copy'], 'flat_ripple_correction', ns)
path = f12dirs['sony']; run = comu.Run.obre(str(path)); ctx = f2.Ctx(run); fcorr, _ = ns['flat_ripple_correction'](ctx, 'sony')
MP = json.loads((OUT / 'fotogrames_flat2d/MAPATGE.json').read_text()); inv = np.array(MP['inv_common_to_final'])
CX, CY, K, ca, sa, dB = MP['CX'], MP['CY'], MP['k'], MP['ca'], MP['sa'], MP['delta_B_rad']
def a_sensor(x, y, f):
    qx = inv[0, 0] * x + inv[0, 1] * y + inv[0, 2]; qy = inv[1, 0] * x + inv[1, 1] * y + inv[1, 2]; dx = (qx - CX) * K; dy = (qy - CY) * K
    if f['grup'] == 'sony_B': c_, s_ = np.cos(dB), np.sin(dB); dx, dy = c_ * dx - s_ * dy, s_ * dx + c_ * dy
    return np.array([ca * dx + sa * dy + f['sol_x'] + f['cx'], -sa * dx + ca * dy + f['sol_y'] + f['cy']])
def afi_sensor_a_llenc(f):
    P = np.array([[0., 0.], [1000., 0.], [0., 1000.]]); S = np.array([a_sensor(x, y, f) for x, y in P])   # raw
    A = np.linalg.lstsq(np.c_[S, np.ones(3)], P, rcond=None)[0].T; return A   # llenç = A · [raw_x, raw_y, 1]
MEITAT = lambda f: ('A1' if f['t'] <= 18 else 'A2') if f['grup'] == 'sony_A' else ('B1' if f['t'] <= 70 else 'B2')
hs, ws_ = 2660, 4000
BANDES = {'ultrafina': (0.5, 2.0), 'fina': (2.0, 7.0)}
ACC = {(m, b): [np.zeros((hs, ws_), np.float32), np.zeros((hs, ws_), np.float32)] for m in ('A1', 'A2', 'B1', 'B2') for b in BANDES}
gy, gx = np.mgrid[0:hs, 0:ws_].astype(np.float32); usats = {}
def banda(img, m, s1, s2):
    w = m.astype(np.float32); v = np.where(m, img, 0).astype(np.float32)
    ng = lambda x, s: cv2.GaussianBlur(x * w, (0, 0), s) / np.maximum(cv2.GaussianBlur(w, (0, 0), s), 1e-6)
    return np.where(m, ng(v, s1) / np.maximum(ng(v, s2), 1e-12) - 1, 0).astype(np.float32)
for nom, f in MP['fotogrames'].items():
    if f['exp'] < 0.1: continue
    plans = ctx.plans(nom, f['exp']); o1 = ctx.orig[1]; o3 = ctx.orig[3]
    g1, w1 = plans[1]; g3, w3 = plans[3]
    if fcorr is not None: g1 = g1 * fcorr[1]; g3 = g3 * fcorr[3]
    G = 0.5 * (g1[:hs, :ws_] + g3[:hs, :ws_]); Wg = np.minimum(w1[:hs, :ws_], w3[:hs, :ws_])
    # zona: posició al llenç de cada superpíxel (centre raw = 2·(i,j) + 0,5) → distància al Sol en R☉, i fora de la Lluna
    A = afi_sensor_a_llenc(f); rx = 2 * gx + 0.5; ry = 2 * gy + 0.5
    lx = A[0, 0] * rx + A[0, 1] * ry + A[0, 2]; ly = A[1, 0] * rx + A[1, 1] * ry + A[1, 2]; r = np.hypot(lx - CS.SOL[0], ly - CS.SOL[1]) / CS.RSOL
    m = (Wg > 0.9 * np.nanmax(Wg)) & np.isfinite(G) & (G > 0) & (r > 3.0) & (r < 9.5)
    if m.mean() < 0.05: continue
    mt = MEITAT(f); usats.setdefault(mt, []).append(nom)
    for b, (s1, s2) in BANDES.items():
        rb = banda(G, m, s1, s2); med = np.median(rb[m]); mad = 1.4826 * np.median(np.abs(rb[m] - med)); mm = m & (np.abs(rb - med) < 6 * mad)
        ACC[(mt, b)][0] += np.where(mm, rb, 0) * f['exp']; ACC[(mt, b)][1] += mm * f['exp']
    print(f"{nom} {f['grup']} {f['exp']:g}s t {f['t']} → {mt} · zona {m.mean()*100:.0f} % · {time.time()-t00:.0f}s", flush=True); del plans
IM = {}
for (mt, b), (nu, de) in ACC.items():
    IM[(mt, b)] = np.where(de > 0, nu / np.maximum(de, 1e-9), np.nan).astype(np.float32); np.savez(SD / f'sensor_{mt}_{b}.npz', rel=IM[(mt, b)], pes=de)
# flat: residu no radial del màster (ronda 1), mateixes bandes
FL = np.load(CS.ARREL / '4-RESULTATS/v108_20260926/marrons/flat_sony_residu_no_radial.npy')[:hs, :ws_] + 1.0
for b, (s1, s2) in BANDES.items():
    mf = np.isfinite(FL) & (FL > 0.5); IM[('flat', b)] = np.where(mf, banda(FL, mf, s1, s2), np.nan)
res = dict(meitats=usats, bandes=BANDES, correlacions={}, tracos={})
def corr_map(a, b, S=12):
    k = np.isfinite(a) & np.isfinite(b); a0 = np.where(k, a - a[k].mean(), 0).astype(np.float32); b0 = np.where(k, b - b[k].mean(), 0).astype(np.float32)
    cc = np.fft.fftshift(np.fft.irfft2(np.conj(np.fft.rfft2(a0)) * np.fft.rfft2(b0), s=a0.shape)); cy, cx = hs // 2, ws_ // 2
    win = cc[cy - S:cy + S + 1, cx - S:cx + S + 1] / np.sqrt((a0 * a0).sum() * (b0 * b0).sum()); iy, ix = np.unravel_index(np.argmax(win), win.shape)
    anell = win.copy(); anell[S - 5:S + 6, S - 5:S + 6] = np.nan
    return dict(a_zero=float(win[S, S]), pic=float(win[iy, ix]), pic_dx_dy=[int(ix - S), int(iy - S)], fons=float(np.nanmedian(anell)), fons_mad=float(1.4826 * np.nanmedian(np.abs(anell - np.nanmedian(anell)))), n=int(k.sum()))
for b in BANDES:
    A_ = np.nanmean(np.stack([IM[('A1', b)], IM[('A2', b)]]), 0); B_ = np.nanmean(np.stack([IM[('B1', b)], IM[('B2', b)]]), 0); IM[('A', b)] = A_; IM[('B', b)] = B_
    for p, q in (('A1', 'A2'), ('B1', 'B2'), ('A', 'B'), ('A1', 'B1'), ('A2', 'B2'), ('A1', 'B2'), ('A2', 'B1'), ('A', 'flat'), ('B', 'flat'), ('A1', 'flat'), ('B1', 'flat')):
        c = corr_map(IM[(p, b)], IM[(q, b)]); res['correlacions'][f'{b}_{p}_{q}'] = c
        print(f"{b:9s} {p}×{q}: a 0 {c['a_zero']:+.4f} · pic {c['pic']:+.4f} a {c['pic_dx_dy']} · fons {c['fons']:+.4f}±{c['fons_mad']:.4f} · n {c['n']}", flush=True)
# T1 i T2 al sensor: perfil a p_A (on el veu l'apuntament A) i a p_B, amb nul de paral·leles
ref = {'A': MP['fotogrames']['DSC06987.ARW'], 'B': MP['fotogrames']['DSC06993.ARW']}
for k, tr in CS.TRACOS.items():
    for ap_, f in ref.items():
        e = tr['extrems']; s0 = a_sensor(e[0, 0], e[0, 1], f) / 2; s1 = a_sensor(e[1, 0], e[1, 1], f) / 2   # subplans
        c = 0.5 * (s0 + s1); d = (s1 - s0) / np.linalg.norm(s1 - s0); L = float(np.linalg.norm(s1 - s0))
        if not (0 <= min(s0[0], s1[0]) and max(s0[0], s1[0]) < ws_ and 0 <= min(s0[1], s1[1]) and max(s0[1], s1[1]) < hs):
            res['tracos'][f'T{k}_a_p{ap_}'] = dict(fora_del_sensor=True, extrems_subpla=[s0.tolist(), s1.tolist()]); print(f'T{k} a p{ap_}: fora del sensor', flush=True); continue
        row = dict(extrems_subpla=[s0.round(1).tolist(), s1.round(1).tolist()])
        for nom in ('A1', 'A2', 'B1', 'B2', 'A', 'B', 'flat'):
            for b in BANDES:
                img = IM[(nom, b)]
                t, pr, cov = CS.perfil(img, (0, 0), c, d, L, tmax=200, dt=0.25, ds=1.0, cob_min=0.5)
                cen = np.abs(t) <= 1.5; fl = (np.abs(t) >= 5) & (np.abs(t) <= 25)
                D0 = float(np.nanmean(pr[cen]) - np.nanmean(pr[fl])) if np.isfinite(pr[cen]).sum() > 3 else np.nan
                nul = [float(np.nanmean(pr[np.abs(t - t0) <= 1.5]) - np.nanmean(pr[(np.abs(t - t0) >= 5) & (np.abs(t - t0) <= 25)])) for t0 in list(np.arange(-180, -29, 3)) + list(np.arange(30, 181, 3))]
                nul = np.array([x for x in nul if np.isfinite(x)])
                zz = (D0 - np.median(nul)) / (1.4826 * np.median(np.abs(nul - np.median(nul)))) if len(nul) > 20 and np.isfinite(D0) else np.nan
                row[f'{nom}_{b}'] = dict(D=D0, z=float(zz), cobertura=float(np.nanmean(cov[np.abs(t) <= 25])))
        res['tracos'][f'T{k}_a_p{ap_}'] = row
        print(f"T{k} al sensor a p{ap_} {row['extrems_subpla']}: " + ' · '.join(f"{n} {v['D']*1e4:+.1f}‱ z{v['z']:+.1f}" for n, v in row.items() if isinstance(v, dict) and 'D' in v and n.endswith('fina') and not n.endswith('ultrafina')), flush=True)
        print(f"      ultrafina: " + ' · '.join(f"{n[:-10]} {v['D']*1e4:+.1f}‱ z{v['z']:+.1f}" for n, v in row.items() if isinstance(v, dict) and n.endswith('ultrafina')), flush=True)
res['flat2d'] = str(FL2D); CS.desa(OUT / f'S11_SENSOR_{ETIQ}.json', res); print('FET', f'{time.time()-t00:.0f}s', flush=True)
