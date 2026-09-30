"""f4c (V120, 29-09-2026): el f4 amb l'AFÍ FIXAT NOMÉS PER LES ESTRELLES (a S/N ≥ 6, soles, quadren amb un afí a 0,7–1,6 px) i la correcció NOMÉS
TANGENCIAL ajustada als residus dels raigs (1,3–6 R☉, esvaïda de 5 a 7 R☉). Per què: al f4 (afí de raigs + estrelles), raigs i estrelles s'estiraven
l'un a l'altre i les estrelles quedaven a 2–2,5 px; el f4b (tot conjunt, amb correcció radial) era degenerat (el camp es disparava fora del rang).
f4 (V120, 29-09-2026) · EL MODEL DEL CAMP SONY → VIXEN QUE FA SERVIR EL WARP (i la seva validació).
Què van dir el f2 i el f3:
  · un afí per apuntament és el que millor prediu les estrelles sense haver-les vist (2,3–2,6 px); els polinomis més alts i els polars
    s'escapen en radi, i el model físic de distorsió radial (centres òptics comprovats) també (26–33 px sense estrelles): les dades
    no en separen els termes;
  · els raigs (5.300 finestres per apuntament) demanen una mica més de flexibilitat EN ANGLE a la zona on la fusió barreja la Vixen i la Sony.
Model: u_X(x) = afí_X(x) + τ(r) · r · δθ_X(ρ, θ) · e_t
  · afí_X: ajustat amb TOTES les mesures (raigs, arcs fiables a r < 2,5 R☉ amb c ≥ 0,8, i estrelles amb S/N ≥ 6), robust;
  · δθ_X: correcció NOMÉS tangencial, harmònics k ≤ 2 × Legendre j ≤ 1 en ρ = ln r normalitzat a [1,3; 6] R☉, ajustada als residus dels
    raigs de 1,3 a 6 R☉; fora d'aquest tram ρ es limita a l'extrem;
  · τ(r) = 1 fins a 5 R☉ i baixa suaument a 0 a 7 R☉: més enllà no hi ha raigs mesurats i la fusió ja és gairebé tota Sony (pes de la Vixen
    0,36 a 6 R☉, 0,07 a 8 R☉); allà mana l'afí, que les estrelles fixen.
Validació (porta de la regla 9): residus SISTEMÀTICS (mediana per caselles de 30° × tram de radi) dels raigs i dels arcs, i estrelles; validació
creuada deixant fora sectors de 30° (un de cada 3) per a tot el procediment (afí + correcció).
Ús: f4_model_final.py <carpeta_f1> → F4_MODEL.json, F4_REBUT.json; i, com a mòdul, camp(model, X, x, y) → (u_x, u_y)"""
import sys, json, time, numpy as np
from pathlib import Path
from numpy.polynomial import legendre as LG
import os
SOL = (5361.768111973117, 3775.747534140857); RS = 440.603; NRM = 2000.0; KT, JT = int(os.environ.get('F4_KT', 2)), int(os.environ.get('F4_JT', 1)); R0, R1 = 1.3, float(os.environ.get('F4_R1', 6.0)); TAU = (float(os.environ.get('F4_T0', 5.0)), float(os.environ.get('F4_T1', 7.0)))
def rho_n(r_px): return np.clip((np.log(np.clip(r_px / RS, R0, R1)) - np.log(R0)) / (np.log(R1) - np.log(R0)) * 2 - 1, -1, 1)
def base_t(r_px, th, K=None, J=None):
    K = KT if K is None else K; J = JT if J is None else J
    P = np.stack([LG.legval(rho_n(r_px), np.eye(J + 1)[j]) for j in range(J + 1)], 1); cols = []
    for k in range(K + 1):
        for j in range(J + 1):
            cols.append(np.cos(k * th) * P[:, j])
            if k > 0: cols.append(np.sin(k * th) * P[:, j])
    return np.stack(cols, 1)
def tau(r_px):
    t = np.clip((r_px / RS - TAU[0]) / (TAU[1] - TAU[0]), 0, 1); return 1 - t * t * (3 - 2 * t)
def camp(model, X, x, y):
    """u = posició a V − posició a X (px), per a punts (x, y) del llenç final (arrays de qualsevol forma)."""
    m = model['models'][X]; x = np.asarray(x, np.float64); y = np.asarray(y, np.float64)
    X_, Y_ = (x - SOL[0]) / NRM, (y - SOL[1]) / NRM
    ux = m['afi'][0] + m['afi'][1] * X_ + m['afi'][2] * Y_; uy = m['afi'][3] + m['afi'][4] * X_ + m['afi'][5] * Y_
    dx, dy = x - SOL[0], -(y - SOL[1]); r = np.hypot(dx, dy); th = np.arctan2(dy, dx)
    dth = (base_t(r.ravel(), th.ravel(), model.get('KT', KT), model.get('JT', JT)) @ np.asarray(m['dtheta'])).reshape(r.shape) * tau(r)
    ut = r * dth; ux = ux + ut * (-np.sin(th)); uy = uy + ut * (-np.cos(th))      # e_t en px amb y cap avall
    return ux, uy
if __name__ == '__main__':
    F1 = Path(sys.argv[1]).resolve(); R = Path(__file__).resolve().parents[3]; t0 = time.time()
    def log(*a): print(f'[{time.time() - t0:5.0f}s]', *a, flush=True)
    Z = np.load(F1 / 'F1_MESURES.npz'); MES = {}
    for k in Z.files:
        a, b = k.split('__'); MES.setdefault(a, {})[b] = Z[k]
    EST = json.load(open(F1 / 'F2_ESTRELLES.json'))
    def xy_de(r_px, th): return SOL[0] + r_px * np.cos(th), SOL[1] - r_px * np.sin(th)
    def afi_files(x, y, ex, ey):
        X_, Y_ = (x - SOL[0]) / NRM, (y - SOL[1]) / NRM; return np.stack([ex, ex * X_, ex * Y_, ey, ey * X_, ey * Y_], 1)
    def dades(X):
        a, r_ = MES[f'ang_{X}'], MES[f'rad_{X}']; kr = (r_['r'] < 2.5 * RS) & (r_['c'] >= 0.8); D = {}
        x, y = xy_de(a['r'], a['th']); et = (-np.sin(a['th']), -np.cos(a['th']))
        D['ang'] = dict(Af=afi_files(x, y, et[0], et[1]), obs=a['r'] * a['dtheta'], sig=np.clip(0.3 * (1 - a['c']) / 0.1, 0.1, 1.5) * np.maximum(a['r'] / (2 * RS), 1),
                        r=a['r'], th=a['th'], sec=np.floor(np.degrees(a['th']) % 360 / 30).astype(int))
        x, y = xy_de(r_['r'][kr], r_['th'][kr]); er = (np.cos(r_['th'][kr]), -np.sin(r_['th'][kr]))
        D['rad'] = dict(Af=afi_files(x, y, er[0], er[1]), obs=r_['r'][kr] * r_['drho'][kr], sig=np.full(kr.sum(), SIG_ARC), r=r_['r'][kr], th=r_['th'][kr],
                        sec=np.floor(np.degrees(r_['th'][kr]) % 360 / 30).astype(int), ex=er[0], ey=er[1], x=x, y=y)
        ex_ = np.array([e['x'] for e in EST[X]]); ey_ = np.array([e['y'] for e in EST[X]]); one = np.ones(len(ex_)); zero = np.zeros(len(ex_))
        th_e = np.arctan2(-(ey_ - SOL[1]), ex_ - SOL[0]); sg = np.array([max(SIG_EST, 3.0 / e['sn_V']) for e in EST[X]])
        D['est'] = dict(Af=np.vstack([afi_files(ex_, ey_, one, zero), afi_files(ex_, ey_, zero, one)]), obs=np.concatenate([[e['ux'] for e in EST[X]], [e['uy'] for e in EST[X]]]),
                        sig=np.concatenate([sg, sg]), sec=np.concatenate([np.floor(np.degrees(th_e) % 360 / 30).astype(int)] * 2), x=ex_, y=ey_, ux=np.array([e['ux'] for e in EST[X]]), uy=np.array([e['uy'] for e in EST[X]]))
        return D
    import os
    SIG_EST, SIG_ARC = float(os.environ.get('F4_SIG_EST', '0.35')), float(os.environ.get('F4_SIG_ARC', '1.0'))
    def robust_lstsq(A_, b, s, k, protegits=None):
        """mínims quadrats ponderats amb exclusió dels > 4σ (MAD) — mai dels protegits (les estrelles, validades a S/N ≥ 6: amb milers de finestres de
        raigs, la MAD global les feia fora com a «extrems» i l'afí quedava sense la seva escala i translació)."""
        pr = np.zeros(len(b), bool) if protegits is None else protegits
        w = 1 / s; p = np.linalg.lstsq(A_[k] * w[k, None], b[k] * w[k], rcond=None)[0]
        for _ in range(4):
            res = (A_ @ p - b) * w; kk = k & ((np.abs(res) < 4 * 1.4826 * np.median(np.abs(res[k & ~pr])) + 1e-9) | pr); p = np.linalg.lstsq(A_[kk] * w[kk, None], b[kk] * w[kk], rcond=None)[0]
        return p
    def ajusta(D, keep=None):
        """afí amb totes les mesures; després la correcció tangencial amb els residus dels raigs de 1,3 a 6 R☉. keep: dict de màscares per tipus."""
        kp = keep or {t: np.ones(len(D[t]['obs']), bool) for t in D}
        Af = np.vstack([D[t]['Af'] for t in ('ang', 'rad', 'est')]); ob = np.concatenate([D[t]['obs'] for t in ('ang', 'rad', 'est')]); sg = np.concatenate([D[t]['sig'] for t in ('ang', 'rad', 'est')])
        e = D['est']; ke = kp['est']
        pa = np.linalg.lstsq(e['Af'][ke] / e['sig'][ke, None], e['obs'][ke] / e['sig'][ke], rcond=None)[0]     # l'afí: NOMÉS les estrelles
        a = D['ang']; res = a['obs'] - a['Af'] @ pa; zona = (a['r'] >= R0 * RS) & (a['r'] <= R1 * RS) & kp['ang']
        Bt = base_t(a['r'], a['th']) * (a['r'] * tau(a['r']))[:, None]; pt = robust_lstsq(Bt, res, a['sig'], zona)
        return dict(afi=pa.tolist(), dtheta=pt.tolist())
    rep = dict(guio=str(Path(__file__).relative_to(R)), model=dict(KT=KT, JT=JT, rang_Rsol=[R0, R1], tau_Rsol=list(TAU), sig_estrelles=SIG_EST, sig_arcs=SIG_ARC, estrelles_protegides=True), cv={}, sistematic={}, estrelles={})
    model = dict(conveni='u = posició a V − posició a X (px del llenç final, x cap a la dreta, y cap avall); X\'(q) = X(q − u(q))', SOL=list(SOL), RS=RS, N=NRM, KT=KT, JT=JT, rang_Rsol=[R0, R1], tau_Rsol=list(TAU), models={})
    for X in ('A', 'B'):
        D = dades(X)
        # validació creuada per sectors (tot el procediment)
        errs = []
        for fold in range(3):
            keep = {t: (D[t]['sec'] % 3) != fold for t in D}; m = ajusta(D, keep); mm = dict(models={X: m})
            a = D['ang']; te = ~keep['ang']; ux, uy = camp(mm, X, *xy_de(a['r'][te], a['th'][te])); pred = ux * (-np.sin(a['th'][te])) + uy * (-np.cos(a['th'][te]))
            errs.append(float(np.median(np.abs(pred - a['obs'][te]))))
        # sense estrelles: prediu les estrelles?
        n_e = len(D['est']['x']); loo = []
        for i in range(n_e):
            keep = {t: np.ones(len(D[t]['obs']), bool) for t in D}; keep['est'][[i, i + n_e]] = False; m = ajusta(D, keep)
            ux, uy = camp(dict(models={X: m}), X, D['est']['x'][i:i + 1], D['est']['y'][i:i + 1]); loo.append(np.hypot(ux[0] - D['est']['ux'][i], uy[0] - D['est']['uy'][i]))
        rms_sense = float(np.sqrt(np.mean(np.square(loo))))
        rep['cv'][X] = dict(error_mediana_px_sectors_fora=round(float(np.mean(errs)), 3), rms_estrelles_px_deixant_ne_una_fora=round(rms_sense, 2))
        # el model final i els residus sistemàtics
        m = ajusta(D); model['models'][X] = m; mm = dict(models={X: m})
        a = D['ang']; ux, uy = camp(mm, X, *xy_de(a['r'], a['th'])); ra = a['obs'] - (ux * (-np.sin(a['th'])) + uy * (-np.cos(a['th'])))
        rr_ = D['rad']; ux, uy = camp(mm, X, rr_['x'], rr_['y']); rrs = rr_['obs'] - (ux * rr_['ex'] + uy * rr_['ey'])
        tb = {}
        for lo, hi in ((1.3, 2), (2, 3), (3, 4.5), (4.5, 6), (6, 8)):
            k = (a['r'] >= lo * RS) & (a['r'] < hi * RS); meds = []; abans = []
            for sct in range(12):
                kk = k & (np.floor(np.degrees(a['th']) % 360 / 30) == sct)
                if kk.sum() >= 15: meds.append(np.median(ra[kk])); abans.append(np.median(a['obs'][kk]))
            kr = (rr_['r'] >= lo * RS) & (rr_['r'] < hi * RS)
            tb[f'{lo}-{hi}'] = dict(raigs_abans_px=[round(float(np.median(np.abs(abans))), 2), round(float(np.max(np.abs(abans))), 2)] if abans else None,
                                   raigs_residu_px=[round(float(np.median(np.abs(meds))), 2), round(float(np.max(np.abs(meds))), 2)] if meds else None,
                                   arcs_residu_px_mediana=round(float(np.median(np.abs(rrs[kr]))), 2) if kr.sum() >= 15 else None)
        ux, uy = camp(mm, X, D['est']['x'], D['est']['y']); d = np.hypot(ux - D['est']['ux'], uy - D['est']['uy']); d0 = np.hypot(D['est']['ux'], D['est']['uy'])
        rep['estrelles'][X] = dict(n=int(len(d)), abans_rms_px=round(float(np.sqrt(np.mean(d0 ** 2))), 2), residu_rms_px=round(float(np.sqrt(np.mean(d ** 2))), 2),
                                   residu_mediana_px=round(float(np.median(d)), 2), residu_max_px=round(float(d.max()), 2))
        rep['sistematic'][X] = tb
        log(X, 'cv', rep['cv'][X], '· estrelles', rep['estrelles'][X]); log(X, json.dumps(tb, ensure_ascii=False))
    th = np.linspace(0, 2 * np.pi, 720, endpoint=False); mag = {}
    for X in ('A', 'B'):
        mag[X] = {}
        for rR in (1.0, 1.5, 2, 3, 4, 5, 6, 8, 10, 12):
            ux, uy = camp(model, X, SOL[0] + rR * RS * np.cos(th), SOL[1] - rR * RS * np.sin(th)); m_ = np.hypot(ux, uy); mag[X][str(rR)] = [round(float(np.median(m_)), 2), round(float(m_.max()), 2)]
    rep['modul_camp_px_mediana_max_per_radi'] = mag; log('camp', json.dumps(mag, ensure_ascii=False))
    # continuïtat del camp (salt màxim entre píxels veïns en una graella de 8 px)
    yy, xx = np.mgrid[0:7506:8, 0:10551:8].astype(np.float64); salts = {}
    for X in ('A', 'B'):
        ux, uy = camp(model, X, xx, yy); salts[X] = round(float(max(np.abs(np.diff(ux, axis=0)).max(), np.abs(np.diff(ux, axis=1)).max(), np.abs(np.diff(uy, axis=0)).max(), np.abs(np.diff(uy, axis=1)).max()) / 8), 4)
    rep['salt_max_px_per_px'] = salts; log('salt màxim del camp (px per px de llenç)', salts)
    json.dump(model, open(F1 / os.environ.get('F4_SORTIDA', 'F4C_MODEL.json'), 'w'), ensure_ascii=False, indent=1)
    rep['segons'] = round(time.time() - t0, 1); json.dump(rep, open(F1 / os.environ.get('F4_SORTIDA', 'F4C_MODEL.json').replace('MODEL', 'REBUT'), 'w'), ensure_ascii=False, indent=1)
