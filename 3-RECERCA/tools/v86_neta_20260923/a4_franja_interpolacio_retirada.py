"""a4 · Interpolació declarada de la franja escombrada per la Lluna a cada ràster de filtre (decisió B de Pere, 23-09-2026).
És la versió sistemàtica de la interpolació que Pere va fer a mà el 17-09 (research/165, capa 225): dins de la franja cap filtre té
dada neta, i hi posem una continuació radial del que el filtre mostra just fora.
Per a cada azimut θ (al voltant de la Lluna de presentació, 1440 cel·les de 0,25°):
  A(θ) = mediana del ràster a l'anell d'ancoratge [rb(θ)+μ, rb(θ)+3μ] (rb = vora exterior de la franja, a2).
Capes d'ESTRUCTURA (NRGF, RHEF): dins de la franja, A(θ) suavitzada a 1° i constant al llarg del raig (l'estructura gran continua fins al limbe).
Capes de DETALL (ACHF, WOW, MGN, ACHF angular): dins de la franja NO s'inventa detall: només el nivell local A(θ) suavitzat a 8°.
Transició [rb+μ, rb+3μ]: el ràster calculat s'esvaeix suaument cap a aquest valor (sense dents ni graons). Fora: el ràster calculat, intacte.
(Primera versió del 23-09 a la 1:45: ancoratge fi i rampa de detall; feia dents a la vora de la franja i es va refusar abans de muntar res.)
Les cel·les indefinides del RHEF local fora de la franja (menys de 50 mostres per sector) s'omplen amb la mitjana normalitzada dels veïns (σ 4 px), declarades."""
from v86_comu import *
from v86_operadors import smoothstep, ng
from scipy.ndimage import gaussian_filter1d
claim()
MU = 6.0; NB = 1440; SIG_A = 4.0; SIG_BAIX = 32.0     # μ px; suavitzat azimutal en cel·les de 0,25° (1° estructura, 8° detall)
ESTRUCTURA = ['P01_NRGF', 'P01_NRGF_extrap', 'P02_RHEF', 'P02b_RHEF_ups0.35', 'P02c_RHEF_local60_native', 'P02d_RHEF_local30_native']
DETALL = ['01', '04', '05', '06', '03', '03v30', '07', 'P03_MGN', 'P04_WOW', 'P05_WOW_bilateral']
C = SORT / 'filtres'; F = SORT / 'filtres_finals'; F.mkdir(exist_ok=True)
geo = json.loads((SORT / 'A2_GEOMETRIA.json').read_text())['lluna_presentacio']; g = np.load(SORT / 'A2_geometria.npz'); by0, by1, bx0, bx1 = g['box']
rb = g['rb_s']; cx, cy, R = geo['cx'], geo['cy'], geo['R']
yy, xx = np.mgrid[by0:by1, bx0:bx1]; rL = np.hypot(xx - cx, yy - cy).astype('float32'); th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
ib = (th / 360 * NB).astype(int) % NB; frac_b = (th / 360 * NB - np.floor(th / 360 * NB)).astype('float32')
def interp_az(v):   # valor per cel·la → valor per píxel, interpolat linealment entre cel·les veïnes
    return (1 - frac_b) * v[ib] + frac_b * v[(ib + 1) % NB]
RB = interp_az(rb).astype('float32')
zona = rL < RB + MU; trans = (rL >= RB + MU) & (rL < RB + 3 * MU); anc = trans
wt = smoothstep(rL, RB + MU, RB + 3 * MU).astype('float32')
rep = dict(transicio_px=[MU, 3 * MU], mu_px=MU, cel_les_azimut=NB, suavitzat_A_graus=SIG_A * 360 / NB, suavitzat_baix_graus=SIG_BAIX * 360 / NB, lluna=geo, capes={})
sup = np.load(FONTS / 'support.npy')[by0:by1, bx0:bx1]
for tag in ESTRUCTURA + DETALL:
    u = np.load(C / f'{tag}_u16.npy'); box = u[by0:by1, bx0:bx1].astype('float32') / 65535
    extra = {}
    if tag.endswith('_native'):   # cel·les indefinides del RHEF local fora de la zona interpolada
        q = np.load(C / f'{tag}_float.npy', mmap_mode='r')[by0:by1, bx0:bx1]; und = sup & ~np.isfinite(q) & ~zona & ~trans
        full_und = np.load(FONTS / 'support.npy') & ~np.isfinite(np.load(C / f'{tag}_float.npy', mmap_mode='r')); full_und[by0:by1, bx0:bx1] &= ~(zona | trans)
        extra['indefinides_fora_franja'] = int(full_und.sum())
        if full_und.any():
            uf = u.astype('float32') / 65535; ok = np.load(FONTS / 'support.npy') & ~full_und; fill = ng(uf, ok, 4.0); uf[full_und] = fill[full_und]; u = np.round(np.clip(uf, 0, 1) * 65535).astype('uint16')
            box = u[by0:by1, bx0:bx1].astype('float32') / 65535
    # ancoratge per cel·la: mediana a l'anell [rb+μ, rb+3μ]
    A = np.full(NB, np.nan)
    for k in range(NB):
        v = box[anc & (ib == k)]
        if v.size: A[k] = np.median(v)
    ok = np.isfinite(A); A[~ok] = np.interp(np.flatnonzero(~ok), np.flatnonzero(ok), A[ok], period=NB)
    A_s = gaussian_filter1d(A, SIG_A, mode='wrap'); A_b = gaussian_filter1d(A, SIG_BAIX, mode='wrap')
    Apx = interp_az(A_s).astype('float32'); Bpx = interp_az(A_b).astype('float32')
    cont = Apx if tag in ESTRUCTURA else Bpx
    new = box.copy(); new[zona] = cont[zona]; new[trans] = (wt * box + (1 - wt) * cont)[trans]
    out = u.copy(); out[by0:by1, bx0:bx1] = np.round(np.clip(new, 0, 1) * 65535).astype('uint16')
    np.save(F / f'{tag}_u16.npy', out)
    rep['capes'][tag] = dict(tipus='estructura' if tag in ESTRUCTURA else 'detall', px_zona=int(zona.sum()), px_transicio=int(trans.sum()), A_min=float(A.min()), A_max=float(A.max()), sha256=sha(F / f'{tag}_u16.npy'), **extra)
    log(tag + ' franja interpolada')
np.savez_compressed(SORT / 'A4_zona.npz', zona=zona, trans=trans, box=np.array([by0, by1, bx0, bx1]))
desa_json('A4_FRANJA.json', rep); log('A4 fet')
