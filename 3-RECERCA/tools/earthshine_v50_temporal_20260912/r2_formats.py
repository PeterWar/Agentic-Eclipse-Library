"""R2 · Prova de FORMATS de dades de l'earthshine (només lectura; escriu només R2_formats.json).

Obre tres fotogrames Vixen —curt 1/3200 s, mitjà 1/125 s, llarg 10 s— i per a cadascun imprimeix
forma, dtype, mínim/màxim/percentils de:
  · `path` i `weight` de B1_inputs.json (tessel·les lunars V43/V44, 1400×1400×3 i 1400×1400),
  · `native_vixen_{stem}.npz` de la V45 (g, q, variance; G1+G2 natiu sense matriu),
  · `A0_native_samples_{stem}.npz` (mostres verdes natives del limbe: g, raw_relative, q, valid…),
  · `A0_quincunx_{stem}.npz` i, si existeix, `D0_native_field_{stem}.npz`,
i la fracció de mostres natives amb raw_relative ≥ 0,85 en un anell de 10 px just dins del radi 455
(445–455) i just fora (455–465), també per 12 sectors d'azimut.

Verificació independent: obre el CR3 amb rawpy i comprova que raw_relative == (raw[native_y, native_x] − 512)/(16382 − 512).

⛔ No importa cap mòdul de la cadena (comu35 i companyia fan mkdir en importar-se): totes les constants són copiades i citades.
"""
import json, sys, time, hashlib
from pathlib import Path
import numpy as np

ROOT = Path('/Users/USUARI/Downloads/Eclipse 2026')
OUT = ROOT / 'output/earthshine_v50_temporal_20260912'
OUT.mkdir(parents=True, exist_ok=True)
B1 = ROOT / 'output/v45_earthshine_20260910/4-rebuts/B1_inputs.json'
NPSF = ROOT / 'output/earthshine_native_psf_20260911'
WIT = ROOT / 'output/earthshine_intermediate_witness_20260911'
EDGE = ROOT / 'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy'

# Constants copiades (font i línia):
PED_VIXEN, SAT_VIXEN = 512.0, 16382.0     # eclipse_determinista/comu.py TRENS['VIXEN'] (pedestal_dn, saturacio_dn)
PED_SONY, SAT_SONY = 512.0, 16383.0       # eclipse_determinista/comu.py TRENS['SONY']
SOSTRE, TERRA_DN = 0.85, 12.0             # eclipse_determinista/f2.py:27-28
CX, CY = 699.568111973117, 699.6475341408573   # earthshine_native_psf_20260911/native_common.py:6 (= MC − (X0,Y0) de comu44)
X0, Y0, N = 4677, 3077, 1400              # idem
RL_EFEM = 455.5018                        # comu44.py:15 (R_lluna_px de F1.2_sol_llenc.json)
STRICT = 0.85                             # b1_native.py:54 i a0_native_and_quincunx.py:46 (raw_relative < 0,85)

STEMS = {'curt_1_3200s': '572A2962', 'mitja_1_125s': '572A2969', 'llarg_10s': '572A2982'}


def stats(a, name):
    a = np.asarray(a)
    fin = np.isfinite(a) if a.dtype.kind == 'f' else np.ones(a.shape, bool)
    v = a[fin].astype(np.float64)
    d = dict(name=name, shape=list(a.shape), dtype=str(a.dtype), n=int(a.size), finite_frac=float(fin.mean()))
    if v.size:
        p = np.percentile(v, [0, 1, 5, 50, 95, 99, 100])
        d.update(min=float(p[0]), p1=float(p[1]), p5=float(p[2]), p50=float(p[3]), p95=float(p[4]), p99=float(p[5]), max=float(p[6]))
        if a.dtype.kind == 'f' or a.dtype.kind in 'iu':
            d['frac_gt0'] = float((v > 0).mean())
    return d


def sectors(phi, m_ring, m_flag, k=12):
    """fracció m_flag dins m_ring per k sectors d'azimut (angle des de +x, sentit de les y creixents)."""
    b = ((phi % (2 * np.pi)) * k / (2 * np.pi)).astype(int) % k
    out = []
    for i in range(k):
        s = m_ring & (b == i)
        out.append(dict(sector=i, az_deg=[i * 360 / k, (i + 1) * 360 / k], n=int(s.sum()), frac=float(m_flag[s].mean()) if s.any() else None))
    return out


def main():
    t0 = time.time()
    fr = {m['stem']: m for m in json.loads(B1.read_text())['frames']}
    a2 = {m['stem']: m for m in json.loads((NPSF / 'A2_all_native.json').read_text())['frames']}
    edge = np.load(EDGE)
    rep = dict(script=str(Path(__file__).resolve()), when_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), constants=dict(
        pedestal_vixen_dn=PED_VIXEN, saturacio_vixen_dn=SAT_VIXEN, span_vixen_dn=SAT_VIXEN - PED_VIXEN, pedestal_sony_dn=PED_SONY, saturacio_sony_dn=SAT_SONY,
        finestra_sostre=SOSTRE, finestra_terra_dn=TERRA_DN, strict_raw_relative_lt=STRICT, centre_local_xy=[CX, CY], roi_origen_llenc_xy=[X0, Y0], N=N, RL_efemeride_px=RL_EFEM,
        F4_edge_px=dict(n=int(len(edge)), min=float(edge.min()), max=float(edge.max()), mediana=float(np.median(edge)))), frames={})
    yy, xx = np.mgrid[:N, :N].astype(np.float64)
    RR = np.hypot(xx - CX, yy - CY); PHI = np.arctan2(yy - CY, xx - CX)
    ring_in = (RR >= 445) & (RR < 455); ring_out = (RR >= 455) & (RR < 465)
    for label, stem in STEMS.items():
        m = fr[stem]; r = dict(stem=stem, nom=m['nom'], exp_s=m['exp'], t_tren_s=m['t'], t_mid_C2_s=m['t_mid_C2'], grup=m['grup'], shift_px=m['shift'], regenerated=m['regenerated'], arrays={})
        print(f'\n===== {label}: {stem} · exp {m["exp"]:g} s · t_mid_C2 {m["t_mid_C2"]:.2f} s · shift {m["shift"]} =====', flush=True)
        # 1. path / weight (V43 o V44)
        P = np.load(m['path'], mmap_mode='r'); W = np.load(m['weight'], mmap_mode='r')
        r['path_file'] = m['path']; r['weight_file'] = m['weight']
        for c, cn in enumerate('RGB'):
            r['arrays'][f'path_{cn}'] = stats(P[..., c], f'path[...,{c}] ({cn}, sRGB lineal AM0, unitats DN/s calibrades)')
        r['arrays']['weight'] = stats(W, 'weight (Σ G1,G2 de finestra_v34·t·valid remostrejada ×disc; 0–2·t)')
        r['weight_max_over_2exp'] = float(np.max(W) / (2 * m['exp']))
        Wf = np.asarray(W); Gf = np.asarray(P[..., 1])
        r['path_G_finite_frac_in_disc_r_lt_440'] = float(np.isfinite(Gf[RR < 440]).mean())
        r['weight_gt0_frac_ring_445_455'] = float((Wf[ring_in] > 0).mean()); r['weight_gt0_frac_ring_455_465'] = float((Wf[ring_out] > 0).mean())
        r['weight_sectors_ring_445_455_frac_gt0'] = sectors(PHI, ring_in, Wf > 0)
        # 2. native V45
        z = np.load(m['native']['file'])
        r['native_file'] = m['native']['file']; r['native_keys'] = list(z.files)
        for k in z.files:
            r['arrays'][f'native_{k}'] = stats(z[k], f'native {k}')
        q = z['q']; r['native_q_max'] = float(q.max()); r['native_q_gt0_frac_ring_445_455'] = float((q[ring_in] > 0).mean()); r['native_q_gt0_frac_ring_455_465'] = float((q[ring_out] > 0).mean())
        r['native_q_gt0_frac_disc_r_lt_440'] = float((q[RR < 440] > 0).mean())
        # comprovació q = den/(2·exp): q1,q2 = pes de cada pla dividit per exp → q == (q1+q2)/2 ?
        r['native_q_equals_mean_q1_q2_maxabs'] = float(np.nanmax(np.abs(q - (z['q1'] + z['q2']) / 2)))
        # 3. A0 native samples
        ns = np.load(NPSF / f'A0_native_samples_{stem}.npz')
        r['native_samples_file'] = str(NPSF / f'A0_native_samples_{stem}.npz'); r['native_samples_keys'] = list(ns.files)
        for k in ns.files:
            if ns[k].ndim >= 1 and ns[k].size > 4:
                r['arrays'][f'A0samples_{k}'] = stats(ns[k], f'A0_native_samples {k}')
        J = ns['native_to_world']; r['native_to_world'] = J.tolist(); r['native_to_world_det'] = float(np.linalg.det(J)); r['native_to_world_rot_deg'] = float(np.degrees(np.arctan2(J[1, 0], J[0, 0])))
        x, y = ns['x'], ns['y']; rad = np.hypot(x - CX, y - CY); phi = np.arctan2(y - CY, x - CX)
        r['A0samples_radius_min_max'] = [float(rad.min()), float(rad.max())]
        rr = ns['raw_relative']; valid = ns['valid']; gp = ns['green_plane']
        r['A0samples_green_plane_counts'] = {int(k): int(v) for k, v in zip(*np.unique(gp, return_counts=True))}
        # coherència world = origin + J@native (origen des de la primera mostra)
        origin = np.array([x[0], y[0]]) - J @ np.array([ns['native_x'][0], ns['native_y'][0]])
        pred = (np.stack([ns['native_x'], ns['native_y']], 1) @ J.T) + origin
        r['A0samples_world_from_native_maxabs_err_px'] = float(np.max(np.abs(pred - np.stack([x, y], 1))))
        # paritat CFA: (native_x + native_y) senar → verd
        r['A0samples_parity_x_plus_y_odd_frac'] = float(((ns['native_x'] + ns['native_y']) % 2 == 1).mean())
        r['A0samples_valid_equals_rr_lt_085_frac'] = float((valid == (rr < STRICT)).mean())
        ri = (rad >= 445) & (rad < 455); ro = (rad >= 455) & (rad < 465)
        sat = rr >= STRICT
        r['A0samples_frac_rr_ge_085_ring_445_455'] = float(sat[ri].mean()); r['A0samples_frac_rr_ge_085_ring_455_465'] = float(sat[ro].mean())
        r['A0samples_n_ring_445_455'] = int(ri.sum()); r['A0samples_n_ring_455_465'] = int(ro.sum())
        r['A0samples_frac_rr_ge_085_sectors_ring_445_455'] = sectors(phi, ri, sat)
        r['A0samples_frac_rr_ge_085_sectors_ring_455_465'] = sectors(phi, ro, sat)
        # perfil radial de la fracció saturada, 2 px, 415–495
        prof = []
        for a in range(415, 495, 2):
            s = (rad >= a) & (rad < a + 2); prof.append([a, int(s.sum()), float(sat[s].mean()) if s.any() else None, float(np.median(rr[s])) if s.any() else None])
        r['A0samples_profile_r_n_fracsat_medrr'] = prof
        # factor de conversió g → raw_relative: rr·span/(g·exp) (≈ flat/(k·field), sense dark ni offset)
        gg = ns['g']; ok = valid & (rr > 0.05) & (gg > 0)
        if ok.any():
            fac = rr[ok] * (SAT_VIXEN - PED_VIXEN) / (gg[ok] * m['exp']); r['A0samples_rr_span_over_g_exp_median_p5_p95'] = [float(np.median(fac)), float(np.percentile(fac, 5)), float(np.percentile(fac, 95))]
        else:
            r['A0samples_rr_span_over_g_exp_median_p5_p95'] = None
        # 4. A0_quincunx
        qz = np.load(NPSF / f'A0_quincunx_{stem}.npz'); r['quincunx_keys'] = list(qz.files)
        for k in qz.files:
            r['arrays'][f'A0quincunx_{k}'] = stats(qz[k], f'A0_quincunx {k}')
        # 5. D0 native field (si hi és)
        d0 = WIT / f'D0_native_field_{stem}.npz'
        if d0.exists():
            dz = np.load(d0); r['D0_file'] = str(d0); r['D0_keys'] = list(dz.files); r['D0_u0_v0'] = [int(dz['u0']), int(dz['v0'])]; r['D0_world_origin'] = dz['world_origin'].tolist()
            for k in ('g', 'variance', 'q'):
                r['arrays'][f'D0_{k}'] = stats(dz[k], f'D0_native_field {k}')
            r['arrays']['D0_valid'] = dict(name='D0 valid', shape=list(dz['valid'].shape), dtype=str(dz['valid'].dtype), frac_true=float(dz['valid'].mean()))
            V, U = np.mgrid[:dz['g'].shape[0], :dz['g'].shape[1]]; U = U + int(dz['u0']); V = V + int(dz['v0']); nx = 1 + U + V; ny = U - V
            wxy = np.stack([nx.ravel(), ny.ravel()], 1) @ dz['native_to_world'].T + dz['world_origin']
            radD = np.hypot(wxy[:, 0] - CX, wxy[:, 1] - CY).reshape(nx.shape); vD = dz['valid']
            r['D0_valid_frac_ring_445_455'] = float(vD[(radD >= 445) & (radD < 455)].mean()); r['D0_valid_frac_ring_455_465'] = float(vD[(radD >= 455) & (radD < 465)].mean())
            # identitat amb A0 samples (com d0_native_fields.py:23-25)
            ou = ((ns['native_x'] + ns['native_y'] - 1) // 2 - int(dz['u0'])).astype(int); ov = ((ns['native_x'] - ns['native_y'] - 1) // 2 - int(dz['v0'])).astype(int)
            r['D0_identity_with_A0samples'] = dict(g=bool(np.array_equal(dz['g'][ov, ou], ns['g'], equal_nan=True)), valid=bool(np.array_equal(dz['valid'][ov, ou], ns['valid'])), world_xy_maxabs=float(np.max(np.abs(wxy.reshape(nx.shape + (2,))[ov, ou] - np.stack([x, y], 1)))))
        else:
            r['D0_file'] = None
        # 6. verificació independent amb el CR3
        rp = Path(a2[stem]['raw_path'])
        try:
            import rawpy
            with rawpy.imread(str(rp)) as raw:
                RAW = raw.raw_image.astype(np.float64); r['raw_shape'] = list(RAW.shape); r['raw_black_level_per_channel_libraw'] = [int(v) for v in raw.black_level_per_channel]; r['raw_white_level_libraw'] = int(raw.white_level)
                r['raw_max_dn'] = float(RAW.max()); r['raw_n_at_16382'] = int((RAW == 16382).sum()); r['raw_n_at_16383'] = int((RAW == 16383).sum()); r['raw_n_gt_16382'] = int((RAW > 16382).sum())
            rr_chk = (RAW[ns['native_y'], ns['native_x']] - PED_VIXEN) / (SAT_VIXEN - PED_VIXEN)
            r['raw_relative_check_maxabs_err'] = float(np.max(np.abs(rr_chk - rr)))
            r['raw_relative_definition_verified'] = bool(r['raw_relative_check_maxabs_err'] < 1e-9)
            r['raw_sha256_matches_A2'] = hashlib.file_digest(rp.open('rb'), 'sha256').hexdigest() == a2[stem]['raw_sha256']
        except Exception as e:
            r['raw_check_error'] = repr(e)
        rep['frames'][label] = r
        # impressió compacta
        for k in ('path_G', 'weight', 'native_g', 'native_q', 'native_variance', 'A0samples_g', 'A0samples_raw_relative', 'A0samples_q', 'A0quincunx_g', 'D0_g'):
            if k in r['arrays']:
                s = r['arrays'][k]; print(f"  {k:22s} shape {s['shape']} {s['dtype']:8s} finite {s['finite_frac']*100:6.2f}%  min {s.get('min', float('nan')):.5g}  p50 {s.get('p50', float('nan')):.5g}  max {s.get('max', float('nan')):.5g}")
        print(f"  raw_relative ≥ 0,85: anell 445–455 {r['A0samples_frac_rr_ge_085_ring_445_455']*100:.2f} % (n {r['A0samples_n_ring_445_455']}) · anell 455–465 {r['A0samples_frac_rr_ge_085_ring_455_465']*100:.2f} % (n {r['A0samples_n_ring_455_465']})")
        print(f"  weight>0: anell 445–455 {r['weight_gt0_frac_ring_445_455']*100:.2f} % · 455–465 {r['weight_gt0_frac_ring_455_465']*100:.2f} % · weight max/(2·exp) {r['weight_max_over_2exp']:.4f}")
        print(f"  raw_relative verificat contra el CR3: {r.get('raw_relative_definition_verified')} (err {r.get('raw_relative_check_maxabs_err')}); libraw black {r.get('raw_black_level_per_channel_libraw')} white {r.get('raw_white_level_libraw')} · raw max {r.get('raw_max_dn')} · n==16382 {r.get('raw_n_at_16382')} · n==16383 {r.get('raw_n_at_16383')}")
        print(f"  factor rr·span/(g·exp) mediana/p5/p95: {r['A0samples_rr_span_over_g_exp_median_p5_p95']}")
    rep['seconds'] = time.time() - t0
    (OUT / 'R2_formats.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1) + '\n')
    print('\nDESAT', OUT / 'R2_formats.json', f'{rep["seconds"]:.1f} s', flush=True)


if __name__ == '__main__':
    main()
