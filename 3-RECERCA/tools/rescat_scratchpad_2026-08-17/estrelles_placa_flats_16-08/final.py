from skyfield.api import load, wgs84, Star
from skyfield.data import hipparcos
import numpy as np, pandas as pd, math

ts=load.timescale(); eph=load('/Users/USUARI/.cache/skyfield/de440s.bsp')
t=ts.utc(2026,8,12,18,29,38)
lloc=eph['earth']+wgs84.latlon(42.299407,-5.02503,elevation_m=798.0)
app_sun=lloc.at(t).observe(eph['sun']).apparent()
sra,sdec,_=app_sun.radec(epoch='date')
with open('hip_main.dat') as f: df=hipparcos.load_dataframe(f)
cand=pd.read_csv('candidates_v8.csv')

# angle de posicio respecte del nord de la data
rows=[]
for _,r in cand.iterrows():
    st=Star.from_dataframe(df.loc[int(r.HIP)])
    ap=lloc.at(t).observe(st).apparent()
    ra,de,_=ap.radec(epoch='date')
    d0=sdec.radians; a0=sra.radians; d1=de.radians; a1=ra.radians
    pa=math.degrees(math.atan2(math.sin(a1-a0)*math.cos(d1),
        math.cos(d0)*math.sin(d1)-math.sin(d0)*math.cos(d1)*math.cos(a1-a0)))%360
    rows.append(pa)
cand['PA_deg']=rows

F0=8.97e5; ETA_PX=0.27; ETA_STAR=0.135; A_EXT=0.37*6.2
rr=np.array([1.2,1.5,2,2.5,3,4,5,6,8,10,14,20])
bb=np.array([4.4e-7,1.2e-7,3.5e-8,1.4e-8,6.5e-9,2.2e-9,1.1e-9,6.0e-10,2.6e-10,1.4e-10,6e-11,2.5e-11])
mu_cor=-10.62-2.5*np.log10(bb)+A_EXT
RS=947.07/3600
T={'sony':dict(D=10.7,sc=3.234,ex=[(8.0,2),(2.0,3),(1.0,3)],npx=20,fwc=46000,rn=3.0),
   'r6'  :dict(D=9.0, sc=2.158,ex=[(10.3,3),(2.0,3),(1.0,2),(0.5,4)],npx=40,fwc=55000,rn=5.0)}
def snr(tr,V,sep,mu_sky):
    A=math.pi*(tr['D']/2)**2; om=tr['sc']**2
    mu_c=np.interp(sep/RS,rr,mu_cor)
    mu=-2.5*math.log10(10**(-0.4*mu_sky)+10**(-0.4*mu_c))
    S=0;B=0;used=[]
    for tex,n in tr['ex']:
        b=F0*10**(-0.4*mu)*A*om*ETA_PX*tex
        if b>0.9*tr['fwc']: continue
        used.append(tex); B+=n*tr['npx']*(b+tr['rn']**2); S+=n*ETA_STAR*F0*A*tex
    if not used: return None,[]
    S*=10**(-0.4*(V+A_EXT))
    return S/math.sqrt(S+B), used

for mu_sky in [11,12,14]:
    cand[f'snr_sony_{mu_sky}']=[ (snr(T['sony'],r.Vmag,r.sep_deg,mu_sky)[0]) for _,r in cand.iterrows()]
    cand[f'snr_r6_{mu_sky}']  =[ (snr(T['r6'],  r.Vmag,r.sep_deg,mu_sky)[0]) for _,r in cand.iterrows()]
cand['exp_sony']=[",".join(f"{x:g}" for x in snr(T['sony'],r.Vmag,r.sep_deg,12)[1]) for _,r in cand.iterrows()]
cand['exp_r6']  =[",".join(f"{x:g}" for x in snr(T['r6'],  r.Vmag,r.sep_deg,12)[1]) for _,r in cand.iterrows()]
pd.set_option('display.width',300)
fm=lambda x: '  --' if x is None or not np.isfinite(x) else f"{x:4.0f}"
print("=== TAULA FINAL (SNR apilat; corona local sumada al fons; nomes exposicions no saturades) ===")
print(f"{'HIP':>6} {'HD':>7} {'V':>5} {'sep°':>6} {'r/Rs':>5} {'PA°':>5} | {'px_sony':>7} {'camp':>8} {'S@11':>5}{'S@12':>5}{'S@14':>5} {'exp':>9} | {'px_r6':>6} {'camp':>8} {'R@11':>5}{'R@12':>5}{'R@14':>5} {'exp':>12}")
for _,r in cand.iterrows():
    print(f"{int(r.HIP):6d} {r.HD:>7} {r.Vmag:5.2f} {r.sep_deg:6.3f} {r.r_Rsol:5.2f} {r.PA_deg:5.1f} | "
          f"{r.px_sony:7.0f} {r.sony:>8} {fm(r.snr_sony_11)} {fm(r.snr_sony_12)} {fm(r.snr_sony_14)} {r.exp_sony:>9} | "
          f"{r.px_r6:6.0f} {r.r6:>8} {fm(r.snr_r6_11)} {fm(r.snr_r6_12)} {fm(r.snr_r6_14)} {r.exp_r6:>12}")
cand.to_csv('taula_final.csv',index=False)
print("\nfitxer: taula_final.csv")
