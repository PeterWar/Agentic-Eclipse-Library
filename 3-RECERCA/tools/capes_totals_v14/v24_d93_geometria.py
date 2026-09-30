"""V24d · geometria: el revelat de Pere (DSC06993.psb) al marc de la tessel·la.

Pere (01-09): «la part del perímetre marcada en verd s'adapta molt millor al
contorn real que el que has fet tu». Causa mesurada: les tessel·les lunars
porten GUARDA de 8 px dins del limbe (ciència: fora corona/protuberàncies) —
la capa V24 no tenia DADA de 447 a 453,5 px i la banda era pedestal+textura.

Aquest pas porta el PSB de Pere al marc de la tessel·la V24 amb la cadena
exacta (cap rotació a mà):

  tessel·la nova → (invers del re-ancoratge ×0,9956) → llenç V16 →
  sv.enrere → v15 → comú → raw Sony (àncora solar de la base; el DSC06993
  ÉS la base: θ=0, t=0) → + offset del retall del revelat (MESURAT per
  correlació amb la tessel·la lineal del mateix RAW).

Sortides a cau_v21:
  d93_pere_tile.npy   (991,991,3) float32 — el revelat de Pere al marc nou
  d93_pere_geo.json   offset mesurat, correlació, límits
"""
from __future__ import annotations
import json, math, os, sys, time

import numpy as np
import cv2

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v21")
sys.path.insert(0, AQUI)
import fes_v15 as F15
import fes_v17 as F17

PSB = "/Users/USUARI/Downloads/DSC06993.psb"
MB_CANVAS = (6465.398680355321, 6752.632845814709)
POSV = (6257, 5969)                       # (y0, x0) de la tessel·la vella
CXV, CYV = MB_CANVAS[0] - POSV[1], MB_CANVAS[1] - POSV[0]   # 496.399, 495.633
CXN = CYN = 495.8
S22 = 453.5 / 455.5018189723177
T0 = time.time()


def marca(t):
    print(f"[{time.time()-T0:7.1f}s] {t}", flush=True)


def coords_raw():
    """raw Sony (x,y) per a cada píxel de la tessel·la NOVA 991×991."""
    sv = F17.SV16()
    geo15 = F15.Geo(padx=3387.0, pady=5109.0)
    RUN = F15.RUN_SONY
    sys.path.insert(0, os.path.join(RUN, "codi"))
    import comu
    run = comu.Run.obre(RUN)
    S13 = run.llegeix_rebut("F1.3_registre.json")["fotogrames"]
    vb = S13["DSC06993.ARW"]
    solb = np.array([vb["sol_x"], vb["sol_y"]])
    yy, xx = np.mgrid[0:991, 0:991].astype(np.float32)
    # invers del re-ancoratge: marc nou → marc vell → llenç
    Xv = (POSV[1] + CXV + (xx - CXN) / S22).astype(np.float32)
    Yv = (POSV[0] + CYV + (yy - CYN) / S22).astype(np.float32)
    x15, y15 = sv.enrere(Xv, Yv)
    dX, dY = geo15.v15_a_comu(x15, y15)
    rbx, rby = geo15.comu_a_raw_sony(dX, dY, solb)
    return rbx.astype(np.float32), rby.astype(np.float32)


def main():
    from psd_tools import PSDImage
    marca("cadena llenç→raw…")
    rbx, rby = coords_raw()
    marca(f"raw coords: x {np.nanmin(rbx):.0f}..{np.nanmax(rbx):.0f} · "
          f"y {np.nanmin(rby):.0f}..{np.nanmax(rby):.0f}")

    marca("obrint el PSB de Pere…")
    p = PSDImage.open(PSB)
    L = p[0].numpy()[..., :3].astype(np.float32)      # el seu revelat, RGB
    marca(f"capa 0: {L.shape}")

    # ── offset del retall del revelat, MESURAT ───────────────────────────
    # referència: la tessel·la lineal del mateix RAW (interior del disc),
    # passa-alt als dos costats, NCC sobre l'anell 150-420 px del disc.
    T93 = np.nan_to_num(np.load(f"{CAU}/lluna_sony_DSC06993_lineal.npy"))[..., 1]
    # la tessel·la vella al marc NOU (mateixa transformació que el muntatge)
    yy, xx = np.mgrid[0:991, 0:991].astype(np.float32)
    mx = (CXV + (xx - CXN) / S22).astype(np.float32)
    my = (CYV + (yy - CYN) / S22).astype(np.float32)
    Tn = cv2.remap(T93, mx, my, cv2.INTER_LINEAR, borderValue=0)
    rr = np.hypot(xx - CXN, yy - CYN)
    zona = (rr > 150) & (rr < 420) & (Tn > 0)

    def hp(Z):
        return Z - cv2.GaussianBlur(Z, (0, 0), 6.0)

    Th = hp(Tn)
    G = L[..., 1]
    H, W = G.shape
    millors = []
    for oy in range(-16, 17, 2):
        for ox in range(-16, 17, 2):
            sx = np.clip(rbx + ox, 0, W - 2)
            sy = np.clip(rby + oy, 0, H - 2)
            P = cv2.remap(G, sx, sy, cv2.INTER_LINEAR, borderValue=0)
            Ph = hp(P)
            a, b = Th[zona], Ph[zona]
            c = float(np.corrcoef(a, b)[0, 1])
            millors.append((c, ox, oy))
    millors.sort(reverse=True)
    c0, ox0, oy0 = millors[0]
    marca(f"graella grossa: millor NCC {c0:.4f} a offset ({ox0:+d},{oy0:+d})")

    # refinat fi ±2 px a passos de 0,25
    def ncc(ox, oy):
        sx = np.clip(rbx + ox, 0, W - 2)
        sy = np.clip(rby + oy, 0, H - 2)
        P = cv2.remap(G, sx.astype(np.float32), sy.astype(np.float32),
                      cv2.INTER_LINEAR, borderValue=0)
        return float(np.corrcoef(Th[zona], hp(P)[zona])[0, 1])

    fins = [(ncc(ox0 + dx, oy0 + dy), ox0 + dx, oy0 + dy)
            for dy in np.arange(-2, 2.01, 0.25)
            for dx in np.arange(-2, 2.01, 0.25)]
    fins.sort(reverse=True)
    cf, oxf, oyf = fins[0]
    marca(f"refinat: NCC {cf:.4f} a offset ({oxf:+.2f},{oyf:+.2f})")

    # ── el revelat de Pere al marc nou ───────────────────────────────────
    out = np.zeros((991, 991, 3), np.float32)
    sx = np.clip(rbx + oxf, 0, W - 2).astype(np.float32)
    sy = np.clip(rby + oyf, 0, H - 2).astype(np.float32)
    for c in range(3):
        out[..., c] = cv2.remap(L[..., c], sx, sy, cv2.INTER_LINEAR,
                                borderValue=0)
    np.save(f"{CAU}/d93_pere_tile.npy", out)
    json.dump({"psb": PSB, "offset_raw_a_psb": [oxf, oyf], "ncc": cf,
               "ncc_graella": c0, "nota": "psb = raw + offset; cadena "
               "canvas→raw exacta de v21_lluna_tren (base, θ=0)"},
              open(f"{CAU}/d93_pere_geo.json", "w"), indent=1)
    marca("d93_pere_tile.npy desat")


if __name__ == "__main__":
    main()
