import numpy as np
d=np.load("catalog.npz",allow_pickle=True)
RSUN=293.; AS=3.234
xa,ya,xc,yc=d['xa'],d['ya'],d['xc'],d['yc']; SNA,SNC=d['SNA'],d['SNC']
shA,shC=d['shA'],d['shC']; FT,ET,r,CH,DK,SN=d['FT'],d['ET'],d['r'],d['CH'],d['DK'],d['SN']
names=list(d['names']); rs=r/RSUN
fw=np.nanmean(np.c_[shA[:,0],shC[:,0]],1); ba=np.nanmean(np.c_[shA[:,1],shC[:,1]],1)
nd=np.nansum(SN>3.0,1)
joint=np.sqrt(SNA**2+SNC**2)
out=rs>3.0
print(f"total matched: {len(rs)} | R>3Rsun: {out.sum()} | R in 1.2-3: {((rs>1.2)&(rs<=3)).sum()} | R<1.2: {(rs<=1.2).sum()}")
print(f"\nPSF of the CONFIRMED OUTER sources (R>3 Rsun, n={out.sum()}):")
print(f"  FWHM  median={np.nanmedian(fw[out]):.2f} px = {np.nanmedian(fw[out])*AS:.1f}\"  "
      f"(16-84%: {np.nanpercentile(fw[out],16):.2f}-{np.nanpercentile(fw[out],84):.2f} px)")
print(f"  b/a   median={np.nanmedian(ba[out]):.2f}   PA median={np.nanmedian(shC[out,2]):.0f} deg")
inn=(rs>1.2)&(rs<=3)
print(f"inner matches (1.2-3 Rsun, n={inn.sum()}): FWHM median={np.nanmedian(fw[inn]):.2f} px = {np.nanmedian(fw[inn])*AS:.1f}\"  b/a={np.nanmedian(ba[inn]):.2f}")
lim=np.nanpercentile(fw[out],90)
print(f"\n--- CONFIRMED POINT SOURCES, R > 3 Rsun, sorted by flux ---")
o=np.nonzero(out)[0]; o=o[np.argsort(-FT[o])]
print(f"{'#':>3}{'x_px':>8}{'y_px':>8}{'R/Rs':>6}{'R(deg)':>7}{'SNR_A':>7}{'SNR_C':>7}{'joint':>7}{'nfr':>4}"
      f"{'FWHM_px':>8}{'FWHM_as':>8}{'b/a':>5}{'flux':>9}{'+-':>6}{'S/N':>6}{'R:G:B':>16}{'dark':>6}")
for j,i in enumerate(o):
    ch=CH[i]; g=max(ch[1],1e-6)
    print(f"{j+1:3d}{xc[i]:8.1f}{yc[i]:8.1f}{rs[i]:6.2f}{r[i]*AS/3600:7.2f}{SNA[i]:7.1f}{SNC[i]:7.1f}{joint[i]:7.1f}{nd[i]:4d}"
          f"{fw[i]:8.2f}{fw[i]*AS:8.1f}{ba[i]:5.2f}{FT[i]:9.0f}{ET[i]:6.0f}{FT[i]/ET[i]:6.1f}"
          f"{ch[0]/g:6.2f}:1:{ch[2]/g:5.2f}{DK[i]:6.0f}")
