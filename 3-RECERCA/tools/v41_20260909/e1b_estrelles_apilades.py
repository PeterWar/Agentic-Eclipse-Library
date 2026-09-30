"""E1b (V41) · La PSF REAL de les estrelles, apilada: a la base lineal cada estrella del catàleg és a S/N ~1–2 per píxel (research/124: «al cru són a ~1σ del gra
correlacionat»), o sigui que els moments d'una estrella sola mesuren el gra, no l'estrella. Aquí s'apilen els 37 retalls (centres del catàleg, sub-píxel, pesats
per flux) per tren i per filtre, amb un CONTROL NUL (mateixos retalls desplaçats +40 px): el que surt a l'apilat i no al nul és l'estrella.
Sortides: REB41/E1b_psf_apilada.json; VIS41/E1b_psf_apilada.png (fusió/Vixen/Sony/nul + resposta apilada de cada filtre, ×6, mateixa escala per fila);
VIS41/E1b_galeria_12.png (les 12 estrelles més brillants a 1:1 amb el nul al costat)."""
from comu41 import *
import cv2
from scipy.ndimage import shift as ndshift
SONY36 = ROOT / 'research/tools/v36_20260908/cau/sony_corrected_total_v36.npy'; PC38 = ROOT / 'research/tools/v38_20260908/purs/cau'
STARS = Path('/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/bb2a9ec7-d793-44f1-a277-703c16855cd4/scratchpad/estrelles_v39.json')
FILTRES = {'01 ACHF fi 2-32': CAU38 / '01_v38_u16.npy', '04 ACHF micro 1-16': CAU38 / '04_v38_u16.npy', '05 ACHF fi 2-48': CAU38 / '05_v38_u16.npy', '06 ACHF estructura 4-64': CAU38 / '06_v38_u16.npy',
           'P03 MGN': PC38 / 'P03_MGN_u16.npy', 'P04 WOW': PC38 / 'P04_WOW_u16.npy', 'P05 WOW bilateral': PC38 / 'P05_WOW_bilateral_u16.npy', 'P01 NRGF': PC38 / 'P01_NRGF_u16.npy', 'P02 RHEF': PC38 / 'P02_RHEF_u16.npy'}
R = 24; NUL = (40, 0)


def retall(arr, cx, cy, c=None, dx=0, dy=0):
    x, y = int(round(cx)) + dx, int(round(cy)) + dy; y0, y1, x0, x1 = y - R - 1, y + R + 2, x - R - 1, x + R + 2
    if y0 < 0 or x0 < 0 or y1 > H or x1 > W: return None
    s = arr[y0:y1, x0:x1]; s = s[..., c] if (c is not None and s.ndim == 3) else s; s = np.asarray(s, np.float64)
    if not np.isfinite(s).all(): return None
    fx, fy = (cx - round(cx)), (cy - round(cy)); s = ndshift(s, (-fy, -fx), order=1, mode='nearest'); return s[1:-1, 1:-1]


def fons_i_sigma(s):
    yy, xx = np.mgrid[-R:R + 1, -R:R + 1]; rr = np.hypot(xx, yy); an = (rr >= 14) & (rr <= 24); bg = np.median(s[an]); sd = 1.4826 * np.median(np.abs(s[an] - bg)); return bg, max(sd, 1e-12), rr


def moments(d, rr, rmax=6):
    yy, xx = np.mgrid[-R:R + 1, -R:R + 1]; w = np.where((rr <= rmax) & (d > 0), d, 0); W_ = w.sum()
    if W_ <= 0: return {}
    mx, my = (w * xx).sum() / W_, (w * yy).sum() / W_; cxx = (w * (xx - mx) ** 2).sum() / W_; cyy = (w * (yy - my) ** 2).sum() / W_; cxy = (w * (xx - mx) * (yy - my)).sum() / W_
    tr, det = cxx + cyy, cxx * cyy - cxy ** 2; q = np.sqrt(max(tr * tr / 4 - det, 0)); l1, l2 = tr / 2 + q, tr / 2 - q; ang = 0.5 * np.degrees(np.arctan2(2 * cxy, cxx - cyy))
    # FWHM directes (perfil pel pic): amplada a mig màxim al llarg dels eixos principals
    return dict(fwhm_major=float(2.355 * np.sqrt(max(l1, 0))), fwhm_menor=float(2.355 * np.sqrt(max(l2, 0))), elongacio=float(np.sqrt(l1 / l2)) if l2 > 0 else float('nan'), angle_deg=float(ang), centre=[float(mx), float(my)])


def apila(arr, stars, c=None, nul=False, pesos=None):
    """suma pesada de retalls normalitzats pel fons local; retorna (apilat en unitats de σ del fons local mitjà, n, nul)"""
    acc = np.zeros((2 * R + 1, 2 * R + 1)); wsum = 0.0; n = 0
    for i, st in enumerate(stars):
        s = retall(arr, st['cx'], st['cy'], c, *(NUL if nul else (0, 0)))
        if s is None: continue
        bg, sd, rr = fons_i_sigma(s); d = (s - bg) / sd; w = 1.0 if pesos is None else pesos[i]; acc += w * d; wsum += w; n += 1
    return (acc / max(wsum, 1e-12), n) if n else (None, 0)


def main():
    stars = json.loads(STARS.read_text()); r, t = coords()
    F = np.load(CAU38 / 'fusion_total_v38.npy', mmap_mode='r'); V = np.load(CAU38 / 'vixen_total_v38.npy', mmap_mode='r'); S = np.load(SONY36, mmap_mode='r'); WV = np.load(CAU38 / 'weight_vixen_v38.npy', mmap_mode='r')
    for st in stars: x, y = int(round(st['cx'])), int(round(st['cy'])); st['r_R'] = float(r[y, x] / RS); st['pes_vixen'] = float(np.nan_to_num(WV[y, x]))
    # només estrelles fora de la corona brillant (r > 2,2 R☉) i lluny de la vora del llenç
    sel = [s for s in stars if s['r_R'] > 2.2 and R + 2 < s['cx'] < W - R - 2 and R + 2 < s['cy'] < H - R - 2]; log(f'{len(stars)} estrelles del catàleg; {len(sel)} a r > 2,2 R☉ i dins del llenç')
    selV = [s for s in sel if s['pes_vixen'] > 0.3]; selS = sel
    rep = dict(n_cataleg=len(stars), n_usades=len(sel), n_vixen=len(selV)); pan = {}
    for nom, arr, c, ss in (('fusio', F, 1, sel), ('vixen', V, 1, selV), ('sony', S, 1, selS)):
        ap, n = apila(arr, ss, c); nu, _ = apila(arr, ss, c, nul=True)
        if ap is None: rep[nom] = None; continue
        bg, sd, rr = fons_i_sigma(ap); d = ap - bg; pic = float(d[rr <= 3].max()); m = moments(d, rr); bgn, sdn, _ = fons_i_sigma(nu); picn = float((nu - bgn)[rr <= 3].max())
        # S/N de l'apilat: pic sobre la dispersió de l'anell de l'apilat (que ja porta l'1/√n)
        rep[nom] = dict(n=n, pic_apilat_sigma=pic, pic_nul_sigma=picn, snr_apilat=pic / sd, snr_nul=picn / sdn, flux_r4=float(d[rr <= 4].sum()), **m); pan[nom] = (d, sd); pan[nom + ' NUL'] = (nu - bgn, sdn)
        log(f"{nom}: {n} estrelles apilades · pic {pic:.2f} σ-píxel (nul {picn:.2f}) · S/N apilat {pic / sd:.1f} (nul {picn / sdn:.1f}) · FWHM {m.get('fwhm_major', float('nan')):.1f} × {m.get('fwhm_menor', float('nan')):.1f} px · elongació {m.get('elongacio', float('nan')):.2f} · angle {m.get('angle_deg', float('nan')):+.0f}°")
    # per estrella (fusió): flux d'obertura r ≤ 4 en σ-píxel, per veure quines dominen
    fl = []
    for st in sel:
        s = retall(F, st['cx'], st['cy'], 1)
        if s is None: continue
        bg, sd, rr = fons_i_sigma(s); d = (s - bg) / sd; fl.append(dict(x=int(st['cx']), y=int(st['cy']), r_R=round(st['r_R'], 2), flux_r4_sigma=float(d[rr <= 4].sum()), pic_sigma=float(d[rr <= 3].max())))
    fl.sort(key=lambda d: -d['flux_r4_sigma']); rep['per_estrella_fusio'] = fl; log('flux d\'obertura (σ-píxel, r ≤ 4) de les 8 més brillants: ' + ', '.join(f"{d['flux_r4_sigma']:.0f}" for d in fl[:8]) + f" · mediana {np.median([d['flux_r4_sigma'] for d in fl]):.0f} · nul esperat 0 ± {np.sqrt(np.pi * 16):.0f}")
    # filtres: resposta apilada (en σ del fons local del filtre) i nul
    rep['filtres'] = {}
    for k, p in FILTRES.items():
        if not p.exists(): continue
        arr = np.load(p, mmap_mode='r'); ap, n = apila(arr, sel); nu, _ = apila(arr, sel, nul=True)
        if ap is None: continue
        bg, sd, rr = fons_i_sigma(ap); d = ap - bg; bgn, sdn, _ = fons_i_sigma(nu); dn = nu - bgn
        prof = [float(np.mean(d[(rr >= a) & (rr < a + 1)])) for a in range(0, 16)]
        rep['filtres'][k] = dict(n=n, centre_sigma=float(d[rr <= 1.5].mean()), minim_anell_sigma=float(min(prof[2:12])), radi_minim_px=int(2 + np.argmin(prof[2:12])), perfil_radial_sigma=prof, centre_nul_sigma=float(dn[rr <= 1.5].mean()), minim_anell_nul_sigma=float(min([float(np.mean(dn[(rr >= a) & (rr < a + 1)])) for a in range(2, 12)])))
        pan[k] = (d, sd); log(f"{k:24s}: centre {rep['filtres'][k]['centre_sigma']:+.2f} σ (nul {rep['filtres'][k]['centre_nul_sigma']:+.2f}) · anell fosc {rep['filtres'][k]['minim_anell_sigma']:+.2f} σ a r={rep['filtres'][k]['radi_minim_px']} px (nul {rep['filtres'][k]['minim_anell_nul_sigma']:+.2f})")
    savejson(REB41 / 'E1b_psf_apilada.json', rep)
    # panell: cada apilat ×6, escala ±max|apilat| pròpia per a base i fixa (±1 σ-píxel mitjà) per als filtres
    keys = list(pan); T = 2 * R + 1; Z = 6; cols = 4; rows = (len(keys) + cols - 1) // cols; canvas = np.full((rows * (T * Z + 28), cols * (T * Z + 6), 3), 25, np.uint8)
    for i, k in enumerate(keys):
        d, sd = pan[k]; esc = float(np.abs(d).max()) if 'NUL' not in k and k in ('fusio', 'vixen', 'sony') else float(max(np.abs(pan.get(k.replace(' NUL', ''), pan[k])[0]).max(), 1e-6)) if 'NUL' in k else 1.0
        img = np.clip((d / esc + 1) / 2 * 255, 0, 255).astype(np.uint8); tile = cv2.resize(img, (T * Z, T * Z), interpolation=cv2.INTER_NEAREST); rr_, cc_ = divmod(i, cols); y0, x0 = rr_ * (T * Z + 28) + 24, cc_ * (T * Z + 6)
        canvas[y0:y0 + T * Z, x0:x0 + T * Z] = tile[..., None]; cv2.putText(canvas, f'{k}  (+-{esc:.2g} sigma-pixel)', (x0 + 4, y0 - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.imwrite(str(VIS41 / 'E1b_psf_apilada.png'), canvas)
    # galeria 12: fusió (σ-píxel, ±5) i nul al costat, 1:1 ×4
    g = fl[:12]; Z = 4; canvas = np.full((len(g) * (T * Z + 6), 2 * (T * Z + 6) + 260, 3), 25, np.uint8)
    for i, d_ in enumerate(g):
        for j, (dx, dy) in enumerate(((0, 0), NUL)):
            s = retall(F, d_['x'], d_['y'], 1, dx, dy); bg, sd, rr = fons_i_sigma(s); img = np.clip(((s - bg) / sd / 5 + 1) / 2 * 255, 0, 255).astype(np.uint8); tile = cv2.resize(img, (T * Z, T * Z), interpolation=cv2.INTER_NEAREST)
            y0, x0 = i * (T * Z + 6), 260 + j * (T * Z + 6); canvas[y0:y0 + T * Z, x0:x0 + T * Z] = tile[..., None]
        cv2.putText(canvas, f"({d_['x']},{d_['y']}) {d_['r_R']:.1f}R flux {d_['flux_r4_sigma']:.0f}s", (4, i * (T * Z + 6) + T * Z // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 255, 200), 1)
    cv2.putText(canvas, 'estrella (fusio, +-5 sigma-pixel)  |  nul +40 px', (260, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1); cv2.imwrite(str(VIS41 / 'E1b_galeria_12.png'), canvas); log('E1b fet')


if __name__ == '__main__':
    main()
