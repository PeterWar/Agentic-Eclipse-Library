"""Catàleg de les marques de la V34: famílies per geometria, encaix amb les marques de la V31
(mateixa capa, solapament de caixes) i mapa global. Consumeix marks_inventory.json; no toca cap PSB."""
from extract import *
import csv
OLD = ROOT / 'output/revisio_marques_v33_20260907/4-rebuts/review_catalog.json'
# capa antiga (PSB V32 anotat, 22 capes) → capa nova (PSB V33 anotat, 11 capes)
OLD2NEW = {i: i for i in range(11)}


_SD = None
def signed_dist_vixen():
    """Distància amb signe a la vora del suport Vixen (ple, sense el forat lunar): + dins."""
    global _SD
    if _SD is None:
        CAUF = ROOT / 'research/tools/v29/cau_final'; mv = np.load(CAUF / 'vixen_support.npy'); yy, xx = np.ogrid[:mv.shape[0], :mv.shape[1]]
        mvf = mv | (np.hypot(xx - CX, yy - CY) < 1.6 * RS)
        _SD = np.where(mvf, cv2.distanceTransform(mvf.astype(np.uint8), cv2.DIST_L2, 5), -cv2.distanceTransform((~mvf).astype(np.uint8), cv2.DIST_L2, 5)).astype(np.float32)
    return _SD


def vixen_edge_fraction(m):
    """Fracció dels píxels pintats de la marca a menys de 250 px de la vora Vixen."""
    x0, y0, x1, y1 = m['bbox']; codes = np.load(WIN / (m['id'] + '_codes.npy')); wx0, wy0, wx1, wy1 = m['window_bbox']
    sd = signed_dist_vixen()[wy0:wy1, wx0:wx1]; k = codes > 0
    return float(np.mean(np.abs(sd[k]) < 250)) if k.any() else 0.0


def family(row, m):
    i = row['index']; r = m['paint_radius_R_p05_p50_p95']; x0, y0, x1, y1 = m['bbox']
    m['vixen_edge_fraction'] = vixen_edge_fraction(m)
    if m['vixen_edge_fraction'] > 0.5:
        return 'Contorn del FOV Vixen dins del camp Sony (nou a la V34)'
    if m['color'] == 'verd':
        return 'Contorn dubtós (verd); preservar'
    if m['color'] == 'groc':
        return 'Costura diagonal interna NW' if (x1 < CX and y1 < CY + 600) else 'Traç groc fora de la diagonal'
    if x0 > 8000 and y1 < 2600 and (x1 - x0) < 700:
        return 'Anomalia local NE'
    if r[0] < 1.15 and r[2] < 1.6:
        return 'Transició estreta al limbe'
    if r[1] > 6:
        return 'Contorn ample exterior'
    if r[1] < 2.3:
        return 'Contorn transversal interior (fronteres HDR Vixen)'
    if 2.3 <= r[1] < 3.0:
        return 'Contorn intermedi (entrada Sony 8 s / fusió de trens)'
    return 'Arc intermedi 3–6 R☉ (família del flat Sony a la V31)'


def iou(a, b):
    ix0, iy0, ix1, iy1 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, ix1 - ix0) * max(0, iy1 - iy0)
    if inter == 0:
        return 0.0
    return inter / ((a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter)


def main():
    rep = json.loads(Path(RUN.rebut('marks_inventory.json')).read_text()); assert 'annotated_sha256' in rep
    old = json.loads(OLD.read_text()); oldmarks = old['marks']
    catalog = []
    for row in rep['layers']:
        for m in row['marks']:
            m2 = dict(m, layer=row['name'], original_index=row['original_index'], family=family(row, m),
                      certainty_by_Pere='dubtos' if m['color'] == 'verd' else 'confirmat',
                      review_status='DUBTOS; no eliminar' if m['color'] == 'verd' else 'ARTEFACTE VIST PER PERE A LA V34; causa per mesurar', correction_applied=False)
            cand = [o for o in oldmarks if OLD2NEW.get(o['layer_index']) == row['index']]
            hits = [(o['id'], iou(m['bbox'], o['bbox']), float(np.hypot(o['center_xy'][0] - m['center_xy'][0], o['center_xy'][1] - m['center_xy'][1]))) for o in cand]
            hits = [h for h in hits if h[1] > 0 or h[2] < 150]
            m2['V33_overlap'] = [{'id': h[0], 'iou': h[1], 'dist_px': h[2]} for h in sorted(hits, key=lambda h: -h[1])]
            catalog.append(m2)
    # marques de la V31 sense cap correspondència a la V32 (a la mateixa capa)
    matched = {h['id'] for m in catalog for h in m['V33_overlap']}
    unmatched = [{'id': o['id'], 'layer': o['layer'], 'color': o['color'], 'family': o['family'], 'r': o['paint_radius_R_p05_p50_p95'], 'new_layer_index': OLD2NEW.get(o['layer_index'])} for o in oldmarks if o['id'] not in matched]
    layers = [{'index': r['index'], 'name': r['name'], 'original_index': r['original_index'], 'n_marks': len(r['marks']), 'color_counts': r['color_counts'], 'paint_pixels_by_color': r['paint_pixels_by_color'], 'detection': r['detection'], 'alpha_equal': r['alpha_equal'], 'mask_equal': r['mask_equal']} for r in rep['layers']]
    tot = {c: sum(m['color'] == c for m in catalog) for c in LEGEND}
    fam = {}
    for m in catalog:
        fam[m['family']] = fam.get(m['family'], 0) + 1
    write(RUN.rebut('review_catalog.json'), {'layers': layers, 'marks': catalog, 'totals_by_color': tot, 'totals_by_family': fam,
                                             'V33_marks_without_V34_counterpart': unmatched, 'n_V33_marks': len(oldmarks), 'n_V33_matched': len(matched),
                                             'old_to_new_layer_index': OLD2NEW, 'scope': '22 annotated layers; components are indexing units, not distinct defects; families by geometry only (causes measured separately)'})
    with Path(RUN.lliurable('CATALEG_MARQUES_V34.csv')).open('w', newline='') as f:
        w = csv.writer(f); w.writerow(['ID', 'capa', 'color', 'to_mode', 'criteri_Pere', 'familia_geometrica', 'bbox_xyxy', 'r_p05', 'r_mediana', 'r_p95', 'az_min', 'az_max', 'px_pintats', 'V33_ids_solapats'])
        for m in catalog:
            w.writerow([m['id'], m['layer'], m['color'], m['hue_mode'], m['certainty_by_Pere'], m['family'], m['bbox'], *[f'{t:.3f}' for t in m['paint_radius_R_p05_p50_p95']], *[f'{t:.1f}' for t in m['paint_azimuth_deg_min_max']], m['paint_pixels'], ';'.join(h['id'] for h in m['V33_overlap'])])
    # mapa global: totes les caixes sobre la base (cel/4) sense pintura
    base = Image.open(RUN.vista('L00_original_sencera.png')).convert('RGB'); sc = base.width / 10551
    d = ImageDraw.Draw(base)
    for m in catalog:
        x0, y0, x1, y1 = [v * sc for v in m['bbox']]; d.rectangle([x0, y0, x1, y1], outline=LEGEND[m['color']], width=2)
    for r_ in (1, 2, 3, 4, 5, 6, 8, 10):
        d.ellipse([(CX - r_ * RS) * sc, (CY - r_ * RS) * sc, (CX + r_ * RS) * sc, (CY + r_ * RS) * sc], outline=(90, 90, 90), width=1)
    y = 6
    for c, col in LEGEND.items():
        if tot[c]:
            d.rectangle([6, y, 22, y + 14], fill=col); d.text((28, y), f'{c}: {tot[c]}', fill='white', font=font(14)); y += 18
    base.save(RUN.vista('00_mapa_marques_sobre_base.png'))
    # histograma de radis per color
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(9, 3.2))
    for c, col in LEGEND.items():
        rs = [m['paint_radius_R_p05_p50_p95'][1] for m in catalog if m['color'] == c]
        if rs:
            ax.hist(rs, bins=np.arange(0.9, 14, 0.2), color=np.array(col) / 255, alpha=.6, label=f'{c} ({len(rs)})')
    for r_, lab in [(1.21, '0,5 s'), (1.33, '1 s'), (1.47, '2 s'), (1.96, '10 s'), (2.74, 'Sony 8 s'), (3.2, ''), (4.6, '')]:
        ax.axvline(r_, color='.4', lw=.6, ls='--'); ax.text(r_, ax.get_ylim()[1] * .95, lab, fontsize=7, rotation=90, va='top')
    ax.axvspan(3.2, 4.6, color='orange', alpha=.08); ax.set_xlabel('radi mitjà del traç [R☉]'); ax.set_ylabel('components'); ax.legend(fontsize=8)
    ax.set_title('Marques de Pere a la V33: radi mitjà per color (línies: fronteres HDR mesurades a la V31; franja: arcs del flat Sony)', fontsize=8)
    fig.tight_layout(); fig.savefig(RUN.vista('00_histograma_radis_per_color.png'), dpi=120)
    print('marques', len(catalog), tot, '| famílies', fam, '| V32 sense correspondència', len(unmatched), 'de', len(oldmarks), flush=True)


if __name__ == '__main__':
    main()
