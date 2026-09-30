"""P0 · BUCLE RÀPID (Pere, 09-09: «hem de trobar una manera més ràpida d'iterar: un filtre de cada tipus, i obviar els que ja estan bé»).
Un filtre per família (01 ACHF, P03 MGN; P05 bilateral opcional), NOMÉS el canal G, en RETALLS de 2048 px (nucli 1024) a quatre llocs:
corona 1,6 R☉, exterior 3,7 i 5,5 R☉, i la vora del camp de la Vixen a ~5 R☉. Els operadors són locals (bandes ≤ 64 px): el retall dona el mateix
que el llenç sencer lluny del marge. Per a cada retall i filtre calcula el detall SENSE guany (τ = 0, la V38) i AMB la regla vigent de cau/tau.json
(mode/k/σ_E) i el model de soroll «ràpid»: N_ref = soroll de meitats de la SONY allà on la Sony hi és (×k_S, mesurat 1,00–1,03 contra el total), i de
la Vixen a l'interior. Surt: residu de gra per banda (candidata/τ0) a cada retall, perfil del rms a través de la vora de la Vixen, i PNG costat a costat.
1–2 minuts per volta. Les portes de llenç sencer (Brno, PSB) només quan això digui que sí.
Ús: p0_rapid.py [etiqueta] [capes=01,P03,P05] [k=3] [mode=wg] [se=6] [ks=1.03]"""
import sys, time
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
import b4a_capes_cadena as B
from comu39 import CAU38, CAU39, VIS39, REB39, H, W, RS, CX, CY, coords, log, savejson
import numpy as np, cv2, json
from pathlib import Path
from scipy.ndimage import gaussian_filter
import filtres_v39 as F
from filtres_v39 import Soroll, guany, ng, mgn_v39, wow_v39
RAP = CAU39 / 'rapid'; RAP.mkdir(exist_ok=True); (VIS39 / 'rapid').mkdir(exist_ok=True)
ARGS = dict(a.split('=', 1) for a in sys.argv[2:] if '=' in a); TAG = sys.argv[1] if len(sys.argv) > 1 and '=' not in sys.argv[1] else 'rapid'
CAPES = ARGS.get('capes', '01,P03').split(','); K = float(ARGS.get('k', F.KSOFT)); MODE = ARGS.get('mode', F.MODE); KS = float(ARGS.get('ks', 1.03))
if 'se' in ARGS: F.SE_FACTOR = float(ARGS['se'])
HALF = 1024; CORE = np.s_[512:1536, 512:1536]
WINS = {'corona1.6R': (int(CX + 1.6 * RS * np.cos(np.radians(-135))), int(CY + 1.6 * RS * np.sin(np.radians(-135)))), 'ext3.7R': (5089, 5294), 'ext5.5R': (int(CX - 5.5 * RS), int(CY + 0.6 * RS)), 'voraVixen5R': (7424, 5760)}
LADDER = [1, 2, 4, 8, 16, 32, 48, 64]; SIG01 = (2, 4, 8, 16, 32); BANDS = [(0, 1), (1, 2), (2, 4), (4, 8), (8, 16), (16, 32), (32, 64)]


def cache(name, fn):
    p = RAP / name
    if p.exists(): return np.load(p, mmap_mode='r')
    a = fn(); np.save(p, a); return np.load(p, mmap_mode='r')


def main():
    t0 = time.time(); r, t = coords(); m = np.load(CAU38 / 'support_v38.npy'); wv = np.nan_to_num(np.asarray(np.load(CAU38 / 'weight_vixen_v38.npy', mmap_mode='r'), np.float32))
    total = np.load(CAU38 / 'fusion_total_v38.npy', mmap_mode='r')
    def x_farcit():
        good = m & (total[..., 1] > 0); x = np.log(np.maximum(total[..., 1], 1e-8)); x, _ = B.farcit_perfil_ln_A(x, good, r); return x.astype(np.float32)
    X = cache('x_farcit_G.npy', x_farcit); ENT = np.load(CAU39 / 'entrada_operadors_farcida_v37.npy', mmap_mode='r')   # entrada lineal farcida dels operadors purs (b4c)
    SOR = Soroll(CAU39 / 'soroll_escales_1q.npz', wv); sS4 = SOR.sS; sV4 = SOR.sV
    mv = wv > 0.005; dsig = np.where(mv, cv2.distanceTransform(mv.astype(np.uint8), cv2.DIST_L2, 5), -cv2.distanceTransform((~mv).astype(np.uint8), cv2.DIST_L2, 5))
    def Nref(key, sl, canal=None):
        """N_ref al retall: Sony (meitats × k_S) on la Sony hi és, Vixen a la resta; 1/4 → retall."""
        NV4, NS4 = SOR.per_tren(key, canal=canal); n4 = np.where(sS4, NS4 * KS, NV4).astype(np.float32)
        y0, y1, x0, x1 = sl[0].start // 4, sl[0].stop // 4, sl[1].start // 4, sl[1].stop // 4; sub = n4[y0:y1, x0:x1]
        return np.maximum(cv2.resize(sub, (sl[1].stop - sl[1].start, sl[0].stop - sl[0].start), interpolation=cv2.INTER_LINEAR), 0)
    rep = {'etiqueta': TAG, 'mode': MODE, 'k': K, 'se_factor': F.SE_FACTOR, 'k_sony': KS, 'capes': CAPES, 'finestres': {}}
    log(f'preparació {time.time() - t0:.0f} s · mode {MODE} k {K} σ_E {F.SE_FACTOR}ℓ (mín {F.SE_MIN}) · k_S {KS}')
    for wn, (xc, yc) in WINS.items():
        sl = (slice(yc - HALF, yc + HALF), slice(xc - HALF, xc + HALF)); good = np.asarray(m[sl]); ones = np.ones(good.shape, bool); rw = {}
        for capa in CAPES:
            t1 = time.time()
            if capa == '01':
                x = np.asarray(X[sl], np.float32); w = np.ones(x.shape, np.float32); prev = x.copy(); hp0 = np.zeros_like(x); hp1 = np.zeros_like(x); acc0 = np.zeros_like(x); acc1 = np.zeros_like(x)
                for j, s in enumerate(LADDER):
                    sm = B.normgauss(x, w, s); bp = prev - sm; key = f'bpachf{s:g}' if j > 0 else 'dog1'
                    g = guany(bp, good, Nref(key, sl), float(s), 1.0, mode=MODE, k=K); hp0 = hp0 + bp; hp1 = hp1 + bp * g
                    if s in SIG01: acc0 += hp0 / len(SIG01); acc1 += hp1 / len(SIG01)
                    prev = sm
                d0, d1 = acc0, acc1
            elif capa == 'P03':
                a = np.maximum(np.asarray(ENT[sl], np.float32), 0); lim = [float(a.min()), float(a.max())]
                class SR:   # soroll per al MGN: N_ref en ln × μ² es fa dins de mgn_v39 (soroll.N retorna ln)
                    z = SOR.z
                    def N(self, key, shape, canal=None): return Nref(key, sl, canal)
                d0 = mgn_v39(a, ones, None, 0.0, h=0.0, limits=lim, log=lambda *_: None); d1 = mgn_v39(a, ones, SR(), 1.0, h=0.0, limits=lim, mode=MODE, log=lambda *_: None)
            elif capa == 'P05':
                a = np.asarray(ENT[sl], np.float32)
                class SR:
                    z = SOR.z; te_bilateral = SOR.te_bilateral
                    def N(self, key, shape, canal=None): return Nref(key, sl, canal)
                d0 = wow_v39(a, ones, 11, True, None, 0.0, log=lambda *_: None); d1 = wow_v39(a, ones, 11, True, SR(), 1.0, mode=MODE, log=lambda *_: None)
            else:
                continue
            # residu per banda (candidata / τ0) al nucli
            res = []
            for s1, s2 in BANDS:
                b0 = (d0 if s1 == 0 else gaussian_filter(d0, s1)) - gaussian_filter(d0, s2); b1 = (d1 if s1 == 0 else gaussian_filter(d1, s1)) - gaussian_filter(d1, s2)
                res.append(float(np.std(b1[CORE]) / max(np.std(b0[CORE]), 1e-12)))
            tot = float(np.std(d1[CORE]) / max(np.std(d0[CORE]), 1e-12)); rw[capa] = {'residu_per_banda': res, 'residu_total': tot, 'segons': round(time.time() - t1)}
            txt = f'{wn} {capa}: residu total ×{tot:.2f} · per banda ' + ' '.join(f'{v:.2f}' for v in res)
            if wn.startswith('vora'):   # perfil del rms a través de la vora (bins de distància signada, dins > 0)
                dd = np.asarray(dsig[sl]); bins = [(-500, -200), (-200, -50), (-50, 0), (0, 50), (50, 200), (200, 500), (500, 900)]
                p0 = [float(np.std(d0[(dd > a_) & (dd <= b_)])) if ((dd > a_) & (dd <= b_)).sum() > 500 else float('nan') for a_, b_ in bins]; p1 = [float(np.std(d1[(dd > a_) & (dd <= b_)])) if ((dd > a_) & (dd <= b_)).sum() > 500 else float('nan') for a_, b_ in bins]
                rw[capa]['vora_bins'] = bins; rw[capa]['rms_tau0'] = p0; rw[capa]['rms_candidata'] = p1; txt += ' · vora τ0 ' + ' '.join(f'{v:.3f}' for v in p0) + ' | cand ' + ' '.join(f'{v:.3f}' for v in p1)
            log(txt + f' ({time.time() - t1:.0f} s)')
            # PNG costat a costat (mateix estirament: percentils del τ0)
            from PIL import Image, ImageDraw
            lo, hi = np.percentile(d0[CORE], [0.5, 99.5]); tiles = []
            for lab, dd_ in (('τ=0 (V38)', d0), (TAG, d1)):
                im = Image.fromarray(np.uint8(np.clip((dd_[CORE] - lo) / max(hi - lo, 1e-9), 0, 1) * 255)).convert('RGB'); ImageDraw.Draw(im).text((8, 8), f'{capa} {wn} {lab}', fill=(255, 60, 60)); tiles.append(im)
            canvas = Image.new('RGB', (2 * 1024 + 8, 1024), (20, 20, 20)); canvas.paste(tiles[0], (0, 0)); canvas.paste(tiles[1], (1032, 0)); canvas.save(VIS39 / 'rapid' / f'P0_{TAG}_{wn}_{capa}.png')
        rep['finestres'][wn] = rw
    savejson(REB39 / f'P0_rapid_{TAG}.json', rep); log(f'P0 fet en {time.time() - t0:.0f} s')


if __name__ == '__main__':
    main()
