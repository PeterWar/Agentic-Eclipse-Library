from experiment import *
from operators import robust_refit
import gc

def main():
    n=1280;y,x=np.mgrid[:n,:n];cx,cy,rs=80.37,639.63,100.
    r=np.maximum(np.hypot(x-cx,y-cy),1e-8);th=np.arctan2(y-cy,x-cx)
    qr=np.log(r/rs);mask=r>rs
    # Holdout geometry differs from the first study; local neighborhood is
    # complete even for the combined2h dependency around the arc peak.
    base=np.log(np.exp(-3*qr)+.003)
    da=np.angle(np.exp(1j*(th-.47)))
    angular=np.maximum(1-(da/.12)**2,0.)**3
    mod=LocalModel(mask,160,'quadratic',qr)
    rng=np.random.default_rng(602917)
    noise_field=rng.normal(size=base.shape)
    rows=[];pics=[];titles=[]
    for noise in [0.,.001]:
        b=base+noise*noise_field
        initial=mod.apply(b)[0]
        rb,_,_=robust_refit(b,mod)
        for width in [4,12,24]:
            arc=np.exp(-.5*((r-600)/width)**2)*angular
            roi=(np.abs(r-600)<3*width)&(np.abs(da)<.12)&mask
            outer=(np.abs(r-600)<200)&(np.abs(da)<.4)&~roi&mask
            linear=mod.apply(arc)[0]
            for amp in [.0002,.002,.02]:
                log(f'robust noise{noise} width{width} amp{amp}')
                plus,mp,_=robust_refit(b+amp*arc,mod)
                minus,mm,_=robust_refit(b-amp*arc,mod)
                assert np.array_equal(mp.valid,mask) and np.array_equal(mm.valid,mask)
                response=(plus-minus)/(2*amp)
                positive=(plus-rb)/amp
                negative=(rb-minus)/amp
                even=(plus+minus-2*rb)/(2*amp)
                for name,z in [('Q2_linear',linear),('Q2_robust_central',response),
                               ('Q2_robust_positive',positive),('Q2_robust_negative',negative)]:
                    gain=float(np.sum(z[roi]*arc[roi])/np.sum(arc[roi]**2))
                    shape=rms((z-arc)[roi])/rms(arc[roi])
                    halo=float(np.max(np.abs(z[mask&~roi])))
                    row={'method':name,'noise_sigma_log':noise,'arc_sigma_px':width,
                         'injected_peak_log':amp,'matched_gain':gain,'shape_error':shape,
                         'outside_arc_max':halo,'all_valid_min':float(np.nanmin(z[mask])),
                         'even_distortion_relative_RMS':rms(even[roi])/rms(arc[roi]),
                         'PASS_preservation':.9<=gain<=1.1 and shape<=.1 and halo<=.05}
                    rows.append(row)
                if noise==.001 and amp==.02:
                    pics.extend([arc,linear,positive]);titles.extend([
                        f'Arc conegut · sigma{width}',f'Q2 lineal · sigma{width}',f'Q2 robust positiu · sigma{width}'])
                save('robust_arcs',{'rows':rows,'geometry':{'shape':[n,n],'sun_xy':[cx,cy],
                     'arc_radius':600,'arc_angle':.47,'arc_angular_halfwidth':.12},
                     'threshold_log':.002,'one_refit':True,'dependency_radius':320,
                     'reference':'known arc, no gain fit; weights recomputed in plus/minus',
                     'criteria':'gain0.90..1.10 AND relative shape error<=0.10 AND external halo<=0.05'})
                del mp,mm;gc.collect()
    panel('05_arcs_robust_llenc_sencer',pics,titles,lo=-.2,hi=1.,colorbar='Resposta dividida per amplitud injectada; pic esperat1')
    # Additional native-size close-up follows the complete synthetic canvases.
    px=int(cx+600*np.cos(.47));py=int(cy+600*np.sin(.47))
    cuts=[z[py-150:py+150,px-150:px+150] for z in pics]
    panel('06_arcs_robust_detall',cuts,titles,lo=-.2,hi=1.,colorbar='Resposta dividida per amplitud injectada; pic esperat1')
    log('robust COMPLETE')

if __name__=='__main__':main()
