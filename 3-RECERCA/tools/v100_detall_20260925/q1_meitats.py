"""q1 (V100 detall, dada) · Hi ha detall REAL i reproduïble a la banda? Correlació del pas alt entre MEITATS INDEPENDENTS de fotogrames.
Entrada: dada/Q0_meitats_rampes.npz (q0: la d29 refeta per a 4 rampes; r1 = 1→2,5 = D29 exacta).
Mètode (res no es modifica: només es mesura):
  · ln G de cada meitat (verd post-matriu lineal).
  · Pas alt ISÒTROP: ln G − Gσ*ln G amb convolució normalitzada per la màscara de dada de la mateixa meitat (σ 1; 1,5; 2 px), mostrejat en polar.
  · Pas alt TANGENCIAL: ln G mostrejat en polar (θ cada 0,5 px d'arc, d cada 0,25 px; bilineal, només mostres amb els 4 veïns vàlids) i
    ln − G1D_σ(ln) al llarg de l'arc (σ en px d'arc). No veu cap perfil radial.
  · A cada fila (d fix) es treu la mitjana corrent al llarg de l'arc (±60 px): elimina el que és constant al llarg de l'arc (vora del domini,
    perfil radial residual), que les dues meitats compartirien sense ser detall.
  · Per sector i calaix: r de Pearson entre meitats (retall a 6 MAD), cov = variància del detall COMÚ, var(A−B)/2 = soroll per meitat,
    S/N per meitat = cov/(var(A−B)/2) i per a l'apilat sencer ≈ cov/(var(A−B)/4). NUL: la meitat A desplaçada ±20…40 px al llarg de l'arc.
  · Dues parelles de meitats: parells/senars (intercalades) i TA/TB (temporals: descarten un patró fix del sensor que camina amb la deriva).
Calaixos: d = distància al cercle de presentació (els de l'encàrrec), i també d_sil = d − e(PA) (distància a la vora real de la Lluna de presentació,
silueta d'ordre 2) i DREAL_MAX (el D_real més gran amb què algun fotograma veu el píxel).
Sortida: 4-RESULTATS/v100_detall_20260925/dada/Q1_MEITATS.json (+ Q1_resum.txt)."""
import json, sys
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter, gaussian_filter1d, map_coordinates, uniform_filter1d
ARREL = Path(__file__).resolve().parents[3]; O = ARREL / '4-RESULTATS/v100_detall_20260925/dada'; R9 = ARREL / '4-RESULTATS/v99_banda_20260925'
SORT = O / 'Q1_MEITATS.json'; assert not SORT.exists(), f'ja existeix {SORT}'
Z = np.load(O / 'Q0_meitats_rampes.npz'); idx = Z['idx']; by0, by1, bx0, bx1 = Z['box']; hb, wb = by1 - by0, bx1 - bx0; LX, LY, RL = Z['centre']
RAMPES = [tuple(r) for r in Z['rampes']]
S = np.load(R9 / 'D21_silueta_o2.npz'); pag, eg = S['pa'], S['e']
SECTORS = [(75, 105), (105, 135), (205, 235), (235, 255), (285, 345)]
BINS_D = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 6), (8, 20)]
BINS_SIL = [(0, 0.5), (0.5, 1), (1, 1.5), (1.5, 2), (2, 2.5), (2.5, 3), (3, 4), (4, 6), (8, 20)]
BINS_DX = [(1, 1.5), (1.5, 2), (2, 2.5), (2.5, 3), (3, 4), (4, 6), (6, 1e9)]
SIGMES = [1.0, 1.5, 2.0]; PARELLES = [('parells', 'senars'), ('TA', 'TB')]
SHIFTS = [s for s in range(20, 41, 2)] + [-s for s in range(20, 41, 2)]
# graella polar
DA = 0.5; NT = int(round(2 * np.pi * RL / DA)); TH = np.arange(NT) * 360.0 / NT; DD = np.arange(-3.0, 25.0001, 0.25); ND = DD.size
rr = RL + DD[:, None]; XP = LX + rr * np.cos(np.radians(TH))[None, :]; YP = LY - rr * np.sin(np.radians(TH))[None, :]
CO = np.array([YP - by0, XP - bx0]); ARC = DA * (RL + DD) / RL          # px d'arc per mostra a cada fila
EP = np.interp(TH, pag, eg, period=360)[None, :] * np.ones((ND, 1)); DSIL = DD[:, None] - EP; DP = DD[:, None] * np.ones((1, NT))
def a2d(v, fill=np.nan):
    a = np.full(hb * wb, fill, np.float64); a[idx] = v; return a.reshape(hb, wb)
def polar(img, order=1): return map_coordinates(img, CO, order=order, mode='constant', cval=0.0)
def treu_lent(P, V):
    """treu la mitjana corrent al llarg de l'arc (±60 px) a cada fila, sobre les mostres vàlides"""
    out = np.array(P);
    for i in range(ND):
        n = int(round(120 / ARC[i])) | 1; a = uniform_filter1d(np.where(V[i], P[i], 0), n, mode='wrap'); b = uniform_filter1d(V[i].astype(float), n, mode='wrap')
        out[i] = np.where(V[i] & (b > 0.2), P[i] - a / np.maximum(b, 1e-9), np.nan)
    return out
def hp_meitat(G, sig, tipus):
    m = np.isfinite(G) & (G > 0); L = np.where(m, np.log(np.where(m, G, 1)), 0.0)
    if tipus == 'iso':
        num = gaussian_filter(L * m, sig, truncate=4); den = gaussian_filter(m.astype(float), sig, truncate=4)
        H = np.where(m & (den > 0.2), L - num / np.maximum(den, 1e-9), 0.0); mm = (m & (den > 0.2)).astype(float)
        ms = polar(mm); V = ms > 0.999; P = np.where(V, polar(H * mm), np.nan)
    else:
        ms = polar(m.astype(float)); V = ms > 0.999; Lp = np.where(V, polar(L * m), 0.0); P = np.full((ND, NT), np.nan)
        for i in range(ND):
            s_ = sig / ARC[i]; a = gaussian_filter1d(Lp[i] * V[i], s_, mode='wrap', truncate=4); b = gaussian_filter1d(V[i].astype(float), s_, mode='wrap', truncate=4)
            P[i] = np.where(V[i] & (b > 0.2), Lp[i] - a / np.maximum(b, 1e-9), np.nan)
        V = np.isfinite(P)
    P = treu_lent(P, V); return P
def stats(a, b):
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 50: return None
    a, b = a[ok], b[ok]
    ma, mb = np.median(a), np.median(b); sa, sb = 1.4826 * np.median(np.abs(a - ma)), 1.4826 * np.median(np.abs(b - mb))
    k = (np.abs(a - ma) < 6 * sa) & (np.abs(b - mb) < 6 * sb); a, b = a[k] - a[k].mean(), b[k] - b[k].mean()
    if a.size < 50: return None
    cov = float(np.mean(a * b)); vd = float(np.var(a - b)) / 2; r = float(cov / np.sqrt(np.mean(a * a) * np.mean(b * b)))
    return dict(n=int(a.size), r=r, cov=cov, soroll_meitat=vd, sn_meitat=cov / vd if vd > 0 else None, sn_apilat=2 * cov / vd if vd > 0 else None,
                rms_detall_pc=100 * float(np.sqrt(max(cov, 0))), rms_soroll_apilat_pc=100 * float(np.sqrt(vd / 2)))
def nul(PA_, PB_, sel):
    rs = []
    for s in SHIFTS:
        k = int(round(s / DA)); A2 = np.roll(PA_, -k, axis=1); st = stats(A2[sel], PB_[sel])
        if st: rs.append(st['r'])
    rs = np.array(rs); return dict(r_mitjana=float(rs.mean()), r_sd=float(rs.std()), r_max_abs=float(np.abs(rs).max()), n=int(rs.size)) if rs.size else None
res = dict(metode=__doc__, graella=dict(DA_px=DA, NT=NT, Dd_px=0.25, d=[float(DD[0]), float(DD[-1])]), shifts_px=SHIFTS, sectors=SECTORS, resultats=[])
DXp = {r: polar(np.nan_to_num(a2d(Z[f'DX_r{r}']), nan=-99), order=0) for r in range(len(RAMPES))}
for r, (LO, HI) in enumerate(RAMPES):
    for pa_, pb_ in PARELLES:
        GA = a2d(Z[f'G_{pa_}_r{r}']); GB = a2d(Z[f'G_{pb_}_r{r}'])
        for tipus in ('iso', 'tan'):
            for sig in SIGMES:
                if r != 1 and not (sig == 1.5): continue          # rampes alternatives: només σ 1,5 (Q2)
                PA_, PB_ = hp_meitat(GA, sig, tipus), hp_meitat(GB, sig, tipus)
                for a0, a1 in SECTORS:
                    zs = (TH >= a0) & (TH < a1)
                    for nom, bins, var in (('d', BINS_D, DP), ('d_sil', BINS_SIL, DSIL), ('DREAL_MAX', BINS_DX, DXp[r])):
                        if nom != 'd' and not (r == 1 or nom == 'DREAL_MAX'): continue
                        for b0, b1 in bins:
                            sel = zs[None, :] & (var >= b0) & (var < b1); st = stats(PA_[sel], PB_[sel])
                            if st is None: continue
                            st['nul'] = nul(PA_, PB_, sel)
                            if st['nul']: st['z'] = (st['r'] - st['nul']['r_mitjana']) / max(st['nul']['r_sd'], 1e-6)
                            res['resultats'].append(dict(rampa=[LO, HI], meitats=f'{pa_}/{pb_}', hp=tipus, sigma=sig, sector=[a0, a1], calaix=nom, rang=[b0, b1], **st))
                print(f'r{r} {pa_}/{pb_} {tipus} σ{sig}', flush=True)
SORT.write_text(json.dumps(res, indent=1, ensure_ascii=False))
# resum llegible
L = []
def fila(x): n = x['nul'] or dict(r_mitjana=float('nan'), r_sd=float('nan')); return (f"{x['rang'][0]:>4}-{x['rang'][1]:<4} n{x['n']:>6} r {x['r']:+.3f} (nul {n['r_mitjana']:+.3f}±{n['r_sd']:.3f}, z {x.get('z', 0):5.1f}) "
                                  f"detall {x['rms_detall_pc']:.2f} % soroll/apilat {x['rms_soroll_apilat_pc']:.2f} % S/N_apilat {x['sn_apilat']:.2f}")
for x in res['resultats']:
    L.append(f"r{x['rampa']} {x['meitats']} {x['hp']} σ{x['sigma']} PA{x['sector']} {x['calaix']}: " + fila(x))
(O / 'Q1_resum.txt').write_text('\n'.join(L)); print('fet', SORT)
