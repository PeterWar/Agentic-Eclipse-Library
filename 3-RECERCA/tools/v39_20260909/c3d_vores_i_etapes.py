"""C3d (V40 pilot) · Portes de GEOMETRIA i de GRA demanades per Codex (09-09): (1) perfil del rms de cada capa (u16 − 0,5) contra la distància SIGNADA a la
vora exterior del camp de la Vixen (dins > 0) i contra la distància a la vora del forat, V38 / V39 / candidata; el salt dins/fora no pot ser pitjor que el de
la V38; (2) residu de gra: rms de la candidata / rms de la V38 a finestres predefinides on la banda és ≥ 90 % soroll (5,5 R☉ i 3,7 R☉, per banda);
(3) etapa a etapa (només informatiu): rms del float abans del tanh/LUT i del u16. Només lectura. Ús: c3d_vores_i_etapes.py <etiqueta> [rutes u16 candidates: clau=ruta …]"""
from comu39 import *
import cv2
from scipy.ndimage import gaussian_filter
PC38 = ROOT / 'research/tools/v38_20260908/purs/cau'; PC39 = HERE39 / 'purs/cau'
V39F = CAU39 / 'v39_final'; P39F = PC39 / 'v39_final'   # còpies de les capes V39 publicades (la candidata sobreescriu les rutes vives)
BASE = {'01': (CAU38 / '01_v38_u16.npy', V39F / '01_v39_u16.npy'), '04': (CAU38 / '04_v38_u16.npy', V39F / '04_v39_u16.npy'), '06': (CAU38 / '06_v38_u16.npy', V39F / '06_v39_u16.npy'),
        'P03': (PC38 / 'P03_MGN_u16.npy', P39F / 'P03_MGN_u16.npy'), 'P04': (PC38 / 'P04_WOW_u16.npy', P39F / 'P04_WOW_u16.npy'), 'P05': (PC38 / 'P05_WOW_bilateral_u16.npy', P39F / 'P05_WOW_bilateral_u16.npy')}
BINS = [(-600, -300), (-300, -100), (-100, -30), (-30, 0), (0, 30), (30, 100), (100, 300), (300, 600), (600, 900), (900, 1300)]
WINS = {'5.5R': (int(CX - 5.5 * RS), int(CY + 0.6 * RS)), '3.7R': (5089, 5294)}; BANDS = [(0, 1), (1, 2), (2, 4), (4, 8), (8, 16), (16, 32), (32, 64)]


def main():
    tag = sys.argv[1]; cand = dict(a.split('=', 1) for a in sys.argv[2:])
    wv = np.nan_to_num(np.asarray(np.load(CAU38 / 'weight_vixen_v38.npy', mmap_mode='r'), np.float32)); m = np.load(CAU38 / 'support_v38.npy'); r, t = coords()
    mv = wv > 0.005; d = np.where(mv, cv2.distanceTransform(mv.astype(np.uint8), cv2.DIST_L2, 5), -cv2.distanceTransform((~mv).astype(np.uint8), cv2.DIST_L2, 5)); far = m & (r > 2.8 * RS)
    rep = {'etiqueta': tag, 'bins_px': BINS, 'vora_vixen': {}, 'gra': {}}
    log(f"pes Vixen per bin: {' '.join(f'{np.mean(wv[far & (d > a) & (d <= b)]):.2f}' for a, b in BINS)}")
    for k, (p38, p39) in BASE.items():
        rows = {}
        for lab, p in (('V38', p38), ('V39', p39), (tag, Path(cand[k]) if k in cand else None)):
            if p is None or not Path(p).exists(): continue
            a = np.load(p, mmap_mode='r'); sd = []
            for a0, b0 in BINS:
                sel = far & (d > a0) & (d <= b0); sd.append(float(np.std(np.asarray(a[sel], np.float32) / 65535 - 0.5)))
            rows[lab] = sd; salt = np.mean(sd[7:9]) / np.mean(sd[5:7]); log(f'{k} {lab}: rms per bin ' + ' '.join(f'{v:.3f}' for v in sd) + f' · salt dins(300–900)/fora(30–300) ×{salt:.2f}')
            rows[lab + '_salt'] = float(salt)
        rep['vora_vixen'][k] = rows
        # gra per banda a les finestres de soroll
        g = {}
        for wn, (X, Y) in WINS.items():
            sl = (slice(Y - 512, Y + 512), slice(X - 512, X + 512)); core = np.s_[128:896, 128:896]; per = {}
            for lab, p in (('V38', p38), ('V39', p39), (tag, Path(cand[k]) if k in cand else None)):
                if p is None or not Path(p).exists(): continue
                a = np.asarray(np.load(p, mmap_mode='r')[sl], np.float32) / 65535 - 0.5; out = []
                for s1, s2 in BANDS:
                    lo = a if s1 == 0 else gaussian_filter(a, s1); hi = gaussian_filter(a, s2); out.append(float(np.std((lo - hi)[core])))
                per[lab] = {'total': float(np.std(a[core])), 'bandes': out}
            if tag in per and 'V38' in per:
                q = [c / max(v, 1e-9) for c, v in zip(per[tag]['bandes'], per['V38']['bandes'])]; per['residu_candidata_sobre_V38'] = q; per['residu_total'] = per[tag]['total'] / max(per['V38']['total'], 1e-9)
                log(f"{k} gra {wn}: residu per banda (candidata/V38) " + ' '.join(f'{v:.2f}' for v in q) + f" · total ×{per['residu_total']:.2f} (V39 ×{per['V39']['total'] / max(per['V38']['total'], 1e-9):.2f})")
            g[wn] = per
        rep['gra'][k] = g
    # retalls 1:1 (1024 px) V38 | V39 | candidata centrats a la vora exterior de la Vixen: dos punts (est i sud-oest), r ≈ 4–6 R☉
    from PIL import Image, ImageDraw
    vora = far & (np.abs(d) < 2) & (r > 4 * RS) & (r < 6.5 * RS); ys, xs = np.nonzero(vora[::8, ::8])
    punts = []
    for az0 in (0.0, -135.0):
        ang = np.degrees(np.arctan2(ys * 8 - CY, xs * 8 - CX)); i = int(np.argmin(np.abs(((ang - az0) + 180) % 360 - 180))) if len(ys) else None
        if i is not None: punts.append((int(xs[i] * 8), int(ys[i] * 8)))
    for k in ('P04', 'P05', '01'):
        if k not in cand: continue
        for (x0, y0) in punts:
            sl = (slice(max(y0 - 512, 0), y0 + 512), slice(max(x0 - 512, 0), x0 + 512)); tiles = []
            for lab, p in (('V38', BASE[k][0]), ('V39', BASE[k][1]), (tag, Path(cand[k]))):
                a = np.asarray(np.load(p, mmap_mode='r')[sl], np.float32) / 65535; lo, hi = np.percentile(a, [0.5, 99.5]); im = Image.fromarray(np.uint8(np.clip((a - lo) / max(hi - lo, 1e-6), 0, 1) * 255)).convert('RGB')
                ImageDraw.Draw(im).text((8, 8), f'{k} {lab} vora Vixen ({x0},{y0}) r={r[y0, x0] / RS:.1f}', fill=(255, 60, 60)); tiles.append(im)
            W_ = sum(t.width for t in tiles) + 8 * (len(tiles) - 1); H_ = max(t.height for t in tiles); canvas = Image.new('RGB', (W_, H_), (20, 20, 20)); x = 0
            for t_ in tiles: canvas.paste(t_, (x, 0)); x += t_.width + 8
            canvas.save(VIS39 / f'C3d_vora_vixen_{k}_{x0}_{y0}_{tag}.png')
    savejson(REB39 / f'C3d_vores_i_gra_{tag}.json', rep); log('C3d fet')


if __name__ == '__main__':
    main()
