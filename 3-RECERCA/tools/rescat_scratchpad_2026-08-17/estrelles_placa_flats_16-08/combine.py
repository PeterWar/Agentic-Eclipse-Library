import numpy as np, json, sys, analyse as A

def per_pair(tag, box, order, q=0.25, only=None, minspan=20.0, minbins=6):
    D, info = A.load(tag)
    S, V, P = D[:, 0], D[:, 1], D[:, 4].astype(int)
    dof = box * box - (order + 1) * (order + 2) // 2
    res = []
    for i, inf in enumerate(info):
        if only is not None and i not in only:
            continue
        m = P == i
        s, v = S[m], V[m]
        if s.max() < minspan:
            continue
        b = A.ptc_bins(s, v, dof, nb=18, smin=max(0.8, np.percentile(s, 2)),
                       smax=s.max(), q=q, minn=40)
        if len(b) < minbins:
            continue
        f = A.fitline(b)
        if not np.isfinite(f['g']) or f['g'] <= 0 or f['dg'] / f['g'] > 0.35:
            continue
        res.append((i, inf, f, b))
    return res

def combine(vals, errs):
    vals = np.asarray(vals, float); errs = np.asarray(errs, float)
    w = 1 / errs ** 2
    m = (w * vals).sum() / w.sum()
    stat = 1 / np.sqrt(w.sum())
    chi2 = (w * (vals - m) ** 2).sum() / max(len(vals) - 1, 1)
    return m, stat * max(np.sqrt(chi2), 1.0), chi2, len(vals)
