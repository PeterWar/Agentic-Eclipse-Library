#!/usr/bin/env python3
"""Requisits v3: amb el terra sistemàtic correlacionat, que és el que mana.

L'error de posició d'una estrella té dues meitats que es comporten de manera
oposada:

  · la part INDEPENDENT (fotons, seeing d'aquell instant) baixa com 1/√N;
  · la part CORRELACIONADA (distorsió òptica residual, model de refracció,
    error d'escala tèrmica, inadequació del model de placa) NO baixa amb N,
    perquè desplaça totes les estrelles d'una regió en el mateix sentit.

És exactament la raó per la qual els equips professionals van quedar encallats
al 10 % durant cinquanta anys tot i tenir plaques amb centenars d'estrelles.
"""
import math
import numpy as np

R_SOL = 946.66
ALPHA = 1.7516
rng = np.random.default_rng(20270802)

DENS_2026, VLIM_2026, PENDENT = 2.07, 9.7, 0.42


def densitat(vlim):
    return DENS_2026 * 10 ** (PENDENT * (vlim - VLIM_2026))


def sigma_stat(r, th, sig, npar=4):
    n = len(r)
    A = np.zeros((2 * n, npar + 1)); w = np.zeros(2 * n)
    for i in range(n):
        x, y = r[i] * math.cos(th[i]), r[i] * math.sin(th[i])
        A[2*i, 0] = 1.0; A[2*i+1, 1] = 1.0
        A[2*i, 2] = -y;  A[2*i+1, 2] = x
        A[2*i, 3] = x;   A[2*i+1, 3] = y
        a = ALPHA / r[i]
        A[2*i, npar] = a * math.cos(th[i]); A[2*i+1, npar] = a * math.sin(th[i])
        w[2*i] = w[2*i+1] = 1.0 / sig[i] ** 2
    return math.sqrt(np.linalg.inv(A.T @ (A * w[:, None]))[npar, npar])


def escenari(vlim, rmin, rmax, sig_sys, fwhm, s_corr, camp_deg2=None,
             snr_lim=5.0, nrep=9):
    """σ(ε) total = quadratura de l'estadístic i del terra correlacionat."""
    dens = densitat(vlim) * (R_SOL / 3600.0) ** 2
    area = math.pi * (rmax ** 2 - rmin ** 2)
    if camp_deg2 is not None:                      # camp rectangular real
        area = min(area, camp_deg2 / (R_SOL / 3600.0) ** 2)
    out, ns = [], []
    for _ in range(nrep):
        n = rng.poisson(dens * area)
        if n < 6:
            continue
        r = np.sqrt(rng.uniform(rmin ** 2, rmax ** 2, n))
        th = rng.uniform(0, 2 * math.pi, n)
        u = rng.uniform(0, 1, n)
        m = np.clip(vlim + np.log10(u) / PENDENT, 5.0, vlim)
        snr = snr_lim * 10 ** (0.4 * (vlim - m))
        sig = np.sqrt(sig_sys ** 2 + (fwhm / (2.355 * snr)) ** 2)
        out.append(sigma_stat(r, th, sig))
        ns.append(n)
    st = float(np.median(out))
    return math.hypot(st, s_corr), st, int(np.median(ns))


print("=" * 78)
print("1. PER QUÈ MÉS ESTRELLES DEIXEN DE SERVIR: LA SATURACIÓ")
print("=" * 78)
print("""
  Camp del 2027 amb el Sol alt, σ per estrella 0,20″, r de 1,8 a 11 R☉.
  Es va afegint fondària (i per tant estrelles) i es mira què passa amb i
  sense un terra sistemàtic correlacionat de 3 % (nivell Bruns 2017).
""")
print(f"  {'V límit':>8} {'N':>6} {'σ(ε) estadístic':>17} {'+ terra 3 %':>13} {'+ terra 10 %':>14}")
print("  " + "-" * 62)
for vlim in (9.7, 10.7, 11.7, 12.7, 13.7, 14.7):
    tot3, st, n = escenari(vlim, 1.8, 11.0, 0.20, 2.5, 0.03, camp_deg2=12.0)
    tot10 = math.hypot(st, 0.10)
    print(f"  {vlim:8.1f} {n:6d} {st:16.4f} {tot3:13.4f} {tot10:14.4f}")
print("""
  → Passat un cert punt, afegir estrelles no mou el resultat gens: el que
    queda és el terra. La feina NO és tenir més estrelles, és baixar el terra.""")

print("\n" + "=" * 78)
print("2. QUÈ DECIDEIX DE VERITAT: EL TERRA SISTEMÀTIC")
print("=" * 78)
print("""
  Amb un camp del 2027 raonable (V<12,5, r 1,8-11 R☉, σ★ 0,20″, ~300 estrelles)
  l'error estadístic surt petit. El resultat final el fixa el terra:
""")
_, st_ref, n_ref = escenari(12.5, 1.8, 11.0, 0.20, 2.5, 0.0, camp_deg2=12.0)
print(f"  error estadístic amb {n_ref} estrelles: σ_stat(ε) = {st_ref:.3f}\n")
print(f"  {'terra correlacionat':>22} {'σ(ε) final':>12} {'GR':>8} {'E contra N':>12}")
print("  " + "-" * 58)
for sc, etiqueta in ((0.0, "cap (impossible)"), (0.02, "2 %, excel·lent"),
                     (0.03, "3 %, nivell Bruns"), (0.05, "5 %"),
                     (0.10, "10 %, els professionals fins al 1973"),
                     (0.20, "20 %"), (0.40, "40 %, campanya descurada")):
    t = math.hypot(st_ref, sc)
    print(f"  {etiqueta:>22} {t:12.3f} {1/t:7.1f}σ {0.5/t:11.1f}σ")

print("\n" + "=" * 78)
print("3. ELS ESCENARIS HONESTOS PER AL 2027")
print("=" * 78)
print(f"\n  {'escenari':<44} {'N':>5} {'σ★':>6} {'terra':>6} {'σ(ε)':>7} {'GR':>7} {'E-N':>6}")
print("  " + "-" * 86)

CASOS = [
    ("res canvia: mateix equip, Sol alt",      11.0, 2.0, 9.6, 0.55, 4.0, 0.35, 11.6),
    ("+ camp de comparació nocturn",           11.5, 1.9, 9.6, 0.30, 3.0, 0.12, 11.6),
    ("+ Gaia DR3 i reducció en alt-az",        12.0, 1.9, 9.6, 0.22, 3.0, 0.07, 11.6),
    ("+ sensor mono ben mostrejat",            12.5, 1.8, 9.6, 0.15, 2.5, 0.05, 11.6),
    ("+ autocalibratge de distorsió",          12.5, 1.8, 11.0, 0.13, 2.5, 0.03, 12.0),
    ("+ filtre vermell i doble instrument",    12.8, 1.8, 11.0, 0.11, 2.5, 0.02, 12.0),
]
for nom, vlim, rmin, rmax, ss, fwhm, sc, area in CASOS:
    t, st, n = escenari(vlim, rmin, rmax, ss, fwhm, sc, camp_deg2=area)
    print(f"  {nom:<44} {n:5d} {ss:5.2f}″ {sc:5.0%} {t:7.3f} {1/t:6.1f}σ {0.5/t:5.1f}σ")

print("\n" + "=" * 78)
print("4. EL RESUM QUE VAL")
print("=" * 78)
print("""
  El 2026 vam quedar a σ(ε) = 0,53. Els factors necessaris:

      1,6×   detectar la deflexió a 3σ
      3,2×   distingir Einstein de Newton a 3σ
      5,3×   el ±10 % d'Eddington
     17,7×   el ±3 % de Bruns 2017

  D'aquests factors, el Sol alt en regala una part molt gran: passar de 9°
  a 40-80° d'altura val, tot sol, entre un factor 3 i un factor 6, perquè
  millora alhora el seeing, la brillantor del cel (i per tant la fondària) i
  el residu de refracció. Amb el mateix equip i el mateix mètode, el 2027 ja
  hauria de donar una detecció de 3-4σ.

  Però per damunt d'aquí manen dues coses que no es compren amb diners:

      · el CAMP DE COMPARACIÓ nocturn, que és l'única manera de restar la
        distorsió òptica pròpia. És el que Eddington tenia i nosaltres no.
      · el TERRA SISTEMÀTIC, que no baixa amb el nombre d'estrelles.

  Amb 300 estrelles, l'error estadístic és del 2 % i el resultat final és
  exactament el terra sistemàtic que s'aconsegueixi. Aquí és on es guanya o
  es perd la mesura.
""")
