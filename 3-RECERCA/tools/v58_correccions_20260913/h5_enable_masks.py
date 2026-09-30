from common58 import *
from psd_tools import PSDImage
import attrs,sys
sys.path.insert(0,str(R/'research/tools/encaix_sony'));from psb_utils import finalize_lr16
claim();s=PSDImage.open(O/'V58_final.psb');r={'finding':'All16 filter masks inherited disabled flags from user V57. Changes to pixels were correct but could not affect Photoshop until masks were enabled. Native O/P RHEF renders were exactly identical; no visual gate is claimed for those intermediates.','layers':{}}
for i in range(11,27):
 m=s[i]._record.mask_data;assert m.flags.mask_disabled;r['layers'][str(i)]={'before_disabled':True,'after_disabled':False};m.flags.mask_disabled=False
finalize_lr16(s);s._updated=False;p=O/'V58_enabled_work.psb';assert not p.exists()
with p.open('xb') as f:s.save(f)
r['path']=str(p);save('H5_enabled_masks.json',r);print('MASKS_ENABLED',flush=True)
