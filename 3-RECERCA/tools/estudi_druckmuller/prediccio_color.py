"""Prediccio del color de la corona en sRGB lineal, feta be.

espectre solar x transmissio atmosferica -> integral contra les corbes CIE
1931 -> XYZ -> sRGB lineal amb blanc D65 (que es el que declara el balanc de
dia de la camera). Aixi la prediccio es COLORIMETRICA i es pot comparar amb el
que mesurem, cosa que amb els multiplicadors sols no es podia.
"""
import numpy as np

XYZ_SRGB = np.array([[3.24096994,-1.53738318,-0.49861076],
                     [-0.96924364,1.87596750,0.04155506],
                     [0.05563008,-0.20397696,1.05697151]])
LAM = np.arange(380.0, 781.0, 1.0)


def g(x, mu, s1, s2):
    s = np.where(x < mu, s1, s2)
    return np.exp(-0.5*((x-mu)/s)**2)


# Wyman, Sloan & Shirley (2013), ajust multi-lobul de les CIE 1931
XB = 1.056*g(LAM,599.8,37.9,31.0) + 0.362*g(LAM,442.0,16.0,26.7) - 0.065*g(LAM,501.1,20.4,26.2)
YB = 0.821*g(LAM,568.8,46.9,40.5) + 0.286*g(LAM,530.9,16.3,31.1)
ZB = 1.217*g(LAM,437.0,11.8,36.0) + 0.681*g(LAM,459.0,26.0,13.8)


def planck(lam_nm, T):
    l = lam_nm*1e-9
    return 1.0/(l**5*(np.exp(1.4387768775e-2/(l*T))-1.0))


def a_srgb_lineal(S):
    X = np.trapezoid(S*XB, LAM); Y = np.trapezoid(S*YB, LAM); Z = np.trapezoid(S*ZB, LAM)
    return XYZ_SRGB @ np.array([X, Y, Z])


# blanc de referencia D65: el balanc de dia hi esta ancorat
D65 = planck(LAM, 6504.0)                      # aproximacio de D65 per Planck
wD65 = a_srgb_lineal(D65)

P = 921.0/1013.25                               # 798 m
AOD, ALPHA, O3DU = 0.237, 1.3, 300.0


def tau(lam_nm):
    l = lam_nm/1000.0
    ray = 0.00879*l**-4.09*P
    aer = AOD*(l/0.550)**-ALPHA
    # Chappuis, forma aproximada centrada a 602 nm
    o3 = (O3DU/1000.0)*0.06*np.exp(-0.5*((lam_nm-602.0)/70.0)**2)
    return ray + aer + o3


SOL = planck(LAM, 5772.0)                       # espectre solar (visible)
print(f"{'X':>6} | {'R/G':>7} {'B/G':>7}   (sRGB lineal, blanc D65)")
for X in [0.0, 1.0, 2.0, 4.0, 6.12, 7.0]:
    v = a_srgb_lineal(SOL*np.exp(-tau(LAM)*X)) / wD65
    print(f"{X:6.2f} | {v[0]/v[1]:7.3f} {v[2]/v[1]:7.3f}" +
          ("   <- la nostra totalitat" if abs(X-6.12) < 0.01 else
           ("   <- sense atmosfera: nomes Sol contra D65" if X == 0 else "")))

v = a_srgb_lineal(SOL*np.exp(-tau(LAM)*6.12)) / wD65
print(f"\n  PREDIT a X = 6,12 :  R/G {v[0]/v[1]:.3f}   B/G {v[2]/v[1]:.3f}")
print(f"  MESURAT (compost Vixen amb matriu, cel restat) :  R/G 1.928   B/G 0.194")
print(f"  MESURAT (Canon 572A2996 a 1,70 R_sol, ~5 % cel):  R/G 1.796   B/G 0.243")
print(f"  MESURAT (Sony DSC06991 a 1,91 R_sol)           :  R/G ~1.95   B/G ~0.40")
print(f"\n  desacord contra el compost: R/G {(v[0]/v[1]/1.928-1)*100:+.1f} %   "
      f"B/G {(v[2]/v[1]/0.194-1)*100:+.1f} %")

print("\n--- sensibilitat ---")
for aod in (0.18, 0.237, 0.30):
    AOD = aod
    v = a_srgb_lineal(SOL*np.exp(-tau(LAM)*6.12))/wD65
    print(f"  AOD(550) {aod:.3f} -> R/G {v[0]/v[1]:.3f}  B/G {v[2]/v[1]:.3f}  "
          f"(k_V {1.0857*tau(550.0):.3f} mag/X)")
AOD = 0.237
for al in (1.0, 1.3, 1.6):
    ALPHA = al
    v = a_srgb_lineal(SOL*np.exp(-tau(LAM)*6.12))/wD65
    print(f"  alpha {al:.1f}      -> R/G {v[0]/v[1]:.3f}  B/G {v[2]/v[1]:.3f}")
