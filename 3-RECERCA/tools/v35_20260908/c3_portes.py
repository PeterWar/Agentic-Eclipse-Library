"""C3 (V35) · Portes i vistes de la V35 contra la V34, mateixa vara:
  · gra per radi de la base (V32/V34/V35) i de cada capa (fi 1,5/3 i mitjà 6/12) V34 vs V35; pendent màxim del gra al relleu 1,8–3,5;
  · VORA VIXEN: perfil de la mitjana local de cada capa contra la distància amb signe a la vora del suport Vixen (r > 4) i graó
    (dins − fora, ±50–250 px) en unitats del rms de la capa; a la base, en % de nivell i de gra;
  · VORA A: graó de gra de la base a la vora del suport de l'apuntament A;
  · LIMBE: biaix d'anell (mediana per anell / σ, 1,0–1,3 respecte de 1,3+) de cada capa;
  · anisotropia tangencial de NRGF/RHEF a la vora del llenç; pes Vixen a 1,0–1,5 (trampa del forat);
  · vistes polars V34 | V35 per capa i retalls 1:1 a les marques de Pere de la V34 (V34 | V35)."""
from comu35 import *
from scipy.ndimage import gaussian_filter
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, str(ROOT / 'research/tools/revisio_marques_v32_20260907'))
from a4_color_i_rho import ring_profile
PC34 = HERE34 / 'purs/cau'; PC35 = HERE35 / 'purs/cau'; WIN34 = ROOT / 'research/tools/revisio_marques_v34_20260908/windows'
CAU32 = ROOT / 'research/tools/v32_arcs_20260907/cau'
LAYERS = {'01': (CAU34 / '01_v34_u16.npy', CAU35 / '01_v35_u16.npy'), '02': (CAU34 / '02_v34_u16.npy', CAU35 / '02_v35_u16.npy'), '04': (CAU34 / '04_v34_u16.npy', CAU35 / '04_v35_u16.npy'),
          '05': (CAU34 / '05_v34_u16.npy', CAU35 / '05_v35_u16.npy'), '06': (CAU34 / '06_v34_u16.npy', CAU35 / '06_v35_u16.npy'),
          'P01': (PC34 / 'P01_NRGF_u16.npy', PC35 / 'P01_NRGF_u16.npy'), 'P02': (PC34 / 'P02_RHEF_u16.npy', PC35 / 'P02_RHEF_u16.npy'), 'P03': (PC34 / 'P03_MGN_u16.npy', PC35 / 'P03_MGN_u16.npy'),
          'P04': (PC34 / 'P04_WOW_u16.npy', PC35 / 'P04_WOW_u16.npy'), 'P05': (PC34 / 'P05_WOW_bilateral_u16.npy', PC35 / 'P05_WOW_bilateral_u16.npy')}
LAYER_OF = {'L01': '01', 'L02': '02', 'L03': '04', 'L04': '05', 'L05': '06', 'L06': 'P01', 'L07': 'P02', 'L08': 'P03', 'L09': 'P04', 'L10': 'P05'}
MARKS = ['L01-M03', 'L01-M07', 'L03-M06', 'L08-M02', 'L08-M03', 'L09-M02', 'L09-M05', 'L10-M02', 'L10-M07', 'L10-M08', 'L10-M12', 'L10-M17']
FONT = '/System/Library/Fonts/Supplemental/Arial.ttf'; NT = 2400


def font(n):
    return ImageFont.truetype(FONT, n)


def ng(a, w, s):
    return gaussian_filter(a * w, s) / np.maximum(gaussian_filter(w, s), 1e-6)


def grain(u, m, r):
    v = np.asarray(u, np.float32) / 65535; w = m.astype(np.float32)
    fine = np.where(m, ng(v, w, 1.5) - ng(v, w, 3), 0); mid = np.where(m, ng(v, w, 6) - ng(v, w, 12), 0)
    rr, pf, _ = ring_profile(fine ** 2, m, r, 1.05, 12.0, step=0.05 * RS); _, pm, _ = ring_profile(mid ** 2, m, r, 1.05, 12.0, step=0.05 * RS)
    return rr, np.sqrt(pf), np.sqrt(pm), mid


def tangential(u, m, r, t, sig, a, b):
    v = np.asarray(u, np.float32) / 65535; w = m.astype(np.float32)
    band = np.where(m, ng(v, w, sig) - ng(v, w, 2 * sig), 0); gy, gx = np.gradient(band); s2 = 1.5 * sig
    Jxx = gaussian_filter(gx * gx, s2); Jyy = gaussian_filter(gy * gy, s2); Jxy = gaussian_filter(gx * gy, s2)
    proj = (Jxx - Jyy) * np.cos(2 * t) + 2 * Jxy * np.sin(2 * t); E = Jxx + Jyy; k = m & (r >= a * RS) & (r < b * RS)
    return float(np.sum(proj[k]) / max(np.sum(E[k]), 1e-20))


def edge_profile(v, w, sd, zone, bins, sig=24):
    lo = ng(v, w, sig); rows = []
    for b0 in bins:
        k = zone & (sd >= b0) & (sd < b0 + 50)
        rows.append(float(np.median(lo[k])) if k.sum() > 300 else None)
    return rows


def ring_bias(v, m, r):
    sd = float(np.nanstd(v[m & (r > 1.05 * RS) & (r < 1.6 * RS)])); rs = np.arange(0.98, 1.6, 0.01); med = []  # el biaix es mesura d'1,03 a 1,3 (1,00–1,03 és el limbe físic: cromosfera i protuberàncies)
    for a0 in rs:
        k = m & (r >= a0 * RS) & (r < (a0 + 0.01) * RS); med.append(float(np.median(v[k])) / max(sd, 1e-12) if k.sum() > 50 else np.nan)
    z = np.array(med); zz = z - np.nanmedian(z[rs > 1.3]); return float(np.nanmax(np.abs(zz[(rs >= 1.03) & (rs < 1.3)])))


def polar_u8(u, m, r0, r1, sigma):
    v = np.asarray(u, np.float32) / 65535; w = m.astype(np.float32); hp = np.where(m, v - ng(v, w, sigma), np.nan)
    rv = np.arange(r0 * RS, r1 * RS, 1.0, dtype=np.float32); th = np.linspace(-np.pi, np.pi, NT, endpoint=False, dtype=np.float32)
    X = (CX + rv[:, None] * np.cos(th)[None, :]).astype(np.float32); Y = (CY + rv[:, None] * np.sin(th)[None, :]).astype(np.float32)
    pol = cv2.remap(np.nan_to_num(hp), X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT); pm = cv2.remap(np.isfinite(hp).astype(np.float32), X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) > 0.99
    z = pol[pm]; sc = float(np.percentile(np.abs(z), 98)) if z.size else 1
    u8 = np.uint8(np.clip(0.5 + pol / (2 * sc), 0, 1) * 255); u8[~pm] = 40
    return u8, sc


def main():
    r, t = coords(); m = np.load(CAU35 / 'support_v35.npy'); mv0 = np.load(CAUF / 'vixen_support.npy'); w = m.astype(np.float32)
    mvf = mv0 | (r < 1.6 * RS); sdv = np.where(mvf, cv2.distanceTransform(mvf.astype(np.uint8), cv2.DIST_L2, 5), -cv2.distanceTransform((~mvf).astype(np.uint8), cv2.DIST_L2, 5)).astype(np.float32)
    pa = np.load(CAUF / 'sony_A_weights.npy', mmap_mode='r'); A = np.load(CAU34 / 'sony_A_total_v34.npy', mmap_mode='r'); ma = np.all(np.isfinite(A) & (A > 0) & (pa > 0), axis=2) | (r < 1.2 * RS); del A
    sda = np.where(ma, cv2.distanceTransform(ma.astype(np.uint8), cv2.DIST_L2, 5), -cv2.distanceTransform((~ma).astype(np.uint8), cv2.DIST_L2, 5)).astype(np.float32)
    y, x = np.ogrid[:H, :W]; dist = np.hypot(x - GHOST_XY[0], y - GHOST_XY[1])
    zoneV = m & (r > 4 * RS); zoneA = m & (r > 2.5 * RS) & (dist > 320) & (np.abs(sdv) > 300)
    binsV = list(range(-500, 900, 50)); binsA = list(range(-400, 700, 50))
    rep = {'gra': {}, 'vora_vixen': {'bins_px': binsV, 'capes': {}}, 'vora_A': {'bins_px': binsA, 'capes': {}}, 'limbe_biaix_anell_sigma': {}, 'tangencial_vora_llenc': {}, 'retalls': [], 'relleu': {}}
    # base: gra per radi (V32/V34/V35) i vores en nivell i gra
    for nm, pth in (('base_V32', CAU32 / 'base_G_v32.npy'), ('base_V34', CAU34 / 'base_G_v34.npy'), ('base_V35', CAU35 / 'base_G_v35.npy')):
        G = np.asarray(np.load(pth, mmap_mode='r')); mm = m & np.isfinite(G) & (G > 0); L = np.where(mm, np.log(np.maximum(G, 1e-9)), 0).astype(np.float32); ww = mm.astype(np.float32)
        fine = np.where(mm, ng(L, ww, 1.5) - ng(L, ww, 3), 0); rr, pf, _ = ring_profile(fine ** 2, mm, r, 1.05, 9.0, step=0.02 * RS)
        rep['gra'][nm] = {'r': rr.tolist(), 'fi_pct': (100 * np.sqrt(pf)).tolist()}
        lf = np.sqrt(np.maximum(ng(fine * fine, ww, 24), 0))
        if nm != 'base_V32':
            rep['vora_vixen']['capes'][nm] = {'nivell_pct': [None if v is None else 100 * v for v in edge_profile(L, ww, sdv, zoneV & mm, binsV, 64)], 'gra_fi_pct': [None if v is None else 100 * v for v in edge_profile(lf, ww, sdv, zoneV & mm, binsV, 1)]}
            rep['vora_A']['capes'][nm] = {'gra_fi_pct': [None if v is None else 100 * v for v in edge_profile(lf, ww, sda, zoneA & mm, binsA, 1)]}
            rr2, pf2, _ = ring_profile(fine ** 2, mm, r, 1.8, 3.5, step=0.05 * RS); s = np.log(np.sqrt(pf2)); rep['relleu'][nm] = {'r': rr2.tolist(), 'fi_pct': (100 * np.sqrt(pf2)).tolist(), 'max_dlnsigma_per_0.1R': float(np.max(np.abs(np.diff(s))) * 2)}
        del G, L, fine, lf
    log('base fet')
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig, axs = plt.subplots(5, 2, figsize=(12, 15), sharex=True); axs = axs.ravel()
    for i, (k, (p34, p35)) in enumerate(LAYERS.items()):
        u34 = np.load(p34, mmap_mode='r'); u35 = np.load(p35, mmap_mode='r')
        rr, f34, m34, mid34 = grain(u34, m, r); _, f35, m35, mid35 = grain(u35, m, r)
        rep['gra'][k] = {'r': rr.tolist(), 'fi_v34': f34.tolist(), 'fi_v35': f35.tolist(), 'mig_v34': m34.tolist(), 'mig_v35': m35.tolist()}
        ax = axs[i]; ax.semilogy(rr, f34, 'r', lw=.8, label='fi V34'); ax.semilogy(rr, f35, 'r--', lw=.8, label='fi V35'); ax.semilogy(rr, m34, 'b', lw=.8, label='mig V34'); ax.semilogy(rr, m35, 'b--', lw=.8, label='mig V35'); ax.set_title(k, fontsize=9); ax.legend(fontsize=7)
        row = {}
        for lab, u, mid in (('V34', u34, mid34), ('V35', u35, mid35)):
            v = np.asarray(u, np.float32) / 65535; rms = float(np.sqrt(np.mean(mid[zoneV] ** 2))); pr = edge_profile(v, w, sdv, zoneV, binsV, 24)
            ins = [p for b, p in zip(binsV, pr) if p is not None and 50 <= b < 250]; outs = [p for b, p in zip(binsV, pr) if p is not None and -250 <= b < -50]
            row[lab] = {'perfil': pr, 'rms_mig_zona': rms, 'grao_sobre_rms': (float(np.mean(ins) - np.mean(outs)) / max(rms, 1e-9)) if ins and outs else None}
            prA = edge_profile(v, w, sda, zoneA, binsA, 24); insA = [p for b, p in zip(binsA, prA) if p is not None and 50 <= b < 250]; outA = [p for b, p in zip(binsA, prA) if p is not None and -250 <= b < -50]
            rep['vora_A']['capes'].setdefault(k, {})[lab] = {'perfil': prA, 'grao_sobre_rms': (float(np.mean(insA) - np.mean(outA)) / max(rms, 1e-9)) if insA and outA else None}
            rep['limbe_biaix_anell_sigma'].setdefault(k, {})[lab] = ring_bias(v, m, r)
        rep['vora_vixen']['capes'][k] = row
        if k in ('P01', 'P02'):
            rep['tangencial_vora_llenc'][k] = {f'σ{s}': {'V34': tangential(u34, m, r, t, s, 8.3, 8.8), 'V35': tangential(u35, m, r, t, s, 8.3, 8.8)} for s in (16, 32)}
        log(f"{k}: gra fi 4R {np.interp(4, rr, f34):.4f}→{np.interp(4, rr, f35):.4f} · graó vora Vixen/rms {row['V34']['grao_sobre_rms']:+.2f}→{row['V35']['grao_sobre_rms']:+.2f} · vora A {rep['vora_A']['capes'][k]['V34']['grao_sobre_rms']:+.2f}→{rep['vora_A']['capes'][k]['V35']['grao_sobre_rms']:+.2f} · limbe {rep['limbe_biaix_anell_sigma'][k]['V34']:.2f}→{rep['limbe_biaix_anell_sigma'][k]['V35']:.2f} σ")
        del u34, u35, mid34, mid35
    fig.tight_layout(); fig.savefig(VIS35 / 'C3_gra_per_radi_V34_V35.png', dpi=110); plt.close(fig)
    rep['pes_vixen_interior'] = json.loads((REB35 / 'B3_fusio.json').read_text())['trains']['perfil_pesos'][:5]
    savejson(REB35 / 'C3_portes.json', rep)
    # polars V34 | V35
    for k, (p34, p35) in LAYERS.items():
        u34 = np.load(p34, mmap_mode='r'); u35 = np.load(p35, mmap_mode='r')
        for tram, (r0, r1), sg in [('interior', (1.0, 3.0), 12), ('intermedi', (3.0, 6.0), 24), ('exterior', (6.0, 10.0), 32)]:
            a34, s34 = polar_u8(u34, m, r0, r1, sg); a35, s35 = polar_u8(u35, m, r0, r1, sg)
            nr = a34.shape[0]; im = Image.new('L', (NT + 60, 2 * (nr + 24)), 30); d = ImageDraw.Draw(im)
            for j, (a, s, lab) in enumerate([(a34, s34, 'V34'), (a35, s35, 'V35')]):
                im.paste(Image.fromarray(a), (60, j * (nr + 24) + 24)); d.text((64, j * (nr + 24) + 4), f'{k} {lab} · passa-alt σ{sg} · ±{s:.4f} u · r {r0}–{r1} R☉ amunt→avall · azimut −180…180°', fill=255, font=font(13))
                for rr_ in np.arange(np.ceil(r0 * 2) / 2, r1, 0.5):
                    yy = int((rr_ - r0) * RS); d.text((2, j * (nr + 24) + 24 + yy - 6), f'{rr_:.1f}', fill=200, font=font(11))
            im.save(VIS35 / f'C3_polar_{k}_{tram}.png')
        log(f'polar {k}')
    # retalls 1:1 a marques de Pere (V34) i a la vora Vixen (4 punts) per a 01, P01, P03
    cat = {x['id']: x for x in json.loads((ROOT / 'output/revisio_marques_v34_20260908/4-rebuts/review_catalog.json').read_text())['marks']}
    jobs = []
    for mid in MARKS:
        mk = cat[mid]; k = LAYER_OF[mid[:3]]; x0, y0, x1, y1 = mk['window_bbox']
        if (x1 - x0) * (y1 - y0) > 1600 * 1600:
            cx, cy = int(mk['center_xy'][0]), int(mk['center_xy'][1]); x0, y0, x1, y1 = max(cx - 700, 0), max(cy - 700, 0), min(cx + 700, W), min(cy + 700, H)
        jobs.append((mid, k, (x0, y0, x1, y1), mk))
    edge = cv2.morphologyEx(mv0.astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0; ey, ex = np.nonzero(edge & (r > 4 * RS))
    for k in ('01', 'P01', 'P03', 'P05'):
        for lab, (tx, ty) in (('N', (CX, CY - 5.3 * RS)), ('S', (CX, CY + 5.3 * RS)), ('E', (CX + 7.6 * RS, CY)), ('W', (CX - 7.6 * RS, CY))):
            i = int(np.argmin((ex - tx) ** 2 + (ey - ty) ** 2)); cx, cy = int(ex[i]), int(ey[i]); jobs.append((f'VORA-{lab}', k, (max(cx - 600, 0), max(cy - 600, 0), min(cx + 600, W), min(cy + 600, H)), None))
    for mid, k, (x0, y0, x1, y1), mk in jobs:
        p34, p35 = LAYERS[k]; a34 = (np.load(p34, mmap_mode='r')[y0:y1, x0:x1] // 257).astype(np.uint8); a35 = (np.load(p35, mmap_mode='r')[y0:y1, x0:x1] // 257).astype(np.uint8)
        pm = np.zeros(a34.shape, bool)
        if mk is not None:
            codes = np.load(WIN34 / (mid + '_codes.npy')); wx0, wy0, wx1, wy1 = mk['window_bbox']; ya, yb, xa, xb = max(wy0, y0), min(wy1, y1), max(wx0, x0), min(wx1, x1)
            if yb > ya and xb > xa:
                pm[ya - y0:yb - y0, xa - x0:xb - x0] = codes[ya - wy0:yb - wy0, xa - wx0:xb - wx0] > 0
        else:
            pm = edge[y0:y1, x0:x1]
        ed = cv2.morphologyEx(pm.astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0 if mk is not None else pm
        panels = []
        for a, lab in ((a34, 'V34'), (a35, 'V35')):
            rgb = np.stack([a, a, a], -1); rgb[ed] = (200, 60, 255); im = Image.fromarray(rgb); im.thumbnail((1000, 1000), Image.Resampling.LANCZOS); panels.append((im, lab))
        wtot = sum(p.width for p, _ in panels) + 30; ht = max(p.height for p, _ in panels) + 30; sheet = Image.new('RGB', (wtot, ht), (24, 24, 24)); d = ImageDraw.Draw(sheet); xx = 10
        for p, lab in panels:
            sheet.paste(p, (xx, 26)); d.text((xx, 6), f'{mid} · {k} · {lab} · {x1 - x0}×{y1 - y0} px' + ('' if mk is None else f" · {mk['family'][:40]}"), fill='white', font=font(14)); xx += p.width + 10
        sheet.save(VIS35 / f'C3_retall_{mid}_{k}.png'); rep['retalls'].append({'id': mid, 'layer': k, 'box': [x0, y0, x1, y1]})
    savejson(REB35 / 'C3_portes.json', rep); log('C3 fet')


if __name__ == '__main__':
    main()
