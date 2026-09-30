"""C1 · Les cinc capes de cadena (01, 02, 04, 05, 06) amb la recepta de la V32 (font fusió V32,
perfils de contrast V29, escales tanh congelades, H1, σ extern V31) però amb UN sol canvi:
el suavitzat S/N ja no és el mapa de resolució congelat de la V29 (σ ≤ 8, calibrat per
coherència en tessel·les de 512 px) sinó f3.suavitza_sn autocalibrat sobre la capa mateixa
(t 0,18, σ ≤ 24 px, píxel a píxel, cap radi): on el gra mana, la resolució baixa.
Sortides: cau/{tag}_v33_u16.npy, mapa σ per capa, rebut amb H1/H1b/geometria i perfil de σ."""
from comu33 import *
sys.path.insert(0, str(ROOT / 'research/tools/v29'))
from fuse_and_filter import centre_rings
from audit_geometry import polar, correlate
from qa_rasters import h1, h1_setup
from PIL import Image
sys.path.insert(0, str(ROOT / 'research/tools/v32_arcs_20260907'))
from b4a_capes_cadena import LAYERS, tanh_scale


def png(a, name):
    im = Image.fromarray(np.uint8(np.clip(a, 0, 1) * 255)); im.thumbnail((1800, 1800), Image.Resampling.LANCZOS); im.save(VIS33 / name)


def main():
    r, t = coords(); m = np.load(CAU32 / 'support_v32.npy'); total = np.load(CAU32 / 'fusion_total_v32.npy', mmap_mode='r')
    profiles = json.loads((CAUF / 'refined_detail_receipt.json').read_text())['profiles']
    only = [a for a in sys.argv[1:] if a in LAYERS] or list(LAYERS)
    all_sigmas = sorted({s for k, v in LAYERS.items() if k in only for s in v['sigmas']})
    for c in range(3):
        good = m & (total[..., c] > 0); x = np.log(np.maximum(total[..., c], 1e-8)); w = good.astype(np.float32)
        p = profiles[str(c)]; scale = np.interp(np.log(np.maximum(r / RS, 1e-5)), p['lnr_centres'], p['robust_contrast']).astype(np.float32)
        acc = {k: np.zeros((H, W), np.float32) for k in only}
        for s in all_sigmas:
            band = x - normgauss(x, w, s)
            for k in only:
                if s in LAYERS[k]['sigmas']:
                    acc[k] += band / len(LAYERS[k]['sigmas'])
            log(f'canal {c} σ{s}')
        for k in only:
            np.save(CAU33 / f'{k}_c{c}.npy', np.where(good, acc[k] / scale, np.nan).astype(np.float32))
        del acc, x, good, w, band, scale
    ctx = h1_setup(r, m); rs = np.linspace(1.12, 2.5, 60).astype(np.float32); R = polar(np.log(np.maximum(np.asarray(total[..., 1]), 1)), CX, CY, RS, rs)
    rep = {'font': 'fusion_total_v32 (idèntica a la V32)', 'canvi_unic': f'sn_smooth(mapa V29) → snmap.sn_v33: σ = max(mapa C0 λ_min/8, f3.suavitza_sn t={T_SN}), smax={SMAX}', 'capes': {}}
    wsup = m.astype(np.float32)
    for k in only:
        v = LAYERS[k]; reals = [np.load(CAU33 / f'{k}_c{c}.npy', mmap_mode='r') for c in range(3)]; d = np.zeros((H, W), np.float32)
        for y in range(0, H, 256):
            d[y:y + 256] = np.nan_to_num(np.nanmedian(np.stack([q[y:y + 256] for q in reals]), axis=0), nan=0)
        sc = tanh_scale(v['tanh']); mapped = (.5 * np.tanh(d / max(sc, 1e-6))).astype(np.float32)
        sm, sig = sn_v33(mapped, m); np.save(CAU33 / f'{k}_sigma.npy', sig.astype(np.float16))
        centered, hist = centre_rings(sm, m, r); a = np.clip(.5 + centered, 0, 1); a[~m] = .5
        se = v['sigma_ext']; den = gauss(wsup, se); b = .5 + gauss((a - .5) * wsup, se) / np.maximum(den, 1e-8); b[~m] = .5
        u = np.round(np.clip(b, 0, 1) * 65535).astype(np.uint16); np.save(CAU33 / f'{k}_v33_u16.npy', u)
        png(b, f'C1_{k}_v33_llenc_sencer.png'); png(np.clip(sig / SMAX, 0, 1), f'C1_{k}_sigma_map.png')
        rep['capes'][k] = {'name': v['name'] + ' · V33 S/N', 'sigmas': v['sigmas'], 'scale_tanh': sc, 'sigma_ext_px': se, 'H1': h1(b, m, ctx), 'H1_history': hist,
                           'H1b': f3.anells_de_calaix(b, r, m), 'geometria_azimutal': correlate(polar(b, CX, CY, RS, rs), R), 'perfil_sigma': sigma_profile(sig, m, r), 'sha256_u16': sha(CAU33 / f'{k}_v33_u16.npy')}
        log(f"{k}: H1 pitjor {rep['capes'][k]['H1']['worst']['error']:.4f} · H1b {rep['capes'][k]['H1b']:.3f} · geometria {rep['capes'][k]['geometria_azimutal']} · σ p50 a 4 R: {[z['sigma_p50'] for z in rep['capes'][k]['perfil_sigma'] if z['r']==4.0]}")
        for c in range(3):
            (CAU33 / f'{k}_c{c}.npy').unlink()
        del reals, d, mapped, sm, sig, centered, a, b, u
    old = json.loads((REB33 / 'C1_capes_cadena.json').read_text()) if (REB33 / 'C1_capes_cadena.json').exists() else {'capes': {}}
    old.update({k_: v_ for k_, v_ in rep.items() if k_ != 'capes'}); old['capes'].update(rep['capes']); savejson(REB33 / 'C1_capes_cadena.json', old); log('C1 fet')


if __name__ == '__main__':
    main()
