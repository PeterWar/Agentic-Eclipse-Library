from pathlib import Path
import numpy as np,ast,json
from scipy.ndimage import gaussian_filter,binary_dilation
R=Path.cwd();O=R/'output/v68_artefactes_20260914';A=O/'arrays';C=R/'research/tools/v42_20260910/cau';sl=np.s_[2777:4777,4377:6377]
tree=ast.parse((R/'research/tools/eclipse_determinista/comu.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['a_lineal','a_srgb']],type_ignores=[]),'pure','exec'))
base=np.stack([np.load(A/f'L3_C{c}.npy') for c in range(3)],-1).astype(float)/65535;lin=a_lineal(base);Y=(lin[...,0]+2*lin[...,1]+lin[...,2])/4;d=np.nan_to_num(np.array(np.load(C/'fusion_total_v42_sense_estrelles.npy',mmap_mode='r')[sl]));m=np.load(C/'support_v42.npy',mmap_mode='r')[sl].astype('float32');L=(d[...,0]+2*d[...,1]+d[...,2])/4
y,x=np.mgrid[2777:4777,4377:6377];rr=np.hypot(y-3776.647534140857,x-5376.568111973117);ex=(d[...,0]>2.5*d[...,1])&(d[...,1]>0)&(m>0)&(rr<650);w=m*(~ex);den=gaussian_filter(L*w,24);q=np.stack([gaussian_filter(d[...,c]*w,24)/np.maximum(den,1e-8) for c in range(3)],-1);protect=gaussian_filter(binary_dilation(ex,iterations=2).astype('float32'),1);protect[ex]=1
son=np.load(R/'output/v62_prominencies_20260913/arrays/B1_sony_linear.npy');ref=son/np.maximum(son[...,1:2],1e-8)*np.array(json.loads((R/'output/v62_prominencies_20260913/C1_colour_validation.json').read_text())['held_out_Sony'][0]['Sony_global_gain'])
rows=[]
for xx,yy in [(4993,4029),(5010,4053),(4985,4005),(5410,3323),(5796,3954)]:
 i,j=yy-2777,xx-4377;rows.append(dict(xy=[xx,yy],display=base[i,j].tolist(),Y=Y[i,j],old_source=d[i,j].tolist(),R_G=float(d[i,j,0]/max(d[i,j,1],1e-8)),corona_q=q[i,j].tolist(),limit=float(1/q[i,j].max()),protect=float(protect[i,j]),Sony_q=ref[i,j].tolist()))
np.savez_compressed(A/'B2_colour_context.npz',q=q,protect=protect,Y=Y,ref=ref,ex=ex)
(O/'B2_colour_diagnosis.json').write_text(json.dumps(rows,indent=2,default=float)+'\n');print(json.dumps(rows,indent=2,default=float))
