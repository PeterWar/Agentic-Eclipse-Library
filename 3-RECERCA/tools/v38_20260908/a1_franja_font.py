"""A1 (V38) · La franja de l'oest a la FONT: recomposició fotograma a fotograma (Vixen, 67 fotogrames, canal G i RGB) de la corona
interior (caixa ±1,13 R☉) a resolució completa, amb la distància de cada píxel a la vora lunar MODELADA de cada fotograma.
Mesura: (a) reproducció exacta de vixen_total_v36 (guardarail 12); (b) perfil de biaix de cada fotograma contra un compost NET
(només contribucions a > 15 px de qualsevol vora lunar) en funció de la distància a la seva pròpia vora; (c) posició real del
limbe de cada fotograma contra la modelada; (d) gra i arcs de la franja amb la màscara vigent i amb guardes/esvaïments alternatius.
Només lectura sobre RAW i runs; escriu cau/ i rebuts."""
from comu38 import *
from scipy.ndimage import gaussian_filter

BOX_R = 1.13; DCLEAN = 15.0
Y0, Y1, X0, X1 = int(CY - BOX_R * RS), int(CY + BOX_R * RS), int(CX - BOX_R * RS), int(CX + BOX_R * RS)
SECTORS = {'W': (150, 210), 'SE': (20, 60), 'N_control': (-105, -75), 'E': (-15, 15)}


def sector_mask(th, a0, a1):
    ang = ((th - 0.5 * (a0 + a1) + 180) % 360) - 180
    return np.abs(ang) <= 0.5 * (a1 - a0)


def main():
    path = RUNS['vixen']; run = comu.Run.obre(str(path)); ctx = f2.Ctx(run)
    pos = json.loads((path / '4-rebuts/F1.3_registre.json').read_text())['fotogrames']
    kq = json.loads((path / '4-rebuts/F2.2_coherencia.json').read_text())['k']
    meta = json.loads((CAU36 / 'vixen_meta.json').read_text())['frames']; names = [m['name'] for m in meta]
    b1 = json.loads((REB36 / 'B1_camps_vixen.json').read_text()); assert b1['frames'] == names
    phis = {c: np.load(CAU36 / f'vixen_{c}_phi.npy', mmap_mode='r') for c in ('R', 'G', 'B')}
    fcorr, frep = flat_ripple_correction(ctx, 'vixen')
    inv = cv2.invertAffineTransform(COMMON_TO_FINAL)
    yy, xx = np.mgrid[Y0:Y1, X0:X1].astype(np.float32)
    qx = inv[0, 0] * xx + inv[0, 1] * yy + inv[0, 2]; qy = inv[1, 0] * xx + inv[1, 1] * yy + inv[1, 2]
    dx = (qx - ctx.CX) * ctx.k; dy = (qy - ctx.CY) * ctx.k
    r = np.hypot(xx - CX, yy - CY) / RS; th = np.degrees(np.arctan2(yy - CY, xx - CX))
    nF, h, w = len(names), Y1 - Y0, X1 - X0
    V = np.full((nF, h, w), np.nan, np.float32); Wt = np.zeros((nF, h, w), np.float32); D = np.zeros((nF, h, w), np.float32)
    numC = np.zeros((h, w, 3), np.float32); denC = np.zeros((h, w, 3), np.float32)
    t0 = time.time(); info = []
    for j, n in enumerate(names):
        v = pos[n]; k = kq.get(n, 1.0); m = meta[j]
        rx = (ctx.ca * dx + ctx.sa * dy + v['sol_x']).astype(np.float32); ry = (-ctx.sa * dx + ctx.ca * dy + v['sol_y']).astype(np.float32)
        mlx = v['sol_x'] + float(v['lluna_dx']); mly = v['sol_y'] + float(v['lluna_dy'])
        D[j] = np.hypot(rx - mlx, ry - mly) - ctx.RL
        fl = f2.mascara_lluna(ctx, v, rx, ry)
        plans = ctx.plans(n, v['exp']); ng = 0; dg = 0
        for i, (pl, wgt) in plans.items():
            c = comu.IDX_CANAL[i]; oy, ox = ctx.orig[i]
            if fcorr is not None:
                pl = pl * fcorr[i]
            mx = ((rx - ox) * .5).astype(np.float32); my = ((ry - oy) * .5).astype(np.float32)
            dd = cv2.remap(wgt, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
            nn = cv2.remap(pl * wgt * k, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
            b = float(m['offset_RGB'][c])
            if b != 0.0:
                nn += b * dd
            phi = upsample(phis[{0: 'R', 1: 'G', 2: 'B'}[c]][j])[Y0:Y1, X0:X1]; nn *= np.exp(-phi)
            numC[..., c] += nn * fl; denC[..., c] += dd * fl
            if c == 1:
                ng = ng + nn; dg = dg + dd
        Wt[j] = dg; V[j] = np.where(dg > 0, ng / np.maximum(dg, 1e-20), np.nan)
        info.append({'name': n, 't': m['t'], 'exp': v['exp'], 'k': k, 'font_lluna': v.get('font', '?'), 'lluna_dx': v['lluna_dx'], 'lluna_dy': v['lluna_dy']})
        if j % 10 == 0 or j == nF - 1:
            log(f'fotograma {j+1}/{nF} ({time.time()-t0:.0f}s)')
        del plans, rx, ry, fl
    # (a) reproducció de vixen_total_v36 (G sRGB via lluminancia)
    cam = np.where(denC > 0, numC / np.maximum(denC, 1e-20), np.nan)
    _, total = comu.lluminancia(cam, run.matriu, run.color['guany']); total = total.astype(np.float32)
    ref = np.asarray(np.load(CAU36 / 'vixen_total_v36.npy', mmap_mode='r')[Y0:Y1, X0:X1])
    good = np.all(np.isfinite(total) & (total > 0), axis=2) & np.all(np.isfinite(ref) & (ref > 0), axis=2)
    rel = np.abs(total[good] - ref[good]) / np.maximum(ref[good], 1e-9); rep = {'reproduccio_vixen_total_v36': {'px': int(good.sum()), 'rel_max': float(rel.max()), 'rel_p999': float(np.percentile(rel, 99.9)), 'px_suport_nomes_un': int((good != (np.all(denC > 0, axis=2) | np.all(ref > 0, axis=2))).sum())}}
    log(f"reproducció de vixen_total_v36 al ROI: rel màx {rel.max():.2e} · p99,9 {np.percentile(rel, 99.9):.2e} sobre {good.sum()} px")
    np.savez(CAU38 / 'franja_perfotograma.npz', V=V, Wt=Wt, D=D, box=np.array([Y0, Y1, X0, X1]), t=np.array([i['t'] for i in info]), exp=np.array([i['exp'] for i in info]))
    (REB38 / 'A1_fotogrames.json').write_text(json.dumps(info, indent=1))
    # (b) compost NET (contribucions a > DCLEAN de la vora del seu fotograma) i perfil de biaix per distància
    far = (D > DCLEAN) & (Wt > 0) & np.isfinite(V)
    clean = np.where(far.any(0), np.nansum(np.where(far, V * Wt, 0), 0) / np.maximum(np.where(far, Wt, 0).sum(0), 1e-20), np.nan).astype(np.float32)
    okp = np.isfinite(clean) & (clean > 0)
    bins = np.arange(-6, 40.5, 1.0); prof = {}
    classes = {'curts (≤1/800)': lambda e: e <= 1 / 800, 'mitjans (1/800–1/50)': lambda e: 1 / 800 < e <= 1 / 50, 'llargs (>1/50)': lambda e: e > 1 / 50}
    exps = np.array([i['exp'] for i in info])
    for cname, cf in classes.items():
        sel = [j for j in range(nF) if cf(exps[j])]
        if not sel: continue
        rows = []
        for b0 in bins:
            vals = []
            for j in sel:
                s = okp & (Wt[j] > 0) & np.isfinite(V[j]) & (D[j] >= b0) & (D[j] < b0 + 1) & (V[j] > 0)
                if s.any(): vals.append(np.log(V[j][s] / clean[s]))
            if vals:
                a = np.concatenate(vals); rows.append({'d': float(b0 + 0.5), 'n': int(a.size), 'mediana_ln': float(np.median(a)), 'p16': float(np.percentile(a, 16)), 'p84': float(np.percentile(a, 84))})
        prof[cname] = {'n_fotogrames': len(sel), 'perfil': rows}
        log(cname + ': ' + ' '.join(f"{rw['d']:.1f}:{rw['mediana_ln']:+.3f}" for rw in rows if rw['d'] < 16))
    rep['perfil_biaix_vs_distancia_vora'] = prof
    # (c) posició real del limbe per fotograma (sector W i global): radi on ln(V_j/clean) creua −0,5 (mitjana per anells d'1 px al voltant de la vora modelada)
    edges = []
    for j in range(nF):
        row = {'name': names[j], 't': info[j]['t'], 'exp': exps[j], 'font': info[j]['font_lluna']}
        for sname, (a0, a1) in (('W', SECTORS['W']), ('tot', (-180, 180))):
            sm = sector_mask(th, a0, a1) if sname == 'W' else np.ones_like(th, bool)
            ds = np.arange(-8, 12.0, 0.5); pr = []
            for d0 in ds:
                s = sm & okp & np.isfinite(V[j]) & (V[j] > 0) & (D[j] >= d0) & (D[j] < d0 + 0.5) & (Wt[j] > 0)
                pr.append(float(np.median(np.log(V[j][s] / clean[s]))) if s.sum() > 30 else np.nan)
            pr = np.array(pr); cross = None
            for a, b in zip(range(len(ds) - 1), range(1, len(ds))):
                if np.isfinite(pr[a]) and np.isfinite(pr[b]) and pr[a] < -0.5 <= pr[b]:
                    cross = float(ds[a] + 0.5 * (-0.5 - pr[a]) / (pr[b] - pr[a]) + 0.25); break
            row[f'vora_mesurada_{sname}_px'] = cross; row[f'perfil_{sname}'] = [None if not np.isfinite(x) else round(float(x), 3) for x in pr]
        edges.append(row)
    rep['limbe_per_fotograma'] = {'ds_px': list(np.arange(-8, 12.0, 0.5)), 'fotogrames': edges}
    cw = [e['vora_mesurada_W_px'] for e in edges if e['vora_mesurada_W_px'] is not None]; log(f"vora mesurada (W, creuament −0,5 ln) respecte de la modelada: n {len(cw)} · mediana {np.median(cw):+.2f} px · rang {min(cw):+.2f}…{max(cw):+.2f}")
    # (d) compost amb màscares alternatives i mètriques de la franja
    def compose(fl_all):
        num = np.nansum(np.where(np.isfinite(V), V * Wt * fl_all, 0), 0); den = (Wt * fl_all).sum(0)
        return np.where(den > 0, num / np.maximum(den, 1e-20), np.nan).astype(np.float32), den
    def metrics(comp, den, tag):
        ln_ = np.where(np.isfinite(comp) & (comp > 0), np.log(np.maximum(comp, 1e-12)), np.nan); ok_ = np.isfinite(ln_)
        hp = np.where(ok_, ln_ - gaussian_filter(np.nan_to_num(ln_) * ok_, 6) / np.maximum(gaussian_filter(ok_.astype(np.float32), 6), 1e-6), np.nan)
        out = {}
        for sname, (a0, a1) in SECTORS.items():
            sm = sector_mask(th, a0, a1); strip = sm & ok_ & (r > 1.003) & (r < 1.045); outer = sm & ok_ & (r > 1.06) & (r < 1.10)
            # arcs: perfil radial (mediana azimutal al sector) passa-alt a 1 px
            rb = np.round(r * RS).astype(int); prof_r = []
            for rr in range(int(1.003 * RS), int(1.10 * RS)):
                s = sm & ok_ & (rb == rr); prof_r.append(np.nanmedian(ln_[s]) if s.sum() > 20 else np.nan)
            prof_r = np.array(prof_r); pr_hp = prof_r - np.convolve(np.nan_to_num(prof_r), np.ones(5) / 5, 'same')
            n_in = int((rb[strip] < 1.045 * RS).sum())
            out[sname] = {'gra_franja_pct': float(100 * np.nanstd(hp[strip])) if strip.any() else None, 'gra_fora_pct': float(100 * np.nanstd(hp[outer])) if outer.any() else None,
                          'arcs_franja_rms_pct': float(100 * np.nanstd(pr_hp[:int(0.042 * RS)])), 'arcs_fora_rms_pct': float(100 * np.nanstd(pr_hp[int(0.057 * RS):])),
                          'px_franja_amb_dada': int(strip.sum()), 'radi_forat_R': float(np.nanmin(r[sm & ok_])) if (sm & ok_).any() else None, 'pes_mitja_franja': float(np.nanmean(den[strip])) if strip.any() else None}
        log(f"{tag}: " + ' | '.join(f"{s}: gra {o['gra_franja_pct']:.2f}% (fora {o['gra_fora_pct']:.2f}) arcs {o['arcs_franja_rms_pct']:.2f}% (fora {o['arcs_fora_rms_pct']:.2f}) px {o['px_franja_amb_dada']} forat {o['radi_forat_R']:.4f}" for s, o in out.items()))
        return out
    variants = {'vigent_G2_V2': (2.0, 2.0), 'G3_V3': (3.0, 3.0), 'G4_V4': (4.0, 4.0), 'G5_V5': (5.0, 5.0), 'G6_V6': (6.0, 6.0), 'G8_V6': (8.0, 6.0), 'G2_V12': (2.0, 12.0), 'G4_V12': (4.0, 12.0)}
    res = {}; comps = {}
    for tag, (G, Vv) in variants.items():
        fl_all = np.clip((D - G) / Vv, 0, 1).astype(np.float32); comp, den = compose(fl_all); res[tag] = {'guarda_px': G, 'vora_px': Vv, **metrics(comp, den, tag)}; comps[tag] = comp
    rep['variants_mascara'] = res
    np.savez(CAU38 / 'franja_compostos_roi.npz', **{k: v for k, v in comps.items()}, clean=clean, r=r.astype(np.float32), th=th.astype(np.float32))
    savejson(REB38 / 'A1_franja_font.json', rep)
    # vistes: perfil de biaix, vora per fotograma, retalls W vigent/net/millor
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(14, 5))
    for cname, pdat in prof.items():
        dd_ = [rw['d'] for rw in pdat['perfil']]; ax[0].plot(dd_, [rw['mediana_ln'] for rw in pdat['perfil']], '-o', ms=3, label=f"{cname} ({pdat['n_fotogrames']} fot.)"); ax[0].fill_between(dd_, [rw['p16'] for rw in pdat['perfil']], [rw['p84'] for rw in pdat['perfil']], alpha=0.15)
    ax[0].axvline(2, color='k', ls='--', lw=0.8); ax[0].axvline(4, color='k', ls=':', lw=0.8); ax[0].axhline(0, color='k', lw=0.5); ax[0].set_ylim(-1.2, 0.3); ax[0].set_xlabel('distància a la vora lunar MODELADA del fotograma (px)'); ax[0].set_ylabel('ln(fotograma / compost net)'); ax[0].legend(); ax[0].set_title('Biaix de cada fotograma prop de la seva pròpia vora lunar (V38 A1)'); ax[0].grid(alpha=0.3)
    tt = [e['t'] for e in edges]; ew = [e['vora_mesurada_W_px'] if e['vora_mesurada_W_px'] is not None else np.nan for e in edges]; et = [e['vora_mesurada_tot_px'] if e['vora_mesurada_tot_px'] is not None else np.nan for e in edges]
    ax[1].plot(tt, ew, 'o', label='sector W'); ax[1].plot(tt, et, 'x', label='tot el limbe'); ax[1].axhline(0, color='k', lw=0.5); ax[1].axhline(2, color='k', ls='--', lw=0.8, label='guarda vigent 2 px'); ax[1].set_xlabel('t (s)'); ax[1].set_ylabel('vora real (creuament −0,5 ln) − vora modelada (px)'); ax[1].legend(); ax[1].grid(alpha=0.3); ax[1].set_title('Posició real del limbe fosc per fotograma')
    fig.tight_layout(); fig.savefig(VIS38 / 'A1_biaix_vora_lunar_per_fotograma.png', dpi=110); plt.close(fig)
    # retalls W (×3): vigent, net, i la variant amb menys gra a W sense perdre més de 3 px de forat
    cand = sorted(((res[k]['W']['gra_franja_pct'], k) for k in res if res[k]['W']['radi_forat_R'] is not None and res[k]['W']['radi_forat_R'] <= res['vigent_G2_V2']['W']['radi_forat_R'] + 3 / RS))
    best = cand[0][1]; rep['millor_variant_W_sense_perdre_mes_de_3px'] = best; savejson(REB38 / 'A1_franja_font.json', rep)
    from PIL import Image, ImageDraw, ImageFont
    cxw, cyw = CX - 1.03 * RS - X0, CY - Y0; hz = 150; font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 14)
    sheet = Image.new('L', (3 * (2 * hz * 3 + 10), 2 * hz * 3 + 30), 30); d = ImageDraw.Draw(sheet)
    for jx, (lab, arr) in enumerate((('vigent (guarda 2, vora 2)', comps['vigent_G2_V2']), ('NET (només > 15 px de tota vora)', clean), (f'{best}', comps[best]))):
        a = arr[int(cyw - hz):int(cyw + hz), int(cxw - hz):int(cxw + hz)]; la = np.log(np.maximum(np.nan_to_num(a), 1e-12)); ok2 = np.isfinite(a) & (a > 0)
        hp = la - gaussian_filter(la * ok2, 6) / np.maximum(gaussian_filter(ok2.astype(np.float32), 6), 1e-6); u8 = np.uint8(np.clip(0.5 + hp / 0.3, 0, 1) * 255); u8[~ok2] = 0
        sheet.paste(Image.fromarray(u8).resize((6 * hz, 6 * hz), Image.NEAREST), (jx * (6 * hz + 10), 26)); d.text((jx * (6 * hz + 10) + 4, 6), f'{lab} · passa-alt σ6 ±0,3 ln · limbe W ×3', fill=255, font=font)
    sheet.save(VIS38 / 'A1_franja_W_vigent_net_millor.png'); log('A1 fet')


if __name__ == '__main__':
    main()
