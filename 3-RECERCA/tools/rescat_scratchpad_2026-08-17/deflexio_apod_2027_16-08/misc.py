import numpy as np
print("=== SUN'S APPARENT MOTION AGAINST THE STARS ===")
v=360*3600/365.256/86400
print(f"  {v:.4f} arcsec/s -> over 371 s of totality the Sun moves {v*371:.1f}\" against the star field")
for T in (5,10,20,30,60):
    print(f"   solar-rate tracking, {T:2d} s exposure -> star trail {v*T:5.2f}\"")
print("\n=== POLAR MISALIGNMENT -> DRIFT ===")
w=15.041
for d_arcmin in (120,60,30,10,5,2,1):
    print(f"  misalignment {d_arcmin:4d}' -> drift {w*(d_arcmin*60/206265)*1000:7.1f} mas/s"
          f"  = {w*(d_arcmin*60/206265)*10:6.3f}\" in 10 s, {w*(d_arcmin*60/206265)*30:6.2f}\" in 30 s")
print("  (2026 campaign measured 0.610\"/s total, ~0.48\"/s from a ~2 deg daylight polar alignment)")

print("\n=== HOW MANY FRAMES TO AVERAGE THE ATMOSPHERE DOWN ===")
print("  Zacharias 1996: sigma_atm = sigma_an*(100/T)^0.5*(fov/20')^(1/3)/cos z ; sigma_an=3 mas @1\", 6 @2\"")
def atm(seeing,T,fov_arcmin,z_deg,D_m):
    san=3.0*seeing
    return san*(100./T)**0.5*(fov_arcmin/20.)**(1/3.)/np.cos(np.radians(z_deg))*(0.9/D_m)**(1/6.)
for lab,see,z,D,fov in [("Leon 2026 train B (per 10.3 s frame)",2.5,80.8,0.09,180),
                        ("Leon 2026 train B (24 s of anchors)",2.5,80.8,0.09,180),
                        ("Luxor 2027, 3\" seeing, 1 x 10 s",3.0,8.3,0.10,180),
                        ("Luxor 2027, 3\" seeing, 300 s total",3.0,8.3,0.10,180),
                        ("Luxor 2027, 5\" daytime seeing, 300 s",5.0,8.3,0.10,180)]:
    T=10.3 if "10.3" in lab else (24 if "24 s" in lab else (10 if "1 x 10" in lab else 300))
    print(f"  {lab:42s} -> {atm(see,T,fov,z,D)*1000:7.1f} mas")
