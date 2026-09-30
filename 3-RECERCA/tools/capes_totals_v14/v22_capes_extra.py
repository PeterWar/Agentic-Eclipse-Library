"""V22 · les dues capes de comparació, amb la MATEIXA recepta de display que
la capa earthshine (parpelleig just):

  · DSC06987 — el fotograma de 8 s de la Sony sol, al marc lunar: vel del
    model comprimit ×0,30, residu pel Wiener mesurat, realç ×12, mateixa
    finestra tonal. La dada és NOMÉS d'aquest fotograma.
  · LROC NASA — el mapa d'albedo renderitzat a l'orientació PREDITA per
    l'efemèride (de421 + IAU 2009; nord del llenç per les estrelles),
    estirament de finestra propi.
"""
from __future__ import annotations
import json, math, os, sys
import numpy as np, cv2

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v21")
sys.path.insert(0, AQUI)
from v21_earthshine_v4 import prepara, fes_neteja

MB = (6465.398680355321, 6752.632845814709)
RL = 455.5018189723177
A_REALC = 12.0


def wiener_fft(Z, H, W):
    fy = np.fft.fftfreq(H)[:, None]; fx = np.fft.rfftfreq(W)[None, :]
    fr = np.hypot(fy, fx)
    lam = np.where(fr > 1e-9, 1.0 / np.maximum(fr, 1e-9), 1e9)
    pl = np.log([2.0, 4.0, 8.0, 16.0, 32.0, 64.0])
    pg = np.array([0.06, 0.06, 0.71, 0.96, 0.995, 1.0])
    G = np.interp(np.log(np.clip(lam, 2.0, 64.0)), pl, pg).astype(np.float32)
    return np.fft.irfft2(np.fft.rfft2(Z) * G, s=Z.shape).astype(np.float32)


def display(G2, rr, netd, dav, H, W, realc_map=None):
    """la recepta de la capa natural, idèntica per a totes les capes."""
    if realc_map is not None:
        G2 = G2 * realc_map
    residu = netd(G2)
    vel = G2 - residu
    residu = wiener_fft(residu, H, W) * dav
    residu *= np.clip((0.985 - rr) / 0.015, 0, 1).astype(np.float32)
    nivc = float(np.median(G2[rr < 0.5]))
    G2d = np.where(dav, nivc + 0.30 * (vel - nivc) + residu, G2)
    dins1 = rr < 0.85
    p1, p99 = np.percentile(G2d[dins1], 1), np.percentile(G2d[dins1], 99)
    lo = p1 - 0.30 * (p99 - p1); hi = p99 + 0.10 * (p99 - p1)
    g8 = ((G2d - lo) / max(hi - lo, 1e-9)).astype(np.float32)
    g8 = np.where(g8 > 0.80, 0.80 + 0.17 * np.tanh((g8 - 0.80) / 0.17), g8)
    g8 = np.where(g8 < 0.10, 0.10 - 0.09 * np.tanh((0.10 - g8) / 0.09), g8)
    return np.clip(g8, 0, 1)


def main():
    IM, tot, rr, bb = prepara()
    x0, y0, x1, y1 = bb; H, W = y1 - y0, x1 - x0
    netd, dav = fes_neteja(tot, rr, (H, W), r_aval=0.995)
    msk = np.load(f"{CAU}/capa_nat_msk.npy")          # la mateixa màscara

    # --- DSC06987 sol, amb el seu propi realç (recepta idèntica) ---
    G87 = IM["DSC06987"]
    reb = json.load(open(f"{CAU}/earthshine4_rebut.json"))
    E87 = wiener_fft(netd(G87), H, W) * dav
    niv87 = float(np.median(G87[rr < 0.85]))
    f_nucli = np.clip((0.88 - rr) / 0.03, 0, 1).astype(np.float32)
    f_vora = np.clip((0.965 - rr) / 0.02, 0, 1).astype(np.float32)
    fada = f_nucli + 0.35 * (1 - f_nucli) * f_vora
    realc = 1.0 + A_REALC * (E87 / niv87) * fada
    g87 = display(G87, rr, netd, dav, H, W, realc_map=realc)
    px87 = np.dstack([g87] * 3)
    np.save(f"{CAU}/capa_6987_px.npy",
            np.clip(np.rint(px87 * 65535), 0, 65535).astype(np.uint16))
    print(f"DSC06987: mediana {np.median(g87[rr<0.9]):.3f}")

    # --- LROC NASA ---
    g0 = np.load(f"{CAU}/earthshine4_lroc.npy").astype(np.float32)
    m = rr < 0.97
    gl = cv2.GaussianBlur(g0, (0, 0), 2.0)
    p1, p99 = np.percentile(gl[m], 1), np.percentile(gl[m], 99)
    lo = p1 - 0.30 * (p99 - p1); hi = p99 + 0.10 * (p99 - p1)
    gL = np.clip((gl - lo) / max(hi - lo, 1e-9), 0, 1).astype(np.float32)
    np.save(f"{CAU}/capa_lroc_px.npy",
            np.clip(np.rint(np.dstack([gL] * 3) * 65535), 0, 65535).astype(np.uint16))
    print(f"LROC: mediana {np.median(gL[m]):.3f}")

    mm = msk.astype(np.float32) / 65535.0
    for nom, g in (("v22_6987", g87), ("v22_lroc", gL)):
        cv2.imwrite(f"/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/"
                    f"423091c7-0adc-498a-80f4-99666c4274fa/scratchpad/{nom}.png",
                    (np.clip(g * mm, 0, 1) * 255).astype(np.uint8))


if __name__ == "__main__":
    main()
