"""Check whether the remaining merged-source discrepancy is a moved perles layer.
Integer translations only, frozen other layers, no tone or edge-radius fitting.
"""
from common50 import *
from PIL import Image
layers={k:dict(np.load(OUT/f'L4_original_{k}.npz')) for k in ['12','11','10','09']};target=np.load(OUT/'L0_09_RGB16.npy').astype(float);y,x=np.mgrid[:N,:N];r=np.hypot(x-CX,y-CY)
above=np.zeros_like(target);trans=np.ones((N,N))
for k in ['11','10','09']:
 z=layers[k];w=z['alpha'].astype(float)*z['mask']/65535**2;above=above*(1-w[...,None])+z['rgb']*w[...,None];trans*=1-w
select=(r>425)&(r<480)&(trans>.1);ys,xs=np.where(select);keep=np.arange(len(ys))%3==0;ys=ys[keep];xs=xs[keep];train=(np.arctan2(ys-CY,xs-CX)%(2*np.pi)*12/np.pi).astype(int)%2==0
z=layers['12'];base=z['rgb'].astype(float)*((z['alpha'].astype(float)*z['mask']/65535**2)[...,None]);rows=[]
for dy in range(-8,9):
 for dx in range(-8,9):
  pred=above[ys,xs]+base[ys-dy,xs-dx]*trans[ys,xs,None];delta=abs(pred-target[ys,xs]);rows.append(dict(dx=dx,dy=dy,train_mae=float(delta[train].mean()),reserved_mae=float(delta[~train].mean())))
rows.sort(key=lambda z:z['train_mae']);best=rows[0];dx=best['dx'];dy=best['dy'];pred=above+np.roll(base,(dy,dx),(0,1))*trans[...,None];np.save(OUT/'L6_reconstructed09.npy',np.rint(pred).astype(np.uint16));regs=[]
for lo,hi in [(0,350),(435,449),(449,454),(454,460),(460,480),(480,650)]:
 u=(r>=lo)&(r<hi);delta=abs(pred-target)[u];regs.append(dict(radius=[lo,hi],mae=float(delta.mean()),p95=float(np.percentile(delta,95)),p99=float(np.percentile(delta,99)),max=float(delta.max())))
save('L6_inner_identity.json',dict(method=__doc__,best=best,regions=regs,top10=rows[:10]));print(json.dumps(dict(best=best,regions=regs),indent=2),flush=True)
ims=[Image.fromarray((np.clip(z,0,65535).astype(np.uint16)>>8).astype('uint8')) for z in [target,pred]]
for name,box in {'right':(1040,430,1220,940),'left':(165,420,365,960),'top':(370,170,990,365)}.items():
 a,b=[im.crop(box) for im in ims];out=Image.new('RGB',(a.width*2,a.height));out.paste(a,(0,0));out.paste(b,(a.width,0));out.save(OUT/f'L6_{name}.png')
