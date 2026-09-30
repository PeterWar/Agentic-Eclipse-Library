"""C0 · Mapa de resolució de la V33, MESURAT: on els dos trens deixen de compartir estructura.

Com coherent_resolution.py de la V29 (tessel·les de 512 px, bandes de Fourier 8–16 … 128–256 px,
correlació entre parelles INDEPENDENTS amb nul per desplaçament de fase), però sobre les fonts
V32 i amb dues parelles: Sony A × Sony B (dos apuntaments) i Vixen × Sony B (dos telescopis).
Banda detectada = correlació > max(0,12; nul + 0,10) en alguna parella. σ_cap = 0,073·λ_min
de la banda més fina detectada. Si cap banda fins a 256 px no és coherent: σ = SMAX_MAP (32 px).
Pas de 256 px; interpolació bilineal; cap radi. Sortida: cau/resolucio_v33.npy i rebut."""
from comu33 import *
SMAX_MAP = 32.0
N, STEP = 512, 256
BANDS = [(8, 16), (16, 32), (32, 64), (64, 128), (128, 256)]


def main():
    V = np.load(CAU32 / 'vixen_total_v32.npy', mmap_mode='r'); A = np.load(CAU32 / 'sony_A_total_v32.npy', mmap_mode='r'); B = np.load(CAU32 / 'sony_B_total_v32.npy', mmap_mode='r')
    mv = np.load(CAUF / 'vixen_support.npy'); ms = np.load(CAUF / 'sony_support.npy'); sup = np.load(CAU32 / 'support_v32.npy')
    fr = np.hypot(np.fft.fftfreq(N)[:, None], np.fft.rfftfreq(N)[None, :]); masks = [(fr >= 1 / b) & (fr < 1 / a) for a, b in BANDS]
    win = np.outer(np.hanning(N), np.hanning(N)); phase = np.exp(2j * np.pi * np.fft.rfftfreq(N)[None, :] * (N / 4))
    ys = list(range(0, H - N + 1, STEP)); xs = list(range(0, W - N + 1, STEP))
    grid = np.full((len(ys), len(xs)), np.nan, np.float32); recs = []
    def fft(z):
        z = np.log(np.maximum(z, 1e-10)); z = z - np.mean(z); return np.fft.rfft2(z * win)
    def corr(a, b, mk):
        av = a[mk]; bv = b[mk]; den = np.sqrt(np.sum(np.abs(av) ** 2) * np.sum(np.abs(bv) ** 2)); return float(np.real(np.vdot(av, bv)) / max(den, 1e-30))
    for iy, y in enumerate(ys):
        for ix, x in enumerate(xs):
            sl = (slice(y, y + N), slice(x, x + N)); s_ok = sup[sl].mean()
            if s_ok < 0.5:
                continue
            bb = np.asarray(B[sl + (1,)]); aa = np.asarray(A[sl + (1,)]); vv = np.asarray(V[sl + (1,)])
            okB = np.isfinite(bb) & (bb > 0) & ms[sl]; okA = np.isfinite(aa) & (aa > 0) & ms[sl]; okV = np.isfinite(vv) & (vv > 0) & mv[sl]
            pairs = []
            if okB.mean() > .995 and okA.mean() > .995:
                pairs.append(('AB', fft(aa), fft(bb)))
            if okB.mean() > .995 and okV.mean() > .995:
                pairs.append(('VB', fft(vv), fft(bb)))
            if okA.mean() > .995 and okV.mean() > .995:
                pairs.append(('VA', fft(vv), fft(aa)))
            if not pairs:
                continue
            row = {'xy': [x + N / 2, y + N / 2], 'r_R': float(np.hypot(x + N / 2 - CX, y + N / 2 - CY) / RS), 'pairs': [p[0] for p in pairs], 'bands': []}; selected = None
            for (lo, hi), mk in zip(BANDS, masks):
                det = False; vals = {}
                for name, fa, fb in pairs:
                    c = corr(fa, fb, mk); nul = corr(fa, fb * phase, mk); vals[name] = [c, nul]
                    det |= c > max(.12, nul + .10)
                row['bands'].append({'wavelength_px': [lo, hi], 'corr': vals, 'detected': det})
                if det and selected is None:
                    selected = lo
            grid[iy, ix] = min(SMAX_MAP, .073058 * selected) if selected is not None else SMAX_MAP
            row['sigma'] = float(grid[iy, ix]); recs.append(row)
        log(f'fila {iy + 1}/{len(ys)}')
    # omple les tessel·les sense parella pel veí més proper i interpola
    from scipy.ndimage import distance_transform_edt
    bad = ~np.isfinite(grid)
    if bad.any():
        idx = distance_transform_edt(bad, return_distances=False, return_indices=True); grid = grid[idx[0], idx[1]]
    full = cv2.resize(grid, (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32)
    np.save(CAU33 / 'resolucio_v33.npy', full)
    r, _ = coords(); prof = []
    for a in (1.2, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0, 7.0, 8.0, 9.0, 11.0):
        k = sup & (r >= a * RS) & (r < (a + 0.5) * RS); prof.append({'r': a, 'sigma_p50': float(np.median(full[k])), 'sigma_p10': float(np.percentile(full[k], 10)), 'sigma_p90': float(np.percentile(full[k], 90))})
    savejson(REB33 / 'C0_resolucio.json', {'bands': BANDS, 'tile_px': N, 'step_px': STEP, 'smax_map': SMAX_MAP, 'rule': 'sigma = 0.073058 * shortest coherent wavelength (any independent pair); SMAX_MAP if none', 'perfil': prof, 'tiles': recs, 'grid': grid})
    from PIL import Image
    Image.fromarray(np.uint8(np.clip(full[::4, ::4] / SMAX_MAP, 0, 1) * 255)).save(VIS33 / 'C0_resolucio_v33.png')
    print(json.dumps(prof, indent=0)); log('C0 fet')


if __name__ == '__main__':
    main()
