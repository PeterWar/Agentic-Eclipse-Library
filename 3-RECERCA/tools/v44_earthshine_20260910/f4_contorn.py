"""Observed lunar optical edge from calibrated native Vixen green CFA planes.
No circle enlargement: retain repeatable azimuthal structure, quantify halves.
"""
from comu44 import *
from scipy.ndimage import gaussian_filter1d

def main():
    prepare();fr,_=frames();path=RUNS['vixen'];run=comu.Run.obre(str(path));ctx=f2.Ctx(run)
    pos=json.loads((path/'4-rebuts/F1.3_registre.json').read_text())['fotogrames']
    th=np.arange(1440)*2*np.pi/1440;rr=np.arange(430.,477.,.25)
    xx=MC[0]+np.cos(th[:,None])*rr[None,:];yy=MC[1]+np.sin(th[:,None])*rr[None,:]
    inv=cv2.invertAffineTransform(COMMON_TO_FINAL)
    qx=inv[0,0]*xx+inv[0,1]*yy+inv[0,2];qy=inv[1,0]*xx+inv[1,1]*yy+inv[1,2]
    qmx=inv[0,0]*MC[0]+inv[0,1]*MC[1]+inv[0,2];qmy=inv[1,0]*MC[0]+inv[1,1]*MC[1]+inv[1,2]
    dx=(qx-qmx)*ctx.k;dy=(qy-qmy)*ctx.k
    tab=[];records=[]
    for m in fr:
        if m['tren']!='vixen' or m['t']>29.3 or m['exp']>.125:continue
        v=pos[m['nom']];rx=ctx.ca*dx+ctx.sa*dy+v['sol_x']+v['lluna_dx'];ry=-ctx.sa*dx+ctx.ca*dy+v['sol_y']+v['lluna_dy']
        num=np.zeros_like(rx);den=np.zeros_like(rx)
        for i,(pl,w) in ctx.plans(m['nom'],m['exp']).items():
            if comu.IDX_CANAL[i]!=1:continue
            oy,ox=ctx.orig[i];mx=((rx-ox)*.5).astype(np.float32);my=((ry-oy)*.5).astype(np.float32)
            # Detector only: do not multiply by the radiometric floor weight,
            # which creates a fictitious edge in very short exposures.
            num+=cv2.remap(pl,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
            den+=cv2.remap(w,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
        g=num/2.;g=gaussian_filter1d(g,2.,axis=0,mode='wrap')
        der=gaussian_filter1d(g,3.,order=1,axis=1)
        ids=np.where((rr>446)&(rr<463))[0];ix=ids[np.argmax(der[:,ids],axis=1)];rows=np.arange(len(th))
        dd=der[rows,ix-1]-2*der[rows,ix]+der[rows,ix+1]
        sub=np.clip(.5*(der[rows,ix-1]-der[rows,ix+1])/np.minimum(dd,-1e-30),-.5,.5)
        edge=rr[ix]+.25*sub
        noise=np.std(np.diff(g[:,rr<438],axis=1),axis=1)
        good=(der[rows,ix]>3*noise)&(den[rows,ix]>.05*m['exp'])&(ix>ids[0])&(ix<ids[-1])
        if good.sum()<100:continue
        A=np.c_[np.ones(len(th)),np.cos(th),np.sin(th)]
        for _ in range(3):
            cf=np.linalg.lstsq(A[good],edge[good],rcond=None)[0];err=edge-A@cf
            good&=abs(err)<max(3*np.std(err[good]),1.)
        edge[~good]=np.nan;tab.append(edge)
        records.append(dict(stem=m['stem'],t_mid_C2=m['t_mid_C2'],exp=m['exp'],fit_R_dx_dy=cf.tolist(),n=int(good.sum()),rms=float(np.std(err[good]))))
    tab=np.array(tab);edge=np.nanmedian(tab,axis=0);ix=np.arange(len(th));good=np.isfinite(edge);edge=np.interp(ix,ix[good],edge[good],period=len(th))
    assert len(records)>=8 and good.mean()>.9, 'insufficient independent native limb coverage'
    # 0.25 degree sample spacing. The measured contour is not rescaled.
    np.save(CAU44/'vixen_optical_edge.npy',edge)
    halves=[np.nanmedian(tab[k::2],axis=0) for k in (0,1)];good=np.isfinite(halves[0])&np.isfinite(halves[1]);dif=halves[0][good]-halves[1][good]
    rep=dict(method='calibrated G1+G2 native CFA, one polar remap; max radial derivative sigma0.75 px; circular angular sigma0.5 degrees',frames=records,edge_median=float(np.median(edge)),half_rms=float(np.sqrt(np.mean(dif*dif))),interframe_median_sigma=float(np.nanmedian(np.nanstd(tab,axis=0))))
    savejson(REB44/'F4_contorn.json',rep);print(json.dumps(rep),flush=True)

if __name__=='__main__':main()
