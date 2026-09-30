"""B5b · Vistes abans/després per a Pere: cada capa de filtre V31 contra la V32,
a les finestres de les seves marques (1:1) i al llenç sencer.

Mateixa LUT als dos costats (els u16 tal com van al PSB). Cap retall del producte:
les finestres són només de diagnosi. També: base V31 contra base V32 (passa-alt 24
en ln, ±1 %) a les mateixes finestres, i el compost per defecte sencer.
"""
from comu32 import *
from PIL import Image, ImageDraw

OLD_U16 = {
    '03 ACHF azimutal 8-128 · V29': FIX / 'gran_u16.npy',
    '03 ACHF azimutal 8-128 · V30': ROOT / 'research/tools/v30/cau/gran_r4_u16.npy',
    '07 ACHF azimutal suau r8 · V30': ROOT / 'research/tools/v30/cau/gran_r8_u16.npy',
    '01 ACHF fi 2-32 · V31': ROOT / 'research/tools/v31/cau/01_final_u16.npy',
    '02 Passa-alt 24 · V31': ROOT / 'research/tools/v31/cau/02_final_u16.npy',
    '04 ACHF micro 1-16 · V31': ROOT / 'research/tools/v31/cau/04_final_u16.npy',
    '05 ACHF fi 2-48 · V31': ROOT / 'research/tools/v31/cau/05_final_u16.npy',
    '06 ACHF estructura 4-64 · V31': ROOT / 'research/tools/v31/cau/06_final_u16.npy',
    'P01 NRGF · V31': V31P / 'cau/P01_NRGF_u16.npy', 'P02 RHEF · comparacio amb anells · V31': V31P / 'cau/P02_RHEF_u16.npy', 'P03 MGN · V31': V31P / 'cau/P03_MGN_u16.npy',
    'P04 WOW sense denoise · V31': V31P / 'cau/P04_WOW_u16.npy', 'P05 WOW bilateral sense denoise · V31': V31P / 'cau/P05_WOW_bilateral_u16.npy', 'P06 NAFE n65 · V31': V31P / 'cau/P06_NAFE_u16.npy',
    'P07 ACHF precursor sigma16 · V31': V31P / 'cau/P07_ACHF_precursor16_u16.npy', 'P08 ACHF precursor sigma32 · V31': V31P / 'cau/P08_ACHF_precursor32_u16.npy', 'P09 SWAP · pilot llum blanca · V31': V31P / 'cau/P09_SWAP_pilot_u16.npy',
    'C01 Passa-alt24 lineal · control · V31': V31P / 'cau/C01_Passa_alt24_lineal_u16.npy'}
PC = HERE / 'purs/cau'
NEW_U16 = {
    '03 ACHF azimutal 8-128 · V29': CAU32 / '03_v32_u16.npy', '03 ACHF azimutal 8-128 · V30': CAU32 / '03v30_v32_u16.npy', '07 ACHF azimutal suau r8 · V30': CAU32 / '07_v32_u16.npy',
    '01 ACHF fi 2-32 · V31': CAU32 / '01_v32_u16.npy', '02 Passa-alt 24 · V31': CAU32 / '02_v32_u16.npy', '04 ACHF micro 1-16 · V31': CAU32 / '04_v32_u16.npy',
    '05 ACHF fi 2-48 · V31': CAU32 / '05_v32_u16.npy', '06 ACHF estructura 4-64 · V31': CAU32 / '06_v32_u16.npy',
    'P01 NRGF · V31': PC / 'P01_NRGF_u16.npy', 'P02 RHEF · comparacio amb anells · V31': PC / 'P02_RHEF_u16.npy', 'P03 MGN · V31': PC / 'P03_MGN_u16.npy',
    'P04 WOW sense denoise · V31': PC / 'P04_WOW_u16.npy', 'P05 WOW bilateral sense denoise · V31': PC / 'P05_WOW_bilateral_u16.npy', 'P06 NAFE n65 · V31': PC / 'P06_NAFE_u16.npy',
    'P07 ACHF precursor sigma16 · V31': PC / 'P07_ACHF_precursor16_u16.npy', 'P08 ACHF precursor sigma32 · V31': PC / 'P08_ACHF_precursor32_u16.npy', 'P09 SWAP · pilot llum blanca · V31': PC / 'P09_SWAP_pilot_u16.npy',
    'C01 Passa-alt24 lineal · control · V31': PC / 'C01_Passa_alt24_lineal_u16.npy'}


def crop(mm, x0, y0, x1, y1):
    return np.asarray(mm[y0:y1, x0:x1])


def u8(u16):
    return np.uint8(np.asarray(u16) // 257)


def passalt_crop(arr, sup, x0, y0, x1, y1, s=24, pad=96):
    xa, ya = max(x0 - pad, 0), max(y0 - pad, 0); xb, yb = min(x1 + pad, W), min(y1 + pad, H)
    a = np.ascontiguousarray(np.asarray(arr[ya:yb, xa:xb], np.float32)); m = np.isfinite(a) & (a > 0)
    if sup is not None:
        m &= np.asarray(sup[ya:yb, xa:xb]) > 0
    la = np.where(m, np.log(np.maximum(a, 1e-12)), 0).astype(np.float32); hp = np.where(m, la - normgauss(la, m.astype(np.float32), s), 0)
    v = np.uint8(np.clip(0.5 + 0.5 * hp / 0.01, 0, 1) * 255); v[~m] = 40
    return v[y0 - ya:y1 - ya, x0 - xa:x1 - xa]


def main():
    ms = marks(('lila', 'blau'))
    bylayer = {}
    for m in ms:
        bylayer.setdefault(m['layer'], []).append(m)
    old_base = np.load(V31P / 'cau/base_G.npy', mmap_mode='r'); new_base = np.load(CAU32 / 'base_G_v32.npy', mmap_mode='r'); sup = np.load(CAU32 / 'support_v32.npy', mmap_mode='r')
    index = []
    for name, mk in bylayer.items():
        if name not in NEW_U16 or not NEW_U16[name].exists():
            continue
        old = np.load(OLD_U16[name], mmap_mode='r'); new = np.load(NEW_U16[name], mmap_mode='r')
        sel = sorted(mk, key=lambda z: -z['paint_pixels'])[:4]
        S = 640; panels = []
        for m in sel:
            cx, cy = int(m['center_xy'][0]), int(m['center_xy'][1]); x0, y0 = max(cx - S // 2, 0), max(cy - S // 2, 0); x1, y1 = min(x0 + S, W), min(y0 + S, H)
            panels.append((m, u8(crop(old, x0, y0, x1, y1)), u8(crop(new, x0, y0, x1, y1)), passalt_crop(old_base, sup, x0, y0, x1, y1), passalt_crop(new_base, sup, x0, y0, x1, y1), (x0, y0)))
        im = Image.new('L', (4 * (S + 8), len(panels) * (S + 30) + 30), 40); dr = ImageDraw.Draw(im)
        dr.text((8, 6), f'{name} → V32 · finestres de les marques de Pere (1:1, mateixa LUT) · columnes: capa V31 | capa V32 | base V31 passa-alt 24 ±1% | base V32 passa-alt 24 ±1%', fill=255)
        for j, (m, a, b, c, d, (x0, y0)) in enumerate(panels):
            yy = 30 + j * (S + 30)
            for i, p in enumerate((a, b, c, d)):
                im.paste(Image.fromarray(p), (i * (S + 8), yy + 22))
            bx0, by0, bx1, by1 = m['bbox']
            for i in range(4):
                dr.rectangle([i * (S + 8) + bx0 - x0, yy + 22 + by0 - y0, i * (S + 8) + bx1 - x0, yy + 22 + by1 - y0], outline=200)
            dr.text((8, yy + 4), f"{m['id']} · {m['color']} · {m['family']} · r {m['paint_radius_R_p05_p50_p95'][0]:.2f}–{m['paint_radius_R_p05_p50_p95'][2]:.2f} R☉", fill=255)
        fn = 'B5_' + name.split(' ·')[0].replace(' ', '_').replace('/', '-') + '_marques_abans_despres.png'; im.save(VIS / fn); index.append({'layer': name, 'file': fn, 'marks': [m['id'] for m in sel]})
        # llenç sencer costat a costat (reduït)
        A = Image.fromarray(u8(np.asarray(old[::6, ::6]))); B = Image.fromarray(u8(np.asarray(new[::6, ::6])))
        big = Image.new('L', (A.width * 2 + 10, A.height + 26), 40); big.paste(A, (0, 26)); big.paste(B, (A.width + 10, 26)); d2 = ImageDraw.Draw(big); d2.text((6, 6), name + ' · V31 (esquerra) · V32 (dreta)', fill=255)
        big.save(VIS / ('B5_' + name.split(' ·')[0].replace(' ', '_').replace('/', '-') + '_llenc_abans_despres.png'))
        log(name)
    savejson(REB / 'B5_montatges.json', {'index': index})
    log('B5b fet')


if __name__ == '__main__':
    main()
