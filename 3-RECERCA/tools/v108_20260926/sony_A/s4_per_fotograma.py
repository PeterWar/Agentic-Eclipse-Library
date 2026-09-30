"""s4 · SENSOR o CEL? Fotograma a fotograma (sortida de s3), per a T1 i T2.
1. Per a cada fotograma: residu relatiu (σ 40) del seu G, perfil perpendicular al traç (geometria fixa M3, en coordenades del LLENÇ),
   profunditat a t = 0 amb el seu nul (paral·leles i girades) i posició del mínim (filtre adaptat, gaussiana σ 3 px, |t| ≤ 15).
2. Mapatge llenç→sensor de cada fotograma (MAPATGE.json de s3): on cau el traç al SENSOR de cada fotograma (píxels RAW), i quant
   s'hauria de desplaçar al LLENÇ (perpendicular al traç) si fos fix al sensor: Δt_f = n · J⁻¹ · (−Δsol_f), respecte d'una referència.
3. Prova d'hipòtesi contínua: s'apilen els perfils dels fotogrames amb el pes invers de la seva variància (del nul), desplaçats α·Δt_f.
   α = 0 → fix al CEL (el que fa l'apilat); α = 1 → fix al SENSOR; α ≈ 2 → lligat a l'eix òptic (reflex, per a un mirall pla de
   l'eix). Es busca la α que fa el solc més profund, dins de cada apuntament i junts, amb bootstrap per trams al llarg del traç.
Sortida: S4_PER_FOTOGRAMA.json i S4_perfils.npz.  Ús: s4_per_fotograma.py [flat2d|control]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); from comu_sonyA import *
var = sys.argv[1] if len(sys.argv) > 1 else 'flat2d'
DIR = OUT / f'fotogrames_{var}'; MP = json.loads((DIR / 'MAPATGE.json').read_text())
inv = np.array(MP['inv_common_to_final']); CX, CY, K, ca, sa, dB = MP['CX'], MP['CY'], MP['k'], MP['ca'], MP['sa'], MP['delta_B_rad']
def a_sensor(x, y, f):
    qx = inv[0, 0] * x + inv[0, 1] * y + inv[0, 2]; qy = inv[1, 0] * x + inv[1, 1] * y + inv[1, 2]; dx = (qx - CX) * K; dy = (qy - CY) * K
    if f['grup'] == 'sony_B': c_, s_ = np.cos(dB), np.sin(dB); dx, dy = c_ * dx - s_ * dy, s_ * dx + c_ * dy
    return ca * dx + sa * dy + f['sol_x'] + f['cx'], -sa * dx + ca * dy + f['sol_y'] + f['cy']
def jacobia(f):
    x0, y0 = 5000.0, 3000.0; p0 = np.array(a_sensor(x0, y0, f)); px = np.array(a_sensor(x0 + 1, y0, f)); py = np.array(a_sensor(x0, y0 + 1, f))
    return np.stack([px - p0, py - p0], 1)   # d(sensor)/d(llenç)
TEMPLATE_S = 3.0
def posicio(t, pr, lim=15.0):
    """mínim del filtre adaptat (gaussiana σ 3 menys la mitjana als flancs 12–60)."""
    best = (np.inf, np.nan)
    for t0 in np.arange(-lim, lim + 1e-6, 0.5):
        D = profunditat(t, pr, t0, nucli=TEMPLATE_S)
        if np.isfinite(D) and D < best[0]: best = (D, t0)
    return best
res = dict(variant=var, fotogrames={}, proves={}); perf = {}
for k, tr in TRACOS.items():
    tn = f'T{k}'; x0, y0, x1, y1 = MP['caixes'][tn]
    c, d, L, n = tr['centre'], tr['d'], tr['llarg'], tr['n']
    segs = np.linspace(-L / 2, L / 2, 9)   # 8 trams per al bootstrap
    PR = {}; INFO = {}
    for nom, f in MP['fotogrames'].items():
        z = np.load(DIR / f'{tn}_{nom[:-4]}.npz'); G = z['G']; w = z['w']
        wmax = float(np.nanmax(w)) if np.isfinite(w).any() else 0.0
        if wmax <= 0: continue
        img = np.where((w > 0.02 * wmax) & np.isfinite(G), G, 0).astype(np.float32)
        r = rel_map(img)
        m, t, pr = mesura_amb_nul(r, (x0, y0), c, d, L)
        if not np.isfinite(m.get('D', np.nan)) or m.get('cobertura', 0) < 0.5 or 'nul_mad' not in m: continue
        prs = []
        for a_, b_ in zip(segs[:-1], segs[1:]):
            _, p_, cov_ = perfil(r, (x0, y0), c, d, L, a_, b_, tmax=100)
            prs.append(p_)
        Dmin, tmin = posicio(t, pr)
        # on cau el traç al sensor d'aquest fotograma (extrems) i desplaçament d'un patró fix al sensor
        e = tr['extrems']; s0 = a_sensor(e[0, 0], e[0, 1], f); s1 = a_sensor(e[1, 0], e[1, 1], f)
        INFO[nom] = dict(grup=f['grup'], exp=f['exp'], t_s=f['t'], D=m['D'], z=m['z'], p=m['p'], nul_mad=m['nul_mad'], D_min=Dmin, t_min=tmin, cobertura=m['cobertura'],
                         sensor_extrems_raw=[list(np.round(s0, 1)), list(np.round(s1, 1))], sol_efectiu=[f['sol_x'] + f['cx'], f['sol_y'] + f['cy']])
        PR[nom] = (t, pr, prs)
        perf[f'{tn}_{nom[:-4]}'] = pr; perf['t'] = t
    # desplaçament perpendicular al llenç que tindria un patró fix al sensor, respecte de la referència (mitjana ponderada de cada grup)
    noms = list(INFO)
    for grup in ('sony_A', 'sony_B'):
        gg = [x for x in noms if INFO[x]['grup'] == grup]
        if not gg: continue
        wv = np.array([1 / INFO[x]['nul_mad'] ** 2 for x in gg]); sol = np.array([INFO[x]['sol_efectiu'] for x in gg]); ref = (wv[:, None] * sol).sum(0) / wv.sum()
        for x in gg:
            J = jacobia(MP['fotogrames'][x]); dcanvas = np.linalg.solve(J, -(np.array(INFO[x]['sol_efectiu']) - ref)); INFO[x]['dt_si_fix_al_sensor'] = float(n @ dcanvas); INFO[x]['dcanvas_si_fix_al_sensor'] = dcanvas.tolist()
    res['fotogrames'][tn] = INFO
    for nom in sorted(INFO, key=lambda x: (INFO[x]['grup'], INFO[x]['t_s'])):
        q = INFO[nom]
        print(f"{tn} {q['grup']} {nom} {q['exp']:>9.5f}s t {q['t_s']:>5.0f}s · D {q['D']*1e4:+6.1f}‱ z {q['z']:+5.1f} (σ {q['nul_mad']*1e4:.1f}) · mín {q['D_min']*1e4:+6.1f}‱ a t {q['t_min']:+5.1f} · Δt si sensor {q.get('dt_si_fix_al_sensor', np.nan):+5.1f} px", flush=True)
    # prova d'hipòtesi: perfil combinat desplaçat α·Δt
    def combina(sel, alfa, trams=None):
        num = 0; den = 0
        for x in sel:
            t, pr, prs = PR[x]; wv = 1 / INFO[x]['nul_mad'] ** 2; sh = alfa * INFO[x].get('dt_si_fix_al_sensor', 0.0)
            if trams is None: p = pr; tt = t
            else:
                tt = np.arange(-100, 100 + 1e-6, 0.5)
                with np.errstate(all='ignore'): p = np.nanmean(np.stack([prs[i] for i in trams]), 0)
            ps = np.interp(tt, tt - sh, np.nan_to_num(p), left=np.nan, right=np.nan)   # un patró a t = sh es porta a t = 0
            ok = np.isfinite(ps); num = num + np.where(ok, ps, 0) * wv; den = den + ok * wv
        tt_ = tt
        return tt_, np.where(den > 0, num / np.maximum(den, 1e-30), np.nan)
    ALF = np.arange(-1.0, 3.01, 0.25); rng = np.random.default_rng(1)
    for nomp, sel in (('A', [x for x in noms if INFO[x]['grup'] == 'sony_A']), ('B', [x for x in noms if INFO[x]['grup'] == 'sony_B']), ('A+B', noms)):
        if len(sel) < 2: continue
        prof = []
        for al in ALF:
            tt, p = combina(sel, al); prof.append(profunditat(tt, p, 0.0, nucli=TEMPLATE_S))
        prof = np.array(prof)
        boots = []
        for _ in range(200):
            tr_ = rng.integers(0, 8, 8); pb = []
            for al in ALF:
                tt, p = combina(sel, al, list(tr_)); pb.append(profunditat(tt, p, 0.0, nucli=TEMPLATE_S))
            pb = np.array(pb); boots.append(float(ALF[np.nanargmin(pb)]) if np.isfinite(pb).any() else np.nan)
        boots = np.array(boots); boots = boots[np.isfinite(boots)]
        spread = [INFO[x].get('dt_si_fix_al_sensor', 0.0) for x in sel]
        res['proves'][f'{tn}_{nomp}'] = dict(alfa=ALF, profunditat=prof, alfa_optima=float(ALF[np.nanargmin(prof)]), D_alfa0=float(prof[ALF == 0][0]), D_alfa1=float(prof[ALF == 1][0]),
                                             alfa_bootstrap_p16_p50_p84=np.percentile(boots, [16, 50, 84]).tolist() if len(boots) else None, frac_boot_alfa_menor_05=float(np.mean(boots < 0.5)) if len(boots) else None,
                                             dispersio_dt_sensor_px=[float(min(spread)), float(max(spread))], fotogrames=sel)
        print(f"{tn} {nomp:3s}: α òptima {ALF[np.nanargmin(prof)]:+.2f} · D(α=0) {prof[ALF == 0][0]*1e4:+.2f}‱ · D(α=1) {prof[ALF == 1][0]*1e4:+.2f}‱ · bootstrap α p16/50/84 {np.percentile(boots, [16, 50, 84]) if len(boots) else None} · Δt sensor de {min(spread):+.1f} a {max(spread):+.1f} px", flush=True)
desa(OUT / f'S4_PER_FOTOGRAMA_{var}.json', res); np.savez_compressed(OUT / f'S4_perfils_{var}.npz', **perf)
