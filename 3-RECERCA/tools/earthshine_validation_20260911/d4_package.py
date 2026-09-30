"""Reversible V47 photographic comparison; preserve all user layers exactly.
Only old lunar source and deprecated manual grade are hidden; new source copy
inherits the complete original layer mask and placement. No geometry edits.
"""
from validation_common import *
from photoshop_api import jsx
import sys,copy,gc,subprocess,tifffile
from PIL import Image
sys.path.insert(0,str(ROOT/'research/tools/v45_earthshine_20260910'))
from c5_fonts_psb import C,PSDImage,fingerprint
from psd_tools.api.layers import PixelLayer
from psd_tools.constants import Tag,Resource,Compression
NAME='V47 prova · composició de fonts · to Camera Raw preservat'
TARGET=OUT/'Earthshine_V47_Comparacio.psb';SRC=PREV/'V46_Detall_live_source.psd';W=10551;H=7506;X0=4677;Y0=3077
if __name__=='__main__':
 assert not TARGET.exists()
 s=PSDImage.open(SRC);assert len(s)==24 and s.size==(W,H) and s.depth==16
 before=[fingerprint(l) for l in s];l=next(l for l in s if l.name=='V45 font G · dos trens · preferència temporal · vel present');assert l.visible and l.opacity==255 and l.blend_mode==C.BlendMode.NORMAL
 old=np.stack([C.channel(l,c) for c in range(3)],-1);new=np.load(OUT/'D2_candidate_rgb.npy');assert np.array_equal(old,np.load(PREV/'A0_live_layer21_rgb.npy'))
 m=C.channel(l,-2);md=l._record.mask_data;assert m.shape==(H,W) and (md.left,md.top)==(0,0) and not md.flags.mask_disabled and not md.flags.invert_mask
 print('mask',md,flush=True)
 mr=m[Y0:Y0+N,X0:X0+N].astype(float)/65535;del m
 nl=PixelLayer(s,copy.deepcopy(l._record),copy.deepcopy(l._channels))
 for info,ch in zip(nl._record.channel_info,nl._channels):
  if int(info.id) in [0,1,2]:
   ch.compression=Compression.ZIP;ch.set_data(np.ascontiguousarray(new[...,int(info.id)].astype('>u2')).tobytes(),N,N,16,2);info.length=len(ch.data)+2
 s.append(nl);nl.name=NAME;nl.visible=True;l.visible=False
 hidden=[l.name]
 for o in list(s)[:24]:
  if o.name.startswith('V46 · contorn fosc gradual'):o.visible=False;hidden.append(o.name)
 s._record.header.version=2
 for tag in (Tag.FILTER_MASK,Tag.COMPOSITOR_INFO):
  if tag in s._record.layer_and_mask_information.tagged_blocks:s._record.layer_and_mask_information.tagged_blocks[tag].signature=b'8B64'
 if Resource.THUMBNAIL_RESOURCE in s._record.image_resources:del s._record.image_resources[Resource.THUMBNAIL_RESOURCE]
 C.finalize_lr16(s)
 a=tifffile.imread(OUT/'D3_baseline_no_manual_grade_RGBA.tif');assert a.shape==(H,W,4) and a.dtype==np.uint16
 alpha=a[...,3].copy();comp=np.empty((H,W,3),np.uint16)
 for y in range(0,H,128):
  sl=slice(y,min(y+128,H));comp[sl]=np.rint(np.clip(a[sl,:,:3].astype(float)*65535/np.maximum(alpha[sl,:,None],1),0,65535)).astype(np.uint16)
 del a
 assert np.all(alpha[Y0:Y0+N,X0:X0+N]==65535)
 roi=comp[Y0:Y0+N,X0:X0+N];baseline=roi.copy();delta=(new.astype(float)-old)*mr[...,None];expected=roi.astype(float)+delta
 assert expected.min()>=0 and expected.max()<=65535
 roi[:]=np.rint(expected).astype(np.uint16);np.save(OUT/'D4_expected_moon.npy',roi)
 np.save(OUT/'D4_inherited_mask_roi.npy',np.rint(mr*65535).astype(np.uint16))
 vis=OUT/'vistes';Image.fromarray((roi>>8).astype(np.uint8)).save(vis/'D4_candidate_composite_moon.png');Image.fromarray((baseline>>8).astype(np.uint8)).save(vis/'D4_baseline_no_grade_moon.png')
 rgba=np.dstack([comp[::4,::4]>>8,alpha[::4,::4]>>8]).astype(np.uint8);Image.fromarray(rgba).save(vis/'D4_candidate_full_canvas.png')
 for title,box in [('top',(550,220,850,290)),('right',(1100,550,1180,850)),('bottom',(550,1100,850,1180))]:
  x1,y1,x2,y2=box;pair=np.concatenate([baseline[y1:y2,x1:x2],roi[y1:y2,x1:x2]],axis=0 if title!='right' else 1);im=Image.fromarray((pair>>8).astype(np.uint8));im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST).save(vis/('D4_'+title+'_before_after_x3.png'))
 chromadelta=(roi.astype(int)-roi[...,1,None].astype(int))-(baseline.astype(int)-baseline[...,1,None].astype(int))
 data=[np.ascontiguousarray(comp[...,c].astype('>u2')).tobytes() for c in range(3)]+[np.ascontiguousarray(alpha.astype('>u2')).tobytes()]
 merged=C.ImageData(compression=Compression.RAW);merged.set_data(data,s._record.header);s._record.image_data=merged;s._updated=False
 del comp,alpha,data;gc.collect()
 with TARGET.open('xb') as f:s.save(f)
 save('D4_build.json',dict(method=__doc__,source=str(SRC),source_sha256=hashlib.file_digest(SRC.open('rb'),'sha256').hexdigest(),target=str(TARGET),new_layer=NAME,source_layers=before,hidden_in_candidate=hidden,mask='Complete source mask bytes and geometry inherited',max_change_chroma_DN16=int(abs(chromadelta).max()),new_photographic_delta=True,science_status='NOT a claim of all-limb recovery or a clean radiance product',expected_composite='Native baseline without manual grade plus inherited-mask normal-source difference'))
 print('BUILT',TARGET,flush=True)
