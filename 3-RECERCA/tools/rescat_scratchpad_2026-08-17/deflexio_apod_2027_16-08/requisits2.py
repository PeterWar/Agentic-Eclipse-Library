#!/usr/bin/env python3
"""Requisits per al 2027, v2: cada estrella amb el seu propi error.

σ_i² = σ_sistemàtic² + (FWHM / (2,355 · S/N_i))²
i la densitat d'estrelles ancorada a la que vam mesurar de veritat el 2026.
"""
import math
import numpy as np

R_SOL = 946.66
ALPHA = 1.7516
rng = np.random.default_rng(20260812)

# ── ancoratge de densitat: el que vam MESURAR el 2026 ────────────────────────
#   tren Vixen: 24 estrelles a 4,17 x 2,78 graus = 11,59 graus² → 2,07 per grau²
#   la més feble identificada V=9,18; les inferides arriben a V≈9,7
DENS_2026, VLIM_2026 = 2.07, 9.7
PENDENT = 0.42          # d log N / d mag a alta latitud galàctica


def densitat(vlim):
    """estrelles per grau² fins a la magnitud vlim"""
    return DENS_2026 * 10 ** (PENDENT * (vlim - VLIM_2026))


def sigma_eps(r, th, sig, npar=4):
    n = len(r)
    A = np.zeros((2 * n, npar + 1))
    w = np.zeros(2 * n)
    for i in range(n):
        x, y = r[i] * math.cos(th[i]), r[i] * math.sin(th[i])
        A[2*i, 0] = 1.0; A[2*i+1, 1] = 1.0
        A[2*i, 2] = -y;  A[2*i+1, 2] = x
        A[2*i, 3] = x;   A[2*i+1, 3] = y
        if npar == 6:
            A[2*i, 4] = x; A[2*i+1, 4] = -y
            A[2*i, 5] = y; A[2*i+1, 5] = x
        a = ALPHA / r[i]
        A[2*i, npar] = a * math.cos(th[i]); A[2*i+1, npar] = a * math.sin(th[i])
        w[2*i] = w[2*i+1] = 1.0 / sig[i] ** 2
    N = A.T @ (A * w[:, None])
    return math.sqrt(np.linalg.inv(N)[npar, npar])


def camp(vlim, rmin, rmax, sig_sys, fwhm, snr_lim=5.0, npar=4, nrep=12):
    """σ(ε) d'un camp sintètic complet."""
    dens = densitat(vlim) * (R_SOL / 3600.0) ** 2      # per R☉²
    area = math.pi * (rmax ** 2 - rmin ** 2)
    ntot = dens * area
    out, ns = [], []
    for _ in range(nrep):
        n = rng.poisson(ntot)
        if n < 6:
            continue
        r = np.sqrt(rng.uniform(rmin ** 2, rmax ** 2, n))
        th = rng.uniform(0, 2 * math.pi, n)
        # magnituds segons la llei de comptatge, entre 5 i vlim
        u = rng.uniform(0, 1, n)
        m = vlim + np.log10(u) / PENDENT
        m = np.clip(m, 5.0, vlim)
        snr = snr_lim * 10 ** (0.4 * (vlim - m))
        sig = np.sqrt(sig_sys ** 2 + (fwhm / (2.355 * snr)) ** 2)
        out.append(sigma_eps(r, th, sig, npar))
        ns.append(n)
    return float(np.median(out)), int(np.median(ns))


print("=" * 78)
print("VALIDACIÓ: el model reprodueix el 2026?")
print("=" * 78)
s, n = camp(vlim=9.7, rmin=2.16, rmax=9.6, sig_sys=0.62, fwhm=5.8, snr_lim=5)
print(f"  tren Vixen simulat : {n} estrelles, σ(ε) = {s:.3f}")
print(f"  tren Vixen mesurat : 24 estrelles, σ(ε) = 0.573")
print(f"  → el model {'concorda' if abs(s/0.573-1) < 0.25 else 'NO concorda'} "
      f"({100*(s/0.573-1):+.0f} %)")

print("\n" + "=" * 78)
print("QUANT ES GUANYA EN FONDÀRIA EL 2027, I QUÈ VAL")
print("=" * 78)
print("""
  El 2026 el cel de la totalitat feia 9,2 mag/arcsec² — extraordinàriament
  brillant, perquè el Sol era a 9° i la llum travessava 6,1 masses d'aire.
  Amb el Sol alt cada component millora:""")
guanys = [
    ("cel més fosc (de 9,2 a ~12,7 mag/arcsec²)", 3.5 / 2),
    ("seeing de 5,8″ a 2,5″ (menys fons per obertura)", 2.5 * math.log10(5.8 / 2.5)),
    ("més temps de totalitat apilat (×3,7 a Egipte)", 2.5 * math.log10(math.sqrt(3.7))),
]
tot = 0.0
for nom, dm in guanys:
    tot += dm
    print(f"     {nom:<50} +{dm:.2f} mag")
print(f"     {'':<50} ─────────")
print(f"     {'TOTAL, amb el mateix telescopi de 90 mm':<50} +{tot:.2f} mag")
print(f"     {'i amb 130 mm d obertura en lloc de 90':<50} +{tot + 2.5*math.log10((130/90)**2):.2f} mag")
vlim27 = VLIM_2026 + tot
print(f"\n  → magnitud límit {VLIM_2026:.1f} → {vlim27:.1f}"
      f"   ·   densitat {DENS_2026:.1f} → {densitat(vlim27):.0f} estrelles/grau²")

print("\n" + "=" * 78)
print("ESCENARIS PER AL 2027, UN CANVI CADA VEGADA")
print("=" * 78)
print(f"\n  {'què es canvia':<46} {'N':>4} {'σ★':>6} {'σ(ε)':>7} {'GR':>7} {'E-N':>7}")
print("  " + "-" * 78)


def linia(nom, **kw):
    s, n = camp(**kw)
    print(f"  {nom:<46} {n:4d} {kw['sig_sys']:5.2f}″ {s:7.3f} {1/s:6.1f}σ {0.5/s:6.1f}σ")
    return s


linia("2026, com va anar", vlim=9.7, rmin=2.16, rmax=9.6, sig_sys=0.62, fwhm=5.8)
linia("2027, mateix equip i mateix mètode", vlim=9.7, rmin=2.2, rmax=9.6, sig_sys=0.62, fwhm=5.8)
linia("+ Sol alt: seeing 2,5″ i cel fosc", vlim=vlim27, rmin=1.6, rmax=9.6, sig_sys=0.62, fwhm=2.5)
linia("+ camp de comparació nocturn", vlim=vlim27, rmin=1.6, rmax=9.6, sig_sys=0.25, fwhm=2.5)
linia("+ Gaia DR3 en lloc de Tycho-2", vlim=vlim27, rmin=1.6, rmax=9.6, sig_sys=0.20, fwhm=2.5)
linia("+ mono ben mostrejat (1,2″/px)", vlim=vlim27, rmin=1.5, rmax=9.6, sig_sys=0.12, fwhm=2.5)
linia("+ camp de 3° de radi en lloc d'1,7°", vlim=vlim27, rmin=1.5, rmax=11.4, sig_sys=0.12, fwhm=2.5)
linia("+ camp de 5° de radi", vlim=vlim27, rmin=1.5, rmax=19.0, sig_sys=0.12, fwhm=2.5)

print("\n  I si res del cel no acompanya (Sol alt però calima, seeing 4″):")
linia("conservador: cel només 2 mag més fosc", vlim=VLIM_2026 + 1.0, rmin=1.8, rmax=11.4,
      sig_sys=0.30, fwhm=4.0)
linia("molt conservador: només camp de comparació", vlim=VLIM_2026 + 0.5, rmin=2.0, rmax=9.6,
      sig_sys=0.35, fwhm=4.5)

print("\n" + "=" * 78)
print("EL REQUISIT, CAPGIRAT: quin σ★ cal, segons què doni el camp")
print("=" * 78)
obj = [("detectar-la a 3σ", 1/3), ("Einstein contra Newton a 3σ", 0.5/3),
       ("±10 % (Eddington)", 0.10), ("±3 % (Bruns 2017)", 0.03)]
print(f"\n  {'camp disponible':<40} " + "".join(f"{o[0]:>22}" for o in obj))
print("  " + "-" * 128)
for vlim, rmin, rmax, etiqueta in (
        (9.7, 2.2, 9.6, "pobre: com el 2026"),
        (11.5, 1.8, 11.4, "mitjà: +1,8 mag, camp 2°"),
        (vlim27, 1.5, 11.4, f"bo: +{tot:.1f} mag, camp 2°"),
        (vlim27, 1.5, 19.0, f"bo i ample: +{tot:.1f} mag, camp 5°")):
    ref, n = camp(vlim=vlim, rmin=rmin, rmax=rmax, sig_sys=1e-6, fwhm=2.5, snr_lim=5)
    # ref és σ(ε) amb σ_sys = 0; cal invertir amb el terme sistemàtic dominant
    fila = f"  {etiqueta:<28} {n:5d} estr. "
    for _, o in obj:
        lo, hi = 0.001, 5.0
        for _ in range(60):
            mid = math.sqrt(lo * hi)
            s, _ = camp(vlim=vlim, rmin=rmin, rmax=rmax, sig_sys=mid, fwhm=2.5, nrep=4)
            if s > o:
                hi = mid
            else:
                lo = mid
        fila += f"{math.sqrt(lo*hi):20.3f}″ "
    print(fila)
