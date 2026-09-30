"""e2 (V106, «LOLA fi») · Reproductibilitat de la vora fina entre grups independents de fotogrames i primera comparació amb LOLA.
Per fotograma: u0(θ) menys harmònics d'ordre ≤ 2 (centre, radi i el·lipse; es treuen per fotograma). Grups: A (0–8, t 15–20 s),
A2 (mitjans 9–17, t 21–29 s), C (curts i mitjans 26–47, t 82–104 s), B (50–66, t 107–118 s). Bandes (longitud d'ona al llarg del limbe):
gran > 4°, mitjana 1–4°, fina 0,5–1° (0,5° = Nyquist dels calaixos de 0,25°)."""
import numpy as np, json, sys
from pathlib import Path
H = Path(__file__).parent
Z = np.load(H / (sys.argv[1] if len(sys.argv) > 1 else 'E1_VORES.npz'))
U = Z["u0"][1]; E = Z["err"][1]; th = Z["theta"]; nF = U.shape[0]; nb = th.size; EXPO = Z["exp"]
GR = {'A': list(range(0, 9)), 'A2': [9, 10, 11, 14, 15, 16, 17], 'C': [26, 27, 28, 29, 32, 33, 34, 35, 38, 39, 40, 41, 44, 45, 46, 47], 'B': list(range(50, 67))}
thr = np.radians(th)
HARM2 = np.stack([np.ones(nb), np.cos(thr), np.sin(thr), np.cos(2 * thr), np.sin(2 * thr)], 1)
def treu_harm(u, w, Hm=HARM2):
    ok = np.isfinite(u) & (w > 0)
    c, *_ = np.linalg.lstsq(Hm[ok] * np.sqrt(w[ok])[:, None], u[ok] * np.sqrt(w[ok]), rcond=None)
    return u - Hm @ c, c
def gsm(x, w, sig_deg):
    """Mitjana gaussiana normalitzada periòdica (σ en graus)."""
    from scipy.ndimage import gaussian_filter1d
    s = sig_deg / 0.25; xw = np.where(w > 0, x * w, 0); ww = np.where(w > 0, w, 0)
    return gaussian_filter1d(xw, s, mode='wrap') / np.maximum(gaussian_filter1d(ww, s, mode='wrap'), 1e-12)
def bandes(x, w):
    x = np.where(w > 0, x, 0.0); L = gsm(x, w, 0.75); M = gsm(x, w, 0.19)
    return {'gran': L, 'mitjana': M - L, 'fina': x - M}
def grup(js):
    S = np.zeros(nb); W = np.zeros(nb)
    for j in js:
        u = U[j]; e = E[j]
        if not np.isfinite(u).any(): continue
        w = np.where(np.isfinite(u) & np.isfinite(e), 1 / np.maximum(e, 0.02) ** 2, 0)
        r, _ = treu_harm(np.nan_to_num(u), w)
        S += w * np.nan_to_num(r); W += w
    return np.where(W > 0, S / np.maximum(W, 1e-30), np.nan), W
def corr(a, b, m):
    m = m & np.isfinite(a) & np.isfinite(b)
    return np.corrcoef(a[m], b[m])[0, 1] if m.sum() > 20 else np.nan
if __name__ == '__main__':
    G = {k: grup(v) for k, v in GR.items()}
    SECT = [(0, 45), (45, 90), (90, 135), (135, 180), (180, 225), (225, 270), (270, 315), (315, 360)]
    print('Correlació entre grups (vora sense ordre ≤ 2), per banda i sector:')
    for a, b in [('A', 'B'), ('A', 'C'), ('C', 'B'), ('A', 'A2'), ('A2', 'B')]:
        ua, wa = G[a]; ub, wb_ = G[b]; m = (wa > 0) & (wb_ > 0)
        Ba = bandes(np.nan_to_num(ua), wa); Bb = bandes(np.nan_to_num(ub), wb_)
        line = f'{a:>2}–{b:<2}: ' + ' '.join(f"{k} ρ {corr(Ba[k], Bb[k], m):+.2f} (rms {np.std(Ba[k][m]):.3f}/{np.std(Bb[k][m]):.3f})" for k in Ba)
        print(line)
        print('      sectors fina+mitjana: ' + ' '.join(f"{lo}-{hi}:{corr(Ba['fina'] + Ba['mitjana'], Bb['fina'] + Bb['mitjana'], m & (th >= lo) & (th < hi)):+.2f}" for lo, hi in SECT))
    # desfasament: correlació A–B en funció del desplaçament angular (lunar = 0; la corona es desplaça segons el moviment de la Lluna)
    ua, wa = G['A']; ub, wb_ = G['B']; C = Z['centres']
    dC = C[GR['B']].mean(0) - C[GR['A']].mean(0); print('moviment del centre lunar B − A (px):', np.round(dC, 2))
    Ba = bandes(np.nan_to_num(ua), wa); Bb = bandes(np.nan_to_num(ub), wb_); xa = Ba['fina'] + Ba['mitjana']; xb = Bb['fina'] + Bb['mitjana']
    for lo, hi in SECT:
        tc = np.radians((lo + hi) / 2); pred = (dC[0] * (-np.sin(tc)) + dC[1] * (-np.cos(tc))) / (452.98 * np.pi / 180)  # graus (desplaçament tangencial de la corona vist des de la Lluna)
        s = (th >= lo) & (th < hi); cc = []
        for L in range(-24, 25):
            yb = np.roll(xb, -L); mb = np.roll(wb_ > 0, -L); cc.append(corr(xa, yb, s & (wa > 0) & mb))
        cc = np.array(cc); Lm = np.nanargmax(cc) - 24
        print(f'  sector {lo}-{hi}: ρ(0) {cc[24]:+.2f}  màxim {np.nanmax(cc):+.2f} a {Lm * 0.25:+.2f}°   (desplaçament solar previst {-pred:+.2f}°)')
    np.savez_compressed(H / 'E2_GRUPS.npz', **{f'u_{k}': G[k][0] for k in G}, **{f'w_{k}': G[k][1] for k in G}, theta=th)
