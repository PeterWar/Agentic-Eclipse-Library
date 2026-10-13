"""Fotometria d'obertura de les estrelles de camp del Vixen + R6 III, PER CANAL (R, G, B).

Tasca msb_calibrat_20261011/zp_canal (11-10-2026). Generalitza, sense canviar res
del mètode, la cadena original:
  original/vixen/proc.py   (RAW − fosc, màscara de saturats i calents dilatada 3×3,
                            pla del canal interpolat a resolució completa, fons i
                            sigma en blocs de 24 px)
  original/xmatch/phot2.py (do_r6: mateixes obertures RMAX 20, anell 26–40 px,
                            recentratge a cada fotograma, ÷ temps d'exposició)

Dues variants, triades ABANS de mirar cap resultat:
  «interp» (PRINCIPAL): el pla del canal s'omple a resolució completa amb la mitjana
      dels veïns vàlids del mateix canal, com fa lib.green_full per al verd. Per al
      verd és EXACTAMENT lib.green_full (es comprova bit a bit contra res_*.npy de
      proc.py). Per al vermell i el blau, la mitjana dels veïns del mateix canal dins
      del 3×3 (que per a una graella de Bayer és la interpolació bilineal). Unitats:
      ADU/s de «superfície completa» del canal, igual que el verd original.
  «natiu» (control): només els píxels CFA del canal (col==0 R, col==1|3 G,
      col==2 B), sans, sobre el mateix residu, multiplicats pel factor d'àrea
      (2 per al verd, 4 per al vermell i el blau).

Cap píxel inventat entra a cap resultat que no sigui la suma d'obertura: l'ompliment
del pla és el mateix que la cadena original ja feia per al verd, i la variant
«natiu» el prescindeix del tot.

Sortides (a comu.work('canal')): phot_r6_<canal>_<variant>.npz amb el mateix format
que phot_r6.npz de phot2.py, segells per estrella (stamps_r6.npz) i
fot_canal_rebut.json (sha256 de cada CR3 i fosc mestre, comprovacions).
"""
import hashlib
import json
import os
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI / "original"))
sys.path.insert(0, str(AQUI / "original" / "vixen"))
import comu  # noqa: E402  (còpia amb rutes de la tasca)
os.chdir(comu.work("vixen"))
import lib  # noqa: E402  (original/vixen/lib.py, intacte)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import rawpy  # noqa: E402
from scipy import ndimage as ndi  # noqa: E402

# Mateixos fotogrames, exposicions i fosc que proc.py i phot2.py (R6_FR).
FRAMES = [('572A2978', 1.0, '1'), ('572A2979', 2.0, '2'), ('572A2980', 2.0, '2'),
          ('572A2981', 2.0, '2'), ('572A2982', 10.3, '10'), ('572A2983', 10.3, '10'),
          ('572A2984', 10.3, '10'), ('572A2996', 1.0, '1')]
RMAX = 20
ANN = (26, 40)
# Disposició CFA del R6 III (raw_pattern [[0,1],[3,2]], comprovada a cada fitxer)
CANALS = {'R': [(0, 0)], 'G': [(0, 1), (1, 0)], 'B': [(1, 1)]}
COLS = {'R': (0,), 'G': (1, 3), 'B': (2,)}
AREA = {'R': 4.0, 'G': 2.0, 'B': 4.0}
H, W = lib.H, lib.W


def sha256(p, bloc=1 << 22):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while True:
            b = f.read(bloc)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def natiu(ch):
    m = np.zeros((H, W), bool)
    for (dy, dx) in CANALS[ch]:
        m[dy::2, dx::2] = True
    return m


def canal_full(im, badmask, ch):
    """Pla del canal a resolució completa. Verd: lib.green_full, intacte.
    Vermell/blau: valor natiu on n'hi ha (NaN si és dolent); a la resta, mitjana
    dels veïns vàlids del mateix canal dins del 3×3 (bilineal a la graella Bayer)."""
    if ch == 'G':
        return lib.green_full(im, badmask)
    g = np.full((H, W), np.nan, dtype=np.float32)
    nat = natiu(ch)
    g[nat] = im[nat]
    if badmask is not None:
        g[badmask] = np.nan
    v = np.isfinite(g)
    gv = np.where(v, g, 0.0).astype(np.float32)
    vv = v.astype(np.float32)
    s = np.zeros_like(gv)
    n = np.zeros_like(vv)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy == 0 and dx == 0:
                continue
            ys = slice(max(dy, 0), H + min(dy, 0))
            yd = slice(max(-dy, 0), H + min(-dy, 0))
            xs = slice(max(dx, 0), W + min(dx, 0))
            xd = slice(max(-dx, 0), W + min(-dx, 0))
            s[yd, xd] += gv[ys, xs]
            n[yd, xd] += vv[ys, xs]
    filled = np.where(n > 0, s / np.maximum(n, 1), np.nan)
    out = np.where(nat, g, filled)      # els natius dolents queden NaN, com al verd
    return out.astype(np.float32)


def phot_stamp(res, valid, x, y, rmax=RMAX, ann=ANN, recenter=True, search=9):
    """Còpia literal de original/xmatch/phot2.py:phot_stamp (mateix algorisme)."""
    P = ann[1]+3
    Hh, Ww = res.shape
    xi, yi = int(round(x)), int(round(y))
    if not (P < xi < Ww-P and P < yi < Hh-P):
        return None
    st = res[yi-P:yi+P+1, xi-P:xi+P+1].astype(np.float64)
    vm = valid[yi-P:yi+P+1, xi-P:xi+P+1]
    Y, X = np.mgrid[-P:P+1, -P:P+1]
    fx, fy = x-xi, y-yi
    if recenter:
        sm = np.where(vm, st, 0.0)
        cnt = ndi.uniform_filter(vm.astype(float), 3)
        sm = ndi.uniform_filter(sm, 3)/np.maximum(cnt, 1e-3)
        box = (np.abs(X-fx) <= search) & (np.abs(Y-fy) <= search)
        w = np.where(box, sm, -1e30)
        j = np.unravel_index(np.argmax(w), w.shape)
        cx0, cy0 = X[j], Y[j]
        rr0 = np.hypot(X-cx0, Y-cy0)
        m = (rr0 <= 4.0) & vm
        b0 = np.median(st[(rr0 >= ann[0]) & (rr0 < ann[1]) & vm])
        s = np.clip(st-b0, 0, None)*m
        tot = s.sum()
        if tot > 0:
            fx = cx0 + (s*(X-cx0)).sum()/tot
            fy = cy0 + (s*(Y-cy0)).sum()/tot
    rr = np.hypot(X-fx, Y-fy)
    a = (rr >= ann[0]) & (rr < ann[1]) & vm
    if a.sum() < 40:
        return None
    b = np.median(st[a])
    s = st - b
    F = np.zeros(rmax)
    N = np.zeros(rmax)
    for k in range(rmax):
        m = (rr <= k+1) & vm
        F[k] = s[m].sum()
        N[k] = m.sum()
    return F, b, xi+fx, yi+fy, N, np.std(st[a])


def main():
    xm = comu.work('xmatch')
    tab = pd.read_csv(xm / 'final_match_r6.csv')
    SH = json.load(open(comu.work('vixen') / 'shifts_start.json'))
    n = len(tab)
    rebut = dict(tasca='msb_calibrat_20261011/zp_canal', guio='fot_canal.py',
                 data=time.strftime('%Y-%m-%dT%H:%M:%S'), entrades={}, comprovacions={})
    for nom in ('final_match_r6.csv',):
        rebut['entrades'][f'work/xmatch/{nom}'] = sha256(xm / nom)
    rebut['entrades']['work/vixen/shifts_start.json'] = sha256(comu.work('vixen') / 'shifts_start.json')
    hm = {k: lib.hotmask('dark_med_%s.npy' % k) for k in ['1', '2', '10']}
    dk = {k: np.load('dark_med_%s.npy' % k)[:H, :W] for k in ['1', '2', '10']}
    for k in ['1', '2', '10']:
        rebut['entrades'][f'work/vixen/dark_med_{k}.npy'] = sha256(Path('dark_med_%s.npy' % k))
    resultats = {(ch, var): dict(F=np.full((len(FRAMES), n, RMAX), np.nan),
                                 S=np.full((len(FRAMES), n), np.nan),
                                 X=np.full((len(FRAMES), n), np.nan),
                                 Y=np.full((len(FRAMES), n), np.nan),
                                 B=np.full((len(FRAMES), n), np.nan),
                                 NPIX=np.full((len(FRAMES), n, RMAX), np.nan))
                 for ch in 'RGB' for var in ('interp', 'natiu')}
    P = ANN[1] + 3
    stamps = np.full((len(FRAMES), 3, n, 2*P+1, 2*P+1), np.nan, np.float32)
    for fi, (f, exp, dkey) in enumerate(FRAMES):
        t0 = time.time()
        cr3 = Path(lib.DIR) / (f + '.CR3')
        rebut['entrades'][f'0-RAW/Vixen R6III/Vixen Fase totalitat/{f}.CR3'] = sha256(cr3)
        with rawpy.imread(str(cr3)) as r:
            col = r.raw_colors_visible[:H, :W].copy()
            patt = r.raw_pattern.tolist()
        assert patt == [[0, 1], [3, 2]], (f, patt)
        im = lib.load_raw(f)
        sat = im >= lib.SAT
        im = im - dk[dkey]
        bad = ndi.binary_dilation(sat | hm[dkey], np.ones((3, 3)))
        _, dx, dy = SH[f]
        for ci, ch in enumerate('RGB'):
            nat = natiu(ch)
            assert np.array_equal(nat, np.isin(col, COLS[ch])), (f, ch)
            g = canal_full(im, bad, ch)
            mask = ~np.isfinite(g)
            bg, sig, res = lib.bg_and_sigma(g, bs=24, mask=mask)
            if ch == 'G':
                ref = comu.work('vixen') / f'res_{f}.npy'
                if ref.exists():
                    r0 = np.load(ref)
                    m0 = np.load(comu.work('vixen') / f'msk_{f}.npy')
                    ok = bool(np.array_equal(r0, res, equal_nan=True) and np.array_equal(m0, mask))
                    rebut['comprovacions'][f'G_interp_bit_identic_a_proc_{f}'] = ok
                    print(f'  {f} G: residu bit a bit igual al de proc.py: {ok}')
                    del r0, m0
            valid_i = ~mask
            valid_n = nat & ~bad & ~mask
            for var, valid, fac in (('interp', valid_i, 1.0), ('natiu', valid_n, AREA[ch])):
                R_ = resultats[(ch, var)]
                for i in range(n):
                    out = phot_stamp(res, valid, tab.x.values[i]+dx, tab.y.values[i]+dy)
                    if out is None:
                        continue
                    F, b, xc, yc, N, sd = out
                    R_['F'][fi, i] = F*fac/exp
                    R_['S'][fi, i] = sd*fac/exp
                    R_['X'][fi, i] = xc
                    R_['Y'][fi, i] = yc
                    R_['B'][fi, i] = b/exp
                    R_['NPIX'][fi, i] = N
                    if var == 'interp':
                        xi, yi = int(round(xc)), int(round(yc))
                        if P < xi < W-P and P < yi < H-P:
                            stamps[fi, ci, i] = res[yi-P:yi+P+1, xi-P:xi+P+1]/exp
            del g, mask, bg, sig, res
        print(f'{f} exp={exp:5.1f}s  {time.time()-t0:5.1f} s'); sys.stdout.flush()
        del im, sat, bad, col
    outdir = comu.work('canal')
    for (ch, var), R_ in resultats.items():
        np.savez(outdir / f'phot_r6_{ch}_{var}.npz',
                 names=np.array([f for f, _, _ in FRAMES]), F=R_['F'], S=R_['S'],
                 exp=np.array([e for _, e, _ in FRAMES]), det=tab.det.values,
                 xc=R_['X'], yc=R_['Y'], bkg=R_['B'], npix=R_['NPIX'])
    np.savez_compressed(outdir / 'stamps_r6.npz', stamps=stamps, canals=np.array(list('RGB')),
                        frames=np.array([f for f, _, _ in FRAMES]), det=tab.det.values,
                        unitats='ADU/s per píxel del pla interpolat del canal, residu després del fons de blocs de 24 px')
    # Control: la variant G «interp» ha de donar exactament phot_r6.npz de phot2.py (si ja hi és)
    p2 = comu.work('xmatch') / 'phot_r6.npz'
    if p2.exists():
        z = np.load(p2, allow_pickle=True)
        a = resultats[('G', 'interp')]['F']
        ok = bool(np.array_equal(z['F'], a, equal_nan=True))
        dif = float(np.nanmax(np.abs(z['F']-a))) if not ok else 0.0
        rebut['comprovacions']['G_interp_igual_a_phot2_phot_r6_npz'] = ok
        rebut['comprovacions']['G_interp_max_dif_ADU_s'] = dif
        print(f'G interp == phot_r6.npz de phot2.py: {ok} (dif. màx. {dif:.3g})')
    json.dump(rebut, open(outdir / 'fot_canal_rebut.json', 'w'), indent=1, ensure_ascii=False)


if __name__ == '__main__':
    main()
