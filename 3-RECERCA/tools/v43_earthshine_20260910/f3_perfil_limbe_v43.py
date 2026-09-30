"""F3 (V43) · PERFIL DEL LIMBE amb el mateix mètode per a: Brno TSE_2026_530mm_DHS i 400mm_DHS (PNG web, R ≈ 105 px), el compost V42 (base corba + `Earthshine V42 lineal (corba)`
amb la seva màscara), el compost V43 (base corba + `V43 vel ×0,3 + relleu` i + `V43 HDR lineal`) i el POWAAAH3 de Pere (disc + màscara). Mediana azimutal de la luminància sRGB
(mitjana RGB) en anells de 0,005 R de 0,80 a 1,20 R; números: nivell del disc (0,90–0,97 R), nivell de la corona (1,03–1,06 R), amplada de la transició 10–90 % (px i R),
ANELL = desviació màxima a 0,97–1,06 R respecte de la recta entre 0,96 i 1,07 R (% del nivell de corona), GRADIENT dins del disc L(0,95)/L(0,5) i L(0,85)/L(0,5), contrast de
l'earthshine (p95−p5)/mediana a r < 0,85 R després d'un passa-alt (σ 3 px a 1:1, 1 px al web). Sortida: REB43/F3_perfil_limbe.json i vistes F3_perfils_limbe.png."""
from comu43 import *
from scipy.ndimage import gaussian_filter
from PIL import Image
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
DHS = Path('/Users/USUARI/Desktop/Eclipse 2026/Drukmuller fotos finals'); MC = (CX + 14.8, CY + 0.9); RL = 453.5; WIN = 700


def centre_disc(L, guess, R):
    """Centre i radi del disc fosc: píxels amb L < llindar dins d'un cercle generós al voltant de la suposició; després el radi pel perfil (50 % entre disc i corona)."""
    yy, xx = np.mgrid[0:L.shape[0], 0:L.shape[1]]; cx, cy = guess
    for _ in range(3):
        rr = np.hypot(xx - cx, yy - cy); win = rr < 1.3 * R; thr = 0.5 * (np.median(L[rr < 0.7 * R]) + np.median(L[(rr > 1.1 * R) & (rr < 1.3 * R)])); dark = win & (L < thr)
        if dark.sum() < 50: break
        cx, cy = xx[dark].mean(), yy[dark].mean(); R = float(np.sqrt(dark.sum() / np.pi))
    rr = np.hypot(xx - cx, yy - cy); prof = np.array([np.median(L[(rr >= k) & (rr < k + 1)]) for k in range(int(0.8 * R), int(1.2 * R))])
    lvd, lvc = np.median(prof[:max(int(0.1 * R), 2)]), np.median(prof[-max(int(0.1 * R), 2):]); k50 = int(0.8 * R) + int(np.argmax(prof > 0.5 * (lvd + lvc)))
    return cx, cy, float(k50)


def perfil(img, cx, cy, R, hp_sigma):
    L = img.mean(2) if img.ndim == 3 else img; yy, xx = np.mgrid[0:L.shape[0], 0:L.shape[1]]; r = np.hypot(xx - cx, yy - cy) / R
    bins = np.arange(0.80, 1.20, 0.005); p = np.array([np.median(L[(r >= b) & (r < b + 0.005)]) if ((r >= b) & (r < b + 0.005)).sum() > 5 else np.nan for b in bins]); rc = bins + 0.0025
    def at(a, b): return float(np.nanmedian(p[(rc >= a) & (rc < b)]))
    ld, lc = at(0.90, 0.97), at(1.03, 1.06); lo, hi = ld + 0.1 * (lc - ld), ld + 0.9 * (lc - ld)
    i10 = np.argmax(p > lo) if (p > lo).any() else 0; i90 = np.argmax(p > hi) if (p > hi).any() else 0; w = max(rc[i90] - rc[i10], 0.0)
    def mx(a, b): return float(np.nanmax(p[(rc >= a) & (rc < b)]))
    def mn(a, b): return float(np.nanmin(p[(rc >= a) & (rc < b)]))
    anell_clar_fora = (mx(1.0, 1.06) - lc) / max(lc, 1e-6) * 100          # vora clara just fora del limbe (per damunt de l'altiplà de corona)
    anell_fosc_fora = (lc - mn(1.005, 1.03)) / max(lc, 1e-6) * 100        # solc fosc just fora del limbe
    glow_dins = (mx(0.90, 0.995) - at(0.90, 0.95)) / max(lc, 1e-6) * 100  # franja clara dins del limbe (glow), respecte del nivell del disc a 0,90–0,95, en % de la corona
    anell = max(anell_clar_fora, anell_fosc_fora)
    d5 = np.median(L[(r > 0.49) & (r < 0.51)]); g95 = np.median(L[(r > 0.945) & (r < 0.955)]) / max(d5, 1e-6); g85 = np.median(L[(r > 0.845) & (r < 0.855)]) / max(d5, 1e-6)
    inn = r < 0.85; z = L.astype(np.float32); hpz = gaussian_filter(z, hp_sigma) - gaussian_filter(z, 4 * hp_sigma); c = float((np.percentile(hpz[inn], 95) - np.percentile(hpz[inn], 5)) / max(np.median(z[inn]), 1e-6))
    return dict(perfil_r=[float(v) for v in rc], perfil_L=[float(v) if np.isfinite(v) else None for v in p], nivell_disc=ld, nivell_corona=lc, transicio_10_90_R=float(w), transicio_10_90_px=float(w * R), anell_pct_corona=anell, vora_clara_fora_pct=anell_clar_fora, solc_fosc_fora_pct=anell_fosc_fora, glow_dins_pct=glow_dins, gradient_L095_L05=float(g95), gradient_L085_L05=float(g85), contrast_earthshine=c, R_px=float(R), centre=[float(cx), float(cy)])


def main():
    rep = {}; curves = {}
    for nom, fn, guess, Rg in (('Brno 530 mm DHS (web)', 'TSE_2026_530mm_DHS.png', (816, 517), 105), ('Brno 400 mm DHS (web)', 'TSE_2026_400mm_DHS.png', None, None), ('Brno 800 mm (web)', 'TSE2026_Trigaza_800mm.png', None, None)):
        a = np.asarray(Image.open(DHS / fn).convert('RGB')).astype(np.float32) / 255; L = a.mean(2)
        if guess is None:
            yy, xx = np.mgrid[0:L.shape[0], 0:L.shape[1]]; cen = (xx > L.shape[1] * 0.25) & (xx < L.shape[1] * 0.75) & (yy > L.shape[0] * 0.25) & (yy < L.shape[0] * 0.75); dark = cen & (L <= np.percentile(L[cen], 0.7)); guess = (xx[dark].mean(), yy[dark].mean()); Rg = float(np.sqrt(dark.sum() / np.pi)); log(f'{nom}: suposició inicial ({guess[0]:.0f}, {guess[1]:.0f}) R {Rg:.0f}')
        cx, cy, R = centre_disc(L, guess, Rg); rep[nom] = perfil(a, cx, cy, R, 1.0); curves[nom] = rep[nom]; log(f"{nom}: centre ({cx:.1f}, {cy:.1f}) R {R:.1f} px · disc {rep[nom]['nivell_disc']:.3f} corona {rep[nom]['nivell_corona']:.3f} · transició {rep[nom]['transicio_10_90_px']:.1f} px ({rep[nom]['transicio_10_90_R']:.3f} R) · vora clara fora {rep[nom]['vora_clara_fora_pct']:.1f} % · solc fosc fora {rep[nom]['solc_fosc_fora_pct']:.1f} % · glow dins {rep[nom]['glow_dins_pct']:.1f} % · L(0,95)/L(0,5) {rep[nom]['gradient_L095_L05']:.2f} · contrast {100 * rep[nom]['contrast_earthshine']:.1f} %")
    x0, y0 = int(round(MC[0])) - WIN, int(round(MC[1])) - WIN; sl = (slice(y0, y0 + 2 * WIN), slice(x0, x0 + 2 * WIN)); cxt, cyt = MC[0] - x0, MC[1] - y0
    base = np.load(HERE42 / 'cau' / 'base_corba_total_v42_u16.npy', mmap_mode='r')[sl].astype(np.float32) / 65535
    m42 = np.load(HERE42 / 'cau' / 'earthshine_v42_mascara_u16.npy', mmap_mode='r')[sl].astype(np.float32) / 65535; m43 = np.load(CAU43 / 'e43_mascara_u16.npy', mmap_mode='r')[sl].astype(np.float32) / 65535
    comps = {'V42: base + Earthshine V42 lineal (corba)': (HERE42 / 'cau' / 'earthshine_v42_lineal_u16.npy', m42), 'V43: base + vel ×0,3 + relleu 12 %': (CAU43 / 'e43_vel03_relleu12_u16.npy', m43), 'V43: base + HDR lineal (corba)': (CAU43 / 'e43_lineal_u16.npy', m43), 'V43: base + nivell POWAAAH3 + relleu': (CAU43 / 'e43_powaaah3_relleu12_u16.npy', m43), 'V43: base + disc pla fosc + relleu (limbe net)': (CAU43 / 'e43_pla_fosc_relleu12_u16.npy', m43), 'V43: base + disc pla POWAAAH3 + relleu (limbe net)': (CAU43 / 'e43_pla_powaaah3_relleu12_u16.npy', m43)}
    for nom, (fn, mk) in comps.items():
        lay = np.load(fn, mmap_mode='r')[sl].astype(np.float32) / 65535; comp = base * (1 - mk[..., None]) + lay * mk[..., None]; rep[nom] = perfil(comp, cxt, cyt, RL, 3.0); curves[nom] = rep[nom]
        log(f"{nom}: disc {rep[nom]['nivell_disc']:.3f} corona {rep[nom]['nivell_corona']:.3f} · transició {rep[nom]['transicio_10_90_px']:.1f} px ({rep[nom]['transicio_10_90_R']:.3f} R) · vora clara fora {rep[nom]['vora_clara_fora_pct']:.1f} % · solc fosc fora {rep[nom]['solc_fosc_fora_pct']:.1f} % · glow dins {rep[nom]['glow_dins_pct']:.1f} % · L(0,95)/L(0,5) {rep[nom]['gradient_L095_L05']:.2f} · L(0,85)/L(0,5) {rep[nom]['gradient_L085_L05']:.2f} · contrast {100 * rep[nom]['contrast_earthshine']:.1f} %")
    pw = np.load(HERE42 / 'cau' / 'powaaah3_rgb_u16.npy', mmap_mode='r')[sl].astype(np.float32) / 65535; pwm = np.load(HERE42 / 'cau' / 'powaaah3_mascara_disc_u16.npy', mmap_mode='r')[sl].astype(np.float32) / 65535
    comp = base * (1 - pwm[..., None]) + pw * pwm[..., None]; nom = 'POWAAAH3 (Pere) sobre la base'; rep[nom] = perfil(comp, cxt, cyt, RL, 3.0); curves[nom] = rep[nom]
    log(f"{nom}: disc {rep[nom]['nivell_disc']:.3f} corona {rep[nom]['nivell_corona']:.3f} · transició {rep[nom]['transicio_10_90_px']:.1f} px · vora clara fora {rep[nom]['vora_clara_fora_pct']:.1f} % · solc fosc fora {rep[nom]['solc_fosc_fora_pct']:.1f} % · glow dins {rep[nom]['glow_dins_pct']:.1f} % · L(0,95)/L(0,5) {rep[nom]['gradient_L095_L05']:.2f} · contrast {100 * rep[nom]['contrast_earthshine']:.1f} %")
    savejson(REB43 / 'F3_perfil_limbe.json', rep)
    fig, ax = plt.subplots(1, 2, figsize=(15, 6))
    for nom, c in curves.items():
        r_ = np.array(c['perfil_r']); p_ = np.array([np.nan if v is None else v for v in c['perfil_L']]); ax[0].plot(r_, p_, label=nom, lw=1.6 if 'V43' in nom else 1.0, ls='--' if 'Brno' in nom else '-'); ax[1].plot(r_, p_ / max(c['nivell_corona'], 1e-6), lw=1.6 if 'V43' in nom else 1.0, ls='--' if 'Brno' in nom else '-')
    ax[0].set_xlabel('r / R (Lluna)'); ax[0].set_ylabel('luminància sRGB (mediana azimutal)'); ax[0].set_title('Perfil del limbe: Brno (web) i els nostres composts'); ax[0].axvline(1.0, color='k', lw=0.5); ax[0].legend(fontsize=7); ax[0].grid(alpha=.3)
    ax[1].set_xlabel('r / R (Lluna)'); ax[1].set_ylabel('luminància / nivell de corona (1,03–1,06 R)'); ax[1].set_title('Normalitzat a la corona just fora del limbe'); ax[1].axvline(1.0, color='k', lw=0.5); ax[1].set_ylim(0, 1.3); ax[1].grid(alpha=.3)
    fig.tight_layout(); fig.savefig(VIS43 / 'F3_perfils_limbe.png', dpi=130); log(f'figura {VIS43 / "F3_perfils_limbe.png"}')


if __name__ == '__main__':
    main()
