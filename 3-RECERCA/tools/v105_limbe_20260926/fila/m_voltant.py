"""m_voltant · tota la volta en sectors de 10°: màx |ΔL/L| de la mitjana per arc (d −1…16, files de 0,25 px) i ràtio d'energia fina
(màx a DMIN+1…DMIN+3 contra DMIN+4…DMIN+7, amb DMIN ≥ 0) de la variant i de la V104."""
import sys; sys.path.insert(0, '/private/tmp/claude_v105/fila')
from comu_fila import *
from m_mesura import CP, L4
Q = np.load(FR); DM = np.maximum(Q['DMIN'], 0); az = np.arange(1440) / 4
for nom in sys.argv[1:]:
    L = lum(np.load(OUT / nom / 'COMP_emul.npy')); pl = pol(L); p4 = pol(L4)
    lp = np.log(np.maximum(pl, 1e-4)); hp = lp - gaussian_filter1d(lp, 3, axis=1, mode='wrap'); l4 = np.log(np.maximum(p4, 1e-4)); h4 = l4 - gaussian_filter1d(l4, 3, axis=1, mode='wrap')
    out = []; rz = (DG >= -1) & (DG <= 16)
    for a0 in range(0, 360, 10):
        s = (DTH >= a0) & (DTH < a0 + 10); dm = float(DM[(az >= a0) & (az < a0 + 10)].mean())
        rel = pl[:, s].mean(1) / np.maximum(p4[:, s].mean(1), 1e-6) - 1; ip = (DG >= dm + 1) & (DG <= dm + 3); io = (DG >= dm + 4) & (DG <= dm + 7)
        f = hp[:, s].std(1); f4 = h4[:, s].std(1)
        out.append((a0, dm, 100 * np.abs(rel[rz]).max(), DG[rz][np.argmax(np.abs(rel[rz]))], f[ip].max() / f[io].mean(), f4[ip].max() / f4[io].mean()))
    print(f'## {nom}: sector DMIN | anell màx % @ d | ràtio fina variant (V104)')
    print('  ' + '\n  '.join(' · '.join(f'{a:3d}° {dm:4.1f} | {r:.2f}%@{d:4.1f} | {q:.2f} ({q4:.2f})' for a, dm, r, d, q, q4 in out[i:i + 4]) for i in range(0, 36, 4)))
    print(f'  PITJOR anell {max(o[2] for o in out):.3f} % · ràtio màx {max(o[4] for o in out):.2f} (V104 {max(o[5] for o in out):.2f})')
    desa(OUT / nom / 'VOLTANT.json', dict(sectors_10graus=[dict(pa=a, dmin=round(dm, 2), anell_pct=round(float(r), 3), d=float(d), ratio=round(float(q), 3), ratio_v104=round(float(q4), 3)) for a, dm, r, d, q, q4 in out], pitjor_anell_pct=round(float(max(o[2] for o in out)), 3), sectors_anell_sobre_05=[o[0] for o in out if o[2] >= 0.5]))
