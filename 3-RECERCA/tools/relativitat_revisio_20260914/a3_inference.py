"""All results are diagnostic fits or conditional forecasts, never a GR detection."""
from a1_inputs import *
from scipy.linalg import block_diag

SCALE={'Sony':3.2020,'Vixen':2.1495}
SUN={'Sony':np.array([3894.7,2768.7]),'Vixen':np.array([3570.8,2267.1])}
RMS={'Sony':.71,'Vixen':.42}
RS=946.6598131719767
ALPHA=1.7511903255599846

def nuisance(p,kind='affine'):
    x,y=p.T/5000;one=np.ones_like(x);basis=np.c_[one,x,y]
    if kind=='quadratic':basis=np.c_[basis,x*x,x*y,y*y]
    n=len(p);A=np.zeros((2*n,basis.shape[1]*2));A[::2,:basis.shape[1]]=basis;A[1::2,basis.shape[1]:]=basis
    if kind=='similarity':
        A=np.zeros((2*n,4));A[::2,0]=1;A[1::2,1]=1;A[::2,2]=-y;A[1::2,2]=x;A[::2,3]=x;A[1::2,3]=y
    if kind=='radial':
        # Four nuisance coefficients used by the historical radial plate.
        extra=np.c_[x*(x*x+y*y),y*(x*x+y*y)]
        E=np.zeros((2*n,4));E[::2,:2]=extra;E[1::2,2:]=extra;A=np.c_[A,E]
    return A

def forecast(p,sigma,kind='similarity',alpha=ALPHA):
    r=np.linalg.norm(p,axis=1);g=(alpha*RS*p/r[:,None]**2).ravel();A=nuisance(p,kind)
    w=np.repeat(1/np.broadcast_to(sigma,len(p)),2);a=A*w[:,None];q=np.linalg.lstsq(a,g*w,rcond=None)[0];gp=g*w-a@q;I=gp@gp
    return dict(n=len(p),sigma_epsilon=float(1/np.sqrt(I)),information=float(I),retained_information_fraction=float(I/np.sum((g*w)**2)))

def frame_part(a,kind,weight='equal',floor=.1):
    n=len(a)
    if n<max(7,{'affine':5,'radial':7,'quadratic':8}[kind]):return None
    p=a[['x0','y0']].to_numpy();xy=a[['x','y']].to_numpy();sc=SCALE[a.source.iloc[0]]
    C=np.linalg.lstsq(np.c_[np.ones(n),p],xy,rcond=None)[0][1:]
    g=a[['gx','gy']].to_numpy()@C*sc
    A=nuisance(p,kind);y=((xy-xy.mean(0))*sc).ravel()
    if weight=='equal':sig=np.ones(2*n)
    else:
        sig=np.sqrt(a[['cxx','cyy']].to_numpy().ravel()*sc*sc+floor*floor)
    w=1/sig;Aw=A*w[:,None];yw=y*w;gw=g.ravel()*w
    P=np.linalg.pinv(Aw);yr=yw-Aw@(P@yw);gr=gw-Aw@(P@gw)
    tg=np.c_[-g[:,1],g[:,0]].ravel()*w;tgr=tg-Aw@(P@tg)
    return dict(a=a,A=A,Aw=Aw,y=y,yw=yw,gw=gw,gr=gr,yr=yr,w=w,g=g,tgr=tgr,npar=A.shape[1],I=float(gr@gr),b=float(gr@yr),scale=sc)

def combine(parts,label,details=False):
    if not parts:return None
    I=sum(p['I'] for p in parts);epsilon=sum(p['b'] for p in parts)/I
    allr=np.concatenate([p['yr']-epsilon*p['gr'] for p in parts]);dof=sum(2*len(p['a'])-p['npar'] for p in parts)-1
    se=1/np.sqrt(I);sigma_emp=se*np.sqrt(allr@allr/dof)
    # Cluster sandwich by star, combining scores across repeated frames and both cameras.
    scores={}
    for p in parts:
        resid=p['yr']-epsilon*p['gr'];s=(p['gr']*resid).reshape(-1,2).sum(1)
        for tyc,v in zip(p['a'].TYC,s):scores[tyc]=scores.get(tyc,0.)+float(v)
    G=len(scores);N=len(allr);K=N-dof
    correction=G/(G-1)*(N-1)/dof if G>1 else np.nan
    cluster=np.sqrt(sum(s*s for s in scores.values())*correction)/I
    tI=sum(p['tgr']@p['tgr'] for p in parts);tval=sum(p['tgr']@p['yr'] for p in parts)/tI
    out=dict(label=label,epsilon=float(epsilon),sigma_unit=float(se),sigma_residual=float(sigma_emp),sigma_cluster_star=float(cluster),dof=dof,nframes=len(parts),nobs=N//2,nstars=G,tangential_amplitude=float(tval),residual_rms_arcsec=float(np.sqrt(np.mean(np.concatenate([(p['yr']-epsilon*p['gr'])/p['w'] for p in parts])**2))),information=float(I),qualification='EXPLORATORY; legacy catalogue, catalogue-guided sample, fixed PSF, uncalibrated shared systematic errors; not a physical GR estimate.')
    if details:
        out['frame_results']=[dict(frame=p['a'].frame.iloc[0],n=len(p['a']),epsilon=p['b']/p['I'],conditional_sigma=1/np.sqrt(p['I'])) for p in parts]
    return out

def main():
    df=pd.read_csv(O/'A1_native_centroids.csv').merge(pd.read_csv(O/'A2_no_sun_and_GR.csv'),on=['frame','TYC'],validate='one_to_one')
    # Secondary weak-source sensitivity declared before examining epsilon.
    for threshold in [5,10,20]:
        valid=df.refined&(df.SNR>=threshold)&~df.blended
        cnt=df[valid].groupby(['source','TYC']).size()
        df[f'use{threshold}']=valid&np.array([cnt.get((r.source,r.TYC),0)>=2 for r in df.itertuples()])
    df.to_csv(O/'A3_analysis_sample.csv',index=False)
    oldrep={};geometry=[]
    for tag,short in [('Sony','sony'),('Vixen','r6')]:
        for sample,path in [('old_identified',W/f'xmatch/final_match_{short}.csv'),('old_literal',W.parent/f'estrelles_{short}.csv')]:
            old=pd.read_csv(path);p=(old[['x','y']].to_numpy()-SUN[tag])*SCALE[tag]
            for kind in ['similarity','affine','radial']:
                q=forecast(p,RMS[tag]/np.sqrt(2)*SCALE[tag],kind,alpha=1.751641075710372);geometry.append(dict(source=tag,sample=sample,kind=kind,**q))
        for sample,sel in [('V65_eligible10',df[(df.source==tag)&df.use10]),('V65_eligible5',df[(df.source==tag)&df.use5]),('all_target_positions_counterfactual',df[(df.source==tag)&~df.blended])]:
            a=sel.drop_duplicates('TYC');p=a[['x0','y0']].to_numpy()
            for kind in ['similarity','affine','radial']:geometry.append(dict(source=tag,sample=sample,kind=kind,**forecast(p,RMS[tag]/np.sqrt(2)*SCALE[tag],kind)))
    for sample in sorted({q['sample'] for q in geometry}):
        for kind in ['similarity','affine','radial']:
            sub=[q for q in geometry if q['sample']==sample and q['kind']==kind];I=sum(q['information'] for q in sub);geometry.append(dict(source='combined_conditional',sample=sample,kind=kind,n=sum(q['n'] for q in sub),sigma_epsilon=1/np.sqrt(I),information=I))
    pd.DataFrame(geometry).to_csv(O/'A3_geometry_forecasts.csv',index=False)
    results=[]
    for threshold in [5,10,20]:
      for sample in ['old','expanded']:
       a=df[df[f'use{threshold}'] & ((df.old) if sample=='old' else True)]
       for kind in ['affine','radial','quadratic']:
        for weight in ['equal','proxy']:
         parts=[frame_part(x,kind,weight) for _,x in a.groupby('frame')];parts=[p for p in parts if p is not None]
         for tag in ['Sony','Vixen','combined']:
          use=parts if tag=='combined' else [p for p in parts if p['a'].source.iloc[0]==tag]
          q=combine(use,f'SNR{threshold}/{sample}/{kind}/{weight}/{tag}',details=True)
          if q:results.append(q)
    dump('A3_diagnostic_fits.json',results)
    selected=df[df.use10];checks=[]
    for kind in ['affine','radial','quadratic']:
      parts=[frame_part(a,kind,'equal') for _,a in selected.groupby('frame')];parts=[p for p in parts if p is not None]
      if not parts:continue
      baseline=combine(parts,'baseline')
      jack=[]
      for tyc in sorted(selected.TYC.unique()):
        leave=[frame_part(a[a.TYC!=tyc],kind,'equal') for _,a in selected.groupby('frame')];leave=[p for p in leave if p is not None];q=combine(leave,tyc)
        if q:jack.append(dict(TYC=tyc,epsilon=q['epsilon'],nobs=q['nobs']))
      # Conditional coordinate injections validate projection; no image or PSF is regenerated.
      injection=[]
      for eps in [0,.5,1]:
        observed=[]
        for p in parts:
          y=p['Aw']@np.arange(p['npar'])*.01+eps*p['gw'];yr=y-p['Aw']@(np.linalg.pinv(p['Aw'])@y);observed.append(float(p['gr']@yr))
        fitted=sum(observed)/sum(p['I'] for p in parts);injection.append(dict(injected=eps,recovered=fitted,error=fitted-eps))
      checks.append(dict(kind=kind,baseline=baseline,jackknife=jack,coordinate_injections=injection))
      assert max(abs(x['error']) for x in injection)<1e-8
    dump('A3_controls.json',checks)
    print('FORECASTS',json.dumps([q for q in geometry if q['source']=='combined_conditional']))
    print('DIAGNOSTICS',json.dumps([{k:v for k,v in q.items() if k not in ['frame_results','qualification']} for q in results if q['label'].startswith('SNR10/expanded') and '/equal/' in q['label']]))
if __name__=='__main__':main()
