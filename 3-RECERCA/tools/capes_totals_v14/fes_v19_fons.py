"""CapesTotalsV19 — el fons per raig de Pere aplicat al llenç sencer de la V18.

Del `research/123`: al camp exterior l'artefacte és variació AL LLARG del raig
i el senyal és variació EN AZIMUT. La V19 = el save de Pere de la V18 (les 12
capes Vixen + la Sony + el Pasalt, byte a byte; fora només la còpia de marques)
MÉS dues capes noves a sobre:

- `FONS_PER_RAIG`: B = suavitzat gaussià normalitzat en ln r (σ=0,2) per raig
  del compost, amb mediana-11 (robusta a estrelles) i pesos a les vores (les
  «cantonades pintades» de Pere, sense pintar). Màscara EDITABLE = la rampa
  radial exacta de Pere (mesurada del seu V18-DesenfocRadialZoom: 0 fins a
  ~2,45 R☉, 1 des de ~3,25).
- `ESTRELLES`: reinjecció additiva (Photoshop: Linear Dodge) de les fonts
  puntuals que el fons esborra — contingut = clip(C − B_det, 0), màscara =
  discos suaus × rampa.

I la fusionada nova (RGBA, RAW). Portes: bony/croma a les 17 marques de les
dues rondes + escombrada de 24 sectors + supervivència d'estrelles + fidelitat
+ porta Photoshop. ⛔ Regles vives: blocs globals heretats fora (8BIM/8B64),
vistes al llenç sencer, el fitxer de Pere només lectura.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import warnings

import numpy as np
import cv2
from scipy.ndimage import median_filter

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU18 = os.path.join(AQUI, "cau_v18")
CAU19 = os.path.join(AQUI, "cau_v19")
CAUD = os.path.join(CAU19, "desenfoc")
CAUF = os.path.join(CAU19, "fons")
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "encaix_sony"))

B = "/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/"
SRC = B + "CapesTotalsV18.psb"
DST = B + "CapesTotalsV19.psb"
SOL = (6469.2, 6757.6)
RS = 455.5
SOL_CROP = (4273.2, 2633.6)      # el Sol al retall del DesenfocRadial de Pere
NT, NR = 8160, 1750              # rajos × mostres ln r (8160 = 24 sectors × 340)
R0, R1 = 1.5, 20.7               # R☉ (la cantonada més llunyana és a 20,54)
SIGMA_B = 0.20                   # composició (equivalent mesurat del zoom de Pere)
SIGMA_DET = 0.05                 # fons de detecció/fotometria (MAI el llis)
MED_K = 11
PREF_PX = 1.2
N_SECTORS = 24
warnings.filterwarnings("ignore", category=RuntimeWarning)
T0 = time.time()


def marca(txt):
    print(f"[{time.time()-T0:7.1f}s] {txt}", flush=True)


def main():
    os.makedirs(CAUF, exist_ok=True)

    # ---------- [1] el compost C del save de Pere (des dels caus verificats) ----------
    S16 = np.load(os.path.join(CAU19, "sony_v18_rgb16.npy"), mmap_mode="r")
    Mso = np.load(os.path.join(CAU19, "mask_v18.npy"), mmap_mode="r")
    V16 = np.load(os.path.join(CAU18, "vixen_sota_rgb16.npy"), mmap_mode="r")
    A8 = np.load(os.path.join(CAU18, "vixen_sota_alfa8.npy"), mmap_mode="r")
    H, W = Mso.shape
    m_sony = np.asarray(Mso, np.float32) / 65535.0
    a_vix = np.asarray(A8, np.float32) / 255.0
    C = np.empty((H, W, 3), np.uint16)
    for ch in range(3):
        C[..., ch] = np.clip(
            np.asarray(S16[..., ch], np.float32) * m_sony
            + np.asarray(V16[..., ch], np.float32) * a_vix * (1.0 - m_sony) + 0.5,
            0, 65535).astype(np.uint16)
    alfaT = m_sony + a_vix * (1.0 - m_sony)
    del a_vix
    marca(f"compost C fet ({W}x{H}) · cobertura mitjana {alfaT.mean():.4f}")

    # ---------- [2] la rampa de Pere, mesurada del seu retall ----------
    mkc = np.load(os.path.join(CAUD, "capa2_mask16.npy"), mmap_mode="r")
    mq = np.asarray(mkc[::2, ::2], np.float32) / 65535.0
    hq, wq = mq.shape
    yyc = np.arange(hq, dtype=np.float32)[:, None] * 2
    xxc = np.arange(wq, dtype=np.float32)[None, :] * 2
    radc = np.hypot(xxc - SOL_CROP[0], yyc - SOL_CROP[1]) / RS
    r_taula = np.arange(1.8, 4.2, 0.02, dtype=np.float32)
    m_taula = np.empty_like(r_taula)
    for i, r0 in enumerate(r_taula):
        z = np.abs(radc - r0) < 0.01
        m_taula[i] = float(np.median(mq[z])) if z.sum() > 200 else np.nan
    bo = np.isfinite(m_taula)
    r_taula, m_taula = r_taula[bo], np.clip(m_taula[bo], 0, 1)
    m_taula = np.maximum.accumulate(m_taula)          # monòtona, com la seva
    del mq, radc
    dx = np.arange(W, dtype=np.float32) - np.float32(SOL[0])
    dy = np.arange(H, dtype=np.float32) - np.float32(SOL[1])
    rR = np.hypot(dx[None, :], dy[:, None]) / np.float32(RS)
    m = np.interp(rR, r_taula, m_taula, left=0.0, right=1.0).astype(np.float32)
    i50 = float(np.interp(0.5, m_taula, r_taula))
    marca(f"rampa de Pere: m=0,5 a r={i50:.2f} R☉ · 0→1 entre "
          f"{r_taula[m_taula > 0.01][0]:.2f} i {r_taula[m_taula > 0.99][0]:.2f}")

    # ---------- [3] maquinària polar ----------
    LNR0, LNR1 = np.log(R0), np.log(R1)
    DLNR = (LNR1 - LNR0) / (NR - 1)
    DTH = 2.0 * np.pi / NT
    th_g = np.arange(NT, dtype=np.float64) * DTH
    r_px = RS * np.exp(LNR0 + np.arange(NR, dtype=np.float64) * DLNR)
    MAPX = (SOL[0] + np.cos(th_g)[:, None] * r_px[None, :]).astype(np.float32)
    MAPY = (SOL[1] + np.sin(th_g)[:, None] * r_px[None, :]).astype(np.float32)
    IDX_R = np.arange(NR)
    r_of_bin = np.exp(LNR0 + IDX_R * DLNR)

    def a_polar(img):
        return cv2.remap(img, MAPX, MAPY, interpolation=cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_CONSTANT, borderValue=0.0)

    # ⛔ el PES és la COBERTURA, no el llenç: les cantonades del llenç són més
    # enllà de la vora de dada de la Sony (14,8 R☉) i el seu negre s'esmunyiria
    # dins del fons prop de la vora. Amb el pes de cobertura, B s'hi estén per
    # raig (farciment endavant) — l'esperit de les cantonades pintades de Pere.
    w_pol = a_polar(alfaT.astype(np.float32))
    VALID = w_pol > 0.5

    def omple_endavant(a, valid):
        idx = np.where(valid, IDX_R[None, :], 0)
        np.maximum.accumulate(idx, axis=1, out=idx)
        return np.take_along_axis(a, idx, axis=1)

    def gauss_lnr(a, sig_mostres):
        k = min(2 * int(3 * sig_mostres) + 1, 2 * NR - 1)
        return cv2.GaussianBlur(a, (k, 1), sigmaX=sig_mostres, sigmaY=0,
                                borderType=cv2.BORDER_REPLICATE)

    def fons_polar(pol, sigma_lnr):
        pol_ff = omple_endavant(pol, VALID)
        pol_med = median_filter(pol_ff, size=(1, MED_K), mode="nearest")
        s = sigma_lnr / DLNR
        num = gauss_lnr(pol_med * w_pol, s)
        den = gauss_lnr(w_pol, s)
        Bp = num / np.maximum(den, 1e-6)
        return omple_endavant(Bp, den > 1e-3)

    lnr_c = np.log(np.maximum(rR, R0))
    IXI = np.clip((lnr_c - LNR0) / DLNR, 0, NR - 1).astype(np.float32)
    del lnr_c
    th_c = np.mod(np.arctan2(dy[:, None], dx[None, :]), 2 * np.pi)
    IYI = np.clip(th_c / DTH, 0, NT - 1e-3).astype(np.float32)
    del th_c
    marca("maquinària polar a punt")

    # ---------- [4] B (σ0,2) i B_det (σ0,05) al llenç ----------
    # ⛔ el compost porta la fosa de la màscara Sony PREMULTIPLICADA (a la vora
    # de cobertura el valor és cel×màscara, no cel): el fons menja C/α — el
    # valor de veritat — i B estén el CEL, no l'esvaït de la vora.
    inv_a = (1.0 / np.maximum(alfaT, 0.02)).astype(np.float32)
    B16 = np.empty((H, W, 3), np.uint16)
    Bdet16 = np.empty((H, W, 3), np.uint16)
    dins_grella = rR >= (R0 + 0.02)
    for ch in range(3):
        pf = cv2.GaussianBlur(np.asarray(C[..., ch], np.float32) * inv_a,
                              (0, 0), PREF_PX)
        pol = a_polar(pf)
        del pf
        for sig, dst in ((SIGMA_B, B16), (SIGMA_DET, Bdet16)):
            Bp = fons_polar(pol, sig)
            Bp = np.vstack([Bp, Bp[:2]])
            Bc = cv2.remap(Bp, IXI, IYI, interpolation=cv2.INTER_LINEAR,
                           borderMode=cv2.BORDER_REPLICATE)
            # dins de la graella no hi ha B: el raster duu C (la màscara hi és 0)
            dst[..., ch] = np.where(dins_grella,
                                    np.clip(Bc + 0.5, 0, 65535),
                                    C[..., ch]).astype(np.uint16)
            del Bp, Bc
        del pol
        marca(f"fons B i B_det del canal {ch}")

    # ---------- [5] estrelles ----------
    L1 = (C[..., 0].astype(np.float32) + C[..., 1] + C[..., 2]) / 3.0
    LBd = (Bdet16[..., 0].astype(np.float32) + Bdet16[..., 1] + Bdet16[..., 2]) / 3.0
    D = L1 - LBd
    del LBd
    # (provat i descartat: el filtre adaptat no hi guanya res perquè el gra del
    # drizzle està correlacionat a l'escala de la PSF — 143 deteccions contra
    # 343 sense; la detecció va al mapa cru amb llindars locals)
    NBb = 64
    lg0, lg1 = np.log(2.5), np.log(20.0)
    pas_b = (lg1 - lg0) / NBb
    bidx = ((np.log(np.maximum(rR, 1e-3)) - lg0) / pas_b).astype(np.int16)
    # ⛔ la detecció NOMÉS a cobertura plena (a les vores parcials D barreja el
    # compost premultiplicat amb el fons des-premultiplicat i infla el MAD), i
    # el llindar és LOCAL: per cel·la calaix radial × sector de 30° (el soroll
    # del cel varia per azimut; un llindar global es menja les febles)
    NSd = 12
    cob_ok = alfaT > 0.98
    th_px = np.mod(np.arctan2(dy[:, None], dx[None, :]), 2 * np.pi)
    sidx = np.clip((th_px / (2 * np.pi / NSd)).astype(np.int16), 0, NSd - 1)
    del th_px
    cidx = np.clip(bidx, 0, NBb - 1).astype(np.int32) * NSd + sidx
    med_c = np.zeros(NBb * NSd, np.float32)
    sig_c = np.full(NBb * NSd, 1e9, np.float32)
    Ds = D[::3, ::3]
    cs = cob_ok[::3, ::3]
    ci = cidx[::3, ::3]
    ordre = np.argsort(ci[cs], kind="stable")
    vs = Ds[cs][ordre]
    talls = np.searchsorted(ci[cs][ordre], np.arange(NBb * NSd + 1))
    for cc in range(NBb * NSd):
        a0, a1 = talls[cc], talls[cc + 1]
        if a1 - a0 > 150:
            v = vs[a0:a1]
            md = np.median(v)
            med_c[cc], sig_c[cc] = md, 1.4826 * np.median(np.abs(v - md))
    del Ds, cs, ci, ordre, vs, talls
    cand = ((D > (med_c + 4.0 * sig_c)[cidx]) & (rR > 2.5) & (rR < 20.0)
            & (m > 0.02) & cob_ok)
    ncc, labels, stats, _ = cv2.connectedComponentsWithStats(
        cand.astype(np.uint8), connectivity=8)
    del cand
    est = []
    for i in range(1, ncc):
        x0, y0, wc, hc, area = stats[i]
        if area < 2 or area > 80 or wc > 14 or hc > 14:
            continue
        if max(wc, hc) > 3 * max(min(wc, hc), 1):
            continue
        sub = np.where(labels[y0:y0 + hc, x0:x0 + wc] == i,
                       D[y0:y0 + hc, x0:x0 + wc], -1e9)
        iy_, ix_ = np.unravel_index(np.argmax(sub), sub.shape)
        py, px = y0 + iy_, x0 + ix_
        if not (13 <= px < W - 13 and 13 <= py < H - 13):
            continue
        cc = int(cidx[py, px])
        if D[py, px] < med_c[cc] + 5.0 * sig_c[cc]:
            continue
        est.append((px, py, float(D[py, px] - med_c[cc]), int(area), float(m[py, px])))
    del labels, bidx, cidx, sidx
    est = np.array(est, np.float32) if est else np.zeros((0, 5), np.float32)
    marca(f"estrelles pròpies (5σ local al cru): {len(est)} (de {ncc-1} components)")

    # ⏭️ UNIÓ amb el catàleg del retall de Pere: la seva passada de Camera Raw
    # (amb reducció de soroll) va fer aflorar 2.117 fonts que al compost CRU
    # són a ~1 σ del gra correlacionat — indetectables individualment però
    # REALS (verificades al seu retall). Es reinjecta l'excés cru de cada
    # posició; la seva corba final les tornarà a fer aflorar, sobre fons net.
    p_crop = os.path.join(CAUD, "operador", "estrelles_xy_c_area_m.npy")
    ec = np.load(p_crop)
    OXC, OYC = 2196, 4124
    xs_c = ec[:, 0] + OXC
    ys_c = ec[:, 1] + OYC
    dins = ((xs_c > 13) & (xs_c < W - 13) & (ys_c > 13) & (ys_c < H - 13))
    xs_c, ys_c, ar_c = xs_c[dins], ys_c[dins], ec[dins, 3]
    ii = np.clip(ys_c.astype(int), 0, H - 1)
    jj = np.clip(xs_c.astype(int), 0, W - 1)
    bo = ((m[ii, jj] > 0.02) & cob_ok[ii, jj]
          & (rR[ii, jj] > 2.5) & (rR[ii, jj] < 20.0))
    xs_c, ys_c, ar_c = xs_c[bo], ys_c[bo], ar_c[bo]
    if len(est):
        from scipy.spatial import cKDTree
        d_, _ = cKDTree(est[:, :2]).query(np.c_[xs_c, ys_c], k=1)
        nous = d_ > 4.0
    else:
        nous = np.ones(len(xs_c), bool)
    afegits = np.stack([xs_c[nous], ys_c[nous],
                        np.zeros(nous.sum(), np.float32), ar_c[nous],
                        m[ii, jj][bo][nous]], axis=1).astype(np.float32)
    est = np.vstack([est, afegits]) if len(est) else afegits
    marca(f"unió amb el catàleg del retall de Pere: +{int(nous.sum())} → "
          f"{len(est)} fonts")

    S = np.zeros((H, W), np.float32)
    for px, py, c0, area, mm_ in est:
        px, py = int(px), int(py)
        Rs_ = float(np.clip(2.2 * np.sqrt(area / np.pi) + 2.5, 4.0, 9.0))
        R_ = int(np.ceil(Rs_))
        oy, ox = np.mgrid[-R_:R_ + 1, -R_:R_ + 1]
        t = np.clip((Rs_ - np.hypot(oy, ox)) / 2.5, 0, 1)
        s_ = (0.5 - 0.5 * np.cos(np.pi * t)).astype(np.float32)
        reg = S[py - R_:py + R_ + 1, px - R_:px + R_ + 1]
        np.maximum(reg, s_, out=reg)
    mS = (m * S).astype(np.float32)
    E16 = np.empty((H, W, 3), np.uint16)
    dins_S = S > 0.001
    for ch in range(3):
        e = np.clip(C[..., ch].astype(np.float32)
                    - Bdet16[..., ch].astype(np.float32), 0, 65535)
        E16[..., ch] = np.where(dins_S, e, 0).astype(np.uint16)
        del e
    marca("capa d'estrelles construïda")

    # ---------- [6] fusionada F i portes ----------
    F = np.empty((H, W, 3), np.uint16)
    for ch in range(3):
        f = (C[..., ch].astype(np.float32) * (1 - m)
             + B16[..., ch].astype(np.float32) * m
             + E16[..., ch].astype(np.float32) * mS)
        F[..., ch] = np.clip(f + 0.5, 0, 65535).astype(np.uint16)
        del f
    np.save(os.path.join(CAUF, "F_v19_rgb16.npy"), F)
    np.save(os.path.join(CAUF, "B_v19_rgb16.npy"), B16)
    np.save(os.path.join(CAUF, "E_v19_rgb16.npy"), E16)
    np.save(os.path.join(CAUF, "mask_rampa16.npy"),
            np.clip(np.rint(m * 65535.0), 0, 65535).astype(np.uint16))
    np.save(os.path.join(CAUF, "mask_estrelles16.npy"),
            np.clip(np.rint(mS * 65535.0), 0, 65535).astype(np.uint16))
    # la cobertura de la V19: la capa FONS (opaca, màscara = rampa) cobreix el
    # que la V18 deixava transparent (les cantonades més enllà de la dada Sony)
    alfaT = alfaT + m * (1.0 - alfaT)
    np.save(os.path.join(CAUF, "alfaT8.npy"),
            np.clip(np.rint(alfaT * 255.0), 0, 255).astype(np.uint8))
    marca(f"fusionada F feta · cobertura V18 → V19: {alfaT.mean():.4f} "
          "(les peces són al cau fons/)")

    # portes de bony i croma per sector (mediana; ≥ meitat de rajos vàlids)
    RAJ = NT // N_SECTORS

    def pava_noninc(y):
        v, wg = [], []
        for yi in y:
            v.append(float(yi)); wg.append(1.0)
            while len(v) > 1 and v[-2] < v[-1]:
                vt = (v[-1] * wg[-1] + v[-2] * wg[-2]) / (wg[-1] + wg[-2])
                wt = wg[-1] + wg[-2]
                v.pop(); wg.pop()
                v[-1] = vt; wg[-1] = wt
        return np.concatenate([np.full(int(round(w_)), v_) for v_, w_ in zip(v, wg)])

    def perfils_sectors(pol):
        a = np.where(VALID, pol, np.nan).reshape(N_SECTORS, RAJ, NR)
        perf = np.nanmedian(a, axis=1)
        compta = np.isfinite(a).sum(axis=1)
        # 4/5 dels rajos vius: a la vora de cobertura el salt de població
        # fabrica bonys falsos (la lliçó del prototip, aquí encara més forta)
        perf[compta < (4 * RAJ) // 5] = np.nan
        return perf

    def bony_perfil(p, sel_r):
        ok = np.isfinite(p) & sel_r
        if ok.sum() < 50:
            return None
        fit = pava_noninc(p[ok])
        return float(np.max((p[ok] - fit) / np.maximum(fit, 1e-3)))

    def portes_img(arr16):
        pols = [a_polar(arr16[..., ch].astype(np.float32)) for ch in range(3)]
        lum = (pols[0] + pols[1] + pols[2]) / 3.0
        perf_l = perfils_sectors(lum / 65535.0)
        perfs = [perfils_sectors(p) for p in pols]
        sel_r = (r_of_bin >= 2.5) & (r_of_bin <= 12.0)
        bonys = [bony_perfil(perf_l[s], sel_r) for s in range(N_SECTORS)]
        sel_c = (r_of_bin >= 4.0) & (r_of_bin <= 10.0)
        tvs = []
        for s in range(N_SECTORS):
            u = (perfs[0][s] - perfs[1][s])[sel_c]
            v_ = (perfs[2][s] - perfs[1][s])[sel_c]
            ok = np.isfinite(u) & np.isfinite(v_)
            tvs.append(float((np.sum(np.abs(np.diff(u[ok])))
                              + np.sum(np.abs(np.diff(v_[ok])))) / 65535.0)
                       if ok.sum() > 50 else None)
        return bonys, tvs, pols, lum

    bonys_C, tvs_C, _, lumC_pol = portes_img(C)
    bonys_F, tvs_F, _, lumF_pol = portes_img(F)
    va_C = [b for b in bonys_C if b is not None]
    va_F = [b for b in bonys_F if b is not None]
    print("    24 sectors: bony C max/med "
          f"{np.max(va_C):.5f}/{np.median(va_C):.5f} → F "
          f"{np.max(va_F):.5f}/{np.median(va_F):.5f}", flush=True)
    exc = [tf - tc for tf, tc in zip(tvs_F, tvs_C) if tf is not None and tc is not None]
    print(f"    tv croma (F − C): mediana {np.median(exc):+.4f} · max {np.max(exc):+.4f}",
          flush=True)

    # les 17 marques de Pere (sector az_med±12°, banda r de cada marca)
    marques = []
    regs = json.load(open(os.path.join(CAU19, "regions_v19.json")))
    for fam in ("verd", "taronja"):
        for z in regs[fam]:
            marques.append((f"r2_{fam}", z["az_med"], z["r_min"], z["r_max"]))
    hm = np.load(os.path.join(CAU18, "halos_marca.npy"), mmap_mode="r")
    hm4 = np.asarray(hm[::4, ::4]) > 0
    n1, lab1, st1, cen1 = cv2.connectedComponentsWithStats(hm4.astype(np.uint8), 8)
    yy4 = np.arange(hm4.shape[0], dtype=np.float32)[:, None] * 4
    xx4 = np.arange(hm4.shape[1], dtype=np.float32)[None, :] * 4
    rad4 = np.hypot(xx4 - SOL[0], yy4 - SOL[1]) / RS
    az4 = np.degrees(np.arctan2(-(yy4 - SOL[1]), xx4 - SOL[0]))
    for k in range(1, n1):
        if st1[k, cv2.CC_STAT_AREA] < 120:
            continue
        mk_ = lab1 == k
        marques.append(("r1", float(np.median(az4[mk_])),
                        float(np.percentile(rad4[mk_], 2)),
                        float(np.percentile(rad4[mk_], 98))))
    th_deg = np.degrees(np.mod(-th_g + 2 * np.pi, 2 * np.pi))
    th_deg = np.where(th_deg > 180, th_deg - 360, th_deg)   # conveni marques
    files_m = []
    for fam, az0, rlo, rhi in marques:
        sel_raig = np.abs(((th_deg - az0 + 180) % 360) - 180) < 12
        sel_r = (r_of_bin >= max(2.3, rlo - 0.5)) & (r_of_bin <= min(14.0, rhi + 0.5))
        res = {}
        for nom, lum in (("C", lumC_pol), ("F", lumF_pol)):
            a = np.where(VALID[sel_raig], lum[sel_raig], np.nan)
            p = np.nanmedian(a, axis=0) / 65535.0
            compta = np.isfinite(a).sum(axis=0)
            p[compta < (4 * int(sel_raig.sum())) // 5] = np.nan
            res[nom] = bony_perfil(p, sel_r)
        files_m.append({"fam": fam, "az": round(az0, 1), "r": [round(rlo, 2),
                        round(rhi, 2)], "bony_C": res["C"], "bony_F": res["F"]})
        bc = f"{res['C']:.4f}" if res["C"] is not None else "  -  "
        bf = f"{res['F']:.4f}" if res["F"] is not None else "  -  "
        print(f"    {fam:10s} az {az0:+7.1f}° r {rlo:.2f}-{rhi:.2f}: "
              f"bony {bc} → {bf}", flush=True)

    # supervivència d'estrelles a F
    surv = {}
    if len(est):
        oy, ox = np.mgrid[-12:13, -12:13]
        ring = (oy**2 + ox**2 >= 64) & (oy**2 + ox**2 <= 144)
        OY, OX = oy[ring].astype(np.int32), ox[ring].astype(np.int32)
        xs = est[:, 0].astype(np.int32)
        ys = est[:, 1].astype(np.int32)
        LF = (F[..., 0].astype(np.float32) + F[..., 1] + F[..., 2]) / 3.0

        def contr(L):
            vals = L[ys[:, None] + OY[None, :], xs[:, None] + OX[None, :]]
            return L[ys, xs] - np.median(vals, axis=1)

        cref = contr(L1)
        cF = contr(LF)
        selt = (est[:, 4] > 0.5) & (cref > 0)
        surv = {"n": int(len(est)), "n_fons": int(selt.sum()),
                "viuen_F": int(np.sum(cF[selt] >= 0.5 * cref[selt])),
                "fraccio": float(np.mean(cF[selt] >= 0.5 * cref[selt]))}
        print(f"    estrelles al fons: {surv['n_fons']} · viuen a F: "
              f"{surv['viuen_F']} ({100*surv['fraccio']:.1f} %)", flush=True)
        del LF, L1, D
    marca("portes calculades")
    json.dump({"sectors": {"bony_C": bonys_C, "bony_F": bonys_F,
                           "tv_C": tvs_C, "tv_F": tvs_F},
               "marques": files_m, "estrelles": surv,
               "n_estrelles": int(len(est)),
               "rampa": {"r_m05": i50, "taula_r": r_taula.tolist(),
                         "taula_m": m_taula.tolist()}},
              open(os.path.join(CAUF, "portes_v19.json"), "w"), indent=1)
    np.save(os.path.join(CAUF, "estrelles_v19.npy"), est)
    if "--nomes-calcul" in sys.argv:
        marca("(--nomes-calcul: les peces són al cau; el PSB es fa amb --nomes-psb)")
        return
    fes_psb(F, B16, E16, m, mS, alfaT, est, i50, bonys_C, bonys_F, tvs_C, tvs_F,
            files_m, surv, r_taula, m_taula)


def fes_psb(F, B16, E16, m, mS, alfaT, est, i50, bonys_C, bonys_F, tvs_C, tvs_F,
            files_m, surv, r_taula, m_taula):
    H, W = F.shape[:2]

    # ---------- [7] el PSB ----------
    from psd_tools import PSDImage
    from psd_tools.constants import Compression, BlendMode
    from psd_tools.psd.image_data import ImageData
    from psb_utils import add_pixel_layer, add_mask16, finalize_lr16
    psd = PSDImage.open(SRC)
    capes = list(psd)
    assert len(capes) == 15
    marques_copia = capes[13]
    pasalt = capes[14]
    psd.remove(marques_copia)
    print("    còpia de marques fora (queda al save de Pere)", flush=True)
    tb = psd._record.layer_and_mask_information.tagged_blocks
    for kk in list(tb.keys()):
        kb = kk.value if hasattr(kk, "value") else kk
        if kb not in (b"Lr16", b"Mt16"):
            del tb[kk]
    print("    blocs globals heretats fora (la trampa 8BIM/8B64)", flush=True)

    nom_fons = ("FONS_PER_RAIG · suavitzat en ln r (σ0,2) del compost, per raig "
                "· màscara = rampa de Pere 2,45-3,25 R☉ (V19)")
    capa_fons = add_pixel_layer(psd, B16, nom_fons, top=0, left=0,
                                blend=BlendMode.NORMAL, compression=Compression.ZIP)
    add_mask16(capa_fons, np.clip(np.rint(m * 65535.0), 0, 65535).astype(np.uint16),
               top=0, left=0)
    nom_est = (f"ESTRELLES · reinjecció additiva de {len(est)} fonts puntuals "
               "(Linear Dodge) (V19)")
    capa_est = add_pixel_layer(psd, E16, nom_est, top=0, left=0,
                               blend=BlendMode.LINEAR_DODGE,
                               compression=Compression.ZIP)
    add_mask16(capa_est, np.clip(np.rint(mS * 65535.0), 0, 65535).astype(np.uint16),
               top=0, left=0)
    psd.remove(pasalt)
    psd.append(pasalt)          # el Pasalt (apagat) torna a dalt de tot
    finalize_lr16(psd)
    marca("capes noves inserides i Lr16 reconstruït")

    n_can = psd._record.header.channels
    rgbW = [np.clip(F[..., ch].astype(np.float32)
                    + (1.0 - alfaT) * 65535.0 + 0.5, 0, 65535)
            .astype(">u2").tobytes() for ch in range(3)]
    if n_can == 4:
        rgbW.append(np.clip(np.rint(alfaT * 65535.0), 0, 65535)
                    .astype(">u2").tobytes())
    else:
        assert n_can == 3, f"canals de capçalera inesperats: {n_can}"
    print(f"    fusionada amb {n_can} plans (capçalera)", flush=True)
    idata = ImageData(compression=Compression.RAW)
    idata.set_data(rgbW, psd._record.header)
    psd._record.image_data = idata
    if getattr(psd, "_updated", False):
        psd._updated = False
    del rgbW
    marca("fusionada posada; desant…")
    psd.save(DST)
    marca(f"{DST} · {os.path.getsize(DST)/1e9:.2f} GB")

    # ---------- [8] portes de fitxer ----------
    p2 = PSDImage.open(DST)
    capes2 = list(p2)
    assert (p2.width, p2.height) == (W, H), "mides"
    assert len(capes2) == 16, f"capes: {len(capes2)}"
    src2 = PSDImage.open(SRC)
    c_src = list(src2)[0]._channels[1].data
    c_dst = capes2[0]._channels[1].data
    assert c_src == c_dst, "fidelitat: capa 0 divergeix"
    print("    fidelitat: canal R de la capa 0 byte a byte ✓", flush=True)
    r = subprocess.run(["sips", "-g", "pixelWidth", DST], capture_output=True, text=True)
    assert f"pixelWidth: {W}" in r.stdout + r.stderr
    r = subprocess.run([os.path.join(AQUI, "porta_photoshop.sh"), DST],
                       capture_output=True, text=True, timeout=1800)
    print("    Photoshop diu:", (r.stdout + r.stderr).strip(), flush=True)

    rebut = {"src": SRC, "desti": DST, "sol": SOL, "rs": RS,
             "polar": {"NT": NT, "NR": NR, "R0": R0, "R1": R1},
             "sigma_b": SIGMA_B, "sigma_det": SIGMA_DET, "med_k": MED_K,
             "rampa": {"r_m05": i50, "taula_r": r_taula.tolist(),
                       "taula_m": m_taula.tolist()},
             "sectors": {"bony_C": bonys_C, "bony_F": bonys_F,
                         "tv_C": tvs_C, "tv_F": tvs_F},
             "marques": files_m, "estrelles": surv,
             "n_estrelles": int(len(est)),
             "capes": [ly.name for ly in capes2],
             "bytes": os.path.getsize(DST)}
    json.dump(rebut, open(os.path.join(CAUF, "rebut_v19.json"), "w"),
              indent=1, ensure_ascii=False)
    np.save(os.path.join(CAUF, "estrelles_v19.npy"), est)
    marca("rebut desat; fet")


def nomes_psb():
    """Reprèn del cau (quan l'accés al Desktop torna): només [7] i [8]."""
    F = np.load(os.path.join(CAUF, "F_v19_rgb16.npy"))
    B16 = np.load(os.path.join(CAUF, "B_v19_rgb16.npy"))
    E16 = np.load(os.path.join(CAUF, "E_v19_rgb16.npy"))
    m = np.load(os.path.join(CAUF, "mask_rampa16.npy")).astype(np.float32) / 65535.0
    mS = np.load(os.path.join(CAUF, "mask_estrelles16.npy")).astype(np.float32) / 65535.0
    alfaT = np.load(os.path.join(CAUF, "alfaT8.npy")).astype(np.float32) / 255.0
    est = np.load(os.path.join(CAUF, "estrelles_v19.npy"))
    p = json.load(open(os.path.join(CAUF, "portes_v19.json")))
    marca("peces del cau carregades; construeixo el PSB")
    fes_psb(F, B16, E16, m, mS, alfaT, est, p["rampa"]["r_m05"],
            p["sectors"]["bony_C"], p["sectors"]["bony_F"],
            p["sectors"]["tv_C"], p["sectors"]["tv_F"],
            p["marques"], p["estrelles"],
            np.array(p["rampa"]["taula_r"], np.float32),
            np.array(p["rampa"]["taula_m"], np.float32))


if __name__ == "__main__":
    if "--nomes-psb" in sys.argv:
        nomes_psb()
    else:
        main()
