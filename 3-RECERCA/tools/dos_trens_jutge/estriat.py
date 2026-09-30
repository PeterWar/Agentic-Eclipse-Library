"""L'ESTRIAT DEL `research/113`, decidit amb els dos trens.

Pere va marcar en lila un estriat al detall. El `113` en va mesurar dues
famílies per FFT —λ ≈ 4,1 px alineada amb els eixos i λ ≈ 51 px a 10°/80°— i va
declarar que amb un sol tren no es podia dir d'on venia. Ara es pot, perquè els
dos trens miren el mateix cel amb els sensors **girats 33,08°** i amb escales
diferents (2,1495 i 3,2020 ''/px). Al llenç comú:

| origen | direcció | mida |
|---|---|---|
| CEL (real) | la mateixa als dos | la mateixa |
| SENSOR (orientació) | **girada 33,08°** | la mateixa |
| PÍXEL del sensor | girada 33,08° | la de la Sony ×1,49 |

⛔ L'FFT es fa sobre l'estructura NORMALITZADA PER RADI: sobre la dada crua la
mana el perfil radial i el resultat només parla d'ell.
"""
from __future__ import annotations

import json
import os

import numpy as np
import cv2

import nucli as N

NB = 900


def normalitza_radi(a, m, rad, nb=NB, rmax=None):
    """Treu el perfil radial: (a − mediana(r)) / MAD(r). Deixa només l'estriat."""
    rmax = rmax or float(rad[m].max())
    idx = np.clip((rad / rmax * nb).astype(np.int32), 0, nb - 1)
    k = m & np.isfinite(a)
    c = np.bincount(idx[k], None, nb); s = np.bincount(idx[k], a[k], nb)
    mu = np.where(c > 200, s / np.maximum(c, 1), np.nan)
    s2 = np.bincount(idx[k], np.abs(a[k] - mu[idx[k]]), nb)
    sd = np.where(c > 200, s2 / np.maximum(c, 1), np.nan) * 1.4826
    for v in (mu, sd):
        bo = np.isfinite(v)
        v[:] = np.interp(np.arange(nb), np.arange(nb)[bo], v[bo])
    return np.where(k, (a - mu[idx]) / np.maximum(sd[idx], 1e-12), 0.0)


def espectre(z, m, finestra=True):
    """Potència 2-D. La finestra de Hann evita que la vora del retall
    fabriqui una creu d'energia als eixos —que és justament la direcció on
    el `113` deia que hi havia una de les famílies—."""
    z = np.where(m, z, 0.0).astype(np.float64)
    if finestra:
        wy = np.hanning(z.shape[0])[:, None]; wx = np.hanning(z.shape[1])[None, :]
        z = z * wy * wx
    F = np.fft.fftshift(np.fft.fft2(z))
    return np.abs(F) ** 2


def pics(P, esc_px, nf=48, nd=180, lam_min=2.5, lam_max=200.0):
    """Potència per (longitud d'ona en px de llenç, direcció en graus)."""
    ny, nx = P.shape
    fy = np.fft.fftshift(np.fft.fftfreq(ny))[:, None]
    fx = np.fft.fftshift(np.fft.fftfreq(nx))[None, :]
    f = np.hypot(fy, fx)
    lam = np.where(f > 0, 1.0 / np.maximum(f, 1e-12), np.inf)
    ang = (np.degrees(np.arctan2(fy, fx)) % 180.0)
    k = (lam >= lam_min) & (lam <= lam_max)
    li = np.clip(((np.log(np.where(k, lam, lam_min)) - np.log(lam_min))
                  / (np.log(lam_max) - np.log(lam_min)) * nf).astype(int), 0, nf - 1)
    ai = np.clip((ang / 180.0 * nd).astype(int), 0, nd - 1)
    idx = li * nd + ai
    s = np.bincount(idx[k], P[k], nf * nd).reshape(nf, nd)
    c = np.bincount(idx[k], None, nf * nd).reshape(nf, nd)
    M = np.where(c > 8, s / np.maximum(c, 1), np.nan)
    lams = np.exp(np.log(lam_min) + (np.arange(nf) + 0.5) / nf
                  * (np.log(lam_max) - np.log(lam_min)))
    angs = (np.arange(nd) + 0.5) * 180.0 / nd
    return M, lams, angs
