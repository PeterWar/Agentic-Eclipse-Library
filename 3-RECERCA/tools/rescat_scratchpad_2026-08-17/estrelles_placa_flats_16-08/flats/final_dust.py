#!/usr/bin/env python3
"""Mesura final de l'estructura de camp sobre el disc solar filtrat.

De cada fotograma es treu (a) el perfil azimutal --enfosquiment del limbe-- i
(b) un PLA, que absorbeix el gradient d'extincio atmosferica. El que queda es
pols, PRNU i soroll de fotons. El sostre de soroll es calcula del propi
fotograma: la dispersio pixel a pixel escala com 1/sqrt(senyal), i d'aixo se'n
treu el guany.

Nomes lectura.
"""
import os, sys
import numpy as np
import rawpy
from scipy import ndimage
from PIL import Image

OUT = os.path.dirname(os.path.abspath(__file__))


def plane_g(path, ped):
    with rawpy.imread(path) as r:
        v = r.raw_image_visible.astype(np.float64)
        wl = r.white_level
    return v[0::2, 1::2] - ped, wl - ped


def fit_disc(a, R):
    lo = np.percentile(a, 99.7)
    ys, xs = np.nonzero(a > 0.35 * lo)
    cy, cx = ys.mean(), xs.mean()
    th = np.linspace(-np.pi, np.pi, 720, endpoint=False)
    rs = np.arange(0.80 * R, 1.10 * R, 0.4)
    sol = [R, 0, 0]
    for _ in range(8):
        yq = cy + rs[None, :] * np.sin(th)[:, None]
        xq = cx + rs[None, :] * np.cos(th)[:, None]
        prof = ndimage.map_coordinates(a, [yq.ravel(), xq.ravel()], order=1).reshape(yq.shape)
        gt, gr = [], []
        for i in range(len(th)):
            p = prof[i]
            lv = 0.5 * np.percentile(p, 95)
            idx = np.nonzero(p > lv)[0]
            if len(idx) == 0 or idx[0] != 0:
                continue
            j = idx[-1]
            if j + 1 >= len(rs):
                continue
            f = (p[j] - lv) / max(p[j] - p[j + 1], 1e-9)
            gt.append(th[i]); gr.append(rs[j] + f * (rs[1] - rs[0]))
        gt = np.array(gt); gr = np.array(gr)
        A = np.stack([np.ones_like(gt), np.cos(gt), np.sin(gt)], 1)
        sol, *_ = np.linalg.lstsq(A, gr, rcond=None)
        cx += sol[1]; cy += sol[2]
        if abs(sol[1]) < 0.01 and abs(sol[2]) < 0.01:
            break
    return cy, cx, sol[0], len(gt), float(np.std(gr - A @ sol))


def analyse(label, path, ped, R, tag, rho_max=0.85):
    a, sat = plane_g(path, ped)
    nsat = int((a >= 0.985 * sat).sum())
    cy, cx, Rf, n, rms = fit_disc(a, R)
    r0 = int(R * rho_max)
    y0, y1 = int(cy) - r0 - 1, int(cy) + r0 + 2
    x0, x1 = int(cx) - r0 - 1, int(cx) + r0 + 2
    sub = a[y0:y1, x0:x1]
    yy, xx = np.mgrid[y0:y1, x0:x1]
    uy = yy - cy; ux = xx - cx
    rr = np.hypot(uy, ux) / R
    ins = rr < rho_max
    nb = 300
    ib = (rr / rho_max * nb).astype(int).clip(0, nb - 1)
    use = ins & (sub > 0)
    model = np.ones_like(sub)
    for _ in range(5):
        q = sub / model
        prof = np.array([np.median(q[use & (ib == k)]) if (use & (ib == k)).sum() > 40 else np.nan
                         for k in range(nb)])
        g = np.isfinite(prof)
        prof = np.interp(np.arange(nb), np.nonzero(g)[0], prof[g])
        base = model * np.interp(rr.ravel() / rho_max * nb, np.arange(nb), prof).reshape(rr.shape)
        # pla en log, per l'extincio
        w = use & (sub > 0.85 * base) & (sub < 1.15 * base)
        A = np.stack([np.ones(w.sum()), ux[w], uy[w]], 1)
        s, *_ = np.linalg.lstsq(A, np.log(sub[w] / base[w]), rcond=None)
        model = base * np.exp(s[0] + s[1] * ux + s[2] * uy)
        use = w
    res = np.where(use, sub / model - 1.0, np.nan)
    lvl = float(np.median(sub[use]))
    print(f"\n--- {label} : {os.path.basename(path)} ---")
    print(f"  centre (raw) ({cx*2:.0f},{cy*2:.0f})  R={Rf*2:.1f} px raw  rms vora {rms*2:.2f} px"
          f"   pixels saturats: {nsat}")
    print(f"  fotosfera {lvl:.0f} ADU   gradient d'extincio ajustat: "
          f"{np.hypot(s[1],s[2])*1.4427*500:.3f} EV / 1000 px raw")
    # guany per transferencia de fotons: sigma relativa contra senyal, per anells
    sig, sg = [], []
    for k in range(0, nb, 25):
        m = use & (ib >= k) & (ib < k + 25)
        if m.sum() < 5000:
            continue
        hp = res - ndimage.uniform_filter(np.nan_to_num(res, nan=0.0), 5)
        sig.append(np.median(sub[m])); sg.append(np.std(hp[m]) * np.sqrt(25 / 24.))
    sig = np.array(sig); sg = np.array(sg)
    gain = float(np.median(1.0 / (sg ** 2 * sig)))
    print(f"  guany estimat: {gain:.2f} e-/ADU  -> soroll de fotons per pixel a "
          f"{lvl:.0f} ADU = {100/np.sqrt(lvl*gain):.3f} %")
    rows = []
    for sc in (24, 60, 120, 260, 500):
        sg_px = sc / 2 / 2.355
        f2 = np.nan_to_num(res, nan=0.0)
        wgt = ndimage.gaussian_filter(use.astype(float), sg_px)
        sm = ndimage.gaussian_filter(f2, sg_px) / np.maximum(wgt, 1e-6)
        core = ndimage.binary_erosion(use, iterations=int(sc / 2) + 4)
        if core.sum() < 800:
            continue
        v = sm[core]
        neff = 4 * np.pi * sg_px ** 2
        floor = 100 / np.sqrt(lvl * gain) / np.sqrt(neff)
        rows.append((sc, np.std(v) * 100, np.min(v) * 100, np.max(v) * 100, floor))
        print(f"    escala {sc:>3} px raw: sigma={np.std(v)*100:.3f} %  "
              f"min={np.min(v)*100:+.3f} %  max={np.max(v)*100:+.3f} %"
              f"   | sostre de soroll {floor:.3f} %")
    v = np.nan_to_num(res, nan=0.0)
    im = np.clip((v + 0.01) / 0.02, 0, 1) * 255
    Image.fromarray(im.astype(np.uint8)).save(os.path.join(OUT, f"fin_{tag}.png"))
    return res, use, (cy, cx), rows, gain, lvl


if __name__ == "__main__":
    S = "/Users/USUARI/Desktop/Eclipse 2026/300mm"
    V = "/Users/USUARI/Desktop/Eclipse 2026/Vixen"
    print("=== R6 III + VSD90SS (f/5,5) — disc filtrat sencer, sense saturar ===")
    analyse("R6 1/1600 19:01", f"{V}/572A2907.CR3", 511.5, 219.4, "r6_2907")
    analyse("R6 1/2500 18:57", f"{V}/572A2906.CR3", 511.5, 219.4, "r6_2906")
    analyse("R6 1/1250 19:27", f"{V}/572A2908.CR3", 511.5, 219.4, "r6_2908")
    print("\n=== A7RIIIA + 300 GM (f/2,8) — disc filtrat, ja mossegat per la Lluna ===")
    analyse("Sony 1/400 19:38", f"{S}/DSC06928.ARW", 512.0, 146.4, "sony_6928")
    analyse("Sony 1/400 19:43", f"{S}/DSC06931.ARW", 512.0, 146.4, "sony_6931")
