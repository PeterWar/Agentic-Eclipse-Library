"""C3b (V35) · Graó APARELLAT a les vores (Vixen i A) per capa: per a cada píxel de la vora (mostreig), diferència de la
mitjana local (σ24) a +D px cap endins i −D px cap enfora al llarg de la normal, dividida pel rms de la banda mitjana
(6–12 px) de la capa a la zona; control nul: la mateixa mesura sobre el contorn desplaçat 600 px cap endins.
(El graó per calaixos de distància del c3 no val per a NRGF/RHEF: els calaixos dins/fora cauen a radis i azimuts diferents.)"""
from comu35 import *
from scipy.ndimage import gaussian_filter, map_coordinates
PC34 = HERE34 / 'purs/cau'; PC35 = HERE35 / 'purs/cau'
LAYERS = {'01': (CAU34 / '01_v34_u16.npy', CAU35 / '01_v35_u16.npy'), '02': (CAU34 / '02_v34_u16.npy', CAU35 / '02_v35_u16.npy'), '04': (CAU34 / '04_v34_u16.npy', CAU35 / '04_v35_u16.npy'),
          '05': (CAU34 / '05_v34_u16.npy', CAU35 / '05_v35_u16.npy'), '06': (CAU34 / '06_v34_u16.npy', CAU35 / '06_v35_u16.npy'),
          'P01': (PC34 / 'P01_NRGF_u16.npy', PC35 / 'P01_NRGF_u16.npy'), 'P02': (PC34 / 'P02_RHEF_u16.npy', PC35 / 'P02_RHEF_u16.npy'), 'P03': (PC34 / 'P03_MGN_u16.npy', PC35 / 'P03_MGN_u16.npy'),
          'P04': (PC34 / 'P04_WOW_u16.npy', PC35 / 'P04_WOW_u16.npy'), 'P05': (PC34 / 'P05_WOW_bilateral_u16.npy', PC35 / 'P05_WOW_bilateral_u16.npy')}
D = 150.0


def ng(a, w, s):
    return gaussian_filter(a * w, s) / np.maximum(gaussian_filter(w, s), 1e-6)


def edge_samples(sd, zone, offset=0.0, step=25):
    band = zone & (np.abs(sd - offset) < 1.5); ys, xs = np.nonzero(band); ys, xs = ys[::step], xs[::step]
    gy, gx = np.gradient(gaussian_filter(sd, 4)); nx, ny = gx[ys, xs], gy[ys, xs]; n = np.hypot(nx, ny); ok = n > 1e-3
    return ys[ok].astype(np.float32), xs[ok].astype(np.float32), nx[ok] / n[ok], ny[ok] / n[ok]


def paired(lo, ys, xs, nx, ny, m):
    vin = map_coordinates(lo, [ys + D * ny, xs + D * nx], order=1, mode='nearest'); vout = map_coordinates(lo, [ys - D * ny, xs - D * nx], order=1, mode='nearest')
    ok_in = map_coordinates(m.astype(np.float32), [ys + D * ny, xs + D * nx], order=1) > 0.99; ok_out = map_coordinates(m.astype(np.float32), [ys - D * ny, xs - D * nx], order=1) > 0.99
    k = ok_in & ok_out; d = vin[k] - vout[k]; return (float(np.median(d)) if k.any() else float('nan')), int(k.sum())


def main():
    r, t = coords(); m = np.load(CAU35 / 'support_v35.npy'); w = m.astype(np.float32); mv0 = np.load(CAUF / 'vixen_support.npy')
    mvf = mv0 | (r < 1.6 * RS); sdv = np.where(mvf, cv2.distanceTransform(mvf.astype(np.uint8), cv2.DIST_L2, 5), -cv2.distanceTransform((~mvf).astype(np.uint8), cv2.DIST_L2, 5)).astype(np.float32)
    pa = np.load(CAUF / 'sony_A_weights.npy', mmap_mode='r'); A = np.load(CAU34 / 'sony_A_total_v34.npy', mmap_mode='r'); ma = np.all(np.isfinite(A) & (A > 0) & (pa > 0), axis=2) | (r < 1.2 * RS); del A
    sda = np.where(ma, cv2.distanceTransform(ma.astype(np.uint8), cv2.DIST_L2, 5), -cv2.distanceTransform((~ma).astype(np.uint8), cv2.DIST_L2, 5)).astype(np.float32)
    y, x = np.ogrid[:H, :W]; dist = np.hypot(x - GHOST_XY[0], y - GHOST_XY[1])
    zoneV = m & (r > 4 * RS) & (r < 9.5 * RS); zoneA = m & (r > 2.5 * RS) & (dist > 320) & (np.abs(sdv) > 400)
    S = {'vixen': [edge_samples(sdv, zoneV, 0.0), edge_samples(sdv, zoneV, 600.0)], 'A': [edge_samples(sda, zoneA, 0.0), edge_samples(sda, zoneA, 600.0)]}
    rep = {'D_px': D, 'sigma_local_px': 24, 'nul': 'contorn desplaçat 600 px cap endins', 'capes': {}}
    for k, (p34, p35) in LAYERS.items():
        row = {}
        for lab, p in (('V34', p34), ('V35', p35)):
            v = np.asarray(np.load(p, mmap_mode='r'), np.float32) / 65535; lo = ng(v, w, 24); mid = np.where(m, ng(v, w, 6) - ng(v, w, 12), 0)
            out = {}
            for vora, (real, nul) in S.items():
                zone = zoneV if vora == 'vixen' else zoneA; rms = float(np.sqrt(np.mean(mid[zone] ** 2)))
                sr, n1 = paired(lo, *real, m); sn, n2 = paired(lo, *nul, m)
                out[vora] = {'grao_sobre_rms': sr / max(rms, 1e-9), 'nul_sobre_rms': sn / max(rms, 1e-9), 'grao_u': sr, 'n': n1, 'n_nul': n2, 'rms_mig': rms}
            row[lab] = out; del v, lo, mid
        rep['capes'][k] = row
        log(f"{k}: vora Vixen {row['V34']['vixen']['grao_sobre_rms']:+.2f} (nul {row['V34']['vixen']['nul_sobre_rms']:+.2f}) → {row['V35']['vixen']['grao_sobre_rms']:+.2f} (nul {row['V35']['vixen']['nul_sobre_rms']:+.2f}) · vora A {row['V34']['A']['grao_sobre_rms']:+.2f} (nul {row['V34']['A']['nul_sobre_rms']:+.2f}) → {row['V35']['A']['grao_sobre_rms']:+.2f} (nul {row['V35']['A']['nul_sobre_rms']:+.2f})")
    savejson(REB35 / 'C3b_vora_aparellada.json', rep); log('C3b fet')


if __name__ == '__main__':
    main()
