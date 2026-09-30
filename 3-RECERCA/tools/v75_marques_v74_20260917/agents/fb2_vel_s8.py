"""fb2: el camp del vel S8 (V53) recuperat del PNG 8 bits, calibrat amb S8_vel.json; perfil W(d) per sector: senyal d'altiplà (màxim acumulat) a la taca?"""
import json, numpy as np
from scipy.ndimage import gaussian_filter1d, map_coordinates
from PIL import Image
S4='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/e4f0fbff-bfdf-4da5-a1d0-1bbdf0423383/scratchpad'
R='/Users/USUARI/Desktop/Eclipse 2026'
png=np.array(Image.open(R+'/4-RESULTATS/earthshine_v50_temporal_20260912/vistes/S8_vel_camp.png')).astype(np.float64)
print('png',png.shape,png.dtype,png.min(),png.max())
if png.ndim==3: png=png[...,0]
J=json.load(open(R+'/4-RESULTATS/earthshine_v50_temporal_20260912/S8_vel.json'))
N=1400; CX=699.568111973117; CY=699.6475341408573
edge=np.load(R+'/3-RECERCA/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy'); print('edge',edge.shape,edge.min(),edge.max())
f4s=gaussian_filter1d(edge,3.0,mode='wrap'); th=np.linspace(0,2*np.pi,1440,endpoint=False)
yy,xx=np.mgrid[0:N,0:N]; r=np.hypot(xx-CX,yy-CY); ang=np.arctan2(yy-CY,xx-CX)%(2*np.pi); F4=np.interp(ang,np.append(th,2*np.pi),np.append(f4s,f4s[0])); d=r-F4
# calibratge: mostres del PNG a l'angle exacte del sector k (5k°, convenció S8) i d = −200,−100,−60,−40,−20,−10
ds=[-200,-100,-60,-40,-20,-10,-4,-1]; xs=[]; ys=[]
for row in J['sectors']:
    k=row['sector_5deg']; a=np.deg2rad(5*k); F=np.interp(a,np.append(th,2*np.pi),np.append(f4s,f4s[0]))
    for dd,W in zip(ds,row['W_a']):
        if dd<-70:   # sense refinament
            rad=F+dd; x=CX+rad*np.cos(a); y=CY+rad*np.sin(a); v=map_coordinates(png,[[y],[x]],order=1)[0]; xs.append(v); ys.append(W)
xs=np.array(xs); ys=np.array(ys); k,b=np.polyfit(xs,ys,1); print('calibratge W = %.2f·png + %.1f ; Wmax≈%.0f ; residu rms %.0f DN16 (n=%d)'%(k,b,255*k+b,np.std(ys-(k*xs+b)),len(xs)))
Wmax=255*k; W2=png*k   # el PNG era rint(Wf/Wmax·255): W = png·Wmax/255 ± Wmax/510
print('quantització ±%.0f DN16'%(Wmax/510))
# perfils W(d) per sector de 5° (convenció S8: ang = atan2(y−CY, x−CX), y avall) i també en convenció de la tasca (az = −ang)
sec=(ang/(2*np.pi)*72).astype(int); dcs=np.arange(-300,2,2.0); dc=dcs[:-1]+1
P=np.full((72,len(dc)),np.nan)
ib=((d+300)//2).astype(int); ok=(ib>=0)&(ib<len(dc))
from scipy.ndimage import mean as ndmean
lab=sec[ok]*len(dc)+ib[ok]; cnt=np.bincount(lab,minlength=72*len(dc)); mu=ndmean(W2[ok],labels=lab,index=np.arange(72*len(dc)))
P=np.where(cnt>=4,mu,np.nan).reshape(72,len(dc))
np.savez_compressed(S4+'/fb2_vel_s8.npz',dc=dc,P_sector_s8=P,W2=W2.astype(np.float32),k=k,b=b)
# la taca: az tasca 240–270 ↔ angle S8 90–120 ↔ sectors 18–23; veïns 210–240 ↔ S8 120–150 (24–29); 270–300 ↔ S8 60–90 (12–17)
T=list(range(18,24)); V1=list(range(24,30)); V2=list(range(12,18))
print('W (DN16) per d, mitjana dels sectors: taca | veïns 210-240 | veïns 270-300 | tots')
rows=[]
for dd in range(-260,0,10):
    i=int((dd+300)//2); t=np.nanmean(P[T,i]); v1=np.nanmean(P[V1,i]); v2=np.nanmean(P[V2,i]); al=np.nanmedian(P[:,i])
    rows.append(dict(d=dd,W_taca=round(float(t)),W_veins_210_240=round(float(v1)),W_veins_270_300=round(float(v2)),W_mediana_tots=round(float(al)))); print(dd,round(t),round(v1),round(v2),round(al))
# altiplà: derivada radial de W per sector, trams amb dW/dd ≈ 0 (dins de la quantització) entre d −220 i −60
plateau={}
for s in range(72):
    w=P[s]; seg=(dc>=-220)&(dc<=-60); dw=np.gradient(w,dc); flat=np.isfinite(dw)&seg&(np.abs(dw)<(Wmax/510)/4)
    plateau[s]=int(flat.sum())
print('bins plans (dW/dd<quant/4) per sector 0..71:',[plateau[s] for s in range(72)])
json.dump(dict(calibratge=dict(k=k,b=b,Wmax=255*k+b,quant_DN16=Wmax/510,n=len(xs),rms=float(np.std(ys-(k*xs+b)))),W_per_d=rows,bins_plans_per_sector_s8=plateau,nota='sectors en convenció S8 (angle horari des de +x, y avall); az tasca = (−angle) mod 360; taca = sectors S8 18–23'),open(S4+'/fb2_vel_s8.json','w'),indent=1)
# vista polar del vel: files = sector S8 (0..71), columnes = d −300..0
im=np.nan_to_num(P)/np.nanmax(P); im=np.clip(im*4,0,1)  # ×4 per veure els 0–7000
Image.fromarray(np.uint8(np.kron(im,np.ones((6,3)))*255)).save(S4+'/v_fb2_vel_s8_polar_x4.png'); print('fet')
