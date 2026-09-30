"""Independent single-exposure angular oracle; no HDR intensity transitions."""
from diagnose import *
import sys
sys.path.insert(0,str(ROOT/'research/tools/v29'))
import common as common29
import f2,comu

def main():
    path=common29.RUNS['vixen'];run=comu.Run.obre(str(path));ctx=f2.Ctx(run)
    pos=json.loads((path/'4-rebuts/F1.3_registre.json').read_text())['fotogrames']
    kq=json.loads((path/'4-rebuts/F2.2_coherencia.json').read_text())['k']
    inv=cv2.invertAffineTransform(common29.COMMON_TO_FINAL)
    nr=1250;nt=4096;rr=np.linspace(445,1700,nr,dtype=np.float32)[:,None]
    th=np.arange(nt,dtype=np.float32)[None,:]*2*np.pi/nt
    fx=(cx+rr*np.cos(th)).astype('float32');fy=(cy+rr*np.sin(th)).astype('float32')
    qx=inv[0,0]*fx+inv[0,1]*fy+inv[0,2];qy=inv[1,0]*fx+inv[1,1]*fy+inv[1,2]
    dx=(qx-ctx.CX)*ctx.k;dy=(qy-ctx.CY)*ctx.k
    k=np.arange(nt//2+1)[None,:]
    def angular(x,m):
        ff=np.fft.rfft(np.where(m,x,0),axis=1);fm=np.fft.rfft(m.astype(float),axis=1);bs=[]
        for sig in [8,32,64,128]:
            gain=np.exp(-.5*(k*sig/rr)**2);den=np.fft.irfft(fm*gain,n=nt,axis=1)
            bs.append(np.fft.irfft(ff*gain,n=nt,axis=1)/np.maximum(den,1e-8))
        return np.where(m,bs[0]-(bs[1]+bs[2]+bs[3])/3,0).astype('float32')
    names=['572A2971.CR3','572A2978.CR3','572A2979.CR3','572A2982.CR3']
    arrays=[];labels=[];rep={}
    roi=(slice(2350,5200),slice(3935,6785));yy,xx=np.ogrid[roi[0],roi[1]]
    r=np.hypot(xx-cx,yy-cy);theta=np.mod(np.arctan2(yy-cy,xx-cx),2*np.pi)
    mx=(theta*nt/(2*np.pi)+1).astype('float32');my=((r-445)*(nr-1)/(1700-445)).astype('float32')
    def back(a):return cv2.remap(np.concatenate([a[:,-1:],a,a[:,:1]],axis=1).astype('float32'),mx,my,cv2.INTER_LINEAR)
    stack=cv2.remap(load('vixen_total')[...,1],fx,fy,cv2.INTER_LINEAR)
    for name in names:
        v=pos[name];rx=ctx.ca*dx+ctx.sa*dy+v['sol_x'];ry=-ctx.sa*dx+ctx.ca*dy+v['sol_y']
        lunar=f2.mascara_lluna(ctx,v,rx,ry)
        num=np.zeros((nr,nt,3),np.float32);den=np.zeros_like(num)
        for i,(pl,w) in ctx.plans(name,v['exp']).items():
            oy,ox=ctx.orig[i];a=((rx-ox)*.5).astype('float32');b=((ry-oy)*.5).astype('float32');c=comu.IDX_CANAL[i]
            num[...,c]+=cv2.remap(pl*w*kq[name],a,b,cv2.INTER_LINEAR)*lunar
            den[...,c]+=cv2.remap(w,a,b,cv2.INTER_LINEAR)*lunar
        cam=num/np.maximum(den,1e-15);_,total=comu.lluminancia(cam,run.matriu,run.color['guany'])
        good=np.all(den>v['exp']*.02,axis=2)&np.all(total>0,axis=2)
        band=angular(np.log(np.maximum(total[...,1],1e-8)),good)
        image=.5+.5*np.tanh(back(band)/.03);image[back(good.astype('float32'))<.995]=.5
        arrays.append(image);labels.append(f'{name}: {v["exp"]} s; gris=sense dada')
        np.save(HERE/(name+'.polar_G.npy'),total[...,1]);np.save(HERE/(name+'.polar_valid.npy'),good)
        ratio=np.where(good& (stack>0),np.log(np.maximum(total[...,1],1e-8)/np.maximum(stack,1e-8)),0)
        np.save(HERE/(name+'.logratio.npy'),ratio)
        rep[name]={'exposure':v['exp'],'valid':int(good.sum()),'ratio_p10_p50_p90':np.percentile(ratio[good],[10,50,90]).tolist()}
        print(name,rep[name],flush=True)
    panel(arrays,labels,'ORACLE_01_fotogrames.png',700)
    (HERE/'frame_oracle_receipt.json').write_text(json.dumps(rep,indent=2)+'\n')
if __name__=='__main__':main()
