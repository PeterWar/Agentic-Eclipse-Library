# -*- coding: utf-8 -*-
"""
PROTOTIP DE L'OPERADOR FORMALITZAT (mètode del Desenfoc Radial Zoom de Pere).

Formalització: fons B = suavitzat gaussià NORMALITZAT al llarg de ln r (mediana
curta abans, robusta a estrelles) en una graella polar (θ × ln r) al voltant del
Sol; cap suavitzat en azimut. El pes (dins/fora del llenç) fa la feina que Pere
feia pintant les cantonades. Compost F2 = capa1·(1−m) + B·m amb la màscara m de
Pere. F3 = F2 + m·S·(capa1 − B): recuperació d'estrelles (S màscara petita per
estrella). Portes comparatives F1 (Pere) / F2 / F3.

La tria de σ_lnr es fa amb dues evidències: (i) rugositat radial (passa-alt
normalitzat pel pes) comparada amb la capa2 de Pere, i (ii) la porta (a) de bony
radial del compost F2 contra la del F1 de Pere; si cap σ del joc especificat
{0,05·0,10·0,20} no iguala Pere al bony, s'estén a {0,30·0,40} i es declara.

Només llegeix capa1/capa2/mask/geometria; escriu a cau_v19/desenfoc/operador/.
Reexecutable: ~/.venvs/eines-ia-py312/bin/python scripts/operador_prototip.py
"""
import json
import os
import time
import warnings

import cv2
import numpy as np
from scipy.ndimage import median_filter

BASE = "/Users/USUARI/Downloads/Eclipse 2026/research/tools/capes_totals_v14/cau_v19/desenfoc"
OUT = os.path.join(BASE, "operador")
os.makedirs(OUT, exist_ok=True)

# ---------------- paràmetres ----------------
NT = 4080            # rajos (24 sectors x 170)
NR = 1200            # mostres log-uniformes en r
R0, R1 = 2.0, 11.5   # R☉
PREF_SIGMA_PX = 1.2  # pre-filtre cartesià abans del remostreig (anti-àlies) NOMÉS per a B
MED_K = 11           # mediana al llarg de ln r (mostres)
SIGMES = [0.05, 0.10, 0.20]
SIGMES_EXTENSIO = [0.30, 0.40]
SIGMA_REF_RUG = 0.30  # passa-alt de referència per a la rugositat
N_SECTORS = 24
RAJOS_SECTOR = NT // N_SECTORS
ANELLS_FIDELITAT = [3.0, 4.0, 5.0, 6.0, 8.0]
FIN_LNR = 0.02        # semi-finestra en ln r dels anells
DET_CC_NSIG = 4.0     # llindar de connectivitat (sobre sigma local)
DET_PIC_NSIG = 5.0    # llindar del pic
SIGMA_DET = 0.05      # fons FI per a deteccio i fotometria local d'estrelles
AMP_DIF = 16.0        # amplificació de la vista |F2-F1|

warnings.filterwarnings("ignore", category=RuntimeWarning)
T0 = time.time()
TEMPS = {}


def marca(nom):
    TEMPS[nom] = round(time.time() - T0, 1)
    print(f"[{TEMPS[nom]:7.1f}s] {nom}", flush=True)


geo = json.load(open(os.path.join(BASE, "geometria.json")))
W, H = geo["llenc"]
cx, cy = geo["sol_crop"]
rs = geo["rs"]
LNR0, LNR1 = np.log(R0), np.log(R1)
DLNR = (LNR1 - LNR0) / (NR - 1)
DTH = 2.0 * np.pi / NT

c1 = np.load(os.path.join(BASE, "capa1_rgb16.npy"), mmap_mode="r")
c2 = np.load(os.path.join(BASE, "capa2_rgb16.npy"), mmap_mode="r")
mk = np.load(os.path.join(BASE, "capa2_mask16.npy"), mmap_mode="r")

# ---------------- mapes polars (endavant) ----------------
th_g = (np.arange(NT, dtype=np.float64) * DTH)
r_px = rs * np.exp(LNR0 + np.arange(NR, dtype=np.float64) * DLNR)
MAPX = (cx + np.cos(th_g)[:, None] * r_px[None, :]).astype(np.float32)
MAPY = (cy + np.sin(th_g)[:, None] * r_px[None, :]).astype(np.float32)


def a_polar(img):
    return cv2.remap(img, MAPX, MAPY, interpolation=cv2.INTER_LINEAR,
                     borderMode=cv2.BORDER_CONSTANT, borderValue=0.0)


w_pol = a_polar(np.ones((H, W), np.float32))
VALID = w_pol > 0.5
V90 = w_pol > 0.9
IDX_R = np.arange(NR)
r_of_bin = np.exp(LNR0 + IDX_R * DLNR)


def omple_endavant(a, valid):
    """Omple cel·les no vàlides amb l'últim valor vàlid cap a dins del raig."""
    idx = np.where(valid, IDX_R[None, :], 0)
    np.maximum.accumulate(idx, axis=1, out=idx)
    return np.take_along_axis(a, idx, axis=1)


def gauss_lnr(a, sigma_mostres):
    k = min(2 * int(3 * sigma_mostres) + 1, 1199)
    return cv2.GaussianBlur(a, (k, 1), sigmaX=sigma_mostres, sigmaY=0,
                            borderType=cv2.BORDER_REPLICATE)


def fons_polar(pol, sigma_lnr):
    """B polar: mediana curta + gaussiana normalitzada al llarg de ln r."""
    pol_ff = omple_endavant(pol, VALID)
    pol_med = median_filter(pol_ff, size=(1, MED_K), mode="nearest")
    s = sigma_lnr / DLNR
    num = gauss_lnr(pol_med * w_pol, s)
    den = gauss_lnr(w_pol, s)
    B = num / np.maximum(den, 1e-6)
    return omple_endavant(B, den > 1e-3)


def gauss_theta(a, sigma_rajos):
    """Gaussiana al llarg de θ amb continuïtat circular (farciment wrap)."""
    k = 2 * int(3 * sigma_rajos) + 1
    pad = min(int(3 * sigma_rajos) + 1, NT)
    ap = np.vstack([a[-pad:], a, a[:pad]])
    b = cv2.GaussianBlur(ap, (1, k), sigmaX=0, sigmaY=sigma_rajos,
                         borderType=cv2.BORDER_REPLICATE)
    return b[pad:pad + NT]


def fons_polar_hibrid(pol, s_fi, s_llis, s_th_rajos):
    """B híbrid: la part azimutalment llisa s'aplana radialment fort (s_llis) i
    el detall azimutal es conserva amb el suavitzat radial fi (s_fi). La B final
    NO va suavitzada en azimut: en azimut és exactament la B fina."""
    A = fons_polar(pol, s_fi)
    L = fons_polar(pol, s_llis)
    num = gauss_theta(A * w_pol, s_th_rajos)
    den = gauss_theta(w_pol, s_th_rajos)
    Aaz = np.where(den > 1e-3, num / np.maximum(den, 1e-6), A)
    return L + A - Aaz


def lum_f32(a):
    L = a[..., 0].astype(np.float32)
    L += a[..., 1]
    L += a[..., 2]
    L /= 3.0
    return L


# ---------------- polars de capa1 (pre-filtrada per a B) i capa2 ----------------
c1f_pol = []
for ch in range(3):
    b = cv2.GaussianBlur(c1[..., ch].astype(np.float32), (0, 0), PREF_SIGMA_PX)
    c1f_pol.append(a_polar(b))
del b
lum1f_pol = (c1f_pol[0] + c1f_pol[1] + c1f_pol[2]) / 3.0
lum2_cart = cv2.GaussianBlur(lum_f32(c2), (0, 0), PREF_SIGMA_PX)
lum2_pol = a_polar(lum2_cart)
del lum2_cart
marca("polars de capa1 i capa2")

# ---------------- rugositat radial (referència normalitzada pel pes) ----------------
BANDA = (r_of_bin >= 2.6) & (r_of_bin <= 10.5)
V_BANDA = V90 & BANDA[None, :]


def rugositat(pol):
    pol_ff = omple_endavant(pol, VALID)
    s = SIGMA_REF_RUG / DLNR
    ref = gauss_lnr(pol_ff * w_pol, s) / np.maximum(gauss_lnr(w_pol, s), 1e-6)
    hp = pol_ff - ref
    rms_hp = float(np.sqrt(np.mean(hp[V_BANDA] ** 2))) / 65535.0
    d = np.diff(pol_ff, axis=1)
    vd = V_BANDA[:, 1:] & V_BANDA[:, :-1]
    rms_d = float(np.sqrt(np.mean(d[vd] ** 2))) / 65535.0
    return rms_hp, rms_d


def _suau_circ_1d(x, sigma_rajos):
    k = 2 * int(3 * sigma_rajos) + 1
    pad = int(3 * sigma_rajos) + 1
    xp = np.concatenate([x[-pad:], x, x[:pad]]).astype(np.float32)
    return cv2.GaussianBlur(xp.reshape(-1, 1), (1, k), sigmaX=0, sigmaY=sigma_rajos,
                            borderType=cv2.BORDER_REPLICATE)[pad:pad + len(x), 0]


def anells_corr(pol_a, pol_b):
    """Correlació del perfil azimutal amb capa1 per anell; també la de només la
    part azimutalment lenta (λ>15°), perquè a radis grans l'alta freqüència del
    perfil de capa1 és soroll radialment incoherent (mesurat al diagnòstic)."""
    out = {}
    idx = np.arange(NT, dtype=np.float64)
    for rr in ANELLS_FIDELITAT:
        sel = np.abs(LNR0 + IDX_R * DLNR - np.log(rr)) <= FIN_LNR
        a = np.nanmedian(np.where(VALID[:, sel], pol_a[:, sel], np.nan), axis=1)
        b = np.nanmedian(np.where(VALID[:, sel], pol_b[:, sel], np.nan), axis=1)
        ok = np.isfinite(a) & np.isfinite(b)
        af = np.interp(idx, idx[ok], a[ok], period=NT)
        bf = np.interp(idx, idx[ok], b[ok], period=NT)
        s15 = 15.0 * NT / 360.0
        al, bl = _suau_circ_1d(af, s15), _suau_circ_1d(bf, s15)
        out[str(rr)] = {"corr": float(np.corrcoef(a[ok], b[ok])[0, 1]),
                        "corr_baixa_15deg": float(np.corrcoef(al[ok], bl[ok])[0, 1]),
                        "rajos_valids": int(ok.sum())}
    return out


# ---------------- portes polars ----------------
def pava_noninc(y):
    v, wgt = [], []
    for yi in y:
        v.append(float(yi)); wgt.append(1.0)
        while len(v) > 1 and v[-2] < v[-1]:
            vt = (v[-1] * wgt[-1] + v[-2] * wgt[-2]) / (wgt[-1] + wgt[-2])
            wt = wgt[-1] + wgt[-2]
            v.pop(); wgt.pop()
            v[-1] = vt; wgt[-1] = wt
    return np.concatenate([np.full(int(round(w_)), v_) for v_, w_ in zip(v, wgt)])


def perfils_sectors(pol):
    """Mediana per sector i calaix; un calaix amb menys de la meitat dels rajos
    vàlids es declara NaN — si no, el salt de població a la vora del llenç
    fabrica un «bony» fals (mesurat: el màxim de TOTS els candidats, Pere
    inclòs, queia als sectors que apunten a la vora superior)."""
    a = np.where(VALID, pol, np.nan).reshape(N_SECTORS, RAJOS_SECTOR, NR)
    perf = np.nanmedian(a, axis=1)   # (24, NR)
    compta = np.isfinite(a).sum(axis=1)
    perf[compta < RAJOS_SECTOR // 2] = np.nan
    return perf


def porta_bony(perf_lum):
    sel_r = (r_of_bin >= 2.5) & (r_of_bin <= 10.0)
    bonys, on = [], []
    for s_ in range(N_SECTORS):
        p = perf_lum[s_]
        ok = np.isfinite(p) & sel_r
        if ok.sum() < 50:
            bonys.append(None); on.append(None); continue
        fit = pava_noninc(p[ok])
        dev = (p[ok] - fit) / np.maximum(fit, 1e-3)
        i = int(np.argmax(dev))
        bonys.append(float(dev[i]))
        on.append(float(r_of_bin[ok][i]))
    va = [b for b in bonys if b is not None]
    imax = int(np.argmax([b if b is not None else -1 for b in bonys]))
    return {"max": float(np.max(va)), "mediana": float(np.median(va)),
            "sector_max": imax, "r_max": on[imax], "per_sector": bonys}


def porta_tv_croma(pR, pG, pB):
    sel_r = (r_of_bin >= 4.0) & (r_of_bin <= 9.0)
    tvs = []
    for s_ in range(N_SECTORS):
        u = (pR[s_] - pG[s_])[sel_r]
        v_ = (pB[s_] - pG[s_])[sel_r]
        ok = np.isfinite(u) & np.isfinite(v_)
        if ok.sum() < 50:
            tvs.append(None); continue
        tvs.append(float((np.sum(np.abs(np.diff(u[ok]))) + np.sum(np.abs(np.diff(v_[ok])))) / 65535.0))
    return tvs


POL1_LUM = None      # lum polar de capa1 SENSE pre-filtre (referència de portes)
TV_REF = None


def portes_de(arr16, es_referencia=False):
    global POL1_LUM, TV_REF
    pols = [a_polar(arr16[..., ch].astype(np.float32)) for ch in range(3)]
    lum = (pols[0] + pols[1] + pols[2]) / 3.0
    perfs = [perfils_sectors(p) for p in pols]
    ent = {"bony_radial": porta_bony(perfils_sectors(lum) / 65535.0),
           "tv_croma_sectors": porta_tv_croma(*perfs)}
    if es_referencia:
        POL1_LUM = lum
        TV_REF = ent["tv_croma_sectors"]
    else:
        ent["fidelitat_azimutal"] = anells_corr(lum, POL1_LUM)
        exc = [t - tr for t, tr in zip(ent["tv_croma_sectors"], TV_REF)
               if t is not None and tr is not None]
        ent["tv_croma_exces_vs_capa1"] = {"mediana": float(np.median(exc)),
                                          "max": float(np.max(exc))}
    return ent


# ---------------- mapes inversos i compostos ----------------
dx = np.arange(W, dtype=np.float32) - np.float32(cx)
dy = np.arange(H, dtype=np.float32) - np.float32(cy)
rpx_c = np.hypot(dx[None, :], dy[:, None])
rR = rpx_c / np.float32(rs)          # (H,W) en R☉ — es conserva per a estrelles
del rpx_c
lnr_c = np.log(np.maximum(rR, R0))
IXI = ((lnr_c - LNR0) / DLNR).astype(np.float32)
np.clip(IXI, 0, NR - 1, out=IXI)
del lnr_c
th_c = np.arctan2(dy[:, None], dx[None, :])
np.mod(th_c, 2 * np.pi, out=th_c)
IYI = (th_c / DTH).astype(np.float32)
np.clip(IYI, 0, NT - 1e-3, out=IYI)
del th_c

m = mk.astype(np.float32)
m /= 65535.0
marca("mapes inversos i màscara")


def construeix_fons_gen(builder):
    """B al llenç (uint16 3 canals) i la seva luminància float32."""
    B16 = np.empty((H, W, 3), np.uint16)
    LB = np.zeros((H, W), np.float32)
    for ch in range(3):
        Bp = builder(c1f_pol[ch])
        Bp = np.vstack([Bp, Bp[:2]])
        Bc = cv2.remap(Bp, IXI, IYI, interpolation=cv2.INTER_LINEAR,
                       borderMode=cv2.BORDER_REPLICATE)
        B16[..., ch] = np.clip(Bc + 0.5, 0, 65535).astype(np.uint16)
        LB += Bc
        del Bp, Bc
    LB /= 3.0
    return B16, LB


def construeix_fons(sigma):
    return construeix_fons_gen(lambda pol: fons_polar(pol, sigma))


def compost(base):
    """F = capa1·(1−m) + base·m, uint16."""
    F = np.empty((H, W, 3), np.uint16)
    for ch in range(3):
        F[..., ch] = np.clip(c1[..., ch].astype(np.float32) * (1 - m)
                             + base[..., ch].astype(np.float32) * m + 0.5,
                             0, 65535).astype(np.uint16)
    return F


# ---------------- referència capa1 i F1 de Pere ----------------
portes = {"capa1": portes_de(np.asarray(c1), es_referencia=True)}
F1_16 = compost(c2)
portes["F1"] = portes_de(F1_16)
print(f"  capa1: bony max={portes['capa1']['bony_radial']['max']:.5f} "
      f"med={portes['capa1']['bony_radial']['mediana']:.5f}", flush=True)
print(f"  F1:    bony max={portes['F1']['bony_radial']['max']:.5f} "
      f"med={portes['F1']['bony_radial']['mediana']:.5f}", flush=True)
marca("portes de capa1 i F1")

# ---------------- escombrat de sigma ----------------
rug1 = rugositat(lum1f_pol)
rug2 = rugositat(lum2_pol)
sel_sigma = {"rugositat_capa1": {"hp": rug1[0], "dif": rug1[1]},
             "rugositat_capa2_pere": {"hp": rug2[0], "dif": rug2[1]},
             "candidats": {}}
bony_f1 = portes["F1"]["bony_radial"]
escombrat = {}


def prova_candidat(clau, builder, extra=None):
    Bl = builder(lum1f_pol)
    rh, rd = rugositat(Bl)
    fidB = anells_corr(Bl, lum1f_pol)
    del Bl
    B16s, _ = construeix_fons_gen(builder)
    F2s = compost(B16s)
    p = portes_de(F2s)
    escombrat[clau] = (B16s, F2s, p)
    ent = {"rug_hp_B": rh, "rug_dif_B": rd,
           "fidelitat_anells_B": {k: v["corr"] for k, v in fidB.items()},
           "porta_F2": {"bony_max": p["bony_radial"]["max"],
                        "bony_mediana": p["bony_radial"]["mediana"],
                        "tv_exces_mediana": p["tv_croma_exces_vs_capa1"]["mediana"],
                        "fid_azimutal": {k: v["corr"] for k, v in p["fidelitat_azimutal"].items()}}}
    if extra:
        ent.update(extra)
    sel_sigma["candidats"][clau] = ent
    print(f"  {clau}: rugB hp={rh:.6f} dif={rd:.6f} | F2 bony "
          f"max={p['bony_radial']['max']:.5f} med={p['bony_radial']['mediana']:.5f} | fid "
          f"{ {k: round(v['corr'],3) for k, v in p['fidelitat_azimutal'].items()} }", flush=True)
    return p


def passa_bony(p):
    return (p["bony_radial"]["max"] <= bony_f1["max"]
            and p["bony_radial"]["mediana"] <= bony_f1["mediana"])


def domina_pere(p):
    """Iguala o millora Pere a (a) i (b) i iguala (c) amb toleràncies declarades."""
    fid1 = portes["F1"]["fidelitat_azimutal"]
    fid_ok = all(v["corr"] >= fid1[k]["corr"] - 0.005
                 for k, v in p["fidelitat_azimutal"].items())
    tv_ok = (p["tv_croma_exces_vs_capa1"]["mediana"]
             <= portes["F1"]["tv_croma_exces_vs_capa1"]["mediana"] + 0.02)
    return passa_bony(p) and fid_ok and tv_ok


# 1) escombrat escalar; extensio si cap no passa el bony
llista = [f"{s:.2f}" for s in SIGMES]
aptes_bony = []
for s in SIGMES:
    p = prova_sigma = prova_candidat(f"{s:.2f}", lambda pol, s=s: fons_polar(pol, s))
    if passa_bony(p):
        aptes_bony.append(f"{s:.2f}")
SIGMA_LLIS = None
if not aptes_bony:
    for s in SIGMES_EXTENSIO:
        clau = f"{s:.2f}"
        llista.append(clau)
        p = prova_candidat(clau, lambda pol, s=s: fons_polar(pol, s))
        if passa_bony(p):
            aptes_bony.append(clau)
            break
SIGMA_LLIS = float(aptes_bony[0]) if aptes_bony else max(float(k) for k in llista)

# 2) candidats hibrids: fi=SIGMA_DET, llis=SIGMA_LLIS, particio azimutal declarada
for sth in (15.0, 10.0):
    clau = f"hibrid_{SIGMA_DET:.2f}_{SIGMA_LLIS:.2f}_{sth:g}deg"
    llista.append(clau)
    prova_candidat(clau,
                   lambda pol, st=sth: fons_polar_hibrid(pol, SIGMA_DET, SIGMA_LLIS,
                                                         st * NT / 360.0),
                   extra={"tipus": "hibrid", "sigma_fi": SIGMA_DET,
                          "sigma_llis": SIGMA_LLIS, "sigma_theta_graus": sth})

# 3) tria: si algun candidat DOMINA Pere (a, b i c alhora), el de fidelitat
#    azimutal mitjana mes alta; si cap, el que passa el bony (a) amb max fidelitat
dominadors = [k for k in llista if domina_pere(escombrat[k][2])]


def fid_mitjana(k):
    f = escombrat[k][2]["fidelitat_azimutal"]
    return float(np.mean([v["corr"] for v in f.values()]))


if dominadors:
    SIGMA_TRIADA = max(dominadors, key=fid_mitjana)
    sel_sigma["regla"] = ("dominacio: iguala o millora F1 a (a) i (b) i iguala (c) "
                          "(tolerancia fid -0,005, tv +0,02); entre dominadors, fid mitjana maxima")
else:
    passen = [k for k in llista if passa_bony(escombrat[k][2])]
    if passen:
        SIGMA_TRIADA = max(passen, key=fid_mitjana)
        sel_sigma["regla"] = "cap candidat domina Pere; entre els que passen (a), fid mitjana maxima"
    else:
        SIGMA_TRIADA = min(llista, key=lambda k: escombrat[k][2]["bony_radial"]["max"])
        sel_sigma["regla"] = "cap candidat passa (a); bony max minim (FAIL declarat)"
sel_sigma["sigma_triada"] = SIGMA_TRIADA
sel_sigma["sigma_llis_per_hibrid"] = SIGMA_LLIS
sel_sigma["dominadors"] = dominadors
sel_sigma["bony_F1_referencia"] = {"max": bony_f1["max"], "mediana": bony_f1["mediana"]}

B16 = escombrat[SIGMA_TRIADA][0]
F2_16 = escombrat[SIGMA_TRIADA][1]
portes["F2"] = escombrat[SIGMA_TRIADA][2]
for s in list(escombrat):
    if s != SIGMA_TRIADA:
        del escombrat[s]
marca(f"tria de candidat -> {SIGMA_TRIADA}")

# ---------------- deteccio d'estrelles ----------------
# El fons de DETECCIO i fotometria local es el fi (SIGMA_DET), que segueix
# l'estructura local; el de COMPOSICIO es el llis (SIGMA_TRIADA).
Bdet16, LBdet = construeix_fons(SIGMA_DET)
L1 = lum_f32(np.asarray(c1))
D = L1 - LBdet
NB = 48
log25, log113 = np.log(2.5), np.log(11.3)
pas_b = (log113 - log25) / NB
with np.errstate(divide="ignore"):
    bidx = ((np.log(np.maximum(rR, 1e-3)) - log25) / pas_b).astype(np.int16)
med_b = np.zeros(NB, np.float32)
sig_b = np.zeros(NB, np.float32)
Ds, bs = D[::3, ::3], bidx[::3, ::3]
for b in range(NB):
    v = Ds[bs == b]
    if v.size > 100:
        mdd = np.median(v)
        med_b[b], sig_b[b] = mdd, 1.4826 * np.median(np.abs(v - mdd))
    else:
        med_b[b], sig_b[b] = 0.0, 1e9
del Ds, bs
thr_cc = med_b + DET_CC_NSIG * sig_b
thr_pic = med_b + DET_PIC_NSIG * sig_b
bok = np.clip(bidx, 0, NB - 1)
cand = (D > thr_cc[bok]) & (rR > 2.5)
del bok
ncc, labels, stats, _ = cv2.connectedComponentsWithStats(cand.astype(np.uint8), connectivity=8)
marca(f"components candidates: {ncc - 1}")

estrelles = []   # (x, y, contrast_c1, area, m_al_pic)
for i in range(1, ncc):
    x0, y0, wc, hc, area = stats[i]
    if area < 2 or area > 80 or wc > 14 or hc > 14:
        continue
    if max(wc, hc) > 3 * max(min(wc, hc), 1):
        continue
    sub = np.where(labels[y0:y0 + hc, x0:x0 + wc] == i, D[y0:y0 + hc, x0:x0 + wc], -1e9)
    iy_, ix_ = np.unravel_index(np.argmax(sub), sub.shape)
    py, px = y0 + iy_, x0 + ix_
    if not (13 <= px < W - 13 and 13 <= py < H - 13):
        continue
    b = int(np.clip(bidx[py, px], 0, NB - 1))
    if D[py, px] < thr_pic[b]:
        continue
    estrelles.append((px, py, float(D[py, px] - med_b[b]), int(area), float(m[py, px])))
del labels, cand, bidx
est = np.array(estrelles, np.float32) if estrelles else np.zeros((0, 5), np.float32)
marca(f"estrelles acceptades: {len(est)}")

# ---------------- mascara d'estrelles i F3 ----------------
S = np.zeros((H, W), np.float32)
for px, py, c0, area, mm in est:
    px, py = int(px), int(py)
    Rs = float(np.clip(2.2 * np.sqrt(area / np.pi) + 2.5, 4.0, 9.0))
    R = int(np.ceil(Rs))
    oy, ox = np.mgrid[-R:R + 1, -R:R + 1]
    rho = np.hypot(oy, ox)
    t = np.clip((Rs - rho) / 2.5, 0, 1)
    s = (0.5 - 0.5 * np.cos(np.pi * t)).astype(np.float32)
    reg = S[py - R:py + R + 1, px - R:px + R + 1]
    np.maximum(reg, s, out=reg)

F3_16 = np.empty((H, W, 3), np.uint16)
mS = m * S
for ch in range(3):
    F3c = F2_16[..., ch].astype(np.float32) + mS * (c1[..., ch].astype(np.float32)
                                                    - Bdet16[..., ch].astype(np.float32))
    F3_16[..., ch] = np.clip(F3c + 0.5, 0, 65535).astype(np.uint16)
    del F3c
del mS
portes["F3"] = portes_de(F3_16)
marca("F3 (recuperacio d'estrelles) i la seva porta")

# ---------------- supervivencia d'estrelles ----------------
oy, ox = np.mgrid[-12:13, -12:13]
ring = (oy ** 2 + ox ** 2 >= 64) & (oy ** 2 + ox ** 2 <= 144)
OY, OX = oy[ring].astype(np.int32), ox[ring].astype(np.int32)


def contrasts(L, ys, xs):
    vals = L[ys[:, None] + OY[None, :], xs[:, None] + OX[None, :]]
    return L[ys, xs] - np.median(vals, axis=1)


surv = {}
if len(est):
    xs = est[:, 0].astype(np.int32)
    ys = est[:, 1].astype(np.int32)
    cref = contrasts(L1, ys, xs)
    contr = {}
    for nom, arr in [("F1", F1_16), ("F2", F2_16), ("F3", F3_16)]:
        Lx = lum_f32(arr)
        contr[nom] = contrasts(Lx, ys, xs)
        del Lx
    rr_e = rR[ys, xs]
    m_e = est[:, 4]
    en_fons = m_e > 0.5
    taula = {}
    for r0, r1 in [(2.5, 3.5), (3.5, 5.0), (5.0, 7.0), (7.0, 9.0), (9.0, 11.2)]:
        sel = (rr_e >= r0) & (rr_e < r1) & en_fons & (cref > 0)
        n = int(sel.sum())
        fila = {"n": n}
        for nom in ("F1", "F2", "F3"):
            fila[nom] = float(np.mean(contr[nom][sel] >= 0.5 * cref[sel])) if n else None
        taula[f"{r0}-{r1}"] = fila
    seltot = en_fons & (cref > 0)
    surv = {
        "n_detectades": int(len(est)),
        "n_en_fons_substituit_m>0.5": int(seltot.sum()),
        "sobreviuen (contrast>=50% del de capa1)": {
            nom: {"n": int(np.sum(contr[nom][seltot] >= 0.5 * cref[seltot])),
                  "fraccio": float(np.mean(contr[nom][seltot] >= 0.5 * cref[seltot]))}
            for nom in ("F1", "F2", "F3")},
        "contrast_residual_mitja_relatiu": {
            nom: float(np.mean(np.clip(contr[nom][seltot] / cref[seltot], 0, 2)))
            for nom in ("F1", "F2", "F3")},
        "per_calaix_de_radi": taula,
        "recuperades_per_F3_que_F1_perdia": int(np.sum(
            (contr["F3"][seltot] >= 0.5 * cref[seltot]) & (contr["F1"][seltot] < 0.5 * cref[seltot]))),
    }
del L1, LBdet, D
marca("supervivencia d'estrelles")

# ---------------- vistes i desats ----------------
def vista(nom, arr16):
    v = (arr16[::4, ::4, ::-1].astype(np.float32) / 257.0)
    cv2.imwrite(os.path.join(OUT, nom), np.clip(v + 0.5, 0, 255).astype(np.uint8))


vista("vista_F1_pere.png", F1_16)
vista("vista_F2_prototip.png", F2_16)
vista("vista_F3_estrelles.png", F3_16)
vista("vista_B_fons.png", B16)

dif = np.zeros((H, W), np.float32)
for ch in range(3):
    dif += np.abs(F2_16[..., ch].astype(np.float32) - F1_16[..., ch].astype(np.float32))
dif /= 3.0
stats_dif = {"mitjana": float(dif.mean() / 65535.0),
             "mediana": float(np.median(dif) / 65535.0),
             "p99": float(np.percentile(dif, 99) / 65535.0),
             "max": float(dif.max() / 65535.0)}
v8 = np.clip(dif[::4, ::4] * AMP_DIF / 257.0 + 0.5, 0, 255).astype(np.uint8)
cv2.imwrite(os.path.join(OUT, "vista_dif_F2_F1_x16.png"), v8)
del dif

np.save(os.path.join(OUT, "B_rgb16.npy"), B16)
np.save(os.path.join(OUT, "F2_rgb16.npy"), F2_16)
np.save(os.path.join(OUT, "F3_rgb16.npy"), F3_16)
np.save(os.path.join(OUT, "estrelles_xy_c_area_m.npy"), est)
marca("vistes i npy desats")

informe = {
    "parametres": {"NT": NT, "NR": NR, "R0": R0, "R1": R1, "DLNR": DLNR,
                   "prefiltre_px": PREF_SIGMA_PX, "mediana_mostres": MED_K,
                   "sigmes_provades": llista, "sigma_triada": SIGMA_TRIADA,
                   "sectors": N_SECTORS, "anells_fidelitat": ANELLS_FIDELITAT,
                   "llindars_detec": [DET_CC_NSIG, DET_PIC_NSIG],
                   "sigma_fons_deteccio": SIGMA_DET,
                   "amplificacio_vista_dif": AMP_DIF},
    "geometria": geo,
    "seleccio_sigma": sel_sigma,
    "portes": portes,
    "estrelles": surv,
    "dif_F2_F1_lum": stats_dif,
    "troballes": [
        "El bony maxim de TOTS els candidats (F1 de Pere inclos) queia als sectors "
        "que apunten a la vora superior del llenc (5,78 R sol): salt de poblacio de "
        "rajos, no bony fisic; la porta exigeix ara >= mitat de rajos valids per calaix.",
        "A r=8 la fidelitat azimutal total premia el gra del cel radialment incoherent "
        "que el zoom de Photoshop conserva i B neteja: la corr de baixa frequencia "
        "(lambda>15 graus) hi queda igualada (0,9982 vs 0,9996).",
        "Els hibrids (part azimutalment lenta aplanada fort + detall azimutal fi) NO "
        "dominen: els bonys interiors reals son azimutalment estrets (15-60 graus) i "
        "travessen la particio azimutal.",
        "La vista |F2-F1|x16 ensenya al F1 de Pere ratlles radials a cada estrella i "
        "empremtes rectes de les cantonades pintades a ma arrossegades pel desenfoc; "
        "el pes normalitzat del prototip les evita per construccio.",
    ],
    "temps_s": TEMPS,
}
with open(os.path.join(OUT, "informe.json"), "w") as f:
    json.dump(informe, f, indent=1, ensure_ascii=False)
marca("informe.json")
print(json.dumps({"sigma": SIGMA_TRIADA,
                  "estrelles": surv.get("sobreviuen (contrast>=50% del de capa1)", {}),
                  "dif": stats_dif}, ensure_ascii=False))
