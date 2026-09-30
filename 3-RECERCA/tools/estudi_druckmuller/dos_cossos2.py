"""Els dos cossos, controlant-ho TOT a ma.

Res de postprocess: el negre de metadata de la R6 III es fals (research/71) i
a la corona externa aixo fa esclatar els quocients. Aqui:
  1. raw sencer, pedestal mesurat al marge FOSC de cada cos (no el declarat);
  2. binning 2x2 del mosaic -> R, G=(G1+G2)/2, B, sense cap interpolacio;
  3. balanc de dia + MATRIU de color de la camera -> primaries sRGB lineals.
Aixi un neutre de dia surt neutre als DOS cossos i es poden comparar.
"""
import numpy as np, rawpy

E = "/Users/USUARI/Desktop/Eclipse determinista/0-ENTRADES"
XYZ_SRGB = np.array([[3.24096994,-1.53738318,-0.49861076],
                     [-0.96924364,1.87596750,0.04155506],
                     [0.05563008,-0.20397696,1.05697151]])


def planes(cami):
    with rawpy.imread(cami) as r:
        raw = r.raw_image.astype(np.float64)
        vis = r.raw_image_visible.astype(np.float64)
        pat = np.asarray(r.raw_pattern)
        tm, lm = r.sizes.top_margin, r.sizes.left_margin
        bl = np.asarray(r.black_level_per_channel, float)
        dw = np.asarray(r.daylight_whitebalance, float)[:3]
        Mx = np.asarray(r.rgb_xyz_matrix)[:3, :3]
        sat = float(r.white_level)
        # pedestal MESURAT al marge esquerre emmascarat, per posicio de mosaic
        if lm >= 16:
            fosc = raw[tm:tm+vis.shape[0], 4:lm-4]
            ped = np.array([np.median(fosc[i::2, j::2]) for i in range(2) for j in range(2)])
        else:
            ped = bl.copy()
    print(f"   pedestal declarat {bl.round(1).tolist()}   MESURAT {ped.round(1).tolist()}   blanc {sat:.0f}")
    v = vis
    h, w = (v.shape[0]//2)*2, (v.shape[1]//2)*2
    v = v[:h, :w]
    # resta el pedestal segons la posicio dins del mosaic 2x2
    q = np.empty((2, 2, h//2, w//2))
    for i in range(2):
        for j in range(2):
            k = pat[i, j]
            q[i, j] = v[i::2, j::2] - ped[k]
    # pat: 0=R 1=G1 2=B 3=G2  (color_desc RGBG)
    P = {}
    for i in range(2):
        for j in range(2):
            P.setdefault(int(pat[i, j]), []).append(q[i, j])
    R = P[0][0]; B = P[2][0]; G = 0.5*(P[1][0] + P[3][0])
    cub = np.stack([R, G, B], -1)
    # balanc de dia
    cub = cub * (dw/dw[1])[None, None, :]
    # matriu: XYZ->cam invertida i a primaries sRGB, normalitzada perque el
    # blanc equilibrat surti neutre
    # convencio dcraw: es normalitzen les files de la matriu ENDAVANT
    # (sRGB->cam) i despres s'inverteix. Normalitzar la d'ENRERE dona una
    # matriu diferent i el cel sortia verdos.
    cam_rgb = Mx @ np.linalg.inv(XYZ_SRGB)
    cam_rgb = cam_rgb / cam_rgb.sum(axis=1, keepdims=True)
    M = np.linalg.inv(cam_rgb)
    print(f"   matriu cam->sRGB normalitzada:\n      " +
          "\n      ".join(str(row.round(4).tolist()) for row in M))
    return np.einsum("ij,hwj->hwi", M, cub), sat


def geo(lum):
    H, W = lum.shape
    ys, xs = np.nonzero(lum >= np.percentile(lum, 99.9))
    cy, cx = float(ys.mean()), float(xs.mean())
    for _ in range(8):
        th = np.linspace(0, 2*np.pi, 720, endpoint=False)
        rs = np.arange(4.0, min(cy, cx, H-cy, W-cx), 0.5)
        rad = []
        for t in th:
            yy = np.clip((cy+rs*np.sin(t)).astype(int), 0, H-1)
            xx = np.clip((cx+rs*np.cos(t)).astype(int), 0, W-1)
            s = lum[yy, xx]; kp = int(np.argmax(s))
            rad.append(rs[int(np.argmax(np.gradient(s)[:max(kp, 3)]))])
        rad = np.asarray(rad); med = np.median(rad); bo = np.abs(rad-med) < 0.06*med
        A = np.column_stack([np.cos(th[bo]), np.sin(th[bo]), np.ones(bo.sum())])
        dx, dy, Rr = np.linalg.lstsq(A, rad[bo], rcond=None)[0]
        cx += dx; cy += dy
        if abs(dx) < 0.05 and abs(dy) < 0.05:
            break
    return cy, cx, Rr/1.0335, bo.mean()


out = {}
for etiq, cami in [("SONY", f"{E}/SONY-A7RIIIA/totalitat/DSC06991.ARW"),
                   ("CANON", f"{E}/VIXEN-R6III/totalitat/572A2996.CR3")]:
    print(f"\n=== {etiq} ===")
    im, sat = planes(cami)
    lum = im @ np.array([0.2126, 0.7152, 0.0722])
    cy, cx, Rsol, bo = geo(lum)
    print(f"   R_sol {Rsol:.1f} px (binat 2x2)   ajust bo {bo*100:.0f} %")
    H, W = lum.shape
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.hypot(yy-cy, xx-cx)/Rsol; del yy, xx
    d = {}
    print(f"   {'r':>6} {'cob':>5} {'sat':>6} {'R/G':>8} {'B/G':>8}")
    vo = np.geomspace(1.05, float(r.max()), 22)
    for a, b in zip(vo[:-1], vo[1:]):
        m = (r >= a) & (r < b)
        if m.sum() < 2000: continue
        v = im[m]
        satf = float((v.max(axis=1) >= 0.90*sat).mean())
        ok = (v.max(axis=1) < 0.90*sat) & (v[:, 1] > 0)
        if ok.sum() < 800: continue
        vv = v[ok]; rc = float(np.sqrt(a*b))
        cob = min(m.sum()/(np.pi*(b*b-a*a)*Rsol*Rsol), 1.0)
        rg = float(np.median(vv[:, 0]/vv[:, 1])); bg = float(np.median(vv[:, 2]/vv[:, 1]))
        d[rc] = (cob, satf, rg, bg)
        print(f"   {rc:6.2f} {cob*100:4.0f}% {satf*100:5.1f}% {rg:8.3f} {bg:8.3f}")
    out[etiq] = d

print("\n=== CARA A CARA ===")
print(f"{'r':>6} | {'SONY R/G':>9} {'SONY B/G':>9} | {'CANON R/G':>10} {'CANON B/G':>10} | {'dif R/G':>8} {'dif B/G':>8}")
for rr in [1.6, 1.9, 2.2, 2.6, 3.1, 3.7, 4.4, 5.2, 6.2]:
    def v(D):
        k = np.array(sorted(D)); j = int(np.argmin(abs(k-rr)))
        return D[k[j]] if abs(k[j]-rr)/rr < 0.10 else None
    a, b = v(out["SONY"]), v(out["CANON"])
    if not a or not b or a[0] < 0.99 or b[0] < 0.99 or a[1] > 0.02 or b[1] > 0.02: continue
    print(f"{rr:6.2f} | {a[2]:9.3f} {a[3]:9.3f} | {b[2]:10.3f} {b[3]:10.3f} | "
          f"{(a[2]/b[2]-1)*100:+7.1f}% {(a[3]/b[3]-1)*100:+7.1f}%")
