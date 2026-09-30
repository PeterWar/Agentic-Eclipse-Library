"""FASE 1 · Registre — només geometria. Res de fotometria.

⛔ El centre absolut és el del **Sol per EFEMÈRIDE**, mai el limbe visible, que
és el de la LLUNA i llisca 28,5 px durant la totalitat.

⏭️ **El registre fi es fa per CORRELACIÓ DE FASE contra el compost, no pel
limbe.** Mesurat el 26-08: l'ajust del limbe té 0,4-0,7 px d'error propi —el
glare de la corona se'l menja i el radi ajustat cau 1,3 px de 1/1000 s a 1 s—
mentre que la correlació dona 0,095 px. El limbe només serveix per arrencar.
"""

from __future__ import annotations

import math
import os
import subprocess
import time

import numpy as np
import cv2
import rawpy
from astropy.io import fits

import comu
import f0

NAZ = 720
SALT_APUNTAMENT_PX = 40.0   # per damunt d'aixo ja no es deriva: es un salt
# ⛔ El radi lunar nominal NO és una constant del projecte: és del TREN. Escrit
#    a mà valia 460 px, que és el de la Vixen; a la Sony n'hi corresponen 306 i
#    amb 460 la cerca del limbe s'enganxava a un altre gradient (mesurat el
#    27-08: donava R = 477 px i només 4 fotogrames de 14). Només cal que caigui
#    dins del ±13 % de la finestra de cerca, o sigui que la relació declarada
#    R_lluna/R_sol del dia hi basta.
RATIO_LLUNA_SOL = 1.0338


def r_lluna_nominal_px(cfg) -> float:
    return cfg["rsol_arcsec"] * RATIO_LLUNA_SOL / cfg["escala_arcsec_px"]


# ------------------------------------------------------------- cronologia


def cronologia(run: comu.Run) -> dict:
    """{fitxer: (exposicio, t_relatiu)}. L'EXIF de la R6 III és l'INICI de
    l'exposició: amb el final, els fotogrames d'1 s i 2 s se solaparien 0,10 s."""
    cfg = run.cfg
    # ⛔ Sobre TOTS els fitxers de llum, que poden venir de mes d'una carpeta i
    #    amb exclusions: passar-li la carpeta llegiria tambe els exclosos.
    o = subprocess.run(["exiftool", "-q", "-n", "-T", "-FileName", "-ExposureTime",
                        "-SubSecDateTimeOriginal"] + comu.llums(run.tren),
                       capture_output=True, text=True, timeout=1800).stdout
    d = {}
    for l in o.splitlines():
        p = l.split("\t")
        if len(p) < 3 or not p[0].upper().endswith(cfg["ext"].lstrip(".")):
            continue
        hh, mm, ss = p[2][11:13], p[2][14:16], p[2][17:].split("+")[0]
        d[p[0]] = (float(p[1]), int(hh) * 3600 + int(mm) * 60 + float(ss))
    return dict(sorted(d.items()))


def _efem(run: comu.Run):
    from skyfield.api import load, wgs84
    eph = load(comu.EFEM); tsc = load.timescale()
    lloc = eph["earth"] + wgs84.latlon(comu.LLOC[0], comu.LLOC[1], elevation_m=comu.LLOC[2])
    return eph, tsc, lloc


def _base(pa_deg):
    a = math.radians(pa_deg)
    return np.array([math.sin(a), -math.cos(a)])


def contactes_i_offsets(run: comu.Run, cronos: dict) -> dict:
    """C2/C3 per efemèride i el vector (Lluna − Sol) en px de cada fotograma."""
    import scipy.optimize as so
    cfg = run.cfg
    eph, tsc, lloc = _efem(run)
    n_ = _base(cfg["pa_north_deg"]); e_ = _base(cfg["pa_north_deg"] + 268.398)
    esc = cfg["escala_arcsec_px"]

    def estat(tl):
        u = tl - comu.UTC_OFF_H * 3600.0
        t = tsc.utc(comu.DIA[0], comu.DIA[1], comu.DIA[2],
                    int(u // 3600), int((u % 3600) // 60), u % 60)
        obs = lloc.at(t)
        mra, mdec, md = obs.observe(eph["moon"]).apparent().radec()
        sra, sdec, sd = obs.observe(eph["sun"]).apparent().radec()
        de = (mra.radians - sra.radians) * math.cos(sdec.radians) * 206264.806
        dn = (mdec.radians - sdec.radians) * 206264.806
        Rm = math.degrees(math.asin(1737.4 / md.km)) * 3600
        Rs = math.degrees(math.asin(696000.0 / (sd.au * 1.495978707e8))) * 3600
        return de, dn, Rm, Rs

    t0 = min(v[1] for v in cronos.values())
    t9 = max(v[1] for v in cronos.values())
    # ⛔ La finestra NO es pot ancorar al primer fotograma. Amb la Vixen el
    #    primer és 14 s ABANS de C2 i el truc de `t0 + 65` funcionava; amb els
    #    14 de la Sony el primer ja és 59 s DINS de la totalitat, la finestra
    #    engolia C2 i C3 alhora i `brentq` fallava amb «f(a) and f(b) must have
    #    different signs». Aquí es busca el canvi de signe damunt d'una graella
    #    ampla i s'exigeix que n'hi hagi EXACTAMENT DOS.
    f = lambda tl: math.hypot(*estat(tl)[:2]) - (estat(tl)[2] - estat(tl)[3])
    graella = np.arange(t0 - 600.0, t9 + 600.0, 5.0)
    v = np.array([f(x) for x in graella])
    canvis = np.nonzero(np.sign(v[:-1]) != np.sign(v[1:]))[0]
    if len(canvis) != 2:
        raise SystemExit(f"PORTA F1.2: s'esperaven dos contactes a la finestra i "
                         f"n'han sortit {len(canvis)}. Els fotogrames cobreixen "
                         f"{t9 - t0:.0f} s; revisa la cronologia.")
    c2 = so.brentq(f, graella[canvis[0]], graella[canvis[0] + 1])
    c3 = so.brentq(f, graella[canvis[1]], graella[canvis[1] + 1])
    de0, dn0, Rm, Rs = estat((c2 + c3) / 2)

    off = {}
    for n, (e, t) in cronos.items():
        de, dn, _, _ = estat(t + e / 2.0)      # instant MIG de l'exposició
        v = (de * e_ + dn * n_) / esc
        off[n] = {"dx": float(v[0]), "dy": float(v[1]), "t": t - t0, "exp": e}
    return {"C2_t": c2 - t0, "C3_t": c3 - t0, "totalitat_s": c3 - c2,
            "R_lluna_arcsec": Rm, "R_sol_arcsec": Rs,
            "R_sol_px": Rs / esc, "R_lluna_px": Rm / esc, "offsets": off}


# ------------------------------------------------------------- 1.1 limbe


def _centre_anell(gp, pct=99.0):
    import scipy.ndimage as ndi
    s = ndi.uniform_filter(gp, 9)
    ll = np.percentile(s, pct)
    m = s >= ll
    if m.sum() < 500:
        return gp.shape[0] / 2, gp.shape[1] / 2
    w = np.where(m, s - ll, 0.0)
    yy, xx = np.mgrid[0:gp.shape[0], 0:gp.shape[1]]
    tot = w.sum()
    return float((w * yy).sum() / tot), float((w * xx).sum() / tot)


def _punts(gp, cy, cx, R):
    az = np.linspace(0, 2 * np.pi, NAZ, endpoint=False)
    rs = np.arange(R - 0.13 * R, R + 0.13 * R, 0.25)
    ys = cy + rs[None, :] * np.cos(az)[:, None]
    xs = cx + rs[None, :] * np.sin(az)[:, None]
    ok = (ys > 1) & (ys < gp.shape[0] - 2) & (xs > 1) & (xs < gp.shape[1] - 2)
    yi = np.clip(ys, 0, gp.shape[0] - 1).astype(np.int32)
    xi = np.clip(xs, 0, gp.shape[1] - 1).astype(np.int32)
    prof = np.where(ok, gp[yi, xi], np.nan)
    q = int(0.25 * len(rs))
    dins = np.nanmedian(prof[:, :q], axis=1); fora = np.nanmedian(prof[:, -q:], axis=1)
    ll = 0.5 * (dins + fora)
    pts = []
    for k in range(NAZ):
        p = prof[k]
        if not np.isfinite(ll[k]) or fora[k] - dins[k] < 3:
            continue
        idx = np.where(p >= ll[k])[0]
        if idx.size == 0 or idx[0] == 0:
            continue
        j = idx[0]
        if not (np.isfinite(p[j - 1]) and np.isfinite(p[j])) or p[j] == p[j - 1]:
            continue
        pts.append((rs[j - 1] + (ll[k] - p[j - 1]) / (p[j] - p[j - 1]) * 0.25, az[k]))
    return np.array(pts) if pts else np.zeros((0, 2))


def _cercle(pts, cy, cx):
    r, a = pts[:, 0], pts[:, 1]
    y = cy + r * np.cos(a); x = cx + r * np.sin(a)
    for _ in range(6):
        A = np.c_[x, y, np.ones_like(x)]
        sol, *_ = np.linalg.lstsq(A, x ** 2 + y ** 2, rcond=None)
        Cx, Cy = sol[0] / 2, sol[1] / 2
        R = math.sqrt(sol[2] + Cx ** 2 + Cy ** 2)
        d = np.hypot(x - Cx, y - Cy) - R
        s = 1.4826 * np.median(np.abs(d - np.median(d)))
        bo = np.abs(d - np.median(d)) < 2.5 * max(s, 0.05)
        if bo.sum() < 60:
            break
        x, y = x[bo], y[bo]
    return float(Cy), float(Cx), float(R), int(len(x)), float(np.std(np.hypot(x - Cx, y - Cy) - R))


def limbe(run: comu.Run) -> dict:
    cronos = cronologia(run)
    cfg = run.cfg
    with rawpy.imread(comu.entrades(run.tren, "totalitat")[0]) as r:
        g = comu.geometria(r); mc = comu.mapa_colors(r)
    ys, xs = np.where(mc == 1); oy, ox = int(ys.min()), int(xs.min())
    flat = fits.getdata(run.fase(0, "FLAT_RADIAL.fits")).astype(np.float32)
    dk = {}
    t_ini = min(v[1] for v in cronos.values())   # ⛔ el temps ha de ser RELATIU:
    t0 = time.time(); res = {}                   # C2 i C3 també ho són
    for n, (e, t_abs) in cronos.items():
        t = t_abs - t_ini
        if e not in dk:
            dk[e] = f0.dark_de(run, e)
        with rawpy.imread(comu.ruta_llum(run.tren, n)) as r:
            raw = r.raw_image.astype(np.float32)
        gp = ((raw - dk[e]) / flat)[oy::2, ox::2]
        R2 = r_lluna_nominal_px(cfg) / 2
        cy, cx = _centre_anell(gp)
        pts = _punts(gp, cy, cx, R2)
        if len(pts) >= 80:
            Cy0, Cx0, R0, _, _ = _cercle(pts, cy, cx)
            pts = _punts(gp, Cy0, Cx0, R0); cy, cx = Cy0, Cx0
        if len(pts) < 80:
            res[n] = {"ok": False, "n_punts": int(len(pts)), "exp": e, "t": t}
            continue
        Cy, Cx, R, nn, rms = _cercle(pts, cy, cx)
        res[n] = {"ok": True, "exp": e, "t": t,
                  "lluna_cy": oy + 2 * Cy, "lluna_cx": ox + 2 * Cx,
                  "R_px": 2 * R, "n_punts": nn, "rms_px": 2 * rms}
    bons = [v for v in res.values() if v.get("ok")]
    Rm = float(np.median([v["R_px"] for v in bons]))
    info = {"n_amb_limbe": len(bons), "n_total": len(res),
            "R_mediana_px": Rm,
            "rms_mediana_px": float(np.median([v["rms_px"] for v in bons])),
            "fotogrames": res}
    run.desa_rebut("F1.1_limbe.json", info)
    print(f"    {len(bons)}/{len(res)} amb limbe · R mediana {Rm:.2f} px "
          f"[{time.time()-t0:.0f}s]", flush=True)
    return info


# ------------------------------------------------------ 1.2 sol i llenç


def sol_i_llenc(run: comu.Run) -> dict:
    cfg = run.cfg
    cronos = cronologia(run)
    C = contactes_i_offsets(run, cronos)
    L = run.llegeix_rebut("F1.1_limbe.json")
    F = L["fotogrames"]; Rm = L["R_mediana_px"]

    # L'RMS DE L'AJUST TAMBE FILTRA. Amb n_punts i el radi sols, un ajust amb
    # 16 px d'rms hi entrava: a la Sony els fotogrames de 2 s tenen la corona
    # interior cremada, el que troba no es el limbe, i el centre en surt 128 px
    # fora amb un radi que encara cau dins del +-3 px. Dos d'aquests fabricaven
    # CINC apuntaments falsos on nomes n'hi ha un (research/115).
    rms_med = float(np.median([v["rms_px"] for v in F.values() if v.get("ok")]))
    rms_max = max(3.0, 4.0 * rms_med)
    bons = sorted(n for n, v in F.items()
                  if v.get("ok") and v["n_punts"] >= 400 and abs(v["R_px"] - Rm) <= 3.0
                  and v["rms_px"] <= rms_max)
    fora_rms = sorted(n for n, v in F.items()
                      if v.get("ok") and v["n_punts"] >= 400 and abs(v["R_px"] - Rm) <= 3.0
                      and v["rms_px"] > rms_max)
    if fora_rms:
        print(f"    fora per rms > {rms_max:.2f} px: " + ", ".join(fora_rms), flush=True)
    t = np.array([F[n]["t"] for n in bons])
    sx = np.array([F[n]["lluna_cx"] - C["offsets"][n]["dx"] for n in bons])
    sy = np.array([F[n]["lluna_cy"] - C["offsets"][n]["dy"] for n in bons])
    o = np.argsort(t); t, sx, sy = t[o], sx[o], sy[o]
    bons = [bons[i] for i in o]
    # SEGMENTS D'APUNTAMENT. Un sol polinomi en t suposa que la muntura no fa
    # salts. La Skywatcher de la Sony en va fer dos (+224 i -715 px, 749 px en
    # total, research/72 i 115): amb un sol ajust el model del Sol passa PEL MIG
    # dels dos apuntaments i no es a cap dels dos. Aqui es talla alla on el salt
    # entre fotogrames consecutius supera el llindar, i cada tros te el seu
    # model. Amb un sol apuntament (Vixen) surt UN segment i res no canvia.
    salt = np.hypot(np.diff(sx), np.diff(sy))
    talls = [0] + [i + 1 for i in np.nonzero(salt > SALT_APUNTAMENT_PX)[0]] + [len(t)]
    segs = [(a, b) for a, b in zip(talls[:-1], talls[1:]) if b - a >= 1]
    models, rx, ry = [], np.zeros_like(t), np.zeros_like(t)
    for a, b in segs:
        n = b - a
        gr = 2 if n >= 6 else (1 if n >= 3 else 0)
        pxs = np.polyfit(t[a:b], sx[a:b], gr) if n > gr else np.array([sx[a:b].mean()])
        pys = np.polyfit(t[a:b], sy[a:b], gr) if n > gr else np.array([sy[a:b].mean()])
        models.append({"t0": float(t[a]), "t1": float(t[b - 1]), "n": int(n),
                       "grau": int(gr), "px": pxs.tolist(), "py": pys.tolist()})
        rx[a:b] = sx[a:b] - np.polyval(pxs, t[a:b])
        ry[a:b] = sy[a:b] - np.polyval(pys, t[a:b])
    rms = float(np.sqrt(np.mean(rx ** 2 + ry ** 2)))
    if len(segs) > 1:
        print(f"    {len(segs)} APUNTAMENTS: " + " · ".join(
            f"{m['n']} fot. t {m['t0']:.0f}-{m['t1']:.0f}s (grau {m['grau']})"
            for m in models), flush=True)

    def model_de(tt):
        m = min(models, key=lambda q: 0.0 if q["t0"] <= tt <= q["t1"]
                else min(abs(tt - q["t0"]), abs(tt - q["t1"])))
        return float(np.polyval(m["px"], tt)), float(np.polyval(m["py"], tt))

    # coronal = DINS de la totalitat per efemèride, amb un segon de guarda
    sol = {}
    for n, v in sorted(F.items()):
        tt = v["t"]
        mx_, my_ = model_de(tt)
        sol[n] = {"t": tt, "exp": v["exp"], "sol_x": mx_, "sol_y": my_,
                  "font": "model", "coronal": (C["C2_t"] + 1.0) < tt < (C["C3_t"] - 1.0),
                  "lluna_dx": C["offsets"][n]["dx"], "lluna_dy": C["offsets"][n]["dy"]}

    with rawpy.imread(comu.entrades(run.tren, "totalitat")[0]) as r:
        g = comu.geometria(r)
    th = math.radians(-cfg["pa_north_deg"])
    Rm_ = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
    cant = []
    for s in sol.values():
        for (yy, xx) in ((0, 0), (0, g.ample), (g.alt, 0), (g.alt, g.ample)):
            cant.append(Rm_ @ np.array([xx - s["sol_x"], yy - s["sol_y"]]))
    cant = np.array(cant)
    hx = float(np.abs(cant[:, 0]).max()) + 16
    hy = float(np.abs(cant[:, 1]).max()) + 16
    esc_llenc = cfg["escala_arcsec_px"]
    if cfg.get("llenc_de"):
        # ⏭️ LLENÇ HERETAT: aquest tren entra a la graella comuna per poder fer
        #    de jutge de l'altre. `hx`/`hy` es conserven al rebut com a
        #    COBERTURA pròpia, que no és el mateix que la mida del llenç.
        L0 = comu.LLENC_COMU
        esc_llenc = L0["escala_arcsec_px"]
        W, H = L0["W"], L0["H"]
        cob = [hx * cfg["escala_arcsec_px"] / C["R_sol_arcsec"],
               hy * cfg["escala_arcsec_px"] / C["R_sol_arcsec"]]
    else:
        W = int(2 * math.ceil(hx / 8) * 8); H = int(2 * math.ceil(hy / 8) * 8)
        cob = None
    # ⛔ R_sol EN PÍXELS DEL LLENÇ, que amb escala heretada NO és el del sensor.
    #    (`contactes.R_lluna_px` es queda en píxels de SENSOR: la màscara lunar
    #    de f2 treballa al marc del sensor.)
    RS = C["R_sol_arcsec"] / esc_llenc

    info = {"contactes": {k: C[k] for k in ("C2_t", "C3_t", "totalitat_s",
                                            "R_lluna_arcsec", "R_sol_arcsec",
                                            "R_sol_px", "R_lluna_px")},
            "model_sol": {"segments": models, "n_segments": len(segs),
                          "salt_llindar_px": SALT_APUNTAMENT_PX,
                          "n_ajust": len(bons), "fora_per_rms": fora_rms,
                          "rms_limbe_max_acceptat_px": rms_max,
                          "rms_contra_quadratic_px": rms,
                          "nota": "NO és el residu de registre: és l'error de l'ajust "
                                  "del limbe. El registre fi el fa la correlació."},
            # ⛔ La deriva es mesura DINS de cada segment. Agafant el primer i
            #    l'ultim fotograma, un salt de muntura hi queda al mig i es
            #    mesura com si fos deriva: al Run 2 de la Sony donava
            #    22,83 ''/s quan la de veritat es 0,7 (research/115).
            "deriva_arcsec_s": float(np.median([
                math.hypot(sx[b - 1] - sx[a], sy[b - 1] - sy[a])
                * cfg["escala_arcsec_px"] / max(t[b - 1] - t[a], 1e-6)
                for a, b in segs if b - a >= 2] or [float("nan")])),
            "deriva_per_segment": [
                {"t0": float(t[a]), "t1": float(t[b - 1]), "n": int(b - a),
                 "deriva_arcsec_s": (float(math.hypot(sx[b-1]-sx[a], sy[b-1]-sy[a])
                                           * cfg["escala_arcsec_px"]
                                           / max(t[b-1]-t[a], 1e-6))
                                     if b - a >= 2 else None)}
                for a, b in segs],
            "llenc": {"W": W, "H": H, "orientacio": "NORD AMUNT",
                      "centre": "Sol per efemèride, simètric",
                      "semi_Rsol": [W / 2.0 / RS, H / 2.0 / RS],
                      "escala_arcsec_px": esc_llenc,
                      "escala_sensor_arcsec_px": cfg["escala_arcsec_px"],
                      "heretat_de": cfg.get("llenc_de"),
                      "cobertura_propia_Rsol": cob,
                      "pa_north_deg": cfg["pa_north_deg"], "R_sol_px": RS},
            "n_coronals": sum(1 for v in sol.values() if v["coronal"]),
            "fotogrames": sol}
    run.desa_rebut("F1.2_sol_llenc.json", info)
    print(f"    C2 {C['C2_t']:.2f}s · C3 {C['C3_t']:.2f}s · totalitat {C['totalitat_s']:.2f}s",
          flush=True)
    print(f"    deriva {info['deriva_arcsec_s']:.4f} ''/s · llenç {W}x{H} "
          f"(±{W/2.0/RS:.2f} x ±{H/2.0/RS:.2f} R☉) · cobertura del tren "
          + (f"±{cob[0]:.2f} x ±{cob[1]:.2f} R☉ · " if cob else "")
          + f"{info['n_coronals']} coronals", flush=True)
    return info
