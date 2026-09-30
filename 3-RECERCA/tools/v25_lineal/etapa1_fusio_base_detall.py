#!/usr/bin/env python3
"""V25 LINEAL · etapa 1: fusió lineal dels dos trens al llenç comú, base amb la
corba B (0,22 / 0,74 / 0,045, decisió de Pere del 02-09) i mapes de detall.

Entrades: runs vigents de la cadena determinista (019 VIXEN, 016 SONYTOT),
tots dos al llenç comú 8096×8960 nord amunt, Sol al centre, R☉ 440,6 px.

Passos (tots al RECTANGLE sencer; cap filtre circular):
  1. cada tren → sRGB lineal amb la SEVA matriu i guany (CIENCIA);
  2. igualació ρ de la Sony a la Vixen en baixa freqüència (radial × Fourier
     azimutal k≤2, per canal), finestra declarada 2,0-3,5 R☉, constant fora;
  3. fusió amb màscara smoothstep 2,00→2,65 R☉ (Vixen dins, Sony fora),
     validesa de cada tren;
  4. fons per raig del camp exterior (suavitzat només en ln r, σ 0,2, per raig,
     autoreferent) amb la rampa de Pere 2,45→3,25 R☉ i re-injecció d'estrelles;
  5. base: corba B sobre la LLUMINÀNCIA amb el croma restituït (comu.render_visual);
  6. detall: NRGF en ln r + ACHF multi-σ sobre ln(corona) per canal, MEDIANA de
     les tres realitzacions, suavitzat pel S/N, anivellat per anell (H1);
     i passa-alt σ 24 px; capes 0,5-neutres per a Superposar.
Sortides al cau: NPY float32/uint16 i un rebut JSON. Res s'escriu als runs.
"""
import os, sys, json, time
import numpy as np
from astropy.io import fits
from scipy.ndimage import gaussian_filter, map_coordinates, median_filter, maximum_filter
from scipy.ndimage import gaussian_filter1d

AQUI = os.path.dirname(os.path.abspath(__file__))
# ⛔ el pilot i la cadena tenen tots dos un `comu.py`: cada família es carrega
#    amb la seva ruta al davant, i el `comu` del pilot es treu de sys.modules
#    abans de carregar el de la cadena (f3 fa `import comu` i ha de trobar el bo).
sys.path.insert(0, "/Users/USUARI/Downloads/Eclipse 2026/research/tools/pilot_vixen_claude")
import filtres as fpil            # ACHF del pilot
import filtres_druckmuller as fd  # passa-alt amb pes
for _m in ("comu",):
    sys.modules.pop(_m, None)
sys.path.insert(0, "/Users/USUARI/Downloads/Eclipse 2026/research/tools/eclipse_determinista")
import comu, f3
assert hasattr(comu, "Run") and hasattr(f3, "suavitza_sn")

CAU = os.path.join(AQUI, "cau_v25"); os.makedirs(CAU, exist_ok=True)
sys.path.insert(0, "/Users/USUARI/Downloads/Eclipse 2026/.claude/skills/corregeix-artefactes/scripts")
import artefactes as art
GHOSTS_LLENC = json.load(open(os.path.join(CAU, "ghosts_llenc.json")))   # V28: el de 3 R☉ + les sis marques grogues de Pere al llenç (etapa0_ghosts_llenc.py)
RUNS = "/Users/USUARI/Desktop/Eclipse determinista/1-RUNS"
VIX = os.path.join(RUNS, "019_VIXEN_CIENCIA_20260827T212404Z")
SON = os.path.join(RUNS, "016_SONYTOT_CIENCIA_20260827T183356Z")
CORBA_B = dict(pend=0.22, anc=0.74, terra=0.045)
FINESTRA_RHO = (2.0, 3.5)       # R☉, declarada
MASCARA_FUSIO = (2.00, 2.65)    # R☉, la de la V17
RAMPA_FONS = (2.45, 3.25)       # R☉, la rampa de Pere (V19)
SIGMA_LNR = 0.20
T0 = time.time()
REBUT = {"corba": CORBA_B, "finestra_rho_Rsol": FINESTRA_RHO, "mascara_fusio_Rsol": MASCARA_FUSIO,
         "rampa_fons_Rsol": RAMPA_FONS, "sigma_lnr": SIGMA_LNR, "runs": {"vixen": VIX, "sony": SON}}


def marca(t):
    print(f"[{time.time()-T0:7.1f} s] {t}", flush=True)


def carrega(dir_run):
    run = comu.Run.obre(dir_run)
    S = run.llegeix_rebut("F1.2_sol_llenc.json")["llenc"]
    C = {c: fits.getdata(run.fase(2, f"CORONA_{c}.fits")).astype(np.float32) for c in comu.CANALS}
    CEL = {c: fits.getdata(run.fase(2, f"CEL_{c}.fits")).astype(np.float32) for c in comu.CANALS}
    P = fits.getdata(run.fase(2, "PES_G.fits")).astype(np.float32)
    return run, S, C, CEL, P


def smoothstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def rho_baixa_freq(uv, us, m, rad, theta, RS, nom):
    """ρ(r,θ) = radial(ln r) × azimutal(k≤2), per canal, a la finestra declarada."""
    lo, hi = FINESTRA_RHO
    a = m & (rad > lo * RS) & (rad < hi * RS) & (uv > 0) & (us > 0)
    q = np.where(a, uv / np.maximum(us, 1e-9), np.nan).astype(np.float32)
    # radial en ln r, per calaixos, INTERPOLAT
    lnr = np.log(np.maximum(rad, 1.0) / RS)
    nb = 40; edges = np.linspace(np.log(lo), np.log(hi), nb + 1); cen = 0.5 * (edges[1:] + edges[:-1])
    prof = np.full(nb, np.nan, np.float32)
    idx = np.clip(((lnr - edges[0]) / (edges[-1] - edges[0]) * nb).astype(np.int32), 0, nb - 1)
    for k in range(nb):
        s = a & (idx == k)
        if s.sum() > 2000:
            prof[k] = np.nanmedian(q[s])
    ok = np.isfinite(prof); prof = np.interp(cen, cen[ok], prof[ok])
    prof = gaussian_filter1d(prof, 2.0, mode="nearest")
    rho_r = np.interp(lnr, cen, prof, left=prof[0], right=prof[-1]).astype(np.float32)  # constant fora
    # azimutal k≤2 sobre q / rho_r
    res = np.where(a, q / rho_r, np.nan)
    nt = 72; tb = np.clip(((theta + np.pi) / (2 * np.pi) * nt).astype(np.int32), 0, nt - 1)
    az = np.full(nt, np.nan)
    for k in range(nt):
        s = a & (tb == k)
        if s.sum() > 500:
            az[k] = np.nanmedian(res[s])
    okt = np.isfinite(az); th = (np.arange(nt) + 0.5) / nt * 2 * np.pi - np.pi
    A = np.column_stack([np.ones(okt.sum()), np.cos(th[okt]), np.sin(th[okt]), np.cos(2 * th[okt]), np.sin(2 * th[okt])])
    coef, *_ = np.linalg.lstsq(A, az[okt], rcond=None)
    rho_az = (coef[0] + coef[1] * np.cos(theta) + coef[2] * np.sin(theta)
              + coef[3] * np.cos(2 * theta) + coef[4] * np.sin(2 * theta)).astype(np.float32)
    rho = rho_r * rho_az
    resid = np.abs(np.where(a, uv / np.maximum(us * rho, 1e-9), np.nan) - 1.0)
    REBUT.setdefault("rho", {})[nom] = {"radial_min_max": [float(prof.min()), float(prof.max())],
                                        "az_coef": [float(c) for c in coef],
                                        "residu_mediana_abans": float(np.nanmedian(np.abs(q - 1))),
                                        "residu_mediana_despres": float(np.nanmedian(resid))}
    return rho


def fons_per_raig(img, m, rad, theta, RS, nom, r0=1.9, r1=None, nt=4080, nr=1200):
    """Suavitzat només al llarg del raig (ln r), autoreferent; rampa de Pere; re-injecció d'estrelles."""
    H, W = img.shape
    if r1 is None:
        r1 = float(rad[m].max()) / RS + 0.05
    lnr0, lnr1 = np.log(r0), np.log(r1)
    lr = np.linspace(lnr0, lnr1, nr, dtype=np.float32); th = np.linspace(-np.pi, np.pi, nt, endpoint=False, dtype=np.float32)
    rr = np.exp(lr)[None, :] * RS; xx = W / 2.0 + rr * np.cos(th)[:, None]; yy = H / 2.0 + rr * np.sin(th)[:, None]
    val = np.where(m, img, np.nan).astype(np.float32)
    pol = map_coordinates(np.nan_to_num(val, nan=0.0), [yy, xx], order=1, mode="constant", cval=0.0)
    pv = map_coordinates(m.astype(np.float32), [yy, xx], order=1, mode="constant", cval=0.0) > 0.5
    # en ln del valor (positiu): omple els forats endavant per raig
    lp = np.where(pv & (pol > 0), np.log(np.maximum(pol, 1e-9)), np.nan).astype(np.float32)
    for i in range(nt):
        row = lp[i]; ok = np.isfinite(row)
        if ok.sum() < 10:
            lp[i] = np.nan; continue
        idx = np.where(ok, np.arange(nr), 0); np.maximum.accumulate(idx, out=idx)
        row = row[idx]; row[: np.argmax(ok)] = row[np.argmax(ok)]
        lp[i] = row
    d = (lnr1 - lnr0) / (nr - 1); s = SIGMA_LNR / d
    fi = median_filter(np.nan_to_num(lp, nan=0.0), size=(1, 11), mode="nearest")
    llis = gaussian_filter1d(fi, s, axis=1, mode="nearest")
    fi2 = gaussian_filter1d(fi, 0.05 / d, axis=1, mode="nearest")        # fons fi per a estrelles
    # tornar al cartesià
    rr_c = np.log(np.maximum(rad, 1.0) / RS); tt = theta
    ci = (rr_c - lnr0) / d; ti = (tt + np.pi) / (2 * np.pi) * nt
    dins = m & (rr_c >= lnr0)
    sm = np.exp(map_coordinates(llis, [ti, np.clip(ci, 0, nr - 1)], order=1, mode="wrap")).astype(np.float32)
    sf = np.exp(map_coordinates(fi2, [ti, np.clip(ci, 0, nr - 1)], order=1, mode="wrap")).astype(np.float32)
    ramp = smoothstep(rad / RS, *RAMPA_FONS).astype(np.float32) * dins
    # estrelles: residu positiu compacte sobre el fons fi (>4 σ local), dilatat 2 px
    resid = np.where(dins, img - sf, 0.0).astype(np.float32)
    sig = np.sqrt(np.maximum(gaussian_filter(resid * resid, 12.0), 1e-12))
    estr = (resid > 4.0 * sig) & dins
    estr = maximum_filter(estr.astype(np.uint8), size=5) > 0
    out = np.where(dins, img * (1 - ramp) + sm * ramp, img).astype(np.float32)
    out = np.where(estr, out + resid * ramp, out)
    REBUT.setdefault("fons_per_raig", {})[nom] = {"px_estrelles_reinjectats": int(estr.sum()),
                                                  "r0_Rsol": r0, "r1_Rsol": float(r1), "nt": nt, "nr": nr}
    return out


def nrgf_lnr(x, m, rad, RS, nb=900):
    """Mediana per calaix de ln r, INTERPOLADA, restada."""
    lnr = np.log(np.maximum(rad, 1.0) / RS); a = m & np.isfinite(x)
    lo, hi = float(lnr[a].min()), float(lnr[a].max())
    edges = np.linspace(lo, hi, nb + 1); cen = 0.5 * (edges[1:] + edges[:-1])
    idx = np.clip(((lnr - lo) / (hi - lo) * nb).astype(np.int32), 0, nb - 1)
    prof = np.full(nb, np.nan)
    for k in range(nb):
        s = a & (idx == k)
        if s.sum() > 300:
            prof[k] = np.median(x[s])
    ok = np.isfinite(prof); prof = np.interp(cen, cen[ok], prof[ok])
    return (x - np.interp(lnr, cen, prof)).astype(np.float32)


def capa_superposar(d, m, rad, RS, nom):
    """0,5-neutra: compressió suau, suavitzat pel S/N, anivellat per anell (H1)."""
    esc = float(np.percentile(np.abs(d[m]), 99)) / 1.5
    y = (0.5 + 0.5 * np.tanh(np.where(m, d, 0.0) / max(esc, 1e-6))).astype(np.float32)
    r = f3.suavitza_sn(y - 0.5, m, rad)
    y = 0.5 + (r[0] if isinstance(r, tuple) else r)
    r = f3.anivella(y, rad, m)
    y = (r[0] if isinstance(r, tuple) else r).astype(np.float32)
    pit, r_pitjor = f3.nivell_per_radi(y, rad, m, RS)      # ja és max |mediana − 0,5|
    h1 = float(pit)
    REBUT.setdefault("capes_detall", {})[nom] = {"escala_tanh": esc, "H1_max_abs_nivell_menys_0.5": h1, "H1_radi_pitjor_Rsol": float(r_pitjor),
                                                 "PASSA_H1": bool(h1 <= 0.05)}
    y = np.where(m, y, 0.5).astype(np.float32)
    return y


def main():
    marca("càrrega dels dos runs")
    rv, Sv, Cv, CELv, Pv = carrega(VIX); rs, Ss, Cs, CELs, Ps = carrega(SON)
    W, H, RS = Sv["W"], Sv["H"], Sv["R_sol_px"]; assert (Ss["W"], Ss["H"]) == (W, H)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rad = np.hypot(yy - H / 2.0, xx - W / 2.0).astype(np.float32); theta = np.arctan2(yy - H / 2.0, xx - W / 2.0).astype(np.float32)
    del yy, xx
    mv = comu.mascara_dada(Pv, rad); ms = comu.mascara_dada(Ps, rad)
    for c in comu.CANALS:
        mv &= np.isfinite(Cv[c]) & np.isfinite(CELv[c]); ms &= np.isfinite(Cs[c]) & np.isfinite(CELs[c])
    marca(f"màscares: vixen {mv.mean():.3f} · sony {ms.mean():.3f} de llenç")
    # 1. sRGB lineal per tren (amb cel i sense)
    _, uv = comu.lluminancia(np.dstack([Cv[c] + CELv[c] for c in comu.CANALS]), rv.matriu, rv.color["guany"])
    _, cv = comu.lluminancia(np.dstack([Cv[c] for c in comu.CANALS]), rv.matriu, rv.color["guany"])
    _, us = comu.lluminancia(np.dstack([Cs[c] + CELs[c] for c in comu.CANALS]), rs.matriu, rs.color["guany"])
    _, cs = comu.lluminancia(np.dstack([Cs[c] for c in comu.CANALS]), rs.matriu, rs.color["guany"])
    del Cv, CELv, Cs, CELs
    # ⛔ fora de la cobertura de cada tren els FITS porten NaN, i 0 × NaN = NaN:
    #    es posen a zero ABANS de la suma ponderada (allà el pes ja és zero).
    uv, cv, us, cs = (np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0) for x in (uv, cv, us, cs))
    marca("sRGB lineal fet")
    # 2. ρ per canal (Sony → Vixen), sobre el total amb cel
    mb = mv & ms
    for i, c in enumerate(comu.CANALS):
        rho = rho_baixa_freq(uv[..., i], us[..., i], mb, rad, theta, RS, c)
        us[..., i] *= rho; cs[..., i] *= rho
        marca(f"ρ {c}: {REBUT['rho'][c]}")
    del rho
    # 3. fusió
    wv = (1.0 - smoothstep(rad / RS, *MASCARA_FUSIO)) * mv; ws = (1.0 - wv) * ms
    wv = np.where(ms, wv, mv.astype(np.float32)); ws = np.where(mv, ws, ms.astype(np.float32))
    den = np.maximum(wv + ws, 1e-6); mf = (wv + ws) > 0
    uf = np.empty_like(uv); cf = np.empty_like(uv)
    for i in range(3):
        uf[..., i] = (wv * uv[..., i] + ws * us[..., i]) / den
        cf[..., i] = (wv * cv[..., i] + ws * cs[..., i]) / den
    del uv, us, cv, cs, wv, ws, den
    np.save(os.path.join(CAU, "mascara_fusio.npy"), mf)
    marca(f"fusió feta · cobertura {mf.mean():.3f}")
    # 4. fons per raig al camp exterior (per canal, sobre el total amb cel; el mateix sobre la corona sola)
    for i, c in enumerate(comu.CANALS):
        uf[..., i] = fons_per_raig(uf[..., i], mf, rad, theta, RS, "total_" + c)
        cf[..., i] = np.where(mf, np.maximum(cf[..., i], 0.0), 0.0)
        marca(f"fons per raig {c}")
    # G a l'ORIGEN (V27, 05-09): el ghost de la Sony a 3 R☉ (nucli de 25 px) s'esborra per inpainting
    # a la base amb cel I a la corona sola ABANS de la corba i de tots els filtres — cap moneda plana.
    REBUT["ghosts_inpaint"] = []
    for gh in GHOSTS_LLENC:
        bol = art.corregeix_bol(cf, gh["x"], gh["y"], r_in=gh["radi"] - 10, r_out=130) if gh.get("bol") else None      # el bol només al de 3 R☉
        art.tapa_inpaint(uf, gh["x"], gh["y"], gh["radi"]); art.tapa_inpaint(cf, gh["x"], gh["y"], gh["radi"])   # ploma per FORA del nucli
        art.clona_textura(uf, gh["x"], gh["y"], gh["radi"], gh["dx"], gh["dy"]); art.clona_textura(cf, gh["x"], gh["y"], gh["radi"], gh["dx"], gh["dy"])   # textura del veí tangencial
        REBUT["ghosts_inpaint"].append(dict(gh, bol_corona=bol, textura="clonada del veí tangencial (dx, dy)"))
    marca(f"ghosts esborrats a l'origen: {GHOSTS_LLENC}")
    np.save(os.path.join(CAU, "fusio_srgb_lin_total.npy"), uf)
    # 5. base amb la corba B
    L = ((uf[..., 0] + 2.0 * uf[..., 1] + uf[..., 2]) / 4.0).astype(np.float32)
    va = comu.ancora(L, rad, mf, RS)
    y = comu.corba_to(L, mf, va, **CORBA_B)
    sigma = 24.0; mfl = mf.astype(np.float32); dn = np.maximum(comu._suau(mfl, sigma), 1e-6)
    LS = comu._suau(np.where(mf, L, 0.0), sigma) / dn
    q = np.empty_like(uf)
    for i in range(3):
        q[..., i] = (comu._suau(np.where(mf, uf[..., i], 0.0), sigma) / dn) / np.maximum(LS, 1e-9)
    ylin = comu.a_lineal(y); qmax = q.max(axis=2)
    with np.errstate(divide="ignore", invalid="ignore"):
        wmax = np.where(qmax > 1.0, (1.0 / np.maximum(ylin, 1e-9) - 1.0) / (qmax - 1.0), np.inf)
    wg = np.clip(np.nan_to_num(wmax, nan=0.0, posinf=1.0), 0.0, 1.0).astype(np.float32)
    base = comu.a_srgb(ylin[..., None] * (1.0 + wg[..., None] * (q - 1.0)))
    base = np.where(mf[..., None], base, 0.0).astype(np.float32)
    del q, LS, dn, ylin, qmax, wmax, wg
    np.save(os.path.join(CAU, "base_B_rgb16.npy"), (np.clip(base, 0, 1) * 65535 + 0.5).astype(np.uint16))
    col = comu.mesura_color({c: base[..., i].astype(np.float64) for i, c in enumerate(comu.CANALS)}, rad, mf, RS)
    REBUT["base"] = {"ancora_va": float(va), "color_base_per_anell": col,
                     "nivell_G_mediana": {str(r): float(np.median(base[..., 1][mf & (np.abs(rad - r * RS) < 0.02 * RS)])) for r in (1.1, 1.5, 2.5, 4.0, 6.0)}}
    marca(f"base B feta · va {va:.1f} · color {col}")
    del base, y, L
    # 6. detall: NRGF + ACHF sobre ln(corona) per canal → mediana; passa-alt σ24
    md = mf & (rad > 1.05 * RS)
    reals = []
    for i, c in enumerate(comu.CANALS):
        x = np.where(mf & (cf[..., i] > 0), np.log(np.maximum(cf[..., i], 1e-9)), np.nan).astype(np.float32)
        ok = mf & np.isfinite(x)
        x = np.where(ok, x, 0.0)
        x = nrgf_lnr(x, ok, rad, RS)
        d, diag = fpil.achf(x, ok.astype(np.float32), (2, 4, 8, 16, 32))
        reals.append(np.where(ok, d, 0.0).astype(np.float32)); del x, d
        marca(f"ACHF {c}")
    dm = np.median(np.stack(reals, axis=0), axis=0).astype(np.float32); del reals
    np.save(os.path.join(CAU, "detall_achf_mediana_raw.npy"), dm)
    ya = capa_superposar(np.where(md, dm, 0.0), md, rad, RS, "ACHF_2-32px_mediana")
    np.save(os.path.join(CAU, "capa_achf_u16.npy"), (ya * 65535 + 0.5).astype(np.uint16)); del ya
    marca(f"capa ACHF: {REBUT['capes_detall']['ACHF_2-32px_mediana']}")
    lnL = np.where(md & (cf.sum(axis=2) > 0), np.log(np.maximum((cf[..., 0] + 2 * cf[..., 1] + cf[..., 2]) / 4.0, 1e-9)), 0.0).astype(np.float32)
    lnL = nrgf_lnr(lnL, md, rad, RS)
    dp, _ = fd.passa_alt(lnL, md.astype(np.float32), 24.0)
    yp = capa_superposar(np.where(md, dp, 0.0), md, rad, RS, "PASSA_ALT_24px")
    np.save(os.path.join(CAU, "capa_passalt24_u16.npy"), (yp * 65535 + 0.5).astype(np.uint16))
    marca(f"capa passa-alt: {REBUT['capes_detall']['PASSA_ALT_24px']}")
    REBUT["llenc"] = {"W": W, "H": H, "R_sol_px": RS}; REBUT["segons"] = time.time() - T0
    json.dump(REBUT, open(os.path.join(CAU, "rebut_etapa1.json"), "w"), indent=1, ensure_ascii=False, default=float)
    marca("FET etapa 1")


if __name__ == "__main__":
    main()
