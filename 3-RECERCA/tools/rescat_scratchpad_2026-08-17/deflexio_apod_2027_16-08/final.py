import numpy as np, sys
sys.path.insert(0, '/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/604fa71e-4fd9-4d66-a0e5-157c6621ceb3/scratchpad')
from model import *

xi, eta_, V = make_field(seed=3)
MU = 12.5

print("=== A. SELF-CONSISTENCY: does the photometric model reproduce 2026? ===")
for t, lbl in ((31.0, '3 frames x 10.3 s (what train B actually used)'),):
    for Vt in (9.18, 9.5, 10.0):
        s = snr(Vt, 9.15, 89.8, t, 5.8, ETA_BAYER, 2.00)
        print(f"   V={Vt:5.2f}  S/N={s:6.2f}   ({lbl})")
print("   -> reported faintest identified V=9.18; model puts it at S/N ~5. OK.\n")

print("=== B. WHERE THE 2027 DEPTH COMES FROM (mag, vs 2026 train B) ===")
terms = [("extinction  X=6.03 k=0.33  ->  X=1.01 k=0.12", 2.00-0.12),
         ("integration 31 s -> 200 s",  2.5*np.log10(np.sqrt(200/31))),
         ("sky 9.15 -> 11.35 mag/as^2 at 8 Rsun", 2.5*np.log10(np.sqrt(10**(0.4*(11.35-9.15))))),
         ("FWHM 5.8 -> 3.5\" (smaller noise aperture)", 2.5*np.log10((5.8/3.5))),
         ("mono + r' vs Bayer luminance (eta x1.33)", 2.5*np.log10(np.sqrt(1.33))),
         ("S/N threshold 5 -> 7", -2.5*np.log10(7/5))]
tot = 0
for n, d in terms:
    tot += d; print(f"   {n:48s} {d:+6.2f}")
print(f"   {'TOTAL':48s} {tot:+6.2f}  ->  V_lim = {9.18+tot:.1f}\n")

print("=== C. CORONA SATURATION: max single-frame exposure (e-/px full well 51k) ===")
Z = 7.0e5      # photons/cm2/s for a V=0 star through r'
for F, pix, D, eff in ((494, 3.76, 90, 0.55), (494, 5.17, 90, 0.20), (300, 3.76, 75, 0.55)):
    p = 206265*pix*1e-3/F; A = np.pi*(D/20)**2
    print(f"   F={F} mm, {pix} um ({p:.2f}\"/px), D={D} mm:", end='')
    for r, mu in ((2, 6.9), (3, 8.4), (5, 10.4), (8, 11.8)):
        rate = Z*10**(-0.4*mu)*A*eff*p**2
        print(f"  {r}Rs:{51000/rate:6.2f}s", end='')
    print()
print()

print("=== D. TOTAL ERROR BUDGET for candidate configurations ===")
def budget(name, F, D, pix, sw, sh, eta, fwhm, aext, csys, order, cost,
           distres_mas, coronares_mas, extcal=False, dS=0.0, t=200.0, mu=MU):
    p = 206265*pix*1e-3/F
    w, h = np.rad2deg(sw/F), np.rad2deg(sh/F)
    sig_eff = np.hypot(fwhm/2.355, p/np.sqrt(12)); fe = 2.355*sig_eff
    m = (np.abs(xi) < w/2) & (np.abs(eta_) < h/2)
    x, y, v = xi[m], eta_[m], V[m]
    r = np.hypot(x, y)/RSUN_DEG
    sn = snr(v, mu_bg(r, mu), D, t, fe, eta, aext)
    ok = sn >= 7.0
    x, y, sn = x[ok], y[ok], sn[ok]
    sig = np.hypot(0.425*fe/sn, csys*fwhm)
    rnd, N = sigma_eps(x, y, sig, order=order, fix_scale=extcal, rmin=1.8)
    # correlated terms
    lk_dist = {1: 0.334, 3: 0.110, 5: 0.036}[order]     # residual optical distortion
    b_dist = lk_dist * distres_mas/1000.0
    b_cor  = 1.15 * coronares_mas/1000.0                # coronal-gradient bias, ~1:1
    Rd = np.hypot(w, h)/2
    b_scale = (dS*1e6) * (0.0037*Rd/1.18) if extcal else 0.0
    tot = np.sqrt(rnd**2 + b_dist**2 + b_cor**2 + b_scale**2)
    return dict(name=name, N=N, rnd=rnd, bd=b_dist, bc=b_cor, bs=b_scale,
                tot=tot, cost=cost, p=p, w=w, h=h, fwhm=fwhm)

C = []
C.append(budget('0  2026 gear, 2027 sky, no changes at all (R6III Bayer, linear fit)',
                494, 89.8, 5.17, 36, 24, ETA_BAYER, 4.13, 0.20, 0.070, 1, 0,
                distres_mas=800, coronares_mas=60))
C.append(budget('1  R6III Bayer + red long-pass, 3rd-order plate model',
                494, 89.8, 5.17, 36, 24, ETA_BAYER, 3.90, 0.14, 0.035, 3, 60,
                distres_mas=150, coronares_mas=30))
C.append(budget('2  A7RIIIA Bayer (4.51 um) + red long-pass, 3rd order',
                494, 89.8, 4.51, 35.9, 23.9, ETA_BAYER, 3.90, 0.14, 0.033, 3, 60,
                distres_mas=150, coronares_mas=30))
C.append(budget('3  ASI2600MM (APS-C mono) + r\', 3rd order',
                494, 89.8, 3.76, 23.5, 15.7, ETA_MONO_R, 3.50, 0.12, 0.020, 3, 2300,
                distres_mas=40, coronares_mas=20))
C.append(budget('4  ASI6200MM (FF mono) + r\', 3rd order            <== RECOMMENDED',
                494, 89.8, 3.76, 36, 24, ETA_MONO_R, 3.50, 0.12, 0.020, 3, 4900,
                distres_mas=40, coronares_mas=20))
C.append(budget('5  ASI6200MM (FF mono) + r\', 5th order',
                494, 89.8, 3.76, 36, 24, ETA_MONO_R, 3.50, 0.12, 0.020, 5, 4900,
                distres_mas=40, coronares_mas=20))
C.append(budget('6  ASI6200MM + r\', 3rd order + calibration fields',
                494, 89.8, 3.76, 36, 24, ETA_MONO_R, 3.50, 0.12, 0.020, 3, 4900,
                distres_mas=40, coronares_mas=20, extcal=True, dS=5e-7))
C.append(budget('7  ASI6200MM + r\' + 0.79x reducer (390 mm), 3rd order',
                390, 89.8, 3.76, 36, 24, ETA_MONO_R, 3.50, 0.12, 0.020, 3, 5700,
                distres_mas=80, coronares_mas=20))
C.append(budget('8  Sony 300/2.8 @f/4 + ASI6200MM + r\', 3rd order',
                300, 75, 3.76, 36, 24, ETA_MONO_R, 5.50, 0.12, 0.035, 3, 4900,
                distres_mas=250, coronares_mas=45))
C.append(budget('9  Sony 300/2.8 + A7RIIIA as flown, 3rd order',
                300, 107, 4.51, 35.9, 23.9, ETA_BAYER, 6.50, 0.20, 0.050, 3, 0,
                distres_mas=600, coronares_mas=60))
C.append(budget('10 BUY TeleVue NP101is 540/101 + ASI6200MM + r\', 3rd order',
                540, 101, 3.76, 36, 24, ETA_MONO_R, 3.30, 0.12, 0.020, 3, 10000,
                distres_mas=25, coronares_mas=18))

hdr = f"{'configuration':58s} {'N*':>5s} {'random':>7s} {'distort':>8s} {'corona':>7s} {'scale':>6s} {'TOTAL':>7s} {'EUR':>6s}"
print(hdr); print('-'*len(hdr))
for c in C:
    print(f"{c['name']:58s} {c['N']:5d} {c['rnd']*100:6.2f}% {c['bd']*100:7.2f}% "
          f"{c['bc']*100:6.2f}% {c['bs']*100:5.2f}% {c['tot']*100:6.2f}% {c['cost']:6d}")

print("\n=== E. TWO TRAINS versus ONE ===")
def comb(a, b, rho_sys=0.0):
    """quadrature combination; correlated systematic fraction rho_sys."""
    ra, rb = a['rnd'], b['rnd']
    sa = np.sqrt(a['bd']**2 + a['bc']**2 + a['bs']**2)
    sb = np.sqrt(b['bd']**2 + b['bc']**2 + b['bs']**2)
    r = 1/np.sqrt(1/ra**2 + 1/rb**2)
    s = 0.5*np.sqrt(sa**2 + sb**2 + 2*rho_sys*sa*sb)
    return np.sqrt(r**2 + s**2)
main = C[4]
for nm, other, rho in [('primary alone', None, 0),
                       ('+ Sony 300 mono  (independent optics)', C[8], 0.3),
                       ('+ Sony 300 + A7RIIIA as flown', C[9], 0.3),
                       ('+ a second identical VSD-class rig', C[4], 1.0)]:
    if other is None:
        print(f"   {nm:44s} {main['tot']*100:6.2f}%")
    else:
        print(f"   {nm:44s} {comb(main, other, rho)*100:6.2f}%")

print("\n=== F. SIGMA(EPS) versus the ACHIEVED PER-STAR FLOOR (the real unknown) ===")
print(f"   {'floor (arcsec)':>16s} {'as x FWHM':>10s} {'random':>8s} {'total':>8s} {'GR sigma':>9s} {'E-vs-N':>8s}")
for c_ in (0.005, 0.010, 0.020, 0.035, 0.060, 0.100, 0.200):
    b = budget('x', 494, 89.8, 3.76, 36, 24, ETA_MONO_R, 3.50, 0.12, c_/3.50, 3, 0,
               distres_mas=40, coronares_mas=20)
    print(f"   {c_:16.3f} {c_/3.50:10.3f} {b['rnd']*100:7.2f}% {b['tot']*100:7.2f}% "
          f"{1/b['tot']:8.1f} {0.5/b['tot']:7.1f}")
print("   (2026 achieved 0.64\" on train B = 0.183 x FWHM; Bruns achieved 0.065\" = 0.021 x FWHM)")
