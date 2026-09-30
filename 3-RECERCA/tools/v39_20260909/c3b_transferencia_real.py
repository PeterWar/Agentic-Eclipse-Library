"""C3b (V39) · Transferència sobre ESTRUCTURA REAL, no injectada (demanat per Codex, ronda 2): a les quatre finestres del jutge extern
(Vixen ORIGINAL, independent de la base Sony), per banda 2–8/8–32/32–64 px, quocient de COVARIÀNCIA creuada cov(banda(capa V39), banda(jutge)) /
cov(banda(capa V38), banda(jutge)). Si el guany només treu component NO correlacionada amb el jutge (soroll), el quocient és ≈ 1; si treu senyal,
és < 1 en la mateixa proporció. La correlació sola no ho distingeix (puja encara que es perdi senyal si el soroll cau més de pressa). Només lectura."""
from comu39 import *
from scipy.ndimage import gaussian_filter
import importlib.util as _iu
_sp = _iu.spec_from_file_location('c3_portes_v39', HERE39 / 'c3_portes.py'); C3 = _iu.module_from_spec(_sp); _sp.loader.exec_module(C3)   # el c3_portes d'AQUESTA carpeta (la v38 en té un altre al sys.path)


def main():
    r, t = coords(); m = np.load(CAU38 / 'support_v38.npy')
    fixed = np.load(ROOT / 'research/tools/v29/cau_final/vixen_total.npy', mmap_mode='r')[..., 1]; mv = np.load(ROOT / 'research/tools/v29/cau_final/vixen_support.npy')
    rep = {}
    for k, (p38, p39) in {**{kk: vv for kk, vv in C3.LAYERS.items() if kk in ('01', '04', '05', '06')}, **{kk: (C3.PC38 / vv[0], C3.PC39 / vv[1]) for kk, vv in C3.FLOATS.items()}}.items():
        A = np.load(p38, mmap_mode='r'); Bb = np.load(p39, mmap_mode='r'); rows = []
        for x, y in C3.WINS:
            sl = (slice(y - 384, y + 384), slice(x - 384, x + 384)); j0 = np.asarray(fixed[sl], np.float32); u = np.nan_to_num(np.asarray(A[sl], np.float32)); v = np.nan_to_num(np.asarray(Bb[sl], np.float32)); core = np.s_[256:512, 256:512]
            for s1, s2 in C3.BANDS:
                def band(zz):
                    return (gaussian_filter(zz, s1) - gaussian_filter(zz, s2))[core].ravel()
                j = band(j0); j = j - j.mean(); bu = band(u); bv = band(v); bu -= bu.mean(); bv -= bv.mean()
                c38 = float(np.mean(bu * j)); c39 = float(np.mean(bv * j))
                rows.append({'xy': [x, y], 'band': [s1, s2], 'cov_ratio_V39_V38': c39 / c38 if abs(c38) > 0 else None, 'rms_ratio_V39_V38': float(np.sqrt(np.mean(bv * bv) / max(np.mean(bu * bu), 1e-30))), 'corr_V38': float(np.corrcoef(bu, j)[0, 1]), 'corr_V39': float(np.corrcoef(bv, j)[0, 1])})
        rep[k] = rows
        for i, (s1, s2) in enumerate(C3.BANDS):
            cr = [rw['cov_ratio_V39_V38'] for rw in rows[i::3]]; rr = [rw['rms_ratio_V39_V38'] for rw in rows[i::3]]
            log(f'{k} banda {s1}–{s2}: transferència real (cov) ' + ' '.join(f'{c:.3f}' for c in cr) + f' · mitjana {np.mean(cr):.3f} · rms ×' + ' '.join(f'{c:.2f}' for c in rr))
    (REB39 / 'C3b_transferencia_real.json').write_text(json.dumps(rep, indent=1)); log('C3b fet')


if __name__ == '__main__':
    main()
