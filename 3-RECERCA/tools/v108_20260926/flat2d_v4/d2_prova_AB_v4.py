"""d2_prova_AB (V108, flat2d_v4 · còpia de la v3, DIAGNOSI) · QUINES PARTS DE C HI SÓN A LA DADA? La prova dels dos apuntaments de la Sony.
El mateix cel es va veure a dues posicions del sensor separades 749 px (el salt de muntura). A la diferència Z = X_A − X_B (ln, en banda), el cel
i la corona s'anul·len i només hi queda el que va fix al sensor (més soroll). Si una part de C és un defecte que hi era a les llums, el canvi que
fa a cada apilat (D_A, D_B) és −(defecte), i Z = −(D_A − D_B): pendent β = −1. Si no hi era, β = 0 (C l'injecta).
Regressió múltiple de Z sobre U_c = D_c,A − D_c,B per a cada component c de d0 (Lf, Lg, Kf, Kg), per bandes (DoG, px del llenç) i anells (R☉),
a la lluminància (ln G) i al color (ln R/G, ln B/G, després de la matriu). NUL: la mateixa regressió amb els U desplaçats (8 desplaçaments de
150–400 px): dona la dispersió de β que dona l'atzar a la mateixa imatge (σ_nul), i z = β/σ_nul.
Entrades: els apilats del control (cadena) i d1 (apilats_<c>). Sortida: 4-RESULTATS/v108_20260926/flat2d_v4/diag/D2_PROVA_AB[_etiqueta].json
Ús: d2_prova_AB.py [--comps Lf,Lg,Kf,Kg] [--dir-comps diag] [--etiqueta …]   (només lectura; ~8 GB)"""
import json, argparse, time
from pathlib import Path
import numpy as np, cv2
ARREL = Path(__file__).resolve().parents[4]; R3 = ARREL / '4-RESULTATS/v108_20260926/flat2d_v4'   # v4: sortida i apilats_<c> a flat2d_v4/diag (còpia del guió de la v3)
CR = ARREL / '4-RESULTATS/v97_refundacio_20260924/cadena_raw'
W, H = 10551, 7506; SOL = (5361.768, 3775.748); RSOL = 440.603; LLUNA = (5375.787, 3775.977); RL = 452.98
ap = argparse.ArgumentParser(); ap.add_argument('--comps', default='Lf,Lg,Kf,Kg'); ap.add_argument('--dir-comps', default=str(R3 / 'diag'))
ap.add_argument('--etiqueta', default=''); ap.add_argument('--quantitats', default='lnG,lnRG,lnBG'); ap.add_argument('--bandes', default='2-6,6-18,18-54,54-160,160-400')
a = ap.parse_args(); t0 = time.time(); DC = Path(a.dir_comps); COMPS = a.comps.split(',')
CTRL = {'A': CR / 'b2_sony_A/cau/sony_A_total_v36.npy', 'B': CR / 'b2_sony_B/cau/sony_B_total_v42.npy'}
def cami(c, P): return DC / f'apilats_{c}' / ('sony_A_total.npy' if P == 'A' else 'cau/sony_B_total_v42.npy')
def q(p, nom):
    x = np.load(p, mmap_mode='r')
    G = np.asarray(x[..., 1], np.float32)
    if nom == 'lnG': v = G
    else: v = np.asarray(x[..., 0 if nom == 'lnRG' else 2], np.float32) / np.maximum(G, 1e-20)
    ok = np.isfinite(v) & (v > 0) & np.isfinite(G) & (G > 0)
    return np.where(ok, np.log(np.maximum(v, 1e-20)), 0).astype(np.float32), ok
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); RS = np.hypot(xx - SOL[0], yy - SOL[1]) / RSOL; DL = np.hypot(xx - LLUNA[0], yy - LLUNA[1]) - RL
SUB = ((yy.astype(np.int32) % 2) == 0) & ((xx.astype(np.int32) % 2) == 0); del yy, xx   # mostreig 1 de cada 4 píxels per a la regressió (la banda ja és correlacionada)
BANDES = [tuple(int(v) for v in b.split('-')) for b in a.bandes.split(',')]
ANELLS = [(1.5, 3), (3, 6), (6, 10), (10, 30)]
DESPL = [(211, -157), (-173, 197), (307, 89), (-263, -241), (151, 331), (-389, 61), (97, -353), (-121, -167)]
res = dict(comps=COMPS, bandes_px=BANDES, anells_Rsol=ANELLS, despl_nul=DESPL, quantitats={})
for nom in a.quantitats.split(','):
    XA, okA = q(CTRL['A'], nom); XB, okB = q(CTRL['B'], nom)
    DA, DB = {}, {}; ok = okA & okB & (DL > 80) & (RS > 1.2)
    for c in COMPS:
        ya, oa = q(cami(c, 'A'), nom); DA[c] = np.where(oa & okA, ya - XA, 0).astype(np.float32); ok &= oa; del ya
        yb, ob = q(cami(c, 'B'), nom); DB[c] = np.where(ob & okB, yb - XB, 0).astype(np.float32); ok &= ob; del yb
    m = ok.astype(np.float32); Z0 = np.where(ok, XA - XB, 0).astype(np.float32); del XA, XB
    U0 = {c: np.where(ok, DA[c] - DB[c], 0).astype(np.float32) for c in COMPS}; del DA, DB
    ng = lambda x, s: cv2.GaussianBlur(x * m, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6)
    out = {}
    for s1, s2 in BANDES:
        er = int(2 * s2) | 1; okb = cv2.erode(m, np.ones((er, er), np.uint8)) > 0
        Z = ng(Z0, s1) - ng(Z0, s2); U = {c: ng(U0[c], s1) - ng(U0[c], s2) for c in COMPS}
        ob = {}
        for r0, r1 in ANELLS:
            k = okb & SUB & (RS >= r0) & (RS < r1)
            if k.sum() < 20000: continue
            z = Z[k].astype(np.float64); Us = np.stack([U[c][k] for c in COMPS], 1).astype(np.float64)
            en = (Us ** 2).mean(0); act = en > 1e-4 * en.max()
            beta = np.full(len(COMPS), np.nan); beta[act] = np.linalg.lstsq(Us[:, act], z, rcond=None)[0]
            nuls = []
            for dx, dy in DESPL:
                ks = k & np.roll(np.roll(okb, dx, 1), dy, 0)
                zs = Z[ks].astype(np.float64); Uss = np.stack([np.roll(np.roll(U[c], dx, 1), dy, 0)[ks] for c in COMPS], 1).astype(np.float64)
                bn = np.full(len(COMPS), np.nan); bn[act] = np.linalg.lstsq(Uss[:, act], zs, rcond=None)[0]; nuls.append(bn)
            nuls = np.array(nuls); sd = np.sqrt(np.nanmean(nuls ** 2, 0))
            fit = Us[:, act] @ beta[act]
            ob[f'{r0}-{r1}'] = {c: dict(beta=None if not act[i] else round(float(beta[i]), 3), sigma_nul=None if not act[i] else round(float(sd[i]), 3),
                                        z=None if not act[i] else round(float(beta[i] / sd[i]), 2), rms_U_ppm=round(1e4 * float(np.sqrt(en[i])), 3)) for i, c in enumerate(COMPS)}
            ob[f'{r0}-{r1}']['rms_Z_ppm'] = round(1e4 * float(z.std()), 3); ob[f'{r0}-{r1}']['frac_var_explicada'] = round(float(1 - ((z - fit) ** 2).mean() / (z ** 2).mean()), 5)
            ob[f'{r0}-{r1}']['n'] = int(k.sum())
        out[f'{s1}-{s2}px'] = ob
        print(nom, f'{s1}-{s2}px', ' | '.join(f"{an}: " + ' '.join(f"{c} {v[c]['beta']}±{v[c]['sigma_nul']}" for c in COMPS if v[c]['beta'] is not None) for an, v in ob.items()), f'{time.time()-t0:.0f}s', flush=True)
        del Z, U
    res['quantitats'][nom] = out; del Z0, U0, m, ok
    (R3 / 'diag' / f'D2_PROVA_AB{a.etiqueta}.json').write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
print('FET', f'{time.time()-t0:.0f}s')
