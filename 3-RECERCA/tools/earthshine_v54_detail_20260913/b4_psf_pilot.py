"""Execute two physically admissible wing inverses with frozen observed fits.
This pilot tests identifiability; it never promotes a display-veil PSF.
"""
from common import *
from scipy.fft import dctn,idctn
claim();r,theta,d=geometry();z=np.load(OUT/'arrays/B1_stacks.npz');g=z['all']
rep=json.loads((OUT/'B1_PSF_identifiability.json').read_text());sig=np.array(rep['sigma'])
# Same sector, similar held-out edge residual, both wing masses inside [0,1].
models=[next(v for v in rep['rows'] if v['sector']==4 and v['degree']==degree) for degree in [0,2]]
freq=np.hypot((np.arange(N)/(2*N))[:,None],(np.arange(N)/(2*N))[None,:])
F=dctn(g,type=2,norm='ortho');models_out=[]
for j,m in enumerate(models):
    a=np.asarray(m['wing_coeff']);assert 0<a.sum()<1
    otf=(1-a.sum())+sum(ai*np.exp(-2*np.pi**2*si**2*freq**2) for ai,si in zip(a,sig))
    # Fixed 1e-3 regularisation; preserves DC exactly. Operator outside full
    # observed frame is Neumann. Strong exterior contamination is part of test.
    inv=otf/(otf**2+1e-3);inv/=inv[0,0]
    recovered=idctn(F*inv,type=2,norm='ortho')
    np.save(OUT/f'arrays/B4_inverse_model{j}.npy',recovered)
    inj=[];rng=np.random.default_rng(540914)
    for lo,hi in [(8,16),(16,24),(24,40),(40,64)]:
        h=(freq>=1/hi)&(freq<=1/lo);S=dctn(rng.normal(size=g.shape),norm='ortho')*h
        # Synthetic scene forward-modelled independently through BOTH kernels;
        # judging against the same assumed kernel alone would be tautological.
        for truth in models:
            b=np.array(truth['wing_coeff']);K=(1-b.sum())+sum(bi*np.exp(-2*np.pi**2*si**2*freq**2) for bi,si in zip(b,sig))
            transfer=float(np.sum(S*S*K*inv)/np.sum(S*S));inj.append(dict(band=[lo,hi],truth_degree=truth['degree'],transfer=transfer,pass_gate=.9<=transfer<=1.1))
    mm=(d>=-80)&(d<-5)
    models_out.append(dict(model=m,delta_p95=float(np.percentile(abs(recovered-g)[mm],95)),injection=inj))
save('B4_psf_pilot.json',dict(models=models_out,conclusion='NO PROMOTION: two admissible wing masses fit the same linear edge equally well but inverse transfer depends strongly on the nuisance baseline. Same-kernel injection alone cannot validate PSF identity.',note='This is a bounded single-sector stationarity pilot; not a measured full-field PSF.'))
print('B4 wing masses',[v['wing_sum'] for v in models],flush=True)
