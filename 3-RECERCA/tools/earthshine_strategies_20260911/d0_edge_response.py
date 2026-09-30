"""Measure exposure-dependent edge response after coronal registration.
Forward profile fit only. No deconvolution, halo subtraction or PSB output.
Fit widths on non-top sectors, reserve top sector as an external spatial test.
"""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'research/tools/v45_earthshine_20260910'))
from b1_native import *
from scipy.optimize import least_squares
from scipy.special import ndtr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
OUT=ROOT/'output/earthshine_strategies_20260911'
assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_EARTHSHINE_STRATEGIES_20260911'
shifts=json.loads((OUT/'C0_early_geometry.json').read_text())['source_shifts']
theta=np.arange(0,360,1.);dist=np.arange(-35,26,.5);edge=np.load(CAU44/'vixen_optical_edge.npy')
rad=np.interp(theta*4,np.arange(len(edge)),edge)
rr=rad[None]+dist[:,None];ang=np.deg2rad(theta)[None]
xx=(X0+CXT+rr*np.cos(ang)).astype(np.float32);yy=(Y0+CYT+rr*np.sin(ang)).astype(np.float32)
ctx=f2.Ctx(comu.Run.obre(str(RUNS['vixen'])));pos=json.loads((RUNS['vixen']/'4-rebuts/F1.3_registre.json').read_text())['fotogrames'];kq=json.loads((RUNS['vixen']/'4-rebuts/F2.2_coherencia.json').read_text())['k']
meta=json.loads((CAU36/'vixen_meta.json').read_text())['frames'];phis=np.load(CAU36/'vixen_G_phi.npy',mmap_mode='r');fcorr,frep=B.flat_ripple_correction(ctx,'vixen');inv=cv2.invertAffineTransform(COMMON_TO_FINAL)
qmx=inv[0,0]*MC[0]+inv[0,1]*MC[1]+inv[0,2];qmy=inv[1,0]*MC[0]+inv[1,1]*MC[1]+inv[1,2];dmx=(qmx-ctx.CX)*ctx.k;dmy=(qmy-ctx.CY)*ctx.k
observed={};valids={}
for n in [2976,2977,2978]:
    nom=f'572A{n}.CR3';v=pos[nom];j=next(j for j,m in enumerate(meta) if m['name']==nom);m=meta[j];sx,sy=shifts[str(n)];xm=xx-sx;ym=yy-sy
    qx=inv[0,0]*xm+inv[0,1]*ym+inv[0,2];qy=inv[1,0]*xm+inv[1,1]*ym+inv[1,2];dx=(qx-ctx.CX)*ctx.k;dy=(qy-ctx.CY)*ctx.k
    rx=(ctx.ca*dx+ctx.sa*dy+v['sol_x']+v['lluna_dx']-(ctx.ca*dmx+ctx.sa*dmy)).astype(np.float32)
    ry=(-ctx.sa*dx+ctx.ca*dy+v['sol_y']+v['lluna_dy']-(-ctx.sa*dmx+ctx.ca*dmy)).astype(np.float32)
    with rawpy.imread(ctx.ruta[nom]) as rf:raw=rf.raw_image.astype(np.float32)
    dark=ctx.dark(v['exp']);phi_full=B.upsample(phis[j]);field=np.exp(-cv2.remap(phi_full,xm,ym,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE));del phi_full
    total=np.zeros_like(xx);valid=np.ones_like(xx,dtype=bool)
    for i in range(4):
        if comu.IDX_CANAL[i]!=1:continue
        oy,ox=ctx.orig[i];rp=raw[oy::2,ox::2];pl=comu.calibra_pla(rp,dark[oy::2,ox::2],ctx.flat[oy::2,ox::2],v['exp'],ctx.wb,ctx.mc,i)
        if fcorr is not None:pl*=fcorr[i]
        mx=((rx-ox)*.5).astype(np.float32);my=((ry-oy)*.5).astype(np.float32);ix=np.floor(mx).astype(int);iy=np.floor(my).astype(int)
        rn=(rp-ctx.cfg['pedestal_dn'])/(ctx.cfg['saturacio_dn']-ctx.cfg['pedestal_dn'])
        valid&=np.maximum.reduce([rn[iy,ix],rn[iy+1,ix],rn[iy,ix+1],rn[iy+1,ix+1]])<.85
        total+=(cv2.remap(pl*kq.get(nom,1),mx,my,cv2.INTER_LINEAR)+m['offset_RGB'][1])*field/2
    observed[n]=total;valids[n]=valid;print('profile',n,flush=True)
np.savez_compressed(OUT/'D0_observed_profiles.npz',theta=theta,distance=dist,**{f'g{n}':g for n,g in observed.items()},**{f'valid{n}':v for n,v in valids.items()})

# Models are deliberately simple and diagnostic: an edge response can include
# PSF, exposure integration, illumination evolution and residual registration.
# Its fitted width is not automatically the optical PSF.
profiles={};models={};rows=[]
sectors=list(range(0,360,30))
for deg in sectors:
    angular=abs((theta-deg+180)%360-180)<=4
    for n in observed:
        vals=np.where(valids[n][:,angular],observed[n][:,angular],np.nan)
        with np.errstate(all='ignore'):prof=np.nanmedian(vals,axis=1)
        coverage=np.isfinite(vals).mean(1);profiles[n,deg]=prof
        bg=np.nanmedian(prof[(dist>=-35)&(dist<=-25)])
        if n==2976:
            use=np.isfinite(prof)&(coverage>=.8)&(dist>-20)&(dist<20)
            # Core + modest broad component; free centre belongs only to the
            # unsaturated reference. Long profiles must use that same centre.
            def pred(p):
                A,c,s,k,eps=p;t=dist-c
                return bg+A*np.exp(np.clip(-k*t,-3,3))*((1-eps)*ndtr(t/s)+eps*ndtr(t/10))
            def fun(p):return (np.log(np.maximum(pred(p)[use]-bg+500,1))-np.log(np.maximum(prof[use]-bg+500,1)))
            p0=[max(float(np.nanmedian(prof[dist>10])-bg),1000),0,2,.02,.02]
            f=least_squares(fun,p0,bounds=([100,-5,.5,-.1,0],[5e6,5,8,.1,.3]),loss='soft_l1',f_scale=.1)
            models[deg]=dict(A=f.x[0],center=f.x[1],sigma=f.x[2],slope=f.x[3],wing=f.x[4]);p=f.x;sigma=float(p[2]);eps=float(p[4]);gain=1.
            prediction=pred(p);err=float(np.sqrt(np.mean(fun(p)**2)))
        else:
            ref=models[deg];A,c,k=ref['A'],ref['center'],ref['slope'];use=np.isfinite(prof)&(coverage>=.8)&(dist>-20)&(dist<12)
            def pred(p):
                s,eps,gain=p;t=dist-c
                return bg+gain*A*np.exp(np.clip(-k*t,-3,3))*((1-eps)*ndtr(t/s)+eps*ndtr(t/10))
            def fun(p):return np.log(np.maximum(pred(p)[use]-bg+500,1))-np.log(np.maximum(prof[use]-bg+500,1))
            f=least_squares(fun,[ref['sigma'],ref['wing'],1.],bounds=([.5,0,.8],[8,.3,1.2]),loss='soft_l1',f_scale=.1)
            sigma,eps,gain=map(float,f.x);prediction=pred(f.x);err=float(np.sqrt(np.mean(fun(f.x)**2)))
        rows.append(dict(frame=n,sector=deg,background=float(bg),sigma=sigma,wing=eps,gain=gain,log_rms=err,valid_points=int(use.sum()),is_top_holdout=deg==270))
        profiles[f'prediction{n}',deg]=prediction
# A held-out top-sector prediction uses only the non-top median response
# change relative to the reference, and the top reference's own geometry.
train=[deg for deg in sectors if deg not in [240,270,300]]
test=[]
for n in [2977,2978]:
    ref=models[270];base={d:next(x for x in rows if x['frame']==2976 and x['sector']==d) for d in train}
    long={d:next(x for x in rows if x['frame']==n and x['sector']==d) for d in train}
    delta=float(np.median([long[d]['sigma']-base[d]['sigma'] for d in train]));eps=float(np.median([long[d]['wing'] for d in train]));gain=float(np.median([long[d]['gain'] for d in train]))
    sig=max(.5,ref['sigma']+delta);t=dist-ref['center'];bg=next(x['background'] for x in rows if x['frame']==n and x['sector']==270)
    def forward(s,e):return bg+gain*ref['A']*np.exp(np.clip(-ref['slope']*t,-3,3))*((1-e)*ndtr(t/s)+e*ndtr(t/10))
    a=forward(ref['sigma'],ref['wing']);b=forward(sig,eps);obs=profiles[n,270];m=np.isfinite(obs)&(dist>-15)&(dist<0)
    error=lambda v:float(np.sqrt(np.mean((np.log(np.maximum(v[m]-bg+500,1))-np.log(np.maximum(obs[m]-bg+500,1)))**2)))
    test.append(dict(frame=n,training_sectors=train,sigma_delta=delta,predicted_sigma=sig,common_response_log_rms=error(a),heldout_response_log_rms=error(b),ratio=error(b)/error(a)))
    profiles[f'heldout{n}',270]=b
rep=dict(method='Descriptive core+wing edge response after independent solar geometry; no PSF correction applied',rows=rows,heldout_top=test,
  claim='Can differing edge responses explain the remaining exposure mismatch?',
  limits=['A fitted edge response is not a uniquely identified optical PSF','Top data excluded from response-difference fit','Lunar texture recovery is not validated','No absolute halo subtraction or image product'])
(OUT/'D0_edge_response.json').write_text(json.dumps(rep,indent=2));print(json.dumps(test,indent=2),flush=True)
fig,ax=plt.subplots(figsize=(11,6),layout='constrained')
for n in [2976,2977,2978]:ax.plot(dist,profiles[n,270],label=f'{n}: observat, registre coronal')
for n in [2977,2978]:ax.plot(dist,profiles[f'heldout{n}',270],ls='--',label=f'{n}: predicció des d’altres sectors')
ax.set(yscale='log',ylim=(500,150000),xlim=(-20,15),xlabel='Distància al contorn observat (px; negatiu = interior)',ylabel='G lineal',title='Resposta del llimb: prova reservada al sector superior');ax.legend(fontsize=9);ax.grid(alpha=.25)
fig.savefig(OUT/'vistes/D0_response_holdout.png',dpi=150);plt.close(fig)
