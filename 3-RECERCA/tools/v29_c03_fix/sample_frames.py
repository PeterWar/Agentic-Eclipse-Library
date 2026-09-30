"""Sparse same-canvas native-channel samples for global photometric offsets."""
from pathlib import Path
import os,sys,json,time
os.environ['V29_FINAL_GRID']='1'
ROOT=Path('/Users/USUARI/Downloads/Eclipse 2026')
sys.path.insert(0,str(ROOT/'research/tools/v29'))
from common import *
import f2
DEST=Path(__file__).parent

def main():
    step=24;ys=np.arange(12,H,step,dtype=np.float32);xs=np.arange(12,W,step,dtype=np.float32)
    xx,yy=np.meshgrid(xs,ys);inv=cv2.invertAffineTransform(COMMON_TO_FINAL)
    qx=inv[0,0]*xx+inv[0,1]*yy+inv[0,2];qy=inv[1,0]*xx+inv[1,1]*yy+inv[1,2]
    for tag in ('vixen','sony'):
        path=RUNS[tag];run=comu.Run.obre(str(path));ctx=f2.Ctx(run)
        pos=json.loads((path/'4-rebuts/F1.3_registre.json').read_text())['fotogrames'];kq=json.loads((path/'4-rebuts/F2.2_coherencia.json').read_text())['k'];names=sorted(pos)
        a=np.lib.format.open_memmap(DEST/f'{tag}_samples.npy',mode='w+',dtype='float32',shape=(len(names),len(ys),len(xs),3));conf=np.lib.format.open_memmap(DEST/f'{tag}_confidence.npy',mode='w+',dtype='float32',shape=a.shape)
        dx=(qx-ctx.CX)*ctx.k;dy=(qy-ctx.CY)*ctx.k
        meta=[]
        for j,name in enumerate(names):
            v=pos[name];rx=(ctx.ca*dx+ctx.sa*dy+v['sol_x']).astype('float32');ry=(-ctx.sa*dx+ctx.ca*dy+v['sol_y']).astype('float32')
            lunar=f2.mascara_lluna(ctx,v,rx,ry)
            num=np.zeros(xx.shape+(3,),np.float32);den=np.zeros_like(num)
            for i,(pl,w) in ctx.plans(name,v['exp']).items():
                oy,ox=ctx.orig[i];mx=((rx-ox)*.5).astype('float32');my=((ry-oy)*.5).astype('float32');c=comu.IDX_CANAL[i]
                num[...,c]+=cv2.remap(pl*w*kq[name],mx,my,cv2.INTER_LINEAR)*lunar
                den[...,c]+=cv2.remap(w,mx,my,cv2.INTER_LINEAR)*lunar
            a[j]=num/np.maximum(den,1e-20);conf[j]=den/(v['exp']*np.array([1,2,1],np.float32))
            meta.append({'name':name,'exposure':v['exp'],'k':kq[name]})
            if j%8==0 or j==len(names)-1:log(f'samples {tag} {j+1}/{len(names)}')
        a.flush();conf.flush();savejson(DEST/f'{tag}_sample_meta.json',{'frames':meta,'ys':ys,'xs':xs,'matrix':run.matriu,'gain':run.color['guany'],'coordinate_grid':'same PSB; sparse diagnostic sampling only'})
        del a,conf,ctx
if __name__=='__main__':main()
