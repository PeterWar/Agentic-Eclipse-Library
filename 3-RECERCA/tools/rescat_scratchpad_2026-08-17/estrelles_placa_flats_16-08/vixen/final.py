import numpy as np, json
cand=np.load('cand.npy'); moons=np.load('moons.npy')
FL=np.load('g_long_flux.npy'); DL=np.load('g_long_den.npy')
FF=np.load('stack_flux.npy'); DF=np.load('stack_sig.npy')
SH=json.load(open('shifts_start.json'))
FR=[('572A2978',1.0),('572A2979',2.0),('572A2980',2.0),('572A2981',2.0),
    ('572A2982',10.3),('572A2983',10.3),('572A2984',10.3),('572A2996',1.0)]
yy,xx=np.mgrid[-14:15,-14:15]; rr=np.hypot(xx,yy)
def phot(img,sig,x,y,rap=5.0):
    x0,y0=int(round(x)),int(round(y))
    if x0<16 or y0<16 or x0>img.shape[1]-17 or y0>img.shape[0]-17: return None
    sub=img[y0-14:y0+15,x0-14:x0+15].astype(np.float64)
    ss=sig[y0-14:y0+15,x0-14:x0+15].astype(np.float64)
    ann=(rr>9)&(rr<=14)
    bg=np.median(sub[ann])
    ap=rr<=rap
    F=(sub[ap]-bg).sum()
    N=ap.sum()
    n=np.median(ss[ann])*np.sqrt(N)
    return F,F/max(n,1e-9)
# growth curve on the brightest, on the full stack
x,y=cand[0,0],cand[0,1]
x0,y0=int(round(x)),int(round(y))
sub=FF[y0-14:y0+15,x0-14:x0+15]-np.median(FF[y0-14:y0+15,x0-14:x0+15][(rr>9)&(rr<=14)])
tot=[(R,(sub[rr<=R]).sum()) for R in [2,3,4,5,6,7,8,9,10,12]]
print('growth curve (brightest, stack, ADU/s):', ' '.join('r=%d:%.0f'%t for t in tot))
apcorr=tot[-1][1]/[t[1] for t in tot if t[0]==5][0]
print('aperture correction r=5 -> r=12: %.3f'%apcorr)
sigF=DF
rows=[]
for i,(x,y,pk,sa,sb) in enumerate(cand):
    r=np.hypot(x-moons[4][0],y-moons[4][1])
    ph=phot(FF,sigF,x,y)
    per=[]
    for f,exp in FR:
        dt,dx,dy=SH[f]
        res=np.load('res_%s.npy'%f,mmap_mode='r'); sg=np.load('sig_%s.npy'%f,mmap_mode='r')
        p=phot(np.array(res[max(0,int(y+dy)-20):int(y+dy)+21, max(0,int(x+dx)-20):int(x+dx)+21]),
               np.array(sg[max(0,int(y+dy)-20):int(y+dy)+21, max(0,int(x+dx)-20):int(x+dx)+21]),
               x+dx-max(0,int(x+dx)-20), y+dy-max(0,int(y+dy)-20))
        per.append((p[0]/exp if p else np.nan, p[1] if p else np.nan))
    nfr=sum(1 for q in per if q[1]==q[1] and q[1]>3)
    rows.append((i,x,y,r,ph[0]*apcorr if ph else np.nan,ph[1] if ph else np.nan,nfr,[q[1] for q in per],[q[0] for q in per]))
    print('%3d x=%7.1f y=%7.1f r=%6.0f px (%5.2f Rm, %4.2f deg) flux=%8.2f ADU/s snr=%6.1f  nfr>3s=%d  perframe_snr=%s'%(
        i,x,y,r,r/451.0,r*2.158/3600,rows[-1][4],rows[-1][5],nfr,' '.join('%.1f'%v if v==v else 'na' for v in rows[-1][7])))
np.save('final_rows.npy',np.array([[r[0],r[1],r[2],r[3],r[4],r[5],r[6]] for r in rows]))
json.dump([[r[0],r[7],r[8]] for r in rows],open('perframe.json','w'))
