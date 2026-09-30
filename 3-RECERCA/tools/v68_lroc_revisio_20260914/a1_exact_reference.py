from pathlib import Path
import sys,json,gc,numpy as np
from psd_tools import PSDImage
from psd_tools.constants import Tag
from PIL import Image,ImageDraw
from scipy.ndimage import gaussian_filter
R=Path.cwd();O=R/'output/v68_lroc_revisio_20260914';A=O/'arrays';V=O/'vistes';P=R/'output/v68_artefactes_20260914'
sys.path.insert(0,str(R/'research/tools/v60_marques_v59_20260913'));from common60 import chan,box
assert json.loads((R/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_V68_LROC_REVIEW_20260914'
s=PSDImage.open(P/'V67_Pere_input.psb');l=next(l for l in s if int(l._record.tagged_blocks.get_data(Tag.LAYER_ID))==62)
bb=(4678,3077,6078,4477);rgb=np.stack([box(l,c,bb) for c in range(3)],-1);al=box(l,-1,bb);mask=box(l,-2,bb)
np.savez_compressed(A/'L62_exact_psb.npz',rgb=rgb,alpha=al,mask=mask,bbox=l.bbox)
meta=dict(name=l.name,bbox=l.bbox,blend=str(l.blend_mode),opacity=l.opacity,source=str(P/'V67_Pere_input.psb'),channels_exact_in_saved_V68=True)
del s,l;gc.collect()
photo=np.load(P/'arrays/B10_photo_pilot.npz')['candidate'].mean(-1);old=np.load(P/'arrays/B10_photo_pilot.npz')['old'].mean(-1);lr=rgb.mean(-1)
sony=np.load(R/'output/earthshine_detail_20260911/B2_sony_reference.npz')['reference'];vs=np.load(R/'output/earthshine_v56_three_routes_20260913/arrays/R5_sources.npz')['Gclean']
# Native source grids originate at 4677; the saved Moon was positioned by Pere at 4678.
# Keep each source's own coordinates and disclose the 1 px chart difference; do not warp any PSB.
sources={'V67 earthshine':old,'V68 earthshine':photo,'LROC exacte V58':lr,'Sony source (chart -1x)':sony,'Vixen source (chart -1x)':vs}
y,x=np.mgrid[:1400,:1400];valid=(np.hypot(x-699.568,y-699.648)<430)&(al>65000)&(mask>65000)
regions={'whole':(4878,3277,5878,4277),'orange':(5140,3910,5470,4180)}
for name,(x0,y0,x1,y1) in regions.items():
 ss=np.s_[y0-bb[1]:y1-bb[1],x0-bb[0]:x1-bb[0]];scale=1 if name=='whole' else 2;ww=(x1-x0)*scale;hh=(y1-y0)*scale
 for mode in ['wide','band16_64']:
  out=Image.new('RGB',(ww*3,(hh+32)*2),'#171717');dr=ImageDraw.Draw(out)
  for j,(label,q) in enumerate(sources.items()):
   q=np.asarray(q,float)
   if mode!='wide':q=gaussian_filter(q,3)-gaussian_filter(q,16)
   lo,hi=np.percentile(q[valid],[2,98]);arr=np.clip((q[ss]-lo)/(hi-lo),0,1);im=Image.fromarray(np.uint8(arr*255+.5)).convert('RGB');xx=(j%3)*ww;yy=(j//3)*(hh+32);out.paste(im.resize((ww,hh),Image.Resampling.NEAREST),(xx,yy+32));dr.text((xx+8,yy+8),label+' | '+mode,fill='white')
   if name=='whole':dr.rectangle((xx+(5228-x0),yy+32+(3979-y0),xx+(5401-x0),yy+32+(4125-y0)),outline='orange',width=2)
  out.save(V/f'A1_{name}_{mode}.png')
(O/'A1_exact_reference.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n');print('EXACT REFERENCE EXTRACTED',meta,flush=True)
