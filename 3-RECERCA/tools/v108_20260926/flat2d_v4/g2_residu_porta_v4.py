"""g2_residu_porta_v4 (V108, flat2d_v4) · QUANT EN QUEDA, DE CADA ESTRUCTURA, DESPRÉS DE CORREGIR? La mesura de la porta (g1_porta_v4: mateixes
plantilles —sencera i de taca—, mateixa banda, mateixa referència) repetida sobre els apilats CORREGITS de la v3 i de la v4, amb el cel anul·lat.
  Sony A: Z_v = ln A_v − ln B_v; Sony B: ln B_v − ln A_v (si g1 va fer servir la Vixen, ln X_v − ln Vixen_v; si l'apilat sol, ln X_v);
  Vixen: ln V_v − ln S (S = la Sony A+B corregida del control, fixa, la mateixa referència que g1).
  a_v = ⟨Z_v, T⟩/⟨T, T⟩: al control és la a de g1 (CONTROL: ha de coincidir); després de corregir hauria de quedar a − (el que s'ha aplicat):
  v3: rebutjades ≈ a (no s'hi toca), aplicades ≈ a − 1; v4: rebutjades ≈ a − â. Cura del grup = la mitjana ponderada (1/σ²) de la a que queda.
  σ de cada estructura: la σ_nul de g1 (mateixa Z, mateixa plantilla, mateixes posicions).
  Versió «a0» (prova_a0/apilats: la C de la v4 amb â = 0 a totes les rebutjades, és a dir, amb la textura i el fons de la petjada aplicats i
  la taca no): el que en queda és la PRESÈNCIA DE LA TACA a la dada un cop tret tot el que ja està validat (r0); és el que encongeix h1.
Sortida: 4-RESULTATS/v108_20260926/flat2d_v4/G2_RESIDU_PORTA[_<etiqueta>].json.
Ús: g2_residu_porta_v4.py VIXEN|SONYTOT [versions, per defecte control,v3,v4] [etiqueta]   (només lectura; ~9 GB)"""
import json, sys, time, math
from pathlib import Path
import numpy as np, cv2
ARREL = Path(__file__).resolve().parents[4]; R3 = ARREL / '4-RESULTATS/v108_20260926/flat2d_v3'; R4 = ARREL / '4-RESULTATS/v108_20260926/flat2d_v4'; CR = ARREL / '4-RESULTATS/v97_refundacio_20260924'
W_, H_ = 10551, 7506; SOL = np.array([5361.768, 3775.748]); RSOL = 440.603; LLUNA = (5375.787, 3775.977); RL = 452.98
TREN = sys.argv[1]; VERS = (sys.argv[2] if len(sys.argv) > 2 else 'control,v3,v4').split(','); ETQ = sys.argv[3] if len(sys.argv) > 3 else ''; SONY = TREN == 'SONYTOT'; TAG = 'sony' if SONY else 'vixen'; BANDA = (2.0, 150.0) if SONY else (2.0, 80.0); t0 = time.time()
AP = {'control': {'sony_A': CR / 'cadena_raw/b2_sony_A/cau/sony_A_total_v36.npy', 'sony_B': CR / 'cadena_raw/b2_sony_B/cau/sony_B_total_v42.npy', 'vixen': CR / 'proves_apilat/vixen_comuna_taula_original/vixen_total.npy'},
      'v3': {'sony_A': R3 / 'apilats/sony_A_total.npy', 'sony_B': R3 / 'apilats/cau/sony_B_total_v42.npy', 'vixen': R3 / 'apilats/vixen_total.npy'},
      'v4': {'sony_A': R4 / 'apilats/sony_A_total.npy', 'sony_B': R4 / 'apilats/cau/sony_B_total_v42.npy', 'vixen': R4 / 'apilats/vixen_total.npy'},
      'a0': {'sony_A': R4 / 'prova_a0/apilats/sony_A_total.npy', 'sony_B': R4 / 'prova_a0/apilats/cau/sony_B_total_v42.npy', 'vixen': R4 / 'prova_a0/apilats/vixen_total.npy'}}
assert VERS[0] == 'control', 'la primera versió ha de ser el control (és el control de la mesura)'
SONY_AB = ARREL / '4-RESULTATS/v98_20260925/cadena_v98/b3/cau/sony_corrected_total_v42.npy'
MP = json.loads((R3 / 'diag/MAPATGE_V3.json').read_text()); inv = np.array(MP['inv_common_to_final']); TRM = MP['trens'][TAG]; dB = MP['delta_B_rad']
Z_ = np.load(R4 / f'flat2d/{TREN}_components_v4.npz'); LAB = Z_['lab']; Wt = Z_['W']; CONT = Z_['cont']; CONTT = Z_['cont_taca']; hs, ws = LAB.shape
EST = {e['id']: e for e in json.loads((R4 / f'flat2d/ESTRUCTURES_{TREN}.json').read_text())['estructures']}
G1 = json.loads((R4 / f'flat2d/G1_PORTA_V4_{TREN}.json').read_text()); H1 = json.loads((R4 / f'flat2d/H1_ENCONGIDA{"_ZERO" if ETQ == "a0" else ""}_{TREN}.json').read_text())   # la regla i la â aplicades (a0: totes 0)
def lnG(p):
    x = np.load(p, mmap_mode='r'); g = np.asarray(x[..., 1], np.float32); ok = np.isfinite(g) & (g > 0)
    return np.where(ok, np.log(np.maximum(g, 1e-20)), 0).astype(np.float32), ok
yy, xx = np.mgrid[0:H_, 0:W_].astype(np.float32); DL = np.hypot(xx - LLUNA[0], yy - LLUNA[1]) - RL; del yy, xx
def a_sensor(X, Y, g, f):
    qx = inv[0, 0] * X + inv[0, 1] * Y + inv[0, 2]; qy = inv[1, 0] * X + inv[1, 1] * Y + inv[1, 2]; dx = (qx - TRM['CX']) * TRM['k']; dy = (qy - TRM['CY']) * TRM['k']
    if g == 'sony_B': c_, s_ = math.cos(dB), math.sin(dB); dx, dy = c_ * dx - s_ * dy, s_ * dx + c_ * dy
    return TRM['ca'] * dx + TRM['sa'] * dy + f['sol_x'], -TRM['sa'] * dx + TRM['ca'] * dy + f['sol_y']
def plantilla(k, g, marge):
    e = EST[k]; x0, y0, x1, y1 = e['caixa_subpla']; Al = np.array(TRM['grups'][g]['afi_sensor_a_llenc'])
    cs = np.array([[2 * x0, 2 * y0], [2 * x1, 2 * y0], [2 * x0, 2 * y1], [2 * x1, 2 * y1]], float)
    cl = (Al[:, :2] @ cs.T).T + Al[:, 2]; X0, Y0 = np.floor(cl.min(0) - marge).astype(int); X1, Y1 = np.ceil(cl.max(0) + marge).astype(int)
    X0, Y0 = max(X0, 0), max(Y0, 0); X1, Y1 = min(X1, W_), min(Y1, H_)
    Yp, Xp = np.mgrid[Y0:Y1, X0:X1].astype(np.float32)
    sx0, sy0 = max(x0 - 6, 0), max(y0 - 6, 0); sx1, sy1 = min(x1 + 6, ws), min(y1 + 6, hs)
    src = np.where(LAB[sy0:sy1, sx0:sx1] == k, Wt[sy0:sy1, sx0:sx1] * CONT[sy0:sy1, sx0:sx1], 0).astype(np.float32)
    srt = np.where(LAB[sy0:sy1, sx0:sx1] == k, Wt[sy0:sy1, sx0:sx1] * CONTT[sy0:sy1, sx0:sx1], 0).astype(np.float32)
    acc = np.zeros(Yp.shape, np.float64); act = np.zeros(Yp.shape, np.float64); wsum = 0.0
    for f in TRM['grups'][g]['fotogrames'].values():
        rx, ry = a_sensor(Xp, Yp, g, f); mx = ((rx - 0.5) / 2 - sx0).astype(np.float32); my = ((ry - 0.5) / 2 - sy0).astype(np.float32)
        acc += f['exp'] * cv2.remap(src, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0); wsum += f['exp']
        act += f['exp'] * cv2.remap(srt, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    return (X0, Y0, X1, Y1), (acc / wsum).astype(np.float32), (act / wsum).astype(np.float32)
def mp(a, s):
    a, s = np.asarray(a, float), np.asarray(s, float); k = np.isfinite(a) & np.isfinite(s) & (s > 0)
    if not k.any(): return None
    w = 1 / s[k] ** 2; m = float((w * a[k]).sum() / w.sum()); e = float(1 / np.sqrt(w.sum())); return dict(a=round(m, 4), err=round(e, 4), z=round(m / e, 2), n=int(k.sum()))
s1, s2 = BANDA; out = dict(tren=TREN, banda_px=BANDA, grups={})
for g in (['sony_A', 'sony_B'] if SONY else ['vixen']):
    dec = G1['grups'][g]['decisions']; hh = H1['grups'][g]['estructures']; prov = [k for k in dec if 'a_taca' in dec[k]]
    refs_usades = sorted({dec[k]['ref'] for k in prov}); res_k = {k: {} for k in prov}
    PL = {k: plantilla(int(k), g, marge=3 * s2) for k in prov}; print(g, 'plantilles', len(PL), f'{time.time()-t0:.0f}s', flush=True)
    for v in VERS:
        Xt, okt = lnG(AP[v][g]); Zc = {}
        for ref in refs_usades:
            if ref.startswith('cap'): Xr, okr = np.zeros_like(Xt), np.ones_like(okt)
            elif ref == 'sony_AB': Xr, okr = lnG(SONY_AB)
            else: Xr, okr = lnG(AP[v][ref])
            m = (okt & okr & (DL > 40)).astype(np.float32)
            ng = lambda x, s: cv2.GaussianBlur(x * m, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6)
            z0 = np.where(m > 0, Xt - Xr, 0).astype(np.float32); Zc[ref] = ((ng(z0, s1) - ng(z0, s2)) * m).astype(np.float32), (cv2.erode(m, np.ones((61, 61), np.uint8)) > 0)
            del Xr, okr, z0, m
        del Xt, okt
        for k in prov:
            (X0, Y0, X1, Y1), T, TT = PL[k]; Z, okz = Zc[dec[k]['ref']]; okp = okz[Y0:Y1, X0:X1]; mpp = okp.astype(np.float32)
            ngp = lambda x, s: cv2.GaussianBlur(x * mpp, (0, 0), s) / np.maximum(cv2.GaussianBlur(mpp, (0, 0), s), 1e-6)
            Tb = ((ngp(T, s1) - ngp(T, s2)) * mpp).astype(np.float32); Ttb = ((ngp(TT, s1) - ngp(TT, s2)) * mpp).astype(np.float32); Zp = Z[Y0:Y1, X0:X1].astype(np.float64)
            res_k[k][v] = dict(a=float((Zp * Tb).sum() / (Tb.astype(np.float64) ** 2).sum()), a_taca=float((Zp * Ttb).sum() / max((Ttb.astype(np.float64) ** 2).sum(), 1e-30)))
        del Zc; print(g, v, f'{time.time()-t0:.0f}s', flush=True)
    ctl = max(abs(res_k[k]['control']['a'] - dec[k]['a']) for k in prov); ctlt = max(abs(res_k[k]['control']['a_taca'] - dec[k]['a_taca']) for k in prov)
    print(g, 'CONTROL: |a_control − a de g1| màx', round(ctl, 4), '(arrodonit a 0,001 a g1) · taca', ctlt, flush=True)
    if ctl > 0.002 or ctlt > 1e-6: sys.exit(f'ATURAT: la mesura del control no reprodueix g1 ({g})')
    o = dict(control_g1_max_dif=dict(a=ctl, a_taca=ctlt), estructures={})
    for grup, sel in (('rebutjades_v3', [k for k in prov if not dec[k]['aplica'] and dec[k]['z_excés_taca'] <= 3]), ('aplicades_v3', [k for k in prov if dec[k]['aplica']]),
                      ('rebutjades_v3_amb_exces', [k for k in prov if not dec[k]['aplica'] and dec[k]['z_excés_taca'] > 3])):
        if not sel: continue
        st = [dec[k]['sigma_nul_taca'] for k in sel]; sp = [dec[k]['sigma_nul'] for k in sel]
        o[grup] = {v: dict(taca=mp([res_k[k][v]['a_taca'] - dec[k]['nul_mitjana_taca'] for k in sel], st), plena=mp([res_k[k][v]['a'] - dec[k]['nul_mitjana'] for k in sel], sp)) for v in VERS}
        o[grup]['aplicat_mitjana'] = round(float(np.mean([hh[k]['a_encongida'] for k in sel])), 4)
        print(g, grup, json.dumps(o[grup]), flush=True)
    for k in prov:
        o['estructures'][k] = dict(regla=hh[k]['regla'], a_aplicada=hh[k].get('a_encongida'), sigma_taca=round(dec[k]['sigma_nul_taca'], 4), centre_llenc=dec[k]['centre_llenc'],
                                   **{f'a_taca_{v}': round(res_k[k][v]['a_taca'] - dec[k]['nul_mitjana_taca'], 4) for v in VERS},
                                   **{f'a_plena_{v}': round(res_k[k][v]['a'] - dec[k]['nul_mitjana'], 4) for v in VERS})
    out['grups'][g] = o
p = R4 / f'G2_RESIDU_PORTA{"_" + ETQ if ETQ else ""}.json'; prev = json.loads(p.read_text()) if p.exists() else {}; prev[TREN] = out
p.write_text(json.dumps(prev, ensure_ascii=False, indent=1) + '\n'); print('FET', f'{time.time()-t0:.0f}s')
