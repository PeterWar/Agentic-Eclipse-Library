import numpy as np, json, sys
import fa_lib as F
C74=np.load(F.S4+'/roi74p_C_sensemarques.npy'); C71=np.load(F.S4+'/roi71_C_sensemarques.npy')
L74=F.Lstar(C74); L71=F.Lstar(C71)
rb=np.arange(440,486); ri=np.floor(F.RR).astype(int)
sectors={'m2':(104,113),'m3':(115,119),'m4':(151,158),'m5':(163,171),'m7':(220,249),'tot':(0,360),'N_ample':(60,120),'W':(150,210),'S':(240,300),'E':(330,30)}
out={}
for k,(a0,a1) in sectors.items():
    sel=((F.AZ>=a0)&(F.AZ<a1)) if a0<a1 else ((F.AZ>=a0)|(F.AZ<a1))
    p74=[];p71=[];n=[]
    for r in rb:
        s=sel&(ri==r); p74.append(float(np.median(L74[s]))); p71.append(float(np.median(L71[s]))); n.append(int(s.sum()))
    out[k]=dict(r=rb.tolist(),L74=p74,L71=p71,n=n)
json.dump(out,open(F.S4+'/fa_e_perfil_radial.json','w'),indent=1)
for k in sectors:
    print('==',k)
    print('   r  : '+' '.join('%5d'%r for r in range(450,476)))
    print('  V74 : '+' '.join('%5.1f'%out[k]['L74'][r-440] for r in range(450,476)))
    print('  V71 : '+' '.join('%5.1f'%out[k]['L71'][r-440] for r in range(450,476)))
    print('  dif : '+' '.join('%+5.1f'%(out[k]['L74'][r-440]-out[k]['L71'][r-440]) for r in range(450,476)))
# gràfic
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
fig,ax=plt.subplots(2,5,figsize=(22,8))
for i,k in enumerate(sectors):
    a=ax.flat[i]; a.plot(rb,out[k]['L74'],'r-',label='V74'); a.plot(rb,out[k]['L71'],'b-',label='V71'); a.axvline(456,color='k',ls=':'); a.set_title(k+' az %s'%(sectors[k],)); a.set_xlabel('r px'); a.set_ylabel('L* mediana anell'); a.grid(alpha=.3); a.legend()
plt.tight_layout(); plt.savefig(F.S4+'/v_fa_perfil_radial.png',dpi=90)
