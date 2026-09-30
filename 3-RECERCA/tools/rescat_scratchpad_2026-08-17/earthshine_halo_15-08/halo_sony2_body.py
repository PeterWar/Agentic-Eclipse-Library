# ── ajust conjunt: DOS nuclis (ales properes + dispersio ampla) + pla de cel + LROC ──
log("retalls i fonts...")
obs8, src8 = {}, {}
for n in CIENCIA["8s"]:
    obs8[n] = crop(n)[0]
    src8[n], ref_exp, nsat = source_map(GROUP_OF[n])
NARROW = [(s, b_) for s in (1.5, 3, 6, 12, 24) for b_ in (0.6, 1.0, 1.5)]
WIDE = [(s, b_) for s in (40, 80, 160, 320, 640) for b_ in (0.6, 1.0, 1.5, 2.5)]
log(f"precalcul de {len(NARROW)+len(WIDE)} convolucions x 2 fotogrames...")
CONV = {}
for k in NARROW + WIDE:
    KF = kernel_fft(*k)
    for n in CIENCIA["8s"]:
        CONV[(k, n)] = convolve(src8[n], KF)
X1 = (xx-N/2)/N; Y1 = (yy-N/2)/N
def design(k1, k2, with_lroc=True, with_plane=True):
    rows, rhs = [], []
    for i, n in enumerate(CIENCIA["8s"]):
        m = fitmask
        cols = [CONV[(k1, n)][m], CONV[(k2, n)][m]]
        if with_lroc: cols.append(LROCn[m])
        if with_plane: cols += [X1[m], Y1[m]]
        cols += [np.ones(m.sum()) if j == i else np.zeros(m.sum()) for j in range(2)]
        rows.append(np.stack(cols, 1)); rhs.append(obs8[n][m])
    return np.vstack(rows), np.concatenate(rhs)
best = None
for k1 in NARROW:
    for k2 in WIDE:
        Amat, bvec = design(k1, k2)
        sol, *_ = np.linalg.lstsq(Amat, bvec, rcond=None)
        rms = float(np.sqrt(np.mean((bvec-Amat@sol)**2)))
        if sol[0] < 0 or sol[1] < 0: rms += 1e6      # amplituds fisiques
        if best is None or rms < best[0]: best = (rms, k1, k2, sol)
rms, k1, k2, sol = best
A1, A2, bL = sol[0], sol[1], sol[2]
log(f"MILLOR 2 nuclis: proper s={k1[0]} beta={k1[1]} A1={A1:.4f} · ample s={k2[0]} beta={k2[1]} A2={A2:.4f} · b_LROC={bL:.1f} · pla=({sol[3]:.0f},{sol[4]:.0f}) · c={sol[5]:.0f},{sol[6]:.0f} · rms={rms:.1f}")
for tag, kw in (("sense LROC", dict(with_lroc=False)), ("sense pla", dict(with_plane=False))):
    Amat, bvec = design(k1, k2, **kw); s2, *_ = np.linalg.lstsq(Amat, bvec, rcond=None)
    log(f"   control {tag}: rms={float(np.sqrt(np.mean((bvec-Amat@s2)**2))):.1f}")
halo8 = {n: A1*CONV[(k1, n)] + A2*CONV[(k2, n)] for n in CIENCIA["8s"]}
log(f"pedestal de halo al centre del disc: {np.mean([halo8[n][N//2-5:N//2+5, N//2-5:N//2+5].mean() for n in CIENCIA['8s']]):.0f} ADU16 · a r=250 (plena): {np.mean([halo8[n][(rr>123)&(rr<127)].mean() for n in CIENCIA['8s']]):.0f}")
log(f"earthshine mitja al disc (8 s): b*mean(LROC)= {bL:.0f} ADU16  (positiu = fisic)")
KF1, KF2 = kernel_fft(*k1), kernel_fft(*k2)
plane = sol[3]*X1 + sol[4]*Y1

def emap(name):
    b, _ = crop(name)
    src, ref_exp, _ = source_map(GROUP_OF[name])
    scaled = src*(expo[name]/ref_exp)
    halo = A1*convolve(scaled, KF1) + A2*convolve(scaled, KF2)
    E = (b - halo - plane*(expo[name]/8.0))/expo[name]
    E[~disc] = 0
    E[disc] -= np.median(E[inner])
    return E
def hf_noise(E):
    d = E - gaussian_filter(E, 2.5); return float(d[inner].std())
def ncc(a, b, m):
    a = a[m]-a[m].mean(); b = b[m]-b[m].mean()
    return float(np.sum(a*b)/np.sqrt(np.sum(a*a)*np.sum(b*b)))
gate_mask = rr < 120
LROCz = LROCn.copy(); LROCz[~disc] = 0
def hp(img, sg=25): return gaussian_filter(img, 1.5) - gaussian_filter(img, sg)
def r_full(Emap): return ncc(gaussian_filter(Emap, 1.5), gaussian_filter(LROCz, 1.5), gate_mask)
def r_hp(Emap): return ncc(hp(Emap), hp(LROCz), gate_mask)
E, sig = {}, {}
for lay in ("8s", "2s", "1s"):
    for n in CIENCIA[lay]:
        E[n] = emap(n); sig[n] = hf_noise(E[n])
ref = (E["DSC06987"]/sig["DSC06987"]**2 + E["DSC06993"]/sig["DSC06993"]**2)/(1/sig["DSC06987"]**2 + 1/sig["DSC06993"]**2)
def r_ref(Emap): return ncc(hp(Emap), hp(ref), gate_mask)
log("porta per capa:")
num = np.zeros((N, N)); den = 0.0; stacks = {}
for lay in ("8s", "2s", "1s"):
    for n in CIENCIA[lay]:
        log(f"  {lay} {n}: sigma={sig[n]:.1f} ADU16/s · r_hp(ref8)={r_ref(E[n]) if lay!='8s' else float('nan'):.3f} · r_hp(LROC)={r_hp(E[n]):.3f} · r_full(LROC)={r_full(E[n]):.3f}")
    for n in CIENCIA[lay]:
        num += E[n]/sig[n]**2; den += 1/sig[n]**2
    stk = num/den; stacks[lay] = stk.copy()
    log(f"  => pila fins {lay}: r_hp(LROC)={r_hp(stk):.3f} · r_full(LROC)={r_full(stk):.3f} · soroll={hf_noise(stk):.2f}")
np.savez(f"{S}/halo_sony_result.npz", A1=A1, A2=A2, k1=k1, k2=k2, b=bL, plane=sol[3:5], rms=rms,
         E=np.stack([E[n] for lay in CIENCIA for n in CIENCIA[lay]]), names=[n for lay in CIENCIA for n in CIENCIA[lay]],
         sig=np.array([sig[n] for lay in CIENCIA for n in CIENCIA[lay]]), stack8=stacks["8s"], stack2=stacks["2s"], stack1=stacks["1s"],
         LROCn=LROCn, ref=ref, halo8=np.stack([halo8[n] for n in CIENCIA["8s"]]), obs8=np.stack([obs8[n] for n in CIENCIA["8s"]]))
tifffile.imwrite(f"{OUT}/earthshine_SONY_halo_model_stack_ADU16_per_s.tif", stacks["1s"].astype(np.float32))
log("etapa 1 (2 nuclis) acabada")
