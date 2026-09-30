import numpy as np, json
from scipy import ndimage as ndi
import fa_lib as F
C=np.load(F.S4+'/roi74p_C_sensemarques.npy'); L=F.Lstar(C); G=C[...,1]
out={}
res_mask={}
for k in F.MARKS:
    m=F.mask(k); e=F.mask('ent_'+k); y0,y1,x0,x1=F.bbox(m|e,pad=25)
    Lc=L[y0:y1,x0:x1]; mc=m[y0:y1,x0:x1]; ec=e[y0:y1,x0:x1]
    d={}
    for w in (9,21,41):
        med=ndi.median_filter(Lc,size=w); diff=Lc-med
        dark=(diff<-2)&mc; lab_,n=ndi.label(dark)
        comps=[]
        for i in range(1,n+1):
            cc=lab_==i; ys,xs=np.nonzero(cc)
            comps.append(dict(n=int(cc.sum()),cy=float(ys.mean()+y0),cx=float(xs.mean()+x0),min_dL=float(diff[cc].min()),mean_dL=float(diff[cc].mean()),
                              r=float(F.RR[y0:y1,x0:x1][cc].mean()),az=float(F.AZ[y0:y1,x0:x1][cc].mean())))
        comps.sort(key=lambda c:c['min_dL'])
        # el mateix criteri a l'entorn: quants píxels de l'entorn cauen sota −2 (taxa de fons)
        d[f'w{w}']=dict(n_px_marca=int(dark.sum()),frac_marca=float(dark.sum()/mc.sum()),frac_entorn=float(((diff<-2)&ec).sum()/ec.sum()),
                        min_dL_marca=float(diff[mc].min()),min_dL_entorn=float(diff[ec].min()),p1_marca=float(np.percentile(diff[mc],1)),p1_entorn=float(np.percentile(diff[ec],1)),
                        std_marca=float(diff[mc].std()),std_entorn=float(diff[ec].std()),n_comp=n,comps=comps[:8])
        if w==21: res_mask[k]=np.zeros_like(m); res_mask[k][y0:y1,x0:x1]=dark
    # canal G sol, finestra 21, en unitats relatives (%)
    Gc=G[y0:y1,x0:x1]; medG=ndi.median_filter(Gc,size=21); dG=(Gc-medG)/np.maximum(medG,1e-4)*100
    d['G_w21']=dict(min_pct_marca=float(dG[mc].min()),min_pct_entorn=float(dG[ec].min()),p1_marca=float(np.percentile(dG[mc],1)),p1_entorn=float(np.percentile(dG[ec],1)),std_marca=float(dG[mc].std()),std_entorn=float(dG[ec].std()))
    # marca contra entorn: mitjanes
    d['global']=dict(L_marca=float(L[m].mean()),L_entorn=float(L[e].mean()),L_marca_med=float(np.median(L[m])),L_entorn_med=float(np.median(L[e])),n_marca=int(m.sum()),n_entorn=int(e.sum()),
                     r_marca=[float(F.RR[m].min()),float(F.RR[m].max())],az_marca=[float(F.AZ[m].min()),float(F.AZ[m].max())])
    out[k]=d
json.dump(out,open(F.S4+'/fa_a_punts.json','w'),indent=1)
np.savez_compressed(F.S4+'/fa_a_dark_w21.npz',**res_mask)
for k in F.MARKS:
    d=out[k]; print(k,'global',{a:round(b,2) if isinstance(b,float) else b for a,b in d['global'].items()})
    for w in ('w9','w21','w41'):
        x=d[w]; print('  ',w,'frac marca %.3f entorn %.3f | min marca %.2f entorn %.2f | p1 marca %.2f entorn %.2f | std %.2f/%.2f | ncomp %d'%(x['frac_marca'],x['frac_entorn'],x['min_dL_marca'],x['min_dL_entorn'],x['p1_marca'],x['p1_entorn'],x['std_marca'],x['std_entorn'],x['n_comp']))
        for c in x['comps'][:4]: print('      comp n=%d (y%.0f,x%.0f) r=%.1f az=%.1f min=%.2f mean=%.2f'%(c['n'],c['cy'],c['cx'],c['r'],c['az'],c['min_dL'],c['mean_dL']))
    print('   G%%',{a:round(b,2) for a,b in d['G_w21'].items()})
