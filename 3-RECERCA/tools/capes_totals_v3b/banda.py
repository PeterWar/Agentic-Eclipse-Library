"""Banda d'artefacte d'apilat al limbe: geometria + mesura al ràster (canal G).
Per capa: (1) extensió de la banda (fracció de pes de la referència > 1/N) en píxels des del centre lunar, per sector;
(2) salt de nivell a la frontera de la banda (mitjana de G 3-7 px dins vs 3-7 px fora, sobre el perfil local) per sector de 15°;
(3) soroll: desviació del residu passa-alt (G - gauss σ3) dins la banda contra fora, al mateix radi lunar."""
import json, sys, numpy as np
from scipy import ndimage as ndi
from geom import *
def mesura(i):
    G = np.load(f'{V2B}/src_id{i}_G.npy', mmap_mode='r')
    e = ELL[str(i)]; cx, cy = e['cx'], e['cy']
    x0, y0 = int(cx-560), int(cy-560); S = 1120
    img = np.asarray(G[y0:y0+S, x0:x0+S], np.float32) / 65535.
    xx, yy = grid(y0, y0+S, x0, x0+S)
    F, N = ref_fraction(i, xx, yy)
    d = d_ell(i, xx, yy); Rm = R_moon(i)
    dref = np.hypot(xx-cx, yy-cy)
    ref, cs = member_centres(i)
    az = np.degrees(np.arctan2(-(yy-cy), xx-cx)) % 360
    banda = F > 1.0/N + 1e-3
    # 1. extensió radial de la banda per sector de 15°
    ext = {}
    for s0 in range(0, 360, 15):
        m = banda & (az >= s0) & (az < s0+15)
        ext[s0] = float(dref[m].max() - Rm) if m.any() else None
    # 2. salt de nivell a la frontera exterior de la banda: per sector, frontera = max dref de la banda
    hp = img - ndi.gaussian_filter(img, 3.0)
    salt = {}; soroll = {}
    for s0 in range(0, 360, 15):
        ms = (az >= s0) & (az < s0+15)
        m = banda & ms
        if not m.any(): continue
        fr = dref[m].max()
        dins = ms & (dref > fr-8) & (dref <= fr-2) & banda
        fora = ms & (dref >= fr+2) & (dref < fr+8) & ~banda
        if dins.sum() < 30 or fora.sum() < 30: continue
        # nivell: mediana; per treure el gradient radial, comparo amb l'esperat per extrapolació lineal del perfil exterior
        # (ajust lineal de mediana vs dref a fr+2..fr+20 i extrapolat a la zona 'dins')
        ext_zone = ms & (dref >= fr+2) & (dref < fr+20) & ~banda
        A = np.c_[dref[ext_zone], np.ones(ext_zone.sum())]
        coef = np.linalg.lstsq(A, img[ext_zone], rcond=None)[0]
        pred_dins = coef[0]*dref[dins] + coef[1]
        lvl_dins = float(np.median(img[dins])); lvl_pred = float(np.median(pred_dins))
        salt[s0] = dict(frontera_px=round(float(fr-Rm), 1), nivell_dins=round(lvl_dins, 4), nivell_esperat=round(lvl_pred, 4),
                        salt_pct=round(100*(lvl_dins-lvl_pred)/max(lvl_pred, 1e-4), 2),
                        sigma_dins=round(float(hp[dins].std()), 5), sigma_fora=round(float(hp[fora].std()), 5),
                        ratio_sigma=round(float(hp[dins].std()/max(hp[fora].std(), 1e-9)), 2),
                        n_dins=int(dins.sum()), n_fora=int(fora.sum()))
    # 3. soroll global: anells de dref on coexisteixen banda i no-banda
    anells = {}
    for r0 in range(int(Rm)+8, int(Rm)+56, 8):
        m = (dref >= r0) & (dref < r0+8)
        a, b = m & banda, m & ~banda
        if a.sum() > 200 and b.sum() > 200:
            anells[r0-int(Rm)] = dict(sigma_banda=round(float(hp[a].std()), 5), sigma_fora=round(float(hp[b].std()), 5),
                                      ratio=round(float(hp[a].std()/hp[b].std()), 2), n_banda=int(a.sum()), n_fora=int(b.sum()),
                                      med_banda=round(float(np.median(img[a])), 4), med_fora=round(float(np.median(img[b])), 4))
    res = dict(layer=i, N_membres=N, R_moon_equiv=round(Rm, 2), centre_local=[round(cx, 2), round(cy, 2)],
               membres={f: dict(dt_s=round(dt, 2), centre=[round(a, 2), round(b, 2)], desplac_px=round(float(np.hypot(a-cx, b-cy)), 2)) for f, (a, b, dt) in cs.items()},
               extensio_banda_px_per_sector=ext, max_extensio_px=round(max(v for v in ext.values() if v is not None), 1),
               salt_frontera=salt, anells=anells)
    return res
if __name__ == '__main__':
    ids = [int(a) for a in sys.argv[1:]] or [7, 8, 9, 10]
    out = {}
    for i in ids:
        r = mesura(i); out[i] = r
        print(f"== ID{i} N={r['N_membres']} Rm={r['R_moon_equiv']} membres={ {f: v['desplac_px'] for f, v in r['membres'].items()} } max ext={r['max_extensio_px']}")
        print('  ext per sector:', {k: round(v, 0) for k, v in r['extensio_banda_px_per_sector'].items() if v is not None})
        print('  salt a la frontera (sector: frontera px, salt %, ratio σ):')
        for s0, v in r['salt_frontera'].items():
            print(f"    {s0:3d}: fr=+{v['frontera_px']:5.1f}  salt={v['salt_pct']:+6.2f}%  σ {v['sigma_dins']:.5f}/{v['sigma_fora']:.5f}={v['ratio_sigma']:.2f}  n={v['n_dins']}/{v['n_fora']}")
        print('  anells (px fora del limbe): σ banda/fora, mediana banda/fora')
        for k, v in r['anells'].items():
            print(f"    +{k:2d}: σ {v['sigma_banda']:.5f}/{v['sigma_fora']:.5f}={v['ratio']:.2f}  med {v['med_banda']:.4f}/{v['med_fora']:.4f}  n={v['n_banda']}/{v['n_fora']}")
    json.dump(out, open('banda_' + '_'.join(map(str, ids)) + '.json', 'w'), indent=1)
