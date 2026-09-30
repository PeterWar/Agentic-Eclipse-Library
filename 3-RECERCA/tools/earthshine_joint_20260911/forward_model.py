"""Linear lunar/solar scene forward model and exact translation adjoints.
Source-domain prototype on the fixed1400 grid, not a native-CFA forward model.
The internal occultation silhouette is measured input and never edits PSB masks.
"""
from joint_common import *
from scipy.fft import dctn,idctn
from scipy.ndimage import distance_transform_edt
from scipy.sparse.linalg import LinearOperator,cg

def integer_shift(a,dy,dx):
    out=np.zeros_like(a)
    ys=slice(max(0,-dy),min(N,N-dy));yd=slice(max(0,dy),min(N,N+dy))
    xs=slice(max(0,-dx),min(N,N-dx));xd=slice(max(0,dx),min(N,N+dx))
    out[yd,xd]=a[ys,xs];return out

class Warp:
    def __init__(self,dy,dx):
        iy=int(np.floor(dy));ix=int(np.floor(dx));fy=dy-iy;fx=dx-ix
        self.parts=[(iy,ix,(1-fy)*(1-fx)),(iy+1,ix,fy*(1-fx)),(iy,ix+1,(1-fy)*fx),(iy+1,ix+1,fy*fx)]
    def forward(self,a):return sum(w*integer_shift(a,dy,dx) for dy,dx,w in self.parts if w)
    def adjoint(self,a):return sum(w*integer_shift(a,-dy,-dx) for dy,dx,w in self.parts if w)

def silhouette():
    edge=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy');P=np.zeros((N,N));y,x=np.mgrid[:N,:N]
    # Pixel-area quadrature of the observed non-circular Vixen silhouette.
    for dy in [-.375,-.125,.125,.375]:
        for dx in [-.375,-.125,.125,.375]:
            xx=x+dx-CX;yy=y+dy-CY;t=(np.arctan2(yy,xx)%(2*np.pi))*len(edge)/(2*np.pi);j=np.floor(t).astype(int);u=t-j;rad=edge[j]*(1-u)+edge[(j+1)%len(edge)]*u;P+=(np.hypot(xx,yy)<rad)/16
    return P

def graph_laplacian(a,mask):
    out=np.zeros_like(a)
    for axis in [0,1]:
        lo=[slice(None)]*2;hi=lo.copy();lo[axis]=slice(None,-1);hi[axis]=slice(1,None);lo=tuple(lo);hi=tuple(hi);ok=mask[lo]&mask[hi];d=(a[hi]-a[lo])*ok;out[lo]-=d;out[hi]+=d
    return out

class JointScene:
    def __init__(self,frames,weights,solar_centres,sigma,occlusion=None,forward_sigma=None):
        self.g=frames;self.w=weights;self.P=silhouette() if occlusion is None else np.array(occlusion,dtype=float,copy=True);self.Q=1-self.P;self.reference=np.mean(solar_centres,axis=0)
        self.warps=[Warp(*(s-self.reference)[::-1]) for s in solar_centres]
        f=np.arange(N)/(2*N);freq2=f[:,None]**2+f[None,:]**2
        # A moment-matched area correction; the approximation is declared and
        # cannot be mistaken for an exact native pixel/CFA response.
        self.sigma=float(np.sqrt(max(sigma**2-1/12,0.1))) if forward_sigma is None else float(forward_sigma);self.H=np.exp(-2*np.pi**2*self.sigma**2*freq2)
        self.mm=self.P>0;covered=sum(t.adjoint(self.Q) for t in self.warps);self.cm=covered>1e-8
        self.mi=np.flatnonzero(self.mm);self.ci=np.flatnonzero(self.cm);self.nm=len(self.mi);self.nc=len(self.ci);self.size=self.nm+self.nc
        sumw=np.sum(weights,0);base=np.sum(weights*frames,0)/np.maximum(sumw,1e-30)
        self.ms=float(np.median(base[self.P>.999]));self.cs=float(np.median(base[(self.P==0)&(sumw>0)]));assert self.ms>0 and self.cs>0
        self.x0=self.pack(base/self.ms,base/self.cs)
        self.rhs=self.adjoint([w*g for w,g in zip(self.w,self.g)])
        # Spatial diagonal approximation for the normal matrix. Positive.
        self.dm=np.zeros((N,N));self.dc=self.dm.copy()
        for w,t in zip(self.w,self.warps):
            ww=self.conv(w);self.dm+=self.ms**2*self.P**2*ww;self.dc+=self.cs**2*t.adjoint(self.Q**2*ww)
    def conv(self,a):return idctn(dctn(a,type=2,norm='ortho')*self.H,type=2,norm='ortho')
    def pack(self,m,c):return np.concatenate([m.ravel()[self.mi],c.ravel()[self.ci]])
    def unpack(self,v):
        m=np.zeros((N,N));c=m.copy();m.ravel()[self.mi]=v[:self.nm];c.ravel()[self.ci]=v[self.nm:];return m,c
    def forward(self,v):
        m,c=self.unpack(v);m*=self.ms;c*=self.cs
        return [self.conv(self.P*m+self.Q*t.forward(c)) for t in self.warps]
    def adjoint(self,ys):
        m=np.zeros((N,N));c=m.copy()
        for y,t in zip(ys,self.warps):
            yy=self.conv(y);m+=self.ms*self.P*yy;c+=self.cs*t.adjoint(self.Q*yy)
        return self.pack(m,c)
    def regularizer(self,v):
        m,c=self.unpack(v);m=graph_laplacian(graph_laplacian(m,self.mm),self.mm);c=graph_laplacian(graph_laplacian(c,self.cm),self.cm);return self.pack(m,c)
    def solve(self,lam,x0=None,maxiter=500,rtol=3e-6):
        def mv(v):return self.adjoint([w*y for w,y in zip(self.w,self.forward(v))])+lam*self.regularizer(v)+1e-8*v
        diag=self.pack(self.dm,self.dc)*float(np.mean(self.H**2))+20*lam+1e-8
        op=LinearOperator((self.size,self.size),matvec=mv,dtype=np.float64);pre=LinearOperator(op.shape,matvec=lambda v:v/diag,dtype=np.float64);steps=[0]
        def cb(v):
            steps[0]+=1
            if steps[0]%100==0:print('JOINT CG',lam,steps[0],flush=True)
        v,info=cg(op,self.rhs,x0=self.x0 if x0 is None else x0,M=pre,rtol=rtol,atol=0,maxiter=maxiter,callback=cb)
        residual=mv(v)-self.rhs
        normal=float(np.linalg.norm(residual)/np.linalg.norm(self.rhs));pred=self.forward(v);chi=float(sum(np.sum(w*(y-g)**2) for w,y,g in zip(self.w,pred,self.g))/sum(np.count_nonzero(w) for w in self.w))
        blocks={k:float(np.linalg.norm(residual[s])/np.linalg.norm(self.rhs[s])) for k,s in [('lunar',slice(None,self.nm)),('solar',slice(self.nm,None))]}
        return v,dict(lambda_scaled=float(lam),cg_info=int(info),iterations=steps[0],rtol=rtol,normal_relative_residual=normal,block_relative_residuals=blocks,effective_noise_discrepancy=chi)
