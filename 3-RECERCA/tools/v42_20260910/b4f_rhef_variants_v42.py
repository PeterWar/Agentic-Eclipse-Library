"""B4f (V42) · Més RHEF, canviant un paràmetre cada vegada (petició de Pere: «posa'n algun més de RHEF modificant algun paràmetre»):
 · P02b «υ 0,35»: la funció upsilon de la referència sunkit-image sobre la RHEF V42 (P02, rang en radi continu de b4d): acosta tot valor a 0,5 (més suau pertot, contrast local a les cues).
 · P02c «local 60°» i P02d «local 30°»: RANG LOCAL. En comptes del rang dins de l'anell sencer (360°), cada píxel es compara amb els píxels de la seva banda radial (8 px)
   dins d'un sector d'azimut de 60° (o 30°) centrat en ell: equalització d'histograma local en coordenades polars (la mateixa idea que la RHEF, però el «context» és un
   tros d'anell). Els sectors se solapen (centres cada S/4) i el rang s'interpola bilinealment entre els dos centres de sector i les dues bandes veïnes: cap costura.
   Efecte: on l'anell sencer és dominat per un streamer brillant, el rang local torna a repartir el contrast dins de cada sector (les regions fosques recuperen detall).
Entrada: base G sense estrelles (V42). Sortides: cau/P02{b,c,d}_*_u16.npy (pantalla [0,1] com la P02), rebut REB42/B4f_rhef_variants.json.
Ús: b4f_rhef_variants_v42.py [base.npy support.npy p02_float.npy]  (per defecte els de la V42)"""
from comu42 import *
import time
DR = 8.0


def upsilon(x, ups=0.35):
    mid = float(np.nanmean(x)); y = np.full_like(x, np.nan); lo = x < mid; y[lo] = ((2 * x[lo]) ** ups) / 2; hi = (~lo) & np.isfinite(x); y[hi] = 1 - ((2 - 2 * x[hi]) ** ups) / 2; return y


def rhef_local(a, m, r, t, S_deg, step_deg):
    """rang local: banda radial DR px × sector S_deg (centres cada step_deg), interpolació bilineal (banda, sector)."""
    out = np.full(a.shape, np.nan, np.float32); K = int(round(360.0 / step_deg)); half = S_deg / 2.0
    th = np.degrees(t) % 360.0; band = np.floor(r / DR).astype(np.int32); fb = (r / DR - band - 0.5)   # posició dins de la banda: −0,5…0,5 → interpola amb la banda veïna
    nb = int(band[m].max()) + 1; idx_all = np.flatnonzero(m); af = a.ravel(); thf = th.ravel(); bf = band.ravel(); fbf = fb.ravel()
    order = np.argsort(bf[idx_all], kind='stable'); idx_all = idx_all[order]; bands_of = bf[idx_all]; cuts = np.searchsorted(bands_of, np.arange(nb + 1))
    def cells(i):
        """CDFs (valors ordenats) dels K sectors de la banda i (cadascun ±half al voltant del centre k·step)"""
        if i < 0 or i >= nb: return None
        ix = idx_all[cuts[i]:cuts[i + 1]]
        if len(ix) == 0: return None
        v = af[ix]; ang = thf[ix]; res = []
        for k in range(K):
            c = k * step_deg; d = np.abs(((ang - c) + 180.0) % 360.0 - 180.0); sel = d <= half; res.append(np.sort(v[sel]) if sel.sum() >= 50 else None)
        return res
    cache = {}
    def get(i):
        if i not in cache: cache[i] = cells(i)
        for old in [k_ for k_ in cache if k_ < i - 1]: del cache[old]
        return cache[i]
    def rank(sorted_vals, v):
        if sorted_vals is None: return np.full(v.shape, np.nan, np.float32)
        n = len(sorted_vals); lo = np.searchsorted(sorted_vals, v, side='left'); hi = np.searchsorted(sorted_vals, v, side='right'); return ((lo + hi) / 2.0 / n).astype(np.float32)   # rang mitjà per als empats / població
    t0 = time.time()
    for i in range(nb):
        ix = idx_all[cuts[i]:cuts[i + 1]]
        if len(ix) == 0: continue
        v = af[ix]; ang = thf[ix]; f = fbf[ix]; k0 = np.floor(ang / step_deg).astype(np.int32) % K; k1 = (k0 + 1) % K; wk = (ang / step_deg - np.floor(ang / step_deg)).astype(np.float32)
        j = np.where(f >= 0, i + 1, i - 1); wj = np.abs(f).astype(np.float32)   # banda veïna i pes
        C0 = get(i); acc = np.zeros(len(ix), np.float32); wsum = np.zeros(len(ix), np.float32)
        for (kk, wk_) in ((k0, 1 - wk), (k1, wk)):
            for k in np.unique(kk):
                sel = kk == k; rk = rank(C0[k] if C0 else None, v[sel]); w = wk_[sel] * (1 - wj[sel]); good = np.isfinite(rk); acc[np.flatnonzero(sel)[good]] += (rk * w)[good]; wsum[np.flatnonzero(sel)[good]] += w[good]
        for jj in np.unique(j):
            Cj = get(int(jj)); selj = j == jj
            if Cj is None: continue
            for (kk, wk_) in ((k0, 1 - wk), (k1, wk)):
                for k in np.unique(kk[selj]):
                    sel = selj & (kk == k); rk = rank(Cj[k], v[sel]); w = wk_[sel] * wj[sel]; good = np.isfinite(rk); acc[np.flatnonzero(sel)[good]] += (rk * w)[good]; wsum[np.flatnonzero(sel)[good]] += w[good]
        out.ravel()[ix] = np.where(wsum > 0, acc / np.maximum(wsum, 1e-9), np.nan)
        if i % 100 == 0: log(f'  banda {i}/{nb} ({time.time() - t0:.0f}s)')
    return out


def main():
    if len(sys.argv) > 3: base, sup, p02 = (Path(p) for p in sys.argv[1:4])
    else: base, sup, p02 = CAU42 / 'base_G_v42_sense_estrelles.npy', CAU42 / 'support_v42.npy', HERE42 / 'purs/cau/P02_RHEF_float.npy'
    a = np.asarray(np.load(base, mmap_mode='r'), np.float32); m = np.load(sup) & np.isfinite(a) & (a > 0); r, t = coords(); rep = {}
    ref_u16 = np.load(HERE42.parent / 'v38_20260908/purs/cau/P02_RHEF_u16.npy', mmap_mode='r'); fill = int(np.bincount(np.asarray(ref_u16[~np.load(CAU38 / 'support_v38.npy')]).ravel()[:200000]).argmax()) if True else 0
    def desa(nom, x, nota):
        u = np.where(m, np.round(np.clip(np.nan_to_num(x, nan=0.5), 0, 1) * 65535), fill).astype(np.uint16); np.save(CAU42 / f'{nom}_u16.npy', u); np.save(CAU42 / f'{nom}_float.npy', np.where(m, x, np.nan).astype(np.float32))
        q = np.nanpercentile(x[m], [1, 10, 50, 90, 99]); rep[nom] = dict(nota=nota, quantils_1_10_50_90_99=q.tolist(), sha256_u16=sha(CAU42 / f'{nom}_u16.npy')); log(f'{nom}: quantils {np.round(q, 3)}')
        from PIL import Image; Image.fromarray(np.uint8(u[::4, ::4] // 257)).save(VIS42 / f'B4f_{nom}_llenc_sencer.png')
    if p02.exists():
        x = np.asarray(np.load(p02, mmap_mode='r'), np.float32); desa('P02b_RHEF_ups0.35', upsilon(np.clip(x, 0, 1)), 'υ 0,35 (sunkit-image apply_upsilon, tall a la mitjana) sobre la RHEF V42')
    for S, nom in ((60.0, 'P02c_RHEF_local60'), (30.0, 'P02d_RHEF_local30')):
        log(f'RHEF local S={S:g}°…'); x = rhef_local(a, m, r, t, S, S / 4.0); desa(nom, x, f'rang local: banda {DR:g} px × sector {S:g}° (centres cada {S / 4:g}°), interpolació bilineal')
    savejson(REB42 / 'B4f_rhef_variants.json', rep); log('B4f fet')


if __name__ == '__main__':
    main()
