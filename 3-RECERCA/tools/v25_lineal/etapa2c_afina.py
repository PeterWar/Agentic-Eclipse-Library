import os, json, numpy as np, cv2, importlib.util
spec = importlib.util.spec_from_file_location("e2b", "etapa2b_geometria_v23.py"); e2b = importlib.util.module_from_spec(spec); spec.loader.exec_module(e2b)
from psd_tools import PSDImage
CAU = "cau_v25"; RS = 440.603; CXP, CYP = 5361.877, 3774.741
G = json.load(open(f"{CAU}/geometria_v23.json")); M0 = np.array(G["M_llenc_a_v23"])
base = np.load(f"{CAU}/base_B_rgb16.npy").astype(np.float32) / 65535.0; mf = np.load(f"{CAU}/mascara_fusio.npy")
Hl, Wl = mf.shape; cxl, cyl = Wl / 2.0, Hl / 2.0
Lb = (base[..., 0] + 2 * base[..., 1] + base[..., 2]) / 4.0; del base
yy, xx = np.mgrid[0:Hl, 0:Wl].astype(np.float32); rl = np.hypot(yy - cyl, xx - cxl) / RS; del yy, xx
hb = e2b.prep(Lb, mf & (rl > 1.15) & (rl < 4.0)); del Lb, rl
psd = PSDImage.open(e2b.V24); Wp, Hp = psd.width, psd.height; hdr = psd._record.header
pl = psd._record.image_data.get_data(hdr)
Lp = sum(np.frombuffer(pl[c], ">u2").reshape(Hp, Wp).astype(np.float32) * w for c, w in ((0, 1), (1, 2), (2, 1))) / (4 * 65535.0)
yy, xx = np.mgrid[0:Hp, 0:Wp].astype(np.float32); rp = np.hypot(yy - CYP, xx - CXP) / RS; del yy, xx
hp = e2b.prep(Lp, (Lp > 0.02) & (rp > 1.15) & (rp < 4.0)); del Lp
def finestres(M1):
    hbw = cv2.warpAffine(hb, M1, (Wp, Hp), flags=cv2.INTER_LINEAR); fin = []
    for r_ in (1.5, 2.0, 2.6, 3.3):
        for az in np.arange(0, 360, 30):
            yc = int(CYP + r_ * RS * np.sin(np.radians(az))); xc = int(CXP + r_ * RS * np.cos(np.radians(az)))
            a = hp[yc - 256:yc + 256, xc - 256:xc + 256]; b = hbw[yc - 256:yc + 256, xc - 256:xc + 256]
            if a.shape != (512, 512) or (np.abs(a) > 0).mean() < 0.6 or (np.abs(b) > 0).mean() < 0.6: continue
            dy, dx, pk = e2b.fase(a, b); fin.append((yc, xc, float(dy), float(dx), float(pk)))
    return fin
def ajust(fin):
    f = [w for w in fin if np.hypot(w[2], w[3]) < 6 and w[4] > 30]
    X = np.array([[1, 0, w[1] - CXP, -(w[0] - CYP)] for w in f] + [[0, 1, w[0] - CYP, (w[1] - CXP)] for w in f], float)
    Y = np.array([w[3] for w in f] + [w[2] for w in f], float); Wt = np.sqrt(np.array([w[4] for w in f] * 2, float))
    ds = np.linalg.lstsq(X * Wt[:, None], Y * Wt, rcond=None)[0]; return ds, len(f)
def rms(fin):
    d = np.array([np.hypot(w[2], w[3]) for w in fin]); return float(np.sqrt(np.mean(np.minimum(d, 6) ** 2))), float(np.median(d)), float(np.percentile(d, 90))
def aplica(M1, ds, signe):
    s = 1 + signe * ds[2]; t = signe * ds[3]
    C = np.array([[s, -t, 0], [t, s, 0]], float)
    C[:, 2] = [signe * ds[0] + CXP - s * CXP + t * CYP, signe * ds[1] + CYP - t * CXP - s * CYP]
    return (C @ np.vstack([M1, [0, 0, 1]]))[:2]
M1 = M0.copy(); fin = finestres(M1); print("inicial: rms/mediana/p90", rms(fin), flush=True)
for it in range(3):
    ds, n = ajust(fin)
    cands = [(rms(finestres(aplica(M1, ds, sg)))[1], sg) for sg in (+1, -1)]
    best = min(cands); print(f"it {it}: n={n} correcció t=({ds[0]:.2f},{ds[1]:.2f}) esc {1+ds[2]:.5f} rot {np.degrees(ds[3]):.4f}° · mediana amb +:{cands[0][0]:.2f} −:{cands[1][0]:.2f}", flush=True)
    M1 = aplica(M1, ds, best[1]); fin = finestres(M1)
    r = rms(fin); print(f"   després: rms/mediana/p90 {r}", flush=True)
    if r[1] < 0.35: break
sol = M1 @ np.array([cxl, cyl, 1.0])
G.update({"M_llenc_a_v23": M1.tolist(), "finestres": [{"yc": w[0], "xc": w[1], "dy": w[2], "dx": w[3], "resposta": w[4]} for w in fin],
          "rms_offset_px": r[0], "mediana_offset_px": r[1], "p90_offset_px": r[2], "sol_a_v23": [float(sol[0]), float(sol[1])],
          "dist_sol_disc_px": float(np.hypot(sol[0] - CXP, sol[1] - CYP)), "escala_total": float(np.hypot(M1[0, 0], M1[1, 0])),
          "rotacio_total_deg": float(np.degrees(np.arctan2(M1[1, 0], M1[0, 0]))), "nota": "afinat 2c: similitud ajustada a les finestres, robust (|d|<6, resposta>30), signe comprovat"})
json.dump(G, open(f"{CAU}/geometria_v23.json", "w"), indent=1)
print("FET 2c ·", {k: G[k] for k in ("rotacio_total_deg", "escala_total", "rms_offset_px", "mediana_offset_px", "p90_offset_px", "dist_sol_disc_px")})
