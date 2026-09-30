"""El groc de Pere: es l'atmosfera o es la camera?

Argument de partida: el balanc de LLUM DE DIA de la camera esta DEFINIT perque
una font de dia (espectre solar travessant poca atmosfera) surti NEUTRA. La
corona K es un mirall de la fotosfera: mateix espectre. Per tant, despres del
balanc de dia, tot el que s'aparti de R/G = B/G = 1 ha de ser ATMOSFERA.
(La matriu de color que ens falta no afecta aquesta prova: una entrada neutra
surt neutra de qualsevol perfil ben format; la matriu canvia la saturacio dels
colors, no el punt blanc.)

Aixi que es calcula l'extincio al lloc de Pere i es compara amb el mesurat.
"""
import numpy as np
from skyfield.api import load, wgs84

LAT, LON, ALT = 42.299407, -5.02503, 798.0        # MIRADOR FINAL 2
ts = load.timescale(); eph = load("de421.bsp")
obs = eph["earth"] + wgs84.latlon(LAT, LON, elevation_m=ALT)
t = ts.utc(2026, 8, 12, 18, 29, 40)                # mig de la totalitat
alt = obs.at(t).observe(eph["sun"]).apparent().altaz()[0].degrees


def kasten_young(h):
    return 1.0 / (np.sin(np.radians(h)) + 0.50572 * (h + 6.07995) ** -1.6364)


X = kasten_young(alt)
P = 1013.25 * (1 - 2.25577e-5 * ALT) ** 5.25588
print(f"Sol a {alt:.2f} deg  ->  massa d'aire (Kasten-Young) X = {X:.2f}")
print(f"altitud {ALT:.0f} m -> pressio {P:.0f} hPa (factor Rayleigh {P/1013.25:.3f})\n")

# longituds d'ona efectives dels tres canals d'una Bayer Canon
LAM = {"R": 0.630, "G": 0.535, "B": 0.465}         # um
ALPHA = 1.3                                         # Angstrom, aerosol
K_V_MESURAT = 0.40                                  # mag/X, mesura nostra del 30-07


def taus(aod550):
    o3 = {"R": 0.025, "G": 0.020, "B": 0.005}       # Chappuis, ~300 DU
    out = {}
    for c, l in LAM.items():
        ray = 0.00879 * l ** -4.09 * (P / 1013.25)
        aer = aod550 * (l / 0.550) ** -ALPHA
        out[c] = dict(ray=ray, aer=aer, o3=o3[c], tot=ray + aer + o3[c])
    return out


# calibra l'aerosol perque el k total en V (canal G) doni el 0,40 mag/X mesurat
lo, hi = 0.0, 1.5
for _ in range(60):
    mid = 0.5 * (lo + hi)
    if 1.0857 * taus(mid)["G"]["tot"] < K_V_MESURAT:
        lo = mid
    else:
        hi = mid
AOD = 0.5 * (lo + hi)
T = taus(AOD)
print(f"aerosol calibrat perque k(G) = {K_V_MESURAT:.2f} mag/X  ->  AOD(550) = {AOD:.3f}\n")
print(f"{'canal':>6} {'lambda':>8} {'Rayleigh':>9} {'aerosol':>8} {'ozo':>6} {'tau':>7} {'k (mag/X)':>10}")
for c in "RGB":
    d = T[c]
    print(f"{c:>6} {LAM[c]*1000:6.0f}nm {d['ray']:9.4f} {d['aer']:8.4f} {d['o3']:6.3f} "
          f"{d['tot']:7.4f} {1.0857*d['tot']:10.3f}")

rg = np.exp(-(T["R"]["tot"] - T["G"]["tot"]) * X)
bg = np.exp(-(T["B"]["tot"] - T["G"]["tot"]) * X)
print(f"\n  EXTINCIO PREDITA a X = {X:.2f}:   R/G = {rg:.3f}   B/G = {bg:.3f}")
print(f"  MESURAT (s_corona)      :        R/G = 1.755   B/G = 0.498")
print(f"  MESURAT (GraduantColor de Pere, 2,65-3,0 R_sol): R/G 1,72-1,77   B/G 0,39-0,48")
print(f"\n  desacord: R/G {(rg/1.755-1)*100:+.1f} %   B/G {(bg/0.498-1)*100:+.1f} %")

print("\n--- sensibilitat: quant depen de les suposicions? ---")
for lr in (0.610, 0.620, 0.630, 0.640, 0.650):
    LAM["R"] = lr; T2 = taus(AOD)
    print(f"  lambda_R = {lr*1000:.0f} nm -> R/G = {np.exp(-(T2['R']['tot']-T2['G']['tot'])*X):.3f}")
LAM["R"] = 0.630
for a in (1.0, 1.3, 1.6):
    ALPHA = a
    lo, hi = 0.0, 1.5
    for _ in range(60):
        mid = 0.5*(lo+hi)
        if 1.0857*taus(mid)["G"]["tot"] < K_V_MESURAT: lo = mid
        else: hi = mid
    T2 = taus(0.5*(lo+hi))
    print(f"  alpha = {a:.1f} -> R/G = {np.exp(-(T2['R']['tot']-T2['G']['tot'])*X):.3f}   "
          f"B/G = {np.exp(-(T2['B']['tot']-T2['G']['tot'])*X):.3f}")
