# CÒPIA per a la cadena V108 (Claude, 26-09-2026) de 3-RECERCA/tools/v105_limbe_20260926/fila/w_wow.py: només canvien el camí d'importació (comu_fila_v108) i les mitjanes d'escala (V108_FILA_MUS).
"""w_wow · la WOW bilateral (capa 56, P05) de la V104 regenerada a la caixa gran BIG amb l'operador V95 (wow_v95.conv_v95, nconv, ng_pes) i
els mateixos paràmetres que f3_filtres_v98 E2 (centra_rad, iso 0,5–1,5, sig_rad, llindar 0,6–0,995, k 0,02317, mitjanes d'escala de la V104).
Sense opcions reprodueix la L56 de la V104 (≤ 1 LSB a la caixa lunar: les mitjanes d'escala del F3_E2.json van arrodonides a 5 decimals).
Ganxos per a les cures de la filera de punts:
  --pot tan        (i)   potència local de les escales fines estimada AL LLARG DE L'ARC (mateixa d, σ_r) a d < tan-d, en lloc d'isòtropa (nconv);
  --pre snp        (ii)  resolució que segueix el S/N: a la franja de banda l'entrada es PROMITJA amb σ(x) = --sn-esc × σ mesurada (SN_MAPA.npz,
                         a3_mapa_sn.py), sobre G/P amb P = perfil al llarg de l'arc a la mateixa d (el perfil radial no es toca); --pre sn = isòtrop sobre G;
  --pre-escales    les escales que surten de l'entrada promitjada (la resta, de l'original: fora de la franja la capa queda com la V104);
  --pot-ref orig   la potència de cada escala es mesura a l'entrada original (sense re-igualar el contrast després del promig);
  --pes sn         (iii) pes de les escales 0–1 dividit pel soroll relatiu ρ (atenuació: NOMÉS per comparar, norma del 27-08).
RECOMANADA: --pre snp --sn-esc 0.7 --pre-escales 0,1,2.  Sortida: <OUT>/<nom>/L56_G_moon.npy (u16, caixa lunar 4677–6077 × 3077–4477)."""
import sys, argparse, time; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from comu_fila_v108 import *
from wow_v95 import conv_v95, nconv, ng_pes, smoothstep
import numexpr as ne
ap = argparse.ArgumentParser(); ap.add_argument('nom'); ap.add_argument('--pot', choices=['iso', 'tan'], default='iso'); ap.add_argument('--tan-escales', default='0,1,2')
ap.add_argument('--sig-t', type=float, default=6.0, help='σ al llarg de l\'arc a l\'escala 0 (px); es dobla a cada escala'); ap.add_argument('--sig-r', type=float, default=0.5)
ap.add_argument('--tan-d', default='8,12', help='fosa tangencial → isòtropa (px de d)'); ap.add_argument('--pre', choices=['cap', 'sn', 'snp'], default='cap'); ap.add_argument('--sn-esc', type=float, default=1.0); ap.add_argument('--pes', choices=['cap', 'sn'], default='cap')
ap.add_argument('--diag', action='store_true'); ap.add_argument('--pre-escales', default='0,1,2,3,4,5,6,7', help='escales que es calculen amb l\'entrada promitjada (la resta, amb l\'original)'); ap.add_argument('--pot-ref', choices=['mateixa', 'orig'], default='mateixa', help='orig: la potència local de cada escala es mesura a l\'entrada SENSE el promig S/N (cap re-igualació del contrast)'); ap.add_argument('--escales-pes', default='0,1')
A = ap.parse_args(); OD = OUT / A.nom; OD.mkdir(parents=True, exist_ok=True)
t0 = time.time(); I = entrades(BIG); a, m = I['a'], I['m']; dB, thB = dist_theta(BIG)
MUS = [0.00118, 0.0029, 0.00758, 0.01881, 0.04219, 0.09397, 0.19489, 0.30817]   # F3_E2.json de la V104 (mitjanes_escala)
if os.environ.get('V108_FILA_MUS'): MUS = [float(v) for v in json.loads(os.environ['V108_FILA_MUS'])]; assert len(MUS) == 8   # V108: les del F3_E2.json de la variant
K56 = 0.02317; SIG = lambda s: min(150.0, max(32.0, 4.0 * 2 ** s)); L0 = 0.6
rep = dict(nom=A.nom, pre_escales=A.pre_escales, pot_ref=A.pot_ref, sn_esc=A.sn_esc, pot=A.pot, pre=A.pre, pes=A.pes, sig_t=A.sig_t, sig_r=A.sig_r, tan_escales=A.tan_escales, tan_d=A.tan_d)
if A.pre in ('sn', 'snp') or A.pes == 'sn':
    SN = np.load(OUT / 'SN_MAPA.npz'); x0, y0 = BOXL[0] - BIG[0], BOXL[1] - BIG[1]
    RHO = np.ones_like(a); RHO[y0:y0 + 1400, x0:x0 + 1400] = SN['rho']          # soroll fi local / soroll del règim net (≥ 1), caixa lunar
a_orig = a.copy()
if A.pre in ('sn', 'snp'):   # promig per píxel amb σ(x) mesurada (SN_MAPA): sn = isòtrop sobre G; snp = sobre G/P (el perfil radial al llarg de l'arc intacte)
    x0, y0 = BOXL[0] - BIG[0], BOXL[1] - BIG[1]; sl = (slice(y0, y0 + 1400), slice(x0, x0 + 1400)); SIGM = SN['sigma'] * A.sn_esc
    a[sl] = mitjana_sn(a[sl], m[sl], SIGM, perfil=(A.pre == 'snp')); rep['pre_sigma_p50_p99'] = np.percentile(SIGM[SIGM > 0], [50, 99]).round(3).tolist()
TE = [int(v) for v in A.tan_escales.split(',')] if A.pot == 'tan' else []; TD0, TD1 = [float(v) for v in A.tan_d.split(',')]
reg = m & (dB > -1) & (dB < TD1 + 1); iy, ix = np.nonzero(reg); d0 = dB[iy, ix]
tr = np.radians(thB[iy, ix]); tx, ty = -np.sin(tr), -np.cos(tr)    # tangent (en píxels: +x = cos, −y = sin; derivada respecte de θ → (−sin, −cos))
def pot_tan(w2, s):
    st = A.sig_t * 2 ** s; sr = A.sig_r * max(1.0, 2 ** s / 2); rw = int(np.ceil(3 * st)); num = np.zeros(len(iy)); den = np.zeros(len(iy))
    hh, ww = w2.shape; mf = m.astype(np.float32)
    for dy in range(-rw, rw + 1):
        for dx in range(-rw, rw + 1):
            if dx * dx + dy * dy > rw * rw: continue
            ny = iy + dy; nx = ix + dx; ok = (ny >= 0) & (ny < hh) & (nx >= 0) & (nx < ww); ny = np.clip(ny, 0, hh - 1); nx = np.clip(nx, 0, ww - 1)
            dd = dB[ny, nx] - d0; ts = dx * tx + dy * ty
            wt = ne.evaluate('exp(-0.5*(dd*dd/(sr*sr) + ts*ts/(st*st)))') * mf[ny, nx] * ok
            num += wt * w2[ny, nx]; den += wt
    return (num / np.maximum(den, 1e-20)).astype(np.float32)
c0 = np.where(m, a_orig, 0).astype(np.float32); c = np.where(m, a, 0).astype(np.float32); outw = np.zeros_like(c); dmap = np.full(a.shape, 1e4, np.float32); diag = {}
PE = [int(v) for v in A.escales_pes.split(',')]
PRE_ESC = [int(v) for v in A.pre_escales.split(',')] if A.pre_escales != '0,1,2,3,4,5,6,7' else None
if PRE_ESC is not None: assert A.pot_ref == 'mateixa'
for s in range(8):
    t1 = time.time(); nxt, compl, radf = conv_v95(c, m, dmap, s, True, iso=(0.5, 1.5), ret_rad=True); nxt = np.where(m, nxt, 0).astype(np.float32)
    wave = np.where(m, c - nxt, 0).astype(np.float32); wave[np.abs(wave) <= 8 * np.finfo('float32').eps * np.maximum(np.abs(c), np.abs(nxt))] = 0
    if PRE_ESC is not None:   # dues cadenes: les escales de PRE_ESC surten de l'entrada promitjada (c), la resta de l'original (c0)
        nx0, compl0, radf0 = conv_v95(c0, m, dmap, s, True, iso=(0.5, 1.5), ret_rad=True); nx0 = np.where(m, nx0, 0).astype(np.float32)
        wv0 = np.where(m, c0 - nx0, 0).astype(np.float32); wv0[np.abs(wv0) <= 8 * np.finfo('float32').eps * np.maximum(np.abs(c0), np.abs(nx0))] = 0; c0 = nx0
        if s not in PRE_ESC: wave, compl, radf = wv0, compl0, radf0
    if A.pot_ref == 'orig':
        nx0 = np.where(m, conv_v95(c0, m, dmap, s, True, iso=(0.5, 1.5))[0], 0).astype(np.float32); wv0 = np.where(m, c0 - nx0, 0).astype(np.float32)
        wv0[np.abs(wv0) <= 8 * np.finfo('float32').eps * np.maximum(np.abs(c0), np.abs(nx0))] = 0; pot = nconv(wv0 * wv0, m, s); c0 = nx0
    else: pot = nconv(wave * wave, m, s)
    if s in TE:
        pt = pot_tan(wave * wave, s); fz = (1 - smoothstep(d0, TD0, TD1)).astype(np.float32); pi_ = pot[iy, ix]
        pot[iy, ix] = np.exp(np.log(np.maximum(pi_, 1e-30)) * (1 - fz) + np.log(np.maximum(pt, 1e-30)) * fz)
    g = np.where(m & (compl > 0), wave / np.sqrt(np.maximum(pot, 1e-20)), 0).astype(np.float32)
    if s >= 3: w = (smoothstep(compl, L0, 0.995) * m).astype(np.float32)
    else: w = (m & (compl > 0)).astype(np.float32)
    if A.pes == 'sn' and s in PE: w = (w / np.maximum(RHO, 1.0)).astype(np.float32)    # atenuació per S/N (NOMÉS comparació)
    g = g - MUS[s]; g = g - radf * ng_pes(g, w * radf, SIG(s)); outw += w * g; c = nxt
    if A.diag: diag[f'gw{s}'] = crop_big_to_moon(w * g).astype(np.float16); diag[f'pot{s}'] = crop_big_to_moon(pot).astype(np.float32); diag[f'wave{s}'] = crop_big_to_moon(wave).astype(np.float32)
    print(f'escala {s} · {time.time() - t1:.0f} s', flush=True)
q = np.where(m, outw, np.nan); disp = np.where(m, 0.5 + K56 * np.nan_to_num(q), 0.5)
u16 = np.round(np.clip(np.nan_to_num(disp, nan=0.5), 0, 1) * 65535).astype(np.uint16)
np.save(OD / 'L56_G_moon.npy', crop_big_to_moon(u16))
if A.diag: np.savez(OD / 'DIAG_ESCALES.npz', **diag)
rep['segons'] = round(time.time() - t0, 1); desa(OD / 'W_REBUT.json', rep); print('FET', A.nom, rep['segons'], 's')
