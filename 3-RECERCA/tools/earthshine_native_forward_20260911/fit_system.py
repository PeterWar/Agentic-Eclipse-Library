"""Recreate the frozen native quadratic system for controlled continuation."""
from native_operator import *
from scipy.sparse import load_npz,vstack,hstack,block_diag,coo_matrix
from types import SimpleNamespace
def laplacian(indices,geo):
    lookup=np.full(geo.size,-1,dtype=int);lookup[indices]=np.arange(len(indices));array=lookup.reshape(geo.shape);ri=[];ci=[];value=[];degree=np.zeros(len(indices))
    for aa,bb in [(array[:,:-1],array[:,1:]),(array[:-1],array[1:])]:
        good=(aa>=0)&(bb>=0);a=aa[good];b=bb[good];ri.extend([a,b]);ci.extend([b,a]);value.extend([-np.ones(len(a)),-np.ones(len(a))]);np.add.at(degree,a,1);np.add.at(degree,b,1)
    ri.append(np.arange(len(indices)));ci.append(np.arange(len(indices)));value.append(degree)
    return coo_matrix((np.concatenate(value),(np.concatenate(ri),np.concatenate(ci))),shape=(len(indices),len(indices))).tocsr()
def build(mode,lam=10):
    geo=Geometry(16);rows=json.loads((OUT/'B0_matrices.json').read_text())['frames'];train=[r for r in rows if r['train']];folder=OUT/'matrices';data={r['stem']:dict(np.load(folder/f'{r["stem"]}_observations.npz')) for r in rows};inside=[];outside=[]
    for r in train:
        z=data[r['stem']];rr=np.hypot(z['xy'][:,0]-CX,z['xy'][:,1]-CY);inside.extend(z['g'][rr<435]);outside.extend(z['g'][rr>465])
    ms=float(np.median(inside));cs=float(np.median(outside));AM=[];AC=[];target=[];weights=[]
    for r in train:
        stem=r['stem'];z=data[stem];AM.append(load_npz(folder/f'{stem}_lunar.npz'));AC.append(load_npz(folder/f'{stem}_solar_{mode}.npz'));target.append(z['g']);weights.append(z['q']/(z['weight_variance']*14.826313721285086))
    M=vstack(AM,format='csr');C=vstack(AC,format='csr');w=np.concatenate(weights);target=np.concatenate(target);mi=np.flatnonzero(np.asarray(M.power(2).T@w).ravel()>1e-20);ci=np.flatnonzero(np.asarray(C.power(2).T@w).ravel()>1e-20)
    A=hstack([M[:,mi]*ms,C[:,ci]*cs],format='csr').multiply(np.sqrt(w)[:,None]).tocsr();b=target*np.sqrt(w);L=block_diag([laplacian(mi,geo),laplacian(ci,geo)],format='csr');eps=1e-10;diag=np.asarray(A.power(2).sum(0)).ravel()+lam*np.asarray(L.power(2).sum(0)).ravel()+eps;scale=1/np.sqrt(diag);B=A.multiply(scale[None,:]).tocsr();K=L.multiply(scale[None,:]).tocsr();rhs=B.T@b
    def objective(u):
        r=B@u-b;k=K@u;return .5*np.dot(r,r)+.5*lam*np.dot(k,k)+.5*eps*np.dot(scale*u,scale*u),B.T@r+lam*(K.T@k)+eps*scale**2*u
    return SimpleNamespace(geo=geo,rows=rows,data=data,folder=folder,ms=ms,cs=cs,mi=mi,ci=ci,scale=scale,B=B,K=K,rhs=rhs,b=b,lam=lam,eps=eps,objective=objective)
