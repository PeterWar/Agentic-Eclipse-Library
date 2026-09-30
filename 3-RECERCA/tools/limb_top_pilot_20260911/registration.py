"""Independent-train registration check, fixed interior aperture and band.

Does not fit the bright limb or a temporal halo. No offset is applied.
The small diagnostic coadd uses five existing Vixen short-frame caches.
"""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'research/tools/v45_earthshine_20260910'))
from f2_temporal import *
sys.path.insert(0,str(ROOT/'research/tools/v44_earthshine_20260910'))
from a2_registre import preprocess,ncc
from scipy.ndimage import shift
OUT=ROOT/'output/limb_top_pilot_20260911'
assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_LIMB_TOP_PILOT_20260911'
fr=json.loads((REB45/'B1_inputs.json').read_text())['frames']
selected=[m for m in fr if epoch(m)=='vixen_2' and m['exp']<1]
num=np.zeros_like(R,dtype=float);den=num.copy()
for m in selected:
    d=np.load(m['native']['file']);g=d['g'];q=d['q'];v=d['variance'];ok=np.isfinite(g)&np.isfinite(v)&(v>0)&(q>0)
    vs,_=ng(v,ok,4);w=np.where(ok,q/np.maximum(vs*ALPHA[component(m)],1e-12),0)
    num+=np.nan_to_num(g)*w;den+=w
short=np.where(den>0,num/np.maximum(den,1e-30),np.nan)
long=np.load(CAU45/'native_vixen_572A2978.npz')['g']
images={'short_coadd':short,'long_2978':long}
refs={s:np.load(CAU45/f'native_sony_{s}.npz')['g'] for s in ['DSC06984','DSC06987']}
z={k:preprocess(g) for k,g in {**images,**refs}.items()}
ap=R<.7*RL;alt=(np.floor((PHI%(2*np.pi))/(np.pi/4)).astype(int)%2)==0
rows=[]
for key in images:
    for ref in refs:
        d=ncc(z[key],z[ref],ap,rg=6)
        halves=[ncc(z[key],z[ref],ap&a,rg=6) for a in [alt,~alt]]
        gap=float(np.hypot(halves[0]['dx']-halves[1]['dx'],halves[0]['dy']-halves[1]['dy']))
        rows.append(dict(image=key,reference=ref,result=d,halves=halves,half_gap=gap,
          gate_pass=bool(d['r']>=.3 and not d['boundary'] and gap<=.5)))
        print(key,ref,d,'half_gap',gap,flush=True)
# A known translation tests estimator equivariance only, never its science.
imposed=(3.,-2.)
shifted=shift(short,(imposed[1],imposed[0]),order=1,cval=np.nan,prefilter=False)
a=rows[0]['result'];b=ncc(preprocess(shifted),z['DSC06984'],ap,rg=6)
err=float(np.hypot(b['dx']-a['dx']+imposed[0],b['dy']-a['dy']+imposed[1]))
report=dict(method='Existing fixed log DoG6–24; target aperture r<0.70R applied only at NCC evaluation; independent sensor references 2s and 8s; alternating angular halves',
    excluded='No limb/halo fitting. Reference mask not multiplied into input before filtering.',
    short_frames=[m['stem'] for m in selected],rows=rows,
    declared_gate=dict(ncc_min=.3,half_gap_max_px=.5,known_translation_error_max_px=.1),
    translation_control=dict(imposed=list(imposed),recovered=[b['dx']-a['dx'],b['dy']-a['dy']],error=err,pass_equivariance=err<.1),
    physical_registration_validated=all(row['gate_pass'] for row in rows) and err<.1,
    scope='Interior reused only to validate geometry for the upper-sector pilot. No global image product.')
(OUT/'A1_registration.json').write_text(json.dumps(report,indent=2));print('Registration validated',report['physical_registration_validated'],flush=True)
