from common58 import *
import cv2,sys,copy,gc
from psd_tools import PSDImage
from psd_tools.psd.layer_and_mask import ChannelInfo,ChannelData
from psd_tools.constants import Compression,Tag,Resource
claim();C=O/'prepared_layers';C.mkdir(exist_ok=True);s=PSDImage.open(O/'V57_Pere_input.psb');rep={};B2=json.loads((O/'B2_geometry_local.json').read_text());B5=json.loads((O/'B5_lroc_local.json').read_text());B6=json.loads((O/'B6_remaining_layers.json').read_text());moonmask=chan(s[29],-2);mb=s[29]._record.mask_data;np.save(C/'moon_physical_mask_u16.npy',moonmask)
def matrix(p,center):
 dx,dy,deg=p[:3];sc=1+p[3] if len(p)==4 else 1.;t=np.deg2rad(deg);A=sc*np.array([[np.cos(t),-np.sin(t)],[np.sin(t),np.cos(t)]]);return np.c_[A,np.array(center)+[dx,dy]-A@center]
def warp(a,bbox,dst,M,c):
 MM=M.copy();MM[:,2]+=M[:,:2]@np.array(bbox[:2])-np.array(dst[:2]);return cv2.warpAffine(a,MM,(dst[2]-dst[0],dst[3]-dst[1]),flags=cv2.INTER_LINEAR if c<0 else cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT,borderValue=0)
def moon_at(bbox):
 x0,y0,x1,y1=bbox;q=np.zeros((y1-y0,x1-x0),np.uint16);xa=max(x0,mb.left);ya=max(y0,mb.top);xb=min(x1,mb.right);yb=min(y1,mb.bottom)
 if xb>xa and yb>ya:q[ya-y0:yb-y0,xa-x0:xb-x0]=moonmask[ya-mb.top:yb-mb.top,xa-mb.left:xb-mb.left]
 return q
trans={i:B2[str(i)]['transform_output_dx_dy_deg_scale_delta'] for i in range(1,7)};trans[28]=B5['logFalse_3_12']['transform_output_dx_dy_deg_scale_delta'];trans[27]=B6['27']['transform_output_dx_dy_deg_scale_delta']
for i,p in trans.items():
 l=s[i];center=[5376.5681,3776.6475] if i>=27 else [CX,CY];M=matrix(p,center);bb=l.bbox;corn=np.array([[bb[0],bb[1],1],[bb[2],bb[1],1],[bb[0],bb[3],1],[bb[2],bb[3],1]])@M.T;dst=(int(np.floor(corn[:,0].min()))-2,int(np.floor(corn[:,1].min()))-2,int(np.ceil(corn[:,0].max()))+2,int(np.ceil(corn[:,1].max()))+2)
 if i>=27:dst=bb # opaque lunar reference support is central; unchanged rectangular canvas, off-canvas black unchanged.
 rows=[]
 for ci in l._record.channel_info:
  c=int(ci.id);a=chan(l,c);sb=(l._record.mask_data.left,l._record.mask_data.top,l._record.mask_data.right,l._record.mask_data.bottom) if c==-2 else bb;v=warp(a,sb,dst,M,c)
  if c==-2 and i==1:
   yy,xx=np.ogrid[dst[1]:dst[3],dst[0]:dst[2]];rr=np.hypot(xx-5376.5681,yy-3776.6475);w=np.clip((480-rr)/15,0,1);w=w*w*(3-2*w);physical=65535-moon_at(dst);v=np.round(v*(1-w)+physical*w).astype('uint16')
  if c==-2 and i>=27:v=moon_at(dst)
  np.save(C/f'L{i:02d}_C{c}.npy',v);rows.append(dict(channel=c,shape=v.shape,sha256=sha(C/f'L{i:02d}_C{c}.npy')));del a,v;gc.collect()
 rep[str(i)]=dict(transform=p,matrix=M,bbox=dst,channels=rows,mask='physical V56 in inner limb; original outer selection' if i==1 else 'physical V56 comparison contour' if i>=27 else 'transformed with RGB');print('prepared',i,p,flush=True)
# Preserve every channel of12 and the accepted V56 image, mask and geometry.
rep['identity_preserved']=[0,7,8,9,29];save('G0_prepared_layers.json',rep)
