"""A1 (V35) · El contorn del FOV Vixen dins del camp Sony, mesurat a la font de la V34.
Per a cada distància (amb signe) a la vora del suport Vixen: pes Vixen, desajust de nivell ln(V/(S·ρ)) per canal
(σ64), graó de nivell que la fusió imprimeix (ln F − ln(S·ρ)), gra fi (DoG 1,5/3) i mitjà (σ8−σ16) de la base fusionada.
També: trampa del forat lunar a dv (pes Vixen per anell interior) i geometria de la vora (radi, azimut)."""
import sys; sys.path.insert(0, '/Users/USUARI/Downloads/Eclipse 2026/research/tools/v34_20260907')
from comu34 import *
from PIL import Image
CAU35 = Path(__file__).resolve().parent / 'cau'; CAU35.mkdir(exist_ok=True)
OUT35 = ROOT / 'output/v35_20260908'; REB35 = OUT35 / '4-rebuts'; VIS35 = OUT35 / 'lliurables/vistes'


def nsmooth(a, w, s):
    return gauss(a * w, s) / np.maximum(gauss(w, s), 1e-6)


def main():
    r, t = coords(); mv0 = np.load(CAUF / 'vixen_support.npy'); ms0 = np.load(CAUF / 'sony_support.npy')
    V = np.load(CAU34 / 'vixen_total_v34.npy', mmap_mode='r'); S = np.load(CAU34 / 'sony_corrected_total_v34.npy', mmap_mode='r'); RHO = np.load(CAU34 / 'rho_v34.npy', mmap_mode='r')
    F = np.load(CAU34 / 'fusion_total_v34.npy', mmap_mode='r'); wv = np.load(CAU34 / 'weight_vixen_v34.npy'); m = np.load(CAU34 / 'support_v34.npy')
    VG = np.asarray(V[..., 1]); SG = np.asarray(S[..., 1]); FG = np.asarray(F[..., 1])
    mv = mv0 & np.isfinite(VG) & (VG > 0); ms = ms0 & np.isfinite(SG) & (SG > 0)
    rep = {}
    # 1. trampa del forat lunar: píxels del suport Vixen sense dada dins d'1,05 R☉ i pes Vixen per anell interior
    hole = mv0 & ~mv; rep['forat_lunar'] = {'px_suport_sense_dada_r<1.05': int((hole & (r < 1.05 * RS)).sum()), 'px_suport_sense_dada_total': int(hole.sum()),
                                            'r_p50_p99_forat': [float(np.percentile(r[hole] / RS, q)) for q in (50, 99)] if hole.any() else None}
    prof_in = []
    for a in np.arange(1.0, 2.0, 0.1):
        k = ms & mv & (r >= a * RS) & (r < (a + 0.1) * RS)
        prof_in.append({'r': round(float(a), 2), 'n': int(k.sum()), 'wv_min': float(wv[k].min()) if k.any() else None, 'wv_p05': float(np.percentile(wv[k], 5)) if k.any() else None, 'wv_p50': float(np.median(wv[k])) if k.any() else None})
    rep['pes_vixen_interior'] = prof_in; log('interior: ' + str(prof_in[:4]))
    # 2. geometria de la vora Vixen (suport ple, sense forat) i de la vora Sony
    mvf = mv | (r < 1.6 * RS); msf = ms | (r < 1.6 * RS)
    dv_in = cv2.distanceTransform(mvf.astype(np.uint8), cv2.DIST_L2, 5); dv_out = cv2.distanceTransform((~mvf).astype(np.uint8), cv2.DIST_L2, 5)
    sd = np.where(mvf, dv_in, -dv_out).astype(np.float32)          # distància amb signe a la vora Vixen (+ dins)
    edge = mvf & (dv_in <= 1.5) & ms
    rep['vora_vixen'] = {'r_min_p05_p50_p95_max': [float(np.percentile(r[edge] / RS, q)) for q in (0, 5, 50, 95, 100)], 'px': int(edge.sum())}
    ds_in = cv2.distanceTransform(msf.astype(np.uint8), cv2.DIST_L2, 5); edge_s = msf & (ds_in <= 1.5) & mv
    rep['vora_sony_dins_vixen'] = {'r_p05_p50_p95': [float(np.percentile(r[edge_s] / RS, q)) for q in (5, 50, 95)] if edge_s.any() else None, 'px': int(edge_s.sum())}
    log(f"vora Vixen r {rep['vora_vixen']} · vora Sony dins Vixen {rep['vora_sony_dins_vixen']}")
    # 3. desajust de nivell per canal a la vora (σ64), dins del suport Vixen, r > 2,65
    both = mv & ms; w = both.astype(np.float32); mis = {}
    for c, nm in enumerate('RGB'):
        v = np.asarray(V[..., c]); s = np.asarray(S[..., c]) * np.asarray(RHO[..., c])
        d = np.where(both, np.log(np.maximum(v, 1e-9) / np.maximum(s, 1e-9)), 0).astype(np.float32); d64 = nsmooth(d, w, 64)
        mis[nm] = d64; del v, s, d
        np.save(CAU35 / f'mismatch64_{nm}_v34.npy', d64)
    # 4. perfils contra la distància amb signe a la vora (fora del ρ-fit: r > 4; i 2,65–4)
    L = np.where(m & (FG > 0), np.log(np.maximum(FG, 1e-9)), 0).astype(np.float32); wm = (m & (FG > 0)).astype(np.float32)
    fine = np.where(m, nsmooth(L, wm, 1.5) - nsmooth(L, wm, 3.0), 0); mid = np.where(m, nsmooth(L, wm, 8) - nsmooth(L, wm, 16), 0)
    Sp = np.where(ms, np.log(np.maximum(SG * np.asarray(RHO[..., 1]), 1e-9)), 0).astype(np.float32)
    step = np.where(ms & m, L - Sp, 0).astype(np.float32); step64 = nsmooth(step, (ms & m).astype(np.float32), 64)
    bins = list(range(-800, 0, 100)) + list(range(0, 1300, 100))
    for zone_name, zone in (('r>4', r > 4 * RS), ('2.65<r<4', (r > 2.65 * RS) & (r < 4 * RS))):
        rows = []
        for b0 in bins:
            k = ms & zone & (sd >= b0) & (sd < b0 + 100) & (r > 1.6 * RS)
            if k.sum() < 500:
                continue
            kin = k & mv
            rows.append({'dist_px': [b0, b0 + 100], 'n': int(k.sum()), 'wv_p50': float(np.median(wv[k])),
                         'mismatch_pct_R_G_B': [float(100 * np.median(mis[nm][kin])) if kin.sum() > 100 else None for nm in 'RGB'],
                         'mismatch_G_p10_p90_pct': [float(100 * np.percentile(mis['G'][kin], q)) for q in (10, 90)] if kin.sum() > 100 else None,
                         'grao_fusio_vs_sony_pct': float(100 * np.median(step64[k])), 'gra_fi_pct': float(100 * np.sqrt(np.mean(fine[k] ** 2))), 'gra_mitja_pct': float(100 * np.sqrt(np.mean(mid[k] ** 2)))})
        rep[f'perfil_vora_{zone_name}'] = rows
        log(zone_name + ': ' + ' | '.join(f"{z['dist_px'][0]}: wv {z['wv_p50']:.2f} mis {z['mismatch_pct_R_G_B'][1] if z['mismatch_pct_R_G_B'][1] is not None else float('nan'):+.2f}% graó {z['grao_fusio_vs_sony_pct']:+.2f}% gra {z['gra_fi_pct']:.3f}/{z['gra_mitja_pct']:.3f}" for z in rows))
    # 5. mapa del desajust G (σ64) i del graó, a 1/6, amb la vora Vixen dibuixada
    sc = 6; small = lambda a: cv2.resize(a, (W // sc, H // sc), interpolation=cv2.INTER_AREA)
    for nm, arr, lim in (('mismatch_G', np.where(both, mis['G'], np.nan), 0.02), ('grao_fusio', np.where(ms & m, step64, np.nan), 0.01)):
        a = small(np.nan_to_num(arr, nan=0)); img = np.clip(0.5 + a / (2 * lim), 0, 1); rgb = np.repeat((img * 255).astype(np.uint8)[..., None], 3, axis=2)
        e = small(edge.astype(np.float32)) > 0.05; rgb[e] = (255, 60, 60); es = small(edge_s.astype(np.float32)) > 0.05; rgb[es] = (60, 160, 255)
        for rr in (2.65, 4, 6, 8):
            cv2.circle(rgb, (int(CX / sc), int(CY / sc)), int(rr * RS / sc), (80, 200, 80), 1)
        Image.fromarray(rgb).save(VIS35 / f'A1_{nm}_sigma64_pm{lim*100:.0f}pct_vora_vixen_vermell.png')
    rep['vistes'] = 'A1_mismatch_G_sigma64 (±2 %: gris = 0), A1_grao_fusio (±1 %); vora Vixen en vermell, vora Sony en blau; cercles 2,65/4/6/8 R☉'
    savejson(REB35 / 'A1_vora_vixen.json', rep); log('A1 fet')


if __name__ == '__main__':
    main()
