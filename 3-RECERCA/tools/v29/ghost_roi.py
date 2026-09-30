"""Recompose the two real Sony pointings locally; Vixen stays held out."""
from common import *
import f2
from inspect_inputs import sha

def compose_roi(name,roi,selection):
    run=comu.Run.obre(str(RUNS[name])); ctx=f2.Ctx(run)
    pos=json.loads((RUNS[name]/'4-rebuts/F1.3_registre.json').read_text())['fotogrames']
    kq=json.loads((RUNS[name]/'4-rebuts/F2.2_coherencia.json').read_text())['k']
    y0,y1,x0,x1=roi; shape=(y1-y0,x1-x0,3)
    num=np.zeros(shape,np.float32); den=np.zeros_like(num); sources=[]
    for n in sorted(pos):
        if not selection(n): continue
        v=pos[n]; k=kq.get(n,1.0); rx,ry=ctx.mapes(v['sol_x'],v['sol_y'],roi); fll=f2.mascara_lluna(ctx,v,rx,ry)
        for i,(pl,w) in ctx.plans(n,v['exp']).items():
            oy,ox=ctx.orig[i]; mx=(rx-ox)*.5; my=(ry-oy)*.5; c=comu.IDX_CANAL[i]
            num[...,c]+=cv2.remap(pl*w*k,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)*fll
            den[...,c]+=cv2.remap(w,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)*fll
        sources.append({'name':n,'exposure':v['exp'],'k':k,'path':ctx.ruta[n]})
    out=np.where(den>0,num/np.maximum(den,1e-20),np.nan)
    _,out=comu.lluminancia(out,run.matriu,run.color['guany'])
    return out,den,sources

def metrics(a,b,mask):
    vals=[]
    for sigma in (3,8,24,64):
        aa=a-normgauss(a,mask.astype(np.float32),sigma); bb=b-normgauss(b,mask.astype(np.float32),sigma)
        vals.append({'sigma':sigma,'pearson':float(np.corrcoef(aa[mask],bb[mask])[0,1]),'gain_ls':float(np.dot(aa[mask],bb[mask])/np.dot(aa[mask],aa[mask]))})
    return vals

def main():
    roi=(3988-512,3988+512,2825-512,2825+512); sl=(slice(roi[0],roi[1]),slice(roi[2],roi[3]))
    rep={'roi_y0_y1_x0_x1':roi,'pointings':{}}
    for name,sel in [('A',lambda n:int(n[3:8])<=6987),('B',lambda n:int(n[3:8])>=6991)]:
        log('ghost Sony '+name); a,p,src=compose_roi('sony',roi,sel)
        np.save(CAU/f'ghost_sony_{name}_rgb.npy',a); np.save(CAU/f'ghost_sony_{name}_weight.npy',p)
        rep['pointings'][name]=src
    A=np.load(CAU/'ghost_sony_A_rgb.npy'); B=np.load(CAU/'ghost_sony_B_rgb.npy'); V=np.load(CAU/'vixen_total.npy',mmap_mode='r')[sl]
    y,x=np.ogrid[:1024,:1024]; rr=np.hypot(x-512,y-512)
    band=(rr>210)&(rr<350)&np.all(np.isfinite(A)&np.isfinite(B)&np.isfinite(V),axis=2)
    core=(rr<140)&np.all(np.isfinite(A)&np.isfinite(B)&np.isfinite(V),axis=2)
    rep['held_out_Vixen']=[]
    for c in range(3):
        fa=float(np.median(V[...,c][band]/A[...,c][band])); fb=float(np.median(V[...,c][band]/B[...,c][band]))
        av=A[...,c]*fa; bv=B[...,c]*fb; vv=V[...,c]
        rep['held_out_Vixen'].append({'channel':c,'A_scale':fa,'B_scale':fb,'A_core_relative_median':float(np.median(av[core]/vv[core]-1)),'B_core_relative_median':float(np.median(bv[core]/vv[core]-1)),'A_detail':metrics(np.log(np.maximum(av,1e-8)),np.log(np.maximum(vv,1e-8)),core),'B_detail':metrics(np.log(np.maximum(bv,1e-8)),np.log(np.maximum(vv,1e-8)),core)})
    savejson(CAU/'ghost_roi_receipt.json',rep); log('ghost ROI judged')

if __name__=='__main__':main()
