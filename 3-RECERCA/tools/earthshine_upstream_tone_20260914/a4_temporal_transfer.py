"""Exact interior-node evaluation of V45 temporal preference with refit.
Spatial means are computed over the full 1400-square source; only pointwise
CDF calculations use a frozen 8-pixel validation grid. No approximate resampling
of the estimator. Photon/read variance is frozen at the epoch-composition stage.
"""
from a1_trace import *
from scipy.special import expit

def main():
    c=ROOT/'research/tools/v45_earthshine_20260910/cau'
    j=json.loads((ROOT/'output/v45_earthshine_20260910/4-rebuts/F2_temporal.json').read_text())
    keys=j['groups']['combined']['keys']
    edge=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy')
    surface=R<np.interp((PHI%(2*np.pi))*len(edge)/(2*np.pi),np.arange(len(edge)),edge,period=len(edge))
    grid=(XX.astype(int)%8==0)&(YY.astype(int)%8==0)&(R<420)
    full_den=gaussian_filter(surface.astype(float),8.)
    data=[]
    for key in keys:
        z=np.load(c/('epoch_'+key+'.npz'));g=z['g'];v=z['variance'];w=z['weight'];valid=(w>0)&surface
        den=gaussian_filter(valid.astype(float),8.)
        qual=gaussian_filter(np.nan_to_num(g)*valid,8.)/np.maximum(den,1e-30)
        qvar=gaussian_filter(np.nan_to_num(v)*valid,8/np.sqrt(2))/(4*np.pi*8**2*np.maximum(den,1e-12)**2)
        support=np.clip(den/np.maximum(full_den,1e-30),0,1)*surface
        data.append(dict(key=key,g=g[grid],w=w[grid],qual=qual[grid],qvar=qvar[grid],support=support[grid],valid=valid,den=den))
    gg=np.array([d['g'] for d in data]);ww=np.array([d['w'] for d in data]);basequal=np.array([d['qual'] for d in data]);qvar=np.array([d['qvar'] for d in data]);support=np.array([d['support'] for d in data])
    def estimate(inj):
        if np.isscalar(inj):values=basequal;g=gg
        else:
            values=basequal+np.array([(gaussian_filter(inj*d['valid'],8.)/np.maximum(d['den'],1e-30))[grid] for d in data]);g=gg+inj[grid]
        precision=np.where((ww>0)&np.isfinite(values),support**4/np.maximum(qvar+(.02*abs(values))**2,1e-12),0)
        width=np.maximum(np.sqrt(np.maximum(qvar,0)+(.02*abs(values))**2),1e-6)
        left=np.min(values-8*width,axis=0);right=np.max(values+8*width,axis=0);total=np.maximum(precision.sum(0),1e-30)
        for _ in range(30):
            mid=(left+right)/2;cdf=np.sum(precision*expit((mid[None]-values)/width),axis=0)/total
            left=np.where(cdf<.2,mid,left);right=np.where(cdf>=.2,mid,right)
        low=(left+right)/2;tau=np.maximum(3*np.sqrt(np.maximum(qvar,0)),.02*np.maximum(abs(low),1))
        pref=support**4/(1+(np.maximum(values-low,0)/np.maximum(tau,1e-9))**4);rw=ww*pref
        return np.sum(np.nan_to_num(g)*rw,axis=0)/np.maximum(rw.sum(0),1e-30)
    baseline=estimate(0);stored=np.load(c/'combined_reference.npy')[grid];error=np.max(abs(baseline-stored))
    assert error<.0001,error
    rows=[]
    for x,y,sigma in [(636,975,50),(636,975,90),(1000,680,50),(500,440,50)]:
        blob=np.exp(-((XX-x)**2+(YY-y)**2)/(2*sigma*sigma));m=blob[grid]>.1
        for sign in [-1,1]:
            inj=sign*2*blob;delta=estimate(inj)-baseline;ideal=inj[grid]
            gain=float(delta[m]@ideal[m]/(ideal[m]@ideal[m]));relative=float(np.linalg.norm(delta[m]-ideal[m])/np.linalg.norm(ideal[m]))
            row=dict(center=[x,y],sigma=sigma,amplitude_sourceDN=sign*2,gain=gain,relative_error=relative,passes=.9<=gain<=1.1);rows.append(row);print(row,flush=True)
    save('A4_temporal_transfer.json',dict(method=__doc__,grid_nodes=int(grid.sum()),exact_replay_max_sourceDN=float(error),rows=rows,passes=sum(a['passes'] for a in rows),total=len(rows),interpretation='Tests distortion added by original temporal selection alone; cannot validate common static optical background or broad lunar albedo.'))

if __name__=='__main__':main()
