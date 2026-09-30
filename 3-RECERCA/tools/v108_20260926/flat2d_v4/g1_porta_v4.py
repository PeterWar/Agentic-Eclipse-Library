"""g1_porta_v4 (V108, flat2d_v4) · LA PORTA DE LA v3 (g1_porta_estructures.py, copiat) amb una segona plantilla per estructura: la PART
D'ESCALA DE TACA (f0_flat2d_v4: DoG G_s − G_6s de ℓ' a l'escala on es va detectar, dins de la petjada suau). És la part que la v4 escala amb
la a encongida; la plantilla sencera (ℓ' dins de la petjada, la de la v3) porta també el fons i la textura, que com a classe ja estan validats.
Les dues es mesuren amb la MATEIXA dada Z, la mateixa referència i les MATEIXES 80 posicions nul·les (mateixa llavor, mateix ordre d'extracció).
CONTROL: la plantilla sencera ha de donar exactament la porta de la v3 (a, σ_nul, z, decisió de cada estructura); si no, s'atura.
Sortida: 4-RESULTATS/v108_20260926/flat2d_v4/flat2d/G1_PORTA_V4_<TREN>.json (camps de la v3 + a_taca, sigma_nul_taca, nul_mitjana_taca, z_present_taca).
Ús: g1_porta_v4.py VIXEN|SONYTOT   (només lectura; ~6 GB)
─── Text de la v3 ───
g1_porta_estructures (V108, flat2d_v3) · LA PORTA PER ESTRUCTURA: cada taca de pols o línia de la C (f0_flat2d_v3: ESTRUCTURES_<TREN>.json i
<TREN>_components_v3.npz) s'aplica NOMÉS a l'apuntament on l'apilat sense corregir hi té el defecte corresponent, validat amb nuls.
La pols es mou: els flats són de 10 dies després de l'eclipsi, i una taca que hi ha als flats pot no ser a les llums (llavors C l'injecta invertida).
Per a cada grup (sony_A, sony_B, vixen) i cada estructura k:
  · PLANTILLA T_k: el contingut de k a C (ℓ' dins de la seva petjada suau), portat al llenç amb el mapatge de cada fotograma del grup
    (g0_mapatge.py: el mateix codi que els apilats) i fet la mitjana ponderada per l'exposició (inclou la deriva). Si el defecte hi és, l'apilat
    sense corregir porta +T_k (i la C el treu).
  · DADA Z: ln G de l'apilat del grup MENYS ln G d'una referència que veu el MATEIX cel amb un altre sensor (el cel i la corona s'anul·len):
    sony_A ↔ sony_B (el salt de 749 px), vixen → la Sony A+B; si la referència no cobreix la plantilla, la Vixen per a la Sony; si no n'hi ha
    cap, l'apilat sol (el nul ho paga). Z i T passen per la mateixa banda (DoG) del llenç.
  · a_k = ⟨Z, T⟩ / ⟨T, T⟩: 1 si el defecte hi és sencer, 0 si no hi és. NUL: la mateixa plantilla a 80 posicions a l'atzar a la mateixa distància
    del Sol (±10 %), a la mateixa Z → σ_nul. La correcció de k fa s_k = 1 − 2·a_k (−1 cura, +1 injecció).
  · PORTA: s'aplica si el defecte HI ÉS, validat amb el nul ((a_k − ⟨nul⟩)/σ_nul ≥ 3), si la correcció en treu més del que en posa (a_k ≥ 0,5,
    és a dir s_k ≤ 0) i si la quantitat que hi ha és compatible amb la de C ((a_k − 1)/σ_nul ≤ 3: si la dada en porta molt més, és una altra
    cosa —p. ex. el «ghost» de l'eix òptic a l'apuntament A— i C no l'explica). Si no, no s'aplica (res inventat: sense prova, la C d'aquesta
    estructura no hi entra). També es desa el criteri estricte ((a_k − 0,5)/σ_nul ≥ 2), només informatiu.
Sortida: 4-RESULTATS/v108_20260926/flat2d_v3/flat2d/G1_PORTA_<TREN>.json.  Ús: g1_porta_estructures.py VIXEN|SONYTOT   (només lectura; ~6 GB)"""
import json, sys, time, math, argparse
from pathlib import Path
import numpy as np, cv2
ARREL = Path(__file__).resolve().parents[4]; R3 = ARREL / '4-RESULTATS/v108_20260926/flat2d_v3'; R4 = ARREL / '4-RESULTATS/v108_20260926/flat2d_v4'; CR = ARREL / '4-RESULTATS/v97_refundacio_20260924'
W_, H_ = 10551, 7506; SOL = np.array([5361.768, 3775.748]); RSOL = 440.603; LLUNA = (5375.787, 3775.977); RL = 452.98
AP = {'sony_A': CR / 'cadena_raw/b2_sony_A/cau/sony_A_total_v36.npy', 'sony_B': CR / 'cadena_raw/b2_sony_B/cau/sony_B_total_v42.npy',
      'vixen': CR / 'proves_apilat/vixen_comuna_taula_original/vixen_total.npy', 'sony_AB': ARREL / '4-RESULTATS/v98_20260925/cadena_v98/b3/cau/sony_corrected_total_v42.npy'}
ap = argparse.ArgumentParser(); ap.add_argument('tren', choices=['VIXEN', 'SONYTOT']); ap.add_argument('--dir', default=str(R4 / 'flat2d'))
ap.add_argument('--n-nul', type=int, default=80); a = ap.parse_args(); t0 = time.time(); D = Path(a.dir)
SONY = a.tren == 'SONYTOT'; TAG = 'sony' if SONY else 'vixen'
BANDA = (2.0, 150.0) if SONY else (2.0, 80.0)                    # px del llenç (1 subplà Sony ≈ 3 px; Vixen = 2 px)
MP = json.loads((R3 / 'diag/MAPATGE_V3.json').read_text()); inv = np.array(MP['inv_common_to_final']); TR = MP['trens'][TAG]; dB = MP['delta_B_rad']
Z_ = np.load(D / f'{a.tren}_components_v4.npz'); LAB = Z_['lab']; Wt = Z_['W']; CONT = Z_['cont']; CONTT = Z_['cont_taca']; hs, ws = LAB.shape
EST = json.loads((D / f'ESTRUCTURES_{a.tren}.json').read_text())['estructures']
G1V3 = json.loads((R3 / f'flat2d/G1_PORTA_{a.tren}.json').read_text())
def lnG(p):
    x = np.load(p, mmap_mode='r'); g = np.asarray(x[..., 1], np.float32); ok = np.isfinite(g) & (g > 0)
    return np.where(ok, np.log(np.maximum(g, 1e-20)), 0).astype(np.float32), ok
yy, xx = np.mgrid[0:H_, 0:W_].astype(np.float32); RS = np.hypot(xx - SOL[0], yy - SOL[1]) / RSOL; DL = np.hypot(xx - LLUNA[0], yy - LLUNA[1]) - RL; del yy, xx
def a_sensor(X, Y, g, f):
    """llenç → sensor RAW per al fotograma f del grup g (el mateix codi que b2 / s3)."""
    qx = inv[0, 0] * X + inv[0, 1] * Y + inv[0, 2]; qy = inv[1, 0] * X + inv[1, 1] * Y + inv[1, 2]; dx = (qx - TR['CX']) * TR['k']; dy = (qy - TR['CY']) * TR['k']
    if g == 'sony_B': c_, s_ = math.cos(dB), math.sin(dB); dx, dy = c_ * dx - s_ * dy, s_ * dx + c_ * dy
    return TR['ca'] * dx + TR['sa'] * dy + f['sol_x'], -TR['sa'] * dx + TR['ca'] * dy + f['sol_y']
def plantilla(k, g, marge):
    """T_k al llenç (pegat) per al grup g: mitjana ponderada per exposició del contingut de k mostrejat a cada fotograma."""
    e = next(x for x in EST if x['id'] == k); x0, y0, x1, y1 = e['caixa_subpla']
    Al = np.array(TR['grups'][g]['afi_sensor_a_llenc'])
    cs = np.array([[2 * x0, 2 * y0], [2 * x1, 2 * y0], [2 * x0, 2 * y1], [2 * x1, 2 * y1]], float)
    cl = (Al[:, :2] @ cs.T).T + Al[:, 2]; X0, Y0 = np.floor(cl.min(0) - marge).astype(int); X1, Y1 = np.ceil(cl.max(0) + marge).astype(int)
    X0, Y0 = max(X0, 0), max(Y0, 0); X1, Y1 = min(X1, W_), min(Y1, H_)
    if X1 - X0 < 20 or Y1 - Y0 < 20: return None
    Yp, Xp = np.mgrid[Y0:Y1, X0:X1].astype(np.float32)
    sx0, sy0 = max(x0 - 6, 0), max(y0 - 6, 0); sx1, sy1 = min(x1 + 6, ws), min(y1 + 6, hs)
    src = np.where(LAB[sy0:sy1, sx0:sx1] == k, Wt[sy0:sy1, sx0:sx1] * CONT[sy0:sy1, sx0:sx1], 0).astype(np.float32)
    srt = np.where(LAB[sy0:sy1, sx0:sx1] == k, Wt[sy0:sy1, sx0:sx1] * CONTT[sy0:sy1, sx0:sx1], 0).astype(np.float32)     # v4: la part d'escala de taca
    acc = np.zeros(Yp.shape, np.float64); act = np.zeros(Yp.shape, np.float64); wsum = 0.0
    for f in TR['grups'][g]['fotogrames'].values():
        rx, ry = a_sensor(Xp, Yp, g, f); mx = ((rx - 0.5) / 2 - sx0).astype(np.float32); my = ((ry - 0.5) / 2 - sy0).astype(np.float32)
        acc += f['exp'] * cv2.remap(src, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0); wsum += f['exp']
        act += f['exp'] * cv2.remap(srt, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    return (X0, Y0, X1, Y1), (acc / wsum).astype(np.float32), (act / wsum).astype(np.float32)
grups = ['sony_A', 'sony_B'] if SONY else ['vixen']
REFS = {'sony_A': ['sony_B', 'vixen', None], 'sony_B': ['sony_A', 'vixen', None], 'vixen': ['sony_AB', None]}
res = dict(tren=a.tren, banda_px=BANDA, n_nul=a.n_nul, criteri='aplica si (a − ⟨nul⟩)/σ_nul ≥ 3 i a ≥ 0,5 i (a − 1)/σ_nul ≤ 3; estricte (informatiu): (a − 0,5)/σ_nul ≥ 2', grups={})
rng = np.random.default_rng(20260927)
for g in grups:
    Xt, okt = lnG(AP[g]); dec = {}; Zc = {}
    s1, s2 = BANDA
    for ref in REFS[g]:
        if ref is None: Xr, okr = np.zeros_like(Xt), np.ones_like(okt)
        else: Xr, okr = lnG(AP[ref])
        m = (okt & okr & (DL > 40)).astype(np.float32)
        ng = lambda x, s: cv2.GaussianBlur(x * m, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6)
        z0 = np.where(m > 0, Xt - Xr, 0).astype(np.float32); Zc[ref] = ((ng(z0, s1) - ng(z0, s2)) * m).astype(np.float32), (cv2.erode(m, np.ones((61, 61), np.uint8)) > 0)
        del Xr, okr, z0, m
    del Xt, okt
    for e in EST:
        k = e['id']; p = plantilla(k, g, marge=3 * s2)
        if p is None: dec[str(k)] = dict(aplica=False, motiu='fora del llenç'); continue
        (X0, Y0, X1, Y1), T, TT = p
        if np.abs(T).max() < 1e-7: dec[str(k)] = dict(aplica=False, motiu='fora del llenç'); continue
        o = None
        for ref in REFS[g]:
            Z, okz = Zc[ref]; okp = okz[Y0:Y1, X0:X1]; ET = float((T[okp] ** 2).sum()); ETt = float((T ** 2).sum())
            if ETt <= 0 or ET < 0.9 * ETt: continue           # la referència (o la dada) no cobreix el 90 % de l'energia de la plantilla
            mp = okp.astype(np.float32)
            ngp = lambda x, s: cv2.GaussianBlur(x * mp, (0, 0), s) / np.maximum(cv2.GaussianBlur(mp, (0, 0), s), 1e-6)
            Tb = ((ngp(T, s1) - ngp(T, s2)) * mp).astype(np.float32); ETb = float((Tb.astype(np.float64) ** 2).sum())
            av = float((Z[Y0:Y1, X0:X1].astype(np.float64) * Tb).sum() / ETb)
            Ttb = ((ngp(TT, s1) - ngp(TT, s2)) * mp).astype(np.float32); ETtb = float((Ttb.astype(np.float64) ** 2).sum())     # v4: la de taca, mateixa banda
            avt = float((Z[Y0:Y1, X0:X1].astype(np.float64) * Ttb).sum() / ETtb) if ETtb > 0 else float('nan'); nult = []
            # nul: la mateixa plantilla (en banda) a posicions a l'atzar a la mateixa distància del Sol
            cx, cy = (X0 + X1) / 2, (Y0 + Y1) / 2; r0 = np.hypot(cx - SOL[0], cy - SOL[1]); hw, hh_ = X1 - X0, Y1 - Y0; nul = []; intents = 0
            while len(nul) < a.n_nul and intents < 4000:
                intents += 1; ang = rng.uniform(0, 2 * np.pi); rr_ = r0 * rng.uniform(0.9, 1.1)
                nx, ny = int(SOL[0] + rr_ * np.cos(ang) - hw / 2), int(SOL[1] + rr_ * np.sin(ang) - hh_ / 2)
                if nx < 0 or ny < 0 or nx + hw > W_ or ny + hh_ > H_ or (abs(nx - X0) < hw and abs(ny - Y0) < hh_): continue
                okn = okz[ny:ny + hh_, nx:nx + hw]
                if float((Tb[okn].astype(np.float64) ** 2).sum()) < 0.9 * ETb: continue
                nul.append(float((Z[ny:ny + hh_, nx:nx + hw].astype(np.float64) * Tb * okn).sum() / ETb))
                if ETtb > 0: nult.append(float((Z[ny:ny + hh_, nx:nx + hw].astype(np.float64) * Ttb * okn).sum() / ETtb))
            if len(nul) < 20: continue
            nul = np.array(nul); sd = float(nul.std()); mu = float(nul.mean())
            zp = (av - mu) / sd; zc = (av - 0.5) / sd
            o = dict(ref=ref or 'cap (apilat sol)', a=round(av, 3), nul_mitjana=round(mu, 3), sigma_nul=round(sd, 3), n_nul=int(len(nul)), z_present=round(zp, 2), z_cura=round(zc, 2),
                     s=round(1 - 2 * av, 3), aplica=bool(zp >= 3 and av >= 0.5 and (av - 1) / sd <= 3), aplica_estricte=bool(zc >= 2 and zp >= 3), z_excés=round((av - 1) / sd, 2), centre_llenc=[round(cx, 1), round(cy, 1)], R_sol=round(r0 / RSOL, 2),
                     rms_plantilla_ppm=round(1e4 * float(np.sqrt(ETb / max(okp.sum(), 1))), 3), amplitud_pic_ppm=e['amplitud_pic_ppm'], area_subpla=e['area_subpla'])
            if len(nult) >= 20:   # v4: la plantilla de taca, sense arrodonir (va a l'encongiment)
                nult = np.array(nult); sdt = float(nult.std()); mut = float(nult.mean())
                o.update(a_taca=avt, nul_mitjana_taca=mut, sigma_nul_taca=sdt, n_nul_taca=int(len(nult)), z_present_taca=round((avt - mut) / sdt, 3), z_excés_taca=round((avt - mut - 1) / sdt, 3),
                         rms_plantilla_taca_ppm=round(1e4 * float(np.sqrt(ETtb / max(okp.sum(), 1))), 3), fraccio_energia_taca=round(ETtb / ETb, 4), escala_subpla=e['escala_subpla'])
            break
        if o is None: o = dict(aplica=False, motiu='cap referència ni dada que cobreixi la plantilla')
        dec[str(k)] = o
    # CONTROL: la plantilla sencera = la porta de la v3, camp a camp
    d3 = G1V3['grups'][g]['decisions']; CAMPS = [c for c in next(iter(v for v in d3.values() if 'a' in v)).keys()]
    dif = [k for k in d3 if {c: d3[k].get(c) for c in CAMPS} != {c: dec[k].get(c) for c in CAMPS}]
    print(g, 'CONTROL porta v3 refeta: estructures diferents', len(dif), dif[:5], flush=True)
    if dif: sys.exit(f'ATURAT: la plantilla sencera no dona la porta de la v3 ({g}: {dif[:5]})')
    n_ap = sum(1 for d in dec.values() if d.get('aplica')); n_t = sum(1 for d in dec.values() if 'a' in d)
    res['grups'][g] = dict(n_estructures=len(EST), n_provades=n_t, n_aplicades=n_ap, decisions=dec)
    print(g, 'provades', n_t, 'aplicades', n_ap, f'{time.time()-t0:.0f}s', flush=True)
    for kk, d in sorted(dec.items(), key=lambda kv: -abs(kv[1].get('amplitud_pic_ppm', 0) or 0))[:25]: print('  ', kk, d, flush=True)
    del Zc
res['control_v3'] = 'plantilla sencera = G1_PORTA_' + a.tren + ' de la v3, camp a camp (si no, ATURAT)'
(D / f'G1_PORTA_V4_{a.tren}.json').write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n'); print('FET', f'{time.time()-t0:.0f}s')
