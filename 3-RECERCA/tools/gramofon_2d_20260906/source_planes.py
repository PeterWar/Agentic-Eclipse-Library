"""Relative per-frame photometry from overlap differences only; no promotion."""
from experiment import *
from scipy.optimize import least_squares

F=ROOT/'research/tools/v29_c03_fix'
def main():
    meta=json.loads((F/'sony_sample_meta.json').read_text());frames=meta['frames']
    a=np.load(F/'sony_samples.npy',mmap_mode='r')[...,1]
    confidence=np.load(F/'sony_confidence.npy',mmap_mode='r')[...,1]
    yy,xx=np.meshgrid(meta['ys'],meta['xs'],indexing='ij')
    u=(xx-5361.768111973117)/440.60304883027544
    v=(yy-3775.747534140857)/440.60304883027544
    r=np.hypot(u,v);theta=np.mod(np.arctan2(v,u),2*np.pi)
    sectors=np.floor(theta*16/(2*np.pi)).astype(int)
    phase=np.mod(theta,2*np.pi/16)
    safe=(r>1.08)&(r<4.5)&(phase>.035)&(phase<2*np.pi/16-.035)
    train=safe&(sectors%2==0);hold=safe&(sectors%2==1)
    far=(r>=4.5)&(r<8.5)
    X=np.stack([np.ones_like(u),u,v],axis=-1).astype(float)
    groups=[('sony_A',[i for i,f in enumerate(frames) if int(f['name'][3:8])<=6987],'DSC06984.ARW'),
            ('sony_B',[i for i,f in enumerate(frames) if int(f['name'][3:8])>=6991],'DSC06996.ARW')]
    reports=[]
    for group,inds,anchor_name in groups:
        anchor=next(i for i in inds if frames[i]['name']==anchor_name)
        edges=[]
        for ii,i in enumerate(inds):
            for j in inds[ii+1:]:
                ei,ej=frames[i]['exposure'],frames[j]['exposure']
                if max(ei,ej)/min(ei,ej)>8.01:continue
                good=(confidence[i]>.995)&(confidence[j]>.995)&(a[i]>0)&(a[j]>0)
                mt=good&train;mh=good&hold
                if mt.sum()<35 or mh.sum()<35:continue
                ids=np.flatnonzero(mt)
                # Deterministic evenly spaced training subsample, independent of residuals.
                ids=ids[np.linspace(0,len(ids)-1,min(400,len(ids))).astype(int)]
                ai=a[i].ravel()[ids].astype(float);aj=a[j].ravel()[ids].astype(float)
                diff=ai-aj;level=float(np.median((ai+aj)/2))
                scatter=1.4826*np.median(np.abs(diff-np.median(diff)))
                scale=max(.003*level,float(scatter),.1)
                edges.append({'i':i,'j':j,'ids':ids,'good':good,'scale':scale})
        connected={anchor}
        for _ in inds:
            for e in edges:
                if e['i'] in connected or e['j'] in connected:connected|={e['i'],e['j']}
        unknown=sorted(connected-{anchor});lookup={j:i for i,j in enumerate(unknown)}
        edges=[e for e in edges if e['i'] in connected and e['j'] in connected]
        models={};fits={}
        for degree in [1,3]:
            nobs=sum(len(e['ids']) for e in edges)
            A=np.zeros((nobs,len(unknown)*degree));target=np.empty(nobs);row=0
            for e in edges:
                i,j,ids,sc=e['i'],e['j'],e['ids'],e['scale'];nn=len(ids)
                xx=X.reshape(-1,3)[ids,:degree]/sc
                if i!=anchor:A[row:row+nn,lookup[i]*degree:(lookup[i]+1)*degree]=xx
                if j!=anchor:A[row:row+nn,lookup[j]*degree:(lookup[j]+1)*degree]=-xx
                target[row:row+nn]=-(a[i].ravel()[ids].astype(float)-a[j].ravel()[ids].astype(float))/sc
                row+=nn
            rank=int(np.linalg.matrix_rank(A));assert rank==A.shape[1]
            initial=np.linalg.lstsq(A,target,rcond=None)[0]
            fit=least_squares(lambda z:A@z-target,initial,jac=lambda z:A.copy(),
                  loss='soft_l1',f_scale=1,ftol=1e-9,xtol=1e-9,gtol=1e-9,max_nfev=100)
            coef=np.zeros((len(frames),3))
            for i in unknown:coef[i,:degree]=fit.x[lookup[i]*degree:(lookup[i]+1)*degree]
            name='constant' if degree==1 else 'plane2D'
            models[name]=coef;fits[name]={'success':bool(fit.success),'rank':rank,'parameters':A.shape[1],
                                         'observations':nobs,'cost':float(fit.cost)}
        # Compare with the exact legacy constant fit as an additional baseline.
        legacy=json.loads((F/'offset_model.json').read_text())['groups'][group]['offsets']
        oldcoef=np.zeros((len(frames),3))
        for i in inds:oldcoef[i,0]=legacy[frames[i]['name']][1]
        models['legacy_constant']=oldcoef
        evaluations=[]
        for e in edges:
            i,j=e['i'],e['j']
            for zone,m in [('heldout_1.08_4.5R',hold),('extrapolation_4.5_8.5R',far)]:
                good=e['good']&m
                if good.sum()<35:continue
                ai=a[i][good].astype(float);aj=a[j][good].astype(float);lev=(ai+aj)/2
                row={'pair':[frames[i]['name'],frames[j]['name']],'zone':zone,'n':int(good.sum()),'models':{}}
                for name,coef in models.items():
                    residual=(ai-aj+X[good]@(coef[i]-coef[j]))/lev
                    med=float(np.median(residual))
                    row['models'][name]={'median_relative':med,'RMS_relative':rms(residual),
                         'MAD_relative':float(1.4826*np.median(np.abs(residual-med)))}
                evaluations.append(row)
        report={'group':group,'anchor':anchor_name,'fits':fits,
                'unconnected':[frames[i]['name'] for i in inds if i not in connected],
                'coefficients':{name:{frames[i]['name']:coef[i].tolist() for i in inds} for name,coef in models.items()},
                'evaluation':evaluations}
        reports.append(report);log('source plane '+group+' complete')
    save('source_planes',{'groups':reports,'model':'a_i(x,y)+b_i0+b_ix*u+b_iy*v; per-frame correction, no fit of common corona',
         'gains_and_raw_weights':'frozen; same plateau masks; anchor correction zero',
         'source_sampling_px':24,'channel':'G only','train':'alternating22.5degree sectors1.08..4.5R; up to400samples per edge',
         'validation':'other angular sectors, plus4.5..8.5R extrapolation',
         'common_corona_invariance':'with frozen design/confidence, identical added structure in every frame cancels exactly from pairwise differences',
         'promotion':False,'limitations':'relative gauge, sparse sampling, no native correction or external-judge verification; shared temporal PSF/registration errors may contaminate fits'})
    log('source planes COMPLETE')

if __name__=='__main__':main()
