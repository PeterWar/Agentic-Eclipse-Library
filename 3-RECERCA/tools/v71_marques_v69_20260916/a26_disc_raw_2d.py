"""A26: mapa 2D del disc lunar als RAW Vixen 10 s (3 fotogrames), normalitzat per anells, girat al marc del llenç i centrat al centre lunar: raw_disc_norm_2000.npy (2000×2000, NaN fora del disc)."""
import sys, numpy as np, json
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad')
from scipy.ndimage import map_coordinates, gaussian_filter, rotate, zoom, label, binary_fill_holes
import rawpy
SP='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad'
exec(open(SP+'/a10_lluna_raw.py').read().split('res=[]')[0].split('# 2) fotogrames RAW')[1])
ROT=11.0; RS=456.0; acc=[]; info=[]
for f in ('572A2983.CR3','572A2982.CR3','572A2984.CR3'):
    img=llegeix(f); Lum=img.mean(-1); cx,cy,R,rms=troba_lluna(Lum)
    yy,xx=np.mgrid[0:Lum.shape[0],0:Lum.shape[1]]; rr=np.hypot(xx-cx,yy-cy)
    prof=np.array([np.median(Lum[(rr>=k)&(rr<k+2)]) for k in range(0,int(R*0.99),2)]); rad=np.interp(rr,np.arange(0,int(R*0.99),2)+1,prof)
    norm=np.where(rr<R*0.985,Lum/np.maximum(rad,1e-6),np.nan)
    S=int(R*1.1); sub=norm[int(round(cy))-S:int(round(cy))+S,int(round(cx))-S:int(round(cx))+S]
    # desplaçament subpíxel del centre al retall
    dx,dy=cx-int(round(cx)),cy-int(round(cy))
    esc=RS/R; subz=zoom(np.nan_to_num(sub,nan=1.0),esc,order=1); valid=zoom((~np.isnan(sub)).astype(np.float32),esc,order=1)>0.5
    subr=rotate(subz,ROT,reshape=False,order=1,cval=1.0); validr=rotate(valid.astype(np.float32),ROT,reshape=False,order=1)>0.5
    c=np.array(subr.shape)/2-np.array([dy*esc,dx*esc]); 
    yy2,xx2=np.mgrid[0:2000,0:2000]; ys=yy2-998.41+c[0]; xs=xx2-998.88+c[1]
    out=map_coordinates(subr,[ys.ravel(),xs.ravel()],order=1,cval=np.nan).reshape(2000,2000); vo=map_coordinates(validr.astype(np.float32),[ys.ravel(),xs.ravel()],order=1,cval=0).reshape(2000,2000)>0.5
    out[~vo]=np.nan; acc.append(out); info.append(dict(frame=f,R=float(R),centre=[float(cx),float(cy)],rms=float(rms)))
    print(f,'R',round(R,2),'centre',round(cx,2),round(cy,2))
M=np.nanmean(np.stack(acc),0); np.save(SP+'/raw_disc_norm_2000.npy',M.astype(np.float32)); json.dump(info,open(SP+'/a26_info.json','w'),indent=1)
rr=np.hypot(*np.mgrid[0:2000,0:2000][::-1]-np.array([[[998.88]],[[998.41]]]))
k=np.isfinite(M)&(rr<0.9*RS); print('píxels vàlids dins 0,9 R:',int(k.sum()),'std %.4f'%np.nanstd(M[k]),'mitjana %.4f'%np.nanmean(M[k]))
# comprovació: la correlació amb la capa lunar (passa-baix σ30) dins r<0,85R
from compo import carrega
rgb,a=carrega(30); L=rgb.mean(-1); k2=np.isfinite(M)&(rr<0.85*RS)
hpM=gaussian_filter(np.nan_to_num(M,nan=1.0),30)-gaussian_filter(np.nan_to_num(M,nan=1.0),120); hpL=gaussian_filter(L,30)-gaussian_filter(L,120)
print('correlació passa-banda 30–120 px RAW-disc vs capa lunar (r<0,85R): %.3f'%np.corrcoef(hpM[k2],hpL[k2])[0,1])
from PIL import Image; Image.fromarray(np.uint8(np.clip((gaussian_filter(np.nan_to_num(M,nan=1.0),4)-0.95)/0.1,0,1)*255)).save(SP+'/v_A26_raw_disc_norm.png'); print('fet')
