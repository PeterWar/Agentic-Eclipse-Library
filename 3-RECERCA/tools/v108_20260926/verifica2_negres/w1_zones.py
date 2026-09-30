"""w1 (V108 · verifica2_negres) · Zones negres, cel, control nul i RECTIFICACIÓ, amb compositor i mètrica PROPIS (pas 2, llenç sencer).
Referències de cel (mediana per sector de 10°, SENSE mediana mòbil, del compost suavitzat 6 px del llenç):
  A  = 6,5–8,5 R☉ a tot el llenç vàlid (com la ronda 1);  B = 5,0–5,6 R☉ dins del marc (com el verificador 1);
  Afix / Bfix = la referència de la V107 aplicada també al candidat (vara fixa: separa «la corona puja» de «el cel baixa»).
També: el mateix sobre el FUSIONAT del PSB × F_nou/F_vell (41·42), independent de qualsevol emulació.
Ús: w1_zones.py [carpeta_candidat]"""
import sys, json, struct, time
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent))
from w0_comu import *
T0 = time.time()
CAND = Path(sys.argv[1]) if len(sys.argv) > 1 else R0 / '4-RESULTATS/v108_20260926/negres_v2/candidats_v4/CEL_G_MAX_T_e30_W_H0'
NOM = CAND.name; PAS = 2
G = geo(pas=PAS); r, th, ok, marc = G['r'], G['th'], G['ok'], G['marc']
Z = ok & marc & (r >= 1.3) & (r < 4.5)
p0 = OUT / 'L_V107_w0_pas2.npy'
if p0.exists(): L0 = np.load(p0)
else: L0 = compon(pas=PAS); np.save(p0, L0)
p1 = OUT / f'L_{NOM}_w0_pas2.npy'
if p1.exists(): L1 = np.load(p1)
else: L1 = compon(pas=PAS, cand=CAND); np.save(p1, L1)
print('composts', round(time.time() - T0), 's', flush=True)
res = dict(candidat=str(CAND))
# --- comparació amb l'emulació de l'agent (a1, pas2) ---
A1 = R0 / '4-RESULTATS/v108_20260926/negres_v2/pas2'
for nom, L, f in (('V107', L0, 'L_V107.npy'), ('cand', L1, 'L_v4_CEL_G_MAX_T_e30_W_H0.npy')):
    if (A1 / f).exists():
        La = np.load(A1 / f); m = Z & (La > 1e-4)
        res[f'emulacio_propia_vs_agent_{nom}'] = dict(corr_lnL=float(np.corrcoef(np.log(L[m]), np.log(La[m]))[0, 1]), quocient_p1_p50_p99=[float(q) for q in np.percentile(L[m] / La[m], [1, 50, 99])])


def cel_sector(Ls, valid, ra, rb):
    s = valid & (r >= ra) & (r < rb) & (Ls > 1e-4); sec = (th // 10).astype(int) % 36
    v = np.array([np.median(Ls[s & (sec == i)]) if (s & (sec == i)).sum() > 200 else np.nan for i in range(36)])
    g = np.isfinite(v); ii = np.arange(36); v = np.interp(ii, ii[g], v[g], period=36)
    return v


def camp(v):
    x = th / 10 - 0.5; i0 = np.floor(x).astype(int) % 36; f = (x - np.floor(x)).astype(np.float32)
    return ((1 - f) * v[i0] + f * v[(i0 + 1) % 36]).astype(np.float32)


def zones(L, vfix=None):
    Ls = cv2.GaussianBlur(L, (0, 0), 6.0 / PAS); o = {}
    vA = cel_sector(Ls, ok, 6.5, 8.5); vB = cel_sector(Ls, ok & marc, 5.0, 5.6)
    refs = {'A': vA, 'B': vB}
    if vfix: refs.update({'Afix': vfix['A'], 'Bfix': vfix['B']})
    for k, v in refs.items():
        neg = Z & (Ls < camp(v)); d = dict(total=float(neg.sum() / Z.sum()))
        for a, b in ((1.3, 2), (2, 3), (3, 4.5)):
            m = Z & (r >= a) & (r < b); d[f'{a:g}-{b:g}'] = float(neg[m].mean())
        d['sectors45'] = [float(neg[Z & (th >= s) & (th < s + 45)].mean()) for s in range(0, 360, 45)]
        o[k] = d
    sky = camp(vA); o['A']['pixel_a_pixel'] = float((L[Z] < sky[Z]).mean())
    o['cel_A_max_min'] = float(vA.max() / vA.min()); o['cel_B_max_min'] = float(vB.max() / vB.min())
    return o, refs


z0, ref0 = zones(L0); z1, _ = zones(L1, ref0)
res['zones_V107'] = z0; res['zones_cand'] = z1
# --- cel que es veu (dalt / baix) ---
def cel_veu(L):
    o = {}
    for nom, (ra, rb, vm) in {'5-5.6_marc': (5.0, 5.6, ok & marc), '6.5-8.5': (6.5, 8.5, ok)}.items():
        for lloc, (s0, s1) in {'dalt': (45, 135), 'baix': (225, 315)}.items():
            m = vm & (r >= ra) & (r < rb) & (th >= s0) & (th < s1); o[f'{nom}_{lloc}'] = float(np.median(L[m]))
    return o
c0, c1 = cel_veu(L0), cel_veu(L1); res['cel_quocient'] = {k: c1[k] / c0[k] for k in c0}
# --- control nul i canvi del compost ---
dl = np.log(np.maximum(L1, 1e-4)) - np.log(np.maximum(L0, 1e-4)); ch = {}
zonesn = {'1.02-1.3': (1.02, 1.3, 0, 360), '1.3-2': (1.3, 2, 0, 360), '2-3': (2, 3, 0, 360), '3-4.5': (3, 4.5, 0, 360), '4.5-7': (4.5, 7, 0, 360), '7-9.5': (7, 9.5, 0, 360),
          'nul_baix_225-315_1.3-3': (1.3, 3, 225, 315), 'nul_1.3-2_sense_negres': (1.3, 2, 0, 360)}
for k, (a, b, s0, s1) in zonesn.items():
    m = ok & marc & (r >= a) & (r < b) & (th >= s0) & (th < s1)
    x = dl[m]; ch[k] = dict(p1_p50_p99=[float(q) for q in np.percentile(x, [1, 50, 99])], frac_gt_0_5pc=float((np.abs(x) > 0.005).mean()), frac_gt_2pc=float((np.abs(x) > 0.02).mean()), mitj_abs=float(np.abs(x).mean()))
res['canvi_compost_lnL'] = ch
# --- RECTIFICACIÓ: la cua fosca de l'estructura de zona (6–64 px) s'escurça més que la clara? ---
def resid(L):
    l = np.log(np.maximum(L, 1e-4)); return cv2.GaussianBlur(l, (0, 0), 3.0) - cv2.GaussianBlur(l, (0, 0), 32.0)
R0_, R1_ = resid(L0), resid(L1); rect = {}
for a, b in ((2, 3), (3, 4.5), (4.5, 7), (7, 9.5)):
    m = ok & marc & (r >= a) & (r < b) & (G['dl'] > 60)
    x0, x1 = R0_[m], R1_[m]; q0 = np.percentile(x0, [1, 5, 50, 95, 99]); q1 = np.percentile(x1, [1, 5, 50, 95, 99])
    sk = lambda x: float(np.mean((x - x.mean()) ** 3) / np.std(x) ** 3)
    rect[f'{a:g}-{b:g}'] = dict(p1_p5_p50_p95_p99_V107=[float(q) for q in q0], p1_p5_p50_p95_p99_cand=[float(q) for q in q1],
                               cua_fosca_p5_quocient=float((q1[1] - q1[2]) / (q0[1] - q0[2])), cua_clara_p95_quocient=float((q1[3] - q1[2]) / (q0[3] - q0[2])),
                               cua_fosca_p1_quocient=float((q1[0] - q1[2]) / (q0[0] - q0[2])), cua_clara_p99_quocient=float((q1[4] - q1[2]) / (q0[4] - q0[2])),
                               asimetria_V107=sk(x0), asimetria_cand=sk(x1))
res['rectificacio_6-64px_lnL'] = rect
del R0_, R1_
# --- fusionat del PSB × F_nou/F_vell (41·42) ---
PSBP = R0 / '1-PHOTOSHOP/V107.psb'
with open(PSBP, 'rb') as f:
    hdr = f.read(26); nch = struct.unpack('>H', hdr[12:14])[0]
    for _ in range(2):
        n = struct.unpack('>I', f.read(4))[0]; f.seek(n, 1)
    n = struct.unpack('>Q', f.read(8))[0]; f.seek(n, 1); pos = f.tell(); cmp_ = struct.unpack('>H', f.read(2))[0]
if cmp_ == 0:
    mm = np.memmap(PSBP, dtype='>u2', mode='r', offset=pos + 2, shape=(nch, H, W))
    Lf = np.stack([np.asarray(mm[k, ::PAS, ::PAS], np.float32) / 65535 for k in range(3)], -1); Lf = (Lf[..., 0] + 2 * Lf[..., 1] + Lf[..., 2]) / 4; del mm
    Fr = np.ones_like(Lf)
    for lid in (41, 42):
        a = alfa(lid, (0, 0, W, H), PAS); u0 = ras(lid, (0, 0, W, H), PAS)
        c = np.load(CAND / f'{TAG[lid]}_u16.npy', mmap_mode='r')[::PAS, ::PAS].astype(np.float32); s = np.load(STD / f'{TAG[lid]}_u16.npy', mmap_mode='r')[::PAS, ::PAS].astype(np.float32)
        u1 = np.clip(u0 + (c - s) / 65535, 0, 1); Fr *= (1 - a * (1 - u1)) / np.maximum(1 - a * (1 - u0), 1e-4); del a, u0, u1, c, s
    zf0, reff = zones(Lf); zf1, _ = zones(Lf * Fr, reff)
    res['PSB_fusionat_V107'] = zf0; res['PSB_fusionat_x_Fnou_Fvell'] = zf1
    m = Z & (Lf > 1e-4); res['emulacio_propia_vs_fusionat'] = dict(corr_lnL=float(np.corrcoef(np.log(L0[m]), np.log(Lf[m]))[0, 1]))
else: res['PSB'] = f'compressió {cmp_}: no llegit'
res['segons'] = round(time.time() - T0)
(OUT / f'W1_{NOM}.json').write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n'); print('FET', round(time.time() - T0), 's')
