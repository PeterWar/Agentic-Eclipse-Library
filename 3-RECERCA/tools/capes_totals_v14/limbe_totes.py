"""Ajusta el limbe lunar a TOTES les capes de la V13 i el compara amb el que la
cadena mesura al fotograma que les va originar. Decideix si la V13 esta
registrada o si cada capa seu a la posicio crua del seu fotograma."""
import json, math, os
import numpy as np, cv2
_src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "mesura_limbe_v13.py")).read()
exec(_src[_src.index("def gradmax"):_src.index("info = json.load")])

RUN = "/Users/USUARI/Desktop/Eclipse determinista/1-RUNS/017_VIXEN_CIENCIA_20260827T193426Z"
D = os.path.dirname(os.path.abspath(__file__))
F12 = json.load(open(f"{RUN}/4-rebuts/F1.2_sol_llenc.json"))
F11 = json.load(open(f"{RUN}/4-rebuts/F1.1_limbe.json"))
S = F12["fotogrames"]; RLL = F12["contactes"]["R_lluna_px"]
LM, TM, OFX, OFY = 172, 108, 457, 463
# fotogrames que la cadena diu de cada esglao (mateixa exposicio)
FONTS = {
 "12": ["572A2956.CR3"], "11": ["572A2968.CR3"], "10": ["572A2969.CR3"],
 "09": ["572A2975.CR3","572A2993.CR3"], "08": ["572A2970.CR3"], "07": ["572A2976.CR3"],
 "06": ["572A2971.CR3"], "05": ["572A2977.CR3"], "04": ["572A2972.CR3"],
 "03": ["572A2978.CR3"], "02": ["572A2979.CR3"], "01": ["572A2982.CR3"]}

info = json.load(open(f"{D}/v13/v13_info.json"))
out = {}
print(f"{'capa':>4} {'fotograma':>14} {'t':>7} | {'Lluna V13 (sensor)':>22} | "
      f"{'Lluna cadena (model)':>22} | {'dif':>14} | {'R':>7} {'rms':>5}")
for c in info["capes"]:
    capa = c["num"]
    r = np.load(f"{D}/v13/rgb_{capa}.npy")
    x0,y0,x1,y1 = c["bbox"]
    g = np.zeros((info["H"], info["W"]), np.float32)
    g[y0:y1, x0:x1] = r[...,1].astype(np.float32)/65535.0
    del r
    IX0,IY0,IX1,IY1 = 457,463,7417,5103
    sub = cv2.GaussianBlur(g[IY0:IY1, IX0:IX1], (0,0), 5)
    fosc = (sub < 0.02*max(float(sub.max()),1e-6)).astype(np.uint8)
    nlab, lab, stats, cents = cv2.connectedComponentsWithStats(fosc, 8)
    k = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA])) if nlab>1 else 0
    cx0 = float(cents[k][0])+IX0; cy0 = float(cents[k][1])+IY0
    del sub, fosc, lab
    gs = cv2.GaussianBlur(g, (0,0), 1.2)
    cy, cx, R = cy0, cx0, RLL; n, rms = 0, float("nan")
    for _ in range(3):
        pts = gradmax(gs, cy, cx, R)
        if len(pts) < 100: break
        cy, cx, R, n, rms = cercle(pts, cy, cx)
    del g, gs
    if n == 0:
        print(f"{capa:>4} SENSE LIMBE"); continue
    sx, sy = cx-OFX+LM, cy-OFY+TM
    fr = FONTS[capa][0]; v = S[fr]
    mx, my = v["sol_x"]+v["lluna_dx"], v["sol_y"]+v["lluna_dy"]
    out[capa] = {"fotograma": fr, "t": v["t"], "lluna_sensor_x": sx, "lluna_sensor_y": sy,
                 "model_x": mx, "model_y": my, "dx": sx-mx, "dy": sy-my,
                 "R_px": R, "rms_px": rms,
                 "sol_sensor_x": sx-v["lluna_dx"], "sol_sensor_y": sy-v["lluna_dy"]}
    print(f"{capa:>4} {fr.replace('.CR3',''):>14} {v['t']:7.2f} | ({sx:9.2f},{sy:9.2f}) | "
          f"({mx:9.2f},{my:9.2f}) | ({sx-mx:+6.2f},{sy-my:+6.2f}) | {R:7.2f} {rms:5.2f}")
json.dump(out, open(f"{D}/limbe_totes.json","w"), indent=1)
