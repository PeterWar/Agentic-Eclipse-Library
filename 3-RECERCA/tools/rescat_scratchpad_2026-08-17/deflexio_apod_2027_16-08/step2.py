import numpy as np, eb_core as E
rng = np.random.default_rng(2027)
RS = E.RSUN27; DEG=3600.

TRAINS = {
 'A  Sony 300/2.8 + A7RIIIA': dict(hw=7.14/2, hh=4.77/2, area=90.1, px=3.202),
 'B  Vixen VSD90SS + R6III' : dict(hw=4.17/2, hh=2.78/2, area=63.3, px=2.1495),
}
print("Footprint reach at Luxor (1 Rsun = %.5f deg):"%(RS/DEG))
for k,v in TRAINS.items():
    print(f"  {k}:  all-round {v['hh']/(RS/DEG):5.2f} Rsun | long axis {v['hw']/(RS/DEG):5.2f}"
          f" | corner {np.hypot(v['hw'],v['hh'])/(RS/DEG):5.2f}")

print("\n"+"="*78)
print("FIELD WEIGHT  W = sum (Rsun/r_i)^2   and the degeneracy factor D")
print("="*78)
print(f"{'config':46s} {'N':>5} {'W':>8} {'sqrt(W)':>8} {'D':>6}")
rows={}
for lab,v in TRAINS.items():
    for Vlim in [10.0, 11.0, 12.0]:
        Ns=[];Ws=[];Ds=[]
        for _ in range(120):
            x,y,V = E.sample_rect(v['hw'],v['hh'],Vlim,rng,rmin_rho=2.0)
            rho=np.hypot(x,y)/RS
            W=np.sum(1/rho**2)
            s_naive=E.sigma_eps_naive(x,y,1.0); s_full=E.sigma_eps(x,y,1.0,order=1)
            Ns.append(len(x)); Ws.append(W); Ds.append(s_full/s_naive)
        N,W,D = np.median(Ns),np.median(Ws),np.median(Ds)
        rows[(lab,Vlim)]=(N,W,D)
        print(f"{lab+f'   to V<{Vlim:.0f}':46s} {N:5.0f} {W:8.1f} {np.sqrt(W):8.2f} {D:6.2f}")

print("\n  cross-check: sigma(eps) = D * sigma_star / (L * sqrt(W)),  L=1.7516")
lab='B  Vixen VSD90SS + R6III'; N,W,D = rows[(lab,11.0)]
print(f"  e.g. {lab} to V<11, sigma_star=0.20\":"
      f"  {D*0.20/(E.L_GR*np.sqrt(W)):.4f}")

print("\n"+"="*78)
print("REQUIRED PER-STAR SIGMA (equivalent uniform), by target")
print("="*78)
targets=[("(a) 3-sigma detection of ANY deflection", 1/3.0),
         ("(b) 5-sigma Einstein vs Newton",          0.5/5.0),
         ("(c) 3% of the deflection coefficient",    0.03)]
def req(W,D,target): return target*E.L_GR*np.sqrt(W)/D
for tl,tv in targets:
    print(f"\n {tl}:  sigma(eps) <= {tv:.4f}")
    for Vlim in [10.,11.,12.]:
        NA,WA,DA = rows[('A  Sony 300/2.8 + A7RIIIA',Vlim)]
        NB,WB,DB = rows[('B  Vixen VSD90SS + R6III',Vlim)]
        # combined: two independent fits, quadrature
        sA=req(WA,DA,tv*np.sqrt(2)); sB=req(WB,DB,tv*np.sqrt(2))
        print(f"   V<{Vlim:.0f}:  train A (N={NA:4.0f}) needs {req(WA,DA,tv):6.3f}\" alone |"
              f" train B (N={NB:4.0f}) needs {req(WB,DB,tv):6.3f}\" alone |"
              f" both together {sA:6.3f}\"/{sB:6.3f}\"")
