from common60 import *
from psd_tools import PSDImage
from psd_tools.constants import Resource
import sys
claim();p=O/('V60_ready.psb' if '--final' in sys.argv else 'V60_work.psb');s=PSDImage.open(p);a=json.loads((O/'A0_freeze.json').read_text());exp=json.loads((O/'D0_build.json').read_text())['expected_channels'];rep={'path':str(p),'changed_channels':{},'unchanged_channels':0,'layers':len(s),'PASS':True}
assert len(s)==31 and s.size==(10551,7506) and s.depth==16
for i,(l,row) in enumerate(zip(s,a['layers'])):
 assert list(l.bbox)==row['bbox'] and str(l.blend_mode)==row['blend'] and l.opacity==row['opacity'] and l.visible==(False if i==30 else row['visible']),(i,'meta')
 assert (None if l._record.mask_data is None else l._record.mask_data.tobytes().hex())==row['mask'],(i,'maskmeta')
 for info,cd,old in zip(l._record.channel_info,l._channels,row['channels']):
  cid=int(info.id);key=f'{i}:{cid}';assert cid==old['id']
  if key in exp:
   u=chan(l,cid);digest=hashlib.sha256(u.astype('>u2').tobytes()).hexdigest();assert digest==exp[key],key;rep['changed_channels'][key]=digest
  else:assert int(cd.compression)==old['compression'] and hashlib.sha256(cd.data).hexdigest()==old['sha256'],key;rep['unchanged_channels']+=1
assert s.image_resources.get_data(Resource.ICC_PROFILE)==(O/'AdobeRGB.icc').read_bytes()
rep['sha256']=sha(p);rep['bytes']=p.stat().st_size;save('D2_final_channels.json' if '--final' in sys.argv else 'D2_work_channels.json',rep);print('VERIFIED',len(exp),'edited channels;',rep['unchanged_channels'],'untouched',flush=True)
