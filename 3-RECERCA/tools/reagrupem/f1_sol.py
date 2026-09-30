#!/usr/bin/env python3
"""FASE 1 · pas 2 — centre del SOL per efemèride, i DECLARACIÓ DEL LLENÇ.

⛔ El centre absolut és el del **Sol per efemèride**, mai el limbe visible, que
és el de la LLUNA i llisca 28,5 px durant la totalitat (`research/99`).

    Sol(fotograma) = Lluna(mesurada al limbe) − (Lluna − Sol)(efemèride)

Els fotogrames sense limbe fiable (els 1/3200 de contacte) reben un **model de
punteria interpolat**, i queden marcats per anar a capes de contacte i NO al
sumatori coronal, tal com mana el contracte de fases.

El llenç es declara projectant els PERÍMETRES, mai amb números a mà, és
**simètric al voltant del Sol** perquè qualsevol retall centrat sigui un
enquadrament vàlid, i **nord amunt**.
"""

from __future__ import annotations

import datetime as dt
import json, math, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comu  # noqa: E402

LLOC = (42.299407, -5.02503, 798.0)     # MIRADOR FINAL 2
UTC_OFF_H = 2.0
DIA = (2026, 8, 12)
EFEM = "/Users/USUARI/Downloads/Eclipse 2026/de421.bsp"
ESCALA = 2.1494813525884373
PA_NORD = 57.194988546068025
PA_EST  = 325.5928710482988
RSOL_AS = 947.068
R_SOL_PX = RSOL_AS / ESCALA             # 440,60 px

# marge de seguretat del llenç del PROJECTE (perquè la Sony hi càpiga demà)
SONY_ESCALA = 3.2020
SONY_WH = (7952, 5304)
SONY_SALT_PX = 750.0


def base(pa_deg: float) -> np.ndarray:
    a = math.radians(pa_deg)
    return np.array([math.sin(a), -math.cos(a)])      # (x, y) amb y cap avall


def lluna_menys_sol(ts_locals: dict[str, float]) -> dict[str, np.ndarray]:
    from skyfield.api import load, wgs84
    eph = load(EFEM); tsc = load.timescale()
    lloc = eph["earth"] + wgs84.latlon(LLOC[0], LLOC[1], elevation_m=LLOC[2])
    n_, e_ = base(PA_NORD), base(PA_EST)
    out = {}
    for nom, t_local in ts_locals.items():
        utc = t_local - UTC_OFF_H * 3600.0
        h = int(utc // 3600); m = int((utc - 3600*h) // 60); s = utc - 3600*h - 60*m
        t = tsc.utc(DIA[0], DIA[1], DIA[2], h, m, s)
        obs = lloc.at(t)
        mra, mdec, _ = obs.observe(eph["moon"]).apparent().radec()
        sra, sdec, _ = obs.observe(eph["sun"]).apparent().radec()
        de = (mra.radians - sra.radians) * math.cos(sdec.radians) * 206264.806
        dn = (mdec.radians - sdec.radians) * 206264.806
        out[nom] = (de * e_ + dn * n_) / ESCALA        # px, (dx, dy)
    return out


def main() -> int:
    L = json.load(open(os.path.join(comu.REBUTS, "F1_limbe.json")))
    F = L["fotogrames"]
    import subprocess
    o = subprocess.run(["exiftool","-q","-n","-T","-FileName","-SubSecDateTimeOriginal",
                        comu.VIXEN], capture_output=True, text=True, timeout=900).stdout
    abs_t = {}
    for l in o.splitlines():
        p = l.split("\t")
        if len(p) >= 2 and p[0].upper().endswith(".CR3"):
            abs_t[p[0]] = (int(p[1][11:13])*3600 + int(p[1][14:16])*60
                           + float(p[1][17:].split("+")[0]))
    # instant MIG de l'exposició (l'EXIF de la R6 és l'INICI: amb final, els
    # fotogrames d'1 s i 2 s se solaparien 0,10 s, que és impossible)
    mig = {n: abs_t[n] + F[n]["exp"]/2.0 for n in F}
    dLS = lluna_menys_sol(mig)

    Rs = np.array([v["R_px"] for v in F.values() if v.get("ok")])
    Rmed = float(np.median(Rs))
    bons, dolents = [], []
    for n, v in F.items():
        if v.get("ok") and v["n_punts"] >= 400 and abs(v["R_px"] - Rmed) <= 3.0:
            bons.append(n)
        else:
            dolents.append(n)
    print(f"limbe fiable: {len(bons)}/{len(F)}   (R mediana {Rmed:.2f} px, "
          f"filtre n>=400 i |R-Rmed|<=3)")

    t = np.array([F[n]["t"] for n in bons])
    sx = np.array([F[n]["lluna_cx"] - dLS[n][0] for n in bons])
    sy = np.array([F[n]["lluna_cy"] - dLS[n][1] for n in bons])
    o_ = np.argsort(t); t, sx, sy = t[o_], sx[o_], sy[o_]

    # model de punteria: quadràtic en t (deriva de muntura + refracció)
    px_ = np.polyfit(t, sx, 2); py_ = np.polyfit(t, sy, 2)
    rx = sx - np.polyval(px_, t); ry = sy - np.polyval(py_, t)
    res = np.sqrt(rx**2 + ry**2)
    rms = float(np.sqrt(np.mean(rx**2 + ry**2)))
    print(f"\nSol (efemèride) — deriva ajustada amb un quadràtic:")
    print(f"  recorregut: {np.hypot(sx[-1]-sx[0], sy[-1]-sy[0]):.2f} px en {t[-1]-t[0]:.1f} s"
          f"  = {np.hypot(sx[-1]-sx[0], sy[-1]-sy[0])*ESCALA/(t[-1]-t[0]):.4f} ''/s")
    print(f"  la muntura NO és suau: separació del quadràtic rms {rms:.3f} px, "
          f"màx {res.max():.3f} px")
    print(f"  ⏭️ per això cada fotograma coronal fa servir la seva posició MESURADA,")
    print(f"     no el model; el model només serveix per als de contacte.")

    sol = {}
    for n in F:
        tt = F[n]["t"]
        if n in bons:                       # MESURAT, sense suavitzar
            X = F[n]["lluna_cx"] - dLS[n][0]; Y = F[n]["lluna_cy"] - dLS[n][1]
        else:                               # model de punteria interpolat
            X = float(np.polyval(px_, tt)); Y = float(np.polyval(py_, tt))
        sol[n] = {"t": tt, "exp": F[n]["exp"],
                  "sol_x": float(X), "sol_y": float(Y),
                  "font": "limbe" if n in bons else "model_interpolat",
                  "coronal": n in bons,
                  "lluna_dx": float(dLS[n][0]), "lluna_dy": float(dLS[n][1])}

    # ---------------- LLENÇ: unió de perímetres, nord amunt, simètric al Sol
    import rawpy
    with rawpy.imread(comu.llista(comu.VIXEN, ".CR3")[0]) as r:
        g = comu.geometria(r)
    th = math.radians(-PA_NORD)          # gir que porta el nord a amunt
    Rm = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
    cantons = []
    for n, s in sol.items():
        for (yy, xx) in ((0,0), (0,g.ample), (g.alt,0), (g.alt,g.ample)):
            v = np.array([xx - s["sol_x"], yy - s["sol_y"]])
            cantons.append(Rm @ v)
    cantons = np.array(cantons)
    hx = float(np.abs(cantons[:,0]).max()); hy = float(np.abs(cantons[:,1]).max())
    W = int(2*math.ceil(hx/8)*8); H = int(2*math.ceil(hy/8)*8)

    d_sony = math.hypot(*SONY_WH)/2 * (SONY_ESCALA/ESCALA) + SONY_SALT_PX*(SONY_ESCALA/ESCALA)
    W_proj = int(2*math.ceil(max(hx, d_sony)/8)*8); H_proj = int(2*math.ceil(max(hy, d_sony)/8)*8)

    llenc = {
        "escala_arcsec_px": ESCALA, "pa_north_deg_origen": PA_NORD,
        "orientacio": "NORD AMUNT (el llenç gira -PA_NORD respecte del sensor)",
        "centre": "SOL per EFEMERIDE, instant de referencia = mig de la totalitat",
        "vixen": {"W": W, "H": H, "semi_x": hx, "semi_y": hy,
                  "sol_xy": [W/2.0, H/2.0]},
        "projecte": {"W": W_proj, "H": H_proj,
                     "nota": "reserva perque la Sony (2 apuntaments, escala 3,2020, "
                             "girada 33,08 graus) hi capigui sense re-registrar res"},
        "R_sol_px": R_SOL_PX, "R_lluna_px": Rmed,
    }
    print(f"\nLLENÇ VIXEN (nord amunt, Sol al centre, simètric): "
          f"{W} x {H} px   =  ±{hx*ESCALA/RSOL_AS:.2f} x ±{hy*ESCALA/RSOL_AS:.2f} R☉")
    print(f"LLENÇ DEL PROJECTE (reserva per a la Sony):        {W_proj} x {H_proj} px")

    json.dump({"llenc": llenc,
               "muntura_no_suau_px": {"rms_contra_quadratic": rms,
                                      "max": float(res.max()),
                                      "nota": "NO és el residu de registre: els coronals "
                                              "usen la posició mesurada. És la mesura de "
                                              "les correccions manuals de la muntura."},
               "n_coronals": len(bons), "n_contacte": len(dolents),
               "model_sol": {"px": px_.tolist(), "py": py_.tolist()},
               "fotogrames": sol},
              open(os.path.join(comu.REBUTS, "F1_sol_llenc.json"), "w"), indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
