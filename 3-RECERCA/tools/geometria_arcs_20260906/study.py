from geometry import *
import argparse
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d

def image_source(case,s):
    guard=200
    x0=int(s.x.min())-guard;y0=int(s.y.min())-guard
    x1=int(s.x.max())+guard+1;y1=int(s.y.max())+guard+1
    sl=np.s_[y0:y1,x0:x1];old=ROOT/'research/tools/v29/cau_final'
    if case.startswith('synthetic'):
        # Smaller canvas, same pixel-scale detail and full analysis procedure.
        y,x=np.mgrid[y0:y1,x0:x1];delta=np.array([37.4,-24.8])
        c=s.center+delta;dx=x-c[0];dy=y-c[1]
        e1,e2=(.035,-.02) if 'ellipse' in case else (0.,0.)
        eta=np.hypot(e1,e2);ss=np.sinh(eta)/eta if eta else 1.
        r=np.sqrt(np.cosh(eta)*(dx*dx+dy*dy)+ss*(e1*(dx*dx-dy*dy)+2*e2*dx*dy))
        th=np.arctan2(dy,dx)
        if 'wobble' in case:r+=8*np.cos(3*th+.4)
        rings=np.sin(2*np.pi*(r/29+0.00008*r*r))+.6*np.cos(2*np.pi*r/63+.3)+.4*np.sin(2*np.pi*r/41+.8)
        rng=np.random.default_rng(473301)
        noise=gauss(rng.normal(size=r.shape).astype('float32'),2)
        noise/=noise.std()
        a=(.004*rings*(1+.4*np.cos(3*th))+.004*noise).astype('float32')
        if 'clean' in case:a=(.004*rings*(1+.4*np.cos(3*th))).astype('float32')
        if 'null' in case:a=(.004*noise).astype('float32')
        return a,(x0,y0),{'type':'synthetic','true_center':c.tolist(),'true_e':[e1,e2],
            'true_axis_ratio':float(np.exp(eta)),'wobble_amplitude_px':8 if 'wobble' in case else 0,
            'seed':473301,'ring_peak_scale':.004,'correlated_noise_RMS':0. if 'clean' in case else .004}
    tag=case[:2];name={'01':'achf','02':'passalt24'}[tag]
    if 'preH1' in case:
        p=old/(name+'_smoothed.npy');a=np.array(np.load(p,mmap_mode='r')[sl],np.float32)
    elif 'H1' in case:
        p=old/(name+'_u16.npy');b=old/(name+'_smoothed.npy')
        a=np.array(np.load(p,mmap_mode='r')[sl],np.float32)/65535-.5-np.load(b,mmap_mode='r')[sl]
    else:
        p=ROOT/f'research/tools/v31/cau/{tag}_final_u16.npy'
        a=np.array(np.load(p,mmap_mode='r')[sl],np.float32)/65535-.5
    mask=np.load(old/'fusion_support.npy',mmap_mode='r')[sl]
    # Entire filter input rectangle need not be valid, but every sampled pixel
    # has valid support in the full square of radius3sigma64=192.
    from scipy.ndimage import distance_transform_cdt
    dist=distance_transform_cdt(np.pad(mask,1),metric='chessboard')[1:-1,1:-1]
    margin=dist[s.y-y0,s.x-x0]
    assert margin.min()>192,margin.min()
    return a,(x0,y0),{'type':'real','source':str(p),'full_canvas_shape':[7506,10551],
        'case':case,'minimum_support_chessboard_distance_px':float(margin.min()),
        'secondary_source':str(b) if 'H1' in case and 'preH1' not in case else None}

def diagnostics(s,z,fit,row):
    p=np.array(row['parameters']);j,f=s.basis(p);b=row['profile'];pred=prediction(j,f,b)
    # Per-sector phase shifts are diagnostic ONLY; not used to improve CV scores.
    phase=[]
    for sector in np.unique(s.sector[fit.valid]):
        good=s.sector==sector;rr=s.radius(p)[good];zz=z[good]
        shifts=np.arange(-16,16.01,.5)
        errors=[]
        for shift in shifts:
            pp=np.interp(rr+shift,s.knots,b)
            errors.append(np.mean((zz-pp)**2))
        k=int(np.argmin(errors));phase.append({'sector':int(sector),'best_shift_px':float(shifts[k]),
            'at_search_edge':k in [0,len(shifts)-1],'zero_shift_error':float(errors[len(shifts)//2]),
            'best_error':float(errors[k])})
    # Heldout null: train template fixed, independent circular radial shifts
    # of its values within each heldout sector preserve template distribution.
    # This is a conditional reference, not significance of physical corona.
    rng=np.random.default_rng(173905);valid=fit.valid
    blocks=[np.flatnonzero((s.sector==sector)&valid) for sector in np.unique(s.sector[valid])]
    ordered=[ids[np.argsort(s.radius(p)[ids])] for ids in blocks]
    observed=float(np.mean(z[valid]*pred[valid]));null=[]
    for _ in range(199):
        total=0
        for ids in ordered:
            n=len(ids);shift=int(rng.integers(max(1,n//5),max(2,4*n//5)))
            total+=np.dot(z[ids],np.roll(pred[ids],shift))
        null.append(total/valid.sum())
    return {'sector_phase_diagnostic':phase,
        'phase_shift_median_px':float(np.median([v['best_shift_px'] for v in phase])),
        'phase_shift_RMS_px':float(np.sqrt(np.mean(np.square([v['best_shift_px'] for v in phase])))),
        'conditional_null_observed_crossmoment':observed,'conditional_null_crossmoments':null,
        'conditional_null_exceedance_fraction':float((1+sum(v>=observed for v in null))/200),
        'null_scope':'fixed training template; heldout sector order shifts; empirical conditional reference, not physical causal significance'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('case');ap.add_argument('--band',choices=['fine','wide'],default='fine');ap.add_argument('--quick',action='store_true');args=ap.parse_args()
    synthetic=args.case.startswith('synthetic')
    geometry_kwargs={'nsectors':12,'margin_deg':9} if args.band=='fine' else {'nsectors':8,'margin_deg':15}
    s=Samples(center=(1200.37,1200.63),radial=(500,1000),step=4,**geometry_kwargs) if synthetic else Samples(**geometry_kwargs)
    a,origin,provenance=image_source(args.case,s)
    sigmas=(2,16) if args.band=='fine' else (8,64)
    minimum_separation=2*s.radial[0]*np.sin(np.deg2rad(s.margin_deg))
    assert minimum_separation>2*np.sqrt(2)*3*sigmas[1], 'train/heldout convolution footprints may overlap'
    filtered=gauss(a,sigmas[0])-gauss(a,sigmas[1])
    z=np.asarray(filtered[s.y-origin[1],s.x-origin[0]],float)
    name=args.case+'_'+args.band
    np.savez(D/(name+'_samples.npz'),x=s.x,y=s.y,z=z,sector=s.sector)
    rep={'name':name,'provenance':provenance,'reference_center':s.center,'solar_center':[CX,CY],
        'sample_count':len(z),'analysis_sigmas_px':sigmas,'spline_knot_spacing_px':2,
        'fitting':'fixed Cartesian samples; training sectors only; all candidate geometries share data',
        'radial_selection_px':s.radial,'sector_count':s.nsectors,'sector_margin_degrees':s.margin_deg,
        'minimum_train_holdout_separation_px':float(minimum_separation),
        'maximum_filter_dependency_diameter_px':float(2*np.sqrt(2)*3*sigmas[1]),'fits':[]}
    plotted=[]
    for parity in [0,1]:
        f=Fit(s,z,parity);log(name+f' parity{parity} fixed')
        fixed=f.evaluate([0,0],True)
        log(name+f' parity{parity} circle search')
        circle=f.optimize(quick=args.quick)
        log(name+f' parity{parity} ellipse search')
        ellipse=f.optimize(ellipse=True,seed=circle['parameters'],quick=args.quick)
        for model,row in [('solar_fixed',fixed),('circle_free',circle),('ellipse_free',ellipse)]:
            result=compact(row);result.update(model=model,training_parity=parity)
            result.update(diagnostics(s,z,f,row));rep['fits'].append(result)
            np.savez(D/(name+f'_{parity}_{model}_profile.npz'),knots=row['knots'],profile=row['profile'])
            log(name+' '+json.dumps({k:result[k] for k in ['model','training_parity','center_xy','axis_ratio','heldout','phase_shift_RMS_px']}))
        plotted.append((fixed,circle,ellipse));save(name,rep)
    # Diagnostic profile comparison, with the same radial axis for all models.
    fig,axes=plt.subplots(2,2,figsize=(13,7))
    for parity,rows in enumerate(plotted):
        for label,row in zip(['Solar fix','Cercle lliure','El·lipse lliure'],rows):
            good=(row['knots']>=s.radial[0])&(row['knots']<=s.radial[1])
            axes[parity,0].plot(row['knots'][good],row['profile'][good],label=label,lw=.9)
            axes[parity,1].scatter(row['center_xy'][0]-s.center[0],row['center_xy'][1]-s.center[1],label=label)
        axes[parity,0].set_title(f'{name} · entrenament sectors {parity}');axes[parity,0].set_ylabel('Component radial estimada')
        axes[parity,0].set_xlabel('Coordenada radial del model [px]');axes[parity,0].legend()
        axes[parity,1].axhline(0,color='gray',lw=.5);axes[parity,1].axvline(0,color='gray',lw=.5)
        axes[parity,1].set_xlim(-135,135);axes[parity,1].set_ylim(135,-135);axes[parity,1].set_aspect('equal')
        axes[parity,1].set_xlabel('Centre − referència: x [px]');axes[parity,1].set_ylabel('y [px]');axes[parity,1].legend()
    fig.tight_layout();fig.savefig(RUN.vista(name+'_profiles.png'),dpi=130);plt.close(fig)
    log(name+' COMPLETE')

if __name__=='__main__':main()
