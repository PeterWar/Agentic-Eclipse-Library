import numpy as np
d=np.load("secure.npz",allow_pickle=True)
AS=3.234; GAIN=3.323; ZP=3.6e6
xc,yc,rs,r,FT,ET,fw,ba,SNA,SNC,nd,CH,loc=[d[k] for k in
  ['xc','yc','rs','r','FT','ET','fw','ba','SNA','SNC','nd','CH','loc']]
idx=d['idx']
g=np.maximum(CH[:,1],1e-6)
ok=idx[(fw[idx]<4.15)&(FT[idx]/ET[idx]>3.0)&(CH[idx,0]/g[idx]>0.15)&(CH[idx,0]/g[idx]<2.6)
       &(CH[idx,2]/g[idx]>-0.5)&(CH[idx,2]/g[idx]<1.9)]
print(f"FINAL confirmed point sources: {len(ok)}")
for lo,hi in [(1.2,3),(3,5),(5,8),(8,12),(12,20)]:
    k=ok[(rs[ok]>=lo)&(rs[ok]<hi)]; print(f"   R/Rsun [{lo:4.1f},{hi:4.1f}): {len(k):3d}")
print(f"\nnumber of frames each is individually detected in (of 7): "
      f"median={np.median(nd[ok]):.0f}, all-7={int((nd[ok]==7).sum())}, >=5={(nd[ok]>=5).sum()}")
print(f"flux range: {FT[ok].min():.0f} - {FT[ok].max():.0f} ADU/s")
print(f"FWHM: median {np.median(fw[ok])*AS:.1f}\" ; b/a median {np.median(ba[ok]):.2f}")
np.save("FINAL_idx.npy",ok)
# text catalogue
with open("catalog_sony.txt","w") as f:
    f.write("# Cerca cega de fonts puntuals — Sony A7RIIIA + FE 300 mm f/2.8 GM, totalitat 12-08-2026\n")
    f.write("# 7 fotogrames sense filtre (2x8s + 3x2s + 2x1s = 24 s). DSC06990 exclosa (moguda).\n")
    f.write("# x,y = pixels del sensor al sistema de DSC06993 (visible 7968x5320). Escala 3,234\"/px.\n")
    f.write("# R = distancia al centre del disc lunar (3894.1,2765.6), en radis solars (Rsun=293 px).\n")
    f.write("# flux = ADU/s verd-equivalent (obertura r=5 px, anell 7-10 px, corregit del 50%% de mostreig verd)\n")
    f.write("# id   x_px      y_px     R_Rsun  R_deg  flux_ADUs  err   S/N   SNR_A  SNR_C  nfr  FWHM_as  b/a   R/G   B/G   V_est\n")
    o=ok[np.argsort(-FT[ok])]
    for j,i in enumerate(o):
        f.write(f"S{j+1:02d}  {xc[i]:8.2f} {yc[i]:8.2f} {rs[i]:7.2f} {r[i]*AS/3600:6.2f} {FT[i]:9.0f} {ET[i]:5.0f} "
                f"{FT[i]/ET[i]:6.1f} {SNA[i]:6.1f} {SNC[i]:6.1f} {nd[i]:4d} {fw[i]*AS:7.1f} {ba[i]:5.2f} "
                f"{CH[i,0]/g[i]:5.2f} {CH[i,2]/g[i]:5.2f} {-2.5*np.log10(FT[i]*GAIN/ZP):6.2f}\n")
print("\nwritten catalog_sony.txt")
o=ok[np.argsort(-FT[ok])]
print(f"\ntop 12:\n{'id':>4}{'x':>9}{'y':>9}{'R/Rs':>7}{'ADU/s':>8}{'S/N':>7}{'nfr':>4}")
for j,i in enumerate(o[:12]): print(f"S{j+1:02d} {xc[i]:9.1f}{yc[i]:9.1f}{rs[i]:7.2f}{FT[i]:8.0f}{FT[i]/ET[i]:7.1f}{nd[i]:4d}")
