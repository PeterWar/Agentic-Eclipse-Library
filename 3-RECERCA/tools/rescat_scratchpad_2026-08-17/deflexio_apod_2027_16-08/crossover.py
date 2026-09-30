import numpy as np
np.random.seed(55); LDEF=1.7516; RSUN=945.6

def h_lever(rin,rout,n=400000):
    r=np.sqrt(np.random.uniform(rin**2,rout**2,n)); return 1.0/np.mean(r**-2)

def sig_eps(rin,rout,N,sper,order=3,fix_scale=False,ntr=8):
    out=[]
    for _ in range(ntr):
        rr=np.sqrt(np.random.uniform(rin**2,rout**2,N)); tt=np.random.uniform(0,2*np.pi,N)
        xx,yy=rr*np.cos(tt),rr*np.sin(tt); Rn=rr.max(); X,Y=xx/Rn,yy/Rn
        cols=[np.ones_like(X)]
        for o in range(1,order+1):
            for i in range(o+1): cols.append(X**(o-i)*Y**i)
        M=np.array(cols).T; n_,m=M.shape; Z=np.zeros((n_,m))
        Jx=np.hstack([M,Z]); Jy=np.hstack([Z,M])
        if fix_scale:
            v=np.zeros(2*m); v[1]=1; v[m+2]=1; v/=np.linalg.norm(v)
            P=np.eye(2*m)-np.outer(v,v); Jx=Jx@P; Jy=Jy@P
        Jx=np.hstack([Jx,(LDEF/rr*(xx/rr))[:,None]]); Jy=np.hstack([Jy,(LDEF/rr*(yy/rr))[:,None]])
        F=Jx.T@Jx+Jy.T@Jy; out.append(np.sqrt(np.linalg.pinv(F,rcond=1e-12)[-1,-1])*sper)
    return float(np.mean(out))

print("="*94)
print("SHOULD YOU IMPORT THE PLATE SCALE?   (sigma_S = 3.34e-6, the best ever achieved: Bruns 2017)")
print("  imported-scale error contribution to eps  =  959\" * h * sigma_S / 1.7516,   h = 1/<r^-2>")
print("="*94)
print(f"{'field':>14} {'N':>6} {'h':>7} {'free':>8} {'fixed':>8} {'imported-scale err':>19} {'total ext':>10} {'verdict':>10}")
for lab,a,b,N in [("1.5-4.8 (Bruns)",1.5,4.82,20),("2-5",2,5,150),("2-8",2,8,500),
                  ("2-11",2,11,1000),("2-15",2,15,1500),("2-20",2,20,2200)]:
    h=h_lever(a,b)
    fr=sig_eps(a,b,N,0.18,3,False); fx=sig_eps(a,b,N,0.18,3,True)
    ext=959*h*3.34e-6/LDEF
    tot=np.hypot(fx,ext)
    print(f"{lab:>14} {N:6d} {h:7.1f} {fr:8.4f} {fx:8.4f} {ext:19.4f} {tot:10.4f} "
          f"{'IMPORT' if tot<fr else 'FIT IN-FRAME':>12}")

print()
print("  break-even sigma_S (below which importing wins), for each field:")
for lab,a,b,N in [("1.5-4.8 (Bruns)",1.5,4.82,20),("2-8",2,8,500),("2-15",2,15,1500)]:
    h=h_lever(a,b); fr=sig_eps(a,b,N,0.18,3,False); fx=sig_eps(a,b,N,0.18,3,True)
    d=fr**2-fx**2
    if d<=0: print(f"    {lab}: never"); continue
    sS=np.sqrt(d)*LDEF/(959*h)
    print(f"    {lab:>16}: sigma_S < {sS:.2e}   (Bruns achieved 3.34e-6 -> "
          f"{'ACHIEVABLE' if sS>3.34e-6 else 'NOT achievable'})")

print()
print("="*94); print("TIME BUDGET: what 120 s of calibration fields costs on the eclipse field")
print("="*94)
T_tot=383.0
for cal in [0,60,120,160]:
    Tecl=T_tot-cal-25          # 25 s slew/settle overhead
    print(f"  calibration {cal:3d} s -> {Tecl:5.1f} s on the Sun ; photon sigma scales x{np.sqrt(263/Tecl):.3f}"
          f" rel. to 263 s ; frames at 10 s: {Tecl/10:.0f}")
