from common60 import *
rows=json.loads((O/'A0_freeze.json').read_text())['layers']
def read(i,c):
 p=O/'arrays'/f'L{i:02d}_C{c}_roi.npy'
 return np.load(p).astype('float64')/65535 if p.exists() else None
def render(changes=None,masks=None,hidden=None,include_moon=True):
 changes=changes or {};masks=masks or {};hidden=set(hidden or []);out=np.zeros((2000,2000,3),np.float64)
 for i,l in enumerate(rows[:30]):
  if i in hidden or not l['visible'] or (i==29 and not include_moon):continue
  g=read(i,1);rgb=changes.get(i)
  if rgb is None:
   if i in [9,29]:rgb=np.stack([read(i,c) for c in range(3)],-1)
   elif 11<=i<=26:rgb=np.repeat(g[...,None],3,-1)
   else:raise ValueError(i)
  if rgb.ndim==2:rgb=np.repeat(rgb[...,None],3,-1)
  a=read(i,-1);a=np.ones(g.shape) if a is None else a;m=masks.get(i,read(i,-2))
  if m is not None and not l['mask_flags']['mask_disabled']:a=a*m
  a=a*(l['opacity']/255);mode=l['blend'];F=rgb
  if mode=='BlendMode.MULTIPLY':res=out*F
  elif mode=='BlendMode.OVERLAY':res=np.where(out<.5,2*out*F,1-2*(1-out)*(1-F))
  elif mode=='BlendMode.NORMAL':res=F
  else:raise ValueError(mode)
  out=out+(res-out)*a[...,None]
 return np.clip(out,0,1)
