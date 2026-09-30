"""V21 (tercera ronda): la capa d'estrelles amb PURESA MESURADA.

Pere: «n'estàs detectant fora del camp teòric del 300 mm». El camp surt net
(cap posició fora del sensor de 2+ fotogrames), però el control nul —les
mateixes 734 posicions predites girades al voltant del Sol, mateix radi i
mateix anell de soroll— destapa que a 3,5σ hi ha un 2,8 % de falsa alarma per
posició: amb 520 candidats de V 10-11,5, 15 dels 18 «detectats» eren gra.

Tall adoptat: finestra ±2 px (l'astrometria ho aguanta: rms de placa 0,71 px)
i V ≤ 9,5, que és el límit de detecció real de l'apilat. Puresa mesurada.
"""
from __future__ import annotations

import json, math, os, sys
import numpy as np, cv2, pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v21")
sys.path.insert(0, AQUI)
import fes_v15 as F15
import fes_v17 as F17
from v21_apilats import carrega_fits, FRAMES, BASE

DERIV = ("/Users/USUARI/Desktop/Eclipse 2026/Derivats/Astrometria/"
         "Estrelles/")
R_FIN, LLIND, VMAX = None, None, None      # els tria el control nul
ANGS = (30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330)
SOLp, RS = (6469.2, 6757.6), 455.5


def main():
    sv = F17.SV16(); geo15 = F15.Geo(padx=3387.0, pady=5109.0)
    comu, f2, run, ctx, S13, K, va = F15.carrega_sony()
    fits = carrega_fits(); vb = S13[BASE]
    solb = np.array([vb["sol_x"], vb["sol_y"]])
    sol = json.load(open(DERIV + "Resultats_acceptacio_2026-08-17/"
                         "final_solution.json"))["sony_radial"]
    cat = pd.read_csv(DERIV + "Work_2026-08-17/xmatch/cat2_sony.csv")
    vus = (cat["Vuse"] if "Vuse" in cat.columns else cat["Vmag"]).to_numpy(float)
    m0 = (np.isfinite(cat["xh_as"]) & np.isfinite(cat["yh_as"])
          & (vus <= 11.5)).to_numpy()
    cat = cat[m0].reset_index(drop=True); vus = vus[m0]
    px, py = np.array(sol["px"]), np.array(sol["py"])
    xi = cat["xh_as"].to_numpy(float); eta = cat["yh_as"].to_numpy(float)
    r2 = xi * xi + eta * eta
    A = np.column_stack([np.ones_like(xi), xi, eta, xi * r2, eta * r2])
    x15, y15 = geo15.raw_sony_a_v15(A @ px, A @ py, tuple(solb))
    xc, yc = sv.endavant(x15, y15)

    ap = np.load(os.path.join(CAU, "apilat_estrelles_rgb.npy"), mmap_mode="r")
    tr = np.asarray(np.load(os.path.join(CAU, "apilat_estrelles_tres.npy"),
                            mmap_mode="r"))
    G = np.asarray(ap[..., 1], np.float32)
    D = G - cv2.GaussianBlur(cv2.medianBlur(G, 5), (0, 0), 10.0); del G
    H, W = D.shape
    d_ = (xc > 20) & (xc < W - 20) & (yc > 20) & (yc < H - 20)
    cat = cat[d_].reset_index(drop=True); xc, yc, vus = xc[d_], yc[d_], vus[d_]

    # --- correcció fina AUTOCALIBRADA amb les brillants (centroide) ---
    ddx, ddy, bx, by = [], [], [], []
    for i in np.where(vus <= 9.0)[0]:
        x, y = int(round(xc[i])), int(round(yc[i]))
        if not (30 <= x < W - 30 and 30 <= y < H - 30) or not tr[y, x]:
            continue
        w = D[y - 8:y + 9, x - 8:x + 9].astype(np.float64)
        if w.max() < 40:
            continue
        iy, ix = np.unravel_index(np.argmax(w), w.shape)
        if not (2 <= iy < 15 and 2 <= ix < 15):
            continue
        sub = np.clip(w[iy - 2:iy + 3, ix - 2:ix + 3], 0, None)
        if sub.sum() <= 0:
            continue
        oy, ox = np.mgrid[-2:3, -2:3]
        ddx.append(x + ix - 8 + (sub * ox).sum() / sub.sum() - xc[i])
        ddy.append(y + iy - 8 + (sub * oy).sum() / sub.sum() - yc[i])
        bx.append(xc[i]); by.append(yc[i])
    OFX, OFY = float(np.median(ddx)), float(np.median(ddy))
    print(f"correcció fina autocalibrada amb {len(ddx)} brillants: "
          f"({OFX:+.2f}, {OFY:+.2f}) px")

    # --- camp de residu QUADRÀTIC mesurat sobre les brillants ---
    #     (la solució de placa és radial i el llenç hi afegeix la seva pròpia
    #      distorsió; sense això el pic queda 2,7 px fora de la predicció)
    PX = np.array(bx); PY = np.array(by)
    u = (PX - SOLp[0]) / 1000.0; v = (PY - SOLp[1]) / 1000.0
    M = np.column_stack([np.ones_like(u), u, v, u * u, u * v, v * v])
    CX = np.linalg.lstsq(M, np.array(ddx), rcond=None)[0]
    CY = np.linalg.lstsq(M, np.array(ddy), rcond=None)[0]
    rr = np.hypot(np.array(ddx) - M @ CX, np.array(ddy) - M @ CY)
    print(f"camp de residu quadràtic: mediana {np.median(rr):.2f} px "
          f"(constant sola: {np.median(np.hypot(np.array(ddx)-OFX, np.array(ddy)-OFY)):.2f} px)")
    uu = (xc - SOLp[0]) / 1000.0; vv = (yc - SOLp[1]) / 1000.0
    MM = np.column_stack([np.ones_like(uu), uu, vv, uu * uu, uu * vv, vv * vv])
    xc = xc + MM @ CX; yc = yc + MM @ CY

    yy = np.arange(H, dtype=np.float32)[:, None]
    xx = np.arange(W, dtype=np.float32)[None, :]
    rad = np.hypot(xx - SOLp[0], yy - SOLp[1]) / RS
    NB, lg0, lg1 = 48, np.log(1.8), np.log(20.0)
    bidx = np.clip(((np.log(np.maximum(rad, 1e-3)) - lg0)
                    / ((lg1 - lg0) / NB)).astype(np.int16), 0, NB - 1)
    del rad, xx, yy
    med_b = np.zeros(NB, np.float32); sig_b = np.full(NB, 1e9, np.float32)
    Ds, bs, ts = D[::3, ::3], bidx[::3, ::3], tr[::3, ::3]
    for bb in range(NB):
        v_ = Ds[(bs == bb) & ts]
        if v_.size > 300:
            md = np.median(v_)
            med_b[bb], sig_b[bb] = md, 1.4826 * np.median(np.abs(v_ - md))

    def mesura(xs, ys, R):
        ns = np.full(len(xs), -9.0); ex = np.zeros(len(xs)); ey = np.zeros(len(xs))
        for i in range(len(xs)):
            x, y = int(round(xs[i])), int(round(ys[i]))
            if not (8 <= x < W - 8 and 8 <= y < H - 8) or not tr[y, x]:
                continue
            w = D[y - R:y + R + 1, x - R:x + R + 1]
            iy, ix = np.unravel_index(np.argmax(w), w.shape)
            ns[i] = ((float(w[iy, ix]) - med_b[bidx[y, x]])
                     / max(sig_b[bidx[y, x]], 1e-6))
            ex[i], ey[i] = ix - R, iy - R
        return ns, ex, ey

    # --- escombrada contra el control nul: guanya el que més ESTRELLES REALS
    #     dona amb puresa >= 95 % ---
    cache = {}
    millor = None
    print(f"{'R':>2} {'llind':>5} {'Vmax':>5} {'sel':>4} {'control':>9} "
          f"{'reals':>6} {'puresa':>7}")
    for R in (1, 2, 3):
        NS, ex, ey = mesura(xc, yc, R)
        NSc = []
        for a_ in ANGS:
            a = math.radians(a_); c_, s_ = math.cos(a), math.sin(a)
            ux, uy = xc - SOLp[0], yc - SOLp[1]
            n_, _, _ = mesura(c_ * ux - s_ * uy + SOLp[0],
                              s_ * ux + c_ * uy + SOLp[1], R)
            NSc.append(n_)
        NSc = np.array(NSc)
        cache[R] = (NS, ex, ey, NSc)
        for lim in (3.0, 3.5, 4.0, 4.5, 5.0):
            for vmax in (11.5, 10.5, 10.0, 9.5, 9.0):
                mv = vus <= vmax
                nsel = int(((NS >= lim) & mv).sum())
                if nsel < 15:
                    continue
                cc = np.array([int(((z >= lim) & mv).sum()) for z in NSc], float)
                reals = nsel - cc.mean()
                pur = 100.0 * reals / nsel
                print(f"{R:>2} {lim:5.1f} {vmax:5.1f} {nsel:4d} "
                      f"{cc.mean():5.1f}±{cc.std():.1f} {reals:6.1f} {pur:6.1f}%")
                if pur >= 95.0 and (millor is None or reals > millor[0]):
                    millor = (reals, R, lim, vmax, cc.mean(), cc.std(), pur, nsel)
    reals, R_FIN, LLIND, VMAX, cm, cs, pur, n = millor
    NS, dx, dy, _ = cache[R_FIN]
    mv = vus <= VMAX
    sel = (NS >= LLIND) & mv
    ctrl = []
    print(f"\nTRIAT: finestra ±{R_FIN} px · llindar {LLIND}σ · V≤{VMAX}")
    print(f"SELECCIONADES: {n} · control nul {cm:.1f}±{cs:.1f} · "
          f"PURESA {pur:.1f} % (falses esperades {cm:.1f})")

    # cobertura per fotograma i radi angular
    def canvas_a_raw(X, Y, nm):
        a15, b15 = sv.enrere(np.asarray(X, float), np.asarray(Y, float))
        dX, dY = geo15.v15_a_comu(a15, b15)
        rbx, rby = geo15.comu_a_raw_sony(dX, dY, solb)
        th, t = fits[nm]; ca, sa = math.cos(th), math.sin(th)
        v = S13[nm]; sn = np.array([v["sol_x"], v["sol_y"]])
        ux = rbx - solb[0] - t[0]; uy = rby - solb[1] - t[1]
        return ca * ux + sa * uy + sn[0], -sa * ux + ca * uy + sn[1]

    Xf = xc[sel] + dx[sel]; Yf = yc[sel] + dy[sel]
    pl = ctx.plans(BASE, vb["exp"]); sh = np.asarray(pl[0]).shape
    RAWW, RAWH = sh[-1] * 2, sh[-2] * 2
    nfr = np.zeros(n, int)
    for nm in FRAMES:
        rx, ry = canvas_a_raw(Xf, Yf, nm)
        nfr += ((rx >= 0) & (rx < RAWW) & (ry >= 0) & (ry < RAWH)).astype(int)
    ESC = 2.1495 / 3600.0
    sol16 = json.load(open(os.path.join(CAU, "apilats_meta.json")))["sol16"]
    rdeg = np.hypot(Xf - sol16[0], Yf - sol16[1]) * ESC
    print(f"cobertura: " + " · ".join(f"{k}f:{int((nfr==k).sum())}"
                                      for k in range(6)))
    print(f"radi angular: mediana {np.median(rdeg):.2f}° · max {rdeg.max():.2f}°"
          f" (semicamp 300 mm: 3,56° x 2,37°)")
    fl = np.array([D[int(round(y))-3:int(round(y))+4,
                     int(round(x))-3:int(round(x))+4].sum()
                   for x, y in zip(Xf, Yf)])
    r_ = float(np.corrcoef(vus[sel], -2.5*np.log10(np.maximum(fl, 1)))[0, 1])
    print(f"fotometria: correlació V ↔ magnitud instrumental r = {r_:+.3f}")
    print(f"residu astromètric: mediana {np.median(np.hypot(dx[sel],dy[sel])):.2f} px")

    sub = cat[sel].reset_index(drop=True)
    files = []
    for i in range(n):
        r = sub.iloc[i]
        hip = r.get("HIP_n", r.get("HIP"))
        files.append({"x": float(Xf[i]), "y": float(Yf[i]),
                      "nsig": round(float(NS[sel][i]), 1),
                      "V": float(vus[sel][i]),
                      "HIP": None if pd.isna(hip) else int(hip),
                      "TYC": str(r.get("TYC", "")),
                      "HD": None if pd.isna(r.get("HD")) else int(r.get("HD")),
                      "Sp": str(r.get("Sp", "")),
                      "n_fotogrames": int(nfr[i]),
                      "r_graus": round(float(rdeg[i]), 2)})
    files.sort(key=lambda z: z["V"])
    json.dump(files, open(os.path.join(CAU, "estrelles_purga.json"), "w"),
              indent=1, ensure_ascii=False)
    np.save(os.path.join(CAU, "estrelles_v21_purga.npy"),
            np.array([[z["x"], z["y"], z["nsig"], 6.0] for z in files],
                     np.float32))
    json.dump({"n": n, "control_mitjana": cm, "control_sd": cs,
               "puresa_pct": pur, "llindar": LLIND, "correccio_fina": [OFX, OFY],
               "camp_residu_CX": list(map(float, CX)),
               "camp_residu_CY": list(map(float, CY)),
               "residu_brillants_px": float(np.median(rr)),
               "finestra_px": R_FIN, "V_max": VMAX,
               "r_fotometria": r_, "rdeg_max": float(rdeg.max()),
               "cobertura_fotogrames": {str(k): int((nfr == k).sum())
                                        for k in range(6)}},
              open(os.path.join(CAU, "purga_rebut.json"), "w"), indent=1)
    print("les 10 més brillants:")
    for z in files[:10]:
        nm = (f"HIP {z['HIP']}" if z["HIP"] else
              (f"HD {z['HD']}" if z["HD"] else z["TYC"]))
        print(f"  V {z['V']:5.2f} · {nm:12s} · {z['nsig']:5.1f}σ · "
              f"{z['n_fotogrames']}f · {z['r_graus']:.2f}° · {z['Sp']}")


if __name__ == "__main__":
    main()
