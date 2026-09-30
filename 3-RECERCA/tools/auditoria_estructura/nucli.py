"""Nucli de l'auditoria d'ESTRUCTURA contra els composts de Brno.

La comparació no és de color ni de nivell: es normalitza CADA ANELL (resta de
la mediana azimutal i divisió per la dispersió) als dos costats, de manera que
qualsevol corba de to monòtona i qualsevol guany global desapareixen. El que
queda és la forma de la corona, i és directament comparable.

⛔ Cap retall circular: la comparació s'atura només on un dels dos no té dada.
"""
from __future__ import annotations

import json
import os

import numpy as np
from PIL import Image

BRNO_DIR = "/Users/USUARI/Desktop/Eclipse 2026/Drukmuller fotos finals"
AQUI = os.path.dirname(os.path.abspath(__file__))
GEO_BRNO = os.path.join(AQUI, "..", "estudi_druckmuller", "geometria.json")

# ⏭️ El registre vàlid és el JUTJAT A ESCALA FINA (`registra2.py`). El primer
#    (`registre.json`) maximitzava la correlació de l'estructura sencera, que la
#    manen els harmònics baixos, i deixava l'escala mal determinada.
REGISTRE = ("registre2.json" if os.path.exists(os.path.join(AQUI, "registre2.json"))
            else "registre.json")

# el nostre llenç (F1.2 del run): Sol per efemèride, nord amunt
RUN = os.path.expanduser(
    (__import__("glob").glob(os.path.expanduser("~/Desktop/Eclipse determinista/1-RUNS/*20260827T012038Z*")) + [""])[0] + "")


def srgb_a_lineal(c):
    c = np.asarray(c, dtype=np.float64)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def carrega_brno(nom):
    """Retorna (lluminància lineal, cy, cx, R_lluna_px) del contingut retallat.

    ⚠️ (cy, cx) és el centre de la LLUNA, no del Sol: als composts de Brno el
    disc lunar és d'UN instant i està desplaçat del Sol fins a 0,065 R☉.
    """
    with open(GEO_BRNO) as fh:
        g = json.load(fh)[nom]
    im = Image.open(os.path.join(BRNO_DIR, nom)).convert("RGB")
    rgb = srgb_a_lineal(np.asarray(im, dtype=np.float64) / 255.0)
    f0, f1, c0, c1 = g["marc"]
    sub = rgb[f0:f1, c0:c1]
    lum = (sub[..., 0] + 2.0 * sub[..., 1] + sub[..., 2]) / 4.0
    # ⛔ Els quatre composts porten un PEU DE FOTO d'unes 29 files al capdavall
    #    del contingut: files planes que, mostrejades com si fossin corona,
    #    hi posen estructura que no hi és (toca els anells de r ≳ 3,2 R☉).
    sd = lum.std(axis=1)
    pla = sd < 0.02 * sd.max()
    tall = lum.shape[0]
    while tall > 0 and pla[tall - 1]:
        tall -= 1
    lum = lum.copy()
    lum[tall:] = np.nan
    return lum, g["cy"], g["cx"], g["R_lluna_px"]


def carrega_nostre(run=RUN, quin="CORONA"):
    """Lluminància LINEAL del compost, i la geometria del llenç."""
    from astropy.io import fits
    S = json.load(open(os.path.join(run, "4-rebuts", "F1.2_sol_llenc.json")))
    LL = S["llenc"]
    lum = None
    for c, w in (("R", 1.0), ("G", 2.0), ("B", 1.0)):
        a = fits.getdata(os.path.join(run, "2-ldic", f"{quin}_{c}.fits")).astype(np.float32)
        lum = a * np.float32(w / 4.0) if lum is None else lum + a * np.float32(w / 4.0)
    pes = fits.getdata(os.path.join(run, "2-ldic", "PES_G.fits")).astype(np.float32)
    return lum, pes, LL, S


def mostreja(img, cy, cx, R, radis, nth, ang0=0.0, val_fora=np.nan):
    """Mostreig bilineal d'anells. `radis` en R☉; angle mesurat des de l'eix +x
    (dreta) cap avall a la imatge, o sigui el mateix conveni als dos costats.
    `ang0` gira el mostreig (radiants)."""
    th = np.linspace(0.0, 2.0 * np.pi, nth, endpoint=False) + ang0
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
    return np.where(ok, v, val_fora)


def estructura(pol, sigma_min=1e-9):
    """Normalitza cada anell: (x − mediana) / MAD. Mata to i guany."""
    p = np.asarray(pol, dtype=np.float64)
    med = np.nanmedian(p, axis=1, keepdims=True)
    mad = np.nanmedian(np.abs(p - med), axis=1, keepdims=True) * 1.4826
    return (p - med) / np.maximum(mad, sigma_min)


def corr_per_anell(a, b):
    """Pearson anell a anell, ignorant NaN."""
    out = np.full(a.shape[0], np.nan)
    for i in range(a.shape[0]):
        u, v = a[i], b[i]
        m = np.isfinite(u) & np.isfinite(v)
        if m.sum() < 32:
            continue
        u = u[m] - u[m].mean(); v = v[m] - v[m].mean()
        d = np.sqrt((u * u).sum() * (v * v).sum())
        if d > 0:
            out[i] = float((u * v).sum() / d)
    return out


# ---------------------------------------------------------- validesa de Brno

GUARDA_LLUNA_BRNO = 0.012   # R☉ de guarda sobre la vora del seu disc pintat


def mascara_brno(nom, reg, radis, nth, guarda=GUARDA_LLUNA_BRNO):
    """0 dins del disc lunar PINTAT de Brno (i la seva vora), 1 fora.

    ⛔ Sense això la comparació correlaciona la nostra corona contra un disc
    negre constant: a 1,04-1,09 R☉ el seu anell és mig Lluna, la dispersió
    azimutal se'n va a zero i en surt una «anticorrelació» que no és cap
    mesura. Aquest va ser el meu primer error d'aquesta auditoria.
    """
    import json as _j
    g = _j.load(open(GEO_BRNO))[nom]
    Rs = reg["R_sol_px"]
    # centre de la Lluna respecte del centre SOLAR que hem registrat, girat
    # com el mostreig (que ja aplica reg["gir_deg"])
    a = np.deg2rad(reg["gir_deg"])
    dx = g["cx"] - reg["cx"]; dy = g["cy"] - reg["cy"]
    mx = (dx * np.cos(a) + dy * np.sin(a)) / Rs
    my = (-dx * np.sin(a) + dy * np.cos(a)) / Rs
    th = np.linspace(0.0, 2 * np.pi, nth, endpoint=False)
    xx = np.asarray(radis)[:, None] * np.cos(th)[None, :]
    yy = np.asarray(radis)[:, None] * np.sin(th)[None, :]
    return np.hypot(xx - mx, yy - my) > (g["R_lluna_px"] / Rs + guarda)


def corr_per_anell_mask(a, b, m, minim=180):
    """Pearson anell a anell només on la màscara diu que hi ha corona als DOS."""
    out = np.full(a.shape[0], np.nan)
    n = np.zeros(a.shape[0], int)
    for i in range(a.shape[0]):
        k = m[i] & np.isfinite(a[i]) & np.isfinite(b[i])
        n[i] = k.sum()
        if n[i] < minim:
            continue
        u = a[i][k] - a[i][k].mean(); v = b[i][k] - b[i][k].mean()
        d = np.sqrt((u * u).sum() * (v * v).sum())
        if d > 0:
            out[i] = float((u * v).sum() / d)
    return out, n


def estructura_mask(pol, m):
    """Normalitza cada anell amb NOMÉS els píxels vàlids."""
    p = np.asarray(pol, dtype=np.float64).copy()
    p[~m] = np.nan
    med = np.nanmedian(p, axis=1, keepdims=True)
    mad = np.nanmedian(np.abs(p - med), axis=1, keepdims=True) * 1.4826
    return (p - med) / np.maximum(mad, 1e-12)
