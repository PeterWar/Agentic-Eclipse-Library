from study import image_source
from geometry import *
import argparse

def expected(s,p):
    dx=s.x-(s.center[0]+p[0]);dy=s.y-(s.center[1]+p[1])
    e1,e2=p[2:4] if len(p)>2 else (0.,0.)
    e=np.hypot(e1,e2);c=np.cosh(e);v=np.sinh(e)/e if e else 1.
    nx=(c+v*e1)*dx+v*e2*dy;ny=v*e2*dx+(c-v*e1)*dy
    den=nx*nx+ny*ny
    return (nx*nx-ny*ny)/den,2*nx*ny/den

def main():
    ap=argparse.ArgumentParser();ap.add_argument('case');args=ap.parse_args()
    synthetic=args.case.startswith('synthetic')
    s=Samples(center=(1200.37,1200.63),radial=(500,1000),step=4,nsectors=24,margin_deg=2) if synthetic else Samples(nsectors=24,margin_deg=2)
    assert 2*s.radial[0]*np.sin(np.deg2rad(2))>2*np.sqrt(2)*10
    a,origin,provenance=image_source(args.case,s);b=gauss(a,3)
    x=s.x-origin[0];y=s.y-origin[1];center=b[y,x]
    xx=b[y,x+1]-2*center+b[y,x-1];yy=b[y+1,x]-2*center+b[y-1,x]
    xy=(b[y+1,x+1]-b[y+1,x-1]-b[y-1,x+1]+b[y-1,x-1])/4
    delta=np.hypot(xx-yy,2*xy);plus=(xx+yy+delta)/2;minus=(xx+yy-delta)/2
    angle=.5*np.arctan2(2*xy,xx-yy)+np.where(np.abs(minus)>np.abs(plus),np.pi/2,0)
    strong=np.maximum(np.abs(plus),np.abs(minus));weak=np.minimum(np.abs(plus),np.abs(minus))
    anisotropy=(strong-weak)/np.maximum(strong+weak,1e-30)
    ca=np.cos(2*angle);sa=np.sin(2*angle);weight=anisotropy**2
    rows=[]
    for parity in [0,1]:
        training=s.sector%2==parity;threshold=float(np.median(strong[training]))
        good=(anisotropy>.6)&(strong>threshold);train=good&training;test=good&~training
        def score(p,sel):
            ce,se=expected(s,p)
            return float(np.sum(weight[sel]*(ca[sel]*ce[sel]+sa[sel]*se[sel]))/np.sum(weight[sel]))
        def fit(ellipse,seed=None):
            scale=np.array([32,32,.02,.02]) if ellipse else np.array([32,32])
            bounds=[(-4,4),(-4,4)]+([(-3,3),(-3,3)] if ellipse else [])
            starts=[np.r_[seed,(0,0)]] if ellipse else [[0,0],[-96,-96],[-96,96],[96,-96],[96,96]]
            fits=[]
            for initial in starts:
                z=minimize(lambda q:-score(q*scale,train),np.asarray(initial)/scale,method='L-BFGS-B',bounds=bounds,
                    options={'maxiter':100,'ftol':1e-12,'gtol':1e-8,'eps':.001})
                fits.append(z)
            z=min(fits,key=lambda z:z.fun);return z.x*scale
        circle=fit(False);ellipse=fit(True,circle)
        for name,p in [('solar_fixed',np.array([0.,0.])),('circle_free',circle),('ellipse_free',ellipse)]:
            ce,se=expected(s,p);align=ca*ce+sa*se
            sect=[]
            for k in np.unique(s.sector[test]):
                sel=test&(s.sector==k);z=float(np.average(align[sel],weights=weight[sel]))
                sect.append({'sector':int(k),'score':z,'selected_points':int(sel.sum())})
            rows.append({'model':name,'training_parity':parity,'parameters':p,'center_xy':s.center+p[:2],
                'offset_from_reference_px':float(np.linalg.norm(p[:2])),
                'axis_ratio':float(np.exp(np.hypot(*p[2:4]))) if len(p)>2 else 1.,
                'train_score':score(p,train),'heldout_score':score(p,test),'sectors':sect,
                'selected_train':int(train.sum()),'selected_heldout':int(test.sum()),
                'threshold_curvature':threshold,
                'at_boundary':any(abs(v)>lim-tol for v,lim,tol in zip(p,[128,128,.06,.06],[.05,.05,1e-4,1e-4]))})
        log(args.case+f' orientation parity{parity}: '+str([(r['model'],r['heldout_score']) for r in rows if r['training_parity']==parity]))
    np.savez(D/(args.case+'_orientation.npz'),x=s.x,y=s.y,ca=ca,sa=sa,anisotropy=anisotropy,strong=strong,sector=s.sector)
    save(args.case+'_orientation',{'case':args.case,'provenance':provenance,'sigma_px':3,
        'selection':'anisotropy>0.6 and curvature>training median, no orientation-relative-to-Sun selection',
        'score':'weighted mean cos(2 angle(normal,gradient elliptical_radius)); positive tangential ridges, negative radial ridges',
        'fits':rows,'scope':'orientation of local ridges; does not prove entire circles, artifact status or a unique center'})

if __name__=='__main__':main()
