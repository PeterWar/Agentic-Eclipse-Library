"""G1 (V79) · Cel continuat dins del triangle sense imatge del V78-FINAL (racó inferior dret, on anirà el logo).
Model: polinomi 2D de 2n ordre per canal ajustat al cel a 20–700 px del triangle; gra = residu del cel reflectit a través de la hipotenusa (mateixes estadístiques); ploma de 24 px fora del triangle amb els píxels originals. Lliurat com a capa nova (b13)."""
import sys, numpy as np, json
NEW='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/6346f583-afd0-49da-9c17-95128c31820e/scratchpad'; sys.path.insert(0,NEW); from psb69 import PSB
from scipy.ndimage import binary_dilation, distance_transform_edt, label, map_coordinates
from PIL import Image
S4='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/e4f0fbff-bfdf-4da5-a1d0-1bbdf0423383/scratchpad'
p=PSB('/Users/USUARI/Desktop/Eclipse 2026/1-PHOTOSHOP/V78-FINAL.psb'); C=p.composite()[...,:3].astype(np.float32)/65535; H,W=C.shape[:2]
L=C.mean(-1); neg=L<0.004; lab,n=label(neg); sizes=np.bincount(lab.ravel())[1:]; T=lab==(int(np.argmax(sizes))+1)
ys,xs=np.nonzero(T); P1=(float(xs[ys==H-1].min()),float(H-1)); P2=(float(W-1),float(ys[xs==W-1].min()))   # extrems de la hipotenusa
m_=(P2[1]-P1[1])/(P2[0]-P1[0]); b_=P1[1]-m_*P1[0]
edge=T&binary_dilation(~T,iterations=1); ey,ex=np.nonzero(edge); k=(ex<W-1)&(ey<H-1); print('triangle %d px · hipotenusa de %s a %s: y = %.4f x + %.1f (angle %.1f°) · residu de la vora: p50 %.1f màx %.1f px'%(T.sum(),P1,P2,m_,b_,np.degrees(np.arctan(m_)),np.median(np.abs(ey[k]-(m_*ex[k]+b_))),np.abs(ey[k]-(m_*ex[k]+b_)).max()))
YY,XX=np.mgrid[0:H,0:W]; T=T|(((m_*XX-YY+b_)/np.sqrt(m_*m_+1))<=4.0)   # semiplà fins a 4 px (distància normal) per sobre de la recta: vora antialiàsada (3 px) i bony inclosos
x0,y0,x1,y1=max(0,xs.min()-900),max(0,ys.min()-900),W,H; sub=C[y0:y1,x0:x1]; Ts=T[y0:y1,x0:x1]; hs,ws=Ts.shape
d_out=distance_transform_edt(~Ts); ref=(~Ts)&(d_out>20)&(d_out<700); yy,xx=np.mgrid[0:hs,0:ws]; xn=(xx-ws/2)/ws; yn=(yy-hs/2)/hs
B=lambda xv,yv: np.c_[np.ones(xv.size),xv,yv,xv**2,xv*yv,yv**2]
suau=np.zeros_like(sub); res=np.zeros_like(sub)
for c in range(3):
    coef=np.linalg.lstsq(B(xn[ref],yn[ref]),sub[...,c][ref],rcond=None)[0]; suau[...,c]=(B(xn.ravel(),yn.ravel())@coef).reshape(hs,ws); res[...,c]=sub[...,c]-suau[...,c]
ty,tx=np.nonzero(Ts); gx=tx+x0; gy=ty+y0; nx,ny=m_,-1.0; nn=nx*nx+ny*ny; b_ref=b_-4.0*np.sqrt(nn)   # reflexió respecte de la vora REAL de la regió (recta desplaçada 4 px enfora)
dist=(nx*gx+ny*gy+b_ref)/nn; rx=gx-2*dist*nx; ry=gy-2*dist*ny
rxl=np.clip(rx-x0,0,ws-1); ryl=np.clip(ry-y0,0,hs-1); valid=~Ts[np.clip(ryl.round().astype(int),0,hs-1),np.clip(rxl.round().astype(int),0,ws-1)]
grain=np.zeros((Ts.sum(),3),np.float32)
from scipy.ndimage import gaussian_filter
res_hp=np.zeros_like(res)
for c in range(3):
    w=(~Ts).astype(np.float32); res_hp[...,c]=res[...,c]-gaussian_filter(np.where(Ts,0,res[...,c]),60)/np.maximum(gaussian_filter(w,60),1e-6)
for c in range(3): grain[:,c]=map_coordinates(np.where(Ts,0,res_hp[...,c]),[ryl,rxl],order=1,mode='nearest')
print('cel de referència %d px · nivell RGB %s · gra std RGB %s (pas alt σ60: %s) · model dins del triangle L %.4f → %.4f · reflexió vàlida %.3f · gra reflectit std %s'%(ref.sum(),sub[ref].mean(0).round(4),res[ref].std(0).round(4),res_hp[ref].std(0).round(4),suau.mean(-1)[Ts].min(),suau.mean(-1)[Ts].max(),valid.mean(),grain.std(0).round(4)))
out=sub.copy(); out[Ts]=np.clip(suau[Ts]+grain,0,1); alpha=np.clip(1-d_out/24.0,0,1); alpha[Ts]=1.0
u=lambda x: np.uint16(np.round(np.clip(x,0,1)*65535))
np.savez_compressed(S4+'/capa_v79_raco.npz',R=u(out[...,0]),G=u(out[...,1]),B=u(out[...,2]),A=u(alpha),compost=u(out))
json.dump({"src":"/Users/USUARI/Desktop/Eclipse 2026/1-PHOTOSHOP/V78-FINAL.psb","dst":"/Users/USUARI/Desktop/Eclipse 2026/1-PHOTOSHOP/V79.psb","rebut":S4+"/b13_escriptura_v79.json","capa":S4+"/capa_v79_raco.npz","nom":"Cel continuat al racó del logo","nom_curt":"Cel continuat al racó del logo","id":229,"roi":[int(x0),int(y0),int(x1),int(y1)],"plantilla":228},open(S4+'/v79_params.json','w'),indent=1,ensure_ascii=False)
comp=C.copy(); comp[y0:y1,x0:x1]=alpha[...,None]*out+(1-alpha[...,None])*sub; sl=(slice(max(0,ys.min()-700),H),slice(max(0,xs.min()-700),W))
a_=np.clip(C[sl],0,1)**(1/1.8); b=np.clip(comp[sl],0,1)**(1/1.8); im=np.hstack([a_,np.ones((a_.shape[0],6,3)),b]); Image.fromarray(np.uint8(im*255)[::2,::2]).save(S4+'/v_G2_raco_abans_despres.png')
a6=np.clip(C[sl].mean(-1)*6,0,1); b6=np.clip(comp[sl].mean(-1)*6,0,1); Image.fromarray(np.uint8(np.hstack([a6,np.ones((a6.shape[0],6)),b6])*255)[::2,::2]).save(S4+'/v_G2_raco_abans_despres_L6.png')
# retall 1:1 a la costura (300×300 al mig de la hipotenusa)
cx,cy=int((P1[0]+P2[0])/2),int((P1[1]+P2[1])/2); s1=(slice(cy-150,cy+150),slice(cx-150,cx+150)); im=np.hstack([np.clip(C[s1]*3,0,1),np.ones((300,4,3)),np.clip(comp[s1]*3,0,1)]); Image.fromarray(np.uint8(im*255)).resize((im.shape[1]*2,600),Image.NEAREST).save(S4+'/v_G2_costura_1a1_x2.png')
print('capa, paràmetres i vistes fets')
