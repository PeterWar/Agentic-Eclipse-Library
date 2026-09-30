"""Revisió V36 · extreu les marques de Pere de V36_Artefactes.psb (còpia adaptada de la revisió V35).

Detecció PRIMÀRIA per diferència: cada capa anotada es compara píxel a píxel amb la mateixa
capa de V32.psb (les 22 capes de Pere són les capes 18–39 de V32.psb, mateix ordre; només els
noms de les dues 03 canvien pel renom posterior). Photoshop re-quantitza els 16 bits en desar
(escala interna 0–32768): el 44 % dels píxels i la màscara difereixen en ±1 DN16 sense cap
pintura (mesurat). Pintura = |A − O| > 1 DN16 en algun canal.
La tonalitat (HSV del píxel pintat) només serveix per CLASSIFICAR el color del pinzell.
Si en una capa la diferència no és creïble (més del 5 % del llenç), es declara i s'usa el
detector de tonalitat de la revisió V31 com a recurs, marcat al rebut.
Cap PSB s'escriu. Sortides a output/revisio_marques_v32_20260907/ (rebuts, vistes) i finestres
natives a windows/ (pintat + original) per a les comparacions.
"""
import sys, json, gc, zlib, time
from pathlib import Path
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
from psd_tools import PSDImage
ROOT = Path('/Users/USUARI/Downloads/Eclipse 2026'); D = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'research/tools/v29')); from inspect_inputs import channel as slow_channel, sha
sys.path.insert(0, str(ROOT / 'research/tools/eclipse_determinista')); from comu import Run
RUN = Run('REVISIO_MARQUES_V36', '20260908', str(ROOT / 'output/revisio_marques_v36_20260908'))
WIN = D / 'windows'; CAU = D / 'cau'
for p in [RUN.vista(''), RUN.lliurable(''), RUN.rebut(''), WIN, CAU]:
    Path(p).mkdir(parents=True, exist_ok=True)
CT = Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals')
ANOT = CT / 'V36_Artefactes.psb'; ORIG = CT / 'V36.psb'; OFFSET = 0
ORIG_SHA = 'fb3f3cefd9492eb8740315b1e567c447787f6af8b3504a6d2a36e5d11385d1bf'
CX, CY, RS = 5361.768111973117, 3775.747534140857, 440.60304883027544
FONT = '/System/Library/Fonts/Supplemental/Arial.ttf'
cv2.setNumThreads(4)
COLORS = {1: 'groc', 2: 'verd', 3: 'blau', 4: 'lila', 5: 'vermell', 6: 'taronja', 7: 'neutre'}
LEGEND = {'groc': (255, 220, 0), 'verd': (0, 220, 60), 'blau': (40, 120, 255), 'lila': (200, 60, 255), 'vermell': (255, 40, 40), 'taronja': (255, 140, 0), 'neutre': (200, 200, 200)}


def channel(l, cid):
    w, h = l.size
    if cid == -2:
        m = l._record.mask_data
        if m is None:
            return None
        w, h = m.right - m.left, m.bottom - m.top
    for ci, cd in zip(l._record.channel_info, l._channels):
        if int(ci.id) != cid:
            continue
        if l._psd.depth == 16 and int(cd.compression) == 3:
            delta = np.frombuffer(zlib.decompress(cd.data), '>u2').reshape(h, w)
            return np.cumsum(delta, axis=1, dtype=np.uint16)
        if l._psd.depth == 16 and int(cd.compression) == 2:
            return np.frombuffer(zlib.decompress(cd.data), '>u2').reshape(h, w).astype(np.uint16)
        return slow_channel(l, cid)
    return None


def font(n):
    return ImageFont.truetype(FONT, n)


def write(p, j):
    Path(p).write_text(json.dumps(p and j, indent=2, ensure_ascii=False, default=lambda v: v.item() if isinstance(v, np.generic) else v.tolist()) + '\n')


def hue_class(h):
    """Classe de color a partir de la tonalitat OpenCV (0–179), amb el tall blau/lila a 116 (mesurat a la V31)."""
    c = np.full(h.shape, 7, np.uint8)
    c[(h >= 20) & (h < 40)] = 1; c[(h >= 40) & (h < 95)] = 2; c[(h >= 95) & (h < 116)] = 3; c[(h >= 116) & (h < 168)] = 4
    c[(h < 10) | (h >= 168)] = 5; c[(h >= 10) & (h < 20)] = 6
    return c


def full_mask(m, md, bbox):
    """Màscara de capa al quadre de la capa (el quadre de la màscara pot ser més gran o més petit)."""
    if m is None:
        return None
    bx0, by0, bx1, by1 = bbox
    out = np.full((by1 - by0, bx1 - bx0), int(md.background_color) * 257, np.uint16)
    x0, y0, x1, y1 = max(md.left, bx0), max(md.top, by0), min(md.right, bx1), min(md.bottom, by1)
    if x1 > x0 and y1 > y0:
        out[y0 - by0:y1 - by0, x0 - bx0:x1 - bx0] = m[y0 - md.top:y1 - md.top, x0 - md.left:x1 - md.left]
    return out


def gray_display(u8, alpha, mask, h, w):
    wgt = np.ones((h, w), np.float32)
    if alpha is not None:
        wgt *= alpha.astype(np.float32) / 65535
    if mask is not None:
        wgt *= mask.astype(np.float32) / 65535
    if u8.ndim == 3:
        return np.round(u8 * wgt[..., None] + 127 * (1 - wgt[..., None])).astype(np.uint8), wgt
    return np.round(u8 * wgt + 127 * (1 - wgt)).astype(np.uint8), wgt


def main():
    t0 = time.time()
    assert sha(ORIG) == ORIG_SHA, 'V36.psb ha canviat'
    sa = PSDImage.open(ANOT); so = PSDImage.open(ORIG); la = list(sa); lo = list(so)
    assert sa.size == so.size == (10551, 7506) and sa.depth == so.depth == 16 and len(la) == 11 and len(lo) == 11
    H, W = sa.height, sa.width
    rep = {'annotated': str(ANOT), 'annotated_bytes': ANOT.stat().st_size, 'original': str(ORIG), 'original_sha256': ORIG_SHA, 'offset_in_original': OFFSET, 'size': [W, H], 'layers': []}
    contact = Image.new('RGB', (4 * 480, 3 * 384), (28, 28, 28)); draw = ImageDraw.Draw(contact)
    for i, l in enumerate(la):
        o = lo[i + OFFSET]
        name_ok = (l.name == o.name)
        assert name_ok, (i, l.name, o.name)
        assert l.bbox == o.bbox, (i, l.bbox, o.bbox)
        bx0, by0, bx1, by1 = l.bbox; hh, ww = by1 - by0, bx1 - bx0
        A = np.stack([channel(l, c) for c in (0, 1, 2)], axis=2); O = np.stack([channel(o, c) for c in (0, 1, 2)], axis=2)
        dabs = np.abs(A.astype(np.int32) - O.astype(np.int32)).max(axis=2); diff = dabs > 1; nd = int(diff.sum()); frac = nd / diff.size; requant = int((dabs == 1).sum()); dmax = int(dabs.max()); del dabs
        aA, aO = channel(l, -1), channel(o, -1); mA, mO = channel(l, -2), channel(o, -2)
        alpha_equal = (aA is None and aO is None) or (aA is not None and aO is not None and aA.shape == aO.shape and int(np.abs(aA.astype(np.int32) - aO.astype(np.int32)).max()) <= 1)
        mdA, mdO = l._record.mask_data, o._record.mask_data
        mask_equal = (mA is None and mO is None) or (mA is not None and mO is not None and mdA.left == mdO.left and mdA.top == mdO.top and mA.shape == mO.shape and int(np.abs(mA.astype(np.int32) - mO.astype(np.int32)).max()) <= 1)
        if mA is None and mO is not None:
            mask_equal = 'absent_a_l_anotat'
        A8 = (A // 257).astype(np.uint8); O8 = (O // 257).astype(np.uint8); del A, O
        hsv = cv2.cvtColor(A8, cv2.COLOR_RGB2HSV); hue, sat, val = hsv[..., 0], hsv[..., 1], hsv[..., 2]
        vivid = (sat > 25) & (val > 20)
        method = 'diff'
        if frac > 0.05:
            method = 'hue_fallback'; paint = vivid.copy()
            if i == 0:
                paint[:] = False   # base de color: la tonalitat sola no identifica pintura
        else:
            paint = diff
        cls = hue_class(hue); cls[~vivid] = 7; codes = np.where(paint, cls, 0).astype(np.uint8)
        counts_px = {COLORS[k]: int(np.sum(codes == k)) for k in COLORS}
        joined = cv2.morphologyEx(paint.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        n, lab, stats, cent = cv2.connectedComponentsWithStats(joined, 8)
        marks = []
        for k in range(1, n):
            x, y, w, h_, area = map(int, stats[k])
            if area < 80:
                continue
            local = (lab[y:y + h_, x:x + w] == k) & paint[y:y + h_, x:x + w]
            cnt = int(local.sum())
            if cnt < 60:
                continue
            cl = codes[y:y + h_, x:x + w][local]; parts = {COLORS[c]: int(np.sum(cl == c)) for c in COLORS if np.sum(cl == c) > 0}
            vivid_parts = {c: v for c, v in parts.items() if c != 'neutre'}
            color = max(vivid_parts, key=vivid_parts.get) if vivid_parts else 'neutre'
            hl = hue[y:y + h_, x:x + w][local & vivid[y:y + h_, x:x + w]]
            yy, xx = np.nonzero(local); xs = xx + x + bx0; ys = yy + y + by0
            rad = np.hypot(xs - CX, ys - CY) / RS; az = np.degrees(np.arctan2(ys - CY, xs - CX))
            cx, cy = float(cent[k][0] + bx0), float(cent[k][1] + by0)
            marks.append({'id': f'L{i:02d}-M{len(marks) + 1:02d}', 'layer_index': i, 'color': color, 'color_parts': parts,
                          'hue_mode': int(np.bincount(hl, minlength=180).argmax()) if hl.size else None,
                          'hue_p10_p90': [int(np.percentile(hl, 10)), int(np.percentile(hl, 90))] if hl.size else None,
                          'bbox': [x + bx0, y + by0, x + w + bx0, y + h_ + by0], 'center_xy': [cx, cy],
                          'radius_R': float(np.hypot(cx - CX, cy - CY) / RS), 'azimuth_image_deg': float(np.degrees(np.arctan2(cy - CY, cx - CX))),
                          'paint_radius_R_p05_p50_p95': [float(t) for t in np.percentile(rad, [5, 50, 95])],
                          'paint_azimuth_deg_min_max': [float(az.min()), float(az.max())], 'paint_pixels': cnt})
        del lab, joined
        # finestres natives (pintat i original amb alfa+màscara sobre gris) i vistes
        disp, wgt = gray_display(O8 if i == 0 else O8[..., 1], aO, full_mask(mO, mdO, l.bbox), hh, ww)
        for m in marks:
            x0, y0, x1, y1 = m['bbox']; pad = 40
            x0 = max(bx0, x0 - pad); y0 = max(by0, y0 - pad); x1 = min(bx1, x1 + pad); y1 = min(by1, y1 + pad)
            m['window_bbox'] = [x0, y0, x1, y1]
            sl = (slice(y0 - by0, y1 - by0), slice(x0 - bx0, x1 - bx0))
            np.save(WIN / (m['id'] + '_marked.npy'), A8[sl]); np.save(WIN / (m['id'] + '_original.npy'), disp[sl])
            np.save(WIN / (m['id'] + '_codes.npy'), codes[sl])
        np.savez_compressed(CAU / f'{i:02d}_mark_codes.npz', codes=codes, bbox=np.array(l.bbox))
        im = Image.fromarray(A8); im.thumbnail((1600, 1600), Image.Resampling.LANCZOS); full = Path(RUN.vista(f'L{i:02d}_anotada_sencera.png')); im.save(full)
        imo = Image.fromarray(disp); imo.thumbnail((1600, 1600), Image.Resampling.LANCZOS); imo.save(RUN.vista(f'L{i:02d}_original_sencera.png'))
        sm = im.copy(); sm.thumbnail((480, 342), Image.Resampling.LANCZOS); xx_, yy_ = (i % 4) * 480, (i // 4) * 384
        contact.paste(sm, (xx_, yy_ + 42)); draw.text((xx_ + 6, yy_ + 5), f'{i:02d} {l.name[:49]}', fill='white', font=font(14))
        cc = {c: sum(m['color'] == c for m in marks) for c in LEGEND}
        draw.text((xx_ + 6, yy_ + 24), f"{len(marks)} components · " + ' '.join(f'{c[:3]} {v}' for c, v in cc.items() if v), fill='#cccccc', font=font(12))
        # atles de comparació: pintat | original
        panels = []
        for m in marks:
            p = Image.new('RGB', (1060, 568), (24, 24, 24)); d = ImageDraw.Draw(p); rr = m['paint_radius_R_p05_p50_p95']
            d.text((8, 5), f"{m['id']} · {m['color']} · traç {rr[0]:.2f}–{rr[2]:.2f} R☉ · {l.name[:40]}", font=font(16), fill='white')
            for j, (suffix, label) in enumerate([('_marked.npy', 'Pintat per Pere'), ('_original.npy', 'V36 sense pintura (alfa i màscara sobre gris)')]):
                a = np.load(WIN / (m['id'] + suffix)); pi = Image.fromarray(a).convert('RGB'); pi.thumbnail((520, 510), Image.Resampling.LANCZOS)
                p.paste(pi, (j * 530 + (530 - pi.width) // 2, 52)); d.text((j * 530 + 8, 29), label, font=font(13), fill='#cccccc')
            panels.append(p)
        for k in range(0, len(panels), 4):
            sub = panels[k:k + 4]; sheet = Image.new('RGB', (2120, 568 * ((len(sub) + 1) // 2)), (24, 24, 24))
            for t, p in enumerate(sub):
                sheet.paste(p, ((t % 2) * 1060, (t // 2) * 568))
            sheet.save(RUN.vista(f'L{i:02d}_comparacio_{k // 4 + 1:02d}.png'))
        row = {'index': i, 'original_index': i + OFFSET, 'name': l.name, 'original_name': o.name, 'visible_annot': l.visible, 'blend_annot': l.blend_mode.name, 'opacity_annot': l.opacity,
               'visible_orig': o.visible, 'blend_orig': o.blend_mode.name, 'opacity_orig': o.opacity, 'bbox': list(l.bbox),
               'diff_pixels': nd, 'diff_fraction': frac, 'requantized_pm1_pixels': requant, 'diff_max_DN16': dmax, 'detection': method, 'alpha_equal': alpha_equal, 'mask_equal': mask_equal,
               'paint_pixels_by_color': counts_px, 'marks': marks, 'color_counts': cc, 'full_view': str(full)}
        rep['layers'].append(row); write(RUN.rebut('marks_inventory.json'), rep)
        print(f'{i:02d} {l.name} · pintura {nd} px ({100*frac:.4f} %) · ±1: {requant} · max {dmax} · {method} · alfa={alpha_equal} màscara={mask_equal} · {len(marks)} comp · {cc} · {time.time()-t0:.0f} s', flush=True)
        del A8, O8, hsv, hue, sat, val, vivid, cls, codes, paint, diff, disp, wgt, im, imo, panels; gc.collect()
    contact.save(RUN.vista('00_totes_les_capes_anotades.png'))
    rep['annotated_sha256'] = sha(ANOT)
    rep['detection'] = ('primary: pixel difference > 1 DN16 against the same layer of V36.psb (same 11 layers, same order; Photoshop re-quantizes 16-bit data by +-1 on save, alpha/mask compared with the same tolerance); hue (OpenCV H) only classifies brush colour: '
                        'groc 20-40, verd 40-95, blau 95-116, lila 116-168, vermell <10 or >=168, taronja 10-20, neutre = not vivid (S<=25 or V<=20); 5px closing for indexing only; '
                        'component>=80 px joined, >=60 painted px; components are indexing units, not distinct defects')
    write(RUN.rebut('marks_inventory.json'), rep); print('COMPLETE', flush=True)


if __name__ == '__main__':
    main()
