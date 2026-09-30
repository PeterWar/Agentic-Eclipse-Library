from common58 import *
from psd_tools import PSDImage
import tifffile as tf,attrs
claim();p=O/'V58_ready.psb';s=PSDImage.open(p);pkg=json.loads((O/'I2_package.json').read_text());exp=pkg['expected_channels'];src=json.loads((O/'A0_freeze.json').read_text());rep=dict(layers=len(s),size=s.size,depth=s.depth,edited_channels={},unchanged_layers={});assert len(s)==30 and s.size==(10551,7506) and s.depth==16
for i,l in enumerate(s):
 for ci in l._record.channel_info:
  c=int(ci.id);key=f'{i}:{c}'
  if key not in exp:continue
  a=chan(l,c);v=hashlib.sha256(a.astype('>u2').tobytes()).hexdigest();assert v==exp[key],key;rep['edited_channels'][key]=v
 if i in [0,7,8,9,29]:
  actual=[dict(id=int(ci.id),compression=int(cd.compression),sha256=hashlib.sha256(cd.data).hexdigest()) for ci,cd in zip(l._record.channel_info,l._channels)];old=src['layers'][i]['channels'];assert actual==old,(i,'compressed channels');assert list(l.bbox)==src['layers'][i]['bbox'];oldmask=src['layers'][i].get('mask');mask=l._record.mask_data.tobytes().hex() if l._record.mask_data else None;assert oldmask==mask,(i,'mask');rep['unchanged_layers'][str(i)]=dict(channels_exact=True,mask_exact=True,geometry_exact=True)
 if 11<=i<=26:assert not l._record.mask_data.flags.mask_disabled
 print('audited',i,flush=True)
def getroi(l,c):
 a=chan(l,c);bb=(l._record.mask_data.left,l._record.mask_data.top) if c==-2 else l.bbox[:2];return a[ROI[1]-bb[1]:ROI[3]-bb[1],ROI[0]-bb[0]:ROI[2]-bb[0]]
mm=getroi(s[1],-2);yy,xx=np.mgrid[:2000,:2000];rad=np.hypot(xx-999.5681,yy-999.6475);rep['mask11_inside_r435_max']=int(mm[rad<435].max());assert rep['mask11_inside_r435_max']==0
rep['all_filter_masks_enabled']=True
native=tf.imread(O/'V58_ready_readback.tif');expected=tf.imread(O/'V58E_default_native.tif');assert native.shape==expected.shape==(7506,10551,3)
d=np.abs(native.astype('int32')-expected.astype('int32'));rep['native_readback_max_DN16']=int(d.max());rep['native_readback_nonzero_values']=int(np.count_nonzero(d));assert d.max()<=3;del d
merged=s._record.image_data.get_data(s._record.header);rep['merged_cache_max_DN16']=[]
for c in range(3):
 a=np.frombuffer(merged[c],dtype='>u2').reshape(7506,10551);mx=int(np.abs(a.astype('int32')-native[...,c].astype('int32')).max());rep['merged_cache_max_DN16'].append(mx);assert mx<=3
assert np.all(np.frombuffer(merged[3],dtype='>u2')==65535)
rep['Photoshop']=(O/'I3_photoshop_gate.txt').read_text().strip();assert 'OBRE 10551 px x 7506 px · 30 capes' in rep['Photoshop']
rep['independent_reader']=(O/'I3_independent_reader.txt').read_text().strip();assert '10551x7506' in rep['independent_reader'] and '16-bit' in rep['independent_reader']
rep['alignment_readback_PASS']=json.loads((O/'B10_alignment_readback.json').read_text())['PASS'];assert rep['alignment_readback_PASS'];rep['sources_unchanged']=json.loads((O/'H10_sources_unchanged.json').read_text());rep['PASS']=True;rep['n_edited_channels_verified']=len(rep['edited_channels']);save('I4_final_QA.json',rep);print('FINAL_QA_PASS',rep['native_readback_max_DN16'],flush=True)
