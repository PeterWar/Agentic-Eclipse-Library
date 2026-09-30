"""Exact channel decoding, existing composition and Photoshop access helpers."""
from common import *
import subprocess
V54=CI/'Earthshine_V54.psb'
V54_SHA='79386f21103b49c16638846e51d70fe1c5e9a29d873b31fcdf1f23dc1886852f'
def channel(layer,cid):
    ix=[int(c.id) for c in layer._record.channel_info].index(cid)
    if cid==-2:m=layer._record.mask_data;w,h=m.right-m.left,m.bottom-m.top
    else:w,h=layer.width,layer.height
    return np.frombuffer(layer._channels[ix].get_data(w,h,16,2),dtype='>u2').reshape(h,w).astype(np.uint16)
def fingerprint(l):
    return dict(name=l.name,bbox=list(l.bbox),opacity=l.opacity,blend=str(l.blend_mode),visible=l.visible,channels=[dict(id=int(i.id),compression=int(c.compression),sha256=hashlib.sha256(c.data).hexdigest()) for i,c in zip(l._record.channel_info,l._channels)],mask=None if l._record.mask_data is None else dict(left=l._record.mask_data.left,top=l._record.mask_data.top,right=l._record.mask_data.right,bottom=l._record.mask_data.bottom,bg=l._record.mask_data.background_color))
def roi(l,c):
    a=channel(l,c)
    if c==-2:m=l._record.mask_data;left,top=m.left,m.top
    else:left,top=l.left,l.top
    return a[Y0-top:Y0-top+N,X0-left:X0-left+N]
def recomposition(s,rgb):
    B=np.stack([roi(s[1],c) for c in range(3)],-1)/65535.;Ba=roi(s[1],-1)/65535.*roi(s[1],-2)/65535.
    S=np.stack([roi(s[7],c) for c in range(3)],-1)/65535.;Sa=roi(s[7],-1)/65535.;La=roi(s[25],-1)/65535.*roi(s[25],-2)/65535.
    Cc=B*Ba[...,None];Ca=Ba;Cb=np.where(Ca[...,None]>0,Cc/np.maximum(Ca[...,None],1e-9),0);mix=(1-Ca[...,None])*S+Ca[...,None]*np.maximum(S,Cb)
    Cc=Sa[...,None]*mix+(1-Sa[...,None])*Cc;Ca=Sa+Ca-Sa*Ca;Cc=La[...,None]*rgb/65535.+(1-La[...,None])*Cc;Ca=La+Ca-La*Ca
    return np.rint(np.where(Ca[...,None]>0,Cc/np.maximum(Ca[...,None],1e-9),0)*65535).astype(np.uint16)
def jsx(js):
    claim();sc='tell application id "com.adobe.Photoshop"\nwith timeout of 3600 seconds\ndo javascript '+json.dumps(js,ensure_ascii=False)+'\nend timeout\nend tell';p=subprocess.run(['osascript','-e',sc],capture_output=True,text=True)
    if p.returncode:raise RuntimeError(p.stderr)
    return p.stdout.strip()
def inventory():
    return jsx('var z=[];for(var i=0;i<app.documents.length;i++){var d=app.documents[i],p="";try{p=d.fullName.fsName;}catch(e){}z.push(d.id+"|"+d.name+"|"+p+"|"+d.saved);} "ACTIVE="+(app.documents.length?app.activeDocument.id:"NONE")+";DIALOGS="+app.displayDialogs.toString()+"\\n"+z.join("\\n");')
