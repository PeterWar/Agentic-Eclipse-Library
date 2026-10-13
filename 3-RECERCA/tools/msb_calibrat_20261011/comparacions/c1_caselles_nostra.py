"""c1 · La nostra brillantor (mapa MSB) per anells i caselles d'1°, per a totes les comparacions. Encàrrec «comparacions», 11-10-2026.

Entrada: els plans plens del mapa (mapa/ple/msb_ple.npy, msb_noext_ple.npy, flags_ple.npy; NOMÉS LECTURA, mmap), la graella de
massa d'aire (mapa/massa_aire_graella.npz) i el cel (mapa/CEL.json). Res de la Paperera: el mapa ja és fet.

Per casella (anell, PA d'1°): mediana dels píxels vàlids de
  msb (cel b, extinció k = 0,40), msb_noext (cel b, sense extinció), msb amb el cel a i amb el c, msb amb k = 0,35 i k = 0,72,
  E (factor d'extinció), cel (B☉, verd de càmera), fracció Sony·ρ;
i el nombre de píxels que TOQUEN una zona prohibida (franja lunar, buit del limbe, sense dada, protuberància, fantasma, fora del cercle
inscrit). ⛔ Regla predeclarada: una casella que en toqui UN sol píxel queda fora de tota comparació.
Conjunts d'anells: K-Cor (5 + l'1,10–1,15 de la c9, només per comptar), C2 (6, com la c9) i els anells fins de la figura.
Escriu comparacions/caselles_nostra.npz i CASELLES_NOSTRA.json."""
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cmp_comu as cc   # noqa: E402

mc = cc.mc
T0 = time.time()
cc.RES.mkdir(parents=True, exist_ok=True)
msb = np.load(cc.PLE / 'msb_ple.npy', mmap_mode='r')
noe = np.load(cc.PLE / 'msb_noext_ple.npy', mmap_mode='r')
flg = np.load(cc.PLE / 'flags_ple.npy', mmap_mode='r')
assert msb.shape == (mc.H, mc.W) and flg.dtype == np.uint8
MA = mc.MassaAire(); CEL = mc.coef_cel()
g = mc.geo_llenc()
RMAX = 6.15
y0 = max(0, int(mc.SOL_XY[1] - RMAX * 1.01 * mc.RSOL_PX)); y1 = min(mc.H, int(mc.SOL_XY[1] + RMAX * 1.01 * mc.RSOL_PX) + 1)
x0 = max(0, int(mc.SOL_XY[0] - RMAX * 1.01 * mc.RSOL_PX)); x1 = min(mc.W, int(mc.SOL_XY[0] + RMAX * 1.01 * mc.RSOL_PX) + 1)

CONJ = {'kcor': cc.ANELLS_KCOR + [cc.ANELL_C9_FRANJA], 'c2': cc.ANELLS_C2,
        'fig': [(round(r * (1 - cc.AMPLE_FIG), 5), round(r * (1 + cc.AMPLE_FIG), 5)) for r in cc.RADIS_FIG]}
VARS = ('msb', 'noe', 'skyA', 'skyC', 'k035', 'k072', 'E', 'sky', 'sony')
acc = {c: {v: [] for v in VARS + ('key', 'toca')} for c in CONJ}
for ya in range(y0, y1, 512):
    yb = min(ya + 512, y1)
    yy = np.arange(ya, yb, dtype=np.float64)[:, None] * np.ones((1, x1 - x0))
    xx = np.ones((yb - ya, 1)) * np.arange(x0, x1, dtype=np.float64)[None, :]
    r, pa = g.polar(xx, yy)
    if np.nanmin(r) > RMAX:
        continue
    m = np.asarray(msb[ya:yb, x0:x1], np.float64); n_ = np.asarray(noe[ya:yb, x0:x1], np.float64); f = np.asarray(flg[ya:yb, x0:x1])
    h = MA.altura_bloc(ya, yb, x0, x1); X = mc.kasten_young(h); E = mc.factor_extincio(X, MA.X_sol)
    Sa, Sb, Sc = (mc.cel_model(xx, yy, k, CEL) for k in ('a', 'b', 'c'))
    skyA = m + mc.FAC_G * E * (Sb - Sa); skyC = m + mc.FAC_G * E * (Sb - Sc)
    k035 = n_ * mc.factor_extincio(X, MA.X_sol, 0.35); k072 = n_ * mc.factor_extincio(X, MA.X_sol, 0.72)
    toca = (f & cc.TOCA) > 0
    valid = ~toca & np.isfinite(m)
    sony = ((f & mc.BITS['SONY_DOMINATED']) > 0).astype(np.float64)
    vals = dict(msb=m, noe=n_, skyA=skyA, skyC=skyC, k035=k035, k072=k072, E=E, sky=mc.FAC_G * Sb, sony=sony)
    for c, an in CONJ.items():
        key, nb = cc.clau_caselles(r, pa, an)
        sel = key >= 0
        if not sel.any():
            continue
        acc[c]['key'].append(key[sel]); acc[c]['toca'].append(toca[sel])
        for v in VARS:
            acc[c][v].append(np.where(valid, vals[v], np.nan)[sel].astype(np.float32))
    print(f'files {ya}-{yb} ({time.time() - T0:.0f} s)', flush=True)

out = {}
resum = {}
for c, an in CONJ.items():
    nb = 360; ng = len(an) * nb
    key = np.concatenate(acc[c]['key']); toca = np.concatenate(acc[c]['toca'])
    ntoca = np.bincount(key[toca], minlength=ng)[:ng]
    ntot = np.bincount(key, minlength=ng)[:ng]
    for v in VARS:
        val = np.concatenate(acc[c][v]).astype(np.float64)
        n, q = cc.percentils_grup(key, val, ng, (50,) if v != 'msb' else (10, 50, 90))
        for qq, arr in q.items():
            nom = f'{c}_{v}' if qq == 50 else f'{c}_{v}_p{qq}'
            out[nom] = arr.reshape(len(an), nb)
        if v == 'msb':
            out[f'{c}_nvalid'] = n.reshape(len(an), nb)
    out[f'{c}_ntoca'] = ntoca.reshape(len(an), nb); out[f'{c}_ntot'] = ntot.reshape(len(an), nb)
    out[f'{c}_anells'] = np.array(an)
    usable = (ntoca == 0) & (ntot > 0) & np.isfinite(out[f'{c}_msb'].ravel())
    out[f'{c}_usable'] = usable.reshape(len(an), nb)
    resum[c] = [dict(anell=list(a), caselles_amb_pixels=int((ntot.reshape(len(an), nb)[i] > 0).sum()),
                     caselles_que_toquen_zona_prohibida=int((ntoca.reshape(len(an), nb)[i] > 0).sum()),
                     caselles_usables=int(usable.reshape(len(an), nb)[i].sum()),
                     fraccio_sony_mediana=float(np.nanmedian(out[f'{c}_sony'][i])))
                for i, a in enumerate(an)]
    del acc[c]
np.savez_compressed(cc.RES / 'caselles_nostra.npz', **out)
entr = {cc.rel(p): cc.sha256(p) for p in (cc.PLE / 'msb_ple.npy', cc.PLE / 'msb_noext_ple.npy', cc.PLE / 'flags_ple.npy',
                                             mc.MAPA / 'massa_aire_graella.npz', mc.MAPA / 'CEL.json', mc.MAPA / 'ZONES.json')}
json.dump(dict(guio=cc.rel(__file__), data=time.strftime('%Y-%m-%dT%H:%M:%S'), entrades_sha256=entr,
               regla='casella fora si toca un sol píxel amb bits ' + str(cc.TOCA) + ' (NO_DATA|LIMB_GAP|MOON_BAND|PROMINENCE|SONY_GHOST|OUTSIDE_INSCRIBED)',
               resum=resum, segons=round(time.time() - T0, 1)),
          open(cc.RES / 'CASELLES_NOSTRA.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps(resum, indent=1, ensure_ascii=False))
print(f'fet ({time.time() - T0:.0f} s)')
