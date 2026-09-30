import numpy as np, json, sys
from scipy.stats import chi2 as chi2d

def load(tag):
    D = np.load(tag + '.npy')
    info = json.load(open(tag + '.json'))
    return D, info

def ptc_bins(S, V, dof, nb=42, smin=0.8, smax=None, q=0.25, minn=60):
    smax = smax if smax is not None else S.max()
    ed = np.logspace(np.log10(smin), np.log10(smax), nb + 1)
    idx = np.digitize(S, ed) - 1
    corr = chi2d.ppf(q, dof) / dof          # biaix del quantil sota chi2
    out = []
    for i in range(nb):
        m = idx == i
        n = int(m.sum())
        if n < minn:
            continue
        s = float(np.median(S[m]))
        vq = float(np.quantile(V[m], q)) / corr
        vmed = float(np.median(V[m]))
        # incertesa: bootstrap simple del quantil
        rng = np.random.default_rng(1)
        bs = [np.quantile(rng.choice(V[m], n), q) / corr for _ in range(60)]
        err = float(np.std(bs))
        out.append((s, vq, err, n, vmed))
    return np.array(out)

def fitline(b, lo=None, hi=None, wmode='err'):
    m = np.ones(len(b), bool)
    if lo is not None: m &= b[:, 0] >= lo
    if hi is not None: m &= b[:, 0] <= hi
    s, v, e, n = b[m, 0], b[m, 1], b[m, 2], b[m, 3]
    w = 1 / np.maximum(e, 1e-6) ** 2 if wmode == 'err' else np.ones_like(s)
    X = np.stack([s, np.ones_like(s)], 1)
    C = np.linalg.inv(X.T @ (w[:, None] * X))
    beta = C @ (X.T @ (w * v))
    r = v - X @ beta
    dof = max(m.sum() - 2, 1)
    chi2 = float((w * r * r).sum() / dof)
    C = C * chi2
    slope, inter = beta
    return dict(npts=int(m.sum()), slope=float(slope), dslope=float(np.sqrt(C[0, 0])),
                inter=float(inter), dinter=float(np.sqrt(C[1, 1])),
                g=float(1 / slope), dg=float(np.sqrt(C[0, 0]) / slope ** 2),
                rn=float(np.sqrt(max(inter, 0))),
                drn=float(np.sqrt(C[1, 1]) / (2 * max(np.sqrt(max(inter, 1e-9)), 1e-6))),
                chi2=chi2, rms_rel=float(np.sqrt(np.mean((r / v) ** 2))))
