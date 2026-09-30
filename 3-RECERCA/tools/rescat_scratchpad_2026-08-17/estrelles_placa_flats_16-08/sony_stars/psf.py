import numpy as np
d=np.load("secure.npz",allow_pickle=True)
IC=np.load("IMGC.npy"); IA=np.load("IMGA.npy")
AS=3.234
xc,yc,rs,FT,fw=d['xc'],d['yc'],d['rs'],d['FT'],d['fw']; idx=d['idx']
out=idx[rs[idx]>4.0]; inn=idx[rs[idx]<3.1]
print(f"FWHM of secure sources with R>4 Rsun (n={len(out)}): median={np.median(fw[out]):.2f} px "
      f"= {np.median(fw[out])*AS:.1f}\"  range {fw[out].min():.2f}-{fw[out].max():.2f}")
print(f"FWHM of the R<3.1 Rsun group      (n={len(inn)}): median={np.median(fw[inn]):.2f} px "
      f"= {np.median(fw[inn])*AS:.1f}\"  range {fw[inn].min():.2f}-{fw[inn].max():.2f}")
print("\nFWHM vs field radius from the optical axis, secure R>4 sources:")
for lo,hi in [(0,1500),(1500,2500),(2500,3500),(3500,5000)]:
    k=out[(np.hypot(xc[out]-3984,yc[out]-2660)>=lo)&(np.hypot(xc[out]-3984,yc[out]-2660)<hi)]
    if len(k): print(f"  r_field {lo}-{hi} px: n={len(k):2d} FWHM={np.median(fw[k]):.2f} px = {np.median(fw[k])*AS:.1f}\"")
# --- radial PSF profile of the brightest, normalised ---
bright=out[np.argsort(-FT[out])][:5]
print(f"\nradial PSF profile from the {len(bright)} brightest confirmed stars (normalised to peak):")
H=70; Y,X=np.mgrid[-H:H+1,-H:H+1]
edges=np.array([0,1,1.5,2,2.5,3,4,5,6,8,10,13,17,22,28,35,45,55,70],float)
prof=np.full((len(bright),len(edges)-1),np.nan); pk=np.zeros(len(bright))
for q,i in enumerate(bright):
    X0,Y0=int(round(xc[i])),int(round(yc[i]))
    st=IC[Y0-H:Y0+H+1,X0-H:X0+H+1].astype(np.float64)
    if st.shape!=(2*H+1,2*H+1): continue
    rr=np.hypot(X-(xc[i]-X0),Y-(yc[i]-Y0))
    st=st-np.median(st[(rr>60)&(rr<=70)])
    pk[q]=st[rr<1.0].max()
    for b in range(len(edges)-1):
        m=(rr>=edges[b])&(rr<edges[b+1])
        if m.sum()>3: prof[q,b]=np.median(st[m])
rc=0.5*(edges[:-1]+edges[1:])
print(f"{'r_px':>7}{'r_arcsec':>10}{'I/Ipeak':>12}{'mag/px':>9}{'scatter':>10}  per-star I/Ipeak")
for b in range(len(edges)-1):
    v=prof[:,b]/pk
    g=np.isfinite(v)
    if g.sum()<2: continue
    print(f"{rc[b]:7.1f}{rc[b]*AS:10.1f}{np.median(v[g]):12.3e}{-2.5*np.log10(max(np.median(v[g]),1e-12)):9.2f}"
          f"{np.std(v[g]):10.1e}  "+" ".join(f"{x:8.1e}" for x in v[g]))
np.savez("psfprof.npz",r=rc,prof=prof,pk=pk,bright=bright)
