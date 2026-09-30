# ── FINAL RGB a resolucio plena: ajust de dos nuclis per canal (sense LROC), 2x8 s ──
from scipy.ndimage import zoom as ndzoom
CH = {0: "R", 1: "G", 2: "B"}
def crop_ch(name, ch):
    cx, cy = centres[name]
    img = tifffile.imread(f"{CAL}/{name}_cal.tif")[..., ch].astype(np.float32)
    ci, cj = int(round(cx)), int(round(cy))
    sub = img[cj-HW-4:cj+HW+4, ci-HW-4:ci+HW+4]
    sub = ndshift(sub, (-(cy-cj), -(cx-ci)), order=1, mode="nearest")[4:-4, 4:-4]
    sat = sub > SAT16
    return sub, sub.reshape(N, B, N, B).mean(axis=(1, 3)), sat.reshape(N, B, N, B).max(axis=(1, 3)) > 0
NARROW = [(s, b_) for s in (1.5, 3, 6, 12, 24) for b_ in (0.6, 1.0, 1.5)]
WIDE = [(s, b_) for s in (40, 80, 160, 320, 640) for b_ in (0.6, 1.0, 1.5, 2.5)]
X1 = (xx-N/2)/N; Y1 = (yy-N/2)/N
KFS = {k: kernel_fft(*k) for k in NARROW+WIDE}
full = {}   # (name, ch) -> full-res crop
E_full = np.zeros((2*HW, 2*HW, 3), np.float64)
params = {}
for ch in (0, 1, 2):
    obs, src, fullc = {}, {}, {}
    for n in CIENCIA["8s"]:
        f_, b_, bs_ = crop_ch(n, ch); fullc[n] = f_; obs[n] = b_
        # font del grup, en aquest canal
        names = GROUPS[GROUP_OF[n]]; order = sorted(names, key=lambda q: -expo[q]); ref_exp = expo[order[0]]
        sm = np.full((N, N), np.nan, np.float32)
        for q in order:
            _, bq, bsq = crop_ch(q, ch); sc = bq*(ref_exp/expo[q]); take = np.isnan(sm) & ~bsq; sm[take] = sc[take]
        still = np.isnan(sm)
        if still.any(): _, bq, _ = crop_ch(order[-1], ch); sm[still] = (bq*(ref_exp/expo[order[-1]]))[still]
        sm[disc_src] = 0; src[n] = sm*(expo[n]/ref_exp)
    CONV = {(k, n): convolve(src[n], KFS[k]) for k in NARROW+WIDE for n in CIENCIA["8s"]}
    best = None
    for k1 in NARROW:
        for k2 in WIDE:
            rows, rhs = [], []
            for i, n in enumerate(CIENCIA["8s"]):
                m = fitmask
                cols = [CONV[(k1, n)][m], CONV[(k2, n)][m], X1[m], Y1[m]] + [np.ones(m.sum()) if j == i else np.zeros(m.sum()) for j in range(2)]
                rows.append(np.stack(cols, 1)); rhs.append(obs[n][m])
            Amat, bvec = np.vstack(rows), np.concatenate(rhs)
            sol, *_ = np.linalg.lstsq(Amat, bvec, rcond=None)
            rms = float(np.sqrt(np.mean((bvec-Amat@sol)**2)))
            if sol[0] < 0 or sol[1] < 0: rms += 1e6
            if best is None or rms < best[0]: best = (rms, k1, k2, sol)
    rms, k1, k2, sol = best
    params[CH[ch]] = dict(k1=k1, k2=k2, A1=float(sol[0]), A2=float(sol[1]), rms=rms)
    log(f"canal {CH[ch]}: proper {k1} A1={sol[0]:.4f} · ample {k2} A2={sol[1]:.4f} · rms={rms:.1f}")
    plane = sol[2]*X1 + sol[3]*Y1
    acc = np.zeros((2*HW, 2*HW)); wsum = 0.0
    for i, n in enumerate(CIENCIA["8s"]):
        halo_b = sol[0]*CONV[(k1, n)] + sol[1]*CONV[(k2, n)] + plane + sol[4+i]
        halo_f = ndzoom(halo_b, B, order=1)                       # el model es suau: bilineal
        Ef = (fullc[n] - halo_f)/expo[n]
        sig_f = float((Ef - gaussian_filter(Ef, 4))[gaussian_filter(np.hypot(*np.mgrid[0:2*HW, 0:2*HW]-HW+0.5).astype(float), 0) < 267].std())
        acc += Ef/sig_f**2; wsum += 1/sig_f**2
    E_full[..., ch] = acc/wsum
np.save(f"{S}/E_full_rgb.npy", E_full)
# mascares i sortides
yf, xf = np.mgrid[0:2*HW, 0:2*HW]; rf = np.hypot(xf-HW+0.5, yf-HW+0.5)
disc_f = rf < R_FULL; valid_f = rf < 267
Ev = E_full.copy()
for ch in range(3):
    Ev[..., ch][~disc_f] = 0
tifffile.imwrite(f"{OUTF}/earthshine_FINAL_Sony2x8s_RGB_fullres_ADU16_per_s.tif", Ev.astype(np.float32), photometric="rgb")
# visible: estirament comu als tres canals (conserva el color relatiu), zona r>267 atenuada
lo = np.percentile(E_full[..., 1][valid_f], 0.5); hi = np.percentile(E_full[..., 1][valid_f], 99.7)
vis = np.clip((E_full - lo)/(hi - lo), 0, 1)
vis = np.where(vis <= 0.0031308, 12.92*vis, 1.055*np.power(vis, 1/2.4) - 0.055)
fade = np.clip((R_FULL - rf)/(R_FULL - 267), 0, 1)[..., None]
vis = vis*(0.35 + 0.65*fade); vis[~disc_f] = 0
tifffile.imwrite(f"{OUTF}/earthshine_FINAL_Sony2x8s_RGB_fullres_visible.tif", (vis*65535).astype(np.uint16), photometric="rgb", compression="zlib")
from PIL import Image
Image.fromarray((vis*255).astype(np.uint8)).save(f"{OUTF}/earthshine_FINAL_Sony2x8s_RGB_fullres_visible.png")
json.dump(params, open(f"{OUTF}/earthshine_FINAL_halo_params.json", "w"), indent=1)
log(f"FINAL RGB escrit a {OUTF}: {sorted(os.listdir(OUTF))}")
