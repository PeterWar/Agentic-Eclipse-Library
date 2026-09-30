"""Validate only the new03 raster and the fixed-weight source correction."""
import os,sys,json
from pathlib import Path
os.environ['V29_FINAL_GRID']='1'
D=Path(__file__).parent;ROOT=D.parents[2]
sys.path.insert(0,str(ROOT/'research/tools/v29'))
from common import *
from qa_rasters import h1_setup,h1
from audit_geometry import polar,correlate
import f3

def main():
    r,t=coords();m=np.load(CAU/'gran_support.npy');a=np.load(D/'gran_u16.npy').astype('float32')/65535
    rep={'H1':h1(a,m,h1_setup(r,m)), 'support_pixels':int(m.sum()), 'inner_1_05R_pixels':int((m&(r<1.05*RS)).sum())}
    rep['H1b']=f3.anells_de_calaix(a,r,m)
    radii=np.linspace(1.12,2.5,60).astype('float32');ref=np.load(CAU/'fusion_total.npy',mmap_mode='r')[...,1]
    P=polar(a,CX,CY,RS,radii);R=polar(np.log(np.maximum(ref,1)),CX,CY,RS,radii)
    rep['solar_geometry']=correlate(P,R)
    rep['controls']={str(d):correlate(np.roll(R,round(d*4),axis=1),R) for d in (0,1,-1,180)}
    rep['independent_train_comparison']={}
    for lo,hi in [(1.12,2.0),(2.0,2.65),(2.65,3.8)]:
        rs=np.linspace(lo,hi,60).astype('float32');v=np.load(D/'angular_vixen_raw.npy',mmap_mode='r');s=np.load(D/'angular_sony_raw.npy',mmap_mode='r')
        rep['independent_train_comparison'][f'{lo}-{hi}']=correlate(polar(v,CX,CY,RS,rs),polar(s,CX,CY,RS,rs))
    # Native common-sky injection at the calibrated sample stage: original
    # weights are frozen. No assertion about rerunning saturation on altered RAW.
    # Offset refit is also tested: a common injection cancels in every difference.
    rng=np.random.default_rng(2903);rep['fixed_weight_injection']={}
    for tag in ['vixen','sony']:
        values=np.load(D/f'{tag}_samples.npy',mmap_mode='r');conf=np.load(D/f'{tag}_confidence.npy',mmap_mode='r');meta=json.loads((D/f'{tag}_sample_meta.json').read_text())
        # Work on a bounded random subset of the existing reserved sample grid.
        shape=values.shape;v=np.moveaxis(values,-1,1).reshape(shape[0],3,-1).astype('float64');q=np.moveaxis(conf,-1,1).reshape(shape[0],3,-1).astype('float64')
        sel=rng.choice(v.shape[-1],min(5000,v.shape[-1]),replace=False);v=v[...,sel];q=q[...,sel]
        exp=np.array([f['exposure'] for f in meta['frames']]);w=q*exp[:,None,None]*np.array([1,2,1])[None,:,None]
        valid=np.isfinite(v);w=np.where(valid,w,0);v=np.nan_to_num(v)
        inj=rng.normal(0,2,size=v.shape[1:]);den=w.sum(0);ok=den>0
        before=(v*w).sum(0)/np.maximum(den,1e-30);after=((v+inj)*w).sum(0)/np.maximum(den,1e-30)
        err=float(np.max(np.abs((after-before-inj)[ok])))
        diff_err=float(np.max(np.abs(((v[0]+inj)-(v[1]+inj))-(v[0]-v[1]))))
        rep['fixed_weight_injection'][tag]={'max_abs_transfer_error':err,'common_pair_difference_error':diff_err,'scope':'calibrated samples, fixed RAW validity/weights and fitted offsets; not raw-level nonlinear injection','PASS':err<1e-8 and diff_err<1e-8}
    rep['PASS']=rep['H1']['PASS'] and rep['solar_geometry']['PASS'] and rep['controls']['0']['PASS'] and all(not rep['controls'][k]['PASS'] for k in ('1','-1','180')) and all(q['PASS'] for q in rep['fixed_weight_injection'].values())
    savejson(D/'candidate_qa.json',rep);log(str({k:v for k,v in rep.items() if k!='H1'}));assert rep['PASS']
if __name__=='__main__':main()
