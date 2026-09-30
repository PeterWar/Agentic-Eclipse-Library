"""B4a (V37) · Les cinc capes no azimutals (01, 02, 04, 05, 06) amb la MATEIXA recepta
de la V29/V30/V31 sobre la fusió V32 (només canvia la font).

Recepta (refine_detail.py / fine_variants.py / package_v31.py):
  x_c = ln TOTAL_c per canal; d_c = ACHF(x_c, σ) / scale_c(r)  (perfils de contrast de la
  V29, congelats); d = mediana dels tres canals; tanh amb l'escala congelada de la V29/V30;
  suavitzat S/N amb el mapa de resolució de la V29; H1 (centre_rings); després el
  suavitzat gaussià extern de la V31 (σ 3 px; 1,5 per a 04) normalitzat al suport.
Sortides: cau/{tag}_v34_u16.npy, rebut amb H1, H1b i prova azimutal; vistes.
"""
from comu37 import *
from fuse_and_filter import achf, sn_smooth, centre_rings
from audit_geometry import polar, correlate
from qa_rasters import h1, h1_setup
import f3
from PIL import Image

LAYERS = {
    '01': {'sigmas': (2, 4, 8, 16, 32), 'tanh': 'refined:achf', 'sigma_ext': 3.0, 'name': '01 ACHF fi 2-32'},
    '02': {'sigmas': (24,), 'tanh': 'refined:passalt24', 'sigma_ext': 3.0, 'name': '02 Passa-alt 24'},
    '04': {'sigmas': (1, 2, 4, 8, 16), 'tanh': 'variants:micro1_16', 'sigma_ext': 1.5, 'name': '04 ACHF micro 1-16'},
    '05': {'sigmas': (2, 4, 8, 16, 32, 48), 'tanh': 'variants:fi2_48', 'sigma_ext': 3.0, 'name': '05 ACHF fi 2-48'},
    '06': {'sigmas': (4, 8, 16, 32, 64), 'tanh': 'variants:estructura4_64', 'sigma_ext': 3.0, 'name': '06 ACHF estructura 4-64'},
}


def tanh_scale(spec):
    kind, key = spec.split(':')
    if kind == 'refined':
        return float(json.loads((CAUF / 'refined_detail_receipt.json').read_text())['filters'][key]['scale_tanh'])
    return float(json.loads((ROOT / 'research/tools/v30/cau/fine_variants_receipt.json').read_text())['variants'][key]['scale_tanh'])


def png(a, name):
    im = Image.fromarray(np.uint8(np.clip(a, 0, 1) * 255)); im.thumbnail((1800, 1800), Image.Resampling.LANCZOS); im.save(VIS37 / name)


def main():
    r, t = coords(); m = np.load(CAU36 / 'support_v36.npy'); total = np.load(CAU36 / 'fusion_total_v36.npy', mmap_mode='r')
    profiles = json.loads((CAUF / 'refined_detail_receipt.json').read_text())['profiles']
    sigma_map = np.load(CAUF / 'resolution_sigma.npy', mmap_mode='r')
    all_sigmas = sorted({s for v in LAYERS.values() for s in v['sigmas']})
    outs = {k: [] for k in LAYERS}
    for c in range(3):
        good = m & (total[..., c] > 0); x = np.log(np.maximum(total[..., c], 1e-8))
        x, frep = farcit_perfil_ln_A(x, good, r); w = np.ones((H, W), np.float32)    # V37: condició de contorn al forat i fora del suport (farcit A); convolució sense màscara
        log(f'canal {c}: farcit {frep}')
        p = profiles[str(c)]; scale = np.interp(np.log(np.maximum(r / RS, 1e-5)), p['lnr_centres'], p['robust_contrast']).astype(np.float32)
        acc = {k: np.zeros((H, W), np.float32) for k in LAYERS}
        for s in all_sigmas:
            band = x - normgauss(x, w, s)
            for k, v in LAYERS.items():
                if s in v['sigmas']:
                    acc[k] += band / len(v['sigmas'])
            log(f'canal {c} σ{s}')
        for k in LAYERS:
            np.save(CAU37 / f'{k}_c{c}_v37.npy', np.where(good, acc[k] / scale, np.nan).astype(np.float32))
        del acc, x, good, w, band, scale
    ctx = h1_setup(r, m); rs = np.linspace(1.12, 2.5, 60).astype(np.float32); R = polar(np.log(np.maximum(np.asarray(total[..., 1]), 1)), CX, CY, RS, rs)
    ctrl = {str(d): correlate(np.roll(R, round(d * 4), axis=1), R) for d in (0, 180)}
    rep = {'font': 'fusion_total_v37 (V34 + suports plens, conformació δ, esvaïments Vixen/A, relleu 1,9→3,5)', 'perfils_contrast': 'V29 refined_detail_receipt, congelats', 'mapa_resolucio': 'V29 resolution_sigma, congelat', 'capes': {}}
    wsup = m.astype(np.float32)
    for k, v in LAYERS.items():
        reals = [np.load(CAU37 / f'{k}_c{c}_v37.npy', mmap_mode='r') for c in range(3)]; d = np.zeros((H, W), np.float32)
        for y in range(0, H, 256):
            d[y:y + 256] = np.nan_to_num(np.nanmedian(np.stack([q[y:y + 256] for q in reals]), axis=0), nan=0)
        arep = {'anivellament_previ': 'REFUSAT: amb anells d\'1 px H1 0,02 però H1b 4,2 (jitter de les medianes dels anells parcials); suavitzat σ3 anells H1 0,12 i H1b 3,0. Es queda el farcit A sol.'}
        sc = tanh_scale(v['tanh']); mapped = (.5 * np.tanh(d / max(sc, 1e-6))).astype(np.float32)
        sm, _ = sn_smooth(mapped, m, sigma=sigma_map); centered, hist = centre_rings(sm, m, r); a = np.clip(.5 + centered, 0, 1); a[~m] = .5
        # suavitzat extern de la V31 (mateixa recepta que package_v31.py)
        se = v['sigma_ext']; den = gauss(wsup, se); b = .5 + gauss((a - .5) * wsup, se) / np.maximum(den, 1e-8); b[~m] = .5
        u = np.round(np.clip(b, 0, 1) * 65535).astype(np.uint16); np.save(CAU37 / f'{k}_v37_u16.npy', u); np.save(CAU37 / f'{k}_v37_raw.npy', d)
        png(b, f'B4_{k}_v37_llenc_sencer.png')
        rep['capes'][k] = {'name': v['name'] + ' · V37', 'anivellament_previ': arep, 'sigmas': v['sigmas'], 'scale_tanh': sc, 'sigma_ext_px': se, 'H1': h1(b, m, ctx), 'H1_history': hist,
                           'H1b': f3.anells_de_calaix(b, r, m), 'geometria_azimutal': correlate(polar(b, CX, CY, RS, rs), R), 'controls_180': ctrl, 'sha256_u16': sha(CAU37 / f'{k}_v37_u16.npy')}
        log(f"{k}: H1 pitjor {rep['capes'][k]['H1']['worst']['error']:.4f} · H1b {rep['capes'][k]['H1b']:.3f} · geometria {rep['capes'][k]['geometria_azimutal']}")
        for c in range(3):
            (CAU37 / f'{k}_c{c}_v37.npy').unlink()
        del reals, d, mapped, sm, centered, a, b, u
    savejson(REB37 / 'B4a_capes_cadena.json', rep); log('B4a fet')


if __name__ == '__main__':
    main()
