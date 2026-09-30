import numpy as np
rng=np.random.default_rng(0)
N=801; c=(N-1)/2
y,x=np.mgrid[0:N,0:N]
r=np.hypot(x-c,y-c); phi=np.arctan2(y-c,x-c)%(2*np.pi)
# corona sintetica: gradient radial + estructura azimutal forta (streamers vs forats) + soroll
base=1e5*np.exp(-(r-100)/120.0)
az=1.0+0.8*np.cos(2*phi)+0.35*np.cos(6*phi)          # streamers equatorials
fine=1.0+0.10*np.cos(18*phi)*np.exp(-(r-100)/400.0)  # estructura fina
img=base*az*fine+rng.normal(0,30,(N,N))
ns=50
ri=np.round(r).astype(int)
seg=(np.floor(phi*ns/(2*np.pi)).astype(int))%ns
sel=(ri>=120)&(ri<=340)
def stats(idx,vals,size):
    n=np.bincount(idx,minlength=size); s=np.bincount(idx,weights=vals,minlength=size)
    s2=np.bincount(idx,weights=vals**2,minlength=size)
    m=np.where(n>0,s/np.maximum(n,1),0.0)
    v=np.where(n>1,(s2-n*m**2)/np.maximum(n-1,1),0.0)
    return n,m,np.sqrt(np.maximum(v,0))
rmax=ri.max()+1
n_r,m_r,s_r=stats(ri[sel],img[sel],rmax)                       # NRGF: anell sencer
idx2=ri[sel]*ns+seg[sel]
n2,m2,s2=stats(idx2,img[sel],rmax*ns)
m2=m2.reshape(rmax,ns); s2=s2.reshape(rmax,ns); n2=n2.reshape(rmax,ns)
print(f"{'r':>5} {'NRGF mean':>12} {'FNRGF a0/2':>12} {'dif %':>7} {'NRGF sigma':>11} {'FNRGF c0/2':>11} {'dif %':>8}")
for rr in (150,200,250,300):
    ok=n2[rr]>0
    a0h=m2[rr][ok].mean()   # A0=1, resta 0  -> a_{r,0}/2 = mitjana de mitjanes de segment
    c0h=s2[rr][ok].mean()   # S0=1, resta 0  -> c_{r,0}/2 = mitjana de desviacions de segment
    print(f"{rr:5d} {m_r[rr]:12.1f} {a0h:12.1f} {100*(a0h-m_r[rr])/m_r[rr]:7.2f} {s_r[rr]:11.1f} {c0h:11.1f} {100*(c0h-s_r[rr])/s_r[rr]:8.2f}")
