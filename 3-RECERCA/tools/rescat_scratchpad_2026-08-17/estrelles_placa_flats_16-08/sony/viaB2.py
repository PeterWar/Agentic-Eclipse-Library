import numpy as np, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0,'.')
from viaB import pair_analysis
from common import SCALE
cases=[
 ("DSC06983.ARW","DSC06995.ARW",'G1',(1.20,180),"corona interior 1/30 (dither 64 s)"),
 ("DSC06983.ARW","DSC06995.ARW",'G1',(1.35,285),"corona 1,35 R 1/30 (dither 64 s)"),
 ("DSC07000.ARW","DSC07002.ARW",'G1',(1.20,180),"corona interior, brack. 1/800+1/100 (mateix instant)"),
 ("DSC07000.ARW","DSC07002.ARW",'G1',(1.05,222),"PROTUBERANCIA az222, brack. 1/800+1/100"),
 ("DSC06979.ARW","DSC06981.ARW",'G1',(1.05,222),"PROTUBERANCIA az222, brack. C2+2,5"),
 ("DSC07000.ARW","DSC07002.ARW",'G1',(0.55,0),"CONTROL dins el disc lunar"),
]
for a,b,ch,pos,lab in cases:
    r=pair_analysis(a,b,ch,pos,n=64,regbox=128,label=lab)
    if r is None: print(lab,"->None"); continue
    f=r['f']; sig=r['Psig']; noi=r['Pn']; ratio=sig/np.maximum(noi,1e-30)
    print("\n== %s"%lab)
    print("   shift=(%.2f,%.2f) plane px  k=%.4f  saturat=%s  mitjana=%.0f ADU"%(r['shift'][0],r['shift'][1],r['k'],r['sat'],r['mean']))
    sel=[0.0625,0.125,0.1875,0.25,0.3125,0.375,0.4375,0.5]
    print("   f[c/px_pla]  lambda[\"]   P_senyal    P_soroll   ratio")
    for ff in sel:
        i=int(np.argmin(np.abs(f-ff)))
        print("     %6.3f    %8.2f  %10.3e %10.3e  %7.2f"%(f[i],2*SCALE/f[i],sig[i],noi[i],ratio[i]))
    good=np.isfinite(ratio)&(f>0.05); ff=f[good]; rr=ratio[good]; cross=np.nan
    for i in range(len(ff)-1):
        if rr[i]>=1 and rr[i+1]<1:
            cross=ff[i]+(1-rr[i])*(ff[i+1]-ff[i])/(rr[i+1]-rr[i]); break
    if np.isnan(cross): print("   -> senyal per damunt del soroll fins a Nyquist (ratio Nyq=%.2f)"%rr[-1])
    else: print("   -> tall a f=%.4f c/px_pla -> 1/(2f)=%.2f px_pla = %.2f arcsec"%(cross,1/(2*cross),1/(2*cross)*2*SCALE))
