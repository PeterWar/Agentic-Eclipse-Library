"""Stream preserved PSB records/channels, replace selected RGB, add lunar-only225mask.
The merged cache is explicitly provisional until native Photoshop save.
"""
from a4_sources import *
import struct,zlib,io
sys.path.insert(0,str(R/'3-RECERCA/tools/v73_marques_v71_20260917'))
from psb69 import PSB,BIG_KEYS,_rf
from psd_tools.psd.layer_and_mask import LayerRecord,MaskData,MaskFlags,ChannelInfo
from psd_tools.constants import Tag,ChannelID

MAP={41:'P01_NRGF',42:'P01_NRGF_extrap',43:'P02_RHEF',44:'P02b_RHEF_ups0.35',45:'P02c_RHEF_local60_native',46:'P02d_RHEF_local30_native',47:'03',48:'03v30',49:'07',50:'01',51:'04',52:'05',53:'06',54:'P03_MGN',55:'P04_WOW',56:'P05_WOW_bilateral',250:'P05_WOW_bilateral'}

def enc(a):
 d=a.copy();d[:,1:]=a[:,1:]-a[:,:-1];return struct.pack('>H',3)+zlib.compress(d.astype('>u2').tobytes(),6)

def build(label,filters=None):
 src=O/'V84_Pere_input.psb';inp=json.loads((O/'INPUT.json').read_text());assert sha(src)==inp['sha256'];dst=O/(label+'.psb');cache=O/(label+'_channels');assert not dst.exists();cache.mkdir(exist_ok=True);p=PSB(str(src));changes={};report={'input':inp,'filter_path':str(filters) if filters else None,'base':'pointwise commonRGB shoulder s75c90, no spatial smoothing','mask225':'existing lunar-photo support only; original RGB and alpha preserved','filters':[],'merged_cache':'PROVISIONAL pending native Photoshop recomposition'}
 # This is a display-only mapping in the same encoded RGB convention as the native pilot.
 base=np.stack([p.channel(3,c)[0] for c in [0,1,2]],-1).astype(np.float32)/65535;mx=base.max(-1);newmax=np.where(mx>.75,.75+.15*(1-np.exp(-(mx-.75)/.15)),mx);gain=np.divide(newmax,mx,out=np.ones_like(mx),where=mx>0);new=np.rint(np.clip(base*gain[...,None],0,1)*65535).astype(np.uint16)
 for c in [0,1,2]:
  file=cache/f'L3_C{c}.bin';prior=O/'DisplayFix2_stage_channels'/file.name
  if prior.exists():
   data=prior.read_bytes();assert np.array_equal(p._decode(data,10551,7506),new[...,c]);file.write_bytes(data)
  else:file.write_bytes(enc(new[...,c]))
  changes[(3,c)]=file
 report['base_changed_pixels']=int(np.count_nonzero(np.any(new!=np.rint(base*65535).astype(np.uint16),-1)));del base,new,mx,newmax,gain
 lunar=np.load(O/'current_lunar_support.npz');m=lunar['support'];x0,y0,x1,y1=lunar['box'];L=p.layer(225);mask=m[L['top']-y0:L['bottom']-y0,L['left']-x0:L['right']-x0].astype(np.uint16)*65535;fmask=cache/'L225_C-2.bin';fmask.write_bytes(enc(mask));changes[(225,-2)]=fmask
 basemask,org=p.channel(3,-2);ox,oy=org;basemask[y0-oy:y1-oy,x0-ox:x1-ox][m]=0;fm=cache/'L3_C-2.bin';fm.write_bytes(enc(basemask));changes[(3,-2)]=fm;report['base_mask']='Existing base mask preserved outside lunar support; zero inside to retain original hidden-base contribution under the partly transparent lunar layers';del basemask
 # The visible PixInsight raster also contains Pere's processed Moon. Retain that
 # exact lunar contribution while removing its baked old corona from the new blend.
 pix,org=p.channel(234,-2);keep=np.zeros_like(pix);ox,oy=org;roi=pix[y0-oy:y1-oy,x0-ox:x1-ox];keep[y0-oy:y1-oy,x0-ox:x1-ox]=np.where(m,roi,0);fpix=cache/'L234_C-2.bin';fpix.write_bytes(enc(keep));changes[(234,-2)]=fpix;report['pix234']='Original RGB/alpha/opacity and mask values retained within exact existing lunar-photo support; mask zero only outside it, so baked V84 corona cannot hide new filters';del pix,keep,roi
 if filters:
  report['newly_undefined_E6_masks']=[]
  domain=np.load(O/'domain_v1/sources/support.npy',mmap_mode='r')
  for lid,tag in [(45,'P02c_RHEF_local60_native'),(46,'P02d_RHEF_local30_native')]:
   oldsup=np.load(O/'filters_baseline/products/filters'/(tag+'_support.npy'),mmap_mode='r');newsup=np.load(O/'filters_harmonic_rest/products/filters'/(tag+'_support.npy'),mmap_mode='r');invalid=oldsup&~newsup&domain;yy,xx=np.where(invalid);oldmask,org=p.channel(lid,-2);ox,oy=org;before=oldmask[yy-oy,xx-ox].copy();oldmask[yy-oy,xx-ox]=0;file=cache/f'L{lid}_C-2.bin';file.write_bytes(enc(oldmask));changes[(lid,-2)]=file;report['newly_undefined_E6_masks'].append({'id':lid,'new_invalid':int(invalid.sum()),'active_mask_changed':int(np.count_nonzero(before)),'coordinates_xy':np.column_stack([xx,yy]).tolist(),'reason':'Original minimum 50 samples per native CDF cell retained; neutral0.5 is not neutral under Multiply; exclude only newly undefined filter contribution, physical radiance untouched'});del oldmask,invalid
  for lid,tag in MAP.items():
   a=np.load(filters/(tag+'_u16.npy'),mmap_mode='r');assert a.shape==(7506,10551) and a.dtype==np.uint16;file=cache/(tag+'.bin')
   if not file.exists():file.write_bytes(enc(a))
   assert np.array_equal(p._decode(file.read_bytes(),10551,7506),a)
   for c in [0,1,2]:changes[(lid,c)]=file
   report['filters'].append({'id':lid,'tag':tag,'input_sha256':sha(filters/(tag+'_u16.npy'))});print('PSB_FILTER',lid,tag,flush=True)
 with src.open('rb') as f:
  f.seek(26)
  for _ in range(2):n=_rf(f,'I')[0];f.seek(n,1)
  lmpos=f.tell();lmlen=_rf(f,'Q')[0];lmend=f.tell()+lmlen;n=_rf(f,'Q')[0];assert n==0;n=_rf(f,'I')[0];f.seek(n,1)
  while f.tell()+12<=lmend:
   sig,key=_rf(f,'4s4s');fmt='Q' if key in BIG_KEYS else 'I';lenpos=f.tell();n=_rf(f,fmt)[0];start=f.tell()
   if key==b'Lr16':break
   f.seek(start+(n+3)//4*4)
  else:raise RuntimeError('Missing Lr16')
  lrlen=n;lrstart=start;lrpadend=start+(n+3)//4*4;count=_rf(f,'h')[0];recordstart=f.tell();records=[];channel_order=[]
  for _ in range(abs(count)):
   pos=f.tell();r=LayerRecord.read(f,version=2);end=f.tell();lid=int(r.tagged_blocks.get_data(Tag.LAYER_ID));f.seek(pos);raw=bytearray(f.read(end-pos));ids=[int(c.id) for c in r.channel_info]
   if lid==225:
    assert -2 not in ids and r.mask_data is None;r.mask_data=MaskData(top=L['top'],left=L['left'],bottom=L['bottom'],right=L['right'],background_color=0,flags=MaskFlags());r.channel_info.append(ChannelInfo(id=ChannelID.USER_LAYER_MASK,length=fmask.stat().st_size));ids.append(-2);buf=io.BytesIO();r.write(buf,version=2);raw=bytearray(buf.getvalue())
   for j,cid in enumerate(ids):
    if (lid,cid) in changes:raw[18+j*10+2:18+j*10+10]=struct.pack('>Q',changes[(lid,cid)].stat().st_size)
   # Flags are the only existing record bytes changed beyond channel lengths.
   off=18+10*len(ids)+10
   if lid in [251,246]:raw[off]|=2
   if lid==3:raw[off]&=253
   records.append(bytes(raw));channel_order.append((lid,ids));f.seek(end)
  recordend=f.tell();assert recordend==min(v[0] for l in p.layers for v in l['chans'].values());newrecords=b''.join(records);delta=len(newrecords)-(recordend-recordstart)
  for (lid,cid),file in changes.items():delta+=file.stat().st_size-p.layer(lid)['chans'].get(cid,(0,0))[1]
  newlen=lrlen+delta;newpad=(newlen+3)//4*4;newlmlen=lmlen+newpad-(lrpadend-lrstart)
  def copyrange(g,start,end):
   f.seek(start)
   while f.tell()<end:g.write(f.read(min(16<<20,end-f.tell())))
  with dst.open('xb') as g:
   copyrange(g,0,lmpos);g.write(struct.pack('>Q',newlmlen));copyrange(g,lmpos+8,lenpos);g.write(struct.pack('>Q',newlen));g.write(struct.pack('>h',count));g.write(newrecords)
   for lid,ids in channel_order:
    for cid in ids:
     if (lid,cid) in changes:
      with changes[(lid,cid)].open('rb') as c:
       while block:=c.read(16<<20):g.write(block)
     else:pos,size=p.layer(lid)['chans'][cid];copyrange(g,pos,pos+size)
   g.write(b'\0'*(newpad-newlen));copyrange(g,lrpadend,src.stat().st_size)
 q=PSB(str(dst));assert (q.width,q.height,len(q.layers))==(10551,7506,len(p.layers));assert q.layer(3)['visible'] and q.layer(234)['visible'];assert all(not q.layer(i)['visible'] for i in [251,246]);got,_=q.channel(225,-2);assert np.array_equal(got,mask)
 save(O/(label+'_BUILD.json'),report);print('PSB_STAGE_READY',dst,flush=True)

if __name__=='__main__':guard();build(sys.argv[1],Path(sys.argv[2]) if len(sys.argv)>2 else None)
