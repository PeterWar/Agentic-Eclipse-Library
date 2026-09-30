from pathlib import Path
import numpy as np,ast,json
from scipy.ndimage import gaussian_filter
from PIL import Image,ImageCms,ImageDraw
R=Path.cwd();O=R/'output/v68_artefactes_20260914';A=O/'arrays';P=R/'output/v65_pere_estrelles_20260914/arrays';sl=np.s_[2777:4777,4377:6377]
tree=ast.parse((R/'research/tools/eclipse_determinista/comu.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['a_lineal','a_srgb']],type_ignores=[]),'pure','exec'))
old=np.stack([np.load(A/f'L3_C{c}.npy') for c in range(3)],-1);base=np.stack([np.load(P/f'L3_C{c}.npy') for c in range(3)],-1).astype(float)/65535;lin=a_lineal(base);Y=(lin[...,0]+2*lin[...,1]+lin[...,2])/4;cur=a_lineal(old/65535);z=np.load(A/'B2_colour_context.npz');protect=z['protect'];d=np.array(np.load(R/'output/v58_correccions_20260913/sources/fusion_starless.npy',mmap_mode='r')[sl]);L=(d[...,0]+2*d[...,1]+d[...,2])/4;q=d/np.maximum(L[...,None],1e-8);valid=(d>0).all(-1)&(protect>0);limit=1/np.maximum(q.max(-1),1);start=.9*limit;v=np.maximum(Y-start,0);Yn=np.where(Y>start,start+v/(1+v/np.maximum(limit-start,1e-6)),Y);newlin=cur+(Yn[...,None]*q-lin)*protect[...,None]*valid[...,None]*(Y>start)[...,None];new=np.rint(a_srgb(np.clip(newlin,0,1))*65535).astype(np.uint16);active=valid&(Y>start);new[~active]=old[~active];np.save(A/'B4_L3_colour.npy',new)
ref=z['ref'];oldratio=cur/np.maximum(cur[...,1:2],1e-8);nl=a_lineal(new/65535);newratio=nl/np.maximum(nl[...,1:2],1e-8);rows=[]
for name,bb in [('SW',(4935,3970,5080,4120)),('east',(5740,3880,5880,4030)),('top',(5280,3220,5520,3370))]:
 x0,y0,x1,y1=bb;ss=np.s_[y0-2777:y1-2777,x0-4377:x1-4377];sel=active[ss]&(ref[ss]>0).all(-1)&(new[ss]>0).all(-1)&(np.load(A/'L30_C-2.npy')[ss]<6553)
 eo=np.median(abs(np.log(oldratio[ss][sel]/ref[ss][sel])),axis=0) if sel.any() else np.zeros(3);en=np.median(abs(np.log(newratio[ss][sel]/ref[ss][sel])),axis=0) if sel.any() else np.zeros(3)
 rows.append(dict(region=name,n=int(sel.sum()),before=eo[[0,2]].tolist(),after=en[[0,2]].tolist()))
 im=Image.new('RGB',((x1-x0)*6,(y1-y0)*3+30),'#151515');dr=ImageDraw.Draw(im)
 for k,a in enumerate([old,new]):
  v=Image.fromarray(np.uint8(a[ss]/257+.5));v=ImageCms.profileToProfile(v,ImageCms.ImageCmsProfile(str(O/'AdobeRGB.icc')),ImageCms.createProfile('sRGB'),outputMode='RGB');im.paste(v.resize(((x1-x0)*3,(y1-y0)*3),Image.Resampling.NEAREST),(k*(x1-x0)*3,30));dr.text((k*(x1-x0)*3+5,8),['V67 base','Pilot: highlights in line-emission protection'][k],fill='white')
 im.save(O/'vistes'/f'B4_{name}.png')
rep=dict(cause='V65 prominence exclusion protected old desaturated highlight mapping as well as true red colour. Complete highlight mapping inside this protection using measured physical source chromaticity.',changed_pixels=int(np.any(new!=old,-1).sum()),outside_protection_exact=bool(np.array_equal(new[protect==0],old[protect==0])),original_Y_used=True,no_second_shoulder=True,Sony=rows);(O/'B4_colour_pilot.json').write_text(json.dumps(rep,indent=2)+'\n');print(rep)
