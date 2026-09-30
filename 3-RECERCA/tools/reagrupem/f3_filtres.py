#!/usr/bin/env python3
"""FASE 3 · Filtres — només presentació, res que canviï el que la dada vol dir.

⛔⛔ **NORMA DEL RECTANGLE**: cap filtre es retalla a una circumferència. Tots
s'apliquen a TOT el rectangle i l'única cosa que els atura és que no hi hagi
dada. Si l'exterior surt lleig es repara aigües amunt, mai retallant un cercle.

⏭️ **El detall va per la MEDIANA de les tres realitzacions de canal**
(`research/107`): cada canal compon cada radi amb un joc de fotogrames
diferent, i la mediana entre R, G i B mata l'anomalia que això fabrica sense
matar l'estructura real.

⏭️ **Corba de to DECLARADA** (`research/108`): pendent 0,17 per dècada, àncora
0,68 a 1,05–1,15 R☉, terra 0,045, i el sostre del MÀXIM de la dada.
⛔ Mai percentils: `estira_log` amb [0,5 · 99,7] crema 1,67 dècades.
"""

from __future__ import annotations

import json, os, sys, time
import numpy as np, cv2
from astropy.io import fits

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comu  # noqa: E402

RS = 440.60
PEND, ANCORA, TERRA = 0.17, 0.68, 0.045
SNR_REF = 30.0    # DN: nivell on l'atenuació val 0,5


def gauss(a, s):
    k = int(6*s) | 1
    return cv2.GaussianBlur(a, (k, k), s)


def suau_emmascarat(a, m, s):
    """Gaussiana que no deixa entrar el no-dada."""
    num = gauss(np.where(m, a, 0.0).astype(np.float32), s)
    den = gauss(m.astype(np.float32), s)
    return np.where(den > 1e-6, num/np.maximum(den, 1e-9), 0.0).astype(np.float32)


def perfil_azimutal(a, rad, m, nb=900):
    """Perfil azimutal SUAVITZAT EN log r i amb pes de COBERTURA.

    ⛔ Sense això, l'NRGF fabrica un artefacte circular: més enllà del radi on
    l'anell deixa de caure sencer dins del rectangle, la mitjana i la
    dispersió azimutals es calculen només amb els CANTONS —que estan a la
    diagonal i tenen un altre nivell— i el filtre hi fa una frontera dura.
    Mesurat el 26-08 a la primera versió: disc brillant fins a ~4 R☉ i salt.

    La cura no és retallar (norma del rectangle) sinó fer el perfil ROBUST:
    mediana per calaix, suavitzat en log r amb pes de cobertura, de manera que
    on la cobertura baixa el perfil continua la tendència en lloc de saltar.
    """
    rmax = float(rad[m].max())
    lr = np.log10(np.maximum(rad, 1.0)/rmax)
    lo = float(np.log10(20.0/rmax))
    idx = np.clip(((lr - lo)/(0.0 - lo)*nb).astype(np.int32), 0, nb-1)
    c = np.bincount(idx[m], None, nb)
    s1 = np.bincount(idx[m], a[m], nb)
    mu = np.where(c > 30, s1/np.maximum(c, 1), np.nan)
    s2 = np.bincount(idx[m], (a[m]-mu[idx[m]])**2, nb)
    sd = np.sqrt(np.where(c > 30, s2/np.maximum(c, 1), np.nan))
    # cobertura de cada anell: fracció d'azimut amb dada (1 = anell sencer)
    ctot = np.bincount(idx.ravel(), None, nb)
    cob = c/np.maximum(ctot, 1)
    w = np.where(np.isfinite(mu), np.clip(cob, 0.02, 1.0)**2, 0.0)
    def suau(v, sig=14.0):
        x = np.where(np.isfinite(v), v, 0.0)*w
        k = np.exp(-0.5*(np.arange(-60, 61)/sig)**2)
        num = np.convolve(x, k, "same"); den = np.convolve(w, k, "same")
        return np.where(den > 1e-6, num/np.maximum(den, 1e-9), np.nan)
    mu = suau(mu); sd = suau(sd)
    for v in (mu, sd):
        bo = np.isfinite(v)
        if bo.any():
            v[~bo] = np.interp(np.flatnonzero(~bo), np.flatnonzero(bo), v[bo])
    return mu[idx], np.maximum(sd[idx], 1e-9)


def corba_to(v, rad, m):
    x = np.where(m & (v > 0), v, np.nan)
    an = m & (rad >= 1.05*RS) & (rad <= 1.15*RS) & np.isfinite(x)
    va = float(np.nanmedian(x[an]))
    y = ANCORA + PEND*np.log10(np.maximum(x, va*1e-9)/va)
    return np.clip(np.where(np.isfinite(y), y, TERRA), TERRA, 1.0).astype(np.float32), va


def main():
    t0 = time.time()
    os.makedirs(comu.F3, exist_ok=True)
    PRE = os.environ.get("CEL_PREFIX", "COLOR_cel_restat")
    C = {c: fits.getdata(os.path.join(comu.F2, f"{PRE}_{c}.fits")).astype(np.float32)
         for c in ("R", "G", "B")}
    P = fits.getdata(os.path.join(comu.F2, "LDIC_pes_G.fits")).astype(np.float32)
    H, W = C["G"].shape
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rad = np.hypot(yy - H/2.0, xx - W/2.0); del yy, xx
    m = (P > 0.02*P.max())
    for c in C: m &= np.isfinite(C[c])
    print(f"llenç {W}x{H} · dada al {100*m.mean():.1f} %", flush=True)

    # --- BASE amb la corba declarada
    base = np.zeros((H, W, 3), np.float32); anc = {}
    for i, c in enumerate(("R", "G", "B")):
        base[..., i], anc[c] = corba_to(C[c], rad, m)
    print(f"àncora 1,05–1,15 R☉ : " + "  ".join(f"{c}={anc[c]:.4g}" for c in anc), flush=True)

    # --- els filtres, un per canal, i després la MEDIANA entre canals
    filtres = {}
    lg = {c: np.where(m & (C[c] > 0), np.log10(np.maximum(C[c], 1e-6)), 0.0).astype(np.float32)
          for c in C}

    def mediana_canals(f):
        return np.median(np.dstack([f(c) for c in ("R", "G", "B")]), axis=2).astype(np.float32)

    def nrgf(c):
        mu, sd = perfil_azimutal(C[c], rad, m)
        return np.where(m, (C[c]-mu)/sd, 0.0).astype(np.float32)
    filtres["NRGF"] = mediana_canals(nrgf); print(f"  NRGF   [{time.time()-t0:.0f}s]", flush=True)

    def passalt(c):
        return np.where(m, lg[c] - suau_emmascarat(lg[c], m, 24.0), 0.0).astype(np.float32)
    filtres["PASSA_ALT"] = mediana_canals(passalt); print(f"  passa-alt [{time.time()-t0:.0f}s]", flush=True)

    def mgn(c):
        out = np.zeros((H, W), np.float32)
        for s in (6.0, 12.0, 24.0, 48.0, 96.0):
            mu = suau_emmascarat(lg[c], m, s)
            d = lg[c] - mu
            sd = np.sqrt(np.maximum(suau_emmascarat(d*d, m, s), 1e-12))
            out += np.arctan(3.0*d/sd)
        return np.where(m, out/5.0, 0.0).astype(np.float32)
    filtres["MGN"] = mediana_canals(mgn); print(f"  MGN    [{time.time()-t0:.0f}s]", flush=True)

    def radial(c):
        """Desenfoc RADIAL: es difumina en radi i es conserva l'estructura
        angular (els plomalls). Fet a l'espai (r, phi) i tornat."""
        nr, na = 1400, 2048
        rr = np.linspace(0, float(rad[m].max()), nr, dtype=np.float32)
        aa = np.linspace(0, 2*np.pi, na, endpoint=False, dtype=np.float32)
        X = (W/2.0 + rr[None, :]*np.sin(aa)[:, None]).astype(np.float32)
        Y = (H/2.0 - rr[None, :]*np.cos(aa)[:, None]).astype(np.float32)
        pol = cv2.remap(lg[c], X, Y, cv2.INTER_LINEAR, borderValue=0.0)
        polm = cv2.remap(m.astype(np.float32), X, Y, cv2.INTER_LINEAR, borderValue=0.0)
        sm = cv2.GaussianBlur(pol*polm, (1, 61), 0, sigmaY=10.0)
        sd = cv2.GaussianBlur(polm, (1, 61), 0, sigmaY=10.0)
        det = pol - np.where(sd > 1e-6, sm/np.maximum(sd, 1e-9), 0.0)
        # tornar a cartesianes
        yy2, xx2 = np.mgrid[0:H, 0:W].astype(np.float32)
        r2 = np.hypot(yy2-H/2.0, xx2-W/2.0); a2 = np.arctan2(xx2-W/2.0, H/2.0-yy2) % (2*np.pi)
        mx = (r2/rr[-1]*(nr-1)).astype(np.float32); my = (a2/(2*np.pi)*na).astype(np.float32)
        return np.where(m, cv2.remap(det, mx, my, cv2.INTER_LINEAR,
                                     borderMode=cv2.BORDER_WRAP), 0.0).astype(np.float32)
    filtres["RADIAL"] = mediana_canals(radial); print(f"  radial [{time.time()-t0:.0f}s]", flush=True)

    # --- atenuació per SENYAL/SOROLL (⛔ NO és un retall circular: segueix la
    # dada, no cap circumferència). Sense això, els cantons del rectangle —on
    # la corona val 6 DN sobre un cel de 450 que s'ha restat— surten a tot
    # contrast i fabriquen textura que no hi és.
    Pn = P/np.nanmax(P)
    snr = np.where(m, C["G"]*np.sqrt(np.maximum(Pn, 0))/SNR_REF, 0.0)
    aten = (snr**2/(snr**2 + 1.0)).astype(np.float32)
    print(f"  atenuació S/N: mediana {np.median(aten[m]):.3f}  "
          f"p5 {np.percentile(aten[m],5):.3f}  p95 {np.percentile(aten[m],95):.3f}")
    for k_ in filtres: filtres[k_] = (filtres[k_]*aten).astype(np.float32)

    rebut = {"corba_to": {"pendent": PEND, "ancora": ANCORA, "terra": TERRA,
                          "valor_ancora": anc,
                          "font": "research/108, DECLARADA no derivada"},
             "norma_rectangle": "cap filtre retallat a cap circumferència",
             "detall": "mediana de les tres realitzacions de canal (research/107)",
             "atenuacio_SN": {"ref_DN": SNR_REF,
                              "nota": "segueix la dada (senyal x sqrt(pes)), no cap "
                                      "circumferencia; evita fabricar textura on el "
                                      "senyal val 6 DN"},
             "filtres": {}}
    np.save(os.path.join(comu.F3, "BASE_rgb.npy"), base)
    for k, v in filtres.items():
        s = 1.4826*float(np.median(np.abs(v[m] - np.median(v[m]))))
        vis = np.clip(0.5 + v/(6.0*max(s, 1e-9)), 0, 1).astype(np.float32)
        np.save(os.path.join(comu.F3, f"DETALL_{k}.npy"), vis)
        rebut["filtres"][k] = {"sigma_robust": s,
                               "amplitud_p1_p99": [float(np.percentile(v[m], 1)),
                                                   float(np.percentile(v[m], 99))]}
        print(f"  {k:>10}: sigma robust {s:.5f}")
    np.save(os.path.join(comu.F3, "MASCARA.npy"), m)
    json.dump(rebut, open(os.path.join(comu.REBUTS, "F3_filtres.json"), "w"), indent=1)
    print(f"\nfet en {time.time()-t0:.0f} s -> {comu.F3}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
