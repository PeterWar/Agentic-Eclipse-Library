import rawpy, numpy as np, pickle
from scipy import ndimage
D="/Users/USUARI/Desktop/Eclipse 2026/300mm/"; AS=3.234; GAIN=3.323
d=np.load("secure.npz",allow_pickle=True)
xc,yc,rs,FT=d['xc'],d['yc'],d['rs'],d['FT']; idx=d['idx']
xa,ya=d['xa'],d['ya']
OFF=pickle.load(open("offsets6.pkl","rb"))['off']
out=idx[rs[idx]>4.0]; bright=out[np.argsort(-FT[out])][:6]
FR=[('DSC06987',8.,'A'),('DSC06993',8.,'C'),('DSC06996',2.,'C'),('DSC06999',2.,'C'),('DSC06984',2.,'A')]
H=150
edges=np.array([0,1,1.5,2,2.5,3,4,5,6.5,8,10,13,17,22,28,36,46,58,74,95,120,150],float)
rc=.5*(edges[:-1]+edges[1:])
acc=np.zeros((len(bright),len(edges)-1)); acw=np.zeros_like(acc); pk=np.zeros(len(bright))
for n,e,g in FR:
    md=np.load(f"masterdark_{int(e)}s.npy")
    with rawpy.imread(D+n+".ARW") as r:
        raw=r.raw_image_visible.astype(np.float32); col=r.raw_colors_visible
    gm=((col==1)|(col==3)); sig=(raw-md)/e   # ADU/s, NO Background2D
    dx,dy=OFF[n]
    for q,i in enumerate(bright):
        px=(xa[i] if g=='A' else xc[i])+dx; py=(ya[i] if g=='A' else yc[i])+dy
        X0,Y0=int(round(px)),int(round(py))
        if not(H<X0<raw.shape[1]-H and H<Y0<raw.shape[0]-H): continue
        st=sig[Y0-H:Y0+H+1,X0-H:X0+H+1]; mk=gm[Y0-H:Y0+H+1,X0-H:X0+H+1]
        sat=raw[Y0-H:Y0+H+1,X0-H:X0+H+1]<15600
        Y,X=np.mgrid[-H:H+1,-H:H+1]; rr=np.hypot(X-(px-X0),Y-(py-Y0))
        ref=mk&sat&(rr>120)&(rr<=150)
        # remove a local plane fitted on the reference annulus (corona gradient)
        A=np.c_[X[ref],Y[ref],np.ones(ref.sum())]
        c,*_=np.linalg.lstsq(A,st[ref],rcond=None)
        base=c[0]*X+c[1]*Y+c[2]
        res=st-base
        for b in range(len(edges)-1):
            m=mk&sat&(rr>=edges[b])&(rr<edges[b+1])
            if m.sum()>=4:
                acc[q,b]+=np.median(res[m])*(e*e); acw[q,b]+=e*e
        pk[q]=max(pk[q],np.median(res[mk&(rr<1.2)]) if (mk&(rr<1.2)).sum() else 0)
    del raw,sig
    print("wings from",n)
P=np.where(acw>0,acc/np.maximum(acw,1e-9),np.nan)
print(f"\nDeep radial profile, {len(bright)} brightest confirmed stars, no small-scale background removal")
print(f"{'r_px':>7}{'r_arcsec':>10}{'I(ADU/s/px)':>13}{'I/Ipeak':>11}{'mag/arcsec2_rel':>17}{'n_stars':>8}")
Pn=P/pk[:,None]
for b in range(len(edges)-1):
    v=Pn[:,b]; g=np.isfinite(v)
    if g.sum()<3: continue
    med=np.median(v[g]); absI=np.median((P[:,b])[g])
    print(f"{rc[b]:7.1f}{rc[b]*AS:10.1f}{absI:13.3f}{med:11.3e}{-2.5*np.log10(abs(med)) if med>0 else float('nan'):17.2f}{g.sum():8d}")
print(f"\npeak I of each star (ADU/s): "+" ".join(f"{x:.1f}" for x in pk))
np.savez("wings.npz",r=rc,P=P,pk=pk)
