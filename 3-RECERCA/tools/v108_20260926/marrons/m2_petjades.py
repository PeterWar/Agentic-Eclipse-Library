"""m2 · Petjades dels fotogrames i vores dels pesos, com a rectes al llenç, i quines coincideixen amb cada traç marró.
Fonts (només lectura): cadena_raw/sources_v36/cau/{sony,vixen}_w.npy (pes per fotograma a 1/4, graella del llenç), sony_meta/vixen_meta;
cadena_v98/b3/cau (sony_fA, weight_vixen, support). Per a cada fotograma: contorn de w>0 → segments rectes (approxPolyDP).
Coincidència amb un traç: |angle| < 3°, distància perpendicular del centre del traç a la recta < 250 px i solapament al llarg > 30 %.
Sortida: M2_PETJADES.json (tots els segments i les coincidències) i M2_petjades.npz (comptadors de fotogrames a 1/4)."""
import sys, json
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent)); from comu_marrons import *
CR = ARREL / '4-RESULTATS/v97_refundacio_20260924/cadena_raw/sources_v36/cau'; B3 = ARREL / '4-RESULTATS/v98_20260925/cadena_v98/b3/cau'
Q = 4
def segments(mask, nom, eps=3.0, min_len=60):
    """Contorn exterior d'una màscara a 1/4 → segments rectes al llenç (px complets)."""
    cnt, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    out = []
    for c in cnt:
        if len(c) < 20: continue
        ap = cv2.approxPolyDP(c, eps, True)[:, 0, :].astype(float)
        for i in range(len(ap)):
            p = ap[i] * Q + Q / 2 - 0.5; q = ap[(i + 1) % len(ap)] * Q + Q / 2 - 0.5
            L = np.hypot(*(q - p))
            if L < min_len: continue
            # la vora del llenç no és una vora de la dada
            if (min(p[0], q[0]) < 8 and max(p[0], q[0]) < 8) or (min(p[1], q[1]) < 8 and max(p[1], q[1]) < 8) or (min(p[0], q[0]) > W - 12) or (min(p[1], q[1]) > H - 12): continue
            out.append(dict(font=nom, p=p.round(1).tolist(), q=q.round(1).tolist(), llarg=float(L), angle=float(np.degrees(np.arctan2(q[1] - p[1], q[0] - p[0])) % 180)))
    return out
def coincideix(tr, sg, tol_ang=3.0, tol_d=250):
    a_tr = np.degrees(np.arctan2(tr['d'][1], tr['d'][0])) % 180; da = abs((sg['angle'] - a_tr + 90) % 180 - 90)
    if da > tol_ang: return None
    p = np.array(sg['p']); q = np.array(sg['q']); u = (q - p) / np.linalg.norm(q - p); nn = np.array([-u[1], u[0]])
    dperp = float((tr['centre'] - p) @ nn)
    if abs(dperp) > tol_d: return None
    # solapament al llarg del traç
    s_p = (p - tr['centre']) @ tr['d']; s_q = (q - tr['centre']) @ tr['d']; lo, hi = min(s_p, s_q), max(s_p, s_q)
    ov = max(0.0, min(hi, tr['llarg'] / 2) - max(lo, -tr['llarg'] / 2)) / tr['llarg']
    if ov < 0.3: return None
    # distància amb signe del traç (en la seva normal n) a la recta
    t_rel = float((p - tr['centre']) @ tr['n'] + ((tr['centre'] - p) @ u) * (u @ tr['n']))
    return dict(dangle=float(da), dist_perp=abs(dperp), t_en_normal_del_traç=t_rel, solapament=float(ov))
segs = []; comptes = {}
for tren in ('sony', 'vixen'):
    meta = json.loads((CR / f'{tren}_meta.json').read_text())['frames']; w = np.load(CR / f'{tren}_w.npy', mmap_mode='r')
    cnt = np.zeros(w.shape[1:], np.int16); cnt_llarg = np.zeros(w.shape[1:], np.int16)
    for j, m in enumerate(meta):
        mk = np.asarray(w[j]) > 0
        if mk.sum() < 10000: continue      # fotogrames curtíssims (només el limbe): no fan vores al camp
        cnt += mk; cnt_llarg += mk & (m['exp'] >= 0.25)
        for s in segments(mk, f"{tren}:{m['group']}:{m['name']}:{m['exp']}s"): segs.append(s)
    comptes[tren] = cnt; comptes[tren + '_llargs'] = cnt_llarg
    print(tren, 'fotogrames', len(meta), 'segments', sum(1 for s in segs if s['font'].startswith(tren)), flush=True)
# vores dels pesos de la fusió (a 1/4)
fA = np.load(B3 / 'sony_fA_v42.npy', mmap_mode='r')[::Q, ::Q]; wv = np.load(B3 / 'weight_vixen_v42.npy', mmap_mode='r')[::Q, ::Q]; sup = np.load(B3 / 'support_v42.npy', mmap_mode='r')[::Q, ::Q]
for nom, arr in (('fusio:fA', fA), ('fusio:wv', wv)):
    for lv in (0.02, 0.5, 0.98):
        for s in segments(np.asarray(arr) > lv, f'{nom}>{lv}', eps=6, min_len=200): segs.append(s)
for s in segments(np.asarray(sup), 'fusio:suport', eps=4, min_len=200): segs.append(s)
res = {}
for tr in TRACOS:
    c = []
    for s in segs:
        q = coincideix(tr, s)
        if q: c.append(dict(s, **q))
    c.sort(key=lambda z: z['dist_perp']); res[tr['k']] = dict(nom=tr['nom'], coincidencies=c)
    print(f"T{tr['k']} {tr['nom']}: {len(c)} coincidències")
    for z in c[:12]: print('   ', z['font'], f"dθ {z['dangle']:.2f}° d⊥ {z['dist_perp']:.0f} px sol {z['solapament']:.2f}", z['p'], z['q'])
desa(OUT / 'M2_PETJADES.json', dict(segments=segs, tracos=res))
np.savez_compressed(OUT / 'M2_petjades.npz', **{k: v for k, v in comptes.items()})
