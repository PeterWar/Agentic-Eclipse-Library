#!/usr/bin/env python3
"""V25 LINEAL · etapa 2: la transformació llenç comú (8096×8960, nord amunt,
Sol al centre) → graella de la V23/V24 de Pere (10551×7506), MESURADA sobre la
corona mateixa: rotació + translació (escala 1, els dos llenços són el sensor
R6 a 2,1495 ″/px), registrant la base lineal contra la capa 10 de la V24
(1/125 s, corona interior) amb correlació de fase sobre ln I passa-alt.
Després, control per finestres: residu de rotació/escala i offsets locals.
"""
import os, sys, json, time, numpy as np, cv2
from scipy.ndimage import gaussian_filter
from psd_tools import PSDImage
AQUI = os.path.dirname(os.path.abspath(__file__)); CAU = os.path.join(AQUI, "cau_v25")
V24 = "/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/CapesTotalsV24.psb"
T0 = time.time()
def marca(t): print(f"[{time.time()-T0:6.1f} s] {t}", flush=True)

def prep(img, m, sig=6.0):
    """ln del valor, passa-alt, pes; per registrar entre corbes de to diferents."""
    x = np.where(m & (img > 0), np.log(np.maximum(img, 1e-9)), 0.0).astype(np.float32)
    mf = m.astype(np.float32)
    den = np.maximum(gaussian_filter(mf, sig), 1e-6)
    hp = np.where(m, x - gaussian_filter(x * mf, sig) / den, 0.0)
    return (hp * mf).astype(np.float32)

def fase(a, b):
    """Correlació de fase: desplaçament (dy, dx) de b respecte d'a, i resposta."""
    A = np.fft.rfft2(a); B = np.fft.rfft2(b)
    R = A * np.conj(B); R /= np.maximum(np.abs(R), 1e-12)
    c = np.fft.irfft2(R, s=a.shape)
    k = np.unravel_index(np.argmax(c), c.shape); pk = float(c[k])
    dy = k[0] if k[0] <= a.shape[0] // 2 else k[0] - a.shape[0]
    dx = k[1] if k[1] <= a.shape[1] // 2 else k[1] - a.shape[1]
    # subpíxel parabòlic
    def sub(cm, i, n):
        i0, i1, i2 = cm[(i - 1) % n], cm[i], cm[(i + 1) % n]
        d = i0 - 2 * i1 + i2
        return 0.0 if d == 0 else 0.5 * (i0 - i2) / d
    ddy = sub(c[:, k[1]], k[0], c.shape[0]); ddx = sub(c[k[0], :], k[1], c.shape[1])
    return dy + ddy, dx + ddx, pk / (np.std(c) * c.size ** 0 + 1e-12)

def main():
    base = np.load(os.path.join(CAU, "base_B_rgb16.npy")).astype(np.float32) / 65535.0
    mf = np.load(os.path.join(CAU, "mascara_fusio.npy"))
    Hl, Wl = mf.shape; cxl, cyl = Wl / 2.0, Hl / 2.0
    Lb = (base[..., 0] + 2 * base[..., 1] + base[..., 2]) / 4.0; del base
    psd = PSDImage.open(V24); Wp, Hp = psd.width, psd.height
    l10 = list(psd)[2]; assert l10.name.startswith("10_1-125s")
    x0, y0, x1, y1 = l10.bbox
    arr = l10.numpy("color"); msk = l10.numpy("mask") if l10.mask else None
    Lp = np.zeros((Hp, Wp), np.float32); Mp = np.zeros((Hp, Wp), bool)
    Lp[y0:y1, x0:x1] = (arr[..., 0] + 2 * arr[..., 1] + arr[..., 2]) / 4.0
    Mp[y0:y1, x0:x1] = True
    if msk is not None:                      # la màscara té el SEU rectangle (pot ser tot el llenç)
        mx0, my0, mx1, my1 = l10.mask.bbox
        MM = np.zeros((Hp, Wp), bool); MM[my0:my1, mx0:mx1] = msk[..., 0] > 0.5
        Mp &= MM
    Mp &= Lp > 0.02
    marca(f"capa 10 llegida {arr.shape} bbox {l10.bbox} · màscara {Mp.mean():.3f}")
    del arr, msk
    # només l'anell on la capa 10 té corona real: 1,05-2,2 R☉ al voltant del disc de la V23
    cxp, cyp, RSp = 5361.877, 3774.741, 440.6      # disc C2 de la V23 (research/128) i R☉ del llenç
    yy, xx = np.mgrid[0:Hp, 0:Wp].astype(np.float32); rp = np.hypot(yy - cyp, xx - cxp) / RSp; del yy, xx
    Mp &= (rp > 1.08) & (rp < 2.3)
    yy, xx = np.mgrid[0:Hl, 0:Wl].astype(np.float32); rl = np.hypot(yy - cyl, xx - cxl) / 440.603; del yy, xx
    Ml = mf & (rl > 1.08) & (rl < 2.3)
    hb = prep(Lb, Ml); hp = prep(Lp, Mp)
    # escombrada de rotació a ×8
    f = 8; sb = cv2.resize(hb, (Wl // f, Hl // f), interpolation=cv2.INTER_AREA); sp = cv2.resize(hp, (Wp // f, Hp // f), interpolation=cv2.INTER_AREA)
    S = (max(sb.shape[0], sp.shape[0]) + 64, max(sb.shape[1], sp.shape[1]) + 64)
    def pad(a):
        o = np.zeros(S, np.float32); o[:a.shape[0], :a.shape[1]] = a; return o
    P = pad(sp)
    def prova(th, img, cx, cy):
        M = cv2.getRotationMatrix2D((cx, cy), th, 1.0)
        r = cv2.warpAffine(img, M, (img.shape[1], img.shape[0]), flags=cv2.INTER_LINEAR)
        return fase(P, pad(r))
    cxb, cyb = cxl / f, cyl / f
    best = max(((prova(th, sb, cxb, cyb)[2], th) for th in np.arange(-180, 180, 1.0)), key=lambda t: t[0])
    marca(f"escombrada 1°: millor θ={best[1]:.0f}° resposta {best[0]:.3f}")
    th0 = best[1]
    best = max(((prova(th, sb, cxb, cyb)[2], th) for th in np.arange(th0 - 1.5, th0 + 1.5, 0.05)), key=lambda t: t[0])
    th1 = best[1]; marca(f"refinat 0,05°: θ={th1:.2f}°")
    # refinat a ×2 amb finestra al voltant
    f2 = 2; sb2 = cv2.resize(hb, (Wl // f2, Hl // f2), interpolation=cv2.INTER_AREA); sp2 = cv2.resize(hp, (Wp // f2, Hp // f2), interpolation=cv2.INTER_AREA)
    S2 = (max(sb2.shape[0], sp2.shape[0]) + 32, max(sb2.shape[1], sp2.shape[1]) + 32)
    def pad2(a):
        o = np.zeros(S2, np.float32); o[:a.shape[0], :a.shape[1]] = a; return o
    P2 = pad2(sp2)
    def prova2(th):
        M = cv2.getRotationMatrix2D((cxl / f2, cyl / f2), th, 1.0)
        r = cv2.warpAffine(sb2, M, (sb2.shape[1], sb2.shape[0]), flags=cv2.INTER_LINEAR)
        return fase(P2, pad2(r))
    res = [(prova2(th), th) for th in np.arange(th1 - 0.3, th1 + 0.3001, 0.02)]
    (dy, dx, pk), th2 = max(res, key=lambda t: t[0][2])
    marca(f"refinat ×2: θ={th2:.2f}° · desplaçament ×2 ({dy:.2f},{dx:.2f}) · resposta {pk:.3f}")
    # transformació completa a ×1: V23 = R(θ) al voltant del centre del llenç, després translació
    # fase(P, pad(r)) dona el desplaçament de r respecte de P: la capa de Pere és a (+dy,+dx) de la meva rotada
    ty, tx = dy * f2, dx * f2
    M1 = cv2.getRotationMatrix2D((cxl, cyl), th2, 1.0); M1[0, 2] += tx; M1[1, 2] += ty
    # comprovació a ×1 per finestres (offsets locals després d'aplicar M1)
    hbw = cv2.warpAffine(hb, M1, (Wp, Hp), flags=cv2.INTER_LINEAR)
    fin = []
    for (yc, xc) in [(cyp - 700, cxp - 700), (cyp - 700, cxp + 700), (cyp + 700, cxp - 700), (cyp + 700, cxp + 700), (cyp, cxp - 900), (cyp, cxp + 900)]:
        y0w, x0w = int(yc) - 384, int(xc) - 384
        a = hp[y0w:y0w + 768, x0w:x0w + 768]; b = hbw[y0w:y0w + 768, x0w:x0w + 768]
        if a.shape != (768, 768) or (np.abs(a) > 0).mean() < 0.3: continue
        ddy, ddx, r = fase(a, b); fin.append({"centre_yx": [int(yc), int(xc)], "dy": float(ddy), "dx": float(ddx), "resposta": float(r)})
    # residu de rotació/escala a partir de les finestres: (dx,dy) ~ a + b·(x−cx) + c·(y−cy)
    if len(fin) >= 3:
        Xs = np.array([[1, w["centre_yx"][1] - cxp, w["centre_yx"][0] - cyp] for w in fin], float)
        cx_ = np.linalg.lstsq(Xs, np.array([w["dx"] for w in fin]), rcond=None)[0]
        cy_ = np.linalg.lstsq(Xs, np.array([w["dy"] for w in fin]), rcond=None)[0]
        rot_res = float(np.degrees(0.5 * (cy_[1] - cx_[2]))); esc_res = float(0.5 * (cx_[1] + cy_[2]))
    else:
        rot_res = esc_res = float("nan")
    out = {"theta_deg": float(th2), "tx": float(tx), "ty": float(ty), "centre_rotacio_llenc": [cxl, cyl],
           "M_llenc_a_v23": M1.tolist(), "resposta_x2": float(pk), "finestres_x1": fin,
           "residu_rotacio_deg": rot_res, "residu_escala": esc_res,
           "rms_offset_finestres_px": float(np.sqrt(np.mean([w["dx"] ** 2 + w["dy"] ** 2 for w in fin]))) if fin else None}
    # on cau el centre del Sol del llenç a la V23, i el disc C2 de la V23
    sol = M1 @ np.array([cxl, cyl, 1.0]); out["sol_a_v23"] = [float(sol[0]), float(sol[1])]
    out["disc_C2_v23"] = [cxp, cyp]; out["dist_sol_disc_px"] = float(np.hypot(sol[0] - cxp, sol[1] - cyp))
    json.dump(out, open(os.path.join(CAU, "geometria_v23.json"), "w"), indent=1)
    marca(f"FET etapa 2 · θ {th2:.3f}° · t ({tx:.1f},{ty:.1f}) · finestres rms {out['rms_offset_finestres_px']} px · rot residual {rot_res:.4f}° · escala residual {esc_res:.5f}")

if __name__ == "__main__":
    main()
