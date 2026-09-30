"""q1c (V100 detall, dada) · El detall reproduïble de la banda per ESCALES més grans (rajos, no gra): pas de banda TANGENCIAL.
Com q1, però en lloc del pas alt de σ 1–2 px es mira el pas de banda al llarg de l'arc: ln G suavitzat amb σ_s menys suavitzat amb 3·σ_s
(σ_s = 1,5; 3; 5; 8 px d'arc), sobre ln G mostrejat en polar (0,5 px d'arc × 0,25 px de d). Nul: meitat A desplaçada 3·σ_gran … 6·σ_gran px
(mínim 20–40 px). A més, CONTINUÏTAT RADIAL: correlació, columna a columna (mateix PA), entre el pas de banda de la meitat A a cada calaix
de la banda i la mitjana del de la meitat B a d 8–12 px (on hi ha dada neta): els rajos reals són radials i han de continuar; el soroll no.
Només es mesura; res no es modifica. Sortida: 4-RESULTATS/v100_detall_20260925/dada/Q1C_ESCALES.json i Q1C_resum.txt."""
import json
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter1d, map_coordinates, uniform_filter1d
ARREL = Path(__file__).resolve().parents[3]; O = ARREL / '4-RESULTATS/v100_detall_20260925/dada'
SORT = O / 'Q1C_ESCALES.json'; assert not SORT.exists()
Z = np.load(O / 'Q0_meitats_rampes.npz'); idx = Z['idx']; by0, by1, bx0, bx1 = Z['box']; hb, wb = by1 - by0, bx1 - bx0; LX, LY, RL = Z['centre']
RAMPES = [tuple(r) for r in Z['rampes']]
SECTORS = [(75, 105), (105, 135), (205, 235), (235, 255), (285, 345)]
BINS_D = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 6), (8, 20)]; BINS_DX = [(1, 2), (2, 3), (3, 4), (4, 6), (6, 1e9)]
ESCALES = [1.5, 3.0, 5.0, 8.0]; PARELLES = [('parells', 'senars'), ('TA', 'TB')]
DA = 0.5; NT = int(round(2 * np.pi * RL / DA)); TH = np.arange(NT) * 360.0 / NT; DD = np.arange(-3.0, 25.0001, 0.25); ND = DD.size
rr = RL + DD[:, None]; CO = np.array([LY - rr * np.sin(np.radians(TH))[None, :] - by0, LX + rr * np.cos(np.radians(TH))[None, :] - bx0])
ARC = DA * (RL + DD) / RL; DP = DD[:, None] * np.ones((1, NT)); REF = (DD >= 8) & (DD < 12)
def a2d(v, fill=np.nan): a = np.full(hb * wb, fill, np.float64); a[idx] = v; return a.reshape(hb, wb)
def polar(img, order=1): return map_coordinates(img, CO, order=order, mode='constant', cval=0.0)
def bp_meitat(G, s):
    m = np.isfinite(G) & (G > 0); L = np.where(m, np.log(np.where(m, G, 1)), 0.0)
    V = polar(m.astype(float)) > 0.999; Lp = np.where(V, polar(L * m), 0.0); P = np.full((ND, NT), np.nan)
    for i in range(ND):
        a1 = gaussian_filter1d(Lp[i] * V[i], s / ARC[i], mode='wrap', truncate=4); b1 = gaussian_filter1d(V[i] * 1.0, s / ARC[i], mode='wrap', truncate=4)
        a3 = gaussian_filter1d(Lp[i] * V[i], 3 * s / ARC[i], mode='wrap', truncate=4); b3 = gaussian_filter1d(V[i] * 1.0, 3 * s / ARC[i], mode='wrap', truncate=4)
        ok = V[i] & (b1 > 0.5) & (b3 > 0.5); p = np.where(ok, a1 / np.maximum(b1, 1e-9) - a3 / np.maximum(b3, 1e-9), np.nan)
        n = int(round(max(120, 12 * s) / ARC[i])) | 1; vv = np.isfinite(p)
        mu = uniform_filter1d(np.where(vv, p, 0), n, mode='wrap') / np.maximum(uniform_filter1d(vv * 1.0, n, mode='wrap'), 1e-9)
        P[i] = np.where(vv, p - mu, np.nan)
    return P
def stats(a, b):
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 50: return None
    a, b = a[ok], b[ok]; ma, mb = np.median(a), np.median(b); sa, sb = 1.4826 * np.median(np.abs(a - ma)), 1.4826 * np.median(np.abs(b - mb))
    k = (np.abs(a - ma) < 6 * sa) & (np.abs(b - mb) < 6 * sb); a, b = a[k] - a[k].mean(), b[k] - b[k].mean()
    if a.size < 50: return None
    cov = float(np.mean(a * b)); vd = float(np.var(a - b)) / 2; r = float(cov / np.sqrt(np.mean(a * a) * np.mean(b * b)))
    return dict(n=int(a.size), r=r, rms_detall_pc=100 * float(np.sqrt(max(cov, 0))), rms_soroll_apilat_pc=100 * float(np.sqrt(vd / 2)), sn_apilat=2 * cov / vd if vd > 0 else None)
res = dict(metode=__doc__, resultats=[])
DXp = {r: polar(np.nan_to_num(a2d(Z[f'DX_r{r}']), nan=-99), order=0) for r in range(len(RAMPES))}
for r in (1, 3):
    for pa_, pb_ in PARELLES:
        GA, GB = a2d(Z[f'G_{pa_}_r{r}']), a2d(Z[f'G_{pb_}_r{r}'])
        for s in ESCALES:
            PA_, PB_ = bp_meitat(GA, s), bp_meitat(GB, s)
            shifts = [int(round(x)) for x in np.linspace(max(20, 9 * s), max(40, 18 * s), 6)]; shifts = shifts + [-x for x in shifts]
            ROLL = {sh: np.roll(PA_, -int(round(sh / DA)), axis=1) for sh in shifts}
            refB = np.nanmean(np.where(REF[:, None], PB_, np.nan), axis=0)          # continuïtat radial: B a d 8–12
            for a0, a1 in ((75, 105), (105, 135), (205, 235), (235, 255), (285, 345)):
                zs = (TH >= a0) & (TH < a1)
                for nom, bins, var in (('d', BINS_D, DP), ('DREAL_MAX', BINS_DX, DXp[r])):
                    for b0, b1 in bins:
                        sel = zs[None, :] & (var >= b0) & (var < b1); st = stats(PA_[sel], PB_[sel])
                        if st is None: continue
                        rn = [stats(ROLL[sh][sel], PB_[sel]) for sh in shifts]; rn = np.array([x['r'] for x in rn if x])
                        st['nul_r'] = [float(rn.mean()), float(rn.std())] if rn.size else None
                        st['z'] = float((st['r'] - rn.mean()) / max(rn.std(), 1e-6)) if rn.size else None
                        cr = stats(PA_[sel], np.broadcast_to(refB[None, :], PA_.shape)[sel])       # A a la banda contra B a 8–12 px
                        st['continuitat_radial_r'] = cr['r'] if cr else None
                        res['resultats'].append(dict(rampa=list(RAMPES[r]), meitats=f'{pa_}/{pb_}', escala_px=s, sector=[a0, a1], calaix=nom, rang=[b0, b1], **st))
            print(f'r{r} {pa_}/{pb_} σ{s}', flush=True)
SORT.write_text(json.dumps(res, indent=1, ensure_ascii=False))
L = [f"r{x['rampa']} {x['meitats']:>14} esc{x['escala_px']} PA{x['sector']} {x['calaix']:>9} {x['rang'][0]}-{x['rang'][1]} n{x['n']} r {x['r']:+.3f} z {x['z'] if x['z'] is None else round(x['z'], 1)} "
     f"detall {x['rms_detall_pc']:.2f}% soroll {x['rms_soroll_apilat_pc']:.2f}% S/N {x['sn_apilat']:.2f} contR {x['continuitat_radial_r'] if x['continuitat_radial_r'] is None else round(x['continuitat_radial_r'], 3)}"
     for x in res['resultats']]
(O / 'Q1C_resum.txt').write_text('\n'.join(L)); print('fet', SORT)
