"""Native-green, epoch-resolved HDR and differential temporal references.
Selection is on smoothed observations, never per-pixel minima or painted masks.
No brightness threshold: short exposures retain negative/read-noise samples.
"""
from comu45 import *
from scipy.ndimage import gaussian_filter, distance_transform_edt
from scipy.special import expit

GAIN={'vixen':1.,'sony_A':.324143,'sony_B':.3372}
ALPHA={'vixen10':35.54865158040903,'vixen2':32.940404784734135,'vixen_short':14.826313721285086,'sony_A':18.864586432620264,'sony_B':18.553169370338857}
# Effective scalar weight calibration in the fixed8–64px band. It includes
# incoherent FPN and may include unmatched MTF. NOT a physical total variance.
def component(m):
    if m['tren']!='vixen':return m['grup']
    return 'vixen10' if m['exp']>5 else 'vixen2' if m['exp']>1 else 'vixen_short'
EDGE=np.load(CAU44/'vixen_optical_edge.npy')
SURFACE=R<np.interp((PHI%(2*np.pi))*len(EDGE)/(2*np.pi),np.arange(len(EDGE)),EDGE,period=len(EDGE))


def ng(a,w,s):
    d=gaussian_filter(w.astype(float),s)
    return gaussian_filter(np.nan_to_num(a)*w,s)/np.maximum(d,1e-30),d

def epoch(m):
    if m['tren']=='vixen':
        t=m['t_mid_C2'];j=int(np.searchsorted([6,12.1,18.5,64,74,80.5,86.5,93,200],t))
        return 'vixen_'+str(j)
    t=m['t_mid_C2'];j=int(np.searchsorted([20,45,74,81,90,200],t))
    return m['grup']+'_'+str(j)

def stack(fr):
    num=np.zeros_like(R,dtype=float);den=num.copy();vn=num.copy();n=num.copy();rows=[]
    for m in fr:
        d=np.load(m['native']['file']);gain=GAIN[m['grup']];g=d['g']*gain;q=d['q'];v=d['variance']*gain**2
        ok=np.isfinite(g)&np.isfinite(v)&(v>0)&(q>0)
        vs,_=ng(v,ok,4.)
        w=np.where(ok,q/np.maximum(vs*ALPHA[component(m)],1e-12),0)
        if m['grup']=='sony_B':
            dist=np.hypot(XX+X0-5367,YY+Y0-3545);t=np.clip((dist-140)/40,0,1);w*=t*t*(3-2*t)
        num+=np.nan_to_num(g)*w;den+=w;vn+=np.nan_to_num(v)*w*w;n+=(w>0)
        rows.append(dict(stem=m['stem'],weight_inner=float(w[R<.7*RL].sum()),weight_ring=float(w[(R>420)&(R<450)].sum()),weight_last=float(w[(R>449)&(R<454)].sum())))
    g=np.where(den>0,num/np.maximum(den,1e-30),np.nan).astype(np.float32)
    v=np.where(den>0,vn/np.maximum(den**2,1e-30),np.nan).astype(np.float32)
    return g,v,den.astype(np.float32),rows

def combine_epochs(data,name,sigma=4.,return_reference=False):
    # All epochs first. The reference preference responds only to excess light
    # above a low temporal quantile after matched Cartesian smoothing.
    gg=np.array([x[0] for x in data]);vv=np.array([x[1] for x in data]);ww=np.array([x[2] for x in data]);ok=ww>0
    qual=[];qvar=[];support=[]
    for g,v,w in zip(gg,vv,ww):
        a,d=ng(g,(w>0)&SURFACE,8.);b,_=ng(v,(w>0)&SURFACE,8.);qual.append(a);qvar.append(gaussian_filter(np.nan_to_num(v)*((w>0)&SURFACE),8/np.sqrt(2))/(4*np.pi*8**2*np.maximum(d,1e-12)**2));support.append(np.clip(d/np.maximum(gaussian_filter(SURFACE.astype(float),8.),1e-30),0,1)*SURFACE)
    qual=np.array(qual);qvar=np.array(qvar);support=np.array(support)
    # Quantile operates on spatial means, with a photon/read uncertainty guard.
    # Inverse uncertainty weighted temporal quantile: read-noise dominated
    # short epochs cannot determine the clean baseline of good long data.
    qp=np.where(ok&np.isfinite(qual),support**4/np.maximum(qvar+(.02*abs(qual))**2,1e-12),0.)
    # Smooth weighted quantile: no discrete epoch switch at a percentile.
    # CDF bandwidth is the declared local uncertainty including2%gauge.
    values=qual[:,SURFACE];prec=qp[:,SURFACE]
    width=np.sqrt(np.maximum(qvar[:,SURFACE],0)+(.02*abs(values))**2)
    width=np.maximum(width,1e-6)
    left=np.min(values-8*width,axis=0);right=np.max(values+8*width,axis=0)
    totalprec=np.maximum(prec.sum(0),1e-30)
    for _ in range(30):
        mid=(left+right)/2
        cdf=np.sum(prec*expit((mid[None]-values)/width),axis=0)/totalprec
        left=np.where(cdf<.2,mid,left);right=np.where(cdf>=.2,mid,right)
    low=np.zeros_like(R,dtype=float);low[SURFACE]=(left+right)/2
    # 2% gauge floor protects against measured few-percent train/epoch scaling
    # uncertainty; held-out comparisons and injection quantify consequences.
    tau=np.maximum(3*np.sqrt(np.maximum(qvar,0)),.02*np.maximum(abs(low),1))
    penalty=1/(1+(np.maximum(qual-low,0)/np.maximum(tau,1e-9))**4)
    preference=penalty*support**4
    # Extend only the temporal preference into the diagnostic exterior, then
    # combine its ACTUAL observed samples. This avoids switching instantly
    # from clean epochs inside to all epochs outside the geometric boundary.
    nearest=distance_transform_edt(~SURFACE,return_distances=False,return_indices=True)
    for k in range(len(preference)):
        preference[k][~SURFACE]=preference[k][tuple(nearest[:,~SURFACE])]
    rw=ww*preference
    dr=rw.sum(0);ref=np.sum(np.nan_to_num(gg)*rw,axis=0)/np.maximum(dr,1e-30)
    ref[dr==0]=np.nan
    if return_reference:return ref
    # Differential correction preserves any common additive lunar signal.
    num=np.zeros_like(R,dtype=float);den=num.copy();corrs=[]
    for g,w in zip(gg,ww):
        common=np.isfinite(g)&np.isfinite(ref)&(w>0)&SURFACE
        delta,sup=ng(g-ref,common,sigma)
        fraction=np.clip(sup/np.maximum(gaussian_filter(SURFACE.astype(float),sigma),1e-30),0,1)
        wc=np.where(common,w*fraction**4,0.)
        corrected=g-delta
        num+=np.nan_to_num(corrected)*wc;den+=wc;corrs.append(delta.astype(np.float32))
    out=num/np.maximum(den,1e-30);missing=den==0;out[missing]=ref[missing]
    allg=np.sum(np.nan_to_num(gg)*ww,axis=0)/np.maximum(ww.sum(0),1e-30)
    out[~SURFACE]=allg[~SURFACE]
    for key,a in [('reference',ref),('corrected',out),('all',allg),('ref_weight',dr),('weight',den),('epoch_ref_weights',rw),('epoch_corrections',np.array(corrs)),('quality_low',low),('epoch_preference',preference)]:
        np.save(CAU45/f'{name}_{key}.npy',a.astype(np.float32))
    return dict(epochs=len(data),reference_status='CANDIDATE convex observed data',differential_status='REJECTED negative/overshoot diagnostic',reference_missing=int((~np.isfinite(ref)&SURFACE).sum()),reference_nonpositive=int(((ref<=0)&SURFACE).sum()),reference_median_G=float(np.nanmedian(ref[R<.7*RL])),differential_nonpositive=int(((out<=0)&SURFACE).sum()),method='smooth logisticCDF inverseuncertaintyweighted20th percentile of8pxCartesian means, continuousrelativecoveragepower4, softexcessweighting2%gaugefloor; native conditional inversevariance; common signal differentialGaussian sigma'+str(sigma),epoch_reference_fraction_lila=[float(w[np.load(CAU45/'lila_mask.npy')].sum()/max(dr[np.load(CAU45/'lila_mask.npy')].sum(),1e-30)) for w in rw])

def main():
    claim45();fr=json.loads((REB45/'B1_inputs.json').read_text())['frames']
    assert all(m['native'].get('no_brightness_floor') for m in fr)
    groups={}
    for m in fr:groups.setdefault(epoch(m),[]).append(m)
    data={};report={'gains':GAIN,'weight_alpha':ALPHA,'weight_calibration':'effective8–64px P-cross-train signal, one scalar per component, fixed inner aperture; not independent or full covariance weights','epochs':{},'groups':{},'B1_inputs_sha256':sha(REB45/'B1_inputs.json'),'variance_limit':'conditional photon/read only; Sony covariance and calibration systematic not represented'}
    for name,ms in groups.items():
        epfile=CAU45/f'epoch_{name}.npz'
        if '--reuse-epochs' in sys.argv and epfile.exists():
            ep=np.load(epfile);g=ep['g'];v=ep['variance'];w=ep['weight'];rows=json.loads((REB45/'F2_temporal.json').read_text())['epochs'][name]['weights']
        else:
            g,v,w,rows=stack(ms);np.savez_compressed(epfile,g=g,variance=v,weight=w)
        data[name]=(g,v,w);report['epochs'][name]=dict(epoch_sha256=sha(epfile),B1_inputs_sha256=sha(REB45/'B1_inputs.json'),frames=[m['stem'] for m in ms],times=[m['t_mid_C2'] for m in ms],weights=rows)
        print('EPOCH',name,flush=True)
    for name,pred in [('vixen',lambda k:k.startswith('vixen')),('sony',lambda k:k.startswith('sony')),('combined',lambda k:True)]:
        ks=[k for k in data if pred(k)];report['groups'][name]=combine_epochs([data[k] for k in ks],name);report['groups'][name]['keys']=ks
        print(name,report['groups'][name],flush=True)
    savejson(REB45/'F2_temporal.json',report)
if __name__=='__main__':main()
