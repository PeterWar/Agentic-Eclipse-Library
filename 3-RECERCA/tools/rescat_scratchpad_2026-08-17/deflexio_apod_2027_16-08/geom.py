import numpy as np
from skyfield.api import load, wgs84
from skyfield.framelib import ecliptic_frame

eph = load('/Users/USUARI/.cache/skyfield/de440s.bsp')
ts  = load.timescale()
earth, sun, moon = eph['earth'], eph['sun'], eph['moon']

# Luxor
site = wgs84.latlon(25.6872, 32.6396, elevation_m=89)
obs  = earth + site

# scan totality window 2027-08-02 ~10:02-10:09 UT
t0 = ts.utc(2027,8,2,10,0,0)
print("=== Sun alt/az and parallactic-angle rate at Luxor, 2027-08-02 ===")
for sec in [0, 120, 127, 250, 383, 510]:
    t = ts.utc(2027,8,2,10,2,7+ (sec))
    app = obs.at(t).observe(sun).apparent()
    alt, az, d = app.altaz()
    print(f"  t=C2+{sec:4d}s  alt={alt.degrees:7.3f}  az={az.degrees:8.3f}")

t = ts.utc(2027,8,2,10,5,18)   # mid-totality
app = obs.at(t).observe(sun).apparent()
alt, az, dist = app.altaz()
ra, dec, _ = app.radec()
phi = np.radians(25.6872); a=np.radians(alt.degrees); A=np.radians(az.degrees)
omega = 7.292115e-5  # rad/s
# parallactic angle rate for a fixed star:  dq/dt = omega*cos(phi)*cos(A)/cos(alt)
dqdt = omega*np.cos(phi)*np.cos(A)/np.cos(a)     # rad/s
# altitude rate
daltdt = -omega*np.cos(phi)*np.sin(A)
# azimuth rate
dazdt = omega*(np.sin(phi) - np.cos(phi)*np.cos(A)*np.tan(a)*0 )  # use exact below
print()
print(f"mid-totality: alt={alt.degrees:.4f} az={az.degrees:.4f} dec={dec.degrees:.4f} RA={ra.hours*15:.4f}")
print(f"parallactic-angle rate = {np.degrees(dqdt)*3600:.2f} arcsec/s = {np.degrees(dqdt):.5f} deg/s")
print(f"  -> field rotation over 383 s totality = {np.degrees(dqdt)*383:.3f} deg")
print(f"  tangential smear at 2 deg field radius over 383 s = {np.degrees(dqdt)*383*np.pi/180*2*3600:.1f} arcsec")
print(f"  tangential smear at 2 deg over ONE 10 s frame     = {np.degrees(dqdt)*10*np.pi/180*2*3600:.2f} arcsec")
print(f"altitude rate = {np.degrees(daltdt)*3600:.3f} arcsec/s")

# refraction at 81.7 deg, Luxor Aug (P~1005 hPa, T~40 C)
def refr_bennett(alt_deg, P=1005.0, T=40.0):
    R = 1.0/np.tan(np.radians(alt_deg + 7.31/(alt_deg+4.4)))  # arcmin
    R *= (P/1010.0)*(283.0/(273.0+T))
    return R*60.0  # arcsec
for altd,lab in [(81.73,'Luxor 2027'),(9.2,'Leon 2026'),(67.8,'Benghazi'),(37.9,'S Spain')]:
    P,T = (1005,40) if altd>60 else (925,25)
    R = refr_bennett(altd,P,T)
    # local compression dR/dalt
    h=1e-3
    dRdz = (refr_bennett(altd-h,P,T)-refr_bennett(altd+h,P,T))/(2*h)   # arcsec per deg of alt
    comp = dRdz/3600.0
    print(f"{lab:12s} alt={altd:6.2f}  R={R:8.2f}\"  vertical compression = {comp*100:.4f} %")
