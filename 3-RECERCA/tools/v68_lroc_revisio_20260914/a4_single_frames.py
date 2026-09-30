from pathlib import Path
import numpy as np,json,cv2,gc
from scipy.ndimage import gaussian_filter
from PIL import Image,ImageDraw
R=Path.cwd();O=R/'output/v68_lroc_revisio_20260914';C=R/'research/tools/v36_20260908/cau';N=1400
allframes=json.loads((R/'output/earthshine_detail_20260911/B0_all_native.json').read_text())['frames'];frames=[]
for tag in ['sony','vixen']:
 z=[q for q in allframes if q['tren']==tag];frames.extend(sorted(z,key=lambda q:(-q['exp'],q['stem']))[:3])
y,x=np.mgrid[:N,:N];globalx=(x+4677).astype('float32');globaly=(y+3077).astype('float32');ss=np.s_[833:1103,462:792];r=np.hypot(x-699.568,y-699.648);local=(x>=462)&(x<792)&(y>=833)&(y<1103)&(r<420);mark=(x>=550)&(x<723)&(y>=902)&(y<1048);ctrl=local&~mark
pan=Image.new('RGB',(660*3,572*4),'#151515');dr=ImageDraw.Draw(pan);rep=[]
for i,q in enumerate(frames):
 a=np.load(q['file'])['g'];tag=q['tren'];meta=json.loads((C/f'{tag}_meta.json').read_text())['frames'];group=q['group'];gm=[mm for mm in meta if tag=='vixen' or mm['group']==group];j=next(j for j,mm in enumerate(gm) if Path(mm['name']).stem==q['stem']);phi=np.load(C/f'{group}_G_phi.npy',mmap_mode='r')[j];p=cv2.resize(np.array(phi,dtype='float32'),(phi.shape[1]*4,phi.shape[0]*4),interpolation=cv2.INTER_LINEAR);sx,sy=q['shift'];field=np.exp(-cv2.remap(p,globalx-sx,globaly-sy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE));del p;raw=a/field
 row=dict(stem=q['stem'],train=tag,exp=q['exp'],field_percentiles_in_mark=np.percentile(field[mark],[0,50,100]).tolist(),file=q['file'])
 for k,(label,img) in enumerate([('native calibrated',a),('before spatial field',raw)]):
  # A fixed blur suppresses shot noise for a broad-feature diagnostic; no fit to LROC.
  img=gaussian_filter(np.nan_to_num(img),4);lo,hi=np.percentile(img[local],[2,98]);v=np.uint8(np.clip((img[ss]-lo)/(hi-lo),0,1)*255+.5);im=Image.fromarray(v).convert('RGB');xx=i%3*660;yy=(i//3*2+k)*572;pan.paste(im.resize((660,540),Image.Resampling.NEAREST),(xx,yy+32));dr.text((xx+8,yy+8),q['stem']+' '+str(q['exp'])+'s | '+label,fill='white');row[label]=dict(mark_median=float(np.median(img[mark])),control_median=float(np.median(img[ctrl])),standardized_contrast=float((np.median(img[mark])-np.median(img[ctrl]))/np.std(img[ctrl])))
 rep.append(row);print(q['stem'],row,flush=True);gc.collect()
pan.save(O/'vistes/A4_individual_frames.png');(O/'A4_individual_frames.json').write_text(json.dumps(rep,indent=2)+'\n')
