"""One final assembly: retain all30 original records/pixels and append independent views."""
from common import *
import sys,copy,gc
sys.path.insert(0,str(ROOT/'research/tools/encaix_sony'))
sys.path.insert(0,str(ROOT/'research/tools/v29'))
from psb_utils import finalize_lr16
from inspect_inputs import channel
from psd_tools import PSDImage
from psd_tools.api.layers import PixelLayer
from psd_tools.constants import Compression,BlendMode,Tag,ChannelID
from psd_tools.psd.layer_and_mask import LayerRecord,ChannelInfo,ChannelData,ChannelDataList,MaskData,MaskFlags
from psd_tools.psd.tagged_blocks import TaggedBlocks
SRC=D/'sources/V31_abans.psb';TARGET=D/'staging/V31.psb'
EXPECTED='bbbb2b93a49a0e09226b89467754f6364d1c6b929bc147bd34387a1c66d7affe'
LAYERS=[
 ('P01_NRGF','P01 NRGF · V31'),
 ('P02_RHEF','P02 RHEF · comparacio amb anells · V31'),
 ('P03_MGN','P03 MGN · V31'),
 ('P04_WOW','P04 WOW sense denoise · V31'),
 ('P05_WOW_bilateral','P05 WOW bilateral sense denoise · V31'),
 ('P06_NAFE','P06 NAFE n65 · V31'),
 ('P07_ACHF_precursor16','P07 ACHF precursor sigma16 · V31'),
 ('P08_ACHF_precursor32','P08 ACHF precursor sigma32 · V31'),
 ('P09_SWAP_pilot','P09 SWAP · pilot llum blanca · V31'),
 ('C01_Passa_alt24_lineal','C01 Passa-alt24 lineal · control · V31')]
def digest(b):return hashlib.sha256(b).hexdigest()
def signature(l):
 return {'name':l.name,'bbox':list(l.bbox),'visible':l.visible,'opacity':l.opacity,'blend':str(l.blend_mode),'record_sha256':digest(l._record.tobytes(version=2)),'channels':{str(int(ci.id)):{'compression':int(cd.compression),'bytes':len(cd.data),'sha256':digest(cd.data)} for ci,cd in zip(l._record.channel_info,l._channels)}}
def global_signature(s):
 lm=s._record.layer_and_mask_information
 return {'header':digest(s._record.header.tobytes()),'color_mode':digest(s._record.color_mode_data.tobytes()),'image_resources':digest(s._record.image_resources.tobytes()),'other_global_tagged_blocks':{str(k):digest(v.tobytes(version=2)) for k,v in lm.tagged_blocks.items() if k!=Tag.LAYER_16}}
def compressed(u):
 cd=ChannelData(Compression.ZIP);cd.set_data(np.ascontiguousarray(u.astype('>u2')).tobytes(),W,H,16,2);return cd
def add_gray(s,u,name,alpha,mask):
 rec=LayerRecord(top=0,left=0,bottom=H,right=W,channel_info=[]);rec.tagged_blocks=TaggedBlocks();rec.name=name
 color=compressed(u);channels=ChannelDataList()
 for cid,cd in [(-1,alpha),(0,color),(1,color),(2,color),(-2,mask)]:
  rec.channel_info.append(ChannelInfo(ChannelID(cid),len(cd.data)+2));channels.append(copy.copy(cd))
 rec.mask_data=MaskData(top=0,left=0,bottom=H,right=W,background_color=0,flags=MaskFlags())
 l=PixelLayer(s,rec,channels);s.append(l);l.name=name;l.blend_mode=BlendMode.NORMAL;l.opacity=255;l.visible=False;return l
def main():
 assert not TARGET.exists();assert sha(SRC)==EXPECTED
 for p in ['base_fit_holdout.json','local_reference_QA.json','ACHF_quadrature_QA.json','external_judge.json','NAFE_reference_validation.json']:assert (D/'receipts'/p).exists()
 s=PSDImage.open(SRC);original=[signature(l) for l in s];assert len(original)==30 and s.size==(W,H) and s.depth==16
 original_global=global_signature(s);merged=digest(s._record.image_data.tobytes());m=np.load(C/'support.npy');alpha=compressed(np.full((H,W),65535,np.uint16));mask=compressed(m.astype('uint16')*65535);added=[]
 for tag,name in LAYERS:
  p=C/(tag+'_u16.npy');assert p.exists();u=np.load(p,mmap_mode='r');assert u.shape==(H,W) and u.dtype==np.uint16
  l=add_gray(s,u,name,alpha,mask);added.append({'tag':tag,'signature':signature(l),'parameters':json.loads((D/'receipts'/(tag+'.json')).read_text())});log('added '+name);gc.collect()
 finalize_lr16(s);s._updated=False
 assert global_signature(s)==original_global
 assert [signature(l) for l in list(s)[:30]]==original
 assert digest(s._record.image_data.tobytes())==merged
 savejson(D/'receipts/package.json',{'source':str(SRC),'source_sha256':EXPECTED,'target':str(TARGET),'original_layers':original,'global':original_global,'merged_sha256':merged,'added':added,'total_layers':len(s),'default':'all30 originals intact including visibility; all10 new independent Normal100% views OFF; enable one new layer at a time','physical_support':'same exact fusion_support, no added circular mask/crop','disposition':'scientific comparison; not a claim of artifact-free final enhancement'})
 log('saving single final assembly');s.save(TARGET);log('saved staging PSB')
def verify():
 rep=json.loads((D/'receipts/package.json').read_text());s=PSDImage.open(TARGET);assert len(s)==40 and s.size==(W,H) and s.depth==16
 assert global_signature(s)==rep['global'];assert digest(s._record.image_data.tobytes())==rep['merged_sha256']
 assert [signature(l) for l in list(s)[:30]]==rep['original_layers']
 m=np.load(C/'support.npy');rows=[]
 for l,(tag,name) in zip(list(s)[30:],LAYERS):
  assert l.name==name and not l.visible and l.opacity==255 and l.blend_mode==BlendMode.NORMAL and l.bbox==(0,0,W,H)
  u=np.load(C/(tag+'_u16.npy'),mmap_mode='r');assert all(np.array_equal(channel(l,c),u) for c in [0,1,2]);assert np.all(channel(l,-1)==65535);assert np.array_equal(channel(l,-2),m.astype('uint16')*65535)
  rows.append({'name':name,'RGB_exact':True,'alpha_opaque':True,'physical_mask_exact':True,'single_layer_recomposition':'Normal100% replaces underlying observed pixels exactly; outside unchanged'});log('verified '+tag)
 result={'PASS':True,'shape':[H,W],'depth':16,'layers':40,'all30_original_layer_records_and_compressed_channels_exact':True,'all_global_resources_exact':True,'default_merged_bytes_exact':True,'new_layers':rows,'sha256':sha(TARGET),'bytes':TARGET.stat().st_size};savejson(D/'receipts/psb_verification.json',result);log('PSB verified')
if __name__=='__main__':verify() if '--verify' in sys.argv else main()
