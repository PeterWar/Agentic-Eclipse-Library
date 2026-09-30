import math,random
random.seed(7)
Rsun=959.0; L=1.7516
def stats(rmin,rmax,N=400000):
    s_t2=s_ts=s_s2=s_im2=s_r2=0.0
    for _ in range(N):
        rho=math.sqrt(random.uniform(rmin*rmin,rmax*rmax))
        td=L/rho; ts=rho*Rsun
        s_t2+=td*td; s_ts+=td*ts; s_s2+=ts*ts
        s_im2+=rho**-2; s_r2+=rho*rho
    h=N/s_im2
    lam=s_ts/s_t2                      # d(eps)/d(s) if scale NOT fitted
    rc=1/math.sqrt((s_im2/N)*(s_r2/N))
    return h,lam,rc,1/math.sqrt(1-rc*rc)
for (a,b,name) in [(2,15,"2-15 (Design4)"),(2,9.6,"2-9.6 (Design1)"),(2,13.6,"trainA"),(2,9.5,"trainB"),(1.5,4.8,"Bruns")]:
    h,lam,rc,vif=stats(a,b)
    print(f"{name:16s} h={h:7.2f}  dEps/1e-6={lam*1e-6:.5f}  (959h/L={Rsun*h/L*1e-6:.5f})  rho={rc:.3f} VIF={vif:.3f}  dEps@3.34ppm={lam*3.34e-6:.4f}")
