"""d34 (V100 detall) · Corroboració INDEPENDENT del detall de la banda: CONTINUÏTAT RADIAL. Els raigs de la corona són radials i llargs: el detall
TANGENCIAL (al llarg de l'arc) d'una fila de la banda (d 1–3,5 px) ha de coincidir amb el de la dada NETA de la V99 al mateix angle a d 5–8 px
(dada diferent: fotogrames amb D_real ≥ 4–6,5). El soroll, un error de T (constant al llarg de l'arc) o la barreja de classes no hi
correlacionen. Nul: la mateixa correlació amb un desplaçament de 15–40 px al llarg de l'arc.
Detall tangencial: ln X remostrejat en polar (dr 0,25 px, ds 0,5 px d'arc), menys la seva mitjana gaussiana al llarg de l'arc (σ = SIG px), amb
convolució normalitzada pels vàlids. Fonts: banda = D29 (G, G_parells, G_senars); neta = V99 lineal (4-RESULTATS/v99_banda_20260925/B/lineal_v99/base_G.npy)
només on la V99 té domini. Ús: d34_continuitat_radial.py [SIG]"""
import json, sys
from pathlib import Path
import numpy as np, cv2
from scipy.ndimage import gaussian_filter1d
ARREL = Path(__file__).resolve().parents[3]; O = ARREL / '4-RESULTATS/v100_detall_20260925'; R9 = ARREL / '4-RESULTATS/v99_banda_20260925/B'
SIG = float(sys.argv[1]) if len(sys.argv) > 1 else 4.0
Z = np.load(O / 'D29_candidat_banda.npz'); by0, by1, bx0, bx1 = [int(v) for v in Z['box']]; LX, LY, RL = [float(v) for v in Z['centre']]
Q9 = np.load(R9 / 'lineal_v99_franja/A3C_franja_silueta.npz'); dom9 = np.asarray(Q9['domini_E']); assert list(Q9['box']) == [by0, by1, bx0, bx1]
G9 = np.asarray(np.load(R9 / 'lineal_v99/base_G.npy', mmap_mode='r')[by0:by1, bx0:bx1], np.float32)
NF = Z['NF']
def polar(img, valid, r0, r1, dr=0.25, ds=0.5):
    rr = np.arange(r0, r1, dr); nth = int(2 * np.pi * RL / ds); tt = np.arange(nth) * 2 * np.pi / nth
    R_, T_ = np.meshgrid(RL + rr, tt, indexing='ij'); mx = (LX + R_ * np.cos(T_) - bx0).astype(np.float32); my = (LY - R_ * np.sin(T_) - by0).astype(np.float32)
    v = cv2.remap(np.where(valid, img, 0).astype(np.float32), mx, my, cv2.INTER_LINEAR); w = cv2.remap(valid.astype(np.float32), mx, my, cv2.INTER_LINEAR)
    return rr, np.degrees(tt), np.where(w > 0.99, v / np.maximum(w, 1e-6), np.nan)
def hp_tang(P):
    ok = np.isfinite(P); x = np.where(ok, np.log(np.maximum(P, 1e-30)), 0); w = ok.astype(np.float64); s = SIG / 0.5
    m = gaussian_filter1d(x * w, s, axis=1, mode='wrap') / np.maximum(gaussian_filter1d(w, s, axis=1, mode='wrap'), 1e-6); return np.where(ok, x - m, np.nan)
valid_b = (Z['G'] > 0) & (NF >= 3)
rr, thd, Pb = polar(Z['G'], valid_b, 0.5, 9.0); _, _, Pp = polar(Z['G_parells'], valid_b & (Z['G_parells'] > 0), 0.5, 9.0); _, _, Ps = polar(Z['G_senars'], valid_b & (Z['G_senars'] > 0), 0.5, 9.0)
rr9, _, P9 = polar(G9, dom9 & (G9 > 0), 4.0, 12.0)
Hb, Hp, Hs, H9 = hp_tang(Pb), hp_tang(Pp), hp_tang(Ps), hp_tang(P9)
def corr(a, b):
    ok = np.isfinite(a) & np.isfinite(b)
    return (float(np.corrcoef(a[ok], b[ok])[0, 1]), int(ok.sum())) if ok.sum() > 200 else (None, int(ok.sum()))
ref9 = np.nanmean(H9[(rr9 >= 5) & (rr9 < 8)], axis=0)      # detall tangencial net mitjà a 5–8 px (per angle)
rep = dict(sigma_arc_px=SIG, sectors={})
for a0, a1 in ((75, 105), (105, 135), (135, 165), (205, 235), (235, 255), (285, 345)):
    sel = ((thd - a0) % 360) < ((a1 - a0) % 360); r = {}
    for lo, hi in ((0.5, 1.5), (1.5, 2.5), (2.5, 3.5), (3.5, 5.0), (5.0, 8.0)):
        rows = (rr >= lo) & (rr < hi); band = np.nanmean(Hb[rows], axis=0); bp = np.nanmean(Hp[rows], axis=0); bs = np.nanmean(Hs[rows], axis=0)
        c_cont = corr(band[sel], ref9[sel]); nul = [corr(np.roll(band, k)[sel], ref9[sel])[0] for k in (30, 50, 70, -40, -60)]
        c_halves = corr(bp[sel], bs[sel]); nulh = [corr(np.roll(bp, k)[sel], bs[sel])[0] for k in (30, 50, -40)]
        r[f'{lo}-{hi}'] = dict(continuitat_amb_neta_5_8=c_cont[0], n=c_cont[1], nul_continuitat=[None if v is None else round(v, 3) for v in nul],
                               meitats=c_halves[0], nul_meitats=[None if v is None else round(v, 3) for v in nulh], amplitud_rms=float(np.nanstd(band[sel])) if np.isfinite(band[sel]).sum() > 50 else None)
    rep['sectors'][f'{a0}-{a1}'] = r
    print(f'{a0}-{a1}', ' | '.join(f"{k}: cont {v['continuitat_amb_neta_5_8'] if v['continuitat_amb_neta_5_8'] is None else round(v['continuitat_amb_neta_5_8'],2)} (nul {max(abs(x) for x in v['nul_continuitat'] if x is not None) if any(x is not None for x in v['nul_continuitat']) else None}) meit {None if v['meitats'] is None else round(v['meitats'],2)}" for k, v in r.items()))
(O / f'D34_CONTINUITAT_RADIAL_s{SIG:g}.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
