import numpy as np, sys
sys.path.insert(0, '/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/604fa71e-4fd9-4d66-a0e5-157c6621ceb3/scratchpad')
from model import *
from final2 import budget, VSD, MU, YIELD, MARGIN

BASE = dict(**VSD, pix=3.76, eta=ETA_MONO_R, fwhm=3.5, aext=0.12, csys=0.020,
            order=3, distres_mas=40, coronares_mas=8, extcal=True, dS=5e-7)

print("=== 1. HOW MUCH IS M44 ACTUALLY WORTH? ===")
import model as M
xi0, eta0, V0 = make_field(seed=3)
# rebuild the field without the cluster
_saveM = M._NM.copy()
M._NM = np.array([1e-6, 1e-6, 1e-6, 1e-6])
xi1, eta1, V1 = make_field(seed=3)
M._NM = _saveM
for lbl, arr in (('with M44 (as it really is)', (xi0, eta0, V0)),
                 ('M44 deleted from the sky', (xi1, eta1, V1))):
    M_xi, M_eta, M_V = arr
    import final2
    old = (final2.xi, final2.eta_, final2.V)
    final2.xi, final2.eta_, final2.V = M_xi, M_eta, M_V
    b = budget(**BASE)
    final2.xi, final2.eta_, final2.V = old
    print(f"   {lbl:34s} N={b['N']:4d}  sigma(eps)={b['tot']*100:5.2f}%")

print("\n=== 2. WHERE THE SIGNAL REALLY LIVES: inner-radius dependence ===")
print("   (this is the single biggest lever in the whole experiment)")
for rmin in (1.6, 1.8, 2.0, 2.2, 2.5, 3.0, 3.5, 4.0):
    import final2
    p = 206265*3.76e-3/494; w, h = np.rad2deg(36/494), np.rad2deg(24/494)
    fe = 2.355*np.hypot(3.5/2.355, p/np.sqrt(12))
    m = (np.abs(final2.xi) < w/2) & (np.abs(final2.eta_) < h/2)
    x, y, v = final2.xi[m], final2.eta_[m], final2.V[m]
    r = np.hypot(x, y)/RSUN_DEG
    sn = snr(v, mu_bg(r, MU), 89.8, 200.0, fe, ETA_MONO_R, 0.12)
    ok = sn >= 7
    sig = np.hypot(0.425*fe/sn[ok], 0.020*3.5)
    se, N = sigma_eps(x[ok], y[ok], sig, order=3, fix_scale=True, rmin=rmin)
    se = se*MARGIN/np.sqrt(YIELD)
    tot = np.sqrt(se**2 + (0.110*0.040)**2 + (1.15*0.008)**2 + 0.0039**2)
    print(f"   innermost usable star at {rmin:4.1f} Rsun -> sigma(eps) = {tot*100:5.2f}%"
          f"   ({'x%.2f worse than 1.8' % (tot/0.0221) if rmin>1.8 else 'reference'})")

print("\n=== 3. FILTER CHOICE (VSD90SS + FF mono, Luxor, 200 s) ===")
print("   dispersion at Luxor: unfiltered 0.192\", r' 0.051\", 10 nm NB 0.002\" (research 3)")
print(f"   {'filter':28s} {'eta':>6s} {'FWHM':>6s} {'N*':>5s} {'random':>7s} {'TOTAL':>7s}")
for nm, eta, fw in (("none (mono, 400-700 nm)", ETA_MONO_L, 3.95),
                    ("Sloan r' (562-695)", ETA_MONO_R, 3.50),
                    ("deep red 610 long-pass", ETA_MONO_R*1.15, 3.45),
                    ("30 nm narrowband ~656", ETA_MONO_NB, 3.35),
                    ("10 nm narrowband", ETA_MONO_NB*0.33, 3.32)):
    a = dict(BASE); a.update(eta=eta, fwhm=fw)
    b = budget(**a)
    print(f"   {nm:28s} {eta:6.2f} {fw:6.2f} {b['N']:5d} {b['rnd']*100:6.2f}% {b['tot']*100:6.2f}%")

print("\n=== 4. MONO vs BAYER, decomposed (same telescope, same 200 s) ===")
ref = budget(**dict(BASE, pix=5.17, eta=ETA_BAYER, fwhm=4.13, aext=0.20, csys=0.035))
print(f"   R6 III Bayer, red filter, everything else equal : sigma(eps) = {ref['tot']*100:5.2f}%")
steps = [("+ remove chromatic focus  FWHM 4.13 -> 3.50", dict(fwhm=3.50)),
         ("+ single well-sampled PSF  csys 0.035 -> 0.020", dict(fwhm=3.50, csys=0.020)),
         ("+ no CFA losses  eta 1.00 -> 1.33", dict(fwhm=3.50, csys=0.020, eta=ETA_MONO_R)),
         ("+ 3.76 um pixels instead of 5.17", dict(fwhm=3.50, csys=0.020, eta=ETA_MONO_R, pix=3.76))]
prev = ref['tot']
for lbl, kw in steps:
    a = dict(BASE); a.update(pix=5.17, eta=ETA_BAYER, fwhm=4.13, aext=0.12, csys=0.035)
    a.update(kw)
    b = budget(**a)
    print(f"   {lbl:48s} {b['tot']*100:5.2f}%   (x{prev/b['tot']:.2f})")
    prev = b['tot']

print("\n=== 5. EXPOSURE LADDER forced by coronal saturation (494 mm, 3.76 um, 51 ke- well) ===")
Z = 7.0e5; A = np.pi*(89.8/20)**2; eff = 0.55; p = 206265*3.76e-3/494
print(f"   {'zone':>16s} {'corona mu':>10s} {'t_max':>8s} {'frames in 200 s':>17s}")
for r, mu, lbl in ((2, 6.9, '1.8-2.5 Rsun'), (3, 8.4, '2.5-4 Rsun'),
                   (5, 10.4, '4-6 Rsun'), (8, 11.8, '6-10 Rsun'), (12, 13.0, '>10 Rsun')):
    tmax = 51000/(Z*10**(-0.4*mu)*A*eff*p**2)
    print(f"   {lbl:>16s} {mu:9.1f}  {tmax:7.2f}s {int(200/max(tmax,0.4)):17d}")
print("   -> a 3-tier ladder (0.4 s / 3 s / 20 s) covers the whole field; ASI6200 reads")
print("      full frame at ~3.5 fps 16-bit, so 200 s of 0.4 s frames is data-rate bound,")
print("      not SNR bound.  Total integration, not frame length, sets the precision.")

print("\n=== 6. delta Cnc and Venus ===")
for nm, Vm in (('delta Cnc  V=3.94 at 3.10 Rsun', 3.94), ('Venus  V=-3.91 at 10.81 Rsun', -3.91)):
    Fst = Z*10**(-0.4*Vm)*A*eff
    sig_as = 3.5/2.355
    peak_per_s = Fst*p**2/(2*np.pi*sig_as**2)
    print(f"   {nm:34s} saturates the well in {51000/peak_per_s*1000:8.2f} ms")
