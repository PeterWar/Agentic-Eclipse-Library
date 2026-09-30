import rawpy, numpy as np
D="/Users/USUARI/Desktop/Eclipse 2026/300mm/"
def load(f):
    with rawpy.imread(D+f+".ARW") as r:
        return r.raw_image_visible.astype(np.float64), r.raw_colors_visible
a,c=load("DSC06996"); b,_=load("DSC06999")
g=(c==1)|(c==3)
# tile 32x32, only green pixels, compute mean signal and variance of difference
h,w=a.shape; T=32
res=[]
for y in range(0,h-T,T*4):
    for x in range(0,w-T,T*4):
        m=g[y:y+T,x:x+T]
        A=a[y:y+T,x:x+T][m]-512; B=b[y:y+T,x:x+T][m]-512
        if A.max()>14000 or A.size<200: continue
        d=A-B
        # robust variance
        v=(np.percentile(d,84.13)-np.percentile(d,15.87))**2/4.0
        res.append((0.5*(A.mean()+B.mean()), v/2.0))
res=np.array(res)
print("n tiles", len(res))
# fit var = S/gain + rn2  (var in ADU^2, S in ADU, gain e-/ADU)
ok=(res[:,0]>50)&(res[:,0]<12000)
A=np.vstack([res[ok,0],np.ones(ok.sum())]).T
sol,*_=np.linalg.lstsq(A,res[ok,1],rcond=None)
slope,inter=sol
print(f"slope={slope:.5f} ADU^2/ADU -> gain={1/slope:.3f} e-/ADU ; intercept={inter:.2f} ADU^2 -> read noise={np.sqrt(max(inter,0)):.2f} ADU = {np.sqrt(max(inter,0))/slope*slope:.2f}")
print(f"read noise = {np.sqrt(max(inter,0)):.2f} ADU = {np.sqrt(max(inter,0))/ (1/ (1/slope)):.2f}")
print(f"read noise in e- = {np.sqrt(max(inter,0))*(1/slope):.2f}")
for lo,hi in [(50,300),(300,1000),(1000,3000),(3000,12000)]:
    s=(res[:,0]>lo)&(res[:,0]<hi)
    if s.sum()>5: print(f"  S in [{lo},{hi}]: n={s.sum()} <S>={res[s,0].mean():.0f} <var>={res[s,1].mean():.1f} -> gain~{res[s,0].mean()/res[s,1].mean():.3f}")
