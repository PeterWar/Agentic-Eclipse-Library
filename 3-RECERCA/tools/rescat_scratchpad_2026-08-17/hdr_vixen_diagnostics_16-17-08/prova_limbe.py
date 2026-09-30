"""Prova: mesura del centre lunar per ajust del limbe, a exposicions diverses."""
import numpy as np, rawpy, time
from pathlib import Path

SRC = Path.home() / "Desktop/Eclipse 2026/Vixen Unfiltered"
MAS = SRC / "Masters_v2"
R_LLUNA = 460.0  # px reixa crua, research/75


def parell(a):
    return a[: a.shape[0] // 2 * 2, : a.shape[1] // 2 * 2]


def verd(nom, exp_key, exp_s):
    with rawpy.imread(str(SRC / nom)) as raw:
        v = parell(raw.raw_image_visible).astype(np.float32)
    m = np.load(MAS / f"master_{exp_key}.npy")
    v -= m
    # pla verd: G1 (0,1) i G2 (1,0) del patró RGGB, mitjana -> mitja resolucio
    g = 0.5 * (v[0::2, 1::2] + v[1::2, 0::2])
    return g / exp_s


def limbe(g, cy, cx, r_half, n_ang=360):
    """Retorna punts del limbe: on el perfil radial creua el 50 % entre
    l'interior del disc i la corona de just a fora."""
    ang = np.linspace(0, 2 * np.pi, n_ang, endpoint=False)
    rr = np.arange(r_half - 40, r_half + 40, 0.5)
    pts = []
    H, W = g.shape
    for a in ang:
        ys = cy + rr * np.sin(a)
        xs = cx + rr * np.cos(a)
        ok = (ys > 1) & (ys < H - 2) & (xs > 1) & (xs < W - 2)
        if ok.sum() < 40:
            continue
        yi = ys[ok].astype(int); xi = xs[ok].astype(int)
        prof = g[yi, xi]
        interior = np.median(prof[:15])
        exterior = np.median(prof[-15:])
        if exterior <= interior * 1.15:      # sense contrast utilitzable
            continue
        llindar = 0.5 * (interior + exterior)
        idx = np.argmax(prof > llindar)
        if idx == 0 or idx >= len(prof) - 1:
            continue
        # interpolació lineal del creuament
        p0, p1 = prof[idx - 1], prof[idx]
        f = (llindar - p0) / (p1 - p0) if p1 != p0 else 0.0
        rc = rr[ok][idx - 1] + f * 0.5
        pts.append((cy + rc * np.sin(a), cx + rc * np.cos(a)))
    return np.array(pts)


def ajusta_cercle(pts):
    """Ajust de cercle per mínims quadrats (algebraic) amb rebuig robust."""
    y, x = pts[:, 0], pts[:, 1]
    for _ in range(4):
        A = np.c_[x, y, np.ones(len(x))]
        b = x ** 2 + y ** 2
        sol, *_ = np.linalg.lstsq(A, b, rcond=None)
        cx, cy = sol[0] / 2, sol[1] / 2
        r = np.sqrt(sol[2] + cx ** 2 + cy ** 2)
        d = np.hypot(x - cx, y - cy) - r
        s = 1.4826 * np.median(np.abs(d - np.median(d)))
        keep = np.abs(d - np.median(d)) < 3 * max(s, 0.3)
        if keep.sum() < 30 or keep.all():
            break
        x, y = x[keep], y[keep]
    return cy, cx, r, len(x), float(np.std(d[np.abs(d) < 5 * max(s, .3)]))


CASOS = [("572A2960.CR3", "0.0003125", 0.0003125),
         ("572A2967.CR3", "0.0005", 0.0005),
         ("572A2969.CR3", "0.008", 0.008),
         ("572A2971.CR3", "0.125", 0.125),
         ("572A2972.CR3", "0.5", 0.5),
         ("572A2978.CR3", "1", 1.0),
         ("572A2980.CR3", "2", 2.0),
         ("572A2982.CR3", "10", 10.3),
         ("572A3020.CR3", "0.0003125", 0.0003125)]

cy0, cx0 = 2267.1 / 2, 3570.8 / 2   # mitja resolució
for nom, k, e in CASOS:
    t = time.time()
    g = verd(nom, k, e)
    cy, cx = cy0, cx0
    for _ in range(3):
        pts = limbe(g, cy, cx, R_LLUNA / 2)
        if len(pts) < 50:
            break
        cy, cx, r, n, rms = ajusta_cercle(pts)
    if len(pts) < 50:
        print(f"{nom} {e:<9g} ⛔ només {len(pts)} punts de limbe")
        continue
    print(f"{nom} {e:<9g} centre_cru=({2*cx:8.2f},{2*cy:8.2f})  R={2*r:6.1f}px "
          f"n={n:3d} rms={2*rms:.2f}px  [{time.time()-t:.1f}s]")
