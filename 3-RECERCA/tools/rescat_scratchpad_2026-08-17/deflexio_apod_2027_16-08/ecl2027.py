import numpy as np
from skyfield.api import load, wgs84, Loader
from skyfield import almanac

load_ = Loader('/Users/USUARI/.cache/skyfield')
eph = load_('de440s.bsp')
ts = load_.timescale()

sun, moon, earth = eph['sun'], eph['moon'], eph['earth']

R_SUN_KM = 696000.0
R_MOON_KM = 1737.4
AU_KM = 149597870.7

def sep_and_sd(t, site):
    obs = (earth + site).at(t)
    s = obs.observe(sun).apparent()
    m = obs.observe(moon).apparent()
    sepd = s.separation_from(m).degrees
    d_s = s.distance().km
    d_m = m.distance().km
    sd_s = np.degrees(np.arcsin(R_SUN_KM/d_s))
    sd_m = np.degrees(np.arcsin(R_MOON_KM/d_m))
    return sepd, sd_s, sd_m

def f_total(t, site):
    """negative when totality (moon disk fully covers sun)"""
    sepd, sd_s, sd_m = sep_and_sd(t, site)
    return sepd - (sd_m - sd_s)

def f_partial(t, site):
    sepd, sd_s, sd_m = sep_and_sd(t, site)
    return sepd - (sd_m + sd_s)

def find_root(func, site, t0, t1, tol_s=0.005):
    a, b = t0.tt, t1.tt
    fa = func(ts.tt_jd(a), site)
    fb = func(ts.tt_jd(b), site)
    if fa*fb > 0:
        return None
    for _ in range(80):
        mid = 0.5*(a+b)
        fm = func(ts.tt_jd(mid), site)
        if fa*fm <= 0:
            b, fb = mid, fm
        else:
            a, fa = mid, fm
        if (b-a)*86400 < tol_s:
            break
    return ts.tt_jd(0.5*(a+b))

def circumstances(lat, lon, elev_m=0.0, day='2027-08-02'):
    site = wgs84.latlon(lat, lon, elevation_m=elev_m)
    y, mo, d = [int(x) for x in day.split('-')]
    # coarse scan over the day
    tgrid = ts.utc(y, mo, d, 0, 0, np.arange(0, 86400, 30.0))
    f = f_total(tgrid, site)
    fp = f_partial(tgrid, site)
    res = {'lat': lat, 'lon': lon, 'elev': elev_m}
    imin = int(np.argmin(f))
    res['min_f_total'] = float(f[imin])
    res['total'] = bool(f.min() < 0)
    res['partial'] = bool(fp.min() < 0)
    # magnitude / obscuration proxy at greatest eclipse
    tmax = tgrid[imin]
    sepd, sd_s, sd_m = sep_and_sd(tmax, site)
    res['mag'] = float((sd_s + sd_m - sepd)/(2*sd_s))
    res['t_max'] = tmax
    if res['total']:
        # bracket sign changes
        sgn = np.sign(f)
        idx = np.where(np.diff(sgn) != 0)[0]
        c2 = find_root(f_total, site, tgrid[idx[0]], tgrid[idx[0]+1])
        c3 = find_root(f_total, site, tgrid[idx[-1]], tgrid[idx[-1]+1])
        res['C2'], res['C3'] = c2, c3
        res['dur_s'] = (c3.tt - c2.tt)*86400.0
        tmid = ts.tt_jd(0.5*(c2.tt+c3.tt))
    else:
        res['dur_s'] = 0.0
        tmid = tmax
    if res['partial']:
        sgnp = np.sign(fp)
        idxp = np.where(np.diff(sgnp) != 0)[0]
        res['C1'] = find_root(f_partial, site, tgrid[idxp[0]], tgrid[idxp[0]+1])
        res['C4'] = find_root(f_partial, site, tgrid[idxp[-1]], tgrid[idxp[-1]+1])
    res['t_mid'] = tmid
    alt, az, _ = (earth + site).at(tmid).observe(sun).apparent().altaz(temperature_C=25.0, pressure_mbar=1010.0)
    res['sun_alt'] = alt.degrees
    res['sun_az'] = az.degrees
    # geometric (unrefracted) altitude too
    altg, azg, _ = (earth + site).at(tmid).observe(sun).apparent().altaz()
    res['sun_alt_geo'] = altg.degrees
    # Kasten-Young airmass on refracted altitude
    h = res['sun_alt']
    res['airmass'] = 1.0/(np.sin(np.radians(h)) + 0.50572*(h + 6.07995)**-1.6364) if h > 0 else np.nan
    return res

def fmt(t):
    return t.utc_strftime('%H:%M:%S') if t is not None else '--'

sites = [
    ('Cadiz, ES',        36.5297,  -6.2926, 15),
    ('Tarifa, ES',       36.0143,  -5.6044, 20),
    ('Gibraltar',        36.1408,  -5.3536, 10),
    ('Malaga, ES',       36.7213,  -4.4213, 30),
    ('Almeria, ES',      36.8381,  -2.4597, 25),
    ('Granada, ES',      37.1773,  -3.5986, 680),
    ('Sevilla, ES',      37.3891,  -5.9845, 10),
    ('Tangier, MA',      35.7595,  -5.8340, 20),
    ('Tetouan, MA',      35.5785,  -5.3684, 100),
    ('Oujda, MA',        34.6805,  -1.9076, 470),
    ('Oran, DZ',         35.6971,  -0.6308, 100),
    ('Constantine, DZ',  36.3650,   6.6147, 640),
    ('Tunis, TN',        36.8065,  10.1815, 10),
    ('Sfax, TN',         34.7406,  10.7603, 10),
    ('Djerba, TN',       33.8076,  10.8451, 5),
    ('Tripoli, LY',      32.8872,  13.1913, 20),
    ('Benghazi, LY',     32.1167,  20.0667, 30),
    ('Luxor, EG',        25.6872,  32.6396, 76),
    ('Aswan, EG',        24.0889,  32.8998, 90),
    ('Sohag, EG',        26.5569,  31.6948, 70),
    ('Hurghada, EG',     27.2579,  33.8116, 10),
    ('Jeddah, SA',       21.4858,  39.1925, 12),
    ('Mecca, SA',        21.3891,  39.8579, 277),
]

print(f"{'Site':<18} {'tot?':<5} {'dur_s':>8} {'C2 UT':>10} {'C3 UT':>10} {'alt':>7} {'X':>6} {'mag':>6}")
out = {}
for name, la, lo, el in sites:
    r = circumstances(la, lo, el)
    out[name] = r
    print(f"{name:<18} {str(r['total']):<5} {r['dur_s']:8.1f} {fmt(r.get('C2')):>10} {fmt(r.get('C3')):>10} "
          f"{r['sun_alt']:7.2f} {r['airmass']:6.3f} {r['mag']:6.3f}")
