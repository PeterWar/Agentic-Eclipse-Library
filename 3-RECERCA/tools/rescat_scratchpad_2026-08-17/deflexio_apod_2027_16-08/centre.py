import numpy as np
exec(open("/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/604fa71e-4fd9-4d66-a0e5-157c6621ceb3/scratchpad/ecl2027.py").read().split("sites = [")[0])

def centreline_at_lon(lon, lat_lo, lat_hi, elev=0.0):
    # coarse then golden-ish refine on duration
    lats = np.linspace(lat_lo, lat_hi, 41)
    durs = [circumstances(la, lon, elev)['dur_s'] for la in lats]
    i = int(np.argmax(durs))
    lo = lats[max(0, i-1)]; hi = lats[min(len(lats)-1, i+1)]
    for _ in range(4):
        lats2 = np.linspace(lo, hi, 11)
        durs2 = [circumstances(la, lon, elev)['dur_s'] for la in lats2]
        j = int(np.argmax(durs2))
        lo = lats2[max(0, j-1)]; hi = lats2[min(len(lats2)-1, j+1)]
    best_lat = 0.5*(lo+hi)
    return best_lat, circumstances(best_lat, lon, elev)

def edges_at_lon(lon, lat_lo, lat_hi, elev=0.0):
    lats = np.linspace(lat_lo, lat_hi, 121)
    tot = np.array([circumstances(la, lon, elev)['total'] for la in lats])
    if not tot.any(): return None, None
    idx = np.where(tot)[0]
    return lats[idx[0]], lats[idx[-1]]

targets = [
    ('S Spain (Cadiz/Tarifa lon)',  -5.90, 35.0, 38.0),
    ('Gibraltar Strait lon',        -5.35, 34.8, 38.0),
    ('Malaga lon',                  -4.42, 34.8, 38.0),
    ('N Morocco (Tangier lon)',     -5.83, 34.5, 37.5),
    ('Morocco/Algeria border lon',  -1.91, 33.5, 37.0),
    ('Oran lon',                    -0.63, 33.5, 37.0),
    ('E Algeria lon',                6.61, 31.0, 36.0),
    ('Tunisia (Sfax lon)',          10.76, 31.0, 36.5),
    ('Libya (Tripoli lon)',         13.19, 30.0, 35.0),
    ('Libya (Benghazi lon)',        20.07, 28.0, 34.0),
    ('Egypt (Luxor lon)',           32.64, 23.0, 29.0),
    ('Egypt (Nile, 31.7E)',         31.69, 23.0, 29.0),
    ('Saudi (Jeddah lon)',          39.19, 19.0, 25.0),
]
print(f"{'segment':<28} {'lon':>7} {'centre lat':>10} {'dur':>8} {'alt':>7} {'X':>6} {'width_km':>9}")
for name, lon, la0, la1 in targets:
    blat, r = centreline_at_lon(lon, la0, la1)
    n_edge, s_edge = None, None
    e1, e2 = edges_at_lon(lon, la0, la1)
    width = (e2-e1)*111.32 if e1 is not None else float('nan')
    print(f"{name:<28} {lon:7.2f} {blat:10.4f} {r['dur_s']:8.1f} {r['sun_alt']:7.2f} {r['airmass']:6.3f} {width:9.1f}")
