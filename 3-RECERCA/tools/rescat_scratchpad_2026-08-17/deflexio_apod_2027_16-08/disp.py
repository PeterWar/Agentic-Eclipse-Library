import numpy as np
def nm1(lam_um,P_hPa,T_C):
    s2=1.0/lam_um**2
    ns=1e-8*(8342.13+2406030/(130-s2)+15997/(38.9-s2))
    return ns*(P_hPa*100/101325.0)*(288.15/(T_C+273.15))
def R(lam,z_deg,P,T):
    return nm1(lam,P,T)*206265.0*np.tan(np.radians(z_deg))
cases=[("Leon 2026  alt 9.2",  80.8, 925.0, 25.0),
       ("Luxor 2027 alt 81.7",  8.27,1005.0, 38.0)]
bands={"Bayer B(450)-R(650) full colour":(0.45,0.65),
       "unfiltered 400-700":(0.40,0.70),
       "Sloan r' 560-700":(0.56,0.70),
       "R 590-690":(0.59,0.69),
       "narrowband 656/10":(0.6535,0.6585),
       "Bayer green plane 500-580":(0.50,0.58)}
for name,z,P,T in cases:
    print(f"\n{name}  (z={z} deg):")
    for b,(l1,l2) in bands.items():
        d=abs(R(l1,z,P,T)-R(l2,z,P,T))
        print(f"   {b:34s}  dispersion = {d:7.3f} arcsec")
