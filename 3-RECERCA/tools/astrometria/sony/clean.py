#!/usr/bin/env python3
# Promogut de research/tools/rescat_scratchpad_2026-08-17/estrelles_placa_flats_16-08/sony_stars/clean.py
# (sessio del 16-08-2026). Nomes canvien les rutes: dades i intermedis surten de comu.py.
import sys, os; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu
os.chdir(comu.work("sony"))
import numpy as np
from scipy import ndimage
d=np.load("catalog.npz",allow_pickle=True)
IC=np.load("IMGC.npy"); IA=np.load("IMGA.npy")
RSUN=293.; AS=3.234; GAIN=3.323
xa,ya,xc,yc=d['xa'],d['ya'],d['xc'],d['yc']; SNA,SNC=d['SNA'],d['SNC']
shA,shC=d['shA'],d['shC']; FT,ET,r,CH,DK,SN=d['FT'],d['ET'],d['r'],d['CH'],d['DK'],d['SN']
fw=np.nanmean(np.c_[shA[:,0],shC[:,0]],1); ba=np.nanmean(np.c_[shA[:,1],shC[:,1]],1)
nd=np.nansum(SN>3.,1); joint=np.sqrt(SNA**2+SNC**2); rs=r/RSUN
# dedupe within 3 px
order=np.argsort(-joint); keep=np.ones(len(xc),bool)
for a in range(len(order)):
    i=order[a]
    if not keep[i]: continue
    dd=np.hypot(xc-xc[i],yc-yc[i]); dup=(dd<3.5)&keep; dup[i]=False; keep[dup]=False
# local corona brightness + crowding
loc=np.full(len(xc),np.nan); crowd=np.zeros(len(xc),int)
Y,X=np.mgrid[-16:17,-16:17]; rr=np.hypot(X,Y); ann=(rr>10)&(rr<=16)
for i in range(len(xc)):
    X0,Y0=int(round(xc[i])),int(round(yc[i]))
    st=IC[Y0-16:Y0+17,X0-16:X0+17]
    if st.shape==(33,33): loc[i]=np.median(st[ann])
    crowd[i]=((np.hypot(xc-xc[i],yc-yc[i])<50)&keep).sum()-1
sec=keep&(joint>6.0)&(fw>2.8)&(fw<4.8)&(ba>0.55)&(loc<25)&(crowd<=1)&(rs>1.2)
print(f"kept after dedupe: {keep.sum()} | SECURE point sources: {sec.sum()}")
print(f"local corona level: secure median={np.nanmedian(loc[sec]):.1f} ADU/s ; rejected-by-corona n={(keep&(loc>=25)&(joint>6)).sum()}")
o=np.nonzero(sec)[0]; o=o[np.argsort(-FT[o])]
ZP=3.6e6  # modelled e-/s for V=0 at this airmass (INFERRED, see notes)
print(f"\n{'#':>3}{'x_px':>8}{'y_px':>8}{'R/Rsun':>7}{'R_deg':>6}{'SNRa':>6}{'SNRc':>6}{'joint':>6}{'nfr':>4}"
      f"{'FWHM_px':>8}{'FWHM_"':>8}{'b/a':>5}{'PA':>5}{'ADU/s':>8}{'+-':>5}{'S/N':>6}{'e-/s':>8}{'Vest':>6}{'cor':>5}")
for j,i in enumerate(o):
    print(f"{j+1:3d}{xc[i]:8.1f}{yc[i]:8.1f}{rs[i]:7.2f}{r[i]*AS/3600:6.2f}{SNA[i]:6.1f}{SNC[i]:6.1f}{joint[i]:6.1f}{nd[i]:4d}"
          f"{fw[i]:8.2f}{fw[i]*AS:8.1f}{ba[i]:5.2f}{shC[i,2]:5.0f}{FT[i]:8.0f}{ET[i]:5.0f}{FT[i]/ET[i]:6.1f}"
          f"{FT[i]*GAIN:8.0f}{-2.5*np.log10(FT[i]*GAIN/ZP):6.2f}{loc[i]:5.0f}")
np.savez("secure.npz",idx=o,xc=xc,yc=yc,rs=rs,r=r,FT=FT,ET=ET,fw=fw,ba=ba,SNA=SNA,SNC=SNC,joint=joint,
         nd=nd,CH=CH,loc=loc,xa=xa,ya=ya,shC=shC)
