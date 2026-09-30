"""vn3 (V108 · verificador de «negres») · A la FONT (linealitzada E + franja, la mateixa entrada de l'E1): és cel o és corona el que la NRGF
normalitza a 3–8 R☉? Prova independent del model de l'agent: harmònics azimutals (m = 1, 2) del perfil de cada anell en funció del radi.
  · un gradient de CEL llis (pla) dona un 1r harmònic d'amplitud ∝ r (creix cap enfora) i fase constant;
  · l'estructura CORONAL gran (serpentines, corona F) decau cap enfora (∝ r^-2…-3) i la seva fase segueix els plomalls.
També: σ de l'anell, σ sense el pla/2n grau (ajust propi, robust, a 6,5–8,4 R☉), i la z que hi posa la NRGF a 90° i 225° (7 R☉).
I quina part de la variància azimutal d'escala gran (> 30°) a 3–4,5 R☉ és el model de cel de 2n grau que la cura treu (risc de treure corona).
Sortida: 4-RESULTATS/v108_20260926/verifica_negres/VN3.json"""
import sys, os, json
from pathlib import Path
import numpy as np, cv2
from scipy.ndimage import gaussian_filter1d
R0 = Path(__file__).resolve().parents[4]
FONTS = R0 / '4-RESULTATS/v103_banda_20260926/E/lineal_v103'; FR = R0 / '4-RESULTATS/v103_banda_20260926/E/lineal_v103_franja/A3C_franja_silueta.npz'
H, W = 7506, 10551; CX, CY, RS = 5361.768111973117, 3775.747534140857, 440.60304883027544
a = np.load(FONTS / 'base_G.npy').astype(np.float32); m = np.load(FONTS / 'support.npy') & np.isfinite(a) & (a > 0)
Q = np.load(FR); qy0, qy1, qx0, qx1 = [int(v) for v in Q['box']]; a[qy0:qy1, qx0:qx1] = Q['G']; m[qy0:qy1, qx0:qx1] = Q['domini'] & (Q['G'] > 0); a = np.nan_to_num(a)
res = {}
# ajust propi del cel (robust, Huber-ish per iteració) a 6,5–8,4 R☉, submostreig 5 px (diferent del de l'agent: 4 px, 2,5σ)
yy, xx = np.mgrid[0:H:5, 0:W:5]; rs = np.hypot(xx - CX, yy - CY) / RS; sel = m[::5, ::5] & (rs > 6.5) & (rs < 8.4)
X = (xx[sel] - CX) / 4000; Y = (yy[sel] - CY) / 4000; b = a[::5, ::5][sel].astype(np.float64)
fits = {}
for nom, k in (('pla', 3), ('quad', 6)):
    A_ = np.stack([np.ones_like(X), X, Y, X * X, X * Y, Y * Y], 1)[:, :k]; w = np.ones_like(b)
    for _ in range(6):
        cf = np.linalg.lstsq(A_ * w[:, None], b * w, rcond=None)[0]; rr = b - A_ @ cf; s = 1.4826 * np.median(np.abs(rr)); w = np.where(np.abs(rr) < 2 * s, 1, 2 * s / np.abs(rr))
    fits[nom] = cf; res[f'cel_{nom}'] = dict(coef=cf.tolist(), residu_mad=float(s))
res['cobertura_cel_6.5-8.4_per_sector_30'] = {}
th_s = np.degrees(np.arctan2(-(yy - CY), xx - CX)) % 360; ring = (rs > 6.5) & (rs < 8.4)
for s0 in range(0, 360, 30):
    k = ring & (th_s >= s0) & (th_s < s0 + 30); res['cobertura_cel_6.5-8.4_per_sector_30'][f'{s0}'] = float((m[::5, ::5] & k).sum() / max(k.sum(), 1))
del yy, xx, rs, sel, X, Y, b, th_s, ring
# perfils azimutals per anells (gruix 0,1 R☉) amb mostreig polar
out = []
def cel_eval(cf, x, y):
    X = (x - CX) / 4000; Y = (y - CY) / 4000; c = np.r_[cf, np.zeros(6 - len(cf))]
    return c[0] + c[1] * X + c[2] * Y + c[3] * X * X + c[4] * X * Y + c[5] * Y * Y
NT = 720; t = np.radians((np.arange(NT) + 0.5) * 360 / NT)
for r_ in np.r_[np.arange(1.5, 3, 0.5), np.arange(3, 8.45, 0.25)]:
    rr = np.arange(r_ * RS, (r_ + 0.1) * RS, 2.0)
    Xp = (CX + np.cos(t)[None, :] * rr[:, None]).astype(np.float32); Yp = (CY - np.sin(t)[None, :] * rr[:, None]).astype(np.float32)
    v = cv2.remap(a, Xp, Yp, cv2.INTER_LINEAR, borderValue=0); mv = cv2.remap(m.astype(np.float32), Xp, Yp, cv2.INTER_LINEAR, borderValue=0) > 0.999
    cob = mv.any(0); prof = np.where(cob, np.nanmean(np.where(mv, v, np.nan), 0), np.nan)
    ok = np.isfinite(prof); f = ok.mean()
    d = dict(r=float(r_), cobertura=float(f))
    if f < 0.6: out.append(d); continue
    ang = t[ok]; p = prof[ok]
    Am = np.stack([np.ones_like(ang), np.cos(ang), np.sin(ang), np.cos(2 * ang), np.sin(2 * ang)], 1); c = np.linalg.lstsq(Am, p, rcond=None)[0]
    d.update(mitjana=float(c[0]), A1=float(np.hypot(c[1], c[2])), fase1=float(np.degrees(np.arctan2(c[2], c[1])) % 360), A2=float(np.hypot(c[3], c[4])),
             sigma_perfil=float(p.std()))
    for nom, cf in fits.items():
        S = cel_eval(cf, Xp.mean(0)[ok], Yp.mean(0)[ok]); ps = p - (S - S.mean())
        d[f'sigma_sense_cel_{nom}'] = float(ps.std())
        # variància d'escala gran (> 30°) del perfil i la part que és el model de cel
        lp = gaussian_filter1d(np.interp(np.arange(NT), np.flatnonzero(ok), p, period=NT), NT / 12 / 2.355, mode='wrap')[ok]
        d[f'var_gran_explicada_cel_{nom}'] = float(1 - np.var(lp - (S - S.mean())) / np.var(lp))
        d[f'ampl_cel_{nom}_sobre_sigma'] = float((S - S.mean()).std() / p.std())
    # z de la NRGF (μ, σ de l'anell) a 90° i 225°
    for ang_ in (90, 225):
        i = int(ang_ / 360 * NT);
        if ok[i]: d[f'z_{ang_}'] = float((prof[i] - p.mean()) / p.std())
    out.append(d)
res['anells'] = out
(R0 / '4-RESULTATS/v108_20260926/verifica_negres/VN3.json').write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
for d in out:
    print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in d.items()})
