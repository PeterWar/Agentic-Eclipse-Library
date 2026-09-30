from skyfield.api import load, wgs84
import numpy as np
eph = load('/Users/USUARI/.cache/skyfield/de440s.bsp')
ts = load.timescale()
earth, sun, moon = eph['earth'], eph['sun'], eph['moon']
# Luxor
site = earth + wgs84.latlon(25.6872, 32.6396, elevation_m=76)
# greatest eclipse ~ 10:07 UT; Luxor totality ~ 10:06 UT
t = ts.utc(2027, 8, 2, 10, 6, 0)
ast = site.at(t).observe(sun).apparent()
ra, dec, d = ast.radec()
alt, az, _ = ast.altaz()
print("Luxor 2027-08-02 10:06 UT")
print(f"  Sun RA  = {ra.hours:.4f} h = {ra._degrees:.4f} deg")
print(f"  Sun Dec = {dec.degrees:.4f} deg")
print(f"  Sun Alt = {alt.degrees:.3f} deg   airmass(sec z) = {1/np.cos(np.radians(90-alt.degrees)):.4f}")
print(f"  Sun ang radius = {np.degrees(np.arcsin(696000/ d.km))*3600:.1f} arcsec")
# angular separation to M44 (Praesepe) J2000 RA 130.100 Dec +19.667  -> precess roughly to date
def sep(ra1,dec1,ra2,dec2):
    r1,d1,r2,d2 = map(np.radians,[ra1,dec1,ra2,dec2])
    return np.degrees(np.arccos(np.sin(d1)*np.sin(d2)+np.cos(d1)*np.cos(d2)*np.cos(r1-r2)))
from skyfield.api import Star
targets = {
 "M44 Praesepe": (130.100, 19.667),
 "delta Cnc (V3.94)": (131.171, 18.154),
 "gamma Cnc (V4.66)": (130.821, 21.469),
 "eta Cnc (V5.33)": (131.674, 20.44),
 "theta Cnc (V5.35)": (129.310, 18.099),
 "M67": (132.825, 11.8),
 "Regulus": (152.093, 11.967),
}
sr = np.degrees(np.arcsin(696000/d.km))  # solar radius in deg
print(f"  1 solar radius = {sr*60:.2f} arcmin")
for k,(r,dd) in targets.items():
    s = sep(ra._degrees, dec.degrees, r, dd)
    print(f"  {k:22s} sep = {s:6.3f} deg = {s/sr:6.2f} R_sun")
