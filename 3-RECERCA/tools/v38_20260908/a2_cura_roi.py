"""A2 (V38) · La cura de la vora lunar provada al ROI (a partir del cau d'A1): correcció mesurada del dèficit de cada fotograma
prop de la seva pròpia vora lunar (taula B_classe(d) = mediana de ln(fotograma/compost net) per classe d'exposició i distància),
aplicada com a calibratge del valor (pl · exp(−B(d))) abans de compondre; guardes 2/3/4 px. Mètriques: perfil residual per classe,
arcs (perfil radial passa-alt a 1 px, robust als NaN), gra a les franges SE/E/W, píxels amb dada, radi del forat i CONTROL NUL
(píxels a > 30 px de tota vora: han de sortir idèntics). Escriu la taula per a B2 (cau/correccio_vora_lunar.json)."""
from comu38 import *
from scipy.ndimage import gaussian_filter, median_filter

SECTORS = {'W': (150, 210), 'SE': (20, 60), 'E': (-15, 15), 'N_control': (-105, -75)}
CLASSES = [('curts', lambda e: e <= 1 / 800), ('mitjans', lambda e: 1 / 800 < e <= 1 / 50), ('llargs', lambda e: e > 1 / 50)]
DMAX = 30.0; DBLEND = (24.0, 30.0)


def sector_mask(th, a0, a1):
    ang = ((th - 0.5 * (a0 + a1) + 180) % 360) - 180
    return np.abs(ang) <= 0.5 * (a1 - a0)


def perfil(V, Wt, D, clean, okp, sel, dbins, extra=None):
    rows = []
    for b0 in dbins:
        vals = []
        for j in sel:
            s = okp & (Wt[j] > 0) & np.isfinite(V[j]) & (V[j] > 0) & (D[j] >= b0) & (D[j] < b0 + 0.5)
            if extra is not None: s &= extra
            if s.any(): vals.append(np.log(V[j][s] / clean[s]))
        if vals:
            a = np.concatenate(vals); rows.append((b0 + 0.25, a.size, float(np.median(a)), float(np.percentile(a, 16)), float(np.percentile(a, 84))))
        else:
            rows.append((b0 + 0.25, 0, np.nan, np.nan, np.nan))
    return rows


def main():
    z = np.load(CAU38 / 'franja_perfotograma.npz'); V, Wt, D, exps = z['V'], z['Wt'], z['D'], z['exp']; Y0, Y1, X0, X1 = [int(x) for x in z['box']]
    c = np.load(CAU38 / 'franja_compostos_roi.npz'); clean, r, th = c['clean'], c['r'], c['th']; okp = np.isfinite(clean) & (clean > 0); nF = V.shape[0]
    dbins = np.arange(-2.0, DMAX + 0.5, 0.5)
    # 1) taula de correcció per classe (i estabilitat per sector)
    taula = {}; rep = {'classes': {}, 'estabilitat_per_sector': {}}
    for cname, cf in CLASSES:
        sel = [j for j in range(nF) if cf(exps[j])]
        rows = perfil(V, Wt, D, clean, okp, sel, dbins); med = np.array([rw[2] for rw in rows]); dd = np.array([rw[0] for rw in rows])
        # suavitzat robust (mediana de 3 caixes) i mescla a 0 entre DBLEND
        ms = median_filter(np.nan_to_num(med, nan=0.0), size=3, mode='nearest'); wblend = np.clip((DBLEND[1] - dd) / (DBLEND[1] - DBLEND[0]), 0, 1); ms = ms * wblend
        taula[cname] = {'d_px': [float(x) for x in dd], 'B_ln': [float(x) for x in ms], 'n_fotogrames': len(sel)}
        rep['classes'][cname] = {'n_fotogrames': len(sel), 'perfil': [{'d': rw[0], 'n': rw[1], 'mediana_ln': rw[2], 'p16': rw[3], 'p84': rw[4]} for rw in rows]}
        est = {}
        for sname, (a0, a1) in SECTORS.items():
            rs = perfil(V, Wt, D, clean, okp, sel, np.array([2.0, 4.0, 6.0, 10.0, 15.0]), extra=sector_mask(th, a0, a1)); est[sname] = {f'd{rw[0]-0.25:.0f}': (None if not np.isfinite(rw[2]) else round(rw[2], 4)) for rw in rs}
        rep['estabilitat_per_sector'][cname] = est; log(f"{cname}: estabilitat per sector a d=2/4/6/10/15 px: {est}")
    (CAU38 / 'correccio_vora_lunar.json').write_text(json.dumps({'origen': 'A2 V38: mediana de ln(fotograma/compost net) per classe d\'exposició i distància a la vora lunar modelada del fotograma; suavitzat mediana 3; mescla lineal a 0 entre 24 i 30 px', 'classes': {'curts': '≤1/800', 'mitjans': '1/800–1/50', 'llargs': '>1/50'}, 'taula': taula}, indent=1))
    def Bof(cname, d):
        tb = taula[cname]; return np.interp(d, tb['d_px'], tb['B_ln'], left=tb['B_ln'][0], right=0.0)
    cls_of = [next(cn for cn, cf in CLASSES if cf(e)) for e in exps]
    # 2) variants
    def compose(G, Vv, corr):
        num = np.zeros(V.shape[1:], np.float32); den = np.zeros(V.shape[1:], np.float32); Vc = np.empty_like(V)
        for j in range(nF):
            fl = np.clip((D[j] - G) / Vv, 0, 1); vj = np.nan_to_num(V[j])
            if corr: vj = vj * np.exp(-Bof(cls_of[j], D[j])).astype(np.float32)
            Vc[j] = np.where(np.isfinite(V[j]), vj, np.nan); num += vj * Wt[j] * fl; den += Wt[j] * fl
        return np.where(den > 0, num / np.maximum(den, 1e-20), np.nan).astype(np.float32), den, Vc
    def arcs(ln_, ok_, sm):
        rb = np.round(r * RS).astype(int); rr = np.arange(int(1.003 * RS), int(1.12 * RS)); prof_r = np.array([np.nanmedian(ln_[sm & ok_ & (rb == k)]) if (sm & ok_ & (rb == k)).sum() > 20 else np.nan for k in rr])
        # passa-alt robust: mediana mòbil de 9 (nan-aware)
        base = np.array([np.nanmedian(prof_r[max(0, i - 4):i + 5]) if np.isfinite(prof_r[max(0, i - 4):i + 5]).sum() >= 3 else np.nan for i in range(len(prof_r))]); hp = prof_r - base
        s_in = rr < 1.045 * RS; s_out = rr > 1.06 * RS
        return float(100 * np.nanstd(hp[s_in])), float(100 * np.nanstd(hp[s_out])), prof_r, rr
    def metrics(comp, den, tag, Vc):
        ln_ = np.where(np.isfinite(comp) & (comp > 0), np.log(np.maximum(comp, 1e-12)), np.nan); ok_ = np.isfinite(ln_)
        hp = np.where(ok_, ln_ - gaussian_filter(np.nan_to_num(ln_) * ok_, 6) / np.maximum(gaussian_filter(ok_.astype(np.float32), 6), 1e-6), np.nan); out = {}
        for sname, (a0, a1) in SECTORS.items():
            sm = sector_mask(th, a0, a1); strip = sm & ok_ & (r > 1.003) & (r < 1.045); outer = sm & ok_ & (r > 1.06) & (r < 1.10); a_in, a_out, _, _ = arcs(ln_, ok_, sm)
            out[sname] = {'gra_franja_pct': float(100 * np.nanstd(hp[strip])) if strip.any() else None, 'gra_fora_pct': float(100 * np.nanstd(hp[outer])) if outer.any() else None, 'arcs_franja_pct': a_in, 'arcs_fora_pct': a_out, 'px_franja': int(strip.sum()), 'radi_forat_R': float(np.nanmin(r[sm & ok_])) if (sm & ok_).any() else None}
        # perfil residual per classe després de la correcció (contra el mateix compost net)
        resid = {}
        for cname, cf in CLASSES:
            sel = [j for j in range(nF) if cf(exps[j])]; rows = perfil(Vc, Wt, D, clean, okp, sel, np.array([2.0, 3.0, 4.0, 6.0, 8.0, 10.0, 15.0, 20.0])); resid[cname] = {f'd{rw[0]-0.25:.0f}': (None if not np.isfinite(rw[2]) else round(rw[2], 4)) for rw in rows}
        out['residu_per_classe'] = resid
        log(f"{tag}: " + ' | '.join(f"{s}: gra {o['gra_franja_pct']:.2f}% (fora {o['gra_fora_pct']:.2f}) arcs {o['arcs_franja_pct']:.2f}% (fora {o['arcs_fora_pct']:.2f}) px {o['px_franja']} forat {o['radi_forat_R']:.4f}" for s, o in out.items() if s != 'residu_per_classe') + f" · residu curts {resid['curts']}")
        return out
    variants = {'vigent_G2_V2_senseCorr': (2.0, 2.0, False), 'G2_V2_corr': (2.0, 2.0, True), 'G3_V3_corr': (3.0, 3.0, True), 'G4_V4_corr': (4.0, 4.0, True), 'G3_V3_senseCorr': (3.0, 3.0, False)}
    res = {}; comps = {}
    for tag, (G, Vv, corr) in variants.items():
        comp, den, Vc = compose(G, Vv, corr); res[tag] = {'guarda_px': G, 'vora_px': Vv, 'correccio': corr, **metrics(comp, den, tag, Vc)}; comps[tag] = comp
    # 3) control nul: píxels a > 30 px de la vora de TOTS els fotogrames que hi contribueixen → idèntics a la vigent
    dmin = np.where(Wt > 0, D, np.inf).min(0); nul = np.isfinite(comps['vigent_G2_V2_senseCorr']) & (dmin > DMAX)
    for tag in variants:
        if tag == 'vigent_G2_V2_senseCorr': continue
        dif = np.abs(comps[tag][nul] / comps['vigent_G2_V2_senseCorr'][nul] - 1); res[tag]['control_nul'] = {'px': int(nul.sum()), 'rel_max': float(np.nanmax(dif)), 'rel_p99': float(np.nanpercentile(dif, 99))}
        log(f"{tag}: control nul (d_min > 30 px, {nul.sum()} px): rel màx {np.nanmax(dif):.2e}")
    rep['variants'] = res; savejson(REB38 / 'A2_cura_roi.json', rep)
    np.savez(CAU38 / 'franja_cura_roi.npz', **comps)
    # vistes: perfils abans/després i retall W
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(14, 5))
    for cname in taula:
        pr = rep['classes'][cname]['perfil']; ax[0].plot([p['d'] for p in pr], [p['mediana_ln'] for p in pr], '-', label=f'{cname} mesurat'); ax[0].plot(taula[cname]['d_px'], taula[cname]['B_ln'], '--', label=f'{cname} taula B(d)')
    ax[0].set_ylim(-0.4, 0.1); ax[0].axhline(0, color='k', lw=0.5); ax[0].axvline(2, color='k', ls='--', lw=0.8); ax[0].set_xlabel('d a la vora lunar del fotograma (px)'); ax[0].set_ylabel('ln(fotograma / compost net)'); ax[0].legend(fontsize=8); ax[0].grid(alpha=0.3); ax[0].set_title('Dèficit prop del limbe fosc per classe d\'exposició i la taula de correcció')
    ln_v = np.log(np.maximum(np.nan_to_num(comps['vigent_G2_V2_senseCorr']), 1e-12)); ok_v = np.isfinite(comps['vigent_G2_V2_senseCorr']); smW = sector_mask(th, *SECTORS['W']); smSE = sector_mask(th, *SECTORS['SE'])
    for tag, col in (('vigent_G2_V2_senseCorr', 'k'), ('G2_V2_corr', 'C0'), ('G3_V3_corr', 'C1')):
        ln_ = np.log(np.maximum(np.nan_to_num(comps[tag]), 1e-12)); ok_ = np.isfinite(comps[tag]); _, _, pr, rr = arcs(ln_, ok_, smSE); ax[1].plot(rr / RS, pr - np.nanmedian(pr), color=col, lw=1, label=f'{tag} (SE)')
    ax[1].set_xlabel('r (R☉)'); ax[1].set_ylabel('perfil radial ln (mediana azimutal, sector SE) − mediana'); ax[1].legend(fontsize=8); ax[1].grid(alpha=0.3); ax[1].set_xlim(1.0, 1.12); ax[1].set_title('Arcs de la franja: perfil radial abans/després')
    fig.tight_layout(); fig.savefig(VIS38 / 'A2_cura_vora_lunar_perfils.png', dpi=110); plt.close(fig)
    from PIL import Image, ImageDraw, ImageFont
    font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 14)
    for sname, azc in (('W', 180.0), ('SE', 40.0)):
        cxw, cyw = CX + 1.03 * RS * np.cos(np.radians(azc)) - X0, CY + 1.03 * RS * np.sin(np.radians(azc)) - Y0; hz = 150
        sheet = Image.new('L', (3 * (6 * hz + 10), 6 * hz + 30), 30); d = ImageDraw.Draw(sheet)
        for jx, tag in enumerate(('vigent_G2_V2_senseCorr', 'G2_V2_corr', 'G3_V3_corr')):
            a = comps[tag][int(cyw - hz):int(cyw + hz), int(cxw - hz):int(cxw + hz)]; ok2 = np.isfinite(a) & (a > 0); la = np.log(np.maximum(np.nan_to_num(a), 1e-12))
            hp = la - gaussian_filter(la * ok2, 6) / np.maximum(gaussian_filter(ok2.astype(np.float32), 6), 1e-6); u8 = np.uint8(np.clip(0.5 + hp / 0.3, 0, 1) * 255); u8[~ok2] = 0
            sheet.paste(Image.fromarray(u8).resize((6 * hz, 6 * hz), Image.NEAREST), (jx * (6 * hz + 10), 26)); d.text((jx * (6 * hz + 10) + 4, 6), f'{tag} · passa-alt σ6 ±0,3 ln · limbe {sname} ×3', fill=255, font=font)
        sheet.save(VIS38 / f'A2_franja_{sname}_vigent_corr.png')
    log('A2 fet')


if __name__ == '__main__':
    main()
