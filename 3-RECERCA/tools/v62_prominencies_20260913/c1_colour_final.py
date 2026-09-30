from pathlib import Path
import ast,json,numpy as np,cv2
from scipy.ndimage import binary_dilation,distance_transform_edt
R=Path.cwd();O=R/'output/v62_prominencies_20260913';A=O/'arrays';V42=R/'research/tools/v42_20260910/cau';ROI=np.s_[2777:4777,4377:6377]
gauss=lambda a,s:cv2.GaussianBlur(np.asarray(a,np.float32),(0,0),s,borderType=cv2.BORDER_REFLECT_101)
tree=ast.parse((R/'research/tools/eclipse_determinista/comu.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['a_lineal','a_srgb']],type_ignores=[]),'comu_pure','exec'))
base=np.stack([np.load(A/f'V61_L02_C{c}.npy') for c in range(3)],-1).astype('float32')/65535
data=np.nan_to_num(np.array(np.load(V42/'fusion_total_v42_sense_estrelles.npy',mmap_mode='r')[ROI]));m=np.load(V42/'support_v42.npy',mmap_mode='r')[ROI].astype('float32');L=(data[...,0]+2*data[...,1]+data[...,2])/4
y,x=np.mgrid[2777:4777,4377:6377];rad=np.hypot(x-5376.568111973117,y-3776.647534140857)
ratio=np.divide(data[...,0],data[...,1],out=np.zeros_like(L),where=data[...,1]>0);ex=(ratio>2.5)&(m>0)&(rad<650)
def field(weight):
 den=gauss(L*weight,24);return np.stack([gauss(data[...,c]*weight,24)/np.maximum(den,1e-8) for c in range(3)],-1)
qo=field(m);qn=field(m*(~ex))
lin=a_lineal(base);Y=(lin[...,0]+2*lin[...,1]+lin[...,2])/4;qm=qn.max(-1);wg=np.clip(np.where(qm>1,(1/np.maximum(Y,1e-8)-1)/np.maximum(qm-1,1e-8),1),0,1)
newlin=Y[...,None]*(1+wg[...,None]*(qn-1));protect=gauss(binary_dilation(ex,iterations=2).astype('float32'),1);protect[ex]=1
influence=(gauss(ex.astype('float32'),24)>0)&(m>0);w=(1-protect)*influence
newlin=lin+(newlin-lin)*w[...,None];new=a_srgb(newlin);new[~influence]=base[~influence];new[ex]=base[ex];u=np.rint(np.clip(new,0,1)*65535).astype('uint16');np.save(A/'C1_base_RGB16.npy',u)
v=np.load(A/'B1_vixen_linear.npy');s=np.load(A/'B1_sony_linear.npy');ok=(v>0).all(-1)&(s>0).all(-1)&np.isfinite(v).all(-1)&np.isfinite(s).all(-1)
train=ok&(rad>550)&(rad<650)&(y<3776-400)
vr=v/np.maximum(v[...,1:2],1e-10);sr=s/np.maximum(s[...,1:2],1e-10);gain=np.median(vr[train]/sr[train],axis=0);sr=sr*gain
vw=np.load(V42/'weight_vixen_v42.npy',mmap_mode='r')[ROI];quiet=ok&(distance_transform_edt(~ex)>8)&(vw>.999)&(rad>458)
rows=[]
for name,bb in [('west',(4824,3713,4900,3904)),('east',(5829,3706,5856,3806))]:
 x0,y0,x1,y1=bb;sel=quiet&(x>=x0)&(x<x1)&(y>=y0)&(y<y1);qold=qo[sel]/qo[sel,1:2];qnew=qn[sel]/qn[sel,1:2]
 rows.append(dict(name=name,n=int(sel.sum()),Sony_global_gain=gain.tolist(),median_abs_log_colour_error_before=np.median(abs(np.log(np.maximum(qold,1e-10)/np.maximum(sr[sel],1e-10))),axis=0).tolist(),median_abs_log_colour_error_after=np.median(abs(np.log(np.maximum(qnew,1e-10)/np.maximum(sr[sel],1e-10))),axis=0).tolist()))
afterlin=a_lineal(u/65535);Ya=(afterlin[...,0]+2*afterlin[...,1]+afterlin[...,2])/4;changed=np.any(u!=np.rint(base*65535).astype('uint16'),-1)
rep=dict(source='V42 q24 producer, own Vixen source at the measured regions; Sony reserved',sigma=24,exclude_R_over_G=2.5,excluded_from_estimator=int(ex.sum()),core_RGB_exact=bool(np.array_equal(u[ex],np.rint(base[ex]*65535).astype('uint16'))),max_linear_display_luminance_error=float(abs(Ya-Y).max()),pixels_changed=int(changed.sum()),changed_bbox=[int(x[changed].min()),int(y[changed].min()),int(x[changed].max()+1),int(y[changed].max()+1)],held_out_Sony=rows,limits='Photographic colour-estimator correction, not proof that all red atmospheric light is absent. No luminance filtering, no raw change.')
for q in rows:
 assert q['median_abs_log_colour_error_after'][0]<q['median_abs_log_colour_error_before'][0]
 assert q['median_abs_log_colour_error_after'][2]<q['median_abs_log_colour_error_before'][2]
assert abs(Ya-Y).max()<3e-5
(O/'C1_colour_validation.json').write_text(json.dumps(rep,indent=2));print(json.dumps(rep,indent=2))
