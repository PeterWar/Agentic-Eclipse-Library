"""Compose directly CFA -> the existing PSB grid, one interpolation only.

No FOV change: 10551x7506, same M fitted against Pere's immutable layers.
The old intermediate rectangle is not a physical coverage boundary.
"""
from common import *
import f2

def main():
    assert FINAL_GRID
    inv=cv2.invertAffineTransform(COMMON_TO_FINAL)
    yy,xx=np.ogrid[:H,:W];cx=(inv[0,0]*xx+inv[0,1]*yy+inv[0,2]).astype(np.float32);cy=(inv[1,0]*xx+inv[1,1]*yy+inv[1,2]).astype(np.float32)
    r,_=coords();rep={'grid':[W,H],'sun_xy':SUN_XY,'common_to_final':COMMON_TO_FINAL,'resampling':'one bilinear CFA subplane -> existing PSB grid; no LDIC image warp','runs':{}}
    for name in ('vixen','sony'):
        path=RUNS[name];run=comu.Run.obre(str(path));ctx=f2.Ctx(run)
        pos=json.loads((path/'4-rebuts/F1.3_registre.json').read_text())['fotogrames'];kq=json.loads((path/'4-rebuts/F2.2_coherencia.json').read_text())['k'];names=sorted(pos)
        groups=['all'] if name=='vixen' else ['A','B','even','odd']
        num={g:np.zeros((H,W,3),np.float32) for g in groups};den={g:np.zeros((H,W,3),np.float32) for g in groups}
        for j,n in enumerate(names):
            v=pos[n];k=kq.get(n,1);dx=(cx-ctx.CX)*ctx.k;dy=(cy-ctx.CY)*ctx.k;rx=ctx.ca*dx+ctx.sa*dy+v['sol_x'];ry=-ctx.sa*dx+ctx.ca*dy+v['sol_y'];fl=f2.mascara_lluna(ctx,v,rx,ry)
            gs=['all'] if name=='vixen' else [('A' if int(n[3:8])<=6987 else 'B'),('even' if j%2==0 else 'odd')]
            for i,(pl,w) in ctx.plans(n,v['exp']).items():
                oy,ox=ctx.orig[i];mx=(rx-ox)*.5;my=(ry-oy)*.5;c=comu.IDX_CANAL[i]
                nn=cv2.remap(pl*w*k,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)*fl
                dd=cv2.remap(w,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)*fl
                for g in gs:num[g][...,c]+=nn;den[g][...,c]+=dd
            if j%10==0 or j==len(names)-1:log(f'final grid {name} {j+1}/{len(names)}')
        del dx,dy,rx,ry,fl,nn,dd,mx,my
        for g in groups:
            d=den.pop(g);cam=np.where(d>0,num[g]/np.maximum(d,1e-20),np.nan);del num[g]
            valid=np.all(np.isfinite(cam)&(cam>0)&(d>0),axis=2)
            _,total=comu.lluminancia(cam,run.matriu,run.color['guany']);del cam
            tag=name if g=='all' else f'{name}_{g}'
            np.save(CAU/f'{tag}_total.npy',np.nan_to_num(total,nan=0).astype(np.float32) if g=='all' else total)
            np.save(CAU/f'{tag}_weights.npy',d)
            if g=='all':
                support=(comu.mascara_dada(d[...,1],r)&valid)|(valid&(r<1.12*RS));np.save(CAU/f'{name}_support.npy',support);np.save(CAU/f'{name}_weight_G.npy',d[...,1])
            del d,total,valid
        if name=='sony':
            aa=np.load(CAU/'sony_A_weights.npy',mmap_mode='r');bb=np.load(CAU/'sony_B_weights.npy',mmap_mode='r');p=aa[...,1]+bb[...,1]
            valid=np.all((aa+bb)>0,axis=2);support=(comu.mascara_dada(p,r)&valid)|(valid&(r<1.12*RS));np.save(CAU/'sony_support.npy',support);np.save(CAU/'sony_weight_G.npy',p)
            del aa,bb,p,valid,support
        # Sky is needed only for the unchanged base convention near the limb
        # and ghost. It is never the source for V29 detail filters.
        oldsky=np.load(HERE/'cau'/f'{name}_sky.npy',mmap_mode='r')
        sky=np.stack([cv2.warpAffine(oldsky[...,i],COMMON_TO_FINAL,(W,H),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT) for i in range(3)],axis=2)
        np.save(CAU/f'{name}_sky.npy',sky);del sky,oldsky,ctx
        rep['runs'][name]={'path':str(path),'frames':names,'groups':groups,'matrix':run.matriu,'gain':run.color['guany']}
    savejson(CAU/'direct_grid_receipt.json',rep);log('direct final grid sources ready')

if __name__=='__main__':main()
