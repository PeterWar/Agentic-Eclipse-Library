"""Mapa de la raó capa_apilat / 1-125 (ID5, fotograma únic sense banda) al voltant de la Lluna, amb la frontera
geomètrica de la banda sobreposada. Si la banda és real, la raó fa un graó just a la frontera."""
import sys, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from geom import *
ID5 = np.load(f'{V2B}/src_id5_G.npy', mmap_mode='r')
def ratio_map(i, S=1120):
    G = np.load(f'{V2B}/src_id{i}_G.npy', mmap_mode='r')
    e = ELL[str(i)]; cx, cy = e['cx'], e['cy']
    x0, y0 = int(cx-S//2), int(cy-S//2)
    a = np.asarray(G[y0:y0+S, x0:x0+S], np.float32)/65535.
    b = np.asarray(ID5[y0+464:y0+464+S, x0+458:x0+458+S], np.float32)/65535.
    xx, yy = grid(y0, y0+S, x0, x0+S)
    F, N = ref_fraction(i, xx, yy)
    d = np.hypot(xx-cx, yy-cy)
    r = a/np.maximum(b, 1e-3)
    return a, b, r, F, N, d, (x0, y0), (cx, cy)
if __name__ == '__main__':
    for i in [int(s) for s in sys.argv[1:]] or [7, 8, 9]:
        a, b, r, F, N, d, (x0, y0), (cx, cy) = ratio_map(i)
        Rm = R_moon(i)
        # perfil de la raó per sector de 15° i radi (bins d'1 px) entre +5 i +70 px: salt a la frontera
        az = np.degrees(np.arctan2(-(np.mgrid[0:r.shape[0]][:,None]+y0-cy), (np.mgrid[0:r.shape[1]][None,:]+x0-cx))) % 360
        banda = F > 1.0/N + 1e-3
        print(f'== ID{i}: raó ID{i}/ID5; salt de la raó a la frontera de la banda per sector (mediana 2-8 px dins vs 2-8 px fora, en % de la raó fora)')
        for s0 in range(0, 360, 15):
            ms = (az >= s0) & (az < s0+15); m = banda & ms
            if not m.any(): continue
            fr = d[m].max()
            dins = ms & banda & (d > fr-8) & (d <= fr-2); fora = ms & ~banda & (d >= fr+2) & (d < fr+8)
            if dins.sum() < 30 or fora.sum() < 30: continue
            # treu la tendència: ajust lineal raó~d fora (fr+2..fr+20), extrapola
            ext = ms & ~banda & (d >= fr+2) & (d < fr+20)
            coef = np.polyfit(d[ext], r[ext], 1)
            pred = np.median(np.polyval(coef, d[dins])); obs = np.median(r[dins])
            print(f'   {s0:3d}: fr=+{fr-Rm:4.1f} px  raó dins {obs:.4f} esperada {pred:.4f}  salt {100*(obs-pred)/pred:+5.2f} %   (nivell ID{i} {np.median(a[dins]):.3f}, ID5 {np.median(b[dins]):.3f})')
        # imatge: raó normalitzada localment (dividida pel seu suavitzat σ=12 per treure el gradient), estirada ±5 %
        sm = ndi.gaussian_filter(r, 12)
        rel = r/np.maximum(sm, 1e-3)
        img = np.clip((rel-0.95)/0.10, 0, 1)
        img[d < Rm-2] = 0
        im = Image.fromarray((img*255).astype(np.uint8)).convert('RGB')
        dr = ImageDraw.Draw(im)
        # frontera de la banda: contorn de F
        edge = ndi.binary_dilation(banda) & ~banda
        ys, xs = np.nonzero(edge)
        for yv, xv in zip(ys[::3], xs[::3]): dr.point((int(xv), int(yv)), fill=(255, 0, 0))
        im.save(f'ratio_id{i}_vs_id5.png')
        print(f'   PNG: ratio_id{i}_vs_id5.png (raó/suavitzat σ12, estirament 0,95–1,05; frontera de la banda en vermell)')
