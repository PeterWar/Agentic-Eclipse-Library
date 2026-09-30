"""New order-of-operations counterfactual: estimate/remove glare in source G.
Same S8 estimator and geometry, upstream of all display curves. A frozen global
response estimates historical baked tone; its uncertainty is reported. This is
not an independently calibrated optical PSF and cannot itself validate albedo.
"""
from a1_trace import *
import importlib.util
from scipy.interpolate import PchipInterpolator
spec=importlib.util.spec_from_file_location('s8_pure',ROOT/'research/tools/earthshine_broad_lroc_20260914/s8_operator.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

def curve(g,p):
    fit=(R>30)&(R<454)&~GUARD&(SECTOR%2==0)&np.isfinite(g)&np.isfinite(p)
    edges=np.unique(np.quantile(g[fit],np.linspace(0,1,513)))
    xx=[];yy=[];ww=[]
    for lo,hi in zip(edges[:-1],edges[1:]):
        m=fit&(g>=lo)&(g<hi)
        if m.sum()<20:continue
        xx.append(float(np.median(g[m])));yy.append(float(np.median(p[m])));ww.append(int(m.sum()))
    yy=isotonic_regression(yy,weights=ww).x
    f=PchipInterpolator(xx,yy,extrapolate=False)
    # Extrapolation never qualifies for production. Interior gate records it.
    def apply(a):return f(np.clip(a,xx[0],xx[-1]))
    return apply,dict(x=xx,y=yy.tolist(),fit_region='r30-454 alternating sectors, excluded mark+guard',extrapolation='clamped for diagnostic; any visible extrapolation fails promotion')

def main():
    g=np.load(ROOT/'research/tools/v45_earthshine_20260910/cau/combined_reference.npy').astype(float)
    p=np.load(ROOT/'research/tools/earthshine_v50_temporal_20260912/cau/lun_ch1_roi.npy').astype(float)
    old=np.load(ROOT/'output/v68_artefactes_20260914/arrays/B10_photo_pilot.npz')['candidate'].astype(float)
    edge=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy')
    old_s8,wp=mod.s8_eval(p,edge)
    stored=np.load(ROOT/'research/tools/earthshine_v50_temporal_20260912/cau/lun_rgb_vel_u16.npy')[...,1]
    assert np.max(abs(np.rint(old_s8)-stored))<=1
    fg,c=curve(g,p);clean,wg=mod.s8_eval(g,edge)
    subtraction=fg(g)-fg(clean)
    delta=wp-subtraction
    candidate=old+delta[...,None]
    support=R<454
    out=(clean<c['x'][0])|(clean>c['x'][-1])|(g<c['x'][0])|(g>c['x'][-1])
    report=dict(method=__doc__,display_curve=c,baseline_replay_max_DN16=float(np.max(abs(np.rint(old_s8)-stored))),curve_held_error_DN16=q(p-fg(g),HELD),curve_mark_error_DN16=q(p-fg(g),MARK),delta_mark_DN16=q(delta,MARK),delta_limb_DN16=q(delta,(R>435)&(R<454)),visible_extrapolated=int((out&support).sum()),visible_out_of_range=int(((candidate.min(-1)<0)|(candidate.max(-1)>65535))[support].sum()),same_source_geometry=True,no_new_mask=True)
    np.savez_compressed(OUT/'arrays/A3_linear_order_NOT_APPROVED.npz',candidate=candidate.astype('float32'),delta=delta.astype('float32'),raw_glare=wg.astype('float32'),raw_clean=clean.astype('float32'))
    save('A3_linear_order.json',report);print(json.dumps({k:v for k,v in report.items() if k!='display_curve'},indent=2),flush=True)
    # Signed structures, all source/background terms refitted. Photographic
    # source->baked-input injection remains conditional on the frozen response.
    rows=[]
    for x,y,sigma in [(636,975,50),(636,975,90),(1000,680,50),(500,440,50)]:
        blob=np.exp(-((XX-x)**2+(YY-y)**2)/(2*sigma*sigma));m=blob>.1
        for sign in [-1,1]:
            injection=sign*2*blob
            gi=g+injection;pi=p+fg(gi)-fg(g)
            fi,_=curve(gi,pi);ci,_=mod.s8_eval(gi,edge)
            result=pi-(fi(gi)-fi(ci))
            base_result=p-subtraction
            ideal=fg(clean+injection)-fg(clean)
            observed=result-base_result
            gain=float(np.sum(observed[m]*ideal[m])/np.sum(ideal[m]**2))
            leakage=float(np.sqrt(np.mean((observed[m]-ideal[m])**2))/np.sqrt(np.mean(ideal[m]**2)))
            row=dict(center=[x,y],sigma=sigma,amplitude_sourceDN=sign*2,gain=gain,relative_error=leakage,passes=.9<=gain<=1.1)
            rows.append(row);print('INJECTION',row,flush=True)
    save('A3_linear_injections.json',dict(rows=rows,passes=sum(q['passes'] for q in rows),total=len(rows),scope='Whole source estimator and global response refit; conditional source-to-baked-input injection, not RAW sensor end-to-end.',status='NO_PROMOTION_UNLESS_ALL_GATES_PASS'))

if __name__=='__main__':main()
