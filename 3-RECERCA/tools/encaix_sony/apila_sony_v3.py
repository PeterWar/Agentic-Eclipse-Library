"""Apilat Sony v3 (19-08-2026, vespre): «fins l'últim fotó» amb MEITATS. Tots els fotogrames de dins la totalitat de MÉS
de 1/8 s (1/4 ×3, 1 s ×2, 2 s ×3, 8 s ×2 = 24,75 s) registrats a la reixa de la DSC06993 i sumats en ADU/s amb pes =
exposició, i a més dos acumuladors de meitats (A i B, alternades per equilibrar la suma d'exposicions: 12,25 / 12,5 s)
per mesurar el soroll i la coherència a baixa freqüència de l'apilat.

Exclosos: DSC06990 (8 s, moguda pel salt 2 de muntura) i DSC06988 (1 s, grup B): les seves estrelles són TRAÇOS de
~25 px en y (S01: σ_maj 7,3 px, detectada només a 6,7σ contra 35σ a la 06985) perquè cau a l'inici del salt 2, i el
seu offset «astromètric» (−6,13, 693,38) era una cerca a 4σ que ni tan sols cau sobre el traç (centre ≈ (−12, 714)).
Vegeu sony3/analisi_06988.log i retalls_tots.log. Cap 1/8 s.

Respecte d'apila_sony_v2.py:
 (1) el registre per correlació de la corona de v2 (banda 6–40 px del ln amb màscara comuna dins el filtre) s'ha
     demostrat INSENSIBLE al desplaçament (una imatge desplaçada 20 px torna −2,5; escampada 25 px no eixampla el pic):
     el pic queda clavat per la vora comuna de la màscara sobre el gradient radial. Per això a v2 els 1/4 s (06982,
     06994, 06997) van quedar a la mitjana del grup, 1–3 px fora de lloc. A v3 els fotogrames sense astrometria es
     registren amb les ESTRELLES brillants del catàleg (S01…S09), per diferència amb el fotograma astromètric del mateix
     grup més proper en el temps (06984 per a 06982; 06996 per a 06994; 06999 per a 06997): mediana de ≥3 estrelles
     detectades a >5σ als dos. Les estrelles també es mesuren als fotogrames amb OFF (residu contra el catàleg, informatiu);
 (2) pes = exposició (igual), mateix anivellament del cel (pla + σ 300 px) contra la 06993, mateixa saturació física;
 (3) MEITATS: A = {06993, 06996, 06985, 06991, 06982}, B = {06987, 06984, 06999, 06994, 06997}; el total és A+B.
Sortides a SONY3_OUT: sony_stack_v3_rgb.npy, sony_stack_v3_wt.npy, sony_half_{A,B}_rgb.npy, sony_half_{A,B}_wt.npy,
registre_v3.json. Variables: EXCLOU_V3 (noms separats per comes a saltar), SAT_V2, SONY3_OUT.
"""
import os, pickle, sys, json, time
import numpy as np, rawpy, cv2
from scipy import ndimage as ndi

WORK = os.path.expanduser('~/Desktop/Eclipse 2026/Derivats/Astrometria/Estrelles/Work_2026-08-17/sony')
DADES = os.path.expanduser('~/Desktop/Eclipse 2026/300mm A7RIIIA')
SCR = '/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/5aa2c2e9-5325-491b-a6ff-4feeb4581ac0/scratchpad'
OUT = os.environ.get('SONY3_OUT', os.path.join(SCR, 'sony3'))
os.makedirs(OUT, exist_ok=True)
OFF = pickle.load(open(os.path.join(WORK, 'offsets6.pkl'), 'rb'))['off']
M = np.load(os.path.join(WORK, 'warpM.npy')); Tt = np.load(os.path.join(WORK, 'warpT.npy')); Cc = np.load(os.path.join(WORK, 'warpC.npy'))
Minv = np.linalg.inv(M)
SX_, SY_ = 3894.7, 2768.7; R_PX = 295.8
SAT_V2 = float(os.environ.get('SAT_V2', 16100)); DIL = 3
EXCLOU = set(filter(None, os.environ.get('EXCLOU_V3', '').split(',')))
# (nom, exposició, grup de muntura, meitat, fotograma astromètric de referència d'estrelles si no té OFF)
# l'ordre: la referència primer; cada fotograma de referència d'estrelles abans del que el necessita
FRAMES = [('DSC06993', 8., 'C', 'A', None), ('DSC06996', 2., 'C', 'A', None), ('DSC06999', 2., 'C', 'B', None),
          ('DSC06991', 1., 'C', 'A', None), ('DSC06994', 0.25, 'C', 'B', 'DSC06996'), ('DSC06997', 0.25, 'C', 'B', 'DSC06999'),
          ('DSC06984', 2., 'A', 'B', None), ('DSC06985', 1., 'A', 'A', None), ('DSC06987', 8., 'A', 'B', None),
          ('DSC06982', 0.25, 'A', 'A', 'DSC06984')]
EXCLOSOS = {'DSC06990': '8 s moguda pel salt 2 de muntura (research/72)',
            'DSC06988': "1 s, traços d'estrelles de ~25 px en y (inici del salt 2); offset astromètric a 4σ no fiable (sony3/analisi_06988)"}
FRAMES = [f for f in FRAMES if f[0] not in EXCLOU]
# MEITATS_PER_GRUP=1 (v9): les meitats són els dos GRUPS de muntura (A = grup A, 11,25 s; B = grup C, 13,5 s). Com que el
# grup A va desplaçat (−233, +713) px respecte del C pel salt de muntura, tot el que és fix al sensor (pols, residu de
# flat, PRNU) cau en llocs del cel diferents a cada meitat i la coherència entre meitats ho rebutja; el que és del cel hi
# coincideix. És la porta de «cada píxel compta» de la SEMIFINAL9.
if os.environ.get('MEITATS_PER_GRUP', '0') == '1':
    FRAMES = [(n, e, g, ('A' if g == 'A' else 'B'), r) for n, e, g, m, r in FRAMES]
SIG = {0: 1.0, 1: 0.7, 2: 1.0}
N_EST = 9          # estrelles del catàleg (les més brillants) que es mesuren
SNR_EST = 5.0      # S/N mínim del pic per comptar una estrella
t0 = time.time()
def log(*a): print(f'[{time.time()-t0:6.0f} s]', *a, flush=True)

def masterdark(e):
    nom = {8.: '8', 2.: '2', 1.: '1', 0.25: '0.25', 0.125: '0.125'}[e]
    for d in (WORK, OUT, os.path.join(SCR, 'sony2')):
        p = os.path.join(d, f'masterdark_{nom}s.npy')
        if os.path.exists(p): return np.load(p)
    raise SystemExit('falta masterdark ' + nom)

def normconv(a, m, sig):
    return ndi.gaussian_filter(a * m, sig, mode='constant'), ndi.gaussian_filter(m, sig, mode='constant')

def llegeix(n, e):
    with rawpy.imread(os.path.join(DADES, n + '.ARW')) as r:
        raw = r.raw_image_visible.astype(np.float32); col = r.raw_colors_visible.copy()
    res = raw - masterdark(e)
    sat = ndi.binary_dilation(raw >= SAT_V2, iterations=DIL)
    valid = ~sat
    valid[:40] = valid[-40:] = False; valid[:, :40] = valid[:, -40:] = False
    return res, col, valid, float(sat.mean())

def plans(res, col, valid, e):
    """tres plans (ADU/s) a resolució plena + pes, a la reixa nativa del fotograma."""
    I3 = []; W3 = []
    for c, pl in ((0, (0,)), (1, (1, 3)), (2, (2,))):
        m = (valid & np.isin(col, pl)).astype(np.float32)
        num, den = normconv(np.where(m > 0, res, 0.0).astype(np.float32), m, SIG[c])
        I3.append((np.where(den > 0.08, num / np.maximum(den, 1e-6), 0.0) / e).astype(np.float32))
        W3.append((den > 0.08).astype(np.float32))
    return I3, W3

def transform(A_xy, b_xy, I, order=1):
    A_rc = np.array([[A_xy[1, 1], A_xy[1, 0]], [A_xy[0, 1], A_xy[0, 0]]]); b_rc = np.array([b_xy[1], b_xy[0]])
    return ndi.affine_transform(I, A_rc, offset=b_rc, order=order, mode='constant', cval=0.0)

def ab_for(grup, dx, dy):
    if grup == 'A':
        A_xy = Minv; b_xy = -Minv @ (Cc + Tt) + Cc + np.array([dx, dy])
    else:
        A_xy = np.eye(2); b_xy = np.array([dx, dy])
    return A_xy, b_xy

# ---- catàleg d'estrelles (coordenades de la 06993), les N_EST més brillants
CAT = []
for ln in open(os.path.join(WORK, 'catalog_sony.txt')):
    if ln.startswith('#') or not ln.strip(): continue
    p = ln.split(); CAT.append((p[0], float(p[1]), float(p[2]), float(p[7])))
CAT = sorted(CAT, key=lambda c: -c[3])[:N_EST]

def estrelles_natives(G, grup, dx0, dy0, B=60):
    """Posicions natives trobades de les estrelles del catàleg al pla verd G (ADU/s), cercades a ±B px de la posició
    predita amb l'offset inicial (dx0, dy0). Retorna {id: (x_nat, y_nat, snr, sig_maj, sig_min)} per a les de pic > SNR_EST."""
    A_xy, b_xy = ab_for(grup, dx0, dy0); H, W = G.shape; out = {}
    for sid, x, y, snr_cat in CAT:
        xin, yin = A_xy @ np.array([x, y]) + b_xy
        xi, yi = int(round(xin)), int(round(yin))
        if not (B + 2 <= xi < W - B - 2 and B + 2 <= yi < H - B - 2): continue
        cut = G[yi - B:yi + B + 1, xi - B:xi + B + 1].astype(np.float64); yy, xx = np.mgrid[-B:B + 1, -B:B + 1]
        A_ = np.c_[np.ones(cut.size), xx.ravel(), yy.ravel()]; v = cut.ravel(); k = np.ones(v.size, bool)
        for _ in range(4):
            p, *_ = np.linalg.lstsq(A_[k], v[k], rcond=None); r_ = v - A_ @ p
            sd = 1.4826 * np.median(np.abs(r_[k] - np.median(r_[k]))) + 1e-9; k = np.abs(r_) < 3 * sd
        d = cut - (p[0] + p[1] * xx + p[2] * yy); sm = ndi.gaussian_filter(d, 1.5)
        sd_sm = 1.4826 * np.median(np.abs(sm - np.median(sm))) + 1e-9
        iy, ix = np.unravel_index(np.argmax(sm), sm.shape); pic_sn = sm[iy, ix] / sd_sm
        if pic_sn < SNR_EST: continue
        lab, nl = ndi.label(sm > 3 * sd_sm)
        if lab[iy, ix] == 0: continue
        reg = lab == lab[iy, ix]; w = np.where(reg, d, 0).clip(0, None); s = w.sum()
        if s <= 0: continue
        mx = (w * xx).sum() / s; my = (w * yy).sum() / s
        cxx = (w * (xx - mx) ** 2).sum() / s; cyy = (w * (yy - my) ** 2).sum() / s; cxy = (w * (xx - mx) * (yy - my)).sum() / s
        ev = np.linalg.eigvalsh([[cxx, cxy], [cxy, cyy]])
        out[sid] = (float(xi + mx), float(yi + my), float(pic_sn), float(np.sqrt(max(ev[1], 0))), float(np.sqrt(max(ev[0], 0))))
    return out

def residu_estrelles(est, grup, dx, dy):
    """mediana i MAD de (trobada − predita amb (dx,dy)) sobre les estrelles trobades: comprovació d'un offset."""
    A_xy, b_xy = ab_for(grup, dx, dy); r = []
    for sid, x, y, _ in CAT:
        if sid in est:
            xin, yin = A_xy @ np.array([x, y]) + b_xy; r.append((est[sid][0] - xin, est[sid][1] - yin))
    if not r: return None
    r = np.array(r); med = np.median(r, axis=0); mad = 1.4826 * np.median(np.abs(r - med), axis=0)
    return dict(n=len(r), med=[float(med[0]), float(med[1])], mad=[float(mad[0]), float(mad[1])])

H = W = None
ACC = {'A': None, 'B': None}; WT = {'A': None, 'B': None}
REF = [None] * 3; REFW = [None] * 3
XX_ = YY_ = RR_ = None
registre = {}; EST = {}; OFFV3 = {}
for n, e, g, meitat, refest in FRAMES:
    res, col, valid, fsat = llegeix(n, e)
    if H is None:
        H, W = res.shape
        for k in ('A', 'B'):
            ACC[k] = np.zeros((H, W, 3), np.float32); WT[k] = np.zeros((H, W, 3), np.float32)
        YY_, XX_ = np.mgrid[0:H, 0:W].astype(np.float32)
        RR_ = (np.hypot(XX_ - SX_, YY_ - SY_) / R_PX).astype(np.float32)
    I3, W3 = plans(res, col, valid, e)
    del res
    # ---- offset: conegut (offsets6) o per estrelles contra el fotograma astromètric del grup més proper en el temps
    if n in OFF:
        dx, dy = OFF[n]; font = 'astrometria'
        EST[n] = estrelles_natives(I3[1], g, dx, dy)
        chk = residu_estrelles(EST[n], g, dx, dy)
        info = dict(dx=float(dx), dy=float(dy), grup=g, font=font, meitat=meitat,
                    estrelles=dict(n=len(EST[n]), residu_vs_cataleg=chk,
                                   detall={k: dict(x=v[0], y=v[1], snr=v[2], sig_maj=v[3], sig_min=v[4]) for k, v in EST[n].items()}))
        if chk: log(f'   {n} estrelles: {chk["n"]} trobades; residu trobada−predita med ({chk["med"][0]:+.2f}, {chk["med"][1]:+.2f}) MAD ({chk["mad"][0]:.2f}, {chk["mad"][1]:.2f})')
    else:
        if refest not in EST: raise SystemExit(f'{n}: el fotograma de referència d\'estrelles {refest} no s\'ha processat abans')
        if g == 'A': dx0, dy0 = np.mean([OFF[k] for k in ('DSC06984', 'DSC06985', 'DSC06987')], axis=0)
        else: dx0, dy0 = np.mean([OFF[k] for k in ('DSC06991', 'DSC06993', 'DSC06996', 'DSC06999')], axis=0)
        est = estrelles_natives(I3[1], g, dx0, dy0); EST[n] = est
        com = [sid for sid in est if sid in EST[refest]]
        if len(com) >= 3:
            dif = np.array([(est[s][0] - EST[refest][s][0], est[s][1] - EST[refest][s][1]) for s in com])
            med = np.median(dif, axis=0)
            # un pic de soroll a 5σ dins la finestra de ±60 px pot passar: fora les que s'aparten > 3 px de la mediana
            keep = np.hypot(dif[:, 0] - med[0], dif[:, 1] - med[1]) < 3.0
            if keep.sum() >= 3 and keep.sum() < len(com):
                log(f'   {n}: es descarten {[s for s, k in zip(com, keep) if not k]} (> 3 px de la mediana)')
                com = [s for s, k in zip(com, keep) if k]; dif = dif[keep]; med = np.median(dif, axis=0)
            mad = 1.4826 * np.median(np.abs(dif - med), axis=0)
            # nat_n − nat_ref = off_n − off_ref (mateix grup → mateix warp; només canvia la translació)
            dx = OFFV3[refest][0] + med[0]; dy = OFFV3[refest][1] + med[1]; font = f'estrelles vs {refest}'
            log(f'   {n} registre per estrelles contra {refest}: {len(com)} comunes {com}, diferència med ({med[0]:+.2f}, {med[1]:+.2f}) MAD ({mad[0]:.2f}, {mad[1]:.2f}) → offset ({dx:.2f}, {dy:.2f}) [inicial grup ({dx0:.2f}, {dy0:.2f})]')
            info = dict(dx=float(dx), dy=float(dy), grup=g, font=font, meitat=meitat, inicial=[float(dx0), float(dy0)],
                        estrelles=dict(n=len(est), comunes=com, dif_med=[float(med[0]), float(med[1])], dif_mad=[float(mad[0]), float(mad[1])],
                                       detall={k: dict(x=v[0], y=v[1], snr=v[2], sig_maj=v[3], sig_min=v[4]) for k, v in est.items()}))
        else:
            dx, dy = dx0, dy0; font = 'mitjana del grup (estrelles insuficients)'
            log(f'   ⚠️ {n}: només {len(com)} estrelles comunes amb {refest}; es queda a la mitjana del grup ({dx:.2f}, {dy:.2f})')
            info = dict(dx=float(dx), dy=float(dy), grup=g, font=font, meitat=meitat, estrelles=dict(n=len(est), comunes=com))
    OFFV3[n] = (float(dx), float(dy)); registre[n] = info
    A_xy, b_xy = ab_for(g, dx, dy)
    for c in range(3):
        Iw = transform(A_xy, b_xy, I3[c]); Ww = transform(A_xy, b_xy, W3[c])
        Ww = np.where(Ww > 0.97, 1.0, 0.0).astype(np.float32)
        if n == 'DSC06993':
            REF[c] = Iw.copy(); REFW[c] = Ww > 0
        else:
            # anivellament del cel: pla robust + residu suavitzat σ 300 px sobre r > 3,5 R☉ (com apila_sony.py / v2)
            m_ = ((Ww > 0) & REFW[c] & (RR_ > 3.5)).astype(np.float32)
            dif = Iw - REF[c]
            sub = (m_ > 0)[::6, ::6]
            dv = dif[::6, ::6][sub].astype(np.float64); xs_ = XX_[::6, ::6][sub].astype(np.float64); ys_ = YY_[::6, ::6][sub].astype(np.float64)
            A_ = np.c_[np.ones_like(dv), xs_ / 1000.0, ys_ / 1000.0]; keep = np.ones(len(dv), bool)
            for it in range(3):
                p, *_ = np.linalg.lstsq(A_[keep], dv[keep], rcond=None)
                res_ = dv - A_ @ p; sd = 1.4826 * np.median(np.abs(res_[keep] - np.median(res_[keep])))
                keep = np.abs(res_) < 3 * sd
            pla = (p[0] + p[1] * XX_ / 1000.0 + p[2] * YY_ / 1000.0).astype(np.float32)
            BS = 8; Hb, Wb = (H // BS) * BS, (W // BS) * BS
            def blk(a): return a[:Hb, :Wb].reshape(Hb // BS, BS, Wb // BS, BS).mean(axis=(1, 3))
            dnum = ndi.gaussian_filter(blk((dif - pla) * m_), 300.0 / BS, mode='constant'); dden = ndi.gaussian_filter(blk(m_), 300.0 / BS, mode='constant')
            cs = np.where(dden > 0.02, dnum / np.maximum(dden, 1e-6), np.nan)
            idx_ = ndi.distance_transform_edt(np.isnan(cs), return_distances=False, return_indices=True)
            cs = cs[tuple(idx_)].astype(np.float32)
            corr_ = pla + ndi.zoom(cs, (H / cs.shape[0], W / cs.shape[1]), order=1)[:H, :W]
            Iw = np.where(Ww > 0, Iw - corr_, 0.0).astype(np.float32)
            if c == 1:
                cm = corr_[m_ > 0]
                log(f'   {n} anivellament G: mediana {np.median(cm):+.1f} ADU/s, rang {cm.min():+.1f}…{cm.max():+.1f}')
                registre[n]['anivellament_G'] = dict(mediana=float(np.median(cm)), min=float(cm.min()), max=float(cm.max()))
        ACC[meitat][..., c] += Iw * Ww * e; WT[meitat][..., c] += Ww * e
    log(f'{n} {e} s grup {g} meitat {meitat} offset ({dx:.2f}, {dy:.2f}) [{font}] saturat {fsat:.4f}')
    del I3, W3

WTt = WT['A'] + WT['B']; ACCt = ACC['A'] + ACC['B']
out = np.where(WTt > 0, ACCt / np.maximum(WTt, 1e-9), np.nan).astype(np.float32)
np.save(os.path.join(OUT, 'sony_stack_v3_rgb.npy'), out); np.save(os.path.join(OUT, 'sony_stack_v3_wt.npy'), WTt)
del ACCt, out
for k in ('A', 'B'):
    hk = np.where(WT[k] > 0, ACC[k] / np.maximum(WT[k], 1e-9), np.nan).astype(np.float32)
    np.save(os.path.join(OUT, f'sony_half_{k}_rgb.npy'), hk); np.save(os.path.join(OUT, f'sony_half_{k}_wt.npy'), WT[k])
    del hk
json.dump(dict(frames=[(n, e, g) for n, e, g, _, _ in FRAMES], meitats={k: [n for n, e, g, m, _ in FRAMES if m == k] for k in ('A', 'B')},
               exposicio_meitats={k: float(sum(e for n, e, g, m, _ in FRAMES if m == k)) for k in ('A', 'B')},
               registre=registre, exclosos=EXCLOSOS, SAT_V2=SAT_V2, pes='exposicio', referencia='DSC06993',
               estrelles_cataleg=[c[0] for c in CAT]),
          open(os.path.join(OUT, 'registre_v3.json'), 'w'), indent=1)
log('fet: forma', (H, W, 3), 'pes màxim (s)', float(WTt.max()), 'meitat A', float(WT['A'].max()), 'meitat B', float(WT['B'].max()),
    'fracció sense dada (verd)', float((WTt[..., 1] <= 0).mean()))
