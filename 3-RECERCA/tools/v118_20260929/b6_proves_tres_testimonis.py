"""b6 (V118, 29-09-2026) · Proves del filtre de tres testimonis (b5), només amb la nostra dada:
  1. INJECCIÓ (norma de portes de senyal feble; com el b2b de la V117): raigs sintètics multiplicatius (L' = L·e^s), perfil azimutal gaussià
     σ 0,2°, de 2,0 a 5,5 R☉ (extrems suaus), ±0,5 % en ln; 8 raigs de cada tipus, signes alternats:
       A, B, V (un sol testimoni: ideal, passa 0) · AB (A i B però no la Vixen: el que faria un defecte de la lent de 300 mm, que A i B comparteixen;
       ideal 0) · ABV (cel: ideal, passa 1).
     Fracció que passa = projecció de Δ(detall filtrat) sobre el perfil / projecció de Δ(detall del testimoni injectat), a ±1°. Es dona per al
     filtre de tres (V118) i per al mínim concordant A·B de la V117 calculat amb les mateixes entrades.
  2. CONTROL NUL: la Vixen girada 5° al voltant del Sol (més que l'escala més gran del filtre): la coincidència de tres ha de caure a ~0.
  3. RASTRE D'ESTRELLES: a les 56 estrelles del catàleg V114, rms del detall filtrat a l'anell de 26–40 px (just fora del peu) dividit pel
     del mateix anell girat ±4° al voltant del Sol (sense estrella), per a la 415 de la V117 i per a la capa nova.
Ús: b6_proves_tres_testimonis.py <carpeta_b5> <carpeta_sortida>  → B6_PROVES.json"""
import sys, json, importlib.util, numpy as np, cv2
from pathlib import Path
B5D, OUT = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(); OUT.mkdir(parents=True, exist_ok=True)
sys.argv = [sys.argv[0], str(OUT)]
spec = importlib.util.spec_from_file_location('b5', Path(__file__).with_name('b5_filtre_tres_testimonis.py')); b5 = importlib.util.module_from_spec(spec); spec.loader.exec_module(b5)
b1, R, H, W, SOL, RS = b5.b1, b5.R, b5.H, b5.W, b5.SOL, b5.RS
HALO = json.load(open(B5D / 'B5_AJUSTOS_ESTRELLES.json'))['halo']; RADIS = {tuple(int(v) for v in k.split(',')): d['radi'] for k, d in HALO.items()}
LA, LB, LV, m, _ = b5.entrades(RADIS)          # els mateixos peus que la capa (radi d'halo de cada estrella)
PM0, DA0, DB0, DV0, w30, D30, wp0 = b5.nucli3(LA, LB, LV, m)
def dmin_ab(DA, DB, w): return (w * np.where(DA * DB > 0, np.sign(DA) * np.minimum(np.abs(DA), np.abs(DB)), 0)).astype(np.float32)
DAB0 = dmin_ab(DA0, DB0, wp0['A·B'])
rrp = np.exp(b1.rho) / RS; out = {}
# 2. control nul
M_ = cv2.getRotationMatrix2D(SOL, 5.0, 1.0); rot = lambda x: cv2.warpAffine(x, M_, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
mn = m & (rot(m.astype(np.float32)) > 0.999)
PMn, _, _, _, w3n, _, wpn = b5.nucli3(LA, LB, rot(LV), mn)
out['2_control_nul_vixen_girada_5graus'] = {}
for a, b in ((1.3, 2), (2, 3.5), (3.5, 5.5)):
    k0 = PM0 & ((rrp >= a) & (rrp < b))[:, None]; kn = PMn & ((rrp >= a) & (rrp < b))[:, None]
    out['2_control_nul_vixen_girada_5graus'][f'{a}-{b}'] = dict(tres_registrat=round(float(np.median(w30[k0])), 3), tres_girada=round(float(np.median(w3n[kn])), 3),
                                                                 AV_registrat=round(float(np.median(wp0['A·V'][k0])), 3), AV_girada=round(float(np.median(wpn['A·V'][kn])), 3))
print('nul', json.dumps(out['2_control_nul_vixen_girada_5graus']), flush=True)
del PMn, w3n, wpn
# 1. injecció
rows = (rrp >= 2.0) & (rrp <= 5.5); cob = PM0[rows].mean(0)
cands = [int(j) for j in np.argsort(-cob) if cob[j] >= 0.95]; tria = []
for j in cands:
    if all(min(abs(j - k), b1.NT - abs(j - k)) * 360 / b1.NT >= 5 for k in tria): tria.append(j)
    if len(tria) == 40: break
n = len(tria) // 5; tria = sorted(tria[:5 * n]); assert n >= 6, f'només {len(tria)} azimuts amb camp comú'
TIPUS = ['A', 'B', 'V', 'AB', 'ABV'] * n; SIGNE = [(+1 if (i // 5) % 2 == 0 else -1) for i in range(5 * n)]
AMP, SIG_T = 0.005, np.radians(0.2)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); rr = np.hypot(xx - SOL[0], yy - SOL[1]) / RS; tt = np.mod(np.arctan2(-(yy - SOL[1]), xx - SOL[0]), 2 * np.pi); del yy, xx
def smooth(x, a, c): t = np.clip((x - a) / (c - a), 0, 1); return t * t * (3 - 2 * t)
env = (smooth(rr, 2.0, 2.3) * (1 - smooth(rr, 5.2, 5.5))).astype(np.float32); del rr
s = {k: np.zeros((H, W), np.float32) for k in 'ABV'}
for j, tp, sg in zip(tria, TIPUS, SIGNE):
    t0 = j * 2 * np.pi / b1.NT; dt = np.angle(np.exp(1j * (tt - t0))).astype(np.float32); prof = (sg * AMP * np.exp(-0.5 * (dt / SIG_T) ** 2)).astype(np.float32) * env
    for k in 'ABV':
        if k in tp: s[k] += prof
del tt
PM1, DA1, DB1, DV1, w31, D31, wp1 = b5.nucli3(LA * np.exp(s['A']), LB * np.exp(s['B']), LV * np.exp(s['V']), m); DAB1 = dmin_ab(DA1, DB1, wp1['A·B'])
HW = int(np.radians(1.0) / (2 * np.pi / b1.NT)); kk = np.arange(-HW, HW + 1); pesos = np.exp(-0.5 * (kk * (2 * np.pi / b1.NT) / SIG_T) ** 2)
out['1_injeccio'] = dict(amplitud_ln=AMP, sigma_graus=0.2, raigs_per_tipus=n, azimuts_graus=[round(j * 360 / b1.NT, 2) for j in tria], tipus=TIPUS, signe=SIGNE, bandes={})
for a, b in ((2.0, 3.5), (3.5, 5.5)):
    rw = (rrp >= a + 0.1) & (rrp <= b - 0.1); o = {}
    for tp in ('A', 'B', 'V', 'AB', 'ABV'):
        f3, fab = [], []
        for j, t_ in zip(tria, TIPUS):
            if t_ != tp: continue
            cols = (j + kk) % b1.NT; ok = rw[:, None] & PM0[:, cols] & PM1[:, cols]
            def proj(X1, X0): return float(np.sum(np.where(ok, (X1[:, cols] - X0[:, cols]) * pesos[None, :], 0)))
            ref = proj(DA1, DA0) if 'A' in tp else (proj(DB1, DB0) if tp == 'B' else proj(DV1, DV0))
            f3.append(proj(D31, D30) / ref); fab.append(proj(DAB1, DAB0) / ref)
        q = lambda v: [round(float(x), 3) for x in np.percentile(v, [25, 50, 75])]
        o[tp] = dict(tres_q25_q50_q75=q(f3), tres_max=round(float(np.max(f3)), 3), AB_V117_q25_q50_q75=q(fab), AB_V117_max=round(float(np.max(fab)), 3),
                     per_raig_tres=[round(v, 3) for v in f3], per_raig_AB=[round(v, 3) for v in fab])
    out['1_injeccio']['bandes'][f'{a}-{b}'] = o
    print(f'{a}–{b} R☉ (mediana, màx): ' + ' · '.join(f'{tp}: tres {o[tp]["tres_q25_q50_q75"][1]:.2f} ({o[tp]["tres_max"]:.2f}), A·B {o[tp]["AB_V117_q25_q50_q75"][1]:.2f} ({o[tp]["AB_V117_max"]:.2f})' for tp in o), flush=True)
del PM1, DA1, DB1, DV1, w31, D31, wp1, DAB1
# 3. rastre d'estrelles
cat = json.load(open(R / '4-RESULTATS/v114_estrelles_20260928/CATALEG_ACCEPTAT_V114.json'))['stars']
D117 = np.load(R / '4-RESULTATS/v117_20260929/AB/b1/D_minim_f32.npy', mmap_mode='r'); D118 = np.load(B5D / 'D_minim_f32.npy', mmap_mode='r')
PT = np.array(list(RADIS.keys()), float)
def anell(D, x, y, a, b):
    x, y = int(round(x)), int(round(y))
    if x < b or y < b or x + b + 1 > W or y + b + 1 > H: return None
    yy, xx = np.mgrid[-b:b + 1, -b:b + 1]; k = (np.hypot(xx, yy) >= a) & (np.hypot(xx, yy) <= b)
    v = np.asarray(D[y - b:y + b + 1, x - b:x + b + 1], np.float32)[k]; v = v[v != 0]
    return float(np.sqrt(np.mean(v ** 2))) if v.size > 200 else None
res = {'V117_415': [], 'V118_nova': []}; per = []
for st in cat:
    x, y = st['x'], st['y']; r_ = np.hypot(x - SOL[0], y - SOL[1]); th = np.arctan2(-(y - SOL[1]), x - SOL[0])
    j = int(np.argmin(np.hypot(PT[:, 0] - x, PT[:, 1] - y))); rs = RADIS[tuple(int(v) for v in PT[j])] if np.hypot(PT[j, 0] - x, PT[j, 1] - y) < 6 else b5.R_PEU
    a, b = rs + 1, rs + 15
    ctl = [(SOL[0] + r_ * np.cos(th + d), SOL[1] - r_ * np.sin(th + d)) for d in (np.radians(4), -np.radians(4))]
    fila = dict(TYC=st.get('TYC'), V=st.get('V'), r_Rsol=round(float(r_ / RS), 2), radi_peu=rs)
    q = {}
    for nom, D in (('V117_415', D117), ('V118_nova', D118)):
        a0 = anell(D, x, y, a, b); cc = [c for c in (anell(D, *p_, a, b) for p_ in ctl) if c]
        if a0 and cc: q[nom] = a0 / np.mean(cc)
    if len(q) == 2:                                   # només les estrelles on es poden comparar totes dues capes
        for nom, v in q.items(): res[nom].append(v); fila[nom] = round(v, 2)
    per.append(fila)
out['3_rastre_estrelles'] = dict(metrica='rms del detall filtrat a l\'anell just fora del peu de la V118 (radi+1 a radi+15 px) / el mateix anell girat ±4° (1 = cap rastre); parelles: les mateixes estrelles a les dues capes',
                                 **{k: dict(estrelles=len(v), p50=round(float(np.median(v)), 2), p90=round(float(np.percentile(v, 90)), 2), max=round(float(np.max(v)), 2)) for k, v in res.items() if v},
                                 per_estrella=per)
print('estrelles', json.dumps({k: v for k, v in out['3_rastre_estrelles'].items() if k != 'per_estrella'}, ensure_ascii=False), flush=True)
(OUT / 'B6_PROVES.json').write_text(json.dumps(out, ensure_ascii=False, indent=1))
