import numpy as np, sys
sys.path.insert(0, '/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/604fa71e-4fd9-4d66-a0e5-157c6621ceb3/scratchpad')
from model import *

MU_SCAT = 12.5; T = 200.0; CUT = 7.0
xi, eta_, V = make_field(seed=3)

def run(F, D, pix, sw, sh, fwhm_atm_opt, eta=ETA_MONO_R, aext=0.12, csys=0.020,
        order=3, mu=MU_SCAT, t=T, cut=CUT, rmin=1.8):
    p = 206265 * pix * 1e-3 / F
    w, h = np.rad2deg(sw / F), np.rad2deg(sh / F)
    fwhm = fwhm_atm_opt
    sig_eff = np.hypot(fwhm / 2.355, p / np.sqrt(12)); fwhm_eff = 2.355 * sig_eff
    m = (np.abs(xi) < w/2) & (np.abs(eta_) < h/2)
    x, y, v = xi[m], eta_[m], V[m]
    r = np.hypot(x, y) / RSUN_DEG
    sn = snr(v, mu_bg(r, mu), D, t, fwhm_eff, eta, aext)
    ok = sn >= cut
    x, y, sn, v = x[ok], y[ok], sn[ok], v[ok]
    sig = np.hypot(0.425 * fwhm_eff / sn, csys * fwhm)
    se, N = sigma_eps(x, y, sig, order=order, rmin=rmin)
    return se, N, p, w, h, (v.max() if len(v) else np.nan), fwhm/p

print("SCAN 1 - FOCAL LENGTH at FIXED 90 mm APERTURE")
print("  full-frame mono 36x24 mm, 3.76 um, Sloan r', FWHM(atm+optics)=3.5\", 200 s")
print(f"{'F(mm)':>7s} {'as/px':>6s} {'px/FWHM':>8s} {'field(deg)':>13s} {'r_corner':>9s} "
      f"{'N*':>6s} {'Vlim':>5s} {'1st':>7s} {'3rd':>7s} {'5th':>7s}")
for F in (200, 250, 300, 390, 450, 494, 550, 650, 800, 1000, 1300):
    out1 = run(F, 90, 3.76, 36, 24, 3.5, order=1)
    out3 = run(F, 90, 3.76, 36, 24, 3.5, order=3)
    out5 = run(F, 90, 3.76, 36, 24, 3.5, order=5)
    se1, N, p, w, h, vl, samp = out1
    rc = np.hypot(w, h)/2/RSUN_DEG
    print(f"{F:7d} {p:6.2f} {samp:8.2f} {w:6.2f}x{h:5.2f} {rc:8.1f}R {N:6d} {vl:5.1f} "
          f"{se1*100:6.2f}% {out3[0]*100:6.2f}% {out5[0]*100:6.2f}%")

print("\nSCAN 2 - FOCAL LENGTH at FIXED f/5.5 (aperture grows with F: a real telescope)")
print(f"{'F(mm)':>7s} {'D(mm)':>6s} {'as/px':>6s} {'field(deg)':>13s} {'N*':>6s} {'Vlim':>5s} "
      f"{'1st':>7s} {'3rd':>7s} {'5th':>7s}")
for F in (250, 300, 390, 450, 494, 550, 650, 800, 1000, 1300):
    D = F / 5.5
    fw = np.hypot(3.30, 1.22 * 620e-9 / (D/1000) * 206265 * 0.9)   # + diffraction
    o = [run(F, D, 3.76, 36, 24, fw, order=k) for k in (1, 3, 5)]
    se1, N, p, w, h, vl, samp = o[0]
    print(f"{F:7d} {D:6.1f} {p:6.2f} {w:6.2f}x{h:5.2f} {N:6d} {vl:5.1f} "
          f"{se1*100:6.2f}% {o[1][0]*100:6.2f}% {o[2][0]*100:6.2f}%")

print("\nSCAN 3 - APERTURE at fixed F=494 mm, full-frame mono + r'")
print(f"{'D(mm)':>6s} {'f/':>5s} {'FWHM':>6s} {'N*':>6s} {'Vlim':>5s} {'3rd':>7s} {'5th':>7s}")
for D in (60, 75, 90, 106, 130, 150, 200):
    fw = np.hypot(3.30, 1.22 * 620e-9 / (D/1000) * 206265 * 0.9)
    o3 = run(494, D, 3.76, 36, 24, fw, order=3)
    o5 = run(494, D, 3.76, 36, 24, fw, order=5)
    print(f"{D:6.0f} {494/D:5.1f} {fw:6.2f} {o3[1]:6d} {o3[5]:5.1f} {o3[0]*100:6.2f}% {o5[0]*100:6.2f}%")

print("\nSCAN 4 - PIXEL SIZE at F=494 mm, D=90 mm, 36x24 mm sensor")
print(f"{'pix(um)':>8s} {'Mpx':>6s} {'as/px':>6s} {'px/FWHM':>8s} {'N*':>6s} {'3rd':>7s}")
for pix in (2.4, 3.0, 3.76, 4.63, 5.17, 6.5, 9.0):
    o = run(494, 90, pix, 36, 24, 3.5, order=3)
    print(f"{pix:8.2f} {36*24/(pix*1e-3)**2/1e6:6.1f} {o[2]:6.2f} {o[6]:8.2f} {o[1]:6d} {o[0]*100:6.2f}%")

print("\nSCAN 5 - SENSITIVITY of the recommended rig (VSD90SS 494/90, FF mono r', 3rd order)")
base = run(494, 90, 3.76, 36, 24, 3.5, order=3)
print(f"  baseline: N={base[1]}, Vlim={base[5]:.1f}, sigma(eps)={base[0]*100:.2f}%")
for lbl, kw in [("seeing 2.5\" (FWHM 3.0)", dict(fwhm_atm_opt=3.0)),
                ("seeing 4.0\" (FWHM 4.4)", dict(fwhm_atm_opt=4.4)),
                ("seeing 5.0\" (FWHM 5.3)", dict(fwhm_atm_opt=5.3)),
                ("sky 11.5 (1 mag brighter)", dict(mu=11.5)),
                ("sky 13.5 (1 mag darker)", dict(mu=13.5)),
                ("only 100 s of totality used", dict(t=100.0)),
                ("only 50 s used", dict(t=50.0)),
                ("sys floor 0.010*FWHM", dict(csys=0.010)),
                ("sys floor 0.040*FWHM", dict(csys=0.040)),
                ("S/N cut 15 (conservative)", dict(cut=15.0)),
                ("no star inside 3 Rsun", dict(rmin=3.0)),
                ("no star inside 2.5 Rsun", dict(rmin=2.5))]:
    a = dict(F=494, D=90, pix=3.76, sw=36, sh=24, fwhm_atm_opt=3.5, order=3)
    a.update(kw)
    o = run(**a)
    print(f"  {lbl:32s} N={o[1]:5d}  Vlim={o[5]:5.1f}  sigma(eps)={o[0]*100:6.2f}%")
