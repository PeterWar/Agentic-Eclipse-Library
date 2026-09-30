"""Els DOS cossos, la mateixa corona, el mateix minut: quin color hi ha?

Aquesta es la prova que separa CAMERA d'ATMOSFERA. DSC06991 (Sony A7RIIIA,
300 mm, 1 s) i 572A2996 (Canon R6 III, VSD90SS, 1 s) son del mateix eclipsi
amb 20 s de diferencia. L'atmosfera hi es la MATEIXA; els sensors, no.

⚠️ Es revelen amb la CADENA DE COLOR SENCERA -- balanc de dia + matriu de
color de la camera + primaries sRGB, gamma lineal -- que es l'unica manera
que un neutre de dia surti neutre. Els multiplicadors sols NO son colorimetria
(avis de Codex, i el forat que teniem).
"""
import os
import numpy as np
import rawpy

E = "/Users/USUARI/Desktop/Eclipse determinista/0-ENTRADES"
COSSOS = [
    ("SONY A7RIIIA · 300 mm", f"{E}/SONY-A7RIIIA/totalitat/DSC06991.ARW", 3.234),
    ("CANON R6 III · VSD90SS", f"{E}/VIXEN-R6III/totalitat/572A2996.CR3", 2.1494813525884373),
]
RSOL_ARCSEC = 947.068


def revela(cami):
    with rawpy.imread(cami) as r:
        dw = np.asarray(r.daylight_whitebalance, float)
        print(f"   daylight LibRaw {dw[0]/dw[1]:.4f} {1.0:.4f} {dw[2]/dw[1]:.4f}   "
              f"matriu XYZ->cam fila0 {np.asarray(r.rgb_xyz_matrix)[0][:3].round(4).tolist()}")
        im = r.postprocess(output_color=rawpy.ColorSpace.sRGB,
                           user_wb=list(dw), no_auto_bright=True,
                           gamma=(1, 1), output_bps=16,
                           demosaic_algorithm=rawpy.DemosaicAlgorithm.AHD,
                           four_color_rgb=False, use_camera_wb=False, use_auto_wb=False)
    return im.astype(np.float32) / 65535.0


def geometria(lum, escala):
    H, W = lum.shape
    llind = np.percentile(lum, 99.9)
    ys, xs = np.nonzero(lum >= llind)
    cy, cx = float(ys.mean()), float(xs.mean())
    for _ in range(8):
        th = np.linspace(0, 2*np.pi, 720, endpoint=False)
        rs = np.arange(5.0, min(cy, cx, H-cy, W-cx), 1.0)
        rad = []
        for t in th:
            yy = np.clip((cy+rs*np.sin(t)).astype(int), 0, H-1)
            xx = np.clip((cx+rs*np.cos(t)).astype(int), 0, W-1)
            s = lum[yy, xx]; kp = int(np.argmax(s)); gg = np.gradient(s)
            rad.append(rs[int(np.argmax(gg[:max(kp, 3)]))])
        rad = np.asarray(rad); med = np.median(rad); bo = np.abs(rad-med) < 0.06*med
        A = np.column_stack([np.cos(th[bo]), np.sin(th[bo]), np.ones(bo.sum())])
        dx, dy, R = np.linalg.lstsq(A, rad[bo], rcond=None)[0]
        cx += dx; cy += dy
        if abs(dx) < 0.05 and abs(dy) < 0.05:
            break
    return cy, cx, R/1.0335, bo.mean()


res = {}
for etiq, cami, escala in COSSOS:
    print(f"\n=== {etiq}  ({os.path.basename(cami)}) ===")
    im = revela(cami)
    lum = im @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    cy, cx, Rsol, bo = geometria(lum, escala)
    print(f"   R_sol {Rsol:.1f} px (esperat {RSOL_ARCSEC/escala:.1f})   bons {bo*100:.0f} %   "
          f"saturats {(im.max(axis=2) >= 0.995).mean()*100:.2f} %")
    H, W = lum.shape
    yy, xx = np.mgrid[0:H, 0:W]
    r = (np.hypot(yy-cy, xx-cx)/Rsol).astype(np.float32); del yy, xx
    print(f"   {'r':>6} {'cob':>5} {'sat':>6} {'R/G':>8} {'B/G':>8}")
    fil = {}
    vores = np.geomspace(1.05, float(r.max()), 24)
    for a, b in zip(vores[:-1], vores[1:]):
        m = (r >= a) & (r < b)
        if m.sum() < 3000:
            continue
        v = im[m]
        sat = float((v.max(axis=1) >= 0.995).mean())
        ok = (v.max(axis=1) < 0.995) & (v[:, 1] > 1e-5)
        if ok.sum() < 1000:
            continue
        vv = v[ok]
        rc = float(np.sqrt(a*b))
        cob = m.sum()/(np.pi*(b*b-a*a)*Rsol*Rsol)
        rg = float(np.median(vv[:, 0]/vv[:, 1])); bg = float(np.median(vv[:, 2]/vv[:, 1]))
        fil[rc] = (min(cob, 1.0), sat, rg, bg)
        print(f"   {rc:6.2f} {min(cob,1)*100:4.0f}% {sat*100:5.1f}% {rg:8.3f} {bg:8.3f}")
    res[etiq] = fil

print("\n=== CARA A CARA (nomes radis amb anell sencer i sense saturar als DOS) ===")
print(f"{'r':>6} | {'SONY R/G':>9} {'SONY B/G':>9} | {'CANON R/G':>10} {'CANON B/G':>10} | {'dif R/G':>8} {'dif B/G':>8}")
S, C = res["SONY A7RIIIA · 300 mm"], res["CANON R6 III · VSD90SS"]
sr = np.array(sorted(S)); cr = np.array(sorted(C))
for rr in [1.15, 1.3, 1.5, 1.8, 2.2, 2.7, 3.3, 4.0, 5.0, 6.0, 7.5]:
    def val(D, K, i):
        k = np.array(sorted(D))
        if rr < k.min() or rr > k.max(): return None
        j = int(np.argmin(abs(k-rr)))
        return D[k[j]] if abs(k[j]-rr)/rr < 0.12 else None
    a, b = val(S, sr, 0), val(C, cr, 0)
    if not a or not b or a[0] < 0.99 or b[0] < 0.99 or a[1] > 0.02 or b[1] > 0.02:
        continue
    print(f"{rr:6.2f} | {a[2]:9.3f} {a[3]:9.3f} | {b[2]:10.3f} {b[3]:10.3f} | "
          f"{(a[2]/b[2]-1)*100:+7.1f}% {(a[3]/b[3]-1)*100:+7.1f}%")
