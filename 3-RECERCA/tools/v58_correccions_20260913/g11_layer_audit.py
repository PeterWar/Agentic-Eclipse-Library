from common58 import *
from psd_tools import PSDImage
claim();p=O/'V58_protected_work.psb';s=PSDImage.open(p);exp=json.loads((O/'G9_RHEF_protection.json').read_text())['edited_channel_raw_sha256'];src=json.loads((O/'A0_freeze.json').read_text());rep=dict(layers=len(s),size=s.size,depth=s.depth,edited_channels={},unchanged_layers={});assert len(s)==30 and s.size==(10551,7506) and s.depth==16
for i,l in enumerate(s):
 for ci in l._record.channel_info:
  c=int(ci.id);key=f'{i}:{c}'
  if key not in exp:continue
  a=chan(l,c);v=hashlib.sha256(a.astype('>u2').tobytes()).hexdigest();assert v==exp[key],key;rep['edited_channels'][key]=v
 if i in [0,7,8,9,29]:
  actual=[dict(id=int(ci.id),compression=int(cd.compression),sha256=hashlib.sha256(cd.data).hexdigest()) for ci,cd in zip(l._record.channel_info,l._channels)];old=src['layers'][i]['channels'];assert actual==old,(i,'compressed channels');assert list(l.bbox)==src['layers'][i]['bbox'];oldmask=src['layers'][i].get('mask');mask=l._record.mask_data.tobytes().hex() if l._record.mask_data else None;assert oldmask==mask,(i,'mask');rep['unchanged_layers'][str(i)]=dict(channels_exact=True,mask_exact=True,geometry_exact=True)
 print('audited',i,l.name,flush=True)
# Field invariants in corrected mask11 and the reference contour.
def getroi(l,c):
 a=chan(l,c);bb=(l._record.mask_data.left,l._record.mask_data.top) if c==-2 else l.bbox[:2];return a[ROI[1]-bb[1]:ROI[3]-bb[1],ROI[0]-bb[0]:ROI[2]-bb[0]]
mm=getroi(s[1],-2);yy,xx=np.mgrid[:2000,:2000];rad=np.hypot(xx-999.5681,yy-999.6475);rep['mask11_inside_r435_max']=int(mm[rad<435].max());assert rep['mask11_inside_r435_max']==0
rep['PASS']=True;rep['n_edited_channels_verified']=len(rep['edited_channels']);save('G11_layer_audit.json',rep);print('LAYER_AUDIT_PASS',flush=True)
