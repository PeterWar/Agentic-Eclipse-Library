"""[CLON V42 de la V38/V39: mateixa recepta; només canvien les rutes d'entrada (apuntament B recompost amb rotació i registre dels llargs; base SENSE ESTRELLES per als filtres) i de sortida (cau/ i output/v42).]"""
"""B4b (V38) · Les tres capes azimutals de la V32 (03 σr0, 03 σr4, 07 σr8) regenerades amb la MATEIXA recepta sobre la fusió V38 (Vixen amb la vora lunar corregida; Sony corregida de la V36). Recuperades per al projecte complet V38.

Heretat: B4b · Les tres capes azimutals (03 V29 σr0, 03 V30 σr4, 07 σr8) amb la recepta
de la V29 (gran_azimuthal) / c03 (filter03) / V30 (angular_pilots) sobre la font V32.

  · per tren: banda angular G8 − (G32+G64+G128)/3 en polar (FFT periòdica, escales d'arc
    físiques), amb regularització radial normalitzada al suport σr ∈ {0, 4, 8} px (V30);
  · d = Σ_tren w·banda / Σ_tren w·scale (perfils de contrast de la V29, congelats), pesos de
    tren de la fusió V32 (weight_vixen_v32);
  · tanh amb l'escala congelada 0,1767; S/N; H1; u16 (fora del suport 32768).
"""
import sys as _s0; from pathlib import Path as _P0; _s0.path.insert(0, str(_P0(__file__).resolve().parent.parent / 'v32_arcs_20260907'))
from comu32 import *
import sys as _s; _s.path.insert(0, str(Path(__file__).resolve().parent)); from comu42 import CAU42, CAU38, REB42, VIS42, CAU36
VIS = VIS42
from fuse_and_filter import sn_smooth, centre_rings
from audit_geometry import polar, correlate
from qa_rasters import h1, h1_setup
from scipy.ndimage import gaussian_filter1d
import f3
from PIL import Image

SIGMAS_R = {'03': 0.0, '03v30': 4.0, '07': 8.0}
NAMES = {'03': '03 ACHF azimutal 8-128', '03v30': '03 ACHF azimutal 8-128 r4', '07': '07 ACHF azimutal suau r8'}


def angular_polar(x, m, r, t):
    """Com gran_azimuthal.angular, però retorna la banda en polar (p) i la validesa, per regularitzar."""
    x = np.where(m, x, 0).astype(np.float32); mf = m.astype(np.float32)
    r0 = 400; nr = int(np.ceil(r.max())) - r0 + 2; nt = 16384; theta = np.arange(nt, dtype=np.float32) * 2 * np.pi / nt
    freq = np.fft.rfftfreq(nt)[None, :]; p = np.empty((nr, nt), np.float32); valid = np.empty_like(p)
    for start in range(0, nr, 64):
        rr = (r0 + np.arange(start, min(start + 64, nr), dtype=np.float32))[:, None]
        mx = (CX + rr * np.cos(theta)[None, :]).astype(np.float32); my = (CY + rr * np.sin(theta)[None, :]).astype(np.float32)
        wm = cv2.remap(mf, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT); xp = cv2.remap(x, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        fx = np.fft.rfft(xp, axis=1); fw = np.fft.rfft(wm, axis=1); bands = []
        for sigma in (8, 32, 64, 128):
            sp = sigma * nt / (2 * np.pi * rr); g = np.exp(-2 * np.pi ** 2 * sp ** 2 * freq ** 2)
            den = np.fft.irfft(fw * g, n=nt, axis=1); num = np.fft.irfft(fx * g, n=nt, axis=1)
            bands.append(np.where(den > 1e-5, num / np.maximum(den, 1e-5), 0).astype(np.float32))
        p[start:start + len(rr)] = bands[0] - (bands[1] + bands[2] + bands[3]) / 3; valid[start:start + len(rr)] = wm
    return p, valid, r0, nt


def back(p, m, r, t, r0, nt):
    ext = np.concatenate([p[:, -1:], p, p[:, :1]], axis=1)
    mx = (np.mod(t, 2 * np.pi) * nt / (2 * np.pi) + 1).astype(np.float32); my = (r - r0).astype(np.float32)
    return np.where(m, cv2.remap(ext, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT), 0)


def png(a, name):
    im = Image.fromarray(np.uint8(np.clip(a, 0, 1) * 255)); im.thumbnail((1800, 1800), Image.Resampling.LANCZOS); im.save(VIS / name)


def main():
    r, t = coords(); oldrep = json.loads((CAUF / 'gran_azimuthal_receipt.json').read_text()); profiles = oldrep['post_contrast_profiles']
    mv = np.load(CAUF / 'vixen_support.npy'); ms = np.load(CAUF / 'sony_support.npy')
    V = np.load(CAU42 / 'vixen_total_v42_sense_estrelles.npy', mmap_mode='r')[..., 1]; S = np.load(CAU42 / 'sony_corrected_total_v42_sense_estrelles.npy', mmap_mode='r')[..., 1]
    masks = {'vixen': mv & np.isfinite(V) & (V > 0), 'sony': ms & np.isfinite(S) & (S > 0)}
    m = masks['vixen'] | masks['sony']
    wv = np.load(CAU42 / 'weight_vixen_v42.npy'); wv = np.where(masks['sony'], wv, masks['vixen'].astype(np.float32)) * masks['vixen']; ws = (1 - wv) * masks['sony']
    sigma_map = np.load(CAUF / 'resolution_sigma.npy', mmap_mode='r')
    bands = {}
    for tag, a, mask in [('vixen', V, masks['vixen']), ('sony', S, masks['sony'])]:
        p, valid, r0, nt = angular_polar(np.log(np.maximum(np.asarray(a), 1e-8)), mask, r, t)
        for key, sr in SIGMAS_R.items():
            q = p if sr == 0 else gaussian_filter1d(p * valid, sr, axis=0, mode='constant', cval=0) / np.maximum(gaussian_filter1d(valid, sr, axis=0, mode='constant', cval=0), 1e-8)
            bands[(tag, key)] = back(q, mask, r, t, r0, nt).astype(np.float32); log(f'angular {tag} σr{sr:g}')
        del p, valid
    scale = np.zeros((H, W), np.float32)
    for tag, w in [('vixen', wv), ('sony', ws)]:
        pr = profiles[tag]; scale += w * np.interp(np.log(np.maximum(r / RS, 1e-5)), pr['lnr_centres'], pr['robust_contrast']).astype(np.float32)
    ctx = h1_setup(r, m); rs = np.linspace(1.12, 2.5, 60).astype(np.float32)
    fus = np.load(CAU42 / 'fusion_total_v42_sense_estrelles.npy', mmap_mode='r')[..., 1]; R = polar(np.log(np.maximum(np.asarray(fus), 1)), CX, CY, RS, rs)
    rep = {'operador': oldrep['operator'], 'scale_tanh': oldrep['scale_tanh'], 'perfils': 'V29 post_contrast_profiles, congelats', 'capes': {}}
    for key, sr in SIGMAS_R.items():
        d = wv * bands[('vixen', key)] + ws * bands[('sony', key)]; d = np.where(m, d / np.maximum(scale, .002), 0).astype(np.float32)
        mapped = (.5 * np.tanh(d / oldrep['scale_tanh'])).astype(np.float32); sm, _ = sn_smooth(mapped, m, sigma=sigma_map); centered, hist = centre_rings(sm, m, r)
        a = np.clip(.5 + centered, 0, 1); a[~m] = .5; u = np.round(a * 65535).astype(np.uint16); u[~m] = 32768
        np.save(CAU42 / f'{key}_v42_u16.npy', u); np.save(CAU42 / f'{key}_v42_raw.npy', d); png(a, f'B4b_{key}_v42_llenc_sencer.png')
        rep['capes'][key] = {'name': NAMES[key] + ' · V38', 'sigma_radial_px': sr, 'H1': h1(a, m, ctx), 'H1_history': hist, 'H1b': f3.anells_de_calaix(a, r, m),
                             'geometria_azimutal': correlate(polar(a, CX, CY, RS, rs), R), 'sha256_u16': sha(CAU42 / f'{key}_v42_u16.npy')}
        log(f"{key}: H1 pitjor {rep['capes'][key]['H1']['worst']['error']:.4f} · H1b {rep['capes'][key]['H1b']:.3f} · geometria {rep['capes'][key]['geometria_azimutal']}")
    np.save(CAU42 / 'gran_support_v42.npy', m)
    savejson(REB42 / 'B4b_capes_azimutals.json', rep); log('B4b fet')


if __name__ == '__main__':
    main()
