import numpy as np, json, sys
from scipy import ndimage as ndi
from PIL import Image, ImageDraw
import fa_lib as F
sys.path.insert(0,F.S4); import compo74 as c
C,a,P=c.recompon(exclou=(222,),retorna_passos=True)
C71=np.load(F.S4+'/roi71_C_sensemarques.npy'); L71=F.Lstar(C71)
Lf=F.Lstar(C)
azi=np.floor(F.AZ*2)/2  # cel·les de 0,5°
# ---- (A) bandes azimutals per marca
res={}
for k in F.MARKS:
    m=F.mask(k); r0,r1=F.RR[m].min(),F.RR[m].max(); az0,az1=F.AZ[m].min(),F.AZ[m].max()
    band=(F.RR>=r0)&(F.RR<=r1); w0,w1=az0-20,az1+20
    cells=np.arange(np.floor(w0*2)/2,w1,0.5)
    def prof(L):
        return np.array([float(L[band&(azi==cc)].mean()) if (band&(azi==cc)).any() else np.nan for cc in cells])
    out={'cells':cells.tolist(),'r':[float(r0),float(r1)],'az':[float(az0),float(az1)]}
    for lid,nom in ((3,'base'),(42,'nrgf'),(53,'achf'),(46,'rhef'),(56,'wow'),(30,'p30'),(76,'p76'),(202,'final')):
        out[nom]=prof(F.Lstar(P[lid][0])).tolist()
    out['v71']=prof(L71).tolist()
    # mesura: dins la marca (cel·les az0..az1) vs. el suavitzat azimutal σ=6° de la mateixa banda: profunditat de banda
    fin=np.array(out['final']); sm=ndi.gaussian_filter1d(np.nan_to_num(fin),12); dev=fin-sm
    inm=(cells>=az0)&(cells<=az1)
    out['banda_final']=dict(dev_min_marca=float(np.nanmin(dev[inm])),dev_mean_marca=float(np.nanmean(dev[inm])),dev_min_fora=float(np.nanmin(dev[~inm])),dev_std_fora=float(np.nanstd(dev[~inm])))
    v71=np.array(out['v71']); dev71=v71-ndi.gaussian_filter1d(np.nan_to_num(v71),12)
    out['banda_v71']=dict(dev_min_marca=float(np.nanmin(dev71[inm])),dev_mean_marca=float(np.nanmean(dev71[inm])))
    res[k]=out
    print(k,'r %.0f-%.0f az %.0f-%.0f'%(r0,r1,az0,az1),'banda final',{q:round(v,2) for q,v in out['banda_final'].items()},'v71',{q:round(v,2) for q,v in out['banda_v71'].items()})
json.dump(res,open(F.S4+'/fa_f_bandes_azimutals.json','w'),indent=1)
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
fig,ax=plt.subplots(1,5,figsize=(26,5))
for i,k in enumerate(F.MARKS):
    o=res[k]; A=ax[i]
    for nom,col in (('base','0.7'),('nrgf','c'),('achf','g'),('rhef','y'),('wow','m'),('p76','orange'),('final','r'),('v71','b')):
        A.plot(o['cells'],o[nom],color=col,label=nom,lw=1.2 if nom in ('final','v71') else 0.8)
    A.axvspan(o['az'][0],o['az'][1],color='k',alpha=0.08); A.set_title('%s  r %.0f–%.0f'%(k,*o['r'])); A.set_xlabel('az (°)'); A.set_ylabel('L* mitjà banda'); A.grid(alpha=.3)
ax[0].legend(fontsize=7); plt.tight_layout(); plt.savefig(F.S4+'/v_fa_bandes_azimutals.png',dpi=85)
# ---- (B) petjada de 76/96 i enfosquiment per azimut
L30=F.Lstar(P[30][0]); L76=F.Lstar(P[76][0]); L96=F.Lstar(P[96][0]); L206=F.Lstar(P[206][0])
rgb76,al76=c.carrega(76); rgb96,al96=c.carrega(96); rgb204,al204=c.carrega(204); rgb206,al206=c.carrega(206)
azc=np.arange(0,360,1.0); azi1=np.floor(F.AZ)
b_out=(F.RR>=470)&(F.RR<=485); b_in=(F.RR>=459)&(F.RR<=467)
rows=[]
for A in azc:
    so=b_out&(azi1==A); si=b_in&(azi1==A)
    rows.append(dict(az=float(A),alfa76=float(al76[so].mean()),alfa96=float(al96[so].mean()),alfa204=float(al204[so].mean()),alfa206=float(al206[so].mean()),
        L_abans=float(L30[so].mean()),L_despres76=float(L76[so].mean()),L_final=float(L206[so].mean()),L71=float(L71[so].mean()),
        solc_v74=float(L206[si].min()-L206[so].mean()),solc_v71=float(L71[si].min()-L71[so].mean()),solc_abans=float(L30[si].min()-L30[so].mean()),
        Lfoto76=float(F.Lstar(rgb76)[so].mean())))
json.dump(rows,open(F.S4+'/fa_f_fotos_azimut.json','w'),indent=1)
print('az  alfa76 alfa96 L_abans L_desp76 L_final L71  solc74 solc71 solc_abans Lfoto76')
for r_ in rows:
    if 90<=r_['az']<=260 and int(r_['az'])%3==0: print('%3d  %.2f  %.2f  %5.1f  %5.1f  %5.1f %5.1f  %6.1f %6.1f %6.1f %5.1f'%(r_['az'],r_['alfa76'],r_['alfa96'],r_['L_abans'],r_['L_despres76'],r_['L_final'],r_['L71'],r_['solc_v74'],r_['solc_v71'],r_['solc_abans'],r_['Lfoto76']))
fig,ax=plt.subplots(2,1,figsize=(16,8),sharex=True)
ax[0].plot(azc,[r_['L_abans'] for r_ in rows],'k',label='abans de les fotos (després de 30)'); ax[0].plot(azc,[r_['L_final'] for r_ in rows],'r',label='final V74'); ax[0].plot(azc,[r_['L71'] for r_ in rows],'b--',label='V71',lw=0.8)
ax[0].set_ylabel('L* mitjà r 470–485'); ax[0].legend(); ax[0].grid(alpha=.3)
ax2=ax[0].twinx(); ax2.plot(azc,[r_['alfa76'] for r_ in rows],'orange',lw=0.8,label='alfa 76'); ax2.plot(azc,[r_['alfa96'] for r_ in rows],'g',lw=0.8,label='alfa 96'); ax2.set_ylabel('alfa'); ax2.legend(loc='lower right')
ax[1].plot(azc,[r_['solc_abans'] for r_ in rows],'k',label='solc abans fotos'); ax[1].plot(azc,[r_['solc_v74'] for r_ in rows],'r',label='solc V74'); ax[1].plot(azc,[r_['solc_v71'] for r_ in rows],'b--',lw=0.8,label='solc V71'); ax[1].set_ylabel('min L*(459–467) − L*(470–485)'); ax[1].set_xlabel('az (°)'); ax[1].legend(); ax[1].grid(alpha=.3)
for A in ax:
    for k in F.MARKS:
        m=F.mask(k); A.axvspan(F.AZ[m].min(),F.AZ[m].max(),color='m',alpha=0.15)
plt.tight_layout(); plt.savefig(F.S4+'/v_fa_fotos_azimut.png',dpi=85)
# ---- (C) vistes sector W: abans fotos / després 76 / final / foto 76 amb alfa / V71  al 200 %
mm=F.mask('m4')|F.mask('m5'); y0,y1,x0,x1=F.bbox(mm,pad=80); Z=2
def to8(Cc): return Image.fromarray((np.clip(Cc[y0:y1,x0:x1],0,1)*255).astype(np.uint8)).resize(((x1-x0)*Z,(y1-y0)*Z),Image.NEAREST)
def contorn(m): return m & ~ndi.binary_erosion(m)
pan=[]
for nom,Cc in (('despres 30 (abans fotos)',P[30][0]),('despres 76',P[76][0]),('despres 96',P[96][0]),('final V74',C),('V71',C71),('foto 76 x alfa',rgb76*al76[...,None]),('foto 96 x alfa',rgb96*al96[...,None])):
    im=to8(Cc); d=ImageDraw.Draw(im); ys,xs=np.nonzero(contorn(mm)[y0:y1,x0:x1])
    for y,x in zip(ys,xs): d.rectangle([x*Z,y*Z,x*Z+Z-1,y*Z+Z-1],outline=(255,0,255))
    d.text((3,3),nom,fill=(255,255,0)); pan.append(im)
W=sum(p.width for p in pan)+6*(len(pan)-1); out=Image.new('RGB',(W,pan[0].height),(40,40,40)); x=0
for p in pan: out.paste(p,(x,0)); x+=p.width+6
out.save(F.S4+'/v_fa_W_fotos_passos.png'); print('vistes ok',out.size)
