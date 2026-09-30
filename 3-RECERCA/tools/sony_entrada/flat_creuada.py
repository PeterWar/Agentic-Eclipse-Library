"""El flat del dither, VALIDAT FORA DE MOSTRA (i amb la constant per parella
com a PARAMETRE, no restada a ma).

Dues coses que la primera versio feia malament i que aqui es corregeixen:

1. **La constant per parella es restava com a mediana de `q`** abans d'ajustar.
   Aixo no es el mateix que ajustar-la: cada parella cobreix una distribucio de
   radis diferent, o sigui que forcar la seva mediana a zero injecta senyal a
   `lnF`. Aqui la constant es una incognita mes.
2. **No hi havia validacio fora de mostra.** Un model radial amb 40 graus de
   llibertat sempre baixa el residu de les dades amb que s'ha ajustat. L'unica
   prova que val es: ajusta amb sis parelles, prediu la setena.

Veredicte honest: si la rms de la parella deixada fora **no baixa**, el model
no ha mesurat el flat, ha memoritzat el soroll (o una altra cosa).
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from flat_pel_salt import CAN, PARELLES, darrer, plans_calibrats   # noqa: E402

NB = 40


def ajusta(iA, iB, ip, q, nb=NB, npar=None):
    """lnF(nb) + una constant per parella, tot alhora, per minims quadrats."""
    npar = npar or (int(ip.max()) + 1)
    n = nb + npar
    A = np.zeros((n, n)); b = np.zeros(n)
    # residu = lnF[iA] - lnF[iB] + c[ip] - q
    np.add.at(A, (iA, iA), 1.0); np.add.at(A, (iB, iB), 1.0)
    np.add.at(A, (iA, iB), -1.0); np.add.at(A, (iB, iA), -1.0)
    np.add.at(A, (iA, nb + ip), 1.0); np.add.at(A, (nb + ip, iA), 1.0)
    np.add.at(A, (iB, nb + ip), -1.0); np.add.at(A, (nb + ip, iB), -1.0)
    np.add.at(A, (nb + ip, nb + ip), 1.0)
    np.add.at(b, iA, q); np.add.at(b, iB, -q); np.add.at(b, nb + ip, q)
    A[0, :] = 0.0; A[0, 0] = 1.0; b[0] = 0.0          # gauge: lnF(0) = 0
    x = np.linalg.lstsq(A + 1e-6 * np.eye(n), b, rcond=None)[0]
    return x[:nb], x[nb:]


def rms_parella(lnF, iA, iB, q):
    """rms de q un cop tret el model, amb la constant lliure (la transparencia
    d'una parella que no s'ha vist mai no es pot coneixer).

    Torna tambe la rms del MODEL mateix: es el guany que hi hauria si el model
    fos exacte i el soroll independent. Sense aquest numero, un «+2 %» no es
    pot llegir: podria ser tot el que hi havia o una cinquena part.
    """
    pred = lnF[iA] - lnF[iB]
    pred = pred - np.median(pred)
    r = q - lnF[iA] + lnF[iB]
    return (float(np.std(r - np.median(r))), float(np.std(q - np.median(q))),
            float(np.std(pred)))


if __name__ == "__main__":
    d = darrer(sys.argv[1] if len(sys.argv) > 1 else "SONYTOT")
    sys.path.insert(0, os.path.join(d, "codi"))
    import comu, f0
    from astropy.io import fits
    run = comu.Run.obre(d)
    S = run.llegeix_rebut("F1.3_registre.json")["fotogrames"]
    flat = fits.getdata(run.fase(0, "FLAT_RADIAL.fits")).astype(np.float32)
    dk = {}
    print(f"run {os.path.basename(d)}\n")

    import cv2
    Q = {c: [] for c in CAN}
    usades = []
    for ip, (na, nb_) in enumerate(PARELLES):
        if na not in S or nb_ not in S:
            continue
        va, vb = S[na], S[nb_]
        PAn, g = plans_calibrats(comu, f0, run, na, va, flat, dk)
        PBn, _ = plans_calibrats(comu, f0, run, nb_, vb, flat, dk)
        M = np.float32([[1, 0, -(vb["sol_x"] - va["sol_x"]) / 2.0],
                        [0, 1, -(vb["sol_y"] - va["sol_y"]) / 2.0]])
        j = len(usades)
        for ic in CAN:
            pa, sa, ra = PAn[ic]; pb, sb, rb = PBn[ic]
            sz = (pa.shape[1], pa.shape[0])
            pbw = cv2.warpAffine(pb, M, sz, cv2.INTER_LINEAR, borderValue=np.nan)
            sbw = cv2.warpAffine(sb.astype(np.float32), M, sz, cv2.INTER_LINEAR,
                                 borderValue=1.0)
            rbw = cv2.warpAffine(rb, M, sz, cv2.INTER_LINEAR, borderValue=np.nan)
            k = (np.isfinite(pbw) & np.isfinite(rbw) & (sa < 0.01) & (sbw < 0.01)
                 & (pa > 50) & (pbw > 50))
            if k.sum() < 20000:
                continue
            # submostreig: 57 M de parells no calen i la validacio creuada en fa 7
            idx = np.nonzero(k.ravel())[0][::8]
            Q[ic].append((np.log(pa.ravel()[idx] / pbw.ravel()[idx]),
                          ra.ravel()[idx], rbw.ravel()[idx], j))
        usades.append((na, nb_, float(va["exp"])))
        print(f"  parella {j}: {na} · {nb_}  ({va['exp']:g} s)", flush=True)

    npar = len(usades)
    print(f"\nVALIDACIO CREUADA: {npar} parelles, es deixa una fora cada vegada\n")
    print(f"{'canal':>6s} {'parella deixada fora':>22s} {'rms sense':>10s} "
          f"{'rms amb':>9s} {'guany':>7s} {'esperat':>8s} {'assolit':>8s}")
    RES = {}
    for ic, cn in CAN.items():
        if not Q[ic]:
            continue
        qs = np.concatenate([t[0] for t in Q[ic]])
        ra = np.concatenate([t[1] for t in Q[ic]])
        rb = np.concatenate([t[2] for t in Q[ic]])
        ip = np.concatenate([np.full(len(t[0]), t[3], np.int64) for t in Q[ic]])
        rmax = float(max(ra.max(), rb.max()))
        iA = np.clip((ra / rmax * NB).astype(np.int64), 0, NB - 1)
        iB = np.clip((rb / rmax * NB).astype(np.int64), 0, NB - 1)
        k = iA != iB
        iA, iB, ip, qs = iA[k], iB[k], ip[k], qs[k]
        # ajust sencer (amb constant per parella lliure)
        lnF, _ = ajusta(iA, iB, ip, qs, npar=npar)
        RES[cn] = (rmax, lnF)
        gu = []
        for j in range(npar):
            f = ip != j
            lf, _ = ajusta(iA[f], iB[f], ip[f], qs[f], npar=npar)
            r1, r0, rm = rms_parella(lf, iA[~f], iB[~f], qs[~f])
            gu.append(100 * (1 - r1 / r0))
            esp = 100 * (1 - math.sqrt(max(1 - (rm / r0) ** 2, 0.0)))
            print(f"{cn:>6s} {usades[j][0] + ' · ' + usades[j][1]:>22s} "
                  f"{r0:10.4f} {r1:9.4f} {gu[-1]:+6.1f}% {esp:7.1f}% "
                  f"{100*gu[-1]/max(esp,1e-9):7.0f}%")
        print(f"{cn:>6s} {'MITJANA':>22s} {'':>10s} {'':>9s} "
              f"{np.mean(gu):+6.1f}%\n")

    print("amplitud del lnF ajustat amb la constant LLIURE (contra la versio "
          "amb la mediana restada):")
    vell = json.load(open(os.path.join(AQUI, "flat_dither.json")))
    for cn in ("R", "G1", "B", "G2"):
        if cn not in RES:
            continue
        a = 100 * (math.exp(np.ptp(RES[cn][1])) - 1)
        b = 100 * (math.exp(np.ptp(np.array(vell["lnF"][cn]))) - 1)
        c = float(np.corrcoef(RES[cn][1], np.array(vell["lnF"][cn]))[0, 1])
        print(f"  {cn:>2s}: {a:5.2f} %  (abans {b:5.2f} %)   forma x forma {c:6.3f}")
    json.dump({"r_sensor_px": ((np.arange(NB) + 0.5) / NB * RES["G1"][0]).tolist(),
               "rmax_px": RES["G1"][0],
               "lnF": {c: RES[c][1].tolist() for c in RES}},
              open(os.path.join(AQUI, "flat_dither_lliure.json"), "w"), indent=1)
