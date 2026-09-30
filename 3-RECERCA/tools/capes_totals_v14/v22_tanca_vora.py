"""V22 · la vora del disc, per construcció suau (cap serrell possible).

De r=424 enfora el contingut es substitueix pel seu PROPI camp suau
radial-azimutal (mediana per anell de 2 px, suavitzada en azimut i en radi),
prolongat de 440 a 460 amb l'últim anell i un decaïment del 15 %. La fosa
interior (424-430) és contra el contingut ple. La màscara arriba a 458 (el
limbe de les capes 11-12 de Pere és a 453,5).
"""
import numpy as np, cv2

CAU = "cau_v21"
CXT = CYT = 495.8
R0, R1, R2 = 434.0, 446.0, 460.0


def repara(A):
    H, W = A.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rr = np.hypot(xx - CXT, yy - CYT)
    az = np.arctan2(yy - CYT, xx - CXT)
    NA = 1080
    ai = np.clip(((az + np.pi) / (2 * np.pi) * NA).astype(int), 0, NA - 1)
    NR = int((R1 - R0) / 2)
    ri = np.clip(((rr - R0) / 2.0).astype(int), 0, NR - 1)
    out = A.copy()
    un = A.ndim == 2
    for c in range(1 if un else A.shape[2]):
        Z = (A if un else A[..., c]).astype(np.float32)
        # camp suau: mediana per (anell 2 px × sector), suavitzada
        P = np.zeros((NR, NA), np.float32)
        for k in range(NR):
            s = (rr >= R0 + 2 * k) & (rr < R0 + 2 * (k + 1))
            zs = Z[s]; a_s = ai[s]
            med = np.zeros(NA, np.float32)
            # mediana per sector de 1080/36=30 sectors amples i interpola
            NS = 36
            si = (a_s * NS // NA).astype(int)
            vs = np.zeros(NS); 
            for q in range(NS):
                m = si == q
                vs[q] = np.median(zs[m]) if m.sum() > 3 else np.nan
            ok = np.isfinite(vs)
            idx = np.arange(NS)
            vs = np.interp(idx, idx[ok], vs[ok], period=NS)
            centres = (idx + 0.5) * NA / NS
            med = np.interp(np.arange(NA), centres, vs, period=NA)
            P[k] = med
        P = cv2.GaussianBlur(P, (0, 0), sigmaX=25, sigmaY=1.2)
        # dins 424-440: fosa del contingut cap al camp suau (suau ell mateix)
        zona = (rr >= R0) & (rr < R1)
        w = np.clip((rr[zona] - R0) / 5.0, 0, 1)
        suau = P[ri[zona], ai[zona]]
        nou = Z[zona] * (1 - w) + suau * w
        # de 440 a 460: l'últim anell estès amb decaïment
        zona2 = (rr >= R1) & (rr < R2)
        dec = 1.0 - 0.15 * np.clip((rr[zona2] - R1) / (R2 - R1), 0, 1)
        nou2 = P[NR - 1, ai[zona2]] * dec
        if un:
            out[zona] = nou.astype(out.dtype); out[zona2] = nou2.astype(out.dtype)
        else:
            out[..., c][zona] = nou.astype(out.dtype)
            out[..., c][zona2] = nou2.astype(out.dtype)
    return out


def main():
    for nom in ("capa_nat_px", "capa_6987_px", "capa_lroc_px"):
        A = np.load(f"{CAU}/{nom}.npy")
        np.save(f"{CAU}/{nom}.npy", repara(A))
        print(f"  {nom}: vora suau")
    H, W = 991, 991
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rr = np.hypot(xx - CXT, yy - CYT)
    m = cv2.GaussianBlur(np.clip((458.0 - rr) / 3.0, 0, 1).astype(np.float32),
                         (0, 0), 1.0)
    np.save(f"{CAU}/capa_nat_msk.npy",
            np.clip(np.rint(m * 65535), 0, 65535).astype(np.uint16))
    print("màscara 455→458")


if __name__ == "__main__":
    main()
