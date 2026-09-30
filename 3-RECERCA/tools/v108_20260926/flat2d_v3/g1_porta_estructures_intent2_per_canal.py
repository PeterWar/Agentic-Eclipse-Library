"""g1_porta_estructures (V108, flat2d_v3) · LA PORTA PER ESTRUCTURA I PER CANAL: cada taca de pols o línia de la C (f0_flat2d_v3:
ESTRUCTURES_<TREN>.json i <TREN>_components_v3.npz) s'aplica NOMÉS a l'apuntament i al canal de càmera (R, G, B) on l'apilat sense corregir hi
té el defecte corresponent, validat amb nuls. (Hi ha línies del sensor que són quasi només al verd: la de T2, a G1.)
La prova es fa a l'espai de CÀMERA: els apilats es desfan de la matriu de color (u = (M·u_càmera)·guany, comu.lluminancia) → ln u_càmera,c.
La pols es mou: els flats són de 10 dies després de l'eclipsi, i una taca que hi ha als flats pot no ser a les llums (llavors C l'injecta invertida).
Per a cada grup (sony_A, sony_B, vixen) i cada estructura k:
  · PLANTILLA T_k,c: el contingut de k al canal de càmera c de C (ln C'_c dins de la seva petjada suau), portat al llenç amb el mapatge de cada fotograma del grup
    (g0_mapatge.py: el mateix codi que els apilats) i fet la mitjana ponderada per l'exposició (inclou la deriva). Si el defecte hi és, l'apilat
    sense corregir porta +T_k (i la C el treu).
  · DADA Z_c: ln del canal de càmera c de l'apilat del grup MENYS el ln d'una referència que veu el MATEIX cel amb un altre sensor (el cel i la corona s'anul·len):
    sony_A ↔ sony_B (el salt de 749 px; el mateix canal c, la mateixa càmera), vixen → el G (després de la matriu) de la Sony A+B; si la referència no cobreix la plantilla, la Vixen per a la Sony; si no n'hi ha
    cap, l'apilat sol (el nul ho paga). Z i T passen per la mateixa banda (DoG) del llenç.
  · a_k = ⟨Z, T⟩ / ⟨T, T⟩: 1 si el defecte hi és sencer, 0 si no hi és. NUL: la mateixa plantilla a 80 posicions a l'atzar a la mateixa distància
    del Sol (±10 %), a la mateixa Z → σ_nul. La correcció de k fa s_k = 1 − 2·a_k (−1 cura, +1 injecció).
  · PORTA: s'aplica si el defecte HI ÉS, validat amb el nul ((a_k − ⟨nul⟩)/σ_nul ≥ 3), si la correcció en treu més del que en posa (a_k ≥ 0,5,
    és a dir s_k ≤ 0) i si la quantitat que hi ha és compatible amb la de C ((a_k − 1)/σ_nul ≤ 3: si la dada en porta molt més, és una altra
    cosa —p. ex. el «ghost» de l'eix òptic a l'apuntament A— i C no l'explica). Si no, no s'aplica (res inventat: sense prova, la C d'aquesta
    estructura no hi entra). També es desa el criteri estricte ((a_k − 0,5)/σ_nul ≥ 2), només informatiu.
Sortida: 4-RESULTATS/v108_20260926/flat2d_v3/flat2d/G1_PORTA_<TREN>.json.  Ús: g1_porta_estructures.py VIXEN|SONYTOT   (només lectura; ~8 GB)"""
import json, sys, time, math, argparse
from pathlib import Path
import numpy as np, cv2
ARREL = Path(__file__).resolve().parents[4]; R3 = ARREL / '4-RESULTATS/v108_20260926/flat2d_v3'; CR = ARREL / '4-RESULTATS/v97_refundacio_20260924'
W_, H_ = 10551, 7506; SOL = np.array([5361.768, 3775.748]); RSOL = 440.603; LLUNA = (5375.787, 3775.977); RL = 452.98
AP = {'sony_A': CR / 'cadena_raw/b2_sony_A/cau/sony_A_total_v36.npy', 'sony_B': CR / 'cadena_raw/b2_sony_B/cau/sony_B_total_v42.npy',
      'vixen': CR / 'proves_apilat/vixen_comuna_taula_original/vixen_total.npy', 'sony_AB': ARREL / '4-RESULTATS/v98_20260925/cadena_v98/b3/cau/sony_corrected_total_v42.npy'}
ap = argparse.ArgumentParser(); ap.add_argument('tren', choices=['VIXEN', 'SONYTOT']); ap.add_argument('--dir', default=str(R3 / 'flat2d'))
ap.add_argument('--n-nul', type=int, default=80); a = ap.parse_args(); t0 = time.time(); D = Path(a.dir)
SONY = a.tren == 'SONYTOT'; TAG = 'sony' if SONY else 'vixen'
BANDA = (2.0, 150.0) if SONY else (2.0, 80.0)                    # px del llenç (1 subplà Sony ≈ 3 px; Vixen = 2 px)
MP = json.loads((R3 / 'diag/MAPATGE_V3.json').read_text()); inv = np.array(MP['inv_common_to_final']); TR = MP['trens'][TAG]; dB = MP['delta_B_rad']
Z_ = np.load(D / f'{a.tren}_components_v3.npz'); LAB = Z_['lab']; Wt = Z_['W']; CAMC = {c: Z_[f'cam_{c}'] for c in ('R', 'G', 'B')}; hs, ws = LAB.shape
EST = json.loads((D / f'ESTRUCTURES_{a.tren}.json').read_text())['estructures']
MINV = {t: np.linalg.inv(np.array(MP['trens'][t]['matriu'])) for t in MP['trens']}; GU = {t: np.array(MP['trens'][t]['guany']) for t in MP['trens']}
TREN_DE = {'sony_A': 'sony', 'sony_B': 'sony', 'vixen': 'vixen', 'sony_AB': 'sony'}
def lncam(g, c):
    """ln del canal de càmera c de l'apilat g (desfent la matriu i el guany); c = None → el G després de la matriu (per a la referència Sony de la Vixen)."""
    x = np.load(AP[g], mmap_mode='r')
    if c is None: v = np.asarray(x[..., 1], np.float32)
    else:
        j = 'RGB'.index(c); t = TREN_DE[g]; mi = MINV[t][j]; gu = GU[t]
        v = sum(float(mi[i] / gu[i]) * np.asarray(x[..., i], np.float32) for i in range(3)).astype(np.float32)
    ok = np.isfinite(v) & (v > 0)
    return np.where(ok, np.log(np.maximum(v, 1e-20)), 0).astype(np.float32), ok
yy, xx = np.mgrid[0:H_, 0:W_].astype(np.float32); DL = np.hypot(xx - LLUNA[0], yy - LLUNA[1]) - RL; del yy, xx
def a_sensor(X, Y, g, f):
    """llenç → sensor RAW per al fotograma f del grup g (el mateix codi que b2 / s3)."""
    qx = inv[0, 0] * X + inv[0, 1] * Y + inv[0, 2]; qy = inv[1, 0] * X + inv[1, 1] * Y + inv[1, 2]; dx = (qx - TR['CX']) * TR['k']; dy = (qy - TR['CY']) * TR['k']
    if g == 'sony_B': c_, s_ = math.cos(dB), math.sin(dB); dx, dy = c_ * dx - s_ * dy, s_ * dx + c_ * dy
    return TR['ca'] * dx + TR['sa'] * dy + f['sol_x'], -TR['sa'] * dx + TR['ca'] * dy + f['sol_y']
def plantilla(k, g, marge, c):
    """T_k,c al llenç (pegat) per al grup g: mitjana ponderada per exposició del contingut de k al canal c mostrejat a cada fotograma."""
    e = next(x for x in EST if x['id'] == k); x0, y0, x1, y1 = e['caixa_subpla']
    Al = np.array(TR['grups'][g]['afi_sensor_a_llenc'])
    cs = np.array([[2 * x0, 2 * y0], [2 * x1, 2 * y0], [2 * x0, 2 * y1], [2 * x1, 2 * y1]], float)
    cl = (Al[:, :2] @ cs.T).T + Al[:, 2]; X0, Y0 = np.floor(cl.min(0) - marge).astype(int); X1, Y1 = np.ceil(cl.max(0) + marge).astype(int)
    X0, Y0 = max(X0, 0), max(Y0, 0); X1, Y1 = min(X1, W_), min(Y1, H_)
    if X1 - X0 < 20 or Y1 - Y0 < 20: return None
    Yp, Xp = np.mgrid[Y0:Y1, X0:X1].astype(np.float32)
    sx0, sy0 = max(x0 - 6, 0), max(y0 - 6, 0); sx1, sy1 = min(x1 + 6, ws), min(y1 + 6, hs)
    src = np.where(LAB[sy0:sy1, sx0:sx1] == k, Wt[sy0:sy1, sx0:sx1] * CAMC[c][sy0:sy1, sx0:sx1], 0).astype(np.float32)
    acc = np.zeros(Yp.shape, np.float64); wsum = 0.0
    for f in TR['grups'][g]['fotogrames'].values():
        rx, ry = a_sensor(Xp, Yp, g, f); mx = ((rx - 0.5) / 2 - sx0).astype(np.float32); my = ((ry - 0.5) / 2 - sy0).astype(np.float32)
        acc += f['exp'] * cv2.remap(src, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0); wsum += f['exp']
    return (X0, Y0, X1, Y1), (acc / wsum).astype(np.float32)
grups = ['sony_A', 'sony_B'] if SONY else ['vixen']
REFS = {'sony_A': ['sony_B', 'vixen', None], 'sony_B': ['sony_A', 'vixen', None], 'vixen': ['sony_AB', None]}
res = dict(tren=a.tren, banda_px=BANDA, n_nul=a.n_nul, criteri='per canal de càmera: aplica si (a − ⟨nul⟩)/σ_nul ≥ 3 i a ≥ 0,5 i (a − 1)/σ_nul ≤ 3; estricte (informatiu): (a − 0,5)/σ_nul ≥ 2', grups={})
rng = np.random.default_rng(20260927); s1, s2 = BANDA
for g in grups:
    dec = {str(e['id']): dict(canals={}) for e in EST}
    for c in ('R', 'G', 'B'):
        Xt, okt = lncam(g, c); Zc = {}
        for ref in REFS[g]:
            if ref is None: Xr, okr = np.zeros_like(Xt), np.ones_like(okt)
            elif ref in ('vixen', 'sony_AB'): Xr, okr = lncam(ref, None)          # una altra càmera: la seva lluminància (el cel), no el seu canal c
            else: Xr, okr = lncam(ref, c)
            m = (okt & okr & (DL > 40)).astype(np.float32)
            ng = lambda x, s: cv2.GaussianBlur(x * m, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6)
            z0 = np.where(m > 0, Xt - Xr, 0).astype(np.float32); Zc[ref] = ((ng(z0, s1) - ng(z0, s2)) * m).astype(np.float32), (cv2.erode(m, np.ones((61, 61), np.uint8)) > 0)
            del Xr, okr, z0, m
        del Xt, okt
        for e in EST:
            k = e['id']; p = plantilla(k, g, 3 * s2, c)
            if p is None: dec[str(k)]['canals'][c] = dict(aplica=False, motiu='fora del llenç'); continue
            (X0, Y0, X1, Y1), T = p
            if np.abs(T).max() < 1e-7: dec[str(k)]['canals'][c] = dict(aplica=False, motiu='fora del llenç'); continue
            o = None
            for ref in REFS[g]:
                Z, okz = Zc[ref]; okp = okz[Y0:Y1, X0:X1]; ET = float((T[okp] ** 2).sum()); ETt = float((T ** 2).sum())
                if ETt <= 0 or ET < 0.9 * ETt: continue
                mp = okp.astype(np.float32)
                ngp = lambda x, s: cv2.GaussianBlur(x * mp, (0, 0), s) / np.maximum(cv2.GaussianBlur(mp, (0, 0), s), 1e-6)
                Tb = ((ngp(T, s1) - ngp(T, s2)) * mp).astype(np.float32); ETb = float((Tb.astype(np.float64) ** 2).sum())
                av = float((Z[Y0:Y1, X0:X1].astype(np.float64) * Tb).sum() / ETb)
                cx, cy = (X0 + X1) / 2, (Y0 + Y1) / 2; r0 = np.hypot(cx - SOL[0], cy - SOL[1]); hw, hh_ = X1 - X0, Y1 - Y0; nul = []; intents = 0
                while len(nul) < a.n_nul and intents < 4000:
                    intents += 1; ang = rng.uniform(0, 2 * np.pi); rr_ = r0 * rng.uniform(0.9, 1.1)
                    nx, ny = int(SOL[0] + rr_ * np.cos(ang) - hw / 2), int(SOL[1] + rr_ * np.sin(ang) - hh_ / 2)
                    if nx < 0 or ny < 0 or nx + hw > W_ or ny + hh_ > H_ or (abs(nx - X0) < hw and abs(ny - Y0) < hh_): continue
                    okn = okz[ny:ny + hh_, nx:nx + hw]
                    if float((Tb[okn].astype(np.float64) ** 2).sum()) < 0.9 * ETb: continue
                    nul.append(float((Z[ny:ny + hh_, nx:nx + hw].astype(np.float64) * Tb * okn).sum() / ETb))
                if len(nul) < 20: continue
                nul = np.array(nul); sd = float(nul.std()); mu = float(nul.mean()); zp = (av - mu) / sd; zc = (av - 0.5) / sd
                o = dict(ref=ref or 'cap (apilat sol)', a=round(av, 3), nul_mitjana=round(mu, 3), sigma_nul=round(sd, 3), n_nul=int(len(nul)), z_present=round(zp, 2), z_cura=round(zc, 2),
                         s=round(1 - 2 * av, 3), aplica=bool(zp >= 3 and av >= 0.5 and (av - 1) / sd <= 3), aplica_estricte=bool(zc >= 2 and zp >= 3), z_exces=round((av - 1) / sd, 2),
                         centre_llenc=[round(cx, 1), round(cy, 1)], R_sol=round(r0 / RSOL, 2), rms_plantilla_ppm=round(1e4 * float(np.sqrt(ETb / max(okp.sum(), 1))), 3))
                break
            dec[str(k)]['canals'][c] = o if o is not None else dict(aplica=False, motiu='cap referència ni dada que cobreixi la plantilla')
        del Zc
        print(g, c, 'fet', f'{time.time()-t0:.0f}s', flush=True)
    for k, d in dec.items():
        d['aplica_canals'] = {c: bool(d['canals'][c].get('aplica')) for c in ('R', 'G', 'B')}; d['aplica'] = any(d['aplica_canals'].values())
        e = next(x for x in EST if str(x['id']) == k); d['tipus'] = e['tipus']
    n_t = sum(1 for d in dec.values() if any('a' in x for x in d['canals'].values()))
    res['grups'][g] = dict(n_estructures=len(EST), n_provades=n_t, n_aplicades={c: sum(1 for d in dec.values() if d['aplica_canals'][c]) for c in ('R', 'G', 'B')}, decisions=dec)
    print(g, 'provades', n_t, 'aplicades per canal', res['grups'][g]['n_aplicades'], f'{time.time()-t0:.0f}s', flush=True)
(D / f'G1_PORTA_{a.tren}.json').write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n'); print('FET', f'{time.time()-t0:.0f}s')
