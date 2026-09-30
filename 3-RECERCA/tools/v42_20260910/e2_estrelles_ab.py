"""E2 (V42) · Separació A→B a les estrelles per a QUALSEVOL recomposició de B (per calibrar el signe de la rotació i les correccions per fotograma).
Llavors: els pics reals de l'apuntament A (E1d). Per a cada estrella: pic a A (±12 px) i a B (±40 px), suavitzat σ 2, > 4 σ; vectors A→B; ajust rotació+translació
al voltant del Sol; elongació dels components de B. Ús: e2_estrelles_ab.py B.npy [A.npy] [etiqueta]"""
from comu42 import *
import importlib.util as _iu
_sp = _iu.spec_from_file_location('e1d', HERE41 / 'e1d_estrelles_dobles.py'); E = _iu.module_from_spec(_sp); _sp.loader.exec_module(E)   # crop, pics (R=60)
_sp2 = _iu.spec_from_file_location('e1e', HERE41 / 'e1e_rotacio_ab.py'); F = _iu.module_from_spec(_sp2); _sp2.loader.exec_module(F)     # ajust, dedup


def main():
    Bp = Path(sys.argv[1]); Ap = Path(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].endswith('.npy') else CAU36 / 'sony_A_total_v36.npy'; tag = sys.argv[-1] if not sys.argv[-1].endswith('.npy') else Bp.stem
    A = np.load(Ap, mmap_mode='r'); Bt = np.load(Bp, mmap_mode='r'); rows = json.loads((REB41 / 'E1d_estrelles_dobles.json').read_text())['files']
    seeds = [(r['cat_x'] + r['sonyA'][0]['dx'], r['cat_y'] + r['sonyA'][0]['dy'], r['r_R']) for r in rows if r.get('sonyA') and r['sonyA'][0]['snr'] > 4]
    seeds = F.dedup([dict(x=x, y=y, r=r) for x, y, r in seeds], lambda d: (d['x'], d['y']))
    vec = []
    for s in seeds:
        a = E.crop(A, s['x'], s['y'], 1); b = E.crop(Bt, s['x'], s['y'], 1)
        if a is None or b is None: continue
        pa = [p for p in E.pics(a) if np.hypot(p['dx'], p['dy']) <= 12]; pb = E.pics(b)
        if not pa or not pb: continue
        pa, pb = pa[0], pb[0]; vec.append(dict(x=s['x'] + pa['dx'], y=s['y'] + pa['dy'], r_R=s['r'], AB=[pb['dx'] - pa['dx'], pb['dy'] - pa['dy']], snrA=pa['snr'], snrB=pb['snr'], elongB=pb['elongacio'], angB=pb['angle_deg'], fwhmB=[pb['fwhm_major'], pb['fwhm_menor']]))
    P = np.array([[v['x'] - CX, v['y'] - CY] for v in vec], float); D = np.array([v['AB'] for v in vec], float)
    tr, pred = F.ajust(P, D); rms_brut = float(np.sqrt(np.mean(D ** 2))); rms_t = float(np.sqrt(np.mean((D - D.mean(0)) ** 2)))
    el = float(np.median([v['elongB'] for v in vec])); fw = np.median([v['fwhmB'] for v in vec], 0)
    log(f"[{tag}] {len(vec)} estrelles · |A→B| mediana {np.median(np.hypot(D[:, 0], D[:, 1])):.1f} px · rms brut {rms_brut:.2f} · només translació {rms_t:.2f} (mitjana ({D.mean(0)[0]:+.1f}, {D.mean(0)[1]:+.1f})) · rotació {tr['theta_arcmin']:+.2f}′ + t ({tr['t'][0]:+.1f}, {tr['t'][1]:+.1f}) rms {tr['rms_px_per_component']:.2f} · B: elongació mediana {el:.2f}, FWHM {fw[0]:.1f}×{fw[1]:.1f}")
    for v in vec: log(f"    {v['r_R']:4.1f} R☉ ({v['x']},{v['y']}) A→B ({v['AB'][0]:+d},{v['AB'][1]:+d}) snr A {v['snrA']:.0f} B {v['snrB']:.0f} elong B {v['elongB']:.2f} ang {v['angB']:+.0f}°")
    savejson(REB42 / f'E2_AB_{tag}.json', dict(B=str(Bp), A=str(Ap), n=len(vec), rms_brut=rms_brut, rms_translacio=rms_t, mitjana_AB=D.mean(0).tolist(), rotacio=tr, elongB_mediana=el, fwhmB=fw.tolist(), estrelles=vec)); log('E2 fet')


if __name__ == '__main__':
    main()
