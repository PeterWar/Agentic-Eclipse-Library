"""d3_prova_VS (V108, flat2d_v3, DIAGNOSI) · QUINES PARTS DE LA C DE LA VIXEN HI SÓN A LA DADA? La Sony com a cel de referència.
La Vixen no té segon apuntament, però la Sony veu el mateix cel amb un altre sensor (girat 33°, a una altra escala). A Z = X_V − X_S (ln, en
banda), el cel i la corona s'anul·len i queda el que va fix a cada sensor. El canvi que la C de la Vixen fa a l'apilat (D_c) només té
correlació amb la part de Z que és el defecte de la Vixen: pendent β = −1 si la component c hi és sencera, 0 si no hi és.
(El patró fix de la Sony a aquell punt és independent de la Vixen: només hi suma soroll, que el nul mesura.)
X_V = apilat Vixen del control; X_S = la Sony A+B del control (b3 de la V98); D_c = apilats_<c>/vixen_total.npy − X_V.
Mateixes bandes, anells i nuls desplaçats que d2. Sortida: diag/D3_PROVA_VS[_etiqueta].json
Ús: d3_prova_VS.py [--comps Lf,Lg,Kf,Kg] [--bandes 2-6,6-18,18-54,54-160] [--etiqueta …]"""
import json, argparse, time
from pathlib import Path
import numpy as np, cv2
ARREL = Path(__file__).resolve().parents[4]; R3 = ARREL / '4-RESULTATS/v108_20260926/flat2d_v3'
XV = ARREL / '4-RESULTATS/v97_refundacio_20260924/proves_apilat/vixen_comuna_taula_original/vixen_total.npy'
XS = ARREL / '4-RESULTATS/v98_20260925/cadena_v98/b3/cau/sony_corrected_total_v42.npy'
W, H = 10551, 7506; SOL = (5361.768, 3775.748); RSOL = 440.603; LLUNA = (5375.787, 3775.977); RL = 452.98
ap = argparse.ArgumentParser(); ap.add_argument('--comps', default='Lf,Lg,Kf,Kg'); ap.add_argument('--dir-comps', default=str(R3 / 'diag'))
ap.add_argument('--etiqueta', default=''); ap.add_argument('--quantitats', default='lnG,lnRG,lnBG'); ap.add_argument('--bandes', default='2-6,6-18,18-54,54-160')
a = ap.parse_args(); t0 = time.time(); DC = Path(a.dir_comps); COMPS = a.comps.split(',')
def q(p, nom):
    x = np.load(p, mmap_mode='r'); G = np.asarray(x[..., 1], np.float32)
    v = G if nom == 'lnG' else np.asarray(x[..., 0 if nom == 'lnRG' else 2], np.float32) / np.maximum(G, 1e-20)
    ok = np.isfinite(v) & (v > 0) & np.isfinite(G) & (G > 0)
    return np.where(ok, np.log(np.maximum(v, 1e-20)), 0).astype(np.float32), ok
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); RS = np.hypot(xx - SOL[0], yy - SOL[1]) / RSOL; DL = np.hypot(xx - LLUNA[0], yy - LLUNA[1]) - RL
SUB = ((yy.astype(np.int32) % 2) == 0) & ((xx.astype(np.int32) % 2) == 0); del yy, xx
BANDES = [tuple(int(v) for v in b.split('-')) for b in a.bandes.split(',')]
ANELLS = [(1.1, 1.5), (1.5, 2.5), (2.5, 4), (4, 6), (6, 10)]
DESPL = [(211, -157), (-173, 197), (307, 89), (-263, -241), (151, 331), (-389, 61), (97, -353), (-121, -167)]
res = dict(comps=COMPS, bandes_px=BANDES, anells_Rsol=ANELLS, despl_nul=DESPL, referencia=str(XS.relative_to(ARREL)), quantitats={})
for nom in a.quantitats.split(','):
    X, okX = q(XV, nom); S, okS = q(XS, nom); ok = okX & okS & (DL > 40) & (RS > 1.05)
    D = {}
    for c in COMPS:
        y, oy = q(DC / f'apilats_{c}' / 'vixen_total.npy', nom); D[c] = np.where(oy & okX, y - X, 0).astype(np.float32); ok &= oy; del y
    m = ok.astype(np.float32); Z0 = np.where(ok, X - S, 0).astype(np.float32); del X, S
    ng = lambda x, s: cv2.GaussianBlur(x * m, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6)
    out = {}
    for s1, s2 in BANDES:
        er = int(2 * s2) | 1; okb = cv2.erode(m, np.ones((er, er), np.uint8)) > 0
        Z = ng(Z0, s1) - ng(Z0, s2); U = {c: ng(D[c], s1) - ng(D[c], s2) for c in COMPS}; ob = {}
        for r0, r1 in ANELLS:
            k = okb & SUB & (RS >= r0) & (RS < r1)
            if k.sum() < 20000: continue
            z = Z[k].astype(np.float64); Us = np.stack([U[c][k] for c in COMPS], 1).astype(np.float64)
            en = (Us ** 2).mean(0); act = en > 1e-4 * en.max()
            beta = np.full(len(COMPS), np.nan); beta[act] = np.linalg.lstsq(Us[:, act], z, rcond=None)[0]; nuls = []
            for dx, dy in DESPL:
                ks = k & np.roll(np.roll(okb, dx, 1), dy, 0); zs = Z[ks].astype(np.float64)
                Uss = np.stack([np.roll(np.roll(U[c], dx, 1), dy, 0)[ks] for c in COMPS], 1).astype(np.float64)
                bn = np.full(len(COMPS), np.nan); bn[act] = np.linalg.lstsq(Uss[:, act], zs, rcond=None)[0]; nuls.append(bn)
            sd = np.sqrt(np.nanmean(np.array(nuls) ** 2, 0)); fit = Us[:, act] @ beta[act]
            ob[f'{r0}-{r1}'] = {c: dict(beta=None if not act[i] else round(float(beta[i]), 3), sigma_nul=None if not act[i] else round(float(sd[i]), 3),
                                        z=None if not act[i] else round(float(beta[i] / sd[i]), 2), rms_U_ppm=round(1e4 * float(np.sqrt(en[i])), 3)) for i, c in enumerate(COMPS)}
            ob[f'{r0}-{r1}'].update(rms_Z_ppm=round(1e4 * float(z.std()), 3), frac_var_explicada=round(float(1 - ((z - fit) ** 2).mean() / (z ** 2).mean()), 5), n=int(k.sum()))
        out[f'{s1}-{s2}px'] = ob
        print(nom, f'{s1}-{s2}px', ' | '.join(f"{an}: " + ' '.join(f"{c} {v[c]['beta']}±{v[c]['sigma_nul']}" for c in COMPS if v[c]['beta'] is not None) for an, v in ob.items()), f'{time.time()-t0:.0f}s', flush=True)
        del Z, U
    res['quantitats'][nom] = out; del Z0, D, m, ok
    (R3 / 'diag' / f'D3_PROVA_VS{a.etiqueta}.json').write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
print('FET', f'{time.time()-t0:.0f}s')
