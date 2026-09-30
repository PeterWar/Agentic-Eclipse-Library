"""a3d (V103 banda) · L'a3c de la V99 (selecció física per fotograma sobre la distància al limbe REAL) més un RÈGIM DE BANDA, només on el règim
net no arriba (el costat d'avanç de la Lluna: dalt, esquerra, baix-esquerra).
Per què (diagnosi del 26-09, 4-RESULTATS/v103_banda_20260926/diag/): la tira llisa arran del limbe NO és cap apilat que ignori la Lluna; és la
rampa 4→6,5 px de l'a3c (porta «biaix ≤ 2 % sense correcció»). Els 11 fotogrames de l'instant de presentació (t 15–22 s, Lluna a ≤ 1,1 px)
tenen, a 2–4 px del limbe real, detall tangencial amb la mateixa amplitud (rms 0,027–0,029) i la mateixa reproductibilitat entre meitats
(ρ 0,83–0,87) que a 7–10 px; l'a3c els llença.
Com:
  · RÈGIM NET = l'a3c tal qual (A3C_RAMPES, per defecte 4→6,5 sobre D_real, tots els fotogrames). Byte a byte on ja hi havia dada neta.
  · RÈGIM DE BANDA (A3D_BANDA, JSON): els fotogrames amb t < tmax que veuen el píxel a D_real ≥ lo (rampa lo→hi), cadascun dividit per la
    seva transmissió de vora T_classe,canal(D_real) MESURADA AQUÍ MATEIX, amb aquests mateixos fotogrames, als sectors de calibració
    (dreta, on els tardans nets són la veritat: E del règim net amb ≥ nmin fotogrames), en calaixos de 0,5 px de D_real; monòtona, i amb el
    desnivell de lluny (≥ 6 px) inclòs, perquè la unió amb el règim net sigui contínua. Pes·T² (variància inversa de V/T). Cap fotograma
    compta dos cops: s_banda = smoothstep(D_real, lo, hi) · (1 − s_net).
  · PORTA per píxel: g = 1 − smoothstep(n_nets_efectius, porta[0], porta[1]); E = (N_net + g·N_banda) / (W_net + g·W_banda).
  · tcorr = "mesura" (per defecte) o "cap" (la banda tal com es veu, amb el dèficit real de la vora, com un fotograma sol).
La resta (validesa, vora del domini, unió amb la fusió a 60–90 px, claus de sortida) és la de l'a3c: f2/f3/j14 la llegeixen igual.
Ús: A3B_LF=<limb_frames_comuna> V97_SORT=<sortida> V97_FONTS=<d4 sources> A3C_SILUETA=<D21_silueta_o2.npz> [A3C_RAMPES=...]
    A3D_BANDA='{"lo":2.0,"hi":3.0,"tmax":32,"porta":[1,4],"calib":[300,60],"nmin":10,"tcorr":"mesura"}' a3d_franja_banda.py"""
import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'v97_refundacio_20260924'))
from v97_comu import *
from v86_operadors import smoothstep
import cv2
from scipy.ndimage import maximum_filter1d, gaussian_filter1d
claim()
LF = Path(os.environ['A3B_LF']); LF = LF if LF.is_absolute() else ARREL / LF
meta = json.loads((LF / 'METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']
num = np.load(LF / 'numerator.npy', mmap_mode='r'); wt = np.load(LF / 'weight.npy', mmap_mode='r'); Dm = np.load(LF / 'distance_model.npy', mmap_mode='r')
geo = json.loads((RES / 'lineal_v97_franja/A2_GEOMETRIA.json').read_text())['lluna_presentacio']; cx, cy, R = geo['cx'], geo['cy'], geo['R']
DR = float(meta['radius_model']) - R
RAMPES = {k: tuple(v) for k, v in json.loads(os.environ.get('A3C_RAMPES', '{"curts": [4.0, 6.5], "mitjans": [4.0, 6.5], "llargs": [4.0, 6.5]}')).items()}
BANDA = dict(lo=2.0, hi=3.0, lo_pa=None, dt=4.0, tmax=None, porta=[1.0, 4.0], calib=[300.0, 60.0], valida=[[300.0, 360.0], [0.0, 60.0]], nmin=10, tcorr='mesura', tref=40.0); BANDA.update(json.loads(os.environ.get('A3D_BANDA', '{}')))
T_PRES = float(geo['instant_s'])   # 18,43 s: l'instant de la Lluna de presentació (A2_GEOMETRIA)
_sil = np.load(os.environ['A3C_SILUETA']); SIL_PA = np.asarray(_sil['pa'], np.float64); SIL_E = np.asarray(_sil['e'], np.float64)
def classe(e): return 'curts' if e <= 1 / 800 else ('mitjans' if e <= 1 / 50 else 'llargs')
yy, xx = np.mgrid[by0:by1, bx0:bx1]; rL = np.hypot(xx - cx, yy - cy); dL = (rL - R).astype(np.float32)
th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
hb, wb = by1 - by0, bx1 - bx0; nF = len(fr); Rm_ = float(meta['radius_model'])
def dreal(j):
    """Distància al limbe REAL del fotograma j (a3c): cercle exacte del model + silueta comuna e(PA_j)."""
    Dj = np.asarray(Dm[j], np.float64); gy_, gx_ = np.gradient(Dj); iy_, ix_ = hb // 2, wb - 100
    cxj = ix_ + bx0 - (Dj[iy_, ix_] + Rm_) * gx_[iy_, ix_]; cyj = iy_ + by0 - (Dj[iy_, ix_] + Rm_) * gy_[iy_, ix_]
    PAj = (np.degrees(np.arctan2(-(yy - cyj), xx - cxj)) + 360) % 360
    return (Dj + DR - np.interp(PAj.ravel(), SIL_PA, SIL_E, period=360).reshape(hb, wb)).astype(np.float32)
# ---------------- pas 1: règim NET (l'a3c)
Ns = np.zeros((hb, wb, 3), np.float64); Ws = np.zeros((hb, wb, 3), np.float64); NF = np.zeros((hb, wb), np.int16); Wraw = np.zeros((hb, wb), np.float64)
S_classe = {k: np.zeros((hb, wb), np.float32) for k in RAMPES}; DREAL_MAX = np.full((hb, wb), -99.0, np.float32); NCLEAN = np.zeros((hb, wb), np.float32)
Nr = np.zeros((hb, wb, 3), np.float64); Wr = np.zeros((hb, wb, 3), np.float64); NFr = np.zeros((hb, wb), np.int16)   # referència INDEPENDENT per a la T: només tardans (t > tref)
BANDA_J = [j for j in range(nF) if (fr[j]['time'] < BANDA['tmax'] if BANDA['tmax'] is not None else abs(fr[j]['time'] - T_PRES) <= BANDA['dt'])]
# rampa de la banda per angle de posició (Codex, 26-09): lo(PA) interpolat periòdicament d'una taula [[PA, lo], ...]; hi = lo + (hi − lo) del JSON
if BANDA['lo_pa']:
    _tp = np.array(BANDA['lo_pa'], np.float64); _o = np.argsort(_tp[:, 0]); LO_MAP = np.interp(th.ravel(), _tp[_o, 0], _tp[_o, 1], period=360).reshape(hb, wb).astype(np.float32)
else: LO_MAP = np.full((hb, wb), BANDA['lo'], np.float32)
HI_MAP = LO_MAP + (BANDA['hi'] - BANDA['lo'])
for j in range(nF):
    Dr = dreal(j); c_ = classe(fr[j]['exposure']); lo, hi = RAMPES[c_]; s = smoothstep(Dr, lo, hi).astype(np.float32)
    ref = fr[j]['time'] > BANDA['tref']
    for c in range(3):
        w = np.asarray(wt[j, :, :, c], np.float64) * s; n_ = np.asarray(num[j, :, :, c], np.float64) * s; Ns[..., c] += n_; Ws[..., c] += w
        if ref: Nr[..., c] += n_; Wr[..., c] += w
        if c == 1:
            NF += ((w > 0)).astype(np.int16); S_classe[c_] += w.astype(np.float32); Wraw += np.asarray(wt[j, :, :, 1], np.float64)
            if ref: NFr += (w > 0).astype(np.int16)
            DREAL_MAX = np.where(np.asarray(wt[j, :, :, 1]) > 0, np.maximum(DREAL_MAX, Dr), DREAL_MAX); NCLEAN += s * (np.asarray(wt[j, :, :, 1]) > 0)
    if j % 10 == 0: log(f'net · fotograma {j + 1}/{nF}')
E_net = np.where(Ws > 0, Ns / np.maximum(Ws, 1e-30), 0); E_ref = np.where(Wr > 0, Nr / np.maximum(Wr, 1e-30), 0)
curts = [i for i, f in enumerate(fr) if classe(f['exposure']) == 'curts']; _wc = np.asarray(wt[curts[0], ::7, ::7, 1]); W_CURT = float(np.median(_wc[_wc > 0]))
# ---------------- pas 2: T de vora de la banda, mesurada a la dreta contra el règim net
BINS = np.arange(1.0, 8.5, 0.5)
def sector(a0, a1): return ((th >= a0) | (th < a1)) if a0 > a1 else ((th >= a0) & (th < a1))
a0, a1 = BANDA['calib']; sect = sector(a0, a1)
base_ok = (Wr[..., 1] >= 1.5 * W_CURT) & (NFr >= BANDA['nmin']) & (E_ref[..., 1] > 0) & (dL > -5) & (dL < 30)   # veritat = només tardans (independent dels fotogrames ajustats)
veritat = sect & base_ok; VALS = [sector(*v) & base_ok for v in BANDA['valida']]
mostres = {}; mostres_val = [{} for _ in VALS]; NOMC = ['R', 'G', 'B']
if BANDA['tcorr'] == 'mesura':
    for j in BANDA_J:
        Dr = dreal(j); c_ = classe(fr[j]['exposure']); ib = np.floor((Dr - BINS[0]) / 0.5).astype(int); okb = (ib >= 0) & (ib < len(BINS) - 1) & veritat
        for c in range(3):
            w = np.asarray(wt[j, :, :, c]); n = np.asarray(num[j, :, :, c]); ok = okb & (w > 0) & (n > 0) & (E_ref[..., c] > 0)
            q = np.log((n[ok] / w[ok]) / E_ref[..., c][ok]); ibq = ib[ok]
            for k in range(len(BINS) - 1):
                z = ibq == k
                if z.sum() >= 50: mostres.setdefault((c_, c, k), []).append(np.median(q[z]))   # mediana per fotograma i calaix (cap fotograma no pesa més pel nombre de píxels)
            for iv, V in enumerate(VALS):
                okv = (ib >= 0) & (ib < len(BINS) - 1) & V & (w > 0) & (n > 0) & (E_ref[..., c] > 0); qv = np.log((n[okv] / w[okv]) / E_ref[..., c][okv]); ibv = ib[okv]
                for k in range(len(BINS) - 1):
                    z = ibv == k
                    if z.sum() >= 50: mostres_val[iv].setdefault((c_, c, k), []).append(np.median(qv[z]))
    def ajusta(mm, c_, c):
        v = np.array([np.median(mm[(c_, c, k)]) if (c_, c, k) in mm else np.nan for k in range(len(BINS) - 1)]); n_ = np.array([len(mm.get((c_, c, k), [])) for k in range(len(BINS) - 1)])
        if np.isfinite(v).sum() < 4: return None
        lluny = v[(BINS[:-1] >= 6.0)]; off = float(np.nanmedian(lluny)) if np.isfinite(lluny).any() else 0.0
        v2 = v.copy(); v2[BINS[:-1] >= 6.0] = off; ok_ = np.isfinite(v2); v2[~ok_] = np.interp(np.flatnonzero(~ok_), np.flatnonzero(ok_), v2[ok_])
        v2 = np.minimum(v2, off)                                   # el dèficit mai no és un excés respecte de lluny
        for k in range(len(v2) - 2, -1, -1): v2[k] = min(v2[k], v2[k + 1])   # monòtona: més a prop del limbe, més dèficit
        return dict(D=(BINS[:-1] + 0.25).tolist(), lnT=v2.tolist(), offset_lluny=off, n_fotogrames_per_calaix=n_.tolist(), mediana_crua=[None if not np.isfinite(x) else float(x) for x in v])
    LNT = {}; VALIDACIO = {}
    for c_ in RAMPES:
        for c in range(3):
            LNT[(c_, c)] = ajusta(mostres, c_, c)
            # validació creuada (Codex): T ajustada en un sector de validació, provada a l'altre; residu = mediana crua de l'altre − T ajustada (en %)
            fits = [ajusta(mv, c_, c) for mv in mostres_val]; res = {}
            for ia, fa in enumerate(fits):
                for ib_, fb in enumerate(fits):
                    if ia == ib_ or fa is None or fb is None: continue
                    r_ = [None if x is None else round(100 * (np.exp(x - y) - 1), 2) for x, y in zip(fb['mediana_crua'], fa['lnT'])]
                    res[f'ajust {BANDA["valida"][ia]} → prova {BANDA["valida"][ib_]}'] = dict(D=fa['D'], residu_pct=r_, max_abs_2_6=max((abs(x) for x, D in zip(r_, fa['D']) if x is not None and 2.0 <= D < 6.0), default=None))
            VALIDACIO[f'{c_}/{NOMC[c]}'] = res
    def lnT(c_, c, D):
        t_ = LNT.get((c_, c))
        if t_ is None: return np.zeros_like(D)
        return np.interp(D, t_['D'], t_['lnT'], left=t_['lnT'][0], right=t_['offset_lluny'])
    # validació post-matriu (Codex, ronda 2): per a cada parell de sectors (ajust A → prova B), cada fotograma de la banda dividit per la T
    # ajustada a A (per classe i canal), passat per la matriu i comparat amb E_ref post-matriu a B; residu de G' i de L' per calaix de D_real,
    # per fotograma (mediana) i ponderat pel pes efectiu del fotograma a la banda (pes LDIC mitjà a 2–4 px)
    Mx_ = np.array(meta['matrix'], np.float64); gn_ = np.array(meta['gain'], np.float64)
    def postm(E3): return np.einsum('ij,...j->...i', Mx_, E3 * gn_)
    Eref_pm = postm(E_ref); Gref = Eref_pm[..., 1]; Lref = (Eref_pm[..., 0] + 2 * Eref_pm[..., 1] + Eref_pm[..., 2]) / 4
    fits_by_sector = [{(c_, c): ajusta(mv, c_, c) for c_ in RAMPES for c in range(3)} for mv in mostres_val]
    POSTM = {}
    for ia in range(len(VALS)):
        for ib_ in range(len(VALS)):
            if ia == ib_: continue
            per_frame = {}; pes_frame = {}
            for j in BANDA_J:
                Dr = dreal(j); c_ = classe(fr[j]['exposure']); ib = np.floor((Dr - BINS[0]) / 0.5).astype(int)
                w3 = np.stack([np.asarray(wt[j, :, :, c], np.float64) for c in range(3)], -1); n3 = np.stack([np.asarray(num[j, :, :, c], np.float64) for c in range(3)], -1)
                okv = (ib >= 0) & (ib < len(BINS) - 1) & VALS[ib_] & (w3 > 0).all(-1) & (n3 > 0).all(-1) & (Gref > 0)
                Ej = np.zeros_like(n3); Ej[okv] = n3[okv] / w3[okv]
                for c in range(3):
                    f_ = fits_by_sector[ia].get((c_, c))
                    if f_ is not None: Ej[..., c] = np.where(okv, Ej[..., c] / np.exp(np.interp(Dr, f_['D'], f_['lnT'], left=f_['lnT'][0], right=f_['offset_lluny'])), Ej[..., c])
                Ep = postm(Ej); Gj = Ep[..., 1]; Lj = (Ep[..., 0] + 2 * Ep[..., 1] + Ep[..., 2]) / 4
                okg = okv & (Gj > 0) & (Lj > 0) & (Lref > 0); qg = np.log(Gj[okg] / Gref[okg]); ql = np.log(Lj[okg] / Lref[okg]); ibq = ib[okg]
                rg = []; rl = []
                for k in range(len(BINS) - 1):
                    z = ibq == k; rg.append(float(np.median(qg[z])) if z.sum() >= 50 else np.nan); rl.append(float(np.median(ql[z])) if z.sum() >= 50 else np.nan)
                per_frame[fr[j]['name']] = dict(classe=c_, Gp=rg, Lp=rl)
                wz = np.asarray(wt[j, :, :, 1])[VALS[ib_] & (Dr >= 2) & (Dr < 4)]; pes_frame[fr[j]['name']] = float(np.median(wz[wz > 0])) if (wz > 0).any() else 0.0
            wsum = sum(pes_frame.values()) or 1.0
            def agreg(key):
                out = []
                for k in range(len(BINS) - 1):
                    vals = [(per_frame[n][key][k], pes_frame[n]) for n in per_frame if np.isfinite(per_frame[n][key][k])]
                    out.append(None if not vals else round(100 * (np.exp(sum(v * w for v, w in vals) / max(sum(w for _, w in vals), 1e-30)) - 1), 2))
                return out
            POSTM[f'ajust {BANDA["valida"][ia]} → prova {BANDA["valida"][ib_]}'] = dict(D=(BINS[:-1] + 0.25).tolist(), Gp_ponderat_pct=agreg('Gp'), Lp_ponderat_pct=agreg('Lp'),
                per_fotograma={n: dict(classe=v['classe'], pes_relatiu=round(pes_frame[n] / wsum, 3), Gp_pct=[None if not np.isfinite(x) else round(100 * (np.exp(x) - 1), 2) for x in v['Gp']]) for n, v in per_frame.items()})
    VALIDACIO['post_matriu'] = POSTM
    for k_, v_ in POSTM.items(): log(f'VALIDACIO POST-MATRIU {k_}: G\' ' + ' '.join(f"{D:.2f}:{x}" for D, x in zip(v_['D'][2:12], v_['Gp_ponderat_pct'][2:12])) + ' · L\' ' + ' '.join(f"{D:.2f}:{x}" for D, x in zip(v_['D'][2:12], v_['Lp_ponderat_pct'][2:12])))
    log('T mesurada: ' + json.dumps({f'{c_}/{NOMC[c]}': ([round(100 * (np.exp(x) - 1), 1) for x in LNT[(c_, c)]['lnT'][:8]] if LNT.get((c_, c)) else None) for c_ in RAMPES for c in range(3)}))
else:
    LNT = {}; VALIDACIO = {}
    def lnT(c_, c, D): return np.zeros_like(D)
# ---------------- pas 3: règim de BANDA
Nb = np.zeros((hb, wb, 3), np.float64); Wb = np.zeros((hb, wb, 3), np.float64); NFb = np.zeros((hb, wb), np.int16); DREAL_MAX_B = np.full((hb, wb), -99.0, np.float32); W2b = np.zeros((hb, wb), np.float64)
for j in BANDA_J:
    Dr = dreal(j); c_ = classe(fr[j]['exposure']); lo, hi = RAMPES[c_]; s_net = smoothstep(Dr, lo, hi); sb = (smoothstep(Dr, LO_MAP, HI_MAP) * (1 - s_net)).astype(np.float32)
    for c in range(3):
        T_ = np.exp(lnT(c_, c, Dr)).astype(np.float64); T_ = np.where(sb > 0, T_, 1.0)
        w = np.asarray(wt[j, :, :, c], np.float64) * sb * T_ ** 2; Nb[..., c] += np.asarray(num[j, :, :, c], np.float64) * sb * T_; Wb[..., c] += w
        if c == 1: NFb += ((w > 0) & (s_net <= 0)).astype(np.int16); DREAL_MAX_B = np.where(w > 0, np.maximum(DREAL_MAX_B, Dr), DREAL_MAX_B); W2b += w * w
E_banda = np.where(Wb > 0, Nb / np.maximum(Wb, 1e-30), 0); W_NET_G = Ws[..., 1].astype(np.float32).copy()   # el pes del règim net, abans de combinar
G_ = (1 - smoothstep(NCLEAN, BANDA['porta'][0], BANDA['porta'][1])).astype(np.float32); NEFF_B = np.where(W2b > 0, Wb[..., 1] ** 2 / np.maximum(W2b, 1e-300), 0).astype(np.float32)
Ns = Ns + G_[..., None] * Nb; Ws = Ws + G_[..., None] * Wb; NF = (NF + NFb * (G_ > 0)).astype(np.int16); DREAL_MAX = np.where(G_ > 0, np.maximum(DREAL_MAX, DREAL_MAX_B), DREAL_MAX)
E = np.where(Ws > 0, Ns / np.maximum(Ws, 1e-30), 0).astype(np.float32)
# ---------------- d'aquí endavant, l'a3c tal qual
omplerts = {}; te_canal = [Ws[..., c] > 0 for c in range(3)]
for c in (0, 2):     # desmosaic: només els píxels on aquest canal no té cap pes i el verd sí
    buit = (Ws[..., c] <= 0) & (Ws[..., 1] > 0); omplerts[c] = int(buit.sum())
    if buit.any():
        Nc = cv2.GaussianBlur(Ns[..., c].astype(np.float32), (0, 0), 0.8); Wc = cv2.GaussianBlur(Ws[..., c].astype(np.float32), (0, 0), 0.8)
        E[..., c] = np.where(buit & (Wc > 0), Nc / np.maximum(Wc, 1e-30), E[..., c]); te_canal[c] = te_canal[c] | (buit & (Wc > 0))
Mx = np.array(meta['matrix'], np.float32); gn = np.array(meta['gain'], np.float32); E = np.einsum('ij,...j->...i', Mx, E * gn).astype(np.float32)
valid = (Ws[..., 1] >= 1.5 * W_CURT) & (NF >= 3) & (E[..., 1] > 0) & te_canal[0] & te_canal[2]
NBZ = 1440; ibz = (th / 360 * NBZ).astype(int) % NBZ; zona = (dL > -40) & (dL < 20)
ordre = np.argsort(ibz[zona]); ib_s = ibz[zona][ordre]; d_s = dL[zona][ordre]; v_s = valid[zona][ordre]; talls = np.searchsorted(ib_s, np.arange(NBZ + 1)); dmin = np.full(NBZ, np.nan)
for k in range(NBZ):
    dd_, vv_ = d_s[talls[k]:talls[k + 1]], v_s[talls[k]:talls[k + 1]]; dolents = dd_[~vv_]
    dmin[k] = (dolents.max() + 0.25) if dolents.size else (dd_.min() if dd_.size else np.nan)
ok_ = np.isfinite(dmin); dmin[~ok_] = np.interp(np.flatnonzero(~ok_), np.flatnonzero(ok_), dmin[ok_], period=NBZ)
DMIN = gaussian_filter1d(maximum_filter1d(dmin, 5, mode='wrap'), 4, mode='wrap'); DMIN = np.maximum(DMIN, maximum_filter1d(dmin, 3, mode='wrap')).astype(np.float32)
llisa = dL >= DMIN[ibz]
forats = int((llisa & ~valid & (dL < 20)).sum())
domini_E = llisa & valid & (dL >= 0)
fonts = dict(G=np.load(FONTS / 'base_G.npy', mmap_mode='r'), F=np.load(FONTS / 'fusion_starless.npy', mmap_mode='r'), V=np.load(FONTS / 'vixen_starless.npy', mmap_mode='r'))
sup = np.load(FONTS / 'support.npy')[by0:by1, bx0:bx1]
D1_, D2_ = 60.0, 90.0
beta = ((1 - smoothstep(dL, D1_, D2_)) * domini_E).astype(np.float32)
anell = domini_E & sup & (dL >= D1_) & (dL <= 120)
def cte(font, e):
    ok = anell & (font > 0) & (e > 0); q = font[ok] / e[ok]; return float(np.median(q)), float(np.percentile(q, 16)), float(np.percentile(q, 84))
out = {}; esc = {}
Gb = np.asarray(fonts['G'][by0:by1, bx0:bx1]).astype(np.float32); cG = cte(Gb, E[..., 1]); esc['c_G'] = cG
out['G'] = np.where(beta > 0, (1 - beta) * Gb + beta * cG[0] * E[..., 1], Gb).astype(np.float32)
Fb = np.asarray(fonts['F'][by0:by1, bx0:bx1]).astype(np.float32); Fn = Fb.copy()
for c in range(3):
    cc = cte(Fb[..., c], E[..., c]); esc[f'c_F{c}'] = cc; Fn[..., c] = np.where(beta > 0, (1 - beta) * Fb[..., c] + beta * cc[0] * E[..., c], Fb[..., c])
out['F'] = Fn
Vb = np.asarray(fonts['V'][by0:by1, bx0:bx1, 1]).astype(np.float32); cV = cte(Vb, E[..., 1]); esc['c_V'] = cV
out['V'] = np.where(beta > 0, (1 - beta) * Vb + beta * cV[0] * E[..., 1], Vb).astype(np.float32)
domini = np.where(dL < D2_, domini_E, sup & (rL > R))
dins_franja = beta > 0
chk = {}
for d0, d1 in [(-10, 0), (0, 3), (3, 6), (6, 10), (10, 20), (20, 40), (40, 60), (60, 90), (90, 120)]:
    s_ = domini_E & (dL >= d0) & (dL < d1)
    chk[f'{d0}..{d1}'] = dict(px=int(s_.sum()), fotogrames_p50=float(np.median(NF[s_])) if s_.any() else None, px_banda_g50=int((s_ & (G_ > 0.5)).sum()),
                               ln_fusio_sobre_nova_p16_50_84=(np.percentile(np.log(Gb[s_ & (Gb > 0)] / (cG[0] * E[..., 1][s_ & (Gb > 0)])), [16, 50, 84]).round(4).tolist() if (s_ & (Gb > 0)).sum() > 100 else None))
dmin_az = {f'{a}': round(float(DMIN[int(a / 360 * NBZ)]), 2) for a in range(0, 360, 15)}
np.savez_compressed(SORT / 'A3C_franja_silueta.npz', DREAL_MAX=DREAL_MAX, box=np.array([by0, by1, bx0, bx1]), G=out['G'], F=out['F'], V=out['V'], domini=domini, dins_franja=dins_franja,
                    beta=beta, E=E, NF=NF, DMIN=DMIN, centre=np.array([cx, cy, R]), domini_E=domini_E, porta_banda=G_, NCLEAN=NCLEAN, NF_banda=NFb, NEFF_banda=NEFF_B, LO_MAP=LO_MAP, E_banda=np.einsum('ij,...j->...i', Mx, E_banda.astype(np.float32) * gn).astype(np.float32), W_banda=Wb[..., 1].astype(np.float32), W_net=W_NET_G, E_net=np.einsum('ij,...j->...i', Mx, E_net.astype(np.float32) * gn).astype(np.float32))
rep = dict(script='a3d_franja_banda.py (V103)', silueta=os.environ['A3C_SILUETA'], limb_frames=str(LF.relative_to(ARREL)), fonts=str(FONTS.relative_to(ARREL)) if str(FONTS).startswith(str(ARREL)) else str(FONTS),
           rampes_net_D_real_px=RAMPES, banda=BANDA, fotogrames_banda=[dict(nom=fr[j]['name'], t=fr[j]['time'], exp=fr[j]['exposure']) for j in BANDA_J],
           T_banda={f'{c_}/{NOMC[c]}': LNT.get((c_, c)) for c_ in RAMPES for c in range(3)} if LNT else 'cap (banda tal com es veu)', T_validacio_creuada=VALIDACIO,
           instant_presentacio_s=T_PRES, n_efectius_banda=dict(p16_50_84_on_g50=np.percentile(NEFF_B[(G_ > 0.5) & (NFb > 0)], [16, 50, 84]).round(2).tolist() if ((G_ > 0.5) & (NFb > 0)).any() else None),
           DR_px=DR, W_CURT=W_CURT, desmosaic_px_omplerts={'R': omplerts[0], 'B': omplerts[2]}, unio_fusio_px=[D1_, D2_], escales=esc,
           vora_domini=dict(azimuts=NBZ, DMIN_per_azimut=dmin_az, p5_p50_p95=np.percentile(DMIN, [5, 50, 95]).round(2).tolist(), forats_dins_la_corba=forats),
           px_regim_banda_g50=int((G_ > 0.5).sum()), px_regim_banda_g50_amb_dada=int(((G_ > 0.5) & domini_E).sum()), per_distancia=chk, domini_caixa=int(domini.sum()))
desa_json('A3C_FRANJA_SILUETA.json', rep); desa_json('A3D_FRANJA_BANDA.json', rep); log('A3D fet · DMIN ' + json.dumps(dmin_az) + ' · c_G ' + json.dumps(cG))
