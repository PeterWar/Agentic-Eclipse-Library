"""Fotometria d'obertura amb corba de creixement sobre les piles (ADU/s,
superficie verda). Dona flux total corregit d'obertura per a cada estrella
identificada."""
import numpy as np, pandas as pd, json

CFG = {
    'sony': dict(img='../sony_stars/F_IMG.npy', imgs=['../sony_stars/IMGA.npy',
                 '../sony_stars/IMGC.npy'], rmax=18, ann=(24, 36), scale=3.2020),
    'r6':   dict(img='../vixen/stack_flux.npy', imgs=[], rmax=18, ann=(24, 36),
                 scale=2.1495),
}


def cog(img, xs, ys, rmax=18, ann=(24, 36)):
    """Corba de creixement: flux acumulat dins de r, fons d'anell restat."""
    H, W = img.shape
    R = np.arange(1, rmax+1)
    out = np.full((len(xs), rmax), np.nan)
    bg = np.full(len(xs), np.nan)
    npx = np.zeros(rmax)
    P = ann[1]+2
    for i, (x, y) in enumerate(zip(xs, ys)):
        xi, yi = int(round(x)), int(round(y))
        if not (P < xi < W-P and P < yi < H-P):
            continue
        st = img[yi-P:yi+P+1, xi-P:xi+P+1].astype(np.float64)
        Y, X = np.mgrid[-P:P+1, -P:P+1]
        rr = np.hypot(X-(x-xi), Y-(y-yi))
        a = (rr >= ann[0]) & (rr < ann[1]) & np.isfinite(st)
        if a.sum() < 50:
            continue
        b = np.median(st[a])
        bg[i] = b
        s = st - b
        for k, r in enumerate(R):
            m = rr <= r
            out[i, k] = s[m].sum()
            npx[k] = m.sum()
    return R, out, bg, npx


def run(tag, tab):
    c = CFG[tag]
    img = np.load(c['img'])
    R, F, bg, npx = cog(img, tab.x.values, tab.y.values, c['rmax'], c['ann'])
    # corba normalitzada de les estrelles brillants
    bright = np.argsort(-tab.flux.values)[:8]
    ref = np.nanmedian(F[bright]/F[bright, 11][:, None], axis=0)   # normalitzat a r=12
    print(f'[{tag}] corba de creixement normalitzada a r=12 px (8 mes brillants):')
    print('   r  :', ' '.join(f'{r:5d}' for r in R[::2]))
    print('   f/f12:', ' '.join(f'{v:5.3f}' for v in ref[::2]))
    return R, F, bg, ref, npx


if __name__ == '__main__':
    res = {}
    for tag in ('sony', 'r6'):
        tab = pd.read_csv(f'final_match_{tag}.csv')
        R, F, bg, ref, npx = run(tag, tab)
        np.savez(f'cog_{tag}.npz', R=R, F=F, bg=bg, ref=ref, npx=npx,
                 det=tab.det.values)
        print()
