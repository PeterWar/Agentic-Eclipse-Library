import numpy as np
u=np.load("u.npy"); v=np.load("v.npy"); s=np.load("s.npy")
c=np.array([3894.,2766.])
def fit(u,v,kind):
    U=u-c; V=v-c
    if kind=='sim':
        # V = s*Rot(th)*U + t  -> linear in (a,b,tx,ty) with a=s cos, b=s sin
        A=np.zeros((2*len(U),4)); y=np.zeros(2*len(U))
        A[0::2,0]=U[:,0]; A[0::2,1]=-U[:,1]; A[0::2,2]=1
        A[1::2,0]=U[:,1]; A[1::2,1]= U[:,0]; A[1::2,3]=1
        y[0::2]=V[:,0]; y[1::2]=V[:,1]
        p,*_=np.linalg.lstsq(A,y,rcond=None)
        a,b,tx,ty=p; M=np.array([[a,-b],[b,a]]); t=np.array([tx,ty])
    else:
        A=np.c_[U,np.ones(len(U))]
        p,*_=np.linalg.lstsq(A,V,rcond=None); M=p[:2].T; t=p[2]
    pred=U@M.T+t+c
    return M,t,pred
keep=np.ones(len(u),bool)
for it in range(5):
    M,t,pred=fit(u[keep],v[keep],'sim')
    r=np.sqrt((( (u-c)@M.T+t+c - v)**2).sum(1))
    keep=r<max(2.5,2.5*np.median(r[keep]))
sc=np.sqrt(abs(np.linalg.det(M))); th=np.degrees(np.arctan2(M[1,0],M[0,0]))
r=np.sqrt((((u-c)@M.T+t+c-v)**2).sum(1))
print(f"similarity A->C : rotation={th:+.4f} deg  scale={sc:.6f}  translation=({t[0]:+.2f},{t[1]:+.2f})")
print(f"   n_used={keep.sum()}/{len(u)}  rms={np.sqrt((r[keep]**2).mean()):.2f} px  (translation-only rms was 7.43)")
Ma,ta,_=fit(u[keep],v[keep],'aff')
ra=np.sqrt((((u-c)@Ma.T+ta+c-v)**2).sum(1))
print(f"full affine     : rms={np.sqrt((ra[keep]**2).mean()):.2f} px")
np.save("warpM.npy",M); np.save("warpT.npy",t); np.save("warpC.npy",c)
print("\nresiduals of the fit (px):")
for j in np.argsort(-s)[:14]:
    p=(u[j]-c)@M.T+t+c
    print(f"  ({u[j,0]:7.1f},{u[j,1]:7.1f}) snr={s[j]:6.1f}  resid=({p[0]-v[j,0]:+5.2f},{p[1]-v[j,1]:+5.2f}) {'' if keep[j] else ' [rejected]'}")
