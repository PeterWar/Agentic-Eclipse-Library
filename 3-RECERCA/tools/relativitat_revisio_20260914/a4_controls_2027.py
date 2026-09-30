from a2_ephemeris import *
from a3_inference import forecast,frame_part,combine,SCALE,RS
from skyfield.data import hipparcos
from scipy.optimize import brentq,minimize_scalar

def geometry(lat,lon,elev,date):
    observer=eph['earth']+wgs84.latlon(lat,lon,elevation_m=elev)
    base=ts.utc(*date)
    def get(sec):
        o=observer.at(ts.tt_jd(base.tt+sec/86400));s=o.observe(eph['sun']).apparent();m=o.observe(eph['moon']).apparent()
        return s,m
    def gap(sec):
        s,m=get(sec);sr=np.arcsin(695700/s.distance().km);mr=np.arcsin(1737.4/m.distance().km)
        return s.separation_from(m).radians-(mr-sr)
    grid=np.arange(0,86400,60);g=np.array([gap(s) for s in grid]);i=g.argmin();res=minimize_scalar(gap,bounds=(grid[i-1],grid[i+1]),method='bounded')
    rootidx=np.flatnonzero(g[:-1]*g[1:]<0);roots=[brentq(gap,grid[j],grid[j+1],xtol=.001) for j in rootidx]
    mid=np.mean(roots);sun,moon=get(mid);alt,az,_=sun.altaz();a=alt.degrees;air=1/(np.sin(np.radians(a))+.50572*(a+6.07995)**-1.6364)
    return dict(lat=lat,lon=lon,elevation_m=elev,mid_utc=ts.tt_jd(base.tt+mid/86400).utc_iso(),totality_s=roots[-1]-roots[0],sun_alt_deg=float(a),sun_az_deg=float(az.degrees),airmass_approx=float(air),solar_radius_arcsec=float(np.arcsin(695700/sun.distance().km)*180/np.pi*3600),model='Spherical Sun 695700 km, Moon 1737.4 km, DE440s; no lunar topography; forecast UTC depends on Earth rotation model, rounded for planning.')

def main():
    d=pd.read_csv(O/'A3_analysis_sample.csv');a=d[d.use10].copy();sens=[]
    # Perturb the declared environmental assumptions without fitting to epsilon.
    for variant in ['baseline','T10','clock_plus15s','BV_nuisance']:
      for kind in ['radial','affine']:
        b=a.copy()
        if variant=='T10':b.x0+=b.cold_dx;b.y0+=b.cold_dy
        if variant=='clock_plus15s':b.x0+=b.time15_dx;b.y0+=b.time15_dy
        parts=[]
        for _,f in b.groupby('frame'):
            p=frame_part(f,kind,'equal')
            if p is None:continue
            if variant=='BV_nuisance':
                # One color-correlated displacement per output axis; diagnostic,
                # not a calibrated passband/refraction model.
                z=f.BV.fillna(.65).to_numpy()-.65;E=np.zeros((2*len(f),2));E[::2,0]=z;E[1::2,1]=z
                Aw=np.c_[p['Aw'],E*p['w'][:,None]];P=np.linalg.pinv(Aw)
                p.update(Aw=Aw,yr=p['yw']-Aw@(P@p['yw']),gr=p['gw']-Aw@(P@p['gw']),npar=Aw.shape[1])
                p['I']=float(p['gr']@p['gr']);p['b']=float(p['gr']@p['yr'])
            parts.append(p)
        for tag in ['Sony','Vixen','combined']:
            pp=parts if tag=='combined' else [p for p in parts if p['a'].source.iloc[0]==tag]
            q=combine(pp,variant+'/'+kind+'/'+tag)
            if q:sens.append(q)
    dump('A4_environment_sensitivity.json',sens)
    geos={n:geometry(lat,lon,el,date) for n,lat,lon,el,date in [('Leon_2026',42.299407,-5.02503,798,(2026,8,12)),('Cadis_2027',36.5297,-6.2926,15,(2027,8,2)),('Luxor_2027',25.6872,32.6396,76,(2027,8,2))]}
    dump('A4_geometry_2027.json',geos)
    hip_path=W.parent/'catalegs/hip_main.dat'
    with hip_path.open('rb') as f:hip=hipparcos.load_dataframe(f)
    hip=hip[np.isfinite(hip.ra_degrees)&np.isfinite(hip.dec_degrees)]
    t=ts.from_datetime(datetime.datetime.fromisoformat(geos['Luxor_2027']['mid_utc'].replace('Z','+00:00')))
    site=eph['earth']+wgs84.latlon(25.6872,32.6396,elevation_m=76);o=site.at(t);sun=o.observe(eph['sun']).apparent();ra,dec,_=sun.radec()
    near=(abs(hip.ra_degrees-ra._degrees)<6)&(abs(hip.dec_degrees-dec.degrees)<6)&(hip.magnitude<=9)
    hp=hip[near];stars=o.observe(Star.from_dataframe(hp)).apparent();sra,sdec,_=stars.radec()
    rr=np.radians(sra._degrees);dd=np.radians(sdec.degrees);r0=np.radians(ra._degrees);d0=np.radians(dec.degrees)
    den=np.sin(dd)*np.sin(d0)+np.cos(dd)*np.cos(d0)*np.cos(rr-r0)
    x=np.cos(dd)*np.sin(rr-r0)/den*180/np.pi*3600;y=(np.sin(dd)*np.cos(d0)-np.cos(dd)*np.sin(d0)*np.cos(rr-r0))/den*180/np.pi*3600
    r=stars.separation_from(sun).arcseconds()/geos['Luxor_2027']['solar_radius_arcsec']
    field=pd.DataFrame(dict(HIP=hp.index,V=hp.magnitude,x_as=x,y_as=y,r_sun=r,alpha_GR_as=1.7511903255599846/r))
    field=field[(field.r_sun>1.5)&(field.r_sun<15)].sort_values('r_sun')
    scenarios=[]
    for tag,ww,hh in [('Sony',7968*3.2020,5320*3.2020),('Vixen',6960*2.1495,4640*2.1495)]:
        field[tag+'_field']=(abs(field.x_as)<ww/2)&(abs(field.y_as)<hh/2)
        for vlim in [7,8,9]:
            sample=field[(field.V<=vlim)&field[tag+'_field']];p=sample[['x_as','y_as']].to_numpy()
            for sig in [.03,.05,.1,.2]:
              for kind in ['similarity','affine','radial']:
                q=forecast(p,sig,kind,alpha=1.7511903255599846*geos['Luxor_2027']['solar_radius_arcsec']/RS)
                scenarios.append(dict(source=tag,V_limit=vlim,per_star_sigma_arcsec=sig,kind=kind,**q,qualification='Conditional actual Hipparcos geometry, Sun-centred FOV axes E/N, every selected star assumed measured at stated independent uncertainty; not a detection prediction or complete faint catalogue.'))
    field.to_csv(O/'A4_Hipparcos_2027_field.csv',index=False);pd.DataFrame(scenarios).to_csv(O/'A4_2027_conditional_scenarios.csv',index=False)
    print('GEOMETRY',json.dumps(geos));print('SCENARIOS',[(q['source'],q['n'],q['kind'],q['sigma_epsilon']) for q in scenarios if q['V_limit']==8 and q['per_star_sigma_arcsec']==.1]);print(field.head(4).to_string(index=False))
if __name__=='__main__':main()
