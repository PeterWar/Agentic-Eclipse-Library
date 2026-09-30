"""Audit the selected fixed-gain spatial smoothing, without fitting a new profile."""
from pilot_isotropic import *
from qa_rasters import h1,h1_setup
from audit_geometry import polar,correlate
import f3

def main():
    r,t=coords();m=np.load(CAU/'fusion_support.npy');ctx=h1_setup(r,m)
    radii=np.linspace(1.12,2.5,60).astype('float32')
    ref=np.load(CAU/'fusion_total.npy',mmap_mode='r')
    reference=polar(np.log(np.maximum(ref[...,1],1)),CX,CY,RS,radii)
    sigmas={tag:(1.5 if tag=='04' else 3) for tag in SOURCES}
    rep={'operator':'positive normalized Cartesian Gaussian; fixed gain; no profile refit, new radial cut or resampling','sigma_px':sigmas,'layers':{},'transfer':{},'status':'pending'}
    for tag,path in SOURCES.items():
        old=np.load(path,mmap_mode='r');u=np.load(D/f'cau/{tag}_s{sigmas[tag]:g}_u16.npy',mmap_mode='r');a=u.astype('float32')/65535
        q={'H1':h1(a,m,ctx),'H1b':f3.anells_de_calaix(a,r,m),'geometry':correlate(polar(a,CX,CY,RS,radii),reference),'rois':{}}
        for name,(x,y) in ROIS.items():
            sl=(slice(y-256,y+256),slice(x-256,x+256));before=old[sl].astype('float32')/65535;after=a[sl]
            q['rois'][name]={}
            for s1,s2 in [(1,4),(2,8),(8,24)]:
                b=gauss(before,s1)-gauss(before,s2);v=gauss(after,s1)-gauss(after,s2)
                q['rois'][name][f'G{s1}-G{s2}']={'RMS_ratio':float(np.std(v[32:-32,32:-32])/np.std(b[32:-32,32:-32]))}
        rep['layers'][tag]=q;log(tag+' H1 '+str(q['H1']['worst'])+' geometry '+str(q['geometry']))
    # Actual additive injection through the sole new operator. It is linear
    # and fixed: the paired response is independent of the background image.
    yy,xx=np.mgrid[:512,:512];w=np.ones((512,512),'float32')
    for sigma in (1.5,3):
        rep['transfer'][str(sigma)]={}
        for lam in [8,12,16,24,32,48,64,96]:
            z=(.0001*np.sin(2*np.pi*xx/lam)).astype('float32');v=gauss(z,sigma);sl=(slice(64,-64),slice(64,-64));gain=float(np.sum(v[sl]*z[sl])/np.sum(z[sl]**2))
            rep['transfer'][str(sigma)][str(lam)]={'measured_gain':gain,'ideal_positive_gaussian':float(np.exp(-.5*(2*np.pi*sigma/lam)**2))}
    rep['status']='CHECKS_PASS' if all(q['H1']['PASS'] and q['geometry']['PASS'] for q in rep['layers'].values()) else 'CHECKS_FAIL'
    rep['limitation']='Smoothing attenuates genuine small structures too; tests do not identify every mini-circle as artifact. H1b warnings remain literal.'
    savejson(D/'candidate_qa.json',rep)
    assert rep['status']=='CHECKS_PASS'
if __name__=='__main__':main()
