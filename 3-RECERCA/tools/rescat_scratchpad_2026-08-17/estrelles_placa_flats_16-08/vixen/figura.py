import numpy as np, json, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import lib, fitmodel, viab2

fig, ax = plt.subplots(2, 2, figsize=(12.5, 9))
COL = {'R': '#c0392b', 'G1': '#27ae60', 'G2': '#16a085', 'B': '#2980b9'}
NOM = {'R': 'vermell', 'G1': 'verd 1', 'G2': 'verd 2', 'B': 'blau'}

# --- a) ESF apilada + LSF
a = ax[0, 0]
for k in ('R', 'G1', 'B'):
    c, m, _ = np.load(f"stack_{k}.npy")
    p, _ = fitmodel.fit(c, m, 14.0)
    u = np.linspace(-6, 6, 2001)
    a.plot(c*lib.SCALE, m, '.', ms=1.5, color=COL[k], alpha=.35)
    a.plot(u*lib.SCALE, fitmodel.esf_model(p, u), '-', color=COL[k], lw=1.6,
           label="%s  FWHM=%.2f\"" % (NOM[k], fitmodel.fwhm_of(p)[0]*lib.SCALE))
a.set_xlim(-13, 13); a.set_ylim(-.05, 1.1)
a.set_xlabel("distancia al limbe lunar (arcsec)   -- negatiu = dins del disc")
a.set_ylabel("ESF normalitzada")
a.set_title("Via A: tall de ganivet al limbe lunar (12 fotogrames apilats)")
a.legend(fontsize=9); a.grid(alpha=.3)

# --- b) LSF
a = ax[0, 1]
for k in ('R', 'G1', 'B'):
    c, m, _ = np.load(f"stack_{k}.npy")
    p, _ = fitmodel.fit(c, m, 14.0)
    u = np.linspace(-10, 10, 4001)
    L = fitmodel.lsf_model(p, u); L /= L.max()
    a.plot(u*lib.SCALE, L, color=COL[k], lw=1.8, label=NOM[k])
a.axhline(.5, color='k', ls=':', lw=.8)
a.axvline(-lib.SCALE, color='gray', ls='--', lw=.8)
a.axvline(lib.SCALE, color='gray', ls='--', lw=.8)
a.text(lib.SCALE*1.1, .9, "1 pixel", fontsize=8, color='gray')
a.set_xlim(-13, 13); a.set_xlabel("arcsec"); a.set_ylabel("LSF normalitzada")
a.set_title("Perfil de linia: nucli estret + ales")
a.legend(fontsize=9); a.grid(alpha=.3)

# --- c) serie temporal
a = ax[1, 0]
d = json.load(open("serie.json"))
t = np.array([r[1] for r in d]); f = np.array([r[2] for r in d])
a.plot(t, f, 'o-', ms=4, color='#27ae60', lw=.8)
a.axhline(np.median(f), color='k', ls='--', lw=1, label="mediana %.2f\"" % np.median(f))
a.axhspan(4.6, 12.2, color='orange', alpha=.15, label="estimacio teorica previa 4,6-12,2\"")
a.set_xlabel("segons des de C2"); a.set_ylabel("FWHM verd (arcsec)")
a.set_title("Resolucio fotograma a fotograma durant la totalitat")
a.set_ylim(0, 13); a.legend(fontsize=8); a.grid(alpha=.3)

# --- d) Via B
a = ax[1, 1]
for pair, lab, col in ((("572A2999.CR3", "572A3005.CR3"), "1/125, corona interior", "#8e44ad"),
                       (("572A3012.CR3", "572A3013.CR3"), "1/3200, protuberancia", "#e67e22")):
    cy, cx, h = (1683, 3572, 96) if "corona" in lab else (2245+int(482*np.cos(np.radians(47))),
                                                          3572+int(482*np.sin(np.radians(47))), 48)
    A = lib.load(pair[0]); B = lib.load(pair[1])
    qa, _ = viab2.quincunx(A, cy-h, cy+h, cx-h, cx+h)
    qb, _ = viab2.quincunx(B, cy-h, cy+h, cx-h, cx+h)
    n0 = min(qa.shape[0], qb.shape[0])//2*2; n1 = min(qa.shape[1], qb.shape[1])//2*2
    F, S, N, _ = viab2.spectra(qa[:n0, :n1], qb[:n0, :n1])
    ok = (F > 0.02) & (S > 0)
    a.loglog(F[ok]/viab2.STEP, S[ok], '-', color=col, lw=1.8, label="senyal: "+lab)
    a.loglog(F/viab2.STEP, N, ':', color=col, lw=1.4, label="soroll: "+lab)
a.axvline(1/(4*lib.SCALE), color='k', ls='--', lw=1)
a.text(1/(4*lib.SCALE)*1.03, 1e3, "Nyquist pla Bayer\n(8,63\")", fontsize=7)
a.axvline(1/(2*np.sqrt(2)*lib.SCALE), color='k', ls='-.', lw=1)
a.text(1/(2*np.sqrt(2)*lib.SCALE)*1.03, 1e1, "Nyquist verd\n(6,10\")", fontsize=7)
a.set_xlabel("frequencia espacial (cicles/arcsec)")
a.set_ylabel("potencia")
a.set_title("Via B: senyal (suma) contra soroll (diferencia)")
a.legend(fontsize=7); a.grid(alpha=.3, which='both')

fig.suptitle("Resolucio angular real del tren Vixen VSD90SS + Canon R6 III — eclipsi 12-08-2026",
             fontsize=13)
fig.tight_layout()
fig.savefig("resolucio_vixen.png", dpi=130)
print("desat resolucio_vixen.png")
