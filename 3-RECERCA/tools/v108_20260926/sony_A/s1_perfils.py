"""s1 · On són T1 i T2 a cada etapa, amb la geometria FIXA (sense cerca) i nul de rectes paral·leles i girades a la mateixa imatge.
Fonts: apilats A i B (control i flat 2D), fusió Sony A+B, base_G, compost amb les màscares de la V107 (abans/després del flat 2D).
T2 es parteix en trams segons la cobertura de B (B cobreix només una part de T2, a la vora de dalt del seu sensor).
Sortida: S1_PERFILS.json i S1_perfils.npz (perfils per a les vistes)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); from comu_sonyA import *
res = {}; perf = {}
# cobertura de B, fA i pes Vixen al llarg de cada traç (control)
Bw = np.load(FONTS['B_ctrl'][0], mmap_mode='r'); fA = np.load(V98 / 'b3/cau/sony_fA_v42.npy', mmap_mode='r'); wv = np.load(V98 / 'b3/cau/weight_vixen_v42.npy', mmap_mode='r')
TRAMS = {}
for k, tr in TRACOS.items():
    L = tr['llarg']; s = np.arange(-L / 2, L / 2 + 1e-6, 4.0); X, Y = graella(tr['centre'], tr['d'], s, np.array([0.0]))
    xi = np.clip(np.round(X[:, 0]).astype(int), 0, W - 1); yi = np.clip(np.round(Y[:, 0]).astype(int), 0, H - 1)
    bcov = np.array([float(np.isfinite(Bw[y, x, 1]) and Bw[y, x, 1] > 0) for x, y in zip(xi, yi)])
    fa = np.array([float(fA[y, x]) for x, y in zip(xi, yi)]); wvv = np.array([float(wv[y, x]) for x, y in zip(xi, yi)])
    res.setdefault('cobertura', {})[k] = dict(s=s, B_cobreix=bcov, fA=fa, pes_vixen=wvv)
    print(f"T{k}: B cobreix {bcov.mean()*100:.0f} % · fA mediana {np.median(fa):.2f} (p10 {np.percentile(fa,10):.2f}, p90 {np.percentile(fa,90):.2f}) · pes Vixen màx {wvv.max():.3f}", flush=True)
    trams = {'sencer': (None, None)}
    if k == 2:
        # trams per cobertura de B (canvi de 0 a 1 al llarg de s)
        sb = s[bcov > 0.5]; sn = s[bcov < 0.5]
        if len(sb) and len(sn):
            tall = float(sb.min() if sb.min() > sn.min() else sb.max())
            if sb.mean() > sn.mean(): trams.update({'amb_B': (tall + 80, L / 2), 'sense_B': (-L / 2, tall - 80)})
            else: trams.update({'amb_B': (-L / 2, tall - 80), 'sense_B': (tall + 80, L / 2)})
            print(f"  T2: tall de cobertura de B a s = {tall:.0f} px", flush=True)
    TRAMS[k] = trams
res['trams'] = {k: {n: list(v) for n, v in t.items()} for k, t in TRAMS.items()}
for nom in FONTS:
    a, ch = obre(nom)
    for k, tr in TRACOS.items():
        box = caixa_tr(tr, 700); r = rel_map(retall(a, ch, box))
        for tn, (s0, s1) in TRAMS[k].items():
            m, t, pr = mesura_amb_nul(r, box[:2], tr['centre'], tr['d'], tr['llarg'], s0, s1)
            res.setdefault(nom, {})[f'T{k}_{tn}'] = m; perf[f'{nom}_T{k}_{tn}'] = pr; perf['t'] = t
            print(f"{nom:13s} T{k} {tn:8s}: D {m['D']*1e4:+7.2f}‱ · nul {m.get('nul_med', np.nan)*1e4:+.2f}±{m.get('nul_mad', np.nan)*1e4:.2f}‱ · z {m.get('z', np.nan):+.1f} · p {m.get('p', np.nan):.3f} · cob {m.get('cobertura', np.nan):.2f}", flush=True)
        del r
desa(OUT / 'S1_PERFILS.json', res); np.savez_compressed(OUT / 'S1_perfils.npz', **perf)
