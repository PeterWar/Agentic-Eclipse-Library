"""Fins on crema Brno, quin color deixa al limbe, i la Lluna."""
import json, os
import numpy as np
from geometria import CARPETA, carrega, retalla_marc, srgb_a_lineal
AQUI = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(AQUI, "perfils.json")))
ordre = ["TSE2026_Trigaza_800mm.png", "TSE_2026_530mm_DHS.png",
         "TSE_2026_400mm_DHS.png", "TSE_2026_200mm_DHS.png"]

print("=== A. FINS ON CREMA (nivell >= 0,99) i QUE ES el que crema ===")
for nom in ordre:
    rgb = carrega(nom); f0,f1,c0,c1 = retalla_marc(rgb); sub = rgb[f0:f1,c0:c1]
    lum = sub.mean(axis=2); g = P[nom]
    yy,xx = np.mgrid[0:lum.shape[0],0:lum.shape[1]]
    r = np.hypot(yy-g["centre"][1], xx-g["centre"][0]) / g["Rsol_px"]
    m = (lum >= 0.99) & (r > 1.00)
    if m.sum():
        rq = r[m]
        # de quin color es el que crema
        col = sub[m].mean(axis=0)
        print(f"  {nom:30s} {m.sum():5d} px  r de {rq.min():.3f} a {rq.max():.3f} R_sol "
              f"(p99 {np.percentile(rq,99):.3f})  color mitja R{col[0]:.2f} G{col[1]:.2f} B{col[2]:.2f}")

print()
print("=== B. EL LIMBE: unic lloc amb color de veritat (cromosfera/protuberancia) ===")
for nom in ordre:
    rgb = carrega(nom); f0,f1,c0,c1 = retalla_marc(rgb); sub = rgb[f0:f1,c0:c1]
    lin = srgb_a_lineal(sub); g = P[nom]
    yy,xx = np.mgrid[0:sub.shape[0],0:sub.shape[1]]
    r = np.hypot(yy-g["centre"][1], xx-g["centre"][0]) / g["Rsol_px"]
    anell = (r > 1.030) & (r < 1.075)
    v = lin[anell]
    rg = v[:,0]/np.maximum(v[:,1],1e-6)
    q = np.percentile(rg, [50, 95, 99.5])
    vermells = anell & (lin[:,:,0]/np.maximum(lin[:,:,1],1e-6) > 1.5)
    print(f"  {nom:30s} anell 1,03-1,075: R/G mediana {q[0]:.2f}  p95 {q[1]:.2f}  p99,5 {q[2]:.2f}"
          f"   px amb R/G>1,5: {vermells.sum():5d} ({vermells.sum()/anell.sum()*100:.2f} %)")

print()
print("=== C. LA LLUNA: earthshine si o no, i quin nivell ===")
for nom in ordre:
    rgb = carrega(nom); f0,f1,c0,c1 = retalla_marc(rgb); sub = rgb[f0:f1,c0:c1]
    lum = sub.mean(axis=2); g = P[nom]
    yy,xx = np.mgrid[0:lum.shape[0],0:lum.shape[1]]
    r = np.hypot(yy-g["centre"][1], xx-g["centre"][0]) / g["Rsol_px"]
    dins = r < 0.90
    v = lum[dins]
    cel = np.array([x["nivell_sRGB"] for x in P[nom]["files"] if x["cobertura"]>0.999])[-3:].mean()
    print(f"  {nom:30s} disc: mediana {np.median(v):.4f}  p5-p95 {np.percentile(v,5):.4f}-{np.percentile(v,95):.4f}"
          f"  contrast intern {np.percentile(v,95)-np.percentile(v,5):.4f}   (cel {cel:.3f})")

print()
print("=== D. LA LLUNA DEL 800 mm: cercle o interseccio de dos cercles? ===")
for nom in ordre:
    rgb = carrega(nom); f0,f1,c0,c1 = retalla_marc(rgb); sub = rgb[f0:f1,c0:c1]
    lum = sub.mean(axis=2); g = P[nom]; cy,cx = g["centre"][1], g["centre"][0]
    ny,nx = lum.shape
    th = np.linspace(0,2*np.pi,720,endpoint=False)
    rs = np.arange(0.5*g["Rsol_px"], 1.5*g["Rsol_px"], 0.25)
    rad=[]
    for t in th:
        yy = np.clip((cy+rs*np.sin(t)).astype(int),0,ny-1); xx=np.clip((cx+rs*np.cos(t)).astype(int),0,nx-1)
        v = lum[yy,xx]; kp=int(np.argmax(v)); gg=np.gradient(v)
        rad.append(rs[int(np.argmax(gg[:max(kp,3)]))]/g["Rsol_px"])
    rad=np.asarray(rad)
    print(f"  {nom:30s} R/R_sol mediana {np.median(rad):.4f}  min {rad.min():.4f} max {rad.max():.4f}"
          f"  amplitud {rad.max()-rad.min():.4f} ({(rad.max()-rad.min())/np.median(rad)*100:.1f} %)")
