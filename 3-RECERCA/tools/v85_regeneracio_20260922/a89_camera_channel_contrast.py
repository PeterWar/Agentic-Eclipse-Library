"""Frozen sparse diagnostic: camera-green versus matrix-converted RGB-green.

Reuse the exact a71 train composition on the existing 4047 lattice points.
No source raster, color matrix, calibration, holdout, or PSB is modified.
"""
import a71_bias_component as base
from a4_sources import *

OUT = O / 'camera_channels_R03'

def measure(v):
    pix, inv, corners, coeff = [v[k] for k in ['pix', 'inv', 'corners', 'coeff']]
    den, matrix, gain, corrected = [v[k] for k in ['den', 'matrix', 'gain', 'corrected']]
    cam = np.where(den > 0, (v['ncO'] + v['ncT']) / np.maximum(den, 1e-20), np.nan).astype(np.float32)
    terms = (cam * matrix[1] * gain[1]).astype(np.float32)
    direct = terms.sum(axis=-1, dtype=np.float32)
    finite = np.isfinite(direct) & np.isfinite(corrected[:, 1])
    maxerr = float(np.max(abs(direct[finite] - corrected[finite, 1])))
    scale = float(np.max(abs(corrected[finite, 1])))
    assert maxerr <= max(1e-12, scale * 1e-6)

    def interp(a):
        return (a[inv].reshape(corners.shape[:-1]) * coeff).sum(axis=-1)

    positive_g = np.isfinite(cam[:, 1]) & (cam[:, 1] > 0)
    good = v['good'] & (interp(positive_g.astype(float)) > .999).all(axis=0)
    comp, aw = v['comp'], v['aw']
    rgb_log = np.log(np.where(v['finite'], corrected[:, 1], 1)).astype(float)
    cam_log = np.log(np.where(positive_g, cam[:, 1], 1)).astype(float)
    rgb_s, cam_s = interp(rgb_log), interp(cam_log)
    rgb_c = rgb_s[0] - .5 * (rgb_s[1] + rgb_s[2])
    cam_c = cam_s[0] - .5 * (cam_s[1] + cam_s[2])
    delta = rgb_c - cam_c
    safe_g = np.where(v['finite'], corrected[:, 1], np.nan)
    shares = terms / safe_g[:, None]
    condition = abs(terms).sum(axis=-1) / safe_g

    def stats(a, w):
        return {'mean': float(np.average(a, weights=w)),
                'rms': float(np.sqrt(np.average(a * a, weights=w))),
                'mean_abs': float(np.average(abs(a), weights=w))}

    rows = []
    for k in [0, *sorted(set(comp))]:
        selected = good if k == 0 else good & (comp == k)
        if selected.sum() < 10:
            continue
        weight = aw[selected]
        row = {'component': int(k), 'n': int(selected.sum()),
               'RGB_G': stats(rgb_c[selected], weight),
               'camera_G': stats(cam_c[selected], weight),
               'matrix_delta': stats(delta[selected], weight),
               'weighted_term_shares_center_outer_inner': {},
               'weighted_cancellation_condition_center_outer_inner':
                   np.average(interp(condition)[:, selected], weights=weight, axis=1).tolist()}
        for j, label in enumerate(['camera_R', 'camera_G', 'camera_B']):
            row['weighted_term_shares_center_outer_inner'][label] = np.average(
                interp(shares[:, j])[:, selected], weights=weight, axis=1).tolist()
            ok = np.isfinite(cam[:, j]) & (cam[:, j] > 0)
            keep = selected & (interp(ok.astype(float)) > .999).all(axis=0)
            s = interp(np.log(np.where(ok, cam[:, j], 1)).astype(float))
            c = s[0] - .5 * (s[1] + s[2])
            row[label + '_positive_log'] = {'n': int(keep.sum()), **stats(c[keep], aw[keep])} if keep.any() else {'n': 0}
        rows.append(row)
    assert len(pix) == 4047 and len(v['train']) == 61
    save(OUT / 'QA.json', {
        'matrix': matrix.tolist(), 'gain': gain.tolist(),
        'RGB_G_linear_coefficients': (matrix[1] * gain[1]).tolist(),
        'additive_reconstruction_max_abs': maxerr,
        'sparse_points': len(pix), 'original_good_triplets': int(v['good'].sum()),
        'common_cameraG_RGBG_triplets': int(good.sum()),
        'rows': rows,
        'limits': ['Full train Vixen B2 plus S4 tiers counterfactual, not D4 splice/Sony/star-subtracted source',
                   'Camera channels are calibrated color-separated source estimates, not untouched sensor samples',
                   'Source contrast can include real structure; smaller absolute contrast is not an acceptance criterion',
                   'No camera-green full-canvas filters or PSB generated; external comparison pending only if hypothesis warrants it']
    })
    np.savez(OUT / 'SAMPLES.npz', pixels=pix, camera=cam, RGB=corrected,
             good=good, components=comp, weights=aw, RGB_G_C=rgb_c, camera_G_C=cam_c)
    save(OUT / 'COMPLETE.json', {'calculation_integrity': True, 'scientific_acceptance': None,
                              'no_reserved_N_read': True, 'no_native_write': True,
                              'samples_sha256': sha(OUT / 'SAMPLES.npz')})
    print('CAMERA_CHANNEL_CONTRAST', [(row['component'], row['RGB_G']['mean'], row['camera_G']['mean']) for row in rows])

def main():
    OUT.mkdir()
    save(OUT / 'FROZEN_TEST.json', {
        'hypothesis': 'Negative color-matrix terms may amplify source normal contrast near the lunar limb',
        'producer': 'a71 exact sparse train source composition up to its final output assignment',
        'producer_sha256': sha(Path(base.__file__)),
        'frozen': '61 train frames, original N/W/D/B2/S4 weights, same 902 h4 marked triplets and CFA-to-RGB matrix/gain',
        'primary': 'common-support calibrated camera G versus transformed RGB G, log normal contrast',
        'secondary': 'signed linear matrix term shares at center and plus/minus4 neighbors; cancellation condition',
        'acceptance': 'causal diagnostic only, no automatic promotion from reduced contrast',
        'heldout_N_excluded': 6
    })
    tree = ast.parse(Path(base.__file__).read_text())
    fn = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == 'main')
    stop = next(i for i, x in enumerate(fn.body) if isinstance(x, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'out' for t in x.targets))
    fn.body = fn.body[:stop] + ast.parse('measure(locals())').body
    ast.fix_missing_locations(fn)
    ns = dict(vars(base), measure=measure)
    exec(compile(ast.Module(body=[fn], type_ignores=[]), str(base.__file__) + ' sparse prefix', 'exec'), ns)
    ns['main']()

if __name__ == '__main__':
    guard()
    main()
