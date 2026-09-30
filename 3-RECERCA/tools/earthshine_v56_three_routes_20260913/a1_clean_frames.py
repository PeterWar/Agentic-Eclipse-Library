"""Read existing calibrated sources, subtract exactly the qualified V55 detector.
Per-frame sources remain calibrated ordinary G; no new photometric fit or PSF.
Original photon weights reproduce B11 baseline; covariance only trained D.
"""
from common import *
from scipy.ndimage import gaussian_filter,gaussian_filter1d
claim();fs=[q for q in frames() if q['tren']=='vixen'];names=[q['stem'] for q in fs];design=json.loads((OLD/'B3_G67_robust_hetero_full_safe_design.json').read_text());assert names==design['names'];sh=np.array(design['shifts']);z=np.load(OLD/'arrays/B11_repeatable_all.npz');D=z['detector'];r,t=geometry();edge=gaussian_filter1d(np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy'),3,mode='wrap');physical=r<np.interp(t,np.linspace(0,2*np.pi,len(edge),endpoint=False),edge,period=2*np.pi)
for n in ['G_frames.npy','W_frames.npy']:assert not (OUT/'arrays'/n).exists()
G=np.lib.format.open_memmap(OUT/'arrays/G_frames.npy',mode='w+',dtype=np.float32,shape=(len(fs),N,N));W=np.lib.format.open_memmap(OUT/'arrays/W_frames.npy',mode='w+',dtype=np.float32,shape=G.shape);num=np.zeros((N,N));den=np.zeros((N,N));before=np.zeros((N,N));rows=[]
for i,m in enumerate(fs):
 a=np.load(m['file']);q=(a['G1_q']+a['G2_q'])/2;g=(np.nan_to_num(a['G1'])*a['G1_q']+np.nan_to_num(a['G2'])*a['G2_q'])/np.maximum(2*q,1e-30);vv=(np.nan_to_num(a['G1_var'])*a['G1_q']**2+np.nan_to_num(a['G2_var'])*a['G2_q']**2)/np.maximum((2*q)**2,1e-30);ok=np.isfinite(g)&np.isfinite(vv)&(q>0)&physical;vs=gaussian_filter(np.where(ok,vv,0),4)/np.maximum(gaussian_filter(ok.astype(float),4),1e-30);w=np.where(ok,q/np.maximum(vs,1e-12),0);dc=pull(D,sh[i]);clean=g-dc;G[i]=np.where(ok,clean,np.nan);W[i]=w;num+=w*clean;den+=w;before+=w*g;rows.append(dict(stem=m['stem'],exp=m['exp'],time=m['time_C2'],shift=sh[i],inner_valid=int(((w>0)&(r<350)).sum())))
 if (i+1)%10==0:print('PREP',i+1,len(fs),flush=True)
G.flush();W.flush();out=num/np.maximum(den,1e-30);base=before/np.maximum(den,1e-30);good=den>0;er=float(np.max(abs(out[good]-z['source'][good])));eb=float(np.max(abs(base[good]-z['raw_baseline'][good])));assert er<1e-8 and eb<1e-8,(er,eb)
np.savez_compressed(OUT/'arrays/A1_sources.npz',source=out,baseline=base,weight=den,physical=physical)
save('A1_clean_frames.json',dict(method=__doc__,frames=rows,V55_source_max_error=er,V55_baseline_max_error=eb,cache_precision='Float32 per-frame cache, float64 accumulation and reference; later cache roundoff declared',reference_sha256=sha(OLD/'arrays/B11_repeatable_all.npz')));print('SOURCE REPRODUCED',er,eb,flush=True)
