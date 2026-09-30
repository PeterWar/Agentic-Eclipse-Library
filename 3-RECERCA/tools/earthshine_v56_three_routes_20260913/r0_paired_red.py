"""Same observations/weights for red-minus-green, before photographic transfer.
Earlier D3 compared separately weighted colour stacks; varying saturation can
compare different moments at the limb. Here each R/G pair must be valid and
receives identical inverse variance weight in both colour stacks. Existing
channel calibrations and detector estimates frozen; no new spatial mask.
"""
from common import *
from scipy.ndimage import gaussian_filter,gaussian_filter1d
claim();model=json.loads((OLD/'A5_color_model.json').read_text());alpha=model['slopes']['R'];offset=model['offsets']['R'];frac=model['weights']['R']/(model['weights']['R']+model['weights']['G']);fs=[m for m in frames() if m['tren']=='vixen'];des=json.loads((OLD/'B3_G67_robust_hetero_full_safe_design.json').read_text());sh=np.array(des['shifts']);Dg=np.load(OLD/'arrays/B11_repeatable_all.npz')['detector'];Dr=np.load(OLD/'arrays/B3_R67_robust_hetero_full_safe_all.npz')['detector'];physical=np.load(OUT/'arrays/A1_sources.npz')['physical'];nr=np.zeros((N,N));ng=nr.copy();den=nr.copy();rows=[]
save('R0_protocol.json',dict(method=__doc__,red_scale=alpha,red_offset=offset,red_fraction=frac,rule='Both source stacks share w=min(qR,qG)/(smoothed variance_R/alpha^2+smoothed variance_G), only common actual support. Subtract frozen own-colour detector; R field has full-safe covariance, G has qualified repeatability gain. No colour pixels forced valid.',planned='Red minus paired green; spatial display response fitted only even sectors; exact Sony/LROC/93 previous photo claims and injections unchanged',limits='Same sensor, shared calibration; red detector independent qualification still required, no physical PSF claim'))
for i,m in enumerate(fs):
 z=np.load(m['file']);qg=(z['G1_q']+z['G2_q'])/2;g=(np.nan_to_num(z['G1'])*z['G1_q']+np.nan_to_num(z['G2'])*z['G2_q'])/np.maximum(2*qg,1e-30);vg=(np.nan_to_num(z['G1_var'])*z['G1_q']**2+np.nan_to_num(z['G2_var'])*z['G2_q']**2)/np.maximum((2*qg)**2,1e-30);qr=z['R_q'];vr=z['R_var']/alpha**2;rr=z['R']/alpha+offset;ok=physical&(qr>0)&(qg>0)&np.isfinite(rr)&np.isfinite(vr)&np.isfinite(vg);v=gaussian_filter(np.where(ok,vr+vg,0),4)/np.maximum(gaussian_filter(ok.astype(float),4),1e-30);w=np.where(ok,np.minimum(qr,qg)/np.maximum(v,1e-12),0);r=rr-pull(Dr,sh[i])/alpha;g=g-pull(Dg,sh[i]);nr+=w*np.nan_to_num(r);ng+=w*g;den+=w;rows.append(dict(stem=m['stem'],valid=int(ok.sum())))
 if (i+1)%15==0:print('RED PAIR',i+1,flush=True)
R=np.divide(nr,den,out=np.full((N,N),np.nan),where=den>0);G=np.divide(ng,den,out=np.full((N,N),np.nan),where=den>0);np.savez_compressed(OUT/'arrays/R0_paired_red.npz',red=R,green=G,contrast=R-G,weight=den,fraction=frac)
save('R0_paired_red.json',dict(frames=rows,common_pixels=int((den>0).sum()),red_fraction=frac,raw_delta_range=[float(np.nanmin(R-G)),float(np.nanmax(R-G))]));print('PAIRED RED DONE',flush=True)
