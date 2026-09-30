"""F1 (V39) · Revisió de FlamaVermella_BLUR.tif (Pere: FlamaVermella.psb = base lineal V32 + 01 ACHF V33 S/N en Lluminositat 100 % + P01 NRGF V33 S/N en
Lluminositat 80 %; després BlurXTerminator a PixInsight). Pregunta: el detall que apareix és dada o prior de la xarxa?
Mètode: lluminància de les dues TIFF (abans/després de BlurX); jutges INDEPENDENTS: la Vixen ORIGINAL (v29/cau_final, sense correccions) a les
quatre finestres de 3,5/4 R☉ on la base és Sony (les del qa_science), i la Sony corregida (V36) a quatre finestres interiors (1,3–1,8 R☉, on la base és
Vixen). Per bandes (1–2, 2–4, 4–8, 8–16, 16–32 px): correlació amb el jutge de (a) l'abans, (b) el després, (c) el que BlurX ha AFEGIT (després − abans).
Si (c) correlaciona amb el jutge, BlurX ha recuperat dada; si no, ha afegit prior o soroll modelat. També: potència per banda abans/després, i
un retall 1:1 abans | després | afegit | jutge. Només lectura."""
from comu39 import *
from scipy.ndimage import gaussian_filter
from PIL import Image, ImageDraw, ImageFont
Image.MAX_IMAGE_PIXELS = None
A = Path('/Users/USUARI/Downloads/FlamaVermella.tif'); B = Path('/Users/USUARI/Downloads/FlamaVermella_BLUR.tif'); OLD = ROOT / 'research/tools/v29/cau_final'
WIN_OUT = [(5890, 2326), (5089, 5294), (5965, 2120), (5056, 5511)]
WIN_IN = [(int(CX + 1.55 * RS * np.cos(np.radians(a))), int(CY + 1.55 * RS * np.sin(np.radians(a)))) for a in (-135, -45, 45, 135)]
BANDS = [(1, 2), (2, 4), (4, 8), (8, 16), (16, 32)]


def lum(p):
    import tifffile; im = tifffile.imread(str(p)); assert im.dtype == np.uint16 and im.ndim == 3, (im.dtype, im.shape); im = im.astype(np.float32) / 65535.0; return (im[..., 0] + 2 * im[..., 1] + im[..., 2]) / 4   # PIL rebaixa els TIFF RGB de 16 bits a 8: tifffile


def band(z, s1, s2, core):
    return (gaussian_filter(z, s1) - gaussian_filter(z, s2))[core].ravel()


def main():
    la = lum(A); lb = lum(B); d = lb - la; m = np.load(CAU38 / 'support_v38.npy')
    vix = np.load(OLD / 'vixen_total.npy', mmap_mode='r')[..., 1]; son = np.load(ROOT / 'research/tools/v36_20260908/cau/sony_corrected_total_v36.npy', mmap_mode='r')[..., 1]
    rep = {'fitxers': {'abans': str(A), 'despres': str(B)}, 'finestres': {}}; core = np.s_[256:512, 256:512]
    for nom, wins, jut, jname in (('exterior_3.5-4R_jutge_Vixen_original', WIN_OUT, vix, 'Vixen original'), ('interior_1.55R_jutge_Sony', WIN_IN, son, 'Sony corregida V36')):
        rows = {f'{s1}-{s2}': {'corr_abans': [], 'corr_despres': [], 'corr_afegit': [], 'pot_abans': [], 'pot_despres': [], 'pot_afegit': []} for s1, s2 in BANDS}
        for x, y in wins:
            sl = (slice(y - 384, y + 384), slice(x - 384, x + 384)); j = np.log(np.maximum(np.nan_to_num(np.asarray(jut[sl], np.float32)), 1e-9)); ok = m[sl][core].ravel()
            for s1, s2 in BANDS:
                bj = band(j, s1, s2, core)[ok]; ba = band(la[sl], s1, s2, core)[ok]; bb = band(lb[sl], s1, s2, core)[ok]; bd = band(d[sl], s1, s2, core)[ok]
                r = rows[f'{s1}-{s2}']; r['corr_abans'].append(float(np.corrcoef(bj, ba)[0, 1])); r['corr_despres'].append(float(np.corrcoef(bj, bb)[0, 1])); r['corr_afegit'].append(float(np.corrcoef(bj, bd)[0, 1]))
                r['pot_abans'].append(float(np.var(ba))); r['pot_despres'].append(float(np.var(bb))); r['pot_afegit'].append(float(np.var(bd)))
        res = {k: {kk: float(np.mean(v)) for kk, v in r.items()} for k, r in rows.items()}; rep['finestres'][nom] = {'finestres_xy': wins, 'jutge': jname, 'per_banda': res}
        log(nom + ' (jutge ' + jname + '):'); [log(f"  banda {k} px: corr amb el jutge abans {v['corr_abans']:+.3f} → després {v['corr_despres']:+.3f} · l'AFEGIT per BlurX correlaciona {v['corr_afegit']:+.3f} · potència ×{v['pot_despres']/max(v['pot_abans'],1e-30):.2f} (afegit/abans {v['pot_afegit']/max(v['pot_abans'],1e-30):.2f})") for k, v in res.items()]
    savejson(REB39 / 'F1_flama_blurx.json', rep)
    font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 14)
    for nom, (x, y), jut in (('exterior_3.7R', WIN_OUT[1], vix), ('interior_1.55R', WIN_IN[0], son)):
        x0, y0 = x - 256, y - 256; sl = (slice(y0, y0 + 512), slice(x0, x0 + 512)); tiles = []
        for lab, arr in (('abans (FlamaVermella)', la[sl]), ('després (BlurX)', lb[sl]), ('afegit ×5 + 0,5', 0.5 + 5 * d[sl]), ('jutge (ln, passa-alt σ8)', None)):
            if arr is None:
                j = np.log(np.maximum(np.nan_to_num(np.asarray(jut[sl], np.float32)), 1e-9)); hp = j - gaussian_filter(j, 8); arr = 0.5 + hp / (4 * np.std(hp) + 1e-9)
            tiles.append((lab, np.uint8(np.clip(arr, 0, 1) * 255)))
        sheet = Image.new('L', (4 * 512 + 30, 512 + 28), 30); dd = ImageDraw.Draw(sheet)
        for i, (lab, t) in enumerate(tiles): sheet.paste(Image.fromarray(t), (i * 522, 26)); dd.text((i * 522 + 4, 6), f'{lab} · {nom} · x {x0}-{x0+512} y {y0}-{y0+512}', fill=255, font=font)
        sheet.save(VIS39 / f'F1_flama_blurx_{nom}.png')
    log('F1 fet')


if __name__ == '__main__':
    main()
