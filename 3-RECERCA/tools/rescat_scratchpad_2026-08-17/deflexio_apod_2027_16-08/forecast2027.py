#!/usr/bin/env python3
"""Previsió per al 2027, validada contra Bruns 2017 i contra el nostre 2026.

Comptatges reals del camp del 2027 (Tycho-2, anell de 2 a 15 R☉):
    V<6: 5 · V<7: 29 · V<8: 70 · V<9: 177 · V<10: 438 · V<11: 944
"""
import math
import numpy as np

ALPHA = 1.7516
rng = np.random.default_rng(2027)

# comptatges acumulats mesurats al camp real de cada any (2-15 R☉, 47,9 graus²)
COMPTES = {
    2027: {6: 5, 7: 29, 8: 70, 9: 177, 10: 438, 11: 944},
    2026: {6: 4, 7: 18, 8: 42, 9: 101, 10: 275, 11: 636},
    1919: {6: 13, 7: 24, 8: 61, 9: 128, 10: 285, 11: 627},
    2017: {6: 4, 7: 10, 8: 28, 9: 84, 10: 224, 11: 564},
}
ANELL_R = (2.0, 15.0)


def poblacio(any_, vlim, rmin, rmax):
    """Estrelles (r, V) del camp real, retallat al rang radial demanat."""
    c = COMPTES[any_]
    ms = sorted(c)
    # interpolació log-lineal del comptatge acumulat
    lx = [c[m] for m in ms]
    if vlim <= ms[0]:
        n_tot = c[ms[0]] * 10 ** (0.42 * (vlim - ms[0]))
    elif vlim >= ms[-1]:
        n_tot = c[ms[-1]] * 10 ** (0.42 * (vlim - ms[-1]))
    else:
        n_tot = math.exp(np.interp(vlim, ms, np.log(lx)))
    # fracció de l'anell que cau dins [rmin, rmax]
    f = ((min(rmax, ANELL_R[1]) ** 2 - max(rmin, ANELL_R[0]) ** 2) /
         (ANELL_R[1] ** 2 - ANELL_R[0] ** 2))
    f = max(f, 0.0)
    # si el camp arriba més endins de 2 R☉, hi afegim la part que toca
    if rmin < 2.0:
        dens = n_tot / (math.pi * (ANELL_R[1] ** 2 - ANELL_R[0] ** 2))
        f += math.pi * (4.0 - rmin ** 2) * dens / max(n_tot, 1e-9)
    n = rng.poisson(max(n_tot * f, 0.0))
    if n < 4:
        return None
    r = np.sqrt(rng.uniform(max(rmin, 0.5) ** 2, rmax ** 2, n))
    u = rng.uniform(0, 1, n)
    V = np.clip(vlim + np.log10(u) / 0.42, 3.5, vlim)
    return r, rng.uniform(0, 2 * math.pi, n), V


def sigma_eps(r, th, sig, escala_externa=False, ordre3=False):
    """σ(ε). escala_externa = el truc de Bruns (l'escala ve de camps de calibratge)."""
    n = len(r)
    cols = 3 if escala_externa else 4
    if ordre3:
        cols += 4                                   # termes r³ radials i tangencials
    A = np.zeros((2 * n, cols + 1)); w = np.zeros(2 * n)
    for i in range(n):
        x, y = r[i] * math.cos(th[i]), r[i] * math.sin(th[i])
        A[2*i, 0] = 1.0; A[2*i+1, 1] = 1.0
        A[2*i, 2] = -y;  A[2*i+1, 2] = x
        k = 3
        if not escala_externa:
            A[2*i, k] = x; A[2*i+1, k] = y; k += 1
        if ordre3:
            r3 = r[i] ** 2
            A[2*i, k] = x*r3;   A[2*i+1, k] = y*r3;   k += 1
            A[2*i, k] = -y*r3;  A[2*i+1, k] = x*r3;   k += 1
            A[2*i, k] = x*x*x;  A[2*i+1, k] = y*y*y;  k += 1
            A[2*i, k] = x*y*y;  A[2*i+1, k] = y*x*x;  k += 1
        a = ALPHA / r[i]
        A[2*i, cols] = a*math.cos(th[i]); A[2*i+1, cols] = a*math.sin(th[i])
        w[2*i] = w[2*i+1] = 1.0 / sig[i] ** 2
    try:
        return math.sqrt(np.linalg.inv(A.T @ (A * w[:, None]))[cols, cols])
    except np.linalg.LinAlgError:
        return float("nan")


def sig_estrella(V, vlim, fwhm, terra, snr_lim=5.0):
    snr = snr_lim * 10 ** (0.4 * (vlim - V))
    return np.sqrt(terra ** 2 + (0.601 * fwhm / snr) ** 2)   # règim limitat pel cel


def corre(any_, vlim, rmin, rmax, fwhm, terra, escala_externa=False, ordre3=False, nrep=15):
    out, ns = [], []
    for _ in range(nrep):
        p = poblacio(any_, vlim, rmin, rmax)
        if p is None:
            continue
        r, th, V = p
        s = sigma_eps(r, th, sig_estrella(V, vlim, fwhm, terra), escala_externa, ordre3)
        if s == s:
            out.append(s); ns.append(len(r))
    return float(np.median(out)), int(np.median(ns))


print("=" * 82)
print("VALIDACIÓ 1 — BRUNS 2017 (resultat publicat: 3,1 % del terme d'estrelles)")
print("=" * 82)
r = np.sqrt(rng.uniform(1.51 ** 2, 4.82 ** 2, 20))
th = rng.uniform(0, 2 * math.pi, 20)
sig = np.full(20, 0.077)
s_ext = sigma_eps(r, th, sig, escala_externa=True)
s_int = sigma_eps(r, th, sig, escala_externa=False)
print(f"  20 estrelles de 1,51 a 4,82 R☉, σ★ = 0,077″")
print(f"    amb l'escala de camps de calibratge : σ(ε) = {s_ext:.3f}  ({s_ext*100:.1f} %)")
print(f"    publicat per Bruns (terme d'estrelles)      3,1 %  → concorda a {100*(s_ext/0.031-1):+.0f} %")
print(f"    amb l'escala treta del mateix camp : σ(ε) = {s_int:.3f}  ({s_int*100:.1f} %)")
print(f"    → el truc dels camps de calibratge val un factor {s_int/s_ext:.2f}")

print("\n" + "=" * 82)
print("VALIDACIÓ 2 — EL NOSTRE 2026")
print("=" * 82)
s26, n26 = corre(2026, vlim=9.7, rmin=2.16, rmax=9.6, fwhm=5.8, terra=0.50)
print(f"  camp real del 2026, {n26} estrelles, terra 0,50″ + soroll de cel → σ(ε) = {s26:.3f}")
print(f"  mesurat de veritat: 0,573 (tren Vixen)  → concorda a {100*(s26/0.573-1):+.0f} %")

print("\n" + "=" * 82)
print("PREVISIÓ 2027, AMB EL CAMP REAL (M44, Venus i δ Cancri hi són)")
print("=" * 82)
print(f"\n  {'configuració':<46} {'N':>4} {'σ★':>6} {'σ(ε)':>7} {'GR':>7} {'E-N':>6}")
print("  " + "-" * 82)

CASOS = [
    # (nom, vlim, rmin, rmax, fwhm, terra, escala_externa, ordre3)
    ("2026 tal com va anar, per referència",     9.7, 2.16, 9.6, 5.8, 0.50, False, False),
    ("mateix equip i mètode, però a Luxor",     10.6, 1.9, 9.6, 2.5, 0.45, False, False),
    ("+ seguiment SIDERI i muntura ben alineada", 10.6, 1.9, 9.6, 2.5, 0.30, False, False),
    ("+ Gaia DR3 i reducció en alt-az",         10.6, 1.9, 9.6, 2.5, 0.25, False, False),
    ("+ autocalibratge de distorsió nocturn",   10.6, 1.9, 9.6, 2.5, 0.12, False, False),
    ("+ camps de calibratge dins la totalitat", 10.6, 1.9, 9.6, 2.5, 0.12, True, False),
    ("+ mono amb filtre r' i bon mostreig",     11.6, 1.8, 9.6, 2.5, 0.08, True, False),
    ("+ camp de 3° de radi (M44 i Venus dins)", 11.6, 1.8, 11.4, 2.5, 0.08, True, False),
    ("   ...i amb model de placa de 3r ordre",  11.6, 1.8, 11.4, 2.5, 0.08, True, True),
]
for nom, vlim, rmin, rmax, fwhm, terra, ext, o3 in CASOS:
    s, n = corre(2027 if "2026" not in nom else 2026, vlim, rmin, rmax, fwhm, terra, ext, o3)
    print(f"  {nom:<46} {n:4d} {terra:5.2f}″ {s:7.3f} {1/s:6.1f}σ {0.5/s:5.1f}σ")

print("""
  ⚠️ Aquests σ(ε) són l'error ALEATORI. Cal sumar-hi en quadratura el terra
     sistemàtic correlacionat, que no baixa amb el nombre d'estrelles i que a
     Bruns li va valdre un 1,23 % (escala) i als professionals fins al 1973
     un 10 %. Amb un 2 % de terra, res per sota de σ(ε) = 0,02 no és creïble.""")

print("\n" + "=" * 82)
print("EL QUE DECIDEIX: la fuita de la distorsió òptica cap a ε")
print("=" * 82)
print("""
  Δε ≈ 0,45 × A, amb A el residu radial de distorsió a la vora del camp.
""")
for A, q in ((1.0, "sense corregir, refractor típic a 1° fora d'eix"),
             (0.30, "model de placa lineal i prou"),
             (0.10, "model de 3r ordre dins el mateix fotograma"),
             (0.02, "calibratge nocturn dedicat, com Bruns"),
             (0.005, "límit del que s'ha publicat")):
    print(f"     A = {A:5.3f}″  →  Δε = {0.45*A:6.3f}  ({45*A:5.1f} % de la deflexió)   {q}")

print("\n" + "=" * 82)
print("I LA TEMPERATURA, QUE ÉS EL PARANY CLÀSSIC")
print("=" * 82)
print("""
  Un tub d'alumini canvia l'escala 22-26 ppm/K. Radialment, a 2° del centre:
""")
for dT in (0.5, 1, 2, 5, 10):
    despl = 24e-6 * dT * 2.0 * 3600
    print(f"     ΔT = {dT:4.1f} K  →  {despl:6.3f}″ de desplaçament radial a 2°"
          f"  →  Δε ≈ {0.45*despl:5.2f}")
print("""
  Entre el calibratge nocturn i l'eclipsi hi pot haver 20 K. Amb tub d'alumini
  això són 4″ a la vora: DOS COPS la deflexió sencera. Per això Bruns va treure
  l'escala de camps de calibratge presos DINS la totalitat, amb el tub a la
  mateixa temperatura, en lloc de fiar-se del calibratge nocturn.
  ⛔ El calibratge nocturn serveix per a la FORMA de la distorsió, no per a
     l'ESCALA. Són dues coses i es mesuren en dos moments diferents.""")
