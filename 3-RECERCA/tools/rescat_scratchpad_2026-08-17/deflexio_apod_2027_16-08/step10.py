import numpy as np
# per-star random budget, quadrature, for the "careful amateur" 2027 plan
terms = {
 'photon / centroid (corona-limited inner stars dominate)': {'A':0.030,'B':0.020},
 'seeing residual, Zacharias, 240 s, seeing 3"'           : {'A':0.020,'B':0.017},
 'undersampling / pixel-phase (Bayer + drizzle + ePSF)'    : {'A':0.120,'B':0.090},
 'PSF-model + flat-field + demosaic residual'              : {'A':0.060,'B':0.045},
 'optical distortion, RANDOM (uncorrelated) part'          : {'A':0.050,'B':0.030},
 'differential refraction residual (Luxor, after linear)'  : {'A':0.010,'B':0.003},
 'atmospheric dispersion residual (r\' + Gaia BP-RP)'      : {'A':0.020,'B':0.015},
 'catalogue position + proper motion (Gaia DR3 @2027.6)'   : {'A':0.0004,'B':0.0004},
 'plate-model inadequacy, random part'                     : {'A':0.030,'B':0.025},
 'thermal / focus drift (scale fitted in-frame)'           : {'A':0.000,'B':0.000},
 'trailing (sidereal, 5\' polar error, 10 s frames)'       : {'A':0.020,'B':0.015},
 'coronal gradient (local background PLANE fitted)'        : {'A':0.010,'B':0.007},
}
print(f"{'term':58s}{'train A':>10}{'train B':>10}")
tA=0.;tB=0.
for k,v in terms.items():
    print(f"{k:58s}{v['A']:10.3f}{v['B']:10.3f}")
    tA+=v['A']**2; tB+=v['B']**2
tA,tB=np.sqrt(tA),np.sqrt(tB)
print(f"{'QUADRATURE TOTAL (per-star, per coordinate)':58s}{tA:10.3f}{tB:10.3f}")

kA,kB = 0.26346, 0.43975      # sigma(eps) per arcsec, 3rd-order plate model
sA,sB = kA*tA, kB*tB
comb=1/np.sqrt(1/sA**2+1/sB**2)
print(f"\n  -> sigma(eps): train A {sA:.4f}, train B {sB:.4f}, combined RANDOM {comb:.4f} ({100*comb:.1f}%)")
# coherent budget
bias = {'cubic distortion residual (killed by the 3rd-order model)':0.000,
        'r^5 distortion residual, 60 mas at the field edge x 0.18':0.011,
        'plate scale (fitted in-frame -> exactly zero)':0.000,
        'differential refraction (Luxor)':0.001,
        'coronal gradient after plane fit':0.001,
        'flat-field / large-scale detector systematics':0.008}
b=np.sqrt(sum(v**2 for v in bias.values()))
print(f"  -> coherent BIAS budget: {b:.4f}")
for k,v in bias.items(): print(f"       {k:58s}{v:.4f}")
print(f"\n  TOTAL sigma(eps) = sqrt({comb:.4f}^2 + {b:.4f}^2) = {np.sqrt(comb**2+b**2):.4f}"
      f"  =  {100*np.sqrt(comb**2+b**2):.1f}% of L")
tot=np.sqrt(comb**2+b**2)
print(f"  Einstein vs Newton separation: {0.5/tot:.1f} sigma ;  GR detection: {1/tot:.1f} sigma")

print("\n  --- what if the distortion solution is only good to 300 mas (r^5 residual)? ---")
b2=np.sqrt(b**2-0.011**2+(0.18*0.300)**2)
print(f"  bias {b2:.4f} -> total {np.sqrt(comb**2+b2**2):.3f} = {100*np.sqrt(comb**2+b2**2):.0f}%")
print("  --- and if a LINEAR plate model is used with 1 arcsec of cubic distortion? ---")
kA1,kB1=0.18767,0.26503
c1=1/np.sqrt(1/(kA1*tA)**2+1/(kB1*tB)**2)
print(f"  random {c1:.4f} but bias 0.44 -> total ~0.44 : the answer would be wrong by 44%")
