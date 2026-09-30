import numpy as np, json, lib, warnings; warnings.filterwarnings('ignore')
from scipy import ndimage as ndi
cand=np.load('cand.npy'); SH=json.load(open('shifts_start.json'))
FR=[('572A2982',10.3),('572A2983',10.3),('572A2984',10.3)]
dk=np.load('dark_med_10.npy')[:lib.H,:lib.W]; hm=lib.hotmask('dark_med_10.npy')
B=16
acc={c:np.zeros((len(cand),2)) for c in 'RB'}   # flux, var
hot=np.zeros(len(cand))
for f,exp in FR:
    im=lib.load_raw(f); sat=im>=lib.SAT; im=im-dk
    bad=ndi.binary_dilation(sat|hm,np.ones((3,3)))
    im=np.where(bad,np.nan,im)
    dt,dx,dy=SH[f]
    for i,(x,y,pk,sa,sb) in enumerate(cand):
        X,Y=x+dx,y+dy; x0,y0=int(round(X)),int(round(Y))
        if x0<B+2 or y0<B+2 or x0>=lib.W-B-2 or y0>=lib.H-B-2: continue
        sub=im[y0-B:y0+B+1,x0-B:x0+B+1]
        yy,xx=np.mgrid[y0-B:y0+B+1,x0-B:x0+B+1]
        rr=np.hypot(xx-X,yy-Y)
        for c,(pr,pc) in [('R',(0,0)),('B',(1,1))]:
            m=((yy%2)==pr)&((xx%2)==pc)
            ann=m&(rr>10)&(rr<=B)&np.isfinite(sub)
            ap=m&(rr<=5.0)&np.isfinite(sub)
            if ann.sum()<40 or ap.sum()<15: continue
            bg=np.nanmedian(sub[ann]); sd=np.nanmedian(np.abs(sub[ann]-bg))*1.4826
            F=np.nansum(sub[ap]-bg)/exp
            V=(sd*np.sqrt(ap.sum())/exp)**2
            acc[c][i,0]+=F/V; acc[c][i,1]+=1.0/V
        hot[i]+=hm[y0-3:y0+4,x0-3:x0+4].sum()
print('%3s | green ADU/s |    R flux   snrR |    B flux   snrB | hotpx_in_7x7(3 frames)'%'id')
for i in range(len(cand)):
    r=acc['R'][i]; b=acc['B'][i]
    fr=r[0]/r[1] if r[1]>0 else np.nan; sr=fr*np.sqrt(r[1]) if r[1]>0 else np.nan
    fb=b[0]/b[1] if b[1]>0 else np.nan; sb_=fb*np.sqrt(b[1]) if b[1]>0 else np.nan
    print('%3d | %11s | %9.1f %6.1f | %9.1f %6.1f | %d'%(i,'',fr,sr,fb,sb_,hot[i]))
np.save('rb.npy',np.vstack([[acc['R'][i,0]/acc['R'][i,1] if acc['R'][i,1]>0 else np.nan for i in range(len(cand))],
                            [acc['R'][i,0]/np.sqrt(acc['R'][i,1]) if acc['R'][i,1]>0 else np.nan for i in range(len(cand))],
                            [acc['B'][i,0]/acc['B'][i,1] if acc['B'][i,1]>0 else np.nan for i in range(len(cand))],
                            [acc['B'][i,0]/np.sqrt(acc['B'][i,1]) if acc['B'][i,1]>0 else np.nan for i in range(len(cand))],hot]).T)
