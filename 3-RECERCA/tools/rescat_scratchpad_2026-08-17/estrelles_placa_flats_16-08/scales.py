"""Senyal contra soroll escala per escala, amb el soroll propagat des del guany."""
import numpy as np
from scipy.ndimage import gaussian_filter


def scale_snr(S_adu, g, rn_adu, mask, sigmas=(0.5, 0.75, 1, 1.5, 2, 3, 4, 6, 8), corr=1.0):
    """Descomposicio en diferencies de gaussianes.
    S_adu: imatge en ADU sobre el pedestal. mask: on mesurar.
    Retorna per a cada escala: rms de l'estructura i rms del soroll propagat."""
    var = np.clip(S_adu, 0, None) / g + rn_adu ** 2
    out = []
    prev_s = 0.0
    for s in sigmas:
        # banda entre l'escala anterior i aquesta
        a = gaussian_filter(S_adu, prev_s) if prev_s > 0 else S_adu.copy()
        b = gaussian_filter(S_adu, s)
        band = a - b
        # nucli efectiu de la banda i propagacio de la variancia
        n = 65
        d = np.zeros((n, n)); d[n // 2, n // 2] = 1.0
        ka = gaussian_filter(d, prev_s) if prev_s > 0 else d
        kb = gaussian_filter(d, s)
        k = ka - kb
        k2 = float(np.sum(k ** 2)) * corr
        nvar = gaussian_filter(var, 0)  # variancia local
        noise_rms = float(np.sqrt(np.mean(nvar[mask]) * k2))
        sig_rms = float(np.std(band[mask]))
        # el senyal net: treu la contribucio del soroll en quadratura
        net = np.sqrt(max(sig_rms ** 2 - noise_rms ** 2, 0.0))
        out.append(dict(sigma=s, prev=prev_s, band_rms=sig_rms, noise_rms=noise_rms,
                        net=net, snr=sig_rms / noise_rms, net_snr=net / noise_rms))
        prev_s = s
    return out
