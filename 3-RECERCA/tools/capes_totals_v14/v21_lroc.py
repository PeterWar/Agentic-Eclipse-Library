"""V21 · orientació lunar per efemèride i mapa LROC de la NASA al marc del llenç.

⛔ Res d'ajustar l'orientació: es PREDIU.
  · l'orientació del cel al llenç surt de les estrelles del catàleg (el
    plate-solve com a comprovació: on és el nord i on és l'est, mesurat);
  · la libració i l'angle de posició del pol lunar surten de l'efemèride
    (de421 + model de rotació IAU/WGCCRE 2009 amb els 13 termes E);
  · el mapa és `ref_LROC_WAC_color_poles_4k_NASA_SVS4720.tif` (NASA SVS 4720).
"""
from __future__ import annotations
import json, math, os, sys
import numpy as np
from scipy.ndimage import map_coordinates

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v21")
LROC_TIF = ("/Users/USUARI/Desktop/Eclipse 2026/Derivats/Earthshine/Historic/"
            "Earthshine_Claude_Sony/ref_LROC_WAC_color_poles_4k_NASA_SVS4720.tif")
BSP = "/Users/USUARI/Downloads/Eclipse 2026/de421.bsp"
LLOC = (42.299407, -5.02503, 798.0)          # MIRADOR FINAL 2
INSTANT = "2026-08-12T18:29:40Z"


def rotz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])


def rotx(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1.0, 0, 0], [0, c, -s], [0, s, c]])


def iau_lluna(d):
    """α0, δ0, W (graus) del model IAU/WGCCRE 2009 per a la Lluna."""
    T = d / 36525.0
    E = [0.0] * 14
    E[1] = 125.045 - 0.0529921 * d;  E[2] = 250.089 - 0.1059842 * d
    E[3] = 260.008 + 13.0120009 * d; E[4] = 176.625 + 13.3407154 * d
    E[5] = 357.529 + 0.9856003 * d;  E[6] = 311.589 + 26.4057084 * d
    E[7] = 134.963 + 13.0649930 * d; E[8] = 276.617 + 0.3287146 * d
    E[9] = 34.226 + 1.7484877 * d;   E[10] = 15.134 - 0.1589763 * d
    E[11] = 119.743 + 0.0036096 * d; E[12] = 239.961 + 0.1643573 * d
    E[13] = 25.053 + 12.9590088 * d
    s = [math.sin(math.radians(x)) for x in E]
    c = [math.cos(math.radians(x)) for x in E]
    a0 = (269.9949 + 0.0031 * T - 3.8787 * s[1] - 0.1204 * s[2] + 0.0700 * s[3]
          - 0.0172 * s[4] + 0.0072 * s[6] - 0.0052 * s[10] + 0.0043 * s[13])
    d0 = (66.5392 + 0.0130 * T + 1.5419 * c[1] + 0.0239 * c[2] - 0.0278 * c[3]
          + 0.0068 * c[4] - 0.0029 * c[6] + 0.0009 * c[7] + 0.0008 * c[10]
          - 0.0009 * c[13])
    W = (38.3213 + 13.17635815 * d - 1.4e-12 * d * d + 3.5610 * s[1]
         + 0.1208 * s[2] - 0.0642 * s[3] + 0.0158 * s[4] + 0.0252 * s[5]
         - 0.0066 * s[6] - 0.0047 * s[7] - 0.0046 * s[8] + 0.0028 * s[9]
         + 0.0052 * s[10] + 0.0040 * s[11] + 0.0019 * s[12] - 0.0044 * s[13])
    return a0, d0, W % 360.0


def geometria_lunar():
    from skyfield.api import load, wgs84
    from skyfield.framelib import ICRS
    ts = load.timescale()
    t = ts.utc(2026, 8, 12, 18, 29, 40)
    eph = load(BSP)
    terra, lluna = eph["earth"], eph["moon"]
    obs = terra + wgs84.latlon(LLOC[0], LLOC[1], elevation_m=LLOC[2])
    ap = obs.at(t).observe(lluna).apparent()
    u = ap.position.km / np.linalg.norm(ap.position.km)      # observador → Lluna
    d = t.tdb - 2451545.0
    a0, d0, W = iau_lluna(d)
    ra0, de0 = math.radians(a0), math.radians(d0)
    p = np.array([math.cos(de0) * math.cos(ra0), math.cos(de0) * math.sin(ra0),
                  math.sin(de0)])                             # pol lunar (ICRF)
    Rb2i = rotz(ra0 + math.pi / 2) @ rotx(math.pi / 2 - de0) @ rotz(math.radians(W))
    Ri2b = Rb2i.T
    s = Ri2b @ (-u)                                           # punt sub-observador
    lat = math.degrees(math.asin(np.clip(s[2], -1, 1)))
    lon = math.degrees(math.atan2(s[1], s[0]))
    z = np.array([0, 0, 1.0])
    e = np.cross(z, u); e /= np.linalg.norm(e)                # est
    n = np.cross(u, e)                                        # nord
    pa = math.degrees(math.atan2(float(p @ e), float(p @ n))) # PA del pol lunar
    return {"libracio_lon": lon, "libracio_lat": lat, "pa_pol_lunar": pa,
            "alfa0": a0, "delta0": d0, "W": W, "instant": INSTANT,
            "distancia_km": float(np.linalg.norm(ap.position.km)),
            "u": u.tolist(), "e": e.tolist(), "n": n.tolist(),
            "pol_icrf": p.tolist(), "Ri2b": Ri2b.tolist()}


def orientacio_del_llenc():
    """Nord i est celestes en píxels del llenç, MESURATS amb les estrelles."""
    import pandas as pd
    est = json.load(open(os.path.join(CAU, "estrelles_purga.json")))
    cat = pd.read_csv("/Users/USUARI/Desktop/Eclipse 2026/Derivats/Astrometria/"
                      "Estrelles/Work_2026-08-17/xmatch/cat2_sony.csv")
    idx = {}
    for i, r in cat.iterrows():
        if not pd.isna(r.get("HIP_n")):
            idx[("HIP", int(r["HIP_n"]))] = i
        idx[("TYC", str(r.get("TYC", "")))] = i
    X, Y, XI, ET = [], [], [], []
    for z in est:
        k = ("HIP", z["HIP"]) if z["HIP"] else ("TYC", z["TYC"])
        if k not in idx:
            continue
        r = cat.iloc[idx[k]]
        X.append(z["x"]); Y.append(z["y"])
        XI.append(float(r["xi_as"])); ET.append(float(r["eta_as"]))
    X, Y, XI, ET = map(np.array, (X, Y, XI, ET))
    A = np.column_stack([np.ones_like(XI), XI, ET])
    cx = np.linalg.lstsq(A, X, rcond=None)[0]
    cy = np.linalg.lstsq(A, Y, rcond=None)[0]
    rms = float(np.sqrt(((X - A @ cx) ** 2 + (Y - A @ cy) ** 2).mean()))
    Ev = np.array([cx[1], cy[1]]); Nv = np.array([cx[2], cy[2]])
    esc = (np.linalg.norm(Ev) + np.linalg.norm(Nv)) / 2.0     # px per arcsec
    return {"n_estrelles": len(X), "rms_px": rms,
            "est_px_per_as": Ev.tolist(), "nord_px_per_as": Nv.tolist(),
            "escala_as_px": float(1.0 / esc),
            "angle_nord_deg": float(math.degrees(math.atan2(Nv[1], Nv[0]))),
            "angle_est_deg": float(math.degrees(math.atan2(Ev[1], Ev[0]))),
            "mirall": bool(Ev[0] * Nv[1] - Ev[1] * Nv[0] < 0)}


def mapa_gris():
    cam = os.path.join(CAU, "lroc_4k_gray.npy")
    if os.path.exists(cam):
        return np.load(cam)
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    A = np.asarray(Image.open(LROC_TIF), np.float32)
    if A.ndim == 3:
        A = A[..., :3] @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    np.save(cam, A)
    return A


def renderitza(M, geo, ori, forma, centre, RL, gir_deg=0.0):
    """El mapa LROC projectat ortogràficament al marc del llenç."""
    H, W = forma
    Ev = np.array(ori["est_px_per_as"]); Nv = np.array(ori["nord_px_per_as"])
    Eu = Ev / np.linalg.norm(Ev); Nu = Nv / np.linalg.norm(Nv)
    if gir_deg:
        a = math.radians(gir_deg); ca, sa = math.cos(a), math.sin(a)
        Eu, Nu = ca * Eu + sa * Nu, -sa * Eu + ca * Nu
    yy, xx = np.mgrid[0:H, 0:W]
    dx = (xx - centre[0]).astype(np.float64); dy = (yy - centre[1]).astype(np.float64)
    # components est/nord del desplaçament, en radis lunars
    det = Eu[0] * Nu[1] - Eu[1] * Nu[0]
    ee = (dx * Nu[1] - dy * Nu[0]) / det / RL
    nn = (-dx * Eu[1] + dy * Eu[0]) / det / RL
    q = ee * ee + nn * nn
    disc = q < 1.0
    w = np.sqrt(np.clip(1.0 - q, 0, None))
    e3 = np.array(geo["e"]); n3 = np.array(geo["n"]); u3 = np.array(geo["u"])
    P = (ee[..., None] * e3 + nn[..., None] * n3 - w[..., None] * u3)
    Ri2b = np.array(geo["Ri2b"])
    B = P @ Ri2b.T
    lat = np.degrees(np.arcsin(np.clip(B[..., 2], -1, 1)))
    lon = np.degrees(np.arctan2(B[..., 1], B[..., 0]))
    MH, MW = M.shape
    xm = (lon + 180.0) / 360.0 * MW
    ym = (90.0 - lat) / 180.0 * MH
    g = map_coordinates(M, [ym.ravel(), xm.ravel()], order=1, mode="wrap"
                        ).reshape(H, W).astype(np.float32)
    g[~disc] = 0
    return g, disc


if __name__ == "__main__":
    geo = geometria_lunar()
    ori = orientacio_del_llenc()
    print("EFEMÈRIDE (de421 + IAU 2009):")
    print(f"  libració sub-observador: lon {geo['libracio_lon']:+.3f}° · "
          f"lat {geo['libracio_lat']:+.3f}°")
    print(f"  angle de posició del pol lunar: {geo['pa_pol_lunar']:+.3f}° "
          f"(des del nord celeste cap a l'est)")
    print(f"  distància {geo['distancia_km']:.0f} km · α0={geo['alfa0']:.4f}° "
          f"δ0={geo['delta0']:.4f}° W={geo['W']:.4f}°")
    print("\nORIENTACIÓ DEL LLENÇ (mesurada amb les estrelles del catàleg):")
    print(f"  {ori['n_estrelles']} estrelles · rms {ori['rms_px']:.2f} px · "
          f"escala {ori['escala_as_px']:.4f}″/px")
    print(f"  nord celeste a {ori['angle_nord_deg']:+.3f}° · "
          f"est a {ori['angle_est_deg']:+.3f}° (angles de la imatge, y avall)")
    json.dump({"efemeride": geo, "orientacio": ori},
              open(os.path.join(CAU, "lroc_geo.json"), "w"), indent=1)
    M = mapa_gris()
    print(f"\nmapa LROC: {M.shape} · {LROC_TIF.split('/')[-1]}")
