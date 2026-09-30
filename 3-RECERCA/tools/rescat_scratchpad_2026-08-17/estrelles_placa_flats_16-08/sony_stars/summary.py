import numpy as np
d=np.load("secure.npz",allow_pickle=True)
AS=3.234; RSUN=293.; GAIN=3.323; ZP=3.6e6
xc,yc,rs,r,FT,ET,fw,ba,SNA,SNC,joint,nd,CH,loc=[d[k] for k in
   ['xc','yc','rs','r','FT','ET','fw','ba','SNA','SNC','joint','nd','CH','loc']]
idx=d['idx']
star=idx[fw[idx]<4.15]
print(f"SECURE POINT SOURCES with stellar FWHM (<4.15 px): {len(star)}")
for lo,hi in [(1.2,2),(2,3),(3,4),(4,6),(6,10),(10,20)]:
    k=star[(rs[star]>=lo)&(rs[star]<hi)]; print(f"   R/Rsun [{lo:4.1f},{hi:4.1f}): {len(k):3d}")
area_deg2=41.6e6*(AS/3600)**2
print(f"\nfield {area_deg2:.1f} deg^2 ; surface density of confirmed sources = {len(star)/area_deg2:.2f} per deg^2")
print(f"faintest confirmed: {FT[star].min():.0f} ADU/s = {FT[star].min()*GAIN:.0f} e-/s -> Vest {-2.5*np.log10(FT[star].min()*GAIN/ZP):.2f}")
print(f"brightest        : {FT[star].max():.0f} ADU/s = {FT[star].max()*GAIN:.0f} e-/s -> Vest {-2.5*np.log10(FT[star].max()*GAIN/ZP):.2f}")
med_e=np.median(ET[star[rs[star]>4]])
print(f"\ntypical 1-sigma photometric error in the outer field: {med_e:.0f} ADU/s")
print(f"detection threshold (4.5 sigma in each group ~ 6.4 sigma joint): ~{6.4*med_e:.0f} ADU/s "
      f"= {6.4*med_e*GAIN:.0f} e-/s -> Vest {-2.5*np.log10(6.4*med_e*GAIN/ZP):.2f}")
ch=CH[star]; g=ch[:,1]
ok=(g>200)
print(f"\ncolour of the {ok.sum()} brightest confirmed sources (aperture flux ratios, no colour calibration):")
print(f"   R/G median={np.median(ch[ok,0]/g[ok]):.2f}  B/G median={np.median(ch[ok,2]/g[ok]):.2f}")
print(f"   (a hot pixel or cosmic ray would show up in ONE channel only)")
print("\n--- FINAL CATALOGUE (stellar FWHM, both pointing groups, isolated) ---")
o=star[np.argsort(-FT[star])]
print(f"{'#':>3}{'x_px':>8}{'y_px':>8}{'R/Rsun':>7}{'R_deg':>6}{'ADU/s':>8}{'+-':>5}{'S/N':>6}{'SNRa':>6}{'SNRc':>6}"
      f"{'nfr':>4}{'FWHM"':>7}{'b/a':>5}{'R/G':>6}{'B/G':>6}{'Vest':>6}")
for j,i in enumerate(o):
    gg=max(CH[i,1],1e-6)
    print(f"{j+1:3d}{xc[i]:8.1f}{yc[i]:8.1f}{rs[i]:7.2f}{r[i]*AS/3600:6.2f}{FT[i]:8.0f}{ET[i]:5.0f}{FT[i]/ET[i]:6.1f}"
          f"{SNA[i]:6.1f}{SNC[i]:6.1f}{nd[i]:4d}{fw[i]*AS:7.1f}{ba[i]:5.2f}{CH[i,0]/gg:6.2f}{CH[i,2]/gg:6.2f}"
          f"{-2.5*np.log10(max(FT[i],1e-3)*GAIN/ZP):6.2f}")
