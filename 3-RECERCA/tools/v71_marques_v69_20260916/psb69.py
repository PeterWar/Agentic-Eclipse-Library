"""Lector lleuger de PSB (només capçaleres + canals a demanda). Sense carregar els 7 GB."""
import struct, zlib, json, logging, numpy as np
from psd_tools.psd.layer_and_mask import LayerRecord
from psd_tools.psd.tagged_blocks import TaggedBlock
from psd_tools.constants import Tag
from psd_tools.compression import decode_rle
logging.getLogger('psd_tools').setLevel(logging.ERROR)
BIG_KEYS={x.value for x in TaggedBlock._BIG_KEYS}

def _rf(f,fmt):
    n=struct.calcsize('>'+fmt); v=f.read(n)
    if len(v)!=n: raise ValueError('short read')
    return struct.unpack('>'+fmt,v)

class PSB:
    def __init__(self,path):
        self.path=path
        with open(path,'rb') as f:
            sig,version=_rf(f,'4sH'); assert sig==b'8BPS' and version==2
            f.seek(12); self.channels,self.height,self.width,self.depth,self.mode=_rf(f,'HIIHH')
            for _ in range(2):
                n=_rf(f,'I')[0]; f.seek(n,1)
            n=_rf(f,'Q')[0]; end=f.tell()+n; self.image_data_offset=end
            n=_rf(f,'Q')[0]; body=f.tell() if n else None; f.seek(n,1)
            if f.tell()+4<=end:
                n=_rf(f,'I')[0]; f.seek(n,1)
            while f.tell()+12<=end:
                sig,key=_rf(f,'4s4s'); fmt='Q' if key in BIG_KEYS else 'I'
                n=_rf(f,fmt)[0]; start=f.tell()
                if key in (b'Lr16',b'Lr32'): body=start
                f.seek(start+(n+3)//4*4)
            f.seek(body); count=abs(_rf(f,'h')[0])
            recs=[LayerRecord.read(f,version=2) for _ in range(count)]
            pos=f.tell(); self.layers=[]
            for i,r in enumerate(recs):
                lid=int(r.tagged_blocks.get_data(Tag.LAYER_ID)); md=r.mask_data
                ch={}
                for c in r.channel_info:
                    ch[int(c.id)]=(pos,c.length); pos+=c.length
                self.layers.append(dict(i=i,id=lid,name=r.name,left=r.left,top=r.top,right=r.right,bottom=r.bottom,
                    visible=bool(r.flags.visible),opacity=int(r.opacity),blend=r.blend_mode.name,clipping=int(r.clipping),
                    mask=None if md is None else dict(left=md.left,top=md.top,right=md.right,bottom=md.bottom,background=int(md.background_color),disabled=bool(md.flags.mask_disabled)),
                    chans=ch))
    def layer(self,lid):
        return next(l for l in self.layers if l['id']==lid)
    def _decode(self,raw,w,h):
        code=struct.unpack('>H',raw[:2])[0]; d=raw[2:]
        if code==0: return np.frombuffer(d,'>u2').reshape(h,w)
        if code==1: return np.frombuffer(decode_rle(d,w,h,16,2),'>u2').reshape(h,w)
        if code==2: return np.frombuffer(zlib.decompress(d),'>u2').reshape(h,w)
        if code==3: return np.cumsum(np.frombuffer(zlib.decompress(d),'>u2').reshape(h,w),axis=1,dtype=np.uint16)
        raise ValueError(code)
    def channel(self,lid,cid):
        """Canal sencer d'una capa (uint16, big-endian → natiu), amb (left, top) del seu marc."""
        l=self.layer(lid)
        if cid not in l['chans']: return None,None
        if cid==-2:
            m=l['mask']; w,h=m['right']-m['left'],m['bottom']-m['top']; org=(m['left'],m['top'])
        else:
            w,h=l['right']-l['left'],l['bottom']-l['top']; org=(l['left'],l['top'])
        off,n=l['chans'][cid]
        with open(self.path,'rb') as f:
            f.seek(off); raw=f.read(n)
        if w==0 or h==0: return np.zeros((h,w),np.uint16),org
        return self._decode(raw,w,h).astype(np.uint16),org
    def channel_box(self,lid,cid,box,fill=0):
        """Canal retallat a box=(x0,y0,x1,y1) del llenç; fora del marc de la capa, `fill`."""
        x0,y0,x1,y1=box; out=np.full((y1-y0,x1-x0),fill,np.uint16); a,org=self.channel(lid,cid)
        if a is None: return None
        x,y=org; h,w=a.shape; xa,ya=max(x,x0),max(y,y0); xb,yb=min(x+w,x1),min(y+h,y1)
        if xb>xa and yb>ya: out[ya-y0:yb-y0,xa-x0:xb-x0]=a[ya-y:yb-y,xa-x:xb-x]
        return out
    def composite(self):
        """Imatge fusionada (canals planars) sencera, uint16 (H,W,C)."""
        with open(self.path,'rb') as f:
            f.seek(self.image_data_offset); code=struct.unpack('>H',f.read(2))[0]; d=f.read()
        W,H,C=self.width,self.height,self.channels
        if code==0: a=np.frombuffer(d,'>u2')
        elif code==1: a=np.frombuffer(decode_rle(d,W,H*C,16,2),'>u2')
        elif code==2: a=np.frombuffer(zlib.decompress(d),'>u2')
        elif code==3: a=np.cumsum(np.frombuffer(zlib.decompress(d),'>u2').reshape(H*C,W),axis=1,dtype=np.uint16)
        return np.moveaxis(a.reshape(C,H,W),0,-1).astype(np.uint16)
