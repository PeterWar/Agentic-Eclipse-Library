"""vm2 (verificador adversari, V108 marrons) · QUÈ FA LA CURA (flat 2D) A LA DADA, amb mesures pròpies. Només llegeix.
Parells abans/després: base_G (E ↔ pilot; el control de determinisme de vm0 demostra que b3d4 + f2 reprodueixen E bit a bit, o sigui que la
diferència és NOMÉS el flat 2D), fusion_starless (color), apilats per tren (G), i el compost amb les màscares de la V107 (de l'agent).
Mesures:
  M1 energia per escales (DoG del ln, bandes de 1–2 … 64–128 px) per anells de R☉: rms abans, després, i rms de la diferència;
  M2 Brno (L230–233 de l'estat E): correlació del DoG σ2–16 del ln, per anells (com j0), abans/després;
  M3 contrast plomall/buit: perfil azimutal (720 calaixos, suavitzat σ 6 px) a 1,2 / 1,5 / 2 / 3 / 4 R☉: (p95 − p5)/p50 i correlació abans↔després;
  M4 anells: perfil radial (mediana azimutal) de D = després/abans − 1, pas 2 px, rms del residu d'alta freqüència (> σ 20 px);
  M5 caixa lunar i disc: |D| dins la caixa de la franja i a d < 60 px del limbe;
  M6 color: ln(R/G) i ln(B/G) de fusion_starless: rms del DoG σ2–30 per anells abans/després, i canvi a gran escala (σ 100) p50/p99;
  M7 textura fina (MAD del DoG σ2–16 del ln, r > 4 R☉) de cada parell; nivell a gran escala |G100(després)/G100(abans) − 1| p50/p99/màx;
  M8 injecció: per rajoles de 256 px, energia del DoG σ2–30 després/abans; fracció de rajoles on PUJA > 5 % i > 15 %, i on són.
Sortida: VM2_EFECTE.json i vistes del llenç sencer (1/4) de D per a la base i la Vixen."""
import sys, json
from pathlib import Path
import numpy as np, cv2
ARREL = Path(__file__).resolve().parents[4]; OUT = ARREL / '4-RESULTATS/v108_20260926/verifica_marrons'
W, H = 10551, 7506; SOL = (5361.768, 3775.748); RSOL = 440.603; LLUNA = (5375.787, 3775.977); RL = 452.98
PI = ARREL / '4-RESULTATS/v108_20260926/marrons/pilot'; E = ARREL / '4-RESULTATS/v103_banda_20260926/E'
ES = E / 'estat_v103'
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v97_refundacio_20260924')); from jutge_comu import Estat; ESTAT = Estat(ES)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); RS = np.hypot(xx - SOL[0], yy - SOL[1]) / RSOL; DL = np.hypot(xx - LLUNA[0], yy - LLUNA[1]) - RL
TH = (np.degrees(np.arctan2(-(yy - SOL[1]), xx - SOL[0])) % 360).astype(np.float32); del yy, xx
ANELLS = [(1.05, 1.5), (1.5, 2.5), (2.5, 4.0), (4.0, 6.0), (6.0, 10.0)]
def carrega(p, ch=None):
    a = np.load(p, mmap_mode='r'); return np.asarray(a if ch is None else a[..., ch], np.float32)
def lnv(img):
    m = (np.isfinite(img) & (img > 0)).astype(np.float32); return np.where(m > 0, np.log(np.maximum(img, 1e-12)), 0).astype(np.float32), m
def ng(l, m, s): return cv2.GaussianBlur(l * m, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6)
def dog(l, m, a, b): return (ng(l, m, a) if a > 0 else l) - ng(l, m, b)
res = {}
def rms(x): return float(np.sqrt(np.mean(x ** 2))) if x.size else None
def mad(x): return float(1.4826 * np.median(np.abs(x - np.median(x)))) if x.size else None
def parell(nom, A, B, fer_brno=False, fer_plomall=False, fer_injeccio=False):
    la, ma = lnv(A); lb, mb = lnv(B); m = ma * mb; ok = cv2.erode(m, np.ones((41, 41), np.uint8)) > 0
    r = {}
    # M1 energia per escales
    bandes = [(0, 1), (1, 2), (2, 4), (4, 8), (8, 16), (16, 32), (32, 64), (64, 128)]
    r['M1_energia'] = {}
    for a_, b_ in bandes:
        da = dog(la, m, a_, b_); db = dog(lb, m, a_, b_); dd = db - da; row = {}
        for r0, r1 in ANELLS:
            k = ok & (RS >= r0) & (RS < r1) & (DL > 30)
            if k.sum() < 1e4: continue
            ea, eb, ed = rms(da[k]), rms(db[k]), rms(dd[k]); row[f'{r0}-{r1}'] = dict(abans=ea, despres=eb, dif=ed, despres_sobre_abans=eb / ea, dif_sobre_abans=ed / ea)
        r['M1_energia'][f'{a_}-{b_}'] = row; del da, db, dd
    # M7 textura fina i nivell a gran escala
    k = ok & (RS > 4)
    da = dog(la, m, 2, 16); db = dog(lb, m, 2, 16); r['M7_textura_MAD_r_gt_4'] = dict(abans=mad(da[k]), despres=mad(db[k]), canvi=mad(db[k]) / mad(da[k]) - 1)
    ga = ng(A * m, m, 100); gb = ng(B * m, m, 100); ok3 = cv2.erode(m, np.ones((301, 301), np.uint8)) > 0
    z = np.abs(gb[ok3] / ga[ok3] - 1); r['M7_nivell_gran_escala'] = dict(p50=float(np.median(z)), p99=float(np.percentile(z, 99)), max=float(z.max())); del ga, gb, z
    # M8 injecció per rajoles
    if fer_injeccio:
        ea = dog(la, m, 2, 30) ** 2; eb = dog(lb, m, 2, 30) ** 2; rat = []; llista = []
        for y0 in range(0, H - 255, 256):
            for x0 in range(0, W - 255, 256):
                kk = ok[y0:y0 + 256, x0:x0 + 256]
                if kk.mean() < 0.9: continue
                q = float(np.sqrt(eb[y0:y0 + 256, x0:x0 + 256][kk].mean() / ea[y0:y0 + 256, x0:x0 + 256][kk].mean())); rat.append(q)
                if q > 1.05: llista.append(dict(x=x0 + 128, y=y0 + 128, r_Rsol=float(RS[y0 + 128, x0 + 128]), energia_despres_sobre_abans=q))
        rat = np.array(rat); r['M8_injeccio_rajoles_256'] = dict(n=int(rat.size), puja_5pc=float((rat > 1.05).mean()), puja_15pc=float((rat > 1.15).mean()), baixa_5pc=float((rat < 0.95).mean()),
                                                               p1_p50_p99=np.percentile(rat, [1, 50, 99]).tolist(), pitjors=sorted(llista, key=lambda d: -d['energia_despres_sobre_abans'])[:12])
        del ea, eb
    # M4 anells i M5 caixa/disc
    D = np.where(m > 0, B / np.where(m > 0, A, 1) - 1, np.nan).astype(np.float32)
    rb = (RS * RSOL / 2).astype(np.int32); kk = np.isfinite(D) & (RS > 1.02) & (RS < 8) & (DL > 5)
    i0, i1 = int(1.02 * RSOL / 2), int(8 * RSOL / 2); nb_ = np.bincount(rb[kk], None, i1 + 1); sb_ = np.bincount(rb[kk], D[kk], i1 + 1)
    prof = np.where(nb_ > 200, sb_ / np.maximum(nb_, 1), np.nan)[i0:i1]
    pf = np.where(np.isfinite(prof), prof, np.nanmedian(prof)).astype(np.float32); sm = cv2.GaussianBlur(pf.reshape(1, -1), (0, 0), 10).ravel()
    r['M4_anells'] = dict(rms_perfil_radial=float(np.nanstd(prof)), rms_alta_freq=float(np.std(pf - sm)), max_abs=float(np.nanmax(np.abs(prof))))
    cx = (slice(3077, 4477), slice(4677, 6077)); dcx = D[cx]
    r['M5_caixa_lunar'] = dict(abs_max=float(np.nanmax(np.abs(dcx))), abs_p99=float(np.nanpercentile(np.abs(dcx), 99)), frac_exactament_0=float(np.nanmean(dcx == 0)))
    kl = np.isfinite(D) & (DL > 0) & (DL < 60); r['M5_limbe_0_60px'] = dict(abs_p50=float(np.median(np.abs(D[kl]))), abs_p99=float(np.percentile(np.abs(D[kl]), 99)))
    r['D_global'] = dict(p1_p50_p99=np.nanpercentile(D[np.isfinite(D)], [1, 50, 99]).tolist())
    # M3 plomall / buit
    if fer_plomall:
        sa = ng(A * m, m, 6); sb = ng(B * m, m, 6); r['M3_plomall_buit'] = {}
        for rr in (1.2, 1.5, 2.0, 3.0, 4.0):
            k = (np.abs(RS - rr) < 0.02) & (DL > 20) & ok; ib = (TH[k] * 2).astype(np.int32)
            pa = np.bincount(ib, sa[k], 720) / np.maximum(np.bincount(ib, None, 720), 1); pb = np.bincount(ib, sb[k], 720) / np.maximum(np.bincount(ib, None, 720), 1)
            v = (np.bincount(ib, None, 720) > 5); pa, pb = pa[v], pb[v]
            ct = lambda p: float((np.percentile(p, 95) - np.percentile(p, 5)) / np.median(p))
            r['M3_plomall_buit'][str(rr)] = dict(contrast_abans=ct(pa), contrast_despres=ct(pb), corr_perfils=float(np.corrcoef(pa, pb)[0, 1]), n=int(v.sum()))
        del sa, sb
    # M2 Brno
    if fer_brno:
        P = 2; la2, ma2 = lnv(A[::P, ::P]); lb2, mb2 = lnv(B[::P, ::P]); m2 = ma2 * mb2; dA = dog(la2, m2, 1, 8); dB = dog(lb2, m2, 1, 8)
        rs2 = RS[::P, ::P]; dl2 = DL[::P, ::P]; r['M2_brno'] = {}
        for lid in (230, 231, 232, 233):
            Br = ESTAT.rgb(lid, pas=P)[:m2.shape[0], :m2.shape[1]]
            Br = 0.25 * Br[..., 0] + 0.5 * Br[..., 1] + 0.25 * Br[..., 2]; okb = Br > 0.002; lbr = np.log(np.maximum(Br, 1e-4)).astype(np.float32); dbr = dog(lbr, okb.astype(np.float32), 1, 8)
            okb = cv2.erode(okb.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool) & (cv2.erode(m2, np.ones((9, 9), np.uint8)) > 0)
            row = {}
            for a_, b_ in ((1.02, 1.5), (1.5, 2.5), (2.5, 4.0), (4.0, 6.0)):
                k = okb & (rs2 >= a_) & (rs2 < b_) & (dl2 > 6)
                if k.sum() < 1000: continue
                row[f'{a_}-{b_}'] = dict(abans=float(np.corrcoef(dA[k], dbr[k])[0, 1]), despres=float(np.corrcoef(dB[k], dbr[k])[0, 1]))
            r['M2_brno'][str(lid)] = row
    res[nom] = r; print(nom, json.dumps({k: v for k, v in r.items() if k not in ('M1_energia',)}, ensure_ascii=False)[:1500], flush=True)
    return D
def vista(D, nom, esc=0.003):
    d = cv2.resize(np.nan_to_num(D, nan=0.0), (W // 4, H // 4), interpolation=cv2.INTER_AREA); u = np.clip(d / esc, -1, 1)
    rgb = np.stack([np.clip(-u, 0, 1), np.zeros_like(u), np.clip(u, 0, 1)], -1) * 0 + 0.5
    rgb = np.stack([0.5 - 0.5 * u, 0.5 - 0.5 * np.abs(u) * 0.3, 0.5 + 0.5 * u], -1)
    cv2.imwrite(str(OUT / f'vm2_{nom}_D_pm{esc*100:g}pc_quart.png'), (np.clip(rgb[..., ::-1], 0, 1) * 255).astype(np.uint8))
quins = sys.argv[1:] or ['base', 'vixen', 'sonyA', 'color', 'compost']
if 'base' in quins:
    D = parell('base_G', carrega(E / 'lineal_v103/base_G.npy'), carrega(PI / 'lineal_v108/base_G.npy'), fer_brno=True, fer_plomall=True, fer_injeccio=True); vista(D, 'base_G', 0.003); del D
if 'vixen' in quins:
    D = parell('vixen_G', carrega(PI / 'control/vixen_total.npy', 1), carrega(PI / 'flat2d/vixen_total.npy', 1), fer_injeccio=True); vista(D, 'vixen_G', 0.005); del D
if 'sonyA' in quins:
    D = parell('sonyA_G', carrega(PI / 'control/sony_A_total.npy', 1), carrega(PI / 'flat2d/sony_A_total.npy', 1), fer_injeccio=True); del D
if 'compost' in quins:
    D = parell('compost_V107_mascares', carrega(PI / 'compost_v107mascares_abans.npy'), carrega(PI / 'compost_v107mascares_despres.npy'), fer_brno=True, fer_plomall=True, fer_injeccio=True); vista(D, 'compost', 0.01); del D
if 'color' in quins:
    fa = np.load(E / 'lineal_v103/fusion_starless.npy', mmap_mode='r'); fb = np.load(PI / 'lineal_v108/fusion_starless.npy', mmap_mode='r'); rc = {}
    for nomc, ch in (('lnRG', 0), ('lnBG', 2)):
        def croma(f):
            X = np.asarray(f[..., ch], np.float32); G = np.asarray(f[..., 1], np.float32); m = (np.isfinite(X) & np.isfinite(G) & (X > 0) & (G > 0)).astype(np.float32)
            return np.where(m > 0, np.log(np.maximum(X, 1e-12) / np.maximum(G, 1e-12)), 0).astype(np.float32), m
        ca, ma = croma(fa); cb, mb = croma(fb); m = ma * mb; ok = cv2.erode(m, np.ones((41, 41), np.uint8)) > 0
        da = dog(ca, m, 2, 30); db = dog(cb, m, 2, 30); row = {}
        for r0, r1 in ANELLS:
            k = ok & (RS >= r0) & (RS < r1) & (DL > 30)
            if k.sum() > 1e4: row[f'{r0}-{r1}'] = dict(abans=rms(da[k]), despres=rms(db[k]), dif=rms((db - da)[k]))
        ga = ng(ca, m, 100); gb = ng(cb, m, 100); ok3 = cv2.erode(m, np.ones((301, 301), np.uint8)) > 0; z = np.abs(gb - ga)[ok3]
        rc[nomc] = dict(dog_2_30_per_anell=row, gran_escala_abs_p50=float(np.median(z)), gran_escala_abs_p99=float(np.percentile(z, 99)))
        print(nomc, json.dumps(rc[nomc])[:800], flush=True); del ca, cb, da, db, ga, gb
    res['M6_color_fusion_starless'] = rc
prev = json.loads((OUT / 'VM2_EFECTE.json').read_text()) if (OUT / 'VM2_EFECTE.json').exists() else {}
prev.update(res); (OUT / 'VM2_EFECTE.json').write_text(json.dumps(prev, ensure_ascii=False, indent=1))
