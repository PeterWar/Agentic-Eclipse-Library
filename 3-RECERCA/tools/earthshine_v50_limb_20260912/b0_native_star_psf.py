"""Independent core-width measurement from native, unsaturated stellar pixels.
Prior star detections seed positions only. No remapped/demosaiced star image is
fitted. Pixel-integrated elliptical Gaussian core convolved with frozen wings;
free local plane. Short exposures limit tracking elongation. Diagnostic only.
"""
from common50 import *
import rawpy
from scipy.optimize import least_squares
PTH=Path('/Users/USUARI/Desktop/Eclipse 2026/Derivats/Astrometria/Estrelles/Work_2026-08-17/vixen')
cand=np.load(PTH/'cand.npy')[:8];shifts=json.loads((PTH/'shifts_start.json').read_text());p=np.array(json.loads((OUT/'A1_fit.json').read_text())['p']);weights=np.r_[1-p.sum(),p];scales=np.r_[0.,SIGMA]
save('B0_star_plan.json',dict(method=__doc__,stems=['572A2978','572A2979','572A2996'],seeds=str(PTH/'cand.npy'),seed_indices=list(range(8)),parameters='Flux, centre ±4 native pixels, elliptical core sigma0.4..3, angle, local plane; 5x5 pixel-area quadrature; fixed A1 wide-kernel mixture.',acceptance='Peak SNR>=5; reduced conditional chi2<=3; no core width at bounds; centroid within3.5px. Report all fits. Star width is field/time-dependent; no universal seeing claimed.',raw_root='/Users/USUARI/Desktop/Eclipse 2026/Vixen R6III/Vixen Fase totalitat',publication='NONE'))
rows=[];receipts=[];q=(np.arange(5)+.5)/5-.5
for stem in ['572A2978','572A2979','572A2996']:
    path=Path('/Users/USUARI/Desktop/Eclipse 2026/Vixen R6III/Vixen Fase totalitat')/(stem+'.CR3')
    with rawpy.imread(str(path)) as raw:
        im=raw.raw_image_visible.copy();colors=raw.raw_colors_visible.copy();green=[i for i,c in enumerate(raw.color_desc.decode().strip('\0')) if c=='G']
    receipts.append(dict(path=str(path),sha256=sha(path)))
    for index,seed in enumerate(cand):
        x=seed[0]+shifts[stem][1];y=seed[1]+shifts[stem][2];ix=int(round(x));iy=int(round(y));YY,XX=np.mgrid[iy-9:iy+10,ix-9:ix+10];patch=im[iy-9:iy+10,ix-9:ix+10].astype(float);cc=colors[iy-9:iy+10,ix-9:ix+10];good=np.isin(cc,green)&(patch<13500)
        dx=(XX[good]-x);dy=(YY[good]-y);observed=patch[good]-511.5;noise=np.sqrt(np.maximum(observed,0)/5.08+1.05**2);bg=float(np.median(observed));peak=float(observed.max()-bg)
        xq=dx[:,None,None]+q[None,:,None];yq=dy[:,None,None]+q[None,None,:]
        def model(par):
            flux,cx,cy,sx,sy,theta,b0,bx,by=par;c=np.cos(theta);s=np.sin(theta);u=(xq-cx)*c+(yq-cy)*s;v=-(xq-cx)*s+(yq-cy)*c
            value=np.zeros((len(dx),5,5))
            for w,scale in zip(weights,scales):
                a=sx*sx+scale*scale;b=sy*sy+scale*scale;value+=w*np.exp(-.5*(u*u/a+v*v/b))/(2*np.pi*np.sqrt(a*b))
            return flux*value.mean((1,2))+b0+bx*dx+by*dy
        initial=[max(peak,1)*2*np.pi,0,0,1.,1.,0,bg,0,0]
        lo=[0,-4,-4,.4,.4,-np.pi,-2000,-100,-100];hi=[1e6,4,4,3,3,np.pi,2000,100,100]
        opt=least_squares(lambda a:(model(a)-observed)/noise,initial,bounds=(lo,hi),loss='soft_l1',f_scale=2,max_nfev=150)
        residual=(model(opt.x)-observed)/noise;chi=float(np.mean(residual**2));snr=peak/np.median(noise);sig=opt.x[3:5];good_fit=bool(snr>=5 and chi<=3 and sig.min()>.401 and sig.max()<2.999 and max(abs(opt.x[1:3]))<3.5)
        row=dict(stem=stem,star_index=index,x=x,y=y,snr=float(snr),chi2_mean=chi,parameters=opt.x.tolist(),core_sigma_geometric=float(np.sqrt(sig.prod())),accepted=good_fit);rows.append(row);print(stem,index,round(snr,1),np.round(sig,3),round(chi,2),good_fit,flush=True)
    del im,colors
accepted=[r for r in rows if r['accepted']];values=[r['core_sigma_geometric'] for r in accepted]
save('B0_native_star_psf.json',dict(method=__doc__,raw_receipts=receipts,rows=rows,accepted=len(accepted),core_sigma_native_percentiles=np.percentile(values,[16,50,84]).tolist() if values else None,limits='Native stellar core plus existing conditional wing model. Atmospheric PSF varies over time and field. No correction accepted solely from this fit.'))
print('CORE',len(accepted),np.percentile(values,[16,50,84]) if values else None,flush=True)
