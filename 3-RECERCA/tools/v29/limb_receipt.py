"""Reproduce the newly exposed inner corona from immutable per-frame inputs."""
from common import *
import f2

def main():
    path=RUNS['vixen'];run=comu.Run.obre(str(path));ctx=f2.Ctx(run)
    pos=json.loads((path/'4-rebuts/F1.3_registre.json').read_text())['fotogrames'];K=json.loads((path/'4-rebuts/F2.2_coherencia.json').read_text())['k']
    sl=(slice(3960,5001),slice(3528,4569));yy,xx=np.mgrid[-520:521,-520:521];rad=np.hypot(yy,xx)
    ld={c:fits.getdata(path/f'2-ldic/LDIC_{c}.fits',memmap=True)[sl] for c in 'RGB'}
    co={c:fits.getdata(path/f'2-ldic/CORONA_{c}.fits',memmap=True)[sl] for c in 'RGB'}
    valid=np.logical_and.reduce([np.isfinite(ld[c])&(ld[c]>0) for c in 'RGB']);old=np.logical_and.reduce([np.isfinite(co[c])&(co[c]>0) for c in 'RGB'])
    missed=valid&~old&(rad<=1.05*RS);jy,jx=np.nonzero(missed);X=(jx+3528).astype(np.float32)[None,:];Y=(jy+3960).astype(np.float32)[None,:]
    weights=[];values=[];clearances=[];exposures=[];times=[];names=sorted(pos)
    for n in names:
        v=pos[n];dx=(X-ctx.CX)*ctx.k;dy=(Y-ctx.CY)*ctx.k;rx=ctx.ca*dx+ctx.sa*dy+v['sol_x'];ry=-ctx.sa*dx+ctx.ca*dy+v['sol_y'];fl=f2.mascara_lluna(ctx,v,rx,ry)
        nu=np.zeros(X.shape,np.float64);de=np.zeros_like(nu)
        for i,(pl,w) in ctx.plans(n,v['exp']).items():
            if comu.IDX_CANAL[i]!=1:continue
            oy,ox=ctx.orig[i];mx=(rx-ox)*.5;my=(ry-oy)*.5
            nu+=cv2.remap(pl*w*K[n],mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)*fl
            de+=cv2.remap(w,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)*fl
        weights.append(de.ravel());values.append(np.where(de>0,nu/np.maximum(de,1e-30),np.nan).ravel())
        clearances.append((np.hypot(rx-v['sol_x']-v['lluna_dx'],ry-v['sol_y']-v['lluna_dy'])-ctx.RL).ravel());exposures.append(v['exp']);times.append(v['t'])
    wg=np.array(weights);vg=np.array(values);D=wg.sum(0);replay=np.nansum(wg*vg,0)/np.maximum(D,1e-30);cnt=(wg>0).sum(0);neff=D*D/np.maximum((wg*wg).sum(0),1e-30)
    target=ld['G'][missed].astype(float);err=np.abs(replay-target)/target
    assert np.max(err)<1e-4
    q=lambda a:np.percentile(a,[0,5,25,50,75,95,100])
    rep={'run':str(path),'frames':names,'pixel_selection':'LDIC RGB positive finite, CORONA RGB not all positive finite, r<=1.05R','pixels':int(missed.sum()),'camera_channel':'G (not transformed sRGB confidence)','quantiles':[0,5,25,50,75,95,100],'replay_relative_error':q(err),'neff':q(neff),'one_observation':int((cnt==1).sum()),'two_or_more':int((cnt>=2).sum()),'splits':{}}
    for tag,sel in [('interleaved',np.arange(len(names))%2==0),('temporal',np.array(times)<np.median(times))]:
        wa=wg[sel].sum(0);wb=wg[~sel].sum(0);a=np.nansum(wg[sel]*vg[sel],0)/np.maximum(wa,1e-30);b=np.nansum(wg[~sel]*vg[~sel],0)/np.maximum(wb,1e-30);both=(wa>0)&(wb>0);rd=np.abs(a-b)/np.maximum(.5*(a+b),1e-30)
        rep['splits'][tag]={'overlap':int(both.sum()),'relative_difference':q(rd[both])}
    # Explicit confidence planes at original global coordinates, for inspection.
    np.savez_compressed(CAU/'limb_confidence.npz',x=X.ravel(),y=Y.ravel(),contributors=cnt,neff=neff,weight=D,replay=replay)
    savejson(CAU/'limb_receipt.json',rep);log(str(rep))

if __name__=='__main__':main()
