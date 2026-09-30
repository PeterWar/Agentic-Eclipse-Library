"""A12: biaix dels filtres contra el forat: valor mitjà (mediana) de cada capa de filtre en funció de la distància d a la vora del forat de la base, per sector de 10°."""
import sys, numpy as np, json
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad')
from compo import *
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
v=np.load(SP+'/a9_vores.npz'); TH=v['TH']; CX,CY=998.88,998.41
r=v['alfa_base_(forat)'].copy(); ok=np.isfinite(r); r[~ok]=np.interp(np.nonzero(~ok)[0],np.nonzero(ok)[0],r[ok]); k=np.exp(-0.5*(np.arange(-40,41)/8)**2); k/=k.sum(); R_hole=np.convolve(np.r_[r[-40:],r,r[:40]],k,'valid')
yy,xx=np.mgrid[0:2000,0:2000]; rr=np.hypot(xx-CX,yy-CY); az=np.rad2deg(np.arctan2(-(yy-CY),xx-CX))%360; ia=np.clip((az/0.25).astype(int),0,len(TH)-1); d=rr-R_hole[ia]
bins=np.arange(-2,31,1.0); sect=np.arange(0,360,10)
out={}; fig,axs=plt.subplots(2,5,figsize=(26,9)); axs=axs.ravel()
for j,lid in enumerate((41,42,45,46,47,49,51,53,55,56)):
    rgb,a=carrega(lid); L=rgb.mean(-1); op=LAYERS[lid]['opacity']/255.0
    tab=np.full((len(sect),len(bins)-1),np.nan); alf=np.full((len(sect),len(bins)-1),np.nan)
    for i,s in enumerate(sect):
        ks=(az>=s)&(az<s+10)
        for b in range(len(bins)-1):
            kk=ks&(d>=bins[b])&(d<bins[b+1])
            if kk.sum()>20: tab[i,b]=np.median(L[kk]); alf[i,b]=np.median(a[kk])/op
    exces=np.nanmedian(tab[:,3:9],1)-np.nanmedian(tab[:,16:26],1)   # d 1–7 vs d 14–24
    ramp=[]
    for i in range(len(sect)):
        ref=np.nanmedian(alf[i,20:28]); w=np.nonzero(alf[i]>=0.9*ref)[0]; ramp.append(float(bins[w[0]]) if len(w) else np.nan)
    out[lid]=dict(nom=LAYERS[lid]['name'],exces_per_sector=[None if np.isnan(x) else round(float(x),4) for x in exces],d_alfa90_per_sector=ramp,taula=np.round(tab,4).tolist(),alfa=np.round(alf,3).tolist())
    print(f"id {lid} {LAYERS[lid]['name'][:34]:34s} excés(d1–7 − d14–24) per sector: "+' '.join(f'{x:+.3f}' if np.isfinite(x) else '  nan ' for x in exces))
    print(f"      d on l'alfa arriba al 90 %:            "+' '.join(f'{x:5.0f} ' if np.isfinite(x) else '  nan ' for x in ramp))
    ax=axs[j]
    for i,s in enumerate(sect):
        if s in (0,40,90,140,170,200,250,270,320): ax.plot(bins[:-1]+.5,tab[i],label=f'az {s}')
    ax.axhline(0.5,color='k',lw=.5); ax.set_title(f'id {lid} {LAYERS[lid]["name"][:24]}',fontsize=9); ax.set_xlabel('d al forat (px)'); ax.grid(alpha=.3)
    if j==0: ax.legend(fontsize=7)
plt.tight_layout(); plt.savefig(SP+'/v_A12_biaix_filtres.png',dpi=70)
json.dump(out,open(SP+'/a12_biaix.json','w'))
print('sectors:',list(sect))
