import numpy as np, json
from scipy import ndimage as ndi
import fa_lib as F
C=np.load(F.S4+'/roi74p_C_sensemarques.npy'); Cps=np.load(F.S4+'/roi74p_compost.npz')['C'][...,:3].astype(np.float32)/65535
L=F.Lstar(C); Lps=F.Lstar(Cps)
m222=np.load(F.S4+'/roi74p_L222.npz'); a222=m222['c-1']>0; a222d=ndi.binary_dilation(a222,iterations=3)
band=(F.RR>=457)&(F.RR<=486)&~a222d
out={}
for k in F.MARKS:
    m=F.mask(k); az=F.AZ[m]; a0,a1=az.min()-8,az.max()+8; sel=band&(F.AZ>=a0)&(F.AZ<=a1)
    d=(Lps-L)[sel]; out[k]=dict(n=int(sel.sum()),dL_mean=float(d.mean()),dL_min=float(d.min()),dL_max=float(d.max()),dL_p1=float(np.percentile(d,1)),dL_p99=float(np.percentile(d,99)),
        DN16_max=float(np.abs(Cps-C)[sel].max()*65535),DN16_p99=float(np.percentile(np.abs(Cps-C)[sel],99)*65535))
    print(k,out[k])
# el traç mateix: quants píxels té alfa>0 i alfa>0.5 a la capa 222, i el seu color
print('222 alfa>0:',int(a222.sum()),' alfa>0.5:',int((m222['c-1']>32767).sum()),' alfa max',m222['c-1'].max()/65535)
json.dump(out,open(F.S4+'/fa_d_ps_vs_recomp.json','w'),indent=1)
