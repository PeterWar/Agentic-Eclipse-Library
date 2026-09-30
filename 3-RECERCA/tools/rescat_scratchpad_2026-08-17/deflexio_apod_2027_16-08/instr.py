import numpy as np, sys
sys.path.insert(0, '/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/604fa71e-4fd9-4d66-a0e5-157c6621ceb3/scratchpad')
from model import *

MU_SCAT_2027 = 12.5      # atmospheric scattered background at Luxor, mag/arcsec^2
T_DEEP = 200.0           # s of eclipse-field integration out of 383 s of totality
SNR_CUT = 7.0

# FWHM budget (arcsec), no trailing, Luxor daytime seeing ~3.0" assumed
FW = {
    'vsd_mono_r' : 3.50,   # VSD90SS, mono + Sloan r'
    'vsd_bayer'  : 4.13,   # VSD90SS, Bayer luminance (chromatic focus adds in quadrature)
    'vsd_bayer_r': 3.70,   # VSD90SS, Bayer + red filter (only R plane useful)
    'sony_mono_r': 5.50,   # Sony 300 GM @f/4, mono + r'
    'sony_bayer' : 6.50,   # Sony 300 GM @f/2.8, Bayer luminance
    'petzval_r'  : 3.30,   # 100 mm class Petzval astrograph + r'
}

def config(name, D, F, pix_um, sw_mm, sh_mm, eta, fwhm, aext, csys, cost,
           offset_deg=0.0, note=''):
    p = 206265 * pix_um * 1e-3 / F                    # arcsec/px
    w = np.rad2deg(sw_mm / F); h = np.rad2deg(sh_mm / F)
    sig_psf = fwhm / 2.355
    sig_eff = np.hypot(sig_psf, p / np.sqrt(12))      # pixel-integration penalty
    fwhm_eff = 2.355 * sig_eff
    return dict(name=name, D=D, F=F, p=p, w=w, h=h, eta=eta, fwhm=fwhm,
                fwhm_eff=fwhm_eff, aext=aext, csys=csys, cost=cost,
                offset=offset_deg, note=note, samp=fwhm / p)

def evaluate(c, xi, eta_, V, order=1, fix_scale=False, seeing_scale=1.0,
             mu_scat=MU_SCAT_2027, t=T_DEEP, sys_floor_mult=1.0):
    fwhm = c['fwhm'] * seeing_scale
    sig_eff = np.hypot(fwhm / 2.355, c['p'] / np.sqrt(12))
    fwhm_eff = 2.355 * sig_eff
    # pointing offset toward PA 314.3 (M44 / Venus)
    pa = np.deg2rad(314.3)
    cx, cy = c['offset'] * np.sin(pa), c['offset'] * np.cos(pa)
    inx = (np.abs(xi - cx) < c['w'] / 2) & (np.abs(eta_ - cy) < c['h'] / 2)
    x, y, v = xi[inx], eta_[inx], V[inx]
    r = np.hypot(x, y) / RSUN_DEG
    mu = mu_bg(r, mu_scat)
    sn = snr(v, mu, c['D'], t, fwhm_eff, c['eta'], c['aext'])
    ok = sn >= SNR_CUT
    x, y, v, sn, r = x[ok], y[ok], v[ok], sn[ok], r[ok]
    sig_phot = 0.425 * fwhm_eff / sn
    sig_sys = c['csys'] * fwhm * sys_floor_mult
    sig = np.hypot(sig_phot, sig_sys)
    se, N = sigma_eps(x, y, sig, order=order, fix_scale=fix_scale, rmin=1.8)
    return se, N, (v.max() if len(v) else np.nan), sig_phot, sig_sys, r

# ------------------------------------------------------------------ configs
CFG = [
 config('1. VSD90SS + R6III  (AS FLOWN, Bayer, no filter)',
        89.8, 494, 5.17, 36, 24, ETA_BAYER, FW['vsd_bayer'], 0.20, 0.035, 0,
        note='owned'),
 config('2. VSD90SS + R6III + 610 nm long-pass (R plane)',
        89.8, 494, 5.17*2, 36, 24, ETA_BAYER*0.28, FW['vsd_bayer_r'], 0.12, 0.030, 60,
        note='+60 EUR filter; R plane only -> 10.34 um effective pixel'),
 config('3. VSD90SS + ASI2600MM Pro (APS-C mono) + r\'',
        89.8, 494, 3.76, 23.5, 15.7, ETA_MONO_R, FW['vsd_mono_r'], 0.12, 0.020, 2300,
        note='2000 EUR cam + 250 filter'),
 config('4. VSD90SS + ASI6200MM Pro (full-frame mono) + r\'',
        89.8, 494, 3.76, 36, 24, ETA_MONO_R, FW['vsd_mono_r'], 0.12, 0.020, 4900,
        note='4300 EUR cam + 350 filter (50 mm sq)'),
 config('5. VSD90SS + ASI6200MM + r\', offset 0.55 deg to M44',
        89.8, 494, 3.76, 36, 24, ETA_MONO_R, FW['vsd_mono_r'], 0.12, 0.020, 4900,
        offset_deg=0.55),
 config('6. VSD90SS + 0.79x reducer (390 mm) + ASI6200MM + r\'',
        89.8, 390, 3.76, 36, 24, ETA_MONO_R, FW['vsd_mono_r'], 0.12, 0.020, 5700,
        note='+800 EUR reducer'),
 config('7. Sony 300/2.8 + A7RIIIA (AS FLOWN)',
        107, 300, 4.51, 36, 24, ETA_BAYER, FW['sony_bayer'], 0.20, 0.045, 0,
        note='owned'),
 config('8. Sony 300/2.8 @f/4 + ASI6200MM + r\'',
        75, 300, 3.76, 36, 24, ETA_MONO_R, FW['sony_mono_r'], 0.12, 0.035, 4900),
 config('9. BUY: TeleVue NP101is 540/5.4 + ASI6200MM + r\'',
        101, 540, 3.76, 36, 24, ETA_MONO_R, FW['petzval_r'], 0.12, 0.020, 10000),
 config('10. BUY: Takahashi FSQ-106EDX4 530/5 + ASI6200MM + r\'',
        106, 530, 3.76, 36, 24, ETA_MONO_R, FW['petzval_r'], 0.12, 0.020, 11000),
]

xi, eta_, V = make_field(seed=3)
print(f"synthetic 2027 field: {len(V)} stars to V=14.5 over 30 Rsun\n")
hdr = (f"{'configuration':52s} {'as/px':>6s} {'field(deg)':>12s} {'px/FWHM':>8s} "
       f"{'N*':>5s} {'Vlim':>5s} {'s_phot':>7s} {'s_sys':>6s} {'sig(e) 1st':>10s} "
       f"{'3rd':>7s} {'5th':>7s} {'3rd+cal':>8s}")
print(hdr); print('-' * len(hdr))
res = {}
for c in CFG:
    row = []
    for order, fx in ((1, False), (3, False), (5, False), (3, True)):
        se, N, vl, sp, ss, r = evaluate(c, xi, eta_, V, order=order, fix_scale=fx)
        row.append(se)
    se1, N, vl, sp, ss, r = evaluate(c, xi, eta_, V, order=1)
    res[c['name']] = (row, N, c)
    print(f"{c['name']:52s} {c['p']:6.2f} {c['w']:5.2f}x{c['h']:5.2f} {c['samp']:8.2f} "
          f"{N:5d} {vl:5.2f} {np.median(sp):7.3f} {ss:6.3f} "
          f"{row[0]:10.3f} {row[1]:7.3f} {row[2]:7.3f} {row[3]:8.3f}")
