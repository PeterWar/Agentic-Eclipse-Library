#!/usr/bin/env python3
"""V28 · llista dels ghosts de la Sony al LLENÇ COMÚ (per esborrar-los a l'origen, etapes 1 i 1b):
les sis marques grogues de Pere (V26, coordenades V23 de la geometria VELLA → llenç amb la seva inversa)
i el de 3 R☉ (research/116). Radi = 0,55·mida de la marca; veí de clonatge a 1,2·(radi+60) px en
direcció tangencial (mateix radi solar). Escriu cau_v25/ghosts_llenc.json."""
import os, json, numpy as np, cv2
AQUI = os.path.dirname(os.path.abspath(__file__)); CAU = os.path.join(AQUI, "cau_v25")
G_old = json.load(open(os.path.join(CAU, "geometria_v23.json"))); Minv = cv2.invertAffineTransform(np.array(G_old["M_llenc_a_v23"], np.float64))
W, H = 8096, 8960; cx, cy = W / 2 - 0.5, H / 2 - 0.5
out = [dict(x=2825, y=3988, radi=50, dx=52, dy=-130, bol=True, font="ghost Sony 3,0 R☉ (research/116)")]
for m in json.load(open(os.path.join(CAU, "marques_pere_artefactes.json"))):
    if m["color"] != "groc" or m["area"] <= 15000: continue
    q = Minv[:, :2] @ np.array([m["x"], m["y"]], np.float64) + Minv[:, 2]; x, y = int(round(q[0])), int(round(q[1])); radi = int(0.55 * max(m["w"], m["h"]))
    v = np.array([x - cx, y - cy]); t = np.array([-v[1], v[0]]) / max(np.hypot(*v), 1e-9); off = 1.2 * (radi + 60)
    for sgn in (1, -1):
        dx, dy = int(round(sgn * t[0] * off)), int(round(sgn * t[1] * off)); R = radi + 60
        if R <= x + dx < W - R and R <= y + dy < H - R and R <= x < W - R and R <= y < H - R: break
    else: print("fora del llenç:", x, y); continue
    out.append(dict(x=x, y=y, radi=radi, dx=dx, dy=dy, bol=False, font=f"marca groga de Pere (V26 {m['x']},{m['y']}) → llenç"))
json.dump(out, open(os.path.join(CAU, "ghosts_llenc.json"), "w"), indent=1); print(len(out), "ghosts al llenç:", [(g["x"], g["y"], g["radi"]) for g in out])
