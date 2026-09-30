import numpy as np
S=2.3548
def sigc_source(fwhm,snr): return 0.425*fwhm/snr          # source(photon)-dominated CRB
def sigc_bg(fwhm,snr):     return 0.601*fwhm/snr          # background-dominated CRB
def undersamp_penalty(fwhm_arc, pix_arc):
    """effective sigma including pixel integration: sqrt(sig^2 + p^2/12)/sig"""
    sig=fwhm_arc/S
    return np.sqrt(sig**2+pix_arc**2/12.)/sig

print("=== 1. UNDERSAMPLING PENALTY (random part only) ===")
print(" FWHM/pix   sigma_eff/sigma   ->  centroid noise penalty")
for r in (0.7,1.0,1.2,1.5,1.7,2.0,2.35,2.5,3.0,4.0,5.0):
    fw=1.0; p=fw/r
    print(f"   {r:4.2f}      {undersamp_penalty(fw,p):.4f}")

print("\n=== 2. THIS CAMPAIGN, per star ===")
cases=[("Train A Sony 300GM", 8.3, 3.2020, 3.41,1.22),("Train B R6III VSD90SS",5.8,2.1495,5.08,1.05)]
for n,fw,ps,g,rn in cases:
    print(f" {n}: FWHM {fw}\" = {fw/ps:.2f} px (luminance) / {fw/(2*ps):.2f} px per Bayer plane")
    print(f"    undersampling penalty  luminance {undersamp_penalty(fw,ps):.3f}   Bayer plane {undersamp_penalty(fw,2*ps):.3f}")

print("\n=== 3. SNR ladder for train B (measured sky 9.15 mag/arcsec^2) ===")
# calibrate on the stated brightest star: V=5.73 -> SNR 121
fwhm=5.8; sig=fwhm/S; Aeff=4*np.pi*sig**2
sky_mag=9.15
sky_in_Aeff = sky_mag-2.5*np.log10(Aeff)
print(f"   effective aperture 4*pi*sigma^2 = {Aeff:.1f} arcsec^2 ; sky inside it = V_eq {sky_in_Aeff:.2f}")
# background-limited: SNR ~ F/sqrt(Fsky) -> SNR ∝ 10^(-0.4 V) ; anchor V=5.73 -> 121
for V in (3.94,5.0,5.73,6.5,7.0,7.5,8.0,8.5,9.0,9.18,10.0,11.0):
    snr=121*10**(-0.4*(V-5.73))
    print(f"   V={V:5.2f}  SNR={snr:7.1f}   photon-limited centroid = {sigc_bg(fwhm,snr):6.3f}\"")
