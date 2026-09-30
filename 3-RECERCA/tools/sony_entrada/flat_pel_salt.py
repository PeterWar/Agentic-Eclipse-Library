"""El salt de muntura com a DITHER: mesura el flat sense flats.

La Skywatcher va saltar 749 px a mig de la totalitat, o sigui que **el mateix
punt del cel cau a dues posicions del sensor molt separades**. Si el flat es
correcte, el valor calibrat ha de ser el MATEIX als dos. Qualsevol residu que
depengui de la posicio al SENSOR (i no del cel) es error de flat.

Aixo es el control que a l'A7RIIIA li falta: no te flats invertits, i la porta
que la Vixen passa alla no existeix (research/115 §2). El salt el substitueix.

⚠️ Entre els dos apuntaments passen ~45 s i la transparencia va canviar durant
la totalitat: hi ha un factor escalar global que NO es error de flat. El test
mira la FORMA, no el nivell.

## Els TRES controls (27-08, ronda 2)

El primer que hi havia (meitats de PIXELS) nomes mesura soroll: els dos
subconjunts venen de les mateixes parelles i comparteixen qualsevol
sistematic. Se n'hi afegeixen dos que si que poden desmentir la mesura:

1. **Per PARELLES** (senars contra parells). Parelles diferents son instants
   diferents i exposicions diferents. Si el residu fos del CEL —una estructura
   de transparencia que va canviar entre els dos apuntaments— cada parella en
   veuria una de diferent i les dues meitats no coincidirien.
2. **Per NIVELL** (exposicions curtes contra llargues). Un residu MULTIPLICATIU
   (flat) val igual a qualsevol nivell; un d'ADDITIU (llum dispersa de la
   corona interior, que tambe esta fixada a l'eix optic) surt mes gran on el
   senyal es feble. Es l'unica alternativa fisica seriosa al flat i aquest
   control la separa.
"""
from __future__ import annotations
import json, math, os, sys
import numpy as np
import cv2
import rawpy

RUN = os.path.expanduser("~/Desktop/Eclipse determinista/1-RUNS")
AQUI = os.path.dirname(os.path.abspath(__file__))

# parelles (apuntament A, apuntament B) de la MATEIXA exposicio
PARELLES = [("DSC06982.ARW", "DSC06994.ARW"),   # 1/4 s
            ("DSC06982.ARW", "DSC06997.ARW"),   # 1/4 s
            ("DSC06983.ARW", "DSC06995.ARW"),   # 1/30 s
            ("DSC06983.ARW", "DSC06998.ARW"),   # 1/30 s
            ("DSC06984.ARW", "DSC06996.ARW"),   # 2 s
            ("DSC06984.ARW", "DSC06999.ARW"),   # 2 s
            ("DSC06986.ARW", "DSC06992.ARW"),   # 1/8 s
            ("DSC06973.ARW", "DSC07000.ARW"),   # 1/800 s
            ("DSC06975.ARW", "DSC07002.ARW")]   # 1/100 s

CAN = {0: "R", 1: "G1", 2: "B", 3: "G2"}
NB = 40


def darrer(tren="SONYTOT"):
    """Amb un nom de run sencer, l'agafa; amb un tren, el mes recent."""
    if os.path.isdir(os.path.join(RUN, tren)):
        return os.path.join(RUN, tren)
    # el run pot haver caigut a una porta de mes endavant: el que aquesta
    # mesura necessita (calibracio i registre) ja hi es igualment.
    pre = __import__("re").compile(r"^(\d{3,})_")
    ds = [d for d in os.listdir(RUN)
          if pre.sub("", d).startswith(f"{tren}_CIENCIA_")
          and not d.endswith(("_AVORTAT", "_FALLIT"))
          and os.path.exists(os.path.join(RUN, d, "4-rebuts", "F1.3_registre.json"))]
    ds.sort(key=lambda d: (int(pre.match(d).group(1)) if pre.match(d) else -1, d))
    if not ds:
        raise SystemExit(f"cap run acabat de {tren}")
    return os.path.join(RUN, ds[-1])


def plans_calibrats(comu, f0, run, nom, v, flat, dk_cache):
    """Els QUATRE plans CFA calibrats (dark, flat, exposicio) i el radi al SENSOR.

    Es llegeix el RAW **una sola vegada** per fotograma: la versio anterior el
    rellegia per canal i pagava 4x.
    """
    with rawpy.imread(comu.ruta_llum(run.tren, nom)) as r:
        raw = r.raw_image.astype(np.float32)
        mc = comu.mapa_colors(r)
        g = comu.geometria(r)
    e = v["exp"]
    if e not in dk_cache:
        dk_cache[e] = f0.dark_de(run, e)
    dk = dk_cache[e]
    out = {}
    for ic in CAN:
        ys, xs = np.nonzero(mc == ic); oy, ox = int(ys.min()), int(xs.min())
        sub = (raw[oy::2, ox::2] - dk[oy::2, ox::2]) / flat[oy::2, ox::2]
        sat = raw[oy::2, ox::2] >= 0.85 * (16383.0 - 512.0)
        h, w = sub.shape
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        rs = np.hypot(yy * 2 + oy - g.alt / 2.0, xx * 2 + ox - g.ample / 2.0)
        out[ic] = (sub / e, sat, rs)
    return out, g


def resol_flat(qs, rA, rB, nb=NB, rmax=None):
    """Inverteix ln q = const + lnF(rA) − lnF(rB) per minims quadrats.

    Es un problema de self-calibration classic: amb prou parells (rA, rB) ben
    separats, lnF queda determinada tret d'una constant (que es fixa a 0 al
    centre). El salt de 749 px es el que fa que rA i rB estiguin separats.
    """
    rmax = rmax or float(max(rA.max(), rB.max()))
    iA = np.clip((rA / rmax * nb).astype(np.int32), 0, nb - 1)
    iB = np.clip((rB / rmax * nb).astype(np.int32), 0, nb - 1)
    k = iA != iB
    iA, iB, q = iA[k], iB[k], qs[k]
    n = len(q)
    # matriu dispersa implicita: normal equations directament
    A = np.zeros((nb, nb)); b = np.zeros(nb)
    np.add.at(A, (iA, iA), 1.0); np.add.at(A, (iB, iB), 1.0)
    np.add.at(A, (iA, iB), -1.0); np.add.at(A, (iB, iA), -1.0)
    np.add.at(b, iA, q); np.add.at(b, iB, -q)
    A[0, :] = 0.0; A[0, 0] = 1.0; b[0] = 0.0          # gauge: lnF(0) = 0
    lnF = np.linalg.lstsq(A + 1e-6 * np.eye(nb), b, rcond=None)[0]
    rs = (np.arange(nb) + 0.5) / nb * rmax
    return rs, lnF, n


def _amp(lnF):
    return 100.0 * (math.exp(float(np.nanmax(lnF)) - float(np.nanmin(lnF))) - 1)


def _desacord(l1, l2):
    """Diferencia maxima entre dos perfils, tret del gauge (la mediana)."""
    d = (l1 - np.nanmedian(l1)) - (l2 - np.nanmedian(l2))
    return 100.0 * float(np.nanmax(np.abs(np.exp(d) - 1)))


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

    # ------------------------------------------- acumula (q, rA, rB) per canal
    Q = {c: [] for c in CAN}          # llistes de (q, ra, rb, i_parella, exp)
    for ip, (na, nb_) in enumerate(PARELLES):
        if na not in S or nb_ not in S:
            print(f"  parella {na} · {nb_}: fora (no registrada)")
            continue
        va, vb = S[na], S[nb_]
        PA, g = plans_calibrats(comu, f0, run, na, va, flat, dk)
        PB, _ = plans_calibrats(comu, f0, run, nb_, vb, flat, dk)
        dx = (vb["sol_x"] - va["sol_x"]) / 2.0
        dy = (vb["sol_y"] - va["sol_y"]) / 2.0
        M = np.float32([[1, 0, -dx], [0, 1, -dy]])
        usats = 0
        for ic in CAN:
            pa, sa, ra = PA[ic]
            pb, sb, rb = PB[ic]
            sz = (pa.shape[1], pa.shape[0])
            pbw = cv2.warpAffine(pb, M, sz, cv2.INTER_LINEAR, borderValue=np.nan)
            sbw = cv2.warpAffine(sb.astype(np.float32), M, sz, cv2.INTER_LINEAR,
                                 borderValue=1.0)
            rbw = cv2.warpAffine(rb, M, sz, cv2.INTER_LINEAR, borderValue=np.nan)
            k = (np.isfinite(pbw) & np.isfinite(rbw) & (sa < 0.01) & (sbw < 0.01)
                 & (pa > 50) & (pbw > 50))
            if k.sum() < 20000:
                continue
            q = np.log(pa[k] / pbw[k]); q -= np.median(q)
            Q[ic].append((q, ra[k], rbw[k], ip, float(va["exp"])))
            usats += 1
        print(f"  parella {na} · {nb_}: {usats}/4 canals · exp {va['exp']:g} s",
              flush=True)

    # ----------------------------------------------------------- resol i jutja
    RES, CTRL = {}, {}
    for ic, cn in CAN.items():
        if not Q[ic]:
            continue
        q = np.concatenate([t[0] for t in Q[ic]])
        ra = np.concatenate([t[1] for t in Q[ic]])
        rb = np.concatenate([t[2] for t in Q[ic]])
        ip = np.concatenate([np.full(len(t[0]), t[3]) for t in Q[ic]])
        ex = np.concatenate([np.full(len(t[0]), t[4]) for t in Q[ic]])
        rs, lnF, n = resol_flat(q, ra, rb)
        rmax = float(max(ra.max(), rb.max()))
        # control 1: meitats de PIXELS (nomes soroll)
        h = np.zeros(len(q), bool); h[::2] = True
        _, lA, _ = resol_flat(q[h], ra[h], rb[h], rmax=rmax)
        _, lB, _ = resol_flat(q[~h], ra[~h], rb[~h], rmax=rmax)
        # control 2: meitats per PARELLA (instants i exposicions diferents)
        pars = sorted(set(ip.tolist()))
        s1 = np.isin(ip, pars[0::2]); s2 = np.isin(ip, pars[1::2])
        _, lP1, _ = resol_flat(q[s1], ra[s1], rb[s1], rmax=rmax)
        _, lP2, _ = resol_flat(q[s2], ra[s2], rb[s2], rmax=rmax)
        # control 3: per NIVELL (multiplicatiu contra additiu)
        tall = float(np.median(sorted(set(ex.tolist()))))
        c_, l_ = ex <= tall, ex > tall
        _, lC, _ = resol_flat(q[c_], ra[c_], rb[c_], rmax=rmax)
        _, lL, _ = resol_flat(q[l_], ra[l_], rb[l_], rmax=rmax)
        # ⏭️ MULTIPLICATIU o ADDITIU: si el residu fos llum dispersa additiva,
        #    les exposicions CURTES i les LLARGUES en veurien la MATEIXA FORMA
        #    amb AMPLITUD diferent. Si el model radial es simplement incomplet,
        #    la forma tambe canvia. Es el que separa les dues explicacions.
        zc = lC - np.nanmedian(lC); zl = lL - np.nanmedian(lL)
        cor = float(np.corrcoef(zc, zl)[0, 1])
        raoa = _amp(lC) / max(_amp(lL), 1e-9)
        RES[cn] = (rs, lnF, n, len(Q[ic]), rmax)
        CTRL[cn] = {"pixels": _desacord(lA, lB), "parelles": _desacord(lP1, lP2),
                    "nivell": _desacord(lC, lL), "amp": _amp(lnF),
                    "amp_curtes": _amp(lC), "amp_llargues": _amp(lL),
                    "forma_curtes_x_llargues": cor, "rao_amplituds": raoa,
                    "tall_exp_s": tall}
        print(f"  {cn:>2s}: {len(Q[ic])} parelles · {n:,} parells de radis")

    rs = RES["G1"][0]
    print(f"\nERROR RESIDUAL DEL FLAT PER CANAL (%)")
    print(f"{'r sensor':>9s} " + " ".join(f"{c:>8s}" for c in ("R", "G1", "B", "G2"))
          + f" {'B − G':>8s}")
    for i in range(0, len(rs), 3):
        v = {c: 100 * (math.exp(RES[c][1][i]) - 1) for c in RES}
        bg = v.get("B", 0) - 0.5 * (v.get("G1", 0) + v.get("G2", 0))
        print(f"{rs[i]:9.0f} " + " ".join(f"{v.get(c, float('nan')):+8.2f}"
                                          for c in ("R", "G1", "B", "G2"))
              + f" {bg:+8.2f}")

    print(f"\n{'canal':>6s} {'amplitud':>9s} | {'px':>7s} {'PARELLES':>9s} {'NIVELL':>8s}"
          "   (desacord entre meitats, %)")
    pitjor_p = pitjor_n = 0.0
    for c in ("R", "G1", "B", "G2"):
        if c not in CTRL:
            continue
        t = CTRL[c]
        pitjor_p = max(pitjor_p, t["parelles"]); pitjor_n = max(pitjor_n, t["nivell"])
        print(f"{c:>6s} {t['amp']:8.2f} % | {t['pixels']:6.2f} % {t['parelles']:8.2f} % "
              f"{t['nivell']:7.2f} %")
    print(f"\n{'canal':>6s} {'amp curtes':>11s} {'amp llargues':>13s} {'rao':>6s} "
          f"{'forma c x ll':>13s}")
    for c in ("R", "G1", "B", "G2"):
        if c in CTRL:
            t = CTRL[c]
            print(f"{c:>6s} {t['amp_curtes']:10.2f} % {t['amp_llargues']:12.2f} % "
                  f"{t['rao_amplituds']:6.2f} {t['forma_curtes_x_llargues']:13.3f}")
    print()
    print(f"  PARELLES {pitjor_p:5.2f} %  → {'CEL descartat' if pitjor_p < 3 else '⛔ podria ser CEL'}"
          f" (instants i exposicions diferents veuen el MATEIX residu)")
    print(f"  NIVELL   {pitjor_n:5.2f} %  → {'ADDITIU descartat' if pitjor_n < 3 else '⛔ podria ser ADDITIU'}"
          f" (curtes i llargues veuen el MATEIX residu)")

    if "B" in RES and "G1" in RES:
        bg = np.exp(RES["B"][1]) / np.exp(0.5 * (RES["G1"][1] + RES["G2"][1]))
        print(f"\n⏭️ B/G: de {100*(bg.min()-1):+.2f} % a {100*(bg.max()-1):+.2f} % "
              f"pel camp · amplitud {100*(bg.max()/bg.min()-1):.2f} %")

    # ------------------------------------------------------------- desa taula
    out = {"font": os.path.basename(d),
           "metode": "self-calibration sobre el salt de muntura (dither de 749 px)",
           "gauge": "lnF(0) = 0; el nivell absolut NO es toca",
           "convencio": "FLAT_corregit(r) = FLAT(r) * exp(lnF(r)) per canal CFA",
           "r_sensor_px": rs.tolist(), "rmax_px": RES["G1"][4],
           "lnF": {c: RES[c][1].tolist() for c in RES},
           "n_parells": {c: RES[c][2] for c in RES},
           "n_parelles": {c: RES[c][3] for c in RES},
           "controls_pct": CTRL}
    p = os.path.join(AQUI, "flat_dither.json")
    json.dump(out, open(p, "w"), indent=1)
    print(f"\ntaula desada a {p}")
