"""j14 (V98) · Jutge dels punts 5 i 6 de Pere, capa per capa, sobre els ràsters de filtre (no el compost):
  ANELLS (punt 6): perfil del filtre per distància al limbe de presentació (calaixos de 0,5 px) a cada azimut (2°), només píxels amb dada
    (alfa ≥ 0,99). A cada azimut, recta ajustada a 12–30 px; residu a 0–12 px. La mediana del residu sobre tots els azimuts d'un sector de 30°
    és la part COHERENT al llarg de l'arc (un anell concèntric); el soroll s'hi anul·la. «clot» = el mínim d'aquesta mediana a 1–9 px, en unitats
    del filtre (0–1), i també dividit per la dispersió (DE) de la mateixa mediana a 12–30 px (unitats de «sigma de l'anell»).
  LUPA (punt 5): escala del gra. Per anells de distància, q = E[(u − G1 u)²] / E[(u − G4 u)²] (energia fina sobre energia fina+mitjana; convolució
    normalitzada per la dada). Una textura ampliada té menys energia fina: q baixa. Índex de lupa = q(2–20 px) / q(40–80 px) per sector
    (1 = mateix gra que lluny del limbe; < 1 = gra més gros arran del limbe).
Ús: j14_anells_lupa.py <sortida.json> nom=<carpeta filtres>[,prefix] ... [--suport <A3B.npz>]   (la carpeta té <tag>_u16.npy i <tag>_alfa_u16.npy)
--suport: (Codex, 25-09) només els píxels del domini de dada d'aquella franja (el mateix suport físic per a totes les versions): així el nivell
del buit de les capes en Multiplicar no compta com a dada."""
import sys, json
from pathlib import Path
import numpy as np, cv2
LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736
TAG = {41: 'P01_NRGF', 42: 'P01_NRGF_extrap', 43: 'P02_RHEF', 44: 'P02b_RHEF_ups0.35', 45: 'P02c_RHEF_local60_native', 46: 'P02d_RHEF_local30_native',
       47: '03', 48: '03v30', 49: '07', 50: '01', 51: '04', 52: '05', 53: '06', 54: 'P03_MGN', 55: 'P04_WOW', 56: 'P05_WOW_bilateral'}
box = (4780, 3180, 5980, 4380); x0, y0, x1, y1 = box
yy, xx = np.mgrid[y0:y1, x0:x1]; d = (np.hypot(xx - LX, yy - LY) - RL).astype(np.float32); th = ((np.degrees(np.arctan2(-(yy - LY), xx - LX)) + 360) % 360).astype(np.float32)
zona = (d >= 0) & (d < 100)
if '--suport' in sys.argv:
    _Q = np.load(sys.argv[sys.argv.index('--suport') + 1]); _by0, _by1, _bx0, _bx1 = [int(v) for v in _Q['box']]; zona &= np.asarray(_Q['domini'])[y0 - _by0:y1 - _by0, x0 - _bx0:x1 - _bx0]
    sys.argv = sys.argv[:sys.argv.index('--suport')]
NB = 200; nb = np.clip((d / 0.5).astype(int), 0, NB - 1); NT = 180; tb = (th / 2).astype(int) % NT
def ngs(u, w, s):
    return cv2.GaussianBlur(u * w, (0, 0), s) / np.maximum(cv2.GaussianBlur(w, (0, 0), s), 1e-6)
def mesura(u, al):
    ok = zona & (al >= 0.99); idx = tb[ok] * NB + nb[ok]
    s = np.bincount(idx, weights=u[ok], minlength=NT * NB); n = np.bincount(idx, minlength=NT * NB)
    P = np.where(n >= 3, s / np.maximum(n, 1), np.nan).reshape(NT, NB); dc = (np.arange(NB) + 0.5) * 0.5
    res = np.full_like(P, np.nan); fit = (dc >= 12) & (dc <= 30)
    for k in range(NT):
        p = P[k]; f = fit & np.isfinite(p)
        if f.sum() < 10: continue
        c = np.polyfit(dc[f], p[f], 1); res[k] = p - np.polyval(c, dc)
    anells = {}
    for a0 in range(0, 360, 30):
        ks = np.arange(a0 // 2, (a0 + 30) // 2); med = np.nanmedian(res[ks], axis=0)
        w19 = (dc >= 1) & (dc <= 9); wr = (dc >= 12) & (dc <= 30)
        if np.isfinite(med[w19]).sum() < 3: continue
        clot = float(np.nanmin(med[w19])); dmin = float(dc[w19][np.nanargmin(med[w19])]); sd = float(np.nanstd(med[wr])) + 1e-6
        anells[f'{a0}-{a0+30}'] = dict(clot=round(clot, 4), d_px=dmin, clot_sigma=round(clot / sd, 1), perfil_0_12=[None if not np.isfinite(v) else round(float(v), 4) for v in med[:24]])
    w = ok.astype(np.float32); uu = np.where(ok, u, 0).astype(np.float32)
    g1 = ngs(uu, w, 1.0); g4 = ngs(uu, w, 4.0); e1 = np.where(ok, (uu - g1) ** 2, 0); e4 = np.where(ok, (uu - g4) ** 2, 0)
    lupa = {}
    for a0 in range(0, 360, 30):
        sec = ok & (((th - a0) % 360) < 30)
        def q(dlo, dhi):
            z = sec & (d >= dlo) & (d < dhi) & (cv2.erode(ok.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0)   # sense els 4 px de la vora de la dada
            return float(e1[z].sum() / max(e4[z].sum(), 1e-12)) if z.sum() > 200 else np.nan
        qn, qf = q(2, 20), q(40, 80)
        lupa[f'{a0}-{a0+30}'] = dict(q_2_20=None if not np.isfinite(qn) else round(qn, 3), q_40_80=None if not np.isfinite(qf) else round(qf, 3), index=None if not (np.isfinite(qn) and np.isfinite(qf)) else round(qn / qf, 3))
    return anells, lupa
if __name__ == '__main__':
    out = Path(sys.argv[1]); rep = {}
    for arg in sys.argv[2:]:
        nom, carp = arg.split('=', 1); carp = Path(carp); rep[nom] = {}
        for lid, tag in TAG.items():
            fu = carp / f'{tag}_u16.npy'; fa = carp / f'{tag}_alfa_u16.npy'
            if not fu.exists(): continue
            u = np.load(fu, mmap_mode='r')[y0:y1, x0:x1].astype(np.float32) / 65535; al = np.load(fa, mmap_mode='r')[y0:y1, x0:x1].astype(np.float32) / 65535
            an, lu = mesura(u, al)
            clots = [v['clot'] for v in an.values()]; idxs = [v['index'] for v in lu.values() if v['index'] is not None]
            rep[nom][lid] = dict(tag=tag, clot_pitjor=min(clots) if clots else None, clot_sigma_pitjor=min(v['clot_sigma'] for v in an.values()) if an else None,
                                 lupa_index_min=min(idxs) if idxs else None, lupa_index_mediana=float(np.median(idxs)) if idxs else None, anells=an, lupa=lu)
            print(nom, lid, tag, 'clot', rep[nom][lid]['clot_pitjor'], '(σ', rep[nom][lid]['clot_sigma_pitjor'], ') lupa min', rep[nom][lid]['lupa_index_min'], 'med', rep[nom][lid]['lupa_index_mediana'], flush=True)
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=1))
