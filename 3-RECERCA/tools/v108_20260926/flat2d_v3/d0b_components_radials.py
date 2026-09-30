"""d0b_components_radials (V108, flat2d_v3, DIAGNOSI) · Els ANELLS de C (la part que només depèn de la distància al centre del sensor) contra
la resta. Hipòtesi a provar: els anells cromàtics de C (fortíssims a R − G a la Sony) són de l'espectre de la llum dels flats (el tall del filtre
IR es mou amb l'angle d'incidència i depèn de l'espectre), i per això a l'eclipsi només n'hi ha una part; la textura no radial (resposta dels
píxels, pols, línies) és del sensor i hi ha de ser sencera.
Per a cada canal CFA: ln C_c = ℓ + κ_c (com d0); cada una es parteix en RADIAL (mitjana per anells d'1 subplà al voltant del centre del sensor,
fora dels 150 subplans de les vores) i NO RADIAL (la resta):  Lr, Ln, Kr, Kn. La suma dels quatre és la v2.
Sortida: <out>/<TREN>_<comp>.npz i D0B_COMPONENTS.json.  Ús: d0b_components_radials.py [--trens SONYTOT,VIXEN]"""
import json, argparse, hashlib, time
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[4]
V2 = ARREL / '4-RESULTATS/v108_20260926/flat2d_v2/flat2d'
CENTRE = {'SONYTOT': (2660.0, 4000.0), 'VIXEN': (2380.0, 3572.0)}      # (y, x) RAW, els de la cadena (FLAT_CENTRE / f0_flat2d_v2)
ap = argparse.ArgumentParser(); ap.add_argument('--trens', default='SONYTOT,VIXEN'); ap.add_argument('--centre', default=None, help='y,x RAW del centre dels anells (per defecte, el de la cadena)'); ap.add_argument('--sufix', default='')
ap.add_argument('--out', default=str(ARREL / '4-RESULTATS/v108_20260926/flat2d_v3/diag/components'))
a = ap.parse_args(); OUT = Path(a.out); OUT.mkdir(parents=True, exist_ok=True); t0 = time.time(); rep = dict(trens={})
for T in a.trens.split(','):
    z = np.load(V2 / f'{T}_flat2d_v2.npz'); C = z['C'].astype(np.float32); pat = z['patró']; h, w = C.shape; hs, ws = h // 2, w // 2
    L = {(oy, ox): np.log(C[oy::2, ox::2][:hs, :ws]).astype(np.float32) for oy in range(2) for ox in range(2)}
    ell = (sum(L.values()) / 4.0).astype(np.float32)
    cy, cx = CENTRE[T] if a.centre is None else tuple(float(v) for v in a.centre.split(',')); yy, xx = np.mgrid[0:hs, 0:ws].astype(np.float32); rr = np.hypot(2 * yy + 0.5 - cy, 2 * xx + 0.5 - cx) / 2.0   # subplans
    ib = rr.astype(np.int32); nb = int(ib.max()) + 1
    interior = np.zeros((hs, ws), bool); interior[150:-150, 150:-150] = True
    def radial(x):
        n = np.bincount(ib[interior], None, nb); s = np.bincount(ib[interior], x[interior].astype(np.float64), nb)
        pr = np.where(n >= 30, s / np.maximum(n, 1), 0.0); return pr[ib].astype(np.float32), pr, n
    comp = {k + a.sufix: {} for k in ('Lr', 'Ln', 'Kr', 'Kn')}; ellr, pr_l, n_l = radial(ell); perfils = dict(L=pr_l)
    for k, v in L.items():
        kap = v - ell; kr, pr_k, _ = radial(kap); perfils[f'K{int(pat[k])}'] = pr_k
        comp['Lr' + a.sufix][k] = ellr; comp['Ln' + a.sufix][k] = ell - ellr; comp['Kr' + a.sufix][k] = kr; comp['Kn' + a.sufix][k] = kap - kr
    r = {}
    for nom, d in comp.items():
        Cn = np.ones((h, w), np.float32)
        for (oy, ox), v in d.items(): Cn[oy::2, ox::2][:hs, :ws] = np.exp(v)
        p = OUT / f'{T}_{nom}.npz'; np.savez(p, C=Cn, patró=pat, component=nom)
        sub = {int(pat[oy, ox]): v[150:-150, 150:-150] for (oy, ox), v in d.items()}
        r[nom] = dict(rms_ppm={['R', 'G1', 'B', 'G2'][c]: round(1e4 * float(v.std()), 3) for c, v in sub.items()}, sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    np.savez(OUT / f'{T}_perfils_radials{a.sufix}.npz', **perfils, n=n_l, centre_yx_RAW=np.array([cy, cx]))
    rep['trens'][T] = dict(r, centre_yx_RAW=[cy, cx]); print(T, json.dumps(r, ensure_ascii=False), f'{time.time()-t0:.0f}s', flush=True)
(OUT / f'D0B_COMPONENTS{a.sufix}.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1) + '\n')
