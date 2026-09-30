from pathlib import Path
import sys, json, time, hashlib
import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from operators import LocalModel, smooth, nrgf

D = Path(__file__).resolve().parent
ROOT = D.parents[2]
sys.path.insert(0, str(ROOT/'research/tools/eclipse_determinista'))
from comu import Run
RUN = Run('GRAMOFON_2D', '20260906', str(ROOT/'output/gramofon_2d_20260906'))
for p in [Path(RUN.vista('')), Path(RUN.lliurable('')), Path(RUN.rebut(''))]:
    p.mkdir(parents=True, exist_ok=True)

def log(s): print(time.strftime('%H:%M:%S'), s, flush=True)
def save(name, obj):
    Path(RUN.rebut(name+'.json')).write_text(json.dumps(obj, indent=2,
        default=lambda v: v.item() if isinstance(v,np.generic) else v.tolist())+'\n')
def rms(a): return float(np.sqrt(np.mean(np.asarray(a)**2)))

def panel(name, arrays, titles, lo=-.01, hi=.01, cmap='RdBu_r', colorbar='Residual log(I); escala comuna'):
    cols=min(3,len(arrays)); rows=(len(arrays)+cols-1)//cols
    fig, axes=plt.subplots(rows,cols,figsize=(5*cols,4.7*rows),squeeze=False)
    for ax,a,title in zip(axes.flat,arrays,titles):
        im=ax.imshow(a,cmap=cmap,vmin=lo,vmax=hi,interpolation='nearest')
        ax.set_title(title,fontsize=10);ax.set_xlabel('x [px]');ax.set_ylabel('y [px]')
    for ax in list(axes.flat)[len(arrays):]:ax.axis('off')
    fig.colorbar(im,ax=list(axes.flat),shrink=.72,label=colorbar)
    fig.savefig(RUN.vista(name+'.png'),dpi=110);plt.close(fig)

def coefficients(delta, q, qs, valid):
    # Least-squares Fourier cos/sin projection, with a DC nuisance term.
    c=q[valid];s=qs[valid];z=delta[valid]
    p=np.array([[np.dot(c,c),np.dot(c,s),c.sum()],
                [np.dot(c,s),np.dot(s,s),s.sum()],
                [c.sum(),s.sum(),len(c)]])
    b=np.array([np.dot(c,z),np.dot(s,z),z.sum()])
    a=np.linalg.solve(p,b)
    res=z-(a[0]*c+a[1]*s+a[2])
    return {'gain':float(a[0]),'quadrature':float(a[1]),
            'phase_deg':float(np.degrees(np.arctan2(a[1],a[0]))),
            'DC_offset':float(a[2]),'magnitude':float(np.hypot(a[0],a[1])),
            'relative_unexplained_RMS':rms(res)/max(rms(c),1e-20)}

def synthetic():
    n=1280;cy,cx=639.63,639.37;rs=100.
    y,x=np.mgrid[:n,:n];r=np.maximum(np.hypot(x-cx,y-cy),1e-3)
    th=np.arctan2(y-cy,x-cx);qrad=np.log(r/rs)
    mask=r>rs
    # Synthetic physical occlusion plus a missing sensor wedge and defect patch.
    partial=mask&(x+.28*y>130)
    partial[220:248,890:932]=False
    distance=distance_transform_edt(np.pad(partial,1))[1:-1,1:-1]
    inner=distance>162  # common full-support set, including sensor edges/holes
    adaptive_inner=distance>322  # residual and contrast each depend on radius160
    edge=partial&(distance<24)
    pure=-3*qrad
    pedestal=np.log(np.exp(pure)+.03)
    texture=.02*np.cos(5*th)+.012*np.cos(2*np.pi*(.6*x+.8*y)/73)
    base=pedestal+texture
    nulls=[];trans=[];leaks=[];loops=[];controls=[];pictures=[];labels=[]
    models={}
    for h in [96,160]:
        for kind in ['quadratic','lograd']:
            key=f'{kind}_h{h}';log('build '+key)
            model=LocalModel(partial,h,kind,qrad);models[key]=model
            dp=model.apply(pure)[0];db=model.apply(pedestal)[0]
            interior=inner&model.valid
            row={'method':key,'valid_pixels':int(model.valid.sum()),'observed_pixels':int(partial.sum()),
                'powerlaw_rms_interior':rms(dp[interior]),'powerlaw_max_abs':float(np.nanmax(np.abs(dp[model.valid]))),
                'full_support_pixels':int(interior.sum()),
                'powerlaw_rms_edge':rms(dp[edge&model.valid]),
                'pedestal_rms_interior':rms(db[interior]),'pedestal_rms_edge':rms(db[edge&model.valid])}
            if kind=='quadratic':
                xx=(x-cx)/n;yy=(y-cy)/n
                poly=1+.3*xx-.2*yy+.15*xx*xx+.07*xx*yy-.1*yy*yy
                err=model.apply(poly)[0][model.valid]
                row['polynomial_reproduction_max']=float(np.max(np.abs(err)))
                assert row['polynomial_reproduction_max']<1e-8,row
            else:
                assert row['powerlaw_max_abs']<1e-7,row
            nulls.append(row)
            if h==160:
                pictures.extend([dp,db]);labels.extend([key+' · llei de potència',key+' · amb pedestal'])
            log('null '+json.dumps(row))

    # Bad control: incomplete support and only a local constant background.
    mean=LocalModel(partial,160,'mean');dm=mean.apply(pure)[0]
    controls.append({'method':'log_mean_h160','powerlaw_rms_edge':rms(dm[edge]),
                     'powerlaw_rms_interior':rms(dm[inner&partial])})
    pictures.extend([dm,np.where(partial,0.,np.nan)]);labels.extend(['Control: mitjana local · potència','Suport observat (blanc = absent)'])
    panel('01_nuls_llenc_sencer',pictures,labels,lo=-.02,hi=.02)
    # Fourier modes; known unit response in log units. All gains fixed at1.
    # Adaptive variant has analytic gain0.002: unit slope at zero residual.
    # No empirical gain fit; it cannot change by wavelength or ROI.
    eps=.0001
    for key,model in models.items():
        log('Fourier '+key)
        d0=model.apply(base)[0]
        for wave in [4,8,16,32,64,128,256]:
            for angle in [0,45,90]:
                phi=2*np.pi*(x*np.cos(np.deg2rad(angle))+y*np.sin(np.deg2rad(angle)))/wave+.371
                q=np.cos(phi);qs=np.sin(phi)
                dq=model.apply(q)[0]  # exact differential of the fixed linear log estimator
                good=inner&model.valid
                vals=coefficients(dq,q,qs,good)
                vals.update(method=key,wavelength_px=wave,angle_deg=angle,adaptive=False)
                vals['PASS_gain']=.9<=vals['gain']<=1.1
                trans.append(vals)
                if wave in [16,64,128] and angle==45:
                    plus=d0+eps*dq;minus=d0-eps*dq
                    sp=np.sqrt(smooth(plus*plus,model.valid,model.radius)+.002**2)
                    sm=np.sqrt(smooth(minus*minus,model.valid,model.radius)+.002**2)
                    ad=.002*(plus/sp-minus/sm)/(2*eps)
                    av=coefficients(ad,q,qs,adaptive_inner&model.valid)
                    av.update(method=key,wavelength_px=wave,angle_deg=angle,adaptive=True,
                              calibration_gain=.002,epsilon=eps)
                    av['PASS_gain']=.9<=av['gain']<=1.1;trans.append(av)
        # True local arc, smooth compact angular envelope, fixed radius400.
        angle_distance=np.angle(np.exp(1j*(th+.55)))
        envelope=np.maximum(1-(angle_distance/.20)**2,0.)**3
        for width in [4,12,24,48]:
            arc=np.exp(-.5*((r-400)/width)**2)*envelope
            da=model.apply(arc)[0]
            roi=(np.abs(r-400)<3*width)&(np.abs(angle_distance)<.20)&model.valid
            projection=float(np.sum(da[roi]*arc[roi])/np.sum(arc[roi]**2))
            negative=float(np.nanmin(da[roi]))
            loops.append({'method':key,'arc_radial_sigma_px':width,
                          'matched_amplitude':projection,'negative_lobe_in_ROI':negative,
                          'negative_lobe_all_valid':float(np.nanmin(da[model.valid])),
                          'relative_shape_error':rms((da-arc)[roi])/rms(arc[roi]),
                          'PASS_amplitude':.9<=projection<=1.1})
        # Compact local bump: strict zero input outside20px, compare farfield.
        bx=cx+400;by=cy
        br=np.hypot(x-bx,y-by)/20
        bump=np.maximum(1-br,0)**4*(1+4*br)
        delta=model.apply(.1*bump)[0]
        far=(np.hypot(x-bx,y-by)>20+model.radius+2)&model.valid
        opposite=(r>350)&(r<450)&(x<cx-200)&model.valid
        leaks.append({'method':key,'input_peak_log':.1,'input_support_radius':20,
                      'operator_dependency_radius':model.radius,
                      'far_max_abs':float(np.max(np.abs(delta[far]))),
                      'opposite_rms':rms(delta[opposite])})
        for distance_px in [64,256]:
            fixed_far=(np.hypot(x-bx,y-by)>distance_px)&model.valid
            leaks[-1]['outside_'+str(distance_px)+'_rms']=rms(delta[fixed_far])
        assert leaks[-1]['far_max_abs']<1e-8,leaks[-1]

    # Annular control: same input structure changes the opposite side of the Sun.
    angular_I=np.exp(pure)*(1+.02*np.cos(5*th))
    for interp in [False,True]:
        a=nrgf(angular_I,mask,r,interp)
        b=nrgf(angular_I*np.exp(.1*bump),mask,r,interp)
        delta=b-a
        leaks.append({'method':'NRGF_'+('continuous' if interp else 'bins'),
                      'opposite_rms':rms(delta[opposite]),
                      'opposite_max_abs':float(np.max(np.abs(delta[opposite]))),
                      'fixed_analytic_calibration_to_log_units':.02/np.sqrt(2),
                      'calibrated_opposite_rms':rms(delta[opposite])*.02/np.sqrt(2)})
    # A radial ripple present in the input is not identifiable as false by shape.
    ripple=.002*np.cos(2*np.pi*r/32)
    ident=[]
    for key,model in models.items():
        dr=model.apply(ripple)[0];good=inner&model.valid
        ident.append({'method':key,'base_ring_period_px':32,
                      'input_ring_transfer':float(np.sum(dr[good]*ripple[good])/np.sum(ripple[good]**2)),
                      'interpretation':'same response whether ripple is real corona or additive error in log input'})
    # Negative controls expose any gate that merely rewards smoother/zero output.
    phase=2*np.pi*(.6*x+.8*y)/16+.371
    qc=np.cos(phase);qs=np.sin(phase)
    negative=[]
    for name,delta in [('zero',qc*0),('gain_0.1',qc*.1),('blur_sigma8',gaussian_filter(qc,8))]:
        z=coefficients(delta,qc,qs,inner)
        z.update(method=name,PASS_gain=.9<=z['gain']<=1.1)
        assert not z['PASS_gain'],z
        negative.append(z)
    save('synthetic',{'nulls':nulls,'bad_controls':controls,'Fourier':trans,'arcs':loops,
          'negative_retention_controls':negative,
          'locality':leaks,'identifiability':ident,'geometry':{'shape':[n,n],'sun_xy':[cx,cy],'radius':rs},
          'mask_correction':'interior is distance to ALL invalid support and zero-padded canvas >162px; adaptive >322px. Supersedes initial incorrectly labelled interior.',
          'interpretation':'gain tests apply to log detail at declared scales, not physical photometry'})
    fig,ax=plt.subplots(figsize=(9,5))
    for key in models:
        rows=[v for v in trans if v['method']==key and not v['adaptive'] and v['angle_deg']==45]
        ax.plot([v['wavelength_px'] for v in rows],[v['gain'] for v in rows],'-o',label=key)
    ax.axhspan(.9,1.1,color='green',alpha=.12);ax.axhline(1,color='black',lw=.5)
    ax.set_xscale('log',base=2);ax.set_xticks([4,8,16,32,64,128,256],labels=[4,8,16,32,64,128,256])
    ax.set_xlabel('Longitud d’ona [px]');ax.set_ylabel('Transferència coherent; guany fix1')
    ax.set_title('Conservar detall: Fourier a45°; franja verda0.90–1.10');ax.legend()
    fig.tight_layout();fig.savefig(RUN.vista('02_transferencia_Fourier.png'),dpi=150);plt.close(fig)
    log('synthetic COMPLETE')

if __name__=='__main__':synthetic()
