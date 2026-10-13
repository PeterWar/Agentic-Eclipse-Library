"""lasco_vista · Visualització d'una imatge LASCO de nivell 0,5 sense fons mensual.
En un desplegat polar (r logarítmic, PA a 0,25°), a cada radi:
  1. log10 de la intensitat (DN/s);
  2. es treuen els harmònics m = 0 … mmax en angle (2 al C2, 4 al C3), ajustats de forma robusta fora del pilar: hi viuen la corona F (llum
     zodiacal, allargada al llarg de l'eclíptica), la llum difusa de l'instrument i el gradient general;
  3. el residu es divideix per la seva dispersió robusta.
Queden els serpentins i els raigs (escales d'angle < ~60°). És una vista, no una mesura: per a les mesures, c2/c3."""
import numpy as np
from scipy import ndimage as nd
from astropy.io import fits
from comu_comp import carrega_lasco, DADES

class VistaLasco:
    def __init__(s, fitxer, rmin, rmax, pilar=(290.0, 355.0), nr=520, dpa=0.25, suau_r=1.0, mmax=2, prepara=None):
        d, g, hd = carrega_lasco(fitxer)
        if hd['detector'] == 'C2':                       # vinyetatge del C2 (SolarSoft, multiplicatiu)
            d = d * fits.open(DADES / 'lasco_calib/c2vig_final.fts')[0].data.astype(np.float32)
        if prepara is not None:                          # p. ex. taques fosques del detector (c11); per defecte, res
            d = prepara(d, g)
        s.g, s.hd, s.rmin, s.rmax, s.dpa = g, hd, rmin, rmax, dpa
        s.lr = np.linspace(np.log10(rmin), np.log10(rmax), nr); s.pa = np.arange(0, 360, dpa)
        RR, PP = np.meshgrid(10 ** s.lr, s.pa, indexing='ij')
        x, y = g.px(RR, PP)
        bo = (d > 0).astype(np.float32)
        if hd['detector'] == 'C3':
            mk = fits.open(DADES / 'lasco_calib/c3clearmask2.fts')[0].data
            bo *= (mk > 0)
        v = nd.map_coordinates(np.log10(np.clip(d, 1e-3, None)), [y, x], order=1, mode='constant', cval=np.nan)
        b = nd.map_coordinates(bo, [y, x], order=1, mode='constant', cval=0) > 0.99
        v[~b] = np.nan
        th = np.radians(s.pa)
        X = np.stack([np.ones_like(th)] + [f(m * th) for m in range(1, mmax + 1) for f in (np.cos, np.sin)], 1)
        fora_pilar = ~((s.pa >= pilar[0]) & (s.pa <= pilar[1]))
        Z = np.full(v.shape, np.nan, np.float32); sig = np.full(nr, np.nan)
        for i in range(nr):
            row = v[i]; m = np.isfinite(row) & fora_pilar
            if m.sum() < 200: continue
            w = m.copy()
            for _ in range(4):                       # ajust robust: retalla el que s'aparta > 2,5 σ (serpentins brillants)
                c, *_ = np.linalg.lstsq(X[w], row[w], rcond=None); res = row - X @ c
                sd = 1.4826 * np.nanmedian(np.abs(res[w])); w = m & (np.abs(res) < 2.5 * sd)
            Z[i] = res; sig[i] = 1.4826 * np.nanmedian(np.abs(res[m]))
        ok = np.isfinite(sig); sig_s = np.interp(np.arange(nr), np.nonzero(ok)[0], nd.median_filter(sig[ok], 9))
        Z = Z / sig_s[:, None]
        if suau_r > 0:
            zz = np.nan_to_num(Z); ww = np.isfinite(Z).astype(float)
            Z = np.where(np.isfinite(Z), nd.gaussian_filter1d(zz, suau_r, 0) / np.maximum(nd.gaussian_filter1d(ww, suau_r, 0), 1e-6), np.nan)
        s.Z = Z

    def mostra(s, r, pa):
        """Valor de la vista (en σ) a (r R☉, PA°); NaN fora del camp."""
        ir = (np.log10(np.clip(r, 1e-6, None)) - s.lr[0]) / (s.lr[1] - s.lr[0])
        ip = (np.asarray(pa) % 360) / s.dpa
        Zp = np.concatenate([s.Z, s.Z[:, :2]], 1)          # volta en angle
        out = nd.map_coordinates(Zp, [ir, ip], order=1, mode='constant', cval=np.nan)
        out[(r < s.rmin) | (r > s.rmax)] = np.nan
        return out
