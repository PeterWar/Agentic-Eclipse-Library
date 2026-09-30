"""V24b · la vora amb textura real i la màscara adaptativa (ordre de Pere).

1. DESAJUST NEGRE (marca verda): la capa opaca fins a 458 px tapava les
   perles de la V23 (la seva llum comença a mediana 454,5 i en alguns
   sectors a 446). Màscara ADAPTATIVA per azimut: la capa acaba 1,5 px
   abans d'on comença la llum del composite V23, sector a sector.
2. PERÍMETRE SENSE DETALL (marques blaves): el camp suau de la vora es
   substitueix per PEDESTAL + TEXTURA REAL — el residu científic estès
   (earthshine4_Gdisp, netejat i filtrat, vàlid fins a 0,975 R) remapat
   amb el mateix re-ancoratge i escalat a l'amplitud del disc interior.
"""
from __future__ import annotations
import json, math, os
import numpy as np, cv2

CAU = "cau_v21"
CXT = CYT = 495.8
S22 = 453.5 / 455.5018189723177        # el re-ancoratge de la tessel·la
MB_V = (6465.398680355321, 6752.632845814709)
POSV = (6257, 5969)                     # bbox del marc vell


def blur_norm(Z, m, s):
    return (cv2.GaussianBlur(Z * m, (0, 0), s)
            / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6))


def main():
    F = np.load(f"{CAU}/capa_fosca_px.npy").astype(np.float32) / 65535.0
    yy, xx = np.mgrid[0:991, 0:991].astype(np.float32)
    rr = np.hypot(xx - CXT, yy - CYT)
    az = np.arctan2(yy - CYT, xx - CXT)

    # --- 2) TEXTURA REAL a la vora ---
    Gd = np.nan_to_num(np.load(f"{CAU}/earthshine4_Gdisp.npy"))
    dav = np.load(f"{CAU}/earthshine4_dav.npy").astype(np.float32)
    # remap al marc reancorat (mateixa transformació que v22_reancora)
    cxt_v = MB_V[0] - POSV[1]; cyt_v = MB_V[1] - POSV[0]
    mx = (cxt_v + (xx - CXT) / S22).astype(np.float32)
    my = (cyt_v + (yy - CYT) / S22).astype(np.float32)
    T = cv2.remap(Gd, mx, my, cv2.INTER_LINEAR, borderValue=0)
    Tm = cv2.remap(dav, mx, my, cv2.INTER_LINEAR, borderValue=0)
    # passa-alt de la textura (el pedestal suau ja el porta la capa)
    HP = T - blur_norm(T, (Tm > 0.5).astype(np.float32), 8.0)
    HP *= (Tm > 0.5)
    # amplitud objectiu: el passa-alt del disc interior de la capa fosca
    g = F[..., 1]
    mint = (rr > 340) & (rr < 420)
    hp_int = g - blur_norm(g, (rr < 470).astype(np.float32), 8.0)
    s_obj = float(hp_int[mint].std())
    anell = (rr >= 425) & (rr < 470) & (Tm > 0.5)
    s_vora = float(HP[anell].std()) if anell.sum() else 1.0
    kk = s_obj / max(s_vora, 1e-9)
    print(f"textura de vora: σ objectiu {s_obj:.4f} · σ residu {s_vora:.4f} · "
          f"factor {kk:.4f}")
    # el pedestal de la vora: el que la capa ja porta, SUAVITZAT (el camp
    # suau actual), i hi sumem la textura
    zona = (rr >= 428) & (rr < 470)
    w = np.clip((rr - 428.0) / 6.0, 0, 1)
    F2 = F.copy()
    for c in range(3):
        ped = blur_norm(F[..., c], (rr < 480).astype(np.float32), 5.0)
        nou = ped + HP * kk * 1.4     # èmfasi lleu del perímetre (Pere: «rascar més detall»)
        F2[..., c] = np.where(zona, F[..., c] * (1 - w) + nou * w, F[..., c])
    np.save(f"{CAU}/capa_fosca_px.npy",
            np.clip(np.rint(np.clip(F2, 0, 1) * 65535), 0, 65535).astype(np.uint16))

    # --- 1) MÀSCARA ADAPTATIVA per azimut ---
    Rllum = np.load(f"{CAU}/Rllum_v23.npy")          # 720 sectors, marc V23
    NA = len(Rllum)
    # suavitzat azimutal curt i marge d'1,5 px
    Rl = np.convolve(np.r_[Rllum[-10:], Rllum, Rllum[:10]],
                     np.ones(7) / 7, "same")[10:-10] - 1.5
    ai = np.clip(((az + np.pi) / (2 * np.pi) * NA).astype(int), 0, NA - 1)
    Rmask = Rl[ai]
    m = np.clip((Rmask - rr) / 2.0, 0, 1).astype(np.float32)
    m = cv2.GaussianBlur(m, (0, 0), 1.0)
    np.save(f"{CAU}/capa_nat_msk.npy",
            np.clip(np.rint(m * 65535), 0, 65535).astype(np.uint16))
    print(f"màscara adaptativa: radi de tall mediana {np.median(Rl):.1f} px · "
          f"min {Rl.min():.1f} · max {Rl.max():.1f}")


if __name__ == "__main__":
    main()
