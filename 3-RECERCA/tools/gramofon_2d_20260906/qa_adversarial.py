from experiment import *

def main():
    n=1280;y,x=np.mgrid[:n,:n];cx,cy,rs=639.37,639.63,100.
    r=np.maximum(np.hypot(x-cx,y-cy),1e-8);qr=np.log(r/rs);mask=r>rs
    mask&=(x+.28*y>130);mask[220:248,890:932]=False
    distance=distance_transform_edt(np.pad(mask,1))[1:-1,1:-1]
    zones=[('complete_common',distance>162),('all_boundary_24',mask&(distance<24))]
    for rr in [110,180,400]:
        for angle in [0,np.pi/4,np.pi,1.5*np.pi]:
            xx=cx+rr*np.cos(angle);yy=cy+rr*np.sin(angle)
            z=(np.abs(x-xx)<32)&(np.abs(y-yy)<32)&mask
            zones.append((f'r{rr}_theta{angle:.3f}',z))
    rows=[];null=[]
    for kind in ['quadratic','lograd']:
        model=LocalModel(mask,160,kind,qr)
        assert np.array_equal(model.valid,mask)
        for wave in [16,32,64,128]:
            for angle in [0,45,90]:
                phi0=2*np.pi*(x*np.cos(np.deg2rad(angle))+y*np.sin(np.deg2rad(angle)))/wave
                qc=np.cos(phi0);qs=np.sin(phi0)
                dc=model.apply(qc)[0];ds=model.apply(qs)[0]
                for phase in [.371,1.237,2.403]:
                    q=qc*np.cos(phase)-qs*np.sin(phase)
                    s=qs*np.cos(phase)+qc*np.sin(phase)
                    delta=dc*np.cos(phase)-ds*np.sin(phase)
                    for zone,good in zones:
                        z=coefficients(delta,q,s,good)
                        z.update(method=kind,wavelength_px=wave,angle_deg=angle,
                                 phase=phase,zone=zone,pixels=int(good.sum()))
                        z['PASS_transfer']=.9<=z['gain']<=1.1 and abs(z['quadrature'])<=.05 and z['relative_unexplained_RMS']<=.1
                        rows.append(z)
        # Non-basis smooth field with slope changes, sky pedestal and 2D sky.
        sky=.03*(1+.2*(x-cx)/n+.1*((y-cy)/n)**2)
        I=np.exp(-2*qr)+.4*np.exp(-6*qr)+sky
        result=model.apply(np.log(I))[0]
        ideal=model.apply(np.log(I-sky))[0]
        for zone,good in zones:
            null.append({'method':kind,'zone':zone,'RMS_log':rms(result[good]),
                         'max_abs_log':float(np.max(np.abs(result[good]))),
                         'known_sky_removed_RMS':rms(ideal[good]),
                         'false_detail_vs_0.002':rms(result[good])/.002,
                         'PASS_1pct_of_weak_probe':rms(result[good])<.00002})
    save('adversarial',{'Fourier':rows,'smooth_nonbasis_nulls':null,
        'gain_reference':'known unit Fourier mode in log units, no local gain fit',
        'PASS_transfer':'0.90..1.10 gain AND |quadrature|<=.05 AND unexplained RMS<=.1',
        'null_threshold':'RMS<1% of fixed weak0.002log probe; conservative engineering criterion',
        'scope':'separates full support and limb/boundary; any failures prohibit full-canvas acceptance'})
    log('adversarial QA COMPLETE')

if __name__=='__main__':main()
