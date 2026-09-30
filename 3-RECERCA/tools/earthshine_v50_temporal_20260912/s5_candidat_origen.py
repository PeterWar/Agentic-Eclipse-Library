"""S5: candidat V51 a la ROI: base amb la fusió recomposta (S4) a la caixa, màscara de la base oberta on hi ha dada nova (d ≥ −2),
alfa lunar = rampa geomètrica [−1,+1] on la base té dada, 1 on no en té (validesa). Sense cap capa nova."""
import json, numpy as np
from pathlib import Path
from scipy.ndimage import gaussian_filter1d, gaussian_filter
from PIL import Image
ROOT=Path('/Users/USUARI/Downloads/Eclipse 2026'); HERE=Path(__file__).resolve().parent; CAU=HERE/'cau'
OUT=ROOT/'output/earthshine_v50_temporal_20260912'; VIS=OUT/'vistes'; V=ROOT/'output/earthshine_v49_pere_reveal_20260912'
N=1400; CX=699.568111973117; CY=699.6475341408573; RX0,RY0=4677,3077
f4=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy'); th=np.linspace(0,2*np.pi,1440,endpoint=False); f4s=gaussian_filter1d(f4,3.0,mode='wrap')
yy,xx=np.mgrid[0:N,0:N]; r=np.hypot(xx-CX,yy-CY); ang=np.arctan2(yy-CY,xx-CX)%(2*np.pi); F4=np.interp(ang,np.append(th,2*np.pi),np.append(f4s,f4s[0])); d=r-F4; sec12=(ang/(2*np.pi)*12).astype(int)
f=lambda nm,c: np.load(CAU/f'{nm}_ch{c}_roi.npy').astype(np.float64)/65535
B_old=np.stack([f('base',c) for c in (0,1,2)],-1); Bm_old=f('base',-2); S=np.stack([f('l09',c) for c in (0,1,2)],-1); Sa=f('l09',-1); Lr_old=np.stack([f('lun',c) for c in (0,1,2)],-1); Lr=np.load(CAU/'lun_rgb_vel_u16.npy').astype(np.float64)/65535; Lm_old=f('lun',-2); La1=f('lun',-1)
z=np.load(CAU/'s4_recomposicio_box.npz'); Y0,Y1,X0,X1=[int(v) for v in z['box']]; bx=(slice(Y0-RY0,Y1-RY0),slice(X0-RX0,X1-RX0))
u_new=np.load(CAU/'s4_base_new_box_u16.npy').astype(np.float64)/65535; supN=np.load(CAU/'s4_support_new_box.npy')
supO=(np.load(CAU/'s4_base_ref_box_u16.npy')>0).any(-1); dbox=d[bx]
# forats sense dada a ±3 px del limbe: omplerts amb el veí vàlid més proper (declarat); es compten
from scipy.ndimage import distance_transform_edt, binary_dilation
holes=(~supN)&(dbox>=-3)&(dbox<=3)&binary_dilation(supN,iterations=3)
print('forats sense dada a ±3 px del limbe:',int(holes.sum()))
if holes.any():
    idx=distance_transform_edt(~supN,return_distances=False,return_indices=True); u_new=np.where(holes[...,None],u_new[idx[0],idx[1]],u_new); supN=supN|holes
take=supN&(~supO|(dbox<6))   # fora de 6 px del limbe, on la base ja tenia dada, no es toca res
B=B_old.copy(); B[bx]=np.where(take[...,None],u_new,B_old[bx]); np.save(CAU/'base_rgb_new_roi_u16.npy',np.rint(B*65535).astype(np.uint16))
sup=np.zeros((N,N),bool); sup[bx]=supN; avail=np.clip(gaussian_filter(sup.astype(float),0.7),0,1)
Bm_new=np.maximum(Bm_old,avail*np.clip((d+2.0)/1.0,0,1))
ramp=np.clip((1.0-d)/2.0,0,1); wg=np.clip((d+10)/2,0,1)
Lm_geo=ramp   # alfa purament geomètrica: els forats de dada ja són omplerts a la base
Lm_new=wg*Lm_geo+(1-wg)*Lm_old
def compose(Bx,Bm,Lm,Lr=Lr):
    Ca=Bm; Cc=Bx*Bm[...,None]; Cb=np.where(Ca[...,None]>0,Cc/np.maximum(Ca[...,None],1e-9),0)
    mix=(1-Ca[...,None])*S+Ca[...,None]*np.maximum(S,Cb); Cc=Sa[...,None]*mix+(1-Sa[...,None])*Cc; Ca=Sa+Ca-Sa*Ca
    La=La1*Lm; Cc=La[...,None]*Lr+(1-La[...,None])*Cc; Ca=La+Ca-La*Ca
    return np.where(Ca[...,None]>0,Cc/np.maximum(Ca[...,None],1e-9),0),Ca
v49,_=compose(B_old,Bm_old,Lm_old,Lr_old); cand,Ca=compose(B,Bm_new,Lm_new)
pere=np.load(V/'A2_Pere_actual_RGB16.npy').astype(np.float64)/65535; assert np.abs(v49-pere).max()*65535<3.5
np.save(CAU/'cand53_roi_u16.npy',np.rint(cand*65535).astype(np.uint16)); np.save(CAU/'base_mask53_u16.npy',np.rint(Bm_new*65535).astype(np.uint16)); np.save(CAU/'lun_mask53_u16.npy',np.rint(Lm_new*65535).astype(np.uint16))
G=lambda a:a[...,1]*65535; prom=(S[...,0]-S[...,1]>0.25)
rows=[]
for s in range(12):
    m=(sec12==s)&~prom
    rows.append(dict(sector=s,v49=[int(np.median(G(v49)[m&(d>=k)&(d<k+1)])) for k in range(-3,9)],v51=[int(np.median(G(cand)[m&(d>=k)&(d<k+1)])) for k in range(-3,9)]))
for x in rows: print(x)
inner=d<-300; print('interior (d<-300) max diff DN16:',float(np.abs(cand-v49)[inner].max()*65535)); print('base RGB canviada: px',int((np.abs(B-B_old).max(-1)*65535>=2).sum()),' max d on canvia:',float(d[np.abs(B-B_old).max(-1)*65535>=2].max()))
pm=prom&(d>-4)&(d<10); print('protuberàncies més fosques >500DN:',int(((v49-cand)[...,0][pm]*65535>500).sum()),'de',int(pm.sum()))
json.dump(dict(perfils_G=rows,interior_max_DN16=float(np.abs(cand-v49)[inner].max()*65535)),open(OUT/'S5_candidat_origen.json','w'),ensure_ascii=False,indent=1)
print('perfil G V52 per sector d=-60..0 pas 6:'); [print(s_,[int(np.median(G(cand)[(sec12==s_)&(d>=k)&(d<k+6)])) for k in range(-60,0,6)]) for s_ in range(12)]
def png(a,name): Image.fromarray(np.rint(np.clip(a,0,1)*255).astype(np.uint8)).save(VIS/name)
png(cand,'S5_candidat53_ROI_1a1.png')
def crop(img,cx,cy,w,h,k):
    a=img[cy-h//2:cy+h//2,cx-w//2:cx+w//2]; return np.repeat(np.repeat(a,k,0),k,1)
for name,(cx,cy,w,h,k) in dict(dalt=(700,246,300,120,3),baix=(700,1153,300,120,3),esquerra=(246,700,120,300,3),dreta=(1153,700,120,300,3),dalt_esq=(379,379,200,200,3),baix_dreta=(1020,1020,200,200,3),z_dalt=(700,250,100,50,6),z_esquerra=(250,700,50,100,6),z_prom_dalt=(600,255,90,60,8),z_baix=(700,1150,100,50,6),z8_dalt=(735,250,90,40,8),z8_dreta=(1150,700,40,90,8)).items():
    a=crop(v49,cx,cy,w,h,k); c=crop(cand,cx,cy,w,h,k); sep=np.ones((a.shape[0],6,3)); png(np.concatenate([a,sep,c],1),f'S5_{name}_V49_vs_V53.png')
print('S5 fet')
