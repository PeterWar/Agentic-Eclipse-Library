import sys, json, numpy as np
sys.path.insert(0, '/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/cmp')
from esfcmp import *

VIX = "/Users/USUARI/Desktop/Eclipse 2026/Vixen Unfiltered/"
SON = "/Users/USUARI/Desktop/Eclipse 2026/300mm/"

TRAINS = {
    'vixen': dict(dirp=VIX, ext='.CR3', scale=2.158, R0=976.0 / 2.158),
    'sony': dict(dirp=SON, ext='.ARW', scale=3.234, R0=976.0 / 3.234),
}


def one(train, name, chan='G', nsec=240, align=True, win_as=30.0, xlim_as=20.0):
    t = TRAINS[train]
    v, c, white = load(t['dirp'] + name + t['ext'])
    x, y, val = pick(v, c, chan)
    cx, cy, Rd = centroid(v)
    R = Rd
    for w in (60.0, 25.0):
        cx, cy, R, sd, ng = fit_circle(x, y, val, cx, cy, R, win=w)
    sat = (white - 512) * 0.93
    fits = sector_fits(x, y, val, cx, cy, R, win_as / t['scale'], nsec, sat)
    if len(fits) < 20:
        return None
    xc, ym, e, cnt = stack_esf(fits, align=align, xlim=xlim_as / t['scale'], bw=0.05)
    f = fit_esf(xc, ym, e, boxw=1.0)
    snr = float(np.median([q['snr'] for q in fits]))
    return dict(train=train, frame=name, chan=chan, nsec=nsec, align=align,
                R_px=float(R), R_as=float(R * t['scale']), nsec_ok=len(fits),
                cx=float(cx), cy=float(cy), medsnr=snr,
                fwhm_tot_as=float(f['fwhm_tot'] * t['scale']),
                fwhm_int_as=float(f['fwhm_int'] * t['scale']),
                fwhm_tot_px=float(f['fwhm_tot']), chi2=f['chi2'],
                sector_s_med_as=float(np.median([q['s'] for q in fits]) * 2.3548 * t['scale']),
                u0_rms_as=float(np.std([q['u0'] for q in fits]) * t['scale']))


if __name__ == '__main__':
    jobs = json.loads(sys.argv[1])
    out = []
    for j in jobs:
        try:
            r = one(**j)
        except Exception as ex:
            r = dict(error=str(ex), **j)
        if r:
            out.append(r)
            k = r.get('frame')
            print(f"{r.get('train'):5s} {k:10s} {r.get('chan')} nsec={r.get('nsec')} "
                  f"align={r.get('align')} sec_ok={r.get('nsec_ok')} R={r.get('R_as',0):.1f}\" "
                  f"FWHMtot={r.get('fwhm_tot_as',0):.2f}\" int={r.get('fwhm_int_as',0):.2f}\" "
                  f"snr={r.get('medsnr',0):.0f} chi2={r.get('chi2',0):.2f} "
                  f"u0rms={r.get('u0_rms_as',0):.2f}\"", flush=True)
    json.dump(out, open(sys.argv[2], 'w'), indent=1)
