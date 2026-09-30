"""Recompose the two Sony pointings without changing raw calibration or k.

Necessary diagnostic for the visible straight footprint edge in the first
V29 pilot. Runs are read only. Native canvas, no crop/resizing of deliverable.
"""
from common import *
import f2

def main():
    path=RUNS['sony']; run=comu.Run.obre(str(path));ctx=f2.Ctx(run)
    pos=json.loads((path/'4-rebuts/F1.3_registre.json').read_text())['fotogrames'];kq=json.loads((path/'4-rebuts/F2.2_coherencia.json').read_text())['k']
    rep={'groups':{},'unchanged':'F0 calibration, F1.3 registration, F2.2 k, lunar mask per frame'}
    groups=[('A',lambda n:int(n[3:8])<=6987),('B',lambda n:int(n[3:8])>=6991)]
    if '--halves' in sys.argv:
        names=sorted(pos);groups=[('even',lambda n:names.index(n)%2==0),('odd',lambda n:names.index(n)%2==1)]
    for group,selection in groups:
        num=np.zeros((H,W,3),np.float32);den=np.zeros_like(num);src=[]
        for n in sorted(pos):
            if not selection(n):continue
            v=pos[n];k=kq.get(n,1);cai=ctx.caixa(v['sol_x'],v['sol_y']);y0,y1,x0,x1=cai;sl=(slice(y0,y1),slice(x0,x1))
            rx,ry=ctx.mapes(v['sol_x'],v['sol_y'],cai);fll=f2.mascara_lluna(ctx,v,rx,ry)
            for i,(pl,w) in ctx.plans(n,v['exp']).items():
                oy,ox=ctx.orig[i];mx=(rx-ox)*.5;my=(ry-oy)*.5;c=comu.IDX_CANAL[i]
                num[sl+(c,)]+=cv2.remap(pl*w*k,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)*fll
                den[sl+(c,)]+=cv2.remap(w,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)*fll
            src.append(n);log(group+' '+n)
        cam=np.where(den>0,num/np.maximum(den,1e-20),np.nan);del num,rx,ry,fll,mx,my
        _,total=comu.lluminancia(cam,run.matriu,run.color['guany']);del cam
        np.save(CAU/f'sony_{group}_total.npy',total);np.save(CAU/f'sony_{group}_weights.npy',den)
        rep['groups'][group]=src;del total,den
    savejson(CAU/('sony_halves.json' if '--halves' in sys.argv else 'sony_pointings.json'),rep);log('pointings done')

if __name__=='__main__':main()
