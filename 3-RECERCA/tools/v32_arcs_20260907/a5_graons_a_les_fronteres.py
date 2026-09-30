"""A5 · El graó de nivell AL LLARG de cada frontera de fusió (mètode research/125).

Per a cada fotograma amb una frontera d'ENTRADA dins de 3 R☉ (on la seva fracció
de pes puja de <10 % a >50 % del seu altiplà anant cap enfora), es traça la
frontera r_i(θ) a 720 azimuts (radi del màxim de ∂f_i/∂r). Després es mostreja
la font FINA (ln G) al llarg de rajos radials centrats a la frontera, k = −150…150
px: recta de base ajustada a [−150,−90] ∪ [90,150]; graó = mediana del residu a
[20,70] − mediana a [−70,−20]. Control: el mateix a la frontera desplaçada ±120
px. El graó és positiu si fora és més brillant que dins respecte de la tendència.

Fonts: base V31 (G), Vixen sola, Sony B sola, Sony A sola. Cap correcció.
Sortida: 4-rebuts/A5_graons.json, lliurables/A5_GRAONS.md i figures per tren.
"""
from comu32 import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

SRC = {'base': (V31P / 'cau/base_G.npy', V31P / 'cau/support.npy'),
       'vixen': (FIX / 'vixen_corrected_G.npy', CAUF / 'vixen_support.npy'),
       'sonyB': (FIX / 'sony_B_corrected_G.npy', None),
       'sonyA': (FIX / 'sony_A_corrected_G.npy', None)}
PFX = 'A5'
if os.environ.get('V32'):
    SRC = {'base': (CAU32 / 'base_G_v32.npy', CAU32 / 'support_v32.npy'), 'vixen': (CAU32 / 'vixen_total_v32.npy', CAUF / 'vixen_support.npy'),
           'sonyB': (CAU32 / 'sony_B_total_v32.npy', None), 'sonyA': (CAU32 / 'sony_A_total_v32.npy', None),
           'vixen_orig': (FIX / 'vixen_corrected_G.npy', CAUF / 'vixen_support.npy'), 'sonyB_orig': (FIX / 'sony_B_corrected_G.npy', None)}
    PFX = 'A5v32'
NT = 720
KS = np.arange(-120, 121, 2, dtype=np.float32)
RMAX_R = 3.2


def entry_contours(tag, group=None, rmax=RMAX_R):
    """Frontera d'entrada (cap enfora) de cada fotograma: r_i(θ) en px, NaN on no n'hi ha."""
    Wm = np.load(CAU32 / f'{tag}_w.npy', mmap_mode='r'); meta = json.loads((CAU32 / f'{tag}_meta.json').read_text())['frames']
    idx = [m['i'] for m in meta if (group is None or m['group'] == group)]
    tot = np.zeros((HC, WC), np.float32)
    for i in idx:
        tot += Wm[i]
    th = np.arange(NT) * 2 * np.pi / NT
    rr = np.arange(0.95 * RS, rmax * RS, 2.0, dtype=np.float32)
    X = ((CX + rr[:, None] * np.cos(th)[None, :]) / Q).astype(np.float32); Y = ((CY + rr[:, None] * np.sin(th)[None, :]) / Q).astype(np.float32)
    out = {}
    for i in idx:
        f = np.where(tot > 0, Wm[i] / np.maximum(tot, 1e-20), 0).astype(np.float32)
        pf = cv2.remap(f, X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)   # (nr, nt)
        plateau = np.percentile(pf, 98)
        if plateau < 0.08:
            continue
        rc = np.full(NT, np.nan)
        for j in range(NT):
            col = pf[:, j]
            above = np.flatnonzero(col >= 0.5 * plateau)
            if len(above) == 0:
                continue
            k1 = above[0]
            below = np.flatnonzero(col[:k1] <= 0.1 * plateau)
            if len(below) == 0:
                continue                      # ja és dins del suport des del principi
            k0 = below[-1]
            seg = np.gradient(col[k0:k1 + 1])
            if len(seg) < 2:
                continue
            rc[j] = rr[k0 + int(np.argmax(seg))]
        if np.isfinite(rc).sum() < 0.5 * NT:
            continue
        out[meta[i]['name']] = {'r_px': rc, 'exp': meta[i]['exp'], 'plateau': float(plateau), 'i': i,
                                'r_R_median': float(np.nanmedian(rc) / RS), 'r_R_p10_p90': [float(np.nanpercentile(rc, 10) / RS), float(np.nanpercentile(rc, 90) / RS)]}
    return out


def step_along(arr, sup, rc, shift=0.0):
    th = np.arange(NT) * 2 * np.pi / NT
    R = (rc[None, :] + shift + KS[:, None]).astype(np.float32)          # (nk, nt)
    X = CX + R * np.cos(th)[None, :]; Y = CY + R * np.sin(th)[None, :]
    ok = np.isfinite(R)
    x0, x1 = int(np.nanmin(X)) - 2, int(np.nanmax(X)) + 3; y0, y1 = int(np.nanmin(Y)) - 2, int(np.nanmax(Y)) + 3
    x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, W), min(y1, H)
    a = np.ascontiguousarray(np.asarray(arr[y0:y1, x0:x1], np.float32)); m = np.isfinite(a) & (a > 0)
    if sup is not None:
        m &= np.asarray(sup[y0:y1, x0:x1]) > 0
    la = np.where(m, np.log(np.maximum(a, 1e-12)), 0).astype(np.float32)
    Xs = np.where(ok, X - x0, -10).astype(np.float32); Ys = np.where(ok, Y - y0, -10).astype(np.float32)
    v = cv2.remap(la, Xs, Ys, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    mm = cv2.remap(m.astype(np.float32), Xs, Ys, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) > 0.999
    return v, mm

def steps_from(v, mm):
    base_k = (np.abs(KS) >= 60); inner = (KS >= -50) & (KS <= -15); outer = (KS >= 15) & (KS <= 50)
    steps = np.full(NT, np.nan)
    A = np.stack([np.ones(base_k.sum()), KS[base_k], KS[base_k] ** 2], axis=1)
    for j in range(NT):
        g = mm[:, j]
        if g.sum() < 0.9 * len(KS):
            continue
        coef = np.linalg.lstsq(A, v[base_k, j], rcond=None)[0]
        res = v[:, j] - (coef[0] + coef[1] * KS + coef[2] * KS ** 2)
        steps[j] = np.median(res[outer]) - np.median(res[inner])
    return steps

def step_pair(arrX, supX, arrY, supY, rc, shift=0.0):
    """Graó de ln X i graó DIFERENCIAL ln X − ln Y (Y = l'altre tren, mateixa corona) al llarg de la frontera de X."""
    vX, mX = step_along(arrX, supX, rc, shift); vY, mY = step_along(arrY, supY, rc, shift)
    return steps_from(vX, mX), steps_from(vX - vY, mX & mY)


def main():
    plt.rcParams.update({'font.size': 8})
    arrs = {}
    for k, (p, s_) in SRC.items():
        a = np.load(p, mmap_mode='r'); arrs[k] = (a[..., 1] if a.ndim == 3 else a, (np.load(s_, mmap_mode='r') if s_ else None))
    if os.environ.get('V32'):
        combos = [('vixen', None, 'Vixen', ['base', 'vixen', 'sonyB_orig']), ('sony', 'sony_B', 'SonyB', ['base', 'sonyB', 'vixen_orig']), ('sony', 'sony_A', 'SonyA', ['sonyA', 'vixen_orig'])]
    else:
        combos = [('vixen', None, 'Vixen', ['base', 'vixen', 'sonyB']), ('sony', 'sony_B', 'SonyB', ['base', 'sonyB', 'vixen']), ('sony', 'sony_A', 'SonyA', ['sonyA', 'vixen'])]
    report = {}
    for tag, group, name, sources in combos:
        cont = entry_contours(tag, group)
        rows = []
        fig, ax = plt.subplots(len(cont), 1, figsize=(9, 1.6 * len(cont) + 1), sharex=True) if cont else (None, [])
        for n, (fname, c) in enumerate(sorted(cont.items(), key=lambda z: z[1]['r_R_median'])):
            row = {'frame': fname, 'exp': c['exp'], 'r_R_median': c['r_R_median'], 'r_R_p10_p90': c['r_R_p10_p90'], 'plateau_fraction': c['plateau'], 'fonts': {}}
            other = sources[-1]
            for src in sources[:-1]:
                arr, sup = arrs[src]; arrY, supY = arrs[other]
                s0, d0 = step_pair(arr, sup, arrY, supY, c['r_px'], 0.0); sm, dm = step_pair(arr, sup, arrY, supY, c['r_px'], -100.0); sp, dp = step_pair(arr, sup, arrY, supY, c['r_px'], +100.0)
                fin = np.isfinite(s0)
                row['fonts'][src] = {'graó_mediana_pct': float(100 * np.nanmedian(s0)), 'dispersio_pct': float(100 * np.nanstd(s0)), 'n_azimuts': int(fin.sum()),
                                     'control_-100_pct': float(100 * np.nanmedian(sm)), 'control_+100_pct': float(100 * np.nanmedian(sp)),
                                     'diferencial_vs_' + other: {'graó_mediana_pct': float(100 * np.nanmedian(d0)), 'dispersio_pct': float(100 * np.nanstd(d0)), 'control_-100_pct': float(100 * np.nanmedian(dm)), 'control_+100_pct': float(100 * np.nanmedian(dp)),
                                                               'p_signe': float(np.mean(np.sign(d0[np.isfinite(d0)]) == np.sign(np.nanmedian(d0)))) if np.isfinite(d0).any() else None}}
                if src == sources[0] and fig is not None:
                    s0, sm, sp = d0, dm, dp   # a la figura: el graó DIFERENCIAL
                    a = ax[n] if len(cont) > 1 else ax
                    a.plot(np.arange(NT) / 2, 100 * s0, 'k', lw=.6, label=f'ln {src} − ln {other} a la frontera'); a.plot(np.arange(NT) / 2, 100 * sm, color='.6', lw=.5, label='control −100 px'); a.plot(np.arange(NT) / 2, 100 * sp, color='.8', lw=.5, label='control +100 px')
                    a.axhline(0, color='r', lw=.4); a.set_ylabel(f"{fname[:-4]}\n{c['exp']:g}s @{c['r_R_median']:.2f}R", fontsize=7)
                    if n == 0:
                        a.legend(ncol=3, fontsize=6)
            rows.append(row)
            log(f"{name} {fname} {c['exp']:g}s r={c['r_R_median']:.2f}R: " + ' · '.join(f"{s} {row['fonts'][s]['graó_mediana_pct']:+.3f}% dif {row['fonts'][s]['diferencial_vs_'+other]['graó_mediana_pct']:+.3f}% (ctrl {row['fonts'][s]['diferencial_vs_'+other]['control_-100_pct']:+.3f}/{row['fonts'][s]['diferencial_vs_'+other]['control_+100_pct']:+.3f})" for s in sources[:-1]))
        if fig is not None:
            (ax[-1] if len(cont) > 1 else ax).set_xlabel('azimut [°]'); fig.suptitle(f'A5 · graó de ln G al llarg de la frontera d\'entrada de cada fotograma · {name}', fontsize=9); fig.tight_layout(); fig.savefig(VIS / f'{PFX}_graons_{name}.png', dpi=110); plt.close(fig)
        report[name] = rows
    savejson(REB / (PFX + '_graons.json'), {'metode': 'research/125: recta de base a |k|>=90 px, graó = mediana residu [20,70] − [−70,−20]; controls a ±120 px', 'rmax_R': RMAX_R, 'trens': report})
    lines = ['# A5 · graó de nivell a les fronteres d\'entrada (ln G, %) · base quadràtica ±60–120 px, finestres ±15–50 px', '', '| tren | fotograma | exp | r frontera (R☉) | font | graó propi | ctrl ±100 | graó DIFERENCIAL (font − altre tren) | dispersió | ctrl −100 | ctrl +100 | fracció mateix signe |', '|---|---|---|---|---|---|---|---|---|---|---|---|']
    for name, rows in report.items():
        for r in rows:
            for src, d in r['fonts'].items():
                k = [q for q in d if q.startswith('diferencial')][0]; dd = d[k]
                lines.append(f"| {name} | {r['frame'][:-4]} | {r['exp']:g} | {r['r_R_median']:.2f} ({r['r_R_p10_p90'][0]:.2f}–{r['r_R_p10_p90'][1]:.2f}) | {src} | {d['graó_mediana_pct']:+.3f} | {d['control_-100_pct']:+.3f}/{d['control_+100_pct']:+.3f} | {dd['graó_mediana_pct']:+.3f} | {dd['dispersio_pct']:.3f} | {dd['control_-100_pct']:+.3f} | {dd['control_+100_pct']:+.3f} | {dd['p_signe'] if dd['p_signe'] is None else round(dd['p_signe'],2)} |")
    (OUT32 / ('lliurables/' + PFX + '_GRAONS.md')).write_text('\n'.join(lines) + '\n')
    log('A5 fet')


if __name__ == '__main__':
    main()
