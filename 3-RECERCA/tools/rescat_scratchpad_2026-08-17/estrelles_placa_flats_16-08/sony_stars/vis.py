import numpy as np, pickle
IA=np.load("IMGA.npy"); IC=np.load("IMGC.npy")
d=np.load("secure.npz",allow_pickle=True)
xa,ya,xc,yc=d['xa'],d['ya'],d['xc'],d['yc']
ok=np.load("FINAL_idx.npy"); FT=d['FT']; rs=d['rs']
o=ok[np.argsort(-FT[ok])]
def show(IM,x,y,lab,H=8):
    X0,Y0=int(round(x)),int(round(y)); st=IM[Y0-H:Y0+H+1,X0-H:X0+H+1]
    print(f"  {lab}")
    for i in range(st.shape[0]): print("   "+"".join(f"{st[i,j]:6.0f}" for j in range(st.shape[1])))
for lab,i in [("S05 R=2.68 Rsun",o[4]),("S09 R=2.52 Rsun",o[8]),("S33 faint, R=6.06",o[32])]:
    print(f"=== {lab}  flux={FT[i]:.0f} ADU/s ===")
    show(IA,xa[i],ya[i],"group A stack (11 s)")
    show(IC,xc[i],yc[i],"group C stack (13 s)")
    print()
