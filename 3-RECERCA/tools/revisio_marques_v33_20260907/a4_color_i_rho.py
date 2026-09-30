"""A4 · Dues hipòtesis mesurades a la font.

1. Interior (marques a 1,5–2,3 R☉ sense cap canvi de fotograma): ¿és l'anell només-verd de la
   Vixen (research/102: ~1,85 R☉, cv 13 % en radi, G sol)? Perfil radial de ln(G/R) i ln(G/B)
   per anells d'1 px (mitjana azimutal a tot el suport i al sector de cada marca) de la Vixen V32
   i de la Sony B V32; passa-alt σ24; amplitud dins del traç contra controls a ±0,25 R☉.
2. Exterior (arc 4,2–4,6 R☉): ¿és un colze del camp de guany ρ (ajustat a 1,5–4,0 R☉ i omplert per
   veí més proper fora)? Perfil radial de ln ρ_G per anells, primera i segona derivades, i el radi
   on ρ esdevé constant al llarg del raig (inici de l'ompliment).
3. Taca NE (7,5–8,2 R☉): amplitud amb filtre adaptat (disc 25 px − anell 40–70 px) a base V32,
   Vixen, Sony A, Sony B, V31 base, i a les capes 02/05/06; si és en A i B a la mateixa posició
   del cel és del cel; si només en una, del tren.
Només lectura."""
from extract import *
from scipy.ndimage import gaussian_filter1d, gaussian_filter
V32T = ROOT / 'research/tools/v32_arcs_20260907'; C32 = V32T / 'cau'; V31P = ROOT / 'research/tools/v31_purs'
H, W = 7506, 10551


def ring_profile(v, ok, r, r0, r1, step=1.0):
    ri = np.floor((r - r0 * RS) / step).astype(np.int32); k = ok & (ri >= 0) & (ri < int((r1 - r0) * RS / step))
    n = np.bincount(ri[k], minlength=int((r1 - r0) * RS / step)); s = np.bincount(ri[k], weights=v[k], minlength=len(n))
    prof = np.where(n > 20, s / np.maximum(n, 1), np.nan); rr = r0 + (np.arange(len(n)) + 0.5) * step / RS
    return rr, prof, n


def hp(p, s):
    ok = np.isfinite(p).astype(float); v = np.where(ok > 0, p, 0)
    sm = gaussian_filter1d(v, s, mode='nearest') / np.maximum(gaussian_filter1d(ok, s, mode='nearest'), 1e-9)
    return np.where(ok > 0, p - sm, np.nan)


def main():
    cat = json.loads(Path(RUN.rebut('review_catalog.json')).read_text())
    x0, x1, y0, y1 = int(CX - 2.8 * RS), int(CX + 2.8 * RS) + 1, int(CY - 2.8 * RS), int(CY + 2.8 * RS) + 1
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32); r = np.hypot(xx - CX, yy - CY); t = np.degrees(np.arctan2(yy - CY, xx - CX))
    out = {'interior_color_ring': {}, 'rho': {}, 'taca_NE': {}}
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(3, 1, figsize=(9, 9), sharex=True)
    for tag, path, sup in [('vixen', C32 / 'vixen_total_v32.npy', ROOT / 'research/tools/v29/cau_final/vixen_support.npy'), ('sonyB', C32 / 'sony_B_total_v32.npy', None), ('sonyA', C32 / 'sony_A_total_v32.npy', None)]:
        a = np.load(path, mmap_mode='r'); A = np.asarray(a[y0:y1, x0:x1], np.float32)
        ok = np.isfinite(A).all(axis=2) & (A > 0).all(axis=2)
        if sup is not None:
            ok &= np.asarray(np.load(sup, mmap_mode='r')[y0:y1, x0:x1]) > 0
        lg = np.log(np.maximum(A[..., 1], 1e-9)); lr = np.log(np.maximum(A[..., 0], 1e-9)); lb = np.log(np.maximum(A[..., 2], 1e-9))
        gr, gb = lg - lr, lg - lb
        rr, pgr, n = ring_profile(gr, ok, r, 1.05, 2.7); _, pgb, _ = ring_profile(gb, ok, r, 1.05, 2.7); _, pg, _ = ring_profile(lg, ok, r, 1.05, 2.7)
        h24 = {'G/R': hp(pgr, 24), 'G/B': hp(pgb, 24), 'G': hp(pg, 24)}
        ax[0].plot(rr, 100 * h24['G/R'], lw=.8, label=f'{tag} ln(G/R) σ24'); ax[1].plot(rr, 100 * h24['G/B'], lw=.8, label=f'{tag} ln(G/B) σ24'); ax[2].plot(rr, 100 * h24['G'], lw=.8, label=f'{tag} ln G σ24')
        res = {'global': {k: {'rms_pct_1.5_2.3': float(100 * np.sqrt(np.nanmean(v[(rr > 1.5) & (rr < 2.3)] ** 2))), 'rms_pct_2.3_2.7': float(100 * np.sqrt(np.nanmean(v[(rr > 2.3) & (rr < 2.7)] ** 2)))} for k, v in h24.items()}, 'marks': []}
        # per sector de cada marca interior
        for m in cat['marks']:
            lo, _, hi = m['paint_radius_R_p05_p50_p95']
            if hi > 2.6 or m['color'] == 'neutre':
                continue
            a0, a1 = m['paint_azimuth_deg_min_max']
            if a1 - a0 > 300:
                sect = np.ones_like(ok)
            else:
                sect = (t >= a0 - 2) & (t <= a1 + 2)
            row = {'id': m['id'], 'r': [lo, hi]}
            for k, fld in (('G/R', gr), ('G/B', gb), ('G', lg)):
                rr2, p2, n2 = ring_profile(fld, ok & sect, r, max(1.02, lo - 0.45), hi + 0.45); h = hp(p2, 24)
                ins = (rr2 >= lo) & (rr2 <= hi); ctl = ((rr2 >= lo - 0.35) & (rr2 < lo - 0.1)) | ((rr2 > hi + 0.1) & (rr2 <= hi + 0.35))
                row[k] = {'rms_pct_dins': float(100 * np.sqrt(np.nanmean(h[ins] ** 2))) if np.isfinite(h[ins]).sum() > 3 else None, 'rms_pct_control': float(100 * np.sqrt(np.nanmean(h[ctl] ** 2))) if np.isfinite(h[ctl]).sum() > 3 else None,
                          'p2p_pct_dins': float(100 * (np.nanmax(h[ins]) - np.nanmin(h[ins]))) if np.isfinite(h[ins]).sum() > 3 else None}
            res['marks'].append(row)
        out['interior_color_ring'][tag] = res
        del A, lg, lr, lb, gr, gb
    for a_ in ax:
        a_.axhline(0, color='.6', lw=.5); a_.legend(fontsize=7, ncol=3)
        for r_ in (1.21, 1.33, 1.47, 1.96, 2.0, 2.65):
            a_.axvline(r_, color='.5', lw=.5, ls='--')
    ax[0].set_ylabel('%'); ax[1].set_ylabel('%'); ax[2].set_ylabel('%'); ax[2].set_xlabel('r [R☉]')
    ax[0].set_title('Perfils radials passa-alt σ24 (mitjana azimutal, tot el suport): color G/R, G/B i G sol, per tren', fontsize=9)
    fig.tight_layout(); fig.savefig(RUN.vista('R32_A4_anell_color_perfils.png'), dpi=120); plt.close(fig)
    # 2. ρ
    rho = np.load(C32 / 'rho_v32.npy', mmap_mode='r')
    X0, X1, Y0, Y1 = int(CX - 6.5 * RS), int(CX + 6.5 * RS) + 1, int(CY - 6.5 * RS), int(CY + 6.5 * RS) + 1
    X0, Y0 = max(X0, 0), max(Y0, 0); X1, Y1 = min(X1, W), min(Y1, H)
    yy, xx = np.mgrid[Y0:Y1, X0:X1].astype(np.float32); r2 = np.hypot(xx - CX, yy - CY); t2 = np.degrees(np.arctan2(yy - CY, xx - CX))
    lrho = np.log(np.asarray(rho[Y0:Y1, X0:X1, 1], np.float32)); ms = np.asarray(np.load(ROOT / 'research/tools/v29/cau_final/sony_support.npy', mmap_mode='r')[Y0:Y1, X0:X1]) > 0
    rr, prho, n = ring_profile(lrho, ms, r2, 1.5, 6.4, step=4.0)
    d1 = np.gradient(prho, rr); d2 = np.gradient(d1, rr)
    # radi on ρ esdevé constant al llarg del raig: |∂ρ/∂r| < 1e-6 per azimut
    gy, gx = np.gradient(lrho); dr_ = (gx * (xx - CX) + gy * (yy - CY)) / np.maximum(r2, 1)
    const = (np.abs(dr_) < 1e-7) & ms & (r2 > 3.0 * RS)
    rconst = {}
    for a0 in range(-180, 180, 30):
        k = const & (t2 >= a0) & (t2 < a0 + 30)
        rconst[f'{a0}..{a0+30}'] = float(np.min(r2[k]) / RS) if k.any() else None
    out['rho'] = {'ring_profile_R': rr.tolist(), 'ln_rho_G_pct': (100 * prho).tolist(), 'd1_pct_per_R': (100 * d1).tolist(), 'd2_pct_per_R2': (100 * d2).tolist(),
                  'radi_inici_omplert_constant_per_sector': rconst, 'nota': 'ρ ajustat a 1,5–4,0 R☉ (b3), suavitzat σ256 a 1/8 i omplert per veí més proper fora del domini'}
    fig, ax = plt.subplots(3, 1, figsize=(9, 8), sharex=True)
    ax[0].plot(rr, 100 * prho); ax[0].set_ylabel('ln ρ_G [%]'); ax[1].plot(rr, 100 * d1); ax[1].set_ylabel('∂/∂r [%/R☉]'); ax[2].plot(rr, 100 * d2); ax[2].set_ylabel('∂²/∂r² [%/R☉²]'); ax[2].set_xlabel('r [R☉]')
    for a_ in ax:
        a_.axvspan(4.2, 4.6, color='violet', alpha=.15); a_.axvline(4.0, color='.4', ls='--', lw=.6)
    ax[0].set_title('Camp de guany ρ (G) de la V32: perfil radial (mitjana azimutal) i derivades; franja = arc marcat 4,2–4,6', fontsize=9)
    fig.tight_layout(); fig.savefig(RUN.vista('R32_A4_rho_perfil.png'), dpi=120); plt.close(fig)
    # vista 2D de ln ρ passa-alt σ64 a 3–6 R☉
    hp2 = lrho - gaussian_filter(lrho, 64); u = np.uint8(np.clip(0.5 + hp2 / 0.002, 0, 1) * 255); u[~ms] = 40
    im = Image.fromarray(u); im.thumbnail((1400, 1400)); im.save(RUN.vista('R32_A4_rho_passalt64_2D.png'))
    # 3. taca NE
    marks_ne = [m for m in cat['marks'] if m['family'] == 'Anomalia local NE']
    m0 = marks_ne[0]; cx0, cy0 = m0['center_xy']; half = 220
    ya, yb, xa, xb = int(cy0 - half), int(cy0 + half), int(cx0 - half), int(cx0 + half)
    yy3, xx3 = np.mgrid[ya:yb, xa:xb].astype(np.float32)
    srcs = {'base_V32': C32 / 'base_G_v32.npy', 'base_V31': V31P / 'cau/base_G.npy', 'vixen_V32': C32 / 'vixen_total_v32.npy', 'sonyA_V32': C32 / 'sony_A_total_v32.npy', 'sonyB_V32': C32 / 'sony_B_total_v32.npy',
            'capa_02': C32 / '02_v32_u16.npy', 'capa_05': C32 / '05_v32_u16.npy', 'capa_06': C32 / '06_v32_u16.npy'}
    panels = []; rep = {}
    for k, p in srcs.items():
        a = np.load(p, mmap_mode='r'); A = np.asarray(a[ya:yb, xa:xb, 1] if a.ndim == 3 else a[ya:yb, xa:xb], np.float32)
        ok = np.isfinite(A) & (A > 0)
        if ok.mean() < 0.5:
            rep[k] = None; continue
        v = np.log(np.maximum(A, 1e-9)) if not k.startswith('capa') else A / 65535
        v = np.where(ok, v, np.nanmedian(v[ok]))
        # filtre adaptat centrat al màxim local de |resposta| dins de 60 px del centre de la marca
        sm = gaussian_filter(v, 6); bg = gaussian_filter(v, 40); resp = sm - bg
        cy_, cx_ = half, half; win = resp[cy_ - 60:cy_ + 60, cx_ - 60:cx_ + 60]; iy, ix = np.unravel_index(np.argmax(np.abs(win)), win.shape)
        py, px = cy_ - 60 + iy, cx_ - 60 + ix; amp = float(resp[py, px]); noise = float(np.std(resp[ok & (np.hypot(xx3 - cx0, yy3 - cy0) > 120)]))
        rep[k] = {'amplitud_pct_o_u': 100 * amp if not k.startswith('capa') else amp, 'soroll_pct_o_u': 100 * noise if not k.startswith('capa') else noise, 'snr': amp / noise if noise > 0 else None, 'pos_xy': [int(px + xa), int(py + ya)]}
        sc = np.percentile(np.abs(resp[ok]), 99.5); u = np.uint8(np.clip(0.5 + resp / (2 * sc), 0, 1) * 255); u[~ok] = 40
        panels.append((k, u, rep[k]))
    im = Image.new('L', (len(panels) * (2 * half + 8), 2 * half + 30), 30); dr = ImageDraw.Draw(im)
    for i, (k, u, rp) in enumerate(panels):
        im.paste(Image.fromarray(u), (i * (2 * half + 8), 30)); dr.text((i * (2 * half + 8) + 4, 4), f"{k} · resposta σ6−σ40 · snr {rp['snr']:.1f}", fill=255)
        dr.ellipse([i * (2 * half + 8) + rp['pos_xy'][0] - xa - 30, 30 + rp['pos_xy'][1] - ya - 30, i * (2 * half + 8) + rp['pos_xy'][0] - xa + 30, 30 + rp['pos_xy'][1] - ya + 30], outline=200)
    im.save(RUN.vista('R32_A4_taca_NE_fonts.png'))
    out['taca_NE'] = {'centre_marca_xy': [cx0, cy0], 'r_R': m0['paint_radius_R_p05_p50_p95'], 'fonts': rep}
    write(RUN.rebut('R32_A4_color_rho_taca.json'), out)
    print('A4 fet'); print(json.dumps({k: v['global'] for k, v in out['interior_color_ring'].items()}, indent=1)); print('rho const per sector', rconst); print('taca', json.dumps(rep, indent=1))


if __name__ == '__main__':
    main()
