"""A2 (V35) · El P05 (WOW bilateral) al limbe: la causa, provada en una ROI.
Hipòtesi: els operadors ISOTRÒPICS (à trous B3 del WOW, gaussianes del MGN) amb el forat lunar com a suport
absent i un gradient radial de ×2 cada 44 px fan una mitjana local D'UN SOL COSTAT (cap enfora, més fosc)
→ coeficient positiu coherent a cada escala → anells clars concèntrics d'amplada 2·2^s (WOW) o ~σ (MGN)
a 1,0–1,3 R☉. Prova d'un sol paràmetre: la mateixa ROI, el mateix codi WOW bilateral, amb (A) el suport tal
com es lliura; (B) el forat lunar OMPLERT NOMÉS PER A L'ENTRADA DEL FILTRE amb el perfil radial mitjà de
cada anell continuat cap endins (el producte no el porta mai); (C) entrada normalitzada radialment
(ln B − ⟨ln B⟩_anell; el gradient radial fora abans del filtre). Mètrica: mediana per anell del resultat
(0,98–1,6 R☉, calaixos 0,01 R☉) — un anell coherent és un biaix, no detall — i rms del residu azimutal."""
import os, sys, json
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]; PURS = ROOT / 'research/tools/v31_purs'; MINE = ROOT / 'research/tools/v34_20260907/purs'
sys.path = [str(PURS)] + [p for p in sys.path if 'research/tools' not in p]; os.environ['V29_FINAL_GRID'] = '1'
import common as vc; vc.D = MINE
import numpy as np
from wow_filters import wow
from local_filters import mgn
from common import RS, CX, CY, log, savejson
CAU34 = ROOT / 'research/tools/v34_20260907/cau'; REB35 = ROOT / 'output/v35_20260908/4-rebuts'; VIS35 = ROOT / 'output/v35_20260908/lliurables/vistes'
RAD = 2.9


def ring_median(a, m, r, r0=0.98, r1=1.6, step=0.01):
    rs = np.arange(r0, r1, step); out = []
    for a0 in rs:
        k = m & (r >= a0) & (r < a0 + step); out.append(float(np.median(a[k])) if k.sum() > 50 else np.nan)
    return rs.tolist(), out


def main():
    G = np.load(CAU34 / 'base_G_v34.npy', mmap_mode='r'); M = np.load(CAU34 / 'support_v34.npy')
    y0, y1, x0, x1 = int(CY - RAD * RS), int(CY + RAD * RS), int(CX - RAD * RS), int(CX + RAD * RS)
    a = np.array(G[y0:y1, x0:x1], np.float32); m = M[y0:y1, x0:x1].copy(); yy, xx = np.ogrid[:a.shape[0], :a.shape[1]]
    r = np.hypot(xx + x0 - CX, yy + y0 - CY) / RS; t = np.arctan2(yy + y0 - CY, xx + x0 - CX)
    m &= a > 0; log(f'ROI {a.shape}, suport {m.mean():.3f}, forat r<1: {(~m & (r < 1)).sum()} px')
    # perfil radial mitjà (ln) per anell d'1 px i continuació cap endins (pendent dels 20 primers anells sencers)
    ri = np.round(r * RS).astype(int); L = np.where(m, np.log(np.maximum(a, 1e-9)), 0)
    n = np.bincount(ri[m]); s = np.bincount(ri[m], weights=L[m]); prof = np.where(n > 0, s / np.maximum(n, 1), np.nan)
    full = np.flatnonzero(n >= 0.999 * 2 * np.pi * np.arange(len(n))); first = int(full[full > 1.0 * RS][0]); k = np.arange(first, first + 20)
    slope = np.polyfit(k, prof[k], 1)[0]; p_in = prof.copy(); p_in[:first] = prof[first] + slope * (np.arange(first) - first)
    radial = np.interp(r * RS, np.arange(len(p_in)), np.nan_to_num(p_in, nan=prof[first]))
    filled = np.where(m, a, np.exp(radial)).astype(np.float32); mfull = np.ones_like(m)
    znorm = np.where(m, L - radial, 0).astype(np.float32)
    rep = {'roi': [x0, y0, x1, y1], 'first_full_ring_px': first, 'slope_ln_per_px': float(slope), 'cases': {}}
    NS = 7
    for tag, inp, sup in (('A_suport_tal_qual', a, m), ('B_forat_omplert_perfil_radial', filled, mfull), ('C_normalitzat_radial_ln', znorm, m)):
        for name, fn in (('WOWbil', lambda x, mm: wow(x, mm, NS, True, False)), ('WOW', lambda x, mm: wow(x, mm, NS, False, False)), ('MGN', lambda x, mm: mgn(x, mm, limits=[float(x[mm].min()), float(x[mm].max())]))):
            if name == 'MGN' and tag == 'C_normalitzat_radial_ln':
                lim = [float(np.percentile(inp[m], 0.1)), float(np.percentile(inp[m], 99.9))]; out = mgn(inp, m, limits=lim)
            else:
                out = fn(inp, sup)
            out = np.where(m, out, np.nan); rs, med = ring_median(out, m, r); sd = float(np.nanstd(out[m & (r > 1.05) & (r < 1.6)]))
            anell = np.array(med); z = (anell - np.nanmedian(anell[(np.array(rs) > 1.3)])) / max(sd, 1e-9)
            rep['cases'][f'{tag}/{name}'] = {'ring_median_r': rs, 'ring_median': med, 'sd_1.05_1.6': sd, 'ring_bias_in_sd_units_max_1.0_1.3': float(np.nanmax(np.abs(z[(np.array(rs) >= 1.0) & (np.array(rs) < 1.3)])))}
            np.save(HERE / 'cau' / f'A2_{tag}_{name}.npy', out.astype(np.float32)); log(f'{tag}/{name}: biaix d\'anell màx (σ) a 1,0–1,3 = {rep["cases"][f"{tag}/{name}"]["ring_bias_in_sd_units_max_1.0_1.3"]:.2f}')
    savejson(REB35 / 'A2_p05_limbe_roi.json', rep)
    # vistes: retall 1:1 del quadrant NE (limbe) A|B|C per WOWbil, i perfils
    from PIL import Image, ImageDraw, ImageFont
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    f = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 14)
    for name in ('WOWbil', 'WOW', 'MGN'):
        panels = []
        for tag in ('A_suport_tal_qual', 'B_forat_omplert_perfil_radial', 'C_normalitzat_radial_ln'):
            o = np.load(HERE / 'cau' / f'A2_{tag}_{name}.npy'); cy, cx = int(CY - y0), int(CX - x0); crop = o[cy - 700:cy + 100, cx - 100:cx + 700]
            v = crop[np.isfinite(crop)]; lo, hi = np.percentile(v, [0.5, 99.5]); u8 = np.uint8(np.clip(np.nan_to_num((crop - lo) / (hi - lo), nan=0), 0, 1) * 255); panels.append((u8, tag))
        sheet = Image.new('L', (3 * 810, 830), 30); d = ImageDraw.Draw(sheet)
        for j, (u8, tag) in enumerate(panels):
            sheet.paste(Image.fromarray(u8), (j * 810, 30)); d.text((j * 810 + 4, 6), f'{name} · {tag} · quadrant NE 1:1 (limbe a baix a l\'esquerra)', fill=255, font=f)
        sheet.save(VIS35 / f'A2_limbe_{name}_A_B_C.png')
    fig, axs = plt.subplots(1, 3, figsize=(15, 4))
    for ax, name in zip(axs, ('WOWbil', 'WOW', 'MGN')):
        for tag in ('A_suport_tal_qual', 'B_forat_omplert_perfil_radial', 'C_normalitzat_radial_ln'):
            c = rep['cases'][f'{tag}/{name}']; ax.plot(c['ring_median_r'], np.array(c['ring_median']) / max(c['sd_1.05_1.6'], 1e-9), label=tag[:14])
        ax.set_title(f'{name}: mediana per anell / σ'); ax.set_xlabel('r (R☉)'); ax.legend(fontsize=7); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(VIS35 / 'A2_limbe_mediana_per_anell.png', dpi=110); log('A2 fet')


if __name__ == '__main__':
    main()
