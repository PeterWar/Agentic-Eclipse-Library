from pathlib import Path
import numpy as np,tifffile,json,struct
from psd_tools.psd.image_resources import ImageResources
from psd_tools.constants import Resource
R=Path(__file__).resolve().parents[3];O=R/'4-RESULTATS/v85_regeneracio_20260922';a=np.load(O/'ROI_L3.npz')['RGB'].astype('float32')/65535
with (O/'V84_Pere_input.psb').open('rb') as f:
 f.seek(26);n=struct.unpack('>I',f.read(4))[0];f.seek(n,1);icc=ImageResources.read(f).get_data(Resource.ICC_PROFILE)
rows=[]
for name,start,cap in [('s75c90',.75,.90),('s70c87',.70,.87)]:
 v=a.max(-1);d=np.maximum(v-start,0);vn=np.where(v>start,start+(cap-start)*(1-np.exp(-d/(cap-start))),v);gain=np.divide(vn,v,out=np.ones_like(v),where=v>0);b=np.rint(np.clip(a*gain[...,None],0,1)*65535).astype('uint16')
 tifffile.imwrite(O/('base_'+name+'.tif'),b,photometric='rgb',metadata=None,extratags=[(34675,'B',len(icc),icc,False)])
 rows.append({'name':name,'start':start,'cap':cap,'domain':'encoded AdobeRGB values, pointwise common RGB gain','rule':'C1 shoulder of max(R,G,B), no spatial selection, no radiance claim','max_change_DN16':int(np.max(np.abs(b.astype('int32')-np.rint(a*65535).astype('int32'))))})
(O/'HIGHLIGHT_CANDIDATES.json').write_text(json.dumps(rows,indent=2))
