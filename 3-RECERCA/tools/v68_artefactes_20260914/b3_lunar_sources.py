from pathlib import Path
import numpy as np,json
from PIL import Image,ImageDraw
from scipy.ndimage import gaussian_filter
R=Path.cwd();O=R/'output/v68_artefactes_20260914';A=O/'arrays';V=O/'vistes';x0,y0,x1,y1=5170,3910,5470,4170
s=np.s_[y0-3077:y1-3077,x0-4678:x1-4678]
sony=np.load(R/'output/earthshine_detail_20260911/B2_sony_reference.npz')['reference'];vixen=np.load(R/'output/earthshine_v56_three_routes_20260913/arrays/R5_sources.npz');lroc=np.load(R/'research/tools/v42_20260910/cau/lroc_capa_v39_rgba.npy');bb=json.loads((R/'output/v42_20260910/4-rebuts/P2b_rotacio.json').read_text())['lroc_bbox'];lr=np.zeros((1400,1400));oy,ox=bb[1]-3077,bb[0]-4677;lr[oy:oy+lroc.shape[0],ox:ox+lroc.shape[1]]=lroc[...,:3].mean(-1)
print('R5 keys',vixen.files)
photo=np.load(A/'L30_C1.npy')[300:1700,301:1701];srcs={'V67 photo':photo,'Sony independent':sony,'LROC reference':lr}
for k in ['Gclean','red_repeatable']:srcs[k]=vixen[k]
pan=Image.new('RGB',(900*3,810*2),'#151515');draw=ImageDraw.Draw(pan);rows=[]
for k,(name,src) in enumerate(srcs.items()):
 q=np.asarray(src[s],float);lo,hi=np.percentile(q[np.isfinite(q)],[1,99]);z=(q-lo)/(hi-lo);im=Image.fromarray(np.uint8(np.clip(z,0,1)*255+.5));im=im.resize((900,780),Image.Resampling.NEAREST);xx=(k%3)*900;yy=(k//3)*810;pan.paste(im,(xx,yy+30));draw.text((xx+10,yy+8),name+' | identical ROI, individual linear stretch',fill='white');np.save(A/('B3_'+name.split()[0]+'.npy'),q)
 base=srcs['V67 photo'][s];qa=q-gaussian_filter(q,12);ba=base-gaussian_filter(base.astype(float),12);rows.append(dict(name=name,correlation=float(np.corrcoef(ba.ravel(),qa.ravel())[0,1])))
pan.save(V/'B3_lunar_sources.png');(O/'B3_lunar_sources.json').write_text(json.dumps(rows,indent=2)+'\n');print(rows)
