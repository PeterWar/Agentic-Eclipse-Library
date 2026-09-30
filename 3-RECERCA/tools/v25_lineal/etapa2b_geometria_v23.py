#!/usr/bin/env python3
"""V25 · etapa 2b: geometria llenç comú → V23 MESURADA contra la fusionada de la
V24 (corona sencera 1,15-4,0 R☉), amb comprovació per finestres a diversos radis
i correcció final de similitud (rotació, escala, translació) ajustada a les
finestres. Substitueix l'etapa 2 (que es va enganxar a la vora del disc)."""
import os, json, time, numpy as np, cv2
from scipy.ndimage import gaussian_filter
from psd_tools import PSDImage
AQUI = os.path.dirname(os.path.abspath(__file__)); CAU = os.path.join(AQUI, "cau_v25")
V24 = "/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/CapesTotalsV24.psb"
RS = 440.603; CXP, CYP = 5361.877, 3774.741
T0 = time.time()
def marca(t): print(f"[{time.time()-T0:6.1f} s] {t}", flush=True)

def prep(img, m, s_lo=4.0, s_hi=40.0):
    x = np.where(m & (img > 0), np.log(np.maximum(img, 1e-9)), 0.0).astype(np.float32); mf = m.astype(np.float32)
    def bl(a, s): return gaussian_filter(a * mf, s) / np.maximum(gaussian_filter(mf, s), 1e-6)
    return (np.where(m, bl(x, s_lo) - bl(x, s_hi), 0.0) * mf).astype(np.float32)

def fase(a, b):
    A = np.fft.rfft2(a); B = np.fft.rfft2(b); R = A * np.conj(B); R /= np.maximum(np.abs(R), 1e-12)
    c = np.fft.irfft2(R, s=a.shape); k = np.unravel_index(np.argmax(c), c.shape); pk = float(c[k])
    dy = k[0] if k[0] <= a.shape[0] // 2 else k[0] - a.shape[0]; dx = k[1] if k[1] <= a.shape[1] // 2 else k[1] - a.shape[1]
    def sub(cm, i, n):
        i0, i1, i2 = cm[(i - 1) % n], cm[i], cm[(i + 1) % n]; d = i0 - 2 * i1 + i2
        return 0.0 if d == 0 else 0.5 * (i0 - i2) / d
    return dy + sub(c[:, k[1]], k[0], c.shape[0]), dx + sub(c[k[0], :], k[1], c.shape[1]), pk / max(float(np.std(c)), 1e-12)

def main():
    base = np.load(os.path.join(CAU, "base_B_rgb16.npy")).astype(np.float32) / 65535.0; mf = np.load(os.path.join(CAU, "mascara_fusio.npy"))
    Hl, Wl = mf.shape; cxl, cyl = Wl / 2.0, Hl / 2.0
    Lb = (base[..., 0] + 2 * base[..., 1] + base[..., 2]) / 4.0; del base
    yy, xx = np.mgrid[0:Hl, 0:Wl].astype(np.float32); rl = np.hypot(yy - cyl, xx - cxl) / RS; del yy, xx
    hb = prep(Lb, mf & (rl > 1.15) & (rl < 4.0)); del Lb, rl
    psd = PSDImage.open(V24); Wp, Hp = psd.width, psd.height; hdr = psd._record.header
    pl = psd._record.image_data.get_data(hdr)
    Lp = sum(np.frombuffer(pl[c], ">u2").reshape(Hp, Wp).astype(np.float32) * w for c, w in ((0, 1), (1, 2), (2, 1))) / (4 * 65535.0)
    yy, xx = np.mgrid[0:Hp, 0:Wp].astype(np.float32); rp = np.hypot(yy - CYP, xx - CXP) / RS; del yy, xx
    hp = prep(Lp, (Lp > 0.02) & (rp > 1.15) & (rp < 4.0)); del Lp
    marca("preparats (banda 4-40 px de ln I, anell 1,15-4,0 R☉)")
    def escombra(f, ths, img_b, img_p):
        sb = cv2.resize(img_b, (Wl // f, Hl // f), interpolation=cv2.INTER_AREA); sp = cv2.resize(img_p, (Wp // f, Hp // f), interpolation=cv2.INTER_AREA)
        S = (max(sb.shape[0], sp.shape[0]) + 64, max(sb.shape[1], sp.shape[1]) + 64)
        def pad(a):
            o = np.zeros(S, np.float32); o[:a.shape[0], :a.shape[1]] = a; return o
        P = pad(sp); out = []
        for th in ths:
            M = cv2.getRotationMatrix2D((cxl / f, cyl / f), th, 1.0)
            r = cv2.warpAffine(sb, M, (sb.shape[1], sb.shape[0]), flags=cv2.INTER_LINEAR)
            dy, dx, pk = fase(P, pad(r)); out.append((pk, th, dy * f, dx * f))
        return max(out, key=lambda t: t[0]), sorted(out, key=lambda t: -t[0])[:3]
    best, top3 = escombra(8, np.arange(0, 360, 0.5), hb, hp); marca(f"escombrada ×8 a 0,5°: {best} · top3 {[(round(t[0],1), t[1]) for t in top3]}")
    best, _ = escombra(4, np.arange(best[1] - 1.0, best[1] + 1.0, 0.05), hb, hp); marca(f"refinat ×4: θ={best[1]:.2f}° · resposta {best[0]:.1f}")
    best, _ = escombra(2, np.arange(best[1] - 0.15, best[1] + 0.1501, 0.01), hb, hp); marca(f"refinat ×2: θ={best[1]:.2f}° · t≈({best[3]:.1f},{best[2]:.1f}) · resposta {best[0]:.1f}")
    th, ty, tx = best[1], best[2], best[3]
    M1 = cv2.getRotationMatrix2D((cxl, cyl), th, 1.0); M1[0, 2] += tx; M1[1, 2] += ty
    # finestres a ×1 i correcció de similitud
    for it in range(2):
        hbw = cv2.warpAffine(hb, M1, (Wp, Hp), flags=cv2.INTER_LINEAR); fin = []
        for r_ in (1.6, 2.4, 3.3):
            for az in np.arange(0, 360, 45):
                yc = int(CYP + r_ * RS * np.sin(np.radians(az))); xc = int(CXP + r_ * RS * np.cos(np.radians(az)))
                a = hp[yc - 256:yc + 256, xc - 256:xc + 256]; b = hbw[yc - 256:yc + 256, xc - 256:xc + 256]
                if a.shape != (512, 512) or (np.abs(a) > 0).mean() < 0.6 or (np.abs(b) > 0).mean() < 0.6: continue
                dy, dx, pk = fase(a, b); fin.append((yc, xc, float(dy), float(dx), float(pk)))
        X = np.array([[1, 0, w[1] - CXP, -(w[0] - CYP)] for w in fin] + [[0, 1, w[0] - CYP, (w[1] - CXP)] for w in fin], float)
        Y = np.array([w[3] for w in fin] + [w[2] for w in fin], float)
        ds = np.linalg.lstsq(X, Y, rcond=None)[0]           # [tx, ty, ds, dθ(rad)] : la capa de Pere és a +(dx,dy) de la meva
        rms = float(np.sqrt(np.mean([w[2] ** 2 + w[3] ** 2 for w in fin])))
        marca(f"iteració {it}: {len(fin)} finestres · rms offset {rms:.2f} px · correcció t=({ds[0]:.2f},{ds[1]:.2f}) escala {1+ds[2]:.5f} rot {np.degrees(ds[3]):.4f}° · resposta mediana {np.median([w[4] for w in fin]):.1f}")
        # aplica la correcció (similitud al voltant del disc de Pere)
        C = np.array([[1 + ds[2], -ds[3], 0], [ds[3], 1 + ds[2], 0]], float); C[:, 2] = [ds[0] + CXP - (1 + ds[2]) * CXP + ds[3] * CYP, ds[1] + CYP - ds[3] * CXP - (1 + ds[2]) * CYP]
        M1 = (C @ np.vstack([M1, [0, 0, 1]]))[:2]
        if rms < 0.3: break
    hbw = cv2.warpAffine(hb, M1, (Wp, Hp), flags=cv2.INTER_LINEAR); fin = []
    for r_ in (1.6, 2.4, 3.3):
        for az in np.arange(0, 360, 45):
            yc = int(CYP + r_ * RS * np.sin(np.radians(az))); xc = int(CXP + r_ * RS * np.cos(np.radians(az)))
            a = hp[yc - 256:yc + 256, xc - 256:xc + 256]; b = hbw[yc - 256:yc + 256, xc - 256:xc + 256]
            if a.shape != (512, 512) or (np.abs(a) > 0).mean() < 0.6 or (np.abs(b) > 0).mean() < 0.6: continue
            dy, dx, pk = fase(a, b); fin.append({"yc": yc, "xc": xc, "r_Rsol": r_, "dy": float(dy), "dx": float(dx), "resposta": float(pk)})
    rms = float(np.sqrt(np.mean([w["dy"] ** 2 + w["dx"] ** 2 for w in fin]))); p95 = float(np.percentile([np.hypot(w["dy"], w["dx"]) for w in fin], 95))
    sol = M1 @ np.array([cxl, cyl, 1.0])
    out = {"M_llenc_a_v23": M1.tolist(), "theta_inicial_deg": float(th), "finestres": fin, "rms_offset_px": rms, "p95_offset_px": p95,
           "sol_a_v23": [float(sol[0]), float(sol[1])], "disc_C2_v23": [CXP, CYP], "dist_sol_disc_px": float(np.hypot(sol[0] - CXP, sol[1] - CYP)),
           "escala_total": float(np.hypot(M1[0, 0], M1[1, 0])), "rotacio_total_deg": float(np.degrees(np.arctan2(M1[1, 0], M1[0, 0])))}
    json.dump(out, open(os.path.join(CAU, "geometria_v23.json"), "w"), indent=1)
    marca(f"FET 2b · rotació {out['rotacio_total_deg']:.3f}° escala {out['escala_total']:.5f} · {len(fin)} finestres rms {rms:.2f} px p95 {p95:.2f} px · Sol a {out['dist_sol_disc_px']:.1f} px del disc C2")

if __name__ == "__main__":
    main()
