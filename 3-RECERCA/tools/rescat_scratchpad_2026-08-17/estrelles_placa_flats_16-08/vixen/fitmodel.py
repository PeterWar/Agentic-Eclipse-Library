import numpy as np, lib, stack2
from scipy.optimize import least_squares
from scipy.special import erf

PHI = lambda z: 0.5*(1+erf(z/np.sqrt(2)))


def esf_model(p, u):
    u0, s1, s2, f, base, sl = p
    return base + sl*u + (f*PHI((u-u0)/s1) + (1-f)*PHI((u-u0)/s2))


def lsf_model(p, u):
    u0, s1, s2, f, base, sl = p
    g = lambda s: np.exp(-0.5*((u-u0)/s)**2)/(s*np.sqrt(2*np.pi))
    return f*g(s1) + (1-f)*g(s2)


def fwhm_of(p, half_side=False):
    u = np.linspace(p[0]-40, p[0]+40, 400001)
    L = lsf_model(p, u)
    i = np.argmax(L); h = L[i]/2
    li = np.where(L[:i] < h)[0][-1]
    ri = i + np.where(L[i:] < h)[0][0]
    l = np.interp(h, [L[li], L[li+1]], [u[li], u[li+1]])
    r = np.interp(-h, [-L[ri-1], -L[ri]], [u[ri-1], u[ri]])
    return r-l, u[i]-l, r-u[i]


def fit(c, med, umax=14.0):
    m = np.isfinite(med) & (np.abs(c) < umax)
    u = c[m]; y = med[m]
    p0 = [0.0, 0.9, 2.5, 0.7, 0.0, 0.0]
    r = least_squares(lambda p: esf_model(p, u)-y, p0,
                      bounds=([-3, 0.2, 0.4, 0.0, -0.3, -0.05],
                              [3, 6, 25, 1.0, 0.3, 0.05]), max_nfev=6000)
    return r.x, np.sqrt(np.mean(r.fun**2))


if __name__ == "__main__":
    print("model: dues gaussianes (nucli + halo), ajust directe sobre l'ESF apilada\n")
    for key in ('R', 'G1', 'G2', 'B'):
        c, med, cnt = np.load(f"stack_{key}.npy")
        for umax in (8.0, 14.0, 20.0):
            p, rms = fit(c, med, umax)
            fw, hi, ho = fwhm_of(p)
            u0, s1, s2, f, base, sl = p
            print("%3s  |u|<%4.1f px   FWHM=%.3f px = %.2f\"   nucli s1=%.2f px (pes %.2f)  "
                  "halo s2=%.2f px  rms=%.4f" %
                  (key, umax, fw, fw*lib.SCALE, s1, f, s2, rms))
        print()
