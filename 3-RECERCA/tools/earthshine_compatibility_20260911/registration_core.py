"""Deterministic coronal photometric geometry; no image generation or product edits."""
import numpy as np
import cv2
PAD=40; CORE=144; RS=440.60304883027544
YY,XX=np.mgrid[PAD:PAD+CORE,PAD:PAD+CORE].astype(np.float32)

def fit(A,B,indices,centres,similarity=False):
    if len(indices)<(4 if similarity else 2):return None
    dim=4 if similarity else 2
    t=np.zeros(dim);trace=[]
    ref=A[indices,PAD:PAD+CORE,PAD:PAD+CORE];mov=B[indices]
    gy=np.gradient(mov,axis=1);gx=np.gradient(mov,axis=2)
    for iteration in range(20):
        H=np.zeros((dim,dim));rhs=np.zeros(dim);residuals=[]
        for j,k in enumerate(indices):
            px=(centres[k][0]+XX-112)/RS;py=(centres[k][1]+YY-112)/RS
            dx=t[0]+(t[2]*px-t[3]*py if similarity else 0)
            dy=t[1]+(t[2]*py+t[3]*px if similarity else 0)
            mx=(XX+dx).astype(np.float32);my=(YY+dy).astype(np.float32)
            obs=cv2.remap(mov[j],mx,my,cv2.INTER_LINEAR).ravel().astype(float)
            D=np.column_stack([np.ones(obs.size),ref[j].ravel()])
            beta=np.linalg.lstsq(D,obs,rcond=None)[0];err=obs-D@beta
            sigma=max(float(np.median(abs(err-np.median(err)))/.67448975),1e-6)
            w=np.minimum(1,2.5*sigma/np.maximum(abs(err),1e-12))/(sigma*sigma)
            Q=D.T@(w[:,None]*D)
            beta=np.linalg.solve(Q,D.T@(w*obs));err=obs-D@beta
            jx=cv2.remap(gx[j],mx,my,cv2.INTER_LINEAR);jy=cv2.remap(gy[j],mx,my,cv2.INTER_LINEAR)
            J=np.column_stack([jx.ravel(),jy.ravel()]+([(jx*px+jy*py).ravel(),(-jx*py+jy*px).ravel()] if similarity else []))
            J-=D@np.linalg.solve(Q,D.T@(w[:,None]*J))
            H+=J.T@(w[:,None]*J);rhs+=J.T@(w*err)
            residuals.append(float(np.sqrt(np.mean(err**2))/max(np.std(ref[j]),1e-9)))
        if np.linalg.cond(H)>1e9:return None
        delta=-np.linalg.solve(H,rhs);delta=np.clip(delta,-.5,.5);t+=delta
        trace.append(float(np.linalg.norm(delta)))
        if trace[-1]<.003:break
    return dict(parameters=t.tolist(),n=len(indices),condition=float(np.linalg.cond(H)),steps=trace,relative_rms_median=float(np.median(residuals)))

def matrix(f):
    t=f['parameters'];s=t[2]/RS if len(t)==4 else 0;r=t[3]/RS if len(t)==4 else 0
    return np.array([[1+s,-r,t[0]],[r,1+s,t[1]],[0,0,1.]])

def limb_gap(a,b,radius=455.5):
    if a is None or b is None:return None
    th=np.arange(0,360,15)*np.pi/180
    p=np.array([radius*np.cos(th),radius*np.sin(th),np.ones(len(th))])
    return float(np.linalg.norm(((matrix(a)-matrix(b))@p)[:2],axis=0).max())

def local_ncc(A,B):
    rg=5;cc=cv2.matchTemplate(B[PAD-rg:PAD+CORE+rg,PAD-rg:PAD+CORE+rg],A[PAD:PAD+CORE,PAD:PAD+CORE],cv2.TM_CCOEFF_NORMED)
    j,i=np.unravel_index(np.argmax(cc),cc.shape)
    return float(cc[j,i]),bool(i in (0,2*rg) or j in (0,2*rg))
