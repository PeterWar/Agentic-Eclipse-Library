import sys, json, numpy as np, rawpy, os

def frame_stats(path):
    with rawpy.imread(path) as raw:
        v = raw.raw_image_visible.astype(np.float64)
        c = raw.raw_colors_visible
        out = {}
        out['file'] = os.path.basename(path)
        out['shape'] = list(v.shape)
        out['median'] = float(np.median(v))
        out['mean'] = float(v.mean())
        out['std'] = float(v.std())
        out['p99'] = float(np.percentile(v, 99))
        out['p999'] = float(np.percentile(v, 99.9))
        out['max'] = float(v.max())
        out['n_gt1000'] = int((v > 1000).sum())
        out['n_gt600'] = int((v > 600).sum())
        ped = {}
        st = {}
        for ci, nm in enumerate(['R','G1','B','G2']):
            m = c == ci
            if m.sum() == 0: continue
            ped[nm] = float(np.median(v[m]))
            st[nm] = float(v[m].std())
        out['pedestal'] = ped
        out['std_ch'] = st
        # quadrant medians (gradient probe) 4x4 tiles
        h, w = v.shape
        tiles = []
        for i in range(4):
            row = []
            for j in range(4):
                row.append(float(np.median(v[i*h//4:(i+1)*h//4, j*w//4:(j+1)*w//4])))
            tiles.append(row)
        out['tiles_med'] = tiles
        # same for mean (light shows in mean more)
        tilesm = []
        for i in range(4):
            row = []
            for j in range(4):
                row.append(round(float(v[i*h//4:(i+1)*h//4, j*w//4:(j+1)*w//4].mean()),3))
            tilesm.append(row)
        out['tiles_mean'] = tilesm
    return out

if __name__ == '__main__':
    res = [frame_stats(p) for p in sys.argv[2:]]
    with open(sys.argv[1],'w') as f: json.dump(res, f, indent=1)
    for r in res:
        print(f"{r['file']}  med={r['median']:.1f} mean={r['mean']:.3f} std={r['std']:.3f} p99={r['p99']:.0f} p99.9={r['p999']:.0f} max={r['max']:.0f} n>1000={r['n_gt1000']} ped R/G1/B/G2={r['pedestal']['R']:.0f}/{r['pedestal']['G1']:.0f}/{r['pedestal']['B']:.0f}/{r['pedestal']['G2']:.0f}")
