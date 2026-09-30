import numpy as np, lib, esf
from scipy.ndimage import map_coordinates

for name in ["572A3012.CR3", "572A2998.CR3", "572A2962.CR3"]:
    img = lib.load(name)
    CY, CX, R = lib.solve_geometry(img)[:3]
    print(name, "centre raw %.1f %.1f  R=%.1f" % (CY, CX, R))
    # perfil azimutal: mitjana radial R+2 .. R+9 (raw px), per canals R i B
    for key, lab in [('R', 'vermell'), ('B', 'blau')]:
        p, oy, ox = lib.plane(img, key)
        naz = 360
        th = np.arange(naz)*2*np.pi/naz
        rr = np.arange(R+2, R+10, 1.0)
        Y = (CY + rr[None, :]*np.cos(th)[:, None] - oy)/2
        X = (CX + rr[None, :]*np.sin(th)[:, None] - ox)/2
        v = map_coordinates(p, [Y.ravel(), X.ravel()], order=1).reshape(naz, len(rr)).mean(1)
        base = np.median(v)
        top = np.argsort(v)[-14:][::-1]
        print("  %s  mediana=%.1f  pics (graus des de +y, horari): %s" % (
            lab, base, ", ".join("%.0f(x%.1f)" % (np.degrees(th[i]), v[i]/base) for i in sorted(top))))
