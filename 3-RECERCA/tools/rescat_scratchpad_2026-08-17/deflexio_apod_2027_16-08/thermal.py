import numpy as np
print("=== PLATE SCALE vs TEMPERATURE ===")
# (a) defocus-induced magnification change: detector at F+d -> scale x (1+d/F)
for tube,alpha,name in [(0.55,23.6e-6,"aluminium tube/focuser"),(0.55,17e-6,"steel"),(0.55,1.0e-6,"carbon fibre (quasi-zero)")]:
    d=alpha*tube*1e3            # mm per K
    for F in (540.,494.,300.):
        print(f"  {name:28s} F={F:5.0f} mm : dscale = {d/F*1e6:7.2f} ppm/K")
    print()
# (b) glass: df/f = -dn/dT/(n-1) + alpha_glass
for gl,n,dndt,ag in [("N-BK7",1.5168,3.0e-6,7.1e-6),("FPL-53/S-FPL53",1.4389,-6.0e-6,13.3e-6),("N-SK16",1.6204,4.6e-6,6.3e-6)]:
    print(f"  {gl:14s} df/f = {(-dndt/(n-1)+ag)*1e6:+7.2f} ppm/K")
print("\n=== WHAT A SCALE ERROR COSTS (radial displacement) ===")
print("  eps_scale   r=1deg    r=2deg    r=3.5deg")
for eps in (1e-6,5e-6,1e-5,2.2e-5,1e-4,1e-3):
    print(f"  {eps*1e6:8.1f} ppm  "+"  ".join(f"{eps*d*3600:8.4f}\"" for d in (1,2,3.5)))
print("\n  -> aluminium tube, F=494 mm: 26.3 ppm/K = 0.095\"/K at r=1deg, 0.33\"/K at r=3.5deg")
print("  -> a 10 K difference between eclipse frame and a night-time comparison frame")
print("     moves every star radially by 0.9-3.3\": 2-6x the whole GR signal.")

print("\n=== TRAILING ===")
S=2.3548
for fwhm,scale,trail_px in [(5.8,2.1495,3.0),(8.3,3.2020,0.0),(3.0,1.2,1.0),(3.0,1.2,3.0),(3.0,1.2,6.0)]:
    sig=fwhm/S/scale                       # px
    L=trail_px
    sa=np.sqrt(sig**2+L**2/12.)            # along-trail sigma
    f_along=(sa/sig)**1.5                  # centroid error factor (bg-limited)
    f_cross=(sa/sig)**0.5
    snr_loss=np.sqrt(sa/sig)
    print(f"  FWHM {fwhm}\" @ {scale}\"/px (sigma={sig:.2f}px), trail {L:.1f}px:"
          f" along x{f_along*snr_loss:.2f}, across x{f_cross*snr_loss:.2f}, SNR x{1/snr_loss:.2f}")
print("\n=== TRACKING SPEC ===")
print("  to keep the trail below 1/3 of sigma_PSF in a T-second exposure:")
for fwhm in (2.5,3.0,5.8):
    sig=fwhm/S
    for T in (10.,30.,60.):
        print(f"   FWHM {fwhm}\", T={T:4.0f}s : drift < {sig/3/T*1000:6.1f} mas/s  ({sig/3:.2f}\" total)")
