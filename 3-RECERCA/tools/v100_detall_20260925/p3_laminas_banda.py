"""p3 (V100 detall · PÍXELS) · làmines a 4× (veí més proper, cap remostreig) dels llocs de la banda: V80 | V99 | D29 estirada.
Fila A: V80 i V99 tal com són (Adobe RGB, perfil incrustat) i D29 (verd lineal de tots els fotogrames que veuen el píxel a D_real ≥ 1 px)
estirada: ln G menys la seva mediana a cada distància d dins de la finestra (treu el gradient radial), percentils 1–99.
Fila B: la mateixa aplanada per a V80 i V99 (ln de la lluminància lineal menys la mediana per d), i el SOROLL de D29 (meitat de la
diferència de les dues meitats independents) a la mateixa escala que D29 → on el soroll és tan gran com la textura, D29 no hi pot fer de jutge.
A la fila B, punts cian = cercle de presentació (d 0) i grocs = d 5 px. Magenta fosc = sense dada a D29 (NF 0).
Sortida: 4-RESULTATS/v100_detall_20260925/pixels/L_<lloc>_PA<nnn>_4x.png i L_TOTES_4x.png (fitxers nous)."""
import sys, time
from pathlib import Path
import numpy as np
import tifffile
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, str(Path(__file__).resolve().parent))
from p0_comu_pixels import FIN, SORT, LX, LY, RL, FONTS, llegeix_finestra, ln_lum, geometria, d29_a_finestra

y0, y1, x0, x1 = FIN
K = 4
W, H = 84, 48          # finestra en px natius (al llarg de l'arc × radial aprox.)
LLOCS = [('dalt', 80), ('dalt', 95), ('dalt', 110), ('dalt', 125), ('baixesq', 215), ('baixesq', 230), ('baixesq', 245)]
try:
    FT = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 15)
    FT2 = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 17)
except OSError:
    FT = FT2 = ImageFont.load_default()


def aplana(ln, dd, m):
    """ln menys la mediana per calaix de d (0,5 px) dins de la finestra; només per veure-hi la textura."""
    out = np.full(ln.shape, np.nan)
    b = np.floor(dd * 2).astype(int)
    for k in np.unique(b[m]):
        z = m & (b == k)
        if z.sum() >= 5:
            out[z] = ln[z] - np.median(ln[z])
    return out


def gris(a, lo, hi, m, nodata=(90, 0, 70)):
    v = np.clip((a - lo) / max(hi - lo, 1e-9), 0, 1)
    g = (255 * np.where(np.isfinite(v), v, 0)).astype(np.uint8)
    rgb = np.dstack([g, g, g])
    rgb[~m] = nodata
    return rgb


def amplia(a):
    return np.kron(a, np.ones((K, K, 1), np.uint8))


def guies(img, dd):
    """punts sobre les isolínies d = 0 (cian) i d = 5 (groc), a la imatge ja ampliada."""
    out = img.copy()
    hh, ww = dd.shape
    for dv, col in ((0.0, (0, 230, 255)), (5.0, (255, 220, 0))):
        for yy in range(hh):
            for xx in range(ww):
                if (xx + yy) % 2 == 0 and abs(dd[yy, xx] - dv) < 0.5:
                    cy, cx = yy * K + K // 2, xx * K + K // 2
                    out[cy - 1:cy + 1, cx - 1:cx + 1] = col
    return out


def main():
    SORT.mkdir(parents=True, exist_ok=True)
    icc = bytes(tifffile.TiffFile(FONTS['V80'][0]).pages[0].tags['InterColorProfile'].value)
    d, pa = geometria()
    A = {k: llegeix_finestra(k) for k in ('V80', 'V99')}
    LN = {k: ln_lum(A[k]) for k in A}
    G, Gp, Gs = (d29_a_finestra(k) for k in ('G', 'G_parells', 'G_senars'))
    mG = np.isfinite(G) & (G > 0); mH = mG & (Gp > 0) & (Gs > 0)
    lnG = np.where(mG, np.log(np.where(mG, G, 1)), np.nan)
    soroll = np.where(mH, (np.log(np.where(mH, Gp, 1)) - np.log(np.where(mH, Gs, 1))) / 2, np.nan)
    files = []
    for lloc, p0 in LLOCS:
        # finestra centrada a d = 8 px sobre el cercle de presentació (la banda queda a la meitat interior)
        cxp = LX + (RL + 8) * np.cos(np.radians(p0)) - x0; cyp = LY - (RL + 8) * np.sin(np.radians(p0)) - y0
        ys, xs = int(round(cyp)) - H // 2, int(round(cxp)) - W // 2
        # si la vora lunar és més vertical que horitzontal, girem la finestra (alt × ample) perquè hi càpiga l'arc
        vertical = abs(np.cos(np.radians(p0))) > 0.7
        hh, ww = (W, H) if vertical else (H, W)
        ys, xs = int(round(cyp)) - hh // 2, int(round(cxp)) - ww // 2
        sl = (slice(ys, ys + hh), slice(xs, xs + ww))
        dd = d[sl]
        pan_a, pan_b = [], []
        for k in ('V80', 'V99'):
            pan_a.append(amplia((A[k][sl] / 257).astype(np.uint8)))
            mk = dd > -3
            ap = aplana(LN[k][sl], dd, mk); lo, hi = np.nanpercentile(ap[mk & (dd > 0)], [1, 99])
            pan_b.append(guies(amplia(gris(ap, lo, hi, np.ones_like(mk))), dd))
        mg = mG[sl]
        apG = aplana(lnG[sl], dd, mg)
        ref = mg & (dd > 1)
        lo, hi = np.nanpercentile(apG[ref], [1, 99]) if ref.sum() > 20 else (-0.05, 0.05)
        pan_a.append(amplia(gris(apG, lo, hi, mg)))
        sr = soroll[sl]; sc = (hi - lo) / 2
        pan_b.append(guies(amplia(gris(sr, -sc, sc, mH[sl])), dd))
        sep = np.full((hh * K, 6, 3), 255, np.uint8)
        fa = np.hstack([pan_a[0], sep, pan_a[1], sep, pan_a[2]]); fb = np.hstack([pan_b[0], sep, pan_b[1], sep, pan_b[2]])
        cap = 48
        tot = np.full((cap + fa.shape[0] + 6 + fb.shape[0], fa.shape[1], 3), 255, np.uint8)
        tot[cap:cap + fa.shape[0]] = fa; tot[cap + fa.shape[0] + 6:] = fb
        im = Image.fromarray(tot); dr = ImageDraw.Draw(im)
        pw = ww * K + 6
        dr.text((4, 2), f'PA {p0}° · {"dalt" if lloc == "dalt" else "baix-esquerra"} · 4×', fill=(0, 0, 0), font=FT2)
        estret = pw < 300
        for i, t in enumerate(['V80 (17-09)', 'V99', 'D29 estirada' if estret else 'D29 estirada (dada real, verd)']):
            dr.text((i * pw + 4, 26), t, fill=(0, 0, 0), font=FT)
        for i, t in enumerate(['V80 aplanada', 'V99 aplanada', 'soroll D29' if estret else 'soroll de D29 (meitats), mateixa escala']):
            dr.text((i * pw + 4, cap + fa.shape[0] + 8), t, fill=(255, 255, 255), font=FT)
        f = SORT / f'L_{lloc}_PA{p0:03d}_4x.png'
        if f.exists():
            f = SORT / f'L_{lloc}_PA{p0:03d}_4x_{int(time.time())}.png'
        im.save(f, icc_profile=icc)
        files.append(im)
        print('fet', f, im.size)
    # full de totes (les de dalt i les de baix-esquerra, apilades)
    wmax = max(i.size[0] for i in files); htot = sum(i.size[1] + 10 for i in files)
    fulla = Image.new('RGB', (wmax, htot), (255, 255, 255)); yy = 0
    for i in files:
        fulla.paste(i, (0, yy)); yy += i.size[1] + 10
    f = SORT / 'L_TOTES_4x.png'
    if f.exists():
        f = SORT / f'L_TOTES_4x_{int(time.time())}.png'
    fulla.save(f, icc_profile=icc); print('fet', f, fulla.size)


if __name__ == '__main__':
    main()
