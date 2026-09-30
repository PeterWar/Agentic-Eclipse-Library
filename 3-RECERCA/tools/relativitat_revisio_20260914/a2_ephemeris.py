"""A paired no-Sun/GR forward model: no subtraction of aberration or other masses."""
from a1_inputs import *
from skyfield.api import Loader,Star,wgs84
import skyfield
L=Loader('/Users/USUARI/.cache/skyfield');ts=L.timescale(builtin=True);eph=L('de440s.bsp')
obs=eph['earth']+wgs84.latlon(42.299407,-5.02503,elevation_m=798)
def uvec(alt,az):
    a,z=np.radians(alt),np.radians(az)
    return np.array([np.cos(a)*np.cos(z),np.cos(a)*np.sin(z),np.sin(a)])
def project(ap,sun,T=20,P=930):
    al,az,_=ap.altaz(temperature_C=T,pressure_mbar=P)
    sa,sz,_=sun.altaz(temperature_C=T,pressure_mbar=P)
    r=uvec(sa.degrees,sz.degrees);e2=np.array([0.,0.,1.])-r*r[2];e2/=np.linalg.norm(e2);e1=np.cross(e2,r)
    u=uvec(al.degrees,az.degrees);den=r@u
    return np.stack([e1@u/den,e2@u/den],axis=-1)*(180/np.pi*3600)
def calculate(cat,t,T=20,P=930):
    s=Star(ra_hours=cat._RAJ2000.to_numpy()/15,dec_degrees=cat._DEJ2000.to_numpy(),ra_mas_per_year=cat.pmRA.fillna(0).to_numpy(),dec_mas_per_year=cat.pmDE.fillna(0).to_numpy(),epoch=ts.tt_jd(2451545.0))
    a=obs.at(t).observe(s);sun=obs.at(t).observe(eph['sun']).apparent()
    p0=project(a.apparent(deflectors=(599,699)),sun,T,P);p1=project(a.apparent(),sun,T,P)
    return p0,p1,sun
def main():
    df=pd.read_csv(O/'A1_native_centroids.csv');cat=pd.read_csv(W/'xmatch/cat2_sony.csv');cat=cat[cat.TYC.isin(df.TYC)].copy().reset_index(drop=True)
    frames=json.loads((O/'A1_frames.json').read_text());rows=[]
    for name,fr in frames.items():
        t=ts.from_datetime(datetime.datetime.fromisoformat(fr['utc_mid']))
        p0,p1,sun=calculate(cat,t);cold,_warm,_=calculate(cat,t,T=10);pt,_,_=calculate(cat,ts.tt_jd(t.tt+15/86400))
        for i,c in cat.iterrows():rows.append(dict(frame=name,TYC=c.TYC,x0=p0[i,0],y0=p0[i,1],gx=p1[i,0]-p0[i,0],gy=p1[i,1]-p0[i,1],cold_dx=cold[i,0]-p0[i,0],cold_dy=cold[i,1]-p0[i,1],time15_dx=pt[i,0]-p0[i,0],time15_dy=pt[i,1]-p0[i,1]))
    pd.DataFrame(rows).to_csv(O/'A2_no_sun_and_GR.csv',index=False)
    t=ts.utc(2026,8,12,18,29,48);p0,p1,sun=calculate(cat,t)
    old=cat[['xh_as','yh_as']].to_numpy();err=p1-old
    # No-refraction radial asymptote check for model scale, not a test of observed data.
    p0n,p1n,sun=calculate(cat,t,P=0);d=p1n-p0n;rr=np.linalg.norm(p0n,axis=1);rad=(d*p0n).sum(1)/rr;tan=(d[:,0]*p0n[:,1]-d[:,1]*p0n[:,0])/rr
    a=4*1.3271244e20/(299792458.**2*6.957e8)*180/np.pi*3600
    rs=np.arcsin(695700/sun.distance().km)*180/np.pi*3600
    valid=rr>rs*1.1;relative=rad[valid]/(a*rs/rr[valid])-1
    # The first 1/r check failed at 4 degrees (0.62%): angular deflection and
    # displacement in a gnomonic plane differ by sec(chi)^2. Retain that result;
    # validate against the finite-angle formula in the same coordinates instead.
    chi=np.arctan(rr/(180/np.pi*3600))
    exact=2*1.3271244e20/(299792458.**2*sun.distance().km*1000)/np.tan(chi/2)/np.cos(chi)**2*(180/np.pi*3600)
    rel_exact=rad[valid]/exact[valid]-1
    rep=dict(skyfield_version=skyfield.__version__,solar_deflectors_off=[599,699],baseline='Aberration, light-time, proper motion, other masses and Earth deflection preserved. Solar coefficient alone exposed.',catalog_old_max_abs_difference_arcsec=float(abs(err).max()),alpha_limb_nominal_arcsec=a,solar_radius_arcsec=rs,initial_small_angle_check_failed=True,no_refraction_radial_relative_difference_max=float(abs(relative).max()),finite_angle_gnomonic_relative_difference_max=float(abs(rel_exact).max()),tangential_deflection_max_arcsec=float(abs(tan[valid]).max()),parallax='Not provided by legacy Tycho catalog; not a qualified absolute GR catalogue.',epochs=frames)
    assert abs(err).max()<1e-5
    assert abs(rel_exact).max()<.0002
    dump('A2_ephemeris_check.json',rep);print({k:v for k,v in rep.items() if k!='epochs'})
if __name__=='__main__':main()
