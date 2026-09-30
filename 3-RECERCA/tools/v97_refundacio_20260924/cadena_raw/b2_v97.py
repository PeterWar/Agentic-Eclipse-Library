"""b2 (V97) · Apilat LDIC per tren i apuntament a la graella final, rellegint els RAW amb la calibració (F0) i el registre (F1.3/F2.2) congelats.
És el bucle de la b2 V38 (`raw_replay/b2_v38_source.py`, idèntic per a vixen, sony_A i sony_B) amb DUES opcions declarades:
  --finestra canal   pes de cada subpla CFA calculat amb el SEU valor (com la V29–V96).
  --finestra comuna  (V97) un sol pes per cel·la Bayer, el del subpla més exposat: les quatre subplans barregen les MATEIXES exposicions.
                     Motiu: amb pesos per canal, cada canal canvia d'exposició a una brillantor diferent i qualsevol desacord entre exposicions
                     fa un graó de color que segueix la isofota (el «polígon» B/G de la Vixen, Artefactes_V95 §1).
  --vora taula       correcció multiplicativa de la vora lunar de la V38 (taula B(D) amb D des del radi del MODEL; només Vixen).
  --vora cap         (V97) sense taula: la dada tal com és, amb la màscara lunar de cada fotograma (guarda 2 px), com la Sony.
  --phi zero         (prova) sense els camps de nivell B1 per fotograma i canal (per defecte, 'original').
Sony B: gir δ +8,10′ i les tres correccions d'estrelles de la V42 (`b2_v42_correccions_B.json`) — NO implementat aquí: per a sony_B
s'ha de fer servir la b2 V42 (a5_recompose.py sony_B). Sortida: <out>/<grup>_total.npy (H,W,3) sRGB lineal (matriu i guany del run),
<out>/<grup>_den.npy (pesos G) i <grup>_REBUT.json. Ús: b2_v97.py <grup> --finestra comuna --vora cap --out <carpeta>"""
import sys, argparse, json, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from a4_sources import *   # context(), guard(), O, H(raw_replay), comu, f2, sha, save, definition
ap = argparse.ArgumentParser(); ap.add_argument('grup', choices=['vixen', 'sony_A']); ap.add_argument('--finestra', choices=['canal', 'comuna'], required=True)
ap.add_argument('--vora', choices=['taula', 'cap'], required=True); ap.add_argument('--out', required=True); ap.add_argument('--desa-den', action='store_true'); ap.add_argument('--phi', choices=['original', 'zero'], default='original')
a = ap.parse_args(); guard(); t00 = time.time()
ns, fr = context(); OUT = Path(a.out); OUT.mkdir(parents=True, exist_ok=True)
ns.update(FLAT_CENTRE_YX={'sony': (2660., 4000.)}, FLAT_SIGMA_PX=32.)
definition(fr['sources']['common32']['copy'], 'flat_ripple_correction', ns); definition(H / 's4_v51_core_comu38.py', 'upsample', ns)
flat_ripple_correction = ns['flat_ripple_correction']; upsample = ns['upsample']; COMMON_TO_FINAL = ns['COMMON_TO_FINAL']
Hh, Ww = 7506, 10551
TAULA = json.loads((H / 'v38_limb_round1/cau/correccio_vora_lunar.json').read_text())['taula']
def classe(e): return 'curts' if e <= 1 / 800 else ('mitjans' if e <= 1 / 50 else 'llargs')
def correccio_vora(D, e):
    tb = TAULA[classe(e)]; B = np.interp(D, np.asarray(tb['d_px'], np.float32), np.asarray(tb['B_ln'], np.float32), left=tb['B_ln'][0], right=0.0).astype(np.float32)
    return np.exp(-B, dtype=np.float32)

def plans_comuna(s, nom, e):
    """Com plans_v36 (LUT Sony abans del flat, calibra_pla), però amb UN pes per cel·la Bayer: la finestra del subpla amb el valor
    normalitzat més alt (el sostre el decideix el canal que satura primer) i el terra del subpla G (el de més senyal a la corona per
    als dos trens; comprovat al rebut amb la fracció de cel·les on el terra decideix)."""
    import rawpy
    with rawpy.imread(s.ruta[nom]) as r: raw = r.raw_image.astype(np.float32)
    dk = s.dark(e); ped = s.cfg['pedestal_dn']; sat = s.cfg['saturacio_dn']; es_sony = s.run.tren.upper().startswith('SONY')
    fs = [raw[s.orig[i][0]::2, s.orig[i][1]::2] - ped for i in range(4)]
    hh = min(x.shape[0] for x in fs); ww = min(x.shape[1] for x in fs); fs = [x[:hh, :ww] for x in fs]
    fmax = np.maximum.reduce(fs)
    gi = [i for i in range(4) if comu.IDX_CANAL[i] == 1]; fg = sum(fs[i] for i in gi) / len(gi)
    alt = f2.SOSTRE * (sat - ped)
    sostre = 1.0 - ns['smooth'](fmax, ns['RAMPA_INICI'] * alt, alt)                 # el sostre, pel subpla més exposat
    terra = np.clip((fg - f2.TERRA_DN) / (3.0 * f2.TERRA_DN), 0.0, 1.0)          # el terra, pel G
    wcom = (sostre * terra * e).astype(np.float32)
    out = {}
    for i in range(4):
        oy, ox = s.orig[i]; rs = raw[oy::2, ox::2]; ds = dk[oy::2, ox::2]
        if es_sony: rs = ds + (rs - ds) * ns['lin_corr_sony'](rs, ped, sat)
        pl = comu.calibra_pla(rs, ds, s.flat[oy::2, ox::2], e, s.wb, s.mc, i)
        v = s.valid[oy::2, ox::2]; w = np.zeros(pl.shape, np.float32); w[:hh, :ww] = wcom * v[:hh, :ww]
        out[i] = (pl, w)
    return out

tag = 'vixen' if a.grup == 'vixen' else 'sony'; grp = None if a.grup == 'vixen' else a.grup
path = f12dirs[tag]; run = comu.Run.obre(str(path)); ctx = f2.Ctx(run)
if a.finestra == 'comuna': f2.Ctx.plans = plans_comuna
pos = json.loads((path / '4-rebuts/F1.3_registre.json').read_text())['fotogrames']; kq = json.loads((path / '4-rebuts/F2.2_coherencia.json').read_text())['k']
meta = json.loads((O / 'sources_v36/cau' / f'{tag}_meta.json').read_text())['frames']
names = [m['name'] for m in meta if (grp is None or m['group'] == grp)]
phis = {c: np.load(O / 'sources_v36/cau' / f'{a.grup}_{c}_phi.npy', mmap_mode='r') for c in ('R', 'G', 'B')}
fcorr, frep = flat_ripple_correction(ctx, tag)
inv = cv2.invertAffineTransform(COMMON_TO_FINAL); yy, xx = np.ogrid[:Hh, :Ww]
qx = (inv[0, 0] * xx + inv[0, 1] * yy + inv[0, 2]).astype(np.float32); qy = (inv[1, 0] * xx + inv[1, 1] * yy + inv[1, 2]).astype(np.float32)
num = np.zeros((Hh, Ww, 3), np.float32); den = np.zeros((Hh, Ww, 3), np.float32); dx = (qx - ctx.CX) * ctx.k; dy = (qy - ctx.CY) * ctx.k
CHN = {0: 'R', 1: 'G', 2: 'B'}; applied = []; t0 = time.time()
for j, n in enumerate(names):
    v = pos[n]; k = kq.get(n, 1.0); m = meta[[mm['name'] for mm in meta].index(n)]
    rx = (ctx.ca * dx + ctx.sa * dy + v['sol_x']).astype(np.float32); ry = (-ctx.sa * dx + ctx.ca * dy + v['sol_y']).astype(np.float32)
    fl = f2.mascara_lluna(ctx, v, rx, ry)
    mlx = v['sol_x'] + float(v['lluna_dx']); mly = v['sol_y'] + float(v['lluna_dy'])
    corr = correccio_vora(np.hypot(rx - mlx, ry - mly) - ctx.RL, v['exp']) if (tag == 'vixen' and a.vora == 'taula') else None
    for i, (pl, w) in ctx.plans(n, v['exp']).items():
        c = comu.IDX_CANAL[i]; oy, ox = ctx.orig[i]
        if fcorr is not None: pl = pl * fcorr[i]
        mx = ((rx - ox) * .5).astype(np.float32); my = ((ry - oy) * .5).astype(np.float32)
        dd = cv2.remap(w, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) * fl
        nn = cv2.remap(pl * w * k, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) * fl
        b = float(m['offset_RGB'][c])
        if b != 0.0: nn += b * dd
        if a.phi == 'original': nn *= np.exp(-upsample(phis[CHN[c]][j]))   # camp de nivell B1 per fotograma i canal (V36)
        if corr is not None: nn *= corr
        num[..., c] += nn; den[..., c] += dd; del dd, nn
    applied.append(dict(name=n, exp=v['exp'], k=k, offset_RGB=m['offset_RGB']))
    if j % 10 == 0 or j == len(names) - 1: print(f'{a.grup} {j+1}/{len(names)} ({time.time()-t0:.0f}s)', flush=True)
    del rx, ry, fl, corr
cam = np.where(den > 0, num / np.maximum(den, 1e-20), np.nan); del num
_, total = comu.lluminancia(cam, run.matriu, run.color['guany']); del cam
total = total.astype(np.float32); np.save(OUT / f'{a.grup}_total.npy', total)
if a.desa_den: np.save(OUT / f'{a.grup}_den.npy', den[..., 1])
rep = dict(grup=a.grup, finestra=a.finestra, vora=a.vora, phi=a.phi, fotogrames=applied, sha256=sha(OUT / f'{a.grup}_total.npy'), segons=time.time() - t00,
           den_rel_RB_sobre_G=[float(np.nanmedian((den[::9, ::9, c] / np.maximum(den[::9, ::9, 1], 1e-20))[den[::9, ::9, 1] > 0])) for c in (0, 2)])
save(OUT / f'{a.grup}_REBUT.json', rep); print('FET', a.grup, rep['sha256'][:12], f"{rep['segons']:.0f}s", flush=True)
