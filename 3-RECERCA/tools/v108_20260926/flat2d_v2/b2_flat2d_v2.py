"""b2_flat2d_v2 (V108, flat 2D lliurable) · APILAT PER TREN amb UN SOL CANVI: cada subpla es divideix, a més, per C (la part NO RADIAL del
flat, f0_flat2d_v2.py). Amb --flat2d no, dona BIT A BIT els apilats de la cadena (control).
Còpia de marrons/b2_v108_flat2d.py (el bucle de cadena_raw/b2_v97.py per a vixen i sony_A; el programa congelat B2 V42 per a sony_B) amb
una correcció que el verificador no va veure i que és necessària perquè l'únic canvi sigui C:
  · la CORRECCIÓ DE L'ONDULACIÓ del flat radial (flat_ripple_correction, només Sony) es calcula a partir de `ctx.flat`. Al pilot, `ctx.flat`
    ja era FLAT_RADIAL·C, i la correcció canviava (el perfil radial del flat 2D no és el del flat radial). Aquí es calcula SEMPRE amb el
    FLAT_RADIAL original de la cadena (`ctx.flat_original`): el rebut en desa el SHA, que ha de ser el mateix amb --flat2d si i no.
Els pesos de cada fotograma (finestra de la dada crua, k, offsets, φ, màscara lunar, taula de vora) no depenen del flat: el rebut desa el
SHA dels denominadors dels tres canals (vixen, sony_A) o dels pesos (sony_B), que han de ser els del control.
Sortida: <out>/<grup>_total.npy (i _den G per a vixen/sony_A; cau/sony_B_total_v42.npy i _weights per a sony_B) i <grup>_REBUT.json.
Ús: b2_flat2d_v2.py vixen|sony_A|sony_B --flat2d si|no --out <carpeta>"""
import sys, argparse, json, time, types, math, hashlib, os
from pathlib import Path
CRT = Path(__file__).resolve().parents[2] / 'v97_refundacio_20260924/cadena_raw'; sys.path.insert(0, str(CRT))
import a4_sources as _A4; _A4.CID = json.loads((_A4.R / '.coordination/claim.lock/owner.json').read_text())['claim_id']
assert _A4.CID == 'CLAUDE_V108_MARRONS_I_ZONES_NEGRES_20260926', _A4.CID
from a4_sources import *   # context(), guard(), O, H, comu, f2, sha, save, definition, np, cv2
ap = argparse.ArgumentParser(); ap.add_argument('grup', choices=['vixen', 'sony_A', 'sony_B']); ap.add_argument('--flat2d', choices=['si', 'no'], required=True); ap.add_argument('--out', required=True)
a = ap.parse_args(); guard(); t00 = time.time(); OUT = Path(a.out); OUT.mkdir(parents=True, exist_ok=True)
FD = _A4.R / '4-RESULTATS/v108_20260926/flat2d_v2/flat2d'
FL2D = {'vixen': Path(os.environ.get('FLAT2D_VIXEN') or FD / 'VIXEN_flat2d_v2.npz'), 'sony': Path(os.environ.get('FLAT2D_SONY') or FD / 'SONYTOT_flat2d_v2.npz')}
tag = 'vixen' if a.grup == 'vixen' else 'sony'; INJ = {}
_orig_init = f2.Ctx.__init__
_C = np.load(FL2D[tag])['C'].astype(np.float32) if a.flat2d == 'si' else None
def _init_v2(s, run):
    _orig_init(s, run); s.flat_original = s.flat
    if _C is not None:
        assert s.flat.shape == _C.shape, (s.flat.shape, _C.shape)
        s.flat = (s.flat * _C).astype(np.float32); INJ['fet'] = True; INJ['C_p1_p99'] = np.percentile(_C, [1, 99]).tolist()
f2.Ctx.__init__ = _init_v2
def amb_flat_original(frc):
    """La correcció de l'ondulació, sempre amb el FLAT_RADIAL de la cadena (no amb el flat 2D)."""
    def w(ctx, tg, *aa, **kk):
        sv = ctx.flat; ctx.flat = ctx.flat_original
        try: out, rep = frc(ctx, tg, *aa, **kk)
        finally: ctx.flat = sv
        if out is not None:
            h = hashlib.sha256()
            for i in sorted(out): h.update(np.ascontiguousarray(out[i]).tobytes())
            INJ['ondulacio_sha256'] = h.hexdigest()
        else: INJ['ondulacio_sha256'] = None
        return out, rep
    return w
if a.grup == 'sony_B':
    ns, fr = context(); ns.update(CAU36=O / 'sources_v36/cau', REB36=O / 'sources_v36/output/v36_20260908/4-rebuts', CAUF=O / 'sources_v29', sha=sha, FLAT_CENTRE_YX={'sony': (2660., 4000.)}, FLAT_SIGMA_PX=32.)
    definition(fr['sources']['common32']['copy'], 'flat_ripple_correction', ns); definition(fr['sources']['common']['copy'], 'savejson', ns)
    from a5_recompose import literal_helpers
    h = literal_helpers(H / 'b2_v42_replay.py', ['programs', 'require'], ['SOURCE_SHA', 'HELPERS_SHA'])
    (OUT / 'cau').mkdir(exist_ok=True); (OUT / 'receipts').mkdir(exist_ok=True)
    ns.update(CAU42=OUT / 'cau', REB42=OUT / 'receipts', math=math)
    code, digest = h['programs'](H / 'b2_v42_source.py', H / 'b2_v42_v38_helpers.py'); exec(code[1], ns)
    ns['flat_ripple_correction'] = amb_flat_original(ns['flat_ripple_correction'])
    ns['B'] = types.SimpleNamespace(flat_ripple_correction=ns['flat_ripple_correction'], upsample=ns['upsample'], CHN=ns['CHN']); exec(code[0], ns)
    sys.argv = ['b2_recomposicio_v42.py', 'sony_B', 'delta_arcmin=8.10', 'corr=' + str(H / 'b2_v42_correccions_B.json')]; ns['main']()
    tot = OUT / 'cau/sony_B_total_v42.npy'; ref = O / 'b2_sony_B/cau/sony_B_total_v42.npy'; wts = OUT / 'cau/sony_B_weights_v42.npy'; refw = O / 'b2_sony_B/cau/sony_B_weights_v42.npy'
    rep = dict(grup='sony_B', flat2d=a.flat2d, fitxer_flat2d=str(FL2D[tag]), injectat=INJ, AST=digest, sha256=sha(tot), igual_a_la_cadena=(sha(tot) == sha(ref)),
               pesos_sha256=sha(wts), pesos_iguals_a_la_cadena=(sha(wts) == sha(refw)), segons=time.time() - t00)
    save(OUT / 'sony_B_REBUT.json', rep); print('FET sony_B', rep['sha256'][:12], 'igual a la cadena:', rep['igual_a_la_cadena'], 'pesos iguals:', rep['pesos_iguals_a_la_cadena'], INJ.get('ondulacio_sha256', '')[:12], f"{rep['segons']:.0f}s", flush=True); sys.exit(0)
# ---- vixen, sony_A: bucle de b2_v97.py (còpia literal; opcions fixades com a la cadena) ----
FINESTRA = 'comuna' if a.grup == 'vixen' else 'canal'; VORA = 'taula' if a.grup == 'vixen' else 'cap'; PHI = 'original'
ns, fr = context()
ns.update(FLAT_CENTRE_YX={'sony': (2660., 4000.)}, FLAT_SIGMA_PX=32.)
definition(fr['sources']['common32']['copy'], 'flat_ripple_correction', ns); definition(H / 's4_v51_core_comu38.py', 'upsample', ns)
flat_ripple_correction = amb_flat_original(ns['flat_ripple_correction']); upsample = ns['upsample']; COMMON_TO_FINAL = ns['COMMON_TO_FINAL']
Hh, Ww = 7506, 10551
TAULA = json.loads((H / 'v38_limb_round1/cau/correccio_vora_lunar.json').read_text())['taula']
def classe(e): return 'curts' if e <= 1 / 800 else ('mitjans' if e <= 1 / 50 else 'llargs')
def correccio_vora(D, e):
    tb = TAULA[classe(e)]; B = np.interp(D, np.asarray(tb['d_px'], np.float32), np.asarray(tb['B_ln'], np.float32), left=tb['B_ln'][0], right=0.0).astype(np.float32)
    return np.exp(-B, dtype=np.float32)
def plans_comuna(s, nom, e):
    import rawpy
    with rawpy.imread(s.ruta[nom]) as r: raw = r.raw_image.astype(np.float32)
    dk = s.dark(e); ped = s.cfg['pedestal_dn']; sat = s.cfg['saturacio_dn']; es_sony = s.run.tren.upper().startswith('SONY')
    fs = [raw[s.orig[i][0]::2, s.orig[i][1]::2] - ped for i in range(4)]
    hh = min(x.shape[0] for x in fs); ww = min(x.shape[1] for x in fs); fs = [x[:hh, :ww] for x in fs]
    fmax = np.maximum.reduce(fs)
    gi = [i for i in range(4) if comu.IDX_CANAL[i] == 1]; fg = sum(fs[i] for i in gi) / len(gi)
    alt = f2.SOSTRE * (sat - ped)
    sostre = 1.0 - ns['smooth'](fmax, ns['RAMPA_INICI'] * alt, alt)
    terra = np.clip((fg - f2.TERRA_DN) / (3.0 * f2.TERRA_DN), 0.0, 1.0)
    wcom = (sostre * terra * e).astype(np.float32)
    out = {}
    for i in range(4):
        oy, ox = s.orig[i]; rs = raw[oy::2, ox::2]; ds = dk[oy::2, ox::2]
        if es_sony: rs = ds + (rs - ds) * ns['lin_corr_sony'](rs, ped, sat)
        pl = comu.calibra_pla(rs, ds, s.flat[oy::2, ox::2], e, s.wb, s.mc, i)
        v = s.valid[oy::2, ox::2]; w = np.zeros(pl.shape, np.float32); w[:hh, :ww] = wcom * v[:hh, :ww]
        out[i] = (pl, w)
    return out
grp = None if a.grup == 'vixen' else a.grup
path = f12dirs[tag]; run = comu.Run.obre(str(path)); ctx = f2.Ctx(run)
if FINESTRA == 'comuna': f2.Ctx.plans = plans_comuna
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
    corr = correccio_vora(np.hypot(rx - mlx, ry - mly) - ctx.RL, v['exp']) if (tag == 'vixen' and VORA == 'taula') else None
    for i, (pl, w) in ctx.plans(n, v['exp']).items():
        c = comu.IDX_CANAL[i]; oy, ox = ctx.orig[i]
        if fcorr is not None: pl = pl * fcorr[i]
        mx = ((rx - ox) * .5).astype(np.float32); my = ((ry - oy) * .5).astype(np.float32)
        dd = cv2.remap(w, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) * fl
        nn = cv2.remap(pl * w * k, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) * fl
        b = float(m['offset_RGB'][c])
        if b != 0.0: nn += b * dd
        if PHI == 'original': nn *= np.exp(-upsample(phis[CHN[c]][j]))
        if corr is not None: nn *= corr
        num[..., c] += nn; den[..., c] += dd; del dd, nn
    applied.append(dict(name=n, exp=v['exp'], k=k, offset_RGB=m['offset_RGB']))
    if j % 10 == 0 or j == len(names) - 1: print(f'{a.grup} {j+1}/{len(names)} ({time.time()-t0:.0f}s)', flush=True)
    del rx, ry, fl, corr
cam = np.where(den > 0, num / np.maximum(den, 1e-20), np.nan); del num
_, total = comu.lluminancia(cam, run.matriu, run.color['guany']); del cam
total = total.astype(np.float32); np.save(OUT / f'{a.grup}_total.npy', total); np.save(OUT / f'{a.grup}_den.npy', den[..., 1])
den_sha = hashlib.sha256(np.ascontiguousarray(den).tobytes()).hexdigest(); del den
REF = {'vixen': _A4.R / '4-RESULTATS/v97_refundacio_20260924/proves_apilat/vixen_comuna_taula_original/vixen_total.npy', 'sony_A': O / 'b2_sony_A/cau/sony_A_total_v36.npy'}[a.grup]
rep = dict(grup=a.grup, flat2d=a.flat2d, fitxer_flat2d=str(FL2D[tag]), injectat=INJ, finestra=FINESTRA, vora=VORA, phi=PHI, fotogrames=applied, sha256=sha(OUT / f'{a.grup}_total.npy'),
           den_RGB_sha256=den_sha, den_G_sha256=sha(OUT / f'{a.grup}_den.npy'), referencia=str(REF.relative_to(_A4.R)), segons=time.time() - t00)
rep['igual_a_la_cadena'] = rep['sha256'] == sha(REF)
if not rep['igual_a_la_cadena']:
    rf = np.load(REF, mmap_mode='r'); sl = (slice(0, Hh, 5), slice(0, Ww, 5)); A_ = total[sl]; B_ = np.asarray(rf[sl]); ok = np.isfinite(A_) & np.isfinite(B_) & (B_ > 0)
    rep['dif_rel_p1_p50_p99'] = np.percentile(A_[ok] / B_[ok] - 1, [1, 50, 99]).tolist()
save(OUT / f'{a.grup}_REBUT.json', rep); print('FET', a.grup, rep['sha256'][:12], 'igual a la cadena:', rep['igual_a_la_cadena'], 'den RGB', den_sha[:12], 'ondulació', str(INJ.get('ondulacio_sha256'))[:12], rep.get('dif_rel_p1_p50_p99'), f"{rep['segons']:.0f}s", flush=True)
