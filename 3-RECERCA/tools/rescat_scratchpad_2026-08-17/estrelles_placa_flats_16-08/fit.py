import numpy as np, json, sys

def binned(S, V, nb=40, smin=None, smax=None, log=True, minn=30):
    smin = smin if smin is not None else max(S.min(), 0.5)
    smax = smax if smax is not None else S.max()
    if log:
        edges = np.logspace(np.log10(smin), np.log10(smax), nb + 1)
    else:
        edges = np.linspace(smin, smax, nb + 1)
    idx = np.digitize(S, edges) - 1
    out = []
    for i in range(nb):
        m = idx == i
        if m.sum() < minn:
            continue
        s = np.median(S[m])
        # variancia tipica del bin: mediana (robusta a pegats amb estructura)
        v = np.median(V[m])
        # error de la mediana
        n = m.sum()
        err = 1.2533 * np.std(V[m]) / np.sqrt(n)
        out.append((s, v, err, n))
    return np.array(out)


def fitline(b, wmode='err'):
    s, v, e, n = b[:, 0], b[:, 1], b[:, 2], b[:, 3]
    w = 1.0 / np.maximum(e, 1e-9) ** 2 if wmode == 'err' else np.ones_like(s)
    X = np.stack([s, np.ones_like(s)], 1)
    C = np.linalg.inv(X.T @ (w[:, None] * X))
    beta = C @ (X.T @ (w * v))
    r = v - X @ beta
    dof = max(len(s) - 2, 1)
    chi2 = float((w * r ** 2).sum() / dof)
    C = C * chi2
    slope, inter = beta
    g = 1 / slope
    dg = g * np.sqrt(C[0, 0]) / slope
    rn = np.sqrt(max(inter, 0))
    drn = np.sqrt(C[1, 1]) / (2 * max(rn, 1e-9))
    return dict(g=g, dg=abs(dg), rn=rn, drn=drn, slope=slope, dslope=np.sqrt(C[0, 0]),
                inter=inter, dinter=np.sqrt(C[1, 1]), chi2=chi2, npts=len(s))
