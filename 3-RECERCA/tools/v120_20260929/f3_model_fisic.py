"""f3 (V120, 29-09-2026) · MODEL FÍSIC DE LA DISTORSIÓ: la Sony (A i B) cap a la geometria de la Vixen.
Pere: «La distorsió òptica importa». La distorsió d'un objectiu és RADIAL al voltant del seu EIX ÒPTIC. Al llenç:
  · Sony A: l'eix és on hi ha la taca del reflex de l'eix, a 2,97 R☉ del Sol (el Sol era descentrat al primer apuntament);
  · Sony B: després de la relliscada de muntura (−233, +713) px al sensor, l'eix queda a ~0,4 R☉ del Sol;
  · Vixen: el centre del sensor (6960 × 4640), a ~0,6 R☉ del Sol.
Els centres es calculen amb la geometria de la cadena (f1: Sol al sensor per fotograma, escala i angle de posició de cada tren, i la matriu del
llenç comú al final) i es COMPROVEN: el de l'A ha de caure a la taca del reflex (2825, 3988 al llenç comú).
Model per a u_X = posició a V − posició a X (X = A, B), en px del llenç final:
  u_X(x) = afí_X(x)                                      (6 paràmetres per apuntament: escala, gir, cisalla i translació que el registre no va encertar)
         + k3S·D3(x; P_X) + k5S·D5(x; P_X)               (l'objectiu de 300 mm: els MATEIXOS coeficients per a A i B, centrats a l'eix de cadascú)
         + k3V·D3(x; P_V) + k5V·D5(x; P_V)               (la Vixen, centrada al seu eix; els mateixos per a A i B)
  amb D3(x; P) = |d|²·d·N i D5 = |d|⁴·d·N, d = (x − P)/N, N = 2000 px. Ajust CONJUNT d'A i B (16 paràmetres) amb les mesures del f1/f2.
Comparació amb el millor genèric del f2 (afí per separat). Validació: sectors de 30° fora i estrelles fora.
Ús: f3_model_fisic.py <carpeta_f1> → F3_MODEL.json (el que farà servir el warp) i F3_REBUT.json"""
import sys, json, time, numpy as np
from pathlib import Path
F1 = Path(sys.argv[1]).resolve(); R = Path(__file__).resolve().parents[3]; t0 = time.time()
SOL = (5361.768111973117, 3775.747534140857); RS = 440.603; NRM = 2000.0
def log(*a): print(f'[{time.time() - t0:5.0f}s]', *a, flush=True)
RUNS = R / '2-ARXIU/reconstruccio_compactacio_20260915/neteja_20260916/eclipse_determinista_docs/1-RUNS'
SONY = json.load(open(RUNS / '016_SONYTOT_CIENCIA_20260827T183356Z/4-rebuts/F1.2_sol_llenc.json'))
VIX = json.load(open(RUNS / '019_VIXEN_CIENCIA_20260827T212404Z/4-rebuts/F1.2_sol_llenc.json'))
M = np.asarray(json.load(open(R / '2-ARXIU/reconstruccio_compactacio_20260915/raw_replay/v36_rgb_dependencies/geometry.json'))['M_llenc_a_v23'], np.float64)
Wc, Hc = SONY['llenc']['W'], SONY['llenc']['H']; SUNc = np.array([Wc / 2, Hc / 2])
def sol_sensor(model, t):
    seg = next(s for s in model['model_sol']['segments'] if s['t0'] - 1 <= t <= s['t1'] + 1)
    return np.array([np.polyval(seg['px'], t), np.polyval(seg['py'], t)])
def a_llenc(p_sensor, sun_sensor, escala_sensor, pa):
    """sensor → llenç comú (Sol al centre, nord amunt) → llenç final (M)."""
    s = escala_sensor / SONY['llenc']['escala_arcsec_px']; phi = np.radians(-pa); Rm = np.array([[np.cos(phi), -np.sin(phi)], [np.sin(phi), np.cos(phi)]])
    c = SUNc + s * Rm @ (np.asarray(p_sensor, float) - sun_sensor); return M @ np.array([c[0], c[1], 1.0]), c
GHOST_S = np.array([4000.0, 2660.0])                    # la taca del reflex de l'eix al sensor de la Sony (memòria ghost-de-leix-optic-sony)
tA = [f['t'] for f in SONY['fotogrames'].values() if f.get('coronal') and f['t'] <= 30]; tB = [f['t'] for f in SONY['fotogrames'].values() if f.get('coronal') and f['t'] >= 60]
tA = np.median(tA) if tA else 15.0; tB = np.median(tB) if tB else 83.0
PA, PAc = a_llenc(GHOST_S, sol_sensor(SONY, tA), SONY['llenc']['escala_sensor_arcsec_px'], SONY['llenc']['pa_north_deg'])
PB, PBc = a_llenc(GHOST_S, sol_sensor(SONY, tB), SONY['llenc']['escala_sensor_arcsec_px'], SONY['llenc']['pa_north_deg'])
tV = np.median([f['t'] for f in VIX['fotogrames'].values() if f.get('coronal')])
PV, PVc = a_llenc(np.array([6960 / 2, 4640 / 2]), sol_sensor(VIX, tV), VIX['llenc']['escala_sensor_arcsec_px'], VIX['llenc']['pa_north_deg'])
geo = dict(PA=PA.tolist(), PB=PB.tolist(), PV=PV.tolist(), PA_llenc_comu=PAc.tolist(), comprovacio_ghost_llenc_comu='(2825, 3988)',
           dist_Rsol=dict(A=float(np.hypot(*(PA - SOL)) / RS), B=float(np.hypot(*(PB - SOL)) / RS), V=float(np.hypot(*(PV - SOL)) / RS)), t_mitja=dict(A=float(tA), B=float(tB), V=float(tV)))
log('centres òptics', json.dumps(geo, ensure_ascii=False))
assert np.hypot(PAc[0] - 2825, PAc[1] - 3988) < 5, 'el centre de l\'A no cau a la taca del reflex: la geometria no quadra'
# ---------------------------------------------------------------- mesures (f1 + estrelles del f2)
Z = np.load(F1 / 'F1_MESURES.npz'); MES = {}
for k in Z.files:
    a, b = k.split('__'); MES.setdefault(a, {})[b] = Z[k]
EST = json.load(open(F1 / 'F2_ESTRELLES.json'))
def xy_de(r_px, th): return SOL[0] + r_px * np.cos(th), SOL[1] - r_px * np.sin(th)
def D3(x, y, P): dx, dy = (x - P[0]) / NRM, (y - P[1]) / NRM; q = dx * dx + dy * dy; return q * dx * NRM, q * dy * NRM
def D5(x, y, P): dx, dy = (x - P[0]) / NRM, (y - P[1]) / NRM; q = (dx * dx + dy * dy) ** 2; return q * dx * NRM, q * dy * NRM
PARAMS = ['A_x0', 'A_xx', 'A_xy', 'A_y0', 'A_yx', 'A_yy', 'B_x0', 'B_xx', 'B_xy', 'B_y0', 'B_yx', 'B_yy', 'k3S', 'k5S', 'k3V', 'k5V']
def files(X, x, y, ex, ey, fisic=True):
    """la component (ex, ey) del model per a mesures d'X a (x, y)."""
    n = len(x); Mx = np.zeros((n, len(PARAMS))); X_, Y_ = (x - SOL[0]) / NRM, (y - SOL[1]) / NRM; o = 0 if X == 'A' else 6
    Mx[:, o + 0] = ex; Mx[:, o + 1] = ex * X_; Mx[:, o + 2] = ex * Y_; Mx[:, o + 3] = ey; Mx[:, o + 4] = ey * X_; Mx[:, o + 5] = ey * Y_
    if fisic:
        P = PA if X == 'A' else PB
        a, b = D3(x, y, P); Mx[:, 12] = ex * a + ey * b; a, b = D5(x, y, P); Mx[:, 13] = ex * a + ey * b
        a, b = D3(x, y, PV); Mx[:, 14] = ex * a + ey * b; a, b = D5(x, y, PV); Mx[:, 15] = ex * a + ey * b
    return Mx
def sistema(fisic=True, amb_estrelles=True):
    rows, obs, sig, sec, tip, qui = [], [], [], [], [], []
    for X in ('A', 'B'):
        a, r_ = MES[f'ang_{X}'], MES[f'rad_{X}']; kr = (r_['r'] < 2.5 * RS) & (r_['c'] >= 0.8)
        x, y = xy_de(a['r'], a['th']); et = (-np.sin(a['th']), -np.cos(a['th']))
        rows.append(files(X, x, y, et[0], et[1], fisic)); obs.append(a['r'] * a['dtheta']); sig.append(np.clip(0.3 * (1 - a['c']) / 0.1, 0.1, 1.5) * np.maximum(a['r'] / (2 * RS), 1))
        sec.append(np.floor(np.degrees(a['th']) % 360 / 30).astype(int)); tip.append(np.zeros(len(x), int)); qui.append(np.full(len(x), X))
        x, y = xy_de(r_['r'][kr], r_['th'][kr]); er = (np.cos(r_['th'][kr]), -np.sin(r_['th'][kr]))
        rows.append(files(X, x, y, er[0], er[1], fisic)); obs.append(r_['r'][kr] * r_['drho'][kr]); sig.append(np.full(kr.sum(), 1.0))
        sec.append(np.floor(np.degrees(r_['th'][kr]) % 360 / 30).astype(int)); tip.append(np.ones(kr.sum(), int)); qui.append(np.full(kr.sum(), X))
        if amb_estrelles and EST[X]:
            ex_ = np.array([e['x'] for e in EST[X]]); ey_ = np.array([e['y'] for e in EST[X]]); th_e = np.arctan2(-(ey_ - SOL[1]), ex_ - SOL[0])
            for comp, obsv in ((0, np.array([e['ux'] for e in EST[X]])), (1, np.array([e['uy'] for e in EST[X]]))):
                one = np.ones(len(ex_)); zero = np.zeros(len(ex_))
                rows.append(files(X, ex_, ey_, one if comp == 0 else zero, zero if comp == 0 else one, fisic)); obs.append(obsv)
                sig.append(np.array([max(0.35, 3.0 / e['sn_V']) for e in EST[X]])); sec.append(np.floor(np.degrees(th_e) % 360 / 30).astype(int)); tip.append(np.full(len(ex_), 2)); qui.append(np.full(len(ex_), X))
    return np.vstack(rows), np.concatenate(obs), np.concatenate(sig), np.concatenate(sec), np.concatenate(tip), np.concatenate(qui)
def ajusta(Am, b, s, k, fisic):
    cols = np.arange(len(PARAMS)) if fisic else np.arange(12); A_ = Am[:, cols]; w = 1 / s
    p = np.linalg.lstsq(A_[k] * w[k, None], b[k] * w[k], rcond=None)[0]
    for _ in range(4):
        res = (A_ @ p - b) * w; kk = k & (np.abs(res) < 4 * 1.4826 * np.median(np.abs(res[k])) + 1e-9); p = np.linalg.lstsq(A_[kk] * w[kk, None], b[kk] * w[kk], rcond=None)[0]
    full = np.zeros(len(PARAMS)); full[cols] = p; return full
rep = dict(guio=str(Path(__file__).relative_to(R)), geometria=geo, comparacio={}, residus={})
for nom, fisic in (('afi_per_separat', False), ('fisic', True)):
    Am, b, s, sec, tip, qui = sistema(fisic); errs = []
    for fold in range(3):
        tr = (sec % 3) != fold; p = ajusta(Am, b, s, tr, fisic); te = ~tr; errs.append(float(np.median(np.abs(Am[te] @ p - b[te]))))
    kno = tip != 2; p = ajusta(Am, b, s, kno, fisic); ke = tip == 2
    est_sense = {X: float(np.sqrt(np.mean(np.sum(((Am[ke & (qui == X)] @ p) - b[ke & (qui == X)]).reshape(2, -1) ** 2, 0)))) for X in ('A', 'B')}
    p = ajusta(Am, b, s, np.ones(len(b), bool), fisic); r_obs = b - Am @ p
    tb = {}
    for X in ('A', 'B'):
        a = MES[f'ang_{X}']; k0 = (qui == X) & (tip == 0); ra = r_obs[k0]; t_ = {}
        for lo, hi in ((1.3, 2), (2, 3), (3, 4.5), (4.5, 6), (6, 8)):
            k = (a['r'] >= lo * RS) & (a['r'] < hi * RS); meds = []
            for sct in range(12):
                kk = k & (np.floor(np.degrees(a['th']) % 360 / 30) == sct)
                if kk.sum() >= 15: meds.append(np.median(ra[kk]))
            t_[f'{lo}-{hi}'] = [round(float(np.median(np.abs(meds))), 2), round(float(np.max(np.abs(meds))), 2)] if meds else None
        ke_ = (qui == X) & (tip == 2)
        if ke_.any(): d = r_obs[ke_].reshape(2, -1); t_['estrelles_rms_max'] = [round(float(np.sqrt(np.mean(np.sum(d ** 2, 0)))), 2), round(float(np.sqrt(np.sum(d ** 2, 0)).max()), 2)]
        tb[X] = t_
    rep['comparacio'][nom] = dict(error_mediana_px_sectors_fora=round(float(np.mean(errs)), 3), rms_estrelles_px_sense_estrelles={X: round(v, 2) for X, v in est_sense.items()},
                                  parametres={PARAMS[i]: round(float(p[i]), 5) for i in range(len(PARAMS))}, residus_sistematics=tb)
    log(nom, json.dumps(rep['comparacio'][nom], ensure_ascii=False)[:1500])
triat = 'fisic' if (rep['comparacio']['fisic']['error_mediana_px_sectors_fora'] <= rep['comparacio']['afi_per_separat']['error_mediana_px_sectors_fora'] * 1.02
                    and max(rep['comparacio']['fisic']['rms_estrelles_px_sense_estrelles'].values()) <= 3.0) else 'afi_per_separat'
rep['triat'] = triat; pp = rep['comparacio'][triat]['parametres']
model = dict(conveni='u = posició a V − posició a X (px del llenç final, x cap a la dreta, y cap avall); X\'(q) = X(q − u(q))', SOL=list(SOL), RS=RS, N=NRM, triat=triat,
             centres=dict(A=PA.tolist(), B=PB.tolist(), V=PV.tolist()), parametres=pp, formula='u_x = X_x0 + X_xx·Xn + X_xy·Yn + [k3S·D3x(P_X) + k5S·D5x(P_X) + k3V·D3x(P_V) + k5V·D5x(P_V)]; u_y anàleg; Xn = (x − SOL_x)/N, Yn = (y − SOL_y)/N')
json.dump(model, open(F1 / 'F3_MODEL.json', 'w'), ensure_ascii=False, indent=1)
# el camp a radis clau
def camp(X, x, y):
    X_, Y_ = (x - SOL[0]) / NRM, (y - SOL[1]) / NRM; o = X
    ux = pp[f'{o}_x0'] + pp[f'{o}_xx'] * X_ + pp[f'{o}_xy'] * Y_; uy = pp[f'{o}_y0'] + pp[f'{o}_yx'] * X_ + pp[f'{o}_yy'] * Y_
    P = PA if X == 'A' else PB
    for kname, fn, PP in (('k3S', D3, P), ('k5S', D5, P), ('k3V', D3, PV), ('k5V', D5, PV)):
        a, b = fn(x, y, PP); ux += pp[kname] * a; uy += pp[kname] * b
    return ux, uy
th = np.linspace(0, 2 * np.pi, 360, endpoint=False); mag = {}
for X in ('A', 'B'):
    mag[X] = {}
    for rR in (1.0, 1.1, 1.5, 2, 3, 4, 6, 8, 12):
        ux, uy = camp(X, SOL[0] + rR * RS * np.cos(th), SOL[1] - rR * RS * np.sin(th)); m_ = np.hypot(ux, uy); mag[X][str(rR)] = [round(float(np.median(m_)), 2), round(float(m_.max()), 2)]
rep['modul_camp_px_mediana_max_per_radi'] = mag; log('triat', triat, 'camp', json.dumps(mag, ensure_ascii=False))
rep['segons'] = round(time.time() - t0, 1); json.dump(rep, open(F1 / 'F3_REBUT.json', 'w'), ensure_ascii=False, indent=1)
