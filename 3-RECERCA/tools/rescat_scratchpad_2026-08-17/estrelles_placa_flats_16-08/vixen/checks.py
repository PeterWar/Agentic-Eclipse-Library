import numpy as np, lib, esf, stack2, fitmodel

# ---------- 1. prova de biaix per soroll ----------
print("=== 1. prova de biaix: degradem un fotograma llarg fins a la relacio S/N d'un de 1/3200 ===")
rng = np.random.default_rng(7)


def snr_med(img, geo, key):
    _, _, o = esf.measure_frame('', keys=[key], nsec=240, img=img, geo=geo)
    a = np.array([x['amp'] for x in o[key]['rows']])
    r = np.array([x['rms'] for x in o[key]['rows']])
    return np.median(a/np.maximum(r, 1e-9))


ref = lib.load("572A2999.CR3"); gref = lib.solve_geometry(ref)[:3]
sh = lib.load("572A3012.CR3"); gsh = lib.solve_geometry(sh)[:3]
s_ref = snr_med(ref, gref, 'G1'); s_sh = snr_med(sh, gsh, 'G1')
print("   S/N mediana per sector, G1:  1/125 = %.1f   1/3200 = %.1f" % (s_ref, s_sh))

med, _ = stack2.merge([stack2.accumulate(ref, gref, 'G1', snr_min=12)])
p, _ = fitmodel.fit(stack2.cent, med, 14.0)
fw0 = fitmodel.fwhm_of(p)[0]*lib.SCALE
print("   1/125 net                    FWHM = %.2f\"" % fw0)

for fac in (2.0, 4.0, 8.0):
    # soroll blanc que baixa la S/N pel factor demanat
    base = np.std(ref[100:1100, 100:1100])
    amp = np.sqrt(max((fac**2-1), 0))*np.sqrt(np.mean((ref[100:1100, 100:1100]-ref[100:1100, 100:1100].mean())**2))
    noisy = ref + rng.normal(0, amp, ref.shape)
    s = snr_med(noisy, gref, 'G1')
    med, _ = stack2.merge([stack2.accumulate(noisy, gref, 'G1', snr_min=8)])
    try:
        p, _ = fitmodel.fit(stack2.cent, med, 14.0)
        fw = fitmodel.fwhm_of(p)[0]*lib.SCALE
    except Exception:
        fw = np.nan
    print("   + soroll x%.0f  -> S/N=%5.1f      FWHM = %.2f\"  (biaix %+.2f\")" % (fac, s, fw, fw-fw0))

# ---------- 2. flux relatiu dels canals i PSF composta ----------
print("\n=== 2. PSF composta (RGB junts, amb la dispersio sense corregir) ===")
img = lib.load("572A2999.CR3"); CY, CX, R = lib.solve_geometry(img)[:3]
flux = {}
for key in ('R', 'G1', 'G2', 'B'):
    p_, oy, ox = lib.plane(img, key)
    ii, jj = np.mgrid[0:p_.shape[0], 0:p_.shape[1]]
    r = np.hypot(2*ii+oy-CY, 2*jj+ox-CX)
    flux[key] = float(np.median(p_[(r > R+20) & (r < R+150)]))
print("   flux medi de la corona interior:", {k: round(v, 1) for k, v in flux.items()})
wR = flux['R']; wG = flux['G1']+flux['G2']; wB = flux['B']
tot = wR+wG+wB
print("   pesos relatius  R=%.2f  G=%.2f  B=%.2f" % (wR/tot, wG/tot, wB/tot))

FW = {'R': 4.20, 'G': 5.24, 'B': 6.67}          # arcsec, tots els azimuts
OFF = {'R': +1.54, 'G': 0.0, 'B': -1.54}        # desplacament al llarg de l'eix vertical (R-B=3,08")
u = np.linspace(-30, 30, 60001)
for corregit in (False, True):
    L = np.zeros_like(u)
    for k, w in (('R', wR/tot), ('G', wG/tot), ('B', wB/tot)):
        s = FW[k]/2.3548
        c = 0.0 if corregit else OFF[k]
        L += w*np.exp(-0.5*((u-c)/s)**2)/(s*np.sqrt(2*np.pi))
    i = np.argmax(L); h = L[i]/2
    l = np.interp(h, [L[np.where(L[:i] < h)[0][-1]], L[np.where(L[:i] < h)[0][-1]+1]],
                  [u[np.where(L[:i] < h)[0][-1]], u[np.where(L[:i] < h)[0][-1]+1]])
    j = i+np.where(L[i:] < h)[0][0]
    rr = np.interp(-h, [-L[j-1], -L[j]], [u[j-1], u[j]])
    print("   FWHM composta (%s dispersio) al llarg de la vertical = %.2f\"" %
          ("sense" if corregit else "amb", rr-l))

# ---------- 3. MTF del model ajustat ----------
print("\n=== 3. MTF del model ajustat a l'ESF apilada ===")
f_nyq_pla = 1.0/(2*2*lib.SCALE)       # c/arcsec, pla de Bayer (pas 4,316\")
f_nyq_qui = 1.0/(2*np.sqrt(2)*lib.SCALE)
print("   Nyquist pla de Bayer = %.4f c/arcsec (periode %.2f\") ; quincunx verd = %.4f c/arcsec (%.2f\")"
      % (f_nyq_pla, 1/f_nyq_pla, f_nyq_qui, 1/f_nyq_qui))
for key in ('R', 'G1', 'G2', 'B'):
    c, m, _ = np.load(f"stack_{key}.npy")
    p, _ = fitmodel.fit(c, m, 14.0)
    u0, s1, s2, fr, b, sl = p
    def M(f):
        return fr*np.exp(-2*np.pi**2*(s1*lib.SCALE)**2*f**2) + (1-fr)*np.exp(-2*np.pi**2*(s2*lib.SCALE)**2*f**2)
    ff = np.linspace(0, 0.3, 30001); mm = M(ff)
    f50 = np.interp(-0.5, -mm, ff); f10 = np.interp(-0.1, -mm, ff)
    print("   %3s  MTF50 a %.4f c/arcsec (periode %5.2f\")  MTF10 a periode %5.2f\"  |  "
          "MTF(Nyq pla)=%.3f  MTF(Nyq quincunx)=%.3f" %
          (key, f50, 1/f50, 1/f10, M(f_nyq_pla), M(f_nyq_qui)))
