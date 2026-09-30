"""A3 (V35) · La vora del suport de l'apuntament A de la Sony dins del camp de B (nou a la V34: fusió A+B per variància).
Per distància amb signe a la vora de A (+ dins de A), a la zona on B existeix (r > 2,5 R☉, fora del ghost):
fracció A, desajust de nivell ln(A_corr/B) σ64, graó de la fusió ln(S_fusió/B) σ64, gra fi/mitjà de la fusió i de B sola.
Geometria de la vora de A (orientació) i mapa amb les caixes de les marques verticals del P04 (L09-M03/M05/M06)."""
import sys; sys.path.insert(0, '/Users/USUARI/Downloads/Eclipse 2026/research/tools/v34_20260907')
from comu34 import *
from PIL import Image, ImageDraw
CAU35 = Path(__file__).resolve().parent / 'cau'; OUT35 = ROOT / 'output/v35_20260908'; REB35 = OUT35 / '4-rebuts'; VIS35 = OUT35 / 'lliurables/vistes'


def nsmooth(a, w, s):
    return gauss(a * w, s) / np.maximum(gauss(w, s), 1e-6)


def main():
    r, t = coords(); y, x = np.ogrid[:H, :W]
    A = np.load(CAU34 / 'sony_A_corr_v34.npy', mmap_mode='r'); B = np.load(CAU34 / 'sony_B_total_v34.npy', mmap_mode='r'); S = np.load(CAU34 / 'sony_corrected_total_v34.npy', mmap_mode='r')
    pa = np.load(CAUF / 'sony_A_weights.npy', mmap_mode='r'); pb = np.load(CAUF / 'sony_B_weights.npy', mmap_mode='r'); fA = np.load(CAU34 / 'sony_fA_v34.npy')
    AG = np.asarray(A[..., 1]); BG = np.asarray(B[..., 1]); SG = np.asarray(S[..., 1])
    ma = np.isfinite(AG) & (AG > 0) & (np.asarray(pa[..., 1]) > 0); mb = np.isfinite(BG) & (BG > 0) & (np.asarray(pb[..., 1]) > 0)
    maf = ma | (r < 1.2 * RS); mbf = mb | (r < 1.2 * RS)
    da_in = cv2.distanceTransform(maf.astype(np.uint8), cv2.DIST_L2, 5); da_out = cv2.distanceTransform((~maf).astype(np.uint8), cv2.DIST_L2, 5); sd = np.where(maf, da_in, -da_out).astype(np.float32)
    db_in = cv2.distanceTransform(mbf.astype(np.uint8), cv2.DIST_L2, 5)
    dist = np.hypot(x - GHOST_XY[0], y - GHOST_XY[1]).astype(np.float32)
    edgeA = maf & (da_in <= 1.5) & mb; edgeB = mbf & (db_in <= 1.5) & ma
    rep = {'vora_A_dins_B': {'px': int(edgeA.sum()), 'r_p05_p50_p95': [float(np.percentile(r[edgeA] / RS, q)) for q in (5, 50, 95)], 'x_p05_p50_p95': [float(np.percentile(np.broadcast_to(x, (H, W))[edgeA], q)) for q in (5, 50, 95)], 'y_p05_p50_p95': [float(np.percentile(np.broadcast_to(y, (H, W))[edgeA], q)) for q in (5, 50, 95)]},
           'vora_B_dins_A': {'px': int(edgeB.sum()), 'r_p05_p50_p95': [float(np.percentile(r[edgeB] / RS, q)) for q in (5, 50, 95)] if edgeB.any() else None}}
    # orientació de la vora A: histograma de l'angle del gradient de maf (suavitzat)
    g = gauss(maf.astype(np.float32), 8); gy, gx = np.gradient(g); ang = np.degrees(np.arctan2(gy, gx))[edgeA]; hist, edges = np.histogram(ang, bins=36, range=(-180, 180))
    rep['vora_A_orientacio_deg_hist'] = {'bins': edges.tolist(), 'counts': hist.tolist()}; log(f"vora A: {rep['vora_A_dins_B']} · pics d'orientació {edges[np.argsort(hist)[-4:]]}")
    both = ma & mb; w = both.astype(np.float32)
    mis = nsmooth(np.where(both, np.log(np.maximum(AG, 1e-9) / np.maximum(BG, 1e-9)), 0).astype(np.float32), w, 64)
    LS = np.where(mb & (SG > 0), np.log(np.maximum(SG, 1e-9)), 0).astype(np.float32); LB = np.where(mb, np.log(np.maximum(BG, 1e-9)), 0).astype(np.float32); wb = mb.astype(np.float32)
    step64 = nsmooth(np.where(mb, LS - LB, 0).astype(np.float32), wb, 64)
    fineS = np.where(mb, nsmooth(LS, wb, 1.5) - nsmooth(LS, wb, 3.0), 0); fineB = np.where(mb, nsmooth(LB, wb, 1.5) - nsmooth(LB, wb, 3.0), 0)
    midS = np.where(mb, nsmooth(LS, wb, 8) - nsmooth(LS, wb, 16), 0)
    zone = mb & (r > 2.5 * RS) & (dist > 320); rows = []
    for b0 in list(range(-600, 0, 100)) + list(range(0, 1300, 100)):
        k = zone & (sd >= b0) & (sd < b0 + 100)
        if k.sum() < 500:
            continue
        kin = k & ma
        rows.append({'dist_px': [b0, b0 + 100], 'n': int(k.sum()), 'fA_p50': float(np.median(fA[k])), 'mismatch_AB_pct_p50': float(100 * np.median(mis[kin])) if kin.sum() > 100 else None,
                     'mismatch_AB_pct_p10_p90': [float(100 * np.percentile(mis[kin], q)) for q in (10, 90)] if kin.sum() > 100 else None, 'grao_fusio_vs_B_pct': float(100 * np.median(step64[k])),
                     'gra_fi_fusio_pct': float(100 * np.sqrt(np.mean(fineS[k] ** 2))), 'gra_fi_B_pct': float(100 * np.sqrt(np.mean(fineB[k] ** 2))), 'gra_mitja_fusio_pct': float(100 * np.sqrt(np.mean(midS[k] ** 2)))})
    rep['perfil_vora_A'] = rows
    log(' | '.join(f"{z['dist_px'][0]}: fA {z['fA_p50']:.2f} mis {z['mismatch_AB_pct_p50'] if z['mismatch_AB_pct_p50'] is not None else float('nan'):+.2f}% graó {z['grao_fusio_vs_B_pct']:+.2f}% gra {z['gra_fi_fusio_pct']:.3f} (B {z['gra_fi_B_pct']:.3f})" for z in rows))
    np.save(CAU35 / 'mismatchAB64_v34.npy', mis)
    # mapa 1/6: graó de la fusió A+B (±0,5 %) amb la vora A (vermell), la vora B (blau) i les caixes de les marques verticals del P04
    sc = 6; small = lambda a: cv2.resize(a, (W // sc, H // sc), interpolation=cv2.INTER_AREA)
    a = small(np.nan_to_num(np.where(mb, step64, 0))); img = np.clip(0.5 + a / 0.01, 0, 1); rgb = np.repeat((img * 255).astype(np.uint8)[..., None], 3, axis=2)
    rgb[small(edgeA.astype(np.float32)) > 0.05] = (255, 60, 60); rgb[small(edgeB.astype(np.float32)) > 0.05] = (60, 160, 255)
    im = Image.fromarray(rgb); d = ImageDraw.Draw(im)
    cat = json.loads((ROOT / 'output/revisio_marques_v34_20260908/4-rebuts/review_catalog.json').read_text())['marks']
    for mk in cat:
        if mk['id'] in ('L09-M03', 'L09-M05', 'L09-M06', 'L09-M02', 'L09-M04', 'L10-M02', 'L10-M17'):
            x0, y0, x1, y1 = [v / sc for v in mk['bbox']]; d.rectangle([x0, y0, x1, y1], outline=(60, 220, 60), width=1); d.text((x0, y0 - 10), mk['id'], fill=(60, 220, 60))
    im.save(VIS35 / 'A3_grao_fusio_AB_sigma64_pm05pct_vora_A_vermell_marques_P04_verd.png')
    savejson(REB35 / 'A3_vora_sonyA.json', rep); log('A3 fet')


if __name__ == '__main__':
    main()
