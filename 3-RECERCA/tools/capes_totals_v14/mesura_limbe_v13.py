"""Ajusta el limbe LUNAR a les capes de la V13 que son d'UN SOL fotograma.

⛔ Maxim de gradient, no llindar: les capes de la V13 estan tonificades i un
llindar de mig nivell es mou amb la corba; el maxim de gradient d'una vora
simetrica, no.

Amb el limbe mesurat i el vector Lluna-Sol que la cadena ja te per a aquell
fotograma, en surt la posicio del SOL al llenc de la V13. Tres capes = tres
mesures independents de la mateixa cosa: si coincideixen, la hipotesi del
transformat es certa.
"""
import json, math, os
import numpy as np
import cv2

RUN = "/Users/USUARI/Desktop/Eclipse determinista/1-RUNS/017_VIXEN_CIENCIA_20260827T193426Z"
D = os.path.dirname(os.path.abspath(__file__))
F12 = json.load(open(f"{RUN}/4-rebuts/F1.2_sol_llenc.json"))
S = F12["fotogrames"]; CT = F12["contactes"]
RLL = CT["R_lluna_px"]
LM, TM, OFX, OFY = 172, 108, 457, 463

# quina capa V13 -> quin fotograma (llegit del nom de la capa)
UNIC = {"12": "572A2956.CR3", "11": "572A2968.CR3", "10": "572A2969.CR3"}

def gradmax(g, cy, cx, R, naz=720, banda=0.06):
    az = np.linspace(0, 2*np.pi, naz, endpoint=False)
    rs = np.arange(R*(1-banda), R*(1+banda), 0.25)
    ys = cy + rs[None,:]*np.cos(az)[:,None]
    xs = cx + rs[None,:]*np.sin(az)[:,None]
    ok = (ys>1)&(ys<g.shape[0]-2)&(xs>1)&(xs<g.shape[1]-2)
    prof = np.where(ok, cv2.remap(g, xs.astype(np.float32), ys.astype(np.float32),
                                  cv2.INTER_LINEAR, borderValue=np.nan), np.nan)
    # suavitzat radial lleu i derivada
    k = np.array([0.25,0.5,0.25])
    pr = np.apply_along_axis(lambda v: np.convolve(v, k, "same"), 1, prof)
    d = np.gradient(pr, axis=1)
    pts = []
    for i in range(naz):
        v = d[i]
        if not np.isfinite(v).all():
            continue
        j = int(np.nanargmax(v))
        if j <= 0 or j >= len(rs)-1:
            continue
        a_, b_, c_ = v[j-1], v[j], v[j+1]
        den = (a_ - 2*b_ + c_)
        dj = 0.5*(a_ - c_)/den if abs(den) > 1e-12 else 0.0
        if abs(dj) > 1: dj = 0.0
        pts.append((rs[j] + dj*0.25, az[i]))
    return np.array(pts)

def cercle(pts, cy, cx):
    r, a = pts[:,0], pts[:,1]
    y = cy + r*np.cos(a); x = cx + r*np.sin(a)
    for _ in range(8):
        A = np.c_[x, y, np.ones_like(x)]
        sol,*_ = np.linalg.lstsq(A, x**2 + y**2, rcond=None)
        Cx, Cy = sol[0]/2, sol[1]/2
        R = math.sqrt(sol[2] + Cx**2 + Cy**2)
        dd = np.hypot(x-Cx, y-Cy) - R
        s = 1.4826*np.median(np.abs(dd - np.median(dd)))
        bo = np.abs(dd - np.median(dd)) < 2.5*max(s, 0.05)
        if bo.sum() < 100: break
        x, y = x[bo], y[bo]
    return float(Cy), float(Cx), float(R), int(len(x)), float(np.std(np.hypot(x-Cx,y-Cy)-R))

info = json.load(open(f"{D}/v13/v13_info.json"))
res = {}
for capa, frame in UNIC.items():
    c = [x for x in info["capes"] if x["num"] == capa][0]
    r = np.load(f"{D}/v13/rgb_{capa}.npy")
    x0, y0, x1, y1 = c["bbox"]
    g = np.zeros((info["H"], info["W"]), np.float32)
    g[y0:y1, x0:x1] = r[..., 1].astype(np.float32)/65535.0
    del r
    # ⛔ punt de partida INDEPENDENT de la hipotesi: el disc lunar es la taca
    #    fosca mes gran DINS de la zona amb imatge (fora hi ha marge BLANC, que
    #    es menjava qualsevol estimador per percentil).
    IX0, IY0, IX1, IY1 = 457, 463, 7417, 5103
    sub = cv2.GaussianBlur(g[IY0:IY1, IX0:IX1], (0,0), 5)
    fosc = (sub < 0.02*max(float(sub.max()), 1e-6)).astype(np.uint8)
    nlab, lab, stats, cents = cv2.connectedComponentsWithStats(fosc, 8)
    k = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA])) if nlab > 1 else 0
    cx0 = float(cents[k][0]) + IX0; cy0 = float(cents[k][1]) + IY0
    area = float(stats[k, cv2.CC_STAT_AREA])
    print(f"  capa {capa}: taca fosca centre=({cx0:.1f},{cy0:.1f}) area={area:.0f} "
          f"-> R equivalent {math.sqrt(area/math.pi):.1f} px")
    del sub, fosc, lab
    gs = cv2.GaussianBlur(g, (0,0), 1.2)
    cy, cx, R = cy0, cx0, RLL
    n, rms, npts = 0, float("nan"), 0
    for _ in range(3):
        pts = gradmax(gs, cy, cx, R)
        npts = len(pts)
        if npts < 100:
            break
        cy, cx, R, n, rms = cercle(pts, cy, cx)
    if n == 0:
        print(f"capa {capa}: NO s'hi pot ajustar el limbe ({npts} punts) — se salta")
        del g, gs
        continue
    v = S[frame]
    solx13 = cx - v["lluna_dx"]; soly13 = cy - v["lluna_dy"]
    res[capa] = {"frame": frame, "t": v["t"], "lluna_cx13": cx, "lluna_cy13": cy,
                 "R_px": R, "n": n, "rms_px": rms,
                 "sol_x13": solx13, "sol_y13": soly13,
                 "sol_x_sensor": solx13 - OFX + LM, "sol_y_sensor": soly13 - OFY + TM}
    print(f"capa {capa} ({frame}, t={v['t']:6.2f}s): Lluna=({cx:8.2f},{cy:8.2f}) "
          f"R={R:7.2f} (cadena {RLL:.2f}) n={n} rms={rms:.2f}  ->  "
          f"Sol13=({solx13:8.2f},{soly13:8.2f}) sensor=({solx13-OFX+LM:8.2f},{soly13-OFY+TM:8.2f})")
    del g, gs
json.dump(res, open(f"{D}/limbe_v13.json","w"), indent=1)
