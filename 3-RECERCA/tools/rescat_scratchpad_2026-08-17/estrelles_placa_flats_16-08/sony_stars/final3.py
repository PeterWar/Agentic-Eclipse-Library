import numpy as np
d=np.load("secure.npz",allow_pickle=True)
IC=np.load("IMGC.npy"); IA=np.load("IMGA.npy")
AS=3.234; GAIN=3.323; ZP=3.6e6
xc,yc,xa,ya,rs,r,FT,ET,fw,ba,SNA,SNC,nd,CH=[d[k] for k in
  ['xc','yc','xa','ya','rs','r','FT','ET','fw','ba','SNA','SNC','nd','CH']]
prev=np.load("FINAL_idx.npy")
Y,X=np.mgrid[-16:17,-16:17]; rr=np.hypot(X,Y); ann=(rr>9)&(rr<=16)
lev=np.full(len(xc),np.nan); grad=np.full(len(xc),np.nan)
for i in prev:
    vals=[]
    for IM,px,py in ((IC,xc[i],yc[i]),(IA,xa[i],ya[i])):
        st=IM[int(round(py))-16:int(round(py))+17,int(round(px))-16:int(round(px))+17]
        if st.shape!=(33,33): continue
        a=st[ann]; vals.append((np.median(a),np.percentile(a,90)-np.percentile(a,10)))
    if vals:
        lev[i]=max(v[0] for v in vals); grad[i]=max(v[1] for v in vals)
ok=prev[(lev[prev]<12)&(grad[prev]<28)]
g=np.maximum(CH[:,1],1e-6)
print(f"FINAL confirmed stellar point sources: {len(ok)}  (rejected {len(prev)-len(ok)} sitting on corona structure)")
for lo,hi in [(1.2,3),(3,5),(5,8),(8,12),(12,20)]:
    k=ok[(rs[ok]>=lo)&(rs[ok]<hi)]; print(f"   R/Rsun [{lo:4.1f},{hi:4.1f}): {len(k):3d}")
print(f"\nflux {FT[ok].min():.0f}-{FT[ok].max():.0f} ADU/s | FWHM median {np.median(fw[ok])*AS:.1f}\" "
      f"| detected in >=5 of 7 frames: {(nd[ok]>=5).sum()}/{len(ok)}")
area=41.6e6*(AS/3600)**2
print(f"surface density {len(ok)/area:.2f} deg^-2 over {area:.1f} deg^2")
o=ok[np.argsort(-FT[ok])]
with open("catalog_sony.txt","w") as f:
    f.write("# CERCA CEGA DE FONTS PUNTUALS - Sony A7RIIIA + FE 300 mm f/2,8 GM - totalitat 12-08-2026\n")
    f.write("# 7 fotogrames sense filtre: 2x8s (DSC06987,06993) + 3x2s (06984,06996,06999) + 2x1s (06985,06991) = 24 s\n")
    f.write("# EXCLOSES: DSC06990 (moguda, per encarrec) i DSC06988 (1s, no es va poder registrar: 4,0 sigma sobre 6561 proves)\n")
    f.write("# Coordenades: pixels del sensor en el sistema de DSC06993 (area visible 7968x5320). Escala 3,234\"/px.\n")
    f.write("# R: distancia al centre del DISC LUNAR ajustat a DSC06993, (3894,1 , 2765,6), en radis solars (Rsun=293 px).\n")
    f.write("#    El centre del Sol NO es el de la Lluna; a l'instant de DSC06993 la diferencia es ~2 px.\n")
    f.write("# flux: ADU/s verd-equivalent (obertura r=5 px, anell 7-10 px; corregit del mostreig verd del 50%)\n")
    f.write("# V_est: NOMES ORIENTATIU (punt zero modelat, k=0,37 mag/massa d'aire, X=6,4). Incertesa ~ +/-0,7 mag.\n")
    f.write("#\n# id      x_px      y_px  R_Rsun  R_deg  flux_ADUs   err    S/N   SNR_A  SNR_C  nfr  FWHM_as   b/a    R/G    B/G   V_est\n")
    for j,i in enumerate(o):
        f.write(f"S{j+1:02d}  {xc[i]:9.2f} {yc[i]:9.2f} {rs[i]:7.2f} {r[i]*AS/3600:6.2f} {FT[i]:10.0f} {ET[i]:5.0f} "
                f"{FT[i]/ET[i]:6.1f} {SNA[i]:7.1f} {SNC[i]:6.1f} {nd[i]:4d} {fw[i]*AS:8.1f} {ba[i]:5.2f} "
                f"{CH[i,0]/g[i]:6.2f} {CH[i,2]/g[i]:6.2f} {-2.5*np.log10(FT[i]*GAIN/ZP):7.2f}\n")
print(f"\n{'id':>4}{'x_px':>9}{'y_px':>9}{'R/Rs':>7}{'R_deg':>6}{'ADU/s':>8}{'S/N':>7}{'SNR_A':>7}{'SNR_C':>7}{'nfr':>4}{'FWHM"':>7}{'V_est':>6}")
for j,i in enumerate(o):
    print(f"S{j+1:02d}{xc[i]:9.1f}{yc[i]:9.1f}{rs[i]:7.2f}{r[i]*AS/3600:6.2f}{FT[i]:8.0f}{FT[i]/ET[i]:7.1f}"
          f"{SNA[i]:7.1f}{SNC[i]:7.1f}{nd[i]:4d}{fw[i]*AS:7.1f}{-2.5*np.log10(FT[i]*GAIN/ZP):6.2f}")
