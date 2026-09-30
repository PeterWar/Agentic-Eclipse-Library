"""B1 · Camps de nivell per fotograma: la cura a l'origen de les fronteres HDR.

Mecanisme (research/102/104/125 i A2/A5 d'aquesta ronda): el compost LDIC és una
mitjana ponderada de fotogrames; on canvia el joc de fotogrames (una isofota de
saturació o de terra) el nivell salta si els fotogrames no comparteixen nivell.
Els offsets constants del c03 no cobreixen un desnivell que varia pel camp
(transparència i cel per fotograma, vinyetatge residual).

Model per fotograma i canal natiu: ln(L_i) = ln T + ε_i(x), amb ε_i SUAU (σ 128 px).
  · L_i = v_i·k_i + b_i  (valor calibrat per segon, guany de coherència k i offset c03, com a la V29/c03)
  · T   = compost del grup (Σ w L / Σ w) amb els mateixos pesos LDIC (els pesos NO es toquen)
  · ε_i s'estima NOMÉS a l'altiplà del fotograma (finestra ≥ 0,5) i s'estén al seu suport
  · gauge: ε̄ = mitjana ponderada dels ε_i suavitzada a σ 512 px → φ_i = ε_i − ε̄
  · fotograma corregit: L_i·exp(−φ_i); s'itera 4 vegades.
La corona real és al fotograma i al compost alhora: surt del quocient. La correcció
és multiplicativa i suau; no toca cap pes, cap suport ni cap píxel de forma local.
Sortida: cau/{grup}_{canal}_phi.npy (n, HC, WC) i rebut B1 amb residus abans/després.
"""
from comu36 import *
from scipy.ndimage import distance_transform_edt

SIG_FIELD_PX = 128.0
SIG_GAUGE_PX = 512.0
ITER = 4
GROUPS = {'vixen': ('vixen', None), 'sony_A': ('sony', 'sony_A'), 'sony_B': ('sony', 'sony_B')}
CH = {'R': ('R', 0), 'G': ('', 1), 'B': ('B', 2)}     # sufix dels fitxers d'A1/A1b, índex a offset_RGB


def gsmooth(a, s):
    k = int(6 * s) | 1
    return cv2.GaussianBlur(np.asarray(a, np.float32), (k, k), s, borderType=cv2.BORDER_REPLICATE)


def norm_smooth(val, wgt, s, fill=True, min_den=0.05):
    num = gsmooth(val * wgt, s); den = gsmooth(wgt, s)
    out = np.where(den > min_den * max(float(den.max()), 1e-30), num / np.maximum(den, 1e-20), np.nan).astype(np.float32)
    if fill:
        bad = ~np.isfinite(out)
        if bad.any() and (~bad).any():
            idx = distance_transform_edt(bad, return_distances=False, return_indices=True)
            out = out[idx[0], idx[1]]
    return out


def fields(group):
    tag, grp = GROUPS[group]
    meta = json.loads((CAU36 / f'{tag}_meta.json').read_text())['frames']
    idx = [m['i'] for m in meta if (grp is None or m['group'] == grp)]
    rep = {'group': group, 'sigma_field_px': SIG_FIELD_PX, 'sigma_gauge_px': SIG_GAUGE_PX, 'iterations': ITER, 'frames': [meta[i]['name'] for i in idx], 'channels': {}}
    for c, (suf, ci) in CH.items():
        Wm = np.load(CAU36 / f'{tag}{"_" + suf if suf else ""}_w.npy', mmap_mode='r'); Vm = np.load(CAU36 / f'{tag}{"_" + suf if suf else ""}_v.npy', mmap_mode='r')
        n = len(idx)
        Wt = np.stack([np.asarray(Wm[i]) for i in idx]); L = np.empty_like(Wt)
        plateau = np.zeros_like(Wt, dtype=bool)
        for j, i in enumerate(idx):
            m = meta[i]; v = np.asarray(Vm[i]); b = float(m['offset_RGB'][ci])
            L[j] = np.where(np.isfinite(v) & (Wt[j] > 0), v * m['k'] + b, np.nan)
            plateau[j] = (Wt[j] >= 0.5 * max(m['exp'], 1e-9)) & np.isfinite(L[j]) & (L[j] > 0)
        Wt = np.where(np.isfinite(L) & (L > 0), Wt, 0).astype(np.float32); Lc = np.nan_to_num(L, nan=0.0)
        phi = np.zeros_like(Wt)
        s_f = SIG_FIELD_PX / Q; s_g = SIG_GAUGE_PX / Q
        hist = []
        for it in range(ITER):
            Lcorr = Lc * np.exp(-phi)
            T = np.sum(Wt * Lcorr, axis=0) / np.maximum(np.sum(Wt, axis=0), 1e-20)
            lnT = np.log(np.maximum(T, 1e-20))
            eps = np.zeros_like(Wt); pw = np.zeros_like(Wt)
            for j in range(n):
                p = plateau[j] & (T > 0)
                if p.sum() < 50:
                    continue
                e = np.where(p, np.log(np.maximum(Lcorr[j], 1e-20)) - lnT, 0).astype(np.float32)
                pw[j] = np.where(p, Wt[j], 0)
                ej = norm_smooth(e, pw[j], s_f)
                if not np.isfinite(ej).all():          # cap camp sense suport: fora del gauge i sense correcció
                    ej = np.nan_to_num(ej, nan=0.0); pw[j] = 0
                eps[j] = ej
            spw = np.sum(pw, axis=0)
            gauge = norm_smooth(np.where(spw > 0, np.sum(eps * pw, axis=0) / np.maximum(spw, 1e-20), 0), spw, s_g)   # mitjana ponderada, DESPRÉS suavitzada
            gauge = np.nan_to_num(gauge, nan=0.0)
            d = np.where(Wt > 0, eps - gauge[None], 0).astype(np.float32)
            phi = phi + d
            # residu a l'altiplà: rms de ln(L_corr/T) per fotograma
            res = []
            for j in range(n):
                p = plateau[j] & (T > 0)
                if p.sum() >= 50:
                    res.append(float(np.sqrt(np.mean((np.log(np.maximum(Lcorr[j][p], 1e-20)) - lnT[p]) ** 2))))
            hist.append({'iter': it, 'rms_residu_altipla_mediana_pct': float(100 * np.median(res)) if res else None, 'rms_residu_altipla_max_pct': float(100 * np.max(res)) if res else None,
                         'increment_phi_rms_pct': float(100 * np.sqrt(np.mean(d[Wt > 0] ** 2)))})
            log(f'{group} {c} iter {it}: residu altiplà mediana {hist[-1]["rms_residu_altipla_mediana_pct"]:.3f}% màx {hist[-1]["rms_residu_altipla_max_pct"]:.3f}% · Δφ rms {hist[-1]["increment_phi_rms_pct"]:.3f}%')
        # compost final i comparació
        assert np.isfinite(phi).all(), 'phi no finit'
        Lcorr = Lc * np.exp(-phi); T1 = np.sum(Wt * Lcorr, axis=0) / np.maximum(np.sum(Wt, axis=0), 1e-20)
        T0 = np.sum(Wt * Lc, axis=0) / np.maximum(np.sum(Wt, axis=0), 1e-20)
        np.save(CAU36 / f'{group}_{c}_phi.npy', phi.astype(np.float32))
        np.save(CAU36 / f'{group}_{c}_T0.npy', T0.astype(np.float32)); np.save(CAU36 / f'{group}_{c}_T1.npy', T1.astype(np.float32))
        sup = np.sum(Wt, axis=0) > 0
        ratio = np.where(sup & (T0 > 0) & (T1 > 0), np.log(np.maximum(T1, 1e-20) / np.maximum(T0, 1e-20)), 0)
        per_frame = []
        for j, i in enumerate(idx):
            p = plateau[j]
            per_frame.append({'name': meta[i]['name'], 'exp': meta[i]['exp'], 'phi_p5_p50_p95_pct': [float(100 * np.percentile(phi[j][p], q)) for q in (5, 50, 95)] if p.sum() else None,
                              'phi_rms_pct': float(100 * np.sqrt(np.mean(phi[j][p] ** 2))) if p.sum() else None, 'plateau_cells': int(p.sum())})
        rep['channels'][c] = {'history': hist, 'per_frame': per_frame, 'compost_canvi_ln_p1_p50_p99_pct': [float(100 * np.percentile(ratio[sup], q)) for q in (1, 50, 99)],
                              'compost_canvi_rms_pct': float(100 * np.sqrt(np.mean(ratio[sup] ** 2)))}
        log(f'{group} {c}: canvi del compost ln p1/p50/p99 = {rep["channels"][c]["compost_canvi_ln_p1_p50_p99_pct"]} %')
        del Wm, Vm, Wt, L, Lc, Lcorr, plateau, phi, eps, pw
    savejson(REB36 / f'B1_camps_{group}.json', rep)
    return rep


def main():
    for g in GROUPS:
        fields(g)
    log('B1 fet')


if __name__ == '__main__':
    main()
