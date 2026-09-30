"""Els dos trens al MATEIX llenç: el jutge independent que ens faltava.

⏭️ El discriminador nou i fort: els dos sensors estan **girats 33,08°** l'un
respecte de l'altre al cel (PA nord 57,19° la Vixen i 90,27° la Sony) i tenen
escales diferents (2,1495 i 3,2020 ''/px). Sobre el llenç comú, doncs:

- una estructura del CEL surt al mateix (r, θ) i a la mateixa mida als dos;
- una estructura del SENSOR surt **girada 33,08°** entre els dos;
- una estructura de PÍXEL DE SENSOR surt a mides diferents: λ píxels del
  sensor són 4,1 px de llenç a la Vixen i **6,1** a la Sony (×1,49).

Amb un sol tren cap d'aquestes tres coses no es podia distingir.
"""
from __future__ import annotations

import json
import os
import re

import numpy as np
from astropy.io import fits

RUNS = os.path.expanduser("~/Desktop/Eclipse determinista/1-RUNS")
PA = {"VIXEN": 57.194988546068025, "SONY": 90.27, "SONYTOT": 90.27}
ESC = {"VIXEN": 2.1494813525884373, "SONY": 3.2020, "SONYTOT": 3.2020}
GIR_ENTRE_SENSORS = PA["SONY"] - PA["VIXEN"]          # 33,075°


_PREFIX = re.compile(r"^(\d{3,})_")


def _num(d):
    m = _PREFIX.match(d)
    return int(m.group(1)) if m else -1


def darrer_run(tren: str, mode: str = "CIENCIA") -> str:
    """L'ultim run acabat d'un tren.

    ⏭️ 27-08: els runs es diuen `NNN_<TREN>_<MODE>_<segell>` amb NNN cronologic
    (comu.py). Aqui es treu el numero abans de comparar i s'ordena PER numero,
    que es el mateix que ordenar en el temps.
    """
    ds = [d for d in os.listdir(RUNS)
          if _PREFIX.sub("", d).startswith(f"{tren}_{mode}_")
          and not d.endswith(("_FALLIT", "_AVORTAT"))
          and os.path.exists(os.path.join(RUNS, d, "2-ldic", "CORONA_G.fits"))]
    if not ds:
        raise SystemExit(f"cap run acabat de {tren}")
    return os.path.join(RUNS, sorted(ds, key=lambda d: (_num(d), d))[-1])


def carrega(tren: str, quin: str = "CORONA", mode: str = "CIENCIA"):
    d = darrer_run(tren, mode)
    S = json.load(open(os.path.join(d, "4-rebuts", "F1.2_sol_llenc.json")))
    LL = S["llenc"]
    lum = None
    for c, w in (("R", 1.0), ("G", 2.0), ("B", 1.0)):
        a = fits.getdata(os.path.join(d, "2-ldic", f"{quin}_{c}.fits")).astype(np.float32)
        lum = a * np.float32(w / 4.0) if lum is None else lum + a * np.float32(w / 4.0)
    pes = fits.getdata(os.path.join(d, "2-ldic", "PES_G.fits")).astype(np.float32)
    return lum, pes, LL, S, d


def mostreja(img, cy, cx, R, radis, nth, ang0=0.0):
    th = np.linspace(0.0, 2 * np.pi, nth, endpoint=False) + ang0
    rr = np.asarray(radis, dtype=np.float64)[:, None] * R
    yy = cy + rr * np.sin(th)[None, :]
    xx = cx + rr * np.cos(th)[None, :]
    ny, nx = img.shape
    y0 = np.floor(yy).astype(np.int64); x0 = np.floor(xx).astype(np.int64)
    fy = yy - y0; fx = xx - x0
    ok = (y0 >= 0) & (x0 >= 0) & (y0 < ny - 1) & (x0 < nx - 1)
    y0c = np.clip(y0, 0, ny - 2); x0c = np.clip(x0, 0, nx - 2)
    v = (img[y0c, x0c] * (1 - fy) * (1 - fx) + img[y0c + 1, x0c] * fy * (1 - fx)
         + img[y0c, x0c + 1] * (1 - fy) * fx + img[y0c + 1, x0c + 1] * fy * fx)
    return np.where(ok, v, np.nan)


def estructura(pol, m):
    p = np.asarray(pol, dtype=np.float64).copy()
    p[~m] = np.nan
    med = np.nanmedian(p, axis=1, keepdims=True)
    mad = np.nanmedian(np.abs(p - med), axis=1, keepdims=True) * 1.4826
    return (p - med) / np.maximum(mad, 1e-12)


def corr(a, b, m, minim=200):
    out = np.full(a.shape[0], np.nan)
    for i in range(a.shape[0]):
        k = m[i] & np.isfinite(a[i]) & np.isfinite(b[i])
        if k.sum() < minim:
            continue
        u = a[i][k] - a[i][k].mean(); v = b[i][k] - b[i][k].mean()
        d = np.sqrt((u * u).sum() * (v * v).sum())
        if d > 0:
            out[i] = float((u * v).sum() / d)
    return out


def banda(e, lo, hi):
    F = np.fft.rfft(np.nan_to_num(e), axis=1)
    G = np.zeros_like(F); G[:, lo:hi + 1] = F[:, lo:hi + 1]
    return np.fft.irfft(G, n=e.shape[1], axis=1)


def a_la_resolucio(pol, radis, R_sol_altre, nth):
    """Desenfoca cada anell fins al pixel de l'altre instrument.

    Copiada de `auditoria_estructura/nucli.py` a proposit: les dues carpetes
    tenen un modul que es diu `nucli`, i importar-les creuades fa que la segona
    es trobi la primera a `sys.modules`. Vuit linies duplicades valen mes que
    una colisio de noms silenciosa.
    """
    from scipy.ndimage import gaussian_filter1d
    out = np.empty_like(pol)
    for i, r in enumerate(radis):
        sig = nth / (2.0 * np.pi * r * R_sol_altre) * 0.45
        out[i] = gaussian_filter1d(pol[i], max(sig, 0.3), mode="wrap")
    return out
