"""A3 · Mapa de fronteres de fusió HDR del llenç sencer, amb les marques de Pere.

Per cada tren (Sony B primari, Sony A, Vixen): fracció de pes de cada fotograma
per cel·la (graella 1/4). Frontera = on canvia el joc de fotogrames:
  F(x) = Σ_i |∇ f_i(x)| / 2   (0 = mateix joc; 1 = un fotograma substitueix un altre)
i mapa del fotograma dominant. Les marques lila/blau (i verd, per contrast) es
dibuixen a sobre com a rectangles. Cap correcció; només lectura.
"""
from comu32 import *
from PIL import Image, ImageDraw
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def boundary_maps(tag, group=None):
    Wm = np.load(CAU32 / f'{tag}_w.npy', mmap_mode='r'); meta = json.loads((CAU32 / f'{tag}_meta.json').read_text())['frames']
    idx = [m['i'] for m in meta if (group is None or m['group'] == group)]
    tot = np.zeros((HC, WC), np.float32)
    for i in idx:
        tot += Wm[i]
    Fsum = np.zeros((HC, WC), np.float32); dom = np.full((HC, WC), -1, np.int16); fmax = np.zeros((HC, WC), np.float32)
    for i in idx:
        f = np.where(tot > 0, Wm[i] / np.maximum(tot, 1e-20), 0).astype(np.float32)
        gy, gx = np.gradient(f)
        Fsum += np.hypot(gx, gy)
        better = f > fmax; dom[better] = i; fmax[better] = f[better]
    return Fsum / 2, dom, tot > 0, meta, idx

def draw_marks(img, colors=('lila', 'blau', 'verd'), q=Q):
    dr = ImageDraw.Draw(img)
    col = {'lila': (200, 60, 220), 'blau': (40, 120, 255), 'verd': (40, 200, 60)}
    for m in marks(colors):
        x0, y0, x1, y1 = [v / q for v in m['bbox']]
        dr.rectangle([x0, y0, x1, y1], outline=col[m['color']], width=2)
    return img

def main():
    r, t = coarse_polar()
    rows = {}
    for tag, group, name in [('sony', 'sony_B', 'SonyB'), ('sony', 'sony_A', 'SonyA'), ('vixen', None, 'Vixen')]:
        Fb, dom, sup, meta, idx = boundary_maps(tag, group)
        # imatge: fronteres en gris (0..1 → 0..255, gamma 0.5 perquè es vegin les febles)
        u = np.uint8(np.clip(np.sqrt(np.clip(Fb * 8, 0, 1)), 0, 1) * 255); u[~sup] = 20
        img = Image.fromarray(u).convert('RGB'); draw_marks(img)
        # anells de referència cada R☉
        dr = ImageDraw.Draw(img)
        for k in range(1, 13):
            rr = k * RS / Q; dr.ellipse([CX / Q - rr, CY / Q - rr, CX / Q + rr, CY / Q + rr], outline=(90, 90, 90))
        img.save(VIS / f'A3_fronteres_{name}.png')
        # fotograma dominant amb colors per exposició
        exps = sorted(set(meta[i]['exp'] for i in idx))
        cmap = plt.get_cmap('tab20')
        rgb = np.zeros((HC, WC, 3), np.uint8)
        for i in idx:
            c = np.array(cmap(exps.index(meta[i]['exp']) % 20)[:3]) * 255
            rgb[dom == i] = c
        img2 = Image.fromarray(rgb); draw_marks(img2)
        dr = ImageDraw.Draw(img2)
        for k in range(1, 13):
            rr = k * RS / Q; dr.ellipse([CX / Q - rr, CY / Q - rr, CX / Q + rr, CY / Q + rr], outline=(255, 255, 255))
        legend = ' · '.join(f'{e:g}s' for e in exps)
        dr.text((10, 10), f'{name}: fotograma dominant per cel·la (color = exposició: {legend})', fill=(255, 255, 255))
        img2.save(VIS / f'A3_dominant_{name}.png')
        # radi (mediana azimutal) on cada fotograma passa de dominar a no fer-ho: taula
        tab = []
        for i in idx:
            f = np.where(sup, np.load(CAU32 / f'{tag}_w.npy', mmap_mode='r')[i] / np.maximum(np.where(sup, 1, 0) * 0 + 1e-20 + np.where(sup, 1, 0) * 0, 1e-20), 0)
        rows[name] = {'n_frames': len(idx), 'boundary_p50_p90_p99': [float(np.percentile(Fb[sup], p)) for p in (50, 90, 99)]}
        # marques sobre fronteres: fracció de la caixa amb Fb > llindar, contra el mateix a caixes girades 180° (control nul)
        rep = []
        for m in marks(('lila', 'blau')):
            x0, y0, x1, y1 = [int(v / Q) for v in m['bbox']]
            box = Fb[y0:y1 + 1, x0:x1 + 1]; sb = sup[y0:y1 + 1, x0:x1 + 1]
            if sb.sum() == 0:
                continue
            # control: la mateixa caixa girada 180° al voltant del Sol
            gx0, gy0 = int(2 * CX / Q - x1), int(2 * CY / Q - y1); gx1, gy1 = int(2 * CX / Q - x0), int(2 * CY / Q - y0)
            gx0, gy0 = max(gx0, 0), max(gy0, 0); gx1, gy1 = min(gx1, WC - 1), min(gy1, HC - 1)
            ctrl = Fb[gy0:gy1 + 1, gx0:gx1 + 1]; sc = sup[gy0:gy1 + 1, gx0:gx1 + 1]
            rep.append({'id': m['id'], 'r': m['paint_radius_R_p05_p50_p95'][1], 'frontera_max': float(box[sb].max()), 'frontera_p90': float(np.percentile(box[sb], 90)),
                        'control180_max': float(ctrl[sc].max()) if sc.sum() else None})
        rows[name]['marques'] = rep
        log(f'{name}: {len(idx)} fotogrames; frontera p50/p90/p99 {rows[name]["boundary_p50_p90_p99"]}')
    savejson(REB / 'A3_fronteres.json', rows)
    log('A3 fet')

if __name__ == '__main__':
    main()
