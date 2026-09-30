import numpy as np, glob, cv2, tifffile, sys, os
sys.path.insert(0,"/Users/USUARI/Downloads/Eclipse 2026/research/tools"); import hdr_corona_vixen as M
SCR="/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/8222da38-0c6f-46a7-867a-f0224834d74e/scratchpad"
capes=[np.load(f, allow_pickle=True) for f in sorted(glob.glob(f"{SCR}/capa_*.npz"))]
noms=[str(c["nom"]) for c in capes]
# compost aplanat de la pàgina 0, reduït ×4
with tifffile.TiffFile("/Users/USUARI/Downloads/UnintCapes3.tif") as t:
    comp=t.pages[0].asarray()
comp4=cv2.resize(comp.astype(np.float32)/65535.0,(comp.shape[1]//4,comp.shape[0]//4),interpolation=cv2.INTER_AREA); del comp
h,w,_=comp4.shape
# centre: el disc lunar fosc al compost → cerca el mínim de la luminància desenfocada... millor: limbe = màxim gradient radial des del centre de la imatge
G=comp4[...,1]
cy0,cx0=h/2,w/2
# refina el centre del disc: umbral fosc dins d'un radi de 200 px (a ×4, R_lluna≈115)
yy,xx=np.mgrid[0:h,0:w]
fosc=(G<0.05)&(np.hypot(xx-cx0,yy-cy0)<180)
cy=float(yy[fosc].mean()); cx=float(xx[fosc].mean())
r=np.hypot(xx-cx,yy-cy); R4=M.R_SOL_PX/4; rs=r/R4
print(f"centre del disc (×4): ({cx:.1f},{cy:.1f}); centre de la imatge ({cx0:.1f},{cy0:.1f}); R☉ a ×4 = {R4:.1f}")
ib=(rs*10).astype(int)   # anells de 0,1 R☉
def perfil(a, m=None):
    out=[]
    for k in range(10, 70):
        sel=(ib==k) if m is None else (ib==k)&m
        out.append(float(np.nanmean(a[sel])) if sel.sum()>30 else np.nan)
    return np.array(out)
rr=(np.arange(10,70)+0.5)/10
print("\n=== MÀSCARES: cobertura efectiva de cada capa per radi (mitjana de la màscara, 0–1) ===")
print(f"{'R☉':>5} " + " ".join(f"{n.split('_')[1][:7]:>7}" for n in noms))
mprof=[]
for c in capes:
    m=c["-2"] if "-2" in c.files else np.ones_like(G)
    mprof.append(perfil(m))
mprof=np.array(mprof)
for i,rv in enumerate(rr):
    if i%3==0: print(f"{rv:5.1f} " + " ".join(f"{mprof[k,i]:7.2f}" for k in range(len(capes))))
# qui "guanya" a cada radi: composició Normal de dalt a baix amb la màscara com a opacitat
print("\n=== PES EFECTIU de cada capa al compost (dalt a baix, Normal) ===")
pes=np.zeros((len(capes),len(rr))); resta=np.ones(len(rr))
vis=[bool(c["visible"]) for c in capes]
for k in range(len(capes)-1,-1,-1):
    if not vis[k]: continue
    a=np.nan_to_num(mprof[k]); pes[k]=resta*a; resta=resta*(1-a)
print(f"{'R☉':>5} " + " ".join(f"{n.split('_')[1][:7]:>7}" for n in noms) + "   (resta)")
for i,rv in enumerate(rr):
    if i%3==0: print(f"{rv:5.1f} " + " ".join(f"{pes[k,i]:7.2f}" for k in range(len(capes))) + f"   {resta[i]:.2f}")
np.savez(f"{SCR}/analisi_capes.npz", comp4=comp4, cx=cx, cy=cy, mprof=mprof, pes=pes, rr=rr)
