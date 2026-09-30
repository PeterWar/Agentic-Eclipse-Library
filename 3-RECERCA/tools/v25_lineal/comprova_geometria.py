import json, numpy as np, cv2, importlib.util
spec=importlib.util.spec_from_file_location("e2","etapa2_geometria_v23.py"); e2=importlib.util.module_from_spec(spec); spec.loader.exec_module(e2)
from psd_tools import PSDImage
G=json.load(open("cau_v25/geometria_v23.json")); M1=np.array(G["M_llenc_a_v23"])
base=np.load("cau_v25/base_B_rgb16.npy").astype(np.float32)/65535.0; mf=np.load("cau_v25/mascara_fusio.npy")
Lb=(base[...,0]+2*base[...,1]+base[...,2])/4.0; del base
Hl,Wl=mf.shape; yy,xx=np.mgrid[0:Hl,0:Wl].astype(np.float32); rl=np.hypot(yy-Hl/2,xx-Wl/2)/440.603; del yy,xx
hb=e2.prep(Lb, mf&(rl>1.05)&(rl<6.0),6.0); del Lb
V24="/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/CapesTotalsV24.psb"
psd=PSDImage.open(V24); Wp,Hp=psd.width,psd.height
hbw=cv2.warpAffine(hb,M1,(Wp,Hp),flags=cv2.INTER_LINEAR)
yy,xx=np.mgrid[0:Hp,0:Wp].astype(np.float32); rp=np.hypot(yy-3774.741,xx-5361.877)/440.6; del yy,xx
out={}
for idx in (3,2,12):
    l=list(psd)[idx]; x0,y0,x1,y1=l.bbox; arr=l.numpy("color"); msk=l.numpy("mask") if l.mask else None
    Lp=np.zeros((Hp,Wp),np.float32); Mp=np.zeros((Hp,Wp),bool); Lp[y0:y1,x0:x1]=(arr[...,0]+2*arr[...,1]+arr[...,2])/4.0; Mp[y0:y1,x0:x1]=True; del arr
    if msk is not None:
        mx0,my0,mx1,my1=l.mask.bbox; MM=np.zeros((Hp,Wp),bool); MM[my0:my1,mx0:mx1]=msk[...,0]>0.5; Mp&=MM; del msk
    Mp&=Lp>0.02
    print(f"capa {l.name[:24]}: màscara {Mp.mean():.4f} · radis p5 {np.percentile(rp[Mp],5):.2f} p50 {np.percentile(rp[Mp],50):.2f} p95 {np.percentile(rp[Mp],95):.2f} R☉", flush=True)
    hp=e2.prep(Lp,Mp,6.0); del Lp
    res=[]
    for (yc,xc) in [(3774-900,5362-900),(3774-900,5362+900),(3774+900,5362-900),(3774+900,5362+900),(3774,5362-1100),(3774,5362+1100),(3774-1100,5362),(3774+1100,5362),(3774-1600,5362-1600),(3774+1600,5362+1600),(3774,5362-2000),(3774,5362+2000)]:
        a=hp[yc-384:yc+384,xc-384:xc+384]; b=hbw[yc-384:yc+384,xc-384:xc+384]
        cob=float((np.abs(a)>0).mean())
        if cob<0.25: continue
        dy,dx,r=e2.fase(a,b); res.append((yc,xc,round(cob,2),round(float(dy),2),round(float(dx),2),round(float(r),1)))
    for t in res: print("   ",t)
    if len(res)>=3:
        X=np.array([[1,t[1]-5361.877,t[0]-3774.741] for t in res],float); cx_=np.linalg.lstsq(X,np.array([t[4] for t in res]),rcond=None)[0]; cy_=np.linalg.lstsq(X,np.array([t[3] for t in res]),rcond=None)[0]
        rr=np.sqrt(np.mean([t[3]**2+t[4]**2 for t in res]))
        print(f"  → rotació residual {np.degrees(0.5*(cy_[1]-cx_[2])):.4f}° · escala residual {0.5*(cx_[1]+cy_[2]):.5f} · rms offset {rr:.2f} px · mitjana (dy,dx) ({np.mean([t[3] for t in res]):.2f},{np.mean([t[4] for t in res]):.2f})", flush=True)
        out[l.name[:24]]={"finestres":res,"rot_res_deg":float(np.degrees(0.5*(cy_[1]-cx_[2]))),"esc_res":float(0.5*(cx_[1]+cy_[2])),"rms_px":float(rr)}
json.dump(out,open("cau_v25/comprova_geometria.json","w"),indent=1)
