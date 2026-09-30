"""j2 (V97) · A2, el «polígon» B/G: estructura de ln(B/G) lligada a la isofota (d 200–560 px del limbe), a qualsevol imatge lineal RGB.
Per a cada imatge: hp = ln(B/G) − la seva mitjana local (σ 25, normalitzada pel suport); q = ln G suavitzat σ 6 (la isofota);
perfil = mitjana de hp per 160 quantils de q a la zona; mètrica = rms del perfil. Nul: el mateix perfil amb la isofota girada
60/90/135/200° al voltant del Sol (mediana). Ràtio ≈ 1 → cap graó de color lligat a la brillantor. També el salt màxim del perfil
(|Δ| entre quantils veïns, suavitzat 3) per comparar amb el llindar de Codex |Δln(B/G)| ≤ 0,002.
Ús: j2_poligon.py <sortida.json> etiqueta=ruta.npy …"""
import sys
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent))
from jutge_comu import SOL, LLUNA, RLLUNA, dist_limbe, desa
BOX = (int(LLUNA[0] - 800), int(LLUNA[1] - 800), int(LLUNA[0] + 800), int(LLUNA[1] + 800)); x0, y0, x1, y1 = BOX
d = dist_limbe(BOX); out = {}
for arg in sys.argv[2:]:
    et, ruta = arg.split('=', 1); f = np.asarray(np.load(ruta, mmap_mode='r')[y0:y1, x0:x1], np.float32)
    G = f[..., 1]; B = f[..., 2]; ok = (G > 0) & (B > 0) & np.isfinite(G) & np.isfinite(B)
    lbg = np.where(ok, np.log(np.maximum(B, 1e-9) / np.maximum(G, 1e-9)), 0).astype(np.float32)
    hp = lbg - cv2.GaussianBlur(lbg * ok, (0, 0), 25) / np.maximum(cv2.GaussianBlur(ok.astype(np.float32), (0, 0), 25), 1e-6)
    q = cv2.GaussianBlur(np.where(ok, np.log(np.maximum(G, 1e-9)), 0).astype(np.float32), (0, 0), 6); zona = ok & (d > 200) & (d < 560)
    def perfil(qm):
        v = qm[zona]; e = np.quantile(v, np.linspace(0, 1, 161)); idx = np.clip(np.searchsorted(e, v) - 1, 0, 159)
        s = np.bincount(idx, hp[zona], 160); n = np.bincount(idx, None, 160); return s / np.maximum(n, 1)
    P = perfil(q); rms = float(np.sqrt(np.mean((P - P.mean()) ** 2)))
    def rms_de(Q): return float(np.sqrt(np.mean((Q - Q.mean()) ** 2)))
    fons = float(np.median(q[zona]))
    nul = float(np.median([rms_de(perfil(cv2.warpAffine(q, cv2.getRotationMatrix2D((SOL[0] - x0, SOL[1] - y0), a, 1.0), (q.shape[1], q.shape[0]), borderValue=fons))) for a in (60, 90, 135, 200)]))
    Ps = cv2.GaussianBlur(P.reshape(1, -1).astype(np.float32), (0, 0), 3).ravel(); salt = float(np.max(np.abs(np.diff(Ps))) * 3)
    out[et] = dict(rms=rms, nul=nul, ratio=rms / nul, salt_max_aprox=salt, perfil=[round(float(x), 5) for x in P])
    print(et, f'rms {rms:.5f} nul {nul:.5f} ràtio {rms/nul:.2f} salt {salt:.4f}', flush=True)
desa(sys.argv[1], out)
