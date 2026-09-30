import numpy as np, json
cand=np.load('cand.npy')
L=np.load('g_long_snr.npy'); S=np.load('g_short_snr.npy')
def mom(img,x,y,box=9,thr=0.0):
    x0,y0=int(round(x)),int(round(y))
    sub=img[y0-box:y0+box+1,x0-box:x0+box+1].astype(np.float64)
    yy,xx=np.mgrid[-box:box+1,-box:box+1]
    r=np.hypot(xx,yy)
    w=np.clip(sub,0,None)*(r<=box)
    if w.sum()<=0: return None
    for _ in range(3):
        cx=(w*xx).sum()/w.sum(); cy=(w*yy).sum()/w.sum()
        r=np.hypot(xx-cx,yy-cy); w=np.clip(sub,0,None)*(r<=box)
        if w.sum()<=0: return None
    Sw=w.sum()
    mxx=(w*(xx-cx)**2).sum()/Sw; myy=(w*(yy-cy)**2).sum()/Sw; mxy=(w*(xx-cx)*(yy-cy)).sum()/Sw
    return cx+x0,cy+y0,mxx,myy,mxy,Sw
# drift unit vector
vx,vy=0.1999,-0.2002
n=np.hypot(vx,vy); ux,uy=vx/n,vy/n
print('drift unit vector (%.3f,%.3f)  PA_array=%.1f deg'%(ux,uy,np.degrees(np.arctan2(uy,ux))))
rows=[]
for i,(x,y,pk,sa,sb) in enumerate(cand):
    a=mom(L,x,y); b=mom(S,x,y)
    if a is None or b is None: continue
    def proj(m):
        mxx,myy,mxy=m[2],m[3],m[4]
        par=ux*ux*mxx+2*ux*uy*mxy+uy*uy*myy
        per=uy*uy*mxx-2*ux*uy*mxy+ux*ux*myy
        return par,per
    pl,ql=proj(a); ps,qs=proj(b)
    d=pl-ps
    Ltr=np.sqrt(12*d) if d>0 else float('nan')
    rows.append((i,x,y,pk,np.sqrt(max(pl,0)),np.sqrt(max(ql,0)),np.sqrt(max(ps,0)),np.sqrt(max(qs,0)),Ltr))
print('%4s %8s %8s %6s | long sig_par sig_per | short sig_par sig_per | trail px | trail arcsec'%('id','x','y','snr'))
for r in rows:
    print('%4d %8.2f %8.2f %6.1f |  %5.2f %5.2f  |  %5.2f %5.2f  |  %6.2f | %6.2f'%(
        r[0],r[1],r[2],r[3],r[4],r[5],r[6],r[7],r[8],r[8]*2.158 if r[8]==r[8] else float('nan')))
rr=[r for r in rows if r[3]>8 and r[8]==r[8]]
tr=np.array([r[8] for r in rr])
print('bright subset n=%d  trail median %.2f px = %.2f arcsec  -> %.3f arcsec/s over 10.3 s'%(len(rr),np.median(tr),np.median(tr)*2.158,np.median(tr)*2.158/10.3))
print('  scatter %.2f px'%np.std(tr))
# FWHM from short stack (essentially untrailed)
f=[np.sqrt(0.5*(r[6]**2+r[7]**2))*2.355 for r in rr]
print('short-stack FWHM median %.2f px = %.2f arcsec'%(np.median(f),np.median(f)*2.158))
fl=[np.sqrt(0.5*(r[4]**2+r[5]**2))*2.355 for r in rr]
print('long-stack  FWHM median %.2f px = %.2f arcsec'%(np.median(fl),np.median(fl)*2.158))
