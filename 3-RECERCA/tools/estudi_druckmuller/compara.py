"""Posa Brno, la maqueta de Pere i el nostre lliurament al MATEIX eix."""
import json, os
import numpy as np
from geometria import CARPETA, carrega, retalla_marc
from mesura import b_de_r, R108

AQUI = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(AQUI, "perfils.json")))

# research/108 §3: nivell mostrat (0-1) al mateix eclipsi
R_REF = np.array([1.09, 1.62, 2.15, 2.68, 3.74, 5.33, 8.51])
MAQUETA = np.array([0.631, 0.510, 0.404, 0.297, 0.212, 0.175, 0.133])
V13 = np.array([0.518, 0.689, 0.719, 0.640, 0.484, 0.429, np.nan])
NOSTRE = np.array([0.998, 0.561, 0.263, 0.160, 0.092, 0.061, 0.041])

print("=" * 78)
print("1. SATURACIO: quant crema cadascu")
print("=" * 78)
for nom in sorted(P):
    rgb = carrega(nom); f0, f1, c0, c1 = retalla_marc(rgb)
    sub = rgb[f0:f1, c0:c1]; lum = sub.mean(axis=2)
    g = P[nom]
    yy, xx = np.mgrid[0:lum.shape[0], 0:lum.shape[1]]
    r = np.hypot(yy - g["centre"][1], xx - g["centre"][0]) / g["Rsol_px"]
    fora = r > 1.05
    print(f"  {nom:32s} max {lum[fora].max():.4f}  "
          f">=0,99: {(lum[fora] >= 0.99).sum():6d} px ({(lum[fora]>=0.99).mean()*100:.4f} %)  "
          f"canal a 255: {(sub[fora].max(axis=-1) >= 254.5/255).sum():6d} px")
print(f"  {'NOSTRE lliurament 26-08':32s} 329.659 px a >=0,999 fins a 1,45 R_sol (research/108)")

print()
print("=" * 78)
print("2. CORBA DE TO: pendent de nivell mostrat per decada de B/B_sol, 1,1-3,0 R_sol")
print("=" * 78)


def pendent(rs, ns):
    ok = np.isfinite(ns) & (rs >= 1.10) & (rs <= 3.00)
    x = np.log10(b_de_r(rs[ok])); y = ns[ok]
    A = np.polyfit(x, y, 1)
    rr = np.corrcoef(x, y)[0, 1]
    return A[0], rr, ok.sum()


for nom in sorted(P):
    f = [x for x in P[nom]["files"] if x["cobertura"] > 0.999]
    rs = np.array([x["r"] for x in f]); ns = np.array([x["nivell_sRGB"] for x in f])
    p, rr, n = pendent(rs, ns)
    print(f"  {nom:32s} {p:7.3f} /decada   r={rr:6.3f}  ({n} anells)")
for lbl, v in [("maqueta de Pere", MAQUETA), ("V13_Pere", V13), ("NOSTRE lliurament 26-08", NOSTRE)]:
    p, rr, n = pendent(R_REF, v)
    print(f"  {lbl:32s} {p:7.3f} /decada   r={rr:6.3f}  ({n} anells)")

print()
print("=" * 78)
print("3. NIVELL MOSTRAT ALS RADIS DE LA TAULA DEL research/108")
print("=" * 78)
hdr = f"{'r':>5} {'800mm':>7} {'530mm':>7} {'400mm':>7} {'200mm':>7} | {'maqueta':>8} {'V13':>6} {'nostre':>7}"
print(hdr); print("-" * len(hdr))
ordre = ["TSE2026_Trigaza_800mm.png", "TSE_2026_530mm_DHS.png",
         "TSE_2026_400mm_DHS.png", "TSE_2026_200mm_DHS.png"]
for i, rr in enumerate(R_REF):
    cel = []
    for nom in ordre:
        f = [x for x in P[nom]["files"] if x["cobertura"] > 0.999]
        R = np.array([x["r"] for x in f]); N = np.array([x["nivell_sRGB"] for x in f])
        cel.append(np.interp(rr, R, N, left=np.nan, right=np.nan))
    s = " ".join(f"{c:7.3f}" if np.isfinite(c) else "      -" for c in cel)
    print(f"{rr:5.2f} {s} | {MAQUETA[i]:8.3f} {V13[i]:6.3f} {NOSTRE[i]:7.3f}")

print()
print("=" * 78)
print("4. EL CEL: on s'atura el nivell, i de quin color es")
print("=" * 78)
for nom in ordre:
    f = [x for x in P[nom]["files"] if x["cobertura"] > 0.999]
    N = np.array([x["nivell_sRGB"] for x in f]); R = np.array([x["r"] for x in f])
    t = np.array([x["tot"] for x in f])
    cel_n = N[-3:].mean(); pic = N.max()
    print(f"  {nom:32s} pic {pic:.3f} a {R[np.argmax(N)]:.2f} R_sol -> "
          f"cel {cel_n:.3f} a {R[-1]:.1f} R_sol   |  recorregut {pic-cel_n:.3f} "
          f"| color del cel R/G {t[-1][0]/t[-1][1]:.3f}  B/G {t[-1][2]/t[-1][1]:.3f}")

print()
print("=" * 78)
print("5. COLOR DE L'ESTRUCTURA CORONAL (el cel s'hi cancel.la), nomes anells sencers")
print("=" * 78)
for nom in ordre:
    f = [x for x in P[nom]["files"] if x["cobertura"] > 0.999 and x["r"] < 5.0]
    e = np.array([x["est"] for x in f])
    rg = e[:, 0] / e[:, 1]; bg = e[:, 2] / e[:, 1]
    ok = np.isfinite(rg) & np.isfinite(bg)
    print(f"  {nom:32s} R/G {np.median(rg[ok]):.3f} (p10-p90 {np.percentile(rg[ok],10):.3f}-{np.percentile(rg[ok],90):.3f})"
          f"   B/G {np.median(bg[ok]):.3f} ({np.percentile(bg[ok],10):.3f}-{np.percentile(bg[ok],90):.3f})")
