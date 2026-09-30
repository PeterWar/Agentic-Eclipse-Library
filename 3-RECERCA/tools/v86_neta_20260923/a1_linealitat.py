"""a1 · Comprovació de la suma lineal que alimenta els filtres (V86). Només lectura de les fonts; escriu un rebut a 4-RESULTATS.
Preguntes: (1) la font dels filtres és la suma lineal (no una capa tonificada)? (2) té valors negatius, plans de saturació o graons?
(3) la capa base de Photoshop és una funció punt a punt d'aquesta suma (corba de to) o porta operacions espacials? (4) R/G i B/G continus?"""
from v86_comu import *
from psb69 import PSB
claim(); SORT.mkdir(exist_ok=True)
F = np.load(FONTS / 'fusion_starless.npy', mmap_mode='r'); G = np.load(FONTS / 'base_G.npy', mmap_mode='r'); M = np.load(FONTS / 'support.npy')
r, t = coords(); rep = {}
# (1) coherència font: base_G = G de la fusió sense estrelles al suport
sub = (slice(0, H, 7), slice(0, W, 7)); g = np.asarray(G[sub]); f1 = np.asarray(F[sub + (1,)]); m = M[sub]
rep['base_G_igual_a_fusio_G'] = bool(np.array_equal(g[m], f1[m]))
# (2) valors, negatius i sostre per anells al voltant del Sol
rs = r[sub]; out = []
for r0, r1 in [(440, 460), (460, 480), (480, 500), (500, 540), (540, 600), (600, 800), (800, 1200), (1200, 2000), (2000, 4000)]:
    s = m & (rs >= r0) & (rs < r1)
    if s.sum() < 50: continue
    q = np.asarray(F[sub])[s]
    out.append(dict(r=[r0, r1], n=int(s.sum()), negatius=int((q <= 0).sum()), p50=np.median(q, 0).round(3), p99=np.percentile(q, 99.9, 0).round(3),
                    RG=float(np.median(q[:, 0] / np.maximum(q[:, 1], 1e-9))), BG=float(np.median(q[:, 2] / np.maximum(q[:, 1], 1e-9)))))
rep['anells'] = out
# graons de sostre: fracció de píxels amb el valor idèntic al màxim del seu anell (pla de saturació)
q = np.asarray(F[sub + (1,)])[m]; rep['G_min_suport'] = float(q.min()); rep['G_max_suport'] = float(q.max())
vals, cnt = np.unique(q[q > np.percentile(q, 99.99)], return_counts=True); rep['valors_repetits_al_sostre'] = int(cnt.max()) if cnt.size else 0
# (3) base de Photoshop (V85, capa 3) contra la suma lineal: dispersió condicionada (és una funció punt a punt?)
p = PSB(str(ARREL / '1-PHOTOSHOP/V85.psb')); ys, xs = np.nonzero(m); rng = np.random.default_rng(1); k = rng.choice(len(ys), 400000, replace=False); ys, xs = ys[k] * 7, xs[k] * 7
disp = np.stack([p.channel(3, c)[0][ys, xs] for c in range(3)], -1).astype('float64') / 65535
lin = np.asarray(F[ys, xs]).astype('float64'); Lg = np.log10(np.maximum(lin[:, 1], 1e-9)); fora = np.hypot(ys - CY, xs - CX) > 470
res = {}
for c, nom in enumerate('RGB'):
    x = np.log10(np.maximum(lin[fora, c], 1e-9)); y = disp[fora, c]; o = np.argsort(x); x, y = x[o], y[o]
    nb = 400; cuts = np.linspace(0, len(x), nb + 1).astype(int); med = np.array([np.median(y[a:b]) for a, b in zip(cuts[:-1], cuts[1:])])
    xm = np.array([np.median(x[a:b]) for a, b in zip(cuts[:-1], cuts[1:])]); pred = np.interp(x, xm, med); e = y - pred
    res[nom] = dict(dispersio_rms_DN16=float(np.sqrt(np.mean(e ** 2)) * 65535), p99_abs_DN16=float(np.percentile(np.abs(e), 99) * 65535),
                    monotona=bool(np.all(np.diff(med) >= -2e-3)), rang_display=[float(med.min()), float(med.max())])
rep['base_V85_contra_suma_lineal'] = res
# dispersió deguda al color: display G en funció de (G, R/G, B/G) amb una regressió lineal local per trams de G
x = Lg[fora]; y = disp[fora, 1]; rg = np.log(np.maximum(lin[fora, 0] / np.maximum(lin[fora, 1], 1e-9), 1e-6)); bg = np.log(np.maximum(lin[fora, 2] / np.maximum(lin[fora, 1], 1e-9), 1e-6))
o = np.argsort(x); x, y, rg, bg = x[o], y[o], rg[o], bg[o]; cuts = np.linspace(0, len(x), 201).astype(int); e2 = []
for a, b in zip(cuts[:-1], cuts[1:]):
    A = np.c_[np.ones(b - a), x[a:b], rg[a:b], bg[a:b]]; c_, *_ = np.linalg.lstsq(A, y[a:b], rcond=None); e2.append(y[a:b] - A @ c_)
e2 = np.concatenate(e2); rep['base_V85_G_amb_color_explicat_rms_DN16'] = float(np.sqrt(np.mean(e2 ** 2)) * 65535)
desa_json('A1_LINEALITAT.json', rep); log('A1 fet'); print(json.dumps({k: v for k, v in rep.items() if k != 'anells'}, indent=1, default=str)); [print(a) for a in out]
