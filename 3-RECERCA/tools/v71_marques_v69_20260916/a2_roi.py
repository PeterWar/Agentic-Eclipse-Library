"""A2: extreu la ROI lunar (4377,2777)-(6377,4777) del compost i de totes les capes visibles de V69 (+ LROC oculta), i el perfil ICC."""
import sys, json, struct, time, numpy as np
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad')
from psb69 import PSB
SP='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad'
ROI=(4377,2777,6377,4777); x0,y0,x1,y1=ROI
p=PSB('/Users/USUARI/Desktop/Eclipse 2026/1-PHOTOSHOP/V69.psb')
# ICC
from psd_tools.psd.image_resources import ImageResources
from psd_tools.constants import Resource
with open(p.path,'rb') as f:
    f.seek(26); n=struct.unpack('>I',f.read(4))[0]; f.seek(n,1); res=ImageResources.read(f)
icc=res.get_data(Resource.ICC_PROFILE); open(SP+'/AdobeRGB.icc','wb').write(icc); print('ICC bytes',len(icc),flush=True)
t=time.time(); C=p.composite(); print('compost',C.shape,C.dtype,'%.1fs'%(time.time()-t),flush=True)
np.savez_compressed(SP+'/roi_compost.npz',C=C[y0:y1,x0:x1]); 
# vista sencera del compost a 1/6 (per tenir el llenç sencer)
np.savez_compressed(SP+'/compost_x6.npz',C=C[::6,::6,:3].copy()); del C
for l in p.layers:
    if not l['visible'] and l['id']!=62: continue
    if l['id']==218: continue
    t=time.time(); d={}
    for cid in l['chans']:
        a=p.channel_box(l['id'],cid,ROI,fill=(l['mask']['background']*257 if (cid==-2 and l['mask']) else 0))
        if a is not None: d['c%d'%cid]=a
    np.savez_compressed(SP+f"/roi_L{l['id']}.npz",**d); print('capa',l['id'],l['name'][:30],list(d),'%.1fs'%(time.time()-t),flush=True)
print('FET')
