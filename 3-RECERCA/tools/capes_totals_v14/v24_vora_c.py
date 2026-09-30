"""V24c · el perímetre amb TOT el detall que la dada dona.

Pere: «encara falta molt detall al perímetre». El residu que hi posava
passava pel Wiener de producte (λ<4 ×0,06 · 4-8 ×0,71) — pensat per al disc,
mata les escales fines de la vora. Per a l'ANELL del perímetre es regenera el
residu estès amb un Wiener SUAU (λ<4 ×0,35 · 4-8 ×0,85 · resta 1): més gra,
tot el detall 4-40 px viu. Amplificació ×2,2 del contrast del disc interior,
DECLARADA. El disc interior no es toca.
"""
from __future__ import annotations
import json, math, os, sys
import numpy as np, cv2

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v21")
sys.path.insert(0, AQUI)
from v21_earthshine_v4 import prepara, fes_neteja, COMPS

CXT = CYT = 495.8
S22 = 453.5 / 455.5018189723177
MB_V = (6465.398680355321, 6752.632845814709)
POSV = (6257, 5969)
R_INI = 395.0          # d'aquí enfora, la vora nova
EMFASI = 2.2


def blur_norm(Z, m, s):
    return (cv2.GaussianBlur(Z * m, (0, 0), s)
            / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6))


def main():
    # --- residu estès amb Wiener SUAU ---
    IM, tot, rr0, bb = prepara()
    x0, y0, x1, y1 = bb; H0, W0 = y1 - y0, x1 - x0
    netd, dav = fes_neteja(tot, rr0, (H0, W0), r_aval=0.995)
    reb = json.load(open(f"{CAU}/earthshine4_rebut.json"))
    Wc = reb["pesos"]
    P = {}
    for k, (fs, ts, tren) in COMPS.items():
        w = np.array(ts) / sum(ts)
        P[k] = sum(netd(IM[f]) * wi for f, wi in zip(fs, w)).astype(np.float32)
    # destripat (el mateix held-out ja validat: mediana per columna/fila del HP)
    def destripa(Z):
        hp = Z - cv2.GaussianBlur(Z, (0, 0), 6.0)
        col = np.nan_to_num(np.nanmedian(np.where(dav, hp, np.nan), axis=0))
        Z = Z - np.where(dav, col[None, :], 0)
        hp = Z - cv2.GaussianBlur(Z, (0, 0), 6.0)
        fil = np.nan_to_num(np.nanmedian(np.where(dav, hp, np.nan), axis=1))
        return Z - np.where(dav, fil[:, None], 0)
    E = destripa(sum(P[k] * Wc[k] for k in P).astype(np.float32))
    fy = np.fft.fftfreq(H0)[:, None]; fx = np.fft.rfftfreq(W0)[None, :]
    fr = np.hypot(fy, fx)
    lam = np.where(fr > 1e-9, 1.0 / np.maximum(fr, 1e-9), 1e9)
    pl = np.log([2.0, 4.0, 8.0, 16.0, 32.0, 64.0])
    pg = np.array([0.35, 0.35, 0.85, 1.0, 1.0, 1.0])     # Wiener SUAU de vora
    G = np.interp(np.log(np.clip(lam, 2.0, 64.0)), pl, pg).astype(np.float32)
    E = np.fft.irfft2(np.fft.rfft2(E) * G, s=E.shape).astype(np.float32) * dav
    np.save(f"{CAU}/vora_residu_viu.npy", E)
    print("residu viu de vora generat")

    # --- a la tessel·la re-ancorada ---
    yy, xx = np.mgrid[0:991, 0:991].astype(np.float32)
    rr = np.hypot(xx - CXT, yy - CYT)
    cxt_v = MB_V[0] - POSV[1]; cyt_v = MB_V[1] - POSV[0]
    mx = (cxt_v + (xx - CXT) / S22).astype(np.float32)
    my = (cyt_v + (yy - CYT) / S22).astype(np.float32)
    T = cv2.remap(E, mx, my, cv2.INTER_LINEAR, borderValue=0)
    Tm = cv2.remap(dav.astype(np.float32), mx, my, cv2.INTER_LINEAR,
                   borderValue=0) > 0.5
    HP = (T - blur_norm(T, Tm.astype(np.float32), 10.0)) * Tm

    F = np.load(f"{CAU}/capa_fosca_px.npy").astype(np.float32) / 65535.0
    np.save(f"{CAU}/capa_fosca_VELLA.npy",
            (F * 65535).astype(np.uint16))          # per al pedaç del composite
    g = F[..., 1]
    mint = (rr > 320) & (rr < 390)
    hp_int = g - blur_norm(g, (rr < 470).astype(np.float32), 10.0)
    s_obj = float(hp_int[mint].std())
    anell = (rr >= R_INI) & (rr < 460) & Tm
    s_v = float(HP[anell].std())
    kk = EMFASI * s_obj / max(s_v, 1e-9)
    print(f"vora: σ int {s_obj:.4f} · σ residu viu {s_v:.2f} · factor {kk:.5f} "
          f"(èmfasi ×{EMFASI})")
    w = np.clip((rr - R_INI) / 8.0, 0, 1).astype(np.float32)
    F2 = F.copy()
    for c in range(3):
        ped = blur_norm(F[..., c], (rr < 480).astype(np.float32), 6.0)
        nou = ped + HP * kk
        F2[..., c] = np.where(rr >= R_INI, F[..., c] * (1 - w) + nou * w,
                              F[..., c])
    np.save(f"{CAU}/capa_fosca_px.npy",
            np.clip(np.rint(np.clip(F2, 0, 1) * 65535), 0, 65535).astype(np.uint16))
    msk = np.load(f"{CAU}/capa_nat_msk.npy").astype(np.float32) / 65535.0
    vis = np.clip(F2 * msk[..., None] * 2.2, 0, 1)
    cv2.imwrite("/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/"
                "423091c7-0adc-498a-80f4-99666c4274fa/scratchpad/v24c_vora.png",
                (vis * 255).astype(np.uint8)[..., ::-1])
    print("tessel·la amb vora viva desada (vista aclarida ×2,2)")


if __name__ == "__main__":
    main()
