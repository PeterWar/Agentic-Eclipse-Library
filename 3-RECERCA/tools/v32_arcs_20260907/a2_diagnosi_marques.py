"""A2 · Cada marca lila/blau contra les fronteres de fusió HDR.

Per a cada marca del catàleg 145 (lila i blau), dins del seu sector (azimut de la
marca ± marge, radi p05−0,4R … p95+0,4R):

  1. perfil radial en ln (mitjana azimutal, 1 px) de la base V31 i de cada font
     per separat —Vixen sola, Sony A sola, Sony B sola, Sony fusionada— i el seu
     passa-alt radial (σ 24 i 96 px): amplitud de l'arc dins del tram marcat;
  2. fracció de pes de CADA fotograma en funció del radi (graella grossa d'A1):
     quins fotogrames entren o surten del compost dins del tram marcat;
  3. desnivell entre fotogrames al sector (mediana de ln(v_i)−ln(v_j) on els dos
     tenen pes ple), amb i sense els offsets del c03;
  4. prova de la cura en 1-D: compost gros del tren amb els nivells de cada
     fotograma igualats (camp ε_i(r) suavitzat 0,25 R☉) → quant baixa l'arc.

Sortides: 4-rebuts/A2_marques.json, lliurables/A2_TAULA.md, una figura per marca
(perfils + fraccions) i un muntatge 1:1 amb el passa-alt 24 de cada font, més el
mapa de fronteres de fusió del llenç sencer amb les marques a sobre.
Només lectura sobre totes les fonts.
"""
from comu32 import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from PIL import Image, ImageDraw

SRC = {
    'base':   V31P / 'cau/base_G.npy',
    'vixen':  FIX / 'vixen_corrected_G.npy',
    'sonyA':  FIX / 'sony_A_corrected_G.npy',
    'sonyB':  FIX / 'sony_B_corrected_G.npy',
    'sony':   FIX / 'sony_corrected_G.npy',
}
SUPPORT = {'base': V31P / 'cau/support.npy', 'vixen': CAUF / 'vixen_support.npy',
           'sonyA': None, 'sonyB': None, 'sony': CAUF / 'sony_support.npy'}
PFX = 'A2'
if os.environ.get('V32'):
    SRC = {'base': CAU32 / 'base_G_v32.npy', 'vixen': CAU32 / 'vixen_total_v32.npy', 'sonyA': CAU32 / 'sony_A_total_v32.npy', 'sonyB': CAU32 / 'sony_B_total_v32.npy', 'sony': CAU32 / 'sony_corrected_total_v32.npy'}
    SUPPORT['base'] = CAU32 / 'support_v32.npy'; PFX = 'A2v32'
HP_SIGMAS = (24, 96)
RMARGE = 0.40       # R☉ de marge radial a cada costat del tram pintat
TMARGE = 2.0        # graus de marge azimutal


def nan_smooth1d(p, s):
    ok = np.isfinite(p).astype(np.float64); v = np.where(ok > 0, p, 0.0)
    from scipy.ndimage import gaussian_filter1d
    num = gaussian_filter1d(v, s, mode='nearest'); den = gaussian_filter1d(ok, s, mode='nearest')
    out = np.where(den > 0.2, num / np.maximum(den, 1e-9), np.nan)
    return out


def sector_of(mark):
    x0, y0, x1, y1 = mark['bbox']
    xs = np.array([x0, x1, x0, x1], float); ys = np.array([y0, y0, y1, y1], float)
    th = np.degrees(np.arctan2(ys - CY, xs - CX))
    # span azimutal: el més petit que conté totes les cantonades (tractant el gir de ±180)
    c = np.degrees(np.arctan2(mark['center_xy'][1] - CY, mark['center_xy'][0] - CX))
    d = (th - c + 180) % 360 - 180
    t0, t1 = c + d.min() - TMARGE, c + d.max() + TMARGE
    r0 = max(1.0, mark['paint_radius_R_p05_p50_p95'][0] - RMARGE)
    r1 = mark['paint_radius_R_p05_p50_p95'][2] + RMARGE
    return r0, r1, t0, t1


def polar_profile(arr, sup, r0, r1, t0, t1, step_r=1.0):
    """Mitjana azimutal de ln(v) per radi (píxels), amb mostreig d'arc ~1 px."""
    rr = np.arange(r0 * RS, r1 * RS, step_r, dtype=np.float32)
    rmid = 0.5 * (r0 + r1) * RS
    nt = max(32, int(np.ceil(np.radians(t1 - t0) * rmid)))
    th = np.radians(np.linspace(t0, t1, nt, dtype=np.float32))
    X = CX + rr[:, None] * np.cos(th)[None, :]; Y = CY + rr[:, None] * np.sin(th)[None, :]
    xa, xb = int(np.floor(X.min())) - 2, int(np.ceil(X.max())) + 3
    ya, yb = int(np.floor(Y.min())) - 2, int(np.ceil(Y.max())) + 3
    xa, ya = max(xa, 0), max(ya, 0); xb, yb = min(xb, W), min(yb, H)
    crop = np.ascontiguousarray(np.asarray(arr[ya:yb, xa:xb], np.float32))
    ok = np.isfinite(crop) & (crop > 0)
    if sup is not None:
        ok &= np.asarray(sup[ya:yb, xa:xb]) > 0
    v = cv2.remap(np.where(ok, np.log(np.maximum(crop, 1e-12)), 0).astype(np.float32),
                  (X - xa).astype(np.float32), (Y - ya).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    m = cv2.remap(ok.astype(np.float32), (X - xa).astype(np.float32), (Y - ya).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    good = m > 0.999
    frac = good.mean(axis=1)
    prof = np.where(frac > 0.5, np.sum(np.where(good, v, 0), axis=1) / np.maximum(good.sum(axis=1), 1), np.nan)
    return rr / RS, prof.astype(np.float64), frac


def highpass(prof, sigma_px, step_r=1.0):
    return prof - nan_smooth1d(prof, sigma_px / step_r)


def arc_amplitude(rR, hp, lo, hi):
    k = (rR >= lo) & (rR <= hi) & np.isfinite(hp)
    if k.sum() < 5:
        return None
    seg = hp[k]
    return {'p2p_pct': float(100 * (seg.max() - seg.min())), 'rms_pct': float(100 * np.sqrt(np.mean(seg ** 2)))}


def coarse_sector(rc, tc, r0, r1, t0, t1):
    tcd = np.degrees(tc)
    d = (tcd - 0.5 * (t0 + t1) + 180) % 360 - 180
    return (rc >= r0 * RS) & (rc < r1 * RS) & (np.abs(d) <= 0.5 * (t1 - t0))


def frame_fractions(Wm, Vm, meta, cells, rc, binpx=8):
    """Fracció de pes per fotograma i valor per fotograma, per calaix radial dins del sector."""
    idx = np.flatnonzero(cells.ravel()); r = rc.ravel()[idx]
    b = ((r - r.min()) / binpx).astype(int); nb = int(b.max()) + 1
    rb = np.array([r[b == i].mean() for i in range(nb)]) / RS
    n = Wm.shape[0]
    F = np.zeros((n, nb)); Lv = np.full((n, nb), np.nan); tot = np.zeros(nb)
    for i in range(n):
        w = Wm[i].ravel()[idx]; v = Vm[i].ravel()[idx]
        sw = np.bincount(b, weights=w, minlength=nb); tot += sw; F[i] = sw
        vv = np.where(np.isfinite(v) & (v > 0), v, 0.0)
        sv = np.bincount(b, weights=w * vv, minlength=nb)
        Lv[i] = np.where(sw > 0, sv / np.maximum(sw, 1e-20), np.nan)
    F = F / np.maximum(tot, 1e-20)
    return rb, F, Lv, tot


def coherent_test(rb, F, Lv, meta, lo, hi, with_offsets=True, sig_R=0.25, binR=None):
    """Compost gros del tren: tal com és, i amb els nivells per fotograma igualats."""
    n = len(meta)
    lev = np.full_like(Lv, np.nan)
    for i, mt in enumerate(meta):
        lev[i] = Lv[i] * mt['k'] + (mt['offset_G'] if with_offsets else 0.0)
    good = np.isfinite(lev) & (lev > 0) & (F > 0)
    C = np.nansum(np.where(good, F * lev, 0), axis=0) / np.maximum(np.where(good, F, 0).sum(axis=0), 1e-20)
    C[~(good.any(axis=0))] = np.nan
    lnC = np.log(np.maximum(C, 1e-20))
    drb = float(np.median(np.diff(rb))) if len(rb) > 1 else 1.0   # R☉ per calaix
    drb_px = drb * RS
    s = sig_R / max(drb, 1e-6)
    eps = np.full_like(lev, np.nan)
    for i in range(n):
        e = np.where(good[i] & (F[i] > 0.05), np.log(np.maximum(lev[i], 1e-20)) - lnC, np.nan)
        if np.isfinite(e).sum() >= 3:
            es = nan_smooth1d(e, s)
            # extensió constant fora del suport propi
            ok = np.isfinite(es)
            if ok.any():
                es = np.interp(np.arange(len(es)), np.flatnonzero(ok), es[ok])
            eps[i] = es
    lev2 = np.where(np.isfinite(eps), lev * np.exp(-eps), lev)
    good2 = np.isfinite(lev2) & (lev2 > 0) & (F > 0)
    C2 = np.nansum(np.where(good2, F * lev2, 0), axis=0) / np.maximum(np.where(good2, F, 0).sum(axis=0), 1e-20)
    C2[~(good2.any(axis=0))] = np.nan
    out = {}
    for sg in HP_SIGMAS:
        hp1 = highpass(np.log(np.maximum(C, 1e-20)), sg, drb_px); hp2 = highpass(np.log(np.maximum(C2, 1e-20)), sg, drb_px)
        a1 = arc_amplitude(rb, hp1, lo, hi); a2 = arc_amplitude(rb, hp2, lo, hi)
        out[f'hp{sg}'] = {'abans': a1, 'despres': a2,
                          'reduccio': (1 - a2['rms_pct'] / a1['rms_pct']) if a1 and a2 and a1['rms_pct'] > 0 else None}
    return C, C2, eps, out


def level_pairs(Lv, F, meta, lo, hi, rb):
    """Desnivell entre parelles de fotogrames amb pes alt dins del tram."""
    k = (rb >= lo - 0.2) & (rb <= hi + 0.2)
    rows = []
    n = len(meta)
    strong = [i for i in range(n) if np.nanmax(np.where(k, F[i], 0)) > 0.15]
    for a in range(len(strong)):
        for c in range(a + 1, len(strong)):
            i, j = strong[a], strong[c]
            both = k & np.isfinite(Lv[i]) & np.isfinite(Lv[j]) & (Lv[i] > 0) & (Lv[j] > 0) & (F[i] > 0.05) & (F[j] > 0.05)
            if both.sum() < 3:
                continue
            li = Lv[i][both] * meta[i]['k']; lj = Lv[j][both] * meta[j]['k']
            d0 = float(100 * np.median(np.log(li / lj)))
            d1 = float(100 * np.median(np.log((li + meta[i]['offset_G']) / (lj + meta[j]['offset_G']))))
            rows.append({'i': meta[i]['name'], 'j': meta[j]['name'], 'exp_i': meta[i]['exp'], 'exp_j': meta[j]['exp'],
                         'bins': int(both.sum()), 'desnivell_pct_sense_offset': d0, 'desnivell_pct_amb_offset': d1})
    return rows


def transitions(rb, F, meta, lo, hi):
    rows = []
    k = (rb >= lo - 0.15) & (rb <= hi + 0.15)
    for i, mt in enumerate(meta):
        f = F[i]
        if np.nanmax(f) < 0.05:
            continue
        fk = f[k]
        if len(fk) < 2:
            continue
        change = float(fk.max() - fk.min())
        if change < 0.10:
            continue
        g = np.abs(np.gradient(f, rb)); g[~k] = 0
        jr = int(np.argmax(g))
        rows.append({'name': mt['name'], 'exp': mt['exp'], 'group': mt['group'], 'canvi_fraccio': change,
                     'fraccio_dins': float(fk[0]), 'fraccio_fora': float(fk[-1]), 'r_transicio_R': float(rb[jr])})
    rows.sort(key=lambda z: -z['canvi_fraccio'])
    return rows


def passalt_crop(arr, sup, x0, y0, x1, y1, s=24, pad=96):
    xa, ya = max(x0 - pad, 0), max(y0 - pad, 0); xb, yb = min(x1 + pad, W), min(y1 + pad, H)
    a = np.ascontiguousarray(np.asarray(arr[ya:yb, xa:xb], np.float32))
    m = np.isfinite(a) & (a > 0)
    if sup is not None:
        m &= np.asarray(sup[ya:yb, xa:xb]) > 0
    la = np.where(m, np.log(np.maximum(a, 1e-12)), 0).astype(np.float32)
    hp = np.where(m, la - normgauss(la, m.astype(np.float32), s), np.nan)
    return hp[y0 - ya:y1 - ya, x0 - xa:x1 - xa], m[y0 - ya:y1 - ya, x0 - xa:x1 - xa]


def to_u8(hp, scale):
    v = np.nan_to_num(hp, nan=0.0) / scale
    return np.uint8(np.clip(0.5 + 0.5 * v, 0, 1) * 255)


def main():
    plt.rcParams.update({'font.size': 8})
    rc, tc = coarse_polar()
    arrs = {}
    for k, p in SRC.items():
        a = np.load(p, mmap_mode='r'); arrs[k] = a[..., 1] if a.ndim == 3 else a
    sups = {k: (np.load(p, mmap_mode='r') if p else None) for k, p in SUPPORT.items()}
    coarse = {}
    for tag in ('sony', 'vixen'):
        coarse[tag] = (np.load(CAU32 / f'{tag}_w.npy', mmap_mode='r'), np.load(CAU32 / f'{tag}_v.npy', mmap_mode='r'),
                       json.loads((CAU32 / f'{tag}_meta.json').read_text())['frames'])
    ms = marks(); results = []
    pass
    for n, mk in enumerate(ms):
        r0, r1, t0, t1 = sector_of(mk); lo, hi = mk['paint_radius_R_p05_p50_p95'][0], mk['paint_radius_R_p05_p50_p95'][2]
        res = {'id': mk['id'], 'layer': mk['layer'], 'color': mk['color'], 'family': mk['family'], 'bbox': mk['bbox'],
               'r_p05_p50_p95': mk['paint_radius_R_p05_p50_p95'], 'sector': {'r0': r0, 'r1': r1, 'az0': t0, 'az1': t1}, 'profiles': {}}
        prof = {}
        for src in SRC:
            rR, p, frac = polar_profile(arrs[src], sups[src], r0, r1, t0, t1)
            prof[src] = (rR, p, frac)
            e = {'cobertura_tram': float(np.nanmean(frac[(rR >= lo) & (rR <= hi)])) if ((rR >= lo) & (rR <= hi)).any() else 0.0}
            for sg in HP_SIGMAS:
                e[f'hp{sg}'] = arc_amplitude(rR, highpass(p, sg), lo, hi)
            res['profiles'][src] = e
        # correlació entre fonts independents dins del tram (el que no comparteixen no és corona)
        res['creuat'] = {}
        for sg in HP_SIGMAS:
            hp = {src: highpass(prof[src][1], sg) for src in SRC}
            rR = prof['base'][0]; k = (rR >= lo) & (rR <= hi)
            def corr(a, b):
                g = k & np.isfinite(hp[a]) & np.isfinite(hp[b])
                if g.sum() < 8: return None
                x, y = hp[a][g] - hp[a][g].mean(), hp[b][g] - hp[b][g].mean()
                d = np.sqrt((x * x).sum() * (y * y).sum())
                return float((x * y).sum() / d) if d > 0 else None
            res['creuat'][f'hp{sg}'] = {'vixen_sonyB': corr('vixen', 'sonyB'), 'sonyA_sonyB': corr('sonyA', 'sonyB'), 'vixen_sonyA': corr('vixen', 'sonyA'),
                                       'rms_pct_vixen_menys_sonyB': (float(100 * np.sqrt(np.nanmean((hp['vixen'] - hp['sonyB'])[k] ** 2))) if k.any() else None)}
        # tren que domina el tram
        rmid = mk['paint_radius_R_p05_p50_p95'][1]
        trains = ['sony'] if rmid > 2.65 else (['vixen'] if rmid < 2.0 else ['vixen', 'sony'])
        res['trens'] = {}
        fig, ax = plt.subplots(2 + len(trains), 1, figsize=(9, 3.2 * (2 + len(trains))), sharex=True)
        for src, colr in [('base', 'k'), ('vixen', 'tab:green'), ('sonyA', 'tab:orange'), ('sonyB', 'tab:red'), ('sony', 'tab:purple')]:
            rR, p, _ = prof[src]
            ax[0].plot(rR, 100 * highpass(p, 96), color=colr, lw=.8, label=src)
            ax[1].plot(rR, 100 * highpass(p, 24), color=colr, lw=.6, label=src)
        for a in ax[:2]:
            a.axvspan(lo, hi, color='violet' if mk['color'] == 'lila' else 'deepskyblue', alpha=.18); a.axhline(0, color='.6', lw=.5)
        ax[0].set_ylabel('passa-alt radial σ96 [%]'); ax[1].set_ylabel('passa-alt radial σ24 [%]'); ax[0].legend(ncol=5, fontsize=7)
        for ti, tag in enumerate(trains):
            Wm, Vm, meta = coarse[tag]
            cells = coarse_sector(rc, tc, r0, r1, t0, t1)
            if cells.sum() < 20:
                continue
            rb, F, Lv, tot = frame_fractions(Wm, Vm, meta, cells, rc)
            tr = transitions(rb, F, meta, lo, hi); pairs = level_pairs(Lv, F, meta, lo, hi, rb)
            C, C2, eps, coh = coherent_test(rb, F, Lv, meta, lo, hi)
            res['trens'][tag] = {'transicions': tr, 'parelles': pairs, 'cura_1d': coh,
                                 'fotogrames_amb_pes': [meta[i]['name'] for i in range(len(meta)) if np.nanmax(F[i]) > 0.05]}
            a = ax[2 + ti]; bottom = np.zeros(len(rb))
            order = np.argsort([-np.nanmax(F[i]) for i in range(len(meta))])
            cmap = plt.get_cmap('tab20')
            for jj, i in enumerate(order[:14]):
                if np.nanmax(F[i]) < 0.03:
                    continue
                a.fill_between(rb, bottom, bottom + F[i], color=cmap(jj % 20), lw=0, label=f"{meta[i]['name'][:-4]} {meta[i]['exp']:g}s")
                bottom = bottom + F[i]
            a.axvspan(lo, hi, color='violet' if mk['color'] == 'lila' else 'deepskyblue', alpha=.18)
            a.set_ylim(0, 1); a.set_ylabel(f'fracció de pes · {tag}'); a.legend(ncol=4, fontsize=6, loc='upper right')
            ax2 = a.twinx()
            dpx = float(np.median(np.diff(rb))) * RS
            ax2.plot(rb, 100 * highpass(np.log(np.maximum(C, 1e-20)), 96, dpx), 'k', lw=.8, label='compost gros')
            ax2.plot(rb, 100 * highpass(np.log(np.maximum(C2, 1e-20)), 96, dpx), 'r', lw=.8, ls='--', label='nivells igualats')
            ax2.set_ylabel('σ96 [%]'); ax2.legend(fontsize=6, loc='upper left')
        ax[-1].set_xlabel('r [R☉]')
        fig.suptitle(f"{mk['id']} · {mk['layer']} · {mk['color']} · {mk['family']} · az {t0:.0f}…{t1:.0f}°", fontsize=9)
        fig.tight_layout(); fig.savefig(VIS / f"{PFX}_{mk['id']}_perfils.png", dpi=110); plt.close(fig)
        # muntatge 1:1 del passa-alt 24 de cada font
        x0, y0, x1, y1 = mk['window_bbox'] if 'window_bbox' in mk else mk['bbox']
        cx, cy = int(mk['center_xy'][0]), int(mk['center_xy'][1]); half = int(max(384, min(768, max(x1 - x0, y1 - y0) // 2 + 64)))
        X0, Y0, X1, Y1 = max(cx - half, 0), max(cy - half, 0), min(cx + half, W), min(cy + half, H)
        panels = []
        scale = None
        for src in ('base', 'vixen', 'sonyA', 'sonyB'):
            hp, m = passalt_crop(arrs[src], sups[src], X0, Y0, X1, Y1)
            if scale is None:
                z = hp[np.isfinite(hp)]; scale = float(np.percentile(np.abs(z), 99)) if z.size else 1.0
            panels.append((src, hp, m))
        im = Image.new('L', ((X1 - X0) * 4 + 30, (Y1 - Y0) + 26), 40); dr = ImageDraw.Draw(im)
        for i, (src, hp, m) in enumerate(panels):
            u = to_u8(np.where(m, hp, np.nan), scale); u[~m] = 40
            im.paste(Image.fromarray(u), (i * ((X1 - X0) + 10), 26))
            dr.text((i * ((X1 - X0) + 10) + 6, 6), f"{src} · passa-alt 24 (ln) · ±{100*scale:.2f}%", fill=255)
            bx0, by0, bx1, by1 = mk['bbox']
            dr.rectangle([i * ((X1 - X0) + 10) + bx0 - X0, 26 + by0 - Y0, i * ((X1 - X0) + 10) + bx1 - X0, 26 + by1 - Y0], outline=200)
        im.save(VIS / f"{PFX}_{mk['id']}_passalt_fonts.png")
        results.append(res)
        log(f"{n+1}/{len(ms)} {mk['id']} {mk['family']} r {lo:.2f}-{hi:.2f}")
    savejson(REB / (PFX + '_marques.json'), {'marques': results, 'fonts': {k: str(v) for k, v in SRC.items()}, 'hp_sigmes_px': HP_SIGMAS,
                                      'marge_R': RMARGE, 'marge_az_deg': TMARGE, 'nota': 'diagnosi; cap correcció aplicada a cap producte'})
    # taula resum
    lines = [f'# {PFX} · marques lila/blau contra fronteres de fusió', '',
             '| marca | capa | color | família | r p05-p95 | arc base σ96 % | vixen | sonyA | sonyB | r(Vixen,SonyB) σ96/σ24 | r(SonyA,SonyB) σ96/σ24 | fotogrames que canvien (tren dominant) | cura 1-D σ96 |', '|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    for r in results:
        def amp(src):
            e = r['profiles'][src]['hp96']; return f"{e['rms_pct']:.3f}" if e else '–'
        tr = ''; cure = ''
        for tag, d in r['trens'].items():
            tr += tag + ': ' + ', '.join(f"{z['name'][:-4]}({z['exp']:g}s Δf{z['canvi_fraccio']:.2f}@{z['r_transicio_R']:.2f})" for z in d['transicions'][:4]) + ' '
            c = d['cura_1d']['hp96']
            if c['reduccio'] is not None:
                cure += f"{tag} {100*c['reduccio']:.0f}% "
        def cc(pair):
            a, b = r['creuat']['hp96'][pair], r['creuat']['hp24'][pair]
            return (f"{a:+.2f}" if a is not None else '–') + '/' + (f"{b:+.2f}" if b is not None else '–')
        lines.append(f"| {r['id']} | {r['layer'][:22]} | {r['color']} | {r['family'][:26]} | {r['r_p05_p50_p95'][0]:.2f}-{r['r_p05_p50_p95'][2]:.2f} | {amp('base')} | {amp('vixen')} | {amp('sonyA')} | {amp('sonyB')} | {cc('vixen_sonyB')} | {cc('sonyA_sonyB')} | {tr} | {cure} |")
    (OUT32 / ('lliurables/' + PFX + '_TAULA.md')).write_text('\n'.join(lines) + '\n')
    log('A2 fet')


if __name__ == '__main__':
    main()
