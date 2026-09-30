"""NRGF de la V96 (24-09-2026). Norma canònica: res inventat ni reflectit; només estadística de la mateixa dada, com l'NRGF de sempre.
L'NRGF normalitza per anells d'1 px centrats al SOL: z = (I − μ(r)) / σ(r). Lluny de la Lluna és EXACTAMENT el de la V88 (E1, radial_v36).
Arran de la Lluna (desplaçada ~14 px del Sol), un mateix anell del Sol barreja píxels a tocar de la vora difuminada de la Lluna (a dalt i a baix) amb
píxels 14–20 px més enfora (a l'esquerra), i els primers px estan enfosquits i doblegats per la Lluna difuminada: surt una franja clara enganxada al limbe
(«el limbe pel mig») i un vorell fosc. Cura:
  1. μ(r), σ(r) dels anells del Sol, només amb corona NETA: sense la zona de la vora difuminada (d_vora < D_NET, amb d_vora = distància al limbe menys el
     desplaçament de la cresta de la dada a cada azimut, com la WOW V95).
  2. A la zona de la vora, a més, NORMALITZACIÓ PER ANELLS CENTRATS A LA LLUNA: A(d_vora) = mediana, a tots els azimuts amb dada, de I/μ(r) a cada d_vora
     (calaixos de 0,25 px). És el perfil de la vora difuminada (enfosquiment i cresta), igual a tot el voltant: z = (I/A_ef − μ) / σ, amb
     A_ef = 1 + (A − 1)·(1 − smoothstep(d_vora, D_NET − 4, D_NET)). La textura (el que canvia al llarg de l'arc) es queda.
"""
import numpy as np, cv2
def smoothstep(x, lo, hi):
    q = np.clip((x - lo) / (hi - lo), 0, 1); return q * q * (3 - 2 * q)
def estad_anells(a, m, r, nr):
    ri = np.floor(r).astype(np.int32); ids = ri[m]; v = a[m].astype(np.float64)
    n = np.bincount(ids, minlength=nr); s = np.bincount(ids, weights=v, minlength=nr); s2 = np.bincount(ids, weights=v * v, minlength=nr)
    mu = np.divide(s, n, out=np.zeros(nr), where=n > 0); sd = np.sqrt(np.maximum(0, np.divide(s2, n, out=np.zeros(nr), where=n > 0) - mu * mu)); return n, mu, sd
def nrgf_v96(a, m, r, dvora, D_NET=12.0, R_MAX=700, DR=0.25, log=print):
    """a, m, r (distància al Sol), dvora (distància al limbe lunar referida a la cresta) a la mateixa caixa, amb els anells r < R_MAX sencers dins la caixa.
    Retorna z (NaN fora de m) per a r < R_MAX, i el diagnòstic."""
    nr = R_MAX + 2; nodes = np.arange(nr) + 0.5; dins = m & (r < R_MAX)
    n0, mu0, sd0 = estad_anells(a, dins, r, nr)                        # com la V88 (totes les dades)
    net = dins & (dvora >= D_NET); n1, mu1, sd1 = estad_anells(a, net, r, nr)
    ok = n1 >= 20; mu = np.interp(r, nodes[ok], mu1[ok]).astype(np.float32); sd = np.interp(r, nodes[ok], sd1[ok]).astype(np.float32)
    zona = dins & (dvora < D_NET + 8); rho = np.where(zona, a / np.maximum(mu, 1e-12), np.nan)
    ds = np.arange(-4.0, D_NET + 8 + 1e-6, DR); ib = np.floor((dvora[zona] - ds[0]) / DR).astype(int); okb = (ib >= 0) & (ib < len(ds)); A = np.full(len(ds), np.nan)
    rv = rho[zona][okb]; ibv = ib[okb]; order = np.argsort(ibv, kind='stable'); cuts = np.searchsorted(ibv[order], np.arange(len(ds) + 1))
    for k in range(len(ds)):
        q = rv[order[cuts[k]:cuts[k + 1]]]
        if q.size >= 200: A[k] = np.median(q)
    okA = np.isfinite(A); A = np.interp(ds, ds[okA], A[okA]); A = np.convolve(np.pad(A, 2, mode='edge'), np.ones(5) / 5, mode='valid')   # suavitzat mínim (1,25 px)
    Aef = 1 + (np.interp(dvora, ds, A) - 1) * (1 - smoothstep(dvora, D_NET - 4, D_NET))
    z = np.where(dins, (a / Aef - mu) / np.maximum(sd, 1e-12), np.nan).astype(np.float32)
    info = dict(D_NET=D_NET, perfil_A={f'{d:.1f}': round(float(v), 4) for d, v in zip(ds[::4], A[::4])},
                anells_canviats=int(np.sum(np.abs(mu1[ok] - mu0[ok]) > 1e-9 * np.maximum(mu0[ok], 1))), r_max_canviat=float(nodes[ok][np.abs(mu1[ok] - mu0[ok]) > 1e-9 * np.maximum(mu0[ok], 1)].max()) if np.any(np.abs(mu1[ok] - mu0[ok]) > 1e-9 * np.maximum(mu0[ok], 1)) else None)
    return z, info
