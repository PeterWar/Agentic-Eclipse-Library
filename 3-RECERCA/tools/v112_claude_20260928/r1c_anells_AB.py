"""r1c · V113 (variant de r1: r_sol mínim i grau del camp suau com a arguments, ρ_sensor < 3800) (Claude, 28-09-2026): anells de la Sony, fixos a l'òptica, mesurats amb els dos apuntaments.
Hipòtesi: les llums de la Sony porten un patró radial p(ρ) centrat a l'eix òptic que el FLAT_RADIAL (centrat al centre DECLARAT del sensor)
no treu. Com que A i B veuen el mateix cel amb l'eix a llocs diferents del llenç, al solapament
    D(x) = ln A(x) − ln B(x) = p(|x − cA|) − p(|x − cB|) + s(x)
on s és un camp suau (canvi del cel entre èpoques, guany). cA, cB = centre del sensor de cada apuntament portat al llenç + un desplaçament Δ
COMÚ (l'eix és fix al sensor). p: lineal a trossos, nodes cada 20 px de llenç; s: polinomi 2D de grau 4. Regularització de 2a diferència feble.
p només queda determinat llevat de c0 + c2 ρ² + c4 ρ⁴ (degenerat amb s): es declara i se'n treu la part suau abans d'aplicar-lo.
Validació: ajust amb la meitat dels blocs (escaquer de 512 px) i predicció a l'altra meitat; cerca de Δ en una graella fixa, triada per la
meitat d'ajust i avaluada a la de prova. Ús: r1_anells_AB.py [canal 0|1|2] → 4-RESULTATS/v112_claude_20260928/anells/"""
from pathlib import Path
import sys, json, time
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import lsqr
from scipy import ndimage as ndi
R = Path(__file__).resolve().parents[3]
F = R / '4-RESULTATS/v108_20260926/flat2d_v5/apilats'
O = R / '4-RESULTATS/v112_claude_20260928/anells'; O.mkdir(parents=True, exist_ok=True)
CH = int(sys.argv[1]) if len(sys.argv) > 1 else 1
RSUN_MIN = float(sys.argv[2]) if len(sys.argv) > 2 else 4.0; GRAU = int(sys.argv[3]) if len(sys.argv) > 3 else 6
B = 8; H, W = 7506, 10551; h, w = H // B, W // B
CX_L, CY_L, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736
# centres declarats del sensor (4000, 2660) portats al llenç final (F1.2/F1.3 + M_llenc_a_v23), vegeu el rebut
CA0 = np.array([4879.4, 2549.9]); CB0 = np.array([5355.4, 3545.0])
t0 = time.time()

def binq(a):
    return np.asarray(a[:h*B, :w*B], np.float64).reshape(h, B, w, B).mean((1, 3))

A = np.load(F / 'sony_A_total.npy', mmap_mode='r'); Ad = np.load(F / 'sony_A_den.npy', mmap_mode='r')
Bt = np.load(F / 'cau/sony_B_total_v42.npy', mmap_mode='r')
Bw = np.load(R / '4-RESULTATS/v97_refundacio_20260924/cadena_raw/b2_sony_B/cau/sony_B_weights_v42.npy', mmap_mode='r')
a = binq(A[..., CH]); b = binq(Bt[..., CH])
va = (np.asarray(Ad[:h*B, :w*B]) > 0).reshape(h, B, w, B).all((1, 3))
vb = (np.asarray(Bw[:h*B, :w*B, CH]) > 0).reshape(h, B, w, B).all((1, 3))
stars = np.load(R / '4-RESULTATS/v108_20260926/flat2d_v5/fusio/d4/products/sources/star_footprints.npy', mmap_mode='r')
st = (np.asarray(stars[:h*B, :w*B]) > 0).reshape(h, B, w, B).any((1, 3))
yy, xx = np.mgrid[0:h, 0:w]; X = xx * B + B / 2; Y = yy * B + B / 2
rsun = np.hypot(X - CX_L, Y - CY_L) / RL
fA = binq(np.load(R / '4-RESULTATS/v98_20260925/cadena_v98/b3/cau/sony_fA_v42.npy', mmap_mode='r'))
ghost = np.hypot(X - 4853, Y - 2531) < 260       # la taca de l'eix d'A (pes 0 a la fusió)
ok = va & vb & ~st & (a > 0) & (b > 0) & (rsun > RSUN_MIN) & ~ghost
ok = ndi.binary_erosion(ok, iterations=6)
ok &= (np.hypot(X - CA0[0] - 30, Y - CA0[1] - 200) < 5660) & (np.hypot(X - CB0[0] - 30, Y - CB0[1] - 200) < 5660)          # 48 px lluny de les vores de dada
D = np.where(ok, np.log(np.maximum(a, 1e-12)) - np.log(np.maximum(b, 1e-12)), 0)
# rebuig robust de valors extrems (estrelles no catalogades, raigs còsmics residuals): 6σ MAD respecte d'una mediana local
med = ndi.median_filter(np.where(ok, D, 0), 9)
res0 = D - med; mad = np.median(np.abs(res0[ok])) * 1.4826
ok &= np.abs(res0) < 6 * mad
iy, ix = np.nonzero(ok); d = D[iy, ix]; x = X[iy, ix]; y = Y[iy, ix]
tile = ((ix * B // 512) + (iy * B // 512)) % 2      # escaquer de 512 px: 0 = ajust, 1 = prova
print(f'canal {CH}: {d.size} blocs vàlids ({time.time()-t0:.0f}s); MAD {mad:.5f}', flush=True)
DR = 20.0
RMAX = 8000.0; K = int(RMAX / DR) + 2

def interp_rows(rho):
    j = np.clip((rho / DR).astype(int), 0, K - 2); f = rho / DR - j
    return j, f

xn = (x - W / 2) / (W / 2); yn = (y - H / 2) / (W / 2)
POLY = [xn**i * yn**j for i in range(GRAU + 1) for j in range(GRAU + 1 - i)]

def design(delta, sel):
    cA = CA0 + delta; cB = CB0 + delta
    rA = np.hypot(x[sel] - cA[0], y[sel] - cA[1]); rB = np.hypot(x[sel] - cB[0], y[sel] - cB[1])
    n = sel.sum(); rows = np.arange(n)
    jA, fA_ = interp_rows(rA); jB, fB_ = interp_rows(rB)
    P = sparse.coo_matrix((np.concatenate([1 - fA_, fA_, -(1 - fB_), -fB_]),
                           (np.concatenate([rows, rows, rows, rows]), np.concatenate([jA, jA + 1, jB, jB + 1]))), shape=(n, K)).tocsr()
    S = sparse.csr_matrix(np.stack([p[sel] for p in POLY], 1))
    return sparse.hstack([P, S]).tocsr()

LAM = 10.0   # pes de la 2a diferència de p (per node), en unitats de ln
Dm = sparse.diags([np.ones(K - 2), -2 * np.ones(K - 2), np.ones(K - 2)], [0, 1, 2], shape=(K - 2, K))
REG = sparse.hstack([Dm * LAM, sparse.csr_matrix((K - 2, len(POLY)))]).tocsr()

def fit(delta, sel):
    # equacions normals (417 incògnites): exacte i ràpid
    M = design(delta, sel)
    N = (M.T @ M).toarray() + (REG.T @ REG).toarray(); rhs = M.T @ d[sel]
    N[np.diag_indices_from(N)] += 1e-9
    return np.linalg.solve(N, rhs)

def resid(delta, sol, sel):
    return d[sel] - design(delta, sel) @ sol

fitsel = tile == 0; testsel = tile == 1
# control: només el camp suau (sense anells)
S_only = np.stack([p for p in POLY], 1)
cs = np.linalg.lstsq(S_only[fitsel], d[fitsel], rcond=None)[0]
rms_suau_fit = float(np.sqrt(np.mean((d[fitsel] - S_only[fitsel] @ cs)**2))); rms_suau_test = float(np.sqrt(np.mean((d[testsel] - S_only[testsel] @ cs)**2)))
print(f'només camp suau: rms ajust {rms_suau_fit:.5f} prova {rms_suau_test:.5f}', flush=True)
resultats = []
for dx in range(-120, 181, 60):
    for dy in range(80, 321, 60):
        dl = np.array([dx, dy], float); sol = fit(dl, fitsel)
        rf = float(np.sqrt(np.mean(resid(dl, sol, fitsel)**2))); rt = float(np.sqrt(np.mean(resid(dl, sol, testsel)**2)))
        resultats.append(dict(dx=dx, dy=dy, rms_ajust=rf, rms_prova=rt)); print(f'Δ=({dx:+4d},{dy:+4d}) rms ajust {rf:.5f} prova {rt:.5f}', flush=True)
best = min(resultats, key=lambda r: r['rms_ajust'])
# refinament fi al voltant del millor (triat per l'ajust, no per la prova)
for dx in range(best['dx'] - 60, best['dx'] + 61, 30):
    for dy in range(best['dy'] - 60, best['dy'] + 61, 30):
        if any(r['dx'] == dx and r['dy'] == dy for r in resultats): continue
        dl = np.array([dx, dy], float); sol = fit(dl, fitsel)
        rf = float(np.sqrt(np.mean(resid(dl, sol, fitsel)**2))); rt = float(np.sqrt(np.mean(resid(dl, sol, testsel)**2)))
        resultats.append(dict(dx=dx, dy=dy, rms_ajust=rf, rms_prova=rt)); print(f'Δ=({dx:+4d},{dy:+4d}) rms ajust {rf:.5f} prova {rt:.5f}', flush=True)
best = min(resultats, key=lambda r: r['rms_ajust'])
dl = np.array([best['dx'], best['dy']], float)
sol_fit = fit(dl, fitsel); sol_all = fit(dl, np.ones_like(fitsel))
p_fit = sol_fit[:K]; p_all = sol_all[:K]
rho = np.arange(K) * DR
out = dict(canal=CH, blocs=int(d.size), bloc_px=B, mad=float(mad), rms_nomes_suau=dict(ajust=rms_suau_fit, prova=rms_suau_test),
           graella=resultats, millor=best, delta_llenc=dl.tolist(), cA=(CA0 + dl).tolist(), cB=(CB0 + dl).tolist(), DR=DR, LAM=LAM,
           nota='p determinat llevat de c0 + c2 ρ² + c4 ρ⁴ (degenerat amb el camp suau); la meitat de prova no ha intervingut en cap tria')
np.savez(O / f'p_canal{CH}_r{RSUN_MIN:g}_g{GRAU}.npz', rho=rho, p_fit=p_fit, p_all=p_all, delta=dl, cA=CA0 + dl, cB=CB0 + dl)
(O / f'AJUST_canal{CH}_r{RSUN_MIN:g}_g{GRAU}.json').write_text(json.dumps(out, indent=1, ensure_ascii=False))
print('MILLOR', best, f'({time.time()-t0:.0f}s)')
