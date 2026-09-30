import numpy as np, pickle
from scipy.spatial import cKDTree
P=pickle.load(open("peaks2.pkl","rb")); OFF=pickle.load(open("offsets2.pkl","rb"))['off']
REF='DSC06993'
def fit(n, model):
    o=np.array(OFF[n],float); A=np.eye(2)
    xa,ya=P[REF]['x'],P[REF]['y']; xb,yb=P[n]['x'],P[n]['y']
    c=np.array([3894.,2766.])
    for it in range(6):
        pa=np.c_[xa,ya]; pb=np.c_[xb,yb]
        pred=(pa-c)@A.T+c+o
        t=cKDTree(pb); d,i=t.query(pred,distance_upper_bound=(4.0 if it<2 else 2.0))
        ok=np.isfinite(d); ia=np.nonzero(ok)[0]; ib=i[ok]
        if ok.sum()<8: return None
        u=pa[ia]-c; v=pb[ib]-c
        if model=='T':
            A=np.eye(2); o=np.median(v-u,axis=0)
        else:
            # similarity/affine least squares: v = A u + o
            M=np.c_[u,np.ones(len(u))]
            sol,*_=np.linalg.lstsq(M,v,rcond=None)
            A=sol[:2].T; o=sol[2]
        r=(u@A.T+o)-v
        rms=np.sqrt((r**2).sum(axis=1).mean())
    return ok.sum(),rms,A,o,r,u
for n in sorted(P):
    if n==REF: continue
    rT=fit(n,'T'); rA=fit(n,'A')
    nT,eT,_,_,resT,uT=rT; nA,eA,A,o,resA,uA=rA
    th=np.degrees(np.arctan2(A[1,0]-A[0,1],A[0,0]+A[1,1]))
    sc=np.sqrt(abs(np.linalg.det(A)))
    print(f"{n} exp={P[n]['exp']:4.1f}  translation: n={nT:3d} rms={eT:5.2f}px | affine: n={nA:3d} rms={eA:5.2f}px  rot={th:+7.4f}deg scale={sc:.6f}")
