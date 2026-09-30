"""Construeix el cataleg de cel (Tycho-2 profund + Hipparcos) projectat al pla
tangent centrat al SOL APARENT, per als dos instants de referencia."""
import numpy as np, pandas as pd, json
from skyfield.api import load, wgs84, Star
from skyfield.data import hipparcos

ts = load.timescale()
eph = load('/Users/USUARI/.cache/skyfield/de440s.bsp')
earth = eph['earth']
lloc = earth + wgs84.latlon(42.299407, -5.02503, elevation_m=798.0)

# --- llegeix Tycho-2 profund ---
lines = open('tyc2_deep.tsv').readlines()
hdr = [i for i, l in enumerate(lines) if l.startswith('_RAJ2000')][0]
cols = [c.strip() for c in lines[hdr].split('\t')]
rows = []
for l in lines[hdr+3:]:
    if l.startswith('#') or not l.strip():
        continue
    v = [x.strip() for x in l.rstrip('\n').split('\t')]
    if len(v) != len(cols):
        continue
    rows.append(dict(zip(cols, v)))
ty = pd.DataFrame(rows)
for c in ['_RAJ2000', '_DEJ2000', '_r', 'BTmag', 'VTmag', 'pmRA', 'pmDE']:
    ty[c] = pd.to_numeric(ty[c], errors='coerce')
ty = ty.dropna(subset=['VTmag', '_RAJ2000', '_DEJ2000']).copy()
# V de Tycho: V = VT - 0.090*(BT-VT)  (Hog+ 2000)
ty['V'] = np.where(ty.BTmag.notna(), ty.VTmag - 0.090*(ty.BTmag-ty.VTmag), ty.VTmag)
ty['BV'] = np.where(ty.BTmag.notna(), 0.850*(ty.BTmag-ty.VTmag), np.nan)
ty['HIP_n'] = pd.to_numeric(ty['HIP'], errors='coerce')
ty['pmRA'] = ty['pmRA'].fillna(0.0)
ty['pmDE'] = ty['pmDE'].fillna(0.0)
ty['TYC'] = ty.TYC1.astype(str)+'-'+ty.TYC2.astype(str)+'-'+ty.TYC3.astype(str)
print('Tycho-2 dins 5 graus amb VT<12,5:', len(ty), ' | V<=11:', (ty.V <= 11).sum())

# --- magnituds V d'Hipparcos per als que en tinguin (mes fiables) ---
with open('../hip_main.dat') as f:
    dfh = hipparcos.load_dataframe(f)
hipV = {}
hipBV = {}
hipHD = {}
hipSp = {}
with open('../hip_main.dat') as f:
    for line in f:
        p = line.split('|')
        try:
            h = int(p[1])
        except Exception:
            continue
        try:
            hipV[h] = float(p[5])
        except Exception:
            pass
        try:
            hipBV[h] = float(p[37])
        except Exception:
            pass
        hipHD[h] = p[71].strip()
        hipSp[h] = p[76].strip()

EPOCHS = {'sony': (2026, 8, 12, 18, 29, 48.0),   # DSC06993, EXIF=final, 8 s -> mig
          'r6':   (2026, 8, 12, 18, 29, 18.6)}   # 572A2982, EXIF=inici, 10,3 s -> mig

out = {}
for tag, e in EPOCHS.items():
    t = ts.utc(*e)
    app_sun = lloc.at(t).observe(eph['sun']).apparent()
    sra, sdec, sdist = app_sun.radec()
    a0 = np.radians(sra._degrees)
    d0 = np.radians(sdec.degrees)
    Rsun_as = np.degrees(np.arcsin(696000.0/(sdist.au*149597870.7)))*3600

    # posicions aparents de totes les estrelles
    ra = np.zeros(len(ty))
    dec = np.zeros(len(ty))
    st = Star(ra_hours=ty._RAJ2000.values/15.0, dec_degrees=ty._DEJ2000.values,
              ra_mas_per_year=ty.pmRA.values, dec_mas_per_year=ty.pmDE.values,
              epoch=ts.tt(jd=2451545.0))
    ap = lloc.at(t).observe(st).apparent()
    ara, adec, _ = ap.radec()
    ra = np.radians(ara._degrees)
    dec = np.radians(adec.degrees)

    den = np.sin(dec)*np.sin(d0) + np.cos(dec)*np.cos(d0)*np.cos(ra-a0)
    xi = np.cos(dec)*np.sin(ra-a0)/den
    eta = (np.sin(dec)*np.cos(d0) - np.cos(dec)*np.sin(d0)*np.cos(ra-a0))/den
    xi_as = np.degrees(xi)*3600.0
    eta_as = np.degrees(eta)*3600.0
    sep = np.degrees(np.arccos(np.clip(den, -1, 1)))

    d = ty.copy()
    d['xi_as'] = xi_as
    d['eta_as'] = eta_as
    d['sep_deg'] = sep
    d['Vmag'] = [hipV.get(int(h), np.nan) if np.isfinite(h) else np.nan for h in d.HIP_n]
    d['Vuse'] = np.where(np.isfinite(d.Vmag), d.Vmag, d.V)
    d['BVuse'] = [hipBV.get(int(h), np.nan) if np.isfinite(h) else np.nan for h in d.HIP_n]
    d['BVuse'] = np.where(np.isfinite(d.BVuse), d.BVuse, d.BV)
    d['HD'] = [hipHD.get(int(h), '') if np.isfinite(h) else '' for h in d.HIP_n]
    d['Sp'] = [hipSp.get(int(h), '') if np.isfinite(h) else '' for h in d.HIP_n]
    d = d.sort_values('sep_deg').reset_index(drop=True)
    d.to_csv(f'cat_{tag}.csv', index=False)
    out[tag] = dict(ra_sun=sra._degrees, dec_sun=sdec.degrees, Rsun_as=float(Rsun_as),
                    dist_au=float(sdist.au), n=len(d))
    print(f'{tag}: Sol RA={sra._degrees:.5f} Dec={sdec.degrees:.5f}  Rsun={Rsun_as:.2f}"  n={len(d)}')

json.dump(out, open('suns.json', 'w'), indent=1)
