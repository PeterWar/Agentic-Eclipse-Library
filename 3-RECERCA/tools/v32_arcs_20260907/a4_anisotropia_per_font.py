"""A4 · On entren els arcs? Anisotropia tangencial per anell, font i escala.

Per a cada anell (2,5–3, 3–3,5, 3,5–4, 4–4,5, 4,5–5 R☉) i escala de banda
(DoG de σ i 2σ, σ = 4, 8, 16, 32 px), la puntuació d'orientació del tensor
d'estructura: +1 = crestes TANGENCIALS (arcs centrats al Sol), −1 = crestes
RADIALS (raigs), 0 = isòtrop. Ponderada per l'energia del gradient. La mateixa
mesura, amb el mateix codi, sobre:
  · la base V31 (G lineal fusionat) en ln, i cada tren sol (Vixen, Sony A, Sony B);
  · les capes finals de la V31 (02 passa-alt, 05, 06, 01) i les pures (P01, P03, P04, P05);
  · controls: soroll blanc filtrat igual, i la base amb el pas radial invertit (girada 90° no
    val: l'anisotropia radial és invariant); el control és un camp sintètic r^-3 + soroll.
Si la base ja és tangencial a l'escala dels arcs, els arcs són a la font; si només
ho són les capes, els fa la cadena. Només lectura.
"""
from comu32 import *
from scipy.ndimage import gaussian_filter

ANELLS = [(2.5, 3.0), (3.0, 3.5), (3.5, 4.0), (4.0, 4.5), (4.5, 5.0), (1.2, 1.6), (1.6, 2.0), (2.0, 2.5)]
SIGMES = [4, 8, 16, 32]
BOX = None

def crop_box():
    r1 = 5.2 * RS
    x0, x1 = int(CX - r1), int(CX + r1) + 1; y0, y1 = int(CY - r1), int(CY + r1) + 1
    return max(x0, 0), max(y0, 0), min(x1, W), min(y1, H)

def orientation_scores(img, m, r, t, sig):
    """Puntuació tangencial per anell a l'escala sig (DoG sig, 2 sig)."""
    w = m.astype(np.float32)
    def ng(a, s):
        return gaussian_filter(a * w, s, mode='nearest') / np.maximum(gaussian_filter(w, s, mode='nearest'), 1e-6)
    band = np.where(m, ng(img, sig) - ng(img, 2 * sig), 0).astype(np.float32)
    gy, gx = np.gradient(band)
    # tensor d'estructura suavitzat a 1,5 sig
    s2 = 1.5 * sig
    Jxx = gaussian_filter(gx * gx, s2); Jyy = gaussian_filter(gy * gy, s2); Jxy = gaussian_filter(gx * gy, s2)
    # orientació del gradient dominant: angle 2φ del tensor
    c2 = Jxx - Jyy; s2v = 2 * Jxy; E = Jxx + Jyy
    # direcció radial unitària (cos t, sin t): el gradient d'un arc és RADIAL → cos(2(φ−t)) = +1
    cr = np.cos(2 * t); sr = np.sin(2 * t)
    proj = (c2 * cr + s2v * sr)           # = |J_aniso| cos(2(φ−t))
    aniso = np.hypot(c2, s2v) / np.maximum(E, 1e-20)
    rows = []
    for a, b in ANELLS:
        k = m & (r >= a * RS) & (r < b * RS) & (E > 0)
        if k.sum() < 1000:
            rows.append({'anell': [a, b], 'n': int(k.sum()), 'score': None}); continue
        score = float(np.sum(proj[k]) / np.maximum(np.sum(E[k]), 1e-20))
        rows.append({'anell': [a, b], 'n': int(k.sum()), 'score': score, 'anisotropia_mitjana': float(np.mean(aniso[k])),
                     'energia': float(np.mean(E[k]))})
    return rows

def load_ln(path, sup, box, log=True):
    x0, y0, x1, y1 = box
    mm = np.load(path, mmap_mode='r')
    a = np.asarray(mm[y0:y1, x0:x1, 1] if mm.ndim == 3 else mm[y0:y1, x0:x1], np.float32)
    m = np.isfinite(a) & (a > 0) if log else np.isfinite(a)
    if sup is not None:
        m &= np.asarray(np.load(sup, mmap_mode='r')[y0:y1, x0:x1]) > 0
    v = np.where(m, np.log(np.maximum(a, 1e-12)) if log else a, 0).astype(np.float32)
    return v, m

def main():
    box = crop_box(); x0, y0, x1, y1 = box
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    r = np.hypot(xx - CX, yy - CY); t = np.arctan2(yy - CY, xx - CX)
    fonts = {
        'base_G_ln': (V31P / 'cau/base_G.npy', V31P / 'cau/support.npy', True),
        'vixen_G_ln': (FIX / 'vixen_corrected_G.npy', CAUF / 'vixen_support.npy', True),
        'sonyA_G_ln': (FIX / 'sony_A_corrected_G.npy', None, True),
        'sonyB_G_ln': (FIX / 'sony_B_corrected_G.npy', None, True),
        'V31_01_ACHF_fi_u16': (ROOT / 'research/tools/v31/cau/01_final_u16.npy', V31P / 'cau/support.npy', False),
        'V31_02_passalt24_u16': (ROOT / 'research/tools/v31/cau/02_final_u16.npy', V31P / 'cau/support.npy', False),
        'V31_05_ACHF_fi48_u16': (ROOT / 'research/tools/v31/cau/05_final_u16.npy', V31P / 'cau/support.npy', False),
        'V31_06_estructura_u16': (ROOT / 'research/tools/v31/cau/06_final_u16.npy', V31P / 'cau/support.npy', False),
        'V29_passalt24_raw': (CAUF / 'passalt24_raw.npy', V31P / 'cau/support.npy', False),
        'V29_achf_raw': (CAUF / 'achf_raw.npy', V31P / 'cau/support.npy', False),
        'P01_NRGF': (V31P / 'cau/P01_NRGF_float.npy', None, False),
        'P03_MGN': (V31P / 'cau/P03_MGN_float.npy', None, False),
        'P04_WOW': (V31P / 'cau/P04_WOW_float.npy', None, False),
        'P05_WOW_bilateral': (V31P / 'cau/P05_WOW_bilateral_float.npy', None, False),
        'C01_passalt24_lineal': (V31P / 'cau/C01_Passa_alt24_lineal_float.npy', None, False),
    }
    if os.environ.get('V32'):
        PC = HERE / 'purs/cau'
        fonts = {
            'base_G_ln_v32': (CAU32 / 'base_G_v32.npy', CAU32 / 'support_v32.npy', True),
            'vixen_G_ln_v32': (CAU32 / 'vixen_total_v32.npy', CAUF / 'vixen_support.npy', True),
            'sonyA_G_ln_v32': (CAU32 / 'sony_A_total_v32.npy', None, True),
            'sonyB_G_ln_v32': (CAU32 / 'sony_B_total_v32.npy', None, True),
            'V32_01_ACHF_fi_u16': (CAU32 / '01_v32_u16.npy', CAU32 / 'support_v32.npy', False),
            'V32_02_passalt24_u16': (CAU32 / '02_v32_u16.npy', CAU32 / 'support_v32.npy', False),
            'V32_05_ACHF_fi48_u16': (CAU32 / '05_v32_u16.npy', CAU32 / 'support_v32.npy', False),
            'V32_06_estructura_u16': (CAU32 / '06_v32_u16.npy', CAU32 / 'support_v32.npy', False),
            'V32_03_azimutal_u16': (CAU32 / '03_v32_u16.npy', CAU32 / 'support_v32.npy', False),
            'P01_NRGF_v32': (PC / 'P01_NRGF_float.npy', None, False),
            'P03_MGN_v32': (PC / 'P03_MGN_float.npy', None, False),
            'P04_WOW_v32': (PC / 'P04_WOW_float.npy', None, False),
            'P05_WOW_bilateral_v32': (PC / 'P05_WOW_bilateral_float.npy', None, False),
            'C01_passalt24_lineal_v32': (PC / 'C01_Passa_alt24_lineal_float.npy', None, False),
        }
        fonts = {k: v for k, v in fonts.items() if v[0].exists()}
    out = {}
    for name, (p, sup, lg) in fonts.items():
        v, m = load_ln(p, sup, box, lg)
        if name.endswith('u16'):
            v = v / 65535.0
        out[name] = {str(s): orientation_scores(v, m, r, t, s) for s in SIGMES}
        log(name + ' ' + ' '.join(f"s{s}:" + ','.join(f"{z['score']:+.3f}" if z['score'] is not None else '–' for z in out[name][str(s)][:5]) for s in SIGMES))
        del v, m
    # control sintètic: perfil radial r^-3 + cel + soroll blanc, mateixa geometria
    rng = np.random.default_rng(7)
    m = (r > 1.0 * RS)
    synth = np.log(np.maximum((r / RS) ** -3 + 0.02, 1e-9)) + rng.normal(0, 0.02, r.shape).astype(np.float32)
    out['CONTROL_r-3_soroll'] = {str(s): orientation_scores(synth.astype(np.float32), m, r, t, s) for s in SIGMES}
    log('control ' + ' '.join(f"s{s}:" + ','.join(f"{z['score']:+.3f}" for z in out['CONTROL_r-3_soroll'][str(s)][:5]) for s in SIGMES))
    savejson(REB / ('A4v32_anisotropia.json' if os.environ.get('V32') else 'A4_anisotropia.json'), {'anells_R': ANELLS, 'sigmes_px': SIGMES, 'score': '+1 tangencial (arcs) · −1 radial (raigs) · 0 isòtrop; ponderat per energia del gradient de la banda DoG(σ,2σ)', 'fonts': out})
    # taula
    lines = ['# A4 · anisotropia tangencial per anell i escala (+ = arcs, − = raigs)', '']
    for s in SIGMES:
        lines += [f'## σ = {s} px', '', '| font | ' + ' | '.join(f'{a}-{b}' for a, b in ANELLS) + ' |', '|---|' + '---|' * len(ANELLS)]
        for name in out:
            lines.append(f'| {name} | ' + ' | '.join((f"{z['score']:+.3f}" if z['score'] is not None else '–') for z in out[name][str(s)]) + ' |')
        lines.append('')
    (OUT32 / ('lliurables/A4v32_ANISOTROPIA.md' if os.environ.get('V32') else 'lliurables/A4_ANISOTROPIA.md')).write_text('\n'.join(lines) + '\n')
    log('A4 fet')

if __name__ == '__main__':
    main()
